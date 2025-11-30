export const getRoleConfig = role => {
  const configs = {
    pm: {
      sidebarMenu: [
        { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', route: '/dashboard/pm' },
        { id: 'projects', label: 'My Projects', icon: 'folder-kanban', route: '/projects' },
        {
          id: 'planning',
          label: 'Planning',
          icon: 'calendar',
          submenu: [
            { id: 'daily-plans', label: 'Daily Plans', route: '/planning' },
            { id: 'daily-logs', label: 'Daily Logs', route: '/daily-logs' }
          ]
        },
        { id: 'tasks', label: 'Tasks', icon: 'check-square', route: '/tasks' },
        { id: 'changeorders', label: 'Change Orders', icon: 'file-text', route: '/changeorders/board' },
        {
          id: 'materials',
          label: 'Materials',
          icon: 'package',
          submenu: [
            { id: 'mat-request', label: 'Request', route: '/materials/request' },
            { id: 'mat-inventory', label: 'Inventory', route: '/inventory' }
          ]
        },
        { id: 'chat', label: 'Team Chat', icon: 'message-square', route: '/chat' }
      ]
    },
    admin: {
      sidebarMenu: [
        { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', route: '/dashboard/admin' },
        { id: 'projects', label: 'All Projects', icon: 'folder-kanban', route: '/projects' },
        {
          id: 'financial',
          label: 'Financial',
          icon: 'dollar-sign',
          submenu: [
            { id: 'invoices', label: 'Invoices', route: '/invoices' }
          ]
        },
        { id: 'settings', label: 'Settings', icon: 'settings', route: '/admin-panel' }
      ]
    },
    client: {
      sidebarMenu: [
        { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', route: '/dashboard/client' },
        { id: 'projects', label: 'My Projects', icon: 'folder-kanban', route: '/projects' },
        { id: 'invoices', label: 'Invoices', icon: 'file-text', route: '/invoices' },
        { id: 'chat', label: 'Messages', icon: 'message-square', route: '/chat' }
      ]
    },
    employee: {
      sidebarMenu: [
        { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', route: '/dashboard/employee' },
        { id: 'checkin', label: 'Check In/Out', icon: 'clock', route: '/check-in' },
        { id: 'tasks', label: 'My Tasks', icon: 'check-square', route: '/tasks/my' },
        { id: 'chat', label: 'Team Chat', icon: 'message-square', route: '/chat' }
      ]
    }
  };
  return configs[role] || configs.pm;
};
