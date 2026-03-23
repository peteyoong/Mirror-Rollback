// ============================================
// HUMAN DESIGN MASTER SYNTHESIS LAYER
// ============================================
// Expert-level integration of ALL HD mechanics into a unified reading
// CHANNELS as narrative drivers
// CONSCIOUS vs UNCONSCIOUS as core tension
// ENVIRONMENT + COGNITION as conditions
// MOTIVATION → TRANSFERENCE as distortion
// SPLIT DEFINITION as relational mechanics
// INCARNATION CROSS as lived behavior

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
  // MASTER LEVEL DATA
  channels?: ChannelData[];
  definedCenters?: string[];
  undefinedCenters?: string[];
  consciousGates?: number[];
  unconsciousGates?: number[];
  // Personality vs Design (Conscious vs Unconscious)
  personalitySun?: number | { gate: number; line: number };
  personalityEarth?: number | { gate: number; line: number };
  designSun?: number | { gate: number; line: number };
  designEarth?: number | { gate: number; line: number };
  // Variables (if available)
  environment?: string;
  cognition?: string;
  determination?: string;
  motivation?: string;
  transference?: string;
  perspective?: string;
  view?: string;
}

// ============================================
// CHANNEL NARRATIVES - The Core Story Drivers
// ============================================
// Channels are NOT details - they are the BACKBONE of life themes

interface ChannelNarrative {
  livedTheme: string;
  behavioralPattern: string;
  tension: string;
  genius: string;
}

const CHANNEL_NARRATIVES: { [key: string]: ChannelNarrative } = {
  // FORMAT COLLECTIVE - Sharing / Understanding
  '35-36': {
    livedTheme: "You're built to move through experiences—testing, learning, and evolving through what life throws at you. You don't grow by thinking. You grow by living it.",
    behavioralPattern: "seeking new emotional experiences, often feeling restless until something stirs you",
    tension: "The hunger for experience can push you into situations before you're ready, or keep you moving when stillness would serve better.",
    genius: "When you trust the emotional journey and don't rush the process, your experiential wisdom becomes genuinely transformative for others."
  },
  '12-22': {
    livedTheme: "You carry emotional expression that needs to land. When the mood is right and you're genuinely moved, your voice has unusual impact.",
    behavioralPattern: "going silent when the emotional timing isn't right, then expressing powerfully when it is",
    tension: "Expressing before the emotional wave settles leads to impact that misses. Holding back too long loses the moment entirely.",
    genius: "When your emotional clarity and timing align, you can move people in ways that feel genuine rather than performed."
  },
  '21-45': {
    livedTheme: "You're designed to control resources and direct energy. There's an inherent authority about how things should be organized and distributed.",
    behavioralPattern: "naturally taking charge of material situations, sometimes before being asked",
    tension: "Control exercised from willpower alone burns out. Control that emerges from genuine desire sustains.",
    genius: "When your will aligns with what truly matters to you, your ability to direct and manage becomes effortlessly effective."
  },
  '37-40': {
    livedTheme: "You're built for community bargains—the give-and-take of belonging. You feel responsible for the people you let close.",
    behavioralPattern: "forming deep bonds with clear (often unspoken) expectations of loyalty and reciprocity",
    tension: "When bargains aren't honored—when you give and don't receive—resentment builds. But trying to keep score kills the warmth.",
    genius: "When you trust the flow of giving and receiving without micromanaging it, your community bonds become genuinely sustaining."
  },
  '6-59': {
    livedTheme: "You carry intimacy that can break through barriers. There's a penetrating emotional quality that either draws people in or pushes them away.",
    behavioralPattern: "creating deep emotional connection quickly, sometimes with intensity others aren't prepared for",
    tension: "Intimacy without discernment exhausts. Not every barrier is meant to be broken.",
    genius: "When you're selective about where you direct this energy, your capacity for connection creates bonds that genuinely transform."
  },
  // LOGIC COLLECTIVE - Pattern Recognition
  '63-4': {
    livedTheme: "Your mind is designed to spot what doesn't make sense. You notice logical inconsistencies others miss.",
    behavioralPattern: "questioning what seems accepted, looking for the flaw in the reasoning",
    tension: "Doubt without resolution creates anxiety. Not every inconsistency needs solving.",
    genius: "When you trust your logical skepticism while staying open to mystery, your ability to refine understanding becomes genuinely valuable."
  },
  '17-62': {
    livedTheme: "You organize information into opinions. There's a drive to form views and share them—to help others see what makes sense.",
    behavioralPattern: "developing strong positions and wanting to share them, sometimes whether asked or not",
    tension: "Opinions shared without invitation feel like lectures. Holding back when you genuinely see something creates frustration.",
    genius: "When your opinions are genuinely requested, your ability to articulate understanding has real impact."
  },
  '18-58': {
    livedTheme: "You're built to spot what's wrong and sense how to improve it. There's an instinctive recognition of what could be better.",
    behavioralPattern: "noticing flaws and feeling driven to correct them, even when others don't see the problem",
    tension: "Correction without request feels like criticism. The drive to fix can damage relationships.",
    genius: "When you direct your corrective insight toward things that genuinely ask for improvement, your precision becomes genuinely valuable."
  },
  // SENSING COLLECTIVE - Instinct / Survival
  '28-38': {
    livedTheme: "You're designed to struggle for what matters. There's a stubbornness that fights for meaning even when others have given up.",
    behavioralPattern: "engaging in battles over principle, often feeling that struggle itself is meaningful",
    tension: "Not every battle is worth fighting. Stubbornness without discernment exhausts everyone.",
    genius: "When you direct your fighting spirit toward causes that genuinely call you, your tenacity creates change that matters."
  },
  '57-34': {
    livedTheme: "You have powerful instincts paired with available energy. When intuition and power align, you can respond with unusual effectiveness.",
    behavioralPattern: "sensing what's right and having the energy to act on it immediately",
    tension: "Instinct ignored in favor of thinking leads to missed opportunities. Acting without real intuition wastes power.",
    genius: "When you trust your instincts and respond in the moment, you have access to a power that can't be manufactured."
  },
  '57-10': {
    livedTheme: "You're built to behave according to intuitive knowing. There's an authenticity that emerges when you trust your instincts.",
    behavioralPattern: "acting true to yourself when intuition supports it, feeling out of integrity when you override",
    tension: "Authenticity performed is fake. Authenticity ignored creates internal conflict.",
    genius: "When you trust your instincts about who you are and act accordingly, you model a way of being that others recognize as real."
  },
  // INDIVIDUAL CIRCUITRY - Knowing / Centering
  '61-24': {
    livedTheme: "Your mind cycles through inspiration and rationalization. Ideas come unbidden, then need to be processed and understood.",
    behavioralPattern: "receiving mental downloads that need time to integrate, feeling pressure to make sense of inner knowing",
    tension: "Forcing understanding before it's ready distorts the inspiration. Sharing too early leads to confusion.",
    genius: "When you let inspirations mature without forcing, your unique knowing becomes accessible to others."
  },
  '51-25': {
    livedTheme: "You're built to initiate others into new ways of being. There's a shocking quality that can catalyze transformation.",
    behavioralPattern: "showing up in ways that shake people out of complacency, sometimes without intending to",
    tension: "Shock for its own sake repels. Withholding your impact when it's genuinely needed serves no one.",
    genius: "When you trust your timing and let your presence create natural disruption, you catalyze transformation that sticks."
  },
  '43-23': {
    livedTheme: "You know things without knowing how you know them. There's inner knowing that wants expression but often feels misunderstood.",
    behavioralPattern: "carrying unique insights that feel obvious to you but strange to others",
    tension: "Expressing knowing to the wrong audience leads to rejection. Holding back leads to frustration.",
    genius: "When you find ears that can hear, your unique knowing has the power to genuinely shift how people see."
  },
  '8-1': {
    livedTheme: "You're designed to contribute creatively and be recognized for it. There's an individual expression that needs to be shared.",
    behavioralPattern: "creating or expressing in distinctive ways, wanting recognition for your unique contribution",
    tension: "Creating for recognition corrupts the expression. Hiding what's genuinely yours serves no one.",
    genius: "When you create from authentic self-expression, recognition finds you without you chasing it."
  },
  '2-14': {
    livedTheme: "You carry resources that respond to direction. There's energy available for causes that genuinely align.",
    behavioralPattern: "having access to power and means, responding to directions that feel right",
    tension: "Resources spent without discernment deplete. Hoarding when genuine calls appear misses the point.",
    genius: "When you let your resources respond to directions that genuinely move you, your contribution becomes precisely effective."
  },
  // EGO CIRCUITRY
  '26-44': {
    livedTheme: "You have influence through memory and transmission. What you remember and share has unusual staying power.",
    behavioralPattern: "recognizing patterns from the past and communicating them in ways that stick",
    tension: "Selling what you don't believe in corrupts your influence. Withholding genuine transmission wastes your gift.",
    genius: "When your influence serves patterns you genuinely recognize as valuable, your transmission becomes authentically compelling."
  },
  '25-51': {
    livedTheme: "You're designed to initiate through spirit. There's a will to shock that serves a higher love or innocence.",
    behavioralPattern: "catalyzing transformation through unexpected spiritual initiation",
    tension: "Initiating without spirit becomes mere disruption. Holding back when spirit moves wastes the moment.",
    genius: "When your initiation comes from genuine spiritual impulse, you wake people up without destroying them."
  },
};

