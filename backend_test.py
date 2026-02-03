#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror - Astrology Auto-Migration Feature
Testing the critical bug fix that ensures old/incomplete astrology charts are automatically migrated.
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://chart-repair-7.preview.emergentagent.com/api"

def test_astrology_auto_migration():
    """Test the Astrology Auto-Migration (BUG #1 Fix) feature"""
    print("=" * 80)
    print("TESTING: Astrology Auto-Migration (BUG #1 Fix)")
    print("=" * 80)
    
    test_results = {
        "migrated_user": False,
        "missing_timezone_user": False, 
        "complete_user": False,
        "summary_endpoint": False,
        "today_endpoint": False
    }
    
    # Test 1: Migrated User (should return success:true with computed ascendant)
    print("\n1. Testing Migrated User (69819f1a1e4549392d7cb6d1)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/astrology/deep-dive/69819f1a1e4549392d7cb6d1", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Check for success
            success = data.get("success", False)
            print(f"Success: {success}")
            
            if success:
                # Check ascendant is not "Unknown"
                core_placements = data.get("core_placements", {})
                ascendant = core_placements.get("ascendant", "Unknown")
                print(f"Ascendant: {ascendant}")
                
                # Check debug_stamp for migration info
                debug_stamp = data.get("debug_stamp", {})
                data_format = debug_stamp.get("data_format", "")
                houses_computed = debug_stamp.get("houses_computed", False)
                print(f"Data Format: {data_format}")
                print(f"Houses Computed: {houses_computed}")
                
                if ascendant != "Unknown" and data_format == "full_computed":
                    test_results["migrated_user"] = True
                    print("✅ PASS: Migrated user returns success with computed ascendant")
                else:
                    print(f"❌ FAIL: Ascendant is '{ascendant}' or data_format is '{data_format}'")
            else:
                print("❌ FAIL: Success is False")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 2: User Missing Timezone (should return success:false with clear error)
    print("\n2. Testing User Missing Timezone (6971cc4381beab3a8955b256)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/astrology/deep-dive/6971cc4381beab3a8955b256", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            success = data.get("success", True)  # Default True to catch failures
            error = data.get("error", "")
            print(f"Success: {success}")
            print(f"Error: {error}")
            
            if not success and ("MIGRATION_FAILED" in error or "missing" in error.lower() or "timezone" in error.lower()):
                test_results["missing_timezone_user"] = True
                print("✅ PASS: User with missing timezone returns success:false with clear error")
            else:
                print(f"❌ FAIL: Expected success:false with migration error, got success:{success}, error:'{error}'")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 3: Complete User (should return success:true)
    print("\n3. Testing Complete User (6971c81f2b40fd5ef501d375)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/astrology/deep-dive/6971c81f2b40fd5ef501d375", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            success = data.get("success", False)
            print(f"Success: {success}")
            
            if success:
                # Check core placements
                core_placements = data.get("core_placements", {})
                sun = core_placements.get("sun", "Unknown")
                moon = core_placements.get("moon", "Unknown")
                ascendant = core_placements.get("ascendant", "Unknown")
                
                print(f"Sun: {sun}")
                print(f"Moon: {moon}")
                print(f"Ascendant: {ascendant}")
                
                if sun != "Unknown" and moon != "Unknown" and ascendant != "Unknown":
                    test_results["complete_user"] = True
                    print("✅ PASS: Complete user returns success with all core placements")
                else:
                    print(f"❌ FAIL: Some core placements are 'Unknown'")
            else:
                print("❌ FAIL: Success is False")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 4: Summary Endpoint (should also auto-migrate)
    print("\n4. Testing Summary Endpoint Auto-Migration (69819f1a1e4549392d7cb6d1)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/astrology/summary/69819f1a1e4549392d7cb6d1", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Check if it returns valid JSON structure
            if "title" in data and "sections" in data:
                test_results["summary_endpoint"] = True
                print("✅ PASS: Summary endpoint returns valid JSON structure")
            else:
                print(f"❌ FAIL: Missing expected keys in response")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 5: Today Endpoint (should also auto-migrate)
    print("\n5. Testing Today Endpoint Auto-Migration (69819f1a1e4549392d7cb6d1)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/astrology/today/69819f1a1e4549392d7cb6d1", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Check if it returns valid JSON with today's date
            if "title" in data and "date" in data:
                today_str = datetime.now().strftime("%Y-%m-%d")
                response_date = data.get("date", "")
                print(f"Expected Date: {today_str}")
                print(f"Response Date: {response_date}")
                
                if today_str in response_date:
                    test_results["today_endpoint"] = True
                    print("✅ PASS: Today endpoint returns valid JSON with today's date")
                else:
                    print(f"❌ FAIL: Date mismatch or missing")
            else:
                print(f"❌ FAIL: Missing expected keys in response")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY - Astrology Auto-Migration")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Astrology Auto-Migration is working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Issues detected with Astrology Auto-Migration")
        return False

def test_other_backend_apis():
    """Test other backend APIs that don't need retesting but should be verified"""
    print("\n" + "=" * 80)
    print("QUICK VERIFICATION: Other Backend APIs")
    print("=" * 80)
    
    # Test Mirror Chat API
    print("\n1. Testing Mirror Chat API")
    print("-" * 40)
    
    try:
        payload = {
            "user_id": "69819f1a1e4549392d7cb6d1",
            "message": "How are you today?",
            "lens": None
        }
        
        response = requests.post(f"{BACKEND_URL}/mirror/chat", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data and "timestamp" in data:
                print("✅ Mirror Chat API working")
            else:
                print("❌ Mirror Chat API response format issue")
        else:
            print(f"❌ Mirror Chat API failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Mirror Chat API error: {str(e)}")
    
    # Test Location Search API
    print("\n2. Testing Location Search API")
    print("-" * 40)
    
    try:
        payload = {"query": "New York"}
        
        response = requests.post(f"{BACKEND_URL}/locations/search", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                print("✅ Location Search API working")
            else:
                print("❌ Location Search API no results")
        else:
            print(f"❌ Location Search API failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Location Search API error: {str(e)}")

if __name__ == "__main__":
    print("Project Mirror - Backend API Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main test focus: Astrology Auto-Migration
    migration_success = test_astrology_auto_migration()
    
    # Quick verification of other APIs
    test_other_backend_apis()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    
    if migration_success:
        print("✅ PRIMARY FOCUS: Astrology Auto-Migration is working correctly")
        sys.exit(0)
    else:
        print("❌ PRIMARY FOCUS: Astrology Auto-Migration has issues")
        sys.exit(1)