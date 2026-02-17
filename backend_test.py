#!/usr/bin/env python3
"""
Backend Testing Suite for Project Mirror
Testing Mirror Chat endpoint as requested in review
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Test Configuration
BASE_URL = "https://api-unifier-1.preview.emergentagent.com/api"
TEST_EMAIL = "pete@pulsifi.me"  # Email from review request
TEST_USER_ID = None  # Will be obtained from login
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
    
    async def test_login_endpoint(self):
        """Test 1: Login endpoint to get valid user ID"""
        test_name = "Login Endpoint"
        
        payload = {"email": TEST_EMAIL}
        
        status, response = await self.make_request("POST", "/users/login", payload)
        
        if status == 200 and response.get("success") and response.get("user"):
            user_id = response["user"]["id"]
            global TEST_USER_ID
            TEST_USER_ID = user_id
            self.log_result(
                test_name,
                "PASS",
                f"✅ Login successful. Got user_id: {user_id}",
                {"user_id": user_id, "email": TEST_EMAIL}
            )
            return user_id
        else:
            self.log_result(
                test_name,
                "FAIL",
                f"❌ Login failed. Status: {status}",
                response
            )
            return None
    
    async def test_mirror_chat_valid_user(self, user_id):
        """Test 2: Mirror chat endpoint with valid user"""
        test_name = "Mirror Chat - Valid User"
        
        payload = {
            "user_id": user_id,
            "message": "Hello, this is a test message",
            "session_id": "test-session-123"
        }
        
        status, response = await self.make_request("POST", "/mirror/chat", payload)
        
        if status != 200:
            self.log_result(test_name, "FAIL", f"❌ HTTP {status} - Expected 200", response)
            return False
        
        # Check for response field
        if "response" not in response:
            self.log_result(test_name, "FAIL", "❌ Missing 'response' field", response)
            return False
        
        # Check that response is not HTML
        response_text = response["response"]
        if "<html>" in response_text.lower() or "<!doctype" in response_text.lower():
            self.log_result(test_name, "FAIL", "❌ Response contains HTML", {"response_preview": response_text[:200]})
            return False
        
        # Check that response is JSON (we already parsed it successfully)
        self.log_result(
            test_name,
            "PASS",
            f"✅ Mirror chat working. Response length: {len(response_text)} chars",
            {
                "status_code": status,
                "has_response_field": True,
                "is_json": True,
                "is_not_html": True,
                "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
            }
        )
        return True
    
    async def test_mirror_chat_invalid_user(self):
        """Test 3: Mirror chat endpoint with invalid user ID"""
        test_name = "Mirror Chat - Invalid User"
        
        payload = {
            "user_id": "invalid-user-id-12345",
            "message": "Hello, this is a test message",
            "session_id": "test-session-456"
        }
        
        status, response = await self.make_request("POST", "/mirror/chat", payload)
        
        # Should return an error status (not 200)
        if status == 200:
            self.log_result(test_name, "FAIL", "❌ Expected error status, got 200", response)
            return False
        
        # Check that error response is not a successful chat response
        if isinstance(response, dict) and "response" in response:
            # This would be a successful chat response, which is wrong for invalid user
            self.log_result(test_name, "FAIL", "❌ Got successful chat response for invalid user", response)
            return False
        
        # Any error response (JSON or HTML) is acceptable for invalid user ID
        # The important thing is that it doesn't return a successful chat response
        self.log_result(
            test_name,
            "PASS",
            f"✅ Proper error handling for invalid user. Status: {status} (error as expected)",
            {"status_code": status, "error_type": "HTML" if "html" in str(response).lower() else "JSON"}
        )
        return True
    
    async def run_all_tests(self):
        """Run all Mirror Chat endpoint tests as requested in review"""
        print("🧪 MIRROR CHAT ENDPOINT TESTING")
        print("=" * 50)
        print(f"Base URL: {BASE_URL}")
        print(f"Test Email: {TEST_EMAIL}")
        print()
        
        # Step 1: Get valid user ID via login
        print("Step 1: Testing login endpoint...")
        user_id = await self.test_login_endpoint()
        
        if not user_id:
            print("❌ Cannot proceed without valid user ID")
            return 0, 3, self.results
        
        # Step 2: Test Mirror chat with valid user
        print("Step 2: Testing Mirror chat with valid user...")
        valid_test_result = await self.test_mirror_chat_valid_user(user_id)
        
        # Step 3: Test Mirror chat with invalid user
        print("Step 3: Testing Mirror chat with invalid user...")
        invalid_test_result = await self.test_mirror_chat_invalid_user()
        
        # Count results
        passed = sum([
            1 if user_id else 0,
            1 if valid_test_result else 0,
            1 if invalid_test_result else 0
        ])
        total = 3
        
        print("=" * 50)
        print(f"📊 TEST SUMMARY: {passed}/{total} PASSED")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Mirror Chat endpoint working correctly!")
        else:
            print(f"⚠️  {total - passed} TESTS FAILED - Issues found with Mirror Chat endpoint")
        
        # Print detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            print(f"   {result['details']}")
        
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