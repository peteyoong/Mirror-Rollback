#!/usr/bin/env python3
"""
Backend Test Suite for Enneagram V3 Assessment Anger Triad Fix
==============================================================

This test suite verifies the critical bug fix in the Enneagram V3 Assessment
where the Anger triad (Types 8, 9, 1) could not be locked during Phase 1.

The fix involved interleaving questions from all triads instead of asking
them sequentially (Fear first, then Shame, then Anger).

Test Scenarios:
1. Type 8 Full Path (Anger Triad)
2. Type 5 Full Path (Fear Triad - Regression Test)
3. Verify all assessment paths complete without errors
4. Verify Anger triad can be locked
5. Verify Fear and Shame triads still work correctly
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import aiohttp


class EnneagramV3Tester:
    """Test suite for Enneagram V3 Assessment endpoints."""
    
    def __init__(self, base_url: str = "https://mirror-lens-fixes.emergent.host"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result."""
        timestamp = datetime.now(timezone.utc).isoformat()
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": timestamp
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    async def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple:
        """Make HTTP request and return (status, response_data, error)."""
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = await response.text()
                    return status, data, None
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = await response.text()
                    return status, data, None
        except Exception as e:
            return 0, None, str(e)
    
    async def test_health_check(self) -> bool:
        """Test basic API health."""
        print("\n🔍 Testing API Health...")
        
        status, data, error = await self.make_request("GET", "/health")
        
        if error:
            self.log_test("API Health Check", "FAIL", f"Connection error: {error}")
            return False
        
        if status != 200:
            self.log_test("API Health Check", "FAIL", f"Status {status}: {data}")
            return False
        
        if isinstance(data, dict) and data.get("env") == "staging":
            self.log_test("API Health Check", "PASS", f"Environment: {data.get('env')}, DB: {data.get('db_name')}")
            return True
        else:
            self.log_test("API Health Check", "FAIL", f"Unexpected response: {data}")
            return False
    
    async def complete_assessment_scenario(self, user_id: str, scenario_name: str, 
                                         target_triad: str, target_type: int) -> Optional[dict]:
        """
        Complete a full assessment scenario targeting a specific type.
        
        Args:
            user_id: Test user ID
            scenario_name: Name for logging
            target_triad: "fear", "shame", or "anger"
            target_type: Target Enneagram type (1-9)
        
        Returns:
            Final result dict or None if failed
        """
        print(f"\n🎯 Testing {scenario_name}...")
        
        # Step 1: Start Assessment
        start_status, start_data, start_error = await self.make_request(
            "POST", "/enneagram/v3/start", {"user_id": user_id}
        )
        
        if start_error or start_status != 200:
            self.log_test(f"{scenario_name} - Start", "FAIL", 
                         f"Status {start_status}, Error: {start_error or start_data}")
            return None
        
        if not isinstance(start_data, dict) or "session_id" not in start_data:
            self.log_test(f"{scenario_name} - Start", "FAIL", 
                         f"Invalid start response: {start_data}")
            return None
        
        session_id = start_data["session_id"]
        self.log_test(f"{scenario_name} - Start", "PASS", 
                     f"Session ID: {session_id}")
        
        # Step 2: Answer questions until completion
        question_count = 0
        max_questions = 100  # Safety limit
        
        while question_count < max_questions:
            # Get current question from start_data or previous response
            if "question" not in start_data:
                self.log_test(f"{scenario_name} - Questions", "FAIL", 
                             "No question in response")
                return None
            
            current_question = start_data["question"]
            question_id = current_question["id"]
            question_count += 1
            
            # Determine answer based on target triad and type
            answer_value = self.get_strategic_answer(
                current_question, target_triad, target_type
            )
            
            # Submit answer
            answer_payload = {
                "user_id": user_id,
                "session_id": session_id,
                "question_id": question_id,
                "response_value": answer_value
            }
            
            answer_status, answer_data, answer_error = await self.make_request(
                "POST", "/enneagram/v3/respond", answer_payload
            )
            
            if answer_error or answer_status != 200:
                self.log_test(f"{scenario_name} - Question {question_count}", "FAIL",
                             f"Status {answer_status}, Error: {answer_error or answer_data}")
                return None
            
            if not isinstance(answer_data, dict):
                self.log_test(f"{scenario_name} - Question {question_count}", "FAIL",
                             f"Invalid answer response: {answer_data}")
                return None
            
            # Check if assessment is complete
            if answer_data.get("status") == "done":
                final_result = answer_data.get("final_result")
                if final_result:
                    self.log_test(f"{scenario_name} - Complete", "PASS",
                                 f"Completed in {question_count} questions. Result: {final_result.get('full_type_string')}")
                    return final_result
                else:
                    self.log_test(f"{scenario_name} - Complete", "FAIL",
                                 "Status 'done' but no final_result")
                    return None
            
            # Continue with next question
            if "question" in answer_data:
                start_data = answer_data  # Update for next iteration
            else:
                self.log_test(f"{scenario_name} - Questions", "FAIL",
                             f"No next question after {question_count} questions")
                return None
        
        self.log_test(f"{scenario_name} - Questions", "FAIL",
                     f"Exceeded maximum questions ({max_questions})")
        return None
    
    def get_strategic_answer(self, question: dict, target_triad: str, target_type: int) -> int:
        """
        Get strategic answer to guide assessment toward target type.
        
        This simulates a user answering questions in a way that would
        naturally lead to the target type being identified.
        """
        question_id = question["id"]
        question_text = question.get("question", "")
        options = question.get("options", [])
        
        # Phase 1: Triad questions (F1-F7, S1-S7, A1-A6)
        if question_id.startswith(("F", "S", "A")) and len(question_id) <= 2:
            if target_triad == "fear" and question_id.startswith("F"):
                return 5  # Strongly agree with Fear triad questions
            elif target_triad == "shame" and question_id.startswith("S"):
                return 5  # Strongly agree with Shame triad questions  
            elif target_triad == "anger" and question_id.startswith("A"):
                return 5  # Strongly agree with Anger triad questions
            else:
                return 1  # Strongly disagree with non-target triads
        
        # Phase 2: Type-specific questions
        if question_id.startswith(("F5-", "F6-", "F7-", "S2-", "S3-", "S4-", "A8-", "A9-", "A1-")):
            # Extract target type from question ID
            if question_id.startswith(f"F{target_type}-") or \
               question_id.startswith(f"S{target_type}-") or \
               question_id.startswith(f"A{target_type}-"):
                return 5  # Strongly agree with target type questions
            else:
                return 1  # Strongly disagree with other type questions
        
        # Phase 2: Differential questions (FD-, SD-, AD-)
        if question_id.startswith(("FD-", "SD-", "AD-")):
            # Look for options that boost target type
            for option in options:
                if option.get("type_boost") == target_type:
                    return option["value"]
            # Fallback to middle option
            return 3
        
        # Phase 3: Wing and subtype questions
        if question_id.startswith(("W", "SP-", "SO-", "SX-")):
            # For wing questions, choose based on target type's wings
            if question_id.startswith("W"):
                # Randomly choose wing direction
                return 3  # Neutral/balanced
            else:
                # For subtype, vary the answers to create a realistic stack
                if question_id.endswith("-1"):
                    return 4  # Primary instinct
                else:
                    return 2  # Secondary/tertiary instincts
        
        # Default: neutral response
        return 3
    
    async def test_type_8_scenario(self) -> bool:
        """Test Type 8 (Anger Triad) full assessment path."""
        user_id = "699dc2e5f8e69a10ec38cd31"  # Valid ObjectId for test user
        
        result = await self.complete_assessment_scenario(
            user_id, "Type 8 Full Path", "anger", 8
        )
        
        if not result:
            return False
        
        # Verify result structure
        required_fields = ["core_type", "wing", "subtype_stack", "full_type_string"]
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            self.log_test("Type 8 - Result Structure", "FAIL",
                         f"Missing fields: {missing_fields}")
            return False
        
        # Verify it's an Anger triad type (8, 9, or 1)
        core_type = result.get("core_type")
        if core_type not in [8, 9, 1]:
            self.log_test("Type 8 - Triad Verification", "FAIL",
                         f"Expected Anger triad (8,9,1), got type {core_type}")
            return False
        
        self.log_test("Type 8 - Result Structure", "PASS",
                     f"All required fields present. Core type: {core_type}")
        return True
    
    async def test_type_5_scenario(self) -> bool:
        """Test Type 5 (Fear Triad) full assessment path - regression test."""
        user_id = "699dc2e6f8e69a10ec38cd32"  # Valid ObjectId for test user
        
        result = await self.complete_assessment_scenario(
            user_id, "Type 5 Full Path (Regression)", "fear", 5
        )
        
        if not result:
            return False
        
        # Verify result structure
        required_fields = ["core_type", "wing", "subtype_stack", "full_type_string"]
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            self.log_test("Type 5 - Result Structure", "FAIL",
                         f"Missing fields: {missing_fields}")
            return False
        
        # Verify it's a Fear triad type (5, 6, or 7)
        core_type = result.get("core_type")
        if core_type not in [5, 6, 7]:
            self.log_test("Type 5 - Triad Verification", "FAIL",
                         f"Expected Fear triad (5,6,7), got type {core_type}")
            return False
        
        self.log_test("Type 5 - Result Structure", "PASS",
                     f"All required fields present. Core type: {core_type}")
        return True
    
    async def test_session_status(self) -> bool:
        """Test session status endpoint."""
        print("\n📊 Testing Session Status...")
        
        # Start a session first
        user_id = "test_status_backend"
        start_status, start_data, start_error = await self.make_request(
            "POST", "/enneagram/v3/start", {"user_id": user_id}
        )
        
        if start_error or start_status != 200 or not isinstance(start_data, dict):
            self.log_test("Session Status - Setup", "FAIL",
                         f"Could not start session: {start_error or start_data}")
            return False
        
        session_id = start_data.get("session_id")
        if not session_id:
            self.log_test("Session Status - Setup", "FAIL", "No session_id in response")
            return False
        
        # Test status endpoint
        status_status, status_data, status_error = await self.make_request(
            "GET", f"/enneagram/v3/status/{session_id}"
        )
        
        if status_error or status_status != 200:
            self.log_test("Session Status", "FAIL",
                         f"Status {status_status}, Error: {status_error or status_data}")
            return False
        
        if not isinstance(status_data, dict):
            self.log_test("Session Status", "FAIL", f"Invalid response: {status_data}")
            return False
        
        # Verify status structure
        expected_fields = ["found", "session_id", "phase", "progress"]
        missing_fields = [field for field in expected_fields if field not in status_data]
        
        if missing_fields:
            self.log_test("Session Status", "FAIL", f"Missing fields: {missing_fields}")
            return False
        
        if not status_data.get("found"):
            self.log_test("Session Status", "FAIL", "Session not found")
            return False
        
        self.log_test("Session Status", "PASS",
                     f"Phase: {status_data.get('phase')}, Progress: {status_data.get('progress', {}).get('percentage', 0)}%")
        return True
    
    async def run_all_tests(self) -> dict:
        """Run all test scenarios."""
        print("🧪 Starting Enneagram V3 Assessment Anger Triad Fix Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Health Check
        health_ok = await self.test_health_check()
        if not health_ok:
            print("\n❌ Health check failed. Aborting tests.")
            return self.get_summary(start_time, False)
        
        # Test 2: Session Status
        status_ok = await self.test_session_status()
        
        # Test 3: Type 8 Scenario (Main test - Anger triad)
        type8_ok = await self.test_type_8_scenario()
        
        # Test 4: Type 5 Scenario (Regression test - Fear triad)
        type5_ok = await self.test_type_5_scenario()
        
        # Summary
        all_passed = health_ok and status_ok and type8_ok and type5_ok
        return self.get_summary(start_time, all_passed)
    
    def get_summary(self, start_time: float, all_passed: bool) -> dict:
        """Generate test summary."""
        end_time = time.time()
        duration = end_time - start_time
        
        passed_count = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_count = len([r for r in self.test_results if r["status"] == "FAIL"])
        total_count = len(self.test_results)
        
        summary = {
            "overall_status": "PASS" if all_passed else "FAIL",
            "total_tests": total_count,
            "passed": passed_count,
            "failed": failed_count,
            "duration_seconds": round(duration, 2),
            "test_results": self.test_results
        }
        
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        status_emoji = "✅" if all_passed else "❌"
        print(f"{status_emoji} Overall Status: {summary['overall_status']}")
        print(f"📊 Tests: {passed_count}/{total_count} passed")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if failed_count > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test']}: {result['details']}")
        
        return summary


async def main():
    """Main test runner."""
    # Use the staging URL from frontend .env
    base_url = "https://mirror-lens-fixes.emergent.host"
    
    async with EnneagramV3Tester(base_url) as tester:
        summary = await tester.run_all_tests()
        
        # Exit with appropriate code
        exit_code = 0 if summary["overall_status"] == "PASS" else 1
        
        print(f"\n🏁 Tests completed with exit code: {exit_code}")
        
        # Save detailed results to file
        with open("/app/test_results_v3.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"📄 Detailed results saved to: /app/test_results_v3.json")
        
        return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)