#!/usr/bin/env python3
"""
Backend Testing Script for "Today" Endpoints Title Verification

This script tests the three "Today" endpoints to verify they return 
`"title": "Today"` instead of `"title": "Today's Snapshot"`.

Test Requirements:
1. GET /api/astrology/today/{user_id} - should return "title": "Today"
2. GET /api/human-design/today/{user_id} - should return "title": "Today"  
3. GET /api/numerology/today/{user_id} - should return "title": "Today"
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from frontend environment
BASE_URL = "https://mirror-ui-refine.preview.emergentagent.com/api"

# Test user credentials (from previous test logs)
TEST_EMAIL = "pete@pulsifi.me"

class TodayEndpointTester:
    def __init__(self):
        self.session = None
        self.test_user_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_test_user_id(self):
        """Get a test user ID by logging in with known credentials"""
        print(f"🔍 Getting test user ID via login...")
        
        login_url = f"{BASE_URL}/users/login"
        login_payload = {"email": TEST_EMAIL}
        
        try:
            async with self.session.post(login_url, json=login_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    user_id = data.get("user", {}).get("id")
                    if user_id:
                        print(f"✅ Successfully retrieved test user ID: {user_id}")
                        return user_id
                    else:
                        print(f"❌ Login successful but no user ID found in response")
                        return None
                else:
                    print(f"❌ Login failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Login request failed: {e}")
            return None
    
    async def test_endpoint(self, endpoint_name, url, expected_title="Today"):
        """Test a single today endpoint for correct title"""
        print(f"\n🧪 Testing {endpoint_name} endpoint...")
        print(f"   URL: {url}")
        
        try:
            start_time = datetime.now()
            async with self.session.get(url) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                print(f"   Status: {response.status}")
                print(f"   Response time: {response_time:.2f}s")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        actual_title = data.get("title")
                        
                        print(f"   Expected title: '{expected_title}'")
                        print(f"   Actual title: '{actual_title}'")
                        
                        if actual_title == expected_title:
                            print(f"   ✅ PASS: Title matches expected value")
                            return True, {
                                "status": "PASS",
                                "expected_title": expected_title,
                                "actual_title": actual_title,
                                "response_time": response_time,
                                "status_code": response.status
                            }
                        else:
                            print(f"   ❌ FAIL: Title mismatch")
                            return False, {
                                "status": "FAIL",
                                "expected_title": expected_title,
                                "actual_title": actual_title,
                                "response_time": response_time,
                                "status_code": response.status,
                                "error": f"Expected '{expected_title}' but got '{actual_title}'"
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"   ❌ FAIL: Invalid JSON response")
                        response_text = await response.text()
                        print(f"   Response text: {response_text[:200]}...")
                        return False, {
                            "status": "FAIL",
                            "error": f"JSON decode error: {e}",
                            "response_time": response_time,
                            "status_code": response.status
                        }
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ FAIL: HTTP {response.status}")
                    print(f"   Error: {error_text[:200]}...")
                    return False, {
                        "status": "FAIL",
                        "error": f"HTTP {response.status}: {error_text[:100]}",
                        "response_time": response_time,
                        "status_code": response.status
                    }
                    
        except Exception as e:
            print(f"   ❌ FAIL: Request exception")
            print(f"   Exception: {e}")
            return False, {
                "status": "FAIL",
                "error": f"Request exception: {e}"
            }
    
    async def run_all_tests(self):
        """Run all today endpoint tests"""
        print("=" * 80)
        print("🚀 STARTING TODAY ENDPOINTS TITLE VERIFICATION TESTS")
        print("=" * 80)
        
        # Get test user ID
        self.test_user_id = await self.get_test_user_id()
        if not self.test_user_id:
            print("\n❌ CRITICAL: Cannot proceed without test user ID")
            return False
        
        # Define test endpoints
        test_cases = [
            {
                "name": "Astrology Today",
                "url": f"{BASE_URL}/astrology/today/{self.test_user_id}",
                "expected_title": "Today"
            },
            {
                "name": "Human Design Today", 
                "url": f"{BASE_URL}/human-design/today/{self.test_user_id}",
                "expected_title": "Today"
            },
            {
                "name": "Numerology Today",
                "url": f"{BASE_URL}/numerology/today/{self.test_user_id}",
                "expected_title": "Today"
            }
        ]
        
        # Run tests
        results = {}
        all_passed = True
        
        for test_case in test_cases:
            passed, result = await self.test_endpoint(
                test_case["name"],
                test_case["url"], 
                test_case["expected_title"]
            )
            results[test_case["name"]] = result
            if not passed:
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for test_name, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result['status']}")
            
            if result["status"] == "PASS":
                print(f"   Title: '{result['actual_title']}' ✓")
                print(f"   Response time: {result['response_time']:.2f}s")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
                if 'actual_title' in result:
                    print(f"   Got title: '{result['actual_title']}'")
        
        print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        if not all_passed:
            print("\n🔧 ISSUES FOUND:")
            for test_name, result in results.items():
                if result["status"] == "FAIL":
                    print(f"   • {test_name}: {result.get('error', 'Failed')}")
        
        return all_passed


async def main():
    """Main test execution function"""
    async with TodayEndpointTester() as tester:
        success = await tester.run_all_tests()
        
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())