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

const safeSet = (
  set: (partial: any) => void,
  actionName: string,
  partial: any
) => {
  __SET_COUNT++;
  const elapsed = Date.now() - __SET_START_TIME;
  
  console.log(`[ZUSTAND set] #${__SET_COUNT} ${actionName} (${elapsed}ms)`);
  
  // Kill switch: if >50 sets in <2 seconds, stop
  if (__SET_COUNT > 50 && elapsed < 2000) {
    if (!__SET_KILL_SWITCH) {
      console.error(`[ZUSTAND] LOOP DETECTED! ${__SET_COUNT} sets in ${elapsed}ms. KILL SWITCH ON.`);
      __SET_KILL_SWITCH = true;
    }
    return; // Don't execute the set
  }
  
  set(partial);
};

// Reset counter periodically (every 5 seconds)
if (typeof window !== 'undefined') {
  setInterval(() => {
    if (__SET_COUNT > 0) {
      console.log(`[ZUSTAND] Resetting counter. Last period: ${__SET_COUNT} sets`);
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
  birth_location: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
  };
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
  date: string;
  title?: string;
  content: string;
  mood?: string;
  tags?: string[];
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
    safeSet(set, 'clearUser', { user: null, chart: null, hasCompletedOnboarding: false, journalEntries: [] });
  },
  
  setJournalEntries: (entries) => {
    safeSet(set, 'setJournalEntries', { journalEntries: entries });
  },
  
  addJournalEntry: (entry) => {
    const current = get().journalEntries ?? [];
    safeSet(set, 'addJournalEntry', { journalEntries: [entry, ...current] });
  },
  
  // Session restore - NO-OP
  restoreSession: async () => {
    console.log('[restoreSession] NO-OP - isolation mode');
    safeSet(set, 'restoreSession-noop', { hasTriedSessionRestore: true, isRestoringSession: false });
    return false;
  },
}));

// Log store creation
console.log('[ZUSTAND] Store created - isolation version');
