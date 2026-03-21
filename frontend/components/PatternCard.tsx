/**
 * PatternCard.tsx
 * ================
 * 
 * Pattern Mirror V1 - Real-time Pattern Reflection Card
 * 
 * This is NOT a personality report.
 * This is a REAL-TIME PATTERN MIRROR.
 * 
 * Structure:
 * - Header: "PATTERN" / "What may be happening right now"
 * - What you may be (current pattern)
 * - What's your challenge (shadow behaviors)
 * - What's your genius (expanded expression + archetype)
 * - Practical ways to think about it (micro shifts)
 * - CTA: "Reflect on this" → Opens Mirror Chat seeded with pattern
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

interface PatternGenius {
  description: string;
  archetype?: string | null;
}

interface Pattern {
  title: string;
  what_you_may_be: string;
  challenge: string[];
  genius: PatternGenius;
  micro_shifts: string[];
}

interface SignalsBySource {
  journal?: string[];
  mirror_chat?: string[];
  lifeline?: string[];
  timing?: string[];
}

// ===== V2 INTERFACES =====

interface PersonalPattern {
  selected_pattern_id: string;
  selected_pattern_title: string;
  selected_pattern_summary: string;
  primary_signal_sources: string[];
  primary_signal_evidence: Record<string, any>;
  signal_strength: string;
  signal_score: number;
}

interface TimingAmplifier {
  active_timing_themes: string[];
  timing_summary: string | null;
  transit_score: number;
  timing_role: 'amplifier' | 'fallback';
  lunar_phase?: string | null;
  seasonal_context?: string | null;
}

interface Narrative {
  main_explanation: string;
  timing_note: string | null;
  evidence_summary: string | null;
  combined: string;
}

interface EvidenceMatch {
  text: string;
  matched_keyword: string;
  strength: 'high' | 'moderate';
  date?: string | null;
  emotional_tone?: string | null;
}

interface Evidence {
  pattern_id: string;
  contributing_sources: string[];
  matched_evidence: Record<string, EvidenceMatch[]>;
  total_matches: number;
  primary_source: string | null;
}

interface SelectionDebug {
  top_3_by_signal_score: Array<{pattern_id: string; signal_score: number; title: string}>;
  top_3_by_final_score: Array<{pattern_id: string; final: number; signal: number; transit: number}>;
  fallback_mode: boolean;
  timing_changed_winner: boolean;
  timing_only_amplified: boolean;
  signal_winner: string;
  final_winner: string;
}

interface PatternData {
  // V2 Structure
  personal_pattern?: PersonalPattern;
  timing_amplifier?: TimingAmplifier;
  narrative?: Narrative;
  evidence?: Evidence;
  selection_debug?: SelectionDebug;
  
  // Legacy fields
  pattern: Pattern;
  pattern_id?: string;
  cached: boolean;
  generated_at: string;
  signal_strength?: string;
  signals_by_source?: SignalsBySource;
  timing_context?: string[];
  active_themes?: string[];
  personal_activations?: Array<{
    target: string;
    gene_key: number;
    score: number;
    name: string;
    description: string;
  }>;
  unified_narrative?: string;
  fallback?: boolean;
}

// Source display names
const SOURCE_LABELS: Record<string, string> = {
  journal: 'Your journal entries',
  mirror_chat: 'Mirror conversations',
  lifeline: 'Your lifeline events',
  timing: 'Current timing (amplifying)',
};

interface PatternCardProps {
  userId: string;
  onPatternLoaded?: (pattern: Pattern | null) => void;
}

export default function PatternCard({ userId, onPatternLoaded }: PatternCardProps) {
  const { theme } = useTheme();
  const router = useRouter();
  
  const [patternData, setPatternData] = useState<PatternData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);
  const [detailsExpanded, setDetailsExpanded] = useState(false);

  const loadPattern = useCallback(async () => {
    if (!userId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/patterns/${userId}`);
      setPatternData(response.data);
      onPatternLoaded?.(response.data?.pattern || null);
    } catch (err: any) {
      console.error('[PatternCard] Load error:', err);
      setError('Unable to load pattern');
      onPatternLoaded?.(null);
    } finally {
      setIsLoading(false);
    }
  }, [userId, onPatternLoaded]);

  useEffect(() => {
    loadPattern();
  }, [loadPattern]);

  // Handle "Reflect on this" button
  const handleReflect = useCallback(() => {
    if (!patternData?.pattern) return;
    
    // Navigate to reflection-chat with seeded message about the pattern
    const seedMessage = `This pattern showed up:\n\n"${patternData.pattern.what_you_may_be}"\n\nHelp me see what I'm not seeing.`;
    
    router.push({
      pathname: '/reflection-chat',
      params: {
        context: 'pattern',
        seedMessage: seedMessage,
        autoSend: 'true',
      }
    });
  }, [patternData, router]);

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading your signals...
          </Text>
        </View>
      </View>
    );
  }

  // Error state
  if (error || !patternData?.pattern) {
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.emptyContainer}>
          <Text style={[styles.emptyText, { color: theme.textTertiary }]}>
            Pattern will appear as you reflect more
          </Text>
        </View>
      </View>
    );
  }

  const { pattern } = patternData;
  
  // V2: Extract signals-first data
  const personalPattern = patternData.personal_pattern;
  const timingAmplifier = patternData.timing_amplifier;
  const narrative = patternData.narrative;
  const evidence = patternData.evidence;
  const isAmplifierMode = timingAmplifier?.timing_role === 'amplifier';

  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>PATTERN</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          What may be happening right now
        </Text>
      </View>

      {/* V2: Title from personal_pattern (primary) */}
      <Text style={[styles.patternTitle, { color: theme.text }]}>
        {personalPattern?.selected_pattern_title || pattern.title}
      </Text>

      {/* V2: SIGNALS-FIRST NARRATIVE */}
      {narrative?.main_explanation ? (
        <View style={styles.section}>
          {/* Main explanation from personal signals */}
          <Text style={[styles.unifiedNarrative, { color: theme.text }]}>
            {narrative.main_explanation}
          </Text>
          
          {/* Timing note - SECONDARY, only if in amplifier mode */}
          {isAmplifierMode && narrative.timing_note && (
            <Text style={[styles.timingNote, { color: theme.textSecondary }]}>
              {narrative.timing_note}
            </Text>
          )}
          
          {/* Evidence summary */}
          {narrative.evidence_summary && (
            <Text style={[styles.evidenceSummary, { color: theme.textTertiary }]}>
              {narrative.evidence_summary}
            </Text>
          )}
        </View>
      ) : patternData.unified_narrative ? (
        /* Legacy fallback to unified_narrative */
        <View style={styles.section}>
          <Text style={[styles.unifiedNarrative, { color: theme.text }]}>
            {patternData.unified_narrative}
          </Text>
        </View>
      ) : (
        /* Fallback to separate sections if no narrative */
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            WHAT YOU MAY BE
          </Text>
          <Text style={[styles.whatYouMayBe, { color: theme.text }]}>
            {pattern.what_you_may_be}
          </Text>
        </View>
      )}

      {/* V2: Timing Context - SECONDARY amplification context */}
      {timingAmplifier && timingAmplifier.active_timing_themes && timingAmplifier.active_timing_themes.length > 0 && (
        <View style={[styles.timingContextSecondary, { backgroundColor: theme.surfaceAlt || theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.timingContextTitleSecondary, { color: theme.textTertiary }]}>
            {isAmplifierMode ? 'WHY THIS MAY FEEL STRONGER RIGHT NOW' : 'CURRENT TIMING'}
          </Text>
          {timingAmplifier.timing_summary && (
            <Text style={[styles.timingContextText, { color: theme.textSecondary }]}>
              {timingAmplifier.timing_summary}
            </Text>
          )}
        </View>
      )}

      {/* Challenge - keep but collapsed by default */}
      <TouchableOpacity
        onPress={() => setDetailsExpanded(!detailsExpanded)}
        activeOpacity={0.7}
        style={styles.detailsTrigger}
      >
        <Text style={[styles.detailsTriggerText, { color: theme.textTertiary }]}>
          {detailsExpanded ? 'Hide details ▲' : 'Show challenge & genius ▼'}
        </Text>
      </TouchableOpacity>

      {detailsExpanded && (
        <>
          {/* Challenge */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              WHAT'S YOUR CHALLENGE
            </Text>
            <View style={styles.challengeList}>
              {pattern.challenge.map((item, index) => (
                <View key={index} style={styles.challengeItem}>
                  <Text style={[styles.bulletPoint, { color: theme.textTertiary }]}>•</Text>
                  <Text style={[styles.challengeText, { color: theme.textSecondary }]}>
                    {item}
                  </Text>
                </View>
              ))}
            </View>
          </View>

          {/* Genius */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              WHAT'S YOUR GENIUS
            </Text>
            <Text style={[styles.geniusDescription, { color: theme.text }]}>
              {pattern.genius.description}
            </Text>
            {pattern.genius.archetype && (
              <Text style={[styles.archetype, { color: theme.accent }]}>
                {pattern.genius.archetype}
              </Text>
            )}
          </View>

          {/* Micro Shifts */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              PRACTICAL WAYS TO THINK ABOUT IT
            </Text>
            {pattern.micro_shifts.map((shift, index) => (
              <Text key={index} style={[styles.microShift, { color: theme.textSecondary }]}>
                {shift}
              </Text>
            ))}
          </View>
        </>
      )}

      {/* CTA: Reflect on this */}
      <TouchableOpacity
        style={[styles.reflectButton, { backgroundColor: theme.accent }]}
        onPress={handleReflect}
        activeOpacity={0.8}
      >
        <Text style={[styles.reflectButtonText, { color: theme.textInverse }]}>
          Reflect on this
        </Text>
      </TouchableOpacity>

      {/* V2: Signal strength indicator with source info */}
      {(personalPattern?.signal_strength || patternData.signal_strength) && (
        <TouchableOpacity
          onPress={() => setSignalsExpanded(!signalsExpanded)}
          activeOpacity={0.7}
          style={styles.signalTrigger}
        >
          <Text style={[styles.signalIndicator, { color: theme.textTertiary }]}>
            Based on {personalPattern?.signal_strength || patternData.signal_strength} signals
            {personalPattern?.primary_signal_sources && personalPattern.primary_signal_sources.length > 0 && (
              <Text style={styles.signalSourceHint}>
                {' '}from {personalPattern.primary_signal_sources.slice(0, 2).map(s => SOURCE_LABELS[s] || s).join(', ')}
              </Text>
            )}
            <Text style={styles.signalExpandHint}>
              {signalsExpanded ? '  ▲' : '  ▼'}
            </Text>
          </Text>
        </TouchableOpacity>
      )}

      {/* V2: TRUE EVIDENCE PANEL - shows actual matched signals */}
      {signalsExpanded && (
        <View style={[styles.signalsSection, { borderTopColor: theme.border }]}>
          <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>
            WHAT THIS IS BASED ON
          </Text>
          
          {/* V2: Render true evidence from evidence object */}
          {evidence?.matched_evidence && Object.entries(evidence.matched_evidence).map(([source, matches]) => {
            if (!matches || matches.length === 0) return null;
            
            // Skip timing in evidence panel - it's shown separately
            if (source === 'timing') return null;
            
            return (
              <View key={source} style={styles.signalSourceGroup}>
                <View style={styles.sourceHeader}>
                  <Text style={[styles.signalSourceLabel, { color: theme.textSecondary }]}>
                    {SOURCE_LABELS[source] || source}
                  </Text>
                  {source === evidence.primary_source && (
                    <Text style={[styles.primaryBadge, { color: theme.accent }]}>
                      primary
                    </Text>
                  )}
                </View>
                {(matches as EvidenceMatch[]).map((match, index) => (
                  <View key={index} style={styles.evidenceItem}>
                    <Text style={[styles.signalBullet, { color: theme.textTertiary }]}>•</Text>
                    <View style={styles.evidenceContent}>
                      <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                        {match.text}
                      </Text>
                      <Text style={[styles.matchedKeyword, { color: theme.textTertiary }]}>
                        matched: "{match.matched_keyword}" ({match.strength})
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            );
          })}
          
          {/* Fallback to legacy signals_by_source if no V2 evidence */}
          {!evidence?.matched_evidence && patternData.signals_by_source && Object.entries(patternData.signals_by_source).map(([source, signals]) => {
            if (!signals || signals.length === 0) return null;
            if (source === 'timing') return null; // Skip timing
            
            return (
              <View key={source} style={styles.signalSourceGroup}>
                <Text style={[styles.signalSourceLabel, { color: theme.textSecondary }]}>
                  {SOURCE_LABELS[source] || source}
                </Text>
                {signals.map((signal, index) => (
                  <View key={index} style={styles.signalItem}>
                    <Text style={[styles.signalBullet, { color: theme.textTertiary }]}>•</Text>
                    <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                      {signal}
                    </Text>
                  </View>
                ))}
              </View>
            );
          })}
          
          {/* V2: Total matches summary */}
          {evidence?.total_matches !== undefined && (
            <Text style={[styles.totalMatches, { color: theme.textTertiary }]}>
              {evidence.total_matches} signal{evidence.total_matches !== 1 ? 's' : ''} matched this pattern
            </Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 20,
    marginVertical: 12,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
  },
  
  // Loading state
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  
  // Empty state
  emptyContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Header
  header: {
    marginBottom: 16,
  },
  headerLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  
  // Pattern title
  patternTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 20,
  },
  
  // Sections
  section: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  
  // What you may be
  whatYouMayBe: {
    fontSize: 16,
    lineHeight: 24,
  },
  
  // Challenge
  challengeList: {
    gap: 6,
  },
  challengeItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bulletPoint: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 2,
  },
  challengeText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  
  // Genius
  geniusDescription: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 8,
  },
  archetype: {
    fontSize: 14,
    fontWeight: '600',
    fontStyle: 'italic',
  },
  
  // Micro shifts
  microShift: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
    marginBottom: 6,
  },
  
  // Timing Context (What's active right now)
  timingContext: {
    marginBottom: 20,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  timingContextTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  timingContextItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 5,
  },
  timingBullet: {
    fontSize: 10,
    marginRight: 6,
    marginTop: 2,
  },
  timingContextText: {
    fontSize: 12,
    lineHeight: 17,
    flex: 1,
    fontStyle: 'italic',
  },
  
  // CTA Button
  reflectButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  reflectButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  
  // Signal indicator with tap to expand
  signalTrigger: {
    marginTop: 16,
    alignItems: 'center',
  },
  signalIndicator: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  signalExpandHint: {
    fontSize: 10,
  },
  
  // Collapsible signals section
  signalsSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
  },
  signalsSectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 16,
  },
  signalSourceGroup: {
    marginBottom: 16,
  },
  signalSourceLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
    paddingLeft: 4,
  },
  signalBullet: {
    fontSize: 12,
    marginRight: 8,
    marginTop: 1,
  },
  signalText: {
    fontSize: 13,
    lineHeight: 19,
    flex: 1,
  },
  
  // V2: Timing note (secondary)
  timingNote: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
    marginTop: 16,
    paddingLeft: 12,
    borderLeftWidth: 2,
    borderLeftColor: 'rgba(128, 128, 128, 0.3)',
  },
  
  // V2: Evidence summary
  evidenceSummary: {
    fontSize: 12,
    marginTop: 12,
    fontStyle: 'italic',
  },
  
  // V2: Secondary timing context (downgraded)
  timingContextSecondary: {
    marginTop: 16,
    marginBottom: 8,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    opacity: 0.8,
  },
  timingContextTitleSecondary: {
    fontSize: 8,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  
  // V2: Signal source hint
  signalSourceHint: {
    fontSize: 11,
    fontStyle: 'normal',
  },
  
  // V2: Source header with badge
  sourceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  primaryBadge: {
    fontSize: 9,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  
  // V2: Evidence item with keyword info
  evidenceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
    paddingLeft: 4,
  },
  evidenceContent: {
    flex: 1,
  },
  matchedKeyword: {
    fontSize: 10,
    fontStyle: 'italic',
    marginTop: 2,
  },
  
  // V2: Total matches summary
  totalMatches: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
});
