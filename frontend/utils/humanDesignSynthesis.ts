// ============================================
// HUMAN DESIGN MASTER SYNTHESIS LAYER
// ============================================
// COMPRESSION + PUNCH VERSION
// Now enhanced with PROGRAMMING PARTNERS for deeper polarity tension
// Sharp. Clear. Undeniable.
// Names reality. Doesn't explain systems.

import {
  getDominantPolarities,
  enhanceTensionWithPolarity,
  enhanceBlindSpotWithPolarity,
  enhanceEdgeWithPolarity,
  getPolarityBehavioralBullet,
  getPolarityRelationshipBullet,
  RankedPolarity,
  PolarityInput,
} from './programmingPartners';

export interface HDSynthesis {
  corePattern: string;
  coreTension: string;
  howThisPlaysOut: string[];
  blindSpot: string;
  edge: string;
  whatSupportsYou: string[];
}

export interface ChannelData {
  gates?: string;
  name?: string;
  circuit?: string;
  centers?: string[];
}

export interface HDSynthesisInput {
  type: string;
  authority: string;
  profile: string;
  definition?: string;
  incarnationCross?: string;
  incarnationCrossGates?: string;
  channels?: ChannelData[];
  definedCenters?: string[];
  undefinedCenters?: string[];
  consciousGates?: number[];
  unconsciousGates?: number[];
  personalitySun?: number | { gate: number; line: number };
  personalityEarth?: number | { gate: number; line: number };
  designSun?: number | { gate: number; line: number };
  designEarth?: number | { gate: number; line: number };
  environment?: string;
  cognition?: string;
  determination?: string;
  motivation?: string;
  transference?: string;
  perspective?: string;
  view?: string;
}

// ============================================
// DOMINANT PATTERN RANKING
// Identifies the 1-2 patterns that matter most
// ============================================

interface DominantPattern {
  id: string;
  punchLine: string;
  tension: string;
  blindSpot: string;
  edge: string;
  conflictStrength: number; // 1-10
  behavioralFrequency: number; // 1-10
}

function rankDominantPatterns(input: HDSynthesisInput): DominantPattern[] {
  const patterns: DominantPattern[] = [];
  const { type, authority, profile, definition, channels } = input;
  
  // TYPE × AUTHORITY CONFLICT (usually highest impact)
  const typeAuthConflict = getTypeAuthorityConflict(type, authority);
  if (typeAuthConflict) {
    patterns.push({
      ...typeAuthConflict,
      id: 'type_authority',
      conflictStrength: typeAuthConflict.conflictStrength || 9,
      behavioralFrequency: 10
    });
  }
  
  // PROFILE CONFLICT (conscious vs unconscious lines)
  const profileConflict = getProfileConflict(profile, authority);
  if (profileConflict) {
    patterns.push({
      ...profileConflict,
      id: 'profile',
      conflictStrength: profileConflict.conflictStrength || 7,
      behavioralFrequency: 9
    });
  }
  
  // SPLIT DEFINITION (relational mechanics)
  if (definition && definition !== 'Single') {
    const splitConflict = getSplitConflict(definition);
    if (splitConflict) {
      patterns.push({
        ...splitConflict,
        id: 'definition',
        conflictStrength: 7,
        behavioralFrequency: 8
      });
    }
  }
  
  // CHANNEL DOMINANT (if channel creates strong theme)
  if (channels && channels.length > 0) {
    const channelConflict = getChannelConflict(channels[0]);
    if (channelConflict) {
      patterns.push({
        ...channelConflict,
        id: 'channel',
        conflictStrength: channelConflict.conflictStrength || 6,
        behavioralFrequency: 7
      });
    }
  }
  
  // Sort by combined impact score
  return patterns.sort((a, b) => 
    (b.conflictStrength + b.behavioralFrequency) - (a.conflictStrength + a.behavioralFrequency)
  );
}

// ============================================
// TYPE × AUTHORITY PUNCH PATTERNS
// Sharp, compressed, immediate
// ============================================

interface TypeAuthPunch {
  punchLine: string;
  tension: string;
  blindSpot: string;
  edge: string;
  conflictStrength: number;
}

