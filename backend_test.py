#!/usr/bin/env python3
"""
Backend Testing Suite for Project Mirror
Testing Transit Engine endpoints:
- POST /api/compute/transits/now (Phase 1)
- POST /api/compute/transits/window (Phase 2 - Window Scanner)
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://mirror-lens-fixes.emergent.host/api"  # Using public URL for testing
TEST_USER_ID = "6971c8f681beab3a8955b255"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_symbol} {test_name}")
    if details:
        print(f"    {details}")

def test_transit_basic_current_time():
    """Test 1: Basic transit calculation (current time)"""
    test_name = "Basic Transit Calculation (Current Time)"
    
    try:
        payload = {
            "user_id": TEST_USER_ID,
            "orb_deg": 2,
            "include_houses": True
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/now", json=payload, timeout=30)
        
        if response.status_code != 200:
            log_test(test_name, "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify response structure
        required_fields = ["meta", "timestamp_utc", "transiting_planets", "aspects_to_natal_now"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
            return False
        
        # Verify meta structure
        meta = data["meta"]
        expected_meta_fields = ["ayanamsa", "house_system", "orb_deg"]
        missing_meta = [field for field in expected_meta_fields if field not in meta]
        
        if missing_meta:
            log_test(test_name, "FAIL", f"Missing meta fields: {missing_meta}")
            return False
        
        # Verify meta values
        if meta["ayanamsa"] != "fixed_sv_31.2836":
            log_test(test_name, "FAIL", f"Expected ayanamsa 'fixed_sv_31.2836', got '{meta['ayanamsa']}'")
            return False
        
        if meta["house_system"] != "equal":
            log_test(test_name, "FAIL", f"Expected house_system 'equal', got '{meta['house_system']}'")
            return False
        
        if meta["orb_deg"] != 2:
            log_test(test_name, "FAIL", f"Expected orb_deg 2, got {meta['orb_deg']}")
            return False
        
        # Verify transiting planets (should have 10 planets)
        transiting_planets = data["transiting_planets"]
        expected_planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
        
        for planet in expected_planets:
            if planet not in transiting_planets:
                log_test(test_name, "FAIL", f"Missing planet: {planet}")
                return False
            
            planet_data = transiting_planets[planet]
            required_planet_fields = ["longitude", "sign", "retrograde"]
            if data.get("include_houses", True):
                required_planet_fields.append("house")
            
            missing_planet_fields = [field for field in required_planet_fields if field not in planet_data]
            if missing_planet_fields:
                log_test(test_name, "FAIL", f"Planet {planet} missing fields: {missing_planet_fields}")
                return False
            
            # Verify house is integer 1-12
            if "house" in planet_data:
                house = planet_data["house"]
                if not isinstance(house, int) or house < 1 or house > 12:
                    log_test(test_name, "FAIL", f"Planet {planet} invalid house: {house}")
                    return False
        
        # Verify aspects structure
        aspects = data["aspects_to_natal_now"]
        if not isinstance(aspects, list):
            log_test(test_name, "FAIL", f"aspects_to_natal_now should be list, got {type(aspects)}")
            return False
        
        # Check aspect structure if any aspects exist
        if aspects:
            aspect = aspects[0]
            required_aspect_fields = ["transit_planet", "aspect", "natal_body", "orb", "exact_angle_delta"]
            missing_aspect_fields = [field for field in required_aspect_fields if field not in aspect]
            if missing_aspect_fields:
                log_test(test_name, "FAIL", f"Aspect missing fields: {missing_aspect_fields}")
                return False
        
        log_test(test_name, "PASS", f"Response contains {len(transiting_planets)} planets and {len(aspects)} aspects")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_fixed_timestamp():
    """Test 2: Fixed timestamp test (deterministic)"""
    test_name = "Fixed Timestamp Test (Deterministic)"
    
    try:
        payload = {
            "user_id": TEST_USER_ID,
            "timestamp_utc": "2026-03-02T09:00:00Z",
            "orb_deg": 2,
            "include_houses": True
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/now", json=payload, timeout=30)
        
        if response.status_code != 200:
            log_test(test_name, "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify timestamp matches exactly
        if data["timestamp_utc"] != "2026-03-02T09:00:00Z":
            log_test(test_name, "FAIL", f"Expected timestamp '2026-03-02T09:00:00Z', got '{data['timestamp_utc']}'")
            return False
        
        # Verify same response structure as test 1
        required_fields = ["meta", "timestamp_utc", "transiting_planets", "aspects_to_natal_now"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
            return False
        
        # Verify we have 10 planets
        transiting_planets = data["transiting_planets"]
        if len(transiting_planets) != 10:
            log_test(test_name, "FAIL", f"Expected 10 planets, got {len(transiting_planets)}")
            return False
        
        log_test(test_name, "PASS", f"Deterministic timestamp working, {len(transiting_planets)} planets computed")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_without_houses():
    """Test 3: Without houses"""
    test_name = "Without Houses Test"
    
    try:
        payload = {
            "user_id": TEST_USER_ID,
            "timestamp_utc": "2026-03-02T09:00:00Z",
            "orb_deg": 2,
            "include_houses": False
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/now", json=payload, timeout=30)
        
        if response.status_code != 200:
            log_test(test_name, "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify planets should NOT have "house" field
        transiting_planets = data["transiting_planets"]
        
        for planet_name, planet_data in transiting_planets.items():
            if "house" in planet_data:
                log_test(test_name, "FAIL", f"Planet {planet_name} should not have 'house' field when include_houses=false")
                return False
        
        # Verify other fields are still present
        for planet_name, planet_data in transiting_planets.items():
            required_fields = ["longitude", "sign", "retrograde"]
            missing_fields = [field for field in required_fields if field not in planet_data]
            if missing_fields:
                log_test(test_name, "FAIL", f"Planet {planet_name} missing fields: {missing_fields}")
                return False
        
        log_test(test_name, "PASS", f"Houses correctly excluded, {len(transiting_planets)} planets without house field")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_invalid_user():
    """Test 4: Error case - Invalid user_id"""
    test_name = "Invalid User ID Error Test"
    
    try:
        payload = {
            "user_id": "invalid_user_id_12345",
            "orb_deg": 2
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/now", json=payload, timeout=30)
        
        # Should return 404 error
        if response.status_code != 404:
            log_test(test_name, "FAIL", f"Expected 404 status, got {response.status_code}")
            return False
        
        # Check error message
        try:
            error_data = response.json()
            if "detail" in error_data:
                detail = error_data["detail"]
                if "Natal chart not found" not in detail:
                    log_test(test_name, "FAIL", f"Expected 'Natal chart not found' in error, got: {detail}")
                    return False
            else:
                log_test(test_name, "FAIL", f"No 'detail' field in error response: {error_data}")
                return False
        except:
            # If response is not JSON, check if it contains the expected message
            if "Natal chart not found" not in response.text:
                log_test(test_name, "FAIL", f"Expected 'Natal chart not found' in response: {response.text}")
                return False
        
        log_test(test_name, "PASS", "Correctly returned 404 error for invalid user_id")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_window_30_days():
    """Test 5: Transit Window Scanner - 30-day window (deterministic test)"""
    test_name = "Transit Window Scanner - 30-day window"
    
    try:
        payload = {
            "user_id": TEST_USER_ID,
            "from_utc": "2026-03-02T00:00:00Z",
            "window_days": 30,
            "orb_deg": 2,
            "include_houses": True,
            "granularity": "daily"
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/window", json=payload, timeout=30)
        
        if response.status_code != 200:
            log_test(test_name, "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify response structure
        required_fields = ["meta", "window", "exact_hits", "ingresses", "stations", "house_activation", "daily_summary"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
            return False
        
        # Verify meta structure
        meta = data["meta"]
        expected_meta = {
            "ayanamsa": "fixed_sv_31.2836",
            "house_system": "equal",
            "orb_deg": 2,
            "window_days": 30,
            "granularity": "daily"
        }
        
        for key, expected_value in expected_meta.items():
            if meta.get(key) != expected_value:
                log_test(test_name, "FAIL", f"Meta field {key}: expected {expected_value}, got {meta.get(key)}")
                return False
        
        # Verify window structure
        window = data["window"]
        if "from_utc" not in window or "to_utc" not in window:
            log_test(test_name, "FAIL", "Window missing from_utc or to_utc")
            return False
        
        # Verify arrays are present
        exact_hits = data["exact_hits"]
        ingresses = data["ingresses"]
        stations = data["stations"]
        
        # Check exact_hits structure
        if exact_hits:
            hit = exact_hits[0]
            required_hit_fields = ["timestamp_utc", "transit_planet", "aspect", "natal_body", "orb", "exact_angle_delta"]
            missing_hit_fields = [field for field in required_hit_fields if field not in hit]
            if missing_hit_fields:
                log_test(test_name, "FAIL", f"exact_hits missing fields: {missing_hit_fields}")
                return False
            
            # Verify orb is within specified range
            if hit["orb"] > 2.0:
                log_test(test_name, "FAIL", f"Orb {hit['orb']} exceeds specified orb_deg of 2")
                return False
        
        # Check ingresses structure
        if ingresses:
            ingress = ingresses[0]
            required_ingress_fields = ["timestamp_utc", "planet", "from_sign", "to_sign", "longitude"]
            if payload["include_houses"]:
                required_ingress_fields.append("house")
            
            missing_ingress_fields = [field for field in required_ingress_fields if field not in ingress]
            if missing_ingress_fields:
                log_test(test_name, "FAIL", f"ingresses missing fields: {missing_ingress_fields}")
                return False
        
        # Check stations structure
        if stations:
            station = stations[0]
            required_station_fields = ["timestamp_utc", "planet", "type", "longitude", "sign"]
            if payload["include_houses"]:
                required_station_fields.append("house")
            
            missing_station_fields = [field for field in required_station_fields if field not in station]
            if missing_station_fields:
                log_test(test_name, "FAIL", f"stations missing fields: {missing_station_fields}")
                return False
            
            # Verify station type
            if station["type"] not in ["station_retrograde", "station_direct"]:
                log_test(test_name, "FAIL", f"Invalid station type: {station['type']}")
                return False
        
        # Check house_activation structure
        house_activation = data["house_activation"]
        if "top_houses" not in house_activation or "scores" not in house_activation:
            log_test(test_name, "FAIL", "house_activation missing top_houses or scores")
            return False
        
        # Verify top_houses is sorted by score (highest first)
        top_houses = house_activation["top_houses"]
        if len(top_houses) > 1:
            for i in range(len(top_houses) - 1):
                if top_houses[i].get("score", 0) < top_houses[i + 1].get("score", 0):
                    log_test(test_name, "FAIL", "top_houses not sorted by score (highest first)")
                    return False
        
        # Check daily_summary structure
        daily_summary = data["daily_summary"]
        if daily_summary:
            day = daily_summary[0]
            required_day_fields = ["date", "peak_events", "top_houses"]
            missing_day_fields = [field for field in required_day_fields if field not in day]
            if missing_day_fields:
                log_test(test_name, "FAIL", f"daily_summary missing fields: {missing_day_fields}")
                return False
        
        log_test(test_name, "PASS", f"Response structure valid. exact_hits: {len(exact_hits)}, ingresses: {len(ingresses)}, stations: {len(stations)}")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_window_90_days():
    """Test 6: Transit Window Scanner - 90-day window"""
    test_name = "Transit Window Scanner - 90-day window"
    
    try:
        payload = {
            "user_id": TEST_USER_ID,
            "from_utc": "2026-03-02T00:00:00Z",
            "window_days": 90,
            "orb_deg": 2,
            "include_houses": True,
            "granularity": "daily"
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/window", json=payload, timeout=30)
        
        if response.status_code != 200:
            log_test(test_name, "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify basic structure (same as 30-day test)
        required_fields = ["meta", "window", "exact_hits", "ingresses", "stations", "house_activation", "daily_summary"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
            return False
        
        # Verify meta shows 90 days
        meta = data["meta"]
        if meta.get("window_days") != 90:
            log_test(test_name, "FAIL", f"Meta window_days: expected 90, got {meta.get('window_days')}")
            return False
        
        # Should have events (generally more than 30-day window)
        exact_hits = data["exact_hits"]
        ingresses = data["ingresses"]
        
        log_test(test_name, "PASS", f"Response structure valid. exact_hits: {len(exact_hits)}, ingresses: {len(ingresses)}")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_window_invalid_days():
    """Test 7: Transit Window Scanner - Invalid window_days (should fail)"""
    test_name = "Transit Window Scanner - Invalid window_days"
    
    try:
        payload = {
            "user_id": TEST_USER_ID,
            "window_days": 45  # Invalid - should be 30 or 90
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/window", json=payload, timeout=30)
        
        if response.status_code != 400:
            log_test(test_name, "FAIL", f"Expected 400, got {response.status_code}")
            return False
        
        data = response.json()
        if "window_days must be 30 or 90" not in data.get("detail", ""):
            log_test(test_name, "FAIL", f"Unexpected error message: {data.get('detail')}")
            return False
        
        log_test(test_name, "PASS", "Correctly rejected invalid window_days with 400 error")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_transit_window_invalid_user():
    """Test 8: Transit Window Scanner - Invalid user_id"""
    test_name = "Transit Window Scanner - Invalid user_id"
    
    try:
        payload = {
            "user_id": "invalid_user_12345",
            "window_days": 30
        }
        
        response = requests.post(f"{BASE_URL}/compute/transits/window", json=payload, timeout=30)
        
        if response.status_code != 404:
            log_test(test_name, "FAIL", f"Expected 404, got {response.status_code}")
            return False
        
        data = response.json()
        if "Natal chart not found" not in data.get("detail", ""):
            log_test(test_name, "FAIL", f"Unexpected error message: {data.get('detail')}")
            return False
        
        log_test(test_name, "PASS", "Correctly rejected invalid user_id with 404 error")
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all transit engine tests"""
    print("=" * 80)
    print("TRANSIT ENGINE TESTING - PHASE 1 & PHASE 2")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("Endpoints:")
    print("  - POST /api/compute/transits/now (Phase 1)")
    print("  - POST /api/compute/transits/window (Phase 2 - Window Scanner)")
    print("=" * 80)
    
    tests = [
        # Phase 1 tests (existing)
        test_transit_basic_current_time,
        test_transit_fixed_timestamp,
        test_transit_without_houses,
        test_transit_invalid_user,
        # Phase 2 tests (new)
        test_transit_window_30_days,
        test_transit_window_90_days,
        test_transit_window_invalid_days,
        test_transit_window_invalid_user
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
        print()  # Add spacing between tests
    
    print("=" * 80)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Both Transit Engine phases are working correctly!")
    else:
        print(f"⚠️  {total - passed} test(s) failed - Transit Engine needs attention")
    
    print("=" * 80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)