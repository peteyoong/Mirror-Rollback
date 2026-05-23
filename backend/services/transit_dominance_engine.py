"""
Transit Dominance Engine
==========================

Deterministic pipeline that makes "Astrology Today" genuinely time-aware
instead of always serving the same background diagnosis.

Responsibilities (single module, single source of truth)
--------------------------------------------------------
  1. Snapshot current True Sidereal positions for all 10 major bodies
     (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
     Pluto) using the canonical sidereal_config.
  2. Compute Moon phase and nearest New/Full lunation.
  3. Detect sign ingresses inside a tiered window:
       - outer planets (Jupiter→Pluto) within ±7-14d (slow movers)
       - personal planets (Mercury, Venus, Mars) within ±3d
       - luminaries (Sun, Moon) always sign-change-aware
  4. Compute transit-to-natal aspects with a TIGHT orb budget:
       - conjunction / opposition : 3°
       - trine / square           : 2°
       - sextile                  : 1°
     Applying/separating flagged by sampling the orb at dt and dt+1d.
  5. Rank detected signals into 3 tiers per the brief:
       - TIER 1 OVERRIDE: Full/New Moon ±48h, eclipses ±7d, outer-planet
         ingresses, ≤0.5° tight aspects, Moon conj/opp natal luminaries.
       - TIER 2 STRONG: Moon sign change today, personal-planet ingress
         ±3d, tight aspects ≤1.5°, sign or house concentrations.
       - TIER 3 BACKGROUND: slow placements, wide aspects.
  6. Emit a stable `signature_hash` so the caller can detect whether
     today's dominance actually changed vs yesterday — this is the
     anti-repetition key.

No LLM. No interpretation. This module ONLY produces structured data.
The v5 endpoint does the interpretation step on top.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from calculations.sidereal_config import (
    ZODIAC_SIGNS,
    calculate_planet_sidereal,
    get_all_transiting_planets,
    PLANETS as _SWE_PLANETS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical aspect set with TIGHT orb budget (per spec § P1 "SIGNAL TIERS")
#   aspect_name: (exact_angle, tight_orb, strong_orb)
ASPECTS: Dict[str, Dict[str, float]] = {
    "conjunction": {"angle": 0.0,   "tight": 0.5, "strong": 3.0},
    "opposition":  {"angle": 180.0, "tight": 0.5, "strong": 3.0},
    "trine":       {"angle": 120.0, "tight": 0.5, "strong": 2.0},
    "square":      {"angle": 90.0,  "tight": 0.5, "strong": 2.0},
    "sextile":     {"angle": 60.0,  "tight": 0.5, "strong": 1.0},
}

# Planets grouped by speed — drives ingress window + tier weighting
OUTER_PLANETS    = ("Uranus", "Neptune", "Pluto")
HEAVY_PLANETS    = ("Saturn", "Jupiter")
PERSONAL_PLANETS = ("Mercury", "Venus", "Mars")
LUMINARIES       = ("Sun", "Moon")
ALL_BODIES       = LUMINARIES + PERSONAL_PLANETS + HEAVY_PLANETS + OUTER_PLANETS

# Moon phase bucketing (angle = Moon lon − Sun lon, normalised 0-360)
def _moon_phase_label(angle: float) -> Tuple[str, str]:
    """Return (phase_key, phase_human). phase_key is stable for hashing."""
    if angle < 7 or angle >= 353:
        return ("new_moon", "New Moon")
    if angle < 83:
        return ("waxing_crescent", "Waxing Crescent")
    if angle < 97:
        return ("first_quarter", "First Quarter")
    if angle < 173:
        return ("waxing_gibbous", "Waxing Gibbous")
    if angle < 187:
        return ("full_moon", "Full Moon")
    if angle < 263:
        return ("waning_gibbous", "Waning Gibbous")
    if angle < 277:
        return ("last_quarter", "Last Quarter")
    return ("waning_crescent", "Waning Crescent")


def _angular_distance(lon1: float, lon2: float) -> float:
    """Signed minimal angular distance (-180, 180]."""
    d = (lon1 - lon2 + 180) % 360 - 180
    return d


# ---------------------------------------------------------------------------
# Sky state
# ---------------------------------------------------------------------------

def get_sky_state(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """Return all 10 major bodies + metadata for dt (default = now UTC)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    bodies = get_all_transiting_planets(dt)
    # Filter out any keys not in our canonical list
    compact: Dict[str, Any] = {}
    for name in ALL_BODIES:
        if name in bodies:
            p = bodies[name]
            compact[name] = {
                "sign":        p["sign"],
                "degree":      round(p["degree"], 4),
                "longitude":   round(p["longitude"], 6),
                "retrograde":  bool(p.get("retrograde", False)),
                "formatted":   p.get("formatted"),
            }
    return {
        "timestamp_utc": dt.isoformat(),
        "bodies":        compact,
    }


