import { useState, useCallback } from 'react';

/**
 * useToast Hook - Easy toast notification management
 * 
 * Features:
 * - Add toasts with show() method
 * - Auto-generate unique IDs
 * - Remove toasts manually or auto-dismiss
 * - Queue management
 * - Type helpers (success, error, warning, info)
 * 
 * Usage:
 * const { toasts, showToast, removeToast } = useToast();
 * 
 * showToast({ type: 'success', title: 'Saved', message: 'Data saved successfully' });
 * showToast.success('Operation completed');
 * showToast.error('An error occurred');
 */
const useToast = () => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((toast) => {
    const id = toast.id || `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const newToast = {
      id,
      type: toast.type || 'info',
      title: toast.title,
      message: toast.message,
      autoClose: toast.autoClose !== false,
      duration: toast.duration || 5000,
    };

    setToasts((prev) => [newToast, ...prev]);
    
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  // Helper methods for common toast types
  showToast.success = useCallback((message, title = 'Success') => {
    return showToast({ type: 'success', title, message });
  }, [showToast]);

  showToast.error = useCallback((message, title = 'Error') => {
    return showToast({ type: 'error', title, message });
  }, [showToast]);

  showToast.warning = useCallback((message, title = 'Warning') => {
    return showToast({ type: 'warning', title, message });
  }, [showToast]);

  showToast.info = useCallback((message, title = 'Info') => {
    return showToast({ type: 'info', title, message });
  }, [showToast]);

  return {
    toasts,
    showToast,
    removeToast,
    clearAll,
  };
};

export default useToast;
