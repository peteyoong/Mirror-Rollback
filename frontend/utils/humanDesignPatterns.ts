// ============================================
// HUMAN DESIGN PATTERN COMPRESSION LAYER
// ============================================
// Transforms descriptive HD content into tension-based pattern recognition
// Matches the Intelligence Layer approach used in Astrology

// ============================================
// TYPE PATTERNS - Core behavioral tensions
// ============================================

interface TypePattern {
  compressedPatternLine: string;
  facetLine: string;
  tensionLine: string;
  geniusLine: string;
  
  // Timing variants
  today: {
    immediate: string;
    watchFor: string;
    question: string;
  };
  week: {
    pattern: string;
    friction: string;
    question: string;
  };
  month: {
    arc: string;
    trap: string;
    question: string;
  };
}

export const TYPE_PATTERNS: { [key: string]: TypePattern } = {
  'Generator': {
    compressedPatternLine: "You wait for the pull—but sometimes your mind commits before your gut has spoken.",
    facetLine: "This shows up most in decisions and work, where frustration signals you said yes to the wrong thing.",
    tensionLine: "When you override your gut response, you end up carrying obligations that drain rather than energize.",
    geniusLine: "When you follow genuine excitement, you have sustainable energy that builds and builds.",
    
    today: {
      immediate: "Something may be pulling at your attention. Notice if it's your gut responding—or your mind rationalizing.",
      watchFor: "Saying yes out of obligation when your body says nothing.",
      question: "What genuinely excited me today—not what I thought I should be excited about?"
    },
    week: {
      pattern: "Notice where your energy keeps building versus where it keeps draining. The pattern reveals what your gut actually wants.",
      friction: "The frustration building may be from accumulated yes-es that weren't real.",
      question: "Where have I been giving energy to things my gut never agreed to?"
    },
    month: {
      arc: "This month is teaching you the difference between what you think you want and what your body actually responds to.",
      trap: "Staying in situations long after your gut went quiet—waiting for it to change.",
      question: "What would shift if I trusted my gut response was the final answer?"
    }
  },
  
  'Manifesting Generator': {
    compressedPatternLine: "You move toward new experiences quickly—but sometimes before you've fully processed the last one.",
    facetLine: "This shows up in work and decisions, where you start fast but may struggle to finish what no longer excites you.",
    tensionLine: "When you force yourself to complete what's lost its spark, your energy scatters and frustration builds.",
    geniusLine: "When you follow the pivot, you find efficiency others can't match—skipping steps that weren't necessary anyway.",
    
    today: {
      immediate: "Multiple things may be calling you at once. Your job isn't to pick one—it's to notice which one your body responds to most strongly right now.",
      watchFor: "Starting something new just because you can, without checking if your gut is actually in it.",
      question: "What is my energy actually drawn to—not what my mind says I should finish?"
    },
    week: {
      pattern: "Notice which excitement survives the initial spark. What keeps calling you back after the novelty fades?",
      friction: "Forcing yourself to finish what lost its energy—this creates scattered attention, not completion.",
      question: "What started this week that still has juice? What's ready to be released?"
    },
    month: {
      arc: "This month is revealing your relationship with completion. Real completion isn't finishing everything—it's knowing when you've extracted what was yours to take.",
      trap: "Guilt over 'not finishing' when the energy was done—staying out of obligation rather than response.",
      question: "What if pivoting isn't quitting—it's efficiency?"
    }
  },
  
  'Projector': {
    compressedPatternLine: "You see what others miss—but sharing that insight without being invited often leaves you feeling unseen.",
    facetLine: "This shows up most in relationships and work, where your guidance lands when recognized and falls flat when offered freely.",
    tensionLine: "When you give wisdom that wasn't requested, you deplete yourself and get bitterness instead of impact.",
    geniusLine: "When truly invited, your ability to see into systems and people becomes your most valuable gift.",
    
    today: {
      immediate: "You may see something clearly that others are missing. The question isn't whether you're right—it's whether you've been asked.",
      watchFor: "Offering guidance because you can see the solution, not because anyone asked for it.",
      question: "Where was I truly seen today—and where did I give without being invited?"
    },
    week: {
      pattern: "Notice where your insights land and where they don't. The difference usually isn't about the insight—it's about whether you were recognized first.",
      friction: "Giving too much to people who don't really see you. The energy drain isn't from the guidance—it's from the lack of recognition.",
      question: "Who actually sees me for what I offer? Who am I trying to convince?"
    },
    month: {
      arc: "This month is teaching you that your value doesn't depend on being used. Rest, study, and wait—your invitation will come.",
      trap: "Working harder to be seen rather than letting recognition find you.",
      question: "What if waiting isn't passive—it's strategic positioning?"
    }
  },
  
  'Manifestor': {
    compressedPatternLine: "You initiate what others can't imagine—but acting without informing creates the resistance you're trying to avoid.",
    facetLine: "This shows up in relationships and work, where informing creates flow and silence creates pushback.",
    tensionLine: "When you act without warning, others feel blindsided—even when your impulse was right.",
    geniusLine: "When you inform before moving, you clear resistance and your initiating power flows without friction.",
    
    today: {
      immediate: "Something may be ready to start. The urge to act is real—but so is the need to let others know what's coming.",
      watchFor: "Acting from impulse and dealing with resistance later instead of informing now.",
      question: "What wanted to be initiated today—and who needed to know before I moved?"
    },
    week: {
      pattern: "Notice where resistance keeps appearing. It may not be about your direction—it may be about how you're moving without warning.",
      friction: "The peace you want comes from informing, not from doing it your way and hoping others adjust.",
      question: "Where has not informing created friction that informing could have prevented?"
    },
    month: {
      arc: "This month is teaching you that your power isn't diminished by including others—it's amplified when you clear the path first.",
      trap: "Resenting others' reactions when you didn't give them a chance to prepare.",
      question: "What if informing isn't asking permission—it's removing obstacles?"
    }
  },
  
  'Reflector': {
    compressedPatternLine: "You experience everything around you deeply—but sometimes take on energies and identities that aren't yours.",
    facetLine: "This shows up in relationships and energy, where your environment shapes you more than you realize.",
    tensionLine: "When you decide too quickly or stay in the wrong environment, you lose yourself in reflections that distort.",
    geniusLine: "When you give yourself a full cycle and choose environments wisely, your wisdom about what's healthy becomes unmatched.",
    
    today: {
      immediate: "How you feel today is largely shaped by where you are and who you're with. Notice, but don't identify with it too strongly.",
      watchFor: "Mistaking others' energy for your own—what you're feeling may not be yours.",
      question: "What am I reflecting from my environment—and what is actually mine?"
    },
    week: {
      pattern: "Watch how you shift across different environments and people. The places that consistently feel good are telling you something important.",
      friction: "Absorbing the wrong environments repeatedly—your sensitivity is a gift when you choose where to apply it.",
      question: "Which environments kept feeling right this week? Which felt draining?"
    },
    month: {
      arc: "This lunar cycle is showing you what's consistently true about you versus what shifts with your surroundings. Both are real—but only one is yours.",
      trap: "Making major decisions before a full cycle has passed—your clarity unfolds over time, not in moments.",
      question: "What has remained true throughout this cycle, regardless of where I was?"
    }
  }
};

