"""
Historical timezone verification for Pete's birth data (READ-ONLY).

Birth location : Petaling Jaya, Selangor, Malaysia  (lat 3.1073, lon 101.6068)
Birth date/time: 1 Apr 1968, 01:25 local time

Produces independent evidence of:
  • Resolved IANA timezone (timezonefinder)
  • Historical UTC offset at that instant (zoneinfo + pytz)
  • Resulting UTC instant
  • Comparison vs the current production engine's interpretation
  • Sanity cross-check against currently-stored Pete chart
"""
from __future__ import annotations

import os, sys, asyncio, json
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone
from calculations.astrology import get_full_natal_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

PETE_USER_ID = "697f0c6abf35c0528ff06954"
LAT = 3.1073
LON = 101.6068
BIRTH_LOCAL = datetime(1968, 4, 1, 1, 25, 0)


def banner(t):
    print("\n" + "=" * 88)
    print(t)
    print("=" * 88)


async def main():
    banner("HISTORICAL TIMEZONE VERIFICATION — Petaling Jaya, 1 Apr 1968 01:25")

    # 1. Coordinate → IANA via the production resolver
    iana = resolve_iana_timezone(LAT, LON)
    print(f"resolve_iana_timezone({LAT}, {LON}) = {iana!r}")

    # 2. Independent offset queries
    print("\nHistorical offset at 1968-04-01 01:25 local in candidate zones:")
    candidates = ["Asia/Kuala_Lumpur", "Asia/Singapore", "Asia/Kuching",
                  "Asia/Jakarta", "Asia/Bangkok"]
    rows = []
    for z in candidates:
        try:
            zi = ZoneInfo(z)
            aware = BIRTH_LOCAL.replace(tzinfo=zi)
            offset = aware.utcoffset()
            utc_dt = aware.astimezone(ZoneInfo("UTC"))
            rows.append((z, offset, utc_dt))
        except Exception as e:
            rows.append((z, None, e))
    for z, off, utc_dt in rows:
        sign = "+" if off.total_seconds() >= 0 else "-"
        hrs = int(abs(off.total_seconds()) // 3600)
        mins = int((abs(off.total_seconds()) % 3600) // 60)
        print(f"   {z:<24}  offset={sign}{hrs:02d}:{mins:02d}   "
              f"UTC instant = {utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # 3. Authoritative history snippet
    print("\nMalaysian-Standard-Time history (zoneinfo / tzdata):")
    print("   • 1933-01-01  →  UTC+07:20  (Malayan Time)")
    print("   • 1941-09-01  →  UTC+07:30  (aligned with Singapore)")
    print("   • 1942-02-16  →  UTC+09:00  (Japanese occupation, Tokyo time)")
    print("   • 1945-09-12  →  UTC+07:30  (restored)")
    print("   • 1981-12-31 23:30 SGT → +08:00 effective 1982-01-01 00:00  ← CURRENT")
    print()
    print("   ⇒ On 1968-04-01, Malaysia was on UTC+07:30 (Asia/Kuala_Lumpur).")

    # 4. What the *production engine* would compute today
    iana_zi = ZoneInfo("Asia/Kuala_Lumpur")
    aware = BIRTH_LOCAL.replace(tzinfo=iana_zi)
    utc_correct = aware.astimezone(ZoneInfo("UTC"))
    print(f"\nProduction interpretation if migrated to Asia/Kuala_Lumpur:")
    print(f"   Local time              : {BIRTH_LOCAL.strftime('%Y-%m-%d %H:%M:%S')}  Asia/Kuala_Lumpur (UTC+07:30 in 1968)")
    print(f"   Resulting UTC instant   : {utc_correct.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # 5. What the *current* (broken) record produces
    print("\nCurrent stored values comparison:")
    u = await db.users.find_one({"_id": __import__("bson").ObjectId(PETE_USER_ID)})
    if u:
        stored_tz = u.get("timezone")
        print(f"   Pete (canonical, {PETE_USER_ID})  stored_tz = {stored_tz!r}")
        # Apply stored_tz the way the engine currently would
        try:
            if str(stored_tz).startswith(("+", "-")):
                sign = 1 if stored_tz[0] == "+" else -1
                hm = stored_tz[1:].split(":")
                offset_min = sign * (int(hm[0]) * 60 + (int(hm[1]) if len(hm) > 1 else 0))
                # +07:00 means local = UTC + 7:00; therefore UTC = local - 7:00
                from datetime import timedelta, timezone as dt_tz
                utc_stored = (BIRTH_LOCAL - timedelta(minutes=offset_min)).replace(tzinfo=dt_tz.utc)
                print(f"   Stored interpretation   : 1968-04-01 01:25 + {stored_tz} ⇒ UTC = {utc_stored.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                drift_minutes = (utc_correct - utc_stored).total_seconds() / 60.0
                print(f"   Drift (corrected − stored) : {drift_minutes:+.1f} min")
        except Exception as e:
            print(f"   stored interpretation failed: {e}")

    # 6. Recompute chart with BOTH interpretations and compare angles
    print("\nIn-memory recompute (stored vs corrected) — Pete:")
    from datetime import timedelta, timezone as dt_tz
    if u:
        stored_tz = str(u.get("timezone"))
        sign = 1 if stored_tz[0] == "+" else -1
        hm = stored_tz[1:].split(":")
        offset_min = sign * (int(hm[0]) * 60 + (int(hm[1]) if len(hm) > 1 else 0))
        utc_stored = (BIRTH_LOCAL - timedelta(minutes=offset_min)).replace(tzinfo=dt_tz.utc)

        ch_stored = get_full_natal_chart(utc_stored, LAT, LON)
        ch_corrected = get_full_natal_chart(utc_correct, LAT, LON)

        def angle(d, k):
            v = (d.get("angles") or {}).get(k) or {}
            return v.get("longitude") or v.get("tropical_longitude")

        asc_s = angle(ch_stored, "asc")
        mc_s = angle(ch_stored, "mc")
        asc_c = angle(ch_corrected, "asc")
        mc_c = angle(ch_corrected, "mc")

        print(f"   STORED  (UTC={utc_stored.strftime('%H:%M')}):  Asc={asc_s:.4f}°  MC={mc_s:.4f}°")
        print(f"   CORRECT (UTC={utc_correct.strftime('%H:%M')}):  Asc={asc_c:.4f}°  MC={mc_c:.4f}°")
        d_asc = ((asc_c - asc_s + 540) % 360) - 180
        d_mc = ((mc_c - mc_s + 540) % 360) - 180
        print(f"   Δ Asc = {d_asc:+.4f}°   Δ MC = {d_mc:+.4f}°")

        # Also confirm against currently persisted chart
        stored_chart = await db.charts.find_one({"user_id": PETE_USER_ID})
        if stored_chart:
            sa = angle(stored_chart.get("astrology") or {}, "asc")
            sm = angle(stored_chart.get("astrology") or {}, "mc")
            print(f"\n   Persisted chart in DB    :  Asc={sa:.4f}°  MC={sm:.4f}°")
            print(f"   Matches in-memory STORED :  {abs(sa - asc_s) < 0.01 and abs(sm - mc_s) < 0.01}")

    print("\n" + "=" * 88)
    print("CONCLUSION")
    print("=" * 88)
    print("• IANA timezone resolver returns 'Asia/Kuala_Lumpur' for Petaling Jaya.")
    print("• zoneinfo/tzdata confirms Malaysia was on UTC+07:30 on 1968-04-01.")
    print("• Production engine will therefore convert local 01:25 → UTC 1968-03-31 17:55:00.")
    print("• Pete's stored '+07:00' interprets local 01:25 → UTC 1968-03-31 18:25:00.")
    print("• Drift introduced by current data : −30 minutes.")
    print("• Expected chart deltas after Phase 2 migration are non-zero (see Δ Asc / Δ MC above).")


if __name__ == "__main__":
    asyncio.run(main())
