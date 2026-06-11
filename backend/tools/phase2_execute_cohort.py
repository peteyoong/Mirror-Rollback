"""
Phase 2 — Cohort Migration Executor (Option C).

Iterates the cohort in the user-approved order, applies the same migration
framework that was proven on canonical Pete, snapshots every user, verifies
every chart against an in-memory recompute, and stops at the first failure.

USAGE:
    python tools/phase2_execute_cohort.py             # dry-run
    python tools/phase2_execute_cohort.py --commit    # real run
"""
from __future__ import annotations

import os, sys, asyncio, json, uuid, argparse
from datetime import datetime, timedelta, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz, bson
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone
from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

MATCH_TOL_DEG = 0.01      # post-verify must match in-memory recompute to 0.01°
STOP_ON_ERROR = True

# Borderline-dormant accounts the user approved (Option C)
BORDERLINE_DORMANT = [
    "6a17e8cf5bc5cc688d66eba0",  # Naina (HIGHEST PRIORITY)
    "69aee5a90710b5654c27cd52",  # PeteTeat
    "69c90702497688b97a8e67a1",  # Mel dup
    "6988e993ef78a656df512498",  # Colin Wee
    "698896de8235f34e01f1e359",  # Jakob
    "69894cc932380843ba87d121",  # Jaan
    "6989d6df276be25f3f007264",  # Natt
    "6989d747276be25f3f007265",  # Pat
    "69a7deee2f433b2372665628",  # Aby
    "698029c55b020b708d7198f5",  # Luna#3
]
NAINA = "6a17e8cf5bc5cc688d66eba0"
PETE_CANONICAL = "697f0c6abf35c0528ff06954"

CACHE_COLLECTIONS = [
    "deep_dive_cache", "astrology_timeline_cache", "governing_chapter_cache",
    "lifeline_synthesis_cache", "lunar_synthesis_cache", "pattern_drift_cache",
    "pattern_mirror_cache", "relationship_today_cache", "forum_story_cache",
    "daily_focus", "daily_keystones", "daily_astrology", "daily_pattern_signals",
    "today_patterns", "user_timeline", "mirror_insights",
    "pattern_memory", "pattern_memory_signals",
    "pattern_running_me_v2", "longitudinal_pattern_memory",
    "home_angle_history", "home_history", "home_v6_state",
    "lifeline_events", "lifeline_imported_moments", "lifeline_import_sources",
    "lunar_considerations", "lunar_journal",
]
PRESERVED_COLLECTIONS = [
    "chat_history", "enneagram_chat_history",
    "forum_chat_messages", "forum_mirror_chat_messages",
    "forum_reflections", "user_reflections", "reflections",
    "journal", "facet_history", "user_memory", "user_thread_state",
    "user_engagement_state", "user_recent_actions",
    "home_engagement_sessions", "enneagram_results",
    "saved_people", "forum_members", "forums", "forum_updates",
    "forum_exercises", "forum_relationship_edges",
]


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
        hh = int(t[0]); mm = int(t[1]) if len(t)>1 else 0
    except (ValueError, IndexError): return None
    if is_pm and hh < 12: hh += 12
    if is_am and hh == 12: hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60): return None
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc_iana(local_dt, iana):
    return pytz.timezone(iana).localize(local_dt, is_dst=None).astimezone(dt_tz.utc)


def angle(d, k):
    if not d: return None
    v = (d.get("angles") or {}).get(k) or {}
    return v.get("longitude") or v.get("tropical_longitude")


async def _gather_cache_ids(user_id: str) -> Dict[str, List[Any]]:
    ids = {}
    for coll in CACHE_COLLECTIONS:
        try:
            id_list = [d["_id"] async for d in
                       db[coll].find({"user_id": user_id}, projection={"_id": 1})]
        except Exception:
            id_list = []
        if id_list:
            ids[coll] = id_list
    return ids


