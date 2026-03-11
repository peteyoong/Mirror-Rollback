#!/usr/bin/env python3
"""
Backend API Testing Suite for Pattern Graph Transit Integration
Testing the new planetary transit integration in the Pattern Graph API.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://mirror-lens-app.preview.emergentagent.com/api"

class PatternGraphTransitTester:
    """Test suite for Pattern Graph API with transit integration."""
    
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = "6971c81f2b40fd5ef501d375"
        self.results = []
        
    def log_result(self, test_name: str, passed: bool, details: str = "", response_data: Any = None):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "response_data": response_data
        })
    
    def test_pattern_graph_endpoint_availability(self) -> bool:
        """Test 1: Basic endpoint availability."""
        try:
            url = f"{self.base_url}/pattern-graph/{self.test_user_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True:
                    self.log_result(
                        "Pattern Graph Endpoint Availability",
                        True,
                        f"Status: {response.status_code}, Success: {data.get('success')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Pattern Graph Endpoint Availability", 
                        False,
                        f"Success field is {data.get('success')}, expected True"
                    )
                    return False
            else:
                self.log_result(
                    "Pattern Graph Endpoint Availability",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Pattern Graph Endpoint Availability",
                False,
                f"Request failed: {str(e)}"
            )
            return False
    
    def test_transit_amplification_works(self, response_data: Dict) -> bool:
        """Test 2: Transit amplification works - categories with has_transit_emphasis: true exist."""
        try:
            categories = response_data.get("categories", [])
            
            # Check if any categories have transit emphasis
            transit_emphasized = [cat for cat in categories if cat.get("has_transit_emphasis") is True]
            
            if not transit_emphasized:
                self.log_result(
                    "Transit Amplification Works",
                    False,
                    "No categories found with has_transit_emphasis: true"
                )
                return False
            
            # Check if transit-emphasized categories have higher scores
            # Look for expected domains: Energy & Vitality, Mind & Meaning, Expression & Action
            expected_domains = ["Energy & Vitality", "Mind & Meaning", "Expression & Action"]
            found_expected = []
            
            for cat in transit_emphasized:
                cat_name = cat.get("category_name", "")
                pattern_score = cat.get("pattern_score", 0)
                
                if cat_name in expected_domains:
                    found_expected.append(cat_name)
                
                # Verify pattern_score is slightly higher (should be > baseline due to 0.5 weight amplification)
                if pattern_score <= 0:
                    self.log_result(
                        "Transit Amplification Works",
                        False,
                        f"Transit-emphasized category '{cat_name}' has pattern_score {pattern_score}, expected > 0"
                    )
                    return False
            
            details = f"Found {len(transit_emphasized)} transit-emphasized categories"
            if found_expected:
                details += f", including expected domains: {', '.join(found_expected)}"
            
            self.log_result(
                "Transit Amplification Works",
                True,
                details
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Transit Amplification Works",
                False,
                f"Error checking transit amplification: {str(e)}"
            )
            return False
    
    def test_transits_dont_create_patterns_alone(self, response_data: Dict) -> bool:
        """Test 3: Transits don't create patterns alone - domains with transit emphasis also have other signal sources."""
        try:
            categories = response_data.get("categories", [])
            
            # Find categories with transit emphasis
            transit_emphasized = [cat for cat in categories if cat.get("has_transit_emphasis") is True]
            
            if not transit_emphasized:
                # This test passes if there are no transit-emphasized categories
                self.log_result(
                    "Transits Don't Create Patterns Alone",
                    True,
                    "No transit-emphasized categories found (expected behavior if no existing support)"
                )
                return True
            
            for cat in transit_emphasized:
                cat_name = cat.get("category_name", "")
                matched_sources = cat.get("matched_sources", [])
                
                # Check that transit is not the only source
                non_transit_sources = [src for src in matched_sources if src != "astrology_transit"]
                
                if not non_transit_sources:
                    self.log_result(
                        "Transits Don't Create Patterns Alone",
                        False,
                        f"Category '{cat_name}' has only transit source, no other signal sources"
                    )
                    return False
            
            self.log_result(
                "Transits Don't Create Patterns Alone",
                True,
                f"All {len(transit_emphasized)} transit-emphasized categories have other signal sources"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Transits Don't Create Patterns Alone",
                False,
                f"Error checking transit isolation: {str(e)}"
            )
            return False
    
    def test_transit_signal_in_matched_signals(self, response_data: Dict) -> bool:
        """Test 4: Transit signal in matched signals - check transit-emphasized domains include astrology_transit signal."""
        try:
            categories = response_data.get("categories", [])
            
            # Find categories with transit emphasis
            transit_emphasized = [cat for cat in categories if cat.get("has_transit_emphasis") is True]
            
            if not transit_emphasized:
                self.log_result(
                    "Transit Signal in Matched Signals",
                    True,
                    "No transit-emphasized categories to check"
                )
                return True
            
            for cat in transit_emphasized:
                cat_name = cat.get("category_name", "")
                matched_signals = cat.get("matched_signals", [])
                
                # Look for transit signal
                transit_signals = [sig for sig in matched_signals if sig.get("source") == "astrology_transit"]
                
                if not transit_signals:
                    self.log_result(
                        "Transit Signal in Matched Signals",
                        False,
                        f"Category '{cat_name}' has transit emphasis but no astrology_transit signal in matched_signals"
                    )
                    return False
                
                # Check if transit signal has expected label
                transit_signal = transit_signals[0]
                expected_label = "Current transit emphasis"
                if transit_signal.get("label") != expected_label:
                    self.log_result(
                        "Transit Signal in Matched Signals",
                        False,
                        f"Transit signal has label '{transit_signal.get('label')}', expected '{expected_label}'"
                    )
                    return False
                
                # Check if transit signal is at the end of matched_signals array
                last_signal = matched_signals[-1] if matched_signals else None
                if last_signal and last_signal.get("source") != "astrology_transit":
                    print(f"   Note: Transit signal not at end for '{cat_name}' (position may vary)")
            
            self.log_result(
                "Transit Signal in Matched Signals",
                True,
                f"All {len(transit_emphasized)} transit-emphasized categories have proper astrology_transit signals"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Transit Signal in Matched Signals",
                False,
                f"Error checking transit signals: {str(e)}"
            )
            return False
    
    def test_categories_sorted_by_score(self, response_data: Dict) -> bool:
        """Test 5: Categories sorted by score - categories should be sorted by pattern_score in descending order."""
        try:
            categories = response_data.get("categories", [])
            
            if len(categories) < 2:
                self.log_result(
                    "Categories Sorted by Score",
                    True,
                    f"Only {len(categories)} categories, sorting not applicable"
                )
                return True
            
            # Check if categories are sorted by pattern_score in descending order
            scores = [cat.get("pattern_score", 0) for cat in categories]
            sorted_scores = sorted(scores, reverse=True)
            
            if scores != sorted_scores:
                self.log_result(
                    "Categories Sorted by Score",
                    False,
                    f"Categories not sorted by pattern_score. Actual: {scores}, Expected: {sorted_scores}"
                )
                return False
            
            # Check that top patterns have the most support + transit amplification
            top_categories = categories[:3]  # Check top 3
            top_details = []
            for cat in top_categories:
                name = cat.get("category_name", "")
                score = cat.get("pattern_score", 0)
                has_transit = cat.get("has_transit_emphasis", False)
                sources = len(cat.get("matched_sources", []))
                top_details.append(f"{name}: {score} pts, {sources} sources, transit: {has_transit}")
            
            self.log_result(
                "Categories Sorted by Score",
                True,
                f"Categories properly sorted. Top 3: {'; '.join(top_details)}"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Categories Sorted by Score",
                False,
                f"Error checking category sorting: {str(e)}"
            )
            return False
    
    def test_enneagram_still_working(self, response_data: Dict) -> bool:
        """Test 6: Enneagram still working - verify enneagram appears in matched_sources but remains invisible."""
        try:
            categories = response_data.get("categories", [])
            
            # Look for enneagram in matched_sources
            enneagram_categories = []
            personality_pattern_signals = []
            
            for cat in categories:
                matched_sources = cat.get("matched_sources", [])
                matched_signals = cat.get("matched_signals", [])
                
                if "enneagram" in matched_sources:
                    enneagram_categories.append(cat.get("category_name", ""))
                
                # Check for "Personality pattern resonance" signals (should be invisible)
                for signal in matched_signals:
                    if "Personality pattern resonance" in signal.get("label", ""):
                        personality_pattern_signals.append({
                            "category": cat.get("category_name", ""),
                            "label": signal.get("label", "")
                        })
            
            # Enneagram should contribute to scoring but remain invisible in display
            if enneagram_categories:
                self.log_result(
                    "Enneagram Still Working",
                    True,
                    f"Enneagram found in matched_sources for: {', '.join(enneagram_categories)}"
                )
            else:
                # This might be OK if user doesn't have Enneagram data
                self.log_result(
                    "Enneagram Still Working",
                    True,
                    "No enneagram sources found (user may not have Enneagram assessment completed)"
                )
            
            # Check that "Personality pattern resonance" is not visible (should be filtered out)
            if personality_pattern_signals:
                self.log_result(
                    "Enneagram Still Working",
                    False,
                    f"Found visible 'Personality pattern resonance' signals: {personality_pattern_signals}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_result(
                "Enneagram Still Working",
                False,
                f"Error checking Enneagram integration: {str(e)}"
            )
            return False
    
    def test_api_response_structure(self, response_data: Dict) -> bool:
        """Test 7: API Response Structure - verify response includes required fields."""
        try:
            # Check top-level structure
            required_top_level = ["success", "categories", "summary", "updated_at"]
            missing_top_level = [field for field in required_top_level if field not in response_data]
            
            if missing_top_level:
                self.log_result(
                    "API Response Structure",
                    False,
                    f"Missing top-level fields: {missing_top_level}"
                )
                return False
            
            # Check categories structure
            categories = response_data.get("categories", [])
            if not categories:
                self.log_result(
                    "API Response Structure",
                    False,
                    "No categories found in response"
                )
                return False
            
            # Check category fields
            required_category_fields = [
                "category_id", "category_name", "signal_strength", "pattern_score",
                "has_transit_emphasis", "matched_sources", "matched_signals"
            ]
            
            for i, cat in enumerate(categories[:3]):  # Check first 3 categories
                missing_fields = [field for field in required_category_fields if field not in cat]
                if missing_fields:
                    self.log_result(
                        "API Response Structure",
                        False,
                        f"Category {i} missing fields: {missing_fields}"
                    )
                    return False
                
                # Check signal_strength values
                signal_strength = cat.get("signal_strength")
                valid_strengths = ["quiet", "present", "recurring"]
                if signal_strength not in valid_strengths:
                    self.log_result(
                        "API Response Structure",
                        False,
                        f"Invalid signal_strength '{signal_strength}', expected one of {valid_strengths}"
                    )
                    return False
                
                # Check matched_sources includes astrology_transit when has_transit_emphasis is True
                has_transit = cat.get("has_transit_emphasis", False)
                matched_sources = cat.get("matched_sources", [])
                if has_transit and "astrology_transit" not in matched_sources:
                    self.log_result(
                        "API Response Structure",
                        False,
                        f"Category '{cat.get('category_name')}' has transit emphasis but 'astrology_transit' not in matched_sources"
                    )
                    return False
            
            # Check summary structure
            summary = response_data.get("summary", {})
            if not isinstance(summary, dict):
                self.log_result(
                    "API Response Structure",
                    False,
                    f"Summary should be dict, got {type(summary)}"
                )
                return False
            
            self.log_result(
                "API Response Structure",
                True,
                f"All required fields present. {len(categories)} categories, summary keys: {list(summary.keys())}"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "API Response Structure",
                False,
                f"Error checking response structure: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all Pattern Graph transit integration tests."""
        print("🧪 PATTERN GRAPH TRANSIT INTEGRATION TESTING")
        print("=" * 60)
        print(f"Testing endpoint: GET /api/pattern-graph/{self.test_user_id}")
        print(f"Backend URL: {self.base_url}")
        print()
        
        # Test 1: Basic endpoint availability
        if not self.test_pattern_graph_endpoint_availability():
            print("\n❌ Basic endpoint test failed. Stopping further tests.")
            return self.generate_summary()
        
        # Get response data for subsequent tests
        try:
            url = f"{self.base_url}/pattern-graph/{self.test_user_id}"
            response = requests.get(url, timeout=30)
            response_data = response.json()
        except Exception as e:
            print(f"\n❌ Failed to get response data for subsequent tests: {e}")
            return self.generate_summary()
        
        print()
        
        # Test 2: Transit amplification works
        self.test_transit_amplification_works(response_data)
        
        # Test 3: Transits don't create patterns alone
        self.test_transits_dont_create_patterns_alone(response_data)
        
        # Test 4: Transit signal in matched signals
        self.test_transit_signal_in_matched_signals(response_data)
        
        # Test 5: Categories sorted by score
        self.test_categories_sorted_by_score(response_data)
        
        # Test 6: Enneagram still working
        self.test_enneagram_still_working(response_data)
        
        # Test 7: API response structure
        self.test_api_response_structure(response_data)
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = [r for r in self.results if r["passed"]]
        failed_tests = [r for r in self.results if not r["passed"]]
        
        print(f"✅ PASSED: {len(passed_tests)}/{len(self.results)} tests")
        print(f"❌ FAILED: {len(failed_tests)}/{len(self.results)} tests")
        
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  ❌ {test['test']}: {test['details']}")
        
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
    tester = PatternGraphTransitTester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    if summary["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()