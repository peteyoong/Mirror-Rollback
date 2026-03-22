import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import { useRouter } from 'expo-router';

// ============================================
// TYPES
// ============================================

interface AstrologySection {
  label: string;
  body: string;
}

interface ChartStructure {
  dominant_element?: string;
  dominant_modality?: string;
  strongest_houses?: number[];
  stellium?: { sign: string; planets: string[] } | null;
  chart_shape?: string;
}

interface PlanetData {
  sign: string;
  degree: number;
  longitude: number;
  house: number;
  retrograde: boolean;
  formatted?: string;
}

interface TransitHit {
  transit_point: string;
  transit_sign: string;
  natal_point: string;
  natal_sign: string;
  natal_house: number;
  aspect_type: string;
  orb: number;
  exactness: number;
  applying: boolean;
  strength_score: number;
  theme_tags: string[];
  transit_retrograde: boolean;
}

interface TransitWindow {
  date?: string;
  period?: string;
  strongest_hits: TransitHit[];
  emphasis_tags: string[];
  activated_natal_points: string[];
  dominant_energy?: {
    transit: string;
    natal: string;
    aspect: string;
  };
  deterministic_summary: string;
}

interface TransitData {
  computed_at: string;
  current_transit_positions: { [key: string]: PlanetData };
  transit_to_natal_aspects: TransitHit[];
  strongest_hits: TransitHit[];
  total_active_aspects: number;
  emphasis_tags: string[];
  windows: {
    today: TransitWindow;
    this_week: TransitWindow;
    this_month: TransitWindow;
  };
}

interface FullChartData {
  success: boolean;
  metadata: {
    node_mode: string;
    house_system: string;
    sidereal_mode: string;
    svp_degrees: number;
    computation_version: string;
  };
  natal: {
    planets: { [key: string]: PlanetData };
    nodes: {
      north: PlanetData;
      south: PlanetData;
    };
    angles: {
      asc: PlanetData;
      dc: PlanetData;
      mc: PlanetData;
      ic: PlanetData;
    };
    houses: {
      system: string;
      cusps: Array<{ house: number; sign: string; degree: number }>;
    };
    aspects: Array<{
      point_a: string;
      point_b: string;
      aspect_type: string;
      orb: number;
      applying: boolean;
    }>;
    balances: {
      elements: { [key: string]: number };
      modalities: { [key: string]: number };
      polarities: { [key: string]: number };
    };
    concentrations: {
      dominant_elements: Array<[string, number]>;
      dominant_modalities: Array<[string, number]>;
      dominant_houses: Array<{ house: number; planets: string[] }>;
      angular_planets: Array<{ planet: string; house: number }>;
    };
  };
  transits: TransitData;
  sect: string;
}

interface CorePlacements {
  sun: string;
  sun_house?: number;
  moon: string;
  moon_house?: number;
  ascendant: string;
  mercury?: string;
  mercury_house?: number;
  venus?: string;
  venus_house?: number;
  mars?: string;
  mars_house?: number;
  jupiter?: string;
  jupiter_house?: number;
  saturn?: string;
  saturn_house?: number;
  chiron?: string;
  chiron_house?: number;
  north_node?: string;
  north_node_house?: number;
  south_node?: string;
  south_node_house?: number;
}

interface AstrologyDeepDiveCard {
  id: string;
  title: string;
  subtitle: string;
  preview: string;
  whatThisIs: string;
  whatYouMightNotice: string[];
  tensionLabel: string;
  tension: string;
  giftLabel: string;
  gift: string;
  reflection: string;
}

interface AstrologySummaryData {
  title?: string;
  sections?: AstrologySection[];
  mirror_prompt?: string;
  core_placements?: CorePlacements;
  success?: boolean;
  error?: string;
  message?: string;
}

// ============================================
// SIGN DATA - Deterministic content
// ============================================

const SIGN_ELEMENTS: { [key: string]: string } = {
  'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
  'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
  'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
  'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
};

const SIGN_MODALITIES: { [key: string]: string } = {
  'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
  'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
  'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable'
};

const SIGN_QUALITIES: { [key: string]: string[] } = {
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
// SYNTHESIS HELPERS
// ============================================

// Premium one-liner descriptor for the hero section
const getHeroDescriptor = (sun: string, moon: string, asc: string): string => {
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  const ascQualities = SIGN_QUALITIES[asc] || [];
  
  // Build a bespoke descriptor based on element combinations
  const coreWord = sunElement === 'Water' ? 'Sensitive' : 
                   sunElement === 'Fire' ? 'Expressive' : 
                   sunElement === 'Earth' ? 'Grounded' : 'Curious';
  
  const emotionalWord = moonElement === 'Fire' ? 'fast in feeling' : 
                        moonElement === 'Water' ? 'deep in feeling' : 
                        moonElement === 'Earth' ? 'steady in feeling' : 'quick to process';
  
  const approachWord = ascQualities[0] || 'open';
  
  return `${coreWord} at the core, ${emotionalWord}, ${approachWord} in approach.`;
};

// Generate the Chart Spine - the backbone statements of the chart
const getChartSpine = (placements: CorePlacements): string[] => {
  const spine: string[] = [];
  const sun = placements.sun || 'Unknown';
  const moon = placements.moon || 'Unknown';
  const asc = placements.ascendant || 'Unknown';
  const saturn = placements.saturn;
  const saturn_house = placements.saturn_house;
  const north_node = placements.north_node;
  const south_node = placements.south_node;
  const chiron = placements.chiron;
  
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  
  // 1. Core tone (Sun)
  if (sunElement === 'Water') {
    spine.push('A sensitive core that perceives more than it says.');
  } else if (sunElement === 'Fire') {
    spine.push('An expressive core that leads with presence and warmth.');
  } else if (sunElement === 'Earth') {
    spine.push('A grounded core that builds through patience and tangible effort.');
  } else if (sunElement === 'Air') {
    spine.push('A curious core that connects through ideas and social exchange.');
  }
  
  // 2. Emotional engine (Moon)
  if (moonElement === 'Fire') {
    spine.push('Emotion moves quickly and wants action before full processing.');
  } else if (moonElement === 'Water') {
    spine.push('Emotion runs deep and needs time to surface fully.');
  } else if (moonElement === 'Earth') {
    spine.push('Emotion is steady and seeks security before expression.');
  } else if (moonElement === 'Air') {
    spine.push('Emotion processes through thought and needs to be understood.');
  }
  
  // 3. How life is approached (Ascendant)
  if (asc === 'Sagittarius') {
    spine.push('Life is approached with openness, scale, and forward motion.');
  } else if (asc === 'Scorpio') {
    spine.push('Life is approached with intensity, depth, and strategic awareness.');
  } else if (asc === 'Capricorn') {
    spine.push('Life is approached with seriousness, structure, and long-term vision.');
  } else if (asc === 'Aquarius') {
    spine.push('Life is approached with independence, originality, and social awareness.');
  } else if (asc === 'Pisces') {
    spine.push('Life is approached with receptivity, imagination, and fluid boundaries.');
  } else if (asc === 'Aries') {
    spine.push('Life is approached with directness, initiative, and competitive energy.');
  } else if (asc === 'Taurus') {
    spine.push('Life is approached with steadiness, sensuality, and practical grounding.');
  } else if (asc === 'Gemini') {
    spine.push('Life is approached with curiosity, adaptability, and verbal agility.');
  } else if (asc === 'Cancer') {
    spine.push('Life is approached with emotional attunement and protective care.');
  } else if (asc === 'Leo') {
    spine.push('Life is approached with warmth, creativity, and natural leadership.');
  } else if (asc === 'Virgo') {
    spine.push('Life is approached with precision, analysis, and service orientation.');
  } else if (asc === 'Libra') {
    spine.push('Life is approached with diplomacy, aesthetic sense, and relational awareness.');
  }
  
  // 4. Developmental pressure (Saturn)
  if (saturn && saturn_house) {
    const houseThemes: { [key: number]: string } = {
      1: 'self-definition and physical presence',
      2: 'resources, values, and self-worth',
      3: 'communication, thought, and self-expression',
      4: 'home, roots, and emotional foundation',
      5: 'creativity, pleasure, and authentic expression',
      6: 'work, health, and daily discipline',
      7: 'partnership and committed relationship',
      8: 'intimacy, shared resources, and transformation',
      9: 'belief, meaning, and worldview',
      10: 'career, public role, and authority',
      11: 'community, friendship, and future vision',
      12: 'solitude, spirituality, and hidden patterns'
    };
    spine.push(`Maturity is being forced through ${houseThemes[saturn_house] || 'specific life themes'}.`);
  }
  
  // 5. Growth direction (Nodes)
  if (north_node && south_node) {
    const southElement = SIGN_ELEMENTS[south_node];
    const northElement = SIGN_ELEMENTS[north_node];
    
    if (southElement === 'Earth' && northElement === 'Water') {
      spine.push('Growth asks a move away from over-control and toward trust.');
    } else if (southElement === 'Air' && northElement === 'Fire') {
      spine.push('Growth asks a move from thinking to doing, from analysis to action.');
    } else if (southElement === 'Fire' && northElement === 'Earth') {
      spine.push('Growth asks a move from impulse to patience, from vision to form.');
    } else if (southElement === 'Water' && northElement === 'Air') {
      spine.push('Growth asks a move from feeling to articulating, from merging to boundarying.');
    } else if (southElement === northElement) {
      spine.push(`Growth refines rather than reverses—staying in ${northElement?.toLowerCase()} but evolving how.`);
    } else {
      spine.push(`Growth pulls from ${south_node} familiarity toward ${north_node} unfamiliarity.`);
    }
  }
  
  return spine.slice(0, 5);
};

// Generate What Matters Most - ranked chart factors
const getWhatMattersMost = (placements: CorePlacements, fullChartData: FullChartData | null): Array<{ label: string; why: string }> => {
  const items: Array<{ label: string; why: string; weight: number }> = [];
  
  // Sun placement
  if (placements.sun && placements.sun_house) {
    const houseTheme = getHouseTheme(placements.sun_house);
    items.push({
      label: `${placements.sun} Sun in House ${placements.sun_house}`,
      why: `Identity develops through ${houseTheme}`,
      weight: 10
    });
  }
  
  // Moon placement
  if (placements.moon && placements.moon_house) {
    const moonElement = SIGN_ELEMENTS[placements.moon];
    items.push({
      label: `${placements.moon} Moon in House ${placements.moon_house}`,
      why: `Emotional life is ${moonElement === 'Fire' ? 'fast, protective, and action-oriented' : moonElement === 'Water' ? 'deep, intuitive, and absorbing' : moonElement === 'Earth' ? 'steady, security-focused, and practical' : 'quick-moving, socially attuned, and idea-driven'}`,
      weight: 9.5
    });
  }
  
  // Saturn placement (major developmental pressure)
  if (placements.saturn && placements.saturn_house) {
    items.push({
      label: `Saturn in ${placements.saturn} in House ${placements.saturn_house}`,
      why: `Pressure and maturation center on ${getHouseTheme(placements.saturn_house)}`,
      weight: 9
    });
  }
  
  // Nodes (life direction)
  if (placements.north_node && placements.north_node_house) {
    items.push({
      label: `North Node in ${placements.north_node}`,
      why: `Growth requires moving toward ${SIGN_QUALITIES[placements.north_node]?.[0] || 'new'} territory`,
      weight: 8.5
    });
  }
  
  // Chiron (wound/medicine)
  if (placements.chiron && placements.chiron_house) {
    items.push({
      label: `Chiron in ${placements.chiron} in House ${placements.chiron_house}`,
      why: `Core sensitivity and healing capacity around ${getHouseTheme(placements.chiron_house)}`,
      weight: 7.5
    });
  }
  
  // House concentration if available
  if (fullChartData?.natal?.concentrations?.dominant_houses?.length) {
    const dominant = fullChartData.natal.concentrations.dominant_houses[0];
    if (dominant && dominant.planets.length >= 2) {
      items.push({
        label: `House ${dominant.house} concentration`,
        why: `${dominant.planets.join(', ')} cluster here—${getHouseTheme(dominant.house)} dominates`,
        weight: 8
      });
    }
  }
  
  // Angular planets
  if (fullChartData?.natal?.concentrations?.angular_planets?.length) {
    const angular = fullChartData.natal.concentrations.angular_planets;
    if (angular.length >= 2) {
      items.push({
        label: `Angular emphasis`,
        why: `${angular.map(a => a.planet).join(', ')} at chart angles—visible, active, defining`,
        weight: 7
      });
    }
  }
  
  // Sort by weight and return top 5
  return items.sort((a, b) => b.weight - a.weight).slice(0, 5).map(({ label, why }) => ({ label, why }));
};

// ============================================
// ENHANCED ASPECT INTELLIGENCE
// ============================================

interface EnhancedAspect {
  aspect: string;
  meaning: string;
  quality: 'ease' | 'friction' | 'complexity';
  whyItMatters: string;
  pointA: string;
  pointB: string;
  aspectType: string;
}

// Get key natal aspects for display - ENHANCED VERSION
const getKeyAspects = (fullChartData: FullChartData | null, placements: CorePlacements): EnhancedAspect[] => {
  if (!fullChartData?.natal?.aspects) return [];
  
  const aspects = fullChartData.natal.aspects;
  const keyAspects: Array<EnhancedAspect & { weight: number }> = [];
  
  // Deep aspect interpretation with chart context
  const getAspectInterpretation = (pointA: string, pointB: string, type: string): { meaning: string; quality: 'ease' | 'friction' | 'complexity'; whyItMatters: string } => {
    const isHard = ['conjunction', 'square', 'opposition'].includes(type);
    const isSoft = ['trine', 'sextile'].includes(type);
    
    // Mercury-Pluto: depth in thinking
    if ((pointA === 'Mercury' && pointB === 'Pluto') || (pointB === 'Mercury' && pointA === 'Pluto')) {
      return {
        meaning: 'Creates depth, suspicion, and intensity in thinking and communication.',
        quality: isHard ? 'friction' : 'complexity',
        whyItMatters: 'Communication is never casual—perception tends to go beneath the obvious. You see what others miss, but may also see threat where none exists.'
      };
    }
    
    // Sun-Saturn: identity under pressure
    if ((pointA === 'Sun' && pointB === 'Saturn') || (pointB === 'Sun' && pointA === 'Saturn')) {
      return {
        meaning: isHard ? 'Identity formed through restriction and early pressure.' : 'Disciplined self-expression that earns authority over time.',
        quality: isHard ? 'friction' : 'complexity',
        whyItMatters: 'You may have felt blocked, criticized, or burdened early. What develops is a self that earns its place—but self-doubt runs deep.'
      };
    }
    
    // Sun-Moon: inner unity or division
    if ((pointA === 'Sun' && pointB === 'Moon') || (pointB === 'Sun' && pointA === 'Moon')) {
      return {
        meaning: isHard ? 'Core self and emotional nature pull in different directions.' : 'Who you are and what you need align naturally.',
        quality: isHard ? 'friction' : 'ease',
        whyItMatters: isHard 
          ? 'Inner division between what you want to be and what you need to feel okay. You may feel split—acting one way, feeling another.'
          : 'Less internal conflict—your identity and emotional life support each other. What fulfills you also expresses you.'
      };
    }
    
    // Moon-Saturn: emotional caution
    if ((pointA === 'Moon' && pointB === 'Saturn') || (pointB === 'Moon' && pointA === 'Saturn')) {
      return {
        meaning: 'Emotional life carries weight, caution, or early deprivation.',
        quality: 'friction',
        whyItMatters: 'You may have learned to contain feelings early, to not need too much. Emotional expression requires trust you don\'t extend easily.'
      };
    }
    
    // Moon-Pluto: emotional intensity
    if ((pointA === 'Moon' && pointB === 'Pluto') || (pointB === 'Moon' && pointA === 'Pluto')) {
      return {
        meaning: 'Emotional life is intense, transformative, and hard to hide.',
        quality: 'complexity',
        whyItMatters: 'Feelings run deeper than you show. You may have experienced emotional overwhelm or manipulation that taught you to guard your vulnerability fiercely.'
      };
    }
    
    // Venus-Saturn: love with conditions
    if ((pointA === 'Venus' && pointB === 'Saturn') || (pointB === 'Venus' && pointA === 'Saturn')) {
      return {
        meaning: isHard ? 'Love and worthiness feel earned, not given.' : 'Loyalty and commitment come naturally.',
        quality: isHard ? 'friction' : 'ease',
        whyItMatters: isHard 
          ? 'You may hold back in relationships, waiting to feel "good enough." Love feels safer when you\'ve proven yourself first.'
          : 'You take relationships seriously and build lasting bonds. Commitment isn\'t scary—it\'s where you thrive.'
      };
    }
    
    // Mars-Saturn: will under pressure
    if ((pointA === 'Mars' && pointB === 'Saturn') || (pointB === 'Mars' && pointA === 'Saturn')) {
      return {
        meaning: isHard ? 'Drive meets obstruction; anger may turn inward.' : 'Disciplined action and controlled strength.',
        quality: isHard ? 'friction' : 'complexity',
        whyItMatters: isHard
          ? 'You may feel blocked when you try to assert yourself. Frustration can build until it erupts, or turn into depression. Timing action is your lesson.'
          : 'You have controlled strength—able to persist where others quit. Your discipline is a genuine advantage.'
      };
    }
    
    // Jupiter-Saturn: expansion vs. contraction
    if ((pointA === 'Jupiter' && pointB === 'Saturn') || (pointB === 'Jupiter' && pointA === 'Saturn')) {
      return {
        meaning: 'Growth and restraint negotiate constantly.',
        quality: isHard ? 'friction' : 'complexity',
        whyItMatters: 'You feel both the urge to expand and the fear of overreaching. Success comes through timing—knowing when to push and when to consolidate.'
      };
    }
    
    // Sun-Pluto: identity transformation
    if ((pointA === 'Sun' && pointB === 'Pluto') || (pointB === 'Sun' && pointA === 'Pluto')) {
      return {
        meaning: 'Identity undergoes repeated death and rebirth.',
        quality: 'friction',
        whyItMatters: 'You can\'t stay the same—life forces transformation whether you choose it or not. Power dynamics shape who you become.'
      };
    }
    
    // Venus-Pluto: intense relating
    if ((pointA === 'Venus' && pointB === 'Pluto') || (pointB === 'Venus' && pointA === 'Pluto')) {
      return {
        meaning: 'Love and power intertwine; relationships transform you.',
        quality: 'complexity',
        whyItMatters: 'You don\'t do casual connection. Relationships involve depth, jealousy, transformation—and sometimes the fear of being consumed.'
      };
    }
    
    // Moon-Neptune: emotional porousness
    if ((pointA === 'Moon' && pointB === 'Neptune') || (pointB === 'Moon' && pointA === 'Neptune')) {
      return {
        meaning: 'Emotional boundaries are fluid; empathy runs deep.',
        quality: 'complexity',
        whyItMatters: 'You absorb others\' feelings easily. Creativity and intuition are heightened, but so is confusion about what you actually feel versus what you\'re picking up.'
      };
    }
    
    // Sun-Jupiter: natural confidence
    if ((pointA === 'Sun' && pointB === 'Jupiter') || (pointB === 'Sun' && pointA === 'Jupiter')) {
      return {
        meaning: 'Identity expands through faith, optimism, and meaning.',
        quality: 'ease',
        whyItMatters: 'You believe in yourself and in possibility. This is a genuine gift—though it can sometimes mean overestimating what you can do.'
      };
    }
    
    // Moon-Mars: emotional fire
    if ((pointA === 'Moon' && pointB === 'Mars') || (pointB === 'Moon' && pointA === 'Mars')) {
      return {
        meaning: isHard ? 'Feelings ignite quickly; emotional reactivity.' : 'Emotional honesty and direct feeling.',
        quality: isHard ? 'friction' : 'ease',
        whyItMatters: isHard
          ? 'Your feelings want immediate expression. You can be reactive—anger and hurt move fast. Learning to pause before acting is ongoing work.'
          : 'You know what you feel and you\'re not afraid to show it. Emotional directness is a strength.'
      };
    }
    
    // Saturn-Chiron: wound and structure
    if ((pointA === 'Saturn' && pointB === 'Chiron') || (pointB === 'Saturn' && pointA === 'Chiron')) {
      return {
        meaning: 'Wound and discipline intertwine; healing through structure.',
        quality: 'complexity',
        whyItMatters: 'Your sense of inadequacy may be real—but so is your capacity to build something lasting from that struggle. The wound becomes expertise.'
      };
    }
    
    // Chiron aspects to personal planets
    if (pointA === 'Chiron' || pointB === 'Chiron') {
      const other = pointA === 'Chiron' ? pointB : pointA;
      return {
        meaning: `${other} carries the wound—sensitized, potentially gifted.`,
        quality: 'complexity',
        whyItMatters: `Whatever ${other} represents is where you\'ve been hurt and where you\'ve developed unusual understanding. The sensitivity is both burden and gift.`
      };
    }
    
    // Pluto aspects (general)
    if (pointA === 'Pluto' || pointB === 'Pluto') {
      const other = pointA === 'Pluto' ? pointB : pointA;
      return {
        meaning: `${other} undergoes deep transformation; power themes present.`,
        quality: 'friction',
        whyItMatters: `${other} in your chart is intensified—more powerful but also more compulsive. Control issues may surface here.`
      };
    }
    
    // Neptune aspects (general)
    if (pointA === 'Neptune' || pointB === 'Neptune') {
      const other = pointA === 'Neptune' ? pointB : pointA;
      return {
        meaning: `${other} is idealized, spiritualized, or confused.`,
        quality: 'complexity',
        whyItMatters: `${other} in your chart dissolves into something less defined—potentially transcendent, potentially deceptive. Clarity takes work here.`
      };
    }
    
    // Uranus aspects (general)
    if (pointA === 'Uranus' || pointB === 'Uranus') {
      const other = pointA === 'Uranus' ? pointB : pointA;
      return {
        meaning: `${other} electrified—unconventional, restless, inventive.`,
        quality: isHard ? 'friction' : 'ease',
        whyItMatters: `${other} won\'t stay conventional. You need freedom and originality here, even when stability would be easier.`
      };
    }
    
    // Default
    return {
      meaning: `${pointA} and ${pointB} in ${type}—an active dynamic in your chart.`,
      quality: isSoft ? 'ease' : isHard ? 'friction' : 'complexity',
      whyItMatters: `These two chart factors interact meaningfully. How they express depends on houses and sign context.`
    };
  };
  
  // Weight aspects by importance - prioritize chart-defining aspects
  const corePersonalPlanets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars'];
  const developmentalPlanets = ['Saturn', 'Chiron', 'Pluto'];
  const outerPlanets = ['Jupiter', 'Neptune', 'Uranus'];
  
  for (const asp of aspects) {
    // Skip very wide orbs
    if (asp.orb > 8) continue;
    
    const isPersonalToPersonal = corePersonalPlanets.includes(asp.point_a) && corePersonalPlanets.includes(asp.point_b);
    const isPersonalToDevelopmental = (corePersonalPlanets.includes(asp.point_a) && developmentalPlanets.includes(asp.point_b)) ||
                                       (developmentalPlanets.includes(asp.point_a) && corePersonalPlanets.includes(asp.point_b));
    const isHardAspect = ['conjunction', 'opposition', 'square'].includes(asp.aspect_type);
    const isTightOrb = asp.orb < 3;
    
    // Only include significant aspects
    if (!isPersonalToPersonal && !isPersonalToDevelopmental && !isTightOrb) continue;
    
    const { meaning, quality, whyItMatters } = getAspectInterpretation(asp.point_a, asp.point_b, asp.aspect_type);
    const symbol = asp.aspect_type === 'conjunction' ? '☌' : asp.aspect_type === 'opposition' ? '☍' : asp.aspect_type === 'square' ? '□' : asp.aspect_type === 'trine' ? '△' : asp.aspect_type === 'sextile' ? '⚹' : '•';
    
    // Calculate weight
    let weight = 0;
    if (isPersonalToPersonal) weight += 10;
    if (isPersonalToDevelopmental) weight += 8;
    if (isHardAspect) weight += 5;
    if (isTightOrb) weight += 6;
    if (asp.orb < 1) weight += 3; // Very tight
    if (asp.point_a === 'Sun' || asp.point_b === 'Sun') weight += 3;
    if (asp.point_a === 'Moon' || asp.point_b === 'Moon') weight += 3;
    if (asp.point_a === 'Saturn' || asp.point_b === 'Saturn') weight += 2;
    if (asp.point_a === 'Chiron' || asp.point_b === 'Chiron') weight += 2;
    
    keyAspects.push({
      aspect: `${asp.point_a} ${symbol} ${asp.point_b}`,
      meaning,
      quality,
      whyItMatters,
      pointA: asp.point_a,
      pointB: asp.point_b,
      aspectType: asp.aspect_type,
      weight
    });
  }
  
  // Sort and return top 5 chart-defining aspects
  return keyAspects
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 5)
    .map(({ aspect, meaning, quality, whyItMatters, pointA, pointB, aspectType }) => 
      ({ aspect, meaning, quality, whyItMatters, pointA, pointB, aspectType }));
};

