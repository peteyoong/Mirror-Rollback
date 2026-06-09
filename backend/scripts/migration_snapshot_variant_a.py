"""
Variant A Migration Snapshot (READ-ONLY)
=========================================
Build marker: ophiuchus-first-class-content-v1
PHASE 5 PRE-FLIGHT — snapshot capture (per user request)

Captures, for every user with valid birth data, a side-by-side record of:
  - old (currently-stored) Sun / Moon / ASC sign + engine_version
  - new (Variant A canonical recompute) Sun / Moon / ASC sign + engine_version
  - whether any placement enters Ophiuchus under Variant A
  - whether Sun specifically enters Ophiuchus
  - whether Moon specifically enters Ophiuchus

This snapshot is the rollback / forensic reference for the upcoming Phase 5
recompute. It is written BEFORE any chart write occurs.

Writes ONE local file:
    /app/backend/audits/variant_a_migration_snapshot.json

Does NOT:
  - Modify migration logic.
  - Write to Mongo (charts, users, caches — nothing).
  - Trigger Phase 5 recompute.

USAGE
-----
    python3 scripts/migration_snapshot_variant_a.py
"""
from __future__ import annotations

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

from calculations.astrology import get_full_natal_chart  # noqa: E402
from calculations.sign_attribution import (                # noqa: E402
    ENGINE_VERSION_VARIANT_A,
    ENGINE_VERSION_VARIANT_B,
    OPHIUCHUS_SIGN_NAME,
)

SNAPSHOT_PATH = "/app/backend/audits/variant_a_migration_snapshot.json"
os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)

# Bodies tracked for Ophiuchus detection.
ALL_TRACKED_BODIES = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)
ALL_TRACKED_ANGLES = ("asc", "mc", "dc", "ic")


# ---------------------------------------------------------------------------
# Birth-data parser (mirrors migration_audit_variant_a.py — kept identical
# so the snapshot reflects exactly what Phase 5 will see).
# ---------------------------------------------------------------------------
def _parse_user_birth(u: Dict[str, Any]) -> Optional[Tuple[datetime, float, float]]:
    """IANA-first timezone resolution. Mirrors the production chart
    pipeline; matches scripts/migration_phase5_variant_a.py."""
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
    tz_minutes = u.get("timezone_minutes")
    if tz_minutes is not None:
        local_aware = local_naive.replace(
            tzinfo=timezone(timedelta(minutes=int(tz_minutes)))
        )
        return local_aware.astimezone(timezone.utc), float(lat), float(lon)
    tz_raw = u.get("timezone")
    if isinstance(tz_raw, str) and tz_raw:
        try:
            from zoneinfo import ZoneInfo
            local_aware = local_naive.replace(tzinfo=ZoneInfo(tz_raw))
            return local_aware.astimezone(timezone.utc), float(lat), float(lon)
        except Exception:
            pass
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
    local_aware = local_naive.replace(tzinfo=timezone.utc)
    return local_aware.astimezone(timezone.utc), float(lat), float(lon)


# ---------------------------------------------------------------------------
# Read the CURRENTLY-STORED chart for a user. Mongo charts collection holds
# the legacy Variant-B-attributed payload until Phase 5 runs.
# ---------------------------------------------------------------------------
async def _fetch_stored_chart(db, user_id: Any) -> Optional[Dict[str, Any]]:
    """Look up the user's stored chart document. Schema varies — try a few
    common shapes the production code uses."""
    for q in (
        {"user_id": str(user_id)},
        {"user_id": user_id},
        {"userId": str(user_id)},
    ):
        doc = await db.charts.find_one(q)
        if doc:
            return doc
    # Fallback: chart embedded inside user document.
    udoc = await db.users.find_one({"_id": user_id})
    if udoc and isinstance(udoc.get("chart"), dict):
        return udoc["chart"]
    return None


