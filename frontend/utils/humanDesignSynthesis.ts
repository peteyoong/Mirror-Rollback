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

// ============================================
// PATTERN THREAD - THE UNIFIED NARRATIVE
// ============================================
// Combines Type + Authority + Top Gate into ONE dominant pattern
// that runs through everything. Max 4-5 lines.
// Mirror tone: observational, emotionally recognizable.

export interface PatternThread {
  title: string;
  body: string;
  coreLoop: string;
}

export function generatePatternThread(input: HDSynthesisInput): PatternThread | null {
  const { type, authority, personalitySun, designSun, channels } = input;
  
  if (!type || !authority) return null;
  
  // Get the top gate - Personality Sun takes priority
  const topGate = typeof personalitySun === 'object' 
    ? personalitySun.gate 
    : (typeof personalitySun === 'number' ? personalitySun : null);
  
  const secondGate = typeof designSun === 'object'
    ? designSun.gate
    : (typeof designSun === 'number' ? designSun : null);
  
  // Build the core pattern narrative from Type + Authority combination
  const patterns = getPatternThreadTemplates(type, authority);
  if (!patterns) return null;
  
  // Select variant based on top gate (or use default)
  const gateInfluence = getGateInfluenceForThread(topGate, secondGate);
  
  // Build the body with gate-specific nuance if available
  let body = patterns.body;
  if (gateInfluence && patterns.gateVariant) {
    body = patterns.gateVariant(gateInfluence);
  }
  
  return {
    title: "The Pattern Running Through You",
    body: body,
    coreLoop: patterns.coreLoop
  };
}

interface ThreadTemplate {
  body: string;
  coreLoop: string;
  gateVariant?: (influence: string) => string;
}