// ============================================
// INCARNATION CROSS NARRATIVES
// Lived behavior, NOT abstract purpose
// ============================================

interface CrossNarrative {
  livedBehavior: string;
  tension: string;
  genius: string;
}

const CROSS_NARRATIVES: { [key: string]: CrossNarrative } = {
  'migration': {
    livedBehavior: "You are here to move people, systems, or situations from one state into another. You disrupt stability so something new can take shape.",
    tension: "Not every stable thing needs disrupting. Your movement instinct can unsettle what's actually working.",
    genius: "When you direct your moving energy toward situations genuinely ready for transition, you become the catalyst that makes change possible."
  },
  'service': {
    livedBehavior: "You are here to be of practical use. Your life orients around contribution that actually helps, not help that looks helpful.",
    tension: "Service without discernment depletes. Not every request deserves your response.",
    genius: "When you serve from genuine response rather than obligation, your contribution lands precisely where it's needed."
  },
  'planning': {
    livedBehavior: "You are here to create structures that sustain. Your mind naturally organizes around what will work over time.",
    tension: "Planning without responsiveness becomes control. Not every situation needs your structure.",
    genius: "When your planning serves what's genuinely emerging, you create foundations others can build on."
  },
  'explanation': {
    livedBehavior: "You are here to translate complexity into understanding. You take what's confusing and make it accessible.",
    tension: "Explaining what wasn't asked for feels like lecturing. Not everything needs your translation.",
    genius: "When your explanations serve genuine questions, you bridge gaps that seemed impossible."
  },
  'consciousness': {
    livedBehavior: "You are here to awaken awareness. Your presence naturally brings attention to what's been overlooked or unconscious.",
    tension: "Forcing awareness creates resistance. Not everyone is ready to see what you see.",
    genius: "When you trust timing and let awareness dawn naturally, you open doors that force would keep locked."
  },
  'eden': {
    livedBehavior: "You are here to remind people of innocence. Your presence points toward original wholeness beneath accumulated damage.",
    tension: "Insisting on innocence when survival requires toughness misses context. Not every moment calls for paradise.",
    genius: "When you hold space for innocence without denying reality, you offer healing that actually integrates."
  },
  'vessel of love': {
    livedBehavior: "You are here to carry love as a felt experience. Your presence transmits warmth that others can actually receive.",
    tension: "Love performed isn't love. When you try to be loving rather than letting love move through you, it falls flat.",
    genius: "When you let yourself be moved rather than trying to move others, your presence becomes genuinely transformative."
  },
  'tension': {
    livedBehavior: "You are here to hold creative discomfort. You sit with what doesn't resolve and let something emerge from that pressure.",
    tension: "Forcing resolution to escape discomfort kills what's trying to be born. But endless tension with no movement exhausts.",
    genius: "When you trust the tension without forcing or fleeing, creativity emerges that could never have been planned."
  },
  'the four ways': {
    livedBehavior: "You are here to show multiple paths. Your life demonstrates that there's more than one right answer.",
    tension: "Too many options paralyzes. Not every situation needs all the alternatives.",
    genius: "When you offer variety in service of genuine choice rather than confusion, you open possibilities others couldn't see."
  },
  'the unexpected': {
    livedBehavior: "You are here to break patterns. Your presence introduces what no one saw coming.",
    tension: "Shock for its own sake repels. Being unpredictable just to maintain unpredictability loses meaning.",
    genius: "When your unexpected nature serves genuine emergence, you become the crack in certainty that lets light through."
  },
  'rulership': {
    livedBehavior: "You are here to demonstrate leadership. Your life naturally orients around directing, guiding, and taking responsibility.",
    tension: "Leadership without invitation becomes control. Not everyone wants or needs your direction.",
    genius: "When you lead what genuinely asks for leadership, your direction feels like a gift rather than imposition."
  },
  'the sphinx': {
    livedBehavior: "You are here to embody questions that have no easy answers. Your presence invites inquiry rather than conclusion.",
    tension: "Remaining mysterious when clarity would serve better creates frustration. Not every question needs preserving.",
    genius: "When you hold essential questions without forcing answers, you create space for genuine discovery."
  },
  'penetration': {
    livedBehavior: "You are here to go deep. Your life moves toward depth rather than breadth, intimacy rather than acquaintance.",
    tension: "Penetration without permission violates. Not everyone wants or is ready for that depth.",
    genius: "When you direct your penetrating quality toward what genuinely invites it, your depth reveals what surfaces miss."
  },
};

