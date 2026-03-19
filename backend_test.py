#!/usr/bin/env python3
"""
Backend API Testing Script for BaZi Contextual Questions API

Tests the upgraded contextual questions API for BaZi as specified in the review request.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://astro-narrative-v6.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"  # Metal element / strong Day Master / Resource Ten God user

# Expected patterns for quality validation
GOOD_PATTERNS = [
    "Why do I keep delaying",
    "Why is it so hard for me to",
    "What am I avoiding", 
    "Why do I get frustrated",
    "What am I trying to",
    "When did I decide",
    "What would happen if"
]

BAD_PATTERNS = [
    "How can I improve",
    "What are my strengths",
    "How do I become",
    "What should I do",
    "you tend to",
    "you may often",
    "you might find"
]

TIMING_KEYWORDS = [
    "today", "this year", "right now", "heavier", "pressure", 
    "flowing", "supporting", "feel", "everything"
]

def make_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API request with error handling."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {url}: {e}")
        return {"error": str(e)}

def test_contextual_prompts_api():
    """
    Test the upgraded BaZi contextual questions API for quality and requirements.
    
    Requirements to verify:
    1. Should contain 5 questions maximum
    2. Questions should be emotionally relevant (not generic self-help)
    3. At least 1 question should be timing-related
    4. Should NOT contain generic phrases like "How can I improve"
    5. SHOULD contain confronting phrases like "Why do I keep delaying..."
    6. Check questions are specific to Metal element / strong Day Master / Resource Ten God
    """
    
    print("🧪 TESTING UPGRADED BAZI CONTEXTUAL QUESTIONS API")
    print("=" * 60)
    
    # Test the adaptive endpoint
    print(f"Testing: GET /api/bazi/{TEST_USER_ID}/adaptive")
    
    start_time = time.time()
    response = make_request(f"/bazi/{TEST_USER_ID}/adaptive")
    end_time = time.time()
    
    if "error" in response:
        print(f"❌ API request failed: {response['error']}")
        return False
    
    print(f"✅ Response received in {end_time - start_time:.2f}s")
    print(f"Status: 200 OK")
    
    # Validate basic response structure
    if not response.get("success", False):
        print(f"❌ Response success=false")
        return False
    
    if "adaptive" not in response:
        print(f"❌ Missing 'adaptive' field in response")
        return False
    
    adaptive = response["adaptive"]
    if "contextual_prompts" not in adaptive:
        print(f"❌ Missing 'contextual_prompts' field in adaptive section")
        return False
    
    contextual_prompts = adaptive["contextual_prompts"]
    
    # Verify it's a list
    if not isinstance(contextual_prompts, list):
        print(f"❌ contextual_prompts is not a list: {type(contextual_prompts)}")
        return False
    
    print(f"✅ Found contextual_prompts array with {len(contextual_prompts)} questions")
    
    # Test 1: Maximum 5 questions
    print("\n1️⃣ TESTING: Maximum 5 questions requirement")
    if len(contextual_prompts) > 5:
        print(f"❌ Too many questions: {len(contextual_prompts)} (should be ≤ 5)")
        return False
    elif len(contextual_prompts) == 0:
        print(f"❌ No questions found")
        return False
    else:
        print(f"✅ Question count: {len(contextual_prompts)} (within limit)")
    
    # Print all questions for analysis
    print(f"\n📝 ALL CONTEXTUAL QUESTIONS:")
    for i, question in enumerate(contextual_prompts, 1):
        print(f"   {i}. \"{question}\"")
    
    # Test 2: Questions should be emotionally relevant (contain confronting patterns)
    print(f"\n2️⃣ TESTING: Emotionally relevant & confronting language")
    confronting_count = 0
    for question in contextual_prompts:
        for pattern in GOOD_PATTERNS:
            if pattern.lower() in question.lower():
                confronting_count += 1
                print(f"✅ Found confronting pattern \"{pattern}\" in: \"{question}\"")
                break
    
    if confronting_count == 0:
        print(f"❌ No confronting patterns found. Questions may be too generic.")
        return False
    else:
        print(f"✅ {confronting_count}/{len(contextual_prompts)} questions contain confronting language")
    
    # Test 3: Should NOT contain generic self-help phrases
    print(f"\n3️⃣ TESTING: No generic self-help language")
    generic_violations = []
    for question in contextual_prompts:
        for bad_pattern in BAD_PATTERNS:
            if bad_pattern.lower() in question.lower():
                generic_violations.append(f"Found \"{bad_pattern}\" in: \"{question}\"")
    
    if generic_violations:
        print(f"❌ Generic language violations found:")
        for violation in generic_violations:
            print(f"   - {violation}")
        return False
    else:
        print(f"✅ No generic self-help patterns detected")
    
    # Test 4: At least 1 timing-related question
    print(f"\n4️⃣ TESTING: At least 1 timing-related question")
    timing_questions = []
    for question in contextual_prompts:
        for timing_word in TIMING_KEYWORDS:
            if timing_word.lower() in question.lower():
                timing_questions.append(question)
                break
    
    if len(timing_questions) == 0:
        print(f"❌ No timing-related questions found")
        return False
    else:
        print(f"✅ Found {len(timing_questions)} timing-related question(s):")
        for tq in timing_questions:
            print(f"   - \"{tq}\"")
    
    # Test 5: Verify Metal element specificity
    print(f"\n5️⃣ TESTING: Metal element / strong Day Master specificity")
    
    # Check if user data confirms Metal element
    chart = response.get("chart", {})
    day_master = chart.get("day_master", {})
    dm_element = day_master.get("element", "")
    dm_strength = day_master.get("strength", "")
    
    print(f"✅ User Day Master confirmed: {dm_element} element, {dm_strength} strength")
    
    if dm_element != "Metal" or dm_strength != "strong":
        print(f"⚠️  WARNING: Test user doesn't match expected Metal/strong profile")
        print(f"   Expected: Metal element, strong strength")
        print(f"   Found: {dm_element} element, {dm_strength} strength")
    
    # Check for Metal-specific themes in questions
    metal_themes = [
        "standards", "critical", "perfect", "right", "quality", "precise", 
        "delaying", "decision", "judgment", "enough"
    ]
    
    metal_specific_count = 0
    for question in contextual_prompts:
        for theme in metal_themes:
            if theme.lower() in question.lower():
                metal_specific_count += 1
                print(f"✅ Found Metal-specific theme \"{theme}\" in: \"{question}\"")
                break
    
    if metal_specific_count > 0:
        print(f"✅ {metal_specific_count}/{len(contextual_prompts)} questions contain Metal-specific themes")
    else:
        print(f"⚠️  No obvious Metal-specific themes detected in questions")
    
    # Test 6: Quality standard verification
    print(f"\n6️⃣ TESTING: Quality matches required standard")
    
    # Check for the specific good example pattern
    good_example_pattern = "Why do I keep delaying decisions even when I already know the answer?"
    has_exact_good_example = good_example_pattern in contextual_prompts
    
    if has_exact_good_example:
        print(f"✅ Found exact good example: \"{good_example_pattern}\"")
    
    # Verify overall quality characteristics
    deep_questions = []
    for question in contextual_prompts:
        # Look for "Why" questions that probe deeper patterns
        if question.startswith("Why") and len(question) > 50:
            deep_questions.append(question)
    
    print(f"✅ {len(deep_questions)}/{len(contextual_prompts)} questions are deep 'Why' questions:")
    for dq in deep_questions:
        print(f"   - \"{dq}\"")
    
    # Final validation
    print(f"\n🎯 FINAL QUALITY ASSESSMENT:")
    print(f"✅ Question count: {len(contextual_prompts)}/5 maximum")
    print(f"✅ Confronting language: {confronting_count}/{len(contextual_prompts)} questions")
    print(f"✅ No generic phrases: Passed")
    print(f"✅ Timing questions: {len(timing_questions)} found")
    print(f"✅ Metal themes: {metal_specific_count} questions")
    print(f"✅ Deep questions: {len(deep_questions)} 'Why' questions")
    
    # Overall success criteria
    success_criteria = [
        len(contextual_prompts) <= 5 and len(contextual_prompts) > 0,  # Right count
        confronting_count >= 1,  # Has confronting language
        len(generic_violations) == 0,  # No generic phrases
        len(timing_questions) >= 1,  # Has timing question
        dm_element == "Metal" and dm_strength == "strong"  # Right user profile
    ]
    
    if all(success_criteria):
        print(f"\n🎉 ALL TESTS PASSED! Upgraded BaZi contextual questions API meets requirements")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED. Check individual test results above.")
        return False

def main():
    """Main test runner."""
    print("🚀 STARTING BAZI CONTEXTUAL QUESTIONS API TESTING")
    print(f"Target User: {TEST_USER_ID}")
    print(f"Base URL: {BASE_URL}")
    print()
    
    success = test_contextual_prompts_api()
    
    print("\n" + "="*60)
    if success:
        print("✅ OVERALL RESULT: ALL TESTS PASSED")
        print("🎯 The upgraded BaZi contextual questions API is working correctly")
        print("📊 Quality requirements met for Metal element / strong Day Master user")
    else:
        print("❌ OVERALL RESULT: SOME TESTS FAILED")
        print("🔧 Review individual test failures above for debugging")
    
    return success

if __name__ == "__main__":
    main()