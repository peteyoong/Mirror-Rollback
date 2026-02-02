#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror - Astrology Deep Dive UI Testing
Testing Pete and Mel's Astrology Deep Dive API responses as requested in review
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend .env
BASE_URL = "https://mirror-lens-fixes.preview.emergentagent.com/api"

def test_astrology_deep_dive():
    """Test Astrology Deep Dive API for Pete and Mel"""
    
    print("=" * 80)
    print("TESTING ASTROLOGY DEEP DIVE API")
    print("=" * 80)
    
    # Test cases from review request
    test_cases = [
        {
            "name": "Pete",
            "user_id": "6971c81f2b40fd5ef501d375",
            "expected": {
                "sun": "Pisces",
                "sun_house": 3,
                "moon": "Aries", 
                "moon_house": 4,
                "ascendant": "Sagittarius",
                "houses_computed": True
            }
        },
        {
            "name": "Mel",
            "user_id": "697ec826ad4b18f75bf42616",
            "expected": {
                "sun": "Gemini",
                "sun_house": 12,
                "moon": "Scorpio",
                "moon_house": 5,
                "ascendant": "Gemini",
                "houses_computed": True
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🧪 Testing {test_case['name']}'s Astrology Deep Dive")
        print(f"User ID: {test_case['user_id']}")
        
        url = f"{BASE_URL}/astrology/deep-dive/{test_case['user_id']}"
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response received successfully")
                
                # Print full response for verification as requested
                print("\n📄 FULL API RESPONSE:")
                print(json.dumps(data, indent=2))
                
                # Verify response structure
                success = data.get('success', False)
                print(f"\n✅ Success: {success}")
                
                if success:
                    core_placements = data.get('core_placements', {})
                    print(f"\n🔍 Core Placements Verification:")
                    
                    # Check each expected field
                    expected = test_case['expected']
                    verification_results = {}
                    
                    for field, expected_value in expected.items():
                        actual_value = core_placements.get(field)
                        matches = actual_value == expected_value
                        verification_results[field] = {
                            'expected': expected_value,
                            'actual': actual_value,
                            'matches': matches
                        }
                        status = "✅" if matches else "❌"
                        print(f"  {status} {field}: expected={expected_value}, actual={actual_value}")
                    
                    # Overall verification
                    all_match = all(v['matches'] for v in verification_results.values())
                    print(f"\n🎯 Overall Verification: {'✅ PASS' if all_match else '❌ FAIL'}")
                    
                    results.append({
                        'name': test_case['name'],
                        'user_id': test_case['user_id'],
                        'success': True,
                        'api_success': success,
                        'verification': verification_results,
                        'all_match': all_match,
                        'response': data
                    })
                else:
                    print(f"❌ API returned success=false")
                    error_code = data.get('error_code', 'unknown')
                    print(f"Error code: {error_code}")
                    
                    results.append({
                        'name': test_case['name'],
                        'user_id': test_case['user_id'],
                        'success': False,
                        'api_success': success,
                        'error_code': error_code,
                        'response': data
                    })
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
                results.append({
                    'name': test_case['name'],
                    'user_id': test_case['user_id'],
                    'success': False,
                    'http_error': response.status_code,
                    'response_text': response.text
                })
                
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
            results.append({
                'name': test_case['name'],
                'user_id': test_case['user_id'],
                'success': False,
                'exception': str(e)
            })
        
        print("-" * 60)
    
    return results

def test_success_false_case():
    """Test success=false case and error handling"""
    
    print(f"\n🧪 Testing success=false and error handling cases")
    
    test_cases = [
        {
            "name": "Non-existent user",
            "user_id": "000000000000000000000000",
            "expected_status": 404,
            "expected_response": "User not found"
        },
        {
            "name": "Invalid user ID format", 
            "user_id": "invalid-id",
            "expected_status": 422,
            "expected_response": "validation error"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing {test_case['name']}")
        print(f"User ID: {test_case['user_id']}")
        
        url = f"{BASE_URL}/astrology/deep-dive/{test_case['user_id']}"
        
        try:
            response = requests.get(url, timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            expected_status = test_case['expected_status']
            if response.status_code == expected_status:
                print(f"✅ Correctly returned {expected_status} status")
                results.append({
                    'name': test_case['name'],
                    'success': True,
                    'message': f'Correctly returned {expected_status} status'
                })
            else:
                print(f"❌ Expected {expected_status}, got {response.status_code}")
                results.append({
                    'name': test_case['name'],
                    'success': False,
                    'message': f'Expected {expected_status}, got {response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'message': f'Exception: {str(e)}'
            })
    
    # Test user creation with invalid timezone
    print(f"\n🔍 Testing user creation with invalid timezone")
    create_url = f"{BASE_URL}/users"
    
    incomplete_user_data = {
        "name": "Test User Incomplete",
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "city": "New York",
        "country": "United States",
        "timezone": "",  # Missing timezone - should cause error
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    
    try:
        print(f"Creating user with empty timezone...")
        create_response = requests.post(create_url, json=incomplete_user_data, timeout=30)
        print(f"Create user status: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        
        if create_response.status_code in [400, 422, 500]:
            print("✅ User creation correctly failed due to invalid timezone")
            results.append({
                'name': 'Invalid timezone creation',
                'success': True,
                'message': 'User creation correctly failed due to invalid timezone'
            })
        else:
            print(f"❌ Expected error status, got {create_response.status_code}")
            results.append({
                'name': 'Invalid timezone creation',
                'success': False,
                'message': f'Expected error status, got {create_response.status_code}'
            })
            
    except Exception as e:
        print(f"❌ Exception in user creation test: {str(e)}")
        results.append({
            'name': 'Invalid timezone creation',
            'success': False,
            'message': f'Exception: {str(e)}'
        })
    
    # Overall result
    all_passed = all(r['success'] for r in results)
    
    return {
        'success': all_passed,
        'message': 'All error handling tests passed' if all_passed else 'Some error handling tests failed',
        'results': results
    }

def main():
    """Main test execution"""
    
    print("🚀 Starting Astrology Deep Dive API Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Test Pete and Mel's deep dive APIs
    deep_dive_results = test_astrology_deep_dive()
    
    # Test error handling cases
    print("\n" + "=" * 80)
    print("TESTING ERROR HANDLING CASES")
    print("=" * 80)
    
    success_false_result = test_success_false_case()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n📊 Deep Dive API Tests:")
    for result in deep_dive_results:
        name = result['name']
        if result['success'] and result.get('api_success') and result.get('all_match'):
            print(f"  ✅ {name}: All data matches expected values")
        elif result['success'] and result.get('api_success'):
            print(f"  ⚠️  {name}: API success but data mismatch")
        elif result['success'] and not result.get('api_success'):
            print(f"  ❌ {name}: API returned success=false")
        else:
            print(f"  ❌ {name}: Test failed")
    
    print(f"\n📊 Error Handling Tests:")
    if success_false_result['success']:
        print(f"  ✅ Error handling: {success_false_result['message']}")
        for result in success_false_result.get('results', []):
            status = "✅" if result['success'] else "❌"
            print(f"    {status} {result['name']}: {result['message']}")
    else:
        print(f"  ❌ Error handling: {success_false_result['message']}")
        for result in success_false_result.get('results', []):
            status = "✅" if result['success'] else "❌"
            print(f"    {status} {result['name']}: {result['message']}")
    
    # Overall result
    all_deep_dive_pass = all(
        r['success'] and r.get('api_success') and r.get('all_match') 
        for r in deep_dive_results
    )
    success_false_pass = success_false_result['success']
    
    overall_pass = all_deep_dive_pass and success_false_pass
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_pass else '❌ SOME TESTS FAILED'}")
    
    return overall_pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)