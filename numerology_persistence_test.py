#!/usr/bin/env python3
"""
Backend API Testing for Numerology Full Name Persistence
Test the end-to-end flow of numerology full name unlock and persistence
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://experience-controls.preview.emergentagent.com/api"

# Test user ID from review request
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

class NumerologyPersistenceTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results with clear formatting"""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   {details}")
        print()
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> tuple[int, Dict]:
        """Make HTTP request and return status code and response data"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"error": "Invalid JSON response", "text": response.text[:500]}
            
            return response.status_code, response_data
        
        except requests.exceptions.RequestException as e:
            return 0, {"error": f"Request failed: {str(e)}"}
    
    def test_1_get_initial_profile(self) -> Dict[str, Any]:
        """Test 1: GET /api/profile/{user_id} - Check initial state"""
        print("🔍 TEST 1: Get Initial Profile State")
        
        status_code, response = self.make_request("GET", f"/profile/{TEST_USER_ID}")
        
        if status_code != 200:
            self.log_test("Initial Profile GET", "FAIL", f"Status: {status_code}, Response: {response}")
            return {}
        
        # Check if numerology_full_name exists
        numerology_full_name = response.get("numerology_full_name")
        
        details = f"Status: {status_code}, numerology_full_name: {numerology_full_name}"
        self.log_test("Initial Profile GET", "PASS", details)
        
        return response
    
    def test_2_unlock_name_first_time(self) -> Dict[str, Any]:
        """Test 2: POST /api/numerology/unlock-name/{user_id} - First unlock"""
        print("🔓 TEST 2: Unlock Name (First Time)")
        
        test_name = "Test Integration Name"
        payload = {"full_birth_name": test_name}
        
        status_code, response = self.make_request("POST", f"/numerology/unlock-name/{TEST_USER_ID}", payload)
        
        if status_code != 200:
            self.log_test("Name Unlock (First)", "FAIL", f"Status: {status_code}, Response: {response}")
            return {}
        
        # Check if response indicates success
        success = response.get("success", False)
        if not success:
            self.log_test("Name Unlock (First)", "FAIL", f"Success: {success}, Response: {response}")
            return {}
        
        # Check if computed numbers are returned in unlocked_numbers structure
        unlocked_numbers = response.get("unlocked_numbers", {})
        expression = unlocked_numbers.get("expression", {}).get("number") if unlocked_numbers else None
        soul_urge = unlocked_numbers.get("soul_urge", {}).get("number") if unlocked_numbers else None
        personality = unlocked_numbers.get("personality", {}).get("number") if unlocked_numbers else None
        
        details = f"Success: {success}, Expression: {expression}, Soul Urge: {soul_urge}, Personality: {personality}"
        self.log_test("Name Unlock (First)", "PASS", details)
        
        return response
    
    def test_3_verify_persistence_read_after_write(self) -> Dict[str, Any]:
        """Test 3: GET /api/profile/{user_id} - Verify name was persisted"""
        print("📖 TEST 3: Verify Persistence (Read-After-Write)")
        
        # Small delay to ensure write is complete
        time.sleep(1)
        
        status_code, response = self.make_request("GET", f"/profile/{TEST_USER_ID}")
        
        if status_code != 200:
            self.log_test("Read-After-Write", "FAIL", f"Status: {status_code}, Response: {response}")
            return {}
        
        # Check if numerology_full_name was persisted
        numerology_full_name = response.get("numerology_full_name")
        expected_name = "Test Integration Name"
        
        if numerology_full_name != expected_name:
            self.log_test("Read-After-Write", "FAIL", f"Expected: '{expected_name}', Got: '{numerology_full_name}'")
            return {}
        
        details = f"numerology_full_name correctly persisted: '{numerology_full_name}'"
        self.log_test("Read-After-Write", "PASS", details)
        
        return response
    
    def test_4_update_name_different_value(self) -> Dict[str, Any]:
        """Test 4: POST /api/numerology/unlock-name/{user_id} - Update with different name"""
        print("🔄 TEST 4: Update Name (Different Value)")
        
        new_test_name = "Updated Integration Name"
        payload = {"full_birth_name": new_test_name}
        
        status_code, response = self.make_request("POST", f"/numerology/unlock-name/{TEST_USER_ID}", payload)
        
        if status_code != 200:
            self.log_test("Name Update", "FAIL", f"Status: {status_code}, Response: {response}")
            return {}
        
        # Check if response indicates success
        success = response.get("success", False)
        if not success:
            self.log_test("Name Update", "FAIL", f"Success: {success}, Response: {response}")
            return {}
        
        # Check if computed numbers are returned (should be different)
        unlocked_numbers = response.get("unlocked_numbers", {})
        expression = unlocked_numbers.get("expression", {}).get("number") if unlocked_numbers else None
        soul_urge = unlocked_numbers.get("soul_urge", {}).get("number") if unlocked_numbers else None
        personality = unlocked_numbers.get("personality", {}).get("number") if unlocked_numbers else None
        
        details = f"Success: {success}, New Expression: {expression}, Soul Urge: {soul_urge}, Personality: {personality}"
        self.log_test("Name Update", "PASS", details)
        
        return response
    
    def test_5_verify_update_persistence(self) -> Dict[str, Any]:
        """Test 5: GET /api/profile/{user_id} - Verify updated name was persisted"""
        print("📝 TEST 5: Verify Update Persistence")
        
        # Small delay to ensure write is complete
        time.sleep(1)
        
        status_code, response = self.make_request("GET", f"/profile/{TEST_USER_ID}")
        
        if status_code != 200:
            self.log_test("Update Persistence", "FAIL", f"Status: {status_code}, Response: {response}")
            return {}
        
        # Check if updated numerology_full_name was persisted
        numerology_full_name = response.get("numerology_full_name")
        expected_name = "Updated Integration Name"
        
        if numerology_full_name != expected_name:
            self.log_test("Update Persistence", "FAIL", f"Expected: '{expected_name}', Got: '{numerology_full_name}'")
            return {}
        
        details = f"Updated numerology_full_name correctly persisted: '{numerology_full_name}'"
        self.log_test("Update Persistence", "PASS", details)
        
        return response
    
    def test_6_numerology_summary_includes_name_numbers(self) -> Dict[str, Any]:
        """Test 6: GET /api/numerology/summary/{user_id} - Verify name-based numbers included"""
        print("📊 TEST 6: Numerology Summary Includes Name-Based Numbers")
        
        status_code, response = self.make_request("GET", f"/numerology/summary/{TEST_USER_ID}")
        
        if status_code != 200:
            self.log_test("Numerology Summary", "FAIL", f"Status: {status_code}, Response: {response}")
            return {}
        
        # Check if name-based numbers are included in the summary text
        sections = response.get("sections", [])
        summary_text = ""
        for section in sections:
            summary_text += section.get("body", "") + " "
        
        summary_text = summary_text.lower()
        
        # Look for the name-based numbers in the text
        has_expression = "expression" in summary_text and any(f"expression {i}" in summary_text for i in range(1, 12))
        has_soul_urge = "soul urge" in summary_text and any(f"soul urge {i}" in summary_text for i in range(1, 12))
        has_personality = "personality" in summary_text and any(f"personality {i}" in summary_text for i in range(1, 12))
        
        # Check if unlock_required is false (meaning name is unlocked)
        unlock_required = response.get("unlock_required", True)
        
        if not has_expression or not has_soul_urge or not has_personality:
            self.log_test("Numerology Summary", "FAIL", f"Name-based numbers missing from summary text. Expression: {has_expression}, Soul Urge: {has_soul_urge}, Personality: {has_personality}")
            return {}
        
        if unlock_required:
            self.log_test("Numerology Summary", "FAIL", f"unlock_required is still True, should be False when name is unlocked")
            return {}
        
        details = f"Name-based numbers present in summary text - Expression: {has_expression}, Soul Urge: {has_soul_urge}, Personality: {has_personality}, unlock_required: {unlock_required}"
        self.log_test("Numerology Summary", "PASS", details)
        
        return response
    
    def run_all_tests(self):
        """Run all numerology persistence tests in sequence"""
        print("=" * 80)
        print("🧪 NUMEROLOGY FULL NAME PERSISTENCE - END-TO-END TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User ID: {TEST_USER_ID}")
        print()
        
        # Track test results
        test_results = []
        
        try:
            # Test 1: Get initial profile state
            initial_profile = self.test_1_get_initial_profile()
            test_results.append(("Initial Profile GET", bool(initial_profile)))
            
            # Test 2: Unlock name for first time
            unlock_response = self.test_2_unlock_name_first_time()
            test_results.append(("Name Unlock (First)", bool(unlock_response)))
            
            # Test 3: Verify persistence (read-after-write)
            read_after_write = self.test_3_verify_persistence_read_after_write()
            test_results.append(("Read-After-Write", bool(read_after_write)))
            
            # Test 4: Update name with different value
            update_response = self.test_4_update_name_different_value()
            test_results.append(("Name Update", bool(update_response)))
            
            # Test 5: Verify update persistence
            update_persistence = self.test_5_verify_update_persistence()
            test_results.append(("Update Persistence", bool(update_persistence)))
            
            # Test 6: Verify numerology summary includes name-based numbers
            summary_response = self.test_6_numerology_summary_includes_name_numbers()
            test_results.append(("Numerology Summary", bool(summary_response)))
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR: {str(e)}")
            test_results.append(("Critical Error", False))
        
        # Summary
        print("=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status_symbol = "✅" if result else "❌"
            print(f"{status_symbol} {test_name}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Numerology full name persistence is working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED - Issues found with numerology full name persistence")
        
        return passed == total


if __name__ == "__main__":
    tester = NumerologyPersistenceTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)