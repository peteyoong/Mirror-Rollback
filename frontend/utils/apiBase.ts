/**
 * Single source of truth for API base URL.
 * NO /api suffix here - that's added at call site.
 * 
 * CONFIGURATION:
 * - EXPO_PUBLIC_API_BASE_URL MUST be set in .env for each environment
 * - Staging: https://mirror-lens-fixes.emergent.host
 * - Production: (separate always-on deployment URL)
 * 
 * NO HARDCODED FALLBACKS:
 * - Each environment must explicitly set its API URL
 * - This prevents accidentally calling the wrong backend
 */

// Environment check
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const IS_STAGING = APP_ENV === 'staging';
const IS_PRODUCTION = APP_ENV === 'production';

// Get the configured API base URL - NO HARDCODED FALLBACK
const raw = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();

// Validate and export
export const API_BASE_URL: string = (() => {
  // Use configured URL if present and non-empty
  if (raw && raw.length > 0) {
    // Ensure it starts with http/https (native requires absolute URLs)
    const url = raw.startsWith('http') ? raw : `https://${raw}`;
    const cleanUrl = url.replace(/\/+$/, '');
    console.log(`[API_BASE] Using configured URL (${APP_ENV}):`, cleanUrl);
    return cleanUrl;
  }
  
  // NO FALLBACK - each environment must set EXPO_PUBLIC_API_BASE_URL
  console.error('[API_BASE] ❌ EXPO_PUBLIC_API_BASE_URL is NOT SET!');
  console.error(`[API_BASE] Environment: ${APP_ENV}`);
  console.error('[API_BASE] Each deployment MUST set EXPO_PUBLIC_API_BASE_URL to its own backend.');
  
  // Return empty string - API calls will fail loudly
  // This is intentional - better to fail fast than silently hit wrong backend
  return '';
})();

// Flag to indicate if API URL is properly configured
export const IS_API_CONFIGURED = raw && raw.length > 0;
export const IS_USING_FALLBACK_URL = !IS_API_CONFIGURED;

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

// Export environment info for debugging
export const ENV_INFO = {
  env: APP_ENV,
  isStaging: IS_STAGING,
  isProduction: IS_PRODUCTION,
  apiConfigured: IS_API_CONFIGURED,
};
