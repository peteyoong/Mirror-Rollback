#!/usr/bin/env python3
"""
Backend Testing Script for Journal ↔ Timeline Connection Feature
Tests the integration between journal entries and timeline phases.
"""

import requests
import json
import sys
from datetime import datetime
import os

# Get backend URL from environment
BACKEND_URL = "https://phase-mirror-reflect.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

def log_test(test_name, status, details=""):
    """Log test results with consistent formatting"""
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"{status_symbol} {test_name}")
    if details:
        print(f"   {details}")
    print()

def test_journal_timeline_connection():
    """Test the Journal ↔ Timeline Connection feature backend endpoints"""
    
    print("🧪 TESTING: Journal ↔ Timeline Connection Feature Backend Endpoints")
    print("=" * 80)
    print()
    
    # Test data for journal entry with phase information
    test_journal_entry = {
        "user_id": TEST_USER_ID,
        "content": "Testing journal entry with timeline phase data. Today I'm reflecting on some choices I need to make.",
        "phase_id": "q1",
        "phase_name": "Recognition"
    }
    
    # =========================================================================
    # TEST 1: POST /api/journal with phase data
    # =========================================================================
    print("TEST 1: POST /api/journal with phase data")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/journal",
            json=test_journal_entry,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ["id", "content", "themes", "created_at", "phase_id", "phase_name"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                log_test("POST /api/journal structure", "FAIL", f"Missing fields: {missing_fields}")
                return False
            
            # Verify phase data is included
            if data.get("phase_id") == "q1" and data.get("phase_name") == "Recognition":
                log_test("POST /api/journal with phase data", "PASS", 
                        f"Entry created with ID: {data['id']}, phase_id: {data['phase_id']}, phase_name: {data['phase_name']}")
                created_entry_id = data["id"]
            else:
                log_test("POST /api/journal phase data", "FAIL", 
                        f"Phase data not properly saved. Got phase_id: {data.get('phase_id')}, phase_name: {data.get('phase_name')}")
                return False
                
        else:
            log_test("POST /api/journal", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("POST /api/journal", "FAIL", f"Exception: {str(e)}")
        return False
    
    # =========================================================================
    # TEST 2: GET /api/journal/{user_id} returns phase data
    # =========================================================================
    print("TEST 2: GET /api/journal/{user_id} returns phase data")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/journal/{TEST_USER_ID}",
            timeout=30
        )
        
        if response.status_code == 200:
            entries = response.json()
            
            if not isinstance(entries, list):
                log_test("GET /api/journal/{user_id} format", "FAIL", "Response is not a list")
                return False
            
            if len(entries) == 0:
                log_test("GET /api/journal/{user_id}", "FAIL", "No journal entries found")
                return False
            
            # Find our test entry and verify phase data
            test_entry_found = False
            phase_data_entries = 0
            
            for entry in entries:
                # Check if this entry has phase data
                if entry.get("phase_id") and entry.get("phase_name"):
                    phase_data_entries += 1
                
                # Check if this is our test entry
                if (entry.get("content") == test_journal_entry["content"] and 
                    entry.get("phase_id") == "q1" and 
                    entry.get("phase_name") == "Recognition"):
                    test_entry_found = True
            
            if test_entry_found:
                log_test("GET /api/journal/{user_id} phase data", "PASS", 
                        f"Found {phase_data_entries} entries with phase data, including our test entry")
            else:
                log_test("GET /api/journal/{user_id} phase data", "FAIL", 
                        f"Test entry not found or missing phase data. Found {phase_data_entries} entries with phase data")
                return False
                
        else:
            log_test("GET /api/journal/{user_id}", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/journal/{user_id}", "FAIL", f"Exception: {str(e)}")
        return False
    
    # =========================================================================
    # TEST 3: GET /api/journal/{user_id}/by-phase/{phase_id}
    # =========================================================================
    print("TEST 3: GET /api/journal/{user_id}/by-phase/{phase_id}")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/journal/{TEST_USER_ID}/by-phase/q1",
            timeout=30
        )
        
        if response.status_code == 200:
            entries = response.json()
            
            if not isinstance(entries, list):
                log_test("GET /api/journal/{user_id}/by-phase/{phase_id} format", "FAIL", "Response is not a list")
                return False
            
            # Verify all entries have the correct phase_id
            correct_phase_entries = 0
            test_entry_found = False
            
            for entry in entries:
                if entry.get("phase_id") == "q1":
                    correct_phase_entries += 1
                    
                    # Check if this is our test entry
                    if (entry.get("content") == test_journal_entry["content"] and 
                        entry.get("phase_name") == "Recognition"):
                        test_entry_found = True
                else:
                    log_test("GET /api/journal by-phase filtering", "FAIL", 
                            f"Entry with wrong phase_id found: {entry.get('phase_id')}")
                    return False
            
            if len(entries) > 0 and correct_phase_entries == len(entries):
                log_test("GET /api/journal/{user_id}/by-phase/{phase_id}", "PASS", 
                        f"Found {len(entries)} entries for phase 'q1', all correctly filtered")
                
                if test_entry_found:
                    log_test("Test entry in by-phase results", "PASS", "Our test entry found in phase-filtered results")
                else:
                    log_test("Test entry in by-phase results", "FAIL", "Our test entry not found in phase-filtered results")
                    return False
            else:
                log_test("GET /api/journal/{user_id}/by-phase/{phase_id}", "FAIL", 
                        f"Found {len(entries)} entries, {correct_phase_entries} with correct phase")
                return False
                
        else:
            log_test("GET /api/journal/{user_id}/by-phase/{phase_id}", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/journal/{user_id}/by-phase/{phase_id}", "FAIL", f"Exception: {str(e)}")
        return False
    
    # =========================================================================
    # TEST 4: Test with different phase (q2) to verify filtering works
    # =========================================================================
    print("TEST 4: Create entry with different phase and verify filtering")
    print("-" * 50)
    
    test_journal_entry_q2 = {
        "user_id": TEST_USER_ID,
        "content": "Testing journal entry with phase q2. This is about confronting difficult truths.",
        "phase_id": "q2",
        "phase_name": "Confrontation"
    }
    
    try:
        # Create entry with q2 phase
        response = requests.post(
            f"{BACKEND_URL}/journal",
            json=test_journal_entry_q2,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            # Now test that by-phase filtering works correctly
            response_q1 = requests.get(f"{BACKEND_URL}/journal/{TEST_USER_ID}/by-phase/q1", timeout=30)
            response_q2 = requests.get(f"{BACKEND_URL}/journal/{TEST_USER_ID}/by-phase/q2", timeout=30)
            
            if response_q1.status_code == 200 and response_q2.status_code == 200:
                entries_q1 = response_q1.json()
                entries_q2 = response_q2.json()
                
                # Verify q1 entries only have q1 phase
                q1_correct = all(entry.get("phase_id") == "q1" for entry in entries_q1)
                # Verify q2 entries only have q2 phase  
                q2_correct = all(entry.get("phase_id") == "q2" for entry in entries_q2)
                
                if q1_correct and q2_correct:
                    log_test("Phase filtering isolation", "PASS", 
                            f"q1 phase: {len(entries_q1)} entries, q2 phase: {len(entries_q2)} entries - no cross-contamination")
                else:
                    log_test("Phase filtering isolation", "FAIL", "Phase filtering not working correctly")
                    return False
            else:
                log_test("Phase filtering test", "FAIL", "Could not retrieve entries for phase comparison")
                return False
        else:
            log_test("Create q2 entry", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("Phase filtering test", "FAIL", f"Exception: {str(e)}")
        return False
    
    # =========================================================================
    # TEST 5: Test edge cases
    # =========================================================================
    print("TEST 5: Edge cases and error handling")
    print("-" * 50)
    
    try:
        # Test non-existent phase
        response = requests.get(f"{BACKEND_URL}/journal/{TEST_USER_ID}/by-phase/nonexistent", timeout=30)
        if response.status_code == 200:
            entries = response.json()
            if len(entries) == 0:
                log_test("Non-existent phase handling", "PASS", "Returns empty list for non-existent phase")
            else:
                log_test("Non-existent phase handling", "FAIL", f"Should return empty list, got {len(entries)} entries")
                return False
        else:
            log_test("Non-existent phase handling", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Test invalid user ID
        response = requests.get(f"{BACKEND_URL}/journal/invalid_user_id/by-phase/q1", timeout=30)
        if response.status_code == 200:
            entries = response.json()
            if len(entries) == 0:
                log_test("Invalid user ID handling", "PASS", "Returns empty list for invalid user ID")
            else:
                log_test("Invalid user ID handling", "FAIL", f"Should return empty list, got {len(entries)} entries")
                return False
        else:
            log_test("Invalid user ID handling", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("Edge cases test", "FAIL", f"Exception: {str(e)}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Journal ↔ Timeline Connection Backend Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print()
    
    success = test_journal_timeline_connection()
    
    print("=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED - Journal ↔ Timeline Connection feature is working correctly!")
        print()
        print("✅ VERIFIED FUNCTIONALITY:")
        print("   • POST /api/journal accepts and stores phase_id and phase_name")
        print("   • GET /api/journal/{user_id} returns entries with phase data")
        print("   • GET /api/journal/{user_id}/by-phase/{phase_id} filters entries by phase")
        print("   • Phase filtering works correctly with isolation between phases")
        print("   • Edge cases handled properly (non-existent phases, invalid users)")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - See details above")
        sys.exit(1)

if __name__ == "__main__":
    main()