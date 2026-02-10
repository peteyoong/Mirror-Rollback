#!/usr/bin/env python3
"""
Human Design Parity Output Generator
=====================================
Generates clean, comparable output for 3 test users to compare with Genetic Matrix.

Output format per user:
1) Incarnation Cross (type: right/left/juxtaposition, canonical label, 4 gates/lines)
2) Profile + Type + Authority
3) Defined Centers (and channels)
4) Planetary activations table (13 planets × 2 sides)
5) Variables (reserved for future)

Run: python scripts/hd_parity_output.py
"""

import sys
sys.path.insert(0, '/app/backend')

import json
from datetime import datetime, timezone
from calculations.human_design import get_human_design_chart

# =============================================================================
# CONFIGURATION
# =============================================================================

SIDEREAL_SETTINGS = {
    "mode": "true_sidereal_user_defined",
    "svp_degrees": 31.2836,
    "reference_year": 2000,
    "yearly_increment": 0.0,
    "nodes": "true_nodes",
    "house_system": "equal",
    "hd_mode": "midpoint"
}

TEST_USERS = [
    {
        "name": "Nattalia C",
        "birth_utc": datetime(1982, 5, 4, 10, 0, tzinfo=timezone.utc),
        "lat": -7.0959,
        "lon": 112.348,
        "place": "Surabaya, Indonesia"
    },
    {
        "name": "Pete Y",
        "birth_utc": datetime(1968, 3, 31, 17, 55, tzinfo=timezone.utc),
        "lat": 3.1073,
        "lon": 101.607,
        "place": "Petaling Jaya, Malaysia"
    },
    {
        "name": "Melisa T",
        "birth_utc": datetime(1981, 7, 12, 23, 55, tzinfo=timezone.utc),
        "lat": 2.1889,
        "lon": 102.251,
        "place": "Melaka, Malaysia"
    }
]

PLANET_ORDER = [
    'Sun', 'Earth', 'North Node', 'South Node', 'Moon',
    'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
    'Uranus', 'Neptune', 'Pluto'
]


def format_parity_output(user: dict, result: dict) -> dict:
    """Format HD result into clean parity output structure"""
    
    # 1) Incarnation Cross
    cross = result['incarnation_cross']
    incarnation_cross = {
        "angle_code": cross['angle'],  # RAX / LAX / JXP
        "angle_full": cross['angle_full'],  # Right Angle Cross / Left Angle Cross / Juxtaposition Cross
        "cross_name": cross['internal_name'],  # e.g., "Tension", "Migration"
        "canonical_label": cross['internal_label'],  # e.g., "RAX Tension"
        "gates_key": cross['gates_key'],  # e.g., "21/48|38/39"
        "canonical_key": cross['canonical_key'],  # e.g., "21.4/48.4|38.6/39.6"
        "4_gates_lines": {
            "personality_sun": f"{cross['personality_sun']}.{cross['personality_sun_line']}",
            "personality_earth": f"{cross['personality_earth']}.{cross['personality_earth_line']}",
            "design_sun": f"{cross['design_sun']}.{cross['design_sun_line']}",
            "design_earth": f"{cross['design_earth']}.{cross['design_earth_line']}"
        },
        "angle_source": cross['angle_source'],
        "angle_proof": cross['angle_proof']
    }
    
    # 2) Profile + Type + Authority
    core = {
        "profile": result['profile'],
        "type": result['type'],
        "authority": result['authority'],
        "strategy": result['strategy'],
        "definition": result['definition']
    }
    
    # 3) Defined Centers and Channels
    centers_channels = {
        "defined_centers": sorted(result['defined_centers']),
        "undefined_centers": sorted(result['undefined_centers']),
        "defined_channels": [f"{ch['gate1']}-{ch['gate2']}" for ch in result['defined_channels']],
        "channel_count": len(result['defined_channels'])
    }
    
    # 4) Planetary Activations Table
    activations = {
        "personality": {},
        "design": {}
    }
    
    for planet in PLANET_ORDER:
        # Personality
        p_data = result['personality'].get(planet, {})
        p_gate = p_data.get('gate', {})
        activations['personality'][planet] = {
            "gate": p_gate.get('gate'),
            "line": p_gate.get('line'),
            "gate_line": f"{p_gate.get('gate')}.{p_gate.get('line')}"
        }
        
        # Design
        d_data = result['design'].get(planet, {})
        d_gate = d_data.get('gate', {})
        activations['design'][planet] = {
            "gate": d_gate.get('gate'),
            "line": d_gate.get('line'),
            "gate_line": f"{d_gate.get('gate')}.{d_gate.get('line')}"
        }
    
    # 5) Variables (reserved)
    variables = result.get('variables', {})
    
    return {
        "user": {
            "name": user['name'],
            "birth_utc": user['birth_utc'].isoformat(),
            "lat": user['lat'],
            "lon": user['lon'],
            "place": user['place']
        },
        "settings": {
            "svp_degrees": SIDEREAL_SETTINGS['svp_degrees'],
            "mode": SIDEREAL_SETTINGS['mode']
        },
        "1_incarnation_cross": incarnation_cross,
        "2_core_attributes": core,
        "3_centers_channels": centers_channels,
        "4_planetary_activations": activations,
        "5_variables": variables,
        "design_datetime_utc": result.get('design_datetime_utc_iso'),
        "computation_version": result.get('computation_version')
    }


