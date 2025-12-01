import React, { useState, useEffect } from 'react';
import { FileText, Clock, CheckCircle, XCircle, GripVertical, DollarSign, ThumbsUp, ThumbsDown } from 'lucide-react';
import * as api from '../../../utils/api';
import './ChangeOrdersWidget.css';

const ChangeOrdersWidget = ({ projectId }) => {
  const [changeOrders, setChangeOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchChangeOrders();
  }, [projectId]);

  const fetchChangeOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('ordering', '-submitted_date');
      if (projectId) {
        params.append('project', projectId);
      }
      const data = await api.get(`/changeorders/?${params.toString()}`);
      setChangeOrders(data.results || data);
    } catch (err) {
      console.error('Error fetching change orders:', err);
      setChangeOrders([]);
      setError('Failed to load change orders');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (coId) => {
    try {
      await api.post(`/changeorders/${coId}/approve/`, { notes: 'Approved' });
      fetchChangeOrders();
    } catch (err) {
      console.error('Error approving change order:', err);
    }
  };

  const handleReject = async (coId) => {
    try {
      await api.post(`/changeorders/${coId}/reject/`, { notes: 'Rejected' });
      fetchChangeOrders();
    } catch (err) {
      console.error('Error rejecting change order:', err);
    }
  };

  const getStatusIcon = (status) => {
    const lowerStatus = (status || '').toLowerCase();
    if (lowerStatus === 'approved' || lowerStatus === 'aprobada') {
      return <CheckCircle size={18} className="status-approved" />;
    } else if (lowerStatus === 'rejected' || lowerStatus === 'rechazada') {
      return <XCircle size={18} className="status-rejected" />;
    } else {
      return <Clock size={18} className="status-pending" />;
    }
  };

  const formatCurrency = (amount) => 
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount);

  return (
    <div className="changeorders-widget">
      <div className="widget-drag-handle">
        <GripVertical size={16} />
      </div>
      
      <div className="widget-header">
        <h3 className="widget-title">
          <FileText size={20} />
          Change Orders
        </h3>
      </div>

      <div className="changeorders-list">
        {loading ? (
          <div className="changeorders-loading">
            <div className="spinner"></div>
            <p>Loading change orders...</p>
          </div>
        ) : error ? (
          <div className="changeorders-error">
            <XCircle size={24} />
            <p>{error}</p>
            <button onClick={fetchChangeOrders} className="retry-btn">Retry</button>
          </div>
        ) : changeOrders.length > 0 ? (
          changeOrders.map((co) => (
            <div
              key={co.id}
              className={`changeorder-item status-${(co.status || '').toLowerCase()}`}
            >
              <div className="changeorder-header">
                <div className="changeorder-number">{co.reference_code || `CO-${co.id}`}</div>
                <div className="changeorder-status">
                  {getStatusIcon(co.status)}
                  <span>{co.status}</span>
                </div>
              </div>
              <p className="changeorder-description">{co.title || co.description}</p>
              <div className="changeorder-footer">
                <div className="changeorder-amount">
                  <DollarSign size={14} />
                  <span>{formatCurrency(co.amount || 0)}</span>
                </div>
                <div className="changeorder-date">{new Date(co.submitted_date || co.created_at).toLocaleDateString()}</div>
              </div>
              {(co.status || '').toLowerCase() === 'pending' && (
                <div className="changeorder-actions">
                  <button onClick={() => handleApprove(co.id)} className="btn-approve" title="Approve">
                    <ThumbsUp size={14} /> Approve
                  </button>
                  <button onClick={() => handleReject(co.id)} className="btn-reject" title="Reject">
                    <ThumbsDown size={14} /> Reject
                  </button>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="no-changeorders">
            <FileText size={24} />
            <p>No change orders</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChangeOrdersWidget;
