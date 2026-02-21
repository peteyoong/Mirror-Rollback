/**
 * Single source of truth for API base URL.
 * NO /api suffix here - that's added at call site.
 * 
 * CONFIGURATION:
 * - Set EXPO_PUBLIC_API_BASE_URL in .env for local development
 * - Set EXPO_PUBLIC_API_BASE_URL in environment for production deployments
 * 
 * ALWAYS-ON FALLBACK:
 * - If EXPO_PUBLIC_API_BASE_URL is missing/empty, uses the always-on deployed host
 * - This ensures Expo Go native builds NEVER use relative URLs (which break on native)
 * - Fallback: https://mirror-lens-fixes.emergent.host
 */

// ALWAYS-ON deployed host - NEVER sleeps
const ALWAYS_ON_HOST = 'https://mirror-lens-fixes.emergent.host';

// Get the configured API base URL
const raw = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();

// Validate and export - with ALWAYS-ON fallback
export const API_BASE_URL: string = (() => {
  // Use configured URL if present and non-empty
  if (raw && raw.length > 0) {
    // Ensure it starts with http/https (native requires absolute URLs)
    const url = raw.startsWith('http') ? raw : `https://${raw}`;
    const cleanUrl = url.replace(/\/+$/, '');
    console.log('[API_BASE] Using configured URL:', cleanUrl);
    return cleanUrl;
  }
  
  // FALLBACK to always-on host - critical for Expo Go native
  console.warn('[API_BASE] ⚠️ EXPO_PUBLIC_API_BASE_URL not set, using always-on fallback');
  console.log('[API_BASE] Fallback URL:', ALWAYS_ON_HOST);
  return ALWAYS_ON_HOST;
})();

// Flag to indicate if we're using fallback
export const IS_USING_FALLBACK_URL = !raw || raw.length === 0;

/**
 * Safely join base URL with a path.
 * Handles trailing/leading slashes correctly.
 */
export function joinUrl(base: string, path: string): string {
  const cleanBase = base.replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

/**
 * Get API URL for a specific endpoint
 * Automatically prepends /api prefix
 * ALWAYS returns absolute URL (required for native)
 */
export function getApiUrl(endpoint: string): string {
  const path = endpoint.startsWith('/api') ? endpoint : `/api${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  return joinUrl(API_BASE_URL, path);
}
