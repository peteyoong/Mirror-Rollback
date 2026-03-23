// ============================================
// ASTROLOGY INTERPRETER - PURE INTERPRETATION LOGIC
// No React, No JSX, No UI styles
// Returns structured data only
// ============================================

import {
  FullChartData,
  CorePlacements,
  TransitHit,
  ChartRuler,
  HouseRulerChain,
  PlanetStrength,
  PriorityPlanet,
  TransitPriority,
  PersonalRelevanceMatch,
  ThemeConcentration,
  ChapterInfo,
  RepeatPattern,
  LifeArena,
  HouseMeaning,
  HouseMistakes,
  HouseBehaviors,
  KeyAspect,
  HouseAnalysis,
  WhatMattersItem,
  DevelopmentalPressureItem,
  Timeframe,
  // Aspect Pattern Types (Master Astrologer v3)
  Stellium,
  OppositionAxis,
  PressureTriangle,
  FlowPattern,
  ConjunctionChain,
  AspectPatternAnalysis,
  DominantAspectPattern,
  HowPressureBuilds,
  EnhancedKeyAspect,
  // Life Chapter Types (Master Astrologer v4)
  ChapterType,
  ChapterActivation,
  LifeChapter,
  LifeChapterAnalysis,
  LifeChapterNarrative,
  // Dominant Truth Types (Master Astrologer v5)
  PressureType,
  ThemeCategory,
  CandidateTheme,
  DominantTruth,
  DominantTruthNarrative,
  CollapsedInsights,
} from './astrologyTypes';

// ============================================
// STATIC DATA - Sign mappings
// ============================================

export const SIGN_ELEMENTS: { [key: string]: string } = {
  'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
  'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
  'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
  'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
};

export const SIGN_MODALITIES: { [key: string]: string } = {
  'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
  'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
  'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable'
};

export const SIGN_QUALITIES: { [key: string]: string[] } = {
  'Aries': ['initiating', 'direct', 'pioneering', 'independent'],
  'Taurus': ['grounded', 'sensual', 'steady', 'value-oriented'],
  'Gemini': ['curious', 'versatile', 'communicative', 'adaptable'],
  'Cancer': ['nurturing', 'protective', 'intuitive', 'emotionally attuned'],
  'Leo': ['expressive', 'warm', 'creative', 'generous'],
  'Virgo': ['analytical', 'service-oriented', 'precise', 'practical'],
  'Libra': ['relational', 'harmonizing', 'aesthetic', 'diplomatic'],
  'Scorpio': ['intense', 'penetrating', 'transformative', 'resourceful'],
  'Sagittarius': ['expansive', 'truth-seeking', 'adventurous', 'philosophical'],
  'Capricorn': ['structured', 'ambitious', 'responsible', 'enduring'],
  'Aquarius': ['innovative', 'humanitarian', 'independent', 'visionary'],
  'Pisces': ['imaginative', 'empathic', 'fluid', 'transcendent']
};

// ============================================
// RULERSHIP SYSTEM
// ============================================

export const SIGN_RULERS: { [key: string]: string } = {
  'aries': 'Mars',
  'taurus': 'Venus',
  'gemini': 'Mercury',
  'cancer': 'Moon',
  'leo': 'Sun',
  'virgo': 'Mercury',
  'libra': 'Venus',
  'scorpio': 'Mars',
  'sagittarius': 'Jupiter',
  'capricorn': 'Saturn',
  'aquarius': 'Saturn',
  'pisces': 'Jupiter'
};

export const SIGN_RULERS_MODERN: { [key: string]: string } = {
  'scorpio': 'Pluto',
  'aquarius': 'Uranus',
  'pisces': 'Neptune'
};

// ============================================
// DIGNITY TABLES
// ============================================

export const PLANET_DOMICILE: { [key: string]: string[] } = {
  'Sun': ['Leo'],
  'Moon': ['Cancer'],
  'Mercury': ['Gemini', 'Virgo'],
  'Venus': ['Taurus', 'Libra'],
  'Mars': ['Aries', 'Scorpio'],
  'Jupiter': ['Sagittarius', 'Pisces'],
  'Saturn': ['Capricorn', 'Aquarius']
};

export const PLANET_EXALTATION: { [key: string]: string } = {
  'Sun': 'Aries',
  'Moon': 'Taurus',
  'Mercury': 'Virgo',
  'Venus': 'Pisces',
  'Mars': 'Capricorn',
  'Jupiter': 'Cancer',
  'Saturn': 'Libra'
};

export const PLANET_DETRIMENT: { [key: string]: string[] } = {
  'Sun': ['Aquarius'],
  'Moon': ['Capricorn'],
  'Mercury': ['Sagittarius', 'Pisces'],
  'Venus': ['Aries', 'Scorpio'],
  'Mars': ['Taurus', 'Libra'],
  'Jupiter': ['Gemini', 'Virgo'],
  'Saturn': ['Cancer', 'Leo']
};

export const PLANET_FALL: { [key: string]: string } = {
  'Sun': 'Libra',
  'Moon': 'Scorpio',
  'Mercury': 'Pisces',
  'Venus': 'Virgo',
  'Mars': 'Cancer',
  'Jupiter': 'Capricorn',
  'Saturn': 'Aries'
};

// House position classifications
export const ANGULAR_HOUSES = [1, 4, 7, 10];
export const SUCCEDENT_HOUSES = [2, 5, 8, 11];
export const CADENT_HOUSES = [3, 6, 9, 12];

// ============================================
// HOUSE MEANINGS DATA
// ============================================

export const HOUSE_MEANINGS: { [key: number]: HouseMeaning } = {
  1: {
    label: "Identity & Self-Presentation",
    shortLabel: "identity",
    arena: "how you show up, first impressions, physical self",
    theme: "self-definition and the way you meet life",
    whenActivated: "questions about who you are and how you're being seen",
    specialty: "This is one of the main places life keeps training you through how you present, what you project, and who you become when observed.",
    developmentalPressure: "You're being asked to show up as yourself—without the costume, without the performance, without the defense.",
    consequenceZone: "What you project gets reflected back. Misalignment here creates friction everywhere.",
    whenIgnored: "You lose touch with who you actually are vs. who you've been performing."
  },
  2: {
    label: "Values & Resources",
    shortLabel: "values & money",
    arena: "money, possessions, self-worth, what you hold onto",
    theme: "security and what you truly value",
    whenActivated: "questions about worth, money, or what you're holding onto",
    specialty: "This is one of the main places life keeps training you through what you have, what you value, and whether you feel like enough.",
    developmentalPressure: "You're being asked to clarify what actually matters—not what should matter, but what does.",
    consequenceZone: "What you hold onto shapes what you become. Over-grip here and growth stops.",
    whenIgnored: "Security gets confused with control. Self-worth collapses into net worth."
  },
  3: {
    label: "Communication & Learning",
    shortLabel: "communication",
    arena: "thinking, speaking, learning, siblings, local environment",
    theme: "how you process and express what you know",
    whenActivated: "how you're thinking, what you're saying, and whether the words are landing",
    specialty: "This is one of the main places life keeps training you through thought, language, interpretation, and how you make meaning from information.",
    developmentalPressure: "You're being asked to clarify—not explain more, but clarify. What you say carries more weight than you realize.",
    consequenceZone: "Miscommunication here ripples outward. What you can't articulate, you can't integrate.",
    whenIgnored: "You keep explaining but not being understood. The same conversation keeps repeating."
  },
  4: {
    label: "Home & Emotional Foundation",
    shortLabel: "home & roots",
    arena: "home, family, roots, private self, emotional baseline",
    theme: "where you come from and what grounds you",
    whenActivated: "your sense of safety, family dynamics, or inner emotional stability",
    specialty: "This is where inner stability gets tested. When this area is unsettled, everything echoes. Growth here is non-negotiable.",
    developmentalPressure: "You're being asked to find ground that doesn't depend on external conditions.",
    consequenceZone: "Instability here makes everything else harder. You can't build on a shaky foundation.",
    whenIgnored: "You keep looking for home in places that can't hold you. Inner restlessness persists."
  },
  5: {
    label: "Creativity & Self-Expression",
    shortLabel: "creativity & play",
    arena: "creativity, romance, pleasure, children, risk-taking",
    theme: "what you create and how you express yourself",
    whenActivated: "desire for recognition, creative blocks, or romantic intensity",
    specialty: "This is one of the main places life keeps training you through what you create, what brings you joy, and how you risk being seen.",
    developmentalPressure: "You're being asked to create without guarantee of applause. Express for its own sake.",
    consequenceZone: "Unexpressed creativity becomes bitterness. Joy deferred turns to resentment.",
    whenIgnored: "Life feels flat. You're surviving but not creating. Something vital goes dormant."
  },
  6: {
    label: "Work & Daily Systems",
    shortLabel: "work & health",
    arena: "daily work, health, routines, service, improvement",
    theme: "how you maintain yourself and contribute through effort",
    whenActivated: "work pressure, health awareness, or the quality of your daily systems",
    specialty: "This is one of the main places life keeps training you through what you do every day—your craft, your discipline, your maintenance.",
    developmentalPressure: "You're being asked to show up consistently, not just when inspired. Discipline is the teacher here.",
    consequenceZone: "Neglect here accumulates silently. The body keeps score. Systems fail when you need them.",
    whenIgnored: "You burn out. Health erodes. Work becomes something that happens to you, not through you."
  },
  7: {
    label: "Relationships & Partnership",
    shortLabel: "relationships",
    arena: "committed relationships, partnerships, contracts, projection",
    theme: "how you relate to others and what you project onto them",
    whenActivated: "relationship dynamics, fairness, or what you keep seeing in others",
    specialty: "This is one of the main places life keeps training you through who you attract, what you project, and what you see in the mirror of another.",
    developmentalPressure: "You're being asked to see the other as they are—not as who you need them to be.",
    consequenceZone: "What you can't see in yourself shows up in your relationships. Every projection has a cost.",
    whenIgnored: "You keep attracting the same dynamic. The partner changes but the pattern doesn't."
  },
  8: {
    label: "Intimacy & Transformation",
    shortLabel: "trust & depth",
    arena: "intimacy, shared resources, power, loss, regeneration",
    theme: "what you merge with and what transforms you",
    whenActivated: "trust issues, power dynamics, or emotional vulnerability",
    specialty: "This is one of the main places life keeps training you through what you can't control—depth, loss, merging, and what forces you to change.",
    developmentalPressure: "You're being asked to let go of something you're still gripping. Transformation requires surrender.",
    consequenceZone: "Avoided depth becomes shadow. Control here backfires. What you won't face keeps returning.",
    whenIgnored: "Intimacy stays shallow. Power dynamics run the show unconsciously. You repeat cycles of loss."
  },
  9: {
    label: "Beliefs & Expansion",
    shortLabel: "meaning & truth",
    arena: "philosophy, travel, higher education, beliefs, truth-seeking",
    theme: "what you believe and how your worldview expands",
    whenActivated: "questions about meaning, direction, or whether you're on the right path",
    specialty: "This is one of the main places life keeps training you through what you believe, what you're reaching toward, and whether your map matches the territory.",
    developmentalPressure: "You're being asked to test your beliefs—not defend them, test them. Truth requires willingness to be wrong.",
    consequenceZone: "Untested beliefs become prisons. A map that doesn't match reality leads you nowhere.",
    whenIgnored: "Meaning collapses. You go through motions without conviction. Life feels like it's happening around you."
  },
  10: {
    label: "Career & Public Role",
    shortLabel: "vocation",
    arena: "career, reputation, public life, responsibility, legacy",
    theme: "what you're here to contribute and be known for",
    whenActivated: "career pressure, visibility, or questions about your direction",
    specialty: "This is one of the main places life keeps training you through what you build, what you contribute, and what remains after you're gone.",
    developmentalPressure: "You're being asked to step into a role that requires more than you've given before. Growth here is public.",
    consequenceZone: "What you build here outlasts you—for better or worse. Reputation is a slow-motion portrait.",
    whenIgnored: "Work becomes meaningless. You climb ladders but don't know why. Achievement without satisfaction."
  },
  11: {
    label: "Community & Future Vision",
    shortLabel: "community",
    arena: "friendships, groups, networks, hopes, future vision",
    theme: "where you belong and what you're building toward",
    whenActivated: "questions about belonging, friendship, or whether you fit",
    specialty: "This is one of the main places life keeps training you through who you run with, what you hope for, and whether your people are really your people.",
    developmentalPressure: "You're being asked to discern—not all communities are yours. Find the ones that actually fit.",
    consequenceZone: "Wrong community, wrong future. The people around you shape what you become.",
    whenIgnored: "Isolation increases. Future feels directionless. You perform belonging instead of actually fitting."
  },
  12: {
    label: "Surrender & Unconscious",
    shortLabel: "hidden self",
    arena: "retreat, spirituality, unconscious patterns, endings, exile",
    theme: "what you can't see yet and what needs release",
    whenActivated: "need for retreat, confusion, or patterns you can't fully name",
    specialty: "This is one of the main places life keeps training you through what you can't see, what you need to release, and what operates beneath your awareness.",
    developmentalPressure: "You're being asked to let something end. Not everything can be fixed—some things need to be released.",
    consequenceZone: "What you won't release follows you. Unconscious patterns run the show until you face them.",
    whenIgnored: "Exhaustion without cause. The same pattern repeats with different faces. Something keeps leaking energy."
  }
};

// House domain short labels
export const HOUSE_DOMAINS: { [key: number]: string } = {
  1: 'identity and how you show up',
  2: 'money and what you value',
  3: 'communication and thinking',
  4: 'home and emotional foundation',
  5: 'creativity and self-expression',
  6: 'work and daily routines',
  7: 'relationships and partnership',
  8: 'intimacy and shared resources',
  9: 'beliefs and meaning-making',
  10: 'career and public role',
  11: 'community and future vision',
  12: 'unconscious patterns and release'
};

// ============================================
// HOUSE BEHAVIORS (timeframe-specific)
// ============================================

export const HOUSE_BEHAVIORS: { [key: number]: HouseBehaviors } = {
  1: {
    today: [
      "checking the mirror more than usual",
      "adjusting how you present yourself mid-conversation",
      "feeling visible in a way that makes you self-conscious"
    ],
    week: [
      "catching yourself performing instead of just being",
      "wondering if people see what you're actually trying to show",
      "small identity adjustments that feel bigger than they should"
    ],
    month: [
      "who you've been presenting no longer matches who you're becoming",
      "wanting to be seen differently but not knowing what to change",
      "outgrowing an image you didn't realize you'd built"
    ]
  },
  2: {
    today: [
      "checking your account balance more than necessary",
      "feeling slightly anxious about what you have—or don't",
      "gripping something tighter than the situation requires"
    ],
    week: [
      "money or security concerns popping up at odd moments",
      "questioning whether you have enough—or are enough",
      "small purchase decisions feeling heavier than they should"
    ],
    month: [
      "reexamining what you actually value vs. what you thought you should",
      "security patterns you built years ago no longer fitting",
      "wanting more but unsure if more is what you actually need"
    ]
  },
  3: {
    today: [
      "saying something and immediately wishing you'd said it differently",
      "reading the same paragraph three times because it won't stick",
      "a conversation playing on loop in your head"
    ],
    week: [
      "the same topic coming up in completely unrelated conversations",
      "explaining something multiple ways but still feeling misunderstood",
      "mental restlessness that won't quite settle"
    ],
    month: [
      "realizing you've been thinking about something for weeks without resolving it",
      "a shift in how you process—old mental habits not working the same",
      "what you used to believe about communication being tested"
    ]
  },
  4: {
    today: [
      "feeling unsettled at home for no obvious reason",
      "reacting more strongly to family tone or emotional atmosphere",
      "wanting to be alone but also wanting comfort"
    ],
    week: [
      "old family patterns surfacing in current situations",
      "home feeling like it needs something you can't quite name",
      "emotional weather that seems to come from nowhere"
    ],
    month: [
      "questioning what 'home' actually means to you now",
      "family dynamics demanding a different response than your usual one",
      "the foundation you built feeling less solid than it did"
    ]
  },
  5: {
    today: [
      "wanting attention you're not getting",
      "creative restlessness without clear outlet",
      "a flash of jealousy when someone else gets recognized"
    ],
    week: [
      "feeling invisible even when you're being seen",
      "creative blocks that feel personal rather than technical",
      "joy requiring more effort than it used to"
    ],
    month: [
      "what used to light you up no longer doing it",
      "creative identity being restructured from the inside",
      "risking being seen in a new way—or avoiding that risk entirely"
    ]
  },
  6: {
    today: [
      "obsessing over a small detail that won't let go",
      "body tension that mirrors mental pressure",
      "feeling behind on maintenance you didn't know you were tracking"
    ],
    week: [
      "systems breaking down in small, annoying ways",
      "health awareness sharpening—something asking for attention",
      "work feeling like a grind even when it's going fine"
    ],
    month: [
      "your routines being redesigned by life rather than choice",
      "capacity limits becoming clearer than you'd like",
      "the gap between what you should do and what you actually do"
    ]
  },
  7: {
    today: [
      "reading more into a partner's comment than is probably there",
      "needing something from someone you haven't asked for",
      "a small relationship friction staying with you longer than it should"
    ],
    week: [
      "the same dynamic replaying with different people",
      "wanting closeness but also feeling irritated by it",
      "seeing something in others that you're not seeing in yourself"
    ],
    month: [
      "relationship patterns you thought you'd resolved resurfacing",
      "what you need from partnership shifting in ways you hadn't expected",
      "the mirror showing you something you'd rather not see"
    ]
  },
  8: {
    today: [
      "sensing something unspoken in a conversation",
      "a slight power struggle you can't quite name",
      "feeling exposed but trying to stay in control"
    ],
    week: [
      "trust getting tested in small ways",
      "intensity rising in situations that shouldn't be intense",
      "something hidden wanting to surface—yours or someone else's"
    ],
    month: [
      "old loss or betrayal echoing in current situations",
      "control strategies that used to work no longer working",
      "being asked to merge with something you're not sure you trust"
    ]
  },
  9: {
    today: [
      "a belief getting quietly challenged",
      "restless for meaning you can't quite reach",
      "feeling stuck in a perspective that's too small"
    ],
    week: [
      "questioning whether your map actually matches the territory",
      "information that doesn't fit your framework arriving anyway",
      "the urge to escape—travel, learn, anything but here"
    ],
    month: [
      "worldview cracks that can't be papered over",
      "what you believed about meaning being tested by reality",
      "direction uncertainty that won't resolve by thinking harder"
    ]
  },
  10: {
    today: [
      "work feeling heavier than the task actually is",
      "wanting recognition for effort no one sees",
      "a brief flash of 'is this what I'm doing with my life?'"
    ],
    week: [
      "career pressure that isn't coming from the job itself",
      "achievement feeling hollow even when you hit the mark",
      "the weight of expectation—yours or someone else's—pressing"
    ],
    month: [
      "questioning what you're actually building toward",
      "professional identity shifting in ways you can't control",
      "the gap between where you are and where you thought you'd be"
    ]
  },
  11: {
    today: [
      "feeling out of place in a group you usually fit",
      "a friend saying something that lands wrong",
      "future plans feeling less certain than yesterday"
    ],
    week: [
      "social energy fluctuating more than usual",
      "questioning whether your people are really your people",
      "hopes for the future getting quieter or louder without clear reason"
    ],
    month: [
      "community shifts—who belongs is changing",
      "vision for the future being rewritten by circumstance",
      "discovering that some friendships were situational, not permanent"
    ]
  },
  12: {
    today: [
      "tired for reasons you can't name",
      "a dream or memory surfacing without invitation",
      "wanting to disappear for a few hours"
    ],
    week: [
      "something asking to be released that you're still holding",
      "energy leaking somewhere you can't identify",
      "the past showing up in unexpected places"
    ],
    month: [
      "patterns you thought you'd moved past returning for review",
      "something ending whether you're ready or not",
      "the need to let go becoming less optional"
    ]
  }
};

// ============================================
// HOUSE MISTAKES DATA
// ============================================

export const HOUSE_MISTAKES: { [key: number]: HouseMistakes } = {
  1: {
    primary: "changing yourself to fit the room instead of showing up as you actually are",
    supporting: ["letting someone else's perception become your self-image", "performing a version of yourself that isn't sustainable"]
  },
  2: {
    primary: "gripping something tighter because you're afraid of what losing it means",
    supporting: ["confusing what you have with who you are", "spending to prove something to yourself"]
  },
  3: {
    primary: "explaining more when what's needed is clarity, not volume",
    supporting: ["saying it before you've actually thought it through", "using words to avoid the silence where truth lives"]
  },
  4: {
    primary: "trying to fix outer circumstances when the instability is internal",
    supporting: ["making family carry a weight they didn't create", "looking for home in a place that can't hold you"]
  },
  5: {
    primary: "performing for approval instead of creating for expression",
    supporting: ["seeking validation to fill a gap only your own work can fill", "avoiding creative risk because rejection feels existential"]
  },
  6: {
    primary: "perfecting the wrong thing while the right thing waits",
    supporting: ["burnout disguised as discipline", "fixing details to avoid the larger structural issue"]
  },
  7: {
    primary: "expecting a partner to fill a gap that only you can address",
    supporting: ["fighting for fairness when understanding is what's needed", "seeing in them what you won't see in yourself"]
  },
  8: {
    primary: "trying to control what can only be surrendered to",
    supporting: ["avoiding vulnerability by intellectualizing it", "escalating because uncertainty feels intolerable", "treating depth as danger instead of doorway"]
  },
  9: {
    primary: "preaching what you haven't actually lived yet",
    supporting: ["running toward new meaning instead of integrating what you already know", "defending your map instead of checking whether it matches the territory"]
  },
  10: {
    primary: "sacrificing what matters for achievement that won't satisfy",
    supporting: ["working harder instead of working smarter", "building toward a goal you inherited but never chose"]
  },
  11: {
    primary: "performing belonging instead of testing whether you actually fit",
    supporting: ["planning the future to avoid the present", "collecting people instead of choosing them"]
  },
  12: {
    primary: "pushing through when the actual task is surrender",
    supporting: ["ignoring what's asking to be released", "treating exhaustion as weakness instead of signal"]
  }
};

