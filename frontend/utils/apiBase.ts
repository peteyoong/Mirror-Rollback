/**
 * Canonical API Base URL Resolver
 * 
 * Single source of truth for API endpoint resolution.
 * NO localtunnel, NO hacks - just clean, predictable URL resolution.
 */

import { Platform } from 'react-native';

let _cachedBaseUrl: string | null = null;

/**
 * Helper to detect Emergent preview hosts (which don't have /api routes)
 * These hosts serve the frontend only - backend is on a different URL
 */
const isEmergentPreviewHost = (url: string): boolean => {
  return url.includes('preview.emergentagent.com') || url.includes('emergent.host');
};

/**
 * Resolve the API base URL once and cache it.
 * 
 * Priority:
 * 1. EXPO_PUBLIC_BACKEND_URL env var + /api (preferred for Emergent previews)
 * 2. EXPO_PUBLIC_API_BASE_URL env var (if set and valid)
 * 3. window.location.origin + /api (for web - ONLY if NOT an Emergent preview)
 * 4. Localhost fallback for dev
 */
export function getApiBaseUrl(): string {
  if (_cachedBaseUrl) {
    return _cachedBaseUrl;
  }

  // Check for web environment
  const isWeb = Platform.OS === 'web' && typeof window !== 'undefined';
  const origin = isWeb ? (window.location?.origin || '') : '';
  
  // Detect if we're in an Emergent preview (frontend-only host)
  const isEmergentPreview = origin && isEmergentPreviewHost(origin);

  // Priority 1: EXPO_PUBLIC_BACKEND_URL (explicit backend - preferred for Emergent previews)
  const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (backendUrl && typeof backendUrl === 'string' && backendUrl.trim().length > 0) {
    const trimmed = backendUrl.trim().replace(/\/+$/, '');
    if (!trimmed.includes('loca.lt') && (trimmed.startsWith('http://') || trimmed.startsWith('https://'))) {
      _cachedBaseUrl = `${trimmed}/api`;
      console.log('[API] base=' + _cachedBaseUrl + ' (from EXPO_PUBLIC_BACKEND_URL)');
      if (__DEV__) {
        console.log('[API] 🔍 DEBUG: origin=' + origin + ', isEmergentPreview=' + isEmergentPreview);
      }
      return _cachedBaseUrl;
    }
  }

  // Priority 2: Explicit EXPO_PUBLIC_API_BASE_URL env var
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

  // Priority 3: Web - use same origin ONLY if NOT an Emergent preview host
  if (isWeb && origin && origin !== 'null' && !isEmergentPreview) {
    _cachedBaseUrl = `${origin}/api`;
    console.log('[API] base=' + _cachedBaseUrl + ' (from window.location.origin - non-preview)');
    return _cachedBaseUrl;
  }

  // Priority 4: Dev fallback
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
