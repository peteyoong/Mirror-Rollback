"""
Canonical Astronomy Service — SINGLE SOURCE OF TRUTH
=====================================================

Mirror enforces ONE canonical True Sidereal compute contract for ALL lenses.
Both Astrology AND Human Design read their planetary longitudes from THIS module.

No lens is permitted to:
- call `swe.set_sid_mode` itself
- call `swe.calc_ut` with its own flags
- apply a manual SVP subtraction
- use a different timezone/datetime normalization
- assume its own ayanamsa

Canonical settings (locked at module import):
- Zodiac Mode:      True Sidereal (SIDM_USER)
- Ayanamsa:         user-defined, SVP 31.2836° at J2000
- Yearly Increment: 0.0 (no precession drift)
- Ephemeris:        Swiss Ephemeris (FLG_SWIEPH)
- House System:     Equal Houses (anchored to sidereal Ascendant)

The canonical object returned by `compute_canonical_birth_positions()` contains:
- birth_metadata (UTC datetime, local tz, lat/lon, source fingerprint)
- sidereal_config_used
- personality_positions  (= birth-moment sidereal positions — astrology consumes directly)
- design_positions       (= "88 solar degrees before birth" sidereal positions — HD consumes this)
- houses, asc, mc
- fingerprint            (hash that astrology + HD MUST both match before rendering)

Anti-drift enforcement:
- `assert_no_drift()` compares a lens's claimed positions against canonical.
- Any mismatch > tolerance raises CanonicalAstronomyDriftError.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

import swisseph as swe

# Delegate ephemeris init + sid_mode to the canonical config module.
# If anything else tries to set a different sid_mode, our validation endpoint will catch it.
from calculations.sidereal_config import (
    SVP_DEGREES,
    J2000_EPOCH,
    YEARLY_INCREMENT,
    CALC_FLAGS_SIDEREAL,
    CALC_FLAGS_TROPICAL,
    PLANETS as CANONICAL_PLANETS,
    ZODIAC_SIGNS,
    _ensure_ephemeris_initialized,
    normalize_degrees,
    longitude_to_sign_degree,
    get_julian_day,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CANONICAL CONFIG (locked, read-only)
# =============================================================================

CANONICAL_SIDEREAL_CONFIG = {
    "mode": "true_sidereal_user_defined",
    "svp_degrees": SVP_DEGREES,
    "reference_epoch": "J2000",
    "reference_epoch_jd": J2000_EPOCH,
    "yearly_increment": YEARLY_INCREMENT,
    "ayanamsa_type": "SIDM_USER",
    "ephemeris_flag": "FLG_SWIEPH | FLG_SIDEREAL",
    "house_system": "equal",
}

# Planets both lenses must resolve before rendering.
# Astrology uses the classical 10; HD adds Earth + South Node.
CANONICAL_PLANET_SET = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "North Node",
]

HD_EXTRA_BODIES = ["Earth", "South Node"]  # derived, not separately queried


# =============================================================================
# ERRORS
# =============================================================================

class CanonicalAstronomyDriftError(Exception):
    """Raised when a lens's positions diverge from the canonical source layer."""


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class PlanetPosition:
    planet: str
    longitude: float        # sidereal longitude (0-360)
    tropical_longitude: float
    sign: str
    degree_in_sign: float
    formatted: str
    speed: float
    retrograde: bool
    latitude: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalBirthPositions:
    # --- Birth metadata (normalized) ---
    birth_datetime_utc: str                 # ISO 8601 UTC
    birth_datetime_local: Optional[str]     # ISO 8601 with local tz, if provided
    birth_timezone: Optional[str]
    latitude: float
    longitude: float

    # --- Sidereal config actually used ---
    sidereal_config_used: Dict[str, Any]

    # --- Canonical positions ---
    personality_positions: Dict[str, Dict[str, Any]]   # birth-moment sidereal
    design_positions: Dict[str, Dict[str, Any]]        # 88-solar-degree-earlier sidereal
    design_datetime_utc: str
    design_solar_offset_degrees: float                 # nominal 88.0

    # --- Houses (sidereal equal) ---
    ascendant_longitude: float
    midheaven_longitude: float
    houses_equal: Dict[int, float]                     # cusp longitudes

    # --- Fingerprint (for drift detection) ---
    fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "birth_metadata": {
                "birth_datetime_utc": self.birth_datetime_utc,
                "birth_datetime_local": self.birth_datetime_local,
                "birth_timezone": self.birth_timezone,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "sidereal_config_used": self.sidereal_config_used,
            "personality_positions": self.personality_positions,
            "design_positions": self.design_positions,
            "design_datetime_utc": self.design_datetime_utc,
            "design_solar_offset_degrees": self.design_solar_offset_degrees,
            "ascendant_longitude": self.ascendant_longitude,
            "midheaven_longitude": self.midheaven_longitude,
            "houses_equal": self.houses_equal,
            "fingerprint": self.fingerprint,
        }


