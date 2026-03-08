/**
 * Human Design Context Layer
 * 
 * This file provides human-readable translations for Human Design sequences.
 * It maps raw gate/line values to themes and plain-language descriptions.
 * 
 * IMPORTANT: This is a presentation layer only. It does not change underlying calculations.
 * All interpretations are original Mirror-native reflective language.
 */

// ============================================================================
// GATE INTERPRETATIONS - Rich meaning-first descriptions for each gate
// ============================================================================
export const GATE_INTERPRETATIONS: Record<number, {
  essence: string;      // One-line essence
  reflection: string;   // Short interpretive paragraph
}> = {
  1: {
    essence: "The creative spark within you",
    reflection: "You carry a unique creative essence that expresses itself naturally when you allow it. There's an originality in how you see and engage with life."
  },
  2: {
    essence: "Trusting your inner compass",
    reflection: "You have an innate sense of direction that doesn't require external validation. When you relax into receptivity, your path tends to reveal itself."
  },
  3: {
    essence: "Learning through lived experience",
    reflection: "You understand things by doing them, not just thinking about them. Your willingness to experiment is how you discover what actually works."
  },
  4: {
    essence: "Finding the pattern that fits",
    reflection: "Your mind naturally seeks answers and solutions. You have a gift for formulating understanding from scattered information."
  },
  5: {
    essence: "Moving with natural rhythms",
    reflection: "You thrive when you honor your own timing rather than forcing pace. There's wisdom in your natural patterns and cycles."
  },
  6: {
    essence: "Growing through emotional honesty",
    reflection: "Your emotional experiences, especially the challenging ones, are pathways to deeper intimacy and self-understanding."
  },
  7: {
    essence: "Guiding through example",
    reflection: "You have a natural capacity to orient others, not by telling them what to do, but by embodying a clear direction yourself."
  },
  8: {
    essence: "Contributing through authenticity",
    reflection: "Your gift lies in doing things your own way. When you're genuine, others are naturally drawn to learn from your example."
  },
  9: {
    essence: "The power of focused attention",
    reflection: "You have a capacity for deep concentration that allows you to master details others might overlook. Focus is your superpower."
  },
  10: {
    essence: "Being true to yourself",
    reflection: "There's a natural self-acceptance available to you when you stop measuring yourself against others and simply be who you are."
  },
  11: {
    essence: "A wealth of inner visions",
    reflection: "Your mind is rich with ideas and possibilities. You're here to share these visions, not necessarily to implement them all yourself."
  },
  12: {
    essence: "Speaking when the time is right",
    reflection: "You have something valuable to express, but timing matters. Your words land most powerfully when you wait for the right moment."
  },
  13: {
    essence: "Holding space for stories",
    reflection: "People sense they can share with you. You have a gift for hearing what's beneath the surface of what others tell you."
  },
  14: {
    essence: "Accessing inner resources",
    reflection: "You have a natural connection to resources—not just material, but energetic. You know how to generate and channel what's needed."
  },
  15: {
    essence: "Embracing human diversity",
    reflection: "You have a wide range within you and can appreciate the same in others. Your rhythm may look different from the norm, and that's your gift."
  },
  16: {
    essence: "Mastery through repetition",
    reflection: "Your skills develop through dedicated practice. Enthusiasm carries you forward, and mastery comes from honoring the learning process."
  },
  17: {
    essence: "Seeing how things could work",
    reflection: "You naturally form opinions about how things might be improved. Your insights are most valuable when offered as possibilities, not prescriptions."
  },
  18: {
    essence: "The eye for refinement",
    reflection: "You notice what could be better. This gift for seeing patterns that need correcting can bring real value when shared with care."
  },
  19: {
    essence: "Sensing what's needed",
    reflection: "You have an intuitive sensitivity to what others need, sometimes before they know it themselves. This attunement is a form of care."
  },
  20: {
    essence: "The gift of presence",
    reflection: "You have access to a quality of being here, now, that others can feel. Your presence itself communicates something essential."
  },
  21: {
    essence: "The courage to take charge",
    reflection: "You have willpower and the capacity to control your domain. When you direct this energy wisely, you can accomplish meaningful things."
  },
  22: {
    essence: "Grace under emotional waves",
    reflection: "Your emotional openness is actually a form of charm. When you're present with your feelings, others feel permission to be present with theirs."
  },
  23: {
    essence: "Making the complex simple",
    reflection: "You can take complicated ideas and distill them into something others can grasp. Simplicity is your contribution."
  },
  24: {
    essence: "The returning to clarity",
    reflection: "Your mind revisits things, turning them over until understanding crystallizes. This repetitive mental process eventually yields insight."
  },
  25: {
    essence: "An innocent openness to life",
    reflection: "There's a quality of universal acceptance in you—a willingness to meet whatever comes without needing it to be different."
  },
  26: {
    essence: "Communicating value",
    reflection: "You have a gift for conveying the worth of things, whether ideas, products, or people. Your enthusiasm can open doors."
  },
  27: {
    essence: "Caring for what matters",
    reflection: "You have a nurturing capacity that extends to people, projects, or causes. What you care for tends to grow."
  },
  28: {
    essence: "Finding meaning in the struggle",
    reflection: "You engage with challenges not because you have to, but because you sense there's something worth fighting for beneath the surface."
  },
  29: {
    essence: "The power of commitment",
    reflection: "When you say yes to something, you really mean it. Your dedication sees things through, even when they get difficult."
  },
  30: {
    essence: "Honoring your desires",
    reflection: "Your feelings point toward experiences you need to have. Following your emotional yearnings is part of your path."
  },
  31: {
    essence: "A voice that influences",
    reflection: "You can speak in ways that move others. This influence works best when it emerges from your own lived truth."
  },
  32: {
    essence: "Knowing what will last",
    reflection: "You have a sense for what has staying power. This instinct for continuity helps you invest in things that matter over time."
  },
  33: {
    essence: "The value of retreat",
    reflection: "You understand that stepping back is sometimes the wisest move. Your memories and reflections have real worth."
  },
  34: {
    essence: "Pure available energy",
    reflection: "You have power available when it's needed. The key is responding to what genuinely calls for your strength."
  },
  35: {
    essence: "Hungry for new experiences",
    reflection: "You're here to taste many things. This drive for variety and progress keeps life fresh and meaningful."
  },
  36: {
    essence: "Growing through emotional intensity",
    reflection: "You learn through feeling deeply, even when it's uncomfortable. These experiences are shaping something in you."
  },
  37: {
    essence: "Creating bonds of belonging",
    reflection: "You understand the value of community and family. The agreements you make with others create containers for mutual care."
  },
  38: {
    essence: "Standing for what matters",
    reflection: "There's a fighter in you that won't back down when something important is at stake. Your stubbornness has purpose."
  },
  39: {
    essence: "Stirring what needs to move",
    reflection: "You have a way of provoking reactions in others that can actually free them. Sometimes tension is the path to liberation."
  },
  40: {
    essence: "The restoration of solitude",
    reflection: "You need time alone to replenish. This isn't avoidance—it's how you maintain the capacity to show up fully."
  },
  41: {
    essence: "The seed of new feelings",
    reflection: "Your imagination and desires initiate emotional journeys. What you dream up tends to create real experiences."
  },
  42: {
    essence: "Bringing things to completion",
    reflection: "You have a gift for finishing what you start. Completion is satisfying to you in a way others might not understand."
  },
  43: {
    essence: "Breakthrough knowing",
    reflection: "Insights come to you suddenly, often differently than they come to others. Trusting these inner knowings is part of your path."
  },
  44: {
    essence: "Reading patterns from the past",
    reflection: "You sense echoes of the past in the present. This pattern recognition helps you navigate based on what came before."
  },
  45: {
    essence: "Gathering and distributing",
    reflection: "You have a natural capacity to bring resources together and share them. Abundance flows through you to others."
  },
  46: {
    essence: "Being at home in your body",
    reflection: "Your body knows things. When you're present in physical experience, you encounter a kind of serendipity and rightness."
  },
  47: {
    essence: "Making sense of the abstract",
    reflection: "Your mind works through confusion to find meaning. The pressure you feel mentally eventually resolves into realization."
  },
  48: {
    essence: "Depth that waits to be called",
    reflection: "You have access to deep wisdom, but it serves best when it's drawn out by life rather than pushed forward prematurely."
  },
  49: {
    essence: "The courage to change allegiances",
    reflection: "You feel strongly about what's right. This clarity about principles gives you the courage to accept or reject based on deeper values."
  },
  50: {
    essence: "Upholding what matters",
    reflection: "You carry a sense of responsibility for maintaining important values. Taking care of what needs protecting is natural to you."
  },
  51: {
    essence: "The spark of initiative",
    reflection: "You have the capacity to leap first, to take the shock of the new so others can follow. Courage initiates."
  },
  52: {
    essence: "The mountain of stillness",
    reflection: "You have access to a deep stillness that allows concentrated focus. When you're still, you become a stable presence."
  },
  53: {
    essence: "Beginning new cycles",
    reflection: "You feel the pressure to start things. This initiating energy wants to begin processes that will unfold over time."
  },
  54: {
    essence: "The drive to rise",
    reflection: "You have ambition and the energy to transform your circumstances. This upward momentum is meant to be used."
  },
  55: {
    essence: "Emotional depth and spirit",
    reflection: "You have access to rich emotional and spiritual states. The fullness and emptiness you feel are both meaningful."
  },
  56: {
    essence: "Weaving stories from experience",
    reflection: "You collect experiences and transform them into meaning. Sharing what you've learned through story is your gift."
  },
  57: {
    essence: "Trusting your intuition",
    reflection: "You have a quiet, penetrating clarity about what's safe and what isn't. This intuitive knowing operates in the present moment."
  },
  58: {
    essence: "The vitality of joy",
    reflection: "You bring a life-enhancing quality to things. Your aliveness and enthusiasm can correct what's stagnant or joyless."
  },
  59: {
    essence: "Breaking through barriers to intimacy",
    reflection: "You have the capacity to dissolve what separates people. This openness creates possibilities for genuine connection."
  },
  60: {
    essence: "Working within limitations",
    reflection: "You understand that constraints can be creative. Accepting what is limited allows you to find freedom within bounds."
  },
  61: {
    essence: "Comfortable with mystery",
    reflection: "You feel the pull to know the unknowable. This relationship with inner truth and mystery is part of your depth."
  },
  62: {
    essence: "Precision in expression",
    reflection: "You care about saying things correctly. This attention to detail in communication helps others understand clearly."
  },
  63: {
    essence: "Questioning toward completion",
    reflection: "You notice what's missing, what doesn't add up. This doubt is actually a gift for testing whether something is truly complete."
  },
  64: {
    essence: "Making sense of confusion",
    reflection: "You live with mental pressure to resolve what hasn't yet come together. The confusion you feel is the prelude to clarity."
  },
};

