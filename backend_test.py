#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror - Human Design Summary Endpoint Consistency
Testing specific scenarios as requested in the review request.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://mirror-daily.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with consistent formatting"""
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_symbol} {test_name}: {status}")
    if details:
        print(f"   {details}")
    print()

def test_human_design_summary_consistency():
    """
    Test Human Design Summary endpoint consistency as specified in review request.
    
    Test 1: Summary with numbered cross (user: 69819f1a1e4549392d7cb6d1)
    Test 2: Summary with named cross (user: 6984b4a4ce7b78080ce4853a)  
    Test 3: Deep Dive consistency (user: 6984b4a4ce7b78080ce4853a)
    """
    
    print("=" * 80)
    print("HUMAN DESIGN SUMMARY ENDPOINT CONSISTENCY TESTING")
    print("=" * 80)
    
    # Test 1: Summary with numbered cross
    print("\n🔍 TEST 1: Summary with numbered cross")
    print("User ID: 69819f1a1e4549392d7cb6d1")
    print("Expected: Projector, Mental/Environment, 5/1, Right Angle Cross, 23/43")
    
    test1_result = test_summary_numbered_cross("69819f1a1e4549392d7cb6d1")
    
    # Test 2: Summary with named cross (different user)
    print("\n🔍 TEST 2: Summary with named cross")
    print("User ID: 6984b4a4ce7b78080ce4853a")
    print("Expected: Valid HD type, human-friendly cross name like 'LAX Migration'")
    
    test2_result = test_summary_named_cross("6984b4a4ce7b78080ce4853a")
    
    # Test 3: Deep Dive consistency
    print("\n🔍 TEST 3: Deep Dive consistency")
    print("User ID: 6984b4a4ce7b78080ce4853a")
    print("Expected: core_mechanics has same structure as Summary")
    
    test3_result = test_deep_dive_consistency("6984b4a4ce7b78080ce4853a", test2_result)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = test1_result and test2_result and test3_result
    
    if all_passed:
        print("✅ ALL TESTS PASSED - Human Design Summary endpoint consistency verified")
    else:
        print("❌ SOME TESTS FAILED - Issues found with endpoint consistency")
        
    return all_passed


