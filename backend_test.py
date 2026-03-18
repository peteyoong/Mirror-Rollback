#!/usr/bin/env python3

"""
BaZi V2 API Endpoint Testing
Test the new BaZi V2 API endpoint: GET /api/bazi/{user_id}/full
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://home-screen-overhaul.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

def test_bazi_v2_full_endpoint():
    """
    Test the BaZi V2 full endpoint with comprehensive validation.
    
    Expected values for this user (Xin Metal Day Master):
    - day_master.element should be "Metal"
    - day_master.stem_pinyin should be "Xin"
    - day_master.strength should be "strong"
    - timing.today.interaction should be one of: "supporting", "pressure", "mixed"
    - timing.year.interaction should be "pressure" (because Fire controls Metal)
    """
    print("🧪 TESTING: BaZi V2 Full Endpoint")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/bazi/{TEST_USER_ID}/full"
    print(f"📍 URL: {url}")
    print(f"🆔 User ID: {TEST_USER_ID}")
    print()
    
    try:
        # Make the API request
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response - {e}")
            print(f"Raw response: {response.text[:500]}")
            return False
        
        # Start validation
        test_results = []
        
        # 1. Basic response structure
        print("\n1️⃣  BASIC RESPONSE STRUCTURE:")
        success_check = validate_basic_response(data, test_results)
        
        # 2. Chart object validation
        print("\n2️⃣  CHART OBJECT VALIDATION:")
        chart_check = validate_chart_structure(data, test_results)
        
        # 3. Day Master validation
        print("\n3️⃣  DAY MASTER VALIDATION:")
        day_master_check = validate_day_master(data, test_results)
        
        # 4. Pillars validation
        print("\n4️⃣  PILLARS VALIDATION:")
        pillars_check = validate_pillars(data, test_results)
        
        # 5. Elements validation
        print("\n5️⃣  ELEMENTS VALIDATION:")
        elements_check = validate_elements(data, test_results)
        
        # 6. Ten Gods Summary validation
        print("\n6️⃣  TEN GODS SUMMARY VALIDATION:")
        ten_gods_check = validate_ten_gods_summary(data, test_results)
        
        # 7. Structure Summary validation
        print("\n7️⃣  STRUCTURE SUMMARY VALIDATION:")
        structure_check = validate_structure_summary(data, test_results)
        
        # 8. Timing validation
        print("\n8️⃣  TIMING VALIDATION:")
        timing_check = validate_timing(data, test_results)
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! BaZi V2 Full endpoint is working correctly.")
            return True
        else:
            print("❌ SOME TESTS FAILED. See details above.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Network error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_basic_response(data: Dict[str, Any], test_results: list) -> bool:
    """Validate basic response structure."""
    # Check success field
    if data.get("success") is True:
        print("  ✅ success: true")
        test_results.append(True)
    else:
        print(f"  ❌ success: Expected true, got {data.get('success')}")
        test_results.append(False)
    
    # Check chart object exists
    if "chart" in data and isinstance(data["chart"], dict):
        print("  ✅ chart object: present and is dict")
        test_results.append(True)
    else:
        print(f"  ❌ chart object: Missing or invalid type")
        test_results.append(False)
    
    return all(test_results[-2:])

def validate_chart_structure(data: Dict[str, Any], test_results: list) -> bool:
    """Validate chart structure has all required fields."""
    chart = data.get("chart", {})
    required_fields = ["day_master", "pillars", "elements", "ten_gods_summary", "structure_summary", "timing"]
    
    for field in required_fields:
        if field in chart:
            print(f"  ✅ {field}: present")
            test_results.append(True)
        else:
            print(f"  ❌ {field}: missing")
            test_results.append(False)
    
    return all(test_results[-len(required_fields):])

def validate_day_master(data: Dict[str, Any], test_results: list) -> bool:
    """Validate day_master structure and expected values."""
    day_master = data.get("chart", {}).get("day_master", {})
    
    # Required fields
    required_fields = ["stem_pinyin", "element", "polarity", "strength", "keywords", "description", "strength_description"]
    for field in required_fields:
        if field in day_master:
            print(f"  ✅ {field}: present")
            test_results.append(True)
        else:
            print(f"  ❌ {field}: missing")
            test_results.append(False)
    
    # Expected values for this user (Xin Metal Day Master)
    expected_values = {
        "element": "Metal",
        "stem_pinyin": "Xin",
        "strength": "strong"
    }
    
    for field, expected in expected_values.items():
        actual = day_master.get(field)
        if actual == expected:
            print(f"  ✅ {field}: {actual} (matches expected)")
            test_results.append(True)
        else:
            print(f"  ❌ {field}: {actual} (expected {expected})")
            test_results.append(False)
    
    return all(test_results[-len(required_fields) - len(expected_values):])

def validate_pillars(data: Dict[str, Any], test_results: list) -> bool:
    """Validate pillars structure."""
    pillars = data.get("chart", {}).get("pillars", {})
    required_pillars = ["year", "month", "day", "hour"]
    
    for pillar_name in required_pillars:
        pillar = pillars.get(pillar_name, {})
        if pillar:
            # Check required fields for each pillar
            required_fields = ["animal_emoji", "animal_name", "meaning_label"]
            pillar_valid = True
            
            for field in required_fields:
                if field in pillar:
                    print(f"  ✅ {pillar_name}.{field}: present ({pillar.get(field)})")
                else:
                    print(f"  ❌ {pillar_name}.{field}: missing")
                    pillar_valid = False
            
            test_results.append(pillar_valid)
        else:
            print(f"  ❌ {pillar_name}: missing pillar")
            test_results.append(False)
    
    return all(test_results[-len(required_pillars):])

def validate_elements(data: Dict[str, Any], test_results: list) -> bool:
    """Validate elements structure."""
    elements = data.get("chart", {}).get("elements", {})
    
    # Check element values
    element_names = ["wood", "fire", "earth", "metal", "water"]
    for element in element_names:
        if element in elements and isinstance(elements[element], (int, float)):
            print(f"  ✅ {element}: {elements[element]} (numeric)")
            test_results.append(True)
        else:
            print(f"  ❌ {element}: missing or non-numeric")
            test_results.append(False)
    
    # Check analysis arrays
    analysis_fields = ["dominant", "weak", "supporting", "balancing"]
    for field in analysis_fields:
        if field in elements and isinstance(elements[field], list):
            print(f"  ✅ {field}: {elements[field]} (array)")
            test_results.append(True)
        else:
            print(f"  ❌ {field}: missing or not array")
            test_results.append(False)
    
    return all(test_results[-len(element_names) - len(analysis_fields):])

def validate_ten_gods_summary(data: Dict[str, Any], test_results: list) -> bool:
    """Validate ten_gods_summary structure."""
    ten_gods = data.get("chart", {}).get("ten_gods_summary", {})
    
    required_fields = ["dominant", "present"]
    for field in required_fields:
        if field in ten_gods and isinstance(ten_gods[field], list):
            print(f"  ✅ {field}: {ten_gods[field]} (array)")
            test_results.append(True)
        else:
            print(f"  ❌ {field}: missing or not array")
            test_results.append(False)
    
    return all(test_results[-len(required_fields):])

def validate_structure_summary(data: Dict[str, Any], test_results: list) -> bool:
    """Validate structure_summary structure."""
    structure = data.get("chart", {}).get("structure_summary", {})
    
    required_fields = ["season", "climate"]
    for field in required_fields:
        if field in structure:
            print(f"  ✅ {field}: {structure[field]}")
            test_results.append(True)
        else:
            print(f"  ❌ {field}: missing")
            test_results.append(False)
    
    return all(test_results[-len(required_fields):])

def validate_timing(data: Dict[str, Any], test_results: list) -> bool:
    """Validate timing structure and expected interactions."""
    timing = data.get("chart", {}).get("timing", {})
    
    timing_periods = ["today", "month", "year"]
    for period in timing_periods:
        period_data = timing.get(period, {})
        if period_data:
            # Check required fields
            required_fields = ["pillar", "ten_god", "ten_god_name", "interaction", "description"]
            period_valid = True
            
            for field in required_fields:
                if field in period_data:
                    value = period_data.get(field)
                    print(f"  ✅ {period}.{field}: {value}")
                else:
                    print(f"  ❌ {period}.{field}: missing")
                    period_valid = False
            
            # Special validation for interactions
            if "interaction" in period_data:
                interaction = period_data["interaction"]
                valid_interactions = ["supporting", "pressure", "mixed"]
                
                if period == "today" and interaction in valid_interactions:
                    print(f"  ✅ {period}.interaction: {interaction} (valid)")
                    test_results.append(True)
                elif period == "year" and interaction == "pressure":
                    print(f"  ✅ {period}.interaction: {interaction} (expected pressure)")
                    test_results.append(True)
                elif period == "year" and interaction != "pressure":
                    print(f"  ❌ {period}.interaction: {interaction} (expected pressure)")
                    test_results.append(False)
                else:
                    print(f"  ✅ {period}.interaction: {interaction}")
                    test_results.append(True)
            else:
                test_results.append(False)
            
            if period_valid:
                test_results.append(True)
            else:
                test_results.append(False)
        else:
            print(f"  ❌ {period}: missing timing data")
            test_results.append(False)
    
    return all(test_results[-6:])  # Last 6 results are from timing validation

if __name__ == "__main__":
    print("🚀 Starting BaZi V2 API Endpoint Testing...")
    print()
    
    success = test_bazi_v2_full_endpoint()
    
    if success:
        print("\n🎉 BaZi V2 Full endpoint testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ BaZi V2 Full endpoint testing failed!")
        sys.exit(1)