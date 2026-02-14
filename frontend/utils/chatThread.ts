/**
 * Chat Thread Utilities - SINGLE SOURCE OF TRUTH
 * 
 * All chat components MUST use these keys for consistency.
 */

// The ONE canonical thread key for Mirror/Reflection chat
export const DEFAULT_THREAD_KEY = 'reflection:default';

// Storage key prefix
const STORAGE_PREFIX = 'mirror_chat_messages';

/**
 * Get the storage key for a chat thread
 * @param userId - User ID
 * @param threadKey - Thread key (defaults to DEFAULT_THREAD_KEY)
 */
export function getChatStorageKey(userId: string, threadKey: string = DEFAULT_THREAD_KEY): string {
  return `${STORAGE_PREFIX}:${userId}:${threadKey}`;
}

/**
 * Available thread keys (for reference)
 */
export const THREAD_KEYS = {
  REFLECTION: 'reflection:default',  // Main Mirror/Reflection chat
  JOURNAL: 'journal:default',        // Journal chat (if separate)
  // Lens-specific chats use lens name as key
} as const;
