import axios from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Resolve API base URL with proper fallback chain for Expo
const getApiBaseUrl = (): string => {
  // 1. Try expo-constants extra config
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (extraUrl && typeof extraUrl === 'string' && extraUrl.length > 0) {
    return extraUrl;
  }
  
  // 2. Try process.env (works in Expo with EXPO_PUBLIC_ prefix)
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    return envUrl;
  }
  
  // 3. For web preview, use relative URL (same origin)
  if (Platform.OS === 'web') {
    // In web, use empty string to make requests relative to current origin
    // The ingress will route /api/* to the backend
    return '';
  }
  
  // 4. Fallback for native development
  return 'http://localhost:8001';
};

const API_BASE_URL = getApiBaseUrl();

// Debug log for troubleshooting (only in dev)
if (__DEV__) {
  console.log('[API] Base URL resolved to:', API_BASE_URL || '(relative)');
}

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 60000, // Increased timeout for slow LLM responses
  headers: {
    'Content-Type': 'application/json',
  },
});

// Daily Focus API (Context Selector Layer)
export interface DailyFocusResponse {
  ambient_line: string;
  context: string | null;
  confidence: number;
  generated_at_iso: string;
}

export const getDailyFocus = async (userId: string): Promise<DailyFocusResponse> => {
  const response = await api.get(`/daily-focus/${userId}`);
  return response.data;
};

// User APIs
export const createUser = async (data: {
  name?: string;
  birth_date: string;
  birth_time?: string;
  city: string;
  country: string;
  timezone: string;
  latitude?: number;
  longitude?: number;
}) => {
  const response = await api.post('/users', data);
  return response.data;
};

export const getUser = async (userId: string) => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};

// Location APIs
export const searchLocations = async (query: string) => {
  const response = await api.post('/locations/search', { query });
  return response.data.results;
};

// Chart APIs
export const calculateChart = async (userId: string) => {
  const response = await api.post('/charts/calculate', { user_id: userId });
  return response.data;
};

export const getChart = async (userId: string) => {
  const response = await api.get(`/charts/${userId}`);
  return response.data;
};

// Journal APIs
export const createJournalEntry = async (userId: string, content: string) => {
  const response = await api.post('/journal', {
    user_id: userId,
    content,
  });
  return response.data;
};

export const getJournalEntries = async (userId: string) => {
  const response = await api.get(`/journal/${userId}`);
  return response.data;
};

// Reflection APIs
export const getDailyReflection = async (userId: string) => {
  const response = await api.post('/reflections/daily', { user_id: userId });
  return response.data;
};

// Chat APIs
export const sendChatMessage = async (userId: string, message: string) => {
  const response = await api.post('/chat', {
    user_id: userId,
    message,
  });
  return response.data;
};

// Lenses APIs
export const getLenses = async () => {
  const response = await api.get('/lenses');
  return response.data;
};

// Enneagram APIs
export const saveEnneagramResult = async (data: {
  user_id: string;
  method: string;
  version: string;
  inferred_core: number;
  inferred_wing: number | string;
  confidence: number;
  confidence_tier: string;
  is_close: boolean;
  top_candidates: { type: number; probability: number }[];
  state_calibration: {
    energy_state: string;
    life_context: string;
    answer_frame: string;
  };
  debug_scores: {
    raw_scores: { [key: string]: number };
    z_scores: { [key: string]: number };
    wing_scores: { left: number; right: number; diff: number };
  };
}) => {
  const response = await api.post('/enneagram/results', data);
  return response.data;
};

export const getEnneagramResult = async (userId: string) => {
  const response = await api.get(`/enneagram/results/${userId}`);
  return response.data;
};

// Enneagram Chat API
export const sendEnneagramChat = async (data: {
  user_id: string;
  message: string;
  context: {
    inferred_core: number;
    inferred_wing: number | string;
    confidence_tier: string;
    is_close?: boolean;
    top_candidates?: { type: number; probability: number }[];
    energy_state: string;
    active_card_context: string;
  };
}) => {
  const response = await api.post('/enneagram/chat', data);
  return response.data;
};

// Enneagram Feedback API
export const submitEnneagramFeedback = async (data: {
  user_id: string;
  accuracy_feedback: 'yes' | 'mostly' | 'no';
  timestamp: string;
  inferred_core: number;
  inferred_wing: number | string;
  confidence: number;
  energy_state?: string;
  life_context?: string;
  answer_frame?: string;
}) => {
  const response = await api.post('/profile/enneagram/feedback', data);
  return response.data;
};

export default api;