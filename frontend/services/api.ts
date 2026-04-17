import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Resolve API base URL with proper fallback chain for Expo
const getApiBaseUrl = (): string => {
  // For web, determine the best URL based on hostname
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      
      // If on preview domain, use relative URLs (ingress will proxy)
      if (hostname.includes('preview.emergentagent.com') || hostname.includes('.emergent.host')) {
        return '';  // Use relative URLs
      }
      
      // If localhost, use direct backend URL
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8001';
      }
    }
    // Fallback for web
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
// SESSION RESTORE ERROR TYPES
// ============================================
export interface SessionRestoreError {
  code: 'invalid_user_id' | 'user_not_found' | 'chart_not_found' | 'server_error' | 'network_error';
  message: string;
  recovery_action: 'clear_session' | 'start_onboarding' | 'retry';
}

/**
 * Parse API error response into structured SessionRestoreError
 */
export function parseSessionRestoreError(error: AxiosError): SessionRestoreError {
  const response = error.response;
  
  // Network error - no response
  if (!response) {
    return {
      code: 'network_error',
      message: 'Unable to connect. Please check your connection.',
      recovery_action: 'retry'
    };
  }
  
  // Try to parse structured error from backend
  const data = response.data as Record<string, any> | undefined;
  const detail = data?.detail;
  if (detail && typeof detail === 'object' && detail.code) {
    return {
      code: detail.code,
      message: detail.message || 'An error occurred',
      recovery_action: detail.recovery_action || 'retry'
    };
  }
  
  // Fallback based on status code
  if (response.status === 400) {
    return {
      code: 'invalid_user_id',
      message: 'Invalid session. Please start fresh.',
      recovery_action: 'clear_session'
    };
  }
  
  if (response.status === 404) {
    return {
      code: 'user_not_found',
      message: 'Profile not found. Please complete setup.',
      recovery_action: 'start_onboarding'
    };
  }
  
  return {
    code: 'server_error',
    message: data?.detail || 'An unexpected error occurred',
    recovery_action: 'retry'
  };
}

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

// Daily Pattern Signal API (Task 43)
export interface DailyPatternSignalResponse {
  success: boolean;
  signal_title: string;
  insight_text: string;
  past_reflection: string | null;
  reflective_question: string;
  pattern_type: string | null; // "arc", "cycle", "phase", or null
  pattern_name: string | null;
  confidence: number;
  generated_at: string;
}

export const getDailyPatternSignal = async (userId: string): Promise<DailyPatternSignalResponse> => {
  const response = await apiWithRetry.get(`/daily-pattern-signal/${userId}`);
  return response.data;
};

