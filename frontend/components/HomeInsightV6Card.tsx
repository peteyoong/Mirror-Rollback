// ============================================================================
// HOME INSIGHT V6 — Today-Powered, Signal-First, Non-Generic
// ============================================================================
//
// Renders the 5-section Home contract anchored on the Astrology Today V5
// dominant signal:
//
//   1. THE CALL          — hero hook + tension line (1-2 lines max)
//   2. THE REALITY       — short paragraph behind the hook
//   3. WHERE THIS LANDS  — house arenas translated to plain language
//   4. THE EDGE          — non-prescriptive trajectory shift
//   5. CTA               — link to Astrology Today
//
// Source: /api/home-insight-v6/{user_id}
//
// Design principles:
//   - Reads in <5 seconds.
//   - Same truth as Today, different angle (zoomed-out).
//   - Tension framing, behavior-grounded, never generic.
//   - signature_hash + angle rotation handled server-side.
//
// Future extension hooks (rendered when payload.future_layers populates):
//   - pattern_memory     (lifeline echoes)
//   - relationship       (shared-pattern overlays)
//   - human_design_timing
//   - bazi
// ============================================================================

import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import api from '../services/api';
import { fontFamily } from '../theme/tokens';
import TimelineWhisper, { TimelineModulation } from './TimelineWhisper';

// ============================================
// Types
// ============================================

interface TodaySignal {
  label?: string | null;
  type?: string | null;
  intensity?: string | null;
  conflict?: boolean;
}

interface PatternMemoryBlock {
  available?: boolean;
  confidence?: 'low' | 'high' | string;
  theme?: string | null;
  summary?: string | null;
  source_type?: string | null;
  source_count?: number;
}

interface RelationalPatternBlock {
  available?: boolean;
  confidence?: 'low' | 'high' | string;
  type?: 'person' | 'context' | string;
  label?: string | null;
  summary?: string | null;
  source_count?: number;
  source_verified?: boolean;
  source_type?: string | null;
  theme?: string | null;
}

interface TimingCompressionBlock {
  available?: boolean;
  line?: string | null;
  bucket?: string | null;
}

interface HomeV6Payload {
  success?: boolean;
  version?: string;
  date?: string;
  signature_hash?: string;
  angle?: 'call' | 'reality' | 'edge';
  today_signal?: TodaySignal;
  the_call: string;
  the_reality: string;
  where_this_lands: string[];
  the_edge: string;
  cta?: string;
  pattern_memory?: PatternMemoryBlock;
  relational_pattern?: RelationalPatternBlock;
  timing_compression?: TimingCompressionBlock;
  proof?: {
    dominant_signal?: string | null;
    intensity?: string | null;
    signal_conflict?: boolean;
    house_clusters?: Array<{ house: number; bodies: string[] }>;
  };
  timeline_modulation?: TimelineModulation;
  generated_at?: string;
}

interface HomeV6CardProps {
  userId: string;
  theme: any;
  onCtaTap?: () => void;
}

// ============================================
// Component
// ============================================

