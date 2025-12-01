/**
 * WebSocket Configuration for Kibray
 * 
 * Centralized WebSocket settings including:
 * - Compression configuration
 * - Connection timeouts
 * - Reconnection strategy
 * - Message size limits
 */

export const WebSocketConfig = {
  // Compression settings
  compression: {
    enabled: true, // Enable permessage-deflate compression
    threshold: 1024, // Only compress messages > 1KB (1024 bytes)
    
    // Browser's WebSocket API automatically negotiates compression
    // if server supports it via Sec-WebSocket-Extensions header
    // No manual configuration needed on client side
  },

  // Connection settings
  connection: {
    reconnectAttempts: 10, // Maximum reconnection attempts
    reconnectDelay: 1000, // Initial reconnect delay in ms
    maxReconnectDelay: 30000, // Maximum reconnect delay (30 seconds)
    connectionTimeout: 10000, // Timeout for initial connection (10 seconds)
    heartbeatInterval: 30000, // Send heartbeat every 30 seconds
    pongTimeout: 5000, // Wait 5 seconds for pong response
  },

  // Message settings
  message: {
    maxSize: 1048576, // Max message size: 1MB
    queueSize: 100, // Max messages in offline queue
    batchSize: 10, // Max messages to send in batch
    batchDelay: 50, // Delay between batched messages (ms)
  },

  // Protocol settings
  protocols: [], // WebSocket subprotocols (empty for default)

  // Logging
  debug: process.env.NODE_ENV === 'development', // Enable debug logs in dev
  logCompression: true, // Log compression stats
};

/**
 * Get compression statistics from WebSocket
 * 
 * Note: Browser WebSocket API doesn't expose compression stats directly.
 * We can only check if compression was negotiated via extensions.
 * 
 * @param {WebSocket} ws - WebSocket instance
 * @returns {object} Compression info
 */
export function getCompressionInfo(ws) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    return {
      supported: false,
      active: false,
      reason: 'WebSocket not connected',
    };
  }

  // Check if extensions are supported (not available in all browsers)
  const extensions = ws.extensions || '';
  
  return {
    supported: true,
    active: extensions.includes('permessage-deflate'),
    extensions: extensions,
    estimatedSavings: extensions.includes('permessage-deflate') ? '40-70%' : '0%',
  };
}

/**
 * Calculate message size for compression threshold check
 * 
 * @param {any} data - Message data
 * @returns {number} Size in bytes
 */
export function getMessageSize(data) {
  if (typeof data === 'string') {
    // UTF-8 encoding: count bytes, not characters
    return new Blob([data]).size;
  } else if (data instanceof ArrayBuffer) {
    return data.byteLength;
  } else if (typeof data === 'object') {
    return new Blob([JSON.stringify(data)]).size;
  }
  return 0;
}

/**
 * Check if message should be compressed based on size
 * 
 * @param {any} data - Message data
 * @returns {boolean} True if message is large enough to benefit from compression
 */
export function shouldCompress(data) {
  const size = getMessageSize(data);
  return size > WebSocketConfig.compression.threshold;
}

/**
 * Format bytes to human-readable string
 * 
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted string (e.g., "1.5 KB")
 */
export function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Log WebSocket compression statistics
 * 
 * @param {WebSocket} ws - WebSocket instance
 * @param {object} stats - Message statistics (optional)
 */
export function logCompressionStats(ws, stats = {}) {
  if (!WebSocketConfig.logCompression || !WebSocketConfig.debug) {
    return;
  }

  const compressionInfo = getCompressionInfo(ws);

  console.group('🗜️ WebSocket Compression Stats');
  console.log('Status:', compressionInfo.active ? '✅ Active' : '❌ Inactive');
  console.log('Extensions:', compressionInfo.extensions || 'None');
  console.log('Estimated Savings:', compressionInfo.estimatedSavings);
  
  if (stats.messagesSent) {
    console.log('Messages Sent:', stats.messagesSent);
  }
  if (stats.totalBytes) {
    console.log('Total Data:', formatBytes(stats.totalBytes));
  }
  if (stats.compressedBytes) {
    const ratio = ((1 - stats.compressedBytes / stats.totalBytes) * 100).toFixed(1);
    console.log('Compressed:', formatBytes(stats.compressedBytes), `(${ratio}% savings)`);
  }
  
  console.groupEnd();
}

export default WebSocketConfig;
