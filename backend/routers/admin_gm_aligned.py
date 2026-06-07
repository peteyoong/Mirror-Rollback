"""
GM-Aligned Migration + Forensic Comparison
==========================================
Build marker: gm-aligned-v1

POST /api/admin/gm-aligned-recompute
    Recomputes every user's astrology chart with the new default
    house_system='Placidus' (GM-aligned), recomputes HD (picks up
    the corrected Incarnation Cross variant numbering), and
    invalidates all derived caches (today_v6, life_lens, deep_dive,
    relationship_mappings, forum_hd_mappings, home_insight).

GET  /api/admin/gm-forensic-ana
    Returns Mirror's current output for Ana Gayoso's birth inputs
    side-by-side with GM's gold-standard expected values.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from fastapi import APIRouter
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin-gm-aligned"])

ASTRO_ENGINE_VERSION = "gm-aligned-v1"
HD_ENGINE_VERSION    = "gm-aligned-v1"
# ---------------------------------------------------------------------------
# FORENSIC V2 FREEZE (2026-05-31)  +  house-system-source-of-truth-v1 (2026-06-07):
# The previous fork's switch to Placidus was based on Ana's PDF only. Pete and
# Mel's GM screenshots explicitly say "House: Equal". Therefore there is NO
# evidence that GM uses Placidus universally — see
# /app/memory/gm_forensic_audit_2026-05-31.md
# Mirror's canonical default is "Equal". Placidus remains an OPTIONAL house
# system available via `house_system="Placidus"` on the engine.
#
# Source of truth: imported from calculations.astrology — the ONLY place
# in the codebase that should declare the canonical value.
# ---------------------------------------------------------------------------
from calculations.astrology import CANONICAL_HOUSE_SYSTEM  # noqa: E402, F401


@router.get("/gm-forensic-ana")
async def gm_forensic_ana():
    """Forensic comparison: Mirror vs GM gold standard for Ana Gayoso."""
    from calculations.astrology import get_full_natal_chart
    from calculations.human_design import get_human_design_chart

    local = datetime(1983, 5, 3, 8, 20, 0, tzinfo=timezone(timedelta(hours=-3)))
    utc   = local.astimezone(timezone.utc)
    lat, lon = -34.5438, -58.715302

    chart_placidus = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon, house_system="Placidus")
    chart_equal    = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon, house_system="Equal")
    chart = chart_placidus
    hd    = get_human_design_chart(birth_datetime=utc, lat=lat, lon=lon)

    angles  = chart.get("angles") or {}
    planets = chart.get("planets") or {}

    def _sign(p):
        return (planets.get(p) or {}).get("sign")
    def _house(p):
        return (planets.get(p) or {}).get("house")

    gm_expected = {
        "Sun":      {"sign": "Aries"},
        "Moon":     {"sign": "Sagittarius"},
        "ASC":      {"sign": "Aries"},
        "type":     "Manifesting Generator",
        "profile":  "3/5",
        "authority": "Sacral",
        "channels": [(20, 34), (26, 44), (28, 38)],
        "incarnation_cross_name": "Right Angle Cross of Tension 1",
    }

    mirror_actual = {
        "Sun":      {"sign": _sign("Sun"),  "house": _house("Sun")},
        "Moon":     {"sign": _sign("Moon"), "house": _house("Moon")},
        "ASC":      {"sign": (angles.get("asc") or {}).get("sign"),
                     "longitude": (angles.get("asc") or {}).get("longitude")},
        "MC":       {"sign": (angles.get("mc") or {}).get("sign")},
        "type":     hd.get("type"),
        "profile":  hd.get("profile"),
        "authority": hd.get("authority"),
        "channels": [
            (c.get("gate1"), c.get("gate2"))
            for c in (hd.get("defined_channels") or hd.get("channels") or [])
        ],
        "incarnation_cross": hd.get("incarnation_cross"),
    }

    # Match flags
    checks: List[Dict[str, Any]] = []
    for key in ("Sun", "Moon", "ASC"):
        checks.append({
            "field":    key,
            "expected": gm_expected[key]["sign"],
            "actual":   mirror_actual[key].get("sign"),
            "match":    mirror_actual[key].get("sign") == gm_expected[key]["sign"],
        })
    for key in ("type", "profile", "authority"):
        v = mirror_actual[key]
        if key == "type" and isinstance(v, str) and "Manifesting Generator" in v:
            match = True
        else:
            match = v == gm_expected[key]
        checks.append({"field": key, "expected": gm_expected[key],
                       "actual": v, "match": match})
    channels_match = sorted([tuple(sorted(c)) for c in mirror_actual["channels"]]) == \
                     sorted([tuple(sorted(c)) for c in gm_expected["channels"]])
    checks.append({"field": "channels",
                   "expected": gm_expected["channels"],
                   "actual":   mirror_actual["channels"],
                   "match":    channels_match})
    ic_name = (mirror_actual["incarnation_cross"] or {}).get("name") if mirror_actual["incarnation_cross"] else None
    checks.append({"field": "incarnation_cross_name",
                   "expected": gm_expected["incarnation_cross_name"],
                   "actual":   ic_name,
                   "match":    ic_name == gm_expected["incarnation_cross_name"]})

    return {
        "marker":                 "gm-forensic-ana-v2",
        "gm_aligned_phase":       2,
        "placidus_cusps_source":  "swisseph.houses_ex",
        "birth_inputs":           {"utc": utc.isoformat(), "lat": lat, "lon": lon},
        "astro_engine_version":   ASTRO_ENGINE_VERSION,
        "hd_engine_version":      HD_ENGINE_VERSION,
        "canonical_house_system": CANONICAL_HOUSE_SYSTEM,
        "gm_expected":            gm_expected,
        "mirror_actual":          mirror_actual,
        "checks":                 checks,
        "placidus_house_checks":  _placidus_check(chart_placidus),
        "side_by_side": {
            "equal":    _planet_houses(chart_equal),
            "placidus": _planet_houses(chart_placidus),
            "asc_equal":    ((chart_equal.get("angles") or {}).get("asc") or {}).get("sign"),
            "asc_placidus": ((chart_placidus.get("angles") or {}).get("asc") or {}).get("sign"),
            "mc_equal":     ((chart_equal.get("angles") or {}).get("mc") or {}).get("sign"),
            "mc_placidus":  ((chart_placidus.get("angles") or {}).get("mc") or {}).get("sign"),
        },
        "all_pass":               all(c["match"] for c in checks)
                                  and all(p["match"] for p in _placidus_check(chart_placidus)),
    }


_EXPECTED_PLACIDUS_HOUSES = {
    "Sun": 12, "Moon": 8, "Mercury": 1, "Venus": 2, "Mars": 12,
    "Jupiter": 7, "Saturn": 6, "Uranus": 7, "Neptune": 8,
    "Pluto": 5, "Chiron": 1, "Juno": 10,
}


def _planet_houses(chart):
    return {p: (chart.get("planets") or {}).get(p, {}).get("house")
            for p in _EXPECTED_PLACIDUS_HOUSES.keys()}


def _placidus_check(chart):
    out = []
    actual = _planet_houses(chart)
    for p, exp in _EXPECTED_PLACIDUS_HOUSES.items():
        got = actual.get(p)
        out.append({"field": f"{p}.house", "expected": exp,
                    "actual": got, "match": got == exp})
    angles = chart.get("angles") or {}
    asc = (angles.get("asc") or {}).get("sign")
    mc  = (angles.get("mc") or {}).get("sign")
    out.append({"field": "ASC.sign", "expected": "Aries", "actual": asc, "match": asc == "Aries"})
    out.append({"field": "MC.sign",  "expected": "Capricorn", "actual": mc,  "match": mc == "Capricorn"})
    return out


# Caches that store derived/lensed payloads keyed off the natal chart.
# These MUST be invalidated after a Placidus/GM recompute so users do not
# see stale Equal-house interpretations.
_DERIVED_CACHE_COLLECTIONS = (
    "daily_astrology",
    "astrology_timeline_cache",
    "deep_dive_cache",
    "life_lens_cache",
    "lifeline_synthesis_cache",
    "lunar_synthesis_cache",
    "relationship_mappings",
    "relationship_today_cache",
    "forum_story_cache",
    "forum_hd_mappings_cache",
    "home_insight_cache",
    "governing_chapter_cache",
    "pattern_mirror_cache",
    "pattern_drift_cache",
    "today_patterns",
    "today_cache",
    "timeline_cache",
    "daily_focus",
    "daily_keystones",
    "daily_pattern_signals",
)

# Tokens required to actually mutate data — guards against accidental
# triggering of a destructive recompute on production.
#
# FORENSIC V2 FREEZE (2026-05-31): the previous Placidus migration is FROZEN.
# The old token ("GM_PLACIDUS_RECOMPUTE_V1") is intentionally rotated so any
# previously-typed curl commands DO NOT mutate the database. A new token will
# only be issued after the gm-true-sidereal-forensic-v2 investigation
# concludes and the user explicitly approves.
_RECOMPUTE_CONFIRM_TOKEN = "__FROZEN__GM_FORENSIC_V2_PENDING__"
_MIGRATION_FROZEN = True
_MIGRATION_FREEZE_REASON = (
    "GM forensic audit (2026-05-31) showed Pete & Mel's GM charts are 'House: Equal'. "
    "Universal Placidus migration is no longer justified. Awaiting gm-true-sidereal-forensic-v2 "
    "outcome before any recompute is permitted. See /app/memory/gm_forensic_audit_2026-05-31.md"
)


def _parse_user_birth(u: Dict[str, Any]):
    """Extract (utc_datetime, lat, lon) from a user document.

    Returns None for any user that does not have the minimum birth data."""
    bd = u.get("birth_date")
    bt = u.get("birth_time") or "12:00"

    # Location can live at top-level (legacy) or inside birth_location
    bl = u.get("birth_location") or {}
    lat = u.get("latitude")
    if lat is None:
        lat = bl.get("latitude")
    lon = u.get("longitude")
    if lon is None:
        lon = bl.get("longitude")

    if bd is None or lat is None or lon is None:
        return None

    # Date
    if isinstance(bd, str):
        try:
            bd_dt = datetime.fromisoformat(bd.split("T")[0])
        except Exception:
            return None
    else:
        bd_dt = bd

    # Time
    try:
        hh, mm = map(int, str(bt).split(":")[:2])
    except Exception:
        hh, mm = 12, 0

    # Timezone — prefer numeric minutes, then "+HH:MM" string
    tz_minutes = u.get("timezone_minutes")
    if tz_minutes is None:
        tz_str = u.get("timezone")
        if isinstance(tz_str, str) and len(tz_str) >= 3 and tz_str[0] in "+-":
            sign = 1 if tz_str[0] == "+" else -1
            try:
                if ":" in tz_str:
                    h, m = map(int, tz_str[1:].split(":"))
                else:
                    h, m = int(tz_str[1:3]), 0
                tz_minutes = sign * (h * 60 + m)
            except Exception:
                tz_minutes = 0
        elif isinstance(tz_str, (int, float)):
            tz_minutes = int(tz_str * 60)
        else:
            tz_minutes = 0

    local = bd_dt.replace(
        hour=hh, minute=mm, second=0,
        tzinfo=timezone(timedelta(minutes=int(tz_minutes))),
    )
    return local.astimezone(timezone.utc), float(lat), float(lon)


@router.post("/gm-aligned-recompute")
async def gm_aligned_recompute(
    dry_run: bool = True,
    confirm: str = "",
    limit: int = 0,
):
    """One-time GM-aligned recompute of every user's chart + cache invalidation.

    SAFETY:
      - dry_run defaults to True. Pass dry_run=false AND confirm=GM_PLACIDUS_RECOMPUTE_V1
        to actually write to the database.
      - Pass `limit=N` to bound the run to the first N users (handy for testing).
    """
    from server import db
    from calculations.astrology import get_full_natal_chart
    from calculations.human_design import get_human_design_chart

    will_write = (
        (not dry_run)
        and (confirm == _RECOMPUTE_CONFIRM_TOKEN)
        and (not _MIGRATION_FROZEN)
    )

    if _MIGRATION_FROZEN and not dry_run:
        return {
            "marker":   "gm-aligned-recompute-FROZEN",
            "frozen":   True,
            "reason":   _MIGRATION_FREEZE_REASON,
            "dry_run":  dry_run,
            "will_write": False,
            "hint": "Pass dry_run=true to inspect candidate users without writing. "
                    "Live recompute is disabled until forensic V2 concludes.",
        }

    now = datetime.now(timezone.utc)
    summary: Dict[str, Any] = {
        "marker":                 "gm-aligned-recompute-v1",
        "dry_run":                dry_run,
        "will_write":             will_write,
        "confirm_token_ok":       confirm == _RECOMPUTE_CONFIRM_TOKEN,
        "limit":                  limit,
        "started_at":             now.isoformat(),
        "astro_engine_version":   ASTRO_ENGINE_VERSION,
        "hd_engine_version":      HD_ENGINE_VERSION,
        "canonical_house_system": CANONICAL_HOUSE_SYSTEM,
        "users_scanned":          0,
        "users_eligible":         0,
        "users_skipped_no_birth": 0,
        "charts_recomputed":      0,
        "errors":                 [],
    }

    cursor = db.users.find({}, {
        "_id": 1, "name": 1, "email": 1,
        "birth_date": 1, "birth_time": 1, "birth_location": 1,
        "latitude": 1, "longitude": 1,
        "timezone": 1, "timezone_minutes": 1,
    })

    processed = 0
    async for u in cursor:
        summary["users_scanned"] += 1
        if limit and processed >= limit:
            break

        uid = str(u["_id"])
        parsed = _parse_user_birth(u)
        if parsed is None:
            summary["users_skipped_no_birth"] += 1
            continue

        utc, lat, lon = parsed
        summary["users_eligible"] += 1
        processed += 1

        if not will_write:
            # Dry run: just count — do NOT call the engines (cheap & safe)
            continue

        try:
            # house-system-source-of-truth-v1: defence in depth — pass the
            # canonical constant explicitly even though the function default
            # now resolves to the same value.
            chart = get_full_natal_chart(
                birth_datetime=utc, lat=lat, lon=lon,
                house_system=CANONICAL_HOUSE_SYSTEM,
            )
            hd    = get_human_design_chart(birth_datetime=utc, lat=lat, lon=lon)
            await db.charts.update_one(
                {"user_id": uid},
                {"$set": {
                    "astrology":                chart,
                    "human_design":             hd,
                    "astrology_engine_version": ASTRO_ENGINE_VERSION,
                    "hd_engine_version":        HD_ENGINE_VERSION,
                    "house_system":             CANONICAL_HOUSE_SYSTEM,
                    "recomputed_at":            now,
                }},
                upsert=True,
            )
            summary["charts_recomputed"] += 1
        except Exception as e:  # noqa: BLE001
            summary["errors"].append({"user_id": uid, "error": str(e)[:200]})
            logger.warning(f"[GM-Align] recompute failed for {uid}: {e}")

    # Cache invalidation — collections that store derived payloads
    if will_write:
        invalidated = {}
        for coll in _DERIVED_CACHE_COLLECTIONS:
            try:
                r = await db[coll].delete_many({})
                invalidated[coll] = r.deleted_count
            except Exception:
                invalidated[coll] = "(collection missing — ok)"
        summary["caches_invalidated"] = invalidated
    else:
        summary["caches_invalidated"] = "(skipped — dry run / missing confirm token)"

    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    return summary
