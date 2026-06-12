# B3.1-v2 · Lens-Term Compound Handling (Iteration 2)
**Build marker:** intent-router-v2 / B3.1-lens-term-v2
**Date:** 2026-06-12 (Stage 1 · 10% live)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED · ✅ NO REGRESSIONS

---

## 1. Goal

Expand the educational-mode regex and lexicon coverage for lens terms
so bare educational queries route to `identity` while contextually-cued
queries still pick up their natural domain.

Target terms (per spec):

* Saturn Return     — already covered (B3.1-v1)
* 7th House         — already covered
* North Node        — added to identity lexicon (was relationship-only)
* **Chiron Return** — NEW — moved from `growth` to `identity`
* **Vertex / Anti-vertex / Lilith** — NEW — added to regex + identity lexicon
* **Synastry / Composite chart** — NEW — added to regex + identity lexicon
* **Progressed moon / Solar return / Lunar return** — NEW — educational-mode aware

## 2. What landed (delta from B3.1-v1)

### 2.1 Expanded `_EDU_LENS_TERM_RE` regex

File: `backend/services/intent_router_v2.py:107-124`

Added tokens:

```
lilith | vertex | anti[-\s]?vertex | mc\b |
chiron\s+return | saturn\s+return | jupiter\s+return |
nodal\s+return | north\s+node\s+return |
solar\s+return | lunar\s+return | progressed | progression |
synastry | composite\s+chart | composite
```

### 2.2 New `identity`-lexicon entries (B3.1-v2 block)

```yaml
- {p: "chiron return",     w: 0.6}
- {p: "my chiron return",  w: 0.75}
- {p: "progressed moon",   w: 0.6}
- {p: "my progressed moon", w: 0.75}
- {p: "solar return chart", w: 0.7}
- {p: "solar return",      w: 0.45}
- {p: "lunar return chart", w: 0.7}
- {p: "vertex",            w: 0.55}
- {p: "anti-vertex",       w: 0.65}
- {p: "my vertex",         w: 0.7}
- {p: "lilith",            w: 0.55}
- {p: "lilith placement",  w: 0.7}
- {p: "lilith placements", w: 0.7}
- {p: "composite chart",   w: 0.5}
- {p: "synastry chart",    w: 0.6}
```

### 2.3 `growth`-lexicon weight reductions

* `solar return`  : 0.55 → 0.30
* `lunar return`  : 0.55 → 0.30
* `chiron return` / `progressed moon` : removed (migrated to `identity`)

Rationale: the previous weights triggered
`EDUCATIONAL_MODE_COMPOUND_SUPPRESS_FLOOR=0.85` on bare queries,
forcing them to `growth` instead of `identity`. Lower weights let
the educational override fire while contextual cues (e.g. "I'm in my
chiron return right now") still steer to growth via the
contextual-cue regex.

## 3. Validation

### 3.1 New golden set: `golden_set_educational_astrology_v2.yaml` (10 cases)

EA11-EA20: chiron return, vertex, anti-vertex, north node, synastry,
solar return chart, progressed moon, IC, Lilith placements, composite
chart.

```
golden_set_educational_astrology_v2   n=10  top1=100.0%  top2=100.0%  routing_pass=100.0%
```

Before this iteration: **70.0% top-1** (3 misses — chiron return,
solar return chart, progressed moon all collapsed to `growth`).
After: **100.0% top-1**.

### 3.2 Baseline regression check

```
golden_set                          100.0%  (was 100.0%)  — NO regression
golden_set_lens_jargon              100.0%  (was 100.0%)  — NO regression
golden_set_educational_astrology    100.0%  (was 100.0%)  — NO regression
```

### 3.3 Verified compound-lane behaviour preserved

* `Tell me about my Saturn return` → `life_direction` ✓
  (compound-lane override fires at >=0.85)
* `Tell me about my Chiron return` → `identity` ✓
  (educational mode fires; no compound-lane signal above floor)

## 4. Files Touched

```
M backend/services/intent_router_v2.py                  (+8 lines, _EDU_LENS_TERM_RE)
M backend/services/lens_registries/domain_lexicons.yaml (+18 identity, -4 growth)
A backend/tests/intent_router_v2/golden_set_educational_astrology_v2.yaml  (10 cases)
```
