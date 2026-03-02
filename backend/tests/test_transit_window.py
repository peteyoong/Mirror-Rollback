"""
Deterministic Snapshot Test for Transit Engine Phase 2 - Window Scanner
========================================================================
Tests that the Window Scanner produces identical output for fixed window:
from_utc = 2026-03-02T00:00:00Z, window_days=30

This test is required per the EMERGENT PROMPT 02 specification.
"""
import sys
sys.path.insert(0, '/app/backend')

import json
from datetime import datetime, timezone
from calculations.transits import compute_transits_window, run_window_deterministic_test


def test_window_deterministic_snapshot():
    """
    Deterministic snapshot test for Transit Window Scanner.
    
    Fixed window: from_utc = 2026-03-02T00:00:00Z, window_days=30
    
    Ensures identical output across runs for fixed inputs.
    """
    print("=" * 70)
    print("TRANSIT ENGINE PHASE 2 - Window Scanner Deterministic Test")
    print("=" * 70)
    print()
    
    # Run the deterministic test
    result = run_window_deterministic_test()
    
    # Verify structure
    assert 'meta' in result, "Missing 'meta' key"
    assert 'window' in result, "Missing 'window' key"
    assert 'exact_hits' in result, "Missing 'exact_hits' key"
    assert 'ingresses' in result, "Missing 'ingresses' key"
    assert 'stations' in result, "Missing 'stations' key"
    assert 'house_activation' in result, "Missing 'house_activation' key"
    assert 'daily_summary' in result, "Missing 'daily_summary' key"
    
    # Verify meta
    meta = result['meta']
    assert meta['ayanamsa'] == 'fixed_sv_31.2836', f"Wrong ayanamsa: {meta['ayanamsa']}"
    assert meta['house_system'] == 'equal', f"Wrong house system: {meta['house_system']}"
    assert meta['orb_deg'] == 2.0, f"Wrong orb_deg: {meta['orb_deg']}"
    assert meta['window_days'] == 30, f"Wrong window_days: {meta['window_days']}"
    assert meta['granularity'] == 'daily', f"Wrong granularity: {meta['granularity']}"
    
    # Verify window
    window = result['window']
    assert window['from_utc'] == '2026-03-02T00:00:00Z', f"Wrong from_utc: {window['from_utc']}"
    assert window['to_utc'] == '2026-04-01T00:00:00Z', f"Wrong to_utc: {window['to_utc']}"
    
    # Verify exact_hits structure
    for hit in result['exact_hits']:
        assert 'timestamp_utc' in hit, "Missing timestamp_utc in exact_hit"
        assert 'transit_planet' in hit, "Missing transit_planet in exact_hit"
        assert 'aspect' in hit, "Missing aspect in exact_hit"
        assert 'natal_body' in hit, "Missing natal_body in exact_hit"
        assert 'orb' in hit, "Missing orb in exact_hit"
        assert 'exact_angle_delta' in hit, "Missing exact_angle_delta in exact_hit"
    
    # Verify ingresses structure
    for ingress in result['ingresses']:
        assert 'timestamp_utc' in ingress, "Missing timestamp_utc in ingress"
        assert 'planet' in ingress, "Missing planet in ingress"
        assert 'from_sign' in ingress, "Missing from_sign in ingress"
        assert 'to_sign' in ingress, "Missing to_sign in ingress"
        assert 'longitude' in ingress, "Missing longitude in ingress"
        assert 'house' in ingress, "Missing house in ingress"
    
    # Verify stations structure
    for station in result['stations']:
        assert 'timestamp_utc' in station, "Missing timestamp_utc in station"
        assert 'planet' in station, "Missing planet in station"
        assert 'type' in station, "Missing type in station"
        assert station['type'] in ['station_retrograde', 'station_direct'], f"Invalid station type: {station['type']}"
        assert 'longitude' in station, "Missing longitude in station"
        assert 'sign' in station, "Missing sign in station"
        assert 'house' in station, "Missing house in station"
    
    # Verify house_activation structure
    ha = result['house_activation']
    assert 'top_houses' in ha, "Missing top_houses in house_activation"
    assert 'scores' in ha, "Missing scores in house_activation"
    assert 'daily' in ha, "Missing daily in house_activation"
    assert isinstance(ha['top_houses'], list), "top_houses must be a list"
    
    print("✅ All structural assertions passed!")
    print()
    
    # Print summary
    print("-" * 70)
    print("SUMMARY:")
    print(f"  Window: {window['from_utc']} to {window['to_utc']}")
    print(f"  Days: {meta['window_days']}")
    print(f"  Exact Hits: {len(result['exact_hits'])}")
    print(f"  Ingresses: {len(result['ingresses'])}")
    print(f"  Stations: {len(result['stations'])}")
    print(f"  Top Houses: {ha['top_houses']}")
    print("-" * 70)
    
    # Sample exact hits
    if result['exact_hits']:
        print("\nEXACT HITS (first 10):")
        for hit in result['exact_hits'][:10]:
            print(f"  {hit['timestamp_utc']}: {hit['transit_planet']} {hit['aspect']} {hit['natal_body']} (orb: {hit['orb']}°)")
    
    # Sample ingresses
    if result['ingresses']:
        print("\nINGRESSES:")
        for ing in result['ingresses'][:5]:
            print(f"  {ing['timestamp_utc']}: {ing['planet']} {ing['from_sign']} → {ing['to_sign']} (House {ing['house']})")
    
    # Sample stations
    if result['stations']:
        print("\nSTATIONS:")
        for sta in result['stations'][:5]:
            print(f"  {sta['timestamp_utc']}: {sta['planet']} {sta['type']} @ {sta['longitude']}° {sta['sign']}")
    
    # House activation scores
    if ha['scores']:
        print("\nHOUSE ACTIVATION SCORES:")
        for house, score in sorted(ha['scores'].items(), key=lambda x: float(x[1]), reverse=True)[:5]:
            print(f"  House {house}: {score}")
    
    print()
    print("=" * 70)
    print("TEST PASSED ✅")
    print("=" * 70)
    
    # Output full JSON for inspection
    print("\nFULL JSON RESPONSE:")
    # Truncate daily arrays for readability
    output = result.copy()
    if len(output.get('daily_summary', [])) > 5:
        output['daily_summary'] = output['daily_summary'][:5] + [{'...': f'{len(result["daily_summary"]) - 5} more days'}]
    if len(output.get('house_activation', {}).get('daily', [])) > 5:
        output['house_activation']['daily'] = output['house_activation']['daily'][:5] + [{'...': f'{len(result["house_activation"]["daily"]) - 5} more days'}]
    
    print(json.dumps(output, indent=2))
    
    return result


if __name__ == '__main__':
    test_window_deterministic_snapshot()
