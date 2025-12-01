/**
 * React Hooks for WebSocket connections
 * Custom hooks for chat, notifications, tasks, and status
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import WebSocketClient from '../utils/websocket';

/**
 * Generic WebSocket hook
 */
export function useWebSocket(url, options = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (!url) return;

    const ws = new WebSocketClient(url);
    wsRef.current = ws;

    // Set initial connecting state
    setConnectionStatus('connecting');

    ws.on('open', () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      setError(null);
      reconnectAttemptsRef.current = 0;
      if (options.onOpen) options.onOpen();
    });

    ws.on('message', (data) => {
      setLastMessage(data);
      if (options.onMessage) options.onMessage(data);
    });

    ws.on('close', (event) => {
      setIsConnected(false);
      
      // Check if it's a normal closure or network issue
      if (event.wasClean) {
        setConnectionStatus('disconnected');
      } else {
        // Will attempt reconnect
        reconnectAttemptsRef.current += 1;
        setConnectionStatus('reconnecting');
      }
      
      if (options.onClose) options.onClose();
    });

    ws.on('error', (err) => {
      setError(err);
      setConnectionStatus('disconnected');
      if (options.onError) options.onError(err);
    });

    ws.on('reconnecting', () => {
      setConnectionStatus('reconnecting');
    });

    ws.connect();

    return () => {
      ws.close();
      setConnectionStatus('disconnected');
    };
  }, [url]);

  const sendMessage = useCallback((data) => {
    if (wsRef.current) {
      wsRef.current.send(data);
    }
  }, []);

  return { 
    isConnected, 
    connectionStatus, 
    lastMessage, 
    error, 
    sendMessage,
    reconnectAttempts: reconnectAttemptsRef.current
  };
}

/**
 * Chat WebSocket hook
 */
export function useChat(channelId) {
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const typingTimeoutRef = useRef({});

  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'chat_message':
        setMessages(prev => [...prev, {
          id: data.message_id,
          text: data.message,
          username: data.username,
          userId: data.user_id,
          timestamp: data.timestamp
        }]);
        break;

      case 'typing_indicator':
        if (data.is_typing) {
          setTypingUsers(prev => {
            if (!prev.find(u => u.userId === data.user_id)) {
              return [...prev, { userId: data.user_id, username: data.username }];
            }
            return prev;
          });

          // Clear typing indicator after 3 seconds
          if (typingTimeoutRef.current[data.user_id]) {
            clearTimeout(typingTimeoutRef.current[data.user_id]);
          }
          typingTimeoutRef.current[data.user_id] = setTimeout(() => {
            setTypingUsers(prev => prev.filter(u => u.userId !== data.user_id));
          }, 3000);
        } else {
          setTypingUsers(prev => prev.filter(u => u.userId !== data.user_id));
        }
        break;

      case 'user_joined':
        setOnlineUsers(prev => {
          if (!prev.find(u => u.userId === data.user_id)) {
            return [...prev, { userId: data.user_id, username: data.username }];
          }
          return prev;
        });
        break;

      case 'user_left':
        setOnlineUsers(prev => prev.filter(u => u.userId !== data.user_id));
        break;

      case 'connection_established':
        console.log('Chat connected:', data.message);
        break;

      default:
        console.log('Unknown chat message type:', data.type);
    }
  }, []);

  const { isConnected, connectionStatus, sendMessage } = useWebSocket(
    channelId ? `/ws/chat/${channelId}/` : null,
    { onMessage: handleMessage }
  );

  const sendChatMessage = useCallback((message) => {
    sendMessage({
      type: 'chat_message',
      message
    });
  }, [sendMessage]);

  const sendTyping = useCallback((isTyping) => {
    sendMessage({
      type: 'typing',
      is_typing: isTyping
    });
  }, [sendMessage]);

  const markAsRead = useCallback((messageId) => {
    sendMessage({
      type: 'read_receipt',
      message_id: messageId
    });
  }, [sendMessage]);

  return {
    isConnected,
    connectionStatus,
    messages,
    typingUsers,
    onlineUsers,
    sendChatMessage,
    sendTyping,
    markAsRead
  };
}

/**
 * Notifications WebSocket hook
 */
/**
 * Hook for real-time notifications
 * Automatically shows toast notifications for new messages
 */
