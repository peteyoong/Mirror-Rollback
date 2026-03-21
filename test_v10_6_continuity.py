#!/usr/bin/env python3
"""
V10.6 Continuity System Test
=============================
Tests the short-term memory and continuity features.

Validates:
1. Continuity detection works for same pattern
2. Continuity detection works for related patterns
3. Continuity detection works for signal continuity
4. Continuity phrases are applied correctly
5. No continuity when patterns/signals are unrelated
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    detect_continuity,
    generate_continuity_phrase,
    apply_continuity_to_why_now,
    RELATED_PATTERNS,
    RELATED_FRAMES,
    CONTINUITY_PHRASES,
)

def test_same_pattern_continuity():
    """Test continuity detection when same pattern appears."""
    print("\n" + "="*60)
    print("TEST 1: Same Pattern Continuity")
    print("="*60)
    
    recent_history = {
        "recent_patterns": ["threshold_standing", "heart_thaw"],
        "last_frame_type": "edge_of_action",
        "last_tones": {"warmth": 0.5, "hesitation": 0.3},
        "history_count": 2
    }
    
    result = detect_continuity(
        current_pattern_id="threshold_standing",  # Same as recent
        current_frame_type="testing_the_waters",
        current_tones={"warmth": 0.6, "hesitation": 0.4},
        recent_history=recent_history
    )
    
    print(f"Current pattern: threshold_standing")
    print(f"Recent patterns: {recent_history['recent_patterns']}")
    print(f"Result: {result}")
    
    assert result["has_continuity"] == True
    assert result["continuity_type"] == "same_pattern"
    assert result["strength"] >= 0.8
    print("✅ PASSED: Same pattern continuity detected")
    
    # Test phrase generation
    phrase = generate_continuity_phrase(result, "test_user")
    print(f"Generated phrase: '{phrase}'")
    assert phrase in CONTINUITY_PHRASES["same_pattern"]
    print("✅ PASSED: Continuity phrase generated")


def test_related_pattern_continuity():
    """Test continuity detection when related pattern appears."""
    print("\n" + "="*60)
    print("TEST 2: Related Pattern Continuity")
    print("="*60)
    
    recent_history = {
        "recent_patterns": ["relational_reopening"],
        "last_frame_type": "testing_the_waters",
        "last_tones": {"warmth": 0.4},
        "history_count": 1
    }
    
    # heart_thaw is related to relational_reopening
    result = detect_continuity(
        current_pattern_id="heart_thaw",  # Related to relational_reopening
        current_frame_type="something_surfacing",
        current_tones={"warmth": 0.5},
        recent_history=recent_history
    )
    
    print(f"Current pattern: heart_thaw")
    print(f"Recent patterns: {recent_history['recent_patterns']}")
    print(f"Related patterns for heart_thaw: {RELATED_PATTERNS.get('heart_thaw', [])}")
    print(f"Result: {result}")
    
    assert result["has_continuity"] == True
    assert result["continuity_type"] == "related_pattern"
    print("✅ PASSED: Related pattern continuity detected")


def test_same_frame_continuity():
    """Test continuity detection when same frame type continues."""
    print("\n" + "="*60)
    print("TEST 3: Same Frame Continuity")
    print("="*60)
    
    recent_history = {
        "recent_patterns": ["expansion_resistance"],  # Different pattern
        "last_frame_type": "edge_of_action",
        "last_tones": {"growth": 0.5},
        "history_count": 1
    }
    
    result = detect_continuity(
        current_pattern_id="moving_through",  # Different, unrelated pattern
        current_frame_type="edge_of_action",  # Same frame
        current_tones={"growth": 0.4},
        recent_history=recent_history
    )
    
    print(f"Current frame: edge_of_action")
    print(f"Last frame: {recent_history['last_frame_type']}")
    print(f"Result: {result}")
    
    assert result["has_continuity"] == True
    assert result["continuity_type"] == "same_frame"
    print("✅ PASSED: Same frame continuity detected")


def test_signal_continuity():
    """Test continuity detection when strong signal persists."""
    print("\n" + "="*60)
    print("TEST 4: Signal Continuity")
    print("="*60)
    
    recent_history = {
        "recent_patterns": ["over_functioning_hero"],  # Unrelated
        "last_frame_type": "here_again",  # Unrelated to grief_underneath
        "last_tones": {"grief": 0.5, "warmth": 0.2},  # Strong grief
        "history_count": 1
    }
    
    result = detect_continuity(
        current_pattern_id="emotional_wave_riding",  # Unrelated
        current_frame_type="grief_underneath",  # Unrelated to here_again
        current_tones={"grief": 0.6, "confusion": 0.3},  # Grief persists
        recent_history=recent_history
    )
    
    print(f"Current tones: grief=0.6")
    print(f"Last tones: grief=0.5")
    print(f"Result: {result}")
    
    assert result["has_continuity"] == True
    assert result["continuity_type"] == "signal_continuity"
    print("✅ PASSED: Signal continuity detected")


def test_no_continuity():
    """Test that no continuity is detected when nothing matches."""
    print("\n" + "="*60)
    print("TEST 5: No Continuity")
    print("="*60)
    
    recent_history = {
        "recent_patterns": ["over_functioning_hero"],
        "last_frame_type": "clarity_arriving",
        "last_tones": {"pressure": 0.5},
        "history_count": 1
    }
    
    result = detect_continuity(
        current_pattern_id="relational_reopening",  # Unrelated
        current_frame_type="grief_underneath",  # Unrelated
        current_tones={"warmth": 0.6},  # Different tone
        recent_history=recent_history
    )
    
    print(f"Current pattern: relational_reopening (unrelated)")
    print(f"Current frame: grief_underneath (unrelated)")
    print(f"Current tones: warmth (different)")
    print(f"Result: {result}")
    
    assert result["has_continuity"] == False
    print("✅ PASSED: No continuity correctly detected")


def test_continuity_phrase_application():
    """Test that continuity phrases are applied correctly to why_now text."""
    print("\n" + "="*60)
    print("TEST 6: Phrase Application")
    print("="*60)
    
    why_now = "Walls that have been up are starting to soften—not all at once, but noticeably."
    continuity_phrase = "This has been present for a few days now."
    
    result = apply_continuity_to_why_now(why_now, continuity_phrase)
    
    print(f"Original: '{why_now}'")
    print(f"With continuity: '{result}'")
    
    assert result.startswith(continuity_phrase)
    assert why_now in result
    print("✅ PASSED: Continuity phrase prepended correctly")
    
    # Test that it doesn't duplicate if similar words exist
    why_now_with_recent = "Things have been continuing to shift recently."
    result2 = apply_continuity_to_why_now(why_now_with_recent, continuity_phrase)
    
    print(f"\nOriginal (with 'continuing'): '{why_now_with_recent}'")
    print(f"Result (should not duplicate): '{result2}'")
    
    assert result2 == why_now_with_recent  # Should not modify
    print("✅ PASSED: No duplicate continuity language added")


def test_empty_history():
    """Test handling of empty history."""
    print("\n" + "="*60)
    print("TEST 7: Empty History")
    print("="*60)
    
    result = detect_continuity(
        current_pattern_id="heart_thaw",
        current_frame_type="testing_the_waters",
        current_tones={"warmth": 0.5},
        recent_history={}
    )
    
    print(f"Result with empty history: {result}")
    assert result["has_continuity"] == False
    print("✅ PASSED: Empty history handled correctly")
    
    result2 = detect_continuity(
        current_pattern_id="heart_thaw",
        current_frame_type="testing_the_waters",
        current_tones={"warmth": 0.5},
        recent_history=None
    )
    
    print(f"Result with None history: {result2}")
    assert result2["has_continuity"] == False
    print("✅ PASSED: None history handled correctly")


def run_all_tests():
    """Run all V10.6 continuity tests."""
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " V10.6 CONTINUITY SYSTEM TEST ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_same_pattern_continuity,
        test_related_pattern_continuity,
        test_same_frame_continuity,
        test_signal_continuity,
        test_no_continuity,
        test_continuity_phrase_application,
        test_empty_history,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test.__name__}")
            print(f"   Exception: {e}")
            failed += 1
    
    print()
    print("="*60)
    print(f"RESULTS: {passed}/{passed+failed} tests passed")
    if failed == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {failed} tests failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
