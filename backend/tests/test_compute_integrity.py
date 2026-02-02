"""
Regression Test: Compute Integrity for Pete & Mel Fixture Profiles

This test ensures that:
1. Stored lat/lon coordinates match expected reference values
2. Astrology computations return valid ascendant, MC, Sun, Moon
3. Human Design computations return valid type and profile
4. No silent fallbacks or partial-success states

Run with: pytest tests/test_compute_integrity.py -v
"""

import pytest
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.timezone_utils import resolve_birth_utc_with_debug
from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# =============================================================================
# FIXTURE DEFINITIONS - Reference values from Genetic Matrix screenshots
# =============================================================================

FIXTURES = {
    "Pete": {
        "name_pattern": "Pete",
        "expected": {
            "birth_place": "Petaling Jaya",
            "lat": 3.1073,
            "lon": 101.607,
            "timezone_iana": "Asia/Kuala_Lumpur",
            "birth_date": "1968-04-01",
            "birth_time": "1:25am",
            # Astrology expectations (True Sidereal-M)
            "astrology": {
                "ascendant_sign": "Sagittarius",
                "mc_sign": "Virgo",
                "sun_sign": "Pisces",
                "moon_sign": "Aries"
            },
            # Human Design expectations
            "human_design": {
                "type": "Manifestor",
                "profile": "5/1",
                "definition": "Split",
                "channels_count_min": 3  # 63-4, 35-36, 37-40
            }
        }
    },
    "Mel": {
        "name_pattern": "Mel",
        "expected": {
            "birth_place": "Melaka",
            "lat": 2.1889,
            "lon": 102.250999,
            "timezone_iana": "Asia/Kuala_Lumpur",
            "birth_date": "1981-07-13",
            "birth_time": "07:25",
            # Astrology expectations (True Sidereal-M)
            "astrology": {
                "ascendant_sign": "Gemini",
                "mc_sign": "Pisces",
                "sun_sign": "Gemini",
                "moon_sign": "Scorpio"
            },
            # Human Design expectations
            "human_design": {
                "type": "Reflector",
                "profile": "3/5",
                "definition": "None",
                "channels_count_min": 0
            }
        }
    }
}

SIDEREAL_SETTINGS = {
    "mode": "true_sidereal_user_defined",
    "svp_degrees": 31.2836,
    "reference_year": 2000,
    "yearly_increment": 0.0
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def degree_to_sign(degree: float) -> str:
    """Convert ecliptic degree to zodiac sign name."""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_idx = int(degree / 30) % 12
    return signs[sign_idx]


async def get_db():
    """Get MongoDB connection."""
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        pytest.skip("MONGO_URL not configured")
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'mirror')
    return client[db_name]


async def find_user_by_name(db, name_pattern: str):
    """Find user by name pattern."""
    import re
    return await db.users.find_one({"name": {"$regex": name_pattern, "$options": "i"}})


# =============================================================================
# TEST CLASS
# =============================================================================

