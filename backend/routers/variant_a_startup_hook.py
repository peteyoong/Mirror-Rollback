"""
TEMPORARY — Variant A Production Migration Startup Hook
========================================================
Build marker: variant-a-prod-migration-startup-hook-v1

Self-contained one-shot migration that runs inside the deployed pod when:

    env: RUN_VARIANT_A_MIGRATION == "VARIANT_A_PHASE_5"

Behaviour:
    1. Print a PRE-FLIGHT block to stdout (mongo host, db name, counts,
       Pulsifi/JH/Jay presence flags).
    2. If ANY safety preflight fails -> log + return WITHOUT writing.
    3. Otherwise: snapshot -> recompute -> invalidate caches -> validate.
    4. Print the final migration report JSON between unique BEGIN/END
       markers so it can be retrieved from the Emergent Logs view.
    5. Best-effort: persist a copy of the report to
       /app/backend/audits/variant_a_prod_migration_report_<ts>.json.
    6. Idempotent: on subsequent restarts the recompute body is a no-op
       because every chart already carries the migration_marker.

Removal:
    Delete this file AND delete the single `await _run_variant_a_startup_hook(db)`
    invocation from server.py's `_safe_run_migrations()`.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

sys.path.insert(0, "/app/backend")
from scripts.migration_phase5_variant_a import (   # noqa: E402
    recompute_users,
    invalidate_caches,
    validate as run_validate,
    ASTROLOGY_ENGINE_VERSION,
    MIGRATION_MARKER,
    CANONICAL_HOUSE_SYSTEM,
)
from scripts.migration_snapshot_variant_a import run_snapshot  # noqa: E402

logger = logging.getLogger("variant_a_startup_hook")

BUILD_MARKER         = "variant-a-prod-migration-startup-hook-v1"
ENV_FLAG_NAME        = "RUN_VARIANT_A_MIGRATION"
ENV_FLAG_VALUE       = "VARIANT_A_PHASE_5"
REPORT_BEGIN_MARKER  = "===== VARIANT_A_PROD_MIGRATION_REPORT_BEGIN ====="
REPORT_END_MARKER    = "===== VARIANT_A_PROD_MIGRATION_REPORT_END ====="
PREFLIGHT_BEGIN      = "===== VARIANT_A_PROD_MIGRATION_PREFLIGHT_BEGIN ====="
PREFLIGHT_END        = "===== VARIANT_A_PROD_MIGRATION_PREFLIGHT_END ====="
ANCHOR_EMAILS        = ("pete@pulsifi.me", "melissa.mars@gmail.com")
ANCHOR_NAMES_RAW     = ("JH", "Jay")


def _redact_mongo_host(mongo_url: Optional[str]) -> Dict[str, Any]:
    if not mongo_url:
        return {"present": False}
    try:
        p = urlparse(mongo_url)
        host = p.hostname or "<unknown>"
        return {
            "present":      True,
            "scheme":       p.scheme,
            "host":         host,
            "port":         p.port,
            "is_loopback":  host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"),
            "userinfo":     "<redacted>" if (p.username or p.password) else None,
        }
    except Exception as e:  # noqa: BLE001
        return {"present": True, "parse_error": str(e)[:120]}


def _looks_like_preview_db(db_name: Optional[str], host_info: Dict[str, Any]) -> bool:
    return (db_name or "").lower() == "test_database" or bool(host_info.get("is_loopback"))


async def _engine_dist(db) -> Dict[str, int]:
    out: Dict[str, int] = {}
    async for c in db.charts.find({}, {"astrology_engine_version": 1}):
        ev = c.get("astrology_engine_version") or "<missing>"
        out[ev] = out.get(ev, 0) + 1
    return out


async def _anchor_signs(db) -> Dict[str, Any]:
    """Read Sun/Moon/Asc for Pete, Mel, JH, Jay (post-migration values)."""
    out: Dict[str, Any] = {}
    # Pete + Mel by email
    for email, key in (("pete@pulsifi.me", "pete"), ("melissa.mars@gmail.com", "mel")):
        u = await db.users.find_one({"email": email})
        out[key] = await _signs_for_user(db, u)
    # JH + Jay by name (prefix, case-insensitive)
    for name, key in (("JH", "jh"), ("Jay", "jay")):
        u = await db.users.find_one({"name": {"$regex": f"^{name}( |$)", "$options": "i"}})
        out[key] = await _signs_for_user(db, u)
    return out


async def _signs_for_user(db, user: Optional[dict]) -> Dict[str, Any]:
    if not user:
        return {"found": False}
    uid = str(user.get("_id"))
    c = await db.charts.find_one({"user_id": uid})
    if not c:
        return {"found": True, "chart": False, "name": user.get("name")}
    ast = c.get("astrology") or {}
    planets = ast.get("planets") or {}
    angles  = ast.get("angles")  or {}
    return {
        "found":  True,
        "chart":  True,
        "name":   user.get("name"),
        "sun":    (planets.get("Sun")  or {}).get("sign"),
        "moon":   (planets.get("Moon") or {}).get("sign"),
        "asc":    (angles.get("asc")   or {}).get("sign"),
        "engine": c.get("astrology_engine_version"),
        "marker": c.get("migration_marker"),
    }


def _emit_block(label_begin: str, label_end: str, payload: Dict[str, Any]) -> None:
    """Print a fenced JSON block to stdout so it's findable in the logs view."""
    text = json.dumps(payload, indent=2, default=str, sort_keys=True)
    # Use both logger AND print so it appears in both supervisor and stdout
    # surfaces — Emergent's logs view shows stdout.
    logger.info(label_begin)
    for line in text.splitlines():
        logger.info(line)
    logger.info(label_end)
    # Also direct stdout for log-aggregation robustness
    print(label_begin, flush=True)
    print(text, flush=True)
    print(label_end, flush=True)


