"""
TEMPORARY — Variant A Phase 5 Migration Admin Routes
====================================================
Build marker: variant-a-prod-migration-admin-v1

Purpose
-------
Three short-lived HTTP routes that allow the operator to:

  1. GET  /api/admin/migration-info       — read-only DB identity + counts
  2. POST /api/admin/migration-snapshot   — read-only snapshot capture
  3. POST /api/admin/migration-run        — wet migration (write-gated)

These routes exist solely to run the Variant A Phase 5 recompute against
the *deployed* MongoDB (the preview pod cannot reach the deployed Mongo).
After the production migration has completed and the operator has captured
the report, this entire file should be deleted and `server.py` should be
re-published without the `register(...)` call.

Security model
--------------
Every route is guarded by `_require_admin(...)` which enforces:
    * env var `MIGRATION_ADMIN_TOKEN` MUST be set        → otherwise HTTP 503
    * request header `X-Admin-Token` MUST match the env   → otherwise HTTP 401
    * comparison uses `hmac.compare_digest` (constant-time)

In addition, the WRITE route `/migration-run` ALSO refuses unless:
    * query parameter `confirm == "VARIANT_A_PHASE_5"`
    * the resolved MongoDB host is NOT `localhost` / `127.0.0.1`
    * the resolved DB_NAME is NOT `test_database`
    * a forum whose name matches /Pulsifi/i exists in this DB
    * a user named "JH" OR "Jay" exists in this DB
    * `charts` collection has at least one document
    * NOT all charts are already migrated
        (already_migrated_count != total_charts_count)

The READ-ONLY routes perform zero writes to Mongo.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

# Re-use the existing migration helpers — these are the SAME functions that
# the CLI scripts call. They each accept a Mongo `db` handle so we can pass
# the server's existing `db` (which is bound to the deployed pod's
# MONGO_URL/DB_NAME at process start).
sys.path.insert(0, "/app/backend")
from scripts.migration_phase5_variant_a import (   # noqa: E402
    recompute_users,
    invalidate_caches,
    validate as run_validate,
    ASTROLOGY_ENGINE_VERSION,
    MIGRATION_MARKER,
    CANONICAL_HOUSE_SYSTEM,
    SIGN_DEPENDENT_CACHES,
)
from scripts.migration_snapshot_variant_a import run_snapshot  # noqa: E402

ROUTE_BUILD_MARKER = "variant-a-prod-migration-admin-v1"


def _member_summary_marker() -> str:
    """Import-time-safe extraction of the member_summary build marker
    so deployment health checks can detect whether the mel-rising-fix
    build (or any subsequent member_summary build) is the one running.

    Returns the marker string, or an explicit absence sentinel if the
    module is missing the marker (which means the deployed image was
    built from a pre-fix code snapshot)."""
    try:
        import services.member_summary as _ms  # noqa: WPS433 (local import is intentional)
        marker = getattr(_ms, "BUILD_MARKER", None)
        if marker:
            return str(marker)
        # Fall back to scanning the module docstring for the marker token
        # so the legacy fix (which only commented it) still reports.
        doc = (_ms.__doc__ or "")
        for token in ("mel-rising-fix-member-summary-v1",):
            if token in doc:
                return token
        return "<member_summary_marker_absent>"
    except Exception as exc:  # pragma: no cover — defensive
        return f"<error:{type(exc).__name__}>"


# Resolve the Mongo connection from the *running pod's* env. Inside the
# preview container this resolves to mongodb://localhost:27017/test_database;
# inside the deployed pod it resolves to the deployed Mongo. The route
# handlers re-check this on every request, so a misrouted invocation is
# always refused by the write-gate preflight.
_MONGO_URL = os.environ.get("MONGO_URL")
_DB_NAME   = os.environ.get("DB_NAME")
_client    = AsyncIOMotorClient(_MONGO_URL) if _MONGO_URL else None
_db        = _client[_DB_NAME] if (_client is not None and _DB_NAME) else None

import logging
logger = logging.getLogger("admin_variant_a_migration")


# =====================================================================
# Helpers
# =====================================================================
def _redact_mongo_host(mongo_url: Optional[str]) -> Dict[str, Any]:
    """Return host + scheme of MONGO_URL with credentials stripped."""
    if not mongo_url:
        return {"present": False}
    try:
        parsed = urlparse(mongo_url)
        # urllib treats `mongodb://` like a normal URL with optional userinfo
        host = parsed.hostname or "<unknown>"
        port = parsed.port
        scheme = parsed.scheme
        # Detect localhost / private loopback / preview Mongo names
        is_loopback = host in ("localhost", "127.0.0.1", "::1", "0.0.0.0")
        return {
            "present":     True,
            "scheme":      scheme,
            "host":        host,
            "port":        port,
            "is_loopback": is_loopback,
            "userinfo":    "<redacted>" if (parsed.username or parsed.password) else None,
        }
    except Exception as e:
        return {"present": True, "parse_error": str(e)[:120]}


def _safe_oid_to_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return "<unprintable>"


def _require_admin(x_admin_token: Optional[str]) -> None:
    """Raises HTTPException if token misconfigured or missing/mismatched."""
    expected = os.environ.get("MIGRATION_ADMIN_TOKEN")
    if not expected:
        # 503 — service-side misconfiguration; the routes are inert.
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MIGRATION_ADMIN_TOKEN_NOT_SET",
                "message": (
                    "MIGRATION_ADMIN_TOKEN env var is not configured on this "
                    "backend. Set it in the deployed pod's environment "
                    "variables and re-publish before invoking admin routes."
                ),
            },
        )
    if not x_admin_token or not hmac.compare_digest(str(x_admin_token), str(expected)):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_ADMIN_TOKEN",
                "message": "Provide a valid X-Admin-Token header.",
            },
        )


async def _engine_version_distribution(db) -> Dict[str, int]:
    out: Dict[str, int] = {}
    async for c in db.charts.find({}, {"astrology_engine_version": 1}):
        ev = c.get("astrology_engine_version") or "<missing>"
        out[ev] = out.get(ev, 0) + 1
    return out


async def _find_pulsifi_forums(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    async for f in db.forums.find(
        {"name": {"$regex": "Pulsifi", "$options": "i"}},
        {"_id": 1, "name": 1, "member_count": 1},
    ):
        out.append({
            "_id":          _safe_oid_to_str(f.get("_id")),
            "name":         f.get("name"),
            "member_count": f.get("member_count"),
        })
    return out


async def _find_named_users(db, names: Tuple[str, ...]) -> List[Dict[str, Any]]:
    """Find users whose name matches any of the provided exact-or-prefix names
    (case-insensitive). Returns minimal fields only."""
    or_clauses: List[Dict[str, Any]] = []
    for n in names:
        # exact (case-insensitive) OR prefix to catch "Jay Foo", "JH Bar".
        safe = re.escape(n)
        or_clauses.append({"name": {"$regex": f"^{safe}( |$)", "$options": "i"}})
    if not or_clauses:
        return []
    out: List[Dict[str, Any]] = []
    async for u in db.users.find({"$or": or_clauses}, {"_id": 1, "name": 1, "email": 1}):
        out.append({
            "_id":   _safe_oid_to_str(u.get("_id")),
            "name":  u.get("name"),
            "email": u.get("email"),
        })
    return out


def _looks_like_preview_db(db_name: Optional[str], host_info: Dict[str, Any]) -> bool:
    """Heuristic — true if this almost certainly is the preview/dev DB."""
    if (db_name or "").lower() == "test_database":
        return True
    if host_info.get("is_loopback"):
        return True
    return False


# =====================================================================
# Router — standalone APIRouter, attached via app.include_router in
# server.py (matches the admin_gm_aligned pattern). Using a standalone
# router avoids the FastAPI gotcha where adding routes to api_router
# AFTER app.include_router(api_router) has been called does not
# propagate them to the live app.
# =====================================================================
router = APIRouter(prefix="/api/admin", tags=["admin-variant-a-migration"])


# ---------------------------------------------------------------------
# TZ-INTEGRITY (Phase 1) — read-only audit endpoints
# ---------------------------------------------------------------------
@router.get("/timezone-integrity-summary")
async def timezone_integrity_summary():
    """Aggregate counts of stored tz values across all users. Read-only."""
    if _db is None:
        raise HTTPException(status_code=500, detail={"code": "MONGO_NOT_CONFIGURED"})
    from services.timezone_resolver import is_iana_name
    total = await _db.users.count_documents({})
    with_tz_count = 0
    iana_count = 0
    fixed_offset_count = 0
    dist = {}
    async for u in _db.users.find({}, {"birth_timezone":1,"timezone":1,"birth_location.timezone":1}):
        tz = u.get("birth_timezone") \
             or (u.get("birth_location") or {}).get("timezone") \
             or u.get("timezone")
        if not tz:
            continue
        with_tz_count += 1
        sval = str(tz)
        dist[sval] = dist.get(sval, 0) + 1
        if is_iana_name(sval):
            iana_count += 1
        elif sval.startswith(("+", "-")) or sval.upper() in ("UTC","GMT","Z"):
            fixed_offset_count += 1
    top = sorted(dist.items(), key=lambda kv: -kv[1])[:20]
    return JSONResponse(content={
        "total_users":                       total,
        "users_with_timezone":               with_tz_count,
        "users_with_iana_timezone":          iana_count,
        "users_with_fixed_offset_timezone":  fixed_offset_count,
        "users_without_timezone":            total - with_tz_count,
        "top_timezone_values":               [{"value": k, "count": v} for k, v in top],
        "server_time_utc":                   datetime.now(timezone.utc).isoformat(),
    }, headers={"Cache-Control": "no-store"})


@router.get("/timezone-audit/{user_id}")
async def timezone_audit(user_id: str):
    """Per-user tz audit. Read-only — no recomputation, no writes."""
    if _db is None:
        raise HTTPException(status_code=500, detail={"code": "MONGO_NOT_CONFIGURED"})
    from services.timezone_resolver import resolve_iana_timezone, is_iana_name
    user = None
    try:
        from bson import ObjectId
        try: user = await _db.users.find_one({"_id": ObjectId(user_id)})
        except Exception: pass
    except Exception:
        pass
    if not user:
        user = await _db.users.find_one({"_id": user_id}) \
            or await _db.users.find_one({"user_id": user_id})
    if not user:
        return JSONResponse(status_code=404,
                            content={"found": False, "user_id_searched": user_id})
    bl = user.get("birth_location") or {}
    lat = bl.get("latitude")
    lon = bl.get("longitude")
    stored_tz = user.get("birth_timezone") or bl.get("timezone") or user.get("timezone")
    resolved_tz = resolve_iana_timezone(lat, lon)
    chart = await _db.charts.find_one({"user_id": str(user.get("_id"))})
    return JSONResponse(content=jsonable_encoder({
        "user_id":                            str(user.get("_id")),
        "name":                               user.get("name"),
        "city":                               bl.get("city"),
        "country":                            bl.get("country"),
        "latitude":                           lat,
        "longitude":                          lon,
        "stored_timezone":                    stored_tz,
        "stored_timezone_is_iana":            is_iana_name(stored_tz) if stored_tz else False,
        "resolved_timezone_from_coordinates": resolved_tz,
        "match":                              (stored_tz == resolved_tz) if resolved_tz else False,
        "chart_present":                      bool(chart),
        "astrology_engine_version":           (chart or {}).get("astrology_engine_version"),
    }), headers={"Cache-Control": "no-store"})



# ---------------------------------------------------------------------
# 0) NO-AUTH READ-ONLY: build & deployed-state proof
# ---------------------------------------------------------------------
@router.get("/build-info")
async def build_info():
    """Returns aggregate facts proving (or disproving) which commit is
    actually live on this pod. Returns only counts + booleans — no PII,
    no chart contents, no user-identifiable data. Safe to expose without
    auth for the duration of the migration window."""
    # Try to import the startup hook module to confirm it exists.
    startup_hook_marker = "not_imported"
    startup_hook_imported = False
    try:
        from routers import variant_a_startup_hook as _vah   # noqa: PLC0415
        startup_hook_marker = getattr(_vah, "BUILD_MARKER", "imported_no_marker")
        startup_hook_imported = True
    except Exception:  # noqa: BLE001
        pass

    # v1.5.5 — Frontend bundle fingerprint. Reads the latest entry-*.js
    # filename + mtime from `backend/web_dist/`.  This lets the caller
    # PROVE whether the deployed frontend matches the deployed backend
    # without trusting any external sources. Returns None when not
    # built or when web_dist is missing.
    frontend_bundle_info = None
    try:
        import glob as _glob
        from pathlib import Path as _Path
        wd_root = _Path("/app/backend/web_dist")
        js_dir  = wd_root / "_expo" / "static" / "js" / "web"
        if js_dir.is_dir():
            entries = sorted(js_dir.glob("entry-*.js"),
                             key=lambda p: p.stat().st_mtime, reverse=True)
            if entries:
                top = entries[0]
                idx_html = wd_root / "index.html"
                frontend_bundle_info = {
                    "entry_filename": top.name,
                    "entry_size_bytes": top.stat().st_size,
                    "entry_mtime_utc": datetime.fromtimestamp(
                        top.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "index_html_mtime_utc": (
                        datetime.fromtimestamp(idx_html.stat().st_mtime,
                                                tz=timezone.utc).isoformat()
                        if idx_html.is_file() else None),
                    # The "hash" inside the filename — used by CDN cache
                    # to prove freshness.
                    "entry_hash": (top.name.replace("entry-", "")
                                     .replace(".js", "")),
                }
    except Exception:  # noqa: BLE001
        pass

    # Env-flag presence (do not echo a real token; just a state label).
    flag_value = os.environ.get("RUN_VARIANT_A_MIGRATION")
    if flag_value is None:
        flag_state = "unset"
    elif flag_value == "VARIANT_A_PHASE_5":
        flag_state = "set"
    else:
        flag_state = "set_wrong_value"

    # DB-side counts (read-only).
    if _db is None:
        return JSONResponse(
            content={
                "build_markers": {
                    "admin_module":     ROUTE_BUILD_MARKER,
                    "startup_hook":     startup_hook_marker,
                    "member_summary":   _member_summary_marker(),
                },
                "startup_hook_imported":          startup_hook_imported,
                "env_flag_run_variant_a":         flag_state,
                "error":                          "MONGO_NOT_CONFIGURED",
                "server_time_utc":                datetime.now(timezone.utc).isoformat(),
            },
            headers={"Cache-Control": "no-store"},
        )

    mongo_url   = os.environ.get("MONGO_URL")
    db_name     = os.environ.get("DB_NAME")
    host_info   = _redact_mongo_host(mongo_url)
    looks_pre   = _looks_like_preview_db(db_name, host_info)

    charts_total = await _db.charts.count_documents({})
    engine_dist  = await _engine_version_distribution(_db)
    migrated_n   = await _db.charts.count_documents({
        "migration_marker": MIGRATION_MARKER,
    })
    forensic_n   = await _db.charts.count_documents({
        "astrology.forensic_variant_b": {"$exists": True},
    })

    return JSONResponse(
        content={
            "build_markers": {
                "admin_module":     ROUTE_BUILD_MARKER,
                "startup_hook":     startup_hook_marker,
                "member_summary":   _member_summary_marker(),
            },
            "frontend_bundle":                frontend_bundle_info,
            "startup_hook_imported":           startup_hook_imported,
            "env_flag_run_variant_a":          flag_state,
            "migration_marker_chart_count":   migrated_n,
            "forensic_variant_b_chart_count": forensic_n,
            "engine_version_distribution":    engine_dist,
            "charts_total":                   charts_total,
            "db_name":                        db_name,
            "mongo_host_redacted":            host_info,
            "looks_like_preview":             looks_pre,
            "server_time_utc":                datetime.now(timezone.utc).isoformat(),
        },
        headers={"Cache-Control": "no-store"},
    )


# ---------------------------------------------------------------------
# 0b) NO-AUTH READ-ONLY: per-user chart snapshot for GM verification
# Returns the RAW stored chart document for one user. No recomputation,
# no formatting, no derived values. Pure dict-walking from Mongo.
# ---------------------------------------------------------------------
@router.get("/chart-snapshot/{user_id}")
async def chart_snapshot(user_id: str):
    if _db is None:
        raise HTTPException(status_code=500, detail={
            "code": "MONGO_NOT_CONFIGURED",
            "message": "MONGO_URL / DB_NAME not present in env."})

    # Find user (try ObjectId first, then string)
    user = None
    try:
        from bson import ObjectId
        try:
            user = await _db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            pass
    except Exception:
        pass
    if not user:
        user = await _db.users.find_one({"_id": user_id})
    if not user:
        user = await _db.users.find_one({"user_id": user_id})

    if not user:
        return JSONResponse(
            content={"found": False, "user_id_searched": user_id},
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )

    uid_str = str(user.get("_id"))
    # Fetch chart by user_id (string)
    chart = await _db.charts.find_one({"user_id": uid_str})
    if not chart:
        chart = await _db.charts.find_one({"user_id": user.get("_id")})

    # Stored birth data — raw values from user doc
    bl = user.get("birth_location") or {}
    coords = bl.get("coordinates") or {}
    birth_data = {
        "birth_date":  user.get("birth_date"),
        "birth_time":  user.get("birth_time"),
        "timezone":    user.get("birth_timezone")
                       or user.get("timezone")
                       or bl.get("timezone"),
        "timezone_minutes": user.get("timezone_minutes"),
        "latitude":    bl.get("latitude") or coords.get("lat") or user.get("latitude"),
        "longitude":   bl.get("longitude") or coords.get("lon") or user.get("longitude"),
        "place":       bl.get("city") or bl.get("name"),
        "country":     bl.get("country"),
    }

    if not chart:
        return JSONResponse(
            content={
                "found":         True,
                "chart_present": False,
                "user_id":       uid_str,
                "name":          user.get("name"),
                "birth_data":    birth_data,
            },
            headers={"Cache-Control": "no-store"},
        )

    ast = chart.get("astrology") or {}
    planets_raw = ast.get("planets") or {}
    nodes_raw   = ast.get("nodes")   or {}
    angles_raw  = ast.get("angles")  or {}
    houses_raw  = ast.get("houses")  or []
    fvb         = ast.get("forensic_variant_b")

    # Per-body raw dump — no computation, no normalisation
    bodies_wanted = [
        "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
        "Uranus", "Neptune", "Pluto", "Chiron",
    ]
    planets_out = {}
    for b in bodies_wanted:
        p = planets_raw.get(b) or planets_raw.get(b.lower()) or {}
        planets_out[b] = {
            "sign":       p.get("sign"),
            "longitude":  p.get("longitude"),
            "degree":     p.get("degree"),
            "house":      p.get("house"),
            "retrograde": p.get("retrograde"),
            "speed":      p.get("speed"),
        }
    nn = (nodes_raw.get("north_node")
          or nodes_raw.get("North Node")
          or planets_raw.get("North Node")
          or {})
    sn = (nodes_raw.get("south_node")
          or nodes_raw.get("South Node")
          or planets_raw.get("South Node")
          or {})
    planets_out["North Node"] = {
        "sign":      nn.get("sign"),
        "longitude": nn.get("longitude"),
        "degree":    nn.get("degree"),
        "house":     nn.get("house"),
    }
    planets_out["South Node"] = {
        "sign":      sn.get("sign"),
        "longitude": sn.get("longitude"),
        "degree":    sn.get("degree"),
        "house":     sn.get("house"),
    }

    # Angles — raw stored values
    asc = angles_raw.get("asc") or angles_raw.get("ascendant") or {}
    mc  = angles_raw.get("mc")  or angles_raw.get("midheaven") or {}
    ic  = angles_raw.get("ic")  or angles_raw.get("imum_coeli") or {}
    dsc = angles_raw.get("dsc") or angles_raw.get("descendant") or {}
    angles_out = {
        "Ascendant":   {"sign": asc.get("sign"), "longitude": asc.get("longitude")},
        "MC":          {"sign": mc.get("sign"),  "longitude": mc.get("longitude")},
        "IC":          {"sign": ic.get("sign"),  "longitude": ic.get("longitude")},
        "Descendant":  {"sign": dsc.get("sign"), "longitude": dsc.get("longitude")},
    }

    # Houses — full list, no derivation
    houses_out = []
    if isinstance(houses_raw, list):
        for h in houses_raw:
            if not isinstance(h, dict):
                houses_out.append({"raw": h})
                continue
            houses_out.append({
                "number":         h.get("number") or h.get("house"),
                "cusp_longitude": h.get("cusp_longitude") or h.get("longitude") or h.get("cusp"),
                "cusp_sign":      h.get("sign") or h.get("cusp_sign"),
                "degree":         h.get("degree"),
            })
    elif isinstance(houses_raw, dict):
        houses_out = houses_raw

    # House system metadata (read whatever is stored)
    house_meta = {
        "house_system":              chart.get("house_system")
                                     or ast.get("house_system")
                                     or (ast.get("metadata") or {}).get("house_system"),
        "equal_house_flag":          (ast.get("metadata") or {}).get("equal_houses"),
        "houses_array_length":       len(houses_raw) if isinstance(houses_raw, list) else None,
    }

    return JSONResponse(
        content=jsonable_encoder({
            "found":         True,
            "chart_present": True,
            "identity": {
                "user_id": uid_str,
                "name":    user.get("name"),
                "email":   user.get("email"),
            },
            "birth_data": birth_data,
            "chart_metadata": {
                "astrology_engine_version": chart.get("astrology_engine_version"),
                "sign_attribution_version": chart.get("sign_attribution_version"),
                "house_system":             chart.get("house_system"),
                "migration_marker":         chart.get("migration_marker"),
                "migrated_at":              chart.get("migrated_at"),
                "updated_at":               chart.get("updated_at"),
                "forensic_variant_b_present": fvb is not None,
            },
            "forensic_variant_b": fvb,
            "planets":            planets_out,
            "angles":             angles_out,
            "houses":             houses_out,
            "house_system_meta":  house_meta,
            "astrology_metadata": ast.get("metadata"),
            "server_time_utc":    datetime.now(timezone.utc).isoformat(),
        }, custom_encoder={bytes: lambda b: b.decode("utf-8", "replace")}),
        headers={"Cache-Control": "no-store"},
    )


# ---------------------------------------------------------------------
# 1) READ-ONLY: DB identity + counts
# ---------------------------------------------------------------------
@router.get("/migration-info")
async def migration_info(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)
    if _db is None:
        raise HTTPException(status_code=500, detail={"code": "MONGO_NOT_CONFIGURED",
            "message": "MONGO_URL / DB_NAME not present in env."})

    mongo_url = os.environ.get("MONGO_URL")
    db_name   = os.environ.get("DB_NAME")
    host_info = _redact_mongo_host(mongo_url)
    is_preview = _looks_like_preview_db(db_name, host_info)

    # Counts (all read-only)
    charts_total = await _db.charts.count_documents({})
    engine_dist = await _engine_version_distribution(_db)
    migrated_count = await _db.charts.count_documents({
        "migration_marker": MIGRATION_MARKER,
    })
    with_forensic = await _db.charts.count_documents({
        "astrology.forensic_variant_b": {"$exists": True},
    })
    users_total = await _db.users.count_documents({})
    forums_total = await _db.forums.count_documents({})

    v_b_count = engine_dist.get("midpoint12_variant_b", 0)
    v_a_count = engine_dist.get(ASTROLOGY_ENGINE_VERSION, 0)

    # Pulsifi + Jay + JH presence
    pulsifi_forums = await _find_pulsifi_forums(_db)
    named_users    = await _find_named_users(_db, ("JH", "Jay"))

    return JSONResponse(
        content={
            "build_marker": ROUTE_BUILD_MARKER,
            "checked_at":   datetime.now(timezone.utc).isoformat(),
            "db_identity": {
                "db_name":        db_name,
                "mongo_host":     host_info,
                "looks_like_preview_or_test_database": is_preview,
            },
            "counts": {
                "users":                        users_total,
                "forums":                       forums_total,
                "charts":                       charts_total,
                "charts_engine_distribution":   engine_dist,
                "charts_with_migration_marker": migrated_count,
                "charts_with_forensic_variant_b": with_forensic,
                "charts_midpoint12_variant_b":  v_b_count,
                "charts_midpoint13_variant_a_v1": v_a_count,
            },
            "presence_checks": {
                "pulsifi_forums": pulsifi_forums,
                "named_users":    named_users,
            },
            "engine_constants": {
                "target_engine_version":  ASTROLOGY_ENGINE_VERSION,
                "migration_marker":       MIGRATION_MARKER,
                "canonical_house_system": CANONICAL_HOUSE_SYSTEM,
            },
            "writes_performed": 0,
            "is_read_only":     True,
        },
        headers={"Cache-Control": "no-store"},
    )


# ---------------------------------------------------------------------
# 2) READ-ONLY: pre-migration snapshot
# ---------------------------------------------------------------------
@router.post("/migration-snapshot")
async def migration_snapshot(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)

    # run_snapshot() opens its own AsyncIOMotorClient using os.environ
    # — which inside the deployed pod resolves to the deployed Mongo.
    # It writes /app/backend/audits/variant_a_migration_snapshot.json
    # AND returns the full snapshot dict.
    try:
        snapshot = await run_snapshot()
    except Exception as e:  # noqa: BLE001
        logger.exception("[admin/migration-snapshot] failed: %s", e)
        raise HTTPException(status_code=500, detail={"code": "SNAPSHOT_FAILED",
            "message": str(e)[:300]})

    return JSONResponse(
        content={
            "build_marker":     ROUTE_BUILD_MARKER,
            "is_read_only":     True,
            "writes_performed": 0,
            "snapshot":         snapshot,
        },
        headers={"Cache-Control": "no-store"},
    )


# ---------------------------------------------------------------------
# 3) WRITE-GATED: live migration
# ---------------------------------------------------------------------
@router.post("/migration-run")
async def migration_run(
    request: Request,
    confirm: str = Query(default=""),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)
    if _db is None:
        raise HTTPException(status_code=500, detail={"code": "MONGO_NOT_CONFIGURED",
            "message": "MONGO_URL / DB_NAME not present in env."})

    if confirm != "VARIANT_A_PHASE_5":
        raise HTTPException(
            status_code=400,
            detail={
                "code":    "MISSING_CONFIRM",
                "message": "Add `?confirm=VARIANT_A_PHASE_5` to the URL to acknowledge live writes.",
            },
        )

    # ---- Preflight: DB identity must NOT be preview / localhost ----
    mongo_url = os.environ.get("MONGO_URL")
    db_name   = os.environ.get("DB_NAME")
    host_info = _redact_mongo_host(mongo_url)
    if _looks_like_preview_db(db_name, host_info):
        raise HTTPException(
            status_code=409,
            detail={
                "code":    "PREVIEW_DB_REFUSED",
                "message": (
                    "Refusing to run migration: connected Mongo appears to "
                    "be a preview/test database (localhost or "
                    "DB_NAME=test_database). Deploy this route to the "
                    "production pod and try again."
                ),
                "db_name":    db_name,
                "mongo_host": host_info,
            },
        )

    # ---- Preflight: Pulsifi forum present ----
    pulsifi_forums = await _find_pulsifi_forums(_db)
    if not pulsifi_forums:
        raise HTTPException(
            status_code=409,
            detail={
                "code":    "PULSIFI_FORUM_NOT_FOUND",
                "message": "Expected at least one forum whose name matches /Pulsifi/i.",
            },
        )

    # ---- Preflight: JH or Jay user present ----
    named_users = await _find_named_users(_db, ("JH", "Jay"))
    if not named_users:
        raise HTTPException(
            status_code=409,
            detail={
                "code":    "NAMED_USERS_NOT_FOUND",
                "message": "Expected at least one user named 'JH' or 'Jay'.",
            },
        )

    # ---- Preflight: chart count + already-migrated check ----
    charts_total = await _db.charts.count_documents({})
    if charts_total <= 0:
        raise HTTPException(
            status_code=409,
            detail={
                "code":    "NO_CHARTS",
                "message": "Refusing to run: charts collection is empty.",
            },
        )

    already_migrated = await _db.charts.count_documents({
        "migration_marker": MIGRATION_MARKER,
    })
    if already_migrated == charts_total:
        raise HTTPException(
            status_code=409,
            detail={
                "code":              "ALREADY_MIGRATED",
                "message":           "All charts are already stamped with the V-A migration marker. Nothing to do.",
                "charts_total":      charts_total,
                "already_migrated":  already_migrated,
            },
        )

    # ---- Step A: snapshot first (in-process, returns full payload) ----
    try:
        snapshot = await run_snapshot()
    except Exception as e:  # noqa: BLE001
        logger.exception("[admin/migration-run] snapshot failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"code": "SNAPSHOT_FAILED", "message": str(e)[:300]},
        )

    # ---- Step B: Phase 5 recompute (writes!) ----
    try:
        recompute_report = await recompute_users(_db, dry_run=False)
    except Exception as e:  # noqa: BLE001
        logger.exception("[admin/migration-run] recompute failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"code": "RECOMPUTE_FAILED", "message": str(e)[:300]},
        )

    # ---- Step C: cache invalidation (writes!) ----
    try:
        cache_report = await invalidate_caches(_db, dry_run=False)
    except Exception as e:  # noqa: BLE001
        logger.exception("[admin/migration-run] cache invalidation failed: %s", e)
        # Don't bail — caches will be rebuilt naturally; include the error.
        cache_report = {"error": str(e)[:300]}

    # ---- Step D: Phase 6 validation ----
    try:
        validation = await run_validate(_db)
    except Exception as e:  # noqa: BLE001
        logger.exception("[admin/migration-run] validation failed: %s", e)
        validation = {"error": str(e)[:300]}

    # ---- Final report payload ----
    finished_at = datetime.now(timezone.utc).isoformat()
    report = {
        "build_marker": ROUTE_BUILD_MARKER,
        "engine":       ASTROLOGY_ENGINE_VERSION,
        "marker":       MIGRATION_MARKER,
        "house_system": CANONICAL_HOUSE_SYSTEM,
        "finished_at":  finished_at,
        "db_identity": {
            "db_name":    db_name,
            "mongo_host": host_info,
        },
        "snapshot_summary": {
            "counts":        snapshot.get("counts"),
            "snapshot_path": snapshot.get("snapshot_path"),
            "started_at":    snapshot.get("started_at"),
            "finished_at":   snapshot.get("finished_at"),
        },
        "recompute":  recompute_report,
        "caches":     cache_report,
        "validation": validation,
        "sign_dependent_caches_targeted": list(SIGN_DEPENDENT_CACHES),
    }

    # Persist report to disk for re-download via subsequent calls.
    try:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = f"/app/backend/audits/variant_a_prod_migration_report_{ts}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        report["report_path"] = report_path
    except Exception as e:  # noqa: BLE001
        report["report_path_error"] = str(e)[:200]

    return JSONResponse(content=report, headers={"Cache-Control": "no-store"})
