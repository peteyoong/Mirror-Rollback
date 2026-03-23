/**
 * Timeline Phase Utilities - V2 Pattern Detection Layer
 * 
 * Focus: Human-readable, emotionally meaningful language.
 * Mirror reflects, it does NOT declare.
 * Always uses observational language ("this keeps appearing", "you may notice")
 * Never deterministic or authoritative.
 */

export interface TimelinePhaseInfo {
  id: string;
  name: string;
  humanMeaning: string;
  dateRange: string;
  isPrimary: boolean;
}

// Phase data structure with human-readable meanings
const PHASES: TimelinePhaseInfo[] = [
  { 
    id: 'q1', 
    name: 'Recognition', 
    humanMeaning: 'Something is becoming clear',
    dateRange: 'Jan – Mar', 
    isPrimary: false 
  },
  { 
    id: 'q2', 
    name: 'Confrontation', 
    humanMeaning: 'Something can no longer be avoided',
    dateRange: 'Apr – Jun', 
    isPrimary: true 
  },
  { 
    id: 'q3', 
    name: 'The Crossroads', 
    humanMeaning: 'A choice, split, or redirection is active',
    dateRange: 'Jul – Sep', 
    isPrimary: true 
  },
  { 
    id: 'q4', 
    name: 'Integration', 
    humanMeaning: 'Something is settling into a new form',
    dateRange: 'Oct – Dec', 
    isPrimary: false 
  },
];

// Phase icons
export const PHASE_ICONS: { [key: string]: string } = {
  q1: '🌱',
  q2: '⚡',
  q3: '🔀',
  q4: '🌊',
};

// Phase Mirror Card content - V2 UPDATED LANGUAGE
// Now uses "This sounds like..." instead of "This entry lands in..."
export interface PhaseMirrorContent {
  phaseName: string;
  humanMeaning: string;
  soundsLikeLine: string;  // Renamed from whyItMatters - observational language
  largerContextLine: string;  // What you're noticing may be part of something larger
  emotionalLine: string;
  repeatLine: string;  // "You've been here before."
  ctaPrefix: string;  // "You may have touched this before."
}

export const PHASE_MIRROR_CONTENT: { [key: string]: PhaseMirrorContent } = {
  q1: {
    phaseName: 'Recognition',
    humanMeaning: 'Something is becoming clear',
    soundsLikeLine: 'This sounds like a moment where something is becoming clear.',
    largerContextLine: 'What you\'re noticing may be part of something larger, not just a one-off moment.',
    emotionalLine: 'Patterns often reveal themselves quietly before they demand attention.',
    repeatLine: 'You\'ve been here before.',
    ctaPrefix: 'You may have touched this before.',
  },
  q2: {
    phaseName: 'Confrontation',
    humanMeaning: 'Something can no longer be avoided',
    soundsLikeLine: 'This sounds like a moment where something can no longer be managed the same way.',
    largerContextLine: 'What you\'re facing may have been building for a while. This could be where it gets real.',
    emotionalLine: 'What\'s tolerable has a way of becoming intolerable—all at once.',
    repeatLine: 'You\'ve been here before.',
    ctaPrefix: 'You may have touched this before.',
  },
  q3: {
    phaseName: 'The Crossroads',
    humanMeaning: 'A choice, split, or redirection is active',
    soundsLikeLine: 'This sounds like a moment where a choice or direction is becoming clearer.',
    largerContextLine: 'What you decide now—or don\'t decide—may shape what comes next. This isn\'t neutral ground.',
    emotionalLine: 'The path that feels familiar and the path that feels alive may not be the same.',
    repeatLine: 'You\'ve been here before.',
    ctaPrefix: 'You may have touched this before.',
  },
  q4: {
    phaseName: 'Integration',
    humanMeaning: 'Something is settling into a new form',
    soundsLikeLine: 'This sounds like a moment where something is starting to settle.',
    largerContextLine: 'What changed may be becoming part of who you are. This is where it becomes real.',
    emotionalLine: 'What you\'ve been through may be trying to become steady ground.',
    repeatLine: 'You\'ve been here before.',
    ctaPrefix: 'You may have touched this before.',
  },
};

// Upgraded reverse prompts - with "If you stay with this..." prefix
export const REVERSE_PROMPTS: { [key: string]: string[] } = {
  q1: [
    'If you stay with this... What are you beginning to admit to yourself?',
    'If you stay with this... What pattern is becoming harder to ignore?',
    'If you stay with this... What feels newly visible?',
  ],
  q2: [
    'If you stay with this... What is asking to be faced instead of managed?',
    'If you stay with this... Where is your usual strategy no longer enough?',
    'If you stay with this... What truth is pressing for acknowledgment?',
  ],
  q3: [
    'If you stay with this... What are you being asked to choose between?',
    'If you stay with this... What path feels familiar, and what path feels alive?',
    'If you stay with this... What changes if you stop waiting for certainty?',
  ],
  q4: [
    'If you stay with this... What is becoming steadier in you?',
    'If you stay with this... What have you already outgrown?',
    'If you stay with this... What is trying to become your new normal?',
  ],
};

