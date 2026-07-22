"""Transit Timing Engine — Timeline Intelligence V2 · Phase 4 plug-in
====================================================================
Surface marker: transit-timing-engine-v1

Computes tight natal-to-transit aspects on a given date, focussed on
the two loci that carry the year's attention under Mirror's timing
model:

    1. the natal position of the Lord of the Year
       (as reported by the AnnualProfection engine),
    2. the four natal angles — ASC · MC · IC · DC.

Any aspect within a tight orb (see `_ASPECT_TABLE`) is surfaced.
Aspects to slow-moving outer transits (Saturn / Uranus / Neptune /
Pluto) are weighted higher — they mark durable pressure windows, not
day-to-day noise.

Deterministic. No LLM. No I/O. Same inputs → same output.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime  import date, datetime, timezone as _tz
from typing    import Any, Dict, List, Optional, Tuple

import swisseph as swe

from services.annual_profection_engine   import compute_profection
from services.timing_engine_protocol     import (
    Confidence, TimingEngine, TimingEvidence,
)

BUILD_MARKER = "transit-timing-engine-v1"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_TRANSITING_BODIES: List[Tuple[str, int]] = [
    ("Sun",     swe.SUN),      ("Moon",    swe.MOON),
    ("Mercury", swe.MERCURY),  ("Venus",   swe.VENUS),
    ("Mars",    swe.MARS),     ("Jupiter", swe.JUPITER),
    ("Saturn",  swe.SATURN),   ("Uranus",  swe.URANUS),
    ("Neptune", swe.NEPTUNE),  ("Pluto",   swe.PLUTO),
]

# aspect_deg, name, orb (deg). Deliberately tight — the Timeline shows
# durable pressure, not fleeting geometry.
_ASPECT_TABLE = [
    (0.0,   "conjunction", 6.0),
    (60.0,  "sextile",     3.0),
    (90.0,  "square",      6.0),
    (120.0, "trine",       6.0),
    (180.0, "opposition",  6.0),
]

# Weight for scoring; outer-planet transits matter more on the Timeline.
_WEIGHT = {
    "Sun": 1.0, "Moon": 0.7, "Mercury": 0.8, "Venus": 0.9, "Mars": 1.2,
    "Jupiter": 1.4, "Saturn": 2.0, "Uranus": 2.2, "Neptune": 2.2, "Pluto": 2.4,
}

# Sidereal frame conversion (Mirror canonical Sharatan SVP).
SVP = 31.2836


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day,
                       dt.hour + dt.minute/60 + dt.second/3600,
                       swe.GREG_CAL)


def _transit_positions(dt: datetime) -> Dict[str, Dict[str, float]]:
    """Compute all 10 transiting bodies at `dt` (UTC). Returns sidereal
    longitudes in Mirror's Sharatan-anchored frame + speed °/day."""
    jd = _jd(dt)
    out: Dict[str, Dict[str, float]] = {}
    for name, code in _TRANSITING_BODIES:
        (lng_trop, lat, dist, spd_lng, spd_lat, spd_dist), _ = \
            swe.calc_ut(jd, code, swe.FLG_SPEED)
        out[name] = {
            "lng_tropical": lng_trop % 360.0,
            "lng_sidereal": (lng_trop - SVP) % 360.0,
            "speed":        spd_lng,
        }
    return out


def _aspect_between(a: float, b: float) -> Optional[Dict[str, Any]]:
    diff = abs((a - b + 180.0) % 360.0 - 180.0)
    for tgt, name, orb in _ASPECT_TABLE:
        if abs(diff - tgt) <= orb:
            return {"aspect": name, "target_deg": tgt,
                    "exact_sep": round(diff, 3),
                    "orb":       round(abs(diff - tgt), 3)}
    return None


def _applying(rel_speed: float,
                sep_now: float, target: float) -> str:
    """True if the aspect is tightening. `sep_now` = current angular
    separation (0..180). If the faster body is moving toward the exact
    aspect angle relative to the slower, we're applying."""
    # Positive rel_speed means transit body is pulling away in +longitude.
    if sep_now < target:
        return "applying" if rel_speed > 0 else "separating"
    return "separating" if rel_speed > 0 else "applying"


def _score(planet: str, orb: float) -> float:
    """Higher = more relevant for the Timeline. Weighted by planet
    slowness and orb tightness."""
    w = _WEIGHT.get(planet, 1.0)
    return round(w * max(0.0, 6.0 - orb), 3)


