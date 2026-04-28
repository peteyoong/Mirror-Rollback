// ============================================
// WhyThisIsActiveNowCard
// ============================================
//
// Subtle, secondary "Why this is active now" layer for the Home tab.
// Sits directly under the main HomeInsightV5Card.
//
// Anchored to GET /api/life/activation-now/{userId}.
//
// HARD UX RULES (per spec):
//   * Must NOT compete with the main Home insight.
//   * If confidence === "low" OR endpoint fails → hide the block entirely.
//     No loading errors. No empty states. No retry buttons.
//   * Pressure (low/medium/high) styles the block subtly. NEVER show the
//     literal label, confidence value, timing score, or debug.
//   * No "based on your chart", "transits", "energy today" copy. Render
//     ONLY the strings the backend returns.

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

// Enable layout animation on Android (no-op on iOS)
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// Theme shape mirrors what HomeInsightV5Card receives — duck-typed.
interface ThemeLike {
  background: string;
  surface: string;
  border: string;
  text: string;
  textSecondary: string;
  textTertiary: string;
  primary?: string;
}

interface ActivationNowResponse {
  activation_line?: string;
  activation_explanation?: string;
  activation_pressure?: 'low' | 'medium' | 'high' | string;
  confidence?: 'high' | 'medium' | 'low' | string;
  generator_version?: string;
}

interface Props {
  userId: string;
  theme: ThemeLike;
}

// ----------------------------------------------------------------------
// Pressure → invisible style modulation
// ----------------------------------------------------------------------

function pressureStyle(pressure: string | undefined, theme: ThemeLike) {
  // Defaults — neutral / muted (matches "low" or unknown)
  let borderColor = theme.border;
  let borderWidth = StyleSheet.hairlineWidth;
  let accentColor = theme.textTertiary;
  let labelOpacity = 0.55;

  if (pressure === 'medium') {
    // Slightly stronger accent — still secondary
    borderColor = theme.border;
    borderWidth = 1;
    accentColor = theme.textSecondary;
    labelOpacity = 0.7;
  } else if (pressure === 'high') {
    // Warmer tint, NOT warning red. We mix textSecondary as the accent
    // and add a slightly stronger border. Background stays surface so
    // it never visually competes with the main insight card.
    borderColor = theme.textTertiary;
    borderWidth = 1;
    accentColor = theme.text;
    labelOpacity = 0.85;
  }

  return { borderColor, borderWidth, accentColor, labelOpacity };
}

// In-memory cache for the session — keyed by userId. Avoids re-fetching
// every time the user navigates back to Home.
const _SESSION_CACHE: Record<string, ActivationNowResponse> = {};

// ----------------------------------------------------------------------
// Component
// ----------------------------------------------------------------------

const WhyThisIsActiveNowCard: React.FC<Props> = ({ userId, theme }) => {
  const [data, setData] = useState<ActivationNowResponse | null>(
    _SESSION_CACHE[userId] || null
  );
  const [loading, setLoading] = useState<boolean>(!_SESSION_CACHE[userId]);
  const [hidden, setHidden] = useState<boolean>(false);
  const [expanded, setExpanded] = useState<boolean>(false);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;

    // Already cached for this session → no fetch
    if (_SESSION_CACHE[userId]) {
      setData(_SESSION_CACHE[userId]);
      setLoading(false);
      // Re-evaluate hidden flag in case the cached payload was low-confidence
      const cached = _SESSION_CACHE[userId];
      if (
        !cached?.activation_line ||
        cached?.confidence === 'low'
      ) {
        setHidden(true);
      }
      return () => {
        cancelledRef.current = true;
      };
    }

    // Lazy fetch — fire after Home main content has had a chance to render.
    // 600ms gives HomeInsightV5Card the priority it needs.
    const timer = setTimeout(() => {
      (async () => {
        try {
          // NOTE: api instance has baseURL ending in `/api`, so do NOT prefix with /api here.
          const res = await api.get<ActivationNowResponse>(
            `/life/activation-now/${userId}`,
            { timeout: 25000 }
          );
          if (cancelledRef.current) return;
          const payload = res?.data || {};
          // Hide on low confidence OR empty line OR fetch error.
          if (
            !payload.activation_line ||
            !payload.activation_line.trim() ||
            payload.confidence === 'low'
          ) {
            setHidden(true);
            setLoading(false);
            return;
          }
          _SESSION_CACHE[userId] = payload;
          setData(payload);
          setLoading(false);
        } catch (err) {
          if (cancelledRef.current) return;
          // Per spec: never show fetch error to user — just hide silently.
          setHidden(true);
          setLoading(false);
        }
      })();
    }, 600);

    return () => {
      cancelledRef.current = true;
      clearTimeout(timer);
    };
  }, [userId]);

  // Loading: render nothing visible — keep Home pristine until ready
  if (loading) {
    return null;
  }
  if (hidden || !data || !data.activation_line) {
    return null;
  }

  const pressure = (data.activation_pressure || '').toLowerCase();
  const { borderColor, borderWidth, accentColor, labelOpacity } = pressureStyle(
    pressure,
    theme
  );
  const explanation = (data.activation_explanation || '').trim();
  const hasExplanation = explanation.length > 0;

  const onToggle = () => {
    if (!hasExplanation) return;
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded((v) => !v);
  };

  return (
    <View style={styles.outer} pointerEvents="box-none">
      <Pressable
        onPress={onToggle}
        disabled={!hasExplanation}
        style={({ pressed }) => [
          styles.card,
          {
            backgroundColor: theme.surface,
            borderColor,
            borderWidth,
            opacity: pressed && hasExplanation ? 0.85 : 1,
          },
        ]}
        accessibilityRole={hasExplanation ? 'button' : 'text'}
        accessibilityLabel="Why this is active now"
        accessibilityHint={
          hasExplanation
            ? expanded
              ? 'Tap to collapse explanation'
              : 'Tap to read more'
            : undefined
        }
      >
        {/* Tiny secondary label — never shows pressure/confidence */}
        <View style={styles.headerRow}>
          <Text
            style={[
              styles.label,
              { color: accentColor, opacity: labelOpacity },
            ]}
          >
            WHY THIS IS ACTIVE NOW
          </Text>
          {hasExplanation && (
            <Ionicons
              name={expanded ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={accentColor}
              style={{ opacity: labelOpacity }}
            />
          )}
        </View>

        <Text style={[styles.line, { color: theme.text }]} numberOfLines={3}>
          {data.activation_line}
        </Text>

        {expanded && hasExplanation && (
          <Text
            style={[
              styles.explanation,
              { color: theme.textSecondary },
            ]}
          >
            {explanation}
          </Text>
        )}
      </Pressable>
    </View>
  );
};

// ----------------------------------------------------------------------
// Styles
// ----------------------------------------------------------------------

const styles = StyleSheet.create({
  outer: {
    paddingHorizontal: 20,
    marginBottom: 16,
    // Subtle nudge upward to feel attached to the main insight card above
    marginTop: -4,
  },
  card: {
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  label: {
    fontSize: 10,
    letterSpacing: 1.2,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  line: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
  },
  explanation: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 8,
  },
});

export default WhyThisIsActiveNowCard;
