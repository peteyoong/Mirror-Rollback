// ============================================
// HUMAN DESIGN SYNTHESIS LAYER
// ============================================
// Master-level integration of all HD mechanics into a unified reading
// NOT fragments - SYNTHESIS

export interface HDSynthesis {
  corePattern: string;
  coreTension: string;
  howThisPlaysOut: string[];
  blindSpot: string;
  edge: string;
  whatSupportsYou: string[];
}

export interface HDSynthesisInput {
  type: string;
  authority: string;
  profile: string;
  definition?: string;
  incarnationCross?: string;
  channels?: string[];
  definedCenters?: string[];
  undefinedCenters?: string[];
  // Variables (if available)
  environment?: string;
  cognition?: string;
  determination?: string;
  motivation?: string;
  transference?: string;
  // Personality vs Design split
  personalitySun?: string;
  designSun?: string;
  personalityEarth?: string;
  designEarth?: string;
}

// ============================================
// TYPE × AUTHORITY SYNTHESIS
// The main operating paradox
// ============================================

interface TypeAuthorityPattern {
  corePattern: string;
  coreTension: string;
  blindSpot: string;
  edge: string;
}

const TYPE_AUTHORITY_SYNTHESIS: { [key: string]: { [auth: string]: TypeAuthorityPattern } } = {
  'Manifestor': {
    'Emotional': {
      corePattern: "You are built to initiate—but your clarity doesn't come instantly. So you move, then understand after.",
      coreTension: "You feel the urge to act now—but the truth isn't settled yet. The world expects decisive Manifestors, but your process requires time you rarely give yourself.",
      blindSpot: "You think the issue is other people resisting you. Often, it's that you moved before your emotional wave had settled into real knowing.",
      edge: "When you inform AND wait for emotional clarity before committing, your impact lands cleanly and others feel included rather than blindsided."
    },
    'Splenic': {
      corePattern: "You are designed to move on instinct—a flash of knowing that doesn't repeat. Your power is in catching that moment and acting before thinking talks you out of it.",
      coreTension: "The hit comes once, quiet and clear. But the pressure to explain or justify makes you second-guess what your body already knew.",
      blindSpot: "You wait for certainty that already came and went. The first knowing was the answer—everything after is just noise.",
      edge: "When you trust the first hit and inform before moving, you navigate with precision others can't match."
    },
    'Ego': {
      corePattern: "You move from will—genuine desire is your engine. When your heart is in it, you're unstoppable. When it's not, nothing moves.",
      coreTension: "You commit based on what you think you should want, then run out of fuel because the desire wasn't real.",
      blindSpot: "Broken promises aren't about discipline. They're about making commitments your heart never agreed to.",
      edge: "When you only commit to what you genuinely want, your follow-through becomes legendary."
    },
    'Self-Projected': {
      corePattern: "You find direction by hearing yourself speak. The truth emerges through expression, not isolated decision-making.",
      coreTension: "You think you should figure it out alone, but decisions made in your head miss what becomes obvious the moment you say it.",
      blindSpot: "Waiting for internal clarity that only comes externally. Your voice IS your processing.",
      edge: "When you find trusted sounding boards and let yourself talk through directions before committing, clarity appears."
    },
    'None': {
      corePattern: "You initiate without a fixed internal compass—your clarity comes from environment, not introspection.",
      coreTension: "You keep looking inside for answers that live outside. The right setting reveals the right direction.",
      blindSpot: "Forcing decisions in wrong environments. Your wisdom is place-dependent.",
      edge: "When you choose environments wisely before initiating, the direction becomes self-evident."
    }
  },
  
  'Generator': {
    'Emotional': {
      corePattern: "You have sustainable energy for what lights you up—but you don't know what that is until the emotional wave settles. Excitement isn't clarity; it's a data point.",
      coreTension: "Your gut responds instantly, but your emotional truth takes time. You're caught between the pull and the process.",
      blindSpot: "You say yes in a high because the pull feels real—then wonder why you're frustrated when the wave passes.",
      edge: "When you let your gut respond AND wait for emotional clarity, you commit to things that stay right."
    },
    'Sacral': {
      corePattern: "Your body knows before your mind catches up. The pull toward or away happens in the moment—no analysis required.",
      coreTension: "You've learned to override your gut with logic. But every time you talk yourself into something your body said no to, you end up drained.",
      blindSpot: "Ignoring the first response because it doesn't come with reasons. Your gut doesn't need to explain itself.",
      edge: "When you trust the visceral response—even without understanding why—your energy stays sustainable."
    }
  },
  
  'Manifesting Generator': {
    'Emotional': {
      corePattern: "You move fast and pivot often—but your clarity comes slow. The excitement is immediate; the truth unfolds over time.",
      coreTension: "Part of you is already three steps ahead. Another part needs to feel through whether those steps are real.",
      blindSpot: "Starting things in emotional highs that look different when the wave passes. Speed without settling creates false starts.",
      edge: "When you sample quickly but commit slowly, you find the paths that actually go somewhere."
    },
    'Sacral': {
      corePattern: "You respond instantly and multi-directionally. Multiple pulls at once, and your job is to follow the strongest one right now.",
      coreTension: "You're called inconsistent because you pivot before others understand why. But forcing yourself through dead tracks is what actually drains you.",
      blindSpot: "Guilt over not finishing what lost its energy. Completion isn't about the end—it's about extracting what was yours.",
      edge: "When you trust the pivot and let your body lead, you find efficiency others can't match."
    }
  },
  
  'Projector': {
    'Emotional': {
      corePattern: "You see deeply into systems and people—but you don't know what to do with that sight until the wave settles.",
      coreTension: "You're invited to guide, but your clarity isn't instant. The pressure to respond immediately leads to guidance that doesn't land.",
      blindSpot: "Giving advice in emotional peaks that you'd word differently in neutral. Recognition doesn't mean readiness.",
      edge: "When you wait for emotional clarity before offering guidance, your insight transforms rather than deflects."
    },
    'Splenic': {
      corePattern: "You see what others miss—and you know it in a flash. The hit is subtle, once, and gone if you don't catch it.",
      coreTension: "Your insight is instant, but recognition doesn't always come at the same speed. You see the answer before anyone asks.",
      blindSpot: "Waiting to be asked when you already know. Sometimes the knowing fades while you wait for the invitation.",
      edge: "When recognition and intuition align, your guidance has precision that cuts through noise."
    },
    'Self-Projected': {
      corePattern: "You understand others by talking through what you see. Your voice reveals your knowing—to yourself and to them.",
      coreTension: "You hold back insight because you're not sure it's right—but speaking is how you'd know.",
      blindSpot: "Waiting for internal certainty that only comes through expression. Your clarity lives in your voice.",
      edge: "When you're invited and you speak, the truth emerges for everyone—including you."
    },
    'Ego': {
      corePattern: "You guide from genuine desire. When your heart is in the invitation, your impact is undeniable.",
      coreTension: "You accept invitations based on should rather than want, then run out of energy because desire wasn't there.",
      blindSpot: "Bitterness from giving to people your heart never chose. Your will only sustains what it wants.",
      edge: "When you only accept invitations that genuinely excite you, your guidance has staying power."
    },
    'Mental': {
      corePattern: "Your insight comes through environment and conversation. You process others' questions by bouncing them off different perspectives.",
      coreTension: "You try to guide from your head alone, but clarity only comes when you've discussed it in the right setting.",
      blindSpot: "Forcing answers in wrong environments. Your wisdom is context-dependent.",
      edge: "When you guide from environments that support your thinking, your insight becomes unusually clear."
    },
    'None': {
      corePattern: "You see into others deeply, but your own clarity depends on where you are. Environment shapes your guidance.",
      coreTension: "Looking inside for direction when the answers live in your surroundings.",
      blindSpot: "Trying to be consistent when your wisdom shifts with place.",
      edge: "When you choose your environments wisely, the guidance you offer becomes precisely attuned."
    }
  },
  
  'Reflector': {
    'Lunar': {
      corePattern: "You take in everything—and you need time to know what's actually yours. A full cycle reveals what stays true.",
      coreTension: "The world rushes you. But your clarity unfolds over 28 days, not 28 minutes.",
      blindSpot: "Making decisions from one day's reflection. You need the whole cycle to see clearly.",
      edge: "When you give yourself a full lunar cycle, you access wisdom that faster types can't reach."
    }
  }
};

