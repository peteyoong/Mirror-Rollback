/**
 * Timeline Phase Utilities
 * 
 * Shared utilities for determining current timeline phase based on date.
 * Used by Journal and Timeline for consistent phase detection.
 */

export interface TimelinePhaseInfo {
  id: string;
  name: string;
  dateRange: string;
  isPrimary: boolean;
}

// Phase data structure
const PHASES: TimelinePhaseInfo[] = [
  { id: 'q1', name: 'Recognition', dateRange: 'Jan – Mar', isPrimary: false },
  { id: 'q2', name: 'Confrontation', dateRange: 'Apr – Jun', isPrimary: true },
  { id: 'q3', name: 'The Crossroads', dateRange: 'Jul – Sep', isPrimary: true },
  { id: 'q4', name: 'Integration', dateRange: 'Oct – Dec', isPrimary: false },
];

// Reverse prompts by phase - contextual questions after journal save
export const REVERSE_PROMPTS: { [key: string]: string[] } = {
  q1: [
    'What pattern are you starting to notice but haven\'t fully named yet?',
    'What keeps echoing in your mind, even when you try to move past it?',
    'If this moment is a signal, what is it pointing toward?',
  ],
  q2: [
    'What have you been avoiding saying?',
    'What would change if you stopped tolerating what you\'ve been tolerating?',
    'Where are you pretending not to see what\'s already clear?',
  ],
  q3: [
    'If you had to choose right now, which direction would you lean?',
    'What are you afraid would happen if you committed fully?',
    'What version of you would emerge if you made this choice?',
  ],
  q4: [
    'What actually changed this year?',
    'What are you still carrying that this year asked you to put down?',
    'What do you want to remember from this period?',
  ],
};

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

export default {
  getCurrentPhase,
  getReversePrompt,
  getPhaseById,
  getAllPhases,
  REVERSE_PROMPTS,
};
