// ============================================
// ASTROLOGY NARRATIVE ENGINE - VOICE / COPY GENERATION
// Consumes interpreter output, generates Mirror-style language
// No interpretation logic, only text generation
// ============================================

import {
  FullChartData,
  CorePlacements,
  TransitHit,
  EnergySynthesis,
  AstrologyDeepDiveCard,
  PersonalRelevanceMatch,
  ChapterInfo,
  LifeArena,
  Timeframe,
  HouseAnalysis,
  WhatMattersItem,
  DevelopmentalPressureItem,
  KeyAspect,
} from './astrologyTypes';

import {
  SIGN_ELEMENTS,
  SIGN_MODALITIES,
  SIGN_QUALITIES,
  HOUSE_MEANINGS,
  HOUSE_DOMAINS,
  HOUSE_BEHAVIORS,
  HOUSE_MISTAKES,
  getChartRuler,
  getDominantHouses,
  getMainLifeArenas,
  detectPersonalRelevance,
  detectChapterTransits,
  detectRepeatPatterns,
  buildRulershipChains,
  isChartRulerActivated,
  prioritizeTransits,
  detectThemeConcentration,
  getActivatedHouses,
  getHouseTheme,
  getDominantPlanets,
  getPlanetImportanceLine,
} from './astrologyInterpreter';

// ============================================
// HERO DESCRIPTOR - Real behavior, calibrated tone
// ============================================

export const getHeroDescriptor = (sun: string, moon: string, asc: string): string => {
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  
  // RECOGNITION tone (60%) - softer, relatable
  const coreAction = sunElement === 'Water' ? 'You often feel things before you can name them' : 
                     sunElement === 'Fire' ? 'You tend to act first and process later' : 
                     sunElement === 'Earth' ? 'You usually trust what you can see and measure' : 'You often need to talk things through to know what you think';
  
  // TENSION tone (30%) - moderate, conditional
  const emotionalAction = moonElement === 'Fire' ? 'emotions can hit fast and move through quickly' : 
                          moonElement === 'Water' ? 'moods may linger longer than you expect' : 
                          moonElement === 'Earth' ? 'you may need physical comfort when things get hard' : 'talking usually helps you feel clearer';
  
  return `${coreAction}—${emotionalAction}.`;
};

// ============================================
// CHART SPINE - Observable behaviors, calibrated
// ============================================

export const getChartSpine = (placements: CorePlacements): string[] => {
  const spine: string[] = [];
  const sun = placements.sun || 'Unknown';
  const moon = placements.moon || 'Unknown';
  const asc = placements.ascendant || 'Unknown';
  const saturn_house = placements.saturn_house;
  
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  
  // 1. Core behavior (Sun) - RECOGNITION tone
  const sunBehaviors: { [key: string]: string } = {
    'Fire': 'You tend to need acknowledgment—being overlooked can drain you.',
    'Earth': 'You often need tangible progress—vague outcomes can frustrate you.',
    'Air': 'You usually need mental stimulation—routine without novelty may leave you restless.',
    'Water': 'You tend to need emotional honesty—surface talk can feel hollow.'
  };
  if (sunElement && sunBehaviors[sunElement]) spine.push(sunBehaviors[sunElement]);

  // 2. Emotional pattern (Moon) - TENSION tone
  const moonBehaviors: { [key: string]: string } = {
    'Fire': 'When stressed, you may get louder or busier rather than quieter.',
    'Earth': 'Under pressure, you can slow down and become more fixed.',
    'Air': 'When overwhelmed, you might overthink or create distance.',
    'Water': 'In difficult moments, you may withdraw or absorb the mood around you.'
  };
  if (moonElement && moonBehaviors[moonElement]) spine.push(moonBehaviors[moonElement]);

  // 3. First impression (Ascendant) - RECOGNITION tone
  const ascBehaviors: { [key: string]: string } = {
    'Aries': 'You often come across as direct—your reactions tend to show.',
    'Taurus': 'You can appear calm—others may not notice when you\'re stressed.',
    'Gemini': 'You often seem curious—you tend to ask questions before committing.',
    'Cancer': 'You may come across as guarded—trust can take time.',
    'Leo': 'You often appear warm—attention tends to energize you.',
    'Virgo': 'You can seem observant—you may notice what others miss.',
    'Libra': 'You often come across as easygoing—you tend to smooth over friction.',
    'Scorpio': 'You can come across as intense—especially when you\'re fully focused on someone.',
    'Sagittarius': 'You often seem optimistic—you may downplay difficulties.',
    'Capricorn': 'You can appear serious—humor might catch you off guard.',
    'Aquarius': 'You may seem detached—though you\'re often observing more than people realize.',
    'Pisces': 'You often come across as gentle—you tend to pick up on the energy around you.'
  };
  if (asc && ascBehaviors[asc]) spine.push(ascBehaviors[asc]);

  return spine.slice(0, 3); // Max 3 lines
};

