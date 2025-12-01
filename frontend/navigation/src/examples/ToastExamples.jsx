/**
 * Toast Notifications - Usage Examples
 * Phase 6 WebSocket Integration
 */

import React from 'react';
import useToast from '../hooks/useToast';
import { useNotifications } from '../hooks/useWebSocket';
import ToastContainer from '../components/notifications/ToastContainer';

/**
 * Example 1: Basic Toast Usage
 */
function BasicToastExample() {
  const { toasts, showToast, removeToast } = useToast();

  const handleClick = () => {
    // Show different types of toasts
    showToast({
      type: 'success',
      title: 'Success!',
      message: 'Your changes have been saved successfully.',
      duration: 5000
    });

    // Using helper methods
    showToast.success('Operation completed successfully');
    showToast.error('An error occurred while processing');
    showToast.warning('Please review your changes');
    showToast.info('New update available');
  };

  return (
    <div>
      <button onClick={handleClick}>Show Toast</button>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

/**
 * Example 2: WebSocket Notifications Integration
 */
function WebSocketNotificationsExample() {
  const { toasts, showToast, removeToast } = useToast();
  
  // Pass showToast to useNotifications hook
  const { isConnected, notifications, unreadCount, markAsRead } = useNotifications(showToast);

  return (
    <div>
      <div>
        Status: {isConnected ? 'Connected' : 'Disconnected'}
      </div>
      <div>
        Unread: {unreadCount}
      </div>
      
      {/* Toast notifications will auto-show when WebSocket receives messages */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Notification list */}
      <div className="notification-list">
        {notifications.map(notif => (
          <div key={notif.id} onClick={() => markAsRead(notif.id)}>
            <strong>{notif.title}</strong>
            <p>{notif.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Example 3: Chat Message Notifications
 */
function ChatNotificationsExample() {
  const { toasts, showToast, removeToast } = useToast();
  
  const handleNewMessage = (message) => {
    showToast({
      type: 'info',
      title: `New message from ${message.username}`,
      message: message.text.substring(0, 100),
      duration: 4000
    });
  };

  return (
    <div>
      {/* Your chat component */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

/**
 * Example 4: Form Submission with Toast
 */
function FormWithToastExample() {
  const { toasts, showToast, removeToast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      // API call
      const response = await fetch('/api/save', {
        method: 'POST',
        body: JSON.stringify({ /* data */ })
      });

      if (response.ok) {
        showToast.success('Form submitted successfully');
      } else {
        showToast.error('Failed to submit form');
      }
    } catch (error) {
      showToast.error('Network error occurred');
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        {/* Form fields */}
        <button type="submit">Submit</button>
      </form>
      <ToastContainer toasts={toasts} onRemove={removeToast} maxToasts={3} />
    </div>
  );
}

/**
 * Example 5: Manual Close and Persistent Toast
 */
function PersistentToastExample() {
  const { toasts, showToast, removeToast } = useToast();

  const handleShowPersistent = () => {
    showToast({
      type: 'warning',
      title: 'Important Notice',
      message: 'This toast will not auto-dismiss',
      autoClose: false // Requires manual close
    });
  };

  const handleShowWithLongDuration = () => {
    showToast({
      type: 'info',
      title: 'Processing',
      message: 'This will take 10 seconds...',
      duration: 10000 // 10 seconds
    });
  };

  return (
    <div>
      <button onClick={handleShowPersistent}>Show Persistent Toast</button>
      <button onClick={handleShowWithLongDuration}>Show Long Toast</button>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

export {
  BasicToastExample,
  WebSocketNotificationsExample,
  ChatNotificationsExample,
  FormWithToastExample,
  PersistentToastExample
};
