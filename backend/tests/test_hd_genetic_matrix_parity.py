#!/usr/bin/env python3
"""
Human Design Genetic Matrix Parity Test
========================================
Verifies our HD calculations match Genetic Matrix (True Sidereal-M / Midpoint)

System Settings (Must Match):
- Zodiac: True Sidereal
- Ayanamsa: User-defined (F)
- Sidereal Vernal Point: 31.2836°
- Yearly Increment: 0.00
- Nodes: True Nodes
- House system: Equal
- HD Mode: Midpoint (M)
"""

import sys
sys.path.insert(0, '/app/backend')

from datetime import datetime, timezone, timedelta
from calculations.human_design import compute_human_design, calculate_design_date
from calculations.astrology import get_full_natal_chart

# Test Users
TEST_USERS = [
    {
        "name": "Nattalia C",
        "birth_local": "04 May 1982, 17:00 (UTC+07)",
        "birth_utc": datetime(1982, 5, 4, 10, 0, tzinfo=timezone.utc),
        "lat": -7.2575,   # Surabaya, Indonesia
        "lon": 112.7521,
        "place": "Surabaya, Indonesia"
    },
    {
        "name": "Pete Y",
        "birth_local": "01 Apr 1968, 01:25 (UTC+07:30)",
        "birth_utc": datetime(1968, 3, 31, 17, 55, tzinfo=timezone.utc),
        "lat": 3.1073,    # Petaling Jaya, Malaysia
        "lon": 101.6067,
        "place": "Petaling Jaya, Malaysia"
    },
    {
        "name": "Melisa T",
        "birth_local": "13 Jul 1981, 07:25 (UTC+07:30)",
        "birth_utc": datetime(1981, 7, 12, 23, 55, tzinfo=timezone.utc),
        "lat": 2.1896,    # Melaka, Malaysia
        "lon": 102.2501,
        "place": "Melaka, Malaysia"
    }
]

# Sidereal settings matching Genetic Matrix
SIDEREAL_SETTINGS = {
    "mode": "true_sidereal_user_defined",
    "svp_degrees": 31.2836,
    "reference_year": 2000,
    "yearly_increment": 0.0
}

def format_gate_line(gate: int, line: int) -> str:
    """Format gate.line for display"""
    return f"{gate}.{line}"

def run_verification():
    """Run HD verification for all test users"""
    
    print("=" * 80)
    print("HUMAN DESIGN GENETIC MATRIX PARITY VERIFICATION")
    print("=" * 80)
    print(f"\nSystem Settings:")
    print(f"  - Zodiac: True Sidereal")
    print(f"  - SVP: {SIDEREAL_SETTINGS['svp_degrees']}°")
    print(f"  - Yearly Increment: {SIDEREAL_SETTINGS['yearly_increment']}")
    print(f"  - HD Mode: Midpoint (88° solar arc)")
    print()
    
    for user in TEST_USERS:
        print("=" * 80)
        print(f"USER: {user['name']}")
        print("=" * 80)
        print(f"Birth (Local): {user['birth_local']}")
        print(f"Birth (UTC):   {user['birth_utc'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Location:      {user['place']} ({user['lat']}, {user['lon']})")
        print()
        
        try:
            # Compute HD
            hd = compute_human_design(
                user['birth_utc'],
                user['lat'],
                user['lon'],
                SIDEREAL_SETTINGS
            )
            
            # Get design date details
            design_dt, design_offset, design_debug = calculate_design_date(
                user['birth_utc'],
                user['lat'],
                user['lon'],
                SIDEREAL_SETTINGS['svp_degrees']
            )
            
            print("DESIGN DATE CALCULATION (88° Solar Arc)")
            print("-" * 40)
            print(f"  Birth Sun (Sidereal):   {design_debug.get('birth_sun_sidereal', 'N/A'):.4f}°")
            print(f"  Target Sun (88° back):  {design_debug.get('target_sun_sidereal', 'N/A'):.4f}°")
            print(f"  Design Sun (Computed):  {design_debug.get('design_sun_sidereal', 'N/A'):.4f}°")
            print(f"  Design DateTime (UTC):  {design_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Days Before Birth:      {(user['birth_utc'] - design_dt).days} days")
            print()
            
            # Print Type, Authority, Profile, Definition
            print("TYPE / AUTHORITY / PROFILE / DEFINITION")
            print("-" * 40)
            print(f"  Type:        {hd.get('type', 'N/A')}")
            print(f"  Authority:   {hd.get('authority', 'N/A')}")
            print(f"  Profile:     {hd.get('profile', 'N/A')}")
            print(f"  Definition:  {hd.get('definition_type', 'N/A')}")
            print()
            
            # Incarnation Cross
            ic = hd.get('incarnation_cross_canonical', {})
            print("INCARNATION CROSS")
            print("-" * 40)
            print(f"  Name:   {ic.get('internal_label', 'N/A')}")
            print(f"  Angle:  {ic.get('angle_full', ic.get('angle', 'N/A'))}")
            print(f"  Gates:  Sun {ic.get('personality_sun_gate', '?')}, Earth {ic.get('personality_earth_gate', '?')}, ")
            print(f"          Sun {ic.get('design_sun_gate', '?')} (D), Earth {ic.get('design_earth_gate', '?')} (D)")
            print()
            
            # Defined Centers
            print("DEFINED CENTERS")
            print("-" * 40)
            defined = hd.get('defined_centers', [])
            print(f"  {', '.join(defined) if defined else 'None'}")
            print()
            
            # Channels
            print("CHANNELS")
            print("-" * 40)
            channels = hd.get('channels', [])
            for ch in channels:
                print(f"  {ch.get('gate1')}-{ch.get('gate2')}: {ch.get('name', 'Unknown')}")
            if not channels:
                print("  None")
            print()
            
            # All 13 Planet Activations - Personality
            print("PERSONALITY ACTIVATIONS (Birth/Conscious)")
            print("-" * 40)
            p_act = hd.get('personality_activations', {})
            planet_order = ['sun', 'earth', 'moon', 'north_node', 'south_node', 
                          'mercury', 'venus', 'mars', 'jupiter', 'saturn', 
                          'uranus', 'neptune', 'pluto']
            for planet in planet_order:
                act = p_act.get(planet, {})
                gate = act.get('gate', '?')
                line = act.get('line', '?')
                lon = act.get('longitude', 0)
                print(f"  {planet.upper():12} {gate:2}.{line}  ({lon:.2f}°)")
            print()
            
            # All 13 Planet Activations - Design
            print("DESIGN ACTIVATIONS (88° Prior/Unconscious)")
            print("-" * 40)
            d_act = hd.get('design_activations', {})
            for planet in planet_order:
                act = d_act.get(planet, {})
                gate = act.get('gate', '?')
                line = act.get('line', '?')
                lon = act.get('longitude', 0)
                print(f"  {planet.upper():12} {gate:2}.{line}  ({lon:.2f}°)")
            print()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()

if __name__ == "__main__":
    run_verification()
