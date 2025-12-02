import { useEffect, useRef, useState } from 'react';

/**
 * Custom hook for pull-to-refresh functionality
 * Detects pull-down gesture on mobile and triggers refresh callback
 * 
 * @param {Function} onRefresh - Callback function to execute on refresh
 * @param {Object} options - Configuration options
 * @param {number} options.threshold - Distance in pixels to trigger refresh (default: 80)
 * @param {boolean} options.enabled - Enable/disable pull-to-refresh (default: true)
 * @returns {Object} - { isRefreshing, pullDistance }
 */
export function usePullToRefresh(onRefresh, options = {}) {
  const {
    threshold = 80,
    enabled = true,
  } = options;

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  
  const touchStartY = useRef(0);
  const isPulling = useRef(false);
  const scrollableElement = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const handleTouchStart = (e) => {
      // Only trigger if at top of scroll
      scrollableElement.current = e.target.closest('[data-pull-to-refresh]') || document.documentElement;
      
      if (scrollableElement.current.scrollTop === 0) {
        touchStartY.current = e.touches[0].clientY;
        isPulling.current = true;
      }
    };

    const handleTouchMove = (e) => {
      if (!isPulling.current) return;

      const touchY = e.touches[0].clientY;
      const distance = touchY - touchStartY.current;

      // Only pull down, not up
      if (distance > 0) {
        // Add resistance
        const resistanceFactor = 0.5;
        const adjustedDistance = Math.min(distance * resistanceFactor, threshold * 1.5);
        
        setPullDistance(adjustedDistance);

        // Prevent default scroll when pulling
        if (adjustedDistance > 10) {
          e.preventDefault();
        }
      }
    };

    const handleTouchEnd = async () => {
      if (!isPulling.current) return;

      isPulling.current = false;

      // Trigger refresh if threshold reached
      if (pullDistance >= threshold) {
        setIsRefreshing(true);
        setPullDistance(0);

        try {
          await onRefresh();
        } catch (error) {
          console.error('Pull-to-refresh error:', error);
        } finally {
          setIsRefreshing(false);
        }
      } else {
        // Reset pull distance
        setPullDistance(0);
      }
    };

    // Add event listeners
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [enabled, onRefresh, pullDistance, threshold]);

  return {
    isRefreshing,
    pullDistance,
  };
}

/**
 * Pull-to-refresh indicator component
 * Shows visual feedback during pull gesture
 */
export function PullToRefreshIndicator({ pullDistance, isRefreshing, threshold = 80 }) {
  const progress = Math.min((pullDistance / threshold) * 100, 100);
  const isActive = pullDistance > 10 || isRefreshing;

  if (!isActive) return null;

  return (
    <div 
      className="pull-to-refresh"
      style={{
        transform: isRefreshing ? 'translateY(0)' : `translateY(${Math.min(pullDistance - 60, 0)}px)`,
        opacity: isRefreshing ? 1 : progress / 100,
      }}
    >
      <div 
        className="pull-to-refresh-spinner"
        style={{
          animation: isRefreshing ? 'spin 1s linear infinite' : 'none',
          transform: `rotate(${progress * 3.6}deg)`,
        }}
      />
    </div>
  );
}