// ============================================
// TODAY TAB EXPERIENTIAL CONTENT
// RECOGNITION-BASED MIRROR VOICE
// ============================================

// Generate "What This May Feel Like" - RECOGNITION-BASED
const getWhatThisMayFeelLike = (transits: TransitHit[]): string[] => {
  const feelings: string[] = [];
  
  for (const hit of transits.slice(0, 3)) {
    const { transit_point, natal_point, aspect_type } = hit;
    const isHard = ['square', 'opposition', 'conjunction'].includes(aspect_type);
    
    // Saturn transits - real-life recognition
    if (transit_point === 'Saturn') {
      if (natal_point === 'Sun') feelings.push('waking up tired even when you slept enough');
      else if (natal_point === 'Moon') feelings.push('replaying an old memory you thought you were done with');
      else if (natal_point === 'Mars') feelings.push('wanting to move but feeling like you\'re pushing through mud');
      else if (natal_point === 'Venus') feelings.push('wondering if you\'re settling or just being realistic');
      else if (natal_point === 'Jupiter') feelings.push('doubting something you believed in last week');
      else feelings.push('everything taking longer than it should');
    }
    
    // Jupiter transits
    if (transit_point === 'Jupiter') {
      if (natal_point === 'Saturn') feelings.push('wanting to say yes to something you know needs more planning');
      else if (natal_point === 'Sun') feelings.push('feeling like you could handle more than you\'re currently doing');
      else if (natal_point === 'Moon') feelings.push('wanting to help everyone—even when you haven\'t been asked');
      else feelings.push('getting impatient with anything that feels small');
    }
    
    // Pluto transits
    if (transit_point === 'Pluto') {
      if (natal_point === 'Sun') feelings.push('not recognizing yourself in the mirror—not literally, but close');
      else if (natal_point === 'Moon') feelings.push('crying at something that shouldn\'t make you cry');
      else if (natal_point === 'Mars') feelings.push('wanting to fight something but not knowing what');
      else feelings.push('noticing what you can\'t stop thinking about');
    }
    
    // Uranus transits
    if (transit_point === 'Uranus') {
      if (natal_point === 'Sun') feelings.push('getting bored with your own life mid-sentence');
      else if (natal_point === 'Moon') feelings.push('mood shifting before you can name why');
      else if (natal_point === 'Venus') feelings.push('suddenly noticing what\'s been missing in a relationship');
      else feelings.push('changing your mind about something you just decided');
    }
    
    // Neptune transits
    if (transit_point === 'Neptune') {
      if (natal_point === 'Sun') feelings.push('spacing out in the middle of something important');
      else if (natal_point === 'Moon') feelings.push('absorbing someone else\'s mood and thinking it\'s yours');
      else feelings.push('not being sure if you\'re tired or sad or just unclear');
    }
    
    // Mars transits
    if (transit_point === 'Mars') {
      if (isHard) feelings.push('snapping at someone and then wondering why');
      else feelings.push('having more energy than you know what to do with');
    }
  }
  
  // Dedupe and limit to 3
  return [...new Set(feelings)].slice(0, 3);
};

// Generate "The Mistake to Watch" - VERB-FIRST, BEHAVIOR-SPECIFIC
const getMistakeToWatch = (transits: TransitHit[]): string[] => {
  const mistakes: string[] = [];
  
  for (const hit of transits.slice(0, 3)) {
    const { transit_point, natal_point, aspect_type } = hit;
    const isHard = ['square', 'opposition'].includes(aspect_type);
    
    // Saturn transits
    if (transit_point === 'Saturn') {
      if (natal_point === 'Sun') mistakes.push('calling yourself lazy when you\'re actually exhausted');
      else if (natal_point === 'Moon') mistakes.push('shutting down a feeling because it\'s inconvenient right now');
      else if (natal_point === 'Mars') mistakes.push('pushing harder when what you need is to wait');
      else if (natal_point === 'Jupiter') mistakes.push('treating a temporary setback like a permanent verdict');
      else mistakes.push('deciding you\'re behind when you\'re actually just slow');
    }
    
    // Jupiter transits
    if (transit_point === 'Jupiter') {
      if (natal_point === 'Saturn') mistakes.push('saying yes because it feels exciting—and figuring out the details later');
      if (isHard) mistakes.push('committing to more than you can actually hold');
      else mistakes.push('skipping the boring parts because you\'re sure it\'ll work out');
    }
    
    // Pluto transits
    if (transit_point === 'Pluto') {
      mistakes.push('holding tighter to something that\'s already leaving');
      if (natal_point === 'Mars') mistakes.push('saying something you can\'t take back just to feel powerful');
      if (natal_point === 'Sun') mistakes.push('pretending you\'re the same person you were six months ago');
    }
    
    // Uranus transits
    if (transit_point === 'Uranus') {
      mistakes.push('blowing something up because you\'re bored, not because it\'s wrong');
      if (natal_point === 'Venus') mistakes.push('leaving what\'s good because you want what\'s new');
      if (natal_point === 'Sun') mistakes.push('confusing rebellion with actually knowing what you want');
    }
    
    // Neptune transits
    if (transit_point === 'Neptune') {
      mistakes.push('making a decision now that requires clarity you don\'t have');
      if (natal_point === 'Sun') mistakes.push('going along with someone else\'s plan because yours feels foggy');
    }
    
    // Mars transits
    if (transit_point === 'Mars' && isHard) {
      mistakes.push('acting now and cleaning up later');
    }
  }
  
  // Dedupe and limit to 3
  return [...new Set(mistakes)].slice(0, 3);
};

// ============================================
// DAILY ENERGY SYNTHESIS - RECOGNITION-BASED MIRROR VOICE
// ============================================

interface DailyEnergySynthesis {
  headline: string;
  body: string;
  supporting: string;
}

const getDailyEnergySynthesis = (
  transits: TransitHit[], 
  timeframe: 'today' | 'week' | 'month'
): DailyEnergySynthesis => {
  if (!transits || transits.length === 0) {
    return {
      headline: 'A pause',
      body: 'You\'re not being pushed right now. Part of you might be looking for the next thing to respond to—but there isn\'t one. This is space to work with what you already have, not to chase what\'s next.',
      supporting: 'No significant transits detected'
    };
  }

  const primary = transits[0];
  const secondary = transits[1];
  
  // Build supporting line
  const supportingParts: string[] = [];
  if (primary) supportingParts.push(`${primary.transit_point} ${primary.aspect_type} ${primary.natal_point}`);
  if (secondary) supportingParts.push(`${secondary.transit_point} ${secondary.aspect_type} ${secondary.natal_point}`);
  const supporting = supportingParts.length > 1 
    ? `Based on ${supportingParts[0]}, with ${supportingParts.slice(1).join(', ')} in the background.`
    : supportingParts.length === 1
    ? `Based on ${supportingParts[0]}.`
    : '';

  // Tone variation by timeframe
  const tone = timeframe === 'today' ? 'immediate' : timeframe === 'week' ? 'pattern' : 'arc';
  
  const { transit_point: t1, natal_point: n1 } = primary;
  
  // === JUPITER PRIMARY ===
  if (t1 === 'Jupiter') {
    if (n1 === 'Saturn') {
      if (tone === 'immediate') {
        return {
          headline: 'Reaching past ready',
          body: 'You\'re feeling pulled toward something bigger—but part of you knows you\'re not ready to hold it yet. The excitement is real. So is the gap between where you are and where you want to be.\n\nThis isn\'t about shutting down the want. It\'s about noticing where you\'re trying to skip steps because patience feels boring.',
          supporting
        };
      } else if (tone === 'pattern') {
        return {
          headline: 'Reaching past ready',
          body: 'You keep bumping into the same tension this week: wanting more than you\'ve built the container for. Part of you is ready to expand. Another part knows the structure isn\'t there yet.\n\nWatch for the pattern of saying yes first and figuring it out later. That\'s where this gets expensive.',
          supporting
        };
      } else {
        return {
          headline: 'Growth meeting limits',
          body: 'This month keeps asking the same question: how much of what you want is actually ready to happen? You\'re being stretched between possibility and reality—and both are valid.\n\nThe work isn\'t choosing one. It\'s learning to hold them at the same time without collapsing into either.',
          supporting
        };
      }
    }
    if (n1 === 'Sun') {
      return {
        headline: 'Bigger than usual',
        body: tone === 'immediate' 
          ? 'You\'re feeling more confident than you have in a while—like you could handle more, reach further, be more. Part of you wants to act on this. Another part wonders if you\'re getting ahead of yourself.\n\nBoth are probably right. The question is what this confidence is actually for.'
          : 'You\'ve been feeling like there\'s more room in you than you\'ve been using. That sense of expansion is real—but so is the temptation to inflate rather than grow.\n\nNotice where the bigness is grounded and where it\'s just excitement wearing a costume.',
        supporting
      };
    }
    if (n1 === 'Moon') {
      return {
        headline: 'Giving more',
        body: 'You want to be generous right now—with your time, your care, your belief in people. Part of you is genuinely open. Another part might be giving to avoid feeling something else.\n\nNotice if the generosity is flowing from overflow or from avoidance. They feel different if you slow down.',
        supporting
      };
    }
    if (n1 === 'Mars') {
      return {
        headline: 'Wanting more action',
        body: 'Your drive is amplified right now. You want to move faster, do more, push further. Part of this is real capacity. Part of it is impatience dressed up as ambition.\n\nThe energy is available—the question is whether you\'re pointing it at something that actually matters.',
        supporting
      };
    }
    return {
      headline: 'Something wants more',
      body: 'There\'s a pull toward expansion right now—more possibility, more reach, more yes. Part of you is ready for it. Another part isn\'t sure where it\'s actually leading.\n\nThis isn\'t about saying no to growth. It\'s about noticing what the growth is actually for.',
      supporting
    };
  }

  // === SATURN PRIMARY ===
  if (t1 === 'Saturn') {
    if (n1 === 'Sun') {
      return {
        headline: 'Feeling tested',
        body: tone === 'immediate'
          ? 'You\'re more aware of your limits today than you want to be. Part of you feels like you should be further along, more together, more something. That voice is loud right now.\n\nWhat if the pressure isn\'t punishment? What if it\'s just asking you to get honest about what actually matters?'
          : 'You keep running into the same wall this week: the gap between who you think you should be and who you actually are right now. That gap feels heavier than usual.\n\nThis isn\'t about trying harder. It\'s about getting clear on what\'s actually worth the effort.',
        supporting
      };
    }
    if (n1 === 'Moon') {
      return {
        headline: 'Old feelings surfacing',
        body: 'Something emotional is asking for attention—something you thought you were done with, or something you\'ve been successfully ignoring. It\'s heavier than it needs to be because you\'ve been carrying it without acknowledging it.\n\nYou don\'t have to fix it. You might just need to let yourself feel it.',
        supporting
      };
    }
    if (n1 === 'Jupiter') {
      return {
        headline: 'Hope meeting reality',
        body: 'Part of you wants to believe something will work out. Another part keeps poking holes in that belief. Both voices are active right now, and neither one is willing to back down.\n\nThis isn\'t pessimism versus optimism. It\'s about figuring out what hope actually needs to become real.',
        supporting
      };
    }
    if (n1 === 'Mars') {
      return {
        headline: 'Blocked movement',
        body: 'You want to act, but something keeps getting in the way. External obstacles, internal resistance, or both. The frustration is real—but pushing harder isn\'t working.\n\nPart of you knows this isn\'t the moment to force. Another part hates waiting. That tension is the work right now.',
        supporting
      };
    }
    if (n1 === 'Venus') {
      return {
        headline: 'Love under pressure',
        body: 'A relationship or something you value is being tested right now. Part of you wants to protect it. Another part is wondering if it\'s worth the effort.\n\nThis pressure isn\'t trying to destroy anything—it\'s showing you what\'s actually solid and what was always more fragile than you admitted.',
        supporting
      };
    }
    return {
      headline: 'Weight you didn\'t ask for',
      body: 'Something feels heavier than it should. Not because you\'re doing it wrong—because life is asking more of you right now than feels fair.\n\nYou can\'t make the weight disappear. But you can stop pretending it\'s not there.',
      supporting
    };
  }

  // === PLUTO PRIMARY ===
  if (t1 === 'Pluto') {
    if (n1 === 'Sun') {
      return {
        headline: 'Not who you were',
        body: tone === 'immediate'
          ? 'Something in you is shifting—not adjusting, shifting. The version of yourself you\'ve been operating as doesn\'t quite fit anymore. Part of you wants to hold onto it anyway.\n\nYou\'re not falling apart. You\'re being rearranged. Fighting it just makes it take longer.'
          : 'You\'ve been in an identity shift that doesn\'t announce itself—it just shows up in the way nothing feels quite right anymore. Old answers don\'t work. Old versions of you feel like costumes.\n\nThis isn\'t loss. It\'s something trying to become more honest.',
        supporting
      };
    }
    if (n1 === 'Moon') {
      return {
        headline: 'Feelings you\'ve been avoiding',
        body: 'Something emotional is demanding attention—something you didn\'t invite and can\'t easily dismiss. It\'s bigger than the situation that triggered it.\n\nYou can keep trying to manage it, or you can let yourself actually feel it. Only one of those works.',
        supporting
      };
    }
    if (n1 === 'Mars') {
      return {
        headline: 'Intensity running high',
        body: 'You\'re carrying more charge than usual—anger, desire, the need to control something. Part of you wants to act on it. Another part knows that acting from this place might create wreckage.\n\nThe intensity is real. What you do with it is the question.',
        supporting
      };
    }
    return {
      headline: 'Something ending',
      body: 'Part of you knows something is over—even if it hasn\'t officially ended yet. You can feel the shift. The question isn\'t whether it\'s happening, but whether you\'re going to let it.\n\nHolding on doesn\'t stop the change. It just makes you the last one to know.',
      supporting
    };
  }

  // === URANUS PRIMARY ===
  if (t1 === 'Uranus') {
    if (n1 === 'Sun') {
      return {
        headline: 'Restless with yourself',
        body: 'The usual version of you feels too small right now. You want something to change—maybe everything. Part of you is ready. Another part just wants to escape what is.\n\nBefore you blow something up, ask: is this freedom or just boredom wearing a costume?',
        supporting
      };
    }
    if (n1 === 'Venus') {
      return {
        headline: 'Unsettled in love',
        body: 'Something in your relationships or values is being questioned—not by anyone else, by you. The familiar feels boring. The new feels exciting but unproven.\n\nThis isn\'t about staying or leaving. It\'s about getting honest about what you actually want—not just what would feel different.',
        supporting
      };
    }
    if (n1 === 'Moon') {
      return {
        headline: 'Emotionally electric',
        body: 'Your feelings are changeable right now—shifting before you can name them, surprising you mid-sentence. Part of you wants to trust every impulse. Another part knows they\'re not all equally true.\n\nLet yourself feel the movement without making it mean everything.',
        supporting
      };
    }
    return {
      headline: 'Something wants to break',
      body: 'You\'re restless with something—maybe you know what, maybe you don\'t yet. The status quo feels intolerable even when you can\'t name why.\n\nChange is available. But not all change is progress. Notice what actually needs to shift versus what just feels uncomfortable.',
      supporting
    };
  }

  // === NEPTUNE PRIMARY ===
  if (t1 === 'Neptune') {
    if (n1 === 'Sun') {
      return {
        headline: 'Less solid than usual',
        body: 'You\'re not quite sure who you are right now—not in a dramatic way, but in a "can\'t find the edges" way. Part of you finds this disorienting. Another part is almost relieved.\n\nYou\'re not losing yourself. You\'re losing the version of yourself that was too rigid to begin with.',
        supporting
      };
    }
    if (n1 === 'Moon') {
      return {
        headline: 'Absorbing everything',
        body: 'Your emotional boundaries are thinner than usual. You\'re picking up feelings that might not be yours—from people, from spaces, from things you can\'t name.\n\nThis isn\'t weakness. But it does mean you need to be more careful about what you let in.',
        supporting
      };
    }
    return {
      headline: 'Unclear on purpose',
      body: 'Clarity is hard to find right now. You keep reaching for certainty and coming up with mist. Part of you wants to force an answer. Another part knows the answer isn\'t ready yet.\n\nDon\'t make permanent decisions from this temporary fog.',
      supporting
    };
  }

  // === MARS PRIMARY ===
  if (t1 === 'Mars') {
    return {
      headline: 'More energy than direction',
      body: 'You have fuel right now—restlessness, drive, the urge to do something. The question is what. Part of you wants to act first and figure it out later.\n\nThe energy is real. Where you point it matters more than usual.',
      supporting
    };
  }

  // === VENUS PRIMARY ===
  if (t1 === 'Venus') {
    return {
      headline: 'Wanting connection',
      body: 'You\'re more aware of what you want right now—in relationships, in beauty, in the things you value. Part of you wants to reach for it. Another part wonders if you deserve it.\n\nNotice what you\'re drawn to. It\'s telling you something.',
      supporting
    };
  }

  // === DEFAULT ===
  return {
    headline: 'Multiple pulls',
    body: 'You\'re being asked to hold more than one thing at once right now. Part of you wants clarity—one direction, one answer. But the situation isn\'t offering that.\n\nThis isn\'t confusion. It\'s complexity. The work is integration, not simplification.',
    supporting
  };
};

