#!/usr/bin/env python3
"""
Backend Testing Script for V3.3 Relationship Insight Engine - Breakthrough Confidence Levels
Testing the specific endpoints and requirements from the review request.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://astrology-today-v3.preview.emergentagent.com/api"

class RelationshipInsightV33Tester:
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
    
    async def test_v33_basic_request(self, user_id: str, other_name: str, context: str):
        """Test basic V3.3 request with all required fields"""
        try:
            url = f"{BACKEND_URL}/relationship-insight/{user_id}"
            params = {
                "other_name": other_name,
                "context": context
            }
            
            print(f"\n🧪 Testing V3.3 Basic Request: {other_name}")
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            async with self.session.get(url, params=params) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    self.log_test("Basic Request - HTTP Status", False, f"Expected 200, got {response.status}")
                    print(f"Response: {response_text}")
                    return None
                
                self.log_test("Basic Request - HTTP Status", True, f"Status: {response.status}")
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    self.log_test("Basic Request - JSON Parse", False, f"Invalid JSON: {e}")
                    return None
                
                self.log_test("Basic Request - JSON Parse", True, "Valid JSON response")
                
                # V3.3 SPECIFIC TESTS
                
                # Test 1: version = "v3.3"
                version = data.get("version")
                self.log_test("V3.3 Version Field", version == "v3.3", f"version: {version}")
                
                # Test 2: breakthrough_confidence (integer 0-3)
                breakthrough_confidence = data.get("breakthrough_confidence")
                is_valid_confidence = isinstance(breakthrough_confidence, int) and 0 <= breakthrough_confidence <= 3
                self.log_test("V3.3 Breakthrough Confidence", is_valid_confidence, 
                             f"breakthrough_confidence: {breakthrough_confidence} (type: {type(breakthrough_confidence)})")
                
                # Test 3: breakthrough_confidence_label (string: "none", "low", "medium", or "high")
                breakthrough_label = data.get("breakthrough_confidence_label")
                valid_labels = ["none", "low", "medium", "high"]
                is_valid_label = breakthrough_label in valid_labels
                self.log_test("V3.3 Breakthrough Confidence Label", is_valid_label,
                             f"breakthrough_confidence_label: {breakthrough_label}")
                
                # Test 4: is_breakthrough (boolean)
                is_breakthrough = data.get("is_breakthrough")
                is_valid_breakthrough = isinstance(is_breakthrough, bool)
                self.log_test("V3.3 Is Breakthrough", is_valid_breakthrough,
                             f"is_breakthrough: {is_breakthrough} (type: {type(is_breakthrough)})")
                
                # Test 5: escalation_level (integer 0-3)
                escalation_level = data.get("escalation_level")
                is_valid_escalation = isinstance(escalation_level, int) and 0 <= escalation_level <= 3
                self.log_test("V3.3 Escalation Level", is_valid_escalation,
                             f"escalation_level: {escalation_level} (type: {type(escalation_level)})")
                
                # Test 6: All content sections present
                required_sections = ["essence", "friction", "tension", "your_shift", "gift", "why_this_connection", "try_this"]
                all_sections_present = True
                missing_sections = []
                
                for section in required_sections:
                    if section not in data:
                        all_sections_present = False
                        missing_sections.append(section)
                
                self.log_test("V3.3 All Content Sections", all_sections_present,
                             f"Missing: {missing_sections}" if missing_sections else "All 7 sections present")
                
                # Test 7: Dynamic object structure
                dynamic = data.get("dynamic", {})
                required_dynamic_fields = ["user_type", "other_type", "user_quality", "other_quality"]
                dynamic_complete = all(field in dynamic for field in required_dynamic_fields)
                self.log_test("V3.3 Dynamic Object", dynamic_complete,
                             f"Dynamic fields: {list(dynamic.keys())}")
                
                # Test 8: breakthrough_debug exists
                breakthrough_debug = data.get("breakthrough_debug")
                has_debug = breakthrough_debug is not None
                self.log_test("V3.3 Breakthrough Debug", has_debug,
                             f"breakthrough_debug present: {has_debug}")
                
                return data
                
        except Exception as e:
            self.log_test("Basic Request - Exception", False, f"Exception: {e}")
            return None
    
    async def test_v33_pattern_detection(self, user_id: str, other_name: str, context: str):
        """Test pattern detection by calling same endpoint multiple times"""
        print(f"\n🧪 Testing V3.3 Pattern Detection: {other_name} (3 calls)")
        
        escalation_levels = []
        
        for i in range(3):
            try:
                url = f"{BACKEND_URL}/relationship-insight/{user_id}"
                params = {
                    "other_name": other_name,
                    "context": context
                }
                
                print(f"   Call {i+1}/3...")
                
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        self.log_test(f"Pattern Detection Call {i+1}", False, f"HTTP {response.status}")
                        continue
                    
                    data = await response.json()
                    escalation_level = data.get("escalation_level", 0)
                    escalation_levels.append(escalation_level)
                    
                    print(f"   Call {i+1}: escalation_level = {escalation_level}")
                    
                    # Small delay between calls
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                self.log_test(f"Pattern Detection Call {i+1}", False, f"Exception: {e}")
                continue
        
        # Check if escalation increased on 3rd+ call
        if len(escalation_levels) >= 3:
            third_call_escalation = escalation_levels[2]
            escalation_increased = third_call_escalation > escalation_levels[0]
            
            self.log_test("Pattern Detection - Escalation Increase", escalation_increased,
                         f"Escalation levels: {escalation_levels}")
        else:
            self.log_test("Pattern Detection - Escalation Increase", False, "Not enough successful calls")
        
        return escalation_levels
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
        
    async def check_content_quality(self, data: Dict[str, Any], test_name: str):
        """Check content quality requirements for V3.3"""
        
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
    
    async def run_all_tests(self):
        """Run all V3.3 tests specified in the review request"""
        
        print("🎯 TESTING V3.3 RELATIONSHIP INSIGHT ENGINE - BREAKTHROUGH CONFIDENCE LEVELS")
        print("=" * 80)
        
        # Test user from review request
        user_id = "697f0c6abf35c0528ff06954"
        
        # Test Case 1: Basic Request Test
        print("\n📋 TEST CASE 1: BASIC REQUEST TEST")
        print("-" * 50)
        basic_result = await self.test_v33_basic_request(
            user_id, 
            "TestPerson", 
            "Direct communicator"
        )
        
        if basic_result:
            await self.check_content_quality(basic_result, "Basic Request")
        
        # Test Case 2: Multiple Requests Test (Pattern Detection)
        print("\n📋 TEST CASE 2: MULTIPLE REQUESTS TEST (PATTERN DETECTION)")
        print("-" * 50)
        await self.test_v33_pattern_detection(
            user_id,
            "RecurringTest",
            "Consistent pattern behavior"
        )
        
        # Test Case 3: Response Structure Validation (additional test)
        print("\n📋 TEST CASE 3: RESPONSE STRUCTURE VALIDATION")
        print("-" * 50)
        structure_result = await self.test_v33_basic_request(
            user_id,
            "StructureTest", 
            "Testing response structure"
        )
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 V3.3 TEST SUMMARY")
        print("=" * 80)
        
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
        
        # Check for critical V3.3 features
        critical_tests = [
            "V3.3 Version Field",
            "V3.3 Breakthrough Confidence", 
            "V3.3 Breakthrough Confidence Label",
            "V3.3 Is Breakthrough",
            "V3.3 Escalation Level",
            "V3.3 All Content Sections",
            "V3.3 Dynamic Object",
            "V3.3 Breakthrough Debug"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result["test"] in critical_tests and result["passed"])
        critical_total = len([r for r in self.test_results if r["test"] in critical_tests])
        
        print(f"\n🔥 CRITICAL V3.3 FEATURES: {critical_passed}/{critical_total} PASSED")
        
        if critical_passed == critical_total:
            print("✅ ALL CRITICAL V3.3 FEATURES WORKING!")
        else:
            print("❌ SOME CRITICAL V3.3 FEATURES FAILED!")
        
        return failed_tests == 0


async def main():
    """Main test runner"""
    async with RelationshipInsightV33Tester() as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 ALL V3.3 TESTS PASSED! Breakthrough Confidence Levels are working correctly.")
            sys.exit(0)
        else:
            print("\n💥 SOME V3.3 TESTS FAILED! Check the details above.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())