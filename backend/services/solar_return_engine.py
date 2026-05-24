"""
Solar Return Engine
===================

Build marker: astrology-chat-grounding-v2

Computes the exact moment in the current solar year when transit Sun
returns to the natal Sun longitude (tropical) — that's the "solar
return". Then calculates a chart for that instant at the user's natal
location.

Conventions
-----------
- Tropical Sun longitude is the anchor (standard for solar returns even
  in sidereal traditions, because the Sun's tropical longitude is what
  "returns" on the same calendar window each year).
- Sign attribution on the resulting chart still uses the system default
  (True Sidereal-M Midpoint) so the user sees signs in the same frame
  as their natal chart.
- Location defaults to the natal birth location. (Relocated solar
  returns are a future enhancement.)
- The "current" solar return is the one PRECEDING today's date (i.e.
  the active year). If the user has just had their birthday, that
  return governs the next 12 months until the following birthday.

This module is deterministic — no LLM calls.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone as _tz
from typing import Any, Dict, Optional

import swisseph as swe

from calculations.astrology import (
    calculate_ascendant_tropical,
    calculate_mc_tropical,
    calculate_planet_position_sidereal,
    calculate_equal_houses,
    get_house_for_planet,
    longitude_to_sign_degree,
    normalize_degrees,
    PLANETS as _PLANET_MAP,
)

logger = logging.getLogger(__name__)

BUILD_MARKER = "astrology-chat-grounding-v2"

# Tolerance for sun-return root-finding (in days). 1e-5 days ≈ ~0.86 s.
_RETURN_TOL_DAYS = 1.0 / 86400.0  # 1 second


# ---------------------------------------------------------------------------
# 1.  Sun longitude (tropical) at a given Julian day
# ---------------------------------------------------------------------------
def _tropical_sun_longitude(jd: float) -> float:
    """Tropical ecliptic longitude of the Sun at jd (UT)."""
    result, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    return float(result[0])


def _angular_distance(a: float, b: float) -> float:
    """Signed shortest angular distance from a to b on the 0–360 circle,
    in the range (-180, +180]. Used for Brent-style bisection.
    """
    d = (b - a + 180.0) % 360.0 - 180.0
    return d


# ---------------------------------------------------------------------------
# 2.  Find Julian day when tropical Sun longitude == target longitude
# ---------------------------------------------------------------------------
def find_solar_return_jd(
    natal_sun_tropical: float,
    search_start_jd: float,
    search_end_jd: float,
) -> Optional[float]:
    """Locate JD in [search_start_jd, search_end_jd] where transit Sun's
    tropical longitude == natal_sun_tropical (within ~1 second).

    Uses bisection on the signed angular distance. The Sun moves
    monotonically forward in tropical longitude (≈ +0.985°/day) so the
    sign of `_angular_distance(transit_sun, natal_sun)` changes from
    negative to positive exactly once across the year.

    Returns None if the root isn't bracketed in the window (caller
    should expand the window).
    """
    lo, hi = search_start_jd, search_end_jd
    f_lo = _angular_distance(_tropical_sun_longitude(lo), natal_sun_tropical)
    f_hi = _angular_distance(_tropical_sun_longitude(hi), natal_sun_tropical)

    # We want the unique crossing where f goes from negative to positive
    # (transit sun is "behind" natal, then catches up and passes).
    if f_lo * f_hi > 0:
        return None

    # Bisection
    for _ in range(80):  # 2^80 precision is overkill; 50 is plenty
        mid = 0.5 * (lo + hi)
        f_mid = _angular_distance(_tropical_sun_longitude(mid), natal_sun_tropical)
        if abs(hi - lo) < _RETURN_TOL_DAYS:
            return mid
        if f_lo * f_mid <= 0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return 0.5 * (lo + hi)


def _jd_to_datetime_utc(jd: float) -> datetime:
    """Convert a Julian day (UT) back to a python UTC datetime."""
    y, m, d, h_frac = swe.revjul(jd)
    hours = int(h_frac)
    minutes_frac = (h_frac - hours) * 60.0
    minutes = int(minutes_frac)
    seconds_frac = (minutes_frac - minutes) * 60.0
    seconds = int(round(seconds_frac))
    # Handle 60-second rollover
    if seconds >= 60:
        seconds = 0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        hours += 1
    return datetime(int(y), int(m), int(d), hours, minutes, seconds, tzinfo=_tz.utc)


# ---------------------------------------------------------------------------
# 3.  Public API
# ---------------------------------------------------------------------------
def compute_solar_return(
    chart: Dict[str, Any],
    user: Dict[str, Any],
    target_year: Optional[int] = None,
    reference_datetime_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Compute the active solar return for this user.

    Args:
        chart: The user's natal chart document (db.charts row). Must contain
               `astrology.planets.Sun.tropical_longitude` (or .longitude as
               sidereal fallback) and `astrology.metadata` with `birth_utc`
               and the natal location coords.
        user:  The user document. Used to read birth_location for the
               return location (defaults to natal location).
        target_year: Optional explicit civil year to compute the return
               for. If omitted, picks the most recent return preceding
               `reference_datetime_utc` (default: now).
        reference_datetime_utc: For determinism in tests. Default: now.

    Returns a structured envelope:
        {
          "success": True/False,
          "reason": short code,
          "build_marker": "astrology-chat-grounding-v2",
          "natal_sun_tropical": float,
          "return_datetime_utc": ISO string,
          "return_jd_ut": float,
          "location": {"latitude": ..., "longitude": ..., "label": ...},
          "asc":      {"sign": ..., "degree": ..., "formatted": ...,
                       "tropical_longitude": ..., "sidereal_longitude": ...},
          "mc":       { ...same shape... },
          "planets":  { "Sun": {sign, degree, formatted, house, ...},
                        "Moon": {...}, ... },
          "houses":   [12 sidereal cusps],
          "message":  human readable one-liner ready for prompt insertion,
        }
    """
    astro = (chart or {}).get("astrology") or {}
    sun_data = (astro.get("planets") or {}).get("Sun") or {}
    natal_sun_tropical = (
        sun_data.get("tropical_longitude")
        or sun_data.get("trop_longitude")
    )
    if natal_sun_tropical is None:
        # Sidereal fallback: reconstruct tropical from sidereal + SVP
        sun_sid = sun_data.get("longitude") or sun_data.get("sidereal_longitude")
        svp = (astro.get("metadata") or {}).get("svp_degrees") or astro.get("svp")
        if sun_sid is not None and svp is not None:
            natal_sun_tropical = normalize_degrees(float(sun_sid) + float(svp))
    if natal_sun_tropical is None:
        return {
            "success": False,
            "reason": "natal_sun_longitude_missing",
            "build_marker": BUILD_MARKER,
            "message": "I can't pull a solar return — the natal Sun "
                       "longitude isn't in your chart yet.",
        }
    natal_sun_tropical = normalize_degrees(float(natal_sun_tropical))

    # Birth metadata for default return location
    birth_loc = (user or {}).get("birth_location") or {}
    nat_lat = float(birth_loc.get("latitude") or 0.0)
    nat_lon = float(birth_loc.get("longitude") or 0.0)
    loc_label = birth_loc.get("city") or "natal location"

    # Pick target year
    if reference_datetime_utc is None:
        reference_datetime_utc = datetime.now(_tz.utc)
    if target_year is None:
        # Find the most recent return whose JD <= now. Natal birthday gives
        # us the anchor; the active return is the one in the current civil
        # year if it has already happened, else the previous one.
        # Use the natal birth date's month/day as the seed.
        birth_dt = (astro.get("metadata") or {}).get("birth_utc") or user.get("birth_date")
        if isinstance(birth_dt, str):
            try:
                birth_dt = datetime.fromisoformat(birth_dt.replace("Z", "+00:00"))
            except Exception:
                birth_dt = None
        if isinstance(birth_dt, datetime):
            seed_month = birth_dt.month
            seed_day = birth_dt.day
        else:
            seed_month, seed_day = 1, 1  # safe fallback
        ref_year = reference_datetime_utc.year
        candidate = datetime(ref_year, seed_month, min(seed_day, 28), tzinfo=_tz.utc)
        if candidate > reference_datetime_utc:
            ref_year -= 1
        target_year = ref_year

    # Build a search window of ±3 days around the natal birthday in target_year.
    birth_dt_meta = (astro.get("metadata") or {}).get("birth_utc") or user.get("birth_date")
    if isinstance(birth_dt_meta, str):
        try:
            birth_dt_meta = datetime.fromisoformat(birth_dt_meta.replace("Z", "+00:00"))
        except Exception:
            birth_dt_meta = None
    if isinstance(birth_dt_meta, datetime):
        seed = birth_dt_meta.replace(year=target_year, tzinfo=_tz.utc)
    else:
        seed = datetime(target_year, 7, 1, tzinfo=_tz.utc)

    search_start = seed - timedelta(days=3)
    search_end   = seed + timedelta(days=3)

    def _to_jd(dt: datetime) -> float:
        return swe.julday(dt.year, dt.month, dt.day,
                          dt.hour + dt.minute / 60.0 + dt.second / 3600.0)

    sr_jd = find_solar_return_jd(natal_sun_tropical, _to_jd(search_start), _to_jd(search_end))
    if sr_jd is None:
        # Try wider window — Sun travels ~360°/year, but at edges of
        # tropical-year cycle the crossing might fall outside ±3 days.
        search_start = seed - timedelta(days=10)
        search_end   = seed + timedelta(days=10)
        sr_jd = find_solar_return_jd(natal_sun_tropical, _to_jd(search_start), _to_jd(search_end))

    if sr_jd is None:
        return {
            "success": False,
            "reason": "return_jd_not_found",
            "build_marker": BUILD_MARKER,
            "message": "I couldn't locate the solar return crossing for "
                       f"{target_year}. The engine's search window didn't "
                       "bracket the root.",
        }

    sr_dt = _jd_to_datetime_utc(sr_jd)

    # Get SVP for sidereal conversions
    from calculations.sidereal_config import SVP_DEGREES as svp

    # Calculate angles at the solar return moment (natal location)
    asc_tropical = calculate_ascendant_tropical(sr_jd, nat_lat, nat_lon)
    mc_tropical  = calculate_mc_tropical(sr_jd, nat_lat, nat_lon)
    asc_sidereal = normalize_degrees(asc_tropical - svp)
    mc_sidereal  = normalize_degrees(mc_tropical - svp)
    asc_sign = longitude_to_sign_degree(asc_sidereal, tropical_longitude=asc_tropical)
    mc_sign  = longitude_to_sign_degree(mc_sidereal,  tropical_longitude=mc_tropical)

    # Equal houses from sidereal ASC
    house_cusps = calculate_equal_houses(asc_sidereal)

    # Planets at the SR moment (sidereal)
    planets_out: Dict[str, Dict[str, Any]] = {}
    for name in ("Sun", "Moon", "Mercury", "Venus", "Mars",
                 "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
        try:
            p = calculate_planet_position_sidereal(_PLANET_MAP[name], sr_jd, svp_degrees=svp)
            p["house"] = get_house_for_planet(p["longitude"], house_cusps)
            planets_out[name] = p
        except Exception as e:
            logger.warning(f"[SolarReturn] planet {name} failed: {e}")

    # Human-readable one-liner for prompt injection
    msg = (
        f"Solar return for {target_year}: {sr_dt.strftime('%Y-%m-%d %H:%M UTC')}. "
        f"SR Ascendant = {asc_sign['formatted']}. "
        f"SR Sun in House {planets_out.get('Sun', {}).get('house', '?')}. "
        f"SR Moon = {planets_out.get('Moon', {}).get('formatted', '?')}, "
        f"House {planets_out.get('Moon', {}).get('house', '?')}. "
        f"SR MC = {mc_sign['formatted']}. "
        f"Location: {loc_label} (lat={nat_lat:.3f}, lon={nat_lon:.3f})."
    )

    return {
        "success": True,
        "build_marker": BUILD_MARKER,
        "target_year": target_year,
        "natal_sun_tropical": natal_sun_tropical,
        "return_jd_ut": sr_jd,
        "return_datetime_utc": sr_dt.isoformat(),
        "location": {
            "latitude": nat_lat,
            "longitude": nat_lon,
            "label": loc_label,
            "note": "natal-location return (relocated returns not yet supported)",
        },
        "asc": {**asc_sign, "tropical_longitude": asc_tropical, "sidereal_longitude": asc_sidereal},
        "mc":  {**mc_sign,  "tropical_longitude": mc_tropical,  "sidereal_longitude": mc_sidereal},
        "houses": house_cusps,
        "planets": planets_out,
        "message": msg,
    }


# ---------------------------------------------------------------------------
# 4.  Proof block builder (analog to build_transit_object_proof_block)
# ---------------------------------------------------------------------------
def build_solar_return_proof_block(envelope: Dict[str, Any]) -> str:
    """Build a deterministic system-prompt block from a solar-return envelope.

    The block is appended to the lens system prompt right before the LLM is
    called. It contains the ONLY data the LLM may reference when answering
    a solar return question.
    """
    if not envelope or not envelope.get("success"):
        reason = (envelope or {}).get("reason", "unknown")
        msg = (envelope or {}).get("message") or "Solar return engine refused."
        return (
            "━━━━ SOLAR RETURN — ENGINE STATUS ━━━━\n"
            f"available: NO\n"
            f"reason: {reason}\n"
            f"engine_message: {msg}\n"
            "INSTRUCTION TO YOU: Respond using engine_message verbatim or "
            "very close to it. DO NOT explain solar return mechanics. "
            "DO NOT offer to substitute another reading. DO NOT ask "
            "reflective questions. Be direct and brief.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    asc = envelope["asc"]; mc = envelope["mc"]; planets = envelope.get("planets", {})
    sun = planets.get("Sun", {}); moon = planets.get("Moon", {})
    venus = planets.get("Venus", {}); mars = planets.get("Mars", {})
    jup = planets.get("Jupiter", {}); sat = planets.get("Saturn", {})

    lines = [
        "━━━━ SOLAR RETURN — ENGINE OUTPUT (USE THIS, NOTHING ELSE) ━━━━",
        f"target_year: {envelope['target_year']}",
        f"return_moment_utc: {envelope['return_datetime_utc']}",
        f"location: {envelope['location']['label']} "
        f"(lat={envelope['location']['latitude']:.3f}, lon={envelope['location']['longitude']:.3f}) "
        f"[{envelope['location']['note']}]",
        "",
        "ANGLES (sign attribution: True Sidereal-M Midpoint, same as natal):",
        f"  SR Ascendant : {asc.get('formatted')}   (sidereal {asc.get('sidereal_longitude'):.3f}°)",
        f"  SR Midheaven : {mc.get('formatted')}    (sidereal {mc.get('sidereal_longitude'):.3f}°)",
        "",
        "KEY SR PLANETS:",
        f"  SR Sun     : {sun.get('formatted', '?')}  House {sun.get('house', '?')}",
        f"  SR Moon    : {moon.get('formatted', '?')}  House {moon.get('house', '?')}",
        f"  SR Venus   : {venus.get('formatted', '?')}  House {venus.get('house', '?')}",
        f"  SR Mars    : {mars.get('formatted', '?')}  House {mars.get('house', '?')}",
        f"  SR Jupiter : {jup.get('formatted', '?')}  House {jup.get('house', '?')}",
        f"  SR Saturn  : {sat.get('formatted', '?')}  House {sat.get('house', '?')}",
        "",
        "INSTRUCTION TO YOU:",
        "1. State the SR Ascendant clearly in sentence 1.",
        "2. Give a 2–3 sentence read of what this SR Ascendant sign "
        "   tends to organise for the coming solar year (the rising "
        "   sign in a solar return sets the year's keynote / lens).",
        "3. Optionally one short observation linking SR Sun house to "
        "   the year's emphasis. Do NOT tour every planet.",
        "4. Voice: observant astrologer, NOT teacher. NO 'solar return "
        "   charts reveal themes…' explanations. NO 'depending on…'. "
        "   NO 'does this resonate?'.",
        "5. Length: 80–150 words MAX.",
        "6. DO NOT END WITH A QUESTION. NO 'Where does this theme of X "
        "   seem to be emerging in your life?'. NO 'How does that "
        "   land for you?'. NO 'Does any of this resonate?'. End on "
        "   the observation itself. Period. Hard rule.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)
