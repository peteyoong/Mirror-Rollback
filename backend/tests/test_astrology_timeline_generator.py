"""
Audit tests for services/astrology_timeline_generator.py
========================================================

Validates the Python port of the frontend AstrologyTimelineTab generator
produces a structured payload that:
  * Maps Sun-sign → year_theme/arc verbatim from SIGN_PATTERNS table
  * Builds 4 phases (Recognition / Confrontation / Crossroads / Integration)
    keyed to the current calendar year
  * Produces 3 turning points (Late April / Mid-August / Early November)
  * Threads natal house placements into life-area phrasing
  * Reports source = "real_astrology_timeline"
  * Survives an end-to-end pipeline through
    astrology_timeline_interpreter.build_timeline_context().
"""

import sys
from datetime import datetime
from pathlib import Path

# Ensure the backend dir is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from services import astrology_timeline_generator as atg  # noqa: E402
from services import astrology_timeline_interpreter as ati  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chart(sun="Pisces", sun_house=3, moon_house=4, mars_house=4,
           venus_house=2, saturn_house=3):
    """Build a minimal chart_doc shape that the generator accepts."""
    return {
        "user_id": "test_user",
        "astrology": {
            "planets": {
                "Sun":    {"sign": sun,        "house": sun_house},
                "Moon":   {"sign": "Aries",    "house": moon_house},
                "Mars":   {"sign": "Aries",    "house": mars_house},
                "Venus":  {"sign": "Aquarius", "house": venus_house},
                "Saturn": {"sign": "Pisces",   "house": saturn_house},
            },
        },
    }


# ---------------------------------------------------------------------------
# Generator output structure
# ---------------------------------------------------------------------------

def test_generator_produces_expected_top_level_keys():
    payload = atg.generate_astrology_timeline(_chart())
    assert payload is not None
    expected = {
        "year_theme", "year_question", "arc", "tension",
        "phases", "turning_points", "decision_windows",
        "house_hints", "year", "source", "generator_version",
    }
    assert expected.issubset(payload.keys()), set(payload) ^ expected
    assert payload["source"] == "real_astrology_timeline"


def test_generator_returns_none_when_chart_missing():
    assert atg.generate_astrology_timeline(None) is None
    assert atg.generate_astrology_timeline({}) is None
    assert atg.generate_astrology_timeline({"astrology": {}}) is None


def test_generator_uses_sun_sign_pattern_table():
    # Pisces should produce the Pisces year_theme
    payload = atg.generate_astrology_timeline(_chart(sun="Pisces"))
    pisces_theme = atg.SIGN_PATTERNS["Pisces"]["year_theme"]
    assert payload["year_theme"] == pisces_theme
    assert payload["tension"] == "absorbing vs. protecting"

    # Capricorn should produce a different one
    payload2 = atg.generate_astrology_timeline(_chart(sun="Capricorn"))
    cap_theme = atg.SIGN_PATTERNS["Capricorn"]["year_theme"]
    assert payload2["year_theme"] == cap_theme
    assert payload["year_theme"] != payload2["year_theme"]


def test_generator_threads_house_areas_into_phase_descriptions():
    # Pete-like layout: Sun in 3rd, Moon in 4th, Venus in 2nd, Saturn in 3rd
    payload = atg.generate_astrology_timeline(_chart(
        sun_house=3, moon_house=4, venus_house=2, saturn_house=3,
    ))
    q1 = payload["phases"][0]
    assert q1["name"] == "Recognition"
    # 3rd house life area = "communication, decisions, and daily routines"
    assert "communication" in q1["description"].lower()
    # 4th house = "home, family, and emotional foundation"
    assert "home" in q1["description"].lower() or "emotional" in q1["description"].lower()
    # 2nd house short = "security"
    assert "security" in q1["description"].lower()


def test_generator_builds_3_turning_points_with_canonical_timing():
    payload = atg.generate_astrology_timeline(_chart())
    tps = payload["turning_points"]
    assert len(tps) == 3
    # Canonical timings the spec requires
    timings = [tp["timing"] for tp in tps]
    assert any("Late April" in t for t in timings)
    assert any("Mid-August" in t for t in timings)
    assert any("Early November" in t for t in timings)
    # Canonical types
    assert tps[0]["type"] == "confrontation"
    assert tps[1]["type"] == "decision"
    assert tps[2]["type"] == "integration"
    # Each turning point has if_avoided text
    for tp in tps:
        assert tp["if_avoided"]


def test_generator_includes_current_year_in_periods():
    year = datetime.utcnow().year
    payload = atg.generate_astrology_timeline(_chart(), current_year=year)
    for ph in payload["phases"]:
        assert str(year) in ph["period"]
    for tp in payload["turning_points"]:
        assert str(year) in tp["timing"]


# ---------------------------------------------------------------------------
# Pipeline integration with the interpreter
# ---------------------------------------------------------------------------

def test_pipeline_real_payload_produces_real_source():
    """When real chart-derived payload flows through the interpreter, the
    interpreter must keep source = real_astrology_timeline."""
    chart = _chart(sun="Pisces", sun_house=3, moon_house=4,
                   mars_house=4, venus_house=2, saturn_house=3)
    payload = atg.generate_astrology_timeline(chart)
    # May 15 2026 → Q2 → Confrontation
    ctx = ati.build_timeline_context(
        user_id="u1",
        astrology_timeline_payload=payload,
        current_date="2026-05-15",
        domain="relationships",
    )
    assert ctx["source"] == "real_astrology_timeline"
    assert ctx["current_phase"]["name"] == "Confrontation"
    assert ctx["next_phase"]["name"] == "Crossroads"
    # Confidence should be high (year_theme + arc + ≥3 phases + ≥1 tp)
    assert ctx["confidence"] == "high"
    # Turning points: confrontation/decision/integration types
    types = [tp["type"] for tp in ctx["key_turning_points"]]
    assert "confrontation" in types
    assert "decision" in types
    assert "integration" in types


def test_pipeline_no_payload_marks_scaffold_source():
    ctx = ati.build_timeline_context(
        user_id="u2",
        astrology_timeline_payload=None,
        current_date="2026-05-15",
    )
    assert ctx["source"] == "deterministic_scaffold"
    assert ctx["confidence"] == "low"
    assert ctx["current_phase"]["name"] in {
        "Recognition", "Confrontation", "Crossroads", "Integration",
    }


def test_pipeline_domain_relevance_picks_up_house_areas():
    """A chart with Venus in 7th + Saturn in 6th should surface domain
    relevance for relationships+work because the rendered phase
    descriptions include those keywords."""
    chart = _chart(sun_house=3, moon_house=4, mars_house=4,
                   venus_house=7, saturn_house=6)
    payload = atg.generate_astrology_timeline(chart)
    ctx = ati.build_timeline_context(
        user_id="u3",
        astrology_timeline_payload=payload,
        current_date="2026-05-15",
        domain="relationships",
    )
    dr = ctx["domain_relevance"]
    assert "relationships" in dr
    assert "work" in dr  # 6th-house language ("work, health, and daily habits")
