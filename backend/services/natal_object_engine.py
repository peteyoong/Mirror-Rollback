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

BUILD_MARKER = "astrology-chat-v5-advanced-object-reconnect"

# Canonical name → swisseph body constant (for objects we COMPUTE on demand
# because they're not pre-stored in the chart doc).
#
# Two flavours:
#   • Direct first-class swisseph bodies (have a top-level constant) — these
#     read from the standard seas_18.se1 asteroid file that ships with the
#     pyswisseph wheel.  Juno / Vesta / Ceres / Pallas / Pholus belong here.
#     Previously this engine routed them via AST_OFFSET + minor-planet-number,
#     which was correct for asteroids but missed Juno entirely because the
#     numbering offset and Juno's swisseph constant are different layers.
#   • Named asteroids that require additional .se1 ephemeris files (Eros,
#     Psyche, Hygiea, Astraea, Eris).  Those calls will fail with a
#     "file not found" error and the engine reports them as
#     `ephemeris_file_missing` (a distinct reason from "not designed").
_AST_OFFSET = getattr(swe, "AST_OFFSET", 10000)
_COMPUTE_ON_DEMAND = {
    # Lunar apogee family
    "Black Moon Lilith":      swe.MEAN_APOG,   # Mean Lunar Apogee — standard BML
    "True Black Moon Lilith": swe.OSCU_APOG,   # Osculating apogee, less common
    # Major asteroids — use direct swisseph constants (always in seas_18.se1)
    "Ceres":                  swe.CERES,
    "Pallas":                 swe.PALLAS,
    "Juno":                   swe.JUNO,
    "Vesta":                  swe.VESTA,
    # Centaur — also in standard ephemeris
    "Pholus":                 swe.PHOLUS,
    # Named asteroids — require additional ephemeris files NOT bundled by default.
    # These return `ephemeris_file_missing` until the .se1 files are installed.
    "Astraea":                _AST_OFFSET + 5,
    "Hygiea":                 _AST_OFFSET + 10,
    "Psyche":                 _AST_OFFSET + 16,
    "Eros":                   _AST_OFFSET + 433,
    "Eris":                   _AST_OFFSET + 136199,
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
    "pholus":              "Pholus",
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
        + ["Chiron", "North Node", "South Node", "Vertex", "Anti-Vertex",
           "Pholus"]
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
    sun_t = _trop(sun)
    moon_t = _trop(moon)
    asc_t = _trop(asc)
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
    cusps = _extract_cusps_list(astro)
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
            cusps = _extract_cusps_list(astro)
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


def _extract_cusps_list(astro: Dict[str, Any]) -> Optional[list]:
    """Extract the 12-element house-cusp list from a stored chart, regardless
    of shape. The current canonical shape is `astro.houses.cusps` (list of
    longitudes) but older builds wrote `astro.house_cusps` directly.
    """
    cusps = astro.get("house_cusps")
    if isinstance(cusps, list) and len(cusps) >= 12:
        return cusps
    houses = astro.get("houses")
    if isinstance(houses, dict):
        inner = houses.get("cusps")
        if isinstance(inner, list) and len(inner) >= 12:
            return inner
    if isinstance(houses, list) and len(houses) >= 12:
        # Already a flat list of cusps
        if all(isinstance(x, (int, float)) for x in houses):
            return houses
        # List of dicts with "cusp" / "longitude"
        try:
            return [h.get("cusp") or h.get("longitude") for h in houses]
        except Exception:
            return None
    return None


def _compute_natal_vertex(chart: Dict[str, Any], anti: bool = False) -> Optional[Dict[str, Any]]:
    """Compute the natal Vertex (or Anti-Vertex) on demand for charts that
    don't have it pre-stored in `astrology.angles.vertex`.

    The Vertex is the 4th element returned by `swe.houses_ex(...)`'s ASC/MC
    array. We use Placidus + sidereal flag to match the same intent as the
    main chart builder (relationship-field amplifier layer in
    `calculations/astrology.py`).

    Requires the chart to expose:
        astrology.metadata.julian_day   (or .jd_ut)
        astrology.metadata.coordinates.{lat,lon}   (or a sibling field)
    Returns None when those inputs are missing.
    """
    astro = (chart or {}).get("astrology") or {}
    metadata = astro.get("metadata") or {}
    jd = metadata.get("julian_day") or metadata.get("jd_ut")
    coords = metadata.get("coordinates") or {}
    lat = coords.get("lat") if coords else None
    lon = coords.get("lon") if coords else None
    if lat is None:
        lat = metadata.get("birth_lat") or metadata.get("latitude")
    if lon is None:
        lon = metadata.get("birth_lon") or metadata.get("longitude")
    if jd is None or lat is None or lon is None:
        return None
    try:
        _h_cusps, ascmc_sid = swe.houses_ex(float(jd), float(lat), float(lon),
                                            b'P', swe.FLG_SIDEREAL)
        if ascmc_sid is None or len(ascmc_sid) <= 3:
            return None
        vx_sid = normalize_degrees(float(ascmc_sid[3]))
        # Anti-vertex = vertex opposition
        if anti:
            vx_sid = normalize_degrees(vx_sid + 180.0)
        # Tropical fallback for the formatted payload
        try:
            _, ascmc_trop = swe.houses(float(jd), float(lat), float(lon), b'P')
            vx_trop = normalize_degrees(float(ascmc_trop[3]) + (180.0 if anti else 0.0)) \
                if ascmc_trop and len(ascmc_trop) > 3 else None
        except Exception:
            vx_trop = None
        sign_data = longitude_to_sign_degree(vx_sid, tropical_longitude=vx_trop)
        # House lookup if cusps are stored
        house = None
        cusps = _extract_cusps_list(astro)
        if cusps:
            try:
                house = get_house_for_planet(vx_sid, cusps)
            except Exception:
                pass
        return {
            **sign_data,
            "longitude":          vx_sid,
            "tropical_longitude": vx_trop,
            "house":              house,
            "body_type":          "angle",
            "source":             "swisseph_houses_ex_FLG_SIDEREAL",
            "amplifier":          True,
        }
    except Exception as e:
        logger.warning(f"[NatalObjectEngine] vertex compute failed: {e}")
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
        cusps = _extract_cusps_list(astro)
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

    # 4) Vertex / Anti-Vertex compute-on-demand fallback.
    # astrology-chat-v5-advanced-object-reconnect — many existing charts
    # were built before the relationship-field amplifier layer that began
    # storing `angles.vertex` / `angles.anti_vertex`. For those charts the
    # stored read in step (1) returns None, but we can still compute the
    # axis directly from the stored birth metadata (jd + lat/lon).
    if canon in ("Vertex", "Anti-Vertex"):
        placement = _compute_natal_vertex(chart, anti=(canon == "Anti-Vertex"))
        if placement:
            return {
                "success": True,
                "object": canon,
                "source": "swisseph_houses_ex_on_demand",
                "build_marker": BUILD_MARKER,
                "placement": placement,
            }
        return {
            "success": False,
            "object": canon,
            "reason": "vertex_inputs_missing",
            "build_marker": BUILD_MARKER,
            "message": f"{canon} couldn't be computed — birth coordinates "
                       f"or Julian Day are missing from this chart.",
        }

    # 5) Fall through — recognised name but no path
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

    For objects that have a dedicated Mirror interpretation block
    (Vertex, Anti-Vertex, Juno, Chiron, Lilith, Part of Fortune,
    Part of Spirit, Pholus), this delegates to the Phase-2 interpreter
    so the chat answer feels Mirror-native rather than generic.
    """
    if not envelope:
        return ""
    # Phase-2 Mirror interpretation routing
    try:
        if envelope.get("success"):
            from services.mirror_object_interpreter import (
                has_mirror_interpretation,
                build_mirror_object_proof_block,
            )
            if has_mirror_interpretation(envelope.get("object") or ""):
                mirror_block = build_mirror_object_proof_block(envelope)
                if mirror_block:
                    return mirror_block
    except Exception as e:  # pragma: no cover — defensive
        logger.warning(f"[NatalObjectEngine] mirror interpretation skipped: {e}")
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
    # Display-cap degree at 29 for user-visible rendering (Variant-A signs
    # can be > 30° wide; raw `degree` stays untouched in the envelope).
    try:
        from services.mirror_object_interpreter import _format_placement_display
        formatted = _format_placement_display(p)
    except Exception:
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



# ---------------------------------------------------------------------------
# Lazy hydration for surfaces that read directly from the stored chart shape.
# ---------------------------------------------------------------------------
# astrology-chat-v5-advanced-object-reconnect
#
# Engines such as `relationship_field.py`, `astrology_relationship_restory_v1.py`,
# `pressure_topology_engine.py`, and `house_inventory_engine.py` read advanced
# objects directly from `chart.astrology.planets.Juno` and
# `chart.astrology.angles.vertex` / `.anti_vertex`. Charts built BEFORE the
# relationship-field amplifier layer landed do not carry these fields, so
# those surfaces silently dropped them.
#
# `ensure_advanced_objects` returns a *new* chart copy with Juno / Vertex /
# Anti-Vertex populated when they can be computed from stored birth
# metadata. Side-effect free; safe to call on any chart shape; falls
# through transparently when inputs are missing.
def ensure_advanced_objects(chart: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return a chart copy with Juno, Vertex, and Anti-Vertex hydrated when
    the stored chart doesn't carry them.

    Use this from any surface (relationship_field, restory, pressure_topology,
    house_inventory, etc.) that reads `astrology.planets.Juno` or
    `astrology.angles.vertex` directly. The hydration is best-effort: if the
    inputs aren't available, the chart is returned unmodified.
    """
    if not chart or not isinstance(chart, dict):
        return chart
    astro = chart.get("astrology")
    if not isinstance(astro, dict):
        return chart

    planets = astro.get("planets") or {}
    angles = astro.get("angles") or {}

    needs_juno = "Juno" not in planets and "juno" not in planets
    vx = angles.get("vertex") or {}
    needs_vertex = not (isinstance(vx, dict) and vx.get("sign"))
    avx = angles.get("anti_vertex") or {}
    needs_anti_vertex = not (isinstance(avx, dict) and avx.get("sign"))

    if not (needs_juno or needs_vertex or needs_anti_vertex):
        return chart  # already hydrated; nothing to do

    # Shallow-copy the chart and the astrology block so we don't mutate the
    # caller's dict. Planets and angles get fresh dicts only when written to.
    new_chart = dict(chart)
    new_astro = dict(astro)
    new_chart["astrology"] = new_astro

    if needs_juno:
        try:
            env = compute_natal_object(chart, "Juno")
            if env.get("success"):
                new_planets = dict(planets)
                new_planets["Juno"] = {**env["placement"], "amplifier": True}
                new_astro["planets"] = new_planets
        except Exception as e:
            logger.debug(f"[ensure_advanced_objects] Juno hydration skipped: {e}")

    if needs_vertex or needs_anti_vertex:
        new_angles_written = False
        new_angles = dict(angles)
        if needs_vertex:
            try:
                env = compute_natal_object(chart, "Vertex")
                if env.get("success"):
                    new_angles["vertex"] = {**env["placement"], "amplifier": True}
                    new_angles_written = True
            except Exception as e:
                logger.debug(f"[ensure_advanced_objects] Vertex hydration skipped: {e}")
        if needs_anti_vertex:
            try:
                env = compute_natal_object(chart, "Anti-Vertex")
                if env.get("success"):
                    new_angles["anti_vertex"] = {**env["placement"], "amplifier": True}
                    new_angles_written = True
            except Exception as e:
                logger.debug(f"[ensure_advanced_objects] Anti-Vertex hydration skipped: {e}")
        if new_angles_written:
            new_astro["angles"] = new_angles

    # ────────────────────────────────────────────────────────────────────
    # advanced-object-hydration-v2 (relationship-corroboration extension)
    # ────────────────────────────────────────────────────────────────────
    # Lazily hydrate Lilith / Lot of Fortune / Lot of Spirit so that
    # downstream relationship surfaces can read them via the same
    # `astrology.planets[...]` lookup path used for Sun/Moon/Mercury.
    #
    # Pattern is identical to Juno/Vertex hydration above:
    #   • Side-effect free (works on a shallow chart copy)
    #   • Best-effort (failures logged at debug, never raised)
    #   • Idempotent (skipped if already present)
    #   • Tagged with `amplifier: True` so consumers know these were
    #     hydrated rather than stored at chart creation time
    # ────────────────────────────────────────────────────────────────────
    planets_for_v2 = (new_astro.get("planets") or astro.get("planets") or {})
    needs_lilith = (
        "Black Moon Lilith" not in planets_for_v2
        and "True Black Moon Lilith" not in planets_for_v2
    )
    needs_fortune = "Lot of Fortune" not in planets_for_v2
    needs_spirit  = "Lot of Spirit"  not in planets_for_v2

    if needs_lilith or needs_fortune or needs_spirit:
        _v2_writes: Dict[str, Dict[str, Any]] = {}
        if needs_lilith:
            try:
                env = compute_natal_object(chart, "Black Moon Lilith")
                if env.get("success"):
                    _v2_writes["Black Moon Lilith"] = {
                        **env["placement"], "amplifier": True,
                    }
            except Exception as e:
                logger.debug(
                    f"[ensure_advanced_objects] Lilith hydration skipped: {e}"
                )
        if needs_fortune:
            try:
                env = compute_natal_object(chart, "Lot of Fortune")
                if env.get("success"):
                    _v2_writes["Lot of Fortune"] = {
                        **env["placement"], "amplifier": True,
                    }
            except Exception as e:
                logger.debug(
                    f"[ensure_advanced_objects] Fortune hydration skipped: {e}"
                )
        if needs_spirit:
            try:
                env = compute_natal_object(chart, "Lot of Spirit")
                if env.get("success"):
                    _v2_writes["Lot of Spirit"] = {
                        **env["placement"], "amplifier": True,
                    }
            except Exception as e:
                logger.debug(
                    f"[ensure_advanced_objects] Spirit hydration skipped: {e}"
                )
        if _v2_writes:
            merged = dict(new_astro.get("planets") or planets_for_v2)
            for k, v in _v2_writes.items():
                merged[k] = v
            new_astro["planets"] = merged

    return new_chart
