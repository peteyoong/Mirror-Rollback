/**
 * Debug Utilities for Enneagram Screens
 * =====================================
 * 
 * Centralized debug visibility logic that ensures debug UI:
 * - Is NEVER visible by default, even when DEBUG_MIRROR=true (staging)
 * - Only appears when explicitly enabled via:
 *   - Web: URL param ?debug=1
 *   - Mobile: Hidden gesture (7 taps or 2-second long press)
 * - Never blocks navigation or interaction
 */

import { Platform } from 'react-native';
import * as Clipboard from 'expo-clipboard';

// Environment flag - must be 'true' to enable debug capability
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
  return new URLSearchParams(window.location?.search || '').get('debug') === '1';
};

/**
 * Determine if debug UI should be shown
 * 
 * Formula: showDebug = DEBUG_MIRROR_ENV && (urlDebugParam || gestureActivated)
 * 
 * @param gestureActivated - Whether the user has activated debug via gesture (mobile)
 * @returns boolean - Whether to show debug UI
 */
export const shouldShowDebugUI = (gestureActivated: boolean = false): boolean => {
  // Debug capability must be enabled in environment
  if (!DEBUG_MIRROR_ENV) return false;
  
  // Check URL param (web only)
  if (getUrlDebugParam()) return true;
  
  // Check gesture activation (mobile)
  return gestureActivated;
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
