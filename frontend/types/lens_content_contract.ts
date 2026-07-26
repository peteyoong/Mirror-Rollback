/**
 * Shared Lens Content Contract V1 — TypeScript types
 *
 * Mirror of /app/backend/services/lens_content_contract.py.
 * Both sides must stay in sync; a schema-parity test lives in
 * /app/backend/tests/test_lens_content_contract.py.
 *
 * build_marker: lens-content-contract-v1
 */

export type Availability = 'present' | 'partial' | 'unavailable';
export type Confidence = 'high' | 'medium' | 'emerging' | 'unknown';
export type ContentOrigin =
  | 'calculated'
  | 'assessed'
  | 'observed'
  | 'inferred'
  | 'generated';
export type TimeScope = 'lifelong' | 'phase' | 'year' | 'season' | 'day' | 'now';

export interface EvidenceRef {
  source_lens: string;
  calculation: string;
  factors_used?: string[];
  derivation_rule?: string | null;
  confidence?: Confidence;
  origin?: ContentOrigin;
  engine_version?: string | null;
  computed_at?: string | null;
  missing_or_disputed?: string[] | null;
}

export interface MaterialClaim {
  text: string;
  evidence?: EvidenceRef[];
  origin?: ContentOrigin;
  confidence?: Confidence;
}

export interface FactBadge {
  label: string;
  value: string;
  source_calculation?: string | null;
  origin?: ContentOrigin;
}

export interface MissingSlot {
  what: string;
  why: string;
  could_be_shown_if?: string | null;
  availability?: Availability;
}

export interface AtAGlanceLayer {
  essential_facts?: FactBadge[];
  recognition_statement: string;
  lens_can_claim?: string[];
  lens_cannot_claim?: string[];
  availability?: Availability;
}

export interface StructureComponent {
  component_id: string;
  label: string;
  value?: unknown;
  provenance?: EvidenceRef | null;
  availability?: Availability;
}

export interface StructureLayer {
  components?: StructureComponent[];
  calculation_provenance?: EvidenceRef | null;
  missing?: MissingSlot[];
  availability?: Availability;
}

export interface CoreStoryLayer {
  essence: MaterialClaim;
  capacity: MaterialClaim;
  shadow_or_distortion: MaterialClaim;
  central_tension: MaterialClaim;
  developmental_possibility: MaterialClaim;
  practical_application: MaterialClaim;
  reflection_question: MaterialClaim;
  availability?: Availability;
}

export interface ComponentStory {
  component_id: string;
  component_type: string;
  calculated_value?: unknown;
  what_it_represents: MaterialClaim;
  why_it_matters: MaterialClaim;
  connections?: string[];
  recognition: MaterialClaim;
  capacity: MaterialClaim;
  distortion: MaterialClaim;
  productive_tension?: MaterialClaim | null;
  what_helps: MaterialClaim;
  evidence?: EvidenceRef[];
  confidence?: Confidence;
  availability?: Availability;
}

export interface ComponentStoriesLayer {
  stories?: ComponentStory[];
  availability?: Availability;
}

export interface IntegrationLayer {
  how_they_operate_together: MaterialClaim;
  complementary_qualities?: MaterialClaim[];
  contradictions?: MaterialClaim[];
  productive_tensions?: MaterialClaim[];
  unresolved?: MissingSlot[];
  availability?: Availability;
}

export interface EvidenceLayer {
  all_refs?: EvidenceRef[];
  disputed?: string[];
  engine_versions?: Record<string, string>;
  availability?: Availability;
}

export interface TimingWindow {
  starts_at?: string | null;
  ends_at?: string | null;
  scope?: TimeScope;
}

export interface TimingSignal {
  current_factor: string;
  structural_target: string;
  interaction: string;
  window: TimingWindow;
  interpretation: MaterialClaim;
  confidence?: Confidence;
  evidence?: EvidenceRef[];
}

export interface TodayTimingLayer {
  signals?: TimingSignal[];
  missing?: MissingSlot[];
  availability?: Availability;
}

export interface LensEnvelope {
  lens: string;
  envelope_version: string;
  engine_version?: string | null;
  computed_at?: string | null;
  at_a_glance: AtAGlanceLayer;
  structure: StructureLayer;
  core_story: CoreStoryLayer;
  component_stories: ComponentStoriesLayer;
  integration: IntegrationLayer;
  evidence: EvidenceLayer;
  today_timing: TodayTimingLayer;
  progressive_disclosure_order?: string[];
}
