"""
FKR v1 — Acceptance Criteria Probes
====================================

5 probes covering the modes mandated by the FKR v1 spec.  Each probe
asserts that the EVIDENCE BLOCK contains the canonical stored value
BEFORE the LLM is called (so the LLM cannot hallucinate around it).

We DO NOT invoke the LLM here.  We only verify the deterministic
retrieval surface — which is what FKR v1 is contractually responsible
for.  LLM behaviour is exercised separately via the
testing_agent integration pass.

Run:
    cd /app/backend && python scripts/fkr_v1_acceptance_probes.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient

from services.forum_chat_knowledge_retrieval import (
    build_fkr_evidence_block,
    classify_query,
    resolve_targets,
)


PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID  = "697ec826ad4b18f75bf42616"


async def _find_thaddeus(db) -> str:
    u = await db.users.find_one(
        {"$or": [
            {"name":       {"$regex": "thaddeus", "$options": "i"}},
            {"first_name": {"$regex": "thaddeus", "$options": "i"}},
        ]}
    )
    return str(u["_id"]) if u else ""


async def _expected_thaddeus_cross(db) -> str:
    tid = await _find_thaddeus(db)
    if not tid:
        return ""
    ch = await db.charts.find_one({"user_id": tid})
    if not ch:
        return ""
    hd = (ch.get("human_design") or {})
    ic = hd.get("incarnation_cross") or {}
    if isinstance(ic, str):
        return ic
    return (ic.get("name") or ic.get("cross_name") or "")


async def run_probe(*, db, name: str, user_id: str, message: str,
                    expected_modes: List[str],
                    must_contain: List[str],
                    must_not_contain: List[str],
                    forum_id: str | None = None
                    ) -> Dict[str, Any]:
    modes = classify_query(message)
    targets = await resolve_targets(
        db=db, user_id=user_id, message=message, forum_id=forum_id,
    )
    block, debug = await build_fkr_evidence_block(
        db=db, user_id=user_id, message=message, forum_id=forum_id,
    )
    res: Dict[str, Any] = {
        "name": name,
        "message": message,
        "asker": user_id,
        "forum_id": forum_id,
        "classified_modes": modes,
        "expected_modes": expected_modes,
        "targets": [
            {"name": t.get("name"), "role": t.get("role"),
             "source": t.get("source")}
            for t in targets
        ],
        "block_emitted": debug.get("emitted"),
        "block_chars": debug.get("block_chars"),
        "must_contain": must_contain,
        "must_not_contain": must_not_contain,
        "checks": {},
        "errors": debug.get("errors", []),
    }
    # Mode-classification check (at least one expected mode hit).
    res["checks"]["modes_overlap"] = bool(set(expected_modes) & set(modes)) \
        if expected_modes else True
    # Evidence containment checks.
    if not block:
        res["checks"]["must_contain"] = {x: False for x in must_contain}
        res["checks"]["must_not_contain"] = {x: True for x in must_not_contain}
        res["block_preview"] = None
    else:
        res["checks"]["must_contain"] = {
            x: (x.lower() in block.lower()) for x in must_contain
        }
        res["checks"]["must_not_contain"] = {
            x: (x.lower() not in block.lower()) for x in must_not_contain
        }
        res["block_preview"] = block[:1200]
    # Pass when all checks are truthy.
    res["pass"] = (
        res["checks"]["modes_overlap"]
        and all(res["checks"]["must_contain"].values())
        and all(res["checks"]["must_not_contain"].values())
    )
    return res


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "test_database")]

    expected_cross = await _expected_thaddeus_cross(db)
    print(f"[fixture] Thaddeus stored Incarnation Cross = {expected_cross!r}")

    probes = []

    # PROBE 1 — CRITICAL: FACT_LOOKUP for Thaddeus's Incarnation Cross.
    # MUST inject the exact stored cross name; MUST NOT inject "Sphinx".
    probes.append(await run_probe(
        db=db,
        name="P1.FACT_LOOKUP — Thaddeus incarnation cross",
        user_id=PETE_ID,
        message="What is Thaddeus's Incarnation Cross?",
        expected_modes=["FACT_LOOKUP"],
        must_contain=[
            "FKR v1",
            "Incarnation Cross",
            expected_cross or "Sleeping Phoenix",
        ],
        must_not_contain=["Right Angle Cross of the Sphinx"],
    ))

    # PROBE 2 — FACT_LOOKUP for asker's own MC / Sun / Moon.
    probes.append(await run_probe(
        db=db,
        name="P2.FACT_LOOKUP — asker self placements",
        user_id=PETE_ID,
        message="What is my Midheaven, Sun and Moon?",
        expected_modes=["FACT_LOOKUP"],
        must_contain=["FKR v1", "ASKER", "Sun", "Moon"],
        must_not_contain=[],
    ))

    # PROBE 3 — RELATIONSHIP (Pete↔Mel).
    probes.append(await run_probe(
        db=db,
        name="P3.RELATIONSHIP — Pete and Mel dynamic",
        user_id=PETE_ID,
        message="How does Mel's chart map to me in our relationship?",
        expected_modes=["RELATIONSHIP"],
        must_contain=["FKR v1", "Mel", "ASKER"],
        must_not_contain=[],
    ))

    # PROBE 4 — COMPARISON (Pete vs Mel).
    probes.append(await run_probe(
        db=db,
        name="P4.COMPARISON — Pete vs Mel",
        user_id=PETE_ID,
        message="Compare my Sun and Moon with Mel's.",
        expected_modes=["COMPARISON", "FACT_LOOKUP"],
        must_contain=["FKR v1", "Mel"],
        must_not_contain=[],
    ))

    # PROBE 5 — TIMELINE (asker).
    probes.append(await run_probe(
        db=db,
        name="P5.TIMELINE — what is emerging for me",
        user_id=PETE_ID,
        message="What transits are emerging for me right now?",
        expected_modes=["TIMELINE"],
        must_contain=["FKR v1"],
        must_not_contain=[],
    ))

    out = {
        "fixture_expected_thaddeus_cross": expected_cross,
        "probes": probes,
        "summary": {
            "total": len(probes),
            "passed": sum(1 for p in probes if p["pass"]),
            "failed": sum(1 for p in probes if not p["pass"]),
        },
    }
    print(json.dumps(out, indent=2, default=str))
    return out


if __name__ == "__main__":
    asyncio.run(main())
