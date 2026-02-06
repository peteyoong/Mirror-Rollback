import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Resolve API base URL with proper fallback chain for Expo
const getApiBaseUrl = (): string => {
  // 1. For web preview, ALWAYS use relative URL (same origin)
  // This is the most reliable approach as it avoids DNS/hostname issues
  // The ingress will route /api/* to the backend
  if (Platform.OS === 'web') {
    return '';
  }
  
  // 2. Try expo-constants extra config (for native builds)
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (extraUrl && typeof extraUrl === 'string' && extraUrl.length > 0) {
    return extraUrl;
  }
  
  // 3. Try process.env (works in Expo with EXPO_PUBLIC_ prefix)
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    return envUrl;
  }
  
  // 4. Fallback for native development
  return 'http://localhost:8001';
};

const API_BASE_URL = getApiBaseUrl();

// Debug log for troubleshooting (only in dev)
if (__DEV__) {
  console.log('[API] Base URL resolved to:', API_BASE_URL || '(relative - web)');
  console.log('[API] Platform:', Platform.OS);
}

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 120000, // Increased timeout (2 min) to handle slow LLM responses and prevent mid-assessment timeouts
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================
// RETRY LOGIC FOR NETWORK RESILIENCE
// ============================================
// Handles transient failures: DNS issues, connection drops, tunnel restarts

interface RetryConfig {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  retryCondition?: (error: AxiosError) => boolean;
}

const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
  retryCondition: (error: AxiosError) => {
    // Retry on network errors (no response received)
    if (!error.response) {
      // This includes: ENOTFOUND (hostname not found), ETIMEDOUT, ECONNREFUSED, etc.
      return true;
    }
    // Retry on 5xx server errors (temporary issues)
    if (error.response.status >= 500) {
      return true;
    }
    // Don't retry on 4xx client errors
    return false;
  },
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function requestWithRetry<T>(
  requestFn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, retryCondition } = {
    ...DEFAULT_RETRY_CONFIG,
    ...config,
  };

  let lastError: AxiosError | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      const axiosError = error as AxiosError;
      lastError = axiosError;

      // Check if we should retry
      const shouldRetry = attempt < maxRetries && retryCondition(axiosError);

      if (__DEV__) {
        console.log(
          `[API] Request failed (attempt ${attempt + 1}/${maxRetries + 1}):`,
          axiosError.message,
          shouldRetry ? '- will retry' : '- giving up'
        );
      }

      if (!shouldRetry) {
        throw error;
      }

      // Exponential backoff with jitter
      const delay = Math.min(
        baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        maxDelayMs
      );

      if (__DEV__) {
        console.log(`[API] Retrying in ${Math.round(delay)}ms...`);
      }

      await sleep(delay);
    }
  }

  throw lastError;
}

// Wrap axios instance methods with retry logic
const apiWithRetry = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    requestWithRetry(() => api.get<T>(url, config)),
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    requestWithRetry(() => api.post<T>(url, data, config)),
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    requestWithRetry(() => api.put<T>(url, data, config)),
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    requestWithRetry(() => api.delete<T>(url, config)),
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    requestWithRetry(() => api.patch<T>(url, data, config)),
};

// Daily Focus API (Context Selector Layer)
export interface DailyFocusResponse {
  ambient_line: string;
  context: string | null;
  confidence: number;
  generated_at_iso: string;
}

export const getDailyFocus = async (userId: string): Promise<DailyFocusResponse> => {
  const response = await apiWithRetry.get(`/daily-focus/${userId}`);
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
  const response = await apiWithRetry.post('/users', data);
  return response.data;
};

export const getUser = async (userId: string) => {
  const response = await apiWithRetry.get(`/users/${userId}`);
  return response.data;
};

// Login API - for existing users
export const loginUser = async (email: string) => {
  const response = await apiWithRetry.post('/users/login', { email });
  return response.data;
};

