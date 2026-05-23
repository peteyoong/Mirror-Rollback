/**
 * GoverningChapterCard.tsx
 * ========================
 * Build marker: phase-architecture-v1a
 *
 * Top-of-timeline card that surfaces the user's current Governing Life
 * Chapter — the 3-9 month phase that becomes the gravitational center
 * of Timeline V2. Existential, behavioral language; categorical /
 * house labels live ONLY inside the collapsible proof drawer.
 *
 * Placement (Phase 1A):
 *   AstrologyTimelineTab → ABOVE the existing "yearTheme" card.
 *   Existing yearly phase cards still render below; they become
 *   visually subordinate to the chapter.
 *
 * Silent failure: if the API returns 404 / errors out, the card
 * renders nothing — same discipline as EchoAcrossSystems.
 */
import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Constants from 'expo-constants';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';

const BACKEND_BASE =
  (Constants.expoConfig?.extra as any)?.EXPO_PUBLIC_BACKEND_URL ||
  process.env.EXPO_PUBLIC_BACKEND_URL ||
  '';
const APP_BASE = typeof window !== 'undefined' ? '' : BACKEND_BASE;

interface ChapterPayload {
  chapter_id:   string;
  title:        string;
  subtitle:     string;
  arc_type:     string;
  body_visible: string;
}

interface ProofPayload {
  proof_summary:   string;
  matched_signals: string[];
  score:           number;
  internal_topics: string[];
}

interface GoverningChapterResponse {
  success?:        boolean;
  build_marker?:   string;
  selection_mode?: string;
  chapter?:        ChapterPayload;
  proof?:          ProofPayload;
}

interface Props {
  userId: string;
}

// ---------------------------------------------------------------------------
// Arc-type → soft chip
// ---------------------------------------------------------------------------
const ARC_LABEL: Record<string, string> = {
  ending:       'ENDING',
  threshold:    'THRESHOLD',
  identity:     'IDENTITY',
  integration:  'INTEGRATION',
  expansion:    'EXPANSION',
  pressure:     'PRESSURE',
  closure:      'CLOSURE',
};

// Human-readable labels for internal signal IDs. Kept inside the proof
// drawer only — never in the visible title.
const SIGNAL_LABEL: Record<string, string> = {
  hd_open_solar_plexus:        'Open Solar Plexus — emotional permeability',
  hd_open_throat:              'Open Throat — containment around what wants to be said',
  hd_defined_heart:            'Defined Heart — willpower runs on a consistent supply',
  hd_defined_authority_center: 'Defined inner-authority center',
  hd_channel_22:               'Gate 22 active — Grace / receive the room',
  hd_channel_49:               'Gate 49 active — tribal-emotional radar',
  astro_saturn_house_3_4_7:    'Saturn in the relational / home / communication houses',
  astro_saturn_angular:        'Saturn angular (1st / 4th / 7th / 10th house)',
  astro_saturn_hard_to_moon:   'Saturn hard aspect to Moon',
  astro_saturn_hard_to_venus:  'Saturn hard aspect to Venus',
  astro_saturn_hard_to_mercury:'Saturn hard aspect to Mercury',
  astro_saturn_hard_to_mars:   'Saturn hard aspect to Mars',
  astro_saturn_hard_to_sun:    'Saturn hard aspect to Sun',
  astro_mars_venus_hard:       'Mars-Venus hard aspect',
  astro_12th_house_moon:       'Moon in the 12th house',
  astro_10th_house_emphasis:   'Personal planets in the 10th house',
  astro_4th_house_emphasis:    'Personal planets in the 4th house',
  timeline_theme_relational:   'Yearly timeline foregrounds relational pressure',
  timeline_theme_boundary:     'Yearly timeline foregrounds boundary pressure',
};

