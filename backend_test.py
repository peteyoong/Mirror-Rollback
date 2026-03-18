#!/usr/bin/env python3
"""
Backend testing script for BaZi V2 API with precise language features.
Tests all the specific requirements mentioned in the review request.
"""
import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "https://home-screen-overhaul.preview.emergentagent.com/api"
TEST_USER_ID = "6971c81f2b40fd5ef501d375"  # User with Xin Metal Day Master

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}🧪 {message}{Colors.END}")

def check_generic_language(text, field_name):
    """Check if text contains generic language that should be avoided."""
    if not text:
        return []
    
    forbidden_phrases = [
        "you tend to",
        "you may often", 
        "you might sometimes",
        "you are likely to",
        "you probably",
        "you generally",
        "you typically",
        "you usually"
    ]
    
    found_issues = []
    text_lower = text.lower()
    
    for phrase in forbidden_phrases:
        if phrase in text_lower:
            found_issues.append(f"{field_name}: contains forbidden phrase '{phrase}'")
    
    return found_issues

def check_precise_language(text, field_name):
    """Check if text contains precise, direct language."""
    if not text:
        return False
    
    precise_patterns = [
        "you don't",
        "you notice", 
        "you prioritize",
        "you move",
        "you create",
        "you understand",
        "you feel",
        "you see",
        "you flow",
        "you cut through",
        "you grow"
    ]
    
    text_lower = text.lower()
    for pattern in precise_patterns:
        if pattern in text_lower:
            return True
    
    return False

