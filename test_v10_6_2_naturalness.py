#!/usr/bin/env python3
"""
V10.6.2 Continuity Naturalness Test
====================================
Tests the improved phrase variation, confidence softening, and location flexibility.

Validates:
1. Phrase variation (4-5 options per type)
2. Confidence-based softening (MEDIUM adds "may", "seems")
3. Core insight integration (occasionally for same_pattern + HIGH confidence)
4. No duplication between sections
5. Varied sentence starters
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    generate_continuity_phrase,
    _soften_phrase,
    apply_continuity_to_why_now,
    apply_continuity_to_core_insight,
    PATTERN_CONTINUITY_PHRASES,
    FRAME_CONTINUITY_PHRASES,
    SIGNAL_CONTINUITY_PHRASES,
    CONFIDENCE_SOFTENERS,
    CORE_INSIGHT_CONTINUITY_TEMPLATES,
)


def test_phrase_variation_count():
    """Test that each category has 4-5 variations."""
    print("\n" + "="*60)
    print("TEST 1: Phrase Variation Count")
    print("="*60)
    
    min_variations = 4
    
    print("Signal phrases:")
    for signal, phrases in SIGNAL_CONTINUITY_PHRASES.items():
        count = len(phrases)
        status = "✅" if count >= min_variations else "❌"
        print(f"  {status} {signal}: {count} variations")
        assert count >= min_variations, f"{signal} has only {count} variations"
    
    print("\nPattern phrases:")
    for pattern, phrases in PATTERN_CONTINUITY_PHRASES.items():
        count = len(phrases)
        status = "✅" if count >= min_variations else "❌"
        print(f"  {status} {pattern}: {count} variations")
        assert count >= min_variations, f"{pattern} has only {count} variations"
    
    print("\nFrame phrases:")
    for frame, phrases in FRAME_CONTINUITY_PHRASES.items():
        count = len(phrases)
        status = "✅" if count >= min_variations else "❌"
        print(f"  {status} {frame}: {count} variations")
        assert count >= min_variations, f"{frame} has only {count} variations"
    
    print("\n✅ PASSED: All categories have sufficient variations")


def test_sentence_starter_variety():
    """Test that phrases don't all start with 'You were already'."""
    print("\n" + "="*60)
    print("TEST 2: Sentence Starter Variety")
    print("="*60)
    
    all_phrases = []
    for phrases in SIGNAL_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    for phrases in PATTERN_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    for phrases in FRAME_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    
    # Count starter patterns
    starters = {}
    for phrase in all_phrases:
        # Get first 3 words
        first_words = " ".join(phrase.split()[:3]).lower()
        starters[first_words] = starters.get(first_words, 0) + 1
    
    print(f"Total phrases: {len(all_phrases)}")
    print("\nTop 5 starters:")
    sorted_starters = sorted(starters.items(), key=lambda x: -x[1])[:5]
    for starter, count in sorted_starters:
        pct = count / len(all_phrases) * 100
        print(f"  '{starter}': {count} ({pct:.0f}%)")
    
    # Check that no single starter dominates (>30%)
    top_starter_pct = sorted_starters[0][1] / len(all_phrases) * 100
    assert top_starter_pct < 30, f"Top starter '{sorted_starters[0][0]}' is {top_starter_pct:.0f}% - too dominant"
    
    print("\n✅ PASSED: Sentence starters are varied")


def test_confidence_softening():
    """Test that MEDIUM confidence applies softening."""
    print("\n" + "="*60)
    print("TEST 3: Confidence-Based Softening")
    print("="*60)
    
    test_phrases = [
        "That warmth is still here.",
        "You were already starting to open…",
        "The softening continues.",
        "You're still at the edge.",
    ]
    
    print("Testing softening:")
    for phrase in test_phrases:
        softened = _soften_phrase(phrase)
        print(f"\n  Original: '{phrase}'")
        print(f"  Softened: '{softened}'")
        # At least some transformation should happen
    
    # Test specific replacements
    test1 = _soften_phrase("That warmth is still here.")
    assert "may still be here" in test1, f"Expected softening, got: {test1}"
    print("\n✅ Verified: 'is still here' → 'may still be here'")
    
    test2 = _soften_phrase("The movement continues.")
    assert "seems to continue" in test2, f"Expected softening, got: {test2}"
    print("✅ Verified: 'continues' → 'seems to continue'")
    
    print("\n✅ PASSED: Confidence softening works correctly")


