/**
 * Single source of truth for API base URL.
 * NO /api suffix here - that's added at call site.
 * 
 * CONFIGURATION:
 * - Set EXPO_PUBLIC_API_BASE_URL in .env for local development
 * - Set EXPO_PUBLIC_API_BASE_URL in environment for production deployments
 * 
 * FALLBACK BEHAVIOR:
 * - If env var is missing, uses preview URL (for development only)
 * - Production builds MUST have EXPO_PUBLIC_API_BASE_URL set
 */

// Default fallback for development - DO NOT rely on this in production
const DEV_FALLBACK_URL = 'https://cachebusting-fix.preview.emergentagent.com';

// Get the configured API base URL
const configuredUrl = process.env.EXPO_PUBLIC_API_BASE_URL;

// Validate and export
export const API_BASE_URL: string = (() => {
  if (configuredUrl && configuredUrl.trim().length > 0) {
    const url = configuredUrl.trim().replace(/\/+$/, '');
    console.log('[API_BASE] Using configured URL:', url);
    return url;
  }
  
  // Development fallback
  if (__DEV__) {
    console.warn('[API_BASE] ⚠️ EXPO_PUBLIC_API_BASE_URL not set, using dev fallback:', DEV_FALLBACK_URL);
    return DEV_FALLBACK_URL;
  }
  
  // Production without config - use fallback but warn loudly
  console.error('[API_BASE] ❌ EXPO_PUBLIC_API_BASE_URL not configured for production!');
  console.error('[API_BASE] Using fallback URL - this should be fixed in deployment config');
  return DEV_FALLBACK_URL;
})();

// Flag to indicate if we're using fallback
export const IS_USING_FALLBACK_URL = !configuredUrl || configuredUrl.trim().length === 0;

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
 */
export function getApiUrl(endpoint: string): string {
  const path = endpoint.startsWith('/api') ? endpoint : `/api${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  return joinUrl(API_BASE_URL, path);
}
