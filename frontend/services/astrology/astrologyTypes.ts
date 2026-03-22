// ============================================
// ASTROLOGY TYPES & CONTRACTS
// All shared interfaces for the astrology lens
// ============================================

// === BASE PLANET/POSITION TYPES ===

export interface PlanetData {
  sign: string;
  degree: number;
  longitude: number;
  house: number;
  retrograde: boolean;
  formatted?: string;
}

// === TRANSIT TYPES ===

export interface TransitHit {
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

export interface TransitWindow {
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

export interface TransitData {
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

// === FULL CHART DATA ===

export interface FullChartData {
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

// === PLACEMENT TYPES ===

export interface CorePlacements {
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

// === INTERPRETATION ENGINE TYPES ===

export interface ChartRuler {
  planet: string;
  sign: string;
  house: number;
}

export interface HouseRulerChain {
  house: number;
  sign: string;
  ruler: string;
  rulerHouse: number;
  rulerSign: string;
  meaningConnection: string;
}

export interface PlanetStrength {
  planet: string;
  sign: string;
  house: number;
  dignityScore: number;
  houseScore: number;
  aspectCount: number;
  isChartRuler: boolean;
  conjunctLuminary: boolean;
  totalScore: number;
  strengthLabel: 'strong' | 'moderate' | 'challenged';
}

export interface PriorityPlanet {
  planet: string;
  rank: number;
  reasons: string[];
  strength: PlanetStrength;
}

export interface TransitPriority {
  transit: TransitHit;
  priorityScore: number;
  priorityLabel: 'primary' | 'supporting' | 'background';
  boostReasons: string[];
}

export interface PersonalRelevanceMatch {
  isHighRelevance: boolean;
  matchType: 'house' | 'angular' | 'element' | null;
  matchDetail?: string;
}

export interface ThemeConcentration {
  theme: string;
  sources: string[];
  count: number;
  collapsedLine: string;
}

export interface ChapterInfo {
  hasChapterTransit: boolean;
  transitPlanet: string | null;
  natalPoint: string | null;
  chapterTheme: string | null;
}

export interface RepeatPattern {
  isRepeating: boolean;
  repeatedTheme: string | null;
  count: number;
  sources: string[];
}

// === HOUSE MEANING TYPE ===

export interface HouseMeaning {
  label: string;
  shortLabel: string;
  arena: string;
  theme: string;
  whenActivated: string;
  specialty: string;
  developmentalPressure: string;
  consequenceZone: string;
  whenIgnored: string;
}

export interface HouseMistakes {
  primary: string;
  supporting: string[];
}

export interface HouseBehaviors {
  today: string[];
  week: string[];
  month: string[];
}

// === LIFE ARENA TYPE ===

export interface LifeArena {
  label: string;
  shortLabel: string;
  explanation: string;
  whenIgnored: string;
}

// === DEEP DIVE CARD TYPE ===

export interface AstrologyDeepDiveCard {
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

// === ASPECT TYPES ===

export interface KeyAspect {
  aspect: string;
  quality: 'ease' | 'friction' | 'dynamic';
  meaning: string;
  whyItMatters: string;
}

// === ENERGY SYNTHESIS TYPE ===

export interface EnergySynthesis {
  headline: string;
  body: string;
  supporting?: string;
}

// === SUMMARY DATA TYPE ===

export interface AstrologySection {
  label: string;
  body: string;
}

export interface AstrologySummaryData {
  title?: string;
  sections?: AstrologySection[];
  mirror_prompt?: string;
  core_placements?: CorePlacements;
  success?: boolean;
  error?: string;
  message?: string;
}

// === TIMEFRAME TYPE ===

export type Timeframe = 'today' | 'week' | 'month';

// === HOUSE ANALYSIS TYPE ===

export interface HouseAnalysis {
  dominant: number[];
  emphasis: string;
  insight: string;
}

// === WHAT MATTERS ITEM ===

export interface WhatMattersItem {
  rank: number;
  label: string;
  descriptor: string;
  force: string;
}

// === DEVELOPMENTAL PRESSURE ITEM ===

export interface DevelopmentalPressureItem {
  planet: string;
  house: number;
  pressure: string;
}

// === ASPECT PATTERN TYPES (Master Astrologer v3) ===

export interface Stellium {
  clusterType: 'sign_cluster' | 'house_cluster';
  sign?: string;
  house?: number;
  planets: string[];
  concentrationScore: number;
  psychologicalSummary: string;
  lifeAreas: string[];
}

export interface OppositionAxis {
  axisPoints: { planet: string; house: number }[];
  axisHouses: number[];
  axisTheme: string;
  pressureScore: number;
  lifeAreas: string[];
}

export interface PressureTriangle {
  focalPlanet: string;
  focalHouse: number;
  supportingPlanets: string[];
  tensionTheme: string;
  intensityScore: number;
  lifeAreas: string[];
  howItManifests: string;
}

export interface FlowPattern {
  planetsInvolved: string[];
  easeTheme: string;
  giftScore: number;
  possibleBlindSpot: string;
  lifeAreas: string[];
}

export interface ConjunctionChain {
  planetsInvolved: string[];
  mergedTheme: string;
  compressionScore: number;
  lifeAreas: string[];
  psychologicalEffect: string;
}

export interface AspectPatternAnalysis {
  stelliums: Stellium[];
  oppositionAxes: OppositionAxis[];
  pressureTriangles: PressureTriangle[];
  flowPatterns: FlowPattern[];
  conjunctionChains: ConjunctionChain[];
  
  // Priority outputs
  dominantPattern: DominantAspectPattern | null;
  secondaryPatterns: DominantAspectPattern[];
  
  // Pressure synthesis
  howPressureBuilds: HowPressureBuilds;
}

export interface DominantAspectPattern {
  patternType: 'stellium' | 'opposition_axis' | 'pressure_triangle' | 'flow_pattern' | 'conjunction_chain';
  patternData: Stellium | OppositionAxis | PressureTriangle | FlowPattern | ConjunctionChain;
  priorityScore: number;
  relevanceReason: string;
  plainLanguageSummary: string;
}

export interface HowPressureBuilds {
  mainStatement: string;
  lifeAreaStatement: string;
  hasSignificantPattern: boolean;
  patternType: string | null;
  whatKeepsTightening: string;
  whereItCollects: string;
  howItTriesToResolve: string;
  giftInsideThePressure: string;
  reflectionQuestion: string;
}

// === UPGRADED KEY ASPECT TYPE ===

export interface EnhancedKeyAspect {
  aspectPair: string;
  humanSummary: string;
  whyItMattersHere: string;
  pressureType: 'pressure' | 'complexity' | 'flow';
  involvedHouses: number[];
  lifeAreas: string[];
}
