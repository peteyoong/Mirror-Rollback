"""True Sidereal Astrology calculations using Swiss Ephemeris - Project Mirror Spec

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: mirror-deterministic-v1
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
    # NORMALIZE NODES TO CANONICAL STRUCTURE
    # =========================================================================
    # Ensure nodes are available under normalized keys for downstream access
    north_node = planets.get('North Node', planets.get('True Node', planets.get('Mean Node')))
    south_node = planets.get('South Node')
    
    nodes = {
        "north": {
            "mode": "true_node",  # Swiss Ephemeris True Node by default
            "sign": north_node['sign'] if north_node else None,
            "degree": north_node['degree'] if north_node else None,
            "longitude": north_node['longitude'] if north_node else None,
            "house": north_node['house'] if north_node else None,
            "retrograde": north_node.get('retrograde', True),  # Nodes are typically retrograde
        },
        "south": {
            "sign": south_node['sign'] if south_node else None,
            "degree": south_node['degree'] if south_node else None,
            "longitude": south_node['longitude'] if south_node else None,
            "house": south_node['house'] if south_node else None,
            "retrograde": south_node.get('retrograde', True),
        },
        "aliases": ["GC", "True Node", "Mean Node"]  # GC maps to North Node
    }
    
    # =========================================================================
    # NORMALIZE ANGLES TO CANONICAL STRUCTURE
    # =========================================================================
    asc_sign_info = longitude_to_sign_degree(asc_sidereal)
    mc_sign_info = longitude_to_sign_degree(mc_sidereal)
    
    # Calculate IC and DC from ASC and MC
    ic_sidereal = normalize_degrees(mc_sidereal + 180)
    dc_sidereal = normalize_degrees(asc_sidereal + 180)
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
    sun_house = planets['Sun']['house'] if 'Sun' in planets else 1
    # Day chart if Sun is in houses 7-12 (above horizon)
    sect = "day" if sun_house >= 7 else "night"
    
    # =========================================================================
    # COMPUTE INTEGRITY ASSERTIONS (FAIL FAST)
    # =========================================================================
    compute_errors = []
    
    # Assert angles
    for angle_name in ["asc", "mc", "ic", "dc"]:
        if not angles.get(angle_name, {}).get("sign"):
            compute_errors.append(f"Angles: {angle_name} missing sign/degree")
    
    # Assert 12 house cusps
    if len(formatted_houses) != 12:
        compute_errors.append(f"Houses: expected 12 cusps, got {len(formatted_houses)}")
    
    # Assert all 10 major planets
    required_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    for planet_name in required_planets:
        planet = planets.get(planet_name)
        if not planet:
            compute_errors.append(f"Planets: {planet_name} missing")
        elif planet.get('house') is None:
            compute_errors.append(f"Planets: {planet_name} missing house placement")
    
    # Assert nodes
    if not nodes["north"].get("sign"):
        compute_errors.append("Nodes: north missing sign/degree")
    if not nodes["south"].get("sign"):
        compute_errors.append("Nodes: south missing sign/degree")
    if nodes["north"].get("house") is None:
        compute_errors.append("Nodes: north missing house placement")
    if nodes["south"].get("house") is None:
        compute_errors.append("Nodes: south missing house placement")
    
    # If any assertions failed, raise error (do not return partial data)
    if compute_errors:
        raise ValueError(f"Compute Integrity Error: {'; '.join(compute_errors)}")
    
    # Build result with normalized structure
    return {
        'planets': planets,
        'nodes': nodes,  # Normalized node structure
        'angles': angles,  # Normalized angle structure
        'houses': {
            'system': "Equal",
            'cusps': house_cusps,
            'formatted_cusps': formatted_houses,
            'ascendant': asc_sidereal,
            'ascendant_tropical': asc_tropical,
            'mc': mc_sidereal,
            'mc_tropical': mc_tropical
        },
        'sect': sect,
        'sidereal_settings': {
            **final_settings,
            'node_mode': 'true_node'  # Explicit node mode in metadata
        },
        'svp_applied': svp_degrees,
        'julian_day': jd,
        'input_datetime_utc': birth_datetime.isoformat() if hasattr(birth_datetime, 'isoformat') else str(birth_datetime),
        'coordinates': {'lat': lat, 'lon': lon},
        'chart_type': f"True Sidereal User-Defined (SVP {svp_degrees}°, Equal Houses)",
        'compute_integrity': {
            'valid': True,
            'planets_count': len([p for p in required_planets if p in planets]),
            'nodes_mode': 'true_node',
            'houses_count': len(formatted_houses),
            'angles_computed': list(angles.keys())
        }
    }


def close_ephemeris():
    """Clean up Swiss Ephemeris resources"""
    swe.close()


# =============================================================================
# ASPECTS CALCULATION (Required for debug_compute_astrology)
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
    """Calculate aspects between planets
    
    Args:
        planets: Dict of planet data with longitude
    
    Returns:
        List of aspect dicts {body1, body2, type, orb, exact_angle}
    """
    aspects = []
    planet_names = [p for p in planets.keys() if p not in ['Earth', 'South Node']]
    
    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i+1:]:
            long1 = planets[p1]['longitude']
            long2 = planets[p2]['longitude']
            
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
    
    print(f"Test Case: Pete")
    print(f"  Birth (local): 1968-04-01 01:25")
    print(f"  UTC Offset:    +07:30")
    print(f"  Birth (UTC):   {birth_utc.isoformat()}")
    print(f"  Coordinates:   lat={lat}, lon={lon}")
    print(f"  Place:         {birth_place}")
    print(f"  House System:  Equal")
    print(f"  Sidereal Mode: true_sidereal_m (SVP 31.2836°)")
    print(f"  Node Mode:     true_node")
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
        # Compute the chart
        chart = get_full_natal_chart(
            birth_datetime=birth_utc,
            lat=lat,
            lon=lon,
            sidereal_settings=sidereal_settings,
            house_system="Equal"
        )
        
        # Calculate aspects
        aspects = calculate_aspects(chart['planets'])
        
        # Add aspects to chart for completeness
        chart['aspects'] = aspects
        
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
        
        # 4. Planets: confirm all 10 names exist
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
            print(f"   All present: ✓")
        # Print planet positions compactly
        for pname in required_planets:
            if pname in planets:
                p = planets[pname]
                print(f"   {pname:8}: {p.get('degree', 0):5.2f}° {p.get('sign', 'N/A'):12} (House {p.get('house', '?')})")
        print()
        
        # 5. Nodes: North and South with metadata.node_mode
        print("5. NODES:")
        nodes = chart.get('nodes', {})
        north = nodes.get('north', {})
        south = nodes.get('south', {})
        node_mode = chart.get('sidereal_settings', {}).get('node_mode', 'unknown')
        
        print(f"   Node Mode: {node_mode}")
        print(f"   North Node: {north.get('degree', 0):.2f}° {north.get('sign', 'N/A')} (House {north.get('house', '?')})")
        print(f"   South Node: {south.get('degree', 0):.2f}° {south.get('sign', 'N/A')} (House {south.get('house', '?')})")
        print()
        
        # 6. Aspects: count and first 5
        print("6. ASPECTS:")
        print(f"   Total count: {len(aspects)}")
        print(f"   First 5:")
        for asp in aspects[:5]:
            print(f"     {asp['body1']}-{asp['body2']} {asp['type']} ({asp['orb']}°)")
        print()
        
        # 7. Sect
        print("7. SECT:")
        print(f"   {chart.get('sect', 'unknown')}")
        print()
        
        print("-" * 70)
        print("DEBUG COMPLETE: Chart computed successfully with full integrity.")
        print("=" * 70)
        
        return chart
        
    except ValueError as e:
        # Compute Integrity Error
        print("COMPUTE INTEGRITY: FAILED ✗")
        print()
        print(f"ERROR: {str(e)}")
        print()
        print("-" * 70)
        print("FULL JSON PAYLOAD FOR DEBUGGING:")
        print("-" * 70)
        
        # Attempt to get partial chart for debugging
        # Re-run computation without integrity check to see what we got
        try:
            # Temporarily bypass integrity check to show partial data
            import json
            
            # Get Julian Day
            jd = get_julian_day(
                birth_utc.year, birth_utc.month, birth_utc.day,
                birth_utc.hour, birth_utc.minute, birth_utc.second
            )
            
            svp = sidereal_settings['svp_degrees']
            
            # Get what we can
            asc_tropical = calculate_ascendant_tropical(jd, lat, lon)
            asc_sidereal = tropical_to_sidereal(asc_tropical, svp)
            house_cusps = calculate_equal_houses(asc_sidereal)
            
            partial_planets = {}
            for name, planet_id in PLANETS.items():
                try:
                    if name == 'South Node':
                        if 'North Node' in partial_planets:
                            north_node = partial_planets['North Node']
                            south_long = normalize_degrees(north_node['longitude'] + 180)
                            sign_info = longitude_to_sign_degree(south_long)
                            partial_planets[name] = {
                                'longitude': south_long,
                                'sign': sign_info['sign'],
                                'degree': sign_info['degree'],
                                'house': get_house_for_planet(south_long, house_cusps)
                            }
                    else:
                        pos = calculate_planet_position_sidereal(planet_id, jd, svp)
                        pos['house'] = get_house_for_planet(pos['longitude'], house_cusps)
                        partial_planets[name] = pos
                except Exception as planet_err:
                    partial_planets[name] = {'error': str(planet_err)}
            
            partial_chart = {
                'planets': partial_planets,
                'house_cusps': house_cusps,
                'ascendant_sidereal': asc_sidereal,
                'julian_day': jd
            }
            
            print(json.dumps(partial_chart, indent=2, default=str))
            
        except Exception as debug_err:
            print(f"Could not generate partial chart: {debug_err}")
        
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