// ============================================
// PERSONAL RELEVANCE LINE
// ============================================

export const getPersonalRelevanceLine = (
  match: PersonalRelevanceMatch, 
  activatedHouses: number[] = [],
  chartData: FullChartData | null = null
): string => {
  if (!match.isHighRelevance) return "";
  
  const chartRuler = chartData ? getChartRuler(chartData) : null;
  
  if (match.matchType === 'house' && activatedHouses.length > 0) {
    const primaryHouse = activatedHouses[0];
    const meaning = HOUSE_MEANINGS[primaryHouse];
    if (meaning) {
      const dominantHouses = getDominantHouses(chartData);
      const isTopDominant = dominantHouses[0] === primaryHouse;
      
      if (isTopDominant) {
        return `This hits harder because ${meaning.shortLabel} isn't a side theme in your chart—it's one of the main places life keeps training you.`;
      }
      return `This may land more personally—${meaning.shortLabel} is already sensitized territory for you.`;
    }
  }
  
  if (match.matchType === 'angular') {
    return "This lands closer to center—it touches a structural piece of how you move through life.";
  }
  
  if (match.matchType === 'element') {
    return "This resonates with how you naturally process things—you'll feel this more than most would.";
  }
  
  return "This may feel louder than usual—this area is already highly active in your chart.";
};

// ============================================
// CHART RULER CONTEXT LINE
// ============================================

export const getChartRulerContextLine = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): string => {
  const chartRuler = getChartRuler(chartData);
  if (!chartRuler) return '';
  
  const isActivated = transits.some(t => t.natal_point === chartRuler.planet);
  if (!isActivated) return '';
  
  return "This goes deeper than it first looks—it touches how you naturally move through life.";
};

// ============================================
// DOMINANT HOUSE RULER LINE
// ============================================

export const getDominantHouseRulerLine = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): string => {
  const chains = buildRulershipChains(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  for (const transit of transits.slice(0, 3)) {
    for (const chain of chains) {
      if (chain.ruler === transit.natal_point && dominantHouses.includes(chain.house)) {
        return "This connects directly to one of the main areas life keeps working on for you.";
      }
    }
  }
  return '';
};

// ============================================
// RULERSHIP CHAIN LINE
// ============================================

export const getRulershipChainLine = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): string => {
  const chains = buildRulershipChains(chartData);
  
  for (const transit of transits.slice(0, 3)) {
    for (const chain of chains) {
      if (chain.ruler === transit.natal_point && chain.house !== chain.rulerHouse) {
        const fromArea = HOUSE_MEANINGS[chain.house]?.shortLabel || 'one area';
        const toArea = HOUSE_MEANINGS[chain.rulerHouse]?.shortLabel || 'another area';
        
        if (chain.house === 3 && chain.rulerHouse === 8) {
          return "This starts as a conversation—but it's really about something deeper underneath it.";
        }
        if (chain.house === 7 && chain.rulerHouse === 4) {
          return "What's happening in a relationship is echoing something about home or emotional safety.";
        }
        if (chain.house === 10 && chain.rulerHouse === 4) {
          return "Career pressure is stirring something about roots or where you come from.";
        }
        if (chain.house === 4 && chain.rulerHouse === 10) {
          return "Home dynamics are affecting how you show up publicly.";
        }
        if (chain.house === 2 && chain.rulerHouse === 8) {
          return "What you're holding onto is connected to what you're afraid to lose.";
        }
        
        return `This isn't isolated—${fromArea} and ${toArea} are linked in how you're built.`;
      }
    }
  }
  return '';
};

