"""PFS chart-integrity forensic audit — read-only.

For each of (Pete, Mel, Isaac, Jaan) dump:
  CALCULATION LAYER — recompute the chart from birth data and dump the
                      angle/house/sign breakdown PLUS the engine config.
  STORAGE LAYER     — read the `charts` collection's stored payload.
  PROMPT LAYER      — fetch the astrology context blob the prompt
                      builder would inject (without actually invoking
                      the LLM).
  NARRATIVE LAYER   — text-grep the codebase for MC references
                      (separate process, results live in the report).

No data is modified. No prompt is sent to an LLM.
"""
import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient   # noqa: E402
from bson import ObjectId                            # noqa: E402


USERS = [
    ("Pete",  "697f0c6abf35c0528ff06954"),
    ("Mel",   "697ec826ad4b18f75bf42616"),
    ("Isaac", "69dda348de9cb1c83c0780f8"),
    ("Jaan",  "69894cc932380843ba87d121"),
]


def _je(o):
    if isinstance(o, dict):  return {k: _je(v) for k, v in o.items()}
    if isinstance(o, list):  return [_je(v) for v in o]
    from datetime import datetime as _dt
    if isinstance(o, _dt):   return o.isoformat()
    if isinstance(o, ObjectId): return str(o)
    return o


