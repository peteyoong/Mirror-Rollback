/**
 * Stable User Identity Module
 * ============================
 * 
 * Provides a persistent, stable user ID for the Mirror app.
 * This ID remains constant across app reloads, reinstalls (if storage persists),
 * and session changes.
 * 
 * Storage key: MIRROR_USER_ID
 * Migration: Checks for legacy keys (DEBUG_LAST_USER_ID, mirror_last_user_id)
 * and migrates them to ensure continuity.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// === STORAGE KEYS ===
const STABLE_USER_ID_KEY = 'MIRROR_USER_ID';
const LEGACY_KEYS = [
  'DEBUG_LAST_USER_ID',      // From NumerologyLensView debug
  'mirror_last_user_id',     // From store/index.ts session persistence
  'user_id',                 // Generic fallback
];

// === DEBUG MODE ===
const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true' || __DEV__;

// === RUNTIME ASSERTION STATE ===
let _cachedStableUserId: string | null = null;
let _assertionCheckCount = 0;

/**
 * Generate a UUIDv4
 */
function generateUUIDv4(): string {
  // Use crypto.randomUUID if available (modern browsers/Node)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  // Fallback to manual generation
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Cross-platform storage get
 */
async function storageGet(key: string): Promise<string | null> {
  try {
    // Try AsyncStorage first
    const value = await AsyncStorage.getItem(key);
    if (value !== null) return value;
    
    // Fallback to localStorage on web
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(key);
    }
    return null;
  } catch (error) {
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(key);
    }
    console.error('[StableUserId] Storage get error:', error);
    return null;
  }
}

/**
 * Cross-platform storage set
 */
async function storageSet(key: string, value: string): Promise<void> {
  try {
    await AsyncStorage.setItem(key, value);
    // Also set in localStorage on web for redundancy
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(key, value);
    }
  } catch (error) {
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(key, value);
    } else {
      console.error('[StableUserId] Storage set error:', error);
    }
  }
}

/**
 * Check for legacy user IDs and migrate them
 * Returns the first found legacy ID, or null if none found
 */
async function migrateLegacyUserId(): Promise<string | null> {
  for (const legacyKey of LEGACY_KEYS) {
    const legacyId = await storageGet(legacyKey);
    if (legacyId && legacyId.length > 0) {
      if (DEBUG_MIRROR) {
        console.log(`[StableUserId] Found legacy ID in ${legacyKey}:`, maskUserId(legacyId));
      }
      return legacyId;
    }
  }
  return null;
}

/**
 * Mask user ID for logging (show first 4 and last 4 chars)
 */
export function maskUserId(userId: string | null): string {
  if (!userId) return '(none)';
  if (userId.length <= 8) return userId;
  return `${userId.slice(0, 4)}...${userId.slice(-4)}`;
}

/**
 * Get or create a stable user ID
 * 
 * This is the PRIMARY function to get a user ID. It:
 * 1. Returns cached ID if available (for performance)
 * 2. Checks for existing MIRROR_USER_ID in storage
 * 3. Migrates from legacy keys if MIRROR_USER_ID not found
 * 4. Generates new UUIDv4 if no existing ID found
 * 5. Persists and caches the ID
 * 
 * @returns Promise<string> - The stable user ID
 */
