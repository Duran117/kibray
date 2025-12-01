import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import './ToastNotification.css';

/**
 * Enhanced Toast Notification Component - Phase 6
 * 
 * Features:
 * - Auto-dismiss after 5 seconds (configurable)
 * - Slide-in animation from top-right
 * - Manual close button
 * - Color-coded by type (success, info, warning, error)
 * - Icon for each type
 * - Progress bar showing auto-dismiss countdown
 * - Stacks multiple notifications
 * 
 * @param {string} id - Unique notification ID
 * @param {string} type - Notification type: 'success' | 'info' | 'warning' | 'error'
 * @param {string} title - Notification title (optional)
 * @param {string} message - Notification message
 * @param {function} onClose - Callback when notification closes
 * @param {boolean} autoClose - Auto-dismiss after duration (default: true)
 * @param {number} duration - Auto-dismiss duration in ms (default: 5000)
 */
const ToastNotification = ({ 
  id,
  type = 'info', 
  title,
  message, 
  onClose,
  autoClose = true,
  duration = 5000 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  // Trigger slide-in animation on mount
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  // Auto-dismiss timer
  useEffect(() => {
    if (!autoClose) return;

    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [autoClose, duration]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      if (onClose) onClose(id);
    }, 300); // Match CSS animation duration
  };

  const getIcon = () => {
    const iconProps = { size: 24, className: 'toast-icon' };
    
    switch (type) {
      case 'success':
        return <CheckCircle {...iconProps} className="toast-icon toast-icon-success" />;
      case 'warning':
        return <AlertTriangle {...iconProps} className="toast-icon toast-icon-warning" />;
      case 'error':
        return <AlertCircle {...iconProps} className="toast-icon toast-icon-error" />;
      case 'info':
      default:
        return <Info {...iconProps} className="toast-icon toast-icon-info" />;
    }
  };

  const getClassName = () => {
    const classes = ['toast-notification', `toast-${type}`];
    if (isVisible) classes.push('toast-visible');
    if (isExiting) classes.push('toast-exiting');
    return classes.join(' ');
  };

  return (
    <div className={getClassName()} role="alert" aria-live="polite">
      <div className="toast-icon-wrapper">
        {getIcon()}
      </div>
      
      <div className="toast-content">
        {title && <div className="toast-title">{title}</div>}
        <div className="toast-message">{message || 'Notification'}</div>
      </div>
      
      <button 
        className="toast-close-btn" 
        onClick={handleClose}
        aria-label="Close notification"
        type="button"
      >
        <X size={18} />
      </button>
      
      {autoClose && (
        <div 
          className="toast-progress-bar" 
          style={{ animationDuration: `${duration}ms` }}
        />
      )}
    </div>
  );
};

export default ToastNotification;
