"""
Phase 1.9 — Chart/Input Consistency Audit (READ-ONLY).

For each sampled user we re-derive UTC from their *stored* (timezone, birth_date,
birth_time), call calculations.astrology.get_full_natal_chart() entirely in
memory, and compare the recomputed Asc/MC against the chart already persisted.

This tells us whether the stored chart actually corresponds to the stored
inputs (MATCH) or to some other set of inputs from a prior generation
(MISMATCH). Combined with Phase 1.8, this lets us validate whether the 119
RECOMPUTE_REQUIRED estimate is the true Phase 2 population.

NO writes. NO migrations. NO chart updates. NO cache touches.
"""
from __future__ import annotations

import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone
from calculations.astrology import get_full_natal_chart

load_dotenv()
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "test_database")

MATCH_TOLERANCE_DEG = 0.5  # degrees of allowed drift between stored and recomputed


# Top-20 from Phase 1.8 -- keyed on the live preview DB
TOP20_UTC = [
    "697fa0652caf672a29468f05","697f9c8a2caf672a29468ef5","697fa4d31ea0ea87a2f58c7d",
    "697fa8549468f7a9126c13b0","697f988a2caf672a29468ed9","697f98ad2caf672a29468edb",
    "697f9e5c2caf672a29468efb","697fa0be2caf672a29468f07","697fa4951ea0ea87a2f58c7b",
    "697fa8149468f7a9126c13ae","697f751b1a7a96aa35e283a1","697f795f1a7a96aa35e283a3",
    "697f98f52caf672a29468edf","697f9b592caf672a29468ee9","697f224b366f6814412d8c84",
    "698063576fce97a58f50ba49","697f9bc22caf672a29468eef","697f9c5e2caf672a29468ef3",
    "69ace84118ee2b46fbc50c20","697f995c2caf672a29468ee3",
]
TOP20_ASC = [
    "697fa0652caf672a29468f05","697f795f1a7a96aa35e283a3","697f9c8a2caf672a29468ef5",
    "697f751b1a7a96aa35e283a1","697fa4951ea0ea87a2f58c7b","697f9b592caf672a29468ee9",
    "697fa8549468f7a9126c13b0","697f988a2caf672a29468ed9","697fa4d31ea0ea87a2f58c7d",
    "697fa0be2caf672a29468f07","697f98f52caf672a29468edf","697f98ad2caf672a29468edb",
    "697f224b366f6814412d8c84","698063576fce97a58f50ba49","697fa8149468f7a9126c13ae",
    "697f9e5c2caf672a29468efb","69804ccaff8ae1f4644f6d12","69804d30ff8ae1f4644f6d13",
    "697f995c2caf672a29468ee3","697f9c5e2caf672a29468ef3",
]


def _parse_local_dt(birth_date: Any, birth_time: Any) -> Optional[datetime]:
    if not birth_date:
        return None
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        try:
            d = datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None
    if not birth_time:
        return None
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt; is_am = "am" in bt
    t = bt.replace("am", "").replace("pm", "").strip().split(":")
    try:
        hh = int(t[0]); mm = int(t[1]) if len(t) > 1 else 0
    except (ValueError, IndexError):
        return None
    if is_pm and hh < 12: hh += 12
    if is_am and hh == 12: hh = 0
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc(local_dt: datetime, tz_str: str) -> Optional[datetime]:
    s = tz_str.strip()
    try:
        if s.startswith(("+", "-")):
            sign = 1 if s[0] == "+" else -1
            hm = s[1:].split(":")
            hh = int(hm[0]); mm = int(hm[1]) if len(hm) > 1 else 0
            off = sign * (hh * 60 + mm)
            return (local_dt - timedelta(minutes=off)).replace(tzinfo=dt_tz.utc)
        if s in ("UTC", "GMT", "Z"):
            return local_dt.replace(tzinfo=dt_tz.utc)
        tz = pytz.timezone(s)
        return tz.localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
    except Exception:
        try:
            tz = pytz.timezone(s)
            return tz.localize(local_dt, is_dst=True).astimezone(dt_tz.utc)
        except Exception:
            return None


