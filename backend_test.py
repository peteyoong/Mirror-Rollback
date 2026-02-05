#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror
Focus: Numerology Full Name Gate Fix Testing
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://mirror-daily.preview.emergentagent.com/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_numerology_full_name_gate():
    """
    Test the Numerology Full Name Gate fix as specified in the review request.
    
    ACCEPTANCE TEST - New User Flow:
    1. Create a new user (without numerology_full_name)
    2. Calculate chart for the new user
    3. Get numerology summary - verify locked state
    4. Unlock with full birth name
    5. Get numerology summary again - verify unlocked state
    """
    
    log_test("🔢 STARTING NUMEROLOGY FULL NAME GATE TEST")
    
    # Step 1: Create a new user (without numerology_full_name)
    log_test("Step 1: Creating new user without numerology_full_name")
    
    user_data = {
        "name": "Numerology Gate Test",
        "birth_date": "1995-08-22",
        "birth_time": "10:00",
        "city": "Chicago",
        "country": "USA",
        "timezone": "America/Chicago",
        "latitude": 41.8781,
        "longitude": -87.6298
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/users", json=user_data, timeout=30)
        log_test(f"POST /api/users - Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test(f"❌ FAILED: User creation failed - {response.text}")
            return False
            
        user_response = response.json()
        new_user_id = user_response.get("id")
        
        if not new_user_id:
            log_test(f"❌ FAILED: No user ID returned - {user_response}")
            return False
            
        log_test(f"✅ User created successfully - ID: {new_user_id}")
        
    except Exception as e:
        log_test(f"❌ FAILED: User creation error - {e}")
        return False
    
    # Step 2: Calculate chart for the new user
    log_test("Step 2: Calculating chart for new user")
    
    try:
        chart_data = {"user_id": new_user_id}
        response = requests.post(f"{BACKEND_URL}/charts/calculate", json=chart_data, timeout=60)
        log_test(f"POST /api/charts/calculate - Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test(f"❌ FAILED: Chart calculation failed - {response.text}")
            return False
            
        chart_response = response.json()
        log_test(f"✅ Chart calculated successfully")
        
    except Exception as e:
        log_test(f"❌ FAILED: Chart calculation error - {e}")
        return False
    
    # Step 3: Get numerology summary - verify locked state
    log_test("Step 3: Getting numerology summary (should be locked)")
    
    try:
        response = requests.get(f"{BACKEND_URL}/numerology/summary/{new_user_id}", timeout=30)
        log_test(f"GET /api/numerology/summary/{new_user_id} - Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test(f"❌ FAILED: Numerology summary failed - {response.text}")
            return False
            
        numerology_response = response.json()
        log_test(f"Numerology response: {json.dumps(numerology_response, indent=2)}")
        
        # Step 4: VERIFY locked state
        log_test("Step 4: Verifying locked state")
        
        core_numbers = numerology_response.get("core_numbers", {})
        unlock_prompt = numerology_response.get("unlock_prompt")
        
        # Check Life Path and Birthday numbers are present
        life_path = core_numbers.get("life_path")
        if not life_path or life_path == "locked":
            log_test(f"❌ FAILED: Life Path should be present, got: {life_path}")
            return False
        log_test(f"✅ Life Path number present: {life_path}")
        
        # Check Expression and Soul Urge are locked
        expression = core_numbers.get("expression")
        soul_urge = core_numbers.get("soul_urge")
        
        if expression != "locked":
            log_test(f"❌ FAILED: Expression should be 'locked', got: {expression}")
            return False
        log_test(f"✅ Expression is locked: {expression}")
        
        if soul_urge != "locked":
            log_test(f"❌ FAILED: Soul Urge should be 'locked', got: {soul_urge}")
            return False
        log_test(f"✅ Soul Urge is locked: {soul_urge}")
        
        # Check unlock_prompt is present
        if not unlock_prompt:
            log_test(f"❌ FAILED: unlock_prompt should be present, got: {unlock_prompt}")
            return False
        log_test(f"✅ Unlock prompt present: {unlock_prompt}")
        
    except Exception as e:
        log_test(f"❌ FAILED: Numerology summary error - {e}")
        return False
    
    # Step 5: Unlock with full birth name
    log_test("Step 5: Unlocking with full birth name")
    
    try:
        unlock_data = {"full_birth_name": "John Robert Williams"}
        response = requests.post(f"{BACKEND_URL}/numerology/unlock-name/{new_user_id}", json=unlock_data, timeout=30)
        log_test(f"POST /api/numerology/unlock-name/{new_user_id} - Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test(f"❌ FAILED: Name unlock failed - {response.text}")
            return False
            
        unlock_response = response.json()
        log_test(f"✅ Name unlocked successfully: {unlock_response}")
        
    except Exception as e:
        log_test(f"❌ FAILED: Name unlock error - {e}")
        return False
    
    # Step 6: Get numerology summary again - verify unlocked state
    log_test("Step 6: Getting numerology summary again (should be unlocked)")
    
    try:
        response = requests.get(f"{BACKEND_URL}/numerology/summary/{new_user_id}", timeout=30)
        log_test(f"GET /api/numerology/summary/{new_user_id} - Status: {response.status_code}")
        
        if response.status_code != 200:
            log_test(f"❌ FAILED: Numerology summary after unlock failed - {response.text}")
            return False
            
        unlocked_response = response.json()
        log_test(f"Unlocked numerology response: {json.dumps(unlocked_response, indent=2)}")
        
        # Step 7: VERIFY unlocked state
        log_test("Step 7: Verifying unlocked state")
        
        core_numbers = unlocked_response.get("core_numbers", {})
        unlock_prompt = unlocked_response.get("unlock_prompt")
        
        # Check Expression and Soul Urge are now actual numbers (not "locked")
        expression = core_numbers.get("expression")
        soul_urge = core_numbers.get("soul_urge")
        
        if expression == "locked" or not expression:
            log_test(f"❌ FAILED: Expression should be unlocked, got: {expression}")
            return False
        log_test(f"✅ Expression is unlocked: {expression}")
        
        if soul_urge == "locked" or not soul_urge:
            log_test(f"❌ FAILED: Soul Urge should be unlocked, got: {soul_urge}")
            return False
        log_test(f"✅ Soul Urge is unlocked: {soul_urge}")
        
        # Check unlock_prompt is now null
        if unlock_prompt is not None:
            log_test(f"❌ FAILED: unlock_prompt should be null after unlock, got: {unlock_prompt}")
            return False
        log_test(f"✅ Unlock prompt is null: {unlock_prompt}")
        
    except Exception as e:
        log_test(f"❌ FAILED: Numerology summary after unlock error - {e}")
        return False
    
    log_test("🎉 NUMEROLOGY FULL NAME GATE TEST COMPLETED SUCCESSFULLY")
    return True

def test_critical_invariant():
    """
    Test the critical invariant: New users WITHOUT numerology_full_name 
    MUST have expression/soul_urge/personality = "locked"
    NO fallback to user.name allowed
    """
    
    log_test("🔒 TESTING CRITICAL INVARIANT")
    
    # Create another user to verify the invariant
    user_data = {
        "name": "Test User With Name",  # This should NOT be used as fallback
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "city": "New York",
        "country": "USA", 
        "timezone": "America/New_York",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    
    try:
        # Create user
        response = requests.post(f"{BACKEND_URL}/users", json=user_data, timeout=30)
        if response.status_code != 200:
            log_test(f"❌ FAILED: User creation failed - {response.text}")
            return False
            
        user_response = response.json()
        user_id = user_response.get("id")
        
        # Calculate chart
        chart_data = {"user_id": user_id}
        response = requests.post(f"{BACKEND_URL}/charts/calculate", json=chart_data, timeout=60)
        if response.status_code != 200:
            log_test(f"❌ FAILED: Chart calculation failed - {response.text}")
            return False
        
        # Get numerology summary
        response = requests.get(f"{BACKEND_URL}/numerology/summary/{user_id}", timeout=30)
        if response.status_code != 200:
            log_test(f"❌ FAILED: Numerology summary failed - {response.text}")
            return False
            
        numerology_response = response.json()
        core_numbers = numerology_response.get("core_numbers", {})
        
        # CRITICAL CHECK: Even though user has a name, expression/soul_urge should be locked
        expression = core_numbers.get("expression")
        soul_urge = core_numbers.get("soul_urge")
        
        if expression != "locked":
            log_test(f"❌ CRITICAL INVARIANT VIOLATED: Expression should be 'locked' for new user, got: {expression}")
            return False
            
        if soul_urge != "locked":
            log_test(f"❌ CRITICAL INVARIANT VIOLATED: Soul Urge should be 'locked' for new user, got: {soul_urge}")
            return False
            
        log_test(f"✅ CRITICAL INVARIANT VERIFIED: New user has locked expression/soul_urge despite having user.name")
        
    except Exception as e:
        log_test(f"❌ FAILED: Critical invariant test error - {e}")
        return False
    
    return True

def main():
    """Run all numerology tests"""
    log_test("🚀 STARTING NUMEROLOGY FULL NAME GATE TESTING")
    log_test(f"Backend URL: {BACKEND_URL}")
    
    all_tests_passed = True
    
    # Test 1: Full numerology gate flow
    if not test_numerology_full_name_gate():
        all_tests_passed = False
    
    # Test 2: Critical invariant
    if not test_critical_invariant():
        all_tests_passed = False
    
    # Summary
    if all_tests_passed:
        log_test("🎉 ALL NUMEROLOGY TESTS PASSED")
        return 0
    else:
        log_test("❌ SOME NUMEROLOGY TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())