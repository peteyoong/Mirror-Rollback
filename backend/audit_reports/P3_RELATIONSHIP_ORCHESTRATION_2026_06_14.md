# P3 · Relationship-Aware Orchestration · Implementation & Validation
**Build marker:** `relationship_orchestration_v1.0.0`
**Date:** 2026-06-14
**Stage:** Stage 1 · 10% live (no rollout flag changes)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED · ✅ TELEMETRY EMITTING · ✅ NO REGRESSIONS

---

## 0. Constraints honoured

* `INTENT_ROUTER_V2_CUTOVER` remains `false` (verified).
* `INTENT_ROUTER_V2_ROLLOUT_PERCENT` remains `10` (verified).
* No timezone migration logic touched.
* No Variant A migrations triggered.
* Strictly **shadow-only / receipt-only**: the plan is recorded but the
  live response continues to read `lens_priority` straight off the
  intent envelope. Stage 1 telemetry collection continues uninterrupted.

---

## 1. Goal

Use `relationship_role`, `target_resolved`, `active_member_id`,
`forum_topology`, and `context_mode` to influence lens prioritization
and surface a framing hint — without changing the live response path
during Stage 1 rollout.

---

## 2. What landed

### 2.1 New service: `services/relationship_orchestration_v1.py`

Pure function `plan_lens_priority(...)` returning a `LensPriorityPlan`
receipt block. Strictly additive. Never raises.

**Rule resolution ladder (first match wins):**

| Order | Bucket | Trigger |
|---|---|---|
| 1 | `spouse` | `relationship_role ∈ {spouse, partner, wife, husband, girlfriend, boyfriend, fiance(e)}` |
| 2 | `child` | `relationship_role ∈ {child, son, daughter, kid, teen, baby, toddler}` |
| 3 | `cofounder` | `relationship_role ∈ {cofounder, co-founder, business_partner, biz_partner}` |
| 3b | `cofounder` (via colleague) | `relationship_role ∈ {colleague, coworker, teammate, boss, manager, report}` AND `primary_domain ∈ {leadership, career}` |
| 4 | `forum_member` | `forum_topology.active_member_id` present (no role-noun match above) |
| 5 | `self` | default |

**Lens modulation maps (additive deltas):**

```
spouse:       astrology +0.30, relationship +0.40, human_design +0.20, timeline +0.10
child:        astrology +0.20, human_design +0.30, enneagram +0.15, timeline +0.20, relationship +0.10
cofounder:    human_design +0.30, astrology +0.15, enneagram +0.25, relationship +0.20, timeline +0.10
forum_member: relationship +0.40, astrology +0.20, human_design +0.20, enneagram +0.10
self:         (no modulation — passthrough)
```

Re-ranking is performed by combining a linear rank weight (1.0 at idx
0, falling to 0.1 at the tail) + the modulation delta, then sorting
descending. This preserves the relative preference encoded in the
intent envelope while letting strong modulations bubble a lens up
without ever zeroing out a lens.

**Framing hints:**

| Bucket | Hint |
|---|---|
| spouse | `spouse_focus` |
| child | `child_developmental` |
| cofounder | `cofounder_strategic` |
| forum_member | `forum_member_dynamic` |
| self | `self_inquiry` |

**Context-mode promotion:**

When `context_mode ∈ {forum, forum_chat}` AND the resolved bucket is
`self` (no role / no topology), the bucket is promoted to
`forum_member` with applied-rule trace
`forum_promotion:self_to_forum_member`.

### 2.2 Shadow-receipt wiring (`services/mirror_chat_shadow.py`)

* New import: `from services.relationship_orchestration_v1 import plan_lens_priority`.
* New block emitted after the cross-lens-synthesis hook:

```python
receipt["relationship_orchestration_v1"] = plan_lens_priority(
    intent_envelope=envd,
    relationship_role=resolved_role,
    target_resolved=resolved_target_id,
    forum_topology=forum_topology,
    context_mode=lens or life_domain,
)
```

Wrapped in try/except so a routing bug can never break production.

### 2.3 Telemetry shape (live, on every receipt)

```json
"relationship_orchestration_v1": {
  "version":                "relationship_orchestration_v1.0.0",
  "computed":               true,
  "role_resolved":          "spouse" | "child" | ... | null,
  "rule_bucket":            "spouse" | "child" | "cofounder" | "forum_member" | "self",
  "applied_rules":          ["role_match:spouse:spouse", "target_bound", "context_mode:reflection"],
  "lens_priority_before":   ["relationship", "astrology", "human_design", ...],
  "lens_priority_after":    ["relationship", "astrology", "human_design", ...],
  "lens_weight_modulation": {"astrology": 0.30, "relationship": 0.40, "human_design": 0.20, "timeline": 0.10},
  "framing_hint":           "spouse_focus",
  "context_mode":           "reflection_chat" | null,
  "target_resolved":        "mel-001" | null,
  "active_member_id":       "patricia-001" | null,
  "reordered":              true | false,
  "lens_outputs_preserved": true
}
```

Confirmed live on `mirror_chat_retrieval_receipts` collection after
`POST /api/mirror/chat`.

---

## 3. Validation

### 3.1 Golden set: `golden_set_relationship_orchestration.yaml` (15 cases)

