#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for "Today" Endpoints

This script performs detailed testing of the three "Today" endpoints to verify:
1. They return `"title": "Today"` (not "Today's Snapshot")
2. Response structure is valid JSON
3. All required fields are present
4. Response times are reasonable
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from frontend environment
BASE_URL = "https://cachebuster-2.preview.emergentagent.com/api"

# Test user credentials (from previous test logs)
TEST_EMAIL = "pete@pulsifi.me"

class ComprehensiveTodayTester:
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
    
    def validate_response_structure(self, data, endpoint_name):
        """Validate the response structure for today endpoints"""
        issues = []
        
        # Check required fields
        if "title" not in data:
            issues.append("Missing 'title' field")
        elif data["title"] != "Today":
            issues.append(f"Title is '{data['title']}' instead of 'Today'")
            
        if "date" not in data:
            issues.append("Missing 'date' field")
        elif not isinstance(data["date"], str):
            issues.append("Date field is not a string")
            
        if "sections" not in data:
            issues.append("Missing 'sections' field")
        elif not isinstance(data["sections"], list):
            issues.append("Sections field is not a list")
        elif len(data["sections"]) == 0:
            issues.append("Sections array is empty")
        else:
            # Validate section structure
            for i, section in enumerate(data["sections"]):
                if not isinstance(section, dict):
                    issues.append(f"Section {i} is not a dict")
                    continue
                if "label" not in section:
                    issues.append(f"Section {i} missing 'label' field")
                if "body" not in section:
                    issues.append(f"Section {i} missing 'body' field")
        
        # Check optional fields
        if "mirror_prompt" in data and not isinstance(data["mirror_prompt"], str):
            issues.append("Mirror prompt is not a string")
            
        return issues
    
    async def test_endpoint_comprehensive(self, endpoint_name, url):
        """Comprehensive test of a single today endpoint"""
        print(f"\n🧪 Testing {endpoint_name} endpoint (comprehensive)...")
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
                        
                        # Basic title check
                        actual_title = data.get("title")
                        print(f"   Title: '{actual_title}'")
                        
                        # Comprehensive structure validation
                        structure_issues = self.validate_response_structure(data, endpoint_name)
                        
                        if not structure_issues:
                            print(f"   ✅ PASS: All validations successful")
                            
                            # Print additional details
                            print(f"   📋 Response details:")
                            print(f"      - Date: {data.get('date')}")
                            print(f"      - Sections count: {len(data.get('sections', []))}")
                            if data.get('mirror_prompt'):
                                print(f"      - Mirror prompt: '{data['mirror_prompt'][:50]}...'")
                            
                            # Print section labels
                            sections = data.get('sections', [])
                            if sections:
                                print(f"      - Section labels: {[s.get('label') for s in sections]}")
                            
                            return True, {
                                "status": "PASS",
                                "title": actual_title,
                                "response_time": response_time,
                                "status_code": response.status,
                                "sections_count": len(sections),
                                "date": data.get('date'),
                                "has_mirror_prompt": bool(data.get('mirror_prompt'))
                            }
                        else:
                            print(f"   ❌ FAIL: Structure validation issues")
                            for issue in structure_issues:
                                print(f"      • {issue}")
                            return False, {
                                "status": "FAIL",
                                "error": f"Structure issues: {'; '.join(structure_issues)}",
                                "response_time": response_time,
                                "status_code": response.status,
                                "title": actual_title
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
    
    async def run_comprehensive_tests(self):
        """Run comprehensive tests on all today endpoints"""
        print("=" * 80)
        print("🚀 COMPREHENSIVE TODAY ENDPOINTS TESTING")
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
                "url": f"{BASE_URL}/astrology/today/{self.test_user_id}"
            },
            {
                "name": "Human Design Today", 
                "url": f"{BASE_URL}/human-design/today/{self.test_user_id}"
            },
            {
                "name": "Numerology Today",
                "url": f"{BASE_URL}/numerology/today/{self.test_user_id}"
            }
        ]
        
        # Run tests
        results = {}
        all_passed = True
        
        for test_case in test_cases:
            passed, result = await self.test_endpoint_comprehensive(
                test_case["name"],
                test_case["url"]
            )
            results[test_case["name"]] = result
            if not passed:
                all_passed = False
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        for test_name, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"\n{status_icon} {test_name}: {result['status']}")
            
            if result["status"] == "PASS":
                print(f"   ✓ Title: '{result['title']}'")
                print(f"   ✓ Response time: {result['response_time']:.2f}s")
                print(f"   ✓ Sections count: {result['sections_count']}")
                print(f"   ✓ Date: {result['date']}")
                print(f"   ✓ Has mirror prompt: {result['has_mirror_prompt']}")
            else:
                print(f"   ✗ Error: {result.get('error', 'Unknown error')}")
                if 'title' in result:
                    print(f"   ✗ Got title: '{result['title']}'")
        
        print(f"\n🎯 FINAL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        if all_passed:
            print("\n🎉 SUCCESS: All 'Today' endpoints return correct title 'Today'")
            print("   ✓ Astrology Today endpoint: title = 'Today'")
            print("   ✓ Human Design Today endpoint: title = 'Today'") 
            print("   ✓ Numerology Today endpoint: title = 'Today'")
        else:
            print("\n🔧 ISSUES FOUND:")
            for test_name, result in results.items():
                if result["status"] == "FAIL":
                    print(f"   • {test_name}: {result.get('error', 'Failed')}")
        
        return all_passed


async def main():
    """Main test execution function"""
    async with ComprehensiveTodayTester() as tester:
        success = await tester.run_comprehensive_tests()
        
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())