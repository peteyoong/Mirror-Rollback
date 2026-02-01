"""True Sidereal Astrology calculations using Swiss Ephemeris - Project Mirror Spec

This module implements True Sidereal astrology with:
- User-defined SVP (Sidereal Vernal Point) 
- Fixed ayanamsa (no yearly increment/precession)
- Equal House System ONLY

Ground Truth Test Case (Mel):
- Local birth: 1981-07-13 07:25
- Timezone: +07:30
- UTC birth: 1981-07-12T23:55:00Z
- Location: Melaka, Malaysia (lat=2.1889, lon=102.250999)
- SVP: 31.2836 degrees at year 2000, yearly_increment=0.0
"""
import swisseph as swe
from datetime import datetime
from typing import Dict, List, Optional
import math

# Set ephemeris path (Swiss Ephemeris will use built-in data)
swe.set_ephe_path(None)

# Planet constants
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
    'South Node': swe.TRUE_NODE  # Calculate as opposite of North Node
}

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]


def get_julian_day(year: int, month: int, day: int, hour: int, minute: int, second: int = 0) -> float:
    """Convert datetime to Julian Day
    
    Args:
        year, month, day, hour, minute, second: UTC datetime components
    
    Returns:
        Julian Day number
    """
    decimal_hour = hour + minute / 60.0 + second / 3600.0
    return swe.julday(year, month, day, decimal_hour)


def normalize_degrees(degrees: float) -> float:
    """Normalize degrees to 0-360 range"""
    degrees = degrees % 360
    if degrees < 0:
        degrees += 360
    return degrees


def tropical_to_sidereal(tropical_longitude: float, svp_degrees: float) -> float:
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


def longitude_to_sign_degree(longitude: float) -> Dict:
    """Convert longitude to sign and degree within sign
    
    Args:
        longitude: Ecliptic longitude (0-360)
    
    Returns:
        Dict with sign index, sign name, degree in sign, formatted string
    """
    longitude = normalize_degrees(longitude)
    sign_num = int(longitude / 30)
    degree_in_sign = longitude % 30
    
    return {
        'sign_index': sign_num,
        'sign': ZODIAC_SIGNS[sign_num],
        'degree': degree_in_sign,
        'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}"
    }


def calculate_planet_position_tropical(planet_id: int, jd: float) -> Dict:
    """Calculate tropical position of a planet
    
    Args:
        planet_id: Swiss Ephemeris planet constant
        jd: Julian day
    
    Returns:
        Dict with tropical longitude, latitude, distance, speed
    """
    # Calculate without sidereal flag - pure tropical
    result = swe.calc_ut(jd, planet_id, 0)
    
    return {
        'longitude': result[0][0],
        'latitude': result[0][1],
        'distance': result[0][2],
        'speed': result[0][3]
    }


def calculate_planet_position_sidereal(planet_id: int, jd: float, svp_degrees: float) -> Dict:
    """Calculate sidereal position of a planet using fixed SVP
    
    Args:
        planet_id: Swiss Ephemeris planet constant
        jd: Julian day
        svp_degrees: Fixed SVP offset
    
    Returns:
        Dict with sidereal longitude, latitude, sign, degree, formatted
    """
    # Get tropical position first
    tropical = calculate_planet_position_tropical(planet_id, jd)
    
    # Convert to sidereal using fixed SVP
    sidereal_longitude = tropical_to_sidereal(tropical['longitude'], svp_degrees)
    
    # Get sign info
    sign_info = longitude_to_sign_degree(sidereal_longitude)
    
    return {
        'longitude': sidereal_longitude,
        'tropical_longitude': tropical['longitude'],
        'latitude': tropical['latitude'],
        'sign': sign_info['sign'],
        'degree': sign_info['degree'],
        'formatted': sign_info['formatted'],
        'speed': tropical['speed']
    }


def calculate_ascendant_tropical(jd: float, lat: float, lon: float) -> float:
    """Calculate tropical Ascendant
    
    Args:
        jd: Julian day
        lat: Geographic latitude
        lon: Geographic longitude
    
    Returns:
        Tropical Ascendant longitude
    """
    # Use Placidus temporarily just to get accurate Ascendant/MC
    # The house cusps from this will be discarded - we use Equal houses
    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    return ascmc[0]  # Ascendant is first element


def calculate_mc_tropical(jd: float, lat: float, lon: float) -> float:
    """Calculate tropical Midheaven (MC)
    
    Args:
        jd: Julian day
        lat: Geographic latitude
        lon: Geographic longitude
    
    Returns:
        Tropical MC longitude
    """
    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    return ascmc[1]  # MC is second element


def calculate_equal_houses(ascendant_sidereal: float) -> List[float]:
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


def get_house_for_planet(planet_longitude: float, house_cusps: List[float]) -> int:
    """Determine which house a planet is in
    
    A planet is in house N if its longitude falls between 
    house N cusp and house N+1 cusp.
    
    Args:
        planet_longitude: Planet's sidereal longitude
        house_cusps: List of 12 house cusps
    
    Returns:
        House number (1-12)
    """
    planet_long = normalize_degrees(planet_longitude)
    
    for i in range(12):
        cusp_current = house_cusps[i]
        cusp_next = house_cusps[(i + 1) % 12]
        
        # Handle wrap around 0° Aries
        if cusp_next < cusp_current:
            # House spans across 0°
            if planet_long >= cusp_current or planet_long < cusp_next:
                return i + 1
        else:
            # Normal case
            if cusp_current <= planet_long < cusp_next:
                return i + 1
    
    # Fallback (should not reach here with correct logic)
    return 1


