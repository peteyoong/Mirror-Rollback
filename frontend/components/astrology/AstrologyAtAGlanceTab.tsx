// ============================================
// ASTROLOGY AT A GLANCE TAB
// Renders: Hero, Chart Spine, What Matters Most, Main Life Arenas, Developmental Row
// ============================================

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

import {
  FullChartData,
  CorePlacements,
  LifeArena,
  WhatMattersItem,
  KeyAspect,
  EnhancedKeyAspect,
  AspectPatternAnalysis,
  LifeChapterAnalysis,
  LifeChapterNarrative,
} from '../../services/astrology/astrologyTypes';

import {
  SIGN_ELEMENTS,
  SIGN_MODALITIES,
  SIGN_QUALITIES,
  HOUSE_MEANINGS,
  getChartRuler,
  getDominantHouses,
  getMainLifeArenas,
  getDominantPlanets,
  buildPlanetStrengths,
  buildAspectPatternAnalysis,
  getEnhancedKeyAspects,
  buildLifeChapterAnalysis,
  buildLifeChapterNarrative,
  generateChartAxis,
  rankMostImportantFactors,
} from '../../services/astrology/astrologyInterpreter';

import {
  getHeroDescriptor,
  getChartSpine,
  getWhereLifeKeepsWorkingOnYou,
} from '../../services/astrology/astrologyNarrative';

import { cleanText } from '../../utils/languageGuard';

// ============================================
// PROPS INTERFACE
// ============================================

interface AstrologyAtAGlanceTabProps {
  placements: CorePlacements;
  fullChartData: FullChartData | null;
  theme: any;
  onOpenChat: () => void;
  aspectsExpanded: boolean;
  setAspectsExpanded: (expanded: boolean) => void;
  tensionsGiftsExpanded: boolean;
  setTensionsGiftsExpanded: (expanded: boolean) => void;
}

// ============================================
// HELPER FUNCTIONS (UI-specific calculations)
// ============================================

// Get synthesis statement
const getSynthesis = (sun: string, moon: string, asc: string): string => {
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  const ascElement = SIGN_ELEMENTS[asc];
  
  if (sunElement === moonElement && moonElement === ascElement) {
    const unified: { [key: string]: string } = {
      'Fire': 'A triple-fire signature—expressive, visible, naturally warm.',
      'Earth': 'A triple-earth signature—grounded, practical, steady.',
      'Air': 'A triple-air signature—curious, conceptual, relational.',
      'Water': 'A triple-water signature—feeling-led, intuitive, emotionally deep.'
    };
    return unified[sunElement] || 'A unified elemental signature.';
  }
  
  const elementCount: { [key: string]: number } = {};
  [sunElement, moonElement, ascElement].forEach(el => {
    if (el) elementCount[el] = (elementCount[el] || 0) + 1;
  });
  
  const dominant = Object.entries(elementCount).sort((a, b) => b[1] - a[1])[0];
  if (dominant && dominant[1] >= 2) {
    const descriptors: { [key: string]: string } = {
      'Fire': 'Fire-dominant: visibility, self-expression, and initiative come naturally.',
      'Earth': 'Earth-dominant: practicality and tangible results anchor you.',
      'Air': 'Air-dominant: ideas and connection drive your engagement.',
      'Water': 'Water-dominant: emotional depth and intuition guide your path.'
    };
    return descriptors[dominant[0]] || 'A distinctive elemental blend.';
  }
  
  return 'A mixed elemental signature—versatile, adaptable, complex.';
};

// Get theme chips
const getThemeChips = (sun: string, moon: string, asc: string): string[] => {
  const sunMod = SIGN_MODALITIES[sun];
  const moonMod = SIGN_MODALITIES[moon];
  const ascMod = SIGN_MODALITIES[asc];
  
  const chips: string[] = [];
  
  if (sunMod === 'Cardinal') chips.push('Initiating');
  if (sunMod === 'Fixed') chips.push('Persistent');
  if (sunMod === 'Mutable') chips.push('Adaptable');
  
  const sunElement = SIGN_ELEMENTS[sun];
  if (sunElement === 'Fire') chips.push('Expressive');
  if (sunElement === 'Earth') chips.push('Grounded');
  if (sunElement === 'Air') chips.push('Curious');
  if (sunElement === 'Water') chips.push('Feeling');
  
  if (moonMod !== sunMod) {
    if (moonMod === 'Fixed') chips.push('Emotionally Steady');
    if (moonMod === 'Mutable') chips.push('Emotionally Fluid');
  }
  
  return chips.slice(0, 4);
};

