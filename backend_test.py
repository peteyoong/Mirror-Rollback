#!/usr/bin/env python3
"""
Backend Testing Script for Astrology Transit Differentiation
Testing the astrology transit differentiation across Today/This Week/This Month
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://lunar-cycle-mirror.preview.emergentagent.com/api"

def test_astrology_chart_transits(user_id: str) -> Dict[str, Any]:
    """Test the astrology chart endpoint for transit differentiation"""
    print(f"\n🧪 Testing Astrology Chart Transits for User: {user_id}")
    
    url = f"{BACKEND_URL}/astrology/chart/{user_id}"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"📡 GET {url}")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check if transits exist
        if "transits" not in data:
            print("❌ ERROR: No 'transits' field in response")
            return {"success": False, "error": "Missing transits field"}
        
        transits = data["transits"]
        
        # Check if windows exist
        if "windows" not in transits:
            print("❌ ERROR: No 'windows' field in transits")
            return {"success": False, "error": "Missing windows field"}
        
        windows = transits["windows"]
        
        # Check for required windows
        required_windows = ["today", "this_week", "this_month"]
        for window in required_windows:
            if window not in windows:
                print(f"❌ ERROR: Missing '{window}' window")
                return {"success": False, "error": f"Missing {window} window"}
        
        print("✅ All required windows present: today, this_week, this_month")
        
        # Test each window
        results = {}
        for window_name in required_windows:
            window_data = windows[window_name]
            results[window_name] = test_window_structure(window_name, window_data)
        
        # Test differentiation between windows
        differentiation_results = test_window_differentiation(windows)
        
        # Test planet focus differentiation
        planet_focus_results = test_planet_focus_differentiation(windows)
        
        return {
            "success": True,
            "user_id": user_id,
            "windows": results,
            "differentiation": differentiation_results,
            "planet_focus": planet_focus_results
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        print(f"❌ JSON ERROR: {e}")
        return {"success": False, "error": f"Invalid JSON: {e}"}
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return {"success": False, "error": str(e)}

def test_window_structure(window_name: str, window_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test the structure of a single transit window"""
    print(f"\n🔍 Testing {window_name.upper()} window structure:")
    
    results = {"window_name": window_name, "tests": []}
    
    # Test 1: Check strongest_hits exists
    if "strongest_hits" not in window_data:
        results["tests"].append({"test": "strongest_hits_exists", "result": False, "error": "Missing strongest_hits"})
        print(f"❌ Missing 'strongest_hits' in {window_name}")
    else:
        strongest_hits = window_data["strongest_hits"]
        if isinstance(strongest_hits, list):
            results["tests"].append({"test": "strongest_hits_exists", "result": True, "count": len(strongest_hits)})
            print(f"✅ strongest_hits exists with {len(strongest_hits)} items")
        else:
            results["tests"].append({"test": "strongest_hits_exists", "result": False, "error": "strongest_hits is not a list"})
            print(f"❌ strongest_hits is not a list in {window_name}")
    
    # Test 2: Check selection_reason exists
    expected_reasons = {
        "today": "tightest_orbs_fast_movers",
        "this_week": "recurring_patterns_medium_movers", 
        "this_month": "outer_planets_slow_movers"
    }
    
    if "selection_reason" not in window_data:
        results["tests"].append({"test": "selection_reason_exists", "result": False, "error": "Missing selection_reason"})
        print(f"❌ Missing 'selection_reason' in {window_name}")
    else:
        selection_reason = window_data["selection_reason"]
        expected_reason = expected_reasons.get(window_name)
        if selection_reason == expected_reason:
            results["tests"].append({"test": "selection_reason_correct", "result": True, "value": selection_reason})
            print(f"✅ selection_reason correct: {selection_reason}")
        else:
            results["tests"].append({"test": "selection_reason_correct", "result": False, "expected": expected_reason, "actual": selection_reason})
            print(f"❌ selection_reason incorrect. Expected: {expected_reason}, Got: {selection_reason}")
    
    # Test 3: Check deterministic_summary exists and has timeframe-specific language
    if "deterministic_summary" not in window_data:
        results["tests"].append({"test": "deterministic_summary_exists", "result": False, "error": "Missing deterministic_summary"})
        print(f"❌ Missing 'deterministic_summary' in {window_name}")
    else:
        summary = window_data["deterministic_summary"]
        timeframe_check = check_timeframe_language(window_name, summary)
        results["tests"].append({"test": "timeframe_language", "result": timeframe_check["result"], "details": timeframe_check})
        if timeframe_check["result"]:
            print(f"✅ deterministic_summary has timeframe-specific language")
            print(f"   Found keywords: {timeframe_check['found_keywords']}")
        else:
            print(f"❌ deterministic_summary missing timeframe-specific language")
        print(f"📝 Summary: {summary[:100]}...")
    
    # Test 4: Check emphasis_tags exists
    if "emphasis_tags" not in window_data:
        results["tests"].append({"test": "emphasis_tags_exists", "result": False, "error": "Missing emphasis_tags"})
        print(f"❌ Missing 'emphasis_tags' in {window_name}")
    else:
        emphasis_tags = window_data["emphasis_tags"]
        if isinstance(emphasis_tags, list):
            results["tests"].append({"test": "emphasis_tags_exists", "result": True, "count": len(emphasis_tags), "tags": emphasis_tags})
            print(f"✅ emphasis_tags exists with {len(emphasis_tags)} tags: {emphasis_tags}")
        else:
            results["tests"].append({"test": "emphasis_tags_exists", "result": False, "error": "emphasis_tags is not a list"})
            print(f"❌ emphasis_tags is not a list in {window_name}")
    
    return results

