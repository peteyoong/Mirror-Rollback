"""
True Sidereal-M Midpoint — Production Migration
================================================
Build marker: true-sidereal-midpoint-production-migration-v1

Re-applies sign attribution to every stored chart using the new
true_sidereal_midpoint mode. PRESERVES:
  - tropical longitudes
  - sidereal longitudes (already SVP-subtracted)
  - JD, UTC, timezone, ephemeris values
  - birth metadata
  - all journals / reflections / unrelated user data

MUTATES ONLY:
  - per-body  sign / degree / formatted
  - per-house sign / degree / formatted (cusps)
  - chart-level zodiac_mode + svp metadata
  - before/after snapshot stored on each chart for reversibility

ALSO INVALIDATES the following caches so they rebuild on next access:
  - today-v4
  - home-insight-v6
  - governing-chapter
  - synthesis-atoms
  - deep-dive
  - timeline

Run:
  cd /app/backend && python -m tests.recompute_true_sidereal_midpoint
  cd /app/backend && python -m tests.recompute_true_sidereal_midpoint --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone as _tz
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DB_NAME", "test_database")
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(str(ROOT / ".env"))

from calculations.sign_attribution import (  # noqa: E402
    attribute_sign_true_sidereal_midpoint,
    DEFAULT_AYANAMSA,
    MIDPOINT_MODEL_NAME,
    MODE_UNIFORM_30,
)

BUILD_MARKER = "true-sidereal-midpoint-production-migration-v1"
ZODIAC_12 = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

CACHE_COLLECTIONS_TO_CLEAR = [
    "today_v4_cache",
    "today_v5_cache",
    "home_insight_v6_cache",
    "governing_chapter_cache",
    "synthesis_atoms_cache",
    "deep_dive_cache",
    "timeline_cache",
    "phase_governor_cache",
    "astrology_today_v4_cache",
    "transit_signals_cache",
]


def _to_tropical(sidereal: float, ayanamsa: float = DEFAULT_AYANAMSA) -> float:
    return (sidereal + ayanamsa) % 360


def _attribute(trop: float) -> Dict[str, Any]:
    r = attribute_sign_true_sidereal_midpoint(trop)
    try:
        idx = ZODIAC_12.index(r["sign"])
    except ValueError:
        idx = 0
    return {
        "sign_index":         idx,
        "sign":               r["sign"],
        "degree":             r["degree_within_sign"],
        "formatted":          f"{int(r['degree_within_sign'])}°{r['sign']}",
        "sign_start_tropical": r["sign_start"],
        "sign_end_tropical":   r["sign_end"],
        "sign_width":         r["sign_width"],
    }


def _migrate_body(body_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Compute new attribution for a body. Returns dict with before/after
    or None if body lacks longitudes."""
    if not isinstance(body_doc, dict):
        return None
    sid = body_doc.get("longitude")
    trop = body_doc.get("tropical_longitude")
    if trop is None and sid is None:
        return None
    if trop is None:
        trop = _to_tropical(sid)
    before_sign = body_doc.get("sign")
    before_deg = body_doc.get("degree")
    new = _attribute(trop)
    # mutate body in place
    body_doc["sign"]      = new["sign"]
    body_doc["degree"]    = new["degree"]
    body_doc["formatted"] = new["formatted"]
    body_doc["sign_index"] = new["sign_index"]
    body_doc["tropical_longitude"] = trop  # ensure stored for forensics
    return {
        "before_sign":   before_sign,
        "before_degree": before_deg,
        "after_sign":    new["sign"],
        "after_degree":  new["degree"],
        "sign_flipped":  before_sign != new["sign"],
    }


