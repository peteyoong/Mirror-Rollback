/**
 * Mirror Response Engine v1
 * 
 * A unified response system that distributes the same underlying intelligence
 * across all product surfaces: Journal, Ask Mirror, Home, Reflect flows.
 * 
 * Core principle: ONE mind, multiple expressions.
 */

// ============================================
// RESPONSE CONTRACT
// ============================================

export interface MirrorResponse {
  recognition: string;           // "You already know..." - always first
  pattern: string;               // The core truth being surfaced
  choice?: string;               // Optional fork/decision framing
  practicalShift?: string;       // Optional behavioral nudge
  reflectionQuestion?: string;   // Optional journaling prompt
  lifeArea?: string;             // Where this shows up in life
  confidence: number;            // 0-100, how strong the signal
  sourceContext: SourceContext;  // Where the intelligence came from
  variationSeed: number;         // For selecting alternate wordings
}

export interface SourceContext {
  dominantTruth?: string;        // From v5 engine
  unifiedPattern?: string;       // From unified pattern engine
  chapter?: string;              // Life chapter if active
  activeLifeArea?: string;       // Current house/area focus
  journalThemes?: string[];      // Detected from journal history
  hasHistory?: boolean;          // Whether we have prior context
}

// Surface types for intensity calibration
export type MirrorSurface = 
  | 'home'        // Lightest - hook only
  | 'journal'     // Warm + seen - short
  | 'ask_mirror'  // Deeper + confronting
  | 'deep_dive'   // Most explicit / integrated
  | 'reflect';    // Question-focused

// Intensity levels
export type IntensityLevel = 'light' | 'warm' | 'direct' | 'confronting';

// ============================================
// VARIATION POOLS
// ============================================

// Recognition line variations - same truth, different words
const RECOGNITION_VARIATIONS: { [key: string]: string[] } = {
  overcommitment: [
    'You already know you\'re carrying too much.',
    'You feel it—the weight of saying yes to everything.',
    'This isn\'t new. You\'ve been here before.',
    'Something in you knows this pace isn\'t sustainable.',
  ],
  avoidance: [
    'You already know what you\'re avoiding.',
    'There\'s something you\'ve been circling around.',
    'You can feel it sitting there, waiting.',
    'The thing you\'re not looking at is getting louder.',
  ],
  premature_action: [
    'You move before you\'re ready—and you know it.',
    'The ground isn\'t stable yet, but you\'re already running.',
    'Waiting feels like weakness, so you don\'t.',
    'You\'ve done this before: act first, understand later.',
  ],
  delayed_decision: [
    'You already know which way you\'re leaning.',
    'The decision has been made; you just haven\'t admitted it.',
    'More information won\'t make this clearer.',
    'You\'re waiting for certainty that won\'t come.',
  ],
  emotional_suppression: [
    'You feel more than you show.',
    'There\'s something underneath that you\'re not letting through.',
    'You\'ve gotten good at containing this.',
    'The feelings are there—you\'re just not letting them land.',
  ],
  boundary_erosion: [
    'You give more ground than you realize.',
    'Each small yes costs more than it seems.',
    'You keep adjusting to make room for everyone else.',
    'Your needs keep getting pushed to the back of the line.',
  ],
  identity_confusion: [
    'You become what the situation requires.',
    'Different versions of you for different people.',
    'You\'re not sure which one is the real one anymore.',
    'You adapt so well that you\'ve lost your own shape.',
  ],
  relationship_strain: [
    'The same pattern keeps showing up with different people.',
    'You recognize this dynamic—it\'s familiar.',
    'The faces change but the friction doesn\'t.',
    'This isn\'t about them. It\'s about a pattern.',
  ],
  control_grip: [
    'You\'re holding this tighter than it needs to be held.',
    'Control feels like the only safe option.',
    'The grip is getting exhausting.',
    'What you\'re protecting might be suffocating.',
  ],
  trust_issues: [
    'You test before you trust.',
    'People have to prove themselves repeatedly.',
    'The walls are up before they get close.',
    'You\'re protecting yourself from something that might not happen.',
  ],
  people_pleasing: [
    'You shape yourself to fit what others want.',
    'Approval matters more than you admit.',
    'You know what they need before they ask.',
    'Your own preferences keep getting overwritten.',
  ],
  perfectionism: [
    'Nothing ever quite reaches the standard.',
    'Good enough doesn\'t exist for you.',
    'The bar keeps moving.',
    'You\'re harder on yourself than anyone else would be.',
  ],
  default: [
    'Something here is asking for attention.',
    'You already know what this is about.',
    'This isn\'t random.',
    'There\'s a reason this keeps coming up.',
  ],
};

