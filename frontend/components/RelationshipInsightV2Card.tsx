// ============================================
// RELATIONSHIP INSIGHT V2 — 3-Layer Architecture
// ============================================
//
// Layer 1 = STORY (Synthesis) — Default view
// Layer 2 = PATTERNS (Behaviors) — Scroll to reveal
// Layer 3 = SIGNALS (Proof) — Expandable "Why this is so strong"
//

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

// ============================================
// INTERFACES
// ============================================

interface HDSignal {
  channel: string;
  name: string;
  translation: string;
}

interface RelInsightV2Data {
  success: boolean;
  version: string;
  other_name: string;
  story: {
    headline: string;
    summary: string;
  };
  patterns: {
    what_happens: string[];
    tensions: string[];
    gifts: string[];
  };
  signals: {
    human_design: HDSignal[];
    astrology: { attraction: string[]; tension: string[]; growth: string[] };
    bazi: { strengthens: string[]; drains: string[]; activates_growth: string[] };
    enneagram: { gift_to_them: string[]; gift_to_you: string[] };
    numerology: { complementarity: string[]; missing_traits: string[] };
  };
}

interface Props {
  userId: string;
  otherName: string;
  relationshipContext?: string;
  theme: any;
  onClose?: () => void;
}

// ============================================
// SECTION DIVIDER
// ============================================

const SectionDivider: React.FC<{ theme: any }> = ({ theme }) => (
  <View style={[styles.divider, { backgroundColor: theme.border }]} />
);

// ============================================
// BULLET COMPONENT
// ============================================

const Bullet: React.FC<{ text: string; theme: any; icon?: string }> = ({ text, theme, icon }) => (
  <View style={styles.bulletRow}>
    <Text style={[styles.bulletDash, { color: theme.textTertiary }]}>
      {icon === 'tension' ? '⚡' : icon === 'gift' ? '✦' : '›'}
    </Text>
    <Text style={[styles.bulletText, { color: theme.textSecondary }]}>
      {text}
    </Text>
  </View>
);

// ============================================
// MAIN COMPONENT
// ============================================