def get_full_natal_chart(
    birth_datetime: datetime,
    lat: float,
    lon: float,
    sidereal_settings: Optional[Dict] = None,
    house_system: str = "Equal"
) -> Dict:
    """Calculate complete True Sidereal natal chart per Project Mirror spec
    
    MANDATORY SETTINGS:
    - Sidereal Mode: true_sidereal_user_defined
    - SVP: 31.2836° (default)
    - Reference Year: 2000 (default)
    - Yearly Increment: 0.0 (FIXED - no precession)
    - House System: Equal ONLY
    
    Args:
        birth_datetime: UTC birth datetime (MUST be UTC)
        lat: Geographic latitude
        lon: Geographic longitude
        sidereal_settings: Optional override for sidereal configuration
        house_system: House system (only "Equal" is supported)
    
    Returns:
        Dict with planets, houses, sidereal settings, debug info
    """
    # Enforce default sidereal settings (Project Mirror spec)
    if sidereal_settings is None:
        sidereal_settings = {}
    
    # Apply defaults with user overrides
    final_settings = {
        "mode": sidereal_settings.get("mode", "true_sidereal_user_defined"),
        "svp_degrees": sidereal_settings.get("svp_degrees", 31.2836),
        "reference_year": sidereal_settings.get("reference_year", 2000),
        "yearly_increment": sidereal_settings.get("yearly_increment", 0.0)
    }
    
    svp_degrees = final_settings["svp_degrees"]
    
    # Validate house system - ONLY Equal is supported
    if house_system != "Equal":
        raise ValueError(f"House system '{house_system}' not supported. Project Mirror requires 'Equal' houses ONLY.")
    
    # Calculate Julian Day from UTC datetime
    jd = get_julian_day(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        birth_datetime.hour,
        birth_datetime.minute,
        birth_datetime.second if hasattr(birth_datetime, 'second') else 0
    )
    
    # Calculate Ascendant (tropical first, then convert)
    asc_tropical = calculate_ascendant_tropical(jd, lat, lon)
    asc_sidereal = tropical_to_sidereal(asc_tropical, svp_degrees)
    
    # Calculate MC (tropical first, then convert)
    mc_tropical = calculate_mc_tropical(jd, lat, lon)
    mc_sidereal = tropical_to_sidereal(mc_tropical, svp_degrees)
    
    # Calculate Equal house cusps from sidereal Ascendant
    house_cusps = calculate_equal_houses(asc_sidereal)
    
    # Calculate all planets
    planets = {}
    for name, planet_id in PLANETS.items():
        if name == 'South Node':
            # South Node is exactly opposite to North Node
            north_node = planets['North Node']
            south_node_long = normalize_degrees(north_node['longitude'] + 180)
            sign_info = longitude_to_sign_degree(south_node_long)
            
            planets[name] = {
                'longitude': south_node_long,
                'tropical_longitude': normalize_degrees(north_node['tropical_longitude'] + 180),
                'latitude': -north_node['latitude'],
                'sign': sign_info['sign'],
                'degree': sign_info['degree'],
                'formatted': sign_info['formatted'],
                'house': get_house_for_planet(south_node_long, house_cusps)
            }
        else:
            planet_pos = calculate_planet_position_sidereal(planet_id, jd, svp_degrees)
            planet_pos['house'] = get_house_for_planet(planet_pos['longitude'], house_cusps)
            planets[name] = planet_pos
    
    # Calculate Earth as opposite of Sun (needed for Human Design)
    sun = planets['Sun']
    earth_long = normalize_degrees(sun['longitude'] + 180)
    earth_tropical = normalize_degrees(sun['tropical_longitude'] + 180)
    earth_sign = longitude_to_sign_degree(earth_long)
    
    planets['Earth'] = {
        'longitude': earth_long,
        'tropical_longitude': earth_tropical,
        'latitude': 0,
        'sign': earth_sign['sign'],
        'degree': earth_sign['degree'],
        'formatted': earth_sign['formatted'],
        'house': get_house_for_planet(earth_long, house_cusps)
    }
    
    # Format house cusps with sign information
    formatted_houses = []
    for i, cusp in enumerate(house_cusps):
        sign_info = longitude_to_sign_degree(cusp)
        formatted_houses.append({
            'house': i + 1,
            'cusp': cusp,
            'sign': sign_info['sign'],
            'degree': sign_info['degree'],
            'formatted': sign_info['formatted']
        })
    
    # Build result
    return {
        'planets': planets,
        'houses': {
            'system': "Equal",
            'cusps': house_cusps,
            'formatted_cusps': formatted_houses,
            'ascendant': asc_sidereal,
            'ascendant_tropical': asc_tropical,
            'mc': mc_sidereal,
            'mc_tropical': mc_tropical
        },
        'sidereal_settings': final_settings,
        'svp_applied': svp_degrees,
        'julian_day': jd,
        'input_datetime_utc': birth_datetime.isoformat() if hasattr(birth_datetime, 'isoformat') else str(birth_datetime),
        'chart_type': f"True Sidereal User-Defined (SVP {svp_degrees}°, Equal Houses)"
    }


def close_ephemeris():
    """Clean up Swiss Ephemeris resources"""
    swe.close()