function getPatternThreadTemplates(type: string, authority: string): ThreadTemplate | null {
  const key = `${type}_${authority}`;
  
  const templates: { [key: string]: ThreadTemplate } = {
    // MANIFESTOR combinations
    'Manifestor_Emotional': {
      body: `You're wired to act on what you see. But your clarity doesn't come instantly.\n\nSo you move before you're fully sure—then feel the consequences after.\n\nThis creates a pattern: you initiate, things shift, and you're left processing what actually happened.`,
      coreLoop: "You act, then feel, then question.",
      gateVariant: (influence) => `You're wired to act on what you see. But your clarity doesn't come instantly.\n\nSo you move before you're fully sure${influence}—then feel the consequences after.\n\nThis creates a pattern: you initiate, things shift, and you're left processing what actually happened.`
    },
    'Manifestor_Splenic': {
      body: `You know things instantly—before reasons arrive. But that knowing comes once, quietly, and doesn't wait.\n\nWhen you hesitate to trust it, the moment passes. Then you're left trying to logic your way to something that already came and went.`,
      coreLoop: "You sense it, you doubt it, the window closes.",
      gateVariant: (influence) => `You know things instantly${influence}—before reasons arrive. But that knowing comes once, quietly, and doesn't wait.\n\nWhen you hesitate to trust it, the moment passes. Then you're left trying to logic your way to something that already came and went.`
    },
    'Manifestor_Ego': {
      body: `When your heart is genuinely in something, you're unstoppable. When it's not, nothing moves.\n\nThe pattern: you commit because you think you should want it. The energy drains. You blame discipline. But it was never about discipline—it was about desire.`,
      coreLoop: "You promise, desire fades, you push through dry.",
      gateVariant: (influence) => `When your heart is genuinely in something${influence}, you're unstoppable. When it's not, nothing moves.\n\nThe pattern: you commit because you think you should want it. The energy drains. You blame discipline. But it was never about discipline—it was about desire.`
    },
    'Manifestor_Self-Projected': {
      body: `You don't know until you hear yourself say it. Waiting for internal certainty keeps you frozen.\n\nThe pattern: you stay silent, hoping clarity will come. But your truth lives in your voice—not before it.`,
      coreLoop: "You wait, you stay silent, you stay stuck.",
    },
    'Manifestor_None': {
      body: `Your clarity doesn't live inside you—it comes from where you are.\n\nThe pattern: you try to figure things out alone. Nothing resolves. You force a choice. It doesn't hold. Because your wisdom is place-dependent, and you keep looking in the wrong spot.`,
      coreLoop: "You look inside, nothing's there, you force it anyway.",
    },
    
    // GENERATOR combinations  
    'Generator_Emotional': {
      body: `Your gut says yes. But your wave says wait.\n\nSo you commit in the excitement—then time passes, the feeling shifts, and you're stuck with something that no longer feels right.\n\nThis creates a pattern: you respond, you commit, you question it later.`,
      coreLoop: "You respond, you commit fast, the feeling changes.",
      gateVariant: (influence) => `Your gut says yes. But your wave says wait.\n\nSo you commit${influence}—then time passes, the feeling shifts, and you're stuck with something that no longer feels right.\n\nThis creates a pattern: you respond, you commit, you question it later.`
    },
    'Generator_Sacral': {
      body: `Your body knows before your mind catches up. There's a pull toward or away—and it happens before reasons.\n\nThe pattern: you feel the response, you override it with logic, you end up drained and stuck. The body knew. You just didn't listen.`,
      coreLoop: "You sense it, you question it, you override.",
      gateVariant: (influence) => `Your body knows before your mind catches up${influence}. There's a pull toward or away—and it happens before reasons.\n\nThe pattern: you feel the response, you override it with logic, you end up drained and stuck. The body knew. You just didn't listen.`
    },
    
    // MANIFESTING GENERATOR combinations
    'Manifesting Generator_Emotional': {
      body: `You move fast. Your clarity doesn't.\n\nYou're already three steps ahead—but the wave hasn't settled. Excitement feels like truth, so you commit. Then time passes, the feeling shifts, and you're scattered across things that no longer feel right.`,
      coreLoop: "You start fast, the wave shifts, you're stuck or scattered.",
      gateVariant: (influence) => `You move fast${influence}. Your clarity doesn't.\n\nYou're already three steps ahead—but the wave hasn't settled. Excitement feels like truth, so you commit. Then time passes, the feeling shifts, and you're scattered across things that no longer feel right.`
    },
    'Manifesting Generator_Sacral': {
      body: `You pivot faster than others understand. They call it inconsistent. You call it following what's alive.\n\nThe pattern: you engage fully, the energy shifts, guilt hits, you force yourself to finish something already dead. The real inconsistency is staying on dead tracks.`,
      coreLoop: "You engage, energy dies, guilt keeps you stuck.",
      gateVariant: (influence) => `You pivot faster than others understand${influence}. They call it inconsistent. You call it following what's alive.\n\nThe pattern: you engage fully, the energy shifts, guilt hits, you force yourself to finish something already dead. The real inconsistency is staying on dead tracks.`
    },
    
    // PROJECTOR combinations
    'Projector_Emotional': {
      body: `You see what others miss. But your timing isn't about speed—it's about emotional clarity.\n\nThe pattern: you know the answer, you share it in a high, it lands wrong. Or you hold back in a low, and the moment passes. Recognition finds you when the wave has settled.`,
      coreLoop: "You see it, share it too soon, it misses.",
      gateVariant: (influence) => `You see what others miss${influence}. But your timing isn't about speed—it's about emotional clarity.\n\nThe pattern: you know the answer, you share it in a high, it lands wrong. Or you hold back in a low, and the moment passes. Recognition finds you when the wave has settled.`
    },
    'Projector_Splenic': {
      body: `You see into systems, people, patterns—often better than they see themselves. And your knowing comes in a flash.\n\nThe pattern: you sense the truth instantly, but share it before you're invited. It falls flat. You wonder why no one listens.`,
      coreLoop: "You know instantly, share uninvited, get ignored.",
      gateVariant: (influence) => `You see into systems, people, patterns${influence}—often better than they see themselves. And your knowing comes in a flash.\n\nThe pattern: you sense the truth instantly, but share it before you're invited. It falls flat. You wonder why no one listens.`
    },
    'Projector_Ego': {
      body: `You see what needs to happen. And when your heart is in it, you can guide powerfully.\n\nThe pattern: you commit your will to places that don't recognize you. Energy drains. Bitterness builds. Recognition only flows where your heart actually wants to be.`,
      coreLoop: "You give to where you're not recognized, resentment builds.",
    },
    'Projector_Self-Projected': {
      body: `You see patterns others miss. But your clarity comes through speaking, not thinking.\n\nThe pattern: you wait to be sure before sharing. But certainty lives in your voice—not before it. Speaking is how you find out what you know.`,
      coreLoop: "You hold back, stay silent, stay unclear.",
    },
    'Projector_None': {
      body: `You read people and systems with unusual depth. But your clarity doesn't live inside—it lives in environment.\n\nThe pattern: you try to figure things out alone. Nothing resolves. Change the setting, and suddenly you know.`,
      coreLoop: "You analyze internally, get nowhere, force it.",
    },
    
    // REFLECTOR combinations
    'Reflector_Lunar': {
      body: `You take in everything. You feel the room, the people, the energy—more intensely than most.\n\nThis creates a pattern: you make decisions too quickly, absorbing whatever energy is around you. Then days pass, the feeling changes, and you question everything.\n\nYour clarity needs time—about 28 days of it.`,
      coreLoop: "You absorb, you decide fast, you regret later.",
    },
    'Reflector_None': {
      body: `You reflect the world around you—deeply, continuously. That's not weakness. It's how you're built.\n\nThe pattern: you feel one way here, another way there. You think you're inconsistent. But you're actually reading each environment perfectly. The question isn't who you are—it's where you belong.`,
      coreLoop: "You shift constantly, think you're lost, but you're reading.",
    }
  };
  
  return templates[key] || null;
}

