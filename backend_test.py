#!/usr/bin/env python3
"""
Backend Test Suite for Emergent! AI Contract Integration
Tests the refactored endpoints after contract integration.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Base URL from frontend/.env
BASE_URL = "https://trait-explorer-3.preview.emergentagent.com/api"

# Test user ID (from test_result.md)
TEST_USER_ID = "69819f1a1e4549392d7cb6d1"

class EmergentContractTester:
    def __init__(self):
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            print(f"   Error: {details.get('error', 'Unknown error')}")
        elif details.get('response_summary'):
            print(f"   {details['response_summary']}")
    
    async def test_contract_analytics_initial(self) -> Dict[str, Any]:
        """Test GET /api/emergent-contract/analytics - Initial state"""
        try:
            async with self.session.get(f"{BASE_URL}/emergent-contract/analytics") as resp:
                if resp.status != 200:
                    self.log_result("Contract Analytics (Initial)", False, {
                        "error": f"HTTP {resp.status}",
                        "response": await resp.text()
                    })
                    return {}
                
                data = await resp.json()
                
                # Check required fields
                required_fields = ["status", "contract_version", "analytics"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    self.log_result("Contract Analytics (Initial)", False, {
                        "error": f"Missing fields: {missing_fields}",
                        "response": data
                    })
                    return {}
                
                # Check for new analytics fields
                analytics = data.get("analytics", {})
                has_block_regen_rate = "block_regen_success_rate" in analytics
                has_top_issue_codes = "top_issue_codes_by_mode" in analytics
                
                self.log_result("Contract Analytics (Initial)", True, {
                    "status": data["status"],
                    "contract_version": data["contract_version"],
                    "total_events": analytics.get("total_events", 0),
                    "has_block_regen_success_rate": has_block_regen_rate,
                    "has_top_issue_codes_by_mode": has_top_issue_codes,
                    "response_summary": f"Status: {data['status']}, Events: {analytics.get('total_events', 0)}"
                })
                
                return data
                
        except Exception as e:
            self.log_result("Contract Analytics (Initial)", False, {
                "error": str(e)
            })
            return {}
    
    async def test_red_team_tests(self) -> Dict[str, Any]:
        """Test GET /api/emergent-contract/red-team - NEW endpoint"""
        try:
            print("Running red team tests (this may take 30-60 seconds)...")
            start_time = time.time()
            
            async with self.session.get(f"{BASE_URL}/emergent-contract/red-team") as resp:
                if resp.status != 200:
                    self.log_result("Red Team Tests", False, {
                        "error": f"HTTP {resp.status}",
                        "response": await resp.text()
                    })
                    return {}
                
                data = await resp.json()
                elapsed = time.time() - start_time
                
                # Check structure
                required_fields = ["timestamp", "tests", "all_passed"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    self.log_result("Red Team Tests", False, {
                        "error": f"Missing fields: {missing_fields}",
                        "response": data
                    })
                    return {}
                
                # Check individual tests
                tests = data.get("tests", {})
                expected_tests = ["timeline_prediction", "relationship_certainty", "work_certainty"]
                
                test_results = {}
                for test_name in expected_tests:
                    if test_name in tests:
                        test_data = tests[test_name]
                        test_results[test_name] = {
                            "passed": test_data.get("passed", False),
                            "input": test_data.get("input", ""),
                            "response_preview": test_data.get("response", "")[:100] + "..." if test_data.get("response") else ""
                        }
                
                all_passed = data.get("all_passed", False)
                
                self.log_result("Red Team Tests", all_passed, {
                    "all_passed": all_passed,
                    "test_count": len(tests),
                    "individual_results": test_results,
                    "elapsed_seconds": round(elapsed, 2),
                    "response_summary": f"All passed: {all_passed}, Tests: {len(tests)}, Time: {elapsed:.1f}s"
                })
                
                return data
                
        except Exception as e:
            self.log_result("Red Team Tests", False, {
                "error": str(e)
            })
            return {}
    
    async def test_reflection_chat_contract_compliance(self) -> Dict[str, Any]:
        """Test POST /api/reflection/chat with contract compliance check"""
        try:
            payload = {
                "user_id": TEST_USER_ID,
                "messages": [{"role": "user", "content": "I'm feeling anxious about work"}],
                "context": "Work & Career"
            }
            
            async with self.session.post(
                f"{BASE_URL}/reflection/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    self.log_result("Reflection Chat Contract Compliance", False, {
                        "error": f"HTTP {resp.status}",
                        "response": await resp.text()
                    })
                    return {}
                
                data = await resp.json()
                
                # Check response structure
                if "response" not in data:
                    self.log_result("Reflection Chat Contract Compliance", False, {
                        "error": "Missing 'response' field",
                        "response": data
                    })
                    return {}
                
                response_text = data["response"]
                
                # Check for forbidden phrases
                forbidden_phrases = ["you should", "you will", "you are a", "you must", "you need to"]
                violations = []
                
                for phrase in forbidden_phrases:
                    if phrase.lower() in response_text.lower():
                        violations.append(phrase)
                
                # Check for contract-compliant language
                compliant_phrases = ["you may", "you might", "it sounds like", "you could", "one way"]
                found_compliant = []
                
                for phrase in compliant_phrases:
                    if phrase.lower() in response_text.lower():
                        found_compliant.append(phrase)
                
                is_compliant = len(violations) == 0
                
                self.log_result("Reflection Chat Contract Compliance", is_compliant, {
                    "response_length": len(response_text),
                    "violations_found": violations,
                    "compliant_phrases_found": found_compliant,
                    "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "response_summary": f"Compliant: {is_compliant}, Violations: {len(violations)}"
                })
                
                return data
                
        except Exception as e:
            self.log_result("Reflection Chat Contract Compliance", False, {
                "error": str(e)
            })
            return {}
    
    async def test_contract_analytics_after_chat(self) -> Dict[str, Any]:
        """Test GET /api/emergent-contract/analytics after chat to verify event logging"""
        try:
            async with self.session.get(f"{BASE_URL}/emergent-contract/analytics") as resp:
                if resp.status != 200:
                    self.log_result("Contract Analytics (After Chat)", False, {
                        "error": f"HTTP {resp.status}",
                        "response": await resp.text()
                    })
                    return {}
                
                data = await resp.json()
                analytics = data.get("analytics", {})
                
                # Check if events were logged
                total_events = analytics.get("total_events", 0)
                violation_rate = analytics.get("violation_rate", 0)
                
                # Check for new required fields
                has_block_regen_rate = "block_regen_success_rate" in analytics
                has_top_issue_codes = "top_issue_codes_by_mode" in analytics
                
                success = total_events > 0 and has_block_regen_rate and has_top_issue_codes
                
                self.log_result("Contract Analytics (After Chat)", success, {
                    "total_events": total_events,
                    "violation_rate": violation_rate,
                    "has_block_regen_success_rate": has_block_regen_rate,
                    "has_top_issue_codes_by_mode": has_top_issue_codes,
                    "block_regen_success_rate": analytics.get("block_regen_success_rate"),
                    "top_issue_codes_by_mode": analytics.get("top_issue_codes_by_mode", {}),
                    "response_summary": f"Events logged: {total_events}, Violation rate: {violation_rate:.2%}"
                })
                
                return data
                
        except Exception as e:
            self.log_result("Contract Analytics (After Chat)", False, {
                "error": str(e)
            })
            return {}
    
    async def test_contract_modes_endpoint(self) -> Dict[str, Any]:
        """Test GET /api/emergent-contract/modes endpoint"""
        try:
            async with self.session.get(f"{BASE_URL}/emergent-contract/modes") as resp:
                if resp.status != 200:
                    self.log_result("Contract Modes Endpoint", False, {
                        "error": f"HTTP {resp.status}",
                        "response": await resp.text()
                    })
                    return {}
                
                data = await resp.json()
                
                # Check required fields
                if "modes" not in data:
                    self.log_result("Contract Modes Endpoint", False, {
                        "error": "Missing 'modes' field",
                        "response": data
                    })
                    return {}
                
                modes = data["modes"]
                expected_modes = [
                    "daily_insight", "reflection_chat", "relationship", "timeline",
                    "deep_dive", "enneagram", "journal_prompt", "synthesis", "general"
                ]
                
                missing_modes = [m for m in expected_modes if m not in modes]
                
                success = len(missing_modes) == 0
                
                self.log_result("Contract Modes Endpoint", success, {
                    "modes_count": len(modes),
                    "modes_found": modes,
                    "missing_modes": missing_modes,
                    "response_summary": f"Modes: {len(modes)}, Missing: {len(missing_modes)}"
                })
                
                return data
                
        except Exception as e:
            self.log_result("Contract Modes Endpoint", False, {
                "error": str(e)
            })
            return {}
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting Emergent! AI Contract Integration Tests")
        print(f"Base URL: {BASE_URL}")
        print(f"Test User ID: {TEST_USER_ID}")
        print("=" * 60)
        
        # Test 1: Initial analytics state
        await self.test_contract_analytics_initial()
        
        # Test 2: Contract modes endpoint
        await self.test_contract_modes_endpoint()
        
        # Test 3: Red team tests (NEW endpoint)
        await self.test_red_team_tests()
        
        # Test 4: Reflection chat with contract compliance
        await self.test_reflection_chat_contract_compliance()
        
        # Test 5: Analytics after chat (verify event logging)
        await self.test_contract_analytics_after_chat()
        
        # Summary
        print("=" * 60)
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details'].get('error', 'Unknown error')}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests,
            "results": self.results
        }

async def main():
    """Main test runner"""
    async with EmergentContractTester() as tester:
        return await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())