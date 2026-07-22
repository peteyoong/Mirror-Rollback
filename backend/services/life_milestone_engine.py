"""Life Milestone Timing Engine — Timeline V2 · Phase 4 plug-in
==============================================================
Surface marker: life-milestone-engine-v1

Ingests user-recorded biographical events and Recognition Moments and
matches them against the deterministic timing lenses to surface
recurring themes — closing the loop between astrology and user-supplied
life history.

For each event with a date, we ask:
    • which house was activated (Annual Profection) at that date?
    • which life-cycle window (if any) was open at that date?

Then we tally the houses that recur across the user's biography — the
histogram often reveals durable patterns (e.g. "seven recorded events
in 8th house years") that no astrology-only lens would show.

Confidence is `conditional` — the signal depends on user-supplied data.

Data contract
-------------
Events are passed in via the `extras` dict from the router:

    extras = {
        "events": [
            {"date": "2015-06-12", "title": "moved to new city", "kind": "life_event"},
            {"date": "2018-11-04", "title": "book published",    "kind": "recognition"},
            ...
        ]
    }

Only `date` is required; everything else is optional. Dates without a
year+month+day are silently skipped.
"""
from __future__ import annotations

from collections import Counter
from datetime    import date, datetime
from typing      import Any, Dict, List, Optional

from services.annual_profection_engine import compute_profection
from services.life_cycle_timing_engine import _hits_for_anchor, _ANCHORS
from services.timing_engine_protocol   import (
    Confidence, TimingEngine, TimingEvidence,
)

BUILD_MARKER = "life-milestone-engine-v1"


def _parse_iso(s: Any) -> Optional[date]:
    if not s: return None
    try:
        if isinstance(s, datetime): return s.date()
        if isinstance(s, date):     return s
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


class LifeMilestoneTimingEngine(TimingEngine):
    """Fifth plug-in — user biography ↔ timing-window match."""

    engine_id          = "life_milestones"
    default_confidence: Confidence = "conditional"
    engine_marker      = BUILD_MARKER

    def compute(self, *,
                 natal_chart: Dict[str, Any],
                 birth_datetime_utc: datetime,
                 target_date: Optional[date] = None,
                 extras: Optional[Dict[str, Any]] = None,
                 ) -> TimingEvidence:
        events: List[Dict[str, Any]] = (extras or {}).get("events") or []

        if not events:
            return TimingEvidence(
                engine_id     = self.engine_id,
                name          = "Life Milestones (no data yet)",
                meaning       = ("Record life events or Recognition Moments "
                                  "to unlock recurring-theme detection."),
                confidence    = "conditional",
                active        = False,
                engine_marker = self.engine_marker,
            )

        matches: List[Dict[str, Any]] = []
        houses = Counter()
        cycles = Counter()

        for ev in events:
            d = _parse_iso(ev.get("date"))
            if d is None: continue

            # Profection at the event date.
            try:
                prof = compute_profection(
                    natal_chart        = natal_chart,
                    birth_datetime_utc = birth_datetime_utc,
                    target_date        = d,
                )
                house = prof.activated_house
                lord  = prof.lord_of_the_year
            except Exception:                                # pragma: no cover
                house, lord = None, None

            # Life-cycle windows active at that date.
            active_anchors: List[str] = []
            age = (datetime(d.year, d.month, d.day, 12, 0, 0,
                             tzinfo=birth_datetime_utc.tzinfo)
                    - birth_datetime_utc).total_seconds() / (365.25 * 86400.0)
            for a in _ANCHORS:
                for h in _hits_for_anchor(a, age, birth_datetime_utc):
                    if h["active"]:
                        active_anchors.append(a["label"])

            if house: houses[house] += 1
            for anc in active_anchors: cycles[anc] += 1

            matches.append({
                "date":            d.isoformat(),
                "title":           ev.get("title") or "",
                "kind":            ev.get("kind") or "life_event",
                "profection_house": house,
                "lord_of_the_year": lord,
                "life_cycle_windows_active": active_anchors,
            })

        top_houses = houses.most_common(3)
        top_cycles = cycles.most_common(3)

        meaning_bits: List[str] = []
        if top_houses:
            hs = ", ".join(f"H{h} (×{n})" for h, n in top_houses if n >= 2)
            if hs:
                meaning_bits.append(f"Recurring profection houses: {hs}.")
        if top_cycles:
            cs = ", ".join(f"{c} (×{n})" for c, n in top_cycles if n >= 2)
            if cs:
                meaning_bits.append(f"Recurring life-cycle windows: {cs}.")
        if not meaning_bits:
            meaning_bits.append(
                "No clear recurrence yet — add more events to see the pattern.")

        return TimingEvidence(
            engine_id  = self.engine_id,
            name       = f"Life Milestones · {len(matches)} recorded",
            meaning    = " ".join(meaning_bits),
            confidence = self.default_confidence,
            supporting_signals = [
                f"{len(matches)} user-supplied event(s)",
                "Annual Profection lookup per event",
                "Life-cycle window intersection per event",
            ],
            details = {
                "target_date":         (target_date or date.today()).isoformat(),
                "events_ingested":     len(matches),
                "matches":             matches,
                "recurring_houses":    top_houses,
                "recurring_cycles":    top_cycles,
            },
            engine_marker = self.engine_marker,
            active        = True,
        )


__all__ = ["BUILD_MARKER", "LifeMilestoneTimingEngine"]
