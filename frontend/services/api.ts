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
}

export const createJournalEntry = async (
  userId: string, 
  content: string,
  metadata?: PatternJournalMetadata
) => {
  const response = await apiWithRetry.post('/journal', {
    user_id: userId,
    content,
    ...metadata
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
  const response = await apiWithRetry.get(`/forums/user/${userId}`);
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

export default api;