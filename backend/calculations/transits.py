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
# PHASE 2: WINDOW LOGIC + EXACT HITS + INGRESS + STATIONS + HOUSE ACTIVATION
# =============================================================================
# Version: transit-engine-v2
# Deterministic window scanner - no interpretation
# =============================================================================

from datetime import timedelta
from collections import defaultdict

# Planet weights for house activation scoring
PLANET_WEIGHTS = {
    'sun': 2.5,
    'moon': 2.5,
    'mercury': 1.5,
    'venus': 1.5,
    'mars': 1.5,
    'jupiter': 2.0,
    'saturn': 3.0,
    'uranus': 3.0,
    'neptune': 3.0,
    'pluto': 3.0,
}

# Aspect weights for house activation scoring
ASPECT_WEIGHTS = {
    'conjunction': 2.0,
    'opposition': 2.0,
    'square': 1.5,
    'trine': 1.5,
    'sextile': 1.0,
}


def get_planet_position_at_jd(
    planet_id: int,
    jd: float,
    svp_degrees: float = DEFAULT_SVP_DEGREES
) -> Dict[str, Any]:
    """Get planet position at a specific Julian Day
    
    Returns longitude, sign, speed (for retrograde detection)
    """
    result = swe.calc_ut(jd, planet_id, 0)
    tropical_longitude = result[0][0]
    speed = result[0][3]
    
    sidereal_longitude = tropical_to_sidereal(tropical_longitude, svp_degrees)
    sign = longitude_to_sign(sidereal_longitude)
    sign_index = int(sidereal_longitude / 30)
    
    return {
        'longitude': sidereal_longitude,
        'sign': sign,
        'sign_index': sign_index,
        'speed': speed,
        'retrograde': speed < 0
    }


def refine_exact_aspect_time(
    planet_id: int,
    natal_longitude: float,
    aspect_angle: float,
    start_jd: float,
    end_jd: float,
    svp_degrees: float = DEFAULT_SVP_DEGREES,
    max_iterations: int = 20,
    precision: float = 0.01
) -> Optional[Dict[str, Any]]:
    """Binary search to find exact aspect hit timestamp
    
    Args:
        planet_id: Transit planet Swiss Ephemeris ID
        natal_longitude: Natal body's sidereal longitude
        aspect_angle: Aspect angle (0, 60, 90, 120, 180)
        start_jd: Start of search window (Julian Day)
        end_jd: End of search window (Julian Day)
        svp_degrees: SVP offset
        max_iterations: Max binary search iterations
        precision: Target precision in degrees
    
    Returns:
        Dict with timestamp and orb, or None if not found
    """
    # Sample points: 00:00, 06:00, 12:00, 18:00
    sample_jds = [
        start_jd,
        start_jd + 0.25,  # 6 hours
        start_jd + 0.5,   # 12 hours
        start_jd + 0.75,  # 18 hours
        end_jd
    ]
    
    best_jd = None
    best_orb = float('inf')
    
    # Find best sample point
    for jd in sample_jds:
        if jd > end_jd:
            break
        pos = get_planet_position_at_jd(planet_id, jd, svp_degrees)
        transit_long = pos['longitude']
        
        # Calculate angular separation
        diff = abs(transit_long - natal_longitude)
        if diff > 180:
            diff = 360 - diff
        
        orb = abs(diff - aspect_angle)
        if orb < best_orb:
            best_orb = orb
            best_jd = jd
    
    if best_jd is None or best_orb > 5.0:  # Too far from aspect
        return None
    
    # Binary search refinement
    low_jd = max(start_jd, best_jd - 0.5)
    high_jd = min(end_jd, best_jd + 0.5)
    
    for _ in range(max_iterations):
        if best_orb < precision:
            break
        
        mid_jd = (low_jd + high_jd) / 2
        
        # Check three points
        for test_jd in [low_jd, mid_jd, high_jd]:
            pos = get_planet_position_at_jd(planet_id, test_jd, svp_degrees)
            transit_long = pos['longitude']
            
            diff = abs(transit_long - natal_longitude)
            if diff > 180:
                diff = 360 - diff
            
            orb = abs(diff - aspect_angle)
            if orb < best_orb:
                best_orb = orb
                best_jd = test_jd
        
        # Narrow the window around best point
        window = (high_jd - low_jd) / 2
        low_jd = best_jd - window / 2
        high_jd = best_jd + window / 2
        
        # Clamp to bounds
        low_jd = max(start_jd, low_jd)
        high_jd = min(end_jd, high_jd)
    
    if best_orb < 0.5:  # Found a good hit
        return {
            'jd': best_jd,
            'orb': round(best_orb, 2)
        }
    
    return None


def jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to datetime UTC"""
    # Swiss Ephemeris reverse conversion
    year, month, day, hour = swe.revjul(jd)
    
    # Extract time components
    hours = int(hour)
    minutes = int((hour - hours) * 60)
    seconds = int(((hour - hours) * 60 - minutes) * 60)
    
    return datetime(year, month, day, hours, minutes, seconds, tzinfo=timezone.utc)


def refine_ingress_time(
    planet_id: int,
    start_jd: float,
    end_jd: float,
    svp_degrees: float = DEFAULT_SVP_DEGREES,
    max_iterations: int = 20
) -> Optional[Dict[str, Any]]:
    """Binary search to find exact ingress (sign change) timestamp
    
    Returns:
        Dict with timestamp, from_sign, to_sign, or None
    """
    pos_start = get_planet_position_at_jd(planet_id, start_jd, svp_degrees)
    pos_end = get_planet_position_at_jd(planet_id, end_jd, svp_degrees)
    
    if pos_start['sign_index'] == pos_end['sign_index']:
        return None  # No sign change
    
    from_sign = pos_start['sign']
    
    low_jd = start_jd
    high_jd = end_jd
    
    for _ in range(max_iterations):
        mid_jd = (low_jd + high_jd) / 2
        pos_mid = get_planet_position_at_jd(planet_id, mid_jd, svp_degrees)
        
        if pos_mid['sign_index'] == pos_start['sign_index']:
            low_jd = mid_jd
        else:
            high_jd = mid_jd
        
        if high_jd - low_jd < 0.001:  # ~1.4 minutes precision
            break
    
    # Get final position at high_jd (just after sign change)
    pos_final = get_planet_position_at_jd(planet_id, high_jd, svp_degrees)
    
    return {
        'jd': high_jd,
        'from_sign': from_sign,
        'to_sign': pos_final['sign'],
        'longitude': round(pos_final['longitude'], 2)
    }


def refine_station_time(
    planet_id: int,
    start_jd: float,
    end_jd: float,
    svp_degrees: float = DEFAULT_SVP_DEGREES,
    max_iterations: int = 20
) -> Optional[Dict[str, Any]]:
    """Binary search to find station (speed crosses 0) timestamp
    
    Returns:
        Dict with timestamp, type (station_retrograde/station_direct), or None
    """
    pos_start = get_planet_position_at_jd(planet_id, start_jd, svp_degrees)
    pos_end = get_planet_position_at_jd(planet_id, end_jd, svp_degrees)
    
    # Check if speed sign changed
    if (pos_start['speed'] >= 0) == (pos_end['speed'] >= 0):
        return None  # No station
    
    # Determine station type
    station_type = 'station_retrograde' if pos_start['speed'] > 0 else 'station_direct'
    
    low_jd = start_jd
    high_jd = end_jd
    
    for _ in range(max_iterations):
        mid_jd = (low_jd + high_jd) / 2
        pos_mid = get_planet_position_at_jd(planet_id, mid_jd, svp_degrees)
        
        if (pos_mid['speed'] >= 0) == (pos_start['speed'] >= 0):
            low_jd = mid_jd
        else:
            high_jd = mid_jd
        
        if high_jd - low_jd < 0.001:  # ~1.4 minutes precision
            break
    
    # Get final position at station
    station_jd = (low_jd + high_jd) / 2
    pos_station = get_planet_position_at_jd(planet_id, station_jd, svp_degrees)
    
    return {
        'jd': station_jd,
        'type': station_type,
        'longitude': round(pos_station['longitude'], 2),
        'sign': pos_station['sign']
    }


def compute_transits_window(
    chart_data: Dict[str, Any],
    from_utc: Optional[datetime] = None,
    window_days: int = 30,
    orb_deg: float = 2.0,
    include_houses: bool = True,
    granularity: str = "daily"
) -> Dict[str, Any]:
    """Compute transit window with exact hits, ingresses, stations, and house activation
    
    Phase 2 Transit Engine - Deterministic Window Scanner
    
    Args:
        chart_data: Full chart document from database
        from_utc: Start of window (default: now)
        window_days: Length of window in days (30 or 90)
        orb_deg: Maximum orb for aspects
        include_houses: Include house placements
        granularity: "daily" only for now
    
    Returns:
        Complete window response with exact_hits, ingresses, stations, house_activation
    """
    # Use current UTC if not provided
    if from_utc is None:
        from_utc = datetime.now(timezone.utc)
    
    # Normalize to midnight UTC
    from_utc = from_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    to_utc = from_utc + timedelta(days=window_days)
    
    # Extract natal data
    natal_planets = extract_natal_planets(chart_data)
    
    # Build natal body -> house mapping
    natal_body_houses = {}
    for name, data in natal_planets.items():
        if data.get('house'):
            natal_body_houses[name.lower()] = data['house']
    
    # Get house cusps
    house_cusps = None
    natal_asc = extract_natal_ascendant(chart_data)
    if include_houses and natal_asc is not None:
        house_cusps = calculate_equal_house_cusps(natal_asc)
    
    # Results collectors
    exact_hits = []
    ingresses = []
    stations = []
    daily_summaries = []
    house_scores_total = defaultdict(float)
    house_scores_daily = []
    
    # Loose orb for candidate detection
    loose_orb = orb_deg * 1.5
    
    # Previous day's data for comparison (ingress/station detection)
    prev_day_planets = {}
    
    # Daily scan
    current_date = from_utc
    day_index = 0
    
    while current_date < to_utc:
        day_jd = get_julian_day(current_date)
        next_day_jd = day_jd + 1.0
        
        day_str = current_date.strftime('%Y-%m-%d')
        day_events = []
        day_house_scores = defaultdict(float)
        
        # Compute all planet positions for this day
        day_planets = {}
        for planet_name, planet_id in TRANSIT_PLANETS.items():
            day_planets[planet_name] = get_planet_position_at_jd(planet_id, day_jd)
        
        # Check for aspects, ingresses, stations
        for planet_name, planet_id in TRANSIT_PLANETS.items():
            pos = day_planets[planet_name]
            transit_long = pos['longitude']
            
            # Get house for transiting planet
            transit_house = None
            if house_cusps:
                transit_house = get_house_for_longitude(transit_long, house_cusps)
                
                # Add planet-in-house presence to house score
                planet_weight = PLANET_WEIGHTS.get(planet_name, 1.0)
                day_house_scores[transit_house] += planet_weight * 0.5  # Presence weight
            
            # Check aspects to natal bodies
            for natal_name, natal_data in natal_planets.items():
                natal_long = natal_data.get('longitude')
                if natal_long is None:
                    continue
                
                natal_house = natal_data.get('house')
                
                # Calculate angular separation
                diff = abs(transit_long - natal_long)
                if diff > 180:
                    diff = 360 - diff
                
                # Check each aspect type
                for aspect_name, aspect_angle in ASPECT_DEFINITIONS.items():
                    deviation = abs(diff - aspect_angle)
                    
                    if deviation <= loose_orb:
                        # Candidate found - refine to exact hit
                        refined = refine_exact_aspect_time(
                            planet_id,
                            natal_long,
                            aspect_angle,
                            day_jd,
                            next_day_jd
                        )
                        
                        if refined and refined['orb'] <= orb_deg:
                            hit_dt = jd_to_datetime(refined['jd'])
                            exact_hits.append({
                                'timestamp_utc': hit_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                'transit_planet': planet_name,
                                'aspect': aspect_name,
                                'natal_body': natal_name.lower(),
                                'orb': refined['orb'],
                                'exact_angle_delta': refined['orb']
                            })
                            
                            day_events.append(f"{planet_name}_{aspect_name[:4]}_{natal_name.lower()}")
                            
                            # House activation scoring
                            if natal_house:
                                planet_weight = PLANET_WEIGHTS.get(planet_name, 1.0)
                                aspect_weight = ASPECT_WEIGHTS.get(aspect_name, 1.0)
                                orb_weight = max(0, 1 - (refined['orb'] / orb_deg))
                                
                                score = planet_weight * aspect_weight * orb_weight
                                day_house_scores[natal_house] += score
                                house_scores_total[natal_house] += score
            
            # Check for ingress (sign change from previous day)
            if prev_day_planets.get(planet_name):
                prev_pos = prev_day_planets[planet_name]
                if prev_pos['sign_index'] != pos['sign_index']:
                    ingress_data = refine_ingress_time(
                        planet_id,
                        day_jd - 1.0,
                        day_jd
                    )
                    if ingress_data:
                        ingress_dt = jd_to_datetime(ingress_data['jd'])
                        ingress_house = None
                        if house_cusps:
                            ingress_house = get_house_for_longitude(ingress_data['longitude'], house_cusps)
                        
                        ingresses.append({
                            'timestamp_utc': ingress_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'planet': planet_name,
                            'from_sign': ingress_data['from_sign'],
                            'to_sign': ingress_data['to_sign'],
                            'longitude': ingress_data['longitude'],
                            'house': ingress_house
                        })
                        
                        day_events.append(f"{planet_name}_ingress_{ingress_data['to_sign'][:3].lower()}")
            
            # Check for station (speed sign change from previous day)
            if prev_day_planets.get(planet_name):
                prev_pos = prev_day_planets[planet_name]
                if (prev_pos['speed'] >= 0) != (pos['speed'] >= 0):
                    station_data = refine_station_time(
                        planet_id,
                        day_jd - 1.0,
                        day_jd
                    )
                    if station_data:
                        station_dt = jd_to_datetime(station_data['jd'])
                        station_house = None
                        if house_cusps:
                            station_house = get_house_for_longitude(station_data['longitude'], house_cusps)
                        
                        stations.append({
                            'timestamp_utc': station_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'planet': planet_name,
                            'type': station_data['type'],
                            'longitude': station_data['longitude'],
                            'sign': station_data['sign'],
                            'house': station_house
                        })
                        
                        day_events.append(f"{planet_name}_{station_data['type']}")
        
        # Store previous day's data
        prev_day_planets = day_planets.copy()
        
        # Daily house scores
        if day_house_scores:
            sorted_houses = sorted(day_house_scores.keys(), key=lambda h: day_house_scores[h], reverse=True)
            top_day_houses = sorted_houses[:3]
            
            house_scores_daily.append({
                'date': day_str,
                'top_houses': top_day_houses,
                'scores': {str(h): round(day_house_scores[h], 1) for h in sorted_houses[:5]}
            })
        
        # Daily summary
        if day_events or day_house_scores:
            sorted_houses = sorted(day_house_scores.keys(), key=lambda h: day_house_scores[h], reverse=True)[:2]
            daily_summaries.append({
                'date': day_str,
                'peak_events': day_events[:5],  # Limit to 5 events per day
                'top_houses': sorted_houses
            })
        
        current_date += timedelta(days=1)
        day_index += 1
    
    # Sort exact_hits by timestamp then planet name for deterministic ordering
    exact_hits.sort(key=lambda x: (x['timestamp_utc'], x['transit_planet']))
    
    # Sort ingresses by timestamp then planet
    ingresses.sort(key=lambda x: (x['timestamp_utc'], x['planet']))
    
    # Sort stations by timestamp then planet
    stations.sort(key=lambda x: (x['timestamp_utc'], x['planet']))
    
    # Compute top houses for entire window
    sorted_total_houses = sorted(house_scores_total.keys(), key=lambda h: house_scores_total[h], reverse=True)
    top_houses = sorted_total_houses[:3]
    
    # Build house activation response
    house_activation = {
        'top_houses': top_houses,
        'scores': {str(h): round(house_scores_total[h], 1) for h in sorted_total_houses if house_scores_total[h] > 0},
        'daily': house_scores_daily
    }
    
    return {
        'meta': {
            'ayanamsa': f'fixed_sv_{DEFAULT_SVP_DEGREES}',
            'house_system': 'equal',
            'orb_deg': orb_deg,
            'window_days': window_days,
            'granularity': granularity
        },
        'window': {
            'from_utc': from_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to_utc': to_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        },
        'exact_hits': exact_hits,
        'ingresses': ingresses,
        'stations': stations,
        'house_activation': house_activation,
        'daily_summary': daily_summaries
    }


def run_window_deterministic_test() -> Dict[str, Any]:
    """Run deterministic window test
    
    Fixed window: from_utc = 2026-03-02T00:00:00Z, window_days=30
    """
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    
    # Same mock natal chart as Phase 1 test
    mock_natal_chart = {
        'astrology': {
            'planets': {
                'Sun': {'longitude': 80.5, 'sign': 'Gemini', 'house': 3},
                'Moon': {'longitude': 356.2, 'sign': 'Pisces', 'house': 12},
                'Mercury': {'longitude': 98.7, 'sign': 'Cancer', 'house': 4},
                'Venus': {'longitude': 108.3, 'sign': 'Cancer', 'house': 4},
                'Mars': {'longitude': 42.1, 'sign': 'Taurus', 'house': 2},
                'Jupiter': {'longitude': 177.8, 'sign': 'Virgo', 'house': 6},
                'Saturn': {'longitude': 147.5, 'sign': 'Leo', 'house': 5},
                'Uranus': {'longitude': 205.2, 'sign': 'Libra', 'house': 7},
                'Neptune': {'longitude': 232.1, 'sign': 'Scorpio', 'house': 8},
                'Pluto': {'longitude': 179.4, 'sign': 'Virgo', 'house': 6},
            },
            'angles': {
                'asc': {'longitude': 110.5}
            }
        }
    }
    
    return compute_transits_window(
        chart_data=mock_natal_chart,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True,
        granularity="daily"
    )


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
