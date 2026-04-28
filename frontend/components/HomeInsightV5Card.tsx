// ============================================
// HOME INSIGHT V5 - Pattern Engine Final Form
// ============================================
//
// CORE IDENTITY:
// Home = Pattern across time (identity + recurrence)
// Today = Moment inside the day (situational + interrupt)
//
// Home must feel like: "This keeps happening to me."
// NOT: "This is happening today."
//
// V5 OUTPUT STRUCTURE:
// 1. PATTERN LABEL: Short (max 3-4 words)
// 2. HEADLINE: Pattern-based, not "today"
// 3. IDENTITY MIRROR: One sharp identity-level reflection (NEW)
// 4. WHAT'S GOING ON: Pattern loops, no abstraction
// 5. WHERE IT SHOWS UP: ONE dominant life area
// 6. WHAT YOU MAY BE DOING: Repeated behaviors, loops
// 7. WHAT THIS CREATES: Quiet cost
// 8. THE MOVE: Pattern-level trajectory shift
// 9. WHY SHOWING UP: Collapsible proof layer
//

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

// ============================================
// V5 DATA INTERFACE
// ============================================

interface WhyShowingUp {
  signals: string[];
  trigger_confidence: string;
  note: string;
}

interface RecurrenceBlock {
  memory_state?: string;
  match_count?: number;
  human_label?: string | null;
  recurrence_detected?: boolean;
  recurrence_confidence?: string;
}

interface HomeInsightV5Data {
  success: boolean;
  version: string;
  date: string;
  pattern_label: string;
  headline: string;
  identity_mirror: string;
  whats_going_on: string[];
  where_it_shows_up: string;
  what_you_may_be_doing: string[];
  what_this_creates: string;
  the_move: string;
  why_showing_up?: WhyShowingUp | null;
  cluster: string;
  house?: number;
  trigger_confidence: string;
  recurrence?: RecurrenceBlock;
}

// ============================================
// PROPS INTERFACE
// ============================================

interface HomeInsightV5CardProps {
  userId: string;
  theme: any;
  onReflect?: (question: string) => void;
}

// ============================================
// BULLET ITEM COMPONENT
// ============================================

const BulletItem: React.FC<{ text: string; theme: any; icon?: string }> = ({ text, theme, icon }) => (
  <View style={styles.bulletRow}>
    <Text style={[styles.bulletDash, { color: theme.textTertiary }]}>
      {icon === 'dash' ? '—' : '›'}
    </Text>
    <Text style={[styles.bulletText, { color: theme.textSecondary }]}>
      {text}
    </Text>
  </View>
);

// ============================================
// SECTION HEADER COMPONENT
// ============================================

const SectionHeader: React.FC<{ title: string; theme: any }> = ({ title, theme }) => (
  <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
    {title}
  </Text>
);

// ============================================
// MAIN COMPONENT
// ============================================