def test_summary_numbered_cross(user_id: str) -> bool:
    """
    Test 1: Summary with numbered cross
    Verify specific expected values for user 69819f1a1e4549392d7cb6d1
    """
    
    url = f"{BACKEND_URL}/human-design/summary/{user_id}"
    
    try:
        print(f"📡 GET {url}")
        response = requests.get(url, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test("Summary Numbered Cross", "FAIL", f"Expected 200, got {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        print(f"📄 Response received: {len(json.dumps(data))} characters")
        
        # Check core_mechanics structure
        if "core_mechanics" not in data:
            log_test("Summary Numbered Cross", "FAIL", "Missing 'core_mechanics' field")
            return False
            
        core_mechanics = data["core_mechanics"]
        print(f"🔧 Core mechanics: {json.dumps(core_mechanics, indent=2)}")
        
        # Verify expected values
        expected_checks = [
            ("type", "Projector"),
            ("authority", "Mental/Environment"),
            ("profile", "5/1"),
            ("incarnation_cross_gates", "23/43")
        ]
        
        all_checks_passed = True
        
        for field, expected_value in expected_checks:
            actual_value = core_mechanics.get(field)
            if actual_value == expected_value:
                print(f"✅ {field}: '{actual_value}' (matches expected)")
            else:
                print(f"❌ {field}: '{actual_value}' (expected '{expected_value}')")
                all_checks_passed = False
        
        # Check incarnation_cross is clean label
        incarnation_cross = core_mechanics.get("incarnation_cross")
        if incarnation_cross and "Right Angle Cross" in incarnation_cross:
            print(f"✅ incarnation_cross: '{incarnation_cross}' (clean label format)")
        else:
            print(f"❌ incarnation_cross: '{incarnation_cross}' (expected clean label like 'Right Angle Cross')")
            all_checks_passed = False
        
        if all_checks_passed:
            log_test("Summary Numbered Cross", "PASS", "All expected values verified")
        else:
            log_test("Summary Numbered Cross", "FAIL", "Some expected values did not match")
            
        return all_checks_passed
        
    except requests.exceptions.RequestException as e:
        log_test("Summary Numbered Cross", "FAIL", f"Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        log_test("Summary Numbered Cross", "FAIL", f"JSON decode error: {e}")
        return False
    except Exception as e:
        log_test("Summary Numbered Cross", "FAIL", f"Unexpected error: {e}")
        return False


def test_summary_named_cross(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Test 2: Summary with named cross (different user)
    Verify valid HD type and human-friendly cross name
    """
    
    url = f"{BACKEND_URL}/human-design/summary/{user_id}"
    
    try:
        print(f"📡 GET {url}")
        response = requests.get(url, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test("Summary Named Cross", "FAIL", f"Expected 200, got {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        print(f"📄 Response received: {len(json.dumps(data))} characters")
        
        # Check core_mechanics structure
        if "core_mechanics" not in data:
            log_test("Summary Named Cross", "FAIL", "Missing 'core_mechanics' field")
            return None
            
        core_mechanics = data["core_mechanics"]
        print(f"🔧 Core mechanics: {json.dumps(core_mechanics, indent=2)}")
        
        # Verify valid HD type
        valid_hd_types = ["Generator", "Manifesting Generator", "Projector", "Manifestor", "Reflector"]
        hd_type = core_mechanics.get("type")
        
        type_valid = hd_type in valid_hd_types
        if type_valid:
            print(f"✅ type: '{hd_type}' (valid HD type)")
        else:
            print(f"❌ type: '{hd_type}' (not a valid HD type)")
        
        # Check incarnation_cross is human-friendly name
        incarnation_cross = core_mechanics.get("incarnation_cross")
        cross_valid = incarnation_cross and incarnation_cross != "Unknown"
        if cross_valid:
            # Should be human-friendly like "LAX Migration" or "Left Angle Cross: Dedication"
            print(f"✅ incarnation_cross: '{incarnation_cross}' (human-friendly name)")
        else:
            print(f"❌ incarnation_cross: '{incarnation_cross}' (expected human-friendly name)")
        
        if type_valid and cross_valid:
            log_test("Summary Named Cross", "PASS", f"Valid HD type ({hd_type}) and human-friendly cross name")
            return data
        else:
            log_test("Summary Named Cross", "FAIL", "Invalid HD type or cross name")
            return None
        
    except requests.exceptions.RequestException as e:
        log_test("Summary Named Cross", "FAIL", f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        log_test("Summary Named Cross", "FAIL", f"JSON decode error: {e}")
        return None
    except Exception as e:
        log_test("Summary Named Cross", "FAIL", f"Unexpected error: {e}")
        return None


def test_deep_dive_consistency(user_id: str, summary_data: Optional[Dict[str, Any]]) -> bool:
    """
    Test 3: Deep Dive consistency
    Verify core_mechanics has same structure as Summary
    """
    
    if not summary_data:
        log_test("Deep Dive Consistency", "FAIL", "Cannot test - Summary test failed")
        return False
    
    url = f"{BACKEND_URL}/human-design/deep-dive/{user_id}"
    
    try:
        print(f"📡 GET {url}")
        response = requests.get(url, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test("Deep Dive Consistency", "FAIL", f"Expected 200, got {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        print(f"📄 Response received: {len(json.dumps(data))} characters")
        
        # Check core_mechanics structure
        if "core_mechanics" not in data:
            log_test("Deep Dive Consistency", "FAIL", "Missing 'core_mechanics' field in Deep Dive")
            return False
            
        deep_dive_core = data["core_mechanics"]
        summary_core = summary_data["core_mechanics"]
        
        print(f"🔧 Deep Dive core mechanics: {json.dumps(deep_dive_core, indent=2)}")
        
        # Check that required fields exist in both
        required_fields = ["type", "authority", "profile", "incarnation_cross", "incarnation_cross_gates"]
        
        all_consistent = True
        
        for field in required_fields:
            summary_value = summary_core.get(field)
            deep_dive_value = deep_dive_core.get(field)
            
            if summary_value == deep_dive_value:
                print(f"✅ {field}: Consistent between Summary and Deep Dive ('{summary_value}')")
            else:
                print(f"❌ {field}: INCONSISTENT - Summary: '{summary_value}', Deep Dive: '{deep_dive_value}'")
                all_consistent = False
        
        if all_consistent:
            log_test("Deep Dive Consistency", "PASS", "All core_mechanics fields consistent between Summary and Deep Dive")
        else:
            log_test("Deep Dive Consistency", "FAIL", "Inconsistencies found between Summary and Deep Dive")
            
        return all_consistent
        
    except requests.exceptions.RequestException as e:
        log_test("Deep Dive Consistency", "FAIL", f"Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        log_test("Deep Dive Consistency", "FAIL", f"JSON decode error: {e}")
        return False
    except Exception as e:
        log_test("Deep Dive Consistency", "FAIL", f"Unexpected error: {e}")
        return False


def main():
    """Run Human Design Summary endpoint consistency tests"""
    print("🧪 HUMAN DESIGN SUMMARY ENDPOINT CONSISTENCY TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    
    success = test_human_design_summary_consistency()
    
    if success:
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("\n💥 TESTS FAILED - See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())