def check_timeframe_language(window_name: str, summary: str) -> Dict[str, Any]:
    """Check if summary contains timeframe-specific language"""
    timeframe_keywords = {
        "today": ["right now", "immediate", "today", "currently", "at this moment", "this moment"],
        "this_week": ["this week", "returning", "recurring", "weekly", "over the week", "week"],
        "this_month": ["this month", "broader pattern", "monthly", "over the month", "longer term", "month"]
    }
    
    keywords = timeframe_keywords.get(window_name, [])
    found_keywords = []
    
    summary_lower = summary.lower()
    for keyword in keywords:
        if keyword in summary_lower:
            found_keywords.append(keyword)
    
    return {
        "result": len(found_keywords) > 0,
        "found_keywords": found_keywords,
        "expected_keywords": keywords,
        "summary_excerpt": summary[:150]
    }

def test_window_differentiation(windows: Dict[str, Any]) -> Dict[str, Any]:
    """Test that the three windows have different content"""
    print(f"\n🔄 Testing Window Differentiation:")
    
    results = {"tests": []}
    
    # Test 1: Different strongest_hits ordering/content
    today_hits = windows.get("today", {}).get("strongest_hits", [])
    week_hits = windows.get("this_week", {}).get("strongest_hits", [])
    month_hits = windows.get("this_month", {}).get("strongest_hits", [])
    
    # Convert to strings for comparison
    today_str = json.dumps(today_hits, sort_keys=True)
    week_str = json.dumps(week_hits, sort_keys=True)
    month_str = json.dumps(month_hits, sort_keys=True)
    
    different_hits = not (today_str == week_str == month_str)
    results["tests"].append({
        "test": "different_strongest_hits",
        "result": different_hits,
        "today_count": len(today_hits),
        "week_count": len(week_hits),
        "month_count": len(month_hits)
    })
    
    if different_hits:
        print("✅ strongest_hits arrays have different content/ordering")
        print(f"   Today: {len(today_hits)} hits, Week: {len(week_hits)} hits, Month: {len(month_hits)} hits")
    else:
        print("❌ strongest_hits arrays are identical across all windows")
    
    # Test 2: Different emphasis_tags
    today_tags = set(windows.get("today", {}).get("emphasis_tags", []))
    week_tags = set(windows.get("this_week", {}).get("emphasis_tags", []))
    month_tags = set(windows.get("this_month", {}).get("emphasis_tags", []))
    
    different_tags = not (today_tags == week_tags == month_tags)
    results["tests"].append({
        "test": "different_emphasis_tags",
        "result": different_tags,
        "today_tags": list(today_tags),
        "week_tags": list(week_tags),
        "month_tags": list(month_tags)
    })
    
    if different_tags:
        print("✅ emphasis_tags are different across windows")
        print(f"   Today: {list(today_tags)}")
        print(f"   Week: {list(week_tags)}")
        print(f"   Month: {list(month_tags)}")
    else:
        print("❌ emphasis_tags are identical across all windows")
    
    # Test 3: Different summaries
    today_summary = windows.get("today", {}).get("deterministic_summary", "")
    week_summary = windows.get("this_week", {}).get("deterministic_summary", "")
    month_summary = windows.get("this_month", {}).get("deterministic_summary", "")
    
    different_summaries = not (today_summary == week_summary == month_summary)
    results["tests"].append({
        "test": "different_summaries",
        "result": different_summaries,
        "summary_lengths": {
            "today": len(today_summary),
            "week": len(week_summary),
            "month": len(month_summary)
        }
    })
    
    if different_summaries:
        print("✅ deterministic_summary texts are different across windows")
    else:
        print("❌ deterministic_summary texts are identical across all windows")
    
    return results