def _extract_sign(doc: Optional[Dict[str, Any]], body: str, is_angle: bool = False) -> Optional[str]:
    """Pull the sign label for a planet or angle out of a stored chart
    document. Tolerant of the few payload shapes we have in production
    (top-level `planets`, embedded `astrology.planets`, etc.)."""
    if not isinstance(doc, dict):
        return None

    def _scan(scope: Dict[str, Any]) -> Optional[str]:
        if not isinstance(scope, dict):
            return None
        if is_angle:
            angles = scope.get("angles") or {}
            a = angles.get(body)
            if isinstance(a, dict):
                return a.get("sign")
            # Some payloads use uppercase angle keys (e.g. "ASC")
            a2 = angles.get(body.upper())
            if isinstance(a2, dict):
                return a2.get("sign")
            return None
        planets = scope.get("planets") or {}
        p = planets.get(body)
        if isinstance(p, dict):
            return p.get("sign")
        return None

    # Direct shape
    sign = _scan(doc)
    if sign:
        return sign
    # Embedded under "astrology"
    sign = _scan(doc.get("astrology") or {})
    if sign:
        return sign
    # Embedded under "natal"
    sign = _scan(doc.get("natal") or {})
    if sign:
        return sign
    return None


def _extract_old_engine_version(doc: Optional[Dict[str, Any]]) -> str:
    """Best-effort lookup of the stored chart's engine_version. Falls back
    to Variant B (midpoint12) when missing — that's the pre-migration
    canonical engine."""
    if not isinstance(doc, dict):
        return ENGINE_VERSION_VARIANT_B
    for path in (
        ("astrology_engine_version",),
        ("metadata", "astrology_engine_version"),
        ("astrology", "metadata", "astrology_engine_version"),
        ("natal", "metadata", "astrology_engine_version"),
        ("engine_version",),
    ):
        cur: Any = doc
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok and isinstance(cur, str) and cur:
            return cur
    return ENGINE_VERSION_VARIANT_B


# ---------------------------------------------------------------------------
# Build per-user snapshot row.
# ---------------------------------------------------------------------------
def _build_row(
    user: Dict[str, Any],
    stored_chart: Optional[Dict[str, Any]],
    new_chart: Dict[str, Any],
) -> Dict[str, Any]:
    # Old (currently-stored) labels
    old_sun  = _extract_sign(stored_chart, "Sun")
    old_moon = _extract_sign(stored_chart, "Moon")
    old_asc  = _extract_sign(stored_chart, "asc", is_angle=True)
    old_engine = _extract_old_engine_version(stored_chart)

    # New (Variant A) labels — straight from the freshly-computed chart.
    planets_new = new_chart.get("planets") or {}
    angles_new  = new_chart.get("angles") or {}
    new_sun  = (planets_new.get("Sun") or {}).get("sign")
    new_moon = (planets_new.get("Moon") or {}).get("sign")
    new_asc  = (angles_new.get("asc")  or {}).get("sign")
    new_engine = new_chart.get("astrology_engine_version") or ENGINE_VERSION_VARIANT_A

    # Ophiuchus detection — scan every tracked body + angle in the NEW chart.
    ophi_bodies: List[str] = []
    for body in ALL_TRACKED_BODIES:
        if (planets_new.get(body) or {}).get("sign") == OPHIUCHUS_SIGN_NAME:
            ophi_bodies.append(body)
    for ang in ALL_TRACKED_ANGLES:
        if (angles_new.get(ang) or {}).get("sign") == OPHIUCHUS_SIGN_NAME:
            ophi_bodies.append(ang.upper())

    return {
        "user_id":                str(user["_id"]),
        "name":                   user.get("name") or user.get("email"),
        "email":                  user.get("email"),
        "old_engine_version":     old_engine,
        "new_engine_version":     new_engine,
        "old_sun":                old_sun,
        "new_sun":                new_sun,
        "old_moon":               old_moon,
        "new_moon":               new_moon,
        "old_asc":                old_asc,
        "new_asc":                new_asc,
        "any_placement_entered_ophiuchus":  bool(ophi_bodies),
        "sun_entered_ophiuchus":            new_sun  == OPHIUCHUS_SIGN_NAME,
        "moon_entered_ophiuchus":           new_moon == OPHIUCHUS_SIGN_NAME,
        "ophiuchus_bodies":                 sorted(set(ophi_bodies)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def run_snapshot() -> Dict[str, Any]:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ.get("DB_NAME", "test_database")]

    started_at = datetime.now(timezone.utc)
    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    users_scanned          = 0
    users_with_birth_data  = 0
    users_skipped_no_birth = 0
    sun_changes            = 0
    moon_changes           = 0
    asc_changes            = 0
    sun_into_ophi          = 0
    moon_into_ophi         = 0
    any_into_ophi          = 0

    cursor = db.users.find({}, {
        "_id": 1, "name": 1, "email": 1,
        "birth_date": 1, "birth_time": 1, "birth_location": 1,
        "latitude": 1, "longitude": 1,
        "timezone": 1, "timezone_minutes": 1,
    })

    async for u in cursor:
        users_scanned += 1
        parsed = _parse_user_birth(u)
        if parsed is None:
            users_skipped_no_birth += 1
            continue
        users_with_birth_data += 1

        try:
            utc, lat, lon = parsed
            new_chart = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon)
            stored_chart = await _fetch_stored_chart(db, u["_id"])
            row = _build_row(u, stored_chart, new_chart)
        except Exception as e:  # noqa: BLE001
            errors.append({
                "user_id": str(u["_id"]),
                "email":   u.get("email"),
                "error":   str(e)[:250],
            })
            continue

        rows.append(row)

        if row["old_sun"] and row["new_sun"] and row["old_sun"]  != row["new_sun"]:
            sun_changes += 1
        if row["old_moon"] and row["new_moon"] and row["old_moon"] != row["new_moon"]:
            moon_changes += 1
        if row["old_asc"] and row["new_asc"] and row["old_asc"]  != row["new_asc"]:
            asc_changes += 1
        if row["sun_entered_ophiuchus"]:           sun_into_ophi += 1
        if row["moon_entered_ophiuchus"]:          moon_into_ophi += 1
        if row["any_placement_entered_ophiuchus"]: any_into_ophi += 1

    finished_at = datetime.now(timezone.utc)

    snapshot = {
        "marker":                       "variant_a_migration_snapshot_v1",
        "build_marker":                 "ophiuchus-first-class-content-v1",
        "purpose":                      "Pre-Phase-5 rollback/forensic baseline. NO Mongo writes performed.",
        "started_at":                   started_at.isoformat(),
        "finished_at":                  finished_at.isoformat(),
        "snapshot_path":                SNAPSHOT_PATH,
        "old_engine_default":           ENGINE_VERSION_VARIANT_B,
        "new_engine_target":            ENGINE_VERSION_VARIANT_A,
        "dry_run":                      True,
        "writes_performed":             0,
        "counts": {
            "users_scanned":            users_scanned,
            "users_with_birth_data":    users_with_birth_data,
            "users_skipped_no_birth":   users_skipped_no_birth,
            "users_changing_sun":       sun_changes,
            "users_changing_moon":      moon_changes,
            "users_changing_asc":       asc_changes,
            "users_sun_into_ophiuchus": sun_into_ophi,
            "users_moon_into_ophiuchus":moon_into_ophi,
            "users_any_into_ophiuchus": any_into_ophi,
            "errors":                   len(errors),
        },
        "users":                        rows,
        "errors":                       errors,
    }

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    return snapshot


