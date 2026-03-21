#!/usr/bin/env python3
"""
V10.7.1 Varied Specificity & Confidence Alignment Test
========================================================
Tests qualifier variation, confidence alignment, and card-level limits.

Validates:
1. Varied qualifiers instead of always "someone"
2. LOW confidence skips specificity
3. MEDIUM confidence uses simpler qualifiers
4. Card-level limit (max 2 injections)
5. Context priority (relational > action > emotional)
"""

import sys
sys.path.insert(0, '/app/backend')

from services.pattern_mirror import (
    inject_specificity,
    _select_varied_qualifier,
    extract_contextual_hints,
    SPECIFICITY_INJECTORS,
    VARIED_QUALIFIERS,
    CONTEXT_PRIORITY,
)


def create_signals(journal_texts):
    """Helper to create signal structure from journal texts."""
    return {
        "memory": {
            "journal_entries": [{"content": t} for t in journal_texts],
            "chat_messages": [],
            "lifeline_events": [],
        }
    }


def test_varied_qualifiers_exist():
    """Test that multiple qualifiers exist for each context."""
    print("\n" + "="*60)
    print("TEST 1: Varied Qualifiers Exist")
    print("="*60)
    
    # Check someone_specific has multiple variations
    someone_injectors = SPECIFICITY_INJECTORS.get("relational", {}).get("someone_specific", {})
    
    print("Checking 'opening up' variations:")
    opening_variations = someone_injectors.get("opening up", [])
    print(f"  Found {len(opening_variations)} variations:")
    for v in opening_variations[:3]:
        print(f"    - '{v}'")
    
    assert isinstance(opening_variations, list), "Should be a list of variations"
    assert len(opening_variations) >= 3, f"Should have 3+ variations, got {len(opening_variations)}"
    
    # Check they use different qualifiers
    unique_qualifiers = set()
    for v in opening_variations:
        if "someone" in v.lower():
            unique_qualifiers.add("someone")
        if "them" in v.lower():
            unique_qualifiers.add("them")
        if "that person" in v.lower():
            unique_qualifiers.add("that person")
    
    print(f"  Unique qualifiers used: {unique_qualifiers}")
    assert len(unique_qualifiers) >= 2, "Should have at least 2 different qualifiers"
    
    print("\n✅ PASSED: Varied qualifiers exist")


def test_low_confidence_skips():
    """Test that LOW confidence skips specificity entirely."""
    print("\n" + "="*60)
    print("TEST 2: LOW Confidence Skips Specificity")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": [],
        "emotional_focus": [],
        "context_strength": 5,
    }
    
    text = "You're opening up again."
    
    # Test with LOW confidence
    result, count = inject_specificity(text, hints, "heart_thaw", confidence="low")
    
    print(f"Text: '{text}'")
    print(f"Confidence: low")
    print(f"Result: '{result}'")
    print(f"Injection count: {count}")
    
    assert result == text, f"LOW confidence should not modify text, got: {result}"
    assert count == 0, f"Injection count should be 0, got: {count}"
    
    print("\n✅ PASSED: LOW confidence correctly skips specificity")


def test_medium_confidence_simpler():
    """Test that MEDIUM confidence prefers simpler/shorter qualifiers."""
    print("\n" + "="*60)
    print("TEST 3: MEDIUM Confidence Prefers Simpler Qualifiers")
    print("="*60)
    
    options = [
        "opening up to someone",  # Simple
        "opening up to them",  # Simple  
        "opening up to that person",  # Longer
        "opening up to a person in your life",  # Longest
    ]
    
    # Test MEDIUM confidence selection
    medium_selections = set()
    for i in range(10):
        selected = _select_varied_qualifier(
            options, 
            f"test text {i}", 
            f"pattern_{i}",
            confidence="medium"
        )
        medium_selections.add(selected)
    
    print(f"MEDIUM confidence selections: {medium_selections}")
    
    # MEDIUM should tend toward shorter options
    short_options = [o for o in medium_selections if len(o) <= 25]
    print(f"Short options selected: {short_options}")
    
    # At least some selections should be short
    assert len(short_options) > 0, "MEDIUM should prefer shorter qualifiers"
    
    print("\n✅ PASSED: MEDIUM confidence prefers simpler qualifiers")


