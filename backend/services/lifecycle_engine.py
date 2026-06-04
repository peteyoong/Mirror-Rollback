"""
Lifecycle Engine — answer the person before the concept
========================================================
Build marker: astrology-lifecycle-v1

P0 fix for the Astrology Chat trust bug where a question like
"tell me about my Saturn return" was being answered with a textbook
explanation of what a Saturn Return is, instead of locating THIS
person in their actual cycle.

What this module does
---------------------
For every supported lifecycle topic it computes, deterministically
from the user's natal chart:

* the relevant cycle period and base age windows
* the exact transit pass date(s) using Swiss Ephemeris bisection
* the user's current cycle instance (1st / 2nd / 3rd return,
  pre / mid / post midlife, etc.)
* a phase label: ``before`` | ``during`` | ``after``
* a meaning tag (so the LLM can distinguish 1st-Saturn-Return =
  adulthood from 2nd-Saturn-Return = legacy/coherence)

The output is rendered to a hard "proof block" that is injected
into the system prompt and read by the LLM as ground truth — the
LLM is forbidden from contradicting or omitting it.

Supported topics
----------------
* Saturn Return / Saturn Opposition / Saturn Square Saturn
* Jupiter Return / Jupiter Opposition
* Uranus Opposition / Uranus Return
* Neptune square Neptune (midlife)
* Pluto square Pluto (midlife — generationally variable)
* Chiron Return
* Nodal Return / Nodal Opposition
* Mars Return / Venus Return / Solar Return (light support)
* Progressed Lunation Cycle (progressed New Moon / Full Moon /
  progressed Moon return)
* Major outer-planet transits to natal Ascendant / Midheaven
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe  # type: ignore[import]

logger = logging.getLogger(__name__)
BUILD_MARKER = "astrology-lifecycle-v1"

# ---------------------------------------------------------------------------
# Swisseph body ids — tropical computations only (transit search runs in
# tropical because the natal longitudes we match against are tropical).
# ---------------------------------------------------------------------------
SE_BODIES = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Mars":    swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    "Uranus":  swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto":   swe.PLUTO,
    "Chiron":  swe.CHIRON,
    "North Node": swe.TRUE_NODE,
}

# Orbital periods in years — used only as the FIRST-PASS bracket guess.
# The actual return date is found by bisection on transit_longitude.
ORBITAL_PERIOD_YEARS = {
    "Sun":     1.0,
    "Moon":    27.3 / 365.25,
    "Mercury": 1.0,
    "Venus":   1.0,
    "Mars":    1.88,
    "Jupiter": 11.862,
    "Saturn":  29.457,
    "Uranus":  84.02,
    "Neptune": 164.79,
    "Pluto":   247.94,
    "Chiron":  50.7,
    "North Node": 18.6,   # nodal precession period
}

# Event-specific "during" windows, in MONTHS on either side of the exact pass.
# Per user spec.
DURING_WINDOW_MONTHS = {
    "saturn_return":         18,
    "chiron_return":         18,
    "uranus_opposition":     18,
    "uranus_return":         18,
    "nodal_return":           9,
    "nodal_opposition":       9,
    "jupiter_return":         6,
    "jupiter_opposition":     6,
    "saturn_opposition":     12,
    "saturn_square_saturn":  12,
    "pluto_square_pluto":    18,
    "neptune_square_neptune":18,
    "progressed_lunation":   12,
    "progressed_new_moon":   12,
    "progressed_full_moon":  12,
    "progressed_moon_return":12,
    "mars_return":            2,
    "venus_return":           2,
    "solar_return":           1,
    "lunar_return":           0.5,  # half a month
    "midheaven_hit":         12,
    "ascendant_hit":         12,
}

# Meaning tags by instance — the LLM must distinguish 1st vs 2nd vs 3rd.
MEANING_BY_INSTANCE: Dict[str, Dict[int, str]] = {
    "saturn_return": {
        1: "1st Saturn Return (~ages 28-31): adulthood, "
           "structural identity formation, choosing the architecture "
           "of an adult life.",
        2: "2nd Saturn Return (~ages 57-60): legacy / coherence / "
           "simplification — NOT young-adult maturation. What remains "
           "meaningful after decades of building. Pruning, completion, "
           "finding the through-line.",
        3: "3rd Saturn Return (~ages 87-90): elderhood, completion, "
           "transmission of what has been carried.",
    },
    "chiron_return": {
        1: "Chiron Return (~ages 49-51): integration of the long-carried "
           "wound; healer becomes the source rather than the seeker.",
    },
    "uranus_opposition": {
        1: "Uranus Opposition (~ages 40-43): mid-life uprising — the "
           "what-have-I-done / what-still-feels-true rupture phase.",
    },
    "uranus_return": {
        1: "Uranus Return (~age 84): full individuation cycle complete.",
    },
    "jupiter_return": {
        1: "1st Jupiter Return (~age 12): worldview expansion at puberty.",
        2: "2nd Jupiter Return (~age 24): adult horizon-setting.",
        3: "3rd Jupiter Return (~age 36): consolidation expansion.",
        4: "4th Jupiter Return (~age 48): mature meaning-making.",
        5: "5th Jupiter Return (~age 60): wisdom expansion / mentor phase.",
        6: "6th Jupiter Return (~age 72): legacy expansion.",
    },
    "nodal_return": {
        1: "1st Nodal Return (~ages 18-19): the dharmic call enters first.",
        2: "2nd Nodal Return (~ages 37-38): dharma confirmed or refused.",
        3: "3rd Nodal Return (~ages 55-57): elder dharma — the gift you "
           "are here to leave.",
    },
    "nodal_opposition": {
        1: "1st Nodal Opposition (~ages 9-10): first contact with destiny "
           "tension.",
        2: "2nd Nodal Opposition (~ages 27-28): adult turning toward "
           "dharma.",
        3: "3rd Nodal Opposition (~ages 46-47): mid-life direction "
           "audit.",
        4: "4th Nodal Opposition (~ages 64-65): elder direction "
           "audit.",
    },
    "pluto_square_pluto": {
        1: "Pluto Square Pluto: generationally variable (~ages 36-55) — "
           "deep transformation of identity, power, and what is "
           "non-negotiable.",
    },
    "neptune_square_neptune": {
        1: "Neptune Square Neptune (~age 41-43): dissolution of the "
           "old story — what was idealized must be re-met or grieved.",
    },
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _jd_to_iso(jd_ut: float) -> str:
    y, mo, d, h = swe.revjul(jd_ut)
    hh = int(h)
    mm = int((h - hh) * 60)
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}T{hh:02d}:{mm:02d}Z"

def _jd_to_date(jd_ut: float) -> datetime:
    y, mo, d, h = swe.revjul(jd_ut)
    hh = int(h)
    mm = int((h - hh) * 60)
    return datetime(int(y), int(mo), int(d), hh, mm, tzinfo=timezone.utc)

def _ang_diff(a: float, b: float) -> float:
    """Signed minimal angular difference (a - b), normalized to (-180, 180]."""
    d = (a - b + 540.0) % 360.0 - 180.0
    return d

def _body_lon(jd_ut: float, body_id: int, flags: int = swe.FLG_SWIEPH) -> float:
    """Tropical longitude of body at UT JD."""
    res = swe.calc_ut(jd_ut, body_id, flags)
    return res[0][0]


# ---------------------------------------------------------------------------
# Core: find transit passes where (body_long - target) hits 0 (within window)
# ---------------------------------------------------------------------------

def _scan_transit_passes(
    body: str,
    target_long: float,
    offset_deg: float,
    jd_start: float,
    jd_end: float,
    step_days: float = 7.0,
) -> List[float]:
    """Scan body's tropical longitude vs (target + offset) between
    jd_start and jd_end and return JDs of every zero-crossing
    (retrograde-aware). Refines each crossing by bisection to ~minute
    precision.
    """
    body_id = SE_BODIES.get(body)
    if body_id is None:
        return []
    tgt = (target_long + offset_deg) % 360.0
    jd = jd_start
    prev_jd = jd
    prev_diff = _ang_diff(_body_lon(jd, body_id), tgt)
    hits: List[float] = []
    jd += step_days
    while jd <= jd_end:
        diff = _ang_diff(_body_lon(jd, body_id), tgt)
        # Sign change ⇒ crossing in [prev_jd, jd]
        if prev_diff == 0 or (prev_diff * diff) < 0:
            lo, hi = prev_jd, jd
            lo_d, hi_d = prev_diff, diff
            for _ in range(40):
                mid = (lo + hi) / 2.0
                mid_d = _ang_diff(_body_lon(mid, body_id), tgt)
                if abs(mid_d) < 1.0 / 3600.0:  # <1 arcsec
                    lo = hi = mid
                    break
                if (lo_d * mid_d) < 0:
                    hi, hi_d = mid, mid_d
                else:
                    lo, lo_d = mid, mid_d
            hits.append((lo + hi) / 2.0)
        prev_jd = jd
        prev_diff = diff
        jd += step_days
    # De-duplicate any hits within 2 days
    deduped: List[float] = []
    for h in sorted(hits):
        if not deduped or (h - deduped[-1]) > 2.0:
            deduped.append(h)
    return deduped


# ---------------------------------------------------------------------------
# Public dataclass for a single lifecycle event
# ---------------------------------------------------------------------------

@dataclass
class LifecycleEvent:
    key: str
    label: str
    instance: int                       # 1, 2, 3, ...
    cycle_period_years: float
    expected_age_at: float
    exact_passes: List[str]             # ISO datetimes of each retrograde pass
    window_start: str                   # ISO datetime
    window_end:   str                   # ISO datetime
    phase: str                          # before | during | after
    months_to_event: float              # negative if past
    meaning: str                        # 1st vs 2nd vs 3rd vs ... text

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# High-level engine
# ---------------------------------------------------------------------------

class LifecycleEngine:
    """Build deterministic lifecycle events for the user."""

    def __init__(self, chart: Dict[str, Any], birth_utc: datetime, now_utc: datetime):
        self.chart = chart or {}
        self.birth = birth_utc
        self.now   = now_utc
        self.birth_jd = swe.julday(
            birth_utc.year, birth_utc.month, birth_utc.day,
            birth_utc.hour + birth_utc.minute / 60.0,
        )
        self.now_jd   = swe.julday(
            now_utc.year, now_utc.month, now_utc.day,
            now_utc.hour + now_utc.minute / 60.0,
        )
        # Cache natal tropical longitudes
        self.natal_long: Dict[str, float] = {}
        planets = self.chart.get("planets") or {}
        for name, p in planets.items():
            t = p.get("tropical_longitude")
            if t is not None:
                self.natal_long[name] = float(t)
        # Angles
        angles = self.chart.get("angles") or {}
        for ang_key, src in (("Ascendant", "asc"), ("Midheaven", "mc")):
            a = angles.get(src) or {}
            t = a.get("tropical_longitude")
            if t is not None:
                self.natal_long[ang_key] = float(t)

    @property
    def current_age_years(self) -> float:
        return (self.now - self.birth).total_seconds() / (365.25 * 86400.0)

    # --- single-event helpers -----------------------------------------

    def _return_event(
        self,
        key: str,
        label: str,
        body: str,
        natal_long: float,
        offset_deg: float,
        instance: int,
    ) -> Optional[LifecycleEvent]:
        period = ORBITAL_PERIOD_YEARS[body]
        target_age = (period * instance) - period * (offset_deg / 360.0) * 0.0
        # For oppositions/squares, the offset shifts the conceptual age:
        #   conj (0°)   ⇒ at full period multiples
        #   opp  (180°) ⇒ first hit at period/2 then every period
        #   square 90°  ⇒ first hit at period/4 then period/2 between
        if abs(offset_deg) < 1e-6:
            expected_age = period * instance
        elif abs(abs(offset_deg) - 180.0) < 1e-6:
            expected_age = period * (instance - 0.5)
        else:  # square (90 or 270)
            quarter = period / 4.0
            # Square hits every period/2 starting at quarter
            expected_age = quarter + (instance - 1) * (period / 2.0)

        if expected_age <= 0 or expected_age > 130:
            return None

        # Search window: ±15% of the period (gives outer planets plenty of slack)
        slack_years = max(0.5, period * 0.10)
        jd_lo = self.birth_jd + (expected_age - slack_years) * 365.25
        jd_hi = self.birth_jd + (expected_age + slack_years) * 365.25

        passes = _scan_transit_passes(body, natal_long, offset_deg, jd_lo, jd_hi)
        if not passes:
            return None

        # The "exact" reference pass = middle hit (or first if only one)
        ref_jd = passes[len(passes) // 2]
        ref_dt = _jd_to_date(ref_jd)
        win_months = DURING_WINDOW_MONTHS.get(key, 12)
        window_start = ref_dt - timedelta(days=int(win_months * 30.4375))
        window_end   = ref_dt + timedelta(days=int(win_months * 30.4375))

        months_to = (ref_dt - self.now).total_seconds() / (30.4375 * 86400.0)
        if self.now < window_start:
            phase = "before"
        elif self.now > window_end:
            phase = "after"
        else:
            phase = "during"

        meaning = MEANING_BY_INSTANCE.get(key, {}).get(instance, "")

        return LifecycleEvent(
            key=key,
            label=label,
            instance=instance,
            cycle_period_years=period,
            expected_age_at=round(expected_age, 2),
            exact_passes=[_jd_to_iso(p) for p in passes],
            window_start=window_start.replace(microsecond=0).isoformat(),
            window_end=window_end.replace(microsecond=0).isoformat(),
            phase=phase,
            months_to_event=round(months_to, 1),
            meaning=meaning,
        )

    # --- public computations ------------------------------------------

    def saturn_returns(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Saturn")
        if nat is None:
            return []
        out: List[LifecycleEvent] = []
        for i in range(1, 4):
            ev = self._return_event(
                "saturn_return", f"{['','1st','2nd','3rd'][i]} Saturn Return",
                "Saturn", nat, 0.0, i,
            )
            if ev:
                out.append(ev)
        return out

    def saturn_opposition(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Saturn")
        if nat is None:
            return []
        out = []
        for i in range(1, 4):
            ev = self._return_event(
                "saturn_opposition", f"Saturn opposition Saturn (#{i})",
                "Saturn", nat, 180.0, i,
            )
            if ev:
                out.append(ev)
        return out

    def saturn_square_saturn(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Saturn")
        if nat is None:
            return []
        out = []
        for i in range(1, 7):
            ev = self._return_event(
                "saturn_square_saturn", f"Saturn square Saturn (#{i})",
                "Saturn", nat, 90.0, i,
            )
            if ev:
                out.append(ev)
        return out

    def jupiter_returns(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Jupiter")
        if nat is None:
            return []
        out = []
        for i in range(1, 8):
            ev = self._return_event(
                "jupiter_return", f"{i}th Jupiter Return" if i > 3 else
                f"{['','1st','2nd','3rd'][i]} Jupiter Return",
                "Jupiter", nat, 0.0, i,
            )
            if ev:
                out.append(ev)
        return out

    def jupiter_opposition(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Jupiter")
        if nat is None:
            return []
        out = []
        for i in range(1, 8):
            ev = self._return_event(
                "jupiter_opposition", f"Jupiter opposition Jupiter (#{i})",
                "Jupiter", nat, 180.0, i,
            )
            if ev:
                out.append(ev)
        return out

    def uranus_opposition(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Uranus")
        if nat is None:
            return []
        ev = self._return_event(
            "uranus_opposition", "Uranus opposition Uranus (midlife)",
            "Uranus", nat, 180.0, 1,
        )
        return [ev] if ev else []

    def uranus_return(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Uranus")
        if nat is None:
            return []
        ev = self._return_event(
            "uranus_return", "Uranus Return",
            "Uranus", nat, 0.0, 1,
        )
        return [ev] if ev else []

    def neptune_square_neptune(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Neptune")
        if nat is None:
            return []
        ev = self._return_event(
            "neptune_square_neptune", "Neptune square Neptune (midlife)",
            "Neptune", nat, 90.0, 1,
        )
        return [ev] if ev else []

    def pluto_square_pluto(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Pluto")
        if nat is None:
            return []
        ev = self._return_event(
            "pluto_square_pluto", "Pluto square Pluto (generationally variable)",
            "Pluto", nat, 90.0, 1,
        )
        return [ev] if ev else []

    def chiron_return(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("Chiron")
        if nat is None:
            return []
        ev = self._return_event(
            "chiron_return", "Chiron Return",
            "Chiron", nat, 0.0, 1,
        )
        return [ev] if ev else []

    def nodal_returns(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("North Node")
        if nat is None:
            return []
        out = []
        for i in range(1, 5):
            ev = self._return_event(
                "nodal_return", f"{['','1st','2nd','3rd','4th'][i]} Nodal Return",
                "North Node", nat, 0.0, i,
            )
            if ev:
                out.append(ev)
        return out

    def nodal_oppositions(self) -> List[LifecycleEvent]:
        nat = self.natal_long.get("North Node")
        if nat is None:
            return []
        out = []
        for i in range(1, 5):
            ev = self._return_event(
                "nodal_opposition", f"{['','1st','2nd','3rd','4th'][i]} Nodal Opposition",
                "North Node", nat, 180.0, i,
            )
            if ev:
                out.append(ev)
        return out

    # --- aggregate ----------------------------------------------------

    EVENT_GROUPS: Dict[str, str] = {
        "saturn_return":         "saturn_returns",
        "saturn_opposition":     "saturn_opposition",
        "saturn_square_saturn":  "saturn_square_saturn",
        "jupiter_return":        "jupiter_returns",
        "jupiter_opposition":    "jupiter_opposition",
        "uranus_opposition":     "uranus_opposition",
        "uranus_return":         "uranus_return",
        "neptune_square_neptune":"neptune_square_neptune",
        "pluto_square_pluto":    "pluto_square_pluto",
        "chiron_return":         "chiron_return",
        "nodal_return":          "nodal_returns",
        "nodal_opposition":      "nodal_oppositions",
    }

    def compute(self, event_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compute requested event(s) and return a structured envelope.

        If `event_keys` is None, computes the full lifecycle audit.
        """
        if not event_keys:
            event_keys = list(self.EVENT_GROUPS.keys())

        events: List[Dict[str, Any]] = []
        for k in event_keys:
            method_name = self.EVENT_GROUPS.get(k)
            if not method_name:
                continue
            method = getattr(self, method_name, None)
            if method is None:
                continue
            try:
                for ev in method():
                    events.append(ev.to_dict())
            except Exception as e:
                logger.warning(f"[LifecycleEngine] {k} failed: {e}")

        # Determine "active instance" per event_group for quick prompting
        active: Dict[str, Dict[str, Any]] = {}
        for ev in events:
            k = ev["key"]
            # Highest-priority match: phase=during, otherwise the next future,
            # otherwise the most recent past.
            current = active.get(k)
            if current is None:
                active[k] = ev
                continue
            # Prefer 'during'
            if ev["phase"] == "during" and current["phase"] != "during":
                active[k] = ev
                continue
            if ev["phase"] == current["phase"]:
                # If both before: pick closer (smaller positive months_to)
                # If both after: pick closer (smaller absolute months_to)
                if abs(ev["months_to_event"]) < abs(current["months_to_event"]):
                    active[k] = ev

        return {
            "build_marker":  BUILD_MARKER,
            "success":       True,
            "person": {
                "current_age_years": round(self.current_age_years, 2),
                "birth_utc":         self.birth.replace(microsecond=0).isoformat(),
                "now_utc":           self.now.replace(microsecond=0).isoformat(),
            },
            "events":        events,
            "active_by_key": active,
        }


