import React, { useEffect, useMemo, useState, useCallback } from 'react';
import axios from 'axios';
import GanttChart, { ViewMode, defaultTheme, darkTheme } from 'react-modern-gantt';
import { format, parseISO } from 'date-fns';
import './styles.css';
import 'react-modern-gantt/dist/index.css';

const clampPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
};

const normalizeDate = (value) => {
  if (!value) return new Date();
  return value instanceof Date ? value : parseISO(value);
};

const buildDependenciesMap = (dependencies = []) => {
  return dependencies.reduce((acc, dep) => {
    const targetKey = `item-${dep.target_item}`;
    const sourceKey = `item-${dep.source_item}`;
    if (!acc[targetKey]) acc[targetKey] = [];
    acc[targetKey].push(sourceKey);
    return acc;
  }, {});
};

const mapApiToTaskGroups = (phases = [], dependencies = []) => {
  const deps = buildDependenciesMap(dependencies);
  return phases.map((phase) => {
    const phaseColor = phase.color || '#22d3ee';
    return {
      id: `phase-${phase.id}`,
      name: phase.name,
      description: phase.allow_sunday ? 'Domingo habilitado' : undefined,
      color: phaseColor,
      allowSunday: phase.allow_sunday,
      tasks: (phase.items || []).map((item) => {
        const start = normalizeDate(item.start_date || item.created_at);
        const end = normalizeDate(item.end_date || item.start_date || item.created_at);
        const isMilestone = !!item.is_milestone || start.getTime() === end.getTime();
        return {
          id: `item-${item.id}`,
          name: item.name,
          startDate: start,
          endDate: end,
          color: item.color || phaseColor,
          percent: clampPercent(item.progress),
          dependencies: deps[`item-${item.id}`] || [],
          status: item.status,
          assignedTo: item.assigned_to_name,
          isMilestone,
          allowSunday: item.allow_sunday_effective,
        };
      }),
    };
  });
};

const viewModes = [ViewMode.DAY, ViewMode.WEEK, ViewMode.MONTH];

function Header({ project, onRefresh, viewMode, onViewModeChange, lastUpdated, counts }) {
  return (
    <div className="gantt-header">
      <div>
        <p className="eyebrow">Gantt v2 · Proyecto</p>
        <h1>{project?.name || 'Proyecto'}</h1>
        <p className="subdued">
          {project?.project_code ? `${project.project_code} · ` : ''}
          {project?.start_date ? `Inicio ${project.start_date}` : ''}
          {project?.end_date ? ` · Fin ${project.end_date}` : ''}
        </p>
        <p className="subdued">
          Items: {counts.items} · Tareas: {counts.tasks} · Dependencias: {counts.dependencies}
        </p>
      </div>
      <div className="gantt-controls">
        <div className="button-group">
          {viewModes.map((mode) => (
            <button
              key={mode}
              className={mode === viewMode ? 'btn active' : 'btn'}
              onClick={() => onViewModeChange(mode)}
            >
              {mode}
            </button>
          ))}
        </div>
        <button className="btn ghost" onClick={onRefresh}>Recargar</button>
        <span className="timestamp">{lastUpdated ? `Actualizado ${format(lastUpdated, 'PPpp')}` : ''}</span>
      </div>
    </div>
  );
}

