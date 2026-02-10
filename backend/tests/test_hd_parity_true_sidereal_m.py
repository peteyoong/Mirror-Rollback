#!/usr/bin/env python3
"""
Human Design Parity Regression Tests - True Sidereal-M / Midpoint
==================================================================
Golden fixtures locked against Genetic Matrix (True Sidereal-M) settings.

These tests ensure:
1. Settings hash matches expected configuration
2. All 13 planetary gate.line values match fixtures
3. Type, authority, profile, definition match fixtures
4. Incarnation cross angle + gates_key match fixtures
5. Channels match fixtures
6. Deterministic idempotency (compute twice yields same results)

DO NOT modify fixtures without re-validating against reference tool.
"""

import sys
sys.path.insert(0, '/app/backend')

import json
import hashlib
import pytest
from datetime import datetime, timezone
from pathlib import Path

from calculations.human_design import get_human_design_chart

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

SIDEREAL_SETTINGS = {
    "mode": "true_sidereal_user_defined",
    "svp_degrees": 31.2836,
    "reference_year": 2000,
    "yearly_increment": 0.0,
    "nodes": "true_nodes",
    "house_system": "equal",
    "hd_mode": "midpoint"
}

EXPECTED_SETTINGS_HASH = "b5f3b052f5454f56"

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "hd"

TEST_USERS = [
    {
        "name": "Nattalia C",
        "fixture": "nattalia_true_sidereal_m.json",
        "birth_utc": datetime(1982, 5, 4, 10, 0, tzinfo=timezone.utc),
        "lat": -7.0959,
        "lon": 112.348
    },
    {
        "name": "Pete Y",
        "fixture": "pete_true_sidereal_m.json",
        "birth_utc": datetime(1968, 3, 31, 17, 55, tzinfo=timezone.utc),
        "lat": 3.1073,
        "lon": 101.607
    },
    {
        "name": "Melisa T",
        "fixture": "mel_true_sidereal_m.json",
        "birth_utc": datetime(1981, 7, 12, 23, 55, tzinfo=timezone.utc),
        "lat": 2.1889,
        "lon": 102.251
    }
]

PLANET_ORDER = [
    'Sun', 'Earth', 'North Node', 'South Node', 'Moon',
    'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
    'Uranus', 'Neptune', 'Pluto'
]