async def test_bazi_v2_full_chart():
    """Test the BaZi V2 Full Chart API for precise language features."""
    
    print_header("BAZI V2 PRECISE LANGUAGE FEATURES TESTING")
    print(f"Testing user: {TEST_USER_ID}")
    print(f"Endpoint: {BASE_URL}/bazi/{TEST_USER_ID}/full")
    
    try:
        async with aiohttp.ClientSession() as session:
            start_time = datetime.now()
            
            async with session.get(f"{BASE_URL}/bazi/{TEST_USER_ID}/full") as response:
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status != 200:
                    print_error(f"HTTP {response.status}: {await response.text()}")
                    return False
                
                data = await response.json()
                print_success(f"Response received in {response_time:.2f}s")
                
                # Basic structure check
                if not data.get("success"):
                    print_error("Response indicates failure")
                    return False
                
                chart = data.get("chart", {})
                if not chart:
                    print_error("No chart data found")
                    return False
                
                print_success("Basic response structure valid")
                
                # Test 1: Day Master has wow_line and why_pattern
                print_header("TEST 1: Day Master Precise Language Fields")
                
                day_master = chart.get("day_master", {})
                if not day_master:
                    print_error("Day Master data missing")
                    return False
                
                # Check wow_line
                wow_line = day_master.get("wow_line", "")
                if not wow_line:
                    print_error("Day Master missing wow_line field")
                    return False
                
                print_success(f"Day Master wow_line present: '{wow_line}'")
                
                # Check if wow_line contains expected content for Xin Metal
                if "you don't move fast" in wow_line.lower() or "move right" in wow_line.lower():
                    print_success("Day Master wow_line contains expected Xin Metal content")
                else:
                    print_warning(f"Day Master wow_line doesn't match expected Xin Metal pattern: '{wow_line}'")
                
                # Check why_pattern
                why_pattern = day_master.get("why_pattern", "")
                if not why_pattern:
                    print_error("Day Master missing why_pattern field")
                    return False
                
                print_success(f"Day Master why_pattern present: '{why_pattern}'")
                
                # Check for generic language in Day Master fields
                generic_issues = []
                generic_issues.extend(check_generic_language(wow_line, "Day Master wow_line"))
                generic_issues.extend(check_generic_language(why_pattern, "Day Master why_pattern"))
                
                if generic_issues:
                    for issue in generic_issues:
                        print_error(f"Generic language found: {issue}")
                    return False
                
                print_success("Day Master fields contain precise language (no generic phrases)")
                
                # Test 2: Deep Dive - Life Pattern has wow_line and why_pattern
                print_header("TEST 2: Deep Dive Life Pattern Precise Language")
                
                deep_dive = chart.get("deep_dive", {})
                if not deep_dive:
                    print_error("Deep Dive data missing")
                    return False
                
                life_pattern = deep_dive.get("life_pattern", {})
                if not life_pattern:
                    print_error("Life Pattern data missing")
                    return False
                
                # Check wow_line in life pattern
                lp_wow_line = life_pattern.get("wow_line", "")
                if not lp_wow_line:
                    print_error("Life Pattern missing wow_line field")
                    return False
                
                print_success(f"Life Pattern wow_line present: '{lp_wow_line}'")
                
                # Check why_pattern in life pattern
                lp_why_pattern = life_pattern.get("why_pattern", "")
                if not lp_why_pattern:
                    print_error("Life Pattern missing why_pattern field")
                    return False
                
                print_success(f"Life Pattern why_pattern present: '{lp_why_pattern}'")
                
                # Check for generic language in Life Pattern fields
                generic_issues = []
                generic_issues.extend(check_generic_language(lp_wow_line, "Life Pattern wow_line"))
                generic_issues.extend(check_generic_language(lp_why_pattern, "Life Pattern why_pattern"))
                
                if generic_issues:
                    for issue in generic_issues:
                        print_error(f"Generic language found: {issue}")
                    return False
                
                print_success("Life Pattern fields contain precise language (no generic phrases)")
                
                # Test 3: Deep Dive - Ten Gods Detailed (first item) has required fields
                print_header("TEST 3: Deep Dive Ten Gods Detailed Precise Language")
                
                ten_gods_detailed = deep_dive.get("ten_gods_detailed", [])
                if not ten_gods_detailed:
                    print_error("Ten Gods Detailed data missing")
                    return False
                
                first_ten_god = ten_gods_detailed[0]
                
                # Check wow_line
                tg_wow_line = first_ten_god.get("wow_line", "")
                if not tg_wow_line:
                    print_error("First Ten God missing wow_line field")
                    return False
                
                print_success(f"First Ten God wow_line present: '{tg_wow_line}'")
                
                # Check why_pattern
                tg_why_pattern = first_ten_god.get("why_pattern", "")
                if not tg_why_pattern:
                    print_error("First Ten God missing why_pattern field")
                    return False
                
                print_success(f"First Ten God why_pattern present: '{tg_why_pattern}'")
                
                # Check go_deeper
                tg_go_deeper = first_ten_god.get("go_deeper", "")
                if not tg_go_deeper:
                    print_error("First Ten God missing go_deeper field")
                    return False
                
                print_success(f"First Ten God go_deeper present: '{tg_go_deeper}'")
                
                # Check for generic language in Ten Gods fields
                generic_issues = []
                generic_issues.extend(check_generic_language(tg_wow_line, "Ten God wow_line"))
                generic_issues.extend(check_generic_language(tg_why_pattern, "Ten God why_pattern"))
                generic_issues.extend(check_generic_language(tg_go_deeper, "Ten God go_deeper"))
                
                if generic_issues:
                    for issue in generic_issues:
                        print_error(f"Generic language found: {issue}")
                    return False
                
                print_success("Ten Gods Detailed fields contain precise language (no generic phrases)")
                
                # Test 4: Deep Dive - Hidden Dynamics (first item) has behavioral and shows_up
                print_header("TEST 4: Deep Dive Hidden Dynamics Behavioral Fields")
                
                hidden_dynamics = deep_dive.get("hidden_dynamics", [])
                if not hidden_dynamics:
                    print_error("Hidden Dynamics data missing")
                    return False
                
                first_hidden = hidden_dynamics[0]
                
                # Check behavioral
                hd_behavioral = first_hidden.get("behavioral", "")
                if not hd_behavioral:
                    print_error("First Hidden Dynamic missing behavioral field")
                    return False
                
                print_success(f"First Hidden Dynamic behavioral present: '{hd_behavioral}'")
                
                # Check shows_up
                hd_shows_up = first_hidden.get("shows_up", "")
                if not hd_shows_up:
                    print_error("First Hidden Dynamic missing shows_up field")
                    return False
                
                print_success(f"First Hidden Dynamic shows_up present: '{hd_shows_up}'")
                
                # Check for generic language in Hidden Dynamics fields
                generic_issues = []
                generic_issues.extend(check_generic_language(hd_behavioral, "Hidden Dynamic behavioral"))
                generic_issues.extend(check_generic_language(hd_shows_up, "Hidden Dynamic shows_up"))
                
                if generic_issues:
                    for issue in generic_issues:
                        print_error(f"Generic language found: {issue}")
                    return False
                
                print_success("Hidden Dynamics fields contain precise language (no generic phrases)")
                
                # Test 5: Verify NO generic language across all key fields
                print_header("TEST 5: Comprehensive Generic Language Check")
                
                all_fields_to_check = []
                
                # Collect all text fields from the response that should use precise language
                if day_master:
                    all_fields_to_check.extend([
                        (day_master.get("description", ""), "Day Master description"),
                        (day_master.get("strength_description", ""), "Day Master strength description")
                    ])
                
                if life_pattern:
                    all_fields_to_check.extend([
                        (life_pattern.get("core_drive", ""), "Life Pattern core drive"),
                        (life_pattern.get("default_mode", ""), "Life Pattern default mode"),
                        (life_pattern.get("under_pressure", ""), "Life Pattern under pressure"),
                        (life_pattern.get("growth_direction", ""), "Life Pattern growth direction")
                    ])
                
                for i, ten_god in enumerate(ten_gods_detailed):
                    all_fields_to_check.extend([
                        (ten_god.get("behavioral_expression", ""), f"Ten God {i+1} behavioral expression"),
                        (ten_god.get("stress_pattern", ""), f"Ten God {i+1} stress pattern"),
                        (ten_god.get("others_experience", ""), f"Ten God {i+1} others experience"),
                        (ten_god.get("insight", ""), f"Ten God {i+1} insight"),
                        (ten_god.get("tension", ""), f"Ten God {i+1} tension"),
                        (ten_god.get("action", ""), f"Ten God {i+1} action")
                    ])
                
                for i, hidden in enumerate(hidden_dynamics):
                    all_fields_to_check.extend([
                        (hidden.get("meaning", ""), f"Hidden Dynamic {i+1} meaning")
                    ])
                
                total_generic_issues = []
                precise_language_count = 0
                
                for text, field_name in all_fields_to_check:
                    if text:
                        issues = check_generic_language(text, field_name)
                        total_generic_issues.extend(issues)
                        
                        if check_precise_language(text, field_name):
                            precise_language_count += 1
                
                if total_generic_issues:
                    print_error(f"Found {len(total_generic_issues)} generic language issues:")
                    for issue in total_generic_issues[:5]:  # Show first 5 issues
                        print_error(f"  {issue}")
                    if len(total_generic_issues) > 5:
                        print_error(f"  ... and {len(total_generic_issues) - 5} more issues")
                    return False
                
                print_success(f"No generic language found across {len(all_fields_to_check)} text fields")
                print_success(f"{precise_language_count} fields contain direct, precise language patterns")
                
                # Test 6: Specific content verification for Xin Metal user
                print_header("TEST 6: Xin Metal Expected Content Verification")
                
                expected_patterns = {
                    "Day Master element": "Metal",
                    "Day Master stem": "Xin",
                    "Direct language usage": True
                }
                
                # Check Day Master element
                dm_element = day_master.get("element", "")
                if dm_element == "Metal":
                    print_success(f"✅ Day Master element is Metal (got: {dm_element})")
                else:
                    print_error(f"Expected Day Master element 'Metal', got: {dm_element}")
                    return False
                
                # Check Day Master stem
                dm_stem = day_master.get("stem_pinyin", "")
                if dm_stem == "Xin":
                    print_success(f"✅ Day Master stem is Xin (got: {dm_stem})")
                else:
                    print_error(f"Expected Day Master stem 'Xin', got: {dm_stem}")
                    return False
                
                # Check for expected Xin Metal content patterns
                xin_metal_patterns = [
                    ("move right", "precision/accuracy focus"),
                    ("notice", "attention to quality"),
                    ("prioritize", "quality over speed"),
                    ("refine", "refinement characteristic"),
                    ("quality", "quality consciousness")
                ]
                
                found_patterns = []
                all_text = f"{wow_line} {why_pattern} {lp_wow_line} {lp_why_pattern}".lower()
                
                for pattern, description in xin_metal_patterns:
                    if pattern in all_text:
                        found_patterns.append(description)
                        print_success(f"✅ Found Xin Metal pattern '{pattern}' ({description})")
                
                if found_patterns:
                    print_success(f"Xin Metal characteristics properly represented ({len(found_patterns)} patterns found)")
                else:
                    print_warning("No specific Xin Metal characteristic patterns detected in wow_line/why_pattern fields")
                
                print_header("🎉 ALL TESTS COMPLETED SUCCESSFULLY")
                print_success("BaZi V2 API with precise language features is working correctly")
                print_info(f"Response time: {response_time:.2f}s")
                print_info(f"User tested: {TEST_USER_ID} (Xin Metal Day Master)")
                print_info("All required fields present with precise, direct language")
                print_info("No generic language detected in critical fields")
                
                return True
                
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution."""
    print(f"{Colors.BOLD}BaZi V2 Precise Language Features Test Suite{Colors.END}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print("=" * 70)
    
    success = await test_bazi_v2_full_chart()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ TESTS FAILED{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())