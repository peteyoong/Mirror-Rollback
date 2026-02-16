/**
 * API Health Check Utility
 * Detects sleeping/unavailable backends and shows appropriate errors
 */

import { API_BASE_URL } from './apiBase';

export interface HealthCheckResult {
  ok: boolean;
  isAwake: boolean;
  isSleeping: boolean;
  isWrongUrl: boolean;
  message: string;
  details?: {
    build_version?: string;
    build_id?: string;
    env?: string;
  };
}

// Known sleep page indicators
const SLEEP_INDICATORS = [
  'wake up',
  'waking up',
  'server is sleeping',
  'starting up',
  'please wait',
  'emergent',
  'preview is asleep',
];

/**
 * Check if the backend is awake and responding correctly
 */
export async function checkBackendHealth(): Promise<HealthCheckResult> {
  try {
    const healthUrl = `${API_BASE_URL}/api/health`;
    console.log('[HealthCheck] Checking:', healthUrl);
    
    const response = await fetch(healthUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      // Short timeout - if sleeping, fail fast
      signal: AbortSignal.timeout(10000),
    });
    
    const contentType = response.headers.get('content-type') || '';
    const text = await response.text();
    
    // Check if response is HTML (likely a sleep page)
    if (contentType.includes('text/html') || text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html')) {
      const lowerText = text.toLowerCase();
      const isSleepPage = SLEEP_INDICATORS.some(indicator => lowerText.includes(indicator));
      
      return {
        ok: false,
        isAwake: false,
        isSleeping: isSleepPage,
        isWrongUrl: !isSleepPage,
        message: isSleepPage 
          ? 'Backend is sleeping. Please use the staging link or wait for it to wake up.'
          : 'Backend returned HTML instead of JSON. Wrong URL or misconfigured.',
      };
    }
    
    // Try to parse as JSON
    try {
      const data = JSON.parse(text);
      
      // Valid health response
      if (data.build || data.ok || data.env) {
        return {
          ok: true,
          isAwake: true,
          isSleeping: false,
          isWrongUrl: false,
          message: 'Backend is healthy',
          details: {
            build_version: data.build || data.build_version,
            build_id: data.build_id,
            env: data.env,
          },
        };
      }
      
      // Unexpected JSON structure
      return {
        ok: false,
        isAwake: true,
        isSleeping: false,
        isWrongUrl: true,
        message: 'Backend responded but health check format is unexpected',
      };
      
    } catch (parseError) {
      return {
        ok: false,
        isAwake: false,
        isSleeping: false,
        isWrongUrl: true,
        message: 'Backend response is not valid JSON',
      };
    }
    
  } catch (error: any) {
    // Network error or timeout
    const isTimeout = error.name === 'TimeoutError' || error.message?.includes('timeout');
    
    return {
      ok: false,
      isAwake: false,
      isSleeping: isTimeout, // Timeouts often mean sleeping server
      isWrongUrl: false,
      message: isTimeout 
        ? 'Backend did not respond in time. It may be sleeping or unavailable.'
        : `Network error: ${error.message}`,
    };
  }
}

/**
 * Validate API_BASE_URL is properly configured
 */
export function validateApiConfig(): { valid: boolean; message: string } {
  if (!API_BASE_URL) {
    return {
      valid: false,
      message: 'EXPO_PUBLIC_API_BASE_URL is not configured',
    };
  }
  
  if (API_BASE_URL === 'MISSING_API_BASE_URL') {
    return {
      valid: false,
      message: 'API base URL is not set. Please configure EXPO_PUBLIC_API_BASE_URL.',
    };
  }
  
  if (!API_BASE_URL.startsWith('http://') && !API_BASE_URL.startsWith('https://')) {
    return {
      valid: false,
      message: 'API base URL must start with http:// or https://',
    };
  }
  
  return {
    valid: true,
    message: 'API configuration is valid',
  };
}
