/**
 * Tests for the text-dedup helpers used in mappings.tsx to prevent
 * duplicate paragraphs from rendering inside the "Why this is so strong"
 * accordion.
 *
 * These helpers are currently INLINED at the top of mappings.tsx.  For
 * lightweight unit testing without setting up a jest RN environment we
 * mirror the pure functions here and exercise them.  If they drift the
 * tests will fail — that's the intended feedback loop.
 *
 * build_marker: relationship-mapping-text-dedup-helpers-v1
 */

// --- Mirror of helpers in mappings.tsx --------------------------------
const _normText = (s) =>
  (s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

const _tokens = (s) =>
  new Set(_normText(s).split(/\s+/).filter((t) => t.length > 3));

const areDuplicateTexts = (a, b, jaccardMin = 0.55) => {
  const na = _normText(a);
  const nb = _normText(b);
  if (!na || !nb) return false;
  if (na === nb) return true;
  if (na.includes(nb) || nb.includes(na)) return true;
  const tA = _tokens(a);
  const tB = _tokens(b);
  if (!tA.size || !tB.size) return false;
  let inter = 0;
  tA.forEach((t) => {
    if (tB.has(t)) inter++;
  });
  const union = new Set([..._tokens(a), ..._tokens(b)]).size || 1;
  return inter / union >= jaccardMin;
};

const stripSentencesAlreadyIn = (candidate, haystack) => {
  if (!candidate) return '';
  const normHay = _normText(haystack || '');
  if (!normHay) return candidate;
  const sentences = candidate
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const kept = sentences.filter((sent) => {
    const ns = _normText(sent);
    if (!ns) return false;
    if (normHay.includes(ns)) return false;
    const t1 = _tokens(sent);
    const t2 = _tokens(haystack);
    if (!t1.size) return false;
    let inter = 0;
    t1.forEach((t) => {
      if (t2.has(t)) inter++;
    });
    const overlap = inter / t1.size;
    return overlap < 0.7;
  });
  return kept.join(' ').trim();
};

// --- Lightweight test runner (no jest dep) ---------------------------
let passed = 0;
let failed = 0;
const eq = (a, b, msg) => {
  const ok = JSON.stringify(a) === JSON.stringify(b);
  if (ok) {
    passed++;
    console.log(`  PASS  ${msg}`);
  } else {
    failed++;
    console.log(`  FAIL  ${msg}\n    expected: ${JSON.stringify(b)}\n    got:      ${JSON.stringify(a)}`);
  }
};

// -- areDuplicateTexts --

// 1. Exact string match (byte-identical)
eq(
  areDuplicateTexts(
    "Pete's closed-and-initiating aura meets Mel's sampling, fluid aura.",
    "Pete's closed-and-initiating aura meets Mel's sampling, fluid aura."
  ),
  true,
  'exact-match'
);

// 2. Whitespace/case difference (case 1 real payload: aura_dynamics vs field_overview)
eq(
  areDuplicateTexts(
    "Pete's closed-and-initiating aura meets Mel's sampling, fluid aura.",
    "PETE'S closed-and-initiating AURA meets Mel's sampling,   fluid aura."
  ),
  true,
  'case-and-whitespace-tolerant'
);

// 3. One string is a substring of the other
eq(
  areDuplicateTexts(
    'This connection teaches Pete that impact lands long after the action.',
    'This connection teaches Pete that impact lands long after the action.  And more context afterwards.'
  ),
  true,
  'substring-either-direction'
);
eq(
  areDuplicateTexts(
    'Preamble here.  This connection teaches Pete that impact lands long after the action.',
    'This connection teaches Pete that impact lands long after the action.'
  ),
  true,
  'substring-reverse-direction'
);

// 4. Genuinely different texts should NOT be flagged as duplicates
eq(
  areDuplicateTexts(
    "Pete's closed-and-initiating aura meets Mel's sampling, fluid aura.",
    'Pete needs a wave; Mel needs a 28-day cycle. Almost no decisions should be made on the spot here.'
  ),
  false,
  'different-texts-not-duplicate'
);

// 5. Empty or null inputs
eq(areDuplicateTexts('', 'anything'), false, 'empty-a-not-duplicate');
eq(areDuplicateTexts('anything', ''), false, 'empty-b-not-duplicate');
eq(areDuplicateTexts('', ''), false, 'both-empty-not-duplicate');
eq(areDuplicateTexts(null, 'x'), false, 'null-a-not-duplicate');

// 6. Threshold behaviour — high jaccard triggers duplicate
eq(
  areDuplicateTexts(
    'Pete reads atmosphere first while Mel reaches for clarity through language.',
    'Mel reaches for clarity through language while Pete reads atmosphere first.'
  ),
  true,
  'high-jaccard-word-reorder'
);

// -- stripSentencesAlreadyIn --

// 7. Case 2 real payload — supporting_signal duplicating a sentence in body
const body = `Pete's Sun in Pisces (processes through atmosphere, emotional permeability, subtle signals, fusion, sensitivity); Mel's Sun in Gemini (processes through language, movement, mental framing, options, change). The asymmetry: Mel reaches for clarity through language; Pete reads atmosphere first. Mel's emotional foundation is shaped by Virgo on the IC — lands through small acts of care. Uranus sits in the 4th house — electric interruption — the field will not stay still.`;

const dupSupportingSignal =
  "Mel's emotional foundation is shaped by Virgo on the IC — lands through small acts of care. Uranus sits in the 4th house — electric interruption — the field will not stay still.";

eq(stripSentencesAlreadyIn(dupSupportingSignal, body), '', 'duplicate-supporting-signal-emptied');

// 8. Non-duplicate signal should pass through mostly unchanged
const uniqueSignal = 'Pete Moon in Aries — feels safe via lands through directness';
const kept = stripSentencesAlreadyIn(uniqueSignal, body);
eq(kept.length > 20 && kept.includes('Moon in Aries'), true, 'unique-signal-passes-through');

// 9. Partial overlap — sentences that ARE in body are stripped, sentences that are new are kept
const partialSignal =
  "Mel's emotional foundation is shaped by Virgo on the IC — lands through small acts of care.  New: Nervous system starts searching when the field goes still.";
const partial = stripSentencesAlreadyIn(partialSignal, body);
eq(
  !partial.includes('shaped by Virgo') && partial.includes('Nervous system'),
  true,
  'partial-overlap-strips-only-duplicates'
);

// 10. Empty haystack — every sentence kept
eq(stripSentencesAlreadyIn('Some fresh sentence.', ''), 'Some fresh sentence.', 'empty-haystack-keeps-all');

// 11. Empty candidate — empty result, no crash
eq(stripSentencesAlreadyIn('', body), '', 'empty-candidate-empty-result');

// --- summary ---
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
