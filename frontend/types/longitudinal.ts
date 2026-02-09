/**
 * Longitudinal Pattern Accumulation Types
 * 
 * V1-Safe types for evidence accumulation and confidence evolution.
 * This layer is ADDITIVE - it never modifies V1 frozen semantics.
 */

import { CROSS_LENS_INVARIANTS } from '../contracts/v1IntegrityContract';

// ============================================
// CONSTANTS (V1-INHERITED BOUNDS)
// ============================================

export const LONGITUDINAL_BOUNDS = {
  /** Max type affinity per single evidence event */
  MAX_AFFINITY_PER_EVENT: 0.03,
  
  /** Max per-type adjustment (same as cross-lens) */
  MAX_PER_TYPE_ADJUSTMENT: CROSS_LENS_INVARIANTS.MAX_ADJUSTMENT_PER_TYPE, // 0.05
  
  /** Max total redistribution (same as cross-lens) */
  MAX_TOTAL_REDISTRIBUTION: CROSS_LENS_INVARIANTS.MAX_TOTAL_REDISTRIBUTION, // 0.10
} as const;

export const LONGITUDINAL_THRESHOLDS = {
  /** Type stability threshold for upshift eligibility */
  STABILITY_HIGH: 0.75,
  
  /** Type stability threshold below which downshift may occur */
  STABILITY_LOW: 0.55,
  
  /** Top-1 frequency threshold for upshift */
  TOP1_DOMINANCE: 0.70,
  
  /** Wing stability threshold for state evolution */
  WING_CLARITY: 0.65,
  
  /** Minimum events for stability calculation */
  MIN_EVENTS_FOR_STABILITY: 3,
  
  /** Minimum events for confidence modifier */
  MIN_EVENTS_FOR_MODIFIER: 5,
  
  /** Recent window in days */
  RECENT_WINDOW_DAYS: 30,
  
  /** Stability window in events */
  STABILITY_WINDOW_EVENTS: 10,
} as const;

// ============================================
// ENUMS
// ============================================

export type EvidenceSource = 
  | 'reflection_chat' 
  | 'journal' 
  | 'enneagram_short' 
  | 'enneagram_deep';

export type StressStyle = 
  | 'vigilance'    // Type 6
  | 'reframing'    // Type 7
  | 'withdrawal'   // Type 5/4/9
  | 'control'      // Type 8/1
  | 'merging'      // Type 2/9
  | 'achieving'    // Type 3
  | 'other'
  | null;

export type AvoidanceStyle = 
  | 'uncertainty'    // Type 6
  | 'pain'           // Type 7
  | 'conflict'       // Type 9
  | 'limitation'     // Type 7/8
  | 'intensity'      // Type 5
  | 'rejection'      // Type 2/3
  | 'ordinariness'   // Type 4
  | 'weakness'       // Type 8
  | 'imperfection'   // Type 1
  | 'other'
  | null;

export type ConfidenceModifier = 'none' | 'upshift' | 'downshift';

export type RecommendedNextStep = 'none' | 'take_deep_assessment' | 'keep_observing';

// ============================================
// EVIDENCE EVENT
// ============================================

export interface EvidenceSignals {
  /** Type affinities: small nudges per event (bounded ±0.03) */
  type_affinities: Record<string, number>;
  
  /** Wing affinities for core type's adjacent wings */
  wing_affinities: Record<string, number>;
  
  /** Stress response pattern indicator */
  stress_style: StressStyle;
  
  /** Avoidance pattern indicator */
  avoidance_style: AvoidanceStyle;
  
  /** Signal confidence (0.0 - 1.0) */
  confidence_hint: number;
}

export interface LongitudinalEvidenceEvent {
  /** Unique event ID */
  event_id: string;
  
  /** User reference */
  user_id: string;
  
  /** When this evidence was recorded */
  created_at: string; // ISO8601
  
  /** Source of evidence */
  source: EvidenceSource;
  
  /** Reference to source record (optional) */
  source_id?: string;
  
  /** Derived signals */
  signals: EvidenceSignals;
  
  /** V1 compliance flag (always true) */
  v1_compliant: true;
}

// ============================================
// AGGREGATOR INPUT/OUTPUT
// ============================================

export interface AggregatorConfig {
  /** Time windows */
  recent_window_days: number;
  stability_window_events: number;
  
  /** Thresholds */
  stability_high_threshold: number;
  stability_low_threshold: number;
  top1_dominance_threshold: number;
  wing_clarity_threshold: number;
  
  /** V1-inherited bounds */
  max_total_adjustment: number;
  max_per_type_adjustment: number;
}

