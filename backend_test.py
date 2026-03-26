#!/usr/bin/env python3
"""
Backend Testing Script for TODAY'S PATTERN v2 API Endpoint
Testing the NOW SIGNAL ENGINE implementation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Backend URL configuration
BACKEND_URL = "https://signal-layer-preview.preview.emergentagent.com/api"

# Test user ID from review request
TEST_USER_ID = "69bf562ac23ef591409d535a"

# Expected pattern titles from the review request
EXPECTED_TITLES = [
    "Forward and Back", "What's Unsaid", "Grip and Release", 
    "Still Searching", "The Pause", "Something Stirring", 
    "Processing", "Waiting", "Moving"
]

# Expected sources from the review request
EXPECTED_SOURCES = ["journal", "human_design", "enneagram", "transits", "baseline", "fallback"]

def test_basic_endpoint():
    """Test 1: Basic endpoint functionality"""
    print("🧪 TEST 1: Basic endpoint functionality")
    print(f"Testing endpoint: GET {BACKEND_URL}/today-pattern/{TEST_USER_ID}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/today-pattern/{TEST_USER_ID}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        data = response.json()
        print(f"✅ SUCCESS: Endpoint returned 200 OK")
        
        # Check required fields
        required_fields = ["title", "lines", "confidence", "sources", "date", "follow_through", "follow_through_route"]
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
            
        print(f"✅ SUCCESS: All required fields present")
        
        # Validate field types and constraints
        if not isinstance(data["lines"], list) or len(data["lines"]) != 3:
            print(f"❌ FAILED: Lines should be array of exactly 3 items, got {len(data.get('lines', []))}")
            return False
            
        if not isinstance(data["confidence"], (int, float)) or not (0.2 <= data["confidence"] <= 0.95):
            print(f"❌ FAILED: Confidence should be float between 0.2-0.95, got {data.get('confidence')}")
            return False
            
        if not isinstance(data["sources"], list) or len(data["sources"]) == 0:
            print(f"❌ FAILED: Sources should be non-empty array, got {data.get('sources')}")
            return False
            
        print(f"✅ SUCCESS: Field types and constraints validated")
        
        # Check if title is one of expected patterns
        title = data.get("title", "")
        if title not in EXPECTED_TITLES:
            print(f"⚠️  WARNING: Title '{title}' not in expected list, but this may be valid")
        else:
            print(f"✅ SUCCESS: Title '{title}' is in expected pattern list")
            
        # Validate lines are micro-moments (specific behavioral statements)
        lines = data.get("lines", [])
        for i, line in enumerate(lines):
            if len(line.strip()) < 10:  # Basic check for meaningful content
                print(f"❌ FAILED: Line {i+1} too short: '{line}'")
                return False
                
        print(f"✅ SUCCESS: All lines contain meaningful content")
        
        # Check sources are valid
        sources = data.get("sources", [])
        invalid_sources = [s for s in sources if s not in EXPECTED_SOURCES]
        if invalid_sources:
            print(f"⚠️  WARNING: Unexpected sources: {invalid_sources}")
        else:
            print(f"✅ SUCCESS: All sources are valid")
            
        print(f"📊 Response Summary:")
        print(f"   Title: {data.get('title')}")
        print(f"   Lines: {len(data.get('lines', []))} lines")
        print(f"   Confidence: {data.get('confidence')}")
        print(f"   Sources: {data.get('sources')}")
        print(f"   Date: {data.get('date')}")
        print(f"   Follow-through: {data.get('follow_through')}")
        print(f"   Follow-through route: {data.get('follow_through_route')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def test_force_refresh():
    """Test 2: Force refresh functionality"""
    print("\n🧪 TEST 2: Force refresh functionality")
    print(f"Testing endpoint: GET {BACKEND_URL}/today-pattern/{TEST_USER_ID}?force_refresh=true")
    
    try:
        response = requests.get(f"{BACKEND_URL}/today-pattern/{TEST_USER_ID}?force_refresh=true", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
            
        data = response.json()
        
        # Check that cached is false when force_refresh=true
        if data.get("cached", True):
            print(f"❌ FAILED: Expected cached=false with force_refresh=true, got cached={data.get('cached')}")
            return False
            
        print(f"✅ SUCCESS: Force refresh working correctly (cached: {data.get('cached')})")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error during force refresh test: {e}")
        return False

def test_response_structure():
    """Test 3: Detailed response structure validation"""
    print("\n🧪 TEST 3: Detailed response structure validation")
    
    try:
        response = requests.get(f"{BACKEND_URL}/today-pattern/{TEST_USER_ID}?force_refresh=true", timeout=30)
        data = response.json()
        
        # Validate title format
        title = data.get("title", "")
        if not title or len(title.strip()) < 3:
            print(f"❌ FAILED: Title too short or empty: '{title}'")
            return False
        print(f"✅ SUCCESS: Title format valid: '{title}'")
        
        # Validate lines are micro-moments (not themes)
        lines = data.get("lines", [])
        if len(lines) != 3:
            print(f"❌ FAILED: Expected exactly 3 lines, got {len(lines)}")
            return False
            
        # Check that lines are specific behavioral statements
        behavioral_indicators = ["you", "your", "might", "may", "could", "feel", "notice", "sense", "find"]
        for i, line in enumerate(lines):
            has_behavioral_language = any(indicator in line.lower() for indicator in behavioral_indicators)
            if not has_behavioral_language:
                print(f"⚠️  WARNING: Line {i+1} may not be behavioral micro-moment: '{line}'")
            else:
                print(f"✅ SUCCESS: Line {i+1} contains behavioral language")
                
        # Validate confidence range
        confidence = data.get("confidence", 0)
        if not (0.2 <= confidence <= 0.95):
            print(f"❌ FAILED: Confidence {confidence} outside expected range 0.2-0.95")
            return False
        print(f"✅ SUCCESS: Confidence {confidence} within valid range")
        
        # Check for low confidence soft language
        if confidence < 0.4:
            soft_indicators = ["something", "might", "may", "could", "perhaps", "seems", "feels like"]
            text_content = " ".join(lines).lower()
            has_soft_language = any(indicator in text_content for indicator in soft_indicators)
            if has_soft_language:
                print(f"✅ SUCCESS: Low confidence ({confidence}) uses appropriate soft language")
            else:
                print(f"⚠️  WARNING: Low confidence ({confidence}) but no soft language detected")
                
        # Validate sources
        sources = data.get("sources", [])
        if not sources:
            print(f"❌ FAILED: No sources provided")
            return False
        print(f"✅ SUCCESS: Sources provided: {sources}")
        
        # Validate follow-through logic
        follow_through = data.get("follow_through")
        follow_through_route = data.get("follow_through_route")
        
        if follow_through and not follow_through_route:
            print(f"⚠️  WARNING: Follow-through text provided but no route specified")
        elif follow_through_route and not follow_through:
            print(f"⚠️  WARNING: Follow-through route provided but no text")
        elif follow_through and follow_through_route:
            print(f"✅ SUCCESS: Follow-through logic complete: '{follow_through}' -> {follow_through_route}")
            
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error during structure validation: {e}")
        return False

def test_engine_behavior():
    """Test 4: NOW SIGNAL ENGINE behavior validation"""
    print("\n🧪 TEST 4: NOW SIGNAL ENGINE behavior validation")
    
    try:
        # Test multiple calls to see if engine detects different patterns
        responses = []
        for i in range(2):
            response = requests.get(f"{BACKEND_URL}/today-pattern/{TEST_USER_ID}?force_refresh=true", timeout=30)
            if response.status_code == 200:
                responses.append(response.json())
            time.sleep(1)  # Brief delay between requests
            
        if len(responses) < 2:
            print(f"❌ FAILED: Could not get multiple responses for comparison")
            return False
            
        # Check if responses show signal processing
        for i, data in enumerate(responses):
            print(f"Response {i+1}:")
            print(f"  Title: {data.get('title')}")
            print(f"  Confidence: {data.get('confidence')}")
            print(f"  Sources: {data.get('sources')}")
            
            # Validate no system language or advice
            all_text = data.get("title", "") + " " + " ".join(data.get("lines", []))
            system_words = ["system", "algorithm", "analysis", "should", "must", "need to", "have to"]
            found_system_words = [word for word in system_words if word.lower() in all_text.lower()]
            
            if found_system_words:
                print(f"⚠️  WARNING: Possible system language detected: {found_system_words}")
            else:
                print(f"✅ SUCCESS: No system language detected in response {i+1}")
                
        # Check for tension detection (opposing forces)
        tension_indicators = ["but", "yet", "while", "though", "however", "still", "even as"]
        for i, data in enumerate(responses):
            all_text = " ".join(data.get("lines", [])).lower()
            has_tension = any(indicator in all_text for indicator in tension_indicators)
            if has_tension:
                print(f"✅ SUCCESS: Response {i+1} shows tension detection")
            else:
                print(f"ℹ️  INFO: Response {i+1} may not show explicit tension")
                
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error during engine behavior test: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 STARTING TODAY'S PATTERN v2 API ENDPOINT TESTING")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Basic Endpoint Functionality", test_basic_endpoint),
        ("Force Refresh Test", test_force_refresh),
        ("Response Structure Validation", test_response_structure),
        ("NOW SIGNAL ENGINE Behavior", test_engine_behavior)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        result = test_func()
        test_results.append((test_name, result))
        
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - TODAY'S PATTERN v2 API is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Review the failures above")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)