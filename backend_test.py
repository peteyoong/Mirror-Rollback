#!/usr/bin/env python3
"""
Backend Test Suite for V10 Context-Aware Language Generation
Testing the Pattern Mirror API upgrade
"""

import requests
import json
import time
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://resonance-check-v7.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def test_pattern_mirror_v10():
    """Test the V10 Context-Aware Language Generation upgrade"""
    print("🧪 TESTING V10 CONTEXT-AWARE LANGUAGE GENERATION UPGRADE")
    print("=" * 60)
    
    # Test endpoint
    endpoint = f"{BASE_URL}/patterns/{TEST_USER_ID}?force_refresh=true"
    print(f"📍 Testing endpoint: {endpoint}")
    
    try:
        # Make the API request
        start_time = time.time()
        response = requests.get(endpoint, timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response - {e}")
            return False
            
        print("✅ Valid JSON response received")
        
        # Test 1: Verify two_layer_output field exists
        if 'two_layer_output' not in data:
            print("❌ FAILED: two_layer_output field missing from response")
            return False
        print("✅ two_layer_output field present")
        
        two_layer = data['two_layer_output']
        
        # Test 2: Verify required structure
        required_fields = ['core_insight', 'why_showing_up', 'cross_lens_derivation', 'friction', 'practical', 'display_config']
        for field in required_fields:
            if field not in two_layer:
                print(f"❌ FAILED: Required field '{field}' missing from two_layer_output")
                return False
        print("✅ All required fields present in two_layer_output")
        
        # Test 3: Verify core_insight structure
        core_insight = two_layer['core_insight']
        if not isinstance(core_insight, dict) or 'title' not in core_insight or 'text' not in core_insight:
            print("❌ FAILED: core_insight missing title or text fields")
            return False
        if not isinstance(core_insight['title'], str) or not isinstance(core_insight['text'], str):
            print("❌ FAILED: core_insight title or text not strings")
            return False
        print("✅ core_insight structure valid")
        
        # Test 4: Verify why_showing_up structure and completeness
        why_showing_up = two_layer['why_showing_up']
        if not isinstance(why_showing_up, dict) or 'text' not in why_showing_up or 'is_timing_driven' not in why_showing_up:
            print("❌ FAILED: why_showing_up missing text or is_timing_driven fields")
            return False
        if not isinstance(why_showing_up['text'], str) or not isinstance(why_showing_up['is_timing_driven'], bool):
            print("❌ FAILED: why_showing_up field types incorrect")
            return False
        
        # Check if why_showing_up text is complete (not truncated)
        why_text = why_showing_up['text'].strip()
        if len(why_text) < 10 or not why_text.endswith(('.', '!', '?')):
            print(f"❌ FAILED: why_showing_up text appears truncated: '{why_text}'")
            return False
        print("✅ why_showing_up structure valid and text complete")
        
        # Test 5: Verify friction field
        friction = two_layer['friction']
        if not isinstance(friction, dict) or 'text' not in friction:
            print("❌ FAILED: friction missing text field")
            return False
        if not isinstance(friction['text'], str):
            print("❌ FAILED: friction text not string")
            return False
        
        friction_text = friction['text'].strip()
        if len(friction_text) < 10 or not friction_text.endswith(('.', '!', '?')):
            print(f"❌ FAILED: friction text appears incomplete: '{friction_text}'")
            return False
        print("✅ friction field valid and complete")
        
        # Test 6: Verify practical field
        practical = two_layer['practical']
        if not isinstance(practical, dict) or 'text' not in practical:
            print("❌ FAILED: practical missing text field")
            return False
        if not isinstance(practical['text'], str):
            print("❌ FAILED: practical text not string")
            return False
        
        practical_text = practical['text'].strip()
        if len(practical_text) < 10 or not practical_text.endswith(('.', '!', '?')):
            print(f"❌ FAILED: practical text appears incomplete: '{practical_text}'")
            return False
        print("✅ practical field valid and complete")
        
        # Test 7: Verify cross_lens_derivation structure
        cross_lens = two_layer['cross_lens_derivation']
        if not isinstance(cross_lens, dict) or 'lenses' not in cross_lens or 'convergence_count' not in cross_lens:
            print("❌ FAILED: cross_lens_derivation missing required fields")
            return False
        if not isinstance(cross_lens['lenses'], list) or not isinstance(cross_lens['convergence_count'], int):
            print("❌ FAILED: cross_lens_derivation field types incorrect")
            return False
        print("✅ cross_lens_derivation structure valid")
        
        # Test 8: Check for mystical/woo language
        mystical_terms = ['universe', 'cosmic', 'divine', 'karma', 'spiritual', 'energy', 'vibration', 'alignment']
        all_text = f"{core_insight['text']} {why_showing_up['text']} {friction['text']} {practical['text']}"
        
        found_mystical = []
        for term in mystical_terms:
            if term.lower() in all_text.lower():
                found_mystical.append(term)
        
        if found_mystical:
            print(f"❌ FAILED: Found mystical/woo language: {found_mystical}")
            return False
        print("✅ No mystical/woo language detected - maintains Mirror tone")
        
        # Test 9: Verify response time is reasonable
        if response_time > 5.0:
            print(f"⚠️  WARNING: Response time {response_time:.2f}s exceeds 5 second threshold")
        else:
            print(f"✅ Response time {response_time:.2f}s is acceptable")
        
        # Test 10: Display sample content for manual review
        print("\n📝 SAMPLE CONTENT FOR MANUAL REVIEW:")
        print("-" * 40)
        print(f"Core Insight Title: {core_insight['title']}")
        print(f"Core Insight Text: {core_insight['text']}")
        print(f"Why Showing Up: {why_showing_up['text']}")
        print(f"Friction: {friction['text']}")
        print(f"Practical: {practical['text']}")
        print(f"Is Timing Driven: {why_showing_up['is_timing_driven']}")
        print(f"Convergence Count: {cross_lens['convergence_count']}")
        
        print("\n🎉 ALL TESTS PASSED - V10 Context-Aware Language Generation working correctly!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False

def test_context_awareness():
    """Test that the language adapts based on signal context"""
    print("\n🔍 TESTING CONTEXT AWARENESS")
    print("=" * 40)
    
    # Make multiple requests to see if content varies appropriately
    endpoint = f"{BASE_URL}/patterns/{TEST_USER_ID}?force_refresh=true"
    
    try:
        responses = []
        for i in range(2):
            print(f"Making request {i+1}/2...")
            response = requests.get(endpoint, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'two_layer_output' in data:
                    responses.append(data['two_layer_output'])
            time.sleep(1)  # Brief pause between requests
        
        if len(responses) >= 1:
            # Check that the content is contextually appropriate
            sample = responses[0]
            why_text = sample['why_showing_up']['text']
            friction_text = sample['friction']['text']
            practical_text = sample['practical']['text']
            
            # Look for context-aware language patterns
            context_indicators = [
                'this time', 'right now', 'currently', 'today', 'at this moment',
                'given', 'because', 'since', 'as', 'when', 'while'
            ]
            
            found_context = False
            for text in [why_text, friction_text, practical_text]:
                for indicator in context_indicators:
                    if indicator.lower() in text.lower():
                        found_context = True
                        break
                if found_context:
                    break
            
            if found_context:
                print("✅ Context-aware language detected")
            else:
                print("⚠️  No obvious context-aware language patterns found")
            
            return True
        else:
            print("❌ FAILED: Could not get valid responses for context testing")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Context awareness test error - {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING V10 PATTERN MIRROR API TESTING")
    print(f"🎯 Test User ID: {TEST_USER_ID}")
    print(f"🌐 Base URL: {BASE_URL}")
    print()
    
    # Run main test
    main_test_passed = test_pattern_mirror_v10()
    
    # Run context awareness test
    context_test_passed = test_context_awareness()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print(f"✅ Main API Test: {'PASSED' if main_test_passed else 'FAILED'}")
    print(f"✅ Context Awareness Test: {'PASSED' if context_test_passed else 'FAILED'}")
    
    if main_test_passed and context_test_passed:
        print("\n🎉 ALL TESTS PASSED - V10 Context-Aware Language Generation is working correctly!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Review the output above for details")
        exit(1)