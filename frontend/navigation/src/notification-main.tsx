import React from 'react'
import ReactDOM from 'react-dom/client'
import NotificationCenter from './components/NotificationCenter'
import './index.css'

ReactDOM.createRoot(document.getElementById('notification-root')!).render(
  <React.StrictMode>
    <NotificationCenter />
  </React.StrictMode>,
)
