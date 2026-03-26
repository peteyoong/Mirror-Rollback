/**
 * TodayPatternCard
 * Home screen keystone - Cross-Lens Synthesis
 * Shows title + 3 lines that feel like immediate recognition
 * + contextual follow-through line based on dominant source
 * + "Why this is showing up" inline expander
 * 
 * NOW WITH EXPERIENCE CONTROLS:
 * - Tone: Affects opener/closer copy
 * - Verbosity: Affects how much is shown
 * - Signal Visibility: Controls expander detail level
 * - Prompt Style: Affects the CTA copy
 * 
 * Structure:
 * - Line 1: What you're feeling / doing
 * - Line 2: The tension / contradiction  
 * - Line 3: The pattern (recognition layer)
 * - Follow-through: Contextual bridge to relevant lens
 * - Expander: Top signals driving today's pattern
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, LayoutAnimation, Platform, UIManager } from 'react-native';
import { useRouter } from 'expo-router';
import api, { getPatternSignals, PatternSignalDetail } from '../services/api';
import { useExperienceControls } from '../hooks/useExperienceControls';

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
  
  // Experience controls for personalization
  const { controls, toneTemplates, promptTemplate } = useExperienceControls();
  
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

  // Get top signals based on signal_visibility setting
  // minimal: 1 signal, standard: 3 signals, expanded: 5 signals
  const getTopSignals = () => {
    if (!signalsData?.signals) return [];
    
    const allSignals: { category: string; signal: PatternSignalDetail }[] = [];
    
    if (signalsData.signals.astrology) {
      signalsData.signals.astrology.forEach(s => allSignals.push({ category: 'Astrology', signal: s }));
    }
    if (signalsData.signals.human_design) {
      signalsData.signals.human_design.forEach(s => allSignals.push({ category: 'Human Design', signal: s }));
    }
    if (signalsData.signals.pattern_history) {
      signalsData.signals.pattern_history.forEach(s => allSignals.push({ category: 'Pattern History', signal: s }));
    }
    
    // Limit based on signal visibility preference
    const limits = { minimal: 1, standard: 3, expanded: 5 };
    const limit = limits[controls.signal_visibility] || 3;
    
    return allSignals.slice(0, limit);
  };

  // Get CTA text based on prompt_style
  const getCtaText = () => {
    const ctaMap = {
      questions: 'What does this bring up?',
      perspectives: 'Write about this',
      reassurance: 'Take a moment with this',
      action: 'What will you do with this?',
    };
    return ctaMap[controls.prompt_style] || 'Write about this';
  };

  // Get lines to show based on verbosity
  const getLinesToShow = () => {
    if (!data?.lines) return [];
    if (controls.verbosity === 'low') return data.lines.slice(0, 2);
    if (controls.verbosity === 'high') return data.lines;
    return data.lines.slice(0, 3); // medium
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
      {/* Label with tone opener */}
      <Text style={[styles.label, { color: theme.textTertiary }]}>
        {toneTemplates.pattern_opener.toUpperCase()}
      </Text>
      
      {/* Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {data?.title}
      </Text>
      
      {/* Lines - controlled by verbosity */}
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
      
      {/* Tone closer - based on tone setting */}
      <Text style={[styles.toneCloser, { color: theme.textTertiary }]}>
        {toneTemplates.pattern_closer}
      </Text>
      
      {/* Follow-through line - tappable bridge to relevant lens */}
      {data?.follow_through && (
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
          Why this is showing up
        </Text>
        <Text style={[styles.expanderArrow, { color: theme.textTertiary }]}>
          {isExpanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>
      
      {/* Expanded Signals Section */}
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
              {/* Top Signals */}
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
                    <Text style={[styles.signalMeaning, { color: theme.textSecondary }]}>
                      {item.signal.meaning}
                    </Text>
                  </View>
                ))}
              </View>
              
              {/* See all signals link */}
              <TouchableOpacity
                style={styles.seeAllLink}
                onPress={handleSeeAllSignals}
                activeOpacity={0.7}
              >
                <Text style={[styles.seeAllText, { color: theme.accent }]}>
                  See all signals →
                </Text>
              </TouchableOpacity>
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
      
      {/* CTA - Personalized based on prompt_style */}
      <TouchableOpacity
        style={styles.ctaContainer}
        onPress={handleReflect}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>{getCtaText()}</Text>
        <Text style={[styles.ctaArrow, { color: theme.textTertiary }]}>→</Text>
      </TouchableOpacity>
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
});