// Phase Tag Modal explanation - V2 UPDATED LANGUAGE
// Uses "Entries like this often appear when..." instead of "This entry was created during..."
export interface PhaseTagExplanation {
  phaseName: string;
  humanMeaning: string;
  whyTagged: string;  // Observational, not declarative
  insight: string;
}

export function getPhaseTagExplanation(phaseId: string): PhaseTagExplanation {
  const explanations: { [key: string]: PhaseTagExplanation } = {
    q1: {
      phaseName: 'Recognition',
      humanMeaning: 'Something is becoming clear',
      whyTagged: 'Entries like this often appear when something is starting to surface.',
      insight: 'What you notice during times like this often becomes the theme of what follows.',
    },
    q2: {
      phaseName: 'Confrontation',
      humanMeaning: 'Something can no longer be avoided',
      whyTagged: 'Entries like this often appear when something can\'t be managed the same way anymore.',
      insight: 'Entries from times like this often carry the energy of things finally being named.',
    },
    q3: {
      phaseName: 'The Crossroads',
      humanMeaning: 'A choice, split, or redirection is active',
      whyTagged: 'Entries like this often appear when a choice or direction is becoming clearer.',
      insight: 'What you write during times like this may show which direction you were leaning before you knew.',
    },
    q4: {
      phaseName: 'Integration',
      humanMeaning: 'Something is settling into a new form',
      whyTagged: 'Entries like this often appear when changes are starting to settle.',
      insight: 'These entries often show what actually stuck, and what you outgrew.',
    },
  };
  
  const phase = getPhaseById(phaseId);
  return explanations[phaseId] || {
    phaseName: phase?.name || 'Unknown',
    humanMeaning: phase?.humanMeaning || 'A period of transition',
    whyTagged: 'This entry was written during a transition period.',
    insight: 'What you write during transitions often carries more weight than it seems at the time.',
  };
}

// Tension insights for Level 3 - observational language
export const PHASE_TENSION_INSIGHTS: { [key: string]: string } = {
  q1: 'Something keeps becoming visible—but it hasn\'t moved yet.',
  q2: 'Something keeps surfacing that doesn\'t want to be managed anymore.',
  q3: 'You\'re circling a choice that hasn\'t fully landed.',
  q4: 'This is starting to settle into something more stable.',
};

// Identity tendency templates for Level 4 - probabilistic language
// Uses "you tend to", never "you are"
export const IDENTITY_TENDENCY_TEMPLATES: { [key: string]: string } = {
  q1: 'You tend to stay in awareness before things shift. Noticing often comes before acting.',
  q2: 'You often meet the same tension more than once before it moves. What\'s tolerable tends to stay tolerable—until it isn\'t.',
  q3: 'You spend time weighing paths before committing. Choice points seem to hold your attention.',
  q4: 'You\'re able to stabilize changes once they land. Integration comes more naturally than initiation.',
};

/**
 * Get the current timeline phase based on today's date
 */
export function getCurrentPhase(): TimelinePhaseInfo {
  const now = new Date();
  const month = now.getMonth();
  
  if (month <= 2) return PHASES[0]; // q1
  if (month <= 5) return PHASES[1]; // q2
  if (month <= 8) return PHASES[2]; // q3
  return PHASES[3]; // q4
}

/**
 * Get a random reverse prompt for the current phase
 */
export function getReversePrompt(phaseId: string, seed?: number): string {
  const prompts = REVERSE_PROMPTS[phaseId] || REVERSE_PROMPTS.q1;
  const index = seed !== undefined 
    ? Math.abs(seed) % prompts.length 
    : Math.floor(Math.random() * prompts.length);
  return prompts[index];
}

/**
 * Get phase info by ID
 */
export function getPhaseById(phaseId: string): TimelinePhaseInfo | null {
  return PHASES.find(p => p.id === phaseId) || null;
}

/**
 * Get all phases
 */
export function getAllPhases(): TimelinePhaseInfo[] {
  return PHASES;
}

/**
 * Get Phase Mirror content for a specific phase
 */
export function getPhaseMirrorContent(phaseId: string): PhaseMirrorContent {
  return PHASE_MIRROR_CONTENT[phaseId] || PHASE_MIRROR_CONTENT.q1;
}

/**
 * Get icon for a phase
 */
export function getPhaseIcon(phaseId: string): string {
  return PHASE_ICONS[phaseId] || '⭐';
}

/**
 * Get tension insight for Level 3
 */
export function getPhaseTensionInsight(phaseId: string): string {
  return PHASE_TENSION_INSIGHTS[phaseId] || 'A pattern may be emerging here.';
}

/**
 * Get identity tendency for Level 4
 */
export function getIdentityTendency(phaseId: string): string {
  return IDENTITY_TENDENCY_TEMPLATES[phaseId] || '';
}

export default {
  getCurrentPhase,
  getReversePrompt,
  getPhaseById,
  getAllPhases,
  getPhaseMirrorContent,
  getPhaseIcon,
  getPhaseTagExplanation,
  getPhaseTensionInsight,
  getIdentityTendency,
  REVERSE_PROMPTS,
  PHASE_MIRROR_CONTENT,
  PHASE_ICONS,
  PHASE_TENSION_INSIGHTS,
  IDENTITY_TENDENCY_TEMPLATES,
};
