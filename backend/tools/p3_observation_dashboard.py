"""p3_observation_dashboard.py — P3 Relationship-Aware Orchestration telemetry.

Aggregates the `relationship_orchestration_v1` block across the live
`mirror_chat_retrieval_receipts` collection and produces both a JSON
metrics payload and a human-readable markdown report.

Strictly read-only. Never writes. Never participates in the live
response path.

Usage:
    # Snapshot last 7 days, write report
    python tools/p3_observation_dashboard.py --window-days 7

    # Custom window, json only
    python tools/p3_observation_dashboard.py --window-days 3 --format json

    # Write markdown to a specific path
    python tools/p3_observation_dashboard.py --window-days 7 --markdown-out /app/backend/audit_reports/P3_OBSERVATION_REPORT.md
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # type: ignore
load_dotenv(BACKEND_DIR / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore

RECEIPTS = "mirror_chat_retrieval_receipts"

# Readiness criteria for exiting shadow mode on the P3 orchestration
# plan (i.e. surfacing lens_priority_after + framing_hint to the live
# response). All must be satisfied.
READINESS_CRITERIA = {
    "min_receipts_in_window":        500,
    "min_p3_coverage_pct":           95.0,   # % of receipts with the P3 block
    "min_spouse_receipts":            20,
    "min_forum_member_receipts":      20,
    "min_cofounder_receipts":         10,
    "min_child_receipts":             10,
    "min_active_member_id_util_pct":  60.0,  # of forum_member, % with active_member_id bound
    "min_target_resolution_pct":      80.0,  # of non-self buckets, % with target_resolved
    "max_reorder_rate_pct":           80.0,  # sanity: if 100% reorder, modulations are too aggressive
    "min_reorder_rate_pct_non_self":  60.0,  # of non-self buckets, % that actually re-ranked
    "regression_top1_floor_pct":      95.0,  # intent_router_v2 baseline must stay ≥ this
    "regression_routing_pass_floor_pct": 100.0,
}


async def fetch_receipts(db, window_days: int) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    cutoff_iso = cutoff.isoformat()
    # `computed_at` is an ISO string in our receipts.
    cursor = db[RECEIPTS].find(
        {"computed_at": {"$gte": cutoff_iso}},
        {
            "_id": 0,
            "computed_at": 1,
            "relationship_orchestration_v1": 1,
            "relationship_resolution": 1,
            "frame_source": 1,
            "intent_envelope": 1,
            "target_resolved": 1,
            "target_resolution_status": 1,
            "forum_topology_resolution": 1,
            "stage1_bucket": 1,
            "cutover_decision": 1,
            "user_id": 1,
        }
    )
    return await cursor.to_list(None)


def aggregate(receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(receipts)
    with_p3 = [r for r in receipts if isinstance(r.get("relationship_orchestration_v1"), dict)
               and r["relationship_orchestration_v1"].get("computed")]
    n_p3 = len(with_p3)

    bucket_counts: Counter = Counter()
    bucket_reordered: Counter = Counter()
    bucket_target_bound: Counter = Counter()
    bucket_active_member_bound: Counter = Counter()
    role_distribution: Counter = Counter()
    framing_hint_distribution: Counter = Counter()
    applied_rules_distribution: Counter = Counter()
    modulation_patterns: Counter = Counter()
    context_mode_distribution: Counter = Counter()

    # For modulation calibration: track top-of-stack lens after re-rank
    top_lens_after_per_bucket: Dict[str, Counter] = defaultdict(Counter)
    # And rank-position delta for each lens across all reorderings
    rank_delta_per_lens_per_bucket: Dict[str, Dict[str, List[int]]] = defaultdict(
        lambda: defaultdict(list)
    )

    target_resolution_attempts = 0
    target_resolution_success = 0

    forum_topology_supplied = 0
    forum_topology_with_active_member = 0

    stage1_buckets_seen: Counter = Counter()  # for sanity (cutover decision)
    cutover_enabled_count = 0

    for r in with_p3:
        ro = r["relationship_orchestration_v1"]
        bucket = ro.get("rule_bucket") or "self"
        bucket_counts[bucket] += 1
        if ro.get("reordered"):
            bucket_reordered[bucket] += 1
        if ro.get("target_resolved"):
            bucket_target_bound[bucket] += 1
        if ro.get("active_member_id"):
            bucket_active_member_bound[bucket] += 1

        role = ro.get("role_resolved") or "_none_"
        role_distribution[role] += 1
        framing_hint_distribution[ro.get("framing_hint") or "_none_"] += 1

        for rule in ro.get("applied_rules") or []:
            # Trim role-suffix variants so the count is rule-class only.
            applied_rules_distribution[rule.split(":", 2)[0] if False else rule] += 1

        # Modulation pattern = signature of which lenses had >0 delta,
        # sorted alphabetically. Compresses noise.
        mod = ro.get("lens_weight_modulation") or {}
        sig = "+".join(sorted(k for k, v in mod.items() if v and v > 0))
        modulation_patterns[sig or "_none_"] += 1

        mode = ro.get("context_mode") or "_none_"
        context_mode_distribution[mode] += 1

        # Top-of-stack after re-rank
        after = ro.get("lens_priority_after") or []
        if after:
            top_lens_after_per_bucket[bucket][after[0]] += 1

        # Rank delta per lens
        before = ro.get("lens_priority_before") or []
        if before and after and len(before) == len(after):
            before_idx = {l: i for i, l in enumerate(before)}
            for new_i, lens in enumerate(after):
                old_i = before_idx.get(lens)
                if old_i is not None:
                    rank_delta_per_lens_per_bucket[bucket][lens].append(old_i - new_i)

        # Target resolution counting (only meaningful for non-self buckets)
        if bucket != "self":
            target_resolution_attempts += 1
            if ro.get("target_resolved"):
                target_resolution_success += 1

        if bucket == "forum_member":
            forum_topology_supplied += 1
            if ro.get("active_member_id"):
                forum_topology_with_active_member += 1

        # Stage 1 telemetry sanity
        sb = r.get("stage1_bucket")
        if isinstance(sb, int):
            stage1_buckets_seen[sb // 10 * 10] += 1   # decile buckets
        cd = r.get("cutover_decision") or {}
        if cd.get("enabled"):
            cutover_enabled_count += 1

    # Compute rank-delta means per bucket (positive = lens moved up)
    rank_delta_means: Dict[str, Dict[str, float]] = {}
    for bucket, lens_map in rank_delta_per_lens_per_bucket.items():
        rank_delta_means[bucket] = {
            lens: round(sum(deltas) / len(deltas), 3)
            for lens, deltas in lens_map.items() if deltas
        }

    # Per-bucket reorder rate
    reorder_rate_pct: Dict[str, float] = {}
    for bucket, total in bucket_counts.items():
        reorder_rate_pct[bucket] = round(100.0 * bucket_reordered[bucket] / max(total, 1), 1)

    overall_reorder_rate_pct = (
        round(100.0 * sum(bucket_reordered.values()) / max(n_p3, 1), 1)
    )

    # Non-self reorder rate (more meaningful — self never reorders)
    non_self_total = sum(v for k, v in bucket_counts.items() if k != "self")
    non_self_reordered = sum(v for k, v in bucket_reordered.items() if k != "self")
    non_self_reorder_rate_pct = (
        round(100.0 * non_self_reordered / max(non_self_total, 1), 1)
    )

    return {
        "schema": "p3_observation_v1",
        "totals": {
            "receipts_in_window":  n,
            "receipts_with_p3":    n_p3,
            "p3_coverage_pct":     round(100.0 * n_p3 / max(n, 1), 1),
        },
        "bucket_counts":               dict(bucket_counts),
        "bucket_reorder_rate_pct":     reorder_rate_pct,
        "bucket_target_bound":         dict(bucket_target_bound),
        "bucket_active_member_bound":  dict(bucket_active_member_bound),
        "overall_reorder_rate_pct":    overall_reorder_rate_pct,
        "non_self_reorder_rate_pct":   non_self_reorder_rate_pct,
        "role_distribution":           dict(role_distribution),
        "framing_hint_distribution":   dict(framing_hint_distribution),
        "applied_rules_distribution":  dict(applied_rules_distribution),
        "modulation_patterns":         dict(modulation_patterns),
        "context_mode_distribution":   dict(context_mode_distribution),
        "top_lens_after_per_bucket":   {b: dict(c) for b, c in top_lens_after_per_bucket.items()},
        "rank_delta_means":            rank_delta_means,
        "target_resolution": {
            "non_self_attempts":  target_resolution_attempts,
            "non_self_success":   target_resolution_success,
            "success_pct":        round(100.0 * target_resolution_success
                                        / max(target_resolution_attempts, 1), 1),
        },
        "forum_topology": {
            "forum_member_bucket_count":      forum_topology_supplied,
            "active_member_id_bound_count":   forum_topology_with_active_member,
            "active_member_id_util_pct":      round(
                100.0 * forum_topology_with_active_member
                / max(forum_topology_supplied, 1), 1),
        },
        "stage1_telemetry": {
            "stage1_bucket_deciles_seen":  dict(stage1_buckets_seen),
            "cutover_enabled_count":       cutover_enabled_count,
            "cutover_enabled_pct":         round(100.0 * cutover_enabled_count
                                                 / max(n, 1), 1),
        },
    }


def evaluate_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Compare metrics to the readiness floors and return pass/fail per criterion."""
    c = READINESS_CRITERIA
    t = metrics["totals"]
    bc = metrics["bucket_counts"]

    results = {
        "min_receipts_in_window": {
            "required": c["min_receipts_in_window"],
            "actual":   t["receipts_in_window"],
            "pass":     t["receipts_in_window"] >= c["min_receipts_in_window"],
        },
        "min_p3_coverage_pct": {
            "required": c["min_p3_coverage_pct"],
            "actual":   t["p3_coverage_pct"],
            "pass":     t["p3_coverage_pct"] >= c["min_p3_coverage_pct"],
        },
        "min_spouse_receipts": {
            "required": c["min_spouse_receipts"],
            "actual":   bc.get("spouse", 0),
            "pass":     bc.get("spouse", 0) >= c["min_spouse_receipts"],
        },
        "min_forum_member_receipts": {
            "required": c["min_forum_member_receipts"],
            "actual":   bc.get("forum_member", 0),
            "pass":     bc.get("forum_member", 0) >= c["min_forum_member_receipts"],
        },
        "min_cofounder_receipts": {
            "required": c["min_cofounder_receipts"],
            "actual":   bc.get("cofounder", 0),
            "pass":     bc.get("cofounder", 0) >= c["min_cofounder_receipts"],
        },
        "min_child_receipts": {
            "required": c["min_child_receipts"],
            "actual":   bc.get("child", 0),
            "pass":     bc.get("child", 0) >= c["min_child_receipts"],
        },
        "min_active_member_id_util_pct": {
            "required": c["min_active_member_id_util_pct"],
            "actual":   metrics["forum_topology"]["active_member_id_util_pct"],
            "pass":     metrics["forum_topology"]["active_member_id_util_pct"]
                        >= c["min_active_member_id_util_pct"],
        },
        "min_target_resolution_pct": {
            "required": c["min_target_resolution_pct"],
            "actual":   metrics["target_resolution"]["success_pct"],
            "pass":     metrics["target_resolution"]["success_pct"]
                        >= c["min_target_resolution_pct"],
        },
        "non_self_reorder_rate_pct": {
            "required_min": c["min_reorder_rate_pct_non_self"],
            "required_max": c["max_reorder_rate_pct"],
            "actual":   metrics["non_self_reorder_rate_pct"],
            "pass":     (c["min_reorder_rate_pct_non_self"]
                         <= metrics["non_self_reorder_rate_pct"]
                         <= c["max_reorder_rate_pct"]),
        },
    }
    results["overall_pass"] = all(v.get("pass") for v in results.values())
    return results


