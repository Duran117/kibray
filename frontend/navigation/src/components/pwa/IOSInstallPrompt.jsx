import React, { useState, useEffect } from 'react';
import './IOSInstallPrompt.css';

function IOSInstallPrompt() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Detect iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    
    // Check if in standalone mode (already installed)
    const isInStandaloneMode = window.navigator.standalone === true;
    
    // Check if user has already seen this prompt
    const hasSeenPrompt = localStorage.getItem('ios-install-prompt-seen');

    // Show prompt if iOS, not installed, and not seen before
    if (isIOS && !isInStandaloneMode && !hasSeenPrompt) {
      // Show after 3 seconds to not be intrusive
      setTimeout(() => {
        setShow(true);
      }, 3000);
    }
  }, []);

  const handleDismiss = () => {
    localStorage.setItem('ios-install-prompt-seen', 'true');
    setShow(false);
  };

  if (!show) {
    return null;
  }

  return (
    <div className="ios-prompt-overlay" onClick={handleDismiss}>
      <div className="ios-prompt-modal" onClick={(e) => e.stopPropagation()}>
        <button className="ios-prompt-close" onClick={handleDismiss}>
          ✕
        </button>
        
        <div className="ios-prompt-header">
          <div className="ios-prompt-icon">📱</div>
          <h2>Install Kibray App</h2>
          <p>Add to your home screen for the best experience</p>
        </div>

        <div className="ios-prompt-instructions">
          <div className="ios-step">
            <div className="ios-step-number">1</div>
            <div className="ios-step-content">
              <div className="ios-step-icon">⬆️</div>
              <p>Tap the <strong>Share</strong> button at the bottom of Safari</p>
            </div>
          </div>

          <div className="ios-step">
            <div className="ios-step-number">2</div>
            <div className="ios-step-content">
              <div className="ios-step-icon">➕</div>
              <p>Scroll down and tap <strong>"Add to Home Screen"</strong></p>
            </div>
          </div>

          <div className="ios-step">
            <div className="ios-step-number">3</div>
            <div className="ios-step-content">
              <div className="ios-step-icon">✅</div>
              <p>Tap <strong>"Add"</strong> in the top right corner</p>
            </div>
          </div>
        </div>

        <div className="ios-prompt-benefits">
          <h3>Benefits:</h3>
          <ul>
            <li>🚀 Faster loading times</li>
            <li>📴 Work offline</li>
            <li>🎯 Quick access from home screen</li>
            <li>🔔 Receive notifications</li>
          </ul>
        </div>

        <button className="ios-prompt-button" onClick={handleDismiss}>
          Got it!
        </button>
      </div>
    </div>
  );
}

export default IOSInstallPrompt;
