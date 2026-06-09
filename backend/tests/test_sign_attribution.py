"""
Tests for the sign-attribution toggle (Build: true-sidereal-midpoint-toggle-v1)

Verifies the two attribution functions match every requirement:
  - Mel ASC flips Gemini → Cancer under midpoint
  - Ana MC flips Capricorn → Aquarius under midpoint
  - Pete signs remain stable across both modes
  - degree_within_sign is always in [0, sign_width)
  - Pisces wrap-around at the 354.93 → 25.61 boundary works
  - Default mode preserves uniform_30 production behaviour

Run:
    cd /app/backend && python -m pytest tests/test_sign_attribution.py -v
    cd /app/backend && python -m tests.test_sign_attribution
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculations.sign_attribution import (
    attribute_sign,
    attribute_sign_uniform_30,
    attribute_sign_true_sidereal_midpoint,
    MIDPOINT_BOUNDARIES,
    MODE_UNIFORM_30,
    MODE_TRUE_SIDEREAL_MIDPOINT,
    MIDPOINT_MODEL_NAME,
    DEFAULT_AYANAMSA,
)


# -----------------------------------------------------------------------------
# Mel / Ana / Pete tropical positions (verified in genetic-matrix-reconciliation)
# -----------------------------------------------------------------------------
MEL  = {"ASC": 120.39, "Sun": 110.51, "Moon": 243.15, "MC": 34.03}
ANA  = {"ASC":  51.48, "Sun":  42.46, "Moon": 294.16, "MC": 329.99}
PETE = {"ASC": 286.82, "Sun":  11.08, "Moon":  41.90, "MC": 201.13}


def _assert_eq(actual, expected, label):
    assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"


# =============================================================================
# Requirement 1 — Mel ASC flips Gemini → Cancer under midpoint
# =============================================================================
def test_mel_asc_gemini_under_uniform():
    r = attribute_sign_uniform_30(MEL["ASC"])
    _assert_eq(r["sign"], "Gemini", "Mel ASC uniform_30")


def test_mel_asc_cancer_under_midpoint():
    r = attribute_sign_true_sidereal_midpoint(MEL["ASC"])
    _assert_eq(r["sign"], "Cancer", "Mel ASC midpoint")
    # Within the 3°-7° tolerance the product owner stated
    assert 3.0 <= r["degree_within_sign"] <= 7.0, \
        f"Mel ASC under midpoint should be 3°-7° Cancer; got {r['degree_within_sign']}"


# =============================================================================
# Requirement 2 — Ana MC flips Capricorn → Aquarius under midpoint
# =============================================================================
def test_ana_mc_capricorn_under_uniform():
    r = attribute_sign_uniform_30(ANA["MC"])
    _assert_eq(r["sign"], "Capricorn", "Ana MC uniform_30")


def test_ana_mc_aquarius_under_midpoint():
    r = attribute_sign_true_sidereal_midpoint(ANA["MC"])
    _assert_eq(r["sign"], "Aquarius", "Ana MC midpoint")


# =============================================================================
# Requirement 3 — Mel Sun stays Gemini, Mel Moon stays Scorpio under midpoint
# =============================================================================
def test_mel_sun_gemini_under_both_modes():
    _assert_eq(attribute_sign_uniform_30(MEL["Sun"])["sign"],            "Gemini", "Mel Sun uniform")
    _assert_eq(attribute_sign_true_sidereal_midpoint(MEL["Sun"])["sign"], "Gemini", "Mel Sun midpoint")


def test_mel_moon_scorpio_under_both_modes():
    _assert_eq(attribute_sign_uniform_30(MEL["Moon"])["sign"],            "Scorpio", "Mel Moon uniform")
    _assert_eq(attribute_sign_true_sidereal_midpoint(MEL["Moon"])["sign"], "Scorpio", "Mel Moon midpoint")


# =============================================================================
# Requirement 4 — Pete signs remain stable across both modes
# =============================================================================
def test_pete_signs_stable():
    expected = {"ASC": "Sagittarius", "Sun": "Pisces", "Moon": "Aries", "MC": "Virgo"}
    for body, expected_sign in expected.items():
        u = attribute_sign_uniform_30(PETE[body])["sign"]
        m = attribute_sign_true_sidereal_midpoint(PETE[body])["sign"]
        _assert_eq(u, expected_sign, f"Pete {body} uniform")
        _assert_eq(m, expected_sign, f"Pete {body} midpoint")


# =============================================================================
# Requirement 5 — Ana Sun stays Aries, Ana Moon stays Sagittarius under midpoint
# =============================================================================
def test_ana_sun_aries_under_midpoint():
    _assert_eq(attribute_sign_true_sidereal_midpoint(ANA["Sun"])["sign"], "Aries", "Ana Sun midpoint")


def test_ana_moon_sagittarius_under_midpoint():
    _assert_eq(attribute_sign_true_sidereal_midpoint(ANA["Moon"])["sign"], "Sagittarius", "Ana Moon midpoint")


# =============================================================================
# Requirement 6 — degree_within_sign is between 0 and sign_width
# =============================================================================
def test_degree_within_sign_bounds_midpoint():
    """Sweep tropical longitudes 0-360° in 0.5° steps and verify bounds."""
    n = 720
    for i in range(n):
        trop = (i * 360.0 / n) % 360
        r = attribute_sign_true_sidereal_midpoint(trop)
        assert 0.0 <= r["degree_within_sign"] < r["sign_width"] + 1e-6, (
            f"At trop={trop:.3f}°: degree={r['degree_within_sign']:.4f} "
            f"out of bounds [0, {r['sign_width']:.4f}) for sign {r['sign']}"
        )


def test_degree_within_sign_bounds_uniform():
    """Uniform 30° should always yield degree in [0, 30)."""
    for i in range(720):
        trop = (i * 360.0 / 720) % 360
        r = attribute_sign_uniform_30(trop)
        assert 0.0 <= r["degree_within_sign"] < 30.0 + 1e-6, (
            f"uniform_30 trop={trop:.3f}°: degree={r['degree_within_sign']} out of bounds"
        )


# =============================================================================
# Requirement 7 — Pisces wrap-around works
# =============================================================================
def test_pisces_wrap_just_before_360():
    r = attribute_sign_true_sidereal_midpoint(359.99)
    _assert_eq(r["sign"], "Pisces", "Pisces just before 360")
    # Pisces starts at 354.93 → degree should be ~5.06
    assert 5.0 <= r["degree_within_sign"] <= 5.1, \
        f"Pisces 359.99° degree should be ~5.06, got {r['degree_within_sign']}"


def test_pisces_wrap_just_after_0():
    r = attribute_sign_true_sidereal_midpoint(5.00)
    _assert_eq(r["sign"], "Pisces", "Pisces just after 0")
    # 5.0° tropical → 5.0 + (360-354.93) = 10.07° within Pisces
    expected_deg = (5.00 - 354.93) % 360
    assert abs(r["degree_within_sign"] - expected_deg) < 1e-4, \
        f"Pisces 5.0° expected {expected_deg}, got {r['degree_within_sign']}"


def test_pisces_aries_boundary():
    # 25.61° is Aries entry; 25.60° should be Pisces.
    assert attribute_sign_true_sidereal_midpoint(25.60)["sign"] == "Pisces"
    assert attribute_sign_true_sidereal_midpoint(25.61)["sign"] == "Aries"


# =============================================================================
# Requirement 8 — boundary table tiles [0, 360) exactly (no gaps, no overlaps)
# =============================================================================
def test_midpoint_boundary_table_tiles_exactly():
    """Walk the boundary table; each end should equal the next start."""
    ordered = sorted(MIDPOINT_BOUNDARIES, key=lambda b: b[1])
    # Reorder so first is the sign whose start is right after Pisces wrap (Aries 25.61)
    # Verify each contiguous join:
    starts = {name: start for name, start, _ in MIDPOINT_BOUNDARIES}
    ends   = {name: end   for name, _, end   in MIDPOINT_BOUNDARIES}
    chain = [
        ("Aries", "Taurus"), ("Taurus", "Gemini"), ("Gemini", "Cancer"),
        ("Cancer", "Leo"), ("Leo", "Virgo"), ("Virgo", "Libra"),
        ("Libra", "Scorpio"), ("Scorpio", "Sagittarius"),
        ("Sagittarius", "Capricorn"), ("Capricorn", "Aquarius"),
        ("Aquarius", "Pisces"),
    ]
    for a, b in chain:
        assert abs(ends[a] - starts[b]) < 1e-6, \
            f"Gap between {a} end ({ends[a]}) and {b} start ({starts[b]})"
    # Pisces wraps: end == Aries start
    assert abs(ends["Pisces"] - starts["Aries"]) < 1e-6, "Pisces does not wrap to Aries"


# =============================================================================
# Requirement 9 — router default = Variant A (canonical), unknown mode → Variant A.
# (Build: midpoint13-variant-a-canonical-v1)
# Previously the default was uniform_30, then Variant B (midpoint12); the
# canonical default is now Variant A (midpoint13_variant_a).
# =============================================================================
def test_router_default_is_variant_a():
    r = attribute_sign(MEL["ASC"])
    _assert_eq(r["sign"], "Cancer", "default router should be Variant A — Mel ASC")
    # attribution_mode comes from the Variant A label
    from calculations.sign_attribution import MIDPOINT_MODEL_NAME_VARIANT_A
    _assert_eq(r["attribution_mode"], MIDPOINT_MODEL_NAME_VARIANT_A,
               "default attribution_mode = Variant A label")


def test_router_unknown_mode_falls_back_to_variant_a():
    r = attribute_sign(MEL["ASC"], mode="not_a_real_mode")
    _assert_eq(r["sign"], "Cancer",
               "unknown mode should fall back to canonical Variant A")


def test_router_explicit_midpoint():
    r = attribute_sign(MEL["ASC"], mode=MODE_TRUE_SIDEREAL_MIDPOINT)
    _assert_eq(r["sign"], "Cancer", "midpoint router")
    _assert_eq(r["attribution_mode"], MIDPOINT_MODEL_NAME, "midpoint mode label")


# =============================================================================
# CLI runner — for quick visual inspection without pytest
# =============================================================================
def main():
    tests = [
        ("Mel ASC Gemini under uniform",              test_mel_asc_gemini_under_uniform),
        ("Mel ASC Cancer under midpoint",             test_mel_asc_cancer_under_midpoint),
        ("Ana MC Capricorn under uniform",            test_ana_mc_capricorn_under_uniform),
        ("Ana MC Aquarius under midpoint",            test_ana_mc_aquarius_under_midpoint),
        ("Mel Sun Gemini in both",                    test_mel_sun_gemini_under_both_modes),
        ("Mel Moon Scorpio in both",                  test_mel_moon_scorpio_under_both_modes),
        ("Pete all signs stable",                     test_pete_signs_stable),
        ("Ana Sun Aries under midpoint",              test_ana_sun_aries_under_midpoint),
        ("Ana Moon Sagittarius under midpoint",       test_ana_moon_sagittarius_under_midpoint),
        ("degree_within_sign bounds midpoint",        test_degree_within_sign_bounds_midpoint),
        ("degree_within_sign bounds uniform",         test_degree_within_sign_bounds_uniform),
        ("Pisces wrap before 360",                    test_pisces_wrap_just_before_360),
        ("Pisces wrap after 0",                       test_pisces_wrap_just_after_0),
        ("Pisces/Aries boundary",                     test_pisces_aries_boundary),
        ("Boundary table tiles [0,360)",              test_midpoint_boundary_table_tiles_exactly),
        ("Router default is uniform",                 test_router_default_is_uniform),
        ("Router unknown → uniform fallback",         test_router_unknown_mode_falls_back_to_uniform),
        ("Router explicit midpoint",                  test_router_explicit_midpoint),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERR ] {name}: {type(e).__name__}: {e}")
            failed += 1
    print()
    print(f"Total: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
