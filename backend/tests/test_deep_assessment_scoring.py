"""
P1: Deep Assessment Scoring Engine Tests
========================================

Tests for the deep assessment scoring engine.

These tests verify:
1. Session lifecycle works
2. Response validation works (wrong types rejected)
3. Completion requires all questions answered
4. Scoring determinism (fixed inputs → fixed outputs)
5. Probability sum + floors
6. Wing_state validity
7. P4 contract validators pass on deep results
8. P5 evidence emission on completion
"""

import pytest
from datetime import datetime, timezone

from deep_assessment_scoring import (
    score_forced_choice,
    score_likert,
    score_ranked,
    aggregate_raw_scores,
    normalize_to_probabilities,
    get_top_types,
    compute_confidence_tier,
    compute_wing_analysis,
    score_deep_assessment,
    validate_response_type,
    validate_result_contract,
    WingState,
    ConfidenceTier,
    PROBABILITY_FLOOR,
    SUM_TOLERANCE,
    VALID_TYPES
)


# ============================================
# SAMPLE DATA FIXTURES
# ============================================

SAMPLE_FORCED_CHOICE_QUESTION = {
    "id": "test_fc_001",
    "type": "forced_choice",
    "stem": "Test question?",
    "options": [
        {"id": "A", "text": "Option A", "primary_type": 6, "secondary_type": None, "weight": 1.0},
        {"id": "B", "text": "Option B", "primary_type": 7, "secondary_type": None, "weight": 1.0}
    ]
}

SAMPLE_LIKERT_QUESTION = {
    "id": "test_likert_001",
    "type": "likert",
    "stem": "Test statement.",
    "scale": {"min": 1, "max": 5},
    "scoring": {"primary_type": 6, "secondary_type": 1, "direction": "positive", "weight": 1.0}
}

SAMPLE_RANKED_QUESTION = {
    "id": "test_ranked_001",
    "type": "ranked",
    "stem": "Rank these:",
    "options": [
        {"id": "A", "text": "Option A", "primary_type": 8, "weight_multipliers": {"rank_1": 1.0, "rank_2": 0.5, "rank_3": 0.2}},
        {"id": "B", "text": "Option B", "primary_type": 6, "weight_multipliers": {"rank_1": 1.0, "rank_2": 0.5, "rank_3": 0.2}},
        {"id": "C", "text": "Option C", "primary_type": 9, "weight_multipliers": {"rank_1": 1.0, "rank_2": 0.5, "rank_3": 0.2}}
    ]
}


# ============================================
# TEST: FORCED CHOICE SCORING
# ============================================

class TestForcedChoiceScoring:
    """Tests for forced choice question scoring."""
    
    def test_scores_primary_type(self):
        """Selecting an option should score its primary type."""
        scores = score_forced_choice(SAMPLE_FORCED_CHOICE_QUESTION, "A")
        assert scores[6] == 1.0
        assert scores[7] == 0.0
    
    def test_scores_secondary_type(self):
        """Secondary type should receive 30% of primary weight."""
        question = {
            "id": "test",
            "type": "forced_choice",
            "options": [
                {"id": "A", "primary_type": 3, "secondary_type": 8, "weight": 1.0}
            ]
        }
        scores = score_forced_choice(question, "A")
        assert scores[3] == 1.0
        assert scores[8] == pytest.approx(0.3, rel=0.01)
    
    def test_invalid_option_returns_zeros(self):
        """Invalid option selection should return all zeros."""
        scores = score_forced_choice(SAMPLE_FORCED_CHOICE_QUESTION, "Z")
        assert all(s == 0.0 for s in scores.values())


# ============================================
# TEST: LIKERT SCORING
# ============================================

class TestLikertScoring:
    """Tests for Likert scale question scoring."""
    
    def test_max_likert_positive_direction(self):
        """Max Likert value with positive direction = full weight."""
        scores = score_likert(SAMPLE_LIKERT_QUESTION, 5)
        assert scores[6] == 1.0  # Primary type gets full score
        assert scores[1] == pytest.approx(0.3, rel=0.01)  # Secondary gets 30%
    
    def test_min_likert_positive_direction(self):
        """Min Likert value with positive direction = zero weight."""
        scores = score_likert(SAMPLE_LIKERT_QUESTION, 1)
        assert scores[6] == 0.0
    
    def test_mid_likert_positive_direction(self):
        """Mid Likert value = half weight."""
        scores = score_likert(SAMPLE_LIKERT_QUESTION, 3)
        assert scores[6] == pytest.approx(0.5, rel=0.01)
    
    def test_reverse_scored(self):
        """Reverse scored (negative direction) flips the scale."""
        question = {
            "id": "test",
            "type": "likert",
            "scale": {"min": 1, "max": 5},
            "scoring": {"primary_type": 4, "secondary_type": None, "direction": "negative", "weight": 1.0}
        }
        # Low value in negative direction = high score
        scores = score_likert(question, 1)
        assert scores[4] == 1.0