def print_pretty_table(user_output: dict):
    """Print a pretty-formatted table for easy comparison"""
    
    print("\n" + "=" * 80)
    print(f"USER: {user_output['user']['name']}")
    print(f"Birth UTC: {user_output['user']['birth_utc']}")
    print(f"Location: {user_output['user']['place']} ({user_output['user']['lat']}, {user_output['user']['lon']})")
    print("=" * 80)
    
    # Section 1: Incarnation Cross
    cross = user_output['1_incarnation_cross']
    print("\n┌─ 1) INCARNATION CROSS ─────────────────────────────────────────────────────────┐")
    print(f"│  Angle:           {cross['angle_code']} ({cross['angle_full']})")
    print(f"│  Cross Name:      {cross['cross_name']}")
    print(f"│  Canonical Label: {cross['canonical_label']}")
    print(f"│  Gates Key:       {cross['gates_key']}")
    print(f"│  Canonical Key:   {cross['canonical_key']}")
    print(f"│  ┌───────────────────────────────────────────────────────────────────────────┐")
    print(f"│  │  Personality Sun:   {cross['4_gates_lines']['personality_sun']:<8}  Design Sun:   {cross['4_gates_lines']['design_sun']:<8}")
    print(f"│  │  Personality Earth: {cross['4_gates_lines']['personality_earth']:<8}  Design Earth: {cross['4_gates_lines']['design_earth']:<8}")
    print(f"│  └───────────────────────────────────────────────────────────────────────────┘")
    print(f"│  Angle Source: {cross['angle_source']}")
    print(f"└────────────────────────────────────────────────────────────────────────────────┘")
    
    # Section 2: Core Attributes
    core = user_output['2_core_attributes']
    print("\n┌─ 2) PROFILE + TYPE + AUTHORITY ───────────────────────────────────────────────┐")
    print(f"│  Profile:    {core['profile']}")
    print(f"│  Type:       {core['type']}")
    print(f"│  Authority:  {core['authority']}")
    print(f"│  Strategy:   {core['strategy']}")
    print(f"│  Definition: {core['definition']}")
    print(f"└────────────────────────────────────────────────────────────────────────────────┘")
    
    # Section 3: Centers and Channels
    cc = user_output['3_centers_channels']
    print("\n┌─ 3) DEFINED CENTERS + CHANNELS ───────────────────────────────────────────────┐")
    print(f"│  Defined Centers ({len(cc['defined_centers'])}):  {', '.join(cc['defined_centers']) or 'None'}")
    print(f"│  Undefined Centers ({len(cc['undefined_centers'])}): {', '.join(cc['undefined_centers']) or 'None'}")
    print(f"│  Channels ({cc['channel_count']}): {', '.join(cc['defined_channels']) or 'None'}")
    print(f"└────────────────────────────────────────────────────────────────────────────────┘")
    
    # Section 4: Planetary Activations
    print("\n┌─ 4) PLANETARY ACTIVATIONS TABLE ──────────────────────────────────────────────┐")
    print(f"│  {'Planet':<12} │ {'Personality':<12} │ {'Design':<12} │")
    print(f"│  {'─'*12}─┼─{'─'*12}─┼─{'─'*12}─┤")
    
    activations = user_output['4_planetary_activations']
    for planet in PLANET_ORDER:
        p_val = activations['personality'][planet]['gate_line']
        d_val = activations['design'][planet]['gate_line']
        print(f"│  {planet:<12} │ {p_val:<12} │ {d_val:<12} │")
    
    print(f"└────────────────────────────────────────────────────────────────────────────────┘")
    
    # Section 5: Variables (if any)
    variables = user_output['5_variables']
    if variables:
        print("\n┌─ 5) VARIABLES ─────────────────────────────────────────────────────────────────┐")
        for k, v in variables.items():
            print(f"│  {k}: {v}")
        print(f"└────────────────────────────────────────────────────────────────────────────────┘")
    else:
        print("\n┌─ 5) VARIABLES ─────────────────────────────────────────────────────────────────┐")
        print(f"│  (Not computed - reserved for future implementation)")
        print(f"└────────────────────────────────────────────────────────────────────────────────┘")
    
    # Metadata
    print(f"\nDesign DateTime UTC: {user_output['design_datetime_utc']}")
    print(f"Computation Version: {user_output['computation_version']}")


def main():
    """Run parity output for all 3 test users"""
    
    print("\n" + "█" * 80)
    print("HUMAN DESIGN PARITY OUTPUT - TRUE SIDEREAL-M (SVP 31.2836°)")
    print("█" * 80)
    print(f"\nSettings: {json.dumps(SIDEREAL_SETTINGS, indent=2)}")
    
    all_outputs = []
    
    for user in TEST_USERS:
        print(f"\n\n>>> Computing HD chart for {user['name']}...")
        
        try:
            result = get_human_design_chart(
                user['birth_utc'],
                user['lat'],
                user['lon'],
                SIDEREAL_SETTINGS
            )
            
            output = format_parity_output(user, result)
            all_outputs.append(output)
            
            # Print pretty table
            print_pretty_table(output)
            
        except Exception as e:
            print(f"ERROR computing chart for {user['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    # Output JSON for programmatic comparison
    print("\n\n" + "█" * 80)
    print("JSON OUTPUT (for programmatic comparison)")
    print("█" * 80)
    print(json.dumps(all_outputs, indent=2, default=str))
    
    return all_outputs


if __name__ == "__main__":
    main()