// ============================================
// CHAPTER / LONG ARC LINE
// ============================================

export const getChapterLine = (chapterInfo: ChapterInfo): string => {
  if (!chapterInfo.hasChapterTransit) return '';
  
  const planetDescriptors: { [key: string]: string } = {
    'Saturn': 'This is part of a longer pressure that\'s been building for a while—not just this month.',
    'Uranus': 'This is part of a larger disruption cycle—changes you\'ve been sensing for a while are becoming harder to ignore.',
    'Neptune': 'This is part of a longer dissolving—clarity won\'t come from forcing it.',
    'Pluto': 'This is part of a deeper transformation—it\'s not a quick fix, it\'s a fundamental shift.'
  };
  
  return planetDescriptors[chapterInfo.transitPlanet || ''] || 
    'This is part of a longer arc—not something to rush.';
};

// ============================================
// REPEAT PATTERN LINE
// ============================================

export const getRepeatPatternLine = (chartData: FullChartData | null, transits: TransitHit[]): string => {
  const repeatInfo = detectRepeatPatterns(chartData, transits);
  
  if (!repeatInfo.isRepeating) return '';
  
  return `This theme keeps surfacing because ${repeatInfo.repeatedTheme} is already active territory in your chart.`;
};

// ============================================
// THEME COLLAPSE LINE
// ============================================

export const getThemeCollapseLineIfApplicable = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): string => {
  const concentrations = detectThemeConcentration(chartData, transits);
  if (concentrations.length === 0) return '';
  
  const top = concentrations[0];
  if (top.count >= 3) {
    return top.collapsedLine;
  }
  return '';
};

// ============================================
// LIFE AREA CONTEXT
// ============================================

export const getLifeAreaContext = (transits: TransitHit[]): string => {
  if (!transits || transits.length === 0) return "";
  
  const houses: number[] = [];
  for (const hit of transits.slice(0, 3)) {
    if (hit.natal_house && !houses.includes(hit.natal_house)) {
      houses.push(hit.natal_house);
    }
  }
  
  if (houses.length === 0) return "";
  
  const selected = houses.slice(0, 2).map(h => HOUSE_DOMAINS[h]).filter(Boolean);
  
  if (selected.length === 0) return "";
  
  if (selected.length === 1) {
    return `This is most likely showing up in ${selected[0]}.`;
  }
  
  return `This is most likely showing up in ${selected[0]}—and possibly in ${selected[1]}.`;
};

// ============================================
// MOON PHASE CONTEXT
// ============================================

export const getMoonPhaseContext = (transits: TransitHit[], chartData: FullChartData | null): string => {
  const moonTransit = transits.find(t => t.transit_point === 'Moon');
  if (!moonTransit) return '';
  
  const moonSign = moonTransit.transit_sign;
  const moonHouse = moonTransit.natal_house;
  
  const signDescriptor: { [key: string]: string } = {
    'Aries': 'emotional urgency',
    'Taurus': 'a need for comfort',
    'Gemini': 'mental restlessness',
    'Cancer': 'heightened sensitivity',
    'Leo': 'a desire to be seen',
    'Virgo': 'critical self-awareness',
    'Libra': 'relationship focus',
    'Scorpio': 'emotional intensity',
    'Sagittarius': 'restless optimism',
    'Capricorn': 'emotional reserve',
    'Aquarius': 'detached observation',
    'Pisces': 'diffuse sensitivity'
  };
  
  const signPart = signDescriptor[moonSign] || 'shifting moods';
  
  if (moonHouse && HOUSE_MEANINGS[moonHouse]) {
    return `The current cycle brings ${signPart}—especially around ${HOUSE_MEANINGS[moonHouse].shortLabel}.`;
  }
  
  return `The current cycle brings ${signPart}.`;
};

// ============================================
// WHAT THIS MAY FEEL LIKE
// ============================================