function getTypeAuthorityConflict(type: string, authority: string): TypeAuthPunch | null {
  const key = `${type}_${authority}`;
  
  const patterns: { [key: string]: TypeAuthPunch } = {
    // MANIFESTOR
    'Manifestor_Emotional': {
      punchLine: "You move before you're clear—and deal with it after.",
      tension: "The urge to act hits now. The truth takes time. You rarely wait.",
      blindSpot: "You think others resist you. Often, you just moved too early.",
      edge: "When you inform AND wait for clarity, your impact lands clean.",
      conflictStrength: 9
    },
    'Manifestor_Splenic': {
      punchLine: "You know instantly—but explain it never.",
      tension: "The hit comes once. You either catch it or lose it.",
      blindSpot: "You wait for reasons that already came and went.",
      edge: "Trust the first knowing. Act before thinking talks you out of it.",
      conflictStrength: 7
    },
    'Manifestor_Ego': {
      punchLine: "When your heart's in it, you're unstoppable. When it's not, nothing moves.",
      tension: "You commit to what you should want—then run out of fuel.",
      blindSpot: "Broken promises aren't about discipline. Your heart never agreed.",
      edge: "Only commit to what you actually want. Follow-through becomes effortless.",
      conflictStrength: 8
    },
    'Manifestor_Self-Projected': {
      punchLine: "You don't know until you hear yourself say it.",
      tension: "You wait for internal clarity that only comes through speaking.",
      blindSpot: "Silence keeps you stuck. Your voice IS your processing.",
      edge: "Talk it through. The direction emerges as you speak.",
      conflictStrength: 6
    },
    'Manifestor_None': {
      punchLine: "Your clarity lives in place, not in your head.",
      tension: "You look inside for answers that live outside.",
      blindSpot: "Forcing decisions in wrong environments. Your wisdom is location-dependent.",
      edge: "Choose environments wisely. Direction becomes obvious.",
      conflictStrength: 5
    },
    
    // GENERATOR
    'Generator_Emotional': {
      punchLine: "Your gut says yes. Your wave says wait.",
      tension: "Response is instant. Truth unfolds over time. You're caught between.",
      blindSpot: "You say yes in highs—then feel trapped when the wave passes.",
      edge: "Let your gut respond, then wait. What stays lit is real.",
      conflictStrength: 9
    },
    'Generator_Sacral': {
      punchLine: "Your body knows. Your mind catches up later.",
      tension: "The pull happens before reasons. You've learned to override it.",
      blindSpot: "Ignoring the first response because it doesn't explain itself.",
      edge: "Trust the gut. Even without reasons. Especially without reasons.",
      conflictStrength: 7
    },
    
    // MANIFESTING GENERATOR
    'Manifesting Generator_Emotional': {
      punchLine: "You move fast. Your clarity doesn't.",
      tension: "Part of you is three steps ahead. Part needs to feel it through.",
      blindSpot: "Speed without settling creates false starts. Excitement isn't clarity.",
      edge: "Sample fast. Commit slow. What survives the wave is yours.",
      conflictStrength: 9
    },
    'Manifesting Generator_Sacral': {
      punchLine: "You pivot faster than others understand.",
      tension: "They call it inconsistent. You call it following what's alive.",
      blindSpot: "Guilt over not finishing what lost its energy.",
      edge: "Trust the pivot. Completion isn't the end—it's extracting what's yours.",
      conflictStrength: 7
    },
    
    // PROJECTOR
    'Projector_Emotional': {
      punchLine: "You see deeply—but you don't know what to do with it until later.",
      tension: "Invited to guide, but your clarity isn't instant.",
      blindSpot: "Giving advice in peaks you'd word differently in neutral.",
      edge: "Wait for the wave. Your insight transforms when it's settled.",
      conflictStrength: 8
    },
    'Projector_Splenic': {
      punchLine: "You see the answer before anyone asks.",
      tension: "Insight is instant. Recognition is slow.",
      blindSpot: "Waiting to be asked when you already know. The knowing fades.",
      edge: "When recognition and intuition align, you cut through noise.",
      conflictStrength: 7
    },
    'Projector_Self-Projected': {
      punchLine: "You understand others by hearing yourself describe them.",
      tension: "You hold back insight because you're not sure. Speaking is how you'd know.",
      blindSpot: "Waiting for certainty that only comes through voice.",
      edge: "When invited, speak. Truth emerges for everyone—including you.",
      conflictStrength: 6
    },
    'Projector_Ego': {
      punchLine: "When your heart's in the invitation, your impact is undeniable.",
      tension: "You accept based on should. Run out of energy because desire wasn't there.",
      blindSpot: "Bitterness from giving to people your heart never chose.",
      edge: "Only accept what genuinely excites you. Your guidance has staying power.",
      conflictStrength: 7
    },
    'Projector_Mental': {
      punchLine: "Your clarity depends on who you're talking to and where.",
      tension: "You try to guide from your head alone. It only works in the right setting.",
      blindSpot: "Forcing answers in wrong environments. Your wisdom is context-dependent.",
      edge: "Find the right setting. Your insight becomes unusually clear.",
      conflictStrength: 5
    },
    'Projector_None': {
      punchLine: "You see into others deeply. Your own clarity shifts with place.",
      tension: "Looking inside when the answers live outside.",
      blindSpot: "Trying to be consistent when your wisdom genuinely shifts.",
      edge: "Choose environments wisely. Your guidance becomes precisely attuned.",
      conflictStrength: 5
    },
    
    // REFLECTOR
    'Reflector_Lunar': {
      punchLine: "You take in everything. You need time to know what's yours.",
      tension: "The world rushes. Your clarity needs 28 days, not 28 minutes.",
      blindSpot: "Deciding from one day's reflection. You need the whole cycle.",
      edge: "Give yourself the full cycle. You access wisdom faster types can't reach.",
      conflictStrength: 8
    }
  };
  
  return patterns[key] || patterns[`${type}_Emotional`] || generateFallbackPunch(type, authority);
}

