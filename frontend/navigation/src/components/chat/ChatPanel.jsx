import React, { useState, useEffect } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import api from '../../utils/api';
import { MessageSquare } from 'lucide-react';
import './ChatPanel.css';

const ChatPanel = ({ channelId = 'general' }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMessages();
  }, [channelId]);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/chat/messages/?channel=${channelId}`);
      setMessages(data.results || data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      // Use mock data if API fails
      setMessages([
        { id: 1, sender: 'John Doe', text: 'Hey team, project update meeting at 2pm', timestamp: '10:30 AM', isOwn: false },
        { id: 2, sender: 'You', text: 'Sounds good, I\'ll be there', timestamp: '10:32 AM', isOwn: true },
        { id: 3, sender: 'Jane Smith', text: 'Can we discuss the budget changes?', timestamp: '10:35 AM', isOwn: false }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (messageText) => {
    try {
      const newMessage = await api.post('/chat/messages/', {
        text: messageText,
        channel: channelId
      });
      setMessages(prev => [...prev, newMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add message optimistically
      const newMsg = {
        id: Date.now(),
        sender: 'You',
        text: messageText,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        isOwn: true
      };
      setMessages(prev => [...prev, newMsg]);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <MessageSquare size={20} />
        <h3>Team Chat</h3>
      </div>
      
      {loading ? (
        <div className="chat-loading">
          <div className="spinner"></div>
          <p>Loading messages...</p>
        </div>
      ) : (
        <>
          <MessageList messages={messages} />
          <MessageInput onSend={handleSendMessage} />
        </>
      )}
    </div>
  );
};

export default ChatPanel;
