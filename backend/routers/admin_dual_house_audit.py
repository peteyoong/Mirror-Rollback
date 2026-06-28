"""admin_dual_house_audit.py — GM parity diagnostic endpoint
================================================================
Surface marker: dual-house-audit-v2

Purpose
-------
Provide a read-only side-by-side audit for a single user so the
operator can compare:

  • Mirror canonical chart  → True Sidereal-M / Variant-A 13-sign /
    Equal Houses (Asc = 1st). This is the production system.

  • GM reference modes — TWO separate views, not merged:
       1. gm_reference_placidus    – computed Placidus cusps using
          Swiss Ephemeris with the same SVP / sidereal frame as
          Mirror. Matches the "House: Placidus" panel on GM PDFs.
       2. gm_reference_equal_overlay – the same Equal houses Mirror
          uses, surfaced explicitly so the GM natal wheel ("Equal
          (Asc = 1st)") and the GM house panel ("Placidus") never
          collapse into a single confused target.

Validation policy
-----------------
Variant-A constellation widths are unequal (Virgo ≈ 49.71°, Taurus
≈ 36.86°, Pisces ≈ 41.99°). A within-sign degree > 30° is NOT a
bug — it is the real offset against a real constellation span.
The endpoint flags a planet position as invalid only when:

    degree_within_sign < 0  OR  degree_within_sign >= sign_width

where sign_width comes from the Athen/Sharatan Variant-A table.

The endpoint is read-only, requires a confirm token, and never
mutates the canonical Mirror system. It is safe to leave deployed.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

CONFIRM_TOKEN = "DUAL_HOUSE_AUDIT_2026_06_28"
BUILD_MARKER  = "dual-house-audit-v2"

PLANETS_OF_INTEREST = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "North Node", "South Node", "Chiron", "Earth",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _variant_a_width_lookup() -> Dict[str, float]:
    """Map sign-name → constellation width (degrees) from the Variant-A
    Athen / Sharatan boundary table. Source of truth lives in
    calculations/sign_attribution.py so we never drift."""
    from calculations.sign_attribution import (   # noqa: PLC0415
        MIDPOINT_BOUNDARIES_VARIANT_A,
    )
    out: Dict[str, float] = {}
    for name, start, end in MIDPOINT_BOUNDARIES_VARIANT_A:
        if start <= end:
            width = end - start
        else:                       # Pisces wrap
            width = (360.0 - start) + end
        out[name] = round(width, 6)
    return out


def _is_invalid_position(sign: Optional[str],
                          degree: Optional[float],
                          widths: Dict[str, float]) -> bool:
    """Variant-A validity check: 0 <= degree < sign_width."""
    if sign is None or degree is None:
        return False
    try:
        d = float(degree)
    except (TypeError, ValueError):
        return False
    w = widths.get(sign)
    if w is None:
        # Unknown sign → can't validate; surface for inspection
        return True
    return d < 0.0 or d >= w


def _planet_view(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a stable planet view from a chart payload."""
    out: Dict[str, Any] = {}
    planets = chart.get("planets") or {}
    # Support both dict-of-name and list-of-dict shapes
    if isinstance(planets, dict):
        items = planets.items()
    elif isinstance(planets, list):
        items = [(p.get("name") or p.get("planet"), p)
                 for p in planets if isinstance(p, dict)]
    else:
        return out
    for name, p in items:
        if name not in PLANETS_OF_INTEREST or not isinstance(p, dict):
            continue
        out[name] = {
            "sign":      p.get("sign"),
            "degree":    round(float(p.get("degree") or 0.0), 4),
            "longitude": round(float(p.get("longitude") or 0.0), 4),
            "house":     p.get("house"),
        }
    return out


def _angle_view(chart: Dict[str, Any]) -> Dict[str, Any]:
    ang = chart.get("angles") or {}
    out: Dict[str, Any] = {}
    for k, v in ang.items():
        if not isinstance(v, dict):
            continue
        out[k] = {
            "sign":      v.get("sign"),
            "degree":    round(float(v.get("degree") or 0.0), 4),
            "longitude": round(float(v.get("longitude") or 0.0), 4),
        }
    return out


