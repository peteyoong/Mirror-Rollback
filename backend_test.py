#!/usr/bin/env python3
"""
Backend API Testing Script for V5.2 Astrology Today and V5.0 Home Synthesis
Testing the specific requirements from the review request.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://deployment-fix-25.preview.emergentagent.com/api"
TEST_USER_ID = "697f0c6abf35c0528ff06954"

def test_v52_astrology_today_horizon_differentiation():
    """
    Test V5.2 Astrology Today with horizon differentiation for all 3 timeframes.
    Verify distinct themes and proper version.
    """
    print("🌟 TESTING V5.2 ASTROLOGY TODAY WITH HORIZON DIFFERENTIATION")
    print("=" * 70)
    
    timeframes = ["today", "week", "month"]
    responses = {}
    themes = {}
    
    # Test all 3 timeframes
    for timeframe in timeframes:
        url = f"{BACKEND_URL}/astro-expert/{TEST_USER_ID}?timeframe={timeframe}"
        print(f"\n📅 Testing timeframe: {timeframe}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                responses[timeframe] = data
                
                # Extract key fields
                todays_theme = data.get("todays_theme", "")
                version = data.get("version", "")
                themes[timeframe] = todays_theme
                
                print(f"✅ Success: {response.status_code}")
                print(f"📝 Theme: {todays_theme}")
                print(f"🔖 Version: {version}")
                
                # Check version
                if version == "v5.2_horizon":
                    print("✅ Version correct: v5.2_horizon")
                else:
                    print(f"❌ Version incorrect: expected 'v5.2_horizon', got '{version}'")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    # Verify all themes are DISTINCT
    print(f"\n🔍 VERIFYING DISTINCT THEMES:")
    print("=" * 50)
    
    all_themes = list(themes.values())
    unique_themes = set(all_themes)
    
    for timeframe, theme in themes.items():
        print(f"{timeframe.upper()}: {theme}")
    
    if len(unique_themes) == len(all_themes):
        print("✅ All themes are DISTINCT")
    else:
        print("❌ Themes are NOT distinct")
        return False
    
    # Verify month has arc-focused language (not immediate language like "NOW")
    month_theme = themes.get("month", "")
    if "NOW" in month_theme.upper():
        print("❌ Month theme contains immediate language 'NOW'")
        return False
    elif "MONTH" in month_theme.upper() or "ARC" in month_theme.upper():
        print("✅ Month theme has arc-focused language")
    else:
        print("⚠️  Month theme may not have clear arc-focused language")
    
    print("\n🎉 V5.2 ASTROLOGY TODAY HORIZON DIFFERENTIATION: PASSED")
    return True

def test_v50_home_synthesis():
    """
    Test V5.0 Home Synthesis endpoint.
    Verify 4-block structure, no internal labels, and correct version.
    """
    print("\n🏠 TESTING V5.0 HOME SYNTHESIS")
    print("=" * 70)
    
    url = f"{BACKEND_URL}/home-synthesis/{TEST_USER_ID}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {response.status_code}")
            
            # Check success field
            success = data.get("success", False)
            if success:
                print("✅ success: true")
            else:
                print("❌ success: false or missing")
                return False
            
            # Check version
            version = data.get("version", "")
            if version == "v5.0_synthesis":
                print("✅ Version correct: v5.0_synthesis")
            else:
                print(f"❌ Version incorrect: expected 'v5.0_synthesis', got '{version}'")
                return False
            
            # Check 4-block structure
            required_blocks = ["the_call", "the_reality", "the_source_hint", "the_edge"]
            missing_blocks = []
            
            print(f"\n🔍 VERIFYING 4-BLOCK STRUCTURE:")
            for block in required_blocks:
                if block in data:
                    print(f"✅ {block}: present")
                else:
                    print(f"❌ {block}: missing")
                    missing_blocks.append(block)
            
            if missing_blocks:
                print(f"❌ Missing blocks: {missing_blocks}")
                return False
            else:
                print("✅ All 4 blocks present")
            
            # Check for internal labels in user-facing fields
            print(f"\n🔍 CHECKING FOR INTERNAL LABELS:")
            internal_patterns = ["_test", "_low_", "_high_", "pattern_", "escalating_"]
            found_internal_labels = []
            
            for block in required_blocks:
                block_content = str(data.get(block, ""))
                for pattern in internal_patterns:
                    if pattern in block_content:
                        found_internal_labels.append(f"{block}: {pattern}")
                        print(f"❌ Found internal label '{pattern}' in {block}")
            
            if found_internal_labels:
                print(f"❌ Internal labels found: {found_internal_labels}")
                return False
            else:
                print("✅ No internal labels found in user-facing fields")
            
            # Show sample content
            print(f"\n📝 SAMPLE CONTENT:")
            for block in required_blocks:
                content = data.get(block, "")
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"{block}: {preview}")
            
            print("\n🎉 V5.0 HOME SYNTHESIS: PASSED")
            return True
            
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 BACKEND API TESTING - V5.2 ASTROLOGY TODAY & V5.0 HOME SYNTHESIS")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("=" * 80)
    
    # Test V5.2 Astrology Today
    test1_passed = test_v52_astrology_today_horizon_differentiation()
    
    # Test V5.0 Home Synthesis
    test2_passed = test_v50_home_synthesis()
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"V5.2 Astrology Today: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"V5.0 Home Synthesis: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())