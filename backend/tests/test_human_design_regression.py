"""
Human Design Regression Tests
=============================
FROZEN: 2025-03-07

These tests ensure the Human Design computation logic remains stable.
DO NOT modify expected values without explicit approval and version bump.

Run with: pytest backend/tests/test_human_design_regression.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
sys.path.insert(0, '/app/backend')

from calculations.human_design import get_human_design_chart


# =============================================================================
# FROZEN BENCHMARK DATA - DO NOT MODIFY
# =============================================================================

BENCHMARK_JAY = {
    "name": "Jay",
    "birth_local": datetime(1981, 10, 12, 18, 16, 0),
    "utc_offset": 8.0,  # Singapore UTC+8
    "lat": 1.3521,
    "lon": 103.8198,
    "expected": {
        "type": "Manifesting Generator",
        "profile": "2/4",
        "definition": "Triple Split",
        "authority": "Emotional",
        "defined_centers": ["Head", "Ajna", "Throat", "Sacral", "Ego", "Solar Plexus", "Spleen"],
        "channels": ["64-47", "59-6", "12-22", "44-26"],
    }
}

BENCHMARK_MELISSA = {
    "name": "Melissa Tan",
    "birth_local": datetime(1981, 7, 13, 7, 25, 0),
    "utc_offset": 8.0,  # Malaysia UTC+8
    "lat": 2.1896,
    "lon": 102.2501,
    "expected": {
        "type": "Reflector",
        "profile": "3/5",
        "definition": "No Definition",
        "authority": "Lunar",
        "defined_centers": [],
        "channels": [],
    }
}

BENCHMARK_PETE = {
    "name": "Pete",
    "birth_local": datetime(1968, 4, 1, 1, 25, 0),
    "utc_offset": 7.5,  # Malaysia historical UTC+7:30
    "lat": 3.1073,
    "lon": 101.6070,
    "expected": {
        "type": "Manifestor",
        "profile": "5/1",
        "definition": "Split",
        "authority": "Emotional",
        "defined_centers": ["Head", "Ajna", "Throat", "Ego", "Solar Plexus"],
        "channels": ["63-4", "35-36", "37-40"],
    }
}


def get_utc_from_local(local_dt: datetime, utc_offset: float) -> datetime:
    """Convert local datetime to UTC given the UTC offset in hours."""
    offset = timedelta(hours=utc_offset)
    return (local_dt - offset).replace(tzinfo=timezone.utc)


class TestJayRegression:
    """Regression tests for Jay's Human Design chart."""
    
    @pytest.fixture
    def jay_chart(self):
        birth_utc = get_utc_from_local(
            BENCHMARK_JAY["birth_local"],
            BENCHMARK_JAY["utc_offset"]
        )
        return get_human_design_chart(
            birth_utc,
            BENCHMARK_JAY["lat"],
            BENCHMARK_JAY["lon"]
        )
    
    def test_type(self, jay_chart):
        """Jay should be a Manifesting Generator."""
        assert jay_chart["type"] == BENCHMARK_JAY["expected"]["type"]
    
    def test_profile(self, jay_chart):
        """Jay should have profile 2/4."""
        assert jay_chart["profile"] == BENCHMARK_JAY["expected"]["profile"]
    
    def test_definition(self, jay_chart):
        """Jay should have Triple Split definition."""
        assert jay_chart["definition"] == BENCHMARK_JAY["expected"]["definition"]
    
    def test_authority(self, jay_chart):
        """Jay should have Emotional authority."""
        assert jay_chart["authority"] == BENCHMARK_JAY["expected"]["authority"]
    
    def test_defined_centers(self, jay_chart):
        """Jay should have 7 defined centers."""
        expected_centers = set(BENCHMARK_JAY["expected"]["defined_centers"])
        actual_centers = set(jay_chart["defined_centers"])
        assert expected_centers == actual_centers
    
    def test_channels(self, jay_chart):
        """Jay should have 4 defined channels."""
        expected_channels = set(BENCHMARK_JAY["expected"]["channels"])
        actual_channels = set(f"{ch['gate1']}-{ch['gate2']}" for ch in jay_chart["defined_channels"])
        assert expected_channels == actual_channels
    
    def test_version_fields(self, jay_chart):
        """Chart should include version metadata."""
        assert jay_chart["computation_version"] == "mirror_compute_v1"
        assert jay_chart["astronomy_version"] == "true_sidereal_m_swe_v1"
        assert jay_chart["human_design_version"] == "hd_sidereal_v1"


