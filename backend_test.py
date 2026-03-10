#!/usr/bin/env python3
"""
Backend API Testing Suite for Pattern Graph Endpoint
Tests the GET /api/pattern-graph/{user_id} endpoint implementation.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://pattern-signals-4.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

# Expected 7 core categories
EXPECTED_CATEGORIES = [
    "Energy & Vitality",
    "Emotional Landscape", 
    "Identity & Direction",
    "Mind & Meaning",
    "Expression & Action",
    "Relationships & Boundaries",
    "Growth & Transformation"
]

# Valid signal strength values
VALID_SIGNAL_STRENGTHS = ["quiet", "emerging", "active"]

# Valid source types
VALID_SOURCES = ["gene_keys", "journal", "chat"]

class PatternGraphTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
            
        self.test_results.append(result)
        print(result)
        
    def test_basic_endpoint_availability(self) -> Dict[str, Any]:
        """Test 1: Basic Pattern Graph Endpoint Test"""
        print(f"\n🧪 TEST 1: Basic Pattern Graph Endpoint Test")
        print(f"Testing: GET {BASE_URL}/pattern-graph/{TEST_USER_ID}")
        
        try:
            response = requests.get(f"{BASE_URL}/pattern-graph/{TEST_USER_ID}", timeout=30)
            
            # Check status code
            self.log_test("HTTP Status Code", response.status_code == 200, 
                         f"Got {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response: {response.text}")
                return {}
                
            # Parse JSON
            try:
                data = response.json()
                self.log_test("JSON Response Parsing", True, "Valid JSON structure")
            except json.JSONDecodeError as e:
                self.log_test("JSON Response Parsing", False, f"Invalid JSON: {e}")
                return {}
            
            # Check required top-level fields
            required_fields = ["success", "categories", "summary", "updated_at"]
            for field in required_fields:
                has_field = field in data
                self.log_test(f"Required field '{field}'", has_field, 
                             f"Present: {has_field}")
            
            # Check success field
            success = data.get("success", False)
            self.log_test("Success field value", success == True, 
                         f"success: {success}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.log_test("HTTP Request", False, f"Request failed: {e}")
            return {}
    
    def test_category_structure(self, data: Dict[str, Any]):
        """Test 2: Category Data Structure Test"""
        print(f"\n🧪 TEST 2: Category Data Structure Test")
        
        categories = data.get("categories", [])
        
        # Check exactly 7 categories
        self.log_test("Exactly 7 categories", len(categories) == 7, 
                     f"Found {len(categories)} categories")
        
        if len(categories) != 7:
            print(f"Categories found: {[c.get('category_name', 'Unknown') for c in categories]}")
            return
        
        # Check each category has required fields
        required_category_fields = [
            "category_id", "category_name", "signal_strength", 
            "matched_sources", "matched_signals", "summary"
        ]
        
        for i, category in enumerate(categories):
            cat_name = category.get("category_name", f"Category {i+1}")
            
            for field in required_category_fields:
                has_field = field in category
                self.log_test(f"Category '{cat_name}' has '{field}'", has_field,
                             f"Field present: {has_field}")
            
            # Check signal strength is valid
            strength = category.get("signal_strength", "")
            valid_strength = strength in VALID_SIGNAL_STRENGTHS
            self.log_test(f"Category '{cat_name}' valid signal_strength", valid_strength,
                         f"Got '{strength}', expected one of {VALID_SIGNAL_STRENGTHS}")
            
            # Check matched_sources is array
            sources = category.get("matched_sources", [])
            is_list = isinstance(sources, list)
            self.log_test(f"Category '{cat_name}' matched_sources is array", is_list,
                         f"Type: {type(sources).__name__}")
            
            # Check matched_signals is array
            signals = category.get("matched_signals", [])
            is_list = isinstance(signals, list)
            self.log_test(f"Category '{cat_name}' matched_signals is array", is_list,
                         f"Type: {type(signals).__name__}")
            
            # Check summary is non-empty string
            summary = category.get("summary", "")
            is_string = isinstance(summary, str) and len(summary.strip()) > 0
            self.log_test(f"Category '{cat_name}' has non-empty summary", is_string,
                         f"Summary length: {len(summary)} chars")
    
    def test_signal_structure(self, data: Dict[str, Any]):
        """Test 3: Signal Structure Test"""
        print(f"\n🧪 TEST 3: Signal Structure Test")
        
        categories = data.get("categories", [])
        total_signals_tested = 0
        
        for category in categories:
            cat_name = category.get("category_name", "Unknown")
            signals = category.get("matched_signals", [])
            
            for i, signal in enumerate(signals):
                total_signals_tested += 1
                signal_id = f"{cat_name} Signal {i+1}"
                
                # Check required signal fields
                required_signal_fields = ["source", "label"]
                for field in required_signal_fields:
                    has_field = field in signal
                    self.log_test(f"{signal_id} has '{field}'", has_field,
                                 f"Field present: {has_field}")
                
                # Check source is valid
                source = signal.get("source", "")
                valid_source = source in VALID_SOURCES
                self.log_test(f"{signal_id} valid source", valid_source,
                             f"Got '{source}', expected one of {VALID_SOURCES}")
                
                # Check label is non-empty string
                label = signal.get("label", "")
                is_string = isinstance(label, str) and len(label.strip()) > 0
                self.log_test(f"{signal_id} has non-empty label", is_string,
                             f"Label: '{label[:50]}...' ({len(label)} chars)")
                
                # Check optional fields exist (can be None)
                optional_fields = ["sphere_name", "detail"]
                for field in optional_fields:
                    has_field = field in signal
                    field_value = signal.get(field)
                    self.log_test(f"{signal_id} has '{field}' field", has_field,
                                 f"Value: {field_value}")
        
        self.log_test("Total signals tested", total_signals_tested > 0,
                     f"Tested {total_signals_tested} signals across all categories")
    
    def test_category_names_verification(self, data: Dict[str, Any]):
        """Test 4: Category Names Verification"""
        print(f"\n🧪 TEST 4: Category Names Verification")
        
        categories = data.get("categories", [])
        found_names = [cat.get("category_name", "") for cat in categories]
        
        print(f"Expected categories: {EXPECTED_CATEGORIES}")
        print(f"Found categories: {found_names}")
        
        for expected_name in EXPECTED_CATEGORIES:
            found = expected_name in found_names
            self.log_test(f"Category '{expected_name}' present", found,
                         f"Found in response: {found}")
        
        # Check for unexpected categories
        unexpected = [name for name in found_names if name not in EXPECTED_CATEGORIES]
        if unexpected:
            self.log_test("No unexpected categories", False,
                         f"Unexpected: {unexpected}")
        else:
            self.log_test("No unexpected categories", True, "All categories expected")
    
    def test_signal_strength_logic(self, data: Dict[str, Any]):
        """Test 5: Signal Strength Logic Test"""
        print(f"\n🧪 TEST 5: Signal Strength Logic Test")
        
        categories = data.get("categories", [])
        
        for category in categories:
            cat_name = category.get("category_name", "Unknown")
            signals = category.get("matched_signals", [])
            sources = category.get("matched_sources", [])
            strength = category.get("signal_strength", "")
            
            num_signals = len(signals)
            num_sources = len(sources)
            
            # Test signal strength logic:
            # - Active: 3+ signals OR 2+ sources
            # - Emerging: 1-2 signals from single source  
            # - Quiet: no signals
            
            expected_strength = ""
            if num_signals >= 3 or num_sources >= 2:
                expected_strength = "active"
            elif num_signals >= 1:
                expected_strength = "emerging"
            else:
                expected_strength = "quiet"
            
            correct_logic = strength == expected_strength
            self.log_test(f"'{cat_name}' signal strength logic", correct_logic,
                         f"Signals: {num_signals}, Sources: {num_sources}, "
                         f"Expected: '{expected_strength}', Got: '{strength}'")
    
    def test_summary_structure(self, data: Dict[str, Any]):
        """Test 6: Summary Structure Test"""
        print(f"\n🧪 TEST 6: Summary Structure Test")
        
        summary = data.get("summary", {})
        
        # Check required summary fields
        required_summary_fields = ["active_categories", "emerging_categories", "total_signals"]
        for field in required_summary_fields:
            has_field = field in summary
            self.log_test(f"Summary has '{field}'", has_field,
                         f"Field present: {has_field}")
        
        # Check field types and values
        active_count = summary.get("active_categories", -1)
        emerging_count = summary.get("emerging_categories", -1)
        total_signals = summary.get("total_signals", -1)
        
        # Verify counts are non-negative integers
        self.log_test("active_categories is non-negative int", 
                     isinstance(active_count, int) and active_count >= 0,
                     f"Value: {active_count}")
        
        self.log_test("emerging_categories is non-negative int",
                     isinstance(emerging_count, int) and emerging_count >= 0,
                     f"Value: {emerging_count}")
        
        self.log_test("total_signals is non-negative int",
                     isinstance(total_signals, int) and total_signals >= 0,
                     f"Value: {total_signals}")
        
        # Verify counts match actual categories
        categories = data.get("categories", [])
        actual_active = sum(1 for c in categories if c.get("signal_strength") == "active")
        actual_emerging = sum(1 for c in categories if c.get("signal_strength") == "emerging")
        actual_total = sum(len(c.get("matched_signals", [])) for c in categories)
        
        self.log_test("active_categories count matches", active_count == actual_active,
                     f"Summary: {active_count}, Actual: {actual_active}")
        
        self.log_test("emerging_categories count matches", emerging_count == actual_emerging,
                     f"Summary: {emerging_count}, Actual: {actual_emerging}")
        
        self.log_test("total_signals count matches", total_signals == actual_total,
                     f"Summary: {total_signals}, Actual: {actual_total}")
    
    def test_timestamp_format(self, data: Dict[str, Any]):
        """Test 7: Timestamp Format Test"""
        print(f"\n🧪 TEST 7: Timestamp Format Test")
        
        updated_at = data.get("updated_at", "")
        
        # Check timestamp is present
        self.log_test("updated_at field present", bool(updated_at),
                     f"Value: '{updated_at}'")
        
        # Try to parse as ISO format
        try:
            parsed_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            self.log_test("updated_at is valid ISO timestamp", True,
                         f"Parsed: {parsed_time}")
        except (ValueError, AttributeError) as e:
            self.log_test("updated_at is valid ISO timestamp", False,
                         f"Parse error: {e}")
    
    def run_all_tests(self):
        """Run all Pattern Graph API tests."""
        print("=" * 80)
        print("🧪 PATTERN GRAPH API ENDPOINT TESTING")
        print("=" * 80)
        print(f"Base URL: {BASE_URL}")
        print(f"Test User ID: {TEST_USER_ID}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Test 1: Basic endpoint availability
        data = self.test_basic_endpoint_availability()
        
        if not data:
            print("\n❌ CRITICAL: Basic endpoint test failed. Stopping further tests.")
            self.print_summary()
            return
        
        # Test 2-7: Structure and logic tests
        self.test_category_structure(data)
        self.test_signal_structure(data)
        self.test_category_names_verification(data)
        self.test_signal_strength_logic(data)
        self.test_summary_structure(data)
        self.test_timestamp_format(data)
        
        # Print final summary
        self.print_summary()
        
        # Print sample response data for verification
        self.print_sample_data(data)
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            print(result)
        
        print(f"\n🎯 OVERALL RESULTS: {self.passed_tests}/{self.total_tests} tests passed")
        
        if self.passed_tests == self.total_tests:
            print("🎉 ALL TESTS PASSED! Pattern Graph API is working correctly.")
        else:
            failed = self.total_tests - self.passed_tests
            print(f"⚠️  {failed} test(s) failed. Review the issues above.")
    
    def print_sample_data(self, data: Dict[str, Any]):
        """Print sample response data for manual verification."""
        print("\n" + "=" * 80)
        print("📋 SAMPLE RESPONSE DATA")
        print("=" * 80)
        
        categories = data.get("categories", [])
        summary = data.get("summary", {})
        
        print(f"Summary: {summary}")
        print(f"Total categories: {len(categories)}")
        
        # Show first few categories with signals
        categories_with_signals = [c for c in categories if c.get("matched_signals")]
        
        if categories_with_signals:
            print(f"\nCategories with signals ({len(categories_with_signals)}):")
            for cat in categories_with_signals[:3]:  # Show first 3
                name = cat.get("category_name", "Unknown")
                strength = cat.get("signal_strength", "unknown")
                signals = cat.get("matched_signals", [])
                sources = cat.get("matched_sources", [])
                
                print(f"  • {name}: {strength} ({len(signals)} signals from {sources})")
                for signal in signals[:2]:  # Show first 2 signals
                    label = signal.get("label", "No label")
                    source = signal.get("source", "unknown")
                    print(f"    - {label} (from {source})")
        else:
            print("\nNo categories with signals found.")
        
        print(f"\nResponse timestamp: {data.get('updated_at', 'Not provided')}")


def main():
    """Main test execution."""
    tester = PatternGraphTester()
    tester.run_all_tests()
    
    # Return exit code based on test results
    if tester.passed_tests == tester.total_tests:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()