#!/usr/bin/env python3
"""
Backend Testing Suite for Project Mirror
Testing Mirror Chat lens context functionality and other backend features
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Test Configuration
BASE_URL = "https://pattern-drift-app.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"  # User ID from review request
FALLBACK_USER_ID = "69819f1a1e4549392d7cb6d1"  # Fallback user from test_result.md

class MirrorChatTester:
    def __init__(self):
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, status: str, details: str, response_data: Optional[Dict] = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.results.append(result)
        
        # Print result
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        print(f"   {details}")
        if response_data and status == "FAIL":
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> tuple[int, Dict]:
        """Make HTTP request and return status code and response data"""
        url = f"{BASE_URL}{endpoint}"
        
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
            return 0, {"error": str(e)}
    
    async def test_mirror_chat_endpoint_availability(self):
        """Test 0: Basic endpoint availability"""
        test_name = "Mirror Chat Endpoint Availability"
        
        # Simple test message
        payload = {
            "user_id": TEST_USER_ID,
            "message": "Hello",
            "session_id": "test_basic"
        }
        
        status, response = await self.make_request("POST", "/mirror/chat", payload)
        
        if status == 200 and "response" in response:
            self.log_result(
                test_name,
                "PASS",
                f"✅ Mirror Chat endpoint accessible and responding",
                {"status": status, "has_response": "response" in response}
            )
            return True
        else:
            self.log_result(
                test_name,
                "FAIL",
                f"❌ Mirror Chat endpoint not working. Status: {status}",
                response
            )
            return False
    
    async def test_human_design_lens_context(self):
        """Test 1: Human Design Chat Context - Should know incarnation cross data"""
        test_name = "Human Design Lens Context"
        
        payload = {
            "user_id": TEST_USER_ID,
            "message": "Tell me about my incarnation cross",
            "lens": "human_design",
            "session_id": "test_hd_context"
        }
        
        status, response = await self.make_request("POST", "/mirror/chat", payload)
        
        if status != 200:
            self.log_result(test_name, "FAIL", f"HTTP {status} - Expected 200", response)
            return False
        
        if "response" not in response:
            self.log_result(test_name, "FAIL", "Missing 'response' field in API response", response)
            return False
        
        response_text = response["response"].lower()
        
        # Check for expected incarnation cross data
        expected_phrases = [
            "right angle cross of migration",
            "migration",
            "37", "40",  # Gates
            "incarnation cross"
        ]
        
        found_phrases = []
        missing_phrases = []
        
        for phrase in expected_phrases:
            if phrase in response_text:
                found_phrases.append(phrase)
            else:
                missing_phrases.append(phrase)
        
        if "right angle cross of migration" in response_text or ("migration" in response_text and "cross" in response_text):
            self.log_result(
                test_name, 
                "PASS", 
                f"✅ Response includes incarnation cross context. Found: {found_phrases}",
                {"response_length": len(response["response"]), "found_context": found_phrases}
            )
            return True
        else:
            self.log_result(
                test_name, 
                "FAIL", 
                f"❌ Response missing incarnation cross context. Missing: {missing_phrases}. Response: {response['response'][:200]}...",
                response
            )
            return False
    
    async def test_system_context_verification(self):
        """Test 2: Verify system includes incarnation cross data in context"""
        test_name = "System Context Verification"
        
        # Test with a more direct question about gates
        payload = {
            "user_id": TEST_USER_ID,
            "message": "What are my incarnation cross gates?",
            "lens": "human_design",
            "session_id": "test_context_gates"
        }
        
        status, response = await self.make_request("POST", "/mirror/chat", payload)
        
        if status != 200:
            self.log_result(test_name, "FAIL", f"HTTP {status} - Expected 200", response)
            return False
        
        if "response" not in response:
            self.log_result(test_name, "FAIL", "Missing 'response' field in API response", response)
            return False
        
        response_text = response["response"].lower()
        
        # Check for gate numbers and incarnation cross references
        context_indicators = [
            "37", "40",  # Specific gates
            "gate", "gates",
            "incarnation",
            "cross"
        ]
        
        found_indicators = [indicator for indicator in context_indicators if indicator in response_text]
        
        if len(found_indicators) >= 2:  # Should find at least 2 context indicators
            self.log_result(
                test_name,
                "PASS", 
                f"✅ System context includes incarnation cross data. Found indicators: {found_indicators}",
                {"found_indicators": found_indicators}
            )
            return True
        else:
            self.log_result(
                test_name,
                "FAIL",
                f"❌ System context missing incarnation cross data. Found only: {found_indicators}. Response: {response['response'][:200]}...",
                response
            )
            return False
    
    async def test_enneagram_lens_context(self):
        """Test 3: Enneagram Context - Should know user's type"""
        test_name = "Enneagram Lens Context"
        
        payload = {
            "user_id": TEST_USER_ID,
            "message": "What is my Enneagram type?",
            "lens": "enneagram", 
            "session_id": "test_ennea_context"
        }
        
        status, response = await self.make_request("POST", "/mirror/chat", payload)
        
        if status != 200:
            self.log_result(test_name, "FAIL", f"HTTP {status} - Expected 200", response)
            return False
        
        if "response" not in response:
            self.log_result(test_name, "FAIL", "Missing 'response' field in API response", response)
            return False
        
        response_text = response["response"].lower()
        
        # Check for Enneagram type indicators
        enneagram_indicators = [
            "type", "enneagram",
            "1", "2", "3", "4", "5", "6", "7", "8", "9",  # Type numbers
            "wing", "stress", "growth"
        ]
        
        found_indicators = [indicator for indicator in enneagram_indicators if indicator in response_text]
        
        # Should find type-related content
        if "type" in response_text and len(found_indicators) >= 2:
            self.log_result(
                test_name,
                "PASS",
                f"✅ Enneagram context working. Found indicators: {found_indicators}",
                {"found_indicators": found_indicators}
            )
            return True
        else:
            self.log_result(
                test_name,
                "FAIL", 
                f"❌ Enneagram context missing or incomplete. Found: {found_indicators}. Response: {response['response'][:200]}...",
                response
            )
            return False
    
    async def test_emergent_contract_analytics(self):
        """Test 4: Emergent Contract Analytics endpoint"""
        test_name = "Emergent Contract Analytics"
        
        status, response = await self.make_request("GET", "/emergent-contract/analytics")
        
        if status != 200:
            self.log_result(test_name, "FAIL", f"HTTP {status} - Expected 200", response)
            return False
        
        required_fields = ["status", "contract_version", "analytics"]
        missing_fields = [f for f in required_fields if f not in response]
        
        if missing_fields:
            self.log_result(test_name, "FAIL", f"Missing required fields: {missing_fields}", response)
            return False
        
        analytics = response.get("analytics", {})
        has_events = analytics.get("total_events", 0) >= 0
        
        self.log_result(
            test_name,
            "PASS",
            f"✅ Contract analytics working. Status: {response['status']}, Events: {analytics.get('total_events', 0)}",
            {"analytics_keys": list(analytics.keys())}
        )
        return True
    
    async def run_all_tests(self):
        """Run all Mirror Chat lens context tests"""
        print("🧪 MIRROR CHAT LENS CONTEXT TESTING")
        print("=" * 50)
        print(f"Base URL: {BASE_URL}")
        print(f"Test User ID: {TEST_USER_ID}")
        print()
        
        # Run tests in order
        tests = [
            self.test_mirror_chat_endpoint_availability,
            self.test_human_design_lens_context,
            self.test_system_context_verification,
            self.test_enneagram_lens_context,
            self.test_emergent_contract_analytics
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                self.log_result(test_func.__name__, "ERROR", f"Test failed with exception: {str(e)}")
        
        print("=" * 50)
        print(f"📊 TEST SUMMARY: {passed}/{total} PASSED")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Mirror Chat lens context working correctly!")
        else:
            print(f"⚠️  {total - passed} TESTS FAILED - Issues found with lens context")
        
        return passed, total, self.results

async def main():
    """Main test runner"""
    async with MirrorChatTester() as tester:
        passed, total, results = await tester.run_all_tests()
        
        # Return exit code based on results
        if passed == total:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())