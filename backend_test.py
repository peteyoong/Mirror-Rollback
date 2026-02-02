#!/usr/bin/env python3
"""
Backend Test Suite for Project Mirror - Astrology Chart Auto-Migration
Tests the newly implemented auto-migration feature for old-format astrology charts.
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import aiohttp
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Configuration
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# Get backend URL from frontend .env
frontend_env_path = Path(__file__).parent / "frontend" / ".env"
backend_url = None
if frontend_env_path.exists():
    with open(frontend_env_path, 'r') as f:
        for line in f:
            if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip()
                break

if not backend_url:
    print("❌ Could not find EXPO_PUBLIC_BACKEND_URL in frontend/.env")
    sys.exit(1)

API_BASE_URL = f"{backend_url}/api"

# Test user ID from the review request
TEST_USER_ID = "6971c81f2b40fd5ef501d375"

class AstrologyMigrationTester:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.session = None
        
    async def setup_session(self):
        """Setup HTTP session for API calls"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.client.close()
        
    async def verify_user_exists(self):
        """Verify the test user exists and has required data"""
        print(f"🔍 Verifying user {TEST_USER_ID} exists...")
        
        user = await self.db.users.find_one({"_id": ObjectId(TEST_USER_ID)})
        if not user:
            print(f"❌ User {TEST_USER_ID} not found in database")
            return False
            
        # Check required fields for migration
        required_fields = ['timezone', 'birth_time', 'birth_date', 'birth_location']
        missing_fields = []
        
        for field in required_fields:
            if not user.get(field):
                missing_fields.append(field)
                
        if missing_fields:
            print(f"❌ User missing required fields for migration: {missing_fields}")
            return False
            
        print(f"✅ User exists with timezone: {user.get('timezone')}, birth_time: {user.get('birth_time')}")
        return True
        
    async def setup_old_format_chart(self):
        """Setup old-format astrology chart in database"""
        print("🔧 Setting up old-format astrology chart...")
        
        # Create old-format chart data (legacy string format)
        old_chart_data = {
            "sun_sign": "Pisces",
            "moon_sign": "Aries", 
            "rising_sign": "Unknown"
        }
        
        # Update the chart to have old format (remove planets and houses keys)
        result = await self.db.charts.update_one(
            {"user_id": TEST_USER_ID},
            {
                "$set": {
                    "astrology": old_chart_data,
                    "test_setup_at": datetime.now(timezone.utc).isoformat()
                },
                "$unset": {
                    "astrology.planets": "",
                    "astrology.houses": "",
                    "migration_info": ""
                }
            }
        )
        
        if result.matched_count == 0:
            print(f"❌ No chart found for user {TEST_USER_ID}")
            return False
            
        print(f"✅ Set up old-format chart: {old_chart_data}")
        return True
        
    async def verify_old_format(self):
        """Verify the chart is in old format before migration"""
        print("🔍 Verifying chart is in old format...")
        
        chart = await self.db.charts.find_one({"user_id": TEST_USER_ID})
        if not chart:
            print("❌ Chart not found")
            return False
            
        astro = chart.get('astrology', {})
        
        # Check it has old format characteristics
        has_sun_sign = 'sun_sign' in astro
        has_planets = 'planets' in astro
        has_houses = 'houses' in astro
        
        print(f"📊 Chart format check:")
        print(f"   - Has sun_sign: {has_sun_sign}")
        print(f"   - Has planets: {has_planets}")
        print(f"   - Has houses: {has_houses}")
        
        if has_sun_sign and not has_planets:
            print("✅ Chart is in old legacy format (ready for migration)")
            return True
        else:
            print("❌ Chart is not in expected old format")
            return False
            
    async def call_astrology_deep_dive(self):
        """Call the astrology deep-dive endpoint to trigger migration"""
        print("🚀 Calling astrology deep-dive endpoint to trigger migration...")
        
        url = f"{API_BASE_URL}/astrology/deep-dive/{TEST_USER_ID}"
        
        try:
            async with self.session.get(url) as response:
                status_code = response.status
                response_data = await response.json()
                
                print(f"📡 API Response:")
                print(f"   - Status Code: {status_code}")
                print(f"   - Success: {response_data.get('success')}")
                
                if response_data.get('success'):
                    core_placements = response_data.get('core_placements', {})
                    print(f"   - Core Placements: {core_placements}")
                    
                    # Check if ascendant is no longer "Unknown"
                    ascendant = core_placements.get('ascendant')
                    if ascendant and ascendant != "Unknown":
                        print(f"✅ Migration successful - Ascendant: {ascendant}")
                        return True, response_data
                    else:
                        print(f"❌ Migration may have failed - Ascendant still: {ascendant}")
                        return False, response_data
                else:
                    error = response_data.get('error', 'Unknown error')
                    print(f"❌ API call failed: {error}")
                    return False, response_data
                    
        except Exception as e:
            print(f"❌ Exception calling API: {e}")
            return False, {}
            
    async def verify_migration_occurred(self):
        """Verify the chart was migrated to new format"""
        print("🔍 Verifying migration occurred in database...")
        
        chart = await self.db.charts.find_one({"user_id": TEST_USER_ID})
        if not chart:
            print("❌ Chart not found")
            return False
            
        astro = chart.get('astrology', {})
        migration_info = chart.get('migration_info', {})
        
        # Check new format characteristics
        has_planets = 'planets' in astro
        has_houses = 'houses' in astro
        has_migration_info = bool(migration_info)
        
        print(f"📊 Post-migration chart check:")
        print(f"   - Has planets: {has_planets}")
        print(f"   - Has houses: {has_houses}")
        print(f"   - Has migration_info: {has_migration_info}")
        
        if has_planets:
            planets = astro.get('planets', {})
            print(f"   - Number of planets: {len(planets)}")
            
        if has_houses:
            houses = astro.get('houses', {})
            cusps = houses.get('cusps', [])
            ascendant = houses.get('ascendant')
            print(f"   - Number of house cusps: {len(cusps)}")
            print(f"   - Ascendant: {ascendant}")
            
        if has_migration_info:
            migration_reason = migration_info.get('migration_reason')
            migrated_at = migration_info.get('migrated_at')
            print(f"   - Migration reason: {migration_reason}")
            print(f"   - Migrated at: {migrated_at}")
            
        # Verify migration success criteria
        success_criteria = [
            has_planets,
            has_houses,
            len(cusps) == 12 if has_houses else False,
            ascendant and ascendant != "Unknown" if has_houses else False,
            migration_reason == "legacy_string_format" if has_migration_info else False
        ]
        
        all_passed = all(success_criteria)
        
        if all_passed:
            print("✅ Migration verification successful - chart upgraded to full format")
        else:
            print("❌ Migration verification failed - chart not properly upgraded")
            print(f"   Success criteria: {success_criteria}")
            
        return all_passed
        
    async def run_test(self):
        """Run the complete migration test"""
        print("🧪 Starting Astrology Chart Auto-Migration Test")
        print("=" * 60)
        
        try:
            await self.setup_session()
            
            # Step 1: Verify user exists
            if not await self.verify_user_exists():
                return False
                
            # Step 2: Setup old-format chart
            if not await self.setup_old_format_chart():
                return False
                
            # Step 3: Verify old format
            if not await self.verify_old_format():
                return False
                
            # Step 4: Call API to trigger migration
            api_success, api_response = await self.call_astrology_deep_dive()
            
            # Step 5: Verify migration in database
            db_success = await self.verify_migration_occurred()
            
            # Final result
            overall_success = api_success and db_success
            
            print("\n" + "=" * 60)
            if overall_success:
                print("🎉 ASTROLOGY CHART AUTO-MIGRATION TEST PASSED")
                print("✅ Old-format chart successfully migrated to full format")
                print("✅ Migration metadata recorded")
                print("✅ API returns valid data with ascendant")
            else:
                print("❌ ASTROLOGY CHART AUTO-MIGRATION TEST FAILED")
                if not api_success:
                    print("❌ API call failed or returned invalid data")
                if not db_success:
                    print("❌ Database migration verification failed")
                    
            return overall_success
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    tester = AstrologyMigrationTester()
    success = await tester.run_test()
    
    if success:
        print("\n🎯 Test Result: PASS")
        sys.exit(0)
    else:
        print("\n💥 Test Result: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())