"""Human Design Life-Cycle Timing Engine — Timeline V2 · Phase 4 plug-in
=======================================================================
Surface marker: life-cycle-timing-engine-v1

Anchors the multi-decade transits that shape every biography, computed
purely from birth date — no ephemeris query needed. These are the
"biological clock" transits: durable, predictable, well-studied.

Anchors covered
---------------
    • Saturn return          — ~29.5 y and every ~29.5 y after
    • Uranus opposition      — ~41-42 y (mid-life)
    • Chiron return          — ~50-51 y
    • Nodal return           — every ~18.6 y  (18.6, 37.2, 55.8, 74.4)
    • Jupiter return         — every ~11.86 y (also the profection 1st-house cycle)

For each anchor we report the age band (±1.5 y default), the calendar
window (start/end dates), whether the user is currently inside the
window, and how many years to the next hit.

Confidence: high — these are astronomy-timed events with tight
statistical distributions, not interpretive claims.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as _tz
from typing   import Any, Dict, List, Optional

from services.timing_engine_protocol import (
    Confidence, TimingEngine, TimingEvidence,
)

BUILD_MARKER = "life-cycle-timing-engine-v1"

_ANCHORS: List[Dict[str, Any]] = [
    {"id":"saturn_return",     "label":"Saturn Return",      "period":29.457,  "band":1.5,
     "note":"maturation checkpoint · what you're actually here to be responsible for"},
    {"id":"uranus_opposition", "label":"Uranus Opposition",  "period":84.0,    "half":True, "band":1.5,
     "note":"midlife window · re-negotiation of freedom versus responsibility"},
    {"id":"chiron_return",     "label":"Chiron Return",      "period":50.4,    "single":True, "band":1.5,
     "note":"integration of the long-standing wound · a moment for wholeness, not fix"},
    {"id":"nodal_return",      "label":"Nodal Return",       "period":18.613,  "band":1.0,
     "note":"life-direction re-anchoring · past and future rearrange around each other"},
    {"id":"jupiter_return",    "label":"Jupiter Return",     "period":11.862,  "band":1.0,
     "note":"expansion checkpoint · re-tests the arena of the previous 12-year chapter"},
]


def _years_since(birth_utc: datetime, target_date: date) -> float:
    dt = datetime(target_date.year, target_date.month, target_date.day,
                   12, 0, 0, tzinfo=_tz.utc)
    return (dt - birth_utc).total_seconds() / (365.25 * 86400.0)


def _date_add_years(start_utc: datetime, years: float) -> str:
    return (start_utc + timedelta(days=years * 365.25)).date().isoformat()


def _hits_for_anchor(anchor: Dict[str, Any],
                      age_now: float,
                      birth_utc: datetime) -> List[Dict[str, Any]]:
    """Return every anchor hit inside [age 0 .. age 120], with active flag."""
    period = float(anchor["period"])
    band   = float(anchor["band"])
    if anchor.get("single"):
        ages = [period]
    elif anchor.get("half"):
        # Half-cycle event (e.g. Uranus opposition happens once at half a
        # Uranus period).
        ages = [period / 2.0]
    else:
        ages = []
        k = 1
        while k * period <= 120:
            ages.append(k * period); k += 1

    out: List[Dict[str, Any]] = []
    for a in ages:
        active = abs(age_now - a) <= band
        out.append({
            "at_age":         round(a, 3),
            "window_start":   _date_add_years(birth_utc, a - band),
            "window_end":     _date_add_years(birth_utc, a + band),
            "active":         active,
            "years_from_now": round(a - age_now, 3),
        })
    return out


class LifeCycleTimingEngine(TimingEngine):
    """Fourth plug-in — birth-date-only life-cycle anchors."""

    engine_id          = "life_cycle"
    default_confidence: Confidence = "high"
    engine_marker      = BUILD_MARKER

    def compute(self, *,
                 natal_chart: Dict[str, Any],
                 birth_datetime_utc: datetime,
                 target_date: Optional[date] = None,
                 extras: Optional[Dict[str, Any]] = None,
                 ) -> TimingEvidence:
        target_date = target_date or datetime.utcnow().date()
        age = _years_since(birth_datetime_utc, target_date)

        blocks: List[Dict[str, Any]] = []
        active_now: List[Dict[str, Any]] = []
        next_hit: Optional[Dict[str, Any]] = None

        for anc in _ANCHORS:
            hits = _hits_for_anchor(anc, age, birth_datetime_utc)
            for h in hits:
                if h["active"]:
                    active_now.append({**h, "anchor_id": anc["id"],
                                        "label": anc["label"], "note": anc["note"]})
            future = [h for h in hits if h["years_from_now"] > 0]
            if future:
                cand = min(future, key=lambda x: x["years_from_now"])
                if next_hit is None or cand["years_from_now"] < next_hit["years_from_now"]:
                    next_hit = {**cand, "anchor_id": anc["id"],
                                 "label": anc["label"], "note": anc["note"]}
            blocks.append({
                "anchor_id": anc["id"], "label": anc["label"],
                "period_years": anc["period"], "note": anc["note"],
                "hits": hits,
            })

        # Meaning line.
        if active_now:
            first = active_now[0]
            meaning = (
                f"You are inside a {first['label']} window "
                f"({first['window_start']} → {first['window_end']}). "
                f"{first['note']}."
            )
            conf: Confidence = "high"
        elif next_hit:
            yrs = next_hit["years_from_now"]
            meaning = (
                f"No life-cycle anchor is active right now. Next hit is "
                f"{next_hit['label']} in {yrs:.1f} years "
                f"({next_hit['window_start']} → {next_hit['window_end']})."
            )
            conf = "moderate"
        else:
            meaning = "All modelled life-cycle anchors sit outside the visible window."
            conf = "low"

        return TimingEvidence(
            engine_id  = self.engine_id,
            name       = ("Life Cycle · " + active_now[0]["label"]
                          if active_now else "Life Cycle · quiet stretch"),
            meaning    = meaning,
            confidence = conf,
            supporting_signals = [
                "birth date only (no ephemeris query required)",
                "sidereal periods: Saturn 29.5y · Uranus 84y · Chiron 50.4y",
                "nodal cycle 18.6y · Jupiter 11.9y",
                "±1.5y default band for outer planets, ±1.0y for nodal/Jupiter",
            ],
            details = {
                "target_date":    target_date.isoformat(),
                "age_years":      round(age, 4),
                "active_windows": active_now,
                "next_hit":       next_hit,
                "anchors":        blocks,
            },
            engine_marker = self.engine_marker,
            active        = True,
        )


__all__ = ["BUILD_MARKER", "LifeCycleTimingEngine"]
