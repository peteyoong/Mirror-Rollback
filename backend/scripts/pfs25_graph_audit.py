"""PFS-2.5 production relationship graph inventory + coverage audit.

Read-only. Designed to be pointed at EITHER Preview (default) OR
Production by overriding MONGO_URL / DB_NAME at the shell. Produces:

  * full edge inventory (source_user, target_user, role, confidence,
    inferred, forum_name)
  * resolved_bucket per edge (using PFS-2.3 lexicon)
  * role_type distribution
  * forum-member-without-edge gap analysis
  * duplicate / contradictory / ambiguous edge detection
  * unknown_role_token frequency in mirror_chat_retrieval_receipts

USAGE:
  # Preview (default)
  python scripts/pfs25_graph_audit.py

  # Production (operator only — supply read-only URI)
  MONGO_URL='mongodb+srv://...' DB_NAME='prod_db' \
      python scripts/pfs25_graph_audit.py
"""
import asyncio
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services.relationship_orchestration_v1 import (  # noqa: E402
    plan_lens_priority,
    DOMAIN_BIAS,
)


SPECIAL_FOCUS_ROLES = {
    "spouse", "child", "cofounder", "advisor",
    "mentor", "investor", "forum_member", "forum_mate",
}


def _bucket_for(role: str) -> Dict[str, str]:
    """Resolve role through the live PFS-2.3 planner to get bucket/framing."""
    plan = plan_lens_priority(
        intent_envelope={"primary_domain": "general",
                         "lens_priority": ["astrology", "human_design",
                                           "enneagram", "numerology",
                                           "relationship", "timeline"]},
        relationship_role=role,
        target_resolved="x-001",
    )
    return {
        "bucket":       plan.get("rule_bucket"),
        "framing":      plan.get("framing_hint"),
        "domain_bias":  plan.get("domain_bias"),
    }


