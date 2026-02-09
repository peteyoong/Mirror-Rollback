/**
 * Narrative Synthesis Layer Types
 * 
 * TypeScript definitions for the interpretive layer that translates
 * Enneagram results into human-readable, non-authoritative reflection.
 */

// ============================================
// INPUT TYPES
// ============================================

export type ConfidenceTier = 'low' | 'moderate' | 'high';
export type WingState = 'dominant' | 'leaning' | 'balanced' | 'not_clear';
export type AssessmentDepth = 'short' | 'deep';
export type CrossLensSource = 'astrology' | 'human_design';
export type NarrativeStyle = 'exploratory' | 'grounded' | 'settled';

export interface TypeProbabilities {
  '1': number;
  '2': number;
  '3': number;
  '4': number;
  '5': number;
  '6': number;
  '7': number;
  '8': number;
  '9': number;
}

export interface TopType {
  type: number;
  probability: number;
}

export interface EnneagramResultData {
  type_probabilities: TypeProbabilities;
  top_types: TopType[];
  confidence_tier: ConfidenceTier;
}

export interface NarrativeInput {
  // Core Enneagram data
  enneagram_raw: EnneagramResultData;
  enneagram_adjusted: EnneagramResultData | null;
  
  // Result metadata
  confidence_tier: ConfidenceTier;
  wing_state: WingState;
  inferred_core: number;
  inferred_wing: number | null;
  
  // Cross-lens context
  adjustment_applied: boolean;
  adjustment_rationale: string[];
  adjustment_sources: CrossLensSource[];
  
  // Assessment context
  assessment_depth: AssessmentDepth;
  longitudinal_signals: boolean;
  
  // Close-call data
  close_call: boolean;
  close_call_types?: number[];
}

// ============================================
// OUTPUT TYPES
// ============================================

export interface NarrativeSections {
  pattern_summary: string;
  confidence_framing: string;
  cross_lens_context: string | null;
  reflection_prompt: string;
}

export interface NarrativeOutput {
  narrative: NarrativeSections;
  narrative_style: NarrativeStyle;
  uncertainty_visible: boolean;
  template_used: string;
  input_scenario: string;
}

// ============================================
// TEMPLATE TYPES
// ============================================

export type TemplateScenario = 
  | 'low_short'
  | 'low_deep'
  | 'moderate_short'
  | 'moderate_deep'
  | 'moderate_deep_crosslens'
  | 'high_any'
  | 'wing_not_clear'
  | 'wing_balanced';

export interface NarrativeTemplate {
  scenario: TemplateScenario;
  pattern_summary: string;
  confidence_framing: string;
  cross_lens_context: string | null;
  reflection_prompt: string;
  narrative_style: NarrativeStyle;
}

// ============================================
// THEME DATA
// ============================================

export interface TypeTheme {
  type: number;
  name: string;
  core_theme: string;
  motivation_hint: string;
  wing_left: number;
  wing_right: number;
  wing_left_theme: string;
  wing_right_theme: string;
}

export const TYPE_THEMES: TypeTheme[] = [
  {
    type: 1,
    name: 'The Perfectionist',
    core_theme: 'improvement and getting things right',
    motivation_hint: 'a drive toward integrity and correctness',
    wing_left: 9,
    wing_right: 2,
    wing_left_theme: 'acceptance and calm',
    wing_right_theme: 'helpfulness and warmth',
  },
  {
    type: 2,
    name: 'The Helper',
    core_theme: 'connection and being needed',
    motivation_hint: 'a need to be valued through caring',
    wing_left: 1,
    wing_right: 3,
    wing_left_theme: 'principled service',
    wing_right_theme: 'charming achievement',
  },
  {
    type: 3,
    name: 'The Achiever',
    core_theme: 'achievement and recognition',
    motivation_hint: 'a drive to succeed and be seen as valuable',
    wing_left: 2,
    wing_right: 4,
    wing_left_theme: 'relational warmth',
    wing_right_theme: 'authentic depth',
  },
  {
    type: 4,
    name: 'The Individualist',
    core_theme: 'depth and authentic self-expression',
    motivation_hint: 'a longing for significance and identity',
    wing_left: 3,
    wing_right: 5,
    wing_left_theme: 'adaptive presentation',
    wing_right_theme: 'intellectual withdrawal',
  },
  {
    type: 5,
    name: 'The Investigator',
    core_theme: 'understanding and preserving energy',
    motivation_hint: 'a need to observe and comprehend',
    wing_left: 4,
    wing_right: 6,
    wing_left_theme: 'emotional depth',
    wing_right_theme: 'loyal skepticism',
  },
  {
    type: 6,
    name: 'The Loyalist',
    core_theme: 'security and anticipating what\'s ahead',
    motivation_hint: 'a drive toward safety and preparedness',
    wing_left: 5,
    wing_right: 7,
    wing_left_theme: 'analytical caution',
    wing_right_theme: 'optimistic engagement',
  },
  {
    type: 7,
    name: 'The Enthusiast',
    core_theme: 'possibility and staying engaged',
    motivation_hint: 'a need for stimulation and freedom',
    wing_left: 6,
    wing_right: 8,
    wing_left_theme: 'loyal commitment',
    wing_right_theme: 'assertive intensity',
  },
  {
    type: 8,
    name: 'The Challenger',
    core_theme: 'strength and maintaining autonomy',
    motivation_hint: 'a drive to protect and control',
    wing_left: 7,
    wing_right: 9,
    wing_left_theme: 'expansive adventure',
    wing_right_theme: 'receptive groundedness',
  },
  {
    type: 9,
    name: 'The Peacemaker',
    core_theme: 'peace and avoiding disruption',
    motivation_hint: 'a need for harmony and stability',
    wing_left: 8,
    wing_right: 1,
    wing_left_theme: 'quiet strength',
    wing_right_theme: 'principled idealism',
  },
];

