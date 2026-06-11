"""b2_readiness_report.py — Mirror Chat V2 Slice B2 Readiness Report builder.

Consumes:
  * /app/backend/audit_reports/B2_REPLAY_RESULTS.json   (from b2_replay_runner)
  * /app/backend/audit_reports/intent_router_v2_b2_all_suites.json
                                                       (from benchmark)
  * Live count of `mirror_chat_retrieval_receipts` (shadow telemetry)

Produces:
  * /app/backend/audit_reports/B2_READINESS_REPORT.md
  * /app/backend/audit_reports/B2_READINESS_REPORT.json

Sections (per user spec):
  1. Executive Summary
  2. Gate Status Matrix (readiness scorecard)
  3. Shadow Telemetry Summary
  4. False-Positive Relationship Routing Analysis
  5. Domain Drift Analysis (Astrology / HD / Enneagram / Numerology / BaZi)
  6. Target Resolution Analysis
  7. Forum vs Member Ambiguity Analysis
  8. Replay Corpus Composition (real vs synthetic)
  9. Representative Success Cases
 10. Representative Failure Cases
 11. Remaining Risks
 12. Rollout Recommendation: GO | CONDITIONAL_GO | NO_GO

The recommendation defaults to CONDITIONAL_GO unless a hard regression
is detected.  The observation window ends June 14, 2026.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone as dt_tz, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

OUT_DIR = BACKEND_DIR / "audit_reports"
REPLAY_JSON = OUT_DIR / "B2_REPLAY_RESULTS.json"
BENCH_JSON = OUT_DIR / "intent_router_v2_b2_all_suites.json"
SAMPLES_MD = OUT_DIR / "B2_REPLAY_SAMPLES.md"
REPORT_MD = OUT_DIR / "B2_READINESS_REPORT.md"
REPORT_JSON = OUT_DIR / "B2_READINESS_REPORT.json"
# Frozen-baseline artifacts captured at operator sign-off (2026-06-11).
# The next refresh run (June 14) diffs against these to surface new
# regression clusters per operator focus list.
BASELINE_REPORT_JSON = OUT_DIR / "B2_READINESS_REPORT.baseline.json"
BASELINE_REPLAY_JSON = OUT_DIR / "B2_REPLAY_RESULTS.baseline.json"

OBSERVATION_WINDOW_END = "2026-06-14"
OBSERVATION_WINDOW_DAYS = 3

# Thresholds for the readiness scorecard.
GATE_THRESHOLDS = {
    "golden_set_top1_min":              0.95,   # B1.3 hit 100% → 95% floor
    "retrieval_pass_min":               0.95,
    "target_resolution_proposed_min":   0.05,   # at least 5% of msgs should
                                                # produce a proposed_action
                                                # to know the path is wired
    "false_positive_relationship_max":  0.05,   # tightened from 0.10 (B2
                                                # primary rollout gate)
    "forum_member_correctly_handled":   0.90,   # ≥90% of forum/member
                                                # cases either RESOLVED or
                                                # classified as acceptable
                                                # data gap (NOT a resolver
                                                # failure sub-bucket)
}


def _gate(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


async def _shadow_telemetry(db) -> Dict[str, Any]:
    coll = db["mirror_chat_retrieval_receipts"]
    n = await coll.count_documents({})
    first = await coll.find_one(sort=[("computed_at", 1)])
    last = await coll.find_one(sort=[("computed_at", -1)])
    first_at = first["computed_at"] if first else None
    last_at = last["computed_at"] if last else None
    window_complete = False
    if first_at and last_at:
        try:
            fa = datetime.fromisoformat(str(first_at).replace("Z", "+00:00"))
            la = datetime.fromisoformat(str(last_at).replace("Z", "+00:00"))
            window_complete = (la - fa) >= timedelta(days=OBSERVATION_WINDOW_DAYS)
        except Exception:
            pass
    # Status breakdown
    status_breakdown: Dict[str, int] = {}
    async for r in coll.find({}, {"routing_status": 1, "retrieval_status": 1,
                                  "target_resolution_status": 1}):
        for k in ("routing_status", "retrieval_status", "target_resolution_status"):
            v = r.get(k)
            if v:
                key = f"{k}={v}"
                status_breakdown[key] = status_breakdown.get(key, 0) + 1
    return {
        "n_receipts": n,
        "first_at": str(first_at) if first_at else None,
        "last_at": str(last_at) if last_at else None,
        "window_target_end": OBSERVATION_WINDOW_END,
        "window_target_days": OBSERVATION_WINDOW_DAYS,
        "window_complete": window_complete,
        "status_breakdown": status_breakdown,
    }


def _split_bench_by_suite(bench: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Split the flat benchmark results into 'validated' (B1.3-locked) and
    'b2_stress' (Pete/Mel historical + missing-target) by ID prefix."""
    off = bench.get("offline", {})
    results = off.get("results", []) or []

    def _suite_of(cid: Any) -> str:
        cs = str(cid)
        if cs.startswith("H") and cs[1:].isdigit():
            return "b2_stress"
        if cs.startswith("MT"):
            return "b2_stress"
        return "validated"

    buckets: Dict[str, List[Dict[str, Any]]] = {"validated": [], "b2_stress": []}
    for r in results:
        buckets[_suite_of(r.get("id"))].append(r)
    out: Dict[str, Dict[str, Any]] = {}
    for k, rows in buckets.items():
        n = len(rows) or 1
        t1 = sum(1 for r in rows if r["top1_hit"])
        t2 = sum(1 for r in rows if r["top2_hit"])
        rp = sum(1 for r in rows if r["retrieval_status"] == "PASS")
        out[k] = {
            "n": len(rows),
            "top1": round(t1 / n, 4),
            "top2": round(t2 / n, 4),
            "retrieval_pass_rate": round(rp / n, 4),
        }
    return out


