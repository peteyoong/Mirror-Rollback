"""Deterministic tests for `relationship_field_v2.resolve_relationship_field`.

Run with:
    cd /app/backend && python -m pytest services/test_relationship_field_v2.py -v

These tests are read-only (no DB writes anywhere) and target the local
`test_database` MongoDB instance which contains Pete's real edge graph:

    Pete (697f0c6a…) → Mel       (697ec826…) spouse  Pete & Mel / Yoong
    Pete             → Thaddeus  (69dd0b2c…) child   Yoong family
    Pete             → Isaac     (69dda348…) child   Yoong family

Slice 1 acceptance criteria (per user directive):
    A1. Mel        → role=spouse, stance=covenant_partner, dir=SYMMETRIC
    A2. Thaddeus   → role=child,  stance=steward_guardian, dir=USER_AS_GIVER
    A3. Isaac      → role=child,  stance=steward_guardian, dir=USER_AS_GIVER
    A4. Patricia   → role=None, stance=neutral, source=proposed_unresolved
    A5. self        → role=self, stance=self_subject, source=self_no_target

Also asserts the guardrails:
    G1. core stance never overridden by provisional
    G2. lexicon-only never auto-binds HIGH-CONFIDENCE
    G4. URL `context` conflict recorded but does not override edges
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Make sibling imports resolve when run from /app/backend
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.relationship_field_v2 import (    # noqa: E402
    resolve_relationship_field,
    CORE_STANCE_MAP,
    PROVISIONAL_STANCE_MAP,
    ResolutionSource,
    ActiveFrame,
    Closeness,
    HIGH_CONFIDENCE_THRESHOLD,
)


# Real edge-graph fixture (from the audit's read-only probe)
PETE_ID     = "697f0c6abf35c0528ff06954"
MEL_ID      = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
ISAAC_ID    = "69dda348de9cb1c83c0780f8"


@pytest.fixture(scope="function")
def db():
    """Per-test Motor client. Each test gets its own client tied to its
    own event loop (each `asyncio.run()` creates a fresh loop, so a
    module-scoped client would error on the 2nd test)."""
    load_dotenv(os.path.join(ROOT, ".env"))
    mongo_url = os.getenv("MONGO_URL")
    assert mongo_url, "MONGO_URL must be set in /app/backend/.env"
    client = AsyncIOMotorClient(mongo_url)
    yield client["test_database"]
    client.close()


# ════════════════════════════════════════════════════════════════════
# A1 — Mel (spouse, covenant_partner)
# ════════════════════════════════════════════════════════════════════

def test_mel_spouse_covenant_partner(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="Tell me about Mel.",
            hints={"about_person_id": MEL_ID},
        )
        assert fld.target_user_id == MEL_ID
        assert fld.relationship_role == "spouse"
        assert fld.relationship_stance == "covenant_partner"
        assert fld.directionality == "SYMMETRIC"
        assert fld.closeness == Closeness.HIGH
        assert fld.emotional_weight == Closeness.HIGH
        assert fld.resolution_source == ResolutionSource.EDGES
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
        assert fld.conflicts == []
        # frame was promoted because explicit about_person_id arrived
        assert fld.active_frame in (ActiveFrame.MEMBER, ActiveFrame.FORUM)
        # Stance audit trail
        assert any("stance:core:spouse->covenant_partner" in r
                   for r in fld.resolution_path)
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# A2 — Thaddeus (child, steward_guardian, USER_AS_GIVER)
# ════════════════════════════════════════════════════════════════════

def test_thaddeus_child_steward_guardian(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What's coming up for Thaddeus this week?",
            hints={"about_person_id": THADDEUS_ID},
        )
        assert fld.target_user_id == THADDEUS_ID
        assert fld.relationship_role == "child"
        assert fld.relationship_stance == "steward_guardian"
        assert fld.directionality == "USER_AS_GIVER"
        assert fld.closeness == Closeness.HIGH
        assert fld.resolution_source == ResolutionSource.EDGES
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
        assert fld.conflicts == []
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# A3 — Isaac (child, steward_guardian) — same shape, different message
# ════════════════════════════════════════════════════════════════════

def test_isaac_child_steward_guardian(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What does Isaac need from me right now?",
            hints={"about_person_id": ISAAC_ID},
        )
        assert fld.target_user_id == ISAAC_ID
        assert fld.relationship_role == "child"
        assert fld.relationship_stance == "steward_guardian"
        assert fld.directionality == "USER_AS_GIVER"
        assert fld.resolution_source == ResolutionSource.EDGES
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# A4 — Patricia (unknown, neutral, proposed_unresolved)
# ════════════════════════════════════════════════════════════════════

def test_patricia_unknown_neutral(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What does Mirror think about Patricia?",
            hints={},
        )
        assert fld.target_user_id is None
        assert fld.relationship_role is None
        assert fld.relationship_stance == "neutral"
        assert fld.directionality is None
        assert fld.resolution_source == ResolutionSource.PROPOSED_UNRESOLVED
        # G2: lexicon-only / proper-name-only must NOT cross the
        # high-confidence threshold.
        assert fld.confidence < HIGH_CONFIDENCE_THRESHOLD
        # The proposed_action should be available for FE consumption
        assert fld.proposed_action is not None
        assert fld.proposed_action["type"] == "add_to_circle"
        assert fld.proposed_action["suggested_name"] == "Patricia"
        # missing_data tag must surface for the dashboard
        assert "target_unresolved" in fld.missing_data
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# A5 — Self (self_subject, no target)
# ════════════════════════════════════════════════════════════════════

def test_self_subject_no_target(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="Tell me about myself.",
            hints={},
        )
        assert fld.target_user_id is None
        assert fld.relationship_role == "self"
        # G3 — self_subject (not null)
        assert fld.relationship_stance == "self_subject"
        assert fld.directionality is None
        assert fld.resolution_source == ResolutionSource.SELF_NO_TARGET
        assert fld.active_frame == ActiveFrame.SELF
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# Guardrails
# ════════════════════════════════════════════════════════════════════

def test_g1_core_stance_frozen_lookup():
    """G1 — every core role-stance pair is present in CORE_STANCE_MAP."""
    expected = {
        "spouse":       "covenant_partner",
        "child":        "steward_guardian",
        "parent":       "lineage_source",
        "sibling":      "shared_origin",
        "close_friend": "chosen_ally",
        "mentor":       "guide",
        "forum_member": "peer",
        "unknown":      "neutral",
    }
    for k, v in expected.items():
        assert CORE_STANCE_MAP[k] == v, (
            f"CORE_STANCE_MAP[{k!r}] expected {v!r} got "
            f"{CORE_STANCE_MAP[k]!r}"
        )


def test_g1_provisional_does_not_collide_with_core_keys():
    """G1 — provisional must not silently replace a core role's stance."""
    for role in CORE_STANCE_MAP:
        if role == "unknown":
            continue
        # If a provisional entry exists for the same role string, it must
        # map to the SAME stance as core (defensive).
        if role in PROVISIONAL_STANCE_MAP:
            assert PROVISIONAL_STANCE_MAP[role] == CORE_STANCE_MAP[role], (
                f"Provisional stance for core role {role!r} differs from "
                f"frozen core. core={CORE_STANCE_MAP[role]!r}, "
                f"prov={PROVISIONAL_STANCE_MAP[role]!r}"
            )


def test_g4_url_context_conflict_recorded_not_overriding_edges(db):
    """G4 — when URL context disagrees with edge graph, edges win and
    the conflict is recorded in `conflicts[]`. No 409, no override."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="Tell me about Mel.",
            hints={
                "about_person_id": MEL_ID,
                "url_context":     "stranger",   # deliberate mismatch
            },
        )
        # Edges still win — role/stance unchanged
        assert fld.relationship_role == "spouse"
        assert fld.relationship_stance == "covenant_partner"
        # Conflict recorded
        assert any("url_context_vs_edge" in c for c in fld.conflicts), (
            f"Expected url_context_vs_edge in conflicts; got {fld.conflicts}"
        )
    asyncio.run(_run())


def test_g4_url_context_synonyms_do_not_trip_conflict(db):
    """G4 — `partner` ~ `spouse` is a known synonym, not a conflict."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="Tell me about Mel.",
            hints={
                "about_person_id": MEL_ID,
                "url_context":     "partner",
            },
        )
        assert fld.relationship_role == "spouse"
        assert fld.conflicts == [], (
            f"partner~spouse should not be a conflict; got {fld.conflicts}"
        )
    asyncio.run(_run())
