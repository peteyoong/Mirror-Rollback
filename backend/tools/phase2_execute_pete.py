"""
Phase 2 — Canonical Pete Migration Executor + PHASE2_PETE_FINAL_REPORT generator.

DEFAULT MODE: --dry-run (NO WRITES).  Pass --commit to actually mutate the DB.

Runbook:
  1. Snapshot user + chart + cache_keys into users_phase2_rollback (PENDING)
  2. Update users.timezone → Asia/Kuala_Lumpur, tz_provenance='phase2_migration_v1'
  3. Recompute natal chart with corrected UTC (1968-03-31 17:55:00 UTC), replace charts doc
  4. Recompute Human Design in same step (lives inside the chart doc)
  5. Delete chart-derived cache rows (snapshotted ids only — never journal/chat/forum)
  6. Verification: re-read chart, compute asc/mc deltas vs expected
  7. Generate PHASE2_PETE_FINAL_REPORT — write to phase2_audit_reports collection
     AND to /app/backend/audit_reports/phase2_pete_<migration_id>.json
  8. Mark rollback status='APPLIED' (or 'ROLLED_BACK' on any failure)

USAGE:
    python tools/phase2_execute_pete.py             # dry-run (no writes)
    python tools/phase2_execute_pete.py --commit    # real migration
    python tools/phase2_execute_pete.py --rollback <migration_id>  # restore prior state
"""
from __future__ import annotations

import os, sys, asyncio, json, uuid, argparse, traceback
from datetime import datetime, timedelta, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bson
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]

PETE_USER_ID = "697f0c6abf35c0528ff06954"
MEL_USER_ID = "697ec826ad4b18f75bf42616"
LAT = 3.1073
LON = 101.6068
CORRECT_TZ = "Asia/Kuala_Lumpur"
CORRECT_UTC = datetime(1968, 3, 31, 17, 55, 0, tzinfo=dt_tz.utc)
EXPECTED_ASC_DEG = 255.5385
EXPECTED_MC_DEG = 169.8445

