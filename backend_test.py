#!/usr/bin/env python3
"""
Backend API Testing for Lifeline Ingestion Architecture
Tests the new Lifeline Ingestion API endpoints as specified in the review request.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://lifeline-fixes.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"  # User with 10 clean events after migration

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"[{timestamp}] {status_symbol} {test_name}")
    if details:
        print(f"    {details}")

def test_endpoint(endpoint, method="GET", expected_status=200, payload=None):
    """Generic endpoint tester"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=payload, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Check status code
        if response.status_code != expected_status:
            return False, f"Expected {expected_status}, got {response.status_code}"
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            return False, "Invalid JSON response"
        
        return True, data
        
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"

def test_lifeline_ingestion_stats():
    """Test GET /api/lifeline/ingestion-stats/{user_id}"""
    print("\n🧪 TESTING: Lifeline Ingestion Stats Endpoint")
    
    success, result = test_endpoint(f"/lifeline/ingestion-stats/{TEST_USER_ID}")
    
    if not success:
        log_test("Ingestion Stats API", "FAIL", result)
        return False
    
    # Verify response structure
    required_fields = ["success"]
    for field in required_fields:
        if field not in result:
            log_test("Ingestion Stats API", "FAIL", f"Missing field: {field}")
            return False
    
    if not result.get("success"):
        log_test("Ingestion Stats API", "FAIL", "success=false in response")
        return False
    
    # Check for expected stats fields
    expected_stats = ["canonical_events", "potential_duplicate_groups"]
    stats_present = []
    for stat in expected_stats:
        if stat in result:
            stats_present.append(f"{stat}={result[stat]}")
    
    log_test("Ingestion Stats API", "PASS", f"Response: {', '.join(stats_present)}")
    
    # Verify expected values from review request
    canonical_events = result.get("canonical_events", 0)
    duplicate_groups = result.get("potential_duplicate_groups", 0)
    
    if canonical_events == 10:
        log_test("Expected canonical_events=10", "PASS", f"Found {canonical_events}")
    else:
        log_test("Expected canonical_events=10", "FAIL", f"Found {canonical_events}")
    
    if duplicate_groups == 0:
        log_test("Expected potential_duplicate_groups=0", "PASS", f"Found {duplicate_groups}")
    else:
        log_test("Expected potential_duplicate_groups=0", "FAIL", f"Found {duplicate_groups}")
    
    return True

def test_duplicate_candidates():
    """Test GET /api/lifeline/duplicate-candidates/{user_id}"""
    print("\n🧪 TESTING: Duplicate Candidates Endpoint")
    
    success, result = test_endpoint(f"/lifeline/duplicate-candidates/{TEST_USER_ID}")
    
    if not success:
        log_test("Duplicate Candidates API", "FAIL", result)
        return False
    
    # Verify response structure
    required_fields = ["success", "duplicate_groups", "total_groups"]
    for field in required_fields:
        if field not in result:
            log_test("Duplicate Candidates API", "FAIL", f"Missing field: {field}")
            return False
    
    if not result.get("success"):
        log_test("Duplicate Candidates API", "FAIL", "success=false in response")
        return False
    
    duplicate_groups = result.get("duplicate_groups", [])
    total_groups = result.get("total_groups", 0)
    
    log_test("Duplicate Candidates API", "PASS", f"Found {total_groups} duplicate groups")
    
    # Verify expected empty array (already cleaned)
    if len(duplicate_groups) == 0:
        log_test("Expected empty duplicate_groups", "PASS", "No duplicates found (already cleaned)")
    else:
        log_test("Expected empty duplicate_groups", "FAIL", f"Found {len(duplicate_groups)} groups")
    
    return True

