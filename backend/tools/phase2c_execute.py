"""
Phase 2C — Execution Executor (manifest-driven).

Reads the operator-certified cohort from
`audit_reports/PHASE2C_EXECUTION_MANIFEST.json` and applies the Phase 2A
proven per-user atomic migration sequence with an explicit idempotency
guard against `users_phase2_rollback` `status=VERIFIED`.

The per-user migration logic (`migrate_one`) is imported unchanged from
`phase2_execute_cohort.py` — the only difference is the cohort source and
the idempotency guard.

USAGE
    python tools/phase2c_execute.py             # dry-run (no writes)
    python tools/phase2c_execute.py --commit    # real run

DOES NOT MODIFY: chat_history, journal, forum_*, saved_people,
                 user_memory, user_engagement_state, reflections.
DOES NOT FLIP: INTENT_ROUTER_V2_CUTOVER (must remain false).
"""
from __future__ import annotations

import os, sys, asyncio, json, uuid, argparse
from datetime import datetime, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bson
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Import the proven per-user atomic migration step from Phase 2A executor.
# We deliberately re-use this so the chart-recompute semantics, snapshot
# format, verify tolerance (0.01°), and rollback mechanics are IDENTICAL
# to what was verified on Pete.
from tools.phase2_execute_cohort import (
    migrate_one,
    MATCH_TOL_DEG,
    STOP_ON_ERROR,
    CACHE_COLLECTIONS,
    PRESERVED_COLLECTIONS,
)

load_dotenv()
db = AsyncIOMotorClient(os.environ["MONGO_URL"])[
    os.environ.get("DB_NAME", "test_database")]

MANIFEST_PATH = Path("/app/backend/audit_reports/PHASE2C_EXECUTION_MANIFEST.json")


async def _verified_user_ids() -> set:
    """Return the set of user_ids that already have a VERIFIED rollback
    record (Pete-1 + COHORT_OPTION_C-84 + any post-hoc verifications)."""
    out = set()
    async for d in db.users_phase2_rollback.find(
            {"rollback_status": "VERIFIED"}, {"user_id": 1}):
        out.add(str(d.get("user_id")))
    return out


