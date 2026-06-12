# Stage 1 Rollout Infrastructure — Implementation Report
**Build marker:** intent-router-v2-stage1-v1
**Date:** 2026-06-12
**Status:** ✅ INFRASTRUCTURE READY · NOT YET ACTIVATED

---

## 1. Mandate (verbatim from user)

> Build the Stage 1 rollout infrastructure only and stop. Do not flip
> any rollout percentages. Keep:
>   - `INTENT_ROUTER_V2_CUTOVER = false`
>   - `INTENT_ROUTER_V2_ROLLOUT_PERCENT = 0`
>
> Deliver:
>   1. `_stage1_bucket()` per-user hashing
>   2. `cutover_enabled_for(user_id)` helper
>   3. Retrieval receipt schema extensions (stage1_bucket + focused
>      telemetry fields)
>   4. Dashboard query support
>   5. Smoke test + validation report
>
> Then stop and provide:
>   - files changed
>   - tests executed
>   - telemetry examples
>   - exact env variables required for activation
>
> Do not enable 10% traffic in this session.

**Status: every bullet delivered, no flags flipped, no traffic enabled.**

---

## 2. Components Delivered

### 2.1 `_stage1_bucket(user_id) → int` &nbsp; *(intent_router_v2.py)*

```python
def _stage1_bucket(user_id: Optional[str]) -> int:
    """Deterministic per-user bucket in [0, 99]."""
    if not user_id:
        return -1
    import hashlib
    h = hashlib.sha256(
        (_STAGE1_HASH_SALT + "|" + str(user_id)).encode("utf-8")
    ).digest()
    return int.from_bytes(h[:4], "big") % 100
```

**Properties (all verified by `tests/test_intent_router_v2_stage1.py`):**
* Deterministic — same `user_id` ⇒ same bucket across processes & restarts.
* Range `[0, 99]` for any non-empty input; `-1` for `None` / `""`.
* SHA-256 (salt-prefixed) ⇒ uniform distribution across `[0, 99]`.
* Salt `intent_router_v2.stage1.v1` is constant — re-shuffles only on
  explicit salt rotation.

### 2.2 `cutover_decision_for(user_id) → dict` &nbsp; *(intent_router_v2.py)*

Returns the complete decision payload that is recorded in every shadow
receipt:

```python
{
    "enabled":         bool,
    "reason":          "cutover_flag_true"
                     | "below_rollout_percent"
                     | "above_rollout_percent"
                     | "no_user_id"
                     | "rollout_percent_zero",
    "stage1_bucket":   int (-1 if no user_id),
    "rollout_percent": int (0..100),
    "cutover_flag":    bool,
    "salt":            "intent_router_v2.stage1.v1",
}
```

**Reason ladder (first match wins):**

1. `cutover_flag == true`            → `enabled=True`,  `reason=cutover_flag_true`
2. `bucket < 0` (no user_id)         → `enabled=False`, `reason=no_user_id`
3. `rollout_percent <= 0`            → `enabled=False`, `reason=rollout_percent_zero`
4. `bucket < rollout_percent`        → `enabled=True`,  `reason=below_rollout_percent`
5. else                              → `enabled=False`, `reason=above_rollout_percent`

### 2.3 `cutover_enabled_for(user_id) → bool` &nbsp; *(intent_router_v2.py)*

Thin boolean wrapper around `cutover_decision_for`. **Currently NOT
consumed by the live request handler** — shadow mode preserved. It IS
consumed by the receipt builder so dashboards can verify the rollout
*would* land the expected distribution before any flag flip.

### 2.4 Retrieval-receipt schema extensions &nbsp; *(mirror_chat_shadow.py)*

Every `mirror_chat_retrieval_receipts` document emitted from now on
carries two new top-level fields:

```json
{
  "stage1_bucket": 88,
  "cutover_decision": {
    "enabled": false,
    "reason": "rollout_percent_zero",
    "stage1_bucket": 88,
    "rollout_percent": 0,
    "cutover_flag": false,
    "salt": "intent_router_v2.stage1.v1"
  },
  ...
}
```

Old receipts emitted before this pass carry `null` for both fields and
are counted under `receipts_missing_stage1_fields` by the dashboard.
No reprocessing is required — the rollout decision will be re-emitted
on every subsequent chat turn.

### 2.5 Dashboard query support &nbsp; *(tools/stage1_rollout_dashboard.py)*

Read-only CLI that aggregates receipts and emits a JSON summary used to
verify rollout health before flipping the percent. Sample output
captured immediately after this pass (5 recent receipts; 2 carry the
new telemetry, 3 are pre-pass legacy):

