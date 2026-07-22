"""Tests for the Life-Cycle + Life-Milestone plug-ins (engines 4 + 5)."""
from __future__ import annotations
from datetime import date, datetime, timezone as _tz

from services.life_cycle_timing_engine import LifeCycleTimingEngine, _hits_for_anchor, _ANCHORS
from services.life_milestone_engine    import LifeMilestoneTimingEngine
from services.timing_evidence_layer    import build_default_layer


BIRTH = datetime(1968, 3, 31, 17, 55, tzinfo=_tz.utc)  # Pete


def _chart():
    return {
        "angles":  {"asc": {"sign":"Cancer","longitude":110.0,"degree":10.0},
                     "mc": {"sign":"Aries","longitude":20.0,"degree":0.0},
                     "ic": {"sign":"Libra","longitude":200.0,"degree":0.0},
                     "dc": {"sign":"Capricorn","longitude":290.0,"degree":0.0}},
        "houses":  {"formatted_cusps": [
            {"house":i,"sign":"Aries","degree":0.0,"cusp":30.0*(i-1)}
            for i in range(1,13)]},
        "planets": {"Sun":{"sign":"Pisces","longitude":340.0,"house":9,"degree":22.0},
                     "Moon":{"sign":"Leo","longitude":131.0,"house":2,"degree":11.0},
                     "Mercury":{"sign":"Pisces","longitude":355.0,"house":9},
                     "Venus":{"sign":"Aries","longitude":25.0,"house":10}},
    }


# ------ Life Cycle ---------------------------------------------------------
def test_life_cycle_anchors_include_all_five_engines():
    ids = {a["id"] for a in _ANCHORS}
    assert ids == {"saturn_return","uranus_opposition","chiron_return",
                    "nodal_return","jupiter_return"}


def test_life_cycle_returns_active_window_when_inside_band():
    # For a 1968-03-31 birth on 1998-01-01, age ≈ 29.75 → inside first
    # Saturn return band (29.457 ± 1.5).
    ev = LifeCycleTimingEngine().compute(
        natal_chart=_chart(), birth_datetime_utc=BIRTH,
        target_date=date(1998, 1, 1))
    assert ev.active is True
    active_ids = [w["anchor_id"] for w in ev.details["active_windows"]]
    assert "saturn_return" in active_ids


def test_life_cycle_next_hit_is_populated_when_quiet():
    # Age ~10 at 1978-06-01 → no anchor active but next hit exists.
    ev = LifeCycleTimingEngine().compute(
        natal_chart=_chart(), birth_datetime_utc=BIRTH,
        target_date=date(1978, 6, 1))
    assert ev.details["next_hit"] is not None
    assert ev.details["next_hit"]["years_from_now"] > 0


# ------ Life Milestone -----------------------------------------------------
def test_milestone_engine_silent_without_events():
    ev = LifeMilestoneTimingEngine().compute(
        natal_chart=_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026,6,1), extras={})
    assert ev.active is False


def test_milestone_engine_matches_events_to_profection_houses():
    events = [
        {"date":"1998-06-15","title":"first co bought","kind":"life_event"},
        {"date":"2010-11-01","title":"book launched",  "kind":"recognition"},
        {"date":"2019-03-10","title":"moved country",  "kind":"life_event"},
    ]
    ev = LifeMilestoneTimingEngine().compute(
        natal_chart=_chart(), birth_datetime_utc=BIRTH,
        target_date=date(2026,6,1), extras={"events":events})
    assert ev.active is True
    d = ev.details
    assert d["events_ingested"] == 3
    for m in d["matches"]:
        assert m["profection_house"] in range(1,13)
    assert ev.confidence == "conditional"


# ------ Aggregator ---------------------------------------------------------
def test_default_layer_now_has_five_engines():
    layer = build_default_layer()
    assert layer.engine_ids == [
        "annual_profection", "transits", "zodiacal_releasing",
        "life_cycle", "life_milestones",
    ]
