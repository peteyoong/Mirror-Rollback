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

BUILD_MARKER = "astro-object-expansion-v1"

# ---------------------------------------------------------------------------
# Supported objects.
# Resolved name aliases all collapse onto these canonical keys.
# Object metadata + ephemeris routing lives in OBJECT_REGISTRY below.
# ---------------------------------------------------------------------------

SUPPORTED_OBJECTS: List[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Chiron", "North Node", "South Node",
    "Ascendant", "MC",
    # V1.1 additions — asteroids + lunar apogee. Eris may degrade to
    # ephemeris-missing depending on installed swisseph data files.
    "Juno", "Vesta", "Ceres", "Pallas",
    "Lilith", "Eris",
    # Calculated chart point — natal only via chart.angles.vertex.
    # Current ("transit") Vertex is intentionally NOT supported and
    # returns vertex_current_transit_not_supported.
    "Vertex", "Anti-Vertex",
]

# Objects that V1 will not enable yet, kept as an explicit gate. Empty in
# V1.1 — everything in the above SUPPORTED list now has an engine path.
NOT_YET_ENABLED: List[str] = []


# Object metadata for the proof layer. The chat orchestrator and any
# downstream consumers can use object_type to render differently and to
# route requests through the right computation path.
OBJECT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Classical luminaries + planets
    "Sun":          {"object_type": "planet",            "ephemeris_constant": "swe.SUN"},
    "Moon":         {"object_type": "planet",            "ephemeris_constant": "swe.MOON"},
    "Mercury":      {"object_type": "planet",            "ephemeris_constant": "swe.MERCURY"},
    "Venus":        {"object_type": "planet",            "ephemeris_constant": "swe.VENUS"},
    "Mars":         {"object_type": "planet",            "ephemeris_constant": "swe.MARS"},
    "Jupiter":      {"object_type": "planet",            "ephemeris_constant": "swe.JUPITER"},
    "Saturn":       {"object_type": "planet",            "ephemeris_constant": "swe.SATURN"},
    "Uranus":       {"object_type": "planet",            "ephemeris_constant": "swe.URANUS"},
    "Neptune":      {"object_type": "planet",            "ephemeris_constant": "swe.NEPTUNE"},
    "Pluto":        {"object_type": "planet",            "ephemeris_constant": "swe.PLUTO"},
    # Lunar nodes + Chiron
    "Chiron":       {"object_type": "minor_body",        "ephemeris_constant": "swe.CHIRON"},
    "North Node":   {"object_type": "lunar_point",       "ephemeris_constant": "swe.TRUE_NODE"},
    "South Node":   {"object_type": "lunar_point",       "ephemeris_constant": "derived(-swe.TRUE_NODE)"},
    # Calculated geometric points — observer-dependent
    "Ascendant":    {"object_type": "calculated_point",  "ephemeris_constant": "derived(houses)"},
    "MC":           {"object_type": "calculated_point",  "ephemeris_constant": "derived(houses)"},
    # V1.1 asteroids
    "Juno":         {"object_type": "asteroid",          "ephemeris_constant": "swe.JUNO"},
    "Vesta":        {"object_type": "asteroid",          "ephemeris_constant": "swe.VESTA"},
    "Ceres":        {"object_type": "asteroid",          "ephemeris_constant": "swe.CERES"},
    "Pallas":       {"object_type": "asteroid",          "ephemeris_constant": "swe.PALLAS"},
    # Eris is a distant body — requires an extra ephemeris file to be
    # present (se136199.se1). If missing, the engine returns
    # object_supported_but_ephemeris_missing rather than guessing.
    "Eris":         {"object_type": "minor_body",        "ephemeris_constant": "swe.AST_OFFSET + 136199"},
    # Lilith — default Mean Black Moon Lilith (lunar apogee). Distinction
    # surfaced in proof.lilith_type.
    "Lilith":       {"object_type": "lunar_point",       "ephemeris_constant": "swe.MEAN_APOG",
                     "lilith_type": "mean_black_moon_lilith"},
    # Vertex / Anti-Vertex — natal-only chart points sourced from
    # chart.astrology.angles. Transit lookup is intentionally refused.
    "Vertex":       {"object_type": "calculated_chart_point",
                     "ephemeris_constant": "derived(chart.angles.vertex)"},
    "Anti-Vertex":  {"object_type": "calculated_chart_point",
                     "ephemeris_constant": "derived(chart.angles.anti_vertex)"},
}

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
    # V1.1 — asteroids + chart points + Lilith
    "juno": "Juno",
    "juno asteroid": "Juno",
    "vesta": "Vesta",
    "vesta asteroid": "Vesta",
    "ceres": "Ceres",
    "ceres asteroid": "Ceres",
    "pallas": "Pallas",
    "pallas athena": "Pallas",
    "lilith": "Lilith",
    "black moon lilith": "Lilith",
    "bml": "Lilith",
    "mean lilith": "Lilith",
    "mean black moon lilith": "Lilith",
    "eris": "Eris",
    "vertex": "Vertex",
    "vx": "Vertex",
    "anti-vertex": "Anti-Vertex",
    "antivertex": "Anti-Vertex",
    "anti vertex": "Anti-Vertex",
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
    """Resolve canonical body name → sidereal longitude + sign/degree/speed.

    Returns:
        dict on success
        None when body is observer-dependent (Ascendant/MC) and should be
            handled by the caller via a separate refusal path
        Dict with `__ephemeris_missing__: True` when the body IS supported
            but the required swisseph data file is not present (e.g., Eris
            needs se136199.se1). Caller surfaces a clean structured failure.
    """
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
    if canonical in ("Ascendant", "MC", "Vertex", "Anti-Vertex"):
        # Geometric / chart-derived points. Caller handles via separate paths.
        return None

    # Map canonical → swisseph body id.
    swe_id = {
        "Sun":     swe.SUN,     "Moon":    swe.MOON,
        "Mercury": swe.MERCURY, "Venus":   swe.VENUS,   "Mars": swe.MARS,
        "Jupiter": swe.JUPITER, "Saturn":  swe.SATURN,
        "Uranus":  swe.URANUS,  "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
        "Chiron":  swe.CHIRON,
        "North Node": swe.TRUE_NODE,
        # V1.1 asteroids
        "Juno":    swe.JUNO,    "Vesta":   swe.VESTA,
        "Ceres":   swe.CERES,   "Pallas":  swe.PALLAS,
        # Mean Black Moon Lilith (lunar apogee).
        "Lilith":  swe.MEAN_APOG,
        # Eris is asteroid #136199 — needs se136199.se1 ephemeris file.
        "Eris":    int(swe.AST_OFFSET + 136199),
    }.get(canonical)
    if swe_id is None:
        return None
    try:
        return calculate_planet_position_sidereal(swe_id, jd)
    except (swe.Error, ValueError, RuntimeError) as exc:
        # Ephemeris file missing or unreadable for distant minor body.
        # Signal upward without faking a position.
        logger.warning(
            f"[TransitObjectEngine] ephemeris lookup failed for "
            f"{canonical} (swe_id={swe_id}): {exc}"
        )
        return {"__ephemeris_missing__": True, "error": str(exc)}


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
            "reason":    "object_not_supported",
            "object":    canonical,
            "message":   f"{canonical} is not yet enabled in the transit lookup engine.",
        }

    # Vertex / Anti-Vertex — chart points, not transiting bodies. V1.1
    # supports natal Vertex via chart.angles.vertex but refuses
    # "current Vertex" computation with a clear structured reason.
    if canonical in ("Vertex", "Anti-Vertex"):
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "vertex_current_transit_not_supported",
            "object":    canonical,
            "object_type": "calculated_chart_point",
            "message": (
                f"{canonical} is a calculated chart point rather than a "
                "moving body. I can show your natal " + canonical +
                " and transits TO it, but current " + canonical +
                " computation is not enabled yet."
            ),
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
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "asc_mc_not_a_transit_body",
            "object":    canonical,
            "object_type": "calculated_point",
            "message":   f"{canonical} is part of your natal chart's geometry; it doesn't transit in the way planets do.",
        }

    dt = date or datetime.now(timezone.utc)
    jd = _jd_for_date(dt)

    pos = _compute_transit_longitude(canonical, jd)
    if pos is None:
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "ephemeris_lookup_failed",
            "object":    canonical,
        }
    if pos.get("__ephemeris_missing__"):
        return {
            "success":   False,
            "data_mode": "transit_object",
            "reason":    "object_supported_but_ephemeris_missing",
            "object":    canonical,
            "object_type": OBJECT_REGISTRY.get(canonical, {}).get("object_type"),
            "message": (
                f"{canonical} is recognised but the swisseph ephemeris file "
                f"for this body is not installed on the server."
            ),
            "diagnostic": pos.get("error"),
        }

    transit_long = pos["longitude"]
    natal_house = get_house_for_planet(transit_long, cusps)
    aspects = _aspects_to_natal(transit_long, pos.get("speed", 0.0), natal_planets)

    registry_entry = OBJECT_REGISTRY.get(canonical, {})
    proof = {
        "ephemeris_source":     "Swiss Ephemeris (pyswisseph)",
        "sidereal_config":      "True Sidereal (SIDM_USER) · SVP ~31.2836° · J2000 epoch",
        "house_system":         houses.get("system", "Equal"),
        "calculation_date_utc": dt.astimezone(timezone.utc).isoformat(),
        "orb_thresholds":       {k: v["orb"] for k, v in ASPECT_TYPES.items()},
        "object_type":          registry_entry.get("object_type"),
        "ephemeris_constant":   registry_entry.get("ephemeris_constant"),
        "calculation_notes":    [
            f"Build: {BUILD_MARKER}",
            "Aspects computed against all natal planets (excluding Earth, South Node).",
            "South Node treated as opposition of natal North Node.",
            "Equal-orb policy matches calculations/astrology::ASPECT_TYPES.",
        ],
    }
    # Surface Lilith disambiguation so advanced users can audit the choice.
    if canonical == "Lilith":
        proof["lilith_type"] = registry_entry.get("lilith_type", "mean_black_moon_lilith")
        proof["calculation_notes"].append(
            "Lilith resolved to Mean Black Moon Lilith (lunar apogee). "
            "True/osculating BML and asteroid Lilith are not surfaced as 'Lilith' in V1.1."
        )

    return {
        "success":      True,
        "data_mode":    "transit_object",
        "object":       canonical,
        "object_type":  registry_entry.get("object_type"),
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
        "proof": proof,
    }


__all__ = [
    "compute_transit_object",
    "resolve_object_name",
    "SUPPORTED_OBJECTS",
    "NOT_YET_ENABLED",
    "BUILD_MARKER",
]