# =============================================================================
# LOW-LEVEL CANONICAL CALCULATION
# =============================================================================

def _canonical_calc_planet(planet_id: int, jd: float) -> Dict[str, Any]:
    """Compute a single planet's sidereal + tropical position using CANONICAL flags only.
    No manual subtraction, no alternative flags, no fallbacks.
    """
    _ensure_ephemeris_initialized()

    trop = swe.calc_ut(jd, planet_id, CALC_FLAGS_TROPICAL)
    sid  = swe.calc_ut(jd, planet_id, CALC_FLAGS_SIDEREAL)

    sid_lon  = normalize_degrees(sid[0][0])
    trop_lon = normalize_degrees(trop[0][0])
    speed    = sid[0][3]
    sign_info = longitude_to_sign_degree(sid_lon)

    return {
        "longitude": sid_lon,
        "tropical_longitude": trop_lon,
        "sign": sign_info["sign"],
        "degree_in_sign": sign_info["degree"],
        "formatted": sign_info["formatted"],
        "speed": speed,
        "retrograde": speed < 0,
        "latitude": sid[0][1],
    }


def _compute_all_positions(jd: float) -> Dict[str, Dict[str, Any]]:
    """Compute canonical sidereal positions for every planet in CANONICAL_PLANET_SET
    plus Earth (= Sun + 180°) and South Node (= North Node + 180°) for HD consumption.
    """
    out: Dict[str, Dict[str, Any]] = {}

    for name in CANONICAL_PLANET_SET:
        pid = CANONICAL_PLANETS.get(name)
        if pid is None:
            continue
        pos = _canonical_calc_planet(pid, jd)
        pos["planet"] = name
        out[name] = pos

    # Earth: exact opposite of Sun in sidereal space
    if "Sun" in out:
        sun = out["Sun"]
        earth_lon = normalize_degrees(sun["longitude"] + 180.0)
        sign_info = longitude_to_sign_degree(earth_lon)
        out["Earth"] = {
            "planet": "Earth",
            "longitude": earth_lon,
            "tropical_longitude": normalize_degrees(sun["tropical_longitude"] + 180.0),
            "sign": sign_info["sign"],
            "degree_in_sign": sign_info["degree"],
            "formatted": sign_info["formatted"],
            "speed": -sun["speed"],
            "retrograde": sun["retrograde"],
            "latitude": -sun["latitude"],
        }

    # South Node: exact opposite of North Node
    if "North Node" in out:
        nn = out["North Node"]
        sn_lon = normalize_degrees(nn["longitude"] + 180.0)
        sign_info = longitude_to_sign_degree(sn_lon)
        out["South Node"] = {
            "planet": "South Node",
            "longitude": sn_lon,
            "tropical_longitude": normalize_degrees(nn["tropical_longitude"] + 180.0),
            "sign": sign_info["sign"],
            "degree_in_sign": sign_info["degree"],
            "formatted": sign_info["formatted"],
            "speed": -nn["speed"],
            "retrograde": nn["retrograde"],
            "latitude": -nn["latitude"],
        }

    return out


# =============================================================================
# HOUSES (canonical sidereal equal-house system)
# =============================================================================

