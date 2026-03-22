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
} from '../../services/astrology/astrologyInterpreter';

import {
  getHeroDescriptor,
  getChartSpine,
  getWhereLifeKeepsWorkingOnYou,
} from '../../services/astrology/astrologyNarrative';

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
        <Text style={[styles.heroDescriptor, { color: theme.textSecondary }]}>{heroDescriptor}</Text>
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

      {/* WHAT MATTERS MOST */}
      <View style={[styles.whatMattersCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.whatMattersTitle, { color: theme.accent }]}>WHAT MATTERS MOST IN THIS CHART</Text>
        {whatMattersMost.map((item, i) => (
          <View key={i} style={styles.whatMattersItem}>
            <Text style={[styles.whatMattersRank, { color: theme.accent }]}>{item.rank}</Text>
            <View style={styles.whatMattersContent}>
              <Text style={[styles.whatMattersLabel, { color: theme.text }]}>{item.label}</Text>
              <Text style={[styles.whatMattersDescriptor, { color: theme.textTertiary }]}>{item.descriptor}</Text>
              <Text style={[styles.whatMattersForce, { color: theme.textSecondary }]}>{item.force}</Text>
            </View>
          </View>
        ))}
        {/* Aspect pattern integration in What Matters Most */}
        {patternAnalysis.dominantPattern && (
          <View style={[styles.whatMattersItem, { marginTop: 8, paddingTop: 8, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: theme.border }]}>
            <Text style={[styles.whatMattersRank, { color: theme.accent }]}>{whatMattersMost.length + 1}</Text>
            <View style={styles.whatMattersContent}>
              <Text style={[styles.whatMattersLabel, { color: theme.text }]}>
                {patternAnalysis.dominantPattern.patternType === 'pressure_triangle' ? 'Pressure Pattern' :
                 patternAnalysis.dominantPattern.patternType === 'stellium' ? 'Concentration Pattern' :
                 patternAnalysis.dominantPattern.patternType === 'opposition_axis' ? 'Tension Axis' :
                 'Structural Pattern'}
              </Text>
              <Text style={[styles.whatMattersDescriptor, { color: theme.textTertiary }]}>Chart-level organization</Text>
              <Text style={[styles.whatMattersForce, { color: theme.textSecondary }]}>
                {patternAnalysis.dominantPattern.plainLanguageSummary}
              </Text>
            </View>
          </View>
        )}
      </View>

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

      {/* KEY ASPECT DYNAMICS - UPGRADED (Part 5) */}
      {enhancedAspects.length > 0 && (
        <TouchableOpacity
          style={[styles.collapsibleSection, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
          onPress={() => setAspectsExpanded(!aspectsExpanded)}
          activeOpacity={0.7}
        >
          <View style={styles.collapsibleHeader}>
            <Text style={[styles.collapsibleTitle, { color: theme.textSecondary }]}>Key aspect dynamics</Text>
            <Text style={[styles.collapsibleIcon, { color: theme.textTertiary }]}>
              {aspectsExpanded ? '▴' : '▾'}
            </Text>
          </View>
          {!aspectsExpanded && (
            <Text style={[styles.collapsibleHint, { color: theme.textTertiary }]}>
              {enhancedAspects.length} most important aspect dynamics
            </Text>
          )}
          {aspectsExpanded && (
            <View style={styles.collapsibleContent}>
              {enhancedAspects.map((asp, i) => (
                <View key={i} style={[styles.enhancedAspectItem, { borderColor: theme.border }]}>
                  <View style={styles.keyAspectHeader}>
                    <Text style={[styles.keyAspectName, { color: theme.text }]}>{asp.aspectPair}</Text>
                    <View style={[styles.keyAspectBadge, { 
                      backgroundColor: asp.pressureType === 'flow' ? '#E8F5E9' : asp.pressureType === 'pressure' ? '#FFEBEE' : '#FFF3E0'
                    }]}>
                      <Text style={[styles.keyAspectBadgeText, { 
                        color: asp.pressureType === 'flow' ? '#2E7D32' : asp.pressureType === 'pressure' ? '#C62828' : '#EF6C00'
                      }]}>{asp.pressureType}</Text>
                    </View>
                  </View>
                  <Text style={[styles.keyAspectMeaning, { color: theme.text }]}>{asp.humanSummary}</Text>
                  {asp.whyItMattersHere && (
                    <Text style={[styles.keyAspectWhy, { color: theme.textSecondary }]}>
                      {asp.whyItMattersHere}
                    </Text>
                  )}
                </View>
              ))}
            </View>
          )}
        </TouchableOpacity>
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
