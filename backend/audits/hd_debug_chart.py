"""
Debug output generator for Human Design chart calibration.
Run with: python -m backend.audits.hd_debug_chart
"""

from datetime import datetime, timezone, timedelta
import json
import sys
sys.path.insert(0, '/app/backend')

from calculations.astrology import get_full_natal_chart, tropical_to_sidereal, normalize_degrees
from calculations.human_design import (
    get_human_design_chart, 
    longitude_to_gate,
    calculate_design_date,
    _get_sun_sidereal
)
import swisseph as swe


# Planets for HD debug output
HD_PLANETS = [
    'Sun', 'Earth', 'Moon', 'Mercury', 'Venus', 'Mars', 
    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 
    'North Node', 'South Node'
]

# 13-sign constellation boundaries (IAU-based, approximate)
# Note: Currently NOT used in production - for reference only
CONSTELLATION_BOUNDARIES_13 = [
    ('Aries', 28.8),          # Aries ends at ~28.8°
    ('Taurus', 53.4),         # Taurus ends at ~53.4°
    ('Gemini', 90.0),         # Gemini ends at ~90°
    ('Cancer', 118.0),        # Cancer ends at ~118°
    ('Leo', 138.0),           # Leo ends at ~138°
    ('Virgo', 174.0),         # Virgo ends at ~174°
    ('Libra', 218.0),         # Libra ends at ~218°
    ('Scorpius', 241.0),      # Scorpius ends at ~241° (short!)
    ('Ophiuchus', 266.0),     # Ophiuchus ends at ~266° (the 13th sign)
    ('Sagittarius', 299.0),   # Sagittarius ends at ~299°
    ('Capricornus', 327.0),   # Capricornus ends at ~327°
    ('Aquarius', 351.6),      # Aquarius ends at ~351.6°
    ('Pisces', 360.0),        # Pisces to end
]


def get_13_sign_label(sidereal_longitude: float) -> str:
    """Get 13-sign constellation label from sidereal longitude.
    
    NOTE: This is for DEBUG/AUDIT purposes only.
    Production currently uses 12-sign zodiac.
    """
    lon = normalize_degrees(sidereal_longitude)
    for sign, end_degree in CONSTELLATION_BOUNDARIES_13:
        if lon < end_degree:
            return sign
    return 'Pisces'


def generate_hd_debug_output(
    birth_local: datetime,
    utc_offset_hours: float,
    lat: float,
    lon: float,
    name: str = "Test Subject"
) -> dict:
    """Generate comprehensive debug output for HD chart calibration.
    
    Args:
        birth_local: Local birth datetime (naive)
        utc_offset_hours: UTC offset in hours (e.g., +7.5 for +07:30)
        lat: Latitude
        lon: Longitude
        name: Name for identification
    
    Returns:
        Dict with complete debug output
    """
    # Calculate UTC
    offset = timedelta(hours=utc_offset_hours)
    birth_utc = (birth_local - offset).replace(tzinfo=timezone.utc)
    
    # Get full charts
    sidereal_settings = {
        "mode": "true_sidereal_user_defined",
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0
    }
    
    astro_chart = get_full_natal_chart(birth_utc, lat, lon, sidereal_settings)
    hd_chart = get_human_design_chart(birth_utc, lat, lon, sidereal_settings)
    
    # Extract design date
    design_utc_str = hd_chart.get('design_datetime_utc_iso', '')
    design_debug = hd_chart.get('design_solver_debug', {})
    
    # Build planet data
    planets_debug = {}
    for planet in HD_PLANETS:
        p_data = astro_chart['planets'].get(planet, {})
        
        if p_data:
            tropical_lon = p_data.get('tropical_longitude', 0)
            sidereal_lon = p_data.get('longitude', 0)
            
            # Get gate info
            gate_info = longitude_to_gate(sidereal_lon)
            
            # Get 13-sign label (for audit comparison)
            sign_13 = get_13_sign_label(sidereal_lon)
            
            planets_debug[planet] = {
                'tropical_longitude': round(tropical_lon, 4),
                'sidereal_longitude': round(sidereal_lon, 4),
                'sign_12': p_data.get('sign', 'N/A'),
                'sign_13': sign_13,
                'degree_in_sign': round(p_data.get('degree', 0), 2),
                'hd_gate': gate_info['gate'],
                'hd_line': gate_info['line'],
                'hd_formatted': gate_info['formatted'],
                'retrograde': p_data.get('retrograde', False),
            }
        else:
            planets_debug[planet] = {'error': 'Planet not found in chart'}
    
    # Build output
    output = {
        'subject': name,
        'input': {
            'birth_local': birth_local.isoformat(),
            'utc_offset': f"+{utc_offset_hours}" if utc_offset_hours >= 0 else str(utc_offset_hours),
            'coordinates': {'lat': lat, 'lon': lon},
        },
        'computed': {
            'birth_utc': birth_utc.isoformat(),
            'design_utc': design_utc_str,
            'design_solver': design_debug,
        },
        'sidereal_settings': {
            'svp_degrees': 31.2836,
            'reference_year': 2000,
            'yearly_increment': 0.0,
            'method': 'manual (tropical - SVP)',
            'note': 'NOT using SE_SIDM_USER or SEFLG_SIDEREAL',
        },
        'planets': planets_debug,
        'human_design': {
            'profile': hd_chart.get('profile'),
            'type': hd_chart.get('type'),
            'authority': hd_chart.get('authority'),
            'strategy': hd_chart.get('strategy'),
            'definition': hd_chart.get('definition'),
            'incarnation_cross': hd_chart.get('incarnation_cross'),
        },
        'centers': {
            'defined': hd_chart.get('defined_centers', []),
            'undefined': hd_chart.get('undefined_centers', []),
        },
        'channels': {
            'active': hd_chart.get('defined_channels', []),
            'count': len(hd_chart.get('defined_channels', [])),
        },
        'gates': {
            'personality': hd_chart.get('personality_gates', []),
            'design': hd_chart.get('design_gates', []),
            'all_unique': list(hd_chart.get('all_gates', [])),
        },
        'metadata': {
            'computation_version': hd_chart.get('computation_version'),
            'chart_type': hd_chart.get('chart_type'),
        },
    }
    
    return output


