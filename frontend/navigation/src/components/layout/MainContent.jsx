import React, { useState, useEffect } from 'react';
import FileManager from '../files/FileManager';
import UserManagement from '../users/UserManagement';
import CalendarView from '../calendar/CalendarView';
import TimelineView from '../calendar/TimelineView';
import ChatPanel from '../chat/ChatPanel';
import NotificationCenter from '../notifications/NotificationCenter';
import GlobalSearch from '../search/GlobalSearch';
import ReportGenerator from '../reports/ReportGenerator';
import './MainContent.css';

const MainContent = () => {
  const [currentView, setCurrentView] = useState('dashboard');

  // Listen for navigation changes from sidebar
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      const path = hash.split('/')[0];
      if (path) {
        setCurrentView(path);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange(); // Initial load

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'files':
        return <FileManager />;
      case 'users':
        return <UserManagement />;
      case 'calendar':
        return <CalendarView />;
      case 'timeline':
        return <TimelineView />;
      case 'chat':
        return <ChatPanel />;
      case 'reports':
        return <ReportGenerator />;
      case 'dashboard':
      default:
        return (
          <div className="dashboard-placeholder">
            <h1>Dashboard</h1>
            <p>Navigate using the sidebar to access different features</p>
            <div className="feature-cards">
              <div className="feature-card" onClick={() => window.location.hash = '#files'}>
                <h3>📁 File Manager</h3>
                <p>Upload, organize, and manage project files</p>
              </div>
              <div className="feature-card" onClick={() => window.location.hash = '#users'}>
                <h3>👥 User Management</h3>
                <p>Invite users and manage permissions</p>
              </div>
              <div className="feature-card" onClick={() => window.location.hash = '#calendar'}>
                <h3>📅 Calendar</h3>
                <p>View project schedule and timeline</p>
              </div>
              <div className="feature-card" onClick={() => window.location.hash = '#chat'}>
                <h3>💬 Team Chat</h3>
                <p>Communicate with your team</p>
              </div>
              <div className="feature-card" onClick={() => window.location.hash = '#reports'}>
                <h3>📊 Reports</h3>
                <p>Generate and export project reports</p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="main-content">
      {renderView()}
      <NotificationCenter />
      <GlobalSearch />
    </div>
  );
};

export default MainContent;
