"""
Gene Keys Regression Tests
==========================
FROZEN: 2025-03-07

These tests ensure the Gene Keys sequence computation remains stable.
DO NOT modify expected values without explicit approval and version bump.

Run with: pytest backend/tests/test_gene_keys_regression.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
sys.path.insert(0, '/app/backend')

from calculations.human_design import get_human_design_chart
from calculations.gene_keys import (
    get_gene_keys_sequences,
    get_gene_keys_from_birth,
    validate_gene_keys_output,
    GENE_KEYS_VERSION,
    SEQUENCE_DEFINITIONS,
    PURPOSE_ARC,
    LOVE_ARC,
    PROSPERITY_ARC,
)


# =============================================================================
# FROZEN BENCHMARK DATA - DO NOT MODIFY
# =============================================================================

def get_utc_from_local(local_dt: datetime, utc_offset: float) -> datetime:
    """Convert local datetime to UTC given the UTC offset in hours."""
    offset = timedelta(hours=utc_offset)
    return (local_dt - offset).replace(tzinfo=timezone.utc)


# Jay - Manifesting Generator 2/4
BENCHMARK_JAY = {
    "name": "Jay",
    "birth_local": datetime(1981, 10, 12, 18, 16, 0),
    "utc_offset": 8.0,  # Singapore UTC+8
    "lat": 1.3521,
    "lon": 103.8198,
}

# Melissa - Reflector 3/5
BENCHMARK_MELISSA = {
    "name": "Melissa Tan",
    "birth_local": datetime(1981, 7, 13, 7, 25, 0),
    "utc_offset": 8.0,  # Malaysia UTC+8
    "lat": 2.1896,
    "lon": 102.2501,
}

# Pete - Manifestor 5/1
BENCHMARK_PETE = {
    "name": "Pete",
    "birth_local": datetime(1968, 4, 1, 1, 25, 0),
    "utc_offset": 7.5,  # Malaysia historical UTC+7:30
    "lat": 3.1073,
    "lon": 101.6070,
}


class TestGeneKeysVersion:
    """Test version and structure."""
    
    def test_version_constant(self):
        """Version should be gk_sidereal_v1."""
        assert GENE_KEYS_VERSION == "gk_sidereal_v1"
    
    def test_sequence_definitions_complete(self):
        """All 13 sequence positions should be defined."""
        expected_positions = [
            # Purpose Arc
            "lifes_work", "evolution", "radiance", "purpose",
            # Love Arc
            "attraction", "iq", "eq", "sq", "core_wound",
            # Prosperity Arc
            "brand", "culture", "vocation", "pearl",
        ]
        for pos in expected_positions:
            assert pos in SEQUENCE_DEFINITIONS, f"Missing sequence: {pos}"
    
    def test_arc_groupings(self):
        """Arc groupings should be correct."""
        assert PURPOSE_ARC == ["lifes_work", "evolution", "radiance", "purpose"]
        assert LOVE_ARC == ["attraction", "iq", "eq", "sq", "core_wound"]
        assert PROSPERITY_ARC == ["brand", "culture", "vocation", "pearl"]


class TestJayGeneKeys:
    """Regression tests for Jay's Gene Keys sequences."""
    
    @pytest.fixture
    def jay_gk(self):
        birth_utc = get_utc_from_local(
            BENCHMARK_JAY["birth_local"],
            BENCHMARK_JAY["utc_offset"]
        )
        hd_chart = get_human_design_chart(
            birth_utc,
            BENCHMARK_JAY["lat"],
            BENCHMARK_JAY["lon"]
        )
        return get_gene_keys_sequences(hd_chart)
    
    def test_version(self, jay_gk):
        """Should return correct version."""
        assert jay_gk["gene_keys_version"] == GENE_KEYS_VERSION
    
    def test_structure(self, jay_gk):
        """Should have all arcs and all_sequences."""
        assert "purpose_arc" in jay_gk
        assert "love_arc" in jay_gk
        assert "prosperity_arc" in jay_gk
        assert "all_sequences" in jay_gk
    
    def test_purpose_arc_count(self, jay_gk):
        """Purpose arc should have 4 positions."""
        assert len(jay_gk["purpose_arc"]) == 4
    
    def test_love_arc_count(self, jay_gk):
        """Love arc should have 5 positions."""
        assert len(jay_gk["love_arc"]) == 5
    
    def test_prosperity_arc_count(self, jay_gk):
        """Prosperity arc should have 4 positions."""
        assert len(jay_gk["prosperity_arc"]) == 4
    
    def test_all_sequences_count(self, jay_gk):
        """All sequences should have 13 positions."""
        assert len(jay_gk["all_sequences"]) == 13
    
    def test_lifes_work_structure(self, jay_gk):
        """Life's Work should have correct structure."""
        lw = jay_gk["all_sequences"]["lifes_work"]
        assert "gate" in lw
        assert "line" in lw
        assert lw["source_planet"] == "Sun"
        assert lw["source_chart"] == "personality"
        assert 1 <= lw["gate"] <= 64
        assert 1 <= lw["line"] <= 6
    
    def test_validation_passes(self, jay_gk):
        """Validation should pass for Jay."""
        errors = validate_gene_keys_output(jay_gk)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    # FROZEN VALUES - Jay's Gene Keys
    def test_lifes_work_gate(self, jay_gk):
        """Jay's Life's Work gate (personality Sun)."""
        assert jay_gk["all_sequences"]["lifes_work"]["gate"] == 47
    
    def test_evolution_gate(self, jay_gk):
        """Jay's Evolution gate (personality Earth)."""
        assert jay_gk["all_sequences"]["evolution"]["gate"] == 22


