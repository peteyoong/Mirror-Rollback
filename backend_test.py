"""
Backend test harness — Achievement-as-Stabilization atom
(third detector in /app/backend/services/cross_lens_atoms.py)
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(HERE, "backend")
load_dotenv(os.path.join(BACKEND, ".env"))

BASE = "http://localhost:8001/api"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "test_database")

SEED_PREFIX = "cross_lens_atoms_test_"

PASS: List[str] = []
FAIL: List[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASS.append(label)
        print(f"  PASS  {label}")
    else:
        FAIL.append(f"{label} :: {detail}")
        print(f"  FAIL  {label} :: {detail}")


def get_atoms(user_id: str) -> Dict[str, Any]:
    r = requests.get(f"{BASE}/synthesis/atoms/{user_id}", timeout=15)
    if r.status_code != 200:
        return {"_status": r.status_code, "_body": r.text, "atom_count": -1, "atoms": []}
    return r.json()


_db = None


async def get_db():
    global _db
    if _db is None:
        client = AsyncIOMotorClient(MONGO_URL)
        _db = client[DB_NAME]
    return _db


async def seed_chart(suffix: str, chart_overrides: Dict[str, Any]) -> str:
    db = await get_db()
    uid = f"{SEED_PREFIX}{suffix}"
    await db.charts.delete_many({"user_id": uid})
    doc = {
        "user_id":       uid,
        "calculated_at": datetime.now(timezone.utc),
        "debug_stamp":   {"migration": "synthetic_achievement_test"},
        "human_design":  chart_overrides.get("human_design", {}),
        "astrology":     chart_overrides.get("astrology", {}),
        "numerology":    chart_overrides.get("numerology", {}),
    }
    await db.charts.insert_one(doc)
    return uid


async def cleanup_synthetic() -> None:
    db = await get_db()
    res = await db.charts.delete_many({"user_id": {"$regex": f"^{SEED_PREFIX}"}})
    print(f"[cleanup] deleted {res.deleted_count} synthetic chart docs")


DEFAULT_PLANETS = {
    "Sun":     {"sign": "Sagittarius", "degree":  3.0, "longitude": 243.0, "house":  9, "retrograde": False},
    "Moon":    {"sign": "Aries",       "degree": 24.0, "longitude":  24.0, "house":  1, "retrograde": False},
    "Mercury": {"sign": "Scorpio",     "degree": 12.0, "longitude": 222.0, "house":  8, "retrograde": False},
    "Venus":   {"sign": "Capricorn",   "degree":  2.0, "longitude": 272.0, "house": 11, "retrograde": False},
    "Mars":    {"sign": "Leo",         "degree": 18.0, "longitude": 138.0, "house":  5, "retrograde": False},
    "Jupiter": {"sign": "Virgo",       "degree":  6.0, "longitude": 156.0, "house":  6, "retrograde": False},
    "Saturn":  {"sign": "Libra",       "degree": 16.0, "longitude": 196.0, "house":  6, "retrograde": False},
    "Uranus":  {"sign": "Scorpio",     "degree": 26.0, "longitude": 236.0, "house":  8, "retrograde": True},
    "Neptune": {"sign": "Sagittarius", "degree": 22.0, "longitude": 262.0, "house":  9, "retrograde": True},
    "Pluto":   {"sign": "Libra",       "degree": 22.0, "longitude": 202.0, "house":  9, "retrograde": True},
}


def mk_chart(
    *,
    hd: Optional[Dict[str, Any]] = None,
    aspects: Optional[List[Dict[str, Any]]] = None,
    planets_override: Optional[Dict[str, Dict[str, Any]]] = None,
    numerology: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hd_default = {
        "defined_centers":   ["Throat", "G Center", "Sacral", "Spleen"],
        "undefined_centers": ["Head", "Ajna", "Solar Plexus", "Root", "Ego"],
        "defined_channels":  [],
        "active_gates":      [],
        "all_gates":         [],
    }
    if hd:
        hd_default.update(hd)
    planets = dict(DEFAULT_PLANETS)
    if planets_override:
        for k, v in planets_override.items():
            planets[k] = v
    astro = {
        "planets": planets,
        "aspects": aspects or [],
        "houses":  {"system": "Equal", "ascendant": 20.0, "mc": 290.0},
    }
    return {"human_design": hd_default, "astrology": astro, "numerology": numerology or {}}


def signals_labels(atom: Dict[str, Any]) -> List[str]:
    return [s["label"] for s in atom.get("signals", [])]


# S1
def test_s1_real_users() -> None:
    print("\n========== S1: Selectivity on real users ==========")
    d = get_atoms("697f0c6abf35c0528ff06954")
    check("S1.Pete returns 1 atom", d.get("atom_count") == 1, f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S1.Pete atom_id == achievement_as_stabilization",
              a.get("atom_id") == "achievement_as_stabilization", f"got {a.get('atom_id')}")
        check("S1.Pete astro_kind == saturn_personal",
              a.get("astro_kind") == "saturn_personal", f"got {a.get('astro_kind')}")

    d = get_atoms("697ec826ad4b18f75bf42616")
    check("S1.Mel atom_count == 0", d.get("atom_count") == 0,
          f"atom_count={d.get('atom_count')} ids={[a.get('atom_id') for a in d.get('atoms',[])]}")

    d = get_atoms("69dda348de9cb1c83c0780f8")
    check("S1.Isaac atom_count == 0", d.get("atom_count") == 0,
          f"atom_count={d.get('atom_count')}")

    d = get_atoms("69dd0b2cc92ba973f8838c11")
    check("S1.Thaddeus returns 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S1.Thaddeus atom_id == achievement_as_stabilization",
              a.get("atom_id") == "achievement_as_stabilization", f"got {a.get('atom_id')}")
        check("S1.Thaddeus astro_kind == saturn_personal",
              a.get("astro_kind") == "saturn_personal", f"got {a.get('astro_kind')}")


# S2
def test_s2_demo() -> None:
    print("\n========== S2: Seeded achievement demo ==========")
    d = get_atoms("6a111d24328ffbb9b24c74cd")
    check("S2.demo atom_count == 1", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if not d.get("atoms"):
        return
    a = d["atoms"][0]
    check("S2.demo atom_id", a.get("atom_id") == "achievement_as_stabilization",
          f"got {a.get('atom_id')}")
    labels = signals_labels(a)
    expected = [
        "Channel 21-45 — Authority",
        "Defined Heart (Ego)",
        "Mars Square Saturn (2.0°)",
        "Life Path 8 (supporting)",
    ]
    check("S2.demo signal order matches exactly", labels == expected, f"got {labels}")
    check("S2.demo astro_kind == mars_saturn",
          a.get("astro_kind") == "mars_saturn", f"got {a.get('astro_kind')}")
    check("S2.demo has_supporting True",
          a.get("has_supporting") is True, f"got {a.get('has_supporting')}")
    check("S2.demo matched == required == 4",
          a.get("matched") == 4 and a.get("required") == 4,
          f"matched={a.get('matched')} required={a.get('required')}")
    check("S2.demo core_signals_required == 2",
          a.get("core_signals_required") == 2, f"got {a.get('core_signals_required')}")
    conf = a.get("confidence")
    check("S2.demo confidence is float > 2.0",
          isinstance(conf, (int, float)) and conf > 2.0, f"got {conf}")


# S3
async def test_s3_boundaries() -> None:
    print("\n========== S3: Boundary variants ==========")

    # (a)
    uid = await seed_chart("s3a_hd_only", mk_chart(
        hd={"defined_centers": ["Ego", "Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[],
    ))
    d = get_atoms(uid)
    check("S3.a HD-only blocks (no astro) -> 0", d.get("atom_count") == 0,
          f"atom_count={d.get('atom_count')}")

    # (b)
    uid = await seed_chart("s3b_astro_only", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [], "all_gates": []},
        aspects=[{"body1": "Mars", "body2": "Saturn", "type": "square", "orb": 2.0}],
    ))
    d = get_atoms(uid)
    check("S3.b Astro-only blocks -> 0", d.get("atom_count") == 0,
          f"atom_count={d.get('atom_count')}")

    # (c)
    uid = await seed_chart("s3c_satmerc_3_5", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[{"body1": "Saturn", "body2": "Mercury", "type": "square", "orb": 3.5}],
    ))
    d = get_atoms(uid)
    check("S3.c Saturn-Mercury 3.5deg -> 0", d.get("atom_count") == 0,
          f"atom_count={d.get('atom_count')}")

    # (d)
    uid = await seed_chart("s3d_satmerc_2", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[{"body1": "Saturn", "body2": "Mercury", "type": "square", "orb": 2.0}],
    ))
    d = get_atoms(uid)
    check("S3.d Saturn-Mercury 2deg -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.d astro_kind == saturn_mercury",
              a.get("astro_kind") == "saturn_mercury", f"got {a.get('astro_kind')}")
        check("S3.d signals length == 2", len(a.get("signals", [])) == 2,
              f"len={len(a.get('signals', []))}")
        labels = signals_labels(a)
        check("S3.d signal[0] starts 'Gate 21'",
              len(labels) >= 1 and labels[0].startswith("Gate 21"),
              f"got {labels}")
        check("S3.d signal[1] is Saturn-Mercury",
              len(labels) >= 2 and "Saturn" in labels[1] and "Mercury" in labels[1],
              f"got {labels}")
        check("S3.d has_supporting False",
              a.get("has_supporting") is False, f"got {a.get('has_supporting')}")
        check("S3.d confidence <= 1.2",
              a.get("confidence", 99) <= 1.2, f"got {a.get('confidence')}")

    # (e)
    uid = await seed_chart("s3e_satsun_4_5", mk_chart(
        hd={
            "defined_centers": ["Throat", "Sacral"],
            "defined_channels": [{"gate1": 32, "gate2": 54}],
            "active_gates": [32, 54], "all_gates": [32, 54],
        },
        aspects=[{"body1": "Saturn", "body2": "Sun", "type": "square", "orb": 4.5}],
        numerology={"core": {"life_path": {"number": 4}}},
    ))
    d = get_atoms(uid)
    check("S3.e Saturn-Sun 4.5 + ch32-54 + LP4 -> 1 atom",
          d.get("atom_count") == 1, f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        labels = signals_labels(a)
        expected = ["Channel 32-54 — Drive", "Saturn Square Sun (4.5°)", "Life Path 4 (supporting)"]
        check("S3.e signal labels match (no Heart)", labels == expected, f"got {labels}")
        check("S3.e astro_kind == saturn_personal",
              a.get("astro_kind") == "saturn_personal", f"got {a.get('astro_kind')}")

    # (f)
    uid = await seed_chart("s3f_satsun_5_5", mk_chart(
        hd={
            "defined_centers": ["Throat", "Sacral"],
            "defined_channels": [{"gate1": 32, "gate2": 54}],
            "active_gates": [32, 54], "all_gates": [32, 54],
        },
        aspects=[{"body1": "Saturn", "body2": "Sun", "type": "square", "orb": 5.5}],
    ))
    d = get_atoms(uid)
    check("S3.f Saturn-Sun 5.5deg (over tight cap) -> 0",
          d.get("atom_count") == 0, f"atom_count={d.get('atom_count')}")

    # (g) priority cascade
    cap_planets = {
        "Sun":     {"sign": "Capricorn", "house": 10, "degree": 5, "longitude": 275},
        "Moon":    {"sign": "Capricorn", "house": 10, "degree": 6, "longitude": 276},
        "Mercury": {"sign": "Capricorn", "house": 10, "degree": 7, "longitude": 277},
        "Venus":   {"sign": "Capricorn", "house": 10, "degree": 8, "longitude": 278},
        "Saturn":  {"sign": "Aries",     "house": 1,  "degree": 1, "longitude": 1},
        "Mars":    {"sign": "Leo",       "house": 5,  "degree": 10, "longitude": 130},
    }
    uid = await seed_chart("s3g_priority", mk_chart(
        hd={"defined_centers": ["Ego"], "active_gates": [21], "all_gates": [21]},
        aspects=[
            {"body1": "Mars",   "body2": "Saturn", "type": "opposition",  "orb": 5.0},
            {"body1": "Saturn", "body2": "MC",     "type": "conjunction", "orb": 1.0},
        ],
        planets_override=cap_planets,
    ))
    d = get_atoms(uid)
    check("S3.g priority cascade -> 1 atom",
          d.get("atom_count") == 1, f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.g astro_kind == mars_saturn",
              a.get("astro_kind") == "mars_saturn", f"got {a.get('astro_kind')}")
        astro_sig = next((s for s in a["signals"] if s["lens"] == "Astrology"), None)
        check("S3.g astro label starts 'Mars Opposition Saturn'",
              astro_sig is not None and astro_sig["label"].startswith("Mars Opposition Saturn"),
              f"got {astro_sig and astro_sig.get('label')}")

    # (h)
    uid = await seed_chart("s3h_satmc", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [45], "all_gates": [45]},
        aspects=[{"body1": "Saturn", "body2": "MC", "type": "square", "orb": 3.0}],
        numerology={"core": {"life_path": {"number": 8}}},
    ))
    d = get_atoms(uid)
    check("S3.h Saturn-MC -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.h astro_kind == saturn_mc",
              a.get("astro_kind") == "saturn_mc", f"got {a.get('astro_kind')}")
        labels = signals_labels(a)
        expected = ["Gate 45 — Gatherer", "Saturn Square MC (3.0°)", "Life Path 8 (supporting)"]
        check("S3.h signal order/labels", labels == expected, f"got {labels}")

    # (i)
    uid = await seed_chart("s3i_marsmc", mk_chart(
        hd={
            "defined_centers": ["Throat", "Sacral"],
            "defined_channels": [{"gate1": 21, "gate2": 45}],
            "active_gates": [21, 45], "all_gates": [21, 45],
        },
        aspects=[{"body1": "Mars", "body2": "MC", "type": "conjunction", "orb": 4.0}],
    ))
    d = get_atoms(uid)
    check("S3.i Mars-MC -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.i astro_kind == mars_mc",
              a.get("astro_kind") == "mars_mc", f"got {a.get('astro_kind')}")

    # (j)
    uid = await seed_chart("s3j_satangular", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [32], "all_gates": [32]},
        aspects=[],
        planets_override={"Saturn": {"sign": "Libra", "house": 4, "degree": 16, "longitude": 196}},
    ))
    d = get_atoms(uid)
    check("S3.j Saturn angular -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.j astro_kind == saturn_angular",
              a.get("astro_kind") == "saturn_angular", f"got {a.get('astro_kind')}")
        astro_sig = next((s for s in a["signals"] if s["lens"] == "Astrology"), None)
        check("S3.j astro label == 'Saturn angular (house 4)'",
              astro_sig is not None and astro_sig["label"] == "Saturn angular (house 4)",
              f"got {astro_sig and astro_sig.get('label')}")

    # (k)
    cap_planets = {
        "Sun":     {"sign": "Capricorn", "house": 6, "degree": 5},
        "Moon":    {"sign": "Capricorn", "house": 6, "degree": 6},
        "Mercury": {"sign": "Capricorn", "house": 6, "degree": 7},
        "Venus":   {"sign": "Aquarius",  "house": 7, "degree": 8},
        "Mars":    {"sign": "Leo",       "house": 11, "degree": 10},
        "Saturn":  {"sign": "Libra",     "house": 6, "degree": 16},
    }
    uid = await seed_chart("s3k_capstellium", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [54], "all_gates": [54]},
        aspects=[],
        planets_override=cap_planets,
    ))
    d = get_atoms(uid)
    check("S3.k Capricorn stellium -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.k astro_kind == capricorn_stellium",
              a.get("astro_kind") == "capricorn_stellium", f"got {a.get('astro_kind')}")
        astro_sig = next((s for s in a["signals"] if s["lens"] == "Astrology"), None)
        check("S3.k label == '3 personal planets in Capricorn'",
              astro_sig is not None and astro_sig["label"] == "3 personal planets in Capricorn",
              f"got {astro_sig and astro_sig.get('label')}")

    # (l)
    h10_planets = {
        "Sun":     {"sign": "Aries",  "house": 10, "degree": 5},
        "Moon":    {"sign": "Taurus", "house": 10, "degree": 6},
        "Mercury": {"sign": "Aries",  "house": 10, "degree": 7},
        "Venus":   {"sign": "Gemini", "house": 11, "degree": 8},
        "Mars":    {"sign": "Leo",    "house": 5,  "degree": 10},
        "Saturn":  {"sign": "Libra",  "house": 6,  "degree": 16},
    }
    uid = await seed_chart("s3l_h10stellium", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[],
        planets_override=h10_planets,
    ))
    d = get_atoms(uid)
    check("S3.l 10th-house stellium -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        check("S3.l astro_kind == tenth_house_stellium",
              a.get("astro_kind") == "tenth_house_stellium", f"got {a.get('astro_kind')}")

    # (m)
    for variant_name, center in [("heart", "Heart"), ("will", "Will")]:
        uid = await seed_chart(f"s3m_{variant_name}", mk_chart(
            hd={"defined_centers": [center, "Throat"],
                "defined_channels": [{"gate1": 21, "gate2": 45}],
                "active_gates": [21, 45], "all_gates": [21, 45]},
            aspects=[{"body1": "Mars", "body2": "Saturn", "type": "square", "orb": 2.0}],
        ))
        d = get_atoms(uid)
        ok = d.get("atom_count") == 1
        labels: List[str] = []
        if ok:
            a = d["atoms"][0]
            labels = signals_labels(a)
            ok = "Defined Heart (Ego)" in labels
        check(f"S3.m '{center}' variant adds Defined Heart (Ego)", ok,
              f"atom_count={d.get('atom_count')} labels={labels}")

    # (n)
    uid = await seed_chart("s3n_expr8", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[{"body1": "Mars", "body2": "Saturn", "type": "square", "orb": 2.0}],
        numerology={"core": {"expression": {"number": 8}}},
    ))
    d = get_atoms(uid)
    check("S3.n Expression 8 fallback -> 1 atom", d.get("atom_count") == 1,
          f"atom_count={d.get('atom_count')}")
    if d.get("atoms"):
        a = d["atoms"][0]
        num_sig = next((s for s in a["signals"] if s["lens"] == "Numerology"), None)
        check("S3.n numerology label == 'Expression 8 (supporting)'",
              num_sig is not None and num_sig["label"] == "Expression 8 (supporting)",
              f"got {num_sig and num_sig.get('label')}")

    # (o) LP 4 wording
    uid = await seed_chart("s3o_lp4_wording", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[{"body1": "Mars", "body2": "Saturn", "type": "square", "orb": 2.0}],
        numerology={"core": {"life_path": {"number": 4}}},
    ))
    d = get_atoms(uid)
    ok = False
    msg = ""
    if d.get("atoms"):
        a = d["atoms"][0]
        num_sig = next((s for s in a["signals"] if s["lens"] == "Numerology"), None)
        if num_sig:
            ev = num_sig.get("evidence", "").lower()
            ok = ("structure" in ev) and ("steady" in ev)
            msg = ev
    check("S3.o LP 4 evidence contains 'structure' and 'steady'", ok, msg)

    # LP 8 wording
    uid = await seed_chart("s3o_lp8_wording", mk_chart(
        hd={"defined_centers": ["Throat"], "active_gates": [21], "all_gates": [21]},
        aspects=[{"body1": "Mars", "body2": "Saturn", "type": "square", "orb": 2.0}],
        numerology={"core": {"life_path": {"number": 8}}},
    ))
    d = get_atoms(uid)
    ok = False
    msg = ""
    if d.get("atoms"):
        a = d["atoms"][0]
        num_sig = next((s for s in a["signals"] if s["lens"] == "Numerology"), None)
        if num_sig:
            ev = num_sig.get("evidence", "").lower()
            ok = ("mastery" in ev) and ("material" in ev)
            msg = ev
    check("S3.o LP 8 evidence contains 'mastery' and 'material'", ok, msg)


# S4
async def test_s4_resilience() -> None:
    print("\n========== S4: Resilience ==========")
    db = await get_db()

    uid = await seed_chart("s4_empty_hd", {"human_design": {},
        "astrology": {"planets": DEFAULT_PLANETS, "aspects": []}, "numerology": {}})
    d = get_atoms(uid)
    check("S4 empty human_design -> 200, atoms=[]",
          d.get("atom_count") == 0 and isinstance(d.get("atoms"), list),
          f"resp={d}")

    uid = await seed_chart("s4_no_aspects", mk_chart(
        hd={"defined_centers": ["Ego"], "active_gates": [21], "all_gates": [21]},
    ))
    await db.charts.update_one({"user_id": uid}, {"$unset": {"astrology.aspects": ""}})
    d = get_atoms(uid)
    check("S4 missing aspects -> 200, no 500",
          isinstance(d.get("atoms"), list), f"resp={d}")

    uid = await seed_chart("s4_no_planets", mk_chart(
        hd={"defined_centers": ["Ego"], "active_gates": [21], "all_gates": [21]},
    ))
    await db.charts.update_one({"user_id": uid}, {"$unset": {"astrology.planets": ""}})
    d = get_atoms(uid)
    check("S4 missing planets -> 200",
          isinstance(d.get("atoms"), list), f"resp={d}")

    uid = await seed_chart("s4_malformed_ch", mk_chart(
        hd={
            "defined_centers": ["Ego"],
            "defined_channels": [{"gate1": "abc", "gate2": 45}, {"gate1": 21, "gate2": "xyz"}],
            "active_gates": [], "all_gates": [],
        },
        aspects=[],
    ))
    d = get_atoms(uid)
    check("S4 malformed channels -> 200",
          isinstance(d.get("atoms"), list), f"resp={d}")

    uid = await seed_chart("s4_no_num", mk_chart(
        hd={"defined_centers": ["Ego"], "active_gates": [21], "all_gates": [21]},
        aspects=[{"body1": "Mars", "body2": "Saturn", "type": "square", "orb": 2.0}],
        numerology=None,
    ))
    d = get_atoms(uid)
    check("S4 missing numerology -> 200",
          isinstance(d.get("atoms"), list), f"resp={d}")


# S5
def test_s5_regression() -> None:
    print("\n========== S5: Regression on prior atoms ==========")
    d = get_atoms("6a110c549ea9d4f6f4e1e961")
    ok = (d.get("atom_count") == 1
          and d.get("atoms", [{}])[0].get("atom_id") == "certainty_pattern")
    check("S5.certainty.demo -> 1 atom: certainty_pattern", ok,
          f"atom_count={d.get('atom_count')} ids={[a.get('atom_id') for a in d.get('atoms',[])]}")

    d = get_atoms("6a111013f662cf2da04a389c")
    ok = (d.get("atom_count") == 1
          and d.get("atoms", [{}])[0].get("atom_id") == "emotional_permeability")
    check("S5.permeability.demo -> 1 atom: emotional_permeability", ok,
          f"atom_count={d.get('atom_count')} ids={[a.get('atom_id') for a in d.get('atoms',[])]}")


# S6
async def test_s6_multi() -> None:
    print("\n========== S6: Multi-atom coexistence ==========")
    hd = {
        "defined_centers":   ["Ajna", "Ego", "Throat", "G Center", "Sacral"],
        "undefined_centers": ["Head", "Solar Plexus", "Spleen", "Root"],
        "defined_channels": [
            {"gate1": 21, "gate2": 45},
            {"gate1": 6,  "gate2": 59},
        ],
        "active_gates": [4, 63, 21, 45, 6, 59],
        "all_gates":    [4, 63, 21, 45, 6, 59],
    }
    aspects = [
        {"body1": "Mercury", "body2": "Saturn",  "type": "square", "orb": 2.0},
        {"body1": "Moon",    "body2": "Neptune", "type": "square", "orb": 2.0},
        {"body1": "Mars",    "body2": "Saturn",  "type": "square", "orb": 2.0},
    ]
    uid = await seed_chart("s6_multi", mk_chart(
        hd=hd,
        aspects=aspects,
        numerology={"core": {"life_path": {"number": 7}}},
    ))
    d = get_atoms(uid)
    check("S6 atom_count == 3", d.get("atom_count") == 3,
          f"atom_count={d.get('atom_count')} ids={[a.get('atom_id') for a in d.get('atoms',[])]}")
    ids = [a.get("atom_id") for a in d.get("atoms", [])]
    expected_order = ["certainty_pattern", "emotional_permeability", "achievement_as_stabilization"]
    check("S6 atoms in declaration order", ids == expected_order, f"got {ids}")


async def main() -> None:
    print("=" * 70)
    print("Achievement-as-Stabilization atom — backend test suite")
    print(f"BASE = {BASE}")
    print(f"DB   = {DB_NAME}")
    print("=" * 70)
    try:
        test_s1_real_users()
        test_s2_demo()
        await test_s3_boundaries()
        await test_s4_resilience()
        test_s5_regression()
        await test_s6_multi()
    finally:
        await cleanup_synthetic()

    print("\n" + "=" * 70)
    print(f"PASSED: {len(PASS)}")
    print(f"FAILED: {len(FAIL)}")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  - {f}")
    print("=" * 70)
    sys.exit(0 if not FAIL else 1)


if __name__ == "__main__":
    asyncio.run(main())
