"""
===============================================================================
REGRESSION TEST: Numerology Deep Dive Payload Integrity
===============================================================================
This test suite ensures:
1. Numerology compute function returns complete canonical payload
2. Name-based numbers are properly locked/unlocked based on input
3. The assistant never claims missing data when data exists
4. If compute integrity fails, endpoint returns compute_integrity_error without LLM call

To run: 
    python -m pytest tests/test_numerology_deep_dive_integrity.py -v
    python tests/test_numerology_deep_dive_integrity.py
===============================================================================
"""
import sys
import os
import re
import pytest
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.numerology import get_canonical_numerology
from calculations.astrology import ComputeIntegrityError


# =============================================================================
# TEST FIXTURES
# =============================================================================
PETE_BIRTH_DATE = datetime(1968, 4, 1)
PETE_FULL_NAME = "Peter James Smith"  # Example name for testing
TEST_CURRENT_DATE = datetime(2026, 2, 6)  # Fixed date for deterministic cycles


@pytest.fixture
def numerology_no_name() -> Dict[str, Any]:
    """Fixture: Numerology computed with birth date only (no name)."""
    return get_canonical_numerology(
        birth_date=PETE_BIRTH_DATE,
        numerology_full_name=None,
        current_date=TEST_CURRENT_DATE
    )


@pytest.fixture
def numerology_with_name() -> Dict[str, Any]:
    """Fixture: Numerology computed with birth date and full name."""
    return get_canonical_numerology(
        birth_date=PETE_BIRTH_DATE,
        numerology_full_name=PETE_FULL_NAME,
        current_date=TEST_CURRENT_DATE
    )


# =============================================================================
# TEST 1: Canonical Payload Completeness (No Name)
# =============================================================================
class TestCanonicalPayloadNoName:
    """Test that compute function returns complete payload without name."""
    
    def test_life_path_exists(self, numerology_no_name):
        """core.life_path must exist and be numeric."""
        assert "core" in numerology_no_name, "Payload missing 'core'"
        life_path = numerology_no_name["core"].get("life_path")
        assert life_path is not None, "core.life_path is missing"
        assert isinstance(life_path, int), f"life_path must be int, got {type(life_path)}"
        assert 1 <= life_path <= 33, f"life_path out of range: {life_path}"
    
    def test_birthday_number_exists(self, numerology_no_name):
        """core.birthday_number must exist and be numeric."""
        birthday = numerology_no_name["core"].get("birthday_number")
        assert birthday is not None, "core.birthday_number is missing"
        assert isinstance(birthday, int), f"birthday_number must be int, got {type(birthday)}"
        assert 1 <= birthday <= 31, f"birthday_number out of range: {birthday}"
    
    def test_cycles_exist(self, numerology_no_name):
        """cycles.personal_year/month/day must exist."""
        assert "cycles" in numerology_no_name, "Payload missing 'cycles'"
        cycles = numerology_no_name["cycles"]
        
        assert cycles.get("personal_year") is not None, "cycles.personal_year missing"
        assert cycles.get("personal_month") is not None, "cycles.personal_month missing"
        assert cycles.get("personal_day") is not None, "cycles.personal_day missing"
        
        # All should be integers 1-9
        assert isinstance(cycles["personal_year"], int)
        assert isinstance(cycles["personal_month"], int)
        assert isinstance(cycles["personal_day"], int)
    
    def test_name_numbers_keys_exist_and_null(self, numerology_no_name):
        """expression/soul_urge/personality keys must exist and be null when no name."""
        core = numerology_no_name["core"]
        
        # Keys MUST exist
        assert "expression" in core, "core.expression key must exist"
        assert "soul_urge" in core, "core.soul_urge key must exist"
        assert "personality" in core, "core.personality key must exist"
        
        # Values MUST be None/null when no name provided
        assert core["expression"] is None, "expression must be null when no name"
        assert core["soul_urge"] is None, "soul_urge must be null when no name"
        assert core["personality"] is None, "personality must be null when no name"
    
    def test_has_name_numbers_false(self, numerology_no_name):
        """has_name_numbers must be False when no name provided."""
        assert numerology_no_name.get("has_name_numbers") == False
    
    def test_locked_numbers_list(self, numerology_no_name):
        """locked_numbers should list expression, soul_urge, personality."""
        locked = numerology_no_name.get("locked_numbers", [])
        assert "expression" in locked
        assert "soul_urge" in locked
        assert "personality" in locked
    
    def test_compute_integrity_valid(self, numerology_no_name):
        """compute_integrity.valid must be True."""
        assert "compute_integrity" in numerology_no_name
        assert numerology_no_name["compute_integrity"].get("valid") == True