class TestMelissaGeneKeys:
    """Regression tests for Melissa's Gene Keys sequences."""
    
    @pytest.fixture
    def melissa_gk(self):
        birth_utc = get_utc_from_local(
            BENCHMARK_MELISSA["birth_local"],
            BENCHMARK_MELISSA["utc_offset"]
        )
        hd_chart = get_human_design_chart(
            birth_utc,
            BENCHMARK_MELISSA["lat"],
            BENCHMARK_MELISSA["lon"]
        )
        return get_gene_keys_sequences(hd_chart)
    
    def test_version(self, melissa_gk):
        """Should return correct version."""
        assert melissa_gk["gene_keys_version"] == GENE_KEYS_VERSION
    
    def test_all_sequences_count(self, melissa_gk):
        """All sequences should have 13 positions."""
        assert len(melissa_gk["all_sequences"]) == 13
    
    def test_validation_passes(self, melissa_gk):
        """Validation should pass for Melissa."""
        errors = validate_gene_keys_output(melissa_gk)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    # FROZEN VALUES - Melissa's Gene Keys (Reflector)
    def test_lifes_work_gate(self, melissa_gk):
        """Melissa's Life's Work gate (personality Sun)."""
        assert melissa_gk["all_sequences"]["lifes_work"]["gate"] == 45
    
    def test_evolution_gate(self, melissa_gk):
        """Melissa's Evolution gate (personality Earth)."""
        assert melissa_gk["all_sequences"]["evolution"]["gate"] == 26


class TestPeteGeneKeys:
    """Regression tests for Pete's Gene Keys sequences."""
    
    @pytest.fixture
    def pete_gk(self):
        birth_utc = get_utc_from_local(
            BENCHMARK_PETE["birth_local"],
            BENCHMARK_PETE["utc_offset"]
        )
        hd_chart = get_human_design_chart(
            birth_utc,
            BENCHMARK_PETE["lat"],
            BENCHMARK_PETE["lon"]
        )
        return get_gene_keys_sequences(hd_chart)
    
    def test_version(self, pete_gk):
        """Should return correct version."""
        assert pete_gk["gene_keys_version"] == GENE_KEYS_VERSION
    
    def test_all_sequences_count(self, pete_gk):
        """All sequences should have 13 positions."""
        assert len(pete_gk["all_sequences"]) == 13
    
    def test_validation_passes(self, pete_gk):
        """Validation should pass for Pete."""
        errors = validate_gene_keys_output(pete_gk)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    # FROZEN VALUES - Pete's Gene Keys (Manifestor)
    def test_lifes_work_gate(self, pete_gk):
        """Pete's Life's Work gate (personality Sun)."""
        assert pete_gk["all_sequences"]["lifes_work"]["gate"] == 37
    
    def test_evolution_gate(self, pete_gk):
        """Pete's Evolution gate (personality Earth)."""
        assert pete_gk["all_sequences"]["evolution"]["gate"] == 40


