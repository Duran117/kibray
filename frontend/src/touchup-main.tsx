import React from 'react'
import ReactDOM from 'react-dom/client'
import TouchupBoard from './pages/TouchupBoard'
import './index.css'

ReactDOM.createRoot(document.getElementById('touchup-root')!).render(
  <React.StrictMode>
    <TouchupBoard />
  </React.StrictMode>,
)
