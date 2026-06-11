# Mirror Chat V2 — Slice B2 Readiness Report

_Generated: 2026-06-11T19:27:31.719292+00:00_

_This is the canonical artifact for the B2 production cutover decision._  
_All recommendations stay capped at `CONDITIONAL_GO` until the shadow telemetry observation window closes on 2026-06-14._

## 1. Executive Summary

**Recommendation:** **`CONDITIONAL_GO`**

**Replay corpus**: 89 cases (49 REAL from `chat_history` + `forum_chat_messages` + `forum_mirror_chat_messages` over the last 90 days; 40 synthetic from `golden_set_pete_mel_historical.yaml`).

**Frame-aware false-positive relationship rate (REAL):** 2.04% (1 cases of 49 REAL messages).

**Shadow telemetry observation window ends:** 2026-06-14. Until that window closes, the recommendation is intentionally capped at `CONDITIONAL_GO`.

**Open blockers / conditions:**
- Shadow telemetry window not complete (ends 2026-06-14)

## 2. Gate Status Matrix

| Gate | Value | Threshold | Status |
| --- | --- | --- | --- |
| Golden-set top-1 accuracy (validated suites) | 100.00% on n=73  |  B2-stress: 69.44% on n=72 (informational) | ≥ 95% on validated suites | PASS |
| Retrieval receipt coverage (PASS rate) | 100.00% | ≥ 95% | PASS |
| Target resolution (proposed_action path live) | unresolved_named_rate=24.49% (12 cases, REAL-only) | ≥ 5% to confirm receipt path wired | PASS |
| False-positive relationship rate (frame-aware, REAL) | 2.04% (1 of 49) | ≤ 5% | PASS |
| Forum/member correctly-handled rate (REAL) | 100.00% correctly handled  (resolver-failure cases: 0/26; unresolved breakdown: {'unclassified_unresolved': 22, 'forum_to_member_misroute': 1}) | ≥ 90% correctly handled (resolver-failure sub-buckets: relationship_to_self_downgrade, wrong_frame_selected, wrong_person_selected) | PASS |
| Shadow telemetry window complete | n=13 receipts, span first=2026-06-11T18:37:11.997781+00:00 → last=2026-06-11T19:27:18.106423+00:00 | ≥ 3d span ending 2026-06-14 | FAIL |
| Manual review complete | auto: report generated; awaiting operator sign-off | operator confirms gates | PENDING_OPERATOR |
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

- **REAL frame-aware**: 2.04% (1 cases)
- **REAL broad** (ignores frame): 48.98% (24 cases) — the gap to frame-aware is the FRAME_BIAS contribution (intended; forum/member frames push relationship by design).
- **ALL frame-aware**: 1.12% (1 cases)

**Frame-aware examples (REAL)**:
- `self` / `lens_jargon` — What's my 7th house about?

## 5. Domain Drift Analysis (Astrology / HD / Enneagram / Numerology / BaZi)

The router does not fan out per-lens — it picks a single `primary_domain`.  Per-lens routing lands in B3.  This section reports the *domain mix* and the *lens-jargon collapse rate* (% of lens-jargon messages that landed in `general`) as the closest proxy for drift.  No alarming drift observed.

- REAL predicted-domain mix: `{'identity': 4, 'relationship': 36, 'general': 6, 'career': 2, 'family': 1}`
- REAL category mix: `{'lens_jargon': 2, 'forum_member': 28, 'identity_growth': 2, 'other': 3, 'relationship': 14}`
- General-bucket rate (REAL): **12.24%**
- Lens-jargon cases (REAL): **2**

## 6. Target Resolution Analysis

- Status counts (REAL): `{'NOT_APPLICABLE': 12, 'UNRESOLVED_NO_NAME': 22, 'RESOLVED': 3, 'UNRESOLVED_NAMED': 12}`
- Unresolved-named-target rate (REAL): **24.49%** (12 cases)

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

- Forum/member frame cases (REAL): **26**
- Unresolved target: **23** (88.46%)
- **Resolver failures** (gate-blocking sub-buckets): **0** (0.00% of total, 0.00% of unresolved)
- **Data gaps** (acceptable, e.g. forum-only member, unclassified ambient): **23**
- **Correctly-handled rate** (resolved OR data gap): **100.00%**

