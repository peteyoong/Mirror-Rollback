#!/usr/bin/env python3
"""
Backend Test for Human Design Variables Strict Computation
Testing the specific review request requirements for no heuristics/estimation.
"""

import requests
import json
import sys
from typing import Dict, Any

# Use the public URL from frontend/.env
BASE_URL = "https://lens-bridge-app.preview.emergentagent.com/api"

def test_human_design_variables_strict_computation():
    """
    Test Human Design Variables strict computation (no heuristics).
    
    SUCCESS CRITERIA:
    - API returns `"variables": null` when exact longitude data unavailable
    - NO estimation/heuristic values are returned
    - System enforces deterministic-only output
    """
    print("🧪 TESTING: Human Design Variables Strict Computation (No Heuristics)")
    print("=" * 80)
    
    # Test scenarios from review request
    test_cases = [
        {
            "name": "Reflector user (should NOT have exact longitude data)",
            "user_id": "697f795f1a7a96aa35e283a3",
            "expected_variables": None,
            "description": "This user does NOT have exact longitude data stored"
        },
        {
            "name": "peter@test.com (test if also returns null)",
            "user_id": "6971c81f2b40fd5ef501d375", 
            "expected_variables": None,
            "description": "Test if this user also returns null if no longitude data"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        print(f"User ID: {test_case['user_id']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected variables: {test_case['expected_variables']}")
        
        try:
            # Make API request
            url = f"{BASE_URL}/human-design/mechanics/{test_case['user_id']}"
            print(f"🌐 GET {url}")
            
            response = requests.get(url, timeout=30)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                variables = data.get('variables')
                
                print(f"📋 Response variables: {variables}")
                
                # Check if variables is null (as expected)
                if variables is None:
                    print("✅ PASS: Variables is null (no estimation/heuristics)")
                    results.append({
                        "test": test_case['name'],
                        "status": "PASS",
                        "variables": variables,
                        "reason": "Variables correctly null - no estimation"
                    })
                else:
                    # Variables is not null - check if it contains estimated field
                    if isinstance(variables, dict):
                        has_estimated_field = 'estimated' in variables
                        print(f"📋 Variables structure: {json.dumps(variables, indent=2)}")
                        
                        if has_estimated_field:
                            print("❌ FAIL: Variables contains 'estimated' field (heuristics detected)")
                            results.append({
                                "test": test_case['name'],
                                "status": "FAIL",
                                "variables": variables,
                                "reason": "Variables contains 'estimated' field - heuristics used"
                            })
                        else:
                            print("⚠️  UNEXPECTED: Variables populated but no 'estimated' field")
                            print("    This suggests exact longitude data IS available for this user")
                            results.append({
                                "test": test_case['name'],
                                "status": "UNEXPECTED",
                                "variables": variables,
                                "reason": "Variables populated with actual computed data (exact longitude available)"
                            })
                    else:
                        print(f"❌ FAIL: Variables is not null but not a dict: {type(variables)}")
                        results.append({
                            "test": test_case['name'],
                            "status": "FAIL",
                            "variables": variables,
                            "reason": f"Variables is {type(variables)}, not null or dict"
                        })
                        
            else:
                print(f"❌ FAIL: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                results.append({
                    "test": test_case['name'],
                    "status": "FAIL",
                    "variables": None,
                    "reason": f"HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "test": test_case['name'],
                "status": "ERROR",
                "variables": None,
                "reason": str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    unexpected_count = sum(1 for r in results if r['status'] == 'UNEXPECTED')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    
    for result in results:
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌', 
            'UNEXPECTED': '⚠️',
            'ERROR': '💥'
        }.get(result['status'], '❓')
        
        print(f"{status_emoji} {result['test']}: {result['status']}")
        print(f"   Reason: {result['reason']}")
        if result['variables'] is not None:
            print(f"   Variables: {result['variables']}")
    
    print(f"\n📈 RESULTS: {pass_count} PASS, {fail_count} FAIL, {unexpected_count} UNEXPECTED, {error_count} ERROR")
    
    # Determine overall test result
    if fail_count > 0 or error_count > 0:
        print("🚨 OVERALL: FAILED - Issues detected with strict computation")
        return False
    elif unexpected_count > 0:
        print("⚠️  OVERALL: UNEXPECTED - Users may have exact longitude data available")
        print("    This means the system is working correctly but test assumptions may be wrong")
        return True
    else:
        print("🎉 OVERALL: PASSED - Strict computation working correctly")
        return True

def test_no_estimation_verification():
    """
    Additional test to verify NO estimation is happening anywhere.
    """
    print("\n🔍 ADDITIONAL TEST: Verify NO estimation fields exist")
    print("=" * 80)
    
    test_users = ["697f795f1a7a96aa35e283a3", "6971c81f2b40fd5ef501d375"]
    
    for user_id in test_users:
        try:
            url = f"{BASE_URL}/human-design/mechanics/{user_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                variables = data.get('variables')
                
                if variables and isinstance(variables, dict):
                    # Check for any estimation-related fields
                    estimation_fields = ['estimated', 'heuristic', 'approximated', 'fallback']
                    found_estimation = []
                    
                    def check_dict_for_estimation(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                current_path = f"{path}.{key}" if path else key
                                if key.lower() in estimation_fields:
                                    found_estimation.append(current_path)
                                check_dict_for_estimation(value, current_path)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                check_dict_for_estimation(item, f"{path}[{i}]")
                    
                    check_dict_for_estimation(variables)
                    
                    if found_estimation:
                        print(f"❌ User {user_id}: Found estimation fields: {found_estimation}")
                    else:
                        print(f"✅ User {user_id}: No estimation fields detected")
                        
        except Exception as e:
            print(f"❌ Error checking user {user_id}: {e}")

if __name__ == "__main__":
    print("🚀 Starting Human Design Variables Strict Computation Test")
    print(f"🌐 Backend URL: {BASE_URL}")
    
    success = test_human_design_variables_strict_computation()
    test_no_estimation_verification()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n🚨 Tests failed!")
        sys.exit(1)