#!/usr/bin/env python3
"""
Backend API Testing Script for Project Mirror
Testing the Keystone Pattern API endpoint as specified in review request.
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

class KeystonePatternTester:
    """Test suite for Keystone Pattern API endpoint"""
    
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
    
    def test_keystone_pattern_response_structure(self, user_id: str, test_name: str) -> Dict[str, Any]:
        """Test basic response structure for keystone pattern endpoint"""
        try:
            url = f"{BACKEND_URL}/keystone-pattern/{user_id}"
            start_time = time.time()
            
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time
            
            # Test HTTP status
            if response.status_code != 200:
                self.log_test(f"{test_name} - HTTP Status", False, f"Got {response.status_code}, expected 200")
                return {}
            
            self.log_test(f"{test_name} - HTTP Status", True, f"200 OK ({response_time:.2f}s)")
            
            # Test JSON parsing
            try:
                data = response.json()
                self.log_test(f"{test_name} - JSON Parse", True, "Valid JSON response")
            except json.JSONDecodeError as e:
                self.log_test(f"{test_name} - JSON Parse", False, f"Invalid JSON: {e}")
                return {}
            
            # Test required fields
            required_fields = [
                "pattern_id", "pattern_label", "behavior_sequence", 
                "confidence", "sources", "date", "cached"
            ]
            
            for field in required_fields:
                if field in data:
                    self.log_test(f"{test_name} - Field '{field}'", True, f"Present: {type(data[field]).__name__}")
                else:
                    self.log_test(f"{test_name} - Field '{field}'", False, "Missing required field")
                    
            # Test behavior_sequence format
            if "behavior_sequence" in data:
                behavior_seq = data["behavior_sequence"]
                if isinstance(behavior_seq, list) and len(behavior_seq) == 3:
                    self.log_test(f"{test_name} - Behavior Sequence Length", True, f"Array of {len(behavior_seq)} items")
                    
                    # Check "You..." format
                    you_format_count = 0
                    for item in behavior_seq:
                        if isinstance(item, str) and item.strip().startswith("You"):
                            you_format_count += 1
                    
                    if you_format_count > 0:
                        self.log_test(f"{test_name} - 'You...' Format", True, f"{you_format_count}/3 items start with 'You'")
                    else:
                        self.log_test(f"{test_name} - 'You...' Format", False, "No items start with 'You'")
                        
                else:
                    self.log_test(f"{test_name} - Behavior Sequence Length", False, f"Expected array of 3, got {type(behavior_seq).__name__}")
            
            # Test confidence range
            if "confidence" in data:
                confidence = data["confidence"]
                if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                    self.log_test(f"{test_name} - Confidence Range", True, f"Valid: {confidence}")
                else:
                    self.log_test(f"{test_name} - Confidence Range", False, f"Invalid: {confidence}")
                    
            # Test sources array
            if "sources" in data:
                sources = data["sources"]
                if isinstance(sources, list):
                    self.log_test(f"{test_name} - Sources Format", True, f"Array with {len(sources)} items")
                else:
                    self.log_test(f"{test_name} - Sources Format", False, f"Expected array, got {type(sources).__name__}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.log_test(f"{test_name} - HTTP Request", False, f"Request failed: {e}")
            return {}
        except Exception as e:
            self.log_test(f"{test_name} - Unexpected Error", False, f"Error: {e}")
            return {}
    
    def test_caching_behavior(self, user_id: str):
        """Test that caching works correctly"""
        try:
            url = f"{BACKEND_URL}/keystone-pattern/{user_id}"
            
            # First call
            print(f"\n--- Testing Caching Behavior for User: {user_id} ---")
            
            start_time = time.time()
            response1 = requests.get(url, timeout=30)
            response_time_1 = time.time() - start_time
            
            if response1.status_code != 200:
                self.log_test("Caching Test - First Call", False, f"HTTP {response1.status_code}")
                return
                
            data1 = response1.json()
            cached_1 = data1.get("cached", None)
            
            # Second call (should be cached)
            time.sleep(1)  # Small delay
            start_time = time.time()
            response2 = requests.get(url, timeout=30)
            response_time_2 = time.time() - start_time
            
            if response2.status_code != 200:
                self.log_test("Caching Test - Second Call", False, f"HTTP {response2.status_code}")
                return
                
            data2 = response2.json()
            cached_2 = data2.get("cached", None)
            
            # Test caching behavior
            if cached_2 is True:
                self.log_test("Caching Test - Second Call Cached", True, f"cached: {cached_2}")
            else:
                self.log_test("Caching Test - Second Call Cached", False, f"Expected cached: true, got: {cached_2}")
            
            # Test response time improvement
            if response_time_2 < response_time_1:
                self.log_test("Caching Test - Response Time", True, f"Faster: {response_time_2:.2f}s vs {response_time_1:.2f}s")
            else:
                self.log_test("Caching Test - Response Time", False, f"Not faster: {response_time_2:.2f}s vs {response_time_1:.2f}s")
                
            # Test content consistency
            fields_to_compare = ["pattern_id", "pattern_label", "behavior_sequence", "confidence", "date"]
            consistent = True
            for field in fields_to_compare:
                if data1.get(field) != data2.get(field):
                    consistent = False
                    break
            
            if consistent:
                self.log_test("Caching Test - Content Consistency", True, "Identical content between calls")
            else:
                self.log_test("Caching Test - Content Consistency", False, "Content differs between calls")
                
        except Exception as e:
            self.log_test("Caching Test - Unexpected Error", False, f"Error: {e}")
    
    def test_force_refresh(self, user_id: str):
        """Test force_refresh parameter"""
        try:
            print(f"\n--- Testing Force Refresh for User: {user_id} ---")
            
            url = f"{BACKEND_URL}/keystone-pattern/{user_id}?force_refresh=true"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                self.log_test("Force Refresh - HTTP Status", False, f"HTTP {response.status_code}")
                return
                
            self.log_test("Force Refresh - HTTP Status", True, "200 OK")
            
            data = response.json()
            cached = data.get("cached", None)
            
            if cached is False:
                self.log_test("Force Refresh - Cached Flag", True, f"cached: {cached}")
            else:
                self.log_test("Force Refresh - Cached Flag", False, f"Expected cached: false, got: {cached}")
                
        except Exception as e:
            self.log_test("Force Refresh - Unexpected Error", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🧪 KEYSTONE PATTERN API TESTING STARTING")
        print("=" * 60)
        
        # Test 1: Basic functionality with user 1
        print(f"\n--- Testing User 1: {TEST_USER_ID_1} ---")
        data1 = self.test_keystone_pattern_response_structure(TEST_USER_ID_1, "User 1")
        
        # Test 2: Different user
        print(f"\n--- Testing User 2: {TEST_USER_ID_2} ---")
        data2 = self.test_keystone_pattern_response_structure(TEST_USER_ID_2, "User 2")
        
        # Test 3: Caching behavior (use user 1)
        self.test_caching_behavior(TEST_USER_ID_1)
        
        # Test 4: Force refresh (use user 1)
        self.test_force_refresh(TEST_USER_ID_1)
        
        # Summary
        print("\n" + "=" * 60)
        print("🧪 KEYSTONE PATTERN API TEST SUMMARY")
        print("=" * 60)
        
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
        
        # Show sample responses if available
        if data1:
            print(f"\n📊 SAMPLE RESPONSE (User 1):")
            print(f"  Pattern ID: {data1.get('pattern_id', 'N/A')}")
            print(f"  Pattern Label: {data1.get('pattern_label', 'N/A')}")
            print(f"  Behavior Sequence: {data1.get('behavior_sequence', 'N/A')}")
            print(f"  Confidence: {data1.get('confidence', 'N/A')}")
            print(f"  Sources: {data1.get('sources', 'N/A')}")
            print(f"  Date: {data1.get('date', 'N/A')}")
            print(f"  Cached: {data1.get('cached', 'N/A')}")
        
        return self.passed_tests == self.total_tests


if __name__ == "__main__":
    tester = KeystonePatternTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n🚨 SOME TESTS FAILED!")
        sys.exit(1)