import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { CheckSquare, Circle, CheckCircle2, Clock, AlertCircle, GripVertical } from 'lucide-react';
import * as api from '../../../utils/api';
import './TasksWidget.css';
import { formatDate } from '../../../utils/formatDate';

const TasksWidget = ({ projectId, openPanel }) => {
  const { t } = useTranslation();
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTasks();
  }, [projectId, filter]);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('ordering', 'due_date');
      
      if (projectId) {
        params.append('project', projectId);
      }
      
      if (filter === 'active') {
        params.append('status', 'IN_PROGRESS');
        params.append('status', 'PENDING');
      } else if (filter === 'completed') {
        params.append('status', 'COMPLETED');
      }
      
      const data = await api.get(`/tasks/?${params.toString()}`);
      setTasks(data.results || data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setTasks([]);
      setError(t('errors.loading_tasks', { defaultValue: 'Failed to load tasks' }));
    } finally {
      setLoading(false);
    }
  };

  const handleTaskClick = (task) => {
    if (openPanel) {
      openPanel({
        title: task.title,
        component: 'TaskDetail',
        props: { taskId: task.id }
      });
    }
  };

  const getStatusIcon = (status) => {
    const upperStatus = (status || '').toUpperCase();
    if (upperStatus === 'COMPLETED' || upperStatus === 'COMPLETADA') {
      return <CheckCircle2 size={18} className="status-icon-completed" />;
    } else if (upperStatus === 'IN_PROGRESS' || upperStatus === 'EN PROGRESO') {
      return <Clock size={18} className="status-icon-progress" />;
    } else if (upperStatus === 'BLOCKED' || upperStatus === 'BLOQUEADA') {
      return <AlertCircle size={18} className="status-icon-blocked" />;
    } else {
      return <Circle size={18} className="status-icon-pending" />;
    }
  };

  const getPriorityClass = (priority) => `priority-${(priority || 'medium').toLowerCase()}`;
  const getPriorityLabel = (priority) => {
    const key = (priority || 'medium').toLowerCase();
    return t(`tasks.priority.${key}`, { defaultValue: (priority || 'medium').toUpperCase() });
  };

  return (
    <div className="tasks-widget">
      <div className="widget-drag-handle">
        <GripVertical size={16} />
      </div>
      
      <div className="widget-header">
        <h3 className="widget-title">
          <CheckSquare size={20} />
          {t('tasks.my_tasks', { defaultValue: 'My Tasks' })}
        </h3>
        <div className="task-filters">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            {t('tasks.filters.all', { defaultValue: 'All' })}
          </button>
          <button
            className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
            onClick={() => setFilter('active')}
          >
            {t('tasks.filters.active', { defaultValue: 'Active' })}
          </button>
          <button
            className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
            onClick={() => setFilter('completed')}
          >
            {t('tasks.filters.completed', { defaultValue: 'Done' })}
          </button>
        </div>
      </div>

      <div className="tasks-list">
        {loading ? (
          <div className="tasks-loading">
            <div className="spinner"></div>
            <p>{t('tasks.loading', { defaultValue: 'Loading tasks...' })}</p>
          </div>
        ) : error ? (
          <div className="tasks-error">
            <AlertCircle size={24} />
            <p>{error}</p>
            <button onClick={fetchTasks} className="retry-btn">{t('common.retry')}</button>
          </div>
        ) : tasks.length > 0 ? (
          tasks.map((task) => (
            <div
              key={task.id}
              className={`task-item ${getPriorityClass(task.priority)}`}
              onClick={() => handleTaskClick(task)}
              style={{ cursor: 'pointer' }}
            >
              <div className="task-status">
                {getStatusIcon(task.status)}
              </div>
              <div className="task-content">
                <h4 className="task-title">{task.title}</h4>
                <div className="task-meta">
                  <span className={`task-priority ${getPriorityClass(task.priority)}`}>
                    {getPriorityLabel(task.priority)}
                  </span>
                  {task.due_date && (
                    <span className="task-due">{formatDate(task.due_date, 'P')}</span>
                  )}
                  {task.assigned_to && (
                    <span className="task-assignee">{task.assigned_to.first_name} {task.assigned_to.last_name}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="no-tasks">
            <CheckSquare size={32} />
            <p>{t('tasks.no_tasks_found', { defaultValue: 'No tasks found' })}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TasksWidget;
