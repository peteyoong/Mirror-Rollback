#!/usr/bin/env python3
"""
V10.6.1 Signal-Aware Continuity Test
=====================================
Tests the improved experiential continuity language.

Validates:
1. Pattern-specific phrases are used for same_pattern
2. Frame-specific phrases are used for same_frame
3. Signal-specific phrases are used when dominant signal present
4. LOW confidence skips continuity
5. No generic/meta language ("this pattern", "this energy")
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    detect_continuity,
    generate_continuity_phrase,
    PATTERN_CONTINUITY_PHRASES,
    FRAME_CONTINUITY_PHRASES,
    SIGNAL_CONTINUITY_PHRASES,
    DEFAULT_CONTINUITY_PHRASES,
)


def test_pattern_specific_phrases():
    """Test that pattern-specific phrases are used for same_pattern continuity."""
    print("\n" + "="*60)
    print("TEST 1: Pattern-Specific Phrases")
    print("="*60)
    
    # Simulate same pattern continuity for heart_thaw
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "same_pattern",
        "strength": 0.9,
        "dominant_signal": "warmth",
        "pattern_id": "heart_thaw",
        "frame_type": "testing_the_waters",
    }
    
    phrase = generate_continuity_phrase(continuity_info, "test_user", confidence="high")
    print(f"Pattern: heart_thaw")
    print(f"Generated phrase: '{phrase}'")
    
    # Should use heart_thaw-specific phrase
    assert phrase in PATTERN_CONTINUITY_PHRASES["heart_thaw"], f"Expected pattern-specific phrase, got: {phrase}"
    print("✅ PASSED: Pattern-specific phrase used")


def test_frame_specific_phrases():
    """Test that frame-specific phrases are used for same_frame continuity."""
    print("\n" + "="*60)
    print("TEST 2: Frame-Specific Phrases")
    print("="*60)
    
    # Simulate same frame continuity for edge_of_action
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "same_frame",
        "strength": 0.8,
        "dominant_signal": "growth",
        "pattern_id": "expansion_resistance",
        "frame_type": "edge_of_action",
    }
    
    phrase = generate_continuity_phrase(continuity_info, "test_user2", confidence="medium")
    print(f"Frame: edge_of_action")
    print(f"Generated phrase: '{phrase}'")
    
    # Should use edge_of_action-specific phrase
    assert phrase in FRAME_CONTINUITY_PHRASES["edge_of_action"], f"Expected frame-specific phrase, got: {phrase}"
    print("✅ PASSED: Frame-specific phrase used")


def test_signal_specific_phrases():
    """Test that signal-specific phrases are used when pattern/frame not available."""
    print("\n" + "="*60)
    print("TEST 3: Signal-Specific Phrases")
    print("="*60)
    
    # Simulate signal continuity with grief dominant
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "signal_continuity",
        "strength": 0.65,
        "dominant_signal": "grief",
        "pattern_id": "unknown_pattern",  # Not in PATTERN_CONTINUITY_PHRASES
        "frame_type": "unknown_frame",  # Not in FRAME_CONTINUITY_PHRASES
    }
    
    phrase = generate_continuity_phrase(continuity_info, "test_user3", confidence="medium")
    print(f"Dominant signal: grief")
    print(f"Generated phrase: '{phrase}'")
    
    # Should use grief-specific phrase
    assert phrase in SIGNAL_CONTINUITY_PHRASES["grief"], f"Expected signal-specific phrase, got: {phrase}"
    print("✅ PASSED: Signal-specific phrase used")


def test_low_confidence_skips():
    """Test that LOW confidence skips continuity."""
    print("\n" + "="*60)
    print("TEST 4: LOW Confidence Skips")
    print("="*60)
    
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "same_pattern",
        "strength": 0.9,
        "dominant_signal": "warmth",
        "pattern_id": "heart_thaw",
        "frame_type": "testing_the_waters",
    }
    
    phrase = generate_continuity_phrase(continuity_info, "test_user", confidence="low")
    print(f"Confidence: low")
    print(f"Generated phrase: '{phrase}'")
    
    assert phrase == "", f"Expected empty string for low confidence, got: {phrase}"
    print("✅ PASSED: Low confidence correctly skipped")


def test_low_strength_skips():
    """Test that low strength (< 0.6) skips continuity."""
    print("\n" + "="*60)
    print("TEST 5: Low Strength Skips")
    print("="*60)
    
    continuity_info = {
        "has_continuity": True,
        "continuity_type": "related_frame",
        "strength": 0.55,  # Below 0.6 threshold
        "dominant_signal": "warmth",
        "pattern_id": "heart_thaw",
        "frame_type": "testing_the_waters",
    }
    
    phrase = generate_continuity_phrase(continuity_info, "test_user", confidence="high")
    print(f"Strength: 0.55")
    print(f"Generated phrase: '{phrase}'")
    
    assert phrase == "", f"Expected empty string for low strength, got: {phrase}"
    print("✅ PASSED: Low strength correctly skipped")


def test_no_meta_language():
    """Test that phrases don't contain generic meta language."""
    print("\n" + "="*60)
    print("TEST 6: No Meta Language Check")
    print("="*60)
    
    banned_phrases = ["this pattern", "this energy", "this theme", "this connects"]
    
    # Check all phrase dictionaries
    all_phrases = []
    for phrases in PATTERN_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    for phrases in FRAME_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    for phrases in SIGNAL_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    for phrases in DEFAULT_CONTINUITY_PHRASES.values():
        all_phrases.extend(phrases)
    
    print(f"Checking {len(all_phrases)} phrases for banned meta language...")
    
    violations = []
    for phrase in all_phrases:
        for banned in banned_phrases:
            if banned.lower() in phrase.lower():
                violations.append((phrase, banned))
    
    if violations:
        print("❌ VIOLATIONS FOUND:")
        for phrase, banned in violations:
            print(f"   - '{phrase}' contains '{banned}'")
        assert False, f"Found {len(violations)} phrases with meta language"
    
    print("✅ PASSED: No meta language found in any phrases")


