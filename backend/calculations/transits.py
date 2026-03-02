"""Real-Time Transit Engine - Project Mirror Phase 1 (Deterministic Core)

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: transit-engine-v1

CONSTRAINTS:
- No interpretation text
- No predictive language
- Pure astronomical + geometric data
- ZERO interpretation logic
===============================================================================

This module implements Real-Time Transit calculations with:
- Swiss Ephemeris (pyswisseph)
- True Sidereal settings:
  - Ayanamsa: Fixed Sidereal Vernal Point 31.2836
  - Yearly Increment: 0.00
  - Reference Year: 2000
  - House System: Equal
"""

import swisseph as swe
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Set ephemeris path (Swiss Ephemeris will use built-in data)
swe.set_ephe_path(None)

# Transit planet constants (Sun through Pluto)
TRANSIT_PLANETS = {
    'sun': swe.SUN,
    'moon': swe.MOON,
    'mercury': swe.MERCURY,
    'venus': swe.VENUS,
    'mars': swe.MARS,
    'jupiter': swe.JUPITER,
    'saturn': swe.SATURN,
    'uranus': swe.URANUS,
    'neptune': swe.NEPTUNE,
    'pluto': swe.PLUTO,
}

# Zodiac signs
ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# Aspect definitions (angle, name)
ASPECT_DEFINITIONS = {
    'conjunction': 0,
    'sextile': 60,
    'square': 90,
    'trine': 120,
    'opposition': 180,
}

# Fixed sidereal settings (Project Mirror spec)
DEFAULT_SVP_DEGREES = 31.2836
DEFAULT_REFERENCE_YEAR = 2000
DEFAULT_YEARLY_INCREMENT = 0.0


