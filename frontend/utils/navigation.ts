/**
 * Navigation Utilities
 * ====================
 * 
 * Provides safe navigation helpers that handle edge cases like:
 * - Direct URL entry (no history stack)
 * - Deep links
 * - Browser refresh
 * - Navigation stack corruption
 */

import { Router } from 'expo-router';

/**
 * Default fallback destination for Enneagram-related screens.
 * Used when router.back() has nowhere to go.
 */
export const ENNEAGRAM_FALLBACK_ROUTE = '/(tabs)/lenses';

/**
 * Default fallback destination for general app navigation.
 */
export const DEFAULT_FALLBACK_ROUTE = '/(tabs)';

/**
 * Safely navigate back with a deterministic fallback.
 * 
 * If the navigation stack is empty (user landed directly via deep link,
 * browser refresh, or direct URL entry), this function will navigate
 * to the specified fallback route instead of doing nothing.
 * 
 * @param router - The expo-router instance
 * @param fallbackRoute - Route to navigate to if back() would fail (default: lenses tab)
 */
export function safeGoBack(
  router: Router,
  fallbackRoute: string = ENNEAGRAM_FALLBACK_ROUTE
): void {
  // Check if we can go back
  // In expo-router, canGoBack() returns true if there's history
  if (router.canGoBack()) {
    router.back();
  } else {
    // No history - use deterministic fallback
    router.replace(fallbackRoute as any);
  }
}

/**
 * Navigate to lenses tab (standard close behavior for lens screens).
 * Uses replace to prevent back-button from returning to the closed screen.
 * 
 * @param router - The expo-router instance
 */
export function navigateToLenses(router: Router): void {
  router.replace('/(tabs)/lenses' as any);
}

/**
 * Navigate to home tab.
 * Uses replace to prevent back-button from returning to the closed screen.
 * 
 * @param router - The expo-router instance
 */
export function navigateToHome(router: Router): void {
  router.replace('/(tabs)' as any);
}
