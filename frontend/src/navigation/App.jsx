import React from 'react';
import { NavigationProvider, useNavigation } from '../context/NavigationContext.jsx';
import { RoleProvider } from './contexts/RoleContext.jsx';
import { ThemeProvider } from './contexts/ThemeContext.jsx';
import Sidebar from './components/Sidebar.jsx';
import Breadcrumbs from '../components/navigation/Breadcrumbs.jsx';
import PanelLauncher from '../components/navigation/PanelLauncher.jsx';
import ProjectSelector from '../components/navigation/ProjectSelector.jsx';
import DashboardPM from '../components/navigation/DashboardPM.jsx';
import SlidingPanel from '../components/navigation/SlidingPanel.jsx';
import '../styles/theme.css';
import '../styles/global.css';

const MainLayout = () => {
  const { sidebarCollapsed, panelStack } = useNavigation();
  return (
    <div className={`navigation-shell ${sidebarCollapsed ? 'collapsed' : ''}`}>      
      <Sidebar />
      <main className="navigation-main">
  <ProjectSelector />
  <PanelLauncher />
        <Breadcrumbs />
        <DashboardPM />
        {panelStack.map((p, idx) => (
          <SlidingPanel
            key={p.key || idx}
            level={idx + 1}
            title={p.title || 'Panel'}
            width={p.width || '600px'}
          >
            {p.content}
          </SlidingPanel>
        ))}
      </main>
    </div>
  );
};

const App = () => (
  <ThemeProvider>
    <RoleProvider>
      <NavigationProvider>
        <MainLayout />
      </NavigationProvider>
    </RoleProvider>
  </ThemeProvider>
);

export default App;