# ---------------------------------------------------------------------------
# Moon phase + lunation search
# ---------------------------------------------------------------------------

def _sun_moon_angle(dt: datetime) -> float:
    sun  = calculate_planet_sidereal(_SWE_PLANETS["Sun"],  dt)["longitude"]
    moon = calculate_planet_sidereal(_SWE_PLANETS["Moon"], dt)["longitude"]
    return (moon - sun) % 360.0


def _search_lunation_crossing(
    dt: datetime, target_angle: float, max_hours: int = 180,
) -> Optional[datetime]:
    """Find the nearest time the Sun-Moon angle crosses target_angle.

    Scans ±max_hours in 3-hour steps, detects a genuine (not wrap-around)
    zero crossing, then bisects to ~1-minute precision. Returns None if
    no crossing is found within the window.

    IMPORTANT: the raw signed-distance function has a discontinuity at
    the antipode of `target_angle` — e.g. for target=0° the signed
    distance jumps from +170° to -170° as the angle crosses 180°. That
    jump LOOKS like a sign change but isn't a real zero crossing. We
    filter for crossings where both samples have |distance| < 45° so
    only real crossings pass.
    """
    step = timedelta(hours=3)
    f = lambda t: _angular_distance(_sun_moon_angle(t), target_angle)

    best_pair: Optional[Tuple[datetime, datetime]] = None
    best_gap = 999.0

    t0 = dt - timedelta(hours=max_hours)
    prev_t = t0
    prev_v = f(prev_t)
    steps = int((2 * max_hours) / 3)
    for i in range(1, steps + 1):
        cur_t = t0 + step * i
        cur_v = f(cur_t)
        # Real zero crossing: sign change AND both samples are within
        # ±45° of the target (rules out the antipode discontinuity).
        if prev_v * cur_v < 0 and abs(prev_v) < 45 and abs(cur_v) < 45:
            gap = abs((cur_t - dt).total_seconds()) / 3600.0
            if gap < best_gap:
                best_gap = gap
                best_pair = (prev_t, cur_t)
        prev_t, prev_v = cur_t, cur_v

    if not best_pair:
        return None

    # Bisection to refine
    lo, hi = best_pair
    for _ in range(30):
        mid = lo + (hi - lo) / 2
        if f(lo) * f(mid) < 0:
            hi = mid
        else:
            lo = mid
        if (hi - lo).total_seconds() < 60:
            break
    return lo + (hi - lo) / 2


