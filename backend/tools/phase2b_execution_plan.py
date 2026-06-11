"""
Phase 2B — Execution Plan Generator (READ-ONLY).

Builds the exact migration cohort, rollback footprint, cache-invalidation
surface, and write sequence for the upcoming Phase 2 timezone migration.

NO snapshots created. NO writes. NO recomputes. NO cache invalidations.
"""
from __future__ import annotations

import os, sys, asyncio, json, bson
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.timezone_resolver import resolve_iana_timezone

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

UTC_TOL_MIN = 1

# Drift-repair singleton from Phase 2 Readiness Gate § 7
DRIFT_REPAIR_USERS = ["6971cc4381beab3a8955b256"]

# ------------------------------------------------------------------
# Cache surface — collections that store CHART-DERIVED state and must
# be invalidated when a chart is recomputed.  Conversation logs are
# intentionally NOT invalidated (history must be preserved).
# ------------------------------------------------------------------
CACHE_COLLECTIONS_USER_ID = [
    # Astrology / chart-derived caches keyed by user_id
    "deep_dive_cache",
    "astrology_timeline_cache",
    "governing_chapter_cache",
    "lifeline_synthesis_cache",
    "lunar_synthesis_cache",
    "pattern_drift_cache",
    "pattern_mirror_cache",
    "relationship_today_cache",
    "forum_story_cache",
    # Derived daily / pattern outputs
    "daily_focus",
    "daily_keystones",
    "daily_astrology",
    "daily_pattern_signals",
    "today_patterns",
    # Timeline + insight derivations
    "user_timeline",
    "mirror_insights",
    "pattern_memory",
    "pattern_memory_signals",
    "pattern_running_me_v2",
    "longitudinal_pattern_memory",
    "home_angle_history",
    "home_history",
    "home_v6_state",
    "lifeline_events",
    "lifeline_imported_moments",
    "lifeline_import_sources",
    "lunar_considerations",
    "lunar_journal",
]
# Conversation/state collections to PRESERVE (NOT invalidated)
CONVERSATION_PRESERVE = [
    "chat_history", "enneagram_chat_history",
    "forum_chat_messages", "forum_mirror_chat_messages",
    "forum_reflections", "user_reflections", "reflections",
    "journal", "facet_history", "user_memory", "user_thread_state",
    "user_engagement_state", "user_recent_actions",
    "home_engagement_sessions", "enneagram_results",
    "saved_people", "forum_members", "forums", "forum_updates",
    "forum_exercises", "forum_relationship_edges", "forum_topology"
    if False else "forum_relationship_edges",
]


def _parse_local(birth_date, birth_time):
    if not birth_date or not birth_time:
        return None
    if isinstance(birth_date, datetime):
        d = birth_date
    else:
        s = str(birth_date).split(" ")[0].split("T")[0]
        try:
            d = datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None
    bt = str(birth_time).strip().lower()
    is_pm = "pm" in bt
    is_am = "am" in bt
    t = bt.replace("am", "").replace("pm", "").strip().split(":")
    try:
        hh = int(t[0]); mm = int(t[1]) if len(t) > 1 else 0
    except (ValueError, IndexError):
        return None
    if is_pm and hh < 12:
        hh += 12
    if is_am and hh == 12:
        hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None
    return datetime(d.year, d.month, d.day, hh, mm)


def _to_utc(local_dt, tz_str):
    if not local_dt or not tz_str:
        return None
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


def _classify_p18(stored_tz, lat, lon, local_dt) -> Dict[str, Any]:
    if lat is None or lon is None:
        return {"phase18": "UNKNOWN", "reason": "no_coords"}
    if not stored_tz:
        return {"phase18": "UNKNOWN", "reason": "no_stored_tz"}
    if not local_dt:
        return {"phase18": "UNKNOWN", "reason": "no_local_dt"}
    try:
        iana = resolve_iana_timezone(float(lat), float(lon))
    except Exception:
        iana = None
    if not iana:
        return {"phase18": "UNKNOWN", "reason": "resolver_failed"}
    su = _to_utc(local_dt, str(stored_tz))
    cu = _to_utc(local_dt, iana)
    if not su or not cu:
        return {"phase18": "UNKNOWN", "reason": "utc_conv_failed"}
    dmin = (cu - su).total_seconds() / 60.0
    if str(stored_tz) == iana and abs(dmin) <= UTC_TOL_MIN:
        bucket = "SAFE"
    elif abs(dmin) <= UTC_TOL_MIN:
        bucket = "FORMAT_ONLY"
    else:
        bucket = "RECOMPUTE_REQUIRED"
    return {
        "phase18": bucket,
        "resolved_iana": iana,
        "utc_delta_min": round(dmin, 2),
    }