// Get the reflection question - RECOGNITION-BASED, BEHAVIOR-SPECIFIC
const getReflectionQuestion = (transits: TransitHit[], timeframe: 'today' | 'week' | 'month'): string => {
  if (!transits || transits.length === 0) {
    return 'What keeps showing up that you keep pushing aside?';
  }
  
  const hit = transits[0];
  const { transit_point, natal_point } = hit;
  
  // Saturn transits - confronting but safe
  if (transit_point === 'Saturn') {
    if (natal_point === 'Sun') return 'What are you pretending is fine that actually needs your attention?';
    if (natal_point === 'Moon') return 'What feeling have you been managing instead of actually feeling?';
    if (natal_point === 'Venus') return 'What are you settling for and calling it "realistic"?';
    if (natal_point === 'Jupiter') return 'What are you quietly giving up on because it\'s taking too long?';
    if (natal_point === 'Mars') return 'What do you keep trying to force that isn\'t moving?';
    return 'Where are you exhausted from pretending something is easier than it is?';
  }
  
  // Jupiter transits
  if (transit_point === 'Jupiter') {
    if (natal_point === 'Sun') return 'What are you ready for—that you haven\'t fully admitted yet?';
    if (natal_point === 'Moon') return 'Who are you trying to save that didn\'t ask for help?';
    if (natal_point === 'Saturn') return 'What are you about to say yes to that you already know needs more structure?';
    return 'Where is your optimism getting ahead of your planning?';
  }
  
  // Pluto transits
  if (transit_point === 'Pluto') {
    if (natal_point === 'Sun') return 'What version of yourself are you holding onto that doesn\'t fit anymore?';
    if (natal_point === 'Moon') return 'What are you feeling that you keep telling yourself you shouldn\'t feel?';
    if (natal_point === 'Mars') return 'What are you angry about that you haven\'t let yourself name yet?';
    return 'What do you already know is over that you haven\'t said out loud?';
  }
  
  // Uranus transits
  if (transit_point === 'Uranus') {
    if (natal_point === 'Sun') return 'What would you change if you weren\'t afraid of looking inconsistent?';
    if (natal_point === 'Venus') return 'What are you staying in because leaving feels like failure?';
    if (natal_point === 'Moon') return 'What would you feel if you stopped managing your feelings?';
    return 'What are you pretending to be okay with that you\'re actually done with?';
  }
  
  // Neptune transits
  if (transit_point === 'Neptune') {
    if (natal_point === 'Sun') return 'What are you going along with because you don\'t know what you want?';
    if (natal_point === 'Moon') return 'Whose feelings are you carrying that aren\'t actually yours?';
    return 'What are you hoping is true even though you don\'t have proof?';
  }
  
  // Mars transits
  if (transit_point === 'Mars') {
    return 'What do you want to do that you keep talking yourself out of?';
  }
  
  // Venus transits
  if (transit_point === 'Venus') {
    return 'What do you want that you\'ve been pretending you don\'t need?';
  }
  
  // Default
  return 'What pattern are you in the middle of right now—that you haven\'t fully seen yet?';
};

// ============================================
// PSYCHOLOGICALLY PRECISE CARD GENERATORS
// ============================================

// Jupiter card - sign + house specific
const getJupiterCard = (placements: CorePlacements): AstrologyDeepDiveCard => {
  const jupiter = placements.jupiter || 'Unknown';
  const jupiter_house = placements.jupiter_house || 1;
  const jupiterQualities = SIGN_QUALITIES[jupiter] || ['expansive'];
  const jupiterElement = SIGN_ELEMENTS[jupiter] || 'Unknown';
  
  // Sign-specific Jupiter expressions
  const jupiterSignExpression: { [key: string]: { believes: string; overdoes: string; finds_meaning: string } } = {
    'Aries': { believes: 'in action, in starting, in the self as capable of anything', overdoes: 'impulsiveness disguised as confidence', finds_meaning: 'through initiative and competition' },
    'Taurus': { believes: 'in what can be built, touched, accumulated', overdoes: 'acquisition, comfort-seeking, resistance to change', finds_meaning: 'through material stability and sensory pleasure' },
    'Gemini': { believes: 'in information, connections, the next interesting thing', overdoes: 'scattered attention, promising more than you can track', finds_meaning: 'through ideas, conversations, and variety' },
    'Cancer': { believes: 'in family, belonging, emotional safety', overdoes: 'over-nurturing, clinging to the familiar', finds_meaning: 'through home, heritage, and caretaking' },
    'Leo': { believes: 'in self-expression, recognition, creative confidence', overdoes: 'drama, attention-seeking, over-promising visibility', finds_meaning: 'through creation, performance, and being seen' },
    'Virgo': { believes: 'in improvement, service, getting it right', overdoes: 'perfectionism, over-analysis, finding more to fix', finds_meaning: 'through usefulness and practical contribution' },
    'Libra': { believes: 'in partnership, fairness, aesthetic harmony', overdoes: 'people-pleasing, over-committing to relationship', finds_meaning: 'through connection, beauty, and balance' },
    'Scorpio': { believes: 'in depth, transformation, what\'s hidden', overdoes: 'intensity, obsession, assuming everything has a shadow', finds_meaning: 'through crisis, intimacy, and regeneration' },
    'Sagittarius': { believes: 'in possibility, freedom, the bigger picture', overdoes: 'overreach, preaching, restlessness with details', finds_meaning: 'through adventure, philosophy, and expansion' },
    'Capricorn': { believes: 'in structure, achievement, earning your place', overdoes: 'ambition without joy, confusing success with meaning', finds_meaning: 'through mastery, status, and lasting contribution' },
    'Aquarius': { believes: 'in ideas, progress, what could be different', overdoes: 'detachment as ideology, contrarianism, intellectual arrogance', finds_meaning: 'through innovation, community, and being ahead' },
    'Pisces': { believes: 'in transcendence, compassion, interconnection', overdoes: 'escapism, over-idealization, believing without discernment', finds_meaning: 'through spirituality, imagination, and dissolution of ego' }
  };
  
  // House-specific manifestations
  const houseManifestations: { [key: number]: { where_grows: string; where_overdoes: string } } = {
    1: { where_grows: 'in how you present yourself—big presence, natural confidence', where_overdoes: 'self-promotion, overestimating your impact' },
    2: { where_grows: 'in resources and values—money can come easily, or go easily', where_overdoes: 'overspending, over-acquiring, confusing abundance with security' },
    3: { where_grows: 'in communication and learning—ideas come fast, connections multiply', where_overdoes: 'scattered thinking, promising more than you can deliver in words' },
    4: { where_grows: 'in home and roots—generous family environment, or wanting more space than you have', where_overdoes: 'domestic over-extension, idealizing family' },
    5: { where_grows: 'in creativity and pleasure—creative abundance, romantic optimism', where_overdoes: 'hedonism, gambling, over-investing in being special' },
    6: { where_grows: 'in work and health—can do too much, generous in service', where_overdoes: 'overwork, taking on others\' tasks, health neglect through excess' },
    7: { where_grows: 'in partnership—attracting growth through relationship, believing in others', where_overdoes: 'over-promising in commitment, projecting potential onto partners' },
    8: { where_grows: 'in shared resources and intimacy—benefits from others, depth in merging', where_overdoes: 'expecting transformation without effort, over-relying on what others provide' },
    9: { where_grows: 'in beliefs and travel—natural philosopher, drawn to expansion', where_overdoes: 'proselytizing, assuming your worldview is universal' },
    10: { where_grows: 'in career and reputation—public success, visible abundance', where_overdoes: 'over-identifying with achievement, spreading too thin professionally' },
    11: { where_grows: 'in community and future vision—many friends, big plans', where_overdoes: 'over-extending socially, confusing acquaintance with friendship' },
    12: { where_grows: 'in solitude and spirituality—faith in the invisible, protected in crisis', where_overdoes: 'avoidance through spirituality, inflated private beliefs' }
  };
  
  const signData = jupiterSignExpression[jupiter] || { believes: 'in growth', overdoes: 'expansion', finds_meaning: 'through experience' };
  const houseData = houseManifestations[jupiter_house] || { where_grows: 'across various life areas', where_overdoes: 'in general over-extension' };
  
  return {
    id: 'jupiter',
    title: 'Jupiter — Growth & Faith',
    subtitle: `${jupiter} in House ${jupiter_house}`,
    preview: `Believes ${signData.believes}. Growth shows up ${houseData.where_grows}.`,
    whatThisIs: `Jupiter in ${jupiter} (House ${jupiter_house}) marks where you say yes to life—where optimism lives, where you believe more is possible. ${signData.believes.charAt(0).toUpperCase() + signData.believes.slice(1)}—this is what feels true to you, what generates hope. But Jupiter also inflates. What you believe in, you can over-believe in.`,
    whatYouMightNotice: [
      `Expansion ${houseData.where_grows}`,
      `A tendency toward ${signData.overdoes}`,
      `Finding meaning ${signData.finds_meaning}`,
      `This area of life where things "work out"—sometimes too easily`
    ],
    tensionLabel: 'Where excess happens',
    tension: `Jupiter doesn't know when to stop. In House ${jupiter_house}, you may ${houseData.where_overdoes}. The optimism that opens doors can also prevent you from seeing limits. When things haven't worked, you may have believed yourself out of necessary reality-checks.`,
    giftLabel: 'Where faith lives',
    gift: `Even when life contracts elsewhere, this part of your chart remembers that more is possible. You regenerate through ${signData.finds_meaning}. Your genuine gift here isn't just luck—it's the capacity to believe when evidence is thin.`,
    reflection: `Where do you most naturally say yes? Where has that yes led to over-extension? What would it look like to trust without inflating?`
  };
};

// Saturn card - sign + house specific with psychological depth
const getSaturnCard = (placements: CorePlacements): AstrologyDeepDiveCard => {
  const saturn = placements.saturn || 'Unknown';
  const saturn_house = placements.saturn_house || 1;
  const saturnElement = SIGN_ELEMENTS[saturn] || 'Unknown';
  
  // Sign-specific Saturn expressions - what maturity asks for
  const saturnSignExpression: { [key: string]: { maturity_through: string; fear: string; eventual_authority: string } } = {
    'Aries': { maturity_through: 'learning to act with patience, to lead without dominating', fear: 'being first, being exposed, being alone in action', eventual_authority: 'disciplined initiative, earned confidence' },
    'Taurus': { maturity_through: 'building slowly, earning stability, valuing correctly', fear: 'scarcity, instability, losing what you have', eventual_authority: 'material wisdom, reliable presence' },
    'Gemini': { maturity_through: 'thinking precisely, communicating with weight', fear: 'being misunderstood, being seen as superficial', eventual_authority: 'intellectual rigor, trusted voice' },
    'Cancer': { maturity_through: 'emotional containment, healthy boundaries in care', fear: 'abandonment, emotional exposure, not belonging', eventual_authority: 'mature nurturing, emotional stability' },
    'Leo': { maturity_through: 'earning recognition, expressing with discipline', fear: 'being unseen, insignificant, or unspecial', eventual_authority: 'creative mastery, quiet confidence' },
    'Virgo': { maturity_through: 'precision without perfectionism, service without self-erasure', fear: 'being flawed, being useless, getting it wrong', eventual_authority: 'true competence, practical wisdom' },
    'Libra': { maturity_through: 'relationship with structure, commitment without losing self', fear: 'being alone, being rejected, being unfair', eventual_authority: 'relational wisdom, diplomatic skill' },
    'Scorpio': { maturity_through: 'control that doesn\'t destroy, depth without drowning', fear: 'betrayal, loss of power, being seen through', eventual_authority: 'psychological insight, regenerative capacity' },
    'Sagittarius': { maturity_through: 'grounding belief in practice, freedom with responsibility', fear: 'being trapped, being wrong about meaning', eventual_authority: 'lived wisdom, credible philosophy' },
    'Capricorn': { maturity_through: 'ambition with integrity, authority earned not assumed', fear: 'failure, public shame, being seen as unsuccessful', eventual_authority: 'genuine achievement, respected leadership' },
    'Aquarius': { maturity_through: 'individuality that contributes, ideas that build', fear: 'being ordinary, being controlled, selling out', eventual_authority: 'innovative structure, respected originality' },
    'Pisces': { maturity_through: 'boundaries around sensitivity, groundedness in imagination', fear: 'being overwhelmed, losing yourself, reality being too harsh', eventual_authority: 'compassionate realism, structured intuition' }
  };
  
  // House-specific Saturn work
  const saturnHouseWork: { [key: number]: { assignment: string; inner_critic: string; mastery: string } } = {
    1: { assignment: 'who you are—identity itself is the project', inner_critic: 'attacks your right to exist as you are', mastery: 'earned self-definition, presence that doesn\'t need approval' },
    2: { assignment: 'resources, security, self-worth', inner_critic: 'says you don\'t have enough, aren\'t worth enough', mastery: 'genuine security, value that you\'ve built' },
    3: { assignment: 'thinking, speaking, learning', inner_critic: 'doubts your intelligence, your voice, your ideas', mastery: 'intellectual authority, communication that lands' },
    4: { assignment: 'home, roots, emotional foundation', inner_critic: 'says you don\'t belong, weren\'t nurtured right', mastery: 'creating the home you didn\'t have, emotional groundedness' },
    5: { assignment: 'creativity, pleasure, self-expression', inner_critic: 'says your creations aren\'t good enough, joy is frivolous', mastery: 'disciplined creativity, earned joy' },
    6: { assignment: 'work, health, daily function', inner_critic: 'says you\'re not productive enough, not healthy enough', mastery: 'real competence, sustainable routines' },
    7: { assignment: 'partnership, commitment, relating', inner_critic: 'doubts your lovability, fears commitment', mastery: 'mature relationship, earned partnership' },
    8: { assignment: 'intimacy, shared power, transformation', inner_critic: 'fears vulnerability, loss of control, being consumed', mastery: 'earned trust, mastered intensity' },
    9: { assignment: 'belief, meaning, philosophy', inner_critic: 'questions your right to teach, your worldview', mastery: 'lived philosophy, credible vision' },
    10: { assignment: 'career, public role, authority', inner_critic: 'says you haven\'t earned your place, will be exposed', mastery: 'genuine authority, earned reputation' },
    11: { assignment: 'community, friendship, future vision', inner_critic: 'says you don\'t fit, your hopes are unrealistic', mastery: 'meaningful contribution, sustained community' },
    12: { assignment: 'solitude, spirituality, what\'s hidden', inner_critic: 'haunts with unnamed fears, old failures', mastery: 'integrated shadow, conscious solitude' }
  };
  
  const signData = saturnSignExpression[saturn] || { maturity_through: 'discipline', fear: 'inadequacy', eventual_authority: 'mastery' };
  const houseData = saturnHouseWork[saturn_house] || { assignment: 'life challenges', inner_critic: 'attacks you', mastery: 'earned wisdom' };
  
  return {
    id: 'saturn',
    title: 'Saturn — Pressure & Maturation',
    subtitle: `${saturn} in House ${saturn_house}`,
    preview: `Pressure concentrates in ${houseData.assignment}. The assignment is ${signData.maturity_through}.`,
    whatThisIs: `Saturn in ${saturn} (House ${saturn_house}) is your assignment—where life won't let you coast. The pressure is real: ${houseData.assignment} is where you face the most friction, the most delay, the most need to get serious. But what Saturn touches, you eventually master. The question isn't whether you'll struggle here—you will. The question is whether you'll let the struggle teach you.`,
    whatYouMightNotice: [
      `Recurring challenges around ${houseData.assignment}—things that don't come easy`,
      `A fear underneath: ${signData.fear}`,
      `Your inner critic ${houseData.inner_critic}`,
      `Over time: ${houseData.mastery}`
    ],
    tensionLabel: 'Where fear lives',
    tension: `Saturn points to where you feel inadequate, behind, or never-quite-good-enough. The fear is ${signData.fear}. You may avoid this area, over-control it, or work obsessively without ever feeling you've done enough. The pressure doesn't disappear—but your relationship to it can mature.`,
    giftLabel: 'What mastery looks like',
    gift: `What you've struggled with, you understand from the inside. ${houseData.mastery}. This isn't easy success or natural talent—it's competence that you've earned through persistence. Over time, you become the person others trust in this domain precisely because you've done the work.`,
    reflection: `Where do you feel like you're still catching up? What would it mean to be "good enough" in this area—not perfect, just sufficient?`
  };
};

