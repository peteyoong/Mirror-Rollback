"""
Regression Test: Human Design 13-Planet Activations
Golden Case: Surabaya, Indonesia - 04 May 1982, 17:00 local (UTC+07:00)

This test ensures that:
1. All 13 planets are computed for both Personality and Design
2. Gate/line mappings match expected values
3. Type, Authority, Centers, and Channels are correct
4. Incarnation Cross canonical structure is properly formed

Reference: Genetic Matrix True Sidereal-M parity test
"""
import pytest
from datetime import datetime, timezone, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.human_design import (
    get_human_design_chart,
    build_incarnation_cross_canonical
)


class TestSurabayaGoldenCase:
    """
    Surabaya Golden Case Test Suite
    
    Test Subject:
    - Birth date (local): 04 May 1982
    - Birth time (local): 17:00
    - Timezone: UTC+07:00
    - Birth place: Surabaya, Indonesia
    - Latitude: -7.0959
    - Longitude: 112.348
    
    Expected Results (Genetic Matrix reference):
    - Type: Manifesting Generator (Emotional)
    - Authority: Emotional (Solar Plexus)
    - Profile: 4/6
    - All 9 centers defined
    - Multiple channels including: 64-47, 46-29, 59-6, 45-21, 28-38, 18-58
    """
    
    @pytest.fixture
    def surabaya_chart(self):
        """Compute the Surabaya golden case chart"""
        # Convert local to UTC
        # Local: 1982-05-04 17:00 UTC+07:00
        # UTC = Local - 07:00 = 1982-05-04 10:00:00Z
        local_dt = datetime(1982, 5, 4, 17, 0, 0)
        utc_offset = timedelta(hours=7)
        utc_dt = local_dt - utc_offset
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        latitude = -7.0959
        longitude = 112.348
        
        sidereal_settings = {
            "mode": "true_sidereal_user_defined",
            "svp_degrees": 31.2836,
            "reference_year": 2000,
            "yearly_increment": 0.0
        }
        
        return get_human_design_chart(utc_dt, latitude, longitude, sidereal_settings)
    
    # =========================================================================
    # TEST 1: Activation Count (13 per side)
    # =========================================================================
    def test_personality_activation_count(self, surabaya_chart):
        """Assert personality has exactly 13 activations"""
        count = surabaya_chart['activations_count']['personality']
        assert count == 13, f"Expected 13 personality activations, got {count}"
    
    def test_design_activation_count(self, surabaya_chart):
        """Assert design has exactly 13 activations"""
        count = surabaya_chart['activations_count']['design']
        assert count == 13, f"Expected 13 design activations, got {count}"
    
    # =========================================================================
    # TEST 2: Personality Sun/Earth Gate.Line
    # =========================================================================
    def test_personality_sun_gate_line(self, surabaya_chart):
        """Assert personality Sun = Gate 21.4"""
        sun_data = surabaya_chart['personality']['Sun']['gate']
        gate_line = f"{sun_data['gate']}.{sun_data['line']}"
        assert gate_line == "21.4", f"Expected personality Sun 21.4, got {gate_line}"
    
    def test_personality_earth_gate_line(self, surabaya_chart):
        """Assert personality Earth = Gate 48.4"""
        earth_data = surabaya_chart['personality']['Earth']['gate']
        gate_line = f"{earth_data['gate']}.{earth_data['line']}"
        assert gate_line == "48.4", f"Expected personality Earth 48.4, got {gate_line}"
    
    # =========================================================================
    # TEST 3: Design Sun/Earth Gate.Line
    # =========================================================================
    def test_design_sun_gate_line(self, surabaya_chart):
        """Assert design Sun = Gate 38.6"""
        sun_data = surabaya_chart['design']['Sun']['gate']
        gate_line = f"{sun_data['gate']}.{sun_data['line']}"
        assert gate_line == "38.6", f"Expected design Sun 38.6, got {gate_line}"
    
    def test_design_earth_gate_line(self, surabaya_chart):
        """Assert design Earth = Gate 39.6"""
        earth_data = surabaya_chart['design']['Earth']['gate']
        gate_line = f"{earth_data['gate']}.{earth_data['line']}"
        assert gate_line == "39.6", f"Expected design Earth 39.6, got {gate_line}"
    
    # =========================================================================
    # TEST 4: Authority = Emotional
    # =========================================================================
    def test_authority_emotional(self, surabaya_chart):
        """Assert authority is Emotional (Solar Plexus defined)"""
        authority = surabaya_chart['authority']
        assert authority == "Emotional", f"Expected authority 'Emotional', got '{authority}'"
    
    # =========================================================================
    # TEST 5: All 9 Centers Defined
    # =========================================================================
    def test_all_nine_centers_defined(self, surabaya_chart):
        """Assert all 9 centers are defined"""
        defined_centers = surabaya_chart['defined_centers']
        expected_centers = {'Head', 'Ajna', 'Throat', 'G Center', 'Ego', 
                          'Sacral', 'Solar Plexus', 'Spleen', 'Root'}
        
        defined_set = set(defined_centers)
        assert defined_set == expected_centers, (
            f"Expected all 9 centers defined.\n"
            f"Got: {defined_set}\n"
            f"Missing: {expected_centers - defined_set}"
        )
    
    def test_no_undefined_centers(self, surabaya_chart):
        """Assert no undefined centers"""
        undefined_centers = surabaya_chart['undefined_centers']
        assert len(undefined_centers) == 0, f"Expected 0 undefined centers, got {undefined_centers}"
    
    # =========================================================================
    # TEST 6: Required Channels Present
    # =========================================================================
    def test_required_channels_present(self, surabaya_chart):
        """Assert required channels are present: 64-47, 46-29, 59-6, 45-21, 28-38, 18-58"""
        channels = surabaya_chart['defined_channels']
        
        # Extract channel pairs as sets for comparison
        channel_pairs = set()
        for ch in channels:
            # Normalize to smaller-first order for comparison
            g1, g2 = ch['gate1'], ch['gate2']
            pair = (min(g1, g2), max(g1, g2))
            channel_pairs.add(pair)
        
        required_channels = [
            (47, 64),  # Head-Ajna
            (29, 46),  # G Center-Sacral
            (6, 59),   # Sacral-Solar Plexus
            (21, 45),  # Throat-Ego
            (28, 38),  # Spleen-Root
            (18, 58),  # Spleen-Root
        ]
        
        missing = []
        for ch in required_channels:
            if ch not in channel_pairs:
                missing.append(f"{ch[0]}-{ch[1]}")
        
        assert len(missing) == 0, f"Missing required channels: {missing}"
    
    # =========================================================================
    # TEST 7: Profile
    # =========================================================================
    def test_profile(self, surabaya_chart):
        """Assert profile is 4/6"""
        profile = surabaya_chart['profile']
        assert profile == "4/6", f"Expected profile '4/6', got '{profile}'"
    
    # =========================================================================
    # TEST 8: Type (Manifesting Generator)
    # =========================================================================
    def test_type_manifesting_generator(self, surabaya_chart):
        """Assert type is Manifesting Generator"""
        hd_type = surabaya_chart['type']
        assert hd_type == "Manifesting Generator", f"Expected type 'Manifesting Generator', got '{hd_type}'"
    
    # =========================================================================
    # TEST 9: Incarnation Cross Canonical Structure
    # =========================================================================
    def test_incarnation_cross_canonical_key(self, surabaya_chart):
        """Assert incarnation cross has proper canonical key format"""
        cross = surabaya_chart['incarnation_cross']
        
        # Canonical key should be "gate.line/gate.line|gate.line/gate.line"
        canonical_key = cross['canonical_key']
        assert canonical_key == "21.4/48.4|38.6/39.6", (
            f"Expected canonical_key '21.4/48.4|38.6/39.6', got '{canonical_key}'"
        )
    
    def test_incarnation_cross_gates_key(self, surabaya_chart):
        """Assert incarnation cross has proper gates key format"""
        cross = surabaya_chart['incarnation_cross']
        
        # Gates key should be "gate/gate|gate/gate"
        gates_key = cross['gates_key']
        assert gates_key == "21/48|38/39", f"Expected gates_key '21/48|38/39', got '{gates_key}'"
    
    def test_incarnation_cross_angle(self, surabaya_chart):
        """Assert incarnation cross angle is JXP (profile line 4)"""
        cross = surabaya_chart['incarnation_cross']
        angle = cross['angle']
        # Profile 4/6 -> first line is 4 -> JXP
        assert angle == "JXP", f"Expected angle 'JXP', got '{angle}'"
    
    def test_incarnation_cross_display_label(self, surabaya_chart):
        """Assert incarnation cross display label format"""
        cross = surabaya_chart['incarnation_cross']
        display_label = cross['display_label']
        
        # Should be "InternalName (p_sun/p_earth • d_sun/d_earth)"
        assert "21/48" in display_label, f"Display label should contain '21/48': {display_label}"
        assert "38/39" in display_label, f"Display label should contain '38/39': {display_label}"
    
    def test_incarnation_cross_vendor_labels(self, surabaya_chart):
        """Assert incarnation cross has vendor labels structure"""
        cross = surabaya_chart['incarnation_cross']
        vendor_labels = cross['vendor_labels']
        
        assert 'emergent' in vendor_labels, "Missing 'emergent' vendor label"
        assert 'genetic_matrix' in vendor_labels, "Missing 'genetic_matrix' vendor label"
        
        # Genetic Matrix label should have angle + name + line
        gm_label = vendor_labels['genetic_matrix']
        assert "JXP" in gm_label, f"Genetic Matrix label should contain 'JXP': {gm_label}"
        assert "4" in gm_label, f"Genetic Matrix label should contain line '4': {gm_label}"
    
    # =========================================================================
    # TEST 10: Compute Integrity
    # =========================================================================
    def test_compute_integrity_valid(self, surabaya_chart):
        """Assert compute integrity is valid"""
        integrity = surabaya_chart['compute_integrity']
        assert integrity['valid'] is True, "Compute integrity should be valid"
    
    def test_compute_integrity_activations(self, surabaya_chart):
        """Assert compute integrity reports correct activation counts"""
        integrity = surabaya_chart['compute_integrity']
        
        assert integrity['personality_activations'] == 13, (
            f"Expected 13 personality activations in integrity, got {integrity['personality_activations']}"
        )
        assert integrity['design_activations'] == 13, (
            f"Expected 13 design activations in integrity, got {integrity['design_activations']}"
        )


