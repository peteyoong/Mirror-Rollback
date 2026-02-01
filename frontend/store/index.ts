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

interface AppState {
  user: User | null;
  chart: any | null;
  dailyReflection: DailyReflection | null;
  journalEntries: JournalEntry[];
  hasCompletedOnboarding: boolean;
  
  // Actions
  setUser: (user: User) => void;
  setChart: (chart: any) => void;
  setDailyReflection: (reflection: DailyReflection) => void;
  setJournalEntries: (entries: JournalEntry[]) => void;
  addJournalEntry: (entry: JournalEntry) => void;
  completeOnboarding: () => void;
  clearUser: () => void;
  loadPersistedData: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  chart: null,
  dailyReflection: null,
  journalEntries: [],
  hasCompletedOnboarding: false,
  
  setUser: async (user) => {
    set({ user });
    await AsyncStorage.setItem('user', JSON.stringify(user));
  },
  
  setChart: async (chart) => {
    set({ chart });
    await AsyncStorage.setItem('chart', JSON.stringify(chart));
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
  
  clearUser: async () => {
    set({
      user: null,
      chart: null,
      dailyReflection: null,
      journalEntries: [],
      hasCompletedOnboarding: false,
    });
    await AsyncStorage.multiRemove(['user', 'chart', 'hasCompletedOnboarding']);
  },
  
  loadPersistedData: async () => {
    try {
      const [userStr, chartStr, onboardingStr] = await AsyncStorage.multiGet([
        'user',
        'chart',
        'hasCompletedOnboarding',
      ]);
      
      if (userStr[1]) {
        set({ user: JSON.parse(userStr[1]) });
      }
      if (chartStr[1]) {
        set({ chart: JSON.parse(chartStr[1]) });
      }
      if (onboardingStr[1]) {
        set({ hasCompletedOnboarding: onboardingStr[1] === 'true' });
      }
    } catch (error) {
      console.error('Error loading persisted data:', error);
    }
  },
}));