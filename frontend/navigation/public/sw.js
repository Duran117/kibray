/**
 * Service Worker for Push Notifications
 * 
 * Handles:
 * - Push notification events
 * - Notification clicks
 * - Background sync
 * - Offline fallbacks
 */

// Service Worker version
const SW_VERSION = '1.0.0';
const CACHE_NAME = `kibray-push-v${SW_VERSION}`;

// Install event
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker version:', SW_VERSION);
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker version:', SW_VERSION);
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith('kibray-push-') && name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

/**
 * Push event - Received when a push notification is sent
 */
self.addEventListener('push', (event) => {
  console.log('[SW] Push received:', event);

  let notificationData = {
    title: 'New Notification',
    body: 'You have a new notification',
    icon: '/static/images/logo.png',
    badge: '/static/images/badge.png',
    tag: 'default',
    requireInteraction: false,
  };

  // Parse notification data
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = {
        title: data.title || notificationData.title,
        body: data.body || data.message || notificationData.body,
        icon: data.icon || notificationData.icon,
        badge: data.badge || notificationData.badge,
        tag: data.tag || data.type || notificationData.tag,
        data: data,
        requireInteraction: data.requireInteraction || false,
        actions: data.actions || [],
        vibrate: data.vibrate || [200, 100, 200],
      };

      // Add image if available
      if (data.image) {
        notificationData.image = data.image;
      }
    } catch (error) {
      console.error('[SW] Failed to parse push data:', error);
    }
  }

  // Show notification
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

/**
 * Notification click event
 */
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event);

  event.notification.close();

  const notification = event.notification;
  const data = notification.data || {};
  
  // Determine URL to open
  let urlToOpen = '/';
  
  if (data.url) {
    urlToOpen = data.url;
  } else if (data.type === 'chat' && data.channel_id) {
    urlToOpen = `/chat/${data.channel_id}`;
  } else if (data.type === 'mention' && data.message_id) {
    urlToOpen = `/chat/${data.channel_id}?message=${data.message_id}`;
  } else if (data.type === 'task' && data.task_id) {
    urlToOpen = `/tasks/${data.task_id}`;
  }

  // Handle action button clicks
  if (event.action) {
    console.log('[SW] Action clicked:', event.action);
    
    if (event.action === 'open') {
      // Open the notification URL
    } else if (event.action === 'dismiss') {
      // Just close (already done above)
      return;
    } else if (event.action === 'reply' && data.channel_id) {
      // Open reply interface
      urlToOpen = `/chat/${data.channel_id}?reply=true`;
    }
  }

  // Open or focus client
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (const client of clientList) {
          if (client.url.includes(urlToOpen) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

/**
 * Notification close event
 */
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed:', event);
  
  const notification = event.notification;
  const data = notification.data || {};
  
  // Track notification dismissal
  if (data.track_dismissal) {
    event.waitUntil(
      fetch('/api/notifications/track/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notification_id: data.id,
          action: 'dismissed',
          timestamp: new Date().toISOString(),
        }),
      }).catch((error) => {
        console.error('[SW] Failed to track dismissal:', error);
      })
    );
  }
});

/**
 * Message event - Communication from client
 */
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: SW_VERSION });
  }
});

/**
 * Background Sync event (optional)
 * Useful for queuing failed notification actions
 */
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-notifications') {
    event.waitUntil(
      syncNotifications()
    );
  }
});

/**
 * Sync notifications with server
 */
async function syncNotifications() {
  try {
    const response = await fetch('/api/notifications/sync/');
    const data = await response.json();
    
    console.log('[SW] Synced notifications:', data);
    
    // Show any pending notifications
    if (data.pending && Array.isArray(data.pending)) {
      for (const notification of data.pending) {
        await self.registration.showNotification(notification.title, {
          body: notification.body,
          icon: notification.icon || '/static/images/logo.png',
          badge: notification.badge || '/static/images/badge.png',
          data: notification.data,
        });
      }
    }
    
    return true;
  } catch (error) {
    console.error('[SW] Failed to sync notifications:', error);
    throw error;
  }
}

/**
 * Fetch event - Intercept network requests (optional)
 * Can be used for offline support
 */
self.addEventListener('fetch', (event) => {
  // Only handle same-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Network-first strategy for API calls
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return new Response(
            JSON.stringify({ error: 'Offline' }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        })
    );
    return;
  }

  // Cache-first for static assets
  if (event.request.url.includes('/static/')) {
    event.respondWith(
      caches.match(event.request)
        .then((response) => response || fetch(event.request))
    );
    return;
  }
});

// Log service worker ready
console.log('[SW] Service Worker loaded, version:', SW_VERSION);
