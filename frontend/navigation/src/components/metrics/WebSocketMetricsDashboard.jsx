import React, { useState, useEffect, useRef } from 'react';
import { Activity, Users, MessageSquare, AlertCircle, Clock, TrendingUp, Zap } from 'lucide-react';
import './WebSocketMetricsDashboard.css';

/**
 * WebSocket Metrics Dashboard
 * 
 * Real-time monitoring dashboard for WebSocket connections
 * 
 * Features:
 * - Live connection count
 * - Message rate (messages/second)
 * - Latency statistics (p50, p95, p99)
 * - Error rate and recent errors
 * - Historical charts
 * - Auto-refresh every 5 seconds
 */
const WebSocketMetricsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const refreshInterval = useRef(null);

  // Fetch current metrics
  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/websocket/metrics/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }

      const data = await response.json();
      setMetrics(data);
      setError(null);
      
      // Add to history
      setHistory(prev => {
        const newHistory = [...prev, {
          timestamp: data.timestamp,
          connections: data.connections.total,
          messageRate: data.messages.rate_1m,
          latency: data.messages.latency.p50,
          errors: data.errors.rate,
        }];
        
        // Keep last 60 data points (5 minutes at 5-second intervals)
        return newHistory.slice(-60);
      });
      
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Setup auto-refresh
  useEffect(() => {
    fetchMetrics();

    if (autoRefresh) {
      refreshInterval.current = setInterval(fetchMetrics, 5000); // Every 5 seconds
    }

    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [autoRefresh]);

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setAutoRefresh(prev => !prev);
  };

  // Format uptime
  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  // Format number with decimals
  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return '0';
    return num.toFixed(decimals);
  };

  // Render loading state
  if (loading && !metrics) {
    return (
      <div className="metrics-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading metrics...</p>
      </div>
    );
  }

  // Render error state
  if (error && !metrics) {
    return (
      <div className="metrics-dashboard error">
        <AlertCircle size={48} />
        <p>Failed to load metrics: {error}</p>
        <button onClick={fetchMetrics}>Retry</button>
      </div>
    );
  }

  const {
    timestamp,
    uptime_seconds,
    connections,
    messages,
    errors,
    connection_duration,
  } = metrics || {};

  return (
    <div className="metrics-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <Activity size={32} />
          <div>
            <h1>WebSocket Metrics</h1>
            <p className="subtitle">Real-time monitoring dashboard</p>
          </div>
        </div>
        
        <div className="header-right">
          <div className="uptime-badge">
            <Clock size={16} />
            <span>Uptime: {formatUptime(uptime_seconds || 0)}</span>
          </div>
          
          <button
            className={`refresh-toggle ${autoRefresh ? 'active' : ''}`}
            onClick={toggleAutoRefresh}
          >
            <Zap size={16} />
            {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </button>
          
          <button className="refresh-btn" onClick={fetchMetrics}>
            Refresh Now
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        {/* Active Connections */}
        <div className="metric-card primary">
          <div className="metric-icon">
            <Users size={24} />
          </div>
          <div className="metric-content">
            <div className="metric-value">{connections?.total || 0}</div>
            <div className="metric-label">Active Connections</div>
          </div>
          <div className="metric-footer">
            <span>Created: {connections?.created || 0}</span>
            <span>Closed: {connections?.closed || 0}</span>
          </div>
        </div>

        {/* Message Rate */}
        <div className="metric-card success">
          <div className="metric-icon">
            <MessageSquare size={24} />
          </div>
          <div className="metric-content">
            <div className="metric-value">
              {formatNumber(messages?.rate_1m || 0, 1)}
            </div>
            <div className="metric-label">Messages/Second</div>
          </div>
          <div className="metric-footer">
            <span>5m: {formatNumber(messages?.rate_5m || 0, 1)}</span>
            <span>15m: {formatNumber(messages?.rate_15m || 0, 1)}</span>
          </div>
        </div>

        {/* Latency */}
        <div className="metric-card info">
          <div className="metric-icon">
            <TrendingUp size={24} />
          </div>
          <div className="metric-content">
            <div className="metric-value">
              {formatNumber(messages?.latency?.p50 || 0, 0)}ms
            </div>
            <div className="metric-label">Latency (p50)</div>
          </div>
          <div className="metric-footer">
            <span>p95: {formatNumber(messages?.latency?.p95 || 0, 0)}ms</span>
            <span>p99: {formatNumber(messages?.latency?.p99 || 0, 0)}ms</span>
          </div>
        </div>

        {/* Errors */}
        <div className="metric-card danger">
          <div className="metric-icon">
            <AlertCircle size={24} />
          </div>
          <div className="metric-content">
            <div className="metric-value">{errors?.rate || 0}</div>
            <div className="metric-label">Errors/Minute</div>
          </div>
          <div className="metric-footer">
            <span>Total: {errors?.total || 0}</span>
          </div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="stats-grid">
        {/* Latency Details */}
        <div className="stat-card">
          <h3>Latency Statistics</h3>
          <div className="stat-rows">
            <div className="stat-row">
              <span>Average:</span>
              <strong>{formatNumber(messages?.latency?.avg || 0, 1)}ms</strong>
            </div>
            <div className="stat-row">
              <span>Minimum:</span>
              <strong>{formatNumber(messages?.latency?.min || 0, 1)}ms</strong>
            </div>
            <div className="stat-row">
              <span>Maximum:</span>
              <strong>{formatNumber(messages?.latency?.max || 0, 1)}ms</strong>
            </div>
            <div className="stat-row">
              <span>Samples:</span>
              <strong>{messages?.latency?.count || 0}</strong>
            </div>
          </div>
        </div>

        {/* Connection Duration */}
        <div className="stat-card">
          <h3>Connection Duration</h3>
          <div className="stat-rows">
            <div className="stat-row">
              <span>Average:</span>
              <strong>{formatNumber(connection_duration?.avg || 0, 1)}s</strong>
            </div>
            <div className="stat-row">
              <span>Median:</span>
              <strong>{formatNumber(connection_duration?.median || 0, 1)}s</strong>
            </div>
            <div className="stat-row">
              <span>Minimum:</span>
              <strong>{formatNumber(connection_duration?.min || 0, 1)}s</strong>
            </div>
            <div className="stat-row">
              <span>Maximum:</span>
              <strong>{formatNumber(connection_duration?.max || 0, 1)}s</strong>
            </div>
          </div>
        </div>

        {/* Errors by Type */}
        <div className="stat-card">
          <h3>Errors by Type</h3>
          <div className="stat-rows">
            {errors?.by_type && Object.keys(errors.by_type).length > 0 ? (
              Object.entries(errors.by_type).map(([type, count]) => (
                <div key={type} className="stat-row">
                  <span>{type}:</span>
                  <strong>{count}</strong>
                </div>
              ))
            ) : (
              <div className="stat-row empty">
                <span>No errors recorded</span>
              </div>
            )}
          </div>
        </div>

        {/* Connections by User */}
        <div className="stat-card">
          <h3>Top Users (by connections)</h3>
          <div className="stat-rows">
            {connections?.by_user && Object.keys(connections.by_user).length > 0 ? (
              Object.entries(connections.by_user)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([userId, count]) => (
                  <div key={userId} className="stat-row">
                    <span>User {userId}:</span>
                    <strong>{count}</strong>
                  </div>
                ))
            ) : (
              <div className="stat-row empty">
                <span>No active connections</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Errors */}
      {errors?.recent && errors.recent.length > 0 && (
        <div className="errors-section">
          <h3>Recent Errors</h3>
          <div className="errors-list">
            {errors.recent.slice(0, 10).map((error, index) => (
              <div key={index} className="error-item">
                <div className="error-type">{error.type}</div>
                <div className="error-message">{error.message}</div>
                <div className="error-timestamp">
                  {new Date(error.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simple Line Chart (using div-based chart) */}
      {history.length > 0 && (
        <div className="chart-section">
          <h3>Connection History (Last 5 minutes)</h3>
          <div className="simple-chart">
            {history.map((point, index) => (
              <div
                key={index}
                className="chart-bar"
                style={{
                  height: `${Math.min((point.connections / Math.max(...history.map(h => h.connections))) * 100, 100)}%`,
                }}
                title={`${point.connections} connections`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="dashboard-footer">
        <p>Last updated: {timestamp ? new Date(timestamp).toLocaleString() : 'Never'}</p>
        <p>Auto-refresh: {autoRefresh ? 'Every 5 seconds' : 'Disabled'}</p>
      </div>
    </div>
  );
};

export default WebSocketMetricsDashboard;