def test_card_level_limit():
    """Test that max 2 injections per card is enforced."""
    print("\n" + "="*60)
    print("TEST 4: Card-Level Limit (Max 2 Injections)")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": ["reaching_out"],
        "emotional_focus": ["missing"],
        "context_strength": 6,
    }
    
    texts = [
        "You're opening up again.",
        "You're reaching out.",
        "You're feeling the loss.",
        "You're taking action.",
    ]
    
    injection_count = 0
    max_injections = 2
    results = []
    
    for text in texts:
        result, injection_count = inject_specificity(
            text, hints, "test_pattern", "high", injection_count, max_injections
        )
        results.append((text, result, injection_count))
    
    print("Injection sequence:")
    for orig, res, cnt in results:
        changed = "✓" if orig != res else "✗"
        print(f"  [{changed}] Count={cnt}: '{orig}' → '{res[:50]}...'")
    
    final_count = results[-1][2]
    print(f"\nFinal injection count: {final_count}")
    
    assert final_count <= max_injections, f"Should not exceed {max_injections}, got {final_count}"
    
    print("\n✅ PASSED: Card-level limit enforced")


def test_context_priority_order():
    """Test that relational > action > emotional priority is followed."""
    print("\n" + "="*60)
    print("TEST 5: Context Priority Order")
    print("="*60)
    
    print(f"Priority order: {CONTEXT_PRIORITY}")
    
    assert CONTEXT_PRIORITY == ["relational", "action", "emotional"], \
        f"Priority should be relational > action > emotional, got {CONTEXT_PRIORITY}"
    
    # Test that relational is tried first
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": ["reaching_out"],
        "emotional_focus": ["missing"],
        "context_strength": 6,
    }
    
    # Text that matches both relational and action
    text = "You're opening up and taking action."
    result, count = inject_specificity(text, hints, "test", "high", 0, 2)
    
    print(f"\nText with multiple matches: '{text}'")
    print(f"Result: '{result}'")
    
    # Should inject relational (opening up) first
    assert "someone" in result.lower() or "them" in result.lower() or "that person" in result.lower(), \
        "Should inject relational qualifier first"
    
    print("✅ Relational context was prioritized")
    
    print("\n✅ PASSED: Context priority order followed")


def test_no_duplicate_qualifiers():
    """Test that we don't add qualifiers when text already has one."""
    print("\n" + "="*60)
    print("TEST 6: No Duplicate Qualifiers")
    print("="*60)
    
    hints = {
        "has_specificity": True,
        "relational_context": ["someone_specific"],
        "action_context": [],
        "emotional_focus": [],
        "context_strength": 3,
    }
    
    # Text that already has "someone"
    text = "You're opening up to someone."
    result, count = inject_specificity(text, hints, "test", "high", 0, 2)
    
    print(f"Text already has 'someone': '{text}'")
    print(f"Result: '{result}'")
    print(f"Injection count: {count}")
    
    # V10.7.1: Should NOT modify text that already has a qualifier
    assert result == text, f"Should not modify text with existing qualifier, got: {result}"
    assert count == 0, f"Injection count should be 0, got: {count}"
    
    # Test with "them" 
    text2 = "You're reaching out to them."
    result2, count2 = inject_specificity(text2, hints, "test2", "high", 0, 2)
    
    print(f"\nText already has 'them': '{text2}'")
    print(f"Result: '{result2}'")
    
    assert result2 == text2, f"Should not modify text with existing 'them', got: {result2}"
    
    print("\n✅ PASSED: No duplicate qualifiers")


def run_all_tests():
    """Run all V10.7.1 tests."""
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " V10.7.1 VARIED SPECIFICITY TEST ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_varied_qualifiers_exist,
        test_low_confidence_skips,
        test_medium_confidence_simpler,
        test_card_level_limit,
        test_context_priority_order,
        test_no_duplicate_qualifiers,
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
