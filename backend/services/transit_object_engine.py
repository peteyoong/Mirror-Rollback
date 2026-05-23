"""
Transit Object Engine
=====================
Build marker: astro-chat-transit-grounding-v1

Deterministic, single-object transit lookup for the Astrology Lens chat.

Purpose
-------
Mirror Chat must NOT roleplay astrology. When a user asks where a body is
*right now*, the chat orchestrator calls this engine and feeds the result
to the LLM as authoritative ground truth. The LLM interprets only what
this module returns — it does not invent positions, aspects, or houses.

Strict rules
------------
1. Uses the existing astrology SSOT (True Sidereal, SIDM_USER mode set in
   `calculations/astrology.py`, Equal House primary). No tropical defaults,
   no duplicate constants.
2. Returns a `data_mode` discriminator so the chat layer can pin the LLM
   prompt to a single answering mode and refuse silent fallback to other
   modes.
3. On failure returns `success=False` with a structured reason — never
   speculative interpretation.

Envelope (success=True):
    {
      "success": True,
      "data_mode": "transit_object",
      "object": "Chiron",
      "timestamp": "2026-05-23T01:12:00+00:00",
      "date": "2026-05-23",
      "zodiac_system": "True Sidereal",
      "ayanamsa": "SVP 31.2836° (SIDM_USER)",
      "house_system": "Equal",
      "transit_position": {
          "sign": "Aries",
          "degree": 26.3144,
          "formatted": "26°Aries",
          "absolute_longitude": 26.3144,
          "retrograde": False,
          "speed": 0.0432,
      },
      "natal_house": 5,
      "aspects_to_natal": [
          {
              "natal_body": "Sun",
              "aspect": "conjunction",
              "orb": 1.42,
              "exact_angle": 1.42,
              "applying": True,
              "transit_longitude": 26.31,
              "natal_longitude": 24.89,
          },
          ...
      ],
      "proof": {
          "ephemeris_source": "Swiss Ephemeris (pyswisseph)",
          "sidereal_config": "True Sidereal (SIDM_USER), SVP 31.2836°, J2000",
          "house_system": "Equal House",
          "calculation_date_utc": "2026-05-23T01:12:00+00:00",
          "orb_thresholds": { "conjunction": 8, "opposition": 8, ... },
          "calculation_notes": [...]
      }
    }
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import swisseph as swe

from calculations.astrology import (
    ASPECT_TYPES,
    PLANETS,
    calculate_planet_position_sidereal,
    get_julian_day,
    longitude_to_sign_degree,
    get_house_for_planet,
    normalize_degrees,
)

logger = logging.getLogger(__name__)

BUILD_MARKER = "astro-chat-transit-grounding-v1"

# ---------------------------------------------------------------------------
# Supported objects.
# Resolved name aliases all collapse onto these canonical keys.
# ---------------------------------------------------------------------------

SUPPORTED_OBJECTS: List[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Chiron", "North Node", "South Node",
    "Ascendant", "MC",
]

# Unsupported in V1 — explicit list so we never hallucinate.
NOT_YET_ENABLED: List[str] = [
    "Juno", "Vertex", "Lilith", "Black Moon Lilith",
    "Ceres", "Pallas", "Vesta", "Eris",
]

# Aliases → canonical names.
_OBJECT_ALIASES: Dict[str, str] = {
    "sun": "Sun",
    "moon": "Moon",
    "luna": "Moon",
    "mercury": "Mercury",
    "venus": "Venus",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "jove": "Jupiter",
    "saturn": "Saturn",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "pluto": "Pluto",
    "chiron": "Chiron",
    "north node": "North Node",
    "rahu": "North Node",
    "true node": "North Node",
    "mean node": "North Node",
    "north_node": "North Node",
    "south node": "South Node",
    "ketu": "South Node",
    "south_node": "South Node",
    "ascendant": "Ascendant",
    "asc": "Ascendant",
    "rising": "Ascendant",
    "rising sign": "Ascendant",
    "mc": "MC",
    "midheaven": "MC",
    # Unsupported (resolve so we can return a clean "not yet enabled" answer)
    "juno": "Juno",
    "vertex": "Vertex",
    "lilith": "Lilith",
    "black moon lilith": "Black Moon Lilith",
    "ceres": "Ceres",
    "pallas": "Pallas",
    "vesta": "Vesta",
    "eris": "Eris",
}


def resolve_object_name(raw: Optional[str]) -> Optional[str]:
    """Resolve a user-supplied body name into a canonical key.

    Returns the canonical name (supported OR explicitly not-yet-enabled),
    or None when the string doesn't look like an astrological body at all.
    """
    if not raw or not isinstance(raw, str):
        return None
    key = raw.strip().lower()
    return _OBJECT_ALIASES.get(key)


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _jd_for_date(dt: datetime) -> float:
    dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return get_julian_day(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour, dt_utc.minute, dt_utc.second,
    )


def _compute_transit_longitude(canonical: str, jd: float) -> Optional[Dict[str, Any]]:
    """Resolve canonical body name → sidereal longitude + sign/degree/speed."""
    if canonical == "South Node":
        # South Node = opposite of True Node.
        north = calculate_planet_position_sidereal(swe.TRUE_NODE, jd)
        opp_long = normalize_degrees(north["longitude"] + 180.0)
        sign_info = longitude_to_sign_degree(opp_long)
        return {
            "longitude":   opp_long,
            "latitude":    -north.get("latitude", 0.0),
            "sign":        sign_info["sign"],
            "degree":      sign_info["degree"],
            "formatted":   sign_info["formatted"],
            "speed":       -north.get("speed", 0.0),
            "retrograde":  north.get("speed", 0.0) > 0,  # opposite direction
            "tropical_longitude": north.get("tropical_longitude", 0.0),
        }
    if canonical in ("Ascendant", "MC"):
        # ASC / MC are observer-dependent (need lat/lon) — not part of the
        # transit_object data_mode. Caller should branch elsewhere.
        return None
    planet_id = PLANETS.get(canonical)
    if planet_id is None:
        return None
    return calculate_planet_position_sidereal(planet_id, jd)


def _aspects_to_natal(
    transit_long: float,
    transit_speed: float,
    natal_planets: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Compute aspects from transit body to every natal body.

    Uses the same orb thresholds as `calculations.astrology.calculate_aspects`
    so we don't drift from the SSOT.
    """
    out: List[Dict[str, Any]] = []
    for name, p in (natal_planets or {}).items():
        if name in ("Earth", "South Node"):
            # South Node aspects via North Node opposition — same convention
            # as `calculate_aspects` to keep parity.
            continue
        natal_long = p.get("longitude")
        if natal_long is None:
            continue
        diff = abs(transit_long - natal_long)
        if diff > 180:
            diff = 360 - diff

        for aspect_name, cfg in ASPECT_TYPES.items():
            angle = cfg["angle"]
            orb = cfg["orb"]
            deviation = abs(diff - angle)
            if deviation <= orb:
                natal_speed = p.get("speed", 0.0)
                out.append({
                    "natal_body":         name,
                    "aspect":             aspect_name,
                    "orb":                round(deviation, 2),
                    "exact_angle":        round(diff, 2),
                    "applying":           transit_speed > natal_speed,
                    "transit_longitude":  round(transit_long, 4),
                    "natal_longitude":    round(natal_long, 4),
                })
                break  # one aspect per pair, tightest wins
    out.sort(key=lambda a: a["orb"])
    return out


