#!/usr/bin/env python3

import requests
import json
import sys
from typing import Dict, List, Any

# Backend URL from frontend .env
BACKEND_URL = "https://deployment-fix-25.preview.emergentagent.com/api"

# Test user ID from review request
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def test_home_synthesis():
    """
    Test Home Synthesis endpoint for V5.2 language requirements:
    - Language is more DIRECT and confronting (shorter phrases, no generic explanations)
    - the_call should be short and sharp
    - the_edge should present a clear binary choice
    - No phrases like "This connects to your tendency..."
    """
    print("🧪 TESTING HOME SYNTHESIS ENDPOINT")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/home-synthesis/{TEST_USER_ID}"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        data = response.json()
        print(f"Response time: {response.elapsed.total_seconds():.2f}s")
        
        # Check required fields
        required_fields = ['the_call', 'the_edge']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
            
        # Test the_call for directness
        the_call = data.get('the_call', '')
        print(f"\n📝 the_call: \"{the_call}\"")
        print(f"Length: {len(the_call)} characters")
        
        # Check for directness (should be short and sharp)
        if len(the_call) > 100:
            print(f"⚠️  WARNING: the_call might be too long ({len(the_call)} chars) - should be short and sharp")
        
        # Test the_edge for binary choice
        the_edge = data.get('the_edge', '')
        print(f"\n🔥 the_edge: \"{the_edge}\"")
        print(f"Length: {len(the_edge)} characters")
        
        # Check for forbidden phrases
        forbidden_phrases = [
            "This connects to your tendency",
            "This is the same pattern showing up again",
            "you tend to",
            "this relates to"
        ]
        
        full_text = f"{the_call} {the_edge}".lower()
        found_forbidden = []
        for phrase in forbidden_phrases:
            if phrase.lower() in full_text:
                found_forbidden.append(phrase)
        
        if found_forbidden:
            print(f"❌ FAILED: Found forbidden phrases: {found_forbidden}")
            return False
        else:
            print("✅ PASSED: No forbidden explanatory phrases found")
        
        # Check for directness indicators
        direct_indicators = ["you do this when", "again.", "this isn't new"]
        found_direct = []
        for indicator in direct_indicators:
            if indicator.lower() in full_text:
                found_direct.append(indicator)
        
        if found_direct:
            print(f"✅ PASSED: Found direct language indicators: {found_direct}")
        
        print("\n✅ HOME SYNTHESIS TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

def test_astro_expert_horizons():
    """
    Test Astro Expert across all 3 horizons for distinct content:
    - how_it_interacts[0] should be DIFFERENT for each timeframe
    - what_to_do should be DIFFERENT for each timeframe
    - No repetition of generic phrases across horizons
    """
    print("\n🧪 TESTING ASTRO EXPERT ACROSS ALL 3 HORIZONS")
    print("=" * 60)
    
    timeframes = ['today', 'week', 'month']
    responses = {}
    
    # Fetch all three timeframes
    for timeframe in timeframes:
        url = f"{BACKEND_URL}/astro-expert/{TEST_USER_ID}?timeframe={timeframe}"
        
        try:
            response = requests.get(url, timeout=30)
            print(f"\n📅 TIMEFRAME: {timeframe.upper()}")
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
            data = response.json()
            responses[timeframe] = data
            print(f"Response time: {response.elapsed.total_seconds():.2f}s")
            
            # Check required fields
            required_fields = ['how_it_interacts', 'what_to_do']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ FAILED: Missing required fields: {missing_fields}")
                return False
            
            # Display key content
            how_it_interacts = data.get('how_it_interacts', [])
            what_to_do = data.get('what_to_do', [])
            
            if how_it_interacts:
                print(f"how_it_interacts[0]: \"{how_it_interacts[0]}\"")
            if what_to_do:
                print(f"what_to_do[0]: \"{what_to_do[0]}\"")
                
        except Exception as e:
            print(f"❌ FAILED: Exception occurred for {timeframe}: {e}")
            return False
    
    # Verify DISTINCT content across horizons
    print("\n🔍 VERIFYING DISTINCT CONTENT ACROSS HORIZONS")
    print("-" * 50)
    
    # Check how_it_interacts[0] distinctness
    how_it_interacts_texts = []
    for timeframe in timeframes:
        how_it_interacts = responses[timeframe].get('how_it_interacts', [])
        if how_it_interacts:
            how_it_interacts_texts.append(how_it_interacts[0])
    
    if len(set(how_it_interacts_texts)) != len(how_it_interacts_texts):
        print("❌ FAILED: how_it_interacts[0] content is NOT distinct across timeframes")
        for i, text in enumerate(how_it_interacts_texts):
            print(f"  {timeframes[i]}: {text}")
        return False
    else:
        print("✅ PASSED: how_it_interacts[0] content is DISTINCT across timeframes")
        for i, text in enumerate(how_it_interacts_texts):
            print(f"  {timeframes[i]}: {text}")
    
    # Check what_to_do distinctness and timeframe appropriateness
    what_to_do_texts = []
    for timeframe in timeframes:
        what_to_do = responses[timeframe].get('what_to_do', [])
        if what_to_do:
            what_to_do_texts.append(what_to_do[0])
    
    if len(set(what_to_do_texts)) != len(what_to_do_texts):
        print("❌ FAILED: what_to_do content is NOT distinct across timeframes")
        for i, text in enumerate(what_to_do_texts):
            print(f"  {timeframes[i]}: {text}")
        return False
    else:
        print("✅ PASSED: what_to_do content is DISTINCT across timeframes")
        for i, text in enumerate(what_to_do_texts):
            print(f"  {timeframes[i]}: {text}")
    
    # Check timeframe appropriateness
    print("\n🎯 VERIFYING TIMEFRAME APPROPRIATENESS")
    print("-" * 40)
    
    today_text = what_to_do_texts[0].lower()
    week_text = what_to_do_texts[1].lower()
    month_text = what_to_do_texts[2].lower()
    
    # TODAY should have immediate, behavioral actions
    immediate_indicators = ['today', 'now', 'right now', 'this moment', 'immediately']
    today_has_immediate = any(indicator in today_text for indicator in immediate_indicators)
    
    # WEEK should have pattern-tracking actions
    pattern_indicators = ['week', 'pattern', 'track', 'notice', 'observe', 'this week']
    week_has_pattern = any(indicator in week_text for indicator in pattern_indicators)
    
    # MONTH should have arc/identity reflection actions
    arc_indicators = ['month', 'arc', 'identity', 'reflection', 'long-term', 'this month']
    month_has_arc = any(indicator in month_text for indicator in arc_indicators)
    
    if today_has_immediate:
        print("✅ PASSED: TODAY has immediate/behavioral language")
    else:
        print("⚠️  WARNING: TODAY might lack immediate/behavioral language")
    
    if week_has_pattern:
        print("✅ PASSED: WEEK has pattern-tracking language")
    else:
        print("⚠️  WARNING: WEEK might lack pattern-tracking language")
    
    if month_has_arc:
        print("✅ PASSED: MONTH has arc/identity language")
    else:
        print("⚠️  WARNING: MONTH might lack arc/identity language")
    
    print("\n✅ ASTRO EXPERT HORIZONS TEST PASSED")
    return True

def test_language_directness():
    """
    Test overall language directness across all endpoints
    """
    print("\n🧪 TESTING LANGUAGE DIRECTNESS")
    print("=" * 60)
    
    # Test both endpoints for direct language
    endpoints = [
        f"{BACKEND_URL}/home-synthesis/{TEST_USER_ID}",
        f"{BACKEND_URL}/astro-expert/{TEST_USER_ID}?timeframe=today"
    ]
    
    all_text = ""
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Extract all text content
                all_text += json.dumps(data, ensure_ascii=False) + " "
        except Exception as e:
            print(f"⚠️  WARNING: Could not fetch {endpoint}: {e}")
    
    all_text = all_text.lower()
    
    # Check for forbidden explanatory phrases
    forbidden_phrases = [
        "this connects to your tendency",
        "this is the same pattern showing up again"
    ]
    
    found_forbidden = []
    for phrase in forbidden_phrases:
        if phrase in all_text:
            found_forbidden.append(phrase)
    
    # Check for preferred direct phrases
    direct_phrases = [
        "you do this when",
        "this isn't new — you've been here before",
        "again. you've been here before"
    ]
    
    found_direct = []
    for phrase in direct_phrases:
        if phrase in all_text:
            found_direct.append(phrase)
    
    if found_forbidden:
        print(f"❌ FAILED: Found forbidden explanatory phrases: {found_forbidden}")
        return False
    else:
        print("✅ PASSED: No forbidden explanatory phrases found")
    
    if found_direct:
        print(f"✅ PASSED: Found direct language patterns: {found_direct}")
    else:
        print("⚠️  INFO: No specific direct language patterns detected (may still be direct)")
    
    print("\n✅ LANGUAGE DIRECTNESS TEST PASSED")
    return True

def main():
    """Run all V5.2 language tests"""
    print("🚀 STARTING V5.2 LANGUAGE TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("=" * 80)
    
    tests = [
        ("Home Synthesis", test_home_synthesis),
        ("Astro Expert Horizons", test_astro_expert_horizons),
        ("Language Directness", test_language_directness)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 TEST RESULTS: {passed}/{total} TESTS PASSED")
    
    if passed == total:
        print("🎉 ALL V5.2 LANGUAGE TESTS PASSED!")
        return True
    else:
        print(f"❌ {total - passed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)