class TestIncarnationCrossCanonical:
    """Test the incarnation cross canonical structure builder"""
    
    def test_build_canonical_key_format(self):
        """Test canonical key format"""
        cross = build_incarnation_cross_canonical(
            p_sun_gate=21, p_sun_line=4,
            p_earth_gate=48, p_earth_line=4,
            d_sun_gate=38, d_sun_line=6,
            d_earth_gate=39, d_earth_line=6,
            profile_line1=4
        )
        
        assert cross['canonical_key'] == "21.4/48.4|38.6/39.6"
        assert cross['gates_key'] == "21/48|38/39"
        assert cross['angle'] == "JXP"
    
    def test_angle_rax_for_line_1_2_3(self):
        """Test RAX angle for profile lines 1, 2, 3"""
        for line in [1, 2, 3]:
            cross = build_incarnation_cross_canonical(
                p_sun_gate=1, p_sun_line=line,
                p_earth_gate=2, p_earth_line=1,
                d_sun_gate=3, d_sun_line=1,
                d_earth_gate=4, d_earth_line=1,
                profile_line1=line
            )
            assert cross['angle'] == "RAX", f"Expected RAX for line {line}"
    
    def test_angle_jxp_for_line_4(self):
        """Test JXP angle for profile line 4"""
        cross = build_incarnation_cross_canonical(
            p_sun_gate=1, p_sun_line=4,
            p_earth_gate=2, p_earth_line=4,
            d_sun_gate=3, d_sun_line=4,
            d_earth_gate=4, d_earth_line=4,
            profile_line1=4
        )
        assert cross['angle'] == "JXP"
    
    def test_angle_lax_for_line_5_6(self):
        """Test LAX angle for profile lines 5, 6"""
        for line in [5, 6]:
            cross = build_incarnation_cross_canonical(
                p_sun_gate=1, p_sun_line=line,
                p_earth_gate=2, p_earth_line=1,
                d_sun_gate=3, d_sun_line=1,
                d_earth_gate=4, d_earth_line=1,
                profile_line1=line
            )
            assert cross['angle'] == "LAX", f"Expected LAX for line {line}"


