/**
 * ZUSTAND STORE - ISOLATION VERSION
 * 
 * - NO persist middleware
 * - Universal set() counter with kill switch
 * - All async code removed from import time
 */

import { create } from 'zustand';
import { Platform } from 'react-native';

// ============================================================================
// UNIVERSAL SET() COUNTER WITH KILL SWITCH
// ============================================================================
let __SET_COUNT = 0;
let __SET_KILL_SWITCH = false;
let __SET_START_TIME = Date.now();
let __LAST_ACTION = '';

const safeSet = (
  set: (partial: any) => void,
  actionName: string,
  partial: any
) => {
  __SET_COUNT++;
  __LAST_ACTION = actionName;
  const elapsed = Date.now() - __SET_START_TIME;
  
  console.log(`[ZUSTAND set] #${__SET_COUNT} ${actionName} (${elapsed}ms)`);
  
  // Kill switch: if >30 sets within 1000ms, we have a loop
  if (__SET_COUNT > 30 && elapsed < 1000) {
    if (!__SET_KILL_SWITCH) {
      const errorMsg = `[ZUSTAND] LOOP DETECTED! ${__SET_COUNT} sets in ${elapsed}ms. Last action: ${actionName}`;
      console.error(errorMsg);
      __SET_KILL_SWITCH = true;
      // Throw to break the loop and show in console
      throw new Error(errorMsg);
    }
    return; // Don't execute the set
  }
  
  set(partial);
};

// Reset counter periodically (every 5 seconds)
if (typeof window !== 'undefined') {
  setInterval(() => {
    if (__SET_COUNT > 0) {
      console.log(`[ZUSTAND] Resetting counter. Last period: ${__SET_COUNT} sets. Last action: ${__LAST_ACTION}`);
    }
    __SET_COUNT = 0;
    __SET_START_TIME = Date.now();
    __SET_KILL_SWITCH = false;
  }, 5000);
}

// ============================================================================
// TYPES
// ============================================================================
interface User {
  id: string;
  email?: string;
  name?: string;
  birth_date: string;
  birth_time?: string | null;          // HH:MM format (24-hour)
  birth_time_known?: boolean | null;   // True if user knows their birth time
  birth_location: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
  };
  timezone?: string;
  has_chart?: boolean;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface JournalEntry {
  id: string;
  content: string;
  themes: string[];
  source?: string | null;
  source_label?: string | null;
  created_at: string;
  // Legacy fields for backward compatibility
  date?: string;
  title?: string;
  mood?: string;
  tags?: string[];
  // Transit signature from Phase 6
  transit_signature?: {
    timestamp_utc: string;
    source: string;
    events: string[];
    top_houses: number[] | null;
    build_id: string;
    error?: string | null;
  } | null;
}

interface AppState {
  // Core data
  user: User | null;
  chart: any | null;
  hasCompletedOnboarding: boolean;
  journalEntries: JournalEntry[];
  
  // Chat state (in-memory only, no persist)
  chatMessages: Record<string, ChatMessage[]>;
  
  // Session state
  isRestoringSession: boolean;
  hasTriedSessionRestore: boolean;
  sessionRestoreError: string | null;
  
  // Actions
  setUser: (user: User) => void;
  setChart: (chart: any) => void;
  clearUser: () => void;
  setJournalEntries: (entries: JournalEntry[]) => void;
  addJournalEntry: (entry: JournalEntry) => void;
  
  // Chat actions (in-memory)
  setChatMessages: (storageKey: string, messages: ChatMessage[]) => void;
  addChatMessage: (storageKey: string, message: ChatMessage) => void;
  clearChatMessages: (storageKey: string) => void;
  loadChatMessages: (storageKey: string) => Promise<void>;
  
  // Session restore - NO-OP for isolation
  restoreSession: () => Promise<boolean>;
  
  // Dev reset - clears ALL local data
  resetLocalSession: (reload?: boolean) => Promise<void>;
}

