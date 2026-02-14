import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// ============================================
// CANONICAL API BASE URL RESOLUTION - HARDENED
// ============================================
// STRICT: API base URL must NEVER be relative
// Must start with http:// or https://
// NO FALLBACKS to relative paths like "/api"

// Track if URL is missing for UI display
export let API_URL_MISSING = false;
export let API_URL_ERROR_MESSAGE = '';

const validateAbsoluteUrl = (url: string): boolean => {
  return url.startsWith('http://') || url.startsWith('https://');
};

export const getApiBaseUrl = (): string => {
  // Priority 1: Explicit EXPO_PUBLIC_API_BASE_URL (MUST be absolute)
  const explicitApiUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (explicitApiUrl && typeof explicitApiUrl === 'string' && explicitApiUrl.length > 0) {
    if (validateAbsoluteUrl(explicitApiUrl)) {
      console.log('[API] ✅ Using EXPO_PUBLIC_API_BASE_URL:', explicitApiUrl);
      return explicitApiUrl;
    } else {
      console.error('[API] ❌ EXPO_PUBLIC_API_BASE_URL is not absolute:', explicitApiUrl);
    }
  }
  
  // Priority 2: EXPO_PUBLIC_BACKEND_URL + /api (MUST be absolute)
  const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (backendUrl && typeof backendUrl === 'string' && backendUrl.length > 0) {
    if (validateAbsoluteUrl(backendUrl)) {
      const withApi = `${backendUrl}/api`;
      console.log('[API] ✅ Using EXPO_PUBLIC_BACKEND_URL + /api:', withApi);
      return withApi;
    } else {
      console.error('[API] ❌ EXPO_PUBLIC_BACKEND_URL is not absolute:', backendUrl);
    }
  }
  
  // Priority 3: expo-constants extra config
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_API_BASE_URL;
  if (extraUrl && typeof extraUrl === 'string' && extraUrl.length > 0) {
    if (validateAbsoluteUrl(extraUrl)) {
      console.log('[API] ✅ Using Constants extra:', extraUrl);
      return extraUrl;
    }
  }
  
  // Priority 4: LOCAL DEVELOPMENT ONLY - localhost
  if (__DEV__) {
    const localhost = 'http://localhost:8001/api';
    console.log('[API] ⚠️ DEV MODE: Falling back to localhost:', localhost);
    return localhost;
  }
  
  // ❌ FAIL LOUDLY - NO RELATIVE PATHS EVER
  API_URL_MISSING = true;
  API_URL_ERROR_MESSAGE = 'API_BASE_URL_MISSING: No absolute URL configured';
  console.error('[API] ❌❌❌ FATAL: API BASE URL MISSING ❌❌❌');
  console.error('[API] Set EXPO_PUBLIC_API_BASE_URL in .env');
  
  // Return error marker (will fail all requests explicitly)
  return 'ERROR://API_BASE_URL_MISSING';
};

// Resolved once at module load
export const API_BASE_URL = getApiBaseUrl();

// Validate the resolved URL
if (!validateAbsoluteUrl(API_BASE_URL)) {
  API_URL_MISSING = true;
  API_URL_ERROR_MESSAGE = `Invalid API URL: ${API_BASE_URL}`;
}

