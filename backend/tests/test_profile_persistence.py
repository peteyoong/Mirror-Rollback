"""
Comprehensive Profile Persistence Test
=======================================

Tests:
1. write_ok=true after POST
2. readback_match=true (read-after-write verification)
3. GET profile matches the written value
4. Persists across simulated restart/reconnect
5. User isolation (User A vs User B - different names stay separate)
6. updated_at changes on each write

Run: cd /app/backend && python tests/test_profile_persistence.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient

# Environment
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Test results tracking
test_results = {
    "write_ok": False,
    "readback_match": False,
    "get_profile_matches": False,
    "persists_across_restart": False,
    "user_isolation": False,
    "updated_at_changes": False
}


async def get_fresh_db():
    """Get a fresh database connection (simulates reconnect)."""
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


async def run_comprehensive_test():
    """Run all persistence tests with detailed output."""
    
    print("\n" + "=" * 70)
    print("🧪 COMPREHENSIVE PROFILE PERSISTENCE TEST")
    print("=" * 70)
    print(f"MONGO_URL: {MONGO_URL[:30]}..." if MONGO_URL else "MONGO_URL: NOT SET")
    print(f"DB_NAME: {DB_NAME}")
    print("=" * 70)
    
    # Import the module under test
    from profile_persistence import get_user_profile, update_numerology_name
    
    db = await get_fresh_db()
    
    # Find or create two test users
    user_a = await db.users.find_one({})
    if not user_a:
        print("❌ FAILED: No users in database to test")
        return False
    
    # Find a second user for isolation test
    user_b = await db.users.find_one({"_id": {"$ne": user_a["_id"]}})
    
    user_a_id = str(user_a["_id"])
    user_b_id = str(user_b["_id"]) if user_b else None
    
    print(f"\nUser A ID: {user_a_id}")
    print(f"User B ID: {user_b_id or 'NOT FOUND (will create)'}")
    
    # Create User B if needed for isolation test
    if not user_b_id:
        insert_result = await db.users.insert_one({
            "name": "Test User B",
            "email": f"testuser_b_{datetime.now().timestamp()}@test.com",
            "created_at": datetime.now(timezone.utc)
        })
        user_b_id = str(insert_result.inserted_id)
        print(f"Created User B: {user_b_id}")
    
    # Generate unique test names
    timestamp = int(datetime.now().timestamp())
    test_name_a = f"Alice Test Name {timestamp}"
    test_name_b = f"Bob Test Name {timestamp}"
    
    # =========================================================================
    # TEST 1: write_ok=true after POST
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 1: write_ok=true")
    print("-" * 70)
    
    # Store original updated_at for later comparison
    original_user_a = await db.users.find_one({"_id": ObjectId(user_a_id)})
    original_updated_at = original_user_a.get("updated_at")
    
    # Perform update
    os.environ['DEBUG_MIRROR'] = 'true'  # Enable debug output
    
    # Reimport to pick up DEBUG_MIRROR
    import importlib
    import profile_persistence
    importlib.reload(profile_persistence)
    from profile_persistence import get_user_profile, update_numerology_name
    
    result_a = await update_numerology_name(user_a_id, test_name_a)
    
    write_ok = result_a.get("success", False)
    debug_write_ok = result_a.get("debug", {}).get("write_ok", False)
    
    print(f"   result.success = {write_ok}")
    print(f"   result.debug.write_ok = {debug_write_ok}")
    
    if write_ok:
        print("   ✅ write_ok=true PASSED")
        test_results["write_ok"] = True
    else:
        print(f"   ❌ write_ok=true FAILED: {result_a}")
        return False
    
    # =========================================================================
    # TEST 2: readback_match=true
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 2: readback_match=true")
    print("-" * 70)
    
    readback_match = result_a.get("debug", {}).get("readback_match", False)
    stored_name = result_a.get("numerology_full_name")
    
    print(f"   Expected name: '{test_name_a}'")
    print(f"   Stored name:   '{stored_name}'")
    print(f"   result.debug.readback_match = {readback_match}")
    
    if readback_match and stored_name == test_name_a:
        print("   ✅ readback_match=true PASSED")
        test_results["readback_match"] = True
    else:
        print(f"   ❌ readback_match=true FAILED")
        return False
    
    # =========================================================================
    # TEST 3: GET profile matches
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 3: GET profile matches")
    print("-" * 70)
    
    profile_a = await get_user_profile(user_a_id)
    get_name = profile_a.get("numerology_full_name")
    
    print(f"   Expected: '{test_name_a}'")
    print(f"   GET returned: '{get_name}'")
    
    if get_name == test_name_a:
        print("   ✅ GET profile matches PASSED")
        test_results["get_profile_matches"] = True
    else:
        print(f"   ❌ GET profile matches FAILED")
        return False
    
    # =========================================================================
    # TEST 4: Persists across simulated restart/reconnect
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 4: Persists across simulated restart/reconnect")
    print("-" * 70)
    
    print("   Closing all connections...")
    
    # Force module reload to simulate restart
    importlib.reload(profile_persistence)
    from profile_persistence import get_user_profile, update_numerology_name
    
    # Create completely fresh DB connection
    fresh_db = await get_fresh_db()
    
    print("   Reconnecting to database...")
    
    # Read directly from fresh connection to verify persistence
    user_after_restart = await fresh_db.users.find_one({"_id": ObjectId(user_a_id)})
    name_after_restart = user_after_restart.get("numerology_full_name") if user_after_restart else None
    
    print(f"   Expected: '{test_name_a}'")
    print(f"   After restart: '{name_after_restart}'")
    
    # Also test via the module
    profile_after_restart = await get_user_profile(user_a_id)
    module_name = profile_after_restart.get("numerology_full_name")
    
    print(f"   Via module: '{module_name}'")
    
    if name_after_restart == test_name_a and module_name == test_name_a:
        print("   ✅ Persists across restart PASSED")
        test_results["persists_across_restart"] = True
    else:
        print(f"   ❌ Persists across restart FAILED")
        return False
    
    # =========================================================================
    # TEST 5: User isolation (A vs B)
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 5: User isolation (A vs B)")
    print("-" * 70)
    
    # Update User B with a different name
    result_b = await update_numerology_name(user_b_id, test_name_b)
    
    print(f"   User A name: '{test_name_a}'")
    print(f"   User B name: '{test_name_b}'")
    
    if not result_b.get("success"):
        print(f"   ❌ Failed to update User B: {result_b}")
        return False
    
    # Now read both profiles
    profile_a_check = await get_user_profile(user_a_id)
    profile_b_check = await get_user_profile(user_b_id)
    
    name_a_check = profile_a_check.get("numerology_full_name")
    name_b_check = profile_b_check.get("numerology_full_name")
    
    print(f"   User A GET: '{name_a_check}'")
    print(f"   User B GET: '{name_b_check}'")
    
    # Verify isolation: A should still have A's name, B should have B's name
    isolation_ok = (name_a_check == test_name_a) and (name_b_check == test_name_b)
    
    if isolation_ok:
        print("   ✅ User isolation PASSED")
        test_results["user_isolation"] = True
    else:
        print(f"   ❌ User isolation FAILED - names got mixed up!")
        return False
    
    # =========================================================================
    # TEST 6: updated_at changes
    # =========================================================================
    print("\n" + "-" * 70)
    print("TEST 6: updated_at changes")
    print("-" * 70)
    
    # Get current updated_at
    user_a_current = await fresh_db.users.find_one({"_id": ObjectId(user_a_id)})
    current_updated_at = user_a_current.get("updated_at")
    
    print(f"   Original updated_at: {original_updated_at}")
    print(f"   Current updated_at:  {current_updated_at}")
    
    # Wait a bit and update again
    await asyncio.sleep(0.1)
    new_name_a = f"Alice Updated {int(datetime.now().timestamp())}"
    await update_numerology_name(user_a_id, new_name_a)
    
    # Check updated_at changed
    user_a_after_update = await fresh_db.users.find_one({"_id": ObjectId(user_a_id)})
    new_updated_at = user_a_after_update.get("updated_at")
    
    print(f"   After 2nd update:    {new_updated_at}")
    
    # Verify updated_at changed
    updated_at_changed = (new_updated_at is not None) and (new_updated_at != current_updated_at)
    
    if updated_at_changed:
        print("   ✅ updated_at changes PASSED")
        test_results["updated_at_changes"] = True
    else:
        print(f"   ❌ updated_at changes FAILED")
        return False
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)
