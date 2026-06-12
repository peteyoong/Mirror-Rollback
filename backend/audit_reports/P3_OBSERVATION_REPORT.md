# P3 Observation Report (7-day window)

Generated: 2026-06-12T05:18:56.768914+00:00

**Mode:** SHADOW (P3 plan recorded; live response unchanged).

---

## Day-0 baseline context

This report is the **Day-0 snapshot** taken immediately after the P3
orchestration block was wired into the shadow-receipt builder. The
72 receipts in the window were captured **before** P3 was emitting,
which is why P3 coverage is 1.4% (only the one post-wiring smoke-test
receipt carries the block).

This is expected. The dashboard's readiness scorecard correctly
reports ❌ NOT READY across all criteria because no real traffic has
yet been logged with the new telemetry.

The next observation run, after 3–7 days of real Stage 1 traffic
through the v3 code path, will populate the bucket counts and
calibration signals. To regenerate:

```bash
python tools/p3_observation_dashboard.py --window-days 7 \
    --markdown-out audit_reports/P3_OBSERVATION_REPORT.md \
    --json-out audit_reports/P3_OBSERVATION_METRICS.json
```

Regression and constraint state at Day-0:

| Item | Status |
|---|---|
| `INTENT_ROUTER_V2_CUTOVER` | `false` ✅ |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `10` ✅ |
| Intent-router regression (139 cases) | 97.8% top-1 / 100% routing-pass ✅ |
| Unit tests (P3 + intent + cross-lens) | 43/43 ✅ |
| P3 receipt block emitting on live `/api/mirror/chat` | verified ✅ |

---

## Volume

* Receipts in window: **72**
* Receipts carrying P3 block: **1** (1.4%)

## Bucket distribution

| Bucket | Count | Re-order rate | Target bound | Active-member bound |
|---|---:|---:|---:|---:|
| spouse | 0 | 0.0% | 0 | 0 |
| child | 0 | 0.0% | 0 | 0 |
| cofounder | 0 | 0.0% | 0 | 0 |
| forum_member | 0 | 0.0% | 0 | 0 |
| self | 1 | 0.0% | 0 | 0 |

**Overall re-order rate:** 0.0%
**Non-self re-order rate:** 0.0%

## Role distribution

* `_none_` — 1

## Modulation patterns (signature of lenses modulated)

* `_none_` — 1

## Target resolution

* Non-self attempts: **0**
* Successful target binds: **0** (0.0%)

## Forum-topology utilization

* forum_member buckets: **0**
* with active_member_id bound: **0** (0.0%)

## Top lens after re-rank (per bucket)

* **self** — `relationship`: 1

## Mean rank-delta per lens (positive = promoted)

* **self** — `relationship`: +0.00, `astrology`: +0.00, `human_design`: +0.00, `enneagram`: +0.00, `timeline`: +0.00, `numerology`: +0.00

## Stage 1 telemetry sanity

* `cutover_enabled=True` count: **0** (0.0% of receipts in window)
  — must be ≤ rollout-percent (currently 10).

## Calibration recommendations

* ℹ️ **spouse_underrepresented** — Spouse bucket has 0 receipts (< 20). Continue observation; do not adjust spouse modulations yet.
* ℹ️ **forum_member_underrepresented** — forum_member bucket has 0 receipts (< 20). Defer modulation tuning.
* ℹ️ **cofounder_underrepresented** — cofounder bucket has 0 receipts (< 10). Defer modulation tuning.
* ℹ️ **child_underrepresented** — child bucket has 0 receipts (< 10). Defer modulation tuning.

## Readiness criteria for exiting shadow mode

| Criterion | Required | Actual | Pass |
|---|---:|---:|:---:|
| `min_receipts_in_window` | 500 | 72 | ❌ |
| `min_p3_coverage_pct` | 95.0 | 1.4 | ❌ |
| `min_spouse_receipts` | 20 | 0 | ❌ |
| `min_forum_member_receipts` | 20 | 0 | ❌ |
| `min_cofounder_receipts` | 10 | 0 | ❌ |
| `min_child_receipts` | 10 | 0 | ❌ |
| `min_active_member_id_util_pct` | 60.0 | 0.0 | ❌ |
| `min_target_resolution_pct` | 80.0 | 0.0 | ❌ |
| `non_self_reorder_rate_pct` | 60.0..80.0 | 0.0 | ❌ |

**Overall:** ❌ NOT READY