function generateFallbackPunch(type: string, authority: string): TypeAuthPunch {
  const typePatterns: { [key: string]: TypeAuthPunch } = {
    'Generator': {
      punchLine: "Your body knows what lights you up. Your mind gets in the way.",
      tension: "Response is simple. Conditioning made it complicated.",
      blindSpot: "Overriding your gut with logic. Every override leads to frustration.",
      edge: "Trust the pull. Even without understanding. Satisfaction follows.",
      conflictStrength: 7
    },
    'Manifesting Generator': {
      punchLine: "You move in multiple directions. That's not scattered—it's how you work.",
      tension: "Others want you to pick one thing. Your design is multi-track.",
      blindSpot: "Forcing yourself through dead tracks. Staying out of obligation.",
      edge: "Follow the strongest pull. Pivot when it's done.",
      conflictStrength: 7
    },
    'Projector': {
      punchLine: "You see what others miss. Your insight transforms when invited.",
      tension: "Seeing clearly but sharing without invitation leads to bitterness.",
      blindSpot: "Offering guidance because you can see it—not because anyone asked.",
      edge: "Wait for recognition. Your seeing becomes your most valuable gift.",
      conflictStrength: 7
    },
    'Manifestor': {
      punchLine: "You initiate what doesn't exist yet. The work is informing first.",
      tension: "The urge to act meets resistance from people unprepared for your movement.",
      blindSpot: "Moving without informing, then resenting the pushback.",
      edge: "Inform before you move. Your power flows without friction.",
      conflictStrength: 7
    },
    'Reflector': {
      punchLine: "You feel completely different depending on who you're with. That's design, not instability.",
      tension: "The world wants consistency. You're designed to reflect.",
      blindSpot: "Trying to hold a fixed identity when you're meant to sample.",
      edge: "Choose your environments. You will become what you're around.",
      conflictStrength: 7
    }
  };
  
  return typePatterns[type] || typePatterns['Generator'];
}

// ============================================
// PROFILE CONFLICT PUNCH PATTERNS
// Conscious vs Unconscious line tensions
// ============================================

