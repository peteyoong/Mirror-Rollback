// ============================================
// BAZI EVIDENCE LAYER — labels & flow verbs
// Pure data. Drives the structural evidence cards beneath the wisdom layer.
// No coupling to backend; consumes only signals.bazi.diagnostics fields.
// MARKER: bazi-evidence-layer-v2
// ============================================

export const BAZI_EVIDENCE_BUILD_MARKER = 'bazi-evidence-layer-v2';

export type BaziCycle =
  | 'a_produces_b' | 'b_produces_a'
  | 'a_controls_b' | 'b_controls_a'
  | 'same' | 'neutral' | 'unknown';

export type AnimalRelation = 'harmony' | 'clash' | 'same' | 'neutral' | 'unknown';

// Direction-of-flow verbs per element pair (producer side / receiver side).
// For control cycles the same table is read with controller/controlled semantics.
type VerbTriple = [string, string, string];
type FlowVerbs = { a: VerbTriple; b: VerbTriple };

const FLOW_PRODUCES: Record<string, FlowVerbs> = {
  'Wood->Fire':   { a: ['ignites', 'feeds', 'fuels'],            b: ['expresses', 'amplifies', 'shows'] },
  'Fire->Earth':  { a: ['warms', 'deposits', 'enriches'],        b: ['holds', 'absorbs', 'gathers'] },
  'Earth->Metal': { a: ['concentrates', 'pressurises', 'refines'], b: ['extracts', 'precipitates', 'clarifies'] },
  'Metal->Water': { a: ['refines', 'structures', 'names'],       b: ['adapts', 'metabolises', 'responds'] },
  'Water->Wood':  { a: ['nourishes', 'moves', 'carries'],        b: ['grows', 'receives', 'extends'] },
};

const FLOW_CONTROLS: Record<string, FlowVerbs> = {
  'Wood->Earth':  { a: ['shapes', 'bounds', 'roots into'],       b: ['yields', 'softens', 'redirects'] },
  'Fire->Metal':  { a: ['shapes', 'tests', 'melts'],             b: ['yields', 'softens', 'redirects'] },
  'Earth->Water': { a: ['shapes', 'directs', 'contains'],        b: ['yields', 'softens', 'redirects'] },
  'Metal->Wood':  { a: ['shapes', 'cuts', 'pares'],              b: ['yields', 'softens', 'redirects'] },
  'Water->Fire':  { a: ['shapes', 'cools', 'tempers'],           b: ['yields', 'softens', 'redirects'] },
};

const SAME_VERBS: Record<string, VerbTriple> = {
  Wood:  ['extends', 'opens', 'grows'],
  Fire:  ['expresses', 'illuminates', 'warms'],
  Earth: ['holds', 'steadies', 'gathers'],
  Metal: ['refines', 'names', 'discerns'],
  Water: ['deepens', 'adapts', 'flows'],
};

export interface FlowRow { left: string; right: string; }

/**
 * Returns 3 flow-direction rows for the Direction-of-Flow mini-table.
 * Names are inserted by the renderer — this function returns just verbs.
 * For cycle='same' the rows show shared verbs (both sides identical).
 * For cycle='neutral' returns empty array — the renderer should show a
 * single explanatory line instead.
 */
export function buildFlowRows(
  cycle: BaziCycle,
  elementA: string,
  elementB: string,
  nameA: string,
  nameB: string,
): FlowRow[] {
  if (cycle === 'a_produces_b' || cycle === 'a_controls_b') {
    const table = cycle === 'a_produces_b' ? FLOW_PRODUCES : FLOW_CONTROLS;
    const verbs = table[`${elementA}->${elementB}`];
    if (!verbs) return [];
    return verbs.a.map((va, i) => ({ left: `${nameA} ${va}`, right: `${nameB} ${verbs.b[i]}` }));
  }
  if (cycle === 'b_produces_a' || cycle === 'b_controls_a') {
    const table = cycle === 'b_produces_a' ? FLOW_PRODUCES : FLOW_CONTROLS;
    const verbs = table[`${elementB}->${elementA}`];
    if (!verbs) return [];
    return verbs.a.map((vb, i) => ({ left: `${nameB} ${vb}`, right: `${nameA} ${verbs.b[i]}` }));
  }
  if (cycle === 'same') {
    const v = SAME_VERBS[elementA];
    if (!v) return [];
    return v.map(vw => ({ left: `${nameA} ${vw}`, right: `${nameB} ${vw}` }));
  }
  return []; // neutral / unknown
}

