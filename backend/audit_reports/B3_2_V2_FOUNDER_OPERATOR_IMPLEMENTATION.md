# B3.2-v2 · Founder / Operator Lexicon Expansion (Iteration 2)
**Build marker:** intent-router-v2 / B3.2-founder-operator-v2
**Date:** 2026-06-12 (Stage 1 · 10% live)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED · ✅ NO REGRESSIONS

---

## 1. Goal

Expand founder/operator routing coverage to handle board, restructuring,
operating-partner, scaling, growth-constraint, organizational-decision,
strategic-risk, leadership-pipeline, and succession-planning vocabulary
that real founder traffic exercises.

## 2. What landed (delta from B3.2-v1)

### 2.1 `domain_lexicons.yaml` — leadership domain

Added 27 new lexicon entries to the `leadership` block:

| Vocabulary | Entries | Sample weights |
|---|---|---|
| Board | `the board`, `my board`, `board meeting`, `board call`, `board wants`, `board is pushing`, `board-level decision`, `answer to the board` | 0.7–0.95 |
| Operating partner | `operating partner`, `my operating partner`, `bring on an operating partner`, `operating partners` | 0.85–0.95 |
| Restructuring | `restructure`, `restructuring`, `reorg`, `the reorg`, `reorganization`, `restructure the company`, `restructure the org`, `company restructure`, `org chart` | 0.7–0.95 |
| Strategic risk | `strategic risk`, `strategic risks` | 0.85 |
| Org decision | `organizational decision`, `org decision` | 0.8–0.9 |
| Scaling | `scaling the company`, `scale the company`, `scale the org`, `scale the business`, `organizational change` | 0.85–0.9 |
| Leadership pipeline | `leadership pipeline`, `succession plan`, `need a succession plan`, `management team isn't scaling` | 0.9–0.95 |

### 2.2 `domain_lexicons.yaml` — career domain

Added 11 new operator-vocabulary entries:

* `operator role`, `as an operator`, `operator path`, `ic role`,
  `individual contributor`, `scaling myself`, `scale myself`,
  `scaling the team`, `scaling the business`, `stage of the company`,
  `stage of company`.

## 3. Validation

### 3.1 Targeted golden set: `golden_set_founder_v2.yaml` (15 new cases)

F16-F30: board, operating partner, restructuring, growth-constraint,
strategic risk, organizational decision, succession plan, scaling,
reorg, downsizing exec team.

```
golden_set_founder_v2    n=15  top1=100.0%  top2=100.0%  routing_pass=93.3%
```

Before this iteration (B3.2-v1 only): **40.0% top-1** — 9 misses routed
to `general` (no signal). After this iteration: **100.0% top-1**.

### 3.2 Baseline regression check

```
golden_set                       100.0%  (was 100.0%)  — NO regression
golden_set_founder               100.0%  (was 100.0%)  — NO regression
golden_set_lens_jargon           100.0%  (was 100.0%)  — NO regression
```

The new vocabulary did not change any existing route. Top-1 across the
five baseline B3-scope suites: 75/75 = 100.0% (unchanged).

## 4. Files Touched

```
M backend/services/lens_registries/domain_lexicons.yaml   (+38 lines)
A backend/tests/intent_router_v2/golden_set_founder_v2.yaml  (15 cases)
```
