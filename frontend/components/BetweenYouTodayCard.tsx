/**
 * BetweenYouTodayCard
 * ====================
 * Relationship Timing Layer v1 — daily modulation card that sits ABOVE
 * the Relationship Field architecture in the mapping detail screen.
 *
 * Sections:
 *   1. HERO            — 1–3 sentences, retention hook
 *   2. ACTIVATED TODAY — short bullets
 *   3. DISTORTION RISK — short bullets
 *   4. WHAT SOFTENS    — short bullets
 *   5. WHY THIS IS SHOWING UP — collapsible proof drawer with
 *        plain ↔ technical toggle
 *
 * Loading: inline shimmer; never blocks the underlying field card.
 * Error: silent fallback (we just don't render). The mapping screen
 * stays functional even when today's modulation can't be computed.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getBetweenYouToday, BetweenYouToday, postBetweenYouTodayEvent } from '../services/api';

interface ThemeShape {
  background: string;
  surface: string;
  surfaceLight?: string;
  border: string;
  text: string;
  textSecondary: string;
  textTertiary: string;
  accent?: string;
}

interface Props {
  forumId: string;
  userId: string;
  memberId: string;
  memberName: string;
  theme: ThemeShape;
  /**
   * Optional subtle undertone line (KG-derived) rendered beneath the
   * transit-driven hero. Per product spec v1.5.2 the hero MUST come
   * from today/transits; this undertone is supplementary.
   */
  undertone?: string;
}

const intensityChipStyle = (level: 'low' | 'medium' | 'high', accent: string) => {
  switch (level) {
    case 'high':
      return { bg: accent + '22', fg: accent, label: 'Strong today' };
    case 'medium':
      return { bg: accent + '14', fg: accent, label: 'Noticeable today' };
    default:
      return { bg: accent + '08', fg: accent + 'CC', label: 'Quiet today' };
  }
};

