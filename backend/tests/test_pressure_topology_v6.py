"""
V6 Pressure Topology Engine — end-to-end + unit tests.

Covers:
  • build_pressure_topology + build_narrative_constraints for Pete & Mel
  • classify_astrology_intent for whole-chart / house / natal-Chiron messages
  • POST /api/mirror/chat with lens="astrology" verifies topology expressed
    in prose for Pete + Mel and that V3/V4/V5 regressions still route
    correctly (Chiron natal, 10th house inventory, Mars now).
"""
from __future__ import annotations

import os
import sys
import re
import asyncio
import pytest
import requests

# Backend imports
sys.path.insert(0, "/app/backend")

BASE_URL = (
    os.environ.get("EXPO_BACKEND_URL")
    or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or "https://pressure-topology.preview.emergentagent.com"
).rstrip("/")

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"

# Phrases the LLM must NOT use (per V6 contract)
BANNED_PHRASES = [
    "this placement suggests",
    "this energy",
    "spiritual journey",
    "may feel",
    "might be",
]


# ───────────────────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def pete_chart():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    assert mongo_url and db_name, "MONGO_URL/DB_NAME must be set"

    async def _load():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        doc = await db.charts.find_one({"user_id": PETE_ID})
        client.close()
        return doc

    return asyncio.get_event_loop().run_until_complete(_load())


@pytest.fixture(scope="module")
def mel_chart():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    async def _load():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        doc = await db.charts.find_one({"user_id": MEL_ID})
        client.close()
        return doc

    return asyncio.get_event_loop().run_until_complete(_load())


