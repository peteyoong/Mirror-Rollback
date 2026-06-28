"""
Admin: chart-provenance repair endpoints.
=========================================

Two endpoints in one router:

  POST /api/admin/repair_chart_for_user
      Single-user surgical repair. Refuses silent +08:00 fallback.
      Defaults dry_run=true. Stamps V-A markers + repair fix marker on
      the live write so the chart can be located later.

  GET  /api/admin/scan_timezone_fallback_cohort
      READ-ONLY cohort scan. Surfaces every chart whose stored
      migration_info indicates a silent timezone fallback was applied
      (resolved_offset == "+08:00" while timezone_iana is missing/null)
      AND whose lat/lon falls outside the Asia/+08:00 longitude band.

Both endpoints:
  * are gated by an explicit confirm token,
  * refuse to operate against loopback Mongo (safety on local dev pod),
  * emit a single JSON document with `build_marker` + cache headers,
  * return early on any inconsistency rather than guessing.

Build marker: chart-provenance-repair-v1
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone as dt_tz
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/admin", tags=["chart-provenance-repair-v1"])
logger = logging.getLogger(__name__)

REPAIR_CONFIRM_TOKEN = "REPAIR_CHART_FOR_USER_2026_06_26"
SCAN_CONFIRM_TOKEN   = "SCAN_TIMEZONE_FALLBACK_COHORT_2026_06_26"
PEEK_CONFIRM_TOKEN   = "PEEK_CHART_ANGLES_2026_06_26"


# =====================================================================
# READ-ONLY DIAGNOSTIC — quick check of a user's stored ASC/MC/Sun/Moon
# Useful in production to verify whether a chart still shows stale
# placements (e.g., a wrong Rising sign) before/after a repair.
# =====================================================================
@router.get("/peek_chart_angles")
async def peek_chart_angles(
    user_id: str = Query(..., description="Mongo _id of the user (24-hex)."),
    confirm: str = Query("", description="Required confirm token."),
):
    """Return stored ASC / MC / Sun / Moon for a single user — read-only."""
    if confirm != PEEK_CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail="confirm token required (peek endpoint)")

    from server import db
    from bson import ObjectId
    try:
        oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid user_id: {e!s}")
    user = await db.users.find_one({"_id": oid}, {
        "_id": 1, "name": 1, "email": 1, "timezone": 1,
        "birth_date": 1, "birth_time": 1, "birth_location": 1,
    })
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
    chart = await db.charts.find_one({"user_id": user_id}) or {}
    astro = chart.get("astrology") or {}
    angles = astro.get("angles") or {}
    planets = astro.get("planets") or []

    asc_node = angles.get("asc") or angles.get("ascendant") or {}
    mc_node  = angles.get("mc")  or angles.get("midheaven") or {}

    # v1.5.6 — surface house_system + ayanamsa metadata so GM-parity
    # audits can be performed externally without trawling chart docs.
    astro_meta = astro.get("metadata") or {}
    houses_meta = astro.get("houses") if isinstance(astro.get("houses"), dict) else {}

    def _pick(p_name: str) -> Dict[str, Any]:
        """Find Sun/Moon/etc in either list-shaped or dict-shaped
        `astro.planets`. Supports lower-case keys too."""
        # List form: [{name|planet: "Sun", sign: "...", ...}, ...]
        if isinstance(planets, list):
            for p in planets:
                if not isinstance(p, dict):
                    continue
                if (p.get("planet") == p_name) or (p.get("name") == p_name):
                    return {"sign": p.get("sign"),
                            "degree": _round(p.get("degree")),
                            "longitude": _round(p.get("longitude"))}
        # Dict form: {"sun": {...}, "moon": {...}, "Sun": {...}, ...}
        elif isinstance(planets, dict):
            for k in (p_name, p_name.lower(), p_name.upper()):
                node = planets.get(k)
                if isinstance(node, dict):
                    return {"sign": node.get("sign"),
                            "degree": _round(node.get("degree")),
                            "longitude": _round(node.get("longitude"))}
        return {}
    payload = {
        "ok": True,
        "build_marker": "peek-chart-angles-v1",
        "user": {
            "id": str(user.get("_id")),
            "name": user.get("name"),
            "email": user.get("email"),
            "timezone": user.get("timezone"),
            "birth_date": _safe_iso(user.get("birth_date")),
            "birth_time": user.get("birth_time"),
            "birth_location": user.get("birth_location"),
        },
        "stored": {
            "ASC": {
                "sign": asc_node.get("sign") if isinstance(asc_node, dict) else None,
                "degree": _round(asc_node.get("degree")) if isinstance(asc_node, dict) else None,
                "longitude": _round(asc_node.get("longitude")) if isinstance(asc_node, dict) else None,
            },
            "MC": {
                "sign": mc_node.get("sign") if isinstance(mc_node, dict) else None,
                "degree": _round(mc_node.get("degree")) if isinstance(mc_node, dict) else None,
                "longitude": _round(mc_node.get("longitude")) if isinstance(mc_node, dict) else None,
            },
            "Sun":  _pick("Sun"),
            "Moon": _pick("Moon"),
        },
        "engine": {
            "house_system":         astro_meta.get("house_system") or houses_meta.get("system"),
            "ayanamsa":             astro_meta.get("ayanamsa"),
            "svp_degrees":          astro_meta.get("svp_degrees"),
            "sidereal_mode":        astro_meta.get("sidereal_mode") or astro_meta.get("zodiac_mode"),
            "astrology_engine_version": astro_meta.get("astrology_engine_version"),
        },
        "migration_info":   chart.get("migration_info"),
        "astrology_metadata_keys": list((astro.get("metadata") or {}).keys()),
        "provenance_hash":  (chart.get("debug_stamp") or {}).get("provenance_hash"),
        "checked_at":       _now_iso(),
    }
    return JSONResponse(payload, headers={"Cache-Control": "no-store"})


def _now_iso() -> str:
    return datetime.now(dt_tz.utc).isoformat()


def _safe_iso(x: Any) -> Optional[str]:
    if x is None:
        return None
    if hasattr(x, "isoformat"):
        return x.isoformat()
    return str(x)


def _refuse_loopback() -> None:
    mongo_url = os.getenv("MONGO_URL", "") or ""
    if "localhost" in mongo_url or "127.0.0.1" in mongo_url:
        raise HTTPException(
            status_code=403,
            detail=(
                "Refusing to operate against loopback Mongo. This endpoint "
                "is intended for production-only forensic repair. If you "
                "are intentionally running locally, set MONGO_URL to a "
                "non-loopback target."
            ),
        )


def _diff_value(stored: Any, fresh: Any) -> Optional[Dict[str, Any]]:
    """Return None if values match, else a diff record."""
    if stored == fresh:
        return None
    return {"stored": stored, "fresh": fresh}


def _round(v: Any, n: int = 4) -> Any:
    try:
        return round(float(v), n)
    except Exception:
        return v


def _planet_diff(stored_p: Dict[str, Any], fresh_p: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Produce a compact diff for a single planet row."""
    out: Dict[str, Any] = {}
    sp = stored_p or {}
    fp = fresh_p or {}
    for k in ("sign", "house", "retrograde"):
        if sp.get(k) != fp.get(k):
            out[k] = {"stored": sp.get(k), "fresh": fp.get(k)}
    for k in ("degree", "longitude"):
        s = _round(sp.get(k))
        f = _round(fp.get(k))
        if s != f:
            out[k] = {"stored": s, "fresh": f}
    return out or None


