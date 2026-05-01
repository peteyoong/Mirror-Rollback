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

// ============================================
// Types
// ============================================

interface TodaySignal {
  label?: string | null;
  type?: string | null;
  intensity?: string | null;
  conflict?: boolean;
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
  proof?: {
    dominant_signal?: string | null;
    intensity?: string | null;
    signal_conflict?: boolean;
    house_clusters?: Array<{ house: number; bodies: string[] }>;
  };
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
    fontWeight: '600',
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
    fontWeight: '700',
    letterSpacing: 1.0,
  },

  // SECTION 1 — THE CALL
  theCall: {
    fontSize: 22,
    lineHeight: 30,
    fontWeight: '600',
    marginBottom: 14,
  },

  // SECTION 2 — THE REALITY
  theReality: {
    fontSize: 15,
    lineHeight: 23,
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
    fontWeight: '700',
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
    fontWeight: '700',
    letterSpacing: 1.0,
    marginBottom: 6,
  },
  edgeText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
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
    fontWeight: '600',
  },
});

export default HomeInsightV6Card;