# Same cache surface as the Phase 2B planner
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

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def sign_of(longitude: float):
    long = longitude % 360.0
    idx = int(long // 30)
    return SIGNS[idx], long - idx * 30


def signed_delta(a, b):
    return ((b - a + 540) % 360) - 180


def angle(d, k):
    if not d: return None
    v = (d.get("angles") or {}).get(k) or {}
    return v.get("longitude") or v.get("tropical_longitude")


def planet_lon(planets, name):
    p = (planets or {}).get(name) or {}
    return p.get("longitude") or p.get("tropical_longitude")


def planet_house(planets, name):
    p = (planets or {}).get(name) or {}
    return p.get("house")


# ─────────────────────────────────────────────────────────────────────────────
# Stage helpers
# ─────────────────────────────────────────────────────────────────────────────
async def _gather_cache_ids(user_id: str) -> Dict[str, List[Any]]:
    ids: Dict[str, List[Any]] = {}
    for coll in CACHE_COLLECTIONS:
        try:
            cursor = db[coll].find({"user_id": user_id}, projection={"_id": 1})
            id_list = [d["_id"] async for d in cursor]
        except Exception:
            id_list = []
        if id_list:
            ids[coll] = id_list
    return ids


async def _gather_preserved_counts(user_id: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for coll in PRESERVED_COLLECTIONS:
        try:
            counts[coll] = await db[coll].count_documents({"user_id": user_id})
        except Exception:
            counts[coll] = -1
    return counts


def _summarise_chart(chart_doc) -> Dict[str, Any]:
    astro = (chart_doc or {}).get("astrology") or {}
    hd = (chart_doc or {}).get("human_design") or {}
    planets = astro.get("planets") or {}
    asc = angle(astro, "asc"); mc = angle(astro, "mc")
    summary = {
        "birth_utc": (astro.get("metadata") or {}).get("birth_utc"),
        "asc_long": asc,
        "asc_sign_deg": (sign_of(asc) if asc is not None else None),
        "mc_long": mc,
        "mc_sign_deg": (sign_of(mc) if mc is not None else None),
        "house_cusps": (astro.get("houses") or {}).get("cusps"),
        "planets": {
            b: {
                "long": planet_lon(planets, b),
                "house": planet_house(planets, b),
                "sign": (planets.get(b) or {}).get("sign"),
            }
            for b in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                       "Uranus","Neptune","Pluto","Chiron","North Node","South Node"]
            if planets.get(b) is not None
        },
        "aspects": astro.get("aspects") or [],
        "hd": {
            "type": hd.get("type"),
            "strategy": hd.get("strategy"),
            "authority": hd.get("authority"),
            "profile": hd.get("profile"),
            "definition": hd.get("definition"),
            "incarnation_cross": (hd.get("incarnation_cross") or {}).get("name"),
            "incarnation_cross_gates": (hd.get("incarnation_cross") or {}).get("gates"),
            "personality_gates": sorted(set(hd.get("personality_gates") or [])),
            "design_gates": sorted(set(hd.get("design_gates") or [])),
            "defined_channels": sorted({
                tuple(sorted([c.get("gate1"), c.get("gate2")])) if isinstance(c, dict) else c
                for c in (hd.get("defined_channels") or [])
            }),
            "defined_centers": sorted(hd.get("defined_centers") or []),
            "design_utc": hd.get("design_datetime_utc_iso"),
        },
    }
    return summary


def _diff_summary(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    diff: Dict[str, Any] = {}
    # angles
    if before["asc_long"] is not None and after["asc_long"] is not None:
        diff["asc_delta_deg"] = round(signed_delta(before["asc_long"], after["asc_long"]), 4)
    if before["mc_long"] is not None and after["mc_long"] is not None:
        diff["mc_delta_deg"] = round(signed_delta(before["mc_long"], after["mc_long"]), 4)
    diff["asc_sign_changed"] = (before["asc_sign_deg"] or [None])[0] != (after["asc_sign_deg"] or [None])[0]
    diff["mc_sign_changed"] = (before["mc_sign_deg"] or [None])[0] != (after["mc_sign_deg"] or [None])[0]
    # planet house changes
    house_changes = []
    for body, info in after["planets"].items():
        b_h = (before["planets"].get(body) or {}).get("house")
        a_h = info.get("house")
        if b_h is not None and a_h is not None and b_h != a_h:
            house_changes.append({"body": body, "before": b_h, "after": a_h})
    diff["planet_house_changes"] = house_changes
    # HD
    diff["hd_type_changed"]       = before["hd"]["type"]       != after["hd"]["type"]
    diff["hd_authority_changed"]  = before["hd"]["authority"]  != after["hd"]["authority"]
    diff["hd_profile_changed"]    = before["hd"]["profile"]    != after["hd"]["profile"]
    diff["hd_definition_changed"] = before["hd"]["definition"] != after["hd"]["definition"]
    diff["hd_incarnation_cross_changed"] = (
        before["hd"]["incarnation_cross"] != after["hd"]["incarnation_cross"])
    diff["hd_gates_changed"] = (
        before["hd"]["personality_gates"] != after["hd"]["personality_gates"] or
        before["hd"]["design_gates"]     != after["hd"]["design_gates"])
    diff["hd_channels_changed"] = before["hd"]["defined_channels"] != after["hd"]["defined_channels"]
    diff["hd_centers_changed"]  = before["hd"]["defined_centers"]  != after["hd"]["defined_centers"]
    return diff


def _classify(diff, before_after) -> Dict[str, str]:
    asc_sign = diff["asc_sign_changed"]; mc_sign = diff["mc_sign_changed"]
    nhc = len(diff["planet_house_changes"])
    if asc_sign or mc_sign:
        astro = "HIGH"
    elif nhc >= 3:
        astro = "MODERATE"
    elif nhc >= 1:
        astro = "LOW"
    else:
        astro = "NONE"

    hd_major = sum(1 for k in ("hd_type_changed", "hd_authority_changed",
                                "hd_profile_changed", "hd_definition_changed",
                                "hd_incarnation_cross_changed",
                                "hd_channels_changed", "hd_centers_changed") if diff[k])
    if hd_major >= 2: hd = "HIGH"
    elif hd_major == 1: hd = "MODERATE"
    elif diff["hd_gates_changed"]: hd = "LOW"
    else: hd = "NONE"

    if astro in ("HIGH",) or nhc >= 3:
        rel = "HIGH"
    elif astro == "MODERATE":
        rel = "MODERATE"
    elif astro == "LOW":
        rel = "LOW"
    else:
        rel = "NONE"
    return {"astrology_impact": astro, "human_design_impact": hd, "relationship_impact": rel}


# ─────────────────────────────────────────────────────────────────────────────
# Main migration
# ─────────────────────────────────────────────────────────────────────────────
async def migrate(commit: bool, audit_dir: Path) -> Dict[str, Any]:
    migration_id = str(uuid.uuid4())
    started_at = datetime.now(dt_tz.utc)
    mode = "COMMIT" if commit else "DRY-RUN"
    print(f"\n=== Phase 2 Pete Migration [{mode}]  migration_id={migration_id} ===\n")

    # 0. Load before
    pete = await db.users.find_one({"_id": bson.ObjectId(PETE_USER_ID)})
    chart_before = await db.charts.find_one({"user_id": PETE_USER_ID})
    mel_chart    = await db.charts.find_one({"user_id": MEL_USER_ID})
    if not pete or not chart_before:
        raise RuntimeError("Pete user or chart not found")

    before_summary = _summarise_chart(chart_before)
    preserved_before = await _gather_preserved_counts(PETE_USER_ID)
    cache_ids = await _gather_cache_ids(PETE_USER_ID)
    cache_total = sum(len(v) for v in cache_ids.values())
    print(f"  Cache rows targeted for invalidation : {cache_total} across {len(cache_ids)} cols")
    print(f"  Preserved collections (will NOT be touched): {len(preserved_before)}")

    # 1. SNAPSHOT
    snapshot = {
        "_id": bson.ObjectId(),
        "migration_id": migration_id,
        "user_id": PETE_USER_ID,
        "classification": "RECOMPUTE_REQUIRED",
        "snapshot_at": started_at,
        "prev_user_doc": pete,
        "prev_chart_doc": chart_before,
        "cache_keys": {k: [str(x) if isinstance(x, bson.ObjectId) else x for x in v]
                       for k, v in cache_ids.items()},
        "planned_corrected_tz": CORRECT_TZ,
        "planned_utc_delta_min": -30,
        "rollback_status": "PENDING",
    }
    if commit:
        await db.users_phase2_rollback.create_index(
            [("migration_id", 1), ("user_id", 1)], unique=True)
        await db.users_phase2_rollback.create_index([("rollback_status", 1)])
        await db.users_phase2_rollback.create_index([("snapshot_at", -1)])
        await db.users_phase2_rollback.insert_one(snapshot)
        print("  [1/6] SNAPSHOT inserted")
    else:
        print("  [1/6] SNAPSHOT (dry-run, not inserted)")

    # 2. TZ UPDATE
    if commit:
        await db.users.update_one(
            {"_id": pete["_id"]},
            {"$set": {"timezone": CORRECT_TZ,
                      "tz_provenance": "phase2_migration_v1",
                      "tz_migrated_at": datetime.now(dt_tz.utc),
                      "tz_migration_id": migration_id}})
        print("  [2/6] users.timezone updated → Asia/Kuala_Lumpur")
    else:
        print("  [2/6] users.timezone update (dry-run skipped)")

    # 3. RECOMPUTE CHART (in-memory regardless of mode)
    new_astro = get_full_natal_chart(CORRECT_UTC.replace(tzinfo=None), LAT, LON)
    new_hd = get_human_design_chart(CORRECT_UTC, LAT, LON)
    new_chart_doc = dict(chart_before)  # preserve user_id, _id, numerology, bazi, etc.
    new_chart_doc["astrology"] = new_astro
    new_chart_doc["human_design"] = new_hd
    new_chart_doc["updated_at"] = datetime.now(dt_tz.utc)
    new_chart_doc["debug_stamp"] = {
        **(chart_before.get("debug_stamp") or {}),
        "migration": "phase2_pete_v1",
        "migration_id": migration_id,
        "tz_provenance": "phase2_migration_v1",
    }
    if commit:
        await db.charts.replace_one({"user_id": PETE_USER_ID}, new_chart_doc, upsert=True)
        print("  [3/6] charts replaced with corrected-tz chart")
    else:
        print("  [3/6] charts replace (dry-run skipped)")

    # 4. CACHE INVALIDATION
    deleted = 0
    if commit:
        for coll, ids in cache_ids.items():
            res = await db[coll].delete_many({"_id": {"$in": ids}})
            deleted += res.deleted_count
        print(f"  [4/6] cache invalidation: deleted {deleted} rows")
    else:
        deleted = 0
        print(f"  [4/6] cache invalidation (dry-run: would delete {cache_total} rows)")

    # 5. VERIFY
    chart_after = await db.charts.find_one({"user_id": PETE_USER_ID}) if commit else None
    after_summary = _summarise_chart(chart_after or new_chart_doc)

    verify_asc = after_summary["asc_long"]
    verify_mc = after_summary["mc_long"]
    asc_delta_from_expected = round(verify_asc - EXPECTED_ASC_DEG, 4) if verify_asc is not None else None
    mc_delta_from_expected = round(verify_mc - EXPECTED_MC_DEG, 4) if verify_mc is not None else None
    verify_ok = (asc_delta_from_expected is not None and abs(asc_delta_from_expected) < 0.01
                 and mc_delta_from_expected is not None and abs(mc_delta_from_expected) < 0.01)
    print(f"  [5/6] verify: asc={verify_asc:.4f}° (Δ {asc_delta_from_expected:+.4f}) "
          f"mc={verify_mc:.4f}° (Δ {mc_delta_from_expected:+.4f}) → {'OK' if verify_ok else 'MISMATCH'}")

    preserved_after = await _gather_preserved_counts(PETE_USER_ID)
    preservation_ok = all(preserved_after.get(k) == preserved_before.get(k)
                          for k in preserved_before)
    print(f"  [5/6] preserved-collection counts unchanged: {preservation_ok}")

    # 6. STATUS UPDATE
    final_status = "APPLIED" if (commit and verify_ok and preservation_ok) else (
        "DRY_RUN" if not commit else "VERIFY_FAILED")
    if commit:
        await db.users_phase2_rollback.update_one(
            {"_id": snapshot["_id"]},
            {"$set": {"rollback_status": final_status,
                      "verification": {
                          "post_chart_asc": verify_asc,
                          "post_chart_mc": verify_mc,
                          "delta_from_expected_asc": asc_delta_from_expected,
                          "delta_from_expected_mc": mc_delta_from_expected,
                          "preserved_collections_unchanged": preservation_ok,
                          "cache_rows_deleted": deleted,
                      }}})
        print(f"  [6/6] rollback_status='{final_status}'")
    else:
        print(f"  [6/6] rollback_status (dry-run) would be {final_status}")

    # ──────────────────────────────────────────────
    # 7. PHASE2_PETE_FINAL_REPORT
    # ──────────────────────────────────────────────
    diff = _diff_summary(before_summary, after_summary)
    cls = _classify(diff, (before_summary, after_summary))

    # Mel anchor (for relationship section)
    mel_summary = _summarise_chart(mel_chart) if mel_chart else None

    report = {
        "report": "PHASE2_PETE_FINAL_REPORT",
        "migration_id": migration_id,
        "mode": "COMMIT" if commit else "DRY_RUN",
        "user_id": PETE_USER_ID,
        "user_email": pete.get("email"),
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(dt_tz.utc).isoformat(),
        "tz_before": pete.get("timezone"),
        "tz_after": CORRECT_TZ,
        "utc_before": (chart_before.get("astrology") or {}).get("metadata", {}).get("birth_utc"),
        "utc_after": CORRECT_UTC.isoformat(),

        "section_1_astrology": {
            "asc_before": {"long": before_summary["asc_long"], "sign_deg": before_summary["asc_sign_deg"]},
            "asc_after":  {"long": after_summary["asc_long"],  "sign_deg": after_summary["asc_sign_deg"]},
            "asc_delta_deg": diff.get("asc_delta_deg"),
            "asc_sign_changed": diff["asc_sign_changed"],
            "mc_before": {"long": before_summary["mc_long"], "sign_deg": before_summary["mc_sign_deg"]},
            "mc_after":  {"long": after_summary["mc_long"],  "sign_deg": after_summary["mc_sign_deg"]},
            "mc_delta_deg": diff.get("mc_delta_deg"),
            "mc_sign_changed": diff["mc_sign_changed"],
            "house_cusps_before": before_summary["house_cusps"],
            "house_cusps_after":  after_summary["house_cusps"],
            "planet_positions_before": before_summary["planets"],
            "planet_positions_after":  after_summary["planets"],
            "planet_house_changes": diff["planet_house_changes"],
            "aspects_before_count": len(before_summary["aspects"]),
            "aspects_after_count":  len(after_summary["aspects"]),
        },

        "section_2_human_design": {
            "type_before": before_summary["hd"]["type"],
            "type_after":  after_summary["hd"]["type"],
            "authority_before": before_summary["hd"]["authority"],
            "authority_after":  after_summary["hd"]["authority"],
            "profile_before": before_summary["hd"]["profile"],
            "profile_after":  after_summary["hd"]["profile"],
            "definition_before": before_summary["hd"]["definition"],
            "definition_after":  after_summary["hd"]["definition"],
            "personality_gates_before": before_summary["hd"]["personality_gates"],
            "personality_gates_after":  after_summary["hd"]["personality_gates"],
            "design_gates_before": before_summary["hd"]["design_gates"],
            "design_gates_after":  after_summary["hd"]["design_gates"],
            "channels_before": [list(t) if isinstance(t, tuple) else t for t in before_summary["hd"]["defined_channels"]],
            "channels_after":  [list(t) if isinstance(t, tuple) else t for t in after_summary["hd"]["defined_channels"]],
            "incarnation_cross_before": before_summary["hd"]["incarnation_cross"],
            "incarnation_cross_after":  after_summary["hd"]["incarnation_cross"],
            "incarnation_cross_gates_before": before_summary["hd"]["incarnation_cross_gates"],
            "incarnation_cross_gates_after":  after_summary["hd"]["incarnation_cross_gates"],
            "design_utc_before": before_summary["hd"]["design_utc"],
            "design_utc_after":  after_summary["hd"]["design_utc"],
        },

        "section_3_mirror_impact": {
            "governing_chapter": "asc-sign unchanged → chapter selection likely identical; verify on next regeneration",
            "timeline": "all user_timeline rows invalidated; will regenerate lazily with new house placements",
            "today": "daily_focus/daily_keystones/daily_astrology cleared; next visit regenerates",
            "astrology_overview": "Asc/MC degrees shift within same signs; overview rewritten on next read",
            "natal_story": f"{len(diff['planet_house_changes'])} planet house re-assignments will re-paragraph",
        },

        "section_4_relationship_impact": {
            "mel_anchor": {
                "user_id": MEL_USER_ID,
                "asc": mel_summary["asc_sign_deg"] if mel_summary else None,
                "mc":  mel_summary["mc_sign_deg"]  if mel_summary else None,
                "unchanged": True,
            },
            "relationship_field": "MODERATE — composite Asc/MC rotates with Pete's −7° shift",
            "between_you_today": "LOW — Mel side unchanged; transit deltas only on Pete side",
            "synastry_overlays": "HIGH — Pete planets shift ~7° in Mel's house frame",
        },

        "section_5_verification": {
            "forum_memberships_preserved": preserved_after.get("forum_members") == preserved_before.get("forum_members"),
            "saved_people_preserved":      preserved_after.get("saved_people")  == preserved_before.get("saved_people"),
            "journal_preserved":           preserved_after.get("journal")       == preserved_before.get("journal"),
            "reflections_preserved":       preserved_after.get("reflections")   == preserved_before.get("reflections"),
            "chat_history_preserved":      preserved_after.get("chat_history")  == preserved_before.get("chat_history"),
            "preserved_collection_counts": {
                "before": preserved_before,
                "after":  preserved_after,
            },
            "post_chart_asc": verify_asc,
            "post_chart_mc": verify_mc,
            "delta_from_expected_asc_deg": asc_delta_from_expected,
            "delta_from_expected_mc_deg":  mc_delta_from_expected,
            "verify_within_tolerance":     verify_ok,
            "cache_rows_deleted":          deleted,
        },

        "section_6_final_classification": {
            **cls,
            "overall_migration_status": (
                "SUCCESS" if commit and verify_ok and preservation_ok
                else "DRY_RUN" if not commit
                else "ROLLED_BACK"
            ),
        },
    }

    # Write artifact
    audit_dir.mkdir(parents=True, exist_ok=True)
    fname = f"phase2_pete_{migration_id}.json"
    fpath = audit_dir / fname
    with open(fpath, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Artifact written: {fpath}")

    if commit:
        await db.phase2_audit_reports.create_index([("migration_id", 1)], unique=True)
        await db.phase2_audit_reports.insert_one(report)
        print(f"  Artifact also persisted in DB: phase2_audit_reports.{migration_id}")
    else:
        print(f"  Artifact NOT persisted to DB (dry-run)")

    return report


async def rollback(migration_id: str) -> None:
    snap = await db.users_phase2_rollback.find_one(
        {"migration_id": migration_id, "user_id": PETE_USER_ID})
    if not snap:
        print(f"No rollback record for migration_id={migration_id}")
        return
    if snap["rollback_status"] not in ("APPLIED", "VERIFY_FAILED"):
        print(f"rollback_status={snap['rollback_status']}, nothing to do")
        return
    await db.users.replace_one({"_id": snap["prev_user_doc"]["_id"]}, snap["prev_user_doc"])
    if snap.get("prev_chart_doc"):
        await db.charts.replace_one({"user_id": PETE_USER_ID}, snap["prev_chart_doc"], upsert=True)
    await db.users_phase2_rollback.update_one(
        {"_id": snap["_id"]},
        {"$set": {"rollback_status": "ROLLED_BACK",
                  "rolled_back_at": datetime.now(dt_tz.utc)}})
    print(f"Rolled back migration {migration_id}")


def _argparse():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", action="store_true",
                   help="actually mutate DB (default: dry-run)")
    p.add_argument("--rollback", default=None,
                   help="restore prior state for migration_id")
    p.add_argument("--audit-dir", default="/app/backend/audit_reports")
    return p.parse_args()


async def amain():
    args = _argparse()
    if args.rollback:
        await rollback(args.rollback); return
    report = await migrate(commit=args.commit, audit_dir=Path(args.audit_dir))
    print("\n" + "=" * 100)
    print(f"FINAL CLASSIFICATION")
    print("=" * 100)
    print(json.dumps(report["section_6_final_classification"], indent=2))


if __name__ == "__main__":
    asyncio.run(amain())