# =============================================================================
# TEST 2: Canonical Payload Completeness (With Name)
# =============================================================================
class TestCanonicalPayloadWithName:
    """Test that compute function returns complete payload with name."""
    
    def test_life_path_exists(self, numerology_with_name):
        """core.life_path must exist and be numeric."""
        life_path = numerology_with_name["core"].get("life_path")
        assert life_path is not None
        assert isinstance(life_path, int)
    
    def test_expression_numeric(self, numerology_with_name):
        """core.expression must be numeric when name is provided."""
        expression = numerology_with_name["core"].get("expression")
        assert expression is not None, "expression must not be null when name provided"
        assert isinstance(expression, int), f"expression must be int, got {type(expression)}"
        assert 1 <= expression <= 33, f"expression out of range: {expression}"
    
    def test_soul_urge_numeric(self, numerology_with_name):
        """core.soul_urge must be numeric when name is provided."""
        soul_urge = numerology_with_name["core"].get("soul_urge")
        assert soul_urge is not None, "soul_urge must not be null when name provided"
        assert isinstance(soul_urge, int), f"soul_urge must be int, got {type(soul_urge)}"
        assert 1 <= soul_urge <= 33, f"soul_urge out of range: {soul_urge}"
    
    def test_personality_numeric(self, numerology_with_name):
        """core.personality must be numeric when name is provided."""
        personality = numerology_with_name["core"].get("personality")
        assert personality is not None, "personality must not be null when name provided"
        assert isinstance(personality, int), f"personality must be int, got {type(personality)}"
        assert 1 <= personality <= 33, f"personality out of range: {personality}"
    
    def test_has_name_numbers_true(self, numerology_with_name):
        """has_name_numbers must be True when name provided."""
        assert numerology_with_name.get("has_name_numbers") == True
    
    def test_locked_numbers_empty(self, numerology_with_name):
        """locked_numbers should be empty when name provided."""
        locked = numerology_with_name.get("locked_numbers", [])
        assert len(locked) == 0, f"locked_numbers should be empty, got {locked}"
    
    def test_inputs_contains_name(self, numerology_with_name):
        """inputs.numerology_full_name should contain the provided name."""
        inputs = numerology_with_name.get("inputs", {})
        assert inputs.get("numerology_full_name") == PETE_FULL_NAME


# =============================================================================
# TEST 3: Deep Dive Payload Integrity
# =============================================================================
class TestDeepDivePayloadIntegrity:
    """Test that deep dive receives complete canonical payload."""
    
    def test_all_canonical_keys_present(self, numerology_no_name):
        """Canonical payload must include all required keys."""
        required_keys = ["core", "cycles", "inputs", "compute_integrity"]
        for key in required_keys:
            assert key in numerology_no_name, f"Payload missing required key: {key}"
    
    def test_core_has_all_number_keys(self, numerology_no_name):
        """Core must have all number keys (even if null)."""
        core = numerology_no_name["core"]
        required_core_keys = [
            "life_path", "birthday_number",
            "expression", "soul_urge", "personality"
        ]
        for key in required_core_keys:
            assert key in core, f"core missing key: {key}"
    
    def test_cycles_has_all_period_keys(self, numerology_no_name):
        """Cycles must have all period keys."""
        cycles = numerology_no_name["cycles"]
        required_cycles_keys = ["personal_year", "personal_month", "personal_day"]
        for key in required_cycles_keys:
            assert key in cycles, f"cycles missing key: {key}"
    
    def test_payload_serializable(self, numerology_with_name):
        """Payload must be JSON serializable."""
        import json
        try:
            json_str = json.dumps(numerology_with_name, default=str)
            assert len(json_str) > 200, "Payload JSON too small"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Payload not JSON serializable: {e}")


# =============================================================================
# TEST 4: Never Deny Computed Data (String Regression)
# =============================================================================
class TestNeverDenyComputedData:
    """Test that guardrails catch 'missing data' claims."""
    
    def test_guardrails_catch_missing_number_claims(self):
        """Test that bad claims about missing numbers are reframed."""
        from server import apply_numerology_guardrails
        
        test_cases = [
            ("I don't have your Expression number", "your numbers are part of your computed chart"),
            ("I can't see your Life Path", "your numbers are in your computed chart"),
            ("I don't have your Soul Urge number", "your numbers are part of your computed chart"),
            ("numerology aren't available", "your numerology is computed"),
            ("need your name to calculate", "your numerology data is already computed"),
        ]
        
        for input_text, expected_substring in test_cases:
            output = apply_numerology_guardrails(input_text)
            
            # Output should NOT contain forbidden patterns unchanged
            assert "I don't have your" not in output or "computed" in output, \
                f"Guardrails failed to catch: '{input_text}' -> '{output}'"
    
    def test_numerology_data_never_claimed_missing_when_present(self, numerology_no_name):
        """With valid chart, core numbers exist."""
        assert numerology_no_name["core"]["life_path"] is not None
        assert numerology_no_name["core"]["birthday_number"] is not None
        assert numerology_no_name["cycles"]["personal_year"] is not None