// ============================================
// CONSCIOUS vs UNCONSCIOUS PATTERNS
// What you think you're doing vs what's actually driving you
// ============================================

interface ConsciousUnconsciousPattern {
  dynamic: string;
  tension: string;
  blindSpot: string;
}

const getConsciousUnconsciousPattern = (
  consciousGates: number[],
  unconsciousGates: number[],
  profile: string,
  personalitySun?: number | { gate: number; line: number },
  designSun?: number | { gate: number; line: number }
): ConsciousUnconsciousPattern => {
  // Get gate numbers
  const pSunGate = typeof personalitySun === 'object' ? personalitySun?.gate : personalitySun;
  const dSunGate = typeof designSun === 'object' ? designSun?.gate : designSun;
  
  // Profile lines reveal conscious/unconscious split
  const [firstLine, secondLine] = profile?.split('/').map(Number) || [1, 3];
  
  // The second line is unconscious - drives behavior without awareness
  const unconsciousLinePatterns: { [key: number]: string } = {
    1: "Your body is always seeking foundation—researching, needing to feel secure before moving—even when your mind thinks it's ready to go.",
    2: "Something natural operates through you without you trying. Others see gifts in you that you don't consciously develop.",
    3: "Part of you keeps experimenting even when you think you've settled. The trial continues underneath your awareness.",
    4: "Your body is network-oriented. Relationships shift your direction more than you consciously choose.",
    5: "You attract projections whether you want them or not. Something about you suggests solutions to others.",
    6: "A part of you is always observing—taking notes for a role you're growing into."
  };
  
  const consciousLinePatterns: { [key: number]: string } = {
    1: "investigate and build foundations",
    2: "wait for your natural gifts to be called out",
    3: "experiment and learn from trial",
    4: "influence through close networks",
    5: "provide practical solutions",
    6: "model wisdom and perspective"
  };
  
  const unconsciousPattern = unconsciousLinePatterns[secondLine] || "Your unconscious drives are operating below your awareness.";
  const consciousPattern = consciousLinePatterns[firstLine] || "express your conscious identity";
  
  // Create dynamic based on sun gates if available
  let sunDynamic = "";
  if (pSunGate && dSunGate && pSunGate !== dSunGate) {
    sunDynamic = ` Your conscious identity (Gate ${pSunGate}) often explains decisions your body (Gate ${dSunGate}) has already made.`;
  }
  
  return {
    dynamic: `You think you're operating one way—trying to ${consciousPattern}—but underneath: ${unconsciousPattern.toLowerCase()}${sunDynamic}`,
    tension: "You often understand your pattern only after it plays out. Your mind tries to explain decisions your body has already made.",
    blindSpot: `You think you know why you do what you do. But ${unconsciousPattern.charAt(0).toLowerCase()}${unconsciousPattern.slice(1)}`
  };
};

// ============================================
// ENVIRONMENT PATTERNS
// Where you function best
// ============================================

interface EnvironmentPattern {
  optimal: string;
  distortion: string;
  practical: string;
}

const ENVIRONMENT_PATTERNS: { [key: string]: EnvironmentPattern } = {
  'caves': {
    optimal: "You function best in enclosed, selective environments where you can control what comes in. Too much exposure scrambles your system.",
    distortion: "In the wrong environment—too open, too exposed—clarity becomes impossible and you feel perpetually unsettled.",
    practical: "Create boundaries around your space. Be selective about what environments you enter and how long you stay."
  },
  'markets': {
    optimal: "You function best in busy, diverse environments where there's movement and variety. Isolation dampens your clarity.",
    distortion: "In too quiet or too uniform environments, you lose access to the information flow you need to function well.",
    practical: "Seek environments with diversity and exchange. Your clarity depends on having enough to sample."
  },
  'kitchens': {
    optimal: "You function best where transformation is happening—where raw materials become something new. Process environments suit you.",
    distortion: "In static environments where nothing is being created or transformed, your energy stagnates.",
    practical: "Position yourself where things are being made, prepared, or transformed. Your clarity lives in process."
  },
  'mountains': {
    optimal: "You function best with perspective—elevated positions where you can see the whole landscape. Being in the weeds clouds you.",
    distortion: "Too close to the details, too embedded in ground-level concerns, you lose the overview that guides you.",
    practical: "Create or find positions of perspective. Your clarity requires some distance from immediate entanglement."
  },
  'valleys': {
    optimal: "You function best in environments where information and people are moving—where there's flow, exchange, and visibility.",
    distortion: "In the wrong environment—too still, too stagnant—nothing feels right even when nothing is technically wrong.",
    practical: "Seek places of natural flow and exchange. Your clarity depends on being where things are moving."
  },
  'shores': {
    optimal: "You function best at edges—where one thing meets another, where transition happens. Pure environments lack what you need.",
    distortion: "Too far from the edge, in environments that are entirely one thing, you lose the contrast that clarifies.",
    practical: "Position yourself at boundaries and transitions. Your clarity emerges at the meeting of different elements."
  }
};

// ============================================
// MOTIVATION → TRANSFERENCE (DISTORTION PATTERNS)
// How correct motivation becomes distorted
// ============================================

interface MotivationTransference {
  correct: string;
  distorted: string;
  behavioral: string;
}

