/**
 * PWA Push Notifications Setup
 * Handles push notification subscription and Firebase integration
 */

import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

// Firebase configuration (replace with your config from Firebase Console)
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "YOUR_API_KEY",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "YOUR_PROJECT.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "YOUR_PROJECT_ID",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "YOUR_PROJECT.appspot.com",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "YOUR_SENDER_ID",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "YOUR_APP_ID",
};

// VAPID key for Web Push (get from Firebase Console -> Project Settings -> Cloud Messaging)
const VAPID_KEY = process.env.REACT_APP_FIREBASE_VAPID_KEY || 'YOUR_VAPID_KEY';

let firebaseApp = null;
let messaging = null;

/**
 * Initialize Firebase app
 */
export function initializeFirebase() {
  try {
    if (!firebaseApp) {
      firebaseApp = initializeApp(firebaseConfig);
      messaging = getMessaging(firebaseApp);
      console.log('🔥 Firebase initialized');
    }
    return true;
  } catch (error) {
    console.error('Failed to initialize Firebase:', error);
    return false;
  }
}

/**
 * Request notification permission from user
 * @returns {Promise<string>} - Permission status: 'granted', 'denied', or 'default'
 */
export async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission();
    console.log('🔔 Notification permission:', permission);
    return permission;
  } catch (error) {
    console.error('Error requesting notification permission:', error);
    return 'denied';
  }
}

/**
 * Subscribe to push notifications
 * Gets FCM token and sends to backend
 * @returns {Promise<string|null>} - FCM token or null on failure
 */
export async function subscribeToPushNotifications() {
  try {
    // Check if notifications are supported
    if (!('Notification' in window)) {
      console.warn('Notifications not supported');
      return null;
    }

    // Request permission
    const permission = await requestNotificationPermission();
    if (permission !== 'granted') {
      console.log('Notification permission denied');
      return null;
    }

    // Initialize Firebase
    if (!initializeFirebase()) {
      return null;
    }

    // Get FCM token
    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY,
    });

    if (token) {
      console.log('📱 FCM Token:', token);

      // Send token to backend
      const response = await fetch('/api/v1/push/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          endpoint: token,
          p256dh: '', // Not used with FCM
          auth: '',   // Not used with FCM
        }),
      });

      if (response.ok) {
        console.log('✅ Push subscription saved to backend');
        localStorage.setItem('fcm_token', token);
        return token;
      } else {
        console.error('Failed to save subscription:', await response.text());
        return null;
      }
    } else {
      console.log('No registration token available');
      return null;
    }
  } catch (error) {
    console.error('Error subscribing to push notifications:', error);
    return null;
  }
}

/**
 * Unsubscribe from push notifications
 */
export async function unsubscribeFromPushNotifications() {
  try {
    const token = localStorage.getItem('fcm_token');
    
    if (!token) {
      console.log('No FCM token found');
      return;
    }

    // Remove from backend
    const response = await fetch('/api/v1/push/unsubscribe/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        endpoint: token,
      }),
    });

    if (response.ok) {
      console.log('✅ Unsubscribed from push notifications');
      localStorage.removeItem('fcm_token');
    } else {
      console.error('Failed to unsubscribe:', await response.text());
    }
  } catch (error) {
    console.error('Error unsubscribing:', error);
  }
}

/**
 * Listen for foreground messages (when app is open)
 * @param {Function} callback - Called when message received with (payload) argument
 */
export function onMessageListener(callback) {
  if (!messaging) {
    initializeFirebase();
  }

  if (messaging) {
    return onMessage(messaging, (payload) => {
      console.log('📩 Foreground message received:', payload);
      
      // Show notification even when app is open
      if (payload.notification) {
        const { title, body, icon } = payload.notification;
        
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(title, {
            body: body,
            icon: icon || '/static/icons/icon-192x192.png',
            badge: '/static/icons/badge-72x72.png',
            data: payload.data,
          });
        }
      }

      // Call user's callback
      if (callback) {
        callback(payload);
      }
    });
  }

  return () => {};
}

/**
 * Check if push notifications are supported and enabled
 * @returns {boolean}
 */
export function isPushNotificationSupported() {
  return 'Notification' in window &&
         'serviceWorker' in navigator &&
         'PushManager' in window;
}

/**
 * Get current notification permission status
 * @returns {string} - 'granted', 'denied', or 'default'
 */
export function getNotificationPermission() {
  if ('Notification' in window) {
    return Notification.permission;
  }
  return 'denied';
}
