# Project Mirror V1 Integrity Contract

**Version:** 1.0.0  
**Status:** FROZEN  
**Effective Date:** 2025-06-15  

---

## Purpose

This contract defines the philosophical and computational invariants that must hold true for every deployment of Project Mirror V1. Any violation of this contract constitutes a regression and must block deployment.

---

## Contract Version

```typescript
export const MIRROR_V1_CONTRACT_VERSION = "1.0.0";
```

**Version Bump Rules:**
- PATCH (1.0.x): Bug fixes that don't change behavior
- MINOR (1.x.0): New features that don't modify existing invariants
- MAJOR (x.0.0): Any change that modifies invariants below

---

## Section A: Enneagram Integrity Invariants

### A1. Wing Display Invariant (CRITICAL)

**Invariant:** Wing must NEVER surface as `null` in user-facing UI.

**Enforcement:**
```
∀ user_facing_display:
  wing_display ∈ { "dominant", "leaning", "balanced", "not_clear" }
  wing_display ≠ null
  wing_display ≠ "null"
  wing_display ≠ "Wing null"
```

**Resolution Rules:**
| Internal State | UI Display |
|----------------|------------|
| `wing === number && confidence === high` | `dominant` → "Type Xw{wing}" |
| `wing === number && confidence !== high` | `leaning` → "Type X — leaning toward Wing {wing}" |
| `wing === 'balanced'` | `balanced` → "Type X — balanced wings ({left} & {right})" |
| `wing === null \|\| wing === undefined` | `not_clear` → "Type X — wing not yet clear" |

### A2. High Confidence Lock Invariant (CRITICAL)

**Invariant:** High-confidence Enneagram results must NEVER be altered by cross-lens weighting.

**Enforcement:**
```
∀ result where confidence_tier === 'high':
  cross_lens_adjustment_applied === false
  enneagram_adjusted === null OR enneagram_adjusted === enneagram_raw
```

### A3. Probability Integrity Invariant

**Invariant:** Type probabilities must always sum to 1.0 (±0.001 tolerance).

**Enforcement:**
```
∀ type_probabilities:
  |Σ(probabilities) - 1.0| < 0.001
  ∀ p ∈ probabilities: p >= 0.001  // No type goes to zero
```

---

## Section B: Cross-Lens Guardrail Invariants

### B1. Eligibility Gate Invariant (CRITICAL)

**Invariant:** Cross-lens adjustments may ONLY apply when ALL conditions are met:

```
adjustment_allowed ⟺ (
  confidence_tier ∈ { 'low', 'moderate' } AND
  top_2_gap <= 0.12 AND
  (assessment_depth === 'deep' OR longitudinal_signals === true) AND
  cross_lens_data_exists === true
)
```

### B2. Adjustment Bound Invariants (CRITICAL)

**Invariant:** Adjustments must respect absolute bounds.

```
∀ type ∈ [1..9]:
  |adjustment[type]| <= 0.05  // Per-type cap

Σ(|adjustments|) / 2 <= 0.10  // Total redistribution cap
```

### B3. Raw Preservation Invariant

**Invariant:** Raw Enneagram results must ALWAYS be preserved alongside adjusted results.

```
∀ cross_lens_result:
  enneagram_raw !== null AND enneagram_raw !== undefined
  IF adjustment_applied THEN enneagram_adjusted !== null
```

### B4. Transparency Invariant

**Invariant:** When adjustment is applied, rationale must be provided.

```
∀ result where adjustment_applied === true:
  adjustment_rationale.length > 0
  adjustment_sources.length > 0
```

---

## Section C: Narrative Language Safety Invariants

### C1. Banned Phrase Invariant (CRITICAL)

**Invariant:** Narrative output must NEVER contain banned phrases.

**Banned Phrase Categories:**

| Category | Examples |
|----------|----------|
| Identity-locking | "you are a", "this is your type", "your personality is" |
| Confirmatory | "this confirms", "this proves", "your astrology shows" |
| Prescriptive | "you should", "you must", "you need to", "try to" |
| Absolute | "always", "never", "permanent", "destiny" |
| Diagnostic | "diagnosis", "symptoms", "treatment" |

**Enforcement:**
```
∀ narrative_text:
  ∀ phrase ∈ BANNED_PHRASES:
    phrase ∉ narrative_text.toLowerCase()
```

### C2. Uncertainty Visibility Invariant

**Invariant:** Uncertainty must be surfaced when confidence is not high.

```
∀ narrative where confidence_tier ∈ { 'low', 'moderate' }:
  uncertainty_visible === true
  confidence_framing !== null AND confidence_framing.length > 0
```

### C3. Time-Bound Language Invariant

**Invariant:** Narratives must use time-bound language.

```
∀ narrative:
  contains_one_of(["right now", "at this stage", "currently", 
                   "at this point", "emerging", "forming"])
```

### C4. Agency Preservation Invariant

**Invariant:** User must be positioned as observer, not object.

```
∀ narrative:
  reflection_prompt uses "notice", "observe", "consider", "might"
  reflection_prompt does NOT use "should", "must", "need to"
```

### C5. Cross-Lens Context Invariant

**Invariant:** Cross-lens context must only appear when adjustment was applied.

```
IF adjustment_applied === false THEN cross_lens_context === null
IF adjustment_applied === true THEN cross_lens_context !== null
```

---

## Section D: Contract Enforcement

### D1. Build-Time Enforcement

The following MUST fail the build:
- Any regression test failure
- Any TypeScript type violation in contract-critical paths
- Any linting rule violation for banned phrases

### D2. Runtime Enforcement (DEBUG_MIRROR mode)

The following MUST be logged when `EXPO_PUBLIC_DEBUG_MIRROR === 'true'`:
- Narrative language violations
- Illegal cross-lens adjustment attempts
- Invalid wing state resolutions
- Probability sum deviations

### D3. Deployment Gate

No deployment may proceed if:
- Regression test suite fails
- Contract version mismatch detected
- Critical invariant violation logged in staging

---

## Section E: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-06-15 | Initial V1 contract freeze |

---

## Certification

By deploying Project Mirror V1, you certify that:

1. All invariants in this contract are satisfied
2. The regression test suite passes
3. No banned phrases appear in any narrative output
4. High-confidence results are protected from cross-lens alteration
5. Wing display never surfaces as null to users

**Contract Status: FROZEN**

Any modification to the invariants defined above requires:
1. Explicit version bump
2. Full regression test update
3. Product review and sign-off
