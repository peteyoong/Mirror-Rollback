"""
Canonical True Sidereal Configuration for Project Mirror

===============================================================================
SINGLE SOURCE OF TRUTH - ALL TRANSIT/ASTROLOGY CALCULATIONS MUST USE THIS
===============================================================================

This module provides the canonical True Sidereal settings used across:
- Natal chart calculations (astrology.py)
- Human Design calculations (human_design.py)
- Transit calculations (transit_signals.py, lunar_cycle.py)
- Aspect calculations

Configuration:
- Zodiac Mode: True Sidereal User-Defined (SIDM_USER)
- SVP (Sidereal Vernal Point): 31.2836° at J2000
- Reference Epoch: J2000 (JD 2451545.0)
- Yearly Increment: 0.0 (FIXED - no precession)
- Aligned with Genetic Matrix / Athen Chimenti framework

DO NOT create alternative sidereal configs elsewhere.
All sidereal calculations must import from here.
"""

import swisseph as swe
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# CANONICAL TRUE SIDEREAL CONFIGURATION
# =============================================================================

# Sidereal Vernal Point - FIXED
SVP_DEGREES = 31.2836

# J2000 Epoch (Julian Day)
J2000_EPOCH = 2451545.0  # Jan 1, 2000, 12:00 TT

# Yearly Increment - FIXED (no precession)
YEARLY_INCREMENT = 0.0

# =============================================================================
# SWISS EPHEMERIS INITIALIZATION
# =============================================================================

# Ephemeris path
EPHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'ephe')
_ephemeris_initialized = False

def _ensure_ephemeris_initialized():
    """Initialize Swiss Ephemeris with canonical sidereal settings."""
    global _ephemeris_initialized
    
    if _ephemeris_initialized:
        return
    
    # Set ephemeris path
    if os.path.exists(EPHE_PATH):
        swe.set_ephe_path(EPHE_PATH)
    else:
        swe.set_ephe_path(None)
        logger.warning(f"[SiderealConfig] Swiss Ephemeris files not found at {EPHE_PATH}, using Moshier fallback")
    
    # Set canonical sidereal mode - SIDM_USER with fixed SVP
    swe.set_sid_mode(swe.SIDM_USER, J2000_EPOCH, SVP_DEGREES)
    
    _ephemeris_initialized = True
    logger.info(f"[SiderealConfig] Initialized True Sidereal mode: SVP={SVP_DEGREES}°, Epoch=J2000")


# =============================================================================
# CALCULATION FLAGS
# =============================================================================

# Sidereal calculation flag (uses SIDM_USER mode set above)
CALC_FLAGS_SIDEREAL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

# Tropical calculation flag (for reference/debugging)
CALC_FLAGS_TROPICAL = swe.FLG_SWIEPH


# =============================================================================
# PLANET CONSTANTS
# =============================================================================

PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
    'North Node': swe.TRUE_NODE,
    'Chiron': swe.CHIRON,
}

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]


# =============================================================================
# CORE CALCULATION HELPERS
# =============================================================================