// ============================================================================
// LINE FLAVORS - How each line colors the expression
// ============================================================================
export const LINE_FLAVORS: Record<number, {
  approach: string;
  quality: string;
}> = {
  1: {
    approach: "through deep investigation",
    quality: "Your approach is to understand things from the foundation up, building secure knowledge before acting."
  },
  2: {
    approach: "with natural talent",
    quality: "You have an innate gift here that works best when you allow it to emerge naturally rather than forcing it."
  },
  3: {
    approach: "through trial and discovery",
    quality: "You learn what works by trying things out. Your mistakes are actually your greatest teachers."
  },
  4: {
    approach: "through relationship and community",
    quality: "Your expression here flows best through your network of connections and close relationships."
  },
  5: {
    approach: "as a practical solution",
    quality: "Others may project expectations onto you here. Your gift is offering universally applicable wisdom."
  },
  6: {
    approach: "with earned wisdom",
    quality: "You're here to eventually model what's possible. Your authority comes from your own life experience."
  },
};

// ============================================================================
// SPHERE DESCRIPTORS - Plain-English one-liners for each sphere
// ============================================================================
export const SPHERE_DESCRIPTORS: Record<string, string> = {
  // Purpose Arc
  lifes_work: "How you naturally contribute through work",
  evolution: "Your personal growth edge",
  radiance: "How your presence affects others",
  purpose: "The deeper direction of your life",
  
  // Love Arc
  attraction: "What draws you and others together",
  iq: "How your mind naturally works",
  eq: "How you navigate emotions in relationship",
  sq: "Your connection to intuition and spirit",
  core_wound: "Where tenderness holds hidden gifts",
  
  // Prosperity Arc
  brand: "What you're naturally known for",
  culture: "The environment where you thrive",
  vocation: "The work that feels aligned",
  pearl: "How abundance flows to you",
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

// Keep legacy exports for backward compatibility
export const GATE_THEMES: Record<number, { name: string; keywords: string[] }> = Object.fromEntries(
  Object.entries(GATE_INTERPRETATIONS).map(([key, value]) => [
    key,
    { name: value.essence, keywords: [] }
  ])
);

export const LINE_THEMES: Record<number, { name: string; quality: string }> = Object.fromEntries(
  Object.entries(LINE_FLAVORS).map(([key, value]) => [
    key,
    { name: value.approach, quality: value.quality }
  ])
);

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get the interpretation for a specific gate
 */
export function getGateInterpretation(gateNumber: number): { essence: string; reflection: string } {
  return GATE_INTERPRETATIONS[gateNumber] || { 
    essence: 'A unique quality within you', 
    reflection: 'This aspect of your design carries meaning that may reveal itself over time.' 
  };
}

/**
 * Get the line flavor
 */
export function getLineFlavor(lineNumber: number): { approach: string; quality: string } {
  return LINE_FLAVORS[lineNumber] || { 
    approach: 'in your own way', 
    quality: 'Your unique approach brings something valuable.' 
  };
}

/**
 * Get the sphere descriptor
 */
export function getSphereDescriptor(sphereName: string): string {
  return SPHERE_DESCRIPTORS[sphereName] || 'An aspect of your design';
}

/**
 * Get the theme information for a specific gate (legacy support)
 */
export function getGateTheme(gateNumber: number): { name: string; keywords: string[] } {
  const interp = getGateInterpretation(gateNumber);
  return { name: interp.essence, keywords: [] };
}

/**
 * Get the theme information for a specific line (legacy support)
 */
export function getLineTheme(lineNumber: number): { name: string; quality: string } {
  const flavor = getLineFlavor(lineNumber);
  return { name: flavor.approach, quality: flavor.quality };
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
 * Generate a meaning-first interpretation for a sphere
 * This is the main function for the new meaning-first cards
 */
export function generateSphereInterpretation(
  sphereName: string,
  gate: number,
  line: number
): {
  sphereTitle: string;
  sphereDescriptor: string;
  meaningInterpretation: string;
  technicalGateLine: string;
  sourceLabel: string;
} {
  const role = getSequenceRole(sphereName);
  const gateInterp = getGateInterpretation(gate);
  const lineFlavor = getLineFlavor(line);
  const descriptor = getSphereDescriptor(sphereName);
  
  // Build meaning-first interpretation combining gate essence with line approach
  // This creates original, contextual language without copyrighted text
  let interpretation = gateInterp.reflection;
  
  // Add line flavor as a subtle modifier
  if (lineFlavor.quality) {
    interpretation = `${interpretation} ${lineFlavor.quality}`;
  }
  
  return {
    sphereTitle: role.title,
    sphereDescriptor: descriptor,
    meaningInterpretation: interpretation,
    technicalGateLine: `Gate ${gate} • Line ${line}`,
    sourceLabel: '', // Will be filled by component with source_planet + chart
  };
}

/**
 * Format a complete sequence explanation in everyday language (legacy support)
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
  const interp = generateSphereInterpretation(roleName, gate, line);
  const role = getSequenceRole(roleName);
  
  return {
    title: interp.sphereTitle,
    themeLabel: interp.sphereDescriptor,
    description: interp.meaningInterpretation,
    technicalValue: interp.technicalGateLine,
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
