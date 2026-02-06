"""
===============================================================================
REGRESSION TEST: Symbolic Compute Contract — Global Interface Tests
===============================================================================
This test suite ensures all symbolic systems conform to the unified contract:
- Deterministic completeness
- Predictable LLM handoff
- Identical failure behavior
- Zero "missing data" hallucinations

CORE PRINCIPLE:
    Interpretation is optional.
    Computation is not.
    Integrity is non-negotiable.

To run: 
    python -m pytest tests/test_symbolic_compute_contract.py -v
===============================================================================
"""
import sys
import os
import pytest
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.symbolic_compute_contract import (
    ComputeIntegrityError,
    ComputeIntegrityResult,
    SymbolicPayload,
    assert_handoff_ready,
    validate_handoff,
    check_forbidden_language,
    get_contract_info,
    ASTROLOGY_REQUIRED_KEYS,
    HUMAN_DESIGN_REQUIRED_KEYS,
    NUMEROLOGY_REQUIRED_KEYS,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================
PETE_BIRTH_UTC = datetime(1968, 3, 31, 17, 55, 0)
PETE_LAT = 3.1073
PETE_LON = 101.6070


# =============================================================================
# TEST 1: ComputeIntegrityError (Shared Exception)
# =============================================================================
class TestComputeIntegrityError:
    """Test the shared ComputeIntegrityError exception."""
    
    def test_error_creation(self):
        """Error can be created with errors list."""
        error = ComputeIntegrityError(["Test error 1", "Test error 2"])
        assert error.errors == ["Test error 1", "Test error 2"]
        assert "Compute Integrity Error" in str(error)
    
    def test_error_with_partial_data(self):
        """Error can include partial data for debugging."""
        partial = {"key": "value"}
        error = ComputeIntegrityError(["Test error"], partial_data=partial)
        assert error.partial_data == partial
    
    def test_error_with_system(self):
        """Error includes system name."""
        error = ComputeIntegrityError(["Test error"], system="astrology")
        assert error.system == "astrology"
        assert "astrology" in str(error)
    
    def test_to_dict(self):
        """to_dict() returns proper structure."""
        error = ComputeIntegrityError(["Error 1", "Error 2"], system="numerology")
        result = error.to_dict()
        
        assert result["system"] == "numerology"
        assert result["compute_integrity"]["valid"] == False
        assert result["compute_integrity"]["errors"] == ["Error 1", "Error 2"]
        assert result["compute_integrity"]["error_count"] == 2
    
    def test_to_api_response(self):
        """to_api_response() returns API-friendly format."""
        error = ComputeIntegrityError(["Missing field"], system="human_design")
        response = error.to_api_response()
        
        assert response["success"] == False
        assert response["error"] == "compute_integrity_error"
        assert response["system"] == "human_design"
        assert response["missing"] == ["Missing field"]


# =============================================================================
# TEST 2: SymbolicPayload (Canonical Wrapper)
# =============================================================================
class TestSymbolicPayload:
    """Test the SymbolicPayload wrapper class."""
    
    def test_payload_creation(self):
        """Payload can be created with required fields."""
        payload = SymbolicPayload(
            system="astrology",
            canonical_payload={"planets": {}, "nodes": {}},
            inputs={"birth_date": "1968-04-01"}
        )
        
        assert payload.system == "astrology"
        assert payload.version == "v1"
        assert payload.is_valid() == True
    
    def test_payload_to_dict(self):
        """to_dict() returns proper structure."""
        payload = SymbolicPayload(
            system="numerology",
            canonical_payload={"life_path": 11},
            inputs={"birth_date": "1968-04-01"}
        )
        
        result = payload.to_dict()
        
        assert result["system"] == "numerology"
        assert "metadata" in result
        assert result["metadata"]["version"] == "v1"
        assert "inputs_hash" in result["metadata"]
        assert "canonical_payload" in result
    
    def test_payload_inputs_hash(self):
        """Inputs hash is deterministic."""
        payload1 = SymbolicPayload(
            system="astrology",
            canonical_payload={},
            inputs={"birth_date": "1968-04-01", "lat": 3.1073}
        )
        payload2 = SymbolicPayload(
            system="astrology",
            canonical_payload={},
            inputs={"birth_date": "1968-04-01", "lat": 3.1073}
        )
        
        assert payload1.inputs_hash == payload2.inputs_hash
    
    def test_payload_with_invalid_integrity(self):
        """Payload can be created with invalid integrity."""
        payload = SymbolicPayload(
            system="astrology",
            canonical_payload={},
            compute_integrity=ComputeIntegrityResult(
                valid=False,
                missing=["planets", "nodes"]
            )
        )
        
        assert payload.is_valid() == False
    
    def test_assert_valid_raises_on_invalid(self):
        """assert_valid() raises ComputeIntegrityError when invalid."""
        payload = SymbolicPayload(
            system="astrology",
            canonical_payload={},
            compute_integrity=ComputeIntegrityResult(
                valid=False,
                missing=["planets missing"]
            )
        )
        
        with pytest.raises(ComputeIntegrityError) as exc_info:
            payload.assert_valid()
        
        assert "planets missing" in exc_info.value.errors


# =============================================================================
# TEST 3: LLM Handoff Validation
# =============================================================================
class TestLLMHandoffValidation:
    """Test LLM handoff validation functions."""
    
    def test_assert_handoff_ready_passes_valid(self):
        """assert_handoff_ready() passes for valid payload."""
        payload = SymbolicPayload(
            system="astrology",
            canonical_payload={"planets": {}, "nodes": {}},
            compute_integrity=ComputeIntegrityResult(valid=True)
        )
        
        result = assert_handoff_ready(payload)
        assert result == True
    
    def test_assert_handoff_ready_raises_invalid(self):
        """assert_handoff_ready() raises for invalid payload."""
        payload = SymbolicPayload(
            system="astrology",
            canonical_payload={},
            compute_integrity=ComputeIntegrityResult(
                valid=False,
                missing=["nodes missing"]
            )
        )
        
        with pytest.raises(ComputeIntegrityError):
            assert_handoff_ready(payload)
    
    def test_validate_handoff_dict(self):
        """validate_handoff() works with raw dicts."""
        payload_dict = {
            "compute_integrity": {"valid": True}
        }
        
        result = validate_handoff(payload_dict, "astrology")
        assert result == True
    
    def test_validate_handoff_dict_invalid(self):
        """validate_handoff() raises for invalid dicts."""
        payload_dict = {
            "compute_integrity": {"valid": False, "missing": ["error"]}
        }
        
        with pytest.raises(ComputeIntegrityError):
            validate_handoff(payload_dict, "astrology")


# =============================================================================
# TEST 4: Forbidden Language Detection
# =============================================================================
class TestForbiddenLanguage:
    """Test detection of forbidden language patterns."""
    
    def test_detects_missing_data_claims(self):
        """Detects claims about missing data."""
        text = "I don't have your birth date information."
        found = check_forbidden_language(text)
        assert len(found) > 0
    
    def test_detects_cant_see_claims(self):
        """Detects 'can't see' patterns."""
        text = "I can't see your nodes in the chart."
        found = check_forbidden_language(text)
        assert len(found) > 0
    
    def test_detects_request_for_data(self):
        """Detects requests for already-computed data."""
        text = "Please provide your birth time so I can calculate."
        found = check_forbidden_language(text)
        assert len(found) > 0
    
    def test_clean_text_passes(self):
        """Clean text has no forbidden patterns."""
        text = "Your chart shows Sun in Pisces with a night sect emphasis."
        found = check_forbidden_language(text)
        assert len(found) == 0


# =============================================================================
# TEST 5: Required Keys By System
# =============================================================================
class TestRequiredKeys:
    """Test required keys are properly defined for each system."""
    
    def test_astrology_required_keys(self):
        """Astrology has all required keys defined."""
        required = ASTROLOGY_REQUIRED_KEYS
        
        assert "planets" in required
        assert "nodes" in required
        assert "angles" in required
        assert "houses" in required
        assert "aspects" in required
        assert "sect" in required
        assert "compute_integrity" in required
    
    def test_human_design_required_keys(self):
        """Human Design has all required keys defined."""
        required = HUMAN_DESIGN_REQUIRED_KEYS
        
        assert "type" in required
        assert "strategy" in required
        assert "authority" in required
        assert "profile" in required
        assert "definition" in required
        assert "incarnation_cross" in required
        assert "defined_centers" in required
        assert "compute_integrity" in required
    
    def test_numerology_required_keys(self):
        """Numerology has all required keys defined."""
        required = NUMEROLOGY_REQUIRED_KEYS
        
        assert "core" in required
        assert "cycles" in required
        assert "inputs" in required
        assert "compute_integrity" in required


# =============================================================================
# TEST 6: Contract Info
# =============================================================================
class TestContractInfo:
    """Test contract version and metadata."""
    
    def test_get_contract_info(self):
        """get_contract_info() returns proper structure."""
        info = get_contract_info()
        
        assert "version" in info
        assert "last_updated" in info
        assert "required_keys" in info
        assert "astrology" in info["required_keys"]
        assert "human_design" in info["required_keys"]
        assert "numerology" in info["required_keys"]


# =============================================================================
# TEST 7: Cross-System Integration (All Systems Work)
# =============================================================================
class TestCrossSystemIntegration:
    """Test that all symbolic systems work with the shared contract."""
    
    def test_astrology_uses_shared_error(self):
        """Astrology uses the shared ComputeIntegrityError."""
        from calculations.astrology import get_full_natal_chart
        
        # Should work without raising
        chart = get_full_natal_chart(
            birth_datetime=PETE_BIRTH_UTC,
            lat=PETE_LAT,
            lon=PETE_LON
        )
        
        assert chart.get("compute_integrity", {}).get("valid") == True
    
    def test_human_design_uses_shared_error(self):
        """Human Design uses the shared ComputeIntegrityError."""
        from calculations.human_design import get_human_design_chart
        
        chart = get_human_design_chart(
            birth_datetime=PETE_BIRTH_UTC,
            lat=PETE_LAT,
            lon=PETE_LON
        )
        
        assert chart.get("compute_integrity", {}).get("valid") == True
    
    def test_numerology_uses_shared_error(self):
        """Numerology uses the shared ComputeIntegrityError."""
        from calculations.numerology import get_canonical_numerology
        
        result = get_canonical_numerology(
            birth_date=datetime(1968, 4, 1)
        )
        
        assert result.get("compute_integrity", {}).get("valid") == True


# =============================================================================
# TEST 8: Regression Guarantee (All Systems Have Tests)
# =============================================================================
class TestRegressionGuarantee:
    """Ensure all symbolic systems have required test coverage."""
    
    def test_astrology_test_file_exists(self):
        """Astrology has regression test file."""
        test_file = os.path.join(
            os.path.dirname(__file__),
            "test_astrology_deep_dive_integrity.py"
        )
        assert os.path.exists(test_file), "Astrology regression tests missing"
    
    def test_human_design_test_file_exists(self):
        """Human Design has regression test file."""
        test_file = os.path.join(
            os.path.dirname(__file__),
            "test_human_design_deep_dive_integrity.py"
        )
        assert os.path.exists(test_file), "Human Design regression tests missing"
    
    def test_numerology_test_file_exists(self):
        """Numerology has regression test file."""
        test_file = os.path.join(
            os.path.dirname(__file__),
            "test_numerology_deep_dive_integrity.py"
        )
        assert os.path.exists(test_file), "Numerology regression tests missing"


# =============================================================================
# RUN TESTS
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("SYMBOLIC COMPUTE CONTRACT — GLOBAL INTERFACE TESTS")
    print("=" * 70)
    
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("ALL CONTRACT TESTS PASSED ✓")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("SOME CONTRACT TESTS FAILED ✗")
        print("=" * 70)
    
    sys.exit(exit_code)