// ============================================
// AUTHORITY PATTERNS - Decision-making tensions
// ============================================

interface AuthorityPattern {
  compressedPatternLine: string;
  facetLine: string;
  tensionLine: string;
  geniusLine: string;
  timingModifier: {
    today: string;
    week: string;
    month: string;
  };
}

export const AUTHORITY_PATTERNS: { [key: string]: AuthorityPattern } = {
  'Emotional': {
    compressedPatternLine: "Your clarity comes in waves—but you often try to decide in the peak or valley instead of waiting for calm.",
    facetLine: "This affects every major decision. Excitement isn't clarity. Frustration isn't clarity. The flat line between them is.",
    tensionLine: "When you decide in emotional extremes, you commit to things that looked different when the wave passed.",
    geniusLine: "When you ride the full wave before committing, your decisions have a depth that snap judgments can't match.",
    timingModifier: {
      today: "You may feel pressure to decide. That pressure isn't clarity—it's the wave moving. Sleep on it.",
      week: "Notice how the same situation feels different day to day. The truth is in the pattern, not the peaks.",
      month: "Real clarity this month will come slowly. What still feels right after the wave has moved is yours to trust."
    }
  },
  
  'Sacral': {
    compressedPatternLine: "Your gut knows instantly—but your mind keeps asking for reasons it can't give.",
    facetLine: "This shows up in decisions and work, where following the uh-huh creates energy and overriding it creates frustration.",
    tensionLine: "When you rationalize past your gut's no, you end up in commitments your body never agreed to.",
    geniusLine: "When you trust the visceral response—even without understanding why—your energy stays sustainable.",
    timingModifier: {
      today: "Something may be asking for your energy. Notice your body's first response before your mind explains it away.",
      week: "Your gut has been responding all week. Notice which responses you followed and which you overrode—there's your lesson.",
      month: "This month is teaching you to trust the sound before the reason. Your gut doesn't need to explain itself."
    }
  },
  
  'Splenic': {
    compressedPatternLine: "Your intuition speaks once, quietly, in the moment—but if you hesitate, you miss it.",
    facetLine: "This affects decisions where survival and timing matter. The knowing is instant, not reasoned.",
    tensionLine: "When you second-guess the first hit, you lose access to an intelligence that doesn't repeat itself.",
    geniusLine: "When you learn to catch that subtle knowing, you navigate with a precision others can't match.",
    timingModifier: {
      today: "A quiet knowing may arrive—once. It won't argue, repeat, or explain. Learn to catch it.",
      week: "Notice which moments this week felt like a subtle 'yes' or 'no' in your body. Those were real.",
      month: "This month is training your attention. The more you notice the quiet voice, the louder it seems."
    }
  },
  
  'Ego': {
    compressedPatternLine: "You know what you want—but sometimes commit to things your heart isn't actually in.",
    facetLine: "This shows up in work and decisions, where willpower sustains what the heart chose and depletes what it didn't.",
    tensionLine: "When you commit without genuine desire, willpower runs out and promises break.",
    geniusLine: "When you only commit to what you truly want, your follow-through becomes unstoppable.",
    timingModifier: {
      today: "Ask yourself simply: Do I want this? If the answer isn't a clear yes, the energy won't sustain.",
      week: "Notice which commitments still have energy and which feel like obligations. Your heart is telling you something.",
      month: "This month is clarifying what you actually want versus what you think you should want."
    }
  },
  
  'Self-Projected': {
    compressedPatternLine: "You find clarity by hearing yourself speak—but sometimes you talk without listening to what you're saying.",
    facetLine: "This affects decisions, where talking it through reveals what thinking alone cannot.",
    tensionLine: "When you decide in your head without speaking, you miss the intelligence that only emerges in expression.",
    geniusLine: "When you find trusted sounding boards and actually listen to yourself, clarity appears in your own voice.",
    timingModifier: {
      today: "If you're unclear, find someone to talk to. Not for their advice—but to hear your own voice.",
      week: "Notice which conversations this week led to clarity. Those people are your sounding boards.",
      month: "This month, your truth is trying to speak through you. Give it more opportunities to be heard."
    }
  },
  
  'Mental': {
    compressedPatternLine: "You need environment and conversation to find clarity—but sometimes make decisions in isolation.",
    facetLine: "This affects all major decisions, where the right setting and people reveal what thinking alone cannot.",
    tensionLine: "When you decide alone or in the wrong environment, clarity stays elusive.",
    geniusLine: "When you find the right places and people to process with, your decisions carry unusual wisdom.",
    timingModifier: {
      today: "Your clarity today depends partly on where you are. Notice which environments help you think clearly.",
      week: "This week, try discussing the same decision in different settings. Notice where thinking feels clearer.",
      month: "This month is teaching you which people and places support your clarity. That data is valuable."
    }
  },
  
  'Lunar': {
    compressedPatternLine: "Your clarity unfolds over a full moon cycle—but you keep trying to decide in days.",
    facetLine: "This affects every major decision, where rushing produces confusion and waiting produces wisdom.",
    tensionLine: "When you decide too fast, you commit to something you didn't fully understand.",
    geniusLine: "When you give yourself a full cycle, you access a perspective on life that others can't achieve.",
    timingModifier: {
      today: "Today's perspective is just one data point. Don't mistake it for the full picture.",
      week: "You're partway through a cycle. Notice how different this week feels from last week on the same question.",
      month: "This is your natural rhythm. By month's end, you may have clarity you couldn't have accessed faster."
    }
  },
  
  'None': {
    compressedPatternLine: "You're designed to rely on environment rather than internal signals—but sometimes forget how much place matters.",
    facetLine: "This affects decisions and energy, where the right environment reveals the right answer.",
    tensionLine: "When you stay in wrong environments too long, clarity remains elusive.",
    geniusLine: "When you choose environments wisely, answers that seemed complex become simple.",
    timingModifier: {
      today: "Where you are today is shaping how clear you feel. Notice it.",
      week: "This week, pay attention to which environments help you think and which cloud your judgment.",
      month: "This month is teaching you that you're not broken—you just need the right setting."
    }
  }
};