// Nodes card - concrete developmental framing
const getNodesCard = (placements: CorePlacements): AstrologyDeepDiveCard => {
  const north_node = placements.north_node || 'Unknown';
  const south_node = placements.south_node || 'Unknown';
  const north_node_house = placements.north_node_house;
  const south_node_house = placements.south_node_house;
  
  // Sign-specific nodal axis - concrete behavioral descriptions
  const nodalExpressions: { [key: string]: { south_familiar: string; south_trap: string; north_asks: string; growth_feels_like: string } } = {
    // South Node first
    'Virgo_Pisces': {
      south_familiar: 'Fixing, analyzing, finding the flaw, earning your place through usefulness. You know how to be helpful, how to improve things, how to serve.',
      south_trap: 'Over-editing yourself before you start. Waiting until you have certainty before you move. Letting perfectionism become paralysis. Serving others to avoid your own unknowing.',
      north_asks: 'Trust without proof. Allowing not-knowing. Letting things be imperfect and finding that acceptable. Faith that you belong even when you haven\'t earned it.',
      growth_feels_like: 'Anxiety—like you\'re being irresponsible. The absence of your usual control mechanisms. Floating instead of fixing.'
    },
    'Pisces_Virgo': {
      south_familiar: 'Going with the flow, merging, dissolving into whatever\'s happening. You know how to adapt, to let go, to transcend.',
      south_trap: 'Avoiding practicality because it feels harsh. Escaping into vagueness when reality requires specificity. Compassion without discernment.',
      north_asks: 'Practical embodiment. Getting specific. Showing up in the details instead of floating above them. Useful contribution, not just being.',
      growth_feels_like: 'Constraining—like the poetry is getting edited out. Boring. But also more real, more grounded, more capable.'
    },
    'Aries_Libra': {
      south_familiar: 'Acting, initiating, going first, being independent. You know how to start things, how to compete, how to survive alone.',
      south_trap: 'Fighting battles that don\'t need fighting. Independence that becomes isolation. Always going first even when partnership would be wiser.',
      north_asks: 'Learning to include others. Compromise as strength. Letting relationship shape you. Fairness over victory.',
      growth_feels_like: 'Weak at first—like you\'re giving up your edge. Dependent. But eventually: supported, collaborative, less alone.'
    },
    'Libra_Aries': {
      south_familiar: 'Partnering, harmonizing, considering others, keeping the peace. You know how to relate, how to balance, how to not rock the boat.',
      south_trap: 'Waiting for permission. Over-compromising until you disappear. Avoiding conflict even when confrontation is exactly what\'s needed.',
      north_asks: 'Acting without consensus. Going first even when others aren\'t ready. Risking disapproval. Trusting your own initiative.',
      growth_feels_like: 'Selfish, rude, disconnected from relationship. But eventually: authentic, honest, actually present instead of performing.'
    },
    'Taurus_Scorpio': {
      south_familiar: 'Stability, comfort, accumulation, staying with what you have. You know how to build, how to enjoy, how to make things last.',
      south_trap: 'Holding on when it\'s time to release. Comfort that becomes stagnation. Avoiding the intensity that would actually transform you.',
      north_asks: 'Letting go. Transformation through crisis. Sharing power, sharing resources. Depth over security.',
      growth_feels_like: 'Destabilizing, scary, like the ground is moving. But eventually: renewed, transformed, alive in a way stability doesn\'t allow.'
    },
    'Scorpio_Taurus': {
      south_familiar: 'Intensity, depth, control, seeing what\'s hidden. You know how to navigate crisis, how to hold power, how to survive transformation.',
      south_trap: 'Creating crisis where there doesn\'t need to be one. Suspicion that prevents trust. Depth that becomes obsession.',
      north_asks: 'Simplicity. Enjoying the surface. Letting things be what they are instead of probing beneath. Comfort without guilt.',
      growth_feels_like: 'Shallow, naive, vulnerable to what you can\'t control. But eventually: peaceful, grounded, actually able to enjoy.'
    },
    'Gemini_Sagittarius': {
      south_familiar: 'Gathering information, making connections, staying curious, keeping options open. You know how to learn, how to adapt, how to converse.',
      south_trap: 'Scattered attention that never settles. Facts without meaning. Curiosity that avoids commitment to a perspective.',
      north_asks: 'Taking a position. Having a philosophy. Speaking with conviction. Meaning over information.',
      growth_feels_like: 'Presumptuous—like you\'re claiming more than you know. But eventually: purposeful, directed, actually going somewhere.'
    },
    'Sagittarius_Gemini': {
      south_familiar: 'Big picture thinking, meaning-making, following belief. You know how to philosophize, how to teach, how to see the horizon.',
      south_trap: 'Preaching without listening. Assuming your truth is universal. Avoiding details because they complicate the vision.',
      north_asks: 'Listening. Asking questions. Staying curious instead of concluding. Letting others\' perspectives actually change you.',
      growth_feels_like: 'Relativistic, groundless, like you\'ve lost your compass. But eventually: flexible, connected, actually in dialogue.'
    },
    'Cancer_Capricorn': {
      south_familiar: 'Nurturing, protecting, staying home, emotional attunement. You know how to care, how to belong, how to create safety.',
      south_trap: 'Hiding in family, using emotion to avoid achievement. Needing to be needed. Fear of the public world.',
      north_asks: 'Building in the world. Career as meaningful. Structure that holds beyond family. Achievement without abandoning care.',
      growth_feels_like: 'Cold, exposing, like leaving something precious unprotected. But eventually: accomplished, respected, mature.'
    },
    'Capricorn_Cancer': {
      south_familiar: 'Achieving, building, being responsible, public competence. You know how to work, how to succeed, how to hold authority.',
      south_trap: 'Work as avoidance. Achievement without connection. Responsibility that starves emotional life.',
      north_asks: 'Vulnerability. Home. Letting yourself need. Emotion as valid as accomplishment.',
      growth_feels_like: 'Soft, unproductive, like you\'re losing your edge. But eventually: supported, nurtured, actually at home somewhere.'
    },
    'Leo_Aquarius': {
      south_familiar: 'Self-expression, creativity, being special, personal significance. You know how to shine, how to create, how to be seen.',
      south_trap: 'Drama that demands attention. Creativity for approval. Specialness that isolates.',
      north_asks: 'Contributing to the group. Ideas over identity. Being part of something larger than your personal story.',
      growth_feels_like: 'Anonymous, unspecial, like you\'re disappearing into the crowd. But eventually: connected, useful, part of a vision.'
    },
    'Aquarius_Leo': {
      south_familiar: 'Group identity, ideas, innovation, being different. You know how to think originally, how to belong to a vision, how to stay detached.',
      south_trap: 'Hiding in ideas. Detachment as defense. Being contrarian instead of genuinely creative.',
      north_asks: 'Personal expression. Heart over intellect. Creating from your own center, not from ideology.',
      growth_feels_like: 'Exposed, embarrassing, like your individual self is too much or too little. But eventually: authentic, warm, genuinely creative.'
    }
  };
  
  // Get axis key
  const axisKey = `${south_node}_${north_node}`;
  const nodalData = nodalExpressions[axisKey] || {
    south_familiar: `${south_node} competence—what you already know how to do.`,
    south_trap: `Over-relying on ${south_node} patterns when they no longer serve growth.`,
    north_asks: `Moving toward ${north_node} unfamiliarity—less practiced, more growth.`,
    growth_feels_like: `Awkward, uncertain, but somehow right.`
  };
  
  return {
    id: 'nodes',
    title: 'Nodes — Direction & Pattern',
    subtitle: `☋ ${south_node}${south_node_house ? ` H${south_node_house}` : ''} → ☊ ${north_node}${north_node_house ? ` H${north_node_house}` : ''}`,
    preview: `${nodalData.south_familiar.split('.')[0]}. Growth asks: ${nodalData.north_asks.split('.')[0]}.`,
    whatThisIs: `The nodal axis is your developmental storyline—not what you're good at, but where you're headed. South Node in ${south_node} is your default: ${nodalData.south_familiar} But this competence has diminishing returns. North Node in ${north_node} is where life keeps pulling you—uncomfortable, less practiced, but where actual evolution happens.`,
    whatYouMightNotice: [
      `WHAT FEELS FAMILIAR: ${nodalData.south_familiar.split('.')[0]}`,
      `THE COMFORT TRAP: ${nodalData.south_trap}`,
      `WHERE LIFE PULLS YOU: ${nodalData.north_asks}`,
      `WHAT GROWTH FEELS LIKE: ${nodalData.growth_feels_like}`
    ],
    tensionLabel: 'The comfort trap',
    tension: nodalData.south_trap,
    giftLabel: 'What growth actually asks',
    gift: `The North Node isn't asking you to abandon your South Node gifts—it's asking you to use them in service of something new. ${nodalData.north_asks} This isn't about becoming someone else. It's about becoming more fully yourself by including what you've avoided.`,
    reflection: `What familiar pattern do you reach for when stressed? What would it actually feel like to move toward ${north_node} instead?`
  };
};

// Chiron card - precise wound/medicine framing
const getChironCard = (placements: CorePlacements): AstrologyDeepDiveCard => {
  const chiron = placements.chiron || 'Unknown';
  const chiron_house = placements.chiron_house || 1;
  
  // Sign-specific Chiron wounds - precise psychological descriptions
  const chironSignWounds: { [key: string]: { where_touched: string; learned_early: string; becomes_guidance: string; runs_system: string } } = {
    'Aries': {
      where_touched: 'Your right to exist, to act, to take up space. Something made self-assertion feel dangerous or wrong.',
      learned_early: 'To hesitate before moving, to question your own impulses, to doubt whether you\'re allowed to want what you want.',
      becomes_guidance: 'You understand what it costs to be unable to act. You can help others claim their own initiative because you know the fear of claiming yours.',
      runs_system: 'When you start second-guessing every impulse, needing permission for everything, or compensating with reckless action.'
    },
    'Taurus': {
      where_touched: 'Your worth, your body, your right to have and to enjoy. Something disrupted basic security or self-value.',
      learned_early: 'That stability isn\'t guaranteed, that worth needs to be proven, that pleasure might be taken away.',
      becomes_guidance: 'You understand embodiment struggles from the inside. You can help others reclaim their right to comfort because you know what it is to doubt your own.',
      runs_system: 'When you hoard, grasp, or can never enjoy what you have because more is never enough.'
    },
    'Gemini': {
      where_touched: 'Your mind, your voice, your intelligence. Something made thinking or speaking feel inadequate.',
      learned_early: 'To doubt your own thoughts, to filter everything before speaking, to assume you\'re not understanding correctly.',
      becomes_guidance: 'You understand communication struggles—being misheard, feeling stupid, thinking differently. You can help others find their voice because you know the fear of losing yours.',
      runs_system: 'When you talk too much to compensate, go silent to avoid exposure, or can never trust your own thinking.'
    },
    'Cancer': {
      where_touched: 'Your right to belong, to be nurtured, to have emotional needs. Something disrupted early care or family safety.',
      learned_early: 'That home might not be safe, that needs might overwhelm others, that belonging has to be earned.',
      becomes_guidance: 'You understand what it costs to feel homeless, emotionally orphaned. You can nurture others because you know what it is to have needed nurturing you didn\'t get.',
      runs_system: 'When you mother everyone except yourself, when you can\'t receive care, when belonging feels impossible.'
    },
    'Leo': {
      where_touched: 'Your right to be seen, to be special, to matter. Something shamed your self-expression or need for recognition.',
      learned_early: 'That standing out is dangerous, that wanting attention is shameful, that your shine threatens others.',
      becomes_guidance: 'You understand what it costs to dim yourself. You can help others reclaim their creative presence because you know the fear of being too much.',
      runs_system: 'When you either hide completely or demand constant attention, when you can\'t just be seen without drama.'
    },
    'Virgo': {
      where_touched: 'Your competence, your usefulness, your ability to get it right. Something made you feel fundamentally flawed.',
      learned_early: 'That you need to fix yourself before you\'re acceptable, that there\'s always more wrong, that perfection is the price of belonging.',
      becomes_guidance: 'You understand the tyranny of perfectionism from the inside. You can help others accept their imperfections because you know what it is to never feel good enough.',
      runs_system: 'When you criticize everything including yourself, when improvement becomes compulsion, when nothing is ever finished.'
    },
    'Libra': {
      where_touched: 'Your right to relationship, to fairness, to be loved as you are. Something disrupted partnership or made love conditional.',
      learned_early: 'That you need to perform harmony to be wanted, that your needs upset balance, that love requires constant adjustment.',
      becomes_guidance: 'You understand relationship wounds—rejection, imbalance, being left. You can help others with partnership because you know what it is to doubt your lovability.',
      runs_system: 'When you can\'t be alone but also can\'t fully commit, when you shape-shift to keep the peace, when fairness becomes obsession.'
    },
    'Scorpio': {
      where_touched: 'Your right to power, to depth, to be vulnerable. Something involved betrayal, trauma, or loss of control.',
      learned_early: 'That intimacy is dangerous, that power can be used against you, that what you love can be destroyed.',
      becomes_guidance: 'You understand crisis and transformation from the inside. You can guide others through their darkness because you\'ve survived yours.',
      runs_system: 'When you trust no one, when you use power preemptively, when you can\'t let anyone fully in.'
    },
    'Sagittarius': {
      where_touched: 'Your right to meaning, to truth, to believe. Something collapsed faith or made hope feel naive.',
      learned_early: 'That truth might be a lie, that belief leads to disappointment, that horizons might be illusions.',
      becomes_guidance: 'You understand the crisis of meaning from the inside. You can help others rebuild faith because you know what it is to lose yours.',
      runs_system: 'When you either preach compulsively or can\'t believe in anything, when cynicism masquerades as wisdom.'
    },
    'Capricorn': {
      where_touched: 'Your right to achieve, to be respected, to have authority. Something shamed ambition or made success feel dangerous.',
      learned_early: 'That achievement doesn\'t protect you, that respect isn\'t reliable, that you can do everything right and still fail.',
      becomes_guidance: 'You understand the burden of ambition from the inside. You can help others with their relationship to success because you know its cost.',
      runs_system: 'When you work obsessively but never feel accomplished, when you sabotage success before it can be taken, when authority terrifies you.'
    },
    'Aquarius': {
      where_touched: 'Your right to be different, to think independently, to belong while being yourself. Something made individuality feel isolating.',
      learned_early: 'That different means alone, that original thinking separates you, that fitting in requires suppressing what makes you you.',
      becomes_guidance: 'You understand outsider experience from the inside. You can help others claim their uniqueness because you know the cost of suppressing yours.',
      runs_system: 'When you either conform completely or reject belonging entirely, when difference becomes identity rather than quality.'
    },
    'Pisces': {
      where_touched: 'Your right to sensitivity, to imagination, to transcendence. Something overwhelmed your boundaries or made softness feel weak.',
      learned_early: 'That feeling too much is a liability, that imagination isn\'t real, that sensitivity has to be hidden.',
      becomes_guidance: 'You understand overwhelm and dissociation from the inside. You can help others with their sensitivity because you know what it costs to be porous.',
      runs_system: 'When you escape instead of engage, when boundaries dissolve completely, when you lose yourself in others or substances.'
    }
  };
  
  // House-specific Chiron manifestations
  const chironHouseManifestations: { [key: number]: { life_area: string; triggers: string } } = {
    1: { life_area: 'identity and self-presentation', triggers: 'being seen, first impressions, asserting who you are' },
    2: { life_area: 'self-worth and resources', triggers: 'money, possessions, valuing yourself' },
    3: { life_area: 'communication and thinking', triggers: 'expressing ideas, being understood, intellectual confidence' },
    4: { life_area: 'home and emotional foundation', triggers: 'family, belonging, emotional security' },
    5: { life_area: 'creativity and self-expression', triggers: 'creating, performing, being spontaneous' },
    6: { life_area: 'work and health', triggers: 'daily competence, usefulness, physical wellbeing' },
    7: { life_area: 'partnership and relating', triggers: 'commitment, being chosen, intimate relationship' },
    8: { life_area: 'intimacy and shared power', triggers: 'vulnerability, merging, trusting deeply' },
    9: { life_area: 'belief and meaning', triggers: 'faith, teaching, having conviction' },
    10: { life_area: 'career and public role', triggers: 'authority, achievement, being respected' },
    11: { life_area: 'community and future vision', triggers: 'belonging to groups, friendship, hopes' },
    12: { life_area: 'spirituality and the unconscious', triggers: 'isolation, surrender, facing what\'s hidden' }
  };
  
  const signData = chironSignWounds[chiron] || { 
    where_touched: 'a core area of sensitivity', 
    learned_early: 'to protect this vulnerable place', 
    becomes_guidance: 'understanding others\' similar wounds', 
    runs_system: 'when the wound takes over' 
  };
  const houseData = chironHouseManifestations[chiron_house] || { 
    life_area: 'certain life areas', 
    triggers: 'specific situations' 
  };
  
  return {
    id: 'chiron',
    title: 'Chiron — Wound & Medicine',
    subtitle: `${chiron} in House ${chiron_house}`,
    preview: `${signData.where_touched.split('.')[0]}. This wound concentrates in ${houseData.life_area}.`,
    whatThisIs: `Chiron in ${chiron} (House ${chiron_house}) marks where you carry a wound that doesn't fully close. This isn't failure—it's specificity. ${signData.where_touched} Because you've been sensitized in ${houseData.life_area}, you notice things others miss. The wound became intelligence.`,
    whatYouMightNotice: [
      `WHERE YOU GET TOUCHED: ${houseData.triggers} affect you more than they "should"`,
      `WHAT THIS MADE YOU LEARN EARLY: ${signData.learned_early}`,
      `HOW THIS BECOMES GUIDANCE: ${signData.becomes_guidance}`,
      `WHEN THE WOUND RUNS THE SYSTEM: ${signData.runs_system}`
    ],
    tensionLabel: 'When the wound takes over',
    tension: signData.runs_system,
    giftLabel: 'The medicine you carry',
    gift: signData.becomes_guidance,
    reflection: `What wound are you still trying to fix instead of integrate? Where might your specific sensitivity be exactly what someone else needs?`
  };
};

const getSynthesis = (sun: string, moon: string, asc: string): string => {
  const sunElement = SIGN_ELEMENTS[sun] || 'Unknown';
  const moonElement = SIGN_ELEMENTS[moon] || 'Unknown';
  const ascQualities = SIGN_QUALITIES[asc] || [];
  
  // Premium, bespoke synthesis that sounds less template-driven
  if (sunElement === 'Water' && moonElement === 'Fire') {
    return `In your chart, depth and immediacy coexist. The sensitivity of ${sun} grounds your identity in perception and feeling, while ${moon}'s fire moves emotion quickly—toward action, toward expression, toward honesty. ${asc} rising shapes how this meets the world: ${ascQualities[0] || 'openly'}, with room to breathe.`;
  } else if (sunElement === 'Fire' && moonElement === 'Earth') {
    return `Your chart holds vision and groundedness in tension. A ${sun} core reaches toward what's possible, while ${moon}'s earthy emotional nature prefers what's real and reliable. Through ${asc} rising, this combination enters life ${ascQualities[0] || 'distinctively'}—bold ideas meeting practical needs.`;
  } else if (sunElement === 'Air' && moonElement === 'Water') {
    return `This chart weaves thought and feeling together. ${sun}'s airy orientation keeps the mind curious and moving, but ${moon} in ${moonElement.toLowerCase()} runs deep—emotion that doesn't explain itself quickly. ${asc} rising adds ${ascQualities[0] || 'distinctive'} energy to how others first encounter you.`;
  } else if (sunElement === 'Earth' && moonElement === 'Air') {
    return `Stability and movement trade places in your chart. ${sun}'s earthy core values what lasts, while ${moon}'s air-sign emotional nature needs variety and mental stimulation. ${asc} rising brings ${ascQualities[0] || 'presence'} energy to how you meet new situations—grounded but not static.`;
  } else if (sunElement === moonElement) {
    return `There's a coherence in your chart—both core identity (${sun}) and emotional nature (${moon}) share ${sunElement.toLowerCase()} energy. What you are and how you feel operate in the same register. ${asc} rising adds texture: a ${ascQualities[0] || 'distinctive'} way of meeting the world that complements this inner consistency.`;
  }
  
  return `Your chart blends ${sun}'s ${sunElement.toLowerCase()} orientation with ${moon}'s ${moonElement.toLowerCase()} emotional process—two different registers working together. ${asc} rising shapes how this combination meets life: ${ascQualities[0] || 'openly'}, bringing its own quality to every entrance.`;
};

const getThemeChips = (sun: string, moon: string, asc: string): string[] => {
  const chips: string[] = [];
  const sunQualities = SIGN_QUALITIES[sun] || [];
  const moonQualities = SIGN_QUALITIES[moon] || [];
  const ascQualities = SIGN_QUALITIES[asc] || [];
  
  // Add unique qualities from each placement
  if (sunQualities[0]) chips.push(sunQualities[0]);
  if (moonQualities[1] && !chips.includes(moonQualities[1])) chips.push(moonQualities[1]);
  if (ascQualities[0] && !chips.includes(ascQualities[0])) chips.push(ascQualities[0]);
  if (sunQualities[2] && !chips.includes(sunQualities[2])) chips.push(sunQualities[2]);
  if (moonQualities[0] && !chips.includes(moonQualities[0])) chips.push(moonQualities[0]);
  if (ascQualities[2] && !chips.includes(ascQualities[2])) chips.push(ascQualities[2]);
  
  return chips.slice(0, 6);
};