async def amain():
    p = argparse.ArgumentParser(description="Phase 2C executor.")
    p.add_argument("--commit", action="store_true",
                   help="Real run. Without this flag, dry-run only.")
    p.add_argument("--limit", type=int, default=None,
                   help="Cap migrations (canary helper).")
    args = p.parse_args()

    # ── Pre-execution: load manifest + apply idempotency guard ────────
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 2
    manifest = json.loads(MANIFEST_PATH.read_text())
    manifest_uids: List[str] = [r["user_id"] for r in manifest["rows"]]
    manifest_size = len(manifest_uids)

    verified = await _verified_user_ids()
    excluded = [u for u in manifest_uids if u in verified]
    cohort = [u for u in manifest_uids if u not in verified]
    if args.limit:
        cohort = cohort[:args.limit]

    # ── Stop if any pre-execution count disagrees with certification ──
    expected_cohort = 45
    expected_recompute = 44
    expected_drift = 1
    expected_format = 0
    expected_cache_rows = 10
    actual_recompute = sum(1 for r in manifest["rows"]
                           if r["classification"] == "RECOMPUTE_REQUIRED"
                           and r["user_id"] in cohort)
    actual_drift = sum(1 for r in manifest["rows"]
                       if r["classification"] == "DRIFT_REPAIR"
                       and r["user_id"] in cohort)
    actual_format = sum(1 for r in manifest["rows"]
                        if r["classification"] == "FORMAT_ONLY"
                        and r["user_id"] in cohort)
    actual_cache_rows = sum(r["cache_rows_affected"] for r in manifest["rows"]
                            if r["user_id"] in cohort)

    print("─" * 88)
    print(f"PHASE 2C EXECUTOR  mode={'COMMIT' if args.commit else 'DRY-RUN'}")
    print("─" * 88)
    print(f"  Manifest size                : {manifest_size}")
    print(f"  Already-VERIFIED in rollback : {len(verified)}")
    print(f"  Manifest ∩ VERIFIED          : {len(excluded)}  (excluded by guard)")
    print(f"  Final cohort                 : {len(cohort)}")
    print(f"  RECOMPUTE_REQUIRED           : {actual_recompute}  "
          f"(expected {expected_recompute})")
    print(f"  FORMAT_ONLY                  : {actual_format}  "
          f"(expected {expected_format})")
    print(f"  DRIFT_REPAIR                 : {actual_drift}  "
          f"(expected {expected_drift})")
    print(f"  Projected chart recomputes   : {len(cohort)}")
    print(f"  Projected cache rows         : {actual_cache_rows}  "
          f"(expected {expected_cache_rows})")
    print(f"  Verified rollback records    : {len(verified)}")
    print("─" * 88)

    # Hard-stop guards (per operator instruction).
    drift_or_stop = False
    if len(cohort) != expected_cohort:
        print(f"\n  STOP: cohort size {len(cohort)} != expected {expected_cohort}")
        drift_or_stop = True
    if actual_recompute != expected_recompute:
        print(f"  STOP: RECOMPUTE_REQUIRED {actual_recompute} != {expected_recompute}")
        drift_or_stop = True
    if actual_drift != expected_drift:
        print(f"  STOP: DRIFT_REPAIR {actual_drift} != {expected_drift}")
        drift_or_stop = True
    if actual_format != expected_format:
        print(f"  STOP: FORMAT_ONLY {actual_format} != {expected_format}")
        drift_or_stop = True
    if actual_cache_rows != expected_cache_rows:
        print(f"  STOP: cache rows {actual_cache_rows} != {expected_cache_rows}")
        drift_or_stop = True
    if drift_or_stop and not args.limit:
        print("\n  Pre-execution drift detected. Halting before any writes.")
        return 3

    # ── Per-user execution ───────────────────────────────────────────
    batch_id = str(uuid.uuid4())
    started_at = datetime.now(dt_tz.utc)
    print(f"\n  batch_id   : {batch_id}")
    print(f"  started_at : {started_at.isoformat()}\n")

    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for i, uid in enumerate(cohort, 1):
        try:
            r = await migrate_one(uid, batch_id, commit=args.commit)
        except Exception as e:
            r = {"user_id": uid, "status": f"EXCEPTION:{type(e).__name__}: {e}"}
        ok = r.get("status") in ("APPLIED", "DRY_RUN")
        marker = "✓" if ok else "✗"
        print(f"  [{i:>3}/{len(cohort)}] {marker} {uid}  "
              f"{(r.get('status') or '—'):<22} "
              f"{(r.get('name') or '—')[:22]:<24}  "
              f"tz: {(r.get('stored_tz_before') or '—'):<10} → "
              f"{(r.get('tz_after') or '—'):<22} "
              f"Δasc={r.get('asc_delta_from_expected', '—')}")
        results.append(r)
        if not ok:
            failures.append(r)
            if STOP_ON_ERROR:
                print(f"\n  STOP_ON_ERROR triggered. Halting cohort migration.")
                break

    # ── Aggregate ────────────────────────────────────────────────────
    finished_at = datetime.now(dt_tz.utc)
    applied = sum(1 for r in results if r.get("status") == "APPLIED")
    dry_run = sum(1 for r in results if r.get("status") == "DRY_RUN")
    failed = sum(1 for r in results
                 if r.get("status") not in ("APPLIED", "DRY_RUN"))
    total_cache = sum(r.get("cache_rows_deleted") or 0 for r in results)
    verify_pass = sum(1 for r in results
                      if abs(r.get("asc_delta_from_expected", 1.0)) < MATCH_TOL_DEG)
    rolled_back = sum(1 for r in results
                      if r.get("status") in ("VERIFY_FAILED",
                                              "PRESERVATION_FAILED"))

    report = {
        "report": "PHASE2C_EXECUTION_REPORT",
        "batch_id": batch_id,
        "mode": "COMMIT" if args.commit else "DRY-RUN",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": (finished_at - started_at).total_seconds(),
        "manifest_path": str(MANIFEST_PATH),
        "manifest_size": manifest_size,
        "excluded_by_guard": len(excluded),
        "cohort_planned": len(cohort),
        "users_processed": len(results),
        "users_skipped": len(cohort) - len(results),
        "users_verified": applied,
        "users_dry_run": dry_run,
        "users_failed": failed,
        "users_rolled_back": rolled_back,
        "verification_pass_rate": (verify_pass / len(results)) if results else 0.0,
        "rollback_records_created": applied,
        "cache_rows_deleted": total_cache,
        "manual_review_users": [r["user_id"] for r in failures],
        "preserved_collections": PRESERVED_COLLECTIONS,
        "cache_collections_invalidated": CACHE_COLLECTIONS,
        "stop_on_error_triggered": failed > 0 and STOP_ON_ERROR,
        "intent_router_v2_cutover_state": "false (unchanged)",
        "results": results,
    }
    audit_dir = Path("/app/backend/audit_reports")
    out_path = audit_dir / f"phase2c_execution_{batch_id}.json"
    out_path.write_text(json.dumps(report, indent=2, default=str))
    print(f"\n  Artifact written: {out_path}")

    if args.commit:
        report_for_db = {**report, "_id": batch_id, "migration_id": batch_id}
        await db.phase2_audit_reports.replace_one(
            {"_id": batch_id}, report_for_db, upsert=True)
        print(f"  Artifact persisted: phase2_audit_reports.{batch_id}")

    print()
    print("=" * 88)
    print("PHASE 2C EXECUTION SUMMARY")
    print("=" * 88)
    print(f"  mode                            : {report['mode']}")
    print(f"  users processed                 : {len(results)}")
    print(f"  users verified                  : {applied}")
    print(f"  users dry-run                   : {dry_run}")
    print(f"  users skipped (after stop)      : {len(cohort) - len(results)}")
    print(f"  users failed                    : {failed}")
    print(f"  users rolled back               : {rolled_back}")
    print(f"  rollback records created        : {applied}")
    print(f"  cache rows deleted              : {total_cache:,}")
    print(f"  verification pass rate          : "
          f"{verify_pass}/{len(results)}  "
          f"({100 * verify_pass / max(1, len(results)):.1f}%)")
    print(f"  execution duration              : "
          f"{(finished_at - started_at).total_seconds():.3f}s")
    print(f"  manifest excluded by guard      : {len(excluded)}")
    print(f"  intent_router_v2_cutover_state  : false (unchanged)")
    print("=" * 88)
    return 0 if not failures else 4


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
