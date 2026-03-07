#!/usr/bin/env python
"""
Human Design Debug Script
=========================
Non-production debug tool for Human Design computation verification.

Usage:
  python -m backend.audits.hd_debug_compute [birth_date] [birth_time] [utc_offset] [lat] [lon]

Examples:
  # Use default test case (Jay)
  python -m backend.audits.hd_debug_compute
  
  # Custom birth data
  python -m backend.audits.hd_debug_compute 1981-10-12 18:16 +8 1.3521 103.8198

Output includes:
  - birth_utc
  - design_utc
  - All planets with tropical/sidereal longitude, gate, line
  - profile, type, authority, definition
  - channels, centers
  - computation versions
"""

import sys
import json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '/app/backend')

from calculations.astrology import get_full_natal_chart, SVP_DEGREES, J2000_EPOCH
from calculations.human_design import get_human_design_chart, longitude_to_gate


HD_PLANETS = [
    'Sun', 'Earth', 'Moon', 'Mercury', 'Venus', 'Mars',
    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
    'North Node', 'South Node'
]


def debug_hd_compute(
    birth_date: str = "1981-10-12",
    birth_time: str = "18:16",
    utc_offset_str: str = "+8",
    lat: float = 1.3521,
    lon: float = 103.8198
) -> dict:
    """
    Debug Human Design computation with full output.
    
    Returns:
        Dict with all debug data
    """
    # Parse input
    dt_str = f"{birth_date} {birth_time}"
    birth_local = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    
    # Parse UTC offset (e.g., "+8", "-5.5", "+7:30")
    if ':' in utc_offset_str:
        sign = 1 if utc_offset_str[0] != '-' else -1
        parts = utc_offset_str.lstrip('+-').split(':')
        utc_offset = sign * (int(parts[0]) + int(parts[1]) / 60)
    else:
        utc_offset = float(utc_offset_str)
    
    # Calculate UTC
    offset = timedelta(hours=utc_offset)
    birth_utc = (birth_local - offset).replace(tzinfo=timezone.utc)
    
    # Get charts
    astro_chart = get_full_natal_chart(birth_utc, lat, lon)
    hd_chart = get_human_design_chart(birth_utc, lat, lon)
    
    # Build planet debug data
    planets_debug = []
    for planet in HD_PLANETS:
        p_data = astro_chart['planets'].get(planet, {})
        if p_data:
            sidereal_lon = p_data.get('longitude', 0)
            tropical_lon = p_data.get('tropical_longitude', 0)
            gate_info = longitude_to_gate(sidereal_lon)
            planets_debug.append({
                'planet': planet,
                'tropical_longitude': round(tropical_lon, 4),
                'sidereal_longitude': round(sidereal_lon, 4),
                'gate': gate_info['gate'],
                'line': gate_info['line'],
            })
    
    # Build result
    result = {
        "input": {
            "birth_local": birth_local.isoformat(),
            "utc_offset": utc_offset,
            "lat": lat,
            "lon": lon,
        },
        "computed": {
            "birth_utc": birth_utc.isoformat(),
            "design_utc": hd_chart.get('design_datetime_utc_iso', ''),
        },
        "planets": planets_debug,
        "human_design": {
            "type": hd_chart.get('type'),
            "profile": hd_chart.get('profile'),
            "authority": hd_chart.get('authority'),
            "definition": hd_chart.get('definition'),
            "strategy": hd_chart.get('strategy'),
        },
        "channels": [f"{ch['gate1']}-{ch['gate2']}" for ch in hd_chart.get('defined_channels', [])],
        "defined_centers": hd_chart.get('defined_centers', []),
        "undefined_centers": hd_chart.get('undefined_centers', []),
        "incarnation_cross": hd_chart.get('incarnation_cross', {}),
        "gates": {
            "personality": hd_chart.get('personality_gates', []),
            "design": hd_chart.get('design_gates', []),
        },
        "versions": {
            "computation_version": hd_chart.get('computation_version'),
            "astronomy_version": hd_chart.get('astronomy_version'),
            "human_design_version": hd_chart.get('human_design_version'),
        },
        "sidereal_config": {
            "svp_degrees": SVP_DEGREES,
            "j2000_epoch": J2000_EPOCH,
        }
    }
    
    return result


