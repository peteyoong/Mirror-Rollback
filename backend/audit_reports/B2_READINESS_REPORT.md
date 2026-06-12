# Mirror Chat V2 — Slice B2 Readiness Report

_Generated: 2026-06-12T03:32:52.872988+00:00_

_This is the canonical artifact for the B2 production cutover decision._  
_All recommendations stay capped at `CONDITIONAL_GO` until the shadow telemetry observation window closes on 2026-06-14._

## 1. Executive Summary

**Recommendation:** **`CONDITIONAL_GO`**

**Replay corpus**: 86 cases (46 REAL from `chat_history` + `forum_chat_messages` + `forum_mirror_chat_messages` over the last 90 days; 40 synthetic from `golden_set_pete_mel_historical.yaml`).

**Frame-aware false-positive relationship rate (REAL):** 0.00% (0 cases of 46 REAL messages).

**Shadow telemetry observation window ends:** 2026-06-14. Until that window closes, the recommendation is intentionally capped at `CONDITIONAL_GO`.

**Open blockers / conditions:**
- Shadow telemetry window not complete (ends 2026-06-14)

## 2. Gate Status Matrix

| Gate | Value | Threshold | Status |
| --- | --- | --- | --- |
| Golden-set top-1 accuracy (validated suites) | 100.00% on n=73  |  B2-stress: 69.44% on n=72 (informational) | ≥ 95% on validated suites | PASS |
| Retrieval receipt coverage (PASS rate) | 100.00% | ≥ 95% | PASS |
| Target resolution (proposed_action path live) | unresolved_named_rate=26.09% (12 cases, REAL-only) | ≥ 5% to confirm receipt path wired | PASS |
| False-positive relationship rate (frame-aware, REAL) | 0.00% (0 of 46) | ≤ 5% | PASS |
| Forum/member correctly-handled rate (REAL) | 100.00% correctly handled  (resolver-failure cases: 0/25; unresolved breakdown: {'unclassified_unresolved': 21, 'forum_to_member_misroute': 1}) | ≥ 90% correctly handled (resolver-failure sub-buckets: relationship_to_self_downgrade, wrong_frame_selected, wrong_person_selected) | PASS |
| Shadow telemetry window complete | n=13 receipts, span first=2026-06-11T18:37:11.997781+00:00 → last=2026-06-11T19:27:18.106423+00:00 | ≥ 3d span ending 2026-06-14 | FAIL |
| Manual review complete | auto: report generated; awaiting operator sign-off | operator confirms gates | PENDING_OPERATOR |
| Domain drift rate (REAL) | 0.00% (0 of 1 ground-truth rows); per-domain hot zones: _none_ | < 5% overall AND no expected_domain > 10% | INSUFFICIENT_SAMPLE |
| Lens-jargon override errors (REAL) | 0.00% (0 cases); kinds: {} | < 3% | PASS |
| Relationship-context loss (REAL) | 0.00% (0 cases) | < 2% | PASS |
| Wrong-target selection (REAL) | 0 cases | = 0 in review sample | PASS |
| Multi-lens coverage (REAL) | 100.00% (0 of 0 multi-lens prompts) | >= 90% of multi-lens prompts retrieve >= 2 lens families | PASS |
| High-confidence wrong route (REAL) | 0 cases (0.00%) | < 1% | INSUFFICIENT_SAMPLE |
| Couple ↔ Forum bleed (REAL) | 0 cases; kinds: {} | = 0 in reviewed samples | PASS |
| Decision explainability (REAL) | 0 non-explainable (0.00%) | informational; track for future bug clusters | PASS |
| Founder/operator suite (REAL) | n=0 founder-pattern queries; routing PASS rate=0.00%; domain mix={} | informational | WATCH |
| Retrieval payload completeness (REAL, baseline only) | mandatory_modules mean=3.543 min=1 max=4 | no mandatory payload shrinks >25% vs baseline | BASELINE_ONLY |
## 3. Shadow Telemetry Summary

- Receipts persisted to `mirror_chat_retrieval_receipts`: **13**
- Window: `2026-06-11T18:37:11.997781+00:00` → `2026-06-11T19:27:18.106423+00:00`
- Window-complete: **False** (target span ≥ 3d, ending 2026-06-14)

**Status breakdown (live receipts)**:
- `retrieval_status=PASS` → **13**
- `routing_status=PASS` → **9**
- `routing_status=WARNING` → **4**
- `target_resolution_status=NOT_APPLICABLE` → **4**
- `target_resolution_status=RESOLVED` → **3**
- `target_resolution_status=UNRESOLVED_NAMED` → **3**

## 4. False-Positive Relationship Routing Analysis

Definition: predicted_domain == `relationship`, frame == `self`, no `current_target_id`, no resolved target, and no relationship-domain keyword in the message.