async def migrate_chart(db, user_id: str, chart_doc: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    # variant-a-13-sign-migration-v1 guard — never downgrade a chart that
    # has already been migrated to the canonical Variant-A engine. This
    # legacy function uses the 12-sign (Variant-B) attributor and would
    # otherwise silently relabel Ophiuchus placements back to Scorpio.
    if isinstance(chart_doc, dict) and (
        chart_doc.get("astrology_engine_version") == "midpoint13_variant_a_v1"
        and chart_doc.get("migration_marker") == "variant-a-13-sign-migration-v1"
    ):
        return {
            "user_id":            user_id,
            "skipped_variant_a":  True,
            "asc_flipped":        False,
            "mc_flipped":         False,
            "placements_changed": 0,
            "planet_sign_flips":  [],
            "asc_before":         None,
            "asc_after":          None,
            "mc_before":          None,
            "mc_after":           None,
            "sun_before":         None,
            "sun_after":          None,
            "moon_before":        None,
            "moon_after":         None,
        }

    astro = chart_doc.get("astrology") or {}
    angles = astro.get("angles", {}) or {}
    planets = astro.get("planets", {}) or {}
    nodes = astro.get("nodes", {}) or {}
    houses = astro.get("houses", {}) or {}

    result: Dict[str, Any] = {
        "user_id":            user_id,
        "asc_before":         None,
        "asc_after":          None,
        "mc_before":          None,
        "mc_after":           None,
        "sun_before":         None,
        "sun_after":          None,
        "moon_before":        None,
        "moon_after":         None,
        "placements_changed": 0,
        "asc_flipped":        False,
        "mc_flipped":         False,
        "planet_sign_flips":  [],
    }

    # angles (ASC / MC / DC / IC)
    for k in ("asc", "mc", "dc", "ic"):
        if k not in angles:
            continue
        b = angles[k]
        before_sign = b.get("sign")
        before_deg = b.get("degree")
        diff = _migrate_body(b)
        if diff is None:
            continue
        if k == "asc":
            result["asc_before"] = (before_sign, before_deg)
            result["asc_after"] = (b["sign"], b["degree"])
            result["asc_flipped"] = diff["sign_flipped"]
        if k == "mc":
            result["mc_before"] = (before_sign, before_deg)
            result["mc_after"] = (b["sign"], b["degree"])
            result["mc_flipped"] = diff["sign_flipped"]
        if diff["sign_flipped"]:
            result["placements_changed"] += 1

    # planets
    for name, b in planets.items():
        before_sign = b.get("sign") if isinstance(b, dict) else None
        diff = _migrate_body(b)
        if diff is None:
            continue
        if name == "Sun":
            result["sun_before"] = before_sign
            result["sun_after"] = b["sign"]
        if name == "Moon":
            result["moon_before"] = before_sign
            result["moon_after"] = b["sign"]
        if diff["sign_flipped"]:
            result["placements_changed"] += 1
            result["planet_sign_flips"].append({
                "body":   name,
                "before": diff["before_sign"],
                "after":  diff["after_sign"],
            })

    # nodes
    for name, b in nodes.items():
        diff = _migrate_body(b)
        if diff and diff["sign_flipped"]:
            result["placements_changed"] += 1

    # house cusps (stored as sidereal long in 'cusps')
    cusps = houses.get("cusps") if isinstance(houses, dict) else None
    if isinstance(cusps, list) and len(cusps) >= 12:
        new_formatted_cusps: List[str] = []
        new_signs: List[str] = []
        for c in cusps[:12]:
            trop = _to_tropical(float(c))
            a = _attribute(trop)
            new_formatted_cusps.append(f"{int(a['degree'])}°{a['sign']}")
            new_signs.append(a["sign"])
        houses["formatted_cusps"] = new_formatted_cusps
        houses["cusp_signs"]      = new_signs

    # chart-level metadata
    chart_doc.setdefault("astrology", astro)
    astro["zodiac_mode"] = MIDPOINT_MODEL_NAME
    astro["svp"]         = DEFAULT_AYANAMSA
    astro["migration_marker"] = BUILD_MARKER
    astro["migrated_at"] = datetime.now(_tz.utc).isoformat()

    # before/after snapshot (preserved on chart for reversibility / audit)
    chart_doc.setdefault("zodiac_migration_audit", {})
    chart_doc["zodiac_migration_audit"][BUILD_MARKER] = {
        "asc":  {"before": result["asc_before"],  "after": result["asc_after"]},
        "mc":   {"before": result["mc_before"],   "after": result["mc_after"]},
        "sun":  {"before": result["sun_before"],  "after": result["sun_after"]},
        "moon": {"before": result["moon_before"], "after": result["moon_after"]},
        "ran_at": datetime.now(_tz.utc).isoformat(),
        "prior_mode": MODE_UNIFORM_30,
    }

    if not dry_run:
        await db.charts.replace_one({"user_id": user_id}, chart_doc)

    return result


async def clear_caches(db, dry_run: bool) -> Dict[str, int]:
    """Drop sign-derived caches so they rebuild on next request."""
    cleared: Dict[str, int] = {}
    for col in CACHE_COLLECTIONS_TO_CLEAR:
        try:
            n = await db[col].count_documents({})
            if not dry_run and n > 0:
                await db[col].delete_many({})
            cleared[col] = n
        except Exception:
            cleared[col] = -1  # collection didn't exist
    return cleared


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Compute changes but do not write")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of users (0 = all)")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = client[os.environ["DB_NAME"]]

    print(f"[migration] build_marker = {BUILD_MARKER}")
    print(f"[migration] dry_run      = {args.dry_run}")

    cur = db.charts.find({})
    if args.limit:
        cur = cur.limit(args.limit)

    users_processed = 0
    users_changed = 0
    placements_changed_total = 0
    asc_flips = 0
    mc_flips = 0
    planet_flips: List[Dict[str, str]] = []
    errors: List[str] = []
    samples: List[Dict[str, Any]] = []
    spot_check_uids = {
        "697ec826ad4b18f75bf42616": "Mel",
        "6971c81f2b40fd5ef501d375": "Pete",  # uid is the Pete chart per cohort
    }

    async for chart in cur:
        users_processed += 1
        uid = chart.get("user_id")
        if not uid:
            continue
        try:
            r = await migrate_chart(db, uid, chart, args.dry_run)
        except Exception as e:
            errors.append(f"{uid}: {type(e).__name__}: {e}")
            continue
        if r["placements_changed"] > 0:
            users_changed += 1
        placements_changed_total += r["placements_changed"]
        if r["asc_flipped"]:
            asc_flips += 1
        if r["mc_flipped"]:
            mc_flips += 1
        for f in r["planet_sign_flips"]:
            planet_flips.append({"user_id": uid, **f})
        if uid in spot_check_uids:
            samples.append({"label": spot_check_uids[uid], **r})

    caches = await clear_caches(db, args.dry_run)

    # Build report
    report = {
        "build_marker":             BUILD_MARKER,
        "dry_run":                  args.dry_run,
        "users_processed":          users_processed,
        "users_changed":            users_changed,
        "placements_changed":       placements_changed_total,
        "asc_sign_flips":           asc_flips,
        "mc_sign_flips":            mc_flips,
        "planet_sign_flips_count":  len(planet_flips),
        "planet_sign_flip_examples": planet_flips[:25],
        "errors":                   errors,
        "caches_cleared":           caches,
        "spot_check_samples":       samples,
    }

    # Persist report
    if not args.dry_run:
        await db.migration_reports.insert_one({
            "ran_at": datetime.now(_tz.utc).isoformat(),
            **report,
        })

    # Print summary
    print()
    print("=" * 60)
    print(" MIGRATION REPORT")
    print("=" * 60)
    for k, v in report.items():
        if isinstance(v, (list, dict)) and len(str(v)) > 200:
            if isinstance(v, list):
                print(f"  {k}: [{len(v)} items]")
            else:
                print(f"  {k}: {{{len(v)} keys}}")
        else:
            print(f"  {k}: {v}")
    print()
    print("Spot checks:")
    for s in samples:
        print(f"  {s.get('label')} ({s['user_id'][:8]}): "
              f"ASC {s['asc_before']} → {s['asc_after']}  "
              f"MC {s['mc_before']} → {s['mc_after']}  "
              f"Sun {s['sun_before']} → {s['sun_after']}  "
              f"Moon {s['moon_before']} → {s['moon_after']}")


if __name__ == "__main__":
    asyncio.run(main())
