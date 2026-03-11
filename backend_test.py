#!/usr/bin/env python3
"""
Backend API Testing Suite for Project Mirror
Testing Pattern Timeline API Endpoint
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://human-design-lens.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

class PatternTimelineAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_user_id = TEST_USER_ID
        self.results = []
        
    def log_result(self, test_name: str, passed: bool, details: str = "", response_data: Dict = None):
        """Log test result with details"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not passed and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()

    def test_basic_response_structure(self):
        """Test Case 1: Basic Response Structure"""
        try:
            url = f"{self.base_url}/pattern-timeline/{self.test_user_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                self.log_result(
                    "Basic Response Structure", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "text": response.text}
                )
                return None
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_result(
                    "Basic Response Structure", 
                    False, 
                    f"Invalid JSON response: {e}",
                    {"raw_response": response.text}
                )
                return None
            
            # Check required top-level fields
            required_fields = ["success", "timeline"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Basic Response Structure", 
                    False, 
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return None
            
            # Check success field
            if data.get("success") != True:
                self.log_result(
                    "Basic Response Structure", 
                    False, 
                    f"Success field is not True: {data.get('success')}",
                    data
                )
                return None
            
            # Check timeline object exists
            timeline = data.get("timeline")
            if not isinstance(timeline, dict):
                self.log_result(
                    "Basic Response Structure", 
                    False, 
                    f"Timeline is not an object: {type(timeline)}",
                    data
                )
                return None
            
            # Check timeline required fields
            timeline_required = ["range_label", "weeks", "insights", "narrative_summary", "reflection_prompt"]
            timeline_missing = [field for field in timeline_required if field not in timeline]
            
            if timeline_missing:
                self.log_result(
                    "Basic Response Structure", 
                    False, 
                    f"Timeline missing required fields: {timeline_missing}",
                    data
                )
                return None
            
            self.log_result(
                "Basic Response Structure", 
                True, 
                f"All required fields present. Response time: {response.elapsed.total_seconds():.2f}s",
                {"timeline_keys": list(timeline.keys())}
            )
            return data
            
        except requests.exceptions.RequestException as e:
            self.log_result(
                "Basic Response Structure", 
                False, 
                f"Request failed: {e}"
            )
            return None

    def test_weeks_array_structure(self, timeline_data: Dict):
        """Test Case 2: Weeks Array Structure"""
        if not timeline_data:
            self.log_result("Weeks Array Structure", False, "No timeline data available")
            return
        
        timeline = timeline_data.get("timeline", {})
        weeks = timeline.get("weeks")
        
        if not isinstance(weeks, list):
            self.log_result(
                "Weeks Array Structure", 
                False, 
                f"Weeks is not an array: {type(weeks)}"
            )
            return
        
        if len(weeks) > 8:
            self.log_result(
                "Weeks Array Structure", 
                False, 
                f"Too many weeks returned: {len(weeks)} (expected max 8)"
            )
            return
        
        # Check each week structure
        required_week_fields = ["week_start", "week_end", "top_domain", "secondary_domains", "trend_map"]
        valid_trends = ["growing", "steady", "softening", "emerging"]
        
        for i, week in enumerate(weeks):
            if not isinstance(week, dict):
                self.log_result(
                    "Weeks Array Structure", 
                    False, 
                    f"Week {i} is not an object: {type(week)}"
                )
                return
            
            missing_fields = [field for field in required_week_fields if field not in week]
            if missing_fields:
                self.log_result(
                    "Weeks Array Structure", 
                    False, 
                    f"Week {i} missing fields: {missing_fields}"
                )
                return
            
            # Check trend_map values
            trend_map = week.get("trend_map", {})
            if isinstance(trend_map, dict):
                for domain, trend in trend_map.items():
                    if trend not in valid_trends:
                        self.log_result(
                            "Weeks Array Structure", 
                            False, 
                            f"Week {i} has invalid trend '{trend}' for domain '{domain}'. Valid: {valid_trends}"
                        )
                        return
        
        self.log_result(
            "Weeks Array Structure", 
            True, 
            f"All {len(weeks)} weeks have valid structure with proper trend mappings"
        )

    def test_timeline_insights(self, timeline_data: Dict):
        """Test Case 3: Timeline Insights Structure"""
        if not timeline_data:
            self.log_result("Timeline Insights", False, "No timeline data available")
            return
        
        timeline = timeline_data.get("timeline", {})
        insights = timeline.get("insights")
        
        if not isinstance(insights, dict):
            self.log_result(
                "Timeline Insights", 
                False, 
                f"Insights is not an object: {type(insights)}"
            )
            return
        
        # Check required insight fields (some may be null)
        required_insight_fields = [
            "most_recurring_domain", 
            "strongest_recent_domain", 
            "volatile_domain", 
            "stable_domain", 
            "reemerging_domain"
        ]
        
        missing_fields = [field for field in required_insight_fields if field not in insights]
        if missing_fields:
            self.log_result(
                "Timeline Insights", 
                False, 
                f"Insights missing required fields: {missing_fields}"
            )
            return
        
        # Count non-null insights
        non_null_insights = sum(1 for field in required_insight_fields if insights.get(field) is not None)
        
        self.log_result(
            "Timeline Insights", 
            True, 
            f"All insight fields present. {non_null_insights}/{len(required_insight_fields)} have values"
        )

    def test_narrative_and_reflection(self, timeline_data: Dict):
        """Test Case 4: Narrative and Reflection Content"""
        if not timeline_data:
            self.log_result("Narrative and Reflection", False, "No timeline data available")
            return
        
        timeline = timeline_data.get("timeline", {})
        narrative = timeline.get("narrative_summary")
        reflection = timeline.get("reflection_prompt")
        
        # Check narrative_summary
        if not isinstance(narrative, str) or len(narrative.strip()) == 0:
            self.log_result(
                "Narrative and Reflection", 
                False, 
                f"Narrative summary is not a non-empty string: {type(narrative)}, length: {len(str(narrative))}"
            )
            return
        
        # Check reflection_prompt
        if not isinstance(reflection, str) or len(reflection.strip()) == 0:
            self.log_result(
                "Narrative and Reflection", 
                False, 
                f"Reflection prompt is not a non-empty string: {type(reflection)}, length: {len(str(reflection))}"
            )
            return
        
        self.log_result(
            "Narrative and Reflection", 
            True, 
            f"Narrative: {len(narrative)} chars, Reflection: {len(reflection)} chars"
        )

    def test_partial_flag(self, timeline_data: Dict):
        """Test Case 5: Partial Flag and Weeks Available"""
        if not timeline_data:
            self.log_result("Partial Flag", False, "No timeline data available")
            return
        
        timeline = timeline_data.get("timeline", {})
        is_partial = timeline.get("is_partial")
        weeks_available = timeline.get("weeks_available")
        weeks = timeline.get("weeks", [])
        
        # Check is_partial is boolean
        if not isinstance(is_partial, bool):
            self.log_result(
                "Partial Flag", 
                False, 
                f"is_partial is not boolean: {type(is_partial)}"
            )
            return
        
        # Check weeks_available is number
        if not isinstance(weeks_available, (int, float)):
            self.log_result(
                "Partial Flag", 
                False, 
                f"weeks_available is not a number: {type(weeks_available)}"
            )
            return
        
        # Check weeks_available matches weeks array length
        if weeks_available != len(weeks):
            self.log_result(
                "Partial Flag", 
                False, 
                f"weeks_available ({weeks_available}) doesn't match weeks array length ({len(weeks)})"
            )
            return
        
        self.log_result(
            "Partial Flag", 
            True, 
            f"is_partial: {is_partial}, weeks_available: {weeks_available} (matches array length)"
        )

    def test_caching_behavior(self):
        """Test Case 6: Caching Behavior"""
        try:
            url = f"{self.base_url}/pattern-timeline/{self.test_user_id}"
            
            # First call
            response1 = requests.get(url, timeout=30)
            if response1.status_code != 200:
                self.log_result(
                    "Caching Behavior", 
                    False, 
                    f"First call failed: HTTP {response1.status_code}"
                )
                return
            
            data1 = response1.json()
            first_cached = data1.get("cached", False)
            
            # Wait a moment
            time.sleep(1)
            
            # Second call
            response2 = requests.get(url, timeout=30)
            if response2.status_code != 200:
                self.log_result(
                    "Caching Behavior", 
                    False, 
                    f"Second call failed: HTTP {response2.status_code}"
                )
                return
            
            data2 = response2.json()
            second_cached = data2.get("cached", False)
            
            # Second call should be cached
            if not second_cached:
                self.log_result(
                    "Caching Behavior", 
                    False, 
                    f"Second call not cached. First cached: {first_cached}, Second cached: {second_cached}"
                )
                return
            
            self.log_result(
                "Caching Behavior", 
                True, 
                f"Caching working correctly. First: cached={first_cached}, Second: cached={second_cached}"
            )
            
        except Exception as e:
            self.log_result(
                "Caching Behavior", 
                False, 
                f"Caching test failed: {e}"
            )

    def test_weeks_query_param(self):
        """Test Case 7: Query Parameter - weeks"""
        try:
            # Test with weeks=4
            url = f"{self.base_url}/pattern-timeline/{self.test_user_id}?weeks=4"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                self.log_result(
                    "Weeks Query Parameter", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return
            
            data = response.json()
            timeline = data.get("timeline", {})
            range_label = timeline.get("range_label", "")
            weeks = timeline.get("weeks", [])
            
            # Check range_label mentions 4 weeks
            if "4" not in range_label or "week" not in range_label.lower():
                self.log_result(
                    "Weeks Query Parameter", 
                    False, 
                    f"Range label doesn't mention 4 weeks: '{range_label}'"
                )
                return
            
            # Check at most 4 weeks returned
            if len(weeks) > 4:
                self.log_result(
                    "Weeks Query Parameter", 
                    False, 
                    f"Too many weeks returned: {len(weeks)} (expected max 4)"
                )
                return
            
            self.log_result(
                "Weeks Query Parameter", 
                True, 
                f"weeks=4 parameter working. Range: '{range_label}', Weeks returned: {len(weeks)}"
            )
            
        except Exception as e:
            self.log_result(
                "Weeks Query Parameter", 
                False, 
                f"Query parameter test failed: {e}"
            )

    def run_all_tests(self):
        """Run all Pattern Timeline API tests"""
        print("=" * 60)
        print("PATTERN TIMELINE API ENDPOINT TESTING")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Test User ID: {self.test_user_id}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test 1: Basic Response Structure
        timeline_data = self.test_basic_response_structure()
        
        if timeline_data:
            # Test 2: Weeks Array Structure
            self.test_weeks_array_structure(timeline_data)
            
            # Test 3: Timeline Insights
            self.test_timeline_insights(timeline_data)
            
            # Test 4: Narrative and Reflection
            self.test_narrative_and_reflection(timeline_data)
            
            # Test 5: Partial Flag
            self.test_partial_flag(timeline_data)
        
        # Test 6: Caching Behavior
        self.test_caching_behavior()
        
        # Test 7: Query Parameter
        self.test_weeks_query_param()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.results:
                if not result["passed"]:
                    print(f"❌ {result['test']}: {result['details']}")
            print()
        
        print("DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print("\n" + "=" * 60)
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! Pattern Timeline API is working correctly.")
        else:
            print(f"⚠️  {failed_tests} test(s) failed. Please review the issues above.")
        print("=" * 60)


if __name__ == "__main__":
    tester = PatternTimelineAPITester()
    tester.run_all_tests()