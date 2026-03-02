/**
 * Transit Service - Frontend client for Transit Engine endpoints
 * 
 * Calls:
 * - POST /api/compute/transits/now
 * - POST /api/interpret/transits
 */

import api from './api';

// ============================================
// TYPES
// ============================================

export interface TransitMeta {
  mode: 'now' | 'window';
  timestamp_utc: string;
  tone_profile: string;
}

export interface TwoMinutePractice {
  title: string;
  steps: string[];
}

export interface AttentionWindow {
  from_utc: string;
  to_utc: string;
  label: string;
  based_on: string[];
}

export interface TransitInterpretation {
  meta: TransitMeta;
  headline: string;
  key_points: string[];
  reflect: string[];
  two_minute_practice: TwoMinutePractice;
  attention_windows: AttentionWindow[];
  guardrails: {
    no_fatalism: boolean;
    no_predictions: boolean;
    user_sovereignty: boolean;
  };
}

export interface TransitComputeResponse {
  meta: {
    ayanamsa: string;
    house_system: string;
    orb_deg: number;
  };
  timestamp_utc: string;
  transiting_planets: Record<string, any>;
  aspects_to_natal_now: any[];
  house_activation?: {
    enabled: boolean;
    reason?: string;
  };
}

export interface HealthResponse {
  build_id?: string;
  has_transits_now?: boolean;
  has_transits_window?: boolean;
  has_transits_interpret?: boolean;
  env?: string;
  status?: string;
}

// ============================================
// CACHED BUILD INFO
// ============================================

let cachedHealthInfo: HealthResponse | null = null;

/**
 * Get cached health/build info
 * Fetches once and caches for the session
 */
export async function getHealthInfo(): Promise<HealthResponse> {
  if (cachedHealthInfo) {
    return cachedHealthInfo;
  }
  
  try {
    const response = await api.get('/health');
    cachedHealthInfo = response.data;
    return cachedHealthInfo;
  } catch (error) {
    console.error('[TransitService] Failed to fetch health info:', error);
    return {};
  }
}

// ============================================
// TRANSIT INSIGHT FETCHER
// ============================================

/**
 * Get transit insight for "now"
 * 
 * 1. Calls POST /api/compute/transits/now
 * 2. Calls POST /api/interpret/transits with the compute response
 * 3. Returns the interpretation JSON
 * 
 * @param userId - User ID for natal chart lookup
 * @param timestamp_utc - Optional timestamp (ISO format), defaults to now
 * @returns TransitInterpretation or throws error
 */
export async function getTransitInsightNow(
  userId: string,
  timestamp_utc?: string
): Promise<TransitInterpretation> {
  // Step 1: Compute transits
  const computePayload: any = {
    user_id: userId,
    orb_deg: 2,
    include_houses: true,
  };
  
  if (timestamp_utc) {
    computePayload.timestamp_utc = timestamp_utc;
  }
  
  const computeResponse = await api.post<TransitComputeResponse>(
    '/compute/transits/now',
    computePayload
  );
  
  const transitPayload = computeResponse.data;
  
  // Step 2: Interpret transits
  const interpretPayload = {
    user_id: userId,
    mode: 'now' as const,
    transit_payload: transitPayload,
  };
  
  const interpretResponse = await api.post<TransitInterpretation>(
    '/interpret/transits',
    interpretPayload
  );
  
  return interpretResponse.data;
}

/**
 * Check if transit endpoints are available
 * Uses cached health info
 */
export async function areTransitsAvailable(): Promise<boolean> {
  try {
    const health = await getHealthInfo();
    return !!(health.has_transits_now && health.has_transits_interpret);
  } catch {
    return false;
  }
}

/**
 * Get build ID for debug display
 */
export async function getTransitBuildId(): Promise<string | null> {
  try {
    const health = await getHealthInfo();
    return health.build_id || null;
  } catch {
    return null;
  }
}