// ============================================
// TIMING LAYER INTEGRATION
// ============================================
// Combines Type + Authority for timeframe-specific content

export interface HDTimingContent {
  bestUse: string;
  watchFor: string;
  reflectionPrompt: string;
}

export interface HDWeekContent {
  theme: string;
  frictionPattern: string;
  reflectionPrompt: string;
}

export interface HDMonthContent {
  theme: string;
  commonTrap: string;
  reflectionPrompt: string;
}

export const getHDTodayContent = (
  type: string,
  authority: string,
  hasTransitSignal: boolean,
  dominantSignal?: { today?: string }
): HDTimingContent => {
  // If we have real transit signals, use them with authority modifier
  if (hasTransitSignal && dominantSignal?.today) {
    const authorityPattern = AUTHORITY_PATTERNS[authority];
    const authorityMod = authorityPattern?.timingModifier.today || '';
    
    return {
      bestUse: dominantSignal.today,
      watchFor: authorityMod,
      reflectionPrompt: TYPE_PATTERNS[type]?.today.question || "What showed up today?"
    };
  }
  
  // Fallback to type + authority patterns
  const typePattern = TYPE_PATTERNS[type] || TYPE_PATTERNS['Generator'];
  const authorityPattern = AUTHORITY_PATTERNS[authority];
  
  // Combine authority modifier with type content for richer experience
  let bestUse = typePattern.today.immediate;
  if (authorityPattern) {
    bestUse = `${bestUse} ${authorityPattern.timingModifier.today}`;
  }
  
  return {
    bestUse,
    watchFor: typePattern.today.watchFor,
    reflectionPrompt: typePattern.today.question
  };
};