function getGateInfluenceForThread(topGate: number | null, secondGate: number | null): string | null {
  if (!topGate) return null;
  
  // Gate-specific flavor modifiers (subtle, not naming the gate)
  const gateInfluences: { [key: number]: string } = {
    1: ", especially around creative vision",
    2: ", particularly when it comes to direction",
    3: ", especially at the start of something new",
    4: ", particularly around finding answers",
    5: ", especially with timing and rhythm",
    6: ", particularly in emotional situations",
    7: ", especially around leadership",
    8: ", particularly when contributing",
    9: ", especially with details",
    10: ", particularly around authenticity",
    11: ", especially with ideas",
    12: ", particularly in expression",
    13: ", especially with past experiences",
    14: ", particularly around resources",
    15: ", especially with rhythms and timing",
    16: ", particularly in mastery",
    17: ", especially with opinions",
    18: ", particularly around correction",
    19: ", especially in sensing needs",
    20: ", particularly in the now",
    21: ", especially around control",
    22: ", particularly in emotional expression",
    23: ", especially with insights",
    24: ", particularly in mental processing",
    25: ", especially around innocence",
    26: ", particularly in influence",
    27: ", especially in caring",
    28: ", particularly around meaning",
    29: ", especially with commitment",
    30: ", particularly with feelings",
    31: ", especially around influence",
    32: ", particularly with continuity",
    33: ", especially in retreat",
    34: ", particularly around power",
    35: ", especially with experience",
    36: ", particularly in emotional exploration",
    37: ", especially in community",
    38: ", particularly in struggle",
    39: ", especially in provocation",
    40: ", particularly around rest",
    41: ", especially with new beginnings",
    42: ", particularly in completion",
    43: ", especially with unique perspectives",
    44: ", particularly around patterns",
    45: ", especially with resources",
    46: ", particularly around the body",
    47: ", especially in realization",
    48: ", particularly around depth",
    49: ", especially in principles",
    50: ", particularly in responsibility",
    51: ", especially with shock",
    52: ", particularly in stillness",
    53: ", especially at beginnings",
    54: ", particularly with ambition",
    55: ", especially emotionally",
    56: ", particularly in storytelling",
    57: ", especially intuitively",
    58: ", particularly with joy",
    59: ", especially in intimacy",
    60: ", particularly with limits",
    61: ", especially with mystery",
    62: ", particularly in details",
    63: ", especially with doubt",
    64: ", particularly in confusion"
  };
  
  return gateInfluences[topGate] || null;
}

