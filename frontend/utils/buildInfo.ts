/**
 * Build Information Utility
 * =========================
 * 
 * Provides build-time diagnostics for debugging deployment issues.
 * Used to verify which bundle version is running and which API it's hitting.
 */

import Constants from 'expo-constants';

// ============================================
// BUILD_ID: Set at export time
// ============================================
// This timestamp is baked into the bundle at build time.
// If you see an old BUILD_ID after deploy, the client is using a stale bundle.
export const BUILD_ID = '2026-02-11T10:05:00Z';
export const BUILD_VERSION = 'v11-env-debug';

// Log BUILD_ID immediately when this module loads
if (typeof console !== 'undefined') {
  console.log(`%c[BUILD] ${BUILD_VERSION} | ${BUILD_ID}`, 'background: #00ff00; color: black; font-weight: bold; padding: 4px 8px;');
}

// ============================================
// API Base URL Resolution
// ============================================
export function getApiBaseUrl(): string {
  // Priority: EXPO_PUBLIC_BACKEND_URL > Constants > fallback
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  const constantsUrl = Constants.expoConfig?.extra?.backendUrl;
  
  if (envUrl) return envUrl;
  if (constantsUrl) return constantsUrl;
  return 'http://localhost:8001';
}

// ============================================
// Debug Info Object (for display)
// ============================================
export interface BuildDebugInfo {
  build_id: string;
  build_version: string;
  api_base_url: string;
  platform: string;
  expo_sdk: string | null;
  debug_mirror_env: boolean;
}

export function getBuildDebugInfo(): BuildDebugInfo {
  return {
    build_id: BUILD_ID,
    build_version: BUILD_VERSION,
    api_base_url: getApiBaseUrl(),
    platform: typeof window !== 'undefined' ? 'web' : 'native',
    expo_sdk: Constants.expoConfig?.sdkVersion || null,
    debug_mirror_env: process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true',
  };
}

// ============================================
// Enneagram Payload Snapshot (for debugging)
// ============================================
export interface EnneagramPayloadSnapshot {
  assessment_depth: string | null | undefined;
  assessment_version: string | null | undefined;
  confidence_tier: string | null | undefined;
  confidence: number | null | undefined;
  core_type: number | null | undefined;
  wing: number | string | null | undefined;
  created_at: string | null | undefined;
  wing_scores?: {
    left: number;
    right: number;
    diff: number;
  } | null;
}

export function createEnneagramPayloadSnapshot(result: any): EnneagramPayloadSnapshot {
  return {
    assessment_depth: result?.assessment_depth,
    assessment_version: result?.assessment_version,
    confidence_tier: result?.confidence_tier,
    confidence: result?.confidence,
    core_type: result?.inferred_core,
    wing: result?.inferred_wing,
    created_at: result?.created_at,
    wing_scores: result?.debug_scores?.wing_scores || null,
  };
}

// ============================================
// INVARIANT ASSERTIONS (Dev only)
// ============================================

/**
 * Assert that the gate state is consistent with assessment_depth.
 * Logs a warning if a contradiction is detected.
 */
export function assertGateInvariant(
  assessment_depth: string | null | undefined,
  confidence_tier: string | null | undefined,
  show_cta: boolean,
  show_preliminary: boolean
): void {
  const isDeep = assessment_depth === 'deep';
  
  // INVARIANT: Deep assessment should NEVER show upgrade CTA or preliminary label
  if (isDeep && (show_cta || show_preliminary)) {
    console.error('[GATE_INVARIANT_VIOLATION]', {
      message: 'Deep assessment is showing upgrade CTA or preliminary label!',
      assessment_depth,
      confidence_tier,
      show_cta,
      show_preliminary,
      build_id: BUILD_ID,
      build_version: BUILD_VERSION,
    });
  }
  
  // INVARIANT: High confidence with upgrade CTA is suspicious (not strictly invalid)
  if (confidence_tier === 'high' && show_cta) {
    console.warn('[GATE_WARNING] High confidence but CTA showing', {
      assessment_depth,
      confidence_tier,
      show_cta,
      build_id: BUILD_ID,
    });
  }
}
