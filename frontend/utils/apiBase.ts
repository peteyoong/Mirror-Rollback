/**
 * Canonical API Base URL Resolver
 * 
 * SIMPLIFIED: Single deterministic backend URL.
 * NO localhost, NO ngrok, NO window.location, NO fallbacks.
 */

// ============================================
// SINGLE DETERMINISTIC BACKEND URL
// ============================================
const PRODUCTION_API_BASE = 'https://mirror-fix.preview.emergentagent.com/api';

/**
 * Get the API base URL.
 * Uses env var if set, otherwise uses the hardcoded production URL.
 */
export function getApiBaseUrl(): string {
  // Check for explicit env var override
  const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim().length > 0) {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    console.log('[API] base=' + trimmed + ' (from EXPO_PUBLIC_API_BASE_URL)');
    return trimmed;
  }
  
  // Use production URL
  console.log('[API] base=' + PRODUCTION_API_BASE + ' (hardcoded production)');
  return PRODUCTION_API_BASE;
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
