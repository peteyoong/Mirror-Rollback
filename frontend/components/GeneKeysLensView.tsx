/**
 * GeneKeysLensView — The Mirror standalone Gene Keys lens (Session 4A scaffold)
 * ============================================================================
 * Structural foundation only.  Consumes the canonical mechanics endpoint
 * `GET /api/gene-keys/mechanics/{userId}` (parent-owned single fetch).
 *
 * Session-4A guardrails:
 *   • Reading tab renders an explicit "pending Session 4B" state — no
 *     fabricated master story.
 *   • Explore tab shows the profile overview, three Golden Path sequences,
 *     per-sphere details, and a progressively disclosed methodology note.
 *   • Star Pearl is not surfaced.
 *   • No Human Design vocabulary is imported or displayed.
 *   • Layout works at 320px width (narrow mobile).
 *
 * When Session 4B lands the Reading tab will be enabled and this file will
 * gain IP-safe Mirror-authored narrative content.
 */
import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import LensTabBar, { LensTabDef } from './LensTabBar';

type SphereMechanics = {
  sphere_name: string;
  sequences: string[];
  gene_key: number | null;
  line: number | null;
  activation: { planet: string; chart_side: 'personality' | 'design' };
  source_longitude: number | null;
  evidence_ref: Record<string, any>;
  content_provenance: 'mirror_original' | 'structural_label' | 'user_authored';
  structural_labels: {
    shadow_label_ref?: string | null;
    gift_label_ref?: string | null;
    siddhi_label_ref?: string | null;
  };
  verification_status: 'verified' | 'discrepancy_held' | 'engine_missing' | 'unavailable';
  verification_note?: string | null;
};

type MechanicsEnvelope = {
  mechanics_version: string;
  sphere_map_version: string;
  methodology: {
    version: string;
    disclosure: string;
    sphere_map_reference_urls: string[];
    longitude_engine: string;
    gate_mandala: string;
  };
  profile_availability: 'present' | 'partial' | 'unavailable';
  sequences: Record<string, SphereMechanics[]>;
  unique_spheres: SphereMechanics[];
  shared_activation_roles: { primary: string; shared: string; reason: string }[];
  all_spheres: SphereMechanics[];
  missing_fields: string[];
  verification_status: 'verified' | 'partial' | 'unavailable';
  verification_discrepancies: unknown[];
  methodology_disclosure: string;
  star_pearl_availability: 'UNAVAILABLE_OR_DEFERRED' | string;
  star_pearl_reason: string;
  reading_availability: { state: 'pending_session_4b'; reason: string };
};

const TABS: LensTabDef[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'activation', label: 'Activation' },
  { key: 'venus', label: 'Venus' },
  { key: 'pearl', label: 'Pearl' },
  { key: 'reading', label: 'Reading' },
  { key: 'methodology', label: 'Methodology' },
];

const SEQUENCE_KEY_TO_TAG: Record<string, string> = {
  activation: 'Activation',
  venus: 'Venus',
  pearl: 'Pearl',
};