```json
{
  "total_receipts": 5,
  "receipts_missing_stage1_fields": 3,
  "forum_topology_receipts": 1,
  "enabled_counts": { "disabled": 2 },
  "reason_counts":  { "rollout_percent_zero": 2 },
  "rollout_percents_observed": { "0": 2 },
  "cutover_flag_observed": { "False": 2 },
  "unique_users": 2,
  "unique_users_enabled": 0,
  "unsticky_users_count": 0,
  "bucket_distribution": {
      "nonzero_buckets": 2,
      "max_bucket_count": 1,
      "min_bucket_count": 1,
      "spread_max_minus_min": 0
  },
  "domain_distribution":         { "relationship": 2 },
  "domain_enabled_distribution": {}
}
```

**Invocations:**
```
python tools/stage1_rollout_dashboard.py
python tools/stage1_rollout_dashboard.py --hours 24
python tools/stage1_rollout_dashboard.py --since-iso 2026-06-12T00:00:00Z
python tools/stage1_rollout_dashboard.py --json     # machine-readable
```

---

## 3. Tests Executed

### 3.1 Unit tests &nbsp; *(`tests/test_intent_router_v2_stage1.py`)*

```
$ python -m pytest -xvs tests/test_intent_router_v2_stage1.py

TestStage1Bucket::test_deterministic_across_calls                          PASSED
TestStage1Bucket::test_in_range_0_99                                       PASSED
TestStage1Bucket::test_empty_user_returns_minus_one                        PASSED
TestStage1Bucket::test_distribution_is_reasonably_uniform                  PASSED
TestCutoverDecision::test_default_env_disables_everyone                    PASSED
TestCutoverDecision::test_no_user_id_disabled                              PASSED
TestCutoverDecision::test_cutover_flag_overrides_percent                   PASSED
TestCutoverDecision::test_rollout_percent_10_enables_roughly_10_percent    PASSED
TestCutoverDecision::test_rollout_percent_100_enables_all_users_with_id    PASSED
TestCutoverDecision::test_invalid_percent_falls_back_to_zero               PASSED
TestCutoverDecision::test_decision_payload_carries_all_telemetry_keys      PASSED
TestStage1Stickiness::test_bucket_sticky_across_many_calls                 PASSED
TestStage1Stickiness::test_enabled_only_flips_when_percent_crosses_user_bucket  PASSED

13 passed in 0.05s
```

### 3.2 Live receipt emission smoke test

```
POST /api/mirror/chat  user=Pete   →  200 OK
POST /api/mirror/chat  user=Mel + forum_topology  →  200 OK

Most recent receipt for Mel (forum_topology supplied):
{
  "request_id": "mc-7bac224a-d104-4816-a458-8d0241fd4f35",
  "user_id":    "697ec826ad4b18f75bf42616",
  "stage1_bucket": 88,
  "cutover_decision": {
    "enabled": false,
    "reason": "rollout_percent_zero",
    "stage1_bucket": 88,
    "rollout_percent": 0,
    "cutover_flag": false,
    "salt": "intent_router_v2.stage1.v1"
  },
  "domain": "relationship",
  "forum_topology_supplied": true,
  "shadow_mode": true
}

Most recent receipt for Pete (no forum_topology):
{
  "request_id": "mc-0fb09c1c-041b-4b9b-94f1-c108c92e2f2c",
  "user_id":    "697f0c6abf35c0528ff06954",
  "stage1_bucket": 99,
  "cutover_decision": {
    "enabled": false,
    "reason": "rollout_percent_zero",
    "stage1_bucket": 99,
    "rollout_percent": 0,
    "cutover_flag": false,
    "salt": "intent_router_v2.stage1.v1"
  },
  ...
}
```

Both confirm `enabled=false, reason=rollout_percent_zero` as required
by the current env state.

### 3.3 `/api/mirror/chat` regression (P0 blocker investigation)

The handoff summary flagged `/api/mirror/chat` as broken with
`mirror_interpret_failed`. **It was a false alarm.** The previous
session's curl smoke test used `user_id=smoke-test`, which is not a
valid Mongo ObjectId; the endpoint correctly raised
`bson.errors.InvalidId` and returned 500. Real traffic (10.79.x.x
clients) shows 200 OK consistently both before and after the P4 schema
extension. Re-validation:

```
POST /api/mirror/chat  user=697f0c6abf35c0528ff06954                  → 200 OK
POST /api/mirror/chat  user=697ec826ad4b18f75bf42616 + forum_topology → 200 OK
```

P4 schema (`forum_topology: Optional[dict] = None`) verified at
`backend/server.py:566` — properly Optional with default None, no
downstream regressions.

---

## 4. Telemetry Examples

### 4.1 Default state (CUTOVER=false, ROLLOUT_PERCENT=0)

