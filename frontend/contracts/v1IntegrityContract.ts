/**
 * Project Mirror V1 Integrity Contract
 * 
 * This module defines the frozen V1 contract invariants and provides
 * validation functions to enforce them at runtime and test time.
 * 
 * VERSION: 1.0.0 - FROZEN
 * 
 * ANY CHANGE TO THRESHOLDS OR INVARIANTS REQUIRES:
 * 1. Version bump
 * 2. Product review
 * 3. Full regression test update
 */

// ============================================
// CONTRACT VERSION (FROZEN)
// ============================================

export const MIRROR_V1_CONTRACT_VERSION = "1.0.0";
export const MIRROR_V1_CONTRACT_FROZEN = true;

// ============================================
// SECTION A: ENNEAGRAM INVARIANT THRESHOLDS
// ============================================

export const ENNEAGRAM_INVARIANTS = {
  /** Valid wing display states - null is NEVER valid */
  VALID_WING_STATES: ['dominant', 'leaning', 'balanced', 'not_clear'] as const,
  
  /** Confidence tiers */
  CONFIDENCE_TIERS: ['low', 'moderate', 'high'] as const,
  
  /** Probability must sum to 1.0 within this tolerance */
  PROBABILITY_SUM_TOLERANCE: 0.001,
  
  /** Minimum probability for any type (no type goes to zero) */
  MIN_PROBABILITY_FLOOR: 0.001,
} as const;

// ============================================
// SECTION B: CROSS-LENS INVARIANT THRESHOLDS
// ============================================

export const CROSS_LENS_INVARIANTS = {
  /** Maximum adjustment allowed per type */
  MAX_ADJUSTMENT_PER_TYPE: 0.05,
  
  /** Maximum total redistribution allowed */
  MAX_TOTAL_REDISTRIBUTION: 0.10,
  
  /** Top-2 gap threshold for eligibility */
  TOP_2_GAP_THRESHOLD: 0.12,
  
  /** Confidence tiers that allow adjustment */
  ADJUSTABLE_CONFIDENCE_TIERS: ['low', 'moderate'] as const,
  
  /** Assessment depths that allow adjustment */
  ADJUSTABLE_DEPTHS: ['deep'] as const,
} as const;

// ============================================
// SECTION C: NARRATIVE LANGUAGE INVARIANTS
// ============================================

export const NARRATIVE_INVARIANTS = {
  /** Phrases that MUST NEVER appear in narratives */
  BANNED_PHRASES: [
    // Identity-locking
    'you are a type',
    'this is your type',
    "you're definitely",
    'your personality is',
    'you are definitely',
    
    // Confirmatory/Causal
    'this confirms',
    'this proves',
    'your astrology shows',
    'your astrology confirms',
    'your human design means',
    'your human design proves',
    'this means you are',
    'this means you have',
    
    // Prescriptive
    'you should',
    'you must',
    'you need to',
    'try to',
    'work on',
    
    // Absolute
    'you will always',
    'you never',
    'this is permanent',
    'your destiny',
    'always will',
    'never will',
    
    // Diagnostic
    'diagnosis',
    'symptoms of',
    'treatment',
    'disorder',
  ] as const,
  
  /** Phrases that indicate time-bound language (at least one required) */
  TIME_BOUND_INDICATORS: [
    'right now',
    'at this stage',
    'currently',
    'at this point',
    'emerging',
    'forming',
    'at this time',
    'for now',
  ] as const,
  
  /** Words that preserve agency in reflection prompts */
  AGENCY_WORDS: [
    'notice',
    'observe',
    'consider',
    'might',
    'may',
    'could',
  ] as const,
  
  /** Words that violate agency in reflection prompts */
  ANTI_AGENCY_WORDS: [
    'should',
    'must',
    'need to',
    'have to',
    'ought to',
  ] as const,
} as const;

// ============================================
// TYPE DEFINITIONS
// ============================================

export type WingState = typeof ENNEAGRAM_INVARIANTS.VALID_WING_STATES[number];
export type ConfidenceTier = typeof ENNEAGRAM_INVARIANTS.CONFIDENCE_TIERS[number];

