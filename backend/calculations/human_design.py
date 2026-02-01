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

def calculate_design_date(birth_datetime: datetime) -> datetime:
    """Calculate Design date (approximately 88 days before birth)
    More precisely, it's when the Sun was at the same position ~88 degrees earlier
    For V1, using 88 days as approximation
    """
    return birth_datetime - timedelta(days=88)

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

def get_human_design_chart(birth_datetime: datetime, lat: float, lon: float) -> Dict:
    """Calculate complete Human Design bodygraph"""
    # Get Personality (Conscious) chart at birth
    personality_chart = get_full_natal_chart(birth_datetime, lat, lon)
    
    # Get Design (Unconscious) chart 88 days before birth
    design_datetime = calculate_design_date(birth_datetime)
    design_chart = get_full_natal_chart(design_datetime, lat, lon)
    
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
