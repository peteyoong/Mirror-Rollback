#!/usr/bin/env python3
"""
Pattern Drift Validation Script v0.1.1

Runs 12 synthetic test cases to validate the drift detection logic.
Tests various signal strengths, keyword combinations, and guardrail scenarios.
"""

import sys
sys.path.insert(0, '/app/backend')

from pattern_drift import (
    calculate_pattern_drift,
    extract_text_signals,
    DRIFT_SIGNAL_CLUSTERS,
    ENNEAGRAM_DRIFT_MAP,
    DETECTION_THRESHOLD,
    MIN_DISTINCT_KEYWORDS,
    MIN_SEPARATE_ENTRIES
)

# Test results tracker
results = []

def run_test(test_name: str, baseline_type: int, reflections: list, journals: list, 
             expected_drift: bool, expected_direction: str = None, 
             min_confidence: str = None, description: str = ""):
    """
    Run a single validation test and record result.
    """
    result = calculate_pattern_drift(
        user_id="test_user",
        baseline_type=baseline_type,
        reflections=reflections,
        journal_entries=journals,
        window_days=14,
        threshold=DETECTION_THRESHOLD
    )
    
    # Determine pass/fail
    drift_detected = result.get("drift_detected", False)
    direction = result.get("direction")
    confidence_label = result.get("confidence_label", "low")
    
    passed = True
    failure_reason = []
    
    # Check drift detection
    if drift_detected != expected_drift:
        passed = False
        failure_reason.append(f"Expected drift={expected_drift}, got {drift_detected}")
    
    # Check direction if drift expected
    if expected_drift and expected_direction and direction != expected_direction:
        passed = False
        failure_reason.append(f"Expected direction={expected_direction}, got {direction}")
    
    # Check minimum confidence if specified
    if min_confidence:
        confidence_levels = {"low": 0, "emerging": 1, "moderate": 2}
        if confidence_levels.get(confidence_label, 0) < confidence_levels.get(min_confidence, 0):
            passed = False
            failure_reason.append(f"Expected min confidence={min_confidence}, got {confidence_label}")
    
    test_result = {
        "name": test_name,
        "passed": passed,
        "description": description,
        "expected": {
            "drift": expected_drift,
            "direction": expected_direction,
            "min_confidence": min_confidence
        },
        "actual": {
            "drift": drift_detected,
            "direction": direction,
            "confidence": confidence_label,
            "score": result.get("_debug", {}).get("stress_score", 0) + result.get("_debug", {}).get("growth_score", 0),
            "keywords": result.get("signal_keywords", []),
            "entry_count": result.get("entry_count", 0),
            "distinct_keywords": result.get("distinct_keywords", 0),
            "passes_guardrails": result.get("_debug", {}).get("passes_guardrails", False)
        },
        "failure_reason": failure_reason
    }
    
    results.append(test_result)
    return test_result