def _angle_diff(stored: Dict[str, Any], fresh: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return _planet_diff(stored, fresh)


def _compute_provenance_hash(payload: Dict[str, Any]) -> str:
    """SHA256 of canonical-JSON of the listed input fields.

    NOTE: This is a *preview* of the Phase 3 architecture (Chart
    Provenance Hash). It is computed here, returned in the response, but
    NOT yet enforced anywhere else in the codebase. Phase 3 is approval-
    gated.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =====================================================================
# POST /api/admin/repair_chart_for_user
# =====================================================================
@router.post("/repair_chart_for_user")
async def repair_chart_for_user(
    user_id: str = Query(..., description="Mongo _id of the user to repair (24-hex)."),
    confirm: str = Query("", description="Required confirm token."),
    dry_run: bool = Query(True, description="Default true. Set false to actually write."),
    timezone_override: Optional[str] = Query(
        None,
        description=(
            "REQUIRED if the user record has no timezone field. "
            "IANA zone name, e.g. 'America/Argentina/Buenos_Aires'."
        ),
    ),
    birth_time_override: Optional[str] = Query(
        None,
        description="Optional birth_time override in HH:MM (24h) format.",
    ),
    fix_marker: str = Query(
        "chart_provenance_repair_v1",
        description="Debug-stamp fix marker for this repair batch.",
    ),
):
    """Surgical single-user chart repair.

    Refuses any silent timezone fallback. If both user.timezone and
    timezone_override are missing/empty, returns a 400 with no compute
    attempted. This is intentional — the whole point of this endpoint
    is to STOP defaulting to +08:00 when the input is unknown.
    """
    if confirm != REPAIR_CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail="confirm token required (write-capable repair endpoint)")
    _refuse_loopback()

    # Lazy imports to avoid circulars at module load
    from server import db
    from calculations.astrology import get_full_natal_chart
    from calculations.human_design import get_human_design_chart
    from calculations.numerology import get_full_numerology
    from calculations.timezone_utils import resolve_birth_utc_with_debug

    # ---- 1. Load user + stored chart ----
    from bson import ObjectId  # type: ignore
    try:
        oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid user_id: {e!s}")
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
    chart_doc = await db.charts.find_one({"user_id": user_id}) or {}

    # ---- 2. Resolve effective inputs (no silent fallback) ----
    user_tz = (user.get("timezone") or "").strip() or None
    override_tz = (timezone_override or "").strip() or None
    effective_tz = override_tz or user_tz
    if not effective_tz:
        raise HTTPException(
            status_code=400,
            detail=(
                "user.timezone is missing and no timezone_override provided. "
                "Refusing to default. Pass ?timezone_override=<IANA_zone>."
            ),
        )

    raw_bd = user.get("birth_date")
    if isinstance(raw_bd, datetime):
        birth_date_str = raw_bd.strftime("%Y-%m-%d")
    else:
        birth_date_str = str(raw_bd or "").split()[0]
    if not birth_date_str:
        raise HTTPException(status_code=400, detail="user.birth_date missing")

    user_bt = (user.get("birth_time") or "").strip() or None
    override_bt = (birth_time_override or "").strip() or None
    effective_bt = override_bt or user_bt
    if not effective_bt:
        raise HTTPException(status_code=400, detail="user.birth_time missing and no override")

    birth_loc = user.get("birth_location") or {}
    lat = birth_loc.get("lat") or birth_loc.get("latitude") or user.get("lat")
    lon = birth_loc.get("lon") or birth_loc.get("lng") or birth_loc.get("longitude") or user.get("lon")
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="user.birth_location lat/lon missing")
    lat = float(lat)
    lon = float(lon)

    # ---- 3. Resolve canonical UTC strictly ----
    tz_result = resolve_birth_utc_with_debug(birth_date_str, effective_bt, effective_tz)
    birth_utc = tz_result.get("birth_utc")
    if not birth_utc:
        raise HTTPException(
            status_code=400,
            detail=f"could not resolve UTC: {tz_result.get('error_message')}",
        )

    # ---- 4. Fresh compute ----
    sidereal_settings = {
        "mode": "true_sidereal_user_defined",
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0,
    }
    fresh_astro = get_full_natal_chart(
        birth_utc,
        lat=lat, lon=lon,
        sidereal_settings=sidereal_settings,
        house_system="Equal",
        node_mode="true_node",
    )
    fresh_hd = get_human_design_chart(
        birth_utc,
        lat=lat, lon=lon,
        sidereal_settings=sidereal_settings,
    )
    fresh_num = None
    try:
        # Pass birth_utc as a datetime (timezone-aware OK; the function
        # only reads date components for life-path math).
        fresh_num = get_full_numerology(
            birth_date=birth_utc,
            full_name=(user.get("name") or user.get("full_name") or "Unknown"),
        )
    except Exception as e:
        logger.warning("[repair_chart_for_user] numerology compute failed: %s", e)

    # ---- 5. Compute Phase-3-preview provenance hash ----
    provenance_inputs = {
        "birth_date":      birth_date_str,
        "birth_time":      effective_bt,
        "timezone_iana":   effective_tz,
        "lat":             lat,
        "lon":             lon,
        "house_system":    "Equal",
        "zodiac_mode":     "true_sidereal_m_midpoint_user_defined",
        "svp_degrees":     31.2836,
        "reference_year":  2000,
        "yearly_increment": 0.0,
        "node_mode":       "true_node",
        "hybrid":          False,
        "engine_version":  "midpoint13_variant_a_v1",
    }
    provenance_hash = _compute_provenance_hash(provenance_inputs)

    # ---- 6. Diff stored vs fresh ----
    stored_astro = chart_doc.get("astrology") or {}
    stored_meta = stored_astro.get("metadata") or {}
    stored_mig = stored_astro.get("migration_info") or {}

    diff: Dict[str, Any] = {"angles": {}, "planets": {}, "nodes": {}, "metadata": {}}
    # metadata
    for k_pretty, s, f in (
        ("input_datetime_utc", stored_meta.get("input_datetime_utc"), birth_utc.isoformat()),
        ("resolved_offset", stored_mig.get("resolved_offset"), tz_result.get("offset_string")),
        ("timezone_iana", stored_mig.get("timezone_iana"), effective_tz),
        ("house_system", stored_meta.get("house_system"), "Equal"),
        ("astrology_engine_version", stored_astro.get("astrology_engine_version"), "midpoint13_variant_a_v1"),
        ("migration_marker", stored_astro.get("migration_marker"), "variant-a-13-sign-migration-v1"),
    ):
        d = _diff_value(s, f)
        if d:
            diff["metadata"][k_pretty] = d
    # angles
    s_ang = stored_astro.get("angles") or {}
    f_ang = fresh_astro.get("angles") or {}
    for k in ("asc", "mc", "dc", "ic"):
        d = _angle_diff(s_ang.get(k) or {}, f_ang.get(k) or {})
        if d:
            diff["angles"][k] = d
    # planets
    s_p = stored_astro.get("planets") or {}
    f_p = fresh_astro.get("planets") or {}
    planet_keys = sorted(set(list(s_p.keys()) + list(f_p.keys())))
    for k in planet_keys:
        d = _planet_diff(s_p.get(k) or {}, f_p.get(k) or {})
        if d:
            diff["planets"][k] = d
    # nodes (older chart shape used `nodes.north` / `nodes.south`)
    s_n = stored_astro.get("nodes") or {}
    f_n = fresh_astro.get("nodes") or {}
    for k in ("north", "south"):
        d = _planet_diff(s_n.get(k) or {}, f_n.get(k) or {})
        if d:
            diff["nodes"][k] = d

    # Prune empty subkeys for cleanliness
    for sect in list(diff.keys()):
        if not diff[sect]:
            del diff[sect]

    response: Dict[str, Any] = {
        "build_marker": "chart-provenance-repair-v1",
        "served_at": _now_iso(),
        "dry_run": dry_run,
        "user_id": user_id,
        "user_summary": {
            "name": user.get("name"),
            "email": user.get("email"),
            "birth_date": birth_date_str,
            "stored_birth_time": user_bt,
            "effective_birth_time": effective_bt,
            "stored_timezone": user_tz,
            "effective_timezone": effective_tz,
            "lat": lat, "lon": lon,
        },
        "resolution": {
            "fresh_birth_utc": birth_utc.isoformat(),
            "fresh_resolved_offset": tz_result.get("offset_string"),
            "stored_birth_utc": stored_meta.get("input_datetime_utc"),
            "stored_resolved_offset": stored_mig.get("resolved_offset"),
            "stored_timezone_iana": stored_mig.get("timezone_iana"),
        },
        "fresh_chart_summary": {
            "asc": (fresh_astro.get("angles") or {}).get("asc"),
            "mc":  (fresh_astro.get("angles") or {}).get("mc"),
            "saturn": (fresh_astro.get("planets") or {}).get("Saturn"),
            "north_node": (fresh_astro.get("planets") or {}).get("North Node"),
            "hd_type": fresh_hd.get("type"),
            "hd_profile": fresh_hd.get("profile"),
            "hd_authority": fresh_hd.get("authority"),
            "hd_definition": fresh_hd.get("definition"),
            "hd_personality_sun_gate_line": (
                ((fresh_hd.get("personality") or {}).get("Sun") or {}).get("gate") or {}
            ).get("formatted"),
            "hd_design_sun_gate_line": (
                ((fresh_hd.get("design") or {}).get("Sun") or {}).get("gate") or {}
            ).get("formatted"),
            "hd_personality_sun_full": (
                ((fresh_hd.get("personality") or {}).get("Sun") or {}).get("gate") or {}
            ).get("full_formatted"),
            "hd_design_sun_full": (
                ((fresh_hd.get("design") or {}).get("Sun") or {}).get("gate") or {}
            ).get("full_formatted"),
            "hd_defined_channels": fresh_hd.get("defined_channels"),
            "hd_incarnation_cross": (
                (fresh_hd.get("incarnation_cross") or {}).get("name")
                if isinstance(fresh_hd.get("incarnation_cross"), dict)
                else fresh_hd.get("incarnation_cross")
            ),
        },
        "diff_stored_vs_fresh": diff,
        "provenance_hash_preview": {
            "hash": provenance_hash,
            "inputs": provenance_inputs,
            "note": "Phase-3-preview only. Not yet enforced.",
        },
        "write_planned": (not dry_run),
    }

    if dry_run:
        response["next_action"] = (
            "Review diff. To execute live, re-call this endpoint with "
            "dry_run=false. NOTHING WAS WRITTEN."
        )
        return JSONResponse(content=response, headers={"Cache-Control": "no-store"})

    # ---- 7. LIVE WRITE ----
    # Stamp the chart with V-A markers + repair fix marker + provenance.
    write_doc: Dict[str, Any] = dict(fresh_astro)
    write_doc.setdefault("metadata", {})
    write_doc["metadata"].update({
        "house_system": "Equal",
        "input_datetime_utc": birth_utc.isoformat(),
        "migration_marker": "variant-a-13-sign-migration-v1",
        "zodiac_mode": "true_sidereal_m_midpoint_user_defined",
        "node_mode": "true_node",
    })
    write_doc["astrology_engine_version"] = "midpoint13_variant_a_v1"
    write_doc["migration_marker"] = "variant-a-13-sign-migration-v1"
    write_doc["svp_applied"] = 31.2836

    now = datetime.now(dt_tz.utc)
    debug_stamp = {
        "fix_marker": fix_marker,
        "computed_at_iso": now.isoformat(),
        "sidereal_settings_used": sidereal_settings,
        "resolved_offset": tz_result.get("offset_string"),
        "resolved_timezone": effective_tz,
        "provenance_hash": provenance_hash,
        "provenance_inputs": provenance_inputs,
        "prior_input_datetime_utc": stored_meta.get("input_datetime_utc"),
        "prior_resolved_offset": stored_mig.get("resolved_offset"),
        "prior_timezone_iana": stored_mig.get("timezone_iana"),
    }
    chart_update = {
        "$set": {
            "astrology": write_doc,
            "human_design": fresh_hd,
            "updated_at": now,
            "calculated_at": now,
            "debug_stamp": debug_stamp,
        }
    }
    if fresh_num is not None:
        chart_update["$set"]["numerology"] = fresh_num
    await db.charts.update_one({"user_id": user_id}, chart_update, upsert=True)

    # Also persist the resolved IANA zone on the user record (so the
    # auto-migration cannot default to +08:00 again).
    user_update = {
        "$set": {
            "timezone": effective_tz,
            "updated_at": now,
        }
    }
    if override_bt:
        user_update["$set"]["birth_time"] = effective_bt
    await db.users.update_one({"_id": oid}, user_update)

    response["written"] = {
        "chart_update_ok": True,
        "user_timezone_persisted": effective_tz,
        "user_birth_time_persisted": (effective_bt if override_bt else None),
        "fix_marker": fix_marker,
    }
    return JSONResponse(content=response, headers={"Cache-Control": "no-store"})


# =====================================================================
# GET /api/admin/scan_timezone_fallback_cohort
# =====================================================================
@router.get("/scan_timezone_fallback_cohort")
async def scan_timezone_fallback_cohort(
    confirm: str = Query("", description="Required confirm token."),
    limit: int = Query(2000, ge=1, le=20000),
    asia_lon_min: float = Query(60.0, description="Asia band low (deg longitude)."),
    asia_lon_max: float = Query(150.0, description="Asia band high (deg longitude)."),
    offset_tolerance_h: float = Query(3.0, description="Hours of tolerance for criterion C."),
):
    """READ-ONLY scan for charts with provenance / timezone-fallback bugs.

    A chart is in the **cohort** if ANY of three criteria holds:

      A) Classic +08:00 fallback signature:
         chart.migration_info.resolved_offset == "+08:00" AND
         chart.migration_info.timezone_iana is null/empty AND
         user.birth_location.lon is OUTSIDE the [asia_lon_min, asia_lon_max] band.

      B) Raw-offset user.timezone field (not IANA):
         user.timezone parses to a numeric offset (e.g. "+08:00", "GMT-3")
         AND that offset is INCONSISTENT (more than `offset_tolerance_h`
         hours) with the offset that would be naturally expected from
         the user's longitude.

      C) UTC ↔ longitude inconsistency:
         An implied offset (local_dt - stored_utc) disagrees with the
         lon-derived expected offset by more than `offset_tolerance_h`.

    No writes. Light-touch compute only — no engine recompute.
    """
    if confirm != SCAN_CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail="confirm token required (read-only scan)")
    _refuse_loopback()
    from server import db
    from bson import ObjectId  # type: ignore

    cohort: List[Dict[str, Any]] = []
    near_miss_asia_safe: List[Dict[str, Any]] = []
    near_miss_explicit_zone: List[Dict[str, Any]] = []
    near_miss_no_coords: List[Dict[str, Any]] = []
    row_failures: List[Dict[str, Any]] = []
    scanned = 0
    cursor = db.charts.find({}).limit(limit)
    async for c in cursor:
        scanned += 1
        try:
            astro = c.get("astrology") or {}
            # FIX: migration_info lives at the chart top level (chart.migration_info),
            # NOT under astrology. The first version of this scan read the wrong path
            # and returned zero hits even for Ana.
            mig = c.get("migration_info") or astro.get("migration_info") or {}
            resolved_offset = (mig.get("resolved_offset") or "").strip()
            timezone_iana = (mig.get("timezone_iana") or "").strip()

            uid = c.get("user_id")
            if not uid:
                continue
            try:
                user = await db.users.find_one({"_id": ObjectId(uid)})
            except Exception:
                user = None
            if not user:
                continue
            loc = user.get("birth_location") or {}
            lat = loc.get("lat") or loc.get("latitude") or user.get("lat")
            lon = loc.get("lon") or loc.get("lng") or loc.get("longitude") or user.get("lon")
            try:
                lonf = float(lon) if lon is not None else None
                latf = float(lat) if lat is not None else None
            except Exception:
                lonf = latf = None

            stored_user_tz = (user.get("timezone") or "").strip() or None
            stored_input_utc = (astro.get("metadata") or {}).get("input_datetime_utc")

            # ---- Criterion C: stored UTC implies offset; compare to lon ----
            implied_offset_h: Optional[float] = None
            offset_disagree_h: Optional[float] = None
            local_dt = _parse_local_dt(user.get("birth_date"), user.get("birth_time"))
            stored_utc = _parse_utc_iso(stored_input_utc)
            if local_dt and stored_utc:
                try:
                    # Strip TZ for diff
                    stored_utc_naive = stored_utc.replace(tzinfo=None)
                    implied_offset_h = (local_dt - stored_utc_naive).total_seconds() / 3600.0
                except Exception:
                    implied_offset_h = None
            if implied_offset_h is not None and lonf is not None:
                expected_h = lonf / 15.0
                offset_disagree_h = round(implied_offset_h - expected_h, 2)

            # ---- Criterion B: user.timezone raw offset vs lon ----
            raw_offset_h = _parse_offset_to_hours(stored_user_tz)
            user_tz_is_iana = bool(stored_user_tz and "/" in stored_user_tz)
            offset_disagree_user_tz_h: Optional[float] = None
            if raw_offset_h is not None and lonf is not None:
                offset_disagree_user_tz_h = round(raw_offset_h - (lonf / 15.0), 2)

            # ---- Criterion A: classic +08:00 silent fallback ----
            crit_A = bool(
                resolved_offset == "+08:00"
                and not timezone_iana
                and lonf is not None
                and not (asia_lon_min <= lonf <= asia_lon_max)
            )
            crit_B = bool(
                raw_offset_h is not None
                and not user_tz_is_iana
                and offset_disagree_user_tz_h is not None
                and abs(offset_disagree_user_tz_h) > offset_tolerance_h
            )
            crit_C = bool(
                offset_disagree_h is not None
                and abs(offset_disagree_h) > offset_tolerance_h
            )

            any_crit = crit_A or crit_B or crit_C
            row = {
                "user_id": uid,
                "chart_id": str(c.get("_id")),
                "name": user.get("name"),
                "email": user.get("email"),
                "stored_birth_date": _safe_iso(user.get("birth_date")),
                "stored_birth_time": user.get("birth_time"),
                "user_timezone_field": stored_user_tz,
                "user_timezone_is_iana": user_tz_is_iana,
                "stored_resolved_offset": resolved_offset or None,
                "stored_timezone_iana": timezone_iana or None,
                "stored_input_datetime_utc": stored_input_utc,
                "lat": latf,
                "lon": lonf,
                "expected_offset_h_from_lon": (lonf / 15.0 if lonf is not None else None),
                "implied_offset_h_from_stored_utc": implied_offset_h,
                "offset_disagree_implied_vs_expected_h": offset_disagree_h,
                "raw_user_tz_offset_h": raw_offset_h,
                "offset_disagree_user_tz_vs_lon_h": offset_disagree_user_tz_h,
                "criteria_hit": [k for k, v in (("A", crit_A), ("B", crit_B), ("C", crit_C)) if v],
                "engine_version": astro.get("astrology_engine_version"),
                "migration_marker": astro.get("migration_marker"),
                "calculated_at": _safe_iso(c.get("calculated_at")),
                "likely_correct_iana_hint": (_lon_to_iana_hint(lonf, latf or 0.0) if lonf is not None else None),
            }

            if any_crit:
                cohort.append(row)
                continue

            # near-miss classification (no real bug, but interesting for context)
            if not any_crit and resolved_offset == "+08:00" and not timezone_iana:
                if lonf is not None and asia_lon_min <= lonf <= asia_lon_max:
                    near_miss_asia_safe.append(row)
                elif lonf is None:
                    near_miss_no_coords.append(row)
                else:
                    # Already covered by crit_A above; defensive
                    cohort.append(row)
            elif not any_crit and timezone_iana:
                near_miss_explicit_zone.append(row)
            elif not any_crit and lonf is None:
                near_miss_no_coords.append(row)
        except Exception as e:
            # Never let one rotten row crash the whole scan.
            row_failures.append({
                "chart_id": str(c.get("_id")) if c else None,
                "user_id": c.get("user_id") if isinstance(c, dict) else None,
                "error": f"{type(e).__name__}: {e!s}",
            })
            logger.warning("[scan_timezone_fallback_cohort] row failed: %s", e)
            continue

    return JSONResponse(
        content={
            "build_marker": "chart-provenance-repair-v1",
            "scan_version": "v2",
            "served_at": _now_iso(),
            "scanned_charts": scanned,
            "criteria_definitions": {
                "A": "chart.migration_info.resolved_offset == '+08:00' AND timezone_iana null/empty AND lon outside Asia band",
                "B": "user.timezone is raw offset (non-IANA) AND offset disagrees with lon-derived expectation by > tolerance",
                "C": "stored UTC implies an offset that disagrees with lon-derived expectation by > tolerance",
            },
            "params": {
                "asia_lon_min": asia_lon_min,
                "asia_lon_max": asia_lon_max,
                "offset_tolerance_h": offset_tolerance_h,
            },
            "cohort_count": len(cohort),
            "near_miss_asia_safe_count": len(near_miss_asia_safe),
            "near_miss_explicit_zone_count": len(near_miss_explicit_zone),
            "near_miss_no_coords_count": len(near_miss_no_coords),
            "row_failure_count": len(row_failures),
            "cohort": cohort,
            "near_miss_asia_safe": near_miss_asia_safe[:50],
            "near_miss_explicit_zone": near_miss_explicit_zone[:50],
            "near_miss_no_coords": near_miss_no_coords[:50],
            "row_failures": row_failures[:50],
        },
        headers={"Cache-Control": "no-store"},
    )


def _lon_to_iana_hint(lon: float, lat: float) -> str:
    """Very coarse longitude→IANA-zone hint. NOT authoritative.

    Used only to give the operator a starting point in the cohort scan
    output; the operator must confirm before any repair call.
    """
    if lon < -120:
        return "America/Los_Angeles (-08:00 hint)"
    if lon < -100:
        return "America/Denver (-07:00 hint)"
    if lon < -80:
        return "America/Chicago (-06:00 hint)"
    if lon < -60:
        return "America/New_York / America/Argentina (-05:00/-03:00 hint)"
    if lon < -30:
        return "America/Argentina/Buenos_Aires (-03:00 hint)"
    if lon < 0:
        return "Atlantic/Azores (-01:00 hint)"
    if lon < 15:
        return "Europe/London (+00/+01 hint)"
    if lon < 30:
        return "Europe/Berlin (+01/+02 hint)"
    if lon < 45:
        return "Europe/Moscow (+03 hint)"
    if lon < 60:
        return "Asia/Dubai (+04 hint)"
    if lon < 80:
        return "Asia/Karachi (+05 hint)"
    if lon < 105:
        return "Asia/Bangkok (+07 hint)"
    if lon < 130:
        return "Asia/Shanghai / Asia/Kuala_Lumpur (+08 hint)"
    if lon < 150:
        return "Asia/Tokyo (+09 hint)"
    return "Pacific/Auckland (+12 hint)"


# ---------------------------------------------------------------------
# Helpers for cohort scan v2 (criteria B and C)
# ---------------------------------------------------------------------
_OFFSET_RE = __import__("re").compile(r"^([+-]?)(\d{1,2}):?(\d{2})?$")


def _parse_offset_to_hours(s: Optional[str]) -> Optional[float]:
    """Parse a raw offset string into hours. Returns None for IANA / unknown.

    Accepts: '+08:00', '-03:00', '+0800', '-0300', '+8', '-3', 'GMT+8',
             'UTC-3', 'Z', 'UTC', 'GMT'. Returns None when input is an
             IANA zone (contains '/') or is unparseable.
    """
    if not s:
        return None
    raw = s.strip()
    if "/" in raw:
        return None  # IANA zone, e.g. America/Argentina/Buenos_Aires
    up = raw.upper()
    if up in ("UTC", "GMT", "Z"):
        return 0.0
    # Strip leading GMT/UTC
    for pre in ("GMT", "UTC"):
        if up.startswith(pre):
            raw = raw[len(pre):]
            break
    raw = raw.strip()
    m = _OFFSET_RE.match(raw)
    if not m:
        return None
    sign = -1.0 if m.group(1) == "-" else 1.0
    hours = float(m.group(2))
    mins = float(m.group(3) or 0)
    return sign * (hours + mins / 60.0)


def _expected_offset_band_for_lon(lon: float) -> tuple:
    """Return (low_h, high_h) plausible offset band for a given longitude.

    Rule of thumb: 15° of longitude == 1 hour of offset. Allow ±2h
    tolerance to absorb large-country zone variation (e.g. China runs a
    single +08 even at lon~75; Argentina runs -03 not -04 etc.).
    """
    center = lon / 15.0
    return (center - 2.5, center + 2.5)


def _parse_utc_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # Accept both 'Z' suffix and explicit offsets
        s2 = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _parse_local_dt(date_field: Any, time_field: Optional[str]) -> Optional[datetime]:
    """Combine user.birth_date + user.birth_time into a naive local datetime."""
    if not date_field:
        return None
    if isinstance(date_field, datetime):
        date_str = date_field.strftime("%Y-%m-%d")
    else:
        date_str = str(date_field).split()[0]
    if not time_field:
        time_field = "12:00"
    try:
        return datetime.fromisoformat(f"{date_str}T{time_field}:00")
    except Exception:
        try:
            return datetime.strptime(f"{date_str} {time_field}", "%Y-%m-%d %H:%M")
        except Exception:
            return None
