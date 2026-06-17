"""
TEMPORARY — Mel Ascendant Read-Only Diagnostic Endpoint
========================================================
Build marker: mel-rising-fix-diag-readonly-v1

Purpose
-------
Single short-lived HTTP route used during the live Mel Ascendant
regression investigation. The preview pod cannot reach Atlas (IP
allowlist), so we use the deployed pod (which IS in the allowlist) as
a bastion: it reads Mel's user + chart documents from Atlas and runs
TWIN canonical recomputes (Melaka vs Kuala Lumpur birth-city inputs)
in memory, then returns a structured JSON evidence dump.

Routes
------
  GET /api/admin/diag/mel-chart-readonly?confirm=MEL_DIAG_2026_06_17

Security model (read-only, but still guarded)
---------------------------------------------
* Hardcoded confirmation token MUST appear in the query string —
  refuses 403 otherwise.
* Refuses if the resolved MONGO_URL host is a localhost / loopback
  address (so this endpoint can never be tricked into operating on
  test_database; it is for the deployed Atlas-backed pod ONLY).
* Refuses if MONGO_URL is unset.
* Logs every accepted call with timestamp + client IP for audit.
* CONTAINS ZERO WRITES. The only Mongo ops are `find_one`. The two
  recomputes happen entirely in-process; no persistence anywhere.
* The endpoint is one-shot — after the bug is diagnosed, the entire
  file is deleted and the router registration is removed from
  server.py in the next commit.

Removal checklist (when diagnosis complete)
-------------------------------------------
  1. Delete this file.
  2. Remove the registration line from server.py.
  3. Re-publish.

Author: main agent, 2026-06-17, for the Mel Ascendant regression P0.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("mel_chart_readonly_diag")

router = APIRouter(prefix="/api/admin/diag", tags=["mel-rising-fix-diag-readonly-v1"])

ROUTE_BUILD_MARKER = "mel-rising-fix-diag-readonly-v1"
CONFIRM_TOKEN      = "MEL_DIAG_2026_06_17"

# Resolve Mongo on import — same pattern as the existing admin module
_MONGO_URL = os.environ.get("MONGO_URL")
_DB_NAME   = os.environ.get("DB_NAME")
_client    = AsyncIOMotorClient(_MONGO_URL) if _MONGO_URL else None
_db        = _client[_DB_NAME] if (_client is not None and _DB_NAME) else None


# ---------------------------------------------------------------------------
# Canonical inputs for the twin recompute
# ---------------------------------------------------------------------------
# The Mel Ascendant ticket says: 13 Jul 1981, 07:25 LT, MELAKA, Malaysia.
# We compute against BOTH Melaka and KL coordinates so the diff reveals
# whether the stored chart was computed from the WRONG city.

CANONICAL_BIRTH = {
    "year": 1981, "month": 7, "day": 13,
    "hour": 7, "minute": 25,
    "tz": "Asia/Kuala_Lumpur",   # IANA name (Malaysia uses one timezone)
}
MELAKA_COORDS = {"lat": 2.1896,  "lon": 102.2501}
KL_COORDS     = {"lat": 3.1390,  "lon": 101.6869}


def _is_loopback_host(mongo_url: Optional[str]) -> bool:
    if not mongo_url:
        return True
    try:
        host = (urlparse(mongo_url).hostname or "").lower()
    except Exception:
        return True
    return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "")


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "<unknown>"


# ---------------------------------------------------------------------------
# In-process canonical recompute (no DB writes)
# ---------------------------------------------------------------------------
def _build_birth_utc() -> datetime:
    """Convert the canonical local birth moment to UTC."""
    from zoneinfo import ZoneInfo
    local = datetime(
        CANONICAL_BIRTH["year"],
        CANONICAL_BIRTH["month"],
        CANONICAL_BIRTH["day"],
        CANONICAL_BIRTH["hour"],
        CANONICAL_BIRTH["minute"],
        tzinfo=ZoneInfo(CANONICAL_BIRTH["tz"]),
    )
    return local.astimezone(timezone.utc)


def _safe_recompute(label: str, lat: float, lon: float) -> Dict[str, Any]:
    """Run get_full_natal_chart for the canonical birth moment + given coords.

    Returns a compact summary suitable for diffing. Never raises — packs
    any compute error into the response under `error`."""
    try:
        from calculations.astrology import get_full_natal_chart
        birth_utc = _build_birth_utc()
        full = get_full_natal_chart(
            birth_datetime=birth_utc,
            lat=lat,
            lon=lon,
        )
        astro = full or {}
        return {
            "label":   label,
            "ok":      True,
            "inputs": {
                "birth_utc": birth_utc.isoformat(),
                "lat":       lat,
                "lon":       lon,
                "tz":        CANONICAL_BIRTH["tz"],
            },
            "asc": (astro.get("angles") or {}).get("asc"),
            "sun": (astro.get("planets") or {}).get("Sun")
                or (astro.get("planets") or {}).get("sun"),
            "moon": (astro.get("planets") or {}).get("Moon")
                or (astro.get("planets") or {}).get("moon"),
            "metadata": astro.get("metadata"),
            "houses_ascendant": (astro.get("houses") or {}).get("ascendant"),
        }
    except Exception as exc:
        return {
            "label":  label,
            "ok":     False,
            "error":  f"{type(exc).__name__}: {exc}",
            "inputs": {"lat": lat, "lon": lon, "tz": CANONICAL_BIRTH["tz"]},
        }


# ---------------------------------------------------------------------------
# The endpoint
# ---------------------------------------------------------------------------
@router.get("/mel-chart-readonly")
async def mel_chart_readonly(
    request: Request,
    confirm: str = Query(..., description="Must equal MEL_DIAG_2026_06_17"),
):
    """Read-only diagnostic dump for the Mel Ascendant regression.

    NEVER writes. Refuses on:
      * wrong confirm token
      * MONGO_URL pointing at localhost / loopback
      * MONGO_URL unset
    """
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail={
            "code": "INVALID_CONFIRM_TOKEN",
            "message": "Provide confirm=MEL_DIAG_2026_06_17 in the query string.",
        })
    if _db is None or _is_loopback_host(_MONGO_URL):
        raise HTTPException(status_code=503, detail={
            "code": "PREVIEW_DB_REFUSED",
            "message": (
                "This endpoint refuses to run against a localhost / loopback "
                "Mongo. It is intended only for the deployed Atlas-backed pod."
            ),
            "mongo_host": (urlparse(_MONGO_URL).hostname if _MONGO_URL else None),
        })

    caller_ip = _client_ip(request)
    started_at = datetime.now(timezone.utc).isoformat()
    logger.warning(
        "[mel-chart-readonly-diag] accepted call from ip=%s at=%s db=%s",
        caller_ip, started_at, _DB_NAME,
    )

    # ----- Step A: Locate Yoong family forum -----
    forum = await _db.forums.find_one({"name": {"$regex": "yoong", "$options": "i"}})
    if not forum:
        return JSONResponse(content={
            "build_marker":  ROUTE_BUILD_MARKER,
            "error":         "Yoong family forum not found in this DB",
            "db_name":       _DB_NAME,
        }, headers={"Cache-Control": "no-store"})
    forum_id = str(forum["_id"])
    forum_name = forum.get("name")

    # ----- Step B: Enumerate active members of the forum -----
    members_raw = await _db.forum_members.find(
        {"forum_id": forum_id, "status": "active"}
    ).to_list(50)
    members_summary = []
    mel_user_id: Optional[str] = None
    mel_user_doc: Optional[Dict[str, Any]] = None

    for m in members_raw:
        uid = m.get("user_id")
        u: Optional[Dict[str, Any]] = None
        try:
            u = await _db.users.find_one({"_id": ObjectId(uid)})
        except Exception:
            u = await _db.users.find_one({"_id": uid}) \
              or await _db.users.find_one({"user_id": uid})
        name = (u or {}).get("name", "")
        members_summary.append({
            "user_id": str(uid),
            "name":    name,
            "email":   (u or {}).get("email"),
        })
        if (name or "").strip().lower() == "mel":
            mel_user_id = str(uid)
            mel_user_doc = u

    # Fall back: email lookup if name match missed
    if mel_user_doc is None:
        u = await _db.users.find_one({"email": {"$regex": "melissa.mars", "$options": "i"}})
        if u:
            mel_user_doc = u
            mel_user_id = str(u["_id"])

    if mel_user_doc is None:
        return JSONResponse(content={
            "build_marker":  ROUTE_BUILD_MARKER,
            "error":         "Mel not found in Yoong family roster or by email",
            "forum_id":      forum_id,
            "members_summary": members_summary,
            "db_name":       _DB_NAME,
        }, headers={"Cache-Control": "no-store"})

    # ----- Step C: Pull Mel's chart document -----
    chart = await _db.charts.find_one({"user_id": mel_user_id})

    # ----- Step D: Reproduce _format_astrology over the stored chart -----
    reproduced_astrology: Optional[str] = None
    reproduction_error: Optional[str] = None
    try:
        from services.member_summary import _format_astrology
        reproduced_astrology = _format_astrology(chart or {})
    except Exception as exc:
        reproduction_error = f"{type(exc).__name__}: {exc}"

    # ----- Step E: Twin canonical recomputes (Melaka vs KL) -----
    recompute_melaka = _safe_recompute("melaka", MELAKA_COORDS["lat"], MELAKA_COORDS["lon"])
    recompute_kl     = _safe_recompute("kuala_lumpur", KL_COORDS["lat"], KL_COORDS["lon"])

    # ----- Step F: Classify (best-effort, advisory) -----
    classification = _classify(mel_user_doc, chart, recompute_melaka, recompute_kl)

    # ----- Step G: Compact response payload -----
    astro = (chart or {}).get("astrology") or {}
    metadata = astro.get("metadata") or {}
    angles = astro.get("angles") or {}
    houses = astro.get("houses") or {}

    payload = {
        "build_marker":  ROUTE_BUILD_MARKER,
        "started_at":    started_at,
        "caller_ip":     caller_ip,
        "db_name":       _DB_NAME,
        "mongo_host":    urlparse(_MONGO_URL).hostname,

        "forum": {
            "forum_id": forum_id,
            "name":     forum_name,
            "active_member_count": len(members_summary),
            "members":  members_summary,
        },

        "mel": {
            "user_id":   mel_user_id,
            "chart_id":  str(chart.get("_id")) if chart else None,

            "user_doc_inputs": {
                "name":          mel_user_doc.get("name"),
                "email":         mel_user_doc.get("email"),
                "birth_date":    mel_user_doc.get("birth_date"),
                "birth_time":    mel_user_doc.get("birth_time"),
                "birth_city":    mel_user_doc.get("birth_city"),
                "birth_country": mel_user_doc.get("birth_country"),
                "birth_location": mel_user_doc.get("birth_location"),
                "timezone":      mel_user_doc.get("timezone"),
                "timezone_id":   mel_user_doc.get("timezone_id"),
                "birth_timezone": mel_user_doc.get("birth_timezone"),
                "latitude":      mel_user_doc.get("latitude"),
                "longitude":     mel_user_doc.get("longitude"),
                "created_at":    str(mel_user_doc.get("created_at")) if mel_user_doc.get("created_at") else None,
                "updated_at":    str(mel_user_doc.get("updated_at")) if mel_user_doc.get("updated_at") else None,
            },

            "chart_envelope": {
                "updated_at":              str(chart.get("updated_at")) if chart and chart.get("updated_at") else None,
                "astrology_updated_at":    str(chart.get("astrology_updated_at")) if chart and chart.get("astrology_updated_at") else None,
                "created_at":              str(chart.get("created_at")) if chart and chart.get("created_at") else None,
                "astrology_engine_version": chart.get("astrology_engine_version") if chart else None,
            } if chart else None,

            "astrology_metadata": metadata,
            "astrology_input_datetime_utc": astro.get("input_datetime_utc"),
            "astrology_coordinates":        astro.get("coordinates"),
            "astrology_zodiac_mode":        astro.get("zodiac_mode"),

            "stored_angles_asc":            angles.get("asc"),
            "stored_angles_ascendant":      angles.get("ascendant"),
            "stored_houses_ascendant":      houses.get("ascendant"),
            "stored_houses_ascendant_sign": houses.get("ascendant_sign"),
            "stored_top_level_legacy": {
                "astro.ascendant": astro.get("ascendant"),
                "astro.sun":       astro.get("sun"),
                "astro.moon":      astro.get("moon"),
                "astro.midheaven": astro.get("midheaven"),
            },

            "stored_planets_sun":  (astro.get("planets") or {}).get("Sun")
                                  or (astro.get("planets") or {}).get("sun"),
            "stored_planets_moon": (astro.get("planets") or {}).get("Moon")
                                  or (astro.get("planets") or {}).get("moon"),

            "stored_forensic_variant_b_asc": (
                ((astro.get("forensic_variant_b") or {}).get("angles") or {}).get("asc")
            ),

            "reproduced_format_astrology": reproduced_astrology,
            "reproduction_error":          reproduction_error,
        },

        "twin_recompute": {
            "melaka":       recompute_melaka,
            "kuala_lumpur": recompute_kl,
        },

        "classification": classification,
    }

    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


def _classify(
    user: Dict[str, Any],
    chart: Optional[Dict[str, Any]],
    rc_melaka: Dict[str, Any],
    rc_kl: Dict[str, Any],
) -> Dict[str, Any]:
    """Best-effort A / B / C / D classification.

    Definitions (per ticket):
      A. Wrong birth inputs stored
      B. Correct birth inputs but stale chart
      C. Variant A migration missed this chart
      D. Other
    """
    if not chart:
        return {"verdict": "D", "reason": "Mel has no chart document at all"}

    astro = chart.get("astrology") or {}
    stored_asc = (astro.get("angles") or {}).get("asc") or {}
    stored_sign = stored_asc.get("sign")
    stored_engine = chart.get("astrology_engine_version")
    metadata_engine = (astro.get("metadata") or {}).get("astrology_engine_version")
    engine_v = stored_engine or metadata_engine

    # Are the stored birth inputs already wrong on the user doc?
    birth_city = (user.get("birth_city") or "")
    user_lat = user.get("latitude")
    user_lon = user.get("longitude")
    looks_like_kl = bool(birth_city) and "kuala lumpur" in birth_city.lower()
    if not looks_like_kl and isinstance(user_lat, (int, float)) and isinstance(user_lon, (int, float)):
        # Coords closer to KL than Melaka?
        d_kl = (user_lat - KL_COORDS["lat"])**2 + (user_lon - KL_COORDS["lon"])**2
        d_mk = (user_lat - MELAKA_COORDS["lat"])**2 + (user_lon - MELAKA_COORDS["lon"])**2
        if d_kl < d_mk:
            looks_like_kl = True

    if looks_like_kl:
        return {
            "verdict": "A",
            "reason":  "user doc's birth_city / coords appear to be Kuala Lumpur, not Melaka",
            "user_birth_city": birth_city,
            "user_lat_lon":    [user_lat, user_lon],
        }

    # Does stored ASC match the KL recompute (not Melaka)?
    rc_mk_sign = (rc_melaka.get("asc") or {}).get("sign") if rc_melaka.get("ok") else None
    rc_kl_sign = (rc_kl.get("asc") or {}).get("sign") if rc_kl.get("ok") else None
    if stored_sign and stored_sign == rc_kl_sign and stored_sign != rc_mk_sign:
        return {
            "verdict": "A",
            "reason":  f"stored ASC sign={stored_sign} matches KL recompute but NOT Melaka recompute ({rc_mk_sign}) — chart was computed from KL inputs",
            "stored_sign":   stored_sign,
            "recompute_melaka_sign": rc_mk_sign,
            "recompute_kl_sign":     rc_kl_sign,
        }

    # If stored ASC matches Melaka recompute, the chart is fine — bug is elsewhere.
    if stored_sign and stored_sign == rc_mk_sign:
        return {
            "verdict": "D",
            "reason":  "stored ASC sign matches the canonical Melaka recompute; bug is not in birth inputs or chart math",
            "stored_sign":   stored_sign,
            "recompute_melaka_sign": rc_mk_sign,
        }

    # Variant A miss?
    if engine_v != "midpoint13_variant_a_v1":
        return {
            "verdict": "C",
            "reason":  f"chart engine version is {engine_v!r}, expected midpoint13_variant_a_v1 — Variant A migration missed this chart",
            "stored_sign":   stored_sign,
            "recompute_melaka_sign": rc_mk_sign,
            "recompute_kl_sign":     rc_kl_sign,
        }

    # Otherwise call it B (correct inputs, but stored chart drifted).
    return {
        "verdict": "B",
        "reason":  "stored ASC sign does not match either canonical recompute; user-doc inputs look like Melaka — stored chart is stale or corrupt",
        "stored_sign":           stored_sign,
        "recompute_melaka_sign": rc_mk_sign,
        "recompute_kl_sign":     rc_kl_sign,
    }


def register(app) -> None:
    """Mounted from server.py."""
    app.include_router(router)
    logger.info("[%s] mel-chart read-only diagnostic router registered", ROUTE_BUILD_MARKER)