def compute_moon_phase(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """Return moon phase, angle, and nearest New + Full Moon times."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    angle = _sun_moon_angle(dt)
    key, human = _moon_phase_label(angle)

    nearest_new  = _search_lunation_crossing(dt, 0.0, max_hours=360)
    nearest_full = _search_lunation_crossing(dt, 180.0, max_hours=360)

    def _dt_info(t: Optional[datetime]) -> Optional[Dict[str, Any]]:
        if not t:
            return None
        delta_hours = (t - dt).total_seconds() / 3600.0
        return {
            "at_utc":      t.isoformat(),
            "hours_offset": round(delta_hours, 2),
            "within_48h": abs(delta_hours) <= 48,
            "within_7d":  abs(delta_hours) <= 24 * 7,
        }

    return {
        "sun_moon_angle_deg": round(angle, 3),
        "phase_key":          key,
        "phase_human":        human,
        "nearest_new_moon":   _dt_info(nearest_new),
        "nearest_full_moon":  _dt_info(nearest_full),
    }


# ---------------------------------------------------------------------------
# Ingress detection
# ---------------------------------------------------------------------------

def detect_ingresses(
    dt: Optional[datetime] = None,
    window_days_outer: int = 14,
    window_days_heavy: int = 7,
    window_days_personal: int = 3,
    window_days_moon: int = 2,
) -> List[Dict[str, Any]]:
    """Find planet sign changes inside tiered windows.

    Strategy: for each planet, sample longitudes on a daily grid and
    look for the discrete sign-index transition. Bisect to hour
    precision.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    plans: List[Tuple[str, int]] = []
    for p in OUTER_PLANETS:    plans.append((p, window_days_outer))
    for p in HEAVY_PLANETS:    plans.append((p, window_days_heavy))
    for p in PERSONAL_PLANETS: plans.append((p, window_days_personal))
    plans.append(("Sun",  window_days_personal))
    plans.append(("Moon", window_days_moon))

    ingresses: List[Dict[str, Any]] = []
    # Sign-index helper honours global attribution mode.
    # Build marker: true-sidereal-midpoint-production-migration-v1
    from calculations.astrology import longitude_to_sign_degree as _lts
    def _sign_idx(lon_sid: float) -> int:
        return _lts(lon_sid % 360)["sign_index"]

    for planet, days in plans:
        pid = _SWE_PLANETS[planet]
        # Sample at 6-hour resolution for the Moon (fast), 1-day for others
        step_hours = 6 if planet == "Moon" else 24
        t0 = dt - timedelta(days=days)
        t_cur = t0
        prev_lon = calculate_planet_sidereal(pid, t_cur)["longitude"]
        prev_sign = _sign_idx(prev_lon)
        total_steps = int((2 * days * 24) / step_hours)
        for _ in range(total_steps):
            t_cur = t_cur + timedelta(hours=step_hours)
            cur_lon = calculate_planet_sidereal(pid, t_cur)["longitude"]
            cur_sign = _sign_idx(cur_lon)
            if cur_sign != prev_sign:
                # Bisect to hour precision within (t_cur - step, t_cur)
                lo = t_cur - timedelta(hours=step_hours)
                hi = t_cur
                for _ in range(18):
                    mid = lo + (hi - lo) / 2
                    lon_mid = calculate_planet_sidereal(pid, mid)["longitude"]
                    sign_mid = _sign_idx(lon_mid)
                    if sign_mid == prev_sign:
                        lo = mid
                    else:
                        hi = mid
                    if (hi - lo).total_seconds() < 3600:
                        break
                ingress_t = lo + (hi - lo) / 2
                delta_hours = (ingress_t - dt).total_seconds() / 3600.0
                ingresses.append({
                    "planet":         planet,
                    "from_sign":      ZODIAC_SIGNS[prev_sign],
                    "to_sign":        ZODIAC_SIGNS[cur_sign],
                    "at_utc":         ingress_t.isoformat(),
                    "hours_offset":   round(delta_hours, 2),
                    "days_offset":    round(delta_hours / 24, 2),
                    "is_outer":       planet in OUTER_PLANETS,
                    "is_heavy":       planet in HEAVY_PLANETS,
                    "is_personal":    planet in PERSONAL_PLANETS,
                    "is_luminary":    planet in LUMINARIES,
                })
            prev_sign = cur_sign
    return ingresses


# ---------------------------------------------------------------------------
# Transit-to-natal aspects
# ---------------------------------------------------------------------------

def _resolve_aspect(delta: float) -> Optional[Tuple[str, float]]:
    """Given a signed angular distance between two longitudes, return
    the matching aspect name + orb (absolute) if within STRONG orb."""
    abs_d = abs(delta)
    for name, spec in ASPECTS.items():
        orb = abs(abs_d - spec["angle"])
        # Also check opposition 180° / conjunction 0° wrap
        if name == "conjunction":
            orb = min(abs_d, 360 - abs_d)
        if orb <= spec["strong"]:
            return (name, round(orb, 3))
    return None


def _extract_natal_planets(chart_doc: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Pull {name: {longitude, sign, house}} out of a user's chart doc."""
    if not isinstance(chart_doc, dict):
        return {}
    astro = chart_doc.get("astrology") or chart_doc.get("natal") or {}
    raw = astro.get("planets") or {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, p in raw.items():
        if not isinstance(p, dict):
            continue
        lon = p.get("longitude")
        if lon is None:
            continue
        out[name] = {
            "longitude": float(lon),
            "sign":      p.get("sign"),
            "house":     p.get("house"),
        }
    return out


def compute_transit_natal_aspects(
    sky: Dict[str, Any],
    natal_planets: Dict[str, Dict[str, Any]],
    dt: datetime,
) -> List[Dict[str, Any]]:
    """Compute transit-to-natal aspects for every pair within STRONG orb.

    Also computes applying/separating by resampling at dt+1d and
    comparing orbs. Natal longitudes are static; only the transit
    side moves.
    """
    if not natal_planets or not sky.get("bodies"):
        return []

    tomorrow = dt + timedelta(days=1)
    aspects: List[Dict[str, Any]] = []

    for t_name, t in sky["bodies"].items():
        t_lon = t["longitude"]
        try:
            t_lon_tomorrow = calculate_planet_sidereal(
                _SWE_PLANETS[t_name], tomorrow,
            )["longitude"]
        except Exception:
            t_lon_tomorrow = t_lon

        for n_name, n in natal_planets.items():
            n_lon = n["longitude"]
            delta = _angular_distance(t_lon, n_lon)
            res = _resolve_aspect(delta)
            if not res:
                continue
            aspect_name, orb = res

            # Orb tomorrow → applying vs separating
            delta_t = _angular_distance(t_lon_tomorrow, n_lon)
            res_t = _resolve_aspect(delta_t)
            if res_t and res_t[0] == aspect_name:
                orb_tomorrow = res_t[1]
                status = "applying" if orb_tomorrow < orb else "separating"
            else:
                status = "separating"  # aspect is dissolving

            spec = ASPECTS[aspect_name]
            is_tight = orb <= spec["tight"]

            aspects.append({
                "id":             f"{t_name}-{aspect_name}-{n_name}",
                "transit":        t_name,
                "aspect":         aspect_name,
                "natal":          n_name,
                "orb":            orb,
                "applying":       status == "applying",
                "is_tight":       is_tight,  # ≤ 0.5° — Tier 1
                "exact_angle":    spec["angle"],
                "natal_house":    n.get("house"),
                "transit_sign":   t["sign"],
                "natal_sign":     n["sign"],
            })
    # Sort by orb ascending — tightest first
    aspects.sort(key=lambda a: a["orb"])
    return aspects


# ---------------------------------------------------------------------------
# House activations
# ---------------------------------------------------------------------------

def compute_house_activations(
    sky: Dict[str, Any],
    chart_doc: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Count how many transiting bodies are sitting in each natal house.

    Uses natal house cusps if available. If the chart was stored with
    precomputed 'house' on each natal planet but no cusps, we fall
    back to per-transit lookup via nearest-cusp heuristic — but most
    stored charts already carry cusps.
    """
    if not chart_doc or not sky.get("bodies"):
        return {"by_house": {}, "clusters": []}

    astro = chart_doc.get("astrology") or chart_doc.get("natal") or {}
    houses_block = astro.get("houses") or {}
    cusps = houses_block.get("cusps") if isinstance(houses_block, dict) else None

    by_house: Dict[int, List[str]] = {i: [] for i in range(1, 13)}
    if isinstance(cusps, list) and len(cusps) >= 12:
        for name, t in sky["bodies"].items():
            t_lon = float(t["longitude"])
            h = _resolve_house(t_lon, cusps)
            if 1 <= h <= 12:
                by_house[h].append(name)

    # Clusters = any house with ≥3 transits
    clusters = [
        {"house": h, "bodies": bs}
        for h, bs in by_house.items() if len(bs) >= 3
    ]
    return {
        "by_house": {str(h): bs for h, bs in by_house.items() if bs},
        "clusters": clusters,
    }


def _resolve_house(lon: float, cusps: List[Any]) -> int:
    """Given a longitude and 12 house cusps, return 1-12."""
    # Normalise cusp values to floats mod 360
    try:
        vals = []
        for c in cusps[:12]:
            if isinstance(c, dict):
                vals.append(float(c.get("longitude", 0)) % 360)
            else:
                vals.append(float(c) % 360)
    except Exception:
        return 0
    lon_n = lon % 360
    for i in range(12):
        start = vals[i]
        end = vals[(i + 1) % 12]
        if start <= end:
            if start <= lon_n < end:
                return i + 1
        else:  # wraps 360 → 0
            if lon_n >= start or lon_n < end:
                return i + 1
    return 0


# ---------------------------------------------------------------------------
# Signal classification (Tier 1 / 2 / 3)
# ---------------------------------------------------------------------------

def classify_signals(
    moon_phase: Dict[str, Any],
    ingresses: List[Dict[str, Any]],
    aspects: List[Dict[str, Any]],
    house_activations: Dict[str, Any],
    prior_moon_sign: Optional[str] = None,
    sky: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ranks signals into Tier 1 / 2 / 3 per the spec. Emits a
    dominant_signal + secondary_signals + background_signals bundle.
    """
    tier1: List[Dict[str, Any]] = []
    tier2: List[Dict[str, Any]] = []
    tier3: List[Dict[str, Any]] = []

    # --- Tier 1 -----------------------------------------------------------

    # Full Moon / New Moon within ±48h
    nfm = moon_phase.get("nearest_full_moon") or {}
    nnm = moon_phase.get("nearest_new_moon") or {}
    if nfm.get("within_48h"):
        tier1.append({
            "type":        "full_moon",
            "phase_key":   "full_moon",
            "at_utc":      nfm["at_utc"],
            "hours":       nfm["hours_offset"],
            "label":       "Full Moon",
        })
    if nnm.get("within_48h"):
        tier1.append({
            "type":        "new_moon",
            "phase_key":   "new_moon",
            "at_utc":      nnm["at_utc"],
            "hours":       nnm["hours_offset"],
            "label":       "New Moon",
        })

    # Outer-planet ingress within ±14d (already filtered by the detector)
    for ing in ingresses:
        if ing["is_outer"]:
            tier1.append({
                "type":        "outer_ingress",
                "planet":      ing["planet"],
                "from_sign":   ing["from_sign"],
                "to_sign":     ing["to_sign"],
                "at_utc":      ing["at_utc"],
                "days":        ing["days_offset"],
                "label":       f"{ing['planet']} → {ing['to_sign']}",
            })
        elif ing["is_heavy"] and abs(ing["days_offset"]) <= 7:
            tier1.append({
                "type":        "heavy_ingress",
                "planet":      ing["planet"],
                "from_sign":   ing["from_sign"],
                "to_sign":     ing["to_sign"],
                "at_utc":      ing["at_utc"],
                "days":        ing["days_offset"],
                "label":       f"{ing['planet']} → {ing['to_sign']}",
            })

    # Exact natal aspects ≤0.5°
    for asp in aspects:
        if asp["is_tight"]:
            tier1.append({
                "type":      "tight_aspect",
                "transit":   asp["transit"],
                "aspect":    asp["aspect"],
                "natal":     asp["natal"],
                "orb":       asp["orb"],
                "applying":  asp["applying"],
                "house":     asp["natal_house"],
                "label":     f"{asp['transit']} {asp['aspect']} natal {asp['natal']}",
            })

    # Moon conj/opp natal Sun/Moon, orb ≤1°
    for asp in aspects:
        if (
            asp["transit"] == "Moon"
            and asp["aspect"] in ("conjunction", "opposition")
            and asp["natal"] in ("Sun", "Moon")
            and asp["orb"] <= 1.0
        ):
            tier1.append({
                "type":     "moon_luminary_trigger",
                "transit":  "Moon",
                "aspect":   asp["aspect"],
                "natal":    asp["natal"],
                "orb":      asp["orb"],
                "label":    f"Moon {asp['aspect']} natal {asp['natal']}",
            })

    # --- Tier 2 -----------------------------------------------------------

    # Moon sign change today
    moon_sign_now = (sky or {}).get("bodies", {}).get("Moon", {}).get("sign")
    if prior_moon_sign and moon_sign_now and moon_sign_now != prior_moon_sign:
        tier2.append({
            "type":      "moon_sign_change",
            "from_sign": prior_moon_sign,
            "to_sign":   moon_sign_now,
            "label":     f"Moon entered {moon_sign_now}",
        })

    # Personal ingress ±3d
    for ing in ingresses:
        if ing["is_personal"] and abs(ing["days_offset"]) <= 3:
            tier2.append({
                "type":      "personal_ingress",
                "planet":    ing["planet"],
                "from_sign": ing["from_sign"],
                "to_sign":   ing["to_sign"],
                "days":      ing["days_offset"],
                "label":     f"{ing['planet']} → {ing['to_sign']}",
            })

    # Strong (non-tight) aspects ≤1.5°
    for asp in aspects:
        if not asp["is_tight"] and asp["orb"] <= 1.5:
            tier2.append({
                "type":     "strong_aspect",
                "transit":  asp["transit"],
                "aspect":   asp["aspect"],
                "natal":    asp["natal"],
                "orb":      asp["orb"],
                "applying": asp["applying"],
                "house":    asp["natal_house"],
                "label":    f"{asp['transit']} {asp['aspect']} natal {asp['natal']}",
            })

    # 3+ bodies in one sign (computed from sky)
    sign_counts: Dict[str, List[str]] = {}
    for name, body in (sky or {}).get("bodies", {}).items():
        sign_counts.setdefault(body["sign"], []).append(name)
    for sign, bodies in sign_counts.items():
        if len(bodies) >= 3:
            tier2.append({
                "type":   "sign_cluster",
                "sign":   sign,
                "bodies": bodies,
                "label":  f"{len(bodies)} bodies in {sign}",
            })

    # 3+ activations in one house
    for cluster in house_activations.get("clusters", []):
        tier2.append({
            "type":   "house_cluster",
            "house":  cluster["house"],
            "bodies": cluster["bodies"],
            "label":  f"{len(cluster['bodies'])} bodies in house {cluster['house']}",
        })

    # --- Tier 3 -----------------------------------------------------------

    # Slow outer placements & wide aspects
    for asp in aspects[:5]:
        if asp["orb"] > 1.5:
            tier3.append({
                "type":    "wide_aspect",
                "transit": asp["transit"],
                "aspect":  asp["aspect"],
                "natal":   asp["natal"],
                "orb":     asp["orb"],
                "label":   f"{asp['transit']} {asp['aspect']} natal {asp['natal']} ({asp['orb']}°)",
            })

    # Pick dominant signal: Tier1 > Tier2 > Tier3
    dominant: Optional[Dict[str, Any]]
    if tier1:
        dominant = tier1[0]
    elif tier2:
        dominant = tier2[0]
    elif tier3:
        dominant = tier3[0]
    else:
        dominant = None

    # Intensity
    if tier1:
        intensity = "high"
    elif tier2:
        intensity = "medium"
    else:
        intensity = "low"

    # ---- Signal conflict detection ---------------------------------------
    # A "conflict" exists when multiple DISTINCT pressure types are live
    # at the same time — the day isn't a single-theme day. We bucket
    # the live signals into coarse pressure categories and flag
    # conflict when ≥2 categories are active at Tier 1/2 level.
    #
    # Categories:
    #   lunation   (full/new moon ±48h)
    #   ingress    (outer/heavy/personal sign change in window)
    #   aspect     (tight or strong transit-to-natal)
    #   moon_move  (moon sign change today, moon-luminary trigger)
    #   cluster    (sign or house cluster)
    live: set = set()
    for s in tier1 + tier2:
        t = s.get("type", "")
        if t in ("full_moon", "new_moon"):
            live.add("lunation")
        elif t in ("outer_ingress", "heavy_ingress", "personal_ingress"):
            live.add("ingress")
        elif t in ("tight_aspect", "strong_aspect"):
            live.add("aspect")
        elif t in ("moon_sign_change", "moon_luminary_trigger"):
            live.add("moon_move")
        elif t in ("sign_cluster", "house_cluster"):
            live.add("cluster")
    signal_conflict = len(live) >= 2

    # why_today_is_different — short phrase derived from tier content
    why = _build_why_line(dominant, tier1, tier2, intensity)

    return {
        "dominant_signal":    dominant,
        "secondary_signals":  tier1[1:] + tier2[:3],  # skip the dominant; keep top context
        "background_signals": tier3[:4],
        "tier1_all":          tier1,
        "tier2_all":          tier2,
        "tier3_all":          tier3,
        "intensity":          intensity,
        "signal_conflict":    signal_conflict,
        "active_categories":  sorted(list(live)),
        "why_today_is_different": why,
    }


def _build_why_line(
    dominant: Optional[Dict[str, Any]],
    tier1: List[Dict[str, Any]],
    tier2: List[Dict[str, Any]],
    intensity: str,
) -> str:
    if not dominant:
        return "A quiet day. No major timing signal is pressing — the background is doing most of the work."
    t = dominant["type"]
    if t == "full_moon":
        return "The Full Moon is within 48 hours — culmination energy dominates."
    if t == "new_moon":
        return "The New Moon is within 48 hours — this is a seeding window."
    if t == "outer_ingress":
        return f"{dominant['planet']} is changing sign ({dominant['from_sign']} → {dominant['to_sign']}) — a long-range background shift is active."
    if t == "heavy_ingress":
        return f"{dominant['planet']} is changing sign soon — structural background is shifting."
    if t == "tight_aspect":
        return f"A tight natal aspect (≤0.5° orb) is exact: {dominant['transit']} {dominant['aspect']} natal {dominant['natal']}."
    if t == "moon_luminary_trigger":
        return f"The Moon is triggering your natal {dominant['natal']} — short-lived but sharp."
    if t == "moon_sign_change":
        return f"The Moon has moved into {dominant['to_sign']} — a fresh emotional frame for the day."
    if t == "personal_ingress":
        return f"{dominant['planet']} is crossing into {dominant['to_sign']} within a few days."
    if t == "strong_aspect":
        return f"{dominant['transit']} is approaching a notable aspect to your natal {dominant['natal']}."
    if t == "sign_cluster":
        return f"{len(dominant['bodies'])} bodies are concentrated in {dominant['sign']}."
    if t == "house_cluster":
        return f"{len(dominant['bodies'])} bodies are activating house {dominant['house']}."
    return f"Today is shaped by a {intensity}-intensity signal."


# ---------------------------------------------------------------------------
# Signature hash
# ---------------------------------------------------------------------------

def compute_signature_hash(classification: Dict[str, Any]) -> str:
    """Stable short hash summarising the day's signal shape. Two
    consecutive days with the same hash → same dominance → continuity
    language at interpretation time."""
    dom = classification.get("dominant_signal") or {}
    parts: List[str] = []

    parts.append(dom.get("type", "none"))
    # Include identity-defining fields per dominant type
    if dom.get("type") in ("tight_aspect", "strong_aspect", "moon_luminary_trigger"):
        parts.append(f"{dom.get('transit')}::{dom.get('aspect')}::{dom.get('natal')}")
    if dom.get("type") in ("outer_ingress", "heavy_ingress", "personal_ingress"):
        parts.append(f"{dom.get('planet')}::{dom.get('to_sign')}")
    if dom.get("type") == "moon_sign_change":
        parts.append(f"Moon::{dom.get('to_sign')}")
    if dom.get("type") in ("sign_cluster",):
        parts.append(f"cluster::{dom.get('sign')}")
    if dom.get("type") in ("house_cluster",):
        parts.append(f"house::{dom.get('house')}")

    # Always include moon_sign + top tier2 type for finer granularity
    t2 = classification.get("tier2_all") or []
    if t2:
        parts.append(f"t2::{t2[0].get('type')}")

    raw = "|".join(parts)
    h = hashlib.blake2b(raw.encode("utf-8"), digest_size=6).hexdigest()
    return h


# ---------------------------------------------------------------------------
# Orchestrator (public API)
# ---------------------------------------------------------------------------

def build_dominance_payload(
    user_id: str,
    chart_doc: Optional[Dict[str, Any]] = None,
    dt: Optional[datetime] = None,
    prior_day_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Single-call pipeline that every consumer of the transit dominance
    engine uses. Deterministic, no LLM."""
    if dt is None:
        dt = datetime.now(timezone.utc)

    sky = get_sky_state(dt)
    phase = compute_moon_phase(dt)
    ingresses = detect_ingresses(dt)
    natal_planets = _extract_natal_planets(chart_doc)
    aspects = compute_transit_natal_aspects(sky, natal_planets, dt)
    house_activations = compute_house_activations(sky, chart_doc)

    # Prior Moon sign (for moon-sign-change detection) — from the prior
    # day's stored dominance payload if caller passed one.
    prior_moon_sign: Optional[str] = None
    if isinstance(prior_day_payload, dict):
        prior_moon_sign = (
            ((prior_day_payload.get("sky") or {}).get("bodies") or {})
            .get("Moon", {}).get("sign")
        )

    classification = classify_signals(
        moon_phase=phase,
        ingresses=ingresses,
        aspects=aspects,
        house_activations=house_activations,
        prior_moon_sign=prior_moon_sign,
        sky=sky,
    )

    sig = compute_signature_hash(classification)
    prior_sig = (prior_day_payload or {}).get("signature_hash") if prior_day_payload else None

    return {
        "user_id":              user_id,
        "timestamp_utc":        dt.isoformat(),
        "sky":                  sky,
        "moon_phase":           phase,
        "ingresses":            ingresses,
        "transit_natal_aspects": aspects,
        "house_activations":    house_activations,
        "dominant_signal":      classification["dominant_signal"],
        "secondary_signals":    classification["secondary_signals"],
        "background_signals":   classification["background_signals"],
        "intensity":            classification["intensity"],
        "signal_conflict":      classification.get("signal_conflict", False),
        "active_categories":    classification.get("active_categories", []),
        "why_today_is_different": classification["why_today_is_different"],
        "signature_hash":       sig,
        "signature_changed":    prior_sig is not None and prior_sig != sig,
        "prior_signature_hash": prior_sig,
        "aspect_count":         len(aspects),
        "tight_aspect_count":   sum(1 for a in aspects if a["is_tight"]),
    }


def build_debug_payload(
    user_id: str,
    chart_doc: Optional[Dict[str, Any]] = None,
    dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Verbose debug surface for /api/astrology/today-debug/{user_id}.
    Adds the next 7 days of sky + ingress/lunation preview."""
    if dt is None:
        dt = datetime.now(timezone.utc)

    base = build_dominance_payload(user_id, chart_doc, dt=dt)

    # 7-day preview of key bodies
    preview: List[Dict[str, Any]] = []
    for offset in range(1, 8):
        t = dt + timedelta(days=offset)
        sk = get_sky_state(t)
        preview.append({
            "date":     t.strftime("%Y-%m-%d"),
            "sun":      sk["bodies"].get("Sun"),
            "moon":     sk["bodies"].get("Moon"),
            "mercury":  sk["bodies"].get("Mercury"),
        })

    base["seven_day_preview"] = preview
    base["debug_generated_at"] = datetime.now(timezone.utc).isoformat()
    return base


__all__ = [
    "ALL_BODIES",
    "ASPECTS",
    "build_dominance_payload",
    "build_debug_payload",
    "compute_house_activations",
    "compute_moon_phase",
    "compute_signature_hash",
    "compute_transit_natal_aspects",
    "detect_ingresses",
    "get_sky_state",
    "classify_signals",
]
