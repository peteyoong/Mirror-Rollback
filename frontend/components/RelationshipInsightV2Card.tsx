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
import * as EL from '../services/bazi/evidenceLabels';
import type { BaziCycle, AnimalRelation } from '../services/bazi/evidenceLabels';

// ============================================
// INTERFACES
// ============================================

interface HDSignal {
  channel: string;
  name: string;
  translation: string;
}

// ── Astrology Re-Story V1 surface wiring (additive) ───────────────
// Single section of the producer payload (see backend
// services/astrology_relationship_restory_v1.py).
//
// `headline` / `body` are user-facing strings — guaranteed jargon-free
// by the producer's acceptance tests.
// `hidden_evidence` may contain astro tokens — must NOT be rendered
// in the main narrative block.
interface ReStorySection {
  headline:        string;
  body:            string;
  hidden_evidence: string[];
}

interface BaziDiagnostics {
  element_a?: string;
  element_b?: string;
  cycle?: string;
  animal_a?: string;
  animal_b?: string;
  animal_relation?: string;
  role_key?: string;
  support_count?: number;
  tension_count?: number;
  growth_count?: number;
}

interface RelInsightV2Data {
  success: boolean;
  version: string;
  other_name: string;
  you_name?: string;
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
    astrology: {
      attraction: string[];
      tension: string[];
      growth: string[];
      // ── Astrology Re-Story V1 surface wiring (additive) ──────────
      // Present only when the backend `ASTROLOGY_RELATIONSHIP_RESTORY_V1`
      // flag is set.  When undefined, the card renders the legacy
      // attraction / tension / growth bullets exactly as before.
      restory_v1?: {
        success:           boolean;
        build_marker:      string;
        relationship_role: string;
        sections: {
          what_lives_between_you:             ReStorySection;
          what_strengthens_this_relationship: ReStorySection;
          growth_edge:                        ReStorySection;
          shadow_pattern:                     ReStorySection;
          why_this_person_matters:            ReStorySection;
        };
      };
    };
    bazi: {
      strengthens: string[];
      drains: string[];
      activates_growth: string[];
      diagnostics?: BaziDiagnostics;
    };
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

              {/* Astrology Signals — Re-Story V1 takes precedence when present */}
              {(() => {
                const restory = data.signals.astrology.restory_v1;
                if (restory && restory.success && restory.sections) {
                  // Render the 5-section narrative.  All strings are
                  // guaranteed jargon-free by the backend producer's
                  // acceptance tests.  `hidden_evidence` is INTENTIONALLY
                  // NOT rendered here (kept for a future expandable tray).
                  const sections = [
                    restory.sections.what_lives_between_you,
                    restory.sections.what_strengthens_this_relationship,
                    restory.sections.growth_edge,
                    restory.sections.shadow_pattern,
                    restory.sections.why_this_person_matters,
                  ];
                  return (
                    <View
                      style={styles.signalGroup}
                      // surface marker: astrology-relationship-restory-v1
                      accessibilityLabel="Relationship narrative"
                    >
                      {sections.map((sec, i) =>
                        sec && sec.headline && sec.body ? (
                          <View
                            key={`rsv1-${i}`}
                            style={[
                              styles.signalItem,
                              { borderColor: theme.border, marginBottom: 12 },
                            ]}
                          >
                            <Text
                              style={[
                                styles.signalGroupLabel,
                                { color: theme.textTertiary, marginBottom: 6 },
                              ]}
                            >
                              {sec.headline.toUpperCase()}
                            </Text>
                            <Text
                              style={[
                                styles.signalTranslation,
                                { color: theme.textSecondary, lineHeight: 20 },
                              ]}
                            >
                              {sec.body}
                            </Text>
                          </View>
                        ) : null,
                      )}
                    </View>
                  );
                }
                // Legacy fallback — preserved byte-for-byte when restory
                // is absent (flag off, missing charts, or producer error).
                const hasLegacy =
                  data.signals.astrology.attraction.length > 0 ||
                  data.signals.astrology.tension.length > 0 ||
                  data.signals.astrology.growth.length > 0;
                if (!hasLegacy) return null;
                return (
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
                );
              })()}