export const DEFAULT_AGGREGATOR_CONFIG: AggregatorConfig = {
  recent_window_days: LONGITUDINAL_THRESHOLDS.RECENT_WINDOW_DAYS,
  stability_window_events: LONGITUDINAL_THRESHOLDS.STABILITY_WINDOW_EVENTS,
  stability_high_threshold: LONGITUDINAL_THRESHOLDS.STABILITY_HIGH,
  stability_low_threshold: LONGITUDINAL_THRESHOLDS.STABILITY_LOW,
  top1_dominance_threshold: LONGITUDINAL_THRESHOLDS.TOP1_DOMINANCE,
  wing_clarity_threshold: LONGITUDINAL_THRESHOLDS.WING_CLARITY,
  max_total_adjustment: LONGITUDINAL_BOUNDS.MAX_TOTAL_REDISTRIBUTION,
  max_per_type_adjustment: LONGITUDINAL_BOUNDS.MAX_PER_TYPE_ADJUSTMENT,
};

export interface EvidenceVolumeStats {
  /** All-time event count */
  total: number;
  
  /** Events in last 30 days */
  last_30_days: number;
  
  /** Breakdown by source */
  sources: {
    reflection_chat: number;
    journal: number;
    enneagram_short: number;
    enneagram_deep: number;
  };
}

export interface TopTypeOverTime {
  type: number;
  share: number; // 0.0 - 1.0
}

export interface LongitudinalAdjustments {
  type_adjustments: Record<string, number>;
  total_redistribution: number;
  v1_bounded: boolean;
}

// ============================================
// LONGITUDINAL SUMMARY (OUTPUT CONTRACT)
// ============================================

export interface LongitudinalSummary {
  /** Feature flag */
  enabled: boolean;
  
  /** Type stability score (0.0 - 1.0) */
  type_stability: number;
  
  /** Wing stability score (0.0 - 1.0) */
  wing_stability: number;
  
  /** Evidence volume statistics */
  evidence_volume: EvidenceVolumeStats;
  
  /** Top types frequency over time */
  top_types_over_time: TopTypeOverTime[];
  
  /** Confidence modifier recommendation */
  confidence_modifier: ConfidenceModifier;
  
  /** Recommended next step for user */
  recommended_next_step: RecommendedNextStep;
  
  /** Adjustment data (for debugging) */
  adjustments?: LongitudinalAdjustments;
  
  /** When this summary was computed */
  computed_at: string; // ISO8601
  
  /** Evidence window used */
  evidence_window_days: number;
}

// ============================================
// COMBINED RESULT WITH LONGITUDINAL
// ============================================

export interface EnneagramResultWithLongitudinal {
  // Standard V1 fields (unchanged)
  inferred_core: number;
  inferred_wing: number | null;
  confidence_tier: 'low' | 'moderate' | 'high';
  wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
  type_probabilities: Record<string, number>;
  
  // Longitudinal enrichment (additive)
  longitudinal?: LongitudinalSummary;
  
  // Effective values (after longitudinal modifier applied)
  effective_confidence_tier: 'low' | 'moderate' | 'high';
  effective_wing_state: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
}

// ============================================
// THEME-TO-TYPE MAPPING
// ============================================

export const THEME_TYPE_AFFINITIES: Record<string, Record<string, number>> = {
  // Security/Trust themes
  'trust': { '6': 0.025, '9': 0.01 },
  'safety': { '6': 0.03, '5': 0.01 },
  'loyalty': { '6': 0.025, '2': 0.015 },
  'doubt': { '6': 0.03, '4': 0.01 },
  
  // Achievement themes
  'success': { '3': 0.03, '8': 0.01 },
  'recognition': { '3': 0.025, '2': 0.015 },
  'efficiency': { '3': 0.02, '1': 0.02 },
  'image': { '3': 0.03 },
  
  // Connection themes
  'helping': { '2': 0.03, '9': 0.01 },
  'relationships': { '2': 0.02, '6': 0.01, '9': 0.01 },
  'being_needed': { '2': 0.03 },
  
  // Depth/Authenticity themes
  'authenticity': { '4': 0.03, '5': 0.01 },
  'meaning': { '4': 0.025, '5': 0.015 },
  'uniqueness': { '4': 0.03 },
  'longing': { '4': 0.025, '9': 0.015 },
  
  // Knowledge themes
  'understanding': { '5': 0.03, '6': 0.01 },
  'observation': { '5': 0.025, '9': 0.015 },
  'privacy': { '5': 0.03 },
  'competence': { '5': 0.02, '3': 0.02 },
  
  // Freedom themes
  'freedom': { '7': 0.03, '8': 0.01 },
  'options': { '7': 0.025, '6': 0.015 },
  'excitement': { '7': 0.03 },
  'future': { '7': 0.025, '3': 0.015 },
  
  // Strength themes
  'control': { '8': 0.03, '1': 0.01 },
  'strength': { '8': 0.025, '3': 0.015 },
  'justice': { '8': 0.02, '1': 0.02 },
  'autonomy': { '8': 0.03, '5': 0.01 },
  
  // Peace themes
  'peace': { '9': 0.03, '2': 0.01 },
  'harmony': { '9': 0.025, '2': 0.015 },
  'stability': { '9': 0.02, '6': 0.02 },
  'comfort': { '9': 0.025, '7': 0.015 },
  
  // Integrity themes
  'improvement': { '1': 0.03, '3': 0.01 },
  'integrity': { '1': 0.025, '6': 0.015 },
  'responsibility': { '1': 0.02, '6': 0.02 },
  'standards': { '1': 0.03 },
};

