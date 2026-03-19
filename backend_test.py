#!/usr/bin/env python3
"""
Backend API Testing Script for Project Mirror
Testing the Astrology Keystone Explanation integration as specified in review request.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Backend URL from frontend environment
BACKEND_URL = "https://insight-lens-7.preview.emergentagent.com/api"

# Test user IDs from review request
TEST_USER_ID_1 = "6971c81f2b40fd5ef501d375"
TEST_USER_ID_2 = "69819f1a1e4549392d7cb6d1"

class AstrologyKeystoneExplanationTester:
    """Test suite for Astrology Keystone Explanation integration"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        
        print(result)
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_keystone_pattern_exists(self, user_id: str, test_name: str) -> Dict[str, Any]:
        """Test that keystone pattern exists for user"""
        try:
            url = f"{BACKEND_URL}/keystone-pattern/{user_id}"
            start_time = time.time()
            
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time
            
            # Test HTTP status
            if response.status_code != 200:
                self.log_test(f"{test_name} - Keystone HTTP Status", False, f"Got {response.status_code}, expected 200")
                return {}
            
            self.log_test(f"{test_name} - Keystone HTTP Status", True, f"200 OK ({response_time:.2f}s)")
            
            # Test JSON parsing
            try:
                data = response.json()
                self.log_test(f"{test_name} - Keystone JSON Parse", True, "Valid JSON response")
            except json.JSONDecodeError as e:
                self.log_test(f"{test_name} - Keystone JSON Parse", False, f"Invalid JSON: {e}")
                return {}
            
            # Test required fields for keystone
            required_fields = ["pattern_id", "pattern_label", "behavior_sequence"]
            
            for field in required_fields:
                if field in data:
                    self.log_test(f"{test_name} - Keystone Field '{field}'", True, f"Present: {data[field]}")
                else:
                    self.log_test(f"{test_name} - Keystone Field '{field}'", False, "Missing required field")
                    
            return data
            
        except requests.exceptions.RequestException as e:
            self.log_test(f"{test_name} - Keystone HTTP Request", False, f"Request failed: {e}")
            return {}
        except Exception as e:
            self.log_test(f"{test_name} - Keystone Unexpected Error", False, f"Error: {e}")
            return {}
    
    def test_astrology_keystone_explanation(self, user_id: str, test_name: str, expected_pattern_id: str = None) -> Dict[str, Any]:
        """Test astrology deep-dive endpoint includes keystone_explanation"""
        try:
            url = f"{BACKEND_URL}/astrology/deep-dive/{user_id}?force_refresh=true"
            start_time = time.time()
            
            response = requests.get(url, timeout=60)  # Longer timeout for deep-dive
            response_time = time.time() - start_time
            
            # Test HTTP status
            if response.status_code != 200:
                self.log_test(f"{test_name} - Astrology HTTP Status", False, f"Got {response.status_code}, expected 200")
                return {}
            
            self.log_test(f"{test_name} - Astrology HTTP Status", True, f"200 OK ({response_time:.2f}s)")
            
            # Test JSON parsing
            try:
                data = response.json()
                self.log_test(f"{test_name} - Astrology JSON Parse", True, "Valid JSON response")
            except json.JSONDecodeError as e:
                self.log_test(f"{test_name} - Astrology JSON Parse", False, f"Invalid JSON: {e}")
                return {}
            
            # Test keystone_explanation field exists
            if "keystone_explanation" in data:
                self.log_test(f"{test_name} - keystone_explanation Field", True, "Present in response")
                keystone_exp = data["keystone_explanation"]
            else:
                self.log_test(f"{test_name} - keystone_explanation Field", False, "Missing from response")
                return data
            
            # Test keystone_explanation required fields
            required_keystone_fields = [
                "keystone_pattern_id",
                "lens_role", 
                "lens_explanation_title",
                "lens_explanation_body",
                "supports_keystone"
            ]
            
            for field in required_keystone_fields:
                if field in keystone_exp:
                    value = keystone_exp[field]
                    if field == "lens_role":
                        if value == "timing_trigger":
                            self.log_test(f"{test_name} - {field}", True, f"Correct: {value}")
                        else:
                            self.log_test(f"{test_name} - {field}", False, f"Expected 'timing_trigger', got: {value}")
                    elif field == "supports_keystone":
                        if value is True:
                            self.log_test(f"{test_name} - {field}", True, f"Correct: {value}")
                        else:
                            self.log_test(f"{test_name} - {field}", False, f"Expected true, got: {value}")
                    elif field in ["lens_explanation_title", "lens_explanation_body"]:
                        if isinstance(value, str) and len(value.strip()) > 0:
                            self.log_test(f"{test_name} - {field}", True, f"Non-empty string ({len(value)} chars)")
                        else:
                            self.log_test(f"{test_name} - {field}", False, f"Empty or invalid: {value}")
                    else:
                        self.log_test(f"{test_name} - {field}", True, f"Present: {value}")
                else:
                    self.log_test(f"{test_name} - {field}", False, "Missing required field")
            
            # Test pattern ID match if provided
            if expected_pattern_id and "keystone_pattern_id" in keystone_exp:
                actual_pattern_id = keystone_exp["keystone_pattern_id"]
                if actual_pattern_id == expected_pattern_id:
                    self.log_test(f"{test_name} - Pattern ID Match", True, f"Matches: {actual_pattern_id}")
                else:
                    self.log_test(f"{test_name} - Pattern ID Match", False, f"Expected: {expected_pattern_id}, got: {actual_pattern_id}")
                    
            return data
            
        except requests.exceptions.RequestException as e:
            self.log_test(f"{test_name} - Astrology HTTP Request", False, f"Request failed: {e}")
            return {}
        except Exception as e:
            self.log_test(f"{test_name} - Astrology Unexpected Error", False, f"Error: {e}")
            return {}
    
    def run_all_tests(self):
        """Run all test scenarios from review request"""
        print("🧪 ASTROLOGY KEYSTONE EXPLANATION INTEGRATION TESTING")
        print("=" * 70)
        
        # Test 1: Verify keystone exists for user 1
        print(f"\n--- Test 1: Keystone Pattern for User {TEST_USER_ID_1} ---")
        keystone_data_1 = self.test_keystone_pattern_exists(TEST_USER_ID_1, "User 1")
        pattern_id_1 = keystone_data_1.get("pattern_id") if keystone_data_1 else None
        
        # Test 2: Test keystone explanation for user 1
        print(f"\n--- Test 2: Astrology Keystone Explanation for User {TEST_USER_ID_1} ---")
        astrology_data_1 = self.test_astrology_keystone_explanation(TEST_USER_ID_1, "User 1", pattern_id_1)
        
        # Test 3: Verify keystone exists for user 2
        print(f"\n--- Test 3: Keystone Pattern for User {TEST_USER_ID_2} ---")
        keystone_data_2 = self.test_keystone_pattern_exists(TEST_USER_ID_2, "User 2")
        pattern_id_2 = keystone_data_2.get("pattern_id") if keystone_data_2 else None
        
        # Test 4: Test keystone explanation for user 2
        print(f"\n--- Test 4: Astrology Keystone Explanation for User {TEST_USER_ID_2} ---")
        astrology_data_2 = self.test_astrology_keystone_explanation(TEST_USER_ID_2, "User 2", pattern_id_2)
        
        # Summary
        print("\n" + "=" * 70)
        print("🧪 ASTROLOGY KEYSTONE EXPLANATION TEST SUMMARY")
        print("=" * 70)
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests / self.total_tests * 100):.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test["passed"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        # Show sample keystone explanation if available
        if astrology_data_1 and "keystone_explanation" in astrology_data_1:
            keystone_exp = astrology_data_1["keystone_explanation"]
            print(f"\n📊 SAMPLE KEYSTONE EXPLANATION (User 1):")
            print(f"  Pattern ID: {keystone_exp.get('keystone_pattern_id', 'N/A')}")
            print(f"  Lens Role: {keystone_exp.get('lens_role', 'N/A')}")
            print(f"  Title: {keystone_exp.get('lens_explanation_title', 'N/A')}")
            print(f"  Body: {keystone_exp.get('lens_explanation_body', 'N/A')[:100]}...")
            print(f"  Supports Keystone: {keystone_exp.get('supports_keystone', 'N/A')}")
        
        # Show pattern matching summary
        print(f"\n📊 PATTERN MATCHING VERIFICATION:")
        if pattern_id_1:
            print(f"  User 1 Keystone Pattern: {pattern_id_1}")
            if astrology_data_1 and "keystone_explanation" in astrology_data_1:
                astro_pattern_1 = astrology_data_1["keystone_explanation"].get("keystone_pattern_id", "N/A")
                match_1 = "✅ MATCH" if astro_pattern_1 == pattern_id_1 else "❌ MISMATCH"
                print(f"  User 1 Astrology Pattern: {astro_pattern_1} {match_1}")
        
        if pattern_id_2:
            print(f"  User 2 Keystone Pattern: {pattern_id_2}")
            if astrology_data_2 and "keystone_explanation" in astrology_data_2:
                astro_pattern_2 = astrology_data_2["keystone_explanation"].get("keystone_pattern_id", "N/A")
                match_2 = "✅ MATCH" if astro_pattern_2 == pattern_id_2 else "❌ MISMATCH"
                print(f"  User 2 Astrology Pattern: {astro_pattern_2} {match_2}")
        
        return self.passed_tests == self.total_tests


if __name__ == "__main__":
    tester = AstrologyKeystoneExplanationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n🚨 SOME TESTS FAILED!")
        sys.exit(1)