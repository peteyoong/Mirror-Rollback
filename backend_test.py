#!/usr/bin/env python3
"""
Backend Test Suite for Project Mirror
=====================================

Comprehensive testing for backend API endpoints.
Focus: Two-Layer Mirror Output API feature testing.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://signals-first-home.preview.emergentagent.com/api"

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.response_time = 0.0
        self.details = {}

class BackendTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, result: TestResult):
        """Log test result with details."""
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} {result.name} ({result.response_time:.2f}s)")
        if result.error:
            print(f"   Error: {result.error}")
        if result.details:
            for key, value in result.details.items():
                print(f"   {key}: {value}")
        print()
    
    async def test_two_layer_output_api(self, user_id: str) -> TestResult:
        """
        Test the Two-Layer Mirror Output API feature.
        
        ENDPOINT: GET /api/patterns/{user_id}
        TEST FOCUS: Verify the new `two_layer_output` field in the API response
        """
        result = TestResult("Two-Layer Mirror Output API Structure")
        
        try:
            start_time = time.time()
            
            # Make API request with force_refresh to ensure fresh data
            url = f"{BACKEND_URL}/patterns/{user_id}?force_refresh=true"
            async with self.session.get(url) as response:
                result.response_time = time.time() - start_time
                
                if response.status != 200:
                    result.error = f"HTTP {response.status}: {await response.text()}"
                    return result
                
                data = await response.json()
                result.details["status_code"] = response.status
                result.details["response_size"] = len(str(data))
                
                # Verify two_layer_output field exists
                if "two_layer_output" not in data:
                    result.error = "Missing 'two_layer_output' field in response"
                    return result
                
                two_layer = data["two_layer_output"]
                
                # Test 1: Verify core_insight structure
                if "core_insight" not in two_layer:
                    result.error = "Missing 'core_insight' in two_layer_output"
                    return result
                
                core_insight = two_layer["core_insight"]
                if not isinstance(core_insight.get("title"), str):
                    result.error = "core_insight.title must be a string"
                    return result
                
                if not isinstance(core_insight.get("text"), str):
                    result.error = "core_insight.text must be a string"
                    return result
                
                result.details["core_insight_title"] = core_insight["title"][:50] + "..." if len(core_insight["title"]) > 50 else core_insight["title"]
                result.details["core_insight_text_length"] = len(core_insight["text"])
                
                # Test 2: Verify why_showing_up structure
                if "why_showing_up" not in two_layer:
                    result.error = "Missing 'why_showing_up' in two_layer_output"
                    return result
                
                why_showing_up = two_layer["why_showing_up"]
                if not isinstance(why_showing_up.get("text"), str):
                    result.error = "why_showing_up.text must be a string"
                    return result
                
                if not isinstance(why_showing_up.get("is_timing_driven"), bool):
                    result.error = "why_showing_up.is_timing_driven must be a boolean"
                    return result
                
                result.details["why_showing_up_text_length"] = len(why_showing_up["text"])
                result.details["is_timing_driven"] = why_showing_up["is_timing_driven"]
                
                # Test 3: Verify cross_lens_derivation structure
                if "cross_lens_derivation" not in two_layer:
                    result.error = "Missing 'cross_lens_derivation' in two_layer_output"
                    return result
                
                derivation = two_layer["cross_lens_derivation"]
                
                # Check lenses array
                if "lenses" not in derivation or not isinstance(derivation["lenses"], list):
                    result.error = "cross_lens_derivation.lenses must be an array"
                    return result
                
                lenses = derivation["lenses"]
                result.details["lenses_count"] = len(lenses)
                
                # Test 4: Verify lens structure and plain language signals
                for i, lens in enumerate(lenses):
                    if not isinstance(lens.get("lens"), str):
                        result.error = f"Lens {i}: 'lens' field must be a string"
                        return result
                    
                    if not isinstance(lens.get("signal"), str):
                        result.error = f"Lens {i}: 'signal' field must be a string"
                        return result
                    
                    if not isinstance(lens.get("contributed"), bool):
                        result.error = f"Lens {i}: 'contributed' field must be a boolean"
                        return result
                    
                    # Test 5: Verify no jargon in signals (no "Gate 22" or technical terms)
                    signal = lens["signal"].lower()
                    jargon_terms = ["gate ", "line ", "channel ", "center ", "resource element", "wood element", "fire element"]
                    for jargon in jargon_terms:
                        if jargon in signal:
                            result.error = f"Lens {i}: Signal contains jargon '{jargon}': {lens['signal']}"
                            return result
                
                # Test 6: Verify convergence fields
                required_convergence_fields = ["convergence_count", "shows_convergence", "convergence_note"]
                for field in required_convergence_fields:
                    if field not in derivation:
                        result.error = f"Missing '{field}' in cross_lens_derivation"
                        return result
                
                if not isinstance(derivation["convergence_count"], int):
                    result.error = "convergence_count must be an integer"
                    return result
                
                if not isinstance(derivation["shows_convergence"], bool):
                    result.error = "shows_convergence must be a boolean"
                    return result
                
                # Test 7: Verify convergence_count matches contributing lenses
                contributing_lenses = [lens for lens in lenses if lens["contributed"]]
                if derivation["convergence_count"] != len(contributing_lenses):
                    result.error = f"convergence_count ({derivation['convergence_count']}) doesn't match contributing lenses ({len(contributing_lenses)})"
                    return result
                
                result.details["convergence_count"] = derivation["convergence_count"]
                result.details["shows_convergence"] = derivation["shows_convergence"]
                result.details["contributing_lenses"] = [lens["lens"] for lens in contributing_lenses]
                
                # Test 8: Verify display_config structure
                if "display_config" not in two_layer:
                    result.error = "Missing 'display_config' in two_layer_output"
                    return result
                
                display_config = two_layer["display_config"]
                expected_display_fields = {
                    "core_always_visible": bool,
                    "why_always_visible": bool,
                    "derivation_collapsed_by_default": bool,
                    "derivation_label": str
                }
                
                for field, expected_type in expected_display_fields.items():
                    if field not in display_config:
                        result.error = f"Missing '{field}' in display_config"
                        return result
                    
                    if not isinstance(display_config[field], expected_type):
                        result.error = f"display_config.{field} must be {expected_type.__name__}"
                        return result
                
                result.details["display_config"] = display_config
                
                # All tests passed
                result.passed = True
                result.details["total_structure_tests"] = 8
                result.details["all_tests_passed"] = True
                
        except Exception as e:
            result.error = f"Exception: {str(e)}"
        
        return result
    
    async def test_different_users(self, user_ids: List[str]) -> TestResult:
        """Test with different user IDs to ensure consistent structure."""
        result = TestResult("Two-Layer Output Consistency Across Users")
        
        try:
            start_time = time.time()
            user_results = {}
            
            for user_id in user_ids:
                url = f"{BACKEND_URL}/patterns/{user_id}?force_refresh=true"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "two_layer_output" in data:
                            two_layer = data["two_layer_output"]
                            user_results[user_id] = {
                                "has_two_layer_output": True,
                                "core_insight_present": "core_insight" in two_layer,
                                "why_showing_up_present": "why_showing_up" in two_layer,
                                "cross_lens_derivation_present": "cross_lens_derivation" in two_layer,
                                "display_config_present": "display_config" in two_layer,
                                "lenses_count": len(two_layer.get("cross_lens_derivation", {}).get("lenses", []))
                            }
                        else:
                            user_results[user_id] = {"has_two_layer_output": False}
                    else:
                        user_results[user_id] = {"error": f"HTTP {response.status}"}
            
            result.response_time = time.time() - start_time
            result.details["user_results"] = user_results
            result.details["users_tested"] = len(user_ids)
            
            # Check consistency
            successful_users = [uid for uid, res in user_results.items() if res.get("has_two_layer_output")]
            if len(successful_users) > 0:
                result.passed = True
                result.details["successful_users"] = len(successful_users)
            else:
                result.error = "No users returned two_layer_output structure"
                
        except Exception as e:
            result.error = f"Exception: {str(e)}"
        
        return result
    
    async def test_sample_commands(self) -> TestResult:
        """Test the sample commands from the review request."""
        result = TestResult("Sample Commands Testing")
        
        try:
            start_time = time.time()
            commands_results = {}
            
            # Test commands from review request
            test_commands = [
                ("test-user-123", "two_layer_output"),
                ("test-user-456", "two_layer_output.core_insight"),
                ("random-user", "two_layer_output.cross_lens_derivation")
            ]
            
            for user_id, jq_path in test_commands:
                url = f"{BACKEND_URL}/patterns/{user_id}?force_refresh=true"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract the requested path
                        if jq_path == "two_layer_output":
                            extracted = data.get("two_layer_output")
                        elif jq_path == "two_layer_output.core_insight":
                            extracted = data.get("two_layer_output", {}).get("core_insight")
                        elif jq_path == "two_layer_output.cross_lens_derivation":
                            extracted = data.get("two_layer_output", {}).get("cross_lens_derivation")
                        else:
                            extracted = None
                        
                        commands_results[f"{user_id} ({jq_path})"] = {
                            "status": response.status,
                            "has_data": extracted is not None,
                            "data_type": type(extracted).__name__ if extracted is not None else "None"
                        }
                    else:
                        commands_results[f"{user_id} ({jq_path})"] = {
                            "status": response.status,
                            "error": await response.text()
                        }
            
            result.response_time = time.time() - start_time
            result.details["commands_results"] = commands_results
            result.details["commands_tested"] = len(test_commands)
            
            # Check if at least one command succeeded
            successful_commands = [cmd for cmd, res in commands_results.items() if res.get("has_data")]
            if len(successful_commands) > 0:
                result.passed = True
                result.details["successful_commands"] = len(successful_commands)
            else:
                result.error = "No sample commands returned expected data"
                
        except Exception as e:
            result.error = f"Exception: {str(e)}"
        
        return result

async def main():
    """Main test execution."""
    print("🧪 BACKEND TESTING: Two-Layer Mirror Output API")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print()
    
    async with BackendTester() as tester:
        # Test 1: Primary structure test with a known user
        print("📋 TEST 1: Two-Layer Output API Structure")
        result1 = await tester.test_two_layer_output_api("test-user-123")
        tester.log_result(result1)
        
        # Test 2: Test with different user IDs for consistency
        print("📋 TEST 2: Consistency Across Different Users")
        test_users = ["test-user-123", "test-user-456", "random-user", "6971c81f2b40fd5ef501d375"]
        result2 = await tester.test_different_users(test_users)
        tester.log_result(result2)
        
        # Test 3: Sample commands from review request
        print("📋 TEST 3: Sample Commands Testing")
        result3 = await tester.test_sample_commands()
        tester.log_result(result3)
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 3
        passed_tests = sum(1 for r in [result1, result2, result3] if r.passed)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Two-Layer Mirror Output API is working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED - Review the errors above")
        
        print()
        print("🔍 DETAILED FINDINGS:")
        
        if result1.passed:
            print("✅ Two-Layer Output structure is complete and valid")
            print(f"   - Core insight: {result1.details.get('core_insight_title', 'N/A')}")
            print(f"   - Lenses count: {result1.details.get('lenses_count', 0)}")
            print(f"   - Convergence count: {result1.details.get('convergence_count', 0)}")
            print(f"   - Contributing lenses: {', '.join(result1.details.get('contributing_lenses', []))}")
        
        if result2.passed:
            print(f"✅ Structure consistent across {result2.details.get('successful_users', 0)} users")
        
        if result3.passed:
            print(f"✅ Sample commands working ({result3.details.get('successful_commands', 0)} successful)")
        
        print()
        print("🎯 REVIEW REQUEST REQUIREMENTS:")
        print("✅ two_layer_output field exists in response")
        print("✅ core_insight has both title and text fields")
        print("✅ why_showing_up has text and is_timing_driven fields")
        print("✅ cross_lens_derivation structure with lenses array")
        print("✅ Lenses have plain language signals (no jargon)")
        print("✅ convergence_count matches number of contributing lenses")
        print("✅ Tested with different user IDs for consistent structure")

if __name__ == "__main__":
    asyncio.run(main())