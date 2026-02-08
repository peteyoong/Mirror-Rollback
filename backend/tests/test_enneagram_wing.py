"""
Enneagram Wing Calculation Regression Tests
============================================

Tests to verify wing calculation robustness:
1. Case where primary type = 7 and wings compute properly (non-zero)
2. Case where raw_scores missing ⇒ wing is null (not balanced)
"""

import pytest
from unittest.mock import MagicMock

# Wing calculation logic (extracted from frontend for testing)
def compute_wing(
    inferred_core: int,
    wing_left_score: float,
    wing_right_score: float
) -> dict:
    """
    Compute wing result based on core type and wing scores.
    
    Returns:
        dict with:
            - inferred_wing: int | 'balanced' | None
            - dominant_wing: int | 'balanced' | 'none' | None
            - left_type: int
            - right_type: int
            - has_wing_data: bool
    """
    # Calculate wing types with wraparound (1↔9)
    left_wing = 9 if inferred_core == 1 else inferred_core - 1
    right_wing = 1 if inferred_core == 9 else inferred_core + 1
    
    # Max possible: 5 (likert max) + 2 (max FC hits) = 7
    max_wing_score = 7
    normalized_left = wing_left_score / max_wing_score
    normalized_right = wing_right_score / max_wing_score
    normalized_diff = abs(normalized_left - normalized_right)
    
    # ROBUSTNESS FIX: Check if we have valid wing data
    # If both scores are 0 or very close to 0, we don't have enough data
    has_wing_data = (wing_left_score > 0.1) or (wing_right_score > 0.1)
    
    if not has_wing_data:
        # No wing data available - cannot determine wing
        return {
            'inferred_wing': None,
            'dominant_wing': None,
            'left_type': left_wing,
            'right_type': right_wing,
            'has_wing_data': False
        }
    elif normalized_diff < 0.07:
        # Both wings have data AND are balanced
        return {
            'inferred_wing': 'balanced',
            'dominant_wing': 'balanced',
            'left_type': left_wing,
            'right_type': right_wing,
            'has_wing_data': True
        }
    elif normalized_left >= 0.25 and normalized_left > normalized_right:
        return {
            'inferred_wing': left_wing,
            'dominant_wing': left_wing,
            'left_type': left_wing,
            'right_type': right_wing,
            'has_wing_data': True
        }
    elif normalized_right >= 0.25 and normalized_right > normalized_left:
        return {
            'inferred_wing': right_wing,
            'dominant_wing': right_wing,
            'left_type': left_wing,
            'right_type': right_wing,
            'has_wing_data': True
        }
    else:
        # Has data but neither wing is dominant enough
        return {
            'inferred_wing': 'balanced',
            'dominant_wing': 'none',
            'left_type': left_wing,
            'right_type': right_wing,
            'has_wing_data': True
        }


