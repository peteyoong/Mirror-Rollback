"""b2_replay_runner.py — Mirror Chat V2 Slice B2 shadow telemetry replay.

Pulls real user messages from `chat_history`, `forum_chat_messages`, and
`forum_mirror_chat_messages` over the last N days, optionally
supplements with synthetic cases from
`tests/intent_router_v2/golden_set_pete_mel_historical.yaml` (only the
`source: synth` rows), then runs every message through the V2 shadow
stack (`intent_router_v2` + `relationship_router_v2` +
`retrieval_validation_v1.build_receipt`).

Produces:
  * /app/backend/audit_reports/B2_REPLAY_RESULTS.json — full per-case
    rows + aggregate metrics, sliced by source(real/synth) and category.
  * /app/backend/audit_reports/B2_REPLAY_SAMPLES.md  — representative
    success cases + representative failure cases for the readiness
    report appendix.

NOTE: shadow only.  Never writes to mirror_chat_retrieval_receipts here
(this is a *replay* of historical messages, not a live ingest).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

import yaml  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services.intent_router_v2 import classify_intent_v2, ROUTER_VERSION as INTENT_VER  # noqa: E402
from services.relationship_router_v2 import (  # noqa: E402
    resolve_relationship_context,
    ROUTER_VERSION as REL_VER,
)
from services.retrieval_validation_v1 import (  # noqa: E402
    build_receipt,
    mandatory_modules,
    VALIDATOR_VERSION,
)

OUT_DIR = BACKEND_DIR / "audit_reports"
RESULTS_JSON = OUT_DIR / "B2_REPLAY_RESULTS.json"
SAMPLES_MD = OUT_DIR / "B2_REPLAY_SAMPLES.md"
SYNTH_YAML = BACKEND_DIR / "tests" / "intent_router_v2" / "golden_set_pete_mel_historical.yaml"

DEFAULT_WINDOW_DAYS = 90
TARGET_TOTAL_LOW = 100
TARGET_TOTAL_HIGH = 150


CATEGORY_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("relationship",     re.compile(r"\b(mel|wife|husband|partner|spouse|marriage|us|we|relationship|relating)\b", re.I)),
    ("forum_member",     re.compile(r"\b(forum|group|member|room|cohort|circle)\b", re.I)),
    ("career_founder",   re.compile(r"\b(ceo|founder|board|team|fundraise|runway|role|vp|company|leader|product|engineering)\b", re.I)),
    ("lens_jargon",      re.compile(r"\b(saturn|venus|mars|jupiter|pluto|mercury|node|house|chart|gate|channel|profile|authority|enneagram|human design|astrology|numerology|bazi)\b", re.I)),
    ("identity_growth",  re.compile(r"\b(show up|naturally|am i|who am i|patterns?|growth|stuck|cycle|season)\b", re.I)),
]


def categorise(message: str, frame: str, has_target: bool) -> str:
    if frame in ("forum",):
        return "forum_member"
    if has_target or frame == "member":
        return "forum_member"
    for name, pat in CATEGORY_PATTERNS:
        if pat.search(message or ""):
            return name
    return "other"


async def _pull_real(db, window_days: int) -> List[Dict[str, Any]]:
    """Pull real user messages from the three chat collections.

    chat_history.messages: array on a user doc → each {role:user} item is a
                            replay case
    forum_chat_messages: 1 doc per user turn with {message, target_member_*,
                          mode}
    forum_mirror_chat_messages: 1 doc per turn with {content, role}
    """
    rows: List[Dict[str, Any]] = []
    cutoff = datetime.now(dt_tz.utc) - timedelta(days=window_days)

    # 1. chat_history — wraps an array of {role, content, timestamp}.
    async for doc in db["chat_history"].find({}):
        user_id = str(doc.get("user_id") or "")
        for m in (doc.get("messages") or []):
            if (m.get("role") or "").lower() != "user":
                continue
            content = (m.get("content") or "").strip()
            if not content:
                continue
            ts = m.get("timestamp")
            try:
                ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).split(".")[0])
                if ts_dt.tzinfo is None:
                    ts_dt = ts_dt.replace(tzinfo=dt_tz.utc)
            except Exception:
                ts_dt = datetime.now(dt_tz.utc)
            if ts_dt < cutoff:
                continue
            rows.append({
                "source": "real",
                "collection": "chat_history",
                "user_id": user_id,
                "message": content,
                "active_frame": "self",
                "current_target_id": None,
                "relationship_role": None,
                "ts": ts_dt.isoformat(),
            })

    # 2. forum_chat_messages — has mode + target_member info.
    async for doc in db["forum_chat_messages"].find({}):
        content = (doc.get("message") or "").strip()
        if not content:
            continue
        ts = doc.get("timestamp")
        try:
            ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).split(".")[0])
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=dt_tz.utc)
        except Exception:
            ts_dt = datetime.now(dt_tz.utc)
        if ts_dt < cutoff:
            continue
        mode = (doc.get("mode") or "").lower()
        target = doc.get("target_member_id")
        frame = "member" if target else ("forum" if mode == "forum" else "self")
        rows.append({
            "source": "real",
            "collection": "forum_chat_messages",
            "user_id": str(doc.get("user_id") or ""),
            "message": content,
            "active_frame": frame,
            "current_target_id": str(target) if target else None,
            "relationship_role": None,
            "target_member_name": doc.get("target_member_name"),
            "ts": ts_dt.isoformat(),
        })

    # 3. forum_mirror_chat_messages — turn-based.
    async for doc in db["forum_mirror_chat_messages"].find({"role": "user"}):
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        ts = doc.get("ts")
        try:
            ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).split(".")[0])
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=dt_tz.utc)
        except Exception:
            ts_dt = datetime.now(dt_tz.utc)
        if ts_dt < cutoff:
            continue
        rows.append({
            "source": "real",
            "collection": "forum_mirror_chat_messages",
            "user_id": str(doc.get("user_id") or ""),
            "message": content,
            "active_frame": "forum",
            "current_target_id": None,
            "relationship_role": None,
            "ts": ts_dt.isoformat(),
        })

    return rows


def _load_synth_supplement(target_min: int) -> List[Dict[str, Any]]:
    if not SYNTH_YAML.exists():
        return []
    with open(SYNTH_YAML) as f:
        cases = yaml.safe_load(f) or []
    synth_rows: List[Dict[str, Any]] = []
    for c in cases:
        if c.get("source") != "synth":
            continue
        synth_rows.append({
            "source": "synth",
            "collection": "golden_set_pete_mel_historical",
            "user_id": "synth-pete",
            "message": c.get("message", ""),
            "active_frame": c.get("active_frame", "self"),
            "current_target_id": c.get("current_target_id"),
            "relationship_role": c.get("relationship_role"),
            "expected_primary": c.get("expected_primary"),
            "category_hint": c.get("category"),
            "ts": None,
        })
    return synth_rows[:target_min]


def _saved_people_for(user_id: str) -> List[Dict[str, Any]]:
    """Replay uses a minimal stub.  In live mode the router would pull
    the user's saved_people; here we keep it empty so the missing-target
    fallback gets a fair chance to fire."""
    return []


def _run_one(row: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    frame = row["active_frame"]
    target_id = row.get("current_target_id")
    role = row.get("relationship_role")
    rel = resolve_relationship_context(
        self_user_id=row.get("user_id") or "",
        user_message=row["message"],
        active_frame=frame,
        target_id=target_id,
        saved_people=_saved_people_for(row.get("user_id") or ""),
    )
    env = classify_intent_v2(
        message=row["message"],
        active_frame=frame,
        current_target_id=rel.target or target_id,
        relationship_role=rel.role or role,
    )
    envd = env.to_dict()
    modules = mandatory_modules(envd["primary_domain"])
    receipt = build_receipt(
        request_id=f"replay-{row.get('user_id', 'unknown')[:8]}-{time.time_ns()}",
        intent_envelope=envd,
        relationship_resolution=rel.to_dict(),
        modules_invoked=modules,
        payloads={m: {"sim": True} for m in modules},
    )
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    predicted = envd["primary_domain"]
    expected = row.get("expected_primary")
    top1_hit = (expected is None) or (predicted == expected)
    category = row.get("category_hint") or categorise(row["message"], frame, bool(target_id or rel.target))

    return {
        "source": row["source"],
        "collection": row["collection"],
        "user_id_short": (row.get("user_id") or "")[:10],
        "message": row["message"],
        "active_frame": frame,
        "explicit_target_id": target_id,
        "category": category,
        "predicted_domain": predicted,
        "expected_domain": expected,
        "top1_hit": top1_hit if expected else None,
        "signal_strength": envd.get("signal_strength"),
        "margin": envd.get("margin"),
        "confidence": envd.get("confidence"),
        "fallback_reason": (envd.get("evidence") or {}).get("fallback_reason"),
        "relationship_relevant": envd.get("relationship_relevant"),
        "secondary_domains": envd.get("secondary_domains"),
        "rel_target_resolved": rel.target,
        "rel_target_unresolved_name": rel.target_unresolved_name,
        "rel_missing_data": rel.missing_data,
        "rel_proposed_action": rel.proposed_action,
        "rel_context_mode": rel.context_mode,
        "retrieval_status": receipt["retrieval_status"],
        "routing_status": receipt["routing_status"],
        "target_resolution_status": receipt["target_resolution_status"],
        "latency_ms": latency_ms,
    }


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute the readiness metrics the user asked for."""
    n = len(rows)
    n_real = sum(1 for r in rows if r["source"] == "real")
    n_synth = sum(1 for r in rows if r["source"] == "synth")

    domain_counts = Counter(r["predicted_domain"] for r in rows)
    routing_counts = Counter(r["routing_status"] for r in rows)
    retrieval_counts = Counter(r["retrieval_status"] for r in rows)
    target_status_counts = Counter(r["target_resolution_status"] for r in rows)
    by_source: Dict[str, Counter] = {"real": Counter(), "synth": Counter()}
    for r in rows:
        by_source[r["source"]][r["predicted_domain"]] += 1
    cat_counts = Counter(r["category"] for r in rows)

    # False-positive relationship routing.  Two flavours:
    #  * "frame_aware" — TRUE false positive: predicted=relationship in
    #    `self` frame with no target_id and no relationship keyword.  The
    #    forum/member frames *intentionally* bias toward relationship via
    #    FRAME_BIAS, so we exclude them.
    #  * "broad"       — pre-bias view: predicted=relationship without
    #    target/keyword regardless of frame.  Useful when reasoning about
    #    the FRAME_BIAS contribution itself.
    rel_keyword_re = re.compile(
        r"\b(mel|wife|husband|partner|spouse|marriage|us|we|her|him|relationship|"
        r"between\s+\w+\s+and|together|fight|distant|connection|conflict)\b", re.I)
    fp_rel = [
        r for r in rows
        if r["predicted_domain"] == "relationship"
        and r["active_frame"] == "self"
        and not r["rel_target_resolved"]
        and not rel_keyword_re.search(r["message"])
        and r["explicit_target_id"] is None
    ]
    fp_rel_broad = [
        r for r in rows
        if r["predicted_domain"] == "relationship"
        and not r["rel_target_resolved"]
        and not rel_keyword_re.search(r["message"])
        and r["explicit_target_id"] is None
    ]

    # False-negative relationship routing: explicit target or relationship
    # keyword present but predicted is NOT relationship/family/parenting.
    fn_rel = [
        r for r in rows
        if r["predicted_domain"] not in ("relationship", "family", "parenting")
        and (r["explicit_target_id"] or r["rel_target_resolved"]
             or rel_keyword_re.search(r["message"]))
    ]

    # Forum/member ambiguity: frame is forum/member but the resolver
    # produced no target AND no proposed_action.
    forum_member_unresolved = [
        r for r in rows
        if r["active_frame"] in ("forum", "member")
        and not r["rel_target_resolved"]
    ]
    forum_member_total = [r for r in rows if r["active_frame"] in ("forum", "member")]

    # Unresolved-named-target rate: rows where a proper name was detected
    # but no saved-people match.
    unresolved_named = [r for r in rows if r["target_resolution_status"] == "UNRESOLVED_NAMED"]

    # General-bucket rate.
    general = [r for r in rows if r["predicted_domain"] == "general"]

    # Fallback (low/no_signal) rate.
    fallbacks = [r for r in rows if r["fallback_reason"] in ("low_signal", "no_signal", "weak_ambiguous")]

    # Real-only golden-set accuracy: only meaningful where expected is
    # provided (synth rows).  For real rows we don't have ground truth.
    expected_rows = [r for r in rows if r["expected_domain"]]
    expected_top1 = [r for r in expected_rows if r["top1_hit"]]

    lat = [r["latency_ms"] for r in rows]

    return {
        "totals": {
            "n": n,
            "n_real": n_real,
            "n_synth": n_synth,
            "in_window_target": (TARGET_TOTAL_LOW <= n <= TARGET_TOTAL_HIGH),
        },
        "stratification": {
            "by_category": dict(cat_counts),
            "by_source": {k: dict(v) for k, v in by_source.items()},
            "domain_counts": dict(domain_counts),
        },
        "routing": {
            "status_counts": dict(routing_counts),
            "pass_rate": round(routing_counts.get("PASS", 0) / max(n, 1), 4),
        },
        "retrieval": {
            "status_counts": dict(retrieval_counts),
            "pass_rate": round(retrieval_counts.get("PASS", 0) / max(n, 1), 4),
        },
        "target_resolution": {
            "status_counts": dict(target_status_counts),
            "unresolved_named_rate": round(len(unresolved_named) / max(n, 1), 4),
            "unresolved_named_count": len(unresolved_named),
        },
        "false_positive_relationship": {
            "count": len(fp_rel),
            "rate": round(len(fp_rel) / max(n, 1), 4),
            "broad_count": len(fp_rel_broad),
            "broad_rate": round(len(fp_rel_broad) / max(n, 1), 4),
            "examples": [{"message": r["message"], "frame": r["active_frame"],
                          "category": r["category"]} for r in fp_rel[:10]],
        },
        "false_negative_relationship": {
            "count": len(fn_rel),
            "rate": round(len(fn_rel) / max(n, 1), 4),
            "examples": [{"message": r["message"], "predicted": r["predicted_domain"],
                          "frame": r["active_frame"]} for r in fn_rel[:10]],
        },
        "forum_member_ambiguity": {
            "total": len(forum_member_total),
            "unresolved": len(forum_member_unresolved),
            "rate": round(
                len(forum_member_unresolved) / max(len(forum_member_total), 1), 4),
        },
        "general_bucket": {
            "count": len(general),
            "rate": round(len(general) / max(n, 1), 4),
        },
        "fallback": {
            "count": len(fallbacks),
            "rate": round(len(fallbacks) / max(n, 1), 4),
        },
        "expected_top1_synth_only": {
            "n_with_expected": len(expected_rows),
            "n_top1": len(expected_top1),
            "accuracy": round(len(expected_top1) / max(len(expected_rows), 1), 4),
        },
        "latency_ms": {
            "mean": round(statistics.mean(lat), 3) if lat else 0,
            "p50": round(statistics.median(lat), 3) if lat else 0,
            "p95": round(sorted(lat)[int(0.95 * (len(lat) - 1))], 3) if lat else 0,
            "max": round(max(lat), 3) if lat else 0,
        },
        "versions": {
            "intent_router": INTENT_VER,
            "relationship_router": REL_VER,
            "validator": VALIDATOR_VERSION,
        },
    }