def get_julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day
    
    Args:
        dt: UTC datetime
    
    Returns:
        Julian Day number
    """
    decimal_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, decimal_hour)


def normalize_degrees(degrees: float) -> float:
    """Normalize degrees to 0-360 range"""
    degrees = degrees % 360
    if degrees < 0:
        degrees += 360
    return degrees


def tropical_to_sidereal(tropical_longitude: float, svp_degrees: float = DEFAULT_SVP_DEGREES) -> float:
    """Convert tropical longitude to sidereal using fixed SVP
    
    For True Sidereal with fixed SVP (yearly_increment=0):
    sidereal = tropical - SVP
    
    Args:
        tropical_longitude: Tropical ecliptic longitude (0-360)
        svp_degrees: Sidereal Vernal Point offset in degrees
    
    Returns:
        Sidereal longitude (0-360)
    """
    sidereal = tropical_longitude - svp_degrees
    return normalize_degrees(sidereal)


def longitude_to_sign(longitude: float) -> str:
    """Convert longitude to zodiac sign name
    
    Args:
        longitude: Ecliptic longitude (0-360)
    
    Returns:
        Zodiac sign name
    """
    longitude = normalize_degrees(longitude)
    sign_num = int(longitude / 30)
    return ZODIAC_SIGNS[sign_num]


def calculate_equal_house_cusps(ascendant_sidereal: float) -> List[float]:
    """Calculate Equal house cusps from sidereal Ascendant
    
    Equal House System: Each house is exactly 30° wide.
    House 1 cusp = Ascendant
    House N cusp = Ascendant + ((N-1) * 30°)
    
    Args:
        ascendant_sidereal: Sidereal Ascendant longitude
    
    Returns:
        List of 12 house cusps (sidereal longitudes)
    """
    house_cusps = []
    for i in range(12):
        cusp = normalize_degrees(ascendant_sidereal + (i * 30))
        house_cusps.append(cusp)
    return house_cusps


def get_house_for_longitude(longitude: float, house_cusps: List[float]) -> int:
    """Determine which house a longitude falls in
    
    A planet is in house N if its longitude falls between 
    house N cusp and house N+1 cusp.
    
    Args:
        longitude: Planet's sidereal longitude
        house_cusps: List of 12 house cusps
    
    Returns:
        House number (1-12)
    """
    longitude = normalize_degrees(longitude)
    
    for i in range(12):
        cusp_current = house_cusps[i]
        cusp_next = house_cusps[(i + 1) % 12]
        
        # Handle wrap around 0° Aries
        if cusp_next < cusp_current:
            # House spans across 0°
            if longitude >= cusp_current or longitude < cusp_next:
                return i + 1
        else:
            # Normal case
            if cusp_current <= longitude < cusp_next:
                return i + 1
    
    # Fallback (should not reach here with correct logic)
    return 1


def calculate_transiting_planet(
    planet_id: int,
    jd: float,
    svp_degrees: float = DEFAULT_SVP_DEGREES,
    house_cusps: Optional[List[float]] = None
) -> Dict[str, Any]:
    """Calculate sidereal position of a transiting planet
    
    Args:
        planet_id: Swiss Ephemeris planet constant
        jd: Julian day
        svp_degrees: Fixed SVP offset
        house_cusps: Optional list of 12 house cusps for house placement
    
    Returns:
        Dict with longitude, sign, retrograde, house (optional)
    """
    # Calculate tropical position (without sidereal flag)
    result = swe.calc_ut(jd, planet_id, 0)
    
    tropical_longitude = result[0][0]
    speed = result[0][3]
    
    # Convert to sidereal using fixed SVP
    sidereal_longitude = tropical_to_sidereal(tropical_longitude, svp_degrees)
    
    # Determine sign
    sign = longitude_to_sign(sidereal_longitude)
    
    # Determine retrograde status (negative speed = retrograde)
    is_retrograde = speed < 0
    
    planet_data = {
        'longitude': round(sidereal_longitude, 2),
        'sign': sign,
        'retrograde': is_retrograde
    }
    
    # Add house if cusps provided
    if house_cusps is not None:
        house = get_house_for_longitude(sidereal_longitude, house_cusps)
        planet_data['house'] = house
    
    return planet_data


def calculate_all_transiting_planets(
    timestamp_utc: datetime,
    svp_degrees: float = DEFAULT_SVP_DEGREES,
    house_cusps: Optional[List[float]] = None
) -> Dict[str, Dict[str, Any]]:
    """Calculate positions of all transiting planets
    
    Args:
        timestamp_utc: UTC timestamp for transit calculation
        svp_degrees: Fixed SVP offset
        house_cusps: Optional list of 12 house cusps for house placement
    
    Returns:
        Dict mapping planet name to position data
    """
    jd = get_julian_day(timestamp_utc)
    
    transiting_planets = {}
    for planet_name, planet_id in TRANSIT_PLANETS.items():
        transiting_planets[planet_name] = calculate_transiting_planet(
            planet_id, jd, svp_degrees, house_cusps
        )
    
    return transiting_planets


def calculate_angular_separation(long1: float, long2: float) -> float:
    """Calculate the angular separation between two longitudes
    
    Args:
        long1: First longitude (0-360)
        long2: Second longitude (0-360)
    
    Returns:
        Angular separation (0-180)
    """
    diff = abs(long1 - long2)
    if diff > 180:
        diff = 360 - diff
    return diff


def calculate_aspect_to_natal(
    transit_planet_name: str,
    transit_longitude: float,
    natal_body_name: str,
    natal_longitude: float,
    orb_deg: float = 2.0
) -> Optional[Dict[str, Any]]:
    """Check if transit planet aspects a natal body within orb
    
    Args:
        transit_planet_name: Name of transiting planet
        transit_longitude: Sidereal longitude of transiting planet
        natal_body_name: Name of natal body
        natal_longitude: Sidereal longitude of natal body
        orb_deg: Maximum orb in degrees
    
    Returns:
        Aspect dict if within orb, None otherwise
    """
    angular_sep = calculate_angular_separation(transit_longitude, natal_longitude)
    
    for aspect_name, aspect_angle in ASPECT_DEFINITIONS.items():
        deviation = abs(angular_sep - aspect_angle)
        if deviation <= orb_deg:
            return {
                'transit_planet': transit_planet_name,
                'aspect': aspect_name,
                'natal_body': natal_body_name,
                'orb': round(deviation, 2),
                'exact_angle_delta': round(deviation, 2)
            }
    
    return None


def calculate_aspects_to_natal(
    transiting_planets: Dict[str, Dict[str, Any]],
    natal_planets: Dict[str, Dict[str, Any]],
    orb_deg: float = 2.0
) -> List[Dict[str, Any]]:
    """Calculate all aspects from transiting planets to natal bodies
    
    Args:
        transiting_planets: Dict of transiting planet positions
        natal_planets: Dict of natal planet positions (from stored chart)
        orb_deg: Maximum orb in degrees
    
    Returns:
        List of aspect dicts sorted by orb (tighter first)
    """
    aspects = []
    
    for transit_name, transit_data in transiting_planets.items():
        transit_long = transit_data['longitude']
        
        for natal_name, natal_data in natal_planets.items():
            # Get natal longitude
            natal_long = natal_data.get('longitude')
            if natal_long is None:
                continue
            
            # Check for aspect
            aspect = calculate_aspect_to_natal(
                transit_name,
                transit_long,
                natal_name.lower(),  # Normalize to lowercase for output
                natal_long,
                orb_deg
            )
            
            if aspect is not None:
                aspects.append(aspect)
    
    # Sort by orb (tighter aspects first)
    aspects.sort(key=lambda x: x['orb'])
    
    return aspects


def extract_natal_planets(chart_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract natal planet positions from stored chart data
    
    Args:
        chart_data: Full chart document from database
    
    Returns:
        Dict mapping planet name to position data with longitude
    """
    # Try to get astrology data
    astrology = chart_data.get('astrology', chart_data)
    planets = astrology.get('planets', {})
    
    # Also include nodes if available
    nodes = astrology.get('nodes', {})
    if nodes:
        north_node = nodes.get('north', {})
        if north_node.get('longitude') is not None:
            planets['North Node'] = north_node
        
        south_node = nodes.get('south', {})
        if south_node.get('longitude') is not None:
            planets['South Node'] = south_node
    
    return planets