function getProfileConflict(profile: string, authority: string): DominantPattern | null {
  if (!profile) return null;
  
  const [firstLine, secondLine] = profile.split('/').map(Number);
  
  // Second line is unconscious - drives behavior without awareness
  const unconsciousPatterns: { [key: number]: { punch: string; blind: string } } = {
    1: { 
      punch: "Your body needs foundation before your mind feels ready to move.",
      blind: "You think you're ready. Underneath, you're still researching."
    },
    2: { 
      punch: "Something operates through you without effort. Others see it before you do.",
      blind: "You dismiss your natural gifts because they come too easy."
    },
    3: { 
      punch: "Part of you keeps experimenting even when you think you've settled.",
      blind: "You're still in trial mode underneath. The experiment continues."
    },
    4: { 
      punch: "Relationships redirect you more than you consciously choose.",
      blind: "You think you're independent. Your body is network-oriented."
    },
    5: { 
      punch: "You attract projections whether you want them or not.",
      blind: "People expect solutions before you've offered any."
    },
    6: { 
      punch: "Part of you is always watching—taking notes for a future role.",
      blind: "You're observing life differently than when you were in it."
    }
  };
  
  const consciousPatterns: { [key: number]: string } = {
    1: "You investigate. You build foundations. You need to know.",
    2: "You wait to be called. Your gifts emerge when recognized.",
    3: "You learn by trying. Failure is data, not defeat.",
    4: "You influence through close bonds. Strangers aren't your market.",
    5: "You're seen as having answers. The projection is real.",
    6: "You're meant to be an example. But only after living it first."
  };
  
  const unconscious = unconsciousPatterns[secondLine];
  const conscious = consciousPatterns[firstLine];
  
  if (!unconscious) return null;
  
  return {
    id: 'profile',
    punchLine: `${conscious} ${unconscious.punch}`,
    tension: `Your conscious pattern says one thing. Your body is already doing something else.`,
    blindSpot: unconscious.blind,
    edge: `When both lines work together, you stop fighting yourself.`,
    conflictStrength: 7,
    behavioralFrequency: 9
  };
}

// ============================================
// SPLIT DEFINITION PUNCH PATTERNS
// ============================================

function getSplitConflict(definition: string): DominantPattern | null {
  const patterns: { [key: string]: DominantPattern } = {
    'Split': {
      id: 'split',
      punchLine: "You're not designed to feel complete alone. Certain people bridge your gaps instantly.",
      tension: "Independence feels real but something's missing. That's design, not deficit.",
      blindSpot: "You think you should feel whole by yourself. You're not built that way.",
      edge: "Stop fighting the need. Let the right people complete your circuit.",
      conflictStrength: 7,
      behavioralFrequency: 8
    },
    'Triple Split': {
      id: 'triple_split',
      punchLine: "Three parts of you operate independently. Integration takes variety.",
      tension: "You feel like multiple people. Different contexts wake different aspects.",
      blindSpot: "Trying to integrate through isolation. You need busy environments.",
      edge: "Seek variety. Different energies connect your different parts.",
      conflictStrength: 7,
      behavioralFrequency: 8
    },
    'Quadruple Split': {
      id: 'quad_split',
      punchLine: "Four parts. Rarely unified. That's design, not disorder.",
      tension: "Full integration is rare. You're highly compartmentalized.",
      blindSpot: "Expecting to feel unified when you're built for multiplicity.",
      edge: "Accept the compartments. Stop trying to solve them.",
      conflictStrength: 6,
      behavioralFrequency: 7
    }
  };
  
  return patterns[definition] || null;
}

// ============================================
// CHANNEL PUNCH PATTERNS
// ============================================

interface ChannelPunch {
  punchLine: string;
  tension: string;
  blindSpot: string;
  edge: string;
  behavioral: string;
  conflictStrength: number;
}

