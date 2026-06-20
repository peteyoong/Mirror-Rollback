"""Mirror Engine — standalone deterministic calculation API
============================================================

Build marker: mirror-engine-v1

Pure compute service.  Every endpoint here is a thin HTTP adapter
that:

  1. Parses the request body.
  2. Calls an existing calculation function from `calculations/`
     or `services/` exactly the way the monolith's routers do.
  3. Returns the function's native return shape unchanged.

No DB.  No auth.  No chat.  No LLM.  No product-specific logic.

The function signatures these endpoints proxy were lifted from
the monolith without modification — search for `get_full_natal_chart`,
`get_human_design_chart`, `get_canonical_numerology`,
`compute_bazi_chart_v2`, `compute_natal_object`, etc., for the
canonical implementations.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import swisseph as swe
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# Path & ephemeris setup
# ----------------------------------------------------------------------
# Pin the working directory so `calculations.*` / `services.*` resolve as
# top-level packages exactly the way they do in the monolith.  Inside the
# Docker image WORKDIR is /app and these dirs are siblings — locally we
# add the project root to sys.path so the same imports work.
_ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _ENGINE_ROOT)

# Ephemeris path — settable via env var, defaults to ./ephe sibling to app/.
_DEFAULT_EPHE = os.path.join(_ENGINE_ROOT, "ephe")
_EPHE_PATH = os.environ.get("EPHE_PATH", _DEFAULT_EPHE)
try:
    swe.set_ephe_path(_EPHE_PATH)
except Exception:
    pass

# ----------------------------------------------------------------------
# Deterministic calculation imports (same names the monolith uses)
# ----------------------------------------------------------------------
from calculations.astrology import (
    get_full_natal_chart,
)
from calculations.human_design import (
    get_human_design_chart,
)
from calculations.numerology import (
    get_full_numerology,
    get_canonical_numerology,
)
from services.numerology_compute_service import (
    compute_numerology_deterministic,
)
from services.bazi_engine_v2 import compute_bazi_chart_v2
from services.natal_object_engine import compute_natal_object
from services.enneagram_source import resolve_with_source

# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
ENGINE_VERSION = "mirror-engine-v1"

app = FastAPI(
    title="Mirror Engine",
    description=(
        "Standalone deterministic calculation service for the Mirror "
        "product family.  Pure compute — no DB, no LLM, no auth."
    ),
    version=ENGINE_VERSION,
)


# ----------------------------------------------------------------------
# Pydantic request schemas
# ----------------------------------------------------------------------
class _LocationBody(BaseModel):
    birth_datetime_utc: str = Field(
        ...,
        description="ISO-8601 UTC birth datetime, e.g. '1981-07-12T23:55:00Z'.",
    )
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class AstrologyNatalBody(_LocationBody):
    house_system: Optional[str] = "Equal"
    node_mode: Optional[str] = "true_node"
    sidereal_settings: Optional[Dict[str, Any]] = None


class AstrologyTransitBody(_LocationBody):
    target_datetime_utc: Optional[str] = Field(
        None,
        description=(
            "ISO-8601 UTC datetime to compute transits *for*.  Defaults "
            "to the current server UTC time."
        ),
    )


class AstrologyObjectsBody(_LocationBody):
    objects: List[str] = Field(
        ...,
        description=(
            "Object names to resolve from the natal chart, e.g. "
            "['Juno','Vertex','Chiron','Black Moon Lilith']."
        ),
    )
    house_system: Optional[str] = "Equal"
    node_mode: Optional[str] = "true_node"


class HumanDesignBody(_LocationBody):
    sidereal_settings: Optional[Dict[str, Any]] = None


class NumerologyBody(BaseModel):
    birth_date: str = Field(
        ...,
        description="ISO date, e.g. '1981-07-13'.  Time-of-day is ignored.",
    )
    full_name: Optional[str] = None


class BaziBody(BaseModel):
    birth_datetime_utc: str = Field(
        ...,
        description="ISO-8601 UTC birth datetime.",
    )


class EnneagramBody(BaseModel):
    enneagram_type: Optional[int] = Field(None, ge=1, le=9)
    enneagram_results: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _parse_utc(value: str, *, field: str = "birth_datetime_utc") -> datetime:
    """Parse an ISO-8601 UTC string into a tz-aware UTC datetime."""
    if not value:
        raise HTTPException(status_code=422, detail={
            "code": "missing_field", "field": field,
        })
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception as e:
        raise HTTPException(status_code=422, detail={
            "code": "invalid_datetime", "field": field,
            "message": f"could not parse {value!r}: {e}",
        })
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _parse_date(value: str, *, field: str = "birth_date") -> datetime:
    """Parse a date or datetime string into a tz-naive midnight datetime."""
    if not value:
        raise HTTPException(status_code=422, detail={
            "code": "missing_field", "field": field,
        })
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1]
    try:
        # Accept either 'YYYY-MM-DD' or full ISO datetime.
        if "T" in s or " " in s:
            return datetime.fromisoformat(s.replace("T", " ").split("+")[0].split("Z")[0])
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=422, detail={
            "code": "invalid_date", "field": field,
            "message": f"could not parse {value!r}: {e}",
        })


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------
@app.get("/health")
async def health():
    """Liveness probe.  Returns engine version + ephemeris-path status."""
    ephe_ok = os.path.isdir(_EPHE_PATH) and any(
        f.endswith(".se1") for f in os.listdir(_EPHE_PATH)
    ) if os.path.isdir(_EPHE_PATH) else False
    return {
        "status":      "ok",
        "version":     ENGINE_VERSION,
        "ephe_path":   _EPHE_PATH,
        "ephe_loaded": ephe_ok,
    }


# ── Astrology ─────────────────────────────────────────────────────────
@app.post("/compute/astrology/natal")
async def compute_astrology_natal(body: AstrologyNatalBody):
    """Full True-Sidereal natal chart (10 planets + chart points + houses).
    Mirrors `calculations.astrology.get_full_natal_chart` exactly."""
    dt = _parse_utc(body.birth_datetime_utc)
    return get_full_natal_chart(
        birth_datetime=dt,
        lat=body.lat,
        lon=body.lon,
        sidereal_settings=body.sidereal_settings,
        house_system=body.house_system or "Equal",
        node_mode=body.node_mode or "true_node",
    )


@app.post("/compute/astrology/transits")
async def compute_astrology_transits(body: AstrologyTransitBody):
    """Active transits for `target_datetime_utc` (defaults to now) aspecting
    the natal chart at `birth_datetime_utc / lat / lon`.  Builds the same
    payload the monolith's `/api/astrology/transit-aspects/{user_id}`
    route returns.

    Computation path: build natal chart, build transit chart at the
    target datetime, then return both for the caller to diff.  Pure
    compute — the caller layers narrative on top.
    """
    natal_dt = _parse_utc(body.birth_datetime_utc, field="birth_datetime_utc")
    if body.target_datetime_utc:
        target_dt = _parse_utc(body.target_datetime_utc, field="target_datetime_utc")
    else:
        target_dt = datetime.now(timezone.utc)
    natal = get_full_natal_chart(
        birth_datetime=natal_dt, lat=body.lat, lon=body.lon,
    )
    transit = get_full_natal_chart(
        birth_datetime=target_dt, lat=body.lat, lon=body.lon,
    )
    return {
        "natal_chart":    natal,
        "transit_chart":  transit,
        "target_utc":     target_dt.isoformat(),
        "build_marker":   ENGINE_VERSION,
    }


@app.post("/compute/astrology/objects")
async def compute_astrology_objects(body: AstrologyObjectsBody):
    """Resolve one-or-more advanced natal objects (Juno / Vertex /
    Chiron / Black Moon Lilith / Lots / Eros / Psyche / Astraea /
    Hygiea / Eris / Sun..Pluto / nodes) from the natal chart.  Returns
    one envelope per requested object using the same `compute_natal_object`
    contract the monolith uses."""
    if not body.objects:
        raise HTTPException(status_code=422, detail={
            "code": "objects_required",
            "message": "Pass a non-empty 'objects' array.",
        })
    dt = _parse_utc(body.birth_datetime_utc)
    chart = get_full_natal_chart(
        birth_datetime=dt, lat=body.lat, lon=body.lon,
        house_system=body.house_system or "Equal",
        node_mode=body.node_mode or "true_node",
    )
    chart_envelope = {"astrology": chart}
    results: Dict[str, Any] = {}
    for name in body.objects:
        results[name] = compute_natal_object(chart_envelope, name)
    return {
        "results":      results,
        "build_marker": ENGINE_VERSION,
    }


# ── Human Design ──────────────────────────────────────────────────────
@app.post("/compute/human-design/bodygraph")
async def compute_human_design_bodygraph(body: HumanDesignBody):
    """Full Human Design bodygraph (Type / Strategy / Authority / Profile /
    Definition / Centers / Channels / Gates / Variables).  Mirrors
    `calculations.human_design.get_human_design_chart`."""
    dt = _parse_utc(body.birth_datetime_utc)
    return get_human_design_chart(
        birth_datetime=dt,
        lat=body.lat,
        lon=body.lon,
        sidereal_settings=body.sidereal_settings,
    )


# ── Numerology ────────────────────────────────────────────────────────
@app.post("/compute/numerology/full")
async def compute_numerology_full(body: NumerologyBody):
    """Full numerology profile (Life Path, Expression, Soul Urge,
    Personality, Lo Shu grid, cycles).  Uses the canonical deterministic
    compute path so output matches the monolith's
    `services.numerology_compute_service.compute_numerology_deterministic`."""
    dt = _parse_date(body.birth_date)
    if body.full_name:
        return compute_numerology_deterministic(
            birth_date=dt, full_name=body.full_name,
        )
    # Legacy DOB-only payload — no Expression/SU/Personality (name-derived).
    return get_full_numerology(birth_date=dt, full_name=None)


# ── BaZi ──────────────────────────────────────────────────────────────
@app.post("/compute/bazi/four-pillars")
async def compute_bazi_four_pillars(body: BaziBody):
    """Four-pillar BaZi chart.  Mirrors
    `services.bazi_engine_v2.compute_bazi_chart_v2`."""
    dt = _parse_utc(body.birth_datetime_utc)
    # BaZi engine operates on tz-naive datetimes (classical Chinese calendar
    # logic compares against naive datetime literals).  Strip tzinfo *after*
    # we've already normalised to UTC so the wall-clock values are preserved.
    naive_dt = dt.replace(tzinfo=None)
    return compute_bazi_chart_v2(birth_date=naive_dt)


# ── Enneagram ─────────────────────────────────────────────────────────
@app.post("/compute/enneagram/resolve")
async def compute_enneagram_resolve(body: EnneagramBody):
    """Resolve a canonical Enneagram type from either an explicit
    `enneagram_type` or an `enneagram_results` envelope produced by the
    quiz.  Returns `(type, source)` plus the raw input echoed back for
    auditability.  Mirrors
    `services.enneagram_source.resolve_with_source`."""
    user_doc: Dict[str, Any] = {}
    if body.enneagram_type is not None:
        user_doc["enneagram_type"] = body.enneagram_type
    if body.enneagram_results is not None:
        user_doc["enneagram_results"] = body.enneagram_results
    if not user_doc:
        raise HTTPException(status_code=422, detail={
            "code": "missing_input",
            "message": "Provide enneagram_type or enneagram_results.",
        })
    e_type, source = resolve_with_source(user_doc)
    return {
        "enneagram_type": e_type,
        "source":         source,
        "build_marker":   ENGINE_VERSION,
    }
