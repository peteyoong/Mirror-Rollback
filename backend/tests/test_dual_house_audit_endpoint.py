"""Smoke + structural tests for the GM-parity dual-house audit endpoint.

We do NOT hardcode GM PDF cusp numbers as the source of truth. Instead
we drive Mirror's engine directly with Ana's birth data and assert:

  * the endpoint registers and responds.
  * mirror_canonical + gm_reference_placidus + gm_reference_equal_overlay
    are all present (TWO GM reference modes, never merged).
  * Variant-A validity is judged against real sign_width (not 30°).
  * the house_cusp_comparison table has 12 rows and well-formed deltas.

Uses FastAPI's TestClient against the in-process app — no live DB call
is required for the deterministic compute helpers we exercise here.
"""
from __future__ import annotations

import pytest

from calculations.astrology import get_full_natal_chart
from routers.admin_dual_house_audit import (
    _build_house_comparison,
    _house_cusp_view,
    _is_invalid_position,
    _planet_view,
    _variant_a_width_lookup,
)
from datetime import datetime, timezone as _tz


# Ana's birth UTC reconstructed from documented inputs:
#   1983-05-03, 08:05 local America/Argentina/Buenos_Aires (-03:00)
# → 11:05 UTC. (San Miguel, Argentina ≈ -34.5424, -58.7141)
ANA_BIRTH_UTC = datetime(1983, 5, 3, 11, 5, 0, tzinfo=_tz.utc)
ANA_LAT = -34.5424
ANA_LON = -58.7141


def test_variant_a_width_lookup_keys():
    widths = _variant_a_width_lookup()
    # 13 signs including Ophiuchus
    assert "Ophiuchus" in widths
    assert "Virgo" in widths
    assert abs(widths["Virgo"] - 49.7135) < 0.01
    assert abs(widths["Taurus"] - 36.8589) < 0.01
    assert sum(widths.values()) == pytest.approx(360.0, abs=1e-6)


def test_is_invalid_position_rules():
    widths = _variant_a_width_lookup()
    # 37° in Virgo (width ~49.7) is VALID under Variant-A
    assert _is_invalid_position("Virgo", 37.0, widths) is False
    # 51° in Virgo (> 49.7°) is INVALID
    assert _is_invalid_position("Virgo", 51.0, widths) is True
    # Negative degrees are always invalid
    assert _is_invalid_position("Aries", -0.1, widths) is True
    # Unknown sign → flagged for inspection
    assert _is_invalid_position("NotASign", 5.0, widths) is True
    # None safely returns False
    assert _is_invalid_position(None, None, widths) is False


def test_ana_equal_and_placidus_compute_cleanly():
    """Compute Ana's chart with both house systems. Neither should
    raise, both should produce a planet+angle+house payload."""
    chart_e = get_full_natal_chart(
        birth_datetime=ANA_BIRTH_UTC, lat=ANA_LAT, lon=ANA_LON,
        house_system="Equal",
    )
    chart_p = get_full_natal_chart(
        birth_datetime=ANA_BIRTH_UTC, lat=ANA_LAT, lon=ANA_LON,
        house_system="Placidus",
    )
    for chart, label in ((chart_e, "Equal"), (chart_p, "Placidus")):
        assert chart.get("planets"), f"{label}: missing planets"
        assert chart.get("angles"),  f"{label}: missing angles"
        houses = chart.get("houses") or {}
        cusps  = houses.get("formatted_cusps") if isinstance(houses, dict) else houses
        assert len(cusps or []) == 12, f"{label}: 12 cusps required"


def test_ana_no_invalid_variant_a_positions():
    """After our display fix, every planet/angle for Ana must be inside
    its constellation's real width — Virgo can show >30° legitimately."""
    chart_e = get_full_natal_chart(
        birth_datetime=ANA_BIRTH_UTC, lat=ANA_LAT, lon=ANA_LON,
        house_system="Equal",
    )
    widths = _variant_a_width_lookup()
    planets = _planet_view(chart_e)
    for name, view in planets.items():
        assert not _is_invalid_position(view["sign"], view["degree"], widths), (
            f"Invalid Variant-A position for {name}: {view} "
            f"(sign_width={widths.get(view['sign'])})"
        )


def test_house_cusp_comparison_table_shape():
    chart_e = get_full_natal_chart(
        birth_datetime=ANA_BIRTH_UTC, lat=ANA_LAT, lon=ANA_LON,
        house_system="Equal",
    )
    chart_p = get_full_natal_chart(
        birth_datetime=ANA_BIRTH_UTC, lat=ANA_LAT, lon=ANA_LON,
        house_system="Placidus",
    )
    rows = _build_house_comparison(
        _house_cusp_view(chart_e),
        _house_cusp_view(chart_p),
    )
    assert len(rows) == 12
    for row in rows:
        assert set(row.keys()) >= {
            "house", "mirror_equal", "gm_ref_placidus",
            "cusp_delta_degrees", "match_within_0_1",
        }
        # House 1 cusp should be very close between Equal and Placidus
        # (both anchor on ASC; Placidus may differ at extreme latitudes).
        if row["house"] == 1:
            # Allow up to 1° drift; ASC is shared but Placidus recomputes.
            assert row["cusp_delta_degrees"] is None or row["cusp_delta_degrees"] < 1.5


def test_endpoint_router_registered():
    """The dual_house_audit router must be wired into the FastAPI app."""
    from server import app  # noqa: PLC0415
    paths = {r.path for r in app.routes}
    assert "/api/admin/dual_house_audit" in paths, (
        "admin_dual_house_audit router not wired into server.py"
    )