export const getHDWeekContent = (
  type: string,
  authority: string,
  hasTransitSignal: boolean,
  dominantSignal?: { week?: string }
): HDWeekContent => {
  if (hasTransitSignal && dominantSignal?.week) {
    const authorityPattern = AUTHORITY_PATTERNS[authority];
    
    return {
      theme: dominantSignal.week,
      frictionPattern: authorityPattern?.timingModifier.week || '',
      reflectionPrompt: TYPE_PATTERNS[type]?.week.question || "What pattern emerged this week?"
    };
  }
  
  const typePattern = TYPE_PATTERNS[type] || TYPE_PATTERNS['Generator'];
  const authorityPattern = AUTHORITY_PATTERNS[authority];
  
  let theme = typePattern.week.pattern;
  if (authorityPattern) {
    theme = `${theme} ${authorityPattern.timingModifier.week}`;
  }
  
  return {
    theme,
    frictionPattern: typePattern.week.friction,
    reflectionPrompt: typePattern.week.question
  };
};

export const getHDMonthContent = (
  type: string,
  authority: string,
  hasTransitSignal: boolean,
  dominantSignal?: { month?: string }
): HDMonthContent => {
  if (hasTransitSignal && dominantSignal?.month) {
    const authorityPattern = AUTHORITY_PATTERNS[authority];
    
    return {
      theme: dominantSignal.month,
      commonTrap: authorityPattern?.timingModifier.month || '',
      reflectionPrompt: TYPE_PATTERNS[type]?.month.question || "What is this month teaching you?"
    };
  }
  
  const typePattern = TYPE_PATTERNS[type] || TYPE_PATTERNS['Generator'];
  const authorityPattern = AUTHORITY_PATTERNS[authority];
  
  let theme = typePattern.month.arc;
  if (authorityPattern) {
    theme = `${theme} ${authorityPattern.timingModifier.month}`;
  }
  
  return {
    theme,
    commonTrap: typePattern.month.trap,
    reflectionPrompt: typePattern.month.question
  };
};

