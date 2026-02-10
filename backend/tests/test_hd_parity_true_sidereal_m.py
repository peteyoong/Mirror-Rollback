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
7. Angle source is "computed_rule" and angle_proof exists with correct structure
8. Invalid profiles return null angle (never default to any angle)
9. No duplicate paragraph bodies exist

DO NOT modify fixtures without re-validating against reference tool.

ANGLE DETERMINATION:
The cross angle (RAX/LAX/JXP) is determined by the FULL PROFILE combination,
NOT by just the first line of the profile. The mapping is:
- RAX (Right Angle): 1/3, 1/4, 2/4, 2/5, 3/5, 3/6, 4/6
- JXP (Juxtaposition): 4/1 ONLY
- LAX (Left Angle): 5/1, 5/2, 6/2, 6/3
"""

import sys
sys.path.insert(0, '/app/backend')

import json
import hashlib
import pytest
from datetime import datetime, timezone
from pathlib import Path

from calculations.human_design import get_human_design_chart, PROFILE_TO_ANGLE, get_angle_from_profile
from quality_gate import detect_duplicate_bodies, remove_duplicate_bodies

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
        "lon": 112.348,
        "expected_angle": "RAX",
        "expected_cross_type_key": "Right Angle Cross"
    },
    {
        "name": "Pete Y",
        "fixture": "pete_true_sidereal_m.json",
        "birth_utc": datetime(1968, 3, 31, 17, 55, tzinfo=timezone.utc),
        "lat": 3.1073,
        "lon": 101.607,
        "expected_angle": "LAX",
        "expected_cross_type_key": "Left Angle Cross"
    },
    {
        "name": "Melisa T",
        "fixture": "mel_true_sidereal_m.json",
        "birth_utc": datetime(1981, 7, 12, 23, 55, tzinfo=timezone.utc),
        "lat": 2.1889,
        "lon": 102.251,
        "expected_angle": "RAX",
        "expected_cross_type_key": "Right Angle Cross"
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
# PROFILE TO ANGLE MAPPING TESTS
# =============================================================================

class TestProfileToAngleMapping:
    """Verify the PROFILE_TO_ANGLE constant is correctly defined"""
    
    def test_all_12_profiles_mapped(self):
        """All 12 HD profiles must be in the mapping"""
        expected_profiles = [
            "1/3", "1/4", "2/4", "2/5", "3/5", "3/6", "4/6",  # RAX
            "4/1",  # JXP
            "5/1", "5/2", "6/2", "6/3"  # LAX
        ]
        for profile in expected_profiles:
            assert profile in PROFILE_TO_ANGLE, f"Profile {profile} missing from mapping"
    
    def test_rax_profiles_correct(self):
        """RAX profiles: 1/3, 1/4, 2/4, 2/5, 3/5, 3/6, 4/6"""
        rax_profiles = ["1/3", "1/4", "2/4", "2/5", "3/5", "3/6", "4/6"]
        for profile in rax_profiles:
            angle, _ = PROFILE_TO_ANGLE[profile]
            assert angle == "RAX", f"Profile {profile} should be RAX, got {angle}"
    
    def test_jxp_only_4_1(self):
        """Only profile 4/1 is JXP (Juxtaposition)"""
        angle, _ = PROFILE_TO_ANGLE["4/1"]
        assert angle == "JXP"
        
        # Verify no other profile is JXP
        for profile, (angle, _) in PROFILE_TO_ANGLE.items():
            if profile != "4/1":
                assert angle != "JXP", f"Profile {profile} incorrectly mapped to JXP"
    
    def test_lax_profiles_correct(self):
        """LAX profiles: 5/1, 5/2, 6/2, 6/3"""
        lax_profiles = ["5/1", "5/2", "6/2", "6/3"]
        for profile in lax_profiles:
            angle, _ = PROFILE_TO_ANGLE[profile]
            assert angle == "LAX", f"Profile {profile} should be LAX, got {angle}"
    
    def test_profile_4_6_is_rax_not_jxp(self):
        """Critical: Profile 4/6 must be RAX, NOT JXP (common misconception)"""
        angle, _ = PROFILE_TO_ANGLE["4/6"]
        assert angle == "RAX", "Profile 4/6 must be RAX (Right Angle), not JXP"
    
    def test_invalid_profile_returns_null(self):
        """Invalid profiles must return None angle, never default to any angle"""
        invalid_profiles = ["7/1", "0/0", "invalid", "", None, "1/7", "abc"]
        
        for profile in invalid_profiles:
            angle, angle_full, proof = get_angle_from_profile(profile)
            assert angle is None, f"Invalid profile '{profile}' should return None angle, got '{angle}'"
            assert angle_full is None, f"Invalid profile '{profile}' should return None angle_full"
            assert proof.get("angle_source") == "unknown", \
                f"Invalid profile '{profile}' should have angle_source='unknown'"
    
    def test_angle_proof_structure(self):
        """angle_proof must have the correct structure"""
        profile = "4/6"
        angle, angle_full, proof = get_angle_from_profile(profile)
        
        # Required fields
        assert "profile" in proof
        assert "profile_to_angle_table_used" in proof
        assert "matched_profile" in proof
        assert "result_angle" in proof
        assert "angle_source" in proof
        
        # Values for valid profile
        assert proof["profile"] == "4/6"
        assert proof["profile_to_angle_table_used"] == True
        assert proof["matched_profile"] == "4/6"
        assert proof["result_angle"] == "RAX"
        assert proof["angle_source"] == "computed_rule"


# =============================================================================
# NATTALIA C TESTS
# =============================================================================

class TestNattaliaC:
    """Regression tests for Nattalia C - RAX Tension (profile 4/6)"""
    
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
        """Incarnation cross angle must match fixture (RAX for profile 4/6)"""
        assert computed['incarnation_cross']['angle'] == fixture['incarnation_cross']['angle']
        # Critical: Nattalia (profile 4/6) must be RAX, NOT JXP
        assert computed['incarnation_cross']['angle'] == 'RAX'
    
    def test_cross_angle_source_is_computed_rule(self, fixture, computed):
        """Angle source must be 'computed_rule'"""
        assert computed['incarnation_cross']['angle_source'] == 'computed_rule'
        assert fixture['incarnation_cross']['angle_source'] == 'computed_rule'
    
    def test_cross_angle_proof_structure(self, fixture, computed):
        """Angle proof must have correct structure and values"""
        proof = computed['incarnation_cross']['angle_proof']
        
        # Required structure
        assert proof is not None
        assert isinstance(proof, dict)
        assert len(proof) > 0
        
        # Required fields
        assert 'profile' in proof
        assert 'profile_to_angle_table_used' in proof
        assert 'matched_profile' in proof
        assert 'result_angle' in proof
        
        # Correct values for Nattalia
        assert proof['profile'] == '4/6'
        assert proof['profile_to_angle_table_used'] == True
        assert proof['matched_profile'] == '4/6'
        assert proof['result_angle'] == 'RAX'
    
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
    
    def test_deep_dive_cross_type_key(self, fixture):
        """Deep dive should use 'Right Angle Cross' for Nattalia"""
        assert fixture['deep_dive_cross_type_key'] == 'Right Angle Cross'


# =============================================================================
# PETE Y TESTS
# =============================================================================

class TestPeteY:
    """Regression tests for Pete Y - LAX Migration (profile 5/1)"""
    
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
        """Pete must be LAX (profile 5/1)"""
        assert computed['incarnation_cross']['angle'] == fixture['incarnation_cross']['angle']
        assert computed['incarnation_cross']['angle'] == 'LAX'
    
    def test_cross_angle_source_is_computed_rule(self, fixture, computed):
        """Angle source must be 'computed_rule'"""
        assert computed['incarnation_cross']['angle_source'] == 'computed_rule'
    
    def test_cross_angle_proof_structure(self, fixture, computed):
        """Angle proof must have correct structure"""
        proof = computed['incarnation_cross']['angle_proof']
        assert proof['profile'] == '5/1'
        assert proof['profile_to_angle_table_used'] == True
        assert proof['result_angle'] == 'LAX'
    
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
    
    def test_deep_dive_cross_type_key(self, fixture):
        """Deep dive should use 'Left Angle Cross' for Pete"""
        assert fixture['deep_dive_cross_type_key'] == 'Left Angle Cross'


# =============================================================================
# MELISA T TESTS
# =============================================================================

class TestMelisaT:
    """Regression tests for Melisa T - RAX Rulership (Reflector, profile 3/5)"""
    
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
        """Melisa must be RAX (profile 3/5)"""
        assert computed['incarnation_cross']['angle'] == fixture['incarnation_cross']['angle']
        assert computed['incarnation_cross']['angle'] == 'RAX'
    
    def test_cross_angle_source_is_computed_rule(self, fixture, computed):
        """Angle source must be 'computed_rule'"""
        assert computed['incarnation_cross']['angle_source'] == 'computed_rule'
    
    def test_cross_angle_proof_structure(self, fixture, computed):
        """Angle proof must have correct structure"""
        proof = computed['incarnation_cross']['angle_proof']
        assert proof['profile'] == '3/5'
        assert proof['profile_to_angle_table_used'] == True
        assert proof['result_angle'] == 'RAX'
    
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
    
    def test_deep_dive_cross_type_key(self, fixture):
        """Deep dive should use 'Right Angle Cross' for Melisa"""
        assert fixture['deep_dive_cross_type_key'] == 'Right Angle Cross'


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
        assert result1['incarnation_cross']['angle_source'] == result2['incarnation_cross']['angle_source']
        assert result1['incarnation_cross']['angle_proof'] == result2['incarnation_cross']['angle_proof']
        
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
# DEEP DIVE CROSS TYPE KEY TESTS
# =============================================================================

class TestDeepDiveCrossTypeKey:
    """Verify Deep Dive uses correct cross_type_key based on angle"""
    
    def test_rax_maps_to_right_angle_cross(self):
        """RAX angle must map to 'Right Angle Cross' in Deep Dive"""
        # This mapping happens in server.py cross detection logic
        angle_to_cross_type = {
            "RAX": "Right Angle Cross",
            "LAX": "Left Angle Cross",
            "JXP": "Juxtaposition Cross"
        }
        
        for user in TEST_USERS:
            expected_angle = user['expected_angle']
            expected_cross_type = user['expected_cross_type_key']
            
            assert angle_to_cross_type[expected_angle] == expected_cross_type, \
                f"User {user['name']}: {expected_angle} should map to {expected_cross_type}"
    
    def test_nattalia_deep_dive_uses_right_angle_copy(self):
        """Nattalia (4/6, RAX) must use Right Angle Cross copy"""
        user = TEST_USERS[0]
        result = get_human_design_chart(
            user['birth_utc'], user['lat'], user['lon'], SIDEREAL_SETTINGS
        )
        
        angle = result['incarnation_cross']['angle']
        assert angle == 'RAX'
        # In server.py, RAX -> "Right Angle Cross"
    
    def test_pete_deep_dive_uses_left_angle_copy(self):
        """Pete (5/1, LAX) must use Left Angle Cross copy"""
        user = TEST_USERS[1]
        result = get_human_design_chart(
            user['birth_utc'], user['lat'], user['lon'], SIDEREAL_SETTINGS
        )
        
        angle = result['incarnation_cross']['angle']
        assert angle == 'LAX'
        # In server.py, LAX -> "Left Angle Cross"


# =============================================================================
# NO DUPLICATE PARAGRAPHS TESTS
# =============================================================================

class TestNoDuplicateParagraphs:
    """Verify no duplicate paragraph bodies exist"""
    
    def test_detect_duplicate_bodies_utility(self):
        """Test the duplicate detection utility"""
        sections = [
            {"section_id": "sec1", "body": "This is content."},
            {"section_id": "sec2", "body": "Different content."},
            {"section_id": "sec3", "body": "This is content."},  # Duplicate of sec1
        ]
        
        duplicates = detect_duplicate_bodies(sections)
        assert len(duplicates) == 1
        assert duplicates[0] == ("sec1", "sec3")
    
    def test_remove_duplicate_bodies_utility(self):
        """Test the duplicate removal utility"""
        sections = [
            {"section_id": "sec1", "body": "First content."},
            {"section_id": "sec2", "body": "Second content."},
            {"section_id": "sec3", "body": "First content."},  # Duplicate
            {"section_id": "sec4", "body": "Third content."},
        ]
        
        deduplicated = remove_duplicate_bodies(sections)
        assert len(deduplicated) == 3
        section_ids = [s['section_id'] for s in deduplicated]
        assert "sec1" in section_ids
        assert "sec2" in section_ids
        assert "sec4" in section_ids
        assert "sec3" not in section_ids  # Removed as duplicate
    
    def test_empty_bodies_preserved(self):
        """Empty bodies should be preserved (structural sections)"""
        sections = [
            {"section_id": "sec1", "body": ""},
            {"section_id": "sec2", "body": "Content."},
            {"section_id": "sec3", "body": ""},  # Should not be removed as duplicate
        ]
        
        deduplicated = remove_duplicate_bodies(sections)
        assert len(deduplicated) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
