import React, { useState } from 'react';
import OfflineQueueIndicator from './OfflineQueueIndicator';
import offlineQueue from '../../services/offlineQueue';
import { useQueueStats } from '../../hooks/useOfflineQueue';
import './OfflineQueueExamples.css';

/**
 * Offline Queue Examples
 * Demonstrates offline message queue functionality
 */
const OfflineQueueExamples = () => {
  const [queueSize, setQueueSize] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [lastError, setLastError] = useState(null);
  const stats = useQueueStats();

  // Subscribe to queue changes
  React.useEffect(() => {
    const unsubscribe = offlineQueue.subscribe(({ queueSize }) => {
      setQueueSize(queueSize);
    });
    setQueueSize(offlineQueue.size());
    return unsubscribe;
  }, []);

  const handleAddMessage = () => {
    offlineQueue.enqueue('chat', {
      type: 'chat_message',
      message: `Test message ${Date.now()}`,
    }, 'general');
  };

  const handleAddMultiple = () => {
    for (let i = 0; i < 5; i++) {
      offlineQueue.enqueue('chat', {
        type: 'chat_message',
        message: `Bulk message ${i + 1}`,
      }, 'general');
    }
  };

  const handleSimulateSending = () => {
    setIsSending(true);
    setLastError(null);
    
    setTimeout(() => {
      setIsSending(false);
      // Randomly succeed or fail
      if (Math.random() > 0.5) {
        offlineQueue.clear();
      } else {
        setLastError('Network error: Connection timeout');
      }
    }, 2000);
  };

  const handleRetry = () => {
    setLastError(null);
    handleSimulateSending();
  };

  const handleClear = () => {
    offlineQueue.clear();
    setLastError(null);
  };

  return (
    <div className="offline-queue-examples">
      <h2>Offline Message Queue Examples</h2>

      {/* Example 1: Basic Indicator */}
      <section className="example-section">
        <h3>1. Queue Indicator (Dynamic)</h3>
        <div className="example-demo">
          <OfflineQueueIndicator
            queueSize={queueSize}
            isSending={isSending}
            lastError={lastError}
            onRetry={handleRetry}
            onClear={handleClear}
          />
          {queueSize === 0 && !isSending && (
            <p className="empty-state">Queue is empty - Add messages to see indicator</p>
          )}
        </div>
        <div className="example-controls">
          <button onClick={handleAddMessage} className="control-btn">
            Add 1 Message
          </button>
          <button onClick={handleAddMultiple} className="control-btn">
            Add 5 Messages
          </button>
          <button
            onClick={handleSimulateSending}
            className="control-btn primary"
            disabled={queueSize === 0 || isSending}
          >
            Simulate Sending
          </button>
          <button
            onClick={handleClear}
            className="control-btn danger"
            disabled={queueSize === 0}
          >
            Clear Queue
          </button>
        </div>
      </section>

      {/* Example 2: Different States */}
      <section className="example-section">
        <h3>2. Different States</h3>
        <div className="states-grid">
          <div className="state-item">
            <h4>Empty (Hidden)</h4>
            <OfflineQueueIndicator queueSize={0} />
            <p className="state-note">Indicator is hidden when queue is empty</p>
          </div>
          
          <div className="state-item">
            <h4>Pending (3 messages)</h4>
            <OfflineQueueIndicator queueSize={3} />
          </div>
          
          <div className="state-item">
            <h4>Sending</h4>
            <OfflineQueueIndicator queueSize={5} isSending={true} />
          </div>
          
          <div className="state-item">
            <h4>Error</h4>
            <OfflineQueueIndicator
              queueSize={2}
              lastError="Connection timeout"
              onRetry={() => {}}
              onClear={() => {}}
            />
          </div>
        </div>
      </section>

      {/* Example 3: Compact Mode */}
      <section className="example-section">
        <h3>3. Compact Badge</h3>
        <div className="compact-demo">
          <p>Use in navigation bars or tight spaces:</p>
          <div className="mock-navbar-compact">
            <span>Navigation</span>
            <OfflineQueueIndicator queueSize={3} compact />
          </div>
        </div>
      </section>

      {/* Example 4: Queue Statistics */}
      <section className="example-section">
        <h3>4. Queue Statistics (Live)</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Messages</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-value">{stats.byType.chat || 0}</div>
            <div className="stat-label">Chat Messages</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-value">{stats.byRetryCount[0] || 0}</div>
            <div className="stat-label">No Retries</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-value">
              {(stats.byRetryCount[1] || 0) + (stats.byRetryCount[2] || 0)}
            </div>
            <div className="stat-label">Retry Attempts</div>
          </div>
        </div>
        
        {stats.oldest && (
          <p className="stats-note">
            Oldest message: {new Date(stats.oldest).toLocaleTimeString()}
          </p>
        )}
      </section>

      {/* Example 5: Code Usage */}
      <section className="example-section code-examples">
        <h3>5. Usage Code Examples</h3>

        <div className="code-block">
          <h4>Basic Integration:</h4>
          <pre>{`import { useOfflineQueue } from '../../hooks/useOfflineQueue';
import OfflineQueueIndicator from './OfflineQueueIndicator';

function ChatPanel() {
  const { isConnected, sendChatMessage } = useChat();
  
  const {
    queueSize,
    isSending,
    lastError,
    sendOrQueue,
    retryFailed,
    clearQueue,
  } = useOfflineQueue({
    isConnected,
    sendMessage: sendChatMessage,
    type: 'chat',
    channelId: 'general',
  });

  return (
    <>
      <OfflineQueueIndicator
        queueSize={queueSize}
        isSending={isSending}
        lastError={lastError}
        onRetry={retryFailed}
        onClear={clearQueue}
      />
      {/* ...rest of chat UI */}
    </>
  );
}`}</pre>
        </div>

        <div className="code-block">
          <h4>Sending Messages:</h4>
          <pre>{`// In your send handler
const handleSendMessage = (text) => {
  // Automatically queues if offline
  const result = sendOrQueue({
    type: 'chat_message',
    message: text
  });
  
  if (result.queued) {
    console.log('Message queued:', result.queueId);
  }
};`}</pre>
        </div>

        <div className="code-block">
          <h4>Direct Queue Access:</h4>
          <pre>{`import offlineQueue from '../../services/offlineQueue';

// Add to queue
offlineQueue.enqueue('chat', messageData, channelId);

// Get queue size
const size = offlineQueue.size();

// Get messages by type
const chatMessages = offlineQueue.getByType('chat');

// Clear queue
offlineQueue.clear();`}</pre>
        </div>
      </section>
    </div>
  );
};

export default OfflineQueueExamples;