// ============================================================================
// STORE - PLAIN CREATE, NO PERSIST
// ============================================================================
export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  user: null,
  chart: null,
  hasCompletedOnboarding: false,
  journalEntries: [], // Default empty array to prevent crashes
  chatMessages: {}, // In-memory chat state
  isRestoringSession: false,
  hasTriedSessionRestore: false,
  sessionRestoreError: null,
  
  // Actions with safeSet
  setUser: (user) => {
    safeSet(set, 'setUser', { user });
  },
  
  setChart: (chart) => {
    safeSet(set, 'setChart', { chart });
  },
  
  clearUser: () => {
    safeSet(set, 'clearUser', { user: null, chart: null, hasCompletedOnboarding: false, journalEntries: [], chatMessages: {} });
  },
  
  setJournalEntries: (entries) => {
    safeSet(set, 'setJournalEntries', { journalEntries: entries });
  },
  
  addJournalEntry: (entry) => {
    const current = get().journalEntries ?? [];
    safeSet(set, 'addJournalEntry', { journalEntries: [entry, ...current] });
  },
  
  // Chat actions (in-memory only - no persist)
  setChatMessages: (storageKey, messages) => {
    const current = get().chatMessages ?? {};
    safeSet(set, 'setChatMessages', { 
      chatMessages: { ...current, [storageKey]: messages } 
    });
  },
  
  addChatMessage: (storageKey, message) => {
    const current = get().chatMessages ?? {};
    const prev = current[storageKey] ?? [];
    safeSet(set, 'addChatMessage', { 
      chatMessages: { ...current, [storageKey]: [...prev, message] } 
    });
  },
  
  clearChatMessages: (storageKey) => {
    const current = get().chatMessages ?? {};
    const updated = { ...current };
    delete updated[storageKey];
    safeSet(set, 'clearChatMessages', { chatMessages: updated });
  },
  
  // NO-OP for now - chat is in-memory only
  loadChatMessages: async (storageKey) => {
    console.log(`[loadChatMessages] NO-OP - chat is in-memory only (key: ${storageKey})`);
  },
  
  // Session restore - NO-OP
  restoreSession: async () => {
    console.log('[restoreSession] NO-OP - isolation mode');
    safeSet(set, 'restoreSession-noop', { hasTriedSessionRestore: true, isRestoringSession: false });
    return false;
  },
  
  // Dev reset - clears ALL local data (for staging dev mode)
  resetLocalSession: async (reload = false) => {
    console.log('[resetLocalSession] Clearing ALL local data...');
    try {
      // Clear AsyncStorage completely
      const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
      await AsyncStorage.clear();
      console.log('[resetLocalSession] AsyncStorage cleared');
      
      // Clear web localStorage if on web
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.clear();
        console.log('[resetLocalSession] localStorage cleared');
      }
      
      // Reset store state
      safeSet(set, 'resetLocalSession', {
        user: null,
        chart: null,
        hasCompletedOnboarding: false,
        journalEntries: [],
        chatMessages: {},
        isRestoringSession: false,
        hasTriedSessionRestore: false,
        sessionRestoreError: null,
      });
      
      console.log('[resetLocalSession] Store state reset');
      
      // Reload if requested
      if (reload && typeof window !== 'undefined') {
        window.location.href = '/';
      }
    } catch (err) {
      console.error('[resetLocalSession] Error:', err);
    }
  },
}));

// Log store creation
console.log('[ZUSTAND] Store created - isolation version');

// ============================================================================
// EXPORTS for other components
// ============================================================================
export type { ChatMessage };

// Chat session storage keys
export const CHAT_SESSION_KEYS = {
  mirror: 'chat:mirror:home',
  astrology: 'chat:mirror:astrology',
  human_design: 'chat:mirror:human_design',
  numerology: 'chat:mirror:numerology',
  enneagram: 'chat:mirror:enneagram',
};

// Simple storage abstraction (in-memory for isolation, can be replaced with AsyncStorage later)
export const storage = {
  getItem: async (key: string): Promise<string | null> => {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(key);
    }
    return null;
  },
  setItem: async (key: string, value: string): Promise<void> => {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(key, value);
    }
  },
  removeItem: async (key: string): Promise<void> => {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(key);
    }
  },
};