export function flowHeaderForCycle(cycle: BaziCycle): string {
  if (cycle === 'same') return 'Shared Operating Mode';
  if (cycle === 'neutral' || cycle === 'unknown') return 'No Automatic Cycle';
  return 'Direction of Flow';
}

export function geometryArrow(cycle: BaziCycle, elementA: string, elementB: string): string {
  if (cycle === 'a_produces_b' || cycle === 'a_controls_b') return `${elementA} → ${elementB}`;
  if (cycle === 'b_produces_a' || cycle === 'b_controls_a') return `${elementB} → ${elementA}`;
  if (cycle === 'same')    return `${elementA} ↔ ${elementB}`;
  return `${elementA} · ${elementB}`;
}

// ---- Structural labels for the existing strings (positional fallback) ----
// Index-based mapping by cycle. Each label is a short observational noun
// phrase that prefixes the existing string in the evidence card.

type LabelSet = { strengthen: string[]; growth: string[]; shadow: string[] };

const DEFAULT_LABELS: LabelSet = {
  strengthen: ['Functional fit', 'Complementary mode', 'Mutual reinforcement'],
  growth:     ['Perspective expansion', 'Acknowledgement asymmetry', 'Generational contrast'],
  shadow:     ['Ledger formation', 'Suppressed need', 'Pattern blindness'],
};

const CYCLE_LABELS: Partial<Record<BaziCycle, LabelSet>> = {
  a_produces_b: {
    strengthen: ['Asymmetric nourishment', 'Stabilising function', 'Receptive recognition'],
    growth:     ['Perspective expansion', 'Acknowledgement asymmetry', 'Generational contrast'],
    shadow:     ['Ledger formation', 'Quiet entitlement', 'Producer exhaustion'],
  },
  b_produces_a: {
    strengthen: ['Upstream contribution', 'Quiet sustenance', 'Sequence respect'],
    growth:     ['Permeability', 'Receiving discipline', 'Generational contrast'],
    shadow:     ['Unrecognised dependency', 'Capacity depletion', 'Hidden asymmetry'],
  },
  a_controls_b: {
    strengthen: ['Consensual refinement', 'Structural pressure', 'Capacity building'],
    growth:     ['Pressure transparency', 'Standard naming', 'Generational contrast'],
    shadow:     ['Refinement-as-surveillance', 'Brittle contraction', 'Warmth thinning'],
  },
  b_controls_a: {
    strengthen: ['Friction as care', 'Standard holding', 'Accountable contact'],
    growth:     ['Reframe of pressure', 'Visible standard', 'Generational contrast'],
    shadow:     ['Shame collapse', 'Pressure intensification', 'Closed loop'],
  },
  same: {
    strengthen: ['Shared idiom', 'Recognition without translation', 'Aligned pacing'],
    growth:     ['Imported difference', 'External corrective', 'Generational contrast'],
    shadow:     ['Shared blind spot', 'Mutual confirmation', 'Stasis disguised as agreement'],
  },
  neutral: {
    strengthen: ['Conscious agreement', 'Built reciprocity', 'Explicit choice'],
    growth:     ['Intentional construction', 'Named purpose', 'Generational contrast'],
    shadow:     ['Parallel living', 'Comfortable distance', 'Drift'],
  },
};

export function labelFor(cycle: BaziCycle, bucket: 'strengthen' | 'growth' | 'shadow', idx: number): string {
  const set = CYCLE_LABELS[cycle] || DEFAULT_LABELS;
  const arr = set[bucket];
  return arr[idx] || arr[arr.length - 1] || DEFAULT_LABELS[bucket][0];
}

export function animalRelationLabel(rel: AnimalRelation, animalA: string, animalB: string): string {
  if (rel === 'harmony') return `${animalA} ⇌ ${animalB} — harmony`;
  if (rel === 'clash')   return `${animalA} ⚠ ${animalB} — clash`;
  if (rel === 'same')    return `${animalA} = ${animalB} — same`;
  return `${animalA} · ${animalB} — neutral`;
}

export function growthTriggerSubtitle(rel: AnimalRelation): string {
  if (rel === 'harmony') return 'Synchronised pacing — growth comes through resonance.';
  if (rel === 'clash')   return 'Generational instinct divergence — growth comes through reconciling opposites.';
  if (rel === 'same')    return 'Identical year-energy — growth comes through finding contrast outside the pair.';
  return 'Growth comes through perspective expansion. You rarely grow in the same way — you grow by exposing each other to different worlds.';
}