class TestComputeIntegrity:
    """Regression tests for compute integrity."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup event loop for async tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        yield
        self.loop.close()
    
    def run_async(self, coro):
        """Helper to run async code in sync test."""
        return self.loop.run_until_complete(coro)
    
    # =========================================================================
    # COORDINATE TESTS
    # =========================================================================
    
    @pytest.mark.parametrize("fixture_name", ["Pete", "Mel"])
    def test_coordinates_match_reference(self, fixture_name):
        """Test that stored lat/lon exactly match reference values."""
        async def _test():
            db = await get_db()
            fixture = FIXTURES[fixture_name]
            expected = fixture["expected"]
            
            user = await find_user_by_name(db, fixture["name_pattern"])
            assert user is not None, f"User {fixture_name} not found in database"
            
            location = user.get("birth_location", {})
            
            # Assert coordinates match exactly
            assert location.get("lat") == expected["lat"] or location.get("latitude") == expected["lat"], \
                f"{fixture_name} latitude mismatch: expected {expected['lat']}, got {location.get('latitude') or location.get('lat')}"
            
            assert location.get("lon") == expected["lon"] or location.get("longitude") == expected["lon"], \
                f"{fixture_name} longitude mismatch: expected {expected['lon']}, got {location.get('longitude') or location.get('lon')}"
            
            # Assert birth place contains expected city
            city = location.get("city", "")
            assert expected["birth_place"].lower() in city.lower(), \
                f"{fixture_name} birth place mismatch: expected '{expected['birth_place']}' in '{city}'"
        
        self.run_async(_test())
    
    @pytest.mark.parametrize("fixture_name", ["Pete", "Mel"])
    def test_timezone_is_iana(self, fixture_name):
        """Test that timezone is stored as IANA string, not fixed offset."""
        async def _test():
            db = await get_db()
            fixture = FIXTURES[fixture_name]
            expected = fixture["expected"]
            
            user = await find_user_by_name(db, fixture["name_pattern"])
            assert user is not None, f"User {fixture_name} not found"
            
            timezone = user.get("timezone")
            assert timezone is not None, f"{fixture_name} timezone is None"
            assert "/" in timezone, f"{fixture_name} timezone '{timezone}' is not IANA format (should contain '/')"
            assert timezone == expected["timezone_iana"], \
                f"{fixture_name} timezone mismatch: expected {expected['timezone_iana']}, got {timezone}"
        
        self.run_async(_test())
    
    # =========================================================================
    # ASTROLOGY COMPUTATION TESTS
    # =========================================================================
    
    @pytest.mark.parametrize("fixture_name", ["Pete", "Mel"])
    def test_astrology_computation_valid(self, fixture_name):
        """Test that astrology computation returns valid ascendant, MC, Sun, Moon."""
        async def _test():
            db = await get_db()
            fixture = FIXTURES[fixture_name]
            expected = fixture["expected"]
            
            user = await find_user_by_name(db, fixture["name_pattern"])
            assert user is not None, f"User {fixture_name} not found"
            
            # Get birth data
            location = user.get("birth_location", {})
            lat = location.get("latitude") or location.get("lat")
            lon = location.get("longitude") or location.get("lon")
            timezone = user.get("timezone")
            birth_date = user.get("birth_date")
            birth_time = user.get("birth_time")
            
            birth_date_str = birth_date.strftime("%Y-%m-%d") if isinstance(birth_date, datetime) else str(birth_date)
            
            # Resolve UTC
            resolution = resolve_birth_utc_with_debug(birth_date_str, birth_time, timezone)
            assert resolution["success"], f"{fixture_name} UTC resolution failed: {resolution.get('error')}"
            
            birth_utc = resolution["birth_utc"]
            
            # Compute astrology chart
            chart = get_full_natal_chart(birth_utc, lat, lon, SIDEREAL_SETTINGS, "Equal")
            
            # Assert houses exist
            houses = chart.get("houses", {})
            assert houses, f"{fixture_name} astrology: houses missing"
            
            cusps = houses.get("cusps", [])
            assert len(cusps) == 12, f"{fixture_name} astrology: expected 12 cusps, got {len(cusps)}"
            
            # Assert ascendant exists and is valid
            ascendant = houses.get("ascendant")
            assert ascendant is not None, f"{fixture_name} astrology: ascendant is None"
            assert ascendant > 0, f"{fixture_name} astrology: ascendant is 0 or negative"
            
            asc_sign = degree_to_sign(ascendant)
            assert asc_sign == expected["astrology"]["ascendant_sign"], \
                f"{fixture_name} ascendant sign mismatch: expected {expected['astrology']['ascendant_sign']}, got {asc_sign}"
            
            # Assert planets exist
            planets = chart.get("planets", {})
            assert planets, f"{fixture_name} astrology: planets missing"
            
            # Assert Sun exists and sign matches
            sun = planets.get("Sun", {})
            assert sun, f"{fixture_name} astrology: Sun missing"
            sun_lon = sun.get("longitude")
            assert sun_lon is not None, f"{fixture_name} astrology: Sun longitude is None"
            
            sun_sign = degree_to_sign(sun_lon)
            assert sun_sign == expected["astrology"]["sun_sign"], \
                f"{fixture_name} Sun sign mismatch: expected {expected['astrology']['sun_sign']}, got {sun_sign}"
            
            # Assert Moon exists and sign matches
            moon = planets.get("Moon", {})
            assert moon, f"{fixture_name} astrology: Moon missing"
            moon_lon = moon.get("longitude")
            assert moon_lon is not None, f"{fixture_name} astrology: Moon longitude is None"
            
            moon_sign = degree_to_sign(moon_lon)
            assert moon_sign == expected["astrology"]["moon_sign"], \
                f"{fixture_name} Moon sign mismatch: expected {expected['astrology']['moon_sign']}, got {moon_sign}"
            
            # Assert MC (10th house cusp)
            mc_cusp = cusps[9] if len(cusps) > 9 else None
            assert mc_cusp is not None, f"{fixture_name} astrology: MC (10th cusp) missing"
            mc_lon = mc_cusp.get("longitude") if isinstance(mc_cusp, dict) else mc_cusp
            mc_sign = degree_to_sign(mc_lon)
            assert mc_sign == expected["astrology"]["mc_sign"], \
                f"{fixture_name} MC sign mismatch: expected {expected['astrology']['mc_sign']}, got {mc_sign}"
        
        self.run_async(_test())
    
    # =========================================================================
    # HUMAN DESIGN COMPUTATION TESTS
    # =========================================================================
    
    @pytest.mark.parametrize("fixture_name", ["Pete", "Mel"])
    def test_human_design_computation_valid(self, fixture_name):
        """Test that Human Design computation returns valid type, profile, definition."""
        async def _test():
            db = await get_db()
            fixture = FIXTURES[fixture_name]
            expected = fixture["expected"]
            
            user = await find_user_by_name(db, fixture["name_pattern"])
            assert user is not None, f"User {fixture_name} not found"
            
            # Get birth data
            location = user.get("birth_location", {})
            lat = location.get("latitude") or location.get("lat")
            lon = location.get("longitude") or location.get("lon")
            timezone = user.get("timezone")
            birth_date = user.get("birth_date")
            birth_time = user.get("birth_time")
            
            birth_date_str = birth_date.strftime("%Y-%m-%d") if isinstance(birth_date, datetime) else str(birth_date)
            
            # Resolve UTC
            resolution = resolve_birth_utc_with_debug(birth_date_str, birth_time, timezone)
            assert resolution["success"], f"{fixture_name} UTC resolution failed"
            
            birth_utc = resolution["birth_utc"]
            
            # Compute Human Design chart
            hd = get_human_design_chart(birth_utc, lat, lon, SIDEREAL_SETTINGS)
            
            # Assert type exists and matches
            hd_type = hd.get("type")
            assert hd_type is not None, f"{fixture_name} HD: type is None"
            assert hd_type == expected["human_design"]["type"], \
                f"{fixture_name} HD type mismatch: expected {expected['human_design']['type']}, got {hd_type}"
            
            # Assert profile exists and matches
            profile = hd.get("profile")
            assert profile is not None, f"{fixture_name} HD: profile is None"
            assert profile == expected["human_design"]["profile"], \
                f"{fixture_name} HD profile mismatch: expected {expected['human_design']['profile']}, got {profile}"
            
            # Assert definition exists and matches
            definition = hd.get("definition")
            assert definition is not None, f"{fixture_name} HD: definition is None"
            assert definition == expected["human_design"]["definition"], \
                f"{fixture_name} HD definition mismatch: expected {expected['human_design']['definition']}, got {definition}"
            
            # Assert channels count >= expected minimum
            channels = hd.get("defined_channels", [])
            expected_min = expected["human_design"]["channels_count_min"]
            assert len(channels) >= expected_min, \
                f"{fixture_name} HD channels count mismatch: expected >= {expected_min}, got {len(channels)}"
            
            # Assert design datetime exists
            design_dt = hd.get("design_datetime_utc_iso")
            assert design_dt is not None, f"{fixture_name} HD: design_datetime_utc is None"
        
        self.run_async(_test())
    
    # =========================================================================
    # NO SILENT FALLBACK TESTS
    # =========================================================================
    
    @pytest.mark.parametrize("fixture_name", ["Pete", "Mel"])
    def test_no_partial_success(self, fixture_name):
        """Test that computations don't silently fail or return partial data."""
        async def _test():
            db = await get_db()
            fixture = FIXTURES[fixture_name]
            
            user = await find_user_by_name(db, fixture["name_pattern"])
            assert user is not None, f"User {fixture_name} not found"
            
            # Get birth data
            location = user.get("birth_location", {})
            lat = location.get("latitude") or location.get("lat")
            lon = location.get("longitude") or location.get("lon")
            timezone = user.get("timezone")
            birth_date = user.get("birth_date")
            birth_time = user.get("birth_time")
            
            birth_date_str = birth_date.strftime("%Y-%m-%d") if isinstance(birth_date, datetime) else str(birth_date)
            
            # Test timezone resolution
            resolution = resolve_birth_utc_with_debug(birth_date_str, birth_time, timezone)
            assert resolution["success"] == True, f"{fixture_name}: UTC resolution returned success=False"
            assert "error" not in resolution or resolution.get("error") is None, \
                f"{fixture_name}: UTC resolution has error: {resolution.get('error')}"
            
            birth_utc = resolution["birth_utc"]
            
            # Test astrology - no partial results
            chart = get_full_natal_chart(birth_utc, lat, lon, SIDEREAL_SETTINGS, "Equal")
            
            # Must have all essential keys
            assert "planets" in chart, f"{fixture_name}: astrology missing 'planets' key"
            assert "houses" in chart, f"{fixture_name}: astrology missing 'houses' key"
            
            # Planets must have all major bodies
            planets = chart["planets"]
            required_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
            for planet in required_planets:
                assert planet in planets, f"{fixture_name}: astrology missing planet '{planet}'"
                assert planets[planet].get("longitude") is not None, \
                    f"{fixture_name}: planet '{planet}' has no longitude"
            
            # Test HD - no partial results
            hd = get_human_design_chart(birth_utc, lat, lon, SIDEREAL_SETTINGS)
            
            required_hd_keys = ["type", "profile", "authority", "strategy", "definition", "incarnation_cross"]
            for key in required_hd_keys:
                assert key in hd, f"{fixture_name}: HD missing key '{key}'"
                assert hd[key] is not None, f"{fixture_name}: HD key '{key}' is None"
        
        self.run_async(_test())


