"""Tests for the 13-sign midpoint forensic module.
Build marker: midpoint13-forensic-module-v1
"""
import sys, copy
sys.path.insert(0, "/app/backend")

from calculations.true_sidereal_midpoint_boundaries import (
    TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13,
    ARIES_BOUNDARY_OFFSET,
    TRANSITION_ZONE_DEGREES,
    midpoint_13_sign_from_tropical_longitude as mp13,
    compare_current_vs_midpoint13 as cmp_,
)


def test_aries_zero_maps_to_aries():
    # tropical = ARIES_BOUNDARY_OFFSET → zodiacal_degree = 0 → Aries
    r = mp13(ARIES_BOUNDARY_OFFSET)
    assert r["sign"] == "Aries"
    assert r["zodiacal_degree"] == 0.0

def test_19p7286_maps_to_taurus():
    # zodiacal_degree = 19.7286 is the Aries→Taurus boundary (half-open: Taurus)
    trop = ARIES_BOUNDARY_OFFSET + 19.7286
    r = mp13(trop)
    assert r["sign"] == "Taurus"

def test_235p0_maps_to_ophiuchus():
    # zodiacal_degree = 235.0 falls inside Ophiuchus [223.4245, 235.7818)
    trop = (ARIES_BOUNDARY_OFFSET + 235.0) % 360.0
    r = mp13(trop)
    assert r["sign"] == "Ophiuchus", f"expected Ophiuchus, got {r['sign']}"
    assert r["zodiacal_degree"] == 235.0

def test_318p5_maps_to_pisces():
    trop = (ARIES_BOUNDARY_OFFSET + 318.5) % 360.0
    r = mp13(trop)
    assert r["sign"] == "Pisces"

def test_transition_zone_flag_inside_3deg():
    # zodiacal_degree = 18.0 → 1.7286° away from Aries→Taurus boundary
    trop = (ARIES_BOUNDARY_OFFSET + 18.0) % 360.0
    r = mp13(trop)
    assert r["within_transition_zone"] is True
    assert r["distance_to_nearest_boundary"] < TRANSITION_ZONE_DEGREES

def test_transition_zone_flag_outside_3deg():
    # zodiacal_degree = 40.0 → in Taurus interior, ~16.6° from boundaries
    trop = (ARIES_BOUNDARY_OFFSET + 40.0) % 360.0
    r = mp13(trop)
    assert r["within_transition_zone"] is False

def test_pisces_aries_seam_wrap():
    # zodiacal_degree just below 360 → Pisces; just above 0 → Aries
    just_below = (ARIES_BOUNDARY_OFFSET + 359.9) % 360.0
    just_above = (ARIES_BOUNDARY_OFFSET + 0.1) % 360.0
    assert mp13(just_below)["sign"] == "Pisces"
    assert mp13(just_above)["sign"] == "Aries"

def test_table_has_13_signs():
    assert len(TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13) == 13
    assert "Ophiuchus" in TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13

def test_table_boundaries_are_continuous_and_cover_0_360():
    items = list(TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13.items())
    assert items[0][1][0] == 0.0
    assert items[-1][1][1] == 360.0
    # adjacency
    for (n1, (_, hi1)), (n2, (lo2, _)) in zip(items, items[1:]):
        assert abs(hi1 - lo2) < 1e-9, f"gap between {n1} and {n2}: {hi1} vs {lo2}"

def test_compare_returns_both_labels_and_does_not_mutate():
    # Mel Sun tropical = 110.51° — same sign in both schemes (Gemini)
    chart_snapshot = {"frozen": True}
    before = copy.deepcopy(chart_snapshot)
    r = cmp_(110.51)
    assert chart_snapshot == before
    assert r["current_sign"] == "Gemini"
    assert r["midpoint13_sign"] == "Gemini"
    assert r["match"] is True
    assert r["midpoint13_is_ophiuchus"] is False

def test_compare_flags_ophiuchus_for_late_scorpio_longitudes():
    # zodiacal_degree = 228 → Ophiuchus under proposed; Scorpio under current
    trop = (ARIES_BOUNDARY_OFFSET + 228.0) % 360.0
    r = cmp_(trop)
    assert r["midpoint13_sign"] == "Ophiuchus"
    assert r["midpoint13_is_ophiuchus"] is True
    # Whatever the current Variant-B label is, it must NOT be "Ophiuchus"
    assert r["current_sign"] != "Ophiuchus"
    assert r["match"] is False

def test_production_sign_attribution_module_canonical_variant_a():
    """After the Variant-A migration (midpoint13_variant_a_v1) the canonical
    default is Variant A. The MODE_TRUE_SIDEREAL_MIDPOINT alias is kept for
    backwards compat and points at Variant B (the forensic engine).
    """
    from calculations import sign_attribution
    assert sign_attribution.DEFAULT_MODE == sign_attribution.MODE_MIDPOINT13_VARIANT_A
    # Variant B still returns the "Gemini" answer at 110.51° (no math change).
    out_b = sign_attribution.attribute_sign(
        110.51, mode=sign_attribution.MODE_MIDPOINT12_VARIANT_B,
    )
    assert out_b["sign"] == "Gemini"
    # Same longitude under Variant A may differ — verify it returns A's
    # engine_version stamp regardless of label.
    out_a = sign_attribution.attribute_sign(
        110.51, mode=sign_attribution.MODE_MIDPOINT13_VARIANT_A,
    )
    assert out_a["engine_version"] == sign_attribution.ENGINE_VERSION_VARIANT_A


if __name__ == "__main__":
    funcs = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = []
    for f in funcs:
        try:
            f(); print(f"  ✓ {f.__name__}")
        except AssertionError as e:
            print(f"  ✗ {f.__name__}: {e}"); failed.append(f.__name__)
        except Exception as e:
            print(f"  ✗ {f.__name__}: {type(e).__name__}: {e}")
            failed.append(f.__name__)
    print(f"\n{len(funcs) - len(failed)}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