def _ang_delta(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _recompute_asc_mc(local_dt: datetime, tz_str: str, lat: float, lon: float) -> Optional[Tuple[float, float]]:
    utc = _to_utc(local_dt, tz_str)
    if not utc:
        return None
    try:
        chart = get_full_natal_chart(utc, float(lat), float(lon))
        ang = (chart or {}).get("angles") or {}
        asc_l = (ang.get("asc") or {}).get("longitude") or (ang.get("asc") or {}).get("tropical_longitude")
        mc_l = (ang.get("mc") or {}).get("longitude") or (ang.get("mc") or {}).get("tropical_longitude")
        if asc_l is None or mc_l is None:
            return None
        return float(asc_l) % 360.0, float(mc_l) % 360.0
    except Exception:
        return None


def _stored_asc_mc(chart: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    a = (chart or {}).get("astrology") or {}
    ang = a.get("angles") or {}
    asc_l = (ang.get("asc") or {}).get("longitude") or (ang.get("asc") or {}).get("tropical_longitude")
    mc_l = (ang.get("mc") or {}).get("longitude") or (ang.get("mc") or {}).get("tropical_longitude")
    if asc_l is None or mc_l is None:
        return None
    return float(asc_l) % 360.0, float(mc_l) % 360.0


async def _audit_user(db, uid: str) -> Dict[str, Any]:
    try:
        u = await db.users.find_one({"_id": ObjectId(uid)})
    except Exception:
        u = None
    if not u:
        return {"user_id": uid, "status": "UNKNOWN", "reason": "user_not_found"}

    chart = await db.charts.find_one({"user_id": uid})
    name = u.get("name") or "(no name)"
    bl = u.get("birth_location") or {}
    lat = bl.get("latitude") or u.get("latitude")
    lon = bl.get("longitude") or u.get("longitude")
    stored_tz = u.get("timezone")
    birth_date = u.get("birth_date")
    birth_time = u.get("birth_time")

    row: Dict[str, Any] = {
        "user_id":         uid,
        "name":            name,
        "email":           u.get("email"),
        "stored_tz":       stored_tz,
        "timezone_minutes": u.get("timezone_minutes"),
        "lat":             lat,
        "lon":             lon,
        "city":            bl.get("city"),
        "country":         bl.get("country"),
        "birth_date":      str(birth_date)[:10] if birth_date else None,
        "birth_time":      birth_time,
    }

    if not chart:
        row.update({"status": "UNKNOWN", "reason": "no_stored_chart"})
        return row

    a = (chart.get("astrology") or {})
    md = a.get("metadata") or {}
    row["chart_metadata_input_utc"] = md.get("input_datetime_utc")
    row["astrology_engine_version"] = md.get("astrology_engine_version")
    row["computation_version"]      = md.get("computation_version")
    row["debug_stamp"]              = chart.get("debug_stamp")
    row["forensic_variant_b"]       = bool(chart.get("forensic_variant_b"))
    row["chart_coords"]             = md.get("coordinates")

    stored = _stored_asc_mc(chart)
    if not stored:
        row.update({"status": "UNKNOWN", "reason": "no_stored_asc_mc"})
        return row
    row["stored_asc"] = round(stored[0], 4)
    row["stored_mc"]  = round(stored[1], 4)

    if not (lat is not None and lon is not None and stored_tz and birth_date and birth_time):
        row.update({"status": "UNKNOWN", "reason": "missing_user_inputs"})
        return row

    local_dt = _parse_local_dt(birth_date, birth_time)
    if not local_dt:
        row.update({"status": "UNKNOWN", "reason": "bad_birth_time"})
        return row

    recomp = _recompute_asc_mc(local_dt, str(stored_tz), float(lat), float(lon))
    if not recomp:
        row.update({"status": "UNKNOWN", "reason": "recompute_failed"})
        return row
    row["recomp_asc"] = round(recomp[0], 4)
    row["recomp_mc"]  = round(recomp[1], 4)
    row["asc_delta_deg"] = round(_ang_delta(stored[0], recomp[0]), 4)
    row["mc_delta_deg"]  = round(_ang_delta(stored[1], recomp[1]), 4)

    row["status"] = (
        "MATCH"
        if (row["asc_delta_deg"] <= MATCH_TOLERANCE_DEG
            and row["mc_delta_deg"] <= MATCH_TOLERANCE_DEG)
        else "MISMATCH"
    )
    return row


async def _pete_special(db) -> Dict[str, Any]:
    uid = "697f224b366f6814412d8c84"
    u = await db.users.find_one({"_id": ObjectId(uid)})
    if not u:
        return {"error": "pete_not_found"}
    chart = await db.charts.find_one({"user_id": uid})
    bl = u.get("birth_location") or {}
    lat = bl.get("latitude") or u.get("latitude")
    lon = bl.get("longitude") or u.get("longitude")
    local_dt = _parse_local_dt(u.get("birth_date"), u.get("birth_time"))
    stored = _stored_asc_mc(chart) if chart else None
    a = (chart.get("astrology") or {}) if chart else {}
    md = a.get("metadata") or {}

    out: Dict[str, Any] = {
        "user_id": uid,
        "name": u.get("name"),
        "email": u.get("email"),
        "stored_timezone": u.get("timezone"),
        "stored_timezone_minutes": u.get("timezone_minutes"),
        "birth_date": str(u.get("birth_date"))[:10] if u.get("birth_date") else None,
        "birth_time": u.get("birth_time"),
        "lat": lat, "lon": lon,
        "stored_input_utc_metadata": md.get("input_datetime_utc"),
        "astrology_engine_version": md.get("astrology_engine_version"),
        "computation_version": md.get("computation_version"),
        "debug_stamp": chart.get("debug_stamp") if chart else None,
        "forensic_variant_b_present": bool(chart and chart.get("forensic_variant_b")),
        "stored_asc": round(stored[0], 4) if stored else None,
        "stored_mc":  round(stored[1], 4) if stored else None,
    }

    candidate_tzs = [
        u.get("timezone"),
        "Asia/Kuala_Lumpur",
        "+08:00",
        "+07:30",
        "UTC",
    ]
    tried = []
    if local_dt:
        for tz in [t for t in candidate_tzs if t]:
            recomp = _recompute_asc_mc(local_dt, str(tz), float(lat), float(lon))
            if not recomp:
                tried.append({"tz": tz, "error": "recompute_failed"}); continue
            d_asc = _ang_delta(stored[0], recomp[0]) if stored else None
            d_mc  = _ang_delta(stored[1], recomp[1]) if stored else None
            tried.append({
                "tz": tz,
                "recomp_asc": round(recomp[0], 4),
                "recomp_mc":  round(recomp[1], 4),
                "asc_delta_deg": round(d_asc, 4) if d_asc is not None else None,
                "mc_delta_deg":  round(d_mc,  4) if d_mc  is not None else None,
                "matches_stored": (d_asc is not None and d_mc is not None
                                    and d_asc <= MATCH_TOLERANCE_DEG
                                    and d_mc <= MATCH_TOLERANCE_DEG),
            })
    out["candidates"] = tried
    return out


async def main():
    cli = AsyncIOMotorClient(MONGO_URL)
    db = cli[DB_NAME]

    # Look-up Mel and Jaan by email
    async def _id_by_email(emails: List[str]) -> Optional[str]:
        for e in emails:
            u = await db.users.find_one({"email": e})
            if u:
                return str(u["_id"])
        return None

    mel_id  = await _id_by_email(["melissa.mars@gmail.com", "mel@test.com"])
    jaan_id = await _id_by_email(["jaan@test.com"]) or None
    if not jaan_id:
        u = await db.users.find_one({"name": {"$regex": "^jaan", "$options": "i"}})
        jaan_id = str(u["_id"]) if u else None

    sample_ids = []
    fixed = [("Pete", "697f224b366f6814412d8c84"),
             ("Mel",  mel_id),
             ("Jaan", jaan_id)]
    print("Fixed sample:")
    for label, uid in fixed:
        print(f"  {label:<6} -> {uid}")
        if uid: sample_ids.append(uid)
    # Add top-20 unions, dedup
    for uid in TOP20_UTC + TOP20_ASC:
        if uid not in sample_ids:
            sample_ids.append(uid)
    print(f"\nTotal unique audit sample: {len(sample_ids)}")

    results = []
    for uid in sample_ids:
        r = await _audit_user(db, uid)
        results.append(r)

    # Counts
    n_match = sum(1 for r in results if r.get("status") == "MATCH")
    n_mism  = sum(1 for r in results if r.get("status") == "MISMATCH")
    n_unk   = sum(1 for r in results if r.get("status") == "UNKNOWN")

    print("\n" + "=" * 78)
    print("Phase 1.9 — Chart/Input Consistency Audit")
    print("=" * 78)
    print(f"  MATCH    : {n_match}")
    print(f"  MISMATCH : {n_mism}")
    print(f"  UNKNOWN  : {n_unk}")
    print(f"  total    : {len(results)}")

    # Per-user table
    print()
    print(f"{'status':<9} {'user_id':<26} {'name':<20} {'tz':<22} {'asc_Δ':>7} {'mc_Δ':>7} {'engine':<28}")
    for r in results:
        engine = (r.get("astrology_engine_version") or "?")[:26]
        print(f"{r.get('status','?'):<9} {r['user_id']:<26} {str(r['name'])[:20]:<20} "
              f"{str(r.get('stored_tz'))[:22]:<22} "
              f"{r.get('asc_delta_deg','?'):>7} {r.get('mc_delta_deg','?'):>7} {engine:<28}")

    # Pete deep dive
    print("\n" + "=" * 78)
    print("Pete — special section")
    print("=" * 78)
    pete = await _pete_special(db)
    for k in ("user_id", "name", "email", "stored_timezone", "stored_timezone_minutes",
              "birth_date", "birth_time", "lat", "lon",
              "stored_input_utc_metadata", "astrology_engine_version",
              "computation_version", "forensic_variant_b_present",
              "debug_stamp", "stored_asc", "stored_mc"):
        print(f"  {k:<30}: {pete.get(k)}")
    print()
    print(f"  {'tz':<22}  {'recomp_asc':>12} {'recomp_mc':>12} {'asc_Δ':>8} {'mc_Δ':>8}  match")
    for cand in pete.get("candidates", []):
        print(f"  {str(cand.get('tz')):<22}  "
              f"{str(cand.get('recomp_asc')):>12} {str(cand.get('recomp_mc')):>12} "
              f"{str(cand.get('asc_delta_deg')):>8} {str(cand.get('mc_delta_deg')):>8}  "
              f"{cand.get('matches_stored')}")

    # Phase 1.8 validation
    print("\n" + "=" * 78)
    print("Phase 1.8 estimate validation")
    print("=" * 78)
    print(f"  Audited {len(results)} users (Pete/Mel/Jaan + top-40 RECOMPUTE_REQUIRED).")
    if n_unk == 0:
        print("  No UNKNOWNs.")
    if n_mism == 0:
        print("  Every stored chart was reproducible from its CURRENT stored inputs.")
        print("  → Phase 1.8's 119 estimate IS the true Phase 2 population.")
    else:
        print(f"  {n_mism} stored chart(s) DID NOT match their stored inputs — Phase 1.8")
        print("  may over-count or under-count. See per-row deltas.")
    print()
    print("NOTE: This script performed NO writes. No charts updated. No users modified.")


if __name__ == "__main__":
    asyncio.run(main())
