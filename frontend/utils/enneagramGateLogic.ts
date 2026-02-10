/**
 * Enneagram Assessment Gate Logic - SINGLE SOURCE OF TRUTH
 * =========================================================
 * 
 * This module provides centralized, deterministic logic for determining
 * when to show upgrade/retake CTAs in the Enneagram views.
 * 
 * RULES:
 * 1. If assessment_depth !== "deep" → needs_deep_assessment = true, result_is_preliminary = true
 * 2. Else if confidence_tier !== "high" → suggest_deep_assessment = true
 * 3. Else → no CTA shown
 * 
 * Optional: If created_at_iso > 6 months old → suggest_refresh = true
 * 
 * CTA COPY (MIRROR-SAFE - NO COACHING LANGUAGE):
 * - Primary (needs_deep): "Want a clearer mirror?"
 * - Secondary (suggest_deep): "Refine this view"
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
  needs_deep_assessment: boolean;
  suggest_deep_assessment: boolean;
  result_is_preliminary: boolean;
  
  // Optional flags
  suggest_refresh: boolean;
  
  // CTA visibility (derived - only one can be true)
  show_primary_cta: boolean;
  show_secondary_cta: boolean;
  
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

// Mirror-safe CTA copy (NO coaching language)
export const PRIMARY_CTA_COPY: EnneagramCTACopy = {
  title: "Want a clearer mirror?",
  body: "This view is based on a shorter Enneagram assessment.\nYou can take a deeper version anytime to refine the picture.",
  button_text: "Take the deeper assessment",
  variant: 'primary',
};

export const SECONDARY_CTA_COPY: EnneagramCTACopy = {
  title: "Refine this view",
  body: "This result is valid, and you can also explore it in more depth if you're curious.",
  button_text: "Explore a deeper assessment",
  variant: 'secondary',
};

export const REFRESH_CTA_COPY: EnneagramCTACopy = {
  title: "It's been a while",
  body: "You took this assessment over 6 months ago. You might find value in reflecting again.",
  button_text: "Retake assessment",
  variant: 'secondary',
};

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
  let suggest_deep_assessment = false;
  let result_is_preliminary = false;
  let suggest_refresh = false;
  let rule_applied = 'none';
  
  // ==========================================================================
  // RULE 1: If assessment_depth !== "deep" → needs deep assessment
  // ==========================================================================
  if (depth !== 'deep') {
    needs_deep_assessment = true;
    result_is_preliminary = true;
    rule_applied = 'rule_1_not_deep';
  }
  // ==========================================================================
  // RULE 2: Else if confidence_tier !== "high" → suggest deep assessment
  // ==========================================================================
  else if (tier !== 'high') {
    suggest_deep_assessment = true;
    result_is_preliminary = false;
    rule_applied = 'rule_2_not_high_confidence';
  }
  // ==========================================================================
  // RULE 3: Else → no CTA shown
  // ==========================================================================
  else {
    result_is_preliminary = false;
    rule_applied = 'rule_3_high_confidence_deep';
  }
  
  // ==========================================================================
  // OPTIONAL: Check for stale result (> 6 months)
  // Only suggest refresh if we're NOT already showing a CTA
  // ==========================================================================
  if (!needs_deep_assessment && !suggest_deep_assessment && ageDays !== null) {
    if (ageDays > REFRESH_THRESHOLD_DAYS) {
      suggest_refresh = true;
      rule_applied += '_with_refresh';
    }
  }
  
  // Derive CTA visibility (mutually exclusive)
  const show_primary_cta = needs_deep_assessment;
  const show_secondary_cta = !needs_deep_assessment && (suggest_deep_assessment || suggest_refresh);
  
  return {
    needs_deep_assessment,
    suggest_deep_assessment,
    result_is_preliminary,
    suggest_refresh,
    show_primary_cta,
    show_secondary_cta,
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
  if (gateState.show_primary_cta) {
    return PRIMARY_CTA_COPY;
  }
  if (gateState.show_secondary_cta) {
    if (gateState.suggest_refresh && !gateState.suggest_deep_assessment) {
      return REFRESH_CTA_COPY;
    }
    return SECONDARY_CTA_COPY;
  }
  return null;
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
