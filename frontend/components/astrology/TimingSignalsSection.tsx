/**
 * TimingSignalsSection.tsx  ·  Timeline Intelligence V2 · Phase 3
 * ---------------------------------------------------------------
 * Renders the aggregated `timing_signals` block emitted by the
 * `TimingEvidenceLayer` on the backend (GET /api/timeline/signals/current).
 *
 * Design goals
 *   • Observational tone — never predictive, never fatalistic.
 *   • Evidence first — every signal shows its confidence label and the
 *     supporting signals that fed the compute.
 *   • Extensible — renders any number of engines the backend registers,
 *     without needing per-engine UI code (falls back to a generic card).
 *   • Silent by default when the network fails or the user has no chart —
 *     never blocks the surrounding Timeline tab.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Pressable, ScrollView, Platform } from 'react-native';
import Constants from 'expo-constants';
import { useLocalSearchParams, useRouter, usePathname } from 'expo-router';

// Match the URL resolution pattern used by AstrologyTimelineTab.
const BACKEND_BASE =
  (Constants.expoConfig?.extra as any)?.EXPO_PUBLIC_BACKEND_URL ||
  process.env.EXPO_PUBLIC_BACKEND_URL ||
  '';
const APP_BASE = typeof window !== 'undefined' ? '' : BACKEND_BASE;

// ---------------------------------------------------------------------------
// Types (mirror the backend TimingEvidence.to_public_dict shape)
// ---------------------------------------------------------------------------
export interface TimingSignal {
  engine_id: string;
  name: string;
  meaning: string;
  confidence: 'high' | 'moderate' | 'conditional' | 'low';
  supporting_signals: string[];
  details: Record<string, any>;
  engine_marker?: string;
  active: boolean;
}

interface TimingSignalsResponse {
  ok: boolean;
  computed_for: { user_id: string; date: string };
  timing_signals: Record<string, TimingSignal>;
  protocol: {
    protocol_marker: string;
    layer_marker: string;
    engines_run: string[];
  };
}

interface Props {
  userId: string | null | undefined;
  theme?: { colors?: { text?: string; background?: string; card?: string; border?: string; muted?: string; accent?: string } };
  isDark?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function TimingSignalsSection({ userId, theme, isDark }: Props) {
  const router   = useRouter();
  const pathname = usePathname();
  const params   = useLocalSearchParams<{ ty?: string }>();

  // Hydrate initial yearOffset from URL (?ty=<int>), else 0.
  const initialOffset = (() => {
    const raw = params?.ty;
    if (raw === undefined) return 0;
    const n = parseInt(String(raw), 10);
    if (Number.isFinite(n) && n >= -5 && n <= 5) return n;
    return 0;
  })();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [signals, setSignals] = useState<Record<string, TimingSignal> | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  // Date scrubber — offset in YEARS from today. 0 = today, negative = past.
  const [yearOffset, setYearOffset] = useState<number>(initialOffset);

  // Persist yearOffset in the URL as ?ty=<int> so shareable Timeline
  // permalinks reopen at the same scrub window.
  useEffect(() => {
    if (!pathname) return;
    try {
      const next: Record<string, any> = { ...(params || {}) };
      if (yearOffset === 0) delete next.ty; else next.ty = String(yearOffset);
      router.setParams(next as any);
    } catch { /* no-op on native */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yearOffset]);

  // Turn yearOffset → concrete YYYY-MM-DD (today shifted by N years).
  const scrubDate = useMemo(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() + yearOffset);
    return d.toISOString().slice(0, 10);
  }, [yearOffset]);

  useEffect(() => {
    if (!userId) { setLoading(false); return; }
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const url =
          `${APP_BASE}/api/timeline/signals/current` +
          `?user_id=${encodeURIComponent(userId)}` +
          `&date=${scrubDate}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: TimingSignalsResponse = await res.json();
        if (cancelled) return;
        setSignals(data.timing_signals || {});
      } catch (err: any) {
        if (cancelled) return;
        setError(String(err?.message ?? err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [userId, scrubDate]);

  // Silent when no user or nothing to show.
  if (!userId) return null;
  if (error && !signals) return null;               // fail quietly, never block
  if (!loading && (!signals || Object.keys(signals).length === 0)) return null;

  const palette = isDark
    ? { bg: '#141821', card: '#1c2230', text: '#E6E9F2', muted: '#8B93A7', border: '#2b3244', accent: '#B79EFF' }
    : { bg: '#F7F8FC', card: '#FFFFFF', text: '#1a1d29', muted: '#5c6478', border: '#E4E7EF', accent: '#6B4EDB' };

  return (
    <View style={[styles.container, { backgroundColor: palette.bg, borderColor: palette.border }]}>
      <View style={styles.headerRow}>
        <Text style={[styles.header, { color: palette.muted }]}>Timing Signals</Text>
        <Text style={[styles.scrubDateLabel, { color: palette.muted }]}>
          {yearOffset === 0 ? 'today' : `${yearOffset > 0 ? '+' : ''}${yearOffset}y · ${scrubDate}`}
        </Text>
      </View>

      {/* Mini date scrubber — past 5 → future 5 years, plus today. */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrubStrip}
      >
        {[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5].map(offset => {
          const active = offset === yearOffset;
          return (
            <Pressable
              key={offset}
              onPress={() => setYearOffset(offset)}
              style={[
                styles.scrubChip,
                {
                  borderColor: active ? palette.accent : palette.border,
                  backgroundColor: active ? palette.accent + '22' : 'transparent',
                },
              ]}
            >
              <Text style={[
                styles.scrubChipText,
                { color: active ? palette.accent : palette.muted,
                  fontWeight: active ? '700' : '500' },
              ]}>
                {offset === 0 ? 'now' : (offset > 0 ? `+${offset}y` : `${offset}y`)}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      {loading && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={palette.accent} />
          <Text style={[styles.loadingText, { color: palette.muted }]}>Reading timing…</Text>
        </View>
      )}

      {signals && Object.entries(signals).map(([id, sig]) => (
        <SignalCard
          key={id}
          signal={sig}
          expanded={!!expanded[id]}
          onToggle={() => setExpanded(prev => ({ ...prev, [id]: !prev[id] }))}
          palette={palette}
        />
      ))}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Per-signal card
// ---------------------------------------------------------------------------
function SignalCard({ signal, expanded, onToggle, palette }: {
  signal: TimingSignal;
  expanded: boolean;
  onToggle: () => void;
  palette: { bg: string; card: string; text: string; muted: string; border: string; accent: string };
}) {
  const conf = signal.confidence;
  const confColor =
    conf === 'high'        ? '#3FA672' :
    conf === 'moderate'    ? palette.accent :
    conf === 'conditional' ? '#D6A24E' :
                             palette.muted;

  const d = signal.details || {};
  const interp = d.interpretation || {};

  return (
    <View style={[styles.card, { backgroundColor: palette.card, borderColor: palette.border }]}>
      <View style={styles.cardHead}>
        <Text style={[styles.cardTitle, { color: palette.text }]}>{signal.name}</Text>
        <View style={[styles.confBadge, { borderColor: confColor }]}>
          <Text style={[styles.confBadgeText, { color: confColor }]}>{conf}</Text>
        </View>
      </View>

      <Text style={[styles.cardMeaning, { color: palette.text }]}>{signal.meaning}</Text>

      {/* Detail row — only render fields we know about; extensible. */}
      {(d.activated_house || d.lord_of_the_year || d.profected_sign) && (
        <View style={styles.detailRow}>
          {d.profected_sign && (
            <Text style={[styles.detailChip, { color: palette.muted, borderColor: palette.border }]}>
              {d.profected_sign}
            </Text>
          )}
          {d.activated_house !== undefined && (
            <Text style={[styles.detailChip, { color: palette.muted, borderColor: palette.border }]}>
              House {d.activated_house}
            </Text>
          )}
          {d.lord_of_the_year && (
            <Text style={[styles.detailChip, { color: palette.muted, borderColor: palette.border }]}>
              Ruler · {d.lord_of_the_year}
            </Text>
          )}
        </View>
      )}

      <Pressable onPress={onToggle} style={styles.expandBtn}>
        <Text style={[styles.expandBtnText, { color: palette.accent }]}>
          {expanded ? 'Hide details' : 'Show details'}
        </Text>
      </Pressable>

      {expanded && (
        <View style={[styles.expandedBody, { borderTopColor: palette.border }]}>
          {interp.experiences_that_tend_to_emerge && (
            <ExpandedLine label="What tends to emerge" body={interp.experiences_that_tend_to_emerge} palette={palette} />
          )}
          {interp.active_developmental_question && (
            <ExpandedLine label="Developmental question" body={interp.active_developmental_question} palette={palette} italic />
          )}
          {interp.strengths_easier_this_year && (
            <ExpandedLine label="Easier this year" body={interp.strengths_easier_this_year} palette={palette} />
          )}
          {interp.blind_spots_more_visible && (
            <ExpandedLine label="More visible blind spots" body={interp.blind_spots_more_visible} palette={palette} />
          )}
          {interp.ruler_condition_note && (
            <ExpandedLine label="Ruler note" body={interp.ruler_condition_note} palette={palette} />
          )}
          {interp.ruler_house_signal && (
            <ExpandedLine label="Where it shows up" body={interp.ruler_house_signal} palette={palette} />
          )}
          {interp.identity_synthesis_interaction && (
            <ExpandedLine label="Identity interaction" body={interp.identity_synthesis_interaction} palette={palette} />
          )}

          {signal.supporting_signals?.length > 0 && (
            <View style={styles.supportingBlock}>
              <Text style={[styles.supportingLabel, { color: palette.muted }]}>Supporting signals</Text>
              {signal.supporting_signals.map((s, i) => (
                <Text key={i} style={[styles.supportingItem, { color: palette.muted }]}>· {s}</Text>
              ))}
            </View>
          )}
        </View>
      )}
    </View>
  );
}

function ExpandedLine({ label, body, palette, italic }: {
  label: string; body: string;
  palette: { text: string; muted: string };
  italic?: boolean;
}) {
  return (
    <View style={styles.expandedLine}>
      <Text style={[styles.expandedLabel, { color: palette.muted }]}>{label}</Text>
      <Text style={[styles.expandedBody_, { color: palette.text, fontStyle: italic ? 'italic' : 'normal' }]}>
        {body}
      </Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const styles = StyleSheet.create({
  container: { padding: 16, borderRadius: 16, borderWidth: 1, marginBottom: 16 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between',
               alignItems: 'flex-end', marginBottom: 8 },
  header:    { fontSize: 12, fontWeight: '600', letterSpacing: 1.2,
               textTransform: 'uppercase' },
  scrubDateLabel: { fontSize: 11, fontFamily: Platform.select({ios:'Menlo', android:'monospace', default:'monospace'}) as any },
  scrubStrip:{ flexDirection: 'row', gap: 6, paddingBottom: 12, paddingRight: 4 },
  scrubChip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999,
               borderWidth: 1, minWidth: 44, alignItems: 'center' },
  scrubChipText: { fontSize: 11 },
  loadingRow:{ flexDirection: 'row', alignItems: 'center', gap: 10 },
  loadingText:{ fontSize: 13 },
  card:      { padding: 14, borderRadius: 12, borderWidth: 1, marginBottom: 10 },
  cardHead:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: '700' },
  confBadge: { borderWidth: 1, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
  confBadgeText: { fontSize: 10, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.8 },
  cardMeaning: { fontSize: 14, lineHeight: 20, marginBottom: 10 },
  detailRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 8 },
  detailChip:{ fontSize: 11, borderWidth: 1, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  expandBtn: { alignSelf: 'flex-start', paddingVertical: 4 },
  expandBtnText: { fontSize: 12, fontWeight: '600' },
  expandedBody: { marginTop: 10, paddingTop: 10, borderTopWidth: 1 },
  expandedLine: { marginBottom: 10 },
  expandedLabel: { fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 3 },
  expandedBody_: { fontSize: 13, lineHeight: 19 },
  supportingBlock: { marginTop: 8 },
  supportingLabel: { fontSize: 10, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 4 },
  supportingItem: { fontSize: 11, lineHeight: 16 },
});