def _pick_angle_sign(angles_dict: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    if not angles_dict: return None
    a = angles_dict.get(key) or {}
    if isinstance(a, dict):
        return a.get("sign") or a.get("zodiac_sign")
    return None


def _pick_angle_degree(angles_dict: Optional[Dict[str, Any]], key: str) -> Optional[float]:
    if not angles_dict: return None
    a = angles_dict.get(key) or {}
    if isinstance(a, dict):
        return a.get("degree") if isinstance(a.get("degree"), (int, float)) else None
    return None


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]

    # Import calculator engine lazily so we capture engine version too.
    from calculations.astrology import (
        get_full_natal_chart,
        CANONICAL_HOUSE_SYSTEM,
        SVP_DEGREES,
        ZODIAC_SIGNS,
    )
    DEFAULT_AYANAMSA = SVP_DEGREES
    engine_version = None
    try:
        from calculations import astrology as _astro_mod
        engine_version = getattr(_astro_mod, "VERSION", None) \
            or getattr(_astro_mod, "ENGINE_VERSION", None) \
            or "unversioned"
    except Exception as e:
        engine_version = f"engine_introspect_error: {e}"

    report: Dict[str, Any] = {
        "engine_global": {
            "house_system":   CANONICAL_HOUSE_SYSTEM,
            "default_ayanamsa": DEFAULT_AYANAMSA,
            "zodiac_signs_n": len(ZODIAC_SIGNS),
            "engine_version": engine_version,
        },
        "users": [],
    }

    for name, uid in USERS:
        per_user: Dict[str, Any] = {"label": name, "user_id": uid}

        # ── USER DOC (birth data) ──────────────────────────────────────
        u = await db.users.find_one({"_id": ObjectId(uid)})
        if not u:
            per_user["error"] = "user_not_found"
            report["users"].append(per_user)
            continue
        bd = {
            "name":         u.get("name"),
            "birth_date":   u.get("birth_date") or u.get("date_of_birth"),
            "birth_time":   u.get("birth_time"),
            "birth_place":  u.get("birth_place") or u.get("birth_location"),
            "birth_lat":    u.get("birth_lat") or (u.get("birth_coordinates") or {}).get("lat"),
            "birth_lon":    u.get("birth_lon") or (u.get("birth_coordinates") or {}).get("lng") \
                                                or (u.get("birth_coordinates") or {}).get("lon"),
            "birth_tz":     u.get("birth_tz") or u.get("timezone"),
        }
        per_user["birth_data"] = bd

        # ── CALCULATION LAYER ──────────────────────────────────────────
        calc_out: Dict[str, Any] = {}
        try:
            chart = get_full_natal_chart(
                birth_date  = bd["birth_date"],
                birth_time  = bd["birth_time"],
                lat         = bd["birth_lat"],
                lon         = bd["birth_lon"],
                tz_str      = bd["birth_tz"],
                house_system = CANONICAL_HOUSE_SYSTEM,
            ) if all(bd.get(k) is not None for k in
                     ("birth_date","birth_time","birth_lat","birth_lon","birth_tz")) else None
            if chart:
                ang = chart.get("angles") or {}
                calc_out = {
                    "ascendant_sign":   _pick_angle_sign(ang,   "asc"),
                    "ascendant_degree": _pick_angle_degree(ang, "asc"),
                    "mc_sign":          _pick_angle_sign(ang,   "mc"),
                    "mc_degree":        _pick_angle_degree(ang, "mc"),
                    "ic_sign":          _pick_angle_sign(ang,   "ic"),
                    "ic_degree":        _pick_angle_degree(ang, "ic"),
                    "house_system":     chart.get("house_system") or CANONICAL_HOUSE_SYSTEM,
                    "zodiac_mode":      chart.get("zodiac_mode")  or "sidereal",
                    "ayanamsa":         chart.get("ayanamsa")     or DEFAULT_AYANAMSA,
                    "engine_version":   engine_version,
                }
            else:
                calc_out = {"error": "insufficient_birth_data_for_recalc",
                            "birth_data_seen": bd}
        except Exception as e:
            calc_out = {"error": f"{type(e).__name__}: {e!s}"}
        per_user["calculation_layer"] = calc_out

        # ── STORAGE LAYER ──────────────────────────────────────────────
        chart_doc = await db.charts.find_one({"user_id": uid})
        if not chart_doc:
            chart_doc = await db.charts.find_one({"user_id": ObjectId(uid)})
        if chart_doc:
            astro = chart_doc.get("astrology") or {}
            angles = astro.get("angles") or {}
            planets = astro.get("planets") or {}
            houses  = astro.get("houses") or []
            def _planet_sign(pl):
                if isinstance(planets, dict):
                    p = planets.get(pl) or planets.get(pl.capitalize()) or {}
                    if isinstance(p, dict):
                        return p.get("sign") or p.get("zodiac_sign")
                return None
            per_user["storage_layer"] = {
                "asc_sign":     _pick_angle_sign(angles, "asc"),
                "asc_degree":   _pick_angle_degree(angles, "asc"),
                "mc_sign":      _pick_angle_sign(angles, "mc"),
                "mc_degree":    _pick_angle_degree(angles, "mc"),
                "ic_sign":      _pick_angle_sign(angles, "ic"),
                "ic_degree":    _pick_angle_degree(angles, "ic"),
                "sun_sign":     _planet_sign("Sun"),
                "moon_sign":    _planet_sign("Moon"),
                "engine_version": astro.get("astrology_engine_version")
                                 or chart_doc.get("astrology_engine_version"),
                "house_system": astro.get("house_system")
                              or chart_doc.get("house_system"),
                "zodiac_mode":  (astro.get("sidereal_settings") or {}).get("mode")
                              or (astro.get("metadata") or {}).get("zodiac_mode"),
                "sidereal_settings": astro.get("sidereal_settings"),
                "tenth_house_cusp_sign": next(
                    (h.get("sign") for h in houses
                     if isinstance(h, dict) and h.get("house") == 10),
                    None),
                "_astro_top_keys": sorted(list(astro.keys())),
            }
        else:
            per_user["storage_layer"] = {"error": "no_chart_doc_for_user"}

        # ── PROMPT LAYER ──────────────────────────────────────────────
        # Reproduce what the prompt builder reads. The canonical surface
        # is `lensful_chart_summary` or `chart_summary` derived from the
        # stored chart. We inspect three plausible sources:
        prompt_layer: Dict[str, Any] = {}
        # (a) user_chart_summaries collection (if present)
        if "user_chart_summaries" in await db.list_collection_names():
            ucs = await db.user_chart_summaries.find_one({"user_id": uid})
            if ucs:
                prompt_layer["user_chart_summaries"] = {
                    k: ucs.get(k) for k in
                    ("sun_sign","moon_sign","asc_sign","mc_sign",
                     "career_sign","public_life_sign","tenth_house_sign")
                    if k in ucs
                }
        # (b) the stored chart's surface fields (what the prompt actually consults)
        if chart_doc:
            surface = (chart_doc.get("summary") or chart_doc.get("chart_summary") or {})
            prompt_layer["chart_doc_surface"] = {
                k: surface.get(k) for k in
                ("sun_sign","moon_sign","asc_sign","mc_sign",
                 "career_sign","public_life_sign","tenth_house_sign")
                if k in surface
            }
        # (c) astrology context block (the canonical USER CONTEXT
        #     section uses these top-level fields if present)
        if chart_doc:
            prompt_layer["chart_doc_top_level"] = {
                k: chart_doc.get(k) for k in
                ("sun_sign","moon_sign","asc_sign","mc_sign",
                 "career_sign","public_life_sign","tenth_house_sign")
                if k in chart_doc
            }
        per_user["prompt_layer"] = prompt_layer

        # ── MISMATCH ANALYSIS ──────────────────────────────────────────
        calc_mc    = calc_out.get("mc_sign")
        store_mc   = per_user["storage_layer"].get("mc_sign")
        # Identify a "prompt_mc" surface — pull whichever source exists.
        prompt_mc  = None
        for src in ("user_chart_summaries", "chart_doc_surface",
                    "chart_doc_top_level"):
            cand = prompt_layer.get(src) or {}
            if cand.get("mc_sign"):
                prompt_mc = cand.get("mc_sign"); break
        # Special: is mc accidentally aliased to sun_sign or 10th-cusp?
        sun_sign       = per_user["storage_layer"].get("sun_sign")
        tenth_cusp_sign = None
        if chart_doc:
            houses = (chart_doc.get("chart") or {}).get("houses") \
                  or chart_doc.get("houses") or []
            for h in houses:
                if isinstance(h, dict) and h.get("house") == 10:
                    tenth_cusp_sign = h.get("sign"); break
        per_user["mismatch_check"] = {
            "calc_mc":         calc_mc,
            "store_mc":        store_mc,
            "prompt_mc":       prompt_mc,
            "sun_sign":        sun_sign,
            "tenth_cusp_sign": tenth_cusp_sign,
            "match_calc_store": (calc_mc == store_mc) if (calc_mc and store_mc) else None,
            "match_store_prompt": (store_mc == prompt_mc) if (store_mc and prompt_mc) else None,
            "alias_to_sun":    (prompt_mc == sun_sign) if (prompt_mc and sun_sign) else None,
            "alias_to_tenth_cusp": (prompt_mc == tenth_cusp_sign) if (prompt_mc and tenth_cusp_sign) else None,
        }

        report["users"].append(per_user)

    print(json.dumps(_je(report), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