async def _preserved_counts(user_id: str) -> Dict[str, int]:
    out = {}
    for coll in PRESERVED_COLLECTIONS:
        try:
            out[coll] = await db[coll].count_documents({"user_id": user_id})
        except Exception:
            out[coll] = -1
    return out


async def migrate_one(user_id: str, batch_id: str, commit: bool) -> Dict[str, Any]:
    """Single-user atomic migration. Returns per-user result row."""
    started = datetime.now(dt_tz.utc)
    u = await db.users.find_one({"_id": bson.ObjectId(user_id)})
    if not u:
        return {"user_id": user_id, "status": "USER_NOT_FOUND"}
    chart_before = await db.charts.find_one({"user_id": user_id})
    bl = u.get("birth_location") or {}
    lat = bl.get("latitude"); lon = bl.get("longitude")
    if lat is None or lon is None:
        return {"user_id": user_id, "status": "NO_COORDS"}
    try:
        iana = resolve_iana_timezone(float(lat), float(lon))
    except Exception:
        iana = None
    if not iana:
        return {"user_id": user_id, "status": "TZ_RESOLVER_FAILED"}
    local_dt = _parse_local(u.get("birth_date"), u.get("birth_time"))
    if not local_dt:
        return {"user_id": user_id, "status": "NO_LOCAL_DT"}
    try:
        corrected_utc = _to_utc_iana(local_dt, iana)
    except Exception as e:
        return {"user_id": user_id, "status": f"TZ_CONV_FAILED:{type(e).__name__}"}

    # In-memory recompute (expected)
    try:
        new_astro = get_full_natal_chart(corrected_utc.replace(tzinfo=None),
                                          float(lat), float(lon))
        new_hd = get_human_design_chart(corrected_utc, float(lat), float(lon))
    except Exception as e:
        return {"user_id": user_id, "status": f"RECOMPUTE_FAILED:{type(e).__name__}: {e}"}
    expected_asc = angle(new_astro, "asc")
    expected_mc = angle(new_astro, "mc")
    if expected_asc is None or expected_mc is None:
        return {"user_id": user_id, "status": "RECOMPUTE_MISSING_ANGLES"}

    # Pre-state for diff
    before_asc = before_mc = None
    if chart_before:
        before_astro = chart_before.get("astrology") or {}
        before_asc = angle(before_astro, "asc")
        before_mc = angle(before_astro, "mc")

    cache_ids = await _gather_cache_ids(user_id)
    cache_total = sum(len(v) for v in cache_ids.values())
    preserved_before = await _preserved_counts(user_id)

    migration_id = str(uuid.uuid4())
    snapshot_doc = {
        "_id": bson.ObjectId(),
        "migration_id": migration_id,
        "batch_id": batch_id,
        "user_id": user_id,
        "classification": "COHORT_OPTION_C",
        "snapshot_at": started,
        "prev_user_doc": u,
        "prev_chart_doc": chart_before,
        "cache_keys": {k: [str(x) if isinstance(x, bson.ObjectId) else x for x in v]
                       for k, v in cache_ids.items()},
        "planned_corrected_tz": iana,
        "planned_utc": corrected_utc.isoformat(),
        "rollback_status": "PENDING",
    }

    if commit:
        await db.users_phase2_rollback.create_index(
            [("migration_id", 1), ("user_id", 1)], unique=True)
        await db.users_phase2_rollback.insert_one(snapshot_doc)

        await db.users.update_one(
            {"_id": u["_id"]},
            {"$set": {
                "timezone": iana,
                "tz_provenance": "phase2_migration_v1",
                "tz_migration_id": migration_id,
                "tz_migrated_at": datetime.now(dt_tz.utc),
                "tz_batch_id": batch_id,
            }})

        new_chart_doc = dict(chart_before) if chart_before else {"user_id": user_id}
        new_chart_doc["astrology"] = new_astro
        new_chart_doc["human_design"] = new_hd
        new_chart_doc["updated_at"] = datetime.now(dt_tz.utc)
        new_chart_doc["debug_stamp"] = {
            **((chart_before or {}).get("debug_stamp") or {}),
            "migration": "phase2_cohort_v1",
            "migration_id": migration_id,
            "batch_id": batch_id,
            "tz_provenance": "phase2_migration_v1",
        }
        await db.charts.replace_one({"user_id": user_id}, new_chart_doc, upsert=True)

        deleted = 0
        for coll, ids in cache_ids.items():
            res = await db[coll].delete_many({"_id": {"$in": ids}})
            deleted += res.deleted_count
    else:
        deleted = 0  # dry-run

    # Verify
    chart_after = await db.charts.find_one({"user_id": user_id}) if commit else None
    verify_chart = chart_after or {"astrology": new_astro}
    got_asc = angle(verify_chart.get("astrology") or {}, "asc")
    got_mc = angle(verify_chart.get("astrology") or {}, "mc")
    asc_delta = abs((got_asc or 0) - expected_asc)
    mc_delta = abs((got_mc or 0) - expected_mc)
    verify_ok = (asc_delta < MATCH_TOL_DEG) and (mc_delta < MATCH_TOL_DEG)

    preserved_after = await _preserved_counts(user_id) if commit else preserved_before
    preserved_ok = all(preserved_after.get(k) == preserved_before.get(k) for k in preserved_before)

    final_status = ("APPLIED" if (commit and verify_ok and preserved_ok)
                    else ("DRY_RUN" if not commit
                          else ("PRESERVATION_FAILED" if not preserved_ok else "VERIFY_FAILED")))
    if commit:
        await db.users_phase2_rollback.update_one(
            {"_id": snapshot_doc["_id"]},
            {"$set": {"rollback_status": final_status,
                      "verification": {
                          "post_chart_asc": got_asc, "post_chart_mc": got_mc,
                          "expected_asc": expected_asc, "expected_mc": expected_mc,
                          "asc_delta_from_expected": asc_delta,
                          "mc_delta_from_expected": mc_delta,
                          "preserved_collections_unchanged": preserved_ok,
                          "cache_rows_deleted": deleted,
                      }}})
    return {
        "user_id": user_id,
        "name": u.get("name"),
        "email": u.get("email"),
        "stored_tz_before": u.get("timezone"),
        "tz_after": iana,
        "corrected_utc": corrected_utc.isoformat(),
        "asc_before": before_asc,
        "asc_after": got_asc,
        "mc_before": before_mc,
        "mc_after": got_mc,
        "asc_delta_from_expected": round(asc_delta, 6),
        "mc_delta_from_expected": round(mc_delta, 6),
        "cache_rows_deleted": deleted if commit else cache_total,
        "preserved_ok": preserved_ok,
        "migration_id": migration_id if commit else None,
        "status": final_status,
    }


