/**
 * PatternArchetypeCard.tsx
 * 
 * Displays the user's primary pattern archetype with:
 * - Icon and headline
 * - Summary narrative
 * - Evidence-based explanation ("Why Mirror sees this")
 * - Reflection question
 * - Current relevance
 * - Task 76: Conversation entry point
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
import { useAppStore } from '../../store';
import api from '../../services/api';
import PatternConversationPanel, { ExploreWithMirrorButton } from '../PatternConversationPanel';
import { InsightCardFooter } from '../InsightCardFooter';

// Types
interface ArchetypeNarrative {
  headline: string;
  icon: string;
  summary: string;
  contrast: string;
  short_description: string;
  how_this_shows_up: string[];
  why_this_pattern: string[];
  current_expression: string;
  reflection_question: string;
  evidence_sources: {
    lifeline: number;
    patterns: number;
    journal: number;
    lunar: number;
  };
}

interface Archetype {
  id: string;
  name: string;
  icon: string;
  score: number;
  evidence_count: number;
  narrative: ArchetypeNarrative;
}

interface ArchetypeResponse {
  success: boolean;
  user_id: string;
  confidence: number;
  primary_archetype?: Archetype;
  secondary_archetype?: Archetype;
  all_scores?: Array<{ id: string; name: string; score: number }>;
}

// Colors
const COLORS = {
  moonlight: '#E8DED1',
  silver: '#A8B2C0',
  cardBg: 'rgba(168, 178, 192, 0.08)',
  accent: '#9B8AC4',
  accentLight: 'rgba(155, 138, 196, 0.15)',
};

export default function PatternArchetypeCard() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  
  const [data, setData] = useState<ArchetypeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showConversation, setShowConversation] = useState(false);

  useEffect(() => {
    if (user?.id) {
      fetchArchetype();
    }
  }, [user?.id]);

  const fetchArchetype = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<ArchetypeResponse>(`/pattern-archetype/${user.id}`);
      setData(response.data);
    } catch (err: any) {
      console.error('[PatternArchetypeCard] Error:', err);
      setError(err.message || 'Failed to load archetype');
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={COLORS.moonlight} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Analyzing your patterns...
        </Text>
      </View>
    );
  }

  // Error or no data state
  if (error || !data || !data.primary_archetype) {
    return null; // Silently fail - don't show card if no archetype
  }

  const archetype = data.primary_archetype;
  const narrative = archetype.narrative;
  const confidence = data.confidence;

  // Confidence label
  const getConfidenceLabel = () => {
    if (confidence >= 0.7) return 'Strong pattern';
    if (confidence >= 0.5) return 'Emerging pattern';
    return 'Early signal';
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header Row */}
      <View style={styles.headerRow}>
        <View style={styles.iconContainer}>
          <Text style={styles.archetypeIcon}>{archetype.icon}</Text>
        </View>
        <View style={styles.headerText}>
          <Text style={[styles.headline, { color: theme.text }]}>
            {narrative.headline}
          </Text>
          <Text style={[styles.subheadline, { color: theme.textTertiary }]}>
            {narrative.short_description} • {getConfidenceLabel()}
          </Text>
        </View>
      </View>

      {/* Summary + Contrast */}
      <Text style={[styles.summary, { color: theme.textSecondary }]}>
        {narrative.summary}
      </Text>
      {narrative.contrast && (
        <Text style={[styles.contrast, { color: theme.text }]}>
          {narrative.contrast}
        </Text>
      )}

      {/* How This Shows Up - Always visible */}
      {narrative.how_this_shows_up && narrative.how_this_shows_up.length > 0 && (
        <View style={styles.showsUpSection}>
          {narrative.how_this_shows_up.map((item, index) => (
            <Text key={index} style={[styles.showsUpItem, { color: theme.textSecondary }]}>
              {item}
            </Text>
          ))}
        </View>
      )}

      {/* Expandable Section */}
      <TouchableOpacity
        style={styles.expandToggle}
        onPress={() => setIsExpanded(!isExpanded)}
      >
        <Text style={[styles.expandToggleText, { color: COLORS.accent }]}>
          {isExpanded ? 'Show less' : 'Why Mirror sees this'}
        </Text>
        <Ionicons
          name={isExpanded ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={COLORS.accent}
        />
      </TouchableOpacity>

      {isExpanded && (
        <View style={styles.expandedContent}>
          {/* Evidence List */}
          <View style={styles.evidenceSection}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              EVIDENCE
            </Text>
            {narrative.why_this_pattern.map((reason, index) => (
              <View key={index} style={styles.evidenceItem}>
                <Text style={[styles.evidenceBullet, { color: COLORS.accent }]}>•</Text>
                <Text style={[styles.evidenceText, { color: theme.textSecondary }]}>
                  {reason}
                </Text>
              </View>
            ))}
          </View>

          {/* Source Breakdown */}
          <View style={styles.sourcesRow}>
            {narrative.evidence_sources.lifeline > 0 && (
              <View style={[styles.sourceBadge, { backgroundColor: COLORS.cardBg }]}>
                <Text style={[styles.sourceBadgeText, { color: theme.textSecondary }]}>
                  Lifeline ({narrative.evidence_sources.lifeline})
                </Text>
              </View>
            )}
            {narrative.evidence_sources.patterns > 0 && (
              <View style={[styles.sourceBadge, { backgroundColor: COLORS.cardBg }]}>
                <Text style={[styles.sourceBadgeText, { color: theme.textSecondary }]}>
                  Patterns ({narrative.evidence_sources.patterns})
                </Text>
              </View>
            )}
            {narrative.evidence_sources.lunar > 0 && (
              <View style={[styles.sourceBadge, { backgroundColor: COLORS.cardBg }]}>
                <Text style={[styles.sourceBadgeText, { color: theme.textSecondary }]}>
                  Lunar ({narrative.evidence_sources.lunar})
                </Text>
              </View>
            )}
            {narrative.evidence_sources.journal > 0 && (
              <View style={[styles.sourceBadge, { backgroundColor: COLORS.cardBg }]}>
                <Text style={[styles.sourceBadgeText, { color: theme.textSecondary }]}>
                  Journal ({narrative.evidence_sources.journal})
                </Text>
              </View>
            )}
          </View>

          {/* Current Expression */}
          <View style={styles.currentSection}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              RIGHT NOW
            </Text>
            <Text style={[styles.currentText, { color: theme.textSecondary }]}>
              {narrative.current_expression}
            </Text>
          </View>
        </View>
      )}

      {/* Unified Insight Card Footer (Resonate + Reflect) */}
      <InsightCardFooter
        source={{
          lens: 'patterns',
          type: 'pattern_archetype',
          name: archetype.name,
          value: narrative.summary,
          id: `pattern_archetype_${archetype.id}`,
        }}
        patternSignature={`pattern_archetype_${archetype.id}`}
        context="patterns_archetype"
        prompt={narrative.reflection_question}
        showBorder={true}
        borderColor={theme.border}
      />

      {/* Task 76: Conversation Entry Point - Now secondary action */}
      <View style={styles.secondaryActionContainer}>
        <ExploreWithMirrorButton onPress={() => setShowConversation(true)} />
      </View>

      {/* Secondary Archetype Hint */}
      {data.secondary_archetype && data.secondary_archetype.score >= 0.6 && (
        <View style={styles.secondaryHint}>
          <Text style={[styles.secondaryText, { color: theme.textTertiary }]}>
            Also present: {data.secondary_archetype.icon} {data.secondary_archetype.name}
          </Text>
        </View>
      )}

      {/* Task 76: Conversation Panel */}
      <PatternConversationPanel 
        visible={showConversation} 
        onClose={() => setShowConversation(false)} 
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  loadingText: {
    textAlign: 'center',
    fontSize: 13,
    marginTop: 8,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.cardBg,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  archetypeIcon: {
    fontSize: 24,
  },
  headerText: {
    flex: 1,
  },
  headline: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 2,
  },
  subheadline: {
    fontSize: 13,
  },
  summary: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  expandToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 12,
  },
  expandToggleText: {
    fontSize: 13,
    fontWeight: '600',
  },
  expandedContent: {
    marginBottom: 12,
  },
  evidenceSection: {
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  evidenceItem: {
    flexDirection: 'row',
    marginBottom: 6,
    paddingLeft: 4,
  },
  evidenceBullet: {
    fontSize: 14,
    marginRight: 8,
    lineHeight: 20,
  },
  evidenceText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  sourcesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  sourceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  sourceBadgeText: {
    fontSize: 12,
  },
  currentSection: {
    marginBottom: 8,
  },
  currentText: {
    fontSize: 14,
    lineHeight: 20,
  },
  reflectionBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 12,
    borderRadius: 12,
    marginTop: 4,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
    fontStyle: 'italic',
  },
  secondaryHint: {
    marginTop: 12,
    alignItems: 'center',
  },
  secondaryText: {
    fontSize: 12,
  },
  secondaryActionContainer: {
    marginTop: 12,
  },
});
