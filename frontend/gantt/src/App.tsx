import React, { useState } from 'react';
import { GanttChart } from './components/GanttChart';
import { TaskEditor } from './components/TaskEditor';
import { ScheduleTask, TaskFormData } from './types';
import './index.css';

const App: React.FC = () => {
  const [tasks, setTasks] = useState<ScheduleTask[]>([]);
  const [selectedTask, setSelectedTask] = useState<ScheduleTask | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  const handleSaveTask = (data: TaskFormData) => {
    if (selectedTask) {
      setTasks(tasks.map(t => 
        t.id === selectedTask.id ? { ...t, ...data } : t
      ));
    } else {
      const newTask: ScheduleTask = {
        id: Date.now(),
        ...data,
        progress: 0
      };
      setTasks([...tasks, newTask]);
    }
    setIsEditorOpen(false);
    setSelectedTask(null);
  };

  const handleDeleteTask = (id: number) => {
    setTasks(tasks.filter(t => t.id !== id));
    setIsEditorOpen(false);
    setSelectedTask(null);
  };

  return (
    <div className="gantt-app">
      <div className="gantt-header">
        <h1>Gantt Board</h1>
        <button onClick={() => {
          setSelectedTask(null);
          setIsEditorOpen(true);
        }}>
          New Task
        </button>
      </div>
      
      <GanttChart 
        tasks={tasks} 
        onTaskClick={(task) => {
          setSelectedTask(task);
          setIsEditorOpen(true);
        }}
      />
      
      <TaskEditor
        task={selectedTask}
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

export default App;