// Pattern line variations
const PATTERN_VARIATIONS: { [key: string]: string[] } = {
  overcommitment: [
    'You take on more than you can hold—and then push through anyway.',
    'Yes comes before you\'ve counted the cost.',
    'Your capacity has become your excuse to exceed it.',
  ],
  avoidance: [
    'You see what needs facing, but you turn toward easier things.',
    'The problem grows while you stay busy elsewhere.',
    'Awareness without action becomes its own kind of suffering.',
  ],
  premature_action: [
    'You launch before the foundation is set.',
    'Action feels safer than uncertainty.',
    'Movement becomes a way to avoid sitting with what\'s unclear.',
  ],
  delayed_decision: [
    'You gather information instead of choosing.',
    'The decision sits there while you wait for clarity that won\'t come.',
    'Options multiply; commitment stays frozen.',
  ],
  emotional_suppression: [
    'Feelings get compressed, managed, scheduled.',
    'What you won\'t let out directly finds indirect ways.',
    'The container is getting full.',
  ],
  boundary_erosion: [
    'Each accommodation seems small, but they add up.',
    'You give ground to avoid conflict.',
    'Your territory keeps shrinking.',
  ],
  identity_confusion: [
    'Different contexts pull out different versions of you.',
    'You\'ve lost track of which one is real.',
    'Flexibility has become formlessness.',
  ],
  relationship_strain: [
    'The same dynamic keeps appearing in different costumes.',
    'You\'re meeting yourself in every relationship.',
    'The pattern predates the person.',
  ],
  control_grip: [
    'Security comes from holding everything in place.',
    'Letting go feels like falling.',
    'Control is the strategy, but it\'s not the solution.',
  ],
  trust_issues: [
    'Trust has to be earned over and over.',
    'Closeness comes with conditions.',
    'You\'re prepared for betrayal before it happens.',
  ],
  people_pleasing: [
    'Your worth gets measured by their approval.',
    'Boundaries dissolve in the face of someone else\'s need.',
    'You become the shape of what\'s missing.',
  ],
  perfectionism: [
    'The standard is always one step ahead of where you are.',
    'Done is never quite done.',
    'Excellence has become a prison.',
  ],
  default: [
    'There\'s a pattern running through this.',
    'This connects to something deeper.',
    'The surface isn\'t the whole story.',
  ],
};

