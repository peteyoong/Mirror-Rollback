# B3.2 — Founder / Operator Lexicon Expansion · Implementation Report
**Build marker:** intent-router-v2 / B3.2-founder-operator-lexicon
**Date:** 2026-06-12  (re-validation pass)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED

---

## 1. Goal

Improve founder / operator routing coverage so that messages anchored
in founder vocabulary (`board`, `runway`, `cap table`, `fundraise`,
`exec hire`, `firing conversation`, `head of product`, `term sheet`,
`co-founder`, `executive`, `manager`, `team`, …) route reliably to
`career` / `leadership` / `money` rather than collapsing into
`general` or being miscaptured as `relationship` when a team member
is named.

## 2. What landed in code

### 2.1 `domain_lexicons.yaml` expansion

File: `backend/services/lens_registries/domain_lexicons.yaml`

Founder / operator related entries (`grep -cE "founder|operator|ceo|cto|cfo|investor|board"`):
**18 lexicon entries** spanning:

* `career`        — `founder`, `cofounder`, `co-founder`, `executive`, `exec`,
                    `manager`, `team`, `company`, `startup`, `firm`,
                    `department`, `role`, `career`, `job`, `workplace`,
                    `deadline`, `deliverable`
* `leadership`    — `ceo`, `cto`, `coo`, `board`, `investor`,
                    `firing conversation`, `head of product`,
                    `team is stuck`, `lift them out`, `scale myself`
* `money`         — `fundraise`, `runway`, `cap table`, `salary`,
                    `wealth`, `finances`, `invest`, `debt`, `budget`,
                    `income`

Entries are weighted to win against:
* `relationship` lane when a teammate is *named* but the verb-frame is
  operational (`how does Sarah show up at work?` → `career`, not
  `relationship`).
* `general` lane when the founder context is implicit but the lens
  vocabulary is sparse (`board meeting tomorrow` → `leadership`).

### 2.2 Contextual-cue regex in `intent_router_v2.py`

The educational-mode override (B3.1) now treats founder vocabulary as
a *contextual cue* so that bare lens-term queries inside a founder
workflow do NOT incorrectly flip to `identity`:

```python
_EDU_CONTEXTUAL_CUE_RE = re.compile(
    r"\b("
    # … relational cues …
    # career / leadership
    r"founder|cofounder|co-founder|ceo|cto|coo|executive|exec|"
    r"manager|management|board|investor|"
    r"team|company|startup|firm|department|"
    r"fundrais|runway|hiring|layoff|downsiz|fire|fired|promotion|"
    r"role|career|job|workplace|deadline|deliverable|"
    # …
)
```

### 2.3 Team-relationship anti-collapse rule (B3.2 companion)

`intent_router_v2.py:167-200` adds a penalty subtraction from
`relationship` when:

* frame is `self`,
* message contains a generic team / business-unit token, AND
* no real proper-name candidate is present.

This prevents "my team is stuck" from being routed to `relationship`
by virtue of the plural-pronoun heuristic.

## 3. Validation

**Golden set:** `tests/intent_router_v2/golden_set_founder.yaml` (15 cases).

```
golden_set_founder        n=15  top1=100.0%  top2=100.0%  routing_pass=100.0%
```

Full re-validation across all 8 suites (165 cases) shows the founder
suite at **15/15 top-1 hits** with no routing-pass warnings. See
`B3_VALIDATION_RERUN_2026_06_12.md` for the full matrix.

## 4. Files Touched (cumulative — landed in prior agent pass, re-verified now)

```
M backend/services/lens_registries/domain_lexicons.yaml
M backend/services/intent_router_v2.py   (contextual-cue regex + anti-collapse)
A backend/tools/founder_operator_suite.py (offline reproduction harness)
```

## 5. Caveats / Known Limits

* The expansion is **lexicon-based**, not embedding-based. Queries that
  use unusual founder vernacular (e.g. `our LTV/CAC is broken`) without
  any covered noun will still fall back to `general`. These are
  candidates for the B4 embeddings tier.
* `founder` vs `co-founder` queries that *also* contain a partner's
  name still resolve through the relationship / role-bonus pathway —
  intentionally, so co-founder dynamics route through the relational
  lane.
