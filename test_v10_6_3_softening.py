#!/usr/bin/env python3
"""
V10.6.3 Controlled Softening & Signal Alignment Test
======================================================
Tests prevention of over-softening and signal-aligned variation.

Validates:
1. Maximum ONE softener per sentence (no stacking)
2. Signal-specific softening preferences (grief=direct, warmth=soft)
3. Clarity prioritization
4. No diluted/over-hedged phrasing
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    generate_continuity_phrase,
    _soften_phrase_controlled,
    _select_signal_aligned_phrase,
    SIGNAL_LANGUAGE_STYLE,
    SOFTENER_WORDS,
    SIGNAL_CONTINUITY_PHRASES,
)


def count_softeners(phrase: str) -> int:
    """Count how many softener words appear in a phrase."""
    phrase_lower = phrase.lower()
    return sum(1 for word in SOFTENER_WORDS if word in phrase_lower)


def test_no_stacking_softeners():
    """Test that softening never adds MORE softeners to already-softened phrases."""
    print("\n" + "="*60)
    print("TEST 1: No Stacking Softeners")
    print("="*60)
    
    test_cases = [
        # (phrase, should_change, expected_max_softeners)
        ("That warmth is still here.", True, 1),  # Gets softened to 1
        ("Something in you may be noticing a shift.", False, 2),  # Already soft, unchanged
        ("Part of you might sense something.", False, 3),  # Already soft, unchanged
        ("The softening continues.", True, 1),  # Gets softened to 1
        ("You were already starting to open…", True, 1),  # Gets softened to 1
    ]
    
    print("Testing softening control:")
    for phrase, should_change, max_softeners in test_cases:
        before_count = count_softeners(phrase)
        softened = _soften_phrase_controlled(phrase)
        after_count = count_softeners(softened)
        
        print(f"\n  Original ({before_count} softeners): '{phrase}'")
        print(f"  Softened ({after_count} softeners): '{softened}'")
        
        if should_change:
            # Phrase should be modified, but result should have max 1 softener
            assert after_count <= max_softeners, f"Over-softened! {after_count} softeners in: {softened}"
            print(f"  ✅ Correctly limited to {after_count} softener(s)")
        else:
            # Phrase should be unchanged (already had softeners)
            assert softened == phrase, f"Should be unchanged, got: {softened}"
            print(f"  ✅ Unchanged (already had {before_count} softener(s))")
    
    print("\n✅ PASSED: No stacking of softeners")


def test_already_softened_unchanged():
    """Test that already-softened phrases are not further softened."""
    print("\n" + "="*60)
    print("TEST 2: Already Softened → Unchanged")
    print("="*60)
    
    # Phrases that already have softening
    already_soft = [
        "Something in you is still moving toward connection.",
        "Part of you may be holding back.",
        "That warmth might still be here.",
        "It seems like the feeling persists.",
    ]
    
    for phrase in already_soft:
        before = count_softeners(phrase)
        result = _soften_phrase_controlled(phrase)
        after = count_softeners(result)
        
        print(f"\n  Input: '{phrase}'")
        print(f"  Output: '{result}'")
        
        assert result == phrase, f"Should be unchanged, got: {result}"
        print(f"  ✅ Unchanged (already had {before} softener(s))")
    
    print("\n✅ PASSED: Pre-softened phrases unchanged")


def test_signal_specific_softening():
    """Test that signals with prefer_softening=False don't get softened."""
    print("\n" + "="*60)
    print("TEST 3: Signal-Specific Softening Preferences")
    print("="*60)
    
    # Signals that should NOT prefer softening
    direct_signals = ["clarity", "grief", "pressure", "growth"]
    # Signals that SHOULD prefer softening
    soft_signals = ["warmth", "hesitation", "resistance", "confusion"]
    
    print("Direct signals (prefer_softening=False):")
    for signal in direct_signals:
        style = SIGNAL_LANGUAGE_STYLE.get(signal, {})
        prefer_soft = style.get("prefer_softening", True)
        status = "✅" if not prefer_soft else "❌"
        print(f"  {status} {signal}: prefer_softening={prefer_soft}")
        assert not prefer_soft, f"{signal} should not prefer softening"
    
    print("\nSoft signals (prefer_softening=True):")
    for signal in soft_signals:
        style = SIGNAL_LANGUAGE_STYLE.get(signal, {})
        prefer_soft = style.get("prefer_softening", True)
        status = "✅" if prefer_soft else "❌"
        print(f"  {status} {signal}: prefer_softening={prefer_soft}")
        assert prefer_soft, f"{signal} should prefer softening"
    
    print("\n✅ PASSED: Signal softening preferences correct")