export default function GeneKeysLensView({ userId }: { userId: string }) {
  const { theme } = useTheme();
  const [tab, setTab] = useState<string>('overview');
  const [mechanics, setMechanics] = useState<MechanicsEnvelope | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Parent-owned single fetch — no duplicate mechanics requests.
  useEffect(() => {
    let cancelled = false;
    async function fetchMechanics() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<MechanicsEnvelope>(`/gene-keys/mechanics/${userId}`);
        if (!cancelled) setMechanics(res.data);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Unable to load Gene Keys profile.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (userId) fetchMechanics();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const activeSequence = useMemo<SphereMechanics[]>(() => {
    if (!mechanics) return [];
    const tag = SEQUENCE_KEY_TO_TAG[tab];
    if (!tag) return [];
    return mechanics.sequences[tag] || [];
  }, [mechanics, tab]);

  if (loading) {
    return (
      <View style={[styles.center, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="small" color={theme.accent} />
        <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 12 }]}>
          Loading your Gene Keys profile…
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.center, { backgroundColor: theme.background }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
      </View>
    );
  }

  if (!mechanics || mechanics.profile_availability === 'unavailable') {
    return (
      <View style={[styles.center, { backgroundColor: theme.background }]}>
        <Text style={[styles.mutedTitle, { color: theme.textSecondary }]}>
          Profile not yet available
        </Text>
        <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 8, textAlign: 'center' }]}>
          We couldn&apos;t derive your Gene Keys profile from your birth data.
          Add or verify your birth details in Settings.
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <LensTabBar tabs={TABS} activeKey={tab} onChange={setTab} theme={theme} />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {tab === 'overview' && <OverviewPanel mechanics={mechanics} onOpenMethodology={() => setTab('methodology')} theme={theme} />}
        {(tab === 'activation' || tab === 'venus' || tab === 'pearl') && (
          <SequencePanel
            sequenceName={SEQUENCE_KEY_TO_TAG[tab]}
            spheres={activeSequence}
            sharedRoles={mechanics.shared_activation_roles}
            theme={theme}
          />
        )}
        {tab === 'reading' && <ReadingPendingPanel reason={mechanics.reading_availability.reason} theme={theme} />}
        {tab === 'methodology' && <MethodologyPanel mechanics={mechanics} theme={theme} />}

        <View style={{ height: 32 }} />
      </ScrollView>
    </View>
  );
}

// -----------------------------------------------------------------------------
// Overview
// -----------------------------------------------------------------------------

function OverviewPanel({
  mechanics,
  onOpenMethodology,
  theme,
}: {
  mechanics: MechanicsEnvelope;
  onOpenMethodology: () => void;
  theme: any;
}) {
  const discrepancyCount = mechanics.verification_discrepancies?.length ?? 0;
  return (
    <View style={styles.section}>
      <Text style={[styles.h1, { color: theme.text }]}>Your Golden Path</Text>
      <Text style={[styles.body, { color: theme.textSecondary, marginTop: 6 }]}>
        Three contemplative sequences derived from your True Sidereal activation.
      </Text>

      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <SphereBadge label="Activation" count={mechanics.sequences.Activation?.length ?? 0} theme={theme} />
        <SphereBadge label="Venus" count={mechanics.sequences.Venus?.length ?? 0} theme={theme} />
        <SphereBadge label="Pearl" count={mechanics.sequences.Pearl?.length ?? 0} theme={theme} />
      </View>

      <Text style={[styles.h2, { color: theme.text, marginTop: 20 }]}>Unique Spheres</Text>
      <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 4 }]}>
        {mechanics.unique_spheres.length} underlying activations.  Life&apos;s Work / Brand share one activation;
        Core / Vocation share one activation.
      </Text>

      {mechanics.verification_status !== 'verified' && (
        <View
          style={[
            styles.notice,
            { backgroundColor: theme.surface, borderColor: theme.border },
          ]}
        >
          <Text style={[styles.noticeTitle, { color: theme.text }]}>
            Some spheres are held pending review
          </Text>
          <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 6 }]}>
            {discrepancyCount} sphere{discrepancyCount === 1 ? '' : 's'} produced a value that differs from a
            legacy expectation.  We&apos;re showing only verified spheres by default while these are reviewed.
          </Text>
        </View>
      )}

      <TouchableOpacity onPress={onOpenMethodology} activeOpacity={0.7} style={styles.methodologyLink}>
        <Text style={[styles.methodologyLinkText, { color: theme.accent }]}>
          About this calculation →
        </Text>
      </TouchableOpacity>
    </View>
  );
}

function SphereBadge({ label, count, theme }: { label: string; count: number; theme: any }) {
  return (
    <View style={styles.badgeRow}>
      <Text style={[styles.badgeLabel, { color: theme.textSecondary }]}>{label}</Text>
      <Text style={[styles.badgeCount, { color: theme.text }]}>{count} spheres</Text>
    </View>
  );
}

