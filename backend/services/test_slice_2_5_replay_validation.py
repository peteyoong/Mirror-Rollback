"""Slice 2.5 — Relationship Field Replay Validation.

Replays five real-world query phrasings against three real family
members (Mel, Thaddeus, Isaac) and asserts the stance invariants hold
across all phrasings.

The resolver MUST return:
    Mel        → relationship_stance == "covenant_partner"   (×5)
    Thaddeus   → relationship_stance == "steward_guardian"   (×5)
    Isaac      → relationship_stance == "steward_guardian"   (×5)

For every turn we ALSO capture (informational):
    relationship_field_v2
    relationship_resolution
    intent_envelope        (router output)
    target / role / stance
    life_domain (primary_domain)
    FKR signal (heuristic from receipt)

Run:
    cd /app/backend && python -m pytest \
        services/test_slice_2_5_replay_validation.py -v -s

Generates:
    /app/backend/audit_reports/SLICE_2_5_REPLAY_RUN.json
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import urllib.request
from typing import Any

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

# Five real-world phrasings to replay against each family member.
PHRASINGS = [
    "Tell me about {name}.",
    "What does {name} need from me?",
    "How does {name} experience me?",
    "What am I missing about {name}?",
    "What is happening between {name} and I today?",
]

# (target_id, target_name, expected_role, expected_stance)
TARGETS = [
    (MEL_ID,      "Mel",      "spouse", "covenant_partner"),
    (THADDEUS_ID, "Thaddeus", "child",  "steward_guardian"),
    (ISAAC_ID,    "Isaac",    "child",  "steward_guardian"),
]

RUN_REPORT_PATH = os.path.join(
    ROOT, "audit_reports", "SLICE_2_5_REPLAY_RUN.json",
)


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

def _post(payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API, data=data, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def _latest_receipt_for(user_id: str, request_id: str | None = None) -> dict | None:
    load_dotenv(os.path.join(ROOT, ".env"))
    client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = client[os.environ["DB_NAME"]]

    async def _q():
        q: dict[str, Any] = {"user_id": user_id}
        if request_id:
            q["request_id"] = request_id
        return await db.mirror_chat_retrieval_receipts.find_one(
            q, sort=[("computed_at", -1)],
        )

    try:
        return asyncio.run(_q())
    finally:
        client.close()


def _summarise(turn_idx: int, target_name: str, phrasing: str,
               receipt: dict) -> dict:
    rfv2 = receipt.get("relationship_field_v2") or {}
    rel  = receipt.get("relationship_resolution") or {}
    env  = receipt.get("intent_envelope") or {}

    # FKR signal — we look for the bridge marker the FKR layer writes
    # into the receipt when it activates.
    fkr_active = bool(
        rel.get("relationship_source") == "forum_relationship_edges"
        or rel.get("role")
        or rel.get("forum_id")
    )

    return {
        "turn":           turn_idx,
        "target":         target_name,
        "phrasing":       phrasing,
        "request_id":     receipt.get("request_id"),
        # router output
        "primary_domain": env.get("primary_domain"),
        "signal_strength": env.get("signal_strength"),
        "margin":         env.get("margin"),
        "lens_priority":  env.get("lens_priority"),
        # relationship_resolution (legacy)
        "rel_resolution_source": rel.get("relationship_source"),
        "rel_resolution_role":   rel.get("role")
                                  or rel.get("relationship_role"),
        # FKR — best-effort heuristic from receipt
        "fkr_signal_present":    fkr_active,
        # RFv2 envelope
        "rfv2_target_user_id":   rfv2.get("target_user_id"),
        "rfv2_target_name":      rfv2.get("target_name"),
        "rfv2_role":             rfv2.get("relationship_role"),
        "rfv2_stance":           rfv2.get("relationship_stance"),
        "rfv2_directionality":   rfv2.get("directionality"),
        "rfv2_active_frame":     rfv2.get("active_frame"),
        "rfv2_source":           rfv2.get("resolution_source"),
        "rfv2_confidence":       rfv2.get("confidence"),
        "rfv2_conflicts":        rfv2.get("conflicts"),
        "rfv2_resolution_path":  rfv2.get("resolution_path"),
    }


# ════════════════════════════════════════════════════════════════════
# The replay
# ════════════════════════════════════════════════════════════════════

def _build_cases():
    cases = []
    for target_id, target_name, exp_role, exp_stance in TARGETS:
        for phrasing in PHRASINGS:
            cases.append((
                target_id, target_name, exp_role, exp_stance,
                phrasing.format(name=target_name),
            ))
    return cases


@pytest.fixture(scope="module")
def replay_run():
    """Run the full 15-turn replay once and yield the row list."""
    cases = _build_cases()
    rows: list[dict] = []
    for i, (tid, tname, exp_role, exp_stance, msg) in enumerate(cases, start=1):
        payload = {
            "user_id":          PETE_ID,
            "message":          msg,
            "about_person_id":  tid,
            "include_history":  False,
            "include_journal":  False,
        }
        status, _ = _post(payload)
        assert status == 200, (
            f"Turn {i}/{len(cases)} (target={tname}, phrasing={msg!r}) "
            f"returned HTTP {status}"
        )
        # Persistence is fire-and-forget — let it commit.
        time.sleep(1.6)
        receipt = _latest_receipt_for(PETE_ID)
        assert receipt is not None, f"No receipt persisted for turn {i}"
        row = _summarise(i, tname, msg, receipt)
        row["expected_role"]   = exp_role
        row["expected_stance"] = exp_stance
        rows.append(row)

    # Persist the run as a structured JSON dump so the .md report and
    # human reviewers can audit it deterministically.
    os.makedirs(os.path.dirname(RUN_REPORT_PATH), exist_ok=True)
    with open(RUN_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "viewer_user_id": PETE_ID,
            "targets":        [t[1] for t in TARGETS],
            "phrasings":      PHRASINGS,
            "total_turns":    len(rows),
            "rows":           rows,
        }, f, indent=2, default=str)

    yield rows


# ════════════════════════════════════════════════════════════════════
# Acceptance
# ════════════════════════════════════════════════════════════════════

def test_acceptance_stance_invariants(replay_run):
    """Hard acceptance: every Mel turn must be covenant_partner;
    every Thaddeus and Isaac turn must be steward_guardian.

    No phrasing drift allowed."""
    drift = [r for r in replay_run if r["rfv2_stance"] != r["expected_stance"]]
    if drift:
        msg = ["stance drift detected:"]
        for r in drift:
            msg.append(
                f"  turn {r['turn']:>2} target={r['target']:<10} "
                f"phrasing={r['phrasing']!r:<55} "
                f"got_stance={r['rfv2_stance']!r:<20} "
                f"expected={r['expected_stance']!r}"
            )
        pytest.fail("\n".join(msg))


def test_acceptance_role_invariants(replay_run):
    drift = [r for r in replay_run if r["rfv2_role"] != r["expected_role"]]
    if drift:
        msg = ["role drift detected:"]
        for r in drift:
            msg.append(
                f"  turn {r['turn']:>2} target={r['target']:<10} "
                f"got_role={r['rfv2_role']!r} "
                f"expected={r['expected_role']!r}"
            )
        pytest.fail("\n".join(msg))


def test_acceptance_target_binding(replay_run):
    """Every turn must bind to the correct target_user_id (the explicit
    about_person_id we passed)."""
    expected_id = {
        "Mel":      MEL_ID,
        "Thaddeus": THADDEUS_ID,
        "Isaac":    ISAAC_ID,
    }
    drift = [
        r for r in replay_run
        if r["rfv2_target_user_id"] != expected_id[r["target"]]
    ]
    if drift:
        msg = ["target binding drift:"]
        for r in drift:
            msg.append(
                f"  turn {r['turn']:>2} target={r['target']} "
                f"got_id={r['rfv2_target_user_id']!r} "
                f"expected={expected_id[r['target']]!r}"
            )
        pytest.fail("\n".join(msg))


def test_acceptance_high_confidence_source(replay_run):
    """Every family-bound turn must come from forum_relationship_edges
    with confidence ≥ 0.95."""
    weak = [
        r for r in replay_run
        if r["rfv2_source"] != "forum_relationship_edges"
        or (r["rfv2_confidence"] or 0) < 0.95
    ]
    if weak:
        msg = ["resolver weak-binding:"]
        for r in weak:
            msg.append(
                f"  turn {r['turn']:>2} target={r['target']:<10} "
                f"source={r['rfv2_source']!r} conf={r['rfv2_confidence']!r}"
            )
        pytest.fail("\n".join(msg))


def test_acceptance_directionality_invariants(replay_run):
    """Mel (spouse) → SYMMETRIC. Thaddeus/Isaac (child) → USER_AS_GIVER."""
    expected_dir = {
        "Mel":      "SYMMETRIC",
        "Thaddeus": "USER_AS_GIVER",
        "Isaac":    "USER_AS_GIVER",
    }
    drift = [
        r for r in replay_run
        if r["rfv2_directionality"] != expected_dir[r["target"]]
    ]
    if drift:
        msg = ["directionality drift:"]
        for r in drift:
            msg.append(
                f"  turn {r['turn']:>2} target={r['target']:<10} "
                f"got={r['rfv2_directionality']!r} "
                f"expected={expected_dir[r['target']]!r}"
            )
        pytest.fail("\n".join(msg))


def test_acceptance_endpoint_health(replay_run):
    """All 15 turns must return HTTP 200 and yield a non-empty receipt."""
    assert len(replay_run) == 15
    for r in replay_run:
        assert r["request_id"], f"turn {r['turn']} has no request_id"
        assert r["rfv2_stance"], f"turn {r['turn']} missing stance"
