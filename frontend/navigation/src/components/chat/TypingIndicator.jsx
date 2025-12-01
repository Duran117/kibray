import React from 'react';
import './TypingIndicator.css';

const TypingIndicator = ({ users = [] }) => {
  if (users.length === 0) return null;

  const getUsersText = () => {
    if (users.length === 1) {
      return `${users[0].username} is typing`;
    } else if (users.length === 2) {
      return `${users[0].username} and ${users[1].username} are typing`;
    } else {
      return `${users.length} people are typing`;
    }
  };

  return (
    <div className="typing-indicator">
      <div className="typing-text">{getUsersText()}</div>
      <div className="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  );
};

export default TypingIndicator;