export default function App() {
  const search = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
  const initialProjectId = search?.get('project') || search?.get('project_id') || search?.get('id');
  const [projectId, setProjectId] = useState(initialProjectId || '1');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState(ViewMode.WEEK);
  const [darkMode, setDarkMode] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [itemForm, setItemForm] = useState({ start_date: '', end_date: '', progress: 0 });
  const [newTaskTitle, setNewTaskTitle] = useState('');

  const api = useMemo(() => {
    const instance = axios.create();
    instance.defaults.xsrfCookieName = 'csrftoken';
    instance.defaults.xsrfHeaderName = 'X-CSRFToken';
    return instance;
  }, []);

  const fetchData = useCallback(async (targetProjectId = projectId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/v1/gantt/v2/projects/${targetProjectId}/`);
      setData(response.data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Error al cargar el Gantt');
    } finally {
      setLoading(false);
    }
  }, [projectId, api]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const itemsById = useMemo(() => {
    const map = {};
    (data?.phases || []).forEach((phase) => {
      (phase.items || []).forEach((item) => {
        map[item.id] = item;
      });
    });
    return map;
  }, [data]);

  const selectedItem = selectedItemId ? itemsById[selectedItemId] : null;

  useEffect(() => {
    if (selectedItem) {
      setItemForm({
        start_date: selectedItem.start_date || '',
        end_date: selectedItem.end_date || '',
        progress: clampPercent(selectedItem.progress),
      });
      setNewTaskTitle('');
    }
  }, [selectedItemId, selectedItem]);

  const taskGroups = useMemo(() => {
    if (!data?.phases) return [];
    return mapApiToTaskGroups(data.phases, data.dependencies);
  }, [data]);

  const metadata = data?.metadata || { items_count: 0, tasks_count: 0, dependencies_count: 0 };

  const phases = data?.phases || [];
  const firstPhaseId = phases[0]?.id;
  const firstItemId = phases[0]?.items?.[0]?.id;

  const createItem = async () => {
    if (!projectId || !firstPhaseId) {
      alert('No hay fases disponibles para crear un item.');
      return;
    }
    const name = window.prompt('Nombre del item', 'Nuevo item');
    if (!name) return;
    setBusy(true);
    try {
      const today = new Date();
      const end = new Date();
      end.setDate(today.getDate() + 3);
      await api.post('/api/v1/gantt/v2/items/', {
        project: projectId,
        phase: firstPhaseId,
        name,
        start_date: today.toISOString().slice(0, 10),
        end_date: end.toISOString().slice(0, 10),
        progress: 0,
      });
      await fetchData(projectId);
    } catch (err) {
      alert(err?.response?.data?.error || 'No se pudo crear el item');
    } finally {
      setBusy(false);
    }
  };

  const createTask = async () => {
    if (!firstItemId) {
      alert('No hay items disponibles para crear tareas.');
      return;
    }
    const title = window.prompt('Título de la tarea', 'Nueva tarea');
    if (!title) return;
    setBusy(true);
    try {
      await api.post('/api/v1/gantt/v2/tasks/', {
        item: firstItemId,
        title,
        status: 'pending',
        order: 0,
      });
      await fetchData(projectId);
    } catch (err) {
      alert(err?.response?.data?.error || 'No se pudo crear la tarea');
    } finally {
      setBusy(false);
    }
  };

  const patchItem = async (itemId, payload) => {
    setBusy(true);
    try {
      await api.patch(`/api/v1/gantt/v2/items/${itemId}/`, payload);
      await fetchData(projectId);
    } catch (err) {
      alert(err?.response?.data?.error || 'No se pudo actualizar el item');
    } finally {
      setBusy(false);
    }
  };

  const addTaskToItem = async (itemId, title) => {
    setBusy(true);
    try {
      await api.post('/api/v1/gantt/v2/tasks/', {
        item: itemId,
        title,
        status: 'pending',
        order: selectedItem?.tasks?.length || 0,
      });
      await fetchData(projectId);
    } catch (err) {
      alert(err?.response?.data?.error || 'No se pudo crear la tarea');
    } finally {
      setBusy(false);
    }
  };

  const theme = useMemo(() => {
    const base = darkMode ? darkTheme : defaultTheme;
    return {
      ...base,
      colors: {
        ...base.colors,
        primary: '#22d3ee',
        accent: '#a855f7',
        success: '#22c55e',
        danger: '#ef4444',
        muted: '#94a3b8',
        background: darkMode ? '#0b1220' : '#f8fafc',
      },
    };
  }, [darkMode]);

  return (
    <div className={darkMode ? 'gantt-shell dark' : 'gantt-shell'}>
      <Header
        project={data?.project}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        onRefresh={() => fetchData(projectId)}
        lastUpdated={lastUpdated}
        counts={{ items: metadata.items_count || 0, tasks: metadata.tasks_count || 0, dependencies: metadata.dependencies_count || 0 }}
      />

      <div className="toolbar">
        <label className="field">
          <span>Proyecto ID</span>
          <input
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            onBlur={(e) => fetchData(e.target.value)}
            placeholder="ID"
          />
        </label>
        <label className="switch">
          <input type="checkbox" checked={darkMode} onChange={() => setDarkMode((v) => !v)} />
          <span>Modo oscuro</span>
        </label>
        <label className="switch">
          <input type="checkbox" checked={editMode} onChange={() => setEditMode((v) => !v)} />
          <span>Edición (drag/progreso)</span>
        </label>
        <div className="button-group">
          <button className="btn" onClick={createItem} disabled={busy}>+ Item</button>
          <button className="btn" onClick={createTask} disabled={busy}>+ Tarea</button>
        </div>
      </div>

      {loading && <div className="notice">Cargando Gantt...</div>}
      {error && <div className="notice error">{error}</div>}

      {!loading && !error && taskGroups.length === 0 && (
        <div className="notice">Sin datos para este proyecto.</div>
      )}

      {!loading && !error && taskGroups.length > 0 && (
        <div className="gantt-card">
          <GanttChart
            tasks={taskGroups}
            viewMode={viewMode}
            title={data?.project?.name || 'Proyecto'}
            editMode={editMode}
            showProgress
            darkMode={darkMode}
            styles={{ container: 'gantt-container' }}
            showCurrentDateMarker
            currentDate={new Date()}
            onDateChange={(task) => {
              if (!editMode) return;
              const id = task.id?.replace('item-', '');
              if (!id) return;
              const start_date = task.startDate instanceof Date ? task.startDate.toISOString().slice(0, 10) : null;
              const end_date = task.endDate instanceof Date ? task.endDate.toISOString().slice(0, 10) : null;
              patchItem(id, { start_date, end_date });
            }}
            onProgressChange={(task) => {
              if (!editMode) return;
              const id = task.id?.replace('item-', '');
              if (!id) return;
              patchItem(id, { progress: clampPercent(task.percent) });
            }}
            onTaskClick={(task, group) => {
              const id = task.id?.replace('item-', '');
              if (!id) return;
              setSelectedItemId(Number(id));
            }}
            onViewModeChange={setViewMode}
            viewModes={viewModes}
            theme={theme}
          />
        </div>
      )}

      {selectedItem && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <div>
                <p className="eyebrow">Item</p>
                <h3>{selectedItem.name}</h3>
              </div>
              <button className="icon-btn" onClick={() => setSelectedItemId(null)} aria-label="Cerrar">×</button>
            </div>

            <div className="modal-body">
              <div className="grid">
                <label className="field">
                  <span>Inicio</span>
                  <input
                    type="date"
                    value={itemForm.start_date || ''}
                    onChange={(e) => setItemForm((f) => ({ ...f, start_date: e.target.value }))}
                  />
                </label>
                <label className="field">
                  <span>Fin</span>
                  <input
                    type="date"
                    value={itemForm.end_date || ''}
                    onChange={(e) => setItemForm((f) => ({ ...f, end_date: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span>Progreso (%)</span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={itemForm.progress}
                  onChange={(e) => setItemForm((f) => ({ ...f, progress: clampPercent(Number(e.target.value)) }))}
                />
              </label>

              <div className="tasks-panel">
                <div className="tasks-header">
                  <h4>Tareas ({selectedItem.tasks?.length || 0})</h4>
                </div>
                <ul className="tasks-list">
                  {(selectedItem.tasks || []).map((t) => (
                    <li key={t.id}>
                      <span>{t.title}</span>
                      <small className="pill">{t.status}</small>
                    </li>
                  ))}
                  {(!selectedItem.tasks || selectedItem.tasks.length === 0) && (
                    <li className="muted">Sin tareas</li>
                  )}
                </ul>
                <div className="task-add">
                  <input
                    type="text"
                    placeholder="Nueva tarea"
                    value={newTaskTitle}
                    onChange={(e) => setNewTaskTitle(e.target.value)}
                  />
                  <button
                    className="btn"
                    onClick={() => {
                      if (!newTaskTitle) return;
                      addTaskToItem(selectedItem.id, newTaskTitle).then(() => setNewTaskTitle(''));
                    }}
                    disabled={busy || !newTaskTitle}
                  >
                    + Agregar
                  </button>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn ghost" onClick={() => setSelectedItemId(null)} disabled={busy}>Cancelar</button>
              <button
                className="btn"
                onClick={() => {
                  if (!selectedItemId) return;
                  const payload = {
                    start_date: itemForm.start_date,
                    end_date: itemForm.end_date,
                    progress: clampPercent(itemForm.progress),
                  };
                  patchItem(selectedItemId, payload).then(() => setSelectedItemId(null));
                }}
                disabled={busy}
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
