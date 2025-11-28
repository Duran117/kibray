import React from 'react'
import ReactDOM from 'react-dom/client'
import PMAssignments from './pages/PMAssignments'
import './index.css'

ReactDOM.createRoot(document.getElementById('pm-assignments-root')!).render(
  <React.StrictMode>
    <PMAssignments />
  </React.StrictMode>,
)
