import React from 'react';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../../utils/formatDate';
import './MessageList.css';

const MessageList = ({ messages }) => {
  const { t } = useTranslation();
  return (
    <div className="message-list">
      {messages.map(msg => (
        <div key={msg.id} className={`message-item ${msg.isOwn ? 'own' : ''}`}>
          <div className="message-avatar">
            {msg.sender.charAt(0).toUpperCase()}
          </div>
          <div className="message-content">
            <div className="message-sender">{msg.sender}</div>
            <div className="message-text">{msg.text}</div>
            <div className="message-time">{formatDate(msg.timestamp)}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
