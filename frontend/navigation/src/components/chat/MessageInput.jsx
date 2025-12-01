import React, { useState } from 'react';
import { Send } from 'lucide-react';
import './MessageInput.css';

const MessageInput = ({ onSend }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSend(inputValue);
      setInputValue('');
    }
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <input 
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="Type a message..."
      />
      <button type="submit" disabled={!inputValue.trim()}>
        <Send size={18} />
      </button>
    </form>
  );
};

export default MessageInput;
