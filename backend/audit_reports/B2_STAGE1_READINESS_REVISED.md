# Mirror Chat V2 — Revised Stage-1 (10%) Rollout Readiness

_Supersedes the `CONDITIONAL_GO` recommendation in
`B2_FOUNDER_OPERATOR_VALIDATION_JUNE14.md` after B3.2, P4, and B3.1
were completed under the operator's priority change._

## Verdict

# `GO` — pending operator authorization to flip the flag

`INTENT_ROUTER_V2_CUTOVER` remains `false` and
`INTENT_ROUTER_V2_ROLLOUT_PERCENT` remains `0`. The actual cutover
implementation (per-user hash `_stage1_bucket()` + receipt schema
extension + bumping the percentage to `10`) is staged for the
operator's next sign-off and is fully described in
`B2_STAGE1_ROLLOUT_PLAN.md`.

## What changed since June 14

| Trade-off (June 14)                          | June 14 status      | Now           |
|----------------------------------------------|---------------------|---------------|
| Lens-jargon override (Saturn return, 7th h.) | FAIL (4.35%)        | **PASS (0%)** |
| Founder/operator lexicon coverage (40%)      | gap accepted        | **PASS (100% on the 30-prompt suite)** |
| Forum-topology wiring (0% pass)              | wiring not plumbed  | **PASS (100% with `active_member_id`)** |
| All five original B2 hard gates              | PASS                | PASS          |
| Retrieval PASS                               | 100%                | 100%          |
| FP relationship rate                         | 2.17%               | **0%**        |
| Forum/member correctly handled               | 100%                | 100%          |
| Live shadow telemetry window                 | FAIL (~50 min)      | unchanged — accept (a) limited span, or wait |

The three structural objections are closed. The only remaining
trade-off is the live-shadow-window coverage gap — a measurement
artefact (not a router defect) that operator can either accept (the
offline replay corpus is comprehensive) or extend by holding for 3+
days.

## Recommended next action

1. Operator authorises Stage-1 implementation per
   `B2_STAGE1_ROLLOUT_PLAN.md`.
2. Implementation lands:
   - `services/intent_router_v2._stage1_bucket(user_id)` per-user hash
   - `mirror_chat_retrieval_receipts` schema extension (cutover lane)
   - `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10` in `backend/.env`
3. Frontend forum-chat surfaces opt into emitting `forum_topology` in
   request payloads (non-blocking — the backend belt-and-braces
   fallback keeps the resolver correct in the meantime).

## Halt criteria (carried forward)

Any of the following automatically halts progression between stages
and reverts `INTENT_ROUTER_V2_ROLLOUT_PERCENT` to 0:

- Retrieval PASS rate < 97%
- FP relationship rate > 5%
- Any new resolver-failure sub-bucket in live telemetry
- Forum/member correctly-handled rate < 90%
- Any unexpected rise in `target_unresolved`
- Any regression cluster (≥3 of same kind) not represented in the
  golden sets
- Any §13 review-signal gate flipping FAIL since the prior stage

## Confirmation of flag state

```
INTENT_ROUTER_V2_CUTOVER          = false   (unchanged)
INTENT_ROUTER_V2_ROLLOUT_PERCENT  = 0       (unchanged)
INTENT_ROUTER_V2_SHADOW           = true    (unchanged)
```
