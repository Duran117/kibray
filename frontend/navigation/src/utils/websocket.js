/**
 * WebSocket Connection Manager for Kibray Real-Time Features
 * 
 * Handles WebSocket connections with:
 * - Automatic reconnection with exponential backoff
 * - Event-based message handling
 * - Connection state management
 * - Error handling and logging
 * - Message compression (permessage-deflate)
 */

import WebSocketConfig, { 
  getCompressionInfo, 
  logCompressionStats, 
  getMessageSize,
  formatBytes 
} from './websocketConfig';

class WebSocketClient {
  constructor(url, protocols = []) {
    this.url = url;
    this.protocols = protocols.length > 0 ? protocols : WebSocketConfig.protocols;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = WebSocketConfig.connection.reconnectAttempts;
    this.reconnectDelay = WebSocketConfig.connection.reconnectDelay;
    this.maxReconnectDelay = WebSocketConfig.connection.maxReconnectDelay;
    this.listeners = {
      message: [],
      open: [],
      close: [],
      error: []
    };
    this.isManualClose = false;
    
    // Compression statistics
    this.compressionStats = {
      messagesSent: 0,
      totalBytes: 0,
      messagesReceived: 0,
      receivedBytes: 0,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    try {
      // Get auth token from localStorage
      const authToken = localStorage.getItem('authToken') || localStorage.getItem('kibray_access_token');
      const lng = (localStorage.getItem('i18nextLng') || navigator.language || 'en').split('-')[0];
      
      // Build WebSocket URL with token if available
      let wsUrl = this.url;
      const hasQuery = this.url.includes('?');
      const qp = [];
      if (authToken) qp.push(`token=${encodeURIComponent(authToken)}`);
      if (lng) qp.push(`lang=${encodeURIComponent(lng)}`);
      if (!hasQuery && qp.length) wsUrl += `?${qp.join('&')}`;
      else if (hasQuery && qp.length) wsUrl += `&${qp.join('&')}`;

      // Determine protocol (ws or wss)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      
      // If URL is relative, make it absolute
      if (wsUrl.startsWith('/')) {
        wsUrl = `${protocol}//${host}${wsUrl}`;
      } else if (wsUrl.startsWith('ws://localhost') || wsUrl.startsWith('ws://127.0.0.1')) {
        // Keep localhost as-is for development
      } else if (!wsUrl.startsWith('ws://') && !wsUrl.startsWith('wss://')) {
        wsUrl = `${protocol}//${host}/${wsUrl}`;
      }

      console.log(`[WebSocket] Connecting to ${wsUrl}`);
      this.ws = new WebSocket(wsUrl, this.protocols);

      // Set up event handlers
      this.ws.onopen = (event) => this.handleOpen(event);
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = (event) => this.handleClose(event);
      this.ws.onerror = (event) => this.handleError(event);

    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.handleError(error);
    }
  }

  /**
   * Send data through WebSocket
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      
      // Track compression statistics
      const messageSize = getMessageSize(message);
      this.compressionStats.messagesSent++;
      this.compressionStats.totalBytes += messageSize;
      
      // Log large message being sent
      if (WebSocketConfig.debug && messageSize > WebSocketConfig.compression.threshold) {
        console.log(`[WebSocket] Sending large message (${formatBytes(messageSize)}) - compression will be applied`);
      }
      
      this.ws.send(message);
      console.log('[WebSocket] Sent:', message.substring(0, 100) + (message.length > 100 ? '...' : ''));
    } else {
      console.warn('[WebSocket] Cannot send - not connected');
    }
  }

  /**
   * Close WebSocket connection
   */
  close() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
    }
  }

  /**
   * Handle WebSocket open event
   */
  handleOpen(event) {
    console.log('[WebSocket] Connected');
    this.reconnectAttempts = 0;
    this.reconnectDelay = WebSocketConfig.connection.reconnectDelay;
    
    // Log compression status
    if (WebSocketConfig.compression.enabled) {
      const compressionInfo = getCompressionInfo(this.ws);
      console.log('[WebSocket] Compression:', compressionInfo.active ? '✅ Enabled' : '❌ Disabled');
      console.log('[WebSocket] Extensions:', compressionInfo.extensions || 'None');
    }
    
    this.listeners.open.forEach(callback => callback(event));
  }

  /**
   * Handle WebSocket message event
   */
  handleMessage(event) {
    try {
      // Track received message size
      const messageSize = getMessageSize(event.data);
      this.compressionStats.messagesReceived++;
      this.compressionStats.receivedBytes += messageSize;
      
      const data = JSON.parse(event.data);
      console.log('[WebSocket] Received:', data);
      this.listeners.message.forEach(callback => callback(data));
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
      this.listeners.message.forEach(callback => callback(event.data));
    }
  }

  /**
   * Handle WebSocket close event
   */
  handleClose(event) {
    console.log('[WebSocket] Disconnected:', event.code, event.reason);
    this.listeners.close.forEach(callback => callback(event));

    // Attempt to reconnect unless manually closed
    if (!this.isManualClose) {
      this.reconnect();
    }
  }

  /**
   * Handle WebSocket error event
   */
  handleError(event) {
    console.error('[WebSocket] Error:', event);
    this.listeners.error.forEach(callback => callback(event));
  }

  /**
   * Reconnect with exponential backoff
   */
  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect();
      }
    }, delay);
  }

  /**
   * Add event listener
   */
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Get connection state
   */
  getState() {
    if (!this.ws) return 'CLOSED';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get compression statistics
   * 
   * @returns {object} Statistics including compression info and message counts
   */
  getCompressionStats() {
    const compressionInfo = this.ws ? getCompressionInfo(this.ws) : { active: false };
    
    return {
      ...this.compressionStats,
      compression: compressionInfo,
      averageMessageSize: this.compressionStats.messagesSent > 0
        ? Math.round(this.compressionStats.totalBytes / this.compressionStats.messagesSent)
        : 0,
      averageReceivedSize: this.compressionStats.messagesReceived > 0
        ? Math.round(this.compressionStats.receivedBytes / this.compressionStats.messagesReceived)
        : 0,
    };
  }

  /**
   * Log compression statistics to console
   */
  logCompressionStats() {
    logCompressionStats(this.ws, this.compressionStats);
  }

  /**
   * Reset compression statistics
   */
  resetCompressionStats() {
    this.compressionStats = {
      messagesSent: 0,
      totalBytes: 0,
      messagesReceived: 0,
      receivedBytes: 0,
    };
  }
}

export default WebSocketClient;
