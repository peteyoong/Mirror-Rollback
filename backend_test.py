#!/usr/bin/env python3
"""
Backend API Testing for Weekly Pattern Synthesis Endpoint
Testing GET /api/weekly-patterns/{user_id}
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://mirror-lens-app.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"
TIMEOUT = 30

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {test_name}: {status}")
    if details:
        print(f"    {details}")

class WeeklyPatternSynthesisTester:
    """Test suite for Weekly Pattern Synthesis API endpoint."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.test_user_id = TEST_USER_ID
        self.results = []
        self.first_response_data = None
        self.first_response_time = 0
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_basic_response_structure(self) -> bool:
        """Test 1: Basic Response Structure"""
        try:
            url = f"{self.base_url}/weekly-patterns/{self.test_user_id}"
            
            start_time = time.time()
            response = requests.get(url, timeout=TIMEOUT)
            self.first_response_time = time.time() - start_time
            
            # Check HTTP status
            if response.status_code != 200:
                self.log_result(
                    "Basic Response Structure - HTTP Status",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text[:200]}"
                )
                return False
            
            # Parse JSON
            try:
                data = response.json()
                self.first_response_data = data
            except json.JSONDecodeError as e:
                self.log_result(
                    "Basic Response Structure - JSON Parse",
                    False,
                    f"Invalid JSON: {e}"
                )
                return False
            
            # Check success field
            if not data.get("success"):
                self.log_result(
                    "Basic Response Structure - Success Flag",
                    False,
                    f"success: {data.get('success')}, expected True"
                )
                return False
            
            # Check weekly_summary exists
            weekly_summary = data.get("weekly_summary")
            if not isinstance(weekly_summary, dict):
                self.log_result(
                    "Basic Response Structure - Weekly Summary",
                    False,
                    f"Expected dict, got {type(weekly_summary)}"
                )
                return False
            
            # Check week dates
            week_start = weekly_summary.get("week_start")
            week_end = weekly_summary.get("week_end")
            
            if not week_start or not week_end:
                self.log_result(
                    "Basic Response Structure - Week Dates",
                    False,
                    f"Missing dates - start: {week_start}, end: {week_end}"
                )
                return False
            
            self.log_result(
                "Basic Response Structure",
                True,
                f"HTTP 200, success: true, week: {week_start} to {week_end}, response time: {self.first_response_time:.2f}s"
            )
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_result(
                "Basic Response Structure",
                False,
                f"Request failed: {e}"
            )
            return False
    
    def test_top_domains(self) -> bool:
        """Test 2: Top Domains Structure"""
        if not self.first_response_data:
            self.log_result("Top Domains", False, "No response data available")
            return False
        
        try:
            weekly_summary = self.first_response_data.get("weekly_summary", {})
            top_domains = weekly_summary.get("top_domains", [])
            
            # Check type
            if not isinstance(top_domains, list):
                self.log_result(
                    "Top Domains - Type",
                    False,
                    f"Expected list, got {type(top_domains)}"
                )
                return False
            
            # Check count (up to 3)
            if len(top_domains) > 3:
                self.log_result(
                    "Top Domains - Count",
                    False,
                    f"Expected max 3, got {len(top_domains)}"
                )
                return False
            
            # Check structure of each domain
            required_fields = ["domain", "domain_id", "trend", "weekly_score", "days_present", "timing_amplified", "evidence_summary"]
            valid_trends = ["rising", "steady", "softening", "emerging"]
            
            for i, domain in enumerate(top_domains):
                if not isinstance(domain, dict):
                    self.log_result(
                        f"Top Domains - Domain {i+1} Type",
                        False,
                        f"Expected dict, got {type(domain)}"
                    )
                    return False
                
                # Check required fields
                missing_fields = [field for field in required_fields if field not in domain]
                if missing_fields:
                    self.log_result(
                        f"Top Domains - Domain {i+1} Fields",
                        False,
                        f"Missing fields: {missing_fields}"
                    )
                    return False
                
                # Check trend value
                trend = domain.get("trend")
                if trend not in valid_trends:
                    self.log_result(
                        f"Top Domains - Domain {i+1} Trend",
                        False,
                        f"Invalid trend '{trend}', expected one of {valid_trends}"
                    )
                    return False
            
            self.log_result(
                "Top Domains",
                True,
                f"{len(top_domains)} domains with all required fields and valid trends"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Top Domains",
                False,
                f"Error checking top domains: {e}"
            )
            return False
    
    def test_all_domains(self) -> bool:
        """Test 3: All Domains Structure"""
        if not self.first_response_data:
            self.log_result("All Domains", False, "No response data available")
            return False
        
        try:
            weekly_summary = self.first_response_data.get("weekly_summary", {})
            all_domains = weekly_summary.get("all_domains", [])
            
            # Check type
            if not isinstance(all_domains, list):
                self.log_result(
                    "All Domains - Type",
                    False,
                    f"Expected list, got {type(all_domains)}"
                )
                return False
            
            # Check count (should be 7 pattern domains)
            if len(all_domains) != 7:
                self.log_result(
                    "All Domains - Count",
                    False,
                    f"Expected 7 pattern domains, got {len(all_domains)}"
                )
                return False
            
            # Check structure of each domain
            required_fields = ["domain", "domain_id", "trend", "weekly_score", "days_present"]
            valid_trends = ["rising", "steady", "softening", "emerging"]
            
            for i, domain in enumerate(all_domains):
                if not isinstance(domain, dict):
                    self.log_result(
                        f"All Domains - Domain {i+1} Type",
                        False,
                        f"Expected dict, got {type(domain)}"
                    )
                    return False
                
                # Check required fields
                missing_fields = [field for field in required_fields if field not in domain]
                if missing_fields:
                    self.log_result(
                        f"All Domains - Domain {i+1} Fields",
                        False,
                        f"Missing fields: {missing_fields}"
                    )
                    return False
                
                # Check trend value
                trend = domain.get("trend")
                if trend not in valid_trends:
                    self.log_result(
                        f"All Domains - Domain {i+1} Trend",
                        False,
                        f"Invalid trend '{trend}', expected one of {valid_trends}"
                    )
                    return False
            
            self.log_result(
                "All Domains",
                True,
                f"7 domains with all required fields and valid trends"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "All Domains",
                False,
                f"Error checking all domains: {e}"
            )
            return False
    
    def test_narrative_and_reflection(self) -> bool:
        """Test 4: Narrative and Reflection"""
        if not self.first_response_data:
            self.log_result("Narrative and Reflection", False, "No response data available")
            return False
        
        try:
            weekly_summary = self.first_response_data.get("weekly_summary", {})
            
            # Check narrative
            narrative = weekly_summary.get("narrative")
            if not narrative or not isinstance(narrative, str) or len(narrative.strip()) == 0:
                self.log_result(
                    "Narrative and Reflection - Narrative",
                    False,
                    f"Empty or invalid narrative: {type(narrative)}"
                )
                return False
            
            # Check reflection prompt
            reflection_prompt = weekly_summary.get("reflection_prompt")
            if not reflection_prompt or not isinstance(reflection_prompt, str) or len(reflection_prompt.strip()) == 0:
                self.log_result(
                    "Narrative and Reflection - Reflection Prompt",
                    False,
                    f"Empty or invalid reflection prompt: {type(reflection_prompt)}"
                )
                return False
            
            self.log_result(
                "Narrative and Reflection",
                True,
                f"Narrative: {len(narrative)} chars, Reflection: {len(reflection_prompt)} chars"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Narrative and Reflection",
                False,
                f"Error checking narrative/reflection: {e}"
            )
            return False
    
    def test_cross_week_shift(self) -> bool:
        """Test 5: Cross-Week Shift"""
        if not self.first_response_data:
            self.log_result("Cross-Week Shift", False, "No response data available")
            return False
        
        try:
            weekly_summary = self.first_response_data.get("weekly_summary", {})
            cross_week_shift = weekly_summary.get("cross_week_shift")
            
            # Should be null or string
            if cross_week_shift is None:
                self.log_result(
                    "Cross-Week Shift",
                    True,
                    "null (as expected)"
                )
                return True
            elif isinstance(cross_week_shift, str):
                self.log_result(
                    "Cross-Week Shift",
                    True,
                    f"string ({len(cross_week_shift)} chars)"
                )
                return True
            else:
                self.log_result(
                    "Cross-Week Shift",
                    False,
                    f"Expected null or string, got {type(cross_week_shift)}"
                )
                return False
            
        except Exception as e:
            self.log_result(
                "Cross-Week Shift",
                False,
                f"Error checking cross-week shift: {e}"
            )
            return False
    
    def test_evidence_sources(self) -> bool:
        """Test 6: Evidence Sources"""
        if not self.first_response_data:
            self.log_result("Evidence Sources", False, "No response data available")
            return False
        
        try:
            weekly_summary = self.first_response_data.get("weekly_summary", {})
            evidence_sources = weekly_summary.get("evidence_sources")
            
            # Check type
            if not isinstance(evidence_sources, list):
                self.log_result(
                    "Evidence Sources - Type",
                    False,
                    f"Expected list, got {type(evidence_sources)}"
                )
                return False
            
            # Check that all sources are strings
            non_string_sources = [i for i, source in enumerate(evidence_sources) if not isinstance(source, str)]
            if non_string_sources:
                self.log_result(
                    "Evidence Sources - Content",
                    False,
                    f"Non-string sources at indices: {non_string_sources}"
                )
                return False
            
            self.log_result(
                "Evidence Sources",
                True,
                f"{len(evidence_sources)} string sources"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Evidence Sources",
                False,
                f"Error checking evidence sources: {e}"
            )
            return False
    
    def test_caching_behavior(self) -> bool:
        """Test 7: Caching Behavior"""
        if not self.first_response_data:
            self.log_result("Caching Behavior", False, "No response data available")
            return False
        
        try:
            # Make second request
            url = f"{self.base_url}/weekly-patterns/{self.test_user_id}"
            
            start_time = time.time()
            response2 = requests.get(url, timeout=TIMEOUT)
            response_time2 = time.time() - start_time
            
            if response2.status_code != 200:
                self.log_result(
                    "Caching Behavior - Second Request",
                    False,
                    f"HTTP {response2.status_code}"
                )
                return False
            
            data2 = response2.json()
            cached2 = data2.get("cached")
            
            # Check if second call returns cached: true
            if cached2:
                self.log_result(
                    "Caching Behavior - Cached Flag",
                    True,
                    f"Second call returned cached: true in {response_time2:.2f}s"
                )
            else:
                self.log_result(
                    "Caching Behavior - Cached Flag",
                    False,
                    f"Second call did not return cached: true (got: {cached2})"
                )
                return False
            
            # Compare response content consistency
            ws1 = self.first_response_data.get("weekly_summary", {})
            ws2 = data2.get("weekly_summary", {})
            
            if (ws1.get("week_start") == ws2.get("week_start") and 
                ws1.get("week_end") == ws2.get("week_end")):
                self.log_result(
                    "Caching Behavior - Consistency",
                    True,
                    "Identical week dates between calls"
                )
            else:
                self.log_result(
                    "Caching Behavior - Consistency",
                    False,
                    "Different week dates between calls"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_result(
                "Caching Behavior",
                False,
                f"Error testing caching: {e}"
            )
            return False
    
    def test_performance(self) -> bool:
        """Test 8: Performance"""
        if self.first_response_time == 0:
            self.log_result("Performance", False, "No response time data available")
            return False
        
        try:
            if self.first_response_time < 2:
                self.log_result(
                    "Performance",
                    True,
                    f"Excellent - {self.first_response_time:.2f}s (under 2s)"
                )
            elif self.first_response_time < 5:
                self.log_result(
                    "Performance",
                    True,
                    f"Good - {self.first_response_time:.2f}s (under 5s)"
                )
            else:
                self.log_result(
                    "Performance",
                    False,
                    f"Slow - {self.first_response_time:.2f}s (over 5s requirement)"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_result(
                "Performance",
                False,
                f"Error checking performance: {e}"
            )
            return False
    
    def run_all_tests(self):
        """Run all Weekly Pattern Synthesis tests."""
        print("🧪 WEEKLY PATTERN SYNTHESIS API TESTING")
        print("=" * 80)
        print(f"Testing endpoint: GET /api/weekly-patterns/{self.test_user_id}")
        print(f"Backend URL: {self.base_url}")
        print()
        
        # Test 1: Basic Response Structure
        if not self.test_basic_response_structure():
            print("\n❌ Basic response test failed. Stopping further tests.")
            return self.generate_summary()
        
        print()
        
        # Test 2: Top Domains
        self.test_top_domains()
        
        # Test 3: All Domains
        self.test_all_domains()
        
        # Test 4: Narrative and Reflection
        self.test_narrative_and_reflection()
        
        # Test 5: Cross-Week Shift
        self.test_cross_week_shift()
        
        # Test 6: Evidence Sources
        self.test_evidence_sources()
        
        # Test 7: Caching Behavior
        self.test_caching_behavior()
        
        # Test 8: Performance
        self.test_performance()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = [r for r in self.results if r["passed"]]
        failed_tests = [r for r in self.results if not r["passed"]]
        
        print(f"✅ PASSED: {len(passed_tests)}/{len(self.results)} tests")
        print(f"❌ FAILED: {len(failed_tests)}/{len(self.results)} tests")
        
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  ❌ {test['test']}: {test['details']}")
        
        if self.first_response_data:
            weekly_summary = self.first_response_data.get("weekly_summary", {})
            top_domains = weekly_summary.get("top_domains", [])
            all_domains = weekly_summary.get("all_domains", [])
            narrative = weekly_summary.get("narrative", "")
            evidence_sources = weekly_summary.get("evidence_sources", [])
            
            print(f"\nENDPOINT DETAILS:")
            print(f"Response Time: {self.first_response_time:.2f}s")
            print(f"Week: {weekly_summary.get('week_start')} to {weekly_summary.get('week_end')}")
            print(f"Top Domains: {len(top_domains)}")
            print(f"All Domains: {len(all_domains)}")
            print(f"Narrative Length: {len(narrative)} chars")
            print(f"Evidence Sources: {len(evidence_sources)}")
            print(f"Cached: {self.first_response_data.get('cached')}")
        
        print(f"\nTesting completed at: {datetime.now().isoformat()}")
        
        return {
            "total_tests": len(self.results),
            "passed": len(passed_tests),
            "failed": len(failed_tests),
            "success_rate": len(passed_tests) / len(self.results) if self.results else 0,
            "results": self.results
        }


def main():
    """Main test execution."""
    tester = WeeklyPatternSynthesisTester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    if summary["failed"] > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)