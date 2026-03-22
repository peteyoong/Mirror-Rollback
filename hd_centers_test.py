#!/usr/bin/env python3
"""
Human Design Centers Endpoint Testing
Testing the GET /api/human-design/centers/{user_id} endpoint implementation
"""

import requests
import json
import time
from typing import Dict, Any, List

# Base URL from frontend/.env REACT_APP_BACKEND_URL
BASE_URL = "https://reflect-ai-25.preview.emergentagent.com/api"

# Test user ID from review request
TEST_USER_ID = "697f0c6abf35c0528ff06954"

# Expected 9 Human Design Centers
EXPECTED_CENTERS = [
    "Head", "Ajna", "Throat", "G Center", "Ego",
    "Solar Plexus", "Sacral", "Spleen", "Root"
]

# Required fields for each center
REQUIRED_CENTER_FIELDS = [
    "center_name", "display_name", "defined", "gates_present",
    "themes", "what_this_means", "your_challenge", "your_genius",
    "practical_experiments", "remember"
]

def log_test_result(test_name: str, passed: bool, details: str = ""):
    """Log test results with clear formatting."""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   Details: {details}")

def test_human_design_centers_endpoint():
    """
    Test the Human Design Centers endpoint implementation.
    
    Test Scenarios:
    1. Basic Centers Endpoint Test
    2. Center Data Structure Test  
    3. Center Names Test
    4. Defined vs Undefined Content Test
    """
    
    print("=" * 80)
    print("HUMAN DESIGN CENTERS ENDPOINT TESTING")
    print("=" * 80)
    
    # Test 1: Basic Centers Endpoint Test
    print(f"\n🧪 TEST 1: Basic Centers Endpoint Test")
    print(f"Testing: GET {BASE_URL}/human-design/centers/{TEST_USER_ID}")
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/human-design/centers/{TEST_USER_ID}", timeout=30)
        response_time = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            log_test_result("Basic Endpoint Access", False, f"Status {response.status_code}: {response.text}")
            return False
            
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            log_test_result("JSON Response Parsing", False, f"Invalid JSON: {e}")
            return False
            
        # Check basic response structure
        if not isinstance(data, dict):
            log_test_result("Response Structure", False, "Response is not a dictionary")
            return False
            
        # Check required top-level fields
        required_fields = ["success", "centers", "summary"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            log_test_result("Required Fields", False, f"Missing fields: {missing_fields}")
            return False
            
        # Check success field
        if data.get("success") != True:
            log_test_result("Success Status", False, f"success: {data.get('success')}")
            return False
            
        # Check centers array
        centers = data.get("centers", [])
        if not isinstance(centers, list):
            log_test_result("Centers Array Type", False, "centers is not an array")
            return False
            
        if len(centers) != 9:
            log_test_result("Centers Count", False, f"Expected 9 centers, got {len(centers)}")
            return False
            
        # Check summary structure
        summary = data.get("summary", {})
        if not isinstance(summary, dict):
            log_test_result("Summary Structure", False, "summary is not a dictionary")
            return False
            
        required_summary_fields = ["defined_count", "undefined_count"]
        missing_summary_fields = [field for field in required_summary_fields if field not in summary]
        if missing_summary_fields:
            log_test_result("Summary Fields", False, f"Missing summary fields: {missing_summary_fields}")
            return False
            
        defined_count = summary.get("defined_count", 0)
        undefined_count = summary.get("undefined_count", 0)
        
        if defined_count + undefined_count != 9:
            log_test_result("Summary Counts", False, f"defined_count ({defined_count}) + undefined_count ({undefined_count}) != 9")
            return False
            
        log_test_result("Basic Centers Endpoint Test", True, f"9 centers, {defined_count} defined, {undefined_count} undefined")
        
    except requests.exceptions.RequestException as e:
        log_test_result("Basic Endpoint Access", False, f"Request failed: {e}")
        return False
    except Exception as e:
        log_test_result("Basic Endpoint Access", False, f"Unexpected error: {e}")
        return False
    
    # Test 2: Center Data Structure Test
    print(f"\n🧪 TEST 2: Center Data Structure Test")
    
    structure_passed = True
    structure_details = []
    
    for i, center in enumerate(centers):
        center_name = center.get("center_name", f"Center {i}")
        
        # Check if center is a dictionary
        if not isinstance(center, dict):
            structure_passed = False
            structure_details.append(f"{center_name}: Not a dictionary")
            continue
            
        # Check required fields
        missing_fields = [field for field in REQUIRED_CENTER_FIELDS if field not in center]
        if missing_fields:
            structure_passed = False
            structure_details.append(f"{center_name}: Missing fields {missing_fields}")
            continue
            
        # Check field types
        field_type_errors = []
        
        # String fields
        string_fields = ["center_name", "display_name", "what_this_means", "your_challenge", "your_genius", "remember"]
        for field in string_fields:
            if not isinstance(center.get(field), str) or not center.get(field).strip():
                field_type_errors.append(f"{field} (empty or not string)")
        
        # Boolean field
        if not isinstance(center.get("defined"), bool):
            field_type_errors.append("defined (not boolean)")
            
        # Array fields
        array_fields = ["gates_present", "themes", "practical_experiments"]
        for field in array_fields:
            if not isinstance(center.get(field), list):
                field_type_errors.append(f"{field} (not array)")
        
        # Check practical_experiments has 3 items
        practical_experiments = center.get("practical_experiments", [])
        if len(practical_experiments) != 3:
            field_type_errors.append(f"practical_experiments (expected 3 items, got {len(practical_experiments)})")
            
        if field_type_errors:
            structure_passed = False
            structure_details.append(f"{center_name}: {', '.join(field_type_errors)}")
    
    if structure_passed:
        log_test_result("Center Data Structure Test", True, "All centers have required fields with correct types")
    else:
        log_test_result("Center Data Structure Test", False, "; ".join(structure_details))
        return False
    
    # Test 3: Center Names Test
    print(f"\n🧪 TEST 3: Center Names Test")
    
    actual_center_names = [center.get("center_name") for center in centers]
    missing_centers = [name for name in EXPECTED_CENTERS if name not in actual_center_names]
    extra_centers = [name for name in actual_center_names if name not in EXPECTED_CENTERS]
    
    names_passed = True
    names_details = []
    
    if missing_centers:
        names_passed = False
        names_details.append(f"Missing centers: {missing_centers}")
        
    if extra_centers:
        names_passed = False
        names_details.append(f"Extra centers: {extra_centers}")
    
    if names_passed:
        log_test_result("Center Names Test", True, "All 9 expected centers present")
    else:
        log_test_result("Center Names Test", False, "; ".join(names_details))
        return False
    
    # Test 4: Defined vs Undefined Content Test
    print(f"\n🧪 TEST 4: Defined vs Undefined Content Test")
    
    defined_centers_found = [center for center in centers if center.get("defined") == True]
    undefined_centers_found = [center for center in centers if center.get("defined") == False]
    
    content_passed = True
    content_details = []
    
    # Check that we have both defined and undefined centers
    if len(defined_centers_found) == 0:
        content_passed = False
        content_details.append("No defined centers found")
    elif len(undefined_centers_found) == 0:
        content_passed = False
        content_details.append("No undefined centers found")
    else:
        # Test defined center content mentions "defined"
        defined_content_check = False
        for center in defined_centers_found[:1]:  # Check first defined center
            what_this_means = center.get("what_this_means", "").lower()
            if "defined" in what_this_means:
                defined_content_check = True
                break
        
        if not defined_content_check:
            content_passed = False
            content_details.append("Defined center content doesn't mention 'defined'")
        
        # Test undefined center content mentions "undefined"
        undefined_content_check = False
        for center in undefined_centers_found[:1]:  # Check first undefined center
            what_this_means = center.get("what_this_means", "").lower()
            if "undefined" in what_this_means:
                undefined_content_check = True
                break
        
        if not undefined_content_check:
            content_passed = False
            content_details.append("Undefined center content doesn't mention 'undefined'")
    
    if content_passed:
        log_test_result("Defined vs Undefined Content Test", True, 
                       f"Found {len(defined_centers_found)} defined and {len(undefined_centers_found)} undefined centers with appropriate content")
    else:
        log_test_result("Defined vs Undefined Content Test", False, "; ".join(content_details))
        return False
    
    # Additional Analysis
    print(f"\n📊 DETAILED ANALYSIS:")
    print(f"Total Centers: {len(centers)}")
    print(f"Defined Centers: {len(defined_centers_found)}")
    print(f"Undefined Centers: {len(undefined_centers_found)}")
    
    print(f"\nDefined Centers:")
    for center in defined_centers_found:
        gates = center.get("gates_present", [])
        print(f"  - {center.get('display_name', center.get('center_name'))}: {len(gates)} gates {gates}")
    
    print(f"\nUndefined Centers:")
    for center in undefined_centers_found:
        gates = center.get("gates_present", [])
        print(f"  - {center.get('display_name', center.get('center_name'))}: {len(gates)} gates {gates}")
    
    # Sample content check
    print(f"\n📝 SAMPLE CONTENT CHECK:")
    if defined_centers_found:
        sample_defined = defined_centers_found[0]
        print(f"Sample Defined Center ({sample_defined.get('display_name')}):")
        print(f"  What This Means: {sample_defined.get('what_this_means', '')[:100]}...")
        
    if undefined_centers_found:
        sample_undefined = undefined_centers_found[0]
        print(f"Sample Undefined Center ({sample_undefined.get('display_name')}):")
        print(f"  What This Means: {sample_undefined.get('what_this_means', '')[:100]}...")
    
    return True

def main():
    """Run all Human Design Centers tests."""
    print("Starting Human Design Centers Endpoint Testing...")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    
    success = test_human_design_centers_endpoint()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED - Human Design Centers endpoint is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - See details above")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    main()