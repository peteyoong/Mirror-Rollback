"""production_chat_review.py

Production-review sample generator.

Pulls the most recent N user messages from the live database (chat_history
and forum_chat_messages), runs them through intent_router_v2 +
relationship_router_v2, and writes a side-by-side report so we can
manually verify that v2 is producing better context, not just different
labels.  Read-only against the DB.

Usage:
    python tools/production_chat_review.py --limit 30 --out audit_reports/v2_production_review.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services.intent_router_v2 import classify_intent_v2  # noqa: E402
from services.relationship_router_v2 import resolve_relationship_context  # noqa: E402
from services.retrieval_validation_v1 import build_receipt, mandatory_modules  # noqa: E402


async def fetch_chat_history_messages(db, limit: int) -> List[Dict[str, Any]]:
    """Walk back from the latest chat_history docs, return user turns."""
    docs = await db["chat_history"].find().sort("updated_at", -1).to_list(length=200)
    out: List[Dict[str, Any]] = []
    for d in docs:
        uid = d.get("user_id")
        for m in (d.get("messages") or []):
            if (m.get("role") == "user") and (m.get("content") or "").strip():
                out.append({
                    "source": "chat_history",
                    "user_id": uid,
                    "timestamp": str(m.get("timestamp")),
                    "text": m["content"],
                    "frame": "self",
                    "target_id": None,
                    "target_name": None,
                })
                if len(out) >= limit:
                    return out
    return out


async def fetch_forum_messages(db, limit: int) -> List[Dict[str, Any]]:
    docs = await db["forum_chat_messages"].find().sort("timestamp", -1).to_list(length=limit)
    out: List[Dict[str, Any]] = []
    for d in docs:
        msg = (d.get("message") or "").strip()
        if not msg:
            continue
        mode = (d.get("mode") or "self").lower()
        # forum_chat_messages.mode ∈ {self, member, forum}
        frame = "forum" if mode == "forum" else ("member" if mode == "member" else "self")
        target_id = d.get("target_member_id")
        target_id = None if target_id in (None, "None", "") else target_id
        out.append({
            "source": "forum_chat_messages",
            "user_id": d.get("user_id"),
            "timestamp": str(d.get("timestamp")),
            "text": msg,
            "frame": frame,
            "target_id": target_id,
            "target_name": d.get("target_member_name"),
        })
    return out


async def saved_people_for(db, user_id: str) -> List[Dict[str, Any]]:
    """Best-effort lookup of saved people for a user."""
    if not user_id:
        return []
    try:
        doc = await db["people"].find_one({"user_id": user_id})
        if doc and isinstance(doc.get("people"), list):
            return doc["people"]
    except Exception:
        pass
    return []


def _legacy_label_guess(text: str) -> str:
    """A *very* shallow proxy for what the legacy router might pick — used
    only for human side-by-side comparison.  Not a faithful re-implementation."""
    t = text.lower()
    if any(k in t for k in ("between", " us ", "my partner", "my wife", "my husband")):
        return "relationship?"
    if any(k in t for k in ("my son", "my daughter", "my kid")):
        return "parenting?"
    if any(k in t for k in ("my career", "promotion", "my job", "my role")):
        return "career?"
    if any(k in t for k in ("money", "salary", "finances")):
        return "money?"
    if any(k in t for k in ("purpose", "calling", "meaning")):
        return "purpose?"
    if any(k in t for k in ("stuck", "grow", "transform")):
        return "growth?"
    return "unknown"


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--out", default="audit_reports/v2_production_review.json")
    ap.add_argument("--markdown", default="audit_reports/v2_production_review.md")
    args = ap.parse_args()

    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]

    half = max(args.limit // 2, 1)
    history_msgs = await fetch_chat_history_messages(db, half)
    forum_msgs = await fetch_forum_messages(db, args.limit - len(history_msgs))
    msgs = (history_msgs + forum_msgs)[:args.limit]

    if not msgs:
        print("No production messages found.", file=sys.stderr)
        return 2

    rows: List[Dict[str, Any]] = []
    domain_counts: Counter = Counter()
    routing_counts: Counter = Counter()
    relationship_relevant_count = 0

    for i, m in enumerate(msgs, 1):
        saved = await saved_people_for(db, m.get("user_id") or "")
        env = classify_intent_v2(
            message=m["text"],
            active_frame=m.get("frame") or "self",
            current_target_id=m.get("target_id"),
        )
        rel = resolve_relationship_context(
            self_user_id=m.get("user_id") or "unknown",
            user_message=m["text"],
            active_frame=m.get("frame") or "self",
            target_id=m.get("target_id"),
            saved_people=saved,
        )
        envd = env.to_dict()
        modules = mandatory_modules(envd["primary_domain"])
        receipt = build_receipt(
            request_id=f"prod-review-{i}",
            intent_envelope=envd,
            relationship_resolution=rel.to_dict(),
            modules_invoked=modules,
            payloads={m: {"sim": True} for m in modules},
        )
        domain_counts[envd["primary_domain"]] += 1
        routing_counts[receipt["routing_status"]] += 1
        if envd["relationship_relevant"]:
            relationship_relevant_count += 1

        rows.append({
            "#": i,
            "source": m["source"],
            "timestamp": m["timestamp"],
            "frame": m.get("frame"),
            "target_id": m.get("target_id"),
            "text": m["text"][:280],
            "v2_primary": envd["primary_domain"],
            "v2_secondary": envd["secondary_domains"],
            "v2_signal": envd["signal_strength"],
            "v2_margin": envd["margin"],
            "v2_confidence": envd["confidence"],
            "v2_lens_priority": envd["lens_priority"][:3],
            "v2_relationship_relevant": envd["relationship_relevant"],
            "v2_timeline_relevant": envd["timeline_relevant"],
            "v2_target_resolved": rel.target,
            "v2_resolution_path": rel.resolution_path,
            "routing_status": receipt["routing_status"],
            "retrieval_status": receipt["retrieval_status"],
            "legacy_guess": _legacy_label_guess(m["text"]),
            "fallback_reason": (envd.get("evidence") or {}).get("fallback_reason"),
        })

    summary = {
        "generated_at": datetime.now(dt_tz.utc).isoformat(),
        "sample_size": len(rows),
        "sources": dict(Counter(r["source"] for r in rows)),
        "v2_domain_counts": dict(domain_counts),
        "routing_status_counts": dict(routing_counts),
        "relationship_relevant_pct": round(relationship_relevant_count / len(rows), 4),
        "avg_signal_strength": round(
            sum(r["v2_signal"] for r in rows) / len(rows), 4),
        "avg_confidence": round(
            sum(r["v2_confidence"] for r in rows) / len(rows), 4),
        "rows": rows,
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"JSON written → {args.out}")

    # Human-readable markdown
    with open(args.markdown, "w") as f:
        f.write(f"# Mirror Chat V2 — Production Review Sample\n\n")
        f.write(f"Generated: {summary['generated_at']}\n\n")
        f.write(f"- Sample size: **{summary['sample_size']}**\n")
        f.write(f"- Sources: {summary['sources']}\n")
        f.write(f"- v2 domain distribution: {summary['v2_domain_counts']}\n")
        f.write(f"- Routing status: {summary['routing_status_counts']}\n")
        f.write(f"- relationship_relevant: {summary['relationship_relevant_pct']*100:.1f}%\n")
        f.write(f"- avg signal_strength: {summary['avg_signal_strength']}\n")
        f.write(f"- avg confidence: {summary['avg_confidence']}\n\n")
        f.write("---\n\n")
        for r in rows:
            f.write(f"### {r['#']}. `{r['source']}`  frame=`{r['frame']}`  "
                    f"target=`{r['target_id'] or '—'}`  ({r['timestamp']})\n\n")
            f.write(f"> {r['text']}\n\n")
            f.write(f"- **v2:** `{r['v2_primary']}` → lens={r['v2_lens_priority']}  "
                    f"sec={r['v2_secondary']}  sig={r['v2_signal']}  "
                    f"margin={r['v2_margin']}  conf={r['v2_confidence']}\n")
            f.write(f"- **routing:** {r['routing_status']}  "
                    f"**retrieval:** {r['retrieval_status']}\n")
            f.write(f"- **target resolved:** {r['v2_target_resolved'] or '—'}  "
                    f"via {r['v2_resolution_path']}\n")
            f.write(f"- **legacy heuristic guess:** {r['legacy_guess']}\n")
            f.write(f"- **manual review:** [ ] domain ok  [ ] target ok  "
                    f"[ ] context retrieved ok  notes: ___\n\n")
    print(f"Markdown written → {args.markdown}")

    print(f"\nDomains:        {dict(domain_counts)}")
    print(f"Routing status: {dict(routing_counts)}")
    print(f"relationship_relevant: "
          f"{relationship_relevant_count}/{len(rows)} "
          f"({relationship_relevant_count*100/len(rows):.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
