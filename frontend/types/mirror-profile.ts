/**
 * Mirror Profile & Experience Controls
 * 
 * This is the personalization layer that converts onboarding answers
 * into actionable experience controls throughout the app.
 * 
 * IMPORTANT: This does NOT affect deterministic compute logic for
 * astrology, human design, or numerology. This is purely an experience layer.
 */

// ============================================================
// MIRROR PROFILE - Raw user preferences from onboarding
// ============================================================

export type PrimaryGoal = 
  | 'self_understanding' 
  | 'emotional_clarity' 
  | 'perspective_during_change' 
  | 'quiet_reflection' 
  | 'not_sure';

export type UncertaintyStyle = 
  | 'meaning' 
  | 'stability' 
  | 'exploration' 
  | 'discomfort' 
  | 'depends';

export type DesiredDepth = 
  | 'light_grounding' 
  | 'thoughtful_simple' 
  | 'deep_exploratory' 
  | 'slow_step_by_step' 
  | 'not_sure';

export type SupportStyle = 
  | 'gentle_questions' 
  | 'clear_perspectives' 
  | 'emotional_reassurance' 
  | 'practical_grounding' 
  | 'dont_reflect_much';

export type CurrentSelfState = 
  | 'steady_grounded' 
  | 'curious_reflective' 
  | 'uncertain_searching' 
  | 'overwhelmed_stuck' 
  | 'hard_to_say';

export interface MirrorProfile {
  primary_goal: PrimaryGoal;
  uncertainty_style: UncertaintyStyle;
  desired_depth: DesiredDepth;
  support_style: SupportStyle;
  current_self_state: CurrentSelfState;
  onboarding_version: 'v1';
  updated_at: string;
}

// ============================================================
// EXPERIENCE CONTROLS - Derived from MirrorProfile
// ============================================================

export type Verbosity = 'low' | 'medium' | 'high';
export type Pacing = 'fast' | 'balanced' | 'progressive';
export type Tone = 'grounding' | 'balanced' | 'exploratory' | 'reassuring' | 'direct';
export type PromptStyle = 'questions' | 'perspectives' | 'reassurance' | 'action';
export type HomePriority = 'today' | 'signals' | 'journal' | 'lenses' | 'guided';
export type SignalVisibility = 'minimal' | 'standard' | 'expanded';

export interface ExperienceControls {
  verbosity: Verbosity;
  pacing: Pacing;
  tone: Tone;
  prompt_style: PromptStyle;
  home_priority: HomePriority;
  signal_visibility: SignalVisibility;
}

// ============================================================
// QUESTIONNAIRE ANSWER MAPPING
// ============================================================

// Maps questionnaire option text to profile values
export const QUESTIONNAIRE_MAPPING = {
  // Question 1: "How would you describe your relationship with yourself right now?"
  current_self_state: {
    "Steady and grounded": 'steady_grounded',
    "Curious and reflective": 'curious_reflective',
    "Uncertain or searching": 'uncertain_searching',
    "Overwhelmed or stuck": 'overwhelmed_stuck',
    "Hard to say right now": 'hard_to_say',
  } as Record<string, CurrentSelfState>,

  // Question 2: "When you pause to reflect, what usually helps most?"
  support_style: {
    "Gentle questions": 'gentle_questions',
    "Clear perspectives": 'clear_perspectives',
    "Emotional reassurance": 'emotional_reassurance',
    "Practical grounding": 'practical_grounding',
    "I don't reflect much": 'dont_reflect_much',
  } as Record<string, SupportStyle>,

  // Question 3: "How deep do you want this experience to go right now?"
  desired_depth: {
    "Light and grounding": 'light_grounding',
    "Thoughtful but simple": 'thoughtful_simple',
    "Deep and exploratory": 'deep_exploratory',
    "Slowly, step by step": 'slow_step_by_step',
    "I'm not sure": 'not_sure',
  } as Record<string, DesiredDepth>,

  // Question 4: "How do you usually relate to uncertainty?"
  uncertainty_style: {
    "I look for meaning": 'meaning',
    "I look for stability": 'stability',
    "I explore perspectives": 'exploration',
    "I feel uncomfortable with it": 'discomfort',
    "It depends": 'depends',
  } as Record<string, UncertaintyStyle>,

  // Question 5: "What are you hoping this space supports you with?"
  primary_goal: {
    "Self-understanding": 'self_understanding',
    "Emotional clarity": 'emotional_clarity',
    "Perspective during change": 'perspective_during_change',
    "Quiet reflection": 'quiet_reflection',
    "I'm not sure yet": 'not_sure',
  } as Record<string, PrimaryGoal>,
};

// ============================================================
// DERIVE EXPERIENCE CONTROLS FROM PROFILE
// ============================================================

