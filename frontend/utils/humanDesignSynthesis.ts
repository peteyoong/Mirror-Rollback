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
// Now with FLOW (cause → effect → consequence)
// and LOOP patterns (A → B → C → repeat)
// ============================================

interface TypeAuthPunch {
  punchLine: string;
  tension: string;
  blindSpot: string;
  edge: string;
  // NEW: Flow and Loop patterns
  flow: string;           // cause → effect → consequence
  loop: string;           // repeating pattern
  correctedFlow: string;  // what breaks the loop
  conflictStrength: number;
}

function getTypeAuthorityConflict(type: string, authority: string): TypeAuthPunch | null {
  const key = `${type}_${authority}`;
  
  const patterns: { [key: string]: TypeAuthPunch } = {
    // MANIFESTOR
    'Manifestor_Emotional': {
      punchLine: "You move before you're clear—and deal with it after.",
      tension: "The urge hits and you act. But the wave hasn't settled. By the time it does, you're already committed to something that might not be true.",
      blindSpot: "You think they're resisting you. But you pushed before the wave passed, so they pushed back. The harder you force, the more they shut down.",
      edge: "When you feel the urge, pause. Let the wave settle. Inform before you move. Then act—and watch how cleanly it lands.",
      flow: "You act first. By the time you explain, they've already reacted.",
      loop: "Move fast → meet resistance → withdraw without explaining → feel misunderstood. Repeat.",
      correctedFlow: "Feel the pull, pause, let clarity come. Then inform, then move.",
      conflictStrength: 9
    },
    'Manifestor_Splenic': {
      punchLine: "You know instantly—but explain it never.",
      tension: "The knowing comes once, quiet and fast. If you hesitate, it fades. Then you're left trying to reason your way to an answer that already came and went.",
      blindSpot: "You wait for logic to confirm what your instincts already knew. By then, the moment has passed—and so has the clarity.",
      edge: "Trust the first hit. Move before thinking talks you out of it. Understanding comes later, or it doesn't—but the knowing was real.",
      flow: "You sense it. You doubt it. You wait. The window closes.",
      loop: "Know instantly → look for reasons → miss the moment. Repeat.",
      correctedFlow: "Sense the knowing, trust it, act. Let reasons catch up later.",
      conflictStrength: 7
    },
    'Manifestor_Ego': {
      punchLine: "When your heart's in it, you're unstoppable. When it's not, nothing moves.",
      tension: "You commit because you think you should want it. But desire fades when it wasn't real. And you can't force what your heart never agreed to.",
      blindSpot: "You promise things your heart didn't choose. When you can't deliver, you blame discipline. But it was never about discipline—it was about desire.",
      edge: "Check your want first. If it's real, commit. If it's not, don't. When desire is genuine, follow-through takes care of itself.",
      flow: "You say yes. The excitement fades. You push through. Resentment builds.",
      loop: "Commit without desire → run dry → break promise → feel guilty → overcommit to prove yourself. Repeat.",
      correctedFlow: "Feel the want, verify it's real, then commit. Energy stays.",
      conflictStrength: 8
    },
    'Manifestor_Self-Projected': {
      punchLine: "You don't know until you hear yourself say it.",
      tension: "You wait for internal certainty. But for you, certainty comes through voice, not thought. Silence keeps you stuck in loops that speaking would break.",
      blindSpot: "You hold back waiting to be sure. But speaking is how you'd find out. Your clarity lives in your voice, not before it.",
      edge: "Start talking. Even if you're not sure. The direction emerges as you speak. That's how you're designed to know.",
      flow: "You think in silence. Nothing resolves. You stay frozen.",
      loop: "Wait to be sure → stay silent → feel unclear → wait longer. Repeat.",
      correctedFlow: "Feel uncertain, speak anyway, hear yourself, know.",
      conflictStrength: 6
    },
    'Manifestor_None': {
      punchLine: "Your clarity lives in place, not in your head.",
      tension: "You look inside for answers that aren't there. You force a choice. It doesn't hold. Because your wisdom is place-dependent—and you keep trying to find it alone.",
      blindSpot: "You think the answer is inside you somewhere. It's not. Your clarity emerges from environment, not introspection.",
      edge: "Change the setting. Move to a different space. Watch how the right direction becomes obvious when you stop trying to figure it out internally.",
      flow: "You sit with it. Nothing clears. You move somewhere else. Suddenly you know.",
      loop: "Try to decide alone → get nowhere → force a choice → regret. Repeat.",
      correctedFlow: "Feel stuck, change environment, let the setting reveal.",
      conflictStrength: 5
    },
    
    // GENERATOR
    'Generator_Emotional': {
      punchLine: "Your gut says yes. Your wave says wait.",
      tension: "Response comes instantly—but it's not the whole truth. The wave takes time. You're caught between the pull of now and the clarity that only unfolds later.",
      blindSpot: "You say yes in the high. The wave drops. Now you're stuck with something that no longer feels right—but you already committed.",
      edge: "Let your gut respond. Then wait. Ride the wave. What's still lit when the emotional weather clears—that's what's real.",
      flow: "You feel the pull. You say yes. Time passes. The feeling changes. But you already committed.",
      loop: "Respond in excitement → commit fast → wave passes → feel trapped → blame your choices. Repeat.",
      correctedFlow: "Feel the response, acknowledge it, wait for clarity, then commit.",
      conflictStrength: 9
    },
    'Generator_Sacral': {
      punchLine: "Your body knows. Your mind catches up later.",
      tension: "The pull happens before reasons. You've learned to override it with logic. Every override leads somewhere your body didn't want to go.",
      blindSpot: "Your gut said no. You talked yourself into yes. Now you wonder why you're drained. The body knew—you just didn't listen.",
      edge: "Trust the pull. Even without reasons. Especially without reasons. That's how your energy stays clean and your satisfaction stays real.",
      flow: "You sense yes or no. You question it. You override. You regret.",
      loop: "Body responds → mind doubts → override → frustration. Repeat.",
      correctedFlow: "Body responds, you honor it, reasons come later or don't.",
      conflictStrength: 7
    },
    
    // MANIFESTING GENERATOR
    'Manifesting Generator_Emotional': {
      punchLine: "You move fast. Your clarity doesn't.",
      tension: "You're already three steps ahead—but the wave hasn't settled. Excitement feels like truth, but it's just a peak. The real answer takes time you rarely give it.",
      blindSpot: "You start things in highs. The wave passes. Now you're scattered across commitments that no longer feel right—calling it 'multi-passionate' instead of 'moved too fast.'",
      edge: "Sample quickly, commit slowly. Let the wave complete. What survives emotional weather is actually yours.",
      flow: "You get excited. You start. The feeling shifts. You're stuck or pivoting blind.",
      loop: "Start fast → wave shifts → force through or scatter → exhaust → wonder why nothing sticks. Repeat.",
      correctedFlow: "Feel the pull, try it, wait for emotional clarity, then commit or release.",
      conflictStrength: 9
    },
    'Manifesting Generator_Sacral': {
      punchLine: "You pivot faster than others understand.",
      tension: "They call it inconsistent. You call it following what's alive. The guilt comes when you think completion means finishing—not extracting what was yours to take.",
      blindSpot: "You stay too long because you think you should finish. But the energy died. Forcing yourself through dead tracks is the real inconsistency.",
      edge: "Trust the pivot. Completion isn't about the end—it's about taking what's yours and moving when the energy does.",
      flow: "You respond. You start. Energy shifts. You're stuck between guilt and pivot.",
      loop: "Start with energy → energy dies → force through → resent it → guilt over next pivot. Repeat.",
      correctedFlow: "Respond, engage, energy shifts, pivot without guilt, find the real path.",
      conflictStrength: 7
    },
    
    // PROJECTOR
    'Projector_Emotional': {
      punchLine: "You see deeply—but you don't know what to do with it until later.",
      tension: "Insight comes, but the wave hasn't settled. You share in a peak. The wave drops. Now you'd say it differently—but they already heard the first version.",
      blindSpot: "You guide in emotional highs. When the wave passes, your advice looks different. They're confused because you were still finding your own clarity.",
      edge: "See it. Hold it. Let the wave settle. When you share from emotional clarity, your insight doesn't just land—it transforms.",
      flow: "You see the answer. You share immediately. The wave shifts. Your guidance contradicts itself.",
      loop: "See clearly → share in a high → wave shifts → wish you'd waited → feel misunderstood. Repeat.",
      correctedFlow: "See the insight, hold it, let the wave settle, then offer.",
      conflictStrength: 8
    },
    'Projector_Splenic': {
      punchLine: "You see the answer before anyone asks.",
      tension: "Insight comes instantly—but recognition takes time. You know, but no one's asking. If you wait too long, the knowing fades. It won't come back the same way.",
      blindSpot: "You hold back the knowing, waiting to be asked. But intuition doesn't repeat. By the time they're ready, the clarity you had is gone.",
      edge: "When recognition meets intuition, don't hesitate. Speak while the knowing is alive. That's when you cut through everything.",
      flow: "You know. You wait for invitation. The knowing fades. You're left with memory, not clarity.",
      loop: "See instantly → wait to be asked → moment passes → insight fades → feel unrecognized. Repeat.",
      correctedFlow: "Sense the knowing, find recognition, speak while it's alive.",
      conflictStrength: 7
    },
    'Projector_Self-Projected': {
      punchLine: "You understand others by hearing yourself describe them.",
      tension: "You hold the insight, waiting to be sure. But for you, speaking is knowing. Silence keeps you uncertain about things your voice would clarify instantly.",
      blindSpot: "You stay quiet because you're not sure you're right. But speaking is how you'd find out. Your clarity lives in expression, not before it.",
      edge: "When you're invited, speak. Truth emerges for everyone—including you. That's how your insight becomes real.",
      flow: "You sense something. You hold it. You wait. It never crystallizes internally.",
      loop: "Have insight → wait to be sure → stay silent → feel unclear → wait longer. Repeat.",
      correctedFlow: "Feel the insight, get invited, speak, hear yourself, now you know.",
      conflictStrength: 6
    },
    'Projector_Ego': {
      punchLine: "When your heart's in the invitation, your impact is undeniable.",
      tension: "You accept because you feel you should. But desire wasn't there. The more you give without wanting to, the more bitterness builds.",
      blindSpot: "You guide people your heart never chose. You call it service. But underneath, resentment is growing—because you're giving to the wrong invitations.",
      edge: "Only accept what genuinely excites you. When your heart is in the invitation, your guidance has staying power and your energy sustains.",
      flow: "You're invited. You accept out of should. You give without heart. They sense it.",
      loop: "Accept without desire → run dry → feel bitter → accept the next hoping it's different. Repeat.",
      correctedFlow: "Get invited, check your heart, accept only what's real, energy sustains.",
      conflictStrength: 7
    },
    'Projector_Mental': {
      punchLine: "Your clarity depends on who you're talking to and where.",
      tension: "You try to know alone. Nothing clears. Because your wisdom needs the right setting and the right conversation—it doesn't emerge in isolation.",
      blindSpot: "You force answers in wrong environments, then wonder why your guidance misses. Your clarity is context-dependent. Some settings cloud, others clarify.",
      edge: "Find the right environment, the right people. Discuss before deciding. Watch how your insight becomes unusually precise.",
      flow: "You think alone. It stays murky. You share anyway. It falls flat.",
      loop: "Try to figure it out → stay isolated → offer unclear guidance → feel ineffective → try harder to think. Repeat.",
      correctedFlow: "Feel uncertain, find right people and place, discuss, clarity emerges.",
      conflictStrength: 5
    },
    'Projector_None': {
      punchLine: "You see into others deeply. Your own clarity shifts with place.",
      tension: "You look inside for stability that isn't there. Your wisdom genuinely shifts—that's design, not instability. Trying to be consistent fights how you work.",
      blindSpot: "You want a fixed sense of self. But you're meant to shift with environment. Fighting that creates more confusion, not less.",
      edge: "Accept that your clarity moves. Choose environments consciously. Let place guide what emerges. That's where your precision lives.",
      flow: "You seek inner certainty. It moves. You doubt yourself. You try harder to be stable.",
      loop: "Look for fixed self-knowledge → find shifting clarity → feel unreliable → try to be more consistent. Repeat.",
      correctedFlow: "Accept you shift, choose environments wisely, offer what emerges.",
      conflictStrength: 5
    },
    
    // REFLECTOR
    'Reflector_Lunar': {
      punchLine: "You take in everything. You need time to know what's yours.",
      tension: "You feel something strongly and act on it. The cycle continues. What felt true on Monday looks different by Friday. That's not inconsistency—it's incomplete information.",
      blindSpot: "You decide from one day's reflection and call it clarity. But you need the full cycle. Fast decisions rarely survive the moon's complete rotation.",
      edge: "Give yourself 28 days. Let the full cycle show you what remains true regardless of who you've been around. That's wisdom faster types can't access.",
      flow: "You sense something strongly. You decide. Time passes. It no longer feels true.",
      loop: "Feel certain → decide quickly → moon shifts → regret → try to decide faster next time. Repeat.",
      correctedFlow: "Feel it, note it, let 28 days pass, see what remains, then choose.",
      conflictStrength: 8
    }
  };
  
  return patterns[key] || patterns[`${type}_Emotional`] || generateFallbackPunch(type, authority);
}

