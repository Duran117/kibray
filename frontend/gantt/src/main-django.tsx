// =============================================================================
// Kibray Gantt - Main Entry Point for Django Integration
// =============================================================================

import React from 'react';
import ReactDOM from 'react-dom/client';
import { KibrayGantt, CalendarView, ViewSwitcher, ViewMode } from './components';
import { GanttMode, GanttItem, GanttCategory, GanttDependency } from './types/gantt';
import { transformV2Response, toV2ItemPayload, toV2TaskPayload } from './api/adapters';
import { GanttApi } from './api/ganttApi';
import './index.css';

// Types for the Django integration
interface KibrayGanttAppConfig {
  mode: GanttMode;
  projectId?: number;
  projectName?: string;
  canEdit: boolean;
  csrfToken: string;
  apiBaseUrl?: string;
  initialView?: ViewMode;
  teamMembers?: { id: number; name: string }[];
  // Data can be passed directly or fetched
  initialData?: {
    project?: any;
    phases?: any[];
    dependencies?: any[];
  };
}

interface KibrayGanttAppState {
  items: GanttItem[];
  categories: GanttCategory[];
  dependencies: GanttDependency[];
  viewMode: ViewMode;
  loading: boolean;
  error: string | null;
}

/**
 * Main Gantt App component for Django integration
 */
const KibrayGanttApp: React.FC<KibrayGanttAppConfig> = ({
  mode,
  projectId,
  projectName,
  canEdit,
  csrfToken,
  apiBaseUrl = '/api/v1',
  initialView = 'gantt',
  teamMembers = [],
  initialData,
}) => {
  const [state, setState] = React.useState<KibrayGanttAppState>({
    items: [],
    categories: [],
    dependencies: [],
    viewMode: initialView,
    loading: !initialData,
    error: null,
  });

  const apiRef = React.useRef<GanttApi | null>(null);

  // Initialize API
  React.useEffect(() => {
    apiRef.current = new GanttApi(apiBaseUrl, csrfToken);
  }, [apiBaseUrl, csrfToken]);

  // Load initial data
  React.useEffect(() => {
    if (initialData) {
      const transformed = transformV2Response(initialData);
      setState(prev => ({
        ...prev,
        items: transformed.items,
        categories: transformed.categories,
        dependencies: transformed.dependencies,
        loading: false,
      }));
    } else if (projectId && apiRef.current) {
      loadData();
    }
  }, [initialData, projectId]);

  const loadData = async () => {
    if (!apiRef.current || !projectId) return;

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await apiRef.current.fetchGanttData(mode, { projectId });
      const transformed = transformV2Response(response);
      setState(prev => ({
        ...prev,
        items: transformed.items,
        categories: transformed.categories,
        dependencies: transformed.dependencies,
        loading: false,
      }));
    } catch (err: any) {
      setState(prev => ({ ...prev, loading: false, error: err.message }));
    }
  };

  // Item update handler
  const handleItemUpdate = async (item: Partial<GanttItem>) => {
    if (!apiRef.current || !item.id) return;

    try {
      const payload = toV2ItemPayload(item);
      await apiRef.current.updateItem(item.id, payload);
      setState(prev => ({
        ...prev,
        items: prev.items.map(i => i.id === item.id ? { ...i, ...item } : i),
      }));
    } catch (err: any) {
      console.error('Failed to update item:', err);
      throw err;
    }
  };

  // Item create handler
  const handleItemCreate = async (item: Partial<GanttItem>): Promise<GanttItem> => {
    if (!apiRef.current) throw new Error('API not initialized');

    try {
      const payload = toV2ItemPayload({
        ...item,
        project_id: projectId,
      });
      const createdItem = await apiRef.current.createItem(payload);
      setState(prev => ({
        ...prev,
        items: [...prev.items, createdItem],
      }));
      return createdItem;
    } catch (err: any) {
      console.error('Failed to create item:', err);
      throw err;
    }
  };

  // Item delete handler
  const handleItemDelete = async (itemId: number) => {
    if (!apiRef.current) return;

    try {
      await apiRef.current.deleteItem(itemId);
      setState(prev => ({
        ...prev,
        items: prev.items.filter(i => i.id !== itemId),
      }));
    } catch (err: any) {
      console.error('Failed to delete item:', err);
      throw err;
    }
  };

  // Task create handler
  const handleTaskCreate = async (task: {
    schedule_item_id: number;
    title: string;
    description: string;
    assigned_to: number | null;
  }) => {
    if (!apiRef.current) return;

    try {
      const payload = toV2TaskPayload(task, task.schedule_item_id);
      await apiRef.current.createTask(task.schedule_item_id, payload);
      // Refresh to get the new task
      loadData();
    } catch (err: any) {
      console.error('Failed to create task:', err);
      throw err;
    }
  };

  // Handle item click from calendar
  const handleCalendarItemClick = (item: GanttItem) => {
    setState(prev => ({ ...prev, viewMode: 'gantt' }));
    // TODO: scroll to item in gantt view
  };

  if (state.loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-600">
          <p className="font-medium">Error loading data</p>
          <p className="text-sm">{state.error}</p>
          <button onClick={loadData} className="mt-2 px-3 py-1 bg-indigo-600 text-white rounded text-sm">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* View Switcher in top-right */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '8px 16px', borderBottom: '1px solid #e5e7eb' }}>
        <ViewSwitcher
          currentView={state.viewMode}
          onViewChange={(view) => setState(prev => ({ ...prev, viewMode: view }))}
        />
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {state.viewMode === 'gantt' ? (
          <KibrayGantt
            mode={mode}
            items={state.items}
            categories={state.categories}
            dependencies={state.dependencies}
            projectId={projectId}
            projectName={projectName}
            canEdit={canEdit}
            onItemCreate={handleItemCreate}
            onItemUpdate={handleItemUpdate}
            onItemDelete={handleItemDelete}
            onTaskCreate={handleTaskCreate}
            teamMembers={teamMembers}
          />
        ) : (
          <CalendarView
            items={state.items}
            categories={state.categories}
            onItemClick={handleCalendarItemClick}
            canEdit={canEdit}
          />
        )}
      </div>
    </div>
  );
};

// =============================================================================
// Global mount function for Django
// =============================================================================

declare global {
  interface Window {
    KibrayGantt: {
      mount: (elementId: string, config: KibrayGanttAppConfig) => void;
      unmount: (elementId: string) => void;
    };
  }
}

const mountedRoots: Map<string, ReactDOM.Root> = new Map();

window.KibrayGantt = {
  mount: (elementId: string, config: KibrayGanttAppConfig) => {
    const container = document.getElementById(elementId);
    if (!container) {
      console.error(`Element with id "${elementId}" not found`);
      return;
    }

    // Unmount if already mounted
    const existingRoot = mountedRoots.get(elementId);
    if (existingRoot) {
      existingRoot.unmount();
    }

    const root = ReactDOM.createRoot(container);
    root.render(
      <React.StrictMode>
        <KibrayGanttApp {...config} />
      </React.StrictMode>
    );

    mountedRoots.set(elementId, root);
  },

  unmount: (elementId: string) => {
    const root = mountedRoots.get(elementId);
    if (root) {
      root.unmount();
      mountedRoots.delete(elementId);
    }
  },
};

export { KibrayGanttApp, KibrayGanttAppConfig };
