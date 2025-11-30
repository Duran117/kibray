import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage.js';

const NavigationContext = createContext();

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within NavigationProvider');
  }
  return context;
};

export const NavigationProvider = ({ children }) => {
  const [isCollapsed, setIsCollapsed] = useLocalStorage('kibray-sidebar-collapsed', false);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [notifications, setNotifications] = useState([]);

  // Fetch notifications count (mock for now)
  useEffect(() => {
    // In production, fetch from API: /api/notifications/unread/
    // For now, get from existing Django template data if available
    const notifElement = document.querySelector('[data-notifications-count]');
    if (notifElement) {
      const count = parseInt(notifElement.getAttribute('data-notifications-count'), 10);
      setNotifications(Array(count).fill({})); // Mock notifications
    }
  }, []);

  const toggleSidebar = () => {
    setIsCollapsed(prev => !prev);
  };

  const navigateTo = (section) => {
    setActiveSection(section);
  };

  const value = {
    isCollapsed,
    toggleSidebar,
    activeSection,
    navigateTo,
    notifications,
    notificationCount: notifications.length
  };

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
};
