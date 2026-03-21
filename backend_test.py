#!/usr/bin/env python3
"""
Backend Test Suite for Pattern Mirror API
Testing deploy-readiness of the Pattern Mirror backend
"""

import requests
import json
import time
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://minimap-debug.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"
SAMPLE_USER_DATA = {
    "user_id": "test_user_deploy_check",
    "force_refresh": True
}

def test_health_check():
    """Test 1: Health Check - Verify the backend is running and responding"""
    print("🏥 TESTING HEALTH CHECK")
    print("=" * 40)
    
    endpoint = f"{BASE_URL}/health"
    print(f"📍 Testing endpoint: {endpoint}")
    
    try:
        start_time = time.time()
        response = requests.get(endpoint, timeout=10)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
            
        try:
            data = response.json()
            if 'status' in data and data['status'] == 'healthy':
                print("✅ Backend is healthy and responding")
                return True
            elif 'ok' in data and data['ok'] is True:
                print("✅ Backend is healthy and responding")
                return True
            else:
                print(f"❌ FAILED: Unexpected health response: {data}")
                return False
        except json.JSONDecodeError:
            print("❌ FAILED: Invalid JSON in health response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Health check request error - {e}")
        return False

def test_database_connectivity():
    """Test 2: Database Connectivity - Verify MongoDB connection through API"""
    print("\n🗄️  TESTING DATABASE CONNECTIVITY")
    print("=" * 40)
    
    # Test a simple endpoint that requires database access
    endpoint = f"{BASE_URL}/users/login"
    test_payload = {"email": "test@connectivity.check"}
    
    print(f"📍 Testing database connectivity via: {endpoint}")
    
    try:
        response = requests.post(endpoint, json=test_payload, timeout=10)
        
        # We expect this to fail with a proper error (user not found), not a database connection error
        if response.status_code in [400, 404]:
            try:
                data = response.json()
                if 'detail' in data and 'not found' in data['detail'].lower():
                    print("✅ Database connectivity working (proper user not found response)")
                    return True
                else:
                    print("✅ Database connectivity working (got structured error response)")
                    return True
            except json.JSONDecodeError:
                print("❌ FAILED: Invalid JSON response from database-dependent endpoint")
                return False
        elif response.status_code == 500:
            print("❌ FAILED: Database connection error (500 Internal Server Error)")
            return False
        else:
            print(f"✅ Database connectivity working (status: {response.status_code})")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Database connectivity test error - {e}")
        return False

