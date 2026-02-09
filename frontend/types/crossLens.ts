/**
 * Cross-Lens Bayesian Weighting Types
 * 
 * TypeScript type definitions for Astrology + Human Design as soft priors to Enneagram.
 * Aligned with JSON schema in /data/cross_lens_schema.json
 */

// ============================================
// ENUMS AND BASIC TYPES
// ============================================

export type CrossLensSource = 'astrology' | 'human_design';

export type EnneagramType = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type EnneagramTypeString = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9';

export type ConfidenceTier = 'high' | 'moderate' | 'low';

// ============================================
// ASTROLOGY SIGNALS
// ============================================

export type AstrologySignalName =
  | 'saturn_dominance'
  | 'jupiter_dominance'
  | 'mars_dominance'
  | 'moon_saturn_hard_aspect'
  | 'moon_jupiter_aspect'
  | 'heavy_mutable_emphasis'
  | 'heavy_fixed_emphasis'
  | 'angular_planets'
  | '12th_house_emphasis'
  | '8th_house_emphasis'
  | 'pluto_dominance'
  | 'neptune_dominance'
  | 'uranus_dominance'
  | 'venus_dominance'
  | 'mercury_dominance';

// ============================================
// HUMAN DESIGN SIGNALS
// ============================================

export type HumanDesignSignalName =
  | 'defined_head_ajna'
  | 'undefined_head_ajna'
  | 'defined_root'
  | 'undefined_root'
  | 'emotional_authority'
  | 'splenic_authority'
  | 'sacral_authority'
  | 'self_projected_authority'
  | 'ego_authority'
  | 'manifestor_type'
  | 'generator_type'
  | 'manifesting_generator_type'
  | 'projector_type'
  | 'reflector_type'
  | 'defined_solar_plexus'
  | 'undefined_solar_plexus'
  | 'defined_sacral'
  | 'undefined_sacral'
  | 'defined_spleen'
  | 'undefined_spleen'
  | 'defined_heart_ego'
  | 'undefined_heart_ego'
  | 'defined_throat'
  | 'defined_g_center'
  | 'undefined_g_center';

export type HumanDesignType = 
  | 'Manifestor' 
  | 'Generator' 
  | 'Manifesting Generator' 
  | 'Projector' 
  | 'Reflector';

export type HumanDesignAuthority =
  | 'Emotional'
  | 'Sacral'
  | 'Splenic'
  | 'Ego'
  | 'Self-Projected'
  | 'Mental'
  | 'Lunar';

// ============================================
// INPUT STRUCTURES
// ============================================

export interface Signal {
  name: string;
  strength: number; // 0.0 - 1.0
  description?: string;
}

export interface AstrologySignal extends Signal {
  name: AstrologySignalName;
}

export interface HumanDesignSignal extends Signal {
  name: HumanDesignSignalName;
}

export interface AstrologyInput {
  available: boolean;
  signals?: AstrologySignal[];
  computed_at?: string; // ISO8601
}

export interface HumanDesignInput {
  available: boolean;
  signals?: HumanDesignSignal[];
  type?: HumanDesignType;
  authority?: HumanDesignAuthority;
  computed_at?: string; // ISO8601
}

export interface CrossLensInput {
  user_id?: string;
  astrology?: AstrologyInput;
  human_design?: HumanDesignInput;
  longitudinal_signals?: boolean;
}

// ============================================
// TYPE PROBABILITIES
// ============================================

export type TypeProbabilities = {
  [K in EnneagramTypeString]: number;
};

export type TypeAdjustments = {
  [K in EnneagramTypeString]?: number;
};

// ============================================
// ELIGIBILITY
// ============================================

export interface EligibilityResult {
  eligible: boolean;
  reason?: string;
  confidence_tier?: ConfidenceTier;
  top_2_gap?: number;
  assessment_depth?: 'short' | 'deep';
  cross_lens_sources?: CrossLensSource[];
}

// ============================================
// ADJUSTMENT DETAILS
// ============================================

export interface AdjustmentDetails {
  astrology_adjustments?: TypeAdjustments;
  human_design_adjustments?: TypeAdjustments;
  combined_adjustments?: TypeAdjustments;
  total_redistribution?: number; // Max 0.10
}

// ============================================
// ENNEAGRAM RESULT
// ============================================

export interface TypeCandidate {
  type: EnneagramType;
  probability: number;
}

export interface EnneagramResult {
  type_probabilities: TypeProbabilities;
  top_types: TypeCandidate[];
  confidence_tier: ConfidenceTier;
}

// ============================================
// CROSS-LENS ADJUSTMENT RESULT
// ============================================

export interface CrossLensAdjustmentResult {
  user_id: string;
  computed_at: string; // ISO8601
  
