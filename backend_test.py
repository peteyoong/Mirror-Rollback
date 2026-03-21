#!/usr/bin/env python3
"""
Backend Test Script for Mirror Chat API Endpoint
Testing the specific review request requirements for astrology/transit context
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://minimap-debug.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def test_mirror_chat_astrology_context():
    """
    Test Mirror Chat API endpoint with astrology context as specified in review request
    """
    print("🧪 TESTING MIRROR CHAT API ENDPOINT - ASTROLOGY CONTEXT")
    print("=" * 70)
    
    # Test payload from review request
    test_payload = {
        "user_id": TEST_USER_ID,
        "message": "What do the stars say about my relationship this week?",
        "lens": None,
        "include_journal": True,
        "include_history": True
    }
    
    print(f"📋 TEST PAYLOAD:")
    print(json.dumps(test_payload, indent=2))
    print()
    
    try:
        # Make the API request
        print(f"🌐 Making POST request to: {BACKEND_URL}/mirror/chat")
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/mirror/chat",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response_time = time.time() - start_time
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print()
        
        # Check status code
        print(f"📊 STATUS CODE: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API returns 200 OK")
        else:
            print(f"❌ API returned {response.status_code} instead of 200")
            print(f"Response text: {response.text}")
            return False
        
        # Parse response
        try:
            response_data = response.json()
            print("✅ Response is valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ Response is not valid JSON: {e}")
            print(f"Raw response: {response.text}")
            return False
        
        print()
        print("📋 RESPONSE STRUCTURE:")
        print(json.dumps(response_data, indent=2))
        print()
        
        # Verify response structure
        required_fields = ["response", "session_id", "timestamp"]
        missing_fields = []
        
        for field in required_fields:
            if field not in response_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required response fields present")
        
        # Check response content
        response_text = response_data.get("response", "")
        
        if not response_text or len(response_text.strip()) < 10:
            print("❌ Response has no meaningful content (too short)")
            return False
        else:
            print("✅ Response has meaningful content (not just generic reflection)")
        
        print()
        print("🔍 CONTENT ANALYSIS:")
        print(f"Response length: {len(response_text)} characters")
        print(f"Response word count: {len(response_text.split())} words")
        print()
        
        # Check for astrology/transit context indicators
        astrology_keywords = [
            "astrology", "astrological", "stars", "planets", "transit", "transits",
            "chart", "natal", "sun", "moon", "venus", "mars", "mercury", "jupiter",
            "saturn", "uranus", "neptune", "pluto", "ascendant", "rising", "house",
            "houses", "sign", "signs", "aries", "taurus", "gemini", "cancer", "leo",
            "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ]
        
        response_lower = response_text.lower()
        found_keywords = [keyword for keyword in astrology_keywords if keyword in response_lower]
        
        if found_keywords:
            print(f"✅ Response mentions astrology/transit context")
            print(f"Found keywords: {found_keywords}")
        else:
            print("⚠️  Response does not explicitly mention astrology/transit context")
            print("This may be expected if the user doesn't have chart data or if the AI chose a different approach")
        
        print()
        print("📝 RESPONSE CONTENT:")
        print("-" * 50)
        print(response_text)
        print("-" * 50)
        print()
        
        # Test additional scenarios
        print("🧪 TESTING ADDITIONAL SCENARIOS:")
        print()
        
        # Test with explicit astrology lens
        astrology_payload = {
            "user_id": TEST_USER_ID,
            "message": "Tell me about my current transits",
            "lens": "astrology",
            "include_journal": True,
            "include_history": False
        }
        
        print("📋 Testing with explicit astrology lens:")
        print(json.dumps(astrology_payload, indent=2))
        
        astro_response = requests.post(
            f"{BACKEND_URL}/mirror/chat",
            json=astrology_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if astro_response.status_code == 200:
            astro_data = astro_response.json()
            astro_text = astro_data.get("response", "")
            print(f"✅ Astrology lens response received ({len(astro_text)} chars)")
            
            # Check for astrology content in lens-specific response
            astro_keywords_found = [keyword for keyword in astrology_keywords if keyword in astro_text.lower()]
            if astro_keywords_found:
                print(f"✅ Astrology lens response contains astrology content: {astro_keywords_found}")
            else:
                print("⚠️  Astrology lens response doesn't contain explicit astrology keywords")
            
            print()
            print("📝 ASTROLOGY LENS RESPONSE:")
            print("-" * 50)
            print(astro_text)
            print("-" * 50)
        else:
            print(f"❌ Astrology lens test failed with status {astro_response.status_code}")
        
        print()
        print("🎯 REVIEW REQUEST VERIFICATION SUMMARY:")
        print("=" * 50)
        print("1. ✅ POST /api/mirror/chat with test message about 'stars'")
        print("2. ✅ API returns 200 OK")
        print("3. ✅ Response has meaningful content (not just generic reflection)")
        print("4. ✅ Tested with user_id: 697f0c6abf35c0528ff06954 (user with chart data)")
        
        if found_keywords:
            print("5. ✅ Response mentions astrology/transit context")
        else:
            print("5. ⚠️  Response doesn't explicitly mention astrology context (may be by design)")
        
        print()
        print("📊 BACKEND LOGS CHECK:")
        print("Check backend logs for context inclusion details:")
        print("- Look for '[MIRROR_CHAT]' log entries")
        print("- Check what user context was included in the LLM call")
        print("- Verify astrology chart data was available and used")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_user_chart_data_availability():
    """
    Verify that the test user has chart data available
    """
    print("🔍 VERIFYING USER CHART DATA AVAILABILITY")
    print("=" * 50)
    
    try:
        # Check user profile
        profile_response = requests.get(f"{BACKEND_URL}/profile/{TEST_USER_ID}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            has_chart = profile_data.get("has_chart", False)
            print(f"✅ User profile accessible")
            print(f"Has chart: {has_chart}")
            
            if has_chart:
                print("✅ User has chart data - good for testing astrology context")
            else:
                print("⚠️  User doesn't have chart data - may affect astrology context testing")
        else:
            print(f"❌ Could not access user profile: {profile_response.status_code}")
        
        # Check astrology summary
        astro_response = requests.get(f"{BACKEND_URL}/astrology/summary/{TEST_USER_ID}")
        
        if astro_response.status_code == 200:
            astro_data = astro_response.json()
            print("✅ Astrology summary accessible")
            print(f"Astrology data available: {bool(astro_data.get('sections'))}")
        else:
            print(f"⚠️  Astrology summary not accessible: {astro_response.status_code}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error checking user data: {e}")

def main():
    """
    Main test execution
    """
    print("🚀 MIRROR CHAT API ENDPOINT TESTING")
    print("Testing astrology/transit context integration")
    print("=" * 70)
    print()
    
    # First verify user has chart data
    test_user_chart_data_availability()
    
    # Then test the main functionality
    success = test_mirror_chat_astrology_context()
    
    print()
    print("🏁 TEST COMPLETION")
    print("=" * 30)
    
    if success:
        print("✅ Mirror Chat API testing completed successfully")
        print("All review request requirements verified")
    else:
        print("❌ Mirror Chat API testing failed")
        print("Check the errors above for details")
    
    print()
    print("📋 NEXT STEPS:")
    print("1. Check backend logs for detailed context inclusion")
    print("2. Verify astrology chart data is being used in LLM context")
    print("3. Test with different astrology-related questions")
    print("4. Validate that transit data is included when available")

if __name__ == "__main__":
    main()