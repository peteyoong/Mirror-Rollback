"""
Phase 2 Readiness Gate — Full Chart/Input Consistency Audit (READ-ONLY).

Expansion of Phase 1.9 from a 24-user sample to every user in the DB.

For each user we (1) classify the user under the Phase-1.8 bucketing
(SAFE / FORMAT_ONLY / RECOMPUTE_REQUIRED / UNKNOWN), (2) recompute their
chart in memory from their *currently-stored* inputs and compare against
their persisted chart's Asc/MC (Phase-1.9 MATCH / MISMATCH / UNKNOWN), then
cross-tabulate. No writes occur at any step.
"""
from __future__ import annotations

import os, sys, asyncio
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone
from calculations.astrology import get_full_natal_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME","test_database")]

MATCH_TOL_DEG = 0.5
UTC_TOL_MIN = 1


def _parse_local(birth_date, birth_time):
    if not birth_date or not birth_time: return None
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        try: d = datetime.strptime(s, "%Y-%m-%d")
        except ValueError: return None
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt; is_am = "am" in bt
    t = bt.replace("am","").replace("pm","").strip().split(":")
    try:
        hh = int(t[0]); mm = int(t[1]) if len(t) > 1 else 0
    except (ValueError, IndexError): return None
    if is_pm and hh < 12: hh += 12
    if is_am and hh == 12: hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60): return None
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc(local_dt, tz_str):
    if not local_dt or not tz_str: return None
    s = str(tz_str).strip()
    try:
        if s.startswith(("+","-")):
            sign = 1 if s[0] == "+" else -1
            hm = s[1:].split(":")
            off = sign * (int(hm[0])*60 + (int(hm[1]) if len(hm)>1 else 0))
            return (local_dt - timedelta(minutes=off)).replace(tzinfo=dt_tz.utc)
        if s in ("UTC","GMT","Z"):
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


def _stored_asc_mc(chart):
    a = (chart.get("astrology") or {}) if chart else {}
    ang = a.get("angles") or {}
    asc = (ang.get("asc") or {}).get("longitude") or (ang.get("asc") or {}).get("tropical_longitude")
    mc  = (ang.get("mc")  or {}).get("longitude") or (ang.get("mc")  or {}).get("tropical_longitude")
    return (float(asc) if asc is not None else None,
            float(mc) if mc is not None else None)


