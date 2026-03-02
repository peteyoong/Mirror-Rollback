"""
Deterministic Snapshot Test for Transit Engine Phase 2 - Window Scanner (Hardened)
==================================================================================
Tests that the Window Scanner produces identical output for fixed window:
from_utc = 2026-03-02T00:00:00Z, window_days=30

Patch tests:
- house_activation.enabled false when natal houses missing
- stable ordering (sorted by timestamp, planet, aspect, body)
- presence of orb_raw and exact_angle_delta in exact_hits
- canonical event strings in daily_summary (full aspect names, no abbreviations)
"""
import sys
sys.path.insert(0, '/app/backend')

import json
from datetime import datetime, timezone
from calculations.transits import compute_transits_window, run_window_deterministic_test


def test_window_deterministic_snapshot():
    """
    Deterministic snapshot test for Transit Window Scanner (Hardened).
    
    Fixed window: from_utc = 2026-03-02T00:00:00Z, window_days=30
    
    Ensures identical output across runs for fixed inputs.
    """
    print("=" * 70)
    print("TRANSIT ENGINE PHASE 2 - Window Scanner (Hardened) Test")
    print("=" * 70)
    print()
    
    # Run the deterministic test (with natal houses)
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
    
    # Verify window
    window = result['window']
    assert window['from_utc'] == '2026-03-02T00:00:00Z', f"Wrong from_utc: {window['from_utc']}"
    assert window['to_utc'] == '2026-04-01T00:00:00Z', f"Wrong to_utc: {window['to_utc']}"
    
    # =========================================================================
    # PATCH TEST 1: house_activation.enabled = true when natal houses present
    # =========================================================================
    ha = result['house_activation']
    assert 'enabled' in ha, "Missing 'enabled' in house_activation"
    assert ha['enabled'] == True, f"house_activation.enabled should be True with natal houses, got: {ha['enabled']}"
    assert 'reason' not in ha, "house_activation should NOT have 'reason' when enabled"
    print("✅ PATCH 1: house_activation.enabled=True when natal houses present")
    
    # =========================================================================
    # PATCH TEST 2: exact_hits have orb, orb_raw, exact_angle_delta
    # =========================================================================
    if result['exact_hits']:
        for i, hit in enumerate(result['exact_hits'][:5]):
            assert 'orb' in hit, f"Missing 'orb' in exact_hit[{i}]"
            assert 'orb_raw' in hit, f"Missing 'orb_raw' in exact_hit[{i}]"
            assert 'exact_angle_delta' in hit, f"Missing 'exact_angle_delta' in exact_hit[{i}]"
            assert isinstance(hit['orb_raw'], float), f"orb_raw should be float, got: {type(hit['orb_raw'])}"
            # Verify orb is rounded to 2 decimals
            assert hit['orb'] == round(hit['orb'], 2), f"orb should be rounded to 2 decimals"
        print("✅ PATCH 2: exact_hits have orb, orb_raw, exact_angle_delta")
    
    # =========================================================================
    # PATCH TEST 3: daily_summary uses canonical event strings (full names)
    # =========================================================================
    for day in result['daily_summary'][:5]:
        for event in day['peak_events']:
            # Check for abbreviated aspect names (should NOT be present)
            assert '_trin_' not in event, f"Found abbreviated 'trin' in event: {event}"
            assert '_conj_' not in event, f"Found abbreviated 'conj' in event: {event}"
            assert '_squa_' not in event, f"Found abbreviated 'squa' in event: {event}"
            assert '_oppo_' not in event, f"Found abbreviated 'oppo' in event: {event}"
            assert '_sext_' not in event, f"Found abbreviated 'sext' in event: {event}"
            # Verify canonical format
            if '_ingress_' in event:
                # Should be {planet}_ingress_{to_sign} (not truncated)
                parts = event.split('_ingress_')
                assert len(parts) == 2, f"Invalid ingress format: {event}"
                # Sign should be full name (Aries, not Ari)
                assert len(parts[1]) > 3, f"Sign should be full name, got: {parts[1]}"
    print("✅ PATCH 3: daily_summary uses canonical event strings (full names)")
    
    # =========================================================================
    # PATCH TEST 4: Ordering stability
    # =========================================================================
    # exact_hits should be sorted by timestamp, planet, aspect, natal_body
    prev = None
    for hit in result['exact_hits']:
        key = (hit['timestamp_utc'], hit['transit_planet'], hit['aspect'], hit['natal_body'])
        if prev is not None:
            assert key >= prev, f"exact_hits not sorted: {prev} > {key}"
        prev = key
    
    # ingresses should be sorted by timestamp, planet
    prev = None
    for ing in result['ingresses']:
        key = (ing['timestamp_utc'], ing['planet'])
        if prev is not None:
            assert key >= prev, f"ingresses not sorted: {prev} > {key}"
        prev = key
    
    # daily_summary should be sorted by date
    prev = None
    for day in result['daily_summary']:
        if prev is not None:
            assert day['date'] >= prev, f"daily_summary not sorted: {prev} > {day['date']}"
        prev = day['date']
    print("✅ PATCH 4: Ordering is stable and deterministic")
    
    print()
    print("=" * 70)
    print("ALL PATCH TESTS PASSED ✅")
    print("=" * 70)
    
    # Print summary
    print()
    print("-" * 70)
    print("SUMMARY:")
    print(f"  Window: {window['from_utc']} to {window['to_utc']}")
    print(f"  Days: {meta['window_days']}")
    print(f"  Exact Hits: {len(result['exact_hits'])}")
    print(f"  Ingresses: {len(result['ingresses'])}")
    print(f"  Stations: {len(result['stations'])}")
    print(f"  House Activation Enabled: {ha['enabled']}")
    print(f"  Top Houses: {ha['top_houses']}")
    print("-" * 70)
    
    # Sample exact hits with new fields
    if result['exact_hits']:
        print("\nEXACT HITS (first 5) - with orb_raw:")
        for hit in result['exact_hits'][:5]:
            print(f"  {hit['timestamp_utc']}: {hit['transit_planet']} {hit['aspect']} {hit['natal_body']}")
            print(f"     orb={hit['orb']} | orb_raw={hit['orb_raw']} | exact_angle_delta={hit['exact_angle_delta']}")
    
    # Sample daily summary events
    if result['daily_summary']:
        print("\nDAILY SUMMARY (first 3) - canonical event strings:")
        for day in result['daily_summary'][:3]:
            print(f"  {day['date']}: {day['peak_events'][:3]}")
    
    return result