  eligibility: EligibilityResult;
  
  enneagram_raw: EnneagramResult;
  
  adjustment_applied: boolean;
  
  adjustment_details?: AdjustmentDetails;
  
  enneagram_adjusted?: EnneagramResult;
  
  adjustment_sources: CrossLensSource[];
  
  adjustment_rationale: string[];
  
  narrative_hint: string | null;
  
  metadata?: {
    version: string;
    constraints_applied: {
      per_type_bounded: boolean;
      total_redistribution_bounded: boolean;
      renormalized: boolean;
    };
  };
}

// ============================================
// SIGNAL AFFINITY MAPPING
// ============================================

export interface SignalAffinityMapping {
  signal_name: string;
  signal_source: CrossLensSource;
  affinities: { [key: string]: number }; // Type string -> affinity weight (0-1)
  notes?: string;
}

// ============================================
// CONSTRAINTS CONFIGURATION
// ============================================

export interface CrossLensConstraints {
  /** Maximum ±adjustment for any single type (default: 0.05) */
  max_adjustment_per_type: number;
  
  /** Maximum total probability mass movement (default: 0.10) */
  max_total_redistribution: number;
  
  /** Only adjust when top-2 gap is at or below this (default: 0.12) */
  top_2_gap_threshold: number;
  
  /** No type probability can go below this (default: 0.001) */
  min_probability_floor: number;
  
  /** Maximum contribution from a single signal (default: 0.025) */
  max_signal_contribution: number;
  
  /** Ignore signals below this strength (default: 0.3) */
  signal_strength_threshold: number;
  
  /** Multiplier when multiple lenses agree (default: 1.2) */
  concordance_bonus: number;
}

export const DEFAULT_CONSTRAINTS: CrossLensConstraints = {
  max_adjustment_per_type: 0.05,
  max_total_redistribution: 0.10,
  top_2_gap_threshold: 0.12,
  min_probability_floor: 0.001,
  max_signal_contribution: 0.025,
  signal_strength_threshold: 0.3,
  concordance_bonus: 1.2,
};

// ============================================
// DISALLOWED BEHAVIORS (TYPE GUARDS)
// ============================================

/**
 * Validates that an adjustment doesn't exceed per-type bounds
 */
export function isAdjustmentBounded(
  adjustment: number, 
  constraints: CrossLensConstraints = DEFAULT_CONSTRAINTS
): boolean {
  return Math.abs(adjustment) <= constraints.max_adjustment_per_type;
}

/**
 * Validates that total redistribution doesn't exceed bounds
 */
export function isTotalRedistributionBounded(
  adjustments: TypeAdjustments,
  constraints: CrossLensConstraints = DEFAULT_CONSTRAINTS
): boolean {
  const total = Object.values(adjustments).reduce(
    (sum, adj) => sum + Math.abs(adj || 0), 
    0
  ) / 2; // Divide by 2 because it's zero-sum
  return total <= constraints.max_total_redistribution;
}

/**
 * Validates that high confidence results are not adjusted
 */
export function canApplyAdjustment(
  confidenceTier: ConfidenceTier,
  top2Gap: number,
  constraints: CrossLensConstraints = DEFAULT_CONSTRAINTS
): boolean {
  if (confidenceTier === 'high') return false;
  if (top2Gap > constraints.top_2_gap_threshold) return false;
  return true;
}

// ============================================
// LANGUAGE VALIDATION
// ============================================

const FORBIDDEN_PHRASES = [
  'confirms',
  'proves',
  'determines',
  'means you are',
  'shows that your type is',
  'your chart says',
  'your design proves',
  'definitely',
  'certainly',
  'without doubt',
];

const ALLOWED_PHRASES = [
  'gently supports',
  'aligns with',
  'resonates with',
  'points in a similar direction',
  'suggests themes of',
  'may relate to',
  'echoes patterns of',
];

/**
 * Validates that narrative text uses soft, non-authoritative language
 */
export function isValidNarrativeLanguage(text: string): boolean {
  const lowerText = text.toLowerCase();
  for (const forbidden of FORBIDDEN_PHRASES) {
    if (lowerText.includes(forbidden)) {
      return false;
    }
  }
  return true;
}

// ============================================
// NARRATIVE TEMPLATES
// ============================================