// Choice line variations
const CHOICE_VARIATIONS: { [key: string]: string[] } = {
  overcommitment: [
    'You can keep pushing through. Or you can set one thing down.',
    'You can carry it all. Or you can find out what happens when you don\'t.',
  ],
  avoidance: [
    'You can keep circling. Or you can face it directly.',
    'You can stay busy. Or you can stop and look.',
  ],
  premature_action: [
    'You can keep moving. Or you can wait for the ground to be ready.',
    'You can act now. Or you can let this develop.',
  ],
  delayed_decision: [
    'You can keep weighing. Or you can trust what you already know.',
    'You can wait for certainty. Or you can choose without it.',
  ],
  emotional_suppression: [
    'You can keep it contained. Or you can let it move.',
    'You can manage it. Or you can feel it.',
  ],
  boundary_erosion: [
    'You can keep accommodating. Or you can hold your line.',
    'You can say yes again. Or you can find out what happens when you don\'t.',
  ],
  identity_confusion: [
    'You can keep adapting. Or you can find your own shape.',
    'You can be what they need. Or you can be what you are.',
  ],
  relationship_strain: [
    'You can keep responding the old way. Or you can try something different.',
    'You can blame the person. Or you can look at the pattern.',
  ],
  control_grip: [
    'You can hold tighter. Or you can loosen your grip and see what stays.',
    'You can manage it. Or you can trust it.',
  ],
  trust_issues: [
    'You can keep testing. Or you can take a small risk.',
    'You can stay protected. Or you can let someone in before they\'ve proven themselves.',
  ],
  people_pleasing: [
    'You can keep adjusting. Or you can find out if they can handle the real you.',
    'You can say what they want to hear. Or you can say what\'s true.',
  ],
  perfectionism: [
    'You can keep refining. Or you can call it done.',
    'You can wait until it\'s right. Or you can release it imperfect.',
  ],
  default: [
    'You can keep going as you are. Or you can try something different.',
    'You can let this pass. Or you can stay with it.',
  ],
};

// Memory/continuity phrases
const MEMORY_PHRASES = [
  'This isn\'t new.',
  'You\'ve been circling this for a while.',
  'This keeps showing up in different forms.',
  'Something about this has been building.',
  'You\'ve touched this before.',
];

// ============================================
// INTENSITY CALIBRATION
// ============================================

const SURFACE_INTENSITY: Record<MirrorSurface, IntensityLevel> = {
  home: 'light',
  journal: 'warm',
  ask_mirror: 'direct',
  deep_dive: 'confronting',
  reflect: 'warm',
};

// How much to include based on intensity
const INTENSITY_CONFIG: Record<IntensityLevel, {
  includeChoice: boolean;
  includeShift: boolean;
  includeQuestion: boolean;
  maxLines: number;
  useMemoryPhrases: boolean;
}> = {
  light: {
    includeChoice: false,
    includeShift: false,
    includeQuestion: false,
    maxLines: 2,
    useMemoryPhrases: false,
  },
  warm: {
    includeChoice: true,
    includeShift: false,
    includeQuestion: false,
    maxLines: 3,
    useMemoryPhrases: true,
  },
  direct: {
    includeChoice: true,
    includeShift: true,
    includeQuestion: true,
    maxLines: 5,
    useMemoryPhrases: true,
  },
  confronting: {
    includeChoice: true,
    includeShift: true,
    includeQuestion: true,
    maxLines: 6,
    useMemoryPhrases: true,
  },
};

// ============================================
// RESPONSE BUILDER
// ============================================

/**
 * Select from variation pool using seed for consistency
 */
const selectVariation = (pool: string[], seed: number): string => {
  const index = Math.abs(seed) % pool.length;
  return pool[index];
};

/**
 * Detect theme from text (for journal context)
 */
export const detectThemeFromText = (text: string): string => {
  const lowerText = text.toLowerCase();
  
  const themeKeywords: { [key: string]: string[] } = {
    overcommitment: ['busy', 'exhausted', 'too much', 'overwhelm', 'can\'t say no'],
    avoidance: ['avoid', 'later', 'putting off', 'not ready', 'ignoring'],
    premature_action: ['already', 'started', 'jumped', 'rushed', 'too fast'],
    delayed_decision: ['decide', 'choice', 'option', 'should', 'can\'t choose'],
    emotional_suppression: ['don\'t feel', 'fine', 'okay', 'holding', 'contain'],
    boundary_erosion: ['they want', 'for them', 'again', 'gave in'],
    relationship_strain: ['they', 'partner', 'friend', 'always', 'never'],
    control_grip: ['control', 'manage', 'handle', 'fix', 'make sure'],
    trust_issues: ['trust', 'hurt', 'betrayed', 'careful', 'walls'],
    people_pleasing: ['like me', 'approval', 'disappointed', 'let down'],
    perfectionism: ['perfect', 'good enough', 'more', 'better', 'right'],
  };
  
  for (const [theme, keywords] of Object.entries(themeKeywords)) {
    for (const keyword of keywords) {
      if (lowerText.includes(keyword)) {
        return theme;
      }
    }
  }
  
  return 'default';
};

