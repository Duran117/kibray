import React from 'react'
import ReactDOM from 'react-dom/client'
import TouchupBoard from './pages/TouchupBoard'
import './index.css'

const root = document.getElementById('touchup-root');
if (root) {
  console.log('[TouchupBoard] Root element found, mounting React app');
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <TouchupBoard />
    </React.StrictMode>,
  );
} else {
  console.error('[TouchupBoard] ERROR: #touchup-root element not found at script execution');
}