export const NARRATIVE_TEMPLATES = {
  /** When cross-lens supports top type */
  supports_top: (type: number) => 
    `Multiple perspectives point in a similar direction. Your assessment suggests Type ${type} patterns, and other lenses gently support this theme—though all of these remain exploratory.`,
  
  /** When cross-lens is mixed */
  mixed_signals: (type: number) => 
    `Different lenses highlight different facets. Your Enneagram assessment leans toward Type ${type}, while other perspectives illuminate additional patterns. This complexity is normal and often meaningful.`,
  
  /** When cross-lens was not applied */
  not_applied: () => 
    `Your Enneagram result carries sufficient clarity that additional weighting wasn't applied. The patterns speak for themselves.`,
  
  /** When blocked due to high confidence */
  high_confidence_blocked: () => 
    `Your Enneagram result carries sufficient clarity that additional perspectives weren't needed to refine it.`,
};

// ============================================
// ASTROLOGY SIGNAL AFFINITIES (PLACEHOLDER VALUES)
// ============================================

export const ASTROLOGY_AFFINITIES: Record<AstrologySignalName, Partial<Record<EnneagramTypeString, number>>> = {
  saturn_dominance: { '6': 0.6, '1': 0.3, '4': 0.1 },
  jupiter_dominance: { '7': 0.5, '3': 0.3, '9': 0.2 },
  mars_dominance: { '8': 0.6, '3': 0.2, '1': 0.2 },
  moon_saturn_hard_aspect: { '6': 0.4, '4': 0.4, '5': 0.2 },
  moon_jupiter_aspect: { '7': 0.4, '2': 0.3, '9': 0.3 },
  heavy_mutable_emphasis: { '7': 0.4, '6': 0.3, '3': 0.3 },
  heavy_fixed_emphasis: { '8': 0.3, '4': 0.3, '1': 0.2, '5': 0.2 },
  angular_planets: { '3': 0.4, '8': 0.3, '1': 0.3 },
  '12th_house_emphasis': { '9': 0.4, '4': 0.3, '5': 0.3 },
  '8th_house_emphasis': { '4': 0.4, '8': 0.3, '5': 0.3 },
  pluto_dominance: { '8': 0.5, '4': 0.3, '6': 0.2 },
  neptune_dominance: { '9': 0.4, '4': 0.3, '2': 0.3 },
  uranus_dominance: { '5': 0.4, '7': 0.3, '4': 0.3 },
  venus_dominance: { '2': 0.4, '4': 0.3, '9': 0.3 },
  mercury_dominance: { '5': 0.4, '3': 0.3, '7': 0.3 },
};

// ============================================
// HUMAN DESIGN SIGNAL AFFINITIES (PLACEHOLDER VALUES)
// ============================================

export const HUMAN_DESIGN_AFFINITIES: Record<HumanDesignSignalName, Partial<Record<EnneagramTypeString, number>>> = {
  defined_head_ajna: { '5': 0.5, '6': 0.3, '1': 0.2 },
  undefined_head_ajna: { '7': 0.4, '9': 0.3, '6': 0.3 },
  defined_root: { '3': 0.4, '8': 0.3, '1': 0.3 },
  undefined_root: { '9': 0.4, '7': 0.3, '4': 0.3 },
  emotional_authority: { '4': 0.5, '2': 0.3, '6': 0.2 },
  splenic_authority: { '8': 0.4, '6': 0.3, '1': 0.3 },
  sacral_authority: { '9': 0.4, '2': 0.3, '3': 0.3 },
  self_projected_authority: { '4': 0.4, '3': 0.3, '5': 0.3 },
  ego_authority: { '3': 0.4, '8': 0.4, '2': 0.2 },
  manifestor_type: { '8': 0.6, '3': 0.2, '1': 0.2 },
  generator_type: { '9': 0.4, '2': 0.3, '3': 0.3 },
  manifesting_generator_type: { '7': 0.4, '3': 0.3, '8': 0.3 },
  projector_type: { '5': 0.4, '4': 0.3, '2': 0.3 },
  reflector_type: { '9': 0.6, '4': 0.2, '7': 0.2 },
  defined_solar_plexus: { '4': 0.4, '2': 0.3, '8': 0.3 },
  undefined_solar_plexus: { '9': 0.4, '7': 0.3, '5': 0.3 },
  defined_sacral: { '3': 0.3, '2': 0.3, '9': 0.2, '8': 0.2 },
  undefined_sacral: { '5': 0.4, '4': 0.3, '1': 0.3 },
  defined_spleen: { '8': 0.4, '6': 0.3, '3': 0.3 },
  undefined_spleen: { '6': 0.5, '9': 0.3, '2': 0.2 },
  defined_heart_ego: { '3': 0.5, '8': 0.3, '2': 0.2 },
  undefined_heart_ego: { '9': 0.4, '4': 0.3, '2': 0.3 },
  defined_throat: { '3': 0.4, '8': 0.3, '7': 0.3 },
  defined_g_center: { '4': 0.4, '3': 0.3, '1': 0.3 },
  undefined_g_center: { '9': 0.4, '6': 0.3, '3': 0.3 },
};