def _write_samples_md(rows: List[Dict[str, Any]], path: Path) -> None:
    """Pick representative success + failure cases for the appendix."""
    successes_real = [r for r in rows if r["source"] == "real"
                      and r["routing_status"] == "PASS"
                      and r["confidence"] and r["confidence"] >= 0.6][:8]
    failures_real = [r for r in rows if r["source"] == "real"
                     and (r["routing_status"] == "FAIL"
                          or r["predicted_domain"] == "general")][:8]
    fp_rel = [r for r in rows if r["predicted_domain"] == "relationship"
              and not r["rel_target_resolved"]
              and r["explicit_target_id"] is None][:5]
    unresolved = [r for r in rows if r["target_resolution_status"] == "UNRESOLVED_NAMED"][:5]

    def fmt(r):
        rp = r.get("rel_proposed_action")
        rp_str = f"  - proposed_action: `{rp}`" if rp else ""
        return (
            f"- `{r['source']}` / `{r['collection']}` / frame=`{r['active_frame']}`"
            f"\n  - **msg**: {r['message'][:200]}"
            f"\n  - predicted=`{r['predicted_domain']}`  conf={r['confidence']}  "
            f"signal={r['signal_strength']}  margin={r['margin']}"
            f"\n  - routing=`{r['routing_status']}`  retrieval=`{r['retrieval_status']}`  "
            f"target=`{r['target_resolution_status']}`"
            + (rp_str if rp_str else "")
        )

    parts = ["# B2 Replay Samples\n",
             "_Companion to `B2_READINESS_REPORT.md`._\n",
             "## Representative success cases (REAL)\n"]
    parts.append("\n".join(fmt(r) for r in successes_real) or "_(none)_")
    parts.append("\n\n## Representative failure cases (REAL)\n")
    parts.append("\n".join(fmt(r) for r in failures_real) or "_(none)_")
    parts.append("\n\n## False-positive relationship routing samples\n")
    parts.append("\n".join(fmt(r) for r in fp_rel) or "_(none)_")
    parts.append("\n\n## Unresolved-named-target samples (with proposed_action)\n")
    parts.append("\n".join(fmt(r) for r in unresolved) or "_(none)_")
    path.write_text("\n".join(parts))


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    ap.add_argument("--target-total", type=int, default=120,
                    help="Target replay corpus size (real first, synth fills the gap)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]

    real_rows = await _pull_real(db, args.window_days)
    print(f"Pulled {len(real_rows)} real rows from the last {args.window_days} days.")

    needed = max(0, args.target_total - len(real_rows))
    synth_rows = _load_synth_supplement(target_min=needed) if needed > 0 else []
    print(f"Supplementing with {len(synth_rows)} synthetic rows to reach target ~{args.target_total}.")

    corpus = real_rows + synth_rows
    print(f"Total replay corpus: {len(corpus)} cases "
          f"({len(real_rows)} real / {len(synth_rows)} synth)")

    # Run every case.
    t0 = time.perf_counter()
    results = [_run_one(r) for r in corpus]
    dt = time.perf_counter() - t0
    print(f"Replay complete in {dt*1000:.1f} ms.")

    agg = _aggregate(results)

    # Aggregates per source (so the readiness report can ground in REAL only)
    real_results = [r for r in results if r["source"] == "real"]
    synth_results = [r for r in results if r["source"] == "synth"]
    agg["aggregates_by_source"] = {
        "real": _aggregate(real_results),
        "synth": _aggregate(synth_results),
    }

    out_doc = {
        "generated_at": datetime.now(dt_tz.utc).isoformat(),
        "window_days": args.window_days,
        "target_total": args.target_total,
        "aggregate": agg,
        "rows": results,
    }
    RESULTS_JSON.write_text(json.dumps(out_doc, indent=2, default=str))
    print(f"Wrote {RESULTS_JSON}")

    _write_samples_md(results, SAMPLES_MD)
    print(f"Wrote {SAMPLES_MD}")

    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
