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


# =============================================================================
# HUMAN DESIGN CHANNEL, CENTER, TYPE, AUTHORITY, PROFILE LOGIC
# =============================================================================

# Complete list of 36 Human Design channels
# Format: (gate1, gate2, center1, center2)
HD_CHANNELS = [
    # Head to Ajna
    (64, 47, 'Head', 'Ajna'),
    (61, 24, 'Head', 'Ajna'),
    (63, 4, 'Head', 'Ajna'),
    # Ajna to Throat
    (17, 62, 'Ajna', 'Throat'),
    (43, 23, 'Ajna', 'Throat'),
    (11, 56, 'Ajna', 'Throat'),
    # Throat to G Center
    (31, 7, 'Throat', 'G Center'),
    (8, 1, 'Throat', 'G Center'),
    (33, 13, 'Throat', 'G Center'),
    # Throat to Sacral (Motor to Throat)
    (20, 34, 'Throat', 'Sacral'),
    # Throat to Solar Plexus (Motor to Throat)
    (35, 36, 'Throat', 'Solar Plexus'),
    (12, 22, 'Throat', 'Solar Plexus'),
    # Throat to Ego/Heart (Motor to Throat)
    (45, 21, 'Throat', 'Ego'),
    # Throat to Spleen
    (16, 48, 'Throat', 'Spleen'),
    (20, 57, 'Throat', 'Spleen'),
    # G Center to Sacral
    (15, 5, 'G Center', 'Sacral'),
    (2, 14, 'G Center', 'Sacral'),
    (46, 29, 'G Center', 'Sacral'),
    # G Center to Spleen
    (10, 57, 'G Center', 'Spleen'),
    # G Center to Ego
    (25, 51, 'G Center', 'Ego'),
    # Sacral to Spleen
    (27, 50, 'Sacral', 'Spleen'),
    (59, 6, 'Sacral', 'Solar Plexus'),
    (3, 60, 'Sacral', 'Root'),
    (9, 52, 'Sacral', 'Root'),
    (42, 53, 'Sacral', 'Root'),
    (34, 57, 'Sacral', 'Spleen'),
    # Solar Plexus to Root
    (49, 19, 'Solar Plexus', 'Root'),
    (55, 39, 'Solar Plexus', 'Root'),
    (30, 41, 'Solar Plexus', 'Root'),
    (36, 35, 'Solar Plexus', 'Throat'),  # Already listed above
    (37, 40, 'Solar Plexus', 'Ego'),
    # Spleen to Root
    (44, 26, 'Spleen', 'Ego'),
    (28, 38, 'Spleen', 'Root'),
    (18, 58, 'Spleen', 'Root'),
    (32, 54, 'Spleen', 'Root'),
    # Ego to Sacral
    (26, 44, 'Ego', 'Spleen'),  # duplicate, already listed
]

