# P3 Observation Dashboard

**Tool:** `backend/tools/p3_observation_dashboard.py`
**Source:** `mirror_chat_retrieval_receipts` collection (MongoDB)
**Mode:** Strictly **read-only**. Never writes, never modifies the live response path.

---

## 1. Purpose

Aggregate the `relationship_orchestration_v1` block emitted in every
shadow receipt and produce:

* Per-bucket counts: `spouse / child / cofounder / forum_member / self`.
* Reorder rate (overall + non-self + per-bucket).
* Most common modulation patterns (which lens-sets get modulated together).
* Role distribution (spouse / wife / cofounder / etc.).
* Target-resolution success rate (non-self only).
* Active-member-id utilization on `forum_member` bucket.
* Mean rank-delta per lens per bucket (positive = lens moved up).
* Top-of-stack lens after re-rank per bucket.
* Stage 1 telemetry sanity (cutover_enabled count ≤ rollout-percent).
* Calibration recommendations.
* Readiness criteria scorecard for exiting shadow mode.

---

## 2. Usage

```bash
# 7-day window, markdown to stdout
python tools/p3_observation_dashboard.py --window-days 7

# 7-day window, write both formats
python tools/p3_observation_dashboard.py \
    --window-days 7 \
    --markdown-out audit_reports/P3_OBSERVATION_REPORT.md \
    --json-out audit_reports/P3_OBSERVATION_METRICS.json

# 3-day window, JSON only
python tools/p3_observation_dashboard.py --window-days 3 --format json
```

Flags:

| Flag | Default | Meaning |
|---|---|---|
| `--window-days N` | 7 | Look-back window in days |
| `--format` | `markdown` | `markdown` or `json` |
| `--markdown-out PATH` | – | Write markdown report to file |
| `--json-out PATH` | – | Write JSON metrics to file |

---

## 3. Metrics shape (JSON)

```jsonc
{
  "window_days": 7,
  "metrics": {
    "schema": "p3_observation_v1",
    "totals": {
      "receipts_in_window":  <int>,
      "receipts_with_p3":    <int>,
      "p3_coverage_pct":     <float 0-100>
    },
    "bucket_counts": {
      "spouse": <int>, "child": <int>, "cofounder": <int>,
      "forum_member": <int>, "self": <int>
    },
    "bucket_reorder_rate_pct":  { "<bucket>": <float> },
    "bucket_target_bound":      { "<bucket>": <int> },
    "bucket_active_member_bound": { "<bucket>": <int> },
    "overall_reorder_rate_pct": <float>,
    "non_self_reorder_rate_pct": <float>,
    "role_distribution":        { "<role>": <int> },
    "framing_hint_distribution":{ "<hint>": <int> },
    "applied_rules_distribution": { "<rule>": <int> },
    "modulation_patterns":      { "<lens+set+signature>": <int> },
    "context_mode_distribution":{ "<mode>": <int> },
    "top_lens_after_per_bucket":{ "<bucket>": { "<lens>": <int> } },
    "rank_delta_means":         { "<bucket>": { "<lens>": <float> } },
    "target_resolution": {
      "non_self_attempts": <int>,
      "non_self_success":  <int>,
      "success_pct":       <float>
    },
    "forum_topology": {
      "forum_member_bucket_count":    <int>,
      "active_member_id_bound_count": <int>,
      "active_member_id_util_pct":    <float>
    },
    "stage1_telemetry": {
      "stage1_bucket_deciles_seen": { "0": <int>, "10": <int>, ... },
      "cutover_enabled_count":      <int>,
      "cutover_enabled_pct":        <float>
    }
  },
  "readiness":       { "<criterion>": {required, actual, pass}, "overall_pass": <bool> },
  "recommendations": [ {severity, rule, msg}, ... ]
}
```

---

## 4. Readiness criteria for exiting shadow mode

The dashboard enforces these floors. **ALL must be satisfied** before
the P3 plan can be surfaced into the live response.