// Get core tensions
const getCoreTensions = (sun: string, moon: string, asc: string): string[] => {
  const tensions: string[] = [];
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  const ascElement = SIGN_ELEMENTS[asc];

  if (sunElement === 'Fire' && moonElement === 'Water') {
    tensions.push('Outer confidence, inner sensitivity—what you show vs. what you feel');
  }
  if (sunElement === 'Earth' && moonElement === 'Air') {
    tensions.push('Practical nature meets restless mind—wanting both stability and variety');
  }
  if (sunElement === 'Air' && ascElement === 'Earth') {
    tensions.push('Ideas outpace implementation—what you think vs. how you come across');
  }

  const sunMod = SIGN_MODALITIES[sun];
  const moonMod = SIGN_MODALITIES[moon];
  if (sunMod === 'Cardinal' && moonMod === 'Fixed') {
    tensions.push('Initiative vs. resistance to change—starting what you\'re hesitant to complete');
  }
  if (sunMod === 'Mutable' && moonMod === 'Fixed') {
    tensions.push('Adaptable mind, stubborn heart—flexibility with resistance');
  }

  if (tensions.length === 0) {
    tensions.push('Your Big 3 work relatively harmoniously—less inner conflict, more consistency');
  }

  return tensions;
};

// Get core gifts
const getCoreGifts = (sun: string, moon: string, asc: string): string[] => {
  const gifts: string[] = [];
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];

  if (sunElement === moonElement) {
    const unified: { [key: string]: string } = {
      'Fire': 'Aligned warmth—what you feel matches what you express',
      'Earth': 'Steady reliability—inner and outer consistency',
      'Air': 'Coherent communication—thinking and feeling align',
      'Water': 'Emotional authenticity—depth that shows'
    };
    if (unified[sunElement]) gifts.push(unified[sunElement]);
  }

  const sunMod = SIGN_MODALITIES[sun];
  const moonMod = SIGN_MODALITIES[moon];
  if (sunMod === moonMod) {
    const modGifts: { [key: string]: string } = {
      'Cardinal': 'Double initiative—natural leadership energy',
      'Fixed': 'Double steadiness—unusual persistence',
      'Mutable': 'Double flexibility—exceptional adaptability'
    };
    if (modGifts[sunMod]) gifts.push(modGifts[sunMod]);
  }

  if (gifts.length === 0) {
    gifts.push('Range—your Big 3 give you access to different modes of being');
  }

  return gifts;
};

// ============================================
// KEY ASPECT DYNAMICS - Aspect Ranking & Selection
// ============================================

interface KeyAspectDynamic {
  label: string;
  category: 'EASE' | 'FRICTION' | 'COMPLEXITY';
  humanSummary: string;
  orb: number;
  score: number;
}

interface NatalAspect {
  point_a: string;
  point_b: string;
  aspect_type: string;
  orb: number;
  applying?: boolean;
}

// Priority points for determining chart-defining aspects
const POINT_PRIORITY: { [key: string]: number } = {
  'Sun': 10,
  'Moon': 9,
  'Ascendant': 8,
  'MC': 7,
  'Saturn': 7,
  'North Node': 6,
  'South Node': 6,
  'Chiron': 6,
  'Jupiter': 5,
  'Mars': 5,
  'Venus': 5,
  'Mercury': 4,
  'Pluto': 4,
  'Neptune': 3,
  'Uranus': 3,
};

// Aspect type priorities (more structurally meaningful = higher)
const ASPECT_TYPE_PRIORITY: { [key: string]: number } = {
  'conjunction': 10,
  'opposition': 9,
  'square': 8,
  'trine': 6,
  'sextile': 5,
  'quincunx': 3,
  'semi-sextile': 2,
  'semi-square': 2,
  'sesquiquadrate': 2,
};

// Aspect category mapping
const getAspectCategory = (aspectType: string): 'EASE' | 'FRICTION' | 'COMPLEXITY' => {
  const easeAspects = ['trine', 'sextile'];
  const frictionAspects = ['square', 'opposition', 'semi-square', 'sesquiquadrate'];
  const complexityAspects = ['conjunction', 'quincunx', 'semi-sextile'];
  
  if (easeAspects.includes(aspectType)) return 'EASE';
  if (frictionAspects.includes(aspectType)) return 'FRICTION';
  return 'COMPLEXITY';
};

// Human-readable aspect type names
const ASPECT_TYPE_DISPLAY: { [key: string]: string } = {
  'conjunction': 'conjunct',
  'opposition': 'opposite',
  'square': 'square',
  'trine': 'trine',
  'sextile': 'sextile',
  'quincunx': 'quincunx',
  'semi-sextile': 'semi-sextile',
  'semi-square': 'semi-square',
  'sesquiquadrate': 'sesquiquadrate',
};

