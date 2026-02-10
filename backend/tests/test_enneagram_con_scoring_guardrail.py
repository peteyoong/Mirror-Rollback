#!/usr/bin/env python3
"""
Enneagram CON_* Scoring Guardrail Tests
========================================

These tests ensure that CON_* (consistency/validation) questions can NEVER affect:
- core_type
- wing  
- center

They may ONLY affect:
- reliability
- confidence tier / final confidence score

This is a CANON CONTRACT for Project Mirror's Enneagram assessment.
Any change that breaks these tests is a regression.
"""

import sys
sys.path.insert(0, '/app/backend')

import copy
import pytest
from unittest.mock import patch
from enneagram_assessment import (
    _create_session,
    process_answer,
    compute_results,
    get_dominant_center,
    CONSISTENCY_POOL,
    CENTER_ITEMS,
    CORE_POOLS,
    DIFFERENTIATORS,
    WING_POOLS,
    INSTINCT_POOL,
    score_likert_answer,
)

# =============================================================================
# DETERMINISTIC BASELINE FIXTURE
# =============================================================================
# This fixture produces a known, predictable result that we use as baseline.
# The answers are crafted to yield a clear Type 5 with 4 wing, head center.

BASELINE_ANSWERS = {
    # CENTER QUESTIONS - Establish head center dominance
    "C01": {"value": 5},  # Head center - strong agree
    "C02": {"value": 2},  # Heart center - disagree
    "C03": {"value": 2},  # Gut center - disagree
    "C04": {"value": 5},  # Head center
    "C05": {"value": 2},  # Heart center
    "C06": {"value": 2},  # Gut center
    "C07": {"value": 5},  # Head center
    "C08": {"value": 2},  # Heart center
    "C09": {"value": 2},  # Gut center
    
    # HEAD CENTER CORE TYPE QUESTIONS - Establish Type 5 dominance
    # Type 5 patterns: Observer, knowledge-seeking, boundary-setting
    "H5_01": {"value": 5},  # Type 5 question
    "H5_02": {"value": 5},
    "H5_03": {"value": 5},
    "H5_04": {"value": 5},
    "H5_05": {"value": 5},
    "H5_06": {"value": 5},
    
    # Type 6 (adjacent) - moderate
    "H6_01": {"value": 2},
    "H6_02": {"value": 2},
    "H6_03": {"value": 2},
    
    # Type 7 (adjacent) - low
    "H7_01": {"value": 2},
    "H7_02": {"value": 2},
    "H7_03": {"value": 2},
}

# Expected baseline result - we verify type 5 and head center
# Wing depends on wing questions which we didn't include, so we'll verify
# the core guarantee: CON_* cannot change type or center
EXPECTED_BASELINE = {
    "core_type": 5,
    "center": "head",
}


def create_test_session_with_answers(answers: dict, include_con: bool = False, con_value: int = 3) -> dict:
    """
    Create a test session and process the given answers.
    
    Args:
        answers: Dict of question_id -> answer
        include_con: Whether to include CON_* questions
        con_value: Value to use for all CON_* answers (1-5)
    
    Returns:
        Session dict with all answers processed
    """
    session = _create_session("test_user")
    
    # Process baseline answers
    for q_id, answer in answers.items():
        try:
            process_answer(session, q_id, answer)
        except ValueError:
            # Question may not exist in current config, skip
            pass
    
    # Process CON_* questions if requested
    if include_con:
        for con_q in CONSISTENCY_POOL:
            con_id = con_q["id"]
            if con_id not in session["answers"]:
                process_answer(session, con_id, {"value": con_value})
    
    return session


# =============================================================================
# TEST CLASS: CON_* IMMUNITY VERIFICATION
# =============================================================================