export const getWhatThisMayFeelLike = (
  transits: TransitHit[], 
  timeframe: Timeframe = 'today'
): string[] => {
  const feelings: string[] = [];
  
  const activatedHouses: number[] = getActivatedHouses(transits);
  
  for (const hit of transits.slice(0, 2)) {
    const { transit_point, natal_point, aspect_type } = hit;
    const isHard = ['square', 'opposition'].includes(aspect_type);
    
    // Saturn transits
    if (transit_point === 'Saturn') {
      if (timeframe === 'today') {
        feelings.push('a heavier undertone than the day actually requires');
      } else if (timeframe === 'week') {
        feelings.push('returning pressure you thought you\'d dealt with');
      } else {
        feelings.push('something asking for more maturity than you\'ve needed before');
      }
      if (natal_point === 'Sun') feelings.push('doubting whether you\'re doing this right');
      if (natal_point === 'Moon') feelings.push('emotional tiredness that doesn\'t match what happened');
    }
    
    // Jupiter transits
    if (transit_point === 'Jupiter') {
      if (timeframe === 'today') {
        feelings.push('wanting to say yes to something before you\'re ready');
      } else if (timeframe === 'week') {
        feelings.push('feeling restless for something bigger than this');
      } else {
        feelings.push('an urge to expand—but uncertainty about where');
      }
    }
    
    // Pluto transits  
    if (transit_point === 'Pluto') {
      feelings.push(timeframe === 'today' ? 'something surfacing that you didn\'t invite' : 'intensity that won\'t be rationalized away');
    }
    
    // Uranus transits
    if (transit_point === 'Uranus') {
      feelings.push(timeframe === 'today' ? 'an unexpected shift in how you see something' : 'a growing intolerance for what used to be tolerable');
    }
    
    // Neptune transits
    if (transit_point === 'Neptune') {
      feelings.push(timeframe === 'today' ? 'a slight fog around decisions' : 'something dissolving that you\'re not ready to lose');
    }
    
    // Mars transits
    if (transit_point === 'Mars') {
      if (timeframe === 'today') {
        feelings.push('a sharper edge than usual');
      } else if (isHard) {
        feelings.push('friction building toward something');
      }
    }
  }
  
  // ADD HOUSE-SPECIFIC BEHAVIOR
  if (activatedHouses.length > 0) {
    const primaryHouse = activatedHouses[0];
    const houseBehaviors = HOUSE_BEHAVIORS[primaryHouse];
    if (houseBehaviors) {
      const timeframeBehaviors = houseBehaviors[timeframe] || houseBehaviors['today'];
      if (timeframeBehaviors && timeframeBehaviors.length > 0) {
        const behavior = timeframeBehaviors[Math.floor(Math.random() * timeframeBehaviors.length)];
        feelings.push(behavior);
      }
    }
  }
  
  return [...new Set(feelings)].slice(0, 3);
};

// ============================================
// THE MISTAKE TO WATCH
// ============================================

export const getMistakeToWatch = (
  transits: TransitHit[], 
  timeframe: Timeframe = 'today'
): string[] => {
  const mistakes: string[] = [];
  
  const activatedHouses: number[] = getActivatedHouses(transits);
  
  for (const hit of transits.slice(0, 2)) {
    const { transit_point, natal_point, aspect_type } = hit;
    const isHard = ['square', 'opposition'].includes(aspect_type);
    
    if (transit_point === 'Saturn') {
      if (timeframe === 'today') {
        mistakes.push('assuming today\'s heaviness means something is wrong');
      } else if (timeframe === 'week') {
        mistakes.push('letting this week\'s frustration become your story');
      } else {
        mistakes.push('treating a temporary phase like permanent reality');
      }
    }
    
    if (transit_point === 'Jupiter') {
      if (timeframe === 'today') {
        mistakes.push('saying yes and figuring it out later');
      } else if (timeframe === 'week') {
        mistakes.push('filling your calendar before checking your capacity');
      } else {
        mistakes.push('confusing "more" with "better"');
      }
    }
    
    if (transit_point === 'Pluto') {
      if (timeframe === 'today') {
        mistakes.push('gripping tighter when something is trying to leave');
      } else {
        mistakes.push('fighting a transformation that\'s already won');
      }
    }
    
    if (transit_point === 'Uranus') {
      if (timeframe === 'today') {
        mistakes.push('blowing something up because you\'re bored');
      } else {
        mistakes.push('confusing restlessness with direction');
      }
    }
    
    if (transit_point === 'Neptune') {
      mistakes.push('making a permanent decision in temporary fog');
    }
    
    if (transit_point === 'Mars' && isHard) {
      mistakes.push('starting a fight you don\'t actually want to win');
    }
  }
  
  // ADD HOUSE-SPECIFIC MISTAKE
  if (activatedHouses.length > 0 && mistakes.length < 3) {
    const primaryHouse = activatedHouses[0];
    const houseMistakeData = HOUSE_MISTAKES[primaryHouse];
    if (houseMistakeData) {
      if (mistakes.length === 0) {
        mistakes.unshift(houseMistakeData.primary);
      } else {
        const supporting = houseMistakeData.supporting[Math.floor(Math.random() * houseMistakeData.supporting.length)];
        mistakes.push(supporting);
      }
    }
  }
  
  return [...new Set(mistakes)].slice(0, 3);
};

