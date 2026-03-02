"""
Unit Tests for Timeline Context - Phase 8
==========================================
Tests:
1. Context is present when feature enabled
2. Caps are enforced on events and journal entries
3. No journal raw content is included
4. Chat still works if transit endpoints fail (graceful fallback)
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


# Import after dotenv to ensure env vars are loaded
from server import (
    get_timeline_context,
    format_timeline_context_for_prompt,
    MAX_NOW_EVENTS,
    MAX_RECENT_JOURNAL_ENTRIES,
    MAX_EVENTS_PER_JOURNAL,
    ENABLE_TIMELINE_CONTEXT,
)


def test_context_present_when_enabled():
    """Test that timeline context is populated when feature is enabled"""
    print("=" * 70)
    print("TEST 1: Context is present when feature is enabled")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    now_utc = datetime.now(timezone.utc)
    
    async def run_test():
        context = await get_timeline_context(user_id, now_utc)
        
        # Verify structure
        assert "now_utc" in context, "Should have now_utc"
        assert "now_events" in context, "Should have now_events"
        assert "next_3d_events" in context, "Should have next_3d_events"
        assert "recent_journal_signatures" in context, "Should have recent_journal_signatures"
        assert "enabled" in context, "Should have enabled flag"
        
        # Verify enabled
        if ENABLE_TIMELINE_CONTEXT:
            assert context["enabled"] == True, "Should be enabled"
            
            # Verify events are populated (Pete has a chart)
            assert len(context["now_events"]) > 0, "now_events should be populated"
            print(f"  now_events: {len(context['now_events'])} events")
            print(f"  next_3d_events: {len(context['next_3d_events'])} events")
            print(f"  recent_journal_signatures: {len(context['recent_journal_signatures'])} entries")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 1 PASSED")
    return result


def test_caps_enforced():
    """Test that event caps are enforced"""
    print()
    print("=" * 70)
    print("TEST 2: Caps are enforced")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    now_utc = datetime.now(timezone.utc)
    
    async def run_test():
        context = await get_timeline_context(user_id, now_utc)
        
        # Verify now_events cap
        assert len(context["now_events"]) <= MAX_NOW_EVENTS, \
            f"now_events should be <= {MAX_NOW_EVENTS}, got {len(context['now_events'])}"
        
        # Verify next_3d_events cap
        assert len(context["next_3d_events"]) <= MAX_NOW_EVENTS, \
            f"next_3d_events should be <= {MAX_NOW_EVENTS}, got {len(context['next_3d_events'])}"
        
        # Verify journal signatures cap
        assert len(context["recent_journal_signatures"]) <= MAX_RECENT_JOURNAL_ENTRIES, \
            f"journal signatures should be <= {MAX_RECENT_JOURNAL_ENTRIES}"
        
        # Verify events per journal cap
        for sig in context["recent_journal_signatures"]:
            assert len(sig.get("events", [])) <= MAX_EVENTS_PER_JOURNAL, \
                f"events per journal should be <= {MAX_EVENTS_PER_JOURNAL}"
        
        print(f"  MAX_NOW_EVENTS: {MAX_NOW_EVENTS}")
        print(f"  MAX_RECENT_JOURNAL_ENTRIES: {MAX_RECENT_JOURNAL_ENTRIES}")
        print(f"  MAX_EVENTS_PER_JOURNAL: {MAX_EVENTS_PER_JOURNAL}")
        print(f"  Actual now_events: {len(context['now_events'])}")
        print(f"  Actual journal_signatures: {len(context['recent_journal_signatures'])}")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 2 PASSED")
    return result


def test_no_journal_raw_content():
    """Test that no journal raw text is included in context"""
    print()
    print("=" * 70)
    print("TEST 3: No journal raw content included")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    now_utc = datetime.now(timezone.utc)
    
    async def run_test():
        db = await get_db()
        
        # Get context
        context = await get_timeline_context(user_id, now_utc)
        
        # Get actual journal entries to compare
        actual_entries = await db.journal.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        # Check that no journal content is in context
        context_str = json.dumps(context)
        
        for entry in actual_entries:
            content = entry.get("content", "")
            if len(content) > 50:  # Only check meaningful content
                # Content should NOT be in context (first 50 chars at least)
                assert content[:50] not in context_str, \
                    f"Journal content should not be in context: {content[:30]}..."
        
        # Verify journal signatures only have date and events
        for sig in context.get("recent_journal_signatures", []):
            assert "date" in sig, "Should have date"
            assert "events" in sig, "Should have events"
            assert "content" not in sig, "Should NOT have content"
            assert "text" not in sig, "Should NOT have text"
        
        print(f"  Verified {len(actual_entries)} journal entries not in context")
        print(f"  Journal signatures contain only: date, events")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 3 PASSED")
    return result


def test_graceful_fallback():
    """Test that context has graceful fallback on errors"""
    print()
    print("=" * 70)
    print("TEST 4: Graceful fallback for missing user/chart")
    print("=" * 70)
    
    # Use a fake user_id that doesn't exist
    user_id = "nonexistent_user_12345"
    now_utc = datetime.now(timezone.utc)
    
    async def run_test():
        # This should not throw, just return empty/error context
        context = await get_timeline_context(user_id, now_utc)
        
        # Should have the base structure
        assert "now_utc" in context, "Should have now_utc even on error"
        assert "now_events" in context, "Should have now_events"
        assert "enabled" in context, "Should have enabled"
        
        # Should have error indicator
        if ENABLE_TIMELINE_CONTEXT:
            assert context.get("error") is not None, "Should have error for missing user"
            print(f"  Error: {context.get('error')}")
        
        # now_events should be empty
        assert context["now_events"] == [], "now_events should be empty on error"
        
        print(f"  Context gracefully handled missing user")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 4 PASSED")
    return result


def test_formatted_prompt():
    """Test that formatted prompt is readable and safe"""
    print()
    print("=" * 70)
    print("TEST 5: Formatted prompt is readable")
    print("=" * 70)
    
    user_id = "6971c81f2b40fd5ef501d375"  # Pete
    now_utc = datetime.now(timezone.utc)
    
    async def run_test():
        context = await get_timeline_context(user_id, now_utc)
        formatted = format_timeline_context_for_prompt(context)
        
        if ENABLE_TIMELINE_CONTEXT and not context.get("error"):
            # Should have content
            assert len(formatted) > 0, "Formatted prompt should not be empty"
            
            # Should have the header
            assert "TIMELINE CONTEXT" in formatted, "Should have header"
            
            # Should have safety note
            assert "Do not make predictions" in formatted, "Should have safety note"
            
            # Should NOT have underscores (events should be readable)
            if context.get("now_events"):
                # Check that at least one event is formatted
                sample_event = context["now_events"][0]
                readable = sample_event.replace("_", " ")
                assert readable in formatted, f"Event should be readable: {readable}"
            
            print(f"  Formatted prompt length: {len(formatted)} chars")
            print(f"  Contains safety note: Yes")
            print(f"  Sample formatted output:")
            for line in formatted.split('\n')[:8]:
                print(f"    {line}")
        
        return True
    
    result = asyncio.run(run_test())
    
    print()
    print("✅ TEST 5 PASSED")
    return result


if __name__ == '__main__':
    all_passed = True
    
    try:
        test_context_present_when_enabled()
        test_caps_enforced()
        test_no_journal_raw_content()
        test_graceful_fallback()
        test_formatted_prompt()
        
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
