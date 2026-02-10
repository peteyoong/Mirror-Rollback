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

import json
from datetime import datetime, timezone, timedelta
from calculations.human_design import get_human_design_chart, calculate_design_date

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
    
    print("=" * 90)
    print("HUMAN DESIGN GENETIC MATRIX PARITY VERIFICATION")
    print("=" * 90)
    print(f"\nSystem Settings:")
    print(f"  - Zodiac: True Sidereal")
    print(f"  - SVP: {SIDEREAL_SETTINGS['svp_degrees']}°")
    print(f"  - Yearly Increment: {SIDEREAL_SETTINGS['yearly_increment']}")
    print(f"  - HD Mode: Midpoint (88° solar arc)")
    print()
    
    for user in TEST_USERS:
        print("=" * 90)
        print(f"USER: {user['name']}")
        print("=" * 90)
        print(f"Birth (Local): {user['birth_local']}")
        print(f"Birth (UTC):   {user['birth_utc'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Location:      {user['place']} ({user['lat']}, {user['lon']})")
        print()
        
        try:
            # Compute HD
            hd = get_human_design_chart(
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
            
            # =====================================================================
            # SECTION 1: INCARNATION CROSS (Priority 1)
            # =====================================================================
            print("┌" + "─" * 88 + "┐")
            print("│ 1. INCARNATION CROSS" + " " * 67 + "│")
            print("├" + "─" * 88 + "┤")
            
            ic = hd.get('incarnation_cross', {})
            print(f"│  Type:            {ic.get('angle_full', 'N/A'):68} │")
            print(f"│  Angle:           {ic.get('angle', 'N/A'):68} │")
            print(f"│  Label:           {ic.get('internal_label', ic.get('name', 'N/A')):68} │")
            print(f"│  Gates Key:       {ic.get('gates_key', 'N/A'):68} │")
            
            # Gate/Line breakdown
            p_sun_g = ic.get('personality_sun', '?')
            p_sun_l = ic.get('personality_sun_line', '?')
            p_earth_g = ic.get('personality_earth', '?')
            p_earth_l = ic.get('personality_earth_line', '?')
            d_sun_g = ic.get('design_sun', '?')
            d_sun_l = ic.get('design_sun_line', '?')
            d_earth_g = ic.get('design_earth', '?')
            d_earth_l = ic.get('design_earth_line', '?')
            
            gates_detail = f"P-Sun {p_sun_g}.{p_sun_l}, P-Earth {p_earth_g}.{p_earth_l} | D-Sun {d_sun_g}.{d_sun_l}, D-Earth {d_earth_g}.{d_earth_l}"
            print(f"│  Gates Detail:    {gates_detail:68} │")
            print("└" + "─" * 88 + "┘")
            print()
            
            # =====================================================================
            # SECTION 2: PROFILE / TYPE / AUTHORITY (Priority 2)
            # =====================================================================
            print("┌" + "─" * 88 + "┐")
            print("│ 2. PROFILE / TYPE / AUTHORITY" + " " * 58 + "│")
            print("├" + "─" * 88 + "┤")
            print(f"│  Profile:         {hd.get('profile', 'N/A'):68} │")
            print(f"│  Type:            {hd.get('type', 'N/A'):68} │")
            print(f"│  Authority:       {hd.get('authority', 'N/A'):68} │")
            print(f"│  Strategy:        {hd.get('strategy', 'N/A'):68} │")
            print(f"│  Definition:      {hd.get('definition', 'N/A'):68} │")
            print("└" + "─" * 88 + "┘")
            print()
            
            # =====================================================================
            # SECTION 3: DEFINED CENTERS & CHANNELS (Priority 3)
            # =====================================================================
            print("┌" + "─" * 88 + "┐")
            print("│ 3. DEFINED CENTERS & CHANNELS" + " " * 58 + "│")
            print("├" + "─" * 88 + "┤")
            
            defined = hd.get('defined_centers', [])
            undefined = hd.get('undefined_centers', [])
            defined_str = ', '.join(defined) if defined else 'None (Reflector)'
            undefined_str = ', '.join(undefined) if undefined else 'All Defined'
            
            # Wrap long center lists
            if len(defined_str) > 66:
                defined_str = defined_str[:63] + "..."
            if len(undefined_str) > 66:
                undefined_str = undefined_str[:63] + "..."
                
            print(f"│  Defined:         {defined_str:68} │")
            print(f"│  Undefined:       {undefined_str:68} │")
            print("│" + " " * 88 + "│")
            
            channels = hd.get('defined_channels', [])
            if channels:
                print(f"│  Channels ({len(channels)}):" + " " * 74 + "│")
                for ch in channels:
                    g1 = ch.get('gate1', '?')
                    g2 = ch.get('gate2', '?')
                    centers = ch.get('centers', ['?', '?'])
                    ch_str = f"    {g1}-{g2} ({centers[0]} ↔ {centers[1]})"
                    print(f"│{ch_str:88}│")
            else:
                print(f"│  Channels:        None" + " " * 65 + "│")
            print("└" + "─" * 88 + "┘")
            print()
            
            # =====================================================================
            # SECTION 4: PLANETARY ACTIVATIONS TABLE (Priority 4)
            # =====================================================================
            print("┌" + "─" * 88 + "┐")
            print("│ 4. PLANETARY ACTIVATIONS TABLE" + " " * 57 + "│")
            print("├" + "─" * 88 + "┤")
            print("│  Planet          │ Personality (Birth)  │ Design (88° Prior)   │ Notes          │")
            print("│                  │ Gate.Line  (Lon°)    │ Gate.Line  (Lon°)    │                │")
            print("├──────────────────┼──────────────────────┼──────────────────────┼────────────────┤")
            
            p_data = hd.get('personality', {})
            d_data = hd.get('design', {})
            
            # Ordered planet list per user request
            planet_order = [
                'Sun', 'Earth', 
                'North Node', 'South Node',
                'Moon',
                'Mercury', 'Venus', 'Mars', 
                'Jupiter', 'Saturn',
                'Uranus', 'Neptune', 'Pluto'
            ]
            
            for planet in planet_order:
                # Personality
                p_info = p_data.get(planet, {})
                p_gate_info = p_info.get('gate', {})
                p_pos_info = p_info.get('position', {})
                p_gate = p_gate_info.get('gate', '?')
                p_line = p_gate_info.get('line', '?')
                p_lon = p_pos_info.get('longitude', 0)
                
                # Design
                d_info = d_data.get(planet, {})
                d_gate_info = d_info.get('gate', {})
                d_pos_info = d_info.get('position', {})
                d_gate = d_gate_info.get('gate', '?')
                d_line = d_gate_info.get('line', '?')
                d_lon = d_pos_info.get('longitude', 0)
                
                # Format columns
                p_col = f"{p_gate:>2}.{p_line}  ({p_lon:>7.2f}°)"
                d_col = f"{d_gate:>2}.{d_line}  ({d_lon:>7.2f}°)"
                
                # Notes column - mark important cross gates
                notes = ""
                if planet in ['Sun', 'Earth']:
                    notes = "← Cross Gate"
                
                print(f"│  {planet:15} │ {p_col:20} │ {d_col:20} │ {notes:14} │")
            
            print("└──────────────────┴──────────────────────┴──────────────────────┴────────────────┘")
            print()
            
            # =====================================================================
            # SECTION 5: DESIGN DATE CALCULATION DEBUG (Priority 5)
            # =====================================================================
            print("┌" + "─" * 88 + "┐")
            print("│ 5. DESIGN DATE CALCULATION (88° Solar Arc)" + " " * 44 + "│")
            print("├" + "─" * 88 + "┤")
            print(f"│  Birth Sun (Sidereal):   {design_debug.get('birth_sun_sidereal', 0):>10.4f}°" + " " * 50 + "│")
            print(f"│  Target Sun (88° back):  {design_debug.get('target_sun_sidereal', 0):>10.4f}°" + " " * 50 + "│")
            print(f"│  Design Sun (Computed):  {design_debug.get('design_sun_sidereal', 0):>10.4f}°" + " " * 50 + "│")
            print(f"│  Design DateTime (UTC):  {design_dt.strftime('%Y-%m-%d %H:%M:%S'):>19}" + " " * 43 + "│")
            print(f"│  Days Before Birth:      {(user['birth_utc'] - design_dt).days:>10} days" + " " * 42 + "│")
            print(f"│  Converged:              {str(design_debug.get('converged', False)):>10}" + " " * 46 + "│")
            print("└" + "─" * 88 + "┘")
            print()
            
            # =====================================================================
            # JSON OUTPUT FOR MACHINE COMPARISON
            # =====================================================================
            print("┌" + "─" * 88 + "┐")
            print("│ JSON SUMMARY (for line-by-line comparison)" + " " * 44 + "│")
            print("└" + "─" * 88 + "┘")
            
            json_summary = {
                "user": user['name'],
                "birth_utc": user['birth_utc'].isoformat(),
                "incarnation_cross": {
                    "type": ic.get('angle_full'),
                    "angle": ic.get('angle'),
                    "label": ic.get('internal_label'),
                    "gates": {
                        "p_sun": f"{p_sun_g}.{p_sun_l}",
                        "p_earth": f"{p_earth_g}.{p_earth_l}",
                        "d_sun": f"{d_sun_g}.{d_sun_l}",
                        "d_earth": f"{d_earth_g}.{d_earth_l}"
                    }
                },
                "profile": hd.get('profile'),
                "type": hd.get('type'),
                "authority": hd.get('authority'),
                "definition": hd.get('definition'),
                "defined_centers": defined,
                "defined_channels": [f"{ch['gate1']}-{ch['gate2']}" for ch in channels],
                "planetary_activations": {
                    "personality": {p: f"{p_data.get(p, {}).get('gate', {}).get('gate', '?')}.{p_data.get(p, {}).get('gate', {}).get('line', '?')}" for p in planet_order},
                    "design": {p: f"{d_data.get(p, {}).get('gate', {}).get('gate', '?')}.{d_data.get(p, {}).get('gate', {}).get('line', '?')}" for p in planet_order}
                },
                "design_date_utc": design_dt.isoformat()
            }
            
            print(json.dumps(json_summary, indent=2))
            print()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n")

if __name__ == "__main__":
    run_verification()
