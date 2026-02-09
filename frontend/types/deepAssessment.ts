/**
 * Enneagram Deep Assessment Types
 * 
 * TypeScript type definitions for the Deep Assessment system.
 * Aligned with JSON schema in /data/deep_assessment_schema.json
 */

// ============================================
// QUESTION TYPES
// ============================================

export type QuestionType = 'forced_choice' | 'likert' | 'ranked';

export type Dimension =
  | 'fear_response'
  | 'uncertainty_management'
  | 'stress_response'
  | 'anxiety_management'
  | 'achievement_motivation'
  | 'image_orientation'
  | 'withdrawal_pattern'
  | 'intensity_relationship'
  | 'control_need'
  | 'autonomy_drive'
  | 'conflict_engagement'
  | 'authority_relationship'
  | 'connection_style'
  | 'identity_search'
  | 'avoidance_pattern';

export type EnneagramType = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;

// ============================================
// QUESTION STRUCTURES
// ============================================

export interface ForcedChoiceOption {
  id: 'A' | 'B';
  text: string;
  primary_type: EnneagramType;
  secondary_type: EnneagramType | null;
  weight: number;
}

export interface ForcedChoiceQuestion {
  id: string;
  type: 'forced_choice';
  section: number;
  stem: string;
  options: [ForcedChoiceOption, ForcedChoiceOption];
  pair_focus: string[];
  dimension: Dimension;
}

export interface LikertScale {
  min: 1;
  max: 5;
  labels: [string, string, string, string, string];
}

export interface LikertScoring {
  primary_type: EnneagramType;
  secondary_type: EnneagramType | null;
  direction: 'positive' | 'negative';
  weight: number;
}

export interface LikertQuestion {
  id: string;
  type: 'likert';
  section: number;
  stem: string;
  scale: LikertScale;
  scoring: LikertScoring;
  pair_focus: string[];
  dimension: Dimension;
}

export interface RankedOption {
  id: 'A' | 'B' | 'C';
  text: string;
  primary_type: EnneagramType;
  weight_multipliers: {
    rank_1: number;
    rank_2: number;
    rank_3: number;
  };
}

export interface RankedQuestion {
  id: string;
  type: 'ranked';
  section: number;
  stem: string;
  options: [RankedOption, RankedOption, RankedOption];
  pair_focus: string[];
  dimension: Dimension;
}

export type DeepAssessmentQuestion =
  | ForcedChoiceQuestion
  | LikertQuestion
  | RankedQuestion;

// ============================================
// RESPONSE TYPES
// ============================================

export interface ForcedChoiceResponse {
  question_id: string;
  question_type: 'forced_choice';
  response: 'A' | 'B';
  response_time_ms?: number;
  section: number;
}

export interface LikertResponse {
  question_id: string;
  question_type: 'likert';
  response: 1 | 2 | 3 | 4 | 5;
  response_time_ms?: number;
  section: number;
}

export interface RankedResponse {
  question_id: string;
  question_type: 'ranked';
  response: ['A' | 'B' | 'C', 'A' | 'B' | 'C', 'A' | 'B' | 'C'];
  response_time_ms?: number;
  section: number;
}

export type DeepAssessmentResponse =
  | ForcedChoiceResponse
  | LikertResponse
  | RankedResponse;

// ============================================
// SESSION STATE
// ============================================

export interface StateCalibration {
  energy_state: 'low' | 'neutral' | 'high';
  life_context: 'surviving' | 'managing' | 'expanding';
  answer_frame: 'best_self' | 'recent_self';
}

export interface DeepAssessmentSession {
  assessment_id: string;
  user_id: string;
  assessment_type: 'deep';
  version: string;
  started_at: string; // ISO8601
  completed_at: string | null;
  state_calibration?: StateCalibration;
  responses: DeepAssessmentResponse[];
}

// ============================================
// SCORING OUTPUT
// ============================================

export type TypeProbabilities = {
  [K in '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9']: number;
};

export type WingState = 'dominant' | 'leaning' | 'balanced' | 'not_clear';

export type ConfidenceTier = 'high' | 'moderate' | 'low';

export interface TypeCandidate {
  type: EnneagramType;
  probability: number;
}

export interface TypeDiscrimination {
  leaning: EnneagramType;
  confidence: number;
  key_differentiators: Dimension[];
}

export interface ConfidenceFactors {
  response_consistency: number;
  pair_discrimination: number;
  top_type_separation: number;
}

export interface Confidence {
  tier: ConfidenceTier;
  score: number;
  factors?: ConfidenceFactors;
}

export interface WingScores {
  [key: string]: number;
}

export interface WingAnalysis {
  core_type: EnneagramType;
  adjacent_types: [EnneagramType, EnneagramType];
  wing_scores: WingScores;
  wing_state: WingState;
  inferred_wing: EnneagramType | null;
  wing_confidence: number;
}

export interface Phase1Integration {
  phase1_top_type: EnneagramType;
  phase1_confidence: number;
  type_shift: boolean;
  shift_explanation?: string;
}

export interface ScoringMetadata {
  questions_answered: number;
  avg_response_time_ms: number;
  sections_completed: number;
  flagged_inconsistencies: string[];
}

export interface DeepAssessmentScoringResult {
  assessment_id: string;
  user_id: string;
  assessment_depth: 'deep';
  computed_at: string; // ISO8601
  