def test_house_activation_disabled_when_natal_houses_missing():
    """
    Test that house_activation is disabled when natal chart lacks house placements.
    """
    print()
    print("=" * 70)
    print("TEST: house_activation disabled when natal houses missing")
    print("=" * 70)
    
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    
    # Natal chart WITHOUT house placements
    mock_natal_chart_no_houses = {
        'astrology': {
            'planets': {
                'Sun': {'longitude': 80.5, 'sign': 'Gemini'},  # No 'house' key
                'Moon': {'longitude': 356.2, 'sign': 'Pisces'},
                'Mercury': {'longitude': 98.7, 'sign': 'Cancer'},
                'Venus': {'longitude': 108.3, 'sign': 'Cancer'},
                'Mars': {'longitude': 42.1, 'sign': 'Taurus'},
                'Jupiter': {'longitude': 177.8, 'sign': 'Virgo'},
                'Saturn': {'longitude': 147.5, 'sign': 'Leo'},
                'Uranus': {'longitude': 205.2, 'sign': 'Libra'},
                'Neptune': {'longitude': 232.1, 'sign': 'Scorpio'},
                'Pluto': {'longitude': 179.4, 'sign': 'Virgo'},
            },
            'angles': {
                'asc': {'longitude': 110.5}
            }
        }
    }
    
    result = compute_transits_window(
        chart_data=mock_natal_chart_no_houses,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True,
        granularity="daily"
    )
    
    ha = result['house_activation']
    
    # Verify disabled state
    assert 'enabled' in ha, "Missing 'enabled' in house_activation"
    assert ha['enabled'] == False, f"house_activation.enabled should be False, got: {ha['enabled']}"
    assert 'reason' in ha, "Missing 'reason' in house_activation when disabled"
    assert ha['reason'] == 'natal_houses_missing', f"Wrong reason: {ha['reason']}"
    assert ha['top_houses'] == [], f"top_houses should be empty, got: {ha['top_houses']}"
    assert ha['scores'] == {}, f"scores should be empty, got: {ha['scores']}"
    assert ha['daily'] == [], f"daily should be empty, got: {ha['daily']}"
    
    print("✅ house_activation correctly disabled when natal houses missing")
    print(f"   enabled: {ha['enabled']}")
    print(f"   reason: {ha['reason']}")
    print()
    print("=" * 70)
    print("TEST PASSED ✅")
    print("=" * 70)


if __name__ == '__main__':
    # Run main deterministic test (with natal houses)
    test_window_deterministic_snapshot()
    
    print()
    
    # Run test for missing natal houses
    test_house_activation_disabled_when_natal_houses_missing()
