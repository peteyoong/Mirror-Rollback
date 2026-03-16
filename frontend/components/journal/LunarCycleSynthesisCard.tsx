/**
 * Lunar Cycle Synthesis Card - Task 55
 * 
 * Displays an observational synthesis of the Reflector's journal entries
 * across a lunar cycle. Shows patterns, shifts, and notable moments.
 * 
 * This component appears before the cycle completion modal to help
 * the user see their process before deciding to close or continue.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface SynthesisData {
  success: boolean;
  has_synthesis: boolean;
  consideration_topic?: string;
  entry_count?: number;
  days_observed?: number;
  consistent_theme?: string;
  top_themes?: string[];
  perspective_shifts?: string;
  clarity_trend?: string;
  clarity_direction?: string;
  notable_gate_text?: string;
  notable_gates?: Array<{
    gate: number;
    title: string;
    entry_count: number;
  }>;
  reflection_summary?: string;
  suggested_question?: string;
  message?: string;
}

interface LunarCycleSynthesisCardProps {
  userId: string;
  considerationId: string;
  onSynthesisLoaded?: (synthesis: SynthesisData | null) => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  glow: 'rgba(192, 200, 212, 0.12)',
  dimGlow: 'rgba(192, 200, 212, 0.08)',
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function LunarCycleSynthesisCard({
  userId,
  considerationId,
  onSynthesisLoaded,
}: LunarCycleSynthesisCardProps) {
  const { theme } = useTheme();
  const [synthesis, setSynthesis] = useState<SynthesisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    const fetchSynthesis = async () => {
      if (!userId || !considerationId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await api.get(
          `/lunar-journal/${userId}/synthesis/${considerationId}`
        );

        if (response.data?.success && response.data?.has_synthesis) {
          setSynthesis(response.data);
          onSynthesisLoaded?.(response.data);
        } else {
          setSynthesis(null);
          onSynthesisLoaded?.(null);
        }
        setError(null);
      } catch (err) {
        console.error('[LunarSynthesis] Error:', err);
        setError('Unable to generate synthesis');
        setSynthesis(null);
        onSynthesisLoaded?.(null);
      } finally {
        setLoading(false);
      }
    };

    fetchSynthesis();
  }, [userId, considerationId, onSynthesisLoaded]);

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={LUNAR_COLORS.moonlight} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Generating synthesis...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !synthesis || !synthesis.has_synthesis) {
    return null; // Don't show anything if there's no synthesis
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <TouchableOpacity 
        style={styles.header}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <Text style={styles.headerIcon}>✦</Text>
          <Text style={[styles.headerTitle, { color: LUNAR_COLORS.moonlight }]}>
            LUNAR CYCLE SYNTHESIS
          </Text>
        </View>
        <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
          {expanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <>
          {/* Stats Row */}
          <View style={[styles.statsRow, { borderBottomColor: theme.border }]}>
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: theme.text }]}>
                {synthesis.entry_count}
              </Text>
              <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
                entries
              </Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: theme.text }]}>
                {synthesis.days_observed}
              </Text>
              <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
                days observed
              </Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: theme.text }]}>
                {synthesis.notable_gates?.length || 0}
              </Text>
              <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
                gates touched
              </Text>
            </View>
          </View>

          {/* Synthesis Sections */}
          <View style={styles.synthesisContent}>
            {/* What stayed consistent */}
            {synthesis.consistent_theme && (
              <View style={styles.section}>
                <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                  WHAT STAYED CONSISTENT
                </Text>
                <Text style={[styles.sectionText, { color: theme.text }]}>
                  {synthesis.consistent_theme}
                </Text>
              </View>
            )}

            {/* What shifted */}
            {synthesis.perspective_shifts && (
              <View style={styles.section}>
                <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                  WHAT SHIFTED ACROSS THE CYCLE
                </Text>
                <Text style={[styles.sectionText, { color: theme.text }]}>
                  {synthesis.perspective_shifts}
                </Text>
              </View>
            )}

            {/* Clarity trend */}
            {synthesis.clarity_trend && (
              <View style={styles.section}>
                <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                  CLARITY
                </Text>
                <Text style={[styles.sectionText, { color: theme.text }]}>
                  {synthesis.clarity_trend}
                </Text>
              </View>
            )}

            {/* Notable gates */}
            {synthesis.notable_gates && synthesis.notable_gates.length > 0 && (
              <View style={styles.section}>
                <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                  NOTABLE GATES
                </Text>
                <Text style={[styles.sectionText, { color: theme.text }]}>
                  {synthesis.notable_gate_text}
                </Text>
                <View style={styles.gatesRow}>
                  {synthesis.notable_gates.map((gate) => (
                    <View 
                      key={gate.gate}
                      style={[styles.gateBadge, { backgroundColor: LUNAR_COLORS.glow }]}
                    >
                      <Text style={[styles.gateBadgeNumber, { color: LUNAR_COLORS.moonlight }]}>
                        {gate.gate}
                      </Text>
                      <Text style={[styles.gateBadgeTitle, { color: theme.textSecondary }]}>
                        {gate.title}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Summary */}
            {synthesis.reflection_summary && (
              <View style={[styles.summarySection, { backgroundColor: LUNAR_COLORS.dimGlow }]}>
                <Text style={[styles.summaryText, { color: theme.text }]}>
                  {synthesis.reflection_summary}
                </Text>
              </View>
            )}

            {/* Reflection Question */}
            {synthesis.suggested_question && (
              <View style={[styles.questionSection, { borderTopColor: theme.border }]}>
                <Text style={[styles.questionLabel, { color: LUNAR_COLORS.silver }]}>
                  REFLECTION
                </Text>
                <Text style={[styles.questionText, { color: theme.textSecondary }]}>
                  {synthesis.suggested_question}
                </Text>
              </View>
            )}
          </View>
        </>
      )}
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    overflow: 'hidden',
  },
  loadingContainer: {
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerIcon: {
    fontSize: 16,
    color: LUNAR_COLORS.moonlight,
  },
  headerTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
  },
  expandIcon: {
    fontSize: 10,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    marginHorizontal: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
  },
  statLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(192, 200, 212, 0.2)',
  },
  synthesisContent: {
    padding: 16,
    paddingTop: 12,
  },
  section: {
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  gatesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  gateBadge: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  gateBadgeNumber: {
    fontSize: 14,
    fontWeight: '600',
  },
  gateBadgeTitle: {
    fontSize: 10,
    marginTop: 2,
  },
  summarySection: {
    padding: 14,
    borderRadius: 10,
    marginBottom: 16,
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  questionSection: {
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  questionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  questionText: {
    fontSize: 15,
    lineHeight: 23,
    fontStyle: 'italic',
  },
});

export type { SynthesisData, LunarCycleSynthesisCardProps };
