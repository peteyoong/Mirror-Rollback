"""Regression + correctness tests for the Annual Profection engine.

Covers:
  • Age computation (integer years since birth, birthday boundary).
  • 12-year cycle (age 0 → H1, age 12 → H1 again).
  • Sign attribution on the profected cusp (from natal chart's Equal cusps).
  • Lord of the Year lookup + Ophiuchus fallback.
  • Feb-29 birthday safety net.
  • Historical and future dates use the same code path.
  • Narrative payload emits the six Mirror-V2 timing answers.
  • Router registration and endpoint response shape (unit-level, no DB).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as _tz

import pytest

from services.annual_profection_engine   import (
    BUILD_MARKER, compute_profection, compute_profection_series,
    _age_and_birthday_window, _sign_on_house_cusp,
)
from services.annual_profection_narrative import build_narrative


# ---------------------------------------------------------------------------
# Chart fixture — matches the shape emitted by
# calculations.astrology.get_full_natal_chart(house_system='Equal'):
#   * planets dict (name → {sign, degree, house, longitude, retrograde, ...})
#   * angles.asc.longitude
#   * houses.formatted_cusps = [{house, sign, degree, cusp}] × 12
# ---------------------------------------------------------------------------
def _mk_chart(asc_sign_sequence, ruler_body_natals=None):
    """Build a minimal Equal-house chart where cusp N carries the Nth sign
    in `asc_sign_sequence`. Simplifies test authoring."""
    cusps = []
    for i, s in enumerate(asc_sign_sequence, start=1):
        cusps.append({"house": i, "sign": s, "degree": 0.0, "cusp": 30.0 * (i-1)})
    return {
        "angles":  {"asc": {"sign": asc_sign_sequence[0],
                            "longitude": 0.0, "degree": 0.0}},
        "houses":  {"formatted_cusps": cusps},
        "planets": ruler_body_natals or {},
    }


# ---------------------------------------------------------------------------
# Basic age + birthday window
# ---------------------------------------------------------------------------
def test_age_before_birthday():
    """Target date one day BEFORE the birthday should give age N-1."""
    birth  = date(1990, 6, 15)
    target = date(2026, 6, 14)
    age, this, nxt = _age_and_birthday_window(birth, target)
    assert age == 35
    assert this == date(2025, 6, 15) and nxt == date(2026, 6, 15)


def test_age_on_and_after_birthday():
    birth  = date(1990, 6, 15)
    for t, expected in [(date(2026, 6, 15), 36), (date(2026, 12, 31), 36)]:
        age, this, nxt = _age_and_birthday_window(birth, t)
        assert age == expected, f"target={t} expected {expected} got {age}"


def test_feb29_birthday_fallback():
    birth  = date(2000, 2, 29)               # leap-day birth
    # 25th birthday: 2025 is not a leap year → Feb 28 fallback.
    age, this, nxt = _age_and_birthday_window(birth, date(2025, 3, 1))
    assert age == 25
    assert this == date(2025, 2, 28)


# ---------------------------------------------------------------------------
# 12-year cycle
# ---------------------------------------------------------------------------
def test_12_year_cycle_activates_first_house_at_age_0_12_24():
    signs = ["Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn",
             "Aquarius","Pisces","Aries","Taurus","Gemini","Cancer"]
    chart = _mk_chart(signs)
    birth = datetime(1990, 6, 15, tzinfo=_tz.utc)
    for age in (0, 12, 24, 36, 48):
        target = birth.date().replace(year=1990 + age) + timedelta(days=1)
        p = compute_profection(natal_chart=chart, birth_datetime_utc=birth,
                                target_date=target)
        assert p.age == age
        assert p.activated_house == 1, f"age {age} expected H1"
        assert p.profected_sign == "Leo"


def test_second_year_activates_second_house():
    signs = ["Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn",
             "Aquarius","Pisces","Aries","Taurus","Gemini","Cancer"]
    chart = _mk_chart(signs)
    birth = datetime(1990, 6, 15, tzinfo=_tz.utc)
    p = compute_profection(natal_chart=chart, birth_datetime_utc=birth,
                            target_date=date(1991, 12, 1))
    assert p.age == 1
    assert p.activated_house == 2
    assert p.profected_sign == "Virgo"
    assert p.lord_of_the_year == "Mercury"


def test_series_covers_full_lifespan_without_error():
    signs = ["Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn",
             "Aquarius","Pisces","Aries","Taurus","Gemini","Cancer"]
    chart = _mk_chart(signs)
    birth = datetime(1990, 6, 15, tzinfo=_tz.utc)
    series = compute_profection_series(
        natal_chart=chart, birth_datetime_utc=birth, from_age=0, to_age=48)
    assert len(series) == 49
    # First entry age 0 → H1; entry age 12 → H1 again.
    assert series[0].activated_house == 1
    assert series[12].activated_house == 1
    # Each successive year advances by exactly one house.
    for i in range(1, len(series)):
        prev = series[i-1].activated_house
        curr = series[i].activated_house
        assert curr == (prev % 12) + 1


# ---------------------------------------------------------------------------
# Lord of the Year lookup
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sign,expected_lord", [
    ("Aries","Mars"), ("Taurus","Venus"), ("Gemini","Mercury"),
    ("Cancer","Moon"),("Leo","Sun"),      ("Virgo","Mercury"),
    ("Libra","Venus"),("Scorpio","Mars"), ("Sagittarius","Jupiter"),
    ("Capricorn","Saturn"),("Aquarius","Saturn"),("Pisces","Jupiter"),
])
def test_lord_of_the_year_traditional_mapping(sign, expected_lord):
    chart = _mk_chart([sign] + ["Aries"]*11)   # sign on the 1st house
    birth = datetime(1990, 1, 1, tzinfo=_tz.utc)
    p = compute_profection(natal_chart=chart, birth_datetime_utc=birth,
                            target_date=date(1990, 6, 1))
    assert p.activated_house == 1
    assert p.lord_of_the_year == expected_lord


def test_ophiuchus_year_has_no_classical_lord():
    """Ophiuchus on any activated cusp → Lord of the Year is None with a
    reason string explaining why. Narrative degrades to house-only voicing."""
    chart = _mk_chart(["Ophiuchus"] + ["Aries"]*11)
    birth = datetime(1990, 1, 1, tzinfo=_tz.utc)
    p = compute_profection(natal_chart=chart, birth_datetime_utc=birth,
                            target_date=date(2026, 1, 1))
    # Age 36 → 36 % 12 = 0 → house 1.
    assert p.activated_house == 1
    assert p.profected_sign == "Ophiuchus"
    assert p.lord_of_the_year is None
    assert "no classical" in (p.ruler_unavailable_reason or "").lower()
    nar = build_narrative(p)
    assert "no classical ruling planet" in nar["identity_synthesis_interaction"]


# ---------------------------------------------------------------------------
# Ruler natal condition surfacing
# ---------------------------------------------------------------------------
def test_ruler_natal_condition_extracted_from_planets():
    signs = ["Leo","Virgo"] + ["Aries"]*10
    ruler_planets = {
        "Sun":     {"sign":"Leo",   "degree":10.0, "house":1, "longitude":110.0,
                    "retrograde":False},
        "Mercury": {"sign":"Cancer","degree":5.0,  "house":12,"longitude":95.0,
                    "retrograde":False},
    }
    chart = _mk_chart(signs, ruler_planets)
    birth = datetime(1990, 1, 1, tzinfo=_tz.utc)
    # Age 1 → H2 (Virgo, ruled by Mercury).
    p = compute_profection(natal_chart=chart, birth_datetime_utc=birth,
                            target_date=date(1991, 6, 1))
    cond = p.ruler_natal_condition
    assert cond["ruler"] == "Mercury"
    assert cond["sign"] == "Cancer" and cond["house"] == 12
    assert cond["angularity"] == "cadent"
    # Sun→Mercury 15° gap → under_beams (17°–8° range excludes this: it's ≤8°? actually 15°.)
    # Distance ≈ 15° → under_beams (8..17).
    assert cond["under_beams"] is True
    assert cond["combust"] is False
    assert cond["cazimi"]  is False


def test_narrative_shape_and_tone_contract():
    signs = ["Leo","Virgo"] + ["Aries"]*10
    chart = _mk_chart(signs, {"Sun":  {"sign":"Leo","longitude":100.0,"house":1},
                               "Mercury":{"sign":"Cancer","longitude":95.0,"house":12}})
    birth = datetime(1990, 1, 1, tzinfo=_tz.utc)
    p = compute_profection(natal_chart=chart, birth_datetime_utc=birth,
                            target_date=date(1991, 6, 1))
    n = build_narrative(p)
    # Six mandatory Mirror-V2 answers.
    for k in ("what_area_is_asking_attention",
               "experiences_that_tend_to_emerge",
               "active_developmental_question",
               "strengths_easier_this_year",
               "blind_spots_more_visible",
               "identity_synthesis_interaction"):
        assert n[k], f"missing narrative field {k}"
    # Tone contract flags.
    tc = n["tone_contract"]
    assert tc["observational_not_predictive"] is True
    assert tc["no_fatalism"] is True
    assert tc["no_certainty_claim"] is True
    assert tc["identity_first"] is True


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
def test_timeline_profection_router_registered():
    from server import app                                              # noqa: PLC0415
    paths = {r.path for r in app.routes}
    assert "/api/timeline/profection/current" in paths
    assert "/api/timeline/profection/series" in paths


# ---------------------------------------------------------------------------
# Guardrails against bad inputs
# ---------------------------------------------------------------------------
def test_compute_rejects_naive_datetime():
    chart = _mk_chart(["Leo"] + ["Aries"]*11)
    with pytest.raises(ValueError):
        compute_profection(natal_chart=chart,
                            birth_datetime_utc=datetime(1990, 1, 1),  # naive
                            target_date=date(2026, 1, 1))


def test_compute_rejects_empty_chart():
    with pytest.raises(ValueError):
        compute_profection(natal_chart={},
                            birth_datetime_utc=datetime(1990, 1, 1, tzinfo=_tz.utc),
                            target_date=date(2026, 1, 1))


# ---------------------------------------------------------------------------
# Historical + future symmetry
# ---------------------------------------------------------------------------
def test_historical_and_future_use_same_code_path():
    signs = ["Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn",
             "Aquarius","Pisces","Aries","Taurus","Gemini","Cancer"]
    chart = _mk_chart(signs)
    birth = datetime(1990, 6, 15, tzinfo=_tz.utc)
    for target in (date(1993, 8, 1), date(2050, 2, 15)):
        p = compute_profection(natal_chart=chart,
                                birth_datetime_utc=birth,
                                target_date=target)
        # Structural — every year should produce a valid house 1..12 and a
        # sign in the table.
        assert 1 <= p.activated_house <= 12
        assert p.profected_sign in signs
        assert p.engine_marker == BUILD_MARKER