def print_debug_report(result: dict):
    """Print formatted debug report."""
    print("=" * 80)
    print("HUMAN DESIGN DEBUG COMPUTE")
    print("=" * 80)
    print()
    
    # Input
    print("INPUT:")
    inp = result['input']
    print(f"  Birth (local):  {inp['birth_local']}")
    print(f"  UTC Offset:     {inp['utc_offset']}")
    print(f"  Location:       {inp['lat']}, {inp['lon']}")
    print()
    
    # Computed times
    print("COMPUTED TIMES:")
    comp = result['computed']
    print(f"  Birth (UTC):    {comp['birth_utc']}")
    print(f"  Design (UTC):   {comp['design_utc']}")
    print()
    
    # Versions
    print("VERSION METADATA:")
    v = result['versions']
    print(f"  computation_version:   {v.get('computation_version', 'N/A')}")
    print(f"  astronomy_version:     {v.get('astronomy_version', 'N/A')}")
    print(f"  human_design_version:  {v.get('human_design_version', 'N/A')}")
    print()
    
    # Sidereal config
    print("SIDEREAL CONFIG:")
    sc = result['sidereal_config']
    print(f"  SVP Degrees:    {sc.get('svp_degrees', 'N/A')}°")
    print(f"  J2000 Epoch:    {sc.get('j2000_epoch', 'N/A')}")
    print()
    
    # Planets table
    print("PLANETS:")
    print("-" * 70)
    print(f"{'Planet':12} {'Tropical°':>12} {'Sidereal°':>12} {'Gate':>8} {'Line':>6}")
    print("-" * 70)
    for p in result['planets']:
        print(f"{p['planet']:12} {p['tropical_longitude']:>12.4f} {p['sidereal_longitude']:>12.4f} {p['gate']:>8} {p['line']:>6}")
    print("-" * 70)
    print()
    
    # Human Design
    print("HUMAN DESIGN:")
    hd = result['human_design']
    print(f"  Type:       {hd['type']}")
    print(f"  Profile:    {hd['profile']}")
    print(f"  Authority:  {hd['authority']}")
    print(f"  Definition: {hd['definition']}")
    print(f"  Strategy:   {hd['strategy']}")
    print()
    
    # Centers
    print("CENTERS:")
    print(f"  Defined ({len(result['defined_centers'])}):   {', '.join(result['defined_centers']) or 'None'}")
    print(f"  Undefined ({len(result['undefined_centers'])}): {', '.join(result['undefined_centers']) or 'None'}")
    print()
    
    # Channels
    print("CHANNELS:")
    if result['channels']:
        for ch in result['channels']:
            print(f"  {ch}")
    else:
        print("  None")
    print()
    
    # Gates
    print("GATES:")
    print(f"  Personality: {result['gates']['personality']}")
    print(f"  Design:      {result['gates']['design']}")
    print()
    
    # Incarnation Cross
    print("INCARNATION CROSS:")
    ic = result.get('incarnation_cross', {})
    print(f"  Name:  {ic.get('name', 'N/A')}")
    print(f"  Gates: {ic.get('gates', 'N/A')}")
    print()
    
    print("=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Use default test case (Jay)
        result = debug_hd_compute()
    elif len(sys.argv) == 6:
        # Custom birth data
        result = debug_hd_compute(
            birth_date=sys.argv[1],
            birth_time=sys.argv[2],
            utc_offset_str=sys.argv[3],
            lat=float(sys.argv[4]),
            lon=float(sys.argv[5])
        )
    else:
        print("Usage: python -m backend.audits.hd_debug_compute [birth_date] [birth_time] [utc_offset] [lat] [lon]")
        print("Example: python -m backend.audits.hd_debug_compute 1981-10-12 18:16 +8 1.3521 103.8198")
        sys.exit(1)
    
    print_debug_report(result)
    
    # Also output JSON for programmatic use
    print("\n--- JSON OUTPUT ---")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
