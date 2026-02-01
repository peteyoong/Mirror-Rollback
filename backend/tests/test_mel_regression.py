"""
===============================================================================
REGRESSION TEST: Mel_1981_true_sidereal
===============================================================================
This test validates the deterministic computation core (mirror-deterministic-v1).

DO NOT modify expected values without understanding the implications.
These values are ground truth for the entire computation pipeline.

To run: python -m pytest tests/test_mel_regression.py -v
Or:     python tests/test_mel_regression.py
===============================================================================
"""
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.timezone_utils import resolve_birth_utc
from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart


# =============================================================================
# TEST INPUT (FROZEN - DO NOT MODIFY)
# =============================================================================
MEL_INPUT = {
    "name": "Mel_1981_true_sidereal",
    "birth_local": "1981-07-13",
    "birth_time": "07:25",
    "timezone": "+07:30",
    "lat": 2.1889,
    "lon": 102.250999,
    "sidereal_settings": {
        "mode": "true_sidereal_user_defined",
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0
    },
    "house_system": "Equal"
}


# =============================================================================
# EXPECTED VALUES (FROZEN - DO NOT MODIFY)
# =============================================================================
MEL_EXPECTED = {
    # UTC Resolution
    "resolved_birth_utc_iso": "1981-07-12T23:55:00Z",
    
    # Astrology
    "sun_sidereal_longitude_min": 78.0,
    "sun_sidereal_longitude_max": 80.0,
    "sun_sign": "Gemini",
    
    "moon_sidereal_longitude_min": 211.0,
    "moon_sidereal_longitude_max": 213.0,
    "moon_sign": "Scorpio",
    
    "ascendant_longitude_min": 89.0,
    "ascendant_longitude_max": 91.0,
    
    # Human Design
    "hd_type": "Reflector",
    "hd_profile": "3/5",
    "hd_authority": "None (Lunar)",
    "hd_defined_centers": [],
    "hd_defined_channels": [],
    
    # Design Date
    "design_datetime_utc_iso_min": "1981-04-12T12:17:00Z",
    "design_datetime_utc_iso_max": "1981-04-12T12:26:00Z"
}


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_utc_resolution() -> Dict[str, Any]:
    """Test timezone parsing and UTC resolution"""
    result = {"name": "UTC Resolution", "passed": False, "details": []}
    
    try:
        birth_utc, resolved_iso, tz_minutes, tz_raw = resolve_birth_utc(
            birth_date_str=MEL_INPUT["birth_local"],
            birth_time_str=MEL_INPUT["birth_time"],
            timezone_str=MEL_INPUT["timezone"]
        )
        
        # Assert resolved_birth_utc_iso
        expected_utc = MEL_EXPECTED["resolved_birth_utc_iso"]
        if resolved_iso == expected_utc:
            result["details"].append(f"✅ resolved_birth_utc_iso: {resolved_iso}")
        else:
            result["details"].append(f"❌ resolved_birth_utc_iso: {resolved_iso} (expected {expected_utc})")
            return result
        
        # Assert timezone minutes
        if tz_minutes == 450:
            result["details"].append(f"✅ parsed_timezone_minutes: {tz_minutes}")
        else:
            result["details"].append(f"❌ parsed_timezone_minutes: {tz_minutes} (expected 450)")
            return result
        
        result["passed"] = True
        result["birth_utc"] = birth_utc
        
    except Exception as e:
        result["details"].append(f"❌ Exception: {e}")
    
    return result