class TestAllPlanetsPresent:
    """Test that all 13 planets are present in the chart"""
    
    @pytest.fixture
    def chart(self):
        """Compute a chart for testing"""
        utc_dt = datetime(1982, 5, 4, 10, 0, 0, tzinfo=timezone.utc)
        return get_human_design_chart(utc_dt, -7.0959, 112.348)
    
    def test_all_personality_planets_present(self, chart):
        """Assert all 13 planets are in personality data"""
        expected_planets = [
            'Sun', 'Earth', 'Moon', 'North Node', 'South Node',
            'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
            'Uranus', 'Neptune', 'Pluto'
        ]
        
        for planet in expected_planets:
            assert planet in chart['personality'], f"Missing personality planet: {planet}"
            assert 'gate' in chart['personality'][planet], f"Missing gate for personality {planet}"
    
    def test_all_design_planets_present(self, chart):
        """Assert all 13 planets are in design data"""
        expected_planets = [
            'Sun', 'Earth', 'Moon', 'North Node', 'South Node',
            'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
            'Uranus', 'Neptune', 'Pluto'
        ]
        
        for planet in expected_planets:
            assert planet in chart['design'], f"Missing design planet: {planet}"
            assert 'gate' in chart['design'][planet], f"Missing gate for design {planet}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
