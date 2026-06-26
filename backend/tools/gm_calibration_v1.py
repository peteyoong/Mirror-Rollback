"""
Project Mirror — GM Calibration Forensic Script v1
====================================================
Pure read-only computation. Does NOT touch any DB or production code.

Computes natal positions from scratch using Swiss Ephemeris for the
4 test subjects (Pete, Mel, Jaan, Ana) and compares them to the values
reported by Genetic Matrix screenshots.

Mode: True Sidereal-M (Midpoint) with User Defined SVP = 31.2836° at
reference year 2000 (no yearly increment, "Hybrid OFF").
- Topocentric planets.
- True Nodes.
- Modern planets.
- 13-sign midpoint boundary table (taken verbatim from Mirror's
  forensic module `calculations/true_sidereal_midpoint_boundaries.py`).
- Equal-house with Asc = cusp of house 1.

Output: a single calibration report and mismatch table.
"""
from __future__ import annotations

import os
import sys
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, List, Optional, Any

# Make repo importable
sys.path.insert(0, "/app/backend")

import swisseph as swe
swe.set_ephe_path("/app/backend/ephe")

# 13-sign midpoint table — verbatim from
# calculations/true_sidereal_midpoint_boundaries.py
SVP_DEG = 31.2836  # User Defined SVP

MIDPOINT_13: Dict[str, Tuple[float, float]] = {
    "Aries":       (0.0,      19.7286),
    "Taurus":      (19.7286,  56.5875),
    "Gemini":      (56.5875,  86.0412),
    "Cancer":      (86.0412,  103.19),
    "Leo":         (103.19,   141.6065),
    "Virgo":       (141.6065, 191.32),
    "Libra":       (191.32,   210.1972),
    "Scorpio":     (210.1972, 223.4245),
    "Ophiuchus":   (223.4245, 235.7818),
    "Sagittarius": (235.7818, 269.2677),
    "Capricorn":   (269.2677, 294.8435),
    "Aquarius":    (294.8435, 318.0103),
    "Pisces":      (318.0103, 360.0),
}


def to_sign(zodiacal_deg: float) -> Tuple[str, float]:
    z = zodiacal_deg % 360.0
    for name, (lo, hi) in MIDPOINT_13.items():
        if lo <= z < hi:
            return name, z - lo
    return "Pisces", z - 318.0103  # fallback


def deg_min(deg: float) -> str:
    d = int(deg)
    m_full = (deg - d) * 60.0
    m = int(round(m_full))
    if m == 60:
        d += 1
        m = 0
    return f"{d:02d}°{m:02d}'"


@dataclass
class Subject:
    name: str
    local_dt: datetime          # naive local
    tz_offset_hours: float      # historical offset, e.g. 7.5 for MY pre-1982
    lat: float
    lon: float
    notes: str = ""


def utc_from_local(local_dt: datetime, tz_offset_hours: float) -> datetime:
    return (local_dt - timedelta(hours=tz_offset_hours)).replace(tzinfo=timezone.utc)


def jd_ut(dt_utc: datetime) -> float:
    h = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h, swe.GREG_CAL)