// ============================================
// REFLECTION QUESTION
// ============================================

export const getReflectionQuestion = (
  transits: TransitHit[], 
  timeframe: Timeframe
): string => {
  if (!transits || transits.length === 0) {
    return 'What keeps showing up that you keep pushing aside—even though it\'s getting louder?';
  }
  
  const hit = transits[0];
  const { transit_point, natal_point, natal_house } = hit;
  
  const houseContext = natal_house ? HOUSE_MEANINGS[natal_house] : null;
  
  // Saturn transits
  if (transit_point === 'Saturn') {
    if (timeframe === 'today') {
      if (natal_point === 'Sun') return 'What are you pretending is fine today—even though you thought about it before you got out of bed?';
      if (natal_point === 'Moon') return 'What feeling are you managing right now instead of actually feeling?';
      if (natal_house === 7) return 'What are you expecting from someone that you haven\'t been willing to ask for directly?';
      if (natal_house === 10) return 'What are you avoiding at work today—and why does it feel so heavy?';
      return 'Where are you bracing for something that might not actually be coming?';
    } else if (timeframe === 'week') {
      if (natal_point === 'Saturn') return 'What keeps getting harder this week—that you\'re pretending hasn\'t?';
      return 'What pattern has shown up multiple times this week—and what is it actually trying to tell you?';
    } else {
      if (natal_point === 'Sun') return 'What part of who you thought you were is being quietly dismantled this month?';
      if (natal_point === 'Moon') return 'What emotional truth are you finally being forced to sit with this month?';
      return 'What can\'t be rushed right now—and what happens if you stop trying to rush it?';
    }
  }
  
  // Jupiter transits
  if (transit_point === 'Jupiter') {
    if (timeframe === 'today') {
      if (natal_point === 'Saturn') return 'What are you about to say yes to today—even though you already know you don\'t have the capacity?';
      if (natal_house === 2) return 'What are you about to spend on today that\'s really about something else?';
      return 'Where is your enthusiasm today outpacing your actual readiness?';
    } else if (timeframe === 'week') {
      return 'What did you commit to earlier this week that you\'re already regretting—and what does that tell you?';
    } else {
      if (natal_point === 'Sun') return 'What are you growing into this month—and are you sure it\'s the right direction?';
      return 'Where is "more" actually the wrong answer this month—even though it feels right?';
    }
  }
  
  // Pluto transits
  if (transit_point === 'Pluto') {
    if (timeframe === 'today') {
      if (natal_house === 8) return 'What unspoken power dynamic showed up today—and which side of it are you on?';
      return 'What are you trying to control right now that actually can\'t be controlled?';
    } else if (timeframe === 'week') {
      return 'What keeps surfacing this week that you keep pushing back down—and what happens if you let it surface?';
    } else {
      if (natal_point === 'Sun') return 'What version of yourself are you being asked to release this month—even though it still feels like you?';
      if (natal_point === 'Moon') return 'What emotional pattern is dying this month—and are you grieving it or fighting it?';
      return 'What do you already know is over—that you haven\'t said out loud because then it becomes real?';
    }
  }
  
  // Uranus transits
  if (transit_point === 'Uranus') {
    if (timeframe === 'today') {
      return 'What thought crossed your mind today that surprised you—and are you willing to follow it?';
    } else if (timeframe === 'week') {
      if (natal_point === 'Venus') return 'What have you been wanting to change in a relationship this week that you\'re afraid to name?';
      return 'What keeps feeling suddenly unbearable this week—that you used to tolerate just fine?';
    } else {
      if (natal_point === 'Sun') return 'What would you change about your life this month—if you weren\'t afraid of looking like you got it wrong before?';
      return 'What structure in your life is this month showing you no longer fits—even if it used to?';
    }
  }
  
  // Neptune transits
  if (transit_point === 'Neptune') {
    if (timeframe === 'today') {
      return 'What are you uncertain about today—that you\'re pretending to be certain about?';
    } else if (timeframe === 'week') {
      return 'What clarity are you waiting for this week—that might not come through thinking?';
    } else {
      if (natal_point === 'Sun') return 'Who have you been pretending to be this month—and who might you actually be underneath?';
      return 'What are you hoping is true this month—even though you already sense it\'s not?';
    }
  }
  
  // Mars transits
  if (transit_point === 'Mars') {
    if (timeframe === 'today') return 'What do you want to do today that you\'re talking yourself out of—and what are you really afraid of?';
    if (timeframe === 'week') return 'Where has your frustration been pointing this week—and are you listening?';
    return 'What have you been wanting to fight for this month—that you keep convincing yourself isn\'t worth it?';
  }
  
  // Venus transits
  if (transit_point === 'Venus') {
    if (timeframe === 'today') return 'What do you want right now that you\'re pretending you don\'t need—because needing it feels weak?';
    return 'What in your relationships is this period asking you to be honest about—even if honesty feels risky?';
  }
  
  // Default with house awareness
  if (houseContext && timeframe === 'month') {
    return `What about ${houseContext.shortLabel} is this month asking you to look at more honestly?`;
  }
  
  return 'What pattern are you in the middle of right now—that you haven\'t fully seen yet, even though part of you knows?';
};