// ============================================
// CHART RULER DETECTION
// ============================================

export const getChartRuler = (chartData: FullChartData | null): ChartRuler | null => {
  if (!chartData?.natal?.angles?.asc?.sign) return null;
  
  const ascSign = chartData.natal.angles.asc.sign.toLowerCase();
  const ruler = SIGN_RULERS[ascSign];
  if (!ruler) return null;
  
  const planets = chartData.natal.planets || {};
  const rulerData = planets[ruler];
  
  if (!rulerData) return null;
  
  return {
    planet: ruler,
    sign: rulerData.sign || '',
    house: rulerData.house || 0
  };
};

export const isChartRulerActivated = (chartData: FullChartData | null, transits: TransitHit[]): boolean => {
  const ruler = getChartRuler(chartData);
  if (!ruler) return false;
  
  return transits.some(t => 
    t.natal_point.toLowerCase() === ruler.planet.toLowerCase()
  );
};

// ============================================
// DOMINANT HOUSES
// ============================================

export const getDominantHouses = (chartData: FullChartData | null): number[] => {
  if (!chartData?.natal?.concentrations?.dominant_houses) return [];
  return chartData.natal.concentrations.dominant_houses
    .slice(0, 3)
    .map((h: { house: number }) => h.house);
};

// ============================================
// RULERSHIP CHAINS
// ============================================

const getChainMeaning = (fromHouse: number, toHouse: number): string => {
  const meanings: { [key: string]: string } = {
    '1-8': 'identity is shaped by depth, trust, and what you can\'t control',
    '1-7': 'identity is shaped through relationships and how others see you',
    '1-10': 'identity is shaped through career and public contribution',
    '2-3': 'security comes through communication and learning',
    '2-8': 'resources are tied to shared power and what you merge with',
    '3-8': 'communication carries more weight—it\'s about trust, not just information',
    '3-9': 'daily thinking connects to bigger questions of meaning',
    '3-12': 'thinking connects to what you can\'t fully see or name',
    '4-10': 'home and career are directly linked—one affects the other',
    '4-8': 'emotional foundation is tied to intimacy and transformation',
    '5-11': 'self-expression connects to community and future vision',
    '6-12': 'daily work connects to something larger—service or surrender',
    '7-1': 'relationships shape who you become',
    '7-4': 'partnership is tied to emotional security and home',
    '8-2': 'transformation happens through what you value and hold',
    '8-5': 'depth and creativity are intertwined',
    '9-3': 'beliefs shape how you think and communicate',
    '10-4': 'career is rooted in where you come from',
    '10-7': 'public role is shaped by partnerships',
    '11-5': 'future vision connects to creative self-expression',
    '12-6': 'what\'s hidden affects daily functioning'
  };
  
  const key = `${fromHouse}-${toHouse}`;
  const reverseKey = `${toHouse}-${fromHouse}`;
  
  return meanings[key] || meanings[reverseKey] || 
    `${HOUSE_MEANINGS[fromHouse]?.shortLabel || 'this area'} connects to ${HOUSE_MEANINGS[toHouse]?.shortLabel || 'another area'}`;
};

export const buildRulershipChains = (chartData: FullChartData | null): HouseRulerChain[] => {
  if (!chartData?.natal?.houses?.cusps) return [];
  
  const chains: HouseRulerChain[] = [];
  const planets = chartData.natal.planets || {};
  
  for (const cusp of chartData.natal.houses.cusps) {
    const houseNumber = cusp.house;
    const houseSign = cusp.sign;
    
    if (!houseSign) continue;
    
    const ruler = SIGN_RULERS[houseSign.toLowerCase()];
    if (!ruler) continue;
    
    const rulerData = planets[ruler];
    if (!rulerData) continue;
    
    chains.push({
      house: houseNumber,
      sign: houseSign,
      ruler: ruler,
      rulerHouse: rulerData.house || 0,
      rulerSign: rulerData.sign || '',
      meaningConnection: getChainMeaning(houseNumber, rulerData.house || 0)
    });
  }
  
  return chains;
};

// ============================================
// DIGNITY / CONDITION WEIGHTING
// ============================================

export const getDignityScore = (planet: string, sign: string): number => {
  if (PLANET_DOMICILE[planet]?.includes(sign)) return 2;
  if (PLANET_EXALTATION[planet] === sign) return 1;
  if (PLANET_FALL[planet] === sign) return -2;
  if (PLANET_DETRIMENT[planet]?.includes(sign)) return -1;
  return 0;
};

export const getHousePositionScore = (house: number): number => {
  if (ANGULAR_HOUSES.includes(house)) return 1;
  if (CADENT_HOUSES.includes(house)) return -1;
  return 0;
};

const isConjunctLuminary = (planet: string, chartData: FullChartData | null): boolean => {
  if (!chartData?.natal?.aspects) return false;
  
  return chartData.natal.aspects.some(asp => 
    asp.aspect_type === 'conjunction' &&
    ((asp.point_a === planet && (asp.point_b === 'Sun' || asp.point_b === 'Moon')) ||
     (asp.point_b === planet && (asp.point_a === 'Sun' || asp.point_a === 'Moon')))
  );
};

const countAspects = (planet: string, chartData: FullChartData | null): number => {
  if (!chartData?.natal?.aspects) return 0;
  
  return chartData.natal.aspects.filter(asp => 
    asp.point_a === planet || asp.point_b === planet
  ).length;
};

export const buildPlanetStrengths = (chartData: FullChartData | null): PlanetStrength[] => {
  if (!chartData?.natal?.planets) return [];
  
  const chartRuler = getChartRuler(chartData);
  const strengths: PlanetStrength[] = [];
  const planets = chartData.natal.planets;
  
  const planetNames = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'];
  
  for (const planetName of planetNames) {
    const planetData = planets[planetName];
    if (!planetData) continue;
    
    const dignityScore = getDignityScore(planetName, planetData.sign || '');
    const houseScore = getHousePositionScore(planetData.house || 0);
    const aspectCount = countAspects(planetName, chartData);
    const isRuler = chartRuler?.planet === planetName;
    const conjunctLum = isConjunctLuminary(planetName, chartData);
    
    let totalScore = dignityScore + houseScore;
    if (aspectCount >= 3) totalScore += 1;
    if (isRuler) totalScore += 2;
    if (conjunctLum) totalScore += 1;
    
    let strengthLabel: 'strong' | 'moderate' | 'challenged' = 'moderate';
    if (totalScore >= 3) strengthLabel = 'strong';
    else if (totalScore <= -1) strengthLabel = 'challenged';
    
    strengths.push({
      planet: planetName,
      sign: planetData.sign || '',
      house: planetData.house || 0,
      dignityScore,
      houseScore,
      aspectCount,
      isChartRuler: isRuler,
      conjunctLuminary: conjunctLum,
      totalScore,
      strengthLabel
    });
  }
  
  return strengths;
};

// ============================================
// PLANET PRIORITY RANKING
// ============================================

export const getDominantPlanets = (chartData: FullChartData | null): PriorityPlanet[] => {
  const strengths = buildPlanetStrengths(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  const sorted = [...strengths].sort((a, b) => b.totalScore - a.totalScore);
  
  return sorted.slice(0, 5).map((strength, index) => {
    const reasons: string[] = [];
    
    if (strength.isChartRuler) reasons.push('shapes how you move through life');
    if (strength.dignityScore >= 2) reasons.push('naturally at home');
    if (strength.dignityScore === 1) reasons.push('elevated');
    if (strength.houseScore === 1) reasons.push('prominent position');
    if (strength.aspectCount >= 3) reasons.push('highly connected');
    if (strength.conjunctLuminary) reasons.push('tied to core identity');
    if (dominantHouses.includes(strength.house)) reasons.push('in a concentrated area');
    
    return {
      planet: strength.planet,
      rank: index + 1,
      reasons,
      strength
    };
  });
};

export const isPlanetDominant = (planet: string, chartData: FullChartData | null): boolean => {
  const dominant = getDominantPlanets(chartData);
  return dominant.slice(0, 3).some(p => p.planet === planet);
};

// ============================================
// TRANSIT PRIORITY HIERARCHY
// ============================================

export const prioritizeTransits = (
  transits: TransitHit[],
  chartData: FullChartData | null
): TransitPriority[] => {
  const chartRuler = getChartRuler(chartData);
  const dominantPlanets = getDominantPlanets(chartData);
  const dominantHouses = getDominantHouses(chartData);
  const chains = buildRulershipChains(chartData);
  const planetStrengths = buildPlanetStrengths(chartData);
  
  return transits.map(transit => {
    let score = 0;
    const reasons: string[] = [];
    
    if (chartRuler && transit.natal_point === chartRuler.planet) {
      score += 3;
      reasons.push('touches how you naturally operate');
    }
    
    if (dominantPlanets.slice(0, 3).some(p => p.planet === transit.natal_point)) {
      score += 2;
      reasons.push('hits a defining force in your chart');
    }
    
    if (dominantHouses.includes(transit.natal_house)) {
      score += 2;
      reasons.push('lands in concentrated territory');
    }
    
    const planetStrength = planetStrengths.find(p => p.planet === transit.natal_point);
    if (planetStrength && ANGULAR_HOUSES.includes(planetStrength.house)) {
      score += 1;
      reasons.push('prominent position');
    }
    
    const chainMatch = chains.find(c => c.ruler === transit.natal_point);
    if (chainMatch && chainMatch.house !== chainMatch.rulerHouse) {
      score += 1;
      reasons.push('connects multiple life areas');
    }
    
    if (planetStrength && planetStrength.strengthLabel === 'challenged') {
      score -= 1;
    }
    
    score += Math.floor(transit.strength_score / 3);
    
    let priorityLabel: 'primary' | 'supporting' | 'background' = 'background';
    if (score >= 4) priorityLabel = 'primary';
    else if (score >= 2) priorityLabel = 'supporting';
    
    return {
      transit,
      priorityScore: score,
      priorityLabel,
      boostReasons: reasons
    };
  }).sort((a, b) => b.priorityScore - a.priorityScore);
};

// ============================================
// PERSONAL RELEVANCE DETECTION
// ============================================

export const detectPersonalRelevance = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): PersonalRelevanceMatch => {
  if (!chartData?.natal?.concentrations || !transits || transits.length === 0) {
    return { isHighRelevance: false, matchType: null };
  }
  
  const concentrations = chartData.natal.concentrations;
  const dominantHouses = concentrations.dominant_houses || [];
  const angularPlanets = concentrations.angular_planets || [];
  const dominantElements = concentrations.dominant_elements || [];
  
  const dominantHouseNumbers = dominantHouses.slice(0, 2).map((h: { house: number }) => h.house);
  const angularPlanetNames = angularPlanets.map((p: { planet: string }) => p.planet.toLowerCase());
  const topElement = dominantElements[0]?.[0]?.toLowerCase();
  
  const elementSigns: { [key: string]: string[] } = {
    'fire': ['aries', 'leo', 'sagittarius'],
    'earth': ['taurus', 'virgo', 'capricorn'],
    'air': ['gemini', 'libra', 'aquarius'],
    'water': ['cancer', 'scorpio', 'pisces']
  };
  
  for (const hit of transits.slice(0, 3)) {
    if (hit.natal_house && dominantHouseNumbers.includes(hit.natal_house)) {
      return {
        isHighRelevance: true,
        matchType: 'house',
        matchDetail: 'areas you spend a lot of time thinking about'
      };
    }
    
    if (angularPlanetNames.includes(hit.natal_point.toLowerCase())) {
      return {
        isHighRelevance: true,
        matchType: 'angular',
        matchDetail: 'a core part of how you move through life'
      };
    }
    
    if (topElement && elementSigns[topElement]) {
      const natalSign = hit.natal_sign?.toLowerCase();
      if (natalSign && elementSigns[topElement].includes(natalSign)) {
        return {
          isHighRelevance: true,
          matchType: 'element',
          matchDetail: 'how you naturally respond to things'
        };
      }
    }
  }
  
  return { isHighRelevance: false, matchType: null };
};

// ============================================
// THEME CONCENTRATION DETECTION
// ============================================