def _print_summary(s: Dict[str, Any]) -> None:
    c = s["counts"]
    print("\n" + "=" * 70)
    print("VARIANT A MIGRATION SNAPSHOT — PRE-PHASE-5 BASELINE")
    print("=" * 70)
    print(f"Snapshot file:                 {s['snapshot_path']}")
    print(f"Started:                       {s['started_at']}")
    print(f"Finished:                      {s['finished_at']}")
    print(f"Old engine (rollback target):  {s['old_engine_default']}")
    print(f"New engine (Phase 5 canon):    {s['new_engine_target']}")
    print()
    print(f"Users scanned:                 {c['users_scanned']}")
    print(f"Users with birth data:         {c['users_with_birth_data']}")
    print(f"Users skipped (no birth):      {c['users_skipped_no_birth']}")
    print()
    print(f"Sun-sign changes:              {c['users_changing_sun']}")
    print(f"Moon-sign changes:             {c['users_changing_moon']}")
    print(f"ASC-sign changes:              {c['users_changing_asc']}")
    print(f"Sun → Ophiuchus:               {c['users_sun_into_ophiuchus']}")
    print(f"Moon → Ophiuchus:              {c['users_moon_into_ophiuchus']}")
    print(f"Any body → Ophiuchus:          {c['users_any_into_ophiuchus']}")
    print(f"Errors:                        {c['errors']}")
    print()
    print(f"Per-user rows written:         {len(s['users'])}")
    print()
    print(f"Snapshot written to: {SNAPSHOT_PATH}")
    print("READ-ONLY. No Mongo writes. No chart writes. No deploy.")
    print("=" * 70)


if __name__ == "__main__":
    snap = asyncio.run(run_snapshot())
    _print_summary(snap)