def compute_settings_hash(settings: dict) -> str:
    """Compute deterministic hash of settings"""
    canonical = json.dumps(settings, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def load_fixture(fixture_name: str) -> dict:
    """Load golden fixture from JSON file"""
    fixture_path = FIXTURE_DIR / fixture_name
    with open(fixture_path, 'r') as f:
        return json.load(f)


# =============================================================================
# SETTINGS HASH TEST
# =============================================================================

class TestSettingsIntegrity:
    """Verify settings configuration matches expected hash"""
    
    def test_settings_hash_matches(self):
        """Settings hash must match expected value to ensure consistent computation"""
        computed_hash = compute_settings_hash(SIDEREAL_SETTINGS)
        assert computed_hash == EXPECTED_SETTINGS_HASH, \
            f"Settings hash mismatch: {computed_hash} != {EXPECTED_SETTINGS_HASH}"
    
    def test_svp_degrees_locked(self):
        """SVP must be locked at 31.2836° for True Sidereal-M"""
        assert SIDEREAL_SETTINGS["svp_degrees"] == 31.2836
    
    def test_yearly_increment_zero(self):
        """Yearly increment must be 0 for stable computations"""
        assert SIDEREAL_SETTINGS["yearly_increment"] == 0.0


# =============================================================================
# NATTALIA C TESTS
# =============================================================================

class TestNattaliaC:
    """Regression tests for Nattalia C - JXP Tension"""
    
    @pytest.fixture
    def fixture(self):
        return load_fixture("nattalia_true_sidereal_m.json")
    
    @pytest.fixture
    def computed(self):
        user = TEST_USERS[0]
        return get_human_design_chart(
            user['birth_utc'],
            user['lat'],
            user['lon'],
            SIDEREAL_SETTINGS
        )
    
    def test_type_matches(self, fixture, computed):
        """Type must match fixture"""
        assert computed['type'] == fixture['core_attributes']['type']
    
    def test_authority_matches(self, fixture, computed):
        """Authority must match fixture"""
        assert computed['authority'] == fixture['core_attributes']['authority']
    
    def test_profile_matches(self, fixture, computed):
        """Profile must match fixture"""
        assert computed['profile'] == fixture['core_attributes']['profile']
    
    def test_definition_matches(self, fixture, computed):
        """Definition must match fixture"""
        assert computed['definition'] == fixture['core_attributes']['definition']
    
    def test_cross_angle_matches(self, fixture, computed):
        """Incarnation cross angle must match fixture (JXP for profile 4/X)"""
        assert computed['incarnation_cross']['angle'] == fixture['incarnation_cross']['angle']
        # Critical: Nattalia must be JXP (profile line 4)
        assert computed['incarnation_cross']['angle'] == 'JXP'
    
    def test_cross_gates_key_matches(self, fixture, computed):
        """Cross gates_key must match fixture"""
        assert computed['incarnation_cross']['gates_key'] == fixture['incarnation_cross']['gates_key']
    
    def test_cross_canonical_key_matches(self, fixture, computed):
        """Cross canonical_key must match fixture"""
        assert computed['incarnation_cross']['canonical_key'] == fixture['incarnation_cross']['canonical_key']
    
    def test_channels_match(self, fixture, computed):
        """Defined channels must match fixture"""
        computed_channels = sorted([f"{ch['gate1']}-{ch['gate2']}" for ch in computed['defined_channels']])
        expected_channels = sorted(fixture['channels']['list'])
        assert computed_channels == expected_channels
    
    def test_defined_centers_match(self, fixture, computed):
        """Defined centers must match fixture"""
        assert sorted(computed['defined_centers']) == sorted(fixture['centers']['defined'])
    
    def test_personality_activations_match(self, fixture, computed):
        """All 13 personality planet activations must match fixture"""
        for planet in PLANET_ORDER:
            expected = fixture['planetary_activations']['personality'][planet]['gate_line']
            p_data = computed['personality'].get(planet, {})
            gate_info = p_data.get('gate', {})
            actual = f"{gate_info.get('gate')}.{gate_info.get('line')}"
            assert actual == expected, f"Personality {planet}: {actual} != {expected}"
    
    def test_design_activations_match(self, fixture, computed):
        """All 13 design planet activations must match fixture"""
        for planet in PLANET_ORDER:
            expected = fixture['planetary_activations']['design'][planet]['gate_line']
            d_data = computed['design'].get(planet, {})
            gate_info = d_data.get('gate', {})
            actual = f"{gate_info.get('gate')}.{gate_info.get('line')}"
            assert actual == expected, f"Design {planet}: {actual} != {expected}"


# =============================================================================
# PETE Y TESTS
# =============================================================================

class TestPeteY:
    """Regression tests for Pete Y - LAX Migration"""
    
    @pytest.fixture
    def fixture(self):
        return load_fixture("pete_true_sidereal_m.json")
    
    @pytest.fixture
    def computed(self):
        user = TEST_USERS[1]
        return get_human_design_chart(
            user['birth_utc'],
            user['lat'],
            user['lon'],
            SIDEREAL_SETTINGS
        )
    
    def test_type_matches(self, fixture, computed):
        assert computed['type'] == fixture['core_attributes']['type']
    
    def test_authority_matches(self, fixture, computed):
        assert computed['authority'] == fixture['core_attributes']['authority']
    
    def test_profile_matches(self, fixture, computed):
        assert computed['profile'] == fixture['core_attributes']['profile']
    
    def test_definition_matches(self, fixture, computed):
        assert computed['definition'] == fixture['core_attributes']['definition']
    
    def test_cross_angle_matches(self, fixture, computed):
        """Pete must be LAX (profile line 5)"""
        assert computed['incarnation_cross']['angle'] == fixture['incarnation_cross']['angle']
        assert computed['incarnation_cross']['angle'] == 'LAX'
    
    def test_cross_gates_key_matches(self, fixture, computed):
        assert computed['incarnation_cross']['gates_key'] == fixture['incarnation_cross']['gates_key']
    
    def test_channels_match(self, fixture, computed):
        computed_channels = sorted([f"{ch['gate1']}-{ch['gate2']}" for ch in computed['defined_channels']])
        expected_channels = sorted(fixture['channels']['list'])
        assert computed_channels == expected_channels
    
    def test_personality_activations_match(self, fixture, computed):
        for planet in PLANET_ORDER:
            expected = fixture['planetary_activations']['personality'][planet]['gate_line']
            p_data = computed['personality'].get(planet, {})
            gate_info = p_data.get('gate', {})
            actual = f"{gate_info.get('gate')}.{gate_info.get('line')}"
            assert actual == expected, f"Personality {planet}: {actual} != {expected}"
    
    def test_design_activations_match(self, fixture, computed):
        for planet in PLANET_ORDER:
            expected = fixture['planetary_activations']['design'][planet]['gate_line']
            d_data = computed['design'].get(planet, {})
            gate_info = d_data.get('gate', {})
            actual = f"{gate_info.get('gate')}.{gate_info.get('line')}"
            assert actual == expected, f"Design {planet}: {actual} != {expected}"


# =============================================================================
# MELISA T TESTS
# =============================================================================

class TestMelisaT:
    """Regression tests for Melisa T - RAX Rulership (Reflector)"""
    
    @pytest.fixture
    def fixture(self):
        return load_fixture("mel_true_sidereal_m.json")
    
    @pytest.fixture
    def computed(self):
        user = TEST_USERS[2]
        return get_human_design_chart(
            user['birth_utc'],
            user['lat'],
            user['lon'],
            SIDEREAL_SETTINGS
        )
    
    def test_type_matches(self, fixture, computed):
        """Melisa must be Reflector (no defined centers)"""
        assert computed['type'] == fixture['core_attributes']['type']
        assert computed['type'] == 'Reflector'
    
    def test_authority_matches(self, fixture, computed):
        assert computed['authority'] == fixture['core_attributes']['authority']
    
    def test_profile_matches(self, fixture, computed):
        assert computed['profile'] == fixture['core_attributes']['profile']
    
    def test_definition_matches(self, fixture, computed):
        """Reflector must have None definition"""
        assert computed['definition'] == fixture['core_attributes']['definition']
        assert computed['definition'] == 'None'
    
    def test_cross_angle_matches(self, fixture, computed):
        """Melisa must be RAX (profile line 3)"""
        assert computed['incarnation_cross']['angle'] == fixture['incarnation_cross']['angle']
        assert computed['incarnation_cross']['angle'] == 'RAX'
    
    def test_cross_gates_key_matches(self, fixture, computed):
        assert computed['incarnation_cross']['gates_key'] == fixture['incarnation_cross']['gates_key']
    
    def test_no_channels_for_reflector(self, fixture, computed):
        """Reflector should have no defined channels"""
        assert len(computed['defined_channels']) == 0
        assert fixture['channels']['count'] == 0
    
    def test_no_defined_centers_for_reflector(self, fixture, computed):
        """Reflector should have no defined centers"""
        assert len(computed['defined_centers']) == 0
        assert len(fixture['centers']['defined']) == 0
    
    def test_personality_activations_match(self, fixture, computed):
        for planet in PLANET_ORDER:
            expected = fixture['planetary_activations']['personality'][planet]['gate_line']
            p_data = computed['personality'].get(planet, {})
            gate_info = p_data.get('gate', {})
            actual = f"{gate_info.get('gate')}.{gate_info.get('line')}"
            assert actual == expected, f"Personality {planet}: {actual} != {expected}"
    
    def test_design_activations_match(self, fixture, computed):
        for planet in PLANET_ORDER:
            expected = fixture['planetary_activations']['design'][planet]['gate_line']
            d_data = computed['design'].get(planet, {})
            gate_info = d_data.get('gate', {})
            actual = f"{gate_info.get('gate')}.{gate_info.get('line')}"
            assert actual == expected, f"Design {planet}: {actual} != {expected}"


# =============================================================================
# IDEMPOTENCY TESTS
# =============================================================================

class TestDeterministicIdempotency:
    """Verify computation is deterministic and idempotent"""
    
    @pytest.mark.parametrize("user_index", [0, 1, 2])
    def test_double_computation_yields_same_result(self, user_index):
        """Computing HD twice must yield identical results"""
        user = TEST_USERS[user_index]
        
        result1 = get_human_design_chart(
            user['birth_utc'],
            user['lat'],
            user['lon'],
            SIDEREAL_SETTINGS
        )
        
        result2 = get_human_design_chart(
            user['birth_utc'],
            user['lat'],
            user['lon'],
            SIDEREAL_SETTINGS
        )
        
        # Core attributes must be identical
        assert result1['type'] == result2['type']
        assert result1['authority'] == result2['authority']
        assert result1['profile'] == result2['profile']
        assert result1['definition'] == result2['definition']
        
        # Cross must be identical
        assert result1['incarnation_cross']['angle'] == result2['incarnation_cross']['angle']
        assert result1['incarnation_cross']['gates_key'] == result2['incarnation_cross']['gates_key']
        
        # All planet activations must be identical
        for planet in PLANET_ORDER:
            p1 = result1['personality'][planet]['gate']
            p2 = result2['personality'][planet]['gate']
            assert p1['gate'] == p2['gate'] and p1['line'] == p2['line'], \
                f"Personality {planet} not idempotent"
            
            d1 = result1['design'][planet]['gate']
            d2 = result2['design'][planet]['gate']
            assert d1['gate'] == d2['gate'] and d1['line'] == d2['line'], \
                f"Design {planet} not idempotent"


# =============================================================================
# ANGLE DETERMINATION PROOF TESTS
# =============================================================================

class TestAngleDetermination:
    """Verify angle is determined from structured data, not heuristics"""
    
    def test_nattalia_jxp_from_profile_4(self):
        """Profile 4/6 → Line 4 → JXP (Juxtaposition)"""
        user = TEST_USERS[0]
        result = get_human_design_chart(
            user['birth_utc'], user['lat'], user['lon'], SIDEREAL_SETTINGS
        )
        
        profile = result['profile']
        angle = result['incarnation_cross']['angle']
        
        assert profile == '4/6'
        assert angle == 'JXP'
        # Verify it's derived from profile, not heuristics
        p_sun_line = result['personality']['Sun']['gate']['line']
        assert p_sun_line == 4  # Line 4 = JXP
    
    def test_pete_lax_from_profile_5(self):
        """Profile 5/1 → Line 5 → LAX (Left Angle)"""
        user = TEST_USERS[1]
        result = get_human_design_chart(
            user['birth_utc'], user['lat'], user['lon'], SIDEREAL_SETTINGS
        )
        
        profile = result['profile']
        angle = result['incarnation_cross']['angle']
        
        assert profile == '5/1'
        assert angle == 'LAX'
        p_sun_line = result['personality']['Sun']['gate']['line']
        assert p_sun_line == 5  # Line 5 = LAX
    
    def test_mel_rax_from_profile_3(self):
        """Profile 3/5 → Line 3 → RAX (Right Angle)"""
        user = TEST_USERS[2]
        result = get_human_design_chart(
            user['birth_utc'], user['lat'], user['lon'], SIDEREAL_SETTINGS
        )
        
        profile = result['profile']
        angle = result['incarnation_cross']['angle']
        
        assert profile == '3/5'
        assert angle == 'RAX'
        p_sun_line = result['personality']['Sun']['gate']['line']
        assert p_sun_line == 3  # Line 3 = RAX


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
