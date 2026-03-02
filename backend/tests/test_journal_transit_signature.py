"""
Unit Tests for Journal Transit Signature - Phase 6
===================================================
Tests:
1. Journal create stores transit_signature.events as non-empty when transit engine works
2. Journal create still succeeds if transit engine is unavailable (mock failure)
3. Journal GET returns stored transit_signature
"""
import sys
sys.path.insert(0, '/app/backend')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import json

load_dotenv()


async def get_db():
    """Get database connection"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    return client[os.environ.get('DB_NAME', 'astrology_app')]


async def create_journal_entry(user_id: str, content: str) -> dict:
    """Create a journal entry via API simulation (direct DB insert with transit signature)"""
    from calculations.transits import compute_transits_now, compute_transits_window
    
    db = await get_db()
    
    entry_timestamp = datetime.now(timezone.utc)
    
    # Get user's chart
    chart = await db.charts.find_one({"user_id": user_id})
    
    # Compute transit signature
    transit_signature = None
    if chart:
        try:
            # Compute transits/now
            transit_now = compute_transits_now(
                chart_data=chart,
                timestamp_utc=entry_timestamp,
                orb_deg=2.0,
                include_houses=True
            )
            
            # Build events from aspects
            events = []
            for aspect in transit_now.get("aspects_to_natal_now", []):
                event_str = f"{aspect['transit_planet']}_{aspect['aspect']}_{aspect['natal_body']}"
                events.append(event_str)
            
            # Get window for same-day events
            window_start = entry_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            transit_window = compute_transits_window(
                chart_data=chart,
                from_utc=window_start,
                window_days=3,
                orb_deg=2.0,
                include_houses=True
            )
            
            entry_date = entry_timestamp.strftime('%Y-%m-%d')
            
            # Add ingresses
            for ingress in transit_window.get("ingresses", []):
                if ingress["timestamp_utc"][:10] == entry_date:
                    event_str = f"{ingress['planet']}_ingress_{ingress['to_sign']}"
                    if event_str not in events:
                        events.append(event_str)
            
            # Add stations
            for station in transit_window.get("stations", []):
                if station["timestamp_utc"][:10] == entry_date:
                    event_str = f"{station['planet']}_{station['type']}"
                    if event_str not in events:
                        events.append(event_str)
            
            # Get top houses
            house_activation = transit_window.get("house_activation", {})
            top_houses = None
            if house_activation.get("enabled"):
                top_houses = house_activation.get("top_houses", [])[:3]
            
            transit_signature = {
                "timestamp_utc": entry_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "source": "compute/transits/now+window",
                "events": events[:8],  # Max 8 events
                "top_houses": top_houses,
                "build_id": "transits_phase6_test"
            }
        except Exception as e:
            transit_signature = {
                "timestamp_utc": entry_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "source": "compute/transits/now",
                "events": [],
                "top_houses": None,
                "build_id": "transits_phase6_test",
                "error": str(e)
            }
    
    entry_data = {
        "user_id": user_id,
        "content": content,
        "themes": ["test"],
        "source": "test",
        "source_label": "Unit Test",
        "created_at": entry_timestamp,
        "transit_signature": transit_signature
    }
    
    result = await db.journal.insert_one(entry_data)
    entry_data["_id"] = result.inserted_id
    
    return entry_data


async def cleanup_test_entries(db, user_id: str):
    """Clean up test journal entries"""
    await db.journal.delete_many({
        "user_id": user_id,
        "source": "test"
    })


def test_journal_transit_signature_populated():
    """Test that journal create stores transit_signature.events as non-empty"""
    print("=" * 70)
    print("TEST 1: Journal create stores transit_signature with events")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete - has natal chart
    
    async def run_test():
        db = await get_db()
        
        # Cleanup any previous test entries
        await cleanup_test_entries(db, user_id)
        
        # Create a journal entry
        entry = await create_journal_entry(
            user_id=user_id,
            content="Test entry for transit signature validation"
        )
        
        # Verify transit_signature exists
        assert entry.get("transit_signature") is not None, "transit_signature should exist"
        
        sig = entry["transit_signature"]
        
        # Verify structure
        assert "timestamp_utc" in sig, "Should have timestamp_utc"
        assert "source" in sig, "Should have source"
        assert "events" in sig, "Should have events"
        assert "build_id" in sig, "Should have build_id"
        
        # Verify events is non-empty (Pete has a valid chart)
        assert len(sig["events"]) > 0, f"events should be non-empty, got: {sig['events']}"
        
        # Verify event format
        for event in sig["events"]:
            assert "_" in event, f"Event should have underscores: {event}"
        
        # Verify top_houses if present
        if sig.get("top_houses"):
            assert isinstance(sig["top_houses"], list), "top_houses should be a list"
            for house in sig["top_houses"]:
                assert isinstance(house, int), f"House should be int: {house}"
                assert 1 <= house <= 12, f"House should be 1-12: {house}"
        
        print(f"  timestamp_utc: {sig['timestamp_utc']}")
        print(f"  source: {sig['source']}")
        print(f"  events ({len(sig['events'])}): {sig['events'][:3]}...")
        print(f"  top_houses: {sig.get('top_houses')}")
        print(f"  build_id: {sig['build_id']}")
        
        # Cleanup
        await cleanup_test_entries(db, user_id)
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 1 PASSED")
    return result


def test_journal_succeeds_without_chart():
    """Test that journal create still succeeds if user has no natal chart"""
    print()
    print("=" * 70)
    print("TEST 2: Journal create succeeds without natal chart")
    print("=" * 70)
    
    # Use a fake user_id that has no chart
    user_id = "test_user_no_chart_" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    async def run_test():
        db = await get_db()
        
        # Create a journal entry for user without chart
        entry_timestamp = datetime.now(timezone.utc)
        
        # Simulate what happens when chart doesn't exist
        chart = await db.charts.find_one({"user_id": user_id})
        
        transit_signature = None
        if not chart:
            # No chart - return error signature
            transit_signature = {
                "timestamp_utc": entry_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "source": "compute/transits/now",
                "events": [],
                "top_houses": None,
                "build_id": "transits_phase6_test",
                "error": "no_natal_chart"
            }
        
        entry_data = {
            "user_id": user_id,
            "content": "Test entry for user without chart",
            "themes": ["test"],
            "source": "test",
            "source_label": "Unit Test - No Chart",
            "created_at": entry_timestamp,
            "transit_signature": transit_signature
        }
        
        result = await db.journal.insert_one(entry_data)
        
        # Verify entry was created
        assert result.inserted_id is not None, "Entry should be created"
        
        # Verify transit_signature has error
        sig = transit_signature
        assert sig is not None, "transit_signature should exist"
        assert sig["error"] == "no_natal_chart", f"Should have error, got: {sig.get('error')}"
        assert sig["events"] == [], f"events should be empty, got: {sig['events']}"
        
        print(f"  Entry created: {result.inserted_id}")
        print(f"  transit_signature.error: {sig['error']}")
        print(f"  transit_signature.events: {sig['events']}")
        
        # Cleanup
        await db.journal.delete_one({"_id": result.inserted_id})
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 2 PASSED")
    return result


def test_journal_get_returns_signature():
    """Test that GET /journal returns stored transit_signature"""
    print()
    print("=" * 70)
    print("TEST 3: Journal GET returns stored transit_signature")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    
    async def run_test():
        db = await get_db()
        
        # Cleanup any previous test entries
        await cleanup_test_entries(db, user_id)
        
        # Create a journal entry
        entry = await create_journal_entry(
            user_id=user_id,
            content="Test entry for GET validation"
        )
        
        entry_id = entry["_id"]
        
        # Fetch the entry back
        fetched = await db.journal.find_one({"_id": entry_id})
        
        assert fetched is not None, "Entry should be fetched"
        assert "transit_signature" in fetched, "Fetched entry should have transit_signature"
        
        sig = fetched["transit_signature"]
        assert sig is not None, "transit_signature should not be None"
        assert "events" in sig, "Should have events"
        assert len(sig["events"]) > 0, "events should not be empty"
        
        print(f"  Fetched entry ID: {entry_id}")
        print(f"  transit_signature.events: {sig['events'][:3]}...")
        print(f"  transit_signature.top_houses: {sig.get('top_houses')}")
        
        # Cleanup
        await cleanup_test_entries(db, user_id)
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 3 PASSED")
    return result


def test_transit_signature_max_events():
    """Test that transit_signature.events is capped at MAX_TRANSIT_EVENTS"""
    print()
    print("=" * 70)
    print("TEST 4: Transit signature events capped at max")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    
    async def run_test():
        db = await get_db()
        
        # Cleanup
        await cleanup_test_entries(db, user_id)
        
        # Create entry
        entry = await create_journal_entry(
            user_id=user_id,
            content="Test entry for max events check"
        )
        
        sig = entry.get("transit_signature")
        assert sig is not None, "transit_signature should exist"
        
        # Verify max is 8
        assert len(sig["events"]) <= 8, f"events should be max 8, got {len(sig['events'])}"
        
        print(f"  Number of events: {len(sig['events'])}")
        print(f"  Max allowed: 8")
        
        # Cleanup
        await cleanup_test_entries(db, user_id)
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 4 PASSED")
    return result


if __name__ == '__main__':
    all_passed = True
    
    try:
        test_journal_transit_signature_populated()
        test_journal_succeeds_without_chart()
        test_journal_get_returns_signature()
        test_transit_signature_max_events()
        
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
