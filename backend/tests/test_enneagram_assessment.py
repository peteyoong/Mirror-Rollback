"""
Unit Tests for Enneagram Deep Assessment Engine

Tests cover:
1. Center scoring produces expected center
2. Head core differentiates 5 vs 6 vs 7
3. Forced both/neither scoring works
4. Wing resolution works
5. Instinct primary/secondary rules
6. Coherence triggers differentiators but does not override type
7. Confidence tier boundaries
8. Session idempotency
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enneagram_assessment import (
    # Question banks
    CENTER_ITEMS, CORE_POOLS, DIFFERENTIATORS, WING_POOLS, INSTINCT_POOL, CONSISTENCY_POOL,
    # Session management
    _create_session, _get_session, _update_session,
    # Scoring
    score_likert_answer, score_forced_answer, process_answer, get_question_by_id,
    # Stage flow
    get_dominant_center, get_top_types, get_top_type_gap, get_next_question, get_progress,
    # Hidden validation
    compute_coherence_score, derive_signals_from_computed_data, TYPE_EXPECTED_SIGNALS,
    # Consistency
    compute_consistency_score,
    # Results
    compute_results,
    # Public API
    start_assessment, submit_answer, get_session_status, format_profile_enneagram,
    # Constants
    Stage, QuestionFormat, ConfidenceTier, Reliability,
    GAP_THRESHOLD, COHERENCE_THRESHOLD, WING_BALANCED_DELTA, INST_DELTA_THRESHOLD
)


class TestCenterScoring:
    """Test 1: Center scoring produces expected center."""
    
    def test_head_center_dominance(self):
        """When head-related answers score high, head center should dominate."""
        session = _create_session("test_user_1")
        
        # Simulate high scores on head items (C01, C04, C07 are head-targeted)
        # Likert 5 = 4 points
        process_answer(session, "C01", {"type": "likert", "value": 5})
        process_answer(session, "C04", {"type": "likert", "value": 5})
        process_answer(session, "C07", {"type": "likert", "value": 5})
        
        # Low scores on heart/gut items
        process_answer(session, "C02", {"type": "likert", "value": 1})
        process_answer(session, "C03", {"type": "likert", "value": 1})
        
        dominant = get_dominant_center(session["center_scores"])
        assert dominant == "head", f"Expected head, got {dominant}"
    
    def test_heart_center_dominance(self):
        """When heart-related answers score high, heart center should dominate."""
        session = _create_session("test_user_2")
        
        # High scores on heart items (C02, C05, C08)
        process_answer(session, "C02", {"type": "likert", "value": 5})
        process_answer(session, "C05", {"type": "likert", "value": 5})
        process_answer(session, "C08", {"type": "likert", "value": 5})
        
        # Low scores on head/gut items
        process_answer(session, "C01", {"type": "likert", "value": 1})
        process_answer(session, "C03", {"type": "likert", "value": 1})
        
        dominant = get_dominant_center(session["center_scores"])
        assert dominant == "heart", f"Expected heart, got {dominant}"
    
    def test_gut_center_dominance(self):
        """When gut-related answers score high, gut center should dominate."""
        session = _create_session("test_user_3")
        
        # High scores on gut items (C03, C06, C09)
        process_answer(session, "C03", {"type": "likert", "value": 5})
        process_answer(session, "C06", {"type": "likert", "value": 5})
        process_answer(session, "C09", {"type": "likert", "value": 5})
        
        # Low scores on head/heart items
        process_answer(session, "C01", {"type": "likert", "value": 1})
        process_answer(session, "C02", {"type": "likert", "value": 1})
        
        dominant = get_dominant_center(session["center_scores"])
        assert dominant == "gut", f"Expected gut, got {dominant}"
    
    def test_forced_choice_center_scoring(self):
        """Forced choice answers should score centers correctly."""
        session = _create_session("test_user_4")
        
        # Answer C10 with "A" (head)
        process_answer(session, "C10", {"type": "forced", "value": "A"})
        
        # Head should have 4 points from forced choice
        assert session["center_scores"]["head"] == 4


class TestHeadCoreDifferentiation:
    """Test 2: Head core differentiates 5 vs 6 vs 7."""
    
    def test_type_5_detection(self):
        """Type 5 questions should score Type 5."""
        session = _create_session("test_user_5")
        session["center_scores"] = {"head": 20, "heart": 5, "gut": 5}
        
        # High scores on Type 5 items
        for q_id in ["H5_01", "H5_02", "H5_03", "H5_04", "H5_05", "H5_06"]:
            process_answer(session, q_id, {"type": "likert", "value": 5})
        
        # Lower on Type 6 and 7
        process_answer(session, "H6_01", {"type": "likert", "value": 2})
        process_answer(session, "H7_01", {"type": "likert", "value": 2})
        
        top_type, _, gap = get_top_type_gap(session["type_scores"])
        assert top_type == 5, f"Expected Type 5, got Type {top_type}"
        assert gap > 0, "Type 5 should have higher score than others"
    
    def test_type_6_detection(self):
        """Type 6 questions should score Type 6."""
        session = _create_session("test_user_6")
        session["center_scores"] = {"head": 20, "heart": 5, "gut": 5}
        
        # High scores on Type 6 items
        for q_id in ["H6_01", "H6_02", "H6_03", "H6_04", "H6_05", "H6_06"]:
            process_answer(session, q_id, {"type": "likert", "value": 5})
        
        # Lower on Type 5 and 7
        process_answer(session, "H5_01", {"type": "likert", "value": 2})
        process_answer(session, "H7_01", {"type": "likert", "value": 2})
        
        top_type, _, _ = get_top_type_gap(session["type_scores"])
        assert top_type == 6, f"Expected Type 6, got Type {top_type}"
    
    def test_type_7_detection(self):
        """Type 7 questions should score Type 7."""
        session = _create_session("test_user_7")
        session["center_scores"] = {"head": 20, "heart": 5, "gut": 5}
        
        # High scores on Type 7 items
        for q_id in ["H7_01", "H7_02", "H7_03", "H7_04", "H7_05", "H7_06"]:
            process_answer(session, q_id, {"type": "likert", "value": 5})
        
        # Lower on Type 5 and 6
        process_answer(session, "H5_01", {"type": "likert", "value": 2})
        process_answer(session, "H6_01", {"type": "likert", "value": 2})
        
        top_type, _, _ = get_top_type_gap(session["type_scores"])
        assert top_type == 7, f"Expected Type 7, got Type {top_type}"


class TestForcedChoiceScoring:
    """Test 3: Forced both/neither scoring works."""
    
    def test_forced_choice_A(self):
        """Choosing A should give 4 points to A target."""
        session = _create_session("test_user_8")
        
        # Use differentiator D_5v6_01 which has A->Type5, B->Type6
        process_answer(session, "D_5v6_01", {"type": "forced", "value": "A"})
        
        assert session["type_scores"][5] == 4, f"Type 5 should have 4 points, has {session['type_scores'][5]}"
        assert session["type_scores"][6] == 0, f"Type 6 should have 0 points, has {session['type_scores'][6]}"
    
    def test_forced_choice_B(self):
        """Choosing B should give 4 points to B target."""
        session = _create_session("test_user_9")
        
        process_answer(session, "D_5v6_01", {"type": "forced", "value": "B"})
        
        assert session["type_scores"][6] == 4, f"Type 6 should have 4 points, has {session['type_scores'][6]}"
        assert session["type_scores"][5] == 0, f"Type 5 should have 0 points, has {session['type_scores'][5]}"
    
    def test_forced_choice_both(self):
        """Choosing both should give 2 points to each target."""
        session = _create_session("test_user_10")
        
        process_answer(session, "D_5v6_01", {"type": "forced", "value": "both"})
        
        assert session["type_scores"][5] == 2, f"Type 5 should have 2 points, has {session['type_scores'][5]}"
        assert session["type_scores"][6] == 2, f"Type 6 should have 2 points, has {session['type_scores'][6]}"
    
    def test_forced_choice_neither(self):
        """Choosing neither should give 0 points but increment neither_count."""
        session = _create_session("test_user_11")
        
        process_answer(session, "D_5v6_01", {"type": "forced", "value": "neither"})
        
        assert session["type_scores"][5] == 0
        assert session["type_scores"][6] == 0
        assert session["neither_count"] == 1


class TestWingResolution:
    """Test 4: Wing resolution works."""
    
    def test_left_wing_dominant(self):
        """When left wing scores higher, that wing should be selected."""
        session = _create_session("test_user_12")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][7] = 20  # Type 7 is top
        session["wing_scores"] = {"left": 15, "right": 5}  # Left wing (6) dominant
        session["instinct_scores"] = {"sp": 10, "so": 5, "sx": 3}
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        # Type 7 left wing is 6
        assert results["wing"] == "6", f"Expected wing 6, got {results['wing']}"
    
    def test_right_wing_dominant(self):
        """When right wing scores higher, that wing should be selected."""
        session = _create_session("test_user_13")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][7] = 20  # Type 7 is top
        session["wing_scores"] = {"left": 5, "right": 15}  # Right wing (8) dominant
        session["instinct_scores"] = {"sp": 10, "so": 5, "sx": 3}
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        # Type 7 right wing is 8
        assert results["wing"] == "8", f"Expected wing 8, got {results['wing']}"
    
    def test_balanced_wings(self):
        """When wings are close, balanced should be detected."""
        session = _create_session("test_user_14")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][7] = 20
        session["wing_scores"] = {"left": 10, "right": 11}  # Within WING_BALANCED_DELTA
        session["instinct_scores"] = {"sp": 10, "so": 5, "sx": 3}
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        assert results["wing"] == "balanced", f"Expected balanced, got {results['wing']}"


class TestInstinctRules:
    """Test 5: Instinct primary/secondary rules."""
    
    def test_clear_primary_secondary(self):
        """When instinct scores have clear gap, both should be assigned."""
        session = _create_session("test_user_15")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][5] = 20
        session["wing_scores"] = {"left": 10, "right": 5}
        session["instinct_scores"] = {"sp": 20, "so": 10, "sx": 5}  # Clear hierarchy
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        assert results["instinct_primary"] == "sp", f"Expected sp primary, got {results['instinct_primary']}"
        assert results["instinct_secondary"] == "so", f"Expected so secondary, got {results['instinct_secondary']}"
    
    def test_close_instincts_no_secondary(self):
        """When primary and secondary are too close, secondary should be null."""
        session = _create_session("test_user_16")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][5] = 20
        session["wing_scores"] = {"left": 10, "right": 5}
        # sp and so within INST_DELTA_THRESHOLD (4)
        session["instinct_scores"] = {"sp": 12, "so": 10, "sx": 5}
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        assert results["instinct_primary"] == "sp"
        assert results["instinct_secondary"] is None, f"Expected None secondary, got {results['instinct_secondary']}"


class TestCoherenceValidation:
    """Test 6: Coherence triggers differentiators but does not override type."""
    
    def test_low_coherence_does_not_change_type(self):
        """Low coherence should not change the determined type."""
        session = _create_session("test_user_17")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][4] = 25  # Type 4 clear winner
        session["type_scores"][5] = 15
        session["wing_scores"] = {"left": 10, "right": 8}
        session["instinct_scores"] = {"sp": 10, "so": 8, "sx": 5}
        session["coherence_score"] = 0.2  # Low coherence (Type 4 doesn't match HD/Astro signals)
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        # Type should still be 4 (coherence NEVER overrides)
        assert results["core_type"] == 4, f"Expected Type 4, got Type {results['core_type']}"
        # But confidence should be lower
        assert results["confidence"] < 0.8, "Confidence should be reduced due to low coherence"
    
    def test_high_coherence_boosts_confidence(self):
        """High coherence should not penalize confidence."""
        session = _create_session("test_user_18")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][4] = 25
        session["type_scores"][5] = 5  # Large gap
        session["wing_scores"] = {"left": 15, "right": 5}  # Clear wing
        session["instinct_scores"] = {"sp": 15, "so": 8, "sx": 3}  # Clear instinct
        session["coherence_score"] = 0.9  # High coherence
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        # High gap + clear wing + clear instinct + high coherence = high confidence
        assert results["confidence_tier"] == "high", f"Expected high tier, got {results['confidence_tier']}"
    
    def test_coherence_signals_derivation(self):
        """Test that signals are derived from computed data."""
        computed_data = {
            "human_design": {
                "type": "Manifestor",
                "authority": "Emotional"
            },
            "astrology": {
                "planets": {
                    "Sun": {"sign": "Aries"},
                    "Moon": {"sign": "Scorpio"}
                }
            }
        }
        
        signals = derive_signals_from_computed_data(computed_data)
        
        # Manifestor should increase assertiveness
        assert "assertiveness" in signals
        assert signals["assertiveness"] > 0.5  # Should be elevated
        
        # Emotional authority should set emotional_intensity
        assert "emotional_intensity" in signals


class TestConfidenceTiers:
    """Test 7: Confidence tier boundaries."""
    
    def test_high_confidence_tier(self):
        """Confidence >= 0.75 should be 'high'."""
        session = _create_session("test_user_19")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][1] = 30  # Very high score
        session["type_scores"][2] = 5   # Large gap
        session["wing_scores"] = {"left": 20, "right": 5}  # Very clear wing
        session["instinct_scores"] = {"sp": 20, "so": 5, "sx": 2}  # Very clear instinct
        session["consistency_score"] = 1.0
        session["coherence_score"] = 1.0
        session["neither_count"] = 0
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        assert results["confidence_tier"] == "high"
    
    def test_moderate_confidence_tier(self):
        """Confidence 0.50-0.74 should be 'moderate'."""
        session = _create_session("test_user_20")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][1] = 15
        session["type_scores"][2] = 10  # Moderate gap
        session["wing_scores"] = {"left": 10, "right": 8}  # Close wings
        session["instinct_scores"] = {"sp": 10, "so": 8, "sx": 6}  # Close instincts
        session["consistency_score"] = 0.7
        session["coherence_score"] = 0.5
        session["neither_count"] = 2
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        assert results["confidence_tier"] in ["moderate", "exploratory"]
    
    def test_exploratory_confidence_tier(self):
        """Confidence < 0.50 should be 'exploratory'."""
        session = _create_session("test_user_21")
        session["type_scores"] = {i: 0 for i in range(1, 10)}
        session["type_scores"][1] = 10
        session["type_scores"][2] = 9  # Tiny gap
        session["type_scores"][3] = 8
        session["wing_scores"] = {"left": 5, "right": 5}  # Exactly tied
        session["instinct_scores"] = {"sp": 5, "so": 5, "sx": 5}  # All tied
        session["consistency_score"] = 0.3
        session["coherence_score"] = 0.2
        session["neither_count"] = 10
        session["stage"] = Stage.DONE.value
        
        results = compute_results(session)
        
        assert results["confidence_tier"] == "exploratory"


class TestSessionIdempotency:
    """Test 8: Session idempotency."""
    
    def test_duplicate_answer_ignored(self):
        """Answering the same question twice should not double-score."""
        session = _create_session("test_user_22")
        
        # Answer C01 first time
        process_answer(session, "C01", {"type": "likert", "value": 5})
        score_after_first = session["center_scores"]["head"]
        
        # Answer C01 second time (should be ignored)
        process_answer(session, "C01", {"type": "likert", "value": 5})
        score_after_second = session["center_scores"]["head"]
        
        assert score_after_first == score_after_second, "Duplicate answer should not change score"
        assert session["asked_question_ids"].count("C01") == 1, "Question should only appear once in asked list"
    
    def test_session_stores_all_answers(self):
        """All answers should be stored in session."""
        session = _create_session("test_user_23")
        
        process_answer(session, "C01", {"type": "likert", "value": 3})
        process_answer(session, "C02", {"type": "likert", "value": 4})
        process_answer(session, "C10", {"type": "forced", "value": "A"})
        
        assert "C01" in session["answers"]
        assert "C02" in session["answers"]
        assert "C10" in session["answers"]
        assert session["answers"]["C01"]["value"] == 3
        assert session["answers"]["C10"]["value"] == "A"


class TestQuestionBank:
    """Additional tests for question bank integrity."""
    
    def test_all_center_items_exist(self):
        """Verify all 12 center items exist."""
        assert len(CENTER_ITEMS) == 12
    
    def test_all_core_pools_have_18_items(self):
        """Verify each core pool has 18 items (6 per type)."""
        for center, pool in CORE_POOLS.items():
            assert len(pool) == 18, f"{center} pool should have 18 items, has {len(pool)}"
    
    def test_all_differentiators_have_separates_field(self):
        """Verify all differentiators specify which types they separate."""
        for diff in DIFFERENTIATORS:
            assert "separates" in diff, f"Differentiator {diff['id']} missing 'separates' field"
            assert len(diff["separates"]) == 2
    
    def test_wing_pools_for_all_types(self):
        """Verify wing pools exist for all 9 types."""
        for t in range(1, 10):
            assert t in WING_POOLS, f"Wing pool missing for Type {t}"
            assert len(WING_POOLS[t]) == 12, f"Type {t} wing pool should have 12 items"
    
    def test_instinct_pool_size(self):
        """Verify instinct pool has 12 items."""
        assert len(INSTINCT_POOL) == 12
    
    def test_consistency_pool_size(self):
        """Verify consistency pool has 6 items."""
        assert len(CONSISTENCY_POOL) == 6


class TestPublicAPI:
    """Test the public API functions."""
    
    def test_start_assessment_returns_session(self):
        """start_assessment should return valid session structure."""
        result = start_assessment("test_api_user_1")
        
        assert "session_id" in result
        assert "question" in result
        assert "progress" in result
        assert result["question"] is not None
        assert result["progress"]["stage"] == "center"
    
    def test_format_profile_enneagram(self):
        """format_profile_enneagram should create correct structure."""
        results = {
            "core_type": 4,
            "wing": "5",
            "instinct_primary": "sx",
            "instinct_secondary": "sp",
            "confidence": 0.78,
            "confidence_tier": "high",
            "assessment_depth": "deep",
            "reliability": "stable",
            "created_at_iso": "2025-01-01T00:00:00Z",
            "_debug": {"test": "data"}
        }
        
        profile = format_profile_enneagram(results, include_debug=False)
        
        assert profile["core_type"] == 4
        assert profile["wing"] == "5"
        assert "_debug" not in profile
        
        profile_with_debug = format_profile_enneagram(results, include_debug=True)
        assert "_debug" in profile_with_debug


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
