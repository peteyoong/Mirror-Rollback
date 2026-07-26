"""The Mirror — Session 4A Gene Keys Foundation Tests
===================================================
Deterministic tests for the canonical Gene Keys sphere map, mechanics
endpoint, and Session-4A guardrails.

Session 4A does NOT rewrite Gene Keys narrative content.  These tests
verify only the structural foundation.

Run: pytest backend/tests/test_the_mirror_session4a_gene_keys_foundation.py -v
"""
import sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '/app/backend')

import pytest

from calculations.human_design import get_human_design_chart
from services.gene_keys_sphere_map import (
    CANONICAL_SPHERE_MAP,
    GENE_KEYS_SPHERE_MAP_VERSION,
    METHODOLOGY_PROVENANCE,
    SEQUENCES,
    ACTIVATION_SEQUENCE,
    VENUS_SEQUENCE,
    PEARL_SEQUENCE,
    STAR_PEARL_AVAILABILITY,
    SHARED_ACTIVATION_ROLES,
    get_unique_activation_points,
    get_sphere_role_map,
    sphere_deltas_vs_canonical,
    LEGACY_CALC_MAP,
    LEGACY_INTERPRETER_DOCSTRING_MAP,
)
from services.gene_keys_mechanics import (
    build_gene_keys_mechanics,
    GENE_KEYS_MECHANICS_VERSION,
    PETE_USER_ID,
    PETE_EXPECTED_GATES,
)


# =============================================================================
# BENCHMARK FIXTURES
# =============================================================================

def _utc_from_local(local_dt, offset):
    return (local_dt - timedelta(hours=offset)).replace(tzinfo=timezone.utc)


BENCHMARK_PETE = {
    "name": "Pete",
    "birth_local": datetime(1968, 4, 1, 1, 25, 0),
    "utc_offset": 7.5,
    "lat": 3.1073,
    "lon": 101.6070,
    "user_id": PETE_USER_ID,
}

BENCHMARK_JAY = {
    "name": "Jay",
    "birth_local": datetime(1981, 10, 12, 18, 16, 0),
    "utc_offset": 8.0,
    "lat": 1.3521,
    "lon": 103.8198,
    "user_id": "synthetic_jay",
}

BENCHMARK_MELISSA = {
    "name": "Melissa",
    "birth_local": datetime(1981, 7, 13, 7, 25, 0),
    "utc_offset": 8.0,
    "lat": 2.1896,
    "lon": 102.2501,
    "user_id": "synthetic_melissa",
}


def _hd_for(fixture):
    return get_human_design_chart(
        _utc_from_local(fixture["birth_local"], fixture["utc_offset"]),
        fixture["lat"],
        fixture["lon"],
    )


# =============================================================================
# 1.  Canonical sphere map integrity
# =============================================================================