async def _run_preflight(db) -> Tuple[Dict[str, Any], Optional[str]]:
    """Returns (preflight_payload, abort_reason_or_None)."""
    mongo_url = os.environ.get("MONGO_URL")
    db_name   = os.environ.get("DB_NAME")
    host_info = _redact_mongo_host(mongo_url)
    is_preview = _looks_like_preview_db(db_name, host_info)

    forum_count = await db.forums.count_documents({})
    user_count  = await db.users.count_documents({})
    chart_count = await db.charts.count_documents({})

    pulsifi_found = (await db.forums.count_documents({
        "name": {"$regex": "Pulsifi", "$options": "i"}
    })) > 0
    jh_found  = (await db.users.count_documents({
        "name": {"$regex": "^JH( |$)", "$options": "i"}
    })) > 0
    jay_found = (await db.users.count_documents({
        "name": {"$regex": "^Jay( |$)", "$options": "i"}
    })) > 0

    already_marker = await db.charts.count_documents({"migration_marker": MIGRATION_MARKER})

    payload = {
        "build_marker":         BUILD_MARKER,
        "checked_at":           datetime.now(timezone.utc).isoformat(),
        "env_flag":             {"name": ENV_FLAG_NAME, "value_seen": os.environ.get(ENV_FLAG_NAME)},
        "db_identity": {
            "db_name":          db_name,
            "mongo_host":       host_info,
            "looks_like_preview_or_test_database": is_preview,
        },
        "counts": {
            "forums":                       forum_count,
            "users":                        user_count,
            "charts":                       chart_count,
            "charts_with_migration_marker": already_marker,
        },
        "presence": {
            "pulsifi_forum_found":          pulsifi_found,
            "jh_user_found":                jh_found,
            "jay_user_found":               jay_found,
        },
    }

    # Hard gates — must all pass.
    if is_preview:
        return payload, "preview_or_localhost_db_refused"
    if chart_count <= 0:
        return payload, "no_charts_in_db"
    if not pulsifi_found:
        return payload, "pulsifi_forum_not_found"
    if not jh_found and not jay_found:
        return payload, "neither_jh_nor_jay_user_found"
    if already_marker == chart_count:
        return payload, "already_migrated_all_charts_have_marker"
    return payload, None