const getCoreTensions = (sun: string, moon: string, asc: string): string[] => {
  const tensions: string[] = [];
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  const sunModality = SIGN_MODALITIES[sun];
  const moonModality = SIGN_MODALITIES[moon];
  const ascModality = SIGN_MODALITIES[asc];
  
  // Core element tensions - psychologically sharp descriptions
  if (sunElement === 'Water' && moonElement === 'Fire') {
    tensions.push('Your core absorbs everything, but your emotions want to act before processing finishes');
  }
  if (sunElement === 'Air' && moonElement === 'Earth') {
    tensions.push('Your mind moves faster than your emotional need for certainty allows');
  }
  if (sunElement === 'Fire' && moonElement === 'Water') {
    tensions.push('The urge to move forward meets a deeper pull to stay with what you feel');
  }
  if (sunElement === 'Earth' && moonElement === 'Air') {
    tensions.push('You want roots, but emotionally you need options');
  }
  
  // Modality-based tensions
  if (sunModality === 'Fixed' && moonModality === 'Mutable') {
    tensions.push('Identity wants consistency; feelings keep shifting the frame');
  }
  if (sunModality === 'Cardinal' && moonModality === 'Fixed') {
    tensions.push('The drive to initiate meets an emotional need to stay put');
  }
  if (sunModality === 'Mutable' && ascModality === 'Fixed') {
    tensions.push('Inner flexibility vs. a presentation style that commits early');
  }
  
  // Sign-specific psychological tensions
  if (sun === 'Pisces') tensions.push('Knowing where you end and others begin');
  if (moon === 'Aries') tensions.push('Needing emotional immediacy in a world that moves slower');
  if (asc === 'Sagittarius') tensions.push('Approaching life with optimism while carrying deeper complexity');
  if (asc === 'Scorpio') tensions.push('Meeting the world guardedly while wanting to be truly known');
  if (sun === 'Virgo' && moon !== 'Virgo') tensions.push('The perfectionist eye turned inward—never quite good enough');
  if (sun === 'Leo' && moonElement === 'Water') tensions.push('Needing to be seen while protecting something private');
  
  return tensions.slice(0, 4);
};

const getCoreGifts = (sun: string, moon: string, asc: string): string[] => {
  const gifts: string[] = [];
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  
  // Element-based gifts
  if (sunElement === 'Water') gifts.push('imaginative perception');
  if (sunElement === 'Fire') gifts.push('natural enthusiasm');
  if (sunElement === 'Earth') gifts.push('practical wisdom');
  if (sunElement === 'Air') gifts.push('mental agility');
  
  if (moonElement === 'Fire') gifts.push('emotional honesty');
  if (moonElement === 'Water') gifts.push('deep empathy');
  if (moonElement === 'Earth') gifts.push('emotional steadiness');
  if (moonElement === 'Air') gifts.push('emotional objectivity');
  
  // Asc-based gifts
  if (SIGN_QUALITIES[asc]) {
    const ascQuality = SIGN_QUALITIES[asc][3];
    if (ascQuality && !gifts.includes(ascQuality)) {
      gifts.push(ascQuality);
    }
  }
  
  // Unique combinations
  if (sun === 'Pisces' && moon === 'Aries') gifts.push('intuitive decisiveness');
  if (sun === 'Leo' && asc === 'Virgo') gifts.push('expressive precision');
  
  return gifts.slice(0, 4);
};

// Helper to analyze house concentration
const getHouseConcentration = (placements: CorePlacements): { dominant: number[], emphasis: string, insight: string } => {
  const houseCounts: { [key: number]: string[] } = {};
  
  // Count planets per house
  if (placements.sun_house) {
    houseCounts[placements.sun_house] = houseCounts[placements.sun_house] || [];
    houseCounts[placements.sun_house].push('Sun');
  }
  if (placements.moon_house) {
    houseCounts[placements.moon_house] = houseCounts[placements.moon_house] || [];
    houseCounts[placements.moon_house].push('Moon');
  }
  if (placements.mercury_house) {
    houseCounts[placements.mercury_house] = houseCounts[placements.mercury_house] || [];
    houseCounts[placements.mercury_house].push('Mercury');
  }
  if (placements.venus_house) {
    houseCounts[placements.venus_house] = houseCounts[placements.venus_house] || [];
    houseCounts[placements.venus_house].push('Venus');
  }
  if (placements.mars_house) {
    houseCounts[placements.mars_house] = houseCounts[placements.mars_house] || [];
    houseCounts[placements.mars_house].push('Mars');
  }
  if (placements.saturn_house) {
    houseCounts[placements.saturn_house] = houseCounts[placements.saturn_house] || [];
    houseCounts[placements.saturn_house].push('Saturn');
  }
  
  // Find dominant houses (2+ planets)
  const dominant = Object.entries(houseCounts)
    .filter(([_, planets]) => planets.length >= 2)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([house]) => parseInt(house));
  
  // Build emphasis description
  const HOUSE_THEMES: { [key: number]: string } = {
    1: 'self-expression and identity',
    2: 'resources, values, and security',
    3: 'communication, learning, and daily environment',
    4: 'home, roots, and emotional foundation',
    5: 'creativity, pleasure, and self-expression',
    6: 'work, health, and daily service',
    7: 'relationships and partnerships',
    8: 'transformation and shared resources',
    9: 'beliefs, travel, and higher meaning',
    10: 'career, reputation, and public role',
    11: 'community, friends, and future vision',
    12: 'spirituality, solitude, and the unconscious'
  };
  
  if (dominant.length >= 2) {
    return {
      dominant,
      emphasis: `Your chart concentrates in Houses ${dominant[0]} and ${dominant[1]}—${HOUSE_THEMES[dominant[0]]} and ${HOUSE_THEMES[dominant[1]]}.`,
      insight: `Life keeps pulling you toward these domains. Other areas may feel less developed by comparison.`
    };
  } else if (dominant.length === 1) {
    return {
      dominant,
      emphasis: `House ${dominant[0]} carries significant weight in your chart—${HOUSE_THEMES[dominant[0]]}.`,
      insight: `This is where life concentrates. You may have developed real depth here, while other areas remain more peripheral.`
    };
  }
  
  return {
    dominant: [],
    emphasis: `Your chart is relatively distributed across houses—no single area dominates.`,
    insight: `This can mean versatility, but also a tendency to spread attention rather than specialize.`
  };
};

// ============================================
// DEEP DIVE CARD GENERATOR
// ============================================

const generateDeepDiveCards = (placements: CorePlacements): AstrologyDeepDiveCard[] => {
  const { sun, sun_house, moon, moon_house, ascendant, mercury, mercury_house, venus, venus_house, mars, mars_house } = placements;
  
  const sunQualities = SIGN_QUALITIES[sun] || ['distinctive'];
  const moonQualities = SIGN_QUALITIES[moon] || ['deep'];
  const ascQualities = SIGN_QUALITIES[ascendant] || ['open'];
  const mercQualities = SIGN_QUALITIES[mercury || sun] || ['quick'];
  const venusQualities = SIGN_QUALITIES[venus || moon] || ['receptive'];
  const marsQualities = SIGN_QUALITIES[mars || sun] || ['direct'];
  
  // Get house concentration analysis
  const houseAnalysis = getHouseConcentration(placements);
  
  // Get psychological tensions
  const chartTensions = getCoreTensions(sun, moon, ascendant);
  
  const cards: AstrologyDeepDiveCard[] = [
    {
      id: 'sun',
      title: 'Sun — Core Identity',
      subtitle: `${sun}${sun_house ? ` in the ${getHouseOrdinal(sun_house)} house` : ''}`,
      preview: `In your chart, a ${sunQualities[0]} core that seeks ${sunQualities[2] || sunQualities[1]} expression.`,
      whatThisIs: `In your chart, the Sun in ${sun}${sun_house ? ` placed in House ${sun_house}` : ''} establishes the essential frequency of who you are. This isn't your whole identity—but it's the thread that runs through everything, the part that seeks expression and recognition. ${sun_house ? `With this energy concentrated in ${getHouseTheme(sun_house)}, your sense of self develops through that domain.` : ''}`,
      whatYouMightNotice: [
        `A ${sunQualities[0]} quality running through how you express yourself`,
        `Natural attraction toward ${sunQualities[2] || sunQualities[1]} activities and people`,
        `Feeling most yourself when you can be genuinely ${sunQualities[1]}`,
        sun_house ? `Identity themes playing out specifically through ${getHouseTheme(sun_house)}` : `This as your general life orientation`
      ],
      tensionLabel: 'The shadow side',
      tension: getSunTension(sun),
      giftLabel: 'What you are here to express',
      gift: getSunGift(sun),
      reflection: `When do you feel most like yourself? What conditions allow this ${sunQualities[0]} nature to come through naturally?`
    },
    {
      id: 'moon',
      title: 'Moon — Emotional Nature',
      subtitle: `${moon}${moon_house ? ` in the ${getHouseOrdinal(moon_house)} house` : ''}`,
      preview: `In your chart, feelings that move ${moonQualities[0]}, needing ${getMoonNeed(moon)} to settle.`,
      whatThisIs: `In your chart, the Moon in ${moon}${moon_house ? ` placed in House ${moon_house}` : ''} reveals your emotional substrate—what you need before you can think, what makes you feel safe, how you nurture and are nurtured. ${moon_house ? `With emotional energy concentrated around ${getHouseTheme(moon_house)}, this is where your inner life meets outer reality.` : ''} This is the part of you that responds before you've decided how to respond.`,
      whatYouMightNotice: [
        `Emotional responses that feel ${moonQualities[0]}—before thought catches up`,
        `A need for ${getMoonNeed(moon)} to feel genuinely settled`,
        `Comfort patterns that involve ${moonQualities[2] || moonQualities[1]} activities`,
        moon_house ? `Emotional sensitivity concentrated around ${getHouseTheme(moon_house)} matters` : `This emotional coloring present everywhere`
      ],
      tensionLabel: 'What tightens emotionally',
      tension: getMoonTension(moon),
      giftLabel: 'The gift in how you feel',
      gift: getMoonGift(moon),
      reflection: `What do you reach for when you need comfort? What does "feeling safe" actually require?`
    },
    {
      id: 'ascendant',
      title: 'Ascendant — How You Meet Life',
      subtitle: 'Your instinctive approach to new situations.',
      preview: 'The way you naturally meet people, change, and new situations.',
      whatThisIs: `${ascendant} rising colors the lens through which you approach everything new—first meetings, fresh starts, unfamiliar territory. It's not who you are inside, but how you instinctively engage.`,
      whatYouMightNotice: [
        `first impressions that come across as ${ascQualities[0]}`,
        `an instinctive ${ascQualities[1]} approach to new situations`,
        `others often perceive you as ${ascQualities[2] || ascQualities[0]} initially`,
        `your physical presence and style reflecting ${ascQualities[0]} energy`
      ],
      tensionLabel: 'The mask',
      tension: getAscTension(ascendant),
      giftLabel: 'What opens doors',
      gift: getAscGift(ascendant),
      reflection: `How do you typically enter a room of strangers? What energy do you project before people know you?`
    },
    {
      id: 'mercury',
      title: 'Mercury — Mind & Communication',
      subtitle: `${mercury || sun}${mercury_house ? ` in the ${getHouseOrdinal(mercury_house)} house` : ''}`,
      preview: `In your chart, a ${mercQualities[0]} mind that processes through ${getMercuryLearningStyle(mercury || sun)}.`,
      whatThisIs: `In your chart, Mercury in ${mercury || sun}${mercury_house ? ` placed in House ${mercury_house}` : ''} reveals how your mind naturally operates—how you sort information, what kind of thinking comes easily, and how you express what you know. ${mercury_house && mercury_house !== sun_house ? `With mental energy concentrated in ${getHouseTheme(mercury_house)} while your identity operates through House ${sun_house || 'elsewhere'}, you may think about different things than you identify with.` : mercury_house ? `Your mind and identity share the same house—what you think about is closely linked to who you are.` : ''}`,
      whatYouMightNotice: [
        `A ${mercQualities[0]} quality to how you think and process`,
        `Learning that works best through ${getMercuryLearningStyle(mercury || sun)} methods`,
        `Communication that tends to be ${mercQualities[1]}—even when you try otherwise`,
        mercury_house ? `Mental focus naturally gravitating toward ${getHouseTheme(mercury_house)} topics` : `Broad intellectual interests without a single focus`
      ],
      tensionLabel: 'Where the mind gets stuck',
      tension: getMercuryTension(mercury || sun),
      giftLabel: 'Your cognitive edge',
      gift: getMercuryGift(mercury || sun),
      reflection: `How do you process new information? What conditions help you think most clearly?`
    },
    {
      id: 'venus',
      title: 'Venus — Love & Relating',
      subtitle: `${venus || moon}${venus_house ? ` in the ${getHouseOrdinal(venus_house)} house` : ''}`,
      preview: `In your chart, drawn to ${venusQualities[0]} beauty, showing love through ${getVenusLoveLanguage(venus || moon)}.`,
      whatThisIs: `In your chart, Venus in ${venus || moon}${venus_house ? ` placed in House ${venus_house}` : ''} reveals what you find genuinely beautiful, how you attract and are attracted, and what you value in love and friendship. ${venus_house ? `With relational energy concentrated in ${getHouseTheme(venus_house)}, connection and aesthetics play out through this domain.` : ''}`,
      whatYouMightNotice: [
        `Attraction to ${venusQualities[0]} people, places, and experiences`,
        `Showing love through ${getVenusLoveLanguage(venus || moon)}—sometimes before you realize it`,
        `Valuing ${venusQualities[2] || venusQualities[1]} qualities in relationships`,
        venus_house ? `Relationship themes concentrated in ${getHouseTheme(venus_house)} areas` : `A general approach to relating across contexts`
      ],
      tensionLabel: 'Relational blind spot',
      tension: getVenusTension(venus || moon),
      giftLabel: 'Gift in connection',
      gift: getVenusGift(venus || moon),
      reflection: `What do you find genuinely beautiful? How do you show someone they matter to you?`
    },
    {
      id: 'mars',
      title: 'Mars — Drive & Friction',
      subtitle: `${mars || sun}${mars_house ? ` in the ${getHouseOrdinal(mars_house)} house` : ''}`,
      preview: `In your chart, a ${marsQualities[0]} approach to action and conflict.`,
      whatThisIs: `In your chart, Mars in ${mars || sun}${mars_house ? ` placed in House ${mars_house}` : ''} reveals how you take action, what ignites your drive, and how you handle conflict and desire. ${mars_house ? `With assertive energy concentrated in ${getHouseTheme(mars_house)}, this is where you push hardest and clash most easily.` : ''}`,
      whatYouMightNotice: [
        `A ${marsQualities[0]} style when you take action or initiate`,
        `Anger that tends to express as ${getMarsAngerStyle(mars || sun)}`,
        `Motivation strongest when pursuing ${marsQualities[2] || marsQualities[1]} goals`,
        mars_house ? `Drive and friction concentrated in ${getHouseTheme(mars_house)} areas` : `General assertive energy across contexts`
      ],
      tensionLabel: 'Where you clash',
      tension: getMarsTension(mars || sun),
      giftLabel: 'Your power',
      gift: getMarsGift(mars || sun),
      reflection: `What makes you want to fight for something? How do you handle frustration?`
    },
    // === ENHANCED: Jupiter - using new psychologically precise generator ===
    getJupiterCard(placements),
    // === ENHANCED: Saturn - using new psychologically precise generator ===
    getSaturnCard(placements),
    // === ENHANCED: Nodes - concrete developmental framing ===
    getNodesCard(placements),
    // === ENHANCED: Chiron - precise wound/medicine framing ===
    getChironCard(placements),
    {
      id: 'houses',
      title: 'House Emphasis',
      subtitle: 'Where life keeps pulling your attention.',
      preview: houseAnalysis.emphasis,
      whatThisIs: houseAnalysis.dominant.length > 0 
        ? `${houseAnalysis.emphasis} ${houseAnalysis.insight}`
        : `Your chart distributes energy across multiple life areas. While no single house dominates, certain themes still emerge from where key planets fall.`,
      whatYouMightNotice: [
        sun_house ? `Your identity (Sun) operates through House ${sun_house}—${getHouseTheme(sun_house)}` : `A broad identity expression`,
        moon_house ? `Your emotional needs (Moon) center on House ${moon_house}—${getHouseTheme(moon_house)}` : `Emotional needs spread across areas`,
        houseAnalysis.dominant.length > 0 
          ? `Houses ${houseAnalysis.dominant.join(' and ')} receiving disproportionate attention`
          : `No single house dominates—but scattered focus has its own challenges`,
        mercury_house && mercury_house === sun_house 
          ? `Mind and identity share the same house—thinking and being are intertwined`
          : mercury_house 
            ? `Mental energy (Mercury) flows toward House ${mercury_house}—${getHouseTheme(mercury_house)}`
            : `Mental energy follows your Sun sign's orientation`
      ],
      tensionLabel: 'What gets overdeveloped',
      tension: houseAnalysis.dominant.length > 0
        ? `When Houses ${houseAnalysis.dominant.join(' and ')} absorb most of your energy, other life areas may feel neglected or underdeveloped. The underused houses still exist—they're just waiting.`
        : `With a distributed chart, the tension is dilution rather than concentration. You may struggle to specialize or go deep in any one domain.`,
      giftLabel: 'Where you develop depth',
      gift: houseAnalysis.dominant.length > 0
        ? `Your concentration in specific houses means you can develop real mastery and depth in those life areas. This isn't limitation—it's specialization that builds over time.`
        : `A distributed chart gives you versatility and the ability to engage with many life areas without fixation. You're less likely to over-identify with any single domain.`,
      reflection: `Which area of life has demanded the most from you? Which feels like it's waiting for attention?`
    },
    {
      id: 'tensions',
      title: 'Core Chart Tensions',
      subtitle: 'The contradictions that make you complex.',
      preview: chartTensions.length > 0 ? chartTensions[0] : 'Inner pulls that shape your experience.',
      whatThisIs: `Your chart holds tensions that don't resolve—they coexist. These are the places where different parts of you want different things. In your case: ${chartTensions.slice(0, 2).join('; ')}.`,
      whatYouMightNotice: chartTensions.length > 0
        ? chartTensions.map(t => t)
        : [
            `A general sense of inner contradiction`,
            `Difficulty committing to one mode of being`,
            `These tensions showing up in relationships and decisions`
          ],
      tensionLabel: 'The psychological bind',
      tension: `When these tensions feel like problems to fix, you may flip between extremes—trying to be one thing, then overcorrecting to the other. The work isn't choosing one side. It's learning to hold both.`,
      giftLabel: 'The range they create',
      gift: `These tensions are why you have range. You can access different modes of being because you contain contradictory drives. Integration doesn't mean resolution—it means spaciousness.`,
      reflection: `Which of these contradictions is loudest in your life right now? What would it look like to stop trying to fix it?`
    },
    {
      id: 'opens',
      title: 'What This Chart Opens',
      subtitle: 'What becomes possible as you grow.',
      preview: 'What becomes possible when the chart matures.',
      whatThisIs: `Your chart isn't a limitation—it's a specific kind of instrument. As you mature and integrate, certain capacities naturally develop from this particular configuration.`,
      whatYouMightNotice: [
        ...getCoreGifts(sun, moon, ascendant).map(g => `growing capacity for ${g}`),
        `earlier tensions becoming sources of wisdom`
      ],
      tensionLabel: 'What you\'re releasing',
      tension: `Growth asks you to release rigid identification with any single part of your chart. You are not your Sun sign—you're the whole pattern.`,
      giftLabel: 'What emerges',
      gift: `As you integrate all parts of this chart, you develop a unique form of wisdom that only this combination can produce.`,
      reflection: `What part of yourself are you just beginning to trust?`
    }
  ];
  
  return cards;
};

// Helper functions for card content
const getHouseTheme = (house: number): string => {
  const themes: { [key: number]: string } = {
    1: 'self and identity',
    2: 'resources and values',
    3: 'communication and learning',
    4: 'home and roots',
    5: 'creativity and pleasure',
    6: 'work and health',
    7: 'relationships and partnership',
    8: 'transformation and shared resources',
    9: 'beliefs and expansion',
    10: 'career and public role',
    11: 'community and future vision',
    12: 'spirituality and the unconscious'
  };
  return themes[house] || 'various life areas';
};

const getHouseOrdinal = (house: number): string => {
  const ordinals: { [key: number]: string } = {
    1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th', 6: '6th',
    7: '7th', 8: '8th', 9: '9th', 10: '10th', 11: '11th', 12: '12th'
  };
  return ordinals[house] || `${house}th`;
};

const getSunTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Impatience and self-centeredness when the pioneering spirit isn\'t channeled productively.',
    'Taurus': 'Stubbornness and resistance to change when comfort becomes more important than growth.',
    'Gemini': 'Superficiality and restlessness when curiosity scatters without depth.',
    'Cancer': 'Over-protectiveness and moodiness when security feels threatened.',
    'Leo': 'Pride and need for attention when self-expression becomes performance for approval.',
    'Virgo': 'Criticism and perfectionism when the desire to improve turns harsh.',
    'Libra': 'Indecision and people-pleasing when harmony-seeking avoids necessary conflict.',
    'Scorpio': 'Control and intensity when depth becomes obsession or manipulation.',
    'Sagittarius': 'Over-promising and restlessness when expansion lacks grounding.',
    'Capricorn': 'Rigidity and workaholism when ambition forgets life\'s other dimensions.',
    'Aquarius': 'Detachment and contrarianism when independence becomes isolation.',
    'Pisces': 'Escapism and boundary issues when sensitivity lacks containment.'
  };
  return tensions[sign] || 'Over-identification with one mode of expression.';
};

const getSunGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'The ability to initiate, to begin, to bring courage when others hesitate.',
    'Taurus': 'The capacity to build lasting value and bring steadiness to chaos.',
    'Gemini': 'Mental versatility and the gift of making connections others miss.',
    'Cancer': 'Emotional intelligence and the ability to create safety for others.',
    'Leo': 'Warmth and the capacity to bring joy and recognition to others.',
    'Virgo': 'Discernment and the ability to improve anything you touch.',
    'Libra': 'Grace in relationship and the gift of creating beauty and harmony.',
    'Scorpio': 'Depth of perception and the power to transform what others avoid.',
    'Sagittarius': 'Vision and the ability to inspire others toward meaning.',
    'Capricorn': 'Mastery and the capacity to build structures that endure.',
    'Aquarius': 'Original thinking and the gift of seeing future possibilities.',
    'Pisces': 'Imagination and the ability to access dimensions others can\'t perceive.'
  };
  return gifts[sign] || 'A unique orientation that only you can bring.';
};

const getMoonNeed = (sign: string): string => {
  const needs: { [key: string]: string } = {
    'Aries': 'action and independence',
    'Taurus': 'stability and sensory comfort',
    'Gemini': 'mental stimulation and variety',
    'Cancer': 'emotional security and belonging',
    'Leo': 'recognition and warmth',
    'Virgo': 'order and usefulness',
    'Libra': 'harmony and connection',
    'Scorpio': 'emotional depth and privacy',
    'Sagittarius': 'freedom and meaning',
    'Capricorn': 'structure and achievement',
    'Aquarius': 'space and intellectual engagement',
    'Pisces': 'transcendence and creative flow'
  };
  return needs[sign] || 'specific conditions';
};

const getMoonTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Emotional impulsiveness can create conflict before reflection catches up.',
    'Taurus': 'Emotional stubbornness can make it hard to adapt when circumstances change.',
    'Gemini': 'Emotional restlessness can prevent deep processing of difficult feelings.',
    'Cancer': 'Over-attachment to the past can limit present emotional availability.',
    'Leo': 'The need for appreciation can make emotional expression performative.',
    'Virgo': 'Self-criticism can interrupt the natural flow of feeling.',
    'Libra': 'The need for others\' approval can disconnect you from your own feelings.',
    'Scorpio': 'Emotional intensity can overwhelm both self and others.',
    'Sagittarius': 'The urge to find meaning can bypass necessary grief.',
    'Capricorn': 'Emotional control can create distance from vulnerability.',
    'Aquarius': 'Emotional detachment can feel like safety but create loneliness.',
    'Pisces': 'Emotional permeability can blur boundaries and absorb others\' feelings.'
  };
  return tensions[sign] || 'A particular emotional pattern that needs awareness.';
};

const getMoonGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Emotional honesty and the ability to take action from feeling.',
    'Taurus': 'Emotional steadiness that others can rely on.',
    'Gemini': 'Emotional flexibility and the ability to articulate feeling.',
    'Cancer': 'Deep empathy and the instinct to nurture and protect.',
    'Leo': 'Emotional generosity and the gift of making others feel seen.',
    'Virgo': 'Emotional precision and the ability to show love through care.',
    'Libra': 'Emotional grace and the capacity for true partnership.',
    'Scorpio': 'Emotional depth and the power to transform through feeling.',
    'Sagittarius': 'Emotional resilience and the ability to find hope.',
    'Capricorn': 'Emotional maturity and the capacity for responsibility.',
    'Aquarius': 'Emotional objectivity and the ability to hold space.',
    'Pisces': 'Emotional attunement and access to collective feeling.'
  };
  return gifts[sign] || 'A particular emotional capacity.';
};

const getAscTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'The mask can be too aggressive, intimidating others before they know you.',
    'Taurus': 'The mask can be too fixed, making you seem resistant to change.',
    'Gemini': 'The mask can be too scattered, making you seem unreliable.',
    'Cancer': 'The mask can be too protective, making connection feel risky.',
    'Leo': 'The mask can demand too much attention, overshadowing others.',
    'Virgo': 'The mask can be too critical, putting others on the defensive.',
    'Libra': 'The mask can be too accommodating, hiding your real preferences.',
    'Scorpio': 'The mask can be too intense, creating distance through intimidation.',
    'Sagittarius': 'The mask can promise more than you deliver, creating disappointment.',
    'Capricorn': 'The mask can be too serious, hiding your warmth.',
    'Aquarius': 'The mask can be too detached, making connection feel impossible.',
    'Pisces': 'The mask can be too diffuse, making it hard for others to find you.'
  };
  return tensions[sign] || 'The way you present can sometimes obscure who you really are.';
};

const getAscGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Your directness and courage make you a natural initiator.',
    'Taurus': 'Your steadiness makes others feel safe in your presence.',
    'Gemini': 'Your curiosity makes you instantly engaging and adaptable.',
    'Cancer': 'Your warmth makes others feel cared for immediately.',
    'Leo': 'Your presence lights up rooms and draws people in.',
    'Virgo': 'Your competence and helpfulness earn immediate respect.',
    'Libra': 'Your grace and charm create instant ease with others.',
    'Scorpio': 'Your depth and presence make interactions feel meaningful.',
    'Sagittarius': 'Your enthusiasm and openness invite adventure.',
    'Capricorn': 'Your seriousness and reliability inspire trust.',
    'Aquarius': 'Your uniqueness makes you memorable and intriguing.',
    'Pisces': 'Your gentleness and receptivity make others feel accepted.'
  };
  return gifts[sign] || 'A distinctive way of meeting the world.';
};

const getMercuryLearningStyle = (sign: string): string => {
  const styles: { [key: string]: string } = {
    'Aries': 'active, hands-on',
    'Taurus': 'slow, sensory',
    'Gemini': 'varied, conversational',
    'Cancer': 'emotional, story-based',
    'Leo': 'creative, demonstrative',
    'Virgo': 'systematic, detailed',
    'Libra': 'collaborative, aesthetic',
    'Scorpio': 'deep, investigative',
    'Sagittarius': 'conceptual, philosophical',
    'Capricorn': 'structured, practical',
    'Aquarius': 'innovative, unconventional',
    'Pisces': 'intuitive, imaginative'
  };
  return styles[sign] || 'distinctive';
};

const getMercuryTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Thinking can be too quick, missing nuance in pursuit of conclusions.',
    'Taurus': 'Thinking can be too slow, struggling to adapt to new information.',
    'Gemini': 'Thinking can scatter, pursuing many threads without synthesis.',
    'Cancer': 'Thinking can be colored by mood, losing objectivity.',
    'Leo': 'Thinking can serve ego, dismissing ideas that don\'t flatter.',
    'Virgo': 'Thinking can get lost in details, missing bigger patterns.',
    'Libra': 'Thinking can defer to others, losing your own perspective.',
    'Scorpio': 'Thinking can become obsessive, unable to let go.',
    'Sagittarius': 'Thinking can be too broad, lacking precision.',
    'Capricorn': 'Thinking can be too rigid, missing creative possibilities.',
    'Aquarius': 'Thinking can be too abstract, disconnecting from practical reality.',
    'Pisces': 'Thinking can be too impressionistic, lacking structure.'
  };
  return tensions[sign] || 'A cognitive pattern that needs awareness.';
};

const getMercuryGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Quick, decisive thinking that cuts to the point.',
    'Taurus': 'Thorough, practical thinking that builds solid foundations.',
    'Gemini': 'Versatile thinking that makes surprising connections.',
    'Cancer': 'Intuitive thinking that senses what isn\'t said.',
    'Leo': 'Creative thinking that inspires and persuades.',
    'Virgo': 'Precise thinking that catches what others miss.',
    'Libra': 'Balanced thinking that sees multiple perspectives.',
    'Scorpio': 'Deep thinking that penetrates to root causes.',
    'Sagittarius': 'Big-picture thinking that finds meaning in patterns.',
    'Capricorn': 'Strategic thinking that plans for the long term.',
    'Aquarius': 'Original thinking that sees future possibilities.',
    'Pisces': 'Imaginative thinking that transcends ordinary categories.'
  };
  return gifts[sign] || 'A distinctive cognitive capacity.';
};

const getVenusLoveLanguage = (sign: string): string => {
  const languages: { [key: string]: string } = {
    'Aries': 'direct action and enthusiasm',
    'Taurus': 'physical presence and gifts',
    'Gemini': 'conversation and mental connection',
    'Cancer': 'nurturing and emotional attunement',
    'Leo': 'grand gestures and admiration',
    'Virgo': 'acts of service and attention to detail',
    'Libra': 'romantic partnership and aesthetic sharing',
    'Scorpio': 'deep emotional intensity and loyalty',
    'Sagittarius': 'shared adventures and philosophical connection',
    'Capricorn': 'commitment and practical support',
    'Aquarius': 'intellectual friendship and freedom',
    'Pisces': 'romantic transcendence and emotional merging'
  };
  return languages[sign] || 'distinctive expressions of care';
};

const getVenusTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Love can be impatient, demanding excitement over depth.',
    'Taurus': 'Love can become possessive when security feels threatened.',
    'Gemini': 'Love can be fickle when variety competes with commitment.',
    'Cancer': 'Love can be smothering when nurturing becomes control.',
    'Leo': 'Love can demand recognition, making partners feel like audiences.',
    'Virgo': 'Love can be critical, improving instead of accepting.',
    'Libra': 'Love can lose self in partnership, abandoning personal needs.',
    'Scorpio': 'Love can become obsessive or test loyalty destructively.',
    'Sagittarius': 'Love can resist commitment in pursuit of freedom.',
    'Capricorn': 'Love can become conditional on achievement.',
    'Aquarius': 'Love can be too detached, maintaining distance as safety.',
    'Pisces': 'Love can lose boundaries, sacrificing self for merger.'
  };
  return tensions[sign] || 'A relational pattern that needs awareness.';
};

const getVenusGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Passionate, direct love that doesn\'t play games.',
    'Taurus': 'Loyal, sensual love that creates lasting stability.',
    'Gemini': 'Curious, communicative love that keeps relating fresh.',
    'Cancer': 'Nurturing, devoted love that creates emotional home.',
    'Leo': 'Generous, warm love that makes partners feel special.',
    'Virgo': 'Attentive, devoted love shown through care.',
    'Libra': 'Graceful, harmonious love that creates true partnership.',
    'Scorpio': 'Deep, transformative love that demands authenticity.',
    'Sagittarius': 'Adventurous, generous love that expands both people.',
    'Capricorn': 'Committed, supportive love that builds over time.',
    'Aquarius': 'Accepting, freedom-giving love that respects individuality.',
    'Pisces': 'Compassionate, imaginative love that transcends the ordinary.'
  };
  return gifts[sign] || 'A distinctive relational capacity.';
};

const getMarsAngerStyle = (sign: string): string => {
  const styles: { [key: string]: string } = {
    'Aries': 'quick, direct, and usually over fast',
    'Taurus': 'slow-building but explosive when pushed too far',
    'Gemini': 'verbal, sharp, sometimes passive-aggressive',
    'Cancer': 'moody, indirect, sometimes through withdrawal',
    'Leo': 'dramatic, proud, needing acknowledgment',
    'Virgo': 'critical, nitpicking, sometimes self-directed',
    'Libra': 'passive-aggressive, conflict-avoiding',
    'Scorpio': 'intense, strategic, holding grudges',
    'Sagittarius': 'righteous, philosophical, then forgotten',
    'Capricorn': 'cold, controlled, expressed through authority',
    'Aquarius': 'detached, intellectual, sometimes erratic',
    'Pisces': 'indirect, victimized, or turned inward'
  };
  return styles[sign] || 'a distinctive pattern';
};

const getMarsTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Aggression can be impulsive, creating conflict unnecessarily.',
    'Taurus': 'Stubbornness can resist necessary change or confrontation.',
    'Gemini': 'Scattered energy can dilute the power of focused action.',
    'Cancer': 'Passive-aggression can undermine direct communication.',
    'Leo': 'Pride can make every conflict about ego rather than issues.',
    'Virgo': 'Perfectionism can create frustration with self and others.',
    'Libra': 'Conflict avoidance can let resentment build silently.',
    'Scorpio': 'Intensity can become controlling or manipulative.',
    'Sagittarius': 'Over-promise and under-deliver when enthusiasm fades.',
    'Capricorn': 'Ambition can override ethics or relationships.',
    'Aquarius': 'Detachment can make assertiveness feel cold.',
    'Pisces': 'Passive tendencies can prevent necessary self-assertion.'
  };
  return tensions[sign] || 'An action pattern that needs awareness.';
};

const getMarsGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Pure courage and the ability to begin what others hesitate on.',
    'Taurus': 'Unstoppable persistence once committed to a path.',
    'Gemini': 'Versatile energy that can adapt strategy mid-course.',
    'Cancer': 'Fierce protectiveness and emotional courage.',
    'Leo': 'Inspiring leadership and the courage of conviction.',
    'Virgo': 'Precise, effective action that improves everything it touches.',
    'Libra': 'The ability to fight fairly and for partnership.',
    'Scorpio': 'Transformative power and the courage to face darkness.',
    'Sagittarius': 'Enthusiastic energy that inspires collective action.',
    'Capricorn': 'Strategic, enduring effort that achieves long-term goals.',
    'Aquarius': 'The courage to be different and fight for ideals.',
    'Pisces': 'The strength to surrender and the power of non-resistance.'
  };
  return gifts[sign] || 'A distinctive action capacity.';
};

// ============================================
// INLINE REFLECT BUTTON COMPONENT
// ============================================

interface InlineReflectButtonProps {
  source: {
    lens: string;
    type: string;
    name: string;
    id: string;
  };
  prompt: string;
}

