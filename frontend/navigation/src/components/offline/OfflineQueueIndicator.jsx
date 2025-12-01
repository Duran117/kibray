import React from 'react';
import { Clock, Send, AlertCircle, CheckCircle, Trash2 } from 'lucide-react';
import './OfflineQueueIndicator.css';

/**
 * Offline Queue Indicator Component
 * Phase 6 - Improvement #11: Offline Message Queue
 * 
 * Visual indicator showing pending offline messages
 * 
 * Props:
 * - queueSize: number - Number of messages in queue
 * - isSending: boolean - Whether queue is being processed
 * - lastError: string - Last error message
 * - onRetry: function - Callback to retry sending
 * - onClear: function - Callback to clear queue
 * - compact: boolean - Compact mode (badge only)
 */
const OfflineQueueIndicator = ({
  queueSize = 0,
  isSending = false,
  lastError = null,
  onRetry,
  onClear,
  compact = false,
}) => {
  if (queueSize === 0 && !isSending) {
    return null; // Don't show when queue is empty
  }

  if (compact) {
    return (
      <div className="offline-queue-badge" title={`${queueSize} pending messages`}>
        <Clock size={14} />
        <span className="queue-count">{queueSize}</span>
      </div>
    );
  }

  return (
    <div className={`offline-queue-indicator ${lastError ? 'has-error' : ''}`}>
      <div className="queue-header">
        <div className="queue-icon">
          {isSending ? (
            <Send size={16} className="icon-sending" />
          ) : lastError ? (
            <AlertCircle size={16} className="icon-error" />
          ) : (
            <Clock size={16} className="icon-pending" />
          )}
        </div>
        <div className="queue-info">
          {isSending ? (
            <span className="queue-status">Sending messages...</span>
          ) : lastError ? (
            <span className="queue-status error">Failed to send</span>
          ) : (
            <span className="queue-status">
              {queueSize} {queueSize === 1 ? 'message' : 'messages'} pending
            </span>
          )}
        </div>
        <div className="queue-count-badge">{queueSize}</div>
      </div>

      {lastError && (
        <div className="queue-error">
          <AlertCircle size={12} />
          <span>{lastError}</span>
        </div>
      )}

      {!isSending && queueSize > 0 && (
        <div className="queue-actions">
          {onRetry && (
            <button
              className="queue-action-btn retry-btn"
              onClick={onRetry}
              title="Retry sending messages"
            >
              <Send size={14} />
              <span>Retry</span>
            </button>
          )}
          {onClear && (
            <button
              className="queue-action-btn clear-btn"
              onClick={onClear}
              title="Clear pending messages"
            >
              <Trash2 size={14} />
              <span>Clear</span>
            </button>
          )}
        </div>
      )}

      {isSending && (
        <div className="queue-progress">
          <div className="progress-bar">
            <div className="progress-bar-fill"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OfflineQueueIndicator;
