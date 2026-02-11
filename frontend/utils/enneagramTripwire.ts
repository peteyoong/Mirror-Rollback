/**
 * Enneagram Label Tripwire - Runtime Guard Against Forbidden Strings
 * ===================================================================
 * 
 * This module provides runtime detection of forbidden "balanced wings" patterns
 * that should never appear in user-facing UI.
 * 
 * FORBIDDEN PATTERNS:
 * - "wbalanced"
 * - "balanced wings"
 * - "balanced wing"
 * - "7wbalanced" (or any digit + wbalanced)
 * - "Type balanced"
 * - "flavor of Xwbalanced"
 */

// Build ID - generated at build time
// This constant helps verify the deployed bundle version
export const APP_BUILD_ID = '2026-02-11-v3-tripwire';
export const APP_BUILD_TIMESTAMP = new Date().toISOString();

// Check if debug mode is enabled
const isDebugMode = (): boolean => {
  if (typeof window !== 'undefined') {
    // Check URL param
    const urlParams = new URLSearchParams(window.location?.search || '');
    if (urlParams.get('debug') === '1') return true;
  }
  // Check env var
  try {
    return process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';
  } catch {
    return false;
  }
};

// Forbidden patterns that should NEVER appear in Enneagram UI
const FORBIDDEN_PATTERNS = [
  /wbalanced/i,
  /balanced\s*wings?/i,
  /\d+wbalanced/i,
  /Type\s+balanced/i,
  /flavor\s+of\s+\d+wbalanced/i,
];

export interface LeakDetection {
  detected: boolean;
  pattern: string | null;
  context: string;
  value: string;
  timestamp: string;
}

// Store detected leaks for UI display
let detectedLeaks: LeakDetection[] = [];

/**
 * Check if a string contains any forbidden patterns
 */
export function containsForbiddenPattern(str: string): { found: boolean; pattern: string | null } {
  if (!str || typeof str !== 'string') {
    return { found: false, pattern: null };
  }
  
  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(str)) {
      return { found: true, pattern: pattern.toString() };
    }
  }
  
  return { found: false, pattern: null };
}

/**
 * Assert that a string contains no forbidden patterns.
 * Logs error and optionally shows UI warning in debug mode.
 * 
 * @param str - The string to check
 * @param context - Where this string came from (e.g., "Deep Dive header", "Summary subtitle")
 * @returns The original string (for chaining)
 */
export function assertNoBalancedWingLeak(str: string, context: string): string {
  if (!str || typeof str !== 'string') return str;
  
  const check = containsForbiddenPattern(str);
  
  if (check.found) {
    const leak: LeakDetection = {
      detected: true,
      pattern: check.pattern,
      context,
      value: str.substring(0, 100), // Truncate for safety
      timestamp: new Date().toISOString(),
    };
    
    // Store the leak
    detectedLeaks.push(leak);
    
    // Always log to console
    console.error(
      `[ENNEAGRAM_LEAK] ⚠️ Forbidden pattern detected!\n` +
      `  Context: ${context}\n` +
      `  Pattern: ${check.pattern}\n` +
      `  Value: "${str.substring(0, 100)}"\n` +
      `  Build: ${APP_BUILD_ID}`
    );
    
    // Log stack trace for debugging
    console.trace('[ENNEAGRAM_LEAK] Stack trace:');
  }
  
  return str;
}

/**
 * Sanitize a string by removing/replacing forbidden patterns.
 * Use this as a last-resort fallback when rendering untrusted content.
 */
export function sanitizeEnneagramString(str: string): string {
  if (!str || typeof str !== 'string') return str;
  
  let result = str;
  
  // Replace specific patterns with safe alternatives
  result = result.replace(/(\d+)wbalanced/gi, 'Type $1');
  result = result.replace(/balanced\s*wings?\s*\([^)]+\)/gi, 'both adjacent wings');
  result = result.replace(/balanced\s*wings?/gi, 'both adjacent wings');
  result = result.replace(/Your\s+balanced\s+wing/gi, 'Your wing access');
  result = result.replace(/flavor\s+of\s+(\d+)wbalanced/gi, 'expression as Type $1');
  result = result.replace(/Type\s+balanced/gi, 'Type');
  
  return result;
}

/**
 * Get all detected leaks (for UI display in debug mode)
 */
export function getDetectedLeaks(): LeakDetection[] {
  return [...detectedLeaks];
}

/**
 * Clear detected leaks
 */
export function clearDetectedLeaks(): void {
  detectedLeaks = [];
}

/**
 * Check if any leaks have been detected
 */
export function hasDetectedLeaks(): boolean {
  return detectedLeaks.length > 0;
}

/**
 * Get debug info for display
 */
export function getDebugInfo(): {
  buildId: string;
  buildTimestamp: string;
  isDebugMode: boolean;
  leakCount: number;
  leaks: LeakDetection[];
} {
  return {
    buildId: APP_BUILD_ID,
    buildTimestamp: APP_BUILD_TIMESTAMP,
    isDebugMode: isDebugMode(),
    leakCount: detectedLeaks.length,
    leaks: [...detectedLeaks],
  };
}
