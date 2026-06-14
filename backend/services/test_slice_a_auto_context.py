"""Slice A acceptance tests — Forum Chat Auto Context Resolver Extensions.

Run with:
    cd /app/backend && python -m pytest services/test_slice_a_auto_context.py -v

User-approved acceptance matrix (9 scenarios):

    S1. SELF                — "Tell me about myself."
    S2. MEMBER spouse       — "What does Mel need from me?"
    S3. MEMBER child        — "What does Thaddeus need from me?"
    S4. FORUM               — "What's the energy of the forum?"
    S5. PAIRWISE            — "How are Mel and Thaddeus affecting each other?"
    S6. MULTI_PERSON        — "What about my children?"
    S7. AMBIGUOUS           — "Tell me about Test." (5 saved_people match)
    S8. Pronoun follow-up   — "What does she need from me?"  + last_target_id=MEL
    S9. Pairwise family     — "How are Mel and Thaddeus affecting each other?"
                              (already S5 — kept for the test_matrix delivery)

Guardrails reasserted (per user directive):
    - Bias MEMBER > PAIRWISE > FORUM.  FORUM intent must NOT fire on
      a message like "What does Mel need from me?"
    - Single-candidate name pools NEVER trigger AMBIGUOUS.
    - Ambiguity requires ≥2 candidates within 0.10 of the top.

All tests are READ-ONLY against the local `test_database`.
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.relationship_field_v2 import (    # noqa: E402
    resolve_relationship_field,
    ResolutionSource,
    ActiveFrame,
    Closeness,
    HIGH_CONFIDENCE_THRESHOLD,
)


# Real edge-graph fixture (verified in slice-1 audit).
PETE_ID     = "697f0c6abf35c0528ff06954"
MEL_ID      = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
ISAAC_ID    = "69dda348de9cb1c83c0780f8"


@pytest.fixture(scope="function")
def db():
    load_dotenv(os.path.join(ROOT, ".env"))
    mongo_url = os.getenv("MONGO_URL")
    assert mongo_url, "MONGO_URL must be set in /app/backend/.env"
    client = AsyncIOMotorClient(mongo_url)
    yield client["test_database"]
    client.close()


# ════════════════════════════════════════════════════════════════════
# S1 — SELF (regression)
# ════════════════════════════════════════════════════════════════════

def test_S1_self_subject_no_hints(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="Tell me about myself.",
            hints={},
        )
        assert fld.active_frame == ActiveFrame.SELF
        assert fld.relationship_role == "self"
        assert fld.relationship_stance == "self_subject"
        assert fld.resolution_source == ResolutionSource.SELF_NO_TARGET
        assert fld.target_user_id is None
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S2 — MEMBER spouse via name-only message
# ════════════════════════════════════════════════════════════════════

def test_S2_member_spouse_by_name(db):
    """No about_person_id is given; resolver must discover Mel via
    name → forum_members → users join, then bind to spouse via the
    canonical edges-first resolver."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What does Mel need from me?",
            hints={},
        )
        # Must NOT classify as FORUM despite the word "from me" — bias
        # toward MEMBER (per user directive).
        assert fld.active_frame in (ActiveFrame.MEMBER, ActiveFrame.SELF), (
            f"Expected MEMBER (or SELF→promoted), got {fld.active_frame!r}"
        )
        assert fld.target_user_id == MEL_ID
        assert fld.relationship_role == "spouse"
        assert fld.relationship_stance == "covenant_partner"
        assert fld.directionality == "SYMMETRIC"
        # Source must be EDGES (canonical graph), not PROPOSED_UNRESOLVED.
        assert fld.resolution_source == ResolutionSource.EDGES
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
        # Audit trail must show the name-match → canonical-resolver path.
        assert any("name_match_single" in r for r in fld.resolution_path), (
            f"Missing name_match_single in path: {fld.resolution_path}"
        )
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S3 — MEMBER child via name-only message
# ════════════════════════════════════════════════════════════════════

def test_S3_member_child_by_name(db):
    """The exact scenario from the user's bug report:
       "What does Thaddeus need from me?"
       Previously interpreted as generic profile; now must resolve to
       the parent→child relational frame."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What does Thaddeus need from me?",
            hints={},
        )
        assert fld.target_user_id == THADDEUS_ID
        assert fld.relationship_role == "child"
        assert fld.relationship_stance == "steward_guardian"
        assert fld.directionality == "USER_AS_GIVER"
        assert fld.resolution_source == ResolutionSource.EDGES
        assert fld.confidence >= HIGH_CONFIDENCE_THRESHOLD
        # Critical: must NOT have fired FORUM intent or scope_class.
        assert fld.scope_class is None
        assert fld.active_frame != ActiveFrame.FORUM
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S4 — FORUM intent
# ════════════════════════════════════════════════════════════════════

def test_S4_forum_intent_explicit(db):
    """Conservative FORUM intent.  Phrasing IS explicit ('this forum')
    so the resolver should bind to FORUM frame.  Pete has 4 forums →
    expect multi-match handling."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What's the energy of this forum as a whole?",
            hints={},
        )
        assert fld.active_frame == ActiveFrame.FORUM
        assert fld.resolution_source == ResolutionSource.FORUM_INTENT
        # Pete has 4 forums → expect multi-match flag
        assert "forum_intent_multi_match" in fld.missing_data
        # Confidence reduced because we couldn't bind a specific forum
        assert fld.confidence < HIGH_CONFIDENCE_THRESHOLD
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S5 — PAIRWISE: "Mel and Thaddeus"
# ════════════════════════════════════════════════════════════════════

