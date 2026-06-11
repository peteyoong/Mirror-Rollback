"""
Phase 1.8 — Historical User Impact Simulation (READ-ONLY).

Scans every user in the live preview DB and projects what *would* happen if
their timezone were corrected to the IANA name implied by their stored
coordinates. NO writes, NO recomputes, NO migrations, NO cache invalidation.

Classification:
  SAFE                  stored tz already equivalent to resolved IANA tz
                        (same string OR same UTC offset at the historical
                         birth moment within ±1 minute)
  FORMAT_ONLY           stored tz string differs but resolved IANA name
                        evaluates to the same UTC moment (within ±1 minute)
  RECOMPUTE_REQUIRED    corrected tz changes the UTC moment by > 1 minute
  UNKNOWN               coords missing, timezone missing, birth time/date
                        missing, or resolver could not produce an IANA name

For every RECOMPUTE_REQUIRED user the script computes the projected
Ascendant and Midheaven deltas with swisseph (same engine the chart
calculator uses) — purely in memory.

Usage:
    cd /app/backend && python3 -m tools.phase18_impact_simulation
"""
from __future__ import annotations

import os
import sys
import math
import asyncio
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional, Tuple

# Allow `python3 tools/phase18_impact_simulation.py` from /app/backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
import swisseph as swe
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone, is_iana_name


load_dotenv()
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "test_database")

UTC_DELTA_TOLERANCE_MIN = 1  # treat ≤1 min delta as 'no UTC shift'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_birth_dt(birth_date: Any, birth_time: Optional[str]) -> Optional[datetime]:
    """Return a naive local datetime parsed from stored fields, or None."""
    if not birth_date:
        return None
    # birth_date may be a datetime or "YYYY-MM-DD"
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        try:
            d = datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None

    if not birth_time:
        # No time = we cannot construct a precise UTC moment; treat as unknown.
        return None
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt
    is_am = "am" in bt
    bt_clean = bt.replace("am", "").replace("pm", "").strip()
    parts = bt_clean.split(":")
    try:
        hh = int(parts[0])
        mm = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return None
    if is_pm and hh < 12:
        hh += 12
    if is_am and hh == 12:
        hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None
    return datetime(d.year, d.month, d.day, hh, mm)


def _stored_tz_to_utc(local_dt: datetime, stored_tz: str) -> Optional[datetime]:
    """Translate local birth dt to UTC using the *stored* tz value.
    Returns None on failure."""
    s = stored_tz.strip()
    try:
        if s.startswith(("+", "-")):
            sign = 1 if s[0] == "+" else -1
            hm = s[1:].split(":")
            hh = int(hm[0]); mm = int(hm[1]) if len(hm) > 1 else 0
            offset_min = sign * (hh * 60 + mm)
            return (local_dt - timedelta(minutes=offset_min)).replace(tzinfo=dt_tz.utc)
        if s in ("UTC", "GMT", "Z"):
            return local_dt.replace(tzinfo=dt_tz.utc)
        # IANA
        tz = pytz.timezone(s)
        return tz.localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
    except Exception:
        return None


def _iana_to_utc(local_dt: datetime, iana: str) -> Optional[datetime]:
    try:
        tz = pytz.timezone(iana)
        return tz.localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
    except Exception:
        try:
            tz = pytz.timezone(iana)
            return tz.localize(local_dt, is_dst=True).astimezone(dt_tz.utc)
        except Exception:
            return None


def _swe_julday(utc_dt: datetime) -> float:
    return swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )


def _asc_mc(utc_dt: datetime, lat: float, lon: float) -> Optional[Tuple[float, float]]:
    """Tropical Asc, MC (degrees, 0..360). Read-only; uses swisseph in memory."""
    try:
        jd = _swe_julday(utc_dt)
        # 'P' = Placidus. House system choice doesn't matter for Asc/MC —
        # they are derived from sidereal time only.
        cusps, ascmc = swe.houses(jd, lat, lon, b"P")
        return float(ascmc[0]) % 360.0, float(ascmc[1]) % 360.0
    except Exception:
        return None


