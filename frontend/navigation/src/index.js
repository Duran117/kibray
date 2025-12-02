import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './i18n';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const rootEl = document.getElementById('react-navigation-root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl);
  root.render(<App />);
  console.log('✅ Kibray Navigation System loaded successfully');
} else {
  console.error('❌ Navigation root element not found');
}

// Register service worker for PWA functionality
serviceWorkerRegistration.register({
  onSuccess: (registration) => {
    console.log('✅ App is ready for offline use');
  },
  onUpdate: (registration) => {
    console.log('🔄 New content available, please refresh');
    // Optionally show a toast/banner to user
    if (window.confirm('New version available! Reload to update?')) {
      registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }
});