const RelationshipInsightV2Card: React.FC<Props> = ({
  userId,
  otherName,
  relationshipContext = '',
  theme,
  onClose,
}) => {
  const [data, setData] = useState<RelInsightV2Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  const loadInsight = useCallback(async () => {
    if (!userId || !otherName) return;
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/relationship-insight-v2/${userId}`, {
        params: {
          other_name: otherName,
          context: relationshipContext,
        },
      });
      if (response.data?.success) {
        setData(response.data);
      } else {
        throw new Error('Invalid response');
      }
    } catch (err: any) {
      console.error('[RelInsightV2] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [userId, otherName, relationshipContext]);

  useEffect(() => {
    loadInsight();
  }, [loadInsight]);

  // Loading
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading what's between you...
        </Text>
      </View>
    );
  }

  // Error
  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
        <TouchableOpacity onPress={loadInsight} style={styles.retryBtn}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!data) return null;

  const hasHDSignals = data.signals.human_design.length > 0;
  // R1 wiring: gate now considers ALL five lenses (was HD+Enneagram only).
  // Lets Astrology / BaZi / Numerology open the "Why this is so strong" surface
  // even when HD and Enneagram are empty.
  const hasAstroSignals =
    data.signals.astrology.attraction.length > 0 ||
    data.signals.astrology.tension.length > 0 ||
    data.signals.astrology.growth.length > 0;
  const hasBaziSignals =
    data.signals.bazi.strengthens.length > 0 ||
    data.signals.bazi.drains.length > 0 ||
    data.signals.bazi.activates_growth.length > 0;
  const hasEnneaSignals =
    data.signals.enneagram.gift_to_them.length > 0 ||
    data.signals.enneagram.gift_to_you.length > 0;
  const hasNumerSignals =
    data.signals.numerology.complementarity.length > 0 ||
    data.signals.numerology.missing_traits.length > 0;
  const hasAnySignals =
    hasHDSignals || hasAstroSignals || hasBaziSignals || hasEnneaSignals || hasNumerSignals;

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
    >
      {/* HEADER */}
      <View style={styles.header}>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeBtn} hitSlop={{ top: 15, bottom: 15, left: 15, right: 15 }}>
            <Ionicons name="close" size={22} color={theme.text} />
          </TouchableOpacity>
        )}
        <Text style={[styles.headerTitle, { color: theme.text }]}>
          Between you and {otherName}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* LAYER 1: STORY                                               */}
      {/* ============================================================ */}
      <View style={[styles.storyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.storyHeadline, { color: theme.text }]}>
          {data.story.headline}
        </Text>
        <Text style={[styles.storySummary, { color: theme.textSecondary }]}>
          {data.story.summary}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* LAYER 2: PATTERNS                                            */}
      {/* ============================================================ */}

      {/* What Happens */}
      <View style={styles.patternSection}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
          WHAT HAPPENS BETWEEN YOU
        </Text>
        {data.patterns.what_happens.map((item, i) => (
          <Bullet key={`wh-${i}`} text={item} theme={theme} />
        ))}
      </View>

      {/* Tensions */}
      <View style={styles.patternSection}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
          WHERE FRICTION SHOWS UP
        </Text>
        {data.patterns.tensions.map((item, i) => (
          <Bullet key={`tn-${i}`} text={item} theme={theme} icon="tension" />
        ))}
      </View>

      {/* Gifts */}
      <View style={[styles.giftSection, { borderLeftColor: (theme.accent || '#8B5CF6') + '50' }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
          WHAT YOU GIVE EACH OTHER
        </Text>
        {data.patterns.gifts.map((item, i) => (
          <Bullet key={`gf-${i}`} text={item} theme={theme} icon="gift" />
        ))}
      </View>

      <SectionDivider theme={theme} />

      {/* ============================================================ */}
      {/* LAYER 3: SIGNALS (Expandable)                                */}
      {/* ============================================================ */}
      {hasAnySignals && (
        <>
          <TouchableOpacity
            style={[styles.signalsToggle, { borderColor: theme.border }]}
            onPress={() => setSignalsExpanded(!signalsExpanded)}
            activeOpacity={0.7}
          >
            <Text style={[styles.signalsToggleText, { color: theme.textSecondary }]}>
              {signalsExpanded ? 'Hide what drives this' : 'Why this is so strong'}
            </Text>
            <Ionicons
              name={signalsExpanded ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={theme.textTertiary}
            />
          </TouchableOpacity>

          {signalsExpanded && (
            <View style={[styles.signalsContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>

              {/* Human Design Signals */}
              {hasHDSignals && (
                <View style={styles.signalGroup}>
                  <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                    DESIGN CONNECTIONS
                  </Text>
                  {data.signals.human_design.map((sig, i) => (
                    <View key={`hd-${i}`} style={[styles.signalItem, { borderColor: theme.border }]}>
                      <View style={styles.signalItemHeader}>
                        <Text style={[styles.signalChannel, { color: theme.accent || '#8B5CF6' }]}>
                          {sig.channel}
                        </Text>
                        <Text style={[styles.signalName, { color: theme.text }]}>
                          {sig.name}
                        </Text>
                      </View>
                      <Text style={[styles.signalTranslation, { color: theme.textSecondary }]}>
                        {sig.translation}
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Enneagram Signals */}
              {(data.signals.enneagram.gift_to_them.length > 0 || data.signals.enneagram.gift_to_you.length > 0) && (
                <View style={styles.signalGroup}>
                  <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                    GROWTH GIFTS
                  </Text>
                  {data.signals.enneagram.gift_to_them.map((item, i) => (
                    <Text key={`e2t-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>
                      You → them: {item}
                    </Text>
                  ))}
                  {data.signals.enneagram.gift_to_you.map((item, i) => (
                    <Text key={`e2u-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>
                      Them → you: {item}
                    </Text>
                  ))}
                </View>
              )}

              {/* Astrology Signals */}
              {(data.signals.astrology.attraction.length > 0 || data.signals.astrology.tension.length > 0 || data.signals.astrology.growth.length > 0) && (
                <View style={styles.signalGroup}>
                  <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                    ASTROLOGICAL DYNAMICS
                  </Text>
                  {data.signals.astrology.attraction.map((item, i) => (
                    <Text key={`aa-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>✦ {item}</Text>
                  ))}
                  {data.signals.astrology.tension.map((item, i) => (
                    <Text key={`at-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>⚡ {item}</Text>
                  ))}
                  {data.signals.astrology.growth.map((item, i) => (
                    <Text key={`ag-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>↑ {item}</Text>
                  ))}
                </View>
              )}

              {/* BaZi Signals */}
              {(data.signals.bazi.strengthens.length > 0 || data.signals.bazi.drains.length > 0 || data.signals.bazi.activates_growth.length > 0) && (
                <View style={styles.signalGroup}>
                  <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                    ELEMENTAL DYNAMICS
                  </Text>
                  {data.signals.bazi.strengthens.map((item, i) => (
                    <Text key={`bs-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>+ {item}</Text>
                  ))}
                  {data.signals.bazi.drains.map((item, i) => (
                    <Text key={`bd-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>- {item}</Text>
                  ))}
                  {data.signals.bazi.activates_growth.map((item, i) => (
                    <Text key={`bg-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>↑ {item}</Text>
                  ))}
                </View>
              )}
            </View>
          )}
        </>
      )}

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 40,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  retryBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  retryText: {
    fontSize: 16,
    fontWeight: '600',
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  closeBtn: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
  },

  // Layer 1: Story
  storyCard: {
    marginHorizontal: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 24,
  },
  storyHeadline: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
    marginBottom: 16,
  },
  storySummary: {
    fontSize: 17,
    lineHeight: 31,
  },

  // Layer 2: Patterns
  patternSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 16,
  },
  bulletRow: {
    flexDirection: 'row',
    marginBottom: 14,
    paddingRight: 8,
  },
  bulletDash: {
    fontSize: 16,
    marginRight: 10,
    marginTop: 1,
    width: 16,
    textAlign: 'center',
  },
  bulletText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 30,
  },
  giftSection: {
    paddingHorizontal: 20,
    paddingLeft: 34,
    borderLeftWidth: 3,
    marginLeft: 20,
    marginBottom: 20,
  },

  // Divider
  divider: {
    height: StyleSheet.hairlineWidth,
    marginHorizontal: 20,
    marginVertical: 16,
  },

  // Layer 3: Signals
  signalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    marginHorizontal: 20,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  signalsToggleText: {
    fontSize: 16,
    fontWeight: '500',
  },
  signalsContainer: {
    marginHorizontal: 20,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    gap: 20,
  },
  signalGroup: {
    gap: 8,
  },
  signalGroupLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  signalItem: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  signalItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  signalChannel: {
    fontSize: 14,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  signalName: {
    fontSize: 16,
    fontWeight: '500',
  },
  signalTranslation: {
    fontSize: 16,
    lineHeight: 32,
    fontStyle: 'italic',
  },
  signalText: {
    fontSize: 16,
    lineHeight: 32,
    paddingLeft: 4,
  },

  bottomSpacer: {
    height: 40,
  },
});

export default RelationshipInsightV2Card;
