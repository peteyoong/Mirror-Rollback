"""
Natal Object Engine
===================

Build marker: astrology-chat-master-interpreter-v3

Answers questions of the shape "Tell me about my Lilith" / "what house
is my Chiron in" / "what does my Vertex mean" by reading natal
positions DIRECTLY from the stored chart doc and (for objects not
stored) computing them on demand via Swiss Ephemeris.

CRITICAL CORRECTNESS RULE
-------------------------
If a user asks about an object the engine cannot provide (e.g. asteroid
Pallas), this engine MUST return success=False with a verbatim
"<Object> is not wired into the astrology engine yet" message.
The chat layer is then required to surface that message UNCHANGED and
MUST NOT substitute a different placement as if it were the requested
one.  (See Phase 5 of astrology-chat-master-interpreter-v3 — the
"Lilith → natal Moon" substitution bug this fixes.)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone as _tz
from typing import Any, Dict, Optional

import swisseph as swe

from calculations.sidereal_config import SVP_DEGREES
from calculations.astrology import (
    longitude_to_sign_degree,
    normalize_degrees,
    get_house_for_planet,
)

logger = logging.getLogger(__name__)

BUILD_MARKER = "astrology-chat-v4-object-coverage"

# Canonical name → swisseph body constant (for objects we COMPUTE on demand
# because they're not pre-stored in the chart doc).
#
# Asteroids use swe.AST_OFFSET + minor planet number. The base asteroid
# file (seas_18.se1) is bundled with pyswisseph and covers the major
# main-belt bodies and many named asteroids.
_AST_OFFSET = getattr(swe, "AST_OFFSET", 10000)
_COMPUTE_ON_DEMAND = {
    "Black Moon Lilith":      swe.MEAN_APOG,   # Mean Lunar Apogee — standard BML
    "True Black Moon Lilith": swe.OSCU_APOG,   # Osculating apogee, less common
    "Ceres":                  _AST_OFFSET + 1,
    "Pallas":                 _AST_OFFSET + 2,
    "Vesta":                  _AST_OFFSET + 4,
    "Astraea":                _AST_OFFSET + 5,
    "Hygiea":                 _AST_OFFSET + 10,
    "Psyche":                 _AST_OFFSET + 16,
    "Eros":                   _AST_OFFSET + 433,
    "Eris":                   _AST_OFFSET + 136199,   # needs s136199s.se1 ephemeris
}

# Aliases — the surface the user is likely to use → canonical name.
_ALIAS = {
    # Lilith family
    "lilith":              "Black Moon Lilith",
    "black moon":          "Black Moon Lilith",
    "black moon lilith":   "Black Moon Lilith",
    "bml":                 "Black Moon Lilith",
    "mean lilith":         "Black Moon Lilith",
    "true lilith":         "True Black Moon Lilith",
    "true black moon":     "True Black Moon Lilith",
    # White Moon family — NOT WIRED (no standard swisseph constant)
    "selena":              "White Moon Selena",
    "white moon":          "White Moon Selena",
    "white moon selena":   "White Moon Selena",
    # Stored-in-chart aliases
    "chiron":              "Chiron",
    "north node":          "North Node",
    "north_node":          "North Node",
    "rahu":                "North Node",
    "south node":          "South Node",
    "south_node":          "South Node",
    "ketu":                "South Node",
    "vertex":              "Vertex",
    "anti-vertex":         "Anti-Vertex",
    "antivertex":          "Anti-Vertex",
    "anti vertex":         "Anti-Vertex",
    "juno":                "Juno",
    # Computed on demand
    "ceres":               "Ceres",
    "pallas":              "Pallas",
    "vesta":               "Vesta",
    "eris":                "Eris",
    "eros":                "Eros",
    "psyche":              "Psyche",
    "hygiea":              "Hygiea",
    "hygieia":             "Hygiea",
    "astraea":             "Astraea",
    # Lots / Arabic Parts
    "part of fortune":     "Lot of Fortune",
    "lot of fortune":      "Lot of Fortune",
    "pars fortuna":        "Lot of Fortune",
    "fortuna":             "Lot of Fortune",
    "part of spirit":      "Lot of Spirit",
    "lot of spirit":       "Lot of Spirit",
    "pars spiritus":       "Lot of Spirit",
    # Lots not yet implemented (will fall into _NOT_WIRED)
    "lot of eros":         "Lot of Eros",
    "lot of necessity":    "Lot of Necessity",
    "lot of courage":      "Lot of Courage",
    "lot of victory":      "Lot of Victory",
    "lot of nemesis":      "Lot of Nemesis",
    "lot of basis":        "Lot of Basis",
    "lot of marriage":     "Lot of Marriage",
}

# Objects that we ACKNOWLEDGE but explicitly DO NOT support yet.
# Any query for these returns the verbatim not-wired message —
# NEVER substituted with another body.
_NOT_WIRED = {
    "White Moon Selena",     # no standard ephemeris point
    "Dark Moon Lilith",      # Waldemath; not in std swisseph
    "Lot of Eros", "Lot of Necessity", "Lot of Courage",
    "Lot of Victory", "Lot of Nemesis", "Lot of Basis",
    "Lot of Marriage", "Lot of Children", "Lot of Father",
    "Lot of Mother", "Lot of Siblings", "Lot of Career",
    "Lot of Profession", "Lot of Wealth", "Lot of Death",
    "Lot of Illness", "Lot of Exaltation",
}

# Computable via formula (no swisseph body needed)
_FORMULA_OBJECTS = {"Lot of Fortune", "Lot of Spirit"}


def resolve_natal_object_name(raw: str) -> Optional[str]:
    """Map a user-typed object name to its canonical form. Returns None
    if no match."""
    if not raw or not isinstance(raw, str):
        return None
    key = raw.strip().lower()
    if key in _ALIAS:
        return _ALIAS[key]
    # Title-case match (e.g. "Chiron")
    cap = raw.strip()
    known_titles = (
        list(_COMPUTE_ON_DEMAND.keys())
        + ["Chiron", "North Node", "South Node", "Vertex", "Anti-Vertex", "Juno"]
        + list(_FORMULA_OBJECTS)
        + list(_NOT_WIRED)
    )
    for canon in known_titles:
        if cap.lower() == canon.lower():
            return canon
    return None


def _compute_lot(
    chart: Dict[str, Any],
    lot_name: str,
) -> Optional[Dict[str, Any]]:
    """Compute a sect-aware Arabic Part / Lot.

    Lot of Fortune:
        day: ASC + Moon - Sun
        night: ASC + Sun - Moon
    Lot of Spirit:
        day: ASC + Sun - Moon
        night: ASC + Moon - Sun

    Sect: day if natal Sun is above the horizon (houses 7–12), else
    night. We approximate by checking the natal Sun house.
    """
    astro = (chart or {}).get("astrology") or {}
    planets = astro.get("planets") or {}
    angles = astro.get("angles") or {}
    sun = planets.get("Sun") or {}
    moon = planets.get("Moon") or {}
    asc = angles.get("asc") or {}

    # Need tropical longitudes for the formula
    def _trop(p):
        return p.get("tropical_longitude") if p.get("tropical_longitude") is not None else (
            (p.get("longitude") + SVP_DEGREES) if p.get("longitude") is not None else None
        )
    sun_t = _trop(sun); moon_t = _trop(moon); asc_t = _trop(asc)
    if sun_t is None or moon_t is None or asc_t is None:
        return None

    # Sect: day chart if Sun house in 7..12 (above horizon in Equal house);
    # fall back to longitude comparison if house missing.
    sun_house = sun.get("house")
    if sun_house is not None:
        is_day = sun_house in (7, 8, 9, 10, 11, 12)
    else:
        # Sun > MC tropical → day-ish. Crude fallback.
        mc = angles.get("mc") or {}
        mc_t = _trop(mc) or 0.0
        is_day = ((sun_t - mc_t + 360.0) % 360.0) < 180.0

    if lot_name == "Lot of Fortune":
        lot_trop = (asc_t + moon_t - sun_t) % 360.0 if is_day else (asc_t + sun_t - moon_t) % 360.0
        formula = "ASC + Moon - Sun" if is_day else "ASC + Sun - Moon"
    elif lot_name == "Lot of Spirit":
        lot_trop = (asc_t + sun_t - moon_t) % 360.0 if is_day else (asc_t + moon_t - sun_t) % 360.0
        formula = "ASC + Sun - Moon" if is_day else "ASC + Moon - Sun"
    else:
        return None

    sid = normalize_degrees(lot_trop - SVP_DEGREES)
    sign_data = longitude_to_sign_degree(sid, tropical_longitude=lot_trop)
    house = None
    cusps = astro.get("houses") or astro.get("house_cusps")
    if cusps:
        try:
            house = get_house_for_planet(sid, cusps)
        except Exception:
            pass
    return {
        **sign_data,
        "longitude":          sid,
        "tropical_longitude": lot_trop,
        "house":              house,
        "body_type":          "lot_formula",
        "source":             "sect_aware_formula",
        "sect":               "day" if is_day else "night",
        "formula":            formula,
    }


def _read_stored_natal_object(chart: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    """Read a body's natal position from the stored chart doc.

    Returns None if the body isn't present in the chart.
    """
    astro = (chart or {}).get("astrology") or {}
    planets = (astro.get("planets") or {})
    angles = (astro.get("angles") or {})

    # Direct planet/asteroid hit
    if name in planets:
        p = dict(planets[name])
        if "house" not in p or p.get("house") is None:
            # Compute house from cusps if we have them
            cusps = astro.get("houses") or astro.get("house_cusps")
            if cusps and "longitude" in p:
                try:
                    p["house"] = get_house_for_planet(p["longitude"], cusps)
                except Exception:
                    pass
        return p

    # Angle/axis (asc, mc, dc, ic, vertex, anti_vertex)
    angle_key_map = {
        "Vertex":      "vertex",
        "Anti-Vertex": "anti_vertex",
        "Ascendant":   "asc",
        "Midheaven":   "mc",
        "MC":          "mc",
        "AC":          "asc",
        "Descendant":  "dc",
        "IC":          "ic",
    }
    a_key = angle_key_map.get(name)
    if a_key and a_key in angles:
        a = dict(angles[a_key])
        a["body_type"] = "angle"
        return a

    return None


def _compute_natal_lilith(
    chart: Dict[str, Any],
    body_const: int,
) -> Optional[Dict[str, Any]]:
    """Compute a natal position via Swiss Ephemeris for objects not stored
    in the chart doc (Lilith family).

    Uses the chart's stored birth_utc / JD if available; otherwise returns
    None.
    """
    astro = (chart or {}).get("astrology") or {}
    metadata = astro.get("metadata") or {}
    # The chart stores julian_day at birth — prefer that.
    jd = metadata.get("julian_day") or metadata.get("jd_ut")
    if jd is None:
        # Try to derive from birth_utc
        birth_utc = metadata.get("birth_utc")
        if isinstance(birth_utc, str):
            try:
                dt = datetime.fromisoformat(birth_utc.replace("Z", "+00:00"))
                jd = swe.julday(dt.year, dt.month, dt.day,
                                dt.hour + dt.minute / 60.0 + dt.second / 3600.0)
            except Exception:
                return None
    if jd is None:
        return None

    try:
        result, _ = swe.calc_ut(jd, body_const, swe.FLG_SWIEPH)
        trop = float(result[0])
        sid = normalize_degrees(trop - SVP_DEGREES)
        sign_data = longitude_to_sign_degree(sid, tropical_longitude=trop)
        # House lookup if cusps are stored
        house = None
        cusps = astro.get("houses") or astro.get("house_cusps")
        if cusps:
            try:
                house = get_house_for_planet(sid, cusps)
            except Exception:
                pass
        return {
            **sign_data,
            "longitude":          sid,
            "tropical_longitude": trop,
            "speed":              float(result[3]) if len(result) > 3 else None,
            "house":              house,
            "body_type":          "computed_on_demand",
            "source":             "swisseph_FLG_SWIEPH",
        }
    except Exception as e:
        msg = str(e)
        # File-not-found vs other compute errors → distinguish for caller
        not_found = "not found" in msg.lower() or ".se1" in msg
        logger.warning(
            f"[NatalObjectEngine] swisseph calc for body_const={body_const} failed: {e}"
        )
        # Return a sentinel dict (not None) so the caller can distinguish
        # "ephemeris file missing" from "JD unavailable".
        return {"__compute_error__": True, "ephemeris_missing": not_found, "raw_error": msg}


def compute_natal_object(chart: Dict[str, Any], object_name: str) -> Dict[str, Any]:
    """Public API. Resolve a user-typed object name and return its natal
    placement envelope, or a clean not-wired refusal.

    Returns:
        { "success": bool,
          "object": canonical name or original input if unrecognised,
          "reason": short code (when success=False),
          "message": human readable answer or refusal,
          "placement": { sign, degree, formatted, house, ... } when success=True,
          "build_marker": ...
        }
    """
    canon = resolve_natal_object_name(object_name)
    if canon is None:
        return {
            "success": False,
            "object": object_name,
            "reason": "object_not_recognised",
            "build_marker": BUILD_MARKER,
            "message": f"I don't recognise the object '{object_name}'. "
                       f"Try a canonical name like Chiron, Lilith, Vertex, North Node.",
        }

    # Explicit not-wired list (Phase 5 protection)
    if canon in _NOT_WIRED:
        return {
            "success": False,
            "object": canon,
            "reason": "object_not_wired",
            "build_marker": BUILD_MARKER,
            "message": f"{canon} is not wired into the astrology engine yet.",
        }

    # 1) Stored in chart doc?
    stored = _read_stored_natal_object(chart, canon)
    if stored:
        return {
            "success": True,
            "object": canon,
            "source": "stored_chart_doc",
            "build_marker": BUILD_MARKER,
            "placement": stored,
        }

    # 2) Computed via formula (Lot of Fortune / Spirit, sect-aware)
    if canon in _FORMULA_OBJECTS:
        placement = _compute_lot(chart, canon)
        if placement:
            return {
                "success": True,
                "object": canon,
                "source": "formula",
                "build_marker": BUILD_MARKER,
                "placement": placement,
            }
        return {
            "success": False,
            "object": canon,
            "reason": "lot_formula_inputs_missing",
            "build_marker": BUILD_MARKER,
            "message": f"{canon} couldn't be computed — required "
                       f"natal Sun/Moon/ASC longitudes are not in the "
                       f"chart.",
        }

    # 3) Compute on demand via Swiss Ephemeris
    if canon in _COMPUTE_ON_DEMAND:
        placement = _compute_natal_lilith(chart, _COMPUTE_ON_DEMAND[canon])
        if placement and not placement.get("__compute_error__"):
            return {
                "success": True,
                "object": canon,
                "source": "swisseph_on_demand",
                "build_marker": BUILD_MARKER,
                "placement": placement,
            }
        # Distinguish ephemeris-missing from JD-missing
        if placement and placement.get("__compute_error__") and placement.get("ephemeris_missing"):
            return {
                "success": False,
                "object": canon,
                "reason": "ephemeris_file_missing",
                "build_marker": BUILD_MARKER,
                "message": f"{canon} is not wired into the astrology engine yet "
                           f"(its Swiss Ephemeris file isn't installed in this build).",
            }
        return {
            "success": False,
            "object": canon,
            "reason": "compute_failed",
            "build_marker": BUILD_MARKER,
            "message": f"{canon} couldn't be computed from the current chart data.",
        }

    # 3) Fall through — recognised name but no path
    return {
        "success": False,
        "object": canon,
        "reason": "no_path_to_compute",
        "build_marker": BUILD_MARKER,
        "message": f"{canon} is not wired into the astrology engine yet.",
    }


# ---------------------------------------------------------------------------
# Proof block for chat
# ---------------------------------------------------------------------------
def build_natal_object_proof_block(envelope: Dict[str, Any]) -> str:
    """Build a deterministic system-prompt block from a natal-object
    envelope. Appended to the lens prompt before the LLM is called.
    """
    if not envelope:
        return ""
    if not envelope.get("success"):
        obj = envelope.get("object", "this object")
        msg = envelope.get("message", f"{obj} is not wired into the astrology engine yet.")
        return (
            f"━━━━ NATAL OBJECT — ENGINE STATUS: {obj} ━━━━\n"
            f"available: NO\n"
            f"reason: {envelope.get('reason','unknown')}\n"
            f"engine_message: {msg}\n"
            "INSTRUCTION TO YOU:\n"
            "1. Respond with the engine_message VERBATIM or near-verbatim "
            "   as the first sentence.\n"
            "2. DO NOT substitute a different placement. Especially: if "
            "   the user asked about Lilith, DO NOT answer with the "
            f"   natal Moon. They are different bodies.\n"
            "3. You MAY offer one short follow-up of the shape:\n"
            "   'I can read your natal Moon if helpful, but that is not "
            "    the same as Lilith.'\n"
            "4. No textbook astrology, no coaching question, no "
            "   'this placement suggests…'.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    p = envelope["placement"]
    obj = envelope["object"]
    formatted = p.get("formatted") or f"{p.get('sign')} {p.get('degree')}"
    house = p.get("house")
    src = envelope.get("source", "?")

    house_line = f"House: {house}" if house is not None else "House: (not computed)"

    lines = [
        f"━━━━ NATAL OBJECT — ENGINE OUTPUT: {obj} ━━━━",
        f"placement: {formatted}",
        f"{house_line}",
        f"source: {src}",
        "sign attribution: True Sidereal-M Midpoint (same as natal chart)",
        "",
        "INSTRUCTION TO YOU:",
        "1. Sentence 1: state the placement directly. "
        "   Example: 'Your Lilith sits at 12° Sagittarius in the 8th house.'",
        "2. Then a 2–4 sentence master-astrologer reading. Behavioural, "
        "   not textbook. Speak to where this energy SHOWS UP in their life, "
        "   not what the sign 'represents'.",
        "3. Voice: direct, observant, slightly clinical. No 'this placement "
        "   suggests…', no 'themes of…', no 'where do you notice…?', no "
        "   'this can manifest as…', no closing reflective question.",
        "4. Length: 60–140 words.",
        "5. DO NOT mention any other body unless directly contextualising "
        "   the requested one.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)
