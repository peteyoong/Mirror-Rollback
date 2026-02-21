/**
 * Staging Keep-Alive Utility
 * ==========================
 * 
 * Prevents the staging backend from sleeping by pinging it periodically.
 * 
 * ONLY runs in staging environment (EXPO_PUBLIC_ENV === 'staging')
 * Does NOT affect production.
 * 
 * Usage:
 *   import { startStagingKeepAlive, stopStagingKeepAlive } from './stagingKeepAlive';
 *   
 *   useEffect(() => {
 *     startStagingKeepAlive();
 *     return () => stopStagingKeepAlive();
 *   }, []);
 */

import { API_BASE_URL } from './apiBase';

// Environment check
const IS_STAGING = process.env.EXPO_PUBLIC_ENV === 'staging';

// Keepalive interval (4 minutes = 240000ms)
const KEEPALIVE_INTERVAL_MS = 4 * 60 * 1000;

// Timeout for health check (10 seconds)
const HEALTH_CHECK_TIMEOUT_MS = 10 * 1000;

// Store interval ID
let keepAliveIntervalId: ReturnType<typeof setInterval> | null = null;

// Track if we've already started (prevent duplicate starts)
let isStarted = false;

/**
 * Ping the backend health endpoint
 * Silently ignores errors - we just want to keep the server awake
 */
async function pingHealth(): Promise<void> {
  try {
    const healthUrl = `${API_BASE_URL}/api/health`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT_MS);
    
    const response = await fetch(healthUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      console.log('[KEEPALIVE] ✓ ping successful');
    } else {
      console.log('[KEEPALIVE] ping returned:', response.status);
    }
  } catch (error: any) {
    // Silently ignore errors - don't show UI alerts
    // Just log for debugging
    if (error.name === 'AbortError') {
      console.log('[KEEPALIVE] ping timed out (server may be waking)');
    } else {
      console.log('[KEEPALIVE] ping error (ignored):', error.message);
    }
  }
}

/**
 * Start the staging keepalive interval
 * Only runs in staging environment
 */
export function startStagingKeepAlive(): void {
  // Only run in staging
  if (!IS_STAGING) {
    console.log('[KEEPALIVE] skipped - not staging environment');
    return;
  }
  
  // Prevent duplicate starts
  if (isStarted) {
    console.log('[KEEPALIVE] already running');
    return;
  }
  
  isStarted = true;
  
  // Log startup (once per app launch)
  console.log(`[KEEPALIVE] staging keepalive started -> ${API_BASE_URL}`);
  console.log(`[KEEPALIVE] interval: ${KEEPALIVE_INTERVAL_MS / 1000 / 60} minutes`);
  
  // Initial ping
  pingHealth();
  
  // Start interval
  keepAliveIntervalId = setInterval(() => {
    pingHealth();
  }, KEEPALIVE_INTERVAL_MS);
}

/**
 * Stop the staging keepalive interval
 */
export function stopStagingKeepAlive(): void {
  if (keepAliveIntervalId) {
    clearInterval(keepAliveIntervalId);
    keepAliveIntervalId = null;
    console.log('[KEEPALIVE] stopped');
  }
  isStarted = false;
}

/**
 * Check if keepalive is currently running
 */
export function isKeepAliveRunning(): boolean {
  return isStarted && keepAliveIntervalId !== null;
}