| Criterion | Floor | Why |
|---|---:|---|
| `min_receipts_in_window` | **500** | Statistical confidence on bucket shares |
| `min_p3_coverage_pct` | **95.0%** | Confirms every shadow request runs the orchestrator |
| `min_spouse_receipts` | **20** | Modulation calibration needs samples |
| `min_forum_member_receipts` | **20** | Forum topology utilization needs samples |
| `min_cofounder_receipts` | **10** | Cofounder bucket fires less often — lower bar OK |
| `min_child_receipts` | **10** | Parenting traffic is lower volume — lower bar OK |
| `min_active_member_id_util_pct` | **60.0%** | Forum buckets without active_member_id signal P4 plumbing gap |
| `min_target_resolution_pct` | **80.0%** | Non-self buckets without target_resolved waste the rule |
| `non_self_reorder_rate_pct` | **60.0–80.0%** | Outside this band → modulations too low or too aggressive |
| `regression_top1_floor_pct` | **95.0%** | Intent-router baseline cannot regress |
| `regression_routing_pass_floor_pct` | **100.0%** | Routing must remain bulletproof |

Regression floors are enforced **externally** (via
`tools/run_v3_validation.py`); the dashboard records the criteria so
operators have a single scorecard.

---

## 5. Calibration heuristics

The recommendation engine surfaces tunings when a bucket has **enough
volume** (default ≥ 20 receipts; cofounder/child ≥ 10):

| Signal | Threshold | Suggested action |
|---|---|---|
| Reorder rate ≥ 95% | bucket samples ≥ 20 | Modulations may be **too aggressive**; reduce dominant lens by 0.05–0.10 |
| Reorder rate < 30% | bucket samples ≥ 20 | Modulations may be **too low**; raise dominant lens by 0.05–0.10 |
| Mean rank-delta ≥ +3.0 for a lens | bucket samples ≥ 20 | That lens is jumping too aggressively |
| Mean rank-delta ≤ −2.0 for a lens | bucket samples ≥ 20 | Lens is being demoted unexpectedly; baseline weight may be too low |
| `target_resolution.success_pct < 80%` | non-self attempts ≥ 30 | Investigate `relationship_router_v2` / `saved_people` coverage |
| `active_member_id_util_pct < 60%` | forum_member samples ≥ 30 | Investigate P4 plumbing at the API edge |
| Bucket samples below floor | – | Defer modulation tuning until traffic accumulates |

Until any bucket clears the volume floor the dashboard emits
`no_action_required` / `defer modulation tuning`.

---

## 6. Operating procedure (3–7 day observation window)

1. **Day 0** — Land the P3 orchestration block (already done).
2. **Day 0** — Generate baseline metrics:
   ```bash
   python tools/p3_observation_dashboard.py --window-days 1 \
     --markdown-out audit_reports/P3_OBSERVATION_DAY_0.md \
     --json-out audit_reports/P3_OBSERVATION_DAY_0.json
   ```
3. **Day 3** — Mid-window check. Same command, window 3.
4. **Day 7** — End-of-window report:
   ```bash
   python tools/p3_observation_dashboard.py --window-days 7 \
     --markdown-out audit_reports/P3_OBSERVATION_REPORT.md \
     --json-out audit_reports/P3_OBSERVATION_METRICS.json
   ```
5. Cross-check intent-router regression at end of window:
   ```bash
   python tools/run_v3_validation.py > audit_reports/P3_OBS_REGRESSION_SNAPSHOT.json
   ```
6. **Review with operator** — bucket coverage, calibration
   recommendations, readiness scorecard.
7. If readiness criteria pass AND regression floors hold → request
   explicit authorisation to surface `lens_priority_after` +
   `framing_hint` to the live response.

---

## 7. Constraints honoured

* `INTENT_ROUTER_V2_CUTOVER` remains `false`.
* `INTENT_ROUTER_V2_ROLLOUT_PERCENT` remains `10`.
* Dashboard is **read-only** — no DB writes, no env writes.
* Live response continues to read `lens_priority` directly from
  `intent_envelope.lens_priority` (the orchestration plan is not yet
  surfaced).
* Shadow telemetry collection continues uninterrupted on the 10%
  rollout bucket.