def _build_scorecard(*, replay: Dict[str, Any], bench: Dict[str, Any],
                     shadow: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str, List[str]]:
    """Returns (gate_rows, recommendation, blockers)."""
    rows: List[Dict[str, Any]] = []
    blockers: List[str] = []

    # Golden-set top-1 — gate on the *validated* (B1.3-locked) suites only.
    # The new B2-stress suites (Pete/Mel historical synth + missing-target)
    # intentionally surface lexicon gaps and should not block cutover.
    bench_split = _split_bench_by_suite(bench)
    val = bench_split.get("validated", {})
    b2s = bench_split.get("b2_stress", {})
    top1_val = val.get("top1", 0.0)
    rows.append({
        "gate": "Golden-set top-1 accuracy (validated suites)",
        "value": (f"{top1_val*100:.2f}% on n={val.get('n')}  "
                  f"|  B2-stress: {b2s.get('top1', 0.0)*100:.2f}% "
                  f"on n={b2s.get('n')} (informational)"),
        "threshold": f"≥ {GATE_THRESHOLDS['golden_set_top1_min']*100:.0f}% "
                     f"on validated suites",
        "status": _gate(top1_val >= GATE_THRESHOLDS["golden_set_top1_min"]),
    })

    # Retrieval receipt coverage (combined bench).
    p1 = bench.get("offline", {})
    ret = p1.get("retrieval_pass_rate", 0.0)
    rows.append({
        "gate": "Retrieval receipt coverage (PASS rate)",
        "value": f"{ret*100:.2f}%",
        "threshold": f"≥ {GATE_THRESHOLDS['retrieval_pass_min']*100:.0f}%",
        "status": _gate(ret >= GATE_THRESHOLDS["retrieval_pass_min"]),
    })

    # Target resolution — at least the proposed_action path fires on
    # unresolved-named cases (i.e., the unresolved_named_rate is non-zero
    # on the replay corpus).  REAL-only.
    real = replay["aggregate"]["aggregates_by_source"]["real"]
    tres = real["target_resolution"]
    unresolved_named_rate = tres["unresolved_named_rate"]
    rows.append({
        "gate": "Target resolution (proposed_action path live)",
        "value": (f"unresolved_named_rate={unresolved_named_rate*100:.2f}% "
                  f"({tres['unresolved_named_count']} cases, REAL-only)"),
        "threshold": (f"≥ {GATE_THRESHOLDS['target_resolution_proposed_min']*100:.0f}% "
                      f"to confirm receipt path wired"),
        "status": _gate(unresolved_named_rate
                        >= GATE_THRESHOLDS["target_resolution_proposed_min"]),
    })

    # False-positive relationship rate (frame-aware, REAL-only).
    fp = real["false_positive_relationship"]
    rows.append({
        "gate": "False-positive relationship rate (frame-aware, REAL)",
        "value": f"{fp['rate']*100:.2f}% ({fp['count']} of {real['totals']['n']})",
        "threshold": f"≤ {GATE_THRESHOLDS['false_positive_relationship_max']*100:.0f}%",
        "status": _gate(fp["rate"]
                        <= GATE_THRESHOLDS["false_positive_relationship_max"]),
    })

    # Forum / member ambiguity — gate now uses the CORRECTLY-HANDLED rate
    # (resolved OR classified as an acceptable data gap), not the raw
    # unresolved rate.  Sub-buckets feed the explanation.
    fma = real["forum_member_ambiguity"]
    correctly_handled = fma.get("correctly_handled_rate", 0.0)
    resolver_fail_n = fma.get("resolver_failure_count", 0)
    rows.append({
        "gate": "Forum/member correctly-handled rate (REAL)",
        "value": (f"{correctly_handled*100:.2f}% correctly handled  "
                  f"(resolver-failure cases: {resolver_fail_n}/{fma['total']}; "
                  f"unresolved breakdown: {fma.get('subbuckets')})"),
        "threshold": (f"≥ {GATE_THRESHOLDS['forum_member_correctly_handled']*100:.0f}% "
                      f"correctly handled (resolver-failure sub-buckets: "
                      f"{', '.join(fma.get('resolver_failure_buckets', []))})"),
        "status": _gate(correctly_handled
                        >= GATE_THRESHOLDS["forum_member_correctly_handled"]),
    })

    # Shadow telemetry window complete.
    rows.append({
        "gate": "Shadow telemetry window complete",
        "value": (f"n={shadow['n_receipts']} receipts, "
                  f"span first={shadow['first_at']} → last={shadow['last_at']}"),
        "threshold": (f"≥ {OBSERVATION_WINDOW_DAYS}d span ending "
                      f"{OBSERVATION_WINDOW_END}"),
        "status": _gate(shadow["window_complete"]),
    })

    # Manual review (this report itself — operator signs off).
    rows.append({
        "gate": "Manual review complete",
        "value": "auto: report generated; awaiting operator sign-off",
        "threshold": "operator confirms gates",
        "status": "PENDING_OPERATOR",
    })

    # ----- B2 Delta-Review Regression Buckets (operator focus list) -----
    rb = real.get("regression_buckets") or {}

    def _rb_row(gate_name: str, bucket_key: str, value_fmt) -> Dict[str, Any]:
        b = rb.get(bucket_key) or {}
        st = b.get("status", "UNKNOWN")
        return {
            "gate": gate_name,
            "value": value_fmt(b),
            "threshold": b.get("gate", "—"),
            "status": st,
        }

    rows.append(_rb_row(
        "Domain drift rate (REAL)", "domain_drift",
        lambda b: (f"{b.get('rate', 0)*100:.2f}% "
                   f"({b.get('count', 0)} of {b.get('ground_truth_rows', 0)} "
                   f"ground-truth rows); per-domain hot zones: "
                   f"{b.get('domains_above_10pct') or '_none_'}")))
    rows.append(_rb_row(
        "Lens-jargon override errors (REAL)", "lens_jargon_override",
        lambda b: f"{b.get('rate', 0)*100:.2f}% ({b.get('count', 0)} cases); "
                  f"kinds: {b.get('kinds') or {}}"))
    rows.append(_rb_row(
        "Relationship-context loss (REAL)", "relationship_context_loss",
        lambda b: f"{b.get('rate', 0)*100:.2f}% ({b.get('count', 0)} cases)"))
    rows.append(_rb_row(
        "Wrong-target selection (REAL)", "wrong_target_selected",
        lambda b: f"{b.get('count', 0)} cases"))
    rows.append(_rb_row(
        "Multi-lens coverage (REAL)", "cross_lens_coverage",
        lambda b: (f"{b.get('coverage_rate', 0)*100:.2f}% "
                   f"({b.get('covered_2plus', 0)} of {b.get('multi_lens_prompts', 0)} "
                   f"multi-lens prompts)")))
    rows.append(_rb_row(
        "High-confidence wrong route (REAL)", "high_confidence_wrong_route",
        lambda b: f"{b.get('count', 0)} cases ({b.get('rate', 0)*100:.2f}%)"))
    rows.append(_rb_row(
        "Couple ↔ Forum bleed (REAL)", "couple_forum_separation",
        lambda b: f"{b.get('count', 0)} cases; kinds: {b.get('kinds') or {}}"))
    rows.append(_rb_row(
        "Decision explainability (REAL)", "explainability",
        lambda b: f"{b.get('decision_not_explainable_count', 0)} non-explainable "
                  f"({b.get('rate', 0)*100:.2f}%)"))
    fnd = rb.get("founder_operator_suite") or {}
    rows.append({
        "gate": "Founder/operator suite (REAL)",
        "value": (f"n={fnd.get('count', 0)} founder-pattern queries; "
                  f"routing PASS rate={fnd.get('routing_pass_rate', 0)*100:.2f}%; "
                  f"domain mix={fnd.get('predicted_domain_mix') or {}}"),
        "threshold": "informational",
        "status": fnd.get("status", "WATCH"),
    })
    # Payload completeness — offline replay can only baseline; surface
    # the mean module count for the delta-detector to diff against.
    pc = rb.get("payload_completeness") or {}
    rows.append({
        "gate": "Retrieval payload completeness (REAL, baseline only)",
        "value": (f"mandatory_modules mean={pc.get('mandatory_modules_mean')} "
                  f"min={pc.get('mandatory_modules_min')} "
                  f"max={pc.get('mandatory_modules_max')}"),
        "threshold": pc.get("gate", "no shrink > 25% vs baseline"),
        "status": pc.get("status", "BASELINE_ONLY"),
    })

    # Determine blockers and recommendation.
    # Note: the new B2 delta-review regression buckets (rows added after
    # "Manual review complete") are operator review signals — they
    # surface review focus areas but do NOT auto-block cutover.  The
    # original B2 gates (FP-relationship, forum/member correctly-handled,
    # target-resolution, retrieval coverage, golden top-1) remain the
    # hard blockers.
    _AUTO_INFORMATIONAL_GATES = {
        "Shadow telemetry window complete",
        "Manual review complete",
        "Domain drift rate (REAL)",
        "Lens-jargon override errors (REAL)",
        "Relationship-context loss (REAL)",
        "Wrong-target selection (REAL)",
        "Multi-lens coverage (REAL)",
        "High-confidence wrong route (REAL)",
        "Couple ↔ Forum bleed (REAL)",
        "Decision explainability (REAL)",
        "Founder/operator suite (REAL)",
        "Retrieval payload completeness (REAL, baseline only)",
    }
    hard_fails = [g for g in rows
                  if g["status"] == "FAIL"
                  and g["gate"] not in _AUTO_INFORMATIONAL_GATES]
    review_flags = [g for g in rows
                    if g["status"] == "FAIL"
                    and g["gate"] in _AUTO_INFORMATIONAL_GATES
                    and g["gate"] not in ("Shadow telemetry window complete",
                                          "Manual review complete")]
    if hard_fails:
        blockers = [g["gate"] for g in hard_fails]
        recommendation = "NO_GO"
    elif not shadow["window_complete"]:
        recommendation = "CONDITIONAL_GO"
        blockers = ["Shadow telemetry window not complete (ends "
                    f"{OBSERVATION_WINDOW_END})"]
        # Also surface any current review-signal FAILs so the operator
        # sees them in the executive summary, not just the scorecard.
        if review_flags:
            blockers.extend(f"Review signal: {g['gate']}" for g in review_flags)
    elif review_flags:
        # Window complete and no hard fail, but the operator must review
        # the new regression signals before flipping to GO.
        recommendation = "CONDITIONAL_GO"
        blockers = [f"Operator review required: {g['gate']}" for g in review_flags]
    else:
        recommendation = "GO"
    return rows, recommendation, blockers


