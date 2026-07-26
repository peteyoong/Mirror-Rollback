/**
 * LifelinePatternSynthesisCard
 * 
 * Displays an LLM-generated pattern synthesis of the user's lifeline events.
 * Shows recurring themes, life arcs, emotional patterns, and event clusters.
 * Uses Mirror language for observational, non-predictive insights.
 * 
 * Only shown when user has 5+ lifeline events.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

interface MajorEvent {
  title: string;
  year: number | null;
  impact: number;
  category: string | null;
}

interface ClusterPeriod {
  years: string;
  event_count: number;
  events: string[];
  description: string;
}

interface PatternArc {
  arc: string;
  events_involved: string[];
  years: string;
}

interface YearRange {
  start: number;
  end: number;
  span: number;
}

interface LifelinePatternSynthesis {
  success: boolean;
  has_synthesis: boolean;
  event_count: number;
  minimum_required?: number;
  message?: string;
  error?: string;
  
  // Synthesis data (when has_synthesis is true)
  major_turning_points?: number;
  major_events?: MajorEvent[];
  pattern_arcs?: PatternArc[];
  recurring_themes?: string[];
  cluster_periods?: ClusterPeriod[];
  emotional_pattern?: string;
  life_pattern_summary?: string;
  reflection_question?: string;
  year_range?: YearRange;
}

interface Props {
  userId: string;
  eventCount: number;
}

const MINIMUM_EVENTS = 5;

// Theme icon mapping
const THEME_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  growth: 'trending-up-outline',
  transition: 'swap-horizontal-outline',
  career: 'briefcase-outline',
  relationships: 'heart-outline',
  family: 'people-outline',
  identity: 'person-outline',
  health: 'fitness-outline',
  loss: 'cloud-outline',
  expansion: 'expand-outline',
  healing: 'leaf-outline',
  ambition: 'rocket-outline',
  crisis: 'alert-circle-outline',
  reinvention: 'refresh-outline',
  leadership: 'star-outline',
  breakthrough: 'flash-outline',
  pressure: 'thermometer-outline',
};

export default function LifelinePatternSynthesisCard({ userId, eventCount }: Props) {
  const { theme } = useTheme();
  
  const [synthesis, setSynthesis] = useState<LifelinePatternSynthesis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Only fetch if we have enough events
  useEffect(() => {
    if (eventCount >= MINIMUM_EVENTS && userId) {
      loadSynthesis();
    }
  }, [userId, eventCount]);
  
  const loadSynthesis = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get<LifelinePatternSynthesis>(`/lifeline/${userId}/synthesis`);
      if (response.data.success) {
        setSynthesis(response.data);
      } else {
        setError(response.data.error || 'Unable to generate synthesis');
      }
    } catch (err: any) {
      console.error('[LifelineSynthesis] Load error:', err);
      setError('Unable to load pattern synthesis');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Don't render if not enough events
  if (eventCount < MINIMUM_EVENTS) {
    return null;
  }
  
  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Analyzing your patterns...
          </Text>
        </View>
      </View>
    );
  }
  
  // Error state
  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.header}>
          <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}15` }]}>
            <Ionicons name="analytics-outline" size={18} color={theme.accent} />
          </View>
          <Text style={[styles.title, { color: theme.text }]}>Pattern Synthesis</Text>
        </View>
        <Text style={[styles.errorText, { color: theme.textTertiary }]}>{error}</Text>
        <TouchableOpacity onPress={loadSynthesis}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Try again</Text>
        </TouchableOpacity>
      </View>
    );
  }
  
  // No synthesis available
  if (!synthesis || !synthesis.has_synthesis) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.header}>
          <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}15` }]}>
            <Ionicons name="analytics-outline" size={18} color={theme.accent} />
          </View>
          <Text style={[styles.title, { color: theme.text }]}>Pattern Synthesis</Text>
        </View>
        <Text style={[styles.messageText, { color: theme.textSecondary }]}>
          {synthesis?.message || 'Add more turning points to reveal patterns in your timeline.'}
        </Text>
      </View>
    );
  }
  
  // Main render with synthesis data
  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <TouchableOpacity 
        style={styles.header}
        onPress={() => setIsExpanded(!isExpanded)}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}15` }]}>
            <Ionicons name="analytics-outline" size={18} color={theme.accent} />
          </View>
          <View>
            <Text style={[styles.title, { color: theme.text }]}>Pattern Synthesis</Text>
            {synthesis.year_range && (
              <Text style={[styles.subtitle, { color: theme.textTertiary }]}>
                {synthesis.year_range.span} years of your story
              </Text>
            )}
          </View>
        </View>
        <Ionicons 
          name={isExpanded ? 'chevron-up' : 'chevron-down'} 
          size={20} 
          color={theme.textTertiary} 
        />
      </TouchableOpacity>
      
      {/* Life Pattern Summary - Always visible */}
      {synthesis.life_pattern_summary && (
        <View style={styles.summarySection}>
          <Text style={[styles.summaryText, { color: theme.textSecondary }]}>
            {synthesis.life_pattern_summary}
          </Text>
        </View>
      )}
      
      {/* Recurring Themes - Always visible */}
      {synthesis.recurring_themes && synthesis.recurring_themes.length > 0 && (
        <View style={styles.themesSection}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            Recurring Threads
          </Text>
          <View style={styles.themeTags}>
            {synthesis.recurring_themes.slice(0, 5).map((themeText, index) => {
              const icon = THEME_ICONS[themeText] || 'ellipse-outline';
              return (
                <View 
                  key={`${themeText}-${index}`} 
                  style={[styles.themeTag, { backgroundColor: theme.background }]}
                >
                  <Ionicons name={icon} size={12} color={theme.accent} />
                  <Text style={[styles.themeTagText, { color: theme.text }]}>
                    {themeText.charAt(0).toUpperCase() + themeText.slice(1)}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>
      )}
      
      {/* Expanded content */}
      {isExpanded && (
        <View style={styles.expandedContent}>
          {/* Emotional Pattern */}
          {synthesis.emotional_pattern && (
            <View style={[styles.detailSection, { borderTopColor: theme.border }]}>
              <View style={styles.detailHeader}>
                <Ionicons name="pulse-outline" size={16} color={theme.accent} />
                <Text style={[styles.detailLabel, { color: theme.text }]}>Emotional Arc</Text>
              </View>
              <Text style={[styles.detailText, { color: theme.textSecondary }]}>
                {synthesis.emotional_pattern}
              </Text>
            </View>
          )}
          
          {/* Cluster Periods */}
          {synthesis.cluster_periods && synthesis.cluster_periods.length > 0 && (
            <View style={[styles.detailSection, { borderTopColor: theme.border }]}>
              <View style={styles.detailHeader}>
                <Ionicons name="layers-outline" size={16} color={theme.accent} />
                <Text style={[styles.detailLabel, { color: theme.text }]}>Concentrated Periods</Text>
              </View>
              {synthesis.cluster_periods.map((cluster, index) => (
                <View key={`cluster-${index}`} style={styles.clusterItem}>
                  <Text style={[styles.clusterYears, { color: theme.text }]}>
                    {cluster.years}
                  </Text>
                  <Text style={[styles.clusterDesc, { color: theme.textSecondary }]}>
                    {cluster.event_count} significant moments
                  </Text>
                </View>
              ))}
            </View>
          )}
          
          {/* Major Turning Points */}
          {synthesis.major_events && synthesis.major_events.length > 0 && (
            <View style={[styles.detailSection, { borderTopColor: theme.border }]}>
              <View style={styles.detailHeader}>
                <Ionicons name="flag-outline" size={16} color={theme.accent} />
                <Text style={[styles.detailLabel, { color: theme.text }]}>
                  Major Turning Points ({synthesis.major_turning_points})
                </Text>
              </View>
              {synthesis.major_events.slice(0, 4).map((event, index) => (
                <View key={`major-${index}`} style={styles.majorEventItem}>
                  <View style={styles.majorEventDot}>
                    <View style={[styles.dot, { backgroundColor: theme.accent }]} />
                  </View>
                  <View style={styles.majorEventContent}>
                    <Text style={[styles.majorEventTitle, { color: theme.text }]}>
                      {event.title}
                    </Text>
                    <Text style={[styles.majorEventMeta, { color: theme.textTertiary }]}>
                      {event.year || 'Year unknown'} • Impact: {event.impact}/10
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
      
      {/* Reflection Question */}
      {synthesis.reflection_question && (
        <View style={[styles.reflectionSection, { borderTopColor: theme.border }]}>
          <Ionicons name="chatbubble-ellipses-outline" size={14} color={theme.textTertiary} />
          <Text style={[styles.reflectionText, { color: theme.textTertiary }]}>
            {synthesis.reflection_question}
          </Text>
        </View>
      )}
      
      {/* Footer */}
      <Text style={[styles.footerNote, { color: theme.textTertiary }]}>
        Patterns are observations, not predictions.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 8,
  },
  loadingText: {
    fontSize: 14,
  },
  errorText: {
    fontSize: 14,
    marginBottom: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  messageText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 15,
    fontWeight: '500',
    letterSpacing: -0.2,
  },
  subtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  summarySection: {
    marginBottom: 14,
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 22,
  },
  themesSection: {
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  themeTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  themeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 14,
  },
  themeTagText: {
    fontSize: 12,
    fontWeight: '500',
  },
  expandedContent: {
    marginTop: 4,
  },
  detailSection: {
    paddingTop: 14,
    marginTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  detailHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  detailLabel: {
    fontSize: 13,
    fontWeight: '500',
  },
  detailText: {
    fontSize: 14,
    lineHeight: 21,
  },
  clusterItem: {
    marginBottom: 8,
  },
  clusterYears: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 2,
  },
  clusterDesc: {
    fontSize: 13,
  },
  majorEventItem: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  majorEventDot: {
    width: 20,
    paddingTop: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  majorEventContent: {
    flex: 1,
  },
  majorEventTitle: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 2,
  },
  majorEventMeta: {
    fontSize: 12,
  },
  reflectionSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    paddingTop: 14,
    marginTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  reflectionText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  footerNote: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 14,
    textAlign: 'center',
  },
});
