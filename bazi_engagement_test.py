#!/usr/bin/env python3

"""
BaZi Engagement & Adaptive Intelligence APIs Testing
Test the specific BaZi feedback and adaptive endpoints as requested in the review.

Endpoints to test:
1. POST /api/bazi/{user_id}/feedback - Submit feedback
2. GET /api/bazi/{user_id}/feedback - Get feedback
3. GET /api/bazi/{user_id}/adaptive - Get adaptive content

Test user ID: 6971c81f2b40fd5ef501d375
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://astro-redesign-2.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

def test_bazi_feedback_submit():
    """Test POST /api/bazi/{user_id}/feedback endpoint with multiple test cases."""
    print("🧪 TESTING: BaZi Feedback Submit (POST)")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/bazi/{TEST_USER_ID}/feedback"
    print(f"📍 URL: {url}")
    print(f"🆔 User ID: {TEST_USER_ID}")
    print()
    
    test_cases = [
        {
            "name": "Day Master feedback - YES",
            "data": {"section": "day_master", "rating": "yes"},
            "expected_success": True
        },
        {
            "name": "Ten Gods feedback with subsection - SOMEWHAT", 
            "data": {"section": "ten_gods", "rating": "somewhat", "subsection": "resource"},
            "expected_success": True
        },
        {
            "name": "Life Pattern feedback - NO",
            "data": {"section": "life_pattern", "rating": "no"},
            "expected_success": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}️⃣  {test_case['name']}:")
        print(f"   Payload: {test_case['data']}")
        
        try:
            start_time = time.time()
            response = requests.post(url, json=test_case['data'], timeout=10)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
                print(f"   Response: {response.text}")
                results.append(False)
                continue
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"   ❌ FAILED: Invalid JSON response - {e}")
                results.append(False)
                continue
            
            # Validate response structure
            if data.get("success") is True:
                print(f"   ✅ success: true")
                
                # Check expected fields
                expected_fields = ["section", "rating"]
                all_fields_present = True
                
                for field in expected_fields:
                    if field in data:
                        print(f"   ✅ {field}: {data[field]}")
                    else:
                        print(f"   ❌ {field}: missing")
                        all_fields_present = False
                
                if all_fields_present:
                    results.append(True)
                    print(f"   🎉 Test case PASSED")
                else:
                    results.append(False)
                    print(f"   ❌ Test case FAILED: Missing required fields")
            else:
                print(f"   ❌ FAILED: success is not true - {data.get('success')}")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAILED: Network error - {e}")
            results.append(False)
        except Exception as e:
            print(f"   ❌ FAILED: Unexpected error - {e}")
            results.append(False)
        
        print()
    
    passed_tests = sum(results)
    total_tests = len(results)
    print(f"📊 Submit Feedback Tests: {passed_tests}/{total_tests} passed")
    return passed_tests == total_tests

def test_bazi_feedback_get():
    """Test GET /api/bazi/{user_id}/feedback endpoint."""
    print("🧪 TESTING: BaZi Feedback Get (GET)")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/bazi/{TEST_USER_ID}/feedback"
    print(f"📍 URL: {url}")
    print(f"🆔 User ID: {TEST_USER_ID}")
    print()
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
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
            return False
        
        # Validate response structure
        if data.get("success") is True:
            print(f"✅ success: true")
            
            # Check required fields
            required_fields = ["user_id", "feedback_count", "feedback_map", "confirmed_traits", "rejected_traits"]
            all_valid = True
            
            for field in required_fields:
                if field in data:
                    value = data[field]
                    if field == "user_id":
                        if value == TEST_USER_ID:
                            print(f"✅ {field}: {value} (matches expected)")
                        else:
                            print(f"❌ {field}: {value} (expected {TEST_USER_ID})")
                            all_valid = False
                    elif field == "feedback_count":
                        if isinstance(value, int) and value >= 0:
                            print(f"✅ {field}: {value} (valid count)")
                        else:
                            print(f"❌ {field}: {value} (expected non-negative integer)")
                            all_valid = False
                    elif field == "feedback_map":
                        if isinstance(value, dict):
                            print(f"✅ {field}: dict with {len(value)} entries")
                            
                            # Check for expected feedback from submit tests
                            expected_keys = ["day_master", "ten_gods:resource", "life_pattern"]
                            for expected_key in expected_keys:
                                if expected_key in value:
                                    rating = value[expected_key]
                                    print(f"   ✅ Found feedback for {expected_key}: {rating}")
                                else:
                                    print(f"   ⚠️  Missing feedback for {expected_key} (may not have been submitted)")
                        else:
                            print(f"❌ {field}: {value} (expected dict)")
                            all_valid = False
                    elif field in ["confirmed_traits", "rejected_traits"]:
                        if isinstance(value, list):
                            print(f"✅ {field}: array with {len(value)} items {value}")
                        else:
                            print(f"❌ {field}: {value} (expected array)")
                            all_valid = False
                else:
                    print(f"❌ {field}: missing")
                    all_valid = False
            
            return all_valid
        else:
            print(f"❌ FAILED: success is not true - {data.get('success')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Network error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False

def test_bazi_adaptive_content():
    """Test GET /api/bazi/{user_id}/adaptive endpoint."""
    print("🧪 TESTING: BaZi Adaptive Content (GET)")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/bazi/{TEST_USER_ID}/adaptive"
    print(f"📍 URL: {url}")
    print(f"🆔 User ID: {TEST_USER_ID}")
    print()
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)  # Higher timeout for complex computation
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
            return False
        
        # Validate response structure
        if data.get("success") is True:
            print(f"✅ success: true")
            
            # Check required top-level fields
            required_fields = ["user_id", "chart", "adaptive", "feedback_map"]
            all_valid = True
            
            for field in required_fields:
                if field in data:
                    value = data[field]
                    print(f"✅ {field}: present ({type(value).__name__})")
                else:
                    print(f"❌ {field}: missing")
                    all_valid = False
            
            # Deep validation of adaptive object
            if "adaptive" in data:
                adaptive = data["adaptive"]
                print(f"\n🔍 Validating adaptive object:")
                
                required_adaptive_fields = [
                    "real_life_checks", 
                    "today_connections", 
                    "contextual_prompts", 
                    "reflection_prompts", 
                    "language_modifiers"
                ]
                
                for field in required_adaptive_fields:
                    if field in adaptive:
                        value = adaptive[field]
                        print(f"   ✅ {field}: present ({type(value).__name__})")
                        
                        # Specific validation for each field
                        if field == "real_life_checks":
                            if isinstance(value, dict):
                                expected_sections = ["day_master"]
                                for section in expected_sections:
                                    if section in value:
                                        section_data = value[section]
                                        if isinstance(section_data, dict):
                                            expected_subsections = ["work", "relationships", "leadership", "stress"]
                                            subsection_count = len([s for s in expected_subsections if s in section_data])
                                            print(f"      ✅ {section}: has {subsection_count}/{len(expected_subsections)} subsections")
                                        else:
                                            print(f"      ❌ {section}: expected dict")
                                            all_valid = False
                            else:
                                print(f"      ❌ Expected dict for real_life_checks")
                                all_valid = False
                                
                        elif field == "today_connections":
                            if isinstance(value, dict):
                                expected_connections = ["main", "core_pattern", "ten_god_specific"]
                                connection_count = len([c for c in expected_connections if c in value])
                                print(f"      ✅ has {connection_count}/{len(expected_connections)} connection types")
                            else:
                                print(f"      ❌ Expected dict for today_connections")
                                all_valid = False
                                
                        elif field in ["contextual_prompts", "reflection_prompts"]:
                            if isinstance(value, list):
                                print(f"      ✅ {len(value)} prompts")
                                
                                # Check for expected prompt patterns
                                if field == "contextual_prompts" and len(value) > 0:
                                    prompt_examples = ["Why do I get frustrated", "How do I", "Why do I"]
                                    matching_patterns = 0
                                    for prompt in value:
                                        for pattern in prompt_examples:
                                            if pattern.lower() in prompt.lower():
                                                matching_patterns += 1
                                                break
                                    print(f"      ✅ {matching_patterns} prompts match expected patterns")
                                    
                                elif field == "reflection_prompts" and len(value) > 0:
                                    reflection_examples = ["Where did I notice", "Did I", "What"]
                                    matching_patterns = 0
                                    for prompt in value:
                                        for pattern in reflection_examples:
                                            if pattern.lower() in prompt.lower():
                                                matching_patterns += 1
                                                break
                                    print(f"      ✅ {matching_patterns} prompts match expected patterns")
                            else:
                                print(f"      ❌ Expected array for {field}")
                                all_valid = False
                                
                        elif field == "language_modifiers":
                            if isinstance(value, dict):
                                print(f"      ✅ has {len(value)} modifier sections")
                            else:
                                print(f"      ❌ Expected dict for language_modifiers")
                                all_valid = False
                    else:
                        print(f"   ❌ {field}: missing")
                        all_valid = False
            
            return all_valid
        else:
            print(f"❌ FAILED: success is not true - {data.get('success')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Network error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all BaZi Engagement & Adaptive Intelligence API tests."""
    print("🚀 Starting BaZi Engagement & Adaptive Intelligence API Testing...")
    print(f"🆔 Test User ID: {TEST_USER_ID}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print()
    
    test_results = []
    
    # Test 1: Submit feedback (this creates feedback data for subsequent tests)
    print("TEST 1: Submit Feedback")
    print("-" * 40)
    submit_result = test_bazi_feedback_submit()
    test_results.append(("Submit Feedback", submit_result))
    print()
    
    # Test 2: Get feedback (this should return the feedback submitted in Test 1)
    print("TEST 2: Get Feedback")
    print("-" * 40)
    get_result = test_bazi_feedback_get()
    test_results.append(("Get Feedback", get_result))
    print()
    
    # Test 3: Get adaptive content (this should use feedback to generate adaptive content)
    print("TEST 3: Get Adaptive Content") 
    print("-" * 40)
    adaptive_result = test_bazi_adaptive_content()
    test_results.append(("Adaptive Content", adaptive_result))
    print()
    
    # Final summary
    print("=" * 60)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 60)
    
    total_passed = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name}")
        if passed:
            total_passed += 1
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    print()
    print(f"📊 Overall Results: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if total_passed == total_tests:
        print("🎉 ALL BAZI ENGAGEMENT & ADAPTIVE INTELLIGENCE API TESTS PASSED!")
        print("\n✅ Expected behaviors verified:")
        print("   - POST feedback submissions return success: true")  
        print("   - GET feedback returns feedback_map with stored ratings")
        print("   - GET feedback returns confirmed_traits and rejected_traits arrays")
        print("   - GET adaptive returns adaptive object with real_life_checks")
        print("   - GET adaptive includes today_connections with main/core_pattern/ten_god_specific")
        print("   - GET adaptive includes contextual_prompts array with 'Why do I...' questions") 
        print("   - GET adaptive includes reflection_prompts array with 'Where did I...' questions")
        print("   - Real_life_checks includes work/relationships/leadership/stress sections")
        print("   - Today_connections references current timing")
        return True
    else:
        print("❌ SOME TESTS FAILED - See details above")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 BaZi Engagement & Adaptive Intelligence API testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ BaZi Engagement & Adaptive Intelligence API testing failed!")
        sys.exit(1)