export interface ContractViolation {
  invariant: string;
  section: 'A' | 'B' | 'C';
  severity: 'critical' | 'warning';
  message: string;
  context?: Record<string, unknown>;
}

export interface ContractValidationResult {
  valid: boolean;
  violations: ContractViolation[];
  contractVersion: string;
}

// ============================================
// SECTION A VALIDATORS: ENNEAGRAM INTEGRITY
// ============================================

/**
 * A1: Validates that wing display state is never null
 */
export function validateWingDisplay(
  wingState: string | null | undefined
): ContractViolation | null {
  if (wingState === null || wingState === undefined || wingState === 'null') {
    return {
      invariant: 'A1_WING_DISPLAY',
      section: 'A',
      severity: 'critical',
      message: 'Wing display must never be null in user-facing UI',
      context: { wingState },
    };
  }
  
  if (!ENNEAGRAM_INVARIANTS.VALID_WING_STATES.includes(wingState as WingState)) {
    return {
      invariant: 'A1_WING_DISPLAY',
      section: 'A',
      severity: 'critical',
      message: `Invalid wing state: ${wingState}. Must be one of: ${ENNEAGRAM_INVARIANTS.VALID_WING_STATES.join(', ')}`,
      context: { wingState, validStates: ENNEAGRAM_INVARIANTS.VALID_WING_STATES },
    };
  }
  
  return null;
}

/**
 * A2: Validates high confidence results are not altered
 */
export function validateHighConfidenceLock(
  confidenceTier: string,
  adjustmentApplied: boolean
): ContractViolation | null {
  if (confidenceTier === 'high' && adjustmentApplied) {
    return {
      invariant: 'A2_HIGH_CONFIDENCE_LOCK',
      section: 'A',
      severity: 'critical',
      message: 'High-confidence Enneagram results must NEVER be altered by cross-lens weighting',
      context: { confidenceTier, adjustmentApplied },
    };
  }
  return null;
}

/**
 * A3: Validates probability sum equals 1.0
 */
export function validateProbabilitySum(
  probabilities: Record<string, number>
): ContractViolation | null {
  const sum = Object.values(probabilities).reduce((a, b) => a + b, 0);
  const deviation = Math.abs(sum - 1.0);
  
  if (deviation > ENNEAGRAM_INVARIANTS.PROBABILITY_SUM_TOLERANCE) {
    return {
      invariant: 'A3_PROBABILITY_SUM',
      section: 'A',
      severity: 'critical',
      message: `Probabilities must sum to 1.0 (±${ENNEAGRAM_INVARIANTS.PROBABILITY_SUM_TOLERANCE}). Got: ${sum}`,
      context: { sum, deviation, tolerance: ENNEAGRAM_INVARIANTS.PROBABILITY_SUM_TOLERANCE },
    };
  }
  
  // Check minimum floor
  for (const [type, prob] of Object.entries(probabilities)) {
    if (prob < ENNEAGRAM_INVARIANTS.MIN_PROBABILITY_FLOOR) {
      return {
        invariant: 'A3_PROBABILITY_FLOOR',
        section: 'A',
        severity: 'critical',
        message: `Type ${type} probability (${prob}) below minimum floor (${ENNEAGRAM_INVARIANTS.MIN_PROBABILITY_FLOOR})`,
        context: { type, probability: prob, floor: ENNEAGRAM_INVARIANTS.MIN_PROBABILITY_FLOOR },
      };
    }
  }
  
  return null;
}

// ============================================
// SECTION B VALIDATORS: CROSS-LENS GUARDRAILS
// ============================================

/**
 * B1: Validates cross-lens adjustment eligibility
 */
