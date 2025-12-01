import React from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';
import './ToastNotification.css';

const ToastNotification = ({ message, type = 'info', onClose }) => {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info
  };
  
  const Icon = icons[type] || Info;

  return (
    <div className={`toast-notification toast-${type}`}>
      <Icon size={20} />
      <span>{message}</span>
      <button onClick={onClose}>
        <X size={16} />
      </button>
    </div>
  );
};

export default ToastNotification;