def test_grief_stays_direct():
    """Test that grief-related continuity stays direct at MEDIUM confidence."""
    print("\n" + "="*60)
    print("TEST 4: Grief Signal → Direct Language")
    print("="*60)
    
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "signal_continuity",
        "strength": 0.7,
        "dominant_signal": "grief",
        "pattern_id": "moving_through",
        "frame_type": "grief_underneath",
    }
    
    # Generate with MEDIUM confidence
    result = generate_continuity_phrase(continuity_info, "test_user", "medium")
    phrase = result.get("why_now_phrase", "")
    
    print(f"Signal: grief")
    print(f"Confidence: medium")
    print(f"Generated phrase: '{phrase}'")
    
    # Grief should not have softening applied
    # Check that it's still direct
    softener_count = count_softeners(phrase)
    print(f"Softener count: {softener_count}")
    
    # Grief phrases should be grounded, not over-hedged
    # Allow at most 1 natural softener from the phrase itself
    assert softener_count <= 1, f"Grief phrase over-softened: {phrase}"
    
    print("\n✅ PASSED: Grief stays direct")


def test_clarity_stays_direct():
    """Test that clarity-related continuity stays direct at MEDIUM confidence."""
    print("\n" + "="*60)
    print("TEST 5: Clarity Signal → Direct Language")
    print("="*60)
    
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "same_frame",
        "strength": 0.8,
        "dominant_signal": "clarity",
        "pattern_id": "threshold_standing",
        "frame_type": "clarity_arriving",
    }
    
    # Generate with MEDIUM confidence
    result = generate_continuity_phrase(continuity_info, "test_user2", "medium")
    phrase = result.get("why_now_phrase", "")
    
    print(f"Signal: clarity")
    print(f"Confidence: medium")
    print(f"Generated phrase: '{phrase}'")
    
    softener_count = count_softeners(phrase)
    print(f"Softener count: {softener_count}")
    
    # Clarity should remain clear, not hedged
    assert softener_count <= 1, f"Clarity phrase over-softened: {phrase}"
    
    print("\n✅ PASSED: Clarity stays direct")


def test_signal_aligned_selection():
    """Test that phrase selection prioritizes signal-appropriate phrases."""
    print("\n" + "="*60)
    print("TEST 6: Signal-Aligned Phrase Selection")
    print("="*60)
    
    phrases = SIGNAL_CONTINUITY_PHRASES.get("warmth", [])
    
    # Run selection multiple times with same user to see consistency
    results = set()
    for i in range(10):
        selected = _select_signal_aligned_phrase(
            phrases, "warmth", "test_user", "signal_continuity", "heart_thaw"
        )
        results.add(selected)
    
    print(f"Warmth phrases available: {len(phrases)}")
    print(f"Unique selections over 10 runs: {len(results)}")
    
    # With signal-aligned selection, should still get some variation
    # but within the preferred set
    print(f"Selected phrases: {results}")
    
    # Verify all selected phrases are valid warmth phrases
    for phrase in results:
        assert phrase in phrases, f"Invalid phrase selected: {phrase}"
    
    print("\n✅ PASSED: Signal-aligned selection works")


def test_no_prefix_stacking():
    """Test that prefixes are never added (V10.6.3 change)."""
    print("\n" + "="*60)
    print("TEST 7: No Prefix Addition")
    print("="*60)
    
    # Direct phrases that previously might get prefixes
    direct_phrases = [
        "The feeling persists.",
        "That tension holds.",
        "The wave continues.",
    ]
    
    print("Testing that no prefixes are added:")
    for phrase in direct_phrases:
        softened = _soften_phrase_controlled(phrase)
        
        # Check no prefix was added
        prefixes = ["It seems like", "There may be", "Part of you might", "Something in you"]
        has_prefix = any(softened.lower().startswith(p.lower()) for p in prefixes)
        
        print(f"\n  Original: '{phrase}'")
        print(f"  Result: '{softened}'")
        
        assert not has_prefix, f"Prefix was added: {softened}"
        print("  ✅ No prefix added")
    
    print("\n✅ PASSED: No prefix stacking")


def run_all_tests():
    """Run all V10.6.3 tests."""
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " V10.6.3 CONTROLLED SOFTENING TEST ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_no_stacking_softeners,
        test_already_softened_unchanged,
        test_signal_specific_softening,
        test_grief_stays_direct,
        test_clarity_stays_direct,
        test_signal_aligned_selection,
        test_no_prefix_stacking,
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