export function validateCrossLensEligibility(
  confidenceTier: string,
  top2Gap: number,
  assessmentDepth: string,
  longitudinalSignals: boolean,
  adjustmentApplied: boolean
): ContractViolation | null {
  // If no adjustment applied, no validation needed
  if (!adjustmentApplied) return null;
  
  // Check confidence tier
  if (!CROSS_LENS_INVARIANTS.ADJUSTABLE_CONFIDENCE_TIERS.includes(confidenceTier as any)) {
    return {
      invariant: 'B1_ELIGIBILITY_CONFIDENCE',
      section: 'B',
      severity: 'critical',
      message: `Cross-lens adjustment applied with ineligible confidence tier: ${confidenceTier}`,
      context: { confidenceTier, allowedTiers: CROSS_LENS_INVARIANTS.ADJUSTABLE_CONFIDENCE_TIERS },
    };
  }
  
  // Check top-2 gap
  if (top2Gap > CROSS_LENS_INVARIANTS.TOP_2_GAP_THRESHOLD) {
    return {
      invariant: 'B1_ELIGIBILITY_GAP',
      section: 'B',
      severity: 'critical',
      message: `Cross-lens adjustment applied with top-2 gap (${top2Gap}) exceeding threshold (${CROSS_LENS_INVARIANTS.TOP_2_GAP_THRESHOLD})`,
      context: { top2Gap, threshold: CROSS_LENS_INVARIANTS.TOP_2_GAP_THRESHOLD },
    };
  }
  
  // Check assessment depth
  const depthEligible = CROSS_LENS_INVARIANTS.ADJUSTABLE_DEPTHS.includes(assessmentDepth as any) || longitudinalSignals;
  if (!depthEligible) {
    return {
      invariant: 'B1_ELIGIBILITY_DEPTH',
      section: 'B',
      severity: 'critical',
      message: `Cross-lens adjustment applied without eligible assessment depth or longitudinal signals`,
      context: { assessmentDepth, longitudinalSignals },
    };
  }
  
  return null;
}

/**
 * B2: Validates adjustment bounds
 */
export function validateAdjustmentBounds(
  adjustments: Record<string, number>
): ContractViolation[] {
  const violations: ContractViolation[] = [];
  
  // Check per-type bounds
  for (const [type, adjustment] of Object.entries(adjustments)) {
    if (Math.abs(adjustment) > CROSS_LENS_INVARIANTS.MAX_ADJUSTMENT_PER_TYPE) {
      violations.push({
        invariant: 'B2_PER_TYPE_BOUND',
        section: 'B',
        severity: 'critical',
        message: `Type ${type} adjustment (${adjustment}) exceeds ±${CROSS_LENS_INVARIANTS.MAX_ADJUSTMENT_PER_TYPE}`,
        context: { type, adjustment, maxAllowed: CROSS_LENS_INVARIANTS.MAX_ADJUSTMENT_PER_TYPE },
      });
    }
  }
  
  // Check total redistribution
  const totalRedistribution = Object.values(adjustments).reduce((sum, adj) => sum + Math.abs(adj), 0) / 2;
  if (totalRedistribution > CROSS_LENS_INVARIANTS.MAX_TOTAL_REDISTRIBUTION) {
    violations.push({
      invariant: 'B2_TOTAL_REDISTRIBUTION',
      section: 'B',
      severity: 'critical',
      message: `Total redistribution (${totalRedistribution}) exceeds ${CROSS_LENS_INVARIANTS.MAX_TOTAL_REDISTRIBUTION}`,
      context: { totalRedistribution, maxAllowed: CROSS_LENS_INVARIANTS.MAX_TOTAL_REDISTRIBUTION },
    });
  }
  
  return violations;
}

/**
 * B3: Validates raw results are preserved
 */
export function validateRawPreservation(
  enneagramRaw: unknown,
  adjustmentApplied: boolean,
  enneagramAdjusted: unknown
): ContractViolation | null {
  if (enneagramRaw === null || enneagramRaw === undefined) {
    return {
      invariant: 'B3_RAW_PRESERVATION',
      section: 'B',
      severity: 'critical',
      message: 'Raw Enneagram results must always be preserved',
      context: { enneagramRaw },
    };
  }
  
  if (adjustmentApplied && (enneagramAdjusted === null || enneagramAdjusted === undefined)) {
    return {
      invariant: 'B3_ADJUSTED_PRESERVATION',
      section: 'B',
      severity: 'critical',
      message: 'Adjusted results must be present when adjustment is applied',
      context: { adjustmentApplied, enneagramAdjusted },
    };
  }
  
  return null;
}

// ============================================
// SECTION C VALIDATORS: NARRATIVE LANGUAGE
// ============================================

/**
 * C1: Validates narrative contains no banned phrases
 */