const HomeInsightV6Card: React.FC<HomeV6CardProps> = ({
  userId,
  theme,
  onCtaTap,
}) => {
  const router = useRouter();
  const [data, setData] = useState<HomeV6Payload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/home-insight-v6/${userId}`);
      if (res?.data?.success) {
        setData(res.data);
      } else {
        throw new Error('Empty payload');
      }
    } catch (e: any) {
      // eslint-disable-next-line no-console
      console.warn('[HomeV6] load failed:', e?.message || e);
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCta = () => {
    if (onCtaTap) {
      onCtaTap();
      return;
    }
    // Default: open Astrology lens which surfaces Today
    try {
      router.push('/lenses/astrology');
    } catch {
      // no-op
    }
  };

  if (loading) {
    return (
      <View
        style={[
          styles.container,
          styles.center,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <ActivityIndicator size="small" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading what's happening…
        </Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View
        style={[
          styles.container,
          styles.center,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          Couldn't load right now.
        </Text>
        <TouchableOpacity onPress={load} style={styles.retryBtn}>
          <Text
            style={[
              styles.retryText,
              { color: theme.accent || theme.text },
            ]}
          >
            Retry
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  const accent = theme.accent || '#8B5CF6';
  const intensity = data.today_signal?.intensity;
  const intensityColor =
    intensity === 'high'
      ? '#D97757'
      : intensity === 'low'
      ? theme.textTertiary
      : accent;

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: theme.surface, borderColor: theme.border },
      ]}
    >
      {/* Tiny anchor: tells the user this Home is wired to a real signal */}
      {data.today_signal?.label ? (
        <View style={styles.anchorRow}>
          <View
            style={[
              styles.intensityDot,
              { backgroundColor: intensityColor },
            ]}
          />
          <Text style={[styles.anchorLabel, { color: theme.textTertiary }]}>
            {(data.today_signal.label || '').toUpperCase()}
          </Text>
        </View>
      ) : null}

      {/* SECTION 1 — THE CALL (hero) */}
      <Text style={[styles.theCall, { color: theme.text }]}>
        {data.the_call}
      </Text>

      {/* SECTION 2 — THE REALITY */}
      {data.the_reality ? (
        <Text style={[styles.theReality, { color: theme.textSecondary }]}>
          {data.the_reality}
        </Text>
      ) : null}

      {/* TIMELINE WHISPER — atmospheric coloration only on HIGH modulation. */}
      {/* Sits between The Reality and Where This Lands — soft weather       */}
      {/* between the body and the situational landing.                       */}
      <TimelineWhisper modulation={data.timeline_modulation} theme={theme} placement="spaced" />

      {/* SECTION 2b — TIMING COMPRESSION ("why now") */}
      {/* Single-line subtle insertion. No label, no divider, slightly */}
      {/* lighter opacity so it reads as part of the narrative — not as */}
      {/* a feature.  Hidden when the V5 sky-state has no clear timing  */}
      {/* pressure (background_pattern with medium intensity).          */}
      {data.timing_compression?.available && data.timing_compression?.line ? (
        <Text style={[styles.timingLine, { color: theme.textSecondary }]}>
          {data.timing_compression.line}
        </Text>
      ) : null}

      {/* SECTION 3 — WHERE THIS LANDS */}
      {data.where_this_lands && data.where_this_lands.length > 0 ? (
        <View
          style={[
            styles.whereWrap,
            { backgroundColor: theme.background, borderColor: theme.border },
          ]}
        >
          <Text style={[styles.whereTitle, { color: theme.textTertiary }]}>
            WHERE THIS LANDS
          </Text>
          {data.where_this_lands.slice(0, 3).map((line, idx) => (
            <View key={`wtl-${idx}`} style={styles.whereRow}>
              <Text
                style={[styles.whereDash, { color: theme.textTertiary }]}
              >
                —
              </Text>
              <Text
                style={[
                  styles.whereText,
                  { color: theme.textSecondary },
                ]}
              >
                {line}
              </Text>
            </View>
          ))}
        </View>
      ) : null}

      {/* SECTION 4 — THE EDGE */}
      {data.the_edge ? (
        <View
          style={[
            styles.edgeWrap,
            {
              borderLeftColor: accent + '60',
              backgroundColor: accent + '0D',
            },
          ]}
        >
          <Text style={[styles.edgeLabel, { color: accent }]}>
            THE EDGE
          </Text>
          <Text style={[styles.edgeText, { color: theme.text }]}>
            {data.the_edge}
          </Text>
        </View>
      ) : null}

      {/* SECTION 4b — MIRROR REMEMBERS (light Pattern Memory layer) */}
      {/* Renders only when high-confidence recurrence is detected. */}
      {/* Subtle, smaller than the hero, never overclaims, never quotes */}
      {/* private journal text — only safe deterministic phrasings.    */}
      {data.pattern_memory?.available && data.pattern_memory?.confidence === 'high' && data.pattern_memory?.summary ? (
        <View
          style={[
            styles.memoryWrap,
            {
              borderColor: theme.border,
              backgroundColor: theme.background,
            },
          ]}
        >
          <View style={styles.memoryHeader}>
            <Ionicons
              name="ellipse"
              size={5}
              color={theme.textTertiary}
              style={{ marginRight: 6, opacity: 0.6 }}
            />
            <Text
              style={[styles.memoryLabel, { color: theme.textTertiary }]}
            >
              MIRROR REMEMBERS
            </Text>
          </View>
          <Text style={[styles.memoryText, { color: theme.textSecondary }]}>
            {data.pattern_memory.summary}
          </Text>
        </View>
      ) : null}

      {/* SECTION 4c — WHERE THIS SHOWS UP WITH PEOPLE (Relational overlay) */}
      {/* High-confidence only. Person reveal additionally requires       */}
      {/* `source_verified === true` — a name is rendered ONLY when it    */}
      {/* exists in db.saved_people / db.people OR has organic            */}
      {/* journal/reflection corroboration. Background-engine derived     */}
      {/* names (relationship_patterns alone) are NEVER revealed.         */}
      {(() => {
        const rp = data.relational_pattern;
        if (!rp || !rp.available || rp.confidence !== 'high' || !rp.summary) {
          return null;
        }
        // Hard gate: a person reveal MUST be source_verified.
        if (rp.type === 'person' && rp.source_verified !== true) {
          return null;
        }
        // Context type must also be source_verified to suppress the
        // legacy unsafe context fallback.
        if (rp.type === 'context' && rp.source_verified !== true) {
          return null;
        }
        return (
          <View
            style={[
              styles.memoryWrap,
              {
                borderColor: theme.border,
                backgroundColor: theme.background,
              },
            ]}
          >
            <View style={styles.memoryHeader}>
              <Ionicons
                name="ellipse"
                size={5}
                color={theme.textTertiary}
                style={{ marginRight: 6, opacity: 0.6 }}
              />
              <Text
                style={[styles.memoryLabel, { color: theme.textTertiary }]}
              >
                WHERE THIS SHOWS UP WITH PEOPLE
              </Text>
            </View>
            <Text style={[styles.memoryText, { color: theme.textSecondary }]}>
              {rp.summary}
            </Text>
          </View>
        );
      })()}

      {/* SECTION 5 — CTA */}
      <TouchableOpacity
        onPress={handleCta}
        activeOpacity={0.8}
        style={[
          styles.ctaBtn,
          { borderColor: theme.border },
        ]}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>
          {data.cta || '→ See what\u2019s driving this today'}
        </Text>
        <Ionicons name="arrow-forward" size={16} color={theme.text} />
      </TouchableOpacity>
    </View>
  );
};

// ============================================
// Styles
// ============================================

const styles = StyleSheet.create({
  container: {
    padding: 22,
    borderRadius: 16,
    borderWidth: 1,
  },
  center: {
    alignItems: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  errorText: {
    fontSize: 14,
  },
  retryBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Anchor row
  anchorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  intensityDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  anchorLabel: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1.0,
  },

  // SECTION 1 — THE CALL
  theCall: {
    fontFamily: fontFamily.display,
    fontSize: 20,
    lineHeight: 27,
    fontWeight: '400',
    letterSpacing: 0.2,
    marginBottom: 12,
  },

  // SECTION 2 — THE REALITY
  theReality: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 18,
  },

  // SECTION 2b — TIMING COMPRESSION ("why now")
  // Same body typography as theReality but slightly lighter opacity
  // and italic so it reads as a continuation, not a new feature.
  timingLine: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
    opacity: 0.78,
    marginTop: -8,    // tighten vertical rhythm against theReality
    marginBottom: 18,
  },

  // SECTION 3 — WHERE THIS LANDS
  whereWrap: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  whereTitle: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1.0,
    marginBottom: 8,
  },
  whereRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
    gap: 8,
  },
  whereDash: {
    fontSize: 14,
    lineHeight: 20,
  },
  whereText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },

  // SECTION 4 — THE EDGE
  edgeWrap: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderLeftWidth: 3,
    marginBottom: 18,
  },
  edgeLabel: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1.0,
    marginBottom: 6,
  },
  edgeText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
  },

  // SECTION 4b — MIRROR REMEMBERS (subtle, smaller than hero)
  memoryWrap: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 18,
  },
  memoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  memoryLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1.2,
  },
  memoryText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
    opacity: 0.92,
  },

  // SECTION 5 — CTA
  ctaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '500',
  },
});

export default HomeInsightV6Card;