// ============================================
// PROFILE × DEFINITION DYNAMICS
// How you relate and process
// ============================================

interface ProfileDefinitionPattern {
  relationalDynamic: string;
  processingPattern: string;
}

const getProfileDefinitionSynthesis = (profile: string, definition?: string): ProfileDefinitionPattern => {
  const firstLine = profile?.split('/')[0];
  const secondLine = profile?.split('/')[1];
  
  let relationalDynamic = '';
  let processingPattern = '';
  
  // Line-based relational patterns
  if (firstLine === '1') {
    relationalDynamic = "You need to feel secure in your foundation before engaging deeply with others.";
  } else if (firstLine === '2') {
    relationalDynamic = "You have natural gifts that others see before you do—relationships often call these out.";
  } else if (firstLine === '3') {
    relationalDynamic = "You learn about relationships through trial—bonds that work teach you as much as bonds that break.";
  } else if (firstLine === '4') {
    relationalDynamic = "Your opportunities flow through your network—closeness and trust are how things happen for you.";
  } else if (firstLine === '5') {
    relationalDynamic = "People project onto you—they expect you to solve things, sometimes before you've offered.";
  } else if (firstLine === '6') {
    relationalDynamic = "You're shifting from being in the mix to observing it—your role in relationships is maturing.";
  }
  
  // Definition-based processing
  if (definition === 'Single') {
    processingPattern = "You process internally and consistently. You don't need others to complete your thinking.";
  } else if (definition === 'Split') {
    processingPattern = "Part of you operates differently than another part. You often need others or environments to bridge the gap.";
  } else if (definition === 'Triple Split') {
    processingPattern = "Multiple parts of you function independently. Busy environments with variety help you feel whole.";
  } else if (definition === 'Quadruple Split') {
    processingPattern = "You have four distinct ways of operating. Integration takes time; don't rush your process.";
  } else if (definition === 'None') {
    processingPattern = "You have no fixed definition—you're designed to sample and reflect, not to operate consistently.";
  } else {
    processingPattern = "Your internal processing has its own rhythm—honor it rather than forcing consistency.";
  }
  
  return { relationalDynamic, processingPattern };
};

