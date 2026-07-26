/**
 * LensContractView — 7 progressive-disclosure sections in a single file.
 *
 * Each section knows how to render its own `availability="unavailable"`
 * state explicitly — Session-2 Content Governance rule "missing
 * information over false coherence".
 *
 * build_marker: lens-contract-view-v1
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type {
  LensEnvelope,
  AtAGlanceLayer,
  StructureLayer,
  CoreStoryLayer,
  ComponentStoriesLayer,
  IntegrationLayer,
  EvidenceLayer,
  TodayTimingLayer,
  MaterialClaim,
  EvidenceRef,
  MissingSlot,
} from '../../types/lens_content_contract';

const UNAVAILABLE_NOTE =
  '(Not yet available — this section will populate as the lens rebuild lands.)';

// ── util ────────────────────────────────────────────────────────────
const isPresent = (a: string | undefined) => a === 'present' || a === 'partial' || a === undefined;

// ── shared bits ─────────────────────────────────────────────────────
const SectionTitle: React.FC<{ label: string; subtle?: boolean }> = ({ label, subtle }) => (
  <Text style={[styles.sectionLabel, subtle && styles.sectionLabelSubtle]}>{label}</Text>
);

const UnavailableBlock: React.FC<{ reason?: string }> = ({ reason }) => (
  <View style={styles.unavailable}>
    <Text style={styles.unavailableText}>{reason || UNAVAILABLE_NOTE}</Text>
  </View>
);

const MissingSlotsList: React.FC<{ slots?: MissingSlot[] }> = ({ slots }) => {
  if (!slots || slots.length === 0) return null;
  return (
    <View style={{ marginTop: 8 }}>
      {slots.map((s, i) => (
        <View key={`ms-${i}`} style={styles.missingRow}>
          <Text style={styles.missingWhat}>· {s.what}</Text>
          <Text style={styles.missingWhy}>{s.why}</Text>
          {!!s.could_be_shown_if && (
            <Text style={styles.missingIf}>Available when: {s.could_be_shown_if}</Text>
          )}
        </View>
      ))}
    </View>
  );
};

const EvidenceInline: React.FC<{ refs?: EvidenceRef[] }> = ({ refs }) => {
  if (!refs || refs.length === 0) return null;
  return (
    <View style={{ marginTop: 4 }}>
      {refs.slice(0, 3).map((r, i) => (
        <Text key={`ev-${i}`} style={styles.evidenceLine}>
          · from {r.source_lens} → {r.calculation}
          {r.origin ? `  · ${r.origin}` : ''}
          {r.confidence && r.confidence !== 'unknown' ? `  · ${r.confidence}` : ''}
        </Text>
      ))}
    </View>
  );
};

const ClaimRow: React.FC<{ label: string; claim: MaterialClaim | undefined }> = ({ label, claim }) => {
  if (!claim || !claim.text) return null;
  return (
    <View style={{ marginBottom: 10 }}>
      <Text style={styles.claimLabel}>{label}</Text>
      <Text style={styles.claimBody}>{claim.text}</Text>
      <EvidenceInline refs={claim.evidence} />
    </View>
  );
};

// ── 1. AT A GLANCE ─────────────────────────────────────────────────
export const AtAGlanceCard: React.FC<{ layer: AtAGlanceLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="AT A GLANCE" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        {!!layer?.essential_facts?.length && (
          <View style={styles.facts}>
            {layer.essential_facts.map((f, i) => (
              <View key={`fact-${i}`} style={styles.factPill}>
                <Text style={styles.factLabel}>{f.label}</Text>
                <Text style={styles.factValue}>{f.value}</Text>
              </View>
            ))}
          </View>
        )}
        {!!layer?.recognition_statement && (
          <Text style={styles.recognition}>{layer.recognition_statement}</Text>
        )}
        {!!layer?.lens_can_claim?.length && (
          <View style={{ marginTop: 8 }}>
            <Text style={styles.canClaimLabel}>This lens can:</Text>
            {layer.lens_can_claim.map((s, i) => (
              <Text key={`can-${i}`} style={styles.canClaimItem}>· {s}</Text>
            ))}
          </View>
        )}
        {!!layer?.lens_cannot_claim?.length && (
          <View style={{ marginTop: 6 }}>
            <Text style={styles.cannotClaimLabel}>Does not claim:</Text>
            {layer.lens_cannot_claim.map((s, i) => (
              <Text key={`cant-${i}`} style={styles.cannotClaimItem}>· {s}</Text>
            ))}
          </View>
        )}
      </>
    )}
  </View>
);

// ── 2. STRUCTURE ────────────────────────────────────────────────────
export const StructureCard: React.FC<{ layer: StructureLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="STRUCTURE" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        {!!layer?.components?.length && layer.components.map((c, i) => (
          <View key={`struct-${i}`} style={styles.componentRow}>
            <Text style={styles.componentLabel}>{c.label}</Text>
            {c.value && typeof c.value === 'object' && (
              <Text style={styles.componentValue}>
                {Object.entries(c.value as Record<string, unknown>)
                  .slice(0, 4)
                  .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                  .join(' · ')}
              </Text>
            )}
          </View>
        ))}
        <MissingSlotsList slots={layer?.missing} />
      </>
    )}
  </View>
);

// ── 3. CORE STORY ───────────────────────────────────────────────────
export const CoreStoryCard: React.FC<{ layer: CoreStoryLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="CORE STORY" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        <ClaimRow label="Essence" claim={layer.essence} />
        <ClaimRow label="Capacity" claim={layer.capacity} />
        <ClaimRow label="Shadow / Distortion" claim={layer.shadow_or_distortion} />
        <ClaimRow label="Central Tension" claim={layer.central_tension} />
        <ClaimRow label="Developmental Possibility" claim={layer.developmental_possibility} />
        <ClaimRow label="Practical Application" claim={layer.practical_application} />
        <ClaimRow label="Reflection" claim={layer.reflection_question} />
      </>
    )}
  </View>
);

// ── 4. COMPONENT STORIES ────────────────────────────────────────────
export const ComponentStoriesCard: React.FC<{ layer: ComponentStoriesLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="COMPONENT STORIES" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        {(layer?.stories || []).map((s, i) => (
          <View key={`cs-${i}`} style={styles.componentStory}>
            <Text style={styles.componentStoryTitle}>{s.component_id}</Text>
            <ClaimRow label="What it is" claim={s.what_it_represents} />
            <ClaimRow label="Why it matters" claim={s.why_it_matters} />
            <ClaimRow label="Recognition" claim={s.recognition} />
            <ClaimRow label="Capacity" claim={s.capacity} />
            <ClaimRow label="Distortion" claim={s.distortion} />
            {s.productive_tension && <ClaimRow label="Productive Tension" claim={s.productive_tension} />}
            <ClaimRow label="What Helps" claim={s.what_helps} />
          </View>
        ))}
      </>
    )}
  </View>
);

// ── 5. INTEGRATION ──────────────────────────────────────────────────
export const IntegrationCard: React.FC<{ layer: IntegrationLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="INTEGRATION" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        <ClaimRow label="How they operate together" claim={layer.how_they_operate_together} />
        {(layer.complementary_qualities || []).map((c, i) => (
          <ClaimRow key={`comp-${i}`} label="Complementary" claim={c} />
        ))}
        {(layer.contradictions || []).map((c, i) => (
          <ClaimRow key={`contr-${i}`} label="Contradiction" claim={c} />
        ))}
        {(layer.productive_tensions || []).map((c, i) => (
          <ClaimRow key={`pt-${i}`} label="Productive Tension" claim={c} />
        ))}
        <MissingSlotsList slots={layer.unresolved} />
      </>
    )}
  </View>
);

// ── 6. EVIDENCE ─────────────────────────────────────────────────────
export const EvidenceCard: React.FC<{ layer: EvidenceLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="EVIDENCE · WHY MIRROR IS SAYING THIS" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        <EvidenceInline refs={layer.all_refs} />
        {layer.engine_versions && Object.keys(layer.engine_versions).length > 0 && (
          <Text style={styles.engineVersions}>
            engines: {Object.entries(layer.engine_versions).map(([k, v]) => `${k}=${v}`).join(', ')}
          </Text>
        )}
      </>
    )}
  </View>
);

// ── 7. TODAY / TIMING ───────────────────────────────────────────────
export const TodayTimingCard: React.FC<{ layer: TodayTimingLayer }> = ({ layer }) => (
  <View style={styles.section}>
    <SectionTitle label="TODAY · TIMING" />
    {!isPresent(layer?.availability) ? <UnavailableBlock /> : (
      <>
        {(layer.signals || []).map((s, i) => (
          <View key={`ts-${i}`} style={styles.timingSignal}>
            <Text style={styles.timingHead}>
              {s.current_factor} → {s.structural_target}
            </Text>
            <Text style={styles.timingInteraction}>{s.interaction}</Text>
            <ClaimRow label="What may be observed" claim={s.interpretation} />
          </View>
        ))}
        <MissingSlotsList slots={layer.missing} />
      </>
    )}
  </View>
);

// ── ROOT: full envelope ────────────────────────────────────────────
export const LensContractView: React.FC<{ envelope: LensEnvelope }> = ({ envelope }) => (
  <View>
    <AtAGlanceCard        layer={envelope.at_a_glance} />
    <StructureCard        layer={envelope.structure} />
    <CoreStoryCard        layer={envelope.core_story} />
    <ComponentStoriesCard layer={envelope.component_stories} />
    <IntegrationCard      layer={envelope.integration} />
    <EvidenceCard         layer={envelope.evidence} />
    <TodayTimingCard      layer={envelope.today_timing} />
  </View>
);

// ── styles ─────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  section: { marginBottom: 20, paddingHorizontal: 4 },
  sectionLabel: { fontSize: 11, letterSpacing: 1, fontWeight: '600', marginBottom: 10, opacity: 0.65 },
  sectionLabelSubtle: { opacity: 0.4 },
  unavailable: { padding: 10, borderRadius: 6, borderWidth: 1, borderColor: '#333' },
  unavailableText: { fontStyle: 'italic', opacity: 0.55 },
  missingRow: { marginBottom: 6 },
  missingWhat: { fontWeight: '500' },
  missingWhy: { opacity: 0.6, fontSize: 12 },
  missingIf: { opacity: 0.55, fontSize: 11, fontStyle: 'italic' },
  evidenceLine: { fontSize: 11, opacity: 0.55, marginLeft: 4 },
  claimLabel: { fontSize: 12, fontWeight: '600', marginBottom: 2, opacity: 0.7 },
  claimBody: { fontSize: 14, lineHeight: 20 },
  facts: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 as any },
  factPill: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, backgroundColor: '#222' },
  factLabel: { fontSize: 10, opacity: 0.6 },
  factValue: { fontSize: 13, fontWeight: '600' },
  recognition: { marginTop: 10, fontSize: 14, lineHeight: 20 },
  canClaimLabel: { fontSize: 11, fontWeight: '600', opacity: 0.7 },
  canClaimItem: { fontSize: 12, opacity: 0.7, marginLeft: 6 },
  cannotClaimLabel: { fontSize: 11, fontWeight: '600', opacity: 0.55 },
  cannotClaimItem: { fontSize: 12, opacity: 0.55, marginLeft: 6 },
  componentRow: { marginBottom: 6 },
  componentLabel: { fontSize: 13, fontWeight: '500' },
  componentValue: { fontSize: 11, opacity: 0.55, marginLeft: 6 },
  componentStory: { marginBottom: 12, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: '#222' },
  componentStoryTitle: { fontSize: 13, fontWeight: '600', marginBottom: 6 },
  engineVersions: { fontSize: 10, opacity: 0.4, marginTop: 6 },
  timingSignal: { marginBottom: 10 },
  timingHead: { fontSize: 13, fontWeight: '500' },
  timingInteraction: { fontSize: 12, opacity: 0.6 },
});

export default LensContractView;