// ============================================
// PATTERN STATE LAYER - REAL-TIME POSITIONING
// ============================================
// Transforms static insight into real-time awareness
// User feels: "This is where I am RIGHT NOW in the pattern"

export interface PatternState {
  currentPhase: string;
  whatThisLeadsTo: string;
  shiftAvailable: string;
}

export interface PatternStateInput {
  type: string;
  authority: string;
  dominantGate?: number | null;
  transitData?: any; // Future: current transit overlay
}

export function generatePatternState(input: PatternStateInput): PatternState | null {
  const { type, authority, dominantGate } = input;
  
  if (!type || !authority) return null;
  
  // Get phase detection based on Type + Authority combination
  const phaseData = detectCurrentPhase(type, authority, dominantGate);
  
  if (!phaseData) return null;
  
  return phaseData;
}

// Phase detection logic - uses Type × Authority to identify current state
function detectCurrentPhase(type: string, authority: string, dominantGate?: number | null): PatternState | null {
  // Emotional Authority phases (applies to all types with Emotional)
  if (authority === 'Emotional' || authority === 'Solar Plexus') {
    return getEmotionalPhase(type, dominantGate);
  }
  
  // Sacral Authority phases (Generator/MG)
  if (authority === 'Sacral') {
    return getSacralPhase(type, dominantGate);
  }
  
  // Splenic Authority phases
  if (authority === 'Splenic') {
    return getSplenicPhase(type, dominantGate);
  }
  
  // Ego/Heart Authority phases
  if (authority === 'Ego' || authority === 'Heart') {
    return getEgoPhase(type, dominantGate);
  }
  
  // Self-Projected Authority
  if (authority === 'Self-Projected' || authority === 'Self Projected') {
    return getSelfProjectedPhase(type, dominantGate);
  }
  
  // Mental/Environmental Authority
  if (authority === 'Mental' || authority === 'None' || authority === 'Environmental') {
    return getMentalPhase(type, dominantGate);
  }
  
  // Lunar Authority (Reflector)
  if (authority === 'Lunar') {
    return getLunarPhase(dominantGate);
  }
  
  // Fallback based on type
  return getTypeBasedPhase(type, dominantGate);
}