// ============================================
// CONSCIOUS vs UNCONSCIOUS PATTERNS
// What you see vs what drives you
// ============================================

const getConsciousUnconsciousPattern = (
  type: string,
  profile: string,
  personalitySun?: string,
  designSun?: string
): string => {
  const firstLine = profile?.split('/')[0];
  const secondLine = profile?.split('/')[1];
  
  // The second line is unconscious - what drives without awareness
  const unconsciousPatterns: { [key: string]: string } = {
    '1': "Your body is always seeking foundation—even when your mind thinks it's ready to move.",
    '2': "Something natural operates through you without trying—others often see it before you claim it.",
    '3': "Part of you keeps experimenting even when you think you've settled. The trial continues underneath.",
    '4': "Your body is network-oriented—relationships shift your direction more than you consciously choose.",
    '5': "You attract projections whether you want them or not. Something about you suggests solutions.",
    '6': "A part of you is always observing—taking notes for a role you're growing into."
  };
  
  const conscious = firstLine ? `You consciously identify with ${firstLine === '1' ? 'investigation and foundation' : firstLine === '2' ? 'natural ability and hermit needs' : firstLine === '3' ? 'experimentation and discovery' : firstLine === '4' ? 'networking and influence' : firstLine === '5' ? 'practical solutions and universalizing' : 'role modeling and wisdom'}.` : '';
  
  const unconscious = secondLine ? unconsciousPatterns[secondLine] || '' : '';
  
  if (unconscious) {
    return `You think you're operating one way, but underneath: ${unconscious.toLowerCase()}`;
  }
  
  return "The part of you that drives behavior isn't always the part you're aware of.";
};

// ============================================
// HOW THIS PLAYS OUT - Real Life Patterns
// ============================================

