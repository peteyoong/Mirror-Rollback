#!/usr/bin/env python3
"""
Backend Test Suite for Pattern Compression Layer (V2.5)
Testing the GET /api/journal/{user_id}/patterns endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://mirror-journal.preview.emergentagent.com/api"

def test_pattern_compression_layer():
    """
    Test the Pattern Compression Layer (V2.5) feature
    Tests GET /api/journal/{user_id}/patterns endpoint for compressed_pattern_lines field
    """
    print("🧪 TESTING: Pattern Compression Layer (V2.5)")
    print("=" * 60)
    
    # Test user ID from review request
    user_id = "6971c81f2b40fd5ef501d375"
    
    try:
        # Test 1: Call GET /api/journal/{user_id}/patterns
        print(f"\n1. ✅ Testing GET /api/journal/{user_id}/patterns")
        url = f"{BACKEND_URL}/journal/{user_id}/patterns"
        
        response = requests.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED: Invalid JSON response: {e}")
            return False
        
        print(f"   ✅ SUCCESS: Valid JSON response received")
        
        # Test 2: Verify response structure includes all required fields
        print(f"\n2. ✅ Testing response structure")
        required_fields = [
            'user_id',
            'total_entries', 
            'phase_distribution',
            'repeating_phases',
            'phase_patterns',
            'compressed_pattern_lines',  # NEW V2.5 field
            'phase_tensions',
            'identity_tendency',
            'identity_threshold_met'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   ❌ FAILED: Missing required fields: {missing_fields}")
            return False
        
        print(f"   ✅ SUCCESS: All required fields present")
        
        # Test 3: Verify compressed_pattern_lines field structure
        print(f"\n3. ✅ Testing compressed_pattern_lines field")
        compressed_lines = data.get('compressed_pattern_lines', {})
        
        if not isinstance(compressed_lines, dict):
            print(f"   ❌ FAILED: compressed_pattern_lines should be dict, got {type(compressed_lines)}")
            return False
        
        print(f"   ✅ SUCCESS: compressed_pattern_lines is a dictionary")
        print(f"   Compressed lines count: {len(compressed_lines)}")
        
        # Test 4: Verify compressed_pattern_lines content
        print(f"\n4. ✅ Testing compressed_pattern_lines content")
        
        if len(compressed_lines) == 0:
            print(f"   ⚠️  INFO: compressed_pattern_lines is empty (no patterns exist)")
        else:
            print(f"   ✅ SUCCESS: Found {len(compressed_lines)} compressed pattern lines")
            for phase_id, line in compressed_lines.items():
                print(f"   Phase {phase_id}: \"{line}\"")
                
                # Verify each line is a string
                if not isinstance(line, str):
                    print(f"   ❌ FAILED: Pattern line for {phase_id} should be string, got {type(line)}")
                    return False
                
                # Verify line is not empty
                if not line.strip():
                    print(f"   ❌ FAILED: Pattern line for {phase_id} is empty")
                    return False
        
        # Test 5: Verify other response fields for completeness
        print(f"\n5. ✅ Testing other response fields")
        
        # Check user_id matches
        if data.get('user_id') != user_id:
            print(f"   ❌ FAILED: user_id mismatch. Expected {user_id}, got {data.get('user_id')}")
            return False
        
        # Check total_entries is a number
        total_entries = data.get('total_entries')
        if not isinstance(total_entries, int) or total_entries < 0:
            print(f"   ❌ FAILED: total_entries should be non-negative int, got {total_entries}")
            return False
        
        # Check phase_distribution is dict
        phase_dist = data.get('phase_distribution', {})
        if not isinstance(phase_dist, dict):
            print(f"   ❌ FAILED: phase_distribution should be dict, got {type(phase_dist)}")
            return False
        
        # Check repeating_phases is list
        repeating_phases = data.get('repeating_phases', [])
        if not isinstance(repeating_phases, list):
            print(f"   ❌ FAILED: repeating_phases should be list, got {type(repeating_phases)}")
            return False
        
        # Check phase_patterns is dict
        phase_patterns = data.get('phase_patterns', {})
        if not isinstance(phase_patterns, dict):
            print(f"   ❌ FAILED: phase_patterns should be dict, got {type(phase_patterns)}")
            return False
        
        # Check phase_tensions is dict
        phase_tensions = data.get('phase_tensions', {})
        if not isinstance(phase_tensions, dict):
            print(f"   ❌ FAILED: phase_tensions should be dict, got {type(phase_tensions)}")
            return False
        
        # Check identity_threshold_met is boolean
        identity_threshold = data.get('identity_threshold_met')
        if not isinstance(identity_threshold, bool):
            print(f"   ❌ FAILED: identity_threshold_met should be bool, got {type(identity_threshold)}")
            return False
        
        print(f"   ✅ SUCCESS: All response fields have correct types")
        
        # Test 6: Display summary of results
        print(f"\n6. ✅ Test Summary")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Total entries: {data.get('total_entries')}")
        print(f"   Phase distribution: {data.get('phase_distribution')}")
        print(f"   Repeating phases: {data.get('repeating_phases')}")
        print(f"   Phase patterns count: {len(data.get('phase_patterns', {}))}")
        print(f"   Compressed pattern lines count: {len(compressed_lines)}")
        print(f"   Phase tensions count: {len(data.get('phase_tensions', {}))}")
        print(f"   Identity tendency: {data.get('identity_tendency')}")
        print(f"   Identity threshold met: {data.get('identity_threshold_met')}")
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"Pattern Compression Layer (V2.5) is working correctly!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAILED: Request error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all backend tests"""
    print("🚀 BACKEND TESTING SUITE")
    print("Testing Pattern Compression Layer (V2.5)")
    print("=" * 60)
    
    success = test_pattern_compression_layer()
    
    if success:
        print(f"\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()