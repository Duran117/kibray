/**
 * Mobile Viewport Height Fix
 * Fixes iOS Safari address bar causing viewport height issues
 * Sets CSS custom property --vh for accurate viewport calculations
 */

export function initMobileViewportFix() {
  // Calculate and set --vh custom property
  function setViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
  }

  // Set on load
  setViewportHeight();

  // Update on resize and orientation change
  window.addEventListener('resize', setViewportHeight);
  window.addEventListener('orientationchange', setViewportHeight);

  console.log('📱 Mobile viewport height fix initialized');
}

/**
 * Detect if running on mobile device
 * @returns {boolean}
 */
export function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Detect if running on iOS
 * @returns {boolean}
 */
export function isIOS() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

/**
 * Detect if running as standalone PWA
 * @returns {boolean}
 */
export function isPWAStandalone() {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );
}

/**
 * Get device orientation
 * @returns {'portrait'|'landscape'}
 */
export function getOrientation() {
  return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
}

/**
 * Detect if user prefers reduced motion
 * @returns {boolean}
 */
export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Detect if user prefers dark mode
 * @returns {boolean}
 */
export function prefersDarkMode() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/**
 * Lock screen orientation (PWA only)
 * @param {'portrait'|'landscape'} orientation
 */
export async function lockOrientation(orientation) {
  if (!screen.orientation) {
    console.warn('Screen Orientation API not supported');
    return false;
  }

  try {
    await screen.orientation.lock(orientation);
    return true;
  } catch (error) {
    console.error('Failed to lock orientation:', error);
    return false;
  }
}

/**
 * Unlock screen orientation
 */
export function unlockOrientation() {
  if (screen.orientation) {
    screen.orientation.unlock();
  }
}

/**
 * Vibrate device (mobile only)
 * @param {number|number[]} pattern - Duration or pattern array
 */
export function vibrate(pattern = 200) {
  if ('vibrate' in navigator) {
    navigator.vibrate(pattern);
  }
}

/**
 * Request wake lock to prevent screen from sleeping
 * Useful for long-running tasks like timers
 * @returns {Promise<WakeLockSentinel|null>}
 */
export async function requestWakeLock() {
  if (!('wakeLock' in navigator)) {
    console.warn('Wake Lock API not supported');
    return null;
  }

  try {
    const wakeLock = await navigator.wakeLock.request('screen');
    console.log('🔓 Wake lock acquired');
    
    wakeLock.addEventListener('release', () => {
      console.log('🔒 Wake lock released');
    });
    
    return wakeLock;
  } catch (error) {
    console.error('Failed to acquire wake lock:', error);
    return null;
  }
}

/**
 * Share content using native share dialog (mobile)
 * @param {Object} data - { title, text, url }
 * @returns {Promise<boolean>}
 */
export async function shareContent(data) {
  if (!navigator.share) {
    console.warn('Web Share API not supported');
    return false;
  }

  try {
    await navigator.share(data);
    return true;
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('Share failed:', error);
    }
    return false;
  }
}
