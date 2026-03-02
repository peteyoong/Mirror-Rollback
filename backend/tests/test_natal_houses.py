"""
Unit Tests for Natal House Data - Phase 5
==========================================
Tests:
- house_activation.enabled=true when natal houses exist
- house_activation.enabled=false when natal houses missing
- Proper house scoring when enabled
"""
import sys
sys.path.insert(0, '/app/backend')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from calculations.transits import (
    compute_transits_window,
    extract_natal_planets,
    extract_natal_ascendant,
)
from datetime import datetime, timezone

load_dotenv()


async def get_chart(user_id: str) -> dict:
    """Fetch a chart from the database"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    return await db.charts.find_one({'user_id': user_id})


def test_houses_enabled_when_data_exists():
    """Test that house_activation.enabled=true when natal houses exist"""
    print("=" * 60)
    print("TEST: house_activation.enabled=true when houses exist")
    print("=" * 60)
    
    # User with houses: 6971c81f2b40fd5ef501d375 (Peter)
    chart = asyncio.run(get_chart('6971c81f2b40fd5ef501d375'))
    
    assert chart is not None, "Chart not found"
    
    # Check natal data
    natal_planets = extract_natal_planets(chart)
    natal_asc = extract_natal_ascendant(chart)
    
    # Verify planets have houses
    planets_with_houses = 0
    for name, data in natal_planets.items():
        if data.get('house') is not None:
            planets_with_houses += 1
    
    print(f"  Planets with house data: {planets_with_houses}")
    print(f"  Ascendant longitude: {natal_asc}")
    
    assert planets_with_houses > 0, "Expected at least one planet with house data"
    assert natal_asc is not None, "Expected ascendant longitude"
    
    # Compute transits
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    result = compute_transits_window(
        chart_data=chart,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True
    )
    
    ha = result['house_activation']
    
    assert ha['enabled'] == True, f"Expected enabled=True, got {ha['enabled']}"
    assert 'reason' not in ha, "Should not have 'reason' when enabled"
    assert len(ha['top_houses']) > 0, "Expected top_houses to be populated"
    assert len(ha['scores']) > 0, "Expected scores to be populated"
    
    print(f"  house_activation.enabled: {ha['enabled']} ✓")
    print(f"  top_houses: {ha['top_houses']}")
    print(f"  scores sample: {list(ha['scores'].items())[:3]}")
    
    print()
    print("✅ TEST PASSED")
    return True


def test_houses_disabled_when_data_missing():
    """Test that house_activation.enabled=false when natal houses missing
    
    NOTE: Uses a mock fixture since all DB users may have houses now after backfill.
    """
    print()
    print("=" * 60)
    print("TEST: house_activation.enabled=false when houses missing")
    print("=" * 60)
    
    # Use a mock chart WITHOUT house data (instead of DB user)
    mock_chart = {
        'astrology': {
            'planets': {
                'Sun': {'longitude': 80.5, 'sign': 'Gemini'},  # No house
                'Moon': {'longitude': 356.2, 'sign': 'Pisces'},
                'Mercury': {'longitude': 98.7, 'sign': 'Cancer'},
            },
            'angles': {
                'asc': {'longitude': 110.5}
            }
        }
    }
    
    # Check natal data
    natal_planets = extract_natal_planets(mock_chart)
    
    # Verify planets don't have houses
    planets_with_houses = 0
    for name, data in natal_planets.items():
        if data.get('house') is not None:
            planets_with_houses += 1
    
    print(f"  Planets with house data: {planets_with_houses}")
    
    # Compute transits
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    result = compute_transits_window(
        chart_data=mock_chart,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True
    )
    
    ha = result['house_activation']
    
    assert ha['enabled'] == False, f"Expected enabled=False, got {ha['enabled']}"
    assert ha.get('reason') == 'natal_houses_missing', f"Expected reason='natal_houses_missing', got {ha.get('reason')}"
    assert ha['top_houses'] == [], f"Expected top_houses=[], got {ha['top_houses']}"
    assert ha['scores'] == {}, f"Expected scores={{}}, got {ha['scores']}"
    assert ha['daily'] == [], f"Expected daily=[], got {ha['daily']}"
    
    print(f"  house_activation.enabled: {ha['enabled']} ✓")
    print(f"  house_activation.reason: {ha.get('reason')} ✓")
    
    print()
    print("✅ TEST PASSED")
    return True


def test_fixture_chart_with_houses():
    """Test with a mock fixture that has house data"""
    print()
    print("=" * 60)
    print("TEST: Fixture chart with houses")
    print("=" * 60)
    
    # Mock chart with all house data
    mock_chart = {
        'astrology': {
            'planets': {
                'Sun': {'longitude': 80.5, 'sign': 'Gemini', 'house': 3},
                'Moon': {'longitude': 356.2, 'sign': 'Pisces', 'house': 12},
                'Mercury': {'longitude': 98.7, 'sign': 'Cancer', 'house': 4},
                'Saturn': {'longitude': 147.5, 'sign': 'Leo', 'house': 5},
                'Jupiter': {'longitude': 177.8, 'sign': 'Virgo', 'house': 6},
            },
            'angles': {
                'asc': {'longitude': 110.5}
            },
            'houses': {
                'system': 'Equal',
                'cusps': [110.5, 140.5, 170.5, 200.5, 230.5, 260.5, 290.5, 320.5, 350.5, 20.5, 50.5, 80.5]
            }
        }
    }
    
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    result = compute_transits_window(
        chart_data=mock_chart,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True
    )
    
    ha = result['house_activation']
    
    assert ha['enabled'] == True, f"Expected enabled=True, got {ha['enabled']}"
    assert len(ha['top_houses']) > 0, "Expected top_houses"
    
    print(f"  house_activation.enabled: {ha['enabled']} ✓")
    print(f"  top_houses: {ha['top_houses']}")
    
    print()
    print("✅ TEST PASSED")
    return True


def test_fixture_chart_without_houses():
    """Test with a mock fixture that has NO house data"""
    print()
    print("=" * 60)
    print("TEST: Fixture chart WITHOUT houses")
    print("=" * 60)
    
    # Mock chart without house data
    mock_chart = {
        'astrology': {
            'planets': {
                'Sun': {'longitude': 80.5, 'sign': 'Gemini'},  # No house
                'Moon': {'longitude': 356.2, 'sign': 'Pisces'},
                'Mercury': {'longitude': 98.7, 'sign': 'Cancer'},
            },
            'angles': {
                'asc': {'longitude': 110.5}
            }
        }
    }
    
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    result = compute_transits_window(
        chart_data=mock_chart,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True
    )
    
    ha = result['house_activation']
    
    assert ha['enabled'] == False, f"Expected enabled=False, got {ha['enabled']}"
    assert ha.get('reason') == 'natal_houses_missing', f"Expected reason='natal_houses_missing'"
    
    print(f"  house_activation.enabled: {ha['enabled']} ✓")
    print(f"  house_activation.reason: {ha.get('reason')} ✓")
    
    print()
    print("✅ TEST PASSED")
    return True


def test_backfilled_user_jane():
    """Test that Jane (backfilled user) now has houses enabled"""
    print()
    print("=" * 60)
    print("TEST: Backfilled user (Jane) has houses enabled")
    print("=" * 60)
    
    # Jane's user_id - was backfilled with house data
    chart = asyncio.run(get_chart('6971c8f681beab3a8955b255'))
    
    if chart is None:
        print("  Jane's chart not found - SKIPPING (user may not exist)")
        print()
        print("⚠️ TEST SKIPPED")
        return True
    
    # Check natal data
    natal_planets = extract_natal_planets(chart)
    natal_asc = extract_natal_ascendant(chart)
    
    # Verify planets have houses
    planets_with_houses = 0
    for name, data in natal_planets.items():
        if data.get('house') is not None:
            planets_with_houses += 1
    
    print(f"  Planets with house data: {planets_with_houses}")
    print(f"  Ascendant longitude: {natal_asc}")
    
    # After backfill, Jane should have houses
    assert planets_with_houses > 0, "Expected Jane to have planets with house data after backfill"
    
    # Compute transits
    test_from = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    result = compute_transits_window(
        chart_data=chart,
        from_utc=test_from,
        window_days=30,
        orb_deg=2.0,
        include_houses=True
    )
    
    ha = result['house_activation']
    
    assert ha['enabled'] == True, f"Expected enabled=True after backfill, got {ha['enabled']}"
    assert 'reason' not in ha, "Should not have 'reason' when enabled"
    assert len(ha['top_houses']) > 0, "Expected top_houses to be populated"
    
    print(f"  house_activation.enabled: {ha['enabled']} ✓")
    print(f"  top_houses: {ha['top_houses']}")
    
    print()
    print("✅ TEST PASSED")
    return True


if __name__ == '__main__':
    all_passed = True
    
    try:
        test_houses_enabled_when_data_exists()
        test_houses_disabled_when_data_missing()
        test_fixture_chart_with_houses()
        test_fixture_chart_without_houses()
        test_backfilled_user_jane()
        
        print()
        print("=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        all_passed = False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    exit(0 if all_passed else 1)
