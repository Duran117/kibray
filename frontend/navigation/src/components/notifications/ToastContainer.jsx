import React, { useState, useCallback, useEffect } from 'react';
import ToastNotification from './ToastNotification';
import './ToastContainer.css';

/**
 * Toast Container - Manages multiple toast notifications
 * 
 * Features:
 * - Stack notifications vertically
 * - Auto-remove dismissed notifications
 * - Position in top-right corner
 * - Maximum 5 visible toasts at once
 * - Queue additional toasts
 * 
 * Usage:
 * <ToastContainer toasts={toasts} onRemove={handleRemove} />
 */
const ToastContainer = ({ toasts = [], onRemove, maxToasts = 5 }) => {
  const [visibleToasts, setVisibleToasts] = useState([]);

  useEffect(() => {
    // Show only the latest maxToasts notifications
    setVisibleToasts(toasts.slice(0, maxToasts));
  }, [toasts, maxToasts]);

  const handleClose = useCallback((id) => {
    if (onRemove) {
      onRemove(id);
    }
  }, [onRemove]);

  if (visibleToasts.length === 0) {
    return null;
  }

  return (
    <div className="toast-container" role="region" aria-label="Notifications">
      {visibleToasts.map((toast) => (
        <ToastNotification
          key={toast.id}
          id={toast.id}
          type={toast.type}
          title={toast.title}
          message={toast.message}
          onClose={handleClose}
          autoClose={toast.autoClose !== false}
          duration={toast.duration || 5000}
        />
      ))}
    </div>
  );
};

export default ToastContainer;
