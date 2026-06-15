"""
Tests for the Mirror Astrology Inventory Audit + Reconnection Task.

Build marker: astrology-chat-v5-advanced-object-reconnect

Validates that the natal_object_engine correctly resolves the advanced
objects that legacy charts may not have stored:

    - Vertex                  → compute via swe.houses_ex (Placidus + sidereal)
    - Anti-Vertex             → derived (Vertex + 180°)
    - Juno                    → compute via swe.JUNO
    - Pholus                  → compute via swe.PHOLUS (centaur)
    - Ceres / Pallas / Vesta  → compute via swe direct constants
    - Lilith / True Lilith    → already wired (lunar apogees)
    - Lots of Fortune/Spirit  → sect-aware formula

Also validates `ensure_advanced_objects()` lazily hydrates legacy charts
for Story / Relationship / Topology / House Inventory surfaces without
mutating the original payload.
"""
from __future__ import annotations

import pytest

from services.natal_object_engine import (
    compute_natal_object,
    ensure_advanced_objects,
    resolve_natal_object_name,
    BUILD_MARKER,
)


# ---- Minimal Pete-shaped chart fixture --------------------------------------
# Reproduces the smoking-gun reality found during audit: a chart with
# planets + nodes + angles but NO stored Juno / Vertex / Anti-Vertex.
@pytest.fixture
def legacy_chart_no_amplifier() -> dict:
    return {
        "astrology": {
            "metadata": {
                "julian_day": 2439947.246527778,           # Pete's natal jd
                "coordinates": {"lat": 3.1073, "lon": 101.6068},
                "svp_degrees": 31.2836,
            },
            "planets": {
                "Sun":   {"longitude": 340.2415, "tropical_longitude": 11.5251,
                          "sign": "Pisces", "degree": 22.2, "house": 4},
                "Moon":  {"longitude": 11.0606, "sign": "Aries", "degree": 11.06,
                          "house": 5},
                "Chiron": {"longitude": 329.1293, "sign": "Pisces", "degree": 11.1, "house": 4},
                "North Node": {"longitude": 347.8377, "sign": "Pisces", "degree": 29.8},
            },
            "angles": {
                "asc": {"longitude": 255.54, "sign": "Sagittarius", "degree": 19.8},
                "mc":  {"longitude": 165.54, "sign": "Virgo", "degree": 23.9},
                "ic":  {"longitude": 345.54, "sign": "Pisces", "degree": 27.5},
                "dc":  {"longitude": 75.54,  "sign": "Gemini", "degree": 18.9},
            },
            "houses": {
                "system": "Equal",
                "cusps": [255.54, 285.54, 315.54, 345.54, 15.54, 45.54,
                          75.54,  105.54, 135.54, 165.54, 195.54, 225.54],
            },
        }
    }


# ============================================================================
# Resolver coverage
# ============================================================================
def test_resolver_recognises_advanced_objects():
    assert resolve_natal_object_name("juno") == "Juno"
    assert resolve_natal_object_name("Juno") == "Juno"
    assert resolve_natal_object_name("vertex") == "Vertex"
    assert resolve_natal_object_name("anti-vertex") == "Anti-Vertex"
    assert resolve_natal_object_name("antivertex") == "Anti-Vertex"
    assert resolve_natal_object_name("pholus") == "Pholus"
    assert resolve_natal_object_name("part of fortune") == "Lot of Fortune"
    assert resolve_natal_object_name("nothing") is None


# ============================================================================
# Vertex / Anti-Vertex compute-on-demand
# ============================================================================
def test_vertex_compute_on_demand(legacy_chart_no_amplifier):
    env = compute_natal_object(legacy_chart_no_amplifier, "Vertex")
    assert env["success"] is True
    assert env["object"] == "Vertex"
    assert env["source"] == "swisseph_houses_ex_on_demand"
    p = env["placement"]
    assert p.get("sign")
    assert p.get("longitude") is not None
    assert p.get("body_type") == "angle"
    # House lookup should succeed because cusps are in the fixture
    assert p.get("house") is not None


def test_anti_vertex_compute_on_demand(legacy_chart_no_amplifier):
    env = compute_natal_object(legacy_chart_no_amplifier, "Anti-Vertex")
    assert env["success"] is True
    assert env["object"] == "Anti-Vertex"
    # Anti-Vertex should sit 180° from Vertex
    vx = compute_natal_object(legacy_chart_no_amplifier, "Vertex")["placement"]
    delta = (env["placement"]["longitude"] - vx["longitude"]) % 360
    assert abs(delta - 180.0) < 0.01


