/**
 * Human Design Context Layer
 * 
 * This file provides human-readable translations for Human Design sequences.
 * It maps raw gate/line values to themes and plain-language descriptions.
 * 
 * IMPORTANT: This is a presentation layer only. It does not change underlying calculations.
 */

// ============================================================================
// GATE THEMES - Core archetypal themes for each of the 64 gates
// ============================================================================
export const GATE_THEMES: Record<number, { name: string; keywords: string[] }> = {
  1: { name: 'Self-Expression', keywords: ['Creativity', 'Individuality', 'Authenticity'] },
  2: { name: 'Direction', keywords: ['Receptivity', 'Self-direction', 'Natural flow'] },
  3: { name: 'Ordering', keywords: ['Innovation', 'New beginnings', 'Mutation'] },
  4: { name: 'Formulization', keywords: ['Mental solutions', 'Logic', 'Understanding'] },
  5: { name: 'Fixed Rhythms', keywords: ['Rhythm', 'Natural timing', 'Patience'] },
  6: { name: 'Friction', keywords: ['Emotional clarity', 'Intimacy', 'pH balance'] },
  7: { name: 'The Role of the Self', keywords: ['Leadership', 'Direction', 'Guidance'] },
  8: { name: 'Contribution', keywords: ['Contribution', 'Authenticity', 'Example'] },
  9: { name: 'Focus', keywords: ['Concentration', 'Details', 'Determination'] },
  10: { name: 'Behavior of the Self', keywords: ['Self-love', 'Authenticity', 'Behavior'] },
  11: { name: 'Ideas', keywords: ['Ideas', 'Stimulation', 'Peace'] },
  12: { name: 'Caution', keywords: ['Articulation', 'Caution', 'Social expression'] },
  13: { name: 'The Listener', keywords: ['Listening', 'Secrets', 'Narrative'] },
  14: { name: 'Power Skills', keywords: ['Resources', 'Wealth', 'Empowerment'] },
  15: { name: 'Extremes', keywords: ['Rhythm', 'Diversity', 'Humanity'] },
  16: { name: 'Skills', keywords: ['Skills', 'Enthusiasm', 'Identification'] },
  17: { name: 'Opinions', keywords: ['Opinions', 'Following', 'Understanding'] },
  18: { name: 'Correction', keywords: ['Correction', 'Judgment', 'Integrity'] },
  19: { name: 'Wanting', keywords: ['Sensitivity', 'Need', 'Approach'] },
  20: { name: 'The Now', keywords: ['Presence', 'Contemplation', 'Now'] },
  21: { name: 'The Hunter', keywords: ['Control', 'Authority', 'Willpower'] },
  22: { name: 'Openness', keywords: ['Grace', 'Charm', 'Emotional openness'] },
  23: { name: 'Assimilation', keywords: ['Simplicity', 'Assimilation', 'Expression'] },
  24: { name: 'Rationalization', keywords: ['Returning', 'Mental review', 'Inspiration'] },
  25: { name: 'The Spirit of the Self', keywords: ['Innocence', 'Self-love', 'Universal love'] },
  26: { name: 'The Taming Power', keywords: ['Salesmanship', 'Ego', 'Persuasion'] },
  27: { name: 'Caring', keywords: ['Nourishment', 'Caring', 'Selflessness'] },
  28: { name: 'The Game Player', keywords: ['Risk', 'Struggle', 'Purpose'] },
  29: { name: 'The Abysmal', keywords: ['Commitment', 'Perseverance', 'Saying yes'] },
  30: { name: 'Recognition of Feelings', keywords: ['Desire', 'Feelings', 'Fate'] },
  31: { name: 'Influence', keywords: ['Leadership', 'Democracy', 'Influence'] },
  32: { name: 'Continuity', keywords: ['Continuity', 'Preservation', 'Transformation'] },
  33: { name: 'Privacy', keywords: ['Retreat', 'Privacy', 'Memory'] },
  34: { name: 'Power', keywords: ['Power', 'Strength', 'Availability'] },
  35: { name: 'Change', keywords: ['Experience', 'Progress', 'Adventure'] },
  36: { name: 'Crisis', keywords: ['Emotional experience', 'Crisis', 'Exploration'] },
  37: { name: 'Friendship', keywords: ['Community', 'Family', 'Bonds'] },
  38: { name: 'The Fighter', keywords: ['Struggle', 'Opposition', 'Purpose'] },
  39: { name: 'Provocation', keywords: ['Provocation', 'Spirit', 'Liberation'] },
  40: { name: 'Aloneness', keywords: ['Solitude', 'Delivery', 'Willpower'] },
  41: { name: 'Contraction', keywords: ['Fantasy', 'Imagination', 'Desire'] },
  42: { name: 'Growth', keywords: ['Completion', 'Growth', 'Finishing'] },
  43: { name: 'Insight', keywords: ['Breakthrough', 'Insight', 'Deafness'] },
  44: { name: 'Coming to Meet', keywords: ['Alertness', 'Memory', 'Pattern recognition'] },
  45: { name: 'The Gatherer', keywords: ['Gathering', 'Synergy', 'King/Queen'] },
  46: { name: 'Determination', keywords: ['Love of body', 'Serendipity', 'Being'] },
  47: { name: 'Realization', keywords: ['Mental oppression', 'Realization', 'Transmutation'] },
  48: { name: 'Depth', keywords: ['Depth', 'Wisdom', 'Solutions'] },
  49: { name: 'Revolution', keywords: ['Revolution', 'Principles', 'Rejection'] },
  50: { name: 'Values', keywords: ['Values', 'Responsibility', 'Law'] },
  51: { name: 'Shock', keywords: ['Initiative', 'Shock', 'Competition'] },
  52: { name: 'Stillness', keywords: ['Stillness', 'Concentration', 'Mountain'] },
  53: { name: 'Beginnings', keywords: ['Starting', 'Development', 'Maturation'] },
  54: { name: 'Ambition', keywords: ['Ambition', 'Drive', 'Rising'] },
  55: { name: 'Spirit', keywords: ['Abundance', 'Spirit', 'Melancholy'] },
  56: { name: 'Stimulation', keywords: ['Stimulation', 'Stories', 'Wanderer'] },
  57: { name: 'Intuitive Clarity', keywords: ['Intuition', 'Clarity', 'Survival'] },
  58: { name: 'Vitality', keywords: ['Joy', 'Vitality', 'Aliveness'] },
  59: { name: 'Sexuality', keywords: ['Intimacy', 'Sexuality', 'Breaking barriers'] },
  60: { name: 'Acceptance', keywords: ['Limitation', 'Acceptance', 'Conservation'] },
  61: { name: 'Mystery', keywords: ['Mystery', 'Inner truth', 'Pressure to know'] },
  62: { name: 'Details', keywords: ['Details', 'Expression', 'Precision'] },
  63: { name: 'Doubt', keywords: ['Logic', 'Questioning', 'After completion'] },
  64: { name: 'Confusion', keywords: ['Confusion', 'Before completion', 'Transition'] },
};