async def main():
    total = 0
    rows = []
    cursor = db.users.find({})
    async for u in cursor:
        total += 1
        uid = str(u["_id"])
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude"); lon = bl.get("longitude")
        stored_tz = u.get("timezone")
        bdate = u.get("birth_date"); btime = u.get("birth_time")
        chart = await db.charts.find_one({"user_id": uid})

        row = {
            "user_id": uid, "name": u.get("name"), "email": u.get("email"),
            "stored_tz": stored_tz, "lat": lat, "lon": lon,
            "city": bl.get("city"), "country": bl.get("country"),
        }

        # ---------- Phase 1.8 classification ----------
        local_dt = _parse_local(bdate, btime)
        if lat is None or lon is None:
            row["phase18"] = "UNKNOWN"; row["p18_reason"] = "no_coords"
        elif not stored_tz:
            row["phase18"] = "UNKNOWN"; row["p18_reason"] = "no_stored_tz"
        elif not local_dt:
            row["phase18"] = "UNKNOWN"; row["p18_reason"] = "no_local_dt"
        else:
            try: iana = resolve_iana_timezone(float(lat), float(lon))
            except Exception: iana = None
            if not iana:
                row["phase18"] = "UNKNOWN"; row["p18_reason"] = "resolver_failed"
            else:
                stored_utc = _to_utc(local_dt, str(stored_tz))
                corrected_utc = _to_utc(local_dt, iana)
                if not stored_utc or not corrected_utc:
                    row["phase18"] = "UNKNOWN"; row["p18_reason"] = "utc_conversion_failed"
                else:
                    dmin = (corrected_utc - stored_utc).total_seconds() / 60.0
                    row["resolved_iana"] = iana
                    row["utc_delta_min"] = round(dmin, 2)
                    if str(stored_tz) == iana and abs(dmin) <= UTC_TOL_MIN:
                        row["phase18"] = "SAFE"
                    elif abs(dmin) <= UTC_TOL_MIN:
                        row["phase18"] = "FORMAT_ONLY"
                    else:
                        row["phase18"] = "RECOMPUTE_REQUIRED"

        # ---------- Phase 1.9 consistency ----------
        if not chart:
            row["phase19"] = "UNKNOWN"; row["p19_reason"] = "no_stored_chart"
        else:
            stored_asc, stored_mc = _stored_asc_mc(chart)
            a_meta = (chart.get("astrology") or {})
            md = a_meta.get("metadata") or {}
            row["engine_version"] = md.get("astrology_engine_version")
            row["computation_version"] = md.get("computation_version")
            row["debug_stamp_migration"] = (chart.get("debug_stamp") or {}).get("migration")
            row["forensic_variant_b"] = bool(chart.get("forensic_variant_b"))
            row["stored_asc"] = stored_asc; row["stored_mc"] = stored_mc
            if stored_asc is None or stored_mc is None:
                row["phase19"] = "UNKNOWN"; row["p19_reason"] = "no_stored_asc_mc"
            elif row.get("phase18") == "UNKNOWN":
                row["phase19"] = "UNKNOWN"; row["p19_reason"] = "phase18_unknown"
            else:
                stored_utc_for_recompute = _to_utc(local_dt, str(stored_tz))
                try:
                    ch = get_full_natal_chart(stored_utc_for_recompute, float(lat), float(lon))
                    ang = ch.get("angles") or {}
                    rasc = (ang.get("asc") or {}).get("longitude") or (ang.get("asc") or {}).get("tropical_longitude")
                    rmc  = (ang.get("mc")  or {}).get("longitude") or (ang.get("mc")  or {}).get("tropical_longitude")
                    if rasc is None or rmc is None:
                        row["phase19"] = "UNKNOWN"; row["p19_reason"] = "recompute_missing_angles"
                    else:
                        da = _ang_delta(stored_asc, float(rasc))
                        dm = _ang_delta(stored_mc, float(rmc))
                        row["recomp_asc"] = round(float(rasc), 4)
                        row["recomp_mc"] = round(float(rmc), 4)
                        row["asc_delta_deg"] = round(da, 4)
                        row["mc_delta_deg"]  = round(dm, 4)
                        row["phase19"] = ("MATCH" if (da <= MATCH_TOL_DEG and dm <= MATCH_TOL_DEG) else "MISMATCH")
                except Exception as e:
                    row["phase19"] = "UNKNOWN"; row["p19_reason"] = f"recompute_error:{type(e).__name__}"

        rows.append(row)

    # ----------------------------------------------------
    # Build cross-tab matrix
    # ----------------------------------------------------
    p18_buckets = ["SAFE", "FORMAT_ONLY", "RECOMPUTE_REQUIRED", "UNKNOWN"]
    p19_buckets = ["MATCH", "MISMATCH", "UNKNOWN"]
    mat = {a: {b: 0 for b in p19_buckets} for a in p18_buckets}
    for r in rows:
        a = r.get("phase18", "UNKNOWN"); b = r.get("phase19", "UNKNOWN")
        if a not in mat: a = "UNKNOWN"
        if b not in mat[a]: b = "UNKNOWN"
        mat[a][b] += 1

    print("=" * 78)
    print(f"Phase 2 Readiness Gate — Full Consistency Audit")
    print("=" * 78)
    print(f"Total users scanned: {total}")
    print()
    print("Cross-tabulation matrix (Phase 1.8 × Phase 1.9):")
    header = "P1.8 \\ P1.9"
    print(f"{header:<24}{'MATCH':>8}{'MISMATCH':>10}{'UNKNOWN':>10}{'TOTAL':>8}")
    for a in p18_buckets:
        ttl = sum(mat[a].values())
        print(f"{a:<24}{mat[a]['MATCH']:>8}{mat[a]['MISMATCH']:>10}{mat[a]['UNKNOWN']:>10}{ttl:>8}")
    grand = sum(sum(mat[a].values()) for a in p18_buckets)
    print(f"{'TOTAL':<24}"
          f"{sum(mat[a]['MATCH'] for a in p18_buckets):>8}"
          f"{sum(mat[a]['MISMATCH'] for a in p18_buckets):>10}"
          f"{sum(mat[a]['UNKNOWN'] for a in p18_buckets):>10}"
          f"{grand:>8}")
    print()

    # ----------------------------------------------------
    # MISMATCH rows
    # ----------------------------------------------------
    mismatches = [r for r in rows if r.get("phase19") == "MISMATCH"]
    print(f"MISMATCH count: {len(mismatches)}")
    if mismatches:
        print(f"{'user_id':<26}{'name':<22}{'phase18':<22}{'stored_tz':<22}{'resolved':<22}"
              f"{'asc_Δ':>8}{'mc_Δ':>8} cause")
        for r in sorted(mismatches, key=lambda x: -(x.get("asc_delta_deg") or 0)):
            # Likely-cause classifier
            cause = "unknown"
            engine = r.get("engine_version") or ""
            if r.get("phase18") == "RECOMPUTE_REQUIRED":
                cause = "timezone corruption — recompute will fix"
            elif r.get("phase18") in ("SAFE", "FORMAT_ONLY"):
                if r.get("debug_stamp_migration") in ("startup_svp_fix", None):
                    cause = "chart drift (stale recompute or pre-engine-upgrade snapshot)"
                else:
                    cause = "engine version mismatch"
            elif r.get("phase18") == "UNKNOWN":
                cause = "input data missing — manual triage"
            print(f"{r['user_id']:<26}{str(r.get('name'))[:20]:<22}"
                  f"{r.get('phase18','?'):<22}"
                  f"{str(r.get('stored_tz'))[:20]:<22}"
                  f"{str(r.get('resolved_iana'))[:20]:<22}"
                  f"{r.get('asc_delta_deg','?'):>8}"
                  f"{r.get('mc_delta_deg','?'):>8} {cause}")
    print()

    # ----------------------------------------------------
    # UNKNOWN breakdown
    # ----------------------------------------------------
    print("UNKNOWN row reasons (Phase 1.9 lens):")
    reason_counts: Dict[str, int] = {}
    for r in rows:
        if r.get("phase19") == "UNKNOWN":
            reason_counts[r.get("p19_reason","?")] = reason_counts.get(r.get("p19_reason","?"), 0) + 1
    for k, v in sorted(reason_counts.items(), key=lambda kv: -kv[1]):
        print(f"   {k:<30s} {v}")

    # ----------------------------------------------------
    # GO / NO-GO
    # ----------------------------------------------------
    print()
    print("=" * 78)
    print("GO / NO-GO determination")
    print("=" * 78)
    safe_or_format_with_mismatch = sum(
        1 for r in rows
        if r.get("phase18") in ("SAFE", "FORMAT_ONLY") and r.get("phase19") == "MISMATCH"
    )
    recompute_with_mismatch = sum(
        1 for r in rows
        if r.get("phase18") == "RECOMPUTE_REQUIRED" and r.get("phase19") == "MISMATCH"
    )
    print(f"  SAFE/FORMAT_ONLY users whose stored chart already disagrees: {safe_or_format_with_mismatch}")
    print(f"  RECOMPUTE_REQUIRED users with pre-existing chart drift:      {recompute_with_mismatch}")
    print()
    if safe_or_format_with_mismatch == 0 and recompute_with_mismatch == 0:
        print("  GO — every stored chart reproduces from its stored inputs.")
    else:
        print("  NO-GO — silent-drift users exist outside Phase 2's planned write set.")


if __name__ == "__main__":
    asyncio.run(main())
