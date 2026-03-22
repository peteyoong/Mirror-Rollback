// ============================================
// ASTROLOGY TODAY TAB
// Renders: Today/Week/Month content, Question, Signals Section
// ============================================

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

import {
  FullChartData,
  TransitHit,
  TransitWindow,
  Timeframe,
} from '../../services/astrology/astrologyTypes';

import {
  HOUSE_MEANINGS,
  getChartRuler,
  getDominantHouses,
  isChartRulerActivated,
  detectChapterTransits,
  detectRepeatPatterns,
  detectPersonalRelevance,
  getActivatedHouses,
  buildRulershipChains,
  detectThemeConcentration,
  prioritizeTransits,
  buildAspectPatternAnalysis,
  isPatternActivatedByTransit,
  buildLifeChapterAnalysis,
  getChapterContextLine,
} from '../../services/astrology/astrologyInterpreter';

import {
  getDailyEnergySynthesis,
  getWhatThisMayFeelLike,
  getMistakeToWatch,
  getReflectionQuestion,
  getLifeAreaContext,
  getMoonPhaseContext,
  getPersonalRelevanceLine,
  getChartRulerContextLine,
  getDominantHouseRulerLine,
  getRulershipChainLine,
  getChapterLine,
  getRepeatPatternLine,
  getThemeCollapseLineIfApplicable,
} from '../../services/astrology/astrologyNarrative';

// ============================================
// SIGNALS SECTION COMPONENT
// ============================================

interface SignalsSectionProps {
  transits: TransitHit[];
  expanded: boolean;
  onToggle: () => void;
  theme: any;
}

const getAspectSymbol = (aspectType: string): string => {
  const symbols: { [key: string]: string } = {
    'conjunction': '☌',
    'opposition': '☍',
    'trine': '△',
    'square': '□',
    'sextile': '⚹'
  };
  return symbols[aspectType] || '•';
};