| Bucket | n | Pass |
|---|---:|---:|
| spouse        | 3 | 3/3 (100.0%) |
| child         | 3 | 3/3 (100.0%) |
| cofounder     | 3 | 3/3 (100.0%) |
| forum_member  | 3 | 3/3 (100.0%) |
| self          | 3 | 3/3 (100.0%) |
| **TOTAL**     | **15** | **15/15 (100.0%)** |

Each case asserts `rule_bucket`, `framing_hint`, expected top-lens (where
applicable), and required substrings in `applied_rules`.

### 3.2 Unit tests: `tests/test_relationship_orchestration_v1.py`

```
28 tests PASSED — covering:
  * version pin
  * lens_outputs_preserved invariant
  * empty/malformed input safety
  * role-bucket parametrized matrices (spouse 6, child 5, cofounder 3)
  * colleague + leadership intent → cofounder
  * colleague + non-leadership intent → self
  * forum-member binding with members[] list
  * self-bucket passthrough (no reordering)
  * spouse promotes relationship lens
  * child promotes human_design
  * cofounder promotes human_design + enneagram
  * context_mode forum-promotes self → forum_member
  * context_mode recorded in applied_rules
  * modulation map values match spec
```

### 3.3 Regression — full intent-router golden suite (139 cases)

| Suite | n | top-1 | top-2 | routing_pass |
|---|---:|---:|---:|---:|
| `golden_set` (baseline)              | 15 | 100.0% | 100.0% | 100.0% |
| `golden_set_founder`                 | 15 | 100.0% | 100.0% | 100.0% |
| `golden_set_founder_v2`              | 15 | 100.0% | 100.0% | 100.0% |
| `golden_set_founder_v3`              | 15 |  93.3% | 100.0% | 100.0% |
| `golden_set_lens_jargon`             | 25 | 100.0% | 100.0% | 100.0% |
| `golden_set_educational_astrology`   | 10 | 100.0% | 100.0% | 100.0% |
| `golden_set_educational_astrology_v2`| 10 | 100.0% | 100.0% | 100.0% |
| `golden_set_educational_astrology_v3`| 10 |  90.0% | 100.0% | 100.0% |
| `golden_set_forum_topology`          | 10 | 100.0% | 100.0% | 100.0% |
| `golden_set_forum_topology_v2`       |  6 | 100.0% | 100.0% | 100.0% |
| `golden_set_forum_topology_v3`       |  8 |  87.5% | 100.0% | 100.0% |
| **TOTAL**                            |**139**|**97.8%**|**100.0%**|**100.0%**|

**Unchanged from iteration 3.** P3 is additive only — it does not feed
back into `classify_intent_v2`.

### 3.4 Combined unit-test sweep

```
tests/test_relationship_orchestration_v1.py  28 passed
tests/test_intent_router_v2.py                8 passed
tests/test_cross_lens_synthesis_v2.py         7 passed
─────────────────────────────────────────────────────
                                             43 passed in 0.14s
```

### 3.5 Live persistence check

Made `POST /api/mirror/chat` → HTTP 200. The fresh
`mirror_chat_retrieval_receipts` document contained:

```json
"relationship_orchestration_v1": {
  "rule_bucket":   "self",
  "framing_hint":  "self_inquiry",
  "applied_rules": ["self:default"],
  "reordered":     false,
  "lens_priority_before": ["relationship","astrology","human_design","enneagram","timeline","numerology"],
  "lens_priority_after":  ["relationship","astrology","human_design","enneagram","timeline","numerology"]
}
```

(`self` bucket because the smoke-test request did not carry a
`relationship_role` or `forum_topology`. Stage-1 traffic on real
requests will populate spouse / forum_member buckets as expected.)

---

## 4. Files touched

```
A backend/services/relationship_orchestration_v1.py             (236 lines)
A backend/tests/test_relationship_orchestration_v1.py           (199 lines)
A backend/tests/intent_router_v2/golden_set_relationship_orchestration.yaml (138 lines)
A backend/tools/run_p3_validation.py                            (102 lines)
M backend/services/mirror_chat_shadow.py
    + new import (relationship_orchestration_v1.plan_lens_priority)
    + 22 lines: receipt-block emission with try/except guard
```

No changes to:
* `backend/services/intent_router_v2.py`
* `backend/services/cross_lens_synthesis_v2.py`
* `backend/services/lens_registries/domain_lexicons.yaml`
* any `.env`

---

## 5. Stage 1 rollout status (unchanged)

```
INTENT_ROUTER_V2_SHADOW          = true
INTENT_ROUTER_V2_CUTOVER         = false   ← unchanged (per constraint)
INTENT_ROUTER_V2_ROLLOUT_PERCENT = 10      ← unchanged (per constraint)
```

Shadow-mode receipts now carry the `relationship_orchestration_v1`
block on every request. Dashboards can split by `rule_bucket`,
`framing_hint`, and `reordered` to monitor:
* Bucket distribution across live traffic.
* How often the orchestration actually re-ranks the lens stack.
* Which `applied_rules` are firing most.

---

## 6. Next-step recommendation (deferred until you authorise)

* Surface `lens_priority_after` and `framing_hint` to the live response
  (Phase 4 — exits shadow-only mode for orchestration; requires
  explicit authorisation).
* Real-traffic re-tuning of modulation deltas once 10% bucket has
  logged several hundred non-`self` plans.
* P5 — Timeline V2 Soft Modulation observation window.
* P6 — Variant A migration (still on hold per session constraints).
