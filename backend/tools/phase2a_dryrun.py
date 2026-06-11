"""
Phase 2A — Controlled Timezone Correction Dry Run.

READ-ONLY. Validates the full Phase 2 workflow on a representative cohort
without writing anything. Generates per-user current-state, resolver output,
in-memory recompute deltas, rollback-snapshot payload (NOT persisted), risk
classification, and final GO/NO-GO recommendation.

NO writes. NO chart updates. NO cache invalidation. NO migrations.
"""
from __future__ import annotations

import os, sys, asyncio
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import (
    resolve_iana_timezone, TIMEZONE_RESOLVER_VERSION,
)
from calculations.astrology import get_full_natal_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

MATCH_TOL_DEG = 0.5
UTC_TOL_MIN = 1


def _parse_local(birth_date, birth_time):
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        d = datetime.strptime(s, "%Y-%m-%d")
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt; is_am = "am" in bt
    parts = bt.replace("am", "").replace("pm", "").strip().split(":")
    hh = int(parts[0]); mm = int(parts[1]) if len(parts) > 1 else 0
    if is_pm and hh < 12: hh += 12
    if is_am and hh == 12: hh = 0
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc(local_dt, tz_str):
    s = str(tz_str).strip()
    try:
        if s.startswith(("+", "-")):
            sign = 1 if s[0] == "+" else -1
            hm = s[1:].split(":")
            off = sign * (int(hm[0]) * 60 + (int(hm[1]) if len(hm) > 1 else 0))
            return (local_dt - timedelta(minutes=off)).replace(tzinfo=dt_tz.utc)
        if s in ("UTC", "GMT", "Z"):
            return local_dt.replace(tzinfo=dt_tz.utc)
        return pytz.timezone(s).localize(local_dt, is_dst=None).astimezone(dt_tz.utc)
    except Exception:
        try:
            return pytz.timezone(s).localize(local_dt, is_dst=True).astimezone(dt_tz.utc)
        except Exception:
            return None