def test_astrology(birth_utc: datetime) -> Dict[str, Any]:
    """Test astrology calculations"""
    result = {"name": "Astrology", "passed": False, "details": []}
    
    try:
        chart = get_full_natal_chart(
            birth_utc,
            MEL_INPUT["lat"],
            MEL_INPUT["lon"],
            sidereal_settings=MEL_INPUT["sidereal_settings"],
            house_system=MEL_INPUT["house_system"]
        )
        
        # Sun longitude
        sun_long = chart["planets"]["Sun"]["longitude"]
        sun_min = MEL_EXPECTED["sun_sidereal_longitude_min"]
        sun_max = MEL_EXPECTED["sun_sidereal_longitude_max"]
        
        if sun_min <= sun_long <= sun_max:
            result["details"].append(f"✅ Sun longitude: {sun_long:.4f}° (in range {sun_min}-{sun_max})")
        else:
            result["details"].append(f"❌ Sun longitude: {sun_long:.4f}° (expected {sun_min}-{sun_max})")
            return result
        
        # Sun sign
        sun_sign = chart["planets"]["Sun"]["sign"]
        if sun_sign == MEL_EXPECTED["sun_sign"]:
            result["details"].append(f"✅ Sun sign: {sun_sign}")
        else:
            result["details"].append(f"❌ Sun sign: {sun_sign} (expected {MEL_EXPECTED['sun_sign']})")
            return result
        
        # Moon longitude
        moon_long = chart["planets"]["Moon"]["longitude"]
        moon_min = MEL_EXPECTED["moon_sidereal_longitude_min"]
        moon_max = MEL_EXPECTED["moon_sidereal_longitude_max"]
        
        if moon_min <= moon_long <= moon_max:
            result["details"].append(f"✅ Moon longitude: {moon_long:.4f}° (in range {moon_min}-{moon_max})")
        else:
            result["details"].append(f"❌ Moon longitude: {moon_long:.4f}° (expected {moon_min}-{moon_max})")
            return result
        
        # Moon sign
        moon_sign = chart["planets"]["Moon"]["sign"]
        if moon_sign == MEL_EXPECTED["moon_sign"]:
            result["details"].append(f"✅ Moon sign: {moon_sign}")
        else:
            result["details"].append(f"❌ Moon sign: {moon_sign} (expected {MEL_EXPECTED['moon_sign']})")
            return result
        
        # Ascendant
        asc_long = chart["houses"]["ascendant"]
        asc_min = MEL_EXPECTED["ascendant_longitude_min"]
        asc_max = MEL_EXPECTED["ascendant_longitude_max"]
        
        if asc_min <= asc_long <= asc_max:
            result["details"].append(f"✅ Ascendant: {asc_long:.4f}° (in range {asc_min}-{asc_max})")
        else:
            result["details"].append(f"❌ Ascendant: {asc_long:.4f}° (expected {asc_min}-{asc_max})")
            return result
        
        # House system
        house_system = chart["houses"]["system"]
        if house_system == "Equal":
            result["details"].append(f"✅ House system: {house_system}")
        else:
            result["details"].append(f"❌ House system: {house_system} (expected Equal)")
            return result
        
        result["passed"] = True
        
    except Exception as e:
        result["details"].append(f"❌ Exception: {e}")
    
    return result


def test_human_design(birth_utc: datetime) -> Dict[str, Any]:
    """Test Human Design calculations"""
    result = {"name": "Human Design", "passed": False, "details": []}
    
    try:
        hd = get_human_design_chart(
            birth_utc,
            MEL_INPUT["lat"],
            MEL_INPUT["lon"],
            sidereal_settings=MEL_INPUT["sidereal_settings"]
        )
        
        # Type
        hd_type = hd["type"]
        if hd_type == MEL_EXPECTED["hd_type"]:
            result["details"].append(f"✅ Type: {hd_type}")
        else:
            result["details"].append(f"❌ Type: {hd_type} (expected {MEL_EXPECTED['hd_type']})")
            return result
        
        # Profile
        profile = hd["profile"]
        if profile == MEL_EXPECTED["hd_profile"]:
            result["details"].append(f"✅ Profile: {profile}")
        else:
            result["details"].append(f"❌ Profile: {profile} (expected {MEL_EXPECTED['hd_profile']})")
            return result
        
        # Authority
        authority = hd["authority"]
        if authority == MEL_EXPECTED["hd_authority"]:
            result["details"].append(f"✅ Authority: {authority}")
        else:
            result["details"].append(f"❌ Authority: {authority} (expected {MEL_EXPECTED['hd_authority']})")
            return result
        
        # Defined Centers
        defined_centers = hd["defined_centers"]
        if defined_centers == MEL_EXPECTED["hd_defined_centers"]:
            result["details"].append(f"✅ Defined Centers: {defined_centers}")
        else:
            result["details"].append(f"❌ Defined Centers: {defined_centers} (expected {MEL_EXPECTED['hd_defined_centers']})")
            return result
        
        # Defined Channels (compare as lists, ignore formatting differences)
        defined_channels = hd.get("defined_channels", [])
        # Extract just gate pairs for comparison
        channel_pairs = [(c["gate1"], c["gate2"]) for c in defined_channels] if defined_channels else []
        expected_pairs = MEL_EXPECTED["hd_defined_channels"]
        
        if channel_pairs == expected_pairs:
            result["details"].append(f"✅ Defined Channels: {channel_pairs}")
        else:
            result["details"].append(f"❌ Defined Channels: {channel_pairs} (expected {expected_pairs})")
            return result
        
        result["passed"] = True
        result["hd_data"] = hd
        
    except Exception as e:
        result["details"].append(f"❌ Exception: {e}")
    
    return result


