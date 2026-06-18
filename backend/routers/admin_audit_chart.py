"""admin_audit_chart.py — P0 forensic audit endpoint
================================================================

READ-ONLY diagnostic endpoint for inspecting the Atlas-persisted
chart document for a single user.  Built specifically for the Mel
Gemini-Rising regression investigation: returns the full provenance
trail (V-A markers, debug_stamp, timestamps, ASC + planet snapshot)
so we can determine whether the cohort repair was ever persisted,
and if so, what wrote over it.

Build marker:           audit-chart-provenance-v1
Confirm token (query):  AUDIT_CHART_V1
Method:                 GET   (never writes; safe to call repeatedly)
Mounted at:             /api/admin/audit_chart

Refuses to operate against loopback Mongo (preview pod) so this
cannot accidentally introspect the wrong cluster.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("admin_audit_chart")

ROUTE_BUILD_MARKER = "audit-chart-provenance-v1"
CONFIRM_TOKEN      = "AUDIT_CHART_V1"

VARIANT_A_ENGINE_VERSION   = "midpoint13_variant_a_v1"
VARIANT_A_MIGRATION_MARKER = "variant-a-13-sign-migration-v1"

# Mongo client — sourced from the same env vars used by server.py so
# we connect to the SAME database the application is reading/writing.
_MONGO_URL = os.environ.get("MONGO_URL", "")
_DB_NAME   = os.environ.get("DB_NAME", "")
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _is_loopback_host(uri: str) -> bool:
    try:
        host = urlparse(uri).hostname or ""
    except Exception:
        return False
    return host in _LOOPBACK_HOSTS


_client: Optional[AsyncIOMotorClient] = None
_db = None
if _MONGO_URL and _DB_NAME:
    try:
        _client = AsyncIOMotorClient(_MONGO_URL)
        _db = _client[_DB_NAME]
    except Exception as e:
        logger.error("[audit_chart] failed to create motor client: %s", e)
        _client = None
        _db = None


router = APIRouter(prefix="/api/admin", tags=["admin-audit"])


def _client_ip(request: Request) -> str:
    try:
        return request.client.host or "?"
    except Exception:
        return "?"


def _iso(v):
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def _safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return default
    return cur if cur is not None else default


def _summarize_planets(astro: Dict[str, Any]) -> Dict[str, Any]:
    """Compact planet-snapshot for the audit response."""
    planets = astro.get("planets") or {}
    if not isinstance(planets, dict):
        return {}
    out: Dict[str, Any] = {}
    for key in ("Sun", "Moon", "Mercury", "Venus", "Mars",
                "Jupiter", "Saturn", "sun", "moon"):
        p = planets.get(key)
        if isinstance(p, dict):
            out[key] = {
                "sign":      p.get("sign") or p.get("sign_name"),
                "degree":    p.get("degree"),
                "formatted": p.get("formatted"),
                "longitude": p.get("longitude"),
                "house":     p.get("house"),
            }
    return out


def _diagnose_state(chart: Dict[str, Any]) -> Dict[str, Any]:
    """High-level pass/fail flags so the caller can read state at a
    glance without unwrapping the whole chart."""
    engine_v = chart.get("astrology_engine_version")
    mig_m    = chart.get("migration_marker")
    is_va    = (engine_v == VARIANT_A_ENGINE_VERSION
                and mig_m == VARIANT_A_MIGRATION_MARKER)
    has_va_engine_only = (engine_v == VARIANT_A_ENGINE_VERSION) and not is_va
    has_va_marker_only = (mig_m == VARIANT_A_MIGRATION_MARKER) and not is_va

    astro = chart.get("astrology") or {}
    asc = _safe_get(astro, "angles", "asc") or {}
    asc_sign = asc.get("sign") or asc.get("sign_name")
    asc_long = asc.get("longitude")

    return {
        "is_variant_a_locked":  bool(is_va),
        "has_va_engine_only":   bool(has_va_engine_only),
        "has_va_marker_only":   bool(has_va_marker_only),
        "auto_migrate_will_run_on_next_read": (not is_va),
        "asc_sign_now":         asc_sign,
        "asc_longitude_now":    asc_long,
        "asc_is_gemini_regression": (
            isinstance(asc_sign, str) and asc_sign.strip().lower() == "gemini"
        ),
    }


# ──────────────────────────────────────────────────────────────────
# Provenance: a heuristic timestamp timeline derived from the chart
# document itself.  Mongo does not natively expose a per-document
# write history, but we DO have multiple datetime fields stamped by
# each write path, so we can build a sequence-of-writes timeline.
# ──────────────────────────────────────────────────────────────────

# Maps a (field_name) → (descriptive_label, write_path_attribution).
_PROVENANCE_FIELDS: List[Dict[str, str]] = [
    {
        "field":       "_id_timestamp",
        "label":       "chart_document_created",
        "write_path":  "POST /api/users (initial chart insert via Mongo ObjectId timestamp)",
    },
    {
        "field":       "created_at",
        "label":       "chart_document.created_at",
        "write_path":  "initial chart creation",
    },
    {
        "field":       "calculated_at",
        "label":       "chart_document.calculated_at",
        "write_path":  "check_and_migrate_astrology_chart (auto-migration) OR initial compute path",
    },
    {
        "field":       "migration_info.migrated_at",
        "label":       "migration_info.migrated_at",
        "write_path":  "server.py check_and_migrate_astrology_chart — AUTO-MIGRATION ran (THIS WOULD STRIP V-A MARKERS IF GUARD FAILED)",
    },
    {
        "field":       "chart_updated_at",
        "label":       "chart_updated_at",
        "write_path":  "cohort repair endpoint OR admin_fix_mel_live (manual surgical write)",
    },
    {
        "field":       "updated_at",
        "label":       "updated_at",
        "write_path":  "any update_one with $set including updated_at",
    },
    {
        "field":       "debug_stamp.fixed_at_iso",
        "label":       "debug_stamp.fixed_at_iso",
        "write_path":  "admin_fix_historical_tz_cohort (THE COHORT REPAIR) — fix-historical-tz-cohort-v1",
    },
]


def _build_timeline(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build a sorted timeline of every datetime-bearing field on the
    chart document, with attribution to the write path that stamps it.
    Earliest first.  Used to determine the LAST WRITE that touched
    Mel's chart and infer who is responsible for the current state."""
    events: List[Dict[str, Any]] = []
    # ObjectId carries a creation timestamp.
    _id = chart.get("_id")
    if isinstance(_id, ObjectId):
        events.append({
            "ts":         _iso(_id.generation_time),
            "field":      "_id_timestamp",
            "label":      "chart_document_created",
            "write_path": "POST /api/users (initial chart insert; from Mongo ObjectId.generation_time)",
        })

    for spec in _PROVENANCE_FIELDS:
        if spec["field"] == "_id_timestamp":
            continue
        # Support nested fields like migration_info.migrated_at and
        # debug_stamp.fixed_at_iso.
        path = spec["field"].split(".")
        cur = chart
        ok = True
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                ok = False
                break
            cur = cur[k]
        if not ok or cur in (None, ""):
            continue
        events.append({
            "ts":         _iso(cur),
            "field":      spec["field"],
            "label":      spec["label"],
            "write_path": spec["write_path"],
        })

    # Sort by ts (string sort works for ISO-8601; tolerate dicts).
    def _key(e):
        ts = e.get("ts")
        return ts if isinstance(ts, str) else ""

    events.sort(key=_key)
    return events