# Clean channel list (remove duplicates, ensure consistent ordering)
HD_CHANNELS_CLEAN = [
    # Head to Ajna (3 channels)
    (64, 47, 'Head', 'Ajna'),
    (61, 24, 'Head', 'Ajna'),
    (63, 4, 'Head', 'Ajna'),
    # Ajna to Throat (3 channels)
    (17, 62, 'Ajna', 'Throat'),
    (43, 23, 'Ajna', 'Throat'),
    (11, 56, 'Ajna', 'Throat'),
    # Throat to G Center (3 channels)
    (31, 7, 'Throat', 'G Center'),
    (8, 1, 'Throat', 'G Center'),
    (33, 13, 'Throat', 'G Center'),
    # G Center to Sacral (3 channels)
    (15, 5, 'G Center', 'Sacral'),
    (2, 14, 'G Center', 'Sacral'),
    (46, 29, 'G Center', 'Sacral'),
    # G Center to Spleen (1 channel)
    (10, 57, 'G Center', 'Spleen'),
    # G Center to Ego (1 channel)
    (25, 51, 'G Center', 'Ego'),
    # Sacral to Throat (1 channel - Motor to Throat)
    (20, 34, 'Sacral', 'Throat'),
    # Sacral to Spleen (2 channels)
    (27, 50, 'Sacral', 'Spleen'),
    (34, 57, 'Sacral', 'Spleen'),
    # Sacral to Solar Plexus (1 channel)
    (59, 6, 'Sacral', 'Solar Plexus'),
    # Sacral to Root (3 channels)
    (3, 60, 'Sacral', 'Root'),
    (9, 52, 'Sacral', 'Root'),
    (42, 53, 'Sacral', 'Root'),
    # Throat to Solar Plexus (2 channels - Motor to Throat)
    (35, 36, 'Throat', 'Solar Plexus'),
    (12, 22, 'Throat', 'Solar Plexus'),
    # Throat to Ego (1 channel - Motor to Throat)
    (45, 21, 'Throat', 'Ego'),
    # Throat to Spleen (2 channels)
    (16, 48, 'Throat', 'Spleen'),
    (57, 20, 'Throat', 'Spleen'),  # 20-57 channel
    # Solar Plexus to Ego (1 channel)
    (37, 40, 'Solar Plexus', 'Ego'),
    # Solar Plexus to Root (3 channels)
    (49, 19, 'Solar Plexus', 'Root'),
    (55, 39, 'Solar Plexus', 'Root'),
    (30, 41, 'Solar Plexus', 'Root'),
    # Spleen to Ego (1 channel)
    (44, 26, 'Spleen', 'Ego'),
    # Spleen to Root (3 channels)
    (28, 38, 'Spleen', 'Root'),
    (18, 58, 'Spleen', 'Root'),
    (32, 54, 'Spleen', 'Root'),
]

# Motors are: Sacral, Solar Plexus, Ego (Heart), Root
MOTOR_CENTERS = {'Sacral', 'Solar Plexus', 'Ego', 'Root'}


def get_defined_channels(all_gates: set) -> List[Tuple]:
    """Find all defined channels based on activated gates
    
    A channel is defined ONLY if BOTH gates are present.
    
    Args:
        all_gates: Set of all activated gate numbers (personality + design)
    
    Returns:
        List of tuples: (gate1, gate2, center1, center2) for each defined channel
    """
    defined_channels = []
    
    for gate1, gate2, center1, center2 in HD_CHANNELS_CLEAN:
        if gate1 in all_gates and gate2 in all_gates:
            defined_channels.append((gate1, gate2, center1, center2))
    
    return defined_channels


def get_defined_centers(defined_channels: List[Tuple]) -> List[str]:
    """Get list of defined centers based on defined channels
    
    A center is defined ONLY if it has at least one FULL channel connected.
    
    Args:
        defined_channels: List of defined channel tuples
    
    Returns:
        List of defined center names
    """
    defined_centers = set()
    
    for gate1, gate2, center1, center2 in defined_channels:
        defined_centers.add(center1)
        defined_centers.add(center2)
    
    return list(defined_centers)


def has_motor_to_throat(defined_channels: List[Tuple]) -> bool:
    """Check if there's a motor connected to Throat
    
    Motors are: Sacral, Solar Plexus, Ego (Heart), Root
    
    This checks for DIRECT motor-to-throat channels only.
    A more complete implementation would trace indirect connections.
    
    Args:
        defined_channels: List of defined channel tuples
    
    Returns:
        True if any motor center is directly connected to Throat
    """
    for gate1, gate2, center1, center2 in defined_channels:
        centers = {center1, center2}
        if 'Throat' in centers:
            other_center = center1 if center2 == 'Throat' else center2
            if other_center in MOTOR_CENTERS:
                return True
    return False