export const detectThemeConcentration = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): ThemeConcentration[] => {
  const chains = buildRulershipChains(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  const themes: { [key: string]: { sources: string[]; label: string } } = {
    'communication': { sources: [], label: 'how you think and express' },
    'relationships': { sources: [], label: 'connection and partnership' },
    'identity': { sources: [], label: 'who you are and how you show up' },
    'security': { sources: [], label: 'safety and resources' },
    'transformation': { sources: [], label: 'depth and change' },
    'career': { sources: [], label: 'work and public role' },
    'meaning': { sources: [], label: 'beliefs and direction' }
  };
  
  for (const house of dominantHouses) {
    if ([3].includes(house)) themes['communication'].sources.push('house concentration');
    if ([7].includes(house)) themes['relationships'].sources.push('house concentration');
    if ([1, 5].includes(house)) themes['identity'].sources.push('house concentration');
    if ([2, 4].includes(house)) themes['security'].sources.push('house concentration');
    if ([8].includes(house)) themes['transformation'].sources.push('house concentration');
    if ([10, 6].includes(house)) themes['career'].sources.push('house concentration');
    if ([9].includes(house)) themes['meaning'].sources.push('house concentration');
  }
  
  for (const chain of chains) {
    if ([3].includes(chain.house) || [3].includes(chain.rulerHouse)) {
      themes['communication'].sources.push('house connection');
    }
    if ([8].includes(chain.house) || [8].includes(chain.rulerHouse)) {
      themes['transformation'].sources.push('house connection');
    }
  }
  
  for (const transit of transits.slice(0, 5)) {
    if (transit.natal_house === 3 || transit.natal_point === 'Mercury') {
      themes['communication'].sources.push('transit');
    }
    if (transit.natal_house === 7 || transit.natal_point === 'Venus') {
      themes['relationships'].sources.push('transit');
    }
    if (transit.natal_house === 8 || transit.natal_point === 'Pluto') {
      themes['transformation'].sources.push('transit');
    }
  }
  
  return Object.entries(themes)
    .filter(([_, data]) => data.sources.length >= 2)
    .map(([theme, data]) => ({
      theme,
      sources: [...new Set(data.sources)],
      count: data.sources.length,
      collapsedLine: `This keeps showing up because ${data.label} is built into how your chart works.`
    }))
    .sort((a, b) => b.count - a.count);
};

// ============================================
// CHAPTER / LONG-CYCLE DETECTION
// ============================================

export const detectChapterTransits = (transits: TransitHit[]): ChapterInfo => {
  const slowTransits = ['Saturn', 'Uranus', 'Neptune', 'Pluto'];
  
  for (const hit of transits.slice(0, 3)) {
    if (slowTransits.includes(hit.transit_point)) {
      const themes: { [key: string]: string } = {
        'Saturn': 'maturation and responsibility',
        'Uranus': 'liberation and disruption',
        'Neptune': 'dissolution and transcendence',
        'Pluto': 'transformation and power'
      };
      
      return {
        hasChapterTransit: true,
        transitPlanet: hit.transit_point,
        natalPoint: hit.natal_point,
        chapterTheme: themes[hit.transit_point] || 'longer-term development'
      };
    }
  }
  
  return {
    hasChapterTransit: false,
    transitPlanet: null,
    natalPoint: null,
    chapterTheme: null
  };
};

// ============================================
// REPEAT PATTERN DETECTION
// ============================================

export const detectRepeatPatterns = (
  chartData: FullChartData | null,
  transits: TransitHit[]
): RepeatPattern => {
  const dominantHouses = getDominantHouses(chartData);
  const dominantPlanets = getDominantPlanets(chartData);
  
  const activatedHouses = transits.slice(0, 3)
    .map(t => t.natal_house)
    .filter((h): h is number => h !== undefined);
  
  const repeatingHouses = activatedHouses.filter(h => dominantHouses.includes(h));
  
  if (repeatingHouses.length > 0) {
    const house = repeatingHouses[0];
    const meaning = HOUSE_MEANINGS[house];
    
    return {
      isRepeating: true,
      repeatedTheme: meaning?.shortLabel || 'this area',
      count: repeatingHouses.length,
      sources: ['natal concentration', 'current transit']
    };
  }
  
  const activatedPlanets = transits.slice(0, 3).map(t => t.natal_point);
  const dominantPlanetNames = dominantPlanets.slice(0, 3).map(p => p.planet);
  const repeatingPlanets = activatedPlanets.filter(p => dominantPlanetNames.includes(p));
  
  if (repeatingPlanets.length > 0) {
    return {
      isRepeating: true,
      repeatedTheme: `${repeatingPlanets[0]} themes`,
      count: repeatingPlanets.length,
      sources: ['natal strength', 'current transit']
    };
  }
  
  return {
    isRepeating: false,
    repeatedTheme: null,
    count: 0,
    sources: []
  };
};

// ============================================
// MAIN LIFE ARENAS
// ============================================

export const getMainLifeArenas = (chartData: FullChartData | null): LifeArena[] => {
  if (!chartData?.natal?.concentrations?.dominant_houses) return [];
  
  const dominantHouses = chartData.natal.concentrations.dominant_houses || [];
  
  const topHouses = dominantHouses.slice(0, 3).map((h: { house: number; planets: string[] }) => ({
    house: h.house,
    planets: h.planets || []
  }));
  
  return topHouses.map(({ house, planets }) => {
    const meaning = HOUSE_MEANINGS[house];
    if (!meaning) return { label: '', shortLabel: '', explanation: '', whenIgnored: '' };
    
    const importantPlanets = ['Sun', 'Moon', 'Saturn', 'Chiron', 'North Node', 'South Node'];
    const presentImportant = planets.filter((p: string) => importantPlanets.includes(p));
    
    let explanation = '';
    if (presentImportant.length >= 2) {
      explanation = `This is a crossroads. Identity, pressure, and growth all concentrate here. Life keeps pulling you back to this arena.`;
    } else if (presentImportant.includes('Sun')) {
      explanation = `Your sense of self lives here. What you experience in this arena shapes who you become.`;
    } else if (presentImportant.includes('Moon')) {
      explanation = `Your emotional baseline is here. When this area shakes, you feel it everywhere.`;
    } else if (presentImportant.includes('Saturn')) {
      explanation = `This is where life asks you to get serious. Maturation happens here—whether you're ready or not.`;
    } else if (presentImportant.includes('Chiron')) {
      explanation = `What hurt you here now makes you useful here. The wound and the gift share the same address.`;
    } else if (presentImportant.includes('North Node')) {
      explanation = `This is growth edge territory. It doesn't come naturally, but it's where you're being pulled.`;
    } else if (planets.length >= 3) {
      explanation = `Multiple parts of you meet here. This is high-traffic territory in your psychology.`;
    } else {
      explanation = meaning.specialty;
    }
    
    return {
      label: meaning.label,
      shortLabel: meaning.shortLabel,
      explanation,
      whenIgnored: meaning.whenIgnored
    };
  }).filter(a => a.label);
};

// ============================================
// PLACEMENTS EXTRACTION
// ============================================

export const extractPlacements = (chartData: FullChartData | null): CorePlacements => {
  if (!chartData?.natal) {
    return { sun: 'Unknown', moon: 'Unknown', ascendant: 'Unknown' };
  }
  
  const { planets, angles, nodes } = chartData.natal;
  
  return {
    sun: planets?.Sun?.sign || 'Unknown',
    sun_house: planets?.Sun?.house,
    moon: planets?.Moon?.sign || 'Unknown',
    moon_house: planets?.Moon?.house,
    ascendant: angles?.asc?.sign || 'Unknown',
    mercury: planets?.Mercury?.sign,
    mercury_house: planets?.Mercury?.house,
    venus: planets?.Venus?.sign,
    venus_house: planets?.Venus?.house,
    mars: planets?.Mars?.sign,
    mars_house: planets?.Mars?.house,
    jupiter: planets?.Jupiter?.sign,
    jupiter_house: planets?.Jupiter?.house,
    saturn: planets?.Saturn?.sign,
    saturn_house: planets?.Saturn?.house,
    chiron: planets?.Chiron?.sign,
    chiron_house: planets?.Chiron?.house,
    north_node: nodes?.north?.sign,
    north_node_house: nodes?.north?.house,
    south_node: nodes?.south?.sign,
    south_node_house: nodes?.south?.house,
  };
};

// ============================================
// ACTIVATED HOUSES
// ============================================

export const getActivatedHouses = (transits: TransitHit[]): number[] => {
  return transits
    .slice(0, 3)
    .map(t => t.natal_house)
    .filter((h): h is number => h !== undefined && h !== null);
};

// ============================================
// HOUSE THEME HELPER
// ============================================

export const getHouseTheme = (house: number): string => {
  return HOUSE_DOMAINS[house] || `House ${house}`;
};

// ============================================
// PLANET IMPORTANCE LINE (for Deep Dive cards)
// ============================================

export const getPlanetImportanceLine = (
  planet: string,
  chartData: FullChartData | null
): string => {
  const chartRuler = getChartRuler(chartData);
  const planetStrengths = buildPlanetStrengths(chartData);
  const dominant = getDominantPlanets(chartData);
  
  const isRuler = chartRuler?.planet === planet;
  const strength = planetStrengths.find(p => p.planet === planet);
  const isDominant = dominant.slice(0, 3).some(p => p.planet === planet);
  
  // Check if part of major chain
  const chains = buildRulershipChains(chartData);
  const isInMajorChain = chains.filter(c => c.ruler === planet && c.house !== c.rulerHouse).length >= 2;
  
  if (isRuler && strength?.strengthLabel === 'strong') {
    return "This is one of the most defining forces in your chart.";
  }
  if (isRuler) {
    return "This shapes how you move through life more than most.";
  }
  if (isDominant && strength?.strengthLabel === 'strong') {
    return "This carries particular weight in how you're built.";
  }
  if (isDominant) {
    return "This carries more structural weight than other factors.";
  }
  if (isInMajorChain) {
    return "This connects multiple areas of your life together.";
  }
  
  return '';
};

// ============================================
// DEBUG HELPERS
// ============================================

export const debugInterpretedChart = (chartData: FullChartData | null): void => {
  if (process.env.NODE_ENV !== 'development') return;
  
  console.log('=== INTERPRETED CHART DEBUG ===');
  console.log('Chart Ruler:', getChartRuler(chartData));
  console.log('Dominant Houses:', getDominantHouses(chartData));
  console.log('Dominant Planets:', getDominantPlanets(chartData));
  console.log('Main Life Arenas:', getMainLifeArenas(chartData));
  console.log('Planet Strengths:', buildPlanetStrengths(chartData));
  console.log('Rulership Chains:', buildRulershipChains(chartData));
  console.log('===============================');
};

export const validateChartInterpretation = (chartData: FullChartData | null): boolean => {
  const chartRuler = getChartRuler(chartData);
  const mainArenas = getMainLifeArenas(chartData);
  const dominantPlanets = getDominantPlanets(chartData);
  
  const isValid = chartRuler !== null || mainArenas.length > 0 || dominantPlanets.length > 0;
  
  if (!isValid && process.env.NODE_ENV === 'development') {
    console.warn('Chart interpretation validation failed - no key data available');
  }
  
  return isValid;
};

// ============================================
// ASPECT PATTERN DETECTION (Master Astrologer v3)
// ============================================

// Planet weights for pattern significance
const PLANET_WEIGHTS: { [key: string]: number } = {
  'Sun': 10, 'Moon': 10, 'Mercury': 5, 'Venus': 5, 'Mars': 6,
  'Jupiter': 6, 'Saturn': 8, 'Uranus': 4, 'Neptune': 4, 'Pluto': 5,
  'North Node': 7, 'South Node': 5, 'Chiron': 6
};

// Aspect types and their qualities
const ASPECT_QUALITIES: { [key: string]: 'tension' | 'flow' | 'dynamic' } = {
  'conjunction': 'dynamic',
  'opposition': 'tension',
  'square': 'tension',
  'trine': 'flow',
  'sextile': 'flow',
  'quincunx': 'tension'
};

// House life area translations
const HOUSE_LIFE_AREAS: { [key: number]: string } = {
  1: 'identity and self-presentation',
  2: 'money, resources, and self-worth',
  3: 'communication, thinking, and daily environment',
  4: 'home, family, and emotional foundation',
  5: 'creativity, romance, and self-expression',
  6: 'work, health, and daily routines',
  7: 'relationships and partnership',
  8: 'intimacy, trust, and transformation',
  9: 'beliefs, meaning, and expansion',
  10: 'career, reputation, and public role',
  11: 'community, friendships, and future vision',
  12: 'unconscious patterns, surrender, and hidden matters'
};

// Get life areas from houses
const getLifeAreasFromHouses = (houses: number[]): string[] => {
  const uniqueHouses = [...new Set(houses)].filter(h => h >= 1 && h <= 12);
  return uniqueHouses.map(h => HOUSE_LIFE_AREAS[h] || `house ${h}`);
};

// ============================================
// STELLIUM / CLUSTER DETECTION
// ============================================

export const detectStelliums = (chartData: FullChartData | null): Stellium[] => {
  if (!chartData?.natal?.planets) return [];
  
  const planets = chartData.natal.planets;
  const stelliums: Stellium[] = [];
  
  // Group by sign
  const bySign: { [sign: string]: { planet: string; house: number }[] } = {};
  // Group by house
  const byHouse: { [house: number]: { planet: string; sign: string }[] } = {};
  
  const relevantPlanets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North Node', 'Chiron'];
  
  for (const planetName of relevantPlanets) {
    const data = planets[planetName];
    if (!data?.sign) continue;
    
    const sign = data.sign;
    const house = data.house || 0;
    
    if (!bySign[sign]) bySign[sign] = [];
    bySign[sign].push({ planet: planetName, house });
    
    if (house > 0) {
      if (!byHouse[house]) byHouse[house] = [];
      byHouse[house].push({ planet: planetName, sign });
    }
  }
  
  // Check sign clusters (3+ planets)
  for (const [sign, planetList] of Object.entries(bySign)) {
    if (planetList.length >= 3) {
      const planetNames = planetList.map(p => p.planet);
      const houses = planetList.map(p => p.house).filter(h => h > 0);
      const uniqueHouses = [...new Set(houses)];
      
      // Calculate concentration score
      let score = planetList.reduce((sum, p) => sum + (PLANET_WEIGHTS[p.planet] || 3), 0);
      if (planetNames.includes('Sun') || planetNames.includes('Moon')) score += 5;
      
      // Psychological summary based on sign element and planets
      const element = SIGN_ELEMENTS[sign] || 'unknown';
      let summary = '';
      
      if (planetNames.includes('Sun') && planetNames.includes('Moon')) {
        summary = `Your sense of self and emotional nature are fused in ${sign}. This creates intensity but also clarity about who you are.`;
      } else if (planetNames.length >= 4) {
        summary = `A significant part of your psychology concentrates through ${sign} ${element} energy. This is a dominant mode of operation.`;
      } else {
        summary = `Multiple parts of you express through ${sign} qualities. This sign isn't just a detail—it's a recurring theme.`;
      }
      
      stelliums.push({
        clusterType: 'sign_cluster',
        sign,
        planets: planetNames,
        concentrationScore: score,
        psychologicalSummary: summary,
        lifeAreas: getLifeAreasFromHouses(uniqueHouses)
      });
    }
  }
  
  // Check house clusters (3+ planets)
  for (const [houseStr, planetList] of Object.entries(byHouse)) {
    const house = parseInt(houseStr);
    if (planetList.length >= 3) {
      const planetNames = planetList.map(p => p.planet);
      
      let score = planetList.reduce((sum, p) => sum + (PLANET_WEIGHTS[p.planet] || 3), 0);
      if (ANGULAR_HOUSES.includes(house)) score += 5;
      
      const houseMeaning = HOUSE_MEANINGS[house];
      let summary = '';
      
      if (planetNames.includes('Sun') || planetNames.includes('Moon')) {
        summary = `Your core identity concentrates in the area of ${houseMeaning?.shortLabel || 'this house'}. Life keeps pulling you back here.`;
      } else {
        summary = `Multiple psychological functions meet in the area of ${houseMeaning?.shortLabel || 'this house'}. This is high-traffic territory.`;
      }
      
      stelliums.push({
        clusterType: 'house_cluster',
        house,
        planets: planetNames,
        concentrationScore: score,
        psychologicalSummary: summary,
        lifeAreas: [HOUSE_LIFE_AREAS[house] || `house ${house}`]
      });
    }
  }
  
  return stelliums.sort((a, b) => b.concentrationScore - a.concentrationScore);
};

// ============================================
// OPPOSITION AXIS DETECTION
// ============================================

export const detectOppositionAxes = (chartData: FullChartData | null): OppositionAxis[] => {
  if (!chartData?.natal?.aspects) return [];
  
  const oppositions = chartData.natal.aspects.filter(a => a.aspect_type === 'opposition');
  if (oppositions.length === 0) return [];
  
  const planets = chartData.natal.planets || {};
  const axes: OppositionAxis[] = [];
  const chartRuler = getChartRuler(chartData);
  
  // Group oppositions by house axis
  const axisByHouses: { [key: string]: { points: string[]; aspects: typeof oppositions }[] } = {};
  
  for (const opp of oppositions) {
    const houseA = planets[opp.point_a]?.house || 0;
    const houseB = planets[opp.point_b]?.house || 0;
    
    // Normalize axis key (always smaller house first)
    const axisKey = houseA < houseB ? `${houseA}-${houseB}` : `${houseB}-${houseA}`;
    
    if (!axisByHouses[axisKey]) axisByHouses[axisKey] = [];
    axisByHouses[axisKey].push({
      points: [opp.point_a, opp.point_b],
      aspects: [opp]
    });
  }
  
  // Find meaningful opposition axes
  for (const [axisKey, oppGroups] of Object.entries(axisByHouses)) {
    const [h1, h2] = axisKey.split('-').map(Number);
    const allPoints = oppGroups.flatMap(g => g.points);
    const uniquePoints = [...new Set(allPoints)];
    
    // Check if axis involves important points
    const importantPoints = ['Sun', 'Moon', 'Saturn', 'North Node', 'Chiron'];
    const hasImportant = uniquePoints.some(p => importantPoints.includes(p));
    const hasChartRuler = chartRuler && uniquePoints.includes(chartRuler.planet);
    
    if (uniquePoints.length >= 2 && (hasImportant || hasChartRuler || oppGroups.length >= 2)) {
      // Calculate pressure score
      let score = uniquePoints.reduce((sum, p) => sum + (PLANET_WEIGHTS[p] || 3), 0);
      if (hasChartRuler) score += 5;
      if (ANGULAR_HOUSES.includes(h1) || ANGULAR_HOUSES.includes(h2)) score += 3;
      
      // Determine axis theme
      let theme = '';
      const axisHouses = [h1, h2];
      
      if ((axisHouses.includes(1) && axisHouses.includes(7)) || axisHouses.includes(7)) {
        theme = 'self vs. other—balancing personal needs with relationship demands';
      } else if ((axisHouses.includes(4) && axisHouses.includes(10))) {
        theme = 'private foundation vs. public role—what you need versus what you show';
      } else if ((axisHouses.includes(2) && axisHouses.includes(8))) {
        theme = 'holding vs. merging—security versus deep transformation';
      } else if ((axisHouses.includes(3) && axisHouses.includes(9))) {
        theme = 'details vs. meaning—local understanding versus big-picture truth';
      } else if ((axisHouses.includes(5) && axisHouses.includes(11))) {
        theme = 'self-expression vs. community—personal creativity versus collective belonging';
      } else if ((axisHouses.includes(6) && axisHouses.includes(12))) {
        theme = 'daily effort vs. surrender—what you control versus what you release';
      } else {
        theme = `tension between ${HOUSE_LIFE_AREAS[h1] || 'one area'} and ${HOUSE_LIFE_AREAS[h2] || 'another'}`;
      }
      
      axes.push({
        axisPoints: uniquePoints.map(p => ({
          planet: p,
          house: planets[p]?.house || 0
        })),
        axisHouses: [h1, h2],
        axisTheme: theme,
        pressureScore: score,
        lifeAreas: getLifeAreasFromHouses([h1, h2])
      });
    }
  }
  
  return axes.sort((a, b) => b.pressureScore - a.pressureScore);
};

// ============================================
// PRESSURE TRIANGLE / T-SQUARE DETECTION
// ============================================

export const detectPressureTriangles = (chartData: FullChartData | null): PressureTriangle[] => {
  if (!chartData?.natal?.aspects) return [];
  
  const aspects = chartData.natal.aspects;
  const planets = chartData.natal.planets || {};
  const triangles: PressureTriangle[] = [];
  
  // Find oppositions first
  const oppositions = aspects.filter(a => a.aspect_type === 'opposition');
  
  // Find squares
  const squares = aspects.filter(a => a.aspect_type === 'square');
  
  // Look for T-square pattern: two planets oppose, both square a third
  for (const opp of oppositions) {
    const oppPlanets = [opp.point_a, opp.point_b];
    
    // Find planets that square both opposition planets
    const focalCandidates = new Set<string>();
    
    for (const sq of squares) {
      if (oppPlanets.includes(sq.point_a)) {
        focalCandidates.add(sq.point_b);
      } else if (oppPlanets.includes(sq.point_b)) {
        focalCandidates.add(sq.point_a);
      }
    }
    
    // Check if any candidate squares both opposition planets
    for (const candidate of focalCandidates) {
      const squaresToOpp = squares.filter(sq =>
        (sq.point_a === candidate && oppPlanets.includes(sq.point_b)) ||
        (sq.point_b === candidate && oppPlanets.includes(sq.point_a))
      );
      
      if (squaresToOpp.length >= 2) {
        // Found a T-square!
        const focalHouse = planets[candidate]?.house || 0;
        const oppHouses = oppPlanets.map(p => planets[p]?.house || 0);
        
        // Calculate intensity
        let score = PLANET_WEIGHTS[candidate] || 3;
        score += oppPlanets.reduce((sum, p) => sum + (PLANET_WEIGHTS[p] || 3), 0);
        if (ANGULAR_HOUSES.includes(focalHouse)) score += 5;
        
        // Determine tension theme based on focal planet
        const themes: { [key: string]: string } = {
          'Sun': 'identity pressure—your sense of self is where the strain collects',
          'Moon': 'emotional pressure—feelings become the release valve',
          'Mercury': 'mental pressure—thinking becomes the focal point of tension',
          'Venus': 'relationship/value pressure—connection and worth carry the strain',
          'Mars': 'action pressure—doing becomes the outlet for accumulated tension',
          'Jupiter': 'expansion pressure—growth and belief become the release point',
          'Saturn': 'responsibility pressure—duty and structure carry the weight',
          'Uranus': 'freedom pressure—the need to break free concentrates here',
          'Neptune': 'dissolution pressure—confusion or transcendence becomes the focus',
          'Pluto': 'transformation pressure—power and depth concentrate here'
        };
        
        const tensionTheme = themes[candidate] || `pressure concentrates through ${candidate}`;
        
        // How it manifests
        const manifestation = `When life activates this pattern, ${candidate.toLowerCase()} themes become the pressure point. ${oppPlanets.join(' and ')} create the underlying split, and ${candidate} is where you feel it most.`;
        
        // Check for duplicates
        const isDuplicate = triangles.some(t => 
          t.focalPlanet === candidate && 
          t.supportingPlanets.sort().join() === oppPlanets.sort().join()
        );
        
        if (!isDuplicate) {
          triangles.push({
            focalPlanet: candidate,
            focalHouse,
            supportingPlanets: oppPlanets,
            tensionTheme,
            intensityScore: score,
            lifeAreas: getLifeAreasFromHouses([focalHouse, ...oppHouses]),
            howItManifests: manifestation
          });
        }
      }
    }
  }
  
  return triangles.sort((a, b) => b.intensityScore - a.intensityScore);
};

// ============================================
// FLOW PATTERN / EASE LOOP DETECTION
// ============================================

export const detectFlowPatterns = (chartData: FullChartData | null): FlowPattern[] => {
  if (!chartData?.natal?.aspects) return [];
  
  const aspects = chartData.natal.aspects;
  const planets = chartData.natal.planets || {};
  const flows: FlowPattern[] = [];
  
  // Find trines and sextiles
  const easyAspects = aspects.filter(a => 
    a.aspect_type === 'trine' || a.aspect_type === 'sextile'
  );
  
  if (easyAspects.length < 2) return [];
  
  // Group connected easy aspects
  const planetConnections: { [planet: string]: string[] } = {};
  
  for (const asp of easyAspects) {
    if (!planetConnections[asp.point_a]) planetConnections[asp.point_a] = [];
    if (!planetConnections[asp.point_b]) planetConnections[asp.point_b] = [];
    
    planetConnections[asp.point_a].push(asp.point_b);
    planetConnections[asp.point_b].push(asp.point_a);
  }
  
  // Find planets with multiple easy connections (part of a flow network)
  const flowNetworks: string[][] = [];
  const visited = new Set<string>();
  
  for (const [planet, connections] of Object.entries(planetConnections)) {
    if (connections.length >= 2 && !visited.has(planet)) {
      // BFS to find connected flow network
      const network: string[] = [];
      const queue = [planet];
      
      while (queue.length > 0) {
        const current = queue.shift()!;
        if (visited.has(current)) continue;
        visited.add(current);
        network.push(current);
        
        for (const connected of (planetConnections[current] || [])) {
          if (!visited.has(connected)) {
            queue.push(connected);
          }
        }
      }
      
      if (network.length >= 3) {
        flowNetworks.push(network);
      }
    }
  }
  
  // Create flow patterns from networks
  for (const network of flowNetworks) {
    const houses = network.map(p => planets[p]?.house || 0).filter(h => h > 0);
    
    // Calculate gift score
    let score = network.reduce((sum, p) => sum + (PLANET_WEIGHTS[p] || 3), 0);
    const hasLuminary = network.includes('Sun') || network.includes('Moon');
    if (hasLuminary) score += 5;
    
    // Determine ease theme
    const elements = network.map(p => SIGN_ELEMENTS[planets[p]?.sign || ''] || '').filter(Boolean);
    const dominantElement = elements.sort((a, b) =>
      elements.filter(e => e === b).length - elements.filter(e => e === a).length
    )[0];
    
    let easeTheme = '';
    let blindSpot = '';
    
    if (dominantElement === 'Fire') {
      easeTheme = 'action and inspiration flow naturally—initiative comes easily';
      blindSpot = 'You may act before fully thinking things through, assuming momentum will carry you.';
    } else if (dominantElement === 'Earth') {
      easeTheme = 'practical grounding flows naturally—building and maintaining comes easily';
      blindSpot = 'You may resist necessary change because stability feels so comfortable.';
    } else if (dominantElement === 'Air') {
      easeTheme = 'thinking and connection flow naturally—ideas and relationships come easily';
      blindSpot = 'You may intellectualize emotions rather than feeling them directly.';
    } else if (dominantElement === 'Water') {
      easeTheme = 'emotional attunement flows naturally—feeling and intuition come easily';
      blindSpot = 'You may absorb others\' emotions without realizing what\'s yours and what isn\'t.';
    } else {
      easeTheme = 'certain psychological functions work together smoothly';
      blindSpot = 'Ease can become complacency—what comes naturally may not be what\'s needed.';
    }
    
    flows.push({
      planetsInvolved: network,
      easeTheme,
      giftScore: score,
      possibleBlindSpot: blindSpot,
      lifeAreas: getLifeAreasFromHouses(houses)
    });
  }
  
  return flows.sort((a, b) => b.giftScore - a.giftScore);
};

// ============================================
// CONJUNCTION CHAIN DETECTION
// ============================================

export const detectConjunctionChains = (chartData: FullChartData | null): ConjunctionChain[] => {
  if (!chartData?.natal?.aspects) return [];
  
  const aspects = chartData.natal.aspects;
  const planets = chartData.natal.planets || {};
  const chains: ConjunctionChain[] = [];
  
  // Find all conjunctions
  const conjunctions = aspects.filter(a => a.aspect_type === 'conjunction');
  if (conjunctions.length < 2) return [];
  
  // Build conjunction graph
  const connections: { [planet: string]: string[] } = {};
  
  for (const conj of conjunctions) {
    if (!connections[conj.point_a]) connections[conj.point_a] = [];
    if (!connections[conj.point_b]) connections[conj.point_b] = [];
    
    connections[conj.point_a].push(conj.point_b);
    connections[conj.point_b].push(conj.point_a);
  }
  
  // Find connected chains
  const visited = new Set<string>();
  
  for (const [planet, connected] of Object.entries(connections)) {
    if (visited.has(planet)) continue;
    
    // BFS to find chain
    const chain: string[] = [];
    const queue = [planet];
    
    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);
      chain.push(current);
      
      for (const next of (connections[current] || [])) {
        if (!visited.has(next)) {
          queue.push(next);
        }
      }
    }
    
    if (chain.length >= 2) {
      const houses = chain.map(p => planets[p]?.house || 0).filter(h => h > 0);
      const uniqueHouses = [...new Set(houses)];
      
      // Calculate compression score
      let score = chain.reduce((sum, p) => sum + (PLANET_WEIGHTS[p] || 3), 0);
      if (chain.length >= 3) score += 5;
      if (chain.includes('Sun') && chain.includes('Moon')) score += 8;
      
      // Determine merged theme based on planets involved
      let theme = '';
      let effect = '';
      
      if (chain.includes('Sun') && chain.includes('Moon')) {
        theme = 'identity and emotions are deeply fused';
        effect = 'What you want and what you feel become almost indistinguishable. This creates intensity but can make it hard to distinguish need from want.';
      } else if (chain.includes('Mercury') && chain.includes('Venus')) {
        theme = 'thinking and relating are merged';
        effect = 'How you think affects your connections; how you connect affects your thinking. Communication and relationship are inseparable.';
      } else if (chain.includes('Mars') && chain.includes('Saturn')) {
        theme = 'action and restraint are bound together';
        effect = 'Drive meets discipline. You may feel like you\'re driving with the brakes on, but this also creates focused, enduring effort.';
      } else if (chain.includes('Sun') && chain.includes('Saturn')) {
        theme = 'identity is bound to responsibility';
        effect = 'Who you are is inseparable from what you must do. Self-worth may feel contingent on achievement.';
      } else if (chain.includes('Moon') && chain.includes('Saturn')) {
        theme = 'emotions are bound to duty';
        effect = 'Feelings get filtered through responsibility. Emotional expression may feel earned rather than free.';
      } else if (chain.includes('Venus') && chain.includes('Saturn')) {
        theme = 'love is bound to commitment';
        effect = 'Connection requires structure. Relationships tend to be serious, and frivolity in love doesn\'t come naturally.';
      } else if (chain.includes('Mercury') && chain.includes('Mars')) {
        theme = 'thinking and action are fused';
        effect = 'Thoughts quickly become actions. This creates directness but may skip important reflection.';
      } else if (chain.length >= 3) {
        theme = 'multiple psychological functions merge into one complex';
        effect = `${chain.join(', ')} operate as a unit. When one is activated, they all activate together.`;
      } else {
        theme = `${chain[0]} and ${chain[1]} are psychologically merged`;
        effect = 'These functions don\'t operate independently—they\'re wired together.';
      }
      
      chains.push({
        planetsInvolved: chain,
        mergedTheme: theme,
        compressionScore: score,
        lifeAreas: getLifeAreasFromHouses(uniqueHouses),
        psychologicalEffect: effect
      });
    }
  }
  
  return chains.sort((a, b) => b.compressionScore - a.compressionScore);
};