// Generate human summary for aspect (chart-specific, not cookbook)
const getAspectHumanSummary = (pointA: string, pointB: string, aspectType: string): string => {
  const category = getAspectCategory(aspectType);
  
  // Sun aspects
  if (pointA === 'Sun' || pointB === 'Sun') {
    const other = pointA === 'Sun' ? pointB : pointA;
    if (other === 'Moon') return category === 'EASE' 
      ? 'Identity and emotional nature flow together here.'
      : 'What you show and what you feel can pull in different directions.';
    if (other === 'Saturn') return category === 'EASE'
      ? 'A natural sense of structure supports your identity.'
      : 'Identity and pressure are tightly linked in this chart.';
    if (other === 'Jupiter') return category === 'EASE'
      ? 'A natural expansiveness colors how you express yourself.'
      : 'Confidence and over-reach can become entangled.';
    if (other === 'Mars') return category === 'EASE'
      ? 'Drive and identity are naturally aligned.'
      : 'Will and action can clash with sense of self.';
    if (other === 'Chiron') return 'Sensitivity around self-expression runs deep here.';
    if (other === 'North Node') return 'Identity is closely tied to developmental direction.';
    if (other === 'Pluto') return 'Intensity and transformation touch the core of who you are.';
    if (other === 'Neptune') return 'Imagination and idealism color your sense of self.';
    if (other === 'Uranus') return 'Individuality and unpredictability are woven into your identity.';
  }
  
  // Moon aspects
  if (pointA === 'Moon' || pointB === 'Moon') {
    const other = pointA === 'Moon' ? pointB : pointA;
    if (other === 'Mars') return category === 'EASE'
      ? 'Feeling and action work together fluidly.'
      : 'Feeling and action can collide quickly here.';
    if (other === 'Saturn') return category === 'EASE'
      ? 'Emotional stability comes from structure.'
      : 'Emotional life carries developmental weight.';
    if (other === 'Venus') return 'Emotional needs and relationship needs are intertwined.';
    if (other === 'Jupiter') return category === 'EASE'
      ? 'Emotional optimism and generosity flow naturally.'
      : 'Emotional needs can inflate or overwhelm.';
    if (other === 'Chiron') return 'Emotional sensitivity runs especially deep here.';
    if (other === 'Pluto') return 'Emotional intensity and depth are amplified.';
    if (other === 'Neptune') return 'Emotional life has a permeable, imaginative quality.';
    if (other === 'North Node') return 'Emotional patterns are linked to growth direction.';
  }
  
  // Saturn aspects
  if (pointA === 'Saturn' || pointB === 'Saturn') {
    const other = pointA === 'Saturn' ? pointB : pointA;
    if (other === 'Jupiter') return category === 'EASE'
      ? 'Expansion and restraint are in productive conversation.'
      : 'Expansion and restraint are in active tension.';
    if (other === 'Mars') return category === 'EASE'
      ? 'Discipline and drive work well together.'
      : 'Action and restriction create friction.';
    if (other === 'Chiron') return 'Pressure and sensitivity are connected here.';
    if (other === 'North Node') return 'Structure and life direction are tightly linked.';
    if (other === 'Pluto') return 'Power, control, and maturation are intertwined.';
  }
  
  // Venus aspects
  if (pointA === 'Venus' || pointB === 'Venus') {
    const other = pointA === 'Venus' ? pointB : pointA;
    if (other === 'Mars') return category === 'EASE'
      ? 'Desire and action are naturally aligned.'
      : 'Desire and assertion can create tension.';
    if (other === 'Pluto') return 'Relationships carry intensity and depth.';
    if (other === 'Neptune') return 'Love and idealism are deeply connected.';
    if (other === 'Uranus') return 'Relationships have an unconventional or unpredictable quality.';
    if (other === 'Mercury') return 'Communication and connection are closely linked.';
  }
  
  // Mercury aspects
  if (pointA === 'Mercury' || pointB === 'Mercury') {
    const other = pointA === 'Mercury' ? pointB : pointA;
    if (other === 'Pluto') return 'Thinking runs deep—perception can be penetrating.';
    if (other === 'Neptune') return 'Mind and imagination are closely connected.';
    if (other === 'North Node') return 'Communication is linked to developmental direction.';
  }
  
  // Chiron aspects
  if (pointA === 'Chiron' || pointB === 'Chiron') {
    const other = pointA === 'Chiron' ? pointB : pointA;
    if (other === 'Neptune') return 'Sensitivity and healing themes are amplified.';
    if (other === 'Uranus') return 'Sensitivity and individuality are connected.';
    if (other === 'Pluto') return 'Deep transformation and healing are intertwined.';
  }
  
  // Node aspects
  if (pointA === 'North Node' || pointB === 'North Node' || pointA === 'South Node' || pointB === 'South Node') {
    return 'This connects directly to your developmental axis.';
  }
  
  // Outer planet connections
  if ((pointA === 'Uranus' || pointB === 'Uranus') && (pointA === 'Pluto' || pointB === 'Pluto')) {
    return 'Generational forces of disruption and transformation are linked.';
  }
  if ((pointA === 'Neptune' || pointB === 'Neptune') && (pointA === 'Pluto' || pointB === 'Pluto')) {
    return 'Collective undercurrents of dissolution and power are connected.';
  }
  if ((pointA === 'Uranus' || pointB === 'Uranus') && (pointA === 'Neptune' || pointB === 'Neptune')) {
    return 'Idealism and disruption are in conversation.';
  }
  
  // Generic fallback
  return `This links ${pointA.toLowerCase()} and ${pointB.toLowerCase()} themes in your chart.`;
};