def test_core_insight_integration():
    """Test that core insight templates exist for key patterns."""
    print("\n" + "="*60)
    print("TEST 4: Core Insight Integration Templates")
    print("="*60)
    
    expected_patterns = ["threshold_standing", "heart_thaw", "relational_reopening"]
    
    print("Core insight templates available for:")
    for pattern in CORE_INSIGHT_CONTINUITY_TEMPLATES:
        templates = CORE_INSIGHT_CONTINUITY_TEMPLATES[pattern]
        print(f"  {pattern}: {len(templates)} templates")
        for t in templates:
            print(f"    - '{t}'")
    
    for pattern in expected_patterns:
        assert pattern in CORE_INSIGHT_CONTINUITY_TEMPLATES, f"Missing {pattern}"
    
    print("\n✅ PASSED: Core insight templates available")


def test_location_selection():
    """Test that generate_continuity_phrase returns correct location info."""
    print("\n" + "="*60)
    print("TEST 5: Location Selection")
    print("="*60)
    
    # Test why_now location (default)
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "signal_continuity",
        "strength": 0.7,
        "dominant_signal": "warmth",
        "pattern_id": "emotional_wave_riding",  # No core insight template
        "frame_type": "something_surfacing",
    }
    
    result = generate_continuity_phrase(continuity_info, "user1", "medium")
    print(f"Signal continuity result: {result}")
    assert result["location"] == "why_now", f"Expected why_now, got {result['location']}"
    assert result["why_now_phrase"] != "", "Expected why_now_phrase"
    print("✅ Signal continuity → why_now location")
    
    # Test that HIGH confidence + same_pattern CAN go to core_insight (30% chance)
    # Run multiple times to check both paths are possible
    core_insight_count = 0
    why_now_count = 0
    
    for i in range(20):
        continuity_info2 = {
            "has_continuity": True,
            "continuity_type": "same_pattern",
            "strength": 0.9,
            "dominant_signal": "warmth",
            "pattern_id": "threshold_standing",  # Has core insight template
            "frame_type": "edge_of_action",
        }
        result2 = generate_continuity_phrase(continuity_info2, f"user_{i}", "high")
        if result2["location"] == "core_insight":
            core_insight_count += 1
        else:
            why_now_count += 1
    
    print(f"\nSame pattern + HIGH confidence over 20 runs:")
    print(f"  core_insight: {core_insight_count}")
    print(f"  why_now: {why_now_count}")
    
    # We expect roughly 30% core_insight (6 out of 20), but allow variance
    assert core_insight_count >= 2, f"Core insight should be selected sometimes (got {core_insight_count})"
    assert why_now_count >= 10, f"Why_now should be selected most times (got {why_now_count})"
    
    print("\n✅ PASSED: Location selection varies appropriately")


def test_duplication_avoidance():
    """Test that continuity isn't applied if similar words exist."""
    print("\n" + "="*60)
    print("TEST 6: Duplication Avoidance")
    print("="*60)
    
    # Why_now that already has continuity words
    why_now_with_still = "You're still processing what happened last week."
    phrase = "That grief is still here."
    result = apply_continuity_to_why_now(why_now_with_still, phrase)
    print(f"Original: '{why_now_with_still}'")
    print(f"Phrase: '{phrase}'")
    print(f"Result: '{result}'")
    assert result == why_now_with_still, "Should not duplicate 'still'"
    print("✅ Correctly skipped - 'still' already present")
    
    # Why_now that already has 'before'
    why_now_with_before = "This connects to patterns from before."
    result2 = apply_continuity_to_why_now(why_now_with_before, phrase)
    assert result2 == why_now_with_before, "Should not duplicate 'before'"
    print("✅ Correctly skipped - 'before' already present")
    
    # Why_now without continuity words - should apply
    why_now_fresh = "The current transit is highlighting relational themes."
    result3 = apply_continuity_to_why_now(why_now_fresh, phrase)
    assert result3.startswith(phrase), "Should prepend phrase"
    print(f"✅ Correctly applied to fresh text: '{result3[:50]}...'")
    
    print("\n✅ PASSED: Duplication avoidance works")


def run_all_tests():
    """Run all V10.6.2 tests."""
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " V10.6.2 CONTINUITY NATURALNESS TEST ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_phrase_variation_count,
        test_sentence_starter_variety,
        test_confidence_softening,
        test_core_insight_integration,
        test_location_selection,
        test_duplication_avoidance,
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
            import traceback
            traceback.print_exc()
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