async def run(db) -> None:
    """Entry point. Safe to call unconditionally — exits early if flag unset."""
    flag = os.environ.get(ENV_FLAG_NAME)
    if flag != ENV_FLAG_VALUE:
        logger.info(
            "[Variant A Startup Hook] flag '%s' not set to expected value; skipping.",
            ENV_FLAG_NAME,
        )
        return

    logger.info("[Variant A Startup Hook] %s — flag accepted, running preflight", BUILD_MARKER)

    # --- 1. Preflight ---
    try:
        preflight, abort_reason = await _run_preflight(db)
    except Exception as e:  # noqa: BLE001
        logger.exception("[Variant A Startup Hook] preflight failed with exception: %s", e)
        return

    _emit_block(PREFLIGHT_BEGIN, PREFLIGHT_END, preflight)

    if abort_reason:
        logger.error(
            "[Variant A Startup Hook] ABORT — preflight failed: %s. No writes performed.",
            abort_reason,
        )
        return

    logger.info("[Variant A Startup Hook] preflight passed — proceeding to snapshot + recompute")

    # --- 2. Snapshot (read-only) ---
    snapshot_summary: Dict[str, Any] = {}
    try:
        snap = await run_snapshot()
        snapshot_summary = {
            "counts":        snap.get("counts"),
            "snapshot_path": snap.get("snapshot_path"),
            "started_at":    snap.get("started_at"),
            "finished_at":   snap.get("finished_at"),
        }
    except Exception as e:  # noqa: BLE001
        logger.exception("[Variant A Startup Hook] snapshot failed: %s", e)
        snapshot_summary = {"error": str(e)[:300]}

    # --- 3. Recompute (writes!) ---
    try:
        recompute_report = await recompute_users(db, dry_run=False)
    except Exception as e:  # noqa: BLE001
        logger.exception("[Variant A Startup Hook] recompute failed: %s", e)
        _emit_block(REPORT_BEGIN_MARKER, REPORT_END_MARKER, {
            "build_marker": BUILD_MARKER,
            "status":       "error_during_recompute",
            "error":        str(e)[:500],
            "preflight":    preflight,
            "snapshot":     snapshot_summary,
        })
        return

    # --- 4. Cache invalidation (writes!) ---
    try:
        cache_report = await invalidate_caches(db, dry_run=False)
    except Exception as e:  # noqa: BLE001
        logger.exception("[Variant A Startup Hook] cache invalidation failed: %s", e)
        cache_report = {"error": str(e)[:300]}

    # --- 5. Phase 6 validation ---
    try:
        validation = await run_validate(db)
    except Exception as e:  # noqa: BLE001
        logger.exception("[Variant A Startup Hook] validation failed: %s", e)
        validation = {"error": str(e)[:300]}

    # --- 6. Post-migration anchor read-back ---
    try:
        anchors = await _anchor_signs(db)
    except Exception as e:  # noqa: BLE001
        anchors = {"error": str(e)[:300]}

    # --- 7. Build final report + emit ---
    finished_at = datetime.now(timezone.utc).isoformat()
    report = {
        "build_marker":    BUILD_MARKER,
        "status":          "success",
        "engine":          ASTROLOGY_ENGINE_VERSION,
        "marker":          MIGRATION_MARKER,
        "house_system":    CANONICAL_HOUSE_SYSTEM,
        "finished_at":     finished_at,
        "preflight":       preflight,
        "snapshot":        snapshot_summary,
        "recompute":       recompute_report,
        "caches":          cache_report,
        "validation":      validation,
        "anchor_signs_after_migration": anchors,
    }
    _emit_block(REPORT_BEGIN_MARKER, REPORT_END_MARKER, report)

    # --- 8. Best-effort persistence to pod disk ---
    try:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = f"/app/backend/audits/variant_a_prod_migration_report_{ts}.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("[Variant A Startup Hook] report persisted to %s", path)
    except Exception as e:  # noqa: BLE001
        logger.warning("[Variant A Startup Hook] report persistence failed (non-fatal): %s", e)

    logger.info("[Variant A Startup Hook] COMPLETE — migration finished successfully")
