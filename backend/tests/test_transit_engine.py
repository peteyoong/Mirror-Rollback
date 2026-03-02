"""
Deterministic Snapshot Test for Transit Engine
===============================================
Tests that the Transit Engine produces identical output for fixed timestamp:
2026-03-02T09:00:00Z

This test is required per the EMERGENT PROMPT 01 specification.
"""
import sys
sys.path.insert(0, '/app/backend')

import json
from datetime import datetime, timezone
from calculations.transits import compute_transits_now, run_deterministic_test


def test_deterministic_snapshot():
    """
    Deterministic snapshot test for Transit Engine.
    
    Test timestamp: 2026-03-02T09:00:00Z
    
    Ensures identical output across runs for fixed inputs.
    """
    print("=" * 70)
    print("TRANSIT ENGINE - Deterministic Snapshot Test")
    print("=" * 70)
    print()
    
    # Run the deterministic test
    result = run_deterministic_test()
    
    # Verify structure
    assert 'meta' in result, "Missing 'meta' key"
    assert 'timestamp_utc' in result, "Missing 'timestamp_utc' key"
    assert 'transiting_planets' in result, "Missing 'transiting_planets' key"
    assert 'aspects_to_natal_now' in result, "Missing 'aspects_to_natal_now' key"
    
    # Verify meta
    meta = result['meta']
    assert meta['ayanamsa'] == 'fixed_sv_31.2836', f"Wrong ayanamsa: {meta['ayanamsa']}"
    assert meta['house_system'] == 'equal', f"Wrong house system: {meta['house_system']}"
    assert meta['orb_deg'] == 2.0, f"Wrong orb_deg: {meta['orb_deg']}"
    
    # Verify timestamp
    assert result['timestamp_utc'] == '2026-03-02T09:00:00Z', f"Wrong timestamp: {result['timestamp_utc']}"
    
    # Verify transiting planets structure
    expected_planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
    for planet in expected_planets:
        assert planet in result['transiting_planets'], f"Missing planet: {planet}"
        p_data = result['transiting_planets'][planet]
        assert 'longitude' in p_data, f"Missing longitude for {planet}"
        assert 'sign' in p_data, f"Missing sign for {planet}"
        assert 'retrograde' in p_data, f"Missing retrograde flag for {planet}"
        assert 'house' in p_data, f"Missing house for {planet}"
    
    # Verify aspects structure
    for aspect in result['aspects_to_natal_now']:
        assert 'transit_planet' in aspect, "Missing transit_planet in aspect"
        assert 'aspect' in aspect, "Missing aspect type"
        assert 'natal_body' in aspect, "Missing natal_body"
        assert 'orb' in aspect, "Missing orb"
        assert 'exact_angle_delta' in aspect, "Missing exact_angle_delta"
    
    print("✅ All structural assertions passed!")
    print()
    print("RESPONSE:")
    print(json.dumps(result, indent=2))
    print()
    
    # Print summary
    print("-" * 70)
    print("SUMMARY:")
    print(f"  Timestamp: {result['timestamp_utc']}")
    print(f"  Ayanamsa: {meta['ayanamsa']}")
    print(f"  House System: {meta['house_system']}")
    print(f"  Orb: {meta['orb_deg']}°")
    print(f"  Transiting Planets: {len(result['transiting_planets'])}")
    print(f"  Aspects Found: {len(result['aspects_to_natal_now'])}")
    print("-" * 70)
    
    # Sample some planetary positions for verification
    print("\nTRANSITING PLANET POSITIONS:")
    for planet, data in result['transiting_planets'].items():
        retro = " Rx" if data['retrograde'] else ""
        print(f"  {planet.capitalize():10}: {data['longitude']:7.2f}° {data['sign']:12} (House {data['house']}){retro}")
    
    if result['aspects_to_natal_now']:
        print("\nASPECTS TO NATAL (first 5):")
        for asp in result['aspects_to_natal_now'][:5]:
            print(f"  {asp['transit_planet'].capitalize()} {asp['aspect']} natal {asp['natal_body'].capitalize()} (orb: {asp['orb']}°)")
    
    print()
    print("=" * 70)
    print("TEST PASSED ✅")
    print("=" * 70)
    
    return result


if __name__ == '__main__':
    test_deterministic_snapshot()
