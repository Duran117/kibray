import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Get project ID from data attribute on root element
const rootElement = document.getElementById('gantt-root');
if (!rootElement) {
  throw new Error('Root element #gantt-root not found');
}

const projectId = rootElement.getAttribute('data-project-id');
if (!projectId) {
  throw new Error('Project ID not provided in data-project-id attribute');
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App projectId={parseInt(projectId, 10)} />
  </React.StrictMode>
);

// Mark mounted for E2E stability (redundant with App instrumentation but immediate)
rootElement.setAttribute('data-mounted', '1');
