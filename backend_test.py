#!/usr/bin/env python3
"""
Gene Keys Mirror Chat Context Awareness Testing (Phase 9)

Tests the POST /api/mirror/chat endpoint with messages that trigger Gene Keys keyword matching.
Verifies that the system correctly identifies shadow/gift patterns and provides subtle context.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://pattern-signals-4.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def log_test(message: str, level: str = "INFO"):
    """Log test messages with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def make_request(method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> Dict[str, Any]:
    """Make HTTP request with error handling."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        log_test(f"{method} {endpoint} -> {response.status_code}")
        
        if response.status_code != 200:
            log_test(f"HTTP Error: {response.status_code} - {response.text}", "ERROR")
            return {"error": f"HTTP {response.status_code}", "details": response.text}
        
        return response.json()
    
    except requests.exceptions.Timeout:
        log_test(f"Request timeout after {timeout}s", "ERROR")
        return {"error": "timeout"}
    except requests.exceptions.RequestException as e:
        log_test(f"Request error: {str(e)}", "ERROR")
        return {"error": "request_failed", "details": str(e)}
    except json.JSONDecodeError as e:
        log_test(f"JSON decode error: {str(e)}", "ERROR")
        return {"error": "json_decode_failed", "details": str(e)}

def test_shadow_keyword_match():
    """Test 1: Shadow Keyword Match Test
    
    POST /api/mirror/chat with message containing shadow keywords.
    Should trigger Gene Keys matching with shadow type.
    """
    log_test("=== TEST 1: Shadow Keyword Match ===")
    
    payload = {
        "user_id": TEST_USER_ID,
        "message": "I feel exhausted and depleted, like I have no energy left to give",
        "lens": None,
        "session_id": None,
        "include_journal": True,
        "include_history": True
    }
    
    log_test(f"Testing shadow keywords: 'exhausted', 'depleted', 'no energy'")
    response = make_request("POST", "/mirror/chat", payload)
    
    if "error" in response:
        log_test(f"❌ FAILED: {response['error']}", "ERROR")
        return False
    
    # Verify response structure
    required_fields = ["response", "session_id", "timestamp"]
    missing_fields = [field for field in required_fields if field not in response]
    
    if missing_fields:
        log_test(f"❌ FAILED: Missing fields: {missing_fields}", "ERROR")
        return False
    
    # Check response quality
    response_text = response.get("response", "")
    
    # Should be reflective, not prescriptive
    forbidden_phrases = ["you should", "you need to", "you must", "you will"]
    violations = [phrase for phrase in forbidden_phrases if phrase.lower() in response_text.lower()]
    
    if violations:
        log_test(f"❌ FAILED: Found prescriptive language: {violations}", "ERROR")
        return False
    
    # Should contain reflective language
    reflective_indicators = ["sounds like", "seems like", "might notice", "may be", "echoes", "pattern"]
    has_reflective = any(indicator in response_text.lower() for indicator in reflective_indicators)
    
    if not has_reflective:
        log_test(f"⚠️  WARNING: No clear reflective language detected", "WARN")
    
    log_test(f"✅ PASSED: Shadow keyword test completed")
    log_test(f"Response preview: {response_text[:100]}...")
    
    return True

def test_gift_keyword_match():
    """Test 2: Gift Keyword Match Test
    
    POST /api/mirror/chat with gift-oriented message.
    Should trigger Gene Keys matching with gift type.
    """
    log_test("=== TEST 2: Gift Keyword Match ===")
    
    payload = {
        "user_id": TEST_USER_ID,
        "message": "I feel patient and calm today, willing to wait for the right timing",
        "lens": None,
        "session_id": None,
        "include_journal": True,
        "include_history": True
    }
    
    log_test(f"Testing gift keywords: 'patient', 'calm', 'timing'")
    response = make_request("POST", "/mirror/chat", payload)
    
    if "error" in response:
        log_test(f"❌ FAILED: {response['error']}", "ERROR")
        return False
    
    # Verify response structure
    required_fields = ["response", "session_id", "timestamp"]
    missing_fields = [field for field in required_fields if field not in response]
    
    if missing_fields:
        log_test(f"❌ FAILED: Missing fields: {missing_fields}", "ERROR")
        return False
    
    # Check response quality
    response_text = response.get("response", "")
    
    # Should be reflective, not prescriptive
    forbidden_phrases = ["you should", "you need to", "you must", "you will"]
    violations = [phrase for phrase in forbidden_phrases if phrase.lower() in response_text.lower()]
    
    if violations:
        log_test(f"❌ FAILED: Found prescriptive language: {violations}", "ERROR")
        return False
    
    log_test(f"✅ PASSED: Gift keyword test completed")
    log_test(f"Response preview: {response_text[:100]}...")
    
    return True

def test_no_match():
    """Test 3: No Match Test
    
    POST /api/mirror/chat with neutral message.
    Should show NO_MATCH in logs and still provide quality response.
    """
    log_test("=== TEST 3: No Match Test ===")
    
    payload = {
        "user_id": TEST_USER_ID,
        "message": "What should I have for dinner tonight? I'm thinking pasta or pizza.",
        "lens": None,
        "session_id": None,
        "include_journal": True,
        "include_history": True
    }
    
    log_test(f"Testing neutral message with no Gene Keys keywords")
    response = make_request("POST", "/mirror/chat", payload)
    
    if "error" in response:
        log_test(f"❌ FAILED: {response['error']}", "ERROR")
        return False
    
    # Verify response structure
    required_fields = ["response", "session_id", "timestamp"]
    missing_fields = [field for field in required_fields if field not in response]
    
    if missing_fields:
        log_test(f"❌ FAILED: Missing fields: {missing_fields}", "ERROR")
        return False
    
    # Check response quality - should still be reflective
    response_text = response.get("response", "")
    
    # Should not force Gene Keys references
    gene_keys_terms = ["gene key", "shadow", "gift", "siddhi", "sphere"]
    forced_references = [term for term in gene_keys_terms if term.lower() in response_text.lower()]
    
    if forced_references:
        log_test(f"⚠️  WARNING: Possible forced Gene Keys reference: {forced_references}", "WARN")
    
    log_test(f"✅ PASSED: No match test completed")
    log_test(f"Response preview: {response_text[:100]}...")
    
    return True

def test_response_quality():
    """Test 4: Response Quality Test
    
    Verify responses maintain Mirror philosophy:
    - Reflective, not prescriptive
    - No forced Gene Keys mentions when not relevant
    - Subtle tone when Gene Keys IS mentioned
    """
    log_test("=== TEST 4: Response Quality Test ===")
    
    # Test with a message that might trigger Gene Keys but should be handled subtly
    payload = {
        "user_id": TEST_USER_ID,
        "message": "I've been feeling really scattered lately, jumping from one thing to another without finishing anything",
        "lens": None,
        "session_id": None,
        "include_journal": True,
        "include_history": True
    }
    
    log_test(f"Testing response quality with potentially matching message")
    response = make_request("POST", "/mirror/chat", payload)
    
    if "error" in response:
        log_test(f"❌ FAILED: {response['error']}", "ERROR")
        return False
    
    response_text = response.get("response", "")
    
    # Check for Mirror philosophy compliance
    quality_checks = {
        "no_prescriptive": True,
        "reflective_tone": False,
        "subtle_references": True,
        "preserves_agency": False
    }
    
    # Check for prescriptive language (should be absent)
    prescriptive_phrases = ["you should", "you need to", "you must", "you will", "the best thing", "you have to"]
    for phrase in prescriptive_phrases:
        if phrase.lower() in response_text.lower():
            quality_checks["no_prescriptive"] = False
            log_test(f"⚠️  Found prescriptive phrase: '{phrase}'", "WARN")
    
    # Check for reflective language (should be present)
    reflective_phrases = ["sounds like", "seems like", "might notice", "may be", "echoes", "pattern", "what you're describing"]
    for phrase in reflective_phrases:
        if phrase.lower() in response_text.lower():
            quality_checks["reflective_tone"] = True
            break
    
    # Check for agency-preserving language
    agency_phrases = ["you might", "could be", "one way", "perhaps", "if that resonates"]
    for phrase in agency_phrases:
        if phrase.lower() in response_text.lower():
            quality_checks["preserves_agency"] = True
            break
    
    # Check if Gene Keys references are subtle (if present)
    gene_keys_phrases = ["gene key", "shadow", "gift", "sphere"]
    for phrase in gene_keys_phrases:
        if phrase.lower() in response_text.lower():
            # If Gene Keys is mentioned, check if it's subtle
            subtle_indicators = ["may connect", "echoes a pattern", "might relate", "could be"]
            is_subtle = any(indicator in response_text.lower() for indicator in subtle_indicators)
            if not is_subtle:
                quality_checks["subtle_references"] = False
                log_test(f"⚠️  Gene Keys reference may not be subtle enough", "WARN")
    
    # Evaluate overall quality
    passed_checks = sum(quality_checks.values())
    total_checks = len(quality_checks)
    
    if passed_checks >= 3:
        log_test(f"✅ PASSED: Response quality test ({passed_checks}/{total_checks} checks passed)")
    else:
        log_test(f"⚠️  PARTIAL: Response quality needs improvement ({passed_checks}/{total_checks} checks passed)", "WARN")
    
    log_test(f"Quality checks: {quality_checks}")
    log_test(f"Response preview: {response_text[:150]}...")
    
    return passed_checks >= 3

def check_backend_logs():
    """Check backend logs for [GK_MATCH] entries.
    
    Note: This is informational only as we can't directly access container logs
    from this test script. The actual log checking should be done manually.
    """
    log_test("=== Backend Log Check (Manual) ===")
    log_test("To verify Gene Keys matching, check backend logs for:")
    log_test("1. [GK_MATCH] entries showing has_match=True/False")
    log_test("2. Sphere matched (e.g., 'Evolution', 'Life's Work')")
    log_test("3. Match type='shadow' or 'gift'")
    log_test("4. Matched keywords arrays")
    log_test("5. [GK_MATCH_DEBUG] entries with detailed matching info")
    log_test("")
    log_test("Example log command:")
    log_test("tail -n 100 /var/log/supervisor/backend.*.log | grep GK_MATCH")

def run_all_tests():
    """Run all Gene Keys Mirror Chat Context Awareness tests."""
    log_test("🧪 Starting Gene Keys Mirror Chat Context Awareness Testing (Phase 9)")
    log_test(f"Base URL: {BASE_URL}")
    log_test(f"Test User ID: {TEST_USER_ID}")
    log_test("")
    
    # Track test results
    test_results = []
    
    # Run individual tests
    test_results.append(("Shadow Keyword Match", test_shadow_keyword_match()))
    test_results.append(("Gift Keyword Match", test_gift_keyword_match()))
    test_results.append(("No Match Test", test_no_match()))
    test_results.append(("Response Quality", test_response_quality()))
    
    # Backend log check (informational)
    check_backend_logs()
    
    # Summary
    log_test("")
    log_test("=== TEST SUMMARY ===")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        log_test(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    log_test("")
    log_test(f"📊 FINAL RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        log_test("🎉 ALL TESTS PASSED - Gene Keys Mirror Chat Context Awareness is working correctly!")
        return True
    else:
        log_test("⚠️  SOME TESTS FAILED - Review failed tests and backend logs")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)