import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

// Wait for DOM to be ready
const initNavigation = () => {
  const rootElement = document.getElementById('react-navigation-root');
  
  if (!rootElement) {
    console.error('Navigation root element not found. Add <div id="react-navigation-root"></div> to your template.');
    return;
  }

  const root = createRoot(rootElement);
  root.render(<App />);
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNavigation);
} else {
  initNavigation();
}
