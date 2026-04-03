#!/usr/bin/env python3
"""
Backend Testing Script for Pattern Signals API Endpoint
Testing GET /api/pattern-signals/{user_id}
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Backend URL configuration
BACKEND_URL = "https://deployment-fix-25.preview.emergentagent.com/api"

# Test users from the review request
TEST_USERS = [
    {"email": "peter@test.com", "user_id": "6971c81f2b40fd5ef501d375"},
    {"email": "reflector@test.com", "user_id": "697f795f1a7a96aa35e283a3"},
    {"email": "astro@test.com", "user_id": "69bf56aebb8e08b219fbd9b5"}
]

def test_pattern_signals_endpoint(user_id: str, user_email: str):
    """Test the pattern signals endpoint for a specific user"""
    print(f"🧪 TESTING PATTERN SIGNALS ENDPOINT")
    print(f"User: {user_email} (ID: {user_id})")
    print(f"Endpoint: GET {BACKEND_URL}/pattern-signals/{user_id}")
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/pattern-signals/{user_id}", timeout=30)
        response_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        data = response.json()
        print(f"✅ SUCCESS: Endpoint returned 200 OK")
        
        # Check required fields from expected response structure
        required_fields = ["summary", "signals", "synthesis", "confidence"]
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
            
        print(f"✅ SUCCESS: All required fields present")
        
        # Validate field types and structure
        if not isinstance(data["summary"], str) or len(data["summary"].strip()) == 0:
            print(f"❌ FAILED: Summary should be non-empty string, got: {type(data['summary'])}")
            return False
        print(f"✅ SUCCESS: Summary field valid")
        
        if not isinstance(data["signals"], dict):
            print(f"❌ FAILED: Signals should be dict, got: {type(data['signals'])}")
            return False
        print(f"✅ SUCCESS: Signals field is dict")
        
        # Check signals structure - should contain astrology, human_design, pattern_history arrays
        expected_signal_types = ["astrology", "human_design", "pattern_history"]
        signals = data["signals"]
        
        for signal_type in expected_signal_types:
            if signal_type in signals:
                if not isinstance(signals[signal_type], list):
                    print(f"❌ FAILED: signals.{signal_type} should be array, got: {type(signals[signal_type])}")
                    return False
                
                # Check signal detail structure
                for i, signal in enumerate(signals[signal_type]):
                    if not isinstance(signal, dict):
                        print(f"❌ FAILED: Signal {i} in {signal_type} should be dict")
                        return False
                    
                    required_signal_fields = ["label", "meaning"]
                    for field in required_signal_fields:
                        if field not in signal:
                            print(f"❌ FAILED: Signal {i} in {signal_type} missing field: {field}")
                            return False
                    
                    if "strength" in signal and not isinstance(signal["strength"], (int, float)):
                        print(f"❌ FAILED: Signal {i} strength should be number")
                        return False
                
                print(f"✅ SUCCESS: {signal_type} signals structure valid ({len(signals[signal_type])} signals)")
        
        if not isinstance(data["synthesis"], str) or len(data["synthesis"].strip()) == 0:
            print(f"❌ FAILED: Synthesis should be non-empty string, got: {type(data['synthesis'])}")
            return False
        print(f"✅ SUCCESS: Synthesis field valid")
        
        if not isinstance(data["confidence"], (int, float)) or not (0.0 <= data["confidence"] <= 1.0):
            print(f"❌ FAILED: Confidence should be float between 0.0-1.0, got: {data['confidence']}")
            return False
        print(f"✅ SUCCESS: Confidence field valid: {data['confidence']}")
        
        # Optional pattern_history field
        if "pattern_history" in data and data["pattern_history"] is not None:
            if not isinstance(data["pattern_history"], str):
                print(f"❌ FAILED: pattern_history should be string or null, got: {type(data['pattern_history'])}")
                return False
            print(f"✅ SUCCESS: pattern_history field valid: {data['pattern_history']}")
        
        # Print response summary
        print(f"\n📊 RESPONSE SUMMARY:")
        print(f"   Summary: {data['summary'][:100]}{'...' if len(data['summary']) > 100 else ''}")
        print(f"   Signals:")
        for signal_type, signal_list in data["signals"].items():
            print(f"     {signal_type}: {len(signal_list)} signals")
            for signal in signal_list:
                strength_str = f" (strength: {signal.get('strength', 'N/A')})" if 'strength' in signal else ""
                print(f"       - {signal['label']}: {signal['meaning'][:50]}{'...' if len(signal['meaning']) > 50 else ''}{strength_str}")
        print(f"   Synthesis: {data['synthesis'][:100]}{'...' if len(data['synthesis']) > 100 else ''}")
        print(f"   Confidence: {data['confidence']}")
        if data.get("pattern_history"):
            print(f"   Pattern History: {data['pattern_history']}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def run_all_tests():
    """Run tests for all available test users"""
    print("🚀 STARTING PATTERN SIGNALS API ENDPOINT TESTING")
    print("=" * 70)
    
    test_results = []
    
    for user in TEST_USERS:
        print(f"\n{'='*70}")
        result = test_pattern_signals_endpoint(user["user_id"], user["email"])
        test_results.append((user["email"], result))
        
    # Summary
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for user_email, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {user_email}")
        
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Pattern Signals API is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Review the failures above")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)