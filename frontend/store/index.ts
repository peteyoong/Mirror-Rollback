import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { getChart, getUser } from '../services/api';
import { getStableUserId, assertUserIdStable, maskUserId } from '../utils/stableUserId';

// ============================================================================
// GLOBAL SET() LOGGER - TEMPORARY FOR DEBUGGING
// ============================================================================
let __SET_COUNT = 0;
const logSet = (actionName: string) => {
  __SET_COUNT++;
  console.log(`[ZUSTAND set] #${__SET_COUNT} ${actionName}`);
  if (__SET_COUNT > 50) {
    console.error('[ZUSTAND] SET COUNT > 50 - POSSIBLE INFINITE LOOP!');
  }
};

// ============================================================================
// SESSION RESTORE - Simple module-level flag (no globalThis hacks)
// ============================================================================
let _sessionRestoreStarted = false;

// Storage key for session persistence (legacy - now using MIRROR_USER_ID via stableUserId)
const SESSION_USER_ID_KEY = 'mirror_last_user_id';

// Chat session keys
export const CHAT_SESSION_KEYS = {
  mirror: 'mirror_session_id',
  astrology: 'astrology_session_id',
  human_design: 'human_design_session_id',
} as const;

// Cross-platform storage helper (AsyncStorage + localStorage fallback for web)
export const storage = {
  async getItem(key: string): Promise<string | null> {
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
      // If AsyncStorage fails on web, try localStorage
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage.getItem(key);
      }
      console.error('Storage getItem error:', error);
      return null;
    }
  },
  
  async setItem(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(key, value);
      // Also set in localStorage on web for redundancy
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);
      }
    } catch (error) {
      // If AsyncStorage fails on web, try localStorage
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);
      } else {
        console.error('Storage setItem error:', error);
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
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(key);
      }
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
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
        keys.forEach(key => window.localStorage.removeItem(key));
      }
      console.error('Storage multiRemove error:', error);
    }
  }
};

interface User {
  id: string;
  name?: string;
  birth_date: string;
  birth_time?: string;
  birth_location: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
  };
  has_chart: boolean;
}

interface JournalEntry {
  id: string;
  content: string;
  themes: string[];
  created_at: string;
}

interface DailyReflection {
  id: string;
  date: string;
  insight: string;
  question: string;
  perspective: string;
}

// Chat message interface for persistence
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date | string;
}

// Chat thread storage key format: "chat:{userId}:{threadKey}"
// threadKey examples: "mirror:default", "reflection:default", "journal:{entryId}"
export const CHAT_STORAGE_PREFIX = 'mirror_chat_messages';

export function getChatStorageKey(userId: string, threadKey: string): string {
  return `${CHAT_STORAGE_PREFIX}:${userId}:${threadKey}`;
}

interface AppState {
  user: User | null;
  chart: any | null;
  dailyReflection: DailyReflection | null;
  journalEntries: JournalEntry[];
  hasCompletedOnboarding: boolean;
  
  // Chat messages state (persisted)
  chatMessages: Record<string, ChatMessage[]>;  // Key: "{userId}:{threadKey}"
  
  // Questionnaire state
  questionnaireAnswers: string[];
  questionnaireComplete: boolean;
  
  // Session restore state - THE AUTH HYDRATION GATE
  isRestoringSession: boolean;
  hasTriedSessionRestore: boolean;  // NEW: true once restore attempt completes (success or fail)
  sessionRestoreError: string | null;
  
  // Actions
  setUser: (user: User) => Promise<void>;
  setChart: (chart: any) => Promise<void>;
  setDailyReflection: (reflection: DailyReflection) => void;
  setJournalEntries: (entries: JournalEntry[]) => void;
  addJournalEntry: (entry: JournalEntry) => void;
  completeOnboarding: () => Promise<void>;
  clearUser: () => Promise<void>;
  resetLocalSession: (forceReload?: boolean) => Promise<void>;  // NEW: Full session reset
  loadPersistedData: () => Promise<void>;
  