def test_experiential_language():
    """Test that phrases feel experiential and specific."""
    print("\n" + "="*60)
    print("TEST 7: Experiential Language Examples")
    print("="*60)
    
    test_cases = [
        ("warmth", "warmth", "You were already starting to open…"),
        ("grief", "grief", "What you've been grieving is still moving through you."),
        ("hesitation", "hesitation", "That hesitation may still be here."),
        ("heart_thaw", "pattern", "The softening you noticed continues."),
        ("edge_of_action", "frame", "You were already leaning toward movement…"),
    ]
    
    print("Example experiential phrases:")
    for key, phrase_type, example in test_cases:
        if phrase_type == "warmth" or phrase_type == "grief" or phrase_type == "hesitation":
            phrases = SIGNAL_CONTINUITY_PHRASES.get(key, [])
        elif phrase_type == "pattern":
            phrases = PATTERN_CONTINUITY_PHRASES.get(key, [])
        elif phrase_type == "frame":
            phrases = FRAME_CONTINUITY_PHRASES.get(key, [])
        
        if phrases:
            print(f"  {key}: '{phrases[0]}'")
            assert any("you" in p.lower() or "that" in p.lower() or "what" in p.lower() for p in phrases), \
                f"Phrases for {key} don't feel personal"
    
    print("✅ PASSED: All examples feel experiential")


def test_detect_continuity_returns_signal():
    """Test that detect_continuity returns dominant_signal for phrase selection."""
    print("\n" + "="*60)
    print("TEST 8: Continuity Detection Returns Signal Info")
    print("="*60)
    
    recent_history = {
        "recent_patterns": ["heart_thaw"],
        "last_frame_type": "testing_the_waters",
        "last_tones": {"warmth": 0.5},
        "history_count": 1
    }
    
    result = detect_continuity(
        current_pattern_id="heart_thaw",
        current_frame_type="testing_the_waters",
        current_tones={"warmth": 0.6, "hesitation": 0.3},
        recent_history=recent_history
    )
    
    print(f"Result: {result}")
    
    assert "dominant_signal" in result, "Missing dominant_signal in result"
    assert "pattern_id" in result, "Missing pattern_id in result"
    assert "frame_type" in result, "Missing frame_type in result"
    assert result["dominant_signal"] == "warmth", f"Expected warmth, got {result['dominant_signal']}"
    print("✅ PASSED: Continuity detection returns signal info")


def run_all_tests():
    """Run all V10.6.1 continuity tests."""
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " V10.6.1 SIGNAL-AWARE CONTINUITY TEST ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_pattern_specific_phrases,
        test_frame_specific_phrases,
        test_signal_specific_phrases,
        test_low_confidence_skips,
        test_low_strength_skips,
        test_no_meta_language,
        test_experiential_language,
        test_detect_continuity_returns_signal,
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