def _load_cohort() -> List[str]:
    """Build ordered cohort: Naina → TEST_REFERENCE → rest of borderline dormant."""
    with open("/app/backend/audit_reports/phase2_cohort_classification.json") as f:
        data = json.load(f)
    test_users = [r["user_id"] for r in data["rows"]
                  if r["cohort_class"] == "TEST_REFERENCE"]
    # Borderline dormant from the user-approved set
    borderline_in_db = [uid for uid in BORDERLINE_DORMANT if uid != NAINA]
    # Order: Naina → TEST → borderline-rest
    ordered = [NAINA] + test_users + borderline_in_db
    # Dedup while preserving order, skip Pete (already migrated)
    seen = {PETE_CANONICAL}
    final = []
    for uid in ordered:
        if uid in seen: continue
        seen.add(uid)
        final.append(uid)
    return final


async def amain():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", action="store_true")
    p.add_argument("--limit", type=int, default=None,
                   help="cap migrations (useful for canary)")
    args = p.parse_args()

    cohort = _load_cohort()
    if args.limit:
        cohort = cohort[:args.limit]
    batch_id = str(uuid.uuid4())
    mode = "COMMIT" if args.commit else "DRY-RUN"
    print(f"\n=== Phase 2 Cohort Migration [{mode}]  batch_id={batch_id}  cohort_size={len(cohort)} ===\n")

    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for i, uid in enumerate(cohort, 1):
        try:
            r = await migrate_one(uid, batch_id, commit=args.commit)
        except Exception as e:
            r = {"user_id": uid, "status": f"EXCEPTION:{type(e).__name__}: {e}"}
        ok = r.get("status") in ("APPLIED", "DRY_RUN")
        marker = "✓" if ok else "✗"
        print(f"  [{i:>3}/{len(cohort)}] {marker} {uid}  {r.get('status'):<22} "
              f"{r.get('name') or '—':<24}  "
              f"tz: {r.get('stored_tz_before') or '—':<10} → {r.get('tz_after') or '—'}  "
              f"Δasc={r.get('asc_delta_from_expected', '—')}")
        results.append(r)
        if not ok:
            failures.append(r)
            if STOP_ON_ERROR:
                print(f"\n  STOP_ON_ERROR triggered. Halting cohort migration.")
                break

    # Aggregate
    applied = sum(1 for r in results if r.get("status") == "APPLIED")
    dry_run = sum(1 for r in results if r.get("status") == "DRY_RUN")
    failed = sum(1 for r in results if r.get("status") not in ("APPLIED", "DRY_RUN"))
    total_cache = sum(r.get("cache_rows_deleted") or 0 for r in results)
    verify_pass = sum(1 for r in results if abs(r.get("asc_delta_from_expected", 1.0)) < MATCH_TOL_DEG)
    manual_review = [r for r in results if r.get("status") not in ("APPLIED", "DRY_RUN")]

    report = {
        "report": "PHASE2_COHORT_MIGRATION_REPORT",
        "batch_id": batch_id,
        "mode": mode,
        "started_at": datetime.now(dt_tz.utc).isoformat(),
        "cohort_planned": len(cohort),
        "applied": applied,
        "dry_run": dry_run,
        "skipped": len(cohort) - len(results),
        "failed": failed,
        "verification_pass": verify_pass,
        "verification_pass_rate": (verify_pass / len(results)) if results else 0.0,
        "total_rollback_records": applied,
        "total_cache_rows_invalidated": total_cache,
        "stop_on_error_triggered": failed > 0 and STOP_ON_ERROR,
        "manual_review_users": [r["user_id"] for r in manual_review],
        "results": results,
    }

    audit_dir = Path("/app/backend/audit_reports")
    audit_dir.mkdir(parents=True, exist_ok=True)
    fpath = audit_dir / f"phase2_cohort_{batch_id}.json"
    with open(fpath, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Artifact written: {fpath}")

    if args.commit:
        # Use batch_id as the unique identifier for cohort-level reports
        report_for_db = {**report, "_id": batch_id, "migration_id": batch_id}
        await db.phase2_audit_reports.replace_one(
            {"_id": batch_id}, report_for_db, upsert=True)
        print(f"  Artifact persisted: phase2_audit_reports.{batch_id}")

    print()
    print("=" * 100)
    print("COHORT EXECUTION SUMMARY")
    print("=" * 100)
    print(f"  cohort planned                  : {len(cohort)}")
    print(f"  applied                         : {applied}")
    print(f"  dry-run                         : {dry_run}")
    print(f"  failed                          : {failed}")
    print(f"  skipped (after stop_on_error)   : {len(cohort) - len(results)}")
    print(f"  rollback records created        : {applied}")
    print(f"  cache rows invalidated          : {total_cache:,}")
    print(f"  verification pass rate          : {verify_pass}/{len(results)}  "
          f"({100 * verify_pass / max(1, len(results)):.1f}%)")
    print(f"  manual review required          : {len(manual_review)}")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(amain())