const generateHowThisPlaysOut = (
  type: string,
  authority: string,
  profile: string,
  definition?: string
): string[] => {
  const patterns: string[] = [];
  
  // Type × Authority behavioral patterns
  if (type === 'Manifestor' && authority === 'Emotional') {
    patterns.push("You make a decision, then question it later when the wave passes");
    patterns.push("People expect certainty from you before you feel it");
    patterns.push("You trigger reactions just by moving faster than others process");
  } else if (type === 'Manifestor' && authority === 'Splenic') {
    patterns.push("You act on instinct, then watch others struggle to keep up");
    patterns.push("You know things before you can explain them—and sometimes never can");
    patterns.push("Hesitation costs you the clarity that was already there");
  } else if (type === 'Generator' && authority === 'Emotional') {
    patterns.push("You say yes in excitement, then feel trapped when the wave passes");
    patterns.push("Your gut responds immediately, but you've learned to wait");
    patterns.push("Frustration builds when you commit before the feeling settles");
  } else if (type === 'Generator' && authority === 'Sacral') {
    patterns.push("Your body says yes or no before your mind catches up");
    patterns.push("You override your gut with logic—and regret it later");
    patterns.push("Energy flows when you follow response; drains when you force");
  } else if (type === 'Manifesting Generator' && authority === 'Emotional') {
    patterns.push("You start things fast, then discover the emotional truth later");
    patterns.push("Pivoting makes sense to your body before it makes sense to others");
    patterns.push("The high of starting can mask whether something is actually right");
  } else if (type === 'Manifesting Generator' && authority === 'Sacral') {
    patterns.push("Multiple pulls at once—you follow the strongest right now");
    patterns.push("What looks like quitting is often your body finding the real path");
    patterns.push("Efficiency comes from skipping what doesn't respond, not from forcing completion");
  } else if (type === 'Projector' && authority === 'Emotional') {
    patterns.push("You see what others miss—but knowing what to do with it takes time");
    patterns.push("You give guidance in highs that you'd phrase differently in neutral");
    patterns.push("Waiting for recognition AND emotional clarity tests your patience");
  } else if (type === 'Projector' && authority === 'Splenic') {
    patterns.push("You catch insight in a flash—but the invitation doesn't always match the timing");
    patterns.push("The knowing fades if you wait too long to speak it");
    patterns.push("Your guidance is precise when you trust the first hit");
  } else if (type === 'Reflector') {
    patterns.push("You feel completely different depending on who you're with");
    patterns.push("Fast decisions rarely survive the full cycle");
    patterns.push("Your clarity is lunar—it needs time others don't understand");
  }
  
  // Profile-based patterns
  const firstLine = profile?.split('/')[0];
  if (firstLine === '1') {
    patterns.push("You research longer than others think necessary—but your foundation holds");
  } else if (firstLine === '3') {
    patterns.push("You learn more from what went wrong than from what went right");
  } else if (firstLine === '5') {
    patterns.push("People expect solutions from you before you've offered any");
  } else if (firstLine === '6') {
    patterns.push("You're starting to observe life differently than when you were in the middle of it");
  }
  
  // Definition patterns
  if (definition === 'Split') {
    patterns.push("You feel more complete around certain people or in certain environments");
  } else if (definition === 'Triple Split' || definition === 'Quadruple Split') {
    patterns.push("Different parts of you come online in different contexts—integration takes time");
  }
  
  return patterns.slice(0, 5); // Max 5 patterns
};

// ============================================
// WHAT SUPPORTS YOU - Environment & Conditions
// ============================================

const generateWhatSupportsYou = (
  type: string,
  authority: string,
  profile: string,
  definition?: string,
  environment?: string
): string[] => {
  const supports: string[] = [];
  
  // Authority-based support
  if (authority === 'Emotional') {
    supports.push("Time between impulse and commitment");
    supports.push("People who don't rush your clarity");
  } else if (authority === 'Sacral') {
    supports.push("Yes/no questions rather than open-ended ones");
    supports.push("Space to respond rather than initiate");
  } else if (authority === 'Splenic') {
    supports.push("Environments where you can act on instinct");
    supports.push("Trust in the first knowing");
  } else if (authority === 'Ego') {
    supports.push("Commitments that genuinely excite you");
    supports.push("Freedom to follow your will, not obligation");
  } else if (authority === 'Self-Projected') {
    supports.push("Sounding boards who listen without directing");
    supports.push("Time to talk things through before deciding");
  } else if (authority === 'Mental' || authority === 'None') {
    supports.push("Multiple perspectives and environments before deciding");
  } else if (authority === 'Lunar') {
    supports.push("A full 28-day cycle before major decisions");
  }
  
  // Type-based support
  if (type === 'Manifestor') {
    supports.push("Environments with movement and information flow");
    supports.push("Relationships that don't require constant explanation");
  } else if (type === 'Generator' || type === 'Manifesting Generator') {
    supports.push("Work that lights you up rather than drains you");
    supports.push("Freedom to follow your response, not others' agendas");
  } else if (type === 'Projector') {
    supports.push("Invitations to share your insight");
    supports.push("Recognition before being asked to contribute");
  } else if (type === 'Reflector') {
    supports.push("Environments that feel genuinely healthy");
    supports.push("People who understand your lunar rhythm");
  }
  
  // Definition support
  if (definition === 'Split') {
    supports.push("People or places that bridge your energy without you trying");
  } else if (definition?.includes('Triple') || definition?.includes('Quadruple')) {
    supports.push("Busy environments with variety of energy");
  }
  
  // Profile-based support
  const firstLine = profile?.split('/')[0];
  if (firstLine === '1') {
    supports.push("Time to build foundations before being pushed to act");
  } else if (firstLine === '2') {
    supports.push("Alone time to develop what comes naturally");
  } else if (firstLine === '4') {
    supports.push("Close relationships where opportunities emerge organically");
  }
  
  return supports.slice(0, 5); // Max 5 supports
};