/**
 * Build a Mirror Response from available context
 */
export const buildMirrorResponse = (params: {
  dominantTruth?: { dominantTheme: string; confidenceScore: number } | null;
  unifiedPattern?: { headline: string; corePattern: string; tension: string; connectorPhrase: string } | null;
  journalText?: string;
  lifeArea?: string;
  chapter?: string;
  hasHistory?: boolean;
  variationSeed?: number;
}): MirrorResponse => {
  const {
    dominantTruth,
    unifiedPattern,
    journalText,
    lifeArea,
    chapter,
    hasHistory = false,
    variationSeed = Date.now(),
  } = params;
  
  // Determine the theme to use
  let theme = 'default';
  let confidence = 50;
  
  // Priority 1: Dominant truth (highest signal)
  if (dominantTruth && dominantTruth.confidenceScore >= 50) {
    theme = dominantTruth.dominantTheme;
    confidence = dominantTruth.confidenceScore;
  }
  // Priority 2: Journal text analysis
  else if (journalText && journalText.length > 20) {
    theme = detectThemeFromText(journalText);
    confidence = journalText.length > 100 ? 65 : 55;
  }
  
  // Select variations using seed for consistency within session
  const recognitionPool = RECOGNITION_VARIATIONS[theme] || RECOGNITION_VARIATIONS.default;
  const patternPool = PATTERN_VARIATIONS[theme] || PATTERN_VARIATIONS.default;
  const choicePool = CHOICE_VARIATIONS[theme] || CHOICE_VARIATIONS.default;
  
  const recognition = selectVariation(recognitionPool, variationSeed);
  const pattern = unifiedPattern?.corePattern || selectVariation(patternPool, variationSeed + 1);
  const choice = selectVariation(choicePool, variationSeed + 2);
  
  // Build practical shift from unified pattern or generate
  const practicalShift = unifiedPattern?.tension?.split('.')[0] || 
    'Notice when this pattern shows up today.';
  
  // Build reflection question
  const reflectionQuestions: { [key: string]: string } = {
    overcommitment: 'What would you have to face if you stopped being busy?',
    avoidance: 'What becomes possible when you stop circling and face it directly?',
    premature_action: 'What are you avoiding by moving so fast?',
    delayed_decision: 'What would you lose if you chose? What would you gain?',
    emotional_suppression: 'What feeling are you managing instead of having?',
    boundary_erosion: 'What would you protect if you weren\'t protecting the peace?',
    identity_confusion: 'Who are you when you\'re not adapting to someone else?',
    relationship_strain: 'What part of this pattern belongs to you?',
    control_grip: 'What are you afraid would happen if you let go?',
    trust_issues: 'What would change if you gave trust before it was earned?',
    people_pleasing: 'What would you want if their opinion didn\'t matter?',
    perfectionism: 'What would "good enough" actually look like?',
    default: 'What does this tell you about where you are right now?',
  };
  
  const reflectionQuestion = reflectionQuestions[theme] || reflectionQuestions.default;
  
  // Build source context
  const sourceContext: SourceContext = {
    dominantTruth: dominantTruth?.dominantTheme,
    unifiedPattern: unifiedPattern?.headline,
    chapter,
    activeLifeArea: lifeArea,
    hasHistory,
  };
  
  return {
    recognition,
    pattern,
    choice,
    practicalShift,
    reflectionQuestion,
    lifeArea,
    confidence,
    sourceContext,
    variationSeed,
  };
};

// ============================================
// SURFACE-SPECIFIC FORMATTERS
// ============================================

