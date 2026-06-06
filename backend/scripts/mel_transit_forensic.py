"""Forensic calibration — Mirror vs Athen True Sidereal Yearly Transit Report.

Loads Mel's chart from Mongo, computes the exact transit pass date for every
benchmark event listed in Athen's Yearly Transit Report, and produces a
side-by-side table.

Read-only. Does NOT modify any chart calculation code.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, "/app/backend")
load_dotenv("/app/backend/.env")

from services.lifecycle_engine import SE_BODIES, _scan_transit_passes, _jd_to_iso

# ---------------------------------------------------------------------------
# Athen benchmark events (extracted from the PDF Event Calendar)
# ---------------------------------------------------------------------------
# Format: (athen_date_iso, transit_body, aspect_offset_deg, natal_body, house, label)
ATHEN_EVENTS: List[Tuple[str, str, float, str, int, str]] = [
    # March 2026
    ("2026-03-20", "Saturn",     180.0, "Jupiter", 9,  "Saturn opp Jupiter"),
    ("2026-03-26", "Saturn",       0.0, "Saturn",  9,  "Saturn return (Saturn opp itself? no, conj=return)"),
    # ↑ "Saturn opposition natal Saturn" in Athen typically means Saturn opposite its own natal position
    # but for a Saturn-Saturn it could be the 14.5yr opposition. We test both.
    # April
    ("2026-04-11", "Jupiter",     30.0, "Venus",   12, "Jupiter semisextile Venus"),
    # May
    ("2026-05-02", "Neptune",    120.0, "Moon",     9, "Neptune trine Moon (1)"),
    ("2026-05-09", "Uranus",      30.0, "Mercury", 10, "Uranus semisextile Mercury"),
    ("2026-05-15", "Jupiter",      0.0, "Sun",     12, "Jupiter conjunction Sun"),
    # June
    ("2026-06-01", "Neptune",    180.0, "Jupiter",  9, "Neptune opposition Jupiter (1)"),
    ("2026-06-16", "Jupiter",     30.0, "Mars",    12, "Jupiter semisextile Mars (1)"),
    ("2026-06-23", "Uranus",     180.0, "Moon",    11, "★ URANUS OPP MOON (1)"),
    # July
    ("2026-07-03", "Jupiter",     30.0, "Mercury", 12, "Jupiter semisextile Mercury"),
    ("2026-07-04", "Pluto",      120.0, "Saturn",   7, "Pluto trine Saturn (1)"),
    ("2026-07-08", "Uranus",     120.0, "Jupiter", 11, "Uranus trine Jupiter (1)"),
    ("2026-07-15", "Jupiter",    120.0, "Moon",     1, "Jupiter trine Moon"),
    ("2026-07-19", "Jupiter",     60.0, "Jupiter",  1, "Jupiter sextile Jupiter"),
    ("2026-07-22", "Jupiter",     60.0, "Saturn",   1, "Jupiter sextile Saturn"),
    ("2026-07-26", "Uranus",     120.0, "Saturn",  11, "Uranus trine Saturn (1)"),
    # August
    ("2026-08-05", "Pluto",      120.0, "Jupiter",  7, "Pluto trine Jupiter (1)"),
    ("2026-08-13", "Neptune",    180.0, "Jupiter",  9, "Neptune opposition Jupiter (2)"),
    # September
    ("2026-09-14", "Pluto",       60.0, "Moon",     7, "Pluto sextile Moon (1)"),
    ("2026-09-15", "Neptune",    120.0, "Moon",     9, "Neptune trine Moon (2)"),
    ("2026-09-15", "Jupiter",      0.0, "Venus",    1, "Jupiter conj Venus"),
    # October
    ("2026-10-10", "Jupiter",     30.0, "Sun",      1, "Jupiter semisextile Sun (1)"),
    ("2026-10-28", "Uranus",     120.0, "Saturn",  11, "Uranus trine Saturn (2)"),
    # November
    ("2026-11-16", "Uranus",     120.0, "Jupiter", 11, "Uranus trine Jupiter (2)"),
    ("2026-11-17", "Pluto",       60.0, "Moon",     7, "Pluto sextile Moon (2)"),
    # December
    ("2026-12-05", "Uranus",     180.0, "Moon",    11, "★ URANUS OPP MOON (2)"),
    ("2026-12-08", "Jupiter",     60.0, "Mars",     1, "Jupiter sextile Mars (1)"),
    ("2026-12-22", "Pluto",      120.0, "Jupiter",  7, "Pluto trine Jupiter (2)"),
    # January 2027
    ("2027-01-16", "Pluto",      120.0, "Saturn",   7, "Pluto trine Saturn (2)"),
    # February
    ("2027-02-18", "Jupiter",     30.0, "Sun",      1, "Jupiter semisextile Sun (2)"),
]


async def load_mel_chart():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ.get("DB_NAME", "test_database")]
    u = await db.users.find_one({"email": "melissa.mars@gmail.com"})
    c = await db.charts.find_one({"user_id": str(u["_id"])})
    return u, c["astrology"]


def find_pass(body: str, target_long: float, offset: float, around_iso: str,
              window_days: int = 60) -> List[float]:
    """Scan ±window_days around the target date for transit zero-crossings.

    For non-conjunction / non-opposition aspects (sextile / square / trine /
    semisextile) BOTH +offset and -offset are valid hit points. We scan both.
    """
    around = datetime.fromisoformat(around_iso).replace(tzinfo=timezone.utc)
    jd_mid = swe.julday(around.year, around.month, around.day, 0.0)
    hits = _scan_transit_passes(
        body=body, target_long=target_long, offset_deg=offset,
        jd_start=jd_mid - window_days, jd_end=jd_mid + window_days,
        step_days=2.0,
    )
    if abs(offset) > 1e-6 and abs(abs(offset) - 180.0) > 1e-6:
        hits.extend(_scan_transit_passes(
            body=body, target_long=target_long, offset_deg=-offset,
            jd_start=jd_mid - window_days, jd_end=jd_mid + window_days,
            step_days=2.0,
        ))
    return sorted(hits)


def main():
    u, chart = asyncio.get_event_loop().run_until_complete(load_mel_chart())
    md = chart.get("metadata") or {}
    print(f"# Mirror engine settings")
    print(f"  zodiac:        {md.get('sidereal_mode')}  (svp={md.get('svp_degrees')})")
    print(f"  house_system:  {md.get('house_system')}")
    print(f"  ayanamsa:      user-defined (Sharatan / β Arietis)")
    print(f"  ephemeris:     Swiss Ephemeris")
    print(f"  birth UTC:     {md.get('input_datetime_utc')}")
    print(f"  birth coords:  {md.get('coordinates')}")
    print(f"  engine ver:    astrology-{md.get('engine_marker','?')}")
    print()

    planets = chart.get("planets") or {}
    angles = chart.get("angles") or {}
    natal_trop: Dict[str, float] = {}
    for name, p in planets.items():
        if "tropical_longitude" in p:
            natal_trop[name] = p["tropical_longitude"]
    for ang_key, src in (("Ascendant", "asc"), ("Midheaven", "mc")):
        a = angles.get(src) or {}
        if "tropical_longitude" in a:
            natal_trop[ang_key] = a["tropical_longitude"]

    print("# Mel natal tropical longitudes (used as transit targets):")
    for k in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
              "Saturn", "Uranus", "Neptune", "Pluto", "North Node",
              "Chiron", "Ascendant", "Midheaven"):
        if k in natal_trop:
            print(f"  {k:14}: {natal_trop[k]:8.4f}°")
    print()

    print("# Forensic table — Athen vs Mirror exact pass dates")
    print()
    print(f"{'#':>2}  {'label':38}  {'Athen':10}  {'Mirror':10}  Δ days  status")
    print("-" * 100)
    summary = {"match": 0, "off_by_lt_3": 0, "off_by_3_7": 0, "off_by_gt_7": 0, "no_pass": 0}
    rows = []
    for i, (athen_date, body, off, natal_b, house, label) in enumerate(ATHEN_EVENTS, 1):
        nat = natal_trop.get(natal_b)
        if nat is None:
            print(f"{i:2}  {label:38}  {athen_date}   (no natal long for {natal_b!r})")
            continue
        passes = find_pass(body, nat, off, athen_date, window_days=60)
        if not passes:
            # Try wider window
            passes = find_pass(body, nat, off, athen_date, window_days=120)
        if not passes:
            summary["no_pass"] += 1
            print(f"{i:2}  {label:38}  {athen_date}   ---         no pass found  E:no_match")
            rows.append((athen_date, label, None, None, "no_pass"))
            continue
        # Find pass closest to athen date
        target_jd = swe.julday(*[int(x) for x in athen_date.split("-")], 0.0)
        nearest = min(passes, key=lambda j: abs(j - target_jd))
        delta_d = nearest - target_jd
        mirror_iso = _jd_to_iso(nearest)[:10]
        if abs(delta_d) <= 1:
            status = "MATCH"
            summary["match"] += 1
        elif abs(delta_d) <= 3:
            status = "near"
            summary["off_by_lt_3"] += 1
        elif abs(delta_d) <= 7:
            status = "drift"
            summary["off_by_3_7"] += 1
        else:
            status = "DIVERGE"
            summary["off_by_gt_7"] += 1
        print(f"{i:2}  {label:38}  {athen_date}  {mirror_iso}  {delta_d:+6.1f}  {status}")
        rows.append((athen_date, label, mirror_iso, delta_d, status))

    print()
    print("# Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return rows


if __name__ == "__main__":
    main()