class TestMelissaRegression:
    """Regression tests for Melissa's Human Design chart."""
    
    @pytest.fixture
    def melissa_chart(self):
        birth_utc = get_utc_from_local(
            BENCHMARK_MELISSA["birth_local"],
            BENCHMARK_MELISSA["utc_offset"]
        )
        return get_human_design_chart(
            birth_utc,
            BENCHMARK_MELISSA["lat"],
            BENCHMARK_MELISSA["lon"]
        )
    
    def test_type(self, melissa_chart):
        """Melissa should be a Reflector."""
        assert melissa_chart["type"] == BENCHMARK_MELISSA["expected"]["type"]
    
    def test_profile(self, melissa_chart):
        """Melissa should have profile 3/5."""
        assert melissa_chart["profile"] == BENCHMARK_MELISSA["expected"]["profile"]
    
    def test_definition(self, melissa_chart):
        """Melissa should have No Definition (Reflector)."""
        assert melissa_chart["definition"] == BENCHMARK_MELISSA["expected"]["definition"]
    
    def test_authority(self, melissa_chart):
        """Melissa should have Lunar authority."""
        assert melissa_chart["authority"] == BENCHMARK_MELISSA["expected"]["authority"]
    
    def test_defined_centers(self, melissa_chart):
        """Melissa should have 0 defined centers."""
        assert len(melissa_chart["defined_centers"]) == 0
    
    def test_channels(self, melissa_chart):
        """Melissa should have 0 defined channels."""
        assert len(melissa_chart["defined_channels"]) == 0


class TestPeteRegression:
    """Regression tests for Pete's Human Design chart."""
    
    @pytest.fixture
    def pete_chart(self):
        birth_utc = get_utc_from_local(
            BENCHMARK_PETE["birth_local"],
            BENCHMARK_PETE["utc_offset"]
        )
        return get_human_design_chart(
            birth_utc,
            BENCHMARK_PETE["lat"],
            BENCHMARK_PETE["lon"]
        )
    
    def test_type(self, pete_chart):
        """Pete should be a Manifestor."""
        assert pete_chart["type"] == BENCHMARK_PETE["expected"]["type"]
    
    def test_profile(self, pete_chart):
        """Pete should have profile 5/1."""
        assert pete_chart["profile"] == BENCHMARK_PETE["expected"]["profile"]
    
    def test_definition(self, pete_chart):
        """Pete should have Split definition."""
        assert pete_chart["definition"] == BENCHMARK_PETE["expected"]["definition"]
    
    def test_authority(self, pete_chart):
        """Pete should have Emotional authority."""
        assert pete_chart["authority"] == BENCHMARK_PETE["expected"]["authority"]
    
    def test_defined_centers(self, pete_chart):
        """Pete should have 5 defined centers."""
        expected_centers = set(BENCHMARK_PETE["expected"]["defined_centers"])
        actual_centers = set(pete_chart["defined_centers"])
        assert expected_centers == actual_centers
    
    def test_channels(self, pete_chart):
        """Pete should have 3 defined channels."""
        expected_channels = set(BENCHMARK_PETE["expected"]["channels"])
        actual_channels = set(f"{ch['gate1']}-{ch['gate2']}" for ch in pete_chart["defined_channels"])
        assert expected_channels == actual_channels


class TestCanonicalLabels:
    """Tests to ensure canonical labels are used."""
    
    def test_valid_type_labels(self):
        """All types should use canonical labels."""
        valid_types = {"Reflector", "Projector", "Manifestor", "Generator", "Manifesting Generator"}
        
        for benchmark in [BENCHMARK_JAY, BENCHMARK_MELISSA, BENCHMARK_PETE]:
            birth_utc = get_utc_from_local(benchmark["birth_local"], benchmark["utc_offset"])
            chart = get_human_design_chart(birth_utc, benchmark["lat"], benchmark["lon"])
            assert chart["type"] in valid_types, f"Invalid type: {chart['type']}"
    
    def test_valid_authority_labels(self):
        """All authorities should use canonical labels."""
        valid_authorities = {"Lunar", "Emotional", "Sacral", "Splenic", "Ego", "Self", "None"}
        
        for benchmark in [BENCHMARK_JAY, BENCHMARK_MELISSA, BENCHMARK_PETE]:
            birth_utc = get_utc_from_local(benchmark["birth_local"], benchmark["utc_offset"])
            chart = get_human_design_chart(birth_utc, benchmark["lat"], benchmark["lon"])
            assert chart["authority"] in valid_authorities, f"Invalid authority: {chart['authority']}"
    
    def test_valid_definition_labels(self):
        """All definitions should use canonical labels."""
        valid_definitions = {"No Definition", "Single", "Split", "Triple Split", "Quadruple Split"}
        
        for benchmark in [BENCHMARK_JAY, BENCHMARK_MELISSA, BENCHMARK_PETE]:
            birth_utc = get_utc_from_local(benchmark["birth_local"], benchmark["utc_offset"])
            chart = get_human_design_chart(birth_utc, benchmark["lat"], benchmark["lon"])
            assert chart["definition"] in valid_definitions, f"Invalid definition: {chart['definition']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
