#!/usr/bin/env python3
"""
Backend Testing Suite for Project Mirror
Tests Human Design Defined Gates endpoint implementation
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://pattern-signals-4.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ {test_name}")
        
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n📊 TEST SUMMARY:")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        if self.errors:
            print(f"\n🔍 FAILURES:")
            for error in self.errors:
                print(f"  - {error}")

def test_human_design_gates_endpoint():
    """Test the Human Design Defined Gates endpoint implementation"""
    results = TestResults()
    
    print("🧪 TESTING HUMAN DESIGN DEFINED GATES ENDPOINT")
    print("=" * 60)
    
    # Test 1: Basic Gates Endpoint Test
    print("\n1. BASIC GATES ENDPOINT TEST")
    try:
        url = f"{BASE_URL}/human-design/gates/{TEST_USER_ID}"
        print(f"   Testing: GET {url}")
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = time.time() - start_time
        
        print(f"   Response Time: {response_time:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results.add_pass("Basic endpoint accessibility (200 OK)")
        else:
            results.add_fail("Basic endpoint accessibility", f"Status {response.status_code}")
            return results
            
        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            results.add_fail("JSON parsing", f"Invalid JSON: {e}")
            return results
            
        # Check basic response structure
        if data.get("success") is True:
            results.add_pass("Response success field is true")
        else:
            results.add_fail("Response success field", f"Expected true, got {data.get('success')}")
            
        if "gates" in data and isinstance(data["gates"], list):
            results.add_pass("Gates array present")
            gates = data["gates"]
            print(f"   Gates Count: {len(gates)}")
        else:
            results.add_fail("Gates array", "Missing or not a list")
            return results
            
        if "summary" in data and isinstance(data["summary"], dict):
            results.add_pass("Summary object present")
            summary = data["summary"]
            if "total_gates" in summary:
                results.add_pass("Summary contains total_gates")
                print(f"   Total Gates: {summary['total_gates']}")
            else:
                results.add_fail("Summary total_gates", "Missing total_gates field")
        else:
            results.add_fail("Summary object", "Missing or not a dict")
            
    except requests.exceptions.RequestException as e:
        results.add_fail("Basic endpoint test", f"Request failed: {e}")
        return results
    except Exception as e:
        results.add_fail("Basic endpoint test", f"Unexpected error: {e}")
        return results
    
    # Test 2: Gate Data Structure Test
    print("\n2. GATE DATA STRUCTURE TEST")
    if len(gates) > 0:
        # Test first gate structure
        sample_gate = gates[0]
        print(f"   Testing gate structure with Gate {sample_gate.get('gate_number', 'Unknown')}")
        
        required_fields = [
            "gate_number", "line_numbers_present", "center_name", "gate_name",
            "themes", "shadow", "gift", "siddhi", "what_this_means",
            "your_challenge", "your_genius", "practical_experiments", "remember"
        ]
        
        for field in required_fields:
            if field in sample_gate:
                results.add_pass(f"Gate has {field} field")
            else:
                results.add_fail(f"Gate {field} field", "Missing required field")
        
        # Validate specific field types and content
        if isinstance(sample_gate.get("gate_number"), int) and 1 <= sample_gate.get("gate_number", 0) <= 64:
            results.add_pass("Gate number is valid integer (1-64)")
        else:
            results.add_fail("Gate number validation", f"Expected int 1-64, got {sample_gate.get('gate_number')}")
            
        if isinstance(sample_gate.get("line_numbers_present"), list):
            results.add_pass("Line numbers present is array")
        else:
            results.add_fail("Line numbers present", "Expected array")
            
        if isinstance(sample_gate.get("center_name"), str) and sample_gate.get("center_name"):
            results.add_pass("Center name is non-empty string")
        else:
            results.add_fail("Center name", "Expected non-empty string")
            
        if isinstance(sample_gate.get("gate_name"), str) and sample_gate.get("gate_name"):
            results.add_pass("Gate name is non-empty string")
        else:
            results.add_fail("Gate name", "Expected non-empty string")
            
        if isinstance(sample_gate.get("themes"), list) and len(sample_gate.get("themes", [])) == 3:
            results.add_pass("Themes is array with 3 items")
        else:
            results.add_fail("Themes validation", f"Expected array with 3 items, got {sample_gate.get('themes')}")
            
        # Gene Keys bridge validation
        gene_keys_fields = ["shadow", "gift", "siddhi"]
        for field in gene_keys_fields:
            value = sample_gate.get(field)
            if isinstance(value, str) and value.strip():
                results.add_pass(f"Gene Keys {field} is non-empty string")
            else:
                results.add_fail(f"Gene Keys {field}", "Expected non-empty string")
        
        # Interpretive content validation
        interpretive_fields = ["what_this_means", "your_challenge", "your_genius", "remember"]
        for field in interpretive_fields:
            value = sample_gate.get(field)
            if isinstance(value, str) and len(value.strip()) > 20:  # Meaningful content
                results.add_pass(f"Interpretive field {field} has meaningful content")
            else:
                results.add_fail(f"Interpretive field {field}", "Expected meaningful content (>20 chars)")
        
        # Practical experiments validation
        experiments = sample_gate.get("practical_experiments")
        if isinstance(experiments, list) and len(experiments) == 3:
            results.add_pass("Practical experiments is array with 3 items")
            all_strings = all(isinstance(exp, str) and len(exp.strip()) > 10 for exp in experiments)
            if all_strings:
                results.add_pass("All practical experiments are meaningful strings")
            else:
                results.add_fail("Practical experiments content", "Expected meaningful strings (>10 chars each)")
        else:
            results.add_fail("Practical experiments", "Expected array with 3 items")
            
    else:
        results.add_fail("Gate data structure test", "No gates returned to test structure")
    
    # Test 3: Content Quality Test
    print("\n3. CONTENT QUALITY TEST")
    if len(gates) > 0:
        # Check for meaningful interpretive content
        sample_gate = gates[0]
        
        # Verify Gene Keys bridge has different values
        shadow = sample_gate.get("shadow", "")
        gift = sample_gate.get("gift", "")
        siddhi = sample_gate.get("siddhi", "")
        
        if shadow != gift and gift != siddhi and shadow != siddhi:
            results.add_pass("Gene Keys bridge has different values for shadow/gift/siddhi")
        else:
            results.add_fail("Gene Keys bridge uniqueness", "Shadow, gift, and siddhi should be different")
        
        # Check for reflective/practical tone (avoid jargon-heavy content)
        what_this_means = sample_gate.get("what_this_means", "")
        jargon_indicators = ["cosmic", "divine", "sacred", "mystical", "karmic", "destiny"]
        jargon_count = sum(1 for word in jargon_indicators if word.lower() in what_this_means.lower())
        
        if jargon_count <= 1:  # Allow minimal jargon
            results.add_pass("Content has practical, non-jargon-heavy tone")
        else:
            results.add_fail("Content tone", f"Too much jargon detected ({jargon_count} indicators)")
        
        # Check for practical language
        practical_indicators = ["you", "your", "practice", "notice", "track", "experiment"]
        practical_count = sum(1 for word in practical_indicators if word.lower() in what_this_means.lower())
        
        if practical_count >= 2:
            results.add_pass("Content uses practical, reflective language")
        else:
            results.add_fail("Content practicality", "Content should be more practical and reflective")
            
        print(f"   Sample Gate: {sample_gate.get('gate_number')} - {sample_gate.get('gate_name')}")
        print(f"   Shadow: {shadow}")
        print(f"   Gift: {gift}")
        print(f"   Siddhi: {siddhi}")
        
    # Test 4: Multiple Gates Test
    print("\n4. MULTIPLE GATES TEST")
    if len(gates) > 10:
        results.add_pass("Returns multiple gates (>10 gates typically)")
        print(f"   Gates returned: {len(gates)}")
        
        # Check that we're getting only user's active gates, not all 64
        if len(gates) < 64:
            results.add_pass("Returns only user's active gates (not all 64)")
        else:
            results.add_fail("Gate filtering", "Should return only active gates, not all 64")
            
        # Test a few more gates for consistency
        gates_to_test = min(3, len(gates))
        consistent_structure = True
        
        for i in range(gates_to_test):
            gate = gates[i]
            required_fields = ["gate_number", "gate_name", "shadow", "gift", "siddhi"]
            for field in required_fields:
                if field not in gate or not gate[field]:
                    consistent_structure = False
                    break
            if not consistent_structure:
                break
                
        if consistent_structure:
            results.add_pass("Multiple gates have consistent structure")
        else:
            results.add_fail("Gate structure consistency", "Not all gates have consistent structure")
            
    else:
        results.add_fail("Multiple gates test", f"Expected >10 gates, got {len(gates)}")
    
    # Test 5: Performance Test
    print("\n5. PERFORMANCE TEST")
    if response_time < 10.0:  # Should be reasonably fast
        results.add_pass(f"Response time acceptable ({response_time:.2f}s < 10s)")
    else:
        results.add_fail("Performance", f"Response too slow: {response_time:.2f}s")
    
    return results

def main():
    """Run all tests"""
    print("🚀 STARTING HUMAN DESIGN GATES ENDPOINT TESTING")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("=" * 80)
    
    # Run the main test
    results = test_human_design_gates_endpoint()
    
    # Print summary
    results.summary()
    
    # Return exit code based on results
    return 0 if results.failed == 0 else 1

if __name__ == "__main__":
    exit(main())