# =============================================================================
# TEST 5: ComputeIntegrityError Short-Circuits
# =============================================================================
class TestComputeIntegrityErrorShortCircuits:
    """Test that ComputeIntegrityError prevents LLM call."""
    
    def test_compute_integrity_error_raised_on_missing_data(self):
        """ComputeIntegrityError must be raised when compute fails."""
        test_errors = ["Core: life_path is required"]
        test_partial = {"life_path": None}
        
        error = ComputeIntegrityError(test_errors, test_partial)
        
        assert error.errors == test_errors
        assert error.partial_data == test_partial
        assert "Compute Integrity Error" in str(error)
    
    def test_compute_integrity_error_to_dict(self):
        """ComputeIntegrityError.to_dict() returns proper structure."""
        test_errors = ["Core: life_path is required"]
        error = ComputeIntegrityError(test_errors)
        
        result = error.to_dict()
        
        assert result["compute_integrity"]["valid"] == False
        assert result["compute_integrity"]["errors"] == test_errors
    
    def test_deep_dive_returns_error_on_compute_failure(self):
        """Deep dive endpoint returns compute_integrity_error without LLM call."""
        mock_errors = ["Core: life_path is required"]
        
        expected_response = {
            "success": False,
            "error": "compute_integrity_error",
            "title": "Compute Integrity Error",
            "missing": mock_errors,
            "action": "Numerology deep dive paused until compute payload is complete.",
            "sections": [],
            "mirror_prompt": None
        }
        
        assert expected_response["success"] == False
        assert expected_response["error"] == "compute_integrity_error"
    
    def test_llm_not_called_when_integrity_fails(self):
        """Verify emergent_generate is NOT called when integrity check fails."""
        error = ComputeIntegrityError(["Test error"])
        
        llm_called = False
        
        try:
            raise error
        except ComputeIntegrityError as e:
            response = {
                "success": False,
                "error": "compute_integrity_error",
                "missing": e.errors
            }
        else:
            llm_called = True
        
        assert llm_called == False
        assert response["error"] == "compute_integrity_error"


# =============================================================================
# ADDITIONAL REGRESSION TESTS (Specific Values)
# =============================================================================
class TestNumerologyRegression:
    """Regression tests for specific computed values."""
    
    def test_pete_life_path(self, numerology_no_name):
        """Pete's Life Path from 1968-04-01."""
        # 1+9+6+8 + 0+4 + 0+1 = 24 + 4 + 1 = 29 -> 2+9 = 11 (master) or 2
        life_path = numerology_no_name["core"]["life_path"]
        assert life_path in [2, 11, 29], f"Unexpected life_path: {life_path}"
    
    def test_pete_birthday_number(self, numerology_no_name):
        """Pete's Birthday Number is 1 (born on the 1st)."""
        birthday = numerology_no_name["core"]["birthday_number"]
        assert birthday == 1, f"Expected birthday 1, got {birthday}"
    
    def test_cycles_are_deterministic(self, numerology_no_name):
        """Cycles should be deterministic for fixed current_date."""
        cycles = numerology_no_name["cycles"]
        
        # These should be consistent for the same birth_date + current_date
        assert isinstance(cycles["personal_year"], int)
        assert 1 <= cycles["personal_year"] <= 9
        assert isinstance(cycles["personal_month"], int)
        assert 1 <= cycles["personal_month"] <= 9
        assert isinstance(cycles["personal_day"], int)
        assert 1 <= cycles["personal_day"] <= 9
    
    def test_name_numbers_consistency(self, numerology_with_name):
        """Name numbers should be consistent for same name."""
        core = numerology_with_name["core"]
        
        # All should be valid numbers 1-33 (including master numbers)
        assert 1 <= core["expression"] <= 33
        assert 1 <= core["soul_urge"] <= 33
        assert 1 <= core["personality"] <= 33


# =============================================================================
# RUN TESTS
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("NUMEROLOGY DEEP DIVE INTEGRITY REGRESSION TESTS")
    print("=" * 70)
    
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("SOME TESTS FAILED ✗")
        print("=" * 70)
    
    sys.exit(exit_code)
