import React from 'react';
import { NavigationProvider } from './context/NavigationContext.jsx';
import { RoleProvider } from './context/RoleContext.jsx';
import { ThemeProvider } from './context/ThemeContext.jsx';
import Sidebar from './components/navigation/Sidebar.jsx';
import './styles/global.css';

function App() {
  return (
    <ThemeProvider>
      <RoleProvider>
        <NavigationProvider>
          <Sidebar />
        </NavigationProvider>
      </RoleProvider>
    </ThemeProvider>
  );
}

export default App;