const BetweenYouTodayCard: React.FC<Props> = ({
  forumId,
  userId,
  memberId,
  memberName,
  theme,
  undertone,
}) => {
  const accent = theme.accent || '#8B5CF6';
  const [today, setToday] = useState<BetweenYouToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [proofExpanded, setProofExpanded] = useState(false);
  const [proofMode, setProofMode] = useState<'plain' | 'technical'>('plain');

  useEffect(() => {
    let cancelled = false;
    const fetchToday = async () => {
      setLoading(true);
      try {
        const res = await getBetweenYouToday(forumId, userId, memberId);
        if (!cancelled && res.success && res.today) {
          setToday(res.today);
          // Telemetry — passive view event
          postBetweenYouTodayEvent(forumId, userId, memberId, 'today_card_viewed', {
            intensity: res.today.intensity,
            cache_hit: !!res.today._cache_hit,
            date: res.today.date,
          });
        }
      } catch (e) {
        // Silent — the field card below still loads.
        if (!cancelled) {
          // eslint-disable-next-line no-console
          console.warn('[BetweenYouToday] fetch failed', e);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchToday();
    return () => {
      cancelled = true;
    };
  }, [forumId, userId, memberId]);

  const handleToggleProof = () => {
    const next = !proofExpanded;
    setProofExpanded(next);
    postBetweenYouTodayEvent(
      forumId,
      userId,
      memberId,
      next ? 'proof_expanded' : 'proof_collapsed',
      {
        intensity: today?.intensity,
        date: today?.date,
        extra: { mode: proofMode },
      }
    );
  };

  const handleProofModeSwitch = (mode: 'plain' | 'technical') => {
    if (mode === proofMode) return;
    setProofMode(mode);
    postBetweenYouTodayEvent(forumId, userId, memberId, 'proof_mode_switched', {
      intensity: today?.intensity,
      date: today?.date,
      extra: { from: proofMode, to: mode },
    });
  };

  if (loading) {
    return (
      <View
        style={[
          styles.card,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <View style={styles.headerRow}>
          <Text style={[styles.eyebrow, { color: accent }]}>BETWEEN YOU TODAY</Text>
        </View>
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            reading today's field…
          </Text>
        </View>
      </View>
    );
  }

  if (!today) return null;

  const chip = intensityChipStyle(today.intensity, accent);

  const renderBullets = (
    items: string[],
    iconName: keyof typeof Ionicons.glyphMap,
    iconColor: string,
  ) => {
    if (!items || items.length === 0) return null;
    return (
      <View style={styles.bulletGroup}>
        {items.map((item, i) => (
          <View key={i} style={styles.bulletRow}>
            <Ionicons
              name={iconName}
              size={14}
              color={iconColor}
              style={styles.bulletIcon}
            />
            <Text style={[styles.bulletText, { color: theme.textSecondary }]}>
              {item}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  const proofItems =
    proofMode === 'plain'
      ? today.proof_layer?.plain_english || []
      : today.proof_layer?.technical || [];

  return (
    <View
      style={[
        styles.card,
        { backgroundColor: theme.surface, borderColor: theme.border },
      ]}
    >
      {/* Eyebrow + intensity chip */}
      <View style={styles.headerRow}>
        <Text style={[styles.eyebrow, { color: accent }]}>BETWEEN YOU TODAY</Text>
        <View style={[styles.intensityChip, { backgroundColor: chip.bg }]}>
          <Text style={[styles.intensityText, { color: chip.fg }]}>{chip.label}</Text>
        </View>
      </View>

      {/* HERO — the retention hook (transit-driven) */}
      <Text style={[styles.hero, { color: theme.text }]}>{today.hero}</Text>

      {/* Optional subtle KG-derived undertone (NEVER replaces the hero) */}
      {!!undertone && (
        <Text
          testID="between-you-today-undertone"
          style={{
            color: theme.textTertiary,
            fontStyle: 'italic',
            fontSize: 13,
            lineHeight: 19,
            marginTop: 4,
            marginBottom: 8,
          }}
        >
          {undertone}
        </Text>
      )}

      {/* WHAT'S ACTIVATED TODAY */}
      {today.activated_today && today.activated_today.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            WHAT'S ACTIVATED
          </Text>
          {renderBullets(today.activated_today, 'flash-outline', accent)}
        </View>
      )}

      {/* DISTORTION RISK */}
      {today.distortion_risk && today.distortion_risk.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            DISTORTION RISK
          </Text>
          {renderBullets(today.distortion_risk, 'alert-circle-outline', '#CF6679')}
        </View>
      )}

      {/* WHAT SOFTENS THE FIELD */}
      {today.softens_field && today.softens_field.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            WHAT SOFTENS THE FIELD
          </Text>
          {renderBullets(today.softens_field, 'leaf-outline', '#81C784')}
        </View>
      )}

      {/* WHY THIS IS SHOWING UP — collapsible proof drawer */}
      {(today.proof_layer?.plain_english?.length || today.proof_layer?.technical?.length) ? (
        <View style={styles.proofSection}>
          <TouchableOpacity
            style={[styles.proofToggle, { borderColor: theme.border }]}
            onPress={handleToggleProof}
            activeOpacity={0.7}
          >
            <Text style={[styles.proofToggleText, { color: theme.textSecondary }]}>
              {proofExpanded ? 'Hide why this is showing up' : 'Why this is showing up'}
            </Text>
            <Ionicons
              name={proofExpanded ? 'chevron-up' : 'chevron-down'}
              size={18}
              color={theme.textTertiary}
            />
          </TouchableOpacity>

          {proofExpanded && (
            <View style={styles.proofContent}>
              {/* Plain ↔ Technical mode toggle */}
              {today.proof_layer?.technical?.length ? (
                <View style={styles.modeRow}>
                  <TouchableOpacity
                    onPress={() => handleProofModeSwitch('plain')}
                    style={[
                      styles.modePill,
                      proofMode === 'plain' && { backgroundColor: accent + '22' },
                      { borderColor: theme.border },
                    ]}
                  >
                    <Text
                      style={[
                        styles.modePillText,
                        { color: proofMode === 'plain' ? accent : theme.textTertiary },
                      ]}
                    >
                      Plain
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => handleProofModeSwitch('technical')}
                    style={[
                      styles.modePill,
                      proofMode === 'technical' && { backgroundColor: accent + '22' },
                      { borderColor: theme.border },
                    ]}
                  >
                    <Text
                      style={[
                        styles.modePillText,
                        { color: proofMode === 'technical' ? accent : theme.textTertiary },
                      ]}
                    >
                      Technical
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : null}

              {proofItems.length === 0 ? (
                <Text style={[styles.proofEmpty, { color: theme.textTertiary }]}>
                  No additional detail to surface.
                </Text>
              ) : (
                proofItems.map((line, i) => (
                  <View key={i} style={styles.proofRow}>
                    <Text style={[styles.proofDot, { color: theme.textTertiary }]}>·</Text>
                    <Text
                      style={[
                        styles.proofLine,
                        {
                          color: theme.textSecondary,
                          fontFamily: proofMode === 'technical' ? 'Courier' : undefined,
                          fontSize: proofMode === 'technical' ? 12 : 13,
                        },
                      ]}
                    >
                      {line}
                    </Text>
                  </View>
                ))
              )}
            </View>
          )}
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 18,
    marginBottom: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1.2,
  },
  intensityChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  intensityText: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  hero: {
    fontSize: 18,
    lineHeight: 26,
    fontWeight: '500',
    marginBottom: 6,
  },
  section: {
    marginTop: 14,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  bulletGroup: {
    gap: 6,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  bulletIcon: {
    marginTop: 4,
    marginRight: 8,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  proofSection: {
    marginTop: 18,
  },
  proofToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderRadius: 8,
  },
  proofToggleText: {
    fontSize: 13,
    fontWeight: '500',
  },
  proofContent: {
    marginTop: 10,
    paddingHorizontal: 4,
  },
  modeRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
  },
  modePill: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  modePillText: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  proofRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  proofDot: {
    fontSize: 13,
    width: 12,
    textAlign: 'center',
    marginTop: 2,
  },
  proofLine: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
  proofEmpty: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
  },
  loadingText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
});

export default BetweenYouTodayCard;
