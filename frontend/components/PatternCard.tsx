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

interface PatternData {
  pattern: Pattern;
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
  journal: 'Journal',
  mirror_chat: 'Mirror chat',
  lifeline: 'Lifeline',
  timing: 'Timing',
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

  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>PATTERN</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          What may be happening right now
        </Text>
      </View>

      {/* Timing Context - What's active right now */}
      {patternData.timing_context && patternData.timing_context.length > 0 && (
        <View style={[styles.timingContext, { backgroundColor: theme.surfaceAlt || theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.timingContextTitle, { color: theme.textTertiary }]}>
            WHAT'S ACTIVE RIGHT NOW
          </Text>
          {patternData.timing_context.map((context, index) => (
            <View key={index} style={styles.timingContextItem}>
              <Text style={[styles.timingBullet, { color: theme.accent }]}>•</Text>
              <Text style={[styles.timingContextText, { color: theme.textSecondary }]}>
                {context}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Title */}
      <Text style={[styles.patternTitle, { color: theme.text }]}>
        {pattern.title}
      </Text>

      {/* UNIFIED NARRATIVE - Single coherent reflection */}
      {patternData.unified_narrative ? (
        <View style={styles.section}>
          <Text style={[styles.unifiedNarrative, { color: theme.text }]}>
            {patternData.unified_narrative}
          </Text>
        </View>
      ) : (
        /* Fallback to separate sections if no unified narrative */
        <>
          {/* What you may be */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              WHAT YOU MAY BE
            </Text>
            <Text style={[styles.whatYouMayBe, { color: theme.text }]}>
              {pattern.what_you_may_be}
            </Text>
          </View>
        </>
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

      {/* Signal strength indicator with tap to expand */}
      {patternData.signal_strength && (
        <TouchableOpacity
          onPress={() => setSignalsExpanded(!signalsExpanded)}
          activeOpacity={0.7}
          style={styles.signalTrigger}
        >
          <Text style={[styles.signalIndicator, { color: theme.textTertiary }]}>
            Based on {patternData.signal_strength} signals
            <Text style={styles.signalExpandHint}>
              {signalsExpanded ? '  ▲' : '  ▼'}
            </Text>
          </Text>
        </TouchableOpacity>
      )}

      {/* Collapsible signals section - grouped by source */}
      {signalsExpanded && patternData.signals_by_source && Object.keys(patternData.signals_by_source).length > 0 && (
        <View style={[styles.signalsSection, { borderTopColor: theme.border }]}>
          <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>
            WHAT THIS IS BASED ON
          </Text>
          
          {/* Render each source that has signals */}
          {Object.entries(patternData.signals_by_source).map(([source, signals]) => {
            if (!signals || signals.length === 0) return null;
            
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
});