// ============================================
// ASPECT PATTERN PRIORITY ENGINE
// ============================================

export const buildAspectPatternAnalysis = (chartData: FullChartData | null): AspectPatternAnalysis => {
  const stelliums = detectStelliums(chartData);
  const oppositionAxes = detectOppositionAxes(chartData);
  const pressureTriangles = detectPressureTriangles(chartData);
  const flowPatterns = detectFlowPatterns(chartData);
  const conjunctionChains = detectConjunctionChains(chartData);
  
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  // Build all patterns with priority scores
  const allPatterns: DominantAspectPattern[] = [];
  
  // Score stelliums
  for (const stellium of stelliums) {
    let score = stellium.concentrationScore;
    if (stellium.planets.includes('Sun') || stellium.planets.includes('Moon')) score += 5;
    if (chartRuler && stellium.planets.includes(chartRuler.planet)) score += 3;
    if (stellium.house && dominantHouses.includes(stellium.house)) score += 3;
    
    const summary = stellium.clusterType === 'sign_cluster'
      ? `A concentration of ${stellium.planets.length} planets in ${stellium.sign} creates a dominant mode of expression.`
      : `${stellium.planets.length} planets cluster in the area of ${HOUSE_LIFE_AREAS[stellium.house || 0] || 'one life domain'}, making it a focal point.`;
    
    allPatterns.push({
      patternType: 'stellium',
      patternData: stellium,
      priorityScore: score,
      relevanceReason: stellium.psychologicalSummary,
      plainLanguageSummary: summary
    });
  }
  
  // Score opposition axes
  for (const axis of oppositionAxes) {
    let score = axis.pressureScore;
    const axisPoints = axis.axisPoints.map(p => p.planet);
    if (axisPoints.includes('Sun') || axisPoints.includes('Moon')) score += 5;
    if (chartRuler && axisPoints.includes(chartRuler.planet)) score += 3;
    if (axis.axisHouses.some(h => ANGULAR_HOUSES.includes(h))) score += 3;
    
    const summary = `An opposition axis creates ongoing tension: ${axis.axisTheme}.`;
    
    allPatterns.push({
      patternType: 'opposition_axis',
      patternData: axis,
      priorityScore: score,
      relevanceReason: `This axis runs through ${axis.lifeAreas.join(' and ')}.`,
      plainLanguageSummary: summary
    });
  }
  
  // Score pressure triangles (T-squares are very significant)
  for (const triangle of pressureTriangles) {
    let score = triangle.intensityScore + 10; // T-squares get a baseline boost
    if (triangle.focalPlanet === 'Sun' || triangle.focalPlanet === 'Moon') score += 5;
    if (chartRuler && triangle.focalPlanet === chartRuler.planet) score += 5;
    if (ANGULAR_HOUSES.includes(triangle.focalHouse)) score += 3;
    if (dominantHouses.includes(triangle.focalHouse)) score += 3;
    
    const summary = `A pressure pattern with ${triangle.focalPlanet} as the focal point—${triangle.tensionTheme}.`;
    
    allPatterns.push({
      patternType: 'pressure_triangle',
      patternData: triangle,
      priorityScore: score,
      relevanceReason: triangle.howItManifests,
      plainLanguageSummary: summary
    });
  }
  
  // Score flow patterns
  for (const flow of flowPatterns) {
    let score = flow.giftScore;
    if (flow.planetsInvolved.includes('Sun') || flow.planetsInvolved.includes('Moon')) score += 3;
    if (chartRuler && flow.planetsInvolved.includes(chartRuler.planet)) score += 2;
    
    const summary = `A flow pattern where ${flow.easeTheme}.`;
    
    allPatterns.push({
      patternType: 'flow_pattern',
      patternData: flow,
      priorityScore: score,
      relevanceReason: flow.possibleBlindSpot,
      plainLanguageSummary: summary
    });
  }
  
  // Score conjunction chains
  for (const chain of conjunctionChains) {
    let score = chain.compressionScore;
    if (chain.planetsInvolved.includes('Sun') || chain.planetsInvolved.includes('Moon')) score += 5;
    if (chartRuler && chain.planetsInvolved.includes(chartRuler.planet)) score += 3;
    
    const summary = `${chain.planetsInvolved.join(' and ')} are conjunct—${chain.mergedTheme}.`;
    
    allPatterns.push({
      patternType: 'conjunction_chain',
      patternData: chain,
      priorityScore: score,
      relevanceReason: chain.psychologicalEffect,
      plainLanguageSummary: summary
    });
  }
  
  // Sort and select dominant patterns
  allPatterns.sort((a, b) => b.priorityScore - a.priorityScore);
  
  const dominantPattern = allPatterns[0] || null;
  const secondaryPatterns = allPatterns.slice(1, 4);
  
  // Build "How Pressure Builds" synthesis
  const howPressureBuilds = buildPressureSynthesis(
    dominantPattern,
    secondaryPatterns,
    stelliums,
    oppositionAxes,
    pressureTriangles,
    flowPatterns,
    conjunctionChains,
    chartData
  );
  
  return {
    stelliums,
    oppositionAxes,
    pressureTriangles,
    flowPatterns,
    conjunctionChains,
    dominantPattern,
    secondaryPatterns,
    howPressureBuilds
  };
};

// ============================================
// BUILD PRESSURE SYNTHESIS
// ============================================

const buildPressureSynthesis = (
  dominant: DominantAspectPattern | null,
  secondary: DominantAspectPattern[],
  stelliums: Stellium[],
  axes: OppositionAxis[],
  triangles: PressureTriangle[],
  flows: FlowPattern[],
  chains: ConjunctionChain[],
  chartData: FullChartData | null
): HowPressureBuilds => {
  const hasTriangle = triangles.length > 0;
  const hasAxis = axes.length > 0;
  const hasStellium = stelliums.length > 0;
  const hasFlow = flows.length > 0;
  const hasChain = chains.length > 0;
  
  const hasSignificantPattern = hasTriangle || (hasAxis && hasStellium) || (hasChain && axes.length > 0);
  
  // Collect all life areas involved in tension patterns
  const tensionAreas = new Set<string>();
  triangles.forEach(t => t.lifeAreas.forEach(a => tensionAreas.add(a)));
  axes.forEach(a => a.lifeAreas.forEach(area => tensionAreas.add(area)));
  chains.forEach(c => c.lifeAreas.forEach(a => tensionAreas.add(a)));
  
  // Collect all life areas involved in ease patterns
  const easeAreas = new Set<string>();
  flows.forEach(f => f.lifeAreas.forEach(a => easeAreas.add(a)));
  
  let mainStatement = '';
  let lifeAreaStatement = '';
  let whatKeepsTightening = '';
  let whereItCollects = '';
  let howItTriesToResolve = '';
  let giftInsideThePressure = '';
  let reflectionQuestion = '';
  let patternType: string | null = null;
  
  if (hasTriangle) {
    const triangle = triangles[0];
    patternType = 'pressure_triangle';
    
    mainStatement = `This chart carries a repeating pressure pattern. When life activates one part of it, the whole configuration responds. The tension doesn't release quickly—it builds until something shifts.`;
    
    lifeAreaStatement = `Most of this pressure collects around ${triangle.lifeAreas.slice(0, 2).join(' and ')}.`;
    
    whatKeepsTightening = `The split between ${triangle.supportingPlanets.join(' and ')} creates ongoing tension. Neither side wins—they pull against each other.`;
    
    whereItCollects = `${triangle.focalPlanet} becomes the pressure point. This is where you feel it—in ${HOUSE_LIFE_AREAS[triangle.focalHouse] || 'this area of life'}.`;
    
    howItTriesToResolve = `Resolution comes through ${triangle.focalPlanet.toLowerCase()} expression—but forced resolution creates more strain. The pattern asks for integration, not elimination.`;
    
    const focalGifts: { [key: string]: string } = {
      'Sun': 'The gift: clarity about what you actually want, forged through the pressure.',
      'Moon': 'The gift: emotional wisdom that only comes from feeling everything.',
      'Mercury': 'The gift: insight and communication depth born from mental pressure.',
      'Venus': 'The gift: relationship wisdom and values clarity earned through strain.',
      'Mars': 'The gift: focused action and courage tested by real resistance.',
      'Saturn': 'The gift: structural integrity and maturity built under pressure.',
      'Jupiter': 'The gift: genuine wisdom and growth that came the hard way.'
    };
    giftInsideThePressure = focalGifts[triangle.focalPlanet] || 'The gift: capacity and depth that only pressure can create.';
    
    reflectionQuestion = `When this pattern activates, do you try to force a resolution—or can you stay with the tension until it teaches you something?`;
    
  } else if (hasAxis && hasStellium) {
    patternType = 'axis_stellium';
    const axis = axes[0];
    const stellium = stelliums[0];
    
    mainStatement = `This chart has concentrated energy in one area, but that concentration is held in tension by an opposition. The intensity doesn't spread evenly—it builds in specific places.`;
    
    lifeAreaStatement = `The concentration is in ${stellium.lifeAreas.join(' and ')}, but it's pulled by tension toward ${axis.lifeAreas.join(' and ')}.`;
    
    whatKeepsTightening = axis.axisTheme;
    whereItCollects = stellium.psychologicalSummary;
    howItTriesToResolve = `The chart keeps trying to balance the concentration with the pull of the opposition. Resolution isn't about choosing one—it's about integrating both.`;
    giftInsideThePressure = `The gift: depth and intensity that comes from having so much energy organized in one pattern.`;
    reflectionQuestion = `Where in your life do you feel pulled between concentration and balance?`;
    
  } else if (hasAxis) {
    patternType = 'opposition_axis';
    const axis = axes[0];
    
    mainStatement = `This chart carries a fundamental split—an opposition that runs through your psychology. The two sides don't naturally agree, and life keeps asking you to balance them.`;
    
    lifeAreaStatement = `This split runs through ${axis.lifeAreas.join(' and ')}.`;
    
    whatKeepsTightening = axis.axisTheme;
    whereItCollects = `The tension concentrates wherever ${axis.axisPoints.map(p => p.planet).join(' and ')} are activated.`;
    howItTriesToResolve = `The chart keeps trying to satisfy both ends. Resolution doesn't mean one side wins—it means you learn to hold both.`;
    giftInsideThePressure = `The gift: perspective and balance that only comes from knowing both sides deeply.`;
    reflectionQuestion = `Which end of this tension do you tend to identify with—and what would it mean to honor the other?`;
    
  } else if (hasChain) {
    patternType = 'conjunction_chain';
    const chain = chains[0];
    
    mainStatement = `This chart has planets fused together—${chain.mergedTheme}. They don't operate separately. When one activates, they all activate.`;
    
    lifeAreaStatement = `This fusion concentrates in ${chain.lifeAreas.join(' and ')}.`;
    
    whatKeepsTightening = chain.psychologicalEffect;
    whereItCollects = `Wherever ${chain.planetsInvolved.join(' and ')} are touched, the whole complex responds.`;
    howItTriesToResolve = `Resolution isn't about separating them—it's about working with them as a unit.`;
    giftInsideThePressure = `The gift: intensity and focus that comes from having these functions merged.`;
    reflectionQuestion = `Can you work with this combination rather than wishing the parts were separate?`;
    
  } else if (hasStellium) {
    patternType = 'stellium';
    const stellium = stelliums[0];
    
    mainStatement = `This chart concentrates energy rather than spreading it. ${stellium.planets.length} planets cluster together, creating intensity in one mode of operation.`;
    
    lifeAreaStatement = `The concentration is in ${stellium.lifeAreas.join(' and ')}.`;
    
    whatKeepsTightening = stellium.psychologicalSummary;
    whereItCollects = `Pressure builds wherever ${stellium.sign || `house ${stellium.house}`} themes are activated.`;
    howItTriesToResolve = `The chart expresses intensely through this concentration. Pressure releases through direct engagement with these themes.`;
    giftInsideThePressure = `The gift: depth and mastery in the concentrated area that wouldn't be possible if energy were spread thin.`;
    reflectionQuestion = `Do you embrace this concentration, or do you sometimes wish you were more balanced?`;
    
  } else if (hasFlow) {
    patternType = 'flow_pattern';
    const flow = flows[0];
    
    mainStatement = `This chart has natural ease in certain areas—${flow.easeTheme}. But ease can become avoidance if it's used to skip the harder work.`;
    
    lifeAreaStatement = `The flow concentrates in ${flow.lifeAreas.join(' and ')}.`;
    
    whatKeepsTightening = `Ironically, what comes easily can create subtle tension if you rely on it too much.`;
    whereItCollects = flow.possibleBlindSpot;
    howItTriesToResolve = `The gift works best when you also do the harder work that doesn't come naturally.`;
    giftInsideThePressure = `The gift: ${flow.easeTheme}.`;
    reflectionQuestion = `Is your ease a genuine strength, or are you using it to avoid something more difficult?`;
    
  } else {
    mainStatement = `This chart doesn't have a single dominant pressure pattern. Energy is distributed rather than concentrated in one structure.`;
    lifeAreaStatement = `Different areas of life carry different weights without one dominating the others.`;
    whatKeepsTightening = `Without a dominant pattern, pressure tends to be situational rather than structural.`;
    whereItCollects = `It varies depending on what's being activated.`;
    howItTriesToResolve = `Flexibility rather than a fixed release point.`;
    giftInsideThePressure = `The gift: adaptability and balance across different life areas.`;
    reflectionQuestion = `How do you respond when pressure does build—without a natural release valve?`;
  }
  
  return {
    mainStatement,
    lifeAreaStatement,
    hasSignificantPattern,
    patternType,
    whatKeepsTightening,
    whereItCollects,
    howItTriesToResolve,
    giftInsideThePressure,
    reflectionQuestion
  };
};

// ============================================
// ENHANCED KEY ASPECTS
// ============================================

export const getEnhancedKeyAspects = (
  chartData: FullChartData | null,
  maxCount: number = 4
): EnhancedKeyAspect[] => {
  if (!chartData?.natal?.aspects) return [];
  
  const aspects = chartData.natal.aspects;
  const planets = chartData.natal.planets || {};
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  const dominantPlanets = getDominantPlanets(chartData);
  
  // Score and enhance each aspect
  const scored = aspects.map(asp => {
    const planetA = asp.point_a;
    const planetB = asp.point_b;
    const houseA = planets[planetA]?.house || 0;
    const houseB = planets[planetB]?.house || 0;
    
    let score = 0;
    
    // Luminaries get priority
    if (planetA === 'Sun' || planetB === 'Sun') score += 10;
    if (planetA === 'Moon' || planetB === 'Moon') score += 10;
    
    // Chart ruler involvement
    if (chartRuler && (planetA === chartRuler.planet || planetB === chartRuler.planet)) score += 8;
    
    // Saturn/Nodes/Chiron involvement
    const developmentalPlanets = ['Saturn', 'North Node', 'South Node', 'Chiron'];
    if (developmentalPlanets.includes(planetA) || developmentalPlanets.includes(planetB)) score += 5;
    
    // Tightness of orb
    if (asp.orb <= 2) score += 5;
    else if (asp.orb <= 5) score += 2;
    
    // Angular house involvement
    if (ANGULAR_HOUSES.includes(houseA) || ANGULAR_HOUSES.includes(houseB)) score += 3;
    
    // Dominant house involvement
    if (dominantHouses.includes(houseA) || dominantHouses.includes(houseB)) score += 3;
    
    // Dominant planet involvement
    const dominantNames = dominantPlanets.slice(0, 3).map(p => p.planet);
    if (dominantNames.includes(planetA) || dominantNames.includes(planetB)) score += 2;
    
    return { aspect: asp, score, houseA, houseB };
  });
  
  // Sort and take top N
  scored.sort((a, b) => b.score - a.score);
  const top = scored.slice(0, maxCount);
  
  return top.map(({ aspect, houseA, houseB }) => {
    const houses = [houseA, houseB].filter(h => h > 0);
    const lifeAreas = getLifeAreasFromHouses(houses);
    const quality = ASPECT_QUALITIES[aspect.aspect_type] || 'dynamic';
    
    // Build human summary
    const summaries: { [key: string]: { [key: string]: string } } = {
      'Sun-Moon': {
        'conjunction': 'Your sense of self and emotional nature are unified—what you want and what you need align.',
        'opposition': 'Your identity and emotions pull in different directions, creating an inner dialogue between want and need.',
        'square': 'Friction between who you are and how you feel. Your wants and needs don\'t easily agree.',
        'trine': 'Your identity and emotions flow together naturally. Self-expression feels emotionally authentic.',
        'sextile': 'Your sense of self and emotional nature support each other when you make the effort.'
      },
      'Mercury-Pluto': {
        'conjunction': 'Thinking has unusual depth, intensity, and penetrating quality.',
        'opposition': 'Mind is drawn to hidden truths but may also obsess or project suspicion.',
        'square': 'Mental intensity that can become obsessive or paranoid under stress.',
        'trine': 'Natural depth in thinking—you see beneath surfaces without trying.',
        'sextile': 'Ability to access deeper understanding when you focus.'
      },
      'Venus-Saturn': {
        'conjunction': 'Love and commitment are fused—relationships are serious matters.',
        'opposition': 'Tension between desire for connection and fear of inadequacy.',
        'square': 'Love feels earned rather than given. Relationship lessons come through difficulty.',
        'trine': 'Loyalty and commitment come naturally. Love deepens over time.',
        'sextile': 'Ability to build lasting relationships when you invest.'
      },
      'Mars-Saturn': {
        'conjunction': 'Action and discipline are fused—drive meets restraint.',
        'opposition': 'Tension between impulse and control. Feeling like you\'re driving with brakes on.',
        'square': 'Frustration between wanting to act and feeling blocked.',
        'trine': 'Focused, enduring effort. Discipline serves action.',
        'sextile': 'Ability to channel drive into structured achievement.'
      },
      'Sun-Saturn': {
        'conjunction': 'Identity is bound to responsibility. Self-worth tied to achievement.',
        'opposition': 'Tension between self-expression and duty.',
        'square': 'Self-doubt and pressure around identity and authority.',
        'trine': 'Natural authority and self-discipline.',
        'sextile': 'Ability to build identity through sustained effort.'
      },
      'Moon-Saturn': {
        'conjunction': 'Emotions filtered through responsibility. Feelings feel earned.',
        'opposition': 'Tension between emotional needs and duty.',
        'square': 'Difficulty with emotional expression. Feelings may feel unsafe.',
        'trine': 'Emotional maturity and stability.',
        'sextile': 'Ability to mature emotionally through experience.'
      }
    };
    
    const key1 = `${aspect.point_a}-${aspect.point_b}`;
    const key2 = `${aspect.point_b}-${aspect.point_a}`;
    const aspectType = aspect.aspect_type;
    
    let humanSummary = summaries[key1]?.[aspectType] || 
                        summaries[key2]?.[aspectType] ||
                        `${aspect.point_a} and ${aspect.point_b} are in ${aspectType}—they ${quality === 'flow' ? 'support' : quality === 'tension' ? 'challenge' : 'intensify'} each other.`;
    
    // Build "why it matters here"
    let whyItMatters = '';
    
    if (lifeAreas.length > 0) {
      const areaStr = lifeAreas.join(' and ');
      if (dominantHouses.includes(houseA) || dominantHouses.includes(houseB)) {
        whyItMatters = `This matters especially because it lands in ${areaStr}—an area already emphasized in your chart.`;
      } else if (ANGULAR_HOUSES.includes(houseA) || ANGULAR_HOUSES.includes(houseB)) {
        whyItMatters = `This is prominent because it involves ${areaStr}—visible, angular territory.`;
      } else {
        whyItMatters = `This plays out in ${areaStr}.`;
      }
    }
    
    const pressureType = quality === 'tension' ? 'pressure' : 
                         quality === 'flow' ? 'flow' : 'complexity';
    
    return {
      aspectPair: `${aspect.point_a} ${aspect.aspect_type} ${aspect.point_b}`,
      humanSummary,
      whyItMattersHere: whyItMatters,
      pressureType,
      involvedHouses: houses,
      lifeAreas
    };
  });
};