// ============================================
// ENERGY SYNTHESIS (TODAY/WEEK/MONTH HEADLINE)
// ============================================

export const getDailyEnergySynthesis = (
  transits: TransitHit[], 
  timeframe: Timeframe
): EnergySynthesis => {
  if (!transits || transits.length === 0) {
    return {
      headline: 'A pause',
      body: 'You\'re not being pushed right now. This is space to work with what you already have.',
      supporting: 'No significant transits detected'
    };
  }

  const primary = transits[0];
  const secondary = transits[1];
  
  const supportingParts: string[] = [];
  if (primary) supportingParts.push(`${primary.transit_point} ${primary.aspect_type} ${primary.natal_point}`);
  if (secondary) supportingParts.push(`${secondary.transit_point} ${secondary.aspect_type} ${secondary.natal_point}`);
  const supporting = supportingParts.length > 1 
    ? `Based on ${supportingParts[0]}, with ${supportingParts.slice(1).join(', ')} in the background.`
    : supportingParts.length === 1
    ? `Based on ${supportingParts[0]}.`
    : '';

  const { transit_point: t1, natal_point: n1 } = primary;
  
  // Jupiter transits
  if (t1 === 'Jupiter') {
    if (n1 === 'Saturn') {
      if (timeframe === 'today') {
        return {
          headline: 'Saying yes too early',
          body: 'You want to say yes to something bigger—but part of you already knows it\'s too early.\n\nYou can probably name exactly what this is about.',
          supporting
        };
      } else if (timeframe === 'week') {
        return {
          headline: 'The overcommit pattern',
          body: 'This keeps happening: you say yes before you\'re ready. You want more than you\'ve built the container for.',
          supporting
        };
      } else {
        return {
          headline: 'Expansion vs capacity',
          body: 'You keep wanting more than you can actually hold right now. This month isn\'t asking you to do more—it\'s asking you to prove you can finish what you start.',
          supporting
        };
      }
    }
    return {
      headline: timeframe === 'today' ? 'Feeling bigger than usual' : 'Growth pressure',
      body: timeframe === 'today' 
        ? 'You want to act on this confidence—like you could handle more than usual.'
        : 'Something in you is ready to expand. The question is whether this is signal or restlessness.',
      supporting
    };
  }
  
  // Saturn transits
  if (t1 === 'Saturn') {
    if (timeframe === 'today') {
      return {
        headline: 'A heavier day',
        body: 'Today feels more serious than it needs to. You might feel like you\'re running behind—even when you\'re not.',
        supporting
      };
    } else if (timeframe === 'week') {
      return {
        headline: 'Reality check',
        body: 'This week is showing you what\'s actually working and what\'s not. The pressure you feel is asking for real adjustment—not just willpower.',
        supporting
      };
    } else {
      return {
        headline: 'A season of restructuring',
        body: 'This month is asking you to take something more seriously. What you build now will hold—but it requires honest foundation work.',
        supporting
      };
    }
  }
  
  // Pluto transits
  if (t1 === 'Pluto') {
    return {
      headline: timeframe === 'today' ? 'Something deeper' : 'Transformation pressure',
      body: timeframe === 'today'
        ? 'There\'s something underneath today that isn\'t about today. Old material is surfacing.'
        : 'You\'re in a transformation that won\'t be rushed. Something is dying so something else can live.',
      supporting
    };
  }
  
  // Uranus transits
  if (t1 === 'Uranus') {
    return {
      headline: timeframe === 'today' ? 'Unexpected clarity' : 'Breaking pattern',
      body: timeframe === 'today'
        ? 'Something might shift without warning today. Your tolerance for the status quo is lower than usual.'
        : 'What used to work doesn\'t anymore. The restlessness you feel is pointing somewhere.',
      supporting
    };
  }
  
  // Neptune transits
  if (t1 === 'Neptune') {
    return {
      headline: timeframe === 'today' ? 'Slight fog' : 'Dissolving boundaries',
      body: timeframe === 'today'
        ? 'Clarity might feel just out of reach today. This isn\'t the time to force decisions.'
        : 'Something is dissolving. It\'s not always clear what\'s real—and that\'s part of the process.',
      supporting
    };
  }
  
  // Mars transits
  if (t1 === 'Mars') {
    return {
      headline: timeframe === 'today' ? 'Higher activation' : 'Drive building',
      body: timeframe === 'today'
        ? 'You may feel edgier today. There\'s more fire available—the question is how you direct it.'
        : 'Energy is accumulating. There\'s something you want to push toward—or push against.',
      supporting
    };
  }
  
  // Default
  return {
    headline: 'Mixed signals',
    body: 'Multiple forces are in play right now. No single theme dominates—which means you have more choice in how you respond.',
    supporting
  };
};

