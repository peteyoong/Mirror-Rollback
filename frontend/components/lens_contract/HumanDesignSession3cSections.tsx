/**
 * HumanDesignSession3cSections.tsx
 *
 * Session-3c authoritative HD narrative surface.  Fetches directly from
 * `/api/human-design/mechanics/{user_id}` (the mechanics endpoint is the
 * canonical Session-3c source; the deep-dive endpoint continues to serve
 * the legacy narrative).  All rendered text is verbatim from backend.
 *
 * Design invariants:
 *   • Text is rendered VERBATIM from the backend (no client-side
 *     re-writes, no client-side Signature/Not-Self derivation).
 *   • Undefined data collapses gracefully to "unavailable" — never
 *     replaced with generic text.
 *   • Split subtype is never rendered when
 *     `definition_topology.split_subtype_unverified === true`.
 *
 * build_marker: hd-session3c-fe-v2
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import api from '../../services/api';

type EvidenceRef = {
  field?: string;
  value?: any;
  source?: string;
  derivation_rule?: string;
};

type NarrativeBlock = {
  text?: string;
  headline?: string;
  evidence?: EvidenceRef[];
  content_provenance?: string;
  [k: string]: any;
};

type Session3cData = {
  core_mechanics?: {
    type?: string;
    strategy?: string;
    authority?: string;
    profile?: string;
    definition?: string;
    signature?: string;
    not_self?: string;
    definition_topology?: {
      derived_type?: string;
      components_count?: number;
      components?: string[][];
      split_subtype?: string | null;
      split_subtype_unverified?: boolean;
      split_subtype_reason?: string | null;
      matches_upstream?: boolean | null;
      derivation_rule?: string;
    };
  };
  component_narratives?: {
    centers?: any[];
    channels?: any[];
    activations?: any[];
    profile?: NarrativeBlock;
    definition?: NarrativeBlock;
    incarnation_cross?: NarrativeBlock;
    content_provenance?: string;
  };
  core_story?: {
    primary?: NarrativeBlock;
    secondary?: NarrativeBlock[];
    hierarchy?: string[];
    score_table?: { thread_id: string; score: number }[];
  };
  activation_table?: {
    personality?: any[];
    design?: any[];
    counts?: { [k: string]: number };
  };
};

// ─────────────────────────────────────────────────────────────
// Collapsible primitive
// ─────────────────────────────────────────────────────────────
const Section: React.FC<{
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  theme: any;
  children: React.ReactNode;
}> = ({ title, subtitle, defaultOpen = true, theme, children }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={[styles.section, { borderColor: theme.border, backgroundColor: theme.surface }]}>
      <TouchableOpacity onPress={() => setOpen((o) => !o)} activeOpacity={0.7}>
        <View style={styles.sectionHeader}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>{title}</Text>
            {!!subtitle && (
              <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
            )}
          </View>
          <Text style={[styles.sectionChevron, { color: theme.textTertiary }]}>{open ? '−' : '+'}</Text>
        </View>
      </TouchableOpacity>
      {open ? <View style={styles.sectionBody}>{children}</View> : null}
    </View>
  );
};

const EvidenceLine: React.FC<{ evidence?: EvidenceRef[]; theme: any }> = ({ evidence, theme }) => {
  if (!evidence || evidence.length === 0) return null;
  return (
    <View style={styles.evidenceLine}>
      <Text style={[styles.evidenceLabel, { color: theme.textTertiary }]}>Derived from: </Text>
      <Text style={[styles.evidenceText, { color: theme.textTertiary }]}>
        {evidence
          .slice(0, 3)
          .map((e) => e.field + (e.value !== undefined ? ` = ${String(e.value)}` : ''))
          .join(' · ')}
        {evidence.length > 3 ? ` · +${evidence.length - 3} more` : ''}
      </Text>
    </View>
  );
};

// ─────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────
type Props = {
  userId: string | null | undefined;
  data?: Session3cData | null | undefined;   // optional preloaded
  theme: any;
};

const HumanDesignSession3cSections: React.FC<Props> = ({ userId, data: preloaded, theme }) => {
  const [data, setData] = useState<Session3cData | null>(preloaded || null);
  const [loaded, setLoaded] = useState<boolean>(!!preloaded);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    if (preloaded && (preloaded as any).component_narratives) {
      setData(preloaded);
      setLoaded(true);
      return;
    }
    let mounted = true;
    (async () => {
      try {
        const resp = await api.get(`/human-design/mechanics/${userId}`);
        if (mounted) {
          setData(resp.data);
          setLoaded(true);
        }
      } catch (e: any) {
        if (mounted) {
          setError(String(e?.message || e));
          setLoaded(true);
        }
      }
    })();
    return () => {
      mounted = false;
    };
  }, [userId, preloaded]);

  if (!loaded) return null;
  if (!data || error) return null;

  const cm = data.core_mechanics || {};
  const topo = cm.definition_topology || {};
  const narr = data.component_narratives || {};
  const cs = data.core_story || {};
  const at = data.activation_table || {};

  const showSplitSubtype =
    topo.split_subtype && !topo.split_subtype_unverified ? topo.split_subtype : null;

  return (
    <View style={{ marginTop: 12 }}>
      {/* Build marker */}
      <View style={{ paddingHorizontal: 12, paddingVertical: 6 }}>
        <Text style={[styles.buildMarker, { color: theme.textTertiary }]}>
          The Mirror · Session-3c · Human Design narratives (backend-derived)
        </Text>
      </View>

      {/* ────────── CORE STORY (evidence-ranked) ────────── */}
      {cs.primary && (
        <Section title="Core Story" subtitle="Evidence-ranked hierarchy" theme={theme} defaultOpen>
          <View>
            <Text style={[styles.primaryHeadline, { color: theme.text }]}>{cs.primary.headline}</Text>
            <Text style={[styles.primaryText, { color: theme.textSecondary }]}>{cs.primary.text}</Text>
            <EvidenceLine evidence={cs.primary.evidence} theme={theme} />
          </View>
          {!!(cs.secondary && cs.secondary.length) && (
            <View style={{ marginTop: 12 }}>
              <Text style={[styles.subtleLabel, { color: theme.textTertiary }]}>Secondary threads</Text>
              {cs.secondary!.map((s, i) => (
                <View key={`sec-${i}`} style={styles.threadRow}>
                  <Text style={[styles.threadHead, { color: theme.text }]}>{s.headline}</Text>
                  <Text style={[styles.threadText, { color: theme.textSecondary }]}>{s.text}</Text>
                  <EvidenceLine evidence={s.evidence} theme={theme} />
                </View>
              ))}
            </View>
          )}
        </Section>
      )}

      {/* ────────── DEFINITION TOPOLOGY (verified) ────────── */}
      {narr.definition && (
        <Section title="Definition Topology" subtitle="Independently derived from your defined-centre graph" theme={theme}>
          <Text style={[styles.h2, { color: theme.text }]}>{narr.definition.headline}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{narr.definition.text}</Text>
          {!!topo.components && topo.components.length > 0 && (
            <View style={{ marginTop: 8 }}>
              <Text style={[styles.subtleLabel, { color: theme.textTertiary }]}>Connected components</Text>
              {topo.components.map((comp, idx) => (
                <Text key={`c-${idx}`} style={[styles.componentRow, { color: theme.textSecondary }]}>
                  · {comp.join(' — ')}
                </Text>
              ))}
            </View>
          )}
          {!showSplitSubtype && topo.derived_type === 'Split Definition' && (
            <Text style={[styles.unverifiedNote, { color: theme.warning || '#B08900' }]}>
              Split sub-classification (Small / Wide) is intentionally not shown — no
              formally verified algorithm has been implemented yet.
            </Text>
          )}
          <EvidenceLine evidence={narr.definition.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── CENTRES (defined + undefined) ────────── */}
      {!!(narr.centers && narr.centers.length) && (
        <Section title="Centres" subtitle={`Nine canonical HD centres — defined vs undefined`} theme={theme} defaultOpen={false}>
          {narr.centers.map((c: any, i: number) => (
            <View key={`ctr-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>
                {c.centre} {c.is_defined ? '· defined' : '· undefined'}
              </Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{c.text}</Text>
              <EvidenceLine evidence={c.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* ────────── CHANNELS (per channel) ────────── */}
      {!!(narr.channels && narr.channels.length) && (
        <Section title="Defined Channels" subtitle="Your fixed circuitry" theme={theme} defaultOpen={false}>
          {narr.channels.map((ch: any, i: number) => (
            <View key={`ch-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>{ch.headline}</Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{ch.text}</Text>
              {ch.variant === 'structural_fallback' && (
                <Text style={[styles.unverifiedNote, { color: theme.warning || '#B08900' }]}>
                  Authored narrative pending; structural lineage only.
                </Text>
              )}
              <EvidenceLine evidence={ch.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* ────────── ACTIVATIONS (Sun/Earth focus) + PROFILE ────────── */}
      {!!(narr.activations && narr.activations.length) && (
        <Section title="Sun / Earth Activations" subtitle="Personality (conscious) · Design (unconscious)" theme={theme} defaultOpen={false}>
          {narr.activations.map((a: any, i: number) => (
            <View key={`act-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>
                {a.side === 'personality' ? 'P' : 'D'}.{a.planet} — {a.gate}.{a.line}
              </Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{a.text}</Text>
              <EvidenceLine evidence={a.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {narr.profile && (
        <Section title="Profile" subtitle={narr.profile.headline} theme={theme} defaultOpen={false}>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{narr.profile.text}</Text>
          {narr.profile.variant === 'structural_fallback' && (
            <Text style={[styles.unverifiedNote, { color: theme.warning || '#B08900' }]}>
              Authored profile interpretation pending for this line-pair.
            </Text>
          )}
          <EvidenceLine evidence={narr.profile.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── INCARNATION CROSS ────────── */}
      {narr.incarnation_cross && (
        <Section title="Incarnation Cross" subtitle="One configured pattern of four activations" theme={theme} defaultOpen={false}>
          <Text style={[styles.h2, { color: theme.text }]}>{narr.incarnation_cross.label || 'Incarnation Cross'}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{narr.incarnation_cross.text}</Text>
          {!!(narr.incarnation_cross.activation_themes && narr.incarnation_cross.activation_themes.length) && (
            <View style={{ marginTop: 8 }}>
              {narr.incarnation_cross.activation_themes.map((t: string, i: number) => (
                <Text key={`th-${i}`} style={[styles.componentRow, { color: theme.textSecondary }]}>· {t}</Text>
              ))}
            </View>
          )}
          <EvidenceLine evidence={narr.incarnation_cross.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── 13-PLANET ACTIVATION TABLE ────────── */}
      {!!(at.personality && at.design) && (
        <Section
          title="13-Planet Activation Table"
          subtitle={`P: ${at.counts?.personality_present ?? 0}/13 · D: ${at.counts?.design_present ?? 0}/13`}
          theme={theme}
          defaultOpen={false}
        >
          <ActivationTableView personality={at.personality} design={at.design} theme={theme} />
        </Section>
      )}
    </View>
  );
};

const ActivationTableView: React.FC<{ personality: any[]; design: any[]; theme: any }> = ({
  personality,
  design,
  theme,
}) => {
  const rows: { planet: string; p: any; d: any }[] = [];
  const byPlanet = (arr: any[], planet: string) => arr.find((r) => r.planet === planet) || null;
  const allPlanets = Array.from(
    new Set([...personality.map((r) => r.planet), ...design.map((r) => r.planet)])
  );
  for (const planet of allPlanets) {
    rows.push({ planet, p: byPlanet(personality, planet), d: byPlanet(design, planet) });
  }
  return (
    <View>
      <View style={[styles.actHead, { borderColor: theme.border }]}>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1.4 }]}>Planet</Text>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1 }]}>Personality</Text>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1 }]}>Design</Text>
      </View>
      {rows.map((r, i) => (
        <View key={`ar-${i}`} style={[styles.actRow, { borderColor: theme.border }]}>
          <Text style={[styles.actCell, { color: theme.text, flex: 1.4 }]}>{r.planet}</Text>
          <Text style={[styles.actCell, { color: theme.textSecondary, flex: 1 }]}>
            {r.p?.missing ? '—' : r.p?.full_formatted || r.p?.formatted || '—'}
          </Text>
          <Text style={[styles.actCell, { color: theme.textSecondary, flex: 1 }]}>
            {r.d?.missing ? '—' : r.d?.full_formatted || r.d?.formatted || '—'}
          </Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  section: {
    borderWidth: 1,
    borderRadius: 12,
    marginHorizontal: 12,
    marginVertical: 6,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  sectionTitle: { fontSize: 16, fontWeight: '600' },
  sectionSubtitle: { fontSize: 12, marginTop: 2 },
  sectionChevron: { fontSize: 20, marginLeft: 8, fontWeight: '400' },
  sectionBody: { paddingHorizontal: 16, paddingBottom: 14 },
  buildMarker: { fontSize: 10, opacity: 0.7 },
  primaryHeadline: { fontSize: 15, fontWeight: '600', marginBottom: 6 },
  primaryText: { fontSize: 14, lineHeight: 20 },
  subtleLabel: { fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 6 },
  threadRow: { marginTop: 12, paddingBottom: 8 },
  threadHead: { fontSize: 14, fontWeight: '500', marginBottom: 4 },
  threadText: { fontSize: 13, lineHeight: 19 },
  h2: { fontSize: 15, fontWeight: '600', marginBottom: 6 },
  bodyText: { fontSize: 13, lineHeight: 19 },
  componentRow: { fontSize: 13, marginTop: 2 },
  unverifiedNote: { fontSize: 12, marginTop: 8, fontStyle: 'italic' },
  evidenceLine: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 },
  evidenceLabel: { fontSize: 11 },
  evidenceText: { fontSize: 11, flex: 1 },
  actHead: {
    flexDirection: 'row',
    paddingVertical: 6,
    borderBottomWidth: 1,
  },
  actHeadCell: { fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 },
  actRow: {
    flexDirection: 'row',
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  actCell: { fontSize: 12 },
});

export default HumanDesignSession3cSections;