const MOTIVATION_TRANSFERENCE: { [key: string]: { [trans: string]: MotivationTransference } } = {
  'fear': {
    'desire': {
      correct: "You're designed to improve what's dangerous or at risk. Your sensitivity to fear drives valuable correction.",
      distorted: "When off, fear becomes desire—you start wanting what you should be afraid of, or fearing what you should desire.",
      behavioral: "You find yourself chasing things that feel exciting but are actually dangerous, or avoiding what would genuinely serve you."
    },
    'default': {
      correct: "You're designed to be moved by genuine fear—using it as intelligent information about what needs attention.",
      distorted: "When you're not yourself, fear distorts into either paralysis or reckless disregard for actual danger.",
      behavioral: "You either freeze when you should act, or ignore danger when you should pay attention."
    }
  },
  'hope': {
    'guilt': {
      correct: "You're designed to move toward possibilities—to sense what could be and work toward it.",
      distorted: "When off, hope becomes guilt—you feel responsible for possibilities not realized, or obligated to hope when you don't.",
      behavioral: "You carry guilt about not being more hopeful, or feel burdened by possibilities you can't fulfill."
    },
    'default': {
      correct: "You're designed to be moved by genuine hope—sensing positive possibilities and moving toward them.",
      distorted: "When you're not yourself, hope distorts into either naive optimism or cynical dismissal of possibility.",
      behavioral: "You either believe anything is possible or refuse to see genuine openings."
    }
  },
  'desire': {
    'fear': {
      correct: "You're designed to move toward what you genuinely want—letting desire guide your direction.",
      distorted: "When off, desire becomes fear—you start fearing what you want, or wanting what scares you.",
      behavioral: "You find yourself afraid of getting what you actually want, or compulsively chasing what frightens you."
    },
    'default': {
      correct: "You're designed to be moved by authentic desire—knowing what you want and moving toward it.",
      distorted: "When you're not yourself, desire distorts into either grasping or denial of wanting anything.",
      behavioral: "You either grasp compulsively or pretend you don't want things."
    }
  },
  'guilt': {
    'hope': {
      correct: "You're designed to improve what isn't working—to feel responsible and act on it.",
      distorted: "When off, that responsibility becomes hope—you start hoping things will improve rather than actually fixing them.",
      behavioral: "You hope problems will resolve themselves instead of taking the corrective action you're designed for."
    },
    'default': {
      correct: "You're designed to feel genuinely responsible—to notice what needs correction and act on it.",
      distorted: "When you're not yourself, responsibility distorts into either crushing guilt or abdication of any responsibility.",
      behavioral: "You either carry guilt for everything or refuse to feel responsible for anything."
    }
  },
  'need': {
    'innocence': {
      correct: "You're designed to recognize and fulfill genuine needs—yours and others.",
      distorted: "When off, need becomes innocence—you ignore real needs in favor of pretending everything is fine.",
      behavioral: "You deny obvious needs in yourself or others, claiming innocence or simplicity when complexity is real."
    },
    'default': {
      correct: "You're designed to be attuned to genuine needs—responding to what's actually required.",
      distorted: "When you're not yourself, need distorts into either neediness or denial of any need.",
      behavioral: "You either become excessively needy or pretend you need nothing from anyone."
    }
  },
  'innocence': {
    'need': {
      correct: "You're designed to see and preserve what's pure—to protect innocence where it genuinely exists.",
      distorted: "When off, innocence becomes need—you become needy for purity or demand others maintain an impossible innocence.",
      behavioral: "You create needs around purity that become their own kind of corruption, or become needy when innocence is threatened."
    },
    'default': {
      correct: "You're designed to recognize genuine innocence—to see and protect what's still pure.",
      distorted: "When you're not yourself, innocence distorts into either naive denial or cynical destruction of purity.",
      behavioral: "You either refuse to see corruption or attack any claim to innocence."
    }
  }
};

// ============================================
// SPLIT DEFINITION PATTERNS
// How you need others to feel complete
// ============================================

interface SplitPattern {
  relational: string;
  experience: string;
  practical: string;
}

const SPLIT_PATTERNS: { [key: string]: SplitPattern } = {
  'Single': {
    relational: "You process internally and consistently. You don't need others to complete your thinking or feel whole.",
    experience: "You can feel quite self-sufficient, which can make it harder to understand why others seem so affected by who they're with.",
    practical: "Your consistency is a gift, but remember that others may need what you naturally have—a sense of internal completion."
  },
  'Split': {
    relational: "You're not designed to feel internally complete all the time. Certain people or environments bridge your internal gaps—that's why some interactions feel instantly 'click' while others feel off.",
    experience: "You may feel different parts of yourself operating independently. With the right bridging energy, suddenly everything connects.",
    practical: "Notice who and what bridges your split. These people and environments aren't luxuries—they're part of how you're designed to function."
  },
  'Triple Split': {
    relational: "Three parts of you operate independently. You need variety—different people and environments to activate different aspects of yourself.",
    experience: "You might feel like you contain multiple people. Integration takes time and requires diverse connections.",
    practical: "Don't try to integrate through isolation. You need busy environments with variety to feel all of yourself."
  },
  'Quadruple Split': {
    relational: "Four distinct parts of you function independently. Full integration is rare and requires just the right combination of energies.",
    experience: "You may feel highly compartmentalized, with different aspects of self emerging in different contexts.",
    practical: "Accept that feeling unified is unusual for you. Your design includes this multiplicity—it's not a problem to solve."
  },
  'None': {
    relational: "You have no fixed definition—you're designed to sample and reflect the energies around you, not operate consistently.",
    experience: "You feel completely different depending on who you're with. This isn't instability—it's your design.",
    practical: "Choose your environments carefully. You will reflect whatever you're around, so be around what's genuinely healthy."
  }
};

// ============================================
// TYPE × AUTHORITY MASTER PATTERNS
// Enhanced with channel integration awareness
// ============================================

interface TypeAuthorityMaster {
  corePattern: string;
  coreTension: string;
  blindSpot: string;
  edge: string;
  channelIntegration: string;
}

