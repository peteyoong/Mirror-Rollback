/**
 * CrossLensSynthesis Component
 * 
 * Displays cross-lens synthesis insights connecting Lifeline, Patterns, and BaZi.
 * Available in two modes:
 * - Teaser: Short version for homepage
 * - Full: Complete version for Patterns page
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';

// =============================================================================
// INTERFACES
// =============================================================================

export interface SynthesisInsight {
  type: 'repetition' | 'tension' | 'operating_style' | 'question';
  text: string;
}

export interface SynthesisData {
  has_synthesis: boolean;
  headline: string;
  summary: string;
  signals_used: string[];
  insights: SynthesisInsight[];
  low_data_hint?: string;
}

export interface SynthesisTeaserData {
  show_teaser: boolean;
  headline: string;
  summary: string;
  signals_used: string[];
  cta_text?: string;
}

interface FullSynthesisProps {
  synthesis: SynthesisData | null;
  isLoading?: boolean;
}

interface SynthesisTeaserProps {
  synthesis: SynthesisTeaserData | null;
  isLoading?: boolean;
}

// =============================================================================
// SIGNAL ICONS
// =============================================================================

const SIGNAL_ICONS: Record<string, { icon: keyof typeof Ionicons.glyphMap; label: string }> = {
  lifeline: { icon: 'time-outline', label: 'Lifeline' },
  pattern_engine: { icon: 'git-network-outline', label: 'Patterns' },
  bazi: { icon: 'apps-outline', label: 'BaZi' },
};

// =============================================================================
// INSIGHT TYPE ICONS
// =============================================================================

const INSIGHT_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  repetition: 'repeat-outline',
  tension: 'git-merge-outline',
  operating_style: 'compass-outline',
  question: 'help-circle-outline',
};

// =============================================================================
// HOMEPAGE TEASER COMPONENT
// =============================================================================

export function SynthesisTeaser({ synthesis, isLoading }: SynthesisTeaserProps) {
  const { theme } = useTheme();
  const router = useRouter();
  
  if (isLoading) {
    return (
      <View style={[styles.teaserContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.teaserHeader}>
          <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}12` }]}>
            <Ionicons name="sparkles-outline" size={16} color={theme.accent} />
          </View>
          <Text style={[styles.teaserTitle, { color: theme.text }]}>Cross-Lens Synthesis</Text>
        </View>
        <View style={[styles.loadingBar, { backgroundColor: theme.border }]} />
        <View style={[styles.loadingBar, { backgroundColor: theme.border, width: '60%' }]} />
      </View>
    );
  }
  
  if (!synthesis || !synthesis.show_teaser) {
    return null;
  }
  
  const handlePress = () => {
    // Navigate to Pattern Lens for deeper exploration
    router.push('/pattern-lens');
  };
  
  return (
    <TouchableOpacity
      style={[styles.teaserContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      {/* Header */}
      <View style={styles.teaserHeader}>
        <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}12` }]}>
          <Ionicons name="sparkles-outline" size={16} color={theme.accent} />
        </View>
        <Text style={[styles.teaserTitle, { color: theme.text }]}>{synthesis.headline}</Text>
        <Ionicons name="chevron-forward" size={16} color={theme.textTertiary} />
      </View>
      
      {/* Summary */}
      <Text style={[styles.teaserSummary, { color: theme.textSecondary }]} numberOfLines={2}>
        {synthesis.summary}
      </Text>
      
      {/* Signal badges */}
      {synthesis.signals_used.length > 0 && (
        <View style={styles.signalBadges}>
          {synthesis.signals_used.map((signal) => {
            const info = SIGNAL_ICONS[signal];
            if (!info) return null;
            return (
              <View
                key={signal}
                style={[styles.signalBadge, { backgroundColor: theme.background }]}
              >
                <Ionicons name={info.icon} size={12} color={theme.textTertiary} />
                <Text style={[styles.signalBadgeText, { color: theme.textTertiary }]}>
                  {info.label}
                </Text>
              </View>
            );
          })}
        </View>
      )}
    </TouchableOpacity>
  );
}

// =============================================================================
// FULL SYNTHESIS COMPONENT (FOR PATTERNS PAGE)
// =============================================================================

export function FullSynthesis({ synthesis, isLoading }: FullSynthesisProps) {
  const { theme } = useTheme();
  
  if (isLoading) {
    return (
      <View style={[styles.fullContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.fullHeader}>
          <View style={[styles.iconContainerLarge, { backgroundColor: `${theme.accent}12` }]}>
            <Ionicons name="sparkles-outline" size={20} color={theme.accent} />
          </View>
          <View style={styles.headerText}>
            <Text style={[styles.fullTitle, { color: theme.text }]}>Cross-Lens Synthesis</Text>
            <Text style={[styles.fullSubtitle, { color: theme.textTertiary }]}>Loading...</Text>
          </View>
        </View>
      </View>
    );
  }
  
  if (!synthesis) {
    return null;
  }
  
  // Low data state
  if (!synthesis.has_synthesis) {
    return (
      <View style={[styles.fullContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.fullHeader}>
          <View style={[styles.iconContainerLarge, { backgroundColor: `${theme.accent}12` }]}>
            <Ionicons name="sparkles-outline" size={20} color={theme.accent} />
          </View>
          <View style={styles.headerText}>
            <Text style={[styles.fullTitle, { color: theme.text }]}>{synthesis.headline}</Text>
          </View>
        </View>
        <Text style={[styles.lowDataMessage, { color: theme.textSecondary }]}>
          {synthesis.summary}
        </Text>
        {synthesis.low_data_hint && (
          <Text style={[styles.lowDataHint, { color: theme.textTertiary }]}>
            {synthesis.low_data_hint}
          </Text>
        )}
      </View>
    );
  }
  
  return (
    <View style={[styles.fullContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.fullHeader}>
        <View style={[styles.iconContainerLarge, { backgroundColor: `${theme.accent}12` }]}>
          <Ionicons name="sparkles-outline" size={20} color={theme.accent} />
        </View>
        <View style={styles.headerText}>
          <Text style={[styles.fullTitle, { color: theme.text }]}>{synthesis.headline}</Text>
          <Text style={[styles.fullSubtitle, { color: theme.textTertiary }]}>Cross-Lens Synthesis</Text>
        </View>
      </View>
      
      {/* Signal badges */}
      {synthesis.signals_used.length > 0 && (
        <View style={styles.signalBadgesRow}>
          <Text style={[styles.signalLabel, { color: theme.textTertiary }]}>Connecting:</Text>
          {synthesis.signals_used.map((signal) => {
            const info = SIGNAL_ICONS[signal];
            if (!info) return null;
            return (
              <View
                key={signal}
                style={[styles.signalBadgeFull, { backgroundColor: theme.background }]}
              >
                <Ionicons name={info.icon} size={14} color={theme.textSecondary} />
                <Text style={[styles.signalBadgeTextFull, { color: theme.textSecondary }]}>
                  {info.label}
                </Text>
              </View>
            );
          })}
        </View>
      )}
      
      {/* Insights */}
      <View style={styles.insightsContainer}>
        {synthesis.insights.map((insight, index) => {
          const isQuestion = insight.type === 'question';
          const icon = INSIGHT_ICONS[insight.type] || 'ellipse-outline';
          
          return (
            <View
              key={index}
              style={[
                styles.insightRow,
                isQuestion && styles.questionRow,
                isQuestion && { borderTopColor: theme.border },
              ]}
            >
              <View style={[styles.insightIcon, { backgroundColor: theme.background }]}>
                <Ionicons
                  name={icon}
                  size={14}
                  color={isQuestion ? theme.accent : theme.textSecondary}
                />
              </View>
              <Text
                style={[
                  styles.insightText,
                  { color: isQuestion ? theme.text : theme.textSecondary },
                  isQuestion && styles.questionText,
                ]}
              >
                {insight.text}
              </Text>
            </View>
          );
        })}
      </View>
      
      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        These connections are observations to explore, not fixed conclusions.
      </Text>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  // Teaser styles
  teaserContainer: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 16,
  },
  teaserHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  iconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  teaserTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  teaserSummary: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 10,
  },
  signalBadges: {
    flexDirection: 'row',
    gap: 8,
  },
  signalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  signalBadgeText: {
    fontSize: 11,
  },
  loadingBar: {
    height: 12,
    borderRadius: 6,
    marginBottom: 8,
  },
  
  // Full synthesis styles
  fullContainer: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 20,
  },
  fullHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  iconContainerLarge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  headerText: {
    flex: 1,
  },
  fullTitle: {
    fontSize: 17,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  fullSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  signalBadgesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  signalLabel: {
    fontSize: 12,
    marginRight: 4,
  },
  signalBadgeFull: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
  },
  signalBadgeTextFull: {
    fontSize: 12,
    fontWeight: '500',
  },
  insightsContainer: {
    gap: 12,
  },
  insightRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  questionRow: {
    marginTop: 12,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  insightIcon: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  questionText: {
    fontWeight: '500',
    fontStyle: 'italic',
  },
  footer: {
    fontSize: 11,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 16,
  },
  lowDataMessage: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  lowDataHint: {
    fontSize: 12,
    marginTop: 10,
  },
});

export default { SynthesisTeaser, FullSynthesis };
