"""True Sidereal Astrology calculations using Swiss Ephemeris - Project Mirror Spec"""
import swisseph as swe
from datetime import datetime
from typing import Dict, List, Tuple
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
    'South Node': swe.TRUE_NODE  # We'll calculate south node from north
}

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

def get_julian_day(year: int, month: int, day: int, hour: int, minute: int) -> float:
    """Convert datetime to Julian Day"""
    return swe.julday(year, month, day, hour + minute / 60.0)

def normalize_degrees(degrees: float) -> float:
    """Normalize degrees to 0-360 range"""
    while degrees < 0:
        degrees += 360
    while degrees >= 360:
        degrees -= 360
    return degrees

def calculate_planet_position(planet_id: int, jd: float, sidereal_settings: Dict) -> Dict:
    """Calculate position of a planet using user-defined sidereal mode
    
    Args:
        planet_id: Swiss Ephemeris planet constant
        jd: Julian day
        sidereal_settings: Dict with svp_degrees, reference_year, yearly_increment
    
    Returns:
        Dict with longitude, latitude, sign, degree, formatted
    """
    # Set user-defined sidereal mode - APPLY EXACTLY ONCE
    svp_degrees = sidereal_settings.get('svp_degrees', 31.2836)
    
    # Use SIDM_USER for user-defined ayanamsa
    # Parameters: (ayanamsa_t0, ayan_t0)
    # ayanamsa_t0 = ayanamsa value at t0 (J2000.0)
    # We set the SVP directly
    swe.set_sid_mode(swe.SIDM_USER, svp_degrees, 0)
    
    # Calculate with sidereal flag
    result = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
    
    longitude = result[0][0]
    latitude = result[0][1]
    
    # Calculate sign and degree
    sign_num = int(longitude / 30)
    degree_in_sign = longitude % 30
    
    return {
        'longitude': longitude,
        'latitude': latitude,
        'sign': ZODIAC_SIGNS[sign_num],
        'degree': degree_in_sign,
        'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}"
    }

def calculate_ascendant(jd: float, lat: float, lon: float, sidereal_settings: Dict) -> float:
    """Calculate Ascendant using user-defined sidereal mode
    
    Args:
        jd: Julian day
        lat: Latitude
        lon: Longitude
        sidereal_settings: Sidereal configuration
    
    Returns:
        Ascendant longitude in degrees
    """
    # Set user-defined sidereal mode
    svp_degrees = sidereal_settings.get('svp_degrees', 31.2836)
    swe.set_sid_mode(swe.SIDM_USER, svp_degrees, 0)
    
    # Calculate houses with Placidus just to get Ascendant
    # (We'll recalculate Equal houses separately)
    houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    
    ascendant = ascmc[0]  # First element is Ascendant
    return ascendant

def calculate_equal_houses(ascendant: float) -> List[float]:
    """Calculate Equal house cusps
    
    Args:
        ascendant: Ascendant longitude (house 1 cusp)
    
    Returns:
        List of 12 house cusps
    """
    house_cusps = []
    for i in range(12):
        cusp = normalize_degrees(ascendant + (i * 30))
        house_cusps.append(cusp)
    return house_cusps

def get_house_for_planet(planet_longitude: float, house_cusps: List[float]) -> int:
    """Determine which house a planet is in
    
    Args:
        planet_longitude: Planet's longitude
        house_cusps: List of 12 house cusps
    
    Returns:
        House number (1-12)
    """
    planet_long = normalize_degrees(planet_longitude)
    
    for i in range(12):
        cusp_current = house_cusps[i]
        cusp_next = house_cusps[(i + 1) % 12]
        
        # Handle wrap around 0°
        if cusp_next < cusp_current:
            # House crosses 0° Aries
            if planet_long >= cusp_current or planet_long < cusp_next:
                return i + 1
        else:
            # Normal case
            if cusp_current <= planet_long < cusp_next:
                return i + 1
    
    # Fallback (shouldn't reach here)
    return 1

def get_full_natal_chart(birth_datetime: datetime, lat: float, lon: float, sidereal_settings: Dict = None, house_system: str = "Equal") -> Dict:
    """Calculate complete True Sidereal natal chart with Project Mirror spec
    
    Args:
        birth_datetime: UTC birth datetime
        lat: Latitude
        lon: Longitude
        sidereal_settings: Dict with mode, svp_degrees, reference_year, yearly_increment
        house_system: House system (only "Equal" supported)
    
    Returns:
        Dict with planets, houses, sidereal info
    """
    # Default sidereal settings (Project Mirror spec)
    if sidereal_settings is None:
        sidereal_settings = {
            "mode": "true_sidereal_user_defined",
            "svp_degrees": 31.2836,
            "reference_year": 2000,
            "yearly_increment": 0.0
        }
    
    # Only Equal houses supported
    if house_system != "Equal":
        raise ValueError(f"House system '{house_system}' not supported. Only 'Equal' is supported.")
    
    jd = get_julian_day(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        birth_datetime.hour,
        birth_datetime.minute
    )
    
    # Calculate Ascendant first
    ascendant = calculate_ascendant(jd, lat, lon, sidereal_settings)
    
    # Calculate Equal house cusps
    house_cusps = calculate_equal_houses(ascendant)
    
    # Calculate all planets
    planets = {}
    for name, planet_id in PLANETS.items():
        if name == 'South Node':
            # Calculate South Node as opposite of North Node
            north_node = planets['North Node']
            south_node_long = normalize_degrees(north_node['longitude'] + 180)
            sign_num = int(south_node_long / 30)
            degree_in_sign = south_node_long % 30
            
            planets[name] = {
                'longitude': south_node_long,
                'latitude': -north_node['latitude'],
                'sign': ZODIAC_SIGNS[sign_num],
                'degree': degree_in_sign,
                'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}",
                'house': get_house_for_planet(south_node_long, house_cusps)
            }
        else:
            planet_pos = calculate_planet_position(planet_id, jd, sidereal_settings)
            planet_pos['house'] = get_house_for_planet(planet_pos['longitude'], house_cusps)
            planets[name] = planet_pos
    
    # Calculate Earth as opposite of Sun (for Human Design)
    sun_long = planets['Sun']['longitude']
    earth_long = normalize_degrees(sun_long + 180)
    sign_num = int(earth_long / 30)
    degree_in_sign = earth_long % 30
    planets['Earth'] = {
        'longitude': earth_long,
        'latitude': 0,
        'sign': ZODIAC_SIGNS[sign_num],
        'degree': degree_in_sign,
        'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}",
        'house': get_house_for_planet(earth_long, house_cusps)
    }
    
    # Get current ayanamsa value for reference
    ayanamsa_value = swe.get_ayanamsa_ut(jd)
    
    return {
        'planets': planets,
        'houses': {
            'system': house_system,
            'cusps': house_cusps,
            'ascendant': ascendant,
        },
        'sidereal_settings': sidereal_settings,
        'ayanamsa': ayanamsa_value,
        'julian_day': jd,
        'chart_type': f'True Sidereal User-Defined (SVP {sidereal_settings.get("svp_degrees")})'
    }

def close_ephemeris():
    """Clean up Swiss Ephemeris resources"""
    swe.close()
