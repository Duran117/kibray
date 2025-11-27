import React from 'react';
import ReactDOM from 'react-dom/client';
import Dashboard from './pages/Dashboard';
import './index.css';

const rootElement = document.getElementById('dashboard-root');
if (!rootElement) {
  throw new Error('Root element #dashboard-root not found');
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <Dashboard />
  </React.StrictMode>
);
