import React from 'react';
import { useOnline } from '../../hooks/useOnline.js';
import './OfflineBanner.css';

/**
 * Offline status banner component
 * Shows a fixed banner at top when offline
 * Auto-hides when connection restored
 */
function OfflineBanner() {
  const isOnline = useOnline();

  // Don't render if online
  if (isOnline) {
    return null;
  }

  return (
    <div className="offline-banner">
      <div className="offline-banner-content">
        <span className="offline-icon">📵</span>
        <div className="offline-text">
          <strong>You're offline</strong>
          <span className="offline-subtext">
            Some features may be limited. We'll reconnect automatically.
          </span>
        </div>
        <span className="offline-pulse"></span>
      </div>
    </div>
  );
}

export default OfflineBanner;
