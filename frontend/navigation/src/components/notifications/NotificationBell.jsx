import React from 'react';
import { Bell } from 'lucide-react';
import './NotificationBell.css';

const NotificationBell = ({ count, onClick }) => {
  return (
    <button className="notification-bell" onClick={onClick}>
      <Bell size={20} />
      {count > 0 && (
        <span className="badge">{count > 99 ? '99+' : count}</span>
      )}
    </button>
  );
};

export default NotificationBell;
