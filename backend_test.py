#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror
Testing the Enneagram Traits Endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://trait-explorer-3.preview.emergentagent.com/api"

def test_enneagram_traits_endpoint():
    """Test the new Enneagram traits endpoint: GET /api/enneagram/traits/{user_id}"""
    
    print("=" * 80)
    print("TESTING ENNEAGRAM TRAITS ENDPOINT")
    print("=" * 80)
    
    # Test Case 1: User with Enneagram result
    print("\n1. Testing user WITH Enneagram result (69819f1a1e4549392d7cb6d1)")
    print("-" * 60)
    
    user_with_result = "69819f1a1e4549392d7cb6d1"
    url = f"{BACKEND_URL}/enneagram/traits/{user_with_result}"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response received: {len(json.dumps(data))} characters")
            
            # Validate response structure
            required_fields = ["cards", "source", "computed_details", "type", "wing"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ MISSING FIELDS: {missing_fields}")
                return False
            
            print(f"✅ All required fields present: {required_fields}")
            
            # Validate cards structure
            cards = data.get("cards", [])
            print(f"Number of cards: {len(cards)}")
            
            if len(cards) == 0:
                print("❌ Expected cards but got empty array")
                return False
            
            # Check each card structure
            for i, card in enumerate(cards):
                card_fields = ["card_id", "title", "body", "suggested_question"]
                missing_card_fields = [field for field in card_fields if field not in card]
                
                if missing_card_fields:
                    print(f"❌ Card {i+1} missing fields: {missing_card_fields}")
                    return False
                
                print(f"✅ Card {i+1}: {card['title'][:50]}...")
            
            # Validate computed_details
            computed_details = data.get("computed_details")
            if computed_details:
                expected_details = ["center", "hornevian_group", "harmonic_group", 
                                  "stress_line_to", "growth_line_to", "wing_balance_label"]
                missing_details = [field for field in expected_details if field not in computed_details]
                
                if missing_details:
                    print(f"⚠️  Missing computed_details fields: {missing_details}")
                else:
                    print("✅ All computed_details fields present")
            
            # Validate source
            source = data.get("source")
            valid_sources = ["static", "book", "none"]
            if source not in valid_sources:
                print(f"❌ Invalid source: {source}. Expected one of: {valid_sources}")
                return False
            
            print(f"✅ Valid source: {source}")
            
            # Validate type and wing
            enneagram_type = data.get("type")
            wing = data.get("wing")
            
            if not isinstance(enneagram_type, int) or enneagram_type < 1 or enneagram_type > 9:
                print(f"❌ Invalid Enneagram type: {enneagram_type}")
                return False
            
            print(f"✅ Valid Enneagram type: {enneagram_type}")
            
            if wing is not None and wing != "balanced":
                if not isinstance(wing, int) or wing < 1 or wing > 9:
                    print(f"❌ Invalid wing: {wing}")
                    return False
            
            print(f"✅ Valid wing: {wing}")
            
            print("✅ TEST 1 PASSED: User with Enneagram result")
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    # Test Case 2: User without Enneagram result (create a fresh user ID)
    print("\n2. Testing user WITHOUT Enneagram result")
    print("-" * 60)
    
    # Use a non-existent user ID
    user_without_result = "000000000000000000000000"
    url = f"{BACKEND_URL}/enneagram/traits/{user_without_result}"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response received: {len(json.dumps(data))} characters")
            
            # Validate expected response for user without result
            expected_fields = ["cards", "source", "message", "computed_details"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"❌ MISSING FIELDS: {missing_fields}")
                return False
            
            # Check that cards is empty
            cards = data.get("cards", [])
            if len(cards) != 0:
                print(f"❌ Expected empty cards array, got {len(cards)} cards")
                return False
            
            print("✅ Cards array is empty as expected")
            
            # Check source is "none"
            source = data.get("source")
            if source != "none":
                print(f"❌ Expected source 'none', got '{source}'")
                return False
            
            print("✅ Source is 'none' as expected")
            
            # Check message is present
            message = data.get("message")
            if not message or "Complete the Enneagram assessment" not in message:
                print(f"❌ Expected assessment completion message, got: {message}")
                return False
            
            print("✅ Appropriate message for incomplete assessment")
            
            # Check computed_details is None
            computed_details = data.get("computed_details")
            if computed_details is not None:
                print(f"❌ Expected computed_details to be None, got: {computed_details}")
                return False
            
            print("✅ computed_details is None as expected")
            print("✅ TEST 2 PASSED: User without Enneagram result")
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    # Test Case 3: Invalid user ID
    print("\n3. Testing INVALID user ID")
    print("-" * 60)
    
    invalid_user_id = "invalid_user_id_format"
    url = f"{BACKEND_URL}/enneagram/traits/{invalid_user_id}"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        # Should handle gracefully - either 400, 404, or 500 with error message
        if response.status_code in [400, 404, 500]:
            print("✅ Graceful error handling for invalid user ID")
            print("✅ TEST 3 PASSED: Invalid user ID handled gracefully")
        elif response.status_code == 200:
            # If it returns 200, it should return empty result
            data = response.json()
            cards = data.get("cards", [])
            source = data.get("source")
            
            if len(cards) == 0 and source == "none":
                print("✅ Invalid user ID treated as user without result")
                print("✅ TEST 3 PASSED: Invalid user ID handled gracefully")
            else:
                print(f"❌ Unexpected response for invalid user ID: {data}")
                return False
        else:
            print(f"❌ Unexpected status code for invalid user ID: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    # Performance Test
    print("\n4. Testing RESPONSE TIME")
    print("-" * 60)
    
    start_time = datetime.now()
    try:
        response = requests.get(f"{BACKEND_URL}/enneagram/traits/{user_with_result}", timeout=30)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        print(f"Response time: {response_time:.2f} seconds")
        
        if response_time > 2.0:
            print("⚠️  Response time > 2 seconds (using static fallback should be faster)")
        else:
            print("✅ Response time acceptable (< 2 seconds)")
            
        print("✅ TEST 4 PASSED: Performance test completed")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("ALL ENNEAGRAM TRAITS ENDPOINT TESTS PASSED ✅")
    print("=" * 80)
    return True


def main():
    """Run all backend tests"""
    print("Starting Backend API Tests...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    success = test_enneagram_traits_endpoint()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()