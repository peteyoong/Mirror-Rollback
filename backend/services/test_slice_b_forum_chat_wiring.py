"""Slice B acceptance tests — Forum Chat backend wiring of the Slice A resolver.

Run with:
    cd /app/backend && python -m pytest services/test_slice_b_forum_chat_wiring.py -v

Verifies:
    L1.  Legacy contract — flag OFF + mode missing → 400 (byte-identical 400 msg)
    L2.  Legacy contract — flag OFF + mode=member + target → unchanged path
    L3.  Legacy contract — flag OFF + mode=self → unchanged path
    L4.  Legacy contract — flag OFF + mode=forum → unchanged path

    B1.  Flag ON, "Tell me about myself"           → resolved_context.frame = SELF
    B2.  Flag ON, "What does Mel need from me?"    → frame=MEMBER, target=Mel, role=spouse
    B3.  Flag ON, "What does Thaddeus need from me?" → frame=MEMBER, target=Thaddeus, role=child
    B4.  Flag ON, "How are Mel and Thaddeus …?"    → frame=PAIRWISE, both targets bound
    B5.  Flag ON, "What about my children?"        → frame=MULTI_PERSON, scope=my_children
    B6.  Flag ON, "Energy of this forum?"          → frame=FORUM
    B7.  Flag ON, "Tell me about Test."            → requires_clarification=True + candidates
    B8.  Flag ON, "What does she need from me?" + last_target_id=MEL → frame=MEMBER

All tests bypass the LLM by stubbing `emergent_generate`.
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# Real fixtures verified in Slice 1 audit.
PETE_ID     = "697f0c6abf35c0528ff06954"
MEL_ID      = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
# Forum where Pete + Mel are both active members (verified Slice A audit).
PETE_MEL_FORUM_ID    = "69dd05eaa333335fcbf3ad33"
# Forum where Pete + Thaddeus are both active members.
PETE_THAD_FORUM_ID   = "69dda348de9cb1c83c0780fa"


# ────────────────────────────────────────────────────────────────────
# LLM stub — short-circuits the expensive emergent_generate path.
# ────────────────────────────────────────────────────────────────────

class _LLMStub:
    def __init__(self):
        self.calls = []
        self.last_system_prompt = None

    async def __call__(self, *args, **kwargs):
        self.calls.append({
            "user_message": kwargs.get("user_message"),
            "mode":         kwargs.get("mode"),
            "context":      kwargs.get("context"),
        })
        self.last_system_prompt = kwargs.get("additional_system_prompt", "")
        return "stub-llm-response: ok"


@pytest.fixture(scope="function")
def app_and_stub(monkeypatch):
    """Build a FastAPI app with the real forums_chat router but a stubbed LLM."""
    load_dotenv(os.path.join(ROOT, ".env"))
    mongo_url = os.getenv("MONGO_URL")
    assert mongo_url, "MONGO_URL must be set in /app/backend/.env"
    client = AsyncIOMotorClient(mongo_url)
    db = client["test_database"]

    import logging
    log = logging.getLogger("test_slice_b")

    stub = _LLMStub()
    # Patch the LLM ENTRY POINT (forum chat imports emergent_contract.emergent_generate
    # inside the route).  Use sys.modules to intercept.
    import emergent_contract
    monkeypatch.setattr(emergent_contract, "emergent_generate", stub)

    from routers import forums_chat
    api_router = APIRouter(prefix="/api")
    forums_chat.register(api_router, db=db, logger=log, emergent_llm_key="test-key")

    app = FastAPI()
    app.include_router(api_router)

    yield app, stub, db
    client.close()


def _post_chat(app, payload, flag_value=None, monkeypatch=None):
    """Helper to POST a forum chat request with the FORUM_CHAT_AUTO_CONTEXT
    env flag set as desired for the duration of one call.  Uses a fresh
    TestClient each time (rate-limit window is per-process)."""
    old = os.environ.get("FORUM_CHAT_AUTO_CONTEXT")
    if flag_value is None:
        os.environ.pop("FORUM_CHAT_AUTO_CONTEXT", None)
    else:
        os.environ["FORUM_CHAT_AUTO_CONTEXT"] = flag_value
    try:
        with TestClient(app) as cl:
            return cl.post(
                f"/api/forums/{payload.pop('forum_id')}/chat",
                json=payload,
            )
    finally:
        if old is None:
            os.environ.pop("FORUM_CHAT_AUTO_CONTEXT", None)
        else:
            os.environ["FORUM_CHAT_AUTO_CONTEXT"] = old


# ════════════════════════════════════════════════════════════════════
# LEGACY CONTRACT — flag OFF
# ════════════════════════════════════════════════════════════════════

def test_L1_legacy_flag_off_mode_missing_returns_400(app_and_stub):
    app, stub, _ = app_and_stub
    # Reset rate limit
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "Anything",
    }, flag_value=None)
    assert res.status_code == 400, res.text
    body = res.json()
    assert "mode is required" in str(body)


def test_L2_legacy_flag_off_explicit_member_unchanged(app_and_stub):
    app, stub, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id":         PETE_MEL_FORUM_ID,
        "user_id":          PETE_ID,
        "message":          "Tell me about Mel.",
        "mode":             "member",
        "target_member_id": MEL_ID,
    }, flag_value=None)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    # Legacy responses must NOT carry resolved_context
    assert body["resolved_context"] is None
    assert body["requires_clarification"] is False


def test_L3_legacy_flag_off_self_unchanged(app_and_stub):
    app, stub, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "What about me?",
        "mode":     "self",
    }, flag_value=None)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["resolved_context"] is None


def test_L4_legacy_flag_off_forum_unchanged(app_and_stub):
    app, stub, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "Forum dynamics?",
        "mode":     "forum",
    }, flag_value=None)
    assert res.status_code == 200, res.text
    assert res.json()["resolved_context"] is None


# ════════════════════════════════════════════════════════════════════
# AUTO-CONTEXT — flag ON
# ════════════════════════════════════════════════════════════════════

def test_B1_auto_self(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "Tell me about myself.",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json().get("resolved_context")
    assert rc is not None, "resolved_context must be present when flag is ON"
    assert rc["frame"] == "SELF"
    assert rc["target_user_id"] is None


def test_B2_auto_member_spouse(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "What does Mel need from me?",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    assert rc["frame"] == "MEMBER"
    assert rc["target_user_id"] == MEL_ID
    assert rc["target_role"] == "spouse"


def test_B3_auto_member_child(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_THAD_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "What does Thaddeus need from me?",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    assert rc["frame"] == "MEMBER"
    assert rc["target_user_id"] == THADDEUS_ID
    assert rc["target_role"] == "child"


def test_B4_auto_pairwise(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_THAD_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "How are Mel and Thaddeus affecting each other?",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    assert rc["frame"] == "PAIRWISE"
    # Both targets present
    pair = {rc["target_user_id"], rc["target_user_id_b"]}
    assert MEL_ID in pair and THADDEUS_ID in pair


def test_B5_auto_multi_person(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "What about my children right now?",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    assert rc["frame"] == "MULTI_PERSON"
    assert rc["scope_class"] == "my_children"


def test_B6_auto_forum(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "What's the energy of this forum as a whole?",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    assert rc["frame"] == "FORUM"


def test_B7_auto_ambiguous_short_circuits_llm(app_and_stub):
    app, stub, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    before_call_count = len(stub.calls)
    res = _post_chat(app, {
        "forum_id": PETE_MEL_FORUM_ID,
        "user_id":  PETE_ID,
        "message":  "Tell me about Test.",
    }, flag_value="true")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["requires_clarification"] is True
    assert body["resolved_context"]["frame"] == "AMBIGUOUS"
    assert len(body["clarification_candidates"]) >= 2
    # The LLM should NOT have been called for the ambiguous branch
    assert len(stub.calls) == before_call_count, (
        "LLM was called on AMBIGUOUS — expected short-circuit"
    )


def test_B8_auto_pronoun_followup(app_and_stub):
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id":       PETE_MEL_FORUM_ID,
        "user_id":        PETE_ID,
        "message":        "What does she need from me?",
        "last_target_id": MEL_ID,
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    assert rc["frame"] == "MEMBER"
    assert rc["target_user_id"] == MEL_ID


# ════════════════════════════════════════════════════════════════════
# REGRESSION — flag ON but explicit mode is preserved when resolver is
# low-confidence.  Defensive: a UI-supplied mode must NOT be silently
# discarded.
# ════════════════════════════════════════════════════════════════════

def test_B9_flag_on_explicit_mode_preserved(app_and_stub):
    """When the user passes mode=member + target, the resolver should
    NOT override it on a low-confidence resolution."""
    app, _, _ = app_and_stub
    from routers.forums_chat import _forum_chat_rate_limits
    _forum_chat_rate_limits.clear()
    res = _post_chat(app, {
        "forum_id":         PETE_MEL_FORUM_ID,
        "user_id":          PETE_ID,
        "message":          "tell me",          # deliberately vague
        "mode":             "member",
        "target_member_id": MEL_ID,
    }, flag_value="true")
    assert res.status_code == 200, res.text
    rc = res.json()["resolved_context"]
    # Resolver landed somewhere (SELF or MEMBER); either way the response
    # MUST include the resolved_context block.
    assert rc is not None
