import React, { useState, useEffect } from 'react';
import NotificationBell from './NotificationBell';
import ToastNotification from './ToastNotification';
import api from '../../utils/api';
import { Bell, X } from 'lucide-react';
import './NotificationCenter.css';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotifications = async () => {
    try {
      const data = await api.get('/alerts/?is_read=false');
      setNotifications(data.results || data);
      setUnreadCount(data.count || (data.results?.length || data.length));
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await api.post(`/alerts/${id}/mark_read/`);
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <div data-testid="notification-center">
      <NotificationBell 
        count={unreadCount}
        onClick={() => setIsOpen(!isOpen)}
      />
      
      {isOpen && (
        <div className="notification-panel">
          <div className="panel-header">
            <h3>Notifications</h3>
            <button onClick={() => setIsOpen(false)}>
              <X size={18} />
            </button>
          </div>
          
          <div className="notification-list">
            {notifications.length > 0 ? (
              notifications.map(notif => (
                <div 
                  key={notif.id}
                  className="notification-item"
                  onClick={() => handleMarkRead(notif.id)}
                >
                  <div className="notif-icon">
                    <Bell size={16} />
                  </div>
                  <div className="notif-content">
                    <h4>{notif.title}</h4>
                    <p>{notif.message}</p>
                    <span className="notif-time">{notif.timestamp}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="no-notifications">
                <Bell size={32} />
                <p>No new notifications</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {toast && (
        <ToastNotification 
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default NotificationCenter;