// ============================================
// EMOTIONAL AUTHORITY PHASES
// ============================================
function getEmotionalPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  if (type === 'Manifestor') {
    const phases: PatternState[] = [
      {
        currentPhase: "Right now, you're moving before the wave has settled. It feels right. That's the problem.",
        whatThisLeadsTo: "If you act from here, you'll be explaining yourself after—or questioning it once the feeling changes.",
        shiftAvailable: "The pattern shifts the moment you let the urgency pass before informing. Not after."
      },
      {
        currentPhase: "Right now, nothing feels certain. The urge to initiate is there, but so is doubt. This is the uncomfortable middle.",
        whatThisLeadsTo: "Force it from here and you'll either over-commit or pull back too hard. Both cost you later.",
        shiftAvailable: "Stay in the discomfort. The wave is still moving. Clarity comes—but not if you force it."
      },
      {
        currentPhase: "Right now, you have clarity—but you're hesitating. You think you need more certainty. You don't.",
        whatThisLeadsTo: "Wait too long and the window closes. The clarity you have won't stay forever.",
        shiftAvailable: "This is the moment. Inform and move. Trust it before the next wave begins."
      }
    ];
    return phases[phaseSelector];
  }
  
  if (type === 'Generator' || type === 'Manifesting Generator') {
    const phases: PatternState[] = [
      {
        currentPhase: "Right now, you're holding a commitment you made in the high. It felt real then. It might not be.",
        whatThisLeadsTo: "If nothing changes, you'll end up frustrated—or questioning every response you have.",
        shiftAvailable: "Next time, acknowledge the pull but don't commit. What's still alive when you're calm is actually yours."
      },
      {
        currentPhase: "Right now, you're in the dip. Nothing feels exciting. Everything feels heavier. This is the wave, not you.",
        whatThisLeadsTo: "Decide from here and you'll say no to things that are actually right—or drop what would satisfy you later.",
        shiftAvailable: "Don't decide anything now. The low is temporary. Ride it out."
      },
      {
        currentPhase: "Right now, the wave has passed. You can feel what landed and what didn't. This is where truth is available.",
        whatThisLeadsTo: "Clarity is here—but only if you're honest about what you're actually feeling now.",
        shiftAvailable: "This is the moment to assess. What still has energy? Keep it. What feels flat? Let it go."
      }
    ];
    return phases[phaseSelector];
  }
  
  if (type === 'Projector') {
    const phases: PatternState[] = [
      {
        currentPhase: "Right now, you see what needs to happen—and the urge to share is strong. But you're in a high. It's coloring everything.",
        whatThisLeadsTo: "Guide from here and it lands wrong. People feel pushed, not helped. The insight is right—the timing isn't.",
        shiftAvailable: "Hold it. Let the wave settle. If the insight is real, it'll still be there when you're calm."
      },
      {
        currentPhase: "Right now, it's hard to see your value. Recognition feels far away. Everything feels like effort. This is the low.",
        whatThisLeadsTo: "Push from here and you'll give where you weren't asked, resent the silence, and pull back wounded.",
        shiftAvailable: "Rest. Not later—now. Your clarity returns when the wave lifts. Wait for it."
      },
      {
        currentPhase: "Right now, you're in a clear space. Neither high nor low. This is when you see without distortion.",
        whatThisLeadsTo: "If you're invited, speak. Your perception is clean right now.",
        shiftAvailable: "Act on the invitations that came. This neutral place is where your guidance actually serves."
      }
    ];
    return phases[phaseSelector];
  }
  
  // Reflector with Emotional definition
  return {
    currentPhase: "Right now, the wave is moving through you—amplified by everything around. It's hard to tell what's yours. That's normal.",
    whatThisLeadsTo: "Whatever you decide now reflects the current mood, not the deeper truth. It will change.",
    shiftAvailable: "Give it time. A full cycle if possible. What stays consistent across the whole wave is what's real."
  };
}

// ============================================
// SACRAL AUTHORITY PHASES
// ============================================
function getSacralPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  if (type === 'Generator') {
    const phases: PatternState[] = [
      {
        currentPhase: "Right now, your gut responded—and your mind is already questioning it. This is where you usually override what you knew.",
        whatThisLeadsTo: "Talk yourself out of it and you'll end up somewhere your body never agreed to. The frustration that follows isn't random.",
        shiftAvailable: "The body already answered. Act on the pull before the mind convinces you otherwise."
      },
      {
        currentPhase: "Right now, you're in something your body never actually said yes to. The energy isn't there. You know it.",
        whatThisLeadsTo: "Push through and you'll finish—but you'll resent it. And you'll wonder why this keeps happening.",
        shiftAvailable: "Notice what your body is telling you now. Not what makes sense—what feels alive. That's where the correction starts."
      },
      {
        currentPhase: "Right now, nothing is lighting up. You're waiting. It feels like stagnation. It's not.",
        whatThisLeadsTo: "Force something just to feel productive and you'll create another draining situation.",
        shiftAvailable: "Stay available. When the right thing appears, your body will tell you instantly. Until then, rest is correct."
      }
    ];
    return phases[phaseSelector];
  }
  
  // Manifesting Generator
  const phases: PatternState[] = [
    {
      currentPhase: "Right now, you're mid-pivot. The energy shifted and you're already moving. You think you know why. You might not.",
      whatThisLeadsTo: "Keep going without pausing and the loop continues: start, die, pivot, guilt, start again.",
      shiftAvailable: "Pause. Just briefly. Is this a real pivot or an escape? If it survives a moment of stillness, it's real."
    },
    {
      currentPhase: "Right now, you're backtracking. You started fast, skipped steps, and now you're stuck. This is the friction of your non-linear path.",
      whatThisLeadsTo: "Fight the backtrack and you waste energy. The steps you skipped need addressing—just not the way they expected.",
      shiftAvailable: "Accept the correction. The path isn't broken. You're doing things in your order, not theirs."
    },
    {
      currentPhase: "Right now, multiple things are pulling at you. You want to respond to all of them. The pressure to choose feels like a trap. It is.",
      whatThisLeadsTo: "Try everything and you'll scatter. Force one choice and you'll resent it.",
      shiftAvailable: "Sample them all. Quickly. Your body will tell you which has real energy. Then go all in—until the energy shifts again."
    }
  ];
  return phases[phaseSelector];
}

