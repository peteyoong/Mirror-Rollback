#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror - Enneagram Assessment Flow
Testing the complete Enneagram results endpoint functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://mirror-daily.preview.emergentagent.com/api"
TEST_USER_ID = "69819f1a1e4549392d7cb6d1"

def log_test(test_name, status, details=""):
    """Log test results with consistent formatting"""
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_symbol} {test_name}: {status}")
    if details:
        print(f"   {details}")
    print()

def test_enneagram_results_save():
    """Test 1: Verify Enneagram results endpoint - POST /api/enneagram/results"""
    print("🔧 TEST 1: POST /api/enneagram/results - Save Enneagram Results")
    
    # Test payload as specified in the review request
    payload = {
        "user_id": TEST_USER_ID,
        "method": "assessment_inference_v1",
        "version": "v1",
        "inferred_core": 4,
        "inferred_wing": 5,
        "confidence": 0.68,
        "confidence_tier": "medium",
        "is_close": True,
        "top_candidates": [
            {"type": 4, "probability": 0.68},
            {"type": 5, "probability": 0.62}
        ],
        "state_calibration": {
            "energy_state": "neutral",
            "life_context": "managing",
            "answer_frame": "recent_self"
        },
        "debug_scores": {
            "raw_scores": {"1": 3.0, "2": 3.5, "3": 3.2, "4": 4.5, "5": 4.3, "6": 3.1, "7": 3.0, "8": 2.8, "9": 3.6},
            "z_scores": {"1": -0.5, "2": 0.2, "3": 0.0, "4": 1.5, "5": 1.3, "6": -0.3, "7": -0.5, "8": -0.8, "9": 0.5},
            "wing_scores": {"left": 3.2, "right": 4.0, "diff": 0.8}
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/enneagram/results",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("result"):
                result = data["result"]
                if (result.get("inferred_core") == 4 and 
                    result.get("inferred_wing") == 5 and 
                    result.get("confidence_tier") == "medium"):
                    log_test("Enneagram Results Save", "PASS", 
                           f"Successfully saved: Type {result['inferred_core']}w{result['inferred_wing']}, {result['confidence_tier']} confidence")
                    return True
                else:
                    log_test("Enneagram Results Save", "FAIL", 
                           f"Response data mismatch: {result}")
                    return False
            else:
                log_test("Enneagram Results Save", "FAIL", 
                       f"Invalid response structure: {data}")
                return False
        else:
            log_test("Enneagram Results Save", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_test("Enneagram Results Save", "FAIL", f"Request error: {e}")
        return False
    except Exception as e:
        log_test("Enneagram Results Save", "FAIL", f"Unexpected error: {e}")
        return False

def test_enneagram_results_retrieve():
    """Test 2: Verify Enneagram results retrieval - GET /api/enneagram/results/{user_id}"""
    print("🔧 TEST 2: GET /api/enneagram/results/{user_id} - Retrieve Enneagram Results")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/enneagram/results/{TEST_USER_ID}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("has_result") and data.get("result"):
                result = data["result"]
                # Verify the data matches what we saved in test 1
                if (result.get("inferred_core") == 4 and 
                    result.get("inferred_wing") == 5 and 
                    result.get("confidence_tier") == "medium" and
                    result.get("user_id") == TEST_USER_ID):
                    
                    # Check for required fields
                    required_fields = ["id", "method", "version", "confidence", "is_close", 
                                     "top_candidates", "state_calibration", "debug_scores", "created_at"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        log_test("Enneagram Results Retrieve", "PASS", 
                               f"Successfully retrieved: Type {result['inferred_core']}w{result['inferred_wing']}, all fields present")
                        return True
                    else:
                        log_test("Enneagram Results Retrieve", "FAIL", 
                               f"Missing required fields: {missing_fields}")
                        return False
                else:
                    log_test("Enneagram Results Retrieve", "FAIL", 
                           f"Data mismatch or missing core fields: {result}")
                    return False
            elif not data.get("has_result"):
                log_test("Enneagram Results Retrieve", "FAIL", 
                       "No result found - may indicate save test failed")
                return False
            else:
                log_test("Enneagram Results Retrieve", "FAIL", 
                       f"Invalid response structure: {data}")
                return False
        else:
            log_test("Enneagram Results Retrieve", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_test("Enneagram Results Retrieve", "FAIL", f"Request error: {e}")
        return False
    except Exception as e:
        log_test("Enneagram Results Retrieve", "FAIL", f"Unexpected error: {e}")
        return False

def test_large_payload_handling():
    """Test 3: Verify large payload handling (simulating many answers)"""
    print("🔧 TEST 3: Large Payload Handling - Confirm no payload size issues")
    
    # Create a large debug_scores object to test payload limits
    large_raw_scores = {}
    large_z_scores = {}
    
    # Generate 100 fake score entries to simulate a large assessment
    for i in range(1, 101):
        large_raw_scores[str(i)] = round(2.0 + (i % 5) * 0.5, 2)
        large_z_scores[str(i)] = round(-2.0 + (i % 5) * 1.0, 2)
    
    large_payload = {
        "user_id": TEST_USER_ID,
        "method": "assessment_inference_v1_large",
        "version": "v1",
        "inferred_core": 7,
        "inferred_wing": 8,
        "confidence": 0.75,
        "confidence_tier": "high",
        "is_close": False,
        "top_candidates": [
            {"type": 7, "probability": 0.75},
            {"type": 8, "probability": 0.65},
            {"type": 6, "probability": 0.55}
        ],
        "state_calibration": {
            "energy_state": "high",
            "life_context": "expanding",
            "answer_frame": "best_self"
        },
        "debug_scores": {
            "raw_scores": large_raw_scores,
            "z_scores": large_z_scores,
            "wing_scores": {"left": 4.2, "right": 4.8, "diff": 0.6}
        }
    }
    
    try:
        # Calculate payload size
        payload_size = len(json.dumps(large_payload))
        print(f"   📊 Payload size: {payload_size:,} bytes ({payload_size/1024:.1f} KB)")
        
        response = requests.post(
            f"{BACKEND_URL}/enneagram/results",
            json=large_payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for large payload
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("result"):
                result = data["result"]
                if (result.get("inferred_core") == 7 and 
                    result.get("inferred_wing") == 8 and 
                    result.get("confidence_tier") == "high"):
                    log_test("Large Payload Handling", "PASS", 
                           f"Successfully processed {payload_size:,} byte payload")
                    return True
                else:
                    log_test("Large Payload Handling", "FAIL", 
                           f"Response data mismatch: {result}")
                    return False
            else:
                log_test("Large Payload Handling", "FAIL", 
                       f"Invalid response structure: {data}")
                return False
        elif response.status_code == 413:
            log_test("Large Payload Handling", "FAIL", 
                   f"Payload too large (413): Server cannot handle {payload_size:,} bytes")
            return False
        else:
            log_test("Large Payload Handling", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_test("Large Payload Handling", "FAIL", f"Request error: {e}")
        return False
    except Exception as e:
        log_test("Large Payload Handling", "FAIL", f"Unexpected error: {e}")
        return False

def main():
    """Run all Enneagram endpoint tests"""
    print("🧪 ENNEAGRAM ASSESSMENT COMPLETE FLOW TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    
    # Run all tests
    test_results = []
    
    # Test 1: Save Enneagram results
    test_results.append(test_enneagram_results_save())
    
    # Test 2: Retrieve Enneagram results
    test_results.append(test_enneagram_results_retrieve())
    
    # Test 3: Large payload handling
    test_results.append(test_large_payload_handling())
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Enneagram Assessment Flow is working correctly!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review the failures above")
        return 1

if __name__ == "__main__":
    sys.exit(main())