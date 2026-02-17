/**
 * Single source of truth for API base URL.
 * NO /api suffix here - that's added at call site.
 * 
 * CONFIGURATION:
 * - Set EXPO_PUBLIC_API_BASE_URL in .env for local development
 * - Set EXPO_PUBLIC_API_BASE_URL in environment for production deployments
 * 
 * SAFETY:
 * - Each Emergent app MUST set EXPO_PUBLIC_API_BASE_URL to its OWN backend origin
 * - NO hardcoded fallback URLs - forces explicit configuration
 * - Build Info screen warns RED if frontend env ≠ backend env
 */

// Get the configured API base URL - NO HARDCODED FALLBACK
const configuredUrl = process.env.EXPO_PUBLIC_API_BASE_URL;

// Validate and export
export const API_BASE_URL: string = (() => {
  if (configuredUrl && configuredUrl.trim().length > 0) {
    const url = configuredUrl.trim().replace(/\/+$/, '');
    console.log('[API_BASE] Using configured URL:', url);
    return url;
  }
  
  // NO FALLBACK - must be explicitly configured
  // This prevents accidentally pointing to wrong environment
  console.error('[API_BASE] ❌ EXPO_PUBLIC_API_BASE_URL is NOT SET!');
  console.error('[API_BASE] Each app MUST set this to its own backend origin.');
  console.error('[API_BASE] Check .env or deployment environment variables.');
  
  // Return empty string - API calls will fail loudly
  // This is intentional - better to fail fast than silently hit wrong backend
  return '';
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