// ============================================
// PATTERN SYNTHESIS
// ============================================
// Creates the unified pattern view for a user's design

export interface HDPatternSynthesis {
  corePatternLine: string;
  typePattern: TypePattern;
  authorityPattern: AuthorityPattern;
  combinedTensionLine: string;
  combinedGeniusLine: string;
}

export const synthesizeHDPattern = (type: string, authority: string): HDPatternSynthesis => {
  const typePattern = TYPE_PATTERNS[type] || TYPE_PATTERNS['Generator'];
  const authorityPattern = AUTHORITY_PATTERNS[authority] || AUTHORITY_PATTERNS['Sacral'];
  
  // Create a combined core pattern that weaves type and authority together
  const corePatternLine = `${typePattern.compressedPatternLine.replace(/\.$/, '')}—and ${authorityPattern.compressedPatternLine.charAt(0).toLowerCase()}${authorityPattern.compressedPatternLine.slice(1)}`;
  
  // Combine tension and genius
  const combinedTensionLine = `${typePattern.tensionLine} Add to this: ${authorityPattern.tensionLine.charAt(0).toLowerCase()}${authorityPattern.tensionLine.slice(1)}`;
  const combinedGeniusLine = `${typePattern.geniusLine} Combined with how you decide: ${authorityPattern.geniusLine.charAt(0).toLowerCase()}${authorityPattern.geniusLine.slice(1)}`;
  
  return {
    corePatternLine,
    typePattern,
    authorityPattern,
    combinedTensionLine,
    combinedGeniusLine
  };
};

// ============================================
// CENTER PATTERNS
// ============================================

interface CenterPattern {
  defined: {
    compressedLine: string;
    tensionLine: string;
    geniusLine: string;
  };
  undefined: {
    compressedLine: string;
    tensionLine: string;
    geniusLine: string;
  };
}

