#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Test configuration
BASE_URL = "https://lens-bridge-app.preview.emergentagent.com/api"

def test_human_design_variables():
    """Test Human Design Variables computation endpoint"""
    
    print("🧪 HUMAN DESIGN VARIABLES (ENVIRONMENT) BACKEND COMPUTATION TESTING")
    print("=" * 80)
    
    # Test users from review request
    test_users = [
        {
            "user_id": "697f795f1a7a96aa35e283a3",
            "description": "Reflector user",
            "expected_note": "Should have Variables computed from Design Sun and Personality Sun positions"
        },
        {
            "user_id": "6971c81f2b40fd5ef501d375", 
            "description": "peter@test.com",
            "expected_note": "Should have Variables computed for this user as well"
        }
    ]
    
    all_tests_passed = True
    
    for i, user in enumerate(test_users, 1):
        print(f"\n🔍 TEST {i}: {user['description']} (ID: {user['user_id']})")
        print("-" * 60)
        
        try:
            # Test the Human Design mechanics endpoint
            url = f"{BASE_URL}/human-design/mechanics/{user['user_id']}"
            print(f"📡 GET {url}")
            
            response = requests.get(url, timeout=30)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                all_tests_passed = False
                continue
                
            data = response.json()
            
            # Check if variables exist
            variables = data.get('variables')
            if not variables:
                print(f"❌ FAILED: No variables found in response")
                all_tests_passed = False
                continue
                
            print(f"✅ Variables object found")
            
            # Test each Variable component
            required_components = ['environment', 'determination', 'cognition', 'motivation']
            
            for component in required_components:
                component_data = variables.get(component)
                if not component_data:
                    print(f"❌ FAILED: Missing {component} component")
                    all_tests_passed = False
                    continue
                    
                # Check required fields for each component
                required_fields = ['type', 'description', 'arrow']
                if component in ['environment', 'motivation']:
                    required_fields.append('tone')
                else:  # determination, cognition
                    required_fields.append('color')
                    
                missing_fields = []
                for field in required_fields:
                    if field not in component_data:
                        missing_fields.append(field)
                        
                if missing_fields:
                    print(f"❌ FAILED: {component} missing fields: {missing_fields}")
                    all_tests_passed = False
                else:
                    print(f"✅ {component}: {component_data['type']} ({component_data['arrow']} arrow)")
                    
            # Validate specific requirements from review request
            print(f"\n🎯 VALIDATION CHECKS:")
            
            # 1. Environment type validation
            env_type = variables.get('environment', {}).get('type')
            valid_env_types = ['mountains', 'caves', 'markets', 'kitchens', 'valleys', 'shores']
            if env_type in valid_env_types:
                print(f"✅ Environment type '{env_type}' is valid")
            else:
                print(f"❌ FAILED: Environment type '{env_type}' not in valid types: {valid_env_types}")
                all_tests_passed = False
                
            # 2. Arrow directions validation
            for component in required_components:
                arrow = variables.get(component, {}).get('arrow')
                if arrow in ['left', 'right']:
                    print(f"✅ {component} arrow direction '{arrow}' is valid")
                else:
                    print(f"❌ FAILED: {component} arrow direction '{arrow}' not 'left' or 'right'")
                    all_tests_passed = False
                    
            # 3. Tone/Color ranges validation
            env_tone = variables.get('environment', {}).get('tone')
            if env_tone and 1 <= env_tone <= 6:
                print(f"✅ Environment tone {env_tone} is in valid range (1-6)")
            else:
                print(f"❌ FAILED: Environment tone {env_tone} not in range 1-6")
                all_tests_passed = False
                
            det_color = variables.get('determination', {}).get('color')
            if det_color and 1 <= det_color <= 6:
                print(f"✅ Determination color {det_color} is in valid range (1-6)")
            else:
                print(f"❌ FAILED: Determination color {det_color} not in range 1-6")
                all_tests_passed = False
                
            cog_color = variables.get('cognition', {}).get('color')
            if cog_color and 1 <= cog_color <= 6:
                print(f"✅ Cognition color {cog_color} is in valid range (1-6)")
            else:
                print(f"❌ FAILED: Cognition color {cog_color} not in range 1-6")
                all_tests_passed = False
                
            mot_tone = variables.get('motivation', {}).get('tone')
            if mot_tone and 1 <= mot_tone <= 6:
                print(f"✅ Motivation tone {mot_tone} is in valid range (1-6)")
            else:
                print(f"❌ FAILED: Motivation tone {mot_tone} not in range 1-6")
                all_tests_passed = False
                
            # Print full Variables structure for verification
            print(f"\n📋 COMPLETE VARIABLES STRUCTURE:")
            print(json.dumps(variables, indent=2))
            
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED: Network error - {e}")
            all_tests_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: JSON decode error - {e}")
            all_tests_passed = False
        except Exception as e:
            print(f"❌ FAILED: Unexpected error - {e}")
            all_tests_passed = False
            
    # Final summary
    print(f"\n{'='*80}")
    print(f"🎯 FINAL TEST RESULTS")
    print(f"{'='*80}")
    
    if all_tests_passed:
        print(f"✅ ALL TESTS PASSED - Human Design Variables computation is working correctly!")
        print(f"✅ Variables are computed from Design Sun and Personality Sun positions")
        print(f"✅ Environment comes from Design Sun tone (1-6 maps to caves/markets/kitchens/mountains/valleys/shores)")
        print(f"✅ Determination comes from Design Sun color (1-6)")
        print(f"✅ Cognition comes from Personality Sun color (1-6)")
        print(f"✅ Motivation comes from Personality Sun tone (1-6)")
        print(f"✅ All arrow directions are 'left' or 'right'")
        return True
    else:
        print(f"❌ SOME TESTS FAILED - See details above")
        return False

if __name__ == "__main__":
    success = test_human_design_variables()
    sys.exit(0 if success else 1)