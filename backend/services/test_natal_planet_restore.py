"""ASTRO-CHAT-PLANET-RESTORE-V1
=================================

Regression-guard for the standard 10 natal planets (Sun → Pluto) in
the Astrology Chat surface.

Background
----------
The Advanced-Object resolver work forked `natal_object_engine.py`
from `transit_object_engine.py` but the standard-planet alias map
was never carried into the fork.  Result: a user asking
"Where is Mercury in my birth chart?" was hitting the
`object_not_recognised` refusal — even though the planet was
present in the stored chart.

This module exercises:

  1.  `resolve_natal_object_name` returns the canonical title-case
      planet name for every standard planet alias and nickname.
  2.  `compute_natal_object` returns success + stored-chart placement
      for each planet (no on-demand asteroid compute).
  3.  The exact user-reported phrase "Where is Mercury in my birth
      chart?" no longer returns `object_not_recognised`.
  4.  The four advanced-object benchmarks (Chiron / Lilith / Vertex /
      North Node) still resolve — no regression on the existing
      catalogue.
  5.  Multi-object phrasing "compare my Mercury and Mars" is detected
      by the chat router's intent classifier as a multi-object natal
      query containing both planets.

No tests touch the transit engine, the advanced-object compute path,
birth data, chart generation, Variant A, relationship/climate/
timeline, or the frontend.
"""
from __future__ import annotations

import pytest

from services.natal_object_engine import (
    resolve_natal_object_name,
    compute_natal_object,
)
from services.astrology_chat_router import (
    classify_astrology_intent,
    _extract_natal_objects,
)


# ────────────────────────────────────────────────────────────────────
# Helper — stored-chart envelope (no compute path engaged)
# ────────────────────────────────────────────────────────────────────
def _chart_with_planet(name: str, *, sign="Gemini", degree=22.4,
                       longitude=82.4, house=10) -> dict:
    """Minimal chart shape that `_read_stored_natal_object` consumes."""
    return {
        "astrology": {
            "planets": {
                name: {
                    "sign":      sign,
                    "degree":    degree,
                    "formatted": f"{int(degree)}°{sign}",
                    "longitude": longitude,
                    "house":     house,
                    "body_type": "planet",
                    "source":    "stored_chart",
                },
            },
            "angles": {},
            "houses": {"cusps": [0,30,60,90,120,150,180,210,240,270,300,330]},
        },
    }


# ────────────────────────────────────────────────────────────────────
# 1.  resolve_natal_object_name — every planet resolves to itself
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("alias,canonical", [
    # Title-case canonical inputs
    ("Sun",        "Sun"),
    ("Moon",       "Moon"),
    ("Mercury",    "Mercury"),
    ("Venus",      "Venus"),
    ("Mars",       "Mars"),
    ("Jupiter",    "Jupiter"),
    ("Saturn",     "Saturn"),
    ("Uranus",     "Uranus"),
    ("Neptune",    "Neptune"),
    ("Pluto",      "Pluto"),
    # Lowercase / mixed-case
    ("mercury",    "Mercury"),
    ("MARS",       "Mars"),
    ("  Saturn ",  "Saturn"),
    # Well-known nicknames
    ("luna",       "Moon"),
    ("Luna",       "Moon"),
    ("jove",       "Jupiter"),
    ("Jove",       "Jupiter"),
])
def test_standard_planet_aliases_resolve(alias, canonical):
    assert resolve_natal_object_name(alias) == canonical


@pytest.mark.parametrize("planet", [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
])
def test_resolve_planet_no_longer_returns_none(planet):
    """Direct guard against the regression — every one of the 10
    canonical planet names must resolve to a non-None value."""
    assert resolve_natal_object_name(planet) is not None


# ────────────────────────────────────────────────────────────────────
# 2.  compute_natal_object — planets served from stored chart
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("planet", [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
])
def test_compute_natal_object_serves_planet_from_stored_chart(planet):
    chart = _chart_with_planet(planet, sign="Gemini", degree=22.4,
                                longitude=82.4, house=10)
    env = compute_natal_object(chart, planet)
    assert env.get("success") is True, env
    assert env.get("object") == planet
    assert env.get("source") == "stored_chart_doc"
    p = env.get("placement") or {}
    assert p.get("sign") == "Gemini"
    assert p.get("house") == 10


