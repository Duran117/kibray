import React, { useEffect, useRef, useState } from 'react';
import Gantt from 'frappe-gantt';
import { ScheduleTask, GanttTask } from '../types';
import { format } from 'date-fns';
import './GanttChart.css';

interface GanttChartProps {
  tasks: ScheduleTask[];
  onTaskUpdate: (taskId: string, start: string, end: string, progress: number) => void;
  onTaskClick: (task: ScheduleTask) => void;
  viewMode?: 'Day' | 'Week' | 'Month';
}

export const GanttChart: React.FC<GanttChartProps> = ({
  tasks,
  onTaskUpdate,
  onTaskClick,
  viewMode = 'Day',
}) => {
  const ganttRef = useRef<HTMLDivElement>(null);
  const ganttInstance = useRef<any>(null);
  const [currentView, setCurrentView] = useState<string>(() => {
    return localStorage.getItem('gantt_view_mode') || viewMode;
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!ganttRef.current) return;

    // Provide empty state if no tasks yet
    if (tasks.length === 0) {
      if (!ganttInstance.current) {
        ganttRef.current.innerHTML = '<div class="p-3 text-muted">No hay tareas en el cronograma todavía.</div>';
      }
      return;
    }

    // Convert tasks to Gantt format
    const ganttTasks: GanttTask[] = tasks.map((task) => ({
      id: task.id,
      name: task.name,
      start: task.start,
      end: task.end,
      progress: task.progress,
      dependencies: task.dependencies?.join(',') || '',
      custom_class: task.is_milestone ? 'milestone' : `status-${task.status.toLowerCase()}`,
    }));

    // Initialize or update Gantt
    if (!ganttInstance.current) {
  ganttInstance.current = new Gantt(ganttRef.current, ganttTasks, {
        view_mode: currentView as 'Day' | 'Week' | 'Month',
        date_format: 'YYYY-MM-DD',
        custom_popup_html: (task: any) => {
          return `
            <div class="gantt-popup">
              <h5>${task.name}</h5>
              <p><strong>Start:</strong> ${format(new Date(task._start), 'MMM dd, yyyy')}</p>
              <p><strong>End:</strong> ${format(new Date(task._end), 'MMM dd, yyyy')}</p>
              <p><strong>Progress:</strong> ${task.progress}%</p>
            </div>
          `;
        },
        on_click: (task: any) => {
          const originalTask = tasks.find((t) => t.id === task.id);
          if (originalTask) {
            onTaskClick(originalTask);
          }
        },
        on_date_change: async (task: any, start: Date, end: Date) => {
          setSaving(true);
          try {
            await onTaskUpdate(
              task.id,
              format(start, 'yyyy-MM-dd'),
              format(end, 'yyyy-MM-dd'),
              task.progress
            );
          } finally {
            setSaving(false);
          }
        },
        on_progress_change: async (task: any, progress: number) => {
          setSaving(true);
          try {
            await onTaskUpdate(task.id, task._start, task._end, progress);
          } finally {
            setSaving(false);
          }
        },
      });
    } else {
      ganttInstance.current.refresh(ganttTasks);
    }
  }, [tasks, currentView, onTaskUpdate, onTaskClick]);

  const changeView = (mode: string) => {
    setCurrentView(mode);
    localStorage.setItem('gantt_view_mode', mode);
    if (ganttInstance.current) {
      ganttInstance.current.change_view_mode(mode);
    }
  };

  return (
  <div className="gantt-wrapper" data-component="gantt-chart">
      <div className="gantt-controls">
        <div className="btn-group">
          <button
            className={`btn btn-sm ${currentView === 'Day' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => changeView('Day')}
          >
            <i className="bi bi-calendar-day"></i> Day
          </button>
          <button
            className={`btn btn-sm ${currentView === 'Week' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => changeView('Week')}
          >
            <i className="bi bi-calendar-week"></i> Week
          </button>
          <button
            className={`btn btn-sm ${currentView === 'Month' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => changeView('Month')}
          >
            <i className="bi bi-calendar-month"></i> Month
          </button>
        </div>
        {saving && (
          <div className="saving-indicator">
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Guardando cambios...
          </div>
        )}
      </div>
      <div ref={ganttRef} className="gantt-container"></div>
      {/* Instrumentation for tests: expose task names */}
      <div id="gantt-task-names" style={{display:'none'}} data-task-names={tasks.map(t=>t.name).join('|')}></div>
    </div>
  );
};
