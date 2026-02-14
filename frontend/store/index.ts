import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { getChart, getUser } from '../services/api';
import { getStableUserId, assertUserIdStable, maskUserId } from '../utils/stableUserId';

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

// ===== DEBUG: Set() loop tracer (temporary) =====
let __setCount = 0;
let __lastSetLabel = '';

function debugSet(setFn: any, payload: any, label: string) {
  __setCount += 1;
  __lastSetLabel = label;
  if (__setCount % 5 === 0) {
    console.warn(`[STORE_SET_LOOP] ${label} count=${__setCount}`);
    if (__setCount > 20) {
      console.error(new Error(`[STORE_SET_LOOP] POTENTIAL INFINITE LOOP: ${label}`).stack);
    }
  }
  setFn(payload);
}

// Reset counter periodically to avoid false positives
setInterval(() => {
  if (__setCount > 0) {
    console.log(`[STORE_SET_LOOP] Resetting counter (was ${__setCount}, last: ${__lastSetLabel})`);
    __setCount = 0;
  }
}, 5000);

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
    debugSet(set, { user }, 'setUser');
    // Persist user ID for session restore
    await storage.setItem(SESSION_USER_ID_KEY, user.id);
    await storage.setItem('user', JSON.stringify(user));
  },
  
  setChart: async (chart) => {
    debugSet(set, { chart }, 'setChart');
    await storage.setItem('chart', JSON.stringify(chart));
  },
  
  setDailyReflection: (reflection) => {
    debugSet(set, { dailyReflection: reflection }, 'setDailyReflection');
  },
  
  setJournalEntries: (entries) => {
    debugSet(set, { journalEntries: entries }, 'setJournalEntries');
  },
  
  addJournalEntry: (entry) => {
    debugSet(set, (state: any) => ({
      journalEntries: [entry, ...state.journalEntries],
    }), 'addJournalEntry');
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
    debugSet(set, {
      chatMessages: {
        ...chatMessages,
        [key]: updatedMessages,
      },
    }, 'addChatMessage');
    
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
    debugSet(set, {
      chatMessages: {
        ...chatMessages,
        [key]: messages,
      },
    }, 'setChatMessages');
    
    // Persist to storage
    const storageKey = getChatStorageKey(user.id, threadKey);
    await storage.setItem(storageKey, JSON.stringify(messages));
    console.log(`[ChatStore] Set ${messages.length} messages for ${key}`);
  },
  
  loadChatMessages: async (threadKey: string): Promise<ChatMessage[]> => {
    const { user, chatMessages } = get();
    if (!user?.id) {
      console.log('[ChatStore] loadChatMessages: No user id, returning empty');
      return [];
    }
    
    const key = `${user.id}:${threadKey}`;
    const storageKey = getChatStorageKey(user.id, threadKey);
    const currentMessages = chatMessages[key] ?? [];
    
    console.log(`[ChatStore] loadChatMessages: key=${key}, storageKey=${storageKey}`);
    
    // Load from storage
    const stored = await storage.getItem(storageKey);
    
    if (stored) {
      try {
        const loadedMessages = JSON.parse(stored) as ChatMessage[];
        console.log(`[ChatStore] Loaded ${loadedMessages.length} messages from storage for ${key}`);
        
        // GUARD: Only update state if data actually changed (prevent infinite loops)
        const currentJson = JSON.stringify(currentMessages);
        const loadedJson = JSON.stringify(loadedMessages);
        
        if (currentJson !== loadedJson) {
          console.log(`[ChatStore] Messages changed, updating state for ${key}`);
          debugSet(set, (state: any) => ({
            chatMessages: {
              ...state.chatMessages,
              [key]: loadedMessages,
            },
          }), 'loadChatMessages');
        } else {
          console.log(`[ChatStore] Messages unchanged, skipping set() for ${key}`);
        }
        
        return loadedMessages;
      } catch (e) {
        console.error('[ChatStore] Failed to parse stored messages:', e);
      }
    } else {
      console.log(`[ChatStore] No stored messages found for ${key}`);
    }
    
    return currentMessages;
  },
  
  clearChatMessages: async (threadKey: string) => {
    const { chatMessages, user } = get();
    if (!user?.id) return;
    
    const key = `${user.id}:${threadKey}`;
    const newChatMessages = { ...chatMessages };
    delete newChatMessages[key];
    
    debugSet(set, { chatMessages: newChatMessages }, 'clearChatMessages');
    
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
  restoreSession: async () => {
    const { user, chart, hasTriedSessionRestore, isRestoringSession } = get();
    
    // Prevent duplicate calls
    if (isRestoringSession) {
      console.log('[SessionRestore] Already restoring, skipping...');
      return false;
    }
    
    // If already have user and chart, mark as tried and return success
    if (user && chart) {
      console.log('[SessionRestore] Already have user and chart, skipping restore');
      set({ hasTriedSessionRestore: true });
      return true;
    }
    
    console.log('[SessionRestore] ▶ Starting restore process...');
    
    // Set restoring=true immediately, hasTriedSessionRestore stays false until finally
    set({ isRestoringSession: true, sessionRestoreError: null });
    
    // =========================================================================
    // TIMEOUT FAILSAFE: Ensure restore cannot hang indefinitely
    // =========================================================================
    const RESTORE_TIMEOUT_MS = 5000; // 5 seconds max
    let timeoutTriggered = false;
    
    const timeoutPromise = new Promise<'timeout'>((resolve) => {
      setTimeout(() => {
        timeoutTriggered = true;
        console.warn('[SessionRestore] ⚠️ Restore timeout fallback triggered after 5s');
        resolve('timeout');
      }, RESTORE_TIMEOUT_MS);
    });
    
    const restorePromise = (async (): Promise<boolean> => {
      try {
        // First try to load from local storage
        await get().loadPersistedData();
        
        // Check if we loaded data from storage
        const stateAfterLoad = get();
        if (stateAfterLoad.user && stateAfterLoad.chart) {
          console.log('[SessionRestore] ✓ Restored from local storage');
          return true;
        }
        
        // Check if we have a stored user ID (not just a generated one)
        // Only try API calls if there's actually persisted user data
        const storedUserId = await storage.getItem(SESSION_USER_ID_KEY);
        const storedUser = await storage.getItem('user');
        
        if (!storedUserId && !storedUser) {
          console.log('[SessionRestore] No stored user data, skipping API calls - new user flow');
          // No stored data = new user, don't try to restore
          return false;
        }
        
        // If we have stored data, try to fetch from API using STABLE user ID
        const userId = await getStableUserId();
        
        console.log('[SessionRestore] Using stable userId:', maskUserId(userId));
        
        // Run assertion check in debug mode
        await assertUserIdStable();
        
        // Fetch user data
        let userData: User | null = null;
        try {
          userData = await getUser(userId);
          console.log('[SessionRestore] ✓ Fetched user:', userData?.name);
        } catch (error) {
          console.warn('[SessionRestore] Could not fetch user data:', error);
          // Continue anyway - we can still get chart data
        }
        
        // Fetch chart data
        const chartData = await getChart(userId);
        console.log('[SessionRestore] ✓ Fetched chart, computation_version:', chartData?.computation_version);
        
        // Create minimal user object if we couldn't fetch user data
        if (!userData && chartData) {
          userData = {
            id: userId,
            birth_date: '',
            birth_location: { city: '', country: '', latitude: 0, longitude: 0 },
            has_chart: true,
          };
        }
        
        // Update store
        if (userData) {
          set({ user: userData });
          await storage.setItem('user', JSON.stringify(userData));
        }
        
        if (chartData) {
          set({ chart: chartData, hasCompletedOnboarding: true });
          await storage.setItem('chart', JSON.stringify(chartData));
          await storage.setItem('hasCompletedOnboarding', 'true');
        }
        
        console.log('[SessionRestore] ✓ Session restored successfully');
        return !!(userData && chartData);
        
      } catch (error: any) {
        console.error('[SessionRestore] ✗ Failed to restore session:', error);
        set({ 
          sessionRestoreError: error?.message || 'Failed to restore session' 
        });
        return false;
      }
    })();
    
    // Race between restore and timeout
    try {
      const result = await Promise.race([restorePromise, timeoutPromise]);
      
      if (result === 'timeout') {
        // Timeout triggered - set error state but allow app to continue
        set({ 
          sessionRestoreError: 'Session restore timed out. Please try again.' 
        });
        return false;
      }
      
      return result;
    } finally {
      // CRITICAL: Always set these in finally block - whether success, error, or timeout
      set({ isRestoringSession: false, hasTriedSessionRestore: true });
      console.log(`[SessionRestore] ■ Restore attempt completed (timeout=${timeoutTriggered}), hasTriedSessionRestore=true`);
    }
  },
  
  retrySessionRestore: async () => {
    set({ sessionRestoreError: null, hasTriedSessionRestore: false });
    return get().restoreSession();
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
