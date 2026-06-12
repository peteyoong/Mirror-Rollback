# Mirror Chat V2 — Slice B2 → Stage 1 Rollout Plan (10%)

_Authorization basis_: Operator decision on June 14 EOD accepted `CONDITIONAL_GO`
and authorized **rollout preparation only**. **No cutover flag flip is
authorized by this plan**.

_State at plan publication_:
- `INTENT_ROUTER_V2_CUTOVER = false` (unchanged, must remain `false` until
  Stage-1 entry is signed off).
- `INTENT_ROUTER_V2_SHADOW = true` (unchanged; shadow telemetry continues).
- All Slice B2 hard gates PASS; no new regressions vs. June 11 baseline.

---

## 1. Scope and intent of Stage 1

| Property                 | Value                                                              |
|--------------------------|--------------------------------------------------------------------|
| Traffic share            | **10%** of eligible `POST /api/mirror/chat` requests                |
| Eligibility              | All authenticated users; all three frames (self/member/forum)       |
| Observation window       | **≥ 72 hours of live traffic** (calendar 3 days), then operator review |
| Minimum sample size      | ≥ 250 chat receipts in the 10% bucket (auto-extend window otherwise) |
| Cutover flag value       | `INTENT_ROUTER_V2_CUTOVER = true` **only inside the 10% bucket**    |
| Shadow flag value        | Remains `true` for the 90% control group (unchanged today)          |
| Rollback latency target  | **< 60 seconds** (single env-var flip + supervisor restart)         |
| Cutover semantics        | Per-user deterministic hash → bucket; users do **not** flip back and forth between runs |

---

## 2. Traffic-split mechanism (proposed)

### 2.1 Selection function

The router cutover check is currently a single global toggle (see
`services/intent_router_v2.py:cutover_enabled()`). For Stage-1 a deterministic
per-user bucket is required so a given user never sees both routers within the
same session.

**Proposed function (NOT YET IMPLEMENTED — implementation will require explicit
operator sign-off as a separate step):**

```python
def _stage1_bucket(user_id: str) -> bool:
    """Return True if this user is in the Stage-1 10% bucket."""
    pct = int(os.environ.get("INTENT_ROUTER_V2_ROLLOUT_PERCENT", "0"))
    if pct <= 0:
        return False
    if pct >= 100:
        return True
    h = hashlib.sha1(f"intent-router-v2|{user_id}".encode()).digest()
    return (h[0] / 256.0) * 100.0 < pct


def cutover_enabled_for(user_id: str) -> bool:
    """Production hook: True iff (legacy flag is set OR user is in the
    Stage-1 bucket).  The router envelope still emits shadow telemetry
    for the 90% control group."""
    if cutover_enabled():
        return True
    return _stage1_bucket(user_id)
```

### 2.2 Env-var contract (Stage 1)

