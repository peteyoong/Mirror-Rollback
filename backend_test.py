#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror
Tests the complete registration + onboarding + astrology compute flow
AND the specific Add/Edit Birth Details flow as requested
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://reflect-personal.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def assert_true(self, condition, message):
        if condition:
            self.passed += 1
            print(f"✅ {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"❌ {message}")
            
    def assert_equal(self, actual, expected, message):
        if actual == expected:
            self.passed += 1
            print(f"✅ {message}")
        else:
            self.failed += 1
            error_msg = f"{message} - Expected: {expected}, Got: {actual}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            
    def assert_in(self, item, container, message):
        if item in container:
            self.passed += 1
            print(f"✅ {message}")
        else:
            self.failed += 1
            error_msg = f"{message} - '{item}' not found in {container}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")

def test_registration_onboarding_astrology_flow():
    """Test the complete flow: register -> login -> onboarding with birth data -> verify astrology computation"""
    
    results = TestResults()
    
    print("🧪 Testing Registration + Onboarding + Astrology Compute Flow")
    print(f"Backend URL: {API_BASE}")
    print("="*60)
    
    # Test data
    test_email = "flowtest2@example.com"  # Different email to avoid conflicts
    test_password = "Test123!"
    test_name = "Flow Test User"
    
    # Birth data for astrology computation
    birth_data = {
        "birth_datetime_local": "1990-05-15T10:30:00",
        "tz_offset_minutes": -300,  # EST
        "latitude": 40.7128,        # New York
        "longitude": -74.0060
    }
    
    # Onboarding answers
    onboarding_answers = {
        "relationship_with_self": "I'm curious about understanding myself better and growing",
        "reflection_style": "I like to look for patterns and connections in my experiences",
        "desired_depth": "deep",
        "uncertainty_relationship": "I find uncertainty challenging but I'm learning to be more comfortable with it",
        "intention": "I want more clarity about my life direction and purpose"
    }
    
    # Combine onboarding answers with birth data
    complete_onboarding = {**onboarding_answers, **birth_data}
    
    token = None
    user_id = None
    
    try:
        # Step 1: Register new user
        print("\n1️⃣ Testing User Registration")
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        results.assert_equal(response.status_code, 200, "Registration returns 200 status")
        
        if response.status_code == 200:
            register_result = response.json()
            results.assert_in("token", register_result, "Registration response contains token")
            results.assert_in("user", register_result, "Registration response contains user")
            
            if "token" in register_result:
                token = register_result["token"]
                user_data = register_result.get("user", {})
                user_id = user_data.get("id")
                results.assert_true(bool(user_id), "User ID is present in registration response")
                results.assert_equal(user_data.get("email"), test_email, "User email matches")
                results.assert_equal(user_data.get("name"), test_name, "User name matches")
                results.assert_equal(user_data.get("onboarding_completed"), False, "Onboarding initially incomplete")
        else:
            print(f"Registration failed: {response.text}")
            return results
            
        # Step 2: Login to verify credentials
        print("\n2️⃣ Testing User Login")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        results.assert_equal(response.status_code, 200, "Login returns 200 status")
        
        if response.status_code == 200:
            login_result = response.json()
            results.assert_in("token", login_result, "Login response contains token")
            results.assert_in("user", login_result, "Login response contains user")
            
            # Update token from login (should be same as registration)
            if "token" in login_result:
                token = login_result["token"]
        else:
            print(f"Login failed: {response.text}")
            return results
            
        # Step 3: Complete onboarding with birth data
        print("\n3️⃣ Testing Onboarding Complete with Birth Data")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{API_BASE}/onboarding/complete", json=complete_onboarding, headers=headers)
        results.assert_equal(response.status_code, 200, "Onboarding complete returns 200 status")
        
        if response.status_code == 200:
            onboarding_result = response.json()
            results.assert_equal(onboarding_result.get("success"), True, "Onboarding completion successful")
        else:
            print(f"Onboarding failed: {response.text}")
            return results
            
        # Step 4: Verify user data and astrology computation
        print("\n4️⃣ Testing User Data Verification (GET /auth/me)")
        
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        results.assert_equal(response.status_code, 200, "Auth/me returns 200 status")
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Verify onboarding completion
            results.assert_equal(user_data.get("onboarding_completed"), True, "Onboarding marked as completed")
            
            # Verify onboarding answers are saved
            saved_answers = user_data.get("onboarding_answers", {})
            results.assert_true(bool(saved_answers), "Onboarding answers are saved")
            results.assert_equal(saved_answers.get("relationship_with_self"), onboarding_answers["relationship_with_self"], "Relationship with self answer saved correctly")
            results.assert_equal(saved_answers.get("desired_depth"), onboarding_answers["desired_depth"], "Desired depth answer saved correctly")
            
            # Verify birth data is saved
            birth_data_saved = user_data.get("birth_data", {})
            results.assert_true(bool(birth_data_saved), "Birth data is saved")
            results.assert_equal(birth_data_saved.get("birth_datetime_local"), birth_data["birth_datetime_local"], "Birth datetime saved correctly")
            results.assert_equal(birth_data_saved.get("tz_offset_minutes"), birth_data["tz_offset_minutes"], "Timezone offset saved correctly")
            results.assert_equal(birth_data_saved.get("latitude"), birth_data["latitude"], "Latitude saved correctly")
            results.assert_equal(birth_data_saved.get("longitude"), birth_data["longitude"], "Longitude saved correctly")
            
            # Verify astrology computation
            computed_profile = user_data.get("computed_profile", {})
            results.assert_true(bool(computed_profile), "Computed profile exists")
            
            astrology_profile = computed_profile.get("astrology", {})
            results.assert_true(bool(astrology_profile), "Astrology profile exists in computed_profile")
            
            if astrology_profile:
                # Verify ayanamsa
                results.assert_equal(astrology_profile.get("ayanamsa"), "FAGAN_BRADLEY", "Ayanamsa is FAGAN_BRADLEY (sidereal)")
                
                # Verify positions exist
                positions = astrology_profile.get("positions", {})
                results.assert_true(bool(positions), "Astrology positions exist")
                
                # Verify Sun position
                sun_pos = positions.get("sun", {})
                results.assert_true(bool(sun_pos), "Sun position exists")
                results.assert_in("sign", sun_pos, "Sun position has sign")
                results.assert_in("degree", sun_pos, "Sun position has degree")
                results.assert_in("formatted", sun_pos, "Sun position has formatted string")
                
                if sun_pos.get("sign"):
                    print(f"   Sun: {sun_pos.get('formatted', sun_pos.get('sign'))}")
                
                # Verify Moon position
                moon_pos = positions.get("moon", {})
                results.assert_true(bool(moon_pos), "Moon position exists")
                results.assert_in("sign", moon_pos, "Moon position has sign")
                results.assert_in("degree", moon_pos, "Moon position has degree")
                results.assert_in("formatted", moon_pos, "Moon position has formatted string")
                
                if moon_pos.get("sign"):
                    print(f"   Moon: {moon_pos.get('formatted', moon_pos.get('sign'))}")
                
                # Verify Ascendant position
                asc_pos = positions.get("ascendant", {})
                results.assert_true(bool(asc_pos), "Ascendant position exists")
                results.assert_in("sign", asc_pos, "Ascendant position has sign")
                results.assert_in("degree", asc_pos, "Ascendant position has degree")
                results.assert_in("formatted", asc_pos, "Ascendant position has formatted string")
                
                if asc_pos.get("sign"):
                    print(f"   Ascendant: {asc_pos.get('formatted', asc_pos.get('sign'))}")
                
                # Verify computed_at timestamp
                results.assert_in("computed_at", astrology_profile, "Astrology profile has computed_at timestamp")
                
                # Verify birth data is also in astrology profile
                results.assert_equal(astrology_profile.get("birth_datetime_local"), birth_data["birth_datetime_local"], "Birth datetime in astrology profile matches")
                results.assert_equal(astrology_profile.get("latitude"), birth_data["latitude"], "Latitude in astrology profile matches")
                results.assert_equal(astrology_profile.get("longitude"), birth_data["longitude"], "Longitude in astrology profile matches")
                
        else:
            print(f"Auth/me failed: {response.text}")
            return results
            
        # Step 5: Test that astrology data persists on subsequent calls
        print("\n5️⃣ Testing Astrology Data Persistence")
        
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        results.assert_equal(response.status_code, 200, "Second auth/me call returns 200 status")
        
        if response.status_code == 200:
            user_data_2 = response.json()
            computed_profile_2 = user_data_2.get("computed_profile", {})
            astrology_profile_2 = computed_profile_2.get("astrology", {})
            
            results.assert_true(bool(astrology_profile_2), "Astrology profile persists on second call")
            
            if astrology_profile_2:
                positions_2 = astrology_profile_2.get("positions", {})
                results.assert_true(bool(positions_2), "Astrology positions persist")
                results.assert_true(bool(positions_2.get("sun")), "Sun position persists")
                results.assert_true(bool(positions_2.get("moon")), "Moon position persists")
                results.assert_true(bool(positions_2.get("ascendant")), "Ascendant position persists")
        
        print("\n✅ Complete Registration + Onboarding + Astrology Compute Flow Test Completed")
        
    except requests.exceptions.RequestException as e:
        results.failed += 1
        results.errors.append(f"Network error: {str(e)}")
        print(f"❌ Network error: {str(e)}")
    except Exception as e:
        results.failed += 1
        results.errors.append(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
    
    return results

def test_birth_details_flow():
    """Test the specific Add/Edit Birth Details flow as requested in the review"""
    print("\n" + "="*80)
    print("🎯 TESTING BIRTH DETAILS FLOW (Review Request)")
    print("="*80)
    
    results = TestResults()
    
    # Test data as specified in the review request
    test_email = "editbirth@test.com"
    test_password = "Test123!"
    test_name = "Birth Details Test User"
    
    birth_data = {
        "birth_datetime_local": "1985-03-20T14:30:00",
        "tz_offset_minutes": -300,
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    
    astrology_data = {
        "birth_datetime_local": "1985-03-20T14:30:00",
        "tz_offset_minutes": -300,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "ayanamsa": "FAGAN_BRADLEY"
    }
    
    token = None
    
    try:
        # Step 1: Register new user
        print("\n1️⃣ REGISTERING NEW USER")
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        results.assert_equal(response.status_code, 200, "User registration returns 200 status")
        
        if response.status_code == 200:
            register_result = response.json()
            results.assert_in("token", register_result, "Registration response contains token")
            results.assert_in("user", register_result, "Registration response contains user object")
            
            if "user" in register_result:
                user_data = register_result["user"]
                results.assert_equal(user_data.get("email"), test_email, "Registration user email matches")
        
        # Step 2: Login to get token
        print("\n2️⃣ LOGGING IN TO GET TOKEN")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        results.assert_equal(response.status_code, 200, "Login returns 200 status")
        
        if response.status_code == 200:
            login_result = response.json()
            results.assert_in("token", login_result, "Login response contains token")
            if "token" in login_result:
                token = login_result["token"]
                print(f"   ✅ Token obtained: {token[:20]}...")
        
        if not token:
            print("❌ Cannot proceed without authentication token")
            return results
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Save Birth Data (Test 1 from review request)
        print("\n3️⃣ TEST 1 - SAVE BIRTH DATA")
        print(f"   POST /api/user/birth-data")
        print(f"   Data: {json.dumps(birth_data, indent=2)}")
        
        response = requests.post(f"{API_BASE}/user/birth-data", json=birth_data, headers=headers)
        results.assert_equal(response.status_code, 200, "Save birth data returns 200 status")
        
        if response.status_code == 200:
            birth_result = response.json()
            results.assert_equal(birth_result.get("success"), True, "Birth data save returns success: true")
            results.assert_in("birth_data", birth_result, "Birth data response contains birth_data object")
            
            if "birth_data" in birth_result:
                saved_birth_data = birth_result["birth_data"]
                results.assert_equal(
                    saved_birth_data.get("birth_datetime_local"), 
                    birth_data["birth_datetime_local"],
                    "Birth datetime saved correctly"
                )
                results.assert_equal(
                    saved_birth_data.get("latitude"), 
                    birth_data["latitude"],
                    "Birth latitude saved correctly"
                )
                results.assert_equal(
                    saved_birth_data.get("longitude"), 
                    birth_data["longitude"],
                    "Birth longitude saved correctly"
                )
                print(f"   ✅ Birth data saved: {saved_birth_data.get('birth_datetime_local')} at ({saved_birth_data.get('latitude')}, {saved_birth_data.get('longitude')})")
        else:
            print(f"   ❌ Response: {response.text}")
        
        # Step 4: Compute Astrology (Test 2 from review request)
        print("\n4️⃣ TEST 2 - COMPUTE ASTROLOGY")
        print(f"   POST /api/computed-profile/astrology")
        print(f"   Data: {json.dumps(astrology_data, indent=2)}")
        
        response = requests.post(f"{API_BASE}/computed-profile/astrology", json=astrology_data, headers=headers)
        results.assert_equal(response.status_code, 200, "Compute astrology returns 200 status")
        
        if response.status_code == 200:
            astrology_result = response.json()
            results.assert_equal(astrology_result.get("has_profile"), True, "Astrology computation returns has_profile: true")
            
            if "profile" in astrology_result and astrology_result["profile"]:
                profile = astrology_result["profile"]
                results.assert_in("positions", profile, "Astrology profile contains positions")
                
                if "positions" in profile:
                    positions = profile["positions"]
                    
                    # Check for required positions (sun, moon, ascendant)
                    required_positions = ["sun", "moon", "ascendant"]
                    for pos in required_positions:
                        results.assert_in(pos, positions, f"Astrology profile contains {pos} position")
                        
                        if pos in positions:
                            pos_data = positions[pos]
                            results.assert_in("sign", pos_data, f"{pos.capitalize()} position has sign")
                            results.assert_in("degree", pos_data, f"{pos.capitalize()} position has degree")
                            results.assert_in("formatted", pos_data, f"{pos.capitalize()} position has formatted string")
                            
                            if "formatted" in pos_data:
                                print(f"   ✅ {pos_data.get('name', pos.capitalize())}: {pos_data['formatted']}")
        else:
            print(f"   ❌ Response: {response.text}")
        
        # Step 5: Verify User Record (Test 3 from review request)
        print("\n5️⃣ TEST 3 - VERIFY USER RECORD")
        print(f"   GET /api/auth/me")
        
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        results.assert_equal(response.status_code, 200, "Get user profile returns 200 status")
        
        if response.status_code == 200:
            user_profile = response.json()
            
            # Verify birth_data is saved
            results.assert_in("birth_data", user_profile, "User profile contains birth_data")
            
            if "birth_data" in user_profile and user_profile["birth_data"]:
                birth_data_in_profile = user_profile["birth_data"]
                results.assert_equal(
                    birth_data_in_profile.get("birth_datetime_local"), 
                    birth_data["birth_datetime_local"],
                    "Birth data persisted correctly in user profile"
                )
                print(f"   ✅ Birth data in user profile: {birth_data_in_profile.get('birth_datetime_local')}")
            
            # Verify computed_profile.astrology exists
            results.assert_in("computed_profile", user_profile, "User profile contains computed_profile")
            
            if "computed_profile" in user_profile and user_profile["computed_profile"]:
                computed_profile = user_profile["computed_profile"]
                results.assert_in("astrology", computed_profile, "Computed profile contains astrology")
                
                if "astrology" in computed_profile and computed_profile["astrology"]:
                    astrology_profile = computed_profile["astrology"]
                    results.assert_in("positions", astrology_profile, "User astrology profile contains positions")
                    
                    if "positions" in astrology_profile:
                        positions = astrology_profile["positions"]
                        for pos in ["sun", "moon", "ascendant"]:
                            results.assert_in(pos, positions, f"User astrology profile contains {pos}")
                        print(f"   ✅ Astrology profile saved in user record with {len(positions)} positions")
        else:
            print(f"   ❌ Response: {response.text}")
        
        print("\n✅ Birth Details Flow Test Completed")
        
    except requests.exceptions.RequestException as e:
        results.failed += 1
        results.errors.append(f"Network error: {str(e)}")
        print(f"❌ Network error: {str(e)}")
    except Exception as e:
        results.failed += 1
        results.errors.append(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
    
    return results

def main():
    """Run all tests"""
    print("🚀 Starting Backend API Tests for Project Mirror")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run the specific birth details flow test (as requested in review)
    birth_results = test_birth_details_flow()
    
    # Run the main test flow
    main_results = test_registration_onboarding_astrology_flow()
    
    # Combine results
    total_passed = birth_results.passed + main_results.passed
    total_failed = birth_results.failed + main_results.failed
    all_errors = birth_results.errors + main_results.errors
    
    # Print combined summary
    print("\n" + "="*80)
    print("📊 COMBINED TEST SUMMARY")
    print("="*80)
    print(f"Total Tests Passed: {total_passed}")
    print(f"Total Tests Failed: {total_failed}")
    
    if all_errors:
        print(f"\nErrors ({len(all_errors)}):")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
    
    # Exit with appropriate code
    if total_failed > 0:
        print(f"\n💥 {total_failed} tests failed!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()