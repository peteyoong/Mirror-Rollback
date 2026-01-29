#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror
Tests the complete registration + onboarding + astrology compute flow
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
    test_email = "flowtest@example.com"
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

def main():
    """Run all tests"""
    print("🚀 Starting Backend API Tests for Project Mirror")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run the main test flow
    results = test_registration_onboarding_astrology_flow()
    
    # Print final summary
    results.print_summary()
    
    # Exit with appropriate code
    if results.failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()