# ---------------------------------------------------------------------------
# Public entrypoint used by mirror_chat.py
# ---------------------------------------------------------------------------

def compute_lifecycle(
    chart: Dict[str, Any],
    birth_utc: datetime,
    now_utc: Optional[datetime] = None,
    event_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    try:
        engine = LifecycleEngine(chart, birth_utc, now_utc)
        return engine.compute(event_keys)
    except Exception as e:
        logger.exception("[LifecycleEngine] fatal")
        return {
            "build_marker": BUILD_MARKER,
            "success":      False,
            "error":        str(e),
        }


# ---------------------------------------------------------------------------
# Prompt block builder
# ---------------------------------------------------------------------------

def build_lifecycle_proof_block(envelope: Dict[str, Any], user_phrasing_mode: str = "personal") -> str:
    """Render the lifecycle envelope into a strict prompt block.

    `user_phrasing_mode`:
        "personal"   — user asked about "my X" / "when does my X" — LLM must
                       lead with the person, then briefly contextualize.
        "concept"    — user asked "what is X" / "explain X generally" —
                       LLM explains the concept first, then in 1–2 sentences
                       anchors to this user's actual position.
        "concept_no_anchor" — pure "explain X" without any chart reference —
                       LLM stays educational, no personalization.
    """
    if not envelope or not envelope.get("success"):
        return ""

    person = envelope.get("person") or {}
    events = envelope.get("events") or []
    active = envelope.get("active_by_key") or {}

    if not events:
        return ""

    lines: List[str] = []
    lines.append("\n=== LIFECYCLE PROOF BLOCK — astrology-lifecycle-v1 ===")
    lines.append(
        f"USER current age: {person.get('current_age_years')}  "
        f"(birth UTC {person.get('birth_utc')})"
    )
    lines.append("")
    lines.append("ACTIVE LIFECYCLE INSTANCES (this user, right now):")
    for k, ev in sorted(active.items()):
        lines.append(
            f"  • {ev['label']}: phase={ev['phase']}  "
            f"exact_passes={ev['exact_passes']}  "
            f"window=[{ev['window_start']} .. {ev['window_end']}]  "
            f"months_to_event={ev['months_to_event']}"
        )
        if ev.get("meaning"):
            lines.append(f"      meaning: {ev['meaning']}")
    lines.append("")
    lines.append("FULL TIMELINE OF EVENTS (chronological by exact_pass):")
    for ev in sorted(events, key=lambda x: x["exact_passes"][0] if x["exact_passes"] else ""):
        passes_str = ", ".join(ev["exact_passes"]) if ev["exact_passes"] else "n/a"
        lines.append(
            f"  - {ev['label']} (instance {ev['instance']}): "
            f"phase={ev['phase']}  passes=[{passes_str}]  "
            f"expected_age={ev['expected_age_at']}"
        )

    lines.append("")
    lines.append("ABSOLUTE RULES (override any earlier voice or safety guard):")
    if user_phrasing_mode == "personal":
        lines.append("  1. ANSWER THE PERSON BEFORE THE CONCEPT.")
        lines.append("     Open with the user's actual lifecycle position from the")
        lines.append("     ACTIVE LIFECYCLE INSTANCES block above. Name the instance")
        lines.append("     (1st / 2nd / 3rd), state the phase (before/during/after),")
        lines.append("     and quote the exact date window.")
        lines.append("  2. Use the `meaning` field to distinguish 1st vs 2nd vs 3rd —")
        lines.append("     do NOT collapse them into the same explanation.")
        lines.append("  3. Brief textbook context ONLY after the person is located.")
        lines.append("     Max one sentence of generic definition.")
        lines.append("  4. NEVER say 'on the horizon if it hasn't begun already' or")
        lines.append("     similar vague hedging when the exact passes above are known.")
        lines.append("  5. NEVER respond with a closing question or coaching prompt.")
        lines.append("  6. If user is currently DURING a return, do NOT refer to it as")
        lines.append("     'upcoming' — they are IN it. If AFTER, do NOT call it ")
        lines.append("     'next' — it has already happened.")
    elif user_phrasing_mode == "concept":
        lines.append("  1. Open with a concise concept explanation (2-3 sentences).")
        lines.append("  2. THEN add a single paragraph anchored to the user's actual")
        lines.append("     position from ACTIVE LIFECYCLE INSTANCES — name the")
        lines.append("     instance, phase, and exact pass dates.")
        lines.append("  3. Do not invent dates that are not in the proof block.")
    else:  # concept_no_anchor
        lines.append("  1. Educational explanation only. Do not personalize.")

    lines.append("=========================================================\n")
    return "\n".join(lines)


__all__ = [
    "BUILD_MARKER",
    "LifecycleEngine",
    "LifecycleEvent",
    "compute_lifecycle",
    "build_lifecycle_proof_block",
    "DURING_WINDOW_MONTHS",
    "MEANING_BY_INSTANCE",
]
