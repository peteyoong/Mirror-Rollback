#!/usr/bin/env python3
"""
Backend API Testing Script for BaZi Today API and Related Endpoints
Testing the new BaZi Today API endpoint and verifying existing endpoints still work.
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://mirror-diagnosis.preview.emergentagent.com"
TEST_USER_ID = "697f0c6abf35c0528ff06954"  # pete@pulsifi.me

def test_bazi_today_endpoint():
    """Test the new BaZi Today API endpoint"""
    print("🧪 TESTING: BaZi Today API Endpoint")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/api/bazi/{TEST_USER_ID}/today"
    print(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"Response Size: {len(response.text)} characters")
        
        # Test 1: Basic response structure
        required_fields = ["success", "user_id", "date", "today_tone", "what_is_active", 
                          "where_it_lands", "what_to_watch", "what_helps_now", "pattern_link"]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
        
        print("✅ All required top-level fields present")
        
        # Test 2: success field
        if data.get("success") != True:
            print(f"❌ FAILED: success should be true, got {data.get('success')}")
            return False
        print("✅ success: true")
        
        # Test 3: today_tone structure
        today_tone = data.get("today_tone", {})
        tone_fields = ["element", "stem", "branch", "meaning"]
        missing_tone_fields = [f for f in tone_fields if f not in today_tone]
        if missing_tone_fields:
            print(f"❌ FAILED: Missing today_tone fields: {missing_tone_fields}")
            return False
        print(f"✅ today_tone object complete: element={today_tone.get('element')}, stem={today_tone.get('stem')}, branch={today_tone.get('branch')}")
        
        # Test 4: what_is_active structure
        what_is_active = data.get("what_is_active", {})
        active_fields = ["ten_gods", "interactions", "strength_shift", "element_balance"]
        missing_active_fields = [f for f in active_fields if f not in what_is_active]
        if missing_active_fields:
            print(f"❌ FAILED: Missing what_is_active fields: {missing_active_fields}")
            return False
        
        # Verify ten_gods is an array
        if not isinstance(what_is_active.get("ten_gods"), list):
            print(f"❌ FAILED: ten_gods should be array, got {type(what_is_active.get('ten_gods'))}")
            return False
        
        # Verify interactions is an array
        if not isinstance(what_is_active.get("interactions"), list):
            print(f"❌ FAILED: interactions should be array, got {type(what_is_active.get('interactions'))}")
            return False
        
        print(f"✅ what_is_active object complete: ten_gods={len(what_is_active.get('ten_gods', []))} items, interactions={len(what_is_active.get('interactions', []))} items")
        
        # Test 5: where_it_lands structure
        where_it_lands = data.get("where_it_lands", {})
        lands_fields = ["implication", "behavioral_hint"]
        missing_lands_fields = [f for f in lands_fields if f not in where_it_lands]
        if missing_lands_fields:
            print(f"❌ FAILED: Missing where_it_lands fields: {missing_lands_fields}")
            return False
        print("✅ where_it_lands object complete")
        
        # Test 6: what_to_watch structure
        what_to_watch = data.get("what_to_watch", {})
        watch_fields = ["pressure_points", "risk_note"]
        missing_watch_fields = [f for f in watch_fields if f not in what_to_watch]
        if missing_watch_fields:
            print(f"❌ FAILED: Missing what_to_watch fields: {missing_watch_fields}")
            return False
        
        # Verify pressure_points is an array
        if not isinstance(what_to_watch.get("pressure_points"), list):
            print(f"❌ FAILED: pressure_points should be array, got {type(what_to_watch.get('pressure_points'))}")
            return False
        
        print(f"✅ what_to_watch object complete: pressure_points={len(what_to_watch.get('pressure_points', []))} items")
        
        # Test 7: what_helps_now structure
        what_helps_now = data.get("what_helps_now", {})
        helps_fields = ["practical", "element_support"]
        missing_helps_fields = [f for f in helps_fields if f not in what_helps_now]
        if missing_helps_fields:
            print(f"❌ FAILED: Missing what_helps_now fields: {missing_helps_fields}")
            return False
        print("✅ what_helps_now object complete")
        
        # Test 8: pattern_link is string
        if not isinstance(data.get("pattern_link"), str):
            print(f"❌ FAILED: pattern_link should be string, got {type(data.get('pattern_link'))}")
            return False
        print("✅ pattern_link string present")
        
        # Test 9: user_id matches
        if data.get("user_id") != TEST_USER_ID:
            print(f"❌ FAILED: user_id mismatch, expected {TEST_USER_ID}, got {data.get('user_id')}")
            return False
        print("✅ user_id matches")
        
        # Test 10: date is today's date
        today_date = datetime.now().strftime("%Y-%m-%d")
        if data.get("date") != today_date:
            print(f"⚠️  WARNING: date is {data.get('date')}, expected {today_date} (may be timezone difference)")
        else:
            print("✅ date is today")
        
        print("\n📊 SAMPLE DATA:")
        print(f"Element: {today_tone.get('element')}")
        print(f"Stem/Branch: {today_tone.get('stem')}/{today_tone.get('branch')}")
        print(f"Meaning: {today_tone.get('meaning')}")
        print(f"Ten Gods Active: {what_is_active.get('ten_gods')}")
        print(f"Interactions: {what_is_active.get('interactions')}")
        print(f"Implication: {where_it_lands.get('implication')}")
        print(f"Pattern Link: {data.get('pattern_link')}")
        
        print("\n✅ BaZi Today API endpoint test PASSED")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: JSON decode error: {e}")
        print(f"Response text: {response.text}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def test_pattern_diagnosis_endpoint():
    """Test the cross-lens diagnosis endpoint"""
    print("\n🧪 TESTING: Cross-Lens Pattern Diagnosis Endpoint")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/api/pattern-diagnosis/{TEST_USER_ID}"
    print(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"Response Size: {len(response.text)} characters")
        
        # Basic structure check
        required_fields = ["pattern_title", "what_is_happening", "evidence"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
        
        print("✅ Cross-lens diagnosis endpoint working")
        print(f"Pattern: {data.get('pattern_title', 'N/A')}")
        print(f"What's happening: {data.get('what_is_happening', 'N/A')[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error testing pattern diagnosis: {e}")
        return False

def test_bazi_full_endpoint():
    """Test the BaZi full endpoint"""
    print("\n🧪 TESTING: BaZi Full Endpoint")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/api/bazi/{TEST_USER_ID}/full"
    print(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"Response Size: {len(response.text)} characters")
        
        # Basic structure check
        required_fields = ["success", "user_id", "chart"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
        
        if data.get("success") != True:
            print(f"❌ FAILED: success should be true, got {data.get('success')}")
            return False
        
        print("✅ BaZi full endpoint working")
        chart = data.get('chart', {})
        print(f"Day Master: {chart.get('day_master', 'N/A')}")
        print(f"Chart has {len(chart.get('pillars', []))} pillars")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error testing BaZi full: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING BACKEND API TESTS")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("=" * 80)
    
    results = []
    
    # Test 1: BaZi Today API (main focus)
    results.append(("BaZi Today API", test_bazi_today_endpoint()))
    
    # Test 2: Cross-lens diagnosis (verification)
    results.append(("Pattern Diagnosis API", test_pattern_diagnosis_endpoint()))
    
    # Test 3: BaZi Full (verification)
    results.append(("BaZi Full API", test_bazi_full_endpoint()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())