// ============================================
// SPLENIC AUTHORITY PHASES
// ============================================
function getSplenicPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  const phases: PatternState[] = [
    {
      currentPhase: "Right now, you knew something a moment ago—and it's gone. You're trying to remember. You won't. That's the pattern.",
      whatThisLeadsTo: "Reason your way back and you'll never find it. The insight came once. It doesn't repeat.",
      shiftAvailable: "Next time, trust the first hit. The knowing is quiet and fast—act before the mind starts."
    },
    {
      currentPhase: "Right now, you're second-guessing. Something felt clear. Now you're not sure. The doubt isn't wisdom—it's noise.",
      whatThisLeadsTo: "Keep questioning and you'll talk yourself into something your instincts already rejected.",
      shiftAvailable: "Return to the body. Not thoughts about the body. The actual sensation. That's the only data that matters."
    },
    {
      currentPhase: "Right now, you caught it. The knowing came. You recognized it. The window is still open. Barely.",
      whatThisLeadsTo: "Wait to think it through and you'll lose it. The clarity is here now. It won't be in five minutes.",
      shiftAvailable: "Move. Now. Understanding can come later—or not at all. The knowing was real."
    }
  ];
  return phases[phaseSelector];
}

// ============================================
// EGO AUTHORITY PHASES
// ============================================
function getEgoPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  const phases: PatternState[] = [
    {
      currentPhase: "Right now, you're running on fumes. You committed to something your heart wasn't in. You know it.",
      whatThisLeadsTo: "Keep pushing and you'll either break the promise or break yourself. Willpower can't sustain what desire didn't choose.",
      shiftAvailable: "Be honest about what you actually want. If the desire isn't there, the commitment needs renegotiating."
    },
    {
      currentPhase: "Right now, something is pulling at you. It feels real—not obligated, not reasoned. This is different. This is genuine want.",
      whatThisLeadsTo: "Commit from here and you'll have the energy to follow through. This is how it's supposed to work.",
      shiftAvailable: "Say yes. Make the promise. When desire is real, your word becomes unbreakable."
    },
    {
      currentPhase: "Right now, you're being asked to promise something—and the fire isn't there. You feel the pressure to say yes. That's not the same as want.",
      whatThisLeadsTo: "Commit without the want and you'll add another broken promise to the pile—or exhaust yourself keeping one your heart never made.",
      shiftAvailable: "Wait until you feel the pull. If it doesn't come, don't commit. Your integrity depends on honest desire."
    }
  ];
  return phases[phaseSelector];
}

// ============================================
// SELF-PROJECTED AUTHORITY PHASES
// ============================================
function getSelfProjectedPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  const phases: PatternState[] = [
    {
      currentPhase: "Right now, you're stuck in your head, trying to think your way to clarity. It won't work. The answer isn't in the thinking.",
      whatThisLeadsTo: "Keep thinking without speaking and you'll stay stuck. Clarity doesn't live in silence—it lives in your voice.",
      shiftAvailable: "Talk. To someone, to yourself, to a recording. Start before you're ready. Direction emerges as you speak."
    },
    {
      currentPhase: "Right now, you just heard yourself say something you didn't expect. That surprised you. Good. That's the truth arriving.",
      whatThisLeadsTo: "What you heard is more accurate than what you've been thinking. Don't dismiss it because it didn't match the plan.",
      shiftAvailable: "Follow what you heard yourself say. Your voice knows things your mind is still catching up to."
    },
    {
      currentPhase: "Right now, you're holding back. Waiting to be sure before you speak. But certainty only comes through speaking. You're waiting for something that arrives after.",
      whatThisLeadsTo: "Stay silent and you stay frozen. Silence isn't helping you process—it's keeping you stuck.",
      shiftAvailable: "Find someone to talk to. Not for advice—for witnessing. The clarity is on the other side of speaking."
    }
  ];
  return phases[phaseSelector];
}