def recommend_calibration(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Heuristic calibration suggestions based on aggregated metrics.

    All recommendations are *receipt-only*; nothing here mutates state.
    """
    recs: List[Dict[str, str]] = []
    bc = metrics["bucket_counts"]
    rr = metrics["bucket_reorder_rate_pct"]
    delta_means = metrics["rank_delta_means"]

    # Bucket-volume signals
    if bc.get("spouse", 0) < READINESS_CRITERIA["min_spouse_receipts"]:
        recs.append({
            "severity": "info",
            "rule":     "spouse_underrepresented",
            "msg": (f"Spouse bucket has {bc.get('spouse', 0)} receipts "
                    f"(< {READINESS_CRITERIA['min_spouse_receipts']}). Continue "
                    f"observation; do not adjust spouse modulations yet."),
        })
    if bc.get("forum_member", 0) < READINESS_CRITERIA["min_forum_member_receipts"]:
        recs.append({
            "severity": "info",
            "rule":     "forum_member_underrepresented",
            "msg": (f"forum_member bucket has {bc.get('forum_member', 0)} receipts "
                    f"(< {READINESS_CRITERIA['min_forum_member_receipts']}). "
                    f"Defer modulation tuning."),
        })
    if bc.get("cofounder", 0) < READINESS_CRITERIA["min_cofounder_receipts"]:
        recs.append({
            "severity": "info",
            "rule":     "cofounder_underrepresented",
            "msg": (f"cofounder bucket has {bc.get('cofounder', 0)} receipts "
                    f"(< {READINESS_CRITERIA['min_cofounder_receipts']}). "
                    f"Defer modulation tuning."),
        })
    if bc.get("child", 0) < READINESS_CRITERIA["min_child_receipts"]:
        recs.append({
            "severity": "info",
            "rule":     "child_underrepresented",
            "msg": (f"child bucket has {bc.get('child', 0)} receipts "
                    f"(< {READINESS_CRITERIA['min_child_receipts']}). "
                    f"Defer modulation tuning."),
        })

    # Reorder-rate signals (only meaningful with adequate volume)
    for bucket in ("spouse", "child", "cofounder", "forum_member"):
        if bc.get(bucket, 0) >= 20:
            rate = rr.get(bucket, 0.0)
            if rate >= 95.0:
                recs.append({
                    "severity": "warn",
                    "rule":     f"{bucket}_modulations_possibly_too_aggressive",
                    "msg": (f"{bucket} re-orders the lens stack on {rate}% of "
                            f"receipts. Consider reducing the largest lens "
                            f"modulation in this bucket by 0.05–0.10 and "
                            f"re-running the regression suite."),
                })
            elif rate < 30.0:
                recs.append({
                    "severity": "warn",
                    "rule":     f"{bucket}_modulations_possibly_too_low",
                    "msg": (f"{bucket} only re-orders the lens stack on {rate}% "
                            f"of receipts. Consider increasing the dominant "
                            f"lens modulation in this bucket by 0.05–0.10."),
                })

    # Rank-delta per-lens signals (which lenses are moving how much)
    for bucket, lens_map in delta_means.items():
        if bc.get(bucket, 0) < 20:
            continue
        for lens, mean_delta in lens_map.items():
            if mean_delta >= 3.0:
                recs.append({
                    "severity": "warn",
                    "rule":     f"{bucket}.{lens}_rank_jump_high",
                    "msg": (f"{bucket}: lens `{lens}` jumps an average of "
                            f"{mean_delta:+.2f} positions. Modulation may "
                            f"be too large."),
                })
            if mean_delta <= -2.0:
                recs.append({
                    "severity": "warn",
                    "rule":     f"{bucket}.{lens}_demoted_unexpectedly",
                    "msg": (f"{bucket}: lens `{lens}` is being demoted by "
                            f"{mean_delta:+.2f} positions on average — "
                            f"check whether its baseline weight is too low "
                            f"for this bucket."),
                })

    # Target resolution health
    tr = metrics["target_resolution"]
    if tr["non_self_attempts"] >= 30 and tr["success_pct"] < 80.0:
        recs.append({
            "severity": "warn",
            "rule":     "target_resolution_below_threshold",
            "msg": (f"Target resolution rate on non-self buckets is "
                    f"{tr['success_pct']}% — investigate relationship_router_v2 "
                    f"path or saved_people coverage."),
        })

    # Forum active_member utilization
    ft = metrics["forum_topology"]
    if ft["forum_member_bucket_count"] >= 30 and ft["active_member_id_util_pct"] < 60.0:
        recs.append({
            "severity": "warn",
            "rule":     "active_member_id_util_low",
            "msg": (f"Only {ft['active_member_id_util_pct']}% of forum_member "
                    f"buckets carry an active_member_id. Check P4 plumbing "
                    f"at the API edge."),
        })

    if not recs:
        recs.append({
            "severity": "info",
            "rule":     "no_action_required",
            "msg":      "Insufficient signal to recommend calibration changes; "
                       "continue observing.",
        })
    return recs


def render_markdown(metrics: Dict[str, Any],
                    readiness: Dict[str, Any],
                    recs: List[Dict[str, str]],
                    window_days: int) -> str:
    lines: List[str] = []
    lines.append(f"# P3 Observation Report ({window_days}-day window)")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("**Mode:** SHADOW (P3 plan recorded; live response unchanged).")
    lines.append("")
    lines.append("## Volume")
    lines.append("")
    lines.append(f"* Receipts in window: **{metrics['totals']['receipts_in_window']}**")
    lines.append(f"* Receipts carrying P3 block: **{metrics['totals']['receipts_with_p3']}** "
                 f"({metrics['totals']['p3_coverage_pct']}%)")
    lines.append("")
    lines.append("## Bucket distribution")
    lines.append("")
    lines.append("| Bucket | Count | Re-order rate | Target bound | Active-member bound |")
    lines.append("|---|---:|---:|---:|---:|")
    for bucket in ("spouse", "child", "cofounder", "forum_member", "self"):
        n_b = metrics["bucket_counts"].get(bucket, 0)
        rr = metrics["bucket_reorder_rate_pct"].get(bucket, 0.0)
        tb = metrics["bucket_target_bound"].get(bucket, 0)
        ab = metrics["bucket_active_member_bound"].get(bucket, 0)
        lines.append(f"| {bucket} | {n_b} | {rr}% | {tb} | {ab} |")
    lines.append("")
    lines.append(f"**Overall re-order rate:** {metrics['overall_reorder_rate_pct']}%")
    lines.append(f"**Non-self re-order rate:** {metrics['non_self_reorder_rate_pct']}%")
    lines.append("")
    lines.append("## Role distribution")
    lines.append("")
    for role, count in sorted(metrics["role_distribution"].items(), key=lambda kv: -kv[1]):
        lines.append(f"* `{role}` — {count}")
    lines.append("")
    lines.append("## Modulation patterns (signature of lenses modulated)")
    lines.append("")
    for sig, count in sorted(metrics["modulation_patterns"].items(), key=lambda kv: -kv[1]):
        lines.append(f"* `{sig}` — {count}")
    lines.append("")
    lines.append("## Target resolution")
    lines.append("")
    tr = metrics["target_resolution"]
    lines.append(f"* Non-self attempts: **{tr['non_self_attempts']}**")
    lines.append(f"* Successful target binds: **{tr['non_self_success']}** ({tr['success_pct']}%)")
    lines.append("")
    lines.append("## Forum-topology utilization")
    lines.append("")
    ft = metrics["forum_topology"]
    lines.append(f"* forum_member buckets: **{ft['forum_member_bucket_count']}**")
    lines.append(f"* with active_member_id bound: **{ft['active_member_id_bound_count']}** "
                 f"({ft['active_member_id_util_pct']}%)")
    lines.append("")
    lines.append("## Top lens after re-rank (per bucket)")
    lines.append("")
    for bucket in ("spouse", "child", "cofounder", "forum_member", "self"):
        top = metrics["top_lens_after_per_bucket"].get(bucket) or {}
        if not top:
            continue
        sig = ", ".join(f"`{k}`: {v}" for k, v in sorted(top.items(), key=lambda kv: -kv[1])[:5])
        lines.append(f"* **{bucket}** — {sig}")
    lines.append("")
    lines.append("## Mean rank-delta per lens (positive = promoted)")
    lines.append("")
    for bucket, lens_map in metrics["rank_delta_means"].items():
        if not lens_map:
            continue
        lines.append(f"* **{bucket}** — " +
                     ", ".join(f"`{lens}`: {d:+.2f}" for lens, d in
                               sorted(lens_map.items(), key=lambda kv: -kv[1])[:6]))
    lines.append("")
    lines.append("## Stage 1 telemetry sanity")
    lines.append("")
    st = metrics["stage1_telemetry"]
    lines.append(f"* `cutover_enabled=True` count: **{st['cutover_enabled_count']}** "
                 f"({st['cutover_enabled_pct']}% of receipts in window)")
    lines.append(f"  — must be ≤ rollout-percent (currently 10).")
    lines.append("")
    lines.append("## Calibration recommendations")
    lines.append("")
    for r in recs:
        prefix = {"warn": "⚠️", "info": "ℹ️", "error": "❌"}.get(r["severity"], "•")
        lines.append(f"* {prefix} **{r['rule']}** — {r['msg']}")
    lines.append("")
    lines.append("## Readiness criteria for exiting shadow mode")
    lines.append("")
    lines.append(f"| Criterion | Required | Actual | Pass |")
    lines.append("|---|---:|---:|:---:|")
    for k, v in readiness.items():
        if k == "overall_pass":
            continue
        req = v.get("required") if "required" in v else f"{v.get('required_min')}..{v.get('required_max')}"
        actual = v.get("actual")
        ok = "✅" if v.get("pass") else "❌"
        lines.append(f"| `{k}` | {req} | {actual} | {ok} |")
    lines.append("")
    overall = "✅ READY" if readiness["overall_pass"] else "❌ NOT READY"
    lines.append(f"**Overall:** {overall}")
    lines.append("")
    return "\n".join(lines)


async def main_async(args: argparse.Namespace) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL or DB_NAME not set", file=sys.stderr)
        return 2

    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]
    receipts = await fetch_receipts(db, args.window_days)
    metrics = aggregate(receipts)
    readiness = evaluate_readiness(metrics)
    recs = recommend_calibration(metrics)

    output = {
        "window_days":  args.window_days,
        "metrics":      metrics,
        "readiness":    readiness,
        "recommendations": recs,
    }

    if args.format == "json":
        print(json.dumps(output, indent=2, default=str))
    else:
        md = render_markdown(metrics, readiness, recs, args.window_days)
        if args.markdown_out:
            Path(args.markdown_out).write_text(md, encoding="utf-8")
            print(f"Markdown written: {args.markdown_out}")
        else:
            print(md)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(output, indent=2, default=str), encoding="utf-8"
        )
        print(f"JSON written: {args.json_out}", file=sys.stderr)

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="P3 observation dashboard")
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--markdown-out", type=str, default=None)
    parser.add_argument("--json-out",     type=str, default=None)
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
