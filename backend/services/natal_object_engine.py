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

BUILD_MARKER = "astrology-chat-master-interpreter-v3"

# Canonical name → swisseph constant (for objects we COMPUTE on demand
# because they're not pre-stored in the chart doc).
_COMPUTE_ON_DEMAND = {
    "Black Moon Lilith":      swe.MEAN_APOG,   # Mean Lunar Apogee, the standard "BML"
    "True Black Moon Lilith": swe.OSCU_APOG,   # Osculating apogee, less common
}

# Aliases — the surface the user is likely to use → canonical name.
_ALIAS = {
    "lilith":              "Black Moon Lilith",
    "black moon":          "Black Moon Lilith",
    "black moon lilith":   "Black Moon Lilith",
    "bml":                 "Black Moon Lilith",
    "mean lilith":         "Black Moon Lilith",
    "true lilith":         "True Black Moon Lilith",
    "true black moon":     "True Black Moon Lilith",
    # Stored-in-chart aliases — accepted but go through chart-read path:
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
    "part of fortune":     "Part of Fortune",
    "pars fortuna":        "Part of Fortune",
    "fortuna":             "Part of Fortune",
    "juno":                "Juno",
    "ceres":               "Ceres",
    "pallas":              "Pallas",
    "vesta":               "Vesta",
    "eris":                "Eris",
}

# Objects that we ACKNOWLEDGE but explicitly DO NOT support yet.
# Any query for these returns the verbatim not-wired message.
_NOT_WIRED = {
    "Ceres", "Pallas", "Vesta", "Eris", "Part of Fortune",
}


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
    for canon in list(_COMPUTE_ON_DEMAND.keys()) + ["Chiron", "North Node",
                                                     "South Node", "Vertex",
                                                     "Anti-Vertex", "Juno"]:
        if cap.lower() == canon.lower():
            return canon
    return None


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
        logger.warning(f"[NatalObjectEngine] swisseph calc for body_const={body_const} failed: {e}")
        return None


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

    # 2) Compute on demand (Lilith family)
    if canon in _COMPUTE_ON_DEMAND:
        placement = _compute_natal_lilith(chart, _COMPUTE_ON_DEMAND[canon])
        if placement:
            return {
                "success": True,
                "object": canon,
                "source": "swisseph_on_demand",
                "build_marker": BUILD_MARKER,
                "placement": placement,
            }
        return {
            "success": False,
            "object": canon,
            "reason": "compute_failed_missing_birth_data",
            "build_marker": BUILD_MARKER,
            "message": f"{canon} couldn't be computed — the chart's "
                       f"birth Julian day isn't accessible.",
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
