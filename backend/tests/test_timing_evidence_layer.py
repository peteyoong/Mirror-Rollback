"""Tests for the Timing Evidence Layer aggregator + protocol (Phase 4)."""
from __future__ import annotations

from datetime import date, datetime, timezone as _tz
from typing import Any, Dict, Optional

import pytest

from services.timing_engine_protocol   import (
    Confidence, TimingEngine, TimingEvidence,
)
from services.timing_evidence_layer    import (
    AnnualProfectionTimingEngine, TimingEvidenceLayer, build_default_layer,
)


def _mk_chart():
    signs = ["Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn",
             "Aquarius","Pisces","Aries","Taurus","Gemini","Cancer"]
    return {
        "angles":  {"asc": {"sign": "Leo", "longitude": 0.0, "degree": 0.0}},
        "houses":  {"formatted_cusps": [
            {"house": i, "sign": s, "degree": 0.0, "cusp": 30.0 * (i-1)}
            for i, s in enumerate(signs, 1)
        ]},
        "planets": {"Sun": {"sign":"Leo","longitude":110.0,"house":1,"degree":10.0}},
    }


BIRTH = datetime(1990, 6, 15, tzinfo=_tz.utc)


# --- Protocol -----------------------------------------------------------------
def test_timing_evidence_public_dict_shape():
    ev = TimingEvidence(
        engine_id="x", name="X", meaning="m",
        confidence="moderate", supporting_signals=["a"], details={"k": 1},
        engine_marker="mk-1",
    )
    d = ev.to_public_dict()
    assert d == {
        "engine_id": "x", "name": "X", "meaning": "m",
        "confidence": "moderate", "supporting_signals": ["a"],
        "details": {"k": 1}, "engine_marker": "mk-1", "active": True,
    }


def test_abstract_engine_cannot_be_instantiated_without_compute():
    with pytest.raises(TypeError):
        TimingEngine()   # type: ignore[abstract]


# --- Aggregator ---------------------------------------------------------------
def test_default_layer_registers_annual_profection():
    layer = build_default_layer()
    assert "annual_profection" in layer.engine_ids


def test_aggregate_produces_annual_profection_signal():
    layer = build_default_layer()
    agg = layer.aggregate(
        natal_chart=_mk_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026, 1, 1),
    )
    assert "annual_profection" in agg["signals"]
    sig = agg["signals"]["annual_profection"]
    for k in ("engine_id", "name", "meaning", "confidence",
              "supporting_signals", "details", "active"):
        assert k in sig, f"missing {k}"
    assert sig["confidence"] == "moderate"
    assert sig["details"]["activated_house"] in range(1, 13)
    assert sig["details"]["interpretation"]["tone_contract"]["observational_not_predictive"] is True


def test_register_is_idempotent_and_order_preserving():
    layer = TimingEvidenceLayer()
    e1 = AnnualProfectionTimingEngine()
    e2 = AnnualProfectionTimingEngine()
    layer.register(e1).register(e2)
    # Same engine_id → only one entry survives.
    assert layer.engine_ids == ["annual_profection"]


def test_broken_engine_reports_inactive_and_is_hidden_by_default():
    class Boom(TimingEngine):
        engine_id = "boom"
        engine_marker = "boom-v1"
        def compute(self, **kw):
            raise RuntimeError("nope")

    layer = TimingEvidenceLayer().register(Boom())
    agg1 = layer.aggregate(
        natal_chart=_mk_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026, 1, 1))
    assert "boom" not in agg1["signals"]           # hidden by default

    agg2 = layer.aggregate(
        natal_chart=_mk_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026, 1, 1), include_inactive=True)
    assert "boom" in agg2["signals"]
    assert agg2["signals"]["boom"]["active"] is False
    assert agg2["signals"]["boom"]["confidence"] == "low"


def test_signals_endpoint_registered():
    from server import app                                             # noqa: PLC0415
    paths = {r.path for r in app.routes}
    assert "/api/timeline/signals/current" in paths