const SignalsSection: React.FC<SignalsSectionProps> = ({ transits, expanded, onToggle, theme }) => {
  if (!transits || transits.length === 0) return null;

  return (
    <>
      <TouchableOpacity
        style={[styles.signalsToggle, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
        onPress={onToggle}
        activeOpacity={0.7}
      >
        <Text style={[styles.signalsToggleText, { color: theme.textSecondary }]}>
          What this is based on {expanded ? '▴' : '▾'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <View style={[styles.signalsContainer, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
          {/* Timing Pressures */}
          <View style={styles.signalsSection}>
            <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>TIMING PRESSURES</Text>
            <View style={styles.signalsCompactList}>
              {transits.slice(0, 4).map((hit, index) => (
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

          {/* What's Being Touched */}
          {transits.length > 0 && (
            <View style={styles.signalsSection}>
              <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>WHAT'S BEING TOUCHED</Text>
              <View style={styles.signalsChipsRow}>
                {[...new Set(transits.slice(0, 6).map(t => t.natal_point))].map((point, i) => (
                  <View key={i} style={[styles.signalsChip, { backgroundColor: theme.accent + '10' }]}>
                    <Text style={[styles.signalsChipText, { color: theme.accent }]}>{point}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Where This Is Landing */}
          <View style={styles.signalsSection}>
            <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>WHERE THIS IS LANDING</Text>
            <View style={styles.signalsLifeAreas}>
              {transits.slice(0, 4).map((hit, i) => {
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
                    • {hit.natal_point}: {shortAreaMap[hit.natal_point] || hit.natal_point}
                  </Text>
                );
              })}
            </View>
          </View>
        </View>
      )}
    </>
  );
};

// ============================================
// PROPS INTERFACE
// ============================================

interface AstrologyTodayTabProps {
  fullChartData: FullChartData | null;
  theme: any;
  onOpenChat: () => void;
  onReflect: (question: string) => void;
}

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyTodayTab: React.FC<AstrologyTodayTabProps> = ({
  fullChartData,
  theme,
  onOpenChat,
  onReflect,
}) => {
  const [activeAltitude, setActiveAltitude] = useState<Timeframe>('today');
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  // Get transit window based on timeframe
  const getTransitWindow = (): TransitWindow | null => {
    if (!fullChartData?.transits?.windows) return null;
    
    switch (activeAltitude) {
      case 'today': return fullChartData.transits.windows.today;
      case 'week': return fullChartData.transits.windows.this_week;
      case 'month': return fullChartData.transits.windows.this_month;
      default: return fullChartData.transits.windows.today;
    }
  };

  const currentWindow = getTransitWindow();
  const transits = currentWindow?.strongest_hits || [];

  // Get activated houses for context
  const activatedHouses = getActivatedHouses(transits);

  // Generate all context lines from services
  const energySynthesis = getDailyEnergySynthesis(transits, activeAltitude);
  const lifeAreaContext = getLifeAreaContext(transits);
  const moonPhaseContext = getMoonPhaseContext(transits, fullChartData);
  
  // Personal relevance
  const personalRelevance = detectPersonalRelevance(fullChartData, transits);
  const personalRelevanceLine = getPersonalRelevanceLine(personalRelevance, activatedHouses, fullChartData);
  
  // Chart ruler context
  const chartRulerLine = getChartRulerContextLine(fullChartData, transits);
  
  // Rulership chain context
  const rulershipChainLine = getRulershipChainLine(fullChartData, transits);
  
  // Dominant house ruler context
  const dominantHouseRulerLine = getDominantHouseRulerLine(fullChartData, transits);
  
  // Theme collapse
  const themeCollapseLine = getThemeCollapseLineIfApplicable(fullChartData, transits);
  
  // Repeat patterns
  const repeatPatternLine = getRepeatPatternLine(fullChartData, transits);
  
  // Chapter awareness (for month view)
  const chapterInfo = detectChapterTransits(transits);
  const chapterLine = activeAltitude === 'month' ? getChapterLine(chapterInfo) : '';

  // Pattern activation check (Part 8)
  const patternAnalysis = buildAspectPatternAnalysis(fullChartData);
  const patternActivation = isPatternActivatedByTransit(patternAnalysis, transits);

  // Life Chapter context (Master Astrologer v4)
  const lifeChapterAnalysis = buildLifeChapterAnalysis(fullChartData);
  const lifeChapterContextLine = getChapterContextLine(lifeChapterAnalysis, activeAltitude);

  // Get content based on timeframe
  const feelings = getWhatThisMayFeelLike(transits, activeAltitude).slice(0, 3);
  const mistakes = getMistakeToWatch(transits, activeAltitude).slice(0, 3);
  const question = getReflectionQuestion(transits, activeAltitude);

  return (
    <View style={styles.todayContainer}>
      {/* Altitude Selector */}
      <View style={[styles.altitudeSelector, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
        <TouchableOpacity
          style={[styles.altitudeButton, activeAltitude === 'today' && { backgroundColor: theme.surface }]}
          onPress={() => setActiveAltitude('today')}
        >
          <Text style={[styles.altitudeText, { color: activeAltitude === 'today' ? theme.text : theme.textTertiary }]}>
            Today
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.altitudeButton, activeAltitude === 'week' && { backgroundColor: theme.surface }]}
          onPress={() => setActiveAltitude('week')}
        >
          <Text style={[styles.altitudeText, { color: activeAltitude === 'week' ? theme.text : theme.textTertiary }]}>
            This Week
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.altitudeButton, activeAltitude === 'month' && { backgroundColor: theme.surface }]}
          onPress={() => setActiveAltitude('month')}
        >
          <Text style={[styles.altitudeText, { color: activeAltitude === 'month' ? theme.text : theme.textTertiary }]}>
            This Month
          </Text>
        </TouchableOpacity>
      </View>

      {/* DAILY ENERGY - Core Reading Card */}
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
        
        {/* Context Lines */}
        <View style={styles.contextLinesContainer}>
          {lifeAreaContext ? (
            <Text style={[styles.contextLine, { color: theme.textTertiary }]}>
              ↳ {lifeAreaContext}
            </Text>
          ) : null}
          {moonPhaseContext ? (
            <Text style={[styles.contextLine, { color: theme.textTertiary }]}>
              ↳ {moonPhaseContext}
            </Text>
          ) : null}
          {personalRelevanceLine ? (
            <Text style={[styles.contextLine, { color: theme.textTertiary }]}>
              ↳ {personalRelevanceLine}
            </Text>
          ) : null}
          {chartRulerLine ? (
            <Text style={[styles.contextLine, { color: theme.accent, fontWeight: '500' }]}>
              ↳ {chartRulerLine}
            </Text>
          ) : null}
          {rulershipChainLine ? (
            <Text style={[styles.contextLine, { color: theme.textSecondary, fontWeight: '500' }]}>
              ↳ {rulershipChainLine}
            </Text>
          ) : null}
          {dominantHouseRulerLine ? (
            <Text style={[styles.contextLine, { color: theme.textSecondary }]}>
              ↳ {dominantHouseRulerLine}
            </Text>
          ) : null}
          {themeCollapseLine ? (
            <Text style={[styles.contextLine, { color: theme.accent, fontStyle: 'italic' }]}>
              ↳ {themeCollapseLine}
            </Text>
          ) : null}
          {repeatPatternLine && !themeCollapseLine ? (
            <Text style={[styles.contextLine, { color: theme.textSecondary, fontStyle: 'italic' }]}>
              ↳ {repeatPatternLine}
            </Text>
          ) : null}
          {chapterLine ? (
            <Text style={[styles.contextLine, { color: theme.textSecondary, fontStyle: 'italic' }]}>
              ↳ {chapterLine}
            </Text>
          ) : null}
          {patternActivation.activated ? (
            <Text style={[styles.contextLine, { color: theme.accent, fontWeight: '500' }]}>
              ↳ {patternActivation.activationLine}
            </Text>
          ) : null}
          {lifeChapterContextLine ? (
            <Text style={[styles.contextLine, { color: theme.accent, fontWeight: '500', fontStyle: 'italic' }]}>
              ↳ {lifeChapterContextLine}
            </Text>
          ) : null}
        </View>
      </View>

      {/* COMPRESSED: WHAT TO NOTICE + WHAT TO AVOID */}
      <View style={styles.compressedInsightsRow}>
        {feelings.length > 0 && (
          <View style={[styles.compressedInsightCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.compressedInsightTitle, { color: theme.textSecondary }]}>MAY FEEL LIKE</Text>
            <Text style={[styles.compressedInsightText, { color: theme.text }]}>
              {feelings[0]}
            </Text>
          </View>
        )}
        
        {mistakes.length > 0 && (
          <View style={[styles.compressedInsightCard, { backgroundColor: '#FF634705', borderColor: '#FF634715' }]}>
            <Text style={[styles.compressedInsightTitle, { color: '#FF6347' }]}>WATCH FOR</Text>
            <Text style={[styles.compressedInsightText, { color: theme.text }]}>
              {mistakes[0]}
            </Text>
          </View>
        )}
      </View>

      {/* Additional feelings/mistakes if present */}
      {(feelings.length > 1 || mistakes.length > 1) && (
        <View style={[styles.additionalInsightsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          {feelings.length > 1 && (
            <View style={styles.additionalSection}>
              <Text style={[styles.additionalTitle, { color: theme.textTertiary }]}>ALSO NOTICE</Text>
              {feelings.slice(1).map((feeling, i) => (
                <Text key={i} style={[styles.additionalBullet, { color: theme.textSecondary }]}>• {feeling}</Text>
              ))}
            </View>
          )}
          {mistakes.length > 1 && (
            <View style={styles.additionalSection}>
              <Text style={[styles.additionalTitle, { color: '#FF6347' }]}>ALSO WATCH</Text>
              {mistakes.slice(1).map((mistake, i) => (
                <Text key={i} style={[styles.additionalBullet, { color: theme.textSecondary }]}>• {mistake}</Text>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Reflection Question */}
      <View style={[styles.reflectionCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
        <Text style={[styles.reflectionLabel, { color: theme.accent }]}>A QUESTION</Text>
        <Text style={[styles.reflectionText, { color: theme.text }]}>{question}</Text>
        <TouchableOpacity
          style={[styles.reflectButton, { borderColor: theme.accent }]}
          onPress={() => onReflect(question)}
        >
          <Text style={[styles.reflectButtonText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>

      {/* Signals Section */}
      <SignalsSection 
        transits={transits}
        expanded={signalsExpanded}
        onToggle={() => setSignalsExpanded(!signalsExpanded)}
        theme={theme}
      />

      {/* Ask Mirror Button */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
        <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about today</Text>
      </TouchableOpacity>
    </View>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  todayContainer: {
    padding: 16,
    gap: 12,
  },
  altitudeSelector: {
    flexDirection: 'row',
    borderRadius: 10,
    padding: 4,
    borderWidth: 1,
    marginBottom: 4,
  },
  altitudeButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  altitudeText: {
    fontSize: 13,
    fontWeight: '500',
  },
  dailyEnergyCard: {
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderLeftWidth: 3,
  },
  dailyEnergyLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  dailyEnergyHeadline: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 10,
    lineHeight: 26,
  },
  dailyEnergyBody: {
    fontSize: 15,
    lineHeight: 23,
  },
  contextLinesContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(0,0,0,0.08)',
    gap: 4,
  },
  contextLine: {
    fontSize: 12,
    lineHeight: 18,
  },
  compressedInsightsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  compressedInsightCard: {
    flex: 1,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
  },
  compressedInsightTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  compressedInsightText: {
    fontSize: 13,
    lineHeight: 19,
  },
  additionalInsightsCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  additionalSection: {
    marginBottom: 10,
  },
  additionalTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  additionalBullet: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 2,
  },
  reflectionCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
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
    marginBottom: 12,
  },
  reflectButton: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
  },
  reflectButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  signalsToggle: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  signalsToggleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  signalsContainer: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  signalsSection: {
    marginBottom: 14,
  },
  signalsSectionTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  signalsCompactList: {
    gap: 4,
  },
  signalsTransitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  signalsChipText: {
    fontSize: 11,
    fontWeight: '500',
  },
  signalsLifeAreas: {
    gap: 2,
  },
  signalsLifeAreaText: {
    fontSize: 11,
    lineHeight: 16,
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 4,
    gap: 8,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },
});

export default AstrologyTodayTab;
