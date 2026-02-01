import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface User {
  id: string;
  name?: string;
  email?: string;
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

// ChartDetails type for UI caching (matches API response)
interface CachedChartDetails {
  computation_version: string;
  human_design: {
    type: string | null;
    authority: string | null;
    profile: string | null;
    incarnation_cross: string | null;
    strategy: string | null;
    personality_sun: any | null;
    design_sun: any | null;
    defined_centers: string[];
    defined_channels: string[];
    definition: string | null;
    design_datetime_utc_iso: string | null;
  };
  astrology: {
    sun: any | null;
    moon: any | null;
    rising: any | null;
    mc: any | null;
    chart_type: string | null;
    sidereal_settings: any | null;
    planets: any[];
    houses: any[];
  };
  numerology: {
    life_path: any | null;
    expression: any | null;
  };
  // Cache metadata
  _cachedAt: number;
  _userBirthDataHash: string;
}

interface AppState {
  user: User | null;
  chart: any | null;
  chartDetails: CachedChartDetails | null;
  dailyReflection: DailyReflection | null;
  journalEntries: JournalEntry[];
  hasCompletedOnboarding: boolean;
  hasSeenInterpretationNotice: boolean;
  
  // Actions
  setUser: (user: User) => void;
  setChart: (chart: any) => void;
  setChartDetails: (details: CachedChartDetails | null) => void;
  cacheChartDetails: (details: any) => void;
  invalidateChartDetailsCache: () => void;
  getChartDetailsCacheKey: () => string;
  setDailyReflection: (reflection: DailyReflection) => void;
  setJournalEntries: (entries: JournalEntry[]) => void;
  addJournalEntry: (entry: JournalEntry) => void;
  completeOnboarding: () => void;
  acknowledgeInterpretationNotice: () => void;
  clearUser: () => void;
  loadPersistedData: () => Promise<void>;
}

// Generate a hash of user birth data for cache invalidation
const generateBirthDataHash = (user: User | null): string => {
  if (!user) return '';
  return `${user.birth_date}|${user.birth_time || ''}|${user.birth_location?.latitude}|${user.birth_location?.longitude}`;
};

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  chart: null,
  chartDetails: null,
  dailyReflection: null,
  journalEntries: [],
  hasCompletedOnboarding: false,
  hasSeenInterpretationNotice: false,
  
  setUser: async (user) => {
    const currentUser = get().user;
    const currentHash = generateBirthDataHash(currentUser);
    const newHash = generateBirthDataHash(user);
    
    set({ user });
    await AsyncStorage.setItem('user', JSON.stringify(user));
    
    // Invalidate chart details cache if birth data changed
    if (currentHash && currentHash !== newHash) {
      console.log('[Store] Birth data changed, invalidating chartDetails cache');
      get().invalidateChartDetailsCache();
    }
  },
  
  setChart: async (chart) => {
    set({ chart });
    await AsyncStorage.setItem('chart', JSON.stringify(chart));
  },
  
  setChartDetails: (details) => {
    set({ chartDetails: details });
  },
  
  cacheChartDetails: async (details) => {
    const user = get().user;
    const cachedDetails: CachedChartDetails = {
      ...details,
      _cachedAt: Date.now(),
      _userBirthDataHash: generateBirthDataHash(user),
    };
    set({ chartDetails: cachedDetails });
    await AsyncStorage.setItem('chartDetails', JSON.stringify(cachedDetails));
    console.log('[Store] ChartDetails cached successfully');
  },
  
  invalidateChartDetailsCache: async () => {
    set({ chartDetails: null });
    await AsyncStorage.removeItem('chartDetails');
    console.log('[Store] ChartDetails cache invalidated');
  },
  
  getChartDetailsCacheKey: () => {
    return generateBirthDataHash(get().user);
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
    await AsyncStorage.setItem('hasCompletedOnboarding', 'true');
  },
  
  acknowledgeInterpretationNotice: async () => {
    set({ hasSeenInterpretationNotice: true });
    await AsyncStorage.setItem('hasSeenInterpretationNotice', 'true');
  },
  
  clearUser: async () => {
    set({
      user: null,
      chart: null,
      chartDetails: null,
      dailyReflection: null,
      journalEntries: [],
      hasCompletedOnboarding: false,
      hasSeenInterpretationNotice: false,
    });
    await AsyncStorage.multiRemove([
      'user', 
      'chart', 
      'chartDetails',
      'hasCompletedOnboarding', 
      'hasSeenInterpretationNotice'
    ]);
  },
  
  loadPersistedData: async () => {
    try {
      const [userStr, chartStr, chartDetailsStr, onboardingStr, interpretationStr] = await AsyncStorage.multiGet([
        'user',
        'chart',
        'chartDetails',
        'hasCompletedOnboarding',
        'hasSeenInterpretationNotice',
      ]);
      
      let loadedUser: User | null = null;
      
      if (userStr[1]) {
        loadedUser = JSON.parse(userStr[1]);
        set({ user: loadedUser });
      }
      if (chartStr[1]) {
        set({ chart: JSON.parse(chartStr[1]) });
      }
      if (chartDetailsStr[1]) {
        const cachedDetails = JSON.parse(chartDetailsStr[1]) as CachedChartDetails;
        // Validate cache - check if birth data hash matches
        const currentHash = generateBirthDataHash(loadedUser);
        if (cachedDetails._userBirthDataHash === currentHash) {
          set({ chartDetails: cachedDetails });
          console.log('[Store] ChartDetails loaded from cache');
        } else {
          // Cache is stale, remove it
          console.log('[Store] ChartDetails cache stale, invalidating');
          await AsyncStorage.removeItem('chartDetails');
        }
      }
      if (onboardingStr[1]) {
        set({ hasCompletedOnboarding: onboardingStr[1] === 'true' });
      }
      if (interpretationStr[1]) {
        set({ hasSeenInterpretationNotice: interpretationStr[1] === 'true' });
      }
    } catch (error) {
      console.error('Error loading persisted data:', error);
    }
  },
}));