// Location APIs
export const searchLocations = async (query: string) => {
  const response = await apiWithRetry.post('/locations/search', { query });
  return response.data.results;
};

// Chart APIs
export const calculateChart = async (userId: string) => {
  const response = await apiWithRetry.post('/charts/calculate', { user_id: userId });
  return response.data;
};

export const getChart = async (userId: string) => {
  const response = await apiWithRetry.get(`/charts/${userId}`);
  return response.data;
};

// Journal APIs
export const createJournalEntry = async (userId: string, content: string) => {
  const response = await apiWithRetry.post('/journal', {
    user_id: userId,
    content,
  });
  return response.data;
};

export const getJournalEntries = async (userId: string) => {
  const response = await apiWithRetry.get(`/journal/${userId}`);
  return response.data;
};

// Reflection APIs
export const getDailyReflection = async (userId: string) => {
  const response = await apiWithRetry.post('/reflections/daily', { user_id: userId });
  return response.data;
};

// Chat APIs
export const sendChatMessage = async (userId: string, message: string) => {
  const response = await apiWithRetry.post('/chat', {
    user_id: userId,
    message,
  });
  return response.data;
};

// Lenses APIs
export const getLenses = async () => {
  const response = await apiWithRetry.get('/lenses');
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
    // Extended debug data (v2 - optional)
    mean_likert?: { [key: string]: number };
    forced_hits?: { [key: string]: number };
    probabilities?: { [key: string]: number };
    wing_access?: {
      left_type: number;
      right_type: number;
      left_accessible: boolean;
      right_accessible: boolean;
      dominant_wing: number | string;
    };
  };
}) => {
  const response = await apiWithRetry.post('/enneagram/results', data);
  return response.data;
};

export const getEnneagramResult = async (userId: string) => {
  const response = await apiWithRetry.get(`/enneagram/results/${userId}`);
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
  const response = await apiWithRetry.post('/enneagram/chat', data);
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
  const response = await apiWithRetry.post('/profile/enneagram/feedback', data);
  return response.data;
};

// Enneagram Q&A API (Knowledge Base)
export interface EnneagramAskResponse {
  answer: string;
  citations: Array<{
    pdf: string;
    page: number;
    chunk_id: string;
    score: number;
  }>;
  kb_status: {
    ready: boolean;
    chunks_available: number;
  };
  debug?: {
    used_chunks: Array<{
      text: string;
      score: number;
      meta: {
        pdf_page: number;
        chunk_id: string;
      };
    }>;
  };
}

export const askEnneagramQuestion = async (
  userId: string | null,
  question: string
): Promise<EnneagramAskResponse> => {
  const response = await apiWithRetry.post('/enneagram/ask', {
    user_id: userId,
    question,
  });
  return response.data;
};

export const getEnneagramKbStatus = async () => {
  const response = await apiWithRetry.get('/enneagram/kb-status');
  return response.data;
};

// Enneagram Trait Cards
export interface EnneagramTraitCard {
  card_id: string;
  title: string;
  body: string;
  citation?: {
    source: string;
    page?: number;
  };
  suggested_question?: string;
}

export interface EnneagramComputedDetails {
  center?: string;
  hornevian_group?: string;
  harmonic_group?: string;
  object_relations?: string;
  stress_line_to?: number;
  growth_line_to?: number;
  wing_left_type?: number;
  wing_right_type?: number;
  wing_balance_label?: string;
  wing_openness_hint?: string;
  social_style_tags?: string[];
}

export interface EnneagramTraitsResponse {
  cards: EnneagramTraitCard[];
  source: 'book' | 'static' | 'none';
  computed_details?: EnneagramComputedDetails;
  type?: number;
  wing?: number | 'balanced';
  message?: string;
}

export const getEnneagramTraits = async (userId: string): Promise<EnneagramTraitsResponse> => {
  const response = await apiWithRetry.get(`/enneagram/traits/${userId}`);
  return response.data;
};

// Export both the raw api instance and the retry-wrapped version
export { apiWithRetry };
export default api;