export function validateNarrativeLanguage(
  narrativeText: string
): ContractViolation[] {
  const violations: ContractViolation[] = [];
  const lowerText = narrativeText.toLowerCase();
  
  for (const phrase of NARRATIVE_INVARIANTS.BANNED_PHRASES) {
    if (lowerText.includes(phrase.toLowerCase())) {
      violations.push({
        invariant: 'C1_BANNED_PHRASE',
        section: 'C',
        severity: 'critical',
        message: `Narrative contains banned phrase: "${phrase}"`,
        context: { phrase, narrativeExcerpt: narrativeText.substring(0, 200) },
      });
    }
  }
  
  return violations;
}

/**
 * C2: Validates uncertainty is visible when confidence is not high
 */
export function validateUncertaintyVisibility(
  confidenceTier: string,
  uncertaintyVisible: boolean,
  confidenceFraming: string | null
): ContractViolation | null {
  if (confidenceTier !== 'high') {
    if (!uncertaintyVisible) {
      return {
        invariant: 'C2_UNCERTAINTY_VISIBILITY',
        section: 'C',
        severity: 'critical',
        message: 'Uncertainty must be visible when confidence is not high',
        context: { confidenceTier, uncertaintyVisible },
      };
    }
    if (!confidenceFraming || confidenceFraming.length === 0) {
      return {
        invariant: 'C2_CONFIDENCE_FRAMING',
        section: 'C',
        severity: 'critical',
        message: 'Confidence framing must be present when confidence is not high',
        context: { confidenceTier, confidenceFraming },
      };
    }
  }
  return null;
}

/**
 * C3: Validates time-bound language is present
 */
export function validateTimeBoundLanguage(
  narrativeText: string
): ContractViolation | null {
  const lowerText = narrativeText.toLowerCase();
  const hasTimeBound = NARRATIVE_INVARIANTS.TIME_BOUND_INDICATORS.some(
    indicator => lowerText.includes(indicator.toLowerCase())
  );
  
  if (!hasTimeBound) {
    return {
      invariant: 'C3_TIME_BOUND',
      section: 'C',
      severity: 'warning',
      message: 'Narrative should contain time-bound language',
      context: { requiredIndicators: NARRATIVE_INVARIANTS.TIME_BOUND_INDICATORS },
    };
  }
  
  return null;
}

/**
 * C4: Validates agency is preserved in reflection prompt
 */
export function validateAgencyPreservation(
  reflectionPrompt: string
): ContractViolation | null {
  const lowerText = reflectionPrompt.toLowerCase();
  
  // Check for anti-agency words
  for (const word of NARRATIVE_INVARIANTS.ANTI_AGENCY_WORDS) {
    if (lowerText.includes(word)) {
      return {
        invariant: 'C4_AGENCY_VIOLATION',
        section: 'C',
        severity: 'critical',
        message: `Reflection prompt contains anti-agency language: "${word}"`,
        context: { reflectionPrompt, violatingWord: word },
      };
    }
  }
  
  return null;
}

/**
 * C5: Validates cross-lens context presence matches adjustment state
 */
export function validateCrossLensContextPresence(
  adjustmentApplied: boolean,
  crossLensContext: string | null
): ContractViolation | null {
  if (!adjustmentApplied && crossLensContext !== null) {
    return {
      invariant: 'C5_CONTEXT_WITHOUT_ADJUSTMENT',
      section: 'C',
      severity: 'warning',
      message: 'Cross-lens context should be null when no adjustment was applied',
      context: { adjustmentApplied, hasContext: crossLensContext !== null },
    };
  }
  
  if (adjustmentApplied && (crossLensContext === null || crossLensContext.length === 0)) {
    return {
      invariant: 'C5_MISSING_CONTEXT',
      section: 'C',
      severity: 'warning',
      message: 'Cross-lens context should be present when adjustment was applied',
      context: { adjustmentApplied, crossLensContext },
    };
  }
  
  return null;
}

// ============================================
// FULL CONTRACT VALIDATION
// ============================================

export interface FullValidationInput {
  // Enneagram data
  wingState: string | null;
  confidenceTier: string;
  typeProbabilities: Record<string, number>;
  
  // Cross-lens data
  adjustmentApplied: boolean;
  adjustments?: Record<string, number>;
  top2Gap?: number;
  assessmentDepth?: string;
  longitudinalSignals?: boolean;
  enneagramRaw?: unknown;
  enneagramAdjusted?: unknown;
  
