import { openDB } from 'idb';

const DB_NAME = 'kibray-offline-queue';
const DB_VERSION = 1;
const STORE_NAME = 'requests';

/**
 * Initialize IndexedDB database for offline request queue
 */
async function initDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'id',
          autoIncrement: true,
        });
        store.createIndex('timestamp', 'timestamp');
        store.createIndex('url', 'url');
      }
    },
  });
}

/**
 * Add a failed request to the offline queue
 * @param {Object} request - Request object with url, method, body, headers
 */
export async function addToQueue(request) {
  try {
    const db = await initDB();
    const queueItem = {
      ...request,
      timestamp: Date.now(),
      retries: 0,
    };
    
    const id = await db.add(STORE_NAME, queueItem);
    console.log(`📥 Queued request ${id}:`, request.url);
    
    return id;
  } catch (error) {
    console.error('Error adding to queue:', error);
    throw error;
  }
}

/**
 * Get all queued requests
 * @returns {Array} - Array of queued request objects
 */
export async function getQueue() {
  try {
    const db = await initDB();
    const requests = await db.getAll(STORE_NAME);
    return requests;
  } catch (error) {
    console.error('Error getting queue:', error);
    return [];
  }
}

/**
 * Remove a request from the queue
 * @param {number} id - Request ID to remove
 */
export async function removeFromQueue(id) {
  try {
    const db = await initDB();
    await db.delete(STORE_NAME, id);
    console.log(`🗑️ Removed request ${id} from queue`);
  } catch (error) {
    console.error('Error removing from queue:', error);
    throw error;
  }
}

/**
 * Clear all requests from the queue
 */
export async function clearQueue() {
  try {
    const db = await initDB();
    await db.clear(STORE_NAME);
    console.log('🧹 Cleared offline queue');
  } catch (error) {
    console.error('Error clearing queue:', error);
    throw error;
  }
}

/**
 * Process all queued requests when back online
 * Attempts to replay each request in order
 */
export async function processQueue() {
  const queue = await getQueue();
  
  if (queue.length === 0) {
    console.log('✅ Offline queue is empty');
    return;
  }

  console.log(`🔄 Processing ${queue.length} queued requests...`);
  
  const results = {
    succeeded: 0,
    failed: 0,
    errors: [],
  };

  for (const request of queue) {
    try {
      const response = await fetch(request.url, {
        method: request.method,
        headers: request.headers,
        body: request.body ? JSON.stringify(request.body) : undefined,
      });

      if (response.ok) {
        // Success - remove from queue
        await removeFromQueue(request.id);
        results.succeeded++;
        console.log(`✅ Replayed request: ${request.method} ${request.url}`);
      } else {
        // HTTP error - retry later
        results.failed++;
        results.errors.push({
          id: request.id,
          error: `HTTP ${response.status}`,
          url: request.url,
        });
        console.warn(`⚠️ Request failed (${response.status}): ${request.url}`);
      }
    } catch (error) {
      // Network error - retry later
      results.failed++;
      results.errors.push({
        id: request.id,
        error: error.message,
        url: request.url,
      });
      console.error(`❌ Request error: ${request.url}`, error);
    }
  }

  console.log(`✅ Processed queue: ${results.succeeded} succeeded, ${results.failed} failed`);
  
  return results;
}

/**
 * Initialize queue processing on online event
 */
export function initOfflineQueue() {
  window.addEventListener('online', async () => {
    console.log('🌐 Back online - processing offline queue...');
    const results = await processQueue();
    
    // Show notification if there were queued requests
    if (results && (results.succeeded > 0 || results.failed > 0)) {
      const message = results.failed === 0
        ? `✅ Synced ${results.succeeded} offline changes`
        : `⚠️ Synced ${results.succeeded} changes, ${results.failed} failed`;
      
      // Optional: Show toast notification (if you have a toast system)
      console.log(message);
    }
  });

  console.log('📦 Offline queue initialized');
}
