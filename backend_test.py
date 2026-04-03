#!/usr/bin/env python3
"""
Backend Test Script for V5.2 Astro Expert Endpoint with TRUE HORIZON INTERPRETATION

Test Requirements:
1. Test endpoint with all 3 timeframes: today, week, month
2. All 3 responses MUST have DISTINCT todays_theme values
3. All 3 responses MUST have DISTINCT whats_happening first bullet
4. All 3 responses MUST have DISTINCT one_question values
5. All 3 responses MUST have DISTINCT what_to_do items
6. Version should be "v5.2_horizon"
7. horizon_interpretation.timeframe should match the requested timeframe

Expected distinct themes for Full Moon in Virgo:
- TODAY: "Full Moon in Virgo — Peak Self-Criticism" (immediate peak)
- WEEK: "Full Moon Week — The Same Critical Voice Returning" (recurring pattern)
- MONTH: "This Month's Arc — Learning the Difference Between Care and Control" (larger arc)
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://deployment-fix-25.preview.emergentagent.com/api"

# Test user ID
USER_ID = "697f0c6abf35c0528ff06954"

def test_astro_expert_endpoint():
    """Test V5.2 Astro Expert endpoint with all three timeframes."""
    
    print("🧪 TESTING V5.2 ASTRO EXPERT ENDPOINT WITH TRUE HORIZON INTERPRETATION")
    print("=" * 80)
    
    timeframes = ["today", "week", "month"]
    responses = {}
    
    # Test all three timeframes
    for timeframe in timeframes:
        print(f"\n📅 Testing timeframe: {timeframe.upper()}")
        print("-" * 40)
        
        url = f"{BACKEND_URL}/astro-expert/{USER_ID}?timeframe={timeframe}"
        
        try:
            response = requests.get(url, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                responses[timeframe] = data
                
                # Basic structure validation
                print(f"✅ Success: {data.get('success', False)}")
                print(f"✅ Version: {data.get('version', 'unknown')}")
                print(f"✅ Today's Theme: {data.get('todays_theme', 'missing')}")
                print(f"✅ Whats Happening (first): {data.get('whats_happening', ['missing'])[0] if data.get('whats_happening') else 'missing'}")
                print(f"✅ One Question: {data.get('one_question', 'missing')}")
                print(f"✅ What To Do (first): {data.get('what_to_do', ['missing'])[0] if data.get('what_to_do') else 'missing'}")
                
                # Horizon interpretation validation
                horizon_interp = data.get('horizon_interpretation', {})
                print(f"✅ Horizon Timeframe: {horizon_interp.get('timeframe', 'missing')}")
                print(f"✅ Horizon Source: {horizon_interp.get('horizon_source', 'missing')}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    # Validation of distinct content across timeframes
    print("\n🔍 VALIDATION: DISTINCT CONTENT ACROSS TIMEFRAMES")
    print("=" * 80)
    
    if len(responses) == 3:
        validate_distinct_content(responses)
    else:
        print(f"❌ FAIL: Only got {len(responses)} responses, need 3")
    
    return responses

def validate_distinct_content(responses: Dict[str, Dict[str, Any]]):
    """Validate that all three timeframes have distinct content."""
    
    # Extract key fields for comparison
    themes = {}
    whats_happening_first = {}
    one_questions = {}
    what_to_do_first = {}
    versions = {}
    horizon_timeframes = {}
    
    for timeframe, data in responses.items():
        themes[timeframe] = data.get('todays_theme', '')
        whats_happening_first[timeframe] = data.get('whats_happening', [''])[0] if data.get('whats_happening') else ''
        one_questions[timeframe] = data.get('one_question', '')
        what_to_do_first[timeframe] = data.get('what_to_do', [''])[0] if data.get('what_to_do') else ''
        versions[timeframe] = data.get('version', '')
        
        horizon_interp = data.get('horizon_interpretation', {})
        horizon_timeframes[timeframe] = horizon_interp.get('timeframe', '')
    
    # Test 1: Version should be v5.2_horizon
    print("\n1. VERSION VALIDATION:")
    all_v52 = all(v == "v5.2_horizon" for v in versions.values())
    if all_v52:
        print("✅ PASS: All responses have version 'v5.2_horizon'")
    else:
        print(f"❌ FAIL: Versions not all v5.2_horizon: {versions}")
    
    # Test 2: Horizon timeframes should match requested timeframes
    print("\n2. HORIZON TIMEFRAME VALIDATION:")
    horizon_match = all(horizon_timeframes[tf] == tf for tf in ["today", "week", "month"])
    if horizon_match:
        print("✅ PASS: All horizon_interpretation.timeframe values match requested timeframes")
    else:
        print(f"❌ FAIL: Horizon timeframes don't match: {horizon_timeframes}")
    
    # Test 3: Distinct themes
    print("\n3. DISTINCT THEMES VALIDATION:")
    unique_themes = set(themes.values())
    if len(unique_themes) == 3:
        print("✅ PASS: All three themes are distinct")
        for tf, theme in themes.items():
            print(f"   {tf.upper()}: {theme}")
    else:
        print(f"❌ FAIL: Themes not distinct (found {len(unique_themes)} unique):")
        for tf, theme in themes.items():
            print(f"   {tf.upper()}: {theme}")
    
    # Test 4: Distinct whats_happening first bullets
    print("\n4. DISTINCT WHATS_HAPPENING FIRST BULLETS:")
    unique_whats_happening = set(whats_happening_first.values())
    if len(unique_whats_happening) == 3:
        print("✅ PASS: All three whats_happening first bullets are distinct")
        for tf, bullet in whats_happening_first.items():
            print(f"   {tf.upper()}: {bullet}")
    else:
        print(f"❌ FAIL: whats_happening first bullets not distinct (found {len(unique_whats_happening)} unique):")
        for tf, bullet in whats_happening_first.items():
            print(f"   {tf.upper()}: {bullet}")
    
    # Test 5: Distinct one_question values
    print("\n5. DISTINCT ONE_QUESTION VALIDATION:")
    unique_questions = set(one_questions.values())
    if len(unique_questions) == 3:
        print("✅ PASS: All three one_question values are distinct")
        for tf, question in one_questions.items():
            print(f"   {tf.upper()}: {question}")
    else:
        print(f"❌ FAIL: one_question values not distinct (found {len(unique_questions)} unique):")
        for tf, question in one_questions.items():
            print(f"   {tf.upper()}: {question}")
    
    # Test 6: Distinct what_to_do first items
    print("\n6. DISTINCT WHAT_TO_DO FIRST ITEMS:")
    unique_what_to_do = set(what_to_do_first.values())
    if len(unique_what_to_do) == 3:
        print("✅ PASS: All three what_to_do first items are distinct")
        for tf, action in what_to_do_first.items():
            print(f"   {tf.upper()}: {action}")
    else:
        print(f"❌ FAIL: what_to_do first items not distinct (found {len(unique_what_to_do)} unique):")
        for tf, action in what_to_do_first.items():
            print(f"   {tf.upper()}: {action}")
    
    # Test 7: Expected Full Moon in Virgo themes (if applicable)
    print("\n7. EXPECTED FULL MOON IN VIRGO THEMES:")
    expected_patterns = {
        "today": ["Peak Self-Criticism", "immediate", "peak"],
        "week": ["Same Critical Voice Returning", "recurring", "pattern"],
        "month": ["Learning the Difference Between Care and Control", "larger", "arc"]
    }
    
    for tf, theme in themes.items():
        expected_keywords = expected_patterns.get(tf, [])
        found_keywords = [kw for kw in expected_keywords if kw.lower() in theme.lower()]
        
        if found_keywords:
            print(f"✅ {tf.upper()}: Found expected keywords {found_keywords} in '{theme}'")
        else:
            print(f"⚠️  {tf.upper()}: No expected keywords {expected_keywords} found in '{theme}'")
    
    # Summary
    print("\n📊 SUMMARY:")
    print("=" * 40)
    
    total_tests = 6
    passed_tests = 0
    
    if all_v52:
        passed_tests += 1
    if horizon_match:
        passed_tests += 1
    if len(unique_themes) == 3:
        passed_tests += 1
    if len(unique_whats_happening) == 3:
        passed_tests += 1
    if len(unique_questions) == 3:
        passed_tests += 1
    if len(unique_what_to_do) == 3:
        passed_tests += 1
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! V5.2 Astro Expert endpoint with TRUE HORIZON INTERPRETATION is working correctly.")
    else:
        print(f"❌ {total_tests - passed_tests} tests failed. V5.2 implementation needs fixes.")

def main():
    """Main test execution."""
    try:
        responses = test_astro_expert_endpoint()
        
        # Save responses for debugging
        with open('/app/v52_test_responses.json', 'w') as f:
            json.dump(responses, f, indent=2)
        print(f"\n💾 Responses saved to /app/v52_test_responses.json")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()