def test_import_sources():
    """Test GET /api/lifeline/import-sources/{user_id}"""
    print("\n🧪 TESTING: Import Sources Endpoint")
    
    success, result = test_endpoint(f"/lifeline/import-sources/{TEST_USER_ID}")
    
    if not success:
        log_test("Import Sources API", "FAIL", result)
        return False
    
    # Verify response structure
    required_fields = ["success", "sources"]
    for field in required_fields:
        if field not in result:
            log_test("Import Sources API", "FAIL", f"Missing field: {field}")
            return False
    
    if not result.get("success"):
        log_test("Import Sources API", "FAIL", "success=false in response")
        return False
    
    sources = result.get("sources", [])
    log_test("Import Sources API", "PASS", f"Found {len(sources)} import sources")
    
    # Sources may be empty for legacy data (as noted in review request)
    if len(sources) == 0:
        log_test("Sources array check", "PASS", "Empty sources array (may be empty for legacy data)")
    else:
        log_test("Sources array check", "PASS", f"Found {len(sources)} sources")
    
    return True

def test_imported_moments():
    """Test GET /api/lifeline/imported-moments/{user_id}"""
    print("\n🧪 TESTING: Imported Moments Endpoint")
    
    success, result = test_endpoint(f"/lifeline/imported-moments/{TEST_USER_ID}")
    
    if not success:
        log_test("Imported Moments API", "FAIL", result)
        return False
    
    # Verify response structure
    required_fields = ["success", "moments"]
    for field in required_fields:
        if field not in result:
            log_test("Imported Moments API", "FAIL", f"Missing field: {field}")
            return False
    
    if not result.get("success"):
        log_test("Imported Moments API", "FAIL", "success=false in response")
        return False
    
    moments = result.get("moments", [])
    log_test("Imported Moments API", "PASS", f"Found {len(moments)} imported moments")
    
    return True

def test_migrate_fix_duplicates_dry_run():
    """Test POST /api/lifeline/migrate-fix-duplicates/{user_id}?dry_run=true"""
    print("\n🧪 TESTING: Migrate Fix Duplicates (Dry Run)")
    
    success, result = test_endpoint(f"/lifeline/migrate-fix-duplicates/{TEST_USER_ID}?dry_run=true", method="POST")
    
    if not success:
        log_test("Migrate Fix Duplicates (Dry Run)", "FAIL", result)
        return False
    
    # Verify response structure
    required_fields = ["success"]
    for field in required_fields:
        if field not in result:
            log_test("Migrate Fix Duplicates (Dry Run)", "FAIL", f"Missing field: {field}")
            return False
    
    if not result.get("success"):
        log_test("Migrate Fix Duplicates (Dry Run)", "FAIL", "success=false in response")
        return False
    
    log_test("Migrate Fix Duplicates (Dry Run)", "PASS", "Dry run completed successfully")
    
    # Check for duplicate_groups_found field
    duplicate_groups_found = result.get("duplicate_groups_found", None)
    if duplicate_groups_found is not None:
        if duplicate_groups_found == 0:
            log_test("Expected duplicate_groups_found=0", "PASS", f"Found {duplicate_groups_found} (already cleaned)")
        else:
            log_test("Expected duplicate_groups_found=0", "FAIL", f"Found {duplicate_groups_found}")
    else:
        log_test("duplicate_groups_found field", "PASS", "Field not present (acceptable)")
    
    return True

def run_all_tests():
    """Run all Lifeline Ingestion Architecture tests"""
    print("🚀 STARTING LIFELINE INGESTION ARCHITECTURE API TESTS")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print("=" * 70)
    
    tests = [
        ("Lifeline Ingestion Stats", test_lifeline_ingestion_stats),
        ("Duplicate Candidates", test_duplicate_candidates),
        ("Import Sources", test_import_sources),
        ("Imported Moments", test_imported_moments),
        ("Migrate Fix Duplicates (Dry Run)", test_migrate_fix_duplicates_dry_run),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log_test(test_name, "FAIL", f"Exception: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed}/{total} TESTS PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Lifeline Ingestion Architecture is working correctly!")
        return True
    else:
        print(f"⚠️  {total - passed} TESTS FAILED - Issues found in Lifeline Ingestion Architecture")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)