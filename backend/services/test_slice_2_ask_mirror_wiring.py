"""Slice 2 acceptance: live POST /api/mirror/chat per scenario, then
read the freshly-persisted receipt and assert the
`relationship_field_v2` envelope.

Run:
    cd /app/backend && python -m pytest services/test_slice_2_ask_mirror_wiring.py -v -s

Hits the LLM (Emergent LLM Key) — keep the message short and pass
include_history=False, include_journal=False to minimise cost.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import urllib.request

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PETE_ID     = "697f0c6abf35c0528ff06954"
MEL_ID      = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
ISAAC_ID    = "69dda348de9cb1c83c0780f8"

API = "http://localhost:8001/api/mirror/chat"


def _post(payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API, data=data, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def _latest_receipt_for(user_id: str) -> dict | None:
    load_dotenv(os.path.join(ROOT, ".env"))
    client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = client[os.environ["DB_NAME"]]
    async def _q():
        return await db.mirror_chat_retrieval_receipts.find_one(
            {"user_id": user_id},
            sort=[("computed_at", -1)],
        )
    try:
        return asyncio.run(_q())
    finally:
        client.close()


def _hit_and_fetch(payload: dict) -> dict:
    """POST and return the freshly-persisted receipt envelope."""
    status, _ = _post(payload)
    assert status == 200, f"Endpoint returned {status}"
    # Persistence is fire-and-forget — wait briefly for the insert.
    time.sleep(1.5)
    r = _latest_receipt_for(payload["user_id"])
    assert r is not None, "No receipt found"
    return r


# ════════════════════════════════════════════════════════════════════
# Acceptance criteria
# ════════════════════════════════════════════════════════════════════

def test_slice2_mel_spouse_covenant_partner():
    receipt = _hit_and_fetch({
        "user_id": PETE_ID, "message": "Tell me about Mel.",
        "about_person_id": MEL_ID,
        "include_history": False, "include_journal": False,
    })
    rfv2 = receipt.get("relationship_field_v2")
    assert rfv2, "relationship_field_v2 missing from receipt"
    assert rfv2["target_user_id"] == MEL_ID
    assert rfv2["relationship_role"] == "spouse"
    assert rfv2["relationship_stance"] == "covenant_partner"
    assert rfv2["directionality"] == "SYMMETRIC"
    assert rfv2["active_frame"] in ("MEMBER", "FORUM")
    assert rfv2["resolution_source"] == "forum_relationship_edges"
    assert rfv2["confidence"] >= 0.95


def test_slice2_thaddeus_child_steward_guardian():
    receipt = _hit_and_fetch({
        "user_id": PETE_ID, "message": "Tell me about Thaddeus.",
        "about_person_id": THADDEUS_ID,
        "include_history": False, "include_journal": False,
    })
    rfv2 = receipt.get("relationship_field_v2")
    assert rfv2
    assert rfv2["relationship_role"] == "child"
    assert rfv2["relationship_stance"] == "steward_guardian"
    assert rfv2["directionality"] == "USER_AS_GIVER"


def test_slice2_isaac_child_steward_guardian():
    receipt = _hit_and_fetch({
        "user_id": PETE_ID, "message": "Tell me about Isaac.",
        "about_person_id": ISAAC_ID,
        "include_history": False, "include_journal": False,
    })
    rfv2 = receipt.get("relationship_field_v2")
    assert rfv2
    assert rfv2["relationship_role"] == "child"
    assert rfv2["relationship_stance"] == "steward_guardian"
    assert rfv2["directionality"] == "USER_AS_GIVER"


def test_slice2_patricia_unknown_neutral():
    receipt = _hit_and_fetch({
        "user_id": PETE_ID, "message": "Tell me about Patricia.",
        "include_history": False, "include_journal": False,
    })
    rfv2 = receipt.get("relationship_field_v2")
    assert rfv2
    assert rfv2["target_user_id"] is None
    assert rfv2["relationship_stance"] == "neutral"
    assert rfv2["resolution_source"] == "proposed_unresolved"
    assert rfv2["confidence"] < 0.70                      # below HIGH
    pa = rfv2.get("proposed_action")
    assert pa and pa.get("type") == "add_to_circle"
    assert pa.get("suggested_name") == "Patricia"


def test_slice2_self_subject():
    receipt = _hit_and_fetch({
        "user_id": PETE_ID, "message": "Tell me about myself.",
        "include_history": False, "include_journal": False,
    })
    rfv2 = receipt.get("relationship_field_v2")
    assert rfv2
    assert rfv2["target_user_id"] is None
    assert rfv2["active_frame"] == "SELF"
    assert rfv2["relationship_stance"] == "self_subject"
    assert rfv2["resolution_source"] == "self_no_target"


# ════════════════════════════════════════════════════════════════════
# Smoke / regression
# ════════════════════════════════════════════════════════════════════

def test_slice2_endpoint_returns_200_no_about_person_no_target_message():
    """Sanity — even when the resolver short-circuits, the endpoint must
    still respond 200 and the receipt persists."""
    status, body = _post({
        "user_id": PETE_ID,
        "message": "What is grounding me today?",
        "include_history": False, "include_journal": False,
    })
    assert status == 200
    assert body and isinstance(body.get("response") or body.get("message") or body.get("data"), (str, dict, list))


def test_slice2_existing_receipt_keys_preserved():
    """Regression — confirm existing receipt schema is intact alongside
    the new key."""
    receipt = _hit_and_fetch({
        "user_id": PETE_ID, "message": "Tell me about Mel.",
        "about_person_id": MEL_ID,
        "include_history": False, "include_journal": False,
    })
    # Established receipt fields must still be present
    for k in (
        "intent_envelope", "relationship_resolution",
        "retrieval_status", "routing_status",
        "mandatory_modules_invoked", "router_version",
    ):
        assert k in receipt, f"missing pre-existing receipt key: {k}"
    # NEW key alongside, not replacing
    assert "relationship_field_v2" in receipt
