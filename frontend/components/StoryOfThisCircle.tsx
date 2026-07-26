/**
 * StoryOfThisCircle — Forum field hero (forum-topology-and-timing-v1)
 * ==================================================================
 *
 * Quiet, recognitional, emotionally observant.  NOT analytics.
 *
 * Lives at the TOP of /forums/[id].  Calls
 *   GET /api/forums/:forum_id/story-of-circle
 * Renders 5 calm sections:
 *   THE FIELD  ·  MOVES TOWARD  ·  SOFTENING  ·  UNSAID  ·  CHIPS
 *
 * Empty / sparse-topology states show a quiet placeholder, not a chart.
 */
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

interface CircleStory {
  marker?: string;
  ready: boolean;
  placeholder: string | null;
  the_field: string | null;
  moves_toward: string | null;
  softening: string | null;
  unsaid: string | null;
  field_state_chips: string[];
}

interface Props {
  forumId: string;
  /** Optional: refresh trigger when membership changes. */
  reloadKey?: any;
}

export default function StoryOfThisCircle({ forumId, reloadKey }: Props) {
  const { theme } = useTheme();
  const [story, setStory] = useState<CircleStory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        // Best-effort: attempt to refresh inferred topology before reading.
        try {
          await api.post(`/forums/${forumId}/topology/infer`, {});
        } catch {
          // Topology inference is opportunistic — never block render.
        }
        const debugFlag =
          process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true' ? '?debug=true' : '';
        const resp = await api.get(`/forums/${forumId}/story-of-circle${debugFlag}`);
        if (!cancelled) {
          setStory((resp?.data?.story as CircleStory) || null);
        }
      } catch {
        if (!cancelled) {
          setStory({
            marker: 'forum-topology-and-timing-v1',
            ready: false,
            placeholder:
              "The field is still becoming visible. Some dynamics only emerge through time, interaction, and shared context.",
            the_field: null,
            moves_toward: null,
            softening: null,
            unsaid: null,
            field_state_chips: [],
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    if (forumId) void load();
    return () => {
      cancelled = true;
    };
  }, [forumId, reloadKey]);

  if (loading) {
    return (
      <View style={[styles.skeleton, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
        <Text style={[styles.skeletonText, { color: theme.textTertiary }]}>
          Reading the room…
        </Text>
      </View>
    );
  }

  if (!story) return null;

  // Empty / sparse — quiet placeholder.
  if (!story.ready) {
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.kicker, { color: theme.textTertiary }]}>The story of this circle</Text>
        <Text style={[styles.placeholderText, { color: theme.textSecondary }]}>
          {story.placeholder ||
            'The field is still becoming visible. Some dynamics only emerge through time, interaction, and shared context.'}
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Text style={[styles.kicker, { color: theme.textTertiary }]}>The story of this circle</Text>

      {!!story.the_field && (
        <Text style={[styles.fieldText, { color: theme.text }]}>{story.the_field}</Text>
      )}

      {!!story.moves_toward && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            What the group moves toward
          </Text>
          <Text style={[styles.sectionText, { color: theme.text }]}>{story.moves_toward}</Text>
        </View>
      )}

      {!!story.softening && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            What is softening
          </Text>
          <Text style={[styles.sectionText, { color: theme.text }]}>{story.softening}</Text>
        </View>
      )}

      {!!story.unsaid && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            What remains unsaid
          </Text>
          <Text style={[styles.sectionText, { color: theme.text }]}>{story.unsaid}</Text>
        </View>
      )}

      {story.field_state_chips && story.field_state_chips.length > 0 && (
        <View style={styles.chipRow}>
          {story.field_state_chips.slice(0, 2).map((c) => (
            <View
              key={c}
              style={[
                styles.chip,
                { borderColor: theme.border, backgroundColor: 'transparent' },
              ]}
            >
              <Text style={[styles.chipText, { color: theme.textSecondary }]}>{c}</Text>
            </View>
          ))}
        </View>
      )}

      <Text style={[styles.footnote, { color: theme.textTertiary }]}>
        Recognition, not verdict. The room is alive; readings shift.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  skeleton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 14,
    marginHorizontal: 16,
    marginTop: 12,
  },
  skeletonText: { fontSize: 12, fontStyle: 'italic' },

  card: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 18,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 14,
  },
  kicker: {
    fontSize: 10.5,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    fontWeight: '500',
  },
  fieldText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '400',
  },
  placeholderText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  section: { gap: 5 },
  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
    fontWeight: '500',
  },
  sectionText: { fontSize: 14, lineHeight: 21 },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 2,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipText: {
    fontSize: 11.5,
    letterSpacing: 0.4,
    fontWeight: '500',
  },
  footnote: {
    fontSize: 11,
    fontStyle: 'italic',
    lineHeight: 16,
  },
});
