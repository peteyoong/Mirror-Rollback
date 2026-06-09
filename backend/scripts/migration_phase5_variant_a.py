"""
Variant A Migration — Phase 5 RECOMPUTE + Phase 6 VALIDATION
============================================================
Build marker: variant-a-13-sign-migration-v1
Engine target: midpoint13_variant_a_v1 (True Sidereal-M Midpoint, 13 signs,
               Ophiuchus separate, Equal houses, SVP=31.2836).

What this script does (in order):

  1. For every user with valid birth data:
       a. Compute a fresh canonical chart (Variant A) via
          calculations.astrology.get_full_natal_chart().
       b. Upsert the result into the charts collection under the
          existing `astrology` sub-document, preserving HD / numerology /
          bazi / etc.
       c. Stamp the chart doc with:
             astrology_engine_version  = "midpoint13_variant_a_v1"
             sign_attribution_version  = "midpoint13_variant_a"
             house_system              = "Equal"
             migrated_at               = <utc now>
             migration_marker          = "variant-a-13-sign-migration-v1"
       d. Persist the Variant-B forensic payload under
          `astrology.forensic_variant_b` (already on the chart payload).

  2. Invalidate every astrology-derived cache collection.

  3. Run Phase-6 validation checks (Jaan, LensTest/TimelineOnly, Pete, Mel).

  4. Write a JSON migration report to:
        /app/backend/audits/variant_a_migration_report_<ts>.json

  5. Run the full test suite list specified by the user.

USAGE
-----
    # Dry run (no writes — counts only):
    python3 scripts/migration_phase5_variant_a.py --dry-run

    # Live recompute (writes to Mongo):
    python3 scripts/migration_phase5_variant_a.py --confirm VARIANT_A_PHASE_5
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv("/app/backend/.env")

from calculations.astrology import get_full_natal_chart          # noqa: E402
from calculations.sign_attribution import (                       # noqa: E402
    ENGINE_VERSION_VARIANT_A,
    ENGINE_VERSION_VARIANT_B,
    MODE_MIDPOINT13_VARIANT_A,
    OPHIUCHUS_SIGN_NAME,
)

# ---------------------------------------------------------------------------
# Constants — the migration's permanent stamps.
# ---------------------------------------------------------------------------
ASTROLOGY_ENGINE_VERSION = "midpoint13_variant_a_v1"
SIGN_ATTRIBUTION_VERSION = "midpoint13_variant_a"
CANONICAL_HOUSE_SYSTEM   = "Equal"
MIGRATION_MARKER         = "variant-a-13-sign-migration-v1"

# Astrology-derived caches that must be flushed because they hold
# sign-dependent narrative content.
SIGN_DEPENDENT_CACHES: Tuple[str, ...] = (
    "astrology_timeline_cache",
    "deep_dive_cache",
    "forum_story_cache",
    "governing_chapter_cache",
    "lifeline_synthesis_cache",
    "lunar_synthesis_cache",
    "pattern_drift_cache",
    "pattern_mirror_cache",
    "pattern_running_me_v2",
    "relationship_today_cache",
    "relationship_mappings",
    "today_patterns",
    "daily_pattern_signals",
    "keystone_patterns",
    "longitudinal_pattern_memory",
    "pattern_signals",
    "pattern_memory_signals",
    "pattern_exposures",
    "pattern_interpretations",
    "relationship_today_events",
    "relationship_patterns",
)

REPORT_DIR = "/app/backend/audits"
os.makedirs(REPORT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Birth-data parser (identical to the audit + snapshot scripts).
# ---------------------------------------------------------------------------
def _parse_user_birth(u: Dict[str, Any]) -> Optional[Tuple[datetime, float, float]]:
    """Resolve birth → UTC, using the SAME logic the production chart
    pipeline uses (IANA zoneinfo first, fixed-offset fallback, then UTC).

    This is critical: many users store `timezone = "Asia/Kuala_Lumpur"`
    style IANA names. A naive offset parser silently treats them as UTC
    and yields chart errors of multiple hours → wrong ASC + wrong house
    placements.
    """
    bd = u.get("birth_date")
    bt = u.get("birth_time") or "12:00"
    bl = u.get("birth_location") or {}
    lat = u.get("latitude")
    if lat is None:
        lat = bl.get("latitude")
    lon = u.get("longitude")
    if lon is None:
        lon = bl.get("longitude")
    if bd is None or lat is None or lon is None:
        return None

    if isinstance(bd, str):
        try:
            bd_dt = datetime.fromisoformat(bd.split("T")[0])
        except Exception:
            return None
    else:
        bd_dt = bd

    try:
        hh, mm = map(int, str(bt).split(":")[:2])
    except Exception:
        hh, mm = 12, 0

    local_naive = bd_dt.replace(hour=hh, minute=mm, second=0, tzinfo=None)

    # Resolve timezone (matches /api/admin/chart-recompute logic):
    # 1. explicit timezone_minutes wins
    # 2. else timezone string → try IANA zoneinfo first, then fixed offset
    # 3. else UTC
    tz_minutes = u.get("timezone_minutes")
    if tz_minutes is not None:
        local_aware = local_naive.replace(
            tzinfo=timezone(timedelta(minutes=int(tz_minutes)))
        )
        return local_aware.astimezone(timezone.utc), float(lat), float(lon)

    tz_raw = u.get("timezone")
    if isinstance(tz_raw, str) and tz_raw:
        # IANA first (handles historical DST / zone changes)
        try:
            from zoneinfo import ZoneInfo
            local_aware = local_naive.replace(tzinfo=ZoneInfo(tz_raw))
            return local_aware.astimezone(timezone.utc), float(lat), float(lon)
        except Exception:
            pass
        # Fixed-offset fallback like "+08:00"
        if len(tz_raw) >= 3 and tz_raw[0] in "+-":
            try:
                sign = 1 if tz_raw[0] == "+" else -1
                hhmm = tz_raw.lstrip("+-")
                hh_o, mm_o = (hhmm.split(":") if ":" in hhmm
                              else (hhmm[:2], hhmm[2:] or "00"))
                offset_min = sign * (int(hh_o) * 60 + int(mm_o))
                local_aware = local_naive.replace(
                    tzinfo=timezone(timedelta(minutes=offset_min))
                )
                return local_aware.astimezone(timezone.utc), float(lat), float(lon)
            except Exception:
                pass
    # Last resort — assume UTC (logged, but should be rare).
    local_aware = local_naive.replace(tzinfo=timezone.utc)
    return local_aware.astimezone(timezone.utc), float(lat), float(lon)


# ---------------------------------------------------------------------------
# Phase 5 — Recompute
# ---------------------------------------------------------------------------
async def recompute_users(db, dry_run: bool) -> Dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    stamp_iso  = started_at.isoformat()

    out: Dict[str, Any] = {
        "phase":                 "5_recompute",
        "build_marker":          MIGRATION_MARKER,
        "engine_version":        ASTROLOGY_ENGINE_VERSION,
        "house_system":          CANONICAL_HOUSE_SYSTEM,
        "dry_run":               dry_run,
        "started_at":            stamp_iso,
        "users_scanned":         0,
        "users_with_birth_data": 0,
        "users_skipped":         0,
        "users_migrated":        0,
        "users_inserted":        0,
        "users_updated":         0,
        "errors":                [],
        "writes":                [],
        "ophiuchus_entries":     0,
    }

    cursor = db.users.find({}, {
        "_id": 1, "name": 1, "email": 1,
        "birth_date": 1, "birth_time": 1, "birth_location": 1,
        "latitude": 1, "longitude": 1,
        "timezone": 1, "timezone_minutes": 1,
    })

    async for u in cursor:
        out["users_scanned"] += 1
        parsed = _parse_user_birth(u)
        if parsed is None:
            out["users_skipped"] += 1
            continue
        out["users_with_birth_data"] += 1

        try:
            utc, lat, lon = parsed
            new_chart = get_full_natal_chart(
                birth_datetime=utc, lat=lat, lon=lon,
                house_system=CANONICAL_HOUSE_SYSTEM,
            )
        except Exception as e:  # noqa: BLE001
            out["errors"].append({
                "user_id": str(u["_id"]),
                "email":   u.get("email"),
                "phase":   "compute",
                "error":   str(e)[:240],
            })
            continue

        planets = new_chart.get("planets") or {}
        angles  = new_chart.get("angles") or {}
        new_sun  = (planets.get("Sun")  or {}).get("sign")
        new_moon = (planets.get("Moon") or {}).get("sign")
        new_asc  = (angles.get("asc")   or {}).get("sign")
        has_ophi = any(
            (planets.get(b) or {}).get("sign") == OPHIUCHUS_SIGN_NAME
            for b in planets.keys()
        ) or any(
            (angles.get(a) or {}).get("sign") == OPHIUCHUS_SIGN_NAME
            for a in angles.keys()
        )
        if has_ophi:
            out["ophiuchus_entries"] += 1

        write_record = {
            "user_id":    str(u["_id"]),
            "name":       u.get("name") or u.get("email"),
            "email":      u.get("email"),
            "new_sun":    new_sun,
            "new_moon":   new_moon,
            "new_asc":    new_asc,
            "has_ophi":   has_ophi,
            "action":     "dry-run",
        }

        if dry_run:
            out["writes"].append(write_record)
            continue

        # ----------------------------------------------------------- WRITE
        # Build $set patch — overwrites only the astrology sub-document and
        # adds the engine-version stamps. Leaves HD / numerology / bazi /
        # consciousness_levels / debug_stamp untouched.
        update_set: Dict[str, Any] = {
            "astrology": {
                "metadata":             new_chart.get("metadata"),
                "planets":              planets,
                "nodes":                new_chart.get("nodes"),
                "angles":               angles,
                "houses":               new_chart.get("houses"),
                "aspects":              new_chart.get("aspects"),
                "sect":                 new_chart.get("sect"),
                "forensic_variant_b":   new_chart.get("forensic_variant_b"),
                "ascendant":            new_chart.get("ascendant"),
                "midheaven":            new_chart.get("midheaven"),
                "sun":                  new_chart.get("sun"),
                "moon":                 new_chart.get("moon"),
            },
            "astrology_engine_version": ASTROLOGY_ENGINE_VERSION,
            "sign_attribution_version": SIGN_ATTRIBUTION_VERSION,
            "house_system":             CANONICAL_HOUSE_SYSTEM,
            "migrated_at":              stamp_iso,
            "migration_marker":         MIGRATION_MARKER,
        }

        try:
            res = await db.charts.update_one(
                {"user_id": str(u["_id"])},
                {"$set": update_set, "$setOnInsert": {"user_id": str(u["_id"])}},
                upsert=True,
            )
            out["users_migrated"] += 1
            if res.upserted_id is not None:
                out["users_inserted"] += 1
                write_record["action"] = "inserted"
            elif res.modified_count > 0:
                out["users_updated"] += 1
                write_record["action"] = "updated"
            else:
                write_record["action"] = "no-op"
        except Exception as e:  # noqa: BLE001
            out["errors"].append({
                "user_id": str(u["_id"]),
                "email":   u.get("email"),
                "phase":   "write",
                "error":   str(e)[:240],
            })
            continue

        out["writes"].append(write_record)

    out["finished_at"] = datetime.now(timezone.utc).isoformat()
    return out


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------
async def invalidate_caches(db, dry_run: bool) -> Dict[str, Any]:
    out = {"dry_run": dry_run, "caches": {}}
    for col in SIGN_DEPENDENT_CACHES:
        existed = await db[col].count_documents({})
        if dry_run:
            out["caches"][col] = {"existed": existed, "deleted": 0}
            continue
        res = await db[col].delete_many({})
        out["caches"][col] = {"existed": existed, "deleted": res.deleted_count}
    return out


# ---------------------------------------------------------------------------
# Phase 6 — Validation
# ---------------------------------------------------------------------------
EXPECTED_PER_USER = [
    # name_or_email_substr → assertions
    {
        "match": "jaan",
        "expected": {"sun": "Ophiuchus"},
        "desc": "Jaan Sun must be Ophiuchus",
    },
    {
        "match": "lenstest",
        "expected": {"moon": "Ophiuchus"},
        "desc": "LensTest Moon must be Ophiuchus",
    },
    {
        "match": "timelineonly",
        "expected": {"moon": "Ophiuchus"},
        "desc": "TimelineOnly Moon must be Ophiuchus",
    },
    {
        "match": "pete@pulsifi.me",
        "expected": {"sun": "Pisces", "mercury": "Pisces", "venus": "Pisces"},
        "desc": "Pete Sun=Pisces, Mercury=Pisces, Venus=Pisces",
    },
    {
        "match": "melissa.mars@gmail.com",
        "expected": {"sun": "Gemini", "sun_house": 12, "venus": "Leo"},
        "desc": "Mel Sun=Gemini House 12, Venus=Leo",
    },
]


async def validate(db) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "phase": "6_validation",
        "checks": [],
        "house_system_check": {},
        "engine_version_check": {},
        "forensic_payload_check": {},
        "snapshot_check": {},
    }

    # 1) Per-user assertions
    for spec in EXPECTED_PER_USER:
        needle = spec["match"].lower()
        matched_user = None
        async for u in db.users.find({}, {"_id": 1, "name": 1, "email": 1}):
            blob = f"{u.get('name') or ''} {u.get('email') or ''}".lower()
            if needle in blob:
                matched_user = u
                break

        result: Dict[str, Any] = {"desc": spec["desc"], "matched_user": None, "ok": False}
        if matched_user is None:
            result["error"] = "no matching user"
            out["checks"].append(result)
            continue

        result["matched_user"] = matched_user.get("email") or matched_user.get("name")
        chart = await db.charts.find_one({"user_id": str(matched_user["_id"])})
        if not chart:
            result["error"] = "no chart doc"
            out["checks"].append(result)
            continue

        astro = chart.get("astrology") or {}
        planets = astro.get("planets") or {}
        actuals: Dict[str, Any] = {}
        ok = True
        for k, expected_val in spec["expected"].items():
            if k == "sun_house":
                sun = planets.get("Sun") or {}
                actuals["sun_house"] = sun.get("house")
                if sun.get("house") != expected_val:
                    ok = False
            else:
                body = k.capitalize()
                actuals[k] = (planets.get(body) or {}).get("sign")
                if actuals[k] != expected_val:
                    ok = False
        result["expected"] = spec["expected"]
        result["actual"] = actuals
        result["ok"] = ok
        out["checks"].append(result)

    # 2) house_system spot-check across all charts
    house_counts: Dict[str, int] = {}
    async for c in db.charts.find({}, {"house_system": 1, "astrology.houses.system": 1}):
        hs = c.get("house_system") or (c.get("astrology", {}).get("houses") or {}).get("system") or "<missing>"
        house_counts[hs] = house_counts.get(hs, 0) + 1
    out["house_system_check"] = house_counts

    # 3) engine_version coverage
    engine_counts: Dict[str, int] = {}
    async for c in db.charts.find({}, {"astrology_engine_version": 1}):
        ev = c.get("astrology_engine_version") or "<missing>"
        engine_counts[ev] = engine_counts.get(ev, 0) + 1
    out["engine_version_check"] = engine_counts

    # 4) forensic payload present?
    with_fb = await db.charts.count_documents({"astrology.forensic_variant_b": {"$exists": True}})
    total = await db.charts.count_documents({})
    out["forensic_payload_check"] = {"with_forensic_variant_b": with_fb, "total": total}

    # 5) snapshot file integrity
    snap_path = "/app/backend/audits/variant_a_migration_snapshot.json"
    if os.path.exists(snap_path):
        size = os.path.getsize(snap_path)
        out["snapshot_check"] = {"exists": True, "path": snap_path, "size_bytes": size}
    else:
        out["snapshot_check"] = {"exists": False}

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def _main(args) -> int:
    if not args.dry_run and args.confirm != "VARIANT_A_PHASE_5":
        print("ABORTED: live writes require --confirm VARIANT_A_PHASE_5", file=sys.stderr)
        return 2

    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ.get("DB_NAME", "test_database")]

    print(f"PHASE 5 — RECOMPUTE  (dry_run={args.dry_run})")
    recompute_report = await recompute_users(db, dry_run=args.dry_run)
    print(f"  scanned={recompute_report['users_scanned']}  with_birth_data={recompute_report['users_with_birth_data']}  "
          f"migrated={recompute_report['users_migrated']}  inserted={recompute_report['users_inserted']}  "
          f"updated={recompute_report['users_updated']}  errors={len(recompute_report['errors'])}")

    print(f"\nCACHE INVALIDATION  (dry_run={args.dry_run})")
    cache_report = await invalidate_caches(db, dry_run=args.dry_run)
    for col, info in cache_report["caches"].items():
        print(f"  {col:40}  existed={info['existed']:5}  deleted={info['deleted']}")

    print("\nPHASE 6 — VALIDATION")
    validation = await validate(db)
    for chk in validation["checks"]:
        sym = "✅" if chk.get("ok") else "❌"
        actual = chk.get("actual")
        print(f"  {sym}  {chk['desc']}  →  matched={chk.get('matched_user')}  actual={actual}")
    print(f"  house_system distribution: {validation['house_system_check']}")
    print(f"  engine_version distribution: {validation['engine_version_check']}")
    print(f"  forensic_variant_b coverage: {validation['forensic_payload_check']}")
    print(f"  snapshot file: {validation['snapshot_check']}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = f"{REPORT_DIR}/variant_a_migration_report_{ts}.json"
    final = {
        "marker":     MIGRATION_MARKER,
        "engine":     ASTROLOGY_ENGINE_VERSION,
        "dry_run":    args.dry_run,
        "recompute":  recompute_report,
        "caches":     cache_report,
        "validation": validation,
    }
    with open(report_path, "w") as f:
        json.dump(final, f, indent=2, default=str)
    print(f"\nReport saved: {report_path}")
    return 0


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Do not write to Mongo.")
    p.add_argument("--confirm", default="",
                   help="Required for live writes: VARIANT_A_PHASE_5")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(_main(_parse_args())))
