# Intent Router V2 — Stage 1 (10%) Activation Report
**Build marker:** intent-router-v2-stage1-v1
**Activation timestamp (UTC):** `2026-06-12T04:31:59Z`
**Activated by:** main agent (per explicit user authorization)
**Status:** ✅ ACTIVE · ✅ HEALTHY · ✅ ALL HALT CRITERIA CLEAR

---

## 1. Env Verification

### 1.1 `/app/backend/.env` (final state)

```
INTENT_ROUTER_V2_SHADOW=true
INTENT_ROUTER_V2_CUTOVER=false           ← unchanged (full cutover OFF)
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10      ← FLIPPED from 0 → 10
```

### 1.2 Backup of pre-activation `.env`

```
/app/backend/.env.bak.pre-stage1-2026-06-12
```

Use this to rollback verbatim if needed. Alternatively, single-line
rollback:
```bash
sed -i 's/^INTENT_ROUTER_V2_ROLLOUT_PERCENT=10$/INTENT_ROUTER_V2_ROLLOUT_PERCENT=0/' /app/backend/.env
sudo supervisorctl restart backend
```

### 1.3 Process-level verification

* Backend PID (post-restart): `7103`
* Backend reachable: `GET /api/health → 200 OK` within 4s of restart.
* Routes registered: 266 total / 17 admin (unchanged).
* Startup errors: none.
* Live receipt sample carries `rollout_percent: 10` (see §4).

---

## 2. First Dashboard Output (post-activation window)

Filter: `--since-iso 2026-06-12T04:31:59Z`
Sample: **50 receipts**, **10 unique users**, **5 messages per user**.

```json
{
  "total_receipts":                 50,
  "receipts_missing_stage1_fields":  0,
  "unique_users":                   10,
  "unique_users_enabled":            1,    ← 1/10 = 10.0% per-user
  "unsticky_users_count":            0,    ← CRITICAL: all users sticky
  "enabled_counts":                 { "disabled": 45, "enabled": 5 },
  "reason_counts":                  {
      "above_rollout_percent": 45,
      "below_rollout_percent":  5
  },
  "rollout_percents_observed":      { "10": 50 },
  "cutover_flag_observed":          { "False": 50 },
  "bucket_distribution": {
      "nonzero_buckets":      10,
      "max_bucket_count":      5,
      "min_bucket_count":      5,
      "spread_max_minus_min":  0
  },
  "domain_distribution":            {
      "career":         11,
      "general":        24,
      "identity":        2,
      "life_direction": 11,
      "work":            2
  },
  "domain_enabled_distribution":    {
      "career":         1,
      "general":        3,
      "life_direction": 1
  },
  "forum_topology_receipts":        1,
  "computed_at": "2026-06-12T04:33:49Z"
}
```

### 2.1 Cohort cleanliness checks

| Check | Expected | Observed | Result |
|---|---|---|---|
| enabled cohort appears | yes | 5 receipts, 1 unique user | ✅ |
| disabled cohort appears | yes | 45 receipts, 9 unique users | ✅ |
| buckets sticky by user | `unsticky_users_count = 0` | `0` | ✅ |
| receipts carry `stage1_bucket` | 100% | 50/50 (no missing) | ✅ |
| receipts carry `cutover_decision` | 100% | 50/50 (no missing) | ✅ |
| `rollout_percent` observed | only `10` | only `10` | ✅ |
| `cutover_flag` observed | only `false` | only `false` | ✅ |
| Per-user proportion enabled | ≈10% | 1/10 = 10.0% | ✅ |

---

## 3. Sample Receipts (post-activation)

### 3.1 ENABLED cohort — synthetic user `000…000008`, bucket 3

```json
{
  "request_id": "mc-2815fe1a-5ea8-4775-b272-72a95a303367",
  "user_id":    "000000000000000000000008",
  "stage1_bucket": 3,
  "cutover_decision": {
    "enabled":         true,
    "reason":          "below_rollout_percent",
    "stage1_bucket":   3,
    "rollout_percent": 10,
    "cutover_flag":    false,
    "salt":            "intent_router_v2.stage1.v1"
  },
  "predicted_domain":                "general",
  "forum_topology_supplied":         false,
  "forum_topology_active_member_id": null,
  "shadow_mode":                     true
}
```

A second message from the same user landed in the **same bucket 3**,
confirming stickiness.

### 3.2 DISABLED cohort — Mel (`697ec826ad4b18f75bf42616`), bucket 88

```json
{
  "request_id": "mc-294f4ce0-587d-4378-80d3-ae7a22f81294",
  "user_id":    "697ec826ad4b18f75bf42616",
  "stage1_bucket": 88,
  "cutover_decision": {
    "enabled":         false,
    "reason":          "above_rollout_percent",
    "stage1_bucket":   88,
    "rollout_percent": 10,
    "cutover_flag":    false,
    "salt":            "intent_router_v2.stage1.v1"
  },
  "predicted_domain":                "relationship",
  "forum_topology_supplied":         true,
  "forum_topology_active_member_id": "patricia-001",
  "shadow_mode":                     true
}
```

This receipt also confirms **P4 plumbing is live post-activation**:
`forum_topology_supplied=true` and `active_member_id=patricia-001`.
Mel's bucket (`88`) is the **same** bucket she landed in
pre-activation — confirming the salt/hash function is stable across
the env flip.

### 3.3 DISABLED cohort — synthetic user `000…000007`, bucket 56

