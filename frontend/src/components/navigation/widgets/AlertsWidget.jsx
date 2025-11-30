import React from 'react';
import './AlertsWidget.css';

const AlertsWidget = ({ alerts }) => {
  return (
    <div className="widget alerts-widget">
      <div className="widget-header">
        <h4>Alerts</h4>
      </div>
      <ul className="alerts-list">
        {alerts.map(a => (
          <li key={a.id} className={`alert-item ${a.severity}`}>\n            <span className="alert-title">{a.title}</span>\n            <span className="alert-meta">{a.scope}</span>\n          </li>
        ))}
        {alerts.length === 0 && <li className="empty">No alerts</li>}
      </ul>
    </div>
  );
};

export default AlertsWidget;
