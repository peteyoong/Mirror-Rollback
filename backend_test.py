#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror
Focus: Numerology Full Name Gate Fix Testing
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://mirror-daily.preview.emergentagent.com/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_questionnaire_persistence():
    """Test POST /api/profile/questionnaire - Questionnaire Persistence"""
    print("\n=== TESTING QUESTIONNAIRE PERSISTENCE API ===")
    
    print(f"\n1. Testing questionnaire persistence for user: {TEST_USER_ID}")
    payload = {
        "user_id": TEST_USER_ID,
        "answers": ["Answer1", "Answer2", "Answer3"],
        "questions": ["Q1", "Q2", "Q3"]
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/profile/questionnaire",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Request Payload: {json.dumps(payload, indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify expected response structure
            expected_success = True
            expected_answers_saved = 3
            
            if (data.get("success") == expected_success and 
                data.get("answers_saved") == expected_answers_saved):
                print("✅ Questionnaire persistence: SUCCESS")
                print(f"   - Response contains success={expected_success}")
                print(f"   - Response contains answers_saved={expected_answers_saved}")
                return True
            else:
                print("❌ Questionnaire persistence: FAILED")
                print(f"   - Expected: {{'success': {expected_success}, 'answers_saved': {expected_answers_saved}}}")
                print(f"   - Got: {data}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during questionnaire persistence test: {e}")
        return False


    """Test POST /api/reflection/chat endpoint"""
    print("\n=== TESTING REFLECTION CHAT API ===")
    
    # Test 1: Reflection chat with context
    print("\n1. Testing reflection chat WITH context...")
    payload_with_context = {
        "user_id": TEST_USER_ID,
        "messages": [{"role": "user", "content": "I feel restless today"}],
        "context": "Rest & Restoration"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/reflection/chat",
            json=payload_with_context,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Check for required response structure
            if "response" in data:
                response_text = data["response"]
                print(f"Response Text (first 200 chars): {response_text[:200]}...")
                
                # Check mirror philosophy compliance (no "you should", no advice)
                forbidden_phrases = ["you should", "you need to", "you must", "i recommend", "try to"]
                violations = [phrase for phrase in forbidden_phrases if phrase in response_text.lower()]
                
                if violations:
                    print(f"❌ MIRROR PHILOSOPHY VIOLATION: Found forbidden phrases: {violations}")
                    return False
                else:
                    print("✅ Mirror philosophy compliance: No prescriptive language found")
                
                print("✅ Reflection chat with context: SUCCESS")
                return True
            else:
                print(f"❌ Missing 'response' key in response: {data}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during reflection chat with context: {e}")
        return False
    
    # Test 2: Reflection chat without context
    print("\n2. Testing reflection chat WITHOUT context...")
    payload_without_context = {
        "user_id": TEST_USER_ID,
        "messages": [{"role": "user", "content": "Just checking in"}],
        "context": None
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/reflection/chat",
            json=payload_without_context,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                print("✅ Reflection chat without context: SUCCESS")
                return True
            else:
                print(f"❌ Missing 'response' key: {data}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during reflection chat without context: {e}")
        return False


def test_reflection_chat_api():
    """Test POST /api/reflection/chat endpoint"""
    print("\n=== TESTING REFLECTION CHAT API ===")
    
    # Test 1: Reflection chat with context
    print("\n1. Testing reflection chat WITH context...")
    payload_with_context = {
        "user_id": TEST_USER_ID,
        "messages": [{"role": "user", "content": "Testing"}],
        "context": "Self & Inner State"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/reflection/chat",
            json=payload_with_context,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Request Payload: {json.dumps(payload_with_context, indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Check for required response structure
            if "response" in data:
                response_text = data["response"]
                print(f"Response Text (first 200 chars): {response_text[:200]}...")
                
                # Check mirror philosophy compliance (no "you should", no advice)
                forbidden_phrases = ["you should", "you need to", "you must", "i recommend", "try to"]
                violations = [phrase for phrase in forbidden_phrases if phrase in response_text.lower()]
                
                if violations:
                    print(f"❌ MIRROR PHILOSOPHY VIOLATION: Found forbidden phrases: {violations}")
                    return False
                else:
                    print("✅ Mirror philosophy compliance: No prescriptive language found")
                
                print("✅ Reflection chat with context: SUCCESS")
                return True
            else:
                print(f"❌ Missing 'response' key in response: {data}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during reflection chat with context: {e}")
        return False


    """Test GET /api/daily-focus/{user_id} endpoint"""
    print("\n=== TESTING DAILY FOCUS API ===")
    
    print(f"\n1. Testing daily focus for user: {TEST_USER_ID}")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/daily-focus/{TEST_USER_ID}",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Check required fields
            required_fields = ["ambient_line", "context", "confidence", "generated_at_iso"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Validate field types and values
            ambient_line = data.get("ambient_line")
            context = data.get("context")
            confidence = data.get("confidence")
            generated_at_iso = data.get("generated_at_iso")
            
            print(f"Ambient Line: {ambient_line}")
            print(f"Context: {context}")
            print(f"Confidence: {confidence}")
            print(f"Generated At: {generated_at_iso}")
            
            # Validate context is one of the 6 allowed or null
            allowed_contexts = [
                "Self & Inner State", 
                "Relationships", 
                "Work & Purpose", 
                "Health & Body", 
                "Rest & Restoration", 
                "Growth & Expansion",
                None
            ]
            
            if context not in allowed_contexts:
                print(f"❌ Invalid context value: {context}. Must be one of {allowed_contexts}")
                return False
            
            # Validate confidence is a number
            if not isinstance(confidence, (int, float)):
                print(f"❌ Confidence must be a number, got: {type(confidence)}")
                return False
            
            # Validate generated_at_iso is a valid ISO string
            try:
                datetime.fromisoformat(generated_at_iso.replace('Z', '+00:00'))
            except ValueError:
                print(f"❌ Invalid ISO timestamp: {generated_at_iso}")
                return False
            
            print("✅ Daily focus API: SUCCESS - All required fields present and valid")
            
            # Test caching behavior - make same request again
            print("\n2. Testing caching behavior (same user, same day)...")
            response2 = requests.get(
                f"{BACKEND_URL}/daily-focus/{TEST_USER_ID}",
                timeout=30
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                
                # Check if responses are identical (cached)
                if data == data2:
                    print("✅ Caching working: Same response returned for same user/day")
                    return True
                else:
                    print("⚠️  Caching may not be working: Different responses for same user/day")
                    print(f"First response generated_at: {data.get('generated_at_iso')}")
                    print(f"Second response generated_at: {data2.get('generated_at_iso')}")
                    return True  # Still consider success as core functionality works
            else:
                print(f"❌ Second request failed: {response2.status_code}")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during daily focus test: {e}")
        return False



def test_daily_focus_api():
    """Test GET /api/daily-focus/{user_id} endpoint"""
    print("\n=== TESTING DAILY FOCUS API ===")
    
    print(f"\n1. Testing daily focus for user: {TEST_USER_ID}")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/daily-focus/{TEST_USER_ID}",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check required fields
            required_fields = ["ambient_line", "context", "confidence", "generated_at_iso"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Validate field types and values
            ambient_line = data.get("ambient_line")
            context = data.get("context")
            confidence = data.get("confidence")
            generated_at_iso = data.get("generated_at_iso")
            
            print(f"Ambient Line: {ambient_line}")
            print(f"Context: {context}")
            print(f"Confidence: {confidence}")
            print(f"Generated At: {generated_at_iso}")
            
            # Validate context is one of the 6 allowed or null
            allowed_contexts = [
                "Self & Inner State", 
                "Relationships", 
                "Work & Purpose", 
                "Health & Body", 
                "Rest & Restoration", 
                "Growth & Expansion",
                None
            ]
            
            if context not in allowed_contexts:
                print(f"❌ Invalid context value: {context}. Must be one of {allowed_contexts}")
                return False
            
            # Validate confidence is a number
            if not isinstance(confidence, (int, float)):
                print(f"❌ Confidence must be a number, got: {type(confidence)}")
                return False
            
            # Validate generated_at_iso is a valid ISO string
            try:
                datetime.fromisoformat(generated_at_iso.replace('Z', '+00:00'))
            except ValueError:
                print(f"❌ Invalid ISO timestamp: {generated_at_iso}")
                return False
            
            print("✅ Daily focus API: SUCCESS - All required fields present and valid")
            return True
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during daily focus test: {e}")
        return False

    """Run all backend tests"""
def main():
    """Run all backend tests"""
    print("🧪 STARTING BACKEND API TESTS")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: Questionnaire Persistence API
    questionnaire_success = test_questionnaire_persistence()
    results.append(("Questionnaire Persistence API", questionnaire_success))
    
    # Test 2: Reflection Chat API
    reflection_success = test_reflection_chat_api()
    results.append(("Reflection Chat API", reflection_success))
    
    # Test 3: Daily Focus API  
    daily_focus_success = test_daily_focus_api()
    results.append(("Daily Focus API", daily_focus_success))
    
    # Summary
    print("\n" + "="*60)
    print("🏁 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())