export function deriveExperienceControls(profile: MirrorProfile): ExperienceControls {
  // Default controls
  let verbosity: Verbosity = 'medium';
  let pacing: Pacing = 'balanced';
  let tone: Tone = 'balanced';
  let prompt_style: PromptStyle = 'questions';
  let home_priority: HomePriority = 'today';
  let signal_visibility: SignalVisibility = 'standard';

  // ============================================================
  // 1. PRIMARY_GOAL → HOME_PRIORITY
  // ============================================================
  switch (profile.primary_goal) {
    case 'self_understanding':
      home_priority = 'lenses';
      break;
    case 'emotional_clarity':
      home_priority = 'journal';
      break;
    case 'perspective_during_change':
      home_priority = 'signals';
      break;
    case 'quiet_reflection':
      home_priority = 'guided';
      break;
    case 'not_sure':
    default:
      home_priority = 'today';
      break;
  }

  // ============================================================
  // 2. UNCERTAINTY_STYLE → TONE / INTERPRETIVE FRAMING
  // ============================================================
  switch (profile.uncertainty_style) {
    case 'meaning':
      tone = 'exploratory';
      break;
    case 'stability':
      tone = 'grounding';
      break;
    case 'exploration':
      tone = 'balanced';
      break;
    case 'discomfort':
      tone = 'reassuring';
      break;
    case 'depends':
    default:
      tone = 'balanced';
      break;
  }

  // ============================================================
  // 3. DESIRED_DEPTH → VERBOSITY, PACING, SIGNAL_VISIBILITY
  // ============================================================
  switch (profile.desired_depth) {
    case 'light_grounding':
      verbosity = 'low';
      pacing = 'fast';
      signal_visibility = 'minimal';
      break;
    case 'thoughtful_simple':
      verbosity = 'medium';
      pacing = 'balanced';
      signal_visibility = 'standard';
      break;
    case 'deep_exploratory':
      verbosity = 'high';
      pacing = 'balanced';
      signal_visibility = 'expanded';
      break;
    case 'slow_step_by_step':
      verbosity = 'medium';
      pacing = 'progressive';
      signal_visibility = 'standard';
      break;
    case 'not_sure':
    default:
      verbosity = 'medium';
      pacing = 'balanced';
      signal_visibility = 'standard';
      break;
  }

  // ============================================================
  // 4. SUPPORT_STYLE → PROMPT_STYLE
  // ============================================================
  switch (profile.support_style) {
    case 'gentle_questions':
      prompt_style = 'questions';
      break;
    case 'clear_perspectives':
      prompt_style = 'perspectives';
      break;
    case 'emotional_reassurance':
      prompt_style = 'reassurance';
      break;
    case 'practical_grounding':
      prompt_style = 'action';
      break;
    case 'dont_reflect_much':
    default:
      prompt_style = 'perspectives';
      break;
  }

  // ============================================================
  // 5. CURRENT_SELF_STATE → EMOTIONAL GUARDRAILS (modifies tone)
  // ============================================================
  switch (profile.current_self_state) {
    case 'overwhelmed_stuck':
      // Override to be more gentle and reassuring
      if (tone === 'exploratory') tone = 'balanced';
      if (verbosity === 'high') verbosity = 'medium';
      break;
    case 'uncertain_searching':
      // Slightly softer approach
      if (tone === 'direct') tone = 'balanced';
      break;
    case 'steady_grounded':
      // Can handle more direct/exploratory content
      if (tone === 'reassuring') tone = 'balanced';
      break;
    case 'curious_reflective':
      // Open to exploration
      if (signal_visibility === 'minimal') signal_visibility = 'standard';
      break;
    case 'hard_to_say':
    default:
      // Keep defaults
      break;
  }

  return {
    verbosity,
    pacing,
    tone,
    prompt_style,
    home_priority,
    signal_visibility,
  };
}

// ============================================================
// CONVERT QUESTIONNAIRE ANSWERS TO MIRROR PROFILE
// ============================================================

export function createMirrorProfileFromAnswers(answers: string[]): MirrorProfile {
  // Map answers to profile fields
  // Questionnaire order:
  // 0: current_self_state
  // 1: support_style
  // 2: desired_depth
  // 3: uncertainty_style
  // 4: primary_goal

  const current_self_state = QUESTIONNAIRE_MAPPING.current_self_state[answers[0]] || 'hard_to_say';
  const support_style = QUESTIONNAIRE_MAPPING.support_style[answers[1]] || 'gentle_questions';
  const desired_depth = QUESTIONNAIRE_MAPPING.desired_depth[answers[2]] || 'not_sure';
  const uncertainty_style = QUESTIONNAIRE_MAPPING.uncertainty_style[answers[3]] || 'depends';
  const primary_goal = QUESTIONNAIRE_MAPPING.primary_goal[answers[4]] || 'not_sure';

  return {
    primary_goal,
    uncertainty_style,
    desired_depth,
    support_style,
    current_self_state,
    onboarding_version: 'v1',
    updated_at: new Date().toISOString(),
  };
}