def extract_natal_ascendant(chart_data: Dict[str, Any]) -> Optional[float]:
    """Extract natal Ascendant longitude from stored chart data
    
    Args:
        chart_data: Full chart document from database
    
    Returns:
        Sidereal Ascendant longitude or None
    """
    astrology = chart_data.get('astrology', chart_data)
    
    # Try angles structure first (new format)
    angles = astrology.get('angles', {})
    if angles:
        asc = angles.get('asc', {})
        if asc.get('longitude') is not None:
            return asc['longitude']
    
    # Try houses structure (legacy format)
    houses = astrology.get('houses', {})
    if houses:
        asc = houses.get('ascendant')
        if asc is not None:
            return asc
    
    return None


def compute_transits_now(
    chart_data: Dict[str, Any],
    timestamp_utc: Optional[datetime] = None,
    orb_deg: float = 2.0,
    include_houses: bool = True
) -> Dict[str, Any]:
    """Compute real-time transits for a user
    
    This is the main entry point for the Transit Engine.
    
    Args:
        chart_data: Full chart document from database (contains natal positions)
        timestamp_utc: UTC timestamp for transit calculation (default: now)
        orb_deg: Maximum orb for aspects in degrees (default: 2)
        include_houses: Whether to include house placements (default: True)
    
    Returns:
        Complete transit response with meta, transiting_planets, aspects_to_natal_now
    """
    # Use current UTC if timestamp not provided
    if timestamp_utc is None:
        timestamp_utc = datetime.now(timezone.utc)
    
    # Extract natal data
    natal_planets = extract_natal_planets(chart_data)
    
    # Determine house cusps (from natal Ascendant if include_houses)
    house_cusps = None
    if include_houses:
        natal_asc = extract_natal_ascendant(chart_data)
        if natal_asc is not None:
            house_cusps = calculate_equal_house_cusps(natal_asc)
    
    # Calculate transiting planet positions
    transiting_planets = calculate_all_transiting_planets(
        timestamp_utc,
        svp_degrees=DEFAULT_SVP_DEGREES,
        house_cusps=house_cusps
    )
    
    # Calculate aspects to natal bodies
    aspects = calculate_aspects_to_natal(
        transiting_planets,
        natal_planets,
        orb_deg=orb_deg
    )
    
    # Build response
    return {
        'meta': {
            'ayanamsa': f'fixed_sv_{DEFAULT_SVP_DEGREES}',
            'house_system': 'equal',
            'orb_deg': orb_deg
        },
        'timestamp_utc': timestamp_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'transiting_planets': transiting_planets,
        'aspects_to_natal_now': aspects
    }


# =============================================================================
# DETERMINISTIC SNAPSHOT TEST
# =============================================================================

def run_deterministic_test() -> Dict[str, Any]:
    """Run deterministic snapshot test for fixed timestamp
    
    Test timestamp: 2026-03-02T09:00:00Z
    
    Returns:
        Transit calculation result for verification
    """
    from datetime import datetime, timezone
    
    # Fixed test timestamp
    test_timestamp = datetime(2026, 3, 2, 9, 0, 0, tzinfo=timezone.utc)
    
    # Mock natal chart data for testing (Mel's chart from astrology.py)
    # Born: 1981-07-13 07:25 local (+07:30) = 1981-07-12T23:55:00Z
    # Location: Melaka, Malaysia (lat=2.1889, lon=102.250999)
    mock_natal_chart = {
        'astrology': {
            'planets': {
                'Sun': {'longitude': 80.5, 'sign': 'Gemini'},
                'Moon': {'longitude': 356.2, 'sign': 'Pisces'},
                'Mercury': {'longitude': 98.7, 'sign': 'Cancer'},
                'Venus': {'longitude': 108.3, 'sign': 'Cancer'},
                'Mars': {'longitude': 42.1, 'sign': 'Taurus'},
                'Jupiter': {'longitude': 177.8, 'sign': 'Virgo'},
                'Saturn': {'longitude': 147.5, 'sign': 'Leo'},
                'Uranus': {'longitude': 205.2, 'sign': 'Libra'},
                'Neptune': {'longitude': 232.1, 'sign': 'Scorpio'},
                'Pluto': {'longitude': 179.4, 'sign': 'Virgo'},
            },
            'angles': {
                'asc': {'longitude': 110.5}  # Sidereal Ascendant
            }
        }
    }
    
    result = compute_transits_now(
        chart_data=mock_natal_chart,
        timestamp_utc=test_timestamp,
        orb_deg=2.0,
        include_houses=True
    )
    
    return result


if __name__ == '__main__':
    import json
    
    print("=" * 70)
    print("Transit Engine Deterministic Snapshot Test")
    print("Timestamp: 2026-03-02T09:00:00Z")
    print("=" * 70)
    
    result = run_deterministic_test()
    print(json.dumps(result, indent=2))
