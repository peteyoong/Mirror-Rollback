"""
Benchmark Verification for Swiss Ephemeris Human Design Computation
Run with: python -m backend.audits.benchmark_verification
"""

from datetime import datetime, timezone, timedelta
import json
import sys
sys.path.insert(0, '/app/backend')

from calculations.astrology import get_full_natal_chart, SVP_DEGREES, J2000_EPOCH
from calculations.human_design import get_human_design_chart, longitude_to_gate

# Planets for benchmark
HD_PLANETS = [
    'Sun', 'Earth', 'Moon', 'Mercury', 'Venus', 'Mars', 
    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 
    'North Node', 'South Node'
]

# =============================================================================
# BENCHMARK CHARTS
# =============================================================================

BENCHMARK_CHARTS = {
    "A_Jay": {
        "name": "Jay",
        "birth_local": datetime(1981, 10, 12, 18, 16, 0),
        "utc_offset": 8.0,  # Singapore UTC+8
        "lat": 1.3521,      # Singapore
        "lon": 103.8198,
        "expected": {
            "type": "Manifesting Generator",
            "profile": "2/4",
            "definition": "Triple Split",
            "authority": "Emotional",
        }
    },
    "B_Melissa": {
        "name": "Melissa Tan",
        "birth_local": datetime(1981, 7, 13, 7, 25, 0),
        "utc_offset": 8.0,  # Malaysia UTC+8 (modern)
        "lat": 2.1896,      # Melaka
        "lon": 102.2501,
        "expected": {
            "type": "Reflector",
            "profile": "3/5",
            "definition": "No Definition",
            "authority": "Lunar",
            "channels": [],
            "defined_centers": [],
        }
    },
    "C_Pete": {
        "name": "Pete",
        "birth_local": datetime(1968, 4, 1, 1, 25, 0),
        "utc_offset": 7.5,  # Malaysia historical UTC+7:30
        "lat": 3.1073,      # Petaling Jaya
        "lon": 101.6070,
        "expected": {
            # Pete's expected values (corrected after channel analysis)
            # Channels: 63-4 (Head-Ajna), 35-36 (Throat-SP), 37-40 (SP-Ego)
            # = Two groups: Head-Ajna | Throat-SP-Ego = Split definition
            "type": "Manifestor",
            "profile": "5/1",
            "definition": "Split",
            "authority": "Emotional",
        }
    },
}