# ──────────────────────────────────────────────────────────────────
# Route
# ──────────────────────────────────────────────────────────────────

@router.get("/audit_chart")
async def audit_chart(
    request: Request,
    user_id: str = Query(..., description="user_id (string of the Mongo ObjectId) whose chart to audit"),
    confirm: str = Query(..., description=f"Must equal {CONFIRM_TOKEN}"),
):
    """READ-ONLY forensic dump of `db.charts.find_one({user_id})`,
    plus a derived timeline of every datetime-stamped write event
    discoverable from the document itself, plus state-flag summary
    (is_variant_a_locked, asc_is_gemini_regression, etc.).

    Pure read.  No writes.  Refuses to run against loopback Mongo.
    """
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail={
            "code":    "INVALID_CONFIRM_TOKEN",
            "message": f"Append ?confirm={CONFIRM_TOKEN} to authorise this read.",
        })
    if _db is None or _is_loopback_host(_MONGO_URL):
        raise HTTPException(status_code=503, detail={
            "code":    "PREVIEW_DB_REFUSED",
            "message": "Refuses to operate on localhost Mongo.  Use the deployed Atlas-backed pod.",
            "mongo_host": urlparse(_MONGO_URL).hostname,
        })

    logger.warning(
        "[%s] audit_chart user_id=%s ip=%s",
        ROUTE_BUILD_MARKER, user_id, _client_ip(request),
    )

    # Find chart by user_id (string).
    chart = await _db.charts.find_one({"user_id": user_id})
    if not chart:
        return JSONResponse(content={
            "build_marker": ROUTE_BUILD_MARKER,
            "user_id":      user_id,
            "found":        False,
            "message":      "No chart document with this user_id in db.charts",
        }, headers={"Cache-Control": "no-store"})

    # User doc for the canonical inputs (so we can sanity-check what
    # was used at the most recent write).
    user_doc = None
    try:
        user_doc = await _db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user_doc = await _db.users.find_one({"_id": user_id})

    astro = chart.get("astrology") or {}
    asc = _safe_get(astro, "angles", "asc") or {}
    meta = astro.get("metadata") or {}

    # Build top-level provenance snapshot.
    provenance = {
        "astrology_engine_version_top": chart.get("astrology_engine_version"),
        "astrology_engine_version_meta": meta.get("astrology_engine_version"),
        "computation_version":          meta.get("computation_version"),
        "migration_marker":             chart.get("migration_marker"),
        "chart_updated_at":             _iso(chart.get("chart_updated_at")),
        "updated_at":                   _iso(chart.get("updated_at")),
        "calculated_at":                _iso(chart.get("calculated_at")),
        "created_at":                   _iso(chart.get("created_at")),
        "input_datetime_utc":           _iso(meta.get("birth_utc")
                                             or meta.get("input_datetime_utc")
                                             or meta.get("birth_datetime_utc")),
        "julian_day":                   meta.get("julian_day"),
        "zodiac_mode":                  astro.get("zodiac_mode")
                                          or meta.get("zodiac_mode"),
        "debug_stamp":                  chart.get("debug_stamp"),
        "migration_info":               chart.get("migration_info"),
    }

    asc_snapshot = {
        "sign":              asc.get("sign") or asc.get("sign_name"),
        "degree":            asc.get("degree"),
        "longitude":         asc.get("longitude"),
        "tropical_longitude": asc.get("tropical_longitude"),
        "formatted":         asc.get("formatted"),
        "house":             asc.get("house"),
    }

    state_flags = _diagnose_state(chart)
    timeline = _build_timeline(chart)

    # User-doc canonical inputs (useful for the cohort to confirm we
    # are not re-introducing wrong tz).
    user_inputs = None
    if user_doc:
        user_inputs = {
            "email":          user_doc.get("email"),
            "name":           user_doc.get("name"),
            "timezone":       user_doc.get("timezone"),
            "birth_date":     _iso(user_doc.get("birth_date")),
            "birth_time":     user_doc.get("birth_time"),
            "birth_location": user_doc.get("birth_location"),
            "user_updated_at": _iso(user_doc.get("updated_at")),
        }

    # Determine the LAST write event (latest ts) and attribute it.
    last_write = timeline[-1] if timeline else None

    return JSONResponse(content={
        "build_marker":         ROUTE_BUILD_MARKER,
        "served_at":            datetime.now(timezone.utc).isoformat(),
        "user_id":              user_id,
        "chart_id":             str(chart.get("_id")),
        "found":                True,

        "state_flags":          state_flags,
        "provenance":           provenance,
        "asc_snapshot":         asc_snapshot,
        "planets_snapshot":     _summarize_planets(astro),
        "user_inputs":          user_inputs,

        "write_timeline":       timeline,
        "last_write":           last_write,

        "next_actions": [
            "If state_flags.is_variant_a_locked is FALSE, the auto-migration hook will OVERWRITE the chart on next /api/forums/.../pulse request.",
            "If state_flags.asc_is_gemini_regression is TRUE and last_write.write_path is the cohort repair, then the repair never persisted (or was overwritten AFTER it).",
            "If a `migration_info.migrated_at` timestamp is LATER than the cohort `debug_stamp.fixed_at_iso`, the auto-migration rewrote the chart AFTER the cohort fix.",
        ],
    }, headers={"Cache-Control": "no-store"})


