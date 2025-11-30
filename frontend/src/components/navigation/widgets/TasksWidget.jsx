import React from 'react';
import './TasksWidget.css';

const TasksWidget = ({ tasks }) => {
  return (
    <div className="widget tasks-widget">
      <div className="widget-header"><h4>Tasks</h4></div>
      <ul className="tasks-list">
        {tasks.map(t => (
          <li key={t.id} className={`task-item ${t.status}`}>\n            <span className="task-title">{t.title}</span>\n            <span className="task-status">{t.status}</span>\n          </li>
        ))}
        {tasks.length === 0 && <li className="empty">No tasks</li>}
      </ul>
    </div>
  );
};

export default TasksWidget;