const TYPE_AUTHORITY_MASTER: { [key: string]: { [auth: string]: TypeAuthorityMaster } } = {
  'Manifestor': {
    'Emotional': {
      corePattern: "You are built to initiate—but your clarity doesn't come instantly. So you move, then understand after. The world expects decisive Manifestors, but your emotional process requires time you rarely give yourself.",
      coreTension: "You feel the urge to act now—but the truth isn't settled yet. The gap between impulse and clarity creates situations where you move before your emotional wave has revealed what's actually right.",
      blindSpot: "You think the issue is other people resisting you. Often, it's that you moved before your emotional wave had settled into real knowing.",
      edge: "When you inform AND wait for emotional clarity before committing, your impact lands cleanly and others feel included rather than blindsided.",
      channelIntegration: "Your channels express most purely when you've waited for emotional clarity before initiating through them."
    },
    'Splenic': {
      corePattern: "You're designed to initiate from instinct—a flash of knowing that doesn't repeat. Your power is in catching that moment and acting before thinking talks you out of it.",
      coreTension: "The hit comes once, quiet and clear. But the pressure to explain or justify makes you second-guess what your body already knew.",
      blindSpot: "You wait for certainty that already came and went. The first knowing was the answer—everything after is just noise.",
      edge: "When you trust the first hit and inform before moving, you navigate with precision others can't match.",
      channelIntegration: "Your channels fire with the first instinct—trust them in the moment or lose the clarity."
    },
    'Ego': {
      corePattern: "You move from will—genuine desire is your engine. When your heart is in it, you're unstoppable. When it's not, nothing moves.",
      coreTension: "You commit based on what you think you should want, then run out of fuel because the desire wasn't real.",
      blindSpot: "Broken promises aren't about discipline. They're about making commitments your heart never agreed to.",
      edge: "When you only commit to what you genuinely want, your follow-through becomes legendary.",
      channelIntegration: "Your channels carry power only when your will is genuinely engaged. Forcing them without desire burns you out."
    },
    'Self-Projected': {
      corePattern: "You initiate through expression. The direction becomes clear when you hear yourself speak it—not before.",
      coreTension: "You think you should know before speaking. But your clarity IS the speaking—talking IS your processing.",
      blindSpot: "Waiting for internal certainty that only comes through expression. Your voice is how you know, not after you know.",
      edge: "When you find trusted sounding boards and let yourself articulate before committing, your direction becomes clear.",
      channelIntegration: "Your channels express through voice. Talking about them reveals how to use them."
    },
    'None': {
      corePattern: "You initiate without a fixed internal compass—your clarity comes from environment, not introspection.",
      coreTension: "You keep looking inside for answers that live outside. The right setting reveals the right direction.",
      blindSpot: "Forcing decisions in wrong environments. Your wisdom is place-dependent.",
      edge: "When you choose environments wisely before initiating, the direction becomes self-evident.",
      channelIntegration: "Your channels respond to environment. Different places activate different aspects of your initiating power."
    }
  },
  
  'Generator': {
    'Emotional': {
      corePattern: "You have sustainable energy for what lights you up—but you don't know what that is until the emotional wave settles. Excitement isn't clarity; it's a data point.",
      coreTension: "Your gut responds instantly, but your emotional truth takes time. You're caught between the pull of response and the requirement of emotional process.",
      blindSpot: "You say yes in a high because the pull feels real—then wonder why you're frustrated when the wave passes and you're stuck with a commitment that no longer fits.",
      edge: "When you let your gut respond AND wait for emotional clarity before fully committing, you find sustainable engagement that doesn't turn to frustration.",
      channelIntegration: "Your channels carry sustained energy only when both gut response AND emotional clarity are present."
    },
    'Sacral': {
      corePattern: "Your body knows before your mind catches up. The pull toward or away happens in the moment—no analysis required, no waiting necessary.",
      coreTension: "You've learned to override your gut with logic. But every time you talk yourself into something your body said no to, you end up drained and frustrated.",
      blindSpot: "Ignoring the first response because it doesn't come with reasons. Your gut doesn't need to explain itself—the reasons come later or don't come at all.",
      edge: "When you trust the visceral response—even without understanding why—your energy stays sustainable and your satisfaction is real.",
      channelIntegration: "Your channels activate through gut response. Follow the pull, and your channels do what they're designed for."
    }
  },
  
  'Manifesting Generator': {
    'Emotional': {
      corePattern: "You move fast and pivot often—but your clarity comes slow. Part of you is already three steps ahead while another part needs to feel through whether those steps are real.",
      coreTension: "The excitement is immediate; the emotional truth unfolds over time. You start things in highs that look different when the wave passes.",
      blindSpot: "Speed without emotional settling creates false starts. You think you're being efficient, but you're actually wasting energy on commitments that won't hold.",
      edge: "When you sample quickly but commit slowly, you find the paths that actually go somewhere.",
      channelIntegration: "Your channels can pivot—but pivot from emotional clarity, not just excitement, and your efficiency becomes real."
    },
    'Sacral': {
      corePattern: "You respond instantly and multi-directionally. Multiple pulls at once, and your job is to follow the strongest one right now—then follow the next when it changes.",
      coreTension: "You're called inconsistent because you pivot before others understand why. But forcing yourself through dead tracks is what actually drains you.",
      blindSpot: "Guilt over not finishing what lost its energy. Completion for you isn't about the end—it's about extracting what was yours to take.",
      edge: "When you trust the pivot and let your body lead, you find efficiency others can't match.",
      channelIntegration: "Your channels express through rapid response. Follow the strongest pull through your channels, pivot when it's done."
    }
  },
  
  'Projector': {
    'Emotional': {
      corePattern: "You see deeply into systems and people—but you don't know what to do with that sight until the emotional wave settles. Your guidance needs time to clarify.",
      coreTension: "You're invited to guide, but your clarity isn't instant. The pressure to respond immediately leads to guidance that doesn't land.",
      blindSpot: "Giving advice in emotional peaks that you'd word differently in neutral. Recognition doesn't mean readiness—your emotional process still applies.",
      edge: "When you wait for emotional clarity before offering guidance, your insight transforms rather than deflects.",
      channelIntegration: "Your channels guide others—but guide from emotional clarity, and your insight becomes genuinely transformative."
    },
    'Splenic': {
      corePattern: "You see what others miss—and you know it in a flash. The insight is subtle, once, and gone if you don't catch it.",
      coreTension: "Your insight is instant, but recognition doesn't always come at the same speed. You see the answer before anyone asks.",
      blindSpot: "Waiting to be asked when you already know. Sometimes the knowing fades while you wait for the invitation that would make it land.",
      edge: "When recognition and intuition align, your guidance has precision that cuts through noise.",
      channelIntegration: "Your channels perceive instantly. Trust the first insight through them—it won't repeat."
    },
    'Self-Projected': {
      corePattern: "You understand others by talking through what you see. Your voice reveals your knowing—to yourself and to them simultaneously.",
      coreTension: "You hold back insight because you're not sure it's right—but speaking is how you'd know.",
      blindSpot: "Waiting for internal certainty that only comes through expression. Your clarity lives in your voice, not before it.",
      edge: "When you're invited and you speak, the truth emerges for everyone—including you.",
      channelIntegration: "Your channels guide through expression. Talking about what you see makes it clear."
    },
    'Ego': {
      corePattern: "You guide from genuine desire. When your heart is in the invitation, your impact is undeniable.",
      coreTension: "You accept invitations based on should rather than want, then run out of energy because desire wasn't there.",
      blindSpot: "Bitterness from giving to people your heart never chose. Your will only sustains what it wants.",
      edge: "When you only accept invitations that genuinely excite you, your guidance has staying power.",
      channelIntegration: "Your channels guide powerfully—but only when your heart is genuinely in the invitation."
    },
    'Mental': {
      corePattern: "Your insight comes through environment and conversation. You process others' questions by bouncing them off different perspectives and places.",
      coreTension: "You try to guide from your head alone, but clarity only comes when you've discussed it in the right setting with the right people.",
      blindSpot: "Forcing answers in wrong environments. Your wisdom is context-dependent—some settings clarify, others cloud.",
      edge: "When you guide from environments that support your thinking, your insight becomes unusually clear.",
      channelIntegration: "Your channels require the right environment to see clearly through them."
    },
    'None': {
      corePattern: "You see into others deeply, but your own clarity depends on where you are and who you're with.",
      coreTension: "Looking inside for direction when the answers live in your surroundings.",
      blindSpot: "Trying to be consistent when your wisdom genuinely shifts with place and people.",
      edge: "When you choose your environments wisely, the guidance you offer becomes precisely attuned.",
      channelIntegration: "Your channels guide differently depending on environment. Different settings, different clarity."
    }
  },
  
  'Reflector': {
    'Lunar': {
      corePattern: "You take in everything—and you need time to know what's actually yours. A full cycle reveals what stays true regardless of who you've been around.",
      coreTension: "The world rushes you. But your clarity unfolds over 28 days, not 28 minutes. Pressure to decide faster than your rhythm allows leads to decisions that don't hold.",
      blindSpot: "Making decisions from one day's reflection. You need the whole cycle to see clearly—what felt true Monday may reverse by Friday, then reverse again.",
      edge: "When you give yourself a full lunar cycle, you access wisdom that faster types can't reach. Your perspective IS the perspective of time.",
      channelIntegration: "Your channels sample and reflect. Over a full cycle, you see how they actually operate rather than how they seemed in one moment."
    }
  }
};