// Debug log for troubleshooting
console.log('[API] ══════════════════════════════════');
console.log('[API] Resolved API_BASE_URL:', API_BASE_URL);
console.log('[API] URL Valid:', validateAbsoluteUrl(API_BASE_URL));
console.log('[API] Platform:', Platform.OS);
console.log('[API] ══════════════════════════════════');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 min for slow LLM responses
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
  inferred_wing: number | string | null;
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
    wing_scores: { 
      left: number; 
      right: number; 
      diff: number;
      // Enhanced debug fields
      left_type?: number;
      right_type?: number;
      has_wing_data?: boolean;
    };
    // Extended debug data (v2 - optional)
    mean_likert?: { [key: string]: number };
    forced_hits?: { [key: string]: number };
    probabilities?: { [key: string]: number };
    wing_access?: {
      left_type: number;
      right_type: number;
      left_accessible: boolean;
      right_accessible: boolean;
      dominant_wing: number | string | null;
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

// ============================================
// P1: DEEP ENNEAGRAM ASSESSMENT API
// ============================================

// Types for deep assessment
export interface DeepAssessmentQuestion {
  id: string;
  type: 'forced_choice' | 'likert' | 'ranked';
  section: number;
  stem: string;
  options?: Array<{
    id: string;
    text: string;
    primary_type: number;
    secondary_type?: number | null;
    weight?: number;
    weight_multipliers?: Record<string, number>;
  }>;
  scale?: {
    min: number;
    max: number;
    labels?: string[];
  };
  scoring?: {
    primary_type: number;
    secondary_type?: number | null;
    direction: 'positive' | 'negative';
    weight: number;
  };
  pair_focus?: number[];
  dimension?: string;
}

export interface DeepAssessmentSection {
  id: number;
  title: string;
  question_count: number;
}

export interface DeepAssessmentResponse {
  type: 'forced_choice' | 'likert' | 'ranked';
  value: string | number | string[];
}

export interface DeepAssessmentSession {
  session_id: string;
  user_id?: string;
  question_set_id: string;
  status: 'in_progress' | 'completed' | 'abandoned';
  current_index: number;
  total_questions: number;
  questions: DeepAssessmentQuestion[];
  sections: DeepAssessmentSection[];
  responses: Array<{
    question_id: string;
    response: DeepAssessmentResponse;
    answered_at: string;
  }>;
  result?: DeepAssessmentResult;
  resumed?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DeepAssessmentResult {
  type_probabilities: Record<string, number>;
  top_types: Array<{ type: number; probability: number }>;
  confidence_tier: 'low' | 'moderate' | 'high';
  assessment_depth: 'deep';
  wing_analysis: {
    wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
    inferred_wing: number | null;
    adjacent_scores: {
      left: number;
      right: number;
      left_type?: number;
      right_type?: number;
    };
  };
  scoring_metadata?: {
    questions_total: number;
    questions_answered: number;
    completeness: number;
    raw_scores?: Record<string, number>;
  };
  completed_at: string;
}

// Start a new deep assessment session
export const startDeepAssessment = async (userId: string): Promise<DeepAssessmentSession> => {
  const response = await apiWithRetry.post(`/enneagram/deep/start/${userId}`);
  return response.data;
};

// Get existing session state
export const getDeepAssessmentSession = async (sessionId: string): Promise<DeepAssessmentSession> => {
  const response = await apiWithRetry.get(`/enneagram/deep/session/${sessionId}`);
  return response.data;
};

// Submit an answer
export const submitDeepAssessmentAnswer = async (
  sessionId: string,
  questionId: string,
  response: DeepAssessmentResponse
): Promise<{
  success: boolean;
  session_id: string;
  question_id: string;
  current_index: number;
  total_answered: number;
  total_questions: number;
}> => {
  const result = await apiWithRetry.post(`/enneagram/deep/answer/${sessionId}`, {
    question_id: questionId,
    response
  });
  return result.data;
};

// Complete the assessment and get results
export const completeDeepAssessment = async (sessionId: string): Promise<{
  success: boolean;
  already_completed: boolean;
  result: DeepAssessmentResult;
}> => {
  const response = await apiWithRetry.post(`/enneagram/deep/complete/${sessionId}`);
  return response.data;
};

// Enneagram Chat API
export const sendEnneagramChat = async (data: {
  user_id: string;
  message: string;
  context: {
    inferred_core: number;
    inferred_wing: number | string | null;
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
  inferred_wing: number | string | null;
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

// Enneagram Deep Dive API
export interface EnneagramDeepDiveSection {
  label: string;
  body: string;
}

export interface EnneagramDeepDiveResponse {
  success: boolean;
  title: string;
  type: number;
  wing: number | null;
  type_label: string;
  type_name: string;
  confidence: number;
  confidence_tier: string;
  sections: EnneagramDeepDiveSection[];
  mirror_prompt: string;
  computed_details?: EnneagramComputedDetails;
  error?: string;
  message?: string;
  debug_stamp?: {
    assessment_version: string;
    convergence_applied: boolean;
    supported_types: number[];
    top_candidates: { type: number; probability: number }[];
  };
}

export const getEnneagramDeepDive = async (userId: string): Promise<EnneagramDeepDiveResponse> => {
  const response = await apiWithRetry.get(`/enneagram/deep-dive/${userId}`);
  return response.data;
};

// Enneagram Narrative Engine Types
export interface EnneagramNarrativeSection {
  id: string;
  label: string;
  body: string;
}

export interface EnneagramNarrativeResponse {
  success: boolean;
  type: number;
  wing: number | null;
  type_label: string;
  type_name: string;
  confidence_tier: string;
  instinct_stacking: string | null;
  sections: EnneagramNarrativeSection[];
  generated_at: string;
  version: string;
  error?: string;
  message?: string;
}

/**
 * Get Enneagram narrative content (layered reflective stories)
 * This is the new Narrative Engine output for the Deep Dive lens
 */
export const getEnneagramNarrative = async (
  userId: string, 
  forceRefresh: boolean = false
): Promise<EnneagramNarrativeResponse> => {
  const params = forceRefresh ? { force_refresh: 'true' } : {};
  const response = await apiWithRetry.get(`/enneagram/narrative/${userId}`, { params });
  return response.data;
};

// Life Context APIs
export interface LifeContextSection {
  label: string;
  body: string;
}

export interface LifeContextResponse {
  context: string;
  title: string;
  sections: LifeContextSection[];
  generated_at: string;
  source_lenses: string[];
}

export type LifeContextType = 'relationships' | 'work' | 'self';

export const getLifeContext = async (
  userId: string,
  context: LifeContextType
): Promise<LifeContextResponse> => {
  const response = await apiWithRetry.get(`/life/${context}`, {
    params: { user_id: userId }
  });
  return response.data;
};

export const getAllLifeContexts = async (userId: string): Promise<{
  user_id: string;
  contexts: {
    relationships: LifeContextResponse | null;
    work: LifeContextResponse | null;
    self: LifeContextResponse | null;
  };
  generated_at: string;
}> => {
  const response = await apiWithRetry.get('/life/contexts/all', {
    params: { user_id: userId }
  });
  return response.data;
};

// ============================================
// P2 ENNEAGRAM DEEP ASSESSMENT (Single-Sitting)
// ============================================
// A 20-30 minute reflective assessment using the new
// multi-stage adaptive question flow (center → core → diff → wing → instinct → consistency)

export interface P2AssessmentQuestion {
  id: string;
  prompt: string;
  format: 'likert' | 'forced';
  options?: {
    A?: string;
    B?: string;
    C?: string;
    allow_both?: boolean;
    allow_neither?: boolean;
  };
}

export interface P2AssessmentProgress {
  stage: 'center' | 'core' | 'diff' | 'wing' | 'instinct' | 'consistency' | 'done';
  questions_answered: number;
  estimated_total: number;
  estimated_remaining: number;
  estimated_minutes_remaining: number;
}

export interface P2AssessmentStartResponse {
  session_id: string;
  question: P2AssessmentQuestion | null;
  progress: P2AssessmentProgress;
}

export interface P2AssessmentAnswer {
  type: 'likert' | 'forced';
  value: number | string;  // 1-5 for likert, "A"|"B"|"C"|"both"|"neither" for forced
}

export interface P2AssessmentResult {
  core_type: number;
  wing: string;
  instinct_primary: string;
  instinct_secondary: string | null;
  confidence: number;
  confidence_tier: 'high' | 'moderate' | 'exploratory';
  assessment_depth: string;
  reliability: 'stable' | 'mixed' | 'low';
  created_at_iso: string;
  _debug?: {
    type_scores: Record<number, number>;
    center_scores: Record<string, number>;
    wing_scores: Record<string, number>;
    instinct_scores: Record<string, number>;
    consistency_score: number;
    coherence_score: number;
    type_gap: number;
    questions_asked: number;
    neither_count: number;
  };
}

export interface P2AssessmentAnswerResponse {
  session_id: string;
  question?: P2AssessmentQuestion;
  progress?: P2AssessmentProgress;
  results?: P2AssessmentResult;
}

export interface P2AssessmentStatusResponse {
  session_id: string;
  user_id: string;
  stage: string;
  progress: P2AssessmentProgress;
  created_at_iso: string;
  updated_at_iso: string;
}

/**
 * Start a new P2 deep assessment session
 */
export const startP2DeepAssessment = async (userId: string): Promise<P2AssessmentStartResponse> => {
  const response = await apiWithRetry.post('/enneagram/deep-assessment/start', {
    user_id: userId
  });
  return response.data;
};

/**
 * Submit an answer to the current P2 assessment question
 */
export const submitP2AssessmentAnswer = async (
  userId: string,
  sessionId: string,
  questionId: string,
  answer: P2AssessmentAnswer
): Promise<P2AssessmentAnswerResponse> => {
  const response = await apiWithRetry.post('/enneagram/deep-assessment/answer', {
    user_id: userId,
    session_id: sessionId,
    question_id: questionId,
    answer: answer
  });
  return response.data;
};

/**
 * Get the status of a P2 assessment session
 */
export const getP2AssessmentStatus = async (sessionId: string): Promise<P2AssessmentStatusResponse> => {
  const response = await apiWithRetry.get(`/enneagram/deep-assessment/status/${sessionId}`);
  return response.data;
};

// Export both the raw api instance and the retry-wrapped version
export { apiWithRetry };
export default api;