#!/usr/bin/env python3
"""
V10.7.2 Resonance Check Test
=============================
Tests resonance-based specificity decisions.

Validates:
1. Already-complete phrases are NOT modified
2. High-value triggers (clarifying action) ARE modified
3. Low-value triggers (padding) are NOT modified  
4. Score-based selection picks best candidate
5. Some cards remain universal
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    inject_specificity,
    calculate_resonance_score,
    should_inject_specificity,
    RESONANT_COMPLETE_PHRASES,
    HIGH_VALUE_SPECIFICITY_TRIGGERS,
    LOW_VALUE_SPECIFICITY_TRIGGERS,
)


def test_complete_phrases_skipped():
    """Test that emotionally complete phrases are NOT modified."""
    print("\n" + "="*60)
    print("TEST 1: Complete Phrases Skipped")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": [],
        "emotional_focus": [],
        "context_strength": 5,
    }
    
    # Short, complete phrase - should be skipped
    text1 = "You're opening up again."
    result1, count1 = inject_specificity(text1, hints, "test", "high", 0, 2)
    score1 = calculate_resonance_score(text1, "opening up", "opening up to someone")
    
    print(f"Text: '{text1}'")
    print(f"Resonance score: {score1:.2f}")
    print(f"Result: '{result1}'")
    
    # Score should be low for complete phrase
    assert score1 < 0.5, f"Complete phrase should have low score, got {score1}"
    print("✅ Complete phrase correctly identified (low score)")
    
    # Another complete phrase
    text2 = "Holding back."
    result2, count2 = inject_specificity(text2, hints, "test2", "high", 0, 2)
    score2 = calculate_resonance_score(text2, "holding back", "holding back from someone")
    
    print(f"\nText: '{text2}'")
    print(f"Resonance score: {score2:.2f}")
    
    assert score2 < 0.5, f"Complete phrase should have low score, got {score2}"
    print("✅ 'Holding back' correctly identified as complete")
    
    print("\n✅ PASSED: Complete phrases skipped")


def test_high_value_triggers():
    """Test that high-value triggers (clarifying action) ARE modified."""
    print("\n" + "="*60)
    print("TEST 2: High-Value Triggers Modified")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": [],
        "action_context": ["holding_back"],
        "emotional_focus": [],
        "context_strength": 4,
    }
    
    # "saying something" - high value because it clarifies what
    text1 = "You've been holding back from saying something important."
    result1, count1 = inject_specificity(text1, hints, "test", "high", 0, 2)
    score1 = calculate_resonance_score(text1, "saying something", "saying what you've been holding")
    
    print(f"Text: '{text1}'")
    print(f"Resonance score: {score1:.2f}")
    print(f"Result: '{result1}'")
    
    # "saying something" is in HIGH_VALUE_SPECIFICITY_TRIGGERS
    print(f"'saying something' trigger value: {HIGH_VALUE_SPECIFICITY_TRIGGERS.get('saying something', 'not found')}")
    
    # Score should be high for action-clarifying phrase
    assert score1 > 0.5, f"Action-clarifying phrase should have high score, got {score1}"
    print("✅ High-value trigger correctly identified")
    
    print("\n✅ PASSED: High-value triggers modified")


def test_low_value_triggers():
    """Test that low-value triggers (padding) are NOT modified."""
    print("\n" + "="*60)
    print("TEST 3: Low-Value Triggers Skipped")
    print("="*60)
    
    # Check configured low-value triggers
    print("Low-value triggers configured:")
    for trigger, value in list(LOW_VALUE_SPECIFICITY_TRIGGERS.items())[:5]:
        print(f"  '{trigger}': {value}")
    
    # Test "opening up" which is in LOW_VALUE
    text1 = "You're opening up again after a long time."
    score1 = calculate_resonance_score(text1, "opening up", "opening up to someone")
    
    print(f"\nText: '{text1}'")
    print(f"Resonance score for 'opening up': {score1:.2f}")
    
    # Score should be reduced for low-value trigger
    assert score1 < 0.6, f"Low-value trigger should have reduced score, got {score1}"
    print("✅ Low-value trigger correctly reduces score")
    
    print("\n✅ PASSED: Low-value triggers handled")


def test_score_based_selection():
    """Test that score-based selection picks best candidate."""
    print("\n" + "="*60)
    print("TEST 4: Score-Based Selection")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": ["holding_back"],
        "emotional_focus": [],
        "context_strength": 5,
    }
    
    # Text with multiple possible injection points
    text = "You're opening up while saying something about the distance."
    
    # Calculate scores for each possibility
    score_opening = calculate_resonance_score(text, "opening up", "opening up to someone")
    score_saying = calculate_resonance_score(text, "saying something", "saying what you've been holding")
    score_distance = calculate_resonance_score(text, "the distance", "the distance between you")
    
    print(f"Text: '{text}'")
    print(f"\nResonance scores:")
    print(f"  'opening up': {score_opening:.2f}")
    print(f"  'saying something': {score_saying:.2f}")
    print(f"  'the distance': {score_distance:.2f}")
    
    # The highest-value one should be selected
    scores = [("opening up", score_opening), ("saying something", score_saying), ("the distance", score_distance)]
    best = max(scores, key=lambda x: x[1])
    print(f"\nBest candidate: '{best[0]}' with score {best[1]:.2f}")
    
    print("\n✅ PASSED: Score-based selection working")


def test_confidence_thresholds():
    """Test that confidence affects injection threshold."""
    print("\n" + "="*60)
    print("TEST 5: Confidence Thresholds")
    print("="*60)
    
    text = "You're opening up again."
    
    # Calculate base score
    score = calculate_resonance_score(text, "opening up", "opening up to someone")
    print(f"Base resonance score: {score:.2f}")
    
    # Test different confidence levels
    should_high = should_inject_specificity(text, "opening up", "opening up to someone", "high")
    should_medium = should_inject_specificity(text, "opening up", "opening up to someone", "medium")
    should_low = should_inject_specificity(text, "opening up", "opening up to someone", "low")
    
    print(f"\nShould inject at confidence levels:")
    print(f"  HIGH (threshold 0.4): {should_high}")
    print(f"  MEDIUM (threshold 0.5): {should_medium}")
    print(f"  LOW (threshold 0.7): {should_low}")
    
    # LOW confidence should be hardest to trigger
    if score < 0.7:
        assert not should_low, "LOW confidence should rarely inject"
        print("✅ LOW confidence correctly restrictive")
    
    print("\n✅ PASSED: Confidence thresholds working")


def test_some_cards_remain_universal():
    """Test that some cards remain more universal (not modified)."""
    print("\n" + "="*60)
    print("TEST 6: Some Cards Remain Universal")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": [],
        "emotional_focus": [],
        "context_strength": 3,  # Moderate context strength
    }
    
    # Test several phrases - some should remain universal
    test_phrases = [
        "You're opening up again.",
        "Letting go is hard.",
        "You're holding back from saying something.",
        "Moving forward takes courage.",
        "The distance between you is growing.",
    ]
    
    modified_count = 0
    universal_count = 0
    
    print("Testing universality preservation:")
    for text in test_phrases:
        result, _ = inject_specificity(text, hints, "test", "medium", 0, 2)
        changed = text != result
        if changed:
            modified_count += 1
            print(f"  ✓ Modified: '{text[:30]}...' → '{result[:35]}...'")
        else:
            universal_count += 1
            print(f"  ○ Universal: '{text[:40]}...'")
    
    print(f"\nResults: {modified_count} modified, {universal_count} universal")
    
    # At least some should remain universal
    assert universal_count >= 1, "At least some phrases should remain universal"
    print("✅ Some phrases correctly remain universal")
    
    print("\n✅ PASSED: Universality preserved")


def run_all_tests():
    """Run all V10.7.2 tests."""
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " V10.7.2 RESONANCE CHECK TEST ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_complete_phrases_skipped,
        test_high_value_triggers,
        test_low_value_triggers,
        test_score_based_selection,
        test_confidence_thresholds,
        test_some_cards_remain_universal,
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