// ============================================================================
// LINE THEMES - Each line 1-6 has a general archetypal quality
// ============================================================================
export const LINE_THEMES: Record<number, { name: string; quality: string }> = {
  1: { name: 'Investigator', quality: 'Foundation and security through introspection' },
  2: { name: 'Hermit', quality: 'Natural talent awaiting recognition' },
  3: { name: 'Martyr', quality: 'Learning through trial and adaptation' },
  4: { name: 'Opportunist', quality: 'Network and influence through relationships' },
  5: { name: 'Heretic', quality: 'Universalizing and practical solutions' },
  6: { name: 'Role Model', quality: 'Wisdom through life experience and overview' },
};

// ============================================================================
// SEQUENCE ROLE DESCRIPTIONS - What each position in the sequence represents
// ============================================================================
export const SEQUENCE_ROLES: Record<string, { title: string; description: string; reflectionPrompt: string }> = {
  // Purpose Arc
  lifes_work: {
    title: "Life's Work",
    description: "How your unique expression may naturally emerge in the world through what you do.",
    reflectionPrompt: "Where do you notice your natural way of contributing showing up?"
  },
  evolution: {
    title: "Evolution",
    description: "The challenge or growth edge that may refine your expression over time.",
    reflectionPrompt: "What patterns around growth or challenge feel familiar to you?"
  },
  radiance: {
    title: "Radiance",
    description: "How your presence may naturally affect others when you're aligned.",
    reflectionPrompt: "When do you feel most naturally radiant or at ease?"
  },
  purpose: {
    title: "Purpose",
    description: "The deeper current your life may be moving toward beneath the surface.",
    reflectionPrompt: "What sense of direction, if any, feels present in your life?"
  },
  
  // Love Arc
  attraction: {
    title: "Attraction",
    description: "What may draw others to you and what you're naturally drawn toward.",
    reflectionPrompt: "What qualities do you notice attracting you in relationships?"
  },
  iq: {
    title: "IQ",
    description: "How your mental intelligence may best express itself.",
    reflectionPrompt: "How do you tend to process and work with information?"
  },
  eq: {
    title: "EQ",
    description: "How your emotional intelligence may navigate relationships.",
    reflectionPrompt: "What patterns do you notice in how you relate emotionally?"
  },
  sq: {
    title: "SQ",
    description: "How your spiritual or intuitive intelligence may guide you.",
    reflectionPrompt: "What deeper knowing, if any, do you sense within yourself?"
  },
  core_wound: {
    title: "Core Wound",
    description: "A sensitive area that may hold both challenge and potential transformation.",
    reflectionPrompt: "What tender places in you might hold hidden gifts?"
  },
  
  // Prosperity Arc
  brand: {
    title: "Brand",
    description: "What you may naturally be known for when aligned with your essence.",
    reflectionPrompt: "What do people tend to recognize or appreciate about you?"
  },
  culture: {
    title: "Culture",
    description: "The environment or context where your gifts may thrive.",
    reflectionPrompt: "What kinds of environments help you feel most productive?"
  },
  vocation: {
    title: "Vocation",
    description: "The nature of work or service that may feel most aligned.",
    reflectionPrompt: "What kind of contribution feels most meaningful to you?"
  },
  pearl: {
    title: "Pearl",
    description: "How prosperity and flow may naturally come to you.",
    reflectionPrompt: "When do resources or opportunities tend to arrive most easily?"
  },
};

