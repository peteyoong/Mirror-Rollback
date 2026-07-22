"""Tests for the second (Transits) and third (ZR scaffold) TimingEngine plug-ins."""
from __future__ import annotations

from datetime import date, datetime, timezone as _tz

import pytest

from services.timing_engine_protocol   import TimingEvidence
from services.transit_timing_engine    import (
    BUILD_MARKER as TR_MARKER, TransitTimingEngine,
    _aspect_between, _score,
)
from services.zodiacal_releasing_engine import (
    BUILD_MARKER as ZR_MARKER, ZodiacalReleasingScaffoldEngine,
    _walk_periods, _YEARS_PER_SIGN,
)
from services.timing_evidence_layer     import build_default_layer


BIRTH = datetime(1968, 3, 31, 17, 55, tzinfo=_tz.utc)   # Pete Yoong

def _pete_like_chart():
    """Minimal chart that satisfies both engines' interfaces."""
    return {
        "angles": {
            "asc": {"sign":"Cancer",    "longitude":110.0, "degree":10.0},
            "mc":  {"sign":"Aries",     "longitude":20.0,  "degree":0.0},
            "ic":  {"sign":"Libra",     "longitude":200.0, "degree":0.0},
            "dc":  {"sign":"Capricorn", "longitude":290.0, "degree":0.0},
        },
        "houses": {"formatted_cusps": [
            {"house": i, "sign": "Aries", "degree": 0.0, "cusp": 30.0*(i-1)}
            for i in range(1, 13)
        ]},
        "planets": {
            "Sun":    {"sign":"Pisces","longitude":340.0,"house":9,"degree":22.0},
            "Moon":   {"sign":"Leo",   "longitude":131.0,"house":2,"degree":11.0},
            "Mercury":{"sign":"Pisces","longitude":355.0,"house":9,"degree":25.0},
            "Venus":  {"sign":"Aries", "longitude":25.0, "house":10,"degree":25.0},
            "Mars":   {"sign":"Aquarius","longitude":301.0,"house":8,"degree":1.0},
            "Jupiter":{"sign":"Virgo", "longitude":170.0,"house":3,"degree":30.0,"retrograde":True},
            "Saturn": {"sign":"Pisces","longitude":347.0,"house":9,"degree":17.0},
            "Uranus": {"sign":"Virgo", "longitude":156.0,"house":3,"degree":6.0,"retrograde":True},
            "Neptune":{"sign":"Virgo", "longitude":163.0,"house":3,"degree":13.0,"retrograde":True},
            "Pluto":  {"sign":"Leo",   "longitude":120.0,"house":2,"degree":0.0},
        },
    }


# ---- Transit engine ---------------------------------------------------------
def test_transit_engine_aspect_math():
    assert _aspect_between(  0.0,   0.0)["aspect"] == "conjunction"
    assert _aspect_between(180.0,   0.0)["aspect"] == "opposition"
    assert _aspect_between( 91.0,   0.0)["aspect"] == "square"
    assert _aspect_between(  8.0,   0.0) is None       # outside 6° orb


def test_transit_engine_score_weights_slow_planets_higher():
    assert _score("Saturn", 0.0) > _score("Sun", 0.0)
    assert _score("Pluto",  1.0) > _score("Mars",   1.0)


def test_transit_engine_returns_evidence_shape():
    e = TransitTimingEngine()
    ev = e.compute(natal_chart=_pete_like_chart(), birth_datetime_utc=BIRTH,
                    target_date=date(2026, 6, 1))
    assert isinstance(ev, TimingEvidence)
    assert ev.engine_id == "transits"
    assert ev.engine_marker == TR_MARKER
    d = ev.details
    assert "aspects_top" in d and "loci_measured" in d
    assert "target_date" in d
    # loci must include the 4 angles even when the Lord of the Year is absent
    assert any("Ascendant" in l for l in d["loci_measured"])


def test_transit_engine_silent_when_no_natal_loci():
    empty = {"angles": {}, "planets": {}, "houses": {}}
    ev = TransitTimingEngine().compute(
        natal_chart=empty, birth_datetime_utc=BIRTH,
        target_date=date(2026, 6, 1))
    assert ev.active is False
    assert ev.confidence == "low"


# ---- ZR engine --------------------------------------------------------------
def test_zr_walk_periods_arithmetic():
    # Start from Aries (15y). At 10 years elapsed we should still be in Aries
    # with 5 years remaining.
    sign, rem, elapsed_at_start, idx = _walk_periods("Aries", 10.0)
    assert sign == "Aries"
    assert rem == pytest.approx(5.0)
    assert elapsed_at_start == 0.0
    assert idx == 0

    # At 16 years elapsed, Aries is done (15y), we're now 1y into Taurus (8y).
    sign, rem, elapsed_at_start, idx = _walk_periods("Aries", 16.0)
    assert sign == "Taurus"
    assert rem == pytest.approx(7.0)
    assert elapsed_at_start == 15.0
    assert idx == 1


def test_zr_engine_computes_from_lots_fallback():
    """No `lots` block on chart → engine should still compute Lot signs
    from Sun/Moon/ASC/Venus and produce active evidence."""
    ev = ZodiacalReleasingScaffoldEngine().compute(
        natal_chart=_pete_like_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026, 6, 1))
    assert ev.active is True
    assert ev.engine_id == "zodiacal_releasing"
    assert ev.engine_marker == ZR_MARKER
    d = ev.details
    # Both Spirit and Fortune should be present
    assert d.get("spirit") is not None
    assert d.get("fortune") is not None
    for k in ("current_L1_sign", "current_L1_ruler",
              "period_years", "period_start_date", "period_end_date"):
        assert k in d["spirit"], f"spirit missing {k}"
    # L1 sign must belong to the 12 signs (Ophiuchus should be folded).
    assert d["spirit"]["current_L1_sign"] in _YEARS_PER_SIGN


def test_zr_years_remaining_within_period_span():
    ev = ZodiacalReleasingScaffoldEngine().compute(
        natal_chart=_pete_like_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026, 6, 1))
    for lot in ("spirit", "fortune"):
        b = ev.details[lot]
        assert 0.0 <= b["years_remaining"] <= b["period_years"]
        assert 0.0 <= b["years_elapsed_in_period"] <= b["period_years"]


# ---- Aggregator registration -----------------------------------------------
def test_default_layer_now_has_three_engines():
    layer = build_default_layer()
    assert layer.engine_ids == [
        "annual_profection", "transits", "zodiacal_releasing"]


def test_aggregator_returns_all_three_signals():
    layer = build_default_layer()
    agg = layer.aggregate(
        natal_chart=_pete_like_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026, 6, 1))
    assert set(agg["signals"].keys()) == {
        "annual_profection", "transits", "zodiacal_releasing"}
    # Confidence vocabulary honoured
    for sid, sig in agg["signals"].items():
        assert sig["confidence"] in ("high","moderate","conditional","low")
        assert sig["engine_marker"]
