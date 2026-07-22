"""Zodiacal Releasing Timing Engine — Timeline Intelligence V2 · Phase 4 plug-in
================================================================================
Surface marker: zodiacal-releasing-engine-v1

SCAFFOLD implementation of Vettius Valens' Zodiacal Releasing (ZR),
released from the Lot of Spirit and the Lot of Fortune. This version
covers the L1 (major-period) layer only — the outermost timing shell.
L2/L3/L4 sub-period nesting, "loosing of the bond" transitions, and
peak-period detection are stubbed for a future release; this scaffold
returns the current L1 period so the Timeline can already show it.

Deterministic. No LLM.

References
----------
Valens, Anthology Book IV. Modern reconstruction: Chris Brennan,
"Hellenistic Astrology" (2017), chapter 17. Firdaria-style year lengths
per sign follow Valens directly.

Mirror canonical note
---------------------
The user's chart is Variant-A (13-sign), but ZR is a 12-sign Hellenistic
technique. When the Lot falls in Ophiuchus we collapse to Scorpio for
ZR purposes (mainstream reading — Firmicus/Valens don't distinguish).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime    import date, datetime, timedelta, timezone as _tz
from typing      import Any, Dict, List, Optional, Tuple

from services.timing_engine_protocol import (
    Confidence, TimingEngine, TimingEvidence,
)

BUILD_MARKER = "zodiacal-releasing-engine-v1"

# Valens' sign-year lengths (major-period durations in years).
_YEARS_PER_SIGN: Dict[str, int] = {
    "Aries": 15,   "Taurus": 8,   "Gemini": 20,  "Cancer": 25,
    "Leo": 19,     "Virgo": 20,   "Libra": 8,    "Scorpio": 15,
    "Sagittarius": 12, "Capricorn": 27, "Aquarius": 30, "Pisces": 12,
}
# Ophiuchus fallback for 13-sign Mirror charts.
_OPHIUCHUS_FALLBACK = "Scorpio"

_ZODIAC_ORDER = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
]

_TRAD_RULER = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}


# ---------------------------------------------------------------------------
# Core arithmetic — walk forward one sign at a time until we've consumed
# `total_years` from birth. Returns (current_sign, remaining_years,
# elapsed_years_at_start_of_current, sign_index).
# ---------------------------------------------------------------------------
def _walk_periods(start_sign: str, total_years: float
                   ) -> Tuple[str, float, float, int]:
    idx    = _ZODIAC_ORDER.index(start_sign)
    elapsed = 0.0
    while True:
        sign = _ZODIAC_ORDER[idx % 12]
        span = float(_YEARS_PER_SIGN[sign])
        if elapsed + span > total_years:
            return sign, span - (total_years - elapsed), elapsed, idx % 12
        elapsed += span
        idx    += 1


def _lot_sign_or_fallback(chart: Dict[str, Any], lot_key: str) -> Optional[str]:
    """Return the sign of `lot_key` from the chart. Accepts several shapes
    (Research-Series 001 chart, Mirror natal chart). Maps Ophiuchus →
    Scorpio for ZR compatibility. Falls back to computing the Lot on the
    fly from ASC/Sun/Moon/Venus longitudes when the chart has no
    pre-computed lots block."""
    # Prefer a dedicated `lots` block on the chart if present.
    lots = chart.get("lots") or {}
    for k in (lot_key, lot_key.title(), lot_key.replace("_"," ").title()):
        v = lots.get(k)
        if isinstance(v, dict) and v.get("sign"):
            s = v["sign"]
            return _OPHIUCHUS_FALLBACK if s == "Ophiuchus" else s

    # Fallback — compute the Lot on the fly.
    sign = _compute_lot_sign(chart, lot_key)
    if sign == "Ophiuchus":
        return _OPHIUCHUS_FALLBACK
    return sign


def _compute_lot_sign(chart: Dict[str, Any], lot_key: str) -> Optional[str]:
    """Compute Fortune/Spirit sign from the chart's sidereal longitudes.
    Uses Hellenistic (Valens) day/night rules:
        Fortune: day → ASC + Moon − Sun ; night → ASC + Sun − Moon
        Spirit : day → ASC + Sun − Moon ; night → ASC + Moon − Sun
    Sect is inferred from whether the Sun is above or below the horizon
    (H7-H12 is above under Mirror-canonical Equal houses)."""
    angles = chart.get("angles") or {}
    planets = chart.get("planets") or {}
    if isinstance(planets, list):
        planets = {p.get("name"): p for p in planets if isinstance(p, dict)}

    try:
        asc  = float((angles.get("asc")  or {}).get("longitude"))
        sun  = float((planets.get("Sun")  or {}).get("longitude"))
        moon = float((planets.get("Moon") or {}).get("longitude"))
    except (TypeError, ValueError):
        return None

    sun_house = (planets.get("Sun") or {}).get("house")
    is_day = sun_house in (7, 8, 9, 10, 11, 12)

    if lot_key.lower().endswith("fortune"):
        lng = (asc + moon - sun) % 360.0 if is_day else (asc + sun - moon) % 360.0
    else:  # Spirit (default)
        lng = (asc + sun - moon) % 360.0 if is_day else (asc + moon - sun) % 360.0

    # Mirror canonical uses Variant-A attribution — convert via the
    # canonical sign_attribution helper.
    try:
        from calculations.sign_attribution import attribute_sign_midpoint13_variant_a  # noqa: PLC0415
        trop = (lng + 31.2836) % 360.0    # sidereal → tropical for the attributor
        return attribute_sign_midpoint13_variant_a(trop)["sign"]
    except Exception:
        # Fallback: 12-sign 30° equal.
        return _ZODIAC_ORDER[int(lng // 30) % 12]


def _fractional_years_since(birth_utc: datetime,
                              target_date: date) -> float:
    delta = datetime(target_date.year, target_date.month, target_date.day,
                      12, 0, 0, tzinfo=_tz.utc) - birth_utc
    return delta.total_seconds() / (365.25 * 86400.0)


# ---------------------------------------------------------------------------
# Plug-in
# ---------------------------------------------------------------------------
class ZodiacalReleasingScaffoldEngine(TimingEngine):
    """L1-only ZR scaffold from Lot of Spirit and Lot of Fortune."""

    engine_id          = "zodiacal_releasing"
    default_confidence: Confidence = "moderate"
    engine_marker      = BUILD_MARKER

    def compute(self, *,
                 natal_chart: Dict[str, Any],
                 birth_datetime_utc: datetime,
                 target_date: Optional[date] = None,
                 extras: Optional[Dict[str, Any]] = None,
                 ) -> TimingEvidence:
        target_date = target_date or datetime.utcnow().date()
        years = _fractional_years_since(birth_datetime_utc, target_date)

        # Spirit is the standard release for character/career; Fortune for
        # body/circumstance. Both are shown when the chart carries them.
        spirit_sign  = _lot_sign_or_fallback(natal_chart, "Lot of Spirit")
        fortune_sign = _lot_sign_or_fallback(natal_chart, "Lot of Fortune")

        if not spirit_sign and not fortune_sign:
            return TimingEvidence(
                engine_id     = self.engine_id,
                name          = "Zodiacal Releasing (unavailable)",
                meaning       = ("Lot of Spirit / Lot of Fortune not on the "
                                  "chart payload — ZR cannot be released."),
                confidence    = "low",
                active        = False,
                engine_marker = self.engine_marker,
            )

        blocks: Dict[str, Any] = {}
        if spirit_sign:
            sign, rem, elapsed_at_start, _ = _walk_periods(spirit_sign, years)
            span = float(_YEARS_PER_SIGN[sign])
            blocks["spirit"] = {
                "release_from":    spirit_sign,
                "current_L1_sign": sign,
                "current_L1_ruler": _TRAD_RULER[sign],
                "period_years":    span,
                "years_elapsed_in_period": round(span - rem, 3),
                "years_remaining":         round(rem, 3),
                "period_start_date":  _date_add_years(birth_datetime_utc.date(),
                                                     elapsed_at_start),
                "period_end_date":    _date_add_years(birth_datetime_utc.date(),
                                                     elapsed_at_start + span),
            }
        if fortune_sign:
            sign, rem, elapsed_at_start, _ = _walk_periods(fortune_sign, years)
            span = float(_YEARS_PER_SIGN[sign])
            blocks["fortune"] = {
                "release_from":    fortune_sign,
                "current_L1_sign": sign,
                "current_L1_ruler": _TRAD_RULER[sign],
                "period_years":    span,
                "years_elapsed_in_period": round(span - rem, 3),
                "years_remaining":         round(rem, 3),
                "period_start_date":  _date_add_years(birth_datetime_utc.date(),
                                                     elapsed_at_start),
                "period_end_date":    _date_add_years(birth_datetime_utc.date(),
                                                     elapsed_at_start + span),
            }

        # Meaning line — observational and mirror-tone. Prefer Spirit.
        primary = blocks.get("spirit") or blocks.get("fortune") or {}
        p_sign  = primary.get("current_L1_sign")
        p_rule  = primary.get("current_L1_ruler")
        p_span  = primary.get("period_years")
        meaning = (
            f"A long-form chapter of {p_sign} (ruled by {p_rule}) is currently "
            f"active — {p_span}-year window. This is Mirror's ZR-L1 scaffold: "
            f"it names the atmosphere of the multi-year period rather than "
            f"the day-to-day."
        ) if p_sign else "Zodiacal Releasing scaffold — insufficient data."

        return TimingEvidence(
            engine_id  = self.engine_id,
            name       = ("ZR · L1 " +
                          (blocks.get("spirit",{}).get("current_L1_sign") or
                           blocks.get("fortune",{}).get("current_L1_sign") or
                           "period")),
            meaning    = meaning,
            confidence = self.default_confidence,
            supporting_signals = [
                "Lot of Spirit + Lot of Fortune (Hellenistic Valens formula)",
                "Valens sign-year lengths",
                "L1 major-period layer only (L2/L3/L4 scaffolded for future)",
                "Ophiuchus → Scorpio fallback for 13-sign Mirror charts",
            ],
            details = {
                "target_date":   target_date.isoformat(),
                "years_since_birth": round(years, 4),
                "spirit":        blocks.get("spirit"),
                "fortune":       blocks.get("fortune"),
                "layer_scope":   "L1 major-period only (scaffold)",
                "future_layers": ["L2 sub-period", "L3", "L4",
                                    "loosing-of-the-bond detection",
                                    "peak-period ranking"],
            },
            engine_marker = self.engine_marker,
            active        = True,
        )


def _date_add_years(start: date, years: float) -> str:
    delta = timedelta(days=years * 365.25)
    d = start + delta
    return d.isoformat()


__all__ = ["BUILD_MARKER", "ZodiacalReleasingScaffoldEngine"]