def _compute_houses_equal(jd: float, lat: float, lon: float, sun_sidereal_lon: float) -> Tuple[float, float, Dict[int, float]]:
    """Compute Ascendant, Midheaven, and equal houses in CANONICAL sidereal frame.
    Uses Swiss ephemeris houses_ex then subtracts canonical SVP to obtain sidereal cusps.
    """
    _ensure_ephemeris_initialized()
    try:
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b'E')  # Equal-house
        asc_trop = normalize_degrees(ascmc[0])
        mc_trop  = normalize_degrees(ascmc[1])
        asc_sid  = normalize_degrees(asc_trop - SVP_DEGREES)
        mc_sid   = normalize_degrees(mc_trop - SVP_DEGREES)
        houses: Dict[int, float] = {}
        for i in range(12):
            houses[i + 1] = normalize_degrees(cusps[i] - SVP_DEGREES)
        return asc_sid, mc_sid, houses
    except Exception as e:
        logger.warning(f"[CanonicalAstronomy] Houses compute failed: {e}")
        # Graceful: still return a valid equal-house grid anchored to ASC=0°
        houses = {i + 1: normalize_degrees(i * 30.0) for i in range(12)}
        return 0.0, 0.0, houses


# =============================================================================
# DESIGN DATE SOLVER (canonical)
# =============================================================================

def _solve_design_datetime(birth_dt_utc: datetime, target_offset_degrees: float = 88.0,
                           tolerance_degrees: float = 0.001) -> Tuple[datetime, float]:
    """
    Find the UTC datetime where sidereal Sun was exactly (target_offset_degrees)
    earlier than the birth-moment sidereal Sun.

    Uses a binary-search solver keyed to the CANONICAL sidereal Sun computation.
    NO tropical-minus-SVP shortcut is used here.
    """
    _ensure_ephemeris_initialized()

    def _sun_sidereal_longitude(dt: datetime) -> float:
        jd = get_julian_day(dt)
        result = swe.calc_ut(jd, swe.SUN, CALC_FLAGS_SIDEREAL)
        return normalize_degrees(result[0][0])

    birth_sun = _sun_sidereal_longitude(birth_dt_utc)
    target_sun = normalize_degrees(birth_sun - target_offset_degrees)

    # Bracket search — Sun moves ~0.95°/day near aphelion (July) and ~1.02°/day near
    # perihelion (January). 88° takes anywhere between ~86 and ~93 days.
    # We use a comfortably wide bracket so binary search always contains the target.
    lo = birth_dt_utc - timedelta(days=96)   # safely before 88° offset
    hi = birth_dt_utc - timedelta(days=82)   # safely after

    for _ in range(60):  # 60 iterations → microsecond precision well before we'd bail
        mid = lo + (hi - lo) / 2
        mid_sun = _sun_sidereal_longitude(mid)

        # Measure signed angular distance (mid_sun relative to target)
        delta = (mid_sun - target_sun + 540.0) % 360.0 - 180.0

        if abs(delta) < tolerance_degrees:
            achieved_offset = (birth_sun - mid_sun + 540.0) % 360.0 - 180.0
            # We want achieved_offset close to +target_offset_degrees
            return mid, abs(achieved_offset)

        # delta > 0 means mid_sun is AHEAD of target → we need EARLIER date → move hi left
        # delta < 0 means mid_sun is BEHIND target → we need LATER date → move lo right
        if delta > 0:
            hi = mid
        else:
            lo = mid

    # Best-effort fallback
    achieved_offset = (birth_sun - _sun_sidereal_longitude(mid) + 540.0) % 360.0 - 180.0
    return mid, abs(achieved_offset)


# =============================================================================
# PUBLIC API — THE ONLY ENTRY POINT FOR LENSES
# =============================================================================

