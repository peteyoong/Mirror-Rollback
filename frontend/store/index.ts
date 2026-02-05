import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { getChart, getUser } from '../services/api';

// Storage key for session persistence
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

interface AppState {
  user: User | null;
  chart: any | null;
  dailyReflection: DailyReflection | null;
  journalEntries: JournalEntry[];
  hasCompletedOnboarding: boolean;
  
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
  loadPersistedData: () => Promise<void>;
  
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
  questionnaireAnswers: [],
  questionnaireComplete: false,
  isRestoringSession: false,
  hasTriedSessionRestore: false,  // NEW: Auth hydration gate
  sessionRestoreError: null,
  
  setUser: async (user) => {
    set({ user });
    // Persist user ID for session restore
    await storage.setItem(SESSION_USER_ID_KEY, user.id);
    await storage.setItem('user', JSON.stringify(user));
  },
  
  setChart: async (chart) => {
    set({ chart });
    await storage.setItem('chart', JSON.stringify(chart));
  },
  
  setDailyReflection: (reflection) => {
    set({ dailyReflection: reflection });
  },
  
  setJournalEntries: (entries) => {
    set({ journalEntries: entries });
  },
  
  addJournalEntry: (entry) => {
    set((state) => ({
      journalEntries: [entry, ...state.journalEntries],
    }));
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
  
  loadPersistedData: async () => {
    try {
      const [userStr, chartStr, onboardingStr] = await Promise.all([
        storage.getItem('user'),
        storage.getItem('chart'),
        storage.getItem('hasCompletedOnboarding'),
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
    
    // Set restoring=true immediately, hasTriedSessionRestore stays false until finally
    set({ isRestoringSession: true, sessionRestoreError: null });
    
    try {
      // First try to load from local storage
      await get().loadPersistedData();
      
      // Check if we loaded data from storage
      const stateAfterLoad = get();
      if (stateAfterLoad.user && stateAfterLoad.chart) {
        console.log('[SessionRestore] Restored from local storage');
        return true;
      }
      
      // If no local data, try to fetch from API using persisted user ID
      const userId = await storage.getItem(SESSION_USER_ID_KEY);
      
      if (!userId) {
        console.log('[SessionRestore] No persisted userId found - fresh user');
        return false;
      }
      
      console.log('[SessionRestore] Found persisted userId:', userId);
      
      // Fetch user data
      let userData: User | null = null;
      try {
        userData = await getUser(userId);
        console.log('[SessionRestore] Fetched user:', userData?.name);
      } catch (error) {
        console.warn('[SessionRestore] Could not fetch user data:', error);
        // Continue anyway - we can still get chart data
      }
      
      // Fetch chart data
      const chartData = await getChart(userId);
      console.log('[SessionRestore] Fetched chart, computation_version:', chartData?.computation_version);
      
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
      
      console.log('[SessionRestore] Session restored successfully');
      return !!(userData && chartData);
      
    } catch (error: any) {
      console.error('[SessionRestore] Failed to restore session:', error);
      set({ 
        sessionRestoreError: error?.message || 'Failed to restore session' 
      });
      return false;
    } finally {
      // CRITICAL: Always set these in finally block
      set({ isRestoringSession: false, hasTriedSessionRestore: true });
      console.log('[SessionRestore] Restore attempt completed, hasTriedSessionRestore=true');
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
