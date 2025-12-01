/**
 * Offline Message Queue Service
 * Phase 6 - Improvement #11: Offline Message Queue
 * 
 * Handles queueing of messages when WebSocket is disconnected
 * and automatic retry when connection is restored.
 */

const STORAGE_KEY = 'kibray_offline_message_queue';
const MAX_QUEUE_SIZE = 100;
const MAX_RETRY_ATTEMPTS = 3;

/**
 * Message Queue Item Structure
 * {
 *   id: string (UUID),
 *   type: 'chat' | 'notification' | 'task' | 'status',
 *   data: object (message payload),
 *   timestamp: number (Date.now()),
 *   retryCount: number,
 *   channelId: string (optional, for chat messages),
 *   error: string (optional, last error message)
 * }
 */

class OfflineMessageQueue {
  constructor() {
    this.queue = this.loadQueue();
    this.listeners = [];
  }

  /**
   * Add a message to the offline queue
   */
  enqueue(type, data, channelId = null) {
    const message = {
      id: this.generateId(),
      type,
      data,
      timestamp: Date.now(),
      retryCount: 0,
      channelId,
      error: null,
    };

    // Check queue size limit
    if (this.queue.length >= MAX_QUEUE_SIZE) {
      console.warn(`Offline queue full (${MAX_QUEUE_SIZE}), removing oldest message`);
      this.queue.shift(); // Remove oldest
    }

    this.queue.push(message);
    this.saveQueue();
    this.notifyListeners('enqueue', message);

    return message.id;
  }

  /**
   * Remove a message from the queue
   */
  dequeue(messageId) {
    const index = this.queue.findIndex(msg => msg.id === messageId);
    if (index !== -1) {
      const message = this.queue.splice(index, 1)[0];
      this.saveQueue();
      this.notifyListeners('dequeue', message);
      return message;
    }
    return null;
  }

  /**
   * Get all messages in the queue
   */
  getAll() {
    return [...this.queue];
  }

  /**
   * Get messages by type
   */
  getByType(type) {
    return this.queue.filter(msg => msg.type === type);
  }

  /**
   * Get messages by channel
   */
  getByChannel(channelId) {
    return this.queue.filter(msg => msg.channelId === channelId);
  }

  /**
   * Get queue size
   */
  size() {
    return this.queue.length;
  }

  /**
   * Clear the entire queue
   */
  clear() {
    this.queue = [];
    this.saveQueue();
    this.notifyListeners('clear', null);
  }

  /**
   * Mark a message as failed (increment retry count)
   */
  markFailed(messageId, error) {
    const message = this.queue.find(msg => msg.id === messageId);
    if (message) {
      message.retryCount++;
      message.error = error;

      // Remove if exceeded max retries
      if (message.retryCount >= MAX_RETRY_ATTEMPTS) {
        console.error(`Message ${messageId} exceeded max retries, removing from queue`);
        this.dequeue(messageId);
        this.notifyListeners('maxRetriesExceeded', message);
      } else {
        this.saveQueue();
        this.notifyListeners('retry', message);
      }
    }
  }

  /**
   * Get messages that need retry
   */
  getPendingRetries() {
    return this.queue.filter(msg => msg.retryCount > 0 && msg.retryCount < MAX_RETRY_ATTEMPTS);
  }

  /**
   * Subscribe to queue changes
   */
  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  }

  /**
   * Notify all listeners
   */
  notifyListeners(action, message) {
    this.listeners.forEach(callback => {
      try {
        callback({ action, message, queueSize: this.queue.length });
      } catch (error) {
        console.error('Error in queue listener:', error);
      }
    });
  }

  /**
   * Load queue from localStorage
   */
  loadQueue() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        
        // Filter out messages older than 24 hours
        const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
        const filtered = parsed.filter(msg => msg.timestamp > oneDayAgo);
        
        if (filtered.length !== parsed.length) {
          console.log(`Removed ${parsed.length - filtered.length} stale messages from queue`);
        }
        
        return filtered;
      }
    } catch (error) {
      console.error('Error loading offline queue from localStorage:', error);
    }
    return [];
  }

  /**
   * Save queue to localStorage
   */
  saveQueue() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
    } catch (error) {
      console.error('Error saving offline queue to localStorage:', error);
      
      // If quota exceeded, remove oldest messages
      if (error.name === 'QuotaExceededError') {
        console.warn('LocalStorage quota exceeded, removing oldest messages');
        this.queue = this.queue.slice(-50); // Keep only last 50
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
        } catch (e) {
          console.error('Still cannot save queue after cleanup:', e);
        }
      }
    }
  }

  /**
   * Generate unique ID
   */
  generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get queue statistics
   */
  getStats() {
    const byType = {};
    const byRetryCount = { 0: 0, 1: 0, 2: 0, 3: 0 };
    
    this.queue.forEach(msg => {
      byType[msg.type] = (byType[msg.type] || 0) + 1;
      byRetryCount[msg.retryCount] = (byRetryCount[msg.retryCount] || 0) + 1;
    });

    return {
      total: this.queue.length,
      byType,
      byRetryCount,
      oldest: this.queue.length > 0 ? this.queue[0].timestamp : null,
      newest: this.queue.length > 0 ? this.queue[this.queue.length - 1].timestamp : null,
    };
  }
}

// Singleton instance
const offlineQueue = new OfflineMessageQueue();

export default offlineQueue;