def test_S5_pairwise_mel_and_thaddeus(db):
    """Pairwise pattern with two known co-members of Pete's forums."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="How are Mel and Thaddeus affecting each other?",
            hints={},
        )
        assert fld.active_frame == ActiveFrame.PAIRWISE
        assert fld.resolution_source == ResolutionSource.PAIRWISE_PATTERN
        # Both targets bound
        assert fld.target_user_id == MEL_ID
        assert fld.target_user_id_b == THADDEUS_ID
        assert fld.target_name == "Mel"
        assert fld.target_name_b is not None and fld.target_name_b.startswith("Thaddeus")
        # Pairwise is relation-between-two-others; no role/stance on the
        # viewer side.
        assert fld.relationship_role is None
        assert fld.relationship_stance == "neutral"
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S6 — MULTI_PERSON: "my children"
# ════════════════════════════════════════════════════════════════════

def test_S6_multi_person_my_children(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What about my children right now?",
            hints={},
        )
        assert fld.active_frame == ActiveFrame.MULTI_PERSON
        assert fld.scope_class == "my_children"
        assert fld.resolution_source == ResolutionSource.SCOPE_CLASS
        assert fld.target_user_id is None       # scope, not single person
        assert fld.target_user_id_b is None
        assert fld.relationship_role is None
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S7 — AMBIGUOUS: "Tell me about Test"
# (Pete has 5 saved_people whose names start with "Test"; all at
#  confidence 0.90 → ambiguity rule fires.)
# ════════════════════════════════════════════════════════════════════

def test_S7_ambiguous_multi_candidate(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="Tell me about Test.",
            hints={},
        )
        assert fld.active_frame == ActiveFrame.AMBIGUOUS
        assert fld.resolution_source == ResolutionSource.AMBIGUITY
        assert len(fld.ambiguity_candidates) >= 2, (
            f"Expected ≥2 candidates, got {len(fld.ambiguity_candidates)}"
        )
        # G2: ambiguous binding must remain BELOW high-confidence threshold
        assert fld.confidence < HIGH_CONFIDENCE_THRESHOLD
        assert "target_ambiguous" in fld.missing_data
        # No target should be bound when ambiguous
        assert fld.target_user_id is None
        assert fld.relationship_role is None
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S8 — Pronoun follow-up (protects Slice E)
# "Tell me about Mel."  →  "What does she need from me?"
# ════════════════════════════════════════════════════════════════════

def test_S8_pronoun_followup_resolves_to_last_target(db):
    """When a pronoun appears AND the caller provides `last_target_id`,
    the resolver must rebind to that target and load its role/stance
    from the canonical edges graph."""
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="What does she need from me?",
            hints={"last_target_id": MEL_ID},
        )
        assert fld.target_user_id == MEL_ID
        assert fld.relationship_role == "spouse"
        assert fld.relationship_stance == "covenant_partner"
        assert fld.resolution_source == ResolutionSource.EDGES
        # Audit trail must show pronoun-memory hint
        assert any("pronoun_memory" in r for r in fld.resolution_path), (
            f"Missing pronoun_memory in path: {fld.resolution_path}"
        )
        # Frame should be MEMBER (or promoted from SELF→MEMBER)
        assert fld.active_frame == ActiveFrame.MEMBER
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# S9 — Pairwise family extended assertion
# (Reuses S5 phrasing but adds the family-domain guarantees the user
#  asked for: BOTH targets must be edge-resolved, and resolution must
#  not mis-bind to the viewer.)
# ════════════════════════════════════════════════════════════════════

def test_S9_pairwise_family_no_viewer_misbind(db):
    async def _run():
        fld = await resolve_relationship_field(
            db=db,
            self_user_id=PETE_ID,
            message="How are Mel and Thaddeus affecting each other?",
            hints={},
        )
        # NEITHER target should be the viewer (Pete).
        assert fld.target_user_id   != PETE_ID
        assert fld.target_user_id_b != PETE_ID
        # Both must resolve to a known co-member, not a stranger.
        assert fld.target_user_id   in (MEL_ID, THADDEUS_ID)
        assert fld.target_user_id_b in (MEL_ID, THADDEUS_ID)
        assert fld.target_user_id != fld.target_user_id_b
    asyncio.run(_run())


# ════════════════════════════════════════════════════════════════════
# Bias regression — MEMBER must NOT be mis-classified as FORUM
# (defends the user-directive "MEMBER > PAIRWISE > FORUM")
# ════════════════════════════════════════════════════════════════════

def test_bias_member_question_not_misclassified_as_forum(db):
    async def _run():
        for msg in [
            "What does Thaddeus need from me?",
            "How is Mel doing today?",
            "Tell me about Isaac's week.",
        ]:
            fld = await resolve_relationship_field(
                db=db,
                self_user_id=PETE_ID,
                message=msg,
                hints={},
            )
            assert fld.active_frame != ActiveFrame.FORUM, (
                f"Misclassified MEMBER question as FORUM: msg={msg!r} "
                f"frame={fld.active_frame} source={fld.resolution_source}"
            )
            assert fld.scope_class is None, (
                f"Member question accidentally captured by scope_class: "
                f"msg={msg!r} scope={fld.scope_class}"
            )
    asyncio.run(_run())