// Calculate aspect score for ranking
const calculateAspectScore = (aspect: NatalAspect): number => {
  const pointAPriority = POINT_PRIORITY[aspect.point_a] || 1;
  const pointBPriority = POINT_PRIORITY[aspect.point_b] || 1;
  const aspectPriority = ASPECT_TYPE_PRIORITY[aspect.aspect_type] || 1;
  
  // Combined priority score
  const priorityScore = pointAPriority + pointBPriority + aspectPriority;
  
  // Orb bonus: tighter orb = higher score (max 10 for exact, 0 for 10+ degree orb)
  const orbBonus = Math.max(0, 10 - aspect.orb);
  
  return priorityScore + orbBonus;
};

// Get key aspect dynamics from natal aspects
const getKeyAspectDynamics = (aspects: NatalAspect[] | undefined): KeyAspectDynamic[] => {
  if (!aspects || aspects.length === 0) return [];
  
  // Filter to meaningful aspect types (exclude very minor aspects)
  const meaningfulAspects = aspects.filter(a => 
    ASPECT_TYPE_PRIORITY[a.aspect_type] !== undefined &&
    ASPECT_TYPE_PRIORITY[a.aspect_type] >= 2
  );
  
  // Score and rank all aspects
  const scoredAspects = meaningfulAspects.map(aspect => ({
    ...aspect,
    score: calculateAspectScore(aspect),
  }));
  
  // Sort by score descending
  scoredAspects.sort((a, b) => b.score - a.score);
  
  // Take top 5
  const topAspects = scoredAspects.slice(0, 5);
  
  // Build output
  return topAspects.map(aspect => ({
    label: `${aspect.point_a} ${ASPECT_TYPE_DISPLAY[aspect.aspect_type] || aspect.aspect_type} ${aspect.point_b}`,
    category: getAspectCategory(aspect.aspect_type),
    humanSummary: getAspectHumanSummary(aspect.point_a, aspect.point_b, aspect.aspect_type),
    orb: aspect.orb,
    score: aspect.score,
  }));
};

// Get What Matters Most in chart
const getWhatMattersMost = (placements: CorePlacements, chartData: FullChartData | null): WhatMattersItem[] => {
  const items: WhatMattersItem[] = [];
  
  const chartRuler = getChartRuler(chartData);
  if (chartRuler) {
    items.push({
      rank: 1,
      label: `${chartRuler.planet} in ${chartRuler.sign}${chartRuler.house ? ` (House ${chartRuler.house})` : ''}`,
      descriptor: 'Chart Ruler',
      force: 'This shapes how you naturally move through life.'
    });
  }
  
  const sun = placements.sun;
  const sunHouse = placements.sun_house;
  items.push({
    rank: items.length + 1,
    label: `${sun} Sun${sunHouse ? ` in House ${sunHouse}` : ''}`,
    descriptor: 'Core Identity',
    force: sunHouse 
      ? `Identity develops through ${HOUSE_MEANINGS[sunHouse]?.shortLabel || 'this area'}.`
      : 'The essential frequency of who you are.'
  });
  
  const saturnHouse = placements.saturn_house;
  if (saturnHouse) {
    items.push({
      rank: items.length + 1,
      label: `Saturn in House ${saturnHouse}`,
      descriptor: 'Pressure Zone',
      force: `${HOUSE_MEANINGS[saturnHouse]?.developmentalPressure || 'Growth happens here whether you\'re ready or not.'}`
    });
  }
  
  return items.slice(0, 4);
};

