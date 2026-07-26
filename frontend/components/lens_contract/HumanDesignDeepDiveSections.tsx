/**
 * HumanDesignDeepDiveSections.tsx
 *
 * Canonical Human Design deep-dive content, split into two mode-aware
 * exports so the parent lens view can route each block into the right
 * mode:
 *
 *   • <HDReadingSections>  → recognition-first Reading mode
 *       Core synthesis → Natural capacities → Central tension →
 *       Relational impact → Integrated gift → Developmental edge →
 *       Practical experiment → Reflection → Why Mirror is saying this
 *
 *   • <HDExploreSections>  → technical/structural Explore mode
 *       (parent renders BodyGraph FIRST, then this component)
 *       Core mechanics → Definition topology → Centres → Channels →
 *       Profile → Personality & Design activations → Incarnation Cross
 *       → Methodology & availability
 *
 * The single default export remains for legacy imports; it renders the
 * Explore subset when `mode` is unspecified so an accidental caller
 * doesn't produce competing "master reading" content.
 *
 * Product invariants:
 *   • Text is rendered VERBATIM from the backend.
 *   • Advanced activation fields (color / tone / base) never appear
 *     until `advanced_fields_verified === true`.
 *   • Split subtype (Small/Wide) never rendered.
 *   • Internal audit / fallback / score / session terminology never
 *     appears in user-facing copy (defensive `stripDiagnostics()`).
 *   • The activation surface is labelled "Personality and Design
 *     Activations" — never "13-planet".  Earth and the Lunar Nodes are
 *     not planets so the term is inaccurate; the canonical label is
 *     "Personality and Design Activations" or "13 activation points on
 *     each side".
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform } from 'react-native';
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
    incarnation_cross?: string;
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
    advanced_fields_verified?: boolean;
  };
};

type Mode = 'reading' | 'explore';

type Props = {
  mode?: Mode;
  userId: string | null | undefined;
  data?: DeepDivePayload | null | undefined;
  theme: any;
};

// ─────────────────────────────────────────────────────────────
// Primitives
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

// Backend rarely leaks diagnostic sentences; this filter catches any
// that slip through so users never see internal audit copy.
function stripDiagnostics(text?: string): string {
  if (!text) return '';
  return text
    .replace(/\n\nSplit sub-classification[^.]*\.[^.]*\./gi, '')
    .replace(/\bSession-3[abcd][^.]*\./gi, '')
    .replace(/\bstructural fallback[^.]*\./gi, '')
    .trim();
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

// ─────────────────────────────────────────────────────────────
// Shared data fetch — parent supplies via prop for the canonical path.
// ─────────────────────────────────────────────────────────────
function useMechanics(
  userId: string | null | undefined,
  preloaded?: DeepDivePayload | null | undefined,
): { data: DeepDivePayload | null; loaded: boolean } {
  const [data, setData] = useState<DeepDivePayload | null>(preloaded || null);
  const [loaded, setLoaded] = useState<boolean>(!!preloaded);

  useEffect(() => {
    if (preloaded && preloaded.component_narratives) {
      setData(preloaded);
      setLoaded(true);
      return;
    }
    if (!userId) return;
    let mounted = true;
    (async () => {
      try {
        const resp = await api.get(`/human-design/mechanics/${userId}`);
        if (mounted) {
          setData(resp.data);
          setLoaded(true);
        }
      } catch {
        if (mounted) setLoaded(true);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [userId, preloaded]);

  return { data, loaded };
}

// ─────────────────────────────────────────────────────────────
// READING mode surface — recognition-first
// ─────────────────────────────────────────────────────────────
export const HDReadingSections: React.FC<Props> = ({ userId, data: preloaded, theme }) => {
  const { data, loaded } = useMechanics(userId, preloaded);

  const cs = data?.core_story || {};
  const narr = data?.component_narratives || {};
  const cm = data?.core_mechanics || {};

  const secondaryByThread = useMemo(() => {
    const map: Record<string, NarrativeBlock> = {};
    for (const t of cs.secondary || []) {
      if (t && (t as any).thread_id) map[(t as any).thread_id] = t;
    }
    return map;
  }, [cs.secondary]);

  if (!loaded || !data) return null;

  return (
    <View style={{ marginTop: 8 }}>
      {/* 1. Core synthesis */}
      {cs.primary && (
        <Section title="Core synthesis" subtitle="How your design is meant to move" theme={theme} defaultOpen>
          <Text style={[styles.primaryHeadline, { color: theme.text }]}>{cs.primary.headline}</Text>
          <Text style={[styles.primaryText, { color: theme.textSecondary }]}>
            {stripDiagnostics(cs.primary.text)}
          </Text>
          <EvidenceDetails evidence={cs.primary.evidence} theme={theme} />
        </Section>
      )}

      {/* 2. Natural capacities — defined channels + authority */}
      {(secondaryByThread.channels || secondaryByThread.authority) && (
        <Section title="Natural capacities" subtitle="What runs consistently in you" theme={theme}>
          {secondaryByThread.channels && (
            <View style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>Defined circuitry</Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>
                {stripDiagnostics(secondaryByThread.channels.text)}
              </Text>
            </View>
          )}
          {secondaryByThread.authority && (
            <View style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>Inner authority</Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>
                {stripDiagnostics(secondaryByThread.authority.text)}
              </Text>
            </View>
          )}
        </Section>
      )}

      {/* 3. Central tension — undefined-centre openness */}
      {(() => {
        const undefinedCentres = ((narr.centers as any[]) || []).filter((c) => !c.is_defined);
        if (undefinedCentres.length === 0) return null;
        const names = undefinedCentres.map((c) => c.centre).join(', ');
        return (
          <Section title="Central tension" subtitle="Where you're most porous" theme={theme}>
            <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
              Your undefined centres — {names} — amplify what is around you. This is where you are most receptive to other people\u2019s signals and most likely to confuse borrowed pressure for your own. The practice is not to armour these places but to notice when the amplified signal is yours and when it belongs to the room.
            </Text>
          </Section>
        );
      })()}

      {/* 4. Relational impact — Type-shaped */}
      {cm.type && (
        <Section title="Relational impact" subtitle="How you land with others" theme={theme}>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            {relationalImpactText(cm.type, cm.strategy)}
          </Text>
        </Section>
      )}

      {/* 5. Integrated gift — signature */}
      {cm.signature && (
        <Section title="Integrated gift" subtitle="What appears when this is honoured" theme={theme}>
          <Text style={[styles.h2, { color: theme.text }]}>{cm.signature}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            When the mechanism above operates without interference, the felt experience settles into{' '}
            <Text style={{ fontWeight: '600', color: theme.text }}>{cm.signature.toLowerCase()}</Text>. This is
            not aspiration; it is the natural signature of this configuration living as itself.
          </Text>
        </Section>
      )}

      {/* 6. Developmental edge — not-self */}
      {cm.not_self && (
        <Section title="Developmental edge" subtitle="What appears when the mechanism is off" theme={theme}>
          <Text style={[styles.h2, { color: theme.text }]}>{cm.not_self}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            The not-self theme for this configuration is{' '}
            <Text style={{ fontWeight: '600', color: theme.text }}>{cm.not_self.toLowerCase()}</Text>. Noticing
            it — without judgement — is the practical signal that this design is being overridden by the mind
            or by outside pressure.
          </Text>
        </Section>
      )}

      {/* 7. Practical experiment */}
      {cm.strategy && (
        <Section title="Practical experiment" subtitle="How to test this in a week" theme={theme}>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            For seven days, try the strategy of your type — <Text style={{ fontWeight: '600', color: theme.text }}>{cm.strategy}</Text> — as your only decision filter. Note when the signature ({cm.signature || '—'}) or the not-self ({cm.not_self || '—'}) shows up. The experiment is the data.
          </Text>
        </Section>
      )}

      {/* 8. Reflection */}
      <Section title="Reflection" subtitle="A question to sit with" theme={theme}>
        <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
          {reflectionPrompt(cm.type)}
        </Text>
      </Section>

      {/* 9. Why Mirror is saying this — evidence disclosure (collapsed) */}
      <Section title="Why Mirror is saying this" subtitle="Evidence trail" theme={theme} defaultOpen={false}>
        <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
          {'Every claim above resolves to a specific field on your chart — expand any prior section\u2019s \u201cHow this was derived\u201d note to see the exact lineage.'}
        </Text>
        {narr.definition && (
          <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
            Definition and topology are derived independently from the connected-component graph of your defined
            centres and channels.
          </Text>
        )}
        {narr.incarnation_cross && (
          <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
            The Incarnation Cross is read as one configuration of four activations (Personality Sun/Earth and
            Design Sun/Earth), not four separate roles.
          </Text>
        )}
      </Section>
    </View>
  );
};

