/**
 * Enneagram Assessment Gate Logic - SINGLE SOURCE OF TRUTH
 * =========================================================
 * 
 * This module provides centralized, deterministic logic for determining
 * when to show upgrade/retake CTAs in the Enneagram views.
 * 
 * PRIORITY ORDER (single CTA only - no dual display):
 * 1. If confidence_tier is low → "Refine your reflection" (retake)
 * 2. Else if assessment_depth !== "deep" → "Want a clearer mirror?" (upgrade)
 * 3. Else → no CTA shown
 * 
 * PRELIMINARY LABEL:
 * - Shown only when assessment_depth !== "deep"
 * 
 * Optional: If created_at_iso > 6 months old → suggest_refresh = true
 * 
 * CTA COPY (MIRROR-SAFE - NO COACHING LANGUAGE)
 */

// =============================================================================
// TYPES
// =============================================================================

export type AssessmentDepth = 'short' | 'deep';
export type ConfidenceTier = 'high' | 'moderate' | 'exploratory' | 'low';

export interface EnneagramGateInput {
  assessment_depth?: AssessmentDepth | string;
  confidence_tier?: ConfidenceTier | string;
  confidence?: number;
  created_at_iso?: string;
}

export interface EnneagramGateState {
  // Core flags
  needs_deep_assessment: boolean;      // Short assessment → upgrade path
  suggest_retake: boolean;             // Low confidence → retake path
  result_is_preliminary: boolean;      // Only true for short assessments
  
  // Optional flags
  suggest_refresh: boolean;
  
  // CTA visibility (derived - ONLY ONE can be true at a time)
  show_cta: boolean;
  cta_type: 'retake' | 'upgrade' | 'refresh' | null;
  
  // Analytics-friendly variant string
  cta_variant: 'retake_low_confidence' | 'upgrade_short' | 'refresh_stale' | null;
  
  // Computed age for analytics
  result_age_days: number | null;
  
  // Debug info
  _debug: {
    input_depth: string | undefined;
    input_tier: string | undefined;
    input_confidence: number | undefined;
    age_days: number | null;
    rule_applied: string;
  };
}

export interface EnneagramCTACopy {
  title: string;
  body: string;
  button_text: string;
  variant: 'primary' | 'secondary';
}

// =============================================================================
// CONSTANTS
// =============================================================================

// Refresh threshold: 6 months in days
const REFRESH_THRESHOLD_DAYS = 180;

// Low confidence tiers that trigger retake CTA
const LOW_CONFIDENCE_TIERS = ['low', 'exploratory'];

// Mirror-safe CTA copy (NO coaching language)

// Primary: For short assessments (upgrade path)
export const UPGRADE_CTA_COPY: EnneagramCTACopy = {
  title: "Want a clearer mirror?",
  body: "This view is based on a shorter Enneagram assessment.\nYou can take a deeper version anytime to refine the picture.",
  button_text: "Take the deeper assessment",
  variant: 'primary',
};

// Secondary: For low confidence (retake path) - HIGHEST PRIORITY
export const RETAKE_CTA_COPY: EnneagramCTACopy = {
  title: "Refine your reflection",
  body: "Your current result shows some ambiguity.\nA retake can help clarify what's showing up.",
  button_text: "Retake assessment",
  variant: 'secondary',
};

export const REFRESH_CTA_COPY: EnneagramCTACopy = {
  title: "It's been a while",
  body: "You took this assessment over 6 months ago.\nYou might find value in reflecting again.",
  button_text: "Retake assessment",
  variant: 'secondary',
};

// Legacy exports for backwards compatibility
export const PRIMARY_CTA_COPY = UPGRADE_CTA_COPY;
export const SECONDARY_CTA_COPY = RETAKE_CTA_COPY;

// =============================================================================
// CORE LOGIC
// =============================================================================

/**
 * Calculate the age of the assessment result in days.
 * Returns null if created_at_iso is not provided or invalid.
 */
