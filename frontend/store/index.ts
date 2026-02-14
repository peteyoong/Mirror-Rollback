/**
 * TEMPORARY STORE STUB - NO ZUSTAND
 * 
 * Purpose: Prove whether Zustand is the crash source.
 * - No create()
 * - No persist()
 * - No AsyncStorage in effects
 * - No subscribe
 * - No set()
 * 
 * If crash STOPS with this stub → Zustand is the root cause.
 * If crash CONTINUES → Navigation/router is the cause.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// ============================================================================
// TYPES (kept for compatibility)
// ============================================================================

export interface User {
  id: string;
  email?: string;
  name?: string;
  birth_date?: string;
  birth_time?: string;
  birth_location?: string;
}

export interface Chart {
  id?: string;
  user_id: string;
  type: string;
  data: any;
  calculated_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

// ============================================================================
// STORAGE HELPER (kept for other code that imports it)
// ============================================================================

export const storage = {
  async getItem(key: string): Promise<string | null> {
    try {
      const value = await AsyncStorage.getItem(key);
      if (value !== null) return value;
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage.getItem(key);
      }
      return null;
    } catch (error) {
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage.getItem(key);
      }
      return null;
    }
  },
  
  async setItem(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(key, value);
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);
      }
    } catch (error) {
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);
      }
    }
  },
  
  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.error('Storage removeItem error:', error);
    }
  },
  
  async multiRemove(keys: string[]): Promise<void> {
    try {
      await AsyncStorage.multiRemove(keys);
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        keys.forEach(key => window.localStorage.removeItem(key));
      }
    } catch (error) {
      console.error('Storage multiRemove error:', error);
    }
  },
};

// ============================================================================
// CHAT SESSION KEYS (kept for compatibility)
// ============================================================================

export const CHAT_SESSION_KEYS = {
  mirror: 'mirror_session_id',
  astrology: 'astrology_session_id',
  human_design: 'human_design_session_id',
} as const;

// ============================================================================
// STATIC STORE SHAPE (NO ZUSTAND)
// ============================================================================

interface StaticStoreShape {
  // State
  user: User | null;
  chart: Chart | null;
  dailyReflection: any;
  journalEntries: any[];
  hasCompletedOnboarding: boolean;
  chatMessages: Record<string, ChatMessage[]>;
  questionnaireAnswers: string[];
  questionnaireComplete: boolean;
  isRestoringSession: boolean;
  hasTriedSessionRestore: boolean;
  sessionRestoreError: string | null;
  
  // Actions (no-ops for stub)
  setUser: (user: User) => void;
  setChart: (chart: Chart) => void;
  setDailyReflection: (r: any) => void;
  setJournalEntries: (e: any[]) => void;
  addJournalEntry: (e: any) => void;
  getChatMessages: (threadKey: string) => ChatMessage[];
  addChatMessage: (threadKey: string, msg: ChatMessage) => Promise<void>;
  setChatMessages: (threadKey: string, msgs: ChatMessage[]) => Promise<void>;
  loadChatMessages: (threadKey: string) => Promise<ChatMessage[]>;
  clearChatMessages: (threadKey: string) => Promise<void>;
  completeOnboarding: () => Promise<void>;
  setQuestionnaireAnswer: (index: number, answer: string) => Promise<void>;
  completeQuestionnaire: () => Promise<void>;
  clearUser: () => Promise<void>;
  loadPersistedData: () => Promise<void>;
  restoreSession: () => Promise<boolean>;
  resetLocalSession: (reload?: boolean) => Promise<void>;
  shouldShowLoadingGate: () => boolean;
}

// STATIC DATA - never changes, no set() calls
const STATIC_STORE: StaticStoreShape = {
  // Pre-populated user for testing (bypasses login)
  user: {
    id: 'test-user-stub',
    email: 'test@stub.local',
    name: 'Test User (Stub)',
  },
  chart: null,
  dailyReflection: null,
  journalEntries: [],
  hasCompletedOnboarding: true,
  chatMessages: {},
  questionnaireAnswers: [],
  questionnaireComplete: true,
  isRestoringSession: false,
  hasTriedSessionRestore: true,  // Already "restored"
  sessionRestoreError: null,
  
  // NO-OP actions
  setUser: () => { console.log('[STUB] setUser called (no-op)'); },
  setChart: () => { console.log('[STUB] setChart called (no-op)'); },
  setDailyReflection: () => { console.log('[STUB] setDailyReflection called (no-op)'); },
  setJournalEntries: () => { console.log('[STUB] setJournalEntries called (no-op)'); },
  addJournalEntry: () => { console.log('[STUB] addJournalEntry called (no-op)'); },
  getChatMessages: () => [],
  addChatMessage: async () => { console.log('[STUB] addChatMessage called (no-op)'); },
  setChatMessages: async () => { console.log('[STUB] setChatMessages called (no-op)'); },
  loadChatMessages: async () => { console.log('[STUB] loadChatMessages called (no-op)'); return []; },
  clearChatMessages: async () => { console.log('[STUB] clearChatMessages called (no-op)'); },
  completeOnboarding: async () => { console.log('[STUB] completeOnboarding called (no-op)'); },
  setQuestionnaireAnswer: async () => { console.log('[STUB] setQuestionnaireAnswer called (no-op)'); },
  completeQuestionnaire: async () => { console.log('[STUB] completeQuestionnaire called (no-op)'); },
  clearUser: async () => { console.log('[STUB] clearUser called (no-op)'); },
  loadPersistedData: async () => { console.log('[STUB] loadPersistedData called (no-op)'); },
  restoreSession: async () => { console.log('[STUB] restoreSession called (no-op)'); return true; },
  resetLocalSession: async () => { console.log('[STUB] resetLocalSession called (no-op)'); },
  shouldShowLoadingGate: () => false,
};

// ============================================================================
// FAKE useAppStore HOOK (NO ZUSTAND)
// ============================================================================

/**
 * STUB: Returns static data, no subscriptions, no re-renders.
 * This mimics the Zustand useStore API but without any reactivity.
 */
export function useAppStore<T>(selector?: (state: StaticStoreShape) => T): T | StaticStoreShape {
  if (selector) {
    return selector(STATIC_STORE);
  }
  return STATIC_STORE;
}

// For code that does useAppStore.getState()
useAppStore.getState = () => STATIC_STORE;

// ============================================================================
// HELPER FUNCTIONS (kept for compatibility)
// ============================================================================

export function getChatStorageKey(userId: string, threadKey: string): string {
  return `mirror_chat_messages:${userId}:${threadKey}`;
}

console.log('========================================');
console.log('[STORE] STUB LOADED - NO ZUSTAND');
console.log('[STORE] User:', STATIC_STORE.user?.name);
console.log('[STORE] hasTriedSessionRestore:', STATIC_STORE.hasTriedSessionRestore);
console.log('========================================');