def test_vertex_failure_when_inputs_missing():
    # No metadata → no compute
    env = compute_natal_object({"astrology": {"planets": {}, "angles": {}}}, "Vertex")
    assert env["success"] is False
    assert env["reason"] == "vertex_inputs_missing"


# ============================================================================
# Juno compute-on-demand
# ============================================================================
def test_juno_compute_on_demand(legacy_chart_no_amplifier):
    env = compute_natal_object(legacy_chart_no_amplifier, "Juno")
    assert env["success"] is True
    assert env["object"] == "Juno"
    assert env["source"] == "swisseph_on_demand"
    assert env["placement"].get("sign")


# ============================================================================
# Pholus (bonus centaur — first-class swisseph constant)
# ============================================================================
def test_pholus_compute_on_demand(legacy_chart_no_amplifier):
    env = compute_natal_object(legacy_chart_no_amplifier, "Pholus")
    assert env["success"] is True
    assert env["source"] == "swisseph_on_demand"


# ============================================================================
# Ephemeris-missing objects — must return clean refusal, not crash
# ============================================================================
@pytest.mark.parametrize("name", ["Eros", "Psyche", "Hygiea", "Astraea", "Eris"])
def test_missing_ephemeris_clean_refusal(legacy_chart_no_amplifier, name):
    env = compute_natal_object(legacy_chart_no_amplifier, name)
    # Either success (if the ephemeris file is installed) or a clean
    # ephemeris_file_missing refusal — but NEVER a hard crash and NEVER
    # a silent "no_path_to_compute".
    if not env["success"]:
        assert env["reason"] == "ephemeris_file_missing", (
            f"{name} returned unexpected reason {env['reason']!r}: {env}"
        )
        assert "not wired" in env["message"]


# ============================================================================
# Object-not-wired safety (Phase 5 Lilith→Moon substitution guard)
# ============================================================================
def test_white_moon_selena_not_wired():
    env = compute_natal_object({}, "Selena")
    assert env["success"] is False
    assert env["reason"] == "object_not_wired"
    assert "White Moon Selena is not wired" in env["message"]


def test_unrecognised_object_clean_refusal():
    env = compute_natal_object({}, "RandomBody")
    assert env["success"] is False
    assert env["reason"] == "object_not_recognised"


# ============================================================================
# ensure_advanced_objects() — lazy hydration helper
# ============================================================================
def test_ensure_advanced_objects_hydrates_juno_and_vertex(legacy_chart_no_amplifier):
    chart = legacy_chart_no_amplifier
    assert "Juno" not in chart["astrology"]["planets"]
    assert "vertex" not in chart["astrology"]["angles"]

    hydrated = ensure_advanced_objects(chart)

    # Hydrated has them
    assert "Juno" in hydrated["astrology"]["planets"]
    assert "vertex" in hydrated["astrology"]["angles"]
    assert "anti_vertex" in hydrated["astrology"]["angles"]
    assert hydrated["astrology"]["planets"]["Juno"].get("amplifier") is True
    assert hydrated["astrology"]["angles"]["vertex"].get("amplifier") is True

    # Original chart was NOT mutated
    assert "Juno" not in chart["astrology"]["planets"]
    assert "vertex" not in chart["astrology"]["angles"]


def test_ensure_advanced_objects_idempotent_when_already_stored():
    chart = {
        "astrology": {
            "metadata": {"julian_day": 2439947.246527778,
                         "coordinates": {"lat": 3.1, "lon": 101.6}},
            "planets": {"Juno": {"sign": "Virgo", "longitude": 189.35}},
            "angles":  {"vertex":      {"sign": "Virgo", "longitude": 142.12},
                         "anti_vertex": {"sign": "Pisces", "longitude": 322.12}},
            "houses": {"cusps": [0]*12},
        }
    }
    out = ensure_advanced_objects(chart)
    # Already hydrated → returns the same object unchanged
    assert out is chart


def test_ensure_advanced_objects_handles_none_and_empty():
    assert ensure_advanced_objects(None) is None
    assert ensure_advanced_objects({}) == {}
    assert ensure_advanced_objects({"astrology": None}) == {"astrology": None}


# ============================================================================
# Build marker freshness
# ============================================================================
def test_build_marker_advertises_reconnect():
    assert "v5-advanced-object-reconnect" in BUILD_MARKER