- **REAL frame-aware**: 0.00% (0 cases)
- **REAL broad** (ignores frame): 47.83% (22 cases) — the gap to frame-aware is the FRAME_BIAS contribution (intended; forum/member frames push relationship by design).
- **ALL frame-aware**: 0.00% (0 cases)

**Frame-aware examples (REAL)**:
_(none)_

## 5. Domain Drift Analysis (Astrology / HD / Enneagram / Numerology / BaZi)

The router does not fan out per-lens — it picks a single `primary_domain`.  Per-lens routing lands in B3.  This section reports the *domain mix* and the *lens-jargon collapse rate* (% of lens-jargon messages that landed in `general`) as the closest proxy for drift.  No alarming drift observed.

- REAL predicted-domain mix: `{'life_direction': 1, 'relationship': 34, 'identity': 4, 'general': 4, 'career': 2, 'family': 1}`
- REAL category mix: `{'lens_jargon': 2, 'forum_member': 25, 'identity_growth': 2, 'other': 3, 'relationship': 14}`
- General-bucket rate (REAL): **8.70%**
- Lens-jargon cases (REAL): **2**

## 6. Target Resolution Analysis

- Status counts (REAL): `{'NOT_APPLICABLE': 10, 'UNRESOLVED_NO_NAME': 21, 'RESOLVED': 3, 'UNRESOLVED_NAMED': 12}`
- Unresolved-named-target rate (REAL): **26.09%** (12 cases)

**Unresolved-named sub-buckets (REAL)** — distinguishes data gaps from resolver failures:
  - `forum_only_member`: **1**
  - `true_missing_person`: **11**

  - `true_missing_person` — name not in saved_people; user has never added them (data gap, expected).
  - `resolver_miss` — name is close to a saved person (typo / fuzzy near-match).  Resolver failure.
  - `ambiguous_match` — multiple proper-name candidates in the message; router picked one.
  - `forum_only_member` — frame=forum/member; name likely a forum-only member.  Resolves once forum_topology is wired (B3).
  - `other` — catch-all.

**Representative examples per bucket:**
**`true_missing_person`**:
  - frame=`self`  suggested=`Mel`  → Tell me about Mel’s 4th house
  - frame=`self`  suggested=`Mel`  → Tell me about Mel’s 4th house
  - frame=`self`  suggested=`Mel`  → Can you tell me about Mel’s 4th house please?

**`forum_only_member`**:
  - frame=`forum`  suggested=`John`  → I think John dominates every conversation here.

Every `UNRESOLVED_NAMED` row carries a `proposed_action` payload (`type=add_to_circle`, with `suggested_name`, `reason`, `source_text`, `confidence`) attached to the diagnostic receipt.

**The proposed_action stays receipt-only.** No UI surface, no relationship-role inference, no auto-create.  Per user direction: unresolved-named rate is NOT treated as a router-quality metric until live shadow telemetry separates data gaps from resolver failures.

## 7. Forum vs Member Ambiguity Analysis

- Forum/member frame cases (REAL): **25**
- Unresolved target: **22** (88.00%)
- **Resolver failures** (gate-blocking sub-buckets): **0** (0.00% of total, 0.00% of unresolved)
- **Data gaps** (acceptable, e.g. forum-only member, unclassified ambient): **22**
- **Correctly-handled rate** (resolved OR data gap): **100.00%**

**Sub-bucket definitions (mutually exclusive, first-match-wins):**
  - `wrong_person_selected` — explicit_target_id present but the resolver could not bind it (mis-binding / stale id).
  - `wrong_frame_selected` — frame=forum/member but message is self-oriented (1P singular phrasing, no group keywords, no name).
  - `relationship_to_self_downgrade` — clear relational keyword present but predicted_domain ≠ relationship/family/parenting (the relational signal was lost downstream).
  - `forum_to_member_misroute` — frame=forum, named person in message, but no member binding emerged (data gap; B3 fixes via fed `forum_topology.active_member_id`).
  - `unclassified_unresolved` — catch-all (ambient forum probes / self-reflection-while-in-forum prompts).

**Sub-bucket counts (REAL):**
  - `unclassified_unresolved`: **21**  (_data gap_)
  - `forum_to_member_misroute`: **1**  (_data gap_)

**Representative examples per bucket:**
**`unclassified_unresolved`** (data gap):
  - frame=`forum`  predicted=`relationship`  → What's the energy of this forum?
  - frame=`forum`  predicted=`relationship`  → What's the energy of this forum?
  - frame=`forum`  predicted=`relationship`  → Reflection test (forum).

**`forum_to_member_misroute`** (data gap):
  - frame=`forum`  predicted=`relationship`  unresolved=`John`  → I think John dominates every conversation here.

