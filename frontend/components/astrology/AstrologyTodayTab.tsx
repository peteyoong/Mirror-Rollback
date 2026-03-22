// ============================================
// ASTROLOGY TODAY TAB
// Renders: Today/Week/Month content with Dominant Truth
// Master Astrologer v5: Narrative Collapse / One Dominant Truth
// ============================================

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

import {
  FullChartData,
  TransitHit,
  TransitWindow,
  Timeframe,
  CollapsedInsights,
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
  buildCollapsedInsights,
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
// SIGNALS SECTION COMPONENT (Now "Evidence" when dominant truth exists)
// ============================================

interface SignalsSectionProps {
  transits: TransitHit[];
  expanded: boolean;
  onToggle: () => void;
  theme: any;
  label?: string;
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

const SignalsSection: React.FC<SignalsSectionProps> = ({ transits, expanded, onToggle, theme, label }) => {
  if (!transits || transits.length === 0) return null;

  const displayLabel = label || 'What this is based on';

  return (
    <>
      <TouchableOpacity
        style={[styles.signalsToggle, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
        onPress={onToggle}
        activeOpacity={0.7}
      >
        <Text style={[styles.signalsToggleText, { color: theme.textSecondary }]}>
          {displayLabel} {expanded ? '▴' : '▾'}
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
  onSwitchToTimeline?: () => void;
}

// ============================================
// TIMELINE PHASE DETECTION
// ============================================

interface CurrentPhase {
  name: string;
  dateRange: string;
  summary: string;
  isPrimary: boolean;
  id: string;
}

function getCurrentTimelinePhase(): CurrentPhase | null {
  const now = new Date();
  const currentMonth = now.getMonth(); // 0-11
  const currentYear = now.getFullYear();
  
  // Q1: Jan-Mar (months 0-2)
  if (currentMonth >= 0 && currentMonth <= 2) {
    return {
      id: 'q1',
      name: 'Recognition',
      dateRange: `Jan – Mar ${currentYear}`,
      summary: 'The year\'s dominant tension is beginning to show itself in small, easy-to-dismiss moments.',
      isPrimary: false,
    };
  }
  
  // Q2: Apr-Jun (months 3-5)
  if (currentMonth >= 3 && currentMonth <= 5) {
    return {
      id: 'q2',
      name: 'Confrontation',
      dateRange: `Apr – Jun ${currentYear}`,
      summary: 'What you\'ve been tolerating becomes harder to keep calling "manageable."',
      isPrimary: true,
    };
  }
  
  // Q3: Jul-Sep (months 6-8)
  if (currentMonth >= 6 && currentMonth <= 8) {
    return {
      id: 'q3',
      name: 'The Crossroads',
      dateRange: `Jul – Sep ${currentYear}`,
      summary: 'Two versions of your direction become visible—the question is which one you\'ll commit to.',
      isPrimary: true,
    };
  }
  
  // Q4: Oct-Dec (months 9-11)
  if (currentMonth >= 9 && currentMonth <= 11) {
    return {
      id: 'q4',
      name: 'Integration',
      dateRange: `Oct – Dec ${currentYear}`,
      summary: 'The year\'s lessons are settling—either as earned clarity or recognition of what needs another cycle.',
      isPrimary: false,
    };
  }
  
  return null;
}

function getTimelineLinkingLine(phase: CurrentPhase | null, altitude: Timeframe): string | null {
  if (!phase) return null;
  
  const phaseName = phase.name;
  
  if (altitude === 'today') {
    if (phase.isPrimary) {
      return `This isn't just today—this is part of your ${phaseName} phase.`;
    }
    return `This moment is connected to a larger ${phaseName.toLowerCase()} happening this quarter.`;
  }
  
  if (altitude === 'week') {
    return `This week sits inside your ${phaseName} phase.`;
  }
  
  if (altitude === 'month') {
    return `This month is where your ${phaseName} phase becomes more visible.`;
  }
  
  return null;
}

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyTodayTab: React.FC<AstrologyTodayTabProps> = ({
  fullChartData,
  theme,
  onOpenChat,
  onReflect,
  onSwitchToTimeline,
}) => {
  const [activeAltitude, setActiveAltitude] = useState<Timeframe>('today');
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  // Get current timeline phase
  const currentPhase = getCurrentTimelinePhase();
  const timelineLinkingLine = getTimelineLinkingLine(currentPhase, activeAltitude);

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

  // DOMINANT TRUTH (Master Astrologer v5)
  const collapsedInsights = buildCollapsedInsights(fullChartData, lifeChapterAnalysis, patternAnalysis, activeAltitude);
  const hasDominantTruth = collapsedInsights.dominantTruth !== null && collapsedInsights.narrative !== null;

  // Get content based on timeframe (fallback if no dominant truth)
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

      {/* TIMELINE CONTEXT STRIP - Connects Today to larger arc */}
      {currentPhase && onSwitchToTimeline && (
        <TouchableOpacity
          style={styles.timelineContextStrip}
          onPress={onSwitchToTimeline}
          activeOpacity={0.7}
        >
          <View style={styles.timelineContextLeft}>
            <Text style={[styles.timelineContextPhase, { color: theme.textSecondary }]}>
              {currentPhase.isPrimary ? '⭐ ' : ''}{currentPhase.name}
            </Text>
            <Text style={[styles.timelineContextDate, { color: theme.textTertiary }]}>
              {currentPhase.dateRange}
            </Text>
          </View>
          <Text style={[styles.timelineContextArrow, { color: theme.textTertiary }]}>→</Text>
        </TouchableOpacity>
      )}

      {/* DOMINANT TRUTH CARD - Master Astrologer v5 */}
      {hasDominantTruth && collapsedInsights.narrative ? (
        <View style={[styles.dominantTruthCard, { backgroundColor: theme.surface, borderColor: theme.accent + '40' }]}>
          {/* Headline */}
          <Text style={[styles.dominantTruthHeadline, { color: theme.text }]}>
            {collapsedInsights.narrative.headline}
          </Text>
          
          {/* Recognition Line */}
          {collapsedInsights.narrative.recognitionLine && (
            <Text style={[styles.recognitionLine, { color: theme.accent }]}>
              {collapsedInsights.narrative.recognitionLine}
            </Text>
          )}
          
          {/* Core Truth */}
          <Text style={[styles.coreTruthText, { color: theme.text }]}>
            {collapsedInsights.narrative.coreTruth}
          </Text>
          
          {/* Timeline Linking Line - Micro context */}
          {timelineLinkingLine && (
            <Text style={[styles.timelineLinkingLine, { color: theme.textTertiary }]}>
              {timelineLinkingLine}
            </Text>
          )}
          
          {/* Where This Shows Up */}
          <View style={[styles.whereShowsUp, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
            <Text style={[styles.whereShowsUpLabel, { color: theme.textTertiary }]}>WHERE THIS SHOWS UP</Text>
            <Text style={[styles.whereShowsUpText, { color: theme.textSecondary }]}>
              {collapsedInsights.narrative.whereThisShowsUp}
            </Text>
          </View>
          
          {/* What Goes Wrong */}
          <View style={[styles.whatGoesWrong, { backgroundColor: '#FF634708', borderColor: '#FF634720' }]}>
            <Text style={[styles.whatGoesWrongLabel, { color: '#FF6347' }]}>WHAT GOES WRONG</Text>
            <Text style={[styles.whatGoesWrongText, { color: theme.text }]}>
              {collapsedInsights.narrative.whatGoesWrong}
            </Text>
          </View>
          
          {/* Question */}
          <View style={[styles.questionContainer, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
            <Text style={[styles.questionText, { color: theme.text }]}>
              {collapsedInsights.narrative.question}
            </Text>
          </View>
          
          {/* Reflect Button */}
          <TouchableOpacity
            style={[styles.reflectButton, { backgroundColor: theme.accent }]}
            onPress={() => onReflect(collapsedInsights.narrative?.question || question)}
          >
            <Text style={[styles.reflectButtonText, { color: theme.background }]}>Reflect on this</Text>
          </TouchableOpacity>
          
          {/* Timeframe Context */}
          <Text style={[styles.timeframeContext, { color: theme.textTertiary }]}>
            {collapsedInsights.narrative.timeframeContext}
          </Text>
          
          {/* Evidence Collapsed */}
          {collapsedInsights.suppressedSignalCount > 0 && (
            <Text style={[styles.evidenceNote, { color: theme.textTertiary }]}>
              Based on {collapsedInsights.surfacedSignalCount + collapsedInsights.suppressedSignalCount} active signals ({collapsedInsights.suppressedSignalCount} supporting)
            </Text>
          )}
        </View>
      ) : (
        /* FALLBACK: Original structure when no dominant truth */
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
            {lifeChapterContextLine ? (
              <Text style={[styles.contextLine, { color: theme.accent, fontWeight: '500', fontStyle: 'italic' }]}>
                ↳ {lifeChapterContextLine}
              </Text>
            ) : null}
          </View>
        </View>
      )}

      {/* COMPRESSED: WHAT TO NOTICE + WHAT TO AVOID - Only show if no dominant truth */}
      {!hasDominantTruth && (
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
      )}

      {/* Additional feelings/mistakes if present - Only show if no dominant truth */}
      {!hasDominantTruth && (feelings.length > 1 || mistakes.length > 1) && (
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

      {/* Reflection Question - Only show if no dominant truth */}
      {!hasDominantTruth && (
        <View style={[styles.reflectionCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.reflectionLabel, { color: theme.accent }]}>A QUESTION</Text>
          <Text style={[styles.reflectionText, { color: theme.text }]}>{question}</Text>
          <TouchableOpacity
            style={[styles.fallbackReflectButton, { borderColor: theme.accent }]}
            onPress={() => onReflect(question)}
        >
          <Text style={[styles.fallbackReflectButtonText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
      )}

      {/* Signals Section - Now labeled as "Evidence" when dominant truth exists */}
      <SignalsSection 
        transits={transits}
        expanded={signalsExpanded}
        onToggle={() => setSignalsExpanded(!signalsExpanded)}
        theme={theme}
        label={hasDominantTruth ? "SUPPORTING EVIDENCE" : undefined}
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
  fallbackReflectButton: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
  },
  fallbackReflectButtonText: {
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
  // DOMINANT TRUTH STYLES (Master Astrologer v5)
  dominantTruthCard: {
    borderRadius: 14,
    padding: 18,
    borderWidth: 1.5,
  },
  dominantTruthHeadline: {
    fontSize: 19,
    fontWeight: '600',
    lineHeight: 26,
    marginBottom: 8,
  },
  recognitionLine: {
    fontSize: 13,
    fontWeight: '500',
    fontStyle: 'italic',
    marginBottom: 12,
  },
  coreTruthText: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 16,
  },
  whereShowsUp: {
    borderRadius: 10,
    padding: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  whereShowsUpLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  whereShowsUpText: {
    fontSize: 13,
    lineHeight: 19,
  },
  whatGoesWrong: {
    borderRadius: 10,
    padding: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  whatGoesWrongLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  whatGoesWrongText: {
    fontSize: 13,
    lineHeight: 19,
  },
  questionContainer: {
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    marginBottom: 14,
  },
  questionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  reflectButton: {
    alignSelf: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
    marginBottom: 14,
  },
  reflectButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  timeframeContext: {
    fontSize: 11,
    textAlign: 'center',
    marginBottom: 4,
  },
  evidenceNote: {
    fontSize: 10,
    textAlign: 'center',
    fontStyle: 'italic',
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
  // TIMELINE CONTEXT STRIP STYLES
  timelineContextStrip: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 10,
    borderRadius: 8,
    backgroundColor: 'transparent',
  },
  timelineContextLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  timelineContextPhase: {
    fontSize: 12,
    fontWeight: '500',
  },
  timelineContextDate: {
    fontSize: 11,
  },
  timelineContextArrow: {
    fontSize: 12,
  },
  timelineLinkingLine: {
    fontSize: 12,
    fontStyle: 'italic',
    marginBottom: 14,
    marginTop: -4,
  },
});

export default AstrologyTodayTab;
