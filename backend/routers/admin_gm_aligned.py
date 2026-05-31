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
CANONICAL_HOUSE_SYSTEM = "Placidus"


@router.get("/gm-forensic-ana")
async def gm_forensic_ana():
    """Forensic comparison: Mirror vs GM gold standard for Ana Gayoso."""
    from calculations.astrology import get_full_natal_chart
    from calculations.human_design import get_human_design_chart

    local = datetime(1983, 5, 3, 8, 20, 0, tzinfo=timezone(timedelta(hours=-3)))
    utc   = local.astimezone(timezone.utc)
    lat, lon = -34.5438, -58.715302

    chart = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon)
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
        "marker":                 "gm-forensic-ana-v1",
        "birth_inputs":           {"utc": utc.isoformat(), "lat": lat, "lon": lon},
        "astro_engine_version":   ASTRO_ENGINE_VERSION,
        "hd_engine_version":      HD_ENGINE_VERSION,
        "canonical_house_system": CANONICAL_HOUSE_SYSTEM,
        "gm_expected":            gm_expected,
        "mirror_actual":          mirror_actual,
        "checks":                 checks,
        "all_pass":               all(c["match"] for c in checks),
    }


@router.post("/gm-aligned-recompute")
async def gm_aligned_recompute(dry_run: bool = False):
    """One-time GM-aligned recompute of every user's chart + cache invalidation."""
    # Lazy import db (server.py owns the AsyncIOMotorClient)
    from server import db
    from calculations.astrology import get_full_natal_chart
    from calculations.human_design import get_human_design_chart

    now = datetime.now(timezone.utc)
    summary: Dict[str, Any] = {
        "marker":   "gm-aligned-recompute-v1",
        "dry_run":  dry_run,
        "started_at": now.isoformat(),
        "astro_engine_version":   ASTRO_ENGINE_VERSION,
        "hd_engine_version":      HD_ENGINE_VERSION,
        "canonical_house_system": CANONICAL_HOUSE_SYSTEM,
        "users_scanned": 0,
        "charts_recomputed": 0,
        "errors": [],
    }

    cursor = db.users.find({}, {
        "_id": 1, "birth_date": 1, "birth_time": 1,
        "latitude": 1, "longitude": 1, "timezone": 1, "name": 1,
    })
    async for u in cursor:
        summary["users_scanned"] += 1
        uid = str(u["_id"])
        try:
            bd = u.get("birth_date")
            bt = u.get("birth_time") or "12:00"
            tz_off = u.get("timezone") or 0  # hours offset
            lat = u.get("latitude")
            lon = u.get("longitude")
            if not (bd and lat is not None and lon is not None):
                continue
            if isinstance(bd, str):
                bd_dt = datetime.fromisoformat(bd.split("T")[0])
            else:
                bd_dt = bd
            hh, mm = map(int, bt.split(":")[:2])
            local = bd_dt.replace(hour=hh, minute=mm, second=0,
                                  tzinfo=timezone(timedelta(hours=float(tz_off))))
            utc = local.astimezone(timezone.utc)

            if dry_run:
                continue

            chart = get_full_natal_chart(birth_datetime=utc, lat=lat, lon=lon)
            hd    = get_human_design_chart(birth_datetime=utc, lat=lat, lon=lon)

            await db.charts.update_one(
                {"user_id": uid},
                {"$set": {
                    "astrology":              chart,
                    "human_design":           hd,
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
    if not dry_run:
        invalidated = {}
        for coll in ("daily_astrology", "today_cache", "deep_dive_cache",
                     "life_lens_cache", "relationship_mappings_cache",
                     "forum_hd_mappings_cache", "home_insight_cache",
                     "timeline_cache"):
            try:
                r = await db[coll].delete_many({})
                invalidated[coll] = r.deleted_count
            except Exception:
                invalidated[coll] = "(collection missing — ok)"
        summary["caches_invalidated"] = invalidated

    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    return summary
