#!/usr/bin/env python3
"""
Backend Testing Suite for Pattern Graph API with Human Design Integration
Testing Agent for Project Mirror - Pattern Signals Integration
"""

import requests
import json
import sys
from typing import Dict, List, Any
from datetime import datetime

# Configuration
BASE_URL = "https://pattern-signals-4.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

class PatternGraphTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.user_id = TEST_USER_ID
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "status": status
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_pattern_graph_endpoint_availability(self) -> bool:
        """Test 1: Basic endpoint availability and response structure"""
        try:
            url = f"{self.base_url}/pattern-graph/{self.user_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                self.log_test("Pattern Graph Endpoint Availability", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
            
            data = response.json()
            
            # Check basic structure
            required_fields = ["success", "categories", "summary", "updated_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Pattern Graph Endpoint Availability", False,
                            f"Missing fields: {missing_fields}")
                return False
            
            if not data.get("success"):
                self.log_test("Pattern Graph Endpoint Availability", False,
                            f"Success field is False: {data}")
                return False
            
            self.log_test("Pattern Graph Endpoint Availability", True,
                        f"Status: 200 OK, Response structure valid")
            return True
            
        except Exception as e:
            self.log_test("Pattern Graph Endpoint Availability", False, f"Exception: {str(e)}")
            return False
    
    def test_human_design_signals_present(self) -> Dict[str, Any]:
        """Test 2: Verify Human Design signals are present in matched_sources"""
        try:
            url = f"{self.base_url}/pattern-graph/{self.user_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                self.log_test("Human Design Signals Present", False,
                            f"API call failed: {response.status_code}")
                return {}
            
            data = response.json()
            categories = data.get("categories", [])
            
            # Check if any category has human_design in matched_sources
            hd_categories = []
            hd_signals_count = 0
            
            for category in categories:
                matched_sources = category.get("matched_sources", [])
                matched_signals = category.get("matched_signals", [])
                
                if "human_design" in matched_sources:
                    hd_categories.append(category["category_name"])
                
                # Count signals with human_design source
                for signal in matched_signals:
                    if signal.get("source") == "human_design":
                        hd_signals_count += 1
            
            if not hd_categories:
                self.log_test("Human Design Signals Present", False,
                            "No categories found with 'human_design' in matched_sources")
                return {}
            
            if hd_signals_count == 0:
                self.log_test("Human Design Signals Present", False,
                            "No signals found with source: 'human_design'")
                return {}
            
            self.log_test("Human Design Signals Present", True,
                        f"Found {hd_signals_count} HD signals in categories: {hd_categories}")
            
            return {
                "hd_categories": hd_categories,
                "hd_signals_count": hd_signals_count,
                "data": data
            }
            
        except Exception as e:
            self.log_test("Human Design Signals Present", False, f"Exception: {str(e)}")
            return {}
    
    def test_center_signal_format(self, test_data: Dict[str, Any]) -> bool:
        """Test 3: Verify HD center signals have proper format"""
        if not test_data:
            self.log_test("Center Signal Format", False, "No test data available")
            return False
        
        try:
            data = test_data.get("data", {})
            categories = data.get("categories", [])
            
            center_signals_found = []
            format_issues = []
            
            for category in categories:
                matched_signals = category.get("matched_signals", [])
                
                for signal in matched_signals:
                    if signal.get("source") == "human_design":
                        label = signal.get("label", "")
                        detail = signal.get("detail", "")
                        
                        # Check if this looks like a center signal
                        center_keywords = ["Center", "Sacral", "Spleen", "Solar Plexus", "Throat", "Head", "Ajna", "Root", "Ego", "G /"]
                        is_center_signal = any(keyword in label for keyword in center_keywords)
                        
                        if is_center_signal:
                            center_signals_found.append({
                                "label": label,
                                "detail": detail,
                                "category": category["category_name"]
                            })
                            
                            # Check format: should have (defined) or (open) in label
                            if not ("(defined)" in label or "(open)" in label):
                                format_issues.append(f"Missing defined/open status in: {label}")
                            
                            # Check detail: should have "Gates:" format
                            if detail and "Gates:" not in detail:
                                format_issues.append(f"Missing 'Gates:' format in detail: {detail}")
            
            if not center_signals_found:
                self.log_test("Center Signal Format", False,
                            "No center signals found in Human Design data")
                return False
            
            if format_issues:
                self.log_test("Center Signal Format", False,
                            f"Format issues found: {format_issues}")
                return False
            
            self.log_test("Center Signal Format", True,
                        f"Found {len(center_signals_found)} properly formatted center signals")
            return True
            
        except Exception as e:
            self.log_test("Center Signal Format", False, f"Exception: {str(e)}")
            return False
    
    def test_multi_source_categories(self, test_data: Dict[str, Any]) -> bool:
        """Test 4: Verify categories can have multiple sources and proper signal strength"""
        if not test_data:
            self.log_test("Multi-Source Categories", False, "No test data available")
            return False
        
        try:
            data = test_data.get("data", {})
            categories = data.get("categories", [])
            
            multi_source_categories = []
            active_categories = []
            signal_strength_issues = []
            
            for category in categories:
                matched_sources = category.get("matched_sources", [])
                matched_signals = category.get("matched_signals", [])
                signal_strength = category.get("signal_strength", "")
                
                # Check for multiple sources
                if len(matched_sources) >= 2:
                    multi_source_categories.append({
                        "name": category["category_name"],
                        "sources": matched_sources,
                        "signal_count": len(matched_signals),
                        "strength": signal_strength
                    })
                
                # Check signal strength logic
                num_signals = len(matched_signals)
                num_sources = len(matched_sources)
                
                expected_strength = "quiet"
                if num_signals >= 3 or num_sources >= 2:
                    expected_strength = "active"
                elif num_signals >= 1:
                    expected_strength = "emerging"
                
                if signal_strength != expected_strength:
                    signal_strength_issues.append(
                        f"{category['category_name']}: expected {expected_strength}, got {signal_strength} "
                        f"(signals: {num_signals}, sources: {num_sources})"
                    )
                
                if signal_strength == "active":
                    active_categories.append(category["category_name"])
            
            # Verify we have some multi-source categories
            if not multi_source_categories:
                self.log_test("Multi-Source Categories", False,
                            "No categories found with multiple sources")
                return False
            
            # Check for signal strength calculation issues
            if signal_strength_issues:
                self.log_test("Multi-Source Categories", False,
                            f"Signal strength calculation issues: {signal_strength_issues}")
                return False
            
            # Verify active categories when 2+ sources present
            active_multi_source = [cat for cat in multi_source_categories if cat["strength"] == "active"]
            
            self.log_test("Multi-Source Categories", True,
                        f"Found {len(multi_source_categories)} multi-source categories, "
                        f"{len(active_multi_source)} marked as active")
            return True
            
        except Exception as e:
            self.log_test("Multi-Source Categories", False, f"Exception: {str(e)}")
            return False
    
    def test_signal_count_verification(self, test_data: Dict[str, Any]) -> bool:
        """Test 5: Verify signal count distribution by source type"""
        if not test_data:
            self.log_test("Signal Count Verification", False, "No test data available")
            return False
        
        try:
            data = test_data.get("data", {})
            categories = data.get("categories", [])
            
            source_counts = {
                "human_design": 0,
                "gene_keys": 0,
                "journal": 0,
                "other": 0
            }
            
            total_signals = 0
            
            for category in categories:
                matched_signals = category.get("matched_signals", [])
                
                for signal in matched_signals:
                    source = signal.get("source", "other")
                    if source in source_counts:
                        source_counts[source] += 1
                    else:
                        source_counts["other"] += 1
                    total_signals += 1
            
            # Verify we have Human Design signals (requirement)
            if source_counts["human_design"] < 3:
                self.log_test("Signal Count Verification", False,
                            f"Expected at least 3 HD signals, found {source_counts['human_design']}")
                return False
            
            # Verify reasonable distribution
            if total_signals < 5:
                self.log_test("Signal Count Verification", False,
                            f"Total signals too low: {total_signals}")
                return False
            
            self.log_test("Signal Count Verification", True,
                        f"Signal distribution: HD={source_counts['human_design']}, "
                        f"GK={source_counts['gene_keys']}, Journal={source_counts['journal']}, "
                        f"Total={total_signals}")
            return True
            
        except Exception as e:
            self.log_test("Signal Count Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_api_response_structure(self, test_data: Dict[str, Any]) -> bool:
        """Test 6: Verify complete API response structure"""
        if not test_data:
            self.log_test("API Response Structure", False, "No test data available")
            return False
        
        try:
            data = test_data.get("data", {})
            
            # Check categories structure
            categories = data.get("categories", [])
            if len(categories) != 7:
                self.log_test("API Response Structure", False,
                            f"Expected 7 categories, found {len(categories)}")
                return False
            
            # Check each category structure
            required_category_fields = ["category_id", "category_name", "signal_strength", 
                                      "matched_sources", "matched_signals", "summary"]
            
            for i, category in enumerate(categories):
                missing_fields = [field for field in required_category_fields if field not in category]
                if missing_fields:
                    self.log_test("API Response Structure", False,
                                f"Category {i} missing fields: {missing_fields}")
                    return False
                
                # Check signal structure
                for j, signal in enumerate(category.get("matched_signals", [])):
                    required_signal_fields = ["source", "label"]
                    missing_signal_fields = [field for field in required_signal_fields if field not in signal]
                    if missing_signal_fields:
                        self.log_test("API Response Structure", False,
                                    f"Signal {j} in category {i} missing fields: {missing_signal_fields}")
                        return False
            
            # Check summary structure
            summary = data.get("summary", {})
            required_summary_fields = ["active_categories", "emerging_categories", "total_signals"]
            missing_summary_fields = [field for field in required_summary_fields if field not in summary]
            
            if missing_summary_fields:
                self.log_test("API Response Structure", False,
                            f"Summary missing fields: {missing_summary_fields}")
                return False
            
            self.log_test("API Response Structure", True,
                        f"All 7 categories present with proper structure, "
                        f"summary: {summary}")
            return True
            
        except Exception as e:
            self.log_test("API Response Structure", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Pattern Graph API tests"""
        print("=" * 80)
        print("PATTERN GRAPH API WITH HUMAN DESIGN SIGNALS INTEGRATION TESTING")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Test User ID: {self.user_id}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test 1: Basic endpoint availability
        if not self.test_pattern_graph_endpoint_availability():
            print("\n❌ CRITICAL: Basic endpoint failed, stopping tests")
            return self.print_summary()
        
        # Test 2: Human Design signals present
        hd_test_data = self.test_human_design_signals_present()
        if not hd_test_data:
            print("\n❌ CRITICAL: No Human Design signals found, continuing with remaining tests")
        
        # Test 3: Center signal format
        self.test_center_signal_format(hd_test_data)
        
        # Test 4: Multi-source categories
        self.test_multi_source_categories(hd_test_data)
        
        # Test 5: Signal count verification
        self.test_signal_count_verification(hd_test_data)
        
        # Test 6: API response structure
        self.test_api_response_structure(hd_test_data)
        
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary and return results"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = [t for t in self.test_results if t["passed"]]
        failed_tests = [t for t in self.test_results if not t["passed"]]
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS: {len(passed_tests)}/{len(self.test_results)}")
        
        print("\n" + "=" * 80)
        
        return {
            "total_tests": len(self.test_results),
            "passed": len(passed_tests),
            "failed": len(failed_tests),
            "success_rate": len(passed_tests)/len(self.test_results)*100,
            "results": self.test_results
        }


def main():
    """Main test execution"""
    tester = PatternGraphTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()