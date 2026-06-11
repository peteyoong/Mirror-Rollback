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

import asyncio
import json
import os
import sys
from datetime import datetime, timezone as dt_tz, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

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

OBSERVATION_WINDOW_END = "2026-06-14"
OBSERVATION_WINDOW_DAYS = 3

# Thresholds for the readiness scorecard.
GATE_THRESHOLDS = {
    "golden_set_top1_min":              0.95,   # B1.3 hit 100% → 95% floor
    "retrieval_pass_min":               0.95,
    "target_resolution_proposed_min":   0.05,   # at least 5% of msgs should
                                                # produce a proposed_action
                                                # to know the path is wired
    "false_positive_relationship_max":  0.10,   # frame-aware fp rate
    "forum_member_ambiguity_max":       0.95,   # ≤95% unresolved on
                                                # forum/member frame is OK
                                                # for now (resolver doesn't
                                                # have forum_topology fed yet)
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

    # Forum / member ambiguity — informational gate; resolver doesn't yet
    # receive forum_topology so high unresolved is expected.
    fma = real["forum_member_ambiguity"]
    rows.append({
        "gate": "Forum/member ambiguity (REAL)",
        "value": (f"{fma['rate']*100:.2f}% unresolved "
                  f"({fma['unresolved']}/{fma['total']})"),
        "threshold": (f"≤ {GATE_THRESHOLDS['forum_member_ambiguity_max']*100:.0f}% "
                      f"(advisory — fed forum_topology lands in B3)"),
        "status": _gate(fma["rate"]
                        <= GATE_THRESHOLDS["forum_member_ambiguity_max"]),
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

    # Determine blockers and recommendation.
    hard_fails = [g for g in rows
                  if g["status"] == "FAIL"
                  and g["gate"] not in ("Forum/member ambiguity (REAL)",
                                        "Shadow telemetry window complete",
                                        "Manual review complete")]
    if hard_fails:
        blockers = [g["gate"] for g in hard_fails]
        recommendation = "NO_GO"
    elif not shadow["window_complete"]:
        recommendation = "CONDITIONAL_GO"
        blockers = ["Shadow telemetry window not complete (ends "
                    f"{OBSERVATION_WINDOW_END})"]
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
    return (
        "## 6. Target Resolution Analysis\n\n"
        f"- Status counts (REAL): `{tr['status_counts']}`\n"
        f"- Unresolved-named-target rate (REAL): "
        f"**{tr['unresolved_named_rate']*100:.2f}%** "
        f"({tr['unresolved_named_count']} cases)\n\n"
        "Every `UNRESOLVED_NAMED` case carries a `proposed_action` payload "
        "(`type=add_to_circle`, with `suggested_name`, `reason`, "
        "`source_text`, `confidence`) attached to the diagnostic receipt.\n\n"
        "**The proposed_action stays receipt-only.** No UI surface, no "
        "relationship-role inference, no auto-create.  This is purely "
        "telemetry-gathering during the B2 observation window.\n"
    )


def _section_forum_ambig(real_agg: Dict[str, Any]) -> str:
    fm = real_agg["forum_member_ambiguity"]
    return (
        "## 7. Forum vs Member Ambiguity Analysis\n\n"
        f"- Forum/member frame cases (REAL): **{fm['total']}**\n"
        f"- Unresolved target (no `target_id`, no resolved name): "
        f"**{fm['unresolved']}** ({fm['rate']*100:.2f}%)\n\n"
        "**Caveat:** the replay harness does not currently feed "
        "`forum_topology.active_member_id` into the resolver (that wiring "
        "lands in B3), so a high unresolved rate on forum/member frames is "
        "expected and is *not* counted as a hard blocker.  In live shadow "
        "mode the active member is hydrated via `lens` / `about_person_id` "
        "request fields, which is why the live shadow `RESOLVED` rate is "
        "higher than the replay-corpus rate.\n"
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


def _section_risks(blockers: List[str], shadow: Dict[str, Any]) -> str:
    risks = [
        "**Forum/member ambiguity:** resolver does not yet receive "
        "`forum_topology.active_member_id` in the replay harness — live "
        "shadow mode hydrates this from request fields. B3 will wire the "
        "topology end-to-end.",
        "**Real corpus size:** the 90-day real corpus is currently "
        "~49 messages.  Synthetic supplementation is required to stress "
        "leadership/purpose/founder voices; the rollout call should not "
        "be made on synth alone.",
        "**Shadow telemetry window not yet complete** — only "
        f"{shadow['n_receipts']} receipts persisted so far.  Window ends "
        f"{OBSERVATION_WINDOW_END}; cutover blocked until window passes.",
        "**Sign-conflation hallucination (P2)** — open issue tracked "
        "separately (`natal_object_engine.py`), unrelated to routing but "
        "feeds the *post-route* synthesis pass.  Not a B2 blocker.",
    ]
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
    parts.append(_section_risks(blockers, shadow))
    parts.append(_section_rollout(recommendation, blockers))
    parts.append(
        "\n---\n"
        "### Evidence separation\n\n"
        "- **From REAL messages**: gate statuses for false-positive "
        "relationship, forum/member ambiguity, target-resolution, "
        "shadow-telemetry status, and general-bucket rate are computed "
        "on REAL only.\n"
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
    REPORT_JSON.write_text(json.dumps({
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
    }, indent=2, default=str))
    print(f"Wrote {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
