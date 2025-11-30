import React, { createContext, useContext, useState, useCallback } from 'react';

const NavigationContext = createContext();

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) throw new Error('useNavigation must be within NavigationProvider');
  return context;
};

export const NavigationProvider = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => 
    localStorage.getItem('sidebar_collapsed') === 'true'
  );
  const [currentContext, setCurrentContext] = useState({
    projectId: null,
    projectName: null
  });

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => {
      const newValue = !prev;
      localStorage.setItem('sidebar_collapsed', newValue.toString());
      return newValue;
    });
  }, []);

  const updateContext = useCallback(updates => {
    setCurrentContext(prev => ({ ...prev, ...updates }));
  }, []);

  return (
    <NavigationContext.Provider value={{
      sidebarCollapsed,
      currentContext,
      toggleSidebar,
      updateContext
    }}>
      {children}
    </NavigationContext.Provider>
  );
};
