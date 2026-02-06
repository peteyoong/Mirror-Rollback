"""True Sidereal Astrology calculations using Swiss Ephemeris - Project Mirror Spec

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: mirror-deterministic-v1

SYMBOLIC COMPUTE CONTRACT:
This module implements the SymbolicComputeContract interface for Astrology.
All payloads must include compute_integrity validation.
===============================================================================

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

# Import from shared symbolic compute contract
from .symbolic_compute_contract import (
    ComputeIntegrityError,
    ComputeIntegrityResult,
    SymbolicPayload,
    ASTROLOGY_REQUIRED_KEYS
)

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


# =============================================================================
# COMPUTE INTEGRITY ERROR - Standardized Error Object
# =============================================================================
class ComputeIntegrityError(Exception):
    """Raised when the astrology compute contract validation fails.
    
    This exception contains structured error information that can be
    serialized to JSON for API responses.
    """
    def __init__(self, errors: List[str], partial_data: Optional[Dict] = None):
        self.errors = errors
        self.partial_data = partial_data
        super().__init__(f"Compute Integrity Error: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict:
        """Return standardized compute integrity error object."""
        return {
            "compute_integrity": {
                "valid": False,
                "errors": self.errors,
                "error_count": len(self.errors),
                "message": "Chart computation failed integrity checks. Do not interpret partial data."
            },
            "partial_data": self.partial_data  # For debugging only
        }


def get_compute_integrity_error(errors: List[str], partial_data: Optional[Dict] = None) -> Dict:
    """Return a standardized compute integrity error object (non-exception version).
    
    Use this when you need to return an error dict instead of raising.
    """
    return {
        "compute_integrity": {
            "valid": False,
            "errors": errors,
            "error_count": len(errors),
            "message": "Chart computation failed integrity checks. Do not interpret partial data."
        },
        "partial_data": partial_data
    }


# =============================================================================
# ASPECT CALCULATION (Production - moved before get_full_natal_chart)
# =============================================================================
ASPECT_TYPES = {
    'conjunction': {'angle': 0, 'orb': 8},
    'opposition': {'angle': 180, 'orb': 8},
    'trine': {'angle': 120, 'orb': 8},
    'square': {'angle': 90, 'orb': 7},
    'sextile': {'angle': 60, 'orb': 6},
    'quincunx': {'angle': 150, 'orb': 3},
    'semi-sextile': {'angle': 30, 'orb': 2},
}


def calculate_aspects(planets: Dict) -> List[Dict]:
    """Calculate aspects between planets.
    
    Args:
        planets: Dict of planet data with longitude
    
    Returns:
        List of aspect dicts {body1, body2, type, orb, exact_angle, applying}
    """
    aspects = []
    # Exclude Earth and South Node from aspect calculations (South Node aspects via North Node opposition)
    planet_names = [p for p in planets.keys() if p not in ['Earth', 'South Node']]
    
    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i+1:]:
            long1 = planets[p1].get('longitude', 0)
            long2 = planets[p2].get('longitude', 0)
            
            # Calculate angular separation
            diff = abs(long1 - long2)
            if diff > 180:
                diff = 360 - diff
            
            # Check against each aspect type
            for aspect_name, aspect_config in ASPECT_TYPES.items():
                angle = aspect_config['angle']
                orb = aspect_config['orb']
                
                deviation = abs(diff - angle)
                if deviation <= orb:
                    aspects.append({
                        'body1': p1,
                        'body2': p2,
                        'type': aspect_name,
                        'orb': round(deviation, 2),
                        'exact_angle': round(diff, 2),
                        'applying': planets[p1].get('speed', 0) > planets[p2].get('speed', 0)
                    })
                    break  # Only one aspect type per planet pair
    
    # Sort by orb (tighter aspects first)
    aspects.sort(key=lambda x: x['orb'])
    return aspects


def get_full_natal_chart(
    birth_datetime: datetime,
    lat: float,
    lon: float,
    sidereal_settings: Optional[Dict] = None,
    house_system: str = "Equal",
    node_mode: str = "true_node"
) -> Dict:
    """Calculate complete True Sidereal natal chart per Project Mirror spec.
    
    SWISS EPHEMERIS COMPUTE CONTRACT:
    This function MUST return a complete, validated payload or raise
    ComputeIntegrityError. Partial charts are NEVER returned.
    
    MANDATORY SETTINGS:
    - Sidereal Mode: true_sidereal_user_defined
    - SVP: 31.2836° (default)
    - Reference Year: 2000 (default)
    - Yearly Increment: 0.0 (FIXED - no precession)
    - House System: Equal ONLY
    - Node Mode: true_node (default) or mean_node
    
    Args:
        birth_datetime: UTC birth datetime (MUST be UTC)
        lat: Geographic latitude
        lon: Geographic longitude
        sidereal_settings: Optional override for sidereal configuration
        house_system: House system (only "Equal" is supported)
        node_mode: "true_node" (default) or "mean_node"
    
    Returns:
        Dict with complete natal chart data including:
        - metadata (with node_mode)
        - planets (with sign, degree, house, retrograde)
        - nodes (north/south with canonical structure)
        - angles (asc/dc/mc/ic)
        - houses (12 cusps)
        - aspects (list with body1/body2/type/orb)
        - sect (day/night)
    
    Raises:
        ComputeIntegrityError: If any required data is missing or invalid
        ValueError: If house_system is not "Equal"
    """
    # =========================================================================
    # VALIDATE INPUTS
    # =========================================================================
    if sidereal_settings is None:
        sidereal_settings = {}
    
    # Validate node_mode
    valid_node_modes = ["true_node", "mean_node"]
    if node_mode not in valid_node_modes:
        node_mode = "true_node"  # Default to true_node
    
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
    
    # =========================================================================
    # CALCULATE JULIAN DAY
    # =========================================================================
    jd = get_julian_day(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        birth_datetime.hour,
        birth_datetime.minute,
        birth_datetime.second if hasattr(birth_datetime, 'second') else 0
    )
    
    # =========================================================================
    # CALCULATE ANGLES (ASC/MC)
    # =========================================================================
    asc_tropical = calculate_ascendant_tropical(jd, lat, lon)
    asc_sidereal = tropical_to_sidereal(asc_tropical, svp_degrees)
    
    mc_tropical = calculate_mc_tropical(jd, lat, lon)
    mc_sidereal = tropical_to_sidereal(mc_tropical, svp_degrees)
    
    # Calculate IC and DC
    ic_sidereal = normalize_degrees(mc_sidereal + 180)
    dc_sidereal = normalize_degrees(asc_sidereal + 180)
    
    # =========================================================================
    # CALCULATE EQUAL HOUSES
    # =========================================================================
    house_cusps = calculate_equal_houses(asc_sidereal)
    
    # =========================================================================
    # CALCULATE ALL PLANETS WITH RETROGRADE STATUS
    # =========================================================================
    planets = {}
    required_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    
    for name, planet_id in PLANETS.items():
        if name == 'South Node':
            # South Node is calculated after North Node
            continue
        
        planet_pos = calculate_planet_position_sidereal(planet_id, jd, svp_degrees)
        house = get_house_for_planet(planet_pos['longitude'], house_cusps)
        
        # Determine retrograde status (negative speed = retrograde)
        speed = planet_pos.get('speed', 0)
        is_retrograde = speed < 0
        
        # Ensure house is integer 1-12
        house = int(house) if house is not None else None
        if house is not None and (house < 1 or house > 12):
            house = ((house - 1) % 12) + 1  # Normalize to 1-12
        
        planets[name] = {
            'longitude': planet_pos['longitude'],
            'tropical_longitude': planet_pos.get('tropical_longitude'),
            'latitude': planet_pos.get('latitude', 0),
            'sign': planet_pos['sign'],
            'degree': planet_pos['degree'],
            'formatted': planet_pos.get('formatted', f"{planet_pos['degree']:.0f}°{planet_pos['sign']}"),
            'house': house,
            'speed': speed,
            'retrograde': is_retrograde
        }
    
    # =========================================================================
    # NORMALIZE NODES TO CANONICAL STRUCTURE
    # =========================================================================
    # Handle various node naming conventions (True Node, Mean Node, North Node, GC)
    north_node_raw = planets.get('North Node') or planets.get('True Node') or planets.get('Mean Node') or planets.get('GC')
    
    if north_node_raw:
        north_house = north_node_raw.get('house')
        if north_house is not None:
            north_house = int(north_house)
            if north_house < 1 or north_house > 12:
                north_house = ((north_house - 1) % 12) + 1
        
        # Calculate South Node as opposite of North Node
        south_node_long = normalize_degrees(north_node_raw['longitude'] + 180)
        south_sign_info = longitude_to_sign_degree(south_node_long)
        south_house = get_house_for_planet(south_node_long, house_cusps)
        if south_house is not None:
            south_house = int(south_house)
            if south_house < 1 or south_house > 12:
                south_house = ((south_house - 1) % 12) + 1
        
        # Nodes are typically retrograde (True Node oscillates, Mean Node always retrograde)
        node_retrograde = True
        if node_mode == "true_node":
            # True Node can occasionally be direct, check speed
            node_retrograde = north_node_raw.get('speed', -1) < 0
        
        nodes = {
            "north": {
                "mode": node_mode,
                "sign": north_node_raw['sign'],
                "degree": north_node_raw['degree'],
                "longitude": north_node_raw['longitude'],
                "house": north_house,
                "retrograde": node_retrograde,
                "formatted": north_node_raw.get('formatted', f"{north_node_raw['degree']:.0f}°{north_node_raw['sign']}")
            },
            "south": {
                "sign": south_sign_info['sign'],
                "degree": south_sign_info['degree'],
                "longitude": south_node_long,
                "house": south_house,
                "retrograde": node_retrograde,
                "formatted": south_sign_info['formatted']
            },
            "aliases": ["GC", "True Node", "Mean Node"]  # GC maps to North Node
        }
        
        # Also add South Node to planets dict for aspect calculations
        planets['South Node'] = {
            'longitude': south_node_long,
            'tropical_longitude': normalize_degrees(north_node_raw.get('tropical_longitude', 0) + 180),
            'latitude': -north_node_raw.get('latitude', 0),
            'sign': south_sign_info['sign'],
            'degree': south_sign_info['degree'],
            'formatted': south_sign_info['formatted'],
            'house': south_house,
            'retrograde': node_retrograde
        }
    else:
        # Nodes not found - will trigger integrity error
        nodes = {
            "north": {"mode": node_mode, "sign": None, "degree": None, "longitude": None, "house": None, "retrograde": None},
            "south": {"sign": None, "degree": None, "longitude": None, "house": None, "retrograde": None},
            "aliases": ["GC", "True Node", "Mean Node"]
        }
    
    # =========================================================================
    # CALCULATE EARTH (for Human Design)
    # =========================================================================
    if 'Sun' in planets:
        sun = planets['Sun']
        earth_long = normalize_degrees(sun['longitude'] + 180)
        earth_tropical = normalize_degrees(sun.get('tropical_longitude', 0) + 180)
        earth_sign = longitude_to_sign_degree(earth_long)
        earth_house = get_house_for_planet(earth_long, house_cusps)
        if earth_house is not None:
            earth_house = int(earth_house)
        
        planets['Earth'] = {
            'longitude': earth_long,
            'tropical_longitude': earth_tropical,
            'latitude': 0,
            'sign': earth_sign['sign'],
            'degree': earth_sign['degree'],
            'formatted': earth_sign['formatted'],
            'house': earth_house,
            'retrograde': False  # Earth doesn't go retrograde from our perspective
        }
    
    # =========================================================================
    # FORMAT HOUSES
    # =========================================================================
    formatted_houses = []
    for i, cusp in enumerate(house_cusps):
        sign_info = longitude_to_sign_degree(cusp)
        formatted_houses.append({
            'house': i + 1,  # Integer 1-12
            'cusp': cusp,
            'sign': sign_info['sign'],
            'degree': sign_info['degree'],
            'formatted': sign_info['formatted']
        })
    
    # =========================================================================
    # FORMAT ANGLES
    # =========================================================================
    asc_sign_info = longitude_to_sign_degree(asc_sidereal)
    mc_sign_info = longitude_to_sign_degree(mc_sidereal)
    ic_sign_info = longitude_to_sign_degree(ic_sidereal)
    dc_sign_info = longitude_to_sign_degree(dc_sidereal)
    
    angles = {
        "asc": {
            "sign": asc_sign_info['sign'],
            "degree": asc_sign_info['degree'],
            "longitude": asc_sidereal,
            "formatted": asc_sign_info['formatted']
        },
        "dc": {
            "sign": dc_sign_info['sign'],
            "degree": dc_sign_info['degree'],
            "longitude": dc_sidereal,
            "formatted": dc_sign_info['formatted']
        },
        "mc": {
            "sign": mc_sign_info['sign'],
            "degree": mc_sign_info['degree'],
            "longitude": mc_sidereal,
            "formatted": mc_sign_info['formatted']
        },
        "ic": {
            "sign": ic_sign_info['sign'],
            "degree": ic_sign_info['degree'],
            "longitude": ic_sidereal,
            "formatted": ic_sign_info['formatted']
        }
    }
    
    # =========================================================================
    # DETERMINE SECT (DAY/NIGHT)
    # =========================================================================
    sun_house = planets.get('Sun', {}).get('house', 1)
    # Day chart if Sun is in houses 7-12 (above horizon)
    sect = "day" if sun_house and sun_house >= 7 else "night"
    
    # =========================================================================
    # CALCULATE ASPECTS
    # =========================================================================
    aspects = calculate_aspects(planets)
    
    # =========================================================================
    # INTERPRETATION BOUNDARY - DO NOT CROSS
    # =========================================================================
    # This payload contains DETERMINISTIC FACTS only.
    # - Positions (longitudes, degrees)
    # - Classifications (signs, houses)
    # - Timestamps and settings
    #
    # This layer must NEVER include:
    # - Meanings or symbolism
    # - Personality descriptions
    # - Predictions or advice
    # - "Good/bad" judgments
    #
    # Interpretation and narrative generation must occur DOWNSTREAM
    # in a separate layer (e.g., AI prompt assembly, UI copy).
    # =========================================================================
    
    # =========================================================================
    # COMPUTE INTEGRITY ASSERTIONS (FAIL FAST)
    # =========================================================================
    compute_errors = []
    
    # 1. Assert angles: asc/dc/mc/ic exist with sign+degree
    for angle_name in ["asc", "mc", "ic", "dc"]:
        angle = angles.get(angle_name, {})
        if not angle.get("sign"):
            compute_errors.append(f"Angles: {angle_name} missing sign")
        if angle.get("degree") is None:
            compute_errors.append(f"Angles: {angle_name} missing degree")
    
    # 2. Assert houses: exactly 12 cusps exist, each with sign+degree
    if len(formatted_houses) != 12:
        compute_errors.append(f"Houses: expected 12 cusps, got {len(formatted_houses)}")
    else:
        for h in formatted_houses:
            if not h.get("sign"):
                compute_errors.append(f"Houses: house {h.get('house', '?')} missing sign")
            if h.get("degree") is None:
                compute_errors.append(f"Houses: house {h.get('house', '?')} missing degree")
    
    # 3. Assert planets: Sun..Pluto all exist with sign+degree+house+retrograde
    for planet_name in required_planets:
        planet = planets.get(planet_name)
        if not planet:
            compute_errors.append(f"Planets: {planet_name} missing")
        else:
            if not planet.get('sign'):
                compute_errors.append(f"Planets: {planet_name} missing sign")
            if planet.get('degree') is None:
                compute_errors.append(f"Planets: {planet_name} missing degree")
            if planet.get('house') is None:
                compute_errors.append(f"Planets: {planet_name} missing house")
            if planet.get('retrograde') is None:
                compute_errors.append(f"Planets: {planet_name} missing retrograde status")
    
    # 4. Assert nodes: nodes.north and nodes.south exist with sign+degree+house
    #    AND metadata.node_mode exists
    if not nodes["north"].get("sign"):
        compute_errors.append("Nodes: north missing sign")
    if nodes["north"].get("degree") is None:
        compute_errors.append("Nodes: north missing degree")
    if nodes["north"].get("house") is None:
        compute_errors.append("Nodes: north missing house")
    if not nodes["south"].get("sign"):
        compute_errors.append("Nodes: south missing sign")
    if nodes["south"].get("degree") is None:
        compute_errors.append("Nodes: south missing degree")
    if nodes["south"].get("house") is None:
        compute_errors.append("Nodes: south missing house")
    if not nodes["north"].get("mode"):
        compute_errors.append("Nodes: metadata.node_mode missing")
    
    # 5. Assert aspects: list exists and each has body1/body2/type/orb
    if not isinstance(aspects, list):
        compute_errors.append("Aspects: must be a list")
    else:
        for i, asp in enumerate(aspects[:10]):  # Check first 10
            if not asp.get('body1'):
                compute_errors.append(f"Aspects[{i}]: missing body1")
            if not asp.get('body2'):
                compute_errors.append(f"Aspects[{i}]: missing body2")
            if not asp.get('type'):
                compute_errors.append(f"Aspects[{i}]: missing type")
            if asp.get('orb') is None:
                compute_errors.append(f"Aspects[{i}]: missing orb")
    
    # 6. Assert sect: exists and is "day" or "night"
    if sect not in ["day", "night"]:
        compute_errors.append(f"Sect: must be 'day' or 'night', got '{sect}'")
    
    # =========================================================================
    # FAIL FAST - DO NOT RETURN PARTIAL DATA
    # =========================================================================
    if compute_errors:
        partial_data = {
            'planets_found': list(planets.keys()),
            'angles_found': list(angles.keys()),
            'houses_count': len(formatted_houses),
            'aspects_count': len(aspects) if isinstance(aspects, list) else 0,
            'nodes_north_sign': nodes.get('north', {}).get('sign'),
            'nodes_south_sign': nodes.get('south', {}).get('sign'),
        }
        raise ComputeIntegrityError(compute_errors, partial_data)
    
    # =========================================================================
    # BUILD FINAL PAYLOAD WITH METADATA
    # =========================================================================
    return {
        # Metadata block (includes node_mode as required)
        'metadata': {
            'node_mode': node_mode,
            'house_system': "Equal",
            'sidereal_mode': final_settings['mode'],
            'svp_degrees': svp_degrees,
            'computation_version': 'mirror-deterministic-v1',
            'julian_day': jd,
            'input_datetime_utc': birth_datetime.isoformat() if hasattr(birth_datetime, 'isoformat') else str(birth_datetime),
            'coordinates': {'lat': lat, 'lon': lon},
        },
        
        # Core chart data
        'planets': planets,
        'nodes': nodes,
        'angles': angles,
        'houses': {
            'system': "Equal",
            'cusps': house_cusps,
            'formatted_cusps': formatted_houses,
            'ascendant': asc_sidereal,
            'ascendant_tropical': asc_tropical,
            'mc': mc_sidereal,
            'mc_tropical': mc_tropical
        },
        'aspects': aspects,
        'sect': sect,
        
        # Legacy compatibility fields
        'sidereal_settings': {
            **final_settings,
            'node_mode': node_mode
        },
        'svp_applied': svp_degrees,
        'julian_day': jd,
        'input_datetime_utc': birth_datetime.isoformat() if hasattr(birth_datetime, 'isoformat') else str(birth_datetime),
        'coordinates': {'lat': lat, 'lon': lon},
        'chart_type': f"True Sidereal User-Defined (SVP {svp_degrees}°, Equal Houses)",
        
        # Compute integrity confirmation
        'compute_integrity': {
            'valid': True,
            'planets_count': len([p for p in required_planets if p in planets]),
            'nodes_mode': node_mode,
            'houses_count': len(formatted_houses),
            'angles_computed': list(angles.keys()),
            'aspects_count': len(aspects)
        }
    }


def close_ephemeris():
    """Clean up Swiss Ephemeris resources"""
    swe.close()


# =============================================================================
# DEBUG HELPER: debug_compute_astrology()
# =============================================================================
# Usage (from REPL or test script):
#   from calculations.astrology import debug_compute_astrology
#   debug_compute_astrology()
#
# Or from project root:
#   python -c "from backend.calculations.astrology import debug_compute_astrology; debug_compute_astrology()"
# =============================================================================

def debug_compute_astrology():
    """Debug runner to compute a full True Sidereal-M chart and print integrity summary.
    
    Test Case: Pete
    - Birth local: 1968-04-01 01:25
    - UTC offset: +07:30 (Malaysia historical timezone)
    - UTC birth: 1968-03-31 17:55:00Z
    - Coordinates: lat=3.1073, lon=101.6070
    - Birth place: Petaling Jaya, Malaysia
    - House system: Equal
    - Sidereal mode: true_sidereal_m (user-defined SVP)
    - Node mode: true_node
    """
    print("=" * 70)
    print("DEBUG: Astrology Compute Integrity Test")
    print("=" * 70)
    print()
    
    # Hardcoded test case for Pete
    # Local: 1968-04-01 01:25 with UTC offset +07:30
    # UTC = Local - 07:30 = 1968-03-31 17:55:00Z
    birth_utc = datetime(1968, 3, 31, 17, 55, 0)
    lat = 3.1073
    lon = 101.6070
    birth_place = "Petaling Jaya, Malaysia"
    
    print("Test Case: Pete")
    print("  Birth (local): 1968-04-01 01:25")
    print("  UTC Offset:    +07:30")
    print(f"  Birth (UTC):   {birth_utc.isoformat()}")
    print(f"  Coordinates:   lat={lat}, lon={lon}")
    print(f"  Place:         {birth_place}")
    print("  House System:  Equal")
    print("  Sidereal Mode: true_sidereal_m (SVP 31.2836°)")
    print("  Node Mode:     true_node")
    print()
    print("-" * 70)
    
    # Sidereal settings for True Sidereal M
    sidereal_settings = {
        "mode": "true_sidereal_m",
        "svp_degrees": 31.2836,  # Project Mirror default SVP
        "reference_year": 2000,
        "yearly_increment": 0.0  # Fixed - no precession
    }
    
    try:
        # Compute the chart using production function (now includes aspects)
        chart = get_full_natal_chart(
            birth_datetime=birth_utc,
            lat=lat,
            lon=lon,
            sidereal_settings=sidereal_settings,
            house_system="Equal",
            node_mode="true_node"
        )
        
        # =====================================================================
        # INTEGRITY REPORT
        # =====================================================================
        print("COMPUTE INTEGRITY: PASSED ✓")
        print()
        
        # 1. Top-level keys
        print("1. TOP-LEVEL KEYS:")
        print(f"   {list(chart.keys())}")
        print()
        
        # 2. Angles: ASC/DC/MC/IC
        print("2. ANGLES:")
        angles = chart.get('angles', {})
        for angle_name in ['asc', 'dc', 'mc', 'ic']:
            angle = angles.get(angle_name, {})
            sign = angle.get('sign', 'N/A')
            degree = angle.get('degree', 0)
            print(f"   {angle_name.upper():3}: {degree:5.2f}° {sign}")
        print()
        
        # 3. Houses: count of cusps, house 1 cusp
        print("3. HOUSES:")
        houses = chart.get('houses', {})
        formatted_cusps = houses.get('formatted_cusps', [])
        print(f"   Cusp count: {len(formatted_cusps)}")
        if formatted_cusps:
            h1 = formatted_cusps[0]
            print(f"   House 1:    {h1.get('degree', 0):.2f}° {h1.get('sign', 'N/A')}")
        print()
        
        # 4. Planets: confirm all 10 names exist with retrograde status
        print("4. PLANETS:")
        required_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", 
                           "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        planets = chart.get('planets', {})
        present = [p for p in required_planets if p in planets]
        missing = [p for p in required_planets if p not in planets]
        print(f"   Required (10): {len(present)}/10 present")
        if missing:
            print(f"   MISSING: {missing}")
        else:
            print("   All present: ✓")
        # Print planet positions compactly with retrograde
        for pname in required_planets:
            if pname in planets:
                p = planets[pname]
                retro = "Rx" if p.get('retrograde') else ""
                print(f"   {pname:8}: {p.get('degree', 0):5.2f}° {p.get('sign', 'N/A'):12} (House {p.get('house', '?')}) {retro}")
        print()
        
        # 5. Nodes: North and South with metadata.node_mode
        print("5. NODES:")
        nodes = chart.get('nodes', {})
        north = nodes.get('north', {})
        south = nodes.get('south', {})
        # Get node_mode from metadata (new structure) or sidereal_settings (legacy)
        node_mode = chart.get('metadata', {}).get('node_mode') or chart.get('sidereal_settings', {}).get('node_mode', 'unknown')
        
        print(f"   metadata.node_mode: {node_mode}")
        print(f"   nodes.north.mode: {north.get('mode', 'N/A')}")
        print(f"   North Node: {north.get('degree', 0):.2f}° {north.get('sign', 'N/A')} (House {north.get('house', '?')})")
        print(f"   South Node: {south.get('degree', 0):.2f}° {south.get('sign', 'N/A')} (House {south.get('house', '?')})")
        print(f"   aliases: {nodes.get('aliases', [])}")
        print()
        
        # 6. Aspects: count and first 5 (now from chart directly)
        print("6. ASPECTS:")
        aspects = chart.get('aspects', [])
        print(f"   Total count: {len(aspects)}")
        print("   First 5:")
        for asp in aspects[:5]:
            print(f"     {asp['body1']}-{asp['body2']} {asp['type']} ({asp['orb']}°)")
        print()
        
        # 7. Sect
        print("7. SECT:")
        print(f"   {chart.get('sect', 'unknown')}")
        print()
        
        # 8. Metadata block
        print("8. METADATA:")
        metadata = chart.get('metadata', {})
        for key, value in metadata.items():
            if key != 'coordinates':
                print(f"   {key}: {value}")
        print()
        
        print("-" * 70)
        print("DEBUG COMPLETE: Chart computed successfully with full integrity.")
        print("=" * 70)
        
        return chart
        
    except ComputeIntegrityError as e:
        # Compute Integrity Error - structured failure
        print("COMPUTE INTEGRITY: FAILED ✗")
        print()
        print(f"ERROR: {str(e)}")
        print(f"Errors ({len(e.errors)}):")
        for err in e.errors:
            print(f"  - {err}")
        print()
        print("-" * 70)
        print("PARTIAL DATA FOR DEBUGGING:")
        print("-" * 70)
        
        import json
        if e.partial_data:
            print(json.dumps(e.partial_data, indent=2, default=str))
        
        print("=" * 70)
        raise
        
    except ValueError as e:
        # Legacy ValueError (e.g., invalid house system)
        print(f"VALIDATION ERROR: {str(e)}")
        print("=" * 70)
        raise
    
    except Exception as e:
        # Unexpected error
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {str(e)}")
        print("=" * 70)
        raise


# =============================================================================
# ADDITIONAL DEBUG ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Allow running directly: python astrology.py
    debug_compute_astrology()