export function calculateAssessmentAgeDays(created_at_iso?: string): number | null {
  if (!created_at_iso) return null;
  
  try {
    const created = new Date(created_at_iso);
    const now = new Date();
    const diffMs = now.getTime() - created.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    return diffDays >= 0 ? diffDays : null;
  } catch {
    return null;
  }
}

/**
 * Compute the gate state for Enneagram assessment CTAs.
 * This is the SINGLE SOURCE OF TRUTH for all retake/upgrade logic.
 * 
 * PRIORITY ORDER (prevents dual CTAs):
 * 1. Low confidence → retake CTA
 * 2. Short assessment → upgrade CTA
 * 3. Stale result → refresh CTA
 * 4. None
 * 
 * @param input - The user's Enneagram result data
 * @returns EnneagramGateState with all derived flags
 */
export function computeEnneagramGateState(input: EnneagramGateInput): EnneagramGateState {
  const depth = input.assessment_depth;
  const tier = input.confidence_tier;
  const confidence = input.confidence;
  const ageDays = calculateAssessmentAgeDays(input.created_at_iso);
  
  // Initialize state
  let needs_deep_assessment = false;
  let suggest_retake = false;
  let result_is_preliminary = false;
  let suggest_refresh = false;
  let cta_type: 'retake' | 'upgrade' | 'refresh' | null = null;
  let rule_applied = 'none';
  
  // Determine preliminary status (independent of CTA priority)
  result_is_preliminary = depth !== 'deep';
  
  // ==========================================================================
  // PRIORITY 1: Low confidence → retake CTA (highest priority)
  // ==========================================================================
  if (tier && LOW_CONFIDENCE_TIERS.includes(tier.toLowerCase())) {
    suggest_retake = true;
    cta_type = 'retake';
    rule_applied = 'priority_1_low_confidence';
  }
  // ==========================================================================
  // PRIORITY 2: Short assessment → upgrade CTA
  // ==========================================================================
  else if (depth !== 'deep') {
    needs_deep_assessment = true;
    cta_type = 'upgrade';
    rule_applied = 'priority_2_short_assessment';
  }
  // ==========================================================================
  // PRIORITY 3: Stale result → refresh CTA
  // ==========================================================================
  else if (ageDays !== null && ageDays > REFRESH_THRESHOLD_DAYS) {
    suggest_refresh = true;
    cta_type = 'refresh';
    rule_applied = 'priority_3_stale_result';
  }
  // ==========================================================================
  // PRIORITY 4: No CTA
  // ==========================================================================
  else {
    rule_applied = 'no_cta_needed';
  }
  
  return {
    needs_deep_assessment,
    suggest_retake,
    result_is_preliminary,
    suggest_refresh,
    show_cta: cta_type !== null,
    cta_type,
    _debug: {
      input_depth: depth,
      input_tier: tier,
      input_confidence: confidence,
      age_days: ageDays,
      rule_applied,
    },
  };
}

/**
 * Get the appropriate CTA copy based on gate state.
 * Returns null if no CTA should be shown.
 */
export function getEnneagramCTACopy(gateState: EnneagramGateState): EnneagramCTACopy | null {
  switch (gateState.cta_type) {
    case 'retake':
      return RETAKE_CTA_COPY;
    case 'upgrade':
      return UPGRADE_CTA_COPY;
    case 'refresh':
      return REFRESH_CTA_COPY;
    default:
      return null;
  }
}

/**
 * Convenience function: Get everything needed for CTA rendering in one call.
 */
export function getEnneagramUpgradeInfo(input: EnneagramGateInput): {
  gateState: EnneagramGateState;
  ctaCopy: EnneagramCTACopy | null;
  showPreliminaryLabel: boolean;
} {
  const gateState = computeEnneagramGateState(input);
  const ctaCopy = getEnneagramCTACopy(gateState);
  
  return {
    gateState,
    ctaCopy,
    showPreliminaryLabel: gateState.result_is_preliminary,
  };
}
