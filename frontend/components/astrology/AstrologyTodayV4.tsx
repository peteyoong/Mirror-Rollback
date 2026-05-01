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

// ---------------------------------------------------------------------------
// v5 proof-payload shape (from /api/astrology/today-v5)
// ---------------------------------------------------------------------------
//
// The v5 backend exposes a richer signal map that includes lunation,
// ingress, and outer-planet activity — categories the v4 frontend
// signal map was previously blind to. We fetch v5 in parallel with
// v4 (cheap, deterministic, ~30ms) and merge its categorical signals
// into the top of the existing "Why it's showing up" accordion.
//
// v4 narrative remains the source of truth for the user-facing text;
// v5 only contributes proof-layer rows.

interface V5DominantSignal {
  type?: string;
  label?: string;
  planet?: string;
  from_sign?: string;
  to_sign?: string;
  hours?: number;
  days?: number;
  at_utc?: string;
  transit?: string;
  aspect?: string;
  natal?: string;
  orb?: number;
  applying?: boolean;
  house?: number;
  bodies?: string[];
  sign?: string;
  transit_sign?: string;
  natal_sign?: string;
}

interface V5MoonPhase {
  phase_human?: string;
  phase_key?: string;
  sun_moon_angle_deg?: number;
  nearest_full_moon?: { hours_offset?: number; within_48h?: boolean; within_7d?: boolean } | null;
  nearest_new_moon?:  { hours_offset?: number; within_48h?: boolean; within_7d?: boolean } | null;
}

interface V5Proof {
  dominant_signal?: V5DominantSignal | null;
  secondary_signals?: V5DominantSignal[];
  background_signals?: V5DominantSignal[];
  active_categories?: string[];
  signal_conflict?: boolean;
  intensity?: string;
  moon_phase?: V5MoonPhase;
  tight_aspect_count?: number;
  aspect_count?: number;
  outer_backdrop?: { planet: string; sign: string; retrograde?: boolean }[];
}

interface TheMove {
  action?: string;
  reflection?: string;
}