class TestCanonicalSphereMap:
    def test_version_stamp(self):
        assert GENE_KEYS_SPHERE_MAP_VERSION == "mirror_true_sidereal_gk_v1"

    def test_sphere_count_and_names(self):
        # 13 sphere roles across three sequences (Life's Work/Brand share
        # an activation; Core/Vocation share an activation → 11 unique
        # underlying activation points).
        assert len(CANONICAL_SPHERE_MAP) == 13
        assert set(CANONICAL_SPHERE_MAP.keys()) == {
            "Life's Work", "Evolution", "Radiance", "Purpose",
            "Attraction", "IQ", "EQ", "SQ", "Core",
            "Vocation", "Culture", "Brand", "Pearl",
        }

    def test_first_party_activation_pairs(self):
        expected = {
            "Life's Work": ("Sun",     "personality"),
            "Evolution":   ("Earth",   "personality"),
            "Radiance":    ("Sun",     "design"),
            "Purpose":     ("Earth",   "design"),
            "Attraction":  ("Moon",    "design"),
            "IQ":          ("Venus",   "personality"),
            "EQ":          ("Mars",    "personality"),
            "SQ":          ("Venus",   "design"),
            "Core":        ("Mars",    "design"),
            "Vocation":    ("Mars",    "design"),
            "Culture":     ("Jupiter", "design"),
            "Brand":       ("Sun",     "personality"),
            "Pearl":       ("Jupiter", "personality"),
        }
        for sphere, (planet, side) in expected.items():
            act = CANONICAL_SPHERE_MAP[sphere]
            assert act["planet"] == planet, sphere
            assert act["chart_side"] == side, sphere

    def test_unique_activation_points_deduplicated(self):
        unique = get_unique_activation_points()
        # Brand shares Life's Work; Vocation shares Core → 13 − 2 = 11
        assert len(unique) == 11

    def test_shared_roles_documented(self):
        pairs = {(r["primary"], r["shared"]) for r in SHARED_ACTIVATION_ROLES}
        assert ("Life's Work", "Brand") in pairs
        assert ("Core", "Vocation") in pairs

    def test_sequence_membership(self):
        assert ACTIVATION_SEQUENCE == ["Life's Work", "Evolution", "Radiance", "Purpose"]
        assert VENUS_SEQUENCE == ["Attraction", "IQ", "EQ", "SQ", "Core"]
        assert PEARL_SEQUENCE == ["Vocation", "Culture", "Brand", "Pearl"]

    def test_methodology_provenance_shape(self):
        m = METHODOLOGY_PROVENANCE
        assert m["version"] == GENE_KEYS_SPHERE_MAP_VERSION
        assert m["longitude_engine"] == "the_mirror.hd_sidereal_v1"
        assert "genekeys.com" in m["sphere_map_reference_urls"][0]
        assert "True Sidereal" in m["disclosure"]

    def test_star_pearl_deferred(self):
        assert STAR_PEARL_AVAILABILITY == "UNAVAILABLE_OR_DEFERRED"


# =============================================================================
# 2.  No duplicate astronomical / gate engine
# =============================================================================

class TestSingleEngine:
    def test_sphere_map_module_has_no_astronomy_code(self):
        import services.gene_keys_sphere_map as m
        src = open(m.__file__).read()
        # No swisseph, no ephemeris, no longitude arithmetic.
        for banned in ("swisseph", "ephemeris", "julian", "longitude_to_gate", "def _compute"):
            assert banned not in src, banned

    def test_mechanics_module_reuses_hd_engine(self):
        import services.gene_keys_mechanics as m
        src = open(m.__file__).read()
        # Strip docstrings/comments before scanning (allow docstring references
        # to the HD engine but forbid actual invocation).
        import re
        code_only = re.sub(r'""".*?"""', '', src, flags=re.DOTALL)
        code_only = re.sub(r"#.*", "", code_only)
        assert "get_human_design_chart(" not in code_only  # mechanics consumes an *existing* HD chart
        assert "longitude_to_gate" not in code_only        # no gate arithmetic

    def test_calculations_gene_keys_delegates_to_sphere_map(self):
        from calculations import gene_keys as gk_calc
        src = open(gk_calc.__file__).read()
        assert "CANONICAL_SPHERE_MAP" in src


# =============================================================================
# 3.  Sphere mapping correctness (per Pete's activations)
# =============================================================================

