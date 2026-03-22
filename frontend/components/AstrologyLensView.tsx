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

// Get key natal aspects for display
const getKeyAspects = (fullChartData: FullChartData | null): Array<{ aspect: string; meaning: string; quality: 'ease' | 'friction' | 'complexity' }> => {
  if (!fullChartData?.natal?.aspects) return [];
  
  const aspects = fullChartData.natal.aspects;
  const keyAspects: Array<{ aspect: string; meaning: string; quality: 'ease' | 'friction' | 'complexity'; weight: number }> = [];
  
  // Aspect meanings
  const getAspectMeaning = (pointA: string, pointB: string, type: string): { meaning: string; quality: 'ease' | 'friction' | 'complexity' } => {
    // Sun aspects
    if ((pointA === 'Sun' && pointB === 'Saturn') || (pointB === 'Sun' && pointA === 'Saturn')) {
      return { meaning: 'identity and pressure are tightly linked', quality: type === 'conjunction' || type === 'square' || type === 'opposition' ? 'friction' : 'complexity' };
    }
    if ((pointA === 'Sun' && pointB === 'Moon') || (pointB === 'Sun' && pointA === 'Moon')) {
      return { meaning: 'core self and emotional nature in dialogue', quality: type === 'trine' || type === 'sextile' ? 'ease' : 'friction' };
    }
    if ((pointA === 'Sun' && pointB === 'Jupiter') || (pointB === 'Sun' && pointA === 'Jupiter')) {
      return { meaning: 'identity expands through faith and meaning', quality: 'ease' };
    }
    
    // Moon aspects
    if ((pointA === 'Moon' && pointB === 'Mars') || (pointB === 'Moon' && pointA === 'Mars')) {
      return { meaning: 'feeling and action can collide quickly', quality: type === 'square' || type === 'opposition' ? 'friction' : 'complexity' };
    }
    if ((pointA === 'Moon' && pointB === 'Saturn') || (pointB === 'Moon' && pointA === 'Saturn')) {
      return { meaning: 'emotional caution and containment', quality: 'friction' };
    }
    if ((pointA === 'Moon' && pointB === 'Neptune') || (pointB === 'Moon' && pointA === 'Neptune')) {
      return { meaning: 'heightened emotional sensitivity and imagination', quality: 'complexity' };
    }
    
    // Saturn aspects
    if ((pointA === 'Saturn' && pointB === 'Chiron') || (pointB === 'Saturn' && pointA === 'Chiron')) {
      return { meaning: 'wound and discipline intertwined', quality: 'complexity' };
    }
    
    // Neptune/Chiron
    if ((pointA === 'Neptune' && pointB === 'Chiron') || (pointB === 'Neptune' && pointA === 'Chiron')) {
      return { meaning: 'sensitivity and healing themes amplified', quality: 'complexity' };
    }
    
    // Pluto aspects
    if (pointA === 'Pluto' || pointB === 'Pluto') {
      const other = pointA === 'Pluto' ? pointB : pointA;
      return { meaning: `${other} undergoes deep transformation`, quality: 'friction' };
    }
    
    // Default
    return { meaning: `${pointA} and ${pointB} interact`, quality: type === 'trine' || type === 'sextile' ? 'ease' : type === 'square' || type === 'opposition' ? 'friction' : 'complexity' };
  };
  
  // Weight aspects by importance
  const importantPlanets = ['Sun', 'Moon', 'Saturn', 'Chiron', 'North Node', 'Jupiter', 'Pluto'];
  
  for (const asp of aspects) {
    const isImportant = importantPlanets.includes(asp.point_a) || importantPlanets.includes(asp.point_b);
    const isHardAspect = ['conjunction', 'opposition', 'square'].includes(asp.aspect_type);
    
    if (isImportant || isHardAspect) {
      const { meaning, quality } = getAspectMeaning(asp.point_a, asp.point_b, asp.aspect_type);
      const symbol = asp.aspect_type === 'conjunction' ? '☌' : asp.aspect_type === 'opposition' ? '☍' : asp.aspect_type === 'square' ? '□' : asp.aspect_type === 'trine' ? '△' : asp.aspect_type === 'sextile' ? '⚹' : '•';
      
      let weight = isImportant ? 5 : 3;
      if (isHardAspect) weight += 2;
      if (asp.orb < 3) weight += 2; // Tight orb
      
      keyAspects.push({
        aspect: `${asp.point_a} ${symbol} ${asp.point_b}`,
        meaning,
        quality,
        weight
      });
    }
  }
  
  // Sort and return top 5
  return keyAspects.sort((a, b) => b.weight - a.weight).slice(0, 5).map(({ aspect, meaning, quality }) => ({ aspect, meaning, quality }));
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
    // === NEW: Jupiter ===
    {
      id: 'jupiter',
      title: 'Jupiter — Growth & Faith',
      subtitle: `${placements.jupiter || 'Unknown'}${placements.jupiter_house ? ` in the ${getHouseOrdinal(placements.jupiter_house)} house` : ''}`,
      preview: `In your chart, growth and opportunity flow through ${getHouseTheme(placements.jupiter_house || 1)}.`,
      whatThisIs: `In your chart, Jupiter in ${placements.jupiter || 'Unknown'}${placements.jupiter_house ? ` placed in House ${placements.jupiter_house}` : ''} reveals where you naturally expand, what you believe in, and where opportunity tends to find you. This is the part of your chart that says "yes" to life and reaches for more.`,
      whatYouMightNotice: [
        `Natural optimism and expansion around ${getHouseTheme(placements.jupiter_house || 1)} themes`,
        `A tendency to over-promise or over-extend in this area`,
        `Where you go when seeking meaning and adventure`,
        `Generosity that flows most easily here`
      ],
      tensionLabel: 'Where excess happens',
      tension: `Jupiter can over-expand. In House ${placements.jupiter_house || '?'}, you may promise too much, believe too readily, or assume growth is always possible. Sometimes the gift becomes the problem.`,
      giftLabel: 'Source of faith',
      gift: `This is where belief comes naturally. Even when life contracts elsewhere, this part of your chart remembers that expansion is possible.`,
      reflection: `Where do you most naturally say yes? Where might you need more discernment?`
    },
    // === NEW: Saturn ===
    {
      id: 'saturn',
      title: 'Saturn — Pressure & Maturation',
      subtitle: `${placements.saturn || 'Unknown'}${placements.saturn_house ? ` in the ${getHouseOrdinal(placements.saturn_house)} house` : ''}`,
      preview: `In your chart, pressure and mastery concentrate in ${getHouseTheme(placements.saturn_house || 1)}.`,
      whatThisIs: `In your chart, Saturn in ${placements.saturn || 'Unknown'}${placements.saturn_house ? ` placed in House ${placements.saturn_house}` : ''} reveals where you face the most pressure, where you are asked to grow up, and where eventual mastery becomes possible. This is your assignment—what life keeps returning you to until you get serious about it.`,
      whatYouMightNotice: [
        `Recurring challenges around ${getHouseTheme(placements.saturn_house || 1)} themes`,
        `A sense that this area requires more effort than it should`,
        `Delayed rewards that eventually become the most solid`,
        `Where your inner critic tends to focus`
      ],
      tensionLabel: 'Where fear lives',
      tension: `Saturn points to where you feel inadequate or behind. In House ${placements.saturn_house || '?'}, you may avoid, over-control, or feel chronically not-good-enough. The pressure is real—and so is the growth potential.`,
      giftLabel: 'Where mastery builds',
      gift: `What Saturn touches, you eventually master through persistence. This isn't easy success—it's earned authority. Over time, you become the person others trust in this domain.`,
      reflection: `What do you take most seriously? Where do you feel you're still catching up?`
    },
    // === NEW: Nodes === (SHARPER DEVELOPMENTAL FRAMING)
    {
      id: 'nodes',
      title: 'Nodes — Direction & Pattern',
      subtitle: `☊ ${placements.north_node || 'Unknown'} · ☋ ${placements.south_node || 'Unknown'}`,
      preview: `Growth pulls from ${placements.south_node || 'Unknown'} familiarity toward ${placements.north_node || 'Unknown'} unfamiliarity.`,
      whatThisIs: `The nodal axis is your developmental storyline. South Node in ${placements.south_node || 'Unknown'}${placements.south_node_house ? ` (House ${placements.south_node_house})` : ''} represents what you already know—your default competency, your comfort zone, your reliable pattern. North Node in ${placements.north_node || 'Unknown'}${placements.north_node_house ? ` (House ${placements.north_node_house})` : ''} is where life keeps pushing you—unfamiliar, less confident, but where growth actually happens.`,
      whatYouMightNotice: [
        `WHAT FEELS FAMILIAR: ${placements.south_node || 'Unknown'} ways of operating—you're good at this, maybe too good`,
        `WHERE LIFE PULLS YOU: Toward ${placements.north_node || 'Unknown'} territory—less practiced, more growth`,
        `THE COMFORT TRAP: Defaulting to ${placements.south_node || 'Unknown'} competence when stressed`,
        `WHAT GROWTH FEELS LIKE: Awkward, uncertain, but right`
      ],
      tensionLabel: 'The comfort trap',
      tension: `${placements.south_node || 'The South Node'} is seductive because you're already competent there. You can coast on these skills indefinitely—but diminishing returns set in. The more you stay, the less alive it feels. The pattern that once protected you starts to confine you.`,
      giftLabel: 'What growth actually asks',
      gift: `${placements.north_node || 'The North Node'} isn't asking you to abandon your South Node gifts—it's asking you to use them in service of something new. Growth feels less like achievement and more like trust. Less control, more allowing.`,
      reflection: `What familiar pattern do you keep returning to even when you know it's limiting? What would it mean to actually trust the unfamiliar direction?`
    },
    // === NEW: Chiron === (MORE PRECISE WOUND/MEDICINE FRAMING)
    {
      id: 'chiron',
      title: 'Chiron — Wound & Medicine',
      subtitle: `${placements.chiron || 'Unknown'}${placements.chiron_house ? ` in the ${getHouseOrdinal(placements.chiron_house)} house` : ''}`,
      preview: `A wound in ${getHouseTheme(placements.chiron_house || 1)} that teaches rather than heals.`,
      whatThisIs: `Chiron in ${placements.chiron || 'Unknown'}${placements.chiron_house ? ` (House ${placements.chiron_house})` : ''} marks where you carry a wound that doesn't fully close. This isn't failure—it's specificity. You're sensitized to ${getHouseTheme(placements.chiron_house || 1)} in ways others aren't. This sensitivity developed into adaptive intelligence.`,
      whatYouMightNotice: [
        `WHERE IT HURTS: ${getHouseTheme(placements.chiron_house || 1)} themes trigger you more than they should`,
        `WHAT YOU LEARNED TO DO: Compensate, over-function, or avoid in this area`,
        `THE MEDICINE INSIDE IT: You understand others' pain here because you've lived it`,
        `WHEN IT OVER-IDENTIFIES: You may believe "this wound is who I am"`
      ],
      tensionLabel: 'Where it still hurts',
      tension: `The Chiron wound stays tender. In ${getHouseTheme(placements.chiron_house || 1)}, you can be triggered by things that don't bother others. You may over-compensate, trying to prove the wound isn't there—or collapse into identifying with it completely.`,
      giftLabel: 'The medicine you carry',
      gift: `Because you've struggled here, you understand it from the inside. You can guide others through ${getHouseTheme(placements.chiron_house || 1)} difficulties—not as someone who's "healed" but as someone who knows the terrain. The wound becomes teaching, not in spite of the pain but through it.`,
      reflection: `What wound are you still trying to fix instead of integrate? Where might your pain be useful to someone else?`
    },
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
    const keyAspects = getKeyAspects(fullChartData);

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

        {/* KEY ASPECT DYNAMICS */}
        {keyAspects.length > 0 && (
          <View style={[styles.keyAspectsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.keyAspectsTitle, { color: theme.accent }]}>KEY ASPECT DYNAMICS</Text>
            {keyAspects.map((asp, i) => (
              <View key={i} style={styles.keyAspectItem}>
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
                <Text style={[styles.keyAspectMeaning, { color: theme.textSecondary }]}>{asp.meaning}</Text>
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
  // RENDER: TODAY SNAPSHOT (Transit-Based)
  // ============================================
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

    // Get symbol for aspect type
    const getAspectSymbol = (type: string) => {
      const symbols: { [key: string]: string } = {
        'conjunction': '☌',
        'opposition': '☍',
        'square': '□',
        'trine': '△',
        'sextile': '⚹',
        'quincunx': '⚻'
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

        {/* Strongest Transit Hits */}
        <View style={[styles.transitHitsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.transitHitsTitle, { color: theme.textTertiary }]}>ACTIVE TRANSITS</Text>
          
          {currentWindow?.strongest_hits?.slice(0, 4).map((hit: TransitHit, index: number) => (
            <View key={index} style={styles.transitHitRow}>
              <Text style={[styles.transitHitSymbol, { color: theme.accent }]}>
                {getAspectSymbol(hit.aspect_type)}
              </Text>
              <Text style={[styles.transitHitText, { color: theme.text }]}>
                {hit.transit_point} {hit.aspect_type} {hit.natal_point}
              </Text>
              <Text style={[styles.transitHitOrb, { color: theme.textTertiary }]}>
                {hit.orb.toFixed(1)}°
              </Text>
            </View>
          ))}
        </View>

        {/* Activated Natal Points */}
        <View style={[styles.activatedPointsCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.activatedTitle, { color: theme.accent }]}>NATAL POINTS ACTIVATED</Text>
          <View style={styles.activatedChips}>
            {currentWindow?.activated_natal_points?.slice(0, 5).map((point: string, i: number) => (
              <View key={i} style={[styles.activatedChip, { backgroundColor: theme.accent + '15' }]}>
                <Text style={[styles.activatedChipText, { color: theme.accent }]}>{point}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Life Areas Affected - NEW */}
        {currentWindow?.activated_natal_points && currentWindow.activated_natal_points.length > 0 && (
          <View style={[styles.todayLifeAreas, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.lifeAreasTitle, { color: theme.textTertiary }]}>LIFE AREAS THIS MAY TOUCH</Text>
            {currentWindow.activated_natal_points.slice(0, 4).map((point: string, i: number) => {
              // Map natal points to life area descriptions
              const getLifeAreaForPoint = (pt: string): string => {
                const mapping: { [key: string]: string } = {
                  'Sun': 'Your sense of purpose and how you show up as yourself',
                  'Moon': 'Your emotional needs, comfort patterns, and inner life',
                  'Mercury': 'How you think, communicate, and process information',
                  'Venus': 'Relationships, values, what you find beautiful',
                  'Mars': 'Drive, action, how you assert yourself and handle conflict',
                  'Jupiter': 'Growth, expansion, where you seek meaning',
                  'Saturn': 'Responsibility, structure, where you face pressure to mature',
                  'Uranus': 'Change, disruption, where you crave freedom',
                  'Neptune': 'Intuition, imagination, where boundaries blur',
                  'Pluto': 'Power, transformation, what you cannot control',
                  'North Node': 'Your growth edge and where life pulls you forward',
                  'South Node': 'Old patterns, comfort zones, what feels familiar',
                  'Chiron': 'Wounds and healing, where you can guide others',
                  'ASC': 'How you meet the world and first impressions',
                  'MC': 'Public role, career direction, reputation'
                };
                return mapping[pt] || `The part of your chart represented by ${pt}`;
              };
              
              return (
                <View key={i} style={styles.lifeAreaItem}>
                  <Text style={[styles.lifeAreaBullet, { color: theme.accent }]}>→</Text>
                  <Text style={[styles.lifeAreaText, { color: theme.text }]}>
                    <Text style={{ fontWeight: '600' }}>{point}:</Text> {getLifeAreaForPoint(point)}
                  </Text>
                </View>
              );
            })}
          </View>
        )}

        {/* Emphasis Tags */}
        <View style={[styles.emphasisCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.emphasisTitle, { color: theme.textTertiary }]}>THEMES</Text>
          <View style={styles.emphasisChips}>
            {currentWindow?.emphasis_tags?.slice(0, 4).map((tag: string, i: number) => (
              <View key={i} style={[styles.emphasisChip, { borderColor: theme.border }]}>
                <Text style={[styles.emphasisChipText, { color: theme.textSecondary }]}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Deterministic Summary */}
        <View style={[styles.transitSummaryCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.transitSummaryText, { color: theme.text }]}>
            {currentWindow?.deterministic_summary || 'Transit patterns loading...'}
          </Text>
        </View>

        {/* Transit Reflection Question - Enhanced */}
        <View style={[styles.reflectionCard, { backgroundColor: theme.accent + '06', borderColor: theme.accent + '15' }]}>
          <Text style={[styles.reflectionLabel, { color: theme.accent }]}>A QUESTION FOR THIS {activeAltitude.toUpperCase()}</Text>
          <Text style={[styles.reflectionText, { color: theme.text }]}>
            {(() => {
              const hit = currentWindow?.strongest_hits?.[0];
              if (!hit) return 'What is asking for your attention right now?';
              
              // Get reflection based on transit + natal combination
              const transitPlanet = hit.transit_point;
              const natalPlanet = hit.natal_point;
              const aspectType = hit.aspect_type;
              
              // Saturn transits
              if (transitPlanet === 'Saturn') {
                if (natalPlanet === 'Sun') return 'Where is life asking you to take yourself more seriously?';
                if (natalPlanet === 'Moon') return 'What emotional pattern is being tested or matured right now?';
                if (natalPlanet === 'Venus') return 'What relationship or value is asking for more structure?';
                return 'Where is growth asking for maturity rather than speed?';
              }
              
              // Jupiter transits
              if (transitPlanet === 'Jupiter') {
                if (natalPlanet === 'Sun') return 'Where are you ready to expand beyond old limits?';
                if (natalPlanet === 'Moon') return 'What feels more possible emotionally than it used to?';
                if (natalPlanet === 'Saturn') return 'Where is opportunity meeting your sense of responsibility?';
                return 'Where might expansion meet resistance today?';
              }
              
              // Pluto transits
              if (transitPlanet === 'Pluto') {
                if (natalPlanet === 'Sun') return 'What part of your identity is being fundamentally reshaped?';
                if (natalPlanet === 'Moon') return 'What deep emotional truth is surfacing?';
                return 'What is being transformed that you cannot control?';
              }
              
              // Uranus transits
              if (transitPlanet === 'Uranus') {
                if (natalPlanet === 'Sun') return 'Where is life disrupting your sense of who you are?';
                if (natalPlanet === 'Venus') return 'What unexpected changes are happening in relationships or values?';
                return 'Where is sudden change creating new possibilities?';
              }
              
              // Neptune transits
              if (transitPlanet === 'Neptune') {
                if (natalPlanet === 'Sun') return 'What illusions about yourself are dissolving?';
                if (natalPlanet === 'Moon') return 'Where are your emotional boundaries becoming more fluid?';
                return 'What is asking to be surrendered rather than controlled?';
              }
              
              // Mars transits
              if (transitPlanet === 'Mars') {
                return 'What is activating your drive or desire to act?';
              }
              
              // Venus transits
              if (transitPlanet === 'Venus') {
                return 'What is inviting connection or appreciation?';
              }
              
              // Default based on aspect type
              if (aspectType === 'square' || aspectType === 'opposition') {
                return `What tension is ${transitPlanet} creating with your natal ${natalPlanet}?`;
              } else if (aspectType === 'conjunction') {
                return `What is ${transitPlanet} intensifying in your ${natalPlanet}?`;
              } else {
                return `How is ${transitPlanet}'s energy supporting your ${natalPlanet}?`;
              }
            })()}
          </Text>
        </View>

        <InlineReflectButton
          source={{
            lens: 'astrology',
            type: `transit_${activeAltitude}`,
            name: `${activeAltitude} Transits`,
            id: `astrology_transit_${activeAltitude}`,
          }}
          prompt={`Reflect on transits: ${currentWindow?.deterministic_summary || ''}`}
        />
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
  keyAspectItem: {
    marginBottom: 10,
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
    fontSize: 12,
    lineHeight: 16,
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
});