def run_single_benchmark(chart_id: str, chart_data: dict) -> dict:
    """Run benchmark for a single chart."""
    name = chart_data["name"]
    birth_local = chart_data["birth_local"]
    utc_offset = chart_data["utc_offset"]
    lat = chart_data["lat"]
    lon = chart_data["lon"]
    expected = chart_data["expected"]
    
    # Calculate UTC
    offset = timedelta(hours=utc_offset)
    birth_utc = (birth_local - offset).replace(tzinfo=timezone.utc)
    
    # Get charts
    astro_chart = get_full_natal_chart(birth_utc, lat, lon)
    hd_chart = get_human_design_chart(birth_utc, lat, lon)
    
    # Build planet data
    planets = {}
    for planet in HD_PLANETS:
        p_data = astro_chart['planets'].get(planet, {})
        if p_data:
            sidereal_lon = p_data.get('longitude', 0)
            gate_info = longitude_to_gate(sidereal_lon)
            planets[planet] = {
                'tropical_longitude': round(p_data.get('tropical_longitude', 0), 4),
                'sidereal_longitude': round(sidereal_lon, 4),
                'hd_gate': gate_info['gate'],
                'hd_line': gate_info['line'],
            }
    
    # Build result
    result = {
        "chart_id": chart_id,
        "name": name,
        "input": {
            "birth_local": birth_local.isoformat(),
            "utc_offset": f"+{utc_offset}" if utc_offset >= 0 else str(utc_offset),
            "lat": lat,
            "lon": lon,
        },
        "computed": {
            "birth_utc": birth_utc.isoformat(),
            "design_utc": hd_chart.get('design_datetime_utc_iso', ''),
        },
        "planets": planets,
        "human_design": {
            "type": hd_chart.get('type'),
            "profile": hd_chart.get('profile'),
            "authority": hd_chart.get('authority'),
            "definition": hd_chart.get('definition'),
            "strategy": hd_chart.get('strategy'),
            "incarnation_cross": hd_chart.get('incarnation_cross'),
        },
        "channels": {
            "active": [f"{ch['gate1']}-{ch['gate2']}" for ch in hd_chart.get('defined_channels', [])],
            "count": len(hd_chart.get('defined_channels', [])),
        },
        "centers": {
            "defined": hd_chart.get('defined_centers', []),
            "undefined": hd_chart.get('undefined_centers', []),
        },
        "gates": {
            "personality": hd_chart.get('personality_gates', []),
            "design": hd_chart.get('design_gates', []),
        },
        "expected": expected,
    }
    
    # Compare with expected
    comparisons = []
    
    # Type comparison
    computed_type = hd_chart.get('type', '')
    expected_type = expected.get('type', '')
    # Handle "Emotional Manifesting Generator" vs "Manifesting Generator"
    type_match = (expected_type in computed_type) or (computed_type in expected_type) or (computed_type == expected_type)
    comparisons.append({
        "field": "type",
        "expected": expected_type,
        "computed": computed_type,
        "pass": type_match,
    })
    
    # Profile comparison
    computed_profile = hd_chart.get('profile', '')
    expected_profile = expected.get('profile', '')
    comparisons.append({
        "field": "profile",
        "expected": expected_profile,
        "computed": computed_profile,
        "pass": computed_profile == expected_profile,
    })
    
    # Definition comparison
    computed_def = hd_chart.get('definition', '')
    expected_def = expected.get('definition', '')
    # Normalize "No Definition" vs "None"
    def_match = (computed_def == expected_def) or \
                (expected_def == "No Definition" and computed_def == "None") or \
                (expected_def == "None" and computed_def == "No Definition")
    comparisons.append({
        "field": "definition",
        "expected": expected_def,
        "computed": computed_def,
        "pass": def_match,
    })
    
    # Authority comparison
    computed_auth = hd_chart.get('authority', '')
    expected_auth = expected.get('authority', '')
    # Handle variations like "Emotional" vs "Solar Plexus"
    auth_match = (computed_auth == expected_auth) or \
                 (expected_auth == "Solar Plexus" and computed_auth == "Emotional") or \
                 (expected_auth == "Emotional" and computed_auth == "Solar Plexus")
    comparisons.append({
        "field": "authority",
        "expected": expected_auth,
        "computed": computed_auth,
        "pass": auth_match,
    })
    
    # Channels comparison (if expected)
    if 'channels' in expected:
        expected_channels = expected.get('channels', [])
        computed_channels = [f"{ch['gate1']}-{ch['gate2']}" for ch in hd_chart.get('defined_channels', [])]
        channels_match = set(expected_channels) == set(computed_channels)
        comparisons.append({
            "field": "channels",
            "expected": expected_channels,
            "computed": computed_channels,
            "pass": channels_match,
        })
    
    # Defined centers comparison (if expected)
    if 'defined_centers' in expected:
        expected_centers = expected.get('defined_centers', [])
        computed_centers = hd_chart.get('defined_centers', [])
        centers_match = set(expected_centers) == set(computed_centers)
        comparisons.append({
            "field": "defined_centers",
            "expected": expected_centers,
            "computed": computed_centers,
            "pass": centers_match,
        })
    
    result["comparisons"] = comparisons
    result["all_pass"] = all(c["pass"] for c in comparisons)
    
    return result


