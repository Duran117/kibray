/**
 * React Hook for Offline Message Queue
 * Phase 6 - Improvement #11: Offline Message Queue
 * 
 * Provides integration between WebSocket hooks and offline queue
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import offlineQueue from '../services/offlineQueue';

/**
 * Hook to manage offline message queue
 * 
 * Features:
 * - Automatically queues messages when offline
 * - Sends queued messages when connection restored
 * - Provides queue state and statistics
 * - Handles retry logic with exponential backoff
 * 
 * @param {Object} options
 * @param {boolean} options.isConnected - WebSocket connection status
 * @param {Function} options.sendMessage - Function to send message via WebSocket
 * @param {string} options.type - Message type ('chat', 'notification', 'task', 'status')
 * @param {string} options.channelId - Optional channel ID for chat messages
 * 
 * @returns {Object} Queue state and methods
 */
export function useOfflineQueue({ isConnected, sendMessage, type, channelId = null }) {
  const [queueSize, setQueueSize] = useState(offlineQueue.size());
  const [isSending, setIsSending] = useState(false);
  const [lastError, setLastError] = useState(null);
  const sendingRef = useRef(false);
  const retryTimeoutRef = useRef(null);

  // Subscribe to queue changes
  useEffect(() => {
    const unsubscribe = offlineQueue.subscribe(({ action, queueSize }) => {
      setQueueSize(queueSize);
    });

    return unsubscribe;
  }, []);

  /**
   * Send a single message from the queue
   */
  const sendQueuedMessage = useCallback(async (message) => {
    try {
      await sendMessage(message.data);
      offlineQueue.dequeue(message.id);
      return { success: true };
    } catch (error) {
      console.error('Error sending queued message:', error);
      offlineQueue.markFailed(message.id, error.message);
      return { success: false, error: error.message };
    }
  }, [sendMessage]);

  /**
   * Process all queued messages
   */
  const processQueue = useCallback(async () => {
    if (sendingRef.current || !isConnected) {
      return;
    }

    sendingRef.current = true;
    setIsSending(true);
    setLastError(null);

    try {
      // Get messages for this type/channel
      let messages = type 
        ? offlineQueue.getByType(type)
        : offlineQueue.getAll();

      if (channelId) {
        messages = messages.filter(msg => msg.channelId === channelId);
      }

      if (messages.length === 0) {
        return;
      }

      console.log(`Processing ${messages.length} queued messages...`);

      // Send messages sequentially with delay
      for (const message of messages) {
        if (!isConnected) {
          console.log('Connection lost during queue processing, stopping');
          break;
        }

        const result = await sendQueuedMessage(message);
        
        if (!result.success) {
          setLastError(result.error);
        }

        // Small delay between messages to avoid overwhelming server
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const remaining = offlineQueue.getByType(type).length;
      if (remaining > 0) {
        console.log(`${remaining} messages still in queue (may need retry)`);
      }
    } catch (error) {
      console.error('Error processing queue:', error);
      setLastError(error.message);
    } finally {
      sendingRef.current = false;
      setIsSending(false);
    }
  }, [isConnected, type, channelId, sendQueuedMessage]);

  /**
   * Automatically process queue when connection restored
   */
  useEffect(() => {
    if (isConnected && queueSize > 0) {
      // Delay to allow connection to stabilize
      retryTimeoutRef.current = setTimeout(() => {
        processQueue();
      }, 1000);
    }

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [isConnected, queueSize, processQueue]);

  /**
   * Send a message (queue if offline)
   */
  const sendOrQueue = useCallback((data) => {
    if (isConnected) {
      // Send immediately
      try {
        sendMessage(data);
        return { queued: false, success: true };
      } catch (error) {
        console.error('Error sending message, queueing:', error);
        const id = offlineQueue.enqueue(type, data, channelId);
        return { queued: true, success: false, queueId: id, error: error.message };
      }
    } else {
      // Queue for later
      const id = offlineQueue.enqueue(type, data, channelId);
      console.log(`Message queued (offline): ${id}`);
      return { queued: true, success: false, queueId: id };
    }
  }, [isConnected, sendMessage, type, channelId]);

  /**
   * Clear queue for this type/channel
   */
  const clearQueue = useCallback(() => {
    if (type) {
      // Remove all messages of this type
      const messages = offlineQueue.getByType(type);
      messages.forEach(msg => offlineQueue.dequeue(msg.id));
    } else {
      offlineQueue.clear();
    }
  }, [type]);

  /**
   * Retry failed messages
   */
  const retryFailed = useCallback(() => {
    if (isConnected) {
      processQueue();
    }
  }, [isConnected, processQueue]);

  return {
    queueSize,
    isSending,
    lastError,
    sendOrQueue,
    processQueue,
    clearQueue,
    retryFailed,
    hasMessages: queueSize > 0,
  };
}

/**
 * Hook for queue statistics (for debugging/monitoring)
 */
export function useQueueStats() {
  const [stats, setStats] = useState(offlineQueue.getStats());

  useEffect(() => {
    const unsubscribe = offlineQueue.subscribe(() => {
      setStats(offlineQueue.getStats());
    });

    // Update stats every 5 seconds
    const interval = setInterval(() => {
      setStats(offlineQueue.getStats());
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  return stats;
}

export default useOfflineQueue;