const HomeInsightV5Card: React.FC<HomeInsightV5CardProps> = ({
  userId,
  theme,
  onReflect,
}) => {
  const [data, setData] = useState<HomeInsightV5Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [proofExpanded, setProofExpanded] = useState(false);

  const loadInsightV5 = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/home-insight-v5/${userId}`);
      if (response.data?.success) {
        setData(response.data);
      } else {
        throw new Error('Invalid response');
      }
    } catch (err: any) {
      console.error('[HomeInsightV5] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadInsightV5();
  }, [loadInsightV5]);

  // Loading state
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading your patterns...
        </Text>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error}
        </Text>
        <TouchableOpacity onPress={loadInsightV5} style={styles.retryButton}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!data) return null;

  // Subtle accent based on trigger confidence
  const getAccentColor = () => {
    switch (data.trigger_confidence) {
      case 'strongly_active_now':
        return theme.accent || '#8B5CF6';
      case 'recurring_plus_trigger':
        return '#D4A574';
      default:
        return theme.textTertiary || '#888';
    }
  };

  const accentColor = getAccentColor();

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      
      {/* ============================================================ */}
      {/* PATTERN LABEL - Soft, max 3-4 words                         */}
      {/* ============================================================ */}
      <View style={[styles.patternLabelRow]}>
        <View style={[styles.patternLabelPill, { backgroundColor: accentColor + '18' }]}>
          <Text style={[styles.patternLabel, { color: accentColor }]}>
            {data.pattern_label.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* ============================================================ */}
      {/* RECURRENCE LABEL - Subtle "you've been here before" line   */}
      {/* Renders ONLY when recurrence_detected is True. No styling */}
      {/* changes beyond a small italic line above the headline.    */}
      {/* ============================================================ */}
      {data.recurrence?.recurrence_detected && data.recurrence?.human_label ? (
        <Text style={[styles.recurrenceLabel, { color: theme.textSecondary }]}>
          {data.recurrence.human_label}
        </Text>
      ) : null}

      {/* ============================================================ */}
      {/* HEADLINE - Pattern-based, recurrence-anchored               */}
      {/* ============================================================ */}
      <Text style={[styles.headline, { color: theme.text }]}>
        {data.headline}
      </Text>

      {/* ============================================================ */}
      {/* IDENTITY MIRROR - One sharp line (NEW in V5)                */}
      {/* Confronting but accurate, identity-level reflection         */}
      {/* ============================================================ */}
      <View style={[styles.identityMirrorContainer, { borderLeftColor: accentColor + '60' }]}>
        <Text style={[styles.identityMirrorText, { color: theme.text }]}>
          {data.identity_mirror}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* WHAT'S GOING ON - Pattern loops, no abstraction             */}
      {/* ============================================================ */}
      {data.whats_going_on && data.whats_going_on.length > 0 && (
        <View style={styles.section}>
          <SectionHeader title="WHAT'S GOING ON" theme={theme} />
          {data.whats_going_on.map((item, index) => (
            <BulletItem key={`wgo-${index}`} text={item} theme={theme} />
          ))}
        </View>
      )}

      {/* ============================================================ */}
      {/* WHERE IT SHOWS UP - ONE dominant life area                  */}
      {/* ============================================================ */}
      {data.where_it_shows_up ? (
        <View style={[styles.whereSection, { backgroundColor: theme.cardBackground || (theme.background + 'CC') }]}>
          <Ionicons name="locate-outline" size={13} color={theme.textTertiary} />
          <Text style={[styles.whereText, { color: theme.textSecondary }]}>
            {data.where_it_shows_up}
          </Text>
        </View>
      ) : null}

      {/* ============================================================ */}
      {/* WHAT YOU MAY BE DOING - Repeated behaviors, loops           */}
      {/* THE MOST IMPORTANT SECTION                                  */}
      {/* Must feel like: "That's EXACTLY what I do."                 */}
      {/* ============================================================ */}
      {data.what_you_may_be_doing && data.what_you_may_be_doing.length > 0 && (
        <View style={styles.section}>
          <SectionHeader title="WHAT YOU MAY BE DOING" theme={theme} />
          {data.what_you_may_be_doing.map((item, index) => (
            <BulletItem key={`doing-${index}`} text={item} theme={theme} icon="dash" />
          ))}
        </View>
      )}

      {/* ============================================================ */}
      {/* WHAT THIS CREATES - Quiet, real cost                        */}
      {/* ============================================================ */}
      {data.what_this_creates ? (
        <View style={[styles.createsSection, { borderLeftColor: accentColor + '50' }]}>
          <Text style={[styles.createsLabel, { color: theme.textTertiary }]}>
            WHAT THIS CREATES
          </Text>
          <Text style={[styles.createsText, { color: theme.text }]}>
            {data.what_this_creates}
          </Text>
        </View>
      ) : null}

      {/* ============================================================ */}
      {/* THE MOVE - Pattern-level trajectory shift                   */}
      {/* NOT moment-level interrupt                                  */}
      {/* ============================================================ */}
      {data.the_move ? (
        <View style={[styles.moveSection, { backgroundColor: accentColor + '0C', borderColor: accentColor + '25' }]}>
          <Text style={[styles.moveLabel, { color: accentColor }]}>
            THE MOVE
          </Text>
          <Text style={[styles.moveText, { color: theme.text }]}>
            {data.the_move}
          </Text>
        </View>
      ) : null}

      {/* ============================================================ */}
      {/* WHY THIS IS SHOWING UP - Collapsible proof layer            */}
      {/* ============================================================ */}
      {data.why_showing_up && data.why_showing_up.signals && data.why_showing_up.signals.length > 0 && (
        <>
          <TouchableOpacity
            style={[styles.proofToggle, { borderColor: theme.border }]}
            onPress={() => setProofExpanded(!proofExpanded)}
            activeOpacity={0.7}
          >
            <Text style={[styles.proofToggleText, { color: theme.textTertiary }]}>
              {proofExpanded ? 'Hide what informed this' : 'Why this keeps showing up'}
            </Text>
            <Ionicons
              name={proofExpanded ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={theme.textTertiary}
            />
          </TouchableOpacity>

          {proofExpanded && (
            <View style={[styles.proofSection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
              <Text style={[styles.proofNote, { color: theme.textTertiary }]}>
                {data.why_showing_up.note}
              </Text>
              {data.why_showing_up.signals.map((signal, index) => (
                <Text key={`signal-${index}`} style={[styles.proofSignal, { color: theme.textSecondary }]}>
                  • {signal}
                </Text>
              ))}
            </View>
          )}
        </>
      )}
    </View>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    padding: 22,
    borderRadius: 16,
    borderWidth: 1,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  errorContainer: {
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  retryText: {
    fontSize: 16,
    fontWeight: '600',
  },
  
  // Pattern Label
  patternLabelRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  patternLabelPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  patternLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  
  // Recurrence label — small italic line above headline.
  // Subtle "you've been here before" recognition (Phase 2).
  recurrenceLabel: {
    fontSize: 13,
    fontStyle: 'italic',
    fontWeight: '500',
    lineHeight: 18,
    marginBottom: 6,
    opacity: 0.85,
  },

  // Headline - Pattern-based
  headline: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
    marginBottom: 18,
    letterSpacing: 0.1,
  },
  
  // Identity Mirror - NEW in V5
  identityMirrorContainer: {
    borderLeftWidth: 3,
    paddingLeft: 16,
    paddingVertical: 10,
    marginBottom: 24,
  },
  identityMirrorText: {
    fontSize: 16,
    fontStyle: 'italic',
    lineHeight: 32,
    fontWeight: '400',
    letterSpacing: 0.1,
  },
  
  // Sections
  section: {
    marginBottom: 22,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 16,
  },
  
  // Bullets - Pattern-focused
  bulletRow: {
    flexDirection: 'row',
    marginBottom: 16,
    paddingRight: 8,
  },
  bulletDash: {
    fontSize: 17,
    fontWeight: '400',
    marginRight: 10,
    marginTop: 2,
    width: 14,
    textAlign: 'center',
  },
  bulletText: {
    flex: 1,
    fontSize: 17,
    lineHeight: 31,
  },
  
  // Where Section - ONE dominant area
  whereSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 14,
    borderRadius: 8,
    marginBottom: 22,
    gap: 8,
  },
  whereText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  
  // Creates Section - Quiet cost
  createsSection: {
    paddingLeft: 16,
    borderLeftWidth: 3,
    marginBottom: 22,
  },
  createsLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  createsText: {
    fontSize: 17,
    lineHeight: 31,
  },
  
  // The Move - Pattern-level trajectory shift
  moveSection: {
    padding: 18,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 14,
  },
  moveLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 14,
  },
  moveText: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 32,
  },
  
  // Proof Section - Collapsible
  proofToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  proofToggleText: {
    fontSize: 16,
    fontWeight: '400',
  },
  proofSection: {
    padding: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 10,
  },
  proofNote: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 14,
    lineHeight: 31,
  },
  proofSignal: {
    fontSize: 16,
    lineHeight: 32,
    marginBottom: 5,
  },
});

export default HomeInsightV5Card;
