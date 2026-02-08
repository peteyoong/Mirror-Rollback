"""
Profile Persistence Layer
=========================

Canonical persistence for user profile data including numerology_full_name.
Ensures data is written to persistent DB, not just cache.

Usage:
    from profile_persistence import get_user_profile, update_numerology_name
    
    profile = await get_user_profile(user_id)
    result = await update_numerology_name(user_id, "John Smith")
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Environment
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
DEBUG_MIRROR = os.environ.get('DEBUG_MIRROR', 'false').lower() == 'true'


async def get_db():
    """Get database connection."""
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user profile from persistent DB.
    
    Returns:
        {
            "user_id": str,
            "preferred_name": str | None,
            "numerology_full_name": str | None,
            "updated_at": str | None,
            "debug": {...} if DEBUG_MIRROR
        }
    """
    db = await get_db()
    
    try:
        # Parse user_id as ObjectId if possible
        try:
            user_oid = ObjectId(user_id)
        except:
            user_oid = user_id
        
        user = await db.users.find_one({"_id": user_oid})
        
        if not user:
            logger.warning(f"[PROFILE] User not found: {user_id}")
            return {
                "user_id": user_id,
                "preferred_name": None,
                "numerology_full_name": None,
                "updated_at": None,
                "exists": False
            }
        
        result = {
            "user_id": str(user.get("_id")),
            "preferred_name": user.get("name") or user.get("preferred_name"),
            "numerology_full_name": user.get("numerology_full_name"),
            "updated_at": user.get("updated_at").isoformat() if user.get("updated_at") else None,
            "exists": True
        }
        
        if DEBUG_MIRROR:
            result["debug"] = {
                "db_row_id": str(user.get("_id")),
                "has_numerology_name": bool(user.get("numerology_full_name")),
                "name_length": len(user.get("numerology_full_name", "")) if user.get("numerology_full_name") else 0
            }
            logger.info(f"[PROFILE] GET user={user_id} numerology_name={bool(user.get('numerology_full_name'))}")
        
        return result
        
    except Exception as e:
        logger.error(f"[PROFILE] Error getting profile: {e}")
        raise


async def update_numerology_name(
    user_id: str, 
    full_name: str
) -> Dict[str, Any]:
    """
    Update numerology_full_name in persistent DB with read-after-write verification.
    
    Args:
        user_id: User ID
        full_name: Full birth name to store
        
    Returns:
        {
            "success": bool,
            "numerology_full_name": str,
            "computed_numbers": {...},
            "debug": {...} if DEBUG_MIRROR
        }
    """
    db = await get_db()
    
    try:
        # Validate input
        if not full_name or not full_name.strip():
            return {
                "success": False,
                "error": "Full name cannot be empty",
                "numerology_full_name": None
            }
        
        clean_name = full_name.strip()
        
        # Parse user_id as ObjectId if possible
        try:
            user_oid = ObjectId(user_id)
        except:
            user_oid = user_id
        
        # Update with timestamp
        update_result = await db.users.update_one(
            {"_id": user_oid},
            {
                "$set": {
                    "numerology_full_name": clean_name,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        write_ok = update_result.modified_count > 0 or update_result.matched_count > 0
        
        if not write_ok:
            logger.error(f"[PROFILE] Write failed for user {user_id}")
            return {
                "success": False,
                "error": "Failed to update user",
                "numerology_full_name": None
            }
        
        # Read-after-write verification
        user = await db.users.find_one({"_id": user_oid})
        stored_name = user.get("numerology_full_name") if user else None
        readback_match = stored_name == clean_name
        
        if not readback_match:
            logger.error(f"[PROFILE] Read-after-write mismatch! Expected '{clean_name}', got '{stored_name}'")
        
        # Compute name-based numbers
        from numerology_compute import calculate_numerology_name_numbers
        computed_numbers = calculate_numerology_name_numbers(clean_name)
        
        result = {
            "success": True,
            "numerology_full_name": stored_name,
            "computed_numbers": computed_numbers
        }
        
        if DEBUG_MIRROR:
            result["debug"] = {
                "write_ok": write_ok,
                "db_row_id": str(user.get("_id")) if user else None,
                "readback_match": readback_match,
                "modified_count": update_result.modified_count,
                "matched_count": update_result.matched_count
            }
            logger.info(f"[PROFILE] UPDATE user={user_id} write_ok={write_ok} readback_match={readback_match}")
        
        # Clear any cached numerology deep dives for this user
        await db.deep_dive_cache.delete_many({
            "user_id": user_id,
            "lens": "numerology"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"[PROFILE] Error updating numerology name: {e}")
        raise


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

async def test_numerology_name_persistence():
    """
    Integration test for numerology name persistence.
    
    Tests:
    1. POST numerology name
    2. GET profile → must match
    3. Simulate cold start (clear local state)
    4. GET profile again → must still match
    """
    import asyncio
    
    # Find a test user
    db = await get_db()
    user = await db.users.find_one({})
    
    if not user:
        print("❌ No test user found")
        return False
    
    user_id = str(user["_id"])
    test_name = f"Test Name {datetime.now().timestamp()}"
    
    print(f"\n{'='*60}")
    print("🧪 NUMEROLOGY NAME PERSISTENCE TEST")
    print(f"{'='*60}")
    print(f"User ID: {user_id}")
    print(f"Test Name: {test_name}")
    
    # Test 1: POST numerology name
    print("\n1. POST numerology name...")
    update_result = await update_numerology_name(user_id, test_name)
    assert update_result["success"], f"Update failed: {update_result}"
    assert update_result["numerology_full_name"] == test_name
    print(f"   ✅ Write successful, readback_match={update_result.get('debug', {}).get('readback_match')}")
    
    # Test 2: GET profile → must match
    print("\n2. GET profile...")
    profile = await get_user_profile(user_id)
    assert profile["numerology_full_name"] == test_name, f"Expected '{test_name}', got '{profile['numerology_full_name']}'"
    print(f"   ✅ Profile read matches: {profile['numerology_full_name']}")
    
    # Test 3: Simulate cold start by creating new DB connection
    print("\n3. Simulating cold start (new connection)...")
    # Force new connection
    global _cached_db
    _cached_db = None
    
    # Test 4: GET profile again
    print("\n4. GET profile after cold start...")
    profile2 = await get_user_profile(user_id)
    assert profile2["numerology_full_name"] == test_name, f"Cold start failed: Expected '{test_name}', got '{profile2['numerology_full_name']}'"
    print(f"   ✅ Profile still matches after cold start: {profile2['numerology_full_name']}")
    
    print(f"\n{'='*60}")
    print("✅ ALL PERSISTENCE TESTS PASSED")
    print(f"{'='*60}\n")
    
    return True


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_numerology_name_persistence())
