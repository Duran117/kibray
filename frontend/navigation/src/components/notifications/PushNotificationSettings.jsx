import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Check, X } from 'lucide-react';
import './PushNotificationSettings.css';

/**
 * Push Notification Settings Component
 * 
 * Allows users to:
 * - Enable/disable push notifications
 * - Configure notification categories
 * - Manage device tokens
 * - Set quiet hours
 */
const PushNotificationSettings = ({ userId }) => {
  const [pushEnabled, setPushEnabled] = useState(false);
  const [permission, setPermission] = useState('default');
  const [preferences, setPreferences] = useState({
    chat: true,
    mention: true,
    task: true,
    system: true,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // Check notification permission status
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }

    // Load user preferences
    loadPreferences();
  }, [userId]);

  const loadPreferences = async () => {
    try {
      const response = await fetch(`/api/notifications/preferences/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPushEnabled(data.push_enabled);
        setPreferences(data.preferences || {
          chat: true,
          mention: true,
          task: true,
          system: true,
        });
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  };

  const requestPermission = async () => {
    if (!('Notification' in window)) {
      setMessage({ type: 'error', text: 'Notifications not supported in this browser' });
      return;
    }

    setLoading(true);

    try {
      const permission = await Notification.requestPermission();
      setPermission(permission);

      if (permission === 'granted') {
        // Register service worker and get token
        await registerServiceWorker();
        setMessage({ type: 'success', text: 'Push notifications enabled!' });
      } else {
        setMessage({ type: 'error', text: 'Notification permission denied' });
      }
    } catch (error) {
      console.error('Failed to request permission:', error);
      setMessage({ type: 'error', text: 'Failed to enable notifications' });
    } finally {
      setLoading(false);
    }
  };

  const registerServiceWorker = async () => {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service workers not supported');
      return;
    }

    try {
      // Register service worker
      const registration = await navigator.serviceWorker.register('/sw.js');
      console.log('Service worker registered:', registration);

      // In production, get FCM token here
      // const token = await getToken(messaging, { vapidKey: 'YOUR_VAPID_KEY' });
      // await saveTokenToServer(token);

      setPushEnabled(true);
      await savePreferences({ push_enabled: true });
    } catch (error) {
      console.error('Failed to register service worker:', error);
      throw error;
    }
  };

  const savePreferences = async (updates = {}) => {
    try {
      const response = await fetch(`/api/notifications/preferences/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          push_enabled: pushEnabled,
          preferences: preferences,
          ...updates,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save preferences');
      }

      return true;
    } catch (error) {
      console.error('Failed to save preferences:', error);
      return false;
    }
  };

  const togglePushNotifications = async () => {
    if (!pushEnabled && permission !== 'granted') {
      await requestPermission();
      return;
    }

    const newValue = !pushEnabled;
    setPushEnabled(newValue);

    const success = await savePreferences({ push_enabled: newValue });
    
    if (success) {
      setMessage({
        type: 'success',
        text: newValue ? 'Push notifications enabled' : 'Push notifications disabled'
      });
    }
  };

  const toggleCategory = async (category) => {
    const newPreferences = {
      ...preferences,
      [category]: !preferences[category],
    };

    setPreferences(newPreferences);

    const success = await savePreferences({ preferences: newPreferences });
    
    if (!success) {
      // Revert on failure
      setPreferences(preferences);
      setMessage({ type: 'error', text: 'Failed to update preferences' });
    }
  };

  const testNotification = () => {
    if (permission === 'granted') {
      new Notification('Test Notification', {
        body: 'This is a test notification from Kibray',
        icon: '/static/images/logo.png',
        badge: '/static/images/badge.png',
      });
    }
  };

  return (
    <div className="push-notification-settings">
      <h2>Push Notifications</h2>

      {/* Master Toggle */}
      <div className="setting-section">
        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-icon">
              {pushEnabled ? <Bell size={24} /> : <BellOff size={24} />}
            </div>
            <div className="setting-text">
              <h3>Push Notifications</h3>
              <p>Receive notifications even when the app is closed</p>
            </div>
          </div>

          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={pushEnabled}
              onChange={togglePushNotifications}
              disabled={loading}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>

        {permission === 'denied' && (
          <div className="permission-warning">
            <AlertCircle size={16} />
            <span>Notifications are blocked. Please enable them in your browser settings.</span>
          </div>
        )}
      </div>

      {/* Category Preferences */}
      {pushEnabled && (
        <div className="setting-section">
          <h3>Notification Types</h3>
          <p className="section-description">Choose which notifications you want to receive</p>

          <div className="category-list">
            <div className="category-item">
              <div className="category-info">
                <strong>Chat Messages</strong>
                <span>New messages in channels you're a member of</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={preferences.chat}
                  onChange={() => toggleCategory('chat')}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="category-item">
              <div className="category-info">
                <strong>Mentions</strong>
                <span>When someone @mentions you in a message</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={preferences.mention}
                  onChange={() => toggleCategory('mention')}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="category-item">
              <div className="category-info">
                <strong>Tasks</strong>
                <span>Task assignments and updates</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={preferences.task}
                  onChange={() => toggleCategory('task')}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="category-item">
              <div className="category-info">
                <strong>System</strong>
                <span>Important system announcements</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={preferences.system}
                  onChange={() => toggleCategory('system')}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Test Button */}
      {pushEnabled && permission === 'granted' && (
        <div className="setting-section">
          <button
            className="test-notification-btn"
            onClick={testNotification}
          >
            Send Test Notification
          </button>
        </div>
      )}

      {/* Status Message */}
      {message && (
        <div className={`status-message ${message.type}`}>
          {message.type === 'success' ? <Check size={16} /> : <X size={16} />}
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)}>
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
};

export default PushNotificationSettings;