def test_design_date(birth_utc: datetime) -> Dict[str, Any]:
    """Test Human Design design date calculation"""
    result = {"name": "Design Date", "passed": False, "details": []}
    
    try:
        hd = get_human_design_chart(
            birth_utc,
            MEL_INPUT["lat"],
            MEL_INPUT["lon"],
            sidereal_settings=MEL_INPUT["sidereal_settings"]
        )
        
        design_dt_iso = hd["design_datetime_utc_iso"]
        
        # Parse the design datetime
        # Handle both +00:00 and Z suffix
        if design_dt_iso.endswith("Z"):
            design_dt = datetime.fromisoformat(design_dt_iso.replace("Z", "+00:00"))
        elif design_dt_iso.endswith("+00:00"):
            design_dt = datetime.fromisoformat(design_dt_iso)
        else:
            design_dt = datetime.fromisoformat(design_dt_iso).replace(tzinfo=timezone.utc)
        
        # Parse expected range
        min_iso = MEL_EXPECTED["design_datetime_utc_iso_min"]
        max_iso = MEL_EXPECTED["design_datetime_utc_iso_max"]
        
        min_dt = datetime.fromisoformat(min_iso.replace("Z", "+00:00"))
        max_dt = datetime.fromisoformat(max_iso.replace("Z", "+00:00"))
        
        if min_dt <= design_dt <= max_dt:
            result["details"].append(f"✅ Design Date: {design_dt_iso}")
            result["details"].append(f"   (in range {min_iso} to {max_iso})")
        else:
            result["details"].append(f"❌ Design Date: {design_dt_iso}")
            result["details"].append(f"   (expected range: {min_iso} to {max_iso})")
            return result
        
        # Also check design offset degrees
        design_offset = hd.get("design_offset_degrees", 999)
        if design_offset < 0.1:
            result["details"].append(f"✅ Design offset: {design_offset:.6f}° (< 0.1°)")
        else:
            result["details"].append(f"⚠️ Design offset: {design_offset:.6f}° (high, but date in range)")
        
        result["passed"] = True
        
    except Exception as e:
        result["details"].append(f"❌ Exception: {e}")
    
    return result


# =============================================================================
# MAIN REGRESSION TEST RUNNER
# =============================================================================

def run_mel_regression_test() -> bool:
    """Run all Mel regression tests. Returns True if all pass."""
    
    print("=" * 70)
    print("  REGRESSION TEST: Mel_1981_true_sidereal")
    print("  Computation Version: mirror-deterministic-v1")
    print("=" * 70)
    print()
    
    all_passed = True
    birth_utc = None
    
    # Test 1: UTC Resolution
    print("TEST 1: UTC Resolution")
    print("-" * 70)
    utc_result = test_utc_resolution()
    for detail in utc_result["details"]:
        print(f"  {detail}")
    
    if utc_result["passed"]:
        print("  ✅ UTC Resolution: PASSED")
        birth_utc = utc_result["birth_utc"]
    else:
        print("  ❌ UTC Resolution: FAILED")
        all_passed = False
    print()
    
    if birth_utc is None:
        print("FATAL: Cannot continue without valid birth_utc")
        return False
    
    # Test 2: Astrology
    print("TEST 2: Astrology")
    print("-" * 70)
    astro_result = test_astrology(birth_utc)
    for detail in astro_result["details"]:
        print(f"  {detail}")
    
    if astro_result["passed"]:
        print("  ✅ Astrology: PASSED")
    else:
        print("  ❌ Astrology: FAILED")
        all_passed = False
    print()
    
    # Test 3: Human Design
    print("TEST 3: Human Design")
    print("-" * 70)
    hd_result = test_human_design(birth_utc)
    for detail in hd_result["details"]:
        print(f"  {detail}")
    
    if hd_result["passed"]:
        print("  ✅ Human Design: PASSED")
    else:
        print("  ❌ Human Design: FAILED")
        all_passed = False
    print()
    
    # Test 4: Design Date
    print("TEST 4: Design Date")
    print("-" * 70)
    design_result = test_design_date(birth_utc)
    for detail in design_result["details"]:
        print(f"  {detail}")
    
    if design_result["passed"]:
        print("  ✅ Design Date: PASSED")
    else:
        print("  ❌ Design Date: FAILED")
        all_passed = False
    print()
    
    # Final Summary
    print("=" * 70)
    if all_passed:
        print("  🎯 ALL REGRESSION TESTS PASSED")
        print("  Computation core is stable.")
    else:
        print("  ❌ REGRESSION TEST FAILED")
        print("  DO NOT deploy changes until all tests pass.")
    print("=" * 70)
    
    return all_passed


# =============================================================================
# PYTEST COMPATIBILITY
# =============================================================================

def test_mel_utc_resolution():
    """pytest: UTC Resolution"""
    result = test_utc_resolution()
    assert result["passed"], f"UTC Resolution failed: {result['details']}"


def test_mel_astrology():
    """pytest: Astrology calculations"""
    utc_result = test_utc_resolution()
    assert utc_result["passed"], "UTC Resolution required first"
    
    result = test_astrology(utc_result["birth_utc"])
    assert result["passed"], f"Astrology failed: {result['details']}"


def test_mel_human_design():
    """pytest: Human Design calculations"""
    utc_result = test_utc_resolution()
    assert utc_result["passed"], "UTC Resolution required first"
    
    result = test_human_design(utc_result["birth_utc"])
    assert result["passed"], f"Human Design failed: {result['details']}"


def test_mel_design_date():
    """pytest: Design Date calculation"""
    utc_result = test_utc_resolution()
    assert utc_result["passed"], "UTC Resolution required first"
    
    result = test_design_date(utc_result["birth_utc"])
    assert result["passed"], f"Design Date failed: {result['details']}"


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == "__main__":
    success = run_mel_regression_test()
    sys.exit(0 if success else 1)