// ============================================
// MENTAL/ENVIRONMENTAL AUTHORITY PHASES
// ============================================
function getMentalPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  const phases: PatternState[] = [
    {
      currentPhase: "Right now, you're trying to decide from where you are. But this place is shaping what you think you know. The clarity you feel might not travel.",
      whatThisLeadsTo: "Decide from here and you'll wonder later why it felt so clear then and so wrong now.",
      shiftAvailable: "Change the environment. Literally move. Notice if the same choice still feels right somewhere else."
    },
    {
      currentPhase: "Right now, you're hearing different things from different people. Each conversation shifts what feels true. That's not confusion—that's how you process.",
      whatThisLeadsTo: "Integrate it all at once and you'll feel scattered. Commit to one view and you'll miss what the others revealed.",
      shiftAvailable: "Keep gathering. The answer emerges from the pattern across conversations, not any single one."
    },
    {
      currentPhase: "Right now, something is becoming clear—not from inside, but from outside. The right setting is revealing the right direction. This is your clarity arriving.",
      whatThisLeadsTo: "The environment is showing you something true. This is the moment to note it.",
      shiftAvailable: "Trust what's being revealed here. Not because you figured it out—because the right conditions made it obvious."
    }
  ];
  return phases[phaseSelector];
}

// ============================================
// LUNAR AUTHORITY PHASES (REFLECTOR)
// CRITICAL: No instant-decision language
// ============================================
function getLunarPhase(dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  const phases: PatternState[] = [
    {
      currentPhase: "Right now, you're still taking this in. It may feel like something is forming—but it's not settled yet. You're early in the cycle.",
      whatThisLeadsTo: "What you feel today is only part of the picture. The perspective will shift—maybe completely. That's not inconsistency. That's how you see.",
      shiftAvailable: "Note what you feel today. Then let it go. Come back to this in a week, and again in two. What stays true across the whole cycle is what's real."
    },
    {
      currentPhase: "Right now, you've felt this from several angles. Some days it felt right, some days wrong. That's data, not confusion. You're building the picture.",
      whatThisLeadsTo: "Don't try to average out the feelings. It's not about which one wins. It's about what pattern is emerging across all of them.",
      shiftAvailable: "Keep tracking. You're seeing more than most ever get to see. The clarity is coming—don't rush it."
    },
    {
      currentPhase: "Right now, the cycle is complete—or nearly. You've felt this from every angle. Something has become consistent. Or consistently inconsistent. Either way, that's your answer.",
      whatThisLeadsTo: "What stayed true across the whole cycle is genuinely yours. What kept changing belongs to the environments you passed through.",
      shiftAvailable: "You have the full picture now. Trust what survived the whole cycle—it's the only thing that will hold."
    }
  ];
  return phases[phaseSelector];
}

