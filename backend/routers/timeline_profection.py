"""timeline_profection.py — Timeline Intelligence V2 · Phase 1+2 endpoint
========================================================================
Surface marker: timeline-profection-router-v1

    GET /api/timeline/profection?user_id=...&date=YYYY-MM-DD
    GET /api/timeline/profection/series?user_id=...&from_age=0&to_age=48

Returns the canonical Annual Profection block (engine + narrative)
under Mirror's Timeline namespace. Read-only; no chart is mutated.

Design notes
------------
• The endpoint prefers the user's already-stored natal chart. If the
  user record has no computed chart yet, we compute one on the fly under
  the canonical Variant-A / Equal-house frame.
• Historical & future dates share the same code path — the caller only
  varies `date`.
• No LLM. Deterministic. Same inputs → same output.
"""
from __future__ import annotations

import logging
from datetime import date as _date, datetime, timezone as _tz
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

BUILD_MARKER = "timeline-profection-router-v1"


# ---------------------------------------------------------------------------
# Chart resolver — prefer stored, fall back to on-the-fly compute.
# ---------------------------------------------------------------------------
async def _resolve_natal_chart(user: Dict[str, Any]) -> Dict[str, Any]:
    """Return a natal chart dict in Equal-houses / Variant-A shape."""
    # Prefer stored chart (fresh key names first, then legacy).
    for key in ("astrology", "chart", "natal_chart"):
        stored = user.get(key)
        if isinstance(stored, dict) and stored.get("planets") and stored.get("angles"):
            return stored

    # Fall back: compute now.
    from calculations.astrology import get_full_natal_chart              # noqa: PLC0415
    from calculations.timezone_utils import resolve_birth_utc_with_debug  # noqa: PLC0415

    loc = user.get("birth_location") or {}
    lat, lon = loc.get("latitude"), loc.get("longitude")
    if lat is None or lon is None:
        raise HTTPException(status_code=400,
                            detail="user has no birth_location.latitude/longitude")

    birth_date_raw = user.get("birth_date")
    if hasattr(birth_date_raw, "strftime"):
        birth_date_str = birth_date_raw.strftime("%Y-%m-%d")
    else:
        birth_date_str = str(birth_date_raw or "").strip()[:10]

    resolved = resolve_birth_utc_with_debug(
        birth_date_str, user.get("birth_time"), user.get("timezone"),
    )
    if not resolved.get("success"):
        raise HTTPException(
            status_code=400,
            detail=f"timezone resolution failed: "
                   f"{resolved.get('error_message') or resolved.get('error')}",
        )

    chart = get_full_natal_chart(
        birth_datetime = resolved["birth_utc"],
        lat = lat, lon = lon, house_system = "Equal",
    )
    return chart


def _resolve_birth_utc(user: Dict[str, Any]) -> datetime:
    """Return the user's birth datetime in UTC (timezone-aware)."""
    def _ensure_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=_tz.utc)
        return dt.astimezone(_tz.utc)

    # If the stored chart already carries a resolved UTC, prefer it.
    for key in ("astrology", "chart", "natal_chart"):
        stored = user.get(key)
        if isinstance(stored, dict):
            iso = ((stored.get("metadata") or {}).get("birth_utc")
                    or stored.get("birth_utc"))
            if iso:
                try:
                    dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
                    return _ensure_aware(dt)
                except Exception:                                # fall through
                    pass

    # Recompute from raw birth fields.
    from calculations.timezone_utils import resolve_birth_utc_with_debug  # noqa: PLC0415
    birth_date_raw = user.get("birth_date")
    if hasattr(birth_date_raw, "strftime"):
        birth_date_str = birth_date_raw.strftime("%Y-%m-%d")
    else:
        birth_date_str = str(birth_date_raw or "").strip()[:10]

    resolved = resolve_birth_utc_with_debug(
        birth_date_str, user.get("birth_time"), user.get("timezone"),
    )
    if not resolved.get("success"):
        raise HTTPException(
            status_code=400,
            detail=f"timezone resolution failed: "
                   f"{resolved.get('error_message') or resolved.get('error')}",
        )
    return _ensure_aware(resolved["birth_utc"])