def print_results():
    """Print all test results."""
    print("\n" + "="*80)
    print("PATTERN DRIFT VALIDATION RESULTS")
    print("="*80 + "\n")
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for i, r in enumerate(results, 1):
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"Test {i}: {r['name']}")
        print(f"  Status: {status}")
        print(f"  Description: {r['description']}")
        print(f"  Expected: drift={r['expected']['drift']}, direction={r['expected']['direction']}, min_conf={r['expected']['min_confidence']}")
        print(f"  Actual: drift={r['actual']['drift']}, direction={r['actual']['direction']}, conf={r['actual']['confidence']}")
        print(f"  Score: {r['actual']['score']:.2f}, Keywords: {r['actual']['keywords'][:5]}, Entries: {r['actual']['entry_count']}, Distinct KW: {r['actual']['distinct_keywords']}")
        print(f"  Guardrails: {r['actual']['passes_guardrails']}")
        if r["failure_reason"]:
            print(f"  Failure: {', '.join(r['failure_reason'])}")
        print()
    
    print("="*80)
    print(f"SUMMARY: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    print("="*80)
    
    return passed == total


# ============================================
# TEST CASES
# ============================================

def run_all_tests():
    """Run all validation tests."""
    
    print("Running Pattern Drift Validation Tests...")
    print(f"Configuration: THRESHOLD={DETECTION_THRESHOLD}, MIN_KEYWORDS={MIN_DISTINCT_KEYWORDS}, MIN_ENTRIES={MIN_SEPARATE_ENTRIES}")
    
    # ------------------------------------------
    # TEST 1: No signals - should return no drift
    # ------------------------------------------
    run_test(
        "No Signals",
        baseline_type=7,
        reflections=[],
        journals=[],
        expected_drift=False,
        description="Empty data should return no drift"
    )
    
    # ------------------------------------------
    # TEST 2: Single entry with multiple stress keywords
    # Type 7 stress → Type 1
    # ------------------------------------------
    run_test(
        "Single Entry - Strong Stress Signal",
        baseline_type=7,
        reflections=[{
            "perspective": "I feel very critical and judgmental lately. Everything seems wrong and needs to be corrected. My perfectionism is overwhelming. I'm full of resentment about how things should be."
        }],
        journals=[],
        expected_drift=True,
        expected_direction="stress",
        min_confidence="emerging",
        description="Single entry with 4+ Type 1 (stress) keywords should detect drift"
    )
    
    # ------------------------------------------
    # TEST 3: Multiple entries with moderate growth keywords
    # Type 7 growth → Type 5
    # ------------------------------------------
    run_test(
        "Multiple Entries - Growth Signal",
        baseline_type=7,
        reflections=[
            {"perspective": "I've been spending time alone to observe and analyze my thoughts."},
            {"perspective": "I'm withdrawing to focus deeply on understanding one topic."}
        ],
        journals=[
            {"content": "Today I studied and researched for hours. I need more space and privacy."}
        ],
        expected_drift=True,
        expected_direction="growth",
        min_confidence="emerging",
        description="Multiple entries with Type 5 (growth) keywords should detect growth drift"
    )
    
    # ------------------------------------------
    # TEST 4: Generic keywords only - should fail guardrails
    # ------------------------------------------
    run_test(
        "Generic Keywords Only",
        baseline_type=9,
        reflections=[
            {"perspective": "I need to avoid this situation. I want comfort."},
            {"perspective": "I feel like I should avoid confrontation and stay comfortable."}
        ],
        journals=[],
        expected_drift=False,
        description="Only generic/overlapping keywords should fail guardrails"
    )
    
    # ------------------------------------------
    # TEST 5: Type 4 stress → Type 2
    # ------------------------------------------
    run_test(
        "Type 4 Stress Pattern",
        baseline_type=4,
        reflections=[
            {"perspective": "I feel the need to be needed by others. I'm seeking approval constantly."},
            {"perspective": "I've been sacrificing my own needs to help everyone else."}
        ],
        journals=[
            {"content": "I gave everything today, nurturing and caring for others. I need appreciation."}
        ],
        expected_drift=True,
        expected_direction="stress",
        min_confidence="emerging",
        description="Type 4 showing Type 2 behaviors (stress direction)"
    )
    
    # ------------------------------------------
    # TEST 6: Type 4 growth → Type 1
    # ------------------------------------------
    run_test(
        "Type 4 Growth Pattern",
        baseline_type=4,
        reflections=[
            {"perspective": "I've been focused on discipline and structure lately."},
            {"perspective": "I'm channeling my emotions into improving things systematically."}
        ],
        journals=[
            {"content": "I corrected several mistakes today and focused on principles and integrity."}
        ],
        expected_drift=True,
        expected_direction="growth",
        min_confidence="emerging",
        description="Type 4 showing Type 1 behaviors (growth direction)"
    )
    
    # ------------------------------------------
    # TEST 7: Weak signal - below threshold
    # ------------------------------------------
    run_test(
        "Weak Signal Below Threshold",
        baseline_type=3,
        reflections=[
            {"perspective": "I felt a bit peaceful today."}
        ],
        journals=[],
        expected_drift=False,
        description="Single weak signal should not trigger drift"
    )
    
    # ------------------------------------------
    # TEST 8: Type 8 stress → Type 5
    # ------------------------------------------
    run_test(
        "Type 8 Stress Pattern",
        baseline_type=8,
        reflections=[
            {"perspective": "I've been withdrawing and observing from a distance."},
            {"perspective": "I need more privacy and space to think alone."}
        ],
        journals=[
            {"content": "Today I detached and analyzed everything. I feel depleted and need to compartmentalize."}
        ],
        expected_drift=True,
        expected_direction="stress",
        min_confidence="emerging",
        description="Type 8 showing Type 5 behaviors (stress direction)"
    )
    
    # ------------------------------------------
    # TEST 9: Type 8 growth → Type 2
    # ------------------------------------------
    run_test(
        "Type 8 Growth Pattern",
        baseline_type=8,
        reflections=[
            {"perspective": "I've been more nurturing and caring lately."},
            {"perspective": "I'm opening up and letting others in more."}
        ],
        journals=[
            {"content": "Today I was selfless and gave generously to those around me."}
        ],
        expected_drift=True,
        expected_direction="growth",
        min_confidence="emerging",
        description="Type 8 showing Type 2 behaviors (growth direction)"
    )
    
    # ------------------------------------------
    # TEST 10: Mixed signals - stress and growth
    # Should pick the stronger direction
    # ------------------------------------------
    run_test(
        "Mixed Signals - Stronger Stress",
        baseline_type=6,
        reflections=[
            {"perspective": "I feel driven to achieve and perform lately. I want success and recognition."},
            {"perspective": "But also feeling more peaceful and calm sometimes."}
        ],
        journals=[
            {"content": "Today was all about accomplishment and ambitious goals. I need to impress others."}
        ],
        expected_drift=True,
        expected_direction="stress",  # Type 6 stress → 3, growth → 9
        description="Mixed signals should pick stronger direction (stress > growth here)"
    )
    
    # ------------------------------------------
    # TEST 11: Anchor keywords should score higher
    # Type 2 stress → Type 8 (need Type 8 keywords!)
    # ------------------------------------------
    run_test(
        "Anchor Keyword Weight Test",
        baseline_type=2,
        reflections=[
            {"perspective": "I've been feeling the need to confront and dominate every situation."},
            {"perspective": "I feel powerful but also vulnerable. I need to protect my territory."}
        ],
        journals=[],
        expected_drift=True,
        expected_direction="stress",  # Type 2 stress → 8
        min_confidence="emerging",
        description="Type 2 stress should show Type 8 behaviors (confront, dominate, power)"
    )
    
    # ------------------------------------------
    # TEST 12: Journal-only signals (lower weight)
    # ------------------------------------------
    run_test(
        "Journal Only Signals",
        baseline_type=5,
        reflections=[],
        journals=[
            {"content": "I've been scattered and restless, seeking excitement and possibilities everywhere."},
            {"content": "Today I escaped into new plans and adventures. I need options and freedom."},
            {"content": "I can't commit to anything, there are too many possibilities to explore."}
        ],
        expected_drift=True,
        expected_direction="stress",  # Type 5 stress → 7
        description="Journal entries (0.8 weight) should still trigger detection with sufficient signals"
    )
    
    # Print and return overall results
    return print_results()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
