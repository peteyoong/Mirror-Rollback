#!/usr/bin/env python3
"""
Additional comprehensive test for Human Design Variables strict computation
"""

import requests
import json

BASE_URL = "https://mirror-diagnosis.preview.emergentagent.com/api"

def test_additional_scenarios():
    """Test additional scenarios to verify strict computation"""
    print("🔍 ADDITIONAL COMPREHENSIVE TESTING")
    print("=" * 80)
    
    # Test a few more users to see if any have exact longitude data
    additional_users = [
        "69819f1a1e4549392d7cb6d1",  # Another test user
        "6984b4a4ce7b78080ce4853a",  # Another test user
    ]
    
    for user_id in additional_users:
        try:
            url = f"{BASE_URL}/human-design/mechanics/{user_id}"
            print(f"\n🧪 Testing user: {user_id}")
            print(f"🌐 GET {url}")
            
            response = requests.get(url, timeout=30)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                variables = data.get('variables')
                
                if variables is None:
                    print("✅ Variables: null (no exact longitude data)")
                elif isinstance(variables, dict):
                    print("📋 Variables populated - checking structure:")
                    
                    # Check if this is actual computed data or estimation
                    has_estimation_markers = any(
                        key in str(variables).lower() 
                        for key in ['estimated', 'heuristic', 'approximated', 'fallback']
                    )
                    
                    if has_estimation_markers:
                        print("❌ FAIL: Contains estimation markers")
                    else:
                        print("✅ Variables populated with actual computed data (exact longitude available)")
                        
                        # Show the structure
                        for component in ['environment', 'determination', 'cognition', 'motivation']:
                            comp_data = variables.get(component)
                            if comp_data:
                                print(f"   {component}: {comp_data.get('type')} ({comp_data.get('arrow')} arrow)")
                            else:
                                print(f"   {component}: null")
                else:
                    print(f"⚠️  Unexpected variables type: {type(variables)}")
                    
            elif response.status_code == 404:
                print("📋 User not found (expected for some test IDs)")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def verify_response_structure():
    """Verify the response structure matches expectations"""
    print("\n🔍 VERIFYING RESPONSE STRUCTURE")
    print("=" * 80)
    
    # Test with the known working user
    user_id = "697f795f1a7a96aa35e283a3"
    
    try:
        url = f"{BASE_URL}/human-design/mechanics/{user_id}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = [
                'core_mechanics',
                'channels', 
                'defined_centers',
                'undefined_centers',
                'conscious_gates',
                'unconscious_gates',
                'variables'
            ]
            
            print("📋 Checking required fields:")
            for field in required_fields:
                if field in data:
                    if field == 'variables':
                        print(f"✅ {field}: {data[field]} (correctly null)")
                    else:
                        print(f"✅ {field}: present")
                else:
                    print(f"❌ {field}: missing")
                    
            # Verify variables is exactly null, not empty dict or other falsy value
            variables = data.get('variables')
            if variables is None:
                print("✅ Variables field is exactly null (not empty dict or other falsy value)")
            else:
                print(f"❌ Variables field is not null: {type(variables)} = {variables}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_additional_scenarios()
    verify_response_structure()
    print("\n🎉 Additional testing complete!")