def compute_transit_object(
    *,
    chart: Dict[str, Any],
    object_name: str,
    date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Compute current transit placement + aspects to natal for a single body.

    Returns a structured envelope (see module docstring). Always includes
    `success`, `data_mode`, and either the full payload or a `reason`.
    """
    canonical = resolve_object_name(object_name)
    if canonical is None:
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "unknown_object",
            "requested": object_name,
        }

    if canonical in NOT_YET_ENABLED:
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "object_not_yet_enabled",
            "object":    canonical,
            "message":   f"{canonical} is not yet enabled in the transit lookup engine.",
        }

    astro = (chart or {}).get("astrology") or {}
    natal_planets = astro.get("planets") or {}
    houses = astro.get("houses") or {}
    cusps = houses.get("cusps") or []

    if not natal_planets or not cusps:
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "natal_chart_incomplete",
            "missing":   [
                k for k in ("planets", "houses.cusps")
                if (k == "planets" and not natal_planets)
                or (k == "houses.cusps" and not cusps)
            ],
        }

    if canonical in ("Ascendant", "MC"):
        # ASC/MC don't transit in the usual sense — they ARE the observer.
        # We don't currently expose body-vs-time ASC/MC lookups; surface
        # this explicitly rather than fabricating.
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "asc_mc_not_a_transit_body",
            "object":    canonical,
            "message":   f"{canonical} is part of your natal chart's geometry; it doesn't transit in the way planets do.",
        }

    dt = date or datetime.now(timezone.utc)
    jd = _jd_for_date(dt)

    pos = _compute_transit_longitude(canonical, jd)
    if not pos:
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "ephemeris_lookup_failed",
            "object":    canonical,
        }

    transit_long = pos["longitude"]
    natal_house = get_house_for_planet(transit_long, cusps)
    aspects = _aspects_to_natal(transit_long, pos.get("speed", 0.0), natal_planets)

    return {
        "success":      True,
        "data_mode":    "transit_object",
        "object":       canonical,
        "timestamp":    dt.astimezone(timezone.utc).isoformat(),
        "date":         dt.astimezone(timezone.utc).strftime("%Y-%m-%d"),
        "zodiac_system": "True Sidereal",
        "ayanamsa":     "SVP ~31.2836° (SIDM_USER, J2000 epoch)",
        "house_system": houses.get("system", "Equal"),
        "transit_position": {
            "sign":               pos["sign"],
            "degree":             round(pos["degree"], 4),
            "formatted":          pos["formatted"],
            "absolute_longitude": round(transit_long, 4),
            "retrograde":         bool(pos.get("retrograde")),
            "speed":              round(float(pos.get("speed", 0.0)), 4),
        },
        "natal_house":   natal_house,
        "aspects_to_natal": aspects,
        "proof": {
            "ephemeris_source":     "Swiss Ephemeris (pyswisseph)",
            "sidereal_config":      "True Sidereal (SIDM_USER) · SVP ~31.2836° · J2000 epoch",
            "house_system":         houses.get("system", "Equal"),
            "calculation_date_utc": dt.astimezone(timezone.utc).isoformat(),
            "orb_thresholds":       {k: v["orb"] for k, v in ASPECT_TYPES.items()},
            "calculation_notes":    [
                f"Build: {BUILD_MARKER}",
                "Aspects computed against all natal planets (excluding Earth, South Node).",
                "South Node treated as opposition of natal North Node.",
                "Equal-orb policy matches calculations/astrology::ASPECT_TYPES.",
            ],
        },
    }


__all__ = [
    "compute_transit_object",
    "resolve_object_name",
    "SUPPORTED_OBJECTS",
    "NOT_YET_ENABLED",
    "BUILD_MARKER",
]