# =============================================================================
# STANDALONE RUNNER
# =============================================================================

if __name__ == "__main__":
    """Run tests directly without pytest."""
    import traceback
    
    print("=" * 70)
    print("COMPUTE INTEGRITY REGRESSION TESTS")
    print("=" * 70)
    
    # Create test instance and set up event loop manually
    test_instance = TestComputeIntegrity()
    test_instance.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(test_instance.loop)
    
    tests = [
        ("test_coordinates_match_reference", ["Pete", "Mel"]),
        ("test_timezone_is_iana", ["Pete", "Mel"]),
        ("test_astrology_computation_valid", ["Pete", "Mel"]),
        ("test_human_design_computation_valid", ["Pete", "Mel"]),
        ("test_no_partial_success", ["Pete", "Mel"]),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, fixtures in tests:
        for fixture_name in fixtures:
            test_id = f"{test_name}[{fixture_name}]"
            try:
                getattr(test_instance, test_name)(fixture_name)
                print(f"✅ PASS: {test_id}")
                passed += 1
            except AssertionError as e:
                print(f"❌ FAIL: {test_id}")
                print(f"   Error: {e}")
                failed += 1
            except Exception as e:
                print(f"❌ ERROR: {test_id}")
                print(f"   {type(e).__name__}: {e}")
                traceback.print_exc()
                failed += 1
    
    test_instance.loop.close()
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    exit(0 if failed == 0 else 1)