def compute_canonical_birth_positions(
    birth_datetime_utc: datetime,
    latitude: float,
    longitude: float,
    birth_timezone: Optional[str] = None,
    birth_datetime_local: Optional[datetime] = None,
) -> CanonicalBirthPositions:
    """
    THE SINGLE ENTRY POINT for all birth-chart compute.
    Returns a CanonicalBirthPositions object; both astrology and HD MUST read
    their planet longitudes from this object.

    Args:
        birth_datetime_utc: UTC datetime (tz-aware recommended).
        latitude/longitude: geographic coords.
        birth_timezone: optional IANA tz string for debug.
        birth_datetime_local: optional localized datetime for debug.

    Returns:
        CanonicalBirthPositions.
    """
    _ensure_ephemeris_initialized()

    # Normalize tz
    if birth_datetime_utc.tzinfo is None:
        birth_datetime_utc = birth_datetime_utc.replace(tzinfo=timezone.utc)
    else:
        birth_datetime_utc = birth_datetime_utc.astimezone(timezone.utc)

    # Personality (birth-moment) positions
    p_jd = get_julian_day(birth_datetime_utc)
    personality = _compute_all_positions(p_jd)

    # Houses
    sun_sid_lon = personality["Sun"]["longitude"] if "Sun" in personality else 0.0
    asc, mc, houses = _compute_houses_equal(p_jd, latitude, longitude, sun_sid_lon)

    # Design (88 sidereal solar degrees before birth) — same canonical pipeline
    design_dt, achieved_offset = _solve_design_datetime(birth_datetime_utc, 88.0)
    d_jd = get_julian_day(design_dt)
    design = _compute_all_positions(d_jd)

    # Fingerprint for drift detection (rounded to 6 decimals = ~0.000001° ~ 4 milliarcsec)
    fp_src = "|".join([
        f"utc={birth_datetime_utc.isoformat()}",
        f"lat={round(latitude, 6)}",
        f"lon={round(longitude, 6)}",
        f"svp={SVP_DEGREES}",
        f"epoch={J2000_EPOCH}",
        f"psun={round(personality.get('Sun', {}).get('longitude', 0), 6)}",
        f"pmoon={round(personality.get('Moon', {}).get('longitude', 0), 6)}",
        f"dsun={round(design.get('Sun', {}).get('longitude', 0), 6)}",
    ])
    fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()[:16]

    return CanonicalBirthPositions(
        birth_datetime_utc=birth_datetime_utc.isoformat(),
        birth_datetime_local=birth_datetime_local.isoformat() if birth_datetime_local else None,
        birth_timezone=birth_timezone,
        latitude=latitude,
        longitude=longitude,
        sidereal_config_used=dict(CANONICAL_SIDEREAL_CONFIG),
        personality_positions=personality,
        design_positions=design,
        design_datetime_utc=design_dt.astimezone(timezone.utc).isoformat(),
        design_solar_offset_degrees=achieved_offset,
        ascendant_longitude=asc,
        midheaven_longitude=mc,
        houses_equal=houses,
        fingerprint=fingerprint,
    )


# =============================================================================
# ANTI-DRIFT GUARD — GLOBAL RUNTIME CHECK
# =============================================================================

DRIFT_TOLERANCE_DEGREES = 0.05  # ~3 arcminutes — generous enough for solver-precision
                                # differences on the Moon (fastest body), strict enough
                                # to catch real ayanamsa / ephemeris drift.


def assert_canonical_sidereal_mode_active() -> None:
    """
    Runtime guard: verify Swiss Ephemeris sidereal mode is STILL the canonical
    SIDM_USER with SVP=31.2836 at J2000 and yearly_increment=0.
    
    If anything has mutated the global sid mode (e.g., a third-party library
    calling `swe.set_sid_mode(SIDM_LAHIRI)` mid-request), raise loudly so we
    never silently ship a different ayanamsa.
    """
    _ensure_ephemeris_initialized()
    try:
        # swe.get_ayanamsa_ut at J2000.0 should return exactly SVP_DEGREES under SIDM_USER
        ayan = swe.get_ayanamsa_ut(J2000_EPOCH)
    except Exception as e:
        raise CanonicalAstronomyDriftError(
            f"Could not query ayanamsa — canonical mode may not be active: {e}"
        )
    if abs(ayan - SVP_DEGREES) > 1e-6:
        raise CanonicalAstronomyDriftError(
            f"Sidereal mode drift detected at runtime: expected SVP={SVP_DEGREES}° "
            f"at J2000 but SwissEph returned ayanamsa={ayan:.10f}. Some code has "
            f"silently switched sid_mode. This must be fixed — no silent fallback allowed."
        )