// -----------------------------------------------------------------------------
// Sequence panel (Activation / Venus / Pearl)
// -----------------------------------------------------------------------------

function SequencePanel({
  sequenceName,
  spheres,
  sharedRoles,
  theme,
}: {
  sequenceName: string;
  spheres: SphereMechanics[];
  sharedRoles: MechanicsEnvelope['shared_activation_roles'];
  theme: any;
}) {
  return (
    <View style={styles.section}>
      <Text style={[styles.h1, { color: theme.text }]}>{sequenceName} Sequence</Text>
      <Text style={[styles.body, { color: theme.textSecondary, marginTop: 6 }]}>
        {sequenceName === 'Activation' && 'Life\u2019s Work, Evolution, Radiance, Purpose.'}
        {sequenceName === 'Venus' && 'Attraction, IQ, EQ, SQ, Core.'}
        {sequenceName === 'Pearl' && 'Vocation, Culture, Brand, Pearl.'}
      </Text>

      {spheres.map((s) => (
        <SphereCard key={s.sphere_name} sphere={s} sharedRoles={sharedRoles} theme={theme} />
      ))}
    </View>
  );
}

function SphereCard({
  sphere,
  sharedRoles,
  theme,
}: {
  sphere: SphereMechanics;
  sharedRoles: MechanicsEnvelope['shared_activation_roles'];
  theme: any;
}) {
  const isHeld = sphere.verification_status === 'discrepancy_held';
  const sharedWith = sharedRoles.find(
    (r) => r.primary === sphere.sphere_name || r.shared === sphere.sphere_name,
  );
  const sharedPartner =
    sharedWith?.primary === sphere.sphere_name ? sharedWith.shared : sharedWith?.primary;

  return (
    <View
      style={[
        styles.sphereCard,
        { backgroundColor: theme.surface, borderColor: theme.border },
        isHeld && { borderColor: 'rgba(255, 176, 96, 0.45)' },
      ]}
    >
      <View style={styles.sphereHeaderRow}>
        <Text style={[styles.sphereName, { color: theme.text }]}>{sphere.sphere_name}</Text>
        {!isHeld && sphere.gene_key !== null && (
          <Text style={[styles.sphereGate, { color: theme.accent }]}>
            Gene Key {sphere.gene_key}
            {sphere.line ? ` \u00B7 Line ${sphere.line}` : ''}
          </Text>
        )}
      </View>

      <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 4 }]}>
        {sphere.activation.chart_side === 'personality' ? 'Natal / Personality' : 'Pre-Natal / Design'}
        {' \u00B7 '}
        {sphere.activation.planet}
      </Text>

      {sharedPartner && (
        <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 4, fontStyle: 'italic' }]}>
          Shares this activation with {sharedPartner}.
        </Text>
      )}

      {isHeld && (
        <View style={[styles.heldNotice, { backgroundColor: 'rgba(255, 176, 96, 0.08)' }]}>
          <Text style={[styles.heldTitle, { color: theme.text }]}>Held pending review</Text>
          <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 4 }]}>
            This sphere&apos;s value differs from a legacy expectation.  Its details are hidden until the
            discrepancy is resolved.
          </Text>
        </View>
      )}

      {!isHeld && sphere.gene_key !== null && (
        <View style={{ marginTop: 12 }}>
          {(['shadow_label_ref', 'gift_label_ref', 'siddhi_label_ref'] as const).map((k) => {
            const val = sphere.structural_labels?.[k];
            if (!val) return null;
            return (
              <Text key={k} style={[styles.labelChip, { color: theme.textSecondary }]}>
                {val}
              </Text>
            );
          })}
          <Text style={[styles.mutedTiny, { color: theme.textTertiary, marginTop: 8 }]}>
            Structural labels only.  Reflective content ships in Session 4B.
          </Text>
        </View>
      )}
    </View>
  );
}

// -----------------------------------------------------------------------------
// Reading — explicit pending state
// -----------------------------------------------------------------------------

