/**
 * Debug Utilities for Enneagram Screens
 * =====================================
 * 
 * Centralized debug visibility logic that ensures debug UI:
 * - Is NEVER visible by default, even when DEBUG_MIRROR=true (staging)
 * - Only appears when BOTH conditions are met:
 *   1. EXPO_PUBLIC_DEBUG_MIRROR === 'true' (environment flag)
 *   2. URL contains ?debug=1 (explicit activation)
 * - Never blocks navigation or interaction
 * 
 * CRITICAL: Debug UI must NEVER show in production or by default.
 */

import { Platform } from 'react-native';
import * as Clipboard from 'expo-clipboard';

// Environment flag - must be EXACTLY 'true' (string compare) to enable debug capability
// Default is FALSE if undefined, empty, or any other value
export const DEBUG_MIRROR_ENV = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// Required tap count for hidden gesture activation
export const DEBUG_TAP_THRESHOLD = 7;

// Long press duration in milliseconds
export const DEBUG_LONG_PRESS_DURATION = 2000;

/**
 * Check if debug is enabled via URL param (?debug=1)
 * Only works on web platform
 */
export const getUrlDebugParam = (): boolean => {
  if (Platform.OS !== 'web') return false;
  if (typeof window === 'undefined') return false;
  try {
    return new URLSearchParams(window.location?.search || '').get('debug') === '1';
  } catch {
    return false;
  }
};

/**
 * Determine if debug UI should be shown
 * 
 * CRITICAL: Requires BOTH conditions:
 * 1. DEBUG_MIRROR_ENV === true (from environment)
 * 2. AND (urlDebugParam || gestureActivated)
 * 
 * If DEBUG_MIRROR_ENV is false (production or default), debug UI NEVER shows.
 * 
 * @param gestureActivated - Whether the user has activated debug via gesture (mobile)
 * @returns boolean - Whether to show debug UI
 */
export const shouldShowDebugUI = (gestureActivated: boolean = false): boolean => {
  // CRITICAL: Debug capability must be enabled in environment FIRST
  // This is the primary gate - if false, nothing else matters
  if (!DEBUG_MIRROR_ENV) {
    return false;
  }
  
  // Secondary gate: explicit activation required
  // Either URL param ?debug=1 (web) or gesture activation (mobile)
  if (getUrlDebugParam()) return true;
  if (gestureActivated) return true;
  
  // Default: NO debug UI even if DEBUG_MIRROR_ENV is true
  return false;
};

/**
 * Copy text to clipboard (works on both web and mobile)
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await Clipboard.setStringAsync(text);
    return true;
  } catch (error) {
    console.error('[Debug] Failed to copy to clipboard:', error);
    return false;
  }
};

/**
 * Format debug data as a string for copying
 */
export const formatDebugData = (data: Record<string, any>): string => {
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
};

// Export API config for diagnostics
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || '';
export const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
export const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'dev';
export const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || new Date().toISOString();
