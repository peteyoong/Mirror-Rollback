# Cross-Lens Synthesis · Phase 2 (tension / contradiction)
**Build marker:** cross_lens_synthesis_v2.1.0
**Date:** 2026-06-12 (Stage 1 · 10% live)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED · ✅ RECEIPT-ONLY (LIVE OUTPUTS UNCHANGED)

---

## 1. Goal

Surface *tension*, *agreement*, and *polarity* patterns across the
lens space without touching existing lens outputs. Specifically:

* Detect domain-pair tensions (e.g. relationship↔leadership = founder
  with spouse pull).
* Detect cluster agreements (e.g. career+leadership+money = founder_op).
* Emit lens coverage (which lens vocabularies the message references).
* Strictly additive — no impact on `lens_payloads`, `lens_priority`,
  or `intent_envelope`.

## 2. Implementation

### 2.1 New service module: `services/cross_lens_synthesis_v2.py`

Pure function with no DB / network / randomness. Called from the
shadow-receipt builder; writes a single nested dict per receipt.

Thresholds (tuned conservatively):

```python
TENSION_FLOOR        = 0.45   # both sides must exceed this
TENSION_PARITY_BAND  = 0.25   # max delta to be called a "tension"
AGREEMENT_FLOOR      = 0.40   # all members of a cluster must exceed this
```

### 2.2 Polarity pairs (ordered — first match wins for top-level label)

```
relationship  ↔ leadership      → founder_with_spouse_pull
relationship  ↔ career          → work_relationship_pull
leadership    ↔ health          → leading_through_burnout
career        ↔ purpose         → role_purpose_misalignment
money         ↔ purpose         → runway_vs_mission
growth        ↔ family          → individuation_vs_roots
identity      ↔ relationship    → self_vs_partnered_self
life_direction↔ identity         → becoming_question
```

### 2.3 Agreement clusters (cluster qualifies when ≥2 members exceed floor)

```
founder_op:      [career, leadership, money]
self_inquiry:    [identity, growth, life_direction]
relational_arc:  [relationship, family, parenting]
vocational_arc:  [career, purpose, life_direction]
embodied_arc:    [health, growth, spirituality]
```

### 2.4 Receipt shape (additive only)

```json
"cross_lens_synthesis_v2": {
  "version":     "cross_lens_synthesis_v2.1.0",
  "computed":    true,
  "agreements":  [{ "cluster": "founder_op", "domains": [...], "min_score": 0.62 }],
  "tensions":    [{ "pair": [...], "scores": [...], "delta": 0.04, "label": "..." }],
  "polarity":    "founder_with_spouse_pull",
  "lens_coverage":          ["astrology", "human_design", "enneagram"],
  "lens_outputs_preserved": true,
  "thresholds":  { ... }
}
```

## 3. Validation

### 3.1 Unit tests (`tests/test_cross_lens_synthesis_v2.py`)

```
TestComputeSynthesisV2::test_preserves_lens_outputs             PASSED
TestComputeSynthesisV2::test_empty_input_no_false_positives     PASSED
TestComputeSynthesisV2::test_malformed_input_does_not_raise     PASSED
TestComputeSynthesisV2::test_synthetic_tension_detected         PASSED  ★
TestComputeSynthesisV2::test_synthetic_agreement_detected       PASSED  ★
TestComputeSynthesisV2::test_lens_coverage_detected_from_message PASSED
TestComputeSynthesisV2::test_golden_polarity_cases_from_yaml    PASSED

7 passed in 0.08s
```

### 3.2 Properties verified

| Property | Status |
|---|---|
| Lens outputs preserved | ✅ `lens_outputs_preserved=true` on every output |
| No false positives on empty input | ✅ returns empty agreements + tensions |
| Never raises | ✅ catches all exceptions, returns `computed=false` |
| Synthetic tension detection | ✅ polarity label correct |
| Synthetic agreement detection | ✅ cluster detected |
| Lens coverage detection | ✅ finds astrology + human_design cues |

### 3.3 Receipt-only constraint (no live-response impact)

The `compute_synthesis_v2()` helper is wired into
`services/mirror_chat_shadow.py` at the receipt-building stage —
AFTER `build_receipt()` returns. It does NOT participate in the
classifier, the resolver, or the live API response path. All eight
baseline B3-scope suites (golden_set + founder + lens_jargon +
educational + forum_topology) retained 100% top-1 after this
landed — confirming the additive guarantee.

## 4. Files Touched

```
A backend/services/cross_lens_synthesis_v2.py            (192 lines)
A backend/tests/test_cross_lens_synthesis_v2.py          (133 lines)
A backend/tests/intent_router_v2/golden_set_cross_lens_v2.yaml  (6 cases)
M backend/services/mirror_chat_shadow.py   (+22 lines, synthesis hook)
```

## 5. Caveats / Known Limits

* Thresholds are conservative — some real-world tension messages
  produce one strong domain (collapse) rather than two near-equal
  scores. The synthesis surfaces are sparse but never wrong.
* Polarity labels are descriptive, not prescriptive — they tag the
  shape of the tension but don't recommend a path through it.
* Future work: surface synthesis hints to the live response (Phase 3),
  but that requires an explicit user authorization since it would
  exit shadow-only mode.
