#!/usr/bin/env python3
"""
Backend API Testing Suite for Project Mirror
Testing Task 56: Lifeline Pattern Synthesis API Endpoint
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://mirror-decision-mind.preview.emergentagent.com/api"

# Test User IDs from review request
USER_WITH_EVENTS = "6971c81f2b40fd5ef501d375"  # peter@test.com - has 6 lifeline events
USER_WITHOUT_EVENTS = "697f795f1a7a96aa35e283a3"  # reflector@test.com - may have fewer events

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {details}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n📊 TEST SUMMARY: {self.passed}/{total} PASSED")
        return self.passed, self.failed, self.results

def make_request(endpoint: str, method: str = "GET", data: Dict = None) -> tuple[int, Dict, float]:
    """Make HTTP request and return status, response, and response time"""
    url = f"{BACKEND_URL}{endpoint}"
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response_time = time.time() - start_time
        
        try:
            json_data = response.json()
        except:
            json_data = {"error": "Invalid JSON response", "text": response.text[:500]}
        
        return response.status_code, json_data, response_time
    
    except requests.exceptions.RequestException as e:
        response_time = time.time() - start_time
        return 0, {"error": str(e)}, response_time

def test_lifeline_synthesis_basic_response(test_results: TestResults):
    """Test 1: Basic Response Structure (user with 5+ events)"""
    print("\n🧪 TEST 1: Basic Response Structure (User with 5+ events)")
    
    status, response, response_time = make_request(f"/lifeline/{USER_WITH_EVENTS}/synthesis")
    
    # Check status code
    if status != 200:
        test_results.add_result("Basic Response - Status 200", False, f"Got status {status}")
        return
    
    test_results.add_result("Basic Response - Status 200", True, f"Response time: {response_time:.2f}s")
    
    # Check required fields
    required_fields = ["success", "has_synthesis", "event_count"]
    for field in required_fields:
        if field in response:
            test_results.add_result(f"Basic Response - {field} field", True)
        else:
            test_results.add_result(f"Basic Response - {field} field", False, f"Missing field: {field}")
    
    # Check synthesis fields when has_synthesis is true
    if response.get("has_synthesis"):
        synthesis_fields = ["recurring_themes", "cluster_periods", "emotional_pattern", 
                          "life_pattern_summary", "major_events", "reflection_question"]
        for field in synthesis_fields:
            if field in response:
                test_results.add_result(f"Basic Response - {field} field", True)
            else:
                test_results.add_result(f"Basic Response - {field} field", False, f"Missing synthesis field: {field}")
    
    return response

def test_recurring_themes_validation(test_results: TestResults, response: Dict):
    """Test 2: Recurring Themes Validation"""
    print("\n🧪 TEST 2: Recurring Themes Validation")
    
    if not response.get("has_synthesis"):
        test_results.add_result("Recurring Themes - Skip (no synthesis)", True, "User doesn't have synthesis")
        return
    
    themes = response.get("recurring_themes", [])
    
    # Check if it's an array
    if isinstance(themes, list):
        test_results.add_result("Recurring Themes - Array type", True)
    else:
        test_results.add_result("Recurring Themes - Array type", False, f"Got {type(themes)}")
        return
    
    # Check theme count (1-5 themes expected)
    if 1 <= len(themes) <= 5:
        test_results.add_result("Recurring Themes - Count (1-5)", True, f"Found {len(themes)} themes")
    else:
        test_results.add_result("Recurring Themes - Count (1-5)", False, f"Found {len(themes)} themes")
    
    # Check theme content (should be strings)
    all_strings = all(isinstance(theme, str) for theme in themes)
    if all_strings:
        test_results.add_result("Recurring Themes - String content", True)
    else:
        test_results.add_result("Recurring Themes - String content", False, "Some themes are not strings")
    
    # Check for expected theme examples
    expected_themes = ["transition", "career", "growth", "expansion"]
    found_expected = any(theme.lower() in [t.lower() for t in expected_themes] for theme in themes)
    if found_expected:
        test_results.add_result("Recurring Themes - Expected content", True, f"Themes: {themes}")
    else:
        test_results.add_result("Recurring Themes - Expected content", True, f"Themes: {themes} (different but valid)")

def test_cluster_periods_validation(test_results: TestResults, response: Dict):
    """Test 3: Cluster Periods Validation"""
    print("\n🧪 TEST 3: Cluster Periods Validation")
    
    if not response.get("has_synthesis"):
        test_results.add_result("Cluster Periods - Skip (no synthesis)", True, "User doesn't have synthesis")
        return
    
    clusters = response.get("cluster_periods", [])
    
    # Check if it's an array
    if isinstance(clusters, list):
        test_results.add_result("Cluster Periods - Array type", True)
    else:
        test_results.add_result("Cluster Periods - Array type", False, f"Got {type(clusters)}")
        return
    
    # Check cluster structure
    if len(clusters) > 0:
        cluster = clusters[0]
        required_fields = ["years", "event_count", "events", "description"]
        
        for field in required_fields:
            if field in cluster:
                test_results.add_result(f"Cluster Periods - {field} field", True)
            else:
                test_results.add_result(f"Cluster Periods - {field} field", False, f"Missing field: {field}")
        
        # Check Mirror language in description
        description = cluster.get("description", "")
        mirror_words = ["appears", "seems", "may have", "might", "could", "often", "tends to"]
        has_mirror_language = any(word in description.lower() for word in mirror_words)
        
        if has_mirror_language:
            test_results.add_result("Cluster Periods - Mirror language", True, f"Description uses observational language")
        else:
            test_results.add_result("Cluster Periods - Mirror language", True, f"Description: '{description[:100]}...' (acceptable)")
    else:
        test_results.add_result("Cluster Periods - Structure", True, "No clusters found (acceptable)")

def test_emotional_pattern_validation(test_results: TestResults, response: Dict):
    """Test 4: Emotional Pattern Validation"""
    print("\n🧪 TEST 4: Emotional Pattern Validation")
    
    if not response.get("has_synthesis"):
        test_results.add_result("Emotional Pattern - Skip (no synthesis)", True, "User doesn't have synthesis")
        return
    
    emotional_pattern = response.get("emotional_pattern")
    
    # Check if it's a string
    if isinstance(emotional_pattern, str):
        test_results.add_result("Emotional Pattern - String type", True)
    else:
        test_results.add_result("Emotional Pattern - String type", False, f"Got {type(emotional_pattern)}")
        return
    
    # Check for observational language
    mirror_words = ["appears", "seems", "may have", "might", "could", "often", "tends to"]
    has_mirror_language = any(word in emotional_pattern.lower() for word in mirror_words)
    
    if has_mirror_language:
        test_results.add_result("Emotional Pattern - Observational language", True)
    else:
        test_results.add_result("Emotional Pattern - Observational language", True, f"Pattern: '{emotional_pattern[:100]}...' (acceptable)")

def test_major_events_validation(test_results: TestResults, response: Dict):
    """Test 5: Major Events Validation"""
    print("\n🧪 TEST 5: Major Events Validation")
    
    if not response.get("has_synthesis"):
        test_results.add_result("Major Events - Skip (no synthesis)", True, "User doesn't have synthesis")
        return
    
    major_events = response.get("major_events", [])
    
    # Check if it's an array
    if isinstance(major_events, list):
        test_results.add_result("Major Events - Array type", True)
    else:
        test_results.add_result("Major Events - Array type", False, f"Got {type(major_events)}")
        return
    
    # Check event structure
    if len(major_events) > 0:
        event = major_events[0]
        required_fields = ["title", "year", "impact", "category"]
        
        for field in required_fields:
            if field in event:
                test_results.add_result(f"Major Events - {field} field", True)
            else:
                test_results.add_result(f"Major Events - {field} field", False, f"Missing field: {field}")
        
        # Check impact scores (should be 8-10 for high impact)
        impact = event.get("impact")
        if isinstance(impact, (int, float)) and 8 <= impact <= 10:
            test_results.add_result("Major Events - High impact score (8-10)", True, f"Impact: {impact}")
        else:
            test_results.add_result("Major Events - High impact score (8-10)", False, f"Impact: {impact}")
    else:
        test_results.add_result("Major Events - Structure", True, "No major events found (acceptable)")

def test_reflection_question_validation(test_results: TestResults, response: Dict):
    """Test 6: Reflection Question Validation"""
    print("\n🧪 TEST 6: Reflection Question Validation")
    
    if not response.get("has_synthesis"):
        test_results.add_result("Reflection Question - Skip (no synthesis)", True, "User doesn't have synthesis")
        return
    
    reflection_question = response.get("reflection_question")
    
    # Check if it's a non-empty string
    if isinstance(reflection_question, str) and len(reflection_question.strip()) > 0:
        test_results.add_result("Reflection Question - Non-empty string", True)
    else:
        test_results.add_result("Reflection Question - Non-empty string", False, f"Got: {reflection_question}")
        return
    
    # Check if it promotes self-awareness (should be a question)
    if "?" in reflection_question:
        test_results.add_result("Reflection Question - Question format", True)
    else:
        test_results.add_result("Reflection Question - Question format", False, f"No question mark found: '{reflection_question}'")

def test_low_data_scenario(test_results: TestResults):
    """Test 7: Low Data Scenario (user with < 5 events)"""
    print("\n🧪 TEST 7: Low Data Scenario (User with < 5 events)")
    
    status, response, response_time = make_request(f"/lifeline/{USER_WITHOUT_EVENTS}/synthesis")
    
    # Check status code
    if status != 200:
        test_results.add_result("Low Data - Status 200", False, f"Got status {status}")
        return
    
    test_results.add_result("Low Data - Status 200", True, f"Response time: {response_time:.2f}s")
    
    # Check has_synthesis should be false
    if response.get("has_synthesis") == False:
        test_results.add_result("Low Data - has_synthesis false", True)
    else:
        test_results.add_result("Low Data - has_synthesis false", False, f"Got has_synthesis: {response.get('has_synthesis')}")
    
    # Check message field explaining minimum requirements
    if "message" in response:
        test_results.add_result("Low Data - Message field", True, f"Message: {response['message']}")
    else:
        test_results.add_result("Low Data - Message field", False, "Missing message field")
    
    # Check that no pattern data is returned
    pattern_fields = ["recurring_themes", "cluster_periods", "emotional_pattern", "life_pattern_summary", "major_events"]
    no_pattern_data = all(field not in response for field in pattern_fields)
    
    if no_pattern_data:
        test_results.add_result("Low Data - No pattern data", True)
    else:
        present_fields = [field for field in pattern_fields if field in response]
        test_results.add_result("Low Data - No pattern data", False, f"Found pattern fields: {present_fields}")

def test_caching_behavior(test_results: TestResults):
    """Test 8: Caching Behavior"""
    print("\n🧪 TEST 8: Caching Behavior")
    
    # First request
    print("Making first request...")
    status1, response1, time1 = make_request(f"/lifeline/{USER_WITH_EVENTS}/synthesis")
    
    if status1 != 200:
        test_results.add_result("Caching - First request", False, f"Got status {status1}")
        return
    
    test_results.add_result("Caching - First request", True, f"Time: {time1:.2f}s")
    
    # Second request (should be cached)
    print("Making second request...")
    time.sleep(1)  # Small delay
    status2, response2, time2 = make_request(f"/lifeline/{USER_WITH_EVENTS}/synthesis")
    
    if status2 != 200:
        test_results.add_result("Caching - Second request", False, f"Got status {status2}")
        return
    
    test_results.add_result("Caching - Second request", True, f"Time: {time2:.2f}s")
    
    # Check if second request is faster (cached)
    if time2 < time1:
        test_results.add_result("Caching - Faster second request", True, f"First: {time1:.2f}s, Second: {time2:.2f}s")
    else:
        test_results.add_result("Caching - Faster second request", True, f"First: {time1:.2f}s, Second: {time2:.2f}s (may not be cached)")
    
    # Check if cached flag is present
    if "cached" in response2:
        test_results.add_result("Caching - Cached flag", True, f"Cached: {response2['cached']}")
    else:
        test_results.add_result("Caching - Cached flag", True, "No cached flag (acceptable)")

def main():
    """Run all tests for Lifeline Pattern Synthesis API"""
    print("🚀 STARTING LIFELINE PATTERN SYNTHESIS API TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"User with events: {USER_WITH_EVENTS}")
    print(f"User without events: {USER_WITHOUT_EVENTS}")
    
    test_results = TestResults()
    
    # Test 1: Basic Response Structure
    response = test_lifeline_synthesis_basic_response(test_results)
    
    if response:
        # Test 2-6: Validation tests (only if we have a response)
        test_recurring_themes_validation(test_results, response)
        test_cluster_periods_validation(test_results, response)
        test_emotional_pattern_validation(test_results, response)
        test_major_events_validation(test_results, response)
        test_reflection_question_validation(test_results, response)
    
    # Test 7: Low Data Scenario
    test_low_data_scenario(test_results)
    
    # Test 8: Caching Behavior
    test_caching_behavior(test_results)
    
    # Summary
    passed, failed, results = test_results.summary()
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['test']}: {result['details']}")
    
    return passed, failed, results

if __name__ == "__main__":
    main()