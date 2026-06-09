"""Regression tests for the Variant-A (midpoint13_variant_a_v1) canonical engine.

Run:
    cd /app/backend && python -m pytest tests/test_variant_a_canonical.py -v
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculations.sign_attribution import (   # noqa: E402
    ASTROLOGY_ENGINE_VERSION,
    DEFAULT_MODE,
    ENGINE_VERSION_VARIANT_A,
    ENGINE_VERSION_VARIANT_B,
    MIDPOINT_BOUNDARIES_VARIANT_A,
    MODE_MIDPOINT12_VARIANT_B,
    MODE_MIDPOINT13_VARIANT_A,
    OPHIUCHUS_SIGN_NAME,
    SIGNS_12,
    SIGNS_13,
    attribute_sign,
    attribute_sign_midpoint12_variant_b,
    attribute_sign_midpoint13_variant_a,
    dual_compute,
)


def test_canonical_default_is_variant_a():
    assert DEFAULT_MODE == MODE_MIDPOINT13_VARIANT_A
    assert ASTROLOGY_ENGINE_VERSION == ENGINE_VERSION_VARIANT_A == "midpoint13_variant_a_v1"


def test_variant_a_sign_count_is_13():
    assert len(SIGNS_13) == 13
    assert OPHIUCHUS_SIGN_NAME in SIGNS_13
    assert OPHIUCHUS_SIGN_NAME not in SIGNS_12
    # Ophiuchus must sit between Scorpio and Sagittarius.
    sco = SIGNS_13.index("Scorpio")
    oph = SIGNS_13.index(OPHIUCHUS_SIGN_NAME)
    sag = SIGNS_13.index("Sagittarius")
    assert sco + 1 == oph == sag - 1


def test_variant_a_table_tiles_360():
    """Variant A's 13 bands must cover [0, 360) once (with Pisces wrap)."""
    total = 0.0
    for name, lo, hi in MIDPOINT_BOUNDARIES_VARIANT_A:
        if lo <= hi:
            total += hi - lo
        else:
            total += (360.0 - lo) + hi  # Pisces wrap
    assert abs(total - 360.0) < 1e-4, f"Variant-A bands sum to {total}, expected 360"


def test_variant_a_returns_ophiuchus_for_known_longitude():
    # Zodiacal 228° (mid-Ophiuchus) → tropical = 228 + SVP = 259.2836°
    out = attribute_sign(259.2836, mode=MODE_MIDPOINT13_VARIANT_A)
    assert out["sign"] == OPHIUCHUS_SIGN_NAME
    assert out["engine_version"] == ENGINE_VERSION_VARIANT_A


def test_variant_b_never_returns_ophiuchus():
    """Variant B (forensic) must merge Ophiuchus into Scorpio."""
    for trop in (255.0, 256.0, 257.0, 258.0, 260.0):
        out = attribute_sign_midpoint12_variant_b(trop)
        assert out["sign"] != OPHIUCHUS_SIGN_NAME, \
            f"Variant B should not produce Ophiuchus at trop={trop}"


def test_dual_compute_emits_both_variants():
    bundle = dual_compute(259.2836)
    assert bundle["canonical"]["engine_version"] == ENGINE_VERSION_VARIANT_A
    assert bundle["forensic_variant_b"]["engine_version"] == ENGINE_VERSION_VARIANT_B
    assert bundle["is_ophiuchus"] is True
    assert bundle["match_a_vs_b"] is False


def test_pete_full_chart_stamps_engine_version():
    """End-to-end: get_full_natal_chart must stamp Variant-A engine version
    and embed the Variant-B forensic payload alongside."""
    from calculations.astrology import get_full_natal_chart

    chart = get_full_natal_chart(
        birth_datetime=datetime(1968, 3, 31, 17, 55, 0),
        lat=3.1073, lon=101.6070,
        house_system="Equal",
    )
    assert chart["astrology_engine_version"] == ENGINE_VERSION_VARIANT_A
    assert chart["metadata"]["astrology_engine_version"] == ENGINE_VERSION_VARIANT_A
    fb = chart["forensic_variant_b"]
    assert fb["engine_version"] == ENGINE_VERSION_VARIANT_B
    # Pete's Mercury moved Aquarius (V-B) → Pisces (V-A) at the boundary.
    assert chart["planets"]["Mercury"]["sign"] == "Pisces"
    assert fb["planets"]["Mercury"]["sign"] == "Aquarius"


def test_ophiuchus_metadata_module_present():
    """The central Ophiuchus metadata module must expose canonical attrs."""
    from services.ophiuchus_metadata import get_ophiuchus_meta
    meta = get_ophiuchus_meta()
    assert meta["sign"] == "Ophiuchus"
    assert meta["element"] == "ether"
    assert meta["ruler"] == "Chiron"
    assert meta["glyph"] == "⛎"


def test_sign_registries_carry_ophiuchus():
    """All structural sign-keyed registries must include an Ophiuchus entry."""
    from services.forum_hd_mapping import ELEMENT_MAP, MODALITY_MAP
    from services.astrology_transit_evidence import SIGN_ELEMENT, SIGN_MODALITY
    from services.field_synthesis_engine import SIGN_RULER
    from services.astrology_domain_context import _RULERS

    for label, m in (
        ("ELEMENT_MAP", ELEMENT_MAP),
        ("MODALITY_MAP", MODALITY_MAP),
        ("SIGN_ELEMENT", SIGN_ELEMENT),
        ("SIGN_MODALITY", SIGN_MODALITY),
        ("SIGN_RULER", SIGN_RULER),
        ("_RULERS", _RULERS),
    ):
        assert "Ophiuchus" in m, f"{label} missing Ophiuchus entry"
