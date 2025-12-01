import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle, GripVertical } from 'lucide-react';
import * as api from '../../../utils/api';
import './AlertsWidget.css';

const AlertsWidget = ({ projectId }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAlerts();
  }, [projectId]);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('ordering', '-created_at');
      if (projectId) {
        params.append('project', projectId);
      }
      const data = await api.get(`/alerts/?${params.toString()}`);
      setAlerts(data.results || data);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setAlerts([]);
      setError('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (alertId) => {
    try {
      await api.post(`/alerts/${alertId}/mark_read/`);
      fetchAlerts();
    } catch (err) {
      console.error('Error marking alert as read:', err);
    }
  };

  const getAlertIcon = (type) => {
    const lowerType = (type || '').toLowerCase();
    if (lowerType.includes('error') || lowerType === 'danger') {
      return <AlertCircle size={20} />;
    } else if (lowerType.includes('warning')) {
      return <AlertTriangle size={20} />;
    } else if (lowerType.includes('success')) {
      return <CheckCircle size={20} />;
    } else {
      return <Info size={20} />;
    }
  };

  return (
    <div className="alerts-widget">
      <div className="widget-drag-handle">
        <GripVertical size={16} />
      </div>
      
      <div className="widget-header">
        <h3 className="widget-title">Recent Alerts</h3>
        {alerts.length > 0 && (
          <span className="alert-count">{alerts.length}</span>
        )}
      </div>

      <div className="alerts-list">
        {loading ? (
          <div className="alerts-loading">
            <div className="spinner"></div>
            <p>Loading alerts...</p>
          </div>
        ) : error ? (
          <div className="alerts-error">
            <AlertCircle size={24} />
            <p>{error}</p>
            <button onClick={fetchAlerts} className="retry-btn">Retry</button>
          </div>
        ) : alerts.length > 0 ? (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-item alert-${alert.type || 'info'}`}
              onClick={() => handleMarkRead(alert.id)}
              style={{ cursor: 'pointer' }}
            >
              <div className="alert-icon">
                {getAlertIcon(alert.type)}
              </div>
              <div className="alert-content">
                <h4 className="alert-title">{alert.title}</h4>
                <p className="alert-message">{alert.message}</p>
                <span className="alert-timestamp">{new Date(alert.created_at || alert.timestamp).toLocaleString()}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="no-alerts">
            <Info size={24} />
            <p>No alerts at this time</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsWidget;