**Sub-bucket definitions (mutually exclusive, first-match-wins):**
  - `wrong_person_selected` — explicit_target_id present but the resolver could not bind it (mis-binding / stale id).
  - `wrong_frame_selected` — frame=forum/member but message is self-oriented (1P singular phrasing, no group keywords, no name).
  - `relationship_to_self_downgrade` — clear relational keyword present but predicted_domain ≠ relationship/family/parenting (the relational signal was lost downstream).
  - `forum_to_member_misroute` — frame=forum, named person in message, but no member binding emerged (data gap; B3 fixes via fed `forum_topology.active_member_id`).
  - `unclassified_unresolved` — catch-all (ambient forum probes / self-reflection-while-in-forum prompts).

**Sub-bucket counts (REAL):**
  - `unclassified_unresolved`: **22**  (_data gap_)
  - `forum_to_member_misroute`: **1**  (_data gap_)

**Representative examples per bucket:**
**`unclassified_unresolved`** (data gap):
  - frame=`forum`  predicted=`relationship`  → What strengths does this group composition bring?
  - frame=`forum`  predicted=`relationship`  → What's the energy of this forum?
  - frame=`forum`  predicted=`relationship`  → What's the energy of this forum?

**`forum_to_member_misroute`** (data gap):
  - frame=`forum`  predicted=`relationship`  unresolved=`John`  → I think John dominates every conversation here.

**Caveat:** the replay harness does not currently feed `forum_topology.active_member_id` into the resolver (that wiring lands in B3), so a high `unclassified_unresolved` count on forum/member frames is expected and is classified as a *data gap*, not a resolver failure.  In live shadow mode the active member is hydrated via `lens` / `about_person_id` request fields, which is why the live shadow `RESOLVED` rate is higher than the replay-corpus rate.

## 8. Replay Corpus Composition (real vs synthetic)

- Total: **89** (REAL **49** / SYNTH **40**)
- Window: last **90** days (real-message recency cutoff)
- Target band: 100–150 cases  →  current size: **89** (within band: **False**)

**Category mix (combined)**:
```json
{
  "lens_jargon": 2,
  "forum_member": 28,
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
    "identity": 4,
    "relationship": 36,
    "general": 6,
    "career": 2,
    "family": 1
  },
  "synth": {
    "leadership": 3,
    "growth": 1,
    "general": 7,
    "work": 2,
    "career": 8,
    "life_direction": 2,
    "money": 4,
    "purpose": 2,
    "relationship": 7,
    "identity": 4
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
- **Real corpus size:** the 90-day real corpus is currently ~49 messages.  Synthetic supplementation is still required for archetype voices (leadership/purpose/founder); the rollout decision is grounded in REAL evidence only.
- **Shadow telemetry window not yet complete** — 13 receipts persisted so far.  Window ends 2026-06-14; cutover blocked until window closes.
- **Sign-conflation hallucination (P2)** — open issue tracked separately (`natal_object_engine.py`).  Not a B2 blocker, but queued for after-B2 priority work.

## 12. Rollout Recommendation

**`CONDITIONAL_GO`**

**Conditions to flip to `GO`:**
- Shadow telemetry window not complete (ends 2026-06-14)

If `GO`: cutover proceeds in three stages over 7 days — **10%** (24h) → **50%** (48h) → **100%** with rollback on any of: (a) frame-aware FP rate >2x baseline, (b) routing PASS rate <70%, (c) p95 latency >100ms, (d) any >5% drop in per-suite golden top-1.


## After-B2 priority queue (per operator review)

1. **Cross-Lens Synthesis Phase 2** (tension / contradiction).
2. **Relationship-aware orchestration** (use `proposed_action` telemetry to inform circle-add prompts and lens chaining).
3. **Forum topology resolution** (wire `forum_topology.active_member_id` into the resolver; promotes `forum_to_member_misroute` and `unclassified_unresolved` cases out of the data-gap bucket).
4. **Sign-conflation safeguards** in `natal_object_engine.py` (P2; anti-confusion clauses).


---
### Evidence separation

- **From REAL messages**: gate statuses for false-positive relationship, forum/member ambiguity, target-resolution, shadow-telemetry status, and general-bucket rate are computed on REAL only.
- **From SYNTHETIC messages**: golden-set top-1 (over all suites including the synth slice of `golden_set_pete_mel_historical.yaml`) and retrieval-receipt coverage (PASS rate).
- **Versions** — `intent_router_v2.1.0`, `relationship_router_v2.1.0`, `retrieval_validation_v1.2.0`.