function getChannelConflict(channel: ChannelData): DominantPattern | null {
  const gates = channel.gates?.toLowerCase() || '';
  const centers = channel.centers || [];
  
  const channelPatterns: { [key: string]: ChannelPunch } = {
    '35-36': {
      punchLine: "You grow by living it, not thinking it.",
      tension: "Hunger for experience pushes you in before you're ready.",
      blindSpot: "You confuse intensity with meaning.",
      edge: "When you trust the journey without rushing, your wisdom becomes transformative.",
      behavioral: "Seeking experiences. Feeling restless until something stirs you.",
      conflictStrength: 7
    },
    '12-22': {
      punchLine: "Your voice has unusual impact—when the timing is right.",
      tension: "Express too early, it misses. Hold back too long, the moment's gone.",
      blindSpot: "You think silence is the problem. Often, timing is.",
      edge: "When mood and moment align, you move people without trying.",
      behavioral: "Going silent when timing's off, then expressing powerfully when it lands.",
      conflictStrength: 8
    },
    '21-45': {
      punchLine: "You're built to direct resources. Whether asked or not.",
      tension: "Control from willpower burns out. Control from desire sustains.",
      blindSpot: "You take charge because you can—not because you want to.",
      edge: "When your will matches what matters, your authority becomes effortless.",
      behavioral: "Naturally taking charge of material situations.",
      conflictStrength: 7
    },
    '37-40': {
      punchLine: "You feel responsible for your people. The bargain is real.",
      tension: "When you give and don't receive, resentment builds. Keeping score kills warmth.",
      blindSpot: "You track what others owe. They don't know there's a tab.",
      edge: "Trust the flow without managing it. Community bonds sustain.",
      behavioral: "Forming deep bonds with unspoken expectations.",
      conflictStrength: 7
    },
    '6-59': {
      punchLine: "Your intimacy breaks through barriers—or pushes people away.",
      tension: "Not every barrier is meant to be broken.",
      blindSpot: "You think depth is always welcome. It isn't.",
      edge: "Be selective. Your capacity for connection transforms the ones who can receive it.",
      behavioral: "Creating deep emotional connection quickly. Sometimes too quickly.",
      conflictStrength: 7
    },
    '63-4': {
      punchLine: "You spot what doesn't make sense. Others miss it.",
      tension: "Doubt without resolution creates anxiety. Not every flaw needs fixing.",
      blindSpot: "You question everything—including what's actually working.",
      edge: "Trust your skepticism while staying open to mystery.",
      behavioral: "Questioning what seems accepted. Looking for the flaw.",
      conflictStrength: 6
    },
    '57-34': {
      punchLine: "Your instincts and your power align. When you trust them.",
      tension: "Thinking talks you out of what your body already knew.",
      blindSpot: "You wait for certainty that already came and went.",
      edge: "Act on the first knowing. Your response has power others can't manufacture.",
      behavioral: "Sensing what's right and having energy to act immediately.",
      conflictStrength: 8
    },
    '43-23': {
      punchLine: "You know things without knowing how. Most people won't understand.",
      tension: "Expressing to wrong ears leads to rejection. Holding back leads to frustration.",
      blindSpot: "You think you're being clear. Your knowing sounds strange to others.",
      edge: "Find ears that can hear. Your insight shifts how people see.",
      behavioral: "Carrying unique knowing that feels obvious to you, strange to others.",
      conflictStrength: 7
    },
    '61-24': {
      punchLine: "Ideas arrive unbidden. Understanding comes later—or doesn't.",
      tension: "Forcing insight before it's ready distorts it. Sharing too early confuses.",
      blindSpot: "You try to explain what needs to mature.",
      edge: "Let inspirations ripen. What emerges becomes accessible.",
      behavioral: "Receiving mental downloads that need time to process.",
      conflictStrength: 6
    },
    '28-38': {
      punchLine: "You fight for meaning. Even when others gave up.",
      tension: "Not every battle is worth fighting. Stubbornness without discernment exhausts.",
      blindSpot: "You think all struggles matter equally. They don't.",
      edge: "Direct your fight toward what genuinely calls you. Your tenacity creates change.",
      behavioral: "Engaging battles over principle. Struggling for what matters.",
      conflictStrength: 7
    }
  };
  
  // Try to match channel
  let channelKey: string | null = null;
  
  if (gates.includes('35') && gates.includes('36')) channelKey = '35-36';
  else if (gates.includes('12') && gates.includes('22')) channelKey = '12-22';
  else if (gates.includes('21') && gates.includes('45')) channelKey = '21-45';
  else if (gates.includes('37') && gates.includes('40')) channelKey = '37-40';
  else if (gates.includes('6') && gates.includes('59')) channelKey = '6-59';
  else if (gates.includes('63') && gates.includes('4')) channelKey = '63-4';
  else if (gates.includes('57') && gates.includes('34')) channelKey = '57-34';
  else if (gates.includes('43') && gates.includes('23')) channelKey = '43-23';
  else if (gates.includes('61') && gates.includes('24')) channelKey = '61-24';
  else if (gates.includes('28') && gates.includes('38')) channelKey = '28-38';
  // Center-based fallback
  else if (centers.includes('Throat') && centers.includes('Solar Plexus')) channelKey = '12-22';
  else if (centers.includes('Solar Plexus') && centers.includes('Sacral')) channelKey = '6-59';
  
  if (!channelKey || !channelPatterns[channelKey]) return null;
  
  const pattern = channelPatterns[channelKey];
  return {
    id: `channel_${channelKey}`,
    punchLine: pattern.punchLine,
    tension: pattern.tension,
    blindSpot: pattern.blindSpot,
    edge: pattern.edge,
    conflictStrength: pattern.conflictStrength,
    behavioralFrequency: 7
  };
}