// ============================================
// TRANSIT PATTERN ACTIVATION CHECK
// ============================================

export const isPatternActivatedByTransit = (
  patternAnalysis: AspectPatternAnalysis,
  transits: TransitHit[]
): { activated: boolean; activationLine: string } => {
  if (!patternAnalysis.dominantPattern) {
    return { activated: false, activationLine: '' };
  }
  
  const pattern = patternAnalysis.dominantPattern;
  const transitPoints = transits.slice(0, 5).map(t => t.natal_point);
  const transitHouses = transits.slice(0, 5).map(t => t.natal_house).filter(Boolean);
  
  let planetsInPattern: string[] = [];
  let housesInPattern: number[] = [];
  
  if (pattern.patternType === 'pressure_triangle') {
    const triangle = pattern.patternData as PressureTriangle;
    planetsInPattern = [triangle.focalPlanet, ...triangle.supportingPlanets];
    housesInPattern = [triangle.focalHouse];
  } else if (pattern.patternType === 'stellium') {
    const stellium = pattern.patternData as Stellium;
    planetsInPattern = stellium.planets;
    if (stellium.house) housesInPattern = [stellium.house];
  } else if (pattern.patternType === 'opposition_axis') {
    const axis = pattern.patternData as OppositionAxis;
    planetsInPattern = axis.axisPoints.map(p => p.planet);
    housesInPattern = axis.axisHouses;
  } else if (pattern.patternType === 'conjunction_chain') {
    const chain = pattern.patternData as ConjunctionChain;
    planetsInPattern = chain.planetsInvolved;
  }
  
  // Check for activation
  const activatedPlanets = transitPoints.filter(p => planetsInPattern.includes(p));
  const activatedHouses = transitHouses.filter(h => housesInPattern.includes(h));
  
  if (activatedPlanets.length > 0 || activatedHouses.length > 0) {
    let line = '';
    
    if (pattern.patternType === 'pressure_triangle') {
      line = 'This is landing in a part of your chart that already carries built-up pressure.';
    } else if (pattern.patternType === 'opposition_axis') {
      line = 'This is activating an existing tension line in your chart.';
    } else if (pattern.patternType === 'stellium') {
      line = 'This is waking up a concentrated part of your chart—expect amplification.';
    } else if (pattern.patternType === 'conjunction_chain') {
      line = 'This touches a psychological complex in your chart—multiple functions will respond.';
    } else {
      line = 'This is touching a structural pattern in your chart.';
    }
    
    return { activated: true, activationLine: line };
  }
  
  return { activated: false, activationLine: '' };
};

// ============================================
// LIFE CHAPTER DETECTION (Master Astrologer v4)
// ============================================

// Important natal points for chapter detection
const PERSONAL_PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars'];
const CHAPTER_DRIVERS = {
  saturn: ['Saturn'],
  jupiter: ['Jupiter'],
  nodal: ['North Node', 'South Node'],
  chiron: ['Chiron']
};

// Aspect types that indicate strong activation
const STRONG_ASPECTS = ['conjunction', 'opposition', 'square'];
const MEDIUM_ASPECTS = ['trine', 'sextile'];

// Get life areas from houses
const getLifeAreasForChapter = (houses: number[]): string[] => {
  const HOUSE_LIFE_AREAS: { [key: number]: string } = {
    1: 'identity and self-presentation',
    2: 'money, resources, and self-worth',
    3: 'communication, thinking, and daily environment',
    4: 'home, family, and emotional foundation',
    5: 'creativity, romance, and self-expression',
    6: 'work, health, and daily routines',
    7: 'relationships and partnership',
    8: 'intimacy, trust, and transformation',
    9: 'beliefs, meaning, and expansion',
    10: 'career, reputation, and public role',
    11: 'community, friendships, and future vision',
    12: 'unconscious patterns, surrender, and hidden matters'
  };
  
  const uniqueHouses = [...new Set(houses)].filter(h => h >= 1 && h <= 12);
  return uniqueHouses.map(h => HOUSE_LIFE_AREAS[h] || `house ${h}`);
};

// Detect Saturn Chapter
const detectSaturnChapter = (chartData: FullChartData | null): LifeChapter => {
  const defaultChapter: LifeChapter = {
    chapterType: 'saturn',
    isActive: false,
    strengthScore: 0,
    natalPointsInvolved: [],
    lifeAreas: [],
    housesInvolved: [],
    activations: [],
    themeSummary: ''
  };
  
  if (!chartData?.transits?.strongest_hits) return defaultChapter;
  
  const transits = chartData.transits.strongest_hits;
  const planets = chartData.natal?.planets || {};
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  const activations: ChapterActivation[] = [];
  const natalPointsInvolved: string[] = [];
  const housesInvolved: number[] = [];
  let score = 0;
  
  // Find Saturn transits
  for (const hit of transits) {
    if (hit.transit_point !== 'Saturn') continue;
    
    const natalPoint = hit.natal_point;
    const house = hit.natal_house || planets[natalPoint]?.house || 0;
    const isStrongAspect = STRONG_ASPECTS.includes(hit.aspect_type);
    const isMediumAspect = MEDIUM_ASPECTS.includes(hit.aspect_type);
    
    // Calculate hit importance
    let hitScore = 0;
    
    // Personal planets are high value
    if (PERSONAL_PLANETS.includes(natalPoint)) {
      hitScore += isStrongAspect ? 15 : isMediumAspect ? 8 : 5;
    }
    
    // Chart ruler is very high value
    if (chartRuler && natalPoint === chartRuler.planet) {
      hitScore += isStrongAspect ? 20 : 12;
    }
    
    // Dominant houses add significance
    if (dominantHouses.includes(house)) {
      hitScore += 5;
    }
    
    // Angular houses (1, 4, 7, 10) are prominent
    if (ANGULAR_HOUSES.includes(house)) {
      hitScore += 5;
    }
    
    // Orb tightness bonus
    if (hit.orb <= 2) hitScore += 5;
    else if (hit.orb <= 5) hitScore += 2;
    
    // Applying aspect bonus
    if (hit.applying) hitScore += 3;
    
    if (hitScore > 0) {
      activations.push({
        transitPoint: 'Saturn',
        natalPoint,
        aspectType: hit.aspect_type,
        orb: hit.orb,
        house,
        isApplying: hit.applying
      });
      
      if (!natalPointsInvolved.includes(natalPoint)) {
        natalPointsInvolved.push(natalPoint);
      }
      if (house > 0 && !housesInvolved.includes(house)) {
        housesInvolved.push(house);
      }
      
      score += hitScore;
    }
  }
  
  const isActive = score >= 10;
  
  // Build theme summary
  let themeSummary = '';
  if (isActive) {
    if (natalPointsInvolved.includes('Sun')) {
      themeSummary = 'Saturn is working on your core identity—testing what you claim to be.';
    } else if (natalPointsInvolved.includes('Moon')) {
      themeSummary = 'Saturn is working on your emotional life—asking what you truly need versus what you cling to.';
    } else if (chartRuler && natalPointsInvolved.includes(chartRuler.planet)) {
      themeSummary = 'Saturn is working on the core of your chart—pressing on how you meet life.';
    } else if (housesInvolved.some(h => [4, 10].includes(h))) {
      themeSummary = 'Saturn is restructuring your foundation and your place in the world.';
    } else if (housesInvolved.some(h => [1, 7].includes(h))) {
      themeSummary = 'Saturn is testing your sense of self and your closest relationships.';
    } else {
      themeSummary = 'Saturn is applying pressure to specific areas of your life, demanding maturation.';
    }
  }
  
  return {
    chapterType: 'saturn',
    isActive,
    strengthScore: score,
    natalPointsInvolved,
    lifeAreas: getLifeAreasForChapter(housesInvolved),
    housesInvolved,
    activations,
    themeSummary
  };
};

// Detect Jupiter Chapter
const detectJupiterChapter = (chartData: FullChartData | null): LifeChapter => {
  const defaultChapter: LifeChapter = {
    chapterType: 'jupiter',
    isActive: false,
    strengthScore: 0,
    natalPointsInvolved: [],
    lifeAreas: [],
    housesInvolved: [],
    activations: [],
    themeSummary: ''
  };
  
  if (!chartData?.transits?.strongest_hits) return defaultChapter;
  
  const transits = chartData.transits.strongest_hits;
  const planets = chartData.natal?.planets || {};
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  const activations: ChapterActivation[] = [];
  const natalPointsInvolved: string[] = [];
  const housesInvolved: number[] = [];
  let score = 0;
  
  // Find Jupiter transits
  for (const hit of transits) {
    if (hit.transit_point !== 'Jupiter') continue;
    
    const natalPoint = hit.natal_point;
    const house = hit.natal_house || planets[natalPoint]?.house || 0;
    const isStrongAspect = STRONG_ASPECTS.includes(hit.aspect_type);
    const isMediumAspect = MEDIUM_ASPECTS.includes(hit.aspect_type);
    
    let hitScore = 0;
    
    // Personal planets
    if (PERSONAL_PLANETS.includes(natalPoint)) {
      hitScore += isStrongAspect ? 12 : isMediumAspect ? 7 : 4;
    }
    
    // Chart ruler
    if (chartRuler && natalPoint === chartRuler.planet) {
      hitScore += isStrongAspect ? 15 : 10;
    }
    
    // Dominant houses
    if (dominantHouses.includes(house)) {
      hitScore += 5;
    }
    
    // 9th house (Jupiter's natural home) or angular
    if (house === 9) hitScore += 5;
    if (ANGULAR_HOUSES.includes(house)) hitScore += 3;
    
    // Orb bonus
    if (hit.orb <= 2) hitScore += 4;
    else if (hit.orb <= 5) hitScore += 2;
    
    if (hit.applying) hitScore += 2;
    
    if (hitScore > 0) {
      activations.push({
        transitPoint: 'Jupiter',
        natalPoint,
        aspectType: hit.aspect_type,
        orb: hit.orb,
        house,
        isApplying: hit.applying
      });
      
      if (!natalPointsInvolved.includes(natalPoint)) {
        natalPointsInvolved.push(natalPoint);
      }
      if (house > 0 && !housesInvolved.includes(house)) {
        housesInvolved.push(house);
      }
      
      score += hitScore;
    }
  }
  
  const isActive = score >= 8;
  
  let themeSummary = '';
  if (isActive) {
    if (natalPointsInvolved.includes('Sun')) {
      themeSummary = 'Jupiter is expanding your sense of self—opportunities to grow into more of who you are.';
    } else if (natalPointsInvolved.includes('Moon')) {
      themeSummary = 'Jupiter is expanding your emotional world—more openness, more possibility in how you feel.';
    } else if (chartRuler && natalPointsInvolved.includes(chartRuler.planet)) {
      themeSummary = 'Jupiter is opening doors at the core of your chart—a period of expansion in how you meet life.';
    } else if (housesInvolved.some(h => [9, 3].includes(h))) {
      themeSummary = 'Jupiter is expanding your beliefs and understanding—a period of learning and meaning-making.';
    } else if (housesInvolved.some(h => [2, 8].includes(h))) {
      themeSummary = 'Jupiter is expanding your resources and depths—growth in what you have and what you share.';
    } else {
      themeSummary = 'Jupiter is bringing expansion and opportunity to specific areas of your life.';
    }
  }
  
  return {
    chapterType: 'jupiter',
    isActive,
    strengthScore: score,
    natalPointsInvolved,
    lifeAreas: getLifeAreasForChapter(housesInvolved),
    housesInvolved,
    activations,
    themeSummary
  };
};

// Detect Nodal Chapter
const detectNodalChapter = (chartData: FullChartData | null): LifeChapter => {
  const defaultChapter: LifeChapter = {
    chapterType: 'nodal',
    isActive: false,
    strengthScore: 0,
    natalPointsInvolved: [],
    lifeAreas: [],
    housesInvolved: [],
    activations: [],
    themeSummary: ''
  };
  
  if (!chartData?.transits?.strongest_hits) return defaultChapter;
  
  const transits = chartData.transits.strongest_hits;
  const planets = chartData.natal?.planets || {};
  const nodes = chartData.natal?.nodes;
  const angles = chartData.natal?.angles;
  
  const activations: ChapterActivation[] = [];
  const natalPointsInvolved: string[] = [];
  const housesInvolved: number[] = [];
  let score = 0;
  
  // Find Nodal transits (both North Node and South Node)
  for (const hit of transits) {
    if (hit.transit_point !== 'North Node' && hit.transit_point !== 'South Node') continue;
    
    const natalPoint = hit.natal_point;
    const house = hit.natal_house || planets[natalPoint]?.house || 0;
    const isStrongAspect = STRONG_ASPECTS.includes(hit.aspect_type);
    
    let hitScore = 0;
    
    // Nodal return or square (nodes touching natal nodes) is very significant
    if (natalPoint === 'North Node' || natalPoint === 'South Node') {
      hitScore += hit.aspect_type === 'conjunction' ? 25 : isStrongAspect ? 18 : 10;
    }
    
    // Sun/Moon activation
    if (natalPoint === 'Sun' || natalPoint === 'Moon') {
      hitScore += isStrongAspect ? 20 : 12;
    }
    
    // Angle activation (Asc, MC)
    if (natalPoint === 'Ascendant' || natalPoint === 'MC') {
      hitScore += isStrongAspect ? 15 : 8;
    }
    
    // Personal planets
    if (PERSONAL_PLANETS.includes(natalPoint) && natalPoint !== 'Sun' && natalPoint !== 'Moon') {
      hitScore += isStrongAspect ? 10 : 5;
    }
    
    // Orb bonus
    if (hit.orb <= 2) hitScore += 5;
    else if (hit.orb <= 5) hitScore += 2;
    
    if (hitScore > 0) {
      activations.push({
        transitPoint: hit.transit_point,
        natalPoint,
        aspectType: hit.aspect_type,
        orb: hit.orb,
        house,
        isApplying: hit.applying
      });
      
      if (!natalPointsInvolved.includes(natalPoint)) {
        natalPointsInvolved.push(natalPoint);
      }
      if (house > 0 && !housesInvolved.includes(house)) {
        housesInvolved.push(house);
      }
      
      score += hitScore;
    }
  }
  
  const isActive = score >= 12;
  
  let themeSummary = '';
  if (isActive) {
    const hasNodalReturn = activations.some(a => 
      (a.natalPoint === 'North Node' || a.natalPoint === 'South Node') && 
      a.aspectType === 'conjunction'
    );
    const hasNodalSquare = activations.some(a => 
      (a.natalPoint === 'North Node' || a.natalPoint === 'South Node') && 
      a.aspectType === 'square'
    );
    
    if (hasNodalReturn) {
      themeSummary = 'A nodal return—a major pivot point where you are asked to realign with your deeper direction.';
    } else if (hasNodalSquare) {
      themeSummary = 'A nodal square—a crossroads where old patterns and new directions create tension.';
    } else if (natalPointsInvolved.includes('Sun')) {
      themeSummary = 'The nodes are activating your identity—questions about direction and purpose are front and center.';
    } else if (natalPointsInvolved.includes('Moon')) {
      themeSummary = 'The nodes are activating your emotional life—what you need is being asked to evolve.';
    } else {
      themeSummary = 'The nodes are activating key points in your chart—a phase of directional recalibration.';
    }
  }
  
  return {
    chapterType: 'nodal',
    isActive,
    strengthScore: score,
    natalPointsInvolved,
    lifeAreas: getLifeAreasForChapter(housesInvolved),
    housesInvolved,
    activations,
    themeSummary
  };
};

// Detect Chiron Chapter
const detectChironChapter = (chartData: FullChartData | null): LifeChapter => {
  const defaultChapter: LifeChapter = {
    chapterType: 'chiron',
    isActive: false,
    strengthScore: 0,
    natalPointsInvolved: [],
    lifeAreas: [],
    housesInvolved: [],
    activations: [],
    themeSummary: ''
  };
  
  if (!chartData?.transits?.strongest_hits) return defaultChapter;
  
  const transits = chartData.transits.strongest_hits;
  const planets = chartData.natal?.planets || {};
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  const activations: ChapterActivation[] = [];
  const natalPointsInvolved: string[] = [];
  const housesInvolved: number[] = [];
  let score = 0;
  
  // Find Chiron transits
  for (const hit of transits) {
    if (hit.transit_point !== 'Chiron') continue;
    
    const natalPoint = hit.natal_point;
    const house = hit.natal_house || planets[natalPoint]?.house || 0;
    const isStrongAspect = STRONG_ASPECTS.includes(hit.aspect_type);
    const isMediumAspect = MEDIUM_ASPECTS.includes(hit.aspect_type);
    
    let hitScore = 0;
    
    // Chiron return (natal Chiron) is very significant
    if (natalPoint === 'Chiron') {
      hitScore += hit.aspect_type === 'conjunction' ? 30 : isStrongAspect ? 20 : 10;
    }
    
    // Personal planets
    if (PERSONAL_PLANETS.includes(natalPoint)) {
      hitScore += isStrongAspect ? 12 : isMediumAspect ? 7 : 4;
    }
    
    // Chart ruler
    if (chartRuler && natalPoint === chartRuler.planet) {
      hitScore += isStrongAspect ? 15 : 8;
    }
    
    // Dominant houses
    if (dominantHouses.includes(house)) {
      hitScore += 5;
    }
    
    // Orb bonus
    if (hit.orb <= 2) hitScore += 4;
    else if (hit.orb <= 5) hitScore += 2;
    
    if (hitScore > 0) {
      activations.push({
        transitPoint: 'Chiron',
        natalPoint,
        aspectType: hit.aspect_type,
        orb: hit.orb,
        house,
        isApplying: hit.applying
      });
      
      if (!natalPointsInvolved.includes(natalPoint)) {
        natalPointsInvolved.push(natalPoint);
      }
      if (house > 0 && !housesInvolved.includes(house)) {
        housesInvolved.push(house);
      }
      
      score += hitScore;
    }
  }
  
  const isActive = score >= 10;
  
  let themeSummary = '';
  if (isActive) {
    const hasChironReturn = activations.some(a => 
      a.natalPoint === 'Chiron' && a.aspectType === 'conjunction'
    );
    
    if (hasChironReturn) {
      themeSummary = 'A Chiron return—a deep healing passage where old wounds can transform into wisdom.';
    } else if (natalPointsInvolved.includes('Sun')) {
      themeSummary = 'Chiron is working on your identity—bringing up old vulnerabilities to be understood differently.';
    } else if (natalPointsInvolved.includes('Moon')) {
      themeSummary = 'Chiron is working on your emotional life—sensitive places asking for integration, not fixing.';
    } else if (natalPointsInvolved.includes('Venus')) {
      themeSummary = 'Chiron is working on your relational life—old patterns of connection asking to be healed.';
    } else {
      themeSummary = 'Chiron is bringing something sensitive forward—a phase of integration and healing.';
    }
  }
  
  return {
    chapterType: 'chiron',
    isActive,
    strengthScore: score,
    natalPointsInvolved,
    lifeAreas: getLifeAreasForChapter(housesInvolved),
    housesInvolved,
    activations,
    themeSummary
  };
};

// ============================================
// BUILD LIFE CHAPTER ANALYSIS
// ============================================

export const buildLifeChapterAnalysis = (chartData: FullChartData | null): LifeChapterAnalysis => {
  const saturnChapter = detectSaturnChapter(chartData);
  const jupiterChapter = detectJupiterChapter(chartData);
  const nodalChapter = detectNodalChapter(chartData);
  const chironChapter = detectChironChapter(chartData);
  
  // Collect all active chapters
  const allChapters = [saturnChapter, jupiterChapter, nodalChapter, chironChapter];
  const activeChapters = allChapters.filter(c => c.isActive);
  
  // Sort by strength score
  activeChapters.sort((a, b) => b.strengthScore - a.strengthScore);
  
  const primaryChapter = activeChapters[0] || null;
  const secondaryChapter = activeChapters[1] || null;
  
  return {
    chapters: {
      saturn: saturnChapter,
      jupiter: jupiterChapter,
      nodal: nodalChapter,
      chiron: chironChapter
    },
    primaryChapter,
    secondaryChapter,
    hasActiveChapter: activeChapters.length > 0
  };
};

// ============================================
// BUILD LIFE CHAPTER NARRATIVE
// ============================================

