"""
Pre-Ungating Validation — Relationship Orchestration LLM Behavior
==================================================================

End-to-end probe through /api/mirror/chat with the LLM in the loop.
For each prompt we capture:
  - the FKR evidence block (deterministic, computed in-process)
  - the LLM response (HTTP POST to local backend)
  - explicit-name checks for Mel / Isaac / Thaddeus
  - generic-language checks ("family members", "someone in", "one of them")
  - role-confusion checks (Thaddeus referred to as spouse, etc.)

Run:
    cd /app/backend && python scripts/preungating_validation_relationship_orchestration.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

from services.forum_chat_knowledge_retrieval import (
    classify_query, resolve_targets, build_fkr_evidence_block,
)


BASE   = os.environ.get("BACKEND_URL", "http://localhost:8001")
PETE   = "697f0c6abf35c0528ff06954"
MEL    = "697ec826ad4b18f75bf42616"
THAD   = "69dd0b2cc92ba973f8838c11"
ISAAC  = "69dda348de9cb1c83c0780f8"
FAMILY = "69dda348de9cb1c83c0780fa"
PAIR   = "69dd05eaa333335fcbf3ad33"

GENERIC_PHRASES = [
    r"\bfamily members?\b",
    r"\bsomeone in your family\b",
    r"\bsomeone in (the|our|your) (family|home)\b",
    r"\bone of (them|the kids|the children|the boys)\b",
    r"\bthe (kid|child|boy|sibling|child in question)\b",  # generic singulars
    r"\bdifferent family members\b",
    r"\bthe people in your (family|life|forum)\b",
    r"\b(another|other) family member\b",
]

PROBES: List[Dict[str, Any]] = [
    # ── The 10 real-world family probes the user requested ──
    {"id": "f1.family_happening",        "msg": "What is happening in our family?",
     "expected_names": ["Mel", "Isaac", "Thaddeus"]},
    {"id": "f2.thad_need",               "msg": "What does Thaddeus need from me?",
     "expected_names": ["Thaddeus"]},
    {"id": "f3.isaac_need",              "msg": "What does Isaac need from me?",
     "expected_names": ["Isaac"]},
    {"id": "f4.boys_differ",             "msg": "How do the boys differ emotionally?",
     "expected_names": ["Isaac", "Thaddeus"]},
    {"id": "f5.more_like_me",            "msg": "Which child is more like me?",
     "expected_names": ["Isaac", "Thaddeus"]},
    {"id": "f6.mel_role_dynamic",        "msg": "What role is Mel playing in the family dynamic?",
     "expected_names": ["Mel"]},
    {"id": "f7.mel_and_boys",            "msg": "What is emerging between Mel and the boys?",
     "expected_names": ["Mel", "Isaac", "Thaddeus"]},
    {"id": "f8.family_blind_spot",       "msg": "What blind spot exists in our family?",
     "expected_names": ["Mel", "Isaac", "Thaddeus"]},
    {"id": "f9.family_growing",          "msg": "Where is the family growing?",
     "expected_names": ["Mel", "Isaac", "Thaddeus"]},
    {"id": "f10.tension_at_home",        "msg": "What tension needs attention at home?",
     "expected_names": ["Mel", "Isaac", "Thaddeus"]},
]

ROLE_CONFUSION_RULES = [
    # role-X should not appear next to person-Y when the truth is role-Z.
    {"text": r"\bThaddeus[^.]{0,40}\bspouse\b",        "violation": "Thaddeus called spouse"},
    {"text": r"\bIsaac[^.]{0,40}\bspouse\b",           "violation": "Isaac called spouse"},
    {"text": r"\bMel[^.]{0,40}\bchild\b",              "violation": "Mel called child"},
    {"text": r"\bMel[^.]{0,40}\b(your )?son\b",        "violation": "Mel called son"},
    {"text": r"\bThaddeus[^.]{0,40}\b(your )?wife\b",  "violation": "Thaddeus called wife"},
    {"text": r"\bIsaac[^.]{0,40}\b(your )?wife\b",     "violation": "Isaac called wife"},
]


def _names_present(text: str, names: List[str]) -> Dict[str, bool]:
    t = (text or "")
    return {n: bool(re.search(rf"\b{re.escape(n)}\b", t, re.IGNORECASE)) for n in names}


def _generic_phrases_found(text: str) -> List[str]:
    """Detect ONLY truly collapsing generic phrases.

    A phrase like 'family members like Thaddeus and Isaac' is NOT a
    collapse — the LLM is being specific, just using a noun phrase to
    introduce the names.  We require a generic phrase to be followed
    by NO specific person name within ~80 chars to count as a real
    collapse.
    """
    t = (text or "")
    found: List[str] = []
    name_re = re.compile(r"\b(Mel|Melissa|Isaac|Thaddeus|Thad|Pete|Peter)\b", re.IGNORECASE)
    for pat in GENERIC_PHRASES:
        for m in re.finditer(pat, t, flags=re.IGNORECASE):
            start, end = m.span()
            # Look 80 chars forward for any specific name; if present,
            # this is a specific-introduction, not a collapse.
            window = t[end : end + 80]
            if not name_re.search(window):
                found.append(m.group(0))
    return found


def _role_confusions(text: str) -> List[str]:
    t = (text or "")
    found = []
    for rule in ROLE_CONFUSION_RULES:
        if re.search(rule["text"], t, re.IGNORECASE):
            found.append(rule["violation"])
    return found


async def _call_mirror(message: str, *, user_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            f"{BASE}/api/mirror/chat",
            json={"user_id": user_id, "message": message, "lens": "generalist"},
        )
        r.raise_for_status()
        return r.json()


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "test_database")]

    results: List[Dict[str, Any]] = []
    for p in PROBES:
        t0 = time.time()
        # ── Capture FKR evidence block deterministically.
        modes = classify_query(p["msg"])
        targets = await resolve_targets(
            db=db, user_id=PETE, message=p["msg"], forum_id=None,
        )
        fkr_block, fkr_debug = await build_fkr_evidence_block(
            db=db, user_id=PETE, message=p["msg"], forum_id=None,
        )
        target_names_emitted = [
            t["name"] for t in fkr_debug.get("targets", [])
            if t.get("source") != "asker"
        ]
        # FKR-level name-presence check: did the block actually carry each
        # expected name?
        block_names_present = _names_present(fkr_block or "", p["expected_names"])

        # ── Now run through the LLM.
        try:
            api_resp = await _call_mirror(p["msg"], user_id=PETE)
            response_text = (api_resp.get("response")
                             or api_resp.get("message")
                             or api_resp.get("text") or "")
        except Exception as e:
            response_text = ""
            api_resp = {"error": f"{type(e).__name__}: {e}"}

        resp_names_present = _names_present(response_text, p["expected_names"])
        generic_hits = _generic_phrases_found(response_text)
        role_confusions = _role_confusions(response_text)

        # Acceptance per probe:
        all_names = all(resp_names_present.values())
        no_generic = (len(generic_hits) == 0)
        no_role = (len(role_confusions) == 0)
        passed = all_names and no_generic and no_role

        results.append({
            "id": p["id"],
            "message": p["msg"],
            "expected_names": p["expected_names"],
            "fkr": {
                "modes": modes,
                "targets": target_names_emitted,
                "block_chars": fkr_debug.get("block_chars"),
                "block_names_present": block_names_present,
                "block_preview": (fkr_block or "")[:1400],
            },
            "llm_response": response_text,
            "checks": {
                "names_in_response": resp_names_present,
                "all_expected_names_present": all_names,
                "generic_phrases_found": generic_hits,
                "no_generic_language": no_generic,
                "role_confusions": role_confusions,
                "no_role_confusion": no_role,
            },
            "pass": passed,
            "duration_s": round(time.time() - t0, 2),
            "raw_api": {k: v for k, v in api_resp.items() if k != "response"},
        })

    summary = {
        "total":   len(results),
        "passed":  sum(1 for r in results if r["pass"]),
        "failed":  sum(1 for r in results if not r["pass"]),
        "fkr_block_complete":  sum(
            1 for r in results
            if all(r["fkr"]["block_names_present"].values())
        ),
        "names_complete_in_response": sum(
            1 for r in results if r["checks"]["all_expected_names_present"]
        ),
        "responses_with_generic_language": sum(
            1 for r in results if r["checks"]["generic_phrases_found"]
        ),
        "responses_with_role_confusion": sum(
            1 for r in results if r["checks"]["role_confusions"]
        ),
    }
    out = {"summary": summary, "results": results}
    print(json.dumps(out, indent=2, default=str))
    return out


if __name__ == "__main__":
    asyncio.run(main())