| Variable                          | Stage 1 value | Notes                                   |
|-----------------------------------|---------------|-----------------------------------------|
| `INTENT_ROUTER_V2_CUTOVER`        | `false`       | Global cutover stays off                |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT`| `10`          | New env var, read by `_stage1_bucket()` |
| `INTENT_ROUTER_V2_SHADOW`         | `true`        | 90% control group continues to shadow   |

### 2.3 Why a per-user hash, not a per-request coin flip?

- A user must experience **one consistent router** within a session.
- Receipts can be **stratified deterministically** (Stage-1 vs control) for
  apples-to-apples comparison.
- Halt criteria can target the Stage-1 bucket without rolling back the entire
  flag.

---

## 3. Stage 1 entry criteria (must ALL be true before flipping
   `INTENT_ROUTER_V2_ROLLOUT_PERCENT` from 0 to 10)

| #  | Criterion                                                                            | Today's status                  |
|----|--------------------------------------------------------------------------------------|---------------------------------|
| 1  | All B2 hard gates PASS                                                               | ✅ PASS                          |
| 2  | Zero new regressions vs. June 11 baseline                                            | ✅ PASS                          |
| 3  | Per-user bucket selection code implemented, peer-reviewed, and merged                | ⏳ NOT IMPLEMENTED               |
| 4  | Stage-1 telemetry counters live in `mirror_chat_retrieval_receipts`                  | ⏳ NEW — needs receipt field     |
| 5  | Rollback runbook tested in staging (single env-var flip restores 100% legacy)        | ⏳ NOT TESTED                    |
| 6  | Operator explicit sign-off on this plan                                              | ⏳ PENDING THIS DOCUMENT         |
| 7  | Stage-1 dashboard wired (see §6)                                                     | ⏳ NEW                           |

> Items 3-7 must each be addressed in **separate authorization steps**. This
> plan does **not** authorize any of them.

---

## 4. Stage 1 advancement criteria (must ALL be true to proceed to Stage 2 / 50%)

| Metric (Stage-1 bucket only)                          | Threshold                       |
|-------------------------------------------------------|---------------------------------|
| Retrieval PASS rate                                   | ≥ 97%                            |
| False-positive relationship rate                      | ≤ 5%                             |
| Forum/member correctly-handled rate                   | ≥ 90%                            |
| New resolver-failure sub-buckets                      | 0                                |
| `target_unresolved` rate vs. control bucket           | Drift ≤ +2 percentage points     |
| `domain_drift_kind` rate (when ground truth exists)   | ≤ 5%                             |
| `lens_jargon_override` rate                           | Stable or improving vs. June 14  |
| `high_confidence_wrong_route` rate                    | < 1%                             |
| `couple_forum_bleed_kind` count                       | = 0                              |
| **Founder/operator routing PASS rate**                | ≥ 85% (baseline collected during Stage-1) |
| **Educational astrology routing PASS rate**           | ≥ 95% (no degradation)           |
| **Forum-topology-dependent context_mode=RELATIONAL**  | ≥ 90% once P4 ships              |
| Regression cluster (≥3 of same kind) NOT in golden    | 0                                |
| Window length                                         | ≥ 72h AND ≥ 250 Stage-1 receipts |

---

## 5. Halt criteria (automatic between any two stages — unchanged from B2 plan)

Any of the following triggers an **immediate halt** and operator review:

- Retrieval PASS rate < 97%
- FP relationship rate > 5%
- Any new resolver-failure sub-bucket in live telemetry
- Forum/member correctly-handled rate < 90%
- Any unexpected rise in `target_unresolved` rate
- Any regression cluster (≥3 of same kind) not represented in the golden sets
- Any §13 review-signal gate flipping FAIL since the prior stage:
  - domain drift, lens-jargon override, relationship-context loss,
    wrong-target selection, multi-lens coverage, high-confidence wrong route,
    couple↔forum bleed, payload >25% shrinkage.

---

## 6. Stage 1 dashboard — three focused telemetry categories
   (analytical classifiers already implemented; PRD only)

Each Stage-1 receipt now carries the three classifier flags (in
`B2_REPLAY_RESULTS.json` per-row and aggregated in `B2_READINESS_REPORT.json`):

### 6.1 Founder / operator queries (B3.2 target lane)
- Trigger: `_FOUNDER_RE` (founder, cofounder, CEO/CTO/COO, board, investor,
  fundraising, runway, hiring, delegation, leadership, executive, etc.).
- Live observation in replay: **0 cases** in the current 90-day REAL corpus.
- Implication: operator's own usage will dominate this counter; the synthetic
  founder/operator validation suite is the primary signal source until live
  founder traffic accumulates.

### 6.2 Educational astrology queries (B3.1 target lane)
- Trigger: `_EDU_ASTRO_LENS_RE` (Saturn/Venus/Mars/Jupiter/Pluto/etc., houses,
  natal, transit, return, ascendant) **AND NOT** `_EDU_CONTEXTUAL_CUE_RE`
  (no name, no relational/career/temporal cue).
- Live observation in replay: **3 cases**, **100% routing PASS rate**, share
  6.5% of REAL corpus.
- Implication: today these route to `identity` or `relationship` (the §13.2
  lens-jargon-override pattern). After B3.1 lands, they should route to a
  dedicated `educational` lane.

### 6.3 Forum-topology-dependent queries (P4 target lane)
- Trigger: `active_frame=forum` AND no `explicit_target_id` AND no name in
  message.
- Live observation in replay: **22 cases**, **90.9% routing PASS rate**,
  share **47.8%** of REAL corpus.
- Implication: P4 (wire `forum_topology.active_member_id` from chat surface)
  affects nearly half of REAL traffic. **This is the largest pre-Stage-2
  lever.**

---

## 7. Rollback runbook (must be rehearsed before Stage 1 enters)

### 7.1 Single-command rollback

```bash
# Restore the 100% legacy router immediately
export INTENT_ROUTER_V2_ROLLOUT_PERCENT=0
sudo supervisorctl restart backend
```

Expected effect:
- Within < 60 seconds, all new requests route through the legacy
  `question_intent_router` / `astrology_chat_router` stack.
- Shadow telemetry continues to be emitted for in-flight requests.
- No DB rollback required; receipts remain queryable for post-incident
  forensics.

### 7.2 Verification after rollback

1. `tail -f /var/log/supervisor/backend.out.log` — confirm 0 v2 routing
   receipts within 30 seconds.
2. Run `python /app/backend/tools/b2_replay_runner.py` to spot-check the
   replay still aligns with the legacy router behavior.
3. Snapshot `mirror_chat_retrieval_receipts` for post-mortem.

### 7.3 Post-incident artifacts

- `audit_reports/STAGE1_INCIDENT_<timestamp>.md` — operator-written summary.
- `audit_reports/B2_READINESS_REPORT.json` — re-run with `--baseline` to
  surface what changed during the Stage-1 window.

---

## 8. Cadence

| Event                                              | When (relative to flip)          |
|----------------------------------------------------|----------------------------------|
| Flip `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`         | T = 0  (operator-initiated)      |
| First Stage-1 health check                         | T + 6h (smoke test)              |
| Mid-window check                                   | T + 24h                          |
| Stage-1 readiness review                           | T + 72h **OR** ≥ 250 receipts    |
| Operator sign-off → Stage 2 (50%) **OR** halt      | After review                     |

---

## 9. Open items (informational; no writes performed)

These are **separate authorization steps** the operator must approve before
the Stage-1 flip can occur. None are touched by this plan.

1. **Implement `_stage1_bucket()`** in `intent_router_v2.py` + wire from
   `mirror_chat_shadow.py` / `mirror_chat.py`. (Code change; requires sign-off.)
2. **Add `stage1_bucket`, `is_founder_query`, `is_educational_astrology`,
   `is_forum_topology_dependent` to `mirror_chat_retrieval_receipts` writes.**
   (Code change; requires sign-off.)
3. **Add `INTENT_ROUTER_V2_ROLLOUT_PERCENT` to `backend/.env`** with default
   `0`. (Env change; requires sign-off — current `.env` is in the protected
   list.)
4. **Stage-1 dashboard query** for live monitoring (Compass/Atlas saved query
   on `mirror_chat_retrieval_receipts`).
5. **Rollback runbook rehearsal** in a staging-equivalent environment.

> The operator must approve each open item individually before the Stage-1
> entry sequence begins. This plan does **not** request, presume, or grant
> that approval.

---

## 10. Linkage to B3 backlog

The three Stage-1 focused-telemetry categories are designed to **measure**
the impact of three B3 backlog items — they do not themselves change router
behavior:

| Stage-1 category               | B3 backlog item                                | Expected effect on metric  |
|--------------------------------|------------------------------------------------|----------------------------|
| Educational astrology          | **B3.1** Lens-term compound entries + educational-mode disambiguation | Lens-jargon override rate → 0%; educational PASS stays ≥95% |
| Founder/operator               | **B3.2** Founder/operator lexicon expansion    | Founder PASS rate ≥ 95%    |
| Forum-topology-dependent       | **P4**  Forum topology resolution              | Forum context_mode=RELATIONAL ≥ 90% (today 0% in production wiring) |

See `B3_BACKLOG.md` for acceptance criteria.

---

## 11. Sign-off block (to be filled by operator)

```
[ ] Plan reviewed and accepted
[ ] Open items 9.1–9.5 authorized as separate steps
[ ] Entry criteria §3 will be re-checked before flipping the percent flag
[ ] Halt criteria §5 acknowledged
[ ] Rollback runbook §7 rehearsed
Date: __________  Operator: __________
```
