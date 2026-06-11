# Mirror Chat V2 — Slice B2 Readiness Report

_Generated: 2026-06-11T19:11:51.974995+00:00_

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
| Target resolution (proposed_action path live) | unresolved_named_rate=26.53% (13 cases, REAL-only) | ≥ 5% to confirm receipt path wired | PASS |
| False-positive relationship rate (frame-aware, REAL) | 2.04% (1 of 49) | ≤ 10% | PASS |
| Forum/member ambiguity (REAL) | 88.46% unresolved (23/26) | ≤ 95% (advisory — fed forum_topology lands in B3) | PASS |
| Shadow telemetry window complete | n=3 receipts, span first=2026-06-11T18:37:11.997781+00:00 → last=2026-06-11T18:46:04.421224+00:00 | ≥ 3d span ending 2026-06-14 | FAIL |
| Manual review complete | auto: report generated; awaiting operator sign-off | operator confirms gates | PENDING_OPERATOR |
## 3. Shadow Telemetry Summary

- Receipts persisted to `mirror_chat_retrieval_receipts`: **3**
- Window: `2026-06-11T18:37:11.997781+00:00` → `2026-06-11T18:46:04.421224+00:00`
- Window-complete: **False** (target span ≥ 3d, ending 2026-06-14)

**Status breakdown (live receipts)**:
- `retrieval_status=PASS` → **3**
- `routing_status=PASS` → **2**
- `routing_status=WARNING` → **1**

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

- Status counts (REAL): `{'NOT_APPLICABLE': 12, 'UNRESOLVED_NO_NAME': 21, 'RESOLVED': 3, 'UNRESOLVED_NAMED': 13}`
- Unresolved-named-target rate (REAL): **26.53%** (13 cases)

Every `UNRESOLVED_NAMED` case carries a `proposed_action` payload (`type=add_to_circle`, with `suggested_name`, `reason`, `source_text`, `confidence`) attached to the diagnostic receipt.

**The proposed_action stays receipt-only.** No UI surface, no relationship-role inference, no auto-create.  This is purely telemetry-gathering during the B2 observation window.

## 7. Forum vs Member Ambiguity Analysis

- Forum/member frame cases (REAL): **26**
- Unresolved target (no `target_id`, no resolved name): **23** (88.46%)

**Caveat:** the replay harness does not currently feed `forum_topology.active_member_id` into the resolver (that wiring lands in B3), so a high unresolved rate on forum/member frames is expected and is *not* counted as a hard blocker.  In live shadow mode the active member is hydrated via `lens` / `about_person_id` request fields, which is why the live shadow `RESOLVED` rate is higher than the replay-corpus rate.

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

- **Forum/member ambiguity:** resolver does not yet receive `forum_topology.active_member_id` in the replay harness — live shadow mode hydrates this from request fields. B3 will wire the topology end-to-end.
- **Real corpus size:** the 90-day real corpus is currently ~49 messages.  Synthetic supplementation is required to stress leadership/purpose/founder voices; the rollout call should not be made on synth alone.
- **Shadow telemetry window not yet complete** — only 3 receipts persisted so far.  Window ends 2026-06-14; cutover blocked until window passes.
- **Sign-conflation hallucination (P2)** — open issue tracked separately (`natal_object_engine.py`), unrelated to routing but feeds the *post-route* synthesis pass.  Not a B2 blocker.

## 12. Rollout Recommendation

**`CONDITIONAL_GO`**

**Conditions to flip to `GO`:**
- Shadow telemetry window not complete (ends 2026-06-14)

If `GO`: cutover proceeds in three stages over 7 days — **10%** (24h) → **50%** (48h) → **100%** with rollback on any of: (a) frame-aware FP rate >2x baseline, (b) routing PASS rate <70%, (c) p95 latency >100ms, (d) any >5% drop in per-suite golden top-1.


---
### Evidence separation

- **From REAL messages**: gate statuses for false-positive relationship, forum/member ambiguity, target-resolution, shadow-telemetry status, and general-bucket rate are computed on REAL only.
- **From SYNTHETIC messages**: golden-set top-1 (over all suites including the synth slice of `golden_set_pete_mel_historical.yaml`) and retrieval-receipt coverage (PASS rate).
- **Versions** — `intent_router_v2.1.0`, `relationship_router_v2.1.0`, `retrieval_validation_v1.2.0`.