def get_julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day.
    
    Args:
        dt: Datetime (should be UTC)
    
    Returns:
        Julian Day number
    """
    if dt.tzinfo is not None:
        # Convert to UTC if timezone-aware
        dt = dt.astimezone(timezone.utc)
    
    decimal_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, decimal_hour)


def normalize_degrees(degrees: float) -> float:
    """Normalize degrees to 0-360 range."""
    degrees = degrees % 360
    if degrees < 0:
        degrees += 360
    return degrees


def longitude_to_sign_degree(longitude: float) -> Dict[str, Any]:
    """Convert longitude to sign and degree within sign.

    ── REMEDIATION (angle-staleness-step1-v1, 2026-02) ─────────────────
    This function previously hosted an independent uniform_30 (12-sign)
    attribution implementation that diverged from the canonical
    midpoint-13 Variant A attributor used by `calculations.astrology`.

    Multiple downstream services
    (canonical_astronomy / transit_signals / lunar_cycle / etc.)
    imported this function and therefore minted uniform_30 sign labels
    for transits, lunar phases, Earth-gate, and the drift-detection
    diagnostic — directly contradicting the chart writer's Variant A
    output.

    To eliminate the divergence, this function now DELEGATES to the
    canonical attributor at `calculations.astrology.longitude_to_sign_degree`,
    which honours the global `DEFAULT_MODE = MODE_MIDPOINT13_VARIANT_A`.

    Behaviour change visible to callers:
      * `sign` may now return "Ophiuchus" for longitudes in the
        Ophiuchus band (~14.50° wide, between Scorpio and Sagittarius).
      * `sign_index` continues to be returned. For Variant A it indexes
        into the 13-sign list (Ophiuchus = 8); for legacy uniform_30
        callers that hardcoded `ZODIAC_SIGNS[sign_index]` (12-sign) this
        is a contract change — those callers must read `sign` instead.
      * Return shape (keys + types) is unchanged.

    Args:
        longitude: Ecliptic longitude (0-360). For Mirror's sidereal
                   pipeline this is the sidereal longitude AFTER SVP
                   subtraction.

    Returns:
        Dict with sign_index, sign name, degree in sign, formatted string.
    """
    # Lazy import to avoid load-time circular dependency. `calculations.astrology`
    # does not import from this module, but the lazy import keeps the dependency
    # graph one-directional even if a future import is added.
    from calculations.astrology import longitude_to_sign_degree as _canonical
    return _canonical(normalize_degrees(longitude))


def _legacy_longitude_to_sign_degree_uniform_30(longitude: float) -> Dict[str, Any]:
    """LEGACY — pure uniform_30 (12-sign) attributor preserved verbatim
    for forensic comparisons only. NEVER call from production paths.

    Use `calculations.sign_attribution.attribute_sign_uniform_30(trop)`
    for the public uniform_30 API.

    Build marker: angle-staleness-step1-v1 (preservation block)
    """
    longitude = normalize_degrees(longitude)
    sign_num = int(longitude / 30)
    degree_in_sign = longitude % 30
    return {
        'sign_index': sign_num,
        'sign': ZODIAC_SIGNS[sign_num],
        'degree': degree_in_sign,
        'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}",
    }


# =============================================================================
# TRUE SIDEREAL PLANET POSITION CALCULATION
# =============================================================================

def calculate_planet_sidereal(planet_id: int, dt: datetime) -> Dict[str, Any]:
    """Calculate TRUE SIDEREAL position of a planet.
    
    Uses Swiss Ephemeris with canonical SIDM_USER mode.
    This is the ONLY correct way to calculate sidereal positions in Mirror.
    
    Args:
        planet_id: Swiss Ephemeris planet constant (e.g., swe.SUN, swe.MOON)
        dt: Datetime for calculation (UTC preferred)
    
    Returns:
        Dict with:
        - longitude: Sidereal longitude (0-360)
        - tropical_longitude: Tropical longitude (for reference)
        - sign: Zodiac sign name
        - degree: Degree within sign
        - formatted: "X°Sign" string
        - speed: Daily motion
        - retrograde: Boolean
    """
    _ensure_ephemeris_initialized()
    
    jd = get_julian_day(dt)
    
    # Get tropical position (for reference)
    result_trop = swe.calc_ut(jd, planet_id, CALC_FLAGS_TROPICAL)
    tropical_longitude = normalize_degrees(result_trop[0][0])
    
    # Get sidereal position (using canonical SIDM_USER mode)
    result_sid = swe.calc_ut(jd, planet_id, CALC_FLAGS_SIDEREAL)
    sidereal_longitude = normalize_degrees(result_sid[0][0])
    
    # Get sign info
    sign_info = longitude_to_sign_degree(sidereal_longitude)
    
    return {
        'longitude': sidereal_longitude,
        'tropical_longitude': tropical_longitude,
        'sign': sign_info['sign'],
        'degree': sign_info['degree'],
        'formatted': sign_info['formatted'],
        'speed': result_sid[0][3],
        'retrograde': result_sid[0][3] < 0,
        'latitude': result_sid[0][1],
    }


def calculate_planet_by_name(planet_name: str, dt: datetime) -> Dict[str, Any]:
    """Calculate TRUE SIDEREAL position by planet name.
    
    Args:
        planet_name: Planet name (e.g., "Sun", "Moon", "Mercury")
        dt: Datetime for calculation
    
    Returns:
        Planet position dict with sidereal longitude, sign, etc.
    """
    planet_id = PLANETS.get(planet_name)
    if planet_id is None:
        raise ValueError(f"Unknown planet: {planet_name}")
    
    result = calculate_planet_sidereal(planet_id, dt)
    result['planet'] = planet_name
    return result


def get_all_transiting_planets(dt: Optional[datetime] = None) -> Dict[str, Dict[str, Any]]:
    """Get TRUE SIDEREAL positions of all major transiting planets.
    
    Args:
        dt: Datetime for calculation (default: now UTC)
    
    Returns:
        Dict mapping planet names to their sidereal position data
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    _ensure_ephemeris_initialized()
    
    planets_data = {}
    for planet_name, planet_id in PLANETS.items():
        if planet_name == 'North Node':
            # Skip North Node for basic transit list
            continue
        try:
            planets_data[planet_name] = calculate_planet_sidereal(planet_id, dt)
            planets_data[planet_name]['planet'] = planet_name
        except Exception as e:
            logger.error(f"[SiderealConfig] Error calculating {planet_name}: {e}")
    
    return planets_data


# =============================================================================
# DEBUG / REGRESSION HELPER
# =============================================================================

def debug_transit_positions(dt: Optional[datetime] = None, user_label: str = "Test") -> Dict[str, Any]:
    """Debug helper to verify transit calculations.
    
    Use this to verify True Sidereal positions are correct.
    
    Args:
        dt: Datetime for calculation (default: now UTC)
        user_label: Label for debug output
    
    Returns:
        Full debug output dict
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    _ensure_ephemeris_initialized()
    jd = get_julian_day(dt)
    
    output = {
        "label": user_label,
        "timestamp_utc": dt.isoformat(),
        "julian_day": jd,
        "sidereal_config": {
            "mode": "SIDM_USER (True Sidereal)",
            "svp_degrees": SVP_DEGREES,
            "reference_epoch": "J2000",
            "yearly_increment": YEARLY_INCREMENT,
        },
        "planets": {}
    }
    
    for planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
        planet_id = PLANETS[planet_name]
        pos = calculate_planet_sidereal(planet_id, dt)
        output["planets"][planet_name] = {
            "sidereal_longitude": round(pos['longitude'], 4),
            "tropical_longitude": round(pos['tropical_longitude'], 4),
            "sign": pos['sign'],
            "degree": round(pos['degree'], 2),
            "formatted": pos['formatted'],
            "retrograde": pos['retrograde'],
        }
    
    return output


def close_ephemeris():
    """Clean up Swiss Ephemeris resources."""
    global _ephemeris_initialized
    swe.close()
    _ephemeris_initialized = False