// ============================================
// MAIN SYNTHESIS GENERATOR
// ============================================

export function generateHDSynthesis(input: HDSynthesisInput): HDSynthesis | null {
  const { type, authority, profile, definition, incarnationCross } = input;
  
  if (!type || !authority) {
    return null;
  }
  
  // Get Type × Authority synthesis (core pattern)
  const typeAuthority = TYPE_AUTHORITY_SYNTHESIS[type]?.[authority];
  
  if (!typeAuthority) {
    // Fallback for missing combinations
    return generateFallbackSynthesis(input);
  }
  
  // Get Profile × Definition patterns
  const profileDef = getProfileDefinitionSynthesis(profile, definition);
  
  // Get Conscious vs Unconscious pattern
  const consciousUnconscious = getConsciousUnconsciousPattern(
    type,
    profile,
    input.personalitySun,
    input.designSun
  );
  
  // Generate How This Plays Out
  const howThisPlaysOut = generateHowThisPlaysOut(type, authority, profile, definition);
  
  // Generate What Supports You
  const whatSupportsYou = generateWhatSupportsYou(type, authority, profile, definition, input.environment);
  
  // Enhance core tension with profile dynamics
  let enhancedTension = typeAuthority.coreTension;
  if (profileDef.processingPattern && definition === 'Split') {
    enhancedTension += ` And because you have Split Definition, parts of you process at different speeds—making the gap feel wider.`;
  }
  
  // Enhance blind spot with conscious/unconscious pattern
  let enhancedBlindSpot = typeAuthority.blindSpot;
  if (consciousUnconscious) {
    enhancedBlindSpot += ` ${consciousUnconscious}`;
  }
  
  return {
    corePattern: typeAuthority.corePattern,
    coreTension: enhancedTension,
    howThisPlaysOut,
    blindSpot: enhancedBlindSpot,
    edge: typeAuthority.edge,
    whatSupportsYou
  };
}

// Fallback for combinations not explicitly mapped
function generateFallbackSynthesis(input: HDSynthesisInput): HDSynthesis {
  const { type, authority, profile, definition } = input;
  
  let corePattern = '';
  let coreTension = '';
  let blindSpot = '';
  let edge = '';
  
  // Generate based on type
  if (type === 'Generator') {
    corePattern = "You have sustainable energy for what genuinely excites you—the work is learning to tell the difference between real response and mental override.";
  } else if (type === 'Manifesting Generator') {
    corePattern = "You move fast and in multiple directions—your efficiency comes from following response, not from forcing completion.";
  } else if (type === 'Projector') {
    corePattern = "You see what others miss—and your insight transforms when it's genuinely invited, not just offered.";
  } else if (type === 'Manifestor') {
    corePattern = "You're built to initiate what doesn't exist yet—the work is learning to inform before you move.";
  } else if (type === 'Reflector') {
    corePattern = "You take in everything around you—the work is learning what's yours and what's borrowed.";
  }
  
  // Generate tension based on authority
  if (authority === 'Emotional') {
    coreTension = "Your clarity doesn't come instantly. What feels true in one moment may shift as the wave moves—waiting is the work.";
  } else if (authority === 'Sacral') {
    coreTension = "Your body knows before your mind does. The tension is trusting response over reason.";
  } else if (authority === 'Splenic') {
    coreTension = "The knowing comes once, quiet and fast. The tension is catching it before thinking drowns it out.";
  } else {
    coreTension = "Your clarity has its own rhythm—forcing it to match others' timelines creates friction.";
  }
  
  blindSpot = "You often see the pattern more clearly in hindsight. The work is catching it sooner.";
  edge = "When you honor your natural rhythm instead of fighting it, everything flows more easily.";
  
  return {
    corePattern,
    coreTension,
    howThisPlaysOut: generateHowThisPlaysOut(type, authority, profile, definition),
    blindSpot,
    edge,
    whatSupportsYou: generateWhatSupportsYou(type, authority, profile, definition)
  };
}

// Check if synthesis is available
export function canGenerateSynthesis(type: string, authority: string): boolean {
  return !!(type && authority);
}
