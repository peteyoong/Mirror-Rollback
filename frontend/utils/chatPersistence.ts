/**
 * Chat Persistence Utilities - UNIFIED
 * Pure functions for loading/saving chat messages - NO Zustand set() calls
 * 
 * SINGLE SOURCE OF TRUTH for chat storage keys
 */

import { Platform } from 'react-native';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

// Single canonical storage prefix
const STORAGE_PREFIX = 'mirror_chat_messages';

// The ONE canonical thread key for Mirror/Reflection chat
export const DEFAULT_THREAD_KEY = 'reflection:default';

/**
 * Get storage key for a user's chat thread
 * Format: mirror_chat_messages:{userId}:{threadKey}
 */
export function getChatStorageKey(userId: string, threadKey: string = DEFAULT_THREAD_KEY): string {
  return `${STORAGE_PREFIX}:${userId}:${threadKey}`;
}

/**
 * Cross-platform storage get
 */
async function storageGet(key: string): Promise<string | null> {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
    try {
      return window.localStorage.getItem(key);
    } catch (e) {
      console.error('[ChatPersistence] localStorage.getItem error:', e);
    }
  }
  
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    return await AsyncStorage.getItem(key);
  } catch (e) {
    console.error('[ChatPersistence] AsyncStorage.getItem error:', e);
    return null;
  }
}

/**
 * Cross-platform storage set
 */
async function storageSet(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
    try {
      window.localStorage.setItem(key, value);
      return;
    } catch (e) {
      console.error('[ChatPersistence] localStorage.setItem error:', e);
    }
  }
  
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    await AsyncStorage.setItem(key, value);
  } catch (e) {
    console.error('[ChatPersistence] AsyncStorage.setItem error:', e);
  }
}

/**
 * Load messages from storage - PURE function, no side effects
 */
export async function loadMessages(userId: string, threadKey: string = DEFAULT_THREAD_KEY): Promise<ChatMessage[]> {
  if (!userId) return [];
  
  const key = getChatStorageKey(userId, threadKey);
  
  try {
    const stored = await storageGet(key);
    if (stored) {
      const messages = JSON.parse(stored) as ChatMessage[];
      console.log(`[ChatPersistence] Loaded ${messages.length} messages from ${key}`);
      return messages;
    }
  } catch (e) {
    console.error('[ChatPersistence] Load error:', e);
  }
  
  return [];
}

/**
 * Save messages to storage - PURE function, no side effects
 */
export async function saveMessages(userId: string, threadKey: string = DEFAULT_THREAD_KEY, messages: ChatMessage[]): Promise<void> {
  if (!userId) return;
  if (!messages?.length) return;
  
  const key = getChatStorageKey(userId, threadKey);
  
  try {
    await storageSet(key, JSON.stringify(messages));
    console.log(`[ChatPersistence] Saved ${messages.length} messages to ${key}`);
  } catch (e) {
    console.error('[ChatPersistence] Save error:', e);
  }
}

/**
 * Clear messages from storage
 */
export async function clearMessages(userId: string, threadKey: string = DEFAULT_THREAD_KEY): Promise<void> {
  if (!userId) return;
  
  const key = getChatStorageKey(userId, threadKey);
  
  try {
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(key);
    } else {
      const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
      await AsyncStorage.removeItem(key);
    }
    console.log(`[ChatPersistence] Cleared messages from ${key}`);
  } catch (e) {
    console.error('[ChatPersistence] Clear error:', e);
  }
}
