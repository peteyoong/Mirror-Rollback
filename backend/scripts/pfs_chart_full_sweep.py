"""Read-only comprehensive chart-points sweep across 3 layers.

For each of (Pete, Mel, Isaac, Jaan) dumps every requested chart point
across calculator output / stored payload / prompt payload, and flags
mismatches.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from bson import ObjectId                            # noqa: E402

USERS = [
    ("Pete",  "697f0c6abf35c0528ff06954"),
    ("Mel",   "697ec826ad4b18f75bf42616"),
    ("Isaac", "69dda348de9cb1c83c0780f8"),
    ("Jaan",  "69894cc932380843ba87d121"),
]

CHART_POINTS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
    "Saturn", "Uranus", "Neptune", "Pluto",
    "North Node", "South Node", "Chiron",
    "ASC", "MC", "IC", "Descendant",
]


def _je(o):
    if isinstance(o, dict): return {k: _je(v) for k, v in o.items()}
    if isinstance(o, list): return [_je(v) for v in o]
    if isinstance(o, datetime): return o.isoformat()
    if isinstance(o, ObjectId): return str(o)
    return o


def _norm_sign(s):  return (s or "").strip() or None
def _norm_deg(d):
    try: return round(float(d), 2) if d is not None else None
    except Exception: return None
def _norm_house(h):
    if h in (None, ""): return None
    try: return int(h)
    except Exception:
        try: return int(float(h))
        except Exception: return str(h)


def _extract_from_stored(astro: Dict[str, Any], point: str) -> Dict[str, Any]:
    """Pull (sign, degree, house) from the stored chart for one point."""
    planets = astro.get("planets") or {}
    nodes   = astro.get("nodes") or {}
    angles  = astro.get("angles") or {}
    p = None
    if point in planets:
        p = planets[point]
    elif point == "North Node":
        p = (nodes.get("north") or {}) or planets.get("North Node")
    elif point == "South Node":
        p = (nodes.get("south") or {}) or planets.get("South Node")
    elif point == "ASC":
        p = angles.get("asc") or {}
    elif point == "MC":
        p = angles.get("mc") or {}
    elif point == "IC":
        p = angles.get("ic") or {}
    elif point == "Descendant":
        p = angles.get("dc") or angles.get("descendant") or {}
    elif point == "Chiron":
        p = planets.get("Chiron") or {}
    if not p:
        return {"sign": None, "degree": None, "house": None}
    return {
        "sign":   _norm_sign(p.get("sign") or p.get("zodiac_sign")),
        "degree": _norm_deg(p.get("degree")),
        "house":  _norm_house(p.get("house")),
    }


async def _extract_from_calculator(astro_meta: Dict[str, Any],
                                   birth_date,
                                   birth_time) -> Optional[Dict[str, Dict]]:
    """Re-run the calculator using stored metadata + birth fields and
    return a dict { point_name → {sign,degree,house} }."""
    if not astro_meta:
        return None
    coords = (astro_meta.get("coordinates") or {})
    lat = coords.get("lat")
    lon = coords.get("lon") or coords.get("lng")
    if lat is None or lon is None or not birth_date or not birth_time:
        return None
    try:
        from calculations.astrology import get_full_natal_chart
        # birth_date is stored as datetime in the DB; convert to date-string.
        bd = (birth_date.date().isoformat()
              if isinstance(birth_date, datetime) else str(birth_date)[:10])
        bt = str(birth_time)[:5]
        chart = get_full_natal_chart(
            birth_date  = bd,
            birth_time  = bt,
            lat         = float(lat),
            lon         = float(lon),
            tz_str      = astro_meta.get("timezone") or astro_meta.get("tz") or "UTC",
            house_system = astro_meta.get("house_system") or "Equal",
        )
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}
    if not chart:
        return {"_error": "calculator_returned_empty"}
    return _extract_from_stored(chart.get("astrology") or chart, "Sun") and \
           {p: _extract_from_stored(chart.get("astrology") or chart, p)
            for p in CHART_POINTS}


def _extract_from_prompt(astro: Dict[str, Any],
                         lens: str = "astrology") -> Dict[str, Dict]:
    """Emulate the prompt-layer USER CONTEXT builder
    (`routers/mirror_chat.py:264-310` + the P0-MC-FIX patch lines 277-339).

    Returns a dict { point_name -> {sign,degree,house}|None } reflecting
    exactly which points are written into the prompt. None means "not
    injected".
    """
    out: Dict[str, Optional[Dict]] = {p: None for p in CHART_POINTS}
    planets = astro.get("planets") or {}
    houses  = astro.get("houses") or {}
    angles  = astro.get("angles") or {}
    nodes   = astro.get("nodes") or {}

    # Always injected (lines 275-277, plus P0-MC-FIX line at 277+):
    sun  = planets.get("Sun") or {}
    moon = planets.get("Moon") or {}
    # Rising sourced from houses.formatted_cusps[0] in the live builder;
    # signs typically coincide with angles.asc when house system is Equal.
    rising_src = ((houses.get("formatted_cusps") or [{}])[0]
                  if (houses.get("formatted_cusps") or []) else (angles.get("asc") or {}))
    mc_doc = angles.get("mc") or angles.get("midheaven") or {}

    out["Sun"]  = {"sign": _norm_sign(sun.get("sign")),
                   "degree": _norm_deg(sun.get("degree")),
                   "house":  _norm_house(sun.get("house"))}
    out["Moon"] = {"sign": _norm_sign(moon.get("sign")),
                   "degree": _norm_deg(moon.get("degree")),
                   "house":  _norm_house(moon.get("house"))}
    out["ASC"]  = {"sign": _norm_sign(rising_src.get("sign")),
                   "degree": _norm_deg(rising_src.get("degree")),
                   "house":  None}
    if mc_doc.get("sign"):
        out["MC"] = {"sign": _norm_sign(mc_doc.get("sign")),
                     "degree": _norm_deg(mc_doc.get("degree")),
                     "house":  None}

    # Astrology-lens-only block (lines 280-299) — only present when
    # lens="astrology".
    if lens == "astrology":
        for p in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                  "Uranus", "Neptune", "Pluto"]:
            pd = planets.get(p) or {}
            if pd:
                out[p] = {"sign": _norm_sign(pd.get("sign")),
                          "degree": _norm_deg(pd.get("degree")),
                          "house":  _norm_house(pd.get("house"))}
        nn = nodes.get("north") or planets.get("North Node") or {}
        sn = nodes.get("south") or planets.get("South Node") or {}
        if nn.get("sign"):
            out["North Node"] = {"sign": _norm_sign(nn.get("sign")),
                                 "degree": _norm_deg(nn.get("degree")),
                                 "house":  _norm_house(nn.get("house"))}
        if sn.get("sign"):
            out["South Node"] = {"sign": _norm_sign(sn.get("sign")),
                                 "degree": _norm_deg(sn.get("degree")),
                                 "house":  _norm_house(sn.get("house"))}
    # Chiron, IC, Descendant are NOT in the USER CONTEXT block — but
    # MAY appear via downstream proof-block builders (build_home_context
    # for IC, build_relationship_context for Descendant, transit / natal
    # object engines for Chiron) IF the intent classifier routes to those
    # domains. The base USER CONTEXT block does not inject them.
    return out


def _compare(a: Optional[Dict], b: Optional[Dict]) -> str:
    """Return 'OK', 'MISSING_LEFT', 'MISSING_RIGHT', or a diff string."""
    if a is None and b is None: return "MISSING_BOTH"
    if a is None:               return "MISSING_LEFT"
    if b is None:               return "MISSING_RIGHT"
    diffs = []
    if a.get("sign") != b.get("sign"):
        diffs.append(f"sign:{a.get('sign')!r}≠{b.get('sign')!r}")
    # Degrees compared at 0.1° tolerance (rounding).
    da, db = a.get("degree"), b.get("degree")
    if da is not None and db is not None and abs(da - db) > 0.1:
        diffs.append(f"deg:{da}≠{db}")
    if a.get("house") != b.get("house"):
        diffs.append(f"house:{a.get('house')}≠{b.get('house')}")
    return "OK" if not diffs else " | ".join(diffs)


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    report: List[Dict[str, Any]] = []

    for name, uid in USERS:
        u = await db.users.find_one({"_id": ObjectId(uid)})
        cd = await db.charts.find_one({"user_id": uid})
        if not cd:
            report.append({"label": name, "error": "no_chart_doc"})
            continue
        astro = cd.get("astrology") or {}
        meta  = astro.get("metadata") or {}
        birth_date = u.get("birth_date") if u else None
        birth_time = u.get("birth_time") if u else None

        # Layer extracts
        stored_layer = {p: _extract_from_stored(astro, p) for p in CHART_POINTS}
        calc_layer   = await _extract_from_calculator(meta, birth_date, birth_time)
        prompt_layer = _extract_from_prompt(astro, lens="astrology")

        # Cross-layer comparison
        rows = []
        for p in CHART_POINTS:
            s_row = stored_layer.get(p) or {}
            c_row = (calc_layer or {}).get(p) if (calc_layer and "_error" not in calc_layer) else None
            pr_row = prompt_layer.get(p)
            rows.append({
                "point":     p,
                "stored":    s_row,
                "calculator": c_row if c_row else "(unable_to_recompute)",
                "prompt":    pr_row if pr_row else "(absent_from_prompt)",
                "calc_vs_stored":  _compare(c_row, s_row) if c_row else "n/a",
                "stored_vs_prompt": _compare(s_row, pr_row),
            })
        report.append({
            "label":   name,
            "user_id": uid,
            "birth":   {"date": birth_date, "time": birth_time,
                        "coords": (meta.get("coordinates") or {}),
                        "tz_in_meta": meta.get("timezone")},
            "engine":  {"engine_version": meta.get("astrology_engine_version"),
                        "house_system":   meta.get("house_system"),
                        "sidereal_mode":  meta.get("sidereal_mode"),
                        "svp_degrees":    meta.get("svp_degrees"),
                        "node_mode":      meta.get("node_mode"),
                        "computation_version": meta.get("computation_version")},
            "calc_layer_error": (calc_layer or {}).get("_error")
                                if isinstance(calc_layer, dict) else None,
            "rows": rows,
        })

    print(json.dumps(_je(report), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
