import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { getChart, getUser, parseSessionRestoreError, SessionRestoreError } from '../services/api';
import { maskUserId, clearStableUserId } from '../utils/stableUserId';

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
    // Persist user ID for session restore - sync ALL storage keys
    // This ensures getStableUserId() and session restore use the same ID
    await storage.setItem(SESSION_USER_ID_KEY, user.id);           // Legacy key
    await storage.setItem('MIRROR_USER_ID', user.id);               // Primary stable key
    await storage.setItem('user', JSON.stringify(user));
    
    // Also update the stableUserId cache if module is imported
    try {
      const { setStableUserIdCache } = await import('../utils/stableUserId');
      setStableUserIdCache(user.id);
    } catch (e) {
      // Module might not have the function, that's ok
    }
    console.log('[setUser] Persisted user ID to all storage keys:', user.id?.slice(0, 8) + '...');
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
    
    // Set restoring=true immediately, hasTriedSessionRestore stays false until finally
    set({ isRestoringSession: true, sessionRestoreError: null });
    
    try {
      // =====================================================================
      // STEP 1: Load persisted data from storage FIRST
      // =====================================================================
      await get().loadPersistedData();
      
      // Check if we loaded COMPLETE data from storage
      const stateAfterLoad = get();
      if (stateAfterLoad.user && stateAfterLoad.chart) {
        console.log('[SessionRestore] ✓ Restored from local storage (user + chart)');
        // IMPORTANT: Also sync the stable user ID cache with the persisted user
        if (stateAfterLoad.user.id) {
          try {
            const { setStableUserIdCache } = await import('../utils/stableUserId');
            setStableUserIdCache(stateAfterLoad.user.id);
            console.log('[SessionRestore] ✓ Synced stable user ID cache:', maskUserId(stateAfterLoad.user.id));
          } catch (e) {
            // Ignore if function not available
          }
        }
        return true;
      }
      
      // =====================================================================
      // STEP 2: Determine the user ID to use for API restore
      // Priority: persisted user.id > MIRROR_USER_ID > mirror_last_user_id > (NO UUID GENERATION)
      // =====================================================================
      let userId: string | null = null;
      let userIdSource = 'unknown';
      
      // Check if we have a persisted user object with an ID
      if (stateAfterLoad.user?.id) {
        userId = stateAfterLoad.user.id;
        userIdSource = 'persisted_user_object';
        console.log('[SessionRestore] 📍 Using user ID from persisted user object:', maskUserId(userId));
      }
      
      // If no user object, check storage keys directly (in priority order)
      if (!userId) {
        const mirrorUserId = await storage.getItem('MIRROR_USER_ID');
        if (mirrorUserId) {
          userId = mirrorUserId;
          userIdSource = 'MIRROR_USER_ID';
          console.log('[SessionRestore] 📍 Using user ID from MIRROR_USER_ID:', maskUserId(userId));
        }
      }
      
      if (!userId) {
        const lastUserId = await storage.getItem(SESSION_USER_ID_KEY);
        if (lastUserId) {
          userId = lastUserId;
          userIdSource = 'mirror_last_user_id';
          console.log('[SessionRestore] 📍 Using user ID from mirror_last_user_id:', maskUserId(userId));
        }
      }
      
      // =====================================================================
      // STEP 3: If NO valid persisted user ID exists, route to onboarding
      // DO NOT generate a UUID - UUIDs are not valid MongoDB ObjectIds
      // =====================================================================
      if (!userId) {
        console.log('[SessionRestore] ⚠️ No persisted user ID found - routing to onboarding');
        console.log('[SessionRestore] 🚫 UUID generation SKIPPED - only MongoDB ObjectIds are valid');
        set({ 
          sessionRestoreError: null,
          hasCompletedOnboarding: false
        });
        return false;
      }
      
      // =====================================================================
      // STEP 4: Validate the user ID format
      // MongoDB ObjectIds are 24 hex characters - reject UUIDs
      // =====================================================================
      const isMongoObjectId = /^[a-f\d]{24}$/i.test(userId);
      const isUUID = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i.test(userId);
      
      if (isUUID) {
        console.log('[SessionRestore] ⚠️ Found UUID format - clearing and routing to onboarding');
        console.log('[SessionRestore] UUID:', maskUserId(userId), '- backend requires MongoDB ObjectId');
        await storage.removeItem('MIRROR_USER_ID');
        await storage.removeItem(SESSION_USER_ID_KEY);
        await storage.removeItem('user');
        await storage.removeItem('chart');
        set({ 
          sessionRestoreError: null,
          hasCompletedOnboarding: false
        });
        return false;
      }
      
      console.log('[SessionRestore] ✓ User ID format valid:', userIdSource, isMongoObjectId ? '(MongoDB ObjectId)' : '');
      console.log('[SessionRestore] Attempting API restore with:', maskUserId(userId));
      
      // Sync the stable user ID cache
      try {
        const { setStableUserIdCache } = await import('../utils/stableUserId');
        setStableUserIdCache(userId);
      } catch (e) {
        // Ignore if function not available
      }
      
      // =====================================================================
      // STEP 5: Fetch user and chart from API
      // =====================================================================
      
      // Fetch user data
      let userData: User | null = null;
      let userError: SessionRestoreError | null = null;
      
      try {
        userData = await getUser(userId);
        console.log('[SessionRestore] Fetched user:', userData?.name);
      } catch (error: any) {
        userError = parseSessionRestoreError(error);
        console.log('[SessionRestore] User fetch error:', userError.code, userError.message);
        
        // Handle recovery actions for user errors
        if (userError.recovery_action === 'clear_session') {
          console.log('[SessionRestore] Clearing invalid session data...');
          await clearStableUserId();
          await storage.removeItem('user');
          await storage.removeItem('chart');
          await storage.removeItem('hasCompletedOnboarding');
          set({ 
            sessionRestoreError: userError.message,
            hasCompletedOnboarding: false
          });
          return false;
        }
        
        if (userError.recovery_action === 'start_onboarding') {
          console.log('[SessionRestore] User not found, routing to onboarding...');
          set({ 
            sessionRestoreError: null,
            hasCompletedOnboarding: false
          });
          return false;
        }
      }
      
      // Fetch chart data
      let chartData = null;
      let chartError: SessionRestoreError | null = null;
      
      try {
        chartData = await getChart(userId);
        console.log('[SessionRestore] Fetched chart, computation_version:', chartData?.computation_version);
      } catch (error: any) {
        chartError = parseSessionRestoreError(error);
        console.log('[SessionRestore] Chart fetch error:', chartError.code, chartError.message);
        
        // Handle recovery actions for chart errors
        if (chartError.recovery_action === 'clear_session') {
          console.log('[SessionRestore] Clearing invalid session data...');
          await clearStableUserId();
          await storage.removeItem('user');
          await storage.removeItem('chart');
          await storage.removeItem('hasCompletedOnboarding');
          set({ 
            sessionRestoreError: chartError.message,
            hasCompletedOnboarding: false
          });
          return false;
        }
        
        if (chartError.recovery_action === 'start_onboarding') {
          console.log('[SessionRestore] Chart not found, routing to onboarding...');
          set({ 
            sessionRestoreError: null,
            hasCompletedOnboarding: false
          });
          return false;
        }
      }
      
      // Create minimal user object if we couldn't fetch user data but have chart
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
      
      // If we have neither user nor chart, route to onboarding
      if (!userData && !chartData) {
        console.log('[SessionRestore] No user or chart found, routing to onboarding');
        set({ hasCompletedOnboarding: false });
        return false;
      }
      
      console.log('[SessionRestore] Session restored successfully');
      return !!(userData && chartData);
      
    } catch (error: any) {
      console.error('[SessionRestore] Unexpected error:', error);
      // For unexpected errors, clear session and route to onboarding
      set({ 
        sessionRestoreError: 'Unable to restore session. Please start fresh.',
        hasCompletedOnboarding: false
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