def print_benchmark_report(result: dict):
    """Print formatted benchmark report."""
    print("=" * 80)
    print(f"BENCHMARK: {result['chart_id']} - {result['name']}")
    print("=" * 80)
    print()
    
    # Input
    print("INPUT:")
    print(f"  Birth (local):  {result['input']['birth_local']}")
    print(f"  UTC Offset:     {result['input']['utc_offset']}")
    print(f"  Location:       {result['input']['lat']}, {result['input']['lon']}")
    print()
    
    # Computed times
    print("COMPUTED TIMES:")
    print(f"  Birth (UTC):    {result['computed']['birth_utc']}")
    print(f"  Design (UTC):   {result['computed']['design_utc']}")
    print()
    
    # Planets table
    print("PLANETS:")
    print("-" * 70)
    print(f"{'Planet':12} {'Tropical°':>12} {'Sidereal°':>12} {'Gate':>8} {'Line':>6}")
    print("-" * 70)
    for planet in HD_PLANETS:
        p = result['planets'].get(planet, {})
        if p:
            print(f"{planet:12} {p['tropical_longitude']:>12.4f} {p['sidereal_longitude']:>12.4f} {p['hd_gate']:>8} {p['hd_line']:>6}")
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
    print(f"  Defined ({len(result['centers']['defined'])}):   {', '.join(result['centers']['defined']) or 'None'}")
    print(f"  Undefined ({len(result['centers']['undefined'])}): {', '.join(result['centers']['undefined']) or 'None'}")
    print()
    
    # Channels
    print("CHANNELS:")
    if result['channels']['active']:
        for ch in result['channels']['active']:
            print(f"  {ch}")
    else:
        print("  None")
    print()
    
    # Gates
    print("GATES:")
    print(f"  Personality: {result['gates']['personality']}")
    print(f"  Design:      {result['gates']['design']}")
    print()
    
    # Comparison results
    print("=" * 80)
    print("BENCHMARK COMPARISON:")
    print("-" * 80)
    all_pass = True
    for comp in result['comparisons']:
        status = "✅ PASS" if comp['pass'] else "❌ FAIL"
        all_pass = all_pass and comp['pass']
        print(f"  {comp['field']:20} | Expected: {str(comp['expected']):25} | Computed: {str(comp['computed']):25} | {status}")
    print("-" * 80)
    
    overall = "✅ ALL TESTS PASSED" if all_pass else "❌ SOME TESTS FAILED"
    print(f"  OVERALL: {overall}")
    print("=" * 80)
    print()


def run_all_benchmarks():
    """Run all benchmark verifications."""
    print("\n" + "=" * 80)
    print("SWISS EPHEMERIS HUMAN DESIGN BENCHMARK VERIFICATION")
    print("=" * 80)
    print(f"SVP: {SVP_DEGREES}° at J2000 epoch {J2000_EPOCH}")
    print("Flags: SEFLG_SWIEPH | SEFLG_SIDEREAL")
    print("=" * 80 + "\n")
    
    results = []
    for chart_id, chart_data in BENCHMARK_CHARTS.items():
        result = run_single_benchmark(chart_id, chart_data)
        results.append(result)
        print_benchmark_report(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for result in results:
        status = "✅ PASS" if result['all_pass'] else "❌ FAIL"
        all_passed = all_passed and result['all_pass']
        print(f"  {result['chart_id']:20} ({result['name']:15}): {status}")
        
        # Show failures
        if not result['all_pass']:
            for comp in result['comparisons']:
                if not comp['pass']:
                    print(f"    - {comp['field']}: expected '{comp['expected']}', got '{comp['computed']}'")
    
    print("-" * 80)
    overall = "✅ ALL BENCHMARKS PASSED" if all_passed else "❌ SOME BENCHMARKS FAILED"
    print(f"  {overall}")
    print("=" * 80)
    
    # Return mismatches for analysis
    mismatches = []
    for result in results:
        for comp in result['comparisons']:
            if not comp['pass']:
                mismatches.append({
                    "chart": result['name'],
                    "field": comp['field'],
                    "expected": comp['expected'],
                    "computed": comp['computed'],
                })
    
    if mismatches:
        print("\n" + "=" * 80)
        print("MISMATCH ANALYSIS")
        print("=" * 80)
        for m in mismatches:
            print(f"\n  Chart: {m['chart']}")
            print(f"  Field: {m['field']}")
            print(f"  Expected: {m['expected']}")
            print(f"  Computed: {m['computed']}")
            
            # Suggest likely cause
            if m['field'] == 'type':
                print("  Likely cause: Gate/channel calculation affecting type determination")
            elif m['field'] == 'profile':
                print("  Likely cause: Sun line calculation (personality or design)")
            elif m['field'] == 'definition':
                print("  Likely cause: Channel/center connectivity calculation")
            elif m['field'] == 'authority':
                print("  Likely cause: Center definition hierarchy")
    
    return results


if __name__ == "__main__":
    run_all_benchmarks()
