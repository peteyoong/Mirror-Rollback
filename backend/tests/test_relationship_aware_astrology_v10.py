"""
V10 Relationship-Aware Astrology integration tests.

Build marker: relationship-aware-astrology-v10

Covers:
  • GET /api/health surfaces V7 + V8 + V10 markers/flags.
  • POST /api/admin/map-relationship upserts into relationship_mappings.
  • lens=null "Tell me about Mel's 4th house and how does that map to me"
    from Pete with explicit map -> relationship_role=spouse,
    relationship_source=explicit_map, relational_synthesis_used=True,
    destabilizing_planet=Uranus, prose contains relational paragraph
    referencing Pete/you/your relationship AND Uranus, no banned phrases.
  • Same query AFTER deleting the explicit map -> fallback to
    forum_inference (Pete & Mel is a 2-member private forum named with
    "&" pattern) -> relationship_role=partner, relationship_source=forum_inference.
  • Regression: lens=astrology "Tell me about my 10th house" for Pete
    fires V8 on H10 with no target person; relationship_context absent
    or relational_synthesis_used=False.
  • Unit test: build_relational_synthesis_block returns a string >500
    chars containing 'relationship-aware-astrology-v10', 'spouse',
    'Pete', 'Mel', 'RELATIONAL paragraph', 'BANNED' tokens.
  • Edge case: lens=null "What is for dinner?" -> no astrology routing,
    no field_synthesis, no relationship_context with relational_synthesis_used.
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest
import requests

sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

_base = (
    os.environ.get("EXPO_BACKEND_URL")
    or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
)
assert _base, "EXPO_BACKEND_URL/EXPO_PUBLIC_BACKEND_URL must be set"
BASE_URL = _base.rstrip("/")

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
FORUM_PETE_MEL = "69dd05eaa333335fcbf3ad33"

BANNED_PHRASES = [
    "the 4th house relates",
    "themes of home/family",
    "in astrology",
    "reflect on",
    "how does this resonate",
    "consider how",
    "typically associated",
    "this house represents",
]


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def db():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]]


def _post_chat(api_client, *, user_id, message, lens=None, timeout=240):
    payload = {"user_id": user_id, "message": message}
    if lens is not None:
        payload["lens"] = lens
    return api_client.post(
        f"{BASE_URL}/api/mirror/chat", json=payload, timeout=timeout
    )


def _astro(body):
    return ((body.get("debug") or {}).get("astro_chat")) or {}


def _assert_no_banned(prose, *, allow_trailing_q=False):
    lower = prose.lower()
    for bp in BANNED_PHRASES:
        assert bp not in lower, f"Banned phrase '{bp}' found in prose: {prose[:400]}"
    if not allow_trailing_q:
        assert not prose.strip().endswith("?"), \
            f"Response must not end with '?': ...{prose[-200:]}"


# ──────────────────────────────────────────────────────────────────────
# 1. /api/health surfaces V10 + V8 + V7 markers
# ──────────────────────────────────────────────────────────────────────
class TestHealthV10:
    def test_health_exposes_v10_markers(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert body.get("relationship_aware_astrology_v10") is True, body
        assert body.get("relationship_resolver_marker") == \
            "relationship-aware-astrology-v10", body
        assert body.get("astrology_field_synthesis_v8") is True, body
        assert body.get("ask_mirror_astrology_v7") is True, body


# ──────────────────────────────────────────────────────────────────────
# 2. POST /api/admin/map-relationship upserts mapping
# ──────────────────────────────────────────────────────────────────────
class TestAdminMapRelationship:
    def test_map_pete_mel_spouse(self, api_client, db):
        # Clean any pre-existing mapping first so we can verify upsert
        async def _pre_clean():
            await db.relationship_mappings.delete_many({
                "asker_user_id": PETE_ID,
                "target_user_id": MEL_ID,
            })
        asyncio.get_event_loop().run_until_complete(_pre_clean())

        r = api_client.post(
            f"{BASE_URL}/api/admin/map-relationship",
            json={
                "asker_user_id": PETE_ID,
                "target_user_id": MEL_ID,
                "target_name": "Mel",
                "relationship_type": "spouse",
            },
            timeout=30,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert body.get("ok") is True, body
        assert (body.get("mapping") or {}).get("relationship_type") == "spouse", body

        # Verify persistence
        async def _check():
            return await db.relationship_mappings.find_one({
                "asker_user_id": PETE_ID,
                "target_user_id": MEL_ID,
            })
        doc = asyncio.get_event_loop().run_until_complete(_check())
        assert doc, "relationship_mappings doc not persisted"
        assert doc.get("relationship_type") == "spouse", doc
        assert doc.get("build_marker") == "relationship-aware-astrology-v10", doc


# ──────────────────────────────────────────────────────────────────────
# 3. lens=null Pete asks about Mel's 4th house WITH explicit spouse map
# ──────────────────────────────────────────────────────────────────────
class TestRelationalSynthesisExplicitMap:
    def test_pete_mel_4th_spouse_relational(self, api_client, db):
        # Ensure explicit spouse map exists
        async def _ensure_map():
            await db.relationship_mappings.update_one(
                {"asker_user_id": PETE_ID, "target_user_id": MEL_ID},
                {"$set": {
                    "asker_user_id": PETE_ID,
                    "target_user_id": MEL_ID,
                    "target_name": "Mel",
                    "relationship_type": "spouse",
                    "build_marker": "relationship-aware-astrology-v10",
                }},
                upsert=True,
            )
        asyncio.get_event_loop().run_until_complete(_ensure_map())

        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="Tell me about Mel's 4th house and how does that map to me",
            lens=None,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        astro = _astro(body)
        rel = astro.get("relationship_context") or {}
        fs = astro.get("field_synthesis") or {}

        # V7 target resolved
        assert astro.get("v7_target_resolved") is True, astro
        assert (astro.get("v7_target_name") or "").lower() == "mel", astro

        # V8 field synthesis fired with Uranus destabilizer
        assert fs.get("house_number") == 4, fs
        assert fs.get("destabilizing_planet") == "Uranus", fs

        # V10 relationship context
        assert rel.get("relationship_detected") is True, rel
        assert rel.get("relationship_role") == "spouse", rel
        assert rel.get("relationship_source") == "explicit_map", rel
        assert rel.get("relational_synthesis_used") is True, rel
        asker = (rel.get("asker_name") or "").lower()
        assert "pete" in asker, f"asker_name unexpected: {rel.get('asker_name')!r}"

        prose = body.get("response") or ""
        assert prose, "Empty response"
        lower = prose.lower()
        # Must mention destabilizer
        assert "uranus" in lower, f"Missing 'uranus' in prose: {prose[:400]}"
        # Must contain relational reference to asker
        assert any(t in lower for t in ("pete", "you", "your relationship")), \
            f"No asker reference in prose: {prose[:400]}"
        _assert_no_banned(prose)


# ──────────────────────────────────────────────────────────────────────
# 4. After deleting explicit map → fallback to forum_inference=partner
# ──────────────────────────────────────────────────────────────────────
class TestRelationalSynthesisForumInferenceFallback:
    def test_pete_mel_fallback_partner(self, api_client, db):
        async def _delete_map():
            await db.relationship_mappings.delete_one({
                "asker_user_id": PETE_ID, "target_user_id": MEL_ID,
            })
        asyncio.get_event_loop().run_until_complete(_delete_map())

        try:
            r = _post_chat(
                api_client, user_id=PETE_ID,
                message="Tell me about Mel's 4th house and how does that map to me",
                lens=None,
            )
            assert r.status_code == 200, r.text[:400]
            body = r.json()
            astro = _astro(body)
            rel = astro.get("relationship_context") or {}

            assert rel.get("relationship_detected") is True, rel
            # Forum-inference path should yield partner (Pete & Mel is a 2-member
            # private forum with "&" name pattern)
            assert rel.get("relationship_role") == "partner", \
                f"Expected partner; rel={rel}"
            assert rel.get("relationship_source") == "forum_inference", rel
            assert rel.get("relational_synthesis_used") is True, rel

            prose = body.get("response") or ""
            assert prose, "Empty response"
            lower = prose.lower()
            assert "uranus" in lower, f"Missing 'uranus' in prose: {prose[:400]}"
            assert any(t in lower for t in ("pete", "you", "your relationship")), \
                f"No asker reference in prose: {prose[:400]}"
            _assert_no_banned(prose)
        finally:
            # Restore explicit map so other tests / live env aren't perturbed
            async def _restore():
                await db.relationship_mappings.update_one(
                    {"asker_user_id": PETE_ID, "target_user_id": MEL_ID},
                    {"$set": {
                        "asker_user_id": PETE_ID,
                        "target_user_id": MEL_ID,
                        "target_name": "Mel",
                        "relationship_type": "spouse",
                        "build_marker": "relationship-aware-astrology-v10",
                    }},
                    upsert=True,
                )
            asyncio.get_event_loop().run_until_complete(_restore())


# ──────────────────────────────────────────────────────────────────────
# 5. Regression: self-chart 10th house (no target) → no relational synthesis
# ──────────────────────────────────────────────────────────────────────
class TestSelfChartNoRelationalSynthesis:
    def test_pete_10th_house_no_relational(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="Tell me about my 10th house", lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        fs = astro.get("field_synthesis") or {}

        assert astro.get("v7_target_resolved") is False, astro
        assert astro.get("house_inventory_used") is True, astro
        assert fs.get("house_number") == 10, fs

        rel = astro.get("relationship_context")
        # Either absent OR relational_synthesis_used must be False
        if rel:
            assert rel.get("relational_synthesis_used") is False, \
                f"relational_synthesis must NOT fire without target: rel={rel}"


# ──────────────────────────────────────────────────────────────────────
# 6. Unit test: build_relational_synthesis_block
# ──────────────────────────────────────────────────────────────────────
class TestBuildRelationalSynthesisBlock:
    def test_block_contents(self):
        from services.relationship_resolver import (
            build_relational_synthesis_block,
            resolve_relationship,  # noqa: F401 — import smoke test
        )

        block = build_relational_synthesis_block(
            asker_name="Pete",
            target_name="Mel",
            relationship_ctx={
                "relationship_role": "spouse",
                "closeness": "high",
                "emotional_weight": "high",
                "relationship_source": "explicit_map",
            },
            field_synthesis={"destabilizing_planet": "Uranus"},
        )
        assert isinstance(block, str)
        assert len(block) > 500, f"block too short: {len(block)}"
        for token in (
            "relationship-aware-astrology-v10",
            "spouse",
            "Pete",
            "Mel",
            "RELATIONAL paragraph",
            "BANNED",
        ):
            assert token in block, f"Missing token {token!r} in block:\n{block}"


# ──────────────────────────────────────────────────────────────────────
# 7. Edge case: non-astrology query → no astrology routing, no
#    field_synthesis, no relational_synthesis_used
# ──────────────────────────────────────────────────────────────────────
class TestNonAstrologyQuery:
    def test_dinner_query_no_routing(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="What is for dinner?", lens=None,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        astro = _astro(body)

        # No astrology routing / no V8 / no relational synthesis
        assert not astro.get("field_synthesis"), \
            f"field_synthesis must NOT fire for non-astrology: astro={astro}"
        rel = astro.get("relationship_context")
        if rel:
            assert rel.get("relational_synthesis_used") is False, \
                f"relational_synthesis must NOT fire for non-astrology: rel={rel}"