  // Narrative data
  narrative?: {
    patternSummary?: string;
    confidenceFraming?: string;
    crossLensContext?: string | null;
    reflectionPrompt?: string;
  };
  uncertaintyVisible?: boolean;
}

/**
 * Validates all V1 contract invariants
 */
export function validateV1Contract(
  input: FullValidationInput
): ContractValidationResult {
  const violations: ContractViolation[] = [];
  
  // Section A: Enneagram Integrity
  const wingViolation = validateWingDisplay(input.wingState);
  if (wingViolation) violations.push(wingViolation);
  
  const highConfViolation = validateHighConfidenceLock(
    input.confidenceTier,
    input.adjustmentApplied
  );
  if (highConfViolation) violations.push(highConfViolation);
  
  const probViolation = validateProbabilitySum(input.typeProbabilities);
  if (probViolation) violations.push(probViolation);
  
  // Section B: Cross-Lens Guardrails
  if (input.adjustmentApplied) {
    const eligibilityViolation = validateCrossLensEligibility(
      input.confidenceTier,
      input.top2Gap || 0,
      input.assessmentDepth || 'short',
      input.longitudinalSignals || false,
      input.adjustmentApplied
    );
    if (eligibilityViolation) violations.push(eligibilityViolation);
    
    if (input.adjustments) {
      violations.push(...validateAdjustmentBounds(input.adjustments));
    }
  }
  
  const rawViolation = validateRawPreservation(
    input.enneagramRaw,
    input.adjustmentApplied,
    input.enneagramAdjusted
  );
  if (rawViolation) violations.push(rawViolation);
  
  // Section C: Narrative Language
  if (input.narrative) {
    const fullNarrative = [
      input.narrative.patternSummary,
      input.narrative.confidenceFraming,
      input.narrative.crossLensContext,
      input.narrative.reflectionPrompt,
    ].filter(Boolean).join(' ');
    
    violations.push(...validateNarrativeLanguage(fullNarrative));
    
    const uncertaintyViolation = validateUncertaintyVisibility(
      input.confidenceTier,
      input.uncertaintyVisible ?? true,
      input.narrative.confidenceFraming || null
    );
    if (uncertaintyViolation) violations.push(uncertaintyViolation);
    
    const timeBoundViolation = validateTimeBoundLanguage(fullNarrative);
    if (timeBoundViolation) violations.push(timeBoundViolation);
    
    if (input.narrative.reflectionPrompt) {
      const agencyViolation = validateAgencyPreservation(input.narrative.reflectionPrompt);
      if (agencyViolation) violations.push(agencyViolation);
    }
    
    const contextViolation = validateCrossLensContextPresence(
      input.adjustmentApplied,
      input.narrative.crossLensContext ?? null
    );
    if (contextViolation) violations.push(contextViolation);
  }
  
  return {
    valid: violations.filter(v => v.severity === 'critical').length === 0,
    violations,
    contractVersion: MIRROR_V1_CONTRACT_VERSION,
  };
}

// ============================================
// DEBUG LOGGING
// ============================================

const IS_DEBUG = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

/**
 * Logs contract violations in DEBUG_MIRROR mode
 */
export function logContractViolation(violation: ContractViolation): void {
  if (!IS_DEBUG) return;
  
  const prefix = violation.severity === 'critical' 
    ? '🚨 [CONTRACT CRITICAL]' 
    : '⚠️ [CONTRACT WARNING]';
  
  console.warn(
    `${prefix} ${violation.invariant}: ${violation.message}`,
    violation.context
  );
}

/**
 * Validates and logs any violations (DEBUG_MIRROR only)
 */
export function assertContract(input: FullValidationInput): ContractValidationResult {
  const result = validateV1Contract(input);
  
  if (IS_DEBUG) {
    for (const violation of result.violations) {
      logContractViolation(violation);
    }
    
    if (!result.valid) {
      console.error(
        `🚨 [CONTRACT FAILED] V1 Integrity Contract violated with ${result.violations.filter(v => v.severity === 'critical').length} critical violations`
      );
    }
  }
  
  return result;
}