// ============================================================
// DEFAULT PROFILE (for users who skip onboarding)
// ============================================================

export const DEFAULT_MIRROR_PROFILE: MirrorProfile = {
  primary_goal: 'not_sure',
  uncertainty_style: 'depends',
  desired_depth: 'thoughtful_simple',
  support_style: 'gentle_questions',
  current_self_state: 'hard_to_say',
  onboarding_version: 'v1',
  updated_at: new Date().toISOString(),
};

export const DEFAULT_EXPERIENCE_CONTROLS: ExperienceControls = deriveExperienceControls(DEFAULT_MIRROR_PROFILE);

// ============================================================
// EXPERIENCE SUMMARY (for post-onboarding card)
// ============================================================

export interface ExperienceSummary {
  focus: string;
  style: string;
  in_uncertainty: string;
  what_helps: string;
}

export function getExperienceSummary(profile: MirrorProfile, controls: ExperienceControls): ExperienceSummary {
  // Focus (from primary_goal)
  const focusMap: Record<PrimaryGoal, string> = {
    'self_understanding': 'Understanding yourself more deeply',
    'emotional_clarity': 'Finding emotional clarity',
    'perspective_during_change': 'Gaining perspective during change',
    'quiet_reflection': 'Creating space for quiet reflection',
    'not_sure': 'Exploring what feels right',
  };

  // Style (from desired_depth + verbosity)
  const styleMap: Record<DesiredDepth, string> = {
    'light_grounding': 'Light and grounding',
    'thoughtful_simple': 'Thoughtful but simple',
    'deep_exploratory': 'Deep and exploratory',
    'slow_step_by_step': 'Gradual, step by step',
    'not_sure': 'Balanced and adaptive',
  };

  // In uncertainty (from uncertainty_style + tone)
  const uncertaintyMap: Record<UncertaintyStyle, string> = {
    'meaning': 'You look for meaning',
    'stability': 'You seek stability',
    'exploration': 'You explore different views',
    'discomfort': 'We\'ll go gently',
    'depends': 'We\'ll adapt as we go',
  };

  // What helps (from support_style)
  const helpsMap: Record<SupportStyle, string> = {
    'gentle_questions': 'Gentle questions that invite reflection',
    'clear_perspectives': 'Clear perspectives to consider',
    'emotional_reassurance': 'Reassurance and validation',
    'practical_grounding': 'Practical, grounding insights',
    'dont_reflect_much': 'Simple observations, no pressure',
  };

  return {
    focus: focusMap[profile.primary_goal],
    style: styleMap[profile.desired_depth],
    in_uncertainty: uncertaintyMap[profile.uncertainty_style],
    what_helps: helpsMap[profile.support_style],
  };
}

// ============================================================
// TONE TEMPLATES (for Today's Pattern, prompts, etc.)
// ============================================================

export interface ToneTemplates {
  pattern_opener: string;
  pattern_closer: string;
  reflection_prompt: string;
  signal_intro: string;
}

export function getToneTemplates(controls: ExperienceControls): ToneTemplates {
  const templates: Record<Tone, ToneTemplates> = {
    grounding: {
      pattern_opener: "Here's what's present today:",
      pattern_closer: "This is what's here. Nothing needs to change right now.",
      reflection_prompt: "If it feels right, notice what this brings up.",
      signal_intro: "What's active in your chart:",
    },
    balanced: {
      pattern_opener: "Today's pattern:",
      pattern_closer: "Something to notice, if you're curious.",
      reflection_prompt: "What does this bring up for you?",
      signal_intro: "Signals contributing to this:",
    },
    exploratory: {
      pattern_opener: "Something interesting is emerging:",
      pattern_closer: "There's more here if you want to look deeper.",
      reflection_prompt: "What questions does this spark?",
      signal_intro: "The layers underneath:",
    },
    reassuring: {
      pattern_opener: "You're noticing something:",
      pattern_closer: "Whatever you're feeling about this is valid.",
      reflection_prompt: "Take your time with this. What feels true?",
      signal_intro: "Some context that might help:",
    },
    direct: {
      pattern_opener: "Today's pattern:",
      pattern_closer: "Consider this as you move through your day.",
      reflection_prompt: "What will you do with this?",
      signal_intro: "Key signals:",
    },
  };

  return templates[controls.tone];
}

// ============================================================
// PROMPT STYLE TEMPLATES
// ============================================================

export function getPromptStyleTemplate(style: PromptStyle): string {
  const templates: Record<PromptStyle, string> = {
    questions: "What do you notice when you read this?",
    perspectives: "Here's another way to see this.",
    reassurance: "Whatever you're feeling right now is okay.",
    action: "What's one small thing you could do today?",
  };
  return templates[style];
}