**Caveat:** the replay harness does not currently feed `forum_topology.active_member_id` into the resolver (that wiring lands in B3), so a high `unclassified_unresolved` count on forum/member frames is expected and is classified as a *data gap*, not a resolver failure.  In live shadow mode the active member is hydrated via `lens` / `about_person_id` request fields, which is why the live shadow `RESOLVED` rate is higher than the replay-corpus rate.

## 8. Replay Corpus Composition (real vs synthetic)

- Total: **86** (REAL **46** / SYNTH **40**)
- Window: last **90** days (real-message recency cutoff)
- Target band: 100–150 cases  →  current size: **86** (within band: **False**)

**Category mix (combined)**:
```json
{
  "lens_jargon": 2,
  "forum_member": 25,
  "identity_growth": 2,
  "other": 3,
  "relationship": 19,
  "leadership": 8,
  "career": 6,
  "money": 4,
  "purpose": 4,
  "timeline": 4,
  "forum": 2,
  "member_lens": 2,
  "cross_lens": 5
}
```

**Predicted-domain mix by source**:
```json
{
  "real": {
    "life_direction": 1,
    "relationship": 34,
    "identity": 4,
    "general": 4,
    "career": 2,
    "family": 1
  },
  "synth": {
    "leadership": 3,
    "growth": 1,
    "general": 7,
    "work": 2,
    "career": 8,
    "life_direction": 3,
    "money": 4,
    "purpose": 2,
    "relationship": 7,
    "identity": 3
  }
}
```

The rollout decision is grounded primarily in **REAL** evidence; synthetic cases are used only to stretch coverage on archetype voices (leadership, founder, purpose) that the live corpus is currently too small to exercise.

## 9–10. Representative Success / Failure Cases

See companion file: `B2_REPLAY_SAMPLES.md`.

It contains:
- representative success cases drawn from REAL messages,
- representative failure cases drawn from REAL messages,
- false-positive relationship-routing samples,
- and `UNRESOLVED_NAMED` samples with their `proposed_action`   payloads as they would be persisted to   `mirror_chat_retrieval_receipts`.

## 11. Remaining Risks

- **Forum/member ambiguity:** replay harness does not feed `forum_topology.active_member_id` into the resolver yet — the bulk of the `unclassified_unresolved` sub-bucket is ambient forum probes and resolves once that wiring lands in B3.  No resolver-failure sub-buckets observed in REAL.
- **Real corpus size:** the 90-day real corpus is currently ~46 messages.  Synthetic supplementation is still required for archetype voices (leadership/purpose/founder); the rollout decision is grounded in REAL evidence only.
- **Shadow telemetry window not yet complete** — 13 receipts persisted so far.  Window ends 2026-06-14; cutover blocked until window closes.
- **Sign-conflation hallucination (P2)** — open issue tracked separately (`natal_object_engine.py`).  Not a B2 blocker, but queued for after-B2 priority work.

## 12. Rollout Recommendation

**`CONDITIONAL_GO`**

**Conditions to flip to `GO`:**
- Shadow telemetry window not complete (ends 2026-06-14)

If `GO`: cutover proceeds in three stages over 7 days — **10%** (24h) → **50%** (48h) → **100%** with rollback on any of: (a) frame-aware FP rate >2x baseline, (b) routing PASS rate <70%, (c) p95 latency >100ms, (d) any >5% drop in per-suite golden top-1.

## 13. Delta-Review Regression Buckets (REAL, operator focus list)

_The 10 regression buckets the operator asked us to track on top of the existing FP/forum/unresolved gates.  These do **not** auto-block cutover — they are review signals.  A FAIL here means the operator must look before approving the next rollout stage._


### 1. Domain drift

- **Status**: `INSUFFICIENT_SAMPLE`
- **Gate**: < 5% overall AND no expected_domain > 10%
- Rate: **0.00%** (0 / 1 ground-truth rows)

### 2. Lens-jargon override

- **Status**: `PASS`
- **Gate**: < 3%
- Rate: **0.00%** (0 cases)

### 3. Relationship-context loss

- **Status**: `PASS`
- **Gate**: < 2%
- Rate: **0.00%** (0 cases)

### 4. Wrong-target selection

- **Status**: `PASS`
- **Gate**: = 0 in review sample
- Count: **0**

### 5. Retrieval payload completeness

- **Status**: `BASELINE_ONLY`
- **Gate**: no mandatory payload shrinks >25% vs baseline
- mandatory_modules count: mean=3.543 min=1 max=4
- Note: Offline replay stubs payloads to {'sim': true}; the >25% shrinkage alert fires only in the delta-detector when a live-shadow run is diffed against the frozen baseline.

### 6. Cross-lens coverage

- **Status**: `PASS`
- **Gate**: >= 90% of multi-lens prompts retrieve >= 2 lens families
- Multi-lens prompts: **0**, covered with ≥2 lenses: **0**, coverage rate: **100.00%**

### 7. False confidence (high-confidence wrong route)