export const buildLifeChapterNarrative = (
  chapter: LifeChapter | null,
  patternAnalysis?: AspectPatternAnalysis | null
): LifeChapterNarrative | null => {
  if (!chapter || !chapter.isActive) return null;
  
  // Check for overlap with dominant aspect patterns
  const hasPatternOverlap = patternAnalysis?.dominantPattern && 
    chapter.lifeAreas.some(area => 
      patternAnalysis.dominantPattern?.patternData && 
      'lifeAreas' in patternAnalysis.dominantPattern.patternData &&
      (patternAnalysis.dominantPattern.patternData as any).lifeAreas?.includes(area)
    );
  
  // Saturn narratives
  if (chapter.chapterType === 'saturn') {
    const titles = [
      'A phase of restructuring',
      'A season of pressure and pruning',
      'A time of necessary discipline'
    ];
    
    const coreDescriptions = [
      'This is a phase where life stops letting things slide. What used to work without structure now demands something more solid.',
      'Saturn is moving through territory that matters to you—pressing on what needs to mature.',
      'This is not a punishment; it is a construction phase. What gets built now will last.'
    ];
    
    const askings = [
      'This phase is asking you to take responsibility for what you\'ve been avoiding.',
      'It wants you to commit to something real—not because it\'s easy, but because it\'s necessary.',
      'You are being asked to show up as an adult in areas where you\'ve been coasting.'
    ];
    
    const resistances = [
      'If resisted, this phase tends to create delays, blockages, and a feeling of being stuck.',
      'Resistance here usually shows up as increased pressure until you face what\'s being asked.',
      'Avoiding Saturn typically means it returns later—harder.'
    ];
    
    // Select based on what natal points are involved
    let idx = 0;
    if (chapter.natalPointsInvolved.includes('Sun')) idx = 0;
    else if (chapter.natalPointsInvolved.includes('Moon')) idx = 1;
    else idx = 2;
    
    return {
      chapterTitle: titles[idx] || titles[0],
      coreDescription: coreDescriptions[idx] || coreDescriptions[0],
      whatPhaseIsAsking: askings[idx] || askings[0],
      whatHappensIfResisted: resistances[idx] || resistances[0],
      shortContextLine: 'a longer phase of restructuring'
    };
  }
  
  // Jupiter narratives
  if (chapter.chapterType === 'jupiter') {
    const titles = [
      'A phase of expansion',
      'A season of opportunity',
      'A time of growth'
    ];
    
    const coreDescriptions = [
      'This is a phase where growth is available—but only if you\'re willing to step beyond what feels contained.',
      'Jupiter is bringing expansion to areas that have been waiting for room to breathe.',
      'Doors are opening. The question is whether you\'ll walk through them.'
    ];
    
    const askings = [
      'This phase is asking you to think bigger than you have been.',
      'It wants you to say yes to something that stretches you.',
      'You are being invited to believe in more than what\'s been safe.'
    ];
    
    const resistances = [
      'If resisted, this phase can feel like restlessness without direction.',
      'Avoiding Jupiter\'s invitations can lead to a vague sense that something is passing you by.',
      'Growth refused tends to show up as stagnation or missed timing.'
    ];
    
    let idx = 0;
    if (chapter.natalPointsInvolved.includes('Sun')) idx = 0;
    else if (chapter.housesInvolved.some(h => [9, 3].includes(h))) idx = 1;
    else idx = 2;
    
    return {
      chapterTitle: titles[idx] || titles[0],
      coreDescription: coreDescriptions[idx] || coreDescriptions[0],
      whatPhaseIsAsking: askings[idx] || askings[0],
      whatHappensIfResisted: resistances[idx] || resistances[0],
      shortContextLine: 'a period of expansion'
    };
  }
  
  // Nodal narratives
  if (chapter.chapterType === 'nodal') {
    const hasReturn = chapter.activations.some(a => 
      (a.natalPoint === 'North Node' || a.natalPoint === 'South Node') && 
      a.aspectType === 'conjunction'
    );
    
    const titles = hasReturn 
      ? ['A major turning point', 'A pivot in your path']
      : ['A shift in direction', 'A season of recalibration'];
    
    const coreDescriptions = hasReturn
      ? [
          'This is a nodal return—a rare recalibration of your life\'s direction. What once felt natural may no longer be enough.',
          'You are at a pivot point. The nodes are asking: have you been moving toward what matters?'
        ]
      : [
          'This is a phase of redirection. What once felt natural may no longer be enough.',
          'The nodes are activating—your sense of where you\'re headed is being updated.'
        ];
    
    const askings = [
      'This phase is asking you to let go of patterns that have served their purpose.',
      'It wants you to move toward what feels unfamiliar but right.'
    ];
    
    const resistances = [
      'If resisted, this phase can feel like being pulled in two directions at once.',
      'Ignoring nodal shifts tends to create a growing sense of being off-track.'
    ];
    
    return {
      chapterTitle: titles[0] || 'A shift in direction',
      coreDescription: coreDescriptions[0] || coreDescriptions[1],
      whatPhaseIsAsking: askings[0] || askings[1],
      whatHappensIfResisted: resistances[0] || resistances[1],
      shortContextLine: 'a shift in direction'
    };
  }
  
  // Chiron narratives
  if (chapter.chapterType === 'chiron') {
    const hasReturn = chapter.activations.some(a => 
      a.natalPoint === 'Chiron' && a.aspectType === 'conjunction'
    );
    
    const titles = hasReturn
      ? ['A deep healing passage', 'The Chiron return']
      : ['A phase of healing', 'A time of integration'];
    
    const coreDescriptions = hasReturn
      ? [
          'This is a Chiron return—a rare passage where old wounds can transform into wisdom. What you\'ve carried can now become what you offer.',
          'Chiron is returning to its natal position. This is about integrating what you\'ve learned from your pain.'
        ]
      : [
          'This is a phase where something sensitive is being brought forward—not to weaken you, but to be understood differently.',
          'Chiron is activating old patterns. This isn\'t about fixing; it\'s about holding what\'s always been tender.'
        ];
    
    const askings = [
      'This phase is asking you to be with what you\'ve been avoiding.',
      'It wants you to stop trying to fix the wound and instead let it teach you.'
    ];
    
    const resistances = [
      'If resisted, this phase tends to surface the same patterns in louder ways.',
      'Avoiding Chiron usually means the sensitivity shows up elsewhere, often through the body or relationships.'
    ];
    
    return {
      chapterTitle: titles[0] || 'A phase of healing',
      coreDescription: coreDescriptions[0] || coreDescriptions[1],
      whatPhaseIsAsking: askings[0] || askings[1],
      whatHappensIfResisted: resistances[0] || resistances[1],
      shortContextLine: 'an ongoing healing process'
    };
  }
  
  return null;
};

// ============================================
// GET CHAPTER CONTEXT LINE FOR TODAY/WEEK/MONTH
// ============================================

export const getChapterContextLine = (
  chapterAnalysis: LifeChapterAnalysis | null,
  timeframe: 'today' | 'week' | 'month' = 'today'
): string | null => {
  if (!chapterAnalysis?.hasActiveChapter || !chapterAnalysis.primaryChapter) {
    return null;
  }
  
  const chapter = chapterAnalysis.primaryChapter;
  const narrative = buildLifeChapterNarrative(chapter);
  
  if (!narrative) return null;
  
  // Only show for strong chapters
  if (chapter.strengthScore < 15) return null;
  
  // Format based on timeframe
  if (timeframe === 'today') {
    return `This isn't just about today—this is part of ${narrative.shortContextLine} you're moving through.`;
  } else if (timeframe === 'week') {
    return `This week sits inside ${narrative.shortContextLine}—a larger phase of your life.`;
  } else {
    return `This month is part of ${narrative.shortContextLine}.`;
  }
};

// ============================================
// DOMINANT TRUTH ENGINE (Master Astrologer v5)
// ============================================

