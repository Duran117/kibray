import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../utils/formatDate';

interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  related_object_type?: string;
  related_object_id?: number;
}

export default function NotificationCenter() {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPanel, setShowPanel] = useState(false);

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/notifications/', {
        headers: {
          Accept: 'application/json',
        },
        credentials: 'include', // Use Django session cookies
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setNotifications(data.results || data);
    } catch (e: any) {
  setError(e.message || t('errors.server_error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const res = await fetch('/api/v1/notifications/count_unread/', {
        headers: {
          Accept: 'application/json',
        },
        credentials: 'include', // Use Django session cookies
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setUnreadCount(data.unread_count || 0);
    } catch (e: any) {
      console.error('Error fetching unread count:', e);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  const markRead = async (id: number) => {
    try {
      await fetch(`/api/v1/notifications/${id}/mark_read/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (e: any) {
      console.error('Error marking as read:', e);
    }
  };

  const markAllRead = async () => {
    try {
      await fetch('/api/v1/notifications/mark_all_read/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e: any) {
      console.error('Error marking all as read:', e);
    }
  };

  const togglePanel = () => {
    if (!showPanel) fetchNotifications();
    setShowPanel(!showPanel);
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={togglePanel}
        style={{
          position: 'relative',
          background: '#fff',
          border: '1px solid #ddd',
          borderRadius: 8,
          padding: '8px 12px',
          cursor: 'pointer',
        }}
      >
        🔔
        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: -4,
              right: -4,
              background: 'red',
              color: '#fff',
              borderRadius: '50%',
              padding: '2px 6px',
              fontSize: 10,
              fontWeight: 'bold',
            }}
          >
            {unreadCount}
          </span>
        )}
      </button>

      {showPanel && (
        <div
          style={{
            position: 'absolute',
            top: 40,
            right: 0,
            width: 400,
            maxHeight: 500,
            background: '#fff',
            border: '1px solid #ddd',
            borderRadius: 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 1000,
            overflow: 'hidden',
          }}
        >
          <div style={{ padding: 12, borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between' }}>
            <strong>{t('notifications.title')}</strong>
            <button onClick={markAllRead} style={{ fontSize: 12 }}>
              {t('notifications.mark_all_read')}
            </button>
          </div>
          {error && <div style={{ padding: 12, color: 'red' }}>{error}</div>}
          <div style={{ maxHeight: 440, overflowY: 'auto' }}>
            {loading && <div style={{ padding: 12 }}>{t('common.loading')}</div>}
            {!loading && notifications.length === 0 && <div style={{ padding: 12, color: '#999' }}>{t('notifications.unread_count_zero')}</div>}
            {notifications.map((n) => (
              <div
                key={n.id}
                style={{
                  padding: 12,
                  borderBottom: '1px solid #eee',
                  background: n.is_read ? '#fff' : '#f0f8ff',
                  cursor: 'pointer',
                }}
                onClick={() => !n.is_read && markRead(n.id)}
              >
                <div style={{ fontWeight: n.is_read ? 'normal' : 'bold', fontSize: 14 }}>{n.title}</div>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>{n.message}</div>
                <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>{formatDate(n.created_at)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