export function useNotifications(showToastFn = null) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'notification':
      case 'send_notification':
        const notification = data.notification || data;
        setNotifications(prev => [notification, ...prev]);
        setUnreadCount(prev => prev + 1);
        
        // Show toast notification - Phase 6 Integration
        if (showToastFn) {
          showToastFn({
            type: notification.category || 'info',
            title: notification.title,
            message: notification.message,
            autoClose: true,
            duration: 5000
          });
        } else if (window.showToast) {
          // Fallback to global function
          window.showToast(notification.title, notification.message, notification.category);
        }
        break;

      case 'notification_update':
      case 'unread_count':
        setUnreadCount(data.unread_count || data.count || 0);
        if (data.status === 'read') {
          setNotifications(prev => 
            prev.map(n => 
              n.notification_id === data.notification_id || n.id === data.notification_id
                ? { ...n, read: true } 
                : n
            )
          );
        }
        break;

      case 'connection_established':
        setUnreadCount(data.unread_count || 0);
        console.log('Notifications connected:', data.message);
        break;

      default:
        console.log('Unknown notification type:', data.type);
    }
  }, [showToastFn]);

  const { isConnected, connectionStatus, sendMessage } = useWebSocket('/ws/notifications/', {
    onMessage: handleMessage
  });

  const markAsRead = useCallback((notificationId) => {
    sendMessage({
      type: 'mark_read',
      notification_id: notificationId
    });
  }, [sendMessage]);

  const markAllAsRead = useCallback(() => {
    sendMessage({
      type: 'mark_all_read'
    });
  }, [sendMessage]);

  const dismissNotification = useCallback((notificationId) => {
    sendMessage({
      type: 'dismiss',
      notification_id: notificationId
    });
    setNotifications(prev => prev.filter(n => 
      (n.notification_id !== notificationId) && (n.id !== notificationId)
    ));
  }, [sendMessage]);

  return {
    isConnected,
    connectionStatus,
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    dismissNotification
  };
}

/**
 * Tasks WebSocket hook
 */
export function useTasks(projectId) {
  const [tasks, setTasks] = useState([]);
  const [taskUpdates, setTaskUpdates] = useState([]);

  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'task_created':
        setTasks(prev => [...prev, data.task_data]);
        setTaskUpdates(prev => [...prev, { type: 'created', task: data.task_data }]);
        break;

      case 'task_updated':
        setTasks(prev => 
          prev.map(task => 
            task.id === data.task_id ? { ...task, ...data.task_data } : task
          )
        );
        setTaskUpdates(prev => [...prev, { 
          type: 'updated', 
          task: data.task_data, 
          changes: data.changes 
        }]);
        break;

      case 'task_deleted':
        setTasks(prev => prev.filter(task => task.id !== data.task_id));
        setTaskUpdates(prev => [...prev, { type: 'deleted', taskId: data.task_id }]);
        break;

      case 'task_status_changed':
        setTasks(prev => 
          prev.map(task => 
            task.id === data.task_id 
              ? { ...task, status: data.new_status } 
              : task
          )
        );
        setTaskUpdates(prev => [...prev, { 
          type: 'status_changed', 
          taskId: data.task_id,
          oldStatus: data.old_status,
          newStatus: data.new_status
        }]);
        break;

      case 'connection_established':
        console.log('Tasks connected for project:', data.project_id);
        break;

      default:
        console.log('Unknown task message type:', data.type);
    }
  }, []);

  const { isConnected, connectionStatus, sendMessage } = useWebSocket(
    projectId ? `/ws/tasks/${projectId}/` : null,
    { onMessage: handleMessage }
  );

  const subscribeToTask = useCallback((taskId) => {
    sendMessage({
      action: 'subscribe_task',
      task_id: taskId
    });
  }, [sendMessage]);

  return {
    isConnected,
    connectionStatus,
    tasks,
    taskUpdates,
    subscribeToTask
  };
}

/**
 * User Status WebSocket hook
 */
export function useStatus() {
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [userStatuses, setUserStatuses] = useState({});
  const heartbeatIntervalRef = useRef(null);

  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'user_status_changed':
        setUserStatuses(prev => ({
          ...prev,
          [data.user_id]: {
            userId: data.user_id,
            username: data.username,
            status: data.status,
            timestamp: data.timestamp
          }
        }));

        if (data.status === 'online') {
          setOnlineUsers(prev => {
            if (!prev.find(u => u.userId === data.user_id)) {
              return [...prev, { userId: data.user_id, username: data.username }];
            }
            return prev;
          });
        } else {
          setOnlineUsers(prev => prev.filter(u => u.userId !== data.user_id));
        }
        break;

      case 'connection_established':
        setOnlineUsers(data.online_users || []);
        console.log('Status connected, online users:', data.online_users?.length);
        break;

      case 'heartbeat_ack':
        // Heartbeat acknowledged
        break;

      default:
        console.log('Unknown status message type:', data.type);
    }
  }, []);

  const { isConnected, connectionStatus, sendMessage } = useWebSocket('/ws/status/', {
    onMessage: handleMessage,
    onOpen: () => {
      // Start sending heartbeats every 30 seconds
      heartbeatIntervalRef.current = setInterval(() => {
        sendMessage({ action: 'heartbeat' });
      }, 30000);
    },
    onClose: () => {
      // Clear heartbeat interval
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
    }
  });

  useEffect(() => {
    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, []);

  const getUserStatus = useCallback((userId) => {
    return userStatuses[userId] || { status: 'offline' };
  }, [userStatuses]);

  const isUserOnline = useCallback((userId) => {
    return onlineUsers.some(u => u.userId === userId);
  }, [onlineUsers]);

  return {
    isConnected,
    connectionStatus,
    onlineUsers,
    userStatuses,
    getUserStatus,
    isUserOnline
  };
}
