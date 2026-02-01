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
import re
from datetime import datetime, timezone
from typing import Dict, Any, List

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
# SANITY TESTS (Lightweight stability checks)
# =============================================================================
# These tests verify basic functionality without deep astrology assertions.
# They ensure the computation pipeline completes without errors.

SANITY_TEST_A = {
    "name": "Sanity_Malaysia_2000",
    "birth_local": "2000-01-01",
    "birth_time": "00:00",
    "timezone": "+08:00",
    "lat": 3.1390,  # Kuala Lumpur
    "lon": 101.6869,
    "expected_utc": "1999-12-31T16:00:00Z",
    "expected_tz_minutes": 480
}

SANITY_TEST_B = {
    "name": "Sanity_NewYork_1990",
    "birth_local": "1990-06-15",
    "birth_time": "12:00",
    "timezone": "-05:00",
    "lat": 40.7128,  # New York
    "lon": -74.0060,
    "expected_utc": "1990-06-15T17:00:00Z",
    "expected_tz_minutes": -300
}


def run_sanity_test(test_config: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single sanity test"""
    result = {
        "name": test_config["name"],
        "passed": False,
        "details": []
    }
    
    sidereal_settings = {
        "mode": "true_sidereal_user_defined",
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0
    }
    
    try:
        # Test 1: UTC Resolution
        birth_utc, resolved_iso, tz_minutes, _ = resolve_birth_utc(
            birth_date_str=test_config["birth_local"],
            birth_time_str=test_config["birth_time"],
            timezone_str=test_config["timezone"]
        )
        
        # Assert UTC
        if resolved_iso == test_config["expected_utc"]:
            result["details"].append(f"✅ resolved_birth_utc_iso: {resolved_iso}")
        else:
            result["details"].append(f"❌ resolved_birth_utc_iso: {resolved_iso} (expected {test_config['expected_utc']})")
            return result
        
        # Assert timezone minutes
        if tz_minutes == test_config["expected_tz_minutes"]:
            result["details"].append(f"✅ parsed_timezone_minutes: {tz_minutes}")
        else:
            result["details"].append(f"❌ parsed_timezone_minutes: {tz_minutes} (expected {test_config['expected_tz_minutes']})")
            return result
        
        # Test 2: Astrology computation completes
        astro_chart = get_full_natal_chart(
            birth_utc,
            test_config["lat"],
            test_config["lon"],
            sidereal_settings=sidereal_settings,
            house_system="Equal"
        )
        
        if astro_chart and "planets" in astro_chart:
            result["details"].append("✅ Astrology computation completed")
        else:
            result["details"].append("❌ Astrology computation failed")
            return result
        
        # Test 3: Human Design computation completes
        hd_chart = get_human_design_chart(
            birth_utc,
            test_config["lat"],
            test_config["lon"],
            sidereal_settings=sidereal_settings
        )
        
        if hd_chart and "type" in hd_chart:
            result["details"].append("✅ Human Design computation completed")
        else:
            result["details"].append("❌ Human Design computation failed")
            return result
        
        result["passed"] = True
        
    except Exception as e:
        result["details"].append(f"❌ Exception: {e}")
    
    return result


def test_sanity_malaysia_2000():
    """pytest: Sanity test - Malaysia 2000"""
    result = run_sanity_test(SANITY_TEST_A)
    assert result["passed"], f"Sanity test A failed: {result['details']}"


def test_sanity_newyork_1990():
    """pytest: Sanity test - New York 1990"""
    result = run_sanity_test(SANITY_TEST_B)
    assert result["passed"], f"Sanity test B failed: {result['details']}"


# =============================================================================
# INTERPRETIVE LANGUAGE GUARDRAIL TEST
# =============================================================================
# This test ensures the deterministic compute output contains no interpretive
# language that should only exist in the downstream interpretation layer.

FORBIDDEN_WORDS = [
    # Addressing user directly
    "you", "your", "yourself",
    # Prescriptive language
    "should", "must", "need to", "have to",
    # Future predictions
    "will", "going to",
    # Interpretive language
    "means", "represents", "symbolizes", "signifies",
    # Inferential language
    "invites", "suggests", "indicates", "implies",
    # Advice language
    "try", "consider", "remember",
]

# Allowed exceptions (field names, technical terms)
ALLOWED_EXCEPTIONS = [
    "your_lenses",  # API field name
    "chart_type",   # Descriptive field
    "julian_day",   # Technical term
]


def scan_for_forbidden_words(obj: Any, path: str = "") -> List[str]:
    """Recursively scan object for forbidden interpretive words"""
    violations = []
    
    if isinstance(obj, str):
        # Skip if it's a known exception
        if any(exc in path.lower() for exc in ALLOWED_EXCEPTIONS):
            return violations
        
        # Check for forbidden words (case-insensitive, whole word)
        lower_str = obj.lower()
        for word in FORBIDDEN_WORDS:
            # Check for whole word match
            import re
            if re.search(r'\b' + re.escape(word) + r'\b', lower_str):
                violations.append(f"'{word}' found at {path}: \"{obj[:50]}...\"" if len(obj) > 50 else f"'{word}' found at {path}: \"{obj}\"")
    
    elif isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            violations.extend(scan_for_forbidden_words(value, new_path))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(scan_for_forbidden_words(item, f"{path}[{i}]"))
    
    return violations


def test_no_interpretive_language():
    """pytest: Verify compute output contains no interpretive language"""
    # Get a sample computation
    utc_result = test_utc_resolution()
    if not utc_result["passed"]:
        assert False, "Cannot run interpretive language test without valid UTC"
    
    birth_utc = utc_result["birth_utc"]
    
    # Get astrology output
    astro_chart = get_full_natal_chart(
        birth_utc,
        MEL_INPUT["lat"],
        MEL_INPUT["lon"],
        sidereal_settings=MEL_INPUT["sidereal_settings"],
        house_system=MEL_INPUT["house_system"]
    )
    
    # Get HD output
    hd_chart = get_human_design_chart(
        birth_utc,
        MEL_INPUT["lat"],
        MEL_INPUT["lon"],
        sidereal_settings=MEL_INPUT["sidereal_settings"]
    )
    
    # Scan for violations
    astro_violations = scan_for_forbidden_words(astro_chart, "astrology")
    hd_violations = scan_for_forbidden_words(hd_chart, "human_design")
    
    all_violations = astro_violations + hd_violations
    
    if all_violations:
        violation_msg = "\n".join(all_violations[:10])  # Show first 10
        assert False, f"Interpretive language found in compute output:\n{violation_msg}"


def run_interpretive_language_test() -> Dict[str, Any]:
    """Run interpretive language guardrail test"""
    result = {"name": "Interpretive Language Guardrail", "passed": False, "details": []}
    
    try:
        # Get a sample computation
        birth_utc, _, _, _ = resolve_birth_utc(
            MEL_INPUT["birth_local"],
            MEL_INPUT["birth_time"],
            MEL_INPUT["timezone"]
        )
        
        astro_chart = get_full_natal_chart(
            birth_utc,
            MEL_INPUT["lat"],
            MEL_INPUT["lon"],
            sidereal_settings=MEL_INPUT["sidereal_settings"],
            house_system=MEL_INPUT["house_system"]
        )
        
        hd_chart = get_human_design_chart(
            birth_utc,
            MEL_INPUT["lat"],
            MEL_INPUT["lon"],
            sidereal_settings=MEL_INPUT["sidereal_settings"]
        )
        
        astro_violations = scan_for_forbidden_words(astro_chart, "astrology")
        hd_violations = scan_for_forbidden_words(hd_chart, "human_design")
        
        all_violations = astro_violations + hd_violations
        
        if all_violations:
            result["details"].append(f"❌ Found {len(all_violations)} violation(s):")
            for v in all_violations[:5]:
                result["details"].append(f"   - {v}")
            if len(all_violations) > 5:
                result["details"].append(f"   ... and {len(all_violations) - 5} more")
        else:
            result["details"].append("✅ No interpretive language found in compute output")
            result["passed"] = True
        
    except Exception as e:
        result["details"].append(f"❌ Exception: {e}")
    
    return result


def run_all_sanity_tests() -> bool:
    """Run all sanity tests. Returns True if all pass."""
    print()
    print("=" * 70)
    print("  SANITY TESTS (Stability Checks)")
    print("=" * 70)
    print()
    
    all_passed = True
    
    for test_config in [SANITY_TEST_A, SANITY_TEST_B]:
        print(f"SANITY: {test_config['name']}")
        print("-" * 70)
        result = run_sanity_test(test_config)
        
        for detail in result["details"]:
            print(f"  {detail}")
        
        if result["passed"]:
            print(f"  ✅ {test_config['name']}: PASSED")
        else:
            print(f"  ❌ {test_config['name']}: FAILED")
            all_passed = False
        print()
    
    # Run interpretive language guardrail
    print("GUARDRAIL: Interpretive Language Check")
    print("-" * 70)
    lang_result = run_interpretive_language_test()
    for detail in lang_result["details"]:
        print(f"  {detail}")
    if lang_result["passed"]:
        print("  ✅ Interpretive Language Guardrail: PASSED")
    else:
        print("  ❌ Interpretive Language Guardrail: FAILED")
        all_passed = False
    print()
    
    return all_passed


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Run Mel regression test
    mel_success = run_mel_regression_test()
    
    # Run sanity tests (includes interpretive language guardrail)
    sanity_success = run_all_sanity_tests()
    
    # Final status
    print("=" * 70)
    if mel_success and sanity_success:
        print("  🎯 ALL TESTS PASSED (Regression + Sanity + Guardrails)")
    else:
        print("  ❌ SOME TESTS FAILED")
    print("=" * 70)
    
    sys.exit(0 if (mel_success and sanity_success) else 1)
