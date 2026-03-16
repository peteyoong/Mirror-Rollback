/**
 * LifelinePatterns
 * 
 * Displays pattern insights generated from the user's lifeline events.
 * Shows grounded, non-deterministic observations about recurring themes,
 * emotional patterns, and time clusters.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';

export interface PatternInsight {
  type: string;
  text: string;
}

export interface LifelinePatternsData {
  has_patterns: boolean;
  low_data_message: string | null;
  insights: PatternInsight[];
}

interface Props {
  patterns: LifelinePatternsData | null;
  eventCount: number;
}

// Map insight types to icons
const INSIGHT_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  category_dominant: 'layers-outline',
  category_repeat: 'layers-outline',
  category_multiple: 'layers-outline',
  emotional_positive: 'sunny-outline',
  emotional_difficult: 'cloud-outline',
  emotional_mixed: 'git-merge-outline',
  cluster_year: 'time-outline',
  cluster_years: 'time-outline',
  cluster_age: 'person-outline',
  time_span: 'calendar-outline',
  time_single_year: 'calendar-outline',
  thematic_overlap: 'git-network-outline',
  transitions: 'swap-horizontal-outline',
  seed: 'leaf-outline',
  early_pattern: 'sparkles-outline',
  early_range: 'resize-outline',
};

export default function LifelinePatterns({ patterns, eventCount }: Props) {
  const { theme } = useTheme();
  
  // Don't show anything if no data
  if (!patterns) {
    return null;
  }
  
  // Low data state - show gentle prompt
  if (!patterns.has_patterns && patterns.low_data_message) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.header}>
          <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}12` }]}>
            <Ionicons name="sparkles-outline" size={16} color={theme.accent} />
          </View>
          <Text style={[styles.title, { color: theme.text }]}>Lifeline Patterns</Text>
        </View>
        
        <Text style={[styles.lowDataMessage, { color: theme.textSecondary }]}>
          {patterns.low_data_message}
        </Text>
        
        {eventCount > 0 && eventCount < 3 && (
          <Text style={[styles.countHint, { color: theme.textTertiary }]}>
            {3 - eventCount} more moment{3 - eventCount > 1 ? 's' : ''} to unlock patterns
          </Text>
        )}
      </View>
    );
  }
  
  // No insights to show
  if (!patterns.insights || patterns.insights.length === 0) {
    return null;
  }
  
  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}12` }]}>
          <Ionicons name="sparkles-outline" size={16} color={theme.accent} />
        </View>
        <Text style={[styles.title, { color: theme.text }]}>Lifeline Patterns</Text>
      </View>
      
      {/* Insights */}
      <View style={styles.insightsContainer}>
        {patterns.insights.map((insight, index) => {
          const iconName = INSIGHT_ICONS[insight.type] || 'ellipse-outline';
          
          return (
            <View 
              key={`${insight.type}-${index}`} 
              style={[
                styles.insightRow,
                index < patterns.insights.length - 1 && styles.insightRowBorder,
                { borderBottomColor: theme.border }
              ]}
            >
              <View style={[styles.insightIcon, { backgroundColor: theme.background }]}>
                <Ionicons name={iconName} size={14} color={theme.textSecondary} />
              </View>
              <Text style={[styles.insightText, { color: theme.textSecondary }]}>
                {insight.text}
              </Text>
            </View>
          );
        })}
      </View>
      
      {/* Footer note */}
      <Text style={[styles.footerNote, { color: theme.textTertiary }]}>
        These patterns are observations, not predictions.
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    gap: 10,
  },
  iconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  insightsContainer: {
    gap: 0,
  },
  insightRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 10,
    gap: 10,
  },
  insightRowBorder: {
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  insightIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  lowDataMessage: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  countHint: {
    fontSize: 12,
    marginTop: 10,
  },
  footerNote: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 12,
    textAlign: 'center',
  },
});
