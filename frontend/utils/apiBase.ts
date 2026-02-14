/**
 * Canonical API Base URL Resolver
 * 
 * Single source of truth for API endpoint resolution.
 * NO localtunnel, NO hacks - just clean, predictable URL resolution.
 */

import { Platform } from 'react-native';

let _cachedBaseUrl: string | null = null;

/**
 * Resolve the API base URL once and cache it.
 * 
 * Priority:
 * 1. EXPO_PUBLIC_API_BASE_URL env var (if set and valid)
 * 2. window.location.origin + /api (for web)
 * 3. Localhost fallback for dev
 */
export function getApiBaseUrl(): string {
  if (_cachedBaseUrl) {
    return _cachedBaseUrl;
  }

  // Priority 1: Explicit env var
  const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim().length > 0) {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    // Skip localtunnel URLs - we want to use origin instead
    if (!trimmed.includes('loca.lt') && (trimmed.startsWith('http://') || trimmed.startsWith('https://'))) {
      _cachedBaseUrl = trimmed;
      console.log('[API] base=' + _cachedBaseUrl + ' (from EXPO_PUBLIC_API_BASE_URL)');
      return _cachedBaseUrl;
    }
  }

  // Priority 2: Web - use same origin
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location?.origin) {
    const origin = window.location.origin;
    if (origin && origin !== 'null') {
      _cachedBaseUrl = `${origin}/api`;
      console.log('[API] base=' + _cachedBaseUrl + ' (from window.location.origin)');
      return _cachedBaseUrl;
    }
  }

  // Priority 3: Dev fallback
  if (__DEV__) {
    _cachedBaseUrl = 'http://localhost:8001/api';
    console.log('[API] base=' + _cachedBaseUrl + ' (dev fallback)');
    return _cachedBaseUrl;
  }

  // Final fallback - should not reach here in production
  _cachedBaseUrl = '/api';
  console.log('[API] base=' + _cachedBaseUrl + ' (relative fallback)');
  return _cachedBaseUrl;
}

/**
 * Safely join base URL with path
 */
export function joinUrl(base: string, path: string): string {
  const cleanBase = base.replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

/**
 * Make a fetch request to the API
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = joinUrl(getApiBaseUrl(), path);
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  return fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'omit',
    mode: 'cors',
  });
}

// Export the base URL (resolved once at import time)
export const API_BASE_URL = getApiBaseUrl();