// ============================================
// INCARNATION CROSS PUNCH PATTERNS
// ============================================

function getCrossPunch(crossName: string): { punch: string; tension: string } | null {
  const name = crossName.toLowerCase();
  
  const crosses: { [key: string]: { punch: string; tension: string } } = {
    'migration': {
      punch: "You move things—people, systems, situations—from one state to another.",
      tension: "Not everything stable needs disrupting."
    },
    'service': {
      punch: "You're here to be genuinely useful. Not helpful—useful.",
      tension: "Service without discernment depletes."
    },
    'planning': {
      punch: "You build structures that last. Organization comes naturally.",
      tension: "Planning without responsiveness becomes control."
    },
    'explanation': {
      punch: "You translate complexity. Make the confusing accessible.",
      tension: "Explaining what wasn't asked for feels like lecturing."
    },
    'consciousness': {
      punch: "You wake people up. Bring attention to what's been overlooked.",
      tension: "Forcing awareness creates resistance."
    },
    'eden': {
      punch: "You remind people of innocence. Original wholeness beneath the damage.",
      tension: "Insisting on innocence when survival requires toughness misses context."
    },
    'vessel of love': {
      punch: "You carry love as felt experience. Warmth others can receive.",
      tension: "Love performed isn't love."
    },
    'tension': {
      punch: "You hold creative discomfort. Let something emerge from pressure.",
      tension: "Forcing resolution kills what's trying to be born."
    },
    'the unexpected': {
      punch: "You break patterns. Introduce what no one saw coming.",
      tension: "Shock for its own sake repels."
    },
    'rulership': {
      punch: "You demonstrate leadership. Guide, direct, take responsibility.",
      tension: "Leadership without invitation becomes control."
    },
    'penetration': {
      punch: "You go deep. Depth over breadth. Intimacy over acquaintance.",
      tension: "Not everyone wants or is ready for that depth."
    }
  };
  
  for (const key of Object.keys(crosses)) {
    if (name.includes(key)) return crosses[key];
  }
  
  return null;
}

// ============================================
// BEHAVIORAL BULLETS GENERATOR
// Max 3-4, specific, different from each other
// Now enhanced with PROGRAMMING PARTNER polarity swings
// ============================================

