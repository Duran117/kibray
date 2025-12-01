import React, { useState } from 'react';
import { useNavigation } from '../../context/NavigationContext.jsx';
import { useRole } from '../../context/RoleContext.jsx';
import { useTheme } from '../../context/ThemeContext.jsx';
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  LayoutDashboard,
  FolderKanban,
  Calendar,
  CheckSquare,
  Package,
  MessageSquare,
  FileText,
  DollarSign,
  Users,
  Settings,
  Clock,
  Moon,
  Sun
} from 'lucide-react';
import './Sidebar.css';

const iconMap = {
  'layout-dashboard': LayoutDashboard,
  'folder-kanban': FolderKanban,
  'calendar': Calendar,
  'check-square': CheckSquare,
  'package': Package,
  'message-square': MessageSquare,
  'file-text': FileText,
  'dollar-sign': DollarSign,
  'users': Users,
  'settings': Settings,
  'clock': Clock
};

const Sidebar = () => {
  const { sidebarCollapsed, toggleSidebar, currentContext } = useNavigation();
  const { getSidebarMenu } = useRole();
  const { theme, toggleTheme, isDark } = useTheme();
  const [expandedMenus, setExpandedMenus] = useState({});

  const menu = getSidebarMenu();

  const toggleSubmenu = id => setExpandedMenus(prev => ({ ...prev, [id]: !prev[id] }));

  const handleMenuClick = item => {
    if (item.submenu) {
      toggleSubmenu(item.id);
    } else if (item.route) {
      window.location.href = item.route;
    }
  };

  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!sidebarCollapsed && (
          <div className="sidebar-logo">
            <span className="logo-icon">🏗️</span>
            <h1 className="logo-text">KIBRAY</h1>
          </div>
        )}
        <button className="sidebar-toggle" onClick={toggleSidebar}>
          {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {!sidebarCollapsed && currentContext.projectName && (
        <div className="sidebar-context">
          <div className="context-label">Current Project</div>
          <div className="context-value">{currentContext.projectName}</div>
        </div>
      )}

      <nav className="sidebar-nav">
        {menu.map(item => {
          const Icon = iconMap[item.icon] || FolderKanban;
          const isExpanded = expandedMenus[item.id];

          return (
            <div key={item.id} className="menu-item">
              <button className="menu-button" onClick={() => handleMenuClick(item)}>
                <Icon size={20} />
                {!sidebarCollapsed && (
                  <>
                    <span className="menu-label">{item.label}</span>
                    {item.submenu && (
                      <ChevronDown
                        size={16}
                        className={`submenu-arrow ${isExpanded ? 'expanded' : ''}`}
                      />
                    )}
                  </>
                )}
              </button>

              {!sidebarCollapsed && item.submenu && isExpanded && (
                <div className="submenu">
                  {item.submenu.map(sub => (
                    <a key={sub.id} href={sub.route} className="submenu-item">
                      <span className="submenu-dot"></span>
                      {sub.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={toggleTheme}>
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
          {!sidebarCollapsed && <span>{isDark ? 'Light' : 'Dark'} Mode</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