// ============================================
// TYPE-BASED FALLBACK
// ============================================
function getTypeBasedPhase(type: string, dominantGate?: number | null): PatternState {
  const gateNumber = dominantGate || 0;
  const phaseSelector = (gateNumber % 3);
  
  const typePhases: { [key: string]: PatternState[] } = {
    'Manifestor': [
      {
        currentPhase: "Right now, the pull to initiate is strong. You want to just do it. The impact feels close. That's real.",
        whatThisLeadsTo: "Move without informing and you'll create resistance you didn't intend. The power is real—so is the pushback.",
        shiftAvailable: "Pause to inform. Not ask—inform. Then move with your full power."
      },
      {
        currentPhase: "Right now, you're in withdrawal mode. The world feels like resistance. You're pulling back, not initiating. That's not wrong.",
        whatThisLeadsTo: "Stay withdrawn too long and you lose touch with your power to create. Isolation becomes pattern, not rest.",
        shiftAvailable: "When the next urge comes, engage. Inform, then act. The resistance you expect might not be there."
      },
      {
        currentPhase: "Right now, you're meeting friction. People are reacting to something you did. Your impact is landing—roughly.",
        whatThisLeadsTo: "Fight the friction and it escalates. Withdraw completely and nothing resolves.",
        shiftAvailable: "Let the impact settle. You don't have to fix their reaction. Clarity reduces resistance."
      }
    ],
    'Projector': [
      {
        currentPhase: "Right now, you see something clearly—a pattern, a solution, a truth. The urge to share is strong. You think you know. You do.",
        whatThisLeadsTo: "Share without invitation and it lands wrong. The insight is right, the delivery misses. Bitterness follows.",
        shiftAvailable: "Wait for the ask. If it doesn't come, ask if they want to hear it. The invitation changes everything."
      },
      {
        currentPhase: "Right now, you're tired. The energy to guide isn't there. You've been giving without receiving. It's showing.",
        whatThisLeadsTo: "Keep pushing and you'll deplete further. Bitterness grows. Recognition feels even further away.",
        shiftAvailable: "Stop. Rest isn't optional for you—it's essential. Your value doesn't depend on constant output."
      },
      {
        currentPhase: "Right now, someone sees you. The energy is right. The invitation is real. This is the space you've been waiting for.",
        whatThisLeadsTo: "This is where your gifts land. Speak here. Guide here. This is why you wait.",
        shiftAvailable: "Accept the recognition. Share what you see. This is the exchange working correctly."
      }
    ],
    'Reflector': [
      {
        currentPhase: "Right now, you're absorbing everything around you. What's yours and what's theirs—it's all mixed together. That's normal.",
        whatThisLeadsTo: "Whatever you conclude now reflects the current conditions, not necessarily your deeper truth. It will change.",
        shiftAvailable: "Don't lock anything in yet. Sample the experience. Let time pass before deciding anything permanent."
      },
      {
        currentPhase: "Right now, something keeps surprising you—a place, a person, a situation that keeps delighting you. That's data.",
        whatThisLeadsTo: "Surprise is your signal that something is alive. Pay attention to what consistently surprises you.",
        shiftAvailable: "Follow the surprise. Where you keep being delighted is where you belong. That's your navigation."
      },
      {
        currentPhase: "Right now, you're showing them something they're not ready to see. You're reflecting who they are—and it's uncomfortable for them.",
        whatThisLeadsTo: "Take on their discomfort and it becomes yours. Hold your place and they might eventually see.",
        shiftAvailable: "Stay neutral. You're not responsible for what they see in you. Reflect accurately—don't manage their reaction."
      }
    ]
  };
  
  // Default Generator fallback
  const defaultPhases: PatternState[] = [
    {
      currentPhase: "Right now, you're in the middle of something—engaged but not sure if it's right. That uncertainty is information.",
      whatThisLeadsTo: "Clarity will come. Whether it feels satisfying or frustrating will tell you everything.",
      shiftAvailable: "Keep paying attention to how it feels. Not what you think—how it feels in your body."
    },
    {
      currentPhase: "Right now, something isn't right. The energy isn't there. You're pushing through something that may not be yours.",
      whatThisLeadsTo: "If the frustration continues, the signal is clear. This isn't aligned. Your body is telling you.",
      shiftAvailable: "Notice where the energy actually wants to go. Not where you think it should. Follow that."
    },
    {
      currentPhase: "Right now, you're in flow. Something is working. The energy is there without forcing. This is what you're looking for.",
      whatThisLeadsTo: "This is alignment. This is what you're seeking in every commitment.",
      shiftAvailable: "Keep going. Trust this. Let satisfaction confirm you're on the right track."
    }
  ];
  
  return typePhases[type]?.[phaseSelector] || defaultPhases[phaseSelector];
}