def determine_type(defined_centers: List[str], defined_channels: List[Tuple]) -> str:
    """Determine Human Design Type based on defined centers and channels
    
    Order matters:
    1. Reflector: NO defined centers
    2. Generator: Sacral defined AND no motor-to-throat
    3. Manifesting Generator: Sacral defined AND motor-to-throat
    4. Manifestor: motor-to-throat AND Sacral undefined
    5. Projector: Sacral undefined AND not Reflector or Manifestor
    
    Args:
        defined_centers: List of defined center names
        defined_channels: List of defined channel tuples
    
    Returns:
        HD Type string
    """
    # Convert to set for efficient lookup
    centers_set = set(defined_centers)
    
    # 1. Reflector: NO defined centers
    if len(defined_centers) == 0:
        return 'Reflector'
    
    sacral_defined = 'Sacral' in centers_set
    motor_to_throat = has_motor_to_throat(defined_channels)
    
    # 2. Generator: Sacral defined AND no motor-to-throat
    if sacral_defined and not motor_to_throat:
        return 'Generator'
    
    # 3. Manifesting Generator: Sacral defined AND motor-to-throat
    if sacral_defined and motor_to_throat:
        return 'Manifesting Generator'
    
    # 4. Manifestor: motor-to-throat AND Sacral undefined
    if motor_to_throat and not sacral_defined:
        return 'Manifestor'
    
    # 5. Projector: everything else (Sacral undefined, not Reflector/Manifestor)
    return 'Projector'


def determine_definition(defined_channels: List[Tuple], defined_centers: List[str]) -> str:
    """Determine Definition type based on how centers are connected
    
    Args:
        defined_channels: List of defined channel tuples
        defined_centers: List of defined center names
    
    Returns:
        Definition type: "None", "Single", "Split", "Triple Split", "Quadruple Split"
    """
    if len(defined_centers) == 0:
        return "None"
    
    if len(defined_channels) == 0:
        return "None"
    
    # Build adjacency graph
    graph = {center: set() for center in defined_centers}
    for gate1, gate2, center1, center2 in defined_channels:
        if center1 in graph and center2 in graph:
            graph[center1].add(center2)
            graph[center2].add(center1)
    
    # Count connected components using BFS
    visited = set()
    components = 0
    
    for center in defined_centers:
        if center not in visited:
            components += 1
            # BFS from this center
            queue = [center]
            while queue:
                current = queue.pop(0)
                if current not in visited:
                    visited.add(current)
                    for neighbor in graph.get(current, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
    
    if components == 1:
        return "Single"
    elif components == 2:
        return "Split"
    elif components == 3:
        return "Triple Split"
    else:
        return "Quadruple Split"


def determine_authority(hd_type: str, defined_centers: List[str]) -> str:
    """Determine Inner Authority based on type and defined centers
    
    Reflector → "None (Lunar)"
    Otherwise follow hierarchy:
    Emotional > Sacral > Splenic > Ego > G > Self-Projected > Mental/None
    
    Args:
        hd_type: Human Design type
        defined_centers: List of defined center names
    
    Returns:
        Authority string
    """
    # Reflector special case
    if hd_type == 'Reflector':
        return 'None (Lunar)'
    
    centers_set = set(defined_centers)
    
    # Standard HD authority hierarchy
    if 'Solar Plexus' in centers_set:
        return 'Emotional'
    if 'Sacral' in centers_set:
        return 'Sacral'
    if 'Spleen' in centers_set:
        return 'Splenic'
    if 'Ego' in centers_set:
        return 'Ego Manifested' if 'Throat' in centers_set else 'Ego Projected'
    if 'G Center' in centers_set:
        return 'Self-Projected'
    
    # Mental/Environment authority (Projector with only Head/Ajna defined)
    return 'Mental/Environment'


def calculate_profile(personality_sun_line: int, design_sun_line: int) -> str:
    """Calculate Human Design Profile
    
    Profile = personality Sun line / design Sun line
    No inversion, no fallback.
    
    Args:
        personality_sun_line: Line number (1-6) from personality Sun gate
        design_sun_line: Line number (1-6) from design Sun gate
    
    Returns:
        Profile string (e.g., "3/5")
    """
    return f"{personality_sun_line}/{design_sun_line}"


def calculate_centers_old(personality_gates: List[int], design_gates: List[int]) -> Dict:
    """DEPRECATED: Old center calculation (incorrect)
    Kept for reference only - DO NOT USE
    """
    pass

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
        'chart_type': 'True Sidereal Human Design',
        # Design date solver outputs
        'design_datetime_utc_iso': design_datetime.isoformat() if hasattr(design_datetime, 'isoformat') else str(design_datetime),
        'design_offset_degrees': design_offset_degrees,
        'design_solver_debug': design_debug
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