class TestPeteCanonicalMapping:
    @pytest.fixture(scope="class")
    def mechanics(self):
        hd = _hd_for(BENCHMARK_PETE)
        return build_gene_keys_mechanics(hd, user_id=PETE_USER_ID)

    def test_profile_available(self, mechanics):
        assert mechanics["profile_availability"] == "present"

    def test_all_13_spheres_derived(self, mechanics):
        assert len(mechanics["all_spheres"]) == 13

    def test_unique_activations_deduplicated_11(self, mechanics):
        assert len(mechanics["unique_spheres"]) == 11

    def test_brand_shares_lifes_work_activation(self, mechanics):
        by_name = {r["sphere_name"]: r for r in mechanics["all_spheres"]}
        assert by_name["Brand"]["gene_key"] == by_name["Life's Work"]["gene_key"]
        assert by_name["Brand"]["line"] == by_name["Life's Work"]["line"]
        assert by_name["Brand"]["source_longitude"] == by_name["Life's Work"]["source_longitude"]

    def test_vocation_shares_core_activation(self, mechanics):
        by_name = {r["sphere_name"]: r for r in mechanics["all_spheres"]}
        assert by_name["Vocation"]["gene_key"] == by_name["Core"]["gene_key"]
        assert by_name["Vocation"]["source_longitude"] == by_name["Core"]["source_longitude"]

    def test_personality_and_design_sides_distinct(self, mechanics):
        by_name = {r["sphere_name"]: r for r in mechanics["all_spheres"]}
        # Life's Work (P Sun) vs Radiance (D Sun) must not collapse.
        assert by_name["Life's Work"]["activation"]["chart_side"] == "personality"
        assert by_name["Radiance"]["activation"]["chart_side"] == "design"
        assert by_name["Life's Work"]["source_longitude"] != by_name["Radiance"]["source_longitude"]

    def test_verified_spheres_include_first_party_matches(self, mechanics):
        by_name = {r["sphere_name"]: r for r in mechanics["all_spheres"]}
        for sphere in ["Life's Work", "Evolution", "Radiance", "Purpose",
                       "Attraction", "SQ", "Vocation", "Brand"]:
            assert by_name[sphere]["verification_status"] == "verified", sphere
            assert by_name[sphere]["gene_key"] == PETE_EXPECTED_GATES[sphere], sphere

    def test_discrepancy_spheres_held(self, mechanics):
        by_name = {r["sphere_name"]: r for r in mechanics["all_spheres"]}
        # Per Session-4A user rule: hold, do not fit-and-document.
        for sphere in ["IQ", "EQ", "Core", "Culture", "Pearl"]:
            assert by_name[sphere]["verification_status"] == "discrepancy_held", sphere
            assert by_name[sphere]["verification_note"] is not None
            assert by_name[sphere]["gene_key"] != PETE_EXPECTED_GATES[sphere]

    def test_top_level_verification_status_partial(self, mechanics):
        assert mechanics["verification_status"] == "partial"
        assert len(mechanics["verification_discrepancies"]) == 5

    def test_pete_gates_not_hardcoded_in_production(self):
        # PETE_EXPECTED_GATES lives in the mechanics module only for
        # regression labelling.  Production sphere logic must never
        # look this dict up as a source of truth.
        import services.gene_keys_mechanics as m
        src = open(m.__file__).read()
        # It's referenced only inside verification checks, not as a
        # gate-derivation lookup.
        for line in src.splitlines():
            if "PETE_EXPECTED_GATES[" in line and "expected" not in line and "==" not in line:
                pytest.fail(f"Unexpected use of PETE_EXPECTED_GATES for gate derivation: {line}")


# =============================================================================
# 4.  Synthetic non-Pete fixtures generalise
# =============================================================================

class TestSyntheticFixtures:
    def test_jay_produces_distinct_valid_profile(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_JAY), user_id="synthetic_jay")
        assert mech["profile_availability"] == "present"
        # Non-Pete → no Pete-regression labels
        assert mech["verification_status"] == "verified"
        assert mech["verification_discrepancies"] == []
        # Every sphere has a valid gate (1..64)
        for r in mech["all_spheres"]:
            assert r["gene_key"] is not None
            assert 1 <= r["gene_key"] <= 64

    def test_melissa_produces_distinct_valid_profile(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_MELISSA), user_id="synthetic_melissa")
        assert mech["profile_availability"] == "present"
        # Melissa's Life's Work must differ from Pete's (proves generalisation)
        pete_mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id="synthetic_pete_probe")
        pete_lw = next(r for r in pete_mech["all_spheres"] if r["sphere_name"] == "Life's Work")
        mel_lw = next(r for r in mech["all_spheres"] if r["sphere_name"] == "Life's Work")
        assert pete_lw["gene_key"] != mel_lw["gene_key"]


# =============================================================================
# 5.  Lines only when verified
# =============================================================================