// User APIs
export const createUser = async (data: {
  name?: string;
  email?: string;
  gender?: string;
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
  // Use GET /account/login to bypass CDN POST caching issues on deploy domain
  const response = await apiWithRetry.get('/account/login', { params: { email, _t: Date.now().toString() } });
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
// Pattern and source metadata for journal entries
export interface PatternJournalMetadata {
  journal_source?: string;  // 'pattern_pulse' | 'pattern_graph' | 'patterns' | 'mirror' etc.
  pattern_category?: string;
  pattern_tension_pair?: string;
  prompt_text?: string;
  // Source metadata for reflection tracking
  source_lens?: string;
  source_domain?: string;
  source_name?: string;
  source_value?: string;
  // Timeline phase metadata (for Journal ↔ Timeline connection)
  phase_id?: string;  // e.g., "q1", "q2", "q3", "q4"
  phase_name?: string;  // e.g., "Recognition", "Confrontation", "The Crossroads", "Integration"
}

// Journal entry response with phase data
export interface JournalEntryResponseWithPhase {
  id: string;
  content: string;
  themes: string[];
  created_at: string;
  phase_id?: string;
  phase_name?: string;
}

export const createJournalEntry = async (
  userId: string, 
  content: string,
  metadata?: PatternJournalMetadata
): Promise<JournalEntryResponseWithPhase> => {
  const response = await apiWithRetry.post('/journal', {
    user_id: userId,
    content,
    ...metadata
  });
  return response.data;
};

export const getJournalEntries = async (userId: string): Promise<JournalEntryResponseWithPhase[]> => {
  const response = await apiWithRetry.get(`/journal/${userId}`);
  return response.data;
};

export const getJournalEntriesByPhase = async (
  userId: string, 
  phaseId: string, 
  limit: number = 3
): Promise<JournalEntryResponseWithPhase[]> => {
  const response = await apiWithRetry.get(`/journal/${userId}/by-phase/${phaseId}`, {
    params: { limit }
  });
  return response.data;
};

// Pattern Detection Layer V2/V2.5/V2.6/V2.7/V3/V3.1 - Journal pattern analysis
export interface JournalPatternAnalysis {
  user_id: string;
  total_entries: number;
  phase_distribution: Record<string, number>;
  phase_distribution_14d: Record<string, number>;
  repeating_phases: string[];
  phase_patterns: Record<string, string[]>;
  compressed_pattern_lines: Record<string, string>;  // V2.5: Emotional tension compression
  phase_tensions: Record<string, string>;
  identity_tendency: string | null;
  identity_threshold_met: boolean;
  identity_echo: string | null;  // V2.6: Identity echo for prominent display
  angle_line: string | null;  // V2.7: Transit-based contextual modifier
  angle_role: string | null;  // V2.7: "amplifier" - enforces modifier role
  // V3: Facet Selection Engine
  selected_facet: {
    name: string;
    label: string;
    score: number;
    reason: string;
  } | null;
  facet_line: string | null;  // "This may be showing up most through..."
  // V3.1: Facet Memory + Progression Layer
  facet_memory: {
    recent_facets: string[];
    dominant_facet_last_5: string;
    is_repeating: boolean;
    streak_count: number;
    last_facet: string;
    first_seen_recently: boolean;
    total_entries: number;
  } | null;
  facet_memory_line: string | null;  // "This has been showing up more than once..."
  // V3.2: Facet Progression Engine - movement over time
  facet_progression: {
    state: 'escalating' | 'deepening' | 'shifting' | 'resolving' | 'stable';
    confidence: number;
    previous_facet: string;
    current_facet: string;
  } | null;
  facet_progression_line: string | null;  // "This seems to be becoming harder to ignore."
}

export const getJournalPatterns = async (userId: string): Promise<JournalPatternAnalysis> => {
  const response = await apiWithRetry.get(`/journal/${userId}/patterns`);
  return response.data;
};

export const updateJournalEntry = async (entryId: string, content: string) => {
  const response = await apiWithRetry.put(`/journal/${entryId}`, { content });
  return response.data;
};

export const deleteJournalEntry = async (entryId: string) => {
  const response = await apiWithRetry.delete(`/journal/${entryId}`);
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

// Pattern Drift API
export interface PatternDriftResponse {
  baseline_type: number | null;
  baseline_name: string | null;
  drift_detected: boolean;
  drift_candidate: number | null;
  drift_candidate_name: string | null;
  direction: 'stress' | 'growth' | null;
  confidence_label: 'low' | 'emerging' | 'moderate';
  confidence_score: number;
  signal_keywords: string[];
  signal_sources: string[];
  signals_detected: number;
  window_days: number;
  summary: string | null;
  calculated_at: string;
  error?: string;
}

export const getPatternDrift = async (userId: string): Promise<PatternDriftResponse> => {
  const response = await apiWithRetry.get(`/insights/pattern-drift/${userId}`);
  return response.data;
};

// Pattern Graph API - Get live pattern signals
export interface PatternGraphCategory {
  category_id: string;
  category_name: string;
  description: string;
  signal_strength: 'quiet' | 'emerging' | 'active' | 'stable' | 'recurring';
  summary: string;
  signals: any[];
}

export interface PatternGraphResponse {
  success: boolean;
  user_id: string;
  categories: PatternGraphCategory[];
  total_signals: number;
  generated_at: string;
  from_cache: boolean;
}

export const getPatternGraph = async (userId: string): Promise<PatternGraphResponse> => {
  const response = await apiWithRetry.get(`/pattern-graph/${userId}`);
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
  keystone_explanation?: {
    keystone_pattern_id: string;
    keystone_label: string;
    keystone_sequence: string[];
    lens_role: string;
    lens_explanation_title: string;
    lens_explanation_body: string;
    supports_keystone: boolean;
  } | null;
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

// Export both the raw api instance and the retry-wrapped version
export { apiWithRetry };

// =============================================================================
// MIRROR INSIGHT API
// =============================================================================

export interface MirrorInsight {
  id: string;
  type: 'mirror_insight';
  summary: string;
  domains: string[];
  tags: string[];
  confidence: number;
  created_at: string;
}

export interface CreateMirrorInsightPayload {
  user_id: string;
  summary: string;
  domains?: string[];
  tags?: string[];
  confidence?: number;
}

export const createMirrorInsight = async (
  payload: CreateMirrorInsightPayload
): Promise<MirrorInsight> => {
  const response = await apiWithRetry.post('/mirror/insight', payload);
  return response.data;
};

export const getMirrorInsights = async (
  userId: string,
  limit: number = 20
): Promise<MirrorInsight[]> => {
  const response = await apiWithRetry.get(`/mirror/insights/${userId}`, {
    params: { limit }
  });
  return response.data;
};

// Combined Timeline (Journal + Mirror Insights)
export interface TimelineItem {
  id: string;
  type: 'journal_entry' | 'mirror_insight';
  // For journal_entry
  content?: string;
  themes?: string[];
  // For mirror_insight
  summary?: string;
  domains?: string[];
  tags?: string[];
  confidence?: number;
  // Common
  created_at: string;
}

export interface CombinedTimelineResponse {
  items: TimelineItem[];
  total: number;
}

export const getCombinedTimeline = async (
  userId: string,
  limit: number = 50
): Promise<CombinedTimelineResponse> => {
  const response = await apiWithRetry.get(`/timeline/combined/${userId}`, {
    params: { limit }
  });
  return response.data;
};

// =============================================================================
// FORUMS API
// =============================================================================

export interface Forum {
  id: string;
  name: string;
  description: string | null;
  invite_token: string;
  created_by: string;
  member_count: number;
  created_at: string;
}

export interface ForumExercise {
  id: string;
  slug: string;
  title: string;
  description: string;
  prompts: string[];
}

export interface PatternDomain {
  id: string;
  name: string;
}

export interface ForumReflection {
  id: string;
  forum_id: string;
  exercise_id: string;
  user_id: string;
  user_name: string;
  selected_domain: string;
  domain_name: string;
  reflection_text: string;
  is_shared: boolean;
  created_at: string;
}

export interface ForumMember {
  user_id: string;
  user_name: string;
  role: string;
  joined_at: string;
}

// Create a new forum
export const createForum = async (data: {
  name: string;
  description?: string;
  user_id: string;
}): Promise<Forum> => {
  const response = await apiWithRetry.post('/forums', data);
  return response.data;
};

// Get user's forums
export const getUserForums = async (userId: string): Promise<{ forums: Forum[] }> => {
  // Use POST to bypass CDN caching of GET requests on deployed domain
  const response = await apiWithRetry.post(`/get-user-forums?_cb=${Date.now()}`, { user_id: userId });
  return response.data;
};

// Get forum by ID
export const getForum = async (forumId: string, userId: string): Promise<Forum & { active_exercise: ForumExercise | null }> => {
  const response = await apiWithRetry.get(`/forums/${forumId}`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Get forum by invite token (for preview)
export const getForumByInvite = async (inviteToken: string): Promise<{
  id: string;
  name: string;
  description: string | null;
  member_count: number;
  created_at: string;
}> => {
  const response = await apiWithRetry.get(`/forums/invite/${inviteToken}`);
  return response.data;
};

// Join forum via invite token
export const joinForum = async (inviteToken: string, userId: string): Promise<{
  message: string;
  forum_id: string;
  already_member: boolean;
}> => {
  const response = await apiWithRetry.post(`/forums/join/${inviteToken}`, { user_id: userId });
  return response.data;
};

// Get active exercise for a forum
export const getForumExercise = async (forumId: string, userId: string): Promise<{
  exercise: ForumExercise | null;
  domains: PatternDomain[];
  has_submitted: boolean;
  user_reflection_id: string | null;
}> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/exercise`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Submit a reflection
export const submitForumReflection = async (
  forumId: string,
  data: {
    user_id: string;
    selected_domain: string;
    reflection_text: string;
    is_shared: boolean;
  }
): Promise<{
  id: string;
  forum_id: string;
  exercise_id: string;
  selected_domain: string;
  domain_name: string;
  is_shared: boolean;
  created_at: string;
}> => {
  const response = await apiWithRetry.post(`/forums/${forumId}/reflections`, data);
  return response.data;
};

// Get shared reflections
export const getSharedReflections = async (forumId: string, userId: string): Promise<{
  reflections: ForumReflection[];
  exercise: { id: string; title: string } | null;
}> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/reflections/shared`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Get forum members
export const getForumMembers = async (forumId: string, userId: string): Promise<{
  members: ForumMember[];
}> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/members`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Get pattern domains list
export const getPatternDomains = async (): Promise<{ domains: PatternDomain[] }> => {
  const response = await apiWithRetry.get('/forums/domains/list');
  return response.data;
};

// Get Human Design mechanics for reflection source
export interface HumanDesignMechanics {
  core_mechanics: {
    type: string;
    strategy: string;
    authority: string;
    profile: string;
    definition: string;
    incarnation_cross: string;
    incarnation_cross_gates: string;
  };
}

export const getHumanDesignMechanics = async (userId: string): Promise<HumanDesignMechanics> => {
  const response = await apiWithRetry.get(`/human-design/mechanics/${userId}`);
  return response.data;
};

// ============================================
// PATTERN INTERPRETATION
// ============================================

export interface PatternInterpretation {
  story: string;
  pattern: string;
  challenge: string;
  genius: string;
  experiments: string[];
}

export interface PatternInterpretationResponse {
  success: boolean;
  domain_id: string;
  domain_name: string;
  signal_strength: string;
  interpretation: PatternInterpretation;
  from_cache: boolean;
  created_at: string;
  error?: string;
}

// Get or generate pattern interpretation for a domain
export const getPatternInterpretation = async (
  userId: string,
  domainId: string
): Promise<PatternInterpretationResponse> => {
  const response = await apiWithRetry.get(`/pattern-interpretation/${userId}/${domainId}`);
  return response.data;
};

// ============================================
// FORUM PULSE
// ============================================

export interface ForumPulseMemberCard {
  user_id: string;
  name: string;
  hd_type: string | null;
  hd_profile: string | null;
  hd_authority: string | null;
  enneagram_type: number | null;
  active_pattern: string | null;
}

// Extended Forum Member Lens Data (full lens profile)
export interface ForumMemberLensData {
  user_id: string;
  name: string | null;
  human_design: {
    type: string | null;
    strategy: string | null;
    authority: string | null;
    profile: string | null;
    definition: string | null;
    incarnation_cross: string | null;
    centers_defined: string[];
    centers_undefined: string[];
    active_gates: number[];
    active_channels: string[];  // Formatted as "35-36", "37-40" etc.
  };
  enneagram: {
    core_type: number | null;
    wing: number | null;
    center: string | null;
    hornevian_group: string | null;
    harmonic_group: string | null;
    growth_direction: number | null;
    stress_direction: number | null;
  };
  astrology: {
    sun: string | null;
    moon: string | null;
    rising: string | null;
    dominant_element: string | null;
    dominant_modality: string | null;
  };
  numerology: {
    life_path: number | { number: number; description: string } | null;
    expression: number | { number: number; description: string } | null;
    soul_urge: number | { number: number; description: string } | null;
    personality: number | { number: number; description: string } | null;
  };
  patterns: {
    active_domains: string[];
    recurring_domains: string[];
  };
}

// Forum Dynamics Context for AI interpretation
export interface ForumDynamicsContext {
  forum_members: ForumMemberLensData[];
  member_count: number;
  hd_type_distribution: Record<string, number>;
  hd_authority_distribution: Record<string, number>;
  hd_profile_distribution: Record<string, number>;
  enneagram_distribution: Record<number, number>;
  astrology_elements: Record<string, number>;
  astrology_modalities: Record<string, number>;
  numerology_life_paths: Record<number, number>;
  active_pattern_domains: { domain: string; count: number }[];
  defined_centers_coverage: Record<string, number>;
  undefined_centers_coverage: Record<string, number>;
}

export interface ForumPulseTheme {
  domain_id: string;
  domain_name: string;
  count: number;
}

export interface ForumPulseResponse {
  success: boolean;
  exploring_themes: ForumPulseTheme[];
  activity_summary: {
    reflections_7d: number;
    active_members_7d: number;
    total_members: number;
    most_active_domain: string | null;
  };
  group_energy: Record<string, number>;
  lens_insight: string | null;
  member_cards: ForumPulseMemberCard[];
}

export const getForumPulse = async (forumId: string, userId: string): Promise<ForumPulseResponse> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/pulse`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Get detailed lens data for a specific forum member
export const getForumMemberLens = async (
  forumId: string,
  memberUserId: string,
  userId: string
): Promise<{ success: boolean; lens_data: ForumMemberLensData }> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/member-lens/${memberUserId}`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Get forum dynamics context (for future Forum Chat integration)
export const getForumDynamicsContext = async (
  forumId: string,
  userId: string
): Promise<{ success: boolean; context: ForumDynamicsContext }> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/dynamics-context`, {
    params: { user_id: userId }
  });
  return response.data;
};

// =====================================================
// FORUM LIVE FIELD - Real-time field dynamics reading
// =====================================================

export interface ForumLiveFieldResponse {
  success: boolean;
  forum_id: string;
  generated_at: string;
  
  // Core field reading
  field_reading: string;
  what_hasnt_landed: string | null;
  what_room_needs: string | null;
  your_shift: string | null;
  
  // Your position in the field
  your_position: string | null;
  your_position_type: 'initiating' | 'holding_back' | 'bridging' | 'observing' | 'withdrawing';
  
  // Trajectory (if nothing changes)
  trajectory: string | null;
  trajectory_type: 'disengagement' | 'tension_building' | 'misalignment' | 'stagnation' | 'fragmentation' | 'stabilizing' | 'unclear';
  trajectory_severity: 'low' | 'moderate' | 'positive';
  
  // THE MOVE (subtle action opening) - only when confidence is high
  the_move: string | null;
  signal_confidence: 'low' | 'medium' | 'high';
  
  // Metadata
  field_temperature: 'warm' | 'cool' | 'charged' | 'still';
  detected_dynamics: string[];
  identity_note: string | null;
  
  // Debug data
  debug?: {
    member_count: number;
    total_activity: number;
    silent_count: number;
    frequency_pattern: string;
    user_activity: number;
    avg_activity: number;
  };
}

export const getForumLiveField = async (
  forumId: string,
  userId: string
): Promise<ForumLiveFieldResponse> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/live-field`, {
    params: { user_id: userId }
  });
  return response.data;
};

// =====================================================
// FORUM CHAT TYPES & API
// =====================================================

export type ForumChatMode = 'self' | 'member' | 'forum';

export interface ForumChatMessage {
  id: string;
  mode: ForumChatMode;
  target_member_id: string | null;
  target_member_name: string | null;
  message: string;
  response: string;
  timestamp: string;
}

export interface ForumChatRequest {
  user_id: string;
  message: string;
  mode: ForumChatMode;
  target_member_id?: string;
}

export interface ForumChatResponse {
  success: boolean;
  message_id: string;
  response: string;
  timestamp: string;
}

// Get forum chat history
export const getForumChatHistory = async (
  forumId: string,
  userId: string,
  limit: number = 50
): Promise<{ success: boolean; messages: ForumChatMessage[] }> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/chat/history`, {
    params: { user_id: userId, limit }
  });
  return response.data;
};

// Send forum chat message
export const sendForumChatMessage = async (
  forumId: string,
  request: ForumChatRequest
): Promise<ForumChatResponse> => {
  const response = await apiWithRetry.post(`/forums/${forumId}/chat`, request);
  return response.data;
};

// Forum Story API
export interface ForumStoryResponse {
  success: boolean;
  story: string;
  generated_at: string;
  from_cache: boolean;
}

export const getForumStory = async (
  forumId: string,
  userId: string
): Promise<ForumStoryResponse> => {
  const response = await apiWithRetry.get(`/forums/${forumId}/story`, {
    params: { user_id: userId }
  });
  return response.data;
};

// Pairwise Dynamics API
export interface PairwiseDynamicsResponse {
  success: boolean;
  member_a: { id: string; name: string };
  member_b: { id: string; name: string };
  reflection: string;
}

export const getPairwiseDynamics = async (
  forumId: string,
  userId: string,
  memberAId: string,
  memberBId: string
): Promise<PairwiseDynamicsResponse> => {
  const response = await apiWithRetry.post(`/forums/${forumId}/pairwise-dynamics`, {
    user_id: userId,
    member_a_id: memberAId,
    member_b_id: memberBId
  });
  return response.data;
};

// =====================================================
// FORUM HD MAPPING API - "How they map to me"
// =====================================================

export interface ChannelCompletion {
  channel: string;
  name: string;
  theme: string;
  your_gate: number;
  their_gate: number;
}

export interface ForumMemberMapping {
  member_id: string;
  member_name: string;
  headline: string;
  description: string;
  what_works: string;
  what_to_watch: string;
  why_this_happens: ChannelCompletion[];
  channel_count: number;
  strength_score: number;
}

export interface ForumMemberMappingsResponse {
  success: boolean;
  mappings: ForumMemberMapping[];
  current_user_id: string;
  error?: string;
}

export const getForumMemberMappings = async (
  forumId: string,
  userId: string
): Promise<ForumMemberMappingsResponse> => {
  // Use a unique URL path with cache-buster to completely bypass CDN edge caching
  // Cloudflare caches by URL+method, so changing the URL path forces fresh fetch
  const cacheBuster = Date.now();
  const response = await apiWithRetry.post(`/forum-mappings?_cb=${cacheBuster}`, {
    forum_id: forumId,
    user_id: userId,
  });
  return response.data;
};

// =====================================================
// PATTERN SIGNALS API (Why this is showing up)
// =====================================================

export interface PatternSignalDetail {
  label: string;
  meaning: string;
  strength?: number;
}

export interface PatternSignalsResponse {
  summary: string;
  signals: {
    astrology?: PatternSignalDetail[];
    human_design?: PatternSignalDetail[];
    pattern_history?: PatternSignalDetail[];
  };
  synthesis: string;
  pattern_history?: string;
  confidence: number;
}

export const getPatternSignals = async (userId: string): Promise<PatternSignalsResponse> => {
  const response = await apiWithRetry.get(`/pattern-signals/${userId}`);
  return response.data;
};

// =====================================================
// CROSS-LENS PATTERN DIAGNOSIS API
// =====================================================

export interface DiagnosisConstitution {
  action_style: string;
  clarity_style: string;
  pressure_distortion: string;
  recurring_gift: string;
  recurring_failure_mode: string;
  timing_tendency: string;
  decision_pattern: string;
}

export interface DiagnosisHistory {
  frequency: number;
  pattern_shape: string;
  examples: string[];
  deeper_roots: string;
  cycle_observation: string;
}

export interface DiagnosisEvidence {
  timing?: {
    summary: string;
    implication: string;
  };
  design?: {
    summary: string;
    implication: string;
  };
  history?: {
    summary: string;
    implication: string;
  };
}

export interface PatternDiagnosisResponse {
  pattern_title: string;
  pattern_family: string;
  
  // Core diagnosis
  what_is_happening: string;
  why_it_is_happening: string;
  what_kind_of_moment: string;
  what_would_be_wise: string;
  full_diagnosis: string | FullDiagnosisWithHome;  // V3.1: Can be string or object with home data
  moment_type: string;
  
  // Constitution (stable patterns)
  constitution: DiagnosisConstitution;
  
  // History analysis
  history: DiagnosisHistory;
  
  // Lens evidence (supporting, not separate)
  evidence: DiagnosisEvidence;
  
  confidence: number;
  
  // Pattern memory (exposure state) - enables evolved messaging
  exposure_state?: 'first_exposure' | 'repeated_exposure' | 'persistent_pattern' | 'engaged_pattern';
  exposure_copy?: {
    headline: string;
    opening: string;
    explanation: string;
    reflection_prompt: string;
    time_words?: string[];
    exposure_state: string;
  };
  
  // V1: Pattern Memory Surfacing (validated, earned memory only)
  memory?: {
    memory_line: string;
    recurrence_count: number;
    last_seen_at: string;
    memory_state: 'returning' | 'repeating' | 'deepening' | 'unresolved' | 'easing';
  } | null;
  
  // V3.1: Pattern ID for angle tracking
  pattern_id?: string;
}

// V3.1: Home insight with angle system data
export interface HomeInsightData {
  title?: string;
  body?: string;
  bridge?: string;
  better_move?: string;
  card_version?: string;
  behavior_snap?: string;
  life_arena?: string;
  engagement_state?: string;
  adaptation_mode?: string;
  first_line_source?: string;
  debug?: {
    angle_system?: {
      pattern_key?: string;
      is_repeated_pattern?: boolean;
      angle_id?: string;
      angle_label?: string;
      angle_selection_reason?: string;
      recent_history_count?: number;
    };
    [key: string]: any;
  };
}

export interface FullDiagnosisWithHome {
  text?: string;
  home?: HomeInsightData;
}

/**
 * Get cross-lens pattern diagnosis.
 * Returns ONE integrated interpretation, not separate lens summaries.
 */
export const getPatternDiagnosis = async (userId: string, forceRefresh: boolean = false): Promise<PatternDiagnosisResponse> => {
  const response = await apiWithRetry.get(`/pattern-diagnosis/${userId}`, {
    params: forceRefresh ? { force_refresh: true } : {}
  });
  return response.data;
};

// ============================================================
// MIRROR PROFILE PERSISTENCE API
// ============================================================

export interface MirrorProfileData {
  primary_goal: string;
  uncertainty_style: string;
  desired_depth: string;
  support_style: string;
  current_self_state: string;
  onboarding_version: string;
  updated_at?: string;
}

export interface SaveMirrorProfileRequest {
  user_id: string;
  mirror_profile: MirrorProfileData;
  questionnaire_answers?: string[];
}

export interface GetMirrorProfileResponse {
  success: boolean;
  has_profile: boolean;
  mirror_profile?: MirrorProfileData;
  questionnaire_answers?: string[];
  source: 'backend' | 'not_found';
}

/**
 * Save MirrorProfile to backend for persistent cross-device storage.
 * This is the canonical store for experience preferences.
 */
export const saveMirrorProfile = async (request: SaveMirrorProfileRequest): Promise<{ success: boolean; saved: boolean }> => {
  const response = await apiWithRetry.post('/profile/mirror-profile', request);
  return response.data;
};

/**
 * Get MirrorProfile from backend.
 * Returns profile if exists, or indicates not found.
 */
export const getMirrorProfile = async (userId: string): Promise<GetMirrorProfileResponse> => {
  const response = await apiWithRetry.get(`/profile/mirror-profile/${userId}`);
  return response.data;
};


// ============================================================
// V5.0 HOME SYNTHESIS API
// ============================================================

export interface HomeSynthesisResponse {
  success: boolean;
  date: string;
  pattern_key: string;
  the_call: string;
  the_reality: string;
  the_source_hint: string;
  the_edge: string;
  cta_text: string;
  cta_target: string;
  pattern_memory_state: string;
  evolution_state: string;
  angle_id: string;
  version: string;
  original_pattern?: {
    title: string;
    body: string;
    pattern_id: string;
  };
  debug?: any;
}

/**
 * V5.0: Get Home Synthesis - 4-block decisive pattern synthesis
 * 
 * Returns:
 * - THE CALL: Sharp, decisive pattern statement
 * - THE REALITY: Grounded, felt experience
 * - THE SOURCE HINT: Subtle multi-source cue
 * - THE EDGE: Tension/choice moment
 * - CTA -> Astrology Today
 */
export const getHomeSynthesis = async (userId: string): Promise<HomeSynthesisResponse> => {
  const response = await apiWithRetry.get(`/home-synthesis/${userId}`);
  return response.data;
};


// ============================================================
// V5.0 ASTRO EXPERT API
// ============================================================

export interface AstroExpertResponse {
  success: boolean;
  lens: string;
  date: string;
  version: string;
  todays_theme: string;
  whats_happening: string[];
  how_it_interacts: string[];
  what_it_feels_like: string[];
  what_to_do: string[];
  one_question: string;
  pattern_memory_state: string;
  evolution_state: string;
  signals?: {
    transits: any[];
    active_houses: number[];
    dominant_planet: string;
    primary_house: number;
  };
  debug?: any;
}

/**
 * V5.0: Get Astrology Expert Diagnosis - 6-section expert interpretation
 * 
 * Feels like: A master astrologer who knows you
 * 
 * Returns:
 * - TODAY'S THEME: Tension headline
 * - WHAT'S HAPPENING: Real transit bullets
 * - HOW IT INTERACTS: Personalization (pattern memory + tendencies)
 * - WHAT IT FEELS LIKE: Concrete experience
 * - WHAT TO DO: Grounded action
 * - ONE QUESTION: Reflective prompt
 * 
 * V5.2: Now supports timeframe parameter for HORIZON INTERPRETATION
 * - today: "What is peaking or loud right now?"
 * - week: "What keeps surfacing across these days?"
 * - month: "What larger arc is this part of?"
 */
export const getAstroExpert = async (
  userId: string, 
  timeframe: 'today' | 'week' | 'month' = 'today'
): Promise<AstroExpertResponse> => {
  console.log(`[API] getAstroExpert called: userId=${userId}, timeframe=${timeframe}`);
  const response = await apiWithRetry.get(`/astro-expert/${userId}?timeframe=${timeframe}`);
  console.log(`[API] getAstroExpert response: theme="${response.data?.todays_theme}", timeframe="${response.data?.timeframe}"`);
  return response.data;
};


// ============================================================
// RELATIONSHIP PATTERN API (Identity-Level)
// ============================================================

export interface RelationshipPatternResponse {
  success: boolean;
  version: string;
  pattern_type: string;
  pattern_quality: string;
  core_pattern: string;
  default_tension: string;
  growth_edge: string;
  gift: string;
  what_teaching: string;  // NEW: What relationships are teaching you
  try_this: string;
  generated_at: string;
}

/**
 * Get user's general relationship pattern (identity-level).
 * 
 * This is NOT about specific people.
 * This is about HOW THE USER SHOWS UP in relationships.
 * 
 * Returns:
 * - CORE PATTERN: How they show up
 * - DEFAULT TENSION: Their typical friction point
 * - GROWTH EDGE: What to shift (Your Shift equivalent)
 * - GIFT: What they bring to relationships
 * - TRY THIS: One actionable suggestion
 */
export const getRelationshipPattern = async (userId: string): Promise<RelationshipPatternResponse> => {
  const response = await apiWithRetry.get(`/relationship-pattern/${userId}`);
  return response.data;
};


// ============================================================
// RELATIONSHIP NARRATIVE FLOW API (1:1 Dynamic)
// ============================================================

export interface RelationshipNarrativeFlowResponse {
  success: boolean;
  other_name: string;
  generated_at: string;
  
  // 5-part narrative flow
  field_state: string;
  your_position: string | null;
  your_position_type: 'initiating' | 'receiving' | 'holding_back' | 'withdrawing' | 'mirroring' | 'protecting';
  trajectory: string | null;
  trajectory_type: 'distance_growing' | 'tension_building' | 'pattern_repeating' | 'connection_deepening' | 'stagnation';
  trajectory_severity: 'low' | 'moderate' | 'high' | 'positive';
  story: string;
  the_move: string | null;
  
  // Metadata
  field_temperature: 'warm' | 'charged' | 'present' | 'quiet';
  escalation_level: number;
  is_breakthrough: boolean;
  signal_confidence: 'low' | 'medium' | 'high';
  
  // Debug data
  debug?: {
    user_type: string;
    other_type: string;
    emotional_tone: string;
  };
}

/**
 * Get 5-part Relationship Narrative Flow for a 1:1 dynamic.
 * 
 * Same structure as Forum Live Field, but adapted for 1:1 dynamics.
 * 
 * 5 Sections:
 * 1. FIELD STATE - What's happening between you two
 * 2. YOUR POSITION - Where you stand in this dynamic
 * 3. TRAJECTORY - What happens if nothing changes
 * 4. STORY - What this connection tends to become
 * 5. THE MOVE - Subtle action opening
 * 
 * Language uses: "between you", "this connection", "this dynamic"
 * Avoids: "the room", "the space", "the circle"
 */
export const getRelationshipNarrativeFlow = async (
  userId: string,
  otherName: string,
  context: string = ''
): Promise<RelationshipNarrativeFlowResponse> => {
  const params = new URLSearchParams({
    other_name: otherName,
    context,
  });
  const response = await apiWithRetry.get(`/relationship-narrative/${userId}?${params}`);
  return response.data;
};


// ============================================================
// DAILY TRANSIT WINDOW API (True Sidereal)
// ============================================================

export interface DailyTransitWindowResponse {
  date: string;
  local_timezone: string;
  scan_start_utc: string;
  scan_end_utc: string;
  computed_at: string;
  total_events: number;
  
  // Events
  all_events: Array<{
    event_type: string;
    timestamp_utc: string;
    timestamp_local: string;
    local_time: string;
    local_timezone: string;
    description: string;
    significance: string;
    timing: 'passed' | 'current' | 'upcoming';
    minutes_from_now: number;
    transit_planet?: string;
    natal_planet?: string;
    aspect_type?: string;
    orb_at_peak?: number;
    from_sign?: string;
    to_sign?: string;
  }>;
  
  moon_ingresses: Array<any>;
  aspect_events: Array<any>;
  slow_transits_active: Array<{
    transit_planet: string;
    natal_planet: string;
    aspect_type: string;
    orb: number;
    description: string;
    note: string;
  }>;
  
  // Summary
  current_moon_sign: string;
  next_moon_sign?: string;
  next_moon_ingress_time?: string;
  strongest_active_aspect?: {
    transit_planet: string;
    natal_planet: string;
    aspect_type: string;
    orb: number;
    is_applying: boolean;
    description: string;
  };
  current_active_aspects?: Array<any>;
  
  // Theme
  daily_theme?: {
    primary_theme: string;
    moon_context: {
      current_sign: string;
      next_sign?: string;
      ingress_time?: string;
    };
    sun_context: {
      sign: string;
      degree: number;
    };
    theme_keywords: string[];
    upcoming_events: any[];
  };
  
  error?: string;
}

/**
 * Get daily transit window scan using TRUE SIDEREAL calculations.
 * 
 * Scans the full local day (midnight to midnight) for:
 * - Moon sign ingress times
 * - Transit-to-natal aspect exact times
 * - Currently active aspects (within 3° orb)
 * - Slow-moving transits (Mercury, Venus, Mars)
 * 
 * All calculations use Swiss Ephemeris True Sidereal (SVP 31.2836°, J2000)
 */
export const getDailyTransitWindow = async (
  userId: string,
  timezone: string = 'UTC'
): Promise<DailyTransitWindowResponse> => {
  const params = new URLSearchParams({ timezone_str: timezone });
  const response = await apiWithRetry.get(`/astrology/daily-window/${userId}?${params}`);
  return response.data;
};

export default api;