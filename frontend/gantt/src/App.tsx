// =============================================================================
// Kibray Gantt - Demo App
// =============================================================================

import { useState } from 'react';
import { KibrayGantt, CalendarView, ViewSwitcher, ViewMode } from './components';
import { GanttMode, GanttItem } from './types/gantt';
import { demoCategories, demoItems, demoDependencies } from './data/demoData';
import './App.css';

function App() {
  const [mode, setMode] = useState<GanttMode>('project');
  const [items, setItems] = useState<GanttItem[]>(demoItems);
  const [viewMode, setViewMode] = useState<ViewMode>('gantt');
  const [selectedItem, setSelectedItem] = useState<GanttItem | null>(null);

  // Demo team members
  const demoTeamMembers = [
    { id: 1, name: 'John Smith' },
    { id: 2, name: 'Maria Garcia' },
    { id: 3, name: 'Mike Johnson' },
  ];

  // Simulated save handlers
  const handleItemUpdate = async (item: any) => {
    console.log('Saving item:', item);
    await new Promise(resolve => setTimeout(resolve, 500));
    // Update local state
    setItems(prev => prev.map(i => i.id === item.id ? { ...i, ...item } : i));
  };

  const handleItemDelete = async (itemId: number) => {
    console.log('Deleting item:', itemId);
    await new Promise(resolve => setTimeout(resolve, 500));
    // Update local state
    setItems(prev => prev.filter(i => i.id !== itemId));
  };

  const handleCreateTask = async (task: { schedule_item_id: number; title: string; description: string; assigned_to: number | null }) => {
    console.log('Creating task:', task);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Create new task with ID
    const newTask = {
      id: Date.now(),
      title: task.title,
      status: 'pending',
      assigned_to: task.assigned_to,
      assigned_to_name: task.assigned_to 
        ? demoTeamMembers.find(m => m.id === task.assigned_to)?.name 
        : undefined,
      is_completed: false,
    };
    
    // Update the item with the new task
    setItems(prev => prev.map(item => {
      if (item.id === task.schedule_item_id) {
        return {
          ...item,
          tasks: [...(item.tasks || []), newTask],
        };
      }
      return item;
    }));
    
    console.log('Task created:', newTask);
  };

  // Handle item click from calendar view
  const handleItemClick = (item: GanttItem) => {
    setSelectedItem(item);
    // Switch to gantt view to see the panel
    setViewMode('gantt');
  };

  return (
    <div className="app-container">
      {/* Header with mode selector and view switcher */}
      <div className="header-row">
        {/* Mode selector for demo */}
        <div className="mode-selector">
          <span className="mode-label">Demo Mode:</span>
          <div className="mode-buttons">
            {(['project', 'master', 'pm', 'strategic'] as GanttMode[]).map(m => (
              <button
                key={m}
                className={'mode-btn ' + (mode === m ? 'active' : '')}
                onClick={() => setMode(m)}
              >
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* View switcher */}
        <ViewSwitcher currentView={viewMode} onViewChange={setViewMode} />
      </div>

      {/* Content area */}
      <div className="content-wrapper">
        {viewMode === 'gantt' ? (
          <div className="gantt-wrapper">
            <KibrayGantt
              mode={mode}
              items={items}
              categories={demoCategories}
              dependencies={demoDependencies}
              projectId={1}
              projectName="Sample Construction Project"
              canEdit={true}
              onItemUpdate={handleItemUpdate}
              onItemDelete={handleItemDelete}
              onTaskCreate={handleCreateTask}
              teamMembers={demoTeamMembers}
            />
          </div>
        ) : (
          <div className="calendar-wrapper">
            <CalendarView
              items={items}
              categories={demoCategories}
              onItemClick={handleItemClick}
              canEdit={true}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