def print_hd_debug(output: dict):
    """Pretty print the debug output."""
    print("=" * 80)
    print(f"HUMAN DESIGN DEBUG OUTPUT - {output['subject']}")
    print("=" * 80)
    print()
    
    # Input
    print("INPUT:")
    print(f"  Birth (local):  {output['input']['birth_local']}")
    print(f"  UTC Offset:     {output['input']['utc_offset']}")
    print(f"  Coordinates:    {output['input']['coordinates']['lat']}, {output['input']['coordinates']['lon']}")
    print()
    
    # Computed times
    print("COMPUTED TIMES:")
    print(f"  Birth (UTC):    {output['computed']['birth_utc']}")
    print(f"  Design (UTC):   {output['computed']['design_utc']}")
    print()
    
    # Sidereal settings
    print("SIDEREAL SETTINGS:")
    ss = output['sidereal_settings']
    print(f"  SVP:            {ss['svp_degrees']}°")
    print(f"  Reference Year: {ss['reference_year']}")
    print(f"  Yearly Inc:     {ss['yearly_increment']}")
    print(f"  Method:         {ss['method']}")
    print(f"  ⚠️  {ss['note']}")
    print()
    
    # Planets table
    print("PLANETS:")
    print("-" * 80)
    print(f"{'Planet':12} {'Trop°':>10} {'Sid°':>10} {'12-Sign':12} {'13-Sign':12} {'Gate':>6} {'Line':>5}")
    print("-" * 80)
    for planet in HD_PLANETS:
        p = output['planets'].get(planet, {})
        if 'error' in p:
            print(f"{planet:12} ERROR: {p['error']}")
        else:
            retro = 'Rx' if p.get('retrograde') else ''
            print(f"{planet:12} {p['tropical_longitude']:>10.4f} {p['sidereal_longitude']:>10.4f} "
                  f"{p['sign_12']:12} {p['sign_13']:12} {p['hd_gate']:>6} {p['hd_line']:>5} {retro}")
    print("-" * 80)
    print()
    
    # Human Design
    print("HUMAN DESIGN:")
    hd = output['human_design']
    print(f"  Profile:        {hd['profile']}")
    print(f"  Type:           {hd['type']}")
    print(f"  Authority:      {hd['authority']}")
    print(f"  Strategy:       {hd['strategy']}")
    print(f"  Definition:     {hd['definition']}")
    print(f"  Cross:          {hd['incarnation_cross']}")
    print()
    
    # Centers
    print("CENTERS:")
    print(f"  Defined ({len(output['centers']['defined'])}):   {', '.join(output['centers']['defined'])}")
    print(f"  Undefined ({len(output['centers']['undefined'])}): {', '.join(output['centers']['undefined'])}")
    print()
    
    # Channels
    print("CHANNELS:")
    for ch in output['channels']['active']:
        print(f"  {ch['gate1']}-{ch['gate2']} ({ch['centers'][0]} ↔ {ch['centers'][1]})")
    print()
    
    # Gates
    print("GATES:")
    print(f"  Personality: {output['gates']['personality']}")
    print(f"  Design:      {output['gates']['design']}")
    print()
    
    print("=" * 80)


# Example usage with test case
if __name__ == "__main__":
    # Test Case: Pete
    # Local: 1968-04-01 01:25
    # UTC Offset: +07:30 (Malaysia historical)
    # Coordinates: Petaling Jaya (3.1073, 101.6070)
    
    birth_local = datetime(1968, 4, 1, 1, 25, 0)
    utc_offset = 7.5  # +07:30
    lat = 3.1073
    lon = 101.6070
    
    output = generate_hd_debug_output(
        birth_local=birth_local,
        utc_offset_hours=utc_offset,
        lat=lat,
        lon=lon,
        name="Pete (Test Case)"
    )
    
    # Print formatted output
    print_hd_debug(output)
    
    # Also print as JSON for machine parsing
    print("\n\n--- JSON OUTPUT ---\n")
    print(json.dumps(output, indent=2, default=str))
