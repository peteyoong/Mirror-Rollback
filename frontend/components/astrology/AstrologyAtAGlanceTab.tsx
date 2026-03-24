// ============================================
// ASTROLOGY AT A GLANCE TAB
// A true snapshot page: fast, clear, scannable in under 5 seconds
// 5 core sections only: Big 3, Chart Spine, Life Arenas, Developmental Pressure, Current Chapter
// ============================================

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

import {
  FullChartData,
  CorePlacements,
  LifeArena,
} from '../../services/astrology/astrologyTypes';

import {
  HOUSE_MEANINGS,
  getMainLifeArenas,
  buildAspectPatternAnalysis,
  buildLifeChapterAnalysis,
  buildLifeChapterNarrative,
} from '../../services/astrology/astrologyInterpreter';

import {
  getHeroDescriptor,
  getChartSpine,
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
// MAIN COMPONENT
// ============================================

const AstrologyAtAGlanceTab: React.FC<AstrologyAtAGlanceTabProps> = ({
  placements,
  fullChartData,
  theme,
  onOpenChat,
}) => {
  // DEFENSIVE GUARD: Ensure placements exists
  const safePlacements = placements && typeof placements === 'object' ? placements : {};
  
  const sun = safePlacements.sun || 'Unknown';
  const moon = safePlacements.moon || 'Unknown';
  const asc = safePlacements.ascendant || 'Unknown';
  
  // Empty state
  if (sun === 'Unknown' && moon === 'Unknown' && asc === 'Unknown') {
    return (
      <View style={styles.emptyState}>
        <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
          Your chart snapshot is loading.
        </Text>
      </View>
    );
  }

  // DEFENSIVE GUARD: Safe fullChartData
  const safeFullChartData = fullChartData && typeof fullChartData === 'object' ? fullChartData : null;

  // ============================================
  // SECTION 1: BIG 3 - Hero descriptor (1 line max)
  // ============================================
  const heroDescriptor = getHeroDescriptor(sun, moon, asc);
  // Compress to max 80 chars
  const compressedDescriptor = heroDescriptor.length > 80 
    ? heroDescriptor.substring(0, 77) + '...' 
    : heroDescriptor;

  // ============================================
  // SECTION 2: CHART SPINE - 3 lines max
  // ============================================
  const rawChartSpine = getChartSpine(safePlacements);
  const chartSpine = Array.isArray(rawChartSpine) ? rawChartSpine.slice(0, 3) : [];

  // ============================================
  // SECTION 3: MAIN LIFE ARENAS - top 2-3 only
  // ============================================
  const rawMainArenas = getMainLifeArenas(safeFullChartData);
  const mainArenas: LifeArena[] = Array.isArray(rawMainArenas) ? rawMainArenas.slice(0, 3) : [];

  // ============================================
  // SECTION 4: DEVELOPMENTAL PRESSURE - top 2 only (Saturn + Node)
  // ============================================
  const saturnHouse = safePlacements.saturn_house;
  const northNodeHouse = safePlacements.north_node_house;

  // ============================================
  // SECTION 5: CURRENT CHAPTER / RIGHT NOW
  // ============================================
  const rawPatternAnalysis = buildAspectPatternAnalysis(safeFullChartData);
  const patternAnalysis = rawPatternAnalysis && typeof rawPatternAnalysis === 'object'
    ? rawPatternAnalysis
    : { howPressureBuilds: { hasSignificantPattern: false, mainStatement: '' } };
  
  const rawChapterAnalysis = buildLifeChapterAnalysis(safeFullChartData);
  const chapterAnalysis = rawChapterAnalysis && typeof rawChapterAnalysis === 'object'
    ? rawChapterAnalysis
    : { hasActiveChapter: false, primaryChapter: null };
  
  const chapterNarrative = chapterAnalysis.primaryChapter 
    ? buildLifeChapterNarrative(chapterAnalysis.primaryChapter, patternAnalysis)
    : null;

  return (
    <View style={styles.container}>
      
      {/* ============================================ */}
      {/* SECTION 1: BIG 3 / CORE TEMPERAMENT */}
      {/* ============================================ */}
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
        <Text style={[styles.heroDescriptor, { color: theme.textSecondary }]} numberOfLines={1}>
          {cleanText(compressedDescriptor)}
        </Text>
      </View>

      {/* ============================================ */}
      {/* SECTION 2: CHART SPINE */}
      {/* What runs through the chart */}
      {/* ============================================ */}
      {chartSpine.length > 0 && (
        <View style={[styles.spineCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.accent }]}>CHART SPINE</Text>
          {chartSpine.map((statement, i) => (
            <Text key={i} style={[styles.spineStatement, { color: theme.text }]}>
              {statement}
            </Text>
          ))}
        </View>
      )}

      {/* ============================================ */}
      {/* SECTION 3: MAIN LIFE ARENAS */}
      {/* Where life hits hardest */}
      {/* ============================================ */}
      {mainArenas.length > 0 && (
        <View style={[styles.arenasCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.accent }]}>WHERE LIFE TRAINS YOU</Text>
          {mainArenas.map((arena, i) => (
            <View key={i} style={styles.arenaItem}>
              <Text style={[styles.arenaRank, { color: theme.accent }]}>{i + 1}</Text>
              <View style={styles.arenaContent}>
                <Text style={[styles.arenaLabel, { color: theme.text }]}>{arena.label}</Text>
                <Text style={[styles.arenaExplanation, { color: theme.textSecondary }]} numberOfLines={2}>
                  {arena.explanation}
                </Text>
                {arena.whenIgnored && (
                  <Text style={[styles.arenaIgnored, { color: theme.textTertiary }]} numberOfLines={1}>
                    If ignored: {arena.whenIgnored}
                  </Text>
                )}
              </View>
            </View>
          ))}
        </View>
      )}

      {/* ============================================ */}
      {/* SECTION 4: DEVELOPMENTAL PRESSURE */}
      {/* What life is trying to mature - top 2 only */}
      {/* ============================================ */}
      {(saturnHouse || northNodeHouse) && (
        <View style={[styles.pressureCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.accent }]}>DEVELOPMENTAL PRESSURE</Text>
          <View style={styles.pressureGrid}>
            {saturnHouse && (
              <View style={styles.pressureItem}>
                <Text style={[styles.pressureHeader, { color: theme.textSecondary }]}>SATURN</Text>
                <Text style={[styles.pressureLabel, { color: theme.text }]}>
                  House {saturnHouse}: {HOUSE_MEANINGS[saturnHouse]?.shortLabel || 'Growth'}
                </Text>
                <Text style={[styles.pressureDesc, { color: theme.textTertiary }]} numberOfLines={2}>
                  {HOUSE_MEANINGS[saturnHouse]?.developmentalPressure || 'Maturation happens here.'}
                </Text>
              </View>
            )}
            {northNodeHouse && (
              <View style={styles.pressureItem}>
                <Text style={[styles.pressureHeader, { color: theme.textSecondary }]}>NORTH NODE</Text>
                <Text style={[styles.pressureLabel, { color: theme.text }]}>
                  House {northNodeHouse}: {HOUSE_MEANINGS[northNodeHouse]?.shortLabel || 'Growth'}
                </Text>
                <Text style={[styles.pressureDesc, { color: theme.textTertiary }]} numberOfLines={2}>
                  Growth edge—doesn't come naturally.
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* ============================================ */}
      {/* SECTION 5: CURRENT CHAPTER / RIGHT NOW */}
      {/* What is active now */}
      {/* ============================================ */}
      {chapterNarrative && chapterAnalysis.hasActiveChapter && (
        <View style={[styles.chapterCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.chapterLabel, { color: theme.accent }]}>RIGHT NOW</Text>
          <Text style={[styles.chapterTitle, { color: theme.text }]}>{chapterNarrative.chapterTitle}</Text>
          <Text style={[styles.chapterDescription, { color: theme.textSecondary }]} numberOfLines={3}>
            {chapterNarrative.coreDescription}
          </Text>
        </View>
      )}

      {/* Ask Mirror Button */}
      <TouchableOpacity
        style={[styles.askButton, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Text style={[styles.askButtonText, { color: theme.background }]}>Ask about your chart</Text>
      </TouchableOpacity>
    </View>
  );
};

// ============================================
// STYLES - Optimized for mobile scan
// ============================================

const styles = StyleSheet.create({
  container: {
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

  // SECTION 1: Big 3 Hero
  heroCard: {
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
  },
  big3Row: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 12,
  },
  big3Item: {
    alignItems: 'center',
    flex: 1,
  },
  big3Divider: {
    width: 1,
    height: 36,
    opacity: 0.3,
  },
  big3Symbol: {
    fontSize: 22,
    marginBottom: 4,
  },
  big3Sign: {
    fontSize: 15,
    fontWeight: '600',
  },
  heroDescriptor: {
    fontSize: 13,
    textAlign: 'center',
    fontStyle: 'italic',
    lineHeight: 18,
  },

  // SECTION 2: Chart Spine
  spineCard: {
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  spineStatement: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 6,
  },

  // SECTION 3: Life Arenas
  arenasCard: {
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
  },
  arenaItem: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  arenaRank: {
    fontSize: 16,
    fontWeight: '700',
    width: 24,
    marginRight: 8,
  },
  arenaContent: {
    flex: 1,
  },
  arenaLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  arenaExplanation: {
    fontSize: 13,
    lineHeight: 18,
  },
  arenaIgnored: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 3,
  },

  // SECTION 4: Developmental Pressure
  pressureCard: {
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
  },
  pressureGrid: {
    gap: 10,
  },
  pressureItem: {
    marginBottom: 4,
  },
  pressureHeader: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 3,
  },
  pressureLabel: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 2,
  },
  pressureDesc: {
    fontSize: 12,
    lineHeight: 16,
  },

  // SECTION 5: Current Chapter
  chapterCard: {
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
  },
  chapterLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  chapterTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 6,
  },
  chapterDescription: {
    fontSize: 13,
    lineHeight: 19,
  },

  // Ask Button
  askButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 4,
  },
  askButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
});

export default AstrologyAtAGlanceTab;
