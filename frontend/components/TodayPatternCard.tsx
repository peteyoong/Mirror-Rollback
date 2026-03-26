/**
 * TodayPatternCard
 * Home screen keystone - Cross-Lens Synthesis
 * 
 * NOW MODE-BASED for structural experience differentiation:
 * 
 * GROUNDING MODE:
 * - Max 2 lines
 * - 1 signal only
 * - Reassuring tone
 * - Simple language
 * - Calming CTA
 * 
 * EXPLORATORY MODE:
 * - Full content (5 lines)
 * - Multiple signals
 * - Cross-lens synthesis
 * - Open-ended reflection
 * - Question-based CTA
 * 
 * DIRECTIVE MODE:
 * - Structured output (3 lines)
 * - 2 signals + interpretation
 * - Clear language
 * - Action-oriented CTA
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, LayoutAnimation, Platform, UIManager } from 'react-native';
import { useRouter } from 'expo-router';
import api, { getPatternSignals, PatternSignalDetail } from '../services/api';
import { useExperienceControls } from '../hooks/useExperienceControls';
import { MODE_CONFIGS } from '../types/mirror-profile';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface TodayPatternData {
  title: string;
  lines: string[];
  confidence: number;
  sources: string[];
  date: string;
  cached: boolean;
  follow_through?: string;
  follow_through_route?: string;
}

interface SignalsData {
  summary: string;
  signals: {
    astrology?: PatternSignalDetail[];
    human_design?: PatternSignalDetail[];
    pattern_history?: PatternSignalDetail[];
  };
  synthesis: string;
}

interface TodayPatternCardProps {
  userId: string;
  theme: any;
  onReflect?: () => void;
}

export default function TodayPatternCard({ userId, theme, onReflect }: TodayPatternCardProps) {
  const router = useRouter();
  const [data, setData] = useState<TodayPatternData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Experience controls for personalization - MODE is the primary driver
  const { mode, modeConfig, controls } = useExperienceControls();
  
  // Expander state
  const [isExpanded, setIsExpanded] = useState(false);
  const [signalsData, setSignalsData] = useState<SignalsData | null>(null);
  const [signalsLoading, setSignalsLoading] = useState(false);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    const fetchPattern = async () => {
      try {
        setIsLoading(true);
        const response = await api.get(`/today-pattern/${userId}`);
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error('[TodayPatternCard] Error:', err);
        setError('Could not load pattern');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPattern();
  }, [userId]);

  const handleReflect = () => {
    if (onReflect) {
      onReflect();
    } else {
      router.push('/(tabs)/reflect?view=mirror');
    }
  };

  const handleFollowThrough = () => {
    if (!data?.follow_through_route) return;
    
    switch (data.follow_through_route) {
      case 'reflect':
        router.push('/(tabs)/reflect');
        break;
      case 'human_design':
        router.push('/lenses/human-design');
        break;
      case 'astrology':
        router.push('/lenses/astrology?tab=today');
        break;
      case 'enneagram':
        router.push('/lenses/enneagram');
        break;
      default:
        break;
    }
  };

  // Toggle expander and fetch signals if needed
  const handleExpandToggle = async () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    
    if (!isExpanded && !signalsData && !signalsLoading) {
      // First time expanding - fetch signals
      setSignalsLoading(true);
      try {
        const response = await getPatternSignals(userId);
        setSignalsData(response);
      } catch (err) {
        console.error('[TodayPatternCard] Error fetching signals:', err);
      } finally {
        setSignalsLoading(false);
      }
    }
    
    setIsExpanded(!isExpanded);
  };

  // Navigate to full signals page
  const handleSeeAllSignals = () => {
    router.push('/signals');
  };

  // ============================================================
  // MODE-BASED STRUCTURAL FUNCTIONS
  // ============================================================

  // Get signals based on MODE (structural change, not just count)
  const getTopSignals = () => {
    if (!signalsData?.signals) return [];
    
    const allSignals: { category: string; signal: PatternSignalDetail; showInterpretation: boolean }[] = [];
    
    if (signalsData.signals.astrology) {
      signalsData.signals.astrology.forEach(s => 
        allSignals.push({ 
          category: 'Astrology', 
          signal: s, 
          showInterpretation: modeConfig.showSignalInterpretation 
        })
      );
    }
    if (signalsData.signals.human_design) {
      signalsData.signals.human_design.forEach(s => 
        allSignals.push({ 
          category: 'Human Design', 
          signal: s, 
          showInterpretation: modeConfig.showSignalInterpretation 
        })
      );
    }
    if (signalsData.signals.pattern_history) {
      signalsData.signals.pattern_history.forEach(s => 
        allSignals.push({ 
          category: 'Pattern History', 
          signal: s, 
          showInterpretation: modeConfig.showSignalInterpretation 
        })
      );
    }
    
    // Use MODE maxSignals for structural limit
    return allSignals.slice(0, modeConfig.maxSignals);
  };

  // Get CTA text based on MODE (structural change in prompt behavior)
  const getCtaText = () => modeConfig.ctaText;

  // Get lines to show based on MODE maxLines (structural change)
  const getLinesToShow = () => {
    if (!data?.lines) return [];
    return data.lines.slice(0, modeConfig.maxLines);
  };

  // Should show cross-lens synthesis (only in exploratory mode)
  const shouldShowCrossLensSynthesis = () => {
    return mode === 'exploratory' && signalsData?.synthesis;
  };

  // Should show "See all signals" link
  const shouldShowSeeAllLink = () => {
    // Only show if we have more signals than maxSignals allows
    if (!signalsData?.signals) return false;
    const totalSignals = 
      (signalsData.signals.astrology?.length || 0) +
      (signalsData.signals.human_design?.length || 0) +
      (signalsData.signals.pattern_history?.length || 0);
    return totalSignals > modeConfig.maxSignals;
  };

  // Don't render if no data
  if (!isLoading && (!data || !data.lines || data.lines.length === 0)) {
    return null;
  }

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      {/* Label with MODE-based opener */}
      <Text style={[styles.label, { color: theme.textTertiary }]}>
        {modeConfig.patternOpener.toUpperCase()}
      </Text>
      
      {/* Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {data?.title}
      </Text>
      
      {/* Lines - controlled by MODE maxLines (structural change) */}
      <View style={styles.linesContainer}>
        {getLinesToShow().map((line, index) => (
          <Text 
            key={index} 
            style={[
              styles.line, 
              { color: index === getLinesToShow().length - 1 ? theme.text : theme.textSecondary },
              index === getLinesToShow().length - 1 && styles.lastLine
            ]}
          >
            {line}
          </Text>
        ))}
      </View>
      
      {/* MODE-based closer */}
      <Text style={[styles.toneCloser, { color: theme.textTertiary }]}>
        {modeConfig.patternCloser}
      </Text>
      
      {/* Follow-through line - only show if MODE allows cross-lens synthesis */}
      {modeConfig.showCrossLensSynthesis && data?.follow_through && (
        <TouchableOpacity
          style={styles.followThroughContainer}
          onPress={handleFollowThrough}
          activeOpacity={0.7}
          disabled={!data.follow_through_route}
        >
          <Text style={[styles.followThrough, { color: theme.textTertiary }]}>
            {data.follow_through}
            {data.follow_through_route && ' →'}
          </Text>
        </TouchableOpacity>
      )}
      
      {/* Why this is showing up - Expander */}
      <TouchableOpacity
        style={[styles.expanderToggle, { borderTopColor: theme.border }]}
        onPress={handleExpandToggle}
        activeOpacity={0.7}
      >
        <Text style={[styles.expanderToggleText, { color: theme.textSecondary }]}>
          {modeConfig.signalIntro}
        </Text>
        <Text style={[styles.expanderArrow, { color: theme.textTertiary }]}>
          {isExpanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>
      
      {/* Expanded Signals Section - MODE-based structure */}
      {isExpanded && (
        <View style={styles.expandedContent}>
          {signalsLoading ? (
            <View style={styles.signalsLoading}>
              <ActivityIndicator size="small" color={theme.textTertiary} />
              <Text style={[styles.signalsLoadingText, { color: theme.textTertiary }]}>
                Tracing signals...
              </Text>
            </View>
          ) : signalsData ? (
            <>
              {/* Top Signals - limited by MODE maxSignals */}
              <View style={styles.signalsList}>
                {getTopSignals().map((item, index) => (
                  <View 
                    key={index} 
                    style={[styles.signalItem, { borderLeftColor: theme.accent + '50' }]}
                  >
                    <Text style={[styles.signalCategory, { color: theme.textTertiary }]}>
                      {item.category}
                    </Text>
                    <Text style={[styles.signalLabel, { color: theme.text }]}>
                      {item.signal.label}
                    </Text>
                    {/* Only show meaning if MODE allows interpretation */}
                    {item.showInterpretation && (
                      <Text style={[styles.signalMeaning, { color: theme.textSecondary }]}>
                        {item.signal.meaning}
                      </Text>
                    )}
                  </View>
                ))}
              </View>
              
              {/* Cross-lens synthesis - ONLY in exploratory mode */}
              {shouldShowCrossLensSynthesis() && (
                <View style={[styles.synthesisBox, { backgroundColor: theme.accent + '10' }]}>
                  <Text style={[styles.synthesisText, { color: theme.textSecondary }]}>
                    {signalsData.synthesis}
                  </Text>
                </View>
              )}
              
              {/* See all signals link - only if more signals exist */}
              {shouldShowSeeAllLink() && (
                <TouchableOpacity
                  style={styles.seeAllLink}
                  onPress={handleSeeAllSignals}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.seeAllText, { color: theme.accent }]}>
                    See all signals →
                  </Text>
                </TouchableOpacity>
              )}
            </>
          ) : (
            <Text style={[styles.noSignalsText, { color: theme.textTertiary }]}>
              Unable to load signals
            </Text>
          )}
        </View>
      )}
      
      {/* Divider */}
      <View style={[styles.divider, { backgroundColor: theme.border }]} />
      
      {/* CTA - MODE-based action type */}
      <TouchableOpacity
        style={styles.ctaContainer}
        onPress={handleReflect}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>{getCtaText()}</Text>
        <Text style={[styles.ctaArrow, { color: theme.textTertiary }]}>→</Text>
      </TouchableOpacity>
      
      {/* DEBUG MARKER - TEMPORARY for profile audit */}
      <Text style={[styles.debugMarker, { color: theme.textTertiary }]}>
        PROFILE: {mode} / {controls.verbosity} / {modeConfig.maxLines} lines
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 24,
    marginBottom: 14,
  },
  linesContainer: {
    gap: 8,
  },
  line: {
    fontSize: 15,
    lineHeight: 22,
  },
  lastLine: {
    fontStyle: 'italic',
  },
  followThroughContainer: {
    marginTop: 12,
    paddingTop: 10,
  },
  followThrough: {
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  // Tone closer (personalized closing line)
  toneCloser: {
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
    marginTop: 14,
  },
  // Expander styles
  expanderToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 14,
    marginTop: 12,
    borderTopWidth: 1,
  },
  expanderToggleText: {
    fontSize: 13,
    fontWeight: '500',
  },
  expanderArrow: {
    fontSize: 10,
  },
  expandedContent: {
    marginTop: 14,
    paddingTop: 4,
  },
  signalsLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  signalsLoadingText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  signalsList: {
    gap: 12,
  },
  signalItem: {
    borderLeftWidth: 2,
    paddingLeft: 12,
  },
  signalCategory: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  signalLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  signalMeaning: {
    fontSize: 13,
    lineHeight: 18,
  },
  synthesisBox: {
    marginTop: 14,
    padding: 12,
    borderRadius: 8,
  },
  synthesisText: {
    fontSize: 13,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  seeAllLink: {
    marginTop: 14,
    alignItems: 'flex-end',
  },
  seeAllText: {
    fontSize: 13,
    fontWeight: '500',
  },
  noSignalsText: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: 12,
  },
  divider: {
    height: 1,
    marginVertical: 14,
  },
  ctaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '500',
  },
  ctaArrow: {
    fontSize: 16,
    fontWeight: '400',
  },
  // DEBUG MARKER - TEMPORARY
  debugMarker: {
    fontSize: 9,
    textAlign: 'center',
    marginTop: 12,
    fontFamily: 'monospace',
    opacity: 0.5,
  },
});
