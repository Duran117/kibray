import { useState, useEffect } from 'react';

/**
 * Custom hook to detect online/offline status
 * Listens to browser online/offline events
 * @returns {boolean} - Current online status
 */
export function useOnline() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    // Update online status
    const handleOnline = () => {
      console.log('🌐 Connection restored');
      setIsOnline(true);
    };

    const handleOffline = () => {
      console.warn('📵 Connection lost');
      setIsOnline(false);
    };

    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