interface AstrologyTodayV4Data {
  version?: string;
  headline: string;
  whats_happening: string;
  how_it_shows_up: string[];
  what_it_feels_like: string[];
  the_risk: string;
  the_move: TheMove | string;
  time_layer: TimeLayer;
  why_showing_up: WhyRow[];
  technical?: Technical;
  intensity?: string;
  tension_type?: string;
  day_class?: string;
  is_extreme_day?: boolean;
  llm_fallback?: boolean;
  distortion_layer?: {
    active?: boolean;
    reason?: string;
    label?: string;
    has_ophiuchus?: boolean;
    ophiuchus_bodies?: string[];
    has_divergence?: boolean;
    divergent_bodies?: { body: string; zodiac_sign: string; constellation: string }[];
  };
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

// ---------------------------------------------------------------------------
// v5 → signal-map row builder
// ---------------------------------------------------------------------------
//
// Order priority (per user spec):
//   1. Tier 1 lunation (Full Moon / New Moon ±48h)
//   2. Tier 1 outer-planet ingress
//   3. Heavy ingress (Saturn / Jupiter ±7d)
//   4. Personal ingress (Mercury / Venus / Mars ±3d)
//   5. Tight aspects + clusters appear via the existing v4 rows
//      (we don't double-render those here).
//   6. Outer-planet backdrop derived from secondary_signals
//
// If `active_categories` includes a category but no row was produced
// (e.g. payload lacks moon_phase detail), we emit a debug fallback
// row so the signal map never silently omits a backend-detected
// category.

interface V5SignalRow { signal: string; effect: string }

function _hoursPhrase(h?: number): string {
  if (typeof h !== 'number' || !isFinite(h)) return '';
  const abs = Math.abs(h);
  if (abs < 1) {
    return h > 0 ? 'within the next hour' : 'just now';
  }
  if (abs < 48) {
    const rounded = Math.round(abs);
    return h > 0 ? `in ${rounded}h` : `${rounded}h ago`;
  }
  const days = Math.round(abs / 24);
  return h > 0 ? `in ${days}d` : `${days}d ago`;
}

function _signalForLunation(mp: V5MoonPhase | undefined): V5SignalRow | null {
  if (!mp) return null;
  const fm = mp.nearest_full_moon;
  const nm = mp.nearest_new_moon;
  if (fm && fm.within_48h) {
    const h = fm.hours_offset;
    const when = _hoursPhrase(h);
    const verb = (typeof h === 'number' && h < 0) ? `peaked ${when}` : `active ${when}`;
    return {
      signal: `Full Moon ${verb}`,
      effect: 'culmination / visibility peak — something is reaching a point where it can be seen',
    };
  }
  if (nm && nm.within_48h) {
    const h = nm.hours_offset;
    const when = _hoursPhrase(h);
    const verb = (typeof h === 'number' && h < 0) ? `passed ${when}` : `active ${when}`;
    return {
      signal: `New Moon ${verb}`,
      effect: 'seeding window — quiet ground for what wants to begin, not for proving',
    };
  }
  return null;
}

function _ingressEffect(planet?: string): string {
  switch (planet) {
    case 'Uranus':
      return 'long-cycle shift in communication, ideas, networks — disruption and reinvention';
    case 'Neptune':
      return 'long-cycle shift in meaning, dissolving old certainties';
    case 'Pluto':
      return 'long-cycle shift in power, control, and what has to be released';
    case 'Saturn':
      return 'structural pressure shift — what holds weight is being reorganised';
    case 'Jupiter':
      return 'expansion shift — where growth and excess will gather next';
    case 'Mars':
      return 'short-cycle shift in drive and how you push';
    case 'Venus':
      return 'short-cycle shift in connection, attraction, and value';
    case 'Mercury':
      return 'short-cycle shift in pace, speech, and decision-making';
    case 'Sun':
      return 'monthly chapter change — the focus of the month rotates';
    case 'Moon':
      return 'short emotional frame change';
    default:
      return 'new long-cycle emphasis is opening';
  }
}

function _signalForIngress(sig: V5DominantSignal | undefined): V5SignalRow | null {
  if (!sig) return null;
  if (!sig.type || !sig.planet || !sig.to_sign) return null;
  if (!['outer_ingress', 'heavy_ingress', 'personal_ingress'].includes(sig.type)) return null;
  const days = sig.days;
  const when = (typeof days === 'number' && Math.abs(days) > 0.1)
    ? (days > 0 ? `in ${Math.round(days * 10) / 10}d` : `${Math.round(Math.abs(days) * 10) / 10}d ago`)
    : 'today';
  return {
    signal: `${sig.planet} → ${sig.to_sign} (${when})`,
    effect: _ingressEffect(sig.planet),
  };
}

function _signalForOuterBackdrop(sig: V5DominantSignal | undefined): V5SignalRow | null {
  if (!sig) return null;
  // Surface outer-planet sign placement when it appears in
  // secondary/background. Skip if it's already represented as an
  // ingress row.
  if (sig.type === 'outer_ingress') return null;
  const planet = sig.planet || sig.transit;
  if (!planet || !['Uranus', 'Neptune', 'Pluto'].includes(planet)) return null;
  const sign = sig.sign || sig.to_sign || sig.transit_sign;
  if (!sign) return null;
  return {
    signal: `${planet} in ${sign}`,
    effect: _ingressEffect(planet),
  };
}

function buildV5SignalRows(proof: V5Proof | null): V5SignalRow[] {
  if (!proof) return [];
  const rows: V5SignalRow[] = [];
  const seen = new Set<string>();
  const push = (r: V5SignalRow | null) => {
    if (!r) return;
    const k = r.signal.toLowerCase();
    if (seen.has(k)) return;
    seen.add(k);
    rows.push(r);
  };

  // 1. Lunation
  push(_signalForLunation(proof.moon_phase));

  // 2-4. Ingresses — dominant first, then secondary
  push(_signalForIngress(proof.dominant_signal || undefined));
  for (const s of proof.secondary_signals || []) {
    push(_signalForIngress(s));
  }

  // 5. Outer-planet backdrop — first from explicit outer_backdrop list
  //    (always populated from current sky), then from secondary signals.
  for (const ob of proof.outer_backdrop || []) {
    if (ob?.planet && ob?.sign) {
      push({
        signal: `${ob.planet} in ${ob.sign}${ob.retrograde ? ' (retrograde)' : ''}`,
        effect: _ingressEffect(ob.planet),
      });
    }
  }
  for (const s of proof.secondary_signals || []) {
    push(_signalForOuterBackdrop(s));
  }
  for (const s of proof.background_signals || []) {
    push(_signalForOuterBackdrop(s));
  }

  // Fallback rows: if backend says a category is active but we
  // produced no row, surface a debug placeholder so we never silently
  // omit a detected signal.
  const cats = (proof.active_categories || []).map((c) => c.toLowerCase());
  const haveLunation = rows.some((r) => /(full|new) moon/i.test(r.signal));
  const haveIngress  = rows.some((r) => /→/.test(r.signal));
  if (cats.includes('lunation') && !haveLunation) {
    rows.unshift({
      signal: 'Lunation signal detected',
      effect: 'details unavailable in proof payload',
    });
  }
  if (cats.includes('ingress') && !haveIngress) {
    rows.push({
      signal: 'Ingress signal detected',
      effect: 'details unavailable in proof payload',
    });
  }

  return rows;
}

const AstrologyTodayV4: React.FC<AstrologyTodayV4Props> = ({ userId, theme, onReflect }) => {
  const [data, setData] = useState<AstrologyTodayV4Data | null>(null);
  const [v5Proof, setV5Proof] = useState<V5Proof | null>(null);
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
      // Fetch v4 narrative and v5 proof in parallel. v5 is best-effort —
      // any failure leaves the existing v4 signal map intact.
      const [v4Res, v5Res] = await Promise.allSettled([
        fetch(`${APP_BASE}/api/astrology/today-v4/${userId}`),
        fetch(`${APP_BASE}/api/astrology/today-v5/${userId}`),
      ]);

      if (v4Res.status === 'fulfilled' && v4Res.value.ok) {
        const json = await v4Res.value.json();
        setData(json);
      } else {
        throw new Error('Failed to load today intelligence');
      }

      if (v5Res.status === 'fulfilled' && v5Res.value.ok) {
        try {
          const v5json = await v5Res.value.json();
          const proof: V5Proof = v5json?.why_this_is_showing_up || {};
          // signal_conflict + active_categories live one level up — pull
          // them in for the fallback-row branch.
          if (typeof v5json?.signal_conflict !== 'undefined' && proof.signal_conflict === undefined) {
            proof.signal_conflict = !!v5json.signal_conflict;
          }
          setV5Proof(proof);
        } catch (parseErr) {
          // eslint-disable-next-line no-console
          console.warn('[AstrologyTodayV4] v5 proof parse failed', parseErr);
          setV5Proof(null);
        }
      } else {
        setV5Proof(null);
      }
    } catch (e: any) {
      // eslint-disable-next-line no-console
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
    data.is_extreme_day || data.intensity === 'extreme' || data.day_class === 'stellium' ? (
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
          <View style={styles.badgeRow}>
            {intensityBadge}
            {data.distortion_layer?.active && (
              <View style={[styles.overlayBadge, { borderColor: theme.textTertiary + '60' }]}>
                <Ionicons name="layers-outline" size={10} color={theme.textTertiary} />
                <Text style={[styles.overlayBadgeText, { color: theme.textTertiary }]}>
                  {data.distortion_layer.label || 'Constellation overlay active'}
                </Text>
              </View>
            )}
          </View>
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

        {/* THE MOVE — TWO LAYERS: Action + Reflection */}
        {(() => {
          const mv = data.the_move;
          const action = typeof mv === 'string' ? mv : (mv?.action || '');
          const reflection = typeof mv === 'string' ? '' : (mv?.reflection || '');
          if (!action && !reflection) return null;
          return (
            <View style={[styles.moveSection, { borderLeftColor: theme.accent }]}>
              <Text style={[styles.moveLabel, { color: theme.textTertiary }]}>THE MOVE</Text>
              {!!action && (
                <View style={styles.moveLayer}>
                  <Text style={[styles.moveLayerTag, { color: theme.accent }]}>ACTION</Text>
                  <Text style={[styles.moveText, { color: theme.text }]}>{action}</Text>
                </View>
              )}
              {!!reflection && (
                <View style={styles.moveLayer}>
                  <Text style={[styles.moveLayerTag, { color: theme.accent }]}>REFLECT</Text>
                  <Text style={[styles.moveTextItalic, { color: theme.text }]}>{reflection}</Text>
                </View>
              )}
            </View>
          );
        })()}

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
        {(data.why_showing_up?.length > 0 || (v5Proof && (v5Proof.dominant_signal || v5Proof.moon_phase || (v5Proof.active_categories || []).length))) && (
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
                size={20}
                color={theme.textTertiary}
              />
            </TouchableOpacity>
            {whyOpen && (
              <View style={[styles.whySection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
                {/* v5 categorical signals — lunation / ingress / outer-planet
                    backdrop. These are surfaced from /today-v5's proof
                    payload. The main narrative remains jargon-free; the
                    signal map is allowed to show astrology terms. */}
                {(() => {
                  const rows = buildV5SignalRows(v5Proof);
                  if (rows.length === 0) return null;
                  return (
                    <View style={[styles.v5HeadBlock, { borderBottomColor: theme.border }]}>
                      <Text style={[styles.v5HeadLabel, { color: theme.textTertiary }]}>
                        ACTIVE TIMING SIGNALS
                      </Text>
                      {rows.map((row, i) => (
                        <View key={`v5-${i}`} style={styles.whyRow}>
                          <Text style={[styles.whySignal, { color: theme.text }]}>{row.signal}</Text>
                          <Text style={[styles.whyArrow, { color: theme.textTertiary }]}> → </Text>
                          <Text style={[styles.whyEffect, { color: theme.textSecondary }]}>{row.effect}</Text>
                        </View>
                      ))}
                    </View>
                  );
                })()}
                {data.why_showing_up?.map((row, i) => (
                  <View key={`w-${i}`} style={styles.whyRow}>
                    <Text style={[styles.whySignal, { color: theme.text }]}>{row.signal}</Text>
                    <Text style={[styles.whyArrow, { color: theme.textTertiary }]}> → </Text>
                    <Text style={[styles.whyEffect, { color: theme.textSecondary }]}>{row.effect}</Text>
                  </View>
                ))}
                {/* Constellation overlay divergence rows — hidden in accordion */}
                {data.distortion_layer?.active && (data.distortion_layer?.divergent_bodies?.length || data.distortion_layer?.ophiuchus_bodies?.length) ? (
                  <View style={[styles.divergenceBlock, { borderTopColor: theme.border }]}>
                    <Text style={[styles.divergenceHeader, { color: theme.textTertiary }]}>
                      SKY vs MODEL
                    </Text>
                    {(data.distortion_layer.ophiuchus_bodies || []).map((b, i) => (
                      <View key={`o-${i}`} style={styles.whyRow}>
                        <Text style={[styles.whySignal, { color: theme.text }]}>{b}</Text>
                        <Text style={[styles.whyArrow, { color: theme.textTertiary }]}> → </Text>
                        <Text style={[styles.whyEffect, { color: theme.textSecondary }]}>
                          passing through Ophiuchus (between Scorpius and Sagittarius)
                        </Text>
                      </View>
                    ))}
                    {(data.distortion_layer.divergent_bodies || []).slice(0, 4).map((row, i) => (
                      <View key={`dv-${i}`} style={styles.whyRow}>
                        <Text style={[styles.whySignal, { color: theme.text }]}>
                          {row.body}
                        </Text>
                        <Text style={[styles.whyArrow, { color: theme.textTertiary }]}> → </Text>
                        <Text style={[styles.whyEffect, { color: theme.textSecondary }]}>
                          {row.zodiac_sign} in model · {row.constellation} in sky
                        </Text>
                      </View>
                    ))}
                  </View>
                ) : null}
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
                size={20}
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
            value: (() => {
              const mv = data.the_move;
              if (typeof mv === 'string') return mv;
              return [mv?.action, mv?.reflection].filter(Boolean).join(' · ');
            })(),
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

  badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 6 },
  overlayBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
    marginBottom: 10,
  },
  overlayBadgeText: { fontSize: 10, fontWeight: '600', letterSpacing: 0.6 },

  divergenceBlock: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  divergenceHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },

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
  moveLayer: { marginBottom: 12 },
  moveLayerTag: { fontSize: 10, fontWeight: '700', letterSpacing: 1, marginBottom: 4 },
  moveText: { fontSize: 16, fontWeight: '500', lineHeight: 25 },
  moveTextItalic: { fontSize: 16, fontWeight: '500', lineHeight: 25, fontStyle: 'italic' },

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
  v5HeadBlock: {
    paddingBottom: 10,
    marginBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  v5HeadLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
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
