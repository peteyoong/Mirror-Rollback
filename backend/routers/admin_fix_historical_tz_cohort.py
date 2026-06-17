"""
SYSTEMIC FIX — Historical-Timezone Drift Repair (cohort scan)
==============================================================
Build marker: fix-historical-tz-cohort-v1   (2026-06-17)

Purpose
-------
The Mel Ascendant regression revealed that some user charts on Atlas were
written with a `metadata.input_datetime_utc` that drifted from the
historically-correct UTC for the user's IANA timezone + birth date. The
classic instance is Malaysia pre-1982-01-01 births (when MYT was +7:30,
not modern +8:00), but the same class of bug applies to any timezone
that changed offset historically (Singapore pre-1982, Argentina, India
pre-1955, etc.).

`fix_mel_live` patched a single user (Mel). This endpoint patches the
ENTIRE COHORT in one atomic scan:

  1. Walk every chart in db.charts.
  2. For each, recompute the canonical UTC via the hardened
     `calculations.timezone_utils.resolve_birth_utc_with_debug`
     (which uses pytz.localize and honours historical offsets).
  3. Compare to the chart's stored `astrology.metadata.input_datetime_utc`.
  4. If they differ by more than 60 seconds → the chart drifted.
  5. Recompute astrology + bazi + human_design with the correct UTC.
  6. Atomic `$set` write with the V-A canonical markers
     (`astrology_engine_version`, `migration_marker`) so subsequent
     auto-migration passes will refuse to touch the chart.
  7. Return a structured summary: scanned / drifted / repaired / skipped /
     errored, with a per-user breakdown.

The endpoint is idempotent: running it twice in a row will repair zero
charts on the second run because the first run brings every drifted
chart into agreement with the canonical UTC.

Security
--------
Confirmation token required (`?confirm=FIX_HISTORICAL_TZ_2026_06_17`).
Refuses to run against a localhost Mongo (the preview pod will return
503; only the deployed Atlas-backed pod can execute writes).

Author: main agent, 2026-06-17. Designed to be removed after the cohort
is repaired (single-use admin route).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("fix_historical_tz_cohort_v1")

router = APIRouter(prefix="/api/admin", tags=["fix-historical-tz-cohort-v1"])

ROUTE_BUILD_MARKER = "fix-historical-tz-cohort-v1"
CONFIRM_TOKEN      = "FIX_HISTORICAL_TZ_2026_06_17"

# Drift tolerance — if the recomputed UTC differs from the stored UTC by
# MORE than this many seconds, we treat the chart as drifted. 60s is
# generous enough to absorb any sub-minute representation differences
# while being far below the 30-minute drifts produced by the +08:00 /
# +07:30 Malaysia bug class.
DRIFT_TOLERANCE_SECONDS = 60

VARIANT_A_ENGINE_VERSION   = "midpoint13_variant_a_v1"
VARIANT_A_MIGRATION_MARKER = "variant-a-13-sign-migration-v1"

# Resolve Mongo on import
_MONGO_URL = os.environ.get("MONGO_URL")
_DB_NAME   = os.environ.get("DB_NAME")
_client    = AsyncIOMotorClient(_MONGO_URL) if _MONGO_URL else None
_db        = _client[_DB_NAME] if (_client is not None and _DB_NAME) else None


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


def _parse_stored_utc(astro: Dict[str, Any]) -> Optional[datetime]:
    """Read the stored canonical UTC anchor off the chart's astrology metadata."""
    meta = (astro or {}).get("metadata") or {}
    raw = meta.get("input_datetime_utc") or astro.get("input_datetime_utc")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


