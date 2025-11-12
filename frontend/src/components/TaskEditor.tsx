import React, { useState, useEffect } from 'react';
import { ScheduleTask, ScheduleCategory, TaskFormData } from '../types';
import { format } from 'date-fns';
import './TaskEditor.css';

interface TaskEditorProps {
  task: ScheduleTask | null;
  categories: ScheduleCategory[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (taskId: string | null, data: TaskFormData) => void;
  onDelete?: (taskId: string) => void;
}

export const TaskEditor: React.FC<TaskEditorProps> = ({
  task,
  categories,
  isOpen,
  onClose,
  onSave,
  onDelete,
}) => {
  const [formData, setFormData] = useState<TaskFormData>({
    name: '',
    start: format(new Date(), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd'),
    status: 'NOT_STARTED',
    progress: 0,
    is_milestone: false,
    description: '',
  });

  useEffect(() => {
    if (task) {
      setFormData({
        name: task.name,
        start: task.start,
        end: task.end,
        status: task.status,
        progress: task.progress,
        category: task.category,
        is_milestone: task.is_milestone || false,
        description: '',
      });
    } else {
      setFormData({
        name: '',
        start: format(new Date(), 'yyyy-MM-dd'),
        end: format(new Date(), 'yyyy-MM-dd'),
        status: 'NOT_STARTED',
        progress: 0,
        is_milestone: false,
        description: '',
      });
    }
  }, [task]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(task?.id || null, formData);
  };

  const handleDelete = () => {
    if (task && onDelete && window.confirm('¿Eliminar esta tarea?')) {
      onDelete(task.id);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="task-editor-overlay" onClick={onClose}>
      <div className="task-editor" onClick={(e) => e.stopPropagation()}>
        <div className="task-editor-header">
          <h3>{task ? 'Editar Tarea' : 'Nueva Tarea'}</h3>
          <button className="btn-close" onClick={onClose}></button>
        </div>

        <form onSubmit={handleSubmit} className="task-editor-body">
          <div className="mb-3">
            <label className="form-label">
              Nombre de la tarea <span className="text-danger">*</span>
            </label>
            <input
              type="text"
              className="form-control"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Fecha de inicio</label>
              <input
                type="date"
                className="form-control"
                value={formData.start}
                onChange={(e) => setFormData({ ...formData, start: e.target.value })}
                required
              />
            </div>
            <div className="col-md-6 mb-3">
              <label className="form-label">Fecha de fin</label>
              <input
                type="date"
                className="form-control"
                value={formData.end}
                onChange={(e) => setFormData({ ...formData, end: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Estado</label>
              <select
                className="form-select"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              >
                <option value="NOT_STARTED">No iniciado</option>
                <option value="IN_PROGRESS">En progreso</option>
                <option value="DONE">Completado</option>
                <option value="BLOCKED">Bloqueado</option>
              </select>
            </div>
            <div className="col-md-6 mb-3">
              <label className="form-label">Progreso (%)</label>
              <input
                type="number"
                className="form-control"
                min="0"
                max="100"
                value={formData.progress}
                onChange={(e) =>
                  setFormData({ ...formData, progress: parseInt(e.target.value) || 0 })
                }
              />
            </div>
          </div>

          <div className="mb-3">
            <label className="form-label">Categoría</label>
            <select
              className="form-select"
              value={formData.category || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  category: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            >
              <option value="">Sin categoría</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-3 form-check">
            <input
              type="checkbox"
              className="form-check-input"
              id="isMilestone"
              checked={formData.is_milestone}
              onChange={(e) => setFormData({ ...formData, is_milestone: e.target.checked })}
            />
            <label className="form-check-label" htmlFor="isMilestone">
              Marcar como hito (milestone)
            </label>
          </div>

          <div className="mb-3">
            <label className="form-label">Descripción</label>
            <textarea
              className="form-control"
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div className="task-editor-footer">
            {task && onDelete && (
              <button type="button" className="btn btn-danger me-auto" onClick={handleDelete}>
                <i className="bi bi-trash"></i> Eliminar
              </button>
            )}
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary">
              <i className="bi bi-save"></i> Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