class TestEnneagramWingCalculation:
    """Regression tests for Enneagram wing calculation robustness."""
    
    def test_type_7_wings_compute_properly_nonzero(self):
        """
        Test Case 1: Primary type = 7 and wings compute properly (non-zero)
        
        Type 7 has wings:
        - Left wing: 6 (The Loyalist)
        - Right wing: 8 (The Challenger)
        
        When both wing scores are non-zero, should return a valid wing.
        """
        # Scenario: User clearly leans toward Type 6 wing
        result = compute_wing(
            inferred_core=7,
            wing_left_score=4.5,   # Strong 6-wing signal
            wing_right_score=1.5   # Weak 8-wing signal
        )
        
        # Assertions
        assert result['has_wing_data'] == True, "Should have wing data"
        assert result['left_type'] == 6, "Left wing for Type 7 should be 6"
        assert result['right_type'] == 8, "Right wing for Type 7 should be 8"
        assert result['inferred_wing'] == 6, "Should infer 6 wing (left dominant)"
        assert result['dominant_wing'] == 6, "Dominant wing should be 6"
        
        print(f"✅ Test 1 PASSED: Type 7 with non-zero wings → wing={result['inferred_wing']}")
    
    def test_type_7_wings_compute_properly_right_dominant(self):
        """
        Test Case 1b: Primary type = 7 with right wing (8) dominant.
        """
        result = compute_wing(
            inferred_core=7,
            wing_left_score=1.5,   # Weak 6-wing signal
            wing_right_score=4.5   # Strong 8-wing signal
        )
        
        assert result['has_wing_data'] == True
        assert result['inferred_wing'] == 8, "Should infer 8 wing (right dominant)"
        
        print(f"✅ Test 1b PASSED: Type 7 with right dominant → wing={result['inferred_wing']}")
    
    def test_raw_scores_missing_wing_is_null(self):
        """
        Test Case 2: raw_scores missing ⇒ wing is null (not balanced)
        
        When wing scores are 0,0 (no wing resolution phase completed),
        the wing should be null/None, NOT "balanced".
        """
        result = compute_wing(
            inferred_core=7,
            wing_left_score=0.0,   # No data
            wing_right_score=0.0   # No data
        )
        
        # Assertions
        assert result['has_wing_data'] == False, "Should NOT have wing data"
        assert result['inferred_wing'] is None, "Wing should be None when no data"
        assert result['inferred_wing'] != 'balanced', "Wing should NOT be 'balanced' when no data"
        assert result['dominant_wing'] is None, "Dominant wing should be None"
        
        print(f"✅ Test 2 PASSED: No wing scores → wing=None (not 'balanced')")
    
    def test_balanced_wing_requires_valid_data(self):
        """
        Test Case 3: 'balanced' should only be returned when both scores are present.
        
        When both scores are present and close, 'balanced' is correct.
        """
        result = compute_wing(
            inferred_core=7,
            wing_left_score=3.0,   # Present
            wing_right_score=3.2   # Present, close to left
        )
        
        assert result['has_wing_data'] == True
        assert result['inferred_wing'] == 'balanced', "Should be balanced when scores are close"
        
        print(f"✅ Test 3 PASSED: Close non-zero scores → wing='balanced'")
    
    def test_wing_wraparound_type_1(self):
        """
        Test Case 4: Wing calculation for Type 1 (edge case with wraparound)
        
        Type 1 has wings:
        - Left wing: 9 (wraparound)
        - Right wing: 2
        """
        result = compute_wing(
            inferred_core=1,
            wing_left_score=4.0,   # Strong 9-wing
            wing_right_score=1.0   # Weak 2-wing
        )
        
        assert result['left_type'] == 9, "Left wing for Type 1 should be 9 (wraparound)"
        assert result['right_type'] == 2, "Right wing for Type 1 should be 2"
        assert result['inferred_wing'] == 9, "Should infer 9 wing"
        
        print(f"✅ Test 4 PASSED: Type 1 wraparound → wing=9")
    
    def test_wing_wraparound_type_9(self):
        """
        Test Case 5: Wing calculation for Type 9 (edge case with wraparound)
        
        Type 9 has wings:
        - Left wing: 8
        - Right wing: 1 (wraparound)
        """
        result = compute_wing(
            inferred_core=9,
            wing_left_score=1.0,   # Weak 8-wing
            wing_right_score=4.0   # Strong 1-wing
        )
        
        assert result['left_type'] == 8, "Left wing for Type 9 should be 8"
        assert result['right_type'] == 1, "Right wing for Type 9 should be 1 (wraparound)"
        assert result['inferred_wing'] == 1, "Should infer 1 wing"
        
        print(f"✅ Test 5 PASSED: Type 9 wraparound → wing=1")


def run_tests():
    """Run all regression tests."""
    print("\n" + "=" * 60)
    print("🧪 ENNEAGRAM WING CALCULATION REGRESSION TESTS")
    print("=" * 60 + "\n")
    
    test_class = TestEnneagramWingCalculation()
    
    try:
        test_class.test_type_7_wings_compute_properly_nonzero()
        test_class.test_type_7_wings_compute_properly_right_dominant()
        test_class.test_raw_scores_missing_wing_is_null()
        test_class.test_balanced_wing_requires_valid_data()
        test_class.test_wing_wraparound_type_1()
        test_class.test_wing_wraparound_type_9()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