def test_compute_natal_object_planet_lowercase_alias_resolves():
    chart = _chart_with_planet("Mercury")
    env = compute_natal_object(chart, "mercury")
    assert env.get("success") is True
    assert env.get("object") == "Mercury"


# ────────────────────────────────────────────────────────────────────
# 3.  The exact user-reported regression phrase
# ────────────────────────────────────────────────────────────────────
def test_user_reported_mercury_question_no_longer_refused():
    """The exact regression report: 'Where is Mercury in my Birth
    chart?'  Must NOT return object_not_recognised."""
    intent = classify_astrology_intent("Where is Mercury in my Birth chart?")
    assert intent.get("data_mode") == "natal_object"
    assert "Mercury" in (intent.get("objects") or []), intent
    # End-to-end: with a stored chart present, compute_natal_object
    # serves the placement (no refusal envelope).
    chart = _chart_with_planet("Mercury")
    env = compute_natal_object(chart, intent["objects"][0])
    assert env.get("success") is True
    assert env.get("reason") != "object_not_recognised"


def test_venus_question_resolves_and_serves_from_chart():
    """`Tell me about my Venus` — must follow the same path as the
    Mercury case."""
    intent = classify_astrology_intent("Tell me about my Venus")
    assert intent.get("data_mode") == "natal_object"
    assert "Venus" in (intent.get("objects") or [])
    chart = _chart_with_planet("Venus", sign="Taurus", degree=5.0,
                                longitude=35.0, house=2)
    env = compute_natal_object(chart, "Venus")
    assert env.get("success") is True
    assert env.get("placement", {}).get("sign") == "Taurus"


# ────────────────────────────────────────────────────────────────────
# 4.  Existing catalogue (Chiron / Lilith / Vertex / North Node)
#     must still resolve — no regression.
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("alias,canonical", [
    ("Chiron",       "Chiron"),
    ("chiron",       "Chiron"),
    ("Lilith",       "Black Moon Lilith"),
    ("Vertex",       "Vertex"),
    ("North Node",   "North Node"),
    ("rahu",         "North Node"),
    ("South Node",   "South Node"),
    ("ketu",         "South Node"),
])
def test_advanced_objects_still_resolve(alias, canonical):
    assert resolve_natal_object_name(alias) == canonical


# ────────────────────────────────────────────────────────────────────
# 5.  Multi-object query "compare my Mercury and Mars" is detected
#     as multi-object natal containing BOTH planets.
# ────────────────────────────────────────────────────────────────────
def test_multi_object_query_mercury_and_mars():
    """`Compare my Mercury and Mars` — both planets must surface in
    the intent envelope's `objects` list, and `multi=True`, so the
    pairwise builder gets engaged downstream instead of the
    single-object fast path silently dropping Mars."""
    intent = classify_astrology_intent("Compare my Mercury and Mars")
    assert intent.get("data_mode") == "natal_object"
    objects = list(intent.get("objects") or [])
    assert "Mercury" in objects
    assert "Mars"    in objects
    assert intent.get("multi") is True


def test_extractor_picks_up_planet_pair_in_order():
    """Lower-level extractor contract: when planets appear in order
    they are returned in order (pairwise builder relies on this for
    the proof-block ordering)."""
    ordered = _extract_natal_objects("Compare my Mercury and Mars")
    assert ordered[:2] == ["Mercury", "Mars"]


def test_extractor_picks_up_planet_and_advanced_object_pair():
    """Mixed pair — planet × advanced object — must be detected
    correctly without one suppressing the other."""
    ordered = _extract_natal_objects("How do my Saturn and my Chiron interact?")
    assert "Saturn" in ordered
    assert "Chiron" in ordered


def test_lilith_query_does_not_collapse_into_moon():
    """Voice-floor regression guard.  'Lilith' contains the bigram
    'moon' inside 'Black Moon Lilith' — but a bare 'my Lilith' query
    must still resolve to Black Moon Lilith, NOT Moon."""
    objects = _extract_natal_objects("Tell me about my Lilith")
    assert "Black Moon Lilith" in objects
    assert "Moon" not in objects
