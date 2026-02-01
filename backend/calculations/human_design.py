"""Human Design calculations using True Sidereal positions"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from .astrology import get_full_natal_chart, normalize_degrees
import swisseph as swe
import math

# I-Ching Hexagram Gate mapping (64 gates)
# Each gate corresponds to 5.625 degrees (360/64)
GATE_MAPPING = {
    # Format: (start_degree, end_degree, gate_number, hexagram_name)
    # Aries (0-30°)
    0: [(0, 5.625, 25, 'Innocence'), (5.625, 11.25, 51, 'Shock'), (11.25, 16.875, 21, 'Biting Through'),
        (16.875, 22.5, 17, 'Following'), (22.5, 28.125, 27, 'Nourishment')],
    # Taurus (30-60°)
    30: [(28.125, 30, 27, 'Nourishment'), (30, 33.75, 42, 'Increase'), (33.75, 39.375, 3, 'Difficulty'),
         (39.375, 45, 51, 'Shock'), (45, 50.625, 27, 'Nourishment'), (50.625, 56.25, 24, 'Return')],
    # ... (simplified for V1 - full mapping would include all 64 gates)
}

def longitude_to_gate(longitude: float) -> Dict:
    """Convert longitude to I-Ching gate"""
    gate_degree = 360 / 64
    gate_number = int(longitude / gate_degree) + 1
    line = int(((longitude % gate_degree) / gate_degree) * 6) + 1
    
    # Wrap gate number to 1-64
    if gate_number > 64:
        gate_number = gate_number % 64
    if gate_number == 0:
        gate_number = 64
    
    return {
        'gate': gate_number,
        'line': line,
        'formatted': f"{gate_number}.{line}"
    }

def calculate_design_date(birth_datetime: datetime, lat: float = 0, lon: float = 0, 
                          svp_degrees: float = 31.2836) -> Tuple[datetime, float, Dict]:
    """Calculate Design date using numerical solver
    
    The Design date is NOT simply 88 days before birth.
    It's the precise moment when the sidereal Sun was 88 degrees
    BEFORE its position at birth.
    
    Algorithm:
    1. Get birth Sun sidereal longitude
    2. Calculate target: birth_sun - 88 degrees (normalized to 0-360)
    3. Binary search in window of 70-110 days before birth
    4. Find timestamp where Sun is within 0.01° of target
    
    Args:
        birth_datetime: UTC birth datetime
        lat: Latitude (for consistency, not used in Sun calc)
        lon: Longitude (for consistency, not used in Sun calc)
        svp_degrees: Sidereal Vernal Point offset
    
    Returns:
        Tuple of (design_datetime, offset_degrees, debug_info)
    """
    # Ensure we're working with UTC
    if birth_datetime.tzinfo is None:
        birth_datetime = birth_datetime.replace(tzinfo=timezone.utc)
    
    # Get birth Sun sidereal position
    birth_sun_sidereal = _get_sun_sidereal(birth_datetime, svp_degrees)
    
    # Target: 88 degrees before birth Sun
    target_sun = normalize_degrees(birth_sun_sidereal - 88.0)
    
    # Search window: 70-110 days before birth
    early_bound = birth_datetime - timedelta(days=110)
    late_bound = birth_datetime - timedelta(days=70)
    
    # Binary search parameters
    tolerance = 0.01  # degrees
    max_iterations = 50
    
    low = early_bound
    high = late_bound
    best_datetime = None
    best_delta = 999
    
    for iteration in range(max_iterations):
        # Calculate midpoint
        mid_timestamp = low + (high - low) / 2
        mid_sun = _get_sun_sidereal(mid_timestamp, svp_degrees)
        
        # Calculate angular delta
        delta = _angular_difference(mid_sun, target_sun)
        
        # Track best result
        if delta < best_delta:
            best_delta = delta
            best_datetime = mid_timestamp
        
        # Check convergence
        if delta < tolerance:
            break
        
        # Determine search direction
        # Sun moves ~1° per day forward through zodiac
        # Signed difference: positive means mid_sun is ahead of target
        signed_diff = (mid_sun - target_sun + 180) % 360 - 180
        
        if signed_diff > 0:
            # mid_sun is ahead of target, need earlier time
            high = mid_timestamp
        else:
            # mid_sun is behind target, need later time
            low = mid_timestamp
    
    # Build debug info
    debug_info = {
        "birth_sun_sidereal": birth_sun_sidereal,
        "target_sun_sidereal": target_sun,
        "design_sun_sidereal": _get_sun_sidereal(best_datetime, svp_degrees),
        "search_iterations": iteration + 1,
        "converged": best_delta < tolerance
    }
    
    return best_datetime, best_delta, debug_info


def _get_sun_sidereal(dt: datetime, svp_degrees: float = 31.2836) -> float:
    """Get sidereal Sun longitude at a given datetime
    
    Uses tropical calculation minus fixed SVP.
    
    Args:
        dt: UTC datetime
        svp_degrees: Sidereal Vernal Point offset
    
    Returns:
        Sidereal Sun longitude (0-360)
    """
    # Convert to Julian Day
    if dt.tzinfo is not None:
        # Convert to UTC if timezone-aware
        utc_dt = dt.astimezone(timezone.utc)
    else:
        utc_dt = dt
    
    decimal_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour)
    
    # Get tropical Sun position
    result = swe.calc_ut(jd, swe.SUN, 0)
    tropical_sun = result[0][0]
    
    # Convert to sidereal using fixed SVP
    sidereal_sun = normalize_degrees(tropical_sun - svp_degrees)
    
    return sidereal_sun


def _angular_difference(a: float, b: float) -> float:
    """Calculate shortest angular distance between two angles
    
    Args:
        a, b: Angles in degrees (0-360)
    
    Returns:
        Absolute shortest distance (0-180)
    """
    diff = abs(a - b) % 360
    if diff > 180:
        diff = 360 - diff
    return diff

def determine_type(defined_centers: Dict) -> str:
    """Determine Human Design Type based on defined centers"""
    sacral_defined = defined_centers.get('Sacral', False)
    throat_defined = defined_centers.get('Throat', False)
    solar_plexus_defined = defined_centers.get('Solar Plexus', False)
    ego_defined = defined_centers.get('Ego', False)
    
    # Simplified type determination for V1
    if sacral_defined:
        return 'Generator' if not throat_defined else 'Manifesting Generator'
    elif throat_defined and (ego_defined or solar_plexus_defined):
        return 'Manifestor'
    elif not sacral_defined and not throat_defined:
        return 'Reflector'
    else:
        return 'Projector'

def determine_authority(defined_centers: Dict) -> str:
    """Determine Inner Authority based on defined centers"""
    if defined_centers.get('Solar Plexus', False):
        return 'Emotional Authority'
    elif defined_centers.get('Sacral', False):
        return 'Sacral Authority'
    elif defined_centers.get('Spleen', False):
        return 'Splenic Authority'
    elif defined_centers.get('Ego', False):
        return 'Ego Authority'
    elif defined_centers.get('G Center', False):
        return 'Self-Projected Authority'
    else:
        return 'Mental/Outer Authority'

def calculate_centers(personality_gates: List[int], design_gates: List[int]) -> Dict:
    """Calculate which centers are defined based on gates
    Simplified for V1 - full implementation would check channel connections
    """
    # Gate to Center mapping (simplified)
    center_gates = {
        'Head': [61, 63, 64],
        'Ajna': [47, 24, 4, 17, 43, 11],
        'Throat': [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16],
        'G Center': [7, 1, 13, 10, 15, 2, 46, 25],
        'Sacral': [5, 14, 29, 59, 9, 3, 42, 27, 34],
        'Solar Plexus': [6, 37, 22, 36, 30, 55, 49],
        'Spleen': [48, 57, 44, 50, 32, 28, 18],
        'Ego': [21, 40, 26, 51],
        'Root': [53, 60, 52, 19, 39, 41, 58, 38, 54]
    }
    
    all_gates = set(personality_gates + design_gates)
    defined_centers = {}
    
    for center, gates in center_gates.items():
        # Simplified: center is defined if any of its gates are activated
        # Full implementation would check for complete channels
        defined_centers[center] = any(gate in all_gates for gate in gates)
    
    return defined_centers

def get_human_design_chart(birth_datetime: datetime, lat: float, lon: float,
                           sidereal_settings: Dict = None) -> Dict:
    """Calculate complete Human Design bodygraph
    
    Args:
        birth_datetime: UTC birth datetime
        lat: Geographic latitude
        lon: Geographic longitude  
        sidereal_settings: Optional sidereal settings override
    
    Returns:
        Dict with HD type, authority, profile, gates, design date info
    """
    # Default sidereal settings
    if sidereal_settings is None:
        sidereal_settings = {
            "mode": "true_sidereal_user_defined",
            "svp_degrees": 31.2836,
            "reference_year": 2000,
            "yearly_increment": 0.0
        }
    
    svp_degrees = sidereal_settings.get("svp_degrees", 31.2836)
    
    # Get Personality (Conscious) chart at birth
    personality_chart = get_full_natal_chart(birth_datetime, lat, lon, sidereal_settings)
    
    # Calculate Design date using numerical solver
    design_datetime, design_offset_degrees, design_debug = calculate_design_date(
        birth_datetime, lat, lon, svp_degrees
    )
    
    # Get Design (Unconscious) chart at solved design date
    design_chart = get_full_natal_chart(design_datetime, lat, lon, sidereal_settings)
    
    # Extract key planets for Human Design
    hd_planets = ['Sun', 'Earth', 'North Node', 'South Node', 'Moon']
    
    personality_data = {}
    design_data = {}
    
    for planet in hd_planets:
        # Personality
        p_pos = personality_chart['planets'][planet]
        personality_data[planet] = {
            'position': p_pos,
            'gate': longitude_to_gate(p_pos['longitude'])
        }
        
        # Design
        d_pos = design_chart['planets'][planet]
        design_data[planet] = {
            'position': d_pos,
            'gate': longitude_to_gate(d_pos['longitude'])
        }
    
    # Get all gates
    personality_gates = [personality_data[p]['gate']['gate'] for p in hd_planets]
    design_gates = [design_data[p]['gate']['gate'] for p in hd_planets]
    
    # Calculate centers
    defined_centers = calculate_centers(personality_gates, design_gates)
    
    # Determine type and authority
    hd_type = determine_type(defined_centers)
    authority = determine_authority(defined_centers)
    
    # Calculate Profile (Sun and Earth lines)
    personality_sun_line = personality_data['Sun']['gate']['line']
    design_sun_line = design_data['Sun']['gate']['line']
    profile = f"{personality_sun_line}/{design_sun_line}"
    
    # Calculate Incarnation Cross (simplified)
    p_sun_gate = personality_data['Sun']['gate']['gate']
    p_earth_gate = personality_data['Earth']['gate']['gate']
    d_sun_gate = design_data['Sun']['gate']['gate']
    d_earth_gate = design_data['Earth']['gate']['gate']
    
    incarnation_cross = f"Right Angle Cross of {p_sun_gate}/{p_earth_gate}"
    
    return {
        'type': hd_type,
        'authority': authority,
        'profile': profile,
        'incarnation_cross': incarnation_cross,
        'personality': personality_data,
        'design': design_data,
        'defined_centers': defined_centers,
        'strategy': get_strategy_for_type(hd_type),
        'chart_type': 'True Sidereal Human Design'
    }

def get_strategy_for_type(hd_type: str) -> str:
    """Get strategy description for each type"""
    strategies = {
        'Generator': 'To Respond',
        'Manifesting Generator': 'To Respond and Inform',
        'Manifestor': 'To Inform',
        'Projector': 'To Wait for Invitation',
        'Reflector': 'To Wait a Lunar Cycle'
    }
    return strategies.get(hd_type, 'Unknown')