class TestSequenceMappings:
    """Test that sequence mappings are correct."""
    
    def test_purpose_arc_mappings(self):
        """Purpose Arc planets should be correct."""
        assert SEQUENCE_DEFINITIONS["lifes_work"] == ("Sun", "personality")
        assert SEQUENCE_DEFINITIONS["evolution"] == ("Earth", "personality")
        assert SEQUENCE_DEFINITIONS["radiance"] == ("Sun", "design")
        assert SEQUENCE_DEFINITIONS["purpose"] == ("Earth", "design")
    
    def test_love_arc_mappings(self):
        """Love Arc planets should be correct."""
        assert SEQUENCE_DEFINITIONS["attraction"] == ("Venus", "design")
        assert SEQUENCE_DEFINITIONS["iq"] == ("Mercury", "personality")
        assert SEQUENCE_DEFINITIONS["eq"] == ("Venus", "personality")
        assert SEQUENCE_DEFINITIONS["sq"] == ("Moon", "design")
        assert SEQUENCE_DEFINITIONS["core_wound"] == ("Mars", "design")
    
    def test_prosperity_arc_mappings(self):
        """Prosperity Arc planets should be correct."""
        assert SEQUENCE_DEFINITIONS["brand"] == ("Sun", "personality")
        assert SEQUENCE_DEFINITIONS["culture"] == ("Jupiter", "design")
        assert SEQUENCE_DEFINITIONS["vocation"] == ("Mars", "design")
        assert SEQUENCE_DEFINITIONS["pearl"] == ("Jupiter", "personality")
    
    def test_brand_equals_lifes_work(self):
        """Brand should use same planet as Life's Work."""
        assert SEQUENCE_DEFINITIONS["brand"] == SEQUENCE_DEFINITIONS["lifes_work"]
    
    def test_vocation_equals_core_wound(self):
        """Vocation should use same planet as Core Wound."""
        assert SEQUENCE_DEFINITIONS["vocation"] == SEQUENCE_DEFINITIONS["core_wound"]


class TestConvenienceFunction:
    """Test get_gene_keys_from_birth convenience function."""
    
    def test_from_birth_returns_sequences(self):
        """Should return Gene Keys directly from birth data."""
        birth_utc = get_utc_from_local(
            BENCHMARK_JAY["birth_local"],
            BENCHMARK_JAY["utc_offset"]
        )
        gk = get_gene_keys_from_birth(
            birth_utc,
            BENCHMARK_JAY["lat"],
            BENCHMARK_JAY["lon"]
        )
        
        assert gk["gene_keys_version"] == GENE_KEYS_VERSION
        assert "purpose_arc" in gk
        assert "hd_metadata" in gk
    
    def test_from_birth_includes_hd_metadata(self):
        """Should include HD metadata for reference."""
        birth_utc = get_utc_from_local(
            BENCHMARK_JAY["birth_local"],
            BENCHMARK_JAY["utc_offset"]
        )
        gk = get_gene_keys_from_birth(
            birth_utc,
            BENCHMARK_JAY["lat"],
            BENCHMARK_JAY["lon"]
        )
        
        meta = gk["hd_metadata"]
        assert meta["computation_version"] == "mirror_compute_v1"
        assert meta["human_design_version"] == "hd_sidereal_v1"
        assert meta["type"] == "Manifesting Generator"
        assert meta["profile"] == "2/4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