function generateBehavioralBullets(
  dominantPatterns: DominantPattern[],
  input: HDSynthesisInput,
  polarities: RankedPolarity[] = []
): string[] {
  const bullets: string[] = [];
  const { type, authority, profile, definition, channels, consciousGates, unconsciousGates, undefinedCenters } = input;
  
  // Type × Authority specific behaviors
  if (type === 'Manifestor' && authority === 'Emotional') {
    bullets.push("You decide, then question it when the wave passes");
    bullets.push("People expect certainty before you feel it");
  } else if (type === 'Manifestor') {
    bullets.push("You act, then watch others catch up");
  } else if (type === 'Generator' && authority === 'Emotional') {
    bullets.push("You say yes in excitement, then feel stuck when it settles");
  } else if (type === 'Generator') {
    bullets.push("Your body knows before your mind catches up");
  } else if (type === 'Manifesting Generator') {
    bullets.push("You start fast, discover if it's right later");
    bullets.push("What looks like quitting is your body finding the real path");
  } else if (type === 'Projector') {
    bullets.push("You see what others miss—and feel unseen when no one asks");
  } else if (type === 'Reflector') {
    bullets.push("You feel different depending on who you're with");
  }
  
  // ADD POLARITY BEHAVIORAL SWING (high priority)
  if (polarities.length > 0 && bullets.length < 3) {
    const polarityBullet = getPolarityBehavioralBullet(polarities);
    if (polarityBullet && !bullets.some(b => b.toLowerCase().includes(polarityBullet.toLowerCase().split(' ')[0]))) {
      bullets.push(polarityBullet);
    }
  }
  
  // ADD POLARITY RELATIONSHIP PATTERN (from second polarity if available)
  if (polarities.length > 1 && bullets.length < 4) {
    const relationshipBullet = getPolarityRelationshipBullet(polarities);
    if (relationshipBullet && !bullets.some(b => b.toLowerCase().includes(relationshipBullet.toLowerCase().split(' ')[0]))) {
      bullets.push(relationshipBullet);
    }
  }
  
  // Conscious/Unconscious (if we have the data and room)
  if (consciousGates && unconsciousGates && consciousGates.length > 0 && unconsciousGates.length > 0 && bullets.length < 4) {
    bullets.push("Your mind explains decisions your body already made");
  }
  
  // Profile first line behavior
  const firstLine = profile?.split('/')[0];
  if (firstLine === '5' && bullets.length < 4 && !bullets.some(b => b.includes('expect') && b.includes('answer'))) {
    bullets.push("People expect answers before you've offered any");
  } else if (firstLine === '1' && bullets.length < 4) {
    bullets.push("You research longer than others think necessary");
  } else if (firstLine === '3' && bullets.length < 4) {
    bullets.push("You learn more from what went wrong than what went right");
  }
  
  // Split definition
  if (definition === 'Split' && bullets.length < 4) {
    bullets.push("You feel more complete around certain people—that's design, not dependency");
  }
  
  // Limit to 4 max, remove duplicates
  const uniqueBullets = [...new Set(bullets)];
  return uniqueBullets.slice(0, 4);
}

// ============================================
// SUPPORT CONDITIONS GENERATOR
// Max 2-3, HIGH IMPACT only
// ============================================

function generateSupports(input: HDSynthesisInput): string[] {
  const supports: string[] = [];
  const { type, authority, definition, undefinedCenters } = input;
  
  // Authority-based (highest impact)
  if (authority === 'Emotional') {
    supports.push("Time between impulse and commitment");
    supports.push("People who don't rush your clarity");
  } else if (authority === 'Sacral') {
    supports.push("Yes/no questions that let your gut respond");
  } else if (authority === 'Splenic') {
    supports.push("Trust in the first knowing, without needing reasons");
  } else if (authority === 'Ego') {
    supports.push("Freedom to follow desire without guilt");
  } else if (authority === 'Lunar') {
    supports.push("A full 28-day cycle before major decisions");
  } else if (authority === 'Self-Projected') {
    supports.push("Sounding boards who listen without directing");
  }
  
  // Type-based (only if room)
  if (type === 'Manifestor' && supports.length < 3) {
    supports.push("Relationships that don't require constant explanation");
  } else if (type === 'Projector' && supports.length < 3) {
    supports.push("Invitations before contribution");
  } else if (type === 'Reflector' && supports.length < 3) {
    supports.push("Genuinely healthy environments—you become what you're around");
  }
  
  // Undefined center (only highest impact)
  if (undefinedCenters && supports.length < 3) {
    if (undefinedCenters.some(c => c.toLowerCase().includes('root'))) {
      supports.push("Release from artificial urgency");
    }
  }
  
  // Split definition
  if (definition === 'Split' && supports.length < 3) {
    supports.push("People who bridge your gaps without you trying");
  }
  
  return supports.slice(0, 3);
}

// ============================================
// MASTER SYNTHESIS GENERATOR
// Compressed + Punchy version
// Now enhanced with PROGRAMMING PARTNERS
// ============================================

