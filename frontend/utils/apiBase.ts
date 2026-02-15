/**
 * Single source of truth for API base URL.
 * NO /api suffix here - that's added at call site.
 */
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  'https://mirror-fix.preview.emergentagent.com';