class TestLineHandling:
    def test_line_present_when_engine_provides_it(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id="probe")
        for r in mech["all_spheres"]:
            # Under the current HD engine every gate has a verified line.
            assert isinstance(r["line"], int)
            assert 1 <= r["line"] <= 6

    def test_line_none_when_engine_missing(self):
        # Synthetic missing-line HD chart
        hd = {"personality": {"Sun": {"gate": {"gate": 1}, "longitude": 0.0}},
              "design": {"Sun": {"gate": {"gate": 1}, "longitude": 180.0}}}
        # Fill in the other planets minimally so the mechanics builder does
        # not crash; each will emit gate=1 line=None which is what we want
        # to assert on.
        for p in ["Earth", "Moon", "Mercury", "Venus", "Mars", "Jupiter"]:
            hd["personality"][p] = {"gate": {"gate": 1}, "longitude": 0.0}
            hd["design"][p] = {"gate": {"gate": 1}, "longitude": 0.0}
        mech = build_gene_keys_mechanics(hd, user_id="synthetic_lineless")
        for r in mech["all_spheres"]:
            assert r["line"] is None


# =============================================================================
# 6.  No Human Design vocabulary leaks into Gene Keys output
# =============================================================================

class TestNoHDLeak:
    HD_TERMS = [
        "Type", "Strategy", "Authority", "Centres", "Centers",
        "Channels", "Definition", "Not-Self", "Signature",
    ]

    def test_mechanics_envelope_free_of_hd_vocabulary(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id=PETE_USER_ID)
        import json
        blob = json.dumps(mech)
        for term in self.HD_TERMS:
            # Whole-word check via space delimiters
            assert f'"{term}"' not in blob, term
            assert f': "{term}"' not in blob, term


# =============================================================================
# 7.  Content provenance is required
# =============================================================================

class TestContentProvenance:
    def test_every_sphere_has_content_provenance(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id=PETE_USER_ID)
        for r in mech["all_spheres"]:
            assert "content_provenance" in r
            assert r["content_provenance"] in ("mirror_original", "structural_label", "user_authored")

    def test_no_interpretive_prose_ships_without_provenance(self):
        # Mechanics ships only structural labels.  Full prose lives in the
        # interpreter which is not consumed by the new lens scaffold in 4A.
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id=PETE_USER_ID)
        for r in mech["all_spheres"]:
            for k, v in (r["structural_labels"] or {}).items():
                # Structural labels are of the form "Shadow of Gene Key N" —
                # short, no proprietary interpretation.
                if v is None:
                    continue
                assert "of Gene Key" in v
                assert len(v.split()) < 8


# =============================================================================
# 8.  Star Pearl remains unavailable in Session 4A
# =============================================================================

class TestStarPearlDeferred:
    def test_star_pearl_flag(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id=PETE_USER_ID)
        assert mech["star_pearl_availability"] == "UNAVAILABLE_OR_DEFERRED"

    def test_star_pearl_not_in_sequences(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id=PETE_USER_ID)
        assert set(mech["sequences"].keys()) == {"Activation", "Venus", "Pearl"}


# =============================================================================
# 9.  Reading availability — pending Session 4B
# =============================================================================

class TestReadingPending:
    def test_reading_pending(self):
        mech = build_gene_keys_mechanics(_hd_for(BENCHMARK_PETE), user_id=PETE_USER_ID)
        assert mech["reading_availability"]["state"] == "pending_session_4b"


# =============================================================================
# 10. Legacy delta reporting
# =============================================================================

class TestLegacyDeltas:
    def test_legacy_calc_map_has_documented_deltas(self):
        deltas = sphere_deltas_vs_canonical(LEGACY_CALC_MAP)
        # Attraction, IQ, EQ, SQ diverged in the old calculations file.
        changed = {d["sphere"] for d in deltas if d["status"] == "changed"}
        assert "Attraction" in changed
        assert "EQ" in changed
        assert "SQ" in changed

    def test_legacy_interpreter_docstring_map_has_documented_deltas(self):
        deltas = sphere_deltas_vs_canonical(LEGACY_INTERPRETER_DOCSTRING_MAP)
        changed = {d["sphere"] for d in deltas if d["status"] == "changed"}
        # Old docstring listed Mercury for IQ/EQ, wrong sides on Core /
        # Culture / Pearl.
        assert "IQ" in changed
        assert "EQ" in changed
        assert "Core" in changed
        assert "Culture" in changed
        assert "Pearl" in changed


# =============================================================================
# 11. Mechanics version constant
# =============================================================================

def test_mechanics_version_stamp():
    assert GENE_KEYS_MECHANICS_VERSION == "gene_keys_mechanics_v1"