// Helper to get theme by type
export function getTypeTheme(type: number): TypeTheme | undefined {
  return TYPE_THEMES.find(t => t.type === type);
}

// ============================================
// LANGUAGE VALIDATION
// ============================================

export const BANNED_PHRASES = [
  // Identity declaration
  'you are a type',
  'this is your type',
  'you\'re definitely',
  'your personality is',
  // Causal / confirmatory
  'this confirms',
  'this proves',
  'your astrology shows',
  'your human design means',
  'this means you have',
  // Prescriptive
  'you should',
  'you need to',
  'try to',
  'work on',
  'you must',
  // Absolute / permanent
  'you will always',
  'you never',
  'this is permanent',
  'your destiny',
  // Diagnostic
  'diagnosis',
  'symptoms of',
  'treatment',
];

export const ALLOWED_REPLACEMENTS: Record<string, string> = {
  'you are a type': 'patterns appear in your responses',
  'this is your type': 'this pattern stands out',
  'you\'re definitely': 'this appears consistently',
  'your personality is': 'your responses suggest',
  'this confirms': 'this is consistent with',
  'this proves': 'this points toward',
  'your astrology shows': 'your chart echoes',
  'your human design means': 'your design resonates with',
  'you should': 'you might notice',
  'you need to': 'it may be worth observing',
  'try to': 'consider whether',
  'work on': 'pay attention to',
  'you will always': 'right now, this pattern',
  'you never': 'at this stage',
  'this is permanent': 'this is where you are now',
  'your destiny': 'this direction',
};

/**
 * Validates narrative text against banned phrases
 */
export function validateNarrativeLanguage(text: string): { valid: boolean; violations: string[] } {
  const lowerText = text.toLowerCase();
  const violations: string[] = [];
  
  for (const phrase of BANNED_PHRASES) {
    if (lowerText.includes(phrase.toLowerCase())) {
      violations.push(phrase);
    }
  }
  
  return {
    valid: violations.length === 0,
    violations,
  };
}

// ============================================
// REFLECTION PROMPTS
// ============================================

export const REFLECTION_PROMPTS = {
  // By confidence tier
  low: [
    'This may become clearer as you notice when this pattern shows up in your daily life.',
    'Consider what resonates — and what doesn\'t. That\'s information too.',
    'Patterns often clarify through reflection, not more questions.',
  ],
  moderate: [
    'You might notice when this pattern feels most active — and what happens when you\'re not in it.',
    'Notice whether this resonates in your lived experience — that\'s the real test.',
    'Pay attention to when this theme serves you, and when it might be worth questioning.',
  ],
  high: [
    'Pay attention to when this pattern serves you well — and when it might be worth softening.',
    'Notice how this shows up in different contexts — work, relationships, solitude.',
    'Consider when this lens feels like a strength, and when it might limit what you see.',
  ],
  
  // By wing state
  wing_not_clear: [
    'Notice which adjacent pattern — {wing_left_theme} or {wing_right_theme} — feels more familiar.',
    'Both wings are available to you. Observe which one you lean toward under pressure.',
    'Wing clarity often emerges from noticing, not deciding.',
  ],
  wing_balanced: [
    'Observe when you lean toward {wing_left_theme} versus {wing_right_theme}. The choice may be more conscious than you realize.',
    'Having access to both wings is range, not confusion. Notice what triggers each.',
    'Balance here means choice. Pay attention to which wing you reach for in different situations.',
  ],
  
  // By close call
  close_call: [
    'Observe which theme — {type_a_theme} or {type_b_theme} — feels more central to your experience.',
    'When two patterns are close, lived experience is the tiebreaker.',
    'Notice which of these themes you return to under stress. That often reveals the core.',
  ],
};

// ============================================
// SCENARIO DETECTION
// ============================================

export function determineScenario(input: NarrativeInput): TemplateScenario {
  // Wing variants take precedence
  if (input.wing_state === 'not_clear') return 'wing_not_clear';
  if (input.wing_state === 'balanced') return 'wing_balanced';
  
  // Then confidence + depth + cross-lens
  if (input.confidence_tier === 'high') return 'high_any';
  
  if (input.confidence_tier === 'moderate') {
    if (input.assessment_depth === 'deep' && input.adjustment_applied) {
      return 'moderate_deep_crosslens';
    }
    if (input.assessment_depth === 'deep') return 'moderate_deep';
    return 'moderate_short';
  }
  
  // Low confidence
  if (input.assessment_depth === 'deep') return 'low_deep';
  return 'low_short';
}

export function determineNarrativeStyle(
  confidenceTier: ConfidenceTier,
  assessmentDepth: AssessmentDepth
): NarrativeStyle {
  if (confidenceTier === 'high') return 'settled';
  if (confidenceTier === 'low') return 'exploratory';
  return 'grounded';
}