// ============================================
// WHERE LIFE KEEPS WORKING ON YOU
// ============================================

export const getWhereLifeKeepsWorkingOnYou = (chartData: FullChartData | null): string[] => {
  const arenas = getMainLifeArenas(chartData);
  
  return arenas.slice(0, 2).map((arena, i) => {
    if (i === 0) {
      return `${arena.shortLabel.charAt(0).toUpperCase() + arena.shortLabel.slice(1)} is not a background theme here—it's one of the main places life keeps trying to shape you.`;
    } else {
      return `${arena.shortLabel.charAt(0).toUpperCase() + arena.shortLabel.slice(1)} is live territory in this chart—what happens here matters more than it first appears.`;
    }
  });
};

// ============================================
// PLANET IMPORTANCE LINE (for Deep Dive)
// ============================================

export { getPlanetImportanceLine } from './astrologyInterpreter';

// ============================================
// DEBUG HELPER
// ============================================

export const debugNarrativePayload = (
  chartData: FullChartData | null,
  transits: TransitHit[],
  timeframe: Timeframe
): void => {
  if (process.env.NODE_ENV !== 'development') return;
  
  console.log('=== NARRATIVE PAYLOAD DEBUG ===');
  console.log('Energy Synthesis:', getDailyEnergySynthesis(transits, timeframe));
  console.log('What This May Feel Like:', getWhatThisMayFeelLike(transits, timeframe));
  console.log('Mistake to Watch:', getMistakeToWatch(transits, timeframe));
  console.log('Reflection Question:', getReflectionQuestion(transits, timeframe));
  console.log('Chart Ruler Line:', getChartRulerContextLine(chartData, transits));
  console.log('Life Area Context:', getLifeAreaContext(transits));
  console.log('================================');
};