function humanizeSignal(id: string): string {
  return SIGNAL_LABEL[id] || id.replace(/_/g, ' ');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function GoverningChapterCard({ userId }: Props) {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [data, setData]       = useState<GoverningChapterResponse | null>(null);
  const [proofOpen, setProofOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const res = await fetch(
          `${APP_BASE}/api/timeline/governing-chapter/${userId}`,
          { headers: { 'Cache-Control': 'no-cache' } as any },
        );
        if (!res.ok) {
          if (!cancelled) setData(null);
          return;
        }
        const json = (await res.json()) as GoverningChapterResponse;
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) setData(null);
        // eslint-disable-next-line no-console
        console.warn('[GoverningChapterCard] load failed:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const chapter = data?.chapter;
  const proof   = data?.proof;

  const proofSignals = useMemo(
    () => (proof?.matched_signals || []).map(humanizeSignal),
    [proof],
  );

  if (loading) {
    return (
      <View style={[styles.loadingWrap, { borderColor: theme.border, backgroundColor: theme.surface }]}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
      </View>
    );
  }

  // Silent failure (no chart, error, etc.) — render nothing.
  if (!data || !chapter || !chapter.title) {
    return null;
  }

  const arcLabel = ARC_LABEL[chapter.arc_type] || chapter.arc_type?.toUpperCase() || '';

  return (
    <View style={[styles.wrap, { borderColor: Colors.accent + '50', backgroundColor: theme.surface }]}>
      <View style={styles.headerRow}>
        <Text style={[styles.eyebrow, { color: Colors.accent }]}>THE CHAPTER YOU'RE IN</Text>
        {arcLabel ? (
          <Text style={[styles.arcChip, { color: theme.textTertiary, borderColor: theme.border }]}>
            {arcLabel}
          </Text>
        ) : null}
      </View>

      <Text style={[styles.title, { color: theme.text }]}>{chapter.title}</Text>
      {chapter.subtitle ? (
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>{chapter.subtitle}</Text>
      ) : null}

      <Text style={[styles.body, { color: theme.text }]}>{chapter.body_visible}</Text>

      <TouchableOpacity
        activeOpacity={0.7}
        hitSlop={8}
        style={styles.proofToggle}
        onPress={() => setProofOpen((s) => !s)}
      >
        <Text style={[styles.proofToggleLabel, { color: theme.textTertiary }]}>
          {proofOpen ? 'Hide the structure' : 'Why this is the chapter we see'}
        </Text>
        <Ionicons
          name={proofOpen ? 'chevron-up' : 'chevron-down'}
          size={14}
          color={theme.textTertiary}
        />
      </TouchableOpacity>

      {proofOpen && (
        <View style={[styles.proofDrawer, { borderTopColor: theme.border }]}>
          {proof?.proof_summary ? (
            <Text style={[styles.proofSummary, { color: theme.textSecondary }]}>
              {proof.proof_summary}
            </Text>
          ) : null}
          {proofSignals.length > 0 && (
            <View style={styles.signalList}>
              {proofSignals.map((s, i) => (
                <View key={`sig-${i}`} style={styles.signalRow}>
                  <View style={[styles.signalDot, { backgroundColor: theme.textTertiary }]} />
                  <Text style={[styles.signalText, { color: theme.textSecondary }]}>{s}</Text>
                </View>
              ))}
            </View>
          )}
          {__DEV__ && data?.selection_mode ? (
            <Text style={[styles.devMeta, { color: theme.textTertiary }]}>
              [dev] selection={data.selection_mode} · score={proof?.score}
            </Text>
          ) : null}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 4,
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 18,
    paddingHorizontal: 16,
    ...Platform.select({
      ios:    { shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 6, shadowOffset: { width: 0, height: 1 } },
      android:{ elevation: 1 },
      default:{},
    }),
  },
  loadingWrap: {
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 4,
    paddingVertical: 16,
    borderWidth: 1,
    borderRadius: 14,
    alignItems: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  eyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  arcChip: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.0,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    overflow: 'hidden',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 28,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 12,
    lineHeight: 19,
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '400',
  },
  proofToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 14,
    paddingVertical: 6,
  },
  proofToggleLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  proofDrawer: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 10,
    marginTop: 4,
  },
  proofSummary: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 10,
  },
  signalList: {
    gap: 6,
  },
  signalRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  signalDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 8,
  },
  signalText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
  },
  devMeta: {
    marginTop: 10,
    fontSize: 10,
    opacity: 0.7,
  },
});
