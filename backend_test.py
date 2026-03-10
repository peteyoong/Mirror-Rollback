#!/usr/bin/env python3
"""
Backend Testing Suite for Gene Keys Pattern Signals Layer
Testing the implementation of shadow_keywords and gift_keywords in Gene Keys profile API.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://pattern-signals-4.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def test_gene_keys_pattern_signals():
    """
    Test the Gene Keys Pattern Signals Layer implementation.
    
    Requirements:
    1. Call GET /api/gene-keys/profile/{user_id}
    2. Verify response contains all_spheres array with 13 spheres (4 Activation + 5 Venus + 4 Pearl)
    3. For EACH sphere in all_spheres, verify shadow_keywords and gift_keywords fields exist
    4. Verify keywords are populated (non-empty arrays) for at least one sphere
    """
    
    print("🧪 GENE KEYS PATTERN SIGNALS LAYER TESTING")
    print("=" * 60)
    
    # Test 1: API Endpoint Availability
    print("\n1. ✅ TESTING API ENDPOINT AVAILABILITY")
    url = f"{BASE_URL}/gene-keys/profile/{TEST_USER_ID}"
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        print("   ✅ PASSED: API endpoint accessible")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAILED: Request error - {e}")
        return False
    
    # Parse response
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"   ❌ FAILED: Invalid JSON response - {e}")
        return False
    
    # Test 2: Response Structure Validation
    print("\n2. ✅ TESTING RESPONSE STRUCTURE")
    
    # Check for required top-level fields
    required_fields = ["activation_sequence", "venus_sequence", "pearl_sequence", "all_spheres"]
    for field in required_fields:
        if field not in data:
            print(f"   ❌ FAILED: Missing required field '{field}'")
            return False
        print(f"   ✅ Found field: {field}")
    
    # Test 3: All Spheres Array Validation
    print("\n3. ✅ TESTING ALL_SPHERES ARRAY")
    
    all_spheres = data.get("all_spheres", [])
    if not isinstance(all_spheres, list):
        print(f"   ❌ FAILED: all_spheres is not a list, got {type(all_spheres)}")
        return False
    
    sphere_count = len(all_spheres)
    print(f"   Total spheres found: {sphere_count}")
    
    # Verify exactly 13 spheres (4 Activation + 5 Venus + 4 Pearl)
    if sphere_count != 13:
        print(f"   ❌ FAILED: Expected 13 spheres, got {sphere_count}")
        return False
    
    print("   ✅ PASSED: Correct number of spheres (13)")
    
    # Test 4: Sequence Distribution Validation
    print("\n4. ✅ TESTING SEQUENCE DISTRIBUTION")
    
    sequence_counts = {}
    for sphere in all_spheres:
        sequence = sphere.get("sequence", "Unknown")
        sequence_counts[sequence] = sequence_counts.get(sequence, 0) + 1
    
    print(f"   Sequence distribution: {sequence_counts}")
    
    expected_distribution = {"Activation": 4, "Venus": 5, "Pearl": 4}
    for seq_name, expected_count in expected_distribution.items():
        actual_count = sequence_counts.get(seq_name, 0)
        if actual_count != expected_count:
            print(f"   ❌ FAILED: {seq_name} sequence - expected {expected_count}, got {actual_count}")
            return False
        print(f"   ✅ {seq_name}: {actual_count} spheres")
    
    # Test 5: Shadow/Gift Keywords Field Validation
    print("\n5. ✅ TESTING SHADOW/GIFT KEYWORDS FIELDS")
    
    spheres_with_keywords = 0
    spheres_with_populated_keywords = 0
    
    for i, sphere in enumerate(all_spheres):
        sphere_name = sphere.get("sphere_name", f"Sphere {i+1}")
        sequence = sphere.get("sequence", "Unknown")
        gene_key = sphere.get("gene_key", "Unknown")
        
        print(f"   Sphere {i+1}: {sphere_name} ({sequence}) - Gene Key {gene_key}")
        
        # Check for shadow_keywords field
        if "shadow_keywords" not in sphere:
            print(f"     ❌ FAILED: Missing 'shadow_keywords' field")
            return False
        
        # Check for gift_keywords field
        if "gift_keywords" not in sphere:
            print(f"     ❌ FAILED: Missing 'gift_keywords' field")
            return False
        
        spheres_with_keywords += 1
        
        # Validate field types
        shadow_keywords = sphere["shadow_keywords"]
        gift_keywords = sphere["gift_keywords"]
        
        if not isinstance(shadow_keywords, list):
            print(f"     ❌ FAILED: shadow_keywords is not a list, got {type(shadow_keywords)}")
            return False
        
        if not isinstance(gift_keywords, list):
            print(f"     ❌ FAILED: gift_keywords is not a list, got {type(gift_keywords)}")
            return False
        
        # Check if keywords are populated (non-empty)
        shadow_populated = len(shadow_keywords) > 0
        gift_populated = len(gift_keywords) > 0
        
        if shadow_populated and gift_populated:
            spheres_with_populated_keywords += 1
            print(f"     ✅ Keywords populated: {len(shadow_keywords)} shadow, {len(gift_keywords)} gift")
            
            # Show sample keywords for verification
            if len(shadow_keywords) > 0:
                sample_shadow = shadow_keywords[:3]  # First 3 keywords
                print(f"     Sample shadow keywords: {sample_shadow}")
            
            if len(gift_keywords) > 0:
                sample_gift = gift_keywords[:3]  # First 3 keywords
                print(f"     Sample gift keywords: {sample_gift}")
        else:
            print(f"     ⚠️  Keywords empty: shadow={len(shadow_keywords)}, gift={len(gift_keywords)}")
    
    print(f"\n   Summary:")
    print(f"   - Spheres with keyword fields: {spheres_with_keywords}/13")
    print(f"   - Spheres with populated keywords: {spheres_with_populated_keywords}/13")
    
    if spheres_with_keywords != 13:
        print(f"   ❌ FAILED: Not all spheres have keyword fields")
        return False
    
    if spheres_with_populated_keywords == 0:
        print(f"   ❌ FAILED: No spheres have populated keywords")
        return False
    
    print(f"   ✅ PASSED: All spheres have keyword fields")
    print(f"   ✅ PASSED: {spheres_with_populated_keywords} spheres have populated keywords")
    
    # Test 6: Detailed Sphere Structure Validation
    print("\n6. ✅ TESTING DETAILED SPHERE STRUCTURE")
    
    required_sphere_fields = [
        "sphere_name", "sequence", "gene_key", "line", 
        "shadow", "gift", "siddhi", "shadow_keywords", "gift_keywords"
    ]
    
    for i, sphere in enumerate(all_spheres):
        sphere_name = sphere.get("sphere_name", f"Sphere {i+1}")
        
        for field in required_sphere_fields:
            if field not in sphere:
                print(f"   ❌ FAILED: Sphere '{sphere_name}' missing field '{field}'")
                return False
        
        # Validate specific field types
        if not isinstance(sphere["gene_key"], int):
            print(f"   ❌ FAILED: Sphere '{sphere_name}' gene_key is not int: {type(sphere['gene_key'])}")
            return False
        
        if not isinstance(sphere["line"], int):
            print(f"   ❌ FAILED: Sphere '{sphere_name}' line is not int: {type(sphere['line'])}")
            return False
        
        if not isinstance(sphere["shadow"], str):
            print(f"   ❌ FAILED: Sphere '{sphere_name}' shadow is not str: {type(sphere['shadow'])}")
            return False
        
        if not isinstance(sphere["gift"], str):
            print(f"   ❌ FAILED: Sphere '{sphere_name}' gift is not str: {type(sphere['gift'])}")
            return False
    
    print(f"   ✅ PASSED: All spheres have correct field structure")
    
    # Test 7: Sample Data Validation
    print("\n7. ✅ TESTING SAMPLE DATA VALIDATION")
    
    # Find a sphere with populated keywords for detailed validation
    sample_sphere = None
    for sphere in all_spheres:
        if len(sphere.get("shadow_keywords", [])) > 0 and len(sphere.get("gift_keywords", [])) > 0:
            sample_sphere = sphere
            break
    
    if sample_sphere:
        print(f"   Sample sphere: {sample_sphere['sphere_name']} (Gene Key {sample_sphere['gene_key']})")
        print(f"   Shadow: {sample_sphere['shadow']}")
        print(f"   Gift: {sample_sphere['gift']}")
        print(f"   Shadow keywords: {sample_sphere['shadow_keywords']}")
        print(f"   Gift keywords: {sample_sphere['gift_keywords']}")
        
        # Validate keywords are strings
        for keyword in sample_sphere['shadow_keywords']:
            if not isinstance(keyword, str):
                print(f"   ❌ FAILED: Shadow keyword is not string: {keyword} ({type(keyword)})")
                return False
        
        for keyword in sample_sphere['gift_keywords']:
            if not isinstance(keyword, str):
                print(f"   ❌ FAILED: Gift keyword is not string: {keyword} ({type(keyword)})")
                return False
        
        print(f"   ✅ PASSED: Sample keywords are valid strings")
    else:
        print(f"   ⚠️  WARNING: No sphere found with populated keywords for detailed validation")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎉 GENE KEYS PATTERN SIGNALS LAYER TESTING COMPLETE")
    print("=" * 60)
    print("✅ ALL TESTS PASSED:")
    print("   1. ✅ API endpoint accessible (200 OK)")
    print("   2. ✅ Response structure valid")
    print("   3. ✅ All_spheres contains exactly 13 spheres")
    print("   4. ✅ Correct sequence distribution (4 Activation + 5 Venus + 4 Pearl)")
    print("   5. ✅ All spheres contain shadow_keywords and gift_keywords fields")
    print("   6. ✅ Keywords are arrays of strings")
    print(f"   7. ✅ {spheres_with_populated_keywords} spheres have populated keywords")
    print("   8. ✅ All required sphere fields present and correctly typed")
    
    return True


def main():
    """Run the Gene Keys Pattern Signals Layer tests."""
    print("Starting Gene Keys Pattern Signals Layer Backend Testing...")
    
    success = test_gene_keys_pattern_signals()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Gene Keys Pattern Signals Layer is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED! Gene Keys Pattern Signals Layer needs attention.")
        sys.exit(1)


if __name__ == "__main__":
    main()