  // Chat message actions
  getChatMessages: (threadKey: string) => ChatMessage[];
  addChatMessage: (threadKey: string, message: ChatMessage) => Promise<void>;
  setChatMessages: (threadKey: string, messages: ChatMessage[]) => Promise<void>;
  loadChatMessages: (threadKey: string) => Promise<ChatMessage[]>;
  clearChatMessages: (threadKey: string) => Promise<void>;
  
  // Questionnaire actions
  setQuestionnaireAnswer: (index: number, answer: string) => Promise<void>;
  completeQuestionnaire: () => Promise<void>;
  
  // Session restore actions
  restoreSession: () => Promise<boolean>;
  retrySessionRestore: () => Promise<boolean>;
  clearSessionRestoreError: () => void;
  
  // Helper to check if we should redirect to onboarding
  shouldRedirectToOnboarding: () => boolean;
}

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  chart: null,
  dailyReflection: null,
  journalEntries: [],
  hasCompletedOnboarding: false,
  chatMessages: {},  // Chat messages by thread key
  questionnaireAnswers: [],
  questionnaireComplete: false,
  isRestoringSession: false,
  hasTriedSessionRestore: false,  // NEW: Auth hydration gate
  sessionRestoreError: null,
  
  setUser: async (user) => {
    logSet('setUser');
    set({ user });
    // Persist user ID for session restore
    await storage.setItem(SESSION_USER_ID_KEY, user.id);
    await storage.setItem('user', JSON.stringify(user));
  },
  
  setChart: async (chart) => {
    logSet('setChart');
    set({ chart });
    await storage.setItem('chart', JSON.stringify(chart));
  },
  
  setDailyReflection: (reflection) => {
    logSet('setDailyReflection');
    set({ dailyReflection: reflection });
  },
  
  setJournalEntries: (entries) => {
    logSet('setJournalEntries');
    set({ journalEntries: entries });
  },
  
  addJournalEntry: (entry) => {
    set((state) => ({
      journalEntries: [entry, ...state.journalEntries],
    }));
  },
  
  // Chat message actions - persist chat history across tab switches and refreshes
  getChatMessages: (threadKey: string) => {
    const { chatMessages, user } = get();
    if (!user?.id) return [];
    const key = `${user.id}:${threadKey}`;
    return chatMessages[key] || [];
  },
  
  addChatMessage: async (threadKey: string, message: ChatMessage) => {
    const { chatMessages, user } = get();
    if (!user?.id) return;
    
    const key = `${user.id}:${threadKey}`;
    const existingMessages = chatMessages[key] || [];
    const updatedMessages = [...existingMessages, message];
    
    // Update state
    set({
      chatMessages: {
        ...chatMessages,
        [key]: updatedMessages,
      },
    });
    
    // Persist to storage
    const storageKey = getChatStorageKey(user.id, threadKey);
    await storage.setItem(storageKey, JSON.stringify(updatedMessages));
    console.log(`[ChatStore] Added message to ${key}, total: ${updatedMessages.length}`);
  },
  
  setChatMessages: async (threadKey: string, messages: ChatMessage[]) => {
    const { chatMessages, user } = get();
    if (!user?.id) return;
    
    const key = `${user.id}:${threadKey}`;
    
    // Update state
    set({
      chatMessages: {
        ...chatMessages,
        [key]: messages,
      },
    });
    
    // Persist to storage
    const storageKey = getChatStorageKey(user.id, threadKey);
    await storage.setItem(storageKey, JSON.stringify(messages));
    console.log(`[ChatStore] Set ${messages.length} messages for ${key}`);
  },
  
  // DEPRECATED: Use pure helpers from utils/chatPersistence.ts instead
  // This function calls set() which can cause loops if called in render paths
  loadChatMessages: async (threadKey: string): Promise<ChatMessage[]> => {
    console.warn('[ChatStore] loadChatMessages is DEPRECATED - use loadMessages from utils/chatPersistence.ts');
    const { user } = get();
    if (!user?.id) {
      console.log('[ChatStore] loadChatMessages: No user id, returning empty');
      return [];
    }
    
    const key = `${user.id}:${threadKey}`;
    const storageKey = getChatStorageKey(user.id, threadKey);
    
    console.log(`[ChatStore] loadChatMessages: key=${key}, storageKey=${storageKey}`);
    
    // Load from storage - READ ONLY, no set() calls
    const stored = await storage.getItem(storageKey);
    
    if (stored) {
      try {
        const loadedMessages = JSON.parse(stored) as ChatMessage[];
        console.log(`[ChatStore] Loaded ${loadedMessages.length} messages from storage for ${key}`);
        // NOTE: NOT calling set() here anymore - use pure helpers instead
        return loadedMessages;
      } catch (e) {
        console.error('[ChatStore] Failed to parse stored messages:', e);
      }
    } else {
      console.log(`[ChatStore] No stored messages found for ${key}`);
    }
    
    return [];
  },
  
  clearChatMessages: async (threadKey: string) => {
    const { chatMessages, user } = get();
    if (!user?.id) return;
    
    const key = `${user.id}:${threadKey}`;
    const newChatMessages = { ...chatMessages };
    delete newChatMessages[key];
    
    set({ chatMessages: newChatMessages });
    
    const storageKey = getChatStorageKey(user.id, threadKey);
    await storage.removeItem(storageKey);
    console.log(`[ChatStore] Cleared messages for ${key}`);
  },
  
  completeOnboarding: async () => {
    set({ hasCompletedOnboarding: true });
    await storage.setItem('hasCompletedOnboarding', 'true');
  },
  
  // Questionnaire actions
  setQuestionnaireAnswer: async (index: number, answer: string) => {
    const { questionnaireAnswers } = get();
    const newAnswers = [...questionnaireAnswers];
    newAnswers[index] = answer;
    set({ questionnaireAnswers: newAnswers });
    // Persist answers to local storage
    await storage.setItem('questionnaireAnswers', JSON.stringify(newAnswers));
  },
  
  completeQuestionnaire: async () => {
    set({ questionnaireComplete: true });
    await storage.setItem('questionnaireComplete', 'true');
  },
  
  clearUser: async () => {
    set({
      user: null,
      chart: null,
      dailyReflection: null,
      journalEntries: [],
      hasCompletedOnboarding: false,
      questionnaireAnswers: [],
      questionnaireComplete: false,
      sessionRestoreError: null,
    });
    // Clear user data and all chat session IDs
    await storage.multiRemove([
      SESSION_USER_ID_KEY, 
      'user', 
      'chart', 
      'hasCompletedOnboarding',
      'questionnaireAnswers',
      'questionnaireComplete',
      CHAT_SESSION_KEYS.mirror,
      CHAT_SESSION_KEYS.astrology,
      CHAT_SESSION_KEYS.human_design,
    ]);
  },
  
  /**
   * Reset Local Session - Clears ALL local data for sign out / start fresh
   * 
   * This function:
   * 1. Clears all AsyncStorage keys
   * 2. Clears localStorage on web
   * 3. Resets zustand state
   * 4. Optionally forces a page reload on web
   */
  resetLocalSession: async (forceReload: boolean = true) => {
    console.log('[resetLocalSession] Clearing all local data...');
    
    // All keys that might be storing session data
    const keysToRemove = [
      SESSION_USER_ID_KEY,
      'user',
      'chart',
      'hasCompletedOnboarding',
      'questionnaireAnswers',
      'questionnaireComplete',
      'mirror_last_build',
      'journal_draft',
      CHAT_SESSION_KEYS.mirror,
      CHAT_SESSION_KEYS.astrology,
      CHAT_SESSION_KEYS.human_design,
      'MIRROR_USER_ID',  // stableUserId key
    ];
    
    // Clear AsyncStorage
    try {
      await AsyncStorage.multiRemove(keysToRemove);
    } catch (e) {
      console.warn('[resetLocalSession] AsyncStorage clear error:', e);
    }
    
    // Clear localStorage on web (for redundancy)
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.localStorage) {
      keysToRemove.forEach(key => {
        try {
          window.localStorage.removeItem(key);
        } catch (e) {
          // Ignore errors
        }
      });
      // Also clear any other Mirror-related keys
      const allKeys = Object.keys(window.localStorage);
      allKeys.forEach(key => {
        if (key.startsWith('mirror_') || key.startsWith('MIRROR_')) {
          window.localStorage.removeItem(key);
        }
      });
    }
    
    // Reset zustand state
    set({
      user: null,
      chart: null,
      dailyReflection: null,
      journalEntries: [],
      hasCompletedOnboarding: false,
      questionnaireAnswers: [],
      questionnaireComplete: false,
      isRestoringSession: false,
      hasTriedSessionRestore: false,
      sessionRestoreError: null,
    });
    
    console.log('[resetLocalSession] Local data cleared');
    
    // Force reload on web to reset app state completely
    if (forceReload && Platform.OS === 'web' && typeof window !== 'undefined') {
      const resetUrl = '/?reset=1&t=' + Date.now();
      console.log('[resetLocalSession] Forcing page reload to:', resetUrl);
      window.location.href = resetUrl;
    }
  },
  
  loadPersistedData: async () => {
    try {
      const [userStr, chartStr, onboardingStr, questionnaireAnswersStr, questionnaireCompleteStr] = await Promise.all([
        storage.getItem('user'),
        storage.getItem('chart'),
        storage.getItem('hasCompletedOnboarding'),
        storage.getItem('questionnaireAnswers'),
        storage.getItem('questionnaireComplete'),
      ]);
      
      if (userStr) {
        set({ user: JSON.parse(userStr) });
      }
      if (chartStr) {
        set({ chart: JSON.parse(chartStr) });
      }
      if (onboardingStr) {
        set({ hasCompletedOnboarding: onboardingStr === 'true' });
      }
      if (questionnaireAnswersStr) {
        set({ questionnaireAnswers: JSON.parse(questionnaireAnswersStr) });
      }
      if (questionnaireCompleteStr) {
        set({ questionnaireComplete: questionnaireCompleteStr === 'true' });
      }
    } catch (error) {
      console.error('Error loading persisted data:', error);
    }
  },
  
  // Session restore: fetch user/chart from API using persisted userId
  // TEMPORARY NO-OP FOR DEBUGGING - REMOVE WHEN LOOP IS FOUND
  restoreSession: async () => {
    console.log('[restoreSession] NO-OP - DISABLED FOR DEBUGGING');
    logSet('restoreSession-NOOP');
    set({ hasTriedSessionRestore: true, isRestoringSession: false });
    return false;
  },
  
  /* ORIGINAL restoreSession - COMMENTED OUT FOR DEBUGGING
  restoreSession: async () => {
    // Guard: Only run once per app lifecycle
    if (_sessionRestoreStarted) {
      console.log('[SessionRestore] Already started, skipping');
      return false;
    }
    _sessionRestoreStarted = true;
    
    const { user, chart } = get();
    
    // If already have user and chart, just mark as tried
    if (user && chart) {
      console.log('[SessionRestore] Already have user and chart');
      logSet('restoreSession-already-have');
      set({ hasTriedSessionRestore: true, isRestoringSession: false });
      return true;
    }
    
    console.log('[SessionRestore] Starting...');
    logSet('restoreSession-start');
    set({ isRestoringSession: true, sessionRestoreError: null });
    
    try {
      // First try to load from local storage
      const [storedUser, storedChart, storedOnboarding] = await Promise.all([
        storage.getItem('user'),
        storage.getItem('chart'),
        storage.getItem('hasCompletedOnboarding'),
      ]);
      
      let restoredUser: User | null = null;
      let restoredChart: any = null;
      let restoredOnboarding = false;
      
      if (storedUser) {
        try { restoredUser = JSON.parse(storedUser); } catch (e) {}
      }
      if (storedChart) {
        try { restoredChart = JSON.parse(storedChart); } catch (e) {}
      }
      if (storedOnboarding === 'true') {
        restoredOnboarding = true;
      }
      
      // If we have stored data, use it directly (no API calls needed)
      if (restoredUser && restoredChart) {
        console.log('[SessionRestore] Restored from local storage');
        set({
          user: restoredUser,
          chart: restoredChart,
          hasCompletedOnboarding: restoredOnboarding,
          isRestoringSession: false,
          hasTriedSessionRestore: true,
        });
        return true;
      }
      
      // No stored data = new user, don't try to restore
      const storedUserId = await storage.getItem(SESSION_USER_ID_KEY);
      if (!storedUserId && !storedUser) {
        console.log('[SessionRestore] No stored user - new user flow');
        set({ isRestoringSession: false, hasTriedSessionRestore: true });
        return false;
      }
      
      // Try to fetch from API using stable user ID
      const userId = await getStableUserId();
      console.log('[SessionRestore] Fetching from API for userId:', maskUserId(userId));
      
      // Fetch user and chart in parallel
      let fetchedUser: User | null = null;
      let fetchedChart: any = null;
      
      try {
        [fetchedUser, fetchedChart] = await Promise.all([
          getUser(userId).catch(() => null),
          getChart(userId).catch(() => null),
        ]);
      } catch (error) {
        console.warn('[SessionRestore] API fetch error:', error);
      }
      
      // Create minimal user if needed
      if (!fetchedUser && fetchedChart) {
        fetchedUser = {
          id: userId,
          birth_date: '',
          birth_location: { city: '', country: '', latitude: 0, longitude: 0 },
          has_chart: true,
        };
      }
      
      // Persist to storage
      if (fetchedUser) {
        await storage.setItem('user', JSON.stringify(fetchedUser));
      }
      if (fetchedChart) {
        await storage.setItem('chart', JSON.stringify(fetchedChart));
        await storage.setItem('hasCompletedOnboarding', 'true');
      }
      
      set({
        user: fetchedUser,
        chart: fetchedChart,
        hasCompletedOnboarding: !!fetchedChart,
        isRestoringSession: false,
        hasTriedSessionRestore: true,
      });
      
      console.log('[SessionRestore] Complete');
      return !!(fetchedUser && fetchedChart);
      
    } catch (error: any) {
      console.error('[SessionRestore] Failed:', error);
      set({
        sessionRestoreError: error?.message || 'Failed to restore session',
        isRestoringSession: false,
        hasTriedSessionRestore: true,
      });
      return false;
    }
  },
  END ORIGINAL restoreSession */
  
  // REMOVED: retrySessionRestore was bypassing the module-level guard and could cause loops.
  // For manual retry, use resetLocalSession() which does a full page reload.
  retrySessionRestore: async () => {
    console.log('[SessionRestore] retrySessionRestore called - use resetLocalSession() for full retry');
    // Do NOT reset didRestoreSession - that would cause potential loops
    // Instead, just return current state
    return !!get().user;
  },
  
  clearSessionRestoreError: () => {
    set({ sessionRestoreError: null });
  },
  
  // Helper: Should we redirect to onboarding?
  // Only returns true if we've tried restoring AND there's no user
  shouldRedirectToOnboarding: () => {
    const { hasTriedSessionRestore, isRestoringSession, user } = get();
    
    // If still restoring or haven't tried yet, DON'T redirect
    if (isRestoringSession || !hasTriedSessionRestore) {
      return false;
    }
    
    // Only redirect if restore is done AND no user
    return !user?.id;
  },
}));
