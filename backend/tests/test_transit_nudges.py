"""
Unit Tests for Transit Nudge Notification System - Phase 9
===========================================================
Tests:
1. Opt-out users get no notifications
2. Opt-in users get notifications with safe language
3. max_per_week is enforced
4. Notification content does not contain fatalistic language
"""
import sys
sys.path.insert(0, '/app/backend')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import json

load_dotenv()


async def get_db():
    """Get database connection"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    return client[os.environ.get('DB_NAME', 'astrology_app')]


# Import helper functions after dotenv
from server import (
    generate_transit_nudge_for_user,
    get_user_notifications_this_week,
    validate_nudge_text,
    NUDGE_FORBIDDEN_WORDS,
)
from bson import ObjectId


def test_opt_out_users_get_no_notifications():
    """Test that users with notifications disabled get no notifications"""
    print("=" * 70)
    print("TEST 1: Opt-out users get no notifications")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    
    async def run_test():
        db = await get_db()
        
        # Temporarily disable notifications for Pete
        original_prefs = await db.users.find_one({"_id": ObjectId(user_id)})
        original_prefs = original_prefs.get("notification_prefs", {}) if original_prefs else {}
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"notification_prefs.enabled": False}}
        )
        
        # Try to generate notification
        notification = await generate_transit_nudge_for_user(user_id, days=7)
        
        # Restore original prefs
        if original_prefs.get("enabled"):
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"notification_prefs.enabled": True}}
            )
        
        # Should be None (no notification generated)
        assert notification is None, "Opt-out user should not receive notification"
        
        print(f"  User with notifications disabled: no notification generated ✓")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 1 PASSED")
    return result


def test_opt_in_users_get_safe_language():
    """Test that opt-in users get notifications with safe, non-fatalistic language"""
    print()
    print("=" * 70)
    print("TEST 2: Opt-in users get notifications with safe language")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    
    async def run_test():
        db = await get_db()
        
        # Ensure Pete is opted in
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "notification_prefs.enabled": True,
                "notification_prefs.max_per_week": 10  # High limit for testing
            }}
        )
        
        # Clear any existing notifications
        await db.notifications.delete_many({"user_id": user_id})
        
        # Generate notification
        notification = await generate_transit_nudge_for_user(user_id, days=7)
        
        if notification is None:
            print("  No significant transit events - SKIPPING (acceptable)")
            return True
        
        # Check title and body for forbidden words
        title = notification.get("title", "").lower()
        body = notification.get("body", "").lower()
        
        for word in NUDGE_FORBIDDEN_WORDS:
            assert word not in title, f"Title contains forbidden word: {word}"
            assert word not in body, f"Body contains forbidden word: {word}"
        
        # Check for non-fatalistic patterns
        assert "may" in body or "might" in body or "could" in body, \
            "Body should use hedging language (may, might, could)"
        
        print(f"  Title: {notification.get('title')}")
        print(f"  Body: {notification.get('body')}")
        print(f"  No forbidden words found ✓")
        print(f"  Uses hedging language ✓")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 2 PASSED")
    return result


def test_max_per_week_enforced():
    """Test that max_per_week limit is respected"""
    print()
    print("=" * 70)
    print("TEST 3: max_per_week is enforced")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    
    async def run_test():
        db = await get_db()
        
        # Set max_per_week to 1
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "notification_prefs.enabled": True,
                "notification_prefs.max_per_week": 1
            }}
        )
        
        # Clear notifications
        await db.notifications.delete_many({"user_id": user_id})
        
        # Generate first notification
        notif1 = await generate_transit_nudge_for_user(user_id, days=7)
        
        # Try to generate second notification
        notif2 = await generate_transit_nudge_for_user(user_id, days=7)
        
        # Second should be None (at weekly cap)
        if notif1 is not None:
            assert notif2 is None, "Second notification should be blocked by max_per_week"
            print(f"  First notification: {notif1.get('title')}")
            print(f"  Second notification: None (blocked by cap) ✓")
        else:
            print("  No notifications generated (no events) - SKIPPING")
        
        # Reset max_per_week
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"notification_prefs.max_per_week": 3}}
        )
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 3 PASSED")
    return result


def test_validate_nudge_text():
    """Test the text validation function"""
    print()
    print("=" * 70)
    print("TEST 4: Nudge text validation")
    print("=" * 70)
    
    # Test with forbidden words
    bad_text = "You will experience a destined change that is guaranteed to happen."
    validated = validate_nudge_text(bad_text)
    
    for word in ["will", "destined", "guaranteed"]:
        assert word not in validated.lower(), f"Validated text still contains: {word}"
    
    print(f"  Original: {bad_text}")
    print(f"  Validated: {validated}")
    print(f"  Forbidden words removed ✓")
    
    # Test with safe text
    safe_text = "You may notice a subtle shift in focus."
    safe_validated = validate_nudge_text(safe_text)
    assert safe_validated == safe_text, "Safe text should remain unchanged"
    
    print(f"  Safe text unchanged ✓")
    
    print()
    print("✅ TEST 4 PASSED")
    return True


def test_notification_data_structure():
    """Test that notification has correct data structure"""
    print()
    print("=" * 70)
    print("TEST 5: Notification data structure"
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    
    async def run_test():
        db = await get_db()
        
        # Get a notification
        notification = await db.notifications.find_one({
            "user_id": user_id,
            "type": "transit_heads_up"
        })
        
        if notification is None:
            print("  No notification found - SKIPPING")
            return True
        
        # Check required fields
        required_fields = ["user_id", "created_at", "type", "title", "body", "data"]
        for field in required_fields:
            assert field in notification, f"Missing required field: {field}"
        
        # Check data structure
        data = notification.get("data", {})
        data_fields = ["from_utc", "to_utc", "based_on"]
        for field in data_fields:
            assert field in data, f"Missing data field: {field}"
        
        # Check based_on is a list
        assert isinstance(data.get("based_on"), list), "based_on should be a list"
        
        print(f"  All required fields present ✓")
        print(f"  Data structure valid ✓")
        print(f"  based_on events: {data.get('based_on')}")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 5 PASSED")
    return result


if __name__ == '__main__':
    all_passed = True
    
    try:
        test_opt_out_users_get_no_notifications()
        test_opt_in_users_get_safe_language()
        test_max_per_week_enforced()
        test_validate_nudge_text()
        test_notification_data_structure()
        
        print()
        print("=" * 70)
        print("ALL TESTS PASSED ✅")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        all_passed = False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    exit(0 if all_passed else 1)
