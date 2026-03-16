/**
 * Lunar Cycle Synthesis Card - Task 69: Mirror Cycle Intelligence Engine
 * 
 * Displays structured insights from the Reflector's journal entries
 * across a lunar cycle. Shows patterns, emotional signals, and notable gates.
 * 
 * IMPORTANT: This should only appear AFTER cycle completion, not during observation.
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
// TYPES - Task 69
// =============================================================================

interface EmotionalSignals {
  dominant_tone: 'excitement_dominant' | 'hesitation_dominant' | 'mixed' | 'neutral';
  excitement_count: number;
  hesitation_count: number;
  summary: string;
}

interface EmotionalThemes {
  excitement_themes: string[];
  hesitation_themes: string[];
}

interface StrongestGate {
  gate: number;
  title: string;
  insight: string;
  entry_count: number;
  longest_entry_preview?: string;
}

interface DecisionMomentum {
  state: 'strong_positive' | 'positive' | 'mixed' | 'unclear' | 'resistant';
  label: string;
  description: string;
  score: number; // 0-5 for visualization
}

interface SynthesisData {
  success: boolean;
  has_synthesis: boolean;
  is_low_data?: boolean;
  consideration_topic?: string;
  cycle_completed?: boolean;
  
  // Cycle Overview
  entry_count?: number;
  days_observed?: number;
  gates_touched?: number;
  
  // Emotional Analysis
  emotional_signals?: EmotionalSignals;
  emotional_themes?: EmotionalThemes;
  
  // Gate Analysis
  strongest_gate?: StrongestGate;
  gate_significance_text?: string;
  
  // Pattern Insight
  pattern_insight?: string;
  top_themes?: string[];
  
  // Decision Momentum (Task 70)
  momentum?: DecisionMomentum;
  
  // Reflection
  reflection_question?: string;
  
  // Low data scenario
  low_data_message?: string;
  suggestion?: string;
  
  // Legacy fields for backward compatibility
  consistent_theme?: string;
  message?: string;
}

interface LunarCycleSynthesisCardProps {
  userId: string;
  considerationId: string;
  cycleCompleted?: boolean;
  onSynthesisLoaded?: (synthesis: SynthesisData | null) => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  glow: 'rgba(192, 200, 212, 0.12)',
  dimGlow: 'rgba(192, 200, 212, 0.06)',
  excitement: 'rgba(129, 199, 132, 0.15)',
  hesitation: 'rgba(239, 154, 154, 0.15)',
};

// =============================================================================
// COMPONENT - Task 69
// =============================================================================

export default function LunarCycleSynthesisCard({
  userId,
  considerationId,
  cycleCompleted = false,
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
            Generating insights...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !synthesis || !synthesis.has_synthesis) {
    return null;
  }

  // Low data scenario
  if (synthesis.is_low_data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity 
          style={styles.header}
          onPress={() => setExpanded(!expanded)}
          activeOpacity={0.7}
        >
          <View style={styles.headerLeft}>
            <Text style={styles.headerIcon}>✦</Text>
            <Text style={[styles.headerTitle, { color: LUNAR_COLORS.moonlight }]}>
              OBSERVATION SUMMARY
            </Text>
          </View>
          <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
            {expanded ? '▲' : '▼'}
          </Text>
        </TouchableOpacity>

        {expanded && (
          <View style={styles.lowDataContent}>
            <Text style={[styles.lowDataMessage, { color: theme.text }]}>
              {synthesis.low_data_message}
            </Text>
            {synthesis.suggestion && (
              <View style={[styles.suggestionBox, { backgroundColor: LUNAR_COLORS.dimGlow }]}>
                <Text style={[styles.suggestionText, { color: theme.textSecondary }]}>
                  💡 {synthesis.suggestion}
                </Text>
              </View>
            )}
          </View>
        )}
      </View>
    );
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
        <View style={styles.synthesisContent}>
          {/* ═══════════════════════════════════════════════════════════════
              SECTION 1: CYCLE OVERVIEW
              ═══════════════════════════════════════════════════════════════ */}
          <View style={[styles.overviewSection, { borderBottomColor: theme.border }]}>
            <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
              CYCLE OVERVIEW
            </Text>
            <Text style={[styles.overviewText, { color: theme.text }]}>
              You observed this decision across:
            </Text>
            <View style={styles.overviewStats}>
              <View style={styles.overviewStat}>
                <Text style={[styles.overviewStatValue, { color: theme.text }]}>
                  {synthesis.entry_count}
                </Text>
                <Text style={[styles.overviewStatLabel, { color: theme.textTertiary }]}>
                  reflections
                </Text>
              </View>
              <View style={[styles.overviewStatDivider, { backgroundColor: LUNAR_COLORS.dimGlow }]} />
              <View style={styles.overviewStat}>
                <Text style={[styles.overviewStatValue, { color: theme.text }]}>
                  {synthesis.days_observed}
                </Text>
                <Text style={[styles.overviewStatLabel, { color: theme.textTertiary }]}>
                  days
                </Text>
              </View>
              <View style={[styles.overviewStatDivider, { backgroundColor: LUNAR_COLORS.dimGlow }]} />
              <View style={styles.overviewStat}>
                <Text style={[styles.overviewStatValue, { color: theme.text }]}>
                  {synthesis.gates_touched}
                </Text>
                <Text style={[styles.overviewStatLabel, { color: theme.textTertiary }]}>
                  lunar gates
                </Text>
              </View>
            </View>
          </View>

          {/* ═══════════════════════════════════════════════════════════════
              SECTION 2: EMOTIONAL SIGNALS
              ═══════════════════════════════════════════════════════════════ */}
          {synthesis.emotional_signals && (
            <View style={[styles.section, { borderBottomColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                EMOTIONAL SIGNALS
              </Text>
              <Text style={[styles.sectionText, { color: theme.text }]}>
                {synthesis.emotional_signals.summary}
              </Text>
              
              {/* Excitement Themes */}
              {synthesis.emotional_themes?.excitement_themes && synthesis.emotional_themes.excitement_themes.length > 0 && (
                <View style={styles.themeRow}>
                  <View style={[styles.themeBadge, { backgroundColor: LUNAR_COLORS.excitement }]}>
                    <Text style={[styles.themeBadgeLabel, { color: '#4CAF50' }]}>Excitement themes</Text>
                  </View>
                  <Text style={[styles.themeList, { color: theme.textSecondary }]}>
                    {synthesis.emotional_themes.excitement_themes.join(', ')}
                  </Text>
                </View>
              )}
              
              {/* Hesitation Themes */}
              {synthesis.emotional_themes?.hesitation_themes && synthesis.emotional_themes.hesitation_themes.length > 0 && (
                <View style={styles.themeRow}>
                  <View style={[styles.themeBadge, { backgroundColor: LUNAR_COLORS.hesitation }]}>
                    <Text style={[styles.themeBadgeLabel, { color: '#EF5350' }]}>Hesitation themes</Text>
                  </View>
                  <Text style={[styles.themeList, { color: theme.textSecondary }]}>
                    {synthesis.emotional_themes.hesitation_themes.join(', ')}
                  </Text>
                </View>
              )}
            </View>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              SECTION 3: NOTABLE GATE
              ═══════════════════════════════════════════════════════════════ */}
          {synthesis.strongest_gate && (
            <View style={[styles.section, { borderBottomColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                NOTABLE GATE
              </Text>
              <View style={[styles.gateCard, { backgroundColor: LUNAR_COLORS.dimGlow }]}>
                <Text style={[styles.gateTitle, { color: theme.text }]}>
                  Gate {synthesis.strongest_gate.gate} — {synthesis.strongest_gate.title}
                </Text>
                <Text style={[styles.gateInsight, { color: theme.textSecondary }]}>
                  {synthesis.strongest_gate.insight}
                </Text>
                {synthesis.strongest_gate.longest_entry_preview && (
                  <View style={styles.gateQuoteBox}>
                    <Text style={[styles.gateQuote, { color: theme.textTertiary }]}>
                      Your reflection: "{synthesis.strongest_gate.longest_entry_preview}"
                    </Text>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              SECTION 4: PATTERN INSIGHT
              ═══════════════════════════════════════════════════════════════ */}
          {synthesis.pattern_insight && (
            <View style={[styles.section, { borderBottomColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                PATTERN INSIGHT
              </Text>
              <Text style={[styles.patternText, { color: theme.text }]}>
                {synthesis.pattern_insight}
              </Text>
            </View>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              SECTION 5: REFLECTION QUESTION
              ═══════════════════════════════════════════════════════════════ */}
          {synthesis.reflection_question && (
            <View style={styles.questionSection}>
              <Text style={[styles.sectionLabel, { color: LUNAR_COLORS.silver }]}>
                REFLECTION
              </Text>
              <Text style={[styles.questionText, { color: theme.textSecondary }]}>
                {synthesis.reflection_question}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

// =============================================================================
// STYLES - Task 69
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
  synthesisContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  
  // Overview Section
  overviewSection: {
    paddingBottom: 16,
    marginBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  overviewText: {
    fontSize: 14,
    marginBottom: 12,
  },
  overviewStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  overviewStat: {
    flex: 1,
    alignItems: 'center',
  },
  overviewStatValue: {
    fontSize: 22,
    fontWeight: '600',
  },
  overviewStatLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  overviewStatDivider: {
    width: 1,
    height: 30,
  },
  
  // Section styles
  section: {
    paddingBottom: 16,
    marginBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // Emotional themes
  themeRow: {
    marginTop: 12,
  },
  themeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginBottom: 4,
  },
  themeBadgeLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  themeList: {
    fontSize: 13,
    lineHeight: 18,
  },
  
  // Gate card
  gateCard: {
    borderRadius: 10,
    padding: 14,
  },
  gateTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 6,
  },
  gateInsight: {
    fontSize: 13,
    lineHeight: 19,
  },
  gateQuoteBox: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(192, 200, 212, 0.2)',
  },
  gateQuote: {
    fontSize: 12,
    lineHeight: 17,
    fontStyle: 'italic',
  },
  
  // Pattern
  patternText: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // Question
  questionSection: {
    paddingTop: 4,
  },
  questionText: {
    fontSize: 15,
    lineHeight: 23,
    fontStyle: 'italic',
  },
  
  // Low data scenario
  lowDataContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  lowDataMessage: {
    fontSize: 14,
    lineHeight: 21,
  },
  suggestionBox: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
  },
  suggestionText: {
    fontSize: 13,
    lineHeight: 18,
  },
});

export type { SynthesisData, LunarCycleSynthesisCardProps };
