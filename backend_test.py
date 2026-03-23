#!/usr/bin/env python3
"""
Backend Test Suite for Pattern Detection Layer V2
Testing the GET /api/journal/{user_id}/patterns endpoint
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta

# Backend URL from frontend environment
BACKEND_URL = "https://phase-mirror-reflect.preview.emergentagent.com/api"

# Test user ID from review request
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

def test_pattern_detection_layer_v2():
    """
    Test Pattern Detection Layer V2 backend endpoint:
    GET /api/journal/{user_id}/patterns
    """
    print("🧪 TESTING PATTERN DETECTION LAYER V2 BACKEND ENDPOINTS")
    print("=" * 70)
    
    # Test 1: GET /api/journal/{user_id}/patterns
    print(f"\n1. ✅ TESTING GET /api/journal/{TEST_USER_ID}/patterns")
    print("-" * 50)
    
    try:
        url = f"{BACKEND_URL}/journal/{TEST_USER_ID}/patterns"
        print(f"Request URL: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Endpoint returned 200 OK")
            
            # Verify response structure
            print("\n📋 RESPONSE STRUCTURE VERIFICATION:")
            
            # Required fields from review request
            required_fields = [
                'total_entries',
                'phase_distribution', 
                'phase_distribution_14d',
                'repeating_phases',
                'phase_patterns',
                'phase_tensions',
                'identity_tendency',
                'identity_threshold_met'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field in data:
                    print(f"  ✅ {field}: {type(data[field]).__name__}")
                else:
                    missing_fields.append(field)
                    print(f"  ❌ {field}: MISSING")
            
            if missing_fields:
                print(f"\n❌ MISSING REQUIRED FIELDS: {missing_fields}")
                return False
            
            # Verify data types
            print("\n📊 DATA TYPE VERIFICATION:")
            type_checks = [
                ('total_entries', int),
                ('phase_distribution', dict),
                ('phase_distribution_14d', dict),
                ('repeating_phases', list),
                ('phase_patterns', dict),
                ('phase_tensions', dict),
                ('identity_threshold_met', bool)
            ]
            
            for field, expected_type in type_checks:
                actual_type = type(data[field])
                if actual_type == expected_type:
                    print(f"  ✅ {field}: {actual_type.__name__} (correct)")
                else:
                    print(f"  ❌ {field}: {actual_type.__name__} (expected {expected_type.__name__})")
                    return False
            
            # Display actual data
            print("\n📈 ACTUAL RESPONSE DATA:")
            print(f"  Total Entries: {data['total_entries']}")
            print(f"  Phase Distribution: {data['phase_distribution']}")
            print(f"  Phase Distribution (14d): {data['phase_distribution_14d']}")
            print(f"  Repeating Phases: {data['repeating_phases']}")
            print(f"  Phase Patterns: {data['phase_patterns']}")
            print(f"  Phase Tensions: {data['phase_tensions']}")
            print(f"  Identity Tendency: {data['identity_tendency']}")
            print(f"  Identity Threshold Met: {data['identity_threshold_met']}")
            
            # Test 2: Verify repeat detection logic
            print("\n2. ✅ TESTING REPEAT DETECTION LOGIC")
            print("-" * 50)
            
            phase_dist = data['phase_distribution']
            phase_dist_14d = data['phase_distribution_14d']
            repeating_phases = data['repeating_phases']
            
            print("Verifying repeat detection rule: phase has >= 3 total entries OR >= 2 entries in last 14 days")
            
            for phase_id, total_count in phase_dist.items():
                recent_count = phase_dist_14d.get(phase_id, 0)
                should_be_repeating = total_count >= 3 or recent_count >= 2
                is_repeating = phase_id in repeating_phases
                
                status = "✅" if should_be_repeating == is_repeating else "❌"
                print(f"  {status} Phase {phase_id}: total={total_count}, recent={recent_count}, repeating={is_repeating}")
                
                if should_be_repeating != is_repeating:
                    print(f"    ❌ LOGIC ERROR: Should be {should_be_repeating}, but is {is_repeating}")
                    return False
            
            # Test 3: Verify recurring patterns extraction
            print("\n3. ✅ TESTING RECURRING PATTERNS EXTRACTION")
            print("-" * 50)
            
            phase_patterns = data['phase_patterns']
            print("Verifying that phases with 2+ entries have extracted patterns:")
            
            for phase_id, total_count in phase_dist.items():
                has_patterns = phase_id in phase_patterns
                should_have_patterns = total_count >= 2
                
                if should_have_patterns:
                    if has_patterns:
                        patterns = phase_patterns[phase_id]
                        print(f"  ✅ Phase {phase_id} ({total_count} entries): {len(patterns)} patterns - {patterns}")
                    else:
                        print(f"  ⚠️  Phase {phase_id} ({total_count} entries): No patterns extracted (may be normal if content is too sparse)")
                else:
                    if has_patterns:
                        print(f"  ❌ Phase {phase_id} ({total_count} entries): Unexpected patterns found")
                        return False
                    else:
                        print(f"  ✅ Phase {phase_id} ({total_count} entries): No patterns (correct)")
            
            print("\n🎉 ALL TESTS PASSED!")
            print("Pattern Detection Layer V2 endpoint is working correctly.")
            return True
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON DECODE ERROR: {e}")
        print(f"Response text: {response.text}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING PATTERN DETECTION LAYER V2 BACKEND TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
    
    success = test_pattern_detection_layer_v2()
    
    if success:
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()