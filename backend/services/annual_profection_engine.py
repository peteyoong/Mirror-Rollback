"""Annual Profection Engine — Timeline Intelligence V2 · Phase 1
================================================================
Surface marker: annual-profection-engine-v1

Canonical annual profection calculator for Personal Mirror.

Model
-----
Traditional Hellenistic annual profections, applied to Mirror's canonical
astrological frame:

    zodiac        = Variant-A True Sidereal (Sharatan SVP = 31.2836°)
    houses        = Equal (Mirror canonical, Asc = 1st)
    profection    = 1st house at age 0, advances one house per birthday,
                    12-year repeating cycle
    Lord of Year  = traditional (Sun–Saturn) ruler of the sign that sits
                    on the activated house cusp

The engine is deterministic. No LLM. No randomness. Same inputs → same
output every call. It is a pure `TimingEngine` implementation (Phase 4
protocol) — no I/O, no DB access — the caller supplies the natal chart
and the target date.

Ophiuchus policy
----------------
If the activated house falls on Ophiuchus (Mirror's 13th Variant-A
constellation), the ruler slot is filled with `None` and a
`ruler_unavailable_reason` field explains that no classical dominion is
assigned. The rest of the profection block still renders — the year is
observationally valid, just without a Lord of the Year label.

Output shape
------------
All outputs are JSON-serialisable dicts. See `_ProfectionOutput` below.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone as _tz
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "annual-profection-engine-v1"

# ---------------------------------------------------------------------------
# Rulership tables (Mirror uses traditional 7-planet rulership for Lords of
# the Year; modern outer-planet rulers are surfaced separately for context.)
# ---------------------------------------------------------------------------
TRAD_RULER = {
    "Aries": "Mars",       "Taurus": "Venus",      "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",           "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",      "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn",   "Pisces": "Jupiter",
    "Ophiuchus": None,     # No classical dominion — Mirror leaves blank.
}
MODERN_RULER = {**TRAD_RULER,
    "Scorpio": "Pluto", "Aquarius": "Uranus", "Pisces": "Neptune"}

ELEMENT  = {"Aries":"Fire","Leo":"Fire","Sagittarius":"Fire",
            "Taurus":"Earth","Virgo":"Earth","Capricorn":"Earth",
            "Gemini":"Air","Libra":"Air","Aquarius":"Air",
            "Cancer":"Water","Scorpio":"Water","Pisces":"Water",
            "Ophiuchus":"—"}
MODALITY = {"Aries":"Cardinal","Cancer":"Cardinal","Libra":"Cardinal",
            "Capricorn":"Cardinal",
            "Taurus":"Fixed","Leo":"Fixed","Scorpio":"Fixed","Aquarius":"Fixed",
            "Gemini":"Mutable","Virgo":"Mutable","Sagittarius":"Mutable",
            "Pisces":"Mutable","Ophiuchus":"—"}

# Aspect table — same tolerances as Research Series 001 & mirror_object.
_ASPECTS = [(0.0,"conjunction",8.0),(60.0,"sextile",6.0),
            (90.0,"square",8.0),(120.0,"trine",8.0),(180.0,"opposition",8.0)]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class ProfectionYear:
    """Result of profecting to a single birthday-year."""
    age:                 int                      # integer age at target date
    activated_house:     int                      # 1..12
    profected_sign:      str                      # sign on that house cusp
    lord_of_the_year:    Optional[str]            # traditional ruler
    modern_ruler:        Optional[str]
    ruler_unavailable_reason: Optional[str] = None
    birthday_range:      Tuple[str, str] = ("", "")   # (start_iso, end_iso)
    ruler_natal_condition: Dict[str, Any] = field(default_factory=dict)
    element:             str = ""
    modality:            str = ""
    is_current:          bool = False
    profection_source: str = "mirror_canonical_variant_a_equal"
    engine_marker:     str = BUILD_MARKER


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def compute_profection(*,
                        natal_chart: Dict[str, Any],
                        birth_datetime_utc: datetime,
                        target_date: date,
                        ) -> ProfectionYear:
    """Compute the annual profection active on `target_date` for a subject
    born at `birth_datetime_utc` whose natal chart is `natal_chart` (in
    Mirror canonical Variant-A / Equal-house shape as returned by
    `calculations.astrology.get_full_natal_chart(house_system='Equal')`).

    The function is pure — no DB, no HTTP, no clock. Deterministic.
    """
    if not natal_chart:
        raise ValueError("natal_chart must be provided")
    if birth_datetime_utc.tzinfo is None:
        raise ValueError("birth_datetime_utc must be timezone-aware (UTC)")

    age, birthday_this, birthday_next = _age_and_birthday_window(
        birth_datetime_utc.date(), target_date)

    house_num = (age % 12) + 1
    prof_sign = _sign_on_house_cusp(natal_chart, house_num)

    lord      = TRAD_RULER.get(prof_sign)
    mod_lord  = MODERN_RULER.get(prof_sign)
    reason    = None
    if lord is None:
        reason = (
            f"{prof_sign} is a 13-sign Variant-A constellation with no "
            f"classical ruler; Lord of the Year is intentionally blank."
        )

    ruler_cond = _ruler_condition(natal_chart, lord) if lord else {}

    # is_current: does the target date fall inside the birthday window?
    is_current = (birthday_this <= target_date < birthday_next)

    return ProfectionYear(
        age                     = age,
        activated_house         = house_num,
        profected_sign          = prof_sign,
        lord_of_the_year        = lord,
        modern_ruler            = mod_lord,
        ruler_unavailable_reason= reason,
        birthday_range          = (birthday_this.isoformat(),
                                    (birthday_next - timedelta(days=1)).isoformat()),
        ruler_natal_condition   = ruler_cond,
        element                 = ELEMENT.get(prof_sign, "—"),
        modality                = MODALITY.get(prof_sign, "—"),
        is_current              = is_current,
    )


def compute_profection_series(*,
                               natal_chart: Dict[str, Any],
                               birth_datetime_utc: datetime,
                               from_age: int,
                               to_age: int,
                               today: Optional[date] = None,
                               ) -> List[ProfectionYear]:
    """Batch-compute profection years [from_age..to_age] inclusive. Useful
    for scrubbing history or previewing a lifespan on the Timeline.

    `is_current` is set on the ONE entry whose birthday-window includes
    `today` (defaults to today's UTC date). All other entries get False.
    """
    if from_age > to_age:
        from_age, to_age = to_age, from_age
    if today is None:
        today = datetime.now(tz=birth_datetime_utc.tzinfo or None).date()

    out: List[ProfectionYear] = []
    for age in range(from_age, to_age + 1):
        # Compute a target_date that always falls INSIDE the birthday
        # window for `age` — namely (birthday + age years + 1 day).
        try:
            anchor = birth_datetime_utc.date().replace(
                year=birth_datetime_utc.date().year + age
            ) + timedelta(days=1)
        except ValueError:
            # Feb-29 birthday → fall back to Feb-28 of that year.
            anchor = (birth_datetime_utc.date().replace(
                month=2, day=28,
                year=birth_datetime_utc.date().year + age
            ) + timedelta(days=1))
        p = compute_profection(
            natal_chart         = natal_chart,
            birth_datetime_utc  = birth_datetime_utc,
            target_date         = anchor,
        )
        # Override is_current using the caller-supplied `today` so only
        # the truly-active year gets flagged.
        bday_start = date.fromisoformat(p.birthday_range[0])
        bday_end   = date.fromisoformat(p.birthday_range[1])
        p.is_current = (bday_start <= today <= bday_end)
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _age_and_birthday_window(birth: date, target: date) -> Tuple[int, date, date]:
    """Return (age, birthday_this_year, birthday_next_year) where
    `birthday_this_year` <= target < `birthday_next_year`. Age is the
    integer number of complete years since birth on `target`."""
    def _bday(year: int) -> date:
        try:
            return birth.replace(year=year)
        except ValueError:                     # Feb-29 → Feb-28 on non-leap
            return birth.replace(year=year, month=2, day=28)

    age = target.year - birth.year
    bday_this = _bday(target.year)
    if target < bday_this:
        age -= 1
        bday_this = _bday(target.year - 1)
    bday_next = _bday(bday_this.year + 1)
    return age, bday_this, bday_next


def _sign_on_house_cusp(chart: Dict[str, Any], house_num: int) -> str:
    """Return the sign printed on the Equal-house cusp of house `house_num`."""
    houses = chart.get("houses")

    # get_full_natal_chart(house_system='Equal') returns houses as a dict
    # with a `formatted_cusps` list. Also accept a bare list for callers
    # that pre-normalised.
    if isinstance(houses, dict):
        cusps = houses.get("formatted_cusps") or []
    elif isinstance(houses, list):
        cusps = houses
    else:
        cusps = []

    for c in cusps:
        if isinstance(c, dict) and int(c.get("house") or 0) == house_num:
            sign = c.get("sign")
            if sign:
                return sign

    # Fallback: compute from ASC longitude + 30° per house (Equal).
    ang = chart.get("angles") or {}
    asc = (ang.get("asc") or {}).get("longitude")
    if asc is None:
        raise ValueError("cannot determine sign on cusp: no ASC in chart")
    # Ask sign_attribution — this keeps Variant-A Ophiuchus honest.
    from calculations.sign_attribution import (   # noqa: PLC0415
        attribute_sign_midpoint13_variant_a,
    )
    from calculations.astrology import SVP_DEGREES_MIRROR  # noqa: PLC0415  (optional)
    _ = SVP_DEGREES_MIRROR                                # only to touch import
    SVP = 31.2836
    cusp_sidereal = (float(asc) + 30.0 * (house_num - 1)) % 360.0
    cusp_tropical = (cusp_sidereal + SVP) % 360.0
    return attribute_sign_midpoint13_variant_a(cusp_tropical)["sign"]


def _ruler_condition(chart: Dict[str, Any], ruler: str) -> Dict[str, Any]:
    """Extract the natal condition of the Lord of the Year from the stored
    Mirror chart. Reuses the shape produced by `get_full_natal_chart`."""
    planets = chart.get("planets") or {}
    if isinstance(planets, list):
        planets = {p.get("name") or p.get("planet"): p for p in planets
                    if isinstance(p, dict)}
    body = planets.get(ruler)
    if not isinstance(body, dict):
        return {"note": f"ruler {ruler} not present on natal chart payload"}

    sign     = body.get("sign")
    house    = body.get("house")
    lng      = float(body.get("longitude") or 0.0)
    deg      = float(body.get("degree")    or 0.0)
    retro    = bool(body.get("retrograde"))

    # Sun distance → combustion classification.
    sun = planets.get("Sun") or {}
    sun_lng = float(sun.get("longitude") or 0.0) if sun else None
    combust = under_beams = cazimi = False
    sun_gap: Optional[float] = None
    if sun_lng is not None and ruler != "Sun":
        gap = abs((lng - sun_lng + 180.0) % 360.0 - 180.0)
        sun_gap = round(gap, 3)
        if   gap <= 17/60:            cazimi = True
        elif gap <= 8.0:              combust = True
        elif gap <= 17.0:             under_beams = True

    # Aspects: reuse the same rule set as Research Series 001.
    aspects: List[Dict[str, Any]] = []
    for pname, p in planets.items():
        if pname == ruler or not isinstance(p, dict): continue
        try:
            p_lng = float(p.get("longitude") or 0.0)
        except (TypeError, ValueError):
            continue
        d = abs((lng - p_lng + 180.0) % 360.0 - 180.0)
        for target, name, orb in _ASPECTS:
            if abs(d - target) <= orb:
                aspects.append({
                    "planet": pname, "aspect": name,
                    "exact":  round(d, 3), "orb": round(abs(d - target), 3),
                })
                break

    return {
        "ruler":        ruler,
        "sign":         sign,
        "house":        house,
        "longitude":    round(lng, 4),
        "degree":       round(deg, 4),
        "retrograde":   retro,
        "sun_distance_deg": sun_gap,
        "cazimi":       cazimi,
        "combust":      combust,
        "under_beams":  under_beams,
        "angularity":   _angularity(house),
        "major_aspects": aspects,
    }


def _angularity(house: Optional[int]) -> str:
    if house in (1, 4, 7, 10): return "angular"
    if house in (2, 5, 8, 11): return "succedent"
    if house in (3, 6, 9, 12): return "cadent"
    return "—"


__all__ = [
    "BUILD_MARKER",
    "ProfectionYear",
    "compute_profection",
    "compute_profection_series",
]
