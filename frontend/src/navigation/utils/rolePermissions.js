export const rolePermissions = {
  admin: {
    label: 'Administrator',
    sections: [
      { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', path: '/' },
      { id: 'projects', label: 'Projects', icon: 'Briefcase', path: '/projects/' },
      { id: 'clients', label: 'Clients', icon: 'Users', path: '/clients/' },
      { id: 'schedule', label: 'Schedule', icon: 'Calendar', path: '/schedule/' },
      { id: 'timesheet', label: 'Timesheet', icon: 'Clock', path: '/timesheet/' },
      { id: 'reports', label: 'Reports', icon: 'FileText', path: '/reports/' },
      { id: 'financial', label: 'Financial', icon: 'DollarSign', path: '/financial/' },
      { id: 'employees', label: 'Employees', icon: 'UserCog', path: '/employees/' },
      { id: 'notifications', label: 'Notifications', icon: 'Bell', path: '/notifications/' },
      { id: 'settings', label: 'Settings', icon: 'Settings', path: '/settings/' }
    ]
  },
  pm: {
    label: 'Project Manager',
    sections: [
      { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', path: '/' },
      { id: 'projects', label: 'Projects', icon: 'Briefcase', path: '/projects/' },
      { id: 'clients', label: 'Clients', icon: 'Users', path: '/clients/' },
      { id: 'schedule', label: 'Schedule', icon: 'Calendar', path: '/schedule/' },
      { id: 'timesheet', label: 'Timesheet', icon: 'Clock', path: '/timesheet/' },
      { id: 'reports', label: 'Reports', icon: 'FileText', path: '/reports/' },
      { id: 'notifications', label: 'Notifications', icon: 'Bell', path: '/notifications/' },
      { id: 'settings', label: 'Settings', icon: 'Settings', path: '/settings/' }
    ]
  },
  client: {
    label: 'Client',
    sections: [
      { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', path: '/' },
      { id: 'projects', label: 'My Projects', icon: 'Briefcase', path: '/projects/' },
      { id: 'reports', label: 'Reports', icon: 'FileText', path: '/reports/' },
      { id: 'notifications', label: 'Notifications', icon: 'Bell', path: '/notifications/' },
      { id: 'settings', label: 'Settings', icon: 'Settings', path: '/settings/' }
    ]
  },
  employee: {
    label: 'Employee',
    sections: [
      { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', path: '/' },
      { id: 'schedule', label: 'My Schedule', icon: 'Calendar', path: '/schedule/' },
      { id: 'timesheet', label: 'Timesheet', icon: 'Clock', path: '/timesheet/' },
      { id: 'notifications', label: 'Notifications', icon: 'Bell', path: '/notifications/' }
    ]
  }
};

export const getSectionsForRole = (role) => {
  return rolePermissions[role]?.sections || rolePermissions.pm.sections;
};

export const getRoleLabel = (role) => {
  return rolePermissions[role]?.label || 'Project Manager';
};

export const hasAccess = (role, sectionId) => {
  const sections = getSectionsForRole(role);
  return sections.some(section => section.id === sectionId);
};
