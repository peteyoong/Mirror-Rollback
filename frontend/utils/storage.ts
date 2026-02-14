/**
 * Cross-platform storage adapter
 * 
 * On Web: Uses localStorage (more reliable in preview mode)
 * On Native: Uses AsyncStorage
 */

import { Platform } from 'react-native';

// Track which backend is being used
let activeBackend: 'localStorage' | 'AsyncStorage' | 'unknown' = 'unknown';

export function getStorageBackend(): string {
  return activeBackend;
}

export async function storageGet(key: string): Promise<string | null> {
  // Web: prefer localStorage
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
    activeBackend = 'localStorage';
    try {
      return window.localStorage.getItem(key);
    } catch (e) {
      console.error('[storage] localStorage.getItem error:', e);
    }
  }
  
  // Native or fallback: use AsyncStorage
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    activeBackend = 'AsyncStorage';
    return await AsyncStorage.getItem(key);
  } catch (e) {
    console.error('[storage] AsyncStorage.getItem error:', e);
    return null;
  }
}

export async function storageSet(key: string, value: string): Promise<void> {
  // Web: prefer localStorage
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
    activeBackend = 'localStorage';
    try {
      window.localStorage.setItem(key, value);
      return;
    } catch (e) {
      console.error('[storage] localStorage.setItem error:', e);
    }
  }
  
  // Native or fallback: use AsyncStorage
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    activeBackend = 'AsyncStorage';
    await AsyncStorage.setItem(key, value);
  } catch (e) {
    console.error('[storage] AsyncStorage.setItem error:', e);
  }
}

export async function storageRemove(key: string): Promise<void> {
  // Web: prefer localStorage
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
    try {
      window.localStorage.removeItem(key);
      return;
    } catch (e) {
      console.error('[storage] localStorage.removeItem error:', e);
    }
  }
  
  // Native or fallback: use AsyncStorage
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    await AsyncStorage.removeItem(key);
  } catch (e) {
    console.error('[storage] AsyncStorage.removeItem error:', e);
  }
}