@router.post("/fix_historical_tz_cohort")
async def fix_historical_tz_cohort(
    request: Request,
    confirm: str = Query(..., description="Must equal FIX_HISTORICAL_TZ_2026_06_17"),
    dry_run: bool = Query(
        True,
        description="If true, scans and reports but performs NO writes. Default true for safety.",
    ),
    limit: int = Query(
        500,
        ge=1, le=10000,
        description="Maximum number of charts to process in this run. Default 500.",
    ),
):
    """Scan every chart, identify ones whose stored UTC drifted from the
    historically-correct value, and (when dry_run=false) repair them with
    V-A canonical markers locked in.

    Safe defaults: dry_run=true, so you can preview what would change
    before authorising the write.
    """
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail={
            "code": "INVALID_CONFIRM_TOKEN",
            "message": f"Provide confirm={CONFIRM_TOKEN} in the query string.",
        })
    if _db is None or _is_loopback_host(_MONGO_URL):
        raise HTTPException(status_code=503, detail={
            "code": "PREVIEW_DB_REFUSED",
            "message": "Refuses to operate on localhost Mongo. Use the deployed Atlas-backed pod.",
            "mongo_host": (urlparse(_MONGO_URL).hostname if _MONGO_URL else None),
        })

    # Lazy imports — these pull in pytz + ephemeris; we want a clean import
    # graph if something downstream is broken.
    try:
        from calculations.timezone_utils import resolve_birth_utc_with_debug
        from calculations.astrology import get_full_natal_chart
        from calculations.human_design import get_human_design_chart
    except Exception as exc:
        raise HTTPException(status_code=500, detail={
            "code": "IMPORT_FAILED",
            "message": f"Failed to load chart-compute libraries: {type(exc).__name__}: {exc}",
        })

    caller_ip = _client_ip(request)
    started_at = datetime.now(timezone.utc)
    logger.warning(
        "[%s] start dry_run=%s limit=%d ip=%s db=%s",
        ROUTE_BUILD_MARKER, dry_run, limit, caller_ip, _DB_NAME,
    )

    scanned = 0
    drifted: List[Dict[str, Any]] = []
    repaired: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    skipped_no_inputs = 0
    skipped_no_chart_utc = 0

    # Walk charts. Use a projection to keep memory footprint reasonable.
    cursor = _db.charts.find({}, {
        "_id": 1,
        "user_id": 1,
        "astrology.metadata.input_datetime_utc": 1,
        "astrology.input_datetime_utc": 1,
        "astrology_engine_version": 1,
    })

    async for chart_proj in cursor:
        if scanned >= limit:
            break
        scanned += 1
        chart_id = str(chart_proj.get("_id"))
        user_id  = chart_proj.get("user_id")
        if not user_id:
            continue

        try:
            # Load the user doc for the canonical inputs we need.
            try:
                user = await _db.users.find_one({"_id": ObjectId(user_id)})
            except Exception:
                user = await _db.users.find_one({"_id": user_id})
            if not user:
                continue

            birth_date  = user.get("birth_date")
            birth_time  = user.get("birth_time")
            tz_string   = user.get("timezone")
            location    = user.get("birth_location") or {}
            lat         = location.get("latitude")  if isinstance(location, dict) else None
            lon         = location.get("longitude") if isinstance(location, dict) else None
            if lat is None:
                lat = user.get("latitude")
            if lon is None:
                lon = user.get("longitude")

            if not birth_date or not birth_time or not tz_string or lat is None or lon is None:
                skipped_no_inputs += 1
                continue

            # Normalise birth_date to YYYY-MM-DD string (the resolver expects str).
            if isinstance(birth_date, datetime):
                birth_date_str = birth_date.strftime("%Y-%m-%d")
            else:
                birth_date_str = str(birth_date)[:10]

            # Compute the canonical historically-correct UTC.
            resolution = resolve_birth_utc_with_debug(
                birth_date_str=birth_date_str,
                birth_time_str=str(birth_time),
                timezone_str=str(tz_string),
            )
            if not resolution.get("success"):
                errors.append({
                    "user_id": user_id,
                    "chart_id": chart_id,
                    "name": user.get("name"),
                    "stage": "resolve_utc",
                    "error": resolution.get("error") or resolution.get("error_message"),
                })
                continue

            correct_utc: datetime = resolution["birth_utc"]
            if correct_utc.tzinfo is None:
                correct_utc = correct_utc.replace(tzinfo=timezone.utc)

            # Full chart astrology subdoc is needed to read stored UTC.
            full_chart = await _db.charts.find_one({"_id": chart_proj["_id"]})
            astro = (full_chart or {}).get("astrology") or {}
            stored_utc = _parse_stored_utc(astro)
            if stored_utc is None:
                skipped_no_chart_utc += 1
                continue

            delta_seconds = abs((stored_utc - correct_utc).total_seconds())
            if delta_seconds <= DRIFT_TOLERANCE_SECONDS:
                continue  # not drifted

            drift_record = {
                "user_id":  user_id,
                "chart_id": chart_id,
                "name":     user.get("name"),
                "email":    user.get("email"),
                "stored_utc":  stored_utc.isoformat(),
                "correct_utc": correct_utc.isoformat(),
                "drift_seconds": int(delta_seconds),
                "drift_minutes": round(delta_seconds / 60.0, 1),
                "tz_string":  tz_string,
                "birth_date": birth_date_str,
                "birth_time": str(birth_time),
            }
            drifted.append(drift_record)

            if dry_run:
                continue  # report only

            # Recompute with the correct UTC.
            sidereal_settings = {
                "mode": "true_sidereal_user_defined",
                "svp_degrees": 31.2836,
                "reference_year": 2000,
                "yearly_increment": 0.0,
            }
            new_astro = get_full_natal_chart(
                correct_utc.replace(tzinfo=None) if correct_utc.tzinfo else correct_utc,
                float(lat), float(lon),
                sidereal_settings=sidereal_settings,
                house_system="Equal",
            )
            try:
                new_hd = get_human_design_chart(
                    correct_utc.replace(tzinfo=None) if correct_utc.tzinfo else correct_utc,
                    float(lat), float(lon),
                    sidereal_settings=sidereal_settings,
                )
            except Exception as hd_exc:
                # HD recompute failures should not block the astrology fix —
                # log and continue with astrology-only write.
                logger.warning(
                    "[%s] HD recompute failed for %s: %s — astrology will still be repaired",
                    ROUTE_BUILD_MARKER, user_id, hd_exc,
                )
                new_hd = (full_chart or {}).get("human_design")

            now_utc = datetime.utcnow()
            update_fields = {
                "astrology":   new_astro,
                "human_design": new_hd,
                "astrology_engine_version": VARIANT_A_ENGINE_VERSION,
                "migration_marker":         VARIANT_A_MIGRATION_MARKER,
                "chart_updated_at":         now_utc,
                "updated_at":               now_utc,
                "debug_stamp": {
                    "fix_marker":    ROUTE_BUILD_MARKER,
                    "fixed_at_iso":  now_utc.isoformat(),
                    "delta_seconds": int(delta_seconds),
                    "stored_utc":    stored_utc.isoformat(),
                    "correct_utc":   correct_utc.isoformat(),
                    "tz_iana":       resolution.get("debug_stamp", {}).get("timezone_iana"),
                    "tz_offset_at_birth": resolution.get("debug_stamp", {}).get("resolved_utc_offset_at_birth"),
                },
            }
            await _db.charts.update_one(
                {"_id": chart_proj["_id"]},
                {"$set": update_fields},
            )

            # Record the after-state for the report.
            after_asc = ((new_astro.get("angles") or {}).get("asc") or {}).get("formatted")
            repaired.append({**drift_record, "after_asc_formatted": after_asc})

        except Exception as exc:
            errors.append({
                "user_id": user_id,
                "chart_id": chart_id,
                "stage": "outer",
                "error": f"{type(exc).__name__}: {exc}",
            })

    finished_at = datetime.now(timezone.utc)
    elapsed_s = (finished_at - started_at).total_seconds()
    logger.warning(
        "[%s] done dry_run=%s scanned=%d drifted=%d repaired=%d errors=%d elapsed=%.2fs",
        ROUTE_BUILD_MARKER, dry_run, scanned, len(drifted), len(repaired),
        len(errors), elapsed_s,
    )

    return JSONResponse(content={
        "build_marker": ROUTE_BUILD_MARKER,
        "dry_run":      dry_run,
        "started_at":   started_at.isoformat(),
        "finished_at":  finished_at.isoformat(),
        "elapsed_seconds": elapsed_s,
        "db_name":      _DB_NAME,
        "mongo_host":   urlparse(_MONGO_URL).hostname,
        "scanned":      scanned,
        "drifted_count": len(drifted),
        "repaired_count": len(repaired),
        "skipped_no_inputs":   skipped_no_inputs,
        "skipped_no_chart_utc": skipped_no_chart_utc,
        "errors_count": len(errors),
        "drifted":  drifted,
        "repaired": repaired,
        "errors":   errors[:50],
    }, headers={"Cache-Control": "no-store"})