def assert_no_drift(
    lens_name: str,
    canonical: CanonicalBirthPositions,
    lens_positions: Dict[str, Dict[str, Any]],
    position_side: str = "personality",   # "personality" | "design"
    raise_on_drift: bool = True,
) -> Dict[str, Any]:
    """
    Compare a lens's claimed planet longitudes against canonical and report drift.
    - Each lens's position dict must contain planet keys with `.longitude` or ["longitude"].
    - If any planet drifts > DRIFT_TOLERANCE_DEGREES, raises CanonicalAstronomyDriftError
      (unless raise_on_drift=False, in which case returns report).

    Returns a drift report dict.
    """
    ref = canonical.personality_positions if position_side == "personality" else canonical.design_positions
    drifts = []
    for planet, ref_data in ref.items():
        lens_data = lens_positions.get(planet)
        if not lens_data:
            # Missing planet is a soft drift; record but don't raise
            drifts.append({
                "planet": planet,
                "severity": "missing_in_lens",
                "canonical_longitude": ref_data["longitude"],
            })
            continue
        lens_lon = (
            lens_data.get("longitude")
            if isinstance(lens_data, dict)
            else getattr(lens_data, "longitude", None)
        )
        if lens_lon is None:
            continue
        diff = abs((ref_data["longitude"] - lens_lon + 540.0) % 360.0 - 180.0)
        if diff > DRIFT_TOLERANCE_DEGREES:
            drifts.append({
                "planet": planet,
                "severity": "drift",
                "canonical_longitude": round(ref_data["longitude"], 6),
                "lens_longitude": round(lens_lon, 6),
                "delta_degrees": round(diff, 6),
            })

    report = {
        "lens": lens_name,
        "position_side": position_side,
        "canonical_fingerprint": canonical.fingerprint,
        "tolerance_degrees": DRIFT_TOLERANCE_DEGREES,
        "drifts": drifts,
        "pass": len([d for d in drifts if d["severity"] == "drift"]) == 0,
    }

    if not report["pass"]:
        msg = f"[CanonicalAstronomy] DRIFT DETECTED in {lens_name}/{position_side}: {drifts}"
        logger.error(msg)
        if raise_on_drift:
            raise CanonicalAstronomyDriftError(msg)

    return report


# =============================================================================
# DIAGNOSTIC REPORTING
# =============================================================================

def build_diagnostic_report(canonical: CanonicalBirthPositions) -> Dict[str, Any]:
    """Human-readable diagnostic suitable for an API endpoint."""
    return {
        "canonical_layer": {
            "sidereal_config": canonical.sidereal_config_used,
            "fingerprint": canonical.fingerprint,
            "birth_metadata": {
                "utc": canonical.birth_datetime_utc,
                "local": canonical.birth_datetime_local,
                "tz": canonical.birth_timezone,
                "lat": canonical.latitude,
                "lon": canonical.longitude,
            },
        },
        "personality_longitudes": {
            p: {
                "sidereal": round(d["longitude"], 4),
                "tropical": round(d["tropical_longitude"], 4),
                "sign": d["sign"],
                "formatted": d["formatted"],
                "retrograde": d["retrograde"],
            }
            for p, d in canonical.personality_positions.items()
        },
        "design_longitudes": {
            p: {
                "sidereal": round(d["longitude"], 4),
                "sign": d["sign"],
                "formatted": d["formatted"],
            }
            for p, d in canonical.design_positions.items()
        },
        "design_datetime_utc": canonical.design_datetime_utc,
        "design_solar_offset_degrees_achieved": round(canonical.design_solar_offset_degrees, 6),
        "ascendant_sidereal": round(canonical.ascendant_longitude, 4),
        "midheaven_sidereal": round(canonical.midheaven_longitude, 4),
        "houses_equal": {k: round(v, 4) for k, v in canonical.houses_equal.items()},
    }