/**
 * Format response for a specific surface with appropriate intensity
 */
export const formatForSurface = (
  response: MirrorResponse,
  surface: MirrorSurface,
  options?: { includeMemoryPhrase?: boolean }
): string => {
  const intensity = SURFACE_INTENSITY[surface];
  const config = INTENSITY_CONFIG[intensity];
  
  const lines: string[] = [];
  
  // Optional memory phrase for continuity
  if (options?.includeMemoryPhrase && config.useMemoryPhrases && response.sourceContext.hasHistory) {
    const memoryPhrase = selectVariation(MEMORY_PHRASES, response.variationSeed);
    lines.push(memoryPhrase);
  }
  
  // Recognition always included
  lines.push(response.recognition);
  
  // Pattern for surfaces that need it
  if (surface !== 'home') {
    lines.push(response.pattern);
  }
  
  // Choice for appropriate intensity
  if (config.includeChoice && response.choice) {
    lines.push(response.choice);
  }
  
  // Trim to max lines
  return lines.slice(0, config.maxLines).join('\n');
};

/**
 * Get response formatted for Journal (inline micro-mirror)
 */
export const getJournalResponse = (
  response: MirrorResponse,
  options?: { expanded?: boolean }
): { text: string; hasMore: boolean } => {
  const shortText = formatForSurface(response, 'journal');
  
  if (options?.expanded) {
    const fullText = [
      response.recognition,
      response.pattern,
      response.choice,
    ].filter(Boolean).join('\n');
    
    return { text: fullText, hasMore: false };
  }
  
  return { 
    text: shortText, 
    hasMore: Boolean(response.choice || response.reflectionQuestion) 
  };
};

/**
 * Get response formatted for Home (daily card)
 */
export const getHomeResponse = (response: MirrorResponse): {
  headline: string;
  supporting: string;
} => {
  return {
    headline: response.recognition,
    supporting: response.pattern.split('.')[0] + '.',
  };
};

/**
 * Get system context for Ask Mirror chat
 */
export const getAskMirrorContext = (response: MirrorResponse): string => {
  const contextParts = [
    `Current recognition: "${response.recognition}"`,
    `Core pattern: "${response.pattern}"`,
  ];
  
  if (response.lifeArea) {
    contextParts.push(`Active life area: ${response.lifeArea}`);
  }
  
  if (response.sourceContext.chapter) {
    contextParts.push(`Life chapter: ${response.sourceContext.chapter}`);
  }
  
  return contextParts.join('\n');
};

/**
 * Get opening line for Ask Mirror (varies to avoid repetition)
 */
export const getAskMirrorOpener = (
  response: MirrorResponse,
  variationIndex: number = 0
): string => {
  const openers = [
    response.recognition,
    `${response.recognition} The question is whether you're ready to look at it directly.`,
    `You already know where this is heading. ${response.pattern.split('.')[0]}.`,
    response.sourceContext.hasHistory 
      ? `This keeps coming back. ${response.recognition}`
      : response.recognition,
  ];
  
  return openers[variationIndex % openers.length];
};

/**
 * Get Reflect flow prompts
 */
export const getReflectPrompts = (response: MirrorResponse): {
  recognition: string;
  question: string;
  journalPrompt: string;
  mirrorFollowUp: string;
} => {
  return {
    recognition: response.recognition,
    question: response.reflectionQuestion || 'What does this bring up for you?',
    journalPrompt: `${response.recognition}\n\nWrite about: ${response.reflectionQuestion}`,
    mirrorFollowUp: `Tell me more about "${response.pattern.split('.')[0]}."`,
  };
};

// ============================================
// EXPORTS
// ============================================

export default {
  buildMirrorResponse,
  formatForSurface,
  getJournalResponse,
  getHomeResponse,
  getAskMirrorContext,
  getAskMirrorOpener,
  getReflectPrompts,
  detectThemeFromText,
};
