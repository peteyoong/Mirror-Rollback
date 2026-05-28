"""
V7 Ask Mirror ↔ Astrology Engine integration tests.

Build marker: ask-mirror-astrology-v7

Covers:
  • member_chart_resolver unit tests (name extraction + forum-member resolution)
  • /api/mirror/chat with lens=null routing astrology intent through
    deterministic engines (Ask Mirror engine path)
  • Mel-by-name routing (Pete → Mel via forum_members 'Pete & Mel')
  • Self-questions ('my whole chart') still route to pressure_topology with
    v7_target_resolved=False
  • Regressions: lens='astrology' continues to route house_inventory /
    pressure_topology / natal_object branches with v7_ask_mirror_engine_used=False
  • Non-astrology Ask Mirror message → gate does NOT fire (no false positive)
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

BASE_URL = (
    os.environ.get("EXPO_BACKEND_URL")
    or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
).rstrip("/")
assert BASE_URL, "EXPO_BACKEND_URL/EXPO_PUBLIC_BACKEND_URL must be set"

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
FORUM_ID = "69dd05eaa333335fcbf3ad33"

# Banned phrases per V7 contract — Ask Mirror MUST NOT refuse or hedge.
BANNED_PHRASES = [
    "i'm here to facilitate reflection",
    "i don't provide direct chart readings",
    "this placement suggests",
    "spiritual journey",
    "this energy",
]


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────
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


def _post_chat(api_client, *, user_id, message, lens=None, timeout=180):
    payload = {"user_id": user_id, "message": message}
    if lens is not None:
        payload["lens"] = lens
    return api_client.post(
        f"{BASE_URL}/api/mirror/chat",
        json=payload,
        timeout=timeout,
    )


def _astro(body):
    return ((body.get("debug") or {}).get("astro_chat")) or {}


def _assert_no_banned(prose):
    lower = prose.lower()
    for bp in BANNED_PHRASES:
        assert bp not in lower, f"Banned phrase found: '{bp}' in prose: {prose[:300]}"


# ──────────────────────────────────────────────────────────────────────────
# 1. member_chart_resolver unit tests
# ──────────────────────────────────────────────────────────────────────────
class TestMemberChartResolver:
    def test_extract_possessive_name(self):
        from services.member_chart_resolver import extract_candidate_names
        names = extract_candidate_names("Tell me about Mel's 4th house")
        assert "Mel" in names, f"Expected 'Mel' in {names}"

    def test_extract_skips_stopwords(self):
        from services.member_chart_resolver import extract_candidate_names
        names = extract_candidate_names("Where is my Sun?")
        # 'Sun' should be filtered by stopwords
        assert "Sun" not in names

    def test_extract_thaddeus_possessive(self):
        from services.member_chart_resolver import extract_candidate_names
        names = extract_candidate_names("How does Thaddeus's Sun work")
        assert "Thaddeus" in names, f"Expected 'Thaddeus' in {names}"

    def test_resolve_mel_target_for_pete(self, db):
        from services.member_chart_resolver import resolve_target_member

        async def _run():
            return await resolve_target_member(
                db=db,
                asker_user_id=PETE_ID,
                message="Tell me about Mel's 4th house",
            )

        result = asyncio.get_event_loop().run_until_complete(_run())
        assert result is not None, "Resolver should find Mel"
        assert result["target_name"].lower() == "mel"
        assert result["target_user_id"] == MEL_ID
        assert result["target_chart"] is not None, "Mel chart must be hydrated"
        assert result["source"] == "forum_member"

    def test_resolve_self_returns_none(self, db):
        from services.member_chart_resolver import resolve_target_member

        async def _run():
            return await resolve_target_member(
                db=db,
                asker_user_id=PETE_ID,
                message="Tell me about my own chart",
            )

        result = asyncio.get_event_loop().run_until_complete(_run())
        assert result is None, f"Self-question must return None, got {result}"

    def test_resolve_thaddeus_target_for_pete(self, db):
        from services.member_chart_resolver import resolve_target_member

        async def _run():
            return await resolve_target_member(
                db=db,
                asker_user_id=PETE_ID,
                message="How does Thaddeus's Sun work",
            )

        result = asyncio.get_event_loop().run_until_complete(_run())
        assert result is not None, "Resolver should find Thaddeus"
        assert result["target_name"].lower() == "thaddeus"
        assert result["target_chart"] is not None, "Thaddeus chart must be hydrated"


# ──────────────────────────────────────────────────────────────────────────
# 2. Ask Mirror (lens=None) — name-based delegation to Mel
# ──────────────────────────────────────────────────────────────────────────
class TestAskMirrorDelegatesToMel:
    def test_pete_asks_about_mels_4th_house_routes_to_mel(self, api_client):
        r = _post_chat(
            api_client,
            user_id=PETE_ID,
            message="Tell me about Mel's 4th house",
            lens=None,
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
        body = r.json()
        astro = _astro(body)

        # V7 routing flags
        assert astro.get("v7_target_resolved") is True, \
            f"v7_target_resolved must be True. astro_chat={astro}"
        assert (astro.get("v7_target_name") or "").lower() == "mel", \
            f"v7_target_name must be 'Mel', got {astro.get('v7_target_name')}"
        assert astro.get("v7_target_user_id") == MEL_ID, \
            f"v7_target_user_id must be {MEL_ID}, got {astro.get('v7_target_user_id')}"
        assert astro.get("v7_ask_mirror_engine_used") is True, \
            f"v7_ask_mirror_engine_used must be True. astro_chat={astro}"
        assert astro.get("house_inventory_used") is True, \
            f"house_inventory_used must be True for 4th house. astro_chat={astro}"
        assert astro.get("house_number") == 4

        prose = body.get("response", "")
        assert prose, "Empty response"
        # Mel referenced by name
        assert "mel" in prose.lower(), f"Response must mention Mel: {prose[:300]}"
        # No banned phrases / no closing question
        _assert_no_banned(prose)
        assert not prose.strip().endswith("?"), \
            f"Response must not end with '?': ...{prose[-120:]}"


# ──────────────────────────────────────────────────────────────────────────
# 3. Ask Mirror (lens=None) — self-question routes to pressure_topology
# ──────────────────────────────────────────────────────────────────────────
class TestAskMirrorSelfWholeChart:
    def test_pete_my_whole_chart_routes_pressure_topology(self, api_client):
        r = _post_chat(
            api_client,
            user_id=PETE_ID,
            message="What does my whole chart say",
            lens=None,
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
        body = r.json()
        astro = _astro(body)

        assert astro.get("v7_target_resolved") is False, \
            f"'my whole chart' must NOT resolve a target. astro={astro}"
        assert astro.get("pressure_topology_used") is True, \
            f"pressure_topology_used must be True. astro={astro}"
        assert astro.get("v7_ask_mirror_engine_used") is True, \
            f"v7_ask_mirror_engine_used must be True. astro={astro}"

        prose = body.get("response", "").lower()
        _assert_no_banned(body.get("response", ""))
        # At least 2 of Pete's deterministic topology cues
        cues = [
            "saturn", "pisces", "third house", "3rd house",
            "precision", "permeability", "compression",
            "containment", "editing",
        ]
        hits = [c for c in cues if c in prose]
        assert len(hits) >= 2, \
            f"Expected ≥2 Pete topology cues. Hits={hits}. Prose: {prose[:400]}"


# ──────────────────────────────────────────────────────────────────────────
# 4. Regression: lens='astrology' still routes correctly (no Ask Mirror flag)
# ──────────────────────────────────────────────────────────────────────────
class TestAstrologyLensRegression:
    def test_pete_10th_house_lens_astrology(self, api_client):
        r = _post_chat(
            api_client,
            user_id=PETE_ID,
            message="Tell me about my 10th house",
            lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        assert astro.get("house_inventory_used") is True, astro
        assert astro.get("v7_target_resolved") is False, astro
        assert astro.get("v7_ask_mirror_engine_used") is False, \
            f"lens=astrology must NOT set v7_ask_mirror_engine_used. astro={astro}"
        objects = astro.get("objects_in_house") or []
        if objects:
            prose = r.json()["response"].lower()
            assert any(o.lower() in prose for o in objects), \
                f"Response should mention {objects}. Prose: {prose[:300]}"

    def test_pete_whole_chart_lens_astrology(self, api_client):
        r = _post_chat(
            api_client,
            user_id=PETE_ID,
            message="Tell me about my whole chart",
            lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        assert astro.get("pressure_topology_used") is True, astro
        assert astro.get("v7_ask_mirror_engine_used") is False, \
            f"lens=astrology must NOT set v7_ask_mirror_engine_used. astro={astro}"

    def test_pete_natal_chiron_lens_astrology(self, api_client):
        r = _post_chat(
            api_client,
            user_id=PETE_ID,
            message="where is my natal Chiron",
            lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        assert astro.get("natal_object_used") is True, astro
        assert astro.get("v7_ask_mirror_engine_used") is False, \
            f"lens=astrology must NOT set v7_ask_mirror_engine_used. astro={astro}"


# ──────────────────────────────────────────────────────────────────────────
# 5. Edge case: non-astrology Ask Mirror message — gate must NOT fire
# ──────────────────────────────────────────────────────────────────────────
class TestNoFalsePositiveGate:
    def test_non_astrology_ask_mirror_does_not_fire_engine(self, api_client):
        r = _post_chat(
            api_client,
            user_id=PETE_ID,
            message="What is happening today?",
            lens=None,
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        # No astrology intent → engine must not run (flags absent or False)
        assert not astro.get("v7_ask_mirror_engine_used"), \
            f"Non-astrology message must NOT fire engine. astro={astro}"
        assert not astro.get("pressure_topology_used"), \
            f"Pressure topology must not run for non-astro msg. astro={astro}"
        assert not astro.get("house_inventory_used"), \
            f"House inventory must not run for non-astro msg. astro={astro}"
        assert not astro.get("natal_object_used"), \
            f"Natal object must not run for non-astro msg. astro={astro}"
        assert not astro.get("transit_object_used"), \
            f"Transit object must not run for non-astro msg. astro={astro}"
        # Should still return a Mirror response
        assert r.json().get("response"), "Mirror should still respond normally"
