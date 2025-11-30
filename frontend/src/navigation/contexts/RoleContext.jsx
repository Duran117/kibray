import React, { createContext, useContext, useState, useEffect } from 'react';

const RoleContext = createContext();

export const useRole = () => {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within RoleProvider');
  }
  return context;
};

export const RoleProvider = ({ children }) => {
  const [user, setUser] = useState({ id: 0, username: '', role: 'pm' });

  useEffect(() => {
    // Get user data from Django template
    const userDataElement = document.getElementById('user-data');
    if (userDataElement) {
      try {
        const userData = JSON.parse(userDataElement.textContent);
        setUser({
          id: userData.id || 0,
          username: userData.username || '',
          role: userData.role || 'pm'
        });
      } catch (error) {
        console.error('Failed to parse user data:', error);
      }
    }
  }, []);

  const hasPermission = (permission) => {
    // Permission check logic based on role
    const rolePermissions = {
      admin: ['all'],
      pm: ['projects', 'schedule', 'reports', 'notifications', 'settings'],
      client: ['projects', 'reports', 'notifications'],
      employee: ['schedule', 'timesheet', 'notifications']
    };

    const userPermissions = rolePermissions[user.role] || [];
    return userPermissions.includes('all') || userPermissions.includes(permission);
  };

  const value = {
    user,
    role: user.role,
    hasPermission,
    isAdmin: user.role === 'admin',
    isPM: user.role === 'pm',
    isClient: user.role === 'client',
    isEmployee: user.role === 'employee'
  };

  return (
    <RoleContext.Provider value={value}>
      {children}
    </RoleContext.Provider>
  );
};
