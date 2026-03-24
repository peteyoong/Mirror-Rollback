#!/usr/bin/env python3
"""
Backend Testing Script for Reflector Journal Synthesis Endpoint
Tests the GET /api/journal/{user_id}/reflector-synthesis endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://lunar-cycle-mirror.preview.emergentagent.com/api"

def test_reflector_synthesis_endpoint():
    """Test the Reflector Journal Synthesis endpoint comprehensively"""
    
    print("🧪 TESTING REFLECTOR JOURNAL SYNTHESIS ENDPOINT")
    print("=" * 60)
    
    # Test cases from review request
    test_cases = [
        {
            "name": "Reflector user with NO journal entries",
            "user_id": "697f795f1a7a96aa35e283a3",
            "expected_has_enough_data": False,
            "expected_message_present": True,
            "expected_synthesis_null": True
        },
        {
            "name": "User with journal entries (Peter)",
            "user_id": "6971c81f2b40fd5ef501d375",
            "expected_has_enough_data": None,  # Will depend on actual data
            "expected_message_present": None,
            "expected_synthesis_null": None
        }
    ]
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 TEST {i}: {test_case['name']}")
        print(f"User ID: {test_case['user_id']}")
        
        try:
            # Make request to endpoint
            url = f"{BACKEND_URL}/journal/{test_case['user_id']}/reflector-synthesis"
            print(f"Request URL: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                all_tests_passed = False
                continue
            
            # Parse JSON response
            try:
                data = response.json()
                print(f"Response received: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"❌ FAILED: Invalid JSON response: {e}")
                print(f"Raw response: {response.text}")
                all_tests_passed = False
                continue
            
            # Validate response structure
            required_fields = [
                "user_id", "cycle_start", "cycle_day", "entries_in_cycle", 
                "synthesis", "has_enough_data"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ FAILED: Missing required fields: {missing_fields}")
                all_tests_passed = False
                continue
            
            # Validate field types
            validation_errors = []
            
            if not isinstance(data["user_id"], str):
                validation_errors.append("user_id should be string")
            
            if not isinstance(data["cycle_start"], str):
                validation_errors.append("cycle_start should be ISO date string")
            else:
                # Validate ISO date format
                try:
                    datetime.fromisoformat(data["cycle_start"].replace('Z', '+00:00'))
                except ValueError:
                    validation_errors.append("cycle_start is not valid ISO date")
            
            if not isinstance(data["cycle_day"], int) or not (1 <= data["cycle_day"] <= 28):
                validation_errors.append("cycle_day should be integer 1-28")
            
            if not isinstance(data["entries_in_cycle"], int) or data["entries_in_cycle"] < 0:
                validation_errors.append("entries_in_cycle should be non-negative integer")
            
            if not isinstance(data["synthesis"], dict):
                validation_errors.append("synthesis should be dict")
            else:
                # Validate synthesis structure
                synthesis_fields = ["early_cycle", "mid_cycle", "current_direction"]
                for field in synthesis_fields:
                    if field not in data["synthesis"]:
                        validation_errors.append(f"synthesis missing {field}")
                    elif data["synthesis"][field] is not None and not isinstance(data["synthesis"][field], str):
                        validation_errors.append(f"synthesis.{field} should be string or null")
            
            if not isinstance(data["has_enough_data"], bool):
                validation_errors.append("has_enough_data should be boolean")
            
            if "message" in data and data["message"] is not None and not isinstance(data["message"], str):
                validation_errors.append("message should be string or null")
            
            if validation_errors:
                print(f"❌ FAILED: Validation errors: {validation_errors}")
                all_tests_passed = False
                continue
            
            # Test case specific validations
            if test_case["expected_has_enough_data"] is not None:
                if data["has_enough_data"] != test_case["expected_has_enough_data"]:
                    print(f"❌ FAILED: Expected has_enough_data={test_case['expected_has_enough_data']}, got {data['has_enough_data']}")
                    all_tests_passed = False
                    continue
            
            if test_case["expected_message_present"] is not None:
                message_present = "message" in data and data["message"] is not None
                if message_present != test_case["expected_message_present"]:
                    print(f"❌ FAILED: Expected message_present={test_case['expected_message_present']}, got {message_present}")
                    all_tests_passed = False
                    continue
            
            if test_case["expected_synthesis_null"] is not None:
                synthesis_all_null = all(v is None for v in data["synthesis"].values())
                if synthesis_all_null != test_case["expected_synthesis_null"]:
                    print(f"❌ FAILED: Expected synthesis_all_null={test_case['expected_synthesis_null']}, got {synthesis_all_null}")
                    all_tests_passed = False
                    continue
            
            print("✅ PASSED: All validations successful")
            
            # Print key insights
            print(f"📊 Key Data:")
            print(f"   - Cycle Day: {data['cycle_day']}")
            print(f"   - Entries in Cycle: {data['entries_in_cycle']}")
            print(f"   - Has Enough Data: {data['has_enough_data']}")
            if data.get("message"):
                print(f"   - Message: {data['message']}")
            
            synthesis = data["synthesis"]
            if any(v is not None for v in synthesis.values()):
                print(f"   - Synthesis Lines:")
                for key, value in synthesis.items():
                    if value:
                        print(f"     * {key}: {value}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED: Request error: {e}")
            all_tests_passed = False
        except Exception as e:
            print(f"❌ FAILED: Unexpected error: {e}")
            all_tests_passed = False
    
    # Test edge cases
    print(f"\n🎯 TEST 3: Invalid User ID")
    try:
        url = f"{BACKEND_URL}/journal/invalid_user_id/reflector-synthesis"
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data["entries_in_cycle"] == 0 and not data["has_enough_data"]:
                print("✅ PASSED: Invalid user ID handled gracefully")
            else:
                print("❌ FAILED: Invalid user ID should return empty data")
                all_tests_passed = False
        else:
            print(f"❌ FAILED: Expected 200 for invalid user, got {response.status_code}")
            all_tests_passed = False
            
    except Exception as e:
        print(f"❌ FAILED: Error testing invalid user ID: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - Reflector Journal Synthesis endpoint working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED - Issues found with Reflector Journal Synthesis endpoint")
        return False

if __name__ == "__main__":
    success = test_reflector_synthesis_endpoint()
    sys.exit(0 if success else 1)