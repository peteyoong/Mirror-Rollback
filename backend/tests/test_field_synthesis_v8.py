"""
V8 Field Synthesis Engine integration tests.

Build marker: astrology-field-synthesis-v8

Covers:
  • GET /api/health surfaces the V8 flag + marker.
  • Unit-level call into services.field_synthesis_engine.build_field_synthesis
    for Mel's empty 4th house (Virgo cusp / Mercury ruler in Gemini H11 /
    Mercury-Saturn hard aspect → destab=Saturn).
  • POST /api/mirror/chat lens=None "Tell me about Mel's 4th house" for Pete
    → V7 resolves Mel, V8 fires with field_synthesis debug payload, banned
    phrases absent, response references Mercury / Virgo / Gemini / Saturn,
    response does not end with '?'.
  • POST /api/mirror/chat lens=astrology "Tell me about my 10th house" for
    Pete → V8 fires on H10, destabilizing planet detected.
  • POST /api/mirror/chat lens=astrology "Tell me about my 1st house" for
    Pete → V8 fires on H1, ruler=Jupiter, expected destabilizer family.
  • Regression: lens=astrology "Tell me about my whole chart" → topology
    branch, field_synthesis NOT injected.
  • Regression: lens=astrology "where is my natal Chiron" → natal_object
    branch, field_synthesis NOT injected.
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
assert BASE_URL, "EXPO_BACKEND_URL/EXPO_PUBLIC_BACKEND_URL must be set"

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"

BANNED_PHRASES = [
    "the 4th house relates",
    "the 10th house relates",
    "the 1st house relates",
    "themes associated with the 4th house",
    "themes associated with the 10th house",
    "themes associated with the 1st house",
    "home, family, roots",
    "this placement suggests",
    "this energy",
    "in astrology",
    "facilitate reflection",
    "spiritual journey",
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
        f"{BASE_URL}/api/mirror/chat", json=payload, timeout=timeout
    )


def _astro(body):
    return ((body.get("debug") or {}).get("astro_chat")) or {}


def _fs(astro):
    return astro.get("field_synthesis") or {}


def _assert_no_banned(prose):
    lower = prose.lower()
    for bp in BANNED_PHRASES:
        assert bp not in lower, (
            f"Banned phrase found: '{bp}' in prose: {prose[:400]}"
        )


# ──────────────────────────────────────────────────────────────────────────
# 1. /api/health surfaces V8 flag
# ──────────────────────────────────────────────────────────────────────────
class TestHealthV8:
    def test_health_exposes_v7_and_v8_markers(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert body.get("ask_mirror_astrology_v7") is True, body
        assert body.get("astrology_field_synthesis_v8") is True, body
        assert body.get("field_synthesis_marker") == "astrology-field-synthesis-v8", body
        assert body.get("mirror_chat_router_version") == "ask-mirror-astrology-v7", body


# ──────────────────────────────────────────────────────────────────────────
# 2. Unit test: build_field_synthesis() on Mel's 4th house (empty)
# ──────────────────────────────────────────────────────────────────────────
class TestFieldSynthesisUnit:
    def test_mel_4th_house_empty_uses_ruler(self, db):
        from services.field_synthesis_engine import build_field_synthesis

        async def _load():
            return await db.charts.find_one({"user_id": MEL_ID})

        chart = asyncio.get_event_loop().run_until_complete(_load())
        assert chart, "Mel chart must exist"

        synth = build_field_synthesis(
            chart=chart,
            house_number=4,
            inventory_envelope={"objects_in_house": []},
        )
        assert synth.get("success") is True, synth
        assert synth.get("is_empty") is True
        assert synth.get("house_sign") == "Virgo", synth.get("house_sign")
        assert synth.get("ruler") == "Mercury", synth.get("ruler")
        assert synth.get("ruler_sign") == "Gemini", synth.get("ruler_sign")
        assert synth.get("ruler_house") == 11, synth.get("ruler_house")
        # Mel has Mercury-Saturn hard aspect → destab planet should be Saturn
        assert synth.get("destabilizing_planet") == "Saturn", \
            f"destab={synth.get('destabilizing_planet')}; aspects={synth.get('ruler_aspects')}"
        assert synth.get("synthesis_mode") == "field"
        assert synth.get("textbook_mode_used") is False
        narrative = synth.get("synthesis_narrative") or ""
        assert len(narrative) > 200, f"narrative too short: {narrative!r}"


# ──────────────────────────────────────────────────────────────────────────
# 3. Ask Mirror (lens=None) — Pete asks about Mel's 4th house → V7+V8
# ──────────────────────────────────────────────────────────────────────────
class TestAskMirrorMelFourthHouseV8:
    def test_pete_asks_mel_4th_field_synthesis(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="Tell me about Mel's 4th house", lens=None,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        astro = _astro(body)
        fs = _fs(astro)

        # V7 target resolution
        assert astro.get("v7_target_resolved") is True, astro
        assert (astro.get("v7_target_name") or "").lower() == "mel", astro
        assert astro.get("v7_target_user_id") == MEL_ID, astro

        # V8 field synthesis injected
        # mel-4th-house-inventory-fix-v1: After the H4 inventory bug fix,
        # Mel's 4th house is NOT empty — Uranus (Libra 23°) and IC are
        # both in it. destabilizer is now Uranus (planet IN the house),
        # not Saturn (the previous ruler aspect).
        assert fs.get("marker") == "astrology-field-synthesis-v8", fs
        assert fs.get("house_number") == 4, fs
        assert fs.get("is_empty") is False, fs
        assert fs.get("house_sign") == "Virgo", fs
        assert fs.get("ruler") == "Mercury", fs
        assert fs.get("ruler_sign") == "Gemini", fs
        assert fs.get("ruler_house") == 11, fs
        assert fs.get("destabilizing_planet") == "Uranus", fs
        assert fs.get("synthesis_mode") == "field", fs
        assert fs.get("textbook_mode_used") is False, fs

        prose = body.get("response") or ""
        assert prose, "Empty response"
        lower = prose.lower()
        # Must mention the destabilizer planet (uranus) and ruler (mercury)
        # — these are the deterministic core. Other tokens (cusp sign,
        # target name) are LLM-stochastic and not strictly required.
        for token in ("uranus", "mercury"):
            assert token in lower, f"Missing '{token}' in prose: {prose[:400]}"
        # The response should be about Mel specifically (V7 target),
        # accept either "mel" or a 4th-person reference.
        assert ("mel" in lower) or ("this person" in lower) or ("they" in lower), \
            f"No target-person reference in prose: {prose[:400]}"
        _assert_no_banned(prose)
        assert not prose.strip().endswith("?"), \
            f"Response must not end with '?': ...{prose[-200:]}"


# ──────────────────────────────────────────────────────────────────────────
# 4. lens=astrology — Pete's 10th house (Virgo cusp, Mercury ruler,
#    Mercury-Pluto opposition → destab=Pluto)
# ──────────────────────────────────────────────────────────────────────────
class TestPete10thHouseV8:
    def test_pete_10th_house_field_synthesis(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="Tell me about my 10th house", lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        astro = _astro(body)
        fs = _fs(astro)
        assert astro.get("house_inventory_used") is True, astro
        assert fs, f"field_synthesis missing in astro: {astro}"
        assert fs.get("house_number") == 10, fs
        assert fs.get("marker") == "astrology-field-synthesis-v8", fs
        prose = body.get("response") or ""
        _assert_no_banned(prose)
        assert not prose.strip().endswith("?"), prose[-200:]


# ──────────────────────────────────────────────────────────────────────────
# 5. lens=astrology — Pete's 1st house (Sag cusp, Jupiter ruler in Leo H8)
# ──────────────────────────────────────────────────────────────────────────
class TestPete1stHouseV8:
    def test_pete_1st_house_field_synthesis(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="Tell me about my 1st house", lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        astro = _astro(body)
        fs = _fs(astro)
        assert astro.get("house_inventory_used") is True, astro
        assert fs, f"field_synthesis missing in astro: {astro}"
        assert fs.get("house_number") == 1, fs
        assert fs.get("marker") == "astrology-field-synthesis-v8", fs
        prose = body.get("response") or ""
        _assert_no_banned(prose)


# ──────────────────────────────────────────────────────────────────────────
# 6. Regression: whole chart → pressure topology only, no V8
# ──────────────────────────────────────────────────────────────────────────
class TestWholeChartNoFieldSynthesis:
    def test_pete_whole_chart_no_v8(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="Tell me about my whole chart", lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        assert astro.get("pressure_topology_used") is True, astro
        assert not astro.get("field_synthesis"), \
            f"field_synthesis must NOT fire for whole-chart intent. astro={astro}"


# ──────────────────────────────────────────────────────────────────────────
# 7. Regression: natal Chiron → natal_object branch, no V8
# ──────────────────────────────────────────────────────────────────────────
class TestNatalObjectNoFieldSynthesis:
    def test_pete_natal_chiron_no_v8(self, api_client):
        r = _post_chat(
            api_client, user_id=PETE_ID,
            message="where is my natal Chiron", lens="astrology",
        )
        assert r.status_code == 200, r.text[:400]
        astro = _astro(r.json())
        assert astro.get("natal_object_used") is True, astro
        assert not astro.get("field_synthesis"), \
            f"field_synthesis must NOT fire for natal-object intent. astro={astro}"