PLANETS = [
    ("Sun",     swe.SUN),
    ("Moon",    swe.MOON),
    ("Mercury", swe.MERCURY),
    ("Venus",   swe.VENUS),
    ("Mars",    swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn",  swe.SATURN),
    ("Uranus",  swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto",   swe.PLUTO),
    ("North_Node", swe.TRUE_NODE),
    ("Chiron",  swe.CHIRON),
    ("Lilith",  swe.MEAN_APOG),  # Black Moon Lilith (mean)
]


def compute_chart(s: Subject) -> Dict[str, Any]:
    utc = utc_from_local(s.local_dt, s.tz_offset_hours)
    jd = jd_ut(utc)

    # Topocentric setup
    swe.set_topo(s.lon, s.lat, 0.0)
    flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_TOPOCTR

    results: Dict[str, Any] = {
        "subject": s.name,
        "local_dt": s.local_dt.isoformat(),
        "tz_offset_hours": s.tz_offset_hours,
        "utc": utc.isoformat(),
        "jd_ut": jd,
        "lat": s.lat,
        "lon": s.lon,
        "bodies": {},
        "asc_mc": {},
        "notes": s.notes,
    }

    for name, pid in PLANETS:
        xx, retflag = swe.calc_ut(jd, pid, flag)
        trop = xx[0] % 360.0
        speed = xx[3]  # longitude speed
        sidereal = (trop - SVP_DEG) % 360.0
        sign, deg_in = to_sign(sidereal)
        retro = speed < 0.0
        results["bodies"][name] = {
            "tropical": trop,
            "sidereal_zodiacal": sidereal,
            "sign": sign,
            "deg_in_sign": deg_in,
            "deg_in_sign_fmt": deg_min(deg_in),
            "retrograde": retro,
            "speed": speed,
        }

    # Earth = Sun + 180
    sun_trop = results["bodies"]["Sun"]["tropical"]
    earth_trop = (sun_trop + 180.0) % 360.0
    earth_sid = (earth_trop - SVP_DEG) % 360.0
    e_sign, e_deg = to_sign(earth_sid)
    results["bodies"]["Earth"] = {
        "tropical": earth_trop,
        "sidereal_zodiacal": earth_sid,
        "sign": e_sign,
        "deg_in_sign": e_deg,
        "deg_in_sign_fmt": deg_min(e_deg),
        "retrograde": False,
        "speed": 0.0,
    }
    # South Node = North Node + 180
    nn_trop = results["bodies"]["North_Node"]["tropical"]
    sn_trop = (nn_trop + 180.0) % 360.0
    sn_sid = (sn_trop - SVP_DEG) % 360.0
    sn_sign, sn_deg = to_sign(sn_sid)
    results["bodies"]["South_Node"] = {
        "tropical": sn_trop,
        "sidereal_zodiacal": sn_sid,
        "sign": sn_sign,
        "deg_in_sign": sn_deg,
        "deg_in_sign_fmt": deg_min(sn_deg),
        "retrograde": results["bodies"]["North_Node"]["retrograde"],
        "speed": 0.0,
    }

    # ASC / MC — use swe.houses with Placidus to read ascmc; the SVP is
    # applied outside as for planets. We do NOT use sidereal house mode.
    cusps, ascmc = swe.houses(jd, s.lat, s.lon, b'A')  # 'A' = Equal
    asc_trop = ascmc[0] % 360.0
    mc_trop  = ascmc[1] % 360.0
    asc_sid = (asc_trop - SVP_DEG) % 360.0
    mc_sid  = (mc_trop  - SVP_DEG) % 360.0
    asc_sign, asc_deg = to_sign(asc_sid)
    mc_sign,  mc_deg  = to_sign(mc_sid)
    dc_trop = (asc_trop + 180.0) % 360.0
    ic_trop = (mc_trop  + 180.0) % 360.0
    dc_sid  = (dc_trop - SVP_DEG) % 360.0
    ic_sid  = (ic_trop - SVP_DEG) % 360.0
    dc_sign, dc_deg = to_sign(dc_sid)
    ic_sign, ic_deg = to_sign(ic_sid)
    results["asc_mc"] = {
        "AC": {"tropical": asc_trop, "sidereal_zodiacal": asc_sid, "sign": asc_sign, "deg_in_sign": asc_deg, "deg_in_sign_fmt": deg_min(asc_deg)},
        "MC": {"tropical": mc_trop, "sidereal_zodiacal": mc_sid, "sign": mc_sign, "deg_in_sign": mc_deg, "deg_in_sign_fmt": deg_min(mc_deg)},
        "DC": {"tropical": dc_trop, "sidereal_zodiacal": dc_sid, "sign": dc_sign, "deg_in_sign": dc_deg, "deg_in_sign_fmt": deg_min(dc_deg)},
        "IC": {"tropical": ic_trop, "sidereal_zodiacal": ic_sid, "sign": ic_sign, "deg_in_sign": ic_deg, "deg_in_sign_fmt": deg_min(ic_deg)},
    }
    return results


# ----------------------------------------------------------------------
# Subjects from GM screenshots
# ----------------------------------------------------------------------
SUBJECTS = [
    Subject(
        name="Pete Y",
        local_dt=datetime(1968, 4, 1, 1, 25),
        tz_offset_hours=7.5,  # MY pre-1982 = +07:30
        lat=3.1073, lon=101.607002,
        notes="GM: Petaling Jaya, MY, UTC+07:30 (historic correct).",
    ),
    Subject(
        name="Mel",
        local_dt=datetime(1981, 7, 13, 7, 25),
        tz_offset_hours=7.5,  # MY pre-1982 = +07:30
        lat=2.1889, lon=102.250999,  # GM: Melaka
        notes="GM: Melaka, MY, UTC+07:30 (historic correct).",
    ),
    Subject(
        name="Jaan C",
        local_dt=datetime(1973, 12, 9, 21, 15),  # GM SCREENSHOT TIME (21:15)
        tz_offset_hours=7.5,  # MY pre-1982 = +07:30
        lat=3.1478, lon=101.695,  # KL
        notes="GM: KL, MY, UTC+07:30. NOTE: Mirror DB has 21:50; GM screenshot has 21:15.",
    ),
    Subject(
        name="Ana Gayoso",
        local_dt=datetime(1983, 5, 3, 8, 20),
        tz_offset_hours=-3.0,  # Argentina
        lat=-34.5433, lon=-58.7122,  # San Miguel approx (58°42'44\"W, 34°32'36\"S)
        notes="GM: San Miguel, AR, UTC-03:00. GM uses Sharatan-2°16'-Aries anchor (≈ SVP 31.28°).",
    ),
]


def print_report(results: List[Dict[str, Any]]) -> None:
    for r in results:
        print("=" * 80)
        print(f"SUBJECT: {r['subject']}")
        print(f"  local: {r['local_dt']}   tz_offset_h: {r['tz_offset_hours']}")
        print(f"  UTC:   {r['utc']}        JD_UT: {r['jd_ut']:.6f}")
        print(f"  lat: {r['lat']}    lon: {r['lon']}")
        print(f"  notes: {r['notes']}")
        print("-" * 80)
        print(f"  {'Body':<14} {'Trop°':>10}  {'Sid_zod°':>10}  {'Sign':<13} {'deg_in_sign':>14}  {'R':>2}")
        order = ["Sun","Earth","Moon","North_Node","South_Node","Mercury","Venus","Mars",
                 "Jupiter","Saturn","Uranus","Neptune","Pluto","Chiron","Lilith"]
        for b in order:
            v = r["bodies"][b]
            print(f"  {b:<14} {v['tropical']:>10.4f}  {v['sidereal_zodiacal']:>10.4f}  {v['sign']:<13} {v['deg_in_sign_fmt']:>14}  {'R' if v['retrograde'] else ''}")
        for ap in ("AC", "MC", "DC", "IC"):
            v = r["asc_mc"][ap]
            print(f"  {ap:<14} {v['tropical']:>10.4f}  {v['sidereal_zodiacal']:>10.4f}  {v['sign']:<13} {v['deg_in_sign_fmt']:>14}")
        print()


if __name__ == "__main__":
    results = [compute_chart(s) for s in SUBJECTS]
    print_report(results)