def _bson_size(doc) -> int:
    if doc is None:
        return 0
    try:
        return len(bson.BSON.encode(doc))
    except Exception:
        return -1


async def main():
    # ------------------------------------------------
    # Step 1 — build cohort
    # ------------------------------------------------
    cohort: List[Dict[str, Any]] = []
    drift_set = set(DRIFT_REPAIR_USERS)
    cohort_user_ids: List[str] = []

    cursor = db.users.find({})
    async for u in cursor:
        uid = str(u["_id"])
        bl = u.get("birth_location") or {}
        lat = bl.get("latitude"); lon = bl.get("longitude")
        stored_tz = u.get("timezone")
        local_dt = _parse_local(u.get("birth_date"), u.get("birth_time"))
        cls = _classify_p18(stored_tz, lat, lon, local_dt)

        include = False
        reason = None
        if cls["phase18"] == "RECOMPUTE_REQUIRED":
            include = True; reason = "RECOMPUTE_REQUIRED"
        elif cls["phase18"] == "FORMAT_ONLY":
            include = True; reason = "FORMAT_ONLY"
        elif uid in drift_set:
            include = True; reason = "DRIFT_REPAIR"

        if not include:
            continue

        chart = await db.charts.find_one({"user_id": uid})
        user_doc_size = _bson_size(u)
        chart_doc_size = _bson_size(chart)

        # Per-user cache footprint
        cache_hits: Dict[str, int] = {}
        for coll in CACHE_COLLECTIONS_USER_ID:
            try:
                c = await db[coll].count_documents({"user_id": uid})
            except Exception:
                c = 0
            if c:
                cache_hits[coll] = c

        rollback_size = user_doc_size + chart_doc_size

        cohort.append({
            "user_id": uid,
            "name": u.get("name"),
            "email": u.get("email"),
            "stored_tz": stored_tz,
            "corrected_tz": cls.get("resolved_iana"),
            "utc_delta_min": cls.get("utc_delta_min"),
            "classification": reason,
            "user_doc_bytes": user_doc_size,
            "chart_doc_bytes": chart_doc_size,
            "rollback_bytes": rollback_size,
            "cache_hits": cache_hits,
        })
        cohort_user_ids.append(uid)

    cohort.sort(key=lambda r: (r["classification"], -(abs(r.get("utc_delta_min") or 0))))

    # ------------------------------------------------
    # Aggregate counters
    # ------------------------------------------------
    n_rec = sum(1 for r in cohort if r["classification"] == "RECOMPUTE_REQUIRED")
    n_fmt = sum(1 for r in cohort if r["classification"] == "FORMAT_ONLY")
    n_drift = sum(1 for r in cohort if r["classification"] == "DRIFT_REPAIR")
    total_rollback_bytes = sum(r["rollback_bytes"] for r in cohort)
    cache_totals: Dict[str, int] = {}
    for r in cohort:
        for k, v in r["cache_hits"].items():
            cache_totals[k] = cache_totals.get(k, 0) + v
    total_cache_invalidations = sum(cache_totals.values())

    # Write counters
    snapshots_writes = len(cohort)           # 1 rollback doc per user
    user_updates = sum(1 for r in cohort
                       if r["classification"] in ("RECOMPUTE_REQUIRED", "FORMAT_ONLY"))
    chart_updates = len(cohort)              # all cohort users recompute
    cache_deletes = total_cache_invalidations

    # ------------------------------------------------
    # PRINT REPORT
    # ------------------------------------------------
    bar = "=" * 88
    print(bar)
    print("PHASE 2B — EXECUTION PLAN (READ-ONLY) — NO WRITES PERFORMED")
    print(bar)
    print(f"DB                 : {os.environ.get('DB_NAME','test_database')}")
    print(f"Cohort size        : {len(cohort)}")
    print(f"  RECOMPUTE_REQUIRED : {n_rec}")
    print(f"  FORMAT_ONLY        : {n_fmt}")
    print(f"  DRIFT_REPAIR       : {n_drift}")
    print(f"Rollback footprint : {total_rollback_bytes:,} bytes "
          f"(~{total_rollback_bytes / 1024:.1f} KiB)")
    print(f"Total cache rows   : {total_cache_invalidations:,} across "
          f"{len(cache_totals)} collections")
    print()

    # § 3 per-user table
    print("─── 3. Per-user cohort table ────────────────────────────────────────────────────────")
    print(f"{'user_id':<26}{'name':<22}{'stored_tz':<14}{'corrected_tz':<22}"
          f"{'class':<20}{'rollback_B':>12}{'cache#':>8}")
    for r in cohort:
        print(f"{r['user_id']:<26}"
              f"{(str(r.get('name') or '')[:20]):<22}"
              f"{(str(r.get('stored_tz') or '')[:12]):<14}"
              f"{(str(r.get('corrected_tz') or '')[:20]):<22}"
              f"{r['classification']:<20}"
              f"{r['rollback_bytes']:>12,}"
              f"{sum(r['cache_hits'].values()):>8}")
    print()

    # § 4 rollback schema
    print("─── 4. Rollback Collection Schema  (collection: `users_phase2_rollback`) ────────────")
    schema = {
        "_id": "ObjectId (auto)",
        "migration_id": "string — UUID for the entire Phase 2 run",
        "user_id": "string — users._id",
        "classification": "RECOMPUTE_REQUIRED | FORMAT_ONLY | DRIFT_REPAIR",
        "snapshot_at": "ISODate — UTC instant snapshot was taken",
        "prev_user_doc": "object — full copy of users.{_id=user_id} before update",
        "prev_chart_doc": "object | null — full copy of charts.{user_id} before update",
        "cache_keys": {
            "<collection_name>": "array of _id strings about to be deleted"
        },
        "planned_corrected_tz": "string — target IANA timezone",
        "planned_utc_delta_min": "number — minutes shift applied to UTC",
        "rollback_status": "PENDING | APPLIED | ROLLED_BACK | VERIFIED",
        "verification": {
            "post_chart_asc": "number",
            "post_chart_mc": "number",
            "delta_from_expected_deg": "number",
        }
    }
    print(json.dumps(schema, indent=2))
    print()
    print("Indexes required:")
    print("  • { migration_id: 1, user_id: 1 } unique")
    print("  • { rollback_status: 1 }")
    print("  • { snapshot_at: -1 }")
    print()

    # § 5 cache invalidation list
    print("─── 5. Cache Invalidation List (per collection, total rows) ─────────────────────────")
    print(f"{'collection':<38}{'rows_to_delete':>16}")
    for k, v in sorted(cache_totals.items(), key=lambda kv: -kv[1]):
        print(f"{k:<38}{v:>16,}")
    print(f"{'TOTAL':<38}{total_cache_invalidations:>16,}")
    print()
    print("Conversation/state collections explicitly PRESERVED (no delete):")
    for c in CONVERSATION_PRESERVE:
        print(f"  • {c}")
    print()

    # § 6 write sequence
    print("─── 6. Write Sequence (per user, atomic block) ──────────────────────────────────────")
    sequence = [
        ("1. SNAPSHOT",     "Insert users_phase2_rollback doc with prev_user_doc + prev_chart_doc + cache_keys + rollback_status='PENDING'"),
        ("2. TZ UPDATE",    "db.users.update_one({_id}, {$set: {timezone: corrected_tz, tz_provenance: 'phase2_migration_v1'}})"),
        ("3. RECOMPUTE",    "Compute new UTC = local_dt converted via corrected_tz; call get_full_natal_chart(); db.charts.replace_one({user_id}, new_chart_doc, upsert=True)"),
        ("4. CACHE INVAL.", "For each cache_keys entry: db[<coll>].delete_many({_id: {$in: cache_keys[coll]}})"),
        ("5. VERIFY",       "Re-read chart, store asc/mc into rollback.verification, set rollback_status='APPLIED'"),
        ("6. FAILURE",      "Any step 2-5 exception ⇒ restore prev_user_doc + prev_chart_doc; mark rollback_status='ROLLED_BACK'; abort batch."),
    ]
    for label, body in sequence:
        print(f"  {label:<18}{body}")
    print()

    # § 7 estimates
    print("─── 7. Estimates ─────────────────────────────────────────────────────────────────────")
    # Estimate runtime: chart recompute ≈ 200ms on this engine; mongo ops ≈ 5ms each
    chart_ms = 200
    mongo_ms = 5
    per_user_ms = (
        chart_ms +              # recompute
        mongo_ms * 5 +          # snapshot + user update + chart upsert + verify read + status update
        mongo_ms * len(cache_totals)  # cache delete_many calls (one per collection that has rows)
    )
    runtime_total_ms = per_user_ms * len(cohort)
    print(f"  Snapshot inserts            : {snapshots_writes}")
    print(f"  User.timezone updates       : {user_updates}")
    print(f"  Chart upserts (recomputes)  : {chart_updates}")
    print(f"  Cache rows deleted          : {cache_deletes:,}")
    print(f"  Total mongo write ops       : {snapshots_writes + user_updates + chart_updates + cache_deletes:,}")
    print(f"  Estimated chart recomputes  : {chart_updates}")
    print(f"  Estimated wall-clock        : "
          f"{runtime_total_ms/1000:.1f}s (sequential) | "
          f"{runtime_total_ms/5000:.1f}s (5-worker pool)")
    print(f"  Rollback footprint          : {total_rollback_bytes/1024:.1f} KiB")
    print()
    print("  Failure-recovery procedure :")
    print("    a) Per-user atomic rollback: restore prev_user_doc + prev_chart_doc from")
    print("       users_phase2_rollback; mark rollback_status='ROLLED_BACK'.")
    print("    b) Batch-wide rollback: iterate users_phase2_rollback where status='APPLIED'")
    print("       and replay step (a) for each.  Caches will repopulate lazily on next read.")
    print("    c) Re-running the migration is idempotent because snapshot insert is the")
    print("       first op; existing rollback rows trigger 'already migrated, skipping'.")
    print()

    # § 8 GO / NO-GO
    print("─── 8. GO / NO-GO ───────────────────────────────────────────────────────────────────")
    blockers: List[str] = []
    soft: List[str] = []
    if not all(r.get("corrected_tz") for r in cohort if r["classification"] != "DRIFT_REPAIR"):
        blockers.append("at least one cohort user has no resolvable IANA timezone")
    if any(r["chart_doc_bytes"] <= 0 and r["classification"] != "DRIFT_REPAIR" for r in cohort):
        soft.append("some cohort users have no stored chart yet — recompute will create one")

    if blockers:
        verdict = "NO GO"
    elif soft:
        verdict = "CONDITIONAL GO"
    else:
        verdict = "GO"
    print(f"  VERDICT: {verdict}")
    if blockers:
        print("  BLOCKERS:")
        for b in blockers:
            print(f"    • {b}")
    if soft:
        print("  SOFT CAVEATS:")
        for s in soft:
            print(f"    • {s}")
    print()

    summary = {
        "write_count": 0,
        "charts_updated": 0,
        "migrations_triggered": False,
        "phase": "2B-plan",
        "cohort_size": len(cohort),
        "recompute_required": n_rec,
        "format_only": n_fmt,
        "drift_repair": n_drift,
        "planned_snapshot_inserts": snapshots_writes,
        "planned_user_updates": user_updates,
        "planned_chart_upserts": chart_updates,
        "planned_cache_deletes": cache_deletes,
        "rollback_total_bytes": total_rollback_bytes,
        "estimated_runtime_seconds_sequential": runtime_total_ms / 1000,
        "verdict": verdict,
    }
    print(bar)
    print(json.dumps(summary, indent=2))
    print(bar)


if __name__ == "__main__":
    asyncio.run(main())