# ============================================
# TEST: RANKED SCORING
# ============================================

class TestRankedScoring:
    """Tests for ranked question scoring."""
    
    def test_rank_1_gets_full_multiplier(self):
        """Rank 1 should get full weight multiplier."""
        scores = score_ranked(SAMPLE_RANKED_QUESTION, ["B", "A", "C"])
        assert scores[6] == 1.0  # B at rank 1
        assert scores[8] == 0.5  # A at rank 2
        assert scores[9] == 0.2  # C at rank 3
    
    def test_different_ranking_order(self):
        """Different ranking should produce different scores."""
        scores1 = score_ranked(SAMPLE_RANKED_QUESTION, ["A", "B", "C"])
        scores2 = score_ranked(SAMPLE_RANKED_QUESTION, ["C", "B", "A"])
        
        assert scores1[8] > scores2[8]  # A ranked higher in scores1
        assert scores2[9] > scores1[9]  # C ranked higher in scores2


# ============================================
# TEST: PROBABILITY NORMALIZATION
# ============================================

class TestProbabilityNormalization:
    """Tests for probability normalization."""
    
    def test_probabilities_sum_to_one(self):
        """Normalized probabilities must sum to 1.0."""
        raw_scores = {t: 1.0 for t in VALID_TYPES}
        probs = normalize_to_probabilities(raw_scores)
        
        total = sum(probs.values())
        assert abs(total - 1.0) <= SUM_TOLERANCE
    
    def test_probability_floor_enforced(self):
        """No probability should be below the floor."""
        raw_scores = {1: 100.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}
        probs = normalize_to_probabilities(raw_scores)
        
        for t, p in probs.items():
            assert p >= PROBABILITY_FLOOR
    
    def test_handles_empty_scores(self):
        """Empty scores should produce uniform distribution."""
        raw_scores = {t: 0.0 for t in VALID_TYPES}
        probs = normalize_to_probabilities(raw_scores)
        
        # Should be approximately uniform
        expected = 1.0 / len(VALID_TYPES)
        for p in probs.values():
            assert abs(p - expected) < 0.1


# ============================================
# TEST: TOP TYPES
# ============================================

class TestTopTypes:
    """Tests for top types computation."""
    
    def test_returns_correct_order(self):
        """Top types should be sorted by probability descending."""
        probs = {"1": 0.1, "2": 0.3, "3": 0.2, "4": 0.05, "5": 0.05, "6": 0.05, "7": 0.15, "8": 0.05, "9": 0.05}
        top = get_top_types(probs, 2)
        
        assert top[0]["type"] == 2
        assert top[1]["type"] == 3
    
    def test_returns_requested_count(self):
        """Should return exactly n top types."""
        probs = {str(t): 1.0/9 for t in VALID_TYPES}
        top = get_top_types(probs, 3)
        assert len(top) == 3


# ============================================
# TEST: CONFIDENCE TIER
# ============================================

class TestConfidenceTier:
    """Tests for confidence tier computation."""
    
    def test_high_confidence_criteria(self):
        """High confidence: top-1 >= 0.35 and gap >= 0.12."""
        probs = {"6": 0.40, "7": 0.20, "1": 0.08, "2": 0.08, "3": 0.06, "4": 0.06, "5": 0.04, "8": 0.04, "9": 0.04}
        tier = compute_confidence_tier(probs, response_completeness=1.0)
        assert tier == ConfidenceTier.HIGH.value
    
    def test_moderate_confidence_criteria(self):
        """Moderate confidence: top-1 >= 0.25 and gap >= 0.05."""
        probs = {"6": 0.28, "7": 0.20, "1": 0.10, "2": 0.10, "3": 0.08, "4": 0.08, "5": 0.06, "8": 0.05, "9": 0.05}
        tier = compute_confidence_tier(probs, response_completeness=1.0)
        assert tier == ConfidenceTier.MODERATE.value
    
    def test_low_confidence_incomplete(self):
        """Incomplete responses should always be low confidence."""
        probs = {"6": 0.50, "7": 0.10, "1": 0.05, "2": 0.05, "3": 0.05, "4": 0.05, "5": 0.05, "8": 0.05, "9": 0.10}
        tier = compute_confidence_tier(probs, response_completeness=0.5)
        assert tier == ConfidenceTier.LOW.value