// ============================================
// MASTER SYNTHESIS GENERATOR
// ============================================

export function generateHDSynthesis(input: HDSynthesisInput): HDSynthesis | null {
  const { 
    type, 
    authority, 
    profile, 
    definition,
    incarnationCross,
    channels,
    definedCenters,
    undefinedCenters,
    consciousGates,
    unconsciousGates,
    personalitySun,
    designSun,
    personalityEarth,
    designEarth,
    environment,
    motivation,
    transference
  } = input;
  
  if (!type || !authority) {
    return null;
  }
  
  // Get Type × Authority master pattern
  const typeAuthority = TYPE_AUTHORITY_MASTER[type]?.[authority] || 
                        TYPE_AUTHORITY_MASTER[type]?.['Emotional'] ||
                        generateFallbackTypeAuthority(type, authority);
  
  // ============================================
  // CORE PATTERN - Integrate channels + cross + conscious/unconscious
  // ============================================
  let corePattern = typeAuthority.corePattern;
  
  // Add channel narrative if channels exist
  if (channels && channels.length > 0) {
    const primaryChannel = channels[0];
    const channelKey = identifyChannel(primaryChannel);
    if (channelKey && CHANNEL_NARRATIVES[channelKey]) {
      corePattern += ` ${CHANNEL_NARRATIVES[channelKey].livedTheme}`;
    }
  }
  
  // Add cross narrative if available
  if (incarnationCross) {
    const crossKey = identifyCross(incarnationCross);
    if (crossKey && CROSS_NARRATIVES[crossKey]) {
      corePattern += ` ${CROSS_NARRATIVES[crossKey].livedBehavior}`;
    }
  }
  
  // ============================================
  // CORE TENSION - Type/Authority + Motivation/Transference + Profile
  // ============================================
  let coreTension = typeAuthority.coreTension;
  
  // Add motivation → transference distortion
  if (motivation && transference) {
    const motTrans = MOTIVATION_TRANSFERENCE[motivation.toLowerCase()]?.[transference.toLowerCase()];
    if (motTrans) {
      coreTension += ` ${motTrans.distorted}`;
    }
  } else if (motivation) {
    const motDefault = MOTIVATION_TRANSFERENCE[motivation.toLowerCase()]?.['default'];
    if (motDefault) {
      coreTension += ` ${motDefault.distorted}`;
    }
  }
  
  // Add split definition tension
  if (definition && definition !== 'Single') {
    const splitPattern = SPLIT_PATTERNS[definition];
    if (splitPattern) {
      coreTension += ` And because you have ${definition} Definition: ${splitPattern.relational.toLowerCase()}`;
    }
  }
  
  // ============================================
  // HOW THIS PLAYS OUT - Multi-dimensional patterns
  // ============================================
  const howThisPlaysOut = generateHowThisPlaysOut(
    type, authority, profile, definition,
    channels, consciousGates, unconsciousGates,
    environment, motivation, transference
  );
  
  // ============================================
  // BLIND SPOT - Unconscious + Motivation distortion
  // ============================================
  let blindSpot = typeAuthority.blindSpot;
  
  // Add conscious/unconscious dynamic
  if (consciousGates && unconsciousGates && profile) {
    const consciousUnconscious = getConsciousUnconsciousPattern(
      consciousGates, unconsciousGates, profile, personalitySun, designSun
    );
    blindSpot += ` ${consciousUnconscious.blindSpot}`;
  }
  
  // Add motivation → transference behavioral blind spot
  if (motivation && transference) {
    const motTrans = MOTIVATION_TRANSFERENCE[motivation.toLowerCase()]?.[transference.toLowerCase()];
    if (motTrans) {
      blindSpot += ` When you're off: ${motTrans.behavioral.toLowerCase()}`;
    }
  }
  
  // ============================================
  // EDGE - Authority + Environment + Channels aligned
  // ============================================
  let edge = typeAuthority.edge;
  
  // Add environment optimal if available
  if (environment) {
    const envPattern = ENVIRONMENT_PATTERNS[environment.toLowerCase()];
    if (envPattern) {
      edge += ` ${envPattern.optimal}`;
    }
  }
  
  // Add channel genius if available
  if (channels && channels.length > 0) {
    const primaryChannel = channels[0];
    const channelKey = identifyChannel(primaryChannel);
    if (channelKey && CHANNEL_NARRATIVES[channelKey]) {
      edge += ` ${CHANNEL_NARRATIVES[channelKey].genius}`;
    }
  }
  
  // ============================================
  // WHAT SUPPORTS YOU - Environment + Pacing + Relational + Clarity
  // ============================================
  const whatSupportsYou = generateWhatSupportsYou(
    type, authority, profile, definition,
    environment, channels, undefinedCenters
  );
  
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
// HELPER: Identify channel from data
// ============================================
function identifyChannel(channel: ChannelData): string | null {
  // Try to match by gates string or centers
  const gates = channel.gates?.toLowerCase() || '';
  const centers = channel.centers || [];
  
  // Direct gate matching
  if (gates.includes('35') && gates.includes('36')) return '35-36';
  if (gates.includes('12') && gates.includes('22')) return '12-22';
  if (gates.includes('21') && gates.includes('45')) return '21-45';
  if (gates.includes('37') && gates.includes('40')) return '37-40';
  if (gates.includes('6') && gates.includes('59')) return '6-59';
  if (gates.includes('63') && gates.includes('4')) return '63-4';
  if (gates.includes('17') && gates.includes('62')) return '17-62';
  if (gates.includes('18') && gates.includes('58')) return '18-58';
  if (gates.includes('28') && gates.includes('38')) return '28-38';
  if (gates.includes('57') && gates.includes('34')) return '57-34';
  if (gates.includes('57') && gates.includes('10')) return '57-10';
  if (gates.includes('61') && gates.includes('24')) return '61-24';
  if (gates.includes('51') && gates.includes('25')) return '51-25';
  if (gates.includes('43') && gates.includes('23')) return '43-23';
  if (gates.includes('8') && gates.includes('1')) return '8-1';
  if (gates.includes('2') && gates.includes('14')) return '2-14';
  if (gates.includes('26') && gates.includes('44')) return '26-44';
  
  // Center-based fallback
  if (centers.includes('Throat') && centers.includes('Solar Plexus')) return '12-22';
  if (centers.includes('Solar Plexus') && centers.includes('Sacral')) return '6-59';
  if (centers.includes('Throat') && centers.includes('G')) return '8-1';
  if (centers.includes('Throat') && centers.includes('Ego')) return '21-45';
  
  return null;
}

// ============================================
// HELPER: Identify cross from name
// ============================================
function identifyCross(crossName: string): string | null {
  const name = crossName.toLowerCase();
  
  if (name.includes('migration')) return 'migration';
  if (name.includes('service')) return 'service';
  if (name.includes('planning')) return 'planning';
  if (name.includes('explanation')) return 'explanation';
  if (name.includes('consciousness')) return 'consciousness';
  if (name.includes('eden')) return 'eden';
  if (name.includes('vessel of love') || name.includes('love')) return 'vessel of love';
  if (name.includes('tension')) return 'tension';
  if (name.includes('four ways')) return 'the four ways';
  if (name.includes('unexpected')) return 'the unexpected';
  if (name.includes('rulership')) return 'rulership';
  if (name.includes('sphinx')) return 'the sphinx';
  if (name.includes('penetration')) return 'penetration';
  
  return null;
}

// ============================================
// HELPER: Generate How This Plays Out
// ============================================
function generateHowThisPlaysOut(
  type: string,
  authority: string,
  profile: string,
  definition?: string,
  channels?: ChannelData[],
  consciousGates?: number[],
  unconsciousGates?: number[],
  environment?: string,
  motivation?: string,
  transference?: string
): string[] {
  const patterns: string[] = [];
  
  // Type × Authority behavioral patterns
  if (type === 'Manifestor' && authority === 'Emotional') {
    patterns.push("You make a decision, then question it later when the wave passes");
    patterns.push("People expect certainty from you before you feel it");
  } else if (type === 'Manifestor' && authority === 'Splenic') {
    patterns.push("You act on instinct, then watch others struggle to keep up");
    patterns.push("Hesitation costs you the clarity that was already there");
  } else if (type === 'Generator' && authority === 'Emotional') {
    patterns.push("You say yes in excitement, then feel trapped when the wave passes");
    patterns.push("Frustration builds when you commit before the feeling settles");
  } else if (type === 'Generator' && authority === 'Sacral') {
    patterns.push("Your body says yes or no before your mind catches up");
    patterns.push("Energy flows when you follow response; drains when you force");
  } else if (type === 'Manifesting Generator') {
    patterns.push("You start things fast, then discover whether they're right later");
    patterns.push("What looks like quitting is often your body finding the real path");
  } else if (type === 'Projector') {
    patterns.push("You see what others miss—and feel unseen when no one asks");
    patterns.push("Your guidance transforms when invited; falls flat when offered freely");
  } else if (type === 'Reflector') {
    patterns.push("You feel completely different depending on who you're with");
    patterns.push("Fast decisions rarely survive the full cycle");
  }
  
  // Conscious/Unconscious pattern
  if (consciousGates && unconsciousGates && consciousGates.length > 0 && unconsciousGates.length > 0) {
    patterns.push("Your mind explains decisions your body has already made");
  }
  
  // Channel behavioral pattern
  if (channels && channels.length > 0) {
    const channelKey = identifyChannel(channels[0]);
    if (channelKey && CHANNEL_NARRATIVES[channelKey]) {
      patterns.push(CHANNEL_NARRATIVES[channelKey].behavioralPattern.charAt(0).toUpperCase() + 
                   CHANNEL_NARRATIVES[channelKey].behavioralPattern.slice(1));
    }
  }
  
  // Profile patterns
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
  
  // Split definition relational pattern
  if (definition === 'Split') {
    patterns.push("You feel more complete around certain people—that's not dependency, it's design");
  } else if (definition?.includes('Triple') || definition?.includes('Quadruple')) {
    patterns.push("Different parts of you come online in different contexts—integration takes time and variety");
  }
  
  // Environment pattern
  if (environment) {
    const envPattern = ENVIRONMENT_PATTERNS[environment.toLowerCase()];
    if (envPattern) {
      patterns.push(envPattern.distortion);
    }
  }
  
  // Motivation/Transference pattern
  if (motivation && transference) {
    const motTrans = MOTIVATION_TRANSFERENCE[motivation.toLowerCase()]?.[transference.toLowerCase()];
    if (motTrans) {
      patterns.push(motTrans.behavioral);
    }
  }
  
  return patterns.slice(0, 6); // Max 6 patterns for depth without overwhelm
}

// ============================================
// HELPER: Generate What Supports You
// ============================================
function generateWhatSupportsYou(
  type: string,
  authority: string,
  profile: string,
  definition?: string,
  environment?: string,
  channels?: ChannelData[],
  undefinedCenters?: string[]
): string[] {
  const supports: string[] = [];
  
  // Authority-based support
  if (authority === 'Emotional') {
    supports.push("Time between impulse and commitment—never decide in the peak or valley");
    supports.push("People who don't rush your clarity");
  } else if (authority === 'Sacral') {
    supports.push("Yes/no questions that let your gut respond in the moment");
    supports.push("Space to respond rather than initiate or explain");
  } else if (authority === 'Splenic') {
    supports.push("Environments where you can act on instinct without second-guessing");
    supports.push("Trust in the first knowing, even without reasons");
  } else if (authority === 'Ego') {
    supports.push("Commitments that genuinely excite you—not ones you think you should want");
    supports.push("Freedom to follow desire without guilt");
  } else if (authority === 'Self-Projected') {
    supports.push("Sounding boards who listen without directing");
    supports.push("Permission to talk things through before deciding");
  } else if (authority === 'Mental' || authority === 'None') {
    supports.push("Multiple perspectives and environments before major decisions");
    supports.push("Time to discuss in different settings");
  } else if (authority === 'Lunar') {
    supports.push("A full 28-day cycle before major decisions—no rushing");
    supports.push("Understanding that your clarity unfolds over time");
  }
  
  // Environment support
  if (environment) {
    const envPattern = ENVIRONMENT_PATTERNS[environment.toLowerCase()];
    if (envPattern) {
      supports.push(envPattern.practical);
    }
  }
  
  // Type-based support
  if (type === 'Manifestor') {
    supports.push("Environments with movement and information flow");
    supports.push("Relationships that don't require constant explanation");
  } else if (type === 'Generator' || type === 'Manifesting Generator') {
    supports.push("Work that lights you up rather than drains you");
    supports.push("Freedom to follow your response without justification");
  } else if (type === 'Projector') {
    supports.push("Invitations to share your insight—recognition before contribution");
    supports.push("Rest without guilt—your energy works differently");
  } else if (type === 'Reflector') {
    supports.push("Genuinely healthy environments—you will reflect whatever you're around");
    supports.push("People who understand your lunar rhythm");
  }
  
  // Split definition support
  if (definition === 'Split') {
    supports.push("People or places that bridge your energy without you trying");
  } else if (definition?.includes('Triple') || definition?.includes('Quadruple')) {
    supports.push("Busy environments with variety of energy and people");
  }
  
  // Profile-based support
  const firstLine = profile?.split('/')[0];
  if (firstLine === '1') {
    supports.push("Time to build foundations before being pushed to act");
  } else if (firstLine === '2') {
    supports.push("Alone time to develop what comes naturally—your gifts emerge when called");
  } else if (firstLine === '4') {
    supports.push("Close relationships where opportunities emerge organically");
  }
  
  // Undefined center wisdom
  if (undefinedCenters && undefinedCenters.length > 0) {
    if (undefinedCenters.some(c => c.toLowerCase().includes('sacral'))) {
      supports.push("Permission to stop before exhaustion—you don't have sustainable energy for everything");
    }
    if (undefinedCenters.some(c => c.toLowerCase().includes('root'))) {
      supports.push("Release from artificial urgency—not everything is actually urgent");
    }
    if (undefinedCenters.some(c => c.toLowerCase().includes('heart') || c.toLowerCase().includes('ego'))) {
      supports.push("Freedom from proving your worth—you don't need to earn your place");
    }
  }
  
  return supports.slice(0, 6); // Max 6 for actionability
}

// ============================================
// FALLBACK: Generate basic type/authority pattern
// ============================================
function generateFallbackTypeAuthority(type: string, authority: string): TypeAuthorityMaster {
  let corePattern = '';
  let coreTension = '';
  let blindSpot = '';
  let edge = '';
  
  // Generate based on type
  if (type === 'Generator') {
    corePattern = "You have sustainable energy for what genuinely excites you—the work is learning to tell the difference between real response and mental override.";
    coreTension = "Your gut knows instantly, but conditioning has taught you to override it with logic. Every override leads to frustration.";
    blindSpot = "Ignoring the first response because it doesn't come with reasons. Your gut doesn't need to explain itself.";
    edge = "When you trust the visceral response—even without understanding why—your energy stays sustainable and your satisfaction is real.";
  } else if (type === 'Manifesting Generator') {
    corePattern = "You move fast and in multiple directions—your efficiency comes from following response, not from forcing completion.";
    coreTension = "You're called inconsistent because you pivot. But forcing yourself through dead tracks is what actually drains you.";
    blindSpot = "Guilt over 'not finishing' when the energy was done—staying out of obligation rather than response.";
    edge = "When you trust the pivot and let your body lead, you find efficiency others can't match.";
  } else if (type === 'Projector') {
    corePattern = "You see what others miss—and your insight transforms when it's genuinely invited, not just offered.";
    coreTension = "You see so clearly, but sharing without invitation leads to bitterness, not impact.";
    blindSpot = "Offering guidance because you can see the solution, not because anyone asked for it.";
    edge = "When truly invited, your ability to see into systems and people becomes your most valuable gift.";
  } else if (type === 'Manifestor') {
    corePattern = "You're built to initiate what doesn't exist yet—the work is learning to inform before you move.";
    coreTension = "The urge to act meets the resistance of others unprepared for your movement.";
    blindSpot = "Acting without informing, then resenting the pushback.";
    edge = "When you inform before acting, your initiating power flows without the friction of surprise.";
  } else if (type === 'Reflector') {
    corePattern = "You take in everything around you—the work is learning what's yours and what's borrowed.";
    coreTension = "The world rushes you, but your clarity needs a full lunar cycle to emerge.";
    blindSpot = "Making decisions from one moment's reflection when you need the whole cycle.";
    edge = "When you give yourself time, you access wisdom that faster types can't reach.";
  } else {
    corePattern = "Your design has a unique rhythm—the work is learning to trust it.";
    coreTension = "Conditioning pushes you toward patterns that don't fit. The friction is information.";
    blindSpot = "Trying to operate like others when your design asks for something different.";
    edge = "When you trust your natural rhythm, everything flows more easily.";
  }
  
  return {
    corePattern,
    coreTension,
    blindSpot,
    edge,
    channelIntegration: "Your channels express most purely when you follow your natural process."
  };
}

// ============================================
// CHECK IF SYNTHESIS IS AVAILABLE
// ============================================
export function canGenerateSynthesis(type: string, authority: string): boolean {
  return !!(type && authority);
}