export const CENTER_PATTERNS: { [key: string]: CenterPattern } = {
  'head': {
    defined: {
      compressedLine: "Certain questions keep returning because they're genuinely yours to carry.",
      tensionLine: "When you try to resolve every mental pressure, you exhaust yourself on questions that aren't yours.",
      geniusLine: "When you recognize your consistent themes, your inspiration becomes fuel rather than noise."
    },
    undefined: {
      compressedLine: "You absorb mental pressure from everywhere—and sometimes try to solve questions that aren't yours.",
      tensionLine: "When you take on others' mental burdens, you lose your own mental peace.",
      geniusLine: "When you learn to let mental pressure pass through, you gain wisdom about what questions actually matter."
    }
  },
  'ajna': {
    defined: {
      compressedLine: "You process information in a consistent way—but sometimes mistake your fixed perspective for the only truth.",
      tensionLine: "When you cling to your way of thinking, you miss perspectives that could expand you.",
      geniusLine: "When you trust your consistent mental process while staying open, your thinking becomes both reliable and wise."
    },
    undefined: {
      compressedLine: "You can see things from any angle—but sometimes lose yourself in others' certainty.",
      tensionLine: "When you adopt others' rigid thinking, you lose your gift of flexible perspective.",
      geniusLine: "When you trust your ability to see multiple sides, you become wiser than those with fixed minds."
    }
  },
  'throat': {
    defined: {
      compressedLine: "You have a consistent way of expressing—but sometimes speak when silence would serve better.",
      tensionLine: "When you fill space just to fill it, your words lose their power.",
      geniusLine: "When you speak from real impulse rather than habit, your expression carries unusual impact."
    },
    undefined: {
      compressedLine: "You can express in many ways—but sometimes stay silent when you have something important to say.",
      tensionLine: "When you hold back what needs to be said, or speak to be noticed, you miss your real expression.",
      geniusLine: "When you trust the right moment to speak, you surprise yourself and others with what comes through."
    }
  },
  'g': {
    defined: {
      compressedLine: "You have a fixed sense of direction—but sometimes follow paths that aren't authentically yours.",
      tensionLine: "When you ignore your inner compass, you end up in places that look right but feel wrong.",
      geniusLine: "When you trust your consistent sense of self and direction, you navigate with unusual certainty."
    },
    undefined: {
      compressedLine: "Your sense of self shifts with environment—but sometimes you forget to choose your environments wisely.",
      tensionLine: "When you stay in wrong places, you lose access to who you really are.",
      geniusLine: "When you choose environments that bring out your best self, your flexibility becomes your greatest asset."
    }
  },
  'heart': {
    defined: {
      compressedLine: "You have consistent willpower—but sometimes make promises your heart isn't in.",
      tensionLine: "When you commit without genuine desire, your willpower depletes and promises break.",
      geniusLine: "When you only commit to what you truly want, your follow-through becomes legendary."
    },
    undefined: {
      compressedLine: "Your sense of worth fluctuates—and sometimes you work too hard to prove yourself.",
      tensionLine: "When you try to prove your value, you exhaust yourself on a race you can't win.",
      geniusLine: "When you stop measuring your worth and simply contribute, your real value becomes obvious."
    }
  },
  'spleen': {
    defined: {
      compressedLine: "You have reliable instincts—but sometimes ignore the quiet knowing that speaks once.",
      tensionLine: "When you override your first hit, you lose access to wisdom that doesn't repeat itself.",
      geniusLine: "When you catch that subtle signal, you navigate with a precision others can't match."
    },
    undefined: {
      compressedLine: "You amplify fears and health signals from others—sometimes holding onto what isn't yours.",
      tensionLine: "When you hold fears that aren't yours, you become more anxious without knowing why.",
      geniusLine: "When you learn which fears are real and which are borrowed, you gain unusual wisdom about safety."
    }
  },
  'solar plexus': {
    defined: {
      compressedLine: "You ride emotional waves—but sometimes mistake the peak or valley for clarity.",
      tensionLine: "When you decide in emotional extremes, you commit to things that look different when the wave passes.",
      geniusLine: "When you wait for emotional clarity, your decisions have a depth that impulsive choices can't match."
    },
    undefined: {
      compressedLine: "You feel others' emotions intensely—sometimes more than they feel them themselves.",
      tensionLine: "When you take on others' emotional waves, you lose track of your own truth.",
      geniusLine: "When you learn to let emotions pass through without attaching, you become emotionally wise."
    }
  },
  'sacral': {
    defined: {
      compressedLine: "You have sustainable energy for what you respond to—but sometimes override your gut with your mind.",
      tensionLine: "When you ignore your gut response, you end up drained by commitments your body never agreed to.",
      geniusLine: "When you follow genuine response, you have energy that builds rather than depletes."
    },
    undefined: {
      compressedLine: "You can amplify others' work energy—but sometimes push past your natural limits.",
      tensionLine: "When you borrow others' pace, you exhaust yourself trying to match what was never yours.",
      geniusLine: "When you honor your need for rest and right timing, you become efficient in ways others aren't."
    }
  },
  'root': {
    defined: {
      compressedLine: "You have consistent drive—but sometimes treat every pressure as urgent when it's not.",
      tensionLine: "When you respond to all pressure equally, you exhaust yourself on false emergencies.",
      geniusLine: "When you trust your natural pace, you handle real urgency without manufactured stress."
    },
    undefined: {
      compressedLine: "You amplify stress and urgency from your environment—sometimes racing to finish what isn't actually urgent.",
      tensionLine: "When you absorb others' urgency, you live in a constant state of pressure that isn't real.",
      geniusLine: "When you learn which urgency is yours and which is borrowed, you find a calm that seems impossible to others."
    }
  }
};

// Helper to get center pattern
export const getCenterPattern = (centerName: string, isDefined: boolean): CenterPattern['defined'] | CenterPattern['undefined'] | null => {
  const normalizedName = centerName.toLowerCase().replace('ego', 'heart').replace(' ', '');
  const pattern = CENTER_PATTERNS[normalizedName];
  if (!pattern) return null;
  return isDefined ? pattern.defined : pattern.undefined;
};