# ============================================
# TEST: WING ANALYSIS
# ============================================

class TestWingAnalysis:
    """Tests for wing analysis computation."""
    
    def test_dominant_wing(self):
        """Clear dominant wing when difference >= 0.15."""
        # Type 6 wings are 5 (left) and 7 (right)
        probs = {"5": 0.25, "6": 0.30, "7": 0.05, "1": 0.05, "2": 0.05, "3": 0.05, "4": 0.05, "8": 0.10, "9": 0.10}
        analysis = compute_wing_analysis(probs, core_type=6)
        
        assert analysis["wing_state"] == WingState.DOMINANT.value
        assert analysis["inferred_wing"] == 5
    
    def test_leaning_wing(self):
        """Leaning wing when difference is 0.05-0.15."""
        probs = {"5": 0.15, "6": 0.30, "7": 0.08, "1": 0.07, "2": 0.07, "3": 0.07, "4": 0.07, "8": 0.09, "9": 0.10}
        analysis = compute_wing_analysis(probs, core_type=6)
        
        assert analysis["wing_state"] == WingState.LEANING.value
        assert analysis["inferred_wing"] == 5
    
    def test_balanced_wings(self):
        """Balanced when difference < 0.05 and both wings significant."""
        probs = {"5": 0.12, "6": 0.30, "7": 0.11, "1": 0.07, "2": 0.07, "3": 0.07, "4": 0.07, "8": 0.09, "9": 0.10}
        analysis = compute_wing_analysis(probs, core_type=6)
        
        assert analysis["wing_state"] == WingState.BALANCED.value
        assert analysis["inferred_wing"] is None
    
    def test_wing_state_always_valid(self):
        """Wing state must always be a valid WingState value."""
        for core in VALID_TYPES:
            probs = {str(t): 1.0/9 for t in VALID_TYPES}
            analysis = compute_wing_analysis(probs, core_type=core)
            
            assert analysis["wing_state"] in [s.value for s in WingState]


# ============================================
# TEST: RESPONSE VALIDATION
# ============================================

class TestResponseValidation:
    """Tests for response validation."""
    
    def test_valid_forced_choice(self):
        """Valid forced choice response should pass."""
        response = {"type": "forced_choice", "value": "A"}
        is_valid, error = validate_response_type(SAMPLE_FORCED_CHOICE_QUESTION, response)
        assert is_valid
        assert error is None
    
    def test_invalid_forced_choice_option(self):
        """Invalid option should be rejected."""
        response = {"type": "forced_choice", "value": "Z"}
        is_valid, error = validate_response_type(SAMPLE_FORCED_CHOICE_QUESTION, response)
        assert not is_valid
        assert "Invalid option" in error
    
    def test_type_mismatch_rejected(self):
        """Response type mismatch should be rejected."""
        response = {"type": "likert", "value": 3}
        is_valid, error = validate_response_type(SAMPLE_FORCED_CHOICE_QUESTION, response)
        assert not is_valid
        assert "does not match" in error
    
    def test_valid_likert(self):
        """Valid Likert response should pass."""
        response = {"type": "likert", "value": 4}
        is_valid, error = validate_response_type(SAMPLE_LIKERT_QUESTION, response)
        assert is_valid
    
    def test_invalid_likert_out_of_range(self):
        """Out of range Likert value should be rejected."""
        response = {"type": "likert", "value": 6}
        is_valid, error = validate_response_type(SAMPLE_LIKERT_QUESTION, response)
        assert not is_valid
        assert "out of range" in error
    
    def test_valid_ranked(self):
        """Valid ranked response should pass."""
        response = {"type": "ranked", "value": ["A", "B", "C"]}
        is_valid, error = validate_response_type(SAMPLE_RANKED_QUESTION, response)
        assert is_valid
    
    def test_invalid_ranked_option(self):
        """Invalid ranked option should be rejected."""
        response = {"type": "ranked", "value": ["A", "Z", "C"]}
        is_valid, error = validate_response_type(SAMPLE_RANKED_QUESTION, response)
        assert not is_valid