def _ang_delta(a: float, b: float) -> float:
    """Smallest absolute angular difference in degrees (0..180)."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _equiv(stored_iso: Optional[datetime], corrected_iso: Optional[datetime]) -> bool:
    if not stored_iso or not corrected_iso:
        return False
    return abs((stored_iso - corrected_iso).total_seconds()) / 60.0 <= UTC_DELTA_TOLERANCE_MIN


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

async def main():
    cli = AsyncIOMotorClient(MONGO_URL)
    db = cli[DB_NAME]

    safe: List[Dict[str, Any]] = []
    format_only: List[Dict[str, Any]] = []
    recompute_required: List[Dict[str, Any]] = []
    unknown: List[Dict[str, Any]] = []

    anag_record: Optional[Dict[str, Any]] = None

    total = 0
    cursor = db.users.find({})
    async for u in cursor:
        total += 1
        uid = str(u.get("_id"))
        name = u.get("name") or "(no name)"
        email = u.get("email")
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude") or u.get("latitude")
        lon = bl.get("longitude") or u.get("longitude")
        stored_tz = u.get("timezone")
        birth_date = u.get("birth_date")
        birth_time = u.get("birth_time")

        local_dt = _parse_birth_dt(birth_date, birth_time)

        # Identify AnaG: stored tz is a fixed +08:00 offset while coords sit in Argentina.
        if not anag_record:
            try:
                if (lat is not None and float(lat) < -20 and float(lon) < -50
                    and stored_tz and str(stored_tz).startswith("+")):
                    anag_record = dict(u)
                elif name and "ana" in str(name).lower().replace(" ", "")[:8]:
                    anag_record = dict(u)
            except Exception:
                pass

        row = {
            "user_id": uid,
            "name": name,
            "email": email,
            "stored_tz": stored_tz,
            "lat": lat,
            "lon": lon,
            "city": bl.get("city"),
            "country": bl.get("country"),
            "birth_date": str(birth_date)[:10] if birth_date else None,
            "birth_time": birth_time,
        }

        if lat is None or lon is None:
            row["reason"] = "no_coords"
            unknown.append(row); continue
        if not stored_tz:
            row["reason"] = "no_stored_tz"
            unknown.append(row); continue
        if not local_dt:
            row["reason"] = "no_local_dt"
            unknown.append(row); continue

        try:
            iana = resolve_iana_timezone(float(lat), float(lon))
        except Exception:
            iana = None
        if not iana:
            row["reason"] = "resolver_failed"
            unknown.append(row); continue
        row["resolved_iana"] = iana

        stored_utc = _stored_tz_to_utc(local_dt, str(stored_tz))
        corrected_utc = _iana_to_utc(local_dt, iana)
        if not stored_utc or not corrected_utc:
            row["reason"] = "utc_conversion_failed"
            unknown.append(row); continue

        delta_min = (corrected_utc - stored_utc).total_seconds() / 60.0
        row["stored_utc"] = stored_utc.isoformat()
        row["corrected_utc"] = corrected_utc.isoformat()
        row["utc_delta_min"] = round(delta_min, 2)

        # Classify
        if str(stored_tz) == iana and abs(delta_min) <= UTC_DELTA_TOLERANCE_MIN:
            safe.append(row); continue
        if abs(delta_min) <= UTC_DELTA_TOLERANCE_MIN:
            # Different string but same UTC moment (e.g. +08:00 ↔ Asia/Kuala_Lumpur post-1982)
            format_only.append(row); continue

        # RECOMPUTE — compute projected Asc/MC deltas
        try:
            lat_f = float(lat); lon_f = float(lon)
        except Exception:
            row["reason"] = "lat_lon_not_float"
            unknown.append(row); continue

        before = _asc_mc(stored_utc, lat_f, lon_f)
        after = _asc_mc(corrected_utc, lat_f, lon_f)
        if not before or not after:
            row["reason"] = "swe_houses_failed"
            unknown.append(row); continue

        asc_b, mc_b = before
        asc_a, mc_a = after
        row.update({
            "asc_before": round(asc_b, 4),
            "asc_after":  round(asc_a, 4),
            "asc_delta_deg": round(_ang_delta(asc_b, asc_a), 4),
            "mc_before":  round(mc_b, 4),
            "mc_after":   round(mc_a, 4),
            "mc_delta_deg": round(_ang_delta(mc_b, mc_a), 4),
        })
        recompute_required.append(row)

    # -----------------------------------------------------------------------
    # Try to locate AnaG by name if not already found
    # -----------------------------------------------------------------------
    if not anag_record:
        async for u in db.users.find({"name": {"$regex": "ana", "$options": "i"}}):
            if (u.get("birth_location") or {}).get("country", "").lower() in (
                "argentina", "uruguay", "chile", "brazil"
            ):
                anag_record = u; break

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    print("=" * 78)
    print("Phase 1.8 — Historical User Impact Simulation (READ-ONLY)")
    print("=" * 78)
    print(f"Total users scanned: {total}\n")

    print(f"  SAFE                : {len(safe):4d}")
    print(f"  FORMAT_ONLY         : {len(format_only):4d}")
    print(f"  RECOMPUTE_REQUIRED  : {len(recompute_required):4d}")
    print(f"  UNKNOWN             : {len(unknown):4d}")
    print(f"  ---  sum = {len(safe)+len(format_only)+len(recompute_required)+len(unknown)}")
    print()

    # UNKNOWN breakdown by reason
    reasons: Dict[str, int] = {}
    for r in unknown:
        reasons[r.get("reason", "?")] = reasons.get(r.get("reason", "?"), 0) + 1
    print("UNKNOWN breakdown by reason:")
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"   {k:30s} {v}")
    print()

    def _print_table(title: str, rows: List[Dict[str, Any]], key: str, top_n: int = 20):
        rows_sorted = sorted(rows, key=lambda r: abs(r.get(key, 0)), reverse=True)[:top_n]
        print("-" * 78)
        print(title)
        print("-" * 78)
        print(f"{'#':>2}  {'user_id':24s} {'name':18s} {'stored→resolved':40s} {'metric':>14s}")
        for i, r in enumerate(rows_sorted, 1):
            transition = f"{str(r.get('stored_tz'))[:15]:<15} → {r.get('resolved_iana','')[:22]:<22}"
            v = r.get(key)
            v_str = f"{v:+.2f}" if isinstance(v, (int, float)) else str(v)
            print(f"{i:2d}  {r['user_id']:24s} {str(r['name'])[:18]:18s} {transition:40s} {v_str:>14s}")
        print()

    if recompute_required:
        _print_table("TOP 20 — largest |UTC delta| (minutes)",        recompute_required, "utc_delta_min")
        _print_table("TOP 20 — largest |Ascendant delta| (degrees)",  recompute_required, "asc_delta_deg")
        _print_table("TOP 20 — largest |MC delta| (degrees)",         recompute_required, "mc_delta_deg")

    # -----------------------------------------------------------------------
    # AnaG section
    # -----------------------------------------------------------------------
    print("=" * 78)
    print("AnaG — special section")
    print("=" * 78)
    if not anag_record:
        print("  No AnaG-like record located (no Argentine coords with fixed offset, ")
        print("  and no name containing 'ana' with a South-American country).")
    else:
        u = anag_record
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude") or u.get("latitude")
        lon = bl.get("longitude") or u.get("longitude")
        local_dt = _parse_birth_dt(u.get("birth_date"), u.get("birth_time"))
        stored_tz = u.get("timezone")
        print(f"  user_id          : {u.get('_id')}")
        print(f"  name             : {u.get('name')}")
        print(f"  email            : {u.get('email')}")
        print(f"  city/country     : {bl.get('city')}, {bl.get('country')}")
        print(f"  coords           : lat={lat}, lon={lon}")
        print(f"  birth_date/time  : {str(u.get('birth_date'))[:10]} {u.get('birth_time')}")
        print(f"  stored_timezone  : {stored_tz!r}")
        try:
            iana = resolve_iana_timezone(float(lat), float(lon))
        except Exception:
            iana = None
        print(f"  resolved_iana    : {iana!r}")
        if local_dt and stored_tz and iana:
            s_utc = _stored_tz_to_utc(local_dt, str(stored_tz))
            c_utc = _iana_to_utc(local_dt, iana)
            if s_utc and c_utc:
                d_min = (c_utc - s_utc).total_seconds() / 60.0
                print(f"  stored_utc       : {s_utc.isoformat()}")
                print(f"  corrected_utc    : {c_utc.isoformat()}")
                print(f"  utc_delta_min    : {d_min:+.2f}")
                if lat is not None and lon is not None:
                    b = _asc_mc(s_utc, float(lat), float(lon))
                    a = _asc_mc(c_utc, float(lat), float(lon))
                    if b and a:
                        print(f"  asc  {b[0]:8.3f}° → {a[0]:8.3f}°   Δ={_ang_delta(*((b[0],a[0]))):.3f}°")
                        print(f"  mc   {b[1]:8.3f}° → {a[1]:8.3f}°   Δ={_ang_delta(*((b[1],a[1]))):.3f}°")
    print()

    # -----------------------------------------------------------------------
    # Final answer
    # -----------------------------------------------------------------------
    print("=" * 78)
    print("FINAL ANSWER")
    print("=" * 78)
    print(f"If Phase 2 were executed today, the number of users who would")
    print(f"receive a MATERIALLY different chart (UTC shifts > {UTC_DELTA_TOLERANCE_MIN} minute)")
    print(f"is: {len(recompute_required)}")
    print()
    print("NOTE: This script performed NO writes. No charts were updated. No users")
    print("were modified. No migrations were triggered.")


if __name__ == "__main__":
    asyncio.run(main())