export function generateHDSynthesis(input: HDSynthesisInput): HDSynthesis | null {
  const { 
    type, 
    authority, 
    profile, 
    incarnationCross,
    channels,
    personalitySun,
    personalityEarth,
    designSun,
    designEarth,
    consciousGates,
    unconsciousGates,
  } = input;
  
  if (!type || !authority) {
    return null;
  }
  
  // ============================================
  // STEP 0: GET DOMINANT POLARITIES (Programming Partners)
  // ============================================
  const polarityInput: PolarityInput = {
    personalitySun,
    personalityEarth,
    designSun,
    designEarth,
    consciousGates,
    unconsciousGates,
    channels,
  };
  const dominantPolarities = getDominantPolarities(polarityInput, 2);
  
  // ============================================
  // STEP 1: RANK DOMINANT PATTERNS
  // ============================================
  const dominantPatterns = rankDominantPatterns(input);
  const primary = dominantPatterns[0];
  const secondary = dominantPatterns[1];
  
  if (!primary) return null;
  
  // ============================================
  // STEP 2: BUILD CORE PATTERN (1 dominant + 1 support max)
  // ============================================
  let corePattern = primary.punchLine;
  
  // Add cross punch if it's powerful enough
  if (incarnationCross) {
    const crossPunch = getCrossPunch(incarnationCross);
    if (crossPunch) {
      corePattern += ` ${crossPunch.punch}`;
    }
  }
  // OR add channel punch if secondary
  else if (secondary?.id?.startsWith('channel')) {
    corePattern += ` ${secondary.punchLine}`;
  }
  
  // ============================================
  // STEP 3: BUILD CORE TENSION (now enhanced with polarity)
  // ============================================
  let coreTension = primary.tension;
  
  // ADD PROGRAMMING PARTNER TENSION if available
  if (dominantPolarities.length > 0) {
    coreTension = enhanceTensionWithPolarity(coreTension, dominantPolarities);
  }
  // Otherwise add secondary tension if different enough
  else if (secondary && !secondary.id?.startsWith('channel') && secondary.tension !== primary.tension) {
    const secondaryTension = secondary.tension;
    if (secondaryTension.length < 60) {
      coreTension += ` ${secondaryTension}`;
    }
  }
  
  // ============================================
  // STEP 4: BUILD HOW THIS PLAYS OUT (3-4 max, now with polarity)
  // ============================================
  const howThisPlaysOut = generateBehavioralBullets(dominantPatterns, input, dominantPolarities);
  
  // ============================================
  // STEP 5: BUILD BLIND SPOT (now enhanced with polarity)
  // ============================================
  let blindSpot = primary.blindSpot;
  
  // ADD PROGRAMMING PARTNER BLIND SPOT
  if (dominantPolarities.length > 0) {
    blindSpot = enhanceBlindSpotWithPolarity(blindSpot, dominantPolarities);
  }
  // Otherwise add profile unconscious if different
  else if (secondary?.id === 'profile' && secondary.blindSpot !== primary.blindSpot) {
    blindSpot += ` ${secondary.blindSpot}`;
  }
  
  // ============================================
  // STEP 6: BUILD EDGE (now enhanced with polarity integration)
  // ============================================
  let edge = primary.edge;
  
  // ADD PROGRAMMING PARTNER INTEGRATION
  if (dominantPolarities.length > 0) {
    edge = enhanceEdgeWithPolarity(edge, dominantPolarities);
  }
  // Otherwise add channel edge if relevant
  else if (channels && channels.length > 0) {
    const channelPattern = getChannelConflict(channels[0]);
    if (channelPattern && channelPattern.edge !== primary.edge) {
      if (channelPattern.edge.length < 80) {
        edge += ` ${channelPattern.edge}`;
      }
    }
  }
  
  // ============================================
  // STEP 7: BUILD WHAT SUPPORTS YOU (2-3 max)
  // ============================================
  const whatSupportsYou = generateSupports(input);
  
  return {
    corePattern,
    coreTension,
    howThisPlaysOut,
    blindSpot,
    edge,
    whatSupportsYou
  };
}

// ============================================
// UTILITY
// ============================================

export function canGenerateSynthesis(type: string, authority: string): boolean {
  return !!(type && authority);
}
