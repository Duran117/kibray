import React from 'react';
import './MessageList.css';

const MessageList = ({ messages }) => {
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
            <div className="message-time">{msg.timestamp}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
