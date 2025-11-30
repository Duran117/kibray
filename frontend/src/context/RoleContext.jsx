import React, { createContext, useContext, useState, useEffect } from 'react';
import { getRoleConfig } from '../utils/rolePermissions.js';

const RoleContext = createContext();

export const useRole = () => {
  const context = useContext(RoleContext);
  if (!context) throw new Error('useRole must be within RoleProvider');
  return context;
};

export const RoleProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [roleConfig, setRoleConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userDataEl = document.getElementById('user-data');
    if (userDataEl) {
      try {
        const data = JSON.parse(userDataEl.textContent);
        setUser(data);
        setRole(data.role);
        setRoleConfig(getRoleConfig(data.role));
      } catch (e) {
        console.error('Error parsing user data:', e);
      }
    }
    setLoading(false);
  }, []);

  const getSidebarMenu = () => roleConfig?.sidebarMenu || [];

  return (
    <RoleContext.Provider value={{
      user,
      role,
      loading,
      getSidebarMenu
    }}>
      {loading ? <div>Loading...</div> : children}
    </RoleContext.Provider>
  );
};
