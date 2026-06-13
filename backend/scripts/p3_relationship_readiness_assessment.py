"""
P3 Relationship Orchestration — Readiness Assessment
====================================================

READ-ONLY assessment.  No code paths are mutated, no flags are changed,
no LLM is invoked.  We exercise the deterministic surfaces that drive
relationship-aware answer construction and report pass/fail.

The 5 scoring areas mandated by the assessment ticket:

    1. Retrieval               — does FKR v1 retrieve target evidence?
    2. Target resolution       — are people resolved to user_ids?
    3. Relationship resolution — is the relationship role assigned?
    4. Prompt construction     — does the orchestration plan + intent
                                  v2 prompt block surface the role?
    5. Answer quality          — (proxy) does the prompt block carry
                                  enough MANDATORY enforcement copy to
                                  hold the LLM accountable?
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
    classify_query, resolve_targets, build_fkr_evidence_block,
)
from services.relationship_resolver import resolve_relationship  # type: ignore
from services.relationship_orchestration_v1 import plan_lens_priority


PETE_ID    = "697f0c6abf35c0528ff06954"
MEL_ID     = "697ec826ad4b18f75bf42616"
THAD_ID    = "69dd0b2cc92ba973f8838c11"
ISAAC_ID   = "69dda348de9cb1c83c0780f8"
PAIR_FORUM = "69dd05eaa333335fcbf3ad33"   # Pete & Mel
FAMILY_FORUM = "69dda348de9cb1c83c0780fa" # Yoong family

SCENARIOS: List[Dict[str, Any]] = [
    # ── 1. Spouse ────────────────────────────────────────────────
    {
        "id": "spouse.affect",
        "category": "spouse",
        "asker": PETE_ID,
        "message": "How does Mel affect me?",
        "expected_role": "spouse",
        "expected_bucket": "spouse",
        "expected_target_name": "Mel",
        "expected_modes": ["RELATIONSHIP"],
    },
    {
        "id": "spouse.struggle",
        "category": "spouse",
        "asker": PETE_ID,
        "message": "What do Mel and I struggle with?",
        "expected_role": "spouse",
        "expected_bucket": "spouse",
        "expected_target_name": "Mel",
        "expected_modes": ["RELATIONSHIP"],
    },
    {
        "id": "spouse.lesson_pronoun",
        "category": "spouse",
        "asker": PETE_ID,
        "message": "What is the lesson between us?",
        "expected_role": "spouse",
        "expected_bucket": "spouse",
        "expected_target_name": "Mel",       # spouse auto-bind
        "expected_modes": ["RELATIONSHIP"],
    },
    # ── 2. Parent → Child ───────────────────────────────────────
    {
        "id": "child.thaddeus_need",
        "category": "child",
        "asker": PETE_ID,
        "message": "What does Thaddeus need from me?",
        "expected_role": "child",
        "expected_bucket": "child",
        "expected_target_name": "Thaddeus",
        "expected_modes": ["RELATIONSHIP"],
    },
    {
        "id": "child.isaac_diff",
        "category": "child",
        "asker": PETE_ID,
        "message": "How is Isaac different from me?",
        "expected_role": "child",
        "expected_bucket": "child",
        "expected_target_name": "Isaac",
        "expected_modes": ["COMPARISON"],
    },
    # ── 3. Child ↔ Child ────────────────────────────────────────
    {
        "id": "child_child.compare",
        "category": "child_child",
        "asker": PETE_ID,
        "message": "Compare Isaac and Thaddeus.",
        "expected_role": None,                # both children — sibling pair
        "expected_bucket": None,              # current model has no sibling-pair bucket
        "expected_targets": ["Isaac", "Thaddeus"],
        "expected_modes": ["COMPARISON"],
    },
    {
        "id": "child_child.boys_differ",
        "category": "child_child",
        "asker": PETE_ID,
        "message": "How do the boys differ emotionally?",
        "expected_role": None,
        "expected_bucket": None,
        "expected_targets": [],               # no proper names — relies on "the boys"
        "expected_modes": ["COMPARISON"],
    },
    # ── 4. Forum member (generic) ───────────────────────────────
    {
        "id": "forum_member.jay",
        "category": "forum_member",
        "asker": PETE_ID,
        "message": "How does Jay affect me?",
        "expected_role": None,                # Jay not in Pete's forum
        "expected_bucket": None,
        "expected_target_name": None,
        "expected_modes": ["RELATIONSHIP"],
    },
    # ── 5. Forum dynamics ───────────────────────────────────────
    {
        "id": "forum_dyn.balance",
        "category": "forum_dynamics",
        "asker": PETE_ID,
        "message": "Who balances Mel best?",
        "expected_role": "spouse",            # Mel resolved as spouse
        "expected_bucket": "spouse",
        "expected_target_name": "Mel",
        "expected_modes": ["FORUM_DYNAMICS", "RELATIONSHIP", "FACT_LOOKUP"],
    },
    {
        "id": "forum_dyn.blind_spot",
        "category": "forum_dynamics",
        "asker": PETE_ID,
        "message": "What is this group's blind spot?",
        "forum_id": FAMILY_FORUM,
        "expected_role": None,
        "expected_bucket": "forum_member",    # forum context with no person
        "expected_target_name": None,
        "expected_modes": ["FORUM_DYNAMICS"],
    },
]


async def _name_to_id(db, name: str) -> str:
    """Best-effort resolver: name → user_id (lowercase exact or partial)."""
    if not name:
        return ""
    u = await db.users.find_one({
        "$or": [
            {"name":       {"$regex": f"^{name}$", "$options": "i"}},
            {"first_name": {"$regex": f"^{name}$", "$options": "i"}},
        ]
    })
    if u:
        return str(u["_id"])
    u = await db.users.find_one({
        "$or": [
            {"name":       {"$regex": name, "$options": "i"}},
            {"first_name": {"$regex": name, "$options": "i"}},
        ]
    })
    return str(u["_id"]) if u else ""


async def assess_one(db, sc: Dict[str, Any]) -> Dict[str, Any]:
    asker = sc["asker"]
    forum_id = sc.get("forum_id")
    message = sc["message"]

    # 1. FKR retrieval (this is the prompt-injected evidence layer)
    modes = classify_query(message)
    targets = await resolve_targets(
        db=db, user_id=asker, message=message, forum_id=forum_id,
    )
    fkr_block, fkr_debug = await build_fkr_evidence_block(
        db=db, user_id=asker, message=message, forum_id=forum_id,
    )

    # 2. Relationship resolution (per resolved target)
    rel_role: str | None = None
    rel_source: str | None = None
    rel_target_id: str | None = None
    rel_target_name: str | None = None
    other_targets = [t for t in targets if t.get("source") != "asker"]
    primary_target = other_targets[0] if other_targets else None
    if primary_target:
        rel_target_id = primary_target.get("user_id")
        rel_target_name = primary_target.get("name")
        try:
            rel = await resolve_relationship(
                db=db,
                asker_user_id=asker,
                target_user_id=rel_target_id,
                target_name=rel_target_name,
                forum_id=forum_id,
            )
            rel_role = rel.get("relationship_role")
            rel_source = rel.get("relationship_source")
        except Exception as e:
            rel_source = f"resolver_error:{type(e).__name__}"

    # 3. Orchestration plan
    fake_envelope = {
        "primary_domain":  "relationship",
        "lens_priority":   ["astrology", "human_design", "enneagram",
                            "numerology", "timeline", "relationship"],
        "confidence":      0.7,
    }
    plan = plan_lens_priority(
        intent_envelope=fake_envelope,
        relationship_role=rel_role,
        target_resolved=rel_target_id,
        forum_topology={
            "active_member_id": rel_target_id,
            "members": [{"id": rel_target_id}] if rel_target_id else [],
        } if rel_target_id else None,
        context_mode="forum" if forum_id else "reflection",
    )

    # 4. Scoring
    def _check_modes() -> bool:
        if not sc.get("expected_modes"):
            return True
        return bool(set(sc["expected_modes"]) & set(modes))

    def _check_target() -> bool:
        if "expected_targets" in sc:
            names = {t.get("name") for t in other_targets if t.get("name")}
            want  = set(sc["expected_targets"])
            return want.issubset(names) or (not want and not other_targets)
        if "expected_target_name" in sc:
            want = sc["expected_target_name"]
            if want is None:
                return primary_target is None
            return primary_target is not None and (
                (primary_target.get("name") or "").lower() == (want or "").lower()
            )
        return True

    def _check_role() -> bool:
        want = sc.get("expected_role")
        if want is None:
            return True  # no role expected
        return rel_role == want

    def _check_bucket() -> bool:
        want = sc.get("expected_bucket")
        if want is None:
            return True
        return plan.get("rule_bucket") == want

    def _check_fkr_emitted() -> bool:
        return bool(fkr_debug.get("emitted"))

    def _check_prompt_quality() -> bool:
        if not fkr_block:
            return False
        if "MANDATORY" not in fkr_block:
            return False
        # Specific containment: if expected target named, evidence block
        # MUST include that name.
        want_name = sc.get("expected_target_name")
        if want_name and want_name.lower() not in fkr_block.lower():
            return False
        return True

    scores = {
        "retrieval":          _check_fkr_emitted(),
        "target_resolution":  _check_target(),
        "relationship_resolution": _check_role(),
        "orchestration_bucket":    _check_bucket(),
        "prompt_construction":     _check_prompt_quality(),
        "modes_overlap":           _check_modes(),
    }

    return {
        "id": sc["id"],
        "category": sc["category"],
        "message": message,
        "asker": asker,
        "forum_id": forum_id,
        "modes": modes,
        "targets": [
            {"name": t.get("name"), "role": t.get("role"),
             "source": t.get("source")}
            for t in targets
        ],
        "fkr_block_chars": fkr_debug.get("block_chars"),
        "fkr_emitted": fkr_debug.get("emitted"),
        "relationship": {
            "target_id":   rel_target_id,
            "target_name": rel_target_name,
            "role":        rel_role,
            "source":      rel_source,
        },
        "orchestration": {
            "rule_bucket":     plan.get("rule_bucket"),
            "framing_hint":    plan.get("framing_hint"),
            "domain_bias":     plan.get("domain_bias"),
            "lens_priority_before": plan.get("lens_priority_before"),
            "lens_priority_after":  plan.get("lens_priority_after"),
            "applied_rules":   plan.get("applied_rules"),
            "reordered":       plan.get("reordered"),
        },
        "scores": scores,
        "pass": all(scores.values()),
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    by_cat: Dict[str, Dict[str, int]] = {}
    for r in results:
        c = r["category"]
        if c not in by_cat:
            by_cat[c] = {"total": 0, "passed": 0}
        by_cat[c]["total"] += 1
        if r["pass"]:
            by_cat[c]["passed"] += 1
    score_totals = {
        k: sum(1 for r in results if r["scores"].get(k))
        for k in ("retrieval", "target_resolution",
                  "relationship_resolution", "orchestration_bucket",
                  "prompt_construction", "modes_overlap")
    }
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "by_category": by_cat,
        "score_dimensions": score_totals,
    }


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "test_database")]

    results = []
    for sc in SCENARIOS:
        try:
            results.append(await assess_one(db, sc))
        except Exception as e:
            results.append({
                "id": sc["id"],
                "category": sc["category"],
                "error": f"{type(e).__name__}: {e}",
                "pass": False,
                "scores": {},
            })
    out = {"summary": summarize(results), "results": results}
    print(json.dumps(out, indent=2, default=str))
    return out


if __name__ == "__main__":
    asyncio.run(main())
