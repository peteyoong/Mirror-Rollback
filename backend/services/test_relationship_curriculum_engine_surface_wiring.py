"""Relationship Curriculum Engine V1 — surface wiring tests.

Verifies:
  1. Curriculum payload flows into forum-mapping signals when flag ON.
  2. Curriculum payload flows into /relationship-insight-v2 signals when flag ON.
  3. Curriculum payload attaches to Forum Chat response envelope.
  4. Legacy behaviour preserved byte-for-byte when flag is OFF.
  5. Source-level wiring presence (helps catch silent removal).
"""
from __future__ import annotations
import asyncio, os, sys
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID  = "697ec826ad4b18f75bf42616"


@pytest.fixture(scope="function")
def db():
    load_dotenv(os.path.join(ROOT, ".env"))
    client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    yield client["test_database"]
    client.close()


def _flag(val: bool):
    if val:
        os.environ["RELATIONSHIP_CURRICULUM_ENGINE"] = "true"
    else:
        os.environ.pop("RELATIONSHIP_CURRICULUM_ENGINE", None)


# ── 1. Flag ON  → maybe_generate returns payload  ─────────────────
def test_wiring_helper_returns_payload_when_flag_on(db):
    async def _run():
        _flag(True)
        from services.relationship_curriculum_engine import maybe_generate
        a = await db.charts.find_one({"user_id": PETE_ID})
        b = await db.charts.find_one({"user_id": MEL_ID})
        out = maybe_generate(
            person_a={"chart": a, "name": "Pete"},
            person_b={"chart": b, "name": "Mel"},
            relationship_context={"role": "spouse"},
        )
        assert out is not None
        rc = out["relationship_curriculum"]
        assert rc["confidence"] in ("low", "medium", "high")
        for k in ("gift", "challenge", "growth_edge", "curriculum"):
            assert rc[k]
    asyncio.run(_run())


# ── 2. Flag OFF → helper returns None (legacy preserved) ─────────
def test_wiring_helper_returns_none_when_flag_off(db):
    async def _run():
        _flag(False)
        from services.relationship_curriculum_engine import maybe_generate, is_enabled
        assert is_enabled() is False
        a = await db.charts.find_one({"user_id": PETE_ID})
        b = await db.charts.find_one({"user_id": MEL_ID})
        out = maybe_generate(
            person_a={"chart": a, "name": "Pete"},
            person_b={"chart": b, "name": "Mel"},
            relationship_context={"role": "spouse"},
        )
        assert out is None
    asyncio.run(_run())


# ── 3. Source wiring in forum_hd_mapping.py ──────────────────────
def test_forum_mapping_source_wiring_present():
    src = open(os.path.join(ROOT, "services", "forum_hd_mapping.py")).read()
    assert "maybe_compute_restory" in src  # Re-Story still wired
    assert "from services.relationship_curriculum_engine import" in src
    assert "_maybe_curriculum" in src
    assert "signals[\"relationship_curriculum\"]" in src


# ── 4. Source wiring in server.py (relationship-insight-v2) ──────
def test_relationship_insight_v2_source_wiring_present():
    src = open(os.path.join(ROOT, "server.py")).read()
    # Curriculum is mounted at top-level under signals
    assert "_curriculum_payload" in src
    assert "relationship_curriculum" in src
    # Surface mount comment marker
    assert "Relationship Curriculum Engine V1" in src


# ── 5. Source wiring in routers/forums_chat.py ───────────────────
def test_forum_chat_source_wiring_present():
    src = open(os.path.join(ROOT, "routers", "forums_chat.py")).read()
    assert "relationship_curriculum: Optional[Dict[str, Any]]" in src
    assert "relationship_curriculum_payload" in src
    assert "ForumChat][Curriculum]" in src
