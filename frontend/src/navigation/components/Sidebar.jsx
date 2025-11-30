import React from 'react';
import * as Icons from 'lucide-react';
// Updated to use consolidated NavigationContext (Phase 3)
import { useNavigation } from '../../context/NavigationContext.jsx';
import { useRole } from '../contexts/RoleContext.jsx';
import { useTheme } from '../contexts/ThemeContext.jsx';
import { getSectionsForRole, getRoleLabel } from '../utils/rolePermissions.js';
import './Sidebar.css';

const Sidebar = () => {
  const { isCollapsed, toggleSidebar, activeSection, navigateTo, notificationCount } = useNavigation();
  const { user, role } = useRole();
  const { theme, toggleTheme, isDark } = useTheme();

  const sections = getSectionsForRole(role);
  const roleLabel = getRoleLabel(role);

  const handleNavigation = (section) => {
    navigateTo(section.id);
    window.location.href = section.path;
  };

  const renderIcon = (iconName, size = 20) => {
    const IconComponent = Icons[iconName];
    return IconComponent ? <IconComponent size={size} /> : null;
  };

  return (
    <aside className={`sidebar ${isCollapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Header */}
      <div className="sidebar__header">
        <div className="sidebar__logo">
          {renderIcon('Hammer', 24)}
          {!isCollapsed && <span className="sidebar__brand">Kibray</span>}
        </div>
        <button 
          className="sidebar__toggle"
          onClick={toggleSidebar}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {renderIcon(isCollapsed ? 'ChevronRight' : 'ChevronLeft', 20)}
        </button>
      </div>

      {/* User Info */}
      {!isCollapsed && (
        <div className="sidebar__user">
          <div className="sidebar__user-avatar">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <div className="sidebar__user-info">
            <div className="sidebar__user-name">{user.username}</div>
            <div className="sidebar__user-role">{roleLabel}</div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="sidebar__nav">
        <ul className="sidebar__menu">
          {sections.map(section => {
            const isActive = activeSection === section.id;
            const hasNotifications = section.id === 'notifications' && notificationCount > 0;

            return (
              <li key={section.id} className="sidebar__menu-item">
                <a
                  href={section.path}
                  className={`sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation(section);
                  }}
                  title={isCollapsed ? section.label : undefined}
                >
                  <span className="sidebar__link-icon">
                    {renderIcon(section.icon, 20)}
                  </span>
                  {!isCollapsed && (
                    <>
                      <span className="sidebar__link-label">{section.label}</span>
                      {hasNotifications && (
                        <span className="sidebar__link-badge">{notificationCount}</span>
                      )}
                    </>
                  )}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="sidebar__footer">
        <button
          className="sidebar__theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
          title={isCollapsed ? (isDark ? 'Light mode' : 'Dark mode') : undefined}
        >
          <span className="sidebar__link-icon">
            {renderIcon(isDark ? 'Sun' : 'Moon', 20)}
          </span>
          {!isCollapsed && (
            <span className="sidebar__link-label">
              {isDark ? 'Light Mode' : 'Dark Mode'}
            </span>
          )}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
