#!/usr/bin/env python3
"""
Backend API Testing for Lifeline Delete and Resonance APIs (Task 67)

Test User:
- User ID: 697f795f1a7a96aa35e283a3
- Birth Year: 1988

Test Cases:
1. Create and Delete Event Flow
2. Resonance API Quality
3. Lifeline Data Refresh After Delete
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://pattern-mirror-2.preview.emergentagent.com/api"

# Test user data
TEST_USER_ID = "697f795f1a7a96aa35e283a3"
TEST_BIRTH_YEAR = 1988

class LifelineAPITester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, status, details):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {test_name}: {details}")
    
    async def create_test_event(self, title="Test Delete Event"):
        """Create a test lifeline event"""
        try:
            payload = {
                "user_id": TEST_USER_ID,
                "title": title,
                "description": "Test event for delete functionality",
                "year": 2020,
                "age": 32,
                "category": "career",
                "emotional_tone": "positive",
                "impact_score": 7,
                "emotional_valence": 7,
                "significance_score": 6
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/lifeline/event",
                json=payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        event_id = data.get("event", {}).get("id")
                        self.log_test("Create Test Event", "PASS", f"Created event with ID: {event_id}")
                        return event_id
                    else:
                        self.log_test("Create Test Event", "FAIL", f"API returned success=false: {data}")
                        return None
                else:
                    text = await response.text()
                    self.log_test("Create Test Event", "FAIL", f"HTTP {response.status}: {text}")
                    return None
                    
        except Exception as e:
            self.log_test("Create Test Event", "FAIL", f"Exception: {str(e)}")
            return None
    
    async def delete_event(self, event_id):
        """Delete a lifeline event"""
        try:
            async with self.session.delete(
                f"{BACKEND_URL}/lifeline/event/{event_id}",
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        deleted_id = data.get("deleted_id")
                        self.log_test("Delete Event", "PASS", f"Successfully deleted event. Response: {data}")
                        return True
                    else:
                        self.log_test("Delete Event", "FAIL", f"API returned success=false: {data}")
                        return False
                else:
                    text = await response.text()
                    self.log_test("Delete Event", "FAIL", f"HTTP {response.status}: {text}")
                    return False
                    
        except Exception as e:
            self.log_test("Delete Event", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def get_event_count(self):
        """Get current event count for user"""
        try:
            async with self.session.get(
                f"{BACKEND_URL}/lifeline/{TEST_USER_ID}",
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        events = data.get("events", [])
                        count = len(events)
                        self.log_test("Get Event Count", "PASS", f"Found {count} events")
                        return count
                    else:
                        self.log_test("Get Event Count", "FAIL", f"API returned success=false: {data}")
                        return None
                else:
                    text = await response.text()
                    self.log_test("Get Event Count", "FAIL", f"HTTP {response.status}: {text}")
                    return None
                    
        except Exception as e:
            self.log_test("Get Event Count", "FAIL", f"Exception: {str(e)}")
            return None
    
    async def get_resonances(self):
        """Get lifeline resonances for the user"""
        try:
            async with self.session.get(
                f"{BACKEND_URL}/lifeline/{TEST_USER_ID}/resonances",
                timeout=15
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.log_test("Get Resonances", "PASS", f"Successfully retrieved resonances")
                        return data
                    else:
                        self.log_test("Get Resonances", "FAIL", f"API returned success=false: {data}")
                        return None
                else:
                    text = await response.text()
                    self.log_test("Get Resonances", "FAIL", f"HTTP {response.status}: {text}")
                    return None
                    
        except Exception as e:
            self.log_test("Get Resonances", "FAIL", f"Exception: {str(e)}")
            return None
    
    async def test_create_and_delete_flow(self):
        """Test 1: Create and Delete Event Flow"""
        print("\n🧪 TEST 1: Create and Delete Event Flow")
        print("=" * 50)
        
        # Create event
        event_id = await self.create_test_event()
        if not event_id:
            return False
        
        # Verify event was created by checking it exists
        initial_count = await self.get_event_count()
        if initial_count is None:
            return False
        
        # Delete event
        delete_success = await self.delete_event(event_id)
        if not delete_success:
            return False
        
        # Verify deletion by checking count decreased
        final_count = await self.get_event_count()
        if final_count is None:
            return False
        
        if final_count < initial_count:
            self.log_test("Delete Verification", "PASS", f"Event count decreased from {initial_count} to {final_count}")
            return True
        else:
            self.log_test("Delete Verification", "FAIL", f"Event count did not decrease: {initial_count} -> {final_count}")
            return False
    
    async def test_resonance_api_quality(self):
        """Test 2: Resonance API Quality"""
        print("\n🧪 TEST 2: Resonance API Quality")
        print("=" * 50)
        
        resonance_data = await self.get_resonances()
        if not resonance_data:
            return False
        
        # Check response structure
        required_fields = ["success", "resonances", "resonance_map", "pattern_summary"]
        missing_fields = []
        for field in required_fields:
            if field not in resonance_data:
                missing_fields.append(field)
        
        if missing_fields:
            self.log_test("Response Structure", "FAIL", f"Missing fields: {missing_fields}")
            return False
        else:
            self.log_test("Response Structure", "PASS", "All required fields present")
        
        # Check birth year filtering (no resonances before 1988)
        resonances = resonance_data.get("resonances", [])
        birth_year = resonance_data.get("birth_year")
        
        if birth_year != TEST_BIRTH_YEAR:
            self.log_test("Birth Year Check", "FAIL", f"Expected birth year {TEST_BIRTH_YEAR}, got {birth_year}")
            return False
        else:
            self.log_test("Birth Year Check", "PASS", f"Birth year correctly identified as {birth_year}")
        
        # Check for events before birth year
        pre_birth_resonances = []
        for resonance in resonances:
            event_year = resonance.get("event_year")
            if event_year and event_year < TEST_BIRTH_YEAR:
                pre_birth_resonances.append(resonance)
        
        if pre_birth_resonances:
            self.log_test("Pre-Birth Filtering", "FAIL", f"Found {len(pre_birth_resonances)} resonances before birth year {TEST_BIRTH_YEAR}")
            return False
        else:
            self.log_test("Pre-Birth Filtering", "PASS", f"No resonances found before birth year {TEST_BIRTH_YEAR}")
        
        # Check for repetitive Saturn Return explanations
        saturn_returns = []
        for resonance in resonances:
            if "saturn" in resonance.get("explanation", "").lower():
                saturn_returns.append(resonance)
        
        if len(saturn_returns) > 3:
            self.log_test("Saturn Return Repetition", "FAIL", f"Found {len(saturn_returns)} Saturn Return explanations (too many)")
        else:
            self.log_test("Saturn Return Repetition", "PASS", f"Found {len(saturn_returns)} Saturn Return explanations (reasonable)")
        
        # Check confidence filtering (min 0.7)
        low_confidence_resonances = []
        for resonance in resonances:
            confidence = resonance.get("confidence", 1.0)
            if confidence < 0.7:
                low_confidence_resonances.append(resonance)
        
        if low_confidence_resonances:
            self.log_test("Confidence Filtering", "FAIL", f"Found {len(low_confidence_resonances)} resonances with confidence < 0.7")
        else:
            self.log_test("Confidence Filtering", "PASS", "All resonances have confidence >= 0.7")
        
        # Log summary
        total_resonances = len(resonances)
        pattern_summary_count = len(resonance_data.get("pattern_summary", []))
        
        self.log_test("Resonance Summary", "PASS", 
                     f"Total resonances: {total_resonances}, Pattern summary items: {pattern_summary_count}")
        
        return True
    
    async def test_lifeline_data_refresh(self):
        """Test 3: Lifeline Data Refresh After Delete"""
        print("\n🧪 TEST 3: Lifeline Data Refresh After Delete")
        print("=" * 50)
        
        # Get initial count
        initial_count = await self.get_event_count()
        if initial_count is None:
            return False
        
        # Create event
        event_id = await self.create_test_event("Refresh Test Event")
        if not event_id:
            return False
        
        # Get count after creation
        after_create_count = await self.get_event_count()
        if after_create_count is None:
            return False
        
        if after_create_count != initial_count + 1:
            self.log_test("Count After Create", "FAIL", 
                         f"Expected {initial_count + 1}, got {after_create_count}")
            return False
        else:
            self.log_test("Count After Create", "PASS", 
                         f"Count increased from {initial_count} to {after_create_count}")
        
        # Delete event
        delete_success = await self.delete_event(event_id)
        if not delete_success:
            return False
        
        # Get final count
        final_count = await self.get_event_count()
        if final_count is None:
            return False
        
        if final_count != initial_count:
            self.log_test("Count After Delete", "FAIL", 
                         f"Expected {initial_count}, got {final_count}")
            return False
        else:
            self.log_test("Count After Delete", "PASS", 
                         f"Count correctly returned to {initial_count}")
        
        return True
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        print(f"🚀 Starting Lifeline API Tests for User {TEST_USER_ID}")
        print(f"📅 Birth Year: {TEST_BIRTH_YEAR}")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        test_results = []
        
        # Test 1: Create and Delete Event Flow
        try:
            result1 = await self.test_create_and_delete_flow()
            test_results.append(("Create and Delete Flow", result1))
        except Exception as e:
            self.log_test("Create and Delete Flow", "FAIL", f"Test exception: {str(e)}")
            test_results.append(("Create and Delete Flow", False))
        
        # Test 2: Resonance API Quality
        try:
            result2 = await self.test_resonance_api_quality()
            test_results.append(("Resonance API Quality", result2))
        except Exception as e:
            self.log_test("Resonance API Quality", "FAIL", f"Test exception: {str(e)}")
            test_results.append(("Resonance API Quality", False))
        
        # Test 3: Lifeline Data Refresh
        try:
            result3 = await self.test_lifeline_data_refresh()
            test_results.append(("Lifeline Data Refresh", result3))
        except Exception as e:
            self.log_test("Lifeline Data Refresh", "FAIL", f"Test exception: {str(e)}")
            test_results.append(("Lifeline Data Refresh", False))
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
            return False

async def main():
    """Main test runner"""
    async with LifelineAPITester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)