// ============================================================================
// ARC DESCRIPTIONS - Overview for each of the three arcs
// ============================================================================
export const ARC_DESCRIPTIONS: Record<string, { title: string; description: string; helperText: string }> = {
  purpose: {
    title: "Purpose Arc",
    description: "Your life direction and how you may naturally express yourself in the world.",
    helperText: "These four spheres map the journey from your daily work to your deeper purpose."
  },
  love: {
    title: "Love Arc", 
    description: "How you may relate to others and navigate the terrain of connection.",
    helperText: "These five spheres explore different dimensions of relationship and intimacy."
  },
  prosperity: {
    title: "Prosperity Arc",
    description: "How abundance and contribution may flow through your unique design.",
    helperText: "These four spheres map the path from your essence to material flow."
  },
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get the theme information for a specific gate
 */
export function getGateTheme(gateNumber: number): { name: string; keywords: string[] } {
  return GATE_THEMES[gateNumber] || { name: 'Unknown', keywords: [] };
}

/**
 * Get the theme information for a specific line
 */
export function getLineTheme(lineNumber: number): { name: string; quality: string } {
  return LINE_THEMES[lineNumber] || { name: 'Unknown', quality: '' };
}

/**
 * Get the sequence role description
 */
export function getSequenceRole(roleName: string): { title: string; description: string; reflectionPrompt: string } {
  return SEQUENCE_ROLES[roleName] || { 
    title: roleName, 
    description: '', 
    reflectionPrompt: '' 
  };
}

/**
 * Format a complete sequence explanation in everyday language
 */
export function formatSequenceExplanation(
  roleName: string, 
  gate: number, 
  line: number
): {
  title: string;
  themeLabel: string;
  description: string;
  technicalValue: string;
  reflectionPrompt: string;
} {
  const role = getSequenceRole(roleName);
  const gateTheme = getGateTheme(gate);
  const lineTheme = getLineTheme(line);
  
  // Create theme label from gate keywords
  const themeLabel = gateTheme.keywords.slice(0, 3).join(' / ');
  
  // Create a contextual description combining gate theme with role
  const gateContext = gateTheme.name.toLowerCase();
  let description = role.description;
  
  // Add gate-specific flavor to the description
  if (gateTheme.name !== 'Unknown') {
    description = `This may point to ${gateContext} as a key theme in ${role.description.toLowerCase()}`;
  }
  
  return {
    title: role.title,
    themeLabel: `Theme: ${themeLabel}`,
    description,
    technicalValue: `Gate ${gate} • Line ${line}`,
    reflectionPrompt: role.reflectionPrompt,
  };
}

/**
 * Get arc description
 */
export function getArcDescription(arcKey: string): { title: string; description: string; helperText: string } {
  return ARC_DESCRIPTIONS[arcKey] || { 
    title: arcKey, 
    description: '', 
    helperText: '' 
  };
}