              {/* BaZi Signals — Evidence Layer V2 (parity with Forum Mapping) */}
              {/* MARKER: bazi-evidence-layer-v2                                */}
              {hasBaziSignals && (() => {
                const baziSig = data.signals.bazi;
                const support = baziSig.strengthens || [];
                const tension = baziSig.drains || [];
                const growth  = baziSig.activates_growth || [];
                const diag = baziSig.diagnostics;

                // Legacy fallback when diagnostics are not yet available
                if (!diag || !diag.element_a || !diag.element_b) {
                  return (
                    <View style={styles.signalGroup}>
                      <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                        ELEMENTAL DYNAMICS — Evidence
                      </Text>
                      {support.map((item, i) => (
                        <Text key={`bs-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>+ {item}</Text>
                      ))}
                      {tension.map((item, i) => (
                        <Text key={`bd-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>- {item}</Text>
                      ))}
                      {growth.map((item, i) => (
                        <Text key={`bg-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>↑ {item}</Text>
                      ))}
                    </View>
                  );
                }

                const cycle = (diag.cycle as BaziCycle) || 'unknown';
                const elA = diag.element_a || '?';
                const elB = diag.element_b || '?';
                const animA = diag.animal_a || '';
                const animB = diag.animal_b || '';
                const animRel = (diag.animal_relation as AnimalRelation) || 'unknown';
                const nameA = data.you_name || 'You';
                const nameB = data.other_name || otherName || 'Them';

                const flowRows = EL.buildFlowRows(cycle, elA, elB, nameA, nameB);
                const flowHeader = EL.flowHeaderForCycle(cycle);
                const geo = EL.geometryArrow(cycle, elA, elB);
                const animLabel = (animA && animB) ? EL.animalRelationLabel(animRel, animA, animB) : null;
                const growthSub = EL.growthTriggerSubtitle(animRel);

                const card = {
                  backgroundColor: (theme.cardSurface || theme.surface || 'rgba(255,255,255,0.03)'),
                  borderColor: theme.border,
                  borderWidth: StyleSheet.hairlineWidth,
                  borderRadius: 10,
                  padding: 12,
                  marginTop: 10,
                };
                const tinyHeader = { fontSize: 11, fontWeight: '700' as const, letterSpacing: 1.0 };
                const labelText  = { fontSize: 13, fontWeight: '600' as const, marginBottom: 2 };

                return (
                  <View style={styles.signalGroup}>
                    <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
                      ELEMENTAL DYNAMICS — Evidence
                    </Text>

                    {/* 1. ELEMENTAL STRUCTURE */}
                    <View style={card}>
                      <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>1 · ELEMENTAL STRUCTURE</Text>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Text style={[styles.signalText, { color: theme.textSecondary }]}>{nameA}</Text>
                        <Text style={[styles.signalText, { color: theme.text, fontWeight: '600' }]}>{elA}</Text>
                      </View>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                        <Text style={[styles.signalText, { color: theme.textSecondary }]}>{nameB}</Text>
                        <Text style={[styles.signalText, { color: theme.text, fontWeight: '600' }]}>{elB}</Text>
                      </View>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 }}>
                        <Text style={[styles.signalText, { color: theme.textSecondary }]}>Relationship Geometry</Text>
                        <Text style={[styles.signalText, { color: theme.text, fontWeight: '600' }]}>{geo}</Text>
                      </View>
                      <Text style={[labelText, { color: theme.textTertiary }]}>{flowHeader}</Text>
                      {flowRows.length === 0 ? (
                        <Text style={[styles.signalText, { color: theme.textSecondary, fontStyle: 'italic' }]}>
                          No automatic cycle — flow is built by agreement.
                        </Text>
                      ) : flowRows.map((r, i) => (
                        <View key={`fr-${i}`} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 2 }}>
                          <Text style={[styles.signalText, { color: theme.textSecondary, flexShrink: 1 }]} numberOfLines={2}>{r.left}</Text>
                          <Text style={[styles.signalText, { color: theme.textTertiary, paddingHorizontal: 6 }]}>→</Text>
                          <Text style={[styles.signalText, { color: theme.textSecondary, flexShrink: 1, textAlign: 'right' }]} numberOfLines={2}>{r.right}</Text>
                        </View>
                      ))}
                      {animLabel ? (
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 }}>
                          <Text style={[styles.signalText, { color: theme.textSecondary }]}>Year Animals</Text>
                          <Text style={[styles.signalText, { color: theme.text }]}>{animLabel}</Text>
                        </View>
                      ) : null}
                    </View>

                    {/* 2. WHAT STRENGTHENS THE FLOW */}
                    {support.length > 0 ? (
                      <View style={card}>
                        <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>2 · WHAT STRENGTHENS THE FLOW</Text>
                        {support.map((item, i) => (
                          <View key={`ev-s-${i}`} style={{ marginBottom: 8 }}>
                            <View style={{ flexDirection: 'row' }}>
                              <Text style={[styles.signalText, { color: '#81C784', paddingLeft: 0, width: 18 }]}>✓</Text>
                              <Text style={[labelText, { color: theme.text, flexShrink: 1 }]}>{EL.labelFor(cycle, 'strengthen', i)}</Text>
                            </View>
                            <Text style={[styles.signalText, { color: theme.textSecondary, paddingLeft: 18 }]}>{item}</Text>
                          </View>
                        ))}
                      </View>
                    ) : null}

                    {/* 3. GROWTH TRIGGER */}
                    {growth.length > 0 ? (
                      <View style={card}>
                        <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>3 · GROWTH TRIGGER</Text>
                        {animA && animB ? (
                          <Text style={[labelText, { color: theme.text, marginBottom: 4 }]}>↑  {animA}  ↔  {animB}</Text>
                        ) : null}
                        <Text style={[styles.signalText, { color: theme.textTertiary, fontStyle: 'italic', marginBottom: 8 }]}>{growthSub}</Text>
                        {growth.map((item, i) => (
                          <View key={`ev-g-${i}`} style={{ marginBottom: 8 }}>
                            <View style={{ flexDirection: 'row' }}>
                              <Text style={[styles.signalText, { color: '#90CAF9', paddingLeft: 0, width: 18 }]}>↑</Text>
                              <Text style={[labelText, { color: theme.text, flexShrink: 1 }]}>{EL.labelFor(cycle, 'growth', i)}</Text>
                            </View>
                            <Text style={[styles.signalText, { color: theme.textSecondary, paddingLeft: 18 }]}>{item}</Text>
                          </View>
                        ))}
                      </View>
                    ) : null}

                    {/* 4. SHADOW SIGNAL — hidden when tension is empty */}
                    {tension.length > 0 ? (
                      <View style={card}>
                        <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>4 · SHADOW SIGNAL</Text>
                        {tension.map((item, i) => (
                          <View key={`ev-t-${i}`} style={{ marginBottom: 8 }}>
                            <View style={{ flexDirection: 'row' }}>
                              <Text style={[styles.signalText, { color: '#CF6679', paddingLeft: 0, width: 18 }]}>⚠</Text>
                              <Text style={[labelText, { color: theme.text, flexShrink: 1 }]}>{EL.labelFor(cycle, 'shadow', i)}</Text>
                            </View>
                            <Text style={[styles.signalText, { color: theme.textSecondary, paddingLeft: 18 }]}>{item}</Text>
                          </View>
                        ))}
                      </View>
                    ) : null}
                  </View>
                );
              })()}
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