class TestCONScoringGuardrail:
    """
    Verify that CON_* questions NEVER affect core_type, wing, or center.
    
    Test methodology:
    1. Establish baseline result with fixed answers
    2. Run same assessment with CON_* = lowest agreement (1)
    3. Run same assessment with CON_* = highest agreement (5)
    4. Assert type/wing/center are IDENTICAL across all runs
    5. Assert confidence/reliability CAN change
    """
    
    def test_con_questions_have_empty_targets(self):
        """All CON_* questions must have empty targets array."""
        for question in CONSISTENCY_POOL:
            q_id = question["id"]
            assert q_id.startswith("CON_"), f"Non-CON question in CONSISTENCY_POOL: {q_id}"
            
            scoring = question.get("scoring", {})
            targets = scoring.get("targets", [])
            
            assert targets == [], \
                f"CON question {q_id} has non-empty targets: {targets}. " \
                f"CON_* questions must have targets=[] to prevent scoring impact."
    
    def test_con_questions_have_zero_weight_for_structural(self):
        """CON_* questions must not contribute to any structural dimension."""
        for question in CONSISTENCY_POOL:
            q_id = question["id"]
            scoring = question.get("scoring", {})
            targets = scoring.get("targets", [])
            
            for target in targets:
                # Check all structural dimensions have zero or no weight
                if "center" in target:
                    weight = target.get("weight", 0)
                    assert weight == 0, \
                        f"CON question {q_id} has center target with weight={weight}"
                
                if "type" in target:
                    weight = target.get("weight", 0)
                    assert weight == 0, \
                        f"CON question {q_id} has type target with weight={weight}"
                
                if "wing" in target:
                    weight = target.get("weight", 0)
                    assert weight == 0, \
                        f"CON question {q_id} has wing target with weight={weight}"
    
    def test_baseline_produces_expected_result(self):
        """Verify our baseline fixture produces the expected type/wing/center."""
        session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        
        # Get center
        center = get_dominant_center(session["center_scores"])
        assert center == EXPECTED_BASELINE["center"], \
            f"Baseline center mismatch: {center} != {EXPECTED_BASELINE['center']}"
        
        # Get results
        results = compute_results(session)
        
        assert results["core_type"] == EXPECTED_BASELINE["core_type"], \
            f"Baseline type mismatch: {results['core_type']} != {EXPECTED_BASELINE['core_type']}"
    
    def test_con_lowest_does_not_change_type(self):
        """CON_* answers at lowest (1) must not change core_type."""
        # Baseline without CON
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_results = compute_results(baseline_session)
        
        # With CON_* = 1 (lowest agreement)
        con_low_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=1)
        con_low_results = compute_results(con_low_session)
        
        assert baseline_results["core_type"] == con_low_results["core_type"], \
            f"CON_* (low) changed core_type: {baseline_results['core_type']} -> {con_low_results['core_type']}"
    
    def test_con_highest_does_not_change_type(self):
        """CON_* answers at highest (5) must not change core_type."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_results = compute_results(baseline_session)
        
        con_high_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        con_high_results = compute_results(con_high_session)
        
        assert baseline_results["core_type"] == con_high_results["core_type"], \
            f"CON_* (high) changed core_type: {baseline_results['core_type']} -> {con_high_results['core_type']}"
    
    def test_con_lowest_does_not_change_wing(self):
        """CON_* answers at lowest (1) must not change wing."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_results = compute_results(baseline_session)
        
        con_low_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=1)
        con_low_results = compute_results(con_low_session)
        
        assert baseline_results["wing"] == con_low_results["wing"], \
            f"CON_* (low) changed wing: {baseline_results['wing']} -> {con_low_results['wing']}"
    
    def test_con_highest_does_not_change_wing(self):
        """CON_* answers at highest (5) must not change wing."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_results = compute_results(baseline_session)
        
        con_high_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        con_high_results = compute_results(con_high_session)
        
        assert baseline_results["wing"] == con_high_results["wing"], \
            f"CON_* (high) changed wing: {baseline_results['wing']} -> {con_high_results['wing']}"
    
    def test_con_lowest_does_not_change_center(self):
        """CON_* answers at lowest (1) must not change dominant center."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_center = get_dominant_center(baseline_session["center_scores"])
        
        con_low_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=1)
        con_low_center = get_dominant_center(con_low_session["center_scores"])
        
        assert baseline_center == con_low_center, \
            f"CON_* (low) changed center: {baseline_center} -> {con_low_center}"
    
    def test_con_highest_does_not_change_center(self):
        """CON_* answers at highest (5) must not change dominant center."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_center = get_dominant_center(baseline_session["center_scores"])
        
        con_high_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        con_high_center = get_dominant_center(con_high_session["center_scores"])
        
        assert baseline_center == con_high_center, \
            f"CON_* (high) changed center: {baseline_center} -> {con_high_center}"
    
    def test_center_scores_unchanged_by_con(self):
        """Raw center_scores must be identical with or without CON_* answers."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        con_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        
        assert baseline_session["center_scores"] == con_session["center_scores"], \
            f"CON_* changed center_scores: {baseline_session['center_scores']} -> {con_session['center_scores']}"
    
    def test_type_scores_unchanged_by_con(self):
        """Raw type_scores must be identical with or without CON_* answers."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        con_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        
        assert baseline_session["type_scores"] == con_session["type_scores"], \
            f"CON_* changed type_scores: {baseline_session['type_scores']} -> {con_session['type_scores']}"
    
    def test_wing_scores_unchanged_by_con(self):
        """Raw wing_scores must be identical with or without CON_* answers."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        con_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        
        assert baseline_session["wing_scores"] == con_session["wing_scores"], \
            f"CON_* changed wing_scores: {baseline_session['wing_scores']} -> {con_session['wing_scores']}"
    
    def test_confidence_can_change_with_con(self):
        """Confidence IS allowed to change based on CON_* answers."""
        # This test documents that confidence can change - not that it must
        con_low_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=1)
        con_high_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        
        con_low_results = compute_results(con_low_session)
        con_high_results = compute_results(con_high_session)
        
        # Confidence is allowed to differ (but not required to)
        # The key assertion is that TYPE/WING/CENTER are unchanged
        assert con_low_results["core_type"] == con_high_results["core_type"]
        assert con_low_results["wing"] == con_high_results["wing"]
    
    def test_confidence_change_within_bounds(self):
        """Confidence change from CON_* must stay within reasonable bounds."""
        con_low_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=1)
        con_high_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=5)
        
        con_low_results = compute_results(con_low_session)
        con_high_results = compute_results(con_high_session)
        
        confidence_delta = abs(con_high_results["confidence"] - con_low_results["confidence"])
        
        # CON_* should not cause more than 30% confidence swing
        MAX_CONFIDENCE_DELTA = 0.30
        assert confidence_delta <= MAX_CONFIDENCE_DELTA, \
            f"CON_* caused excessive confidence change: {confidence_delta:.2f} > {MAX_CONFIDENCE_DELTA}"


# =============================================================================
# TEST CLASS: EXTREME EDGE CASES
# =============================================================================

class TestCONExtremeEdgeCases:
    """Test edge cases and extreme scenarios."""
    
    def test_all_con_questions_answered_same(self):
        """All CON_* answered identically should not affect type."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_results = compute_results(baseline_session)
        
        # All CON at 3 (neutral)
        neutral_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=True, con_value=3)
        neutral_results = compute_results(neutral_session)
        
        assert baseline_results["core_type"] == neutral_results["core_type"]
        assert baseline_results["wing"] == neutral_results["wing"]
    
    def test_con_answers_varied(self):
        """Varied CON_* answers should still not affect type."""
        baseline_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        baseline_results = compute_results(baseline_session)
        
        # Create session and manually vary CON answers
        varied_session = create_test_session_with_answers(BASELINE_ANSWERS, include_con=False)
        
        con_values = [1, 5, 2, 4]  # Varied pattern
        for i, con_q in enumerate(CONSISTENCY_POOL):
            con_id = con_q["id"]
            value = con_values[i % len(con_values)]
            process_answer(varied_session, con_id, {"value": value})
        
        varied_results = compute_results(varied_session)
        
        assert baseline_results["core_type"] == varied_results["core_type"], \
            f"Varied CON_* changed type: {baseline_results['core_type']} -> {varied_results['core_type']}"
        assert baseline_results["wing"] == varied_results["wing"], \
            f"Varied CON_* changed wing: {baseline_results['wing']} -> {varied_results['wing']}"


# =============================================================================
# TEST CLASS: GUARDRAIL ASSERTIONS IN SCORING CODE
# =============================================================================

class TestScoringCodeGuardrails:
    """Verify guardrails exist in the scoring code itself."""
    
    def test_con_question_scoring_produces_no_structural_changes(self):
        """Directly verify CON_* scoring has no effect on structural scores."""
        session = _create_session("test_user")
        
        # Record initial scores
        initial_center = copy.deepcopy(session["center_scores"])
        initial_type = copy.deepcopy(session["type_scores"])
        initial_wing = copy.deepcopy(session["wing_scores"])
        
        # Process all CON_* questions with extreme values
        for con_q in CONSISTENCY_POOL:
            scoring = con_q.get("scoring", {})
            score_likert_answer(5, scoring, session)  # Max agreement
        
        # Verify no change
        assert session["center_scores"] == initial_center, \
            "CON_* scoring changed center_scores"
        assert session["type_scores"] == initial_type, \
            "CON_* scoring changed type_scores"
        assert session["wing_scores"] == initial_wing, \
            "CON_* scoring changed wing_scores"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