# ──────────────────────────────────────────────────────────────────
# Companion route — write-path map.  Pure static dump of every
# place in the codebase that writes to db.charts, so the user can
# reason about which paths could plausibly have touched Mel's chart.
# ──────────────────────────────────────────────────────────────────

_WRITE_PATH_MAP: List[Dict[str, str]] = [
    {
        "path":        "POST /api/users",
        "file":        "server.py:4733",
        "operation":   "db.charts.update_one (initial creation / upsert)",
        "sets_V_A":    "NO (initial create; V-A markers added separately on later writes)",
        "trigger":     "User signup / re-onboarding submits birth data.",
    },
    {
        "path":        "PUT /api/users/{user_id} (profile update with birth data)",
        "file":        "server.py:10999 (inside check_and_migrate_astrology_chart)",
        "operation":   "db.charts.update_one({'user_id'}, {'$set': chart_update})",
        "sets_V_A":    "NO  ← does NOT stamp astrology_engine_version or migration_marker!",
        "trigger":     "Any read that flows through /api/astrology/summary, /api/astrology/deep-dive, or /api/forums/.../member-summary when the chart shape is judged 'old'.",
        "regression_risk": "HIGH — this is the auto-migration path that the V-A guard at server.py:10866 is supposed to stop.  If the V-A markers are absent for any reason, this re-runs.",
    },
    {
        "path":        "Auto-migration: check_and_migrate_astrology_chart",
        "file":        "server.py:10848-11011",
        "operation":   "db.charts.update_one (recomputes astrology + HD + numerology)",
        "sets_V_A":    "NO — only sets calculated_at + migration_info; V-A markers are NEVER set by this path",
        "trigger":     "Called from /api/astrology/summary, /api/astrology/deep-dive, /api/forums/.../pulse on every read that hits the migration guard.",
        "regression_risk": "CRITICAL — if guard fails (markers stripped), every pulse/summary read re-rewrites the chart and reintroduces drift.",
    },
    {
        "path":        "POST /api/admin/fix_mel_live",
        "file":        "server.py:32560",
        "operation":   "db.charts.update_one(..., upsert=True) — stamps V-A markers",
        "sets_V_A":    "YES — explicit astrology_engine_version + migration_marker stamp",
        "trigger":     "Manual call with ?confirm=FIX_MEL_LIVE_V1.",
    },
    {
        "path":        "POST /api/admin/fix_historical_tz_cohort",
        "file":        "routers/admin_fix_historical_tz_cohort.py:366",
        "operation":   "db.charts.update_one (per drifted user) — stamps V-A markers + debug_stamp",
        "sets_V_A":    "YES — explicit astrology_engine_version + migration_marker stamp",
        "trigger":     "Manual call with ?confirm=FIX_HISTORICAL_TZ_2026_06_17.",
    },
    {
        "path":        "Variant A migration script",
        "file":        "scripts/migration_phase5_variant_a.py:294",
        "operation":   "db.charts.update_one",
        "sets_V_A":    "YES — sets both markers as part of the migration",
        "trigger":     "Manual operator script; gated by RUN_VARIANT_A_MIGRATION env flag.",
    },
    {
        "path":        "HD type migration",
        "file":        "services/hd_type_migration.py:214,241",
        "operation":   "db.charts.update_one (touches human_design subtree only)",
        "sets_V_A":    "NO (does not touch astrology subtree or V-A markers)",
        "trigger":     "Admin endpoint; only updates HD type field.",
    },
    {
        "path":        "Forum lens helpers (chart maintenance)",
        "file":        "services/forum_lens_helpers.py:421",
        "operation":   "db.charts.update_one",
        "sets_V_A":    "DEPENDS — check the specific update_doc",
        "trigger":     "Forum member summary computation flow.",
    },
    {
        "path":        "Forum HD mapping",
        "file":        "services/forum_hd_mapping.py:1802",
        "operation":   "db.charts.update_one",
        "sets_V_A":    "DEPENDS — check the specific update_doc",
        "trigger":     "Forum HD mapping refresh.",
    },
    {
        "path":        "True Sidereal Midpoint background migration",
        "file":        "server.py:15026,16750,20877,27783,27894,33115,33271,33360",
        "operation":   "db.charts.update_one (various background backfills)",
        "sets_V_A":    "DEPENDS per call site",
        "trigger":     "Startup data-migration tasks and runtime backfills.",
    },
]


@router.get("/write_path_map")
async def write_path_map(
    request: Request,
    confirm: str = Query(..., description=f"Must equal {CONFIRM_TOKEN}"),
):
    """READ-ONLY catalog of every code path that writes to db.charts."""
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail={
            "code":    "INVALID_CONFIRM_TOKEN",
            "message": f"Append ?confirm={CONFIRM_TOKEN} to authorise this read.",
        })
    return JSONResponse(content={
        "build_marker":    ROUTE_BUILD_MARKER,
        "write_path_map":  _WRITE_PATH_MAP,
        "total_paths":     len(_WRITE_PATH_MAP),
        "highest_risk_paths": [
            p["path"] for p in _WRITE_PATH_MAP
            if p.get("regression_risk", "").startswith("CRITICAL")
        ],
    }, headers={"Cache-Control": "no-store"})