# ---------------------------------------------------------------------------
# Endpoint 1 — single-year profection
# ---------------------------------------------------------------------------
@router.get("/profection/current")
async def profection_for_date(
    user_id: str = Query(..., description="Mongo _id of the user (24-hex)."),
    date:    Optional[str] = Query(
        None, description="Target date YYYY-MM-DD. Defaults to today (UTC)."),
):
    from server import db                                                 # noqa: PLC0415
    from bson import ObjectId                                              # noqa: PLC0415
    from services.annual_profection_engine   import compute_profection    # noqa: PLC0415
    from services.annual_profection_narrative import build_narrative      # noqa: PLC0415

    try:
        oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid user_id: {e!s}")

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")

    # Parse target date; default = today UTC.
    if date is None:
        target = datetime.now(_tz.utc).date()
    else:
        try:
            target = _date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400,
                                detail="date must be YYYY-MM-DD")

    chart      = await _resolve_natal_chart(user)
    birth_utc  = _resolve_birth_utc(user)

    prof = compute_profection(
        natal_chart        = chart,
        birth_datetime_utc = birth_utc,
        target_date        = target,
    )
    narrative = build_narrative(prof)

    return JSONResponse({
        "ok":            True,
        "engine_marker": BUILD_MARKER,
        "computed_for": {
            "user_id":  user_id,
            "date":     target.isoformat(),
            "age":      prof.age,
        },
        "profection": {
            "activated_house":        prof.activated_house,
            "profected_sign":         prof.profected_sign,
            "lord_of_the_year":       prof.lord_of_the_year,
            "modern_ruler":           prof.modern_ruler,
            "ruler_unavailable_reason": prof.ruler_unavailable_reason,
            "birthday_range":         prof.birthday_range,
            "element":                prof.element,
            "modality":               prof.modality,
            "is_current":             prof.is_current,
            "ruler_natal_condition":  prof.ruler_natal_condition,
            "profection_source":      prof.profection_source,
            "engine_marker":          prof.engine_marker,
        },
        "interpretation":  narrative,
        # Phase-3 forward-compat: emit the timing_signals wrapper too so
        # callers already reading the aggregated shape don't have to change
        # once the aggregator lands.
        "timing_signals": {
            "annual_profection": {
                "name":       f"{_ordinal(prof.activated_house)} House Year",
                "house":      prof.activated_house,
                "meaning":    narrative["what_area_is_asking_attention"],
                "confidence": "moderate",
                "supporting_signals": [
                    "natal chart (Variant-A / Equal houses)",
                    "traditional rulership table",
                    "birth-anchored 12-year cycle",
                ],
            },
        },
    }, headers={"Cache-Control": "no-store"})


# ---------------------------------------------------------------------------
# Endpoint 2 — profection series (past + future scrub)
# ---------------------------------------------------------------------------
@router.get("/profection/series")
async def profection_series(
    user_id:  str = Query(..., description="Mongo _id of the user."),
    from_age: int = Query(0,  ge=0, le=120,
                           description="Start age (inclusive)."),
    to_age:   int = Query(48, ge=0, le=120,
                           description="End age (inclusive)."),
):
    from server import db                                                # noqa: PLC0415
    from bson import ObjectId                                             # noqa: PLC0415
    from services.annual_profection_engine   import compute_profection_series  # noqa: PLC0415
    from services.annual_profection_narrative import build_narrative     # noqa: PLC0415

    try:
        oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid user_id: {e!s}")

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")

    chart     = await _resolve_natal_chart(user)
    birth_utc = _resolve_birth_utc(user)

    series = compute_profection_series(
        natal_chart        = chart,
        birth_datetime_utc = birth_utc,
        from_age           = from_age,
        to_age             = to_age,
    )
    return JSONResponse({
        "ok":            True,
        "engine_marker": BUILD_MARKER,
        "computed_for": {"user_id": user_id,
                          "from_age": from_age, "to_age": to_age},
        "years": [
            {
                "age":                     p.age,
                "activated_house":         p.activated_house,
                "profected_sign":          p.profected_sign,
                "lord_of_the_year":        p.lord_of_the_year,
                "modern_ruler":            p.modern_ruler,
                "birthday_range":          p.birthday_range,
                "element":                 p.element,
                "modality":                p.modality,
                "is_current":              p.is_current,
                # narrative summary — full body available via /profection endpoint
                "one_line_focus":          build_narrative(p)["what_area_is_asking_attention"],
            }
            for p in series
        ],
    }, headers={"Cache-Control": "no-store"})


def _ordinal(n: int) -> str:
    if 10 <= (n % 100) < 20: suf = "th"
    else: suf = {1:"st", 2:"nd", 3:"rd"}.get(n % 10, "th")
    return f"{n}{suf}"


# ---------------------------------------------------------------------------
# Endpoint 3 — aggregated timing signals (Phase 4)
# ---------------------------------------------------------------------------
@router.get("/signals/current")
async def timeline_signals(
    user_id: str = Query(..., description="Mongo _id of the user (24-hex)."),
    date:    Optional[str] = Query(
        None, description="Target date YYYY-MM-DD. Defaults to today (UTC)."),
    include_inactive: bool = Query(
        False, description="Surface engines that returned active=False."),
):
    """Aggregated `timing_signals` block from every registered TimingEngine.

    Currently registered plug-ins:
        • annual_profection

    Future plug-ins will appear here automatically once registered in
    `services.timing_evidence_layer.build_default_layer()`.
    """
    from server import db                                                 # noqa: PLC0415
    from bson import ObjectId                                              # noqa: PLC0415
    from services.timing_evidence_layer import build_default_layer         # noqa: PLC0415

    try:
        oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid user_id: {e!s}")

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")

    if date is None:
        target = datetime.now(_tz.utc).date()
    else:
        try:
            target = _date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400,
                                detail="date must be YYYY-MM-DD")

    chart     = await _resolve_natal_chart(user)
    birth_utc = _resolve_birth_utc(user)

    # Feed user-recorded events into the milestone engine if present.
    extras = {"events": (user.get("life_events") or [])
                        + (user.get("recognition_moments") or [])}

    layer = build_default_layer()
    agg = layer.aggregate(
        natal_chart        = chart,
        birth_datetime_utc = birth_utc,
        target_date        = target,
        extras             = extras,
        include_inactive   = include_inactive,
    )

    return JSONResponse({
        "ok":            True,
        "engine_marker": BUILD_MARKER,
        "computed_for":  {"user_id": user_id, "date": target.isoformat()},
        "timing_signals": agg["signals"],
        "protocol": {
            "protocol_marker": agg["protocol_marker"],
            "layer_marker":    agg["layer_marker"],
            "engines_run":     agg["engines_run"],
        },
    }, headers={"Cache-Control": "no-store"})