function ReadingPendingPanel({ reason, theme }: { reason: string; theme: any }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.h1, { color: theme.text }]}>Reading coming soon</Text>
      <Text style={[styles.body, { color: theme.textSecondary, marginTop: 8 }]}>{reason}</Text>
      <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 14 }]}>
        For now, use the Activation, Venus and Pearl tabs to explore the structure of your profile.
      </Text>
    </View>
  );
}

// -----------------------------------------------------------------------------
// Methodology — progressive disclosure
// -----------------------------------------------------------------------------

function MethodologyPanel({ mechanics, theme }: { mechanics: MechanicsEnvelope; theme: any }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.h1, { color: theme.text }]}>About this calculation</Text>
      <Text style={[styles.body, { color: theme.textSecondary, marginTop: 8 }]}>
        {mechanics.methodology_disclosure}
      </Text>

      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border, marginTop: 16 }]}>
        <MethodologyRow k="Mapping version" v={mechanics.sphere_map_version} theme={theme} />
        <MethodologyRow k="Longitude engine" v={mechanics.methodology.longitude_engine} theme={theme} />
        <MethodologyRow k="Gate mandala" v={mechanics.methodology.gate_mandala} theme={theme} />
      </View>

      <Text style={[styles.mutedSmall, { color: theme.textTertiary, marginTop: 16 }]}>
        Sphere-to-activation semantics follow the first-party Gene Keys correlation.  Longitudes, the Design
        (pre-natal) calculation and 64-gate placement come from The Mirror&apos;s governed True Sidereal
        activation engine.  We do not claim parity with the standard Gene Keys online profile unless
        independently verified.
      </Text>

      <Text style={[styles.mutedTiny, { color: theme.textTertiary, marginTop: 20 }]}>
        Star Pearl is deferred in this release.
      </Text>
    </View>
  );
}

function MethodologyRow({ k, v, theme }: { k: string; v: string; theme: any }) {
  return (
    <View style={styles.methRow}>
      <Text style={[styles.methKey, { color: theme.textTertiary }]}>{k}</Text>
      <Text style={[styles.methVal, { color: theme.textSecondary }]} numberOfLines={2}>
        {v}
      </Text>
    </View>
  );
}

// -----------------------------------------------------------------------------
// Styles
// -----------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 16, paddingTop: 12 },

  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },

  section: { paddingBottom: 24 },
  h1: { fontSize: 20, fontWeight: '500', letterSpacing: 0.2 },
  h2: { fontSize: 16, fontWeight: '500', letterSpacing: 0.2 },
  body: { fontSize: 14, lineHeight: 20 },
  mutedTitle: { fontSize: 15, fontWeight: '500' },
  mutedSmall: { fontSize: 12, lineHeight: 18 },
  mutedTiny: { fontSize: 11, lineHeight: 16, letterSpacing: 0.1 },
  errorText: { fontSize: 13, textAlign: 'center', paddingHorizontal: 24 },

  card: {
    marginTop: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    gap: 10,
  },
  badgeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    minHeight: 24,
  },
  badgeLabel: { fontSize: 13, fontWeight: '500' },
  badgeCount: { fontSize: 13 },

  notice: {
    marginTop: 20,
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  noticeTitle: { fontSize: 13, fontWeight: '500' },

  methodologyLink: { marginTop: 20, alignSelf: 'flex-start' },
  methodologyLinkText: { fontSize: 13, fontWeight: '500' },

  sphereCard: {
    marginTop: 12,
    padding: 14,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  sphereHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    gap: 8,
    flexWrap: 'wrap',
  },
  sphereName: { fontSize: 15, fontWeight: '500' },
  sphereGate: { fontSize: 13, fontWeight: '500' },

  heldNotice: {
    marginTop: 12,
    padding: 10,
    borderRadius: 8,
  },
  heldTitle: { fontSize: 12, fontWeight: '500' },

  labelChip: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 2,
  },

  methRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  methKey: { fontSize: 12, flexShrink: 0 },
  methVal: { fontSize: 12, textAlign: 'right', flexShrink: 1 },
});