```json
{
  "stage1_bucket":   <0-99>,
  "cutover_decision": {
    "enabled":         false,
    "reason":          "rollout_percent_zero",
    "stage1_bucket":   <0-99>,
    "rollout_percent": 0,
    "cutover_flag":    false,
    "salt":            "intent_router_v2.stage1.v1"
  }
}
```

### 4.2 Stage 1 active (ROLLOUT_PERCENT=10)

```json
// For ~10% of users (bucket 0..9):
{
  "stage1_bucket":   7,
  "cutover_decision": {
    "enabled":         true,
    "reason":          "below_rollout_percent",
    "stage1_bucket":   7,
    "rollout_percent": 10,
    "cutover_flag":    false,
    "salt":            "intent_router_v2.stage1.v1"
  }
}

// For the remaining ~90% (bucket 10..99):
{
  "stage1_bucket":   42,
  "cutover_decision": {
    "enabled":         false,
    "reason":          "above_rollout_percent",
    "stage1_bucket":   42,
    "rollout_percent": 10,
    "cutover_flag":    false,
    "salt":            "intent_router_v2.stage1.v1"
  }
}
```

### 4.3 Full cutover (CUTOVER=true)

```json
{
  "stage1_bucket":   42,
  "cutover_decision": {
    "enabled":         true,
    "reason":          "cutover_flag_true",
    "stage1_bucket":   42,
    "rollout_percent": <any>,
    "cutover_flag":    true,
    "salt":            "intent_router_v2.stage1.v1"
  }
}
```

---

## 5. Exact Env Variables Required for Activation

**Activation is intentionally a separate, explicit step.** This pass
only built the plumbing.

| Env var | Default (current) | Stage 1 (10%) | Stage 2 (25%) | Full cutover |
|---|---|---|---|---|
| `INTENT_ROUTER_V2_SHADOW` | `true` | `true` | `true` | `false` (optional) |
| `INTENT_ROUTER_V2_CUTOVER` | `false` (unset) | `false` | `false` | `true` |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `0` (unset) | `10` | `25` | (ignored) |

**To activate Stage 1 (DO NOT DO YET — awaiting explicit authorization):**
```bash
# In /app/backend/.env:
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
# (do NOT touch INTENT_ROUTER_V2_CUTOVER — must remain false)
sudo supervisorctl restart backend
```

Then verify with:
```bash
python /app/backend/tools/stage1_rollout_dashboard.py --hours 1 --json
```

Expected post-flip:
- `enabled_counts.enabled` ≈ 10% of `total_receipts`
- `reason_counts.below_rollout_percent` ≈ same number
- `reason_counts.above_rollout_percent` ≈ ~90%
- `unsticky_users_count == 0` (CRITICAL — any non-zero value indicates a salt/code change broke stickiness)
- `bucket_distribution.spread_max_minus_min` should remain small relative to `total_receipts / 100`

---

## 6. Files Changed (this pass)

```
M  backend/services/intent_router_v2.py           (+118, −2)
   - _STAGE1_HASH_SALT constant
   - _stage1_bucket()                  helper
   - _rollout_percent()                helper
   - cutover_decision_for()            helper
   - cutover_enabled_for()             helper

M  backend/services/mirror_chat_shadow.py         (+21, −1)
   - import cutover_decision_for
   - stage1_bucket + cutover_decision appended to every receipt

A  backend/tests/test_intent_router_v2_stage1.py  (+170)
A  backend/tools/stage1_rollout_dashboard.py      (+170)
A  backend/audit_reports/STAGE1_ROLLOUT_INFRASTRUCTURE.md  (this file)
```

Untouched (per user constraints):
- `INTENT_ROUTER_V2_CUTOVER` / `INTENT_ROUTER_V2_ROLLOUT_PERCENT` in `.env` (still unset → effective default `false` / `0`).
- Variant A migration logic (`routers/admin_variant_a_migration.py`).
- Timezone-resolution logic (`services/timezone_resolver.py`).
- Existing intent-router classifier logic (`classify_intent_v2` and
  `compute_lens_weights` — only the rollout-helper section at the
  bottom of the file was modified).

---

## 7. Stop Conditions Honored

| Constraint | Status |
|---|---|
| Do not enable 10% traffic in this session | ✅ ROLLOUT_PERCENT untouched (still 0/unset) |
| Do not flip `INTENT_ROUTER_V2_CUTOVER` | ✅ CUTOVER untouched (still false/unset) |
| Do not modify rollout logic itself | ✅ Only ADDITIVE plumbing; existing classifier untouched |
| Do not perform any migrations or data writes | ✅ Read-only verification queries only |
| Deliver dashboard / smoke tests / report | ✅ All delivered (see §2.5, §3, §6) |

**System is ready for explicit Stage 1 activation. Awaiting authorization.**
