import React from 'react';
import { NavigationProvider } from './contexts/NavigationContext.jsx';
import { RoleProvider } from './contexts/RoleContext.jsx';
import { ThemeProvider } from './contexts/ThemeContext.jsx';
import Sidebar from './components/Sidebar.jsx';
import './styles/theme.css';
import './styles/global.css';

const App = () => {
  return (
    <ThemeProvider>
      <RoleProvider>
        <NavigationProvider>
          <div className="kibray-navigation">
            <Sidebar />
          </div>
        </NavigationProvider>
      </RoleProvider>
    </ThemeProvider>
  );
};

export default App;
