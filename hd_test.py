#!/usr/bin/env python3
"""
Backend API Testing for Project Mirror - Human Design Profile APIs
Tests the Human Design Profile endpoints as requested in the review.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend env
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'http://localhost:8001')
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
            error_msg = f"{message} - {item} not found in {container}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")

async def register_test_user(session, email, password, name):
    """Register a new test user and return JWT token"""
    register_data = {
        "email": email,
        "password": password,
        "name": name
    }
    
    async with session.post(f"{API_BASE}/auth/register", json=register_data) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("token")
        else:
            error_text = await resp.text()
            raise Exception(f"Registration failed: {resp.status} - {error_text}")

async def test_human_design_profile_apis():
    """Test Human Design Profile APIs comprehensively"""
    results = TestResults()
    
    print("🧪 Testing Human Design Profile APIs")
    print("=" * 50)
    
    # Create test user with realistic data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"sarah.reflection.{timestamp}@example.com"
    test_password = "SecurePass123!"
    test_name = "Sarah Chen"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Register test user
            print(f"\n📝 Registering test user: {test_email}")
            token = await register_test_user(session, test_email, test_password, test_name)
            results.assert_true(token is not None, "User registration successful")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test 1: GET HD profile when none exists
            print(f"\n🔍 Test 1: GET HD profile (should return has_profile: false)")
            async with session.get(f"{API_BASE}/computed-profile/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "GET HD profile returns 200")
                data = await resp.json()
                results.assert_equal(data.get("has_profile"), False, "has_profile is false when no profile exists")
                results.assert_equal(data.get("profile"), None, "profile is None when no profile exists")
            
            # Test 2: POST HD profile - Save complete profile
            print(f"\n💾 Test 2: POST HD profile (save complete profile)")
            hd_profile_data = {
                "type": "Manifesting Generator",
                "strategy": "To Respond",
                "authority": "Sacral",
                "profile": "3/5",
                "definition": "Single Definition",
                "not_self_theme": "Frustration",
                "signature": "Satisfaction"
            }
            
            async with session.post(f"{API_BASE}/computed-profile/human-design", 
                                  json=hd_profile_data, headers=headers) as resp:
                results.assert_equal(resp.status, 200, "POST HD profile returns 200")
                data = await resp.json()
                results.assert_equal(data.get("success"), True, "POST returns success: true")
                
                # Verify saved profile data
                saved_profile = data.get("profile", {})
                results.assert_equal(saved_profile.get("type"), "Manifesting Generator", "Type saved correctly")
                results.assert_equal(saved_profile.get("strategy"), "To Respond", "Strategy saved correctly")
                results.assert_equal(saved_profile.get("authority"), "Sacral", "Authority saved correctly")
                results.assert_equal(saved_profile.get("profile"), "3/5", "Profile saved correctly")
                results.assert_equal(saved_profile.get("definition"), "Single Definition", "Definition saved correctly")
                results.assert_equal(saved_profile.get("not_self_theme"), "Frustration", "Not-self theme saved correctly")
                results.assert_equal(saved_profile.get("signature"), "Satisfaction", "Signature saved correctly")
                results.assert_true("updated_at" in saved_profile, "updated_at timestamp included")
            
            # Test 3: GET HD profile after saving
            print(f"\n📖 Test 3: GET HD profile (should return has_profile: true with data)")
            async with session.get(f"{API_BASE}/computed-profile/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "GET HD profile returns 200")
                data = await resp.json()
                results.assert_equal(data.get("has_profile"), True, "has_profile is true after saving")
                
                profile = data.get("profile", {})
                results.assert_equal(profile.get("type"), "Manifesting Generator", "Retrieved type matches saved")
                results.assert_equal(profile.get("strategy"), "To Respond", "Retrieved strategy matches saved")
                results.assert_equal(profile.get("authority"), "Sacral", "Retrieved authority matches saved")
                results.assert_equal(profile.get("profile"), "3/5", "Retrieved profile matches saved")
                results.assert_true("_id" not in profile, "_id field properly removed from response")
            
            # Test 4: GET lenses/human-design - Verify personalized_insights
            print(f"\n🔮 Test 4: GET lenses/human-design (verify personalized_insights)")
            async with session.get(f"{API_BASE}/lenses/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "GET lenses/human-design returns 200")
                data = await resp.json()
                
                # Check for personalized_insights
                personalized = data.get("personalized_insights", {})
                results.assert_true(personalized, "personalized_insights exists")
                results.assert_equal(personalized.get("has_personalization"), True, "has_personalization is true")
                
                # Check required insight fields
                results.assert_true("type_insight" in personalized, "type_insight exists")
                results.assert_true("strategy_insight" in personalized, "strategy_insight exists")
                results.assert_true("authority_insight" in personalized, "authority_insight exists")
                
                # Check elements contain user's data
                elements = personalized.get("elements", {})
                results.assert_equal(elements.get("type"), "Manifesting Generator", "elements.type matches user's type")
                results.assert_equal(elements.get("strategy"), "To Respond", "elements.strategy matches user's strategy")
                results.assert_equal(elements.get("authority"), "Sacral", "elements.authority matches user's authority")
                
                # Verify insights contain meaningful content (not just empty strings)
                type_insight = personalized.get("type_insight", "")
                results.assert_true(len(type_insight) > 20, "type_insight has substantial content")
                results.assert_in("Manifesting Generator", type_insight, "type_insight mentions user's type")
                
                strategy_insight = personalized.get("strategy_insight", "")
                results.assert_true(len(strategy_insight) > 20, "strategy_insight has substantial content")
                
                authority_insight = personalized.get("authority_insight", "")
                results.assert_true(len(authority_insight) > 20, "authority_insight has substantial content")
                results.assert_in("Sacral", authority_insight, "authority_insight mentions user's authority")
            
            # Test 5: Update HD profile (POST again with different data)
            print(f"\n🔄 Test 5: Update HD profile (POST with different data)")
            updated_profile_data = {
                "type": "Projector",
                "strategy": "Wait for Invitation",
                "authority": "Emotional",
                "profile": "2/4",
                "definition": "Split Definition",
                "not_self_theme": "Bitterness",
                "signature": "Success"
            }
            
            async with session.post(f"{API_BASE}/computed-profile/human-design", 
                                  json=updated_profile_data, headers=headers) as resp:
                results.assert_equal(resp.status, 200, "POST HD profile update returns 200")
                data = await resp.json()
                results.assert_equal(data.get("success"), True, "Update returns success: true")
                
                # Verify updated data
                saved_profile = data.get("profile", {})
                results.assert_equal(saved_profile.get("type"), "Projector", "Type updated correctly")
                results.assert_equal(saved_profile.get("strategy"), "Wait for Invitation", "Strategy updated correctly")
                results.assert_equal(saved_profile.get("authority"), "Emotional", "Authority updated correctly")
            
            # Test 6: Verify updated profile is retrieved correctly
            print(f"\n📖 Test 6: GET HD profile after update")
            async with session.get(f"{API_BASE}/computed-profile/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "GET updated HD profile returns 200")
                data = await resp.json()
                profile = data.get("profile", {})
                results.assert_equal(profile.get("type"), "Projector", "Retrieved updated type")
                results.assert_equal(profile.get("authority"), "Emotional", "Retrieved updated authority")
            
            # Test 7: DELETE HD profile
            print(f"\n🗑️ Test 7: DELETE HD profile")
            async with session.delete(f"{API_BASE}/computed-profile/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "DELETE HD profile returns 200")
                data = await resp.json()
                results.assert_equal(data.get("deleted"), True, "Profile deletion confirmed")
            
            # Test 8: Verify profile is deleted
            print(f"\n🔍 Test 8: GET HD profile after deletion (should return has_profile: false)")
            async with session.get(f"{API_BASE}/computed-profile/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "GET HD profile after deletion returns 200")
                data = await resp.json()
                results.assert_equal(data.get("has_profile"), False, "has_profile is false after deletion")
                results.assert_equal(data.get("profile"), None, "profile is None after deletion")
            
            # Test 9: Verify lenses/human-design has no personalized_insights after deletion
            print(f"\n🔮 Test 9: GET lenses/human-design after profile deletion")
            async with session.get(f"{API_BASE}/lenses/human-design", headers=headers) as resp:
                results.assert_equal(resp.status, 200, "GET lenses/human-design returns 200")
                data = await resp.json()
                
                # Should not have personalized_insights or should have has_personalization: false
                personalized = data.get("personalized_insights")
                if personalized:
                    results.assert_equal(personalized.get("has_personalization"), False, 
                                       "has_personalization is false after profile deletion")
                else:
                    results.assert_true(True, "No personalized_insights after profile deletion")
            
            # Test 10: Authentication required tests
            print(f"\n🔒 Test 10: Authentication required for all endpoints")
            
            # Test without auth header
            async with session.get(f"{API_BASE}/computed-profile/human-design") as resp:
                results.assert_equal(resp.status, 403, "GET HD profile requires authentication")
            
            async with session.post(f"{API_BASE}/computed-profile/human-design", json=hd_profile_data) as resp:
                results.assert_equal(resp.status, 403, "POST HD profile requires authentication")
            
            async with session.delete(f"{API_BASE}/computed-profile/human-design") as resp:
                results.assert_equal(resp.status, 403, "DELETE HD profile requires authentication")
                
        except Exception as e:
            results.failed += 1
            results.errors.append(f"Test execution error: {str(e)}")
            print(f"❌ Test execution error: {str(e)}")
    
    # Print summary
    print(f"\n" + "=" * 50)
    print(f"🧪 HUMAN DESIGN PROFILE API TEST RESULTS")
    print(f"✅ Passed: {results.passed}")
    print(f"❌ Failed: {results.failed}")
    print(f"📊 Total: {results.passed + results.failed}")
    
    if results.errors:
        print(f"\n🚨 ERRORS FOUND:")
        for error in results.errors:
            print(f"   • {error}")
    
    return results.failed == 0, results

async def main():
    """Run all Human Design Profile API tests"""
    print("🚀 Starting Human Design Profile API Testing")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🔗 API Base: {API_BASE}")
    
    success, results = await test_human_design_profile_apis()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED! Human Design Profile APIs are working correctly.")
        return 0
    else:
        print(f"\n💥 SOME TESTS FAILED! Check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)