function relationalImpactText(type?: string, strategy?: string): string {
  const t = (type || '').toLowerCase();
  if (t.includes('manifestor')) {
    return (
      'You initiate; other people feel the wake. When you inform before acting, the wake becomes something they can move with. When you skip the inform step, they meet the initiation as resistance — which reads as "controlling" from the outside and "peaceless" from the inside.'
    );
  }
  if (t.includes('manifesting generator')) {
    return (
      'Your energy responds and moves quickly. Others feel the momentum; the practice is to inform them when a step is being skipped so the shortcut is legible rather than confusing.'
    );
  }
  if (t.includes('generator')) {
    return (
      'You are designed to respond, not to initiate. Others feel your sacral "yes" as a stabilising fact and your sacral "no" as a real boundary. Trying to initiate outside of response is the friction others read as unavailability.'
    );
  }
  if (t.includes('projector')) {
    return (
      "Your gift is recognition — of systems, of people, of what wants to move. It lands when the invitation is real; when unrecognised, the same insight reads as unsolicited. The invitation isn\u2019t optional here — it\u2019s the mechanism."
    );
  }
  if (t.includes('reflector')) {
    return (
      "You sample the field. Your presence reflects the health of the environment back to it. Others feel most seen by you when you\u2019ve had time to move with the moon before speaking."
    );
  }
  return `Your Type is ${type || 'unavailable'}${strategy ? ` and your strategy is ${strategy}` : ''}.`;
}

