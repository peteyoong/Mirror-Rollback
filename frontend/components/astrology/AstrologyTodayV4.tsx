/**
 * AstrologyTodayV4 — Behavior-First Interception Engine (Frontend)
 * =================================================================
 * Renders the v4 unified narrative from /api/astrology/today-v4/{userId}.
 *
 * Visual order (reads as ONE diagnosis, not disconnected sections):
 *   HEADLINE        — tension-based pattern recognition
 *   WHAT'S HAPPENING — single paragraph (causal synthesis)
 *   HOW IT SHOWS UP — 2-4 behavioral bullets
 *   WHAT IT FEELS LIKE — 2-4 somatic/emotional bullets
 *   THE RISK        — single sharp consequence line (emphasized card)
 *   THE MOVE        — single actionable interrupt (primary card)
 *   TIME LAYER      — today / this week / this month (compact rows)
 *   WHY IT'S SHOWING UP — collapsed accordion (signal → effect)
 *   TECHNICAL       — existing proof layer (secondary, collapsed)
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { InsightCardFooter } from '../InsightCardFooter';

interface TimeLayer {
  today?: string;
  this_week?: string;
  this_month?: string;
}

interface WhyRow {
  signal: string;
  effect: string;
}

interface Technical {
  dominant_pattern?: string;
  pattern_detail?: string;
  active_transits?: string[];
  sign_emphasis?: string[];
  house_emphasis?: string[];
  slow_planet_backdrop?: string[];
  transit_info?: string;
}

interface AstrologyTodayV4Data {
  version?: string;
  headline: string;
  whats_happening: string;
  how_it_shows_up: string[];
  what_it_feels_like: string[];
  the_risk: string;
  the_move: string;
  time_layer: TimeLayer;
  why_showing_up: WhyRow[];
  technical?: Technical;
  intensity?: string;
  tension_type?: string;
  day_class?: string;
  llm_fallback?: boolean;
  distortion_layer?: { active?: boolean; reason?: string };
}

interface AstrologyTodayV4Props {
  userId: string;
  theme: any;
  onReflect?: (question: string) => void;
}

const BACKEND_BASE_URL =
  Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL ||
  process.env.EXPO_PUBLIC_BACKEND_URL ||
  '';
const APP_BASE = typeof window !== 'undefined' ? '' : BACKEND_BASE_URL;

const BulletRow: React.FC<{ text: string; theme: any }> = ({ text, theme }) => (
  <View style={styles.bulletRow}>
    <View style={[styles.bulletDot, { backgroundColor: theme.textTertiary }]} />
    <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{text}</Text>
  </View>
);

const SectionHeader: React.FC<{ title: string; icon: any; theme: any }> = ({
  title,
  icon,
  theme,
}) => (
  <View style={styles.sectionHeader}>
    <Ionicons name={icon} size={16} color={theme.textTertiary} />
    <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>{title}</Text>
  </View>
);

const AstrologyTodayV4: React.FC<AstrologyTodayV4Props> = ({ userId, theme, onReflect }) => {
  const [data, setData] = useState<AstrologyTodayV4Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [whyOpen, setWhyOpen] = useState(false);
  const [techOpen, setTechOpen] = useState(false);

  useEffect(() => {
    load();
  }, [userId]);

  const load = async () => {
    try {
      setLoading(true);
      setErr(null);
      const res = await fetch(`${APP_BASE}/api/astrology/today-v4/${userId}`);
      if (!res.ok) throw new Error('Failed to load today intelligence');
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      console.error('[AstrologyTodayV4] Error:', e);
      setErr(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading today's pattern...
        </Text>
      </View>
    );
  }

  if (err) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{err}</Text>
        <TouchableOpacity onPress={load}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!data) return null;

  const intensityBadge =
    data.intensity === 'extreme' || data.day_class === 'stellium' ? (
      <View style={[styles.intensityBadge, { borderColor: theme.accent + '80' }]}>
        <Text style={[styles.intensityBadgeText, { color: theme.accent }]}>
          NOT A NORMAL DAY
        </Text>
      </View>
    ) : null;

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
        {/* HEADLINE */}
        <View style={styles.headlineSection}>
          {intensityBadge}
          <Text style={[styles.headlineText, { color: theme.text }]}>{data.headline}</Text>
        </View>

        {/* WHAT'S HAPPENING — paragraph */}
        {!!data.whats_happening && (
          <View style={styles.paragraphSection}>
            <Text style={[styles.paragraphText, { color: theme.text }]}>{data.whats_happening}</Text>
          </View>
        )}

        {/* HOW IT SHOWS UP */}
        {data.how_it_shows_up?.length > 0 && (
          <View style={[styles.section, styles.highlightedSection, { backgroundColor: theme.cardBackground || theme.background }]}>
            <SectionHeader title="How this shows up for you" icon="person-outline" theme={theme} />
            {data.how_it_shows_up.map((b, i) => (
              <BulletRow key={`h-${i}`} text={b} theme={theme} />
            ))}
          </View>
        )}

        {/* WHAT IT FEELS LIKE */}
        {data.what_it_feels_like?.length > 0 && (
          <View style={styles.section}>
            <SectionHeader title="What it may feel like" icon="heart-outline" theme={theme} />
            {data.what_it_feels_like.map((b, i) => (
              <BulletRow key={`f-${i}`} text={b} theme={theme} />
            ))}
          </View>
        )}

        {/* THE RISK — emphasized warning card */}
        {!!data.the_risk && (
          <View style={[styles.riskCard, { backgroundColor: (theme.accent || '#C49A6C') + '10', borderColor: (theme.accent || '#C49A6C') + '40' }]}>
            <Text style={[styles.riskLabel, { color: theme.accent }]}>THE RISK</Text>
            <Text style={[styles.riskText, { color: theme.text }]}>{data.the_risk}</Text>
          </View>
        )}

        {/* THE MOVE — primary action */}
        {!!data.the_move && (
          <View style={[styles.moveSection, { borderLeftColor: theme.accent }]}>
            <Text style={[styles.moveLabel, { color: theme.textTertiary }]}>THE MOVE</Text>
            <Text style={[styles.moveText, { color: theme.text }]}>{data.the_move}</Text>
          </View>
        )}

        {/* TIME LAYER — compact rows */}
        {data.time_layer && (
          <View style={styles.timeLayerSection}>
            <SectionHeader title="Why it's active now" icon="time-outline" theme={theme} />
            <View style={styles.timeRow}>
              <Text style={[styles.timeLabel, { color: theme.textTertiary }]}>Today</Text>
              <Text style={[styles.timeValue, { color: theme.text }]}>{data.time_layer.today || '—'}</Text>
            </View>
            <View style={styles.timeRow}>
              <Text style={[styles.timeLabel, { color: theme.textTertiary }]}>This week</Text>
              <Text style={[styles.timeValue, { color: theme.text }]}>{data.time_layer.this_week || '—'}</Text>
            </View>
            <View style={styles.timeRow}>
              <Text style={[styles.timeLabel, { color: theme.textTertiary }]}>This month</Text>
              <Text style={[styles.timeValue, { color: theme.text }]}>{data.time_layer.this_month || '—'}</Text>
            </View>
          </View>
        )}

        {/* WHY IT'S SHOWING UP — collapsible accordion */}
        {data.why_showing_up?.length > 0 && (
          <>
            <TouchableOpacity
              style={[styles.accordionToggle, { borderColor: theme.border }]}
              onPress={() => setWhyOpen((v) => !v)}
              activeOpacity={0.7}
            >
              <Text style={[styles.accordionToggleText, { color: theme.textTertiary }]}>
                {whyOpen ? 'Hide signal map' : "Why it's showing up (signal map)"}
              </Text>
              <Ionicons
                name={whyOpen ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textTertiary}
              />
            </TouchableOpacity>
            {whyOpen && (
              <View style={[styles.whySection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
                {data.why_showing_up.map((row, i) => (
                  <View key={`w-${i}`} style={styles.whyRow}>
                    <Text style={[styles.whySignal, { color: theme.text }]}>{row.signal}</Text>
                    <Text style={[styles.whyArrow, { color: theme.textTertiary }]}> → </Text>
                    <Text style={[styles.whyEffect, { color: theme.textSecondary }]}>{row.effect}</Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}

        {/* TECHNICAL — secondary accordion */}
        {data.technical && (
          <>
            <TouchableOpacity
              style={[styles.accordionToggle, { borderColor: theme.border }]}
              onPress={() => setTechOpen((v) => !v)}
              activeOpacity={0.7}
            >
              <Text style={[styles.accordionToggleText, { color: theme.textTertiary }]}>
                {techOpen ? 'Hide technical detail' : 'Technical detail'}
              </Text>
              <Ionicons
                name={techOpen ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textTertiary}
              />
            </TouchableOpacity>
            {techOpen && (
              <View style={[styles.technicalSection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
                {!!data.technical.dominant_pattern && (
                  <View style={{ marginBottom: 12 }}>
                    <Text style={[styles.technicalLabel, { color: theme.textTertiary }]}>DOMINANT PATTERN</Text>
                    <Text style={[styles.technicalText, { color: theme.text, fontWeight: '600' }]}>
                      {data.technical.dominant_pattern}
                    </Text>
                    {!!data.technical.pattern_detail && (
                      <Text style={[styles.technicalText, { color: theme.textSecondary, marginTop: 2 }]}>
                        {data.technical.pattern_detail}
                      </Text>
                    )}
                  </View>
                )}
                {!!data.technical.active_transits?.length && (
                  <View style={{ marginBottom: 12 }}>
                    <Text style={[styles.proofSectionLabel, { color: theme.textTertiary }]}>ACTIVE TRANSITS</Text>
                    {data.technical.active_transits.map((t, i) => (
                      <Text key={i} style={[styles.proofItem, { color: theme.textSecondary }]}>{t}</Text>
                    ))}
                  </View>
                )}
                {!!data.technical.sign_emphasis?.length && (
                  <View style={{ marginBottom: 12 }}>
                    <Text style={[styles.proofSectionLabel, { color: theme.textTertiary }]}>SIGN CONCENTRATION</Text>
                    {data.technical.sign_emphasis.map((t, i) => (
                      <Text key={i} style={[styles.proofItem, { color: theme.textSecondary }]}>{t}</Text>
                    ))}
                  </View>
                )}
                {!!data.technical.house_emphasis?.length && (
                  <View style={{ marginBottom: 12 }}>
                    <Text style={[styles.proofSectionLabel, { color: theme.textTertiary }]}>LIFE AREAS ACTIVATED</Text>
                    {data.technical.house_emphasis.map((t, i) => (
                      <Text key={i} style={[styles.proofItem, { color: theme.textSecondary }]}>{t}</Text>
                    ))}
                  </View>
                )}
                {!!data.technical.slow_planet_backdrop?.length && (
                  <View style={{ marginBottom: 4 }}>
                    <Text style={[styles.proofSectionLabel, { color: theme.textTertiary }]}>LONGER-CYCLE BACKDROP</Text>
                    {data.technical.slow_planet_backdrop.map((t, i) => (
                      <Text key={i} style={[styles.proofItem, { color: theme.textTertiary }]}>{t}</Text>
                    ))}
                  </View>
                )}
              </View>
            )}
          </>
        )}

        {/* Insight footer (reflect CTA) */}
        <InsightCardFooter
          source={{
            lens: 'astrology',
            type: 'today_v4',
            name: data.headline,
            value: data.the_move,
            id: `astro_today_v4_${new Date().toISOString().slice(0, 10)}`,
          }}
          patternSignature={`astro_today_v4_${new Date().toISOString().slice(0, 10)}`}
          context="astrology_today_v4"
          prompt={`Looking at today: "${data.headline}" — what comes up for you?`}
          showBorder={true}
          borderColor={theme.border}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { padding: 40, alignItems: 'center', gap: 12 },
  loadingText: { fontSize: 16 },
  errorContainer: { padding: 24, alignItems: 'center', gap: 12 },
  errorText: { fontSize: 16, textAlign: 'center' },
  retryText: { fontSize: 16, fontWeight: '600' },

  card: { margin: 16, padding: 20, borderRadius: 16, borderWidth: 1 },

  intensityBadge: {
    alignSelf: 'flex-start',
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
    marginBottom: 10,
  },
  intensityBadgeText: { fontSize: 10, fontWeight: '700', letterSpacing: 1 },

  headlineSection: { marginBottom: 20 },
  headlineText: { fontSize: 24, fontWeight: '600', lineHeight: 31 },

  paragraphSection: { marginBottom: 22 },
  paragraphText: { fontSize: 17, lineHeight: 27 },

  section: { marginBottom: 22 },
  highlightedSection: { padding: 16, borderRadius: 12, marginHorizontal: -4 },

  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 12 },
  sectionTitle: { fontSize: 13, fontWeight: '600', letterSpacing: 0.6, textTransform: 'uppercase' },

  bulletRow: { flexDirection: 'row', paddingLeft: 4, marginBottom: 10 },
  bulletDot: { width: 5, height: 5, borderRadius: 2.5, marginTop: 10, marginRight: 10 },
  bulletText: { flex: 1, fontSize: 16, lineHeight: 26 },

  riskCard: {
    padding: 14,
    borderRadius: 10,
    marginBottom: 20,
    borderWidth: 1,
  },
  riskLabel: { fontSize: 11, fontWeight: '700', letterSpacing: 1, marginBottom: 6 },
  riskText: { fontSize: 16, lineHeight: 24, fontWeight: '500' },

  moveSection: { paddingLeft: 16, borderLeftWidth: 3, marginBottom: 22 },
  moveLabel: { fontSize: 12, fontWeight: '700', letterSpacing: 0.8, marginBottom: 10 },
  moveText: { fontSize: 17, fontWeight: '500', lineHeight: 26, fontStyle: 'italic' },

  timeLayerSection: { marginBottom: 10, paddingTop: 6 },
  timeRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 10, paddingLeft: 4 },
  timeLabel: { width: 86, fontSize: 13, fontWeight: '500' },
  timeValue: { flex: 1, fontSize: 15, lineHeight: 22 },

  accordionToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 6,
  },
  accordionToggleText: { fontSize: 14 },

  whySection: { padding: 12, borderRadius: 8, borderWidth: StyleSheet.hairlineWidth, marginTop: 8 },
  whyRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 8 },
  whySignal: { fontSize: 13, fontWeight: '500' },
  whyArrow: { fontSize: 13 },
  whyEffect: { fontSize: 13 },

  technicalSection: { padding: 14, borderRadius: 8, borderWidth: StyleSheet.hairlineWidth, marginTop: 8 },
  technicalLabel: { fontSize: 11, fontWeight: '700', letterSpacing: 0.9, marginBottom: 6, textTransform: 'uppercase' },
  technicalText: { fontSize: 14, lineHeight: 22 },
  proofSectionLabel: { fontSize: 11, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 },
  proofItem: { fontSize: 13, lineHeight: 20, marginBottom: 3, paddingLeft: 4 },
});

export default AstrologyTodayV4;
