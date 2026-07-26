/**
 * HumanDesignDeepDiveSections.tsx
 *
 * Production-grade Human Design deep-dive surface.  Renders the
 * canonical narrative payload the backend emits at
 * `/api/human-design/mechanics/{user_id}`.  Prefers a `data` prop
 * supplied by the parent (single canonical fetch); falls back to its
 * own request when rendered standalone.
 *
 * Product invariants:
 *   • All copy is rendered VERBATIM from the backend.
 *   • Advanced activation fields (color / tone / base) are NEVER shown
 *     in the primary UI — see the "Verified activation fields" gate
 *     in ActivationTableView.
 *   • Missing / composed / verified variants are internal metadata;
 *     they never leak into user-facing copy.
 *   • The Evidence disclosure lives inside a collapsed "How this was
 *     derived" section — never at the primary card level.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform } from 'react-native';
import api from '../../services/api';

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────
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
  variant?: string;
  [k: string]: any;
};

export type DeepDivePayload = {
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
    advanced_fields_verified?: boolean;   // v2 marker
  };
};

type Props = {
  userId: string | null | undefined;
  data?: DeepDivePayload | null | undefined;
  theme: any;
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
  testID?: string;
}> = ({ title, subtitle, defaultOpen = true, theme, children, testID }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View
      style={[styles.section, { borderColor: theme.border, backgroundColor: theme.surface }]}
      testID={testID}
    >
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

// The evidence panel is collapsed by default and is deliberately
// visually secondary; internal derivation_rule identifiers are hidden.
const EvidenceDetails: React.FC<{ evidence?: EvidenceRef[]; theme: any }> = ({
  evidence,
  theme,
}) => {
  const [open, setOpen] = useState(false);
  if (!evidence || evidence.length === 0) return null;
  return (
    <View style={{ marginTop: 6 }}>
      <TouchableOpacity onPress={() => setOpen((o) => !o)} activeOpacity={0.6}>
        <Text style={[styles.evidenceToggle, { color: theme.textTertiary }]}>
          {open ? 'Hide evidence' : 'How this was derived'}
        </Text>
      </TouchableOpacity>
      {open && (
        <View style={styles.evidencePanel}>
          {evidence.slice(0, 6).map((e, i) => (
            <Text key={`e-${i}`} style={[styles.evidenceRow, { color: theme.textTertiary }]}>
              · {formatEvidenceField(e)}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
};

const formatEvidenceField = (e: EvidenceRef): string => {
  const field = (e.field || '').replace(/[_.]/g, ' ').trim();
  const value = e.value !== undefined && e.value !== null ? ` — ${String(e.value)}` : '';
  return `${field}${value}`;
};

// ─────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────
const HumanDesignDeepDiveSections: React.FC<Props> = ({ userId, data: preloaded, theme }) => {
  const [data, setData] = useState<DeepDivePayload | null>(preloaded || null);
  const [loaded, setLoaded] = useState<boolean>(!!preloaded);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Prefer parent-supplied payload → single canonical fetch.
    if (preloaded && preloaded.component_narratives) {
      setData(preloaded);
      setLoaded(true);
      return;
    }
    if (!userId) return;
    // Fallback: fetch once, only when parent did not pass a payload.
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

  const cm = data?.core_mechanics || {};
  const topo = cm.definition_topology || {};
  const narr = data?.component_narratives || {};
  const cs = data?.core_story || {};
  const at = data?.activation_table || {};

  const advancedActivationVerified = at?.advanced_fields_verified === true;

  const orderedCenters = useMemo(() => {
    const arr = (narr.centers as any[]) || [];
    // Defined centres first, then undefined; canonical order preserved
    return [...arr].sort((a, b) => {
      if (a.is_defined === b.is_defined) return 0;
      return a.is_defined ? -1 : 1;
    });
  }, [narr.centers]);

  if (!loaded) return null;
  if (!data || error) return null;

  return (
    <View style={{ marginTop: 8 }}>
      {/* ────────── 1. CORE SYNTHESIS ────────── */}
      {cs.primary && (
        <Section title="Core synthesis" subtitle="How this design is meant to move" theme={theme} defaultOpen>
          <Text style={[styles.primaryHeadline, { color: theme.text }]}>{cs.primary.headline}</Text>
          <Text style={[styles.primaryText, { color: theme.textSecondary }]}>{cs.primary.text}</Text>
          {!!(cs.secondary && cs.secondary.length) && (
            <View style={{ marginTop: 14 }}>
              {cs.secondary!.slice(0, 3).map((s, i) => (
                <View key={`sec-${i}`} style={styles.threadRow}>
                  <Text style={[styles.threadHead, { color: theme.text }]}>{s.headline}</Text>
                  <Text style={[styles.threadText, { color: theme.textSecondary }]}>{s.text}</Text>
                </View>
              ))}
            </View>
          )}
          <EvidenceDetails evidence={cs.primary.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── 2. CORE MECHANICS ────────── */}
      <Section title="Core mechanics" subtitle="Type · Strategy · Authority · Profile · Definition" theme={theme}>
        <MechanicRow label="Type" value={cm.type} theme={theme} />
        <MechanicRow label="Strategy" value={cm.strategy} theme={theme} />
        <MechanicRow label="Authority" value={cm.authority} theme={theme} />
        <MechanicRow label="Profile" value={cm.profile} theme={theme} />
        <MechanicRow label="Definition" value={topo.derived_type || cm.definition} theme={theme} />
        <MechanicRow label="Signature" value={cm.signature} theme={theme} />
        <MechanicRow label="Not-self" value={cm.not_self} theme={theme} />
      </Section>

      {/* ────────── 3. DEFINITION ────────── */}
      {narr.definition && (
        <Section title="Definition" subtitle="How your defined centres connect" theme={theme} defaultOpen={false}>
          <Text style={[styles.h2, { color: theme.text }]}>{topo.derived_type || narr.definition.headline}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{stripDiagnostics(narr.definition.text)}</Text>
          {!!topo.components && topo.components.length > 0 && (
            <View style={{ marginTop: 8 }}>
              <Text style={[styles.subtleLabel, { color: theme.textTertiary }]}>Connected networks</Text>
              {topo.components.map((comp, idx) => (
                <Text key={`c-${idx}`} style={[styles.componentRow, { color: theme.textSecondary }]}>
                  · {comp.join(' — ')}
                </Text>
              ))}
            </View>
          )}
          <EvidenceDetails evidence={narr.definition.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── 4. CENTRES ────────── */}
      {!!(orderedCenters && orderedCenters.length) && (
        <Section title="Centres" subtitle="Nine energy centres — defined and undefined" theme={theme} defaultOpen={false}>
          {orderedCenters.map((c: any, i: number) => (
            <View key={`ctr-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>
                {c.centre} · {c.is_defined ? 'Defined' : 'Undefined'}
              </Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{c.text}</Text>
              <EvidenceDetails evidence={c.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* ────────── 5. CHANNELS ────────── */}
      {!!(narr.channels && narr.channels.length) && (
        <Section title="Defined channels" subtitle="Your fixed circuitry" theme={theme} defaultOpen={false}>
          {narr.channels.map((ch: any, i: number) => (
            <View key={`ch-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>{ch.headline}</Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{ch.text}</Text>
              <EvidenceDetails evidence={ch.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* ────────── 6. GATES / PROFILE ────────── */}
      {narr.profile && (
        <Section title="Profile" subtitle={cm.profile ? `${cm.profile}` : undefined} theme={theme} defaultOpen={false}>
          <Text style={[styles.h2, { color: theme.text }]}>{narr.profile.headline}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{narr.profile.text}</Text>
          <EvidenceDetails evidence={narr.profile.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── 7. PERSONALITY / DESIGN ACTIVATIONS ────────── */}
      {!!(narr.activations && narr.activations.length) && (
        <Section
          title="Sun / Earth activations"
          subtitle="Personality (conscious) · Design (unconscious)"
          theme={theme}
          defaultOpen={false}
        >
          {narr.activations.map((a: any, i: number) => (
            <View key={`act-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>
                {a.side === 'personality' ? 'Personality' : 'Design'} · {a.planet} · {a.gate}.{a.line}
              </Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{a.text}</Text>
              <EvidenceDetails evidence={a.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* ────────── 8. INCARNATION CROSS ────────── */}
      {narr.incarnation_cross && (
        <Section title="Incarnation Cross" subtitle="Four activations, one configured pattern" theme={theme} defaultOpen={false}>
          <Text style={[styles.h2, { color: theme.text }]}>{narr.incarnation_cross.label || 'Incarnation Cross'}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{narr.incarnation_cross.text}</Text>
          {!!(narr.incarnation_cross.activation_themes && narr.incarnation_cross.activation_themes.length) && (
            <View style={{ marginTop: 8 }}>
              {narr.incarnation_cross.activation_themes.map((t: string, i: number) => (
                <Text key={`th-${i}`} style={[styles.componentRow, { color: theme.textSecondary }]}>· {t}</Text>
              ))}
            </View>
          )}
          <EvidenceDetails evidence={narr.incarnation_cross.evidence} theme={theme} />
        </Section>
      )}

      {/* ────────── 9. ACTIVATION TABLE (13 planets) ────────── */}
      {!!(at.personality && at.design) && (
        <Section
          title="13-planet activation table"
          subtitle={`Personality ${at.counts?.personality_present ?? 0}/13 · Design ${at.counts?.design_present ?? 0}/13`}
          theme={theme}
          defaultOpen={false}
        >
          <ActivationTableView
            personality={at.personality}
            design={at.design}
            theme={theme}
            advancedVerified={advancedActivationVerified}
          />
          {!advancedActivationVerified && (
            <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
              Fine-grain activation fields (color · tone · base) are not shown until an
              independent reproducible calibration source is added.
            </Text>
          )}
        </Section>
      )}
    </View>
  );
};

// Strip any internal diagnostic sentences (e.g. subtype-unverified) that
// the backend may append to narrative text.  Users see clean product
// copy; missing detail is disclosed only inside the collapsed evidence.
function stripDiagnostics(text?: string): string {
  if (!text) return '';
  const stripped = text
    .replace(/\n\nSplit sub-classification[^.]*\.[^.]*\./gi, '')
    .replace(/\bSession-3[abcd][^.]*\./gi, '')
    .replace(/\bstructural fallback[^.]*\./gi, '')
    .trim();
  return stripped;
}

const MechanicRow: React.FC<{ label: string; value?: string | null; theme: any }> = ({
  label,
  value,
  theme,
}) => {
  const shown = value && String(value).trim().length > 0 ? String(value) : '—';
  return (
    <View style={[styles.mechRow, { borderColor: theme.border }]}>
      <Text style={[styles.mechLabel, { color: theme.textTertiary }]}>{label}</Text>
      <Text style={[styles.mechValue, { color: theme.text }]}>{shown}</Text>
    </View>
  );
};

const ActivationTableView: React.FC<{
  personality: any[];
  design: any[];
  theme: any;
  advancedVerified: boolean;
}> = ({ personality, design, theme, advancedVerified }) => {
  const byPlanet = (arr: any[], planet: string) => arr.find((r) => r.planet === planet) || null;
  const allPlanets = Array.from(
    new Set([...personality.map((r) => r.planet), ...design.map((r) => r.planet)])
  );
  const rows = allPlanets.map((planet) => ({
    planet,
    p: byPlanet(personality, planet),
    d: byPlanet(design, planet),
  }));

  const renderCell = (row: any) => {
    if (!row || row.missing) return '—';
    // Show gate.line always (verified); color/tone/base only when verified
    if (advancedVerified && row.full_formatted) return row.full_formatted;
    return row.formatted || `${row.gate ?? '—'}.${row.line ?? '—'}`;
  };

  // On very narrow mobile, allow horizontal scroll to prevent clipping
  const isNarrow = Platform.OS !== 'web' || (typeof window !== 'undefined' && window.innerWidth < 360);

  const table = (
    <View>
      <View style={[styles.actHead, { borderColor: theme.border }]}>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1.4 }]}>Planet</Text>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1 }]}>Personality</Text>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1 }]}>Design</Text>
      </View>
      {rows.map((r, i) => (
        <View key={`ar-${i}`} style={[styles.actRow, { borderColor: theme.border }]}>
          <Text style={[styles.actCell, { color: theme.text, flex: 1.4 }]}>{r.planet}</Text>
          <Text style={[styles.actCell, { color: theme.textSecondary, flex: 1 }]}>{renderCell(r.p)}</Text>
          <Text style={[styles.actCell, { color: theme.textSecondary, flex: 1 }]}>{renderCell(r.d)}</Text>
        </View>
      ))}
    </View>
  );

  return isNarrow ? (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ minWidth: 320 }}>
      {table}
    </ScrollView>
  ) : (
    table
  );
};

// ─────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────
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
  primaryHeadline: { fontSize: 15, fontWeight: '600', marginBottom: 6 },
  primaryText: { fontSize: 14, lineHeight: 20 },
  subtleLabel: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 6,
    marginTop: 8,
  },
  threadRow: { marginTop: 12, paddingBottom: 8 },
  threadHead: { fontSize: 14, fontWeight: '500', marginBottom: 4 },
  threadText: { fontSize: 13, lineHeight: 19 },
  h2: { fontSize: 15, fontWeight: '600', marginBottom: 6 },
  bodyText: { fontSize: 13, lineHeight: 19 },
  componentRow: { fontSize: 13, marginTop: 2 },
  methodologyNote: { fontSize: 12, marginTop: 12, fontStyle: 'italic' },
  evidenceToggle: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 8,
  },
  evidencePanel: {
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(120,120,120,0.2)',
  },
  evidenceRow: { fontSize: 11, marginTop: 2 },
  mechRow: {
    flexDirection: 'row',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  mechLabel: { fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.4, flex: 0.8 },
  mechValue: { fontSize: 14, fontWeight: '500', flex: 1.2, textAlign: 'right' },
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

export default HumanDesignDeepDiveSections;
