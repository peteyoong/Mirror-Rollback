"""True Sidereal Astrology calculations using Swiss Ephemeris"""
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

# Lahiri Ayanamsa (True Sidereal)
AYANAMSA = swe.SIDM_LAHIRI

def get_julian_day(year: int, month: int, day: int, hour: int, minute: int) -> float:
    """Convert datetime to Julian Day"""
    return swe.julday(year, month, day, hour + minute / 60.0)

def get_ayanamsa(jd: float) -> float:
    """Get ayanamsa value for given Julian Day"""
    swe.set_sid_mode(AYANAMSA)
    return swe.get_ayanamsa_ut(jd)

def calculate_planet_position(planet_id: int, jd: float, sidereal: bool = True) -> Dict:
    """Calculate position of a planet"""
    if sidereal:
        swe.set_sid_mode(AYANAMSA)
        result = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
    else:
        result = swe.calc_ut(jd, planet_id)
    
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

def calculate_houses(jd: float, lat: float, lon: float, house_system: str = 'P') -> Dict:
    """Calculate house cusps
    house_system: 'P' = Placidus (default), 'K' = Koch, 'W' = Whole Sign, etc.
    """
    swe.set_sid_mode(AYANAMSA)
    houses, ascmc = swe.houses_ex(jd, lat, lon, house_system.encode(), swe.FLG_SIDEREAL)
    
    return {
        'houses': list(houses),
        'ascendant': ascmc[0],
        'mc': ascmc[1],
        'armc': ascmc[2],
        'vertex': ascmc[3],
        'equatorial_ascendant': ascmc[4],
        'co_ascendant_koch': ascmc[5] if len(ascmc) > 5 else None,
    }

def get_full_natal_chart(birth_datetime: datetime, lat: float, lon: float) -> Dict:
    """Calculate complete True Sidereal natal chart"""
    jd = get_julian_day(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        birth_datetime.hour,
        birth_datetime.minute
    )
    
    ayanamsa_value = get_ayanamsa(jd)
    
    # Calculate all planets
    planets = {}
    for name, planet_id in PLANETS.items():
        if name == 'South Node':
            # Calculate South Node as opposite of North Node
            north_node = planets['North Node']
            south_node_long = (north_node['longitude'] + 180) % 360
            sign_num = int(south_node_long / 30)
            degree_in_sign = south_node_long % 30
            planets[name] = {
                'longitude': south_node_long,
                'latitude': -north_node['latitude'],
                'sign': ZODIAC_SIGNS[sign_num],
                'degree': degree_in_sign,
                'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}"
            }
        else:
            planets[name] = calculate_planet_position(planet_id, jd, sidereal=True)
    
    # Calculate Earth as opposite of Sun (for Human Design)
    sun_long = planets['Sun']['longitude']
    earth_long = (sun_long + 180) % 360
    sign_num = int(earth_long / 30)
    degree_in_sign = earth_long % 30
    planets['Earth'] = {
        'longitude': earth_long,
        'latitude': 0,  # Earth's latitude is always 0 from Sun's perspective
        'sign': ZODIAC_SIGNS[sign_num],
        'degree': degree_in_sign,
        'formatted': f"{int(degree_in_sign)}°{ZODIAC_SIGNS[sign_num]}"
    }
    
    # Calculate houses
    house_data = calculate_houses(jd, lat, lon)
    
    return {
        'planets': planets,
        'houses': house_data,
        'ayanamsa': ayanamsa_value,
        'julian_day': jd,
        'chart_type': 'True Sidereal (Lahiri)'
    }

def close_ephemeris():
    """Clean up Swiss Ephemeris resources"""
    swe.close()