// Theme detection based on house/planet combinations
const THEME_INDICATORS: { [key in ThemeCategory]: {
  houses: number[];
  planets: string[];
  aspects: string[];
  chapters: ChapterType[];
  patterns: string[];
} } = {
  overcommitment: {
    houses: [6, 10, 1],
    planets: ['Saturn', 'Mars', 'Jupiter'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn'],
    patterns: ['pressure_triangle', 'stellium']
  },
  avoidance: {
    houses: [12, 4, 8],
    planets: ['Neptune', 'Moon', 'Pluto'],
    aspects: ['square', 'opposition'],
    chapters: ['nodal', 'chiron'],
    patterns: ['opposition_axis']
  },
  premature_action: {
    houses: [1, 5, 9],
    planets: ['Mars', 'Jupiter', 'Uranus'],
    aspects: ['conjunction', 'square'],
    chapters: ['jupiter'],
    patterns: ['conjunction_chain']
  },
  delayed_decision: {
    houses: [7, 4, 12],
    planets: ['Saturn', 'Neptune', 'Moon'],
    aspects: ['opposition', 'square'],
    chapters: ['saturn', 'nodal'],
    patterns: ['opposition_axis', 'pressure_triangle']
  },
  emotional_suppression: {
    houses: [4, 8, 12],
    planets: ['Moon', 'Saturn', 'Pluto'],
    aspects: ['square', 'opposition', 'conjunction'],
    chapters: ['saturn', 'chiron'],
    patterns: ['pressure_triangle']
  },
  boundary_erosion: {
    houses: [7, 1, 12],
    planets: ['Neptune', 'Venus', 'Moon'],
    aspects: ['conjunction', 'opposition'],
    chapters: ['nodal', 'chiron'],
    patterns: ['conjunction_chain', 'flow_pattern']
  },
  identity_confusion: {
    houses: [1, 12, 4],
    planets: ['Neptune', 'Sun', 'Moon'],
    aspects: ['square', 'opposition', 'conjunction'],
    chapters: ['nodal', 'chiron'],
    patterns: ['opposition_axis']
  },
  relationship_strain: {
    houses: [7, 8, 5],
    planets: ['Venus', 'Mars', 'Saturn'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn', 'chiron'],
    patterns: ['pressure_triangle', 'opposition_axis']
  },
  financial_pressure: {
    houses: [2, 8, 6],
    planets: ['Saturn', 'Pluto', 'Jupiter'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn'],
    patterns: ['pressure_triangle']
  },
  health_neglect: {
    houses: [6, 1, 12],
    planets: ['Mars', 'Saturn', 'Neptune'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn', 'chiron'],
    patterns: ['stellium']
  },
  communication_breakdown: {
    houses: [3, 7, 9],
    planets: ['Mercury', 'Saturn', 'Pluto'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn'],
    patterns: ['pressure_triangle']
  },
  control_grip: {
    houses: [8, 10, 1],
    planets: ['Pluto', 'Saturn', 'Mars'],
    aspects: ['conjunction', 'square'],
    chapters: ['saturn'],
    patterns: ['conjunction_chain', 'pressure_triangle']
  },
  trust_issues: {
    houses: [8, 7, 12],
    planets: ['Pluto', 'Saturn', 'Neptune'],
    aspects: ['square', 'opposition'],
    chapters: ['chiron', 'saturn'],
    patterns: ['opposition_axis']
  },
  purpose_drift: {
    houses: [9, 10, 12],
    planets: ['Jupiter', 'Neptune', 'Saturn'],
    aspects: ['square', 'opposition'],
    chapters: ['nodal', 'jupiter'],
    patterns: ['opposition_axis']
  },
  creative_block: {
    houses: [5, 12, 10],
    planets: ['Saturn', 'Neptune', 'Sun'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn', 'chiron'],
    patterns: ['pressure_triangle']
  },
  isolation: {
    houses: [12, 4, 11],
    planets: ['Saturn', 'Neptune', 'Moon'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn', 'chiron'],
    patterns: ['stellium']
  },
  people_pleasing: {
    houses: [7, 1, 11],
    planets: ['Venus', 'Neptune', 'Moon'],
    aspects: ['conjunction', 'opposition'],
    chapters: ['chiron', 'nodal'],
    patterns: ['conjunction_chain', 'flow_pattern']
  },
  perfectionism: {
    houses: [6, 10, 1],
    planets: ['Saturn', 'Mercury', 'Pluto'],
    aspects: ['conjunction', 'square'],
    chapters: ['saturn'],
    patterns: ['conjunction_chain', 'pressure_triangle']
  },
  procrastination: {
    houses: [12, 6, 3],
    planets: ['Neptune', 'Saturn', 'Mercury'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn', 'nodal'],
    patterns: ['opposition_axis']
  },
  overwhelm: {
    houses: [6, 12, 4],
    planets: ['Moon', 'Neptune', 'Saturn'],
    aspects: ['square', 'opposition', 'conjunction'],
    chapters: ['saturn', 'chiron'],
    patterns: ['stellium', 'pressure_triangle']
  }
};

// Life area translations
const THEME_LIFE_AREAS: { [key in ThemeCategory]: string } = {
  overcommitment: 'what you\'re carrying',
  avoidance: 'what you\'re not looking at',
  premature_action: 'where you\'re rushing',
  delayed_decision: 'what you\'re putting off',
  emotional_suppression: 'what you\'re holding in',
  boundary_erosion: 'where you\'re giving yourself away',
  identity_confusion: 'who you\'re trying to be',
  relationship_strain: 'how you\'re relating',
  financial_pressure: 'your resources and security',
  health_neglect: 'your body and daily life',
  communication_breakdown: 'what\'s not being said',
  control_grip: 'what you\'re trying to control',
  trust_issues: 'what you\'re not trusting',
  purpose_drift: 'your sense of direction',
  creative_block: 'what\'s not flowing',
  isolation: 'where you\'ve withdrawn',
  people_pleasing: 'whose approval you\'re seeking',
  perfectionism: 'where nothing is good enough',
  procrastination: 'what keeps getting delayed',
  overwhelm: 'how much you\'re holding'
};

// Get dominant truth from all inputs
export const getDominantTruth = (
  chartData: FullChartData | null,
  chapterAnalysis: LifeChapterAnalysis | null,
  patternAnalysis: AspectPatternAnalysis | null,
  timeframe: Timeframe = 'today'
): DominantTruth | null => {
  if (!chartData?.transits?.strongest_hits) return null;
  
  const transits = chartData.transits.strongest_hits;
  const planets = chartData.natal?.planets || {};
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  const primaryChapter = chapterAnalysis?.primaryChapter || null;
  const dominantPattern = patternAnalysis?.dominantPattern || null;
  
  // Score each theme category
  const themeScores: { [key in ThemeCategory]?: CandidateTheme } = {};
  
  // Initialize all themes
  for (const category of Object.keys(THEME_INDICATORS) as ThemeCategory[]) {
    themeScores[category] = {
      category,
      score: 0,
      sources: [],
      lifeAreas: [],
      houses: [],
      chapterAlignment: false,
      patternAlignment: false
    };
  }
  
  // Score based on transits
  for (const hit of transits.slice(0, 10)) {
    const natalHouse = hit.natal_house || planets[hit.natal_point]?.house || 0;
    const transitPlanet = hit.transit_point;
    const aspectType = hit.aspect_type;
    
    for (const [category, indicators] of Object.entries(THEME_INDICATORS)) {
      const cat = category as ThemeCategory;
      const theme = themeScores[cat]!;
      
      let hitScore = 0;
      
      // House match
      if (indicators.houses.includes(natalHouse)) {
        hitScore += 5;
        if (!theme.houses.includes(natalHouse)) theme.houses.push(natalHouse);
      }
      
      // Planet match (either transit or natal)
      if (indicators.planets.includes(transitPlanet)) {
        hitScore += 4;
      }
      if (indicators.planets.includes(hit.natal_point)) {
        hitScore += 4;
      }
      
      // Aspect match
      if (indicators.aspects.includes(aspectType)) {
        hitScore += 3;
      }
      
      // Chart ruler involvement
      if (chartRuler && (hit.natal_point === chartRuler.planet || transitPlanet === chartRuler.planet)) {
        hitScore += 5;
      }
      
      // Dominant house involvement
      if (dominantHouses.includes(natalHouse)) {
        hitScore += 3;
      }
      
      // Orb tightness
      if (hit.orb <= 2) hitScore += 3;
      else if (hit.orb <= 5) hitScore += 1;
      
      if (hitScore > 0) {
        theme.score += hitScore;
        if (!theme.sources.includes(`${transitPlanet} ${aspectType} ${hit.natal_point}`)) {
          theme.sources.push(`${transitPlanet} ${aspectType} ${hit.natal_point}`);
        }
      }
    }
  }
  
  // Boost themes that align with chapter
  if (primaryChapter) {
    for (const [category, indicators] of Object.entries(THEME_INDICATORS)) {
      const cat = category as ThemeCategory;
      if (indicators.chapters.includes(primaryChapter.chapterType)) {
        themeScores[cat]!.score += 10;
        themeScores[cat]!.chapterAlignment = true;
        themeScores[cat]!.sources.push(`${primaryChapter.chapterType} chapter`);
      }
    }
  }
  
  // Boost themes that align with aspect pattern
  if (dominantPattern) {
    for (const [category, indicators] of Object.entries(THEME_INDICATORS)) {
      const cat = category as ThemeCategory;
      if (indicators.patterns.includes(dominantPattern.patternType)) {
        themeScores[cat]!.score += 8;
        themeScores[cat]!.patternAlignment = true;
        themeScores[cat]!.sources.push(`${dominantPattern.patternType} pattern`);
      }
    }
  }
  
  // Add house-based life areas
  for (const theme of Object.values(themeScores)) {
    if (theme && theme.houses.length > 0) {
      theme.lifeAreas = theme.houses.map(h => HOUSE_LIFE_AREAS[h] || '').filter(Boolean);
    }
  }
  
  // Sort themes by score
  const sortedThemes = Object.values(themeScores)
    .filter(t => t && t.score > 0)
    .sort((a, b) => (b?.score || 0) - (a?.score || 0));
  
  if (sortedThemes.length === 0) return null;
  
  const dominant = sortedThemes[0]!;
  const supporting = sortedThemes.slice(1, 4).map(t => t!.category);
  
  // Minimum threshold for confidence
  if (dominant.score < 15) return null;
  
  // Determine pressure type
  let pressureType: PressureType = 'tension';
  if (['overcommitment', 'premature_action', 'control_grip'].includes(dominant.category)) {
    pressureType = 'push';
  } else if (['avoidance', 'procrastination', 'delayed_decision'].includes(dominant.category)) {
    pressureType = 'pull';
  } else if (['emotional_suppression', 'overwhelm', 'isolation'].includes(dominant.category)) {
    pressureType = 'holding';
  } else if (['creative_block', 'purpose_drift'].includes(dominant.category)) {
    pressureType = 'release';
  }
  
  // Calculate confidence
  const confidence = Math.min(100, Math.round((dominant.score / 50) * 100));
  
  return {
    dominantTheme: dominant.category,
    supportingThemes: supporting,
    confidenceScore: confidence,
    lifeArea: THEME_LIFE_AREAS[dominant.category],
    pressureType,
    houses: dominant.houses,
    sources: dominant.sources.slice(0, 5),
    chapterType: primaryChapter?.chapterType || null,
    patternType: dominantPattern?.patternType || null
  };
};

// ============================================
// COLLAPSED INSIGHTS BUILDER
// ============================================

export const buildCollapsedInsights = (
  chartData: FullChartData | null,
  chapterAnalysis: LifeChapterAnalysis | null,
  patternAnalysis: AspectPatternAnalysis | null,
  timeframe: Timeframe = 'today'
): CollapsedInsights => {
  const dominantTruth = getDominantTruth(chartData, chapterAnalysis, patternAnalysis, timeframe);
  
  const defaultResult: CollapsedInsights = {
    dominantTruth: null,
    narrative: null,
    primaryFeeling: null,
    primaryMistake: null,
    secondaryMistake: null,
    suppressedSignalCount: 0,
    surfacedSignalCount: 0
  };
  
  if (!dominantTruth) return defaultResult;
  
  // Build narrative (this will be enhanced in astrologyNarrative.ts)
  const narrative = buildDominantTruthNarrativeInternal(dominantTruth, chapterAnalysis, timeframe);
  
  // Get collapsed feelings and mistakes
  const transits = chartData?.transits?.strongest_hits || [];
  const totalSignals = transits.length;
  const surfacedSignals = Math.min(3, totalSignals);
  
  return {
    dominantTruth,
    narrative,
    primaryFeeling: narrative?.whereThisShowsUp || null,
    primaryMistake: narrative?.whatGoesWrong || null,
    secondaryMistake: null, // Only show one mistake for clarity
    suppressedSignalCount: Math.max(0, totalSignals - surfacedSignals),
    surfacedSignalCount: surfacedSignals
  };
};

// Internal narrative builder (basic version in interpreter)
const buildDominantTruthNarrativeInternal = (
  truth: DominantTruth,
  chapterAnalysis: LifeChapterAnalysis | null,
  timeframe: Timeframe
): DominantTruthNarrative => {
  const headlines: { [key in ThemeCategory]: { today: string; week: string; month: string } } = {
    overcommitment: {
      today: 'You\'re carrying more than you can sustain.',
      week: 'The weight keeps accumulating.',
      month: 'This is a season of recalibrating what you carry.'
    },
    avoidance: {
      today: 'There\'s something you\'re not looking at.',
      week: 'The same thing keeps getting pushed aside.',
      month: 'Avoidance is becoming a pattern.'
    },
    premature_action: {
      today: 'You\'re moving before the ground is ready.',
      week: 'Impatience keeps surfacing.',
      month: 'This period is teaching you about timing.'
    },
    delayed_decision: {
      today: 'Something needs to be decided.',
      week: 'The same choice keeps circling back.',
      month: 'Indecision is shaping this period.'
    },
    emotional_suppression: {
      today: 'Something is being held in that wants out.',
      week: 'The pressure keeps building.',
      month: 'This is a phase of learning to express.'
    },
    boundary_erosion: {
      today: 'You\'re giving parts of yourself away.',
      week: 'Your boundaries keep getting tested.',
      month: 'This period is redefining where you end and others begin.'
    },
    identity_confusion: {
      today: 'You\'re not sure who you\'re being.',
      week: 'The question of identity keeps arising.',
      month: 'This is a phase of self-redefinition.'
    },
    relationship_strain: {
      today: 'Something in how you\'re relating isn\'t working.',
      week: 'The same tension keeps appearing in connection.',
      month: 'Relationships are undergoing restructuring.'
    },
    financial_pressure: {
      today: 'Resources are under pressure.',
      week: 'Money stress keeps surfacing.',
      month: 'This period is reshaping your relationship with resources.'
    },
    health_neglect: {
      today: 'Your body is asking for attention.',
      week: 'Physical signals keep repeating.',
      month: 'This is a phase of reclaiming your body.'
    },
    communication_breakdown: {
      today: 'Something isn\'t being said.',
      week: 'The same unsaid thing keeps creating distance.',
      month: 'This period is teaching you about speaking truth.'
    },
    control_grip: {
      today: 'You\'re holding on too tight.',
      week: 'The grip keeps tightening.',
      month: 'This phase is about learning to release.'
    },
    trust_issues: {
      today: 'Trust is being tested.',
      week: 'The same fears keep surfacing.',
      month: 'This period is rebuilding trust.'
    },
    purpose_drift: {
      today: 'You\'ve lost sight of where you\'re headed.',
      week: 'Direction keeps feeling unclear.',
      month: 'This is a phase of purpose realignment.'
    },
    creative_block: {
      today: 'Something that wants to come through is stuck.',
      week: 'The same creative resistance keeps appearing.',
      month: 'This period is unblocking something important.'
    },
    isolation: {
      today: 'You\'ve pulled back from something you need.',
      week: 'Withdrawal has become a pattern.',
      month: 'This phase is about re-engaging.'
    },
    people_pleasing: {
      today: 'You\'re shaping yourself for someone else.',
      week: 'The same accommodations keep happening.',
      month: 'This period is about reclaiming your own shape.'
    },
    perfectionism: {
      today: 'Nothing is good enough right now.',
      week: 'The same impossible standard keeps appearing.',
      month: 'This phase is learning to accept good enough.'
    },
    procrastination: {
      today: 'Something important keeps getting pushed back.',
      week: 'The delay is becoming a pattern.',
      month: 'This period is confronting what you\'ve been avoiding.'
    },
    overwhelm: {
      today: 'There\'s more coming in than you can process.',
      week: 'The same overwhelm keeps building.',
      month: 'This phase is about creating space.'
    }
  };

  const coreTruths: { [key in ThemeCategory]: { today: string; week: string; month: string } } = {
    overcommitment: {
      today: 'You\'ve taken on responsibilities that exceed your current capacity. This isn\'t about working harder—it\'s about recognizing that some commitments were made before you understood what they would actually cost.',
      week: 'A pattern of overextension is running through this week. Each day adds to a load that\'s already too heavy. The question isn\'t whether you can handle it—it\'s whether you should be trying to.',
      month: 'This month is a reckoning with how much you\'ve been carrying. The accumulation isn\'t sustainable, and this period is forcing a choice about what actually matters versus what you\'ve agreed to out of obligation.'
    },
    avoidance: {
      today: 'There\'s something you already know needs attention, but looking at it feels harder than ignoring it. The avoidance isn\'t protecting you—it\'s preserving a problem that will grow.',
      week: 'The same thing keeps getting avoided this week. Each time you push it aside, it grows slightly larger. The pattern is becoming harder to ignore.',
      month: 'This month, avoidance has become a theme. Something you\'ve been not-looking-at is demanding attention. The longer you wait, the more it shapes your choices.'
    },
    premature_action: {
      today: 'You\'re ready to move, but the situation isn\'t. Acting now won\'t speed things up—it will create complications that slow everything down.',
      week: 'Impatience keeps pushing you toward action this week. But the timing isn\'t right, and forcing it creates more work than waiting would.',
      month: 'This period is teaching you about the cost of moving too fast. Actions taken before conditions are ready create problems that take longer to solve than the original waiting.'
    },
    delayed_decision: {
      today: 'A decision has been waiting. The delay isn\'t giving you clarity—it\'s letting the pressure build while options narrow.',
      week: 'The same decision keeps appearing this week in different forms. The avoidance of choosing is itself becoming a choice—and it\'s choosing stagnation.',
      month: 'This month, indecision has become its own direction. The longer choices remain unmade, the more your path is being determined by default rather than intention.'
    },
    emotional_suppression: {
      today: 'Something is being compressed inside you that needs expression. The containment is costing more than the release would.',
      week: 'This week, emotions keep pushing against the walls you\'ve built. The pressure is building because something needs to move through.',
      month: 'This period is about what you\'ve been holding. The suppression has been running long enough that release isn\'t just needed—it\'s overdue.'
    },
    boundary_erosion: {
      today: 'You\'ve been agreeing to things that cost you. Each yes has been a small erosion of what you actually need.',
      week: 'Your boundaries have been tested repeatedly this week. The pattern of giving ground is creating a deficit you\'ll have to address.',
      month: 'This month is revealing where your boundaries have worn thin. What started as accommodation has become a pattern of self-betrayal.'
    },
    identity_confusion: {
      today: 'You\'re showing up in ways that don\'t feel like you. The gap between who you are and who you\'re being is creating friction.',
      week: 'This week keeps asking who you are. The answer keeps changing depending on who\'s asking, and the inconsistency is exhausting.',
      month: 'This period is a renegotiation of identity. Who you\'ve been presenting isn\'t who you are becoming, and the transition is uncomfortable.'
    },
    relationship_strain: {
      today: 'Something in how you\'re connecting with someone isn\'t working. The pattern keeps repeating because something isn\'t being addressed.',
      week: 'The same relational tension keeps appearing this week. Different faces, same dynamic. Something in how you connect needs attention.',
      month: 'This month, relationships are under reconstruction. Patterns that have been running are being exposed, and continuing as before isn\'t an option.'
    },
    financial_pressure: {
      today: 'Resources are tighter than they should be. The pressure isn\'t random—it\'s pointing to something about how you\'ve been managing.',
      week: 'Money stress keeps surfacing this week. The anxiety isn\'t just about numbers—it\'s about security and what you believe you deserve.',
      month: 'This period is reshaping your relationship with resources. What you have, what you need, and what you believe about abundance are all under review.'
    },
    health_neglect: {
      today: 'Your body has been asking for something you haven\'t been giving. The signals are getting louder.',
      week: 'Physical messages keep repeating this week. Your body is not just communicating—it\'s insisting.',
      month: 'This month, the body is having its say. What you\'ve been ignoring is now demanding attention. This is a phase of returning to the physical.'
    },
    communication_breakdown: {
      today: 'What needs to be said isn\'t being said. The silence isn\'t keeping peace—it\'s creating distance.',
      week: 'The same unsaid thing keeps creating problems this week. The gap between what\'s true and what\'s spoken is widening.',
      month: 'This period is about communication debt. What hasn\'t been said is accumulating interest, and the cost of continued silence is growing.'
    },
    control_grip: {
      today: 'You\'re holding something so tightly that it can\'t move. The grip isn\'t creating security—it\'s preventing what needs to happen.',
      week: 'The need for control keeps intensifying this week. Each attempt to hold things in place creates more strain.',
      month: 'This period is teaching you about release. What you\'ve been gripping is asking to move, and the holding is becoming its own burden.'
    },
    trust_issues: {
      today: 'Something has made it hard to trust. The protection is keeping out what you need along with what you\'re avoiding.',
      week: 'Trust keeps being tested this week. The same fears surface in different situations, revealing a pattern.',
      month: 'This period is about rebuilding trust—with others, with life, with yourself. The walls that protected have also isolated.'
    },
    purpose_drift: {
      today: 'You\'ve lost connection with why you\'re doing what you\'re doing. The motion continues but the meaning has faded.',
      week: 'Purpose keeps slipping away this week. You\'re busy but not fulfilled. The doing continues but the why is missing.',
      month: 'This month is a reckoning with direction. Where you\'ve been heading no longer feels like where you want to go.'
    },
    creative_block: {
      today: 'Something wants to come through you but can\'t find its way out. The block isn\'t about ability—it\'s about what\'s in the way.',
      week: 'Creative resistance keeps appearing this week. The same wall, different approaches, same result.',
      month: 'This period is unblocking something that\'s been stuck for longer than this month. What wants to emerge has been waiting.'
    },
    isolation: {
      today: 'You\'ve withdrawn from something you actually need. The distance that felt protective is now creating its own problem.',
      week: 'Withdrawal has become a pattern this week. Each time you pull back, the gap widens.',
      month: 'This month is about re-engagement. The isolation that served you is now limiting you.'
    },
    people_pleasing: {
      today: 'You\'ve been adjusting yourself to fit what others want. The shape you\'ve taken isn\'t sustainable.',
      week: 'The pattern of accommodation keeps running this week. Each adjustment takes you further from your own center.',
      month: 'This period is about reclaiming your shape. Who you\'ve been for others is being asked to make room for who you are.'
    },
    perfectionism: {
      today: 'Your standards have become a barrier. Nothing can meet them, including you.',
      week: 'The same impossible standard keeps appearing this week. The goal post moves every time you approach.',
      month: 'This period is learning to accept imperfection. What you\'ve been chasing doesn\'t exist, and the pursuit is costing you.'
    },
    procrastination: {
      today: 'Something important keeps getting delayed. The postponement isn\'t buying time—it\'s spending it.',
      week: 'The same task keeps being pushed this week. The avoidance is becoming expensive.',
      month: 'This month, procrastination is reaching its limit. What you\'ve been putting off is demanding attention.'
    },
    overwhelm: {
      today: 'More is coming in than you can process. The system is overloaded and signals are being missed.',
      week: 'Overwhelm keeps building this week. Each day adds to a pile that doesn\'t shrink.',
      month: 'This period is forcing triage. Not everything can be carried, and this month is teaching you what to put down.'
    }
  };
  
  const whereItShowsUp: { [key in ThemeCategory]: string } = {
    overcommitment: 'in your schedule, in your energy levels, in the things that keep slipping',
    avoidance: 'in the conversation you\'re not having, in the task you keep moving, in what you think about at 3am',
    premature_action: 'in the impatience you feel, in the urge to just do something, in the restlessness',
    delayed_decision: 'in the thing you keep circling, in the options you won\'t narrow, in the question you won\'t answer',
    emotional_suppression: 'in your body, in unexpected reactions, in the fatigue that doesn\'t match your sleep',
    boundary_erosion: 'in the resentment you don\'t voice, in the time that isn\'t yours, in the energy you don\'t have',
    identity_confusion: 'in the discomfort when you\'re alone, in not knowing what you actually want, in performing',
    relationship_strain: 'in the same conversation happening again, in distance that wasn\'t chosen, in what\'s not being said',
    financial_pressure: 'in decisions being made from scarcity, in anxiety about numbers, in avoiding looking',
    health_neglect: 'in how you feel in your body, in what you\'re ignoring, in symptoms that persist',
    communication_breakdown: 'in assumptions filling gaps, in growing misunderstanding, in connection that\'s fading',
    control_grip: 'in your body tension, in trying to manage what others do, in not being able to let go',
    trust_issues: 'in checking, in waiting for the other shoe, in not being able to relax into connection',
    purpose_drift: 'in going through motions, in feeling disconnected from outcomes, in nothing feeling worth it',
    creative_block: 'in starting and stopping, in self-criticism before anything forms, in the gap between vision and output',
    isolation: 'in not reaching out, in declining without reason, in loneliness that feels safer than connection',
    people_pleasing: 'in saying yes when you mean no, in not knowing your own opinion, in exhaustion from performing',
    perfectionism: 'in not finishing, in redoing, in criticism that outpaces accomplishment',
    procrastination: 'in the same task on every list, in creative avoidance, in running out of runway',
    overwhelm: 'in forgetting things, in short fuse, in not being able to prioritize'
  };
  
  const whatGoesWrong: { [key in ThemeCategory]: string } = {
    overcommitment: 'Continuing to add without subtracting. Believing you can handle what you couldn\'t handle yesterday.',
    avoidance: 'Waiting until it becomes a crisis. Letting the thing you\'re avoiding grow into something worse.',
    premature_action: 'Acting from impatience and having to undo it. Creating problems where none existed.',
    delayed_decision: 'Letting circumstances decide for you. Losing options while you wait for certainty.',
    emotional_suppression: 'Having it come out sideways. Letting the pressure build until something breaks.',
    boundary_erosion: 'Continuing to give what you don\'t have. Building resentment you\'ll have to address.',
    identity_confusion: 'Making decisions from a self that isn\'t you. Getting further from what you actually want.',
    relationship_strain: 'Pretending it\'s fine. Letting distance become the new normal.',
    financial_pressure: 'Making decisions from anxiety. Short-term fixes that create long-term problems.',
    health_neglect: 'Waiting until your body forces the issue. Treating symptoms instead of causes.',
    communication_breakdown: 'Letting the unsaid become unfixable. Filling silence with assumptions.',
    control_grip: 'Pushing away what you\'re trying to keep. Breaking what you\'re trying to protect.',
    trust_issues: 'Testing until you create what you feared. Making prophecy out of suspicion.',
    purpose_drift: 'Continuing on momentum alone. Arriving somewhere you never wanted to be.',
    creative_block: 'Judging before creating. Letting the critic win before the artist starts.',
    isolation: 'Convincing yourself you\'re fine alone. Letting connection atrophy.',
    people_pleasing: 'Losing yourself in maintenance of others. Not knowing what you want when you\'re finally asked.',
    perfectionism: 'Never finishing. Never starting. Never being good enough.',
    procrastination: 'Running out of time. Having the thing you avoided become the only thing.',
    overwhelm: 'Missing what matters while managing what doesn\'t. Burning out before it gets better.'
  };
  
  const questions: { [key in ThemeCategory]: string } = {
    overcommitment: 'What would you need to put down to carry what actually matters?',
    avoidance: 'What are you protecting by not looking?',
    premature_action: 'What are you hoping to skip by moving now?',
    delayed_decision: 'What would you have to accept to decide?',
    emotional_suppression: 'What would happen if you let it out?',
    boundary_erosion: 'What are you afraid will happen if you say no?',
    identity_confusion: 'Who are you when no one is watching?',
    relationship_strain: 'What do you need that you\'re not asking for?',
    financial_pressure: 'What belief about money is running this?',
    health_neglect: 'What is your body trying to tell you?',
    communication_breakdown: 'What are you afraid will happen if you say it?',
    control_grip: 'What are you afraid will happen if you let go?',
    trust_issues: 'What would trust require you to risk?',
    purpose_drift: 'What would make this feel worth it again?',
    creative_block: 'What are you afraid to create?',
    isolation: 'What would connection cost you?',
    people_pleasing: 'Whose approval are you trying to earn?',
    perfectionism: 'What would "good enough" look like?',
    procrastination: 'What are you avoiding by delaying?',
    overwhelm: 'What\'s the one thing that would create space?'
  };
  
  // Build timeframe context
  let timeframeContext = '';
  if (timeframe === 'today') {
    timeframeContext = 'This is what\'s most active today.';
  } else if (timeframe === 'week') {
    timeframeContext = 'This keeps showing up. It\'s the thread running through this week.';
  } else {
    timeframeContext = 'This is the theme of this period. It\'s shaping what comes next.';
  }
  
  // Align with chapter if present
  let chapterAmplification = '';
  if (chapterAnalysis?.primaryChapter?.isActive) {
    const chapter = chapterAnalysis.primaryChapter;
    if (chapter.chapterType === 'saturn') {
      chapterAmplification = ' And this phase won\'t let you get away with it.';
    } else if (chapter.chapterType === 'jupiter') {
      chapterAmplification = ' There\'s growth available here, but only if you address this.';
    } else if (chapter.chapterType === 'nodal') {
      chapterAmplification = ' Your direction depends on how you handle this.';
    } else if (chapter.chapterType === 'chiron') {
      chapterAmplification = ' This is touching something that\'s been tender for a long time.';
    }
  }
  
  // Recognition line for moderate-to-high confidence
  // Calibration: Lowered threshold from 70 to 60 for better emotional resonance
  let recognitionLine: string | null = null;
  if (truth.confidenceScore >= 60) {
    const recognitionLines = [
      'You already know where this is happening.',
      'This isn\'t new.',
      'You\'ve felt this before.',
      'You know exactly what this is about.',
      'Something in you recognizes this.'
    ];
    // Use deterministic selection based on theme to avoid random flicker
    const index = truth.dominantTheme.length % recognitionLines.length;
    recognitionLine = recognitionLines[index];
  }
  
  // Get timeframe-specific content
  const headlineForTimeframe = headlines[truth.dominantTheme][timeframe];
  const coreTruthForTimeframe = coreTruths[truth.dominantTheme][timeframe];
  
  return {
    headline: headlineForTimeframe,
    coreTruth: coreTruthForTimeframe + chapterAmplification,
    whereThisShowsUp: whereItShowsUp[truth.dominantTheme],
    whatGoesWrong: whatGoesWrong[truth.dominantTheme],
    question: questions[truth.dominantTheme],
    recognitionLine,
    timeframeContext
  };
};


// ============================================
// UNIFIED PATTERN ENGINE
// Synthesizes the entire chart into ONE repeating pattern
// ============================================

export interface UnifiedPattern {
  headline: string;
  corePattern: string;
  tension: string;
  connectorPhrase: string; // Used to link individual cards
}

interface UnifiedPatternInput {
  chartData: FullChartData | null;
  placements: CorePlacements;
  dominantTruth: DominantTruth | null;
  aspectPatterns: AspectPatternAnalysis | null;
  lifeChapter: LifeChapterAnalysis | null;
}

// Pattern archetype templates based on element/modality combinations
const PATTERN_ARCHETYPES: { [key: string]: {
  headline: string;
  corePattern: string;
  tension: string;
  connectorPhrase: string;
}} = {
  // Fire-driven patterns
  'fire_cardinal': {
    headline: 'The pattern you keep repeating',
    corePattern: 'You move before you\'re ready. Action feels safer than waiting, so you launch before the ground is stable—and then spend your energy managing the consequences.',
    tension: 'This creates a loop: act first, understand later, then handle the fallout. The urgency that drives you forward also prevents the preparation that would make the forward motion stick.',
    connectorPhrase: 'this is one part of how you move before you\'re ready'
  },
  'fire_fixed': {
    headline: 'The pattern running through everything',
    corePattern: 'You commit intensely but resist adjusting. Once you\'ve decided something matters, you hold on—even when holding on is costing more than letting go would.',
    tension: 'This creates a loop: invest deeply, refuse to pivot, justify the sunk cost. Your loyalty to what you\'ve chosen can trap you in positions that no longer serve you.',
    connectorPhrase: 'this is one part of how you hold on past the point of usefulness'
  },
  'fire_mutable': {
    headline: 'The pattern you already recognize',
    corePattern: 'You start things brilliantly but struggle to finish them. The spark of beginning is intoxicating; the work of completion feels like a prison.',
    tension: 'This creates a loop: inspire yourself, get bored, chase the next spark. Your enthusiasm for beginnings creates a trail of incomplete projects.',
    connectorPhrase: 'this is one part of how you start more than you finish'
  },
  // Earth-driven patterns
  'earth_cardinal': {
    headline: 'The pattern underneath everything',
    corePattern: 'You build toward goals but struggle to celebrate arriving. Achievement creates a brief satisfaction before the next mountain appears.',
    tension: 'This creates a loop: achieve, immediately re-focus, never fully arrive. Your drive for accomplishment can become a treadmill that never lets you rest.',
    connectorPhrase: 'this is one part of how you never let yourself arrive'
  },
  'earth_fixed': {
    headline: 'What keeps happening',
    corePattern: 'You maintain stability by resisting change. What you\'ve built feels safer than what you could build—even when what exists has stopped working.',
    tension: 'This creates a loop: hold on, resist necessary change, wait until crisis forces movement. Your need for security can keep you in situations that feel safe but aren\'t alive.',
    connectorPhrase: 'this is one part of how you resist necessary change'
  },
  'earth_mutable': {
    headline: 'The pattern you keep meeting',
    corePattern: 'You analyze endlessly before acting. The search for the optimal choice prevents any choice from being made until circumstances force your hand.',
    tension: 'This creates a loop: research, doubt, delay, react under pressure. Your desire to be prepared prevents the action that would actually prepare you.',
    connectorPhrase: 'this is one part of how you analyze instead of act'
  },
  // Air-driven patterns
  'air_cardinal': {
    headline: 'The pattern in your relationships',
    corePattern: 'You adapt to others so skillfully that you lose track of your own shape. Harmony becomes more important than honesty, and your needs disappear into accommodation.',
    tension: 'This creates a loop: adapt, lose yourself, resent, repeat. Your gift for connection can become a way of avoiding the confrontation of having your own needs.',
    connectorPhrase: 'this is one part of how you disappear to keep the peace'
  },
  'air_fixed': {
    headline: 'What runs through everything',
    corePattern: 'You think your way around feeling. Understanding replaces experiencing, and analysis becomes a way to stay at arm\'s length from what actually moves you.',
    tension: 'This creates a loop: feel something, intellectualize it, maintain distance. Your mental clarity can become a shield against the emotional experiences that would change you.',
    connectorPhrase: 'this is one part of how you think instead of feel'
  },
  'air_mutable': {
    headline: 'The pattern you keep creating',
    corePattern: 'You gather information instead of making decisions. Options multiply, perspectives accumulate, but the moment of choice keeps getting deferred.',
    tension: 'This creates a loop: explore, discover complexity, defer choice. Your ability to see all sides can prevent you from standing on any of them.',
    connectorPhrase: 'this is one part of how you stay curious instead of committed'
  },
  // Water-driven patterns
  'water_cardinal': {
    headline: 'The pattern you carry',
    corePattern: 'You protect by controlling the emotional environment. Your sensitivity becomes a radar for danger, and safety means managing how others feel about you.',
    tension: 'This creates a loop: sense threat, control surroundings, exhaust yourself. Your emotional intelligence can become a burden when it\'s always on duty.',
    connectorPhrase: 'this is one part of how you manage everyone\'s feelings'
  },
  'water_fixed': {
    headline: 'What keeps repeating',
    corePattern: 'You feel everything at full intensity but show almost nothing. The gap between your internal experience and external expression creates a pressure that leaks out sideways.',
    tension: 'This creates a loop: feel deeply, suppress expression, accumulate pressure. Your emotional depth becomes a weight when it can\'t find release.',
    connectorPhrase: 'this is one part of how you hide what you\'re actually feeling'
  },
  'water_mutable': {
    headline: 'The pattern in your psyche',
    corePattern: 'You absorb more than you can process. Others\' emotions, the atmosphere of spaces, the weight of situations—it all moves through you without clear boundaries.',
    tension: 'This creates a loop: absorb, become overwhelmed, escape, repeat. Your empathic capacity can become a form of self-abandonment.',
    connectorPhrase: 'this is one part of how you take on what isn\'t yours'
  }
};

// Theme-specific pattern overrides when dominant truth is clear
const THEME_PATTERN_OVERRIDES: { [key in ThemeCategory]?: {
  headline: string;
  corePattern: string;
  tension: string;
  connectorPhrase: string;
}} = {
  overcommitment: {
    headline: 'The pattern you keep repeating',
    corePattern: 'You take on more than you can carry. Yes comes before you\'ve calculated the cost, and then you push through on willpower alone.',
    tension: 'This creates a loop: overcommit, exhaust yourself, recover barely, overcommit again. Your capacity to handle pressure has become an excuse to create it.',
    connectorPhrase: 'this is one part of how you overextend yourself'
  },
  avoidance: {
    headline: 'What keeps happening',
    corePattern: 'You see what needs to be faced but turn toward easier things. The problem grows in the periphery while you stay busy with what feels manageable.',
    tension: 'This creates a loop: notice, avoid, watch it grow, notice again. Your awareness of what\'s wrong becomes torture when you don\'t act on it.',
    connectorPhrase: 'this is one part of how you avoid what you can see'
  },
  premature_action: {
    headline: 'The pattern running through everything',
    corePattern: 'You move before the ground is ready. Waiting feels like weakness, so you launch before conditions support what you\'re trying to build.',
    tension: 'This creates a loop: act too soon, manage consequences, wonder why things don\'t land. Your courage becomes recklessness when it doesn\'t include patience.',
    connectorPhrase: 'this is one part of how you move before the ground is ready'
  },
  delayed_decision: {
    headline: 'What you keep doing',
    corePattern: 'You wait for certainty that will never come. The decision sits there while you gather more information, hoping clarity will eventually make choosing easy.',
    tension: 'This creates a loop: consider, wait, watch options narrow, choose under pressure. Your desire for the right choice prevents any choice at all.',
    connectorPhrase: 'this is one part of how you delay until circumstances decide'
  },
  emotional_suppression: {
    headline: 'The pattern underneath',
    corePattern: 'You contain what needs to move. Feelings get compressed, managed, scheduled—anything but simply felt and expressed.',
    tension: 'This creates a loop: feel, suppress, accumulate, leak. What you won\'t let out directly finds indirect ways to surface.',
    connectorPhrase: 'this is one part of how you suppress instead of express'
  },
  boundary_erosion: {
    headline: 'What keeps happening',
    corePattern: 'You give ground to avoid conflict. Each small accommodation seems harmless, but they accumulate into a territory that\'s no longer yours.',
    tension: 'This creates a loop: get asked, say yes, resent, say yes again. Your desire for peace creates a war inside yourself.',
    connectorPhrase: 'this is one part of how you give away what you need'
  },
  identity_confusion: {
    headline: 'The pattern you\'re living',
    corePattern: 'You become what the situation requires. Different versions of you for different contexts, until you\'ve forgotten which one is real.',
    tension: 'This creates a loop: adapt, lose center, feel empty, adapt again. Your flexibility has become a form of self-erasure.',
    connectorPhrase: 'this is one part of how you become what others need'
  },
  relationship_strain: {
    headline: 'The pattern in connection',
    corePattern: 'You repeat the same dynamic with different people. The faces change but the friction is familiar.',
    tension: 'This creates a loop: connect, encounter the pattern, struggle, disconnect. What you\'re looking for keeps showing up as what you\'re trying to avoid.',
    connectorPhrase: 'this is one part of how the same dynamic repeats'
  },
  control_grip: {
    headline: 'What you keep doing',
    corePattern: 'You hold things so tightly they can\'t breathe. Control feels like safety, but what you\'re protecting is being strangled.',
    tension: 'This creates a loop: fear loss, grip tighter, create distance, fear more. Your security measures are creating the instability they\'re meant to prevent.',
    connectorPhrase: 'this is one part of how you grip too tight'
  },
  trust_issues: {
    headline: 'The pattern you carry',
    corePattern: 'You test before you trust. People have to prove themselves repeatedly, and the tests never quite end.',
    tension: 'This creates a loop: want closeness, test for safety, push away, want closeness again. Your protection prevents the very thing you\'re protecting yourself for.',
    connectorPhrase: 'this is one part of how you test instead of trust'
  },
  people_pleasing: {
    headline: 'What keeps happening',
    corePattern: 'You shape yourself to fit what others want. Approval feels necessary, so you become whatever earns it.',
    tension: 'This creates a loop: read others, adapt, lose self, resent. Your talent for attunement has become a trap.',
    connectorPhrase: 'this is one part of how you become what they want'
  },
  perfectionism: {
    headline: 'The pattern running through everything',
    corePattern: 'Nothing is ever good enough. The standard keeps moving, and what you produce never reaches it.',
    tension: 'This creates a loop: create, critique, perfect, exhaust. Your high standards have become impossible demands.',
    connectorPhrase: 'this is one part of how you demand the impossible'
  }
};

// Get dominant element and modality from chart
const getChartElementModality = (placements: CorePlacements): { element: string; modality: string } => {
  const elements: { [key: string]: number } = { Fire: 0, Earth: 0, Air: 0, Water: 0 };
  const modalities: { [key: string]: number } = { Cardinal: 0, Fixed: 0, Mutable: 0 };
  
  // Weight the big three more heavily
  const signs = [
    { sign: placements.sun, weight: 3 },
    { sign: placements.moon, weight: 2 },
    { sign: placements.ascendant, weight: 2 },
    { sign: placements.mercury || placements.sun, weight: 1 },
    { sign: placements.venus || placements.moon, weight: 1 },
    { sign: placements.mars || placements.sun, weight: 1 }
  ];
  
  for (const { sign, weight } of signs) {
    const element = SIGN_ELEMENTS[sign];
    const modality = SIGN_MODALITIES[sign];
    if (element) elements[element] += weight;
    if (modality) modalities[modality] += weight;
  }
  
  const dominantElement = Object.entries(elements).reduce((a, b) => a[1] > b[1] ? a : b)[0];
  const dominantModality = Object.entries(modalities).reduce((a, b) => a[1] > b[1] ? a : b)[0];
  
  return { element: dominantElement.toLowerCase(), modality: dominantModality.toLowerCase() };
};

// Enhance pattern based on aspect patterns
const enhancePatternWithAspects = (
  pattern: UnifiedPattern, 
  aspectPatterns: AspectPatternAnalysis | null
): UnifiedPattern => {
  if (!aspectPatterns?.dominantPattern) return pattern;
  
  const dominant = aspectPatterns.dominantPattern;
  
  // Add specificity based on pattern type
  if (dominant.patternType === 'pressure_triangle' || dominant.patternType === 't_square') {
    return {
      ...pattern,
      tension: pattern.tension + ' The pressure doesn\'t resolve—it redirects. What can\'t go one way forces its way out another.'
    };
  }
  
  if (dominant.patternType === 'opposition_axis') {
    return {
      ...pattern,
      tension: pattern.tension + ' Two parts of you pull in opposite directions. Progress in one feels like betrayal of the other.'
    };
  }
  
  if (dominant.patternType === 'stellium') {
    return {
      ...pattern,
      corePattern: pattern.corePattern + ' Everything concentrates in one area. What should be distributed is instead focused—intensely, sometimes overwhelmingly.'
    };
  }
  
  return pattern;
};

// Enhance pattern based on life chapter
const enhancePatternWithChapter = (
  pattern: UnifiedPattern, 
  chapterAnalysis: LifeChapterAnalysis | null
): UnifiedPattern => {
  if (!chapterAnalysis?.primaryChapter?.isActive) return pattern;
  
  const chapter = chapterAnalysis.primaryChapter;
  
  if (chapter.chapterType === 'saturn' && chapter.strengthScore >= 20) {
    return {
      ...pattern,
      tension: pattern.tension + ' And this phase isn\'t letting you get away with it.'
    };
  }
  
  if (chapter.chapterType === 'chiron' && chapter.strengthScore >= 15) {
    return {
      ...pattern,
      corePattern: pattern.corePattern + ' An old wound is being touched. The pattern connects to something that\'s been tender for a long time.'
    };
  }
  
  return pattern;
};

/**
 * GET UNIFIED PATTERN
 * Synthesizes the entire chart into ONE integrated pattern
 */
export const getUnifiedPattern = (input: UnifiedPatternInput): UnifiedPattern | null => {
  const { chartData, placements, dominantTruth, aspectPatterns, lifeChapter } = input;
  
  // If we have a strong dominant truth, use its theme for the pattern
  if (dominantTruth && dominantTruth.confidenceScore >= 55) {
    const override = THEME_PATTERN_OVERRIDES[dominantTruth.dominantTheme];
    if (override) {
      let pattern = { ...override };
      pattern = enhancePatternWithAspects(pattern, aspectPatterns);
      pattern = enhancePatternWithChapter(pattern, lifeChapter);
      return pattern;
    }
  }
  
  // Otherwise, derive from element/modality
  const { element, modality } = getChartElementModality(placements);
  const archetypeKey = `${element}_${modality}`;
  const archetype = PATTERN_ARCHETYPES[archetypeKey];
  
  if (!archetype) {
    // Fallback to a generic but meaningful pattern
    return {
      headline: 'The pattern running through this chart',
      corePattern: 'There\'s a way you keep meeting yourself—in different situations, different relationships, different choices. The same thread runs through all of it.',
      tension: 'This creates a loop that feels familiar even when the circumstances are new. You\'ve been here before, in some form.',
      connectorPhrase: 'this is one part of a larger pattern'
    };
  }
  
  let pattern = { ...archetype };
  pattern = enhancePatternWithAspects(pattern, aspectPatterns);
  pattern = enhancePatternWithChapter(pattern, lifeChapter);
  
  return pattern;
};



// ============================================
// CHART AXIS - Developmental Spine Analysis
// Part of Astrological Intelligence Hierarchy v1
// ============================================

export interface ChartAxisOutput {
  lines: string[];
  coreTension: string;
  growthDirection: string;
  woundMedicine: string;
}

export interface MostImportantFactor {
  rank: number;
  factorName: string;
  whyItMatters: string;
  factorType: 'placement' | 'aspect' | 'pattern' | 'emphasis';
}

export function generateChartAxis(
  placements: CorePlacements,
  fullChartData: FullChartData | null
): ChartAxisOutput {
  const lines: string[] = [];
  
  const sun = placements.sun || 'Unknown';
  const moon = placements.moon || 'Unknown';
  const asc = placements.ascendant || 'Unknown';
  const saturn = placements.saturn;
  const saturnHouse = placements.saturn_house;
  const northNode = placements.north_node;
  const northNodeHouse = placements.north_node_house;
  const chiron = placements.chiron;
  const chironHouse = placements.chiron_house;
  
  // 1. CORE ORIENTATION LINE
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  
  const coreOrientationLines: { [key: string]: { [key: string]: string } } = {
    'Fire': {
      'Fire': 'A direct, expressive core that moves before it considers.',
      'Earth': 'An expressive identity grounded by practical emotional needs.',
      'Air': 'A warm presence whose emotions process through thought.',
      'Water': 'Outer confidence paired with deep inner sensitivity.',
    },
    'Earth': {
      'Fire': 'A steady nature with emotions that want to move quickly.',
      'Earth': 'Double-grounded—consistent inside and out.',
      'Air': 'Practical by nature, but emotionally restless.',
      'Water': 'Solid on the surface, deep currents underneath.',
    },
    'Air': {
      'Fire': 'A curious mind fueled by emotional enthusiasm.',
      'Earth': 'Ideas that need practical emotional grounding.',
      'Air': 'Pure thought—both identity and emotions live in the mind.',
      'Water': 'A thinking nature with feeling depths that surprise.',
    },
    'Water': {
      'Fire': 'A sensitive core with impulses that demand expression.',
      'Earth': 'Emotional depth stabilized by practical needs.',
      'Air': 'Deep feelings processed through mental frameworks.',
      'Water': 'Feeling all the way down—boundaries are the work.',
    },
  };
  
  if (sunElement && moonElement && coreOrientationLines[sunElement]?.[moonElement]) {
    lines.push(coreOrientationLines[sunElement][moonElement]);
  } else {
    lines.push('A mixed elemental signature—versatile, complex, less predictable.');
  }
  
  // 2. MAIN TENSION LINE
  const sunMod = SIGN_MODALITIES[sun];
  const moonMod = SIGN_MODALITIES[moon];
  
  if (sunMod === 'Cardinal' && moonMod === 'Fixed') {
    lines.push('Life is approached with initiative, but emotions resist the changes identity keeps starting.');
  } else if (sunMod === 'Fixed' && moonMod === 'Cardinal') {
    lines.push('Identity holds steady, but emotional impulses keep pushing for new beginnings.');
  } else if (sunElement === 'Fire' && moonElement === 'Water') {
    lines.push('What you show and what you feel live in different registers—confidence outside, sensitivity inside.');
  } else if (sunElement === 'Earth' && moonElement === 'Air') {
    lines.push('A practical nature with emotional restlessness—wanting both stability and variety.');
  } else {
    lines.push('Your Big 3 work relatively harmoniously—less internal conflict, more consistent expression.');
  }
  
  // 3. SATURN LINE
  if (saturn && saturnHouse) {
    const saturnLines: { [key: number]: string } = {
      1: 'Self-definition itself is where life keeps demanding more discipline and structure.',
      2: 'Growth demands structure around resources, body, or material foundations.',
      3: 'Maturation pressure concentrates on communication, thought, and mental containment.',
      4: 'Home, roots, and inner foundation are where maturity keeps getting tested.',
      5: 'Creative expression and visibility require more discipline than feels natural.',
      6: 'Daily routines and service are where discipline builds character.',
      7: 'Relationships are where you learn the hardest lessons about commitment and boundaries.',
      8: 'Intimacy and shared resources require uncommon emotional discipline.',
      9: 'Meaning-making and beliefs are where structure gets demanded.',
      10: 'Career and public standing are where maturity gets tested hardest.',
      11: 'Community and friendships require more intentional cultivation.',
      12: 'The inner world and spiritual life demand structure that doesn\'t come naturally.',
    };
    lines.push(saturnLines[saturnHouse] || `Pressure and maturation concentrate around House ${saturnHouse}.`);
  }
  
  // 4. NODAL LINE
  if (northNode) {
    const northElement = SIGN_ELEMENTS[northNode];
    const nodalLines: { [key: string]: string } = {
      'Fire': 'Growth asks for more courage, self-assertion, and willingness to be seen.',
      'Earth': 'Growth asks for more grounding, patience, and building something lasting.',
      'Air': 'Growth asks for more objectivity, communication, and mental flexibility.',
      'Water': 'Growth asks for trust, surrender, and emotional intelligence.',
    };
    lines.push(nodalLines[northElement || ''] || 'Growth direction involves moving toward what feels less familiar.');
  }
  
  // 5. CHIRON LINE
  if (chiron && chironHouse) {
    const chironLines: { [key: number]: string } = {
      1: 'A wound around selfhood or visibility may become your medicine for helping others be seen.',
      2: 'A wound around worth or resources may become your medicine for helping others value themselves.',
      3: 'A wound around voice or communication may become your medicine for helping others be heard.',
      4: 'A wound around belonging or family may become your medicine for helping others find home.',
      5: 'A wound around creativity or being seen may become your medicine for helping others shine.',
      6: 'A wound around health or usefulness may become your medicine for helping others serve.',
      7: 'A wound around partnership may become your medicine for helping others relate.',
      8: 'A wound around trust or intimacy may become your medicine for helping others transform.',
      9: 'A wound around meaning or belonging may become your medicine for helping others find truth.',
      10: 'A wound around achievement or authority may become your medicine for helping others lead.',
      11: 'A wound around belonging or difference may become your medicine for helping others find their people.',
      12: 'A wound around isolation or transcendence may become your medicine for helping others heal.',
    };
    lines.push(chironLines[chironHouse] || `A wound in House ${chironHouse} may become part of your medicine.`);
  }
  
  return {
    lines: lines.slice(0, 6),
    coreTension: lines[1] || '',
    growthDirection: lines.find(l => l.includes('Growth') || l.includes('growth')) || '',
    woundMedicine: lines.find(l => l.includes('wound') || l.includes('medicine')) || '',
  };
}

export function rankMostImportantFactors(
  placements: CorePlacements,
  fullChartData: FullChartData | null
): MostImportantFactor[] {
  const factors: MostImportantFactor[] = [];
  
  // 1. SUN
  const sunHouse = placements.sun_house;
  const sunElement = SIGN_ELEMENTS[placements.sun];
  factors.push({
    rank: 1,
    factorName: `Sun in ${placements.sun}${sunHouse ? ` in House ${sunHouse}` : ''}`,
    whyItMatters: sunHouse && HOUSE_MEANINGS[sunHouse]
      ? `Identity develops through ${HOUSE_MEANINGS[sunHouse].shortLabel.toLowerCase()} and ${sunElement?.toLowerCase() || 'distinctive'} expression.`
      : 'The essential frequency of who you are.',
    factorType: 'placement',
  });
  
  // 2. MOON
  const moonHouse = placements.moon_house;
  const moonElement = SIGN_ELEMENTS[placements.moon];
  factors.push({
    rank: 2,
    factorName: `Moon in ${placements.moon}${moonHouse ? ` in House ${moonHouse}` : ''}`,
    whyItMatters: moonHouse && HOUSE_MEANINGS[moonHouse]
      ? `Emotional life anchors in ${HOUSE_MEANINGS[moonHouse].shortLabel.toLowerCase()} and processes through ${moonElement?.toLowerCase() || 'distinctive'} patterns.`
      : 'How you feel when no one is watching.',
    factorType: 'placement',
  });
  
  // 3. SATURN
  if (placements.saturn && placements.saturn_house) {
    factors.push({
      rank: 3,
      factorName: `Saturn in ${placements.saturn} in House ${placements.saturn_house}`,
      whyItMatters: HOUSE_MEANINGS[placements.saturn_house]
        ? `Pressure and maturation concentrate around ${HOUSE_MEANINGS[placements.saturn_house].shortLabel.toLowerCase()}—this is where life keeps demanding growth.`
        : 'Where maturation pressure concentrates.',
      factorType: 'placement',
    });
  }
  
  // 4. NORTH NODE
  if (placements.north_node) {
    const nodeElement = SIGN_ELEMENTS[placements.north_node];
    const nodeLines: { [key: string]: string } = {
      'Fire': 'Growth asks for more courage, self-assertion, and willingness to be seen.',
      'Earth': 'Growth asks for more grounding, patience, and building something lasting.',
      'Air': 'Growth asks for more objectivity, communication, and mental flexibility.',
      'Water': 'Growth asks for trust, surrender, and emotional intelligence.',
    };
    factors.push({
      rank: 4,
      factorName: `North Node in ${placements.north_node}${placements.north_node_house ? ` in House ${placements.north_node_house}` : ''}`,
      whyItMatters: nodeLines[nodeElement || ''] || 'The direction life keeps pulling you toward.',
      factorType: 'placement',
    });
  }
  
  // 5. CHIRON
  if (placements.chiron && placements.chiron_house) {
    factors.push({
      rank: 5,
      factorName: `Chiron in ${placements.chiron} in House ${placements.chiron_house}`,
      whyItMatters: HOUSE_MEANINGS[placements.chiron_house]
        ? `A wound in ${HOUSE_MEANINGS[placements.chiron_house].shortLabel.toLowerCase()} that becomes wisdom through lived experience.`
        : 'A wound that becomes wisdom over time.',
      factorType: 'placement',
    });
  }
  
  return factors.slice(0, 5);
}
