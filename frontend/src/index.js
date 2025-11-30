import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

const rootEl = document.getElementById('react-navigation-root');

if (rootEl) {
  const root = ReactDOM.createRoot(rootEl);
  root.render(<App />);
  console.log('✅ Kibray Navigation System loaded');
}
