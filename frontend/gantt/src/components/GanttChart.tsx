import React from 'react';
import { ScheduleTask } from '../types';

interface GanttChartProps {
  tasks: ScheduleTask[];
  onTaskClick?: (task: ScheduleTask) => void;
}

export const GanttChart: React.FC<GanttChartProps> = ({ tasks, onTaskClick }) => {
  return (
    <div className="gantt-chart">
      <h3>Gantt Chart</h3>
      <div className="gantt-tasks">
        {tasks.map(task => (
          <div 
            key={task.id} 
            className="gantt-task"
            onClick={() => onTaskClick?.(task)}
          >
            <span>{task.name}</span>
            <span>{task.start} - {task.end}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