function generateFallbackPunch(type: string, authority: string): TypeAuthPunch {
  const typePatterns: { [key: string]: TypeAuthPunch } = {
    'Generator': {
      punchLine: "Your body knows what lights you up. Your mind gets in the way.",
      tension: "Response comes first. Then mind intervenes. You override the pull. Frustration builds—because you went against what you already knew.",
      blindSpot: "You talked yourself into yes when your body said no. Now you're drained. The body knew. You just didn't listen.",
      edge: "Trust the pull. Even without reasons. Especially without reasons. That's how satisfaction becomes real.",
      flow: "You sense the pull. You question it. You override. You regret.",
      loop: "Body responds → mind doubts → override → frustration. Repeat.",
      correctedFlow: "Feel the pull, honor it, reasons come later or don't.",
      conflictStrength: 7
    },
    'Manifesting Generator': {
      punchLine: "You move in multiple directions. That's not scattered—it's how you work.",
      tension: "You start with energy. Energy shifts. You want to pivot but guilt holds you. Forcing through dead tracks is the real waste.",
      blindSpot: "You think you should finish. But the energy died. Staying out of obligation isn't completion—it's self-betrayal.",
      edge: "Follow the strongest pull. Pivot when it's done. Completion is extracting what's yours, not enduring what isn't.",
      flow: "You respond. You start. Energy shifts. You're stuck between guilt and pivot.",
      loop: "Start with energy → energy dies → force through → resent. Repeat.",
      correctedFlow: "Respond, engage, energy shifts, pivot without guilt.",
      conflictStrength: 7
    },
    'Projector': {
      punchLine: "You see what others miss. Your insight transforms when invited.",
      tension: "You see it clearly. You share without being asked. It falls flat. Bitterness builds—because you gave something no one requested.",
      blindSpot: "You offer guidance because you can see the answer. But no one asked. And uninvited insight rarely lands, no matter how accurate.",
      edge: "Wait for recognition. When you're truly invited, your seeing becomes your most valuable gift.",
      flow: "You see clearly. You share. No one asked. It doesn't land.",
      loop: "See answer → share uninvited → rejected → bitter. Repeat.",
      correctedFlow: "See it, wait for invitation, share when asked, it transforms.",
      conflictStrength: 7
    },
    'Manifestor': {
      punchLine: "You initiate what doesn't exist yet. The work is informing first.",
      tension: "You act. No one knew it was coming. They resist. You resent the resistance—but they just weren't prepared.",
      blindSpot: "You moved without informing. They pushed back. You blame their resistance. But the issue was the surprise, not their response.",
      edge: "Inform before you move. Let them know what's coming. Watch how the resistance dissolves.",
      flow: "You feel the urge. You act. People are unprepared. They push back.",
      loop: "Move without warning → meet resistance → resent them. Repeat.",
      correctedFlow: "Feel the urge, inform, give a moment, then move.",
      conflictStrength: 7
    },
    'Reflector': {
      punchLine: "You feel completely different depending on who you're with. That's design, not instability.",
      tension: "You feel something strongly. You act on it. The cycle continues. What felt true shifts. That's not inconsistency—that's incomplete information.",
      blindSpot: "You try to hold a fixed identity. But you're meant to reflect and shift. Fighting that creates more confusion, not stability.",
      edge: "Choose your environments carefully. You become what you're around. That's not weakness—it's how you access wisdom.",
      flow: "You feel certain. You act. Time passes. Truth shifts.",
      loop: "Feel strongly → decide fast → moon moves → regret. Repeat.",
      correctedFlow: "Feel it, note it, let the cycle complete, see what remains.",
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
// BEHAVIORAL BULLETS GENERATOR WITH LOOP PATTERN
// Max 3-4, specific, different from each other
// Now includes at least ONE loop pattern
// ============================================

function generateBehavioralBulletsWithLoop(
  dominantPatterns: DominantPattern[],
  input: HDSynthesisInput,
  polarities: RankedPolarity[] = [],
  loopPattern?: string
): string[] {
  const bullets: string[] = [];
  const { type, authority, profile, definition, consciousGates, unconsciousGates } = input;
  
  // FIRST BULLET: The LOOP PATTERN (most important)
  if (loopPattern) {
    bullets.push(loopPattern);
  }
  
  // Type × Authority specific flow behaviors (natural language)
  if (type === 'Manifestor' && authority === 'Emotional' && bullets.length < 4) {
    if (!loopPattern) bullets.push("Move fast → meet resistance → withdraw → feel misunderstood. Repeat.");
    bullets.push("You decide. Wave shifts. You question. But you already committed.");
  } else if (type === 'Manifestor' && bullets.length < 4) {
    if (!loopPattern) bullets.push("Act → surprise them → they resist → you resent. Repeat.");
    bullets.push("You move. No one knew. They push back.");
  } else if (type === 'Generator' && authority === 'Emotional' && bullets.length < 4) {
    if (!loopPattern) bullets.push("Say yes in the high → wave drops → feel stuck. Repeat.");
    bullets.push("You commit fast. The wave passes. Now you're locked into something that changed.");
  } else if (type === 'Generator' && bullets.length < 4) {
    if (!loopPattern) bullets.push("Body responds → mind doubts → override → frustration. Repeat.");
    bullets.push("Gut said no. You talked yourself in. Energy drains.");
  } else if (type === 'Manifesting Generator' && bullets.length < 4) {
    if (!loopPattern) bullets.push("Start with energy → energy shifts → guilt keeps you. Repeat.");
    bullets.push("You pivot. They call it inconsistent. You start to doubt yourself.");
  } else if (type === 'Projector' && bullets.length < 4) {
    if (!loopPattern) bullets.push("See the answer → share uninvited → rejected. Repeat.");
    bullets.push("You see it clearly. No one asked. It doesn't land.");
  } else if (type === 'Reflector' && bullets.length < 4) {
    if (!loopPattern) bullets.push("Feel certain → decide → moon moves → regret. Repeat.");
    bullets.push("What felt true on Monday looks different by Friday. That's not inconsistency—that's incomplete data.");
  }
  
  // ADD POLARITY swing if room
  if (polarities.length > 0 && bullets.length < 4) {
    const polarityBullet = getPolarityBehavioralBullet(polarities);
    if (polarityBullet && !bullets.some(b => b.toLowerCase().includes(polarityBullet.toLowerCase().split(' ')[0]))) {
      bullets.push(polarityBullet);
    }
  }
  
  // Conscious/Unconscious flow (natural language)
  if (consciousGates && unconsciousGates && consciousGates.length > 0 && unconsciousGates.length > 0 && bullets.length < 4) {
    bullets.push("Your mind explains decisions your body already made. You realize this later.");
  }
  
  // Profile patterns (natural language)
  const firstLine = profile?.split('/')[0];
  if (firstLine === '5' && bullets.length < 4) {
    bullets.push("They expect answers from you before you've even offered anything.");
  }
  
  // Split definition (natural language)
  if (definition === 'Split' && bullets.length < 4) {
    bullets.push("Around certain people you feel whole. They leave and the incompleteness returns.");
  }
  
  // Limit to 4 max, remove duplicates
  const uniqueBullets = [...new Set(bullets)];
  return uniqueBullets.slice(0, 4);
}

// ============================================
// SUPPORTS GENERATOR WITH LOOP BREAKERS
// Focuses on what interrupts the pattern
// ============================================

function generateSupportsWithLoopBreakers(input: HDSynthesisInput): string[] {
  const supports: string[] = [];
  const { type, authority, definition, undefinedCenters } = input;
  
  // Authority-based loop breakers (highest impact)
  if (authority === 'Emotional') {
    supports.push("The pause between impulse and action—that's where the loop breaks");
    supports.push("People who don't rush you through the wave");
  } else if (authority === 'Sacral') {
    supports.push("Questions that let your body respond before your mind intervenes");
  } else if (authority === 'Splenic') {
    supports.push("Trust the first hit—waiting for reasons restarts the loop");
  } else if (authority === 'Ego') {
    supports.push("Only commit to what you actually want—forced desire starts the loop");
  } else if (authority === 'Lunar') {
    supports.push("A full cycle before deciding—shortcuts restart the pattern");
  } else if (authority === 'Self-Projected') {
    supports.push("Sounding boards—the loop breaks when you hear yourself");
  }
  
  // Type-based loop breakers
  if (type === 'Manifestor' && supports.length < 3) {
    supports.push("Informing before acting—resistance stops before it starts");
  } else if (type === 'Projector' && supports.length < 3) {
    supports.push("Waiting for invitation—uninvited sharing feeds the loop");
  } else if (type === 'Reflector' && supports.length < 3) {
    supports.push("Healthy environments—you become what you're around");
  }
  
  // Split definition
  if (definition === 'Split' && supports.length < 3) {
    supports.push("People who bridge your gaps—without them, incompleteness loops");
  }
  
  return supports.slice(0, 3);
}

// Keep the old function for compatibility
function generateBehavioralBullets(
  dominantPatterns: DominantPattern[],
  input: HDSynthesisInput,
  polarities: RankedPolarity[] = []
): string[] {
  return generateBehavioralBulletsWithLoop(dominantPatterns, input, polarities);
}

// Keep the old function for compatibility
function generateSupports(input: HDSynthesisInput): string[] {
  return generateSupportsWithLoopBreakers(input);
}

// ============================================
// MASTER SYNTHESIS GENERATOR
// Compressed + Punchy + FLOW/LOOP version
// Now patterns unfold and repeat
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
  
  // Get the full TypeAuthPunch with flow/loop patterns
  const typeAuthPattern = getTypeAuthorityConflict(type, authority);
  
  // ============================================
  // STEP 2: BUILD CORE PATTERN (punch + flow sequence)
  // ============================================
  let corePattern = primary.punchLine;
  
  // Add FLOW sequence (cause → effect → consequence)
  if (typeAuthPattern?.flow) {
    corePattern += ` ${typeAuthPattern.flow}`;
  }
  // Or add cross punch if powerful
  else if (incarnationCross) {
    const crossPunch = getCrossPunch(incarnationCross);
    if (crossPunch) {
      corePattern += ` ${crossPunch.punch}`;
    }
  }
  
  // ============================================
  // STEP 3: BUILD CORE TENSION (contradiction in motion)
  // ============================================
  // Use the flow-based tension from TypeAuthPunch
  let coreTension = typeAuthPattern?.tension || primary.tension;
  
  // ADD PROGRAMMING PARTNER TENSION if available
  if (dominantPolarities.length > 0) {
    coreTension = enhanceTensionWithPolarity(coreTension, dominantPolarities);
  }
  
  // ============================================
  // STEP 4: BUILD HOW THIS PLAYS OUT (with LOOP pattern)
  // ============================================
  const howThisPlaysOut = generateBehavioralBulletsWithLoop(
    dominantPatterns, 
    input, 
    dominantPolarities,
    typeAuthPattern?.loop
  );
  
  // ============================================
  // STEP 5: BUILD BLIND SPOT (flow/loop format)
  // ============================================
  // Use the loop-style blind spot from TypeAuthPunch
  let blindSpot = typeAuthPattern?.blindSpot || primary.blindSpot;
  
  // ADD PROGRAMMING PARTNER BLIND SPOT
  if (dominantPolarities.length > 0) {
    blindSpot = enhanceBlindSpotWithPolarity(blindSpot, dominantPolarities);
  }
  
  // ============================================
  // STEP 6: BUILD EDGE (corrected flow)
  // ============================================
  // Use corrected flow from TypeAuthPunch
  let edge = typeAuthPattern?.correctedFlow || typeAuthPattern?.edge || primary.edge;
  
  // ADD PROGRAMMING PARTNER INTEGRATION
  if (dominantPolarities.length > 0) {
    edge = enhanceEdgeWithPolarity(edge, dominantPolarities);
  }
  
  // ============================================
  // STEP 7: BUILD WHAT SUPPORTS YOU (loop breakers)
  // ============================================
  const whatSupportsYou = generateSupportsWithLoopBreakers(input);
  
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