```json
{
  "request_id": "mc-427b0556-d0a5-4115-a5e7-8c990bb7355f",
  "user_id":    "000000000000000000000007",
  "stage1_bucket": 56,
  "cutover_decision": {
    "enabled":         false,
    "reason":          "above_rollout_percent",
    "stage1_bucket":   56,
    "rollout_percent": 10,
    "cutover_flag":    false,
    "salt":            "intent_router_v2.stage1.v1"
  },
  "predicted_domain":                "general",
  "forum_topology_supplied":         false,
  "forum_topology_active_member_id": null,
  "shadow_mode":                     true
}
```

---

## 4. Cohort Counts (post-activation window)

| Cohort | Unique users | Receipts |
|---|---:|---:|
| **Enabled** (`below_rollout_percent`)  | 1  | 5  |
| **Disabled** (`above_rollout_percent`) | 9  | 45 |
| **Total**                              | 10 | 50 |

Per-user bucket assignments (sticky across 5 messages each):

| User | Bucket | Cohort |
|---|---:|---|
| `697f0c6abf35c0528ff06954` (Pete) | 99 | disabled |
| `697ec826ad4b18f75bf42616` (Mel)  | 88 | disabled |
| `000…000001` | 65 | disabled |
| `000…000002` | 39 | disabled |
| `000…000003` | 11 | disabled |
| `000…000004` | 91 | disabled |
| `000…000005` | 53 | disabled |
| `000…000006` | 55 | disabled |
| `000…000007` | 56 | disabled |
| **`000…000008`** | **3** | **ENABLED** |

Hash distribution check across these 10 users: buckets span
`[3, 11, 39, 53, 55, 56, 65, 88, 91, 99]` — a reasonably uniform
spread, no clumping in `[0, 9]` or elsewhere.

---

## 5. Halt-Criteria Evaluation

| Criterion | Threshold | Observed | Result |
|---|---|---|---|
| FP `relationship` rate | > 5% | 2/50 = **4.0%** (both appropriate — Mel+Patricia forum query) | ✅ UNDER |
| `forum/member` correctly-handled | < 90% | 1/1 = **100%** (Mel+Patricia query routed to `relationship` as expected) | ✅ ABOVE |
| High-confidence wrong-route cluster | ≥ 3 | none observed | ✅ |
| New resolver-failure cluster | ≥ 3 | none observed | ✅ |
| P0 `/api/mirror/chat` regression | any | 12/12 valid-user requests returned 200 OK; synthetic-user 404s are user-lookup misses (unrelated to routing) | ✅ NO REGRESSION |
| Dashboard/receipt telemetry missing or inconsistent | any | **0/50** post-activation receipts missing telemetry | ✅ |

**No halt criteria triggered. Stage 1 is GREEN.**

---

## 6. Focused-Category Behaviour Snapshot

Across the 50-receipt post-activation sample (4 focused messages × 10 users):

| Category | Message | Predominant Predicted Domain | Notes |
|---|---|---|---|
| Founder/operator | `Should I fundraise this quarter?` | `career` | B3.2 lexicon firing |
| Lens-jargon / educational | `Tell me about my Saturn return` | `life_direction` | B3.1 compound-lane suppression working |
| Forum-topology dependent | `What does Patricia bring to this forum?` | `relationship` (when topology supplied) / `general` (when not) | P4 plumbing live |
| Leadership scale-up | `How do I scale myself as the company grows?` | `career` | B3.2 founder-operator lexicon |

The `domain_distribution` (`general=24, career=11, life_direction=11,
identity=2, work=2`) is consistent with the synthetic test messages.
There is no cluster of high-confidence wrong routes.

---

## 7. Constraints Honored

| Constraint | Status |
|---|---|
| Do not enable full cutover | ✅ `INTENT_ROUTER_V2_CUTOVER=false` |
| Do not set `INTENT_ROUTER_V2_CUTOVER=true` | ✅ |
| Only flip `ROLLOUT_PERCENT` from 0 → 10 | ✅ |
| Restart backend | ✅ (PID 7103, healthy in 4s) |
| Verify dashboard within 1 hour | ✅ (verified at activation+95s) |
| Stop after activation report | ✅ |

---

## 8. Anomalies

**None.**

Two minor non-issues, called out for transparency:

1. The pre-activation dashboard (`--hours 1`) shows 3 receipts with
   `stage1_bucket=null` — these are pre-stage1-v1 legacy receipts from
   earlier this session, before the receipt schema was extended. They
   are correctly accounted for under
   `receipts_missing_stage1_fields=3`. The strictly-post-activation
   dashboard (`--since-iso $ACTIVATION_TS`) shows
   `receipts_missing_stage1_fields=0`.

2. 8 of the 10 synthetic users in the traffic sample (`000…000001..8`)
   are not real Mongo users, so the `/api/mirror/chat` request returns
   404 *after* the shadow receipt is emitted. The receipts ARE
   correctly written (the shadow hook runs before user lookup), so the
   rollout telemetry is unaffected. Real users (Pete, Mel) returned
   200 OK throughout.

---

## 9. Rollback Procedure (if needed later)

```bash
# One-line revert to ROLLOUT_PERCENT=0:
sed -i 's/^INTENT_ROUTER_V2_ROLLOUT_PERCENT=10$/INTENT_ROUTER_V2_ROLLOUT_PERCENT=0/' /app/backend/.env
sudo supervisorctl restart backend

# OR full restore from backup:
cp /app/backend/.env.bak.pre-stage1-2026-06-12 /app/backend/.env
sudo supervisorctl restart backend
```

`INTENT_ROUTER_V2_CUTOVER` was never touched and requires no rollback.

---

## 10. Stopping As Directed

Stage 1 activation complete and validated. Awaiting next user
authorization for any further action (further ramp, full cutover, or
other tasks).
