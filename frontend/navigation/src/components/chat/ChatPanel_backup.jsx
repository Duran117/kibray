import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import TypingIndicator from './TypingIndicator';
import api from '../../utils/api';
import { useChat } from '../../hooks/useWebSocket';
import { MessageSquare, Wifi, WifiOff } from 'lucide-react';
import './ChatPanel.css';

const ChatPanel = ({ channelId = 'general' }) => {
  const [historicalMessages, setHistoricalMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const typingTimeoutRef = useRef(null);
  
  // WebSocket connection for real-time chat
  const {
    isConnected,
    messages: liveMessages,
    typingUsers,
    onlineUsers,
    sendChatMessage,
    sendTyping,
    markAsRead
  } = useChat(channelId);

  // Combine historical and live messages
  const allMessages = [...historicalMessages, ...liveMessages];

  useEffect(() => {
    fetchMessages();
  }, [channelId]);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/chat/messages/?channel=${channelId}`);
      setHistoricalMessages(data.results || data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      // Use mock data if API fails
      setHistoricalMessages([
        { id: 1, sender: 'John Doe', text: 'Hey team, project update meeting at 2pm', timestamp: '10:30 AM', isOwn: false },
        { id: 2, sender: 'You', text: 'Sounds good, I\'ll be there', timestamp: '10:32 AM', isOwn: true },
        { id: 3, sender: 'Jane Smith', text: 'Can we discuss the budget changes?', timestamp: '10:35 AM', isOwn: false }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    // Send via WebSocket if connected
    if (isConnected) {
      sendChatMessage(messageText);
      setInputValue('');
      sendTyping(false);
    } else {
      // Fallback to HTTP if WebSocket not available
      try {
        const newMessage = await api.post('/chat/messages/', {
          text: messageText,
          channel: channelId
        });
        setHistoricalMessages(prev => [...prev, newMessage]);
        setInputValue('');
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
        setHistoricalMessages(prev => [...prev, newMsg]);
        setInputValue('');
      }
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);

    // Send typing indicator
    if (isConnected) {
      sendTyping(true);
      
      // Clear previous timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Stop typing after 2 seconds of inactivity
      typingTimeoutRef.current = setTimeout(() => {
        sendTyping(false);
      }, 2000);
    }
  };

  const handleInputSubmit = () => {
    handleSendMessage(inputValue);
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <MessageSquare size={20} />
        <h3>Team Chat</h3>
        <div className="connection-status">
          {isConnected ? (
            <span className="connected">
              <Wifi size={16} />
              <span>Live</span>
            </span>
          ) : (
            <span className="disconnected">
              <WifiOff size={16} />
              <span>Offline</span>
            </span>
          )}
        </div>
        {onlineUsers.length > 0 && (
          <div className="online-count">
            {onlineUsers.length} online
          </div>
        )}
      </div>
      
      {loading ? (
        <div className="chat-loading">
          <div className="spinner"></div>
          <p>Loading messages...</p>
        </div>
      ) : (
        <>
          <MessageList messages={allMessages} />
          {typingUsers.length > 0 && (
            <TypingIndicator users={typingUsers} />
          )}
          <MessageInput 
            value={inputValue}
            onChange={handleInputChange}
            onSend={handleInputSubmit} 
          />
        </>
      )}
    </div>
  );
};

export default ChatPanel;