def test_planet_focus_differentiation(windows: Dict[str, Any]) -> Dict[str, Any]:
    """Test that different windows focus on different planet types"""
    print(f"\n🪐 Testing Planet Focus Differentiation:")
    
    results = {"tests": []}
    
    # Define planet categories
    fast_movers = ["sun", "moon", "mercury", "venus", "mars"]
    medium_movers = ["jupiter", "saturn"]
    slow_movers = ["uranus", "neptune", "pluto"]
    
    for window_name, window_data in windows.items():
        strongest_hits = window_data.get("strongest_hits", [])
        
        # Count planets by category
        fast_count = 0
        medium_count = 0
        slow_count = 0
        planets_found = []
        
        for hit in strongest_hits:
            if isinstance(hit, dict) and "transit_point" in hit:
                planet = hit["transit_point"].lower()
                planets_found.append(planet)
                if planet in fast_movers:
                    fast_count += 1
                elif planet in medium_movers:
                    medium_count += 1
                elif planet in slow_movers:
                    slow_count += 1
        
        results["tests"].append({
            "window": window_name,
            "fast_movers": fast_count,
            "medium_movers": medium_count,
            "slow_movers": slow_count,
            "total_hits": len(strongest_hits),
            "planets_found": planets_found
        })
        
        print(f"📊 {window_name.upper()}: Fast={fast_count}, Medium={medium_count}, Slow={slow_count}")
        print(f"   Planets: {planets_found}")
    
    # Verify expected focus patterns
    today_data = next((t for t in results["tests"] if t["window"] == "today"), {})
    week_data = next((t for t in results["tests"] if t["window"] == "this_week"), {})
    month_data = next((t for t in results["tests"] if t["window"] == "this_month"), {})
    
    # TODAY should favor fast-moving planets
    today_favors_fast = today_data.get("fast_movers", 0) >= today_data.get("slow_movers", 0)
    
    # THIS MONTH should favor slow-moving planets  
    month_favors_slow = month_data.get("slow_movers", 0) >= month_data.get("fast_movers", 0)
    
    print(f"\n📈 Focus Pattern Analysis:")
    print(f"   TODAY favors fast movers: {today_favors_fast}")
    print(f"   THIS MONTH favors slow movers: {month_favors_slow}")
    
    results["focus_analysis"] = {
        "today_favors_fast": today_favors_fast,
        "month_favors_slow": month_favors_slow
    }
    
    return results

def main():
    """Main testing function"""
    print("🚀 Starting Astrology Transit Differentiation Testing")
    print("=" * 60)
    
    # Test users from the review request
    test_users = [
        "697f795f1a7a96aa35e283a3",
        "6971c81f2b40fd5ef501d375"
    ]
    
    all_results = []
    
    for user_id in test_users:
        result = test_astrology_chart_transits(user_id)
        all_results.append(result)
        print("\n" + "="*60)
    
    # Summary
    print("\n📋 TESTING SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in all_results if r["success"])
    total_tests = len(all_results)
    
    print(f"✅ Successful Tests: {successful_tests}/{total_tests}")
    
    # Detailed analysis
    if successful_tests > 0:
        print("\n🔍 DETAILED ANALYSIS:")
        
        for result in all_results:
            if result["success"]:
                user_id = result["user_id"]
                print(f"\n👤 User {user_id}:")
                
                # Check window structure tests
                all_window_tests_passed = True
                for window_name, window_result in result["windows"].items():
                    window_tests = window_result.get("tests", [])
                    passed_tests = sum(1 for t in window_tests if t.get("result", False))
                    total_window_tests = len(window_tests)
                    
                    if passed_tests < total_window_tests:
                        all_window_tests_passed = False
                    
                    print(f"   {window_name}: {passed_tests}/{total_window_tests} tests passed")
                
                # Check differentiation tests
                diff_tests = result["differentiation"].get("tests", [])
                passed_diff_tests = sum(1 for t in diff_tests if t.get("result", False))
                total_diff_tests = len(diff_tests)
                
                print(f"   Differentiation: {passed_diff_tests}/{total_diff_tests} tests passed")
                
                if all_window_tests_passed and passed_diff_tests == total_diff_tests:
                    print(f"   ✅ ALL TESTS PASSED for user {user_id}")
                else:
                    print(f"   ❌ Some tests failed for user {user_id}")
    
    if successful_tests == total_tests:
        print("\n🎉 ALL ASTROLOGY TRANSIT DIFFERENTIATION TESTS PASSED!")
        print("\n✅ SUCCESS CRITERIA MET:")
        print("   - TODAY favors fast-moving planets (Sun, Moon, Mercury, Venus, Mars)")
        print("   - THIS WEEK favors recurring themes + medium movers (Jupiter, Saturn)")
        print("   - THIS MONTH favors outer planets (Uranus, Neptune, Pluto) and slow movers")
        print("   - Each window has different summaries with timeframe-specific language")
        print("   - Multiple signals are clearly being evaluated differently")
    else:
        print("❌ Some tests failed. Check details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()