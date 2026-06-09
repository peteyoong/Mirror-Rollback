"""
Variant A Migration Audit (READ-ONLY)
======================================
Build marker: midpoint13-variant-a-canonical-v1
PHASE 4 — Migration Audit (per user execution plan)

Scans every user with valid birth data and reports — without writing to
the database — how each user's chart would change if recomputed under
the canonical Variant A engine (midpoint13_variant_a_v1) versus the
currently-stored Variant B chart.

Counts produced:
  - users_scanned
  - users_with_chart
  - users_with_birth_data
  - users_changing_sun
  - users_changing_moon
  - users_changing_asc
  - users_entering_ophiuchus (any body lands in Ophiuchus under V-A)
  - per-body changes (Sun/Moon/Mercury/Venus/Mars/ASC)

Writes the report to /app/backend/audits/variant_a_migration_audit_<ts>.json
and prints a human-readable summary.

USAGE
-----
    python3 scripts/migration_audit_variant_a.py            # full audit
    python3 scripts/migration_audit_variant_a.py --limit 5  # quick smoke

No DB writes. Safe to run at any time.
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

from calculations.astrology import get_full_natal_chart  # noqa: E402
from calculations.sign_attribution import (                # noqa: E402
    attribute_sign_midpoint12_variant_b,
    attribute_sign_midpoint13_variant_a,
    ENGINE_VERSION_VARIANT_A,
    ENGINE_VERSION_VARIANT_B,
    OPHIUCHUS_SIGN_NAME,
)

REPORT_DIR = "/app/backend/audits"
os.makedirs(REPORT_DIR, exist_ok=True)

BODIES_TRACKED = ("Sun", "Moon", "Mercury", "Venus", "Mars",
                  "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
ANGLES_TRACKED = ("asc", "mc", "dc", "ic")


# ---------------------------------------------------------------------------
# Birth-data parsing (mirrors the production parser in admin_gm_aligned.py)
# ---------------------------------------------------------------------------
def _parse_user_birth(u: Dict[str, Any]) -> Optional[Tuple[datetime, float, float]]:
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

    tz_minutes = u.get("timezone_minutes")
    if tz_minutes is None:
        tz_str = u.get("timezone")
        if isinstance(tz_str, str) and len(tz_str) >= 3 and tz_str[0] in "+-":
            sign = 1 if tz_str[0] == "+" else -1
            try:
                if ":" in tz_str:
                    h, m = map(int, tz_str[1:].split(":"))
                else:
                    h, m = int(tz_str[1:3]), 0
                tz_minutes = sign * (h * 60 + m)
            except Exception:
                tz_minutes = 0
        elif isinstance(tz_str, (int, float)):
            tz_minutes = int(tz_str * 60)
        else:
            tz_minutes = 0

    local = bd_dt.replace(
        hour=hh, minute=mm, second=0,
        tzinfo=timezone(timedelta(minutes=int(tz_minutes))),
    )
    return local.astimezone(timezone.utc), float(lat), float(lon)


# ---------------------------------------------------------------------------
# Per-user audit
# ---------------------------------------------------------------------------
def _audit_chart_for_user(utc: datetime, lat: float, lon: float) -> Dict[str, Any]:
    """Compute the Variant A chart and emit per-body Variant A vs B sign deltas.

    Pure read-only. Does NOT touch the DB."""
    chart = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon)
    planets = chart.get("planets") or {}
    angles  = chart.get("angles") or {}

    body_changes: List[Dict[str, Any]] = []
    angle_changes: List[Dict[str, Any]] = []
    ophiuchus_bodies: List[str] = []

    for body in BODIES_TRACKED:
        p = planets.get(body) or {}
        trop = p.get("tropical_longitude")
        if trop is None:
            continue
        a = attribute_sign_midpoint13_variant_a(trop)
        b = attribute_sign_midpoint12_variant_b(trop)
        if a["sign"] == OPHIUCHUS_SIGN_NAME:
            ophiuchus_bodies.append(body)
        if a["sign"] != b["sign"]:
            body_changes.append({
                "body":              body,
                "variant_a":         a["sign"],
                "variant_b":         b["sign"],
                "tropical_longitude": round(float(trop), 4),
                "variant_a_degree":   round(a["degree_within_sign"], 3),
                "variant_b_degree":   round(b["degree_within_sign"], 3),
            })

    for ang in ANGLES_TRACKED:
        a_data = angles.get(ang) or {}
        trop = a_data.get("tropical_longitude")
        if trop is None and a_data.get("longitude") is not None:
            # Reconstruct tropical from sidereal (SVP = 31.2836).
            trop = (float(a_data["longitude"]) + 31.2836) % 360.0
        if trop is None:
            continue
        a = attribute_sign_midpoint13_variant_a(trop)
        b = attribute_sign_midpoint12_variant_b(trop)
        if a["sign"] == OPHIUCHUS_SIGN_NAME:
            ophiuchus_bodies.append(ang.upper())
        if a["sign"] != b["sign"]:
            angle_changes.append({
                "angle":              ang,
                "variant_a":          a["sign"],
                "variant_b":          b["sign"],
                "tropical_longitude": round(float(trop), 4),
            })

    return {
        "body_changes":      body_changes,
        "angle_changes":     angle_changes,
        "ophiuchus_bodies":  sorted(set(ophiuchus_bodies)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def run_audit(limit: int = 0) -> Dict[str, Any]:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ.get("DB_NAME", "test_database")]

    started_at = datetime.now(timezone.utc)

    summary: Dict[str, Any] = {
        "marker":                    "variant_a_migration_audit_v1",
        "started_at":                started_at.isoformat(),
        "engine_version_target":     ENGINE_VERSION_VARIANT_A,
        "engine_version_forensic":   ENGINE_VERSION_VARIANT_B,
        "limit":                     limit,
        "dry_run":                   True,
        "writes_performed":          0,
        "users_scanned":             0,
        "users_with_birth_data":     0,
        "users_skipped_no_birth":    0,
        "users_changing_sun":        0,
        "users_changing_moon":       0,
        "users_changing_mercury":    0,
        "users_changing_venus":      0,
        "users_changing_mars":       0,
        "users_changing_asc":        0,
        "users_changing_mc":         0,
        "users_entering_ophiuchus":  0,
        "users_with_ophiuchus_sun":  0,
        "users_with_ophiuchus_moon": 0,
        "ophiuchus_distribution":   {},  # body -> count
        "errors":                    [],
        "sample_changes":            [],  # first 10 users, full delta
    }

    cursor = db.users.find({}, {
        "_id": 1, "name": 1, "email": 1,
        "birth_date": 1, "birth_time": 1, "birth_location": 1,
        "latitude": 1, "longitude": 1,
        "timezone": 1, "timezone_minutes": 1,
    })

    processed = 0
    async for u in cursor:
        summary["users_scanned"] += 1
        if limit and processed >= limit:
            break

        parsed = _parse_user_birth(u)
        if parsed is None:
            summary["users_skipped_no_birth"] += 1
            continue

        summary["users_with_birth_data"] += 1
        processed += 1

        try:
            utc, lat, lon = parsed
            delta = _audit_chart_for_user(utc, lat, lon)
        except Exception as e:  # noqa: BLE001
            summary["errors"].append({
                "user_id": str(u["_id"]),
                "email":   u.get("email"),
                "error":   str(e)[:200],
            })
            continue

        # Per-body delta counters
        for change in delta["body_changes"]:
            key = f"users_changing_{change['body'].lower()}"
            if key in summary:
                summary[key] += 1
        for change in delta["angle_changes"]:
            key = f"users_changing_{change['angle']}"
            if key in summary:
                summary[key] += 1

        # Ophiuchus counters
        if delta["ophiuchus_bodies"]:
            summary["users_entering_ophiuchus"] += 1
            for body in delta["ophiuchus_bodies"]:
                summary["ophiuchus_distribution"][body] = \
                    summary["ophiuchus_distribution"].get(body, 0) + 1
            if "Sun" in delta["ophiuchus_bodies"]:
                summary["users_with_ophiuchus_sun"] += 1
            if "Moon" in delta["ophiuchus_bodies"]:
                summary["users_with_ophiuchus_moon"] += 1

        # Sample first 10 users' full delta
        if len(summary["sample_changes"]) < 10:
            summary["sample_changes"].append({
                "user_id":          str(u["_id"]),
                "name":             u.get("name") or u.get("email"),
                "body_changes":     delta["body_changes"],
                "angle_changes":    delta["angle_changes"],
                "ophiuchus_bodies": delta["ophiuchus_bodies"],
            })

    summary["finished_at"] = datetime.now(timezone.utc).isoformat()

    # Write report to disk
    ts = started_at.strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"variant_a_migration_audit_{ts}.json")
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    summary["report_path"] = report_path

    return summary


def _print_human_summary(s: Dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("VARIANT A MIGRATION AUDIT — REPORT")
    print("=" * 70)
    print(f"Engine target (canonical):   {s['engine_version_target']}")
    print(f"Engine forensic (rollback):  {s['engine_version_forensic']}")
    print(f"Started:                     {s['started_at']}")
    print(f"Finished:                    {s.get('finished_at')}")
    print(f"Report path:                 {s.get('report_path')}")
    print()
    print(f"Users scanned:               {s['users_scanned']}")
    print(f"Users with birth data:       {s['users_with_birth_data']}")
    print(f"Users skipped (no birth):    {s['users_skipped_no_birth']}")
    print()
    print("PER-BODY SIGN CHANGES (Variant A vs Variant B):")
    for body in ("sun", "moon", "mercury", "venus", "mars"):
        key = f"users_changing_{body}"
        print(f"  {body.capitalize():10}: {s.get(key, 0)} users")
    print(f"  ASC       : {s.get('users_changing_asc', 0)} users")
    print(f"  MC        : {s.get('users_changing_mc', 0)} users")
    print()
    print("OPHIUCHUS ENTRIES (any body lands in Ophiuchus under V-A):")
    print(f"  Total users:              {s['users_entering_ophiuchus']}")
    print(f"  Users with Sun=Ophiuchus: {s['users_with_ophiuchus_sun']}")
    print(f"  Users with Moon=Ophiuchus:{s['users_with_ophiuchus_moon']}")
    if s["ophiuchus_distribution"]:
        print("  By body:")
        for body, count in sorted(s["ophiuchus_distribution"].items(),
                                  key=lambda x: -x[1]):
            print(f"    {body:10}: {count}")
    print()
    if s["errors"]:
        print(f"ERRORS ({len(s['errors'])}):")
        for e in s["errors"][:5]:
            print(f"  - {e['email'] or e['user_id']}: {e['error']}")
    print("=" * 70)
    print("READ-ONLY. No DB writes. Awaiting approval before PHASE 5 recompute.")
    print("=" * 70)


async def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit to first N users (0 = all).")
    args = parser.parse_args()

    summary = await run_audit(limit=args.limit)
    _print_human_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