def _house_cusp_view(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    houses = chart.get("houses")
    out: List[Dict[str, Any]] = []
    # `get_full_natal_chart` returns houses as a dict with a
    # `formatted_cusps` list (12 items). Some legacy callers pass a
    # bare list directly. Support both shapes.
    if isinstance(houses, dict):
        items = houses.get("formatted_cusps") or []
    elif isinstance(houses, list):
        items = houses
    else:
        items = []
    for h in items:
        if not isinstance(h, dict):
            continue
        out.append({
            "house":  h.get("house"),
            "sign":   h.get("sign"),
            "degree": round(float(h.get("degree") or 0.0), 4),
            "cusp":   round(float(h.get("cusp") or 0.0), 4),
        })
    return out


def _build_house_comparison(equal_houses: List[Dict[str, Any]],
                             placidus_houses: List[Dict[str, Any]]
                             ) -> List[Dict[str, Any]]:
    """House | Equal (Mirror) | Placidus (GM-ref) | Δ°-on-cusp | match?"""
    rows: List[Dict[str, Any]] = []
    by_num_e = {h.get("house"): h for h in equal_houses}
    by_num_p = {h.get("house"): h for h in placidus_houses}
    for n in range(1, 13):
        e = by_num_e.get(n) or {}
        p = by_num_p.get(n) or {}
        try:
            d = abs((float(e.get("cusp", 0.0)) - float(p.get("cusp", 0.0))) % 360.0)
            if d > 180.0:
                d = 360.0 - d
        except Exception:
            d = None
        rows.append({
            "house":             n,
            "mirror_equal": {
                "sign":   e.get("sign"),
                "degree": e.get("degree"),
                "cusp":   e.get("cusp"),
            },
            "gm_ref_placidus": {
                "sign":   p.get("sign"),
                "degree": p.get("degree"),
                "cusp":   p.get("cusp"),
            },
            "cusp_delta_degrees": round(d, 4) if d is not None else None,
            "match_within_0_1":   (d is not None and d <= 0.1),
        })
    return rows


def _planet_house_delta_table(equal_p: Dict[str, Any],
                               placidus_p: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Planet rows where Equal-house ≠ Placidus-house assignment."""
    rows: List[Dict[str, Any]] = []
    for n in PLANETS_OF_INTEREST:
        he = (equal_p.get(n) or {}).get("house")
        hp = (placidus_p.get(n) or {}).get("house")
        if he is not None and hp is not None and he != hp:
            rows.append({
                "planet":         n,
                "equal_house":    he,
                "placidus_house": hp,
                "sign":           (equal_p.get(n) or {}).get("sign"),
                "degree":         (equal_p.get(n) or {}).get("degree"),
            })
    return rows


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.get("/dual_house_audit")
async def dual_house_audit(
    user_id: str = Query(..., description="Mongo _id of the user (24-hex)."),
    confirm: str = Query("", description="Required confirm token."),
):
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail="confirm token required")

    # Late imports keep this router decoupled from server.py boot order.
    from server import db                                          # noqa: PLC0415
    from bson import ObjectId                                       # noqa: PLC0415
    from calculations.astrology import get_full_natal_chart         # noqa: PLC0415
    from calculations.timezone_utils import resolve_birth_utc_with_debug  # noqa: PLC0415

    try:
        oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid user_id: {e!s}")

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")

    loc = (user.get("birth_location") or {})
    lat, lon = loc.get("latitude"), loc.get("longitude")
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="missing lat/lon for user")

    # Normalize possibly datetime fields to strings expected by the resolver.
    birth_date_raw = user.get("birth_date")
    if hasattr(birth_date_raw, "strftime"):
        birth_date_str = birth_date_raw.strftime("%Y-%m-%d")
    else:
        birth_date_str = str(birth_date_raw or "").strip()[:10]

    resolved = resolve_birth_utc_with_debug(
        birth_date_str,
        user.get("birth_time"),
        user.get("timezone"),
    )
    if not resolved.get("success"):
        raise HTTPException(
            status_code=400,
            detail=f"timezone resolution failed: {resolved.get('error_message') or resolved.get('error')}",
        )
    resolved_utc = resolved["birth_utc"]
    tz_debug     = resolved.get("debug_stamp", {})

    # Compute two charts — same astronomy, two house systems.
    chart_equal    = get_full_natal_chart(
        birth_datetime=resolved_utc, lat=lat, lon=lon, house_system="Equal",
    )
    chart_placidus = get_full_natal_chart(
        birth_datetime=resolved_utc, lat=lat, lon=lon, house_system="Placidus",
    )

    widths = _variant_a_width_lookup()

    equal_p     = _planet_view(chart_equal)
    placidus_p  = _planet_view(chart_placidus)
    equal_a     = _angle_view(chart_equal)
    placidus_a  = _angle_view(chart_placidus)
    equal_h     = _house_cusp_view(chart_equal)
    placidus_h  = _house_cusp_view(chart_placidus)

    # Variant-A validity sweep — flag any sign/degree outside [0, sign_width).
    invalid_positions: List[Dict[str, Any]] = []
    for n, view in equal_p.items():
        if _is_invalid_position(view.get("sign"), view.get("degree"), widths):
            invalid_positions.append({
                "kind": "planet", "name": n, **view,
                "sign_width": widths.get(view.get("sign")),
            })
    for k, v in equal_a.items():
        if _is_invalid_position(v.get("sign"), v.get("degree"), widths):
            invalid_positions.append({
                "kind": "angle", "name": k, **v,
                "sign_width": widths.get(v.get("sign")),
            })

    return JSONResponse({
        "ok":            True,
        "build_marker":  BUILD_MARKER,
        "checked_at":    datetime.now(timezone.utc).isoformat(),
        "user": {
            "id":          user_id,
            "name":        user.get("name"),
            "birth_date":  str(user.get("birth_date")),
            "birth_time":  user.get("birth_time"),
            "timezone":    user.get("timezone"),
            "location":    {"latitude": lat, "longitude": lon,
                            "city": loc.get("city"), "country": loc.get("country")},
            "resolved_utc": resolved_utc.isoformat() if resolved_utc else None,
            "timezone_debug": tz_debug,
        },

        # --- Mirror canonical (production) ------------------------------
        "mirror_canonical": {
            "house_system":      "Equal",
            "zodiac_mode":       "Variant-A (13-sign, Sharatan SVP=31.2836°)",
            "ayanamsa_degrees":  31.2836,
            "planets":           equal_p,
            "angles":            equal_a,
            "house_cusps":       equal_h,
        },

        # --- GM reference views (TWO separate modes, never merged) -------
        # 1) GM "House: Placidus" panel — actual Placidus cusps computed
        #    in Mirror's sidereal frame for like-for-like comparison.
        "gm_reference_placidus": {
            "label":             "GM PDF panel: House: Placidus",
            "house_system":      "Placidus",
            "zodiac_mode":       "Variant-A (13-sign, Sharatan SVP=31.2836°)",
            "ayanamsa_degrees":  31.2836,
            "planets":           placidus_p,
            "angles":            placidus_a,
            "house_cusps":       placidus_h,
        },
        # 2) GM natal wheel — Equal houses (Asc = 1st). Identical to the
        #    Mirror canonical view; surfaced explicitly so the two GM
        #    reference modes never collapse into a single target.
        "gm_reference_equal_overlay": {
            "label":             "GM PDF natal wheel: Equal (Asc = 1st)",
            "house_system":      "Equal",
            "note":              "Identical to mirror_canonical by construction.",
            "planets":           equal_p,
            "angles":            equal_a,
            "house_cusps":       equal_h,
        },

        # --- Cross-mode diagnostics --------------------------------------
        "house_cusp_comparison":   _build_house_comparison(equal_h, placidus_h),
        "planet_house_deltas":     _planet_house_delta_table(equal_p, placidus_p),
        "invalid_positions":       invalid_positions,
        "variant_a_widths":        widths,

        # Operator note: validity is judged against real constellation
        # widths, NOT against a 0–30° box. Virgo ~49.71°, etc.
        "validity_policy": (
            "Variant-A allows degree_within_sign up to (but not including) "
            "the real sign_width. Degrees above 30° are valid when the "
            "constellation is wider than 30°."
        ),
    }, headers={"Cache-Control": "no-store"})