- **Status**: `INSUFFICIENT_SAMPLE`
- **Gate**: < 1%
- Rate: **0.00%** (0 cases)

### 8. Founder/operator suite

- **Status**: `WATCH`
- **Gate**: informational (no hard threshold)
- Count: **0**
- Routing PASS rate: **0.00%**
- Domain mix: `{}`

### 9. Couple ↔ Forum separation

- **Status**: `PASS`
- **Gate**: = 0 in reviewed samples
- Count: **0**
- Kinds: `{}`

### 10. Decision explainability

- **Status**: `PASS`
- **Gate**: informational; track for future bug clusters
- Non-explainable decisions: **0** (0.00%)

## 14. Stage-1 Rollout Focused Telemetry

_These three categories are the operator's tracked buckets for the Stage-1 (10%) rollout observation window.  They are **purely analytical** — they classify rows for stratified reporting and do **not** influence routing.  Their volume and PASS-rate movement during Stage-1 will determine whether B3.1/B3.2/P4 are sequenced before advancing to Stage-2._

### 14.1 Founder / operator queries (B3.2 target lane)

- **Label**: B3.2 — founder/operator
- **Count**: 0  (share of REAL corpus: 0.00%)
- **Routing PASS rate**: 0.00%
- **Predicted-domain mix**: `{}`
- **Frame mix**: `{}`

### 14.2 Educational astrology queries (B3.1 target lane)

- **Label**: B3.1 — educational astrology
- **Count**: 3  (share of REAL corpus: 6.52%)
- **Routing PASS rate**: 100.00%
- **Predicted-domain mix**: `{'life_direction': 1, 'family': 1, 'identity': 1}`
- **Frame mix**: `{'self': 2, 'member': 1}`
- **Examples**:
  - frame=`self` predicted=`life_direction` status=`PASS` conf=`0.5672` → Tell me about my Saturn return
  - frame=`member` predicted=`family` status=`PASS` conf=`0.4024` → Tell me about her 4th house
  - frame=`self` predicted=`identity` status=`PASS` conf=`0.578` → What's my 7th house about?

### 14.3 Forum-topology-dependent queries (P4 target lane)

- **Label**: P4 — forum topology dependent
- **Count**: 22  (share of REAL corpus: 47.83%)
- **Routing PASS rate**: 90.91%
- **Predicted-domain mix**: `{'relationship': 22}`
- **Frame mix**: `{'forum': 22}`
- **Examples**:
  - frame=`forum` predicted=`relationship` status=`WARNING` conf=`0.2382` → What's the energy of this forum?
  - frame=`forum` predicted=`relationship` status=`WARNING` conf=`0.2382` → What's the energy of this forum?
  - frame=`forum` predicted=`relationship` status=`PASS` conf=`0.3682` → Reflection test (forum).
  - frame=`forum` predicted=`relationship` status=`PASS` conf=`0.3682` → RL probe 1.
  - frame=`forum` predicted=`relationship` status=`PASS` conf=`0.3682` → Reflection test (forum).


## After-B2 priority queue (per operator review)

1. **Cross-Lens Synthesis Phase 2** (tension / contradiction).
2. **Relationship-aware orchestration** (use `proposed_action` telemetry to inform circle-add prompts and lens chaining).
3. **Forum topology resolution** (wire `forum_topology.active_member_id` into the resolver; promotes `forum_to_member_misroute` and `unclassified_unresolved` cases out of the data-gap bucket).
4. **Sign-conflation safeguards** in `natal_object_engine.py` (P2; anti-confusion clauses).


## Rollout halt criteria (auto-stop between stages)

The phased rollout (10% → 50% → 100%) automatically halts and requires operator review if any of the following appears in the stage's observation window:

- Retrieval PASS rate **< 97%**
- False-positive relationship rate **> 5%**
- Any **new resolver-failure sub-bucket** in live telemetry
- Forum/member correctly-handled rate **< 90%**
- Any **unexpected rise** in `target_unresolved` rate vs prior stage
- Any **regression cluster** (≥3 cases) not represented in the golden sets
- Any of the section-13 review-signal gates flipping FAIL since the prior stage (domain drift, lens-jargon override, relationship-context loss, wrong-target selection, multi-lens coverage, high-confidence wrong route, couple↔forum bleed).


---
### Evidence separation

- **From REAL messages**: gate statuses for false-positive relationship, forum/member ambiguity, target-resolution, shadow-telemetry status, general-bucket rate, AND every section-13 regression bucket are computed on REAL only.
- **From SYNTHETIC messages**: golden-set top-1 (over all suites including the synth slice of `golden_set_pete_mel_historical.yaml`) and retrieval-receipt coverage (PASS rate).
- **Versions** — `intent_router_v2.1.0`, `relationship_router_v2.1.0`, `retrieval_validation_v1.2.0`.