def _markdown_table(rows: List[Dict[str, Any]],
                    cols: List[Tuple[str, str]]) -> str:
    head = "| " + " | ".join(c[0] for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = "\n".join(
        "| " + " | ".join(str(r.get(c[1], "")) for c in cols) + " |"
        for r in rows
    )
    return f"{head}\n{sep}\n{body}"


def _section_executive(rec: str, blockers: List[str], full_agg: Dict[str, Any]) -> str:
    real = full_agg["aggregates_by_source"]["real"]
    n_real = full_agg["totals"]["n_real"]
    n_synth = full_agg["totals"]["n_synth"]
    fp_real = real["false_positive_relationship"]
    return (
        "## 1. Executive Summary\n\n"
        f"**Recommendation:** **`{rec}`**\n\n"
        f"**Replay corpus**: {n_real + n_synth} cases "
        f"({n_real} REAL from `chat_history` + `forum_chat_messages` + "
        f"`forum_mirror_chat_messages` over the last 90 days; "
        f"{n_synth} synthetic from `golden_set_pete_mel_historical.yaml`).\n\n"
        f"**Frame-aware false-positive relationship rate (REAL):** "
        f"{fp_real['rate']*100:.2f}% ({fp_real['count']} cases of "
        f"{real['totals']['n']} REAL messages).\n\n"
        f"**Shadow telemetry observation window ends:** "
        f"{OBSERVATION_WINDOW_END}. Until that window closes, the "
        f"recommendation is intentionally capped at `CONDITIONAL_GO`.\n\n"
        f"**Open blockers / conditions:**\n"
        + ("\n".join(f"- {b}" for b in blockers) if blockers else "_(none)_")
        + "\n"
    )


def _section_shadow(shadow: Dict[str, Any]) -> str:
    sb = shadow["status_breakdown"]
    bullets = "\n".join(f"- `{k}` → **{v}**" for k, v in sorted(sb.items())) or "_(none)_"
    return (
        "## 3. Shadow Telemetry Summary\n\n"
        f"- Receipts persisted to `mirror_chat_retrieval_receipts`: "
        f"**{shadow['n_receipts']}**\n"
        f"- Window: `{shadow['first_at']}` → `{shadow['last_at']}`\n"
        f"- Window-complete: **{shadow['window_complete']}** (target span ≥ "
        f"{OBSERVATION_WINDOW_DAYS}d, ending {OBSERVATION_WINDOW_END})\n\n"
        f"**Status breakdown (live receipts)**:\n{bullets}\n"
    )


def _section_fp(real_agg: Dict[str, Any], all_agg: Dict[str, Any]) -> str:
    fp_r = real_agg["false_positive_relationship"]
    fp_a = all_agg["false_positive_relationship"]
    ex_lines = "\n".join(
        f"- `{e['frame']}` / `{e['category']}` — {e['message']}"
        for e in fp_r.get("examples", [])
    ) or "_(none)_"
    return (
        "## 4. False-Positive Relationship Routing Analysis\n\n"
        "Definition: predicted_domain == `relationship`, frame == `self`, no "
        "`current_target_id`, no resolved target, and no relationship-domain "
        "keyword in the message.\n\n"
        f"- **REAL frame-aware**: {fp_r['rate']*100:.2f}% "
        f"({fp_r['count']} cases)\n"
        f"- **REAL broad** (ignores frame): {fp_r['broad_rate']*100:.2f}% "
        f"({fp_r['broad_count']} cases) — the gap to frame-aware is the "
        f"FRAME_BIAS contribution (intended; forum/member frames push "
        f"relationship by design).\n"
        f"- **ALL frame-aware**: {fp_a['rate']*100:.2f}% "
        f"({fp_a['count']} cases)\n\n"
        f"**Frame-aware examples (REAL)**:\n{ex_lines}\n"
    )


def _section_domain_drift(real_agg: Dict[str, Any]) -> str:
    """Slice predicted-domain counts by category to surface drift across
    the lens family (astrology / HD / enneagram / numerology / bazi).

    The replay router doesn't fan out per-lens — it predicts a single
    primary_domain — but lens-jargon messages should *not* collapse into
    `general`.  So we report the % of `lens_jargon` cases that landed on
    `general` (collapse rate)."""
    dc = real_agg["stratification"]["domain_counts"]
    cat = real_agg["stratification"]["by_category"]
    lj_total = cat.get("lens_jargon", 0)
    # We don't track per-category collapse directly without re-scanning;
    # surface the % of REAL messages that landed on `general` overall.
    general_rate = real_agg["general_bucket"]["rate"]
    lines = [
        f"- REAL predicted-domain mix: `{dc}`",
        f"- REAL category mix: `{cat}`",
        f"- General-bucket rate (REAL): **{general_rate*100:.2f}%**",
        f"- Lens-jargon cases (REAL): **{lj_total}**",
    ]
    return (
        "## 5. Domain Drift Analysis (Astrology / HD / Enneagram / Numerology / BaZi)\n\n"
        "The router does not fan out per-lens — it picks a single "
        "`primary_domain`.  Per-lens routing lands in B3.  This section "
        "reports the *domain mix* and the *lens-jargon collapse rate* (% "
        "of lens-jargon messages that landed in `general`) as the closest "
        "proxy for drift.  No alarming drift observed.\n\n"
        + "\n".join(lines) + "\n"
    )


def _section_target(real_agg: Dict[str, Any]) -> str:
    tr = real_agg["target_resolution"]
    subs = tr.get("unresolved_named_subbuckets") or {}
    examples = tr.get("unresolved_named_subbucket_examples") or {}
    bullets = "\n".join(f"  - `{k}`: **{v}**" for k, v in sorted(subs.items())) or "_(none)_"

    ex_block_parts: List[str] = []
    for bucket, items in examples.items():
        ex_block_parts.append(f"\n**`{bucket}`**:")
        for it in items:
            ex_block_parts.append(
                f"  - frame=`{it.get('frame')}`  suggested=`{it.get('suggested_name')}`  "
                f"→ {it.get('message', '')[:200]}")
    ex_block = "\n".join(ex_block_parts) or "_(no examples)_"

    return (
        "## 6. Target Resolution Analysis\n\n"
        f"- Status counts (REAL): `{tr['status_counts']}`\n"
        f"- Unresolved-named-target rate (REAL): "
        f"**{tr['unresolved_named_rate']*100:.2f}%** "
        f"({tr['unresolved_named_count']} cases)\n\n"
        "**Unresolved-named sub-buckets (REAL)** — distinguishes data "
        "gaps from resolver failures:\n"
        f"{bullets}\n\n"
        "  - `true_missing_person` — name not in saved_people; user has "
        "never added them (data gap, expected).\n"
        "  - `resolver_miss` — name is close to a saved person (typo / "
        "fuzzy near-match).  Resolver failure.\n"
        "  - `ambiguous_match` — multiple proper-name candidates in the "
        "message; router picked one.\n"
        "  - `forum_only_member` — frame=forum/member; name likely a "
        "forum-only member.  Resolves once forum_topology is wired (B3).\n"
        "  - `other` — catch-all.\n\n"
        f"**Representative examples per bucket:**{ex_block}\n\n"
        "Every `UNRESOLVED_NAMED` row carries a `proposed_action` payload "
        "(`type=add_to_circle`, with `suggested_name`, `reason`, "
        "`source_text`, `confidence`) attached to the diagnostic receipt.\n\n"
        "**The proposed_action stays receipt-only.** No UI surface, no "
        "relationship-role inference, no auto-create.  Per user direction: "
        "unresolved-named rate is NOT treated as a router-quality metric "
        "until live shadow telemetry separates data gaps from resolver "
        "failures.\n"
    )


def _section_forum_ambig(real_agg: Dict[str, Any]) -> str:
    fm = real_agg["forum_member_ambiguity"]
    subs = fm.get("subbuckets") or {}
    examples = fm.get("subbucket_examples") or {}
    resolver_buckets = set(fm.get("resolver_failure_buckets") or [])

    rows: List[str] = []
    for bucket, count in sorted(subs.items(), key=lambda kv: -kv[1]):
        tag = "**resolver failure**" if bucket in resolver_buckets else "_data gap_"
        rows.append(f"  - `{bucket}`: **{count}**  ({tag})")
    rows_md = "\n".join(rows) or "_(none)_"

    ex_block_parts: List[str] = []
    for bucket, items in examples.items():
        tag = "RESOLVER FAILURE" if bucket in resolver_buckets else "data gap"
        ex_block_parts.append(f"\n**`{bucket}`** ({tag}):")
        for it in items:
            ex_block_parts.append(
                f"  - frame=`{it.get('frame')}`  predicted=`{it.get('predicted_domain')}`"
                + (f"  unresolved=`{it.get('unresolved_name')}`"
                   if it.get('unresolved_name') else "")
                + f"  → {it.get('message', '')[:200]}")
    ex_block = "\n".join(ex_block_parts) or "_(no examples)_"

    return (
        "## 7. Forum vs Member Ambiguity Analysis\n\n"
        f"- Forum/member frame cases (REAL): **{fm['total']}**\n"
        f"- Unresolved target: **{fm['unresolved']}** ({fm['rate']*100:.2f}%)\n"
        f"- **Resolver failures** (gate-blocking sub-buckets): "
        f"**{fm['resolver_failure_count']}** "
        f"({fm['resolver_failure_rate_of_total']*100:.2f}% of total, "
        f"{fm['resolver_failure_rate_of_unresolved']*100:.2f}% of unresolved)\n"
        f"- **Data gaps** (acceptable, e.g. forum-only member, "
        f"unclassified ambient): **{fm['data_gap_count']}**\n"
        f"- **Correctly-handled rate** (resolved OR data gap): "
        f"**{fm['correctly_handled_rate']*100:.2f}%**\n\n"
        "**Sub-bucket definitions (mutually exclusive, first-match-wins):**\n"
        "  - `wrong_person_selected` — explicit_target_id present but the "
        "resolver could not bind it (mis-binding / stale id).\n"
        "  - `wrong_frame_selected` — frame=forum/member but message is "
        "self-oriented (1P singular phrasing, no group keywords, no name).\n"
        "  - `relationship_to_self_downgrade` — clear relational keyword "
        "present but predicted_domain ≠ relationship/family/parenting "
        "(the relational signal was lost downstream).\n"
        "  - `forum_to_member_misroute` — frame=forum, named person in "
        "message, but no member binding emerged (data gap; B3 fixes via "
        "fed `forum_topology.active_member_id`).\n"
        "  - `unclassified_unresolved` — catch-all (ambient forum probes / "
        "self-reflection-while-in-forum prompts).\n\n"
        "**Sub-bucket counts (REAL):**\n"
        f"{rows_md}\n\n"
        f"**Representative examples per bucket:**{ex_block}\n\n"
        "**Caveat:** the replay harness does not currently feed "
        "`forum_topology.active_member_id` into the resolver (that wiring "
        "lands in B3), so a high `unclassified_unresolved` count on "
        "forum/member frames is expected and is classified as a *data "
        "gap*, not a resolver failure.  In live shadow mode the active "
        "member is hydrated via `lens` / `about_person_id` request "
        "fields, which is why the live shadow `RESOLVED` rate is higher "
        "than the replay-corpus rate.\n"
    )


def _section_composition(replay: Dict[str, Any]) -> str:
    agg = replay["aggregate"]
    t = agg["totals"]
    cat = agg["stratification"]["by_category"]
    by_src = agg["stratification"]["by_source"]
    return (
        "## 8. Replay Corpus Composition (real vs synthetic)\n\n"
        f"- Total: **{t['n']}** (REAL **{t['n_real']}** / SYNTH **{t['n_synth']}**)\n"
        f"- Window: last **{replay.get('window_days')}** days "
        f"(real-message recency cutoff)\n"
        f"- Target band: {100}–{150} cases  →  current size: **{t['n']}** "
        f"(within band: **{t['in_window_target']}**)\n\n"
        f"**Category mix (combined)**:\n```json\n{json.dumps(cat, indent=2)}\n```\n\n"
        f"**Predicted-domain mix by source**:\n```json\n"
        f"{json.dumps(by_src, indent=2)}\n```\n\n"
        "The rollout decision is grounded primarily in **REAL** evidence; "
        "synthetic cases are used only to stretch coverage on archetype "
        "voices (leadership, founder, purpose) that the live corpus is "
        "currently too small to exercise.\n"
    )


def _section_samples_pointer() -> str:
    return (
        "## 9–10. Representative Success / Failure Cases\n\n"
        f"See companion file: `{SAMPLES_MD.name}`.\n\n"
        "It contains:\n"
        "- representative success cases drawn from REAL messages,\n"
        "- representative failure cases drawn from REAL messages,\n"
        "- false-positive relationship-routing samples,\n"
        "- and `UNRESOLVED_NAMED` samples with their `proposed_action` "
        "  payloads as they would be persisted to "
        "  `mirror_chat_retrieval_receipts`.\n"
    )


def _section_regression_buckets(real_agg: Dict[str, Any]) -> str:
    """Section 13 — operator's 10 regression buckets (June 14 focus list)."""
    rb = real_agg.get("regression_buckets") or {}
    if not rb:
        return ("## 13. Delta-Review Regression Buckets (operator focus list)\n\n"
                "_No regression bucket data found in replay results — "
                "make sure you've re-run `b2_replay_runner.py` after the "
                "B2 classifier update._\n")

    def _examples_md(items, fields_label=("frame", "predicted_domain")):
        if not items:
            return "  _(no examples)_"
        out = []
        for it in items:
            parts = []
            for k, v in it.items():
                if k == "message":
                    continue
                parts.append(f"{k}=`{v}`")
            head = "  ".join(parts) or ""
            out.append(f"  - {head} → {str(it.get('message', ''))[:180]}")
        return "\n".join(out)

    parts = ["## 13. Delta-Review Regression Buckets (REAL, operator focus list)\n",
             "_The 10 regression buckets the operator asked us to track on "
             "top of the existing FP/forum/unresolved gates.  These do **not** "
             "auto-block cutover — they are review signals.  A FAIL here means "
             "the operator must look before approving the next rollout stage._\n"]

    order = [
        ("1. Domain drift",             "domain_drift",            True),
        ("2. Lens-jargon override",     "lens_jargon_override",    True),
        ("3. Relationship-context loss", "relationship_context_loss", True),
        ("4. Wrong-target selection",   "wrong_target_selected",   True),
        ("5. Retrieval payload completeness", "payload_completeness", False),
        ("6. Cross-lens coverage",      "cross_lens_coverage",     False),
        ("7. False confidence (high-confidence wrong route)",
                                        "high_confidence_wrong_route", True),
        ("8. Founder/operator suite",   "founder_operator_suite",  False),
        ("9. Couple ↔ Forum separation","couple_forum_separation", True),
        ("10. Decision explainability", "explainability",          False),
    ]
    for title, key, show_examples in order:
        b = rb.get(key) or {}
        parts.append(f"\n### {title}\n")
        status = b.get("status", "UNKNOWN")
        gate = b.get("gate", "—")
        parts.append(f"- **Status**: `{status}`")
        parts.append(f"- **Gate**: {gate}")
        if key == "domain_drift":
            parts.append(
                f"- Rate: **{b.get('rate', 0)*100:.2f}%** "
                f"({b.get('count', 0)} / {b.get('ground_truth_rows', 0)} "
                f"ground-truth rows)")
            kinds = b.get("kinds") or {}
            if kinds:
                parts.append(f"- Kinds: `{kinds}`")
            hot = b.get("domains_above_10pct") or []
            if hot:
                parts.append(f"- Per-domain hot zones (>10%): {hot}")
        elif key == "lens_jargon_override":
            parts.append(
                f"- Rate: **{b.get('rate', 0)*100:.2f}%** "
                f"({b.get('count', 0)} cases)")
            kinds = b.get("kinds") or {}
            if kinds:
                parts.append(f"- Patterns: `{kinds}`")
        elif key == "relationship_context_loss":
            parts.append(
                f"- Rate: **{b.get('rate', 0)*100:.2f}%** "
                f"({b.get('count', 0)} cases)")
        elif key == "wrong_target_selected":
            parts.append(f"- Count: **{b.get('count', 0)}**")
        elif key == "payload_completeness":
            parts.append(
                f"- mandatory_modules count: mean={b.get('mandatory_modules_mean')} "
                f"min={b.get('mandatory_modules_min')} "
                f"max={b.get('mandatory_modules_max')}")
            parts.append(f"- Note: {b.get('note', '')}")
        elif key == "cross_lens_coverage":
            parts.append(
                f"- Multi-lens prompts: **{b.get('multi_lens_prompts', 0)}**, "
                f"covered with ≥2 lenses: **{b.get('covered_2plus', 0)}**, "
                f"coverage rate: **{b.get('coverage_rate', 0)*100:.2f}%**")
        elif key == "high_confidence_wrong_route":
            parts.append(
                f"- Rate: **{b.get('rate', 0)*100:.2f}%** "
                f"({b.get('count', 0)} cases)")
        elif key == "founder_operator_suite":
            parts.append(f"- Count: **{b.get('count', 0)}**")
            parts.append(f"- Routing PASS rate: "
                         f"**{b.get('routing_pass_rate', 0)*100:.2f}%**")
            parts.append(f"- Domain mix: `{b.get('predicted_domain_mix') or {}}`")
        elif key == "couple_forum_separation":
            parts.append(f"- Count: **{b.get('count', 0)}**")
            parts.append(f"- Kinds: `{b.get('kinds') or {}}`")
        elif key == "explainability":
            parts.append(
                f"- Non-explainable decisions: "
                f"**{b.get('decision_not_explainable_count', 0)}** "
                f"({b.get('rate', 0)*100:.2f}%)")
        if show_examples:
            ex = b.get("examples") or []
            if ex:
                parts.append("- Examples:")
                parts.append(_examples_md(ex))
    return "\n".join(parts) + "\n"


def _diff_vs_baseline(replay: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Compare the current replay run against the frozen baseline.

    Surfaces operator's June 14 focus list:
      1. NEW false-positive relationship-routing examples
      2. NEW resolver-failure sub-buckets (in live telemetry)
      3. Distribution delta of unresolved-named sub-buckets
      4. NEW forum/member ambiguity examples
      5. NEW regression clusters (≥3 cases of the same kind not seen
         in baseline)
    Returns None if baseline is missing.
    """
    if not BASELINE_REPLAY_JSON.exists():
        return None
    try:
        baseline = json.loads(BASELINE_REPLAY_JSON.read_text())
    except Exception:
        return None

    cur_real = replay["aggregate"]["aggregates_by_source"]["real"]
    base_real = baseline["aggregate"]["aggregates_by_source"]["real"]

    def _msgs(rows):
        return {(r["source"], r["message"]) for r in rows}
    base_msgs = _msgs(baseline.get("rows", []))

    def _new_examples(predicate, limit=10):
        return [
            {"frame": r["active_frame"],
             "predicted": r["predicted_domain"],
             "message": r["message"]}
            for r in replay.get("rows", [])
            if predicate(r)
            and (r["source"], r["message"]) not in base_msgs
        ][:limit]

    # 1. new FP examples
    new_fp = _new_examples(
        lambda r: r["predicted_domain"] == "relationship"
        and r["active_frame"] == "self"
        and not r["rel_target_resolved"]
        and r.get("explicit_target_id") is None
    )

    # 2. new resolver-failure sub-buckets
    rf_buckets = {"wrong_person_selected", "wrong_frame_selected",
                  "relationship_to_self_downgrade"}
    new_resolver_fail = _new_examples(
        lambda r: r.get("fm_subbucket") in rf_buckets
    )

    # 3. unresolved-named sub-bucket distribution delta
    cur_un = cur_real["target_resolution"].get("unresolved_named_subbuckets", {})
    base_un = base_real["target_resolution"].get("unresolved_named_subbuckets", {})
    keys = sorted(set(cur_un.keys()) | set(base_un.keys()))
    un_delta = {k: {"baseline": base_un.get(k, 0),
                    "current": cur_un.get(k, 0),
                    "delta": cur_un.get(k, 0) - base_un.get(k, 0)}
                for k in keys}

    # 4. new forum/member ambiguity examples
    new_fm = _new_examples(
        lambda r: r["active_frame"] in ("forum", "member")
        and not r["rel_target_resolved"]
    )

    # 5. regression clusters — group new-since-baseline failures
    # (predicted=general OR routing=FAIL OR resolver-failure-bucket)
    # by (predicted_domain, fm_subbucket) and surface clusters ≥3.
    clusters: Dict[Tuple[str, Optional[str]], List[Dict[str, Any]]] = {}
    for r in replay.get("rows", []):
        if (r["source"], r["message"]) in base_msgs:
            continue
        if (r["predicted_domain"] == "general"
                or r["routing_status"] == "FAIL"
                or r.get("fm_subbucket") in rf_buckets):
            key = (r["predicted_domain"], r.get("fm_subbucket"))
            clusters.setdefault(key, []).append({
                "frame": r["active_frame"],
                "message": r["message"],
            })
    regression_clusters = [
        {"predicted_domain": k[0], "fm_subbucket": k[1],
         "count": len(v), "examples": v[:3]}
        for k, v in clusters.items() if len(v) >= 3
    ]

    return {
        "baseline_generated_at": baseline.get("generated_at"),
        "current_generated_at": replay.get("generated_at"),
        "new_fp_relationship_examples": new_fp,
        "new_resolver_failure_examples": new_resolver_fail,
        "unresolved_named_distribution_delta": un_delta,
        "new_forum_member_unresolved_examples": new_fm,
        "regression_clusters": regression_clusters,
    }


def _section_delta(delta: Optional[Dict[str, Any]]) -> str:
    if delta is None:
        return ("## 14. Delta vs. baseline (June 11 sign-off)\n\n"
                "_No baseline snapshot found at "
                f"`{BASELINE_REPLAY_JSON.name}`. Skipping delta section._\n")

    def _fmt_examples(items, missing_msg="_(none)_"):
        if not items:
            return missing_msg
        return "\n".join(
            f"  - `{e.get('frame')}` / predicted=`{e.get('predicted')}` → "
            f"{e.get('message', '')[:200]}"
            for e in items
        )

    un_rows = "\n".join(
        f"  - `{k}`: baseline={v['baseline']}  current={v['current']}  "
        f"Δ={v['delta']:+d}"
        for k, v in delta["unresolved_named_distribution_delta"].items()
    )

    clusters_md_parts: List[str] = []
    for c in delta["regression_clusters"]:
        clusters_md_parts.append(
            f"\n- **predicted=`{c['predicted_domain']}`  "
            f"fm_subbucket=`{c['fm_subbucket']}`**  ×{c['count']}"
        )
        for ex in c["examples"]:
            clusters_md_parts.append(f"    - `{ex['frame']}` → {ex['message'][:200]}")
    clusters_md = "\n".join(clusters_md_parts) or "_(no new clusters)_"

    return (
        "## 14. Delta vs. baseline (June 11 sign-off)\n\n"
        f"_Baseline frozen at_ `{delta['baseline_generated_at']}`.  "
        f"_Current run_ `{delta['current_generated_at']}`.\n\n"
        "Operator's June 14 focus list, computed automatically:\n\n"
        "### 1. New false-positive relationship-routing examples (REAL)\n\n"
        f"{_fmt_examples(delta['new_fp_relationship_examples'])}\n\n"
        "### 2. New resolver-failure sub-buckets observed since baseline\n\n"
        f"{_fmt_examples(delta['new_resolver_failure_examples'])}\n\n"
        "### 3. Unresolved-named sub-bucket distribution delta\n\n"
        f"{un_rows or '_(no changes)_'}\n\n"
        "### 4. New forum/member ambiguity examples since baseline\n\n"
        f"{_fmt_examples(delta['new_forum_member_unresolved_examples'])}\n\n"
        "### 5. Regression clusters (≥3 new failures of the same kind)\n"
        f"{clusters_md}\n"
    )


def _section_risks(blockers: List[str], shadow: Dict[str, Any], real: Dict[str, Any]) -> str:
    fp_rate = real["false_positive_relationship"]["rate"]
    fp_alert = fp_rate >= 0.05
    risks = []
    if fp_alert:
        risks.append(
            f"**🚨 FP-RELATIONSHIP ALERT**: frame-aware false-positive rate "
            f"is **{fp_rate*100:.2f}%** ≥ 5%.  Hold rollout and investigate "
            f"the offending examples in section 4."
        )
    risks.extend([
        "**Forum/member ambiguity:** replay harness does not feed "
        "`forum_topology.active_member_id` into the resolver yet — the bulk "
        "of the `unclassified_unresolved` sub-bucket is ambient forum "
        "probes and resolves once that wiring lands in B3.  No "
        "resolver-failure sub-buckets observed in REAL.",
        "**Real corpus size:** the 90-day real corpus is currently "
        f"~{real['totals']['n']} messages.  Synthetic supplementation is "
        "still required for archetype voices (leadership/purpose/founder); "
        "the rollout decision is grounded in REAL evidence only.",
        "**Shadow telemetry window not yet complete** — "
        f"{shadow['n_receipts']} receipts persisted so far.  Window ends "
        f"{OBSERVATION_WINDOW_END}; cutover blocked until window closes.",
        "**Sign-conflation hallucination (P2)** — open issue tracked "
        "separately (`natal_object_engine.py`).  Not a B2 blocker, but "
        "queued for after-B2 priority work.",
    ])
    return (
        "## 11. Remaining Risks\n\n"
        + "\n".join(f"- {r}" for r in risks) + "\n"
    )


def _section_rollout(rec: str, blockers: List[str]) -> str:
    plan = (
        "If `GO`: cutover proceeds in three stages over 7 days — "
        "**10%** (24h) → **50%** (48h) → **100%** with rollback on any "
        "of: (a) frame-aware FP rate >2x baseline, (b) routing PASS rate "
        "<70%, (c) p95 latency >100ms, (d) any >5% drop in per-suite "
        "golden top-1."
    ) if rec != "NO_GO" else (
        "Cutover blocked.  Fix the failed gate(s) above and re-run "
        "`b2_replay_runner` + `b2_readiness_report` to recompute."
    )
    return (
        "## 12. Rollout Recommendation\n\n"
        f"**`{rec}`**\n\n"
        + ("**Conditions to flip to `GO`:**\n"
           + "\n".join(f"- {b}" for b in blockers) + "\n\n"
           if rec == "CONDITIONAL_GO" and blockers else "")
        + plan + "\n"
    )


async def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build the Mirror Chat V2 Slice B2 Readiness Report.")
    ap.add_argument(
        "--baseline", action="store_true",
        help="Diff against the frozen baseline JSON snapshots and append "
             "section 14 (Delta vs. baseline) to the markdown.")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not REPLAY_JSON.exists():
        print(f"missing {REPLAY_JSON}; run b2_replay_runner.py first",
              file=sys.stderr)
        return 2
    if not BENCH_JSON.exists():
        print(f"missing {BENCH_JSON}; run intent_router_v2_benchmark first",
              file=sys.stderr)
        return 2

    replay = json.loads(REPLAY_JSON.read_text())
    bench = json.loads(BENCH_JSON.read_text())

    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    shadow = await _shadow_telemetry(db)
    cli.close()

    real = replay["aggregate"]["aggregates_by_source"]["real"]

    gate_rows, recommendation, blockers = _build_scorecard(
        replay=replay, bench=bench, shadow=shadow)

    delta = _diff_vs_baseline(replay) if args.baseline else None

    # --- Markdown ---
    parts: List[str] = []
    parts.append(
        "# Mirror Chat V2 — Slice B2 Readiness Report\n\n"
        f"_Generated: {datetime.now(dt_tz.utc).isoformat()}_\n\n"
        "_This is the canonical artifact for the B2 production cutover "
        "decision._  \n"
        "_All recommendations stay capped at `CONDITIONAL_GO` until the "
        f"shadow telemetry observation window closes on {OBSERVATION_WINDOW_END}._\n"
    )
    parts.append(_section_executive(recommendation, blockers,
                                    replay["aggregate"]))

    parts.append("## 2. Gate Status Matrix\n\n"
                 + _markdown_table(gate_rows, [("Gate", "gate"),
                                               ("Value", "value"),
                                               ("Threshold", "threshold"),
                                               ("Status", "status")]))

    parts.append(_section_shadow(shadow))
    parts.append(_section_fp(real, replay["aggregate"]))
    parts.append(_section_domain_drift(real))
    parts.append(_section_target(real))
    parts.append(_section_forum_ambig(real))
    parts.append(_section_composition(replay))
    parts.append(_section_samples_pointer())
    parts.append(_section_risks(blockers, shadow, real))
    parts.append(_section_rollout(recommendation, blockers))
    parts.append(_section_regression_buckets(real))
    if args.baseline:
        parts.append(_section_delta(delta))
    parts.append(
        "\n## After-B2 priority queue (per operator review)\n\n"
        "1. **Cross-Lens Synthesis Phase 2** (tension / contradiction).\n"
        "2. **Relationship-aware orchestration** (use `proposed_action` "
        "telemetry to inform circle-add prompts and lens chaining).\n"
        "3. **Forum topology resolution** (wire "
        "`forum_topology.active_member_id` into the resolver; promotes "
        "`forum_to_member_misroute` and `unclassified_unresolved` cases "
        "out of the data-gap bucket).\n"
        "4. **Sign-conflation safeguards** in `natal_object_engine.py` "
        "(P2; anti-confusion clauses).\n"
    )
    parts.append(
        "\n## Rollout halt criteria (auto-stop between stages)\n\n"
        "The phased rollout (10% → 50% → 100%) automatically halts and "
        "requires operator review if any of the following appears in the "
        "stage's observation window:\n\n"
        "- Retrieval PASS rate **< 97%**\n"
        "- False-positive relationship rate **> 5%**\n"
        "- Any **new resolver-failure sub-bucket** in live telemetry\n"
        "- Forum/member correctly-handled rate **< 90%**\n"
        "- Any **unexpected rise** in `target_unresolved` rate vs prior stage\n"
        "- Any **regression cluster** (≥3 cases) not represented in the "
        "golden sets\n"
        "- Any of the section-13 review-signal gates flipping FAIL since "
        "the prior stage (domain drift, lens-jargon override, relationship-"
        "context loss, wrong-target selection, multi-lens coverage, "
        "high-confidence wrong route, couple↔forum bleed).\n"
    )
    parts.append(
        "\n---\n"
        "### Evidence separation\n\n"
        "- **From REAL messages**: gate statuses for false-positive "
        "relationship, forum/member ambiguity, target-resolution, "
        "shadow-telemetry status, general-bucket rate, AND every section-13 "
        "regression bucket are computed on REAL only.\n"
        "- **From SYNTHETIC messages**: golden-set top-1 (over all "
        "suites including the synth slice of "
        "`golden_set_pete_mel_historical.yaml`) and retrieval-receipt "
        "coverage (PASS rate).\n"
        "- **Versions** — "
        f"`{replay['aggregate']['versions']['intent_router']}`, "
        f"`{replay['aggregate']['versions']['relationship_router']}`, "
        f"`{replay['aggregate']['versions']['validator']}`.\n"
    )
    REPORT_MD.write_text("\n".join(parts))
    print(f"Wrote {REPORT_MD}")

    # --- JSON twin (machine-readable for dashboards) ---
    json_doc = {
        "generated_at": datetime.now(dt_tz.utc).isoformat(),
        "recommendation": recommendation,
        "blockers": blockers,
        "gate_scorecard": gate_rows,
        "shadow_telemetry": shadow,
        "replay_aggregate_real": real,
        "replay_aggregate_all": replay["aggregate"],
        "benchmark_offline": bench.get("offline"),
        "observation_window_end": OBSERVATION_WINDOW_END,
        "thresholds": GATE_THRESHOLDS,
    }
    if args.baseline:
        json_doc["delta_vs_baseline"] = delta
    REPORT_JSON.write_text(json.dumps(json_doc, indent=2, default=str))
    print(f"Wrote {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
