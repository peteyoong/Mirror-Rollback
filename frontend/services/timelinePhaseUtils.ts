/**
 * Timeline Phase Utilities
 * 
 * Shared utilities for determining current timeline phase based on date.
 * Used by Journal and Timeline for consistent phase detection.
 * 
 * Focus: Human-readable, emotionally meaningful language.
 * NOT overly astrological - feels like a reflection tool first.
 */

export interface TimelinePhaseInfo {
  id: string;
  name: string;
  humanMeaning: string;  // One-line plain-English explanation
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
  q1: '🌱',  // Recognition - new growth
  q2: '⚡',  // Confrontation - energy
  q3: '🔀',  // The Crossroads - decision
  q4: '🌊',  // Integration - flow
};

// Phase Mirror Card content - emotionally resonant messages for each phase
export interface PhaseMirrorContent {
  phaseName: string;
  humanMeaning: string;
  whyItMatters: string;
  emotionalLine: string;
}

export const PHASE_MIRROR_CONTENT: { [key: string]: PhaseMirrorContent } = {
  q1: {
    phaseName: 'Recognition',
    humanMeaning: 'Something is becoming clear',
    whyItMatters: 'What you\'re noticing now may be part of a larger shift, not just a passing thought.',
    emotionalLine: 'Patterns often reveal themselves quietly before they demand attention.',
  },
  q2: {
    phaseName: 'Confrontation',
    humanMeaning: 'Something can no longer be avoided',
    whyItMatters: 'What you\'re facing now has likely been building for a while. This is the part where it gets real.',
    emotionalLine: 'Avoidance gets expensive. You\'re in the part of the cycle where it stops working.',
  },
  q3: {
    phaseName: 'The Crossroads',
    humanMeaning: 'A choice, split, or redirection is active',
    whyItMatters: 'What you decide now—or don\'t decide—will shape what comes next. This isn\'t neutral ground.',
    emotionalLine: 'The path that feels familiar and the path that feels alive may not be the same.',
  },
  q4: {
    phaseName: 'Integration',
    humanMeaning: 'Something is settling into a new form',
    whyItMatters: 'What changed this year is now becoming part of who you are. This is where it becomes real.',
    emotionalLine: 'What you\'ve been through is trying to become steady ground.',
  },
};

// Upgraded reverse prompts - 3 stronger prompts per phase
export const REVERSE_PROMPTS: { [key: string]: string[] } = {
  q1: [
    'What are you beginning to admit to yourself?',
    'What pattern is becoming harder to ignore?',
    'What feels newly visible?',
  ],
  q2: [
    'What is asking to be faced instead of managed?',
    'Where is your usual strategy no longer enough?',
    'What truth is pressing for acknowledgment?',
  ],
  q3: [
    'What are you being asked to choose between?',
    'What path feels familiar, and what path feels alive?',
    'What changes if you stop waiting for certainty?',
  ],
  q4: [
    'What is becoming steadier in you?',
    'What have you already outgrown?',
    'What is trying to become your new normal?',
  ],
};

// Extended explanation for journal tag modal
export interface PhaseTagExplanation {
  phaseName: string;
  humanMeaning: string;
  whyTagged: string;
  insight: string;
}

export function getPhaseTagExplanation(phaseId: string): PhaseTagExplanation {
  const phase = getPhaseById(phaseId);
  if (!phase) {
    return {
      phaseName: 'Unknown',
      humanMeaning: 'A period of transition',
      whyTagged: 'This entry was created during a transition period.',
      insight: 'What you write during transitions often carries more weight than it seems at the time.',
    };
  }
  
  const explanations: { [key: string]: PhaseTagExplanation } = {
    q1: {
      phaseName: 'Recognition',
      humanMeaning: 'Something is becoming clear',
      whyTagged: 'This entry was written during your Recognition period—when patterns first start to surface.',
      insight: 'What you notice during this time often becomes the theme of what follows.',
    },
    q2: {
      phaseName: 'Confrontation',
      humanMeaning: 'Something can no longer be avoided',
      whyTagged: 'This entry was written during your Confrontation period—when what was tolerable stops being so.',
      insight: 'Entries from this time often carry the energy of things finally being named.',
    },
    q3: {
      phaseName: 'The Crossroads',
      humanMeaning: 'A choice, split, or redirection is active',
      whyTagged: 'This entry was written during your Crossroads period—the year\'s primary choice point.',
      insight: 'What you wrote here may show which direction you were leaning before you knew.',
    },
    q4: {
      phaseName: 'Integration',
      humanMeaning: 'Something is settling into a new form',
      whyTagged: 'This entry was written during your Integration period—when changes become the new normal.',
      insight: 'These entries often show what actually stuck, and what you outgrew.',
    },
  };
  
  return explanations[phaseId] || explanations.q1;
}

/**
 * Get the current timeline phase based on today's date
 */
export function getCurrentPhase(): TimelinePhaseInfo {
  const now = new Date();
  const month = now.getMonth(); // 0-indexed (Jan = 0)
  
  if (month <= 2) { // Jan, Feb, Mar
    return PHASES[0]; // q1 - Recognition
  } else if (month <= 5) { // Apr, May, Jun
    return PHASES[1]; // q2 - Confrontation
  } else if (month <= 8) { // Jul, Aug, Sep
    return PHASES[2]; // q3 - The Crossroads
  } else { // Oct, Nov, Dec
    return PHASES[3]; // q4 - Integration
  }
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

export default {
  getCurrentPhase,
  getReversePrompt,
  getPhaseById,
  getAllPhases,
  getPhaseMirrorContent,
  getPhaseIcon,
  getPhaseTagExplanation,
  REVERSE_PROMPTS,
  PHASE_MIRROR_CONTENT,
  PHASE_ICONS,
};
