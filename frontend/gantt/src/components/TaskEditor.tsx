import React from 'react';
import { ScheduleTask, TaskFormData } from '../types';

interface TaskEditorProps {
  task: ScheduleTask | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: TaskFormData) => void;
  onDelete?: (id: number) => void;
}

export const TaskEditor: React.FC<TaskEditorProps> = ({ 
  task, 
  isOpen, 
  onClose, 
  onSave, 
  onDelete 
}) => {
  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    onSave({
      name: formData.get('name') as string,
      start: formData.get('start') as string,
      end: formData.get('end') as string,
    });
  };

  return (
    <div className="task-editor-modal">
      <div className="task-editor">
        <h3>{task ? 'Edit Task' : 'New Task'}</h3>
        <form onSubmit={handleSubmit}>
          <input name="name" defaultValue={task?.name} placeholder="Task name" required />
          <input name="start" type="date" defaultValue={task?.start} required />
          <input name="end" type="date" defaultValue={task?.end} required />
          <div className="task-editor-actions">
            <button type="submit">Save</button>
            <button type="button" onClick={onClose}>Cancel</button>
            {task && onDelete && (
              <button type="button" onClick={() => onDelete(task.id)}>Delete</button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
