"""Variant-A sign attribution validity sweep.

Policy (per product owner, 2026-06-28):
  display_degree = absolute_longitude - sign_boundary_start
  Valid iff: 0 <= display_degree < sign_width
  Degrees > 30° are LEGITIMATE for wide constellations
  (Virgo ~49.71°, Taurus ~36.86°, Pisces ~41.99°).
  No clamping, no proportional rescaling, no wrap.
"""
from __future__ import annotations

import pytest

from calculations.sign_attribution import (
    MIDPOINT_BOUNDARIES_VARIANT_A,
    attribute_sign_midpoint13_variant_a,
)


def _expected_widths():
    out = {}
    for name, start, end in MIDPOINT_BOUNDARIES_VARIANT_A:
        if start <= end:
            out[name] = end - start
        else:
            out[name] = (360.0 - start) + end
    return out


def test_variant_a_widths_match_athen_table():
    widths = _expected_widths()
    # Sample known wide constellations from the Athen / Sharatan table.
    assert abs(widths["Virgo"]    - 49.7135) < 0.01
    assert abs(widths["Taurus"]   - 36.8589) < 0.01
    assert abs(widths["Pisces"]   - 41.9897) < 0.01
    # Total span must close at 360°.
    assert abs(sum(widths.values()) - 360.0) < 1e-6


@pytest.mark.parametrize("step", [0.5])
def test_sweep_no_invalid_degrees(step):
    """Sweep tropical longitudes [0, 360) and verify every attribution
    returns degree_within_sign in [0, sign_width). No clamping, no
    artificial 30° cap."""
    widths = _expected_widths()
    lng = 0.0
    seen_above_30 = 0
    while lng < 360.0:
        r = attribute_sign_midpoint13_variant_a(lng)
        sign  = r["sign"]
        deg   = r["degree_within_sign"]
        width = r["sign_width"]
        # ── Validity rule ────────────────────────────────────────
        assert 0.0 <= deg, f"negative degree at lng={lng}: {r}"
        assert deg < width + 1e-6, (
            f"degree {deg} >= sign_width {width} at lng={lng}: {r}"
        )
        assert abs(width - widths[sign]) < 1e-3
        # display_degree must mirror degree_within_sign (no rescaling)
        assert abs(r["display_degree"] - deg) < 1e-6
        if deg > 30.0:
            seen_above_30 += 1
        lng += step
    # Sanity: wide constellations MUST yield some degrees > 30°.
    assert seen_above_30 > 0, (
        "Variant-A must produce degrees > 30° in wide constellations."
    )


def test_virgo_37_is_valid_under_variant_a():
    """Concrete instance: a planet at the tropical longitude that puts
    it 37° into Virgo's ~49.71° band is legitimate, not a bug."""
    # Find Virgo entry
    name, start, end = next(
        (n, s, e) for (n, s, e) in MIDPOINT_BOUNDARIES_VARIANT_A if n == "Virgo"
    )
    width = end - start
    target_deg = 37.0
    assert target_deg < width, "Virgo's width must accommodate 37° for this test"
    lng = (start + target_deg) % 360.0
    r = attribute_sign_midpoint13_variant_a(lng)
    assert r["sign"] == "Virgo"
    assert abs(r["degree_within_sign"] - target_deg) < 1e-3
    assert abs(r["display_degree"] - target_deg) < 1e-3
    # And the result must NOT be clamped/rescaled to 30°.
    assert r["display_degree"] > 30.0
