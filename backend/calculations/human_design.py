"""Human Design calculations using True Sidereal positions

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: mirror-deterministic-v1
===============================================================================
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from .astrology import get_full_natal_chart, normalize_degrees, ComputeIntegrityError
import swisseph as swe
import math


# All centers in Human Design
ALL_CENTERS = ['Head', 'Ajna', 'Throat', 'G Center', 'Ego', 'Sacral', 'Solar Plexus', 'Spleen', 'Root']

# =============================================================================
# HUMAN DESIGN RAVE MANDALA GATE WHEEL
# =============================================================================
# The HD gates are NOT evenly distributed around the zodiac.
# They follow the I-Ching sequence mapped to specific zodiac positions.
# Format: (gate_number, start_degree, end_degree) in absolute zodiac degrees
# where Aries 0° = 0, Taurus 0° = 30, etc.

HD_GATE_WHEEL = [
    # Gate, Start Degree, End Degree (absolute zodiac 0-360)
    
    # Aries (0-30°)
    (25, 358.25, 363.867),  # 28°15′ Pisces to 3°52′ Aries (wraps around)
    (17, 3.867, 9.5),       # 3°52′ to 9°30′ Aries
    (21, 9.5, 15.117),      # 9°30′ to 15°07′ Aries
    (51, 15.117, 20.75),    # 15°07′ to 20°45′ Aries
    (42, 20.75, 26.367),    # 20°45′ to 26°22′ Aries
    (3, 26.367, 32.0),      # 26°22′ Aries to 2°00′ Taurus
    
    # Taurus (30-60°)
    (27, 32.0, 37.617),     # 2°00′ to 7°37′ Taurus
    (24, 37.617, 43.25),    # 7°37′ to 13°15′ Taurus
    (2, 43.25, 48.867),     # 13°15′ to 18°52′ Taurus
    (23, 48.867, 54.5),     # 18°52′ to 24°30′ Taurus
    (8, 54.5, 60.117),      # 24°30′ Taurus to 0°07′ Gemini
    
    # Gemini (60-90°)
    (20, 60.117, 65.75),    # 0°07′ to 5°45′ Gemini
    (16, 65.75, 71.367),    # 5°45′ to 11°22′ Gemini
    (35, 71.367, 77.0),     # 11°22′ to 17°00′ Gemini
    (45, 77.0, 82.617),     # 17°00′ to 22°37′ Gemini
    (12, 82.617, 88.25),    # 22°37′ to 28°15′ Gemini
    (15, 88.25, 93.867),    # 28°15′ Gemini to 3°52′ Cancer
    
    # Cancer (90-120°)
    (52, 93.867, 99.5),     # 3°52′ to 9°30′ Cancer
    (39, 99.5, 105.117),    # 9°30′ to 15°07′ Cancer
    (53, 105.117, 110.75),  # 15°07′ to 20°45′ Cancer
    (62, 110.75, 116.367),  # 20°45′ to 26°22′ Cancer
    (56, 116.367, 122.0),   # 26°22′ Cancer to 2°00′ Leo
    
    # Leo (120-150°)
    (31, 122.0, 127.617),   # 2°00′ to 7°37′ Leo
    (33, 127.617, 133.25),  # 7°37′ to 13°15′ Leo
    (7, 133.25, 138.867),   # 13°15′ to 18°52′ Leo
    (4, 138.867, 144.5),    # 18°52′ to 24°30′ Leo
    (29, 144.5, 150.117),   # 24°30′ Leo to 0°07′ Virgo
    
    # Virgo (150-180°)
    (59, 150.117, 155.75),  # 0°07′ to 5°45′ Virgo
    (40, 155.75, 161.367),  # 5°45′ to 11°22′ Virgo
    (64, 161.367, 167.0),   # 11°22′ to 17°00′ Virgo
    (47, 167.0, 172.617),   # 17°00′ to 22°37′ Virgo
    (6, 172.617, 178.25),   # 22°37′ to 28°15′ Virgo
    (46, 178.25, 183.867),  # 28°15′ Virgo to 3°52′ Libra
    
    # Libra (180-210°)
    (18, 183.867, 189.5),   # 3°52′ to 9°30′ Libra
    (48, 189.5, 195.117),   # 9°30′ to 15°07′ Libra
    (57, 195.117, 200.75),  # 15°07′ to 20°45′ Libra
    (32, 200.75, 206.367),  # 20°45′ to 26°22′ Libra
    (50, 206.367, 212.0),   # 26°22′ Libra to 2°00′ Scorpio
    
    # Scorpio (210-240°)
    (28, 212.0, 217.617),   # 2°00′ to 7°37′ Scorpio
    (44, 217.617, 223.25),  # 7°37′ to 13°15′ Scorpio
    (1, 223.25, 228.867),   # 13°15′ to 18°52′ Scorpio
    (43, 228.867, 234.5),   # 18°52′ to 24°30′ Scorpio
    (14, 234.5, 240.117),   # 24°30′ Scorpio to 0°07′ Sagittarius
    
    # Sagittarius (240-270°)
    (34, 240.117, 245.75),  # 0°07′ to 5°45′ Sagittarius
    (9, 245.75, 251.367),   # 5°45′ to 11°22′ Sagittarius
    (5, 251.367, 257.0),    # 11°22′ to 17°00′ Sagittarius
    (26, 257.0, 262.617),   # 17°00′ to 22°37′ Sagittarius
    (11, 262.617, 268.25),  # 22°37′ to 28°15′ Sagittarius
    (10, 268.25, 273.867),  # 28°15′ Sagittarius to 3°52′ Capricorn
    
    # Capricorn (270-300°)
    (58, 273.867, 279.5),   # 3°52′ to 9°30′ Capricorn
    (38, 279.5, 285.117),   # 9°30′ to 15°07′ Capricorn
    (54, 285.117, 290.75),  # 15°07′ to 20°45′ Capricorn
    (61, 290.75, 296.367),  # 20°45′ to 26°22′ Capricorn
    (60, 296.367, 302.0),   # 26°22′ Capricorn to 2°00′ Aquarius
    
    # Aquarius (300-330°)
    (41, 302.0, 307.617),   # 2°00′ to 7°37′ Aquarius
    (19, 307.617, 313.25),  # 7°37′ to 13°15′ Aquarius
    (13, 313.25, 318.867),  # 13°15′ to 18°52′ Aquarius
    (49, 318.867, 324.5),   # 18°52′ to 24°30′ Aquarius
    (30, 324.5, 330.117),   # 24°30′ Aquarius to 0°07′ Pisces
    
    # Pisces (330-360°)
    (55, 330.117, 335.75),  # 0°07′ to 5°45′ Pisces
    (37, 335.75, 341.367),  # 5°45′ to 11°22′ Pisces
    (63, 341.367, 347.0),   # 11°22′ to 17°00′ Pisces
    (22, 347.0, 352.617),   # 17°00′ to 22°37′ Pisces
    (36, 352.617, 358.25),  # 22°37′ to 28°15′ Pisces
    # Gate 25 wraps from Pisces to Aries (handled specially)
]

# =============================================================================
# INCARNATION CROSS NAMES
# =============================================================================
# Maps personality Sun gate to the cross name. The cross is determined by
# the Sun gate in the Personality (conscious) calculation.
# Format: gate_number -> cross_name

INCARNATION_CROSS_NAMES = {
    1: "Sphinx",
    2: "Driver",
    3: "Laws",
    4: "Explanation",
    5: "Consciousness",
    6: "Eden",
    7: "Sphinx",
    8: "Contagion",
    9: "Planning",
    10: "Vessel of Love",
    11: "Education",
    12: "Eden",
    13: "Sphinx",
    14: "Contagion",
    15: "Vessel of Love",
    16: "Planning",
    17: "Service",
    18: "Service",
    19: "Four Ways",
    20: "Sleeping Phoenix",
    21: "Tension",
    22: "Rulership",
    23: "Assimilation",
    24: "Incarnation",
    25: "Vessel of Love",
    26: "Rulership",
    27: "Unexpected",
    28: "Game Player",
    29: "Contagion",
    30: "Contagion",
    31: "Unexpected",
    32: "Maya",
    33: "Four Ways",
    34: "Sleeping Phoenix",
    35: "Consciousness",
    36: "Eden",
    37: "Migration",
    38: "Tension",
    39: "Tension",
    40: "Migration",
    41: "Unexpected",
    42: "Maya",
    43: "Explanation",
    44: "Four Ways",
    45: "Rulership",
    46: "Vessel of Love",
    47: "Rulership",
    48: "Tension",
    49: "Explanation",
    50: "Laws",
    51: "Penetration",
    52: "Service",
    53: "Penetration",
    54: "Penetration",
    55: "Sleeping Phoenix",
    56: "Laws",
    57: "Penetration",
    58: "Service",
    59: "Sleeping Phoenix",
    60: "Laws",
    61: "Maya",
    62: "Maya",
    63: "Consciousness",
    64: "Consciousness",
}

def get_incarnation_cross_name(p_sun_gate: int, profile_line1: int) -> str:
    """
    Get the full incarnation cross name based on personality Sun gate and profile.
    
    The cross angle (Right Angle, Left Angle, Juxtaposition) is determined by the
    first number of the profile:
    - Lines 1, 2, 3, 4 = Right Angle Cross (RAX) - Personal destiny
    - Line 4 with specific gates = Juxtaposition Cross (JXP) - Fixed fate
    - Lines 5, 6 = Left Angle Cross (LAX) - Transpersonal karma
    
    Args:
        p_sun_gate: Personality Sun gate number
        profile_line1: First line of the profile (1-6)
    
    Returns:
        Full cross name like "RAX Migration" or "LAX Tension"
    """
    cross_name = INCARNATION_CROSS_NAMES.get(p_sun_gate, f"Cross of Gate {p_sun_gate}")
    
    # Determine cross angle from profile
    if profile_line1 in [1, 2, 3]:
        angle = "RAX"  # Right Angle Cross
    elif profile_line1 == 4:
        angle = "JXP"  # Juxtaposition Cross
    elif profile_line1 in [5, 6]:
        angle = "LAX"  # Left Angle Cross
    else:
        angle = "RAX"  # Default fallback
    
    return f"{angle} {cross_name}"


def longitude_to_gate(longitude: float) -> Dict:
    """Convert sidereal longitude to I-Ching gate using HD Rave Mandala wheel
    
    The HD gate wheel is NOT a simple 360/64 division.
    Each gate has specific zodiac degree boundaries following I-Ching order.
    
    Args:
        longitude: Sidereal longitude (0-360)
    
    Returns:
        Dict with gate number, line (1-6), and formatted string
    """
    # Normalize to 0-360
    longitude = longitude % 360
    
    # Special handling for Gate 25 which wraps around 0°
    if longitude >= 358.25 or longitude < 3.867:
        gate = 25
        if longitude >= 358.25:
            pos_in_gate = longitude - 358.25
        else:
            pos_in_gate = (360 - 358.25) + longitude
        gate_size = (360 - 358.25) + 3.867  # ~5.617°
    else:
        # Search through gate wheel
        gate = None
        pos_in_gate = 0
        gate_size = 5.625  # Default
        
        for g, start, end in HD_GATE_WHEEL:
            if g == 25:  # Skip, handled above
                continue
            if start <= longitude < end:
                gate = g
                pos_in_gate = longitude - start
                gate_size = end - start
                break
        
        # Fallback if not found (shouldn't happen)
        if gate is None:
            gate = 1
            pos_in_gate = 0
            gate_size = 5.625
    
    # Calculate line (1-6) within gate
    # Each gate has 6 lines, evenly distributed
    line = int((pos_in_gate / gate_size) * 6) + 1
    if line > 6:
        line = 6
    if line < 1:
        line = 1
    
    return {
        'gate': gate,
        'line': line,
        'formatted': f"{gate}.{line}"
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
    
    # Get all gates (gate numbers only)
    personality_gates = [personality_data[p]['gate']['gate'] for p in hd_planets]
    design_gates = [design_data[p]['gate']['gate'] for p in hd_planets]
    all_gates = set(personality_gates + design_gates)
    
    # NEW CORRECT LOGIC: Calculate channels first, then centers
    # A channel is defined ONLY if BOTH gates are present
    defined_channels = get_defined_channels(all_gates)
    
    # A center is defined ONLY if it has at least one FULL channel
    defined_centers = get_defined_centers(defined_channels)
    
    # Determine type based on defined centers and channels
    hd_type = determine_type(defined_centers, defined_channels)
    
    # Determine definition (None, Single, Split, etc.)
    definition = determine_definition(defined_channels, defined_centers)
    
    # Determine authority based on type and defined centers
    authority = determine_authority(hd_type, defined_centers)
    
    # Calculate Profile: personality Sun line / design Sun line
    personality_sun_line = personality_data['Sun']['gate']['line']
    design_sun_line = design_data['Sun']['gate']['line']
    profile = calculate_profile(personality_sun_line, design_sun_line)
    
    # Calculate Incarnation Cross with proper naming
    p_sun_gate = personality_data['Sun']['gate']['gate']
    p_earth_gate = personality_data['Earth']['gate']['gate']
    d_sun_gate = design_data['Sun']['gate']['gate']
    d_earth_gate = design_data['Earth']['gate']['gate']
    
    # Get proper cross name (e.g., "RAX Migration" instead of "Right Angle Cross of 37/40")
    incarnation_cross = get_incarnation_cross_name(p_sun_gate, personality_sun_line)
    
    # Format channels for output
    defined_channels_formatted = [
        {"gate1": g1, "gate2": g2, "centers": [c1, c2]} 
        for g1, g2, c1, c2 in defined_channels
    ]
    
    # =========================================================================
    # INTERPRETATION BOUNDARY - DO NOT CROSS
    # =========================================================================
    # This payload contains DETERMINISTIC FACTS only.
    # - Type, Profile, Authority (classifications)
    # - Gates, Channels, Centers (structural data)
    # - Design date calculations
    #
    # This layer must NEVER include:
    # - Personality descriptions ("you are...")
    # - Life advice or strategies explained
    # - Predictions about relationships or career
    # - Value judgments about types
    #
    # Interpretation and narrative generation must occur DOWNSTREAM
    # in a separate layer (e.g., AI prompt assembly, UI copy).
    # =========================================================================
    
    return {
        'type': hd_type,
        'definition': definition,
        'authority': authority,
        'profile': profile,
        'incarnation_cross': incarnation_cross,
        'personality': personality_data,
        'design': design_data,
        'defined_centers': defined_centers,
        'defined_channels': defined_channels_formatted,
        'all_gates': list(all_gates),
        'personality_gates': personality_gates,
        'design_gates': design_gates,
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
# Deployment: 20260204_080831 - Incarnation cross naming fix
