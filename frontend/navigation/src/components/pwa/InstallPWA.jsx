import React, { useState, useEffect } from 'react';
import './InstallPWA.css';

function InstallPWA() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [installable, setInstallable] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      // Stash the event so it can be triggered later
      setDeferredPrompt(e);
      setInstallable(true);
      console.log('💾 Install prompt ready');
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) {
      return;
    }

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    
    console.log(`User ${outcome === 'accepted' ? 'accepted' : 'dismissed'} the install prompt`);

    // Clear the deferredPrompt for next time
    setDeferredPrompt(null);
    setInstallable(false);

    // Hide the install button
    if (outcome === 'accepted') {
      console.log('✅ PWA installed successfully');
    }
  };

  // Don't show if not installable
  if (!installable) {
    return null;
  }

  return (
    <div className="install-pwa-banner">
      <div className="install-pwa-content">
        <div className="install-pwa-icon">📱</div>
        <div className="install-pwa-text">
          <h3>Install Kibray App</h3>
          <p>Get quick access and work offline</p>
        </div>
      </div>
      <div className="install-pwa-actions">
        <button 
          className="install-button-primary" 
          onClick={handleInstall}
          aria-label="Install app"
        >
          Install
        </button>
        <button 
          className="install-button-dismiss" 
          onClick={() => setInstallable(false)}
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

export default InstallPWA;