function reflectionPrompt(type?: string): string {
  const t = (type || '').toLowerCase();
  if (t.includes('manifestor')) return 'Where in this week did I move without informing — and what did that cost the relationship?';
  if (t.includes('manifesting generator')) return 'Where did I skip a step this week, and where would informing have prevented friction?';
  if (t.includes('generator')) return 'Which "yes" this week was a sacral response — and which was mental?';
  if (t.includes('projector')) return 'Where did I offer insight uninvited, and where was I recognised for offering it?';
  if (t.includes('reflector')) return 'What did I feel today that was mine, and what did I feel that belonged to the environment?';
  return 'Which of my decisions this week was made through my strategy — and which by the mind?';
}

// ─────────────────────────────────────────────────────────────
// EXPLORE mode surface — technical/structural
// (parent renders BodyGraph FIRST, then this component)
// ─────────────────────────────────────────────────────────────
export const HDExploreSections: React.FC<Props> = ({ userId, data: preloaded, theme }) => {
  const { data, loaded } = useMechanics(userId, preloaded);
  const cm = data?.core_mechanics || {};
  const topo = cm.definition_topology || {};
  const narr = data?.component_narratives || {};
  const at = data?.activation_table || {};
  const advancedActivationVerified = at?.advanced_fields_verified === true;

  const orderedCenters = useMemo(() => {
    const arr = (narr.centers as any[]) || [];
    return [...arr].sort((a, b) => {
      if (a.is_defined === b.is_defined) return 0;
      return a.is_defined ? -1 : 1;
    });
  }, [narr.centers]);

  if (!loaded || !data) return null;

  return (
    <View style={{ marginTop: 8 }}>
      {/* 1. Core mechanics */}
      <Section title="Core mechanics" subtitle="Type · Strategy · Authority · Profile · Definition" theme={theme} defaultOpen>
        <MechanicRow label="Type" value={cm.type} theme={theme} />
        <MechanicRow label="Strategy" value={cm.strategy} theme={theme} />
        <MechanicRow label="Authority" value={cm.authority} theme={theme} />
        <MechanicRow label="Profile" value={cm.profile} theme={theme} />
        <MechanicRow label="Definition" value={topo.derived_type || cm.definition} theme={theme} />
        <MechanicRow label="Signature" value={cm.signature} theme={theme} />
        <MechanicRow label="Not-self" value={cm.not_self} theme={theme} />
      </Section>

      {/* 2. Definition topology */}
      {narr.definition && (
        <Section title="Definition topology" subtitle="How your defined centres connect" theme={theme}>
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

      {/* 3. Centres */}
      {!!(orderedCenters && orderedCenters.length) && (
        <Section title="Centres" subtitle="Nine energy centres — defined and undefined" theme={theme} defaultOpen={false}>
          {orderedCenters.map((c: any, i: number) => (
            <View key={`ctr-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>
                {c.centre} · {c.is_defined ? 'Defined' : 'Undefined'}
              </Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>
                {stripDiagnostics(c.text)}
              </Text>
              <EvidenceDetails evidence={c.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* 4. Channels */}
      {!!(narr.channels && narr.channels.length) && (
        <Section title="Defined channels" subtitle="Your fixed circuitry" theme={theme} defaultOpen={false}>
          {narr.channels.map((ch: any, i: number) => (
            <View key={`ch-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>{ch.headline}</Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{stripDiagnostics(ch.text)}</Text>
              <EvidenceDetails evidence={ch.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* 5. Profile */}
      {narr.profile && (
        <Section title="Profile" subtitle={cm.profile ? cm.profile : undefined} theme={theme} defaultOpen={false}>
          <Text style={[styles.h2, { color: theme.text }]}>{narr.profile.headline}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{stripDiagnostics(narr.profile.text)}</Text>
          <EvidenceDetails evidence={narr.profile.evidence} theme={theme} />
        </Section>
      )}

      {/* 6. Personality and Design activations (Sun/Earth) */}
      {!!(narr.activations && narr.activations.length) && (
        <Section
          title="Personality and Design activations"
          subtitle="Personality (conscious) · Design (unconscious)"
          theme={theme}
          defaultOpen={false}
        >
          {narr.activations.map((a: any, i: number) => (
            <View key={`act-${i}`} style={styles.threadRow}>
              <Text style={[styles.threadHead, { color: theme.text }]}>
                {a.side === 'personality' ? 'Personality' : 'Design'} · {a.planet} · {a.gate}.{a.line}
              </Text>
              <Text style={[styles.threadText, { color: theme.textSecondary }]}>{stripDiagnostics(a.text)}</Text>
              <EvidenceDetails evidence={a.evidence} theme={theme} />
            </View>
          ))}
        </Section>
      )}

      {/* 7. Incarnation Cross */}
      {narr.incarnation_cross && (
        <Section title="Incarnation Cross" subtitle="Four activations, one configured pattern" theme={theme} defaultOpen={false}>
          <Text style={[styles.h2, { color: theme.text }]}>{narr.incarnation_cross.label || cm.incarnation_cross || 'Incarnation Cross'}</Text>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{stripDiagnostics(narr.incarnation_cross.text)}</Text>
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

      {/* 8. Personality and Design activations — full table */}
      {!!(at.personality && at.design) && (
        <Section
          title="Personality and Design Activations"
          subtitle={`13 activation points on each side · Personality ${at.counts?.personality_present ?? 0}/13 · Design ${at.counts?.design_present ?? 0}/13`}
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

      {/* 9. Methodology & availability */}
      <Section title="Methodology & availability" subtitle="How this chart is calculated and what is intentionally hidden" theme={theme} defaultOpen={false}>
        <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
          Definition topology is derived independently from the connected-component graph of your defined-centre / defined-channel network — it is never taken on trust from an upstream label.
        </Text>
        <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
          Split sub-classification (Small / Wide) is intentionally not shown. There is no formally verified, independently reproducible algorithm for it in the current build; the topology itself remains accurate.
        </Text>
        <Text style={[styles.methodologyNote, { color: theme.textTertiary }]}>
          Fine-grain activation fields (color · tone · base) remain hidden pending an independent HD-software calibration fixture. Gate and line are verified and shown.
        </Text>
      </Section>
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
  const allNames = Array.from(new Set([...personality.map((r) => r.planet), ...design.map((r) => r.planet)]));
  const rows = allNames.map((planet) => ({
    planet,
    p: byPlanet(personality, planet),
    d: byPlanet(design, planet),
  }));

  const renderCell = (row: any) => {
    if (!row || row.missing) return '—';
    if (advancedVerified && row.full_formatted) return row.full_formatted;
    return row.formatted || `${row.gate ?? '—'}.${row.line ?? '—'}`;
  };

  const isNarrow = Platform.OS !== 'web' || (typeof window !== 'undefined' && window.innerWidth < 360);
  const table = (
    <View>
      <View style={[styles.actHead, { borderColor: theme.border }]}>
        <Text style={[styles.actHeadCell, { color: theme.textTertiary, flex: 1.4 }]}>Activation point</Text>
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

// Default export retained for legacy imports — renders Explore only,
// which prevents any accidental "master reading" duplication.
const HumanDesignDeepDiveSections: React.FC<Props> = (props) => (
  props.mode === 'reading' ? <HDReadingSections {...props} /> : <HDExploreSections {...props} />
);
export default HumanDesignDeepDiveSections;

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
  methodologyNote: { fontSize: 12, marginTop: 8, fontStyle: 'italic' },
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