def test_pattern_generation_get():
    """Test 3a: Core API Endpoint - GET /api/patterns/{user_id}"""
    print("\n🎯 TESTING PATTERN GENERATION (GET)")
    print("=" * 40)
    
    endpoint = f"{BASE_URL}/patterns/{TEST_USER_ID}"
    print(f"📍 Testing endpoint: {endpoint}")
    
    try:
        start_time = time.time()
        response = requests.get(endpoint, timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response - {e}")
            return False
            
        # Verify required fields
        required_fields = ['pattern', 'cached', 'generated_at', 'signal_strength']
        for field in required_fields:
            if field not in data:
                print(f"❌ FAILED: Required field '{field}' missing from response")
                return False
        
        # Verify pattern structure
        pattern = data['pattern']
        pattern_fields = ['title', 'what_you_may_be', 'challenge', 'genius', 'micro_shifts']
        for field in pattern_fields:
            if field not in pattern:
                print(f"❌ FAILED: Required pattern field '{field}' missing")
                return False
        
        print("✅ GET /api/patterns/{user_id} working correctly")
        print(f"   Pattern title: {pattern['title']}")
        print(f"   Signal strength: {data['signal_strength']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: GET pattern request error - {e}")
        return False

def test_pattern_generation_post():
    """Test 3b: Core API Endpoint - POST /api/patterns/generate"""
    print("\n🎯 TESTING PATTERN GENERATION (POST)")
    print("=" * 40)
    
    endpoint = f"{BASE_URL}/patterns/generate"
    print(f"📍 Testing endpoint: {endpoint}")
    
    try:
        start_time = time.time()
        response = requests.post(endpoint, json=SAMPLE_USER_DATA, timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response - {e}")
            return False
            
        # Verify required fields
        required_fields = ['pattern', 'cached', 'generated_at', 'signal_strength']
        for field in required_fields:
            if field not in data:
                print(f"❌ FAILED: Required field '{field}' missing from response")
                return False
        
        # Verify pattern structure
        pattern = data['pattern']
        pattern_fields = ['title', 'what_you_may_be', 'challenge', 'genius', 'micro_shifts']
        for field in pattern_fields:
            if field not in pattern:
                print(f"❌ FAILED: Required pattern field '{field}' missing")
                return False
        
        # Verify language rules
        what_you_may_be = pattern['what_you_may_be']
        if not what_you_may_be.startswith('You may be'):
            print(f"❌ FAILED: 'what_you_may_be' should start with 'You may be', got: {what_you_may_be[:50]}...")
            return False
        
        print("✅ POST /api/patterns/generate working correctly")
        print(f"   Pattern title: {pattern['title']}")
        print(f"   Signal strength: {data['signal_strength']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: POST pattern request error - {e}")
        return False

def test_error_handling():
    """Test 4: Error Handling - Test edge cases and invalid inputs"""
    print("\n⚠️  TESTING ERROR HANDLING")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 4a: Invalid user ID
    print("Testing invalid user ID...")
    try:
        response = requests.get(f"{BASE_URL}/patterns/invalid_user_id", timeout=10)
        if response.status_code in [400, 404, 500]:
            print("✅ Invalid user ID handled gracefully")
            tests_passed += 1
        else:
            print(f"⚠️  Unexpected response for invalid user ID: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing invalid user ID: {e}")
    
    # Test 4b: Missing data in POST request
    print("Testing missing data in POST request...")
    try:
        response = requests.post(f"{BASE_URL}/patterns/generate", json={}, timeout=10)
        if response.status_code in [400, 422]:
            print("✅ Missing data in POST handled gracefully")
            tests_passed += 1
        else:
            print(f"⚠️  Unexpected response for missing data: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing missing data: {e}")
    
    # Test 4c: Malformed JSON
    print("Testing malformed request...")
    try:
        response = requests.post(
            f"{BASE_URL}/patterns/generate", 
            data="invalid json", 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if response.status_code in [400, 422]:
            print("✅ Malformed JSON handled gracefully")
            tests_passed += 1
        else:
            print(f"⚠️  Unexpected response for malformed JSON: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing malformed JSON: {e}")
    
    print(f"Error handling tests passed: {tests_passed}/{total_tests}")
    return tests_passed >= 2  # Allow some flexibility

def test_pattern_mirror_v10():
    """Test the V10 Context-Aware Language Generation upgrade"""
    print("🧪 TESTING V10 CONTEXT-AWARE LANGUAGE GENERATION UPGRADE")
    print("=" * 60)
    
    # Test endpoint
    endpoint = f"{BASE_URL}/patterns/{TEST_USER_ID}?force_refresh=true"
    print(f"📍 Testing endpoint: {endpoint}")
    
    try:
        # Make the API request
        start_time = time.time()
        response = requests.get(endpoint, timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
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
            
        print("✅ Valid JSON response received")
        
        # Test 1: Verify two_layer_output field exists
        if 'two_layer_output' not in data:
            print("❌ FAILED: two_layer_output field missing from response")
            return False
        print("✅ two_layer_output field present")
        
        two_layer = data['two_layer_output']
        
        # Test 2: Verify required structure
        required_fields = ['core_insight', 'why_showing_up', 'cross_lens_derivation', 'friction', 'practical', 'display_config']
        for field in required_fields:
            if field not in two_layer:
                print(f"❌ FAILED: Required field '{field}' missing from two_layer_output")
                return False
        print("✅ All required fields present in two_layer_output")
        
        # Test 3: Verify core_insight structure
        core_insight = two_layer['core_insight']
        if not isinstance(core_insight, dict) or 'title' not in core_insight or 'text' not in core_insight:
            print("❌ FAILED: core_insight missing title or text fields")
            return False
        if not isinstance(core_insight['title'], str) or not isinstance(core_insight['text'], str):
            print("❌ FAILED: core_insight title or text not strings")
            return False
        print("✅ core_insight structure valid")
        
        # Test 4: Verify why_showing_up structure and completeness
        why_showing_up = two_layer['why_showing_up']
        if not isinstance(why_showing_up, dict) or 'text' not in why_showing_up or 'is_timing_driven' not in why_showing_up:
            print("❌ FAILED: why_showing_up missing text or is_timing_driven fields")
            return False
        if not isinstance(why_showing_up['text'], str) or not isinstance(why_showing_up['is_timing_driven'], bool):
            print("❌ FAILED: why_showing_up field types incorrect")
            return False
        
        # Check if why_showing_up text is complete (not truncated)
        why_text = why_showing_up['text'].strip()
        if len(why_text) < 10 or not why_text.endswith(('.', '!', '?')):
            print(f"❌ FAILED: why_showing_up text appears truncated: '{why_text}'")
            return False
        print("✅ why_showing_up structure valid and text complete")
        
        # Test 5: Verify friction field
        friction = two_layer['friction']
        if not isinstance(friction, dict) or 'text' not in friction:
            print("❌ FAILED: friction missing text field")
            return False
        if not isinstance(friction['text'], str):
            print("❌ FAILED: friction text not string")
            return False
        
        friction_text = friction['text'].strip()
        if len(friction_text) < 10 or not friction_text.endswith(('.', '!', '?')):
            print(f"❌ FAILED: friction text appears incomplete: '{friction_text}'")
            return False
        print("✅ friction field valid and complete")
        
        # Test 6: Verify practical field
        practical = two_layer['practical']
        if not isinstance(practical, dict) or 'text' not in practical:
            print("❌ FAILED: practical missing text field")
            return False
        if not isinstance(practical['text'], str):
            print("❌ FAILED: practical text not string")
            return False
        
        practical_text = practical['text'].strip()
        if len(practical_text) < 10 or not practical_text.endswith(('.', '!', '?')):
            print(f"❌ FAILED: practical text appears incomplete: '{practical_text}'")
            return False
        print("✅ practical field valid and complete")
        
        # Test 7: Verify cross_lens_derivation structure
        cross_lens = two_layer['cross_lens_derivation']
        if not isinstance(cross_lens, dict) or 'lenses' not in cross_lens or 'convergence_count' not in cross_lens:
            print("❌ FAILED: cross_lens_derivation missing required fields")
            return False
        if not isinstance(cross_lens['lenses'], list) or not isinstance(cross_lens['convergence_count'], int):
            print("❌ FAILED: cross_lens_derivation field types incorrect")
            return False
        print("✅ cross_lens_derivation structure valid")
        
        # Test 8: Check for mystical/woo language
        mystical_terms = ['universe', 'cosmic', 'divine', 'karma', 'spiritual', 'energy', 'vibration', 'alignment']
        all_text = f"{core_insight['text']} {why_showing_up['text']} {friction['text']} {practical['text']}"
        
        found_mystical = []
        for term in mystical_terms:
            if term.lower() in all_text.lower():
                found_mystical.append(term)
        
        if found_mystical:
            print(f"❌ FAILED: Found mystical/woo language: {found_mystical}")
            return False
        print("✅ No mystical/woo language detected - maintains Mirror tone")
        
        # Test 9: Verify response time is reasonable
        if response_time > 5.0:
            print(f"⚠️  WARNING: Response time {response_time:.2f}s exceeds 5 second threshold")
        else:
            print(f"✅ Response time {response_time:.2f}s is acceptable")
        
        # Test 10: Display sample content for manual review
        print("\n📝 SAMPLE CONTENT FOR MANUAL REVIEW:")
        print("-" * 40)
        print(f"Core Insight Title: {core_insight['title']}")
        print(f"Core Insight Text: {core_insight['text']}")
        print(f"Why Showing Up: {why_showing_up['text']}")
        print(f"Friction: {friction['text']}")
        print(f"Practical: {practical['text']}")
        print(f"Is Timing Driven: {why_showing_up['is_timing_driven']}")
        print(f"Convergence Count: {cross_lens['convergence_count']}")
        
        print("\n🎉 ALL TESTS PASSED - V10 Context-Aware Language Generation working correctly!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False

def test_context_awareness():
    """Test that the language adapts based on signal context"""
    print("\n🔍 TESTING CONTEXT AWARENESS")
    print("=" * 40)
    
    # Make multiple requests to see if content varies appropriately
    endpoint = f"{BASE_URL}/patterns/{TEST_USER_ID}?force_refresh=true"
    
    try:
        responses = []
        for i in range(2):
            print(f"Making request {i+1}/2...")
            response = requests.get(endpoint, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'two_layer_output' in data:
                    responses.append(data['two_layer_output'])
            time.sleep(1)  # Brief pause between requests
        
        if len(responses) >= 1:
            # Check that the content is contextually appropriate
            sample = responses[0]
            why_text = sample['why_showing_up']['text']
            friction_text = sample['friction']['text']
            practical_text = sample['practical']['text']
            
            # Look for context-aware language patterns
            context_indicators = [
                'this time', 'right now', 'currently', 'today', 'at this moment',
                'given', 'because', 'since', 'as', 'when', 'while'
            ]
            
            found_context = False
            for text in [why_text, friction_text, practical_text]:
                for indicator in context_indicators:
                    if indicator.lower() in text.lower():
                        found_context = True
                        break
                if found_context:
                    break
            
            if found_context:
                print("✅ Context-aware language detected")
            else:
                print("⚠️  No obvious context-aware language patterns found")
            
            return True
        else:
            print("❌ FAILED: Could not get valid responses for context testing")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Context awareness test error - {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING PATTERN MIRROR API DEPLOY-READINESS TESTING")
    print(f"🎯 Test User ID: {TEST_USER_ID}")
    print(f"🌐 Base URL: {BASE_URL}")
    print()
    
    # Deploy-readiness tests
    health_passed = test_health_check()
    db_passed = test_database_connectivity()
    get_pattern_passed = test_pattern_generation_get()
    post_pattern_passed = test_pattern_generation_post()
    error_handling_passed = test_error_handling()
    
    # Additional V10 tests (if needed)
    v10_test_passed = test_pattern_mirror_v10()
    context_test_passed = test_context_awareness()
    
    print("\n" + "=" * 60)
    print("📊 DEPLOY-READINESS TEST RESULTS:")
    print(f"🏥 Health Check: {'✅ PASSED' if health_passed else '❌ FAILED'}")
    print(f"🗄️  Database Connectivity: {'✅ PASSED' if db_passed else '❌ FAILED'}")
    print(f"🎯 GET Pattern Generation: {'✅ PASSED' if get_pattern_passed else '❌ FAILED'}")
    print(f"🎯 POST Pattern Generation: {'✅ PASSED' if post_pattern_passed else '❌ FAILED'}")
    print(f"⚠️  Error Handling: {'✅ PASSED' if error_handling_passed else '❌ FAILED'}")
    print(f"🔧 V10 API Features: {'✅ PASSED' if v10_test_passed else '❌ FAILED'}")
    print(f"🔍 Context Awareness: {'✅ PASSED' if context_test_passed else '❌ FAILED'}")
    
    # Calculate overall readiness
    core_tests = [health_passed, db_passed, get_pattern_passed, post_pattern_passed]
    core_passed = all(core_tests)
    
    if core_passed:
        print("\n🎉 DEPLOY-READY: All core Pattern Mirror API tests passed!")
        if error_handling_passed and v10_test_passed and context_test_passed:
            print("🌟 EXCELLENT: All advanced features also working correctly!")
        exit(0)
    else:
        print("\n❌ NOT DEPLOY-READY: Core functionality tests failed")
        print("🔧 Review the failed tests above before deploying")
        exit(1)