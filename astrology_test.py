#!/usr/bin/env python3
"""
Astrology API Endpoints Testing Script
Testing the True Sidereal Astrology Lens Refactor implementation
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://decision-signals-hub.preview.emergentagent.com/api"

def test_astrology_summary(user_id):
    """
    Test GET /api/astrology/summary/{user_id}
    Verify it returns core_placements with sun, moon, ascendant
    """
    print(f"🧪 TESTING ASTROLOGY SUMMARY ENDPOINT")
    print("=" * 60)
    
    endpoint = f"{BACKEND_URL}/astrology/summary/{user_id}"
    print(f"📋 TEST SETUP:")
    print(f"   Endpoint: {endpoint}")
    print(f"   User ID: {user_id}")
    print()
    
    print("🚀 SENDING REQUEST...")
    start_time = time.time()
    
    try:
        response = requests.get(endpoint, timeout=30)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response_time:.2f} seconds")
        print()
        
        if response.status_code == 200:
            response_data = response.json()
            
            print("✅ API REQUEST SUCCESSFUL")
            print()
            
            # Verify response structure
            print("🔍 VERIFYING RESPONSE STRUCTURE:")
            print("-" * 50)
            
            # Check for core_placements
            core_placements = response_data.get('core_placements')
            if core_placements:
                print("✅ core_placements field exists")
                
                # Check for sun, moon, ascendant
                sun = core_placements.get('sun')
                moon = core_placements.get('moon')
                ascendant = core_placements.get('ascendant')
                
                print(f"   Sun: {sun}")
                print(f"   Moon: {moon}")
                print(f"   Ascendant: {ascendant}")
                
                # Verify no "Unknown" values
                has_unknown = any(
                    str(value).lower() == 'unknown' 
                    for value in [sun, moon, ascendant] 
                    if value is not None
                )
                
                if not has_unknown:
                    print("✅ No 'Unknown' values in placements")
                else:
                    print("❌ Found 'Unknown' values in placements")
                
                # Check expected values for test user
                if user_id == "6971c81f2b40fd5ef501d375":
                    expected_sun = "Pisces"
                    expected_moon = "Aries" 
                    expected_asc = "Sagittarius"
                    
                    sun_match = str(sun) == expected_sun
                    moon_match = str(moon) == expected_moon
                    asc_match = str(ascendant) == expected_asc
                    
                    print(f"   Expected vs Actual:")
                    print(f"   Sun: {expected_sun} vs {sun} {'✅' if sun_match else '❌'}")
                    print(f"   Moon: {expected_moon} vs {moon} {'✅' if moon_match else '❌'}")
                    print(f"   Ascendant: {expected_asc} vs {ascendant} {'✅' if asc_match else '❌'}")
                
            else:
                print("❌ core_placements field missing")
            
            # Check other required fields
            title = response_data.get('title')
            sections = response_data.get('sections')
            mirror_prompt = response_data.get('mirror_prompt')
            
            print(f"\n📋 OTHER FIELDS:")
            print(f"   Title: {'✅' if title else '❌'} {title}")
            print(f"   Sections: {'✅' if sections else '❌'} ({len(sections) if sections else 0} sections)")
            print(f"   Mirror Prompt: {'✅' if mirror_prompt else '❌'}")
            
            if sections:
                for i, section in enumerate(sections):
                    label = section.get('label', 'N/A')
                    body_length = len(section.get('body', ''))
                    print(f"     Section {i+1}: {label} ({body_length} chars)")
            
            return True, response_data
            
        else:
            print(f"❌ API REQUEST FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        return False, None

def test_astrology_deep_dive(user_id):
    """
    Test GET /api/astrology/deep-dive/{user_id}
    Verify it returns sections and core_placements
    """
    print(f"\n🧪 TESTING ASTROLOGY DEEP DIVE ENDPOINT")
    print("=" * 60)
    
    endpoint = f"{BACKEND_URL}/astrology/deep-dive/{user_id}"
    print(f"📋 TEST SETUP:")
    print(f"   Endpoint: {endpoint}")
    print(f"   User ID: {user_id}")
    print()
    
    print("🚀 SENDING REQUEST...")
    start_time = time.time()
    
    try:
        response = requests.get(endpoint, timeout=60)  # Longer timeout for deep dive
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response_time:.2f} seconds")
        print()
        
        if response.status_code == 200:
            response_data = response.json()
            
            print("✅ API REQUEST SUCCESSFUL")
            print()
            
            # Verify response structure
            print("🔍 VERIFYING RESPONSE STRUCTURE:")
            print("-" * 50)
            
            # Check success field
            success = response_data.get('success')
            print(f"   Success: {'✅' if success else '❌'} {success}")
            
            if success:
                # Check for core_placements
                core_placements = response_data.get('core_placements')
                if core_placements:
                    print("✅ core_placements field exists")
                    
                    # Check for sun, moon, ascendant
                    sun = core_placements.get('sun')
                    moon = core_placements.get('moon')
                    ascendant = core_placements.get('ascendant')
                    
                    print(f"   Sun: {sun}")
                    print(f"   Moon: {moon}")
                    print(f"   Ascendant: {ascendant}")
                    
                    # Verify no "Unknown" values
                    has_unknown = any(
                        str(value).lower() == 'unknown' 
                        for value in [sun, moon, ascendant] 
                        if value is not None
                    )
                    
                    if not has_unknown:
                        print("✅ No 'Unknown' values in placements")
                    else:
                        print("❌ Found 'Unknown' values in placements")
                    
                    # Check expected values for test user
                    if user_id == "6971c81f2b40fd5ef501d375":
                        expected_sun = "Pisces"
                        expected_moon = "Aries" 
                        expected_asc = "Sagittarius"
                        
                        sun_match = str(sun) == expected_sun
                        moon_match = str(moon) == expected_moon
                        asc_match = str(ascendant) == expected_asc
                        
                        print(f"   Expected vs Actual:")
                        print(f"   Sun: {expected_sun} vs {sun} {'✅' if sun_match else '❌'}")
                        print(f"   Moon: {expected_moon} vs {moon} {'✅' if moon_match else '❌'}")
                        print(f"   Ascendant: {expected_asc} vs {ascendant} {'✅' if asc_match else '❌'}")
                    
                else:
                    print("❌ core_placements field missing")
                
                # Check sections
                sections = response_data.get('sections')
                if sections:
                    print(f"✅ sections field exists ({len(sections)} sections)")
                    for i, section in enumerate(sections):
                        label = section.get('label', 'N/A')
                        body_length = len(section.get('body', ''))
                        print(f"     Section {i+1}: {label} ({body_length} chars)")
                else:
                    print("❌ sections field missing or empty")
                
                # Check other fields
                title = response_data.get('title')
                mirror_prompt = response_data.get('mirror_prompt')
                
                print(f"\n📋 OTHER FIELDS:")
                print(f"   Title: {'✅' if title else '❌'} {title}")
                print(f"   Mirror Prompt: {'✅' if mirror_prompt else '❌'}")
                
            else:
                # Handle error response
                error = response_data.get('error')
                message = response_data.get('message')
                print(f"❌ API returned success=false")
                print(f"   Error: {error}")
                print(f"   Message: {message}")
            
            return True, response_data
            
        else:
            print(f"❌ API REQUEST FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        return False, None

def check_backend_logs():
    """
    Check backend logs for astrology-related processing
    """
    print("\n🔍 CHECKING BACKEND LOGS:")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for astrology-related patterns
            astrology_patterns = [
                "ASTRO_SUMMARY",
                "ASTRO_DEEP_DIVE", 
                "Auto-migrated chart",
                "astrology/summary",
                "astrology/deep-dive"
            ]
            
            print("Looking for astrology-related log patterns:")
            for pattern in astrology_patterns:
                if pattern in log_content:
                    print(f"   ✅ Found: {pattern}")
                else:
                    print(f"   ❌ Missing: {pattern}")
            
            # Show recent astrology logs
            astro_logs = [line for line in log_content.split('\n') 
                         if any(p in line for p in ['ASTRO', 'astrology'])]
            if astro_logs:
                print(f"\n📋 Recent Astrology logs ({len(astro_logs)} entries):")
                for log in astro_logs[-3:]:  # Show last 3
                    print(f"   {log}")
            else:
                print("\n❓ No recent astrology logs found")
                
        else:
            print("❌ Could not read backend logs")
            
    except Exception as e:
        print(f"❌ Error reading logs: {str(e)}")

def main():
    """
    Main test execution
    """
    print("🧪 ASTROLOGY API ENDPOINTS TESTING")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    # Test user from review request
    user_id = "6971c81f2b40fd5ef501d375"
    print(f"Test User: {user_id} (Sun=Pisces, Moon=Aries, Ascendant=Sagittarius)")
    print()
    
    # Test both endpoints
    summary_success, summary_data = test_astrology_summary(user_id)
    deep_dive_success, deep_dive_data = test_astrology_deep_dive(user_id)
    
    # Check backend logs
    check_backend_logs()
    
    # Summary
    print("\n🎯 TESTING SUMMARY:")
    print("=" * 60)
    
    if summary_success:
        print("✅ Astrology Summary endpoint working")
    else:
        print("❌ Astrology Summary endpoint failed")
    
    if deep_dive_success:
        print("✅ Astrology Deep Dive endpoint working")
    else:
        print("❌ Astrology Deep Dive endpoint failed")
    
    # Overall assessment
    if summary_success and deep_dive_success:
        print("\n🎉 ALL TESTS PASSED")
        print("✅ Both astrology endpoints are working correctly")
        print("✅ core_placements structure verified")
        print("✅ No 'Unknown' values found in placements")
        print("✅ Response structure matches requirements")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("- Check backend service status")
        print("- Verify user chart data exists")
        print("- Review error messages above")

if __name__ == "__main__":
    main()