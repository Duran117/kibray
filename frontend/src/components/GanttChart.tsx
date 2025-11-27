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
  const [currentView, setCurrentView] = useState<string>(viewMode);

  useEffect(() => {
    if (!ganttRef.current || tasks.length === 0) return;

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
        on_date_change: (task: any, start: Date, end: Date) => {
          onTaskUpdate(
            task.id,
            format(start, 'yyyy-MM-dd'),
            format(end, 'yyyy-MM-dd'),
            task.progress
          );
        },
        on_progress_change: (task: any, progress: number) => {
          onTaskUpdate(task.id, task._start, task._end, progress);
        },
      });
    } else {
      ganttInstance.current.refresh(ganttTasks);
    }
  }, [tasks, currentView, onTaskUpdate, onTaskClick]);

  const changeView = (mode: string) => {
    setCurrentView(mode);
    if (ganttInstance.current) {
      ganttInstance.current.change_view_mode(mode);
    }
  };

  return (
    <div className="gantt-wrapper">
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
      </div>
      <div ref={ganttRef} className="gantt-container"></div>
    </div>
  );
};