# ───────────────────────────────────────────────────────────────────────────
# 1. Engine unit tests (Pete)
# ───────────────────────────────────────────────────────────────────────────
class TestPressureTopologyEngine:
    def test_pete_chart_exists(self, pete_chart):
        assert pete_chart is not None, "Pete chart missing from db.charts"
        assert (pete_chart.get("astrology") or {}).get("planets"), \
            "Pete chart missing astrology.planets block"

    def test_pete_topology_structure(self, pete_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(pete_chart)
        assert topo["success"] is True
        assert "build_marker" in topo and "v6" in topo["build_marker"]
        # Required keys
        for k in (
            "dominant_pressures", "contradiction_pairs",
            "overcompensation_patterns", "repetition_loops",
            "activation_hubs", "dominant_signs",
        ):
            assert k in topo, f"missing key {k}"

    def test_pete_compression_detected(self, pete_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(pete_chart)
        types = [p.get("type") for p in topo["dominant_pressures"]]
        assert "compression" in types, \
            f"Pete must show Sun↔Saturn compression, got {types}"

    def test_pete_pisces_stellium_repetition(self, pete_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(pete_chart)
        signs = [
            loop["sign"] for loop in topo["repetition_loops"]
            if loop.get("type") == "sign_repetition"
        ]
        assert "Pisces" in signs, f"Pete must show Pisces repetition, got {signs}"

    def test_pete_third_house_hub(self, pete_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(pete_chart)
        hubs = topo["activation_hubs"]
        assert hubs, "Pete must have activation hubs"
        assert hubs[0]["house"] == 3, \
            f"Pete's top activation hub must be house 3, got {hubs[0]}"

    def test_pete_virgo_pisces_contradiction(self, pete_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(pete_chart)
        themes = [c.get("theme", "") for c in topo["contradiction_pairs"]]
        assert any("precision vs permeability" in t for t in themes), \
            f"Pete must show Virgo↔Pisces contradiction, got {themes}"

    def test_pete_narrative_constraints(self, pete_chart):
        from services.pressure_topology_engine import (
            build_pressure_topology, build_narrative_constraints,
        )
        topo = build_pressure_topology(pete_chart)
        c = build_narrative_constraints(topo)
        assert c["available"] is True
        assert c["core_field"]
        assert c["primary_tension"]
        assert c["dominant_survival_strategy"] == "containment and editing", \
            f"Pete survival strategy must be containment/editing, got {c}"


# ───────────────────────────────────────────────────────────────────────────
# 2. Engine unit tests (Mel)
# ───────────────────────────────────────────────────────────────────────────
class TestPressureTopologyEngineMel:
    def test_mel_chart_exists(self, mel_chart):
        assert mel_chart is not None, f"Mel chart missing for user_id={MEL_ID}"

    def test_mel_pluto_pressure_detected(self, mel_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(mel_chart)
        assert topo["success"] is True
        types = [p.get("type") for p in topo["dominant_pressures"]]
        assert "pluto_pressure" in types, \
            f"Mel must show Sun↔Pluto pressure, got {types}"

    def test_mel_virgo_stellium(self, mel_chart):
        from services.pressure_topology_engine import build_pressure_topology
        topo = build_pressure_topology(mel_chart)
        signs = [
            loop["sign"] for loop in topo["repetition_loops"]
            if loop.get("type") == "sign_repetition"
        ]
        assert "Virgo" in signs, f"Mel must show Virgo stellium, got {signs}"

    def test_mel_survival_strategy(self, mel_chart):
        from services.pressure_topology_engine import (
            build_pressure_topology, build_narrative_constraints,
        )
        c = build_narrative_constraints(build_pressure_topology(mel_chart))
        assert c["dominant_survival_strategy"] == "controlled intensity", \
            f"Mel survival strategy must be controlled intensity, got {c}"


# ───────────────────────────────────────────────────────────────────────────
# 3. Classifier unit tests
# ───────────────────────────────────────────────────────────────────────────
class TestAstrologyIntentClassifier:
    def test_whole_chart_routes_to_pressure_topology(self):
        from services.astrology_chat_router import classify_astrology_intent
        r = classify_astrology_intent("Tell me about my whole chart")
        assert r is not None and r["data_mode"] == "pressure_topology", r

    def test_chart_say_about_me_routes_to_pressure_topology(self):
        from services.astrology_chat_router import classify_astrology_intent
        r = classify_astrology_intent("What does my whole chart say about me")
        assert r is not None and r["data_mode"] == "pressure_topology", r

    def test_10th_house_routes_to_house_inventory(self):
        from services.astrology_chat_router import classify_astrology_intent
        r = classify_astrology_intent("tell me about my 10th house")
        assert r is not None and r["data_mode"] == "house_inventory", r
        assert r.get("house_number") == 10

    def test_natal_chiron_routes_to_natal_object(self):
        from services.astrology_chat_router import classify_astrology_intent
        r = classify_astrology_intent("where is my natal Chiron")
        assert r is not None and r["data_mode"] == "natal_object", r

    def test_mars_now_routes_to_transit_object(self):
        from services.astrology_chat_router import classify_astrology_intent
        r = classify_astrology_intent("where is Mars now")
        assert r is not None and r["data_mode"] == "transit_object", r


# ───────────────────────────────────────────────────────────────────────────
# 4. End-to-end /api/mirror/chat tests
# ───────────────────────────────────────────────────────────────────────────
def _post_chat(api_client, user_id, message, timeout=120):
    return api_client.post(
        f"{BASE_URL}/api/mirror/chat",
        json={"user_id": user_id, "message": message, "lens": "astrology"},
        timeout=timeout,
    )


class TestMirrorChatPressureTopology:
    def test_pete_whole_chart_expresses_topology(self, api_client):
        r = _post_chat(api_client, PETE_ID, "Tell me about my whole chart")
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
        body = r.json()
        prose = body.get("response", "")
        assert prose, "Empty response"
        debug = body.get("debug") or {}
        astro_chat = debug.get("astro_chat") or {}

        # Debug must reflect topology used
        assert astro_chat.get("pressure_topology_used") is True, \
            f"debug.astro_chat should show pressure_topology_used=True. Got: {astro_chat}"
        assert astro_chat.get("intent_detected") == "pressure_topology", \
            f"intent_detected should be pressure_topology, got {astro_chat.get('intent_detected')}"

        # Banned phrases
        lower = prose.lower()
        for bp in BANNED_PHRASES:
            assert bp not in lower, f"Banned phrase found: '{bp}' in prose"
        # No trailing question mark
        assert not prose.strip().endswith("?"), \
            "Response must not end with a question mark"

    def test_pete_response_mentions_topology_themes(self, api_client):
        """Lighter content check — at least ONE of the deterministic
        topology cues should surface in the prose."""
        r = _post_chat(api_client, PETE_ID, "Tell me about my whole chart")
        assert r.status_code == 200
        prose_lower = r.json()["response"].lower()
        # Check for any sign of topology expression
        cues = [
            "saturn", "pisces", "third house", "3rd house",
            "permeability", "precision", "containment", "editing",
            "compression",
        ]
        hits = [c for c in cues if c in prose_lower]
        assert len(hits) >= 2, \
            f"Expected ≥2 topology cues in prose. Hits={hits}. Prose: {prose_lower[:400]}"

    def test_mel_whole_chart_expresses_topology(self, api_client):
        r = _post_chat(api_client, MEL_ID, "What does my whole chart say about me")
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:400]}"
        body = r.json()
        debug = body.get("debug") or {}
        astro_chat = debug.get("astro_chat") or {}
        assert astro_chat.get("pressure_topology_used") is True, \
            f"Mel debug.astro_chat should show pressure_topology_used=True. Got: {astro_chat}"
        prose = body.get("response", "").lower()
        # Banned check
        for bp in BANNED_PHRASES:
            assert bp not in prose, f"Banned phrase '{bp}' in Mel response"
        # Mel topology cues
        cues = ["pluto", "virgo", "intensity", "control", "precision", "standards"]
        hits = [c for c in cues if c in prose]
        assert len(hits) >= 2, \
            f"Mel response missing topology cues. Hits={hits}. Prose: {prose[:400]}"


# ───────────────────────────────────────────────────────────────────────────
# 5. Regression tests (V3 / V4 / V5 routing still wins)
# ───────────────────────────────────────────────────────────────────────────
class TestRoutingRegression:
    def test_pete_natal_chiron_uses_natal_object_engine(self, api_client):
        r = _post_chat(api_client, PETE_ID, "where is my natal Chiron")
        assert r.status_code == 200, r.text[:400]
        astro_chat = (r.json().get("debug") or {}).get("astro_chat") or {}
        assert astro_chat.get("natal_object_used") is True, \
            f"Chiron should route to natal_object engine, got astro_chat={astro_chat}"
        assert astro_chat.get("intent_detected") == "natal_object", \
            f"intent_detected should be natal_object, got {astro_chat.get('intent_detected')}"
        prose = r.json()["response"].lower()
        assert "chiron" in prose, f"Response must mention Chiron, got: {prose[:300]}"

    def test_pete_10th_house_uses_inventory_engine(self, api_client):
        r = _post_chat(api_client, PETE_ID, "tell me about my 10th house")
        assert r.status_code == 200, r.text[:400]
        astro_chat = (r.json().get("debug") or {}).get("astro_chat") or {}
        assert astro_chat.get("house_inventory_used") is True, \
            f"10th house should route to house_inventory engine, got astro_chat={astro_chat}"
        assert astro_chat.get("house_number") == 10, \
            f"house_number should be 10, got {astro_chat.get('house_number')}"
        # Verify response includes actual objects in house 10 (no hallucination)
        objects = astro_chat.get("objects_in_house") or []
        assert objects, f"Should report objects in Pete's house 10, got {objects}"
        prose = r.json()["response"].lower()
        # At least one of the actual objects should be mentioned
        assert any(o.lower() in prose for o in objects), \
            f"Response should mention {objects}; got prose: {prose[:300]}"

    def test_pete_mars_now_uses_transit_engine(self, api_client):
        r = _post_chat(api_client, PETE_ID, "where is Mars now")
        assert r.status_code == 200, r.text[:400]
        astro_chat = (r.json().get("debug") or {}).get("astro_chat") or {}
        assert astro_chat.get("transit_object_used") is True, \
            f"Mars now should route to transit_object engine, got astro_chat={astro_chat}"
        assert astro_chat.get("intent_detected") == "transit_object", \
            f"intent_detected should be transit_object, got {astro_chat.get('intent_detected')}"