export const STRESS_TYPE_AFFINITIES: Record<NonNullable<StressStyle>, Record<string, number>> = {
  'vigilance': { '6': 0.025 },
  'reframing': { '7': 0.025 },
  'withdrawal': { '5': 0.02, '4': 0.015, '9': 0.01 },
  'control': { '8': 0.02, '1': 0.015 },
  'merging': { '2': 0.02, '9': 0.015 },
  'achieving': { '3': 0.025 },
  'other': {},
};

export const AVOIDANCE_TYPE_AFFINITIES: Record<NonNullable<AvoidanceStyle>, Record<string, number>> = {
  'uncertainty': { '6': 0.025 },
  'pain': { '7': 0.025 },
  'conflict': { '9': 0.025 },
  'limitation': { '7': 0.015, '8': 0.015 },
  'intensity': { '5': 0.025 },
  'rejection': { '2': 0.015, '3': 0.015 },
  'ordinariness': { '4': 0.025 },
  'weakness': { '8': 0.025 },
  'imperfection': { '1': 0.025 },
  'other': {},
};

// ============================================
// SOURCE WEIGHTS
// ============================================

export const SOURCE_WEIGHTS: Record<EvidenceSource, number> = {
  'enneagram_deep': 1.0,
  'enneagram_short': 0.7,
  'reflection_chat': 0.5,
  'journal': 0.4,
};

// ============================================
// VALIDATION HELPERS
// ============================================

/**
 * Validates that type affinities respect bounds
 */
export function validateTypeAffinities(
  affinities: Record<string, number>
): { valid: boolean; violations: string[] } {
  const violations: string[] = [];
  
  for (const [type, value] of Object.entries(affinities)) {
    if (Math.abs(value) > LONGITUDINAL_BOUNDS.MAX_AFFINITY_PER_EVENT) {
      violations.push(
        `Type ${type} affinity (${value}) exceeds ±${LONGITUDINAL_BOUNDS.MAX_AFFINITY_PER_EVENT}`
      );
    }
  }
  
  return {
    valid: violations.length === 0,
    violations,
  };
}

/**
 * Validates that total adjustment respects V1 bounds
 */
export function validateTotalAdjustment(
  adjustments: Record<string, number>
): { valid: boolean; totalRedistribution: number } {
  const total = Object.values(adjustments).reduce(
    (sum, adj) => sum + Math.abs(adj), 0
  ) / 2;
  
  return {
    valid: total <= LONGITUDINAL_BOUNDS.MAX_TOTAL_REDISTRIBUTION,
    totalRedistribution: total,
  };
}

/**
 * Bounds adjustments to V1 limits
 */
export function boundAdjustments(
  adjustments: Record<string, number>
): Record<string, number> {
  const bounded: Record<string, number> = {};
  
  // Per-type bounds
  for (const [type, adj] of Object.entries(adjustments)) {
    bounded[type] = Math.max(
      -LONGITUDINAL_BOUNDS.MAX_PER_TYPE_ADJUSTMENT,
      Math.min(LONGITUDINAL_BOUNDS.MAX_PER_TYPE_ADJUSTMENT, adj)
    );
  }
  
  // Total redistribution bounds
  const { totalRedistribution } = validateTotalAdjustment(bounded);
  
  if (totalRedistribution > LONGITUDINAL_BOUNDS.MAX_TOTAL_REDISTRIBUTION) {
    const scale = LONGITUDINAL_BOUNDS.MAX_TOTAL_REDISTRIBUTION / totalRedistribution;
    for (const type of Object.keys(bounded)) {
      bounded[type] *= scale;
    }
  }
  
  return bounded;
}