const InlineReflectButton: React.FC<InlineReflectButtonProps> = ({ source, prompt }) => {
  const { theme } = useTheme();
  const router = useRouter();

  const handlePress = () => {
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: `Reflecting on ${source.name}: ${prompt}`
      }
    });
  };

  return (
    <TouchableOpacity
      style={[styles.inlineReflectButton, { borderColor: theme.border }]}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <Text style={{ fontSize: 14, color: theme.textSecondary }}>Reflect →</Text>
    </TouchableOpacity>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

interface AstrologyLensViewProps {
  userId: string;
  onOpenChat: () => void;
}

export default function AstrologyLensView({ userId, onOpenChat }: AstrologyLensViewProps) {
  const { theme } = useTheme();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<'at_a_glance' | 'today' | 'deep_dive'>('at_a_glance');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryData, setSummaryData] = useState<AstrologySummaryData | null>(null);
  const [deepDiveData, setDeepDiveData] = useState<any>(null);
  const [snapshotData, setSnapshotData] = useState<any>(null);
  const [fullChartData, setFullChartData] = useState<FullChartData | null>(null);
  const [activeAltitude, setActiveAltitude] = useState<'today' | 'week' | 'month'>('today');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set(['sun']));
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    if (userId) {
      // Always fetch full chart data for deterministic astrology
      loadFullChartData();
      loadTabData(activeTab);
    }
  }, [userId, activeTab]);

  const loadFullChartData = async () => {
    if (!userId) return;
    try {
      const response = await api.get(`/astrology/chart/${userId}`);
      setFullChartData(response.data);
      console.log('[AstrologyLens] Full chart data loaded:', {
        success: response.data.success,
        chiron_present: !!response.data.natal?.planets?.Chiron,
        north_node_present: !!response.data.natal?.planets?.['North Node'],
        jupiter_present: !!response.data.natal?.planets?.Jupiter,
        saturn_present: !!response.data.natal?.planets?.Saturn,
        aspects_count: response.data.natal?.aspects?.length,
        transit_aspects_count: response.data.transits?.total_active_aspects,
        strongest_hits: response.data.transits?.strongest_hits?.length
      });
    } catch (err) {
      console.error('[AstrologyLens] Full chart data error:', err);
    }
  };

  const loadTabData = async (tab: string) => {
    if (!userId) return;
    setIsLoading(true);
    setError(null);

    try {
      if (tab === 'at_a_glance' || tab === 'summary') {
        const response = await api.get(`/astrology/summary/${userId}`);
        setSummaryData(response.data);
      } else if (tab === 'today') {
        try {
          const response = await api.get(`/astrology/snapshot/${userId}`);
          setSnapshotData(response.data);
        } catch {
          const response = await api.get(`/astrology/today/${userId}`);
          setSummaryData(response.data);
        }
      } else if (tab === 'deep_dive') {
        const response = await api.get(`/astrology/deep-dive/${userId}`);
        setDeepDiveData(response.data);
      }
    } catch (err: any) {
      console.error('Tab data error:', err);
      setError('Unable to load astrology data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCard = (cardId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cardId)) {
        newSet.delete(cardId);
      } else {
        newSet.add(cardId);
      }
      return newSet;
    });
  };

  // Action handlers
  const handleReflect = (card: AstrologyDeepDiveCard) => {
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: `I'd like to reflect on "${card.title}": ${card.reflection}`
      }
    });
  };

  const handleJournal = (card: AstrologyDeepDiveCard) => {
    const journalPrompt = `Reflecting on: ${card.title}\n\n"${card.reflection}"\n\nMy thoughts:\n`;
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'journal',
        prefill: journalPrompt
      }
    });
  };

  const handleAskMirror = (card: AstrologyDeepDiveCard) => {
    const mirrorContext = `I want to explore ${card.title.toLowerCase()} in my chart. ${card.whatThisIs}`;
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: mirrorContext
      }
    });
  };

  // Get placements from available data - prefer full chart data
  const getPlacements = (): CorePlacements => {
    // Use full chart data if available (most complete)
    if (fullChartData?.natal?.planets) {
      const planets = fullChartData.natal.planets;
      const nodes = fullChartData.natal.nodes;
      const angles = fullChartData.natal.angles;
      
      return {
        sun: planets.Sun?.sign || 'Unknown',
        sun_house: planets.Sun?.house,
        moon: planets.Moon?.sign || 'Unknown',
        moon_house: planets.Moon?.house,
        ascendant: angles?.asc?.sign || 'Unknown',
        mercury: planets.Mercury?.sign,
        mercury_house: planets.Mercury?.house,
        venus: planets.Venus?.sign,
        venus_house: planets.Venus?.house,
        mars: planets.Mars?.sign,
        mars_house: planets.Mars?.house,
        jupiter: planets.Jupiter?.sign,
        jupiter_house: planets.Jupiter?.house,
        saturn: planets.Saturn?.sign,
        saturn_house: planets.Saturn?.house,
        chiron: planets.Chiron?.sign,
        chiron_house: planets.Chiron?.house,
        north_node: planets['North Node']?.sign || nodes?.north?.sign,
        north_node_house: planets['North Node']?.house || nodes?.north?.house,
        south_node: planets['South Node']?.sign || nodes?.south?.sign,
        south_node_house: planets['South Node']?.house || nodes?.south?.house
      };
    }
    // Fallback to deep dive data
    if (deepDiveData?.core_placements) {
      return deepDiveData.core_placements;
    }
    // Fallback to summary data
    if (summaryData?.core_placements) {
      return summaryData.core_placements;
    }
    return {
      sun: 'Unknown',
      moon: 'Unknown',
      ascendant: 'Unknown'
    };
  };

  const placements = getPlacements();

  // ============================================
  // RENDER: DEBUG PANEL
  // ============================================
  const renderDebugPanel = () => {
    if (!showDebug || !fullChartData) return null;
    
    const { natal, transits, metadata } = fullChartData;
    
    return (
      <View style={[styles.debugPanel, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.debugHeader}>
          <Text style={[styles.debugTitle, { color: theme.text }]}>🔍 CHART DATA DEBUG</Text>
          <TouchableOpacity onPress={() => setShowDebug(false)}>
            <Text style={{ color: theme.textSecondary }}>✕</Text>
          </TouchableOpacity>
        </View>
        
        <Text style={[styles.debugSection, { color: theme.accent }]}>METADATA</Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          Sidereal: {metadata?.sidereal_mode} | SVP: {metadata?.svp_degrees}°
        </Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          Houses: {metadata?.house_system} | Node: {metadata?.node_mode}
        </Text>
        
        <Text style={[styles.debugSection, { color: theme.accent }]}>NATAL POINTS ({Object.keys(natal?.planets || {}).length})</Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          ☉ Sun: {natal?.planets?.Sun?.sign} {natal?.planets?.Sun?.degree?.toFixed(1)}° H{natal?.planets?.Sun?.house}
        </Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          ☽ Moon: {natal?.planets?.Moon?.sign} {natal?.planets?.Moon?.degree?.toFixed(1)}° H{natal?.planets?.Moon?.house}
        </Text>
        <Text style={[styles.debugText, { color: '#4CAF50' }]}>
          ♃ Jupiter: {natal?.planets?.Jupiter?.sign} H{natal?.planets?.Jupiter?.house}
        </Text>
        <Text style={[styles.debugText, { color: '#FFA726' }]}>
          ♄ Saturn: {natal?.planets?.Saturn?.sign} H{natal?.planets?.Saturn?.house}
        </Text>
        <Text style={[styles.debugText, { color: '#CE93D8' }]}>
          ⚷ Chiron: {natal?.planets?.Chiron?.sign} H{natal?.planets?.Chiron?.house} {natal?.planets?.Chiron ? '✓' : '✗'}
        </Text>
        <Text style={[styles.debugText, { color: '#81D4FA' }]}>
          ☊ N.Node: {natal?.nodes?.north?.sign} H{natal?.nodes?.north?.house}
        </Text>
        <Text style={[styles.debugText, { color: '#81D4FA' }]}>
          ☋ S.Node: {natal?.nodes?.south?.sign} H{natal?.nodes?.south?.house}
        </Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          MC: {natal?.angles?.mc?.sign} | IC: {natal?.angles?.ic?.sign}
        </Text>
        
        <Text style={[styles.debugSection, { color: theme.accent }]}>ASPECTS ({natal?.aspects?.length})</Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          {natal?.aspects?.slice(0, 3).map((a: any) => `${a.point_a} ${a.aspect_type} ${a.point_b}`).join(', ')}
        </Text>
        
        <Text style={[styles.debugSection, { color: theme.accent }]}>TRANSITS ({transits?.total_active_aspects})</Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          Top hits: {transits?.strongest_hits?.slice(0, 3).map((h: any) => `${h.transit_point}→${h.natal_point}`).join(', ')}
        </Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          Emphasis: {transits?.emphasis_tags?.slice(0, 4).join(', ')}
        </Text>
        <Text style={[styles.debugText, { color: theme.textSecondary }]}>
          Today activated: {transits?.windows?.today?.activated_natal_points?.join(', ')}
        </Text>
      </View>
    );
  };

  // ============================================
  // RENDER: TABS
  // ============================================
  const renderTabs = () => (
    <View style={[styles.tabContainer, { borderBottomColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'at_a_glance' && styles.activeTab]}
        onPress={() => setActiveTab('at_a_glance')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'at_a_glance' && { color: theme.text }]}>
          At a Glance
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
          Today
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );

  // ============================================
  // RENDER: AT A GLANCE (Premium Summary)
  // ============================================
  const renderAtAGlance = () => {
    const sun = placements.sun || 'Unknown';
    const moon = placements.moon || 'Unknown';
    const asc = placements.ascendant || 'Unknown';
    
    if (sun === 'Unknown' && moon === 'Unknown' && asc === 'Unknown') {
      return (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
            Your chart data is still loading or incomplete.
          </Text>
        </View>
      );
    }

    const heroDescriptor = getHeroDescriptor(sun, moon, asc);
    const synthesis = getSynthesis(sun, moon, asc);
    const themeChips = getThemeChips(sun, moon, asc);
    const tensions = getCoreTensions(sun, moon, asc);
    const gifts = getCoreGifts(sun, moon, asc);
    
    // New interpretive hierarchy data
    const chartSpine = getChartSpine(placements);
    const whatMattersMost = getWhatMattersMost(placements, fullChartData);
    const keyAspects = getKeyAspects(fullChartData, placements);

    return (
      <View style={styles.atAGlanceContainer}>
        {/* Hero Section: Big 3 + Descriptor */}
        <View style={[styles.heroCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.big3Row}>
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☉</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{sun}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☽</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{moon}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>↑</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{asc}</Text>
            </View>
          </View>
          <Text style={[styles.heroDescriptor, { color: theme.textSecondary }]}>{heroDescriptor}</Text>
        </View>

        {/* CHART SPINE - The backbone of the chart */}
        <View style={[styles.chartSpineCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.chartSpineTitle, { color: theme.accent }]}>CHART SPINE</Text>
          {chartSpine.map((statement, i) => (
            <Text key={i} style={[styles.chartSpineStatement, { color: theme.text }]}>
              {statement}
            </Text>
          ))}
        </View>

        {/* WHAT MATTERS MOST IN THIS CHART */}
        <View style={[styles.whatMattersCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.whatMattersTitle, { color: theme.accent }]}>WHAT MATTERS MOST IN THIS CHART</Text>
          {whatMattersMost.map((item, i) => (
            <View key={i} style={styles.whatMattersItem}>
              <Text style={[styles.whatMattersRank, { color: theme.accent }]}>{i + 1}</Text>
              <View style={styles.whatMattersContent}>
                <Text style={[styles.whatMattersLabel, { color: theme.text }]}>{item.label}</Text>
                <Text style={[styles.whatMattersWhy, { color: theme.textSecondary }]}>{item.why}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* KEY ASPECT DYNAMICS - ENHANCED */}
        {keyAspects.length > 0 && (
          <View style={[styles.keyAspectsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.keyAspectsTitle, { color: theme.accent }]}>KEY ASPECT DYNAMICS</Text>
            <Text style={[styles.keyAspectsSubtitle, { color: theme.textTertiary }]}>
              The 3-5 most chart-defining natal aspects
            </Text>
            {keyAspects.map((asp, i) => (
              <View key={i} style={[styles.keyAspectItem, { borderColor: theme.border }]}>
                <View style={styles.keyAspectHeader}>
                  <Text style={[styles.keyAspectName, { color: theme.text }]}>{asp.aspect}</Text>
                  <View style={[styles.keyAspectBadge, { 
                    backgroundColor: asp.quality === 'ease' ? '#E8F5E9' : asp.quality === 'friction' ? '#FFEBEE' : '#FFF3E0'
                  }]}>
                    <Text style={[styles.keyAspectBadgeText, { 
                      color: asp.quality === 'ease' ? '#2E7D32' : asp.quality === 'friction' ? '#C62828' : '#EF6C00'
                    }]}>{asp.quality}</Text>
                  </View>
                </View>
                <Text style={[styles.keyAspectMeaning, { color: theme.text }]}>{asp.meaning}</Text>
                <Text style={[styles.keyAspectWhyMatters, { color: theme.textSecondary }]}>
                  <Text style={{ fontWeight: '600', color: theme.accent }}>Why this matters: </Text>
                  {asp.whyItMatters}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Key Planets: Jupiter, Saturn, Nodes, Chiron */}
        <View style={[styles.keyPlanetsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.keyPlanetsTitle, { color: theme.textTertiary }]}>KEY DEVELOPMENTAL POINTS</Text>
          <View style={styles.keyPlanetsGrid}>
            <View style={styles.keyPlanetItem}>
              <Text style={[styles.keyPlanetSymbol, { color: '#4CAF50' }]}>♃</Text>
              <Text style={[styles.keyPlanetLabel, { color: theme.textTertiary }]}>Jupiter</Text>
              <Text style={[styles.keyPlanetValue, { color: theme.text }]}>{placements.jupiter || '—'}</Text>
              {placements.jupiter_house && <Text style={[styles.keyPlanetHouse, { color: theme.textSecondary }]}>H{placements.jupiter_house}</Text>}
            </View>
            <View style={styles.keyPlanetItem}>
              <Text style={[styles.keyPlanetSymbol, { color: '#FFA726' }]}>♄</Text>
              <Text style={[styles.keyPlanetLabel, { color: theme.textTertiary }]}>Saturn</Text>
              <Text style={[styles.keyPlanetValue, { color: theme.text }]}>{placements.saturn || '—'}</Text>
              {placements.saturn_house && <Text style={[styles.keyPlanetHouse, { color: theme.textSecondary }]}>H{placements.saturn_house}</Text>}
            </View>
            <View style={styles.keyPlanetItem}>
              <Text style={[styles.keyPlanetSymbol, { color: '#81D4FA' }]}>☊</Text>
              <Text style={[styles.keyPlanetLabel, { color: theme.textTertiary }]}>North Node</Text>
              <Text style={[styles.keyPlanetValue, { color: theme.text }]}>{placements.north_node || '—'}</Text>
              {placements.north_node_house && <Text style={[styles.keyPlanetHouse, { color: theme.textSecondary }]}>H{placements.north_node_house}</Text>}
            </View>
            <View style={styles.keyPlanetItem}>
              <Text style={[styles.keyPlanetSymbol, { color: '#CE93D8' }]}>⚷</Text>
              <Text style={[styles.keyPlanetLabel, { color: theme.textTertiary }]}>Chiron</Text>
              <Text style={[styles.keyPlanetValue, { color: theme.text }]}>{placements.chiron || '—'}</Text>
              {placements.chiron_house && <Text style={[styles.keyPlanetHouse, { color: theme.textSecondary }]}>H{placements.chiron_house}</Text>}
            </View>
          </View>
        </View>

        {/* Theme Chips */}
        <View style={styles.chipsContainer}>
          {themeChips.map((chip, i) => (
            <View key={i} style={[styles.chip, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '25' }]}>
              <Text style={[styles.chipText, { color: theme.accent }]}>{chip}</Text>
            </View>
          ))}
        </View>

        {/* Structure Section */}
        <View style={[styles.structureCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.structureTitle, { color: theme.textTertiary }]}>CHART STRUCTURE</Text>
          <View style={styles.structureGrid}>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Core Element</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_ELEMENTS[sun] || 'Mixed'}</Text>
            </View>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Sun Mode</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_MODALITIES[sun] || 'Mixed'}</Text>
            </View>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Emotional Element</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_ELEMENTS[moon] || 'Unknown'}</Text>
            </View>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Rising Mode</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_MODALITIES[asc] || 'Unknown'}</Text>
            </View>
          </View>
        </View>

        {/* Core Tensions & Gifts Side by Side on larger screens, stacked on mobile */}
        <View style={styles.tensionsGiftsRow}>
          {/* Core Tensions */}
          {tensions.length > 0 && (
            <View style={[styles.tensionsCard, { backgroundColor: '#FEF3F2', borderColor: '#FECACA' }]}>
              <Text style={[styles.tensionsTitle, { color: '#DC2626' }]}>TENSIONS</Text>
              {tensions.map((t, i) => (
                <View key={i} style={styles.tensionItem}>
                  <Text style={[styles.tensionText, { color: '#7F1D1D' }]}>{t}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Core Gifts */}
          {gifts.length > 0 && (
            <View style={[styles.giftsCard, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}>
              <Text style={[styles.giftsTitle, { color: '#16A34A' }]}>GIFTS</Text>
              {gifts.map((g, i) => (
                <View key={i} style={styles.giftItem}>
                  <Text style={[styles.giftText, { color: '#14532D' }]}>{g}</Text>
                </View>
              ))}
            </View>
          )}
        </View>

        {/* Reflection Prompt */}
        <View style={[styles.reflectionCard, { backgroundColor: theme.accent + '06', borderColor: theme.accent + '15' }]}>
          <Text style={[styles.reflectionLabel, { color: theme.accent }]}>A QUESTION</Text>
          <Text style={[styles.reflectionText, { color: theme.text }]}>
            When you feel most like yourself, which of these qualities are present—and which are conspicuously absent?
          </Text>
        </View>

        {/* Ask Mirror Button */}
        <TouchableOpacity
          style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
          onPress={onOpenChat}
        >
          <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
          <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about your chart</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // ============================================
  // RENDER: TODAY SNAPSHOT - INSIGHT FIRST, SIGNALS SECOND
  // ============================================
  const [signalsExpanded, setSignalsExpanded] = useState(false);
  
  const renderTodaySnapshot = () => {
    // Use deterministic transit data from full chart
    const transits = fullChartData?.transits;
    
    if (!transits || transits.error) {
      // Fallback to old snapshot if transits not available
      if (snapshotData) {
        const currentAltitude = snapshotData[activeAltitude];
        if (currentAltitude) {
          return (
            <View style={styles.todayContainer}>
              <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <Text style={[styles.narrativeText, { color: theme.text }]}>
                  {currentAltitude.body}
                </Text>
              </View>
            </View>
          );
        }
      }
      return (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
            Transit data is loading...
          </Text>
        </View>
      );
    }

    const windows = transits.windows;
    const currentWindow = activeAltitude === 'today' ? windows.today :
                          activeAltitude === 'week' ? windows.this_week :
                          windows.this_month;

    // Get the daily energy synthesis
    const energySynthesis = getDailyEnergySynthesis(
      currentWindow?.strongest_hits || [], 
      activeAltitude === 'week' ? 'week' : activeAltitude === 'month' ? 'month' : 'today'
    );

    // Get refined content (max 3 items each)
    const feelings = getWhatThisMayFeelLike(currentWindow?.strongest_hits || []).slice(0, 3);
    const mistakes = getMistakeToWatch(currentWindow?.strongest_hits || []).slice(0, 3);
    const question = getReflectionQuestion(
      currentWindow?.strongest_hits || [],
      activeAltitude === 'week' ? 'week' : activeAltitude === 'month' ? 'month' : 'today'
    );

    // Get symbol for aspect type (for signals section)
    const getAspectSymbol = (type: string) => {
      const symbols: { [key: string]: string } = {
        'conjunction': '☌', 'opposition': '☍', 'square': '□',
        'trine': '△', 'sextile': '⚹', 'quincunx': '⚻'
      };
      return symbols[type] || '•';
    };

    return (
      <View style={styles.todayContainer}>
        {/* Altitude Selector */}
        <View style={[styles.altitudeSelector, { backgroundColor: theme.surfaceLight }]}>
          {['today', 'week', 'month'].map((alt) => (
            <TouchableOpacity
              key={alt}
              style={[
                styles.altitudeTab,
                activeAltitude === alt && [styles.altitudeTabActive, { backgroundColor: theme.surface }]
              ]}
              onPress={() => setActiveAltitude(alt as 'today' | 'week' | 'month')}
            >
              <Text style={[
                styles.altitudeTabText,
                { color: activeAltitude === alt ? theme.text : theme.textTertiary }
              ]}>
                {alt === 'today' ? 'Today' : alt === 'week' ? 'This Week' : 'This Month'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* ============================================ */}
        {/* LAYER 1: PRIMARY DAILY EXPERIENCE */}
        {/* ============================================ */}

        {/* 1. DAILY ENERGY - Premium Primary Card */}
        <View style={[styles.dailyEnergyCard, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
          <Text style={[styles.dailyEnergyLabel, { color: theme.accent }]}>
            {activeAltitude === 'today' ? "TODAY'S ENERGY" : activeAltitude === 'week' ? "THIS WEEK'S ENERGY" : "THIS MONTH'S ENERGY"}
          </Text>
          <Text style={[styles.dailyEnergyHeadline, { color: theme.text }]}>
            {energySynthesis.headline}
          </Text>
          <Text style={[styles.dailyEnergyBody, { color: theme.text }]}>
            {energySynthesis.body}
          </Text>
          {energySynthesis.supporting && (
            <Text style={[styles.dailyEnergySupporting, { color: theme.textTertiary }]}>
              {energySynthesis.supporting}
            </Text>
          )}
        </View>

        {/* 2. WHAT THIS MAY FEEL LIKE - 3 bullets max */}
        {feelings.length > 0 && (
          <View style={[styles.todayInsightBlock, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.todayInsightTitle, { color: theme.textSecondary }]}>WHAT THIS MAY FEEL LIKE</Text>
            {feelings.map((feeling: string, i: number) => (
              <View key={i} style={styles.todayInsightItem}>
                <Text style={[styles.todayInsightBullet, { color: theme.textTertiary }]}>•</Text>
                <Text style={[styles.todayInsightText, { color: theme.text }]}>{feeling}</Text>
              </View>
            ))}
          </View>
        )}

        {/* 3. THE MISTAKE TO WATCH - 3 bullets max */}
        {mistakes.length > 0 && (
          <View style={[styles.todayInsightBlock, { backgroundColor: '#FF634705', borderColor: '#FF634715' }]}>
            <Text style={[styles.todayInsightTitle, { color: '#FF6347' }]}>THE MISTAKE TO WATCH</Text>
            {mistakes.map((mistake: string, i: number) => (
              <View key={i} style={styles.todayInsightItem}>
                <Text style={[styles.todayInsightBullet, { color: '#FF6347' }]}>⚠</Text>
                <Text style={[styles.todayInsightText, { color: theme.text }]}>{mistake}</Text>
              </View>
            ))}
          </View>
        )}

        {/* 4. TODAY'S QUESTION - Large, prominent */}
        <View style={[styles.todayQuestionCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.todayQuestionLabel, { color: theme.accent }]}>
            {activeAltitude === 'today' ? "TODAY'S QUESTION" : activeAltitude === 'week' ? "THIS WEEK'S QUESTION" : "THIS MONTH'S QUESTION"}
          </Text>
          <Text style={[styles.todayQuestionText, { color: theme.text }]}>
            {question}
          </Text>
        </View>

        {/* 5. REFLECT CTA */}
        <InlineReflectButton
          source={{
            lens: 'astrology',
            type: `transit_${activeAltitude}`,
            name: `${activeAltitude === 'today' ? 'Today' : activeAltitude === 'week' ? 'This Week' : 'This Month'}`,
            id: `astrology_transit_${activeAltitude}`,
          }}
          prompt={`${energySynthesis.headline}: ${energySynthesis.body.substring(0, 100)}...`}
        />

        {/* ============================================ */}
        {/* LAYER 2: SIGNALS (Collapsible, Secondary) */}
        {/* ============================================ */}
        <TouchableOpacity
          style={[styles.signalsToggle, { borderColor: theme.border }]}
          onPress={() => setSignalsExpanded(!signalsExpanded)}
          activeOpacity={0.7}
        >
          <Text style={[styles.signalsToggleText, { color: theme.textTertiary }]}>
            {signalsExpanded ? 'Hide signals' : 'See signals'}
          </Text>
          <Text style={[styles.signalsToggleIcon, { color: theme.textTertiary }]}>
            {signalsExpanded ? '▲' : '▼'}
          </Text>
        </TouchableOpacity>

        {signalsExpanded && (
          <View style={[styles.signalsContainer, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
            {/* Active Transits - Compact */}
            <View style={styles.signalsSection}>
              <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>ACTIVE TRANSITS</Text>
              <View style={styles.signalsCompactList}>
                {currentWindow?.strongest_hits?.slice(0, 4).map((hit: TransitHit, index: number) => (
                  <View key={index} style={styles.signalsTransitRow}>
                    <Text style={[styles.signalsTransitText, { color: theme.textSecondary }]}>
                      {getAspectSymbol(hit.aspect_type)} {hit.transit_point} {hit.aspect_type} {hit.natal_point}
                    </Text>
                    <Text style={[styles.signalsTransitOrb, { color: theme.textTertiary }]}>
                      {hit.orb.toFixed(1)}°
                    </Text>
                  </View>
                ))}
              </View>
            </View>

            {/* Natal Points Activated - Chips */}
            {currentWindow?.activated_natal_points && currentWindow.activated_natal_points.length > 0 && (
              <View style={styles.signalsSection}>
                <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>POINTS ACTIVATED</Text>
                <View style={styles.signalsChipsRow}>
                  {currentWindow.activated_natal_points.slice(0, 6).map((point: string, i: number) => (
                    <View key={i} style={[styles.signalsChip, { backgroundColor: theme.accent + '10' }]}>
                      <Text style={[styles.signalsChipText, { color: theme.accent }]}>{point}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Themes - Chips */}
            {currentWindow?.emphasis_tags && currentWindow.emphasis_tags.length > 0 && (
              <View style={styles.signalsSection}>
                <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>THEMES</Text>
                <View style={styles.signalsChipsRow}>
                  {currentWindow.emphasis_tags.slice(0, 4).map((tag: string, i: number) => (
                    <View key={i} style={[styles.signalsChip, { backgroundColor: theme.border }]}>
                      <Text style={[styles.signalsChipText, { color: theme.textSecondary }]}>{tag}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Life Areas - Short bullets */}
            {currentWindow?.activated_natal_points && currentWindow.activated_natal_points.length > 0 && (
              <View style={styles.signalsSection}>
                <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>LIFE AREAS TOUCHED</Text>
                <View style={styles.signalsLifeAreas}>
                  {currentWindow.activated_natal_points.slice(0, 4).map((point: string, i: number) => {
                    const shortAreaMap: { [key: string]: string } = {
                      'Sun': 'Purpose, identity',
                      'Moon': 'Emotions, comfort',
                      'Mercury': 'Thinking, communication',
                      'Venus': 'Relationships, values',
                      'Mars': 'Action, drive',
                      'Jupiter': 'Growth, meaning',
                      'Saturn': 'Structure, maturity',
                      'Uranus': 'Change, freedom',
                      'Neptune': 'Intuition, boundaries',
                      'Pluto': 'Power, transformation',
                      'Chiron': 'Wounds, healing'
                    };
                    return (
                      <Text key={i} style={[styles.signalsLifeAreaText, { color: theme.textSecondary }]}>
                        • {point}: {shortAreaMap[point] || point}
                      </Text>
                    );
                  })}
                </View>
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  // ============================================
  // RENDER: DEEP DIVE CARDS WITH SECTION HEADERS
  // ============================================
  
  // Define section groupings for cards
  const CARD_SECTIONS = {
    foundation: { 
      title: 'FOUNDATION',
      subtitle: 'Your core identity and emotional substrate',
      cards: ['sun', 'moon', 'ascendant'],
      color: '#7C3AED'
    },
    personal_style: { 
      title: 'PERSONAL STYLE',
      subtitle: 'How you think, connect, and act',
      cards: ['mercury', 'venus', 'mars'],
      color: '#EC4899'
    },
    developmental_axis: { 
      title: 'DEVELOPMENTAL AXIS',
      subtitle: 'Growth, pressure, and healing',
      cards: ['jupiter', 'saturn', 'nodes', 'chiron'],
      color: '#10B981'
    },
    structure: { 
      title: 'STRUCTURE & INTEGRATION',
      subtitle: 'Pattern, emphasis, and potential',
      cards: ['houses', 'tensions', 'opens'],
      color: '#F59E0B'
    }
  };
  
  const renderDeepDive = () => {
    const cards = generateDeepDiveCards(placements);
    
    // Group cards by section
    const getCardSection = (cardId: string): string => {
      for (const [sectionKey, section] of Object.entries(CARD_SECTIONS)) {
        if (section.cards.includes(cardId)) return sectionKey;
      }
      return 'structure';
    };
    
    // Render a section header
    const renderSectionHeader = (sectionKey: string) => {
      const section = CARD_SECTIONS[sectionKey as keyof typeof CARD_SECTIONS];
      return (
        <View style={[styles.deepDiveSectionHeaderWrapper, { borderColor: section.color + '30' }]}>
          <View style={[styles.deepDiveSectionHeaderLine, { backgroundColor: section.color + '20' }]} />
          <View style={styles.deepDiveSectionHeaderContent}>
            <Text style={[styles.deepDiveSectionHeaderTitle, { color: section.color }]}>{section.title}</Text>
            <Text style={[styles.deepDiveSectionHeaderSubtitle, { color: theme.textTertiary }]}>{section.subtitle}</Text>
          </View>
        </View>
      );
    };
    
    // Track which sections we've rendered
    let lastSection = '';

    return (
      <View style={styles.deepDiveContainer}>
        {/* Header */}
        <View style={[styles.deepDiveHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.big3Row}>
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☉</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{placements.sun}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☽</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{placements.moon}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>↑</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{placements.ascendant}</Text>
            </View>
          </View>
          <Text style={[styles.deepDiveNote, { color: theme.textTertiary }]}>
            13 reflection cards organized by chart layer.
          </Text>
        </View>

        {/* Cards with Section Headers */}
        {cards.map((card, index) => {
          const isExpanded = expandedCards.has(card.id);
          const currentSection = getCardSection(card.id);
          const showSectionHeader = currentSection !== lastSection;
          lastSection = currentSection;
          
          // Badge colors by card type
          const getBadgeColor = () => {
            const section = CARD_SECTIONS[currentSection as keyof typeof CARD_SECTIONS];
            if (section) return section.color;
            switch (card.id) {
              case 'sun': return theme.accent;
              case 'moon': return '#B39DDB';
              case 'ascendant': return '#64B5F6';
              case 'mercury': return '#FFD54F';
              case 'venus': return '#F48FB1';
              case 'mars': return '#E57373';
              case 'jupiter': return '#4CAF50';
              case 'saturn': return '#FFA726';
              case 'nodes': return '#81D4FA';
              case 'chiron': return '#CE93D8';
              case 'houses': return '#81C784';
              case 'tensions': return '#FFB74D';
              case 'opens': return '#4DD0E1';
              default: return theme.accent;
            }
          };

          return (
            <React.Fragment key={card.id}>
              {/* Section Header (if entering new section) */}
              {showSectionHeader && renderSectionHeader(currentSection)}
              
              <View 
                style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              >
              {/* Card Header */}
              <TouchableOpacity
                style={styles.deepDiveCardHeader}
                onPress={() => toggleCard(card.id)}
                activeOpacity={0.7}
              >
                <View style={styles.deepDiveCardHeaderContent}>
                  <View style={[styles.deepDiveCardNumber, { backgroundColor: getBadgeColor() + '15' }]}>
                    <Text style={[styles.deepDiveCardNumberText, { color: getBadgeColor() }]}>{index + 1}</Text>
                  </View>
                  <View style={styles.deepDiveCardTitleContainer}>
                    <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{card.title}</Text>
                    <Text style={[styles.deepDiveCardSubtitle, { color: theme.textSecondary }]}>{card.subtitle}</Text>
                    {!isExpanded && (
                      <Text style={[styles.deepDiveCardPreview, { color: theme.textTertiary }]}>{card.preview}</Text>
                    )}
                  </View>
                </View>
                <Text style={[styles.deepDiveChevron, { color: theme.textTertiary }]}>
                  {isExpanded ? '▼' : '▶'}
                </Text>
              </TouchableOpacity>

              {/* Card Content */}
              {isExpanded && (
                <View style={styles.deepDiveCardContent}>
                  {/* What this is */}
                  <View style={styles.deepDiveSection}>
                    <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHAT THIS IS</Text>
                    <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.whatThisIs}</Text>
                  </View>

                  {/* What you might notice */}
                  <View style={styles.deepDiveSection}>
                    <Text style={[styles.deepDiveSectionLabel, { color: theme.accent }]}>WHAT YOU MIGHT NOTICE</Text>
                    <View style={styles.bulletList}>
                      {card.whatYouMightNotice.map((item, i) => (
                        <View key={i} style={styles.bulletItem}>
                          <Text style={[styles.bullet, { color: theme.accent }]}>•</Text>
                          <Text style={[styles.bulletText, { color: theme.text }]}>{item}</Text>
                        </View>
                      ))}
                    </View>
                  </View>

                  {/* Tension */}
                  <View style={[styles.deepDiveSection, styles.tensionSection]}>
                    <Text style={[styles.deepDiveSectionLabel, { color: '#E57373' }]}>{card.tensionLabel.toUpperCase()}</Text>
                    <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.tension}</Text>
                  </View>

                  {/* Gift */}
                  <View style={[styles.deepDiveSection, styles.giftSection]}>
                    <Text style={[styles.deepDiveSectionLabel, { color: '#81C784' }]}>{card.giftLabel.toUpperCase()}</Text>
                    <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.gift}</Text>
                  </View>

                  {/* Reflection */}
                  <View style={[styles.reflectionBox, { backgroundColor: theme.accent + '06', borderColor: theme.border }]}>
                    <Text style={[styles.reflectionBoxLabel, { color: theme.accent }]}>A QUESTION TO SIT WITH</Text>
                    <Text style={[styles.reflectionBoxText, { color: theme.textSecondary }]}>{card.reflection}</Text>
                  </View>

                  {/* Action Buttons */}
                  <View style={styles.actionButtons}>
                    <TouchableOpacity
                      style={[styles.actionButton, { borderColor: theme.border }]}
                      onPress={() => handleReflect(card)}
                      activeOpacity={0.6}
                    >
                      <Text style={styles.actionIcon}>💭</Text>
                      <Text style={[styles.actionText, { color: theme.textSecondary }]}>Reflect</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.actionButton, { borderColor: theme.border }]}
                      onPress={() => handleJournal(card)}
                      activeOpacity={0.6}
                    >
                      <Text style={styles.actionIcon}>📝</Text>
                      <Text style={[styles.actionText, { color: theme.textSecondary }]}>Journal</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.actionButton, { borderColor: theme.border }]}
                      onPress={() => handleAskMirror(card)}
                      activeOpacity={0.6}
                    >
                      <Text style={styles.actionIcon}>✨</Text>
                      <Text style={[styles.actionText, { color: theme.textSecondary }]}>Ask Mirror</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
            </React.Fragment>
          );
        })}

        {/* Footer */}
        <Text style={[styles.footer, { color: theme.textTertiary }]}>
          A lens for understanding patterns, not a definition of identity.
        </Text>
      </View>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================
  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              {activeTab === 'deep_dive'
                ? 'Generating your personalized reading...'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.surface }]}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {/* Debug Toggle */}
            {fullChartData && (
              <TouchableOpacity
                style={[styles.debugToggle, { backgroundColor: showDebug ? theme.accent : theme.surface, borderColor: theme.border }]}
                onPress={() => setShowDebug(!showDebug)}
              >
                <Text style={{ fontSize: 10, color: showDebug ? '#fff' : theme.textSecondary }}>
                  🔍 {showDebug ? 'Hide' : 'Show'} Data
                </Text>
              </TouchableOpacity>
            )}
            
            {/* Debug Panel */}
            {renderDebugPanel()}
            
            {activeTab === 'at_a_glance' && renderAtAGlance()}
            {activeTab === 'today' && renderTodaySnapshot()}
            {activeTab === 'deep_dive' && renderDeepDive()}
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  activeTab: {},
  tabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    textAlign: 'center',
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginTop: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 14,
    fontStyle: 'italic',
  },

  // At a Glance
  atAGlanceContainer: {
    gap: 16,
  },
  heroCard: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    alignItems: 'center',
  },
  heroDescriptor: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 16,
    textAlign: 'center',
    lineHeight: 20,
  },
  big3Card: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    alignItems: 'center',
  },
  big3Label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  big3Row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  big3Item: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  big3Symbol: {
    fontSize: 18,
    marginBottom: 6,
  },
  big3Sign: {
    fontSize: 16,
    fontWeight: '600',
  },
  big3Divider: {
    width: 1,
    height: 36,
  },
  synthesisCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
  },
  synthesisText: {
    fontSize: 15,
    lineHeight: 24,
    letterSpacing: 0.2,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    paddingVertical: 4,
  },
  chip: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipText: {
    fontSize: 12,
    fontWeight: '500',
  },
  structureCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  structureTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  structureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  structureItem: {
    width: '50%',
    marginBottom: 12,
  },
  structureLabel: {
    fontSize: 10,
    marginBottom: 2,
  },
  structureValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  tensionsGiftsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  tensionsCard: {
    flex: 1,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  tensionsTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  tensionItem: {
    marginBottom: 8,
  },
  tensionBullet: {
    fontSize: 14,
    marginRight: 8,
  },
  tensionText: {
    fontSize: 13,
    lineHeight: 18,
  },
  giftsCard: {
    flex: 1,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  giftsTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  giftItem: {
    marginBottom: 8,
  },
  giftBullet: {
    fontSize: 14,
    marginRight: 8,
  },
  giftText: {
    fontSize: 13,
    lineHeight: 18,
  },
  reflectionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  reflectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 10,
    gap: 8,
    marginTop: 4,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },

  // Today
  todayContainer: {
    gap: 12,
  },
  altitudeSelector: {
    flexDirection: 'row',
    padding: 4,
    borderRadius: 10,
  },
  altitudeTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  altitudeTabActive: {},
  altitudeTabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  narrativeCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  narrativeText: {
    fontSize: 15,
    lineHeight: 22,
  },
  causeText: {
    fontSize: 13,
    marginTop: 12,
    fontStyle: 'italic',
  },
  inlineReflectButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    alignSelf: 'flex-start',
  },

  // Deep Dive
  deepDiveContainer: {
    gap: 10,
  },
  deepDiveHeader: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    alignItems: 'center',
    marginBottom: 4,
  },
  deepDiveNote: {
    fontSize: 12,
    marginTop: 12,
    textAlign: 'center',
  },
  deepDiveCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  deepDiveCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  deepDiveCardHeaderContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
  },
  deepDiveCardNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  deepDiveCardNumberText: {
    fontSize: 12,
    fontWeight: '600',
  },
  deepDiveCardTitleContainer: {
    flex: 1,
  },
  deepDiveCardTitle: {
    fontSize: 15,
    fontWeight: '600',
  },
  deepDiveCardSubtitle: {
    fontSize: 12,
    marginTop: 2,
    opacity: 0.75,
  },
  deepDiveCardPreview: {
    fontSize: 12,
    marginTop: 6,
    fontStyle: 'italic',
  },
  deepDiveChevron: {
    fontSize: 10,
    marginLeft: 8,
  },
  deepDiveCardContent: {
    paddingHorizontal: 14,
    paddingBottom: 14,
  },
  deepDiveSection: {
    marginBottom: 14,
  },
  tensionSection: {
    paddingLeft: 10,
    borderLeftWidth: 2,
    borderLeftColor: '#E57373',
  },
  giftSection: {
    paddingLeft: 10,
    borderLeftWidth: 2,
    borderLeftColor: '#81C784',
  },
  deepDiveSectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  deepDiveSectionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  bulletList: {
    gap: 5,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bullet: {
    fontSize: 13,
    marginRight: 8,
    lineHeight: 19,
  },
  bulletText: {
    fontSize: 14,
    lineHeight: 19,
    flex: 1,
  },
  reflectionBox: {
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
    marginBottom: 12,
  },
  reflectionBoxLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  reflectionBoxText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 6,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 4,
  },
  actionIcon: {
    fontSize: 11,
  },
  actionText: {
    fontSize: 11,
    fontWeight: '500',
  },
  footer: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  // Debug Panel Styles
  debugToggle: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: StyleSheet.hairlineWidth,
    zIndex: 10,
  },
  debugPanel: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 16,
  },
  debugHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: '700',
  },
  debugSection: {
    fontSize: 10,
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 4,
  },
  debugText: {
    fontSize: 10,
    lineHeight: 14,
  },
  // Transit/Today Tab Styles
  transitHitsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  transitHitsTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  transitHitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  transitHitSymbol: {
    fontSize: 14,
    width: 24,
    textAlign: 'center',
  },
  transitHitText: {
    flex: 1,
    fontSize: 14,
  },
  transitHitOrb: {
    fontSize: 11,
  },
  activatedPointsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  activatedTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  activatedChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  activatedChip: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
  },
  activatedChipText: {
    fontSize: 12,
    fontWeight: '500',
  },
  emphasisCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  emphasisTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  emphasisChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  emphasisChip: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  emphasisChipText: {
    fontSize: 12,
  },
  transitSummaryCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  transitSummaryText: {
    fontSize: 15,
    lineHeight: 22,
  },
  // Key Planets Grid
  keyPlanetsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  keyPlanetsTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  keyPlanetsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  keyPlanetItem: {
    alignItems: 'center',
    flex: 1,
  },
  keyPlanetSymbol: {
    fontSize: 18,
    marginBottom: 4,
  },
  keyPlanetLabel: {
    fontSize: 9,
    marginBottom: 2,
  },
  keyPlanetValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  keyPlanetHouse: {
    fontSize: 10,
    marginTop: 2,
  },
  // Chart Spine Styles
  chartSpineCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  chartSpineTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  chartSpineStatement: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 6,
  },
  // What Matters Most Styles
  whatMattersCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  whatMattersTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  whatMattersItem: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  whatMattersRank: {
    fontSize: 14,
    fontWeight: '700',
    width: 20,
    marginRight: 8,
  },
  whatMattersContent: {
    flex: 1,
  },
  whatMattersLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 2,
  },
  whatMattersWhy: {
    fontSize: 12,
    lineHeight: 18,
  },
  // Key Aspects Styles
  keyAspectsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  keyAspectsTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  keyAspectHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  keyAspectName: {
    fontSize: 13,
    fontWeight: '600',
  },
  keyAspectBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  keyAspectBadgeText: {
    fontSize: 9,
    fontWeight: '600',
  },
  keyAspectMeaning: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 4,
  },
  keyAspectsSubtitle: {
    fontSize: 11,
    marginBottom: 12,
  },
  keyAspectWhyMatters: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 4,
    fontStyle: 'italic',
  },
  keyAspectItem: {
    marginBottom: 14,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  // Deep Dive Section Header
  deepDiveSectionHeader: {
    paddingVertical: 8,
    marginBottom: 4,
    marginTop: 12,
  },
  deepDiveSectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
  },
  // Deep Dive Section Header Wrapper styles
  deepDiveSectionHeaderWrapper: {
    marginTop: 20,
    marginBottom: 8,
    paddingTop: 16,
    borderTopWidth: 1,
  },
  deepDiveSectionHeaderLine: {
    height: 3,
    width: 40,
    borderRadius: 2,
    marginBottom: 8,
  },
  deepDiveSectionHeaderContent: {
    paddingHorizontal: 4,
  },
  deepDiveSectionHeaderTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  deepDiveSectionHeaderSubtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  // Enhanced Today Tab styles
  todayLifeAreas: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  lifeAreasTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  lifeAreaItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
    paddingLeft: 4,
  },
  lifeAreaBullet: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 2,
  },
  lifeAreaText: {
    fontSize: 13,
    lineHeight: 19,
    flex: 1,
  },
  activatedPointDetail: {
    fontSize: 11,
    marginTop: 2,
  },
  // ============================================
  // NEW SIMPLIFIED TODAY TAB STYLES
  // ============================================
  // Daily Energy Card - Premium Primary Card
  dailyEnergyCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 12,
  },
  dailyEnergyLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  dailyEnergyHeadline: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 26,
    marginBottom: 12,
  },
  dailyEnergyBody: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 12,
  },
  dailyEnergySupporting: {
    fontSize: 11,
    lineHeight: 16,
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  // Today Insight Blocks
  todayInsightBlock: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 10,
  },
  todayInsightTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  todayInsightItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  todayInsightBullet: {
    fontSize: 12,
    marginRight: 8,
    marginTop: 2,
  },
  todayInsightText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  // Today Question Card
  todayQuestionCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 18,
    marginBottom: 12,
  },
  todayQuestionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 10,
  },
  todayQuestionText: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 24,
  },
  // Signals Toggle
  signalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginTop: 8,
    marginBottom: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  signalsToggleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  signalsToggleIcon: {
    fontSize: 10,
    marginLeft: 6,
  },
  // Signals Container
  signalsContainer: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 16,
  },
  signalsSection: {
    marginBottom: 12,
  },
  signalsSectionTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  signalsCompactList: {
    gap: 2,
  },
  signalsTransitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  signalsTransitText: {
    fontSize: 12,
  },
  signalsTransitOrb: {
    fontSize: 11,
  },
  signalsChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  signalsChip: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  signalsChipText: {
    fontSize: 11,
  },
  signalsLifeAreas: {
    gap: 2,
  },
  signalsLifeAreaText: {
    fontSize: 11,
    lineHeight: 16,
  },
});