def _je(o: Any) -> Any:
    if isinstance(o, dict): return {k: _je(v) for k, v in o.items()}
    if isinstance(o, list): return [_je(v) for v in o]
    if isinstance(o, datetime): return o.isoformat()
    return o


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    print(f"# PFS-2.5 production graph audit")
    print(f"# DB={os.environ['DB_NAME']}")
    print(f"# run_at={datetime.utcnow().isoformat()}Z\n")

    # ── 1. Edge inventory ─────────────────────────────────────────────
    edges: List[Dict[str, Any]] = []
    async for e in db.forum_relationship_edges.find():
        e.pop("_id", None)
        edges.append(e)
    print(f"## edge inventory ({len(edges)} total)")

    # Hydrate forum names & user names for readability.
    forums: Dict[str, str] = {}
    async for f in db.forums.find():
        forums[str(f.get("_id"))] = f.get("name") or "(unnamed)"
    user_names: Dict[str, str] = {}
    async for u in db.users.find({}, {"name": 1, "email": 1}):
        user_names[str(u.get("_id"))] = (u.get("name")
                                          or u.get("email") or "(unknown)")

    inventory: List[Dict[str, Any]] = []
    for e in edges:
        b = _bucket_for(e.get("role_type", ""))
        inventory.append({
            "forum_id":         e.get("forum_id"),
            "forum_name":       forums.get(str(e.get("forum_id"))),
            "source_user_id":   e.get("from_user_id"),
            "source_user_name": user_names.get(str(e.get("from_user_id"))),
            "target_user_id":   e.get("to_user_id"),
            "target_user_name": user_names.get(str(e.get("to_user_id"))),
            "stored_role":      e.get("role_type"),
            "resolved_bucket":  b["bucket"],
            "resolved_framing": b["framing"],
            "domain_bias":      b["domain_bias"],
            "topology_confidence": e.get("confidence"),
            "topology_inferred":   e.get("inferred"),
            "edge_id":          e.get("id"),
            "created_at":       e.get("created_at"),
        })
    print(json.dumps(_je(inventory), indent=2, default=str))

    # ── 2. Role distribution ──────────────────────────────────────────
    role_counter = Counter(e["stored_role"] for e in inventory)
    bucket_counter = Counter(e["resolved_bucket"] for e in inventory)
    confidence_counter = Counter(e["topology_confidence"] for e in inventory)
    inferred_counter = Counter(str(e["topology_inferred"]) for e in inventory)
    print("\n## role_type distribution")
    print(json.dumps(dict(role_counter), indent=2))
    print("\n## resolved_bucket distribution")
    print(json.dumps(dict(bucket_counter), indent=2))
    print("\n## confidence distribution")
    print(json.dumps(dict(confidence_counter), indent=2))
    print("\n## inferred flag distribution")
    print(json.dumps(dict(inferred_counter), indent=2))

    # ── 3. Special-focus coverage ─────────────────────────────────────
    print("\n## SPECIAL FOCUS coverage")
    coverage: Dict[str, int] = {}
    for r in sorted(SPECIAL_FOCUS_ROLES):
        coverage[r] = role_counter.get(r, 0)
    print(json.dumps(coverage, indent=2))

    # ── 4. Duplicates / ambiguities / contradictions ──────────────────
    keyed: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for e in inventory:
        keyed[(e["forum_id"], e["source_user_id"],
               e["target_user_id"])].append(e)
    duplicates: List[Dict[str, Any]] = []
    contradictions: List[Dict[str, Any]] = []
    for key, lst in keyed.items():
        if len(lst) > 1:
            roles = {x["stored_role"] for x in lst}
            if len(roles) == 1:
                duplicates.append({"key": key, "count": len(lst),
                                   "role": list(roles)[0]})
            else:
                contradictions.append({"key": key, "count": len(lst),
                                       "roles": list(roles)})
    # Inverse-direction inconsistency: A→B exists but B→A does not.
    inverse_missing: List[Dict[str, Any]] = []
    pair_keys = {(e["forum_id"], e["source_user_id"], e["target_user_id"]):
                 e["stored_role"] for e in inventory}
    for k, role in pair_keys.items():
        fid, src, tgt = k
        if (fid, tgt, src) not in pair_keys:
            inverse_missing.append({
                "forum_id": fid, "from": src, "to": tgt, "role": role
            })
    print(f"\n## duplicates: {len(duplicates)}")
    print(json.dumps(_je(duplicates), indent=2, default=str))
    print(f"\n## contradictions (same pair, different role): {len(contradictions)}")
    print(json.dumps(_je(contradictions), indent=2, default=str))
    print(f"\n## inverse-direction missing: {len(inverse_missing)}")
    print(json.dumps(_je(inverse_missing[:50]), indent=2, default=str))

    # ── 5. Forum members without an outbound edge ─────────────────────
    print("\n## FORUM-MEMBER-WITHOUT-EDGE gap analysis")
    members_by_forum: Dict[str, List[str]] = defaultdict(list)
    async for m in db.forum_members.find({}, {"forum_id": 1, "user_id": 1}):
        members_by_forum[str(m["forum_id"])].append(str(m["user_id"]))
    edges_keyset = {(str(e["forum_id"]), str(e["source_user_id"]),
                     str(e["target_user_id"])) for e in inventory}
    gaps: List[Dict[str, Any]] = []
    for fid, members in members_by_forum.items():
        fname = forums.get(fid, "(?)")
        for src in members:
            for tgt in members:
                if src == tgt:
                    continue
                if (fid, src, tgt) not in edges_keyset:
                    gaps.append({
                        "forum_id":   fid,
                        "forum_name": fname,
                        "from":       src,
                        "from_name":  user_names.get(src, "(?)"),
                        "to":         tgt,
                        "to_name":    user_names.get(tgt, "(?)"),
                    })
    print(f"  Total ordered (from→to) member pairs WITHOUT an edge: {len(gaps)}")
    # Show first 30
    print(json.dumps(_je(gaps[:30]), indent=2, default=str))

    # ── 6. unknown_role_token frequency ───────────────────────────────
    print("\n## unknown_role_token frequency in mirror_chat_retrieval_receipts")
    total_receipts = await db.mirror_chat_retrieval_receipts.count_documents({})
    n_replanned = await db.mirror_chat_retrieval_receipts.count_documents(
        {"relationship_orchestration_v1.replanned_after_topology": True})
    n_unknown = await db.mirror_chat_retrieval_receipts.count_documents({
        "relationship_orchestration_v1.applied_rules": {
            "$elemMatch": {"$regex": "^self:unknown_role_token:"}
        }
    })
    rate = (n_unknown / n_replanned * 100.0) if n_replanned else 0.0
    print(json.dumps({
        "total_receipts":              total_receipts,
        "replanned_after_topology_T":  n_replanned,
        "unknown_role_token_events":   n_unknown,
        "unknown_rate_pct_of_replanned": round(rate, 2),
        "ungating_threshold_pct":      5.0,
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
