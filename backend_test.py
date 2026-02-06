#!/usr/bin/env python3
"""
Backend Test Suite for Enneagram Knowledge Base and Enriched Computed Details
Testing the new Enneagram KB functionality and enriched details computation.
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://mirror-daily.preview.emergentagent.com/api"

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_result(success, message, details=None):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {details}")

def test_kb_status():
    """Test 1: KB Status Endpoint"""
    print_test_header("KB Status Endpoint")
    
    try:
        url = f"{BACKEND_URL}/enneagram/kb-status"
        print(f"Testing: GET {url}")
        
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check expected fields
            required_fields = ["status", "ready", "chunks_count", "error", "pdf_path"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_result(False, f"Missing required fields: {missing_fields}")
                return False
            
            # Check if ready is false (expected if PDF missing)
            if data.get("ready") == False:
                print_result(True, "KB Status correctly shows ready: false (PDF missing as expected)")
                return True
            elif data.get("ready") == True:
                print_result(True, f"KB Status shows ready: true with {data.get('chunks_count', 0)} chunks")
                return True
            else:
                print_result(False, f"Unexpected ready status: {data.get('ready')}")
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Request failed: {str(e)}")
        return False

def test_enneagram_ask():
    """Test 2: Enneagram Ask Endpoint (Graceful Degradation)"""
    print_test_header("Enneagram Ask Endpoint (Graceful Degradation)")
    
    try:
        url = f"{BACKEND_URL}/enneagram/ask"
        payload = {
            "question": "What is Type 4?"
        }
        
        print(f"Testing: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for graceful message when KB unavailable
            answer = data.get("answer", "")
            if "unavailable" in answer.lower() or "try again later" in answer.lower():
                print_result(True, "Returns graceful message when KB unavailable")
                return True
            elif len(answer) > 50:  # If KB is available and returns actual content
                print_result(True, "KB is available and returns detailed answer")
                return True
            else:
                print_result(False, f"Unexpected response format or content: {answer}")
                return False
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Request failed: {str(e)}")
        return False

def test_enneagram_results_save():
    """Test 3: Enneagram Results with Enriched Details"""
    print_test_header("Enneagram Results Save with Enriched Details")
    
    try:
        url = f"{BACKEND_URL}/enneagram/results"
        payload = {
            "user_id": "69819f1a1e4549392d7cb6d1",
            "method": "assessment_inference_v1",
            "version": "v1",
            "inferred_core": 7,
            "inferred_wing": 8,
            "confidence": 0.72,
            "confidence_tier": "medium",
            "is_close": False,
            "top_candidates": [{"type": 7, "probability": 0.72}],
            "state_calibration": {
                "energy_state": "high",
                "life_context": "exploring",
                "answer_frame": "best_self"
            },
            "debug_scores": {
                "raw_scores": {"7": 4.5},
                "z_scores": {"7": 1.5},
                "wing_scores": {"left": 3.5, "right": 4.0, "diff": 0.5}
            }
        }
        
        print(f"Testing: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for success
            if not data.get("success"):
                print_result(False, "Response does not indicate success")
                return False
            
            # Check for enneagram_computed_details in result object
            result = data.get("result", {})
            computed_details = result.get("enneagram_computed_details", {})
            if not computed_details:
                print_result(False, "Missing enneagram_computed_details in result")
                return False
            
            # Check required enriched fields for Type 7
            expected_fields = {
                "center": "head",
                "hornevian_group": "assertive", 
                "harmonic_group": "positive_outlook",
                "stress_line_to": 1,
                "growth_line_to": 5
            }
            
            missing_or_wrong = []
            for field, expected_value in expected_fields.items():
                actual_value = computed_details.get(field)
                if actual_value != expected_value:
                    missing_or_wrong.append(f"{field}: expected {expected_value}, got {actual_value}")
            
            if missing_or_wrong:
                print_result(False, f"Incorrect enriched details: {missing_or_wrong}")
                return False
            
            # Check for additional expected fields
            additional_fields = ["social_style_tags", "traits_library_refs"]
            missing_additional = [field for field in additional_fields if field not in computed_details]
            
            if missing_additional:
                print_result(False, f"Missing additional fields: {missing_additional}")
                return False
            
            print_result(True, "Successfully saved results with correct enriched details")
            print(f"Enriched details: {json.dumps(computed_details, indent=2)}")
            return True
            
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Request failed: {str(e)}")
        return False

def test_enneagram_results_get():
    """Test 4: Get Results with Enriched Details"""
    print_test_header("Get Enneagram Results with Enriched Details")
    
    try:
        user_id = "69819f1a1e4549392d7cb6d1"
        url = f"{BACKEND_URL}/enneagram/results/{user_id}"
        
        print(f"Testing: GET {url}")
        
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if has_result is true
            if not data.get("has_result"):
                print_result(False, "No results found for user (has_result: false)")
                return False
            
            # Check for result object
            result = data.get("result", {})
            if not result:
                print_result(False, "Missing result object in response")
                return False
            
            # Check for enneagram_computed_details in result
            computed_details = result.get("enneagram_computed_details", {})
            if not computed_details:
                print_result(False, "Missing enneagram_computed_details in result")
                return False
            
            # Verify the enriched details are present
            required_fields = ["center", "hornevian_group", "harmonic_group", "stress_line_to", "growth_line_to"]
            missing_fields = [field for field in required_fields if field not in computed_details]
            
            if missing_fields:
                print_result(False, f"Missing enriched detail fields: {missing_fields}")
                return False
            
            print_result(True, "Successfully retrieved results with enriched details")
            print(f"Enriched details: {json.dumps(computed_details, indent=2)}")
            return True
            
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Request failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 ENNEAGRAM KNOWLEDGE BASE & ENRICHED DETAILS TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    tests = [
        ("KB Status Endpoint", test_kb_status),
        ("Enneagram Ask Endpoint", test_enneagram_ask),
        ("Enneagram Results Save", test_enneagram_results_save),
        ("Enneagram Results Get", test_enneagram_results_get),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_result(False, f"Test {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())