def _ang_delta(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _historical_offset_str(iana, local_dt):
    try:
        aware = pytz.timezone(iana).localize(local_dt, is_dst=None)
        secs = int(aware.utcoffset().total_seconds())
        sign = "+" if secs >= 0 else "-"
        h, m = divmod(abs(secs) // 60, 60)
        return f"{sign}{h:02d}:{m:02d}"
    except Exception:
        return None


async def _pick_one(query, exclude_ids: set) -> Optional[Dict[str, Any]]:
    async for u in db.users.find(query):
        if str(u["_id"]) in exclude_ids:
            continue
        # Require usable inputs
        bl = u.get("birth_location") or {}
        if (bl.get("latitude") is not None and bl.get("longitude") is not None
                and u.get("birth_date") and u.get("birth_time")):
            return u
    return None


async def _audit_user(u: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(u["_id"])
    bl = u.get("birth_location") or {}
    lat = bl.get("latitude"); lon = bl.get("longitude")
    stored_tz = u.get("timezone")
    bdate = u.get("birth_date"); btime = u.get("birth_time")

    chart = await db.charts.find_one({"user_id": uid})
    a_meta = (chart.get("astrology") if chart else {}) or {}
    md = a_meta.get("metadata") or {}
    ang = a_meta.get("angles") or {}
    stored_asc = ((ang.get("asc") or {}).get("longitude")
                  or (ang.get("asc") or {}).get("tropical_longitude"))
    stored_mc = ((ang.get("mc") or {}).get("longitude")
                 or (ang.get("mc") or {}).get("tropical_longitude"))
    engine_version = md.get("astrology_engine_version")
    computation_version = md.get("computation_version")

    out: Dict[str, Any] = {
        "user_id": uid,
        "name": u.get("name"),
        "email": u.get("email"),
        "step1_current_state": {
            "birth_date": str(bdate)[:10] if bdate else None,
            "birth_time": btime,
            "stored_timezone": stored_tz,
            "timezone_minutes": u.get("timezone_minutes"),
            "latitude": lat, "longitude": lon,
            "city": bl.get("city"), "country": bl.get("country"),
            "current_chart_asc_longitude": stored_asc,
            "current_chart_mc_longitude": stored_mc,
            "astrology_engine_version": engine_version,
            "computation_version": computation_version,
        },
    }

    if not (lat is not None and lon is not None and bdate and btime and stored_tz):
        out["classification"] = "UNKNOWN"
        out["reason"] = "missing_required_inputs"
        return out

    local_dt = _parse_local(bdate, btime)

    # ---- Step 2 — resolver ----
    iana = resolve_iana_timezone(float(lat), float(lon))
    hist_offset = _historical_offset_str(iana, local_dt) if iana else None
    corrected_utc = _to_utc(local_dt, iana) if iana else None
    out["step2_resolver"] = {
        "resolved_iana": iana,
        "historical_offset_at_birth": hist_offset,
        "resolving_resulting_utc": corrected_utc.isoformat() if corrected_utc else None,
        "resolver_version": TIMEZONE_RESOLVER_VERSION,
    }

    # ---- Step 3 — in-memory recompute ----
    stored_utc = _to_utc(local_dt, stored_tz)
    recomp_asc = recomp_mc = None
    if corrected_utc:
        try:
            ch = get_full_natal_chart(corrected_utc, float(lat), float(lon))
            ang2 = ch.get("angles") or {}
            recomp_asc = ((ang2.get("asc") or {}).get("longitude")
                          or (ang2.get("asc") or {}).get("tropical_longitude"))
            recomp_mc = ((ang2.get("mc") or {}).get("longitude")
                         or (ang2.get("mc") or {}).get("tropical_longitude"))
        except Exception as e:
            out["recompute_error"] = str(e)
    asc_delta = _ang_delta(stored_asc, recomp_asc) if (stored_asc is not None and recomp_asc is not None) else None
    mc_delta = _ang_delta(stored_mc, recomp_mc) if (stored_mc is not None and recomp_mc is not None) else None
    utc_delta_min = ((corrected_utc - stored_utc).total_seconds() / 60.0
                     if (stored_utc and corrected_utc) else None)
    out["step3_recompute_in_memory"] = {
        "stored_utc": stored_utc.isoformat() if stored_utc else None,
        "corrected_utc": corrected_utc.isoformat() if corrected_utc else None,
        "utc_delta_min": round(utc_delta_min, 2) if utc_delta_min is not None else None,
        "corrected_asc_longitude": round(recomp_asc, 6) if recomp_asc is not None else None,
        "corrected_mc_longitude":  round(recomp_mc, 6)  if recomp_mc  is not None else None,
        "asc_delta_deg": round(asc_delta, 4) if asc_delta is not None else None,
        "mc_delta_deg":  round(mc_delta, 4)  if mc_delta  is not None else None,
    }

    # ---- Step 4 — rollback snapshot (PLAN ONLY, not persisted) ----
    out["step4_rollback_snapshot_plan"] = {
        "user_id": uid,
        "snapshot_collection_target": "users_phase2_rollback (NOT YET CREATED)",
        "rollback_snapshot": {
            "previous_timezone": stored_tz,
            "previous_timezone_minutes": u.get("timezone_minutes"),
            "previous_chart": {
                "asc_longitude": stored_asc,
                "mc_longitude": stored_mc,
                "engine_version": engine_version,
                "computation_version": computation_version,
                "debug_stamp": chart.get("debug_stamp") if chart else None,
            },
            "captured_at": "<set_at_phase2_execution_time>",
        },
        "WRITE_OPERATION_PERFORMED": False,
    }

    # ---- Step 5 — classification ----
    if utc_delta_min is None:
        out["classification"] = "UNKNOWN"; out["reason"] = "utc_conversion_failed"
    elif iana == stored_tz and abs(utc_delta_min) <= UTC_TOL_MIN:
        out["classification"] = "SAFE"
        out["reason"] = "stored_tz already matches resolved IANA name"
    elif abs(utc_delta_min) <= UTC_TOL_MIN:
        out["classification"] = "FORMAT_ONLY"
        out["reason"] = (f"stored tz {stored_tz!r} differs textually from {iana!r} "
                          "but produces same UTC moment")
    else:
        out["classification"] = "RECOMPUTE_REQUIRED"
        out["reason"] = (f"corrected tz shifts UTC by {utc_delta_min:+.0f} min and Asc by "
                          f"{(asc_delta if asc_delta else 0):.2f}°")
    return out


async def main():
    cohort_ids = []
    excl: set = set()

    # 1. Pete
    pete = await db.users.find_one({"_id": ObjectId("697f224b366f6814412d8c84")})
    if pete: cohort_ids.append(("Pete (anchor)", pete)); excl.add(str(pete["_id"]))
    # 2. Jaan
    jaan = await db.users.find_one({"_id": ObjectId("69894cc932380843ba87d121")})
    if jaan: cohort_ids.append(("Jaan (anchor)", jaan)); excl.add(str(jaan["_id"]))
    # 3. One +00:00 cluster representative
    rep_zero = await _pick_one({"timezone": "+00:00"}, excl)
    if rep_zero: cohort_ids.append(("+00:00 cluster representative", rep_zero)); excl.add(str(rep_zero["_id"]))
    # 4. One +08:00 cluster representative (other than Jaan)
    rep_eight = await _pick_one({"timezone": "+08:00"}, excl)
    if rep_eight: cohort_ids.append(("+08:00 cluster representative", rep_eight)); excl.add(str(rep_eight["_id"]))
    # 5. One North-America stored-tz representative
    rep_na = await _pick_one({"timezone": {"$regex": "^America/", "$options": ""}}, excl)
    if rep_na: cohort_ids.append(("North-America cluster representative", rep_na)); excl.add(str(rep_na["_id"]))

    print("=" * 78); print("Cohort selection"); print("=" * 78)
    for label, u in cohort_ids:
        print(f"  {label:<40} | user_id={str(u['_id']):<28} stored_tz={u.get('timezone')!r}  name={u.get('name')!r}")

    print()
    results = []
    for label, u in cohort_ids:
        r = await _audit_user(u)
        r["cohort_role"] = label
        results.append(r)

    # ----- Print per-user audit -----
    import json
    for r in results:
        print("=" * 78); print(f"{r['cohort_role']} — {r['name']!r} ({r['user_id']})"); print("=" * 78)
        print(json.dumps({k: r[k] for k in ("step1_current_state", "step2_resolver",
                                            "step3_recompute_in_memory",
                                            "step4_rollback_snapshot_plan",
                                            "classification", "reason")},
                         indent=2, default=str))

    # ----- Summary -----
    print()
    print("=" * 78); print("Cohort summary"); print("=" * 78)
    counts = {"SAFE": 0, "FORMAT_ONLY": 0, "RECOMPUTE_REQUIRED": 0, "UNKNOWN": 0}
    for r in results: counts[r.get("classification", "UNKNOWN")] += 1
    for k, v in counts.items(): print(f"  {k:<22}: {v}")
    print()
    print("No DB writes performed. No charts updated. No caches invalidated.")


if __name__ == "__main__":
    asyncio.run(main())
