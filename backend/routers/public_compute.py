"""public_compute.py — Public deterministic profile compute API
================================================================

Stateless, unauthenticated aggregator endpoint that wraps the four
canonical Mirror calculation engines (Astrology, Human Design,
Numerology, BaZi) into a single round-trip suitable for external
consumer frontends (e.g. the kimi.page B2C client).

Build marker:  public-compute-v1
Mounted at:    POST /api/v1/profile/full
Auth:          NONE — pure compute, no DB writes, no user context

The compute functions invoked here are the EXACT same ones the
authenticated `/api/charts/calculate` path uses, so the output is
byte-for-byte identical to what the monolith produces internally.
Engine version is stamped as Variant A canonical so downstream
consumers can detect drift.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Canonical calculation engines — same imports server.py uses.
from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart
from calculations.numerology import get_full_numerology
from services.numerology_compute_service import compute_numerology_deterministic
from services.bazi_engine_v2 import compute_bazi_chart_v2

logger = logging.getLogger("public_compute")

ROUTE_BUILD_MARKER       = "public-compute-v1"
VARIANT_A_ENGINE_VERSION = "midpoint13_variant_a_v1"

router = APIRouter(prefix="/api/v1", tags=["public-compute"])


# ----------------------------------------------------------------------
# Pydantic request schema
# ----------------------------------------------------------------------
class ProfileFullRequest(BaseModel):
    birth_date: str = Field(
        ...,
        description="ISO date 'YYYY-MM-DD', e.g. '1968-04-01'.",
        examples=["1968-04-01"],
    )
    birth_time: str = Field(
        ...,
        description="24-h local clock time 'HH:MM' or 'HH:MM:SS'.",
        examples=["01:25"],
    )
    timezone_offset: float = Field(
        ...,
        ge=-14.0, le=14.0,
        description=(
            "Hours east of UTC at the moment of birth.  Positive=east, "
            "negative=west.  Fractional values supported (e.g. 7.5 for "
            "Malaysia +07:30 pre-1982, 5.75 for Nepal +05:45)."
        ),
        examples=[7.5, -3.0, 5.75],
    )
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    full_name: Optional[str] = Field(
        None,
        description=(
            "Birth name for Pythagorean numerology (Expression / Soul "
            "Urge / Personality).  Optional — omit for date-only "
            "numerology."
        ),
    )


# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------
def _parse_local_birth_to_utc(req: ProfileFullRequest) -> datetime:
    """Combine birth_date + birth_time + timezone_offset → tz-aware UTC.

    Uses millisecond-level offset arithmetic so fractional zones (Nepal
    +05:45, pre-1982 Malaysia +07:30) round-trip without truncation.
    """
    try:
        date_str = req.birth_date.strip()
        time_str = req.birth_time.strip()
        if len(time_str.split(":")) == 2:
            time_str = time_str + ":00"
        local_naive = datetime.strptime(
            f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S",
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_datetime",
                "message": (
                    f"Could not parse birth_date={req.birth_date!r} "
                    f"birth_time={req.birth_time!r}: {e}"
                ),
            },
        )

    # Build a fixed-offset tz from the fractional hours, then convert.
    tz = timezone(timedelta(hours=float(req.timezone_offset)))
    local_aware = local_naive.replace(tzinfo=tz)
    return local_aware.astimezone(timezone.utc)


# ----------------------------------------------------------------------
# Endpoint
# ----------------------------------------------------------------------
@router.post("/profile/full")
async def compute_profile_full(req: ProfileFullRequest) -> Dict[str, Any]:
    """Compute the full deterministic Mirror profile in one round-trip.

    Returns the canonical Variant A astrology / Human Design / numerology
    / BaZi payloads exactly as the authenticated chart endpoints emit
    them, plus top-level `engine_version` and `computation_timestamp`
    so external clients can detect drift without unpacking nested keys.
    """
    birth_utc = _parse_local_birth_to_utc(req)
    birth_local_naive = birth_utc.astimezone(
        timezone(timedelta(hours=float(req.timezone_offset)))
    ).replace(tzinfo=None)

    # ── Astrology (Variant A 13-sign true-sidereal canonical) ─────────
    try:
        astrology = get_full_natal_chart(
            birth_datetime=birth_utc,
            lat=req.lat,
            lon=req.lon,
        )
    except Exception as e:
        logger.exception("[public_compute] astrology failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "astrology_failed", "message": str(e)},
        )

    # ── Human Design ──────────────────────────────────────────────────
    try:
        human_design = get_human_design_chart(
            birth_datetime=birth_utc,
            lat=req.lat,
            lon=req.lon,
        )
    except Exception as e:
        logger.exception("[public_compute] human_design failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "human_design_failed", "message": str(e)},
        )

    # ── Numerology ────────────────────────────────────────────────────
    # Use the deterministic full-name path when name is provided (gives
    # Expression / Soul Urge / Personality); otherwise the date-only
    # canonical path.
    try:
        if req.full_name:
            numerology = compute_numerology_deterministic(
                birth_date=birth_local_naive,
                full_name=req.full_name,
            )
        else:
            numerology = get_full_numerology(
                birth_date=birth_local_naive,
                full_name=None,
            )
    except Exception as e:
        logger.exception("[public_compute] numerology failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "numerology_failed", "message": str(e)},
        )

    # ── BaZi (classical Four Pillars; tz-naive wall-clock) ────────────
    try:
        bazi = compute_bazi_chart_v2(birth_date=birth_local_naive)
    except Exception as e:
        logger.exception("[public_compute] bazi failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "bazi_failed", "message": str(e)},
        )

    return {
        "astrology":             astrology,
        "human_design":          human_design,
        "numerology":            numerology,
        "bazi":                  bazi,
        "enneagram":             None,  # quiz-driven; not computable from DOB.
        "engine_version":        VARIANT_A_ENGINE_VERSION,
        "computation_timestamp": datetime.now(timezone.utc).isoformat(),
        "build_marker":          ROUTE_BUILD_MARKER,
        "input_echo": {
            "birth_date":      req.birth_date,
            "birth_time":      req.birth_time,
            "timezone_offset": req.timezone_offset,
            "lat":             req.lat,
            "lon":             req.lon,
            "birth_utc":       birth_utc.isoformat(),
            "full_name_used":  bool(req.full_name),
        },
    }