# ---------------------------------------------------------------------------
# Core: aspects to a single natal longitude
# ---------------------------------------------------------------------------
def _aspects_to(target_lng: float,
                 label: str,
                 transits: Dict[str, Dict[str, float]]
                 ) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for tname, td in transits.items():
        asp = _aspect_between(td["lng_sidereal"], target_lng)
        if not asp: continue
        # Relative speed vs target (target is stationary in natal terms).
        applying = _applying(td["speed"], asp["exact_sep"], asp["target_deg"])
        rows.append({
            "target":           label,
            "transiting":       tname,
            "aspect":           asp["aspect"],
            "orb":              asp["orb"],
            "exact_separation": asp["exact_sep"],
            "applying":         applying,
            "score":            _score(tname, asp["orb"]),
        })
    return rows


# ---------------------------------------------------------------------------
# Public plug-in
# ---------------------------------------------------------------------------
class TransitTimingEngine(TimingEngine):
    """Aspects from today's transits to the Lord of the Year + natal angles."""

    engine_id          = "transits"
    default_confidence: Confidence = "high"     # tight aspects are unambiguous
    engine_marker      = BUILD_MARKER

    def compute(self, *,
                 natal_chart: Dict[str, Any],
                 birth_datetime_utc: datetime,
                 target_date: Optional[date] = None,
                 extras: Optional[Dict[str, Any]] = None,
                 ) -> TimingEvidence:
        target_date = target_date or datetime.utcnow().date()

        # 1) Determine natal loci: Lord of the Year + four angles.
        try:
            prof = compute_profection(
                natal_chart        = natal_chart,
                birth_datetime_utc = birth_datetime_utc,
                target_date        = target_date,
            )
        except Exception as exc:   # pragma: no cover - defensive
            return TimingEvidence(
                engine_id="transits",
                name="Transits (unavailable)",
                meaning=f"could not compute profection first: {exc}",
                confidence="low", active=False,
                engine_marker=self.engine_marker,
            )

        planets = natal_chart.get("planets") or {}
        if isinstance(planets, list):
            planets = {p.get("name"): p for p in planets if isinstance(p, dict)}
        angles = natal_chart.get("angles") or {}

        loci: List[Tuple[str, float]] = []

        # Lord of the Year (may be None → Ophiuchus year: silent block).
        lord = prof.lord_of_the_year
        if lord and lord in planets:
            try:
                loci.append((f"Lord of the Year ({lord})",
                              float(planets[lord].get("longitude") or 0.0)))
            except (TypeError, ValueError):
                pass

        for k, human in (("asc","Ascendant"),("mc","MC"),
                          ("ic","IC"),("dc","Descendant")):
            v = angles.get(k) or {}
            try:
                lng = float(v.get("longitude"))
                loci.append((human, lng))
            except (TypeError, ValueError):
                pass

        if not loci:
            return TimingEvidence(
                engine_id="transits", name="Transits (silent)",
                meaning="no natal loci to measure against",
                confidence="low", active=False,
                engine_marker=self.engine_marker,
            )

        # 2) Compute current transit positions.
        dt_now = datetime(target_date.year, target_date.month,
                           target_date.day, 12, 0, 0, tzinfo=_tz.utc)
        transits = _transit_positions(dt_now)

        # 3) Aspects to each locus.
        rows: List[Dict[str, Any]] = []
        for label, natal_lng in loci:
            rows.extend(_aspects_to(natal_lng, label, transits))

        # 4) Rank by score, keep top 5.
        rows.sort(key=lambda r: (-r["score"], r["orb"]))
        top = rows[:5]

        # 5) Compose meaning line.
        if not top:
            meaning = ("No tight outer-body transits to the year's loci "
                        "right now — surface pressure is low; the year is "
                        "moving through its slower background material.")
        else:
            first = top[0]
            meaning = (
                f"{first['transiting']} is {first['aspect']} "
                f"{first['target']} within {first['orb']:.2f}°"
                f" ({first['applying']}). "
                "This tends to add pressure or lift to the year's theme."
            )

        # 6) Confidence: if the tightest aspect is >3° from exact, drop
        # to moderate. If nothing hits, low.
        conf: Confidence
        if not top:
            conf = "low"
        elif top[0]["orb"] > 3.0:
            conf = "moderate"
        else:
            conf = "high"

        return TimingEvidence(
            engine_id  = self.engine_id,
            name       = "Current Transits" + (" · nothing tight" if not top else ""),
            meaning    = meaning,
            confidence = conf,
            supporting_signals = [
                "Swiss Ephemeris (Mirror Sharatan frame)",
                f"natal Lord of the Year ({lord})" if lord else "natal angles only",
                "6° orb (majors); outer planets weighted higher",
            ],
            details = {
                "target_date": target_date.isoformat(),
                "lord_of_the_year_natal_lng":
                    float(planets[lord].get("longitude"))
                    if lord and lord in planets else None,
                "aspects_top": top,
                "aspects_all_count": len(rows),
                "loci_measured": [l for l, _ in loci],
            },
            engine_marker = self.engine_marker,
            active        = True,
        )


__all__ = ["BUILD_MARKER", "TransitTimingEngine"]
