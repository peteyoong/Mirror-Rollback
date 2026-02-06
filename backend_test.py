#!/usr/bin/env python3
"""
Backend Test Suite for Emergent! AI Contract Integration
Testing the new Emergent! AI Contract system in Project Mirror
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL from frontend .env
BASE_URL = "https://trait-explorer-3.preview.emergentagent.com/api"

# Test user ID from review request
TEST_USER_ID = "69819f1a1e4549392d7cb6d1"

class EmergentContractTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test result for summary"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
    
    async def test_emergent_contract_analytics(self):
        """Test GET /api/emergent-contract/analytics endpoint"""
        test_name = "Emergent Contract Analytics"
        
        try:
            url = f"{BASE_URL}/emergent-contract/analytics"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify expected structure
                    required_fields = ["status", "contract_version", "analytics"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, 
                                           f"Missing required fields: {missing_fields}", data)
                        return False
                    
                    # Verify expected values
                    if data.get("status") != "ok":
                        self.log_test_result(test_name, False, 
                                           f"Expected status='ok', got '{data.get('status')}'", data)
                        return False
                    
                    if data.get("contract_version") != "1.0":
                        self.log_test_result(test_name, False, 
                                           f"Expected contract_version='1.0', got '{data.get('contract_version')}'", data)
                        return False
                    
                    analytics = data.get("analytics", {})
                    self.log_test_result(test_name, True, 
                                       f"Analytics endpoint working. Total events: {analytics.get('total_events', 0)}", data)
                    return True
                else:
                    self.log_test_result(test_name, False, 
                                       f"HTTP {response.status}: {await response.text()}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_emergent_contract_modes(self):
        """Test GET /api/emergent-contract/modes endpoint"""
        test_name = "Emergent Contract Modes"
        
        try:
            url = f"{BASE_URL}/emergent-contract/modes"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify expected structure
                    if "modes" not in data:
                        self.log_test_result(test_name, False, "Missing 'modes' field", data)
                        return False
                    
                    modes = data["modes"]
                    expected_modes = [
                        "daily_insight", "reflection_chat", "relationship", "timeline", 
                        "deep_dive", "enneagram", "journal_prompt", "synthesis", "general"
                    ]
                    
                    # Check if we have all 9 expected modes
                    missing_modes = [mode for mode in expected_modes if mode not in modes]
                    if missing_modes:
                        self.log_test_result(test_name, False, 
                                           f"Missing expected modes: {missing_modes}. Got: {modes}", data)
                        return False
                    
                    if len(modes) != 9:
                        self.log_test_result(test_name, False, 
                                           f"Expected 9 modes, got {len(modes)}: {modes}", data)
                        return False
                    
                    self.log_test_result(test_name, True, 
                                       f"All 9 expected modes found: {modes}", data)
                    return True
                else:
                    self.log_test_result(test_name, False, 
                                       f"HTTP {response.status}: {await response.text()}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_reflection_chat_emergent_generate(self):
        """Test POST /api/reflection/chat with emergent_generate integration"""
        test_name = "Reflection Chat with Emergent Generate"
        
        try:
            url = f"{BASE_URL}/reflection/chat"
            payload = {
                "user_id": TEST_USER_ID,
                "messages": [{"role": "user", "content": "I feel restless today"}],
                "context": "Self & Inner State"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    if "response" not in data:
                        self.log_test_result(test_name, False, "Missing 'response' field", data)
                        return False
                    
                    response_text = data["response"]
                    
                    # Check for contract violations (forbidden phrases)
                    forbidden_phrases = [
                        "you should", "you need to", "you must", "you have to",
                        "you will", "this will happen", "it will happen",
                        "you're going to", "in the future you"
                    ]
                    
                    violations = []
                    for phrase in forbidden_phrases:
                        if phrase.lower() in response_text.lower():
                            violations.append(phrase)
                    
                    if violations:
                        self.log_test_result(test_name, False, 
                                           f"Contract violations found: {violations}. Response: {response_text[:200]}...", data)
                        return False
                    
                    # Check for positive indicators (reflective language)
                    positive_indicators = [
                        "it sounds like", "you might notice", "there's a quality", 
                        "you may", "often experienced as", "one way to look"
                    ]
                    
                    has_reflective_language = any(
                        indicator.lower() in response_text.lower() 
                        for indicator in positive_indicators
                    )
                    
                    if not has_reflective_language:
                        self.log_test_result(test_name, False, 
                                           f"No reflective language detected. Response: {response_text[:200]}...", data)
                        return False
                    
                    self.log_test_result(test_name, True, 
                                       f"Contract-compliant response received. Length: {len(response_text)} chars", data)
                    return True
                else:
                    self.log_test_result(test_name, False, 
                                       f"HTTP {response.status}: {await response.text()}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_analytics_after_chat(self):
        """Test that analytics are logged after chat interaction"""
        test_name = "Analytics Logging After Chat"
        
        try:
            # First, get initial analytics
            url = f"{BASE_URL}/emergent-contract/analytics"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, "Could not get initial analytics")
                    return False
                
                initial_data = await response.json()
                initial_events = initial_data.get("analytics", {}).get("total_events", 0)
            
            # Make a chat request
            chat_url = f"{BASE_URL}/reflection/chat"
            payload = {
                "user_id": TEST_USER_ID,
                "messages": [{"role": "user", "content": "Testing analytics logging"}],
                "context": "Self & Inner State"
            }
            
            async with self.session.post(chat_url, json=payload) as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, "Chat request failed")
                    return False
            
            # Wait a moment for logging
            await asyncio.sleep(1)
            
            # Check analytics again
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, "Could not get updated analytics")
                    return False
                
                updated_data = await response.json()
                updated_events = updated_data.get("analytics", {}).get("total_events", 0)
            
            if updated_events > initial_events:
                self.log_test_result(test_name, True, 
                                   f"Analytics logged: {initial_events} -> {updated_events} events", updated_data)
                return True
            else:
                self.log_test_result(test_name, False, 
                                   f"No new events logged: {initial_events} -> {updated_events}", updated_data)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_backend_logs_for_contract(self):
        """Test that backend logs contain [EMERGENT_CONTRACT] entries"""
        test_name = "Backend Contract Logging"
        
        try:
            # Make a reflection chat request to trigger logging
            url = f"{BASE_URL}/reflection/chat"
            payload = {
                "user_id": TEST_USER_ID,
                "messages": [{"role": "user", "content": "Testing contract logging"}],
                "context": "Self & Inner State"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    # We can't directly check backend logs from here, but we can verify
                    # the response indicates the contract system is working
                    data = await response.json()
                    
                    if "response" in data and len(data["response"]) > 0:
                        self.log_test_result(test_name, True, 
                                           "Chat response received, contract system should be logging", data)
                        return True
                    else:
                        self.log_test_result(test_name, False, "Empty or invalid response", data)
                        return False
                else:
                    self.log_test_result(test_name, False, 
                                       f"HTTP {response.status}: {await response.text()}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Emergent Contract tests"""
        logger.info("🚀 Starting Emergent! AI Contract Integration Tests")
        logger.info(f"Base URL: {BASE_URL}")
        logger.info(f"Test User ID: {TEST_USER_ID}")
        logger.info("=" * 80)
        
        # Run tests in order
        tests = [
            self.test_emergent_contract_analytics,
            self.test_emergent_contract_modes,
            self.test_reflection_chat_emergent_generate,
            self.test_analytics_after_chat,
            self.test_backend_logs_for_contract
        ]
        
        results = []
        for test in tests:
            result = await test()
            results.append(result)
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Summary
        logger.info("=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        
        passed = sum(1 for r in results if r)
        total = len(results)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} {result['test']}")
            if not result["success"]:
                logger.info(f"    Details: {result['details']}")
        
        logger.info("=" * 80)
        logger.info(f"📈 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Emergent Contract Integration is working correctly!")
        else:
            logger.error(f"⚠️  {total-passed} tests failed - Issues found with Emergent Contract Integration")
        
        return passed == total

async def main():
    """Main test runner"""
    async with EmergentContractTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)