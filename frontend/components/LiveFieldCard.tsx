// ============================================================================
// LIVE FIELD V1 — Forum field-level pattern card
// ============================================================================
//
// Reads the *room*, not the people in it. Every member sees the same
// field state and same field-level lines; only "Your Position" is
// personalised. No individual is ever named or exposed.
//
// Sections (rendered in order):
//   FIELD STATE     — bold, primary
//   YOUR POSITION   — secondary
//   TRAJECTORY      — secondary
//   THE STORY       — italic body
//   THE MOVE        — only when payload.move.available
//
// Source: GET /api/forums/{forum_id}/live-field?user_id={user_id}
//
// When the field is below the confidence floor (<3 members) the
// component renders nothing — the parent screen continues to work
// normally without it.
// ============================================================================

import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import api from '../services/api';

// ============================================
// Types
// ============================================

type FieldState =
  | 'acceleration_field'
  | 'holding_field'
  | 'tension_field'
  | 'disengagement_field'
  | 'alignment_field'
  | string;

interface LiveFieldPayload {
  version?: string;
  forum_id?: string;
  available?: boolean;
  reason?: string;
  field_state?: FieldState;
  intensity?: 'low' | 'medium' | 'high' | string;
  field_message?: string;
  user_position?: string;
  trajectory?: string;
  story?: string;
  move?: {
    available?: boolean;
    line?: string;
  };
  stats?: {
    member_count?: number;
    members_with_v5?: number;
  };
  generated_at?: string;
}

interface LiveFieldCardProps {
  forumId: string;
  userId: string;
  theme: any;
}

// Friendly state label (kept short — no astrology language).
const FIELD_STATE_LABELS: Record<string, string> = {
  acceleration_field:  'ACCELERATION',
  holding_field:       'HOLDING',
  tension_field:       'TENSION',
  disengagement_field: 'QUIET',
  alignment_field:     'ALIGNED',
};

// ============================================
// Component
// ============================================

const LiveFieldCard: React.FC<LiveFieldCardProps> = ({ forumId, userId, theme }) => {
  const [data, setData] = useState<LiveFieldPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!forumId || !userId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/forums/${forumId}/live-field-v1`, {
        params: { user_id: userId },
      });
      setData(res?.data || null);
    } catch (e: any) {
      // eslint-disable-next-line no-console
      console.warn('[LiveField] load failed:', e?.message || e);
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [forumId, userId]);

  useEffect(() => {
    load();
  }, [load]);

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
          Reading the room…
        </Text>
      </View>
    );
  }

  // Don't render anything if confidence floor isn't met.
  if (error || !data || data.available === false) {
    return null;
  }

  const accent = theme.accent || '#8B5CF6';
  const intensityColor =
    data.intensity === 'high'
      ? '#D97757'
      : data.intensity === 'low'
      ? theme.textTertiary
      : accent;

  const stateLabel = FIELD_STATE_LABELS[data.field_state || ''] || 'FIELD';

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: theme.surface, borderColor: theme.border },
      ]}
    >
      {/* Header — small anchor, no jargon */}
      <View style={styles.headerRow}>
        <Text style={[styles.title, { color: theme.textTertiary }]}>
          LIVE FIELD
        </Text>
        <View style={styles.stateRow}>
          <View
            style={[
              styles.intensityDot,
              { backgroundColor: intensityColor },
            ]}
          />
          <Text style={[styles.stateLabel, { color: theme.textTertiary }]}>
            {stateLabel}
          </Text>
        </View>
      </View>

      {/* SECTION 1 — FIELD STATE */}
      {data.field_message ? (
        <Text style={[styles.fieldMessage, { color: theme.text }]}>
          {data.field_message}
        </Text>
      ) : null}

      {/* SECTION 2 — YOUR POSITION */}
      {data.user_position ? (
        <View
          style={[
            styles.posWrap,
            {
              borderColor: theme.border,
              backgroundColor: theme.background,
            },
          ]}
        >
          <Text style={[styles.posLabel, { color: theme.textTertiary }]}>
            YOUR POSITION
          </Text>
          <Text style={[styles.posText, { color: theme.textSecondary }]}>
            {data.user_position}
          </Text>
        </View>
      ) : null}

      {/* SECTION 3 — TRAJECTORY */}
      {data.trajectory ? (
        <View style={styles.trajWrap}>
          <Text style={[styles.smallLabel, { color: theme.textTertiary }]}>
            TRAJECTORY
          </Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            {data.trajectory}
          </Text>
        </View>
      ) : null}

      {/* SECTION 4 — THE STORY */}
      {data.story ? (
        <View style={styles.trajWrap}>
          <Text style={[styles.smallLabel, { color: theme.textTertiary }]}>
            THE STORY
          </Text>
          <Text style={[styles.storyText, { color: theme.textSecondary }]}>
            {data.story}
          </Text>
        </View>
      ) : null}

      {/* SECTION 5 — THE MOVE (subtle opening) */}
      {data.move?.available && data.move?.line ? (
        <View
          style={[
            styles.moveWrap,
            {
              borderLeftColor: accent + '60',
              backgroundColor: accent + '0D',
            },
          ]}
        >
          <Text style={[styles.smallLabel, { color: accent }]}>
            THE MOVE
          </Text>
          <Text style={[styles.moveText, { color: theme.text }]}>
            {data.move.line}
          </Text>
        </View>
      ) : null}
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
    fontSize: 13,
    fontStyle: 'italic',
  },

  // Header
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.4,
  },
  stateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  intensityDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  stateLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.0,
  },

  // SECTION 1
  fieldMessage: {
    fontSize: 17,
    lineHeight: 25,
    fontWeight: '600',
    marginBottom: 16,
  },

  // SECTION 2 — Your Position
  posWrap: {
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  posLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 6,
  },
  posText: {
    fontSize: 14,
    lineHeight: 21,
  },

  // SECTION 3, 4
  trajWrap: {
    marginBottom: 14,
  },
  smallLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 4,
  },
  bodyText: {
    fontSize: 14,
    lineHeight: 21,
  },
  storyText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
    opacity: 0.92,
  },

  // SECTION 5 — Move
  moveWrap: {
    marginTop: 4,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderLeftWidth: 3,
  },
  moveText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },
});

export default LiveFieldCard;
