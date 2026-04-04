#!/usr/bin/env python3
"""
Backend Testing Script for V2.0 Relationship Insight Engine
Testing the specific endpoints and requirements from the review request.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://insight-engine-126.preview.emergentagent.com/api"

class RelationshipInsightTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    async def test_relationship_insight_endpoint(self, user_id: str, other_name: str, context: str, test_name: str):
        """Test a specific relationship insight endpoint call"""
        try:
            url = f"{BACKEND_URL}/relationship-insight/{user_id}"
            params = {
                "other_name": other_name,
                "context": context
            }
            
            print(f"\n🧪 Testing: {test_name}")
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            async with self.session.get(url, params=params) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    self.log_test(f"{test_name} - HTTP Status", False, f"Expected 200, got {response.status}")
                    print(f"Response: {response_text}")
                    return None
                
                self.log_test(f"{test_name} - HTTP Status", True, f"Status: {response.status}")
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    self.log_test(f"{test_name} - JSON Parse", False, f"Invalid JSON: {e}")
                    return None
                
                self.log_test(f"{test_name} - JSON Parse", True, "Valid JSON response")
                
                # Test 1: success: true
                success = data.get("success")
                self.log_test(f"{test_name} - Success Field", success is True, f"success: {success}")
                
                # Test 2: version: v2.0
                version = data.get("version")
                self.log_test(f"{test_name} - Version Field", version == "v2.0", f"version: {version}")
                
                # Test 3: All 6 sections present
                required_sections = ["essence", "friction", "tension", "your_shift", "gift", "try_this"]
                all_sections_present = True
                missing_sections = []
                
                for section in required_sections:
                    if section not in data:
                        all_sections_present = False
                        missing_sections.append(section)
                
                self.log_test(f"{test_name} - All 6 Sections Present", all_sections_present, 
                             f"Missing: {missing_sections}" if missing_sections else "All sections present")
                
                # Test 4: Dynamic metadata shows user_quality and other_quality
                dynamic = data.get("dynamic", {})
                has_user_quality = "user_quality" in dynamic
                has_other_quality = "other_quality" in dynamic
                
                self.log_test(f"{test_name} - Dynamic Metadata", has_user_quality and has_other_quality,
                             f"user_quality: {dynamic.get('user_quality')}, other_quality: {dynamic.get('other_quality')}")
                
                # Quality checks
                await self.check_content_quality(data, test_name)
                
                return data
                
        except Exception as e:
            self.log_test(f"{test_name} - Request", False, f"Exception: {e}")
            return None
    
    async def check_content_quality(self, data: Dict[str, Any], test_name: str):
        """Check content quality requirements"""
        
        # Check YOUR SHIFT is actionable and centered on USER
        your_shift = data.get("your_shift", "")
        
        # Should not suggest what other person should do
        forbidden_other_phrases = [
            "they should", "they need to", "tell them", "ask them to", "make them"
        ]
        
        has_forbidden_other = any(phrase in your_shift.lower() for phrase in forbidden_other_phrases)
        self.log_test(f"{test_name} - YOUR SHIFT User-Centered", not has_forbidden_other,
                     f"No suggestions about other person: {not has_forbidden_other}")
        
        # Check GIFT explains why person matters
        gift = data.get("gift", "")
        gift_has_meaning = len(gift) > 20 and ("matter" in gift.lower() or "bring" in gift.lower() or "show" in gift.lower())
        self.log_test(f"{test_name} - GIFT Meaningful", gift_has_meaning,
                     f"Gift explains value: {gift[:100]}...")
        
        # Check TRY THIS is behavioral action
        try_this = data.get("try_this", "")
        is_behavioral = len(try_this) > 10 and not any(phrase in try_this.lower() for phrase in ["therapy", "counseling", "meditate"])
        self.log_test(f"{test_name} - TRY THIS Behavioral", is_behavioral,
                     f"Behavioral action: {try_this[:100]}...")
        
        # Check for forbidden generic phrases
        all_content = f"{data.get('essence', '')} {data.get('friction', '')} {data.get('tension', '')} {your_shift} {gift} {try_this}"
        
        forbidden_generic = ["hold space", "be present"]
        has_generic = any(phrase in all_content.lower() for phrase in forbidden_generic)
        self.log_test(f"{test_name} - No Generic Phrases", not has_generic,
                     f"No 'hold space' or 'be present': {not has_generic}")
        
        # Check for overly long explanatory sentences (should be direct)
        sentences = all_content.split('.')
        long_sentences = [s for s in sentences if len(s.strip()) > 150]
        has_long_sentences = len(long_sentences) > 2
        self.log_test(f"{test_name} - Direct Language", not has_long_sentences,
                     f"Not overly explanatory: {not has_long_sentences}")
    
    async def run_all_tests(self):
        """Run all the tests specified in the review request"""
        
        print("🎯 TESTING V2.0 RELATIONSHIP INSIGHT ENGINE")
        print("=" * 60)
        
        # Test cases from review request
        test_cases = [
            {
                "user_id": "697f0c6abf35c0528ff06954",
                "other_name": "Mel",
                "context": "She senses the room. Attunes before acting.",
                "test_name": "Mel - Attunement Type"
            },
            {
                "user_id": "697f0c6abf35c0528ff06954", 
                "other_name": "Jake",
                "context": "He carries momentum forward. Doesn't stop.",
                "test_name": "Jake - Momentum Type"
            },
            {
                "user_id": "697f0c6abf35c0528ff06954",
                "other_name": "Sarah", 
                "context": "She holds what she feels. Contained. Protected.",
                "test_name": "Sarah - Container Type"
            }
        ]
        
        for test_case in test_cases:
            await self.test_relationship_insight_endpoint(
                test_case["user_id"],
                test_case["other_name"], 
                test_case["context"],
                test_case["test_name"]
            )
            print()  # Add spacing between tests
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return failed_tests == 0


async def main():
    """Main test runner"""
    async with RelationshipInsightTester() as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 ALL TESTS PASSED! V2.0 Relationship Insight Engine is working correctly.")
            sys.exit(0)
        else:
            print("\n💥 SOME TESTS FAILED! Check the details above.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())