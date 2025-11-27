// Touch-Up Board route
// import TouchupBoard from './pages/TouchupBoard';

// ...existing code...

// Example route wiring (adjust if using react-router)
// <Route path="/touchups" element={<TouchupBoard />} />
import React, { useState, useEffect } from 'react';
import { GanttChart } from './components/GanttChart';
import { TaskEditor } from './components/TaskEditor';
import { ScheduleTask, ScheduleCategory, TaskFormData } from './types';
import { scheduleApi } from './api';
import './App.css';

interface AppProps {
  projectId: number;
}

export const App: React.FC<AppProps> = ({ projectId }) => {
  const [tasks, setTasks] = useState<ScheduleTask[]>([]);
  const [categories, setCategories] = useState<ScheduleCategory[]>([]);
  const [selectedTask, setSelectedTask] = useState<ScheduleTask | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [viewMode] = useState<'Day' | 'Week' | 'Month'>('Day');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [tasksData, categoriesData] = await Promise.all([
        scheduleApi.getTasks(projectId),
        scheduleApi.getCategories(projectId),
      ]);
      setTasks(tasksData);
      setCategories(categoriesData);
    } catch (err) {
      setError('Error al cargar los datos del cronograma');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskUpdate = async (taskId: string, changes: Partial<ScheduleTask>) => {
    try {
      const updatedTask = await scheduleApi.updateTask(taskId, changes);
      setTasks((prev) => prev.map((t) => (t.id === taskId ? updatedTask : t)));
    } catch (err) {
      setError('Error al actualizar la tarea');
      console.error('Error updating task:', err);
    }
  };

  const handleGanttTaskUpdate = (taskId: string, start: string, end: string, progress: number) => {
    handleTaskUpdate(taskId, { start, end, progress });
  };

  const handleTaskClick = (task: ScheduleTask) => {
    setSelectedTask(task);
    setIsEditorOpen(true);
  };

  const handleNewTask = () => {
    setSelectedTask(null);
    setIsEditorOpen(true);
  };

  const handleSaveTask = async (taskId: string | null, data: TaskFormData) => {
    try {
      if (taskId) {
        // Update existing task
        const updatedTask = await scheduleApi.updateTask(taskId, data);
        setTasks((prev) => prev.map((t) => (t.id === taskId ? updatedTask : t)));
      } else {
        // Create new task
        const newTask = await scheduleApi.createTask(projectId, data);
        setTasks((prev) => [...prev, newTask]);
      }
      setIsEditorOpen(false);
      setSelectedTask(null);
    } catch (err) {
      setError(taskId ? 'Error al actualizar la tarea' : 'Error al crear la tarea');
      console.error('Error saving task:', err);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await scheduleApi.deleteTask(taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      setIsEditorOpen(false);
      setSelectedTask(null);
    } catch (err) {
      setError('Error al eliminar la tarea');
      console.error('Error deleting task:', err);
    }
  };

  const handleExportPDF = async () => {
    try {
      const { jsPDF } = await import('jspdf');
      const html2canvas = (await import('html2canvas')).default;

      const ganttElement = document.querySelector('.gantt-container');
      if (!ganttElement) return;

      const canvas = await html2canvas(ganttElement as HTMLElement);
      const imgData = canvas.toDataURL('image/png');

      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4',
      });

      const imgWidth = 297; // A4 landscape width in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
      pdf.save(`cronograma-proyecto-${projectId}.pdf`);
    } catch (err) {
      setError('Error al exportar PDF');
      console.error('Error exporting PDF:', err);
    }
  };

  if (loading) {
    return (
      <div className="app-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando cronograma...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-container">
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
          <button className="btn btn-link" onClick={loadData}>
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="app-header">
        <h2>Cronograma del Proyecto</h2>
        <div className="app-toolbar">
          <button className="btn btn-primary" onClick={handleNewTask}>
            <i className="bi bi-plus-lg"></i> Nueva Tarea
          </button>
          <button className="btn btn-secondary" onClick={handleExportPDF}>
            <i className="bi bi-file-pdf"></i> Exportar PDF
          </button>
          <button className="btn btn-secondary" onClick={loadData}>
            <i className="bi bi-arrow-clockwise"></i> Actualizar
          </button>
        </div>
      </div>

      <GanttChart
        tasks={tasks}
        onTaskUpdate={handleGanttTaskUpdate}
        onTaskClick={handleTaskClick}
        viewMode={viewMode}
      />

      <TaskEditor
        task={selectedTask}
        categories={categories}
        isOpen={isEditorOpen}
        onClose={() => {
          setIsEditorOpen(false);
          setSelectedTask(null);
        }}
        onSave={handleSaveTask}
        onDelete={handleDeleteTask}
      />
    </div>
  );
};
