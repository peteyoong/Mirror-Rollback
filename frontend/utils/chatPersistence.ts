/**
 * Chat Persistence Utilities
 * Pure functions for loading/saving chat messages - NO Zustand set() calls
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

const STORAGE_PREFIX = 'mirror_chat_v2:';

/**
 * Get storage key for a user's chat thread
 */
export function getChatKey(userId: string, threadKey: string): string {
  return `${STORAGE_PREFIX}${userId}:${threadKey}`;
}

/**
 * Load messages from storage - PURE function, no side effects
 */
export async function loadMessages(userId: string, threadKey: string): Promise<ChatMessage[]> {
  if (!userId) return [];
  
  const key = getChatKey(userId, threadKey);
  
  try {
    const stored = await AsyncStorage.getItem(key);
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
export async function saveMessages(userId: string, threadKey: string, messages: ChatMessage[]): Promise<void> {
  if (!userId) return;
  
  const key = getChatKey(userId, threadKey);
  
  try {
    await AsyncStorage.setItem(key, JSON.stringify(messages));
    console.log(`[ChatPersistence] Saved ${messages.length} messages to ${key}`);
  } catch (e) {
    console.error('[ChatPersistence] Save error:', e);
  }
}

/**
 * Clear messages from storage
 */
export async function clearMessages(userId: string, threadKey: string): Promise<void> {
  if (!userId) return;
  
  const key = getChatKey(userId, threadKey);
  
  try {
    await AsyncStorage.removeItem(key);
    console.log(`[ChatPersistence] Cleared messages from ${key}`);
  } catch (e) {
    console.error('[ChatPersistence] Clear error:', e);
  }
}
