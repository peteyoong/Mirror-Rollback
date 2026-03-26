#!/usr/bin/env python3
"""
Backend Test Suite for Cross-Lens Pattern Diagnosis Endpoint
Testing the new pattern diagnosis endpoint as specified in the review request.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://experience-controls.preview.emergentagent.com/api"

def test_cross_lens_pattern_diagnosis():
    """
    Test the new cross-lens pattern diagnosis endpoint:
    GET /api/pattern-diagnosis/697f0c6abf35c0528ff06954
    
    Verify the response contains all required fields and structure.
    """
    print("🧪 TESTING: Cross-Lens Pattern Diagnosis Endpoint")
    print("=" * 60)
    
    # Test user ID from review request
    user_id = "697f0c6abf35c0528ff06954"
    endpoint = f"{BACKEND_URL}/pattern-diagnosis/{user_id}"
    
    print(f"📍 Testing endpoint: {endpoint}")
    
    try:
        # Make the API request
        response = requests.get(endpoint, timeout=30)
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response: {e}")
            return False
            
        print(f"📊 Response size: {len(response.text)} characters")
        
        # Test 1: Core Diagnosis Structure
        print("\n🔍 TEST 1: Core Diagnosis Structure")
        core_fields = [
            'what_is_happening',
            'why_it_is_happening', 
            'what_kind_of_moment',
            'what_would_be_wise',
            'full_diagnosis',
            'moment_type'
        ]
        
        missing_core = []
        for field in core_fields:
            if field not in data:
                missing_core.append(field)
            else:
                print(f"  ✅ {field}: Present ({len(str(data[field]))} chars)")
                
        if missing_core:
            print(f"❌ FAILED: Missing core fields: {missing_core}")
            return False
        else:
            print("✅ All core diagnosis fields present")
            
        # Test 2: Constitution (stable patterns)
        print("\n🔍 TEST 2: Constitution Structure")
        if 'constitution' not in data:
            print("❌ FAILED: Missing 'constitution' field")
            return False
            
        constitution = data['constitution']
        constitution_fields = [
            'action_style',
            'clarity_style', 
            'timing_tendency',
            'recurring_failure_mode'
        ]
        
        missing_constitution = []
        for field in constitution_fields:
            if field not in constitution:
                missing_constitution.append(field)
            else:
                print(f"  ✅ {field}: {constitution[field]}")
                
        if missing_constitution:
            print(f"❌ FAILED: Missing constitution fields: {missing_constitution}")
            return False
        else:
            print("✅ All constitution fields present")
            
        # Test 3: Evidence Structure
        print("\n🔍 TEST 3: Evidence Structure")
        if 'evidence' not in data:
            print("❌ FAILED: Missing 'evidence' field")
            return False
            
        evidence = data['evidence']
        evidence_types = ['timing', 'design', 'history']
        
        missing_evidence = []
        for evidence_type in evidence_types:
            if evidence_type not in evidence:
                missing_evidence.append(evidence_type)
            else:
                ev = evidence[evidence_type]
                if 'summary' in ev and 'implication' in ev:
                    print(f"  ✅ {evidence_type}: summary + implication present")
                else:
                    print(f"  ⚠️  {evidence_type}: missing summary or implication")
                    
        if missing_evidence:
            print(f"❌ FAILED: Missing evidence types: {missing_evidence}")
            return False
        else:
            print("✅ All evidence types present")
            
        # Test 4: Content Quality Validation
        print("\n🔍 TEST 4: Content Quality Validation")
        
        # Check Pete as Manifestor
        action_style = constitution.get('action_style', '').lower()
        if 'initiating' in action_style or 'manifestor' in action_style:
            print("  ✅ action_style reflects Pete as Manifestor (initiating force)")
        else:
            print(f"  ⚠️  action_style may not reflect Manifestor: {constitution.get('action_style')}")
            
        # Check Emotional authority
        clarity_style = constitution.get('clarity_style', '').lower()
        if 'wave' in clarity_style or 'emotional' in clarity_style:
            print("  ✅ clarity_style reflects Emotional authority (wave-dependent)")
        else:
            print(f"  ⚠️  clarity_style may not reflect Emotional authority: {constitution.get('clarity_style')}")
            
        # Check timing tendency
        timing_tendency = constitution.get('timing_tendency', '').lower()
        if 'initiating' in timing_tendency:
            print("  ✅ timing_tendency is 'initiating'")
        else:
            print(f"  ⚠️  timing_tendency is not 'initiating': {constitution.get('timing_tendency')}")
            
        # Check recurring failure mode
        failure_mode = constitution.get('recurring_failure_mode', '').lower()
        if 'field' in failure_mode and 'ready' in failure_mode:
            print("  ✅ recurring_failure_mode mentions 'moving before the field is ready'")
        else:
            print(f"  ⚠️  recurring_failure_mode doesn't mention field readiness: {constitution.get('recurring_failure_mode')}")
            
        # Test 5: Integration Quality
        print("\n🔍 TEST 5: Integration Quality")
        
        # Check if diagnosis feels integrated vs separate summaries
        full_diagnosis = data.get('full_diagnosis', '')
        why_happening = data.get('why_it_is_happening', '')
        
        # Look for cross-lens integration language
        integration_indicators = ['design', 'history', 'timing', 'pattern']
        integration_count = sum(1 for indicator in integration_indicators if indicator in why_happening.lower())
        
        if integration_count >= 2:
            print(f"  ✅ Cross-lens integration detected ({integration_count} integration indicators)")
        else:
            print(f"  ⚠️  Limited cross-lens integration detected ({integration_count} indicators)")
            
        # Check moment_type is specific
        moment_type = data.get('moment_type', '')
        if moment_type and moment_type != 'unknown':
            print(f"  ✅ Specific moment_type: {moment_type}")
        else:
            print(f"  ⚠️  Generic or missing moment_type: {moment_type}")
            
        print("\n🎯 SAMPLE CONTENT ANALYSIS:")
        print(f"📝 what_is_happening: {data.get('what_is_happening', '')[:100]}...")
        print(f"🔍 moment_type: {data.get('moment_type', '')}")
        print(f"⚡ action_style: {constitution.get('action_style', '')}")
        print(f"🌊 clarity_style: {constitution.get('clarity_style', '')}")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def test_multiple_users():
    """Test the endpoint with multiple users to ensure consistency."""
    print("\n🧪 TESTING: Multiple Users")
    print("=" * 40)
    
    test_users = [
        "697f0c6abf35c0528ff06954",  # Pete (primary test user)
        "6971c81f2b40fd5ef501d375",  # Secondary test user
    ]
    
    results = []
    for user_id in test_users:
        endpoint = f"{BACKEND_URL}/pattern-diagnosis/{user_id}"
        try:
            response = requests.get(endpoint, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    'user_id': user_id,
                    'status': 'success',
                    'moment_type': data.get('moment_type', 'unknown'),
                    'pattern_family': data.get('pattern_family', 'unknown'),
                    'confidence': data.get('confidence', 0)
                })
                print(f"✅ {user_id}: {data.get('moment_type', 'unknown')} (confidence: {data.get('confidence', 0)})")
            else:
                results.append({
                    'user_id': user_id,
                    'status': 'failed',
                    'error': response.status_code
                })
                print(f"❌ {user_id}: HTTP {response.status_code}")
        except Exception as e:
            results.append({
                'user_id': user_id,
                'status': 'error',
                'error': str(e)
            })
            print(f"❌ {user_id}: {e}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n📊 Results: {success_count}/{len(test_users)} users successful")
    
    return success_count == len(test_users)

def test_error_handling():
    """Test error handling with invalid user ID."""
    print("\n🧪 TESTING: Error Handling")
    print("=" * 30)
    
    invalid_user_id = "invalid_user_id"
    endpoint = f"{BACKEND_URL}/pattern-diagnosis/{invalid_user_id}"
    
    try:
        response = requests.get(endpoint, timeout=15)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Should return graceful fallback
            if data.get('what_is_happening') and data.get('confidence', 0) < 0.5:
                print("✅ Graceful error handling with low confidence fallback")
                return True
            else:
                print("⚠️  Unexpected response for invalid user")
                return False
        else:
            print(f"⚠️  Non-200 status for invalid user: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests for the Cross-Lens Pattern Diagnosis endpoint."""
    print("🚀 CROSS-LENS PATTERN DIAGNOSIS ENDPOINT TESTING")
    print("=" * 80)
    
    tests = [
        ("Core Endpoint Functionality", test_cross_lens_pattern_diagnosis),
        ("Multiple Users", test_multiple_users),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Cross-Lens Pattern Diagnosis endpoint is working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Review the failures above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)