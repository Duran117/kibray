import React, { createContext, useContext, useState, useCallback } from 'react';

const NavigationContext = createContext();

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) throw new Error('useNavigation must be within NavigationProvider');
  return context;
};

export const NavigationProvider = ({ children }) => {
  // Sidebar state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true');

  // Global navigation context (e.g. selected project)
  const [currentContext, setCurrentContext] = useState({ projectId: null, projectName: null });

  // Sliding panels stack (each item: { key, title, content, width })
  const [panelStack, setPanelStack] = useState([]);

  // Breadcrumbs (each item: { label, path })
  const [breadcrumbs, setBreadcrumbs] = useState([{ label: 'Dashboard', path: '/' }]);

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

  // Panels API
  const openPanel = useCallback(panel => {
    setPanelStack(prev => [...prev, panel]);
  }, []);

  const closePanel = useCallback(() => {
    setPanelStack(prev => prev.slice(0, -1));
  }, []);

  const closeAllPanels = useCallback(() => setPanelStack([]), []);

  // Breadcrumbs API
  const pushBreadcrumb = useCallback((label, path = null) => {
    setBreadcrumbs(prev => {
      // Avoid duplicates if last breadcrumb matches
      if (prev.length && prev[prev.length - 1].label === label) return prev;
      return [...prev, { label, path }];
    });
  }, []);

  const navigateToBreadcrumb = useCallback(index => {
    setBreadcrumbs(prev => prev.slice(0, index + 1));
  }, []);

  const currentPanel = panelStack[panelStack.length - 1] || null;

  return (
    <NavigationContext.Provider
      value={{
        // Sidebar
        sidebarCollapsed,
        toggleSidebar,
        // Context
        currentContext,
        updateContext,
        // Panels
        panelStack,
        openPanel,
        closePanel,
        closeAllPanels,
        currentPanel,
        // Breadcrumbs
        breadcrumbs,
        pushBreadcrumb,
        navigateToBreadcrumb
      }}
    >
      {children}
    </NavigationContext.Provider>
  );
};