// Get key aspects
const getKeyAspects = (chartData: FullChartData | null, placements: CorePlacements): KeyAspect[] => {
  if (!chartData?.natal?.aspects) return [];
  
  const keyAspects: KeyAspect[] = [];
  const aspects = chartData.natal.aspects;
  
  const importantPlanets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Saturn', 'Jupiter'];
  const importantAspects = aspects.filter(asp => 
    importantPlanets.includes(asp.point_a) && 
    importantPlanets.includes(asp.point_b) &&
    Math.abs(asp.orb) < 5
  );
  
  for (const asp of importantAspects.slice(0, 5)) {
    const aspectName = `${asp.point_a} ${asp.aspect_type} ${asp.point_b}`;
    
    let quality: 'ease' | 'friction' | 'dynamic' = 'dynamic';
    if (['trine', 'sextile'].includes(asp.aspect_type)) quality = 'ease';
    if (['square', 'opposition'].includes(asp.aspect_type)) quality = 'friction';
    
    let meaning = '';
    let whyItMatters = '';
    
    if (asp.point_a === 'Sun' && asp.point_b === 'Moon') {
      meaning = quality === 'ease' 
        ? 'Your conscious purpose and emotional needs work together.' 
        : 'Your identity and emotional needs are in tension—what you want vs. what you feel.';
      whyItMatters = 'This is the most fundamental internal relationship in a chart.';
    } else if (asp.point_a === 'Sun' && asp.point_b === 'Saturn') {
      meaning = quality === 'ease'
        ? 'Discipline and identity align—you naturally structure yourself.'
        : 'Pressure on your sense of self—doubt competes with confidence.';
      whyItMatters = 'Saturn-Sun aspects shape your relationship with authority and achievement.';
    } else {
      meaning = quality === 'ease'
        ? `${asp.point_a} and ${asp.point_b} support each other naturally.`
        : `${asp.point_a} and ${asp.point_b} create productive tension.`;
      whyItMatters = 'This is a defining dynamic in how you operate.';
    }
    
    keyAspects.push({ aspect: aspectName, quality, meaning, whyItMatters });
  }
  
  return keyAspects;
};

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyAtAGlanceTab: React.FC<AstrologyAtAGlanceTabProps> = ({
  placements,
  fullChartData,
  theme,
  onOpenChat,
  aspectsExpanded,
  setAspectsExpanded,
  tensionsGiftsExpanded,
  setTensionsGiftsExpanded,
}) => {
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

  // Use services for data
  const heroDescriptor = getHeroDescriptor(sun, moon, asc);
  const chartSpine = getChartSpine(placements);
  const mainArenas = getMainLifeArenas(fullChartData);
  const whereLifeWorks = getWhereLifeKeepsWorkingOnYou(fullChartData);
  
  // NEW: Chart Axis - the developmental spine of the chart
  const chartAxis = generateChartAxis(placements, fullChartData);
  
  // NEW: Most Important Factors ranking
  const mostImportantFactors = rankMostImportantFactors(placements, fullChartData);
  
  // Aspect pattern analysis (Master Astrologer v3)
  const patternAnalysis = buildAspectPatternAnalysis(fullChartData);
  const enhancedAspects = getEnhancedKeyAspects(fullChartData, 4);
  
  // Use local helpers for UI-specific calculations
  const synthesis = getSynthesis(sun, moon, asc);
  const themeChips = getThemeChips(sun, moon, asc);
  const tensions = getCoreTensions(sun, moon, asc);
  const gifts = getCoreGifts(sun, moon, asc);
  const whatMattersMost = getWhatMattersMost(placements, fullChartData);
  const keyAspects = getKeyAspects(fullChartData, placements);
  
  // NEW: Key Aspect Dynamics - top 5 chart-defining aspects
  const natalAspects = fullChartData?.natal?.aspects || [];
  const keyAspectDynamics = getKeyAspectDynamics(natalAspects);
  
  // Life Chapter analysis (Master Astrologer v4)
  const chapterAnalysis = buildLifeChapterAnalysis(fullChartData);
  const chapterNarrative = chapterAnalysis.primaryChapter 
    ? buildLifeChapterNarrative(chapterAnalysis.primaryChapter, patternAnalysis)
    : null;
  
  // Developmental pressure row data
  const saturnHouse = placements.saturn_house;
  const chironHouse = placements.chiron_house;
  const northNodeHouse = placements.north_node_house;

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
        <Text style={[styles.heroDescriptor, { color: theme.textSecondary }]}>{cleanText(heroDescriptor)}</Text>
      </View>

      {/* CHART SPINE */}
      <View style={[styles.chartSpineCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.chartSpineTitle, { color: theme.accent }]}>CHART SPINE</Text>
        {chartSpine.map((statement, i) => (
          <Text key={i} style={[styles.chartSpineStatement, { color: theme.text }]}>
            {statement}
          </Text>
        ))}
      </View>

      {/* CHART AXIS - The developmental spine (NEW) */}
      {chartAxis.lines.length > 0 && (
        <View style={[styles.chartAxisCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '25' }]}>
          <Text style={[styles.chartAxisTitle, { color: theme.accent }]}>CHART AXIS</Text>
          <Text style={[styles.chartAxisSubtitle, { color: theme.textTertiary }]}>
            The developmental spine of this chart
          </Text>
          {chartAxis.lines.map((line, i) => (
            <Text key={i} style={[styles.chartAxisLine, { color: theme.text }]}>
              {line}
            </Text>
          ))}
        </View>
      )}

      {/* MOST IMPORTANT FACTORS (NEW) */}
      {mostImportantFactors.length > 0 && (
        <View style={[styles.whatMattersCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.whatMattersTitle, { color: theme.accent }]}>MOST IMPORTANT FACTORS IN THIS CHART</Text>
          {mostImportantFactors.map((factor, i) => (
            <View key={i} style={styles.whatMattersItem}>
              <Text style={[styles.whatMattersRank, { color: theme.accent }]}>{factor.rank}</Text>
              <View style={styles.whatMattersContent}>
                <Text style={[styles.whatMattersLabel, { color: theme.text }]}>{factor.factorName}</Text>
                <Text style={[styles.whatMattersForce, { color: theme.textSecondary }]}>{factor.whyItMatters}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* LIFE CHAPTER - Master Astrologer v4 */}
      {chapterNarrative && chapterAnalysis.hasActiveChapter && (
        <View style={[styles.lifeChapterCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.lifeChapterLabel, { color: theme.accent }]}>LIFE CHAPTER</Text>
          <Text style={[styles.lifeChapterTitle, { color: theme.text }]}>{chapterNarrative.chapterTitle}</Text>
          <Text style={[styles.lifeChapterDescription, { color: theme.textSecondary }]}>
            {chapterNarrative.coreDescription}
          </Text>
          {chapterAnalysis.primaryChapter && chapterAnalysis.primaryChapter.lifeAreas.length > 0 && (
            <Text style={[styles.lifeChapterAreas, { color: theme.textTertiary }]}>
              This phase is especially active in {chapterAnalysis.primaryChapter.lifeAreas.slice(0, 2).join(' and ')}.
            </Text>
          )}
        </View>
      )}

      {/* HOW PRESSURE BUILDS IN THIS CHART - New Section */}
      {patternAnalysis.howPressureBuilds.hasSignificantPattern && (
        <View style={[styles.pressureCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.whatMattersTitle, { color: theme.accent }]}>HOW PRESSURE BUILDS IN THIS CHART</Text>
          <Text style={[styles.pressureMainStatement, { color: theme.text }]}>
            {patternAnalysis.howPressureBuilds.mainStatement}
          </Text>
          {patternAnalysis.howPressureBuilds.lifeAreaStatement && (
            <Text style={[styles.pressureSubStatement, { color: theme.textSecondary }]}>
              {patternAnalysis.howPressureBuilds.lifeAreaStatement}
            </Text>
          )}
        </View>
      )}

      {/* MAIN LIFE ARENAS */}
      {mainArenas.length > 0 && (
        <View style={[styles.whatMattersCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.whatMattersTitle, { color: theme.accent }]}>YOUR CHART'S MAIN LIFE ARENAS</Text>
          <Text style={[styles.sectionSubtitle, { color: theme.textTertiary, marginBottom: 12 }]}>
            Where life keeps training you
          </Text>
          {mainArenas.map((arena, i) => (
            <View key={i} style={styles.whatMattersItem}>
              <Text style={[styles.whatMattersRank, { color: theme.accent }]}>{i + 1}</Text>
              <View style={styles.whatMattersContent}>
                <Text style={[styles.whatMattersLabel, { color: theme.text }]}>{arena.label}</Text>
                <Text style={[styles.whatMattersForce, { color: theme.textSecondary }]}>{arena.explanation}</Text>
                {arena.whenIgnored && (
                  <Text style={[styles.whatMattersIgnored, { color: theme.textTertiary }]}>
                    If ignored: {arena.whenIgnored}
                  </Text>
                )}
              </View>
            </View>
          ))}
          <View style={{ marginTop: 14, paddingTop: 12, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: theme.border }}>
            <Text style={[styles.arenaSynthesis, { color: theme.textSecondary }]}>
              This chart does not spread life evenly. Certain arenas carry more consequence than others—what happens here echoes.
            </Text>
          </View>
          {whereLifeWorks.length > 0 && (
            <View style={{ marginTop: 8 }}>
              {whereLifeWorks.map((statement, i) => (
                <Text key={i} style={[styles.chartSpineStatement, { color: theme.textSecondary, fontStyle: 'italic' }]}>
                  {statement}
                </Text>
              ))}
            </View>
          )}
        </View>
      )}

      {/* DEVELOPMENTAL PRESSURE ROW */}
      {(saturnHouse || chironHouse || northNodeHouse) && (
        <View style={[styles.developmentalCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.whatMattersTitle, { color: theme.accent }]}>DEVELOPMENTAL PRESSURE</Text>
          <Text style={[styles.sectionSubtitle, { color: theme.textTertiary, marginBottom: 12 }]}>
            Where growth keeps getting demanded
          </Text>
          <View style={styles.developmentalGrid}>
            {saturnHouse && (
              <View style={styles.developmentalItem}>
                <Text style={[styles.developmentalHeader, { color: theme.textSecondary }]}>SATURN</Text>
                <Text style={[styles.developmentalLabel, { color: theme.text }]}>
                  House {saturnHouse}: {HOUSE_MEANINGS[saturnHouse]?.shortLabel}
                </Text>
                <Text style={[styles.developmentalDesc, { color: theme.textTertiary }]}>
                  {HOUSE_MEANINGS[saturnHouse]?.developmentalPressure || 'Maturation happens here.'}
                </Text>
              </View>
            )}
            {chironHouse && (
              <View style={styles.developmentalItem}>
                <Text style={[styles.developmentalHeader, { color: theme.textSecondary }]}>CHIRON</Text>
                <Text style={[styles.developmentalLabel, { color: theme.text }]}>
                  House {chironHouse}: {HOUSE_MEANINGS[chironHouse]?.shortLabel}
                </Text>
                <Text style={[styles.developmentalDesc, { color: theme.textTertiary }]}>
                  What hurt you here now makes you useful here.
                </Text>
              </View>
            )}
            {northNodeHouse && (
              <View style={styles.developmentalItem}>
                <Text style={[styles.developmentalHeader, { color: theme.textSecondary }]}>NORTH NODE</Text>
                <Text style={[styles.developmentalLabel, { color: theme.text }]}>
                  House {northNodeHouse}: {HOUSE_MEANINGS[northNodeHouse]?.shortLabel}
                </Text>
                <Text style={[styles.developmentalDesc, { color: theme.textTertiary }]}>
                  Growth edge territory—this doesn't come naturally.
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* CHART STRUCTURE + TENSIONS/GIFTS - COLLAPSIBLE */}
      <TouchableOpacity
        style={[styles.collapsibleSection, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
        onPress={() => setTensionsGiftsExpanded(!tensionsGiftsExpanded)}
        activeOpacity={0.7}
      >
        <View style={styles.collapsibleHeader}>
          <Text style={[styles.collapsibleTitle, { color: theme.textSecondary }]}>Chart structure & inner tensions</Text>
          <Text style={[styles.collapsibleIcon, { color: theme.textTertiary }]}>
            {tensionsGiftsExpanded ? '▴' : '▾'}
          </Text>
        </View>
        {!tensionsGiftsExpanded && (
          <Text style={[styles.collapsibleHint, { color: theme.textTertiary }]}>
            {SIGN_ELEMENTS[sun]} core • {tensions.length} tensions • {gifts.length} gifts
          </Text>
        )}
        {tensionsGiftsExpanded && (
          <View style={styles.collapsibleContent}>
            <View style={styles.structureGridCompact}>
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
            
            {tensions.length > 0 && (
              <View style={{ marginTop: 12 }}>
                <Text style={[styles.collapsibleSubtitle, { color: '#B85450' }]}>TENSIONS</Text>
                {tensions.map((t, i) => (
                  <Text key={i} style={[styles.collapsibleBullet, { color: '#6B4544' }]}>• {t}</Text>
                ))}
              </View>
            )}
            {gifts.length > 0 && (
              <View style={{ marginTop: 10 }}>
                <Text style={[styles.collapsibleSubtitle, { color: '#5A8A62' }]}>GIFTS</Text>
                {gifts.map((g, i) => (
                  <Text key={i} style={[styles.collapsibleBullet, { color: '#3D5A42' }]}>• {g}</Text>
                ))}
              </View>
            )}
          </View>
        )}
      </TouchableOpacity>

      {/* KEY ASPECT DYNAMICS - Chart-defining internal mechanics */}
      {keyAspectDynamics.length > 0 && (
        <View style={[styles.aspectDynamicsSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.aspectDynamicsTitle, { color: theme.text }]}>KEY ASPECT DYNAMICS</Text>
          <Text style={[styles.aspectDynamicsSubtitle, { color: theme.textTertiary }]}>
            The internal mechanics shaping this chart most strongly
          </Text>
          
          <View style={styles.aspectDynamicsList}>
            {keyAspectDynamics.map((aspect, index) => (
              <View key={index} style={[styles.aspectDynamicRow, { borderBottomColor: theme.border }]}>
                <View style={styles.aspectDynamicHeader}>
                  <Text style={[styles.aspectDynamicLabel, { color: theme.text }]}>{aspect.label}</Text>
                  <View style={[
                    styles.aspectDynamicTag,
                    {
                      backgroundColor: aspect.category === 'EASE' ? '#10B98115' :
                                       aspect.category === 'FRICTION' ? '#EF444415' :
                                       '#8B5CF615'
                    }
                  ]}>
                    <Text style={[
                      styles.aspectDynamicTagText,
                      {
                        color: aspect.category === 'EASE' ? '#10B981' :
                               aspect.category === 'FRICTION' ? '#EF4444' :
                               '#8B5CF6'
                      }
                    ]}>{aspect.category}</Text>
                  </View>
                </View>
                <Text style={[styles.aspectDynamicSummary, { color: theme.textSecondary }]}>
                  {aspect.humanSummary}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

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
// STYLES
// ============================================

const styles = StyleSheet.create({
  atAGlanceContainer: {
    padding: 16,
    gap: 12,
  },
  emptyState: {
    padding: 24,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 14,
    textAlign: 'center',
  },
  heroCard: {
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    marginBottom: 4,
  },
  big3Row: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 16,
  },
  big3Item: {
    alignItems: 'center',
    flex: 1,
  },
  big3Divider: {
    width: 1,
    height: 40,
    opacity: 0.3,
  },
  big3Symbol: {
    fontSize: 24,
    marginBottom: 4,
  },
  big3Sign: {
    fontSize: 16,
    fontWeight: '600',
  },
  heroDescriptor: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
    lineHeight: 20,
  },
  chartSpineCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 4,
  },
  chartSpineTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  chartSpineStatement: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 8,
  },
  // CHART AXIS STYLES (NEW)
  chartAxisCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 4,
  },
  chartAxisTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  chartAxisSubtitle: {
    fontSize: 11,
    marginBottom: 14,
    fontStyle: 'italic',
  },
  chartAxisLine: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 10,
    paddingLeft: 0,
  },
  lifeChapterCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 4,
  },
  lifeChapterLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  lifeChapterTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 8,
  },
  lifeChapterDescription: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 6,
  },
  lifeChapterAreas: {
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  whatMattersCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 4,
  },
  whatMattersTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  whatMattersItem: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  whatMattersRank: {
    fontSize: 18,
    fontWeight: '700',
    width: 28,
    marginRight: 8,
  },
  whatMattersContent: {
    flex: 1,
  },
  whatMattersLabel: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  whatMattersDescriptor: {
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 4,
  },
  whatMattersForce: {
    fontSize: 13,
    lineHeight: 19,
  },
  whatMattersIgnored: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 4,
    lineHeight: 16,
  },
  arenaSynthesis: {
    fontSize: 12,
    fontStyle: 'italic',
    lineHeight: 18,
    textAlign: 'center',
  },
  sectionSubtitle: {
    fontSize: 12,
  },
  developmentalCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 4,
  },
  developmentalGrid: {
    gap: 12,
  },
  developmentalItem: {
    marginBottom: 8,
  },
  developmentalHeader: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  developmentalLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  developmentalDesc: {
    fontSize: 12,
    lineHeight: 18,
  },
  collapsibleSection: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 4,
  },
  collapsibleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  collapsibleTitle: {
    fontSize: 13,
    fontWeight: '500',
  },
  collapsibleIcon: {
    fontSize: 11,
    marginLeft: 8,
  },
  collapsibleHint: {
    fontSize: 11,
    marginTop: 4,
  },
  collapsibleContent: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(0,0,0,0.08)',
  },
  collapsibleSubtitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  collapsibleBullet: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 4,
    paddingLeft: 4,
  },
  structureGridCompact: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  structureItem: {
    width: '45%',
  },
  structureLabel: {
    fontSize: 10,
    marginBottom: 2,
  },
  structureValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  keyAspectItem: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  keyAspectHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  keyAspectName: {
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
  },
  keyAspectBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  keyAspectBadgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  keyAspectMeaning: {
    fontSize: 13,
    lineHeight: 19,
  },
  keyAspectWhy: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 6,
    fontStyle: 'italic',
  },
  enhancedAspectItem: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    marginBottom: 8,
  },
  pressureCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 4,
  },
  pressureMainStatement: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 10,
  },
  pressureSubStatement: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  reflectionCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginTop: 8,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  // KEY ASPECT DYNAMICS styles
  aspectDynamicsSection: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginTop: 4,
  },
  aspectDynamicsTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  aspectDynamicsSubtitle: {
    fontSize: 12,
    marginBottom: 16,
  },
  aspectDynamicsList: {
    gap: 12,
  },
  aspectDynamicRow: {
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  aspectDynamicHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  aspectDynamicLabel: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  aspectDynamicTag: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginLeft: 8,
  },
  aspectDynamicTagText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  aspectDynamicSummary: {
    fontSize: 13,
    lineHeight: 19,
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
    gap: 8,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },
});

export default AstrologyAtAGlanceTab;
