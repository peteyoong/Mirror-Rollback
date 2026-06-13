"""
Backfill parent/child edges in `forum_relationship_edges`.

Purpose: the P3 readiness assessment found that the canonical
relationship graph is missing parent/child edges for Pete↔Thaddeus and
Pete↔Isaac.  This script ADDS the missing edges only.  It is
idempotent: existing edges are not duplicated or modified.

Scope (per P0 ticket):
  * Pete  → Thaddeus  : role_type=child
  * Thaddeus → Pete   : role_type=parent
  * Pete  → Isaac     : role_type=child
  * Isaac → Pete      : role_type=parent

Constraints respected:
  * No new collections.
  * No schema changes.
  * No edits to existing edges.
  * No relationships beyond parent/child are touched.
  * No flag changes.

Reads:
  * `users` (for `name`, `birth_date` snapshot in source metadata)
  * `forum_relationship_edges` (to detect existing edges)
Writes:
  * `forum_relationship_edges` (insert only when no matching edge exists)

Run:
  cd /app/backend && python scripts/backfill_parent_child_edges.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient


PETE     = "697f0c6abf35c0528ff06954"
THADDEUS = "69dd0b2cc92ba973f8838c11"
ISAAC    = "69dda348de9cb1c83c0780f8"
FAMILY_FORUM = "69dda348de9cb1c83c0780fa"  # Yoong family

EDGES_TO_BACKFILL: List[Tuple[str, str, str]] = [
    (PETE,     THADDEUS, "child"),
    (THADDEUS, PETE,     "parent"),
    (PETE,     ISAAC,    "child"),
    (ISAAC,    PETE,     "parent"),
]


async def _has_existing_edge(
    db, from_uid: str, to_uid: str, forum_id: str
) -> bool:
    # Match either a forum-scoped edge or any global edge between the pair.
    e = await db.forum_relationship_edges.find_one({
        "from_user_id": from_uid,
        "to_user_id":   to_uid,
        "forum_id":     forum_id,
    })
    if e:
        return True
    e = await db.forum_relationship_edges.find_one({
        "from_user_id": from_uid,
        "to_user_id":   to_uid,
    })
    return bool(e)


async def main() -> Dict[str, Any]:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "test_database")]

    actions: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for from_uid, to_uid, role in EDGES_TO_BACKFILL:
        already = await _has_existing_edge(db, from_uid, to_uid, FAMILY_FORUM)
        if already:
            actions.append({
                "from": from_uid, "to": to_uid, "role": role,
                "status": "skipped_exists",
            })
            continue
        doc: Dict[str, Any] = {
            "from_user_id": from_uid,
            "to_user_id":   to_uid,
            "role_type":    role,
            "confidence":   "high",
            "forum_id":     FAMILY_FORUM,
            "source":       "p0_parent_child_backfill",
            "evidence":     "Yoong family forum membership + admin attestation",
            "created_at":   now,
            "updated_at":   now,
        }
        await db.forum_relationship_edges.insert_one(doc)
        actions.append({
            "from": from_uid, "to": to_uid, "role": role,
            "status": "inserted",
        })

    # Verification readout
    final = []
    pairs: Iterable[Tuple[str, str]] = [
        (PETE, THADDEUS), (THADDEUS, PETE),
        (PETE, ISAAC),    (ISAAC, PETE),
    ]
    for a, b in pairs:
        e = await db.forum_relationship_edges.find_one({
            "from_user_id": a, "to_user_id": b,
        })
        final.append({
            "from": a, "to": b,
            "role": e.get("role_type") if e else None,
            "forum_id": e.get("forum_id") if e else None,
            "source":   e.get("source") if e else None,
        })

    summary = {
        "actions": actions,
        "final_state": final,
        "inserted":  sum(1 for a in actions if a["status"] == "inserted"),
        "skipped":   sum(1 for a in actions if a["status"] == "skipped_exists"),
    }
    import json
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    asyncio.run(main())
