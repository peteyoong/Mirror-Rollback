/**
 * Session Validator
 * =================
 * 
 * Validates that the cached user ID actually exists in the current database.
 * If the user doesn't exist (404/500), clears the session and redirects to Welcome.
 * 
 * This handles the case where:
 * - User has a cached session from a different environment
 * - User was deleted from the database
 * - Database was reset/switched
 */

import { API_BASE_URL } from './apiBase';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// Storage key for user ID
const STABLE_USER_ID_KEY = 'MIRROR_USER_ID';

// Timeout for validation request (5 seconds)
const VALIDATION_TIMEOUT_MS = 5000;

// Retry configuration
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

export interface SessionValidationResult {
  isValid: boolean;
  userId: string | null;
  error: string | null;
  statusCode: number | null;
}

/**
 * Get the stored user ID from storage
 */
async function getStoredUserId(): Promise<string | null> {
  try {
    // Try localStorage first on web
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(STABLE_USER_ID_KEY);
    }
    
    // Fall back to AsyncStorage
    return await AsyncStorage.getItem(STABLE_USER_ID_KEY);
  } catch (error) {
    console.error('[SessionValidator] Error reading stored userId:', error);
    return null;
  }
}

/**
 * Clear the stored session (userId and related data)
 */
export async function clearStoredSession(): Promise<void> {
  console.log('[AUTH] Clearing stored session...');
  
  try {
    // Clear AsyncStorage
    await AsyncStorage.multiRemove([
      STABLE_USER_ID_KEY,
      'mirror_last_user_id',
      'mirror_user_email',
      'DEEP_ENNEAGRAM_SESSION_ID',
    ]);
    
    // Clear localStorage on web
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(STABLE_USER_ID_KEY);
      window.localStorage.removeItem('mirror_last_user_id');
      window.localStorage.removeItem('mirror_user_email');
      window.localStorage.removeItem('DEEP_ENNEAGRAM_SESSION_ID');
    }
    
    console.log('[AUTH] Session cleared successfully');
  } catch (error) {
    console.error('[AUTH] Error clearing session:', error);
  }
}

/**
 * Validate that the stored user ID exists in the database
 * Returns immediately if no stored userId
 */
export async function validateStoredSession(): Promise<SessionValidationResult> {
  const userId = await getStoredUserId();
  
  // No stored userId - session is "valid" (user will see Welcome screen)
  if (!userId) {
    console.log('[AUTH] No stored userId found');
    return { isValid: true, userId: null, error: null, statusCode: null };
  }
  
  console.log(`[AUTH] Validating stored userId: ${userId.slice(0, 8)}...`);
  
  let lastError: string | null = null;
  let lastStatusCode: number | null = null;
  
  // Try validation with retries
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), VALIDATION_TIMEOUT_MS);
      
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      lastStatusCode = response.status;
      
      if (response.ok) {
        console.log(`[AUTH] ✓ Session valid (user exists)`);
        return { isValid: true, userId, error: null, statusCode: response.status };
      }
      
      // Handle specific error cases
      if (response.status === 401 || response.status === 403) {
        // Unauthorized - clear session
        console.log(`[AUTH] restore failed -> ${response.status} unauthorized`);
        await clearStoredSession();
        return { isValid: false, userId: null, error: 'Session expired', statusCode: response.status };
      }
      
      if (response.status === 404) {
        // User not found - clear session
        console.log(`[AUTH] restore failed -> ${response.status} user not found`);
        await clearStoredSession();
        return { isValid: false, userId: null, error: 'User not found', statusCode: response.status };
      }
      
      if (response.status === 500) {
        // Server error - likely user doesn't exist (bad ID format or DB mismatch)
        console.log(`[AUTH] restore failed -> ${response.status} server error (treating as user not found)`);
        await clearStoredSession();
        return { isValid: false, userId: null, error: 'Session invalid', statusCode: response.status };
      }
      
      // Other error - retry
      lastError = `HTTP ${response.status}`;
      console.log(`[AUTH] Validation attempt ${attempt} failed: ${lastError}`);
      
    } catch (error: any) {
      if (error.name === 'AbortError') {
        lastError = 'Request timed out';
        console.log(`[AUTH] Validation attempt ${attempt} timed out`);
      } else {
        lastError = error.message || 'Network error';
        console.log(`[AUTH] Validation attempt ${attempt} error:`, lastError);
      }
    }
    
    // Wait before retry (except on last attempt)
    if (attempt < MAX_RETRIES) {
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
    }
  }
  
  // All retries failed - but don't clear session (might be network issue)
  // Return invalid but keep userId so user can retry
  console.log(`[AUTH] restore failed -> network error after ${MAX_RETRIES} attempts`);
  return { isValid: false, userId, error: lastError, statusCode: lastStatusCode };
}
