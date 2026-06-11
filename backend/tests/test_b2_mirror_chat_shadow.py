"""B2 — Mirror Chat V2 shadow-mode missing-target validation.

Validates that POST /api/mirror/chat is unaffected by the new B2 routing
additions, but that the shadow `mirror_chat_retrieval_receipts` document
correctly carries the new target-resolution telemetry.
"""
from __future__ import annotations

import os
import time
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://birth-data-remediate.preview.emergentagent.com",
).rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

PETE_USER_ID = "697f0c6abf35c0528ff06954"
# Pick any saved-person record on Pete to drive the "explicit target" path.
# (Mel is not in Pete's saved_people in this DB, so we use "Test Spouse"
# whose id is stable in the seed.)
PETE_TEST_SPOUSE_PERSON_ID = "6a0b0ac57a933e4a69a5183b"


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _wait_for_receipt(db, user_id: str, since_ts: float, timeout: float = 12.0):
    """Poll the receipts collection for a new doc inserted after since_ts."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        cur = db.mirror_chat_retrieval_receipts.find(
            {"user_id": user_id}
        ).sort("computed_at", -1).limit(1)
        for r in cur:
            # ISO string compare is safe within seconds here
            if r.get("computed_at", "") >= since_ts:
                return r
        time.sleep(0.5)
    return None


# ------------------------------------------------------------------
# 1. Backend health
# ------------------------------------------------------------------
def test_health_ok(api):
    r = api.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200, r.text


# ------------------------------------------------------------------
# 2. Unresolved proper name → UNRESOLVED_NAMED + proposed_action
# ------------------------------------------------------------------
def test_mirror_chat_unresolved_named_sarah(api, db):
    since = time.strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "user_id": PETE_USER_ID,
        "message": "How does Sarah show up at work?",
        "include_journal": False,
        "include_history": False,
    }
    r = api.post(f"{BASE_URL}/api/mirror/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:500]}"

    body = r.json()
    # Live response must look unchanged (no new B2 fields leaked)
    assert "response" in body and isinstance(body["response"], str) and body["response"]
    assert "session_id" in body
    assert "timestamp" in body
    for forbidden in ("target_unresolved_name", "proposed_action",
                       "target_resolution_status"):
        assert forbidden not in body, (
            f"Live response leaked receipt-only field: {forbidden}"
        )

    # Shadow receipt must surface telemetry
    receipt = _wait_for_receipt(db, PETE_USER_ID, since, timeout=15)
    assert receipt is not None, "No shadow receipt persisted in time"
    rel = receipt.get("relationship_resolution") or {}
    assert rel.get("target_unresolved_name") == "Sarah", rel
    pa = rel.get("proposed_action") or {}
    assert pa.get("type") == "add_to_circle", pa
    assert pa.get("suggested_name") == "Sarah", pa
    assert receipt.get("target_resolution_status") == "UNRESOLVED_NAMED", receipt
    assert receipt.get("target_unresolved_name") == "Sarah"
    assert receipt.get("target_resolved") in (None, ""), receipt.get("target_resolved")


# ------------------------------------------------------------------
# 3. No proper name → no false-fire
# ------------------------------------------------------------------
def test_mirror_chat_no_propername_no_falsefire(api, db):
    since = time.strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "user_id": PETE_USER_ID,
        "message": "Tell me about my chart",
        "include_journal": False,
        "include_history": False,
    }
    r = api.post(f"{BASE_URL}/api/mirror/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:500]}"

    body = r.json()
    assert "response" in body and body["response"]

    receipt = _wait_for_receipt(db, PETE_USER_ID, since, timeout=15)
    assert receipt is not None, "No shadow receipt persisted in time"
    rel = receipt.get("relationship_resolution") or {}
    assert rel.get("target_unresolved_name") is None, rel
    assert rel.get("proposed_action") is None, rel
    # Should not be UNRESOLVED_NAMED — either RESOLVED, UNRESOLVED_NO_NAME,
    # or NOT_APPLICABLE depending on saved_people loading.
    assert receipt.get("target_resolution_status") != "UNRESOLVED_NAMED", receipt
    assert receipt.get("proposed_action") is None
    assert receipt.get("target_unresolved_name") is None


# ------------------------------------------------------------------
# 4. Explicit about_person_id → RESOLVED
# ------------------------------------------------------------------
def test_mirror_chat_explicit_target_resolved(api, db):
    since = time.strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "user_id": PETE_USER_ID,
        "message": "What does today look like for them?",
        "about_person_id": PETE_TEST_SPOUSE_PERSON_ID,
        "include_journal": False,
        "include_history": False,
    }
    r = api.post(f"{BASE_URL}/api/mirror/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"status={r.status_code} body={r.text[:500]}"

    receipt = _wait_for_receipt(db, PETE_USER_ID, since, timeout=15)
    assert receipt is not None, "No shadow receipt persisted in time"
    assert receipt.get("target_resolution_status") == "RESOLVED", receipt
    assert receipt.get("proposed_action") is None, receipt.get("proposed_action")
    rel = receipt.get("relationship_resolution") or {}
    assert rel.get("target") == PETE_TEST_SPOUSE_PERSON_ID, rel