  type_probabilities: TypeProbabilities;
  top_types: TypeCandidate[];
  
  type_discrimination?: {
    [key: string]: TypeDiscrimination;
  };
  
  confidence: Confidence;
  wing_analysis: WingAnalysis;
  
  integration_with_phase1?: Phase1Integration;
  metadata?: ScoringMetadata;
}

// ============================================
// COMBINED RESULT (Phase 1 + Phase 2)
// ============================================

export interface FinalResult {
  inferred_core: EnneagramType;
  inferred_wing: EnneagramType | null;
  wing_state: WingState;
  confidence_tier: ConfidenceTier;
  confidence_score: number;
  assessment_depth: 'short' | 'deep';
}

export interface TopCandidate {
  type: EnneagramType;
  probability: number;
  name: string;
}

export interface DisplayConfig {
  type_label: string;
  type_name: string;
  confidence_badge: 'High' | 'Exploratory' | 'Low';
  helper_text: string | null;
}

export interface CombinedEnneagramResult {
  user_id: string;
  assessment_complete: boolean;
  
  final_result: FinalResult;
  type_probabilities: TypeProbabilities;
  top_candidates: TopCandidate[];
  
  close_call: boolean;
  close_call_types?: EnneagramType[];
  
  display: DisplayConfig;
  
  phase_data?: {
    phase1?: object; // Short assessment result
    phase2?: DeepAssessmentScoringResult;
  };
}

// ============================================
// FRONTEND STATE
// ============================================

export interface DeepAssessmentState {
  session_id: string;
  current_section: number;
  current_question_index: number;
  questions: DeepAssessmentQuestion[];
  responses: DeepAssessmentResponse[];
  started_at: string;
  estimated_time_remaining: number; // seconds
  section_intros_shown: number[];
  is_complete: boolean;
}

export interface DeepAssessmentProgress {
  section: number;
  total_sections: number;
  questions_in_section: number;
  current_question_in_section: number;
  estimated_minutes_remaining: number;
}

// ============================================
// API TYPES
// ============================================

export interface StartDeepAssessmentRequest {
  user_id: string;
  state_calibration?: StateCalibration;
}

export interface StartDeepAssessmentResponse {
  session_id: string;
  questions: DeepAssessmentQuestion[];
  section_intros: { [key: string]: string };
  estimated_duration_minutes: number;
}

export interface SubmitDeepAssessmentRequest {
  session_id: string;
  responses: DeepAssessmentResponse[];
}

export interface SubmitDeepAssessmentResponse {
  success: boolean;
  result: CombinedEnneagramResult;
}

// ============================================
// SECTION CONFIGURATION
// ============================================

export interface SectionConfig {
  id: number;
  name: string;
  intro_text: string;
  primary_pairs: string[];
  question_count: number;
}

export const SECTION_CONFIGS: SectionConfig[] = [
  {
    id: 1,
    name: 'Fear & Security',
    intro_text: 'These questions explore how you respond when things feel uncertain or potentially threatening.',
    primary_pairs: ['6↔7', '6↔9'],
    question_count: 5,
  },
  {
    id: 2,
    name: 'Achievement & Image',
    intro_text: 'Now we\'ll look at patterns around achievement, recognition, and how you present yourself.',
    primary_pairs: ['3↔7', '3↔8'],
    question_count: 5,
  },
  {
    id: 3,
    name: 'Withdrawal & Intensity',
    intro_text: 'The following questions explore your relationship with intensity, withdrawal, and inner experience.',
    primary_pairs: ['4↔5', '5↔9'],
    question_count: 5,
  },
  {
    id: 4,
    name: 'Control & Autonomy',
    intro_text: 'These questions focus on control, autonomy, and how you assert yourself in the world.',
    primary_pairs: ['8↔1', '8↔2'],
    question_count: 5,
  },
  {
    id: 5,
    name: 'Anxiety & Optimism',
    intro_text: 'Now we\'ll explore patterns around anxiety, optimism, and how you manage discomfort.',
    primary_pairs: ['6↔7', '7↔9'],
    question_count: 5,
  },
  {
    id: 6,
    name: 'Identity & Authenticity',
    intro_text: 'The following questions look at identity, authenticity, and your sense of self.',
    primary_pairs: ['4↔3', '4↔9'],
    question_count: 5,
  },
  {
    id: 7,
    name: 'Authority & Trust',
    intro_text: 'These questions explore your relationship with authority, trust, and guidance.',
    primary_pairs: ['6↔8', '1↔6'],
    question_count: 5,
  },
  {
    id: 8,
    name: 'Connection & Independence',
    intro_text: 'Now we\'ll look at connection, independence, and how you relate to others.',
    primary_pairs: ['2↔9', '5↔8'],
    question_count: 5,
  },
  {
    id: 9,
    name: 'Stress Patterns',
    intro_text: 'Finally, these questions explore how you respond under stress and pressure.',
    primary_pairs: ['all'],
    question_count: 5,
  },
];

// ============================================
// TYPE NAMES (for display)
// ============================================

export const TYPE_NAMES: { [key: number]: string } = {
  1: 'The Perfectionist',
  2: 'The Helper',
  3: 'The Achiever',
  4: 'The Individualist',
  5: 'The Investigator',
  6: 'The Loyalist',
  7: 'The Enthusiast',
  8: 'The Challenger',
  9: 'The Peacemaker',
};