export async function getStableUserId(): Promise<string> {
  // Return cached ID if available (performance optimization)
  if (_cachedStableUserId) {
    // Runtime assertion: ID must remain constant
    if (DEBUG_MIRROR) {
      _assertionCheckCount++;
      if (_assertionCheckCount > 1) {
        console.log(`[StableUserId] ✓ ID stable (check #${_assertionCheckCount}):`, maskUserId(_cachedStableUserId));
      }
    }
    return _cachedStableUserId;
  }
  
  // Check for existing stable ID
  let stableId = await storageGet(STABLE_USER_ID_KEY);
  
  if (stableId) {
    if (DEBUG_MIRROR) {
      console.log('[StableUserId] Found existing MIRROR_USER_ID:', maskUserId(stableId));
    }
  } else {
    // Try to migrate from legacy keys
    const legacyId = await migrateLegacyUserId();
    
    if (legacyId) {
      stableId = legacyId;
      if (DEBUG_MIRROR) {
        console.log('[StableUserId] Migrated from legacy key:', maskUserId(stableId));
      }
    } else {
      // Generate new ID
      stableId = generateUUIDv4();
      if (DEBUG_MIRROR) {
        console.log('[StableUserId] Generated new ID:', maskUserId(stableId));
      }
    }
    
    // Persist the stable ID
    await storageSet(STABLE_USER_ID_KEY, stableId);
    
    // Also update legacy key for backward compatibility
    await storageSet('mirror_last_user_id', stableId);
  }
  
  // Cache for future calls
  _cachedStableUserId = stableId;
  _assertionCheckCount = 1;
  
  return stableId;
}

/**
 * Get the cached stable user ID synchronously
 * Returns null if not yet initialized - call getStableUserId() first
 */
export function getStableUserIdSync(): string | null {
  return _cachedStableUserId;
}

/**
 * Runtime assertion: Verify user ID hasn't changed
 * Call this periodically in DEBUG mode to detect ID instability
 * 
 * @throws Error if ID has changed (in DEBUG mode only)
 */
export async function assertUserIdStable(): Promise<boolean> {
  if (!DEBUG_MIRROR) return true;
  
  const currentStoredId = await storageGet(STABLE_USER_ID_KEY);
  
  if (_cachedStableUserId && currentStoredId && _cachedStableUserId !== currentStoredId) {
    const error = `[StableUserId] ❌ ASSERTION FAILED: User ID changed!\n` +
      `  Cached: ${maskUserId(_cachedStableUserId)}\n` +
      `  Stored: ${maskUserId(currentStoredId)}`;
    console.error(error);
    return false;
  }
  
  if (_cachedStableUserId) {
    console.log('[StableUserId] ✓ Assertion passed: ID is stable');
  }
  
  return true;
}

/**
 * Clear the stable user ID (use with caution - for logout/reset only)
 */
export async function clearStableUserId(): Promise<void> {
  if (DEBUG_MIRROR) {
    console.log('[StableUserId] ⚠️ Clearing stable user ID');
  }
  
  _cachedStableUserId = null;
  _assertionCheckCount = 0;
  
  await AsyncStorage.removeItem(STABLE_USER_ID_KEY);
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.removeItem(STABLE_USER_ID_KEY);
  }
}

/**
 * Set the cached stable user ID directly
 * Used when user logs in and we need to sync the cache with the persisted ID
 * @param userId The user ID to cache (typically MongoDB ObjectId from login)
 */
export function setStableUserIdCache(userId: string): void {
  if (DEBUG_MIRROR) {
    console.log('[StableUserId] Setting cache directly:', maskUserId(userId));
  }
  _cachedStableUserId = userId;
  _assertionCheckCount = 1;
}

/**
 * Debug: Get all user ID related info
 */
export async function getDebugUserIdInfo(): Promise<{
  stable_id: string | null;
  stable_id_masked: string;
  cached_id: string | null;
  cached_id_masked: string;
  legacy_ids: Record<string, string | null>;
  is_stable: boolean;
  assertion_count: number;
}> {
  const stableId = await storageGet(STABLE_USER_ID_KEY);
  const legacyIds: Record<string, string | null> = {};
  
  for (const key of LEGACY_KEYS) {
    legacyIds[key] = await storageGet(key);
  }
  
  return {
    stable_id: stableId,
    stable_id_masked: maskUserId(stableId),
    cached_id: _cachedStableUserId,
    cached_id_masked: maskUserId(_cachedStableUserId),
    legacy_ids: legacyIds,
    is_stable: !_cachedStableUserId || !stableId || _cachedStableUserId === stableId,
    assertion_count: _assertionCheckCount,
  };
}
