#!/usr/bin/env python3
"""
Backend Testing Suite for Project Mirror
Testing Enneagram Deep Assessment Completion Flow on STAGING
Based on review request requirements
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration from review request
BASE_URL = "https://cachebuster-2.preview.emergentagent.com/api"
TEST_USER_ID = "69954fa73125ba897cbea948"  # From review request

class EnneagramDeepAssessmentTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Dict = None):
        """Log test results for reporting"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        # Print immediate feedback
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")
        print()
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> tuple[int, Dict]:
        """Make HTTP request and return status code and response data"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response", "text": await response.text()}
                    return status, response_data
            
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response", "text": await response.text()}
                    return status, response_data
                    
        except Exception as e:
            return 0, {"error": f"Request failed: {str(e)}"}
    
    async def test_0_health_endpoint(self) -> bool:
        """Test 0: Verify Health Endpoint (Review Request Test 1)"""
        print("🧪 TEST 0: Health Endpoint Verification")
        
        status, response = await self.make_request("GET", "/health")
        
        if status != 200:
            self.log_test("Health Endpoint", "FAIL", f"HTTP {status}: {response.get('detail', 'Unknown error')}", response)
            return False
        
        # Check required fields from review request
        expected_env = "staging"
        expected_db_name = "mirror_staging"
        expected_debug_mirror = False
        
        actual_env = response.get("env")
        actual_db_name = response.get("db_name")
        actual_debug_mirror = response.get("debug_mirror")
        
        issues = []
        if actual_env != expected_env:
            issues.append(f"env: expected '{expected_env}', got '{actual_env}'")
        if actual_db_name != expected_db_name:
            issues.append(f"db_name: expected '{expected_db_name}', got '{actual_db_name}'")
        if actual_debug_mirror != expected_debug_mirror:
            issues.append(f"debug_mirror: expected {expected_debug_mirror}, got {actual_debug_mirror}")
        
        if issues:
            self.log_test("Health Endpoint", "FAIL", f"Health check issues: {'; '.join(issues)}", response)
            return False
        
        details = f"env: '{actual_env}', db_name: '{actual_db_name}', debug_mirror: {actual_debug_mirror}"
        self.log_test("Health Endpoint", "PASS", details, response)
        return True
        """Test 1: Start Deep Assessment"""
        print("🧪 TEST 1: Starting Enneagram Deep Assessment")
        
        payload = {"user_id": TEST_USER_ID}
        status, response = await self.make_request("POST", "/enneagram/deep-assessment/start", payload)
        
        if status == 200:
            if "session_id" in response and "question" in response and "progress" in response:
                session_id = response["session_id"]
                question = response["question"]
                progress = response["progress"]
                
                details = f"Session ID: {session_id}, Question ID: {question.get('id', 'N/A')}, Progress: {progress.get('current', 0)}/{progress.get('total', 0)}"
                self.log_test("Start Assessment", "PASS", details, response)
                return session_id
            else:
                missing_fields = []
                if "session_id" not in response:
                    missing_fields.append("session_id")
                if "question" not in response:
                    missing_fields.append("question")
                if "progress" not in response:
                    missing_fields.append("progress")
                
                self.log_test("Start Assessment", "FAIL", f"Missing required fields: {missing_fields}", response)
                return None
        else:
            self.log_test("Start Assessment", "FAIL", f"HTTP {status}: {response.get('detail', 'Unknown error')}", response)
            return None
    
    async def test_2_submit_answers_until_completion(self, session_id: str) -> Optional[Dict]:
        """Test 2: Submit Multiple Answers Until Assessment Completion"""
        print("🧪 TEST 2: Submitting Answers Until Assessment Completion")
        
        answers_submitted = 0
        max_answers = 70  # Safety limit (should complete around 58)
        results = None
        
        while answers_submitted < max_answers:
            # Get current question by submitting a dummy answer first to see what question we're on
            # Actually, let's start by getting the first question from start response
            if answers_submitted == 0:
                # We need to get the first question - let's restart to get it
                payload = {"user_id": TEST_USER_ID}
                status, response = await self.make_request("POST", "/enneagram/deep-assessment/start", payload)
                if status != 200 or "question" not in response:
                    self.log_test("Get First Question", "FAIL", f"Could not get first question: {response}", response)
                    return None
                
                session_id = response["session_id"]  # Update session_id
                current_question = response["question"]
            else:
                # For subsequent questions, we'll get them from the previous answer response
                pass
            
            # Submit answer for current question
            question_id = current_question["id"]
            
            # Determine answer type based on question format
            question_type = current_question.get("type", "likert")
            
            if question_type == "forced" or "options" in current_question:
                # Forced choice question - use "A" as default
                answer_payload = {
                    "user_id": TEST_USER_ID,
                    "session_id": session_id,
                    "question_id": question_id,
                    "answer": {"type": "forced", "value": "A"}
                }
            else:
                # Likert scale question - use 3 (neutral)
                answer_payload = {
                    "user_id": TEST_USER_ID,
                    "session_id": session_id,
                    "question_id": question_id,
                    "answer": {"type": "likert", "value": 3}
                }
            
            status, response = await self.make_request("POST", "/enneagram/deep-assessment/answer", answer_payload)
            answers_submitted += 1
            
            if status != 200:
                # Check if this is the MongoDB error we're testing for
                error_detail = response.get("detail", "")
                if "documents must have only string keys, key was" in error_detail:
                    self.log_test("Submit Answers", "FAIL", f"MongoDB bug detected after {answers_submitted} answers: {error_detail}", response)
                    return None
                else:
                    self.log_test("Submit Answers", "FAIL", f"HTTP {status} after {answers_submitted} answers: {error_detail}", response)
                    return None
            
            # Check if assessment is complete
            if "results" in response:
                results = response["results"]
                progress = response.get("progress", {})
                self.log_test("Submit Answers", "PASS", f"Assessment completed after {answers_submitted} answers. Progress: {progress}", response)
                return results
            
            # Check if we have next question
            if "question" in response:
                current_question = response["question"]
                progress = response.get("progress", {})
                print(f"   Answer {answers_submitted}: Question {question_id} → Next: {current_question['id']} (Progress: {progress.get('current', 0)}/{progress.get('total', 0)})")
            else:
                self.log_test("Submit Answers", "FAIL", f"No 'question' or 'results' in response after {answers_submitted} answers", response)
                return None
        
        # If we reach here, we hit the safety limit
        self.log_test("Submit Answers", "FAIL", f"Assessment did not complete after {max_answers} answers (safety limit)", None)
        return None
    
    async def test_3_verify_results_structure(self, results: Dict) -> bool:
        """Test 3: Verify Results Structure"""
        print("🧪 TEST 3: Verifying Results Structure")
        
        required_fields = ["core_type", "wing", "confidence", "confidence_tier"]
        missing_fields = []
        invalid_fields = []
        
        # Check required fields exist
        for field in required_fields:
            if field not in results:
                missing_fields.append(field)
        
        if missing_fields:
            self.log_test("Results Structure", "FAIL", f"Missing required fields: {missing_fields}", results)
            return False
        
        # Validate field values
        core_type = results.get("core_type")
        if not isinstance(core_type, int) or core_type < 1 or core_type > 9:
            invalid_fields.append(f"core_type must be 1-9, got: {core_type}")
        
        wing = results.get("wing")
        if not isinstance(wing, (int, str)):
            invalid_fields.append(f"wing must be int or string, got: {type(wing)}")
        
        confidence = results.get("confidence")
        if not isinstance(confidence, (int, float)):
            invalid_fields.append(f"confidence must be number, got: {type(confidence)}")
        
        confidence_tier = results.get("confidence_tier")
        valid_tiers = ["high", "moderate", "exploratory"]
        if confidence_tier not in valid_tiers:
            invalid_fields.append(f"confidence_tier must be one of {valid_tiers}, got: {confidence_tier}")
        
        if invalid_fields:
            self.log_test("Results Structure", "FAIL", f"Invalid field values: {invalid_fields}", results)
            return False
        
        # Success
        details = f"core_type: {core_type}, wing: {wing}, confidence: {confidence}, confidence_tier: {confidence_tier}"
        self.log_test("Results Structure", "PASS", details, results)
        return True
    
    async def run_all_tests(self):
        """Run the complete test suite"""
        print("=" * 80)
        print("🧪 ENNEAGRAM DEEP ASSESSMENT MONGODB BUG FIX TESTING")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Test User ID: {TEST_USER_ID}")
        print()
        
        # Test 1: Start Assessment
        session_id = await self.test_1_start_assessment()
        if not session_id:
            print("❌ Cannot continue testing - failed to start assessment")
            return False
        
        # Test 2: Submit Answers Until Completion
        results = await self.test_2_submit_answers_until_completion(session_id)
        if not results:
            print("❌ Cannot continue testing - failed to complete assessment")
            return False
        
        # Test 3: Verify Results Structure
        structure_valid = await self.test_3_verify_results_structure(results)
        if not structure_valid:
            print("❌ Results structure validation failed")
            return False
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for test in self.test_results:
                if test["status"] == "FAIL":
                    print(f"   • {test['test']}: {test['details']}")
            print()
        
        # Key findings
        mongodb_error_found = any("MongoDB bug detected" in t.get("details", "") for t in self.test_results)
        assessment_completed = any("Assessment completed" in t.get("details", "") for t in self.test_results)
        
        print("🔍 KEY FINDINGS:")
        if mongodb_error_found:
            print("   ❌ MongoDB bug 'documents must have only string keys, key was 1' STILL EXISTS")
        else:
            print("   ✅ MongoDB bug 'documents must have only string keys, key was 1' NOT detected")
        
        if assessment_completed:
            print("   ✅ Assessment completed successfully with results object")
        else:
            print("   ❌ Assessment did not complete successfully")
        
        print()
        
        return failed_tests == 0


async def main():
    """Main test execution"""
    async with EnneagramDeepAssessmentTester() as tester:
        success = await tester.run_all_tests()
        tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())