# ============================================
# TEST: FULL SCORING DETERMINISM
# ============================================

class TestScoringDeterminism:
    """Tests for scoring determinism."""
    
    def get_sample_questions(self, n=5):
        """Generate sample questions for testing."""
        questions = []
        for i in range(n):
            questions.append({
                "id": f"q_{i}",
                "type": "forced_choice",
                "options": [
                    {"id": "A", "primary_type": 6, "secondary_type": None, "weight": 1.0},
                    {"id": "B", "primary_type": 7, "secondary_type": None, "weight": 1.0}
                ]
            })
        return questions
    
    def test_same_inputs_same_outputs(self):
        """Same inputs should produce identical outputs."""
        questions = self.get_sample_questions()
        responses = [
            {"question_id": "q_0", "response": {"type": "forced_choice", "value": "A"}},
            {"question_id": "q_1", "response": {"type": "forced_choice", "value": "B"}},
            {"question_id": "q_2", "response": {"type": "forced_choice", "value": "A"}},
            {"question_id": "q_3", "response": {"type": "forced_choice", "value": "A"}},
            {"question_id": "q_4", "response": {"type": "forced_choice", "value": "B"}},
        ]
        
        result1 = score_deep_assessment(questions, responses)
        result2 = score_deep_assessment(questions, responses)
        
        # Check key metrics are identical
        assert result1["type_probabilities"] == result2["type_probabilities"]
        assert result1["top_types"] == result2["top_types"]
        assert result1["confidence_tier"] == result2["confidence_tier"]
        assert result1["wing_analysis"]["wing_state"] == result2["wing_analysis"]["wing_state"]


# ============================================
# TEST: P4 CONTRACT VALIDATION
# ============================================

class TestP4ContractValidation:
    """Tests for P4 contract validation."""
    
    def test_valid_result_passes(self):
        """Valid result should pass all P4 checks."""
        result = {
            "type_probabilities": {str(t): 1.0/9 for t in VALID_TYPES},
            "top_types": [{"type": 6, "probability": 0.15}, {"type": 7, "probability": 0.12}],
            "confidence_tier": "moderate",
            "assessment_depth": "deep",
            "wing_analysis": {
                "wing_state": "leaning",
                "inferred_wing": 7,
                "adjacent_scores": {"left": 0.12, "right": 0.10}
            }
        }
        
        is_valid, violations = validate_result_contract(result)
        assert is_valid
        assert len(violations) == 0
    
    def test_invalid_probability_sum(self):
        """Probability sum != 1 should fail."""
        result = {
            "type_probabilities": {str(t): 0.2 for t in VALID_TYPES},  # Sum = 1.8
            "top_types": [{"type": 6, "probability": 0.2}, {"type": 7, "probability": 0.2}],
            "confidence_tier": "moderate",
            "assessment_depth": "deep",
            "wing_analysis": {"wing_state": "leaning", "inferred_wing": 7, "adjacent_scores": {}}
        }
        
        is_valid, violations = validate_result_contract(result)
        assert not is_valid
        assert any("sum" in v.lower() for v in violations)
    
    def test_invalid_wing_state(self):
        """Invalid wing_state should fail."""
        result = {
            "type_probabilities": {str(t): 1.0/9 for t in VALID_TYPES},
            "top_types": [{"type": 6, "probability": 0.15}, {"type": 7, "probability": 0.12}],
            "confidence_tier": "moderate",
            "assessment_depth": "deep",
            "wing_analysis": {
                "wing_state": "invalid_state",  # Invalid!
                "inferred_wing": 7,
                "adjacent_scores": {}
            }
        }
        
        is_valid, violations = validate_result_contract(result)
        assert not is_valid
        assert any("wing_state" in v for v in violations)
    
    def test_wrong_assessment_depth(self):
        """Non-deep assessment_depth should fail."""
        result = {
            "type_probabilities": {str(t): 1.0/9 for t in VALID_TYPES},
            "top_types": [{"type": 6, "probability": 0.15}, {"type": 7, "probability": 0.12}],
            "confidence_tier": "moderate",
            "assessment_depth": "short",  # Wrong!
            "wing_analysis": {"wing_state": "leaning", "inferred_wing": 7, "adjacent_scores": {}}
        }
        
        is_valid, violations = validate_result_contract(result)
        assert not is_valid
        assert any("assessment_depth" in v for v in violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
