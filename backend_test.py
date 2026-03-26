#!/usr/bin/env python3
"""
Backend API Testing Script for Today Pattern Endpoint
Testing the updated Today Pattern endpoint with pattern-specific content
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://experience-controls.preview.emergentagent.com/api"

def test_today_pattern_endpoint():
    """Test the Today Pattern endpoint with pattern-specific content"""
    
    print("🧪 TESTING TODAY PATTERN ENDPOINT WITH PATTERN-SPECIFIC CONTENT")
    print("=" * 70)
    
    # Test user ID from review request
    user_id = "697f0c6abf35c0528ff06954"
    
    # Test endpoint with force_refresh=true
    endpoint = f"{BACKEND_URL}/today-pattern/{user_id}?force_refresh=true"
    
    print(f"📍 Testing endpoint: {endpoint}")
    print(f"👤 User ID: {user_id}")
    print()
    
    try:
        # Make the API request
        print("🔄 Making API request...")
        response = requests.get(endpoint, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS - API returned 200 OK")
            print()
            
            # Test 1: Verify response includes new fields
            print("🔍 TEST 1: VERIFY NEW FIELDS PRESENT")
            print("-" * 40)
            
            required_fields = ['pattern_family', 'pattern_closer', 'action_guidance']
            all_fields_present = True
            
            for field in required_fields:
                if field in data:
                    print(f"✅ {field}: Present")
                    if data[field] is not None:
                        print(f"   Value: {data[field]}")
                    else:
                        print(f"   Value: null")
                else:
                    print(f"❌ {field}: Missing")
                    all_fields_present = False
            
            print()
            
            # Test 2: Verify pattern_family is valid
            print("🔍 TEST 2: VERIFY PATTERN_FAMILY VALUE")
            print("-" * 40)
            
            valid_pattern_families = [
                'push_pull', 'expression', 'control', 'clarity', 
                'stall', 'movement', 'release', 'general'
            ]
            
            pattern_family = data.get('pattern_family')
            if pattern_family in valid_pattern_families:
                print(f"✅ pattern_family is valid: '{pattern_family}'")
            else:
                print(f"❌ pattern_family is invalid: '{pattern_family}'")
                print(f"   Expected one of: {valid_pattern_families}")
            
            print()
            
            # Test 3: Verify pattern_closer is pattern-specific
            print("🔍 TEST 3: VERIFY PATTERN_CLOSER SPECIFICITY")
            print("-" * 40)
            
            pattern_closer = data.get('pattern_closer')
            if pattern_closer:
                # Check it's not generic
                generic_phrases = [
                    "Consider this as you move forward",
                    "Think about this",
                    "Reflect on this"
                ]
                
                is_generic = any(phrase in pattern_closer for phrase in generic_phrases)
                if not is_generic:
                    print(f"✅ pattern_closer appears specific: '{pattern_closer}'")
                else:
                    print(f"❌ pattern_closer appears generic: '{pattern_closer}'")
            else:
                print("❌ pattern_closer is null or empty")
            
            print()
            
            # Test 4: Verify action_guidance structure
            print("🔍 TEST 4: VERIFY ACTION_GUIDANCE STRUCTURE")
            print("-" * 40)
            
            action_guidance = data.get('action_guidance')
            if action_guidance and isinstance(action_guidance, dict):
                required_ag_fields = ['action', 'context', 'timeframe', 'cta']
                ag_complete = True
                
                for field in required_ag_fields:
                    if field in action_guidance:
                        print(f"✅ action_guidance.{field}: '{action_guidance[field]}'")
                    else:
                        print(f"❌ action_guidance.{field}: Missing")
                        ag_complete = False
                
                if ag_complete:
                    print("✅ action_guidance structure is complete")
                else:
                    print("❌ action_guidance structure is incomplete")
            else:
                print("❌ action_guidance is not a valid object")
            
            print()
            
            # Test 5: Verify pattern title matches tension type
            print("🔍 TEST 5: VERIFY PATTERN TITLE APPROPRIATENESS")
            print("-" * 40)
            
            title = data.get('title', '')
            pattern_family = data.get('pattern_family', '')
            
            # Expected title patterns for different families
            title_patterns = {
                'stall': ['The Pause', 'Waiting', 'Stillness'],
                'push_pull': ['Forward and Back', 'Push and Pull', 'Back and Forth'],
                'movement': ['Something Stirring', 'In Motion', 'Shifting'],
                'clarity': ['Coming Clear', 'Clarity', 'Focus'],
                'expression': ['Finding Voice', 'Expression', 'Speaking'],
                'control': ['Holding On', 'Control', 'Grip'],
                'release': ['Letting Go', 'Release', 'Opening']
            }
            
            if pattern_family in title_patterns:
                expected_patterns = title_patterns[pattern_family]
                title_matches = any(pattern.lower() in title.lower() for pattern in expected_patterns)
                if title_matches:
                    print(f"✅ Title '{title}' matches pattern family '{pattern_family}'")
                else:
                    print(f"⚠️  Title '{title}' may not match pattern family '{pattern_family}'")
                    print(f"   Expected patterns: {expected_patterns}")
            else:
                print(f"ℹ️  Pattern family '{pattern_family}' - title appropriateness not checked")
            
            print()
            
            # Summary
            print("📋 FULL RESPONSE SUMMARY")
            print("-" * 40)
            print(f"Title: {data.get('title', 'N/A')}")
            print(f"Lines: {data.get('lines', [])}")
            print(f"Confidence: {data.get('confidence', 'N/A')}")
            print(f"Sources: {data.get('sources', [])}")
            print(f"Pattern Family: {data.get('pattern_family', 'N/A')}")
            print(f"Pattern Closer: {data.get('pattern_closer', 'N/A')}")
            print(f"Action Guidance: {data.get('action_guidance', 'N/A')}")
            
            print()
            print("🎉 TESTING COMPLETE")
            
            # Overall assessment
            if all_fields_present and pattern_family in valid_pattern_families:
                print("✅ OVERALL: All major requirements met")
                return True
            else:
                print("❌ OVERALL: Some requirements not met")
                return False
                
        else:
            print(f"❌ FAILED - API returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON DECODE FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 BACKEND API TESTING - TODAY PATTERN ENDPOINT")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_today_pattern_endpoint()
    
    print()
    if success:
        print("🎯 ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()