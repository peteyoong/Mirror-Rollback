"""
Backend test for Emotional Permeability cross-lens atom.

Tests scenarios S1-S5 from the review request against
GET /api/synthesis/atoms/{user_id} on the public backend URL.

Synthetic test users are seeded directly into MongoDB with user_ids
prefixed `cross_lens_atoms_test_` and removed during teardown.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load backend .env for MONGO_URL & DB_NAME
load_dotenv("/app/backend/.env")

BACKEND_URL = "https://certainty-pattern.preview.emergentagent.com/api"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "test_database")

PREFIX = "cross_lens_atoms_test_"

# -------------------- Chart builders --------------------
EMPTY_DEBUG_STAMP = {
    "sidereal_settings_used": {
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0,
    },
    "computed_at_iso": datetime.utcnow().isoformat(),
    "migration": "synthetic_test",
}


def base_planets() -> Dict[str, Any]:
    return {
        "Sun": {"sign": "Pisces", "degree": 18.0, "longitude": 348.0, "house": 7, "retrograde": False},
        "Moon": {"sign": "Scorpio", "degree": 22.0, "longitude": 232.0, "house": 12, "retrograde": False},
        "Mercury": {"sign": "Pisces", "degree": 2.0, "longitude": 332.0, "house": 6, "retrograde": False},
        "Venus": {"sign": "Aries", "degree": 5.0, "longitude": 5.0, "house": 8, "retrograde": False},
        "Mars": {"sign": "Pisces", "degree": 14.0, "longitude": 344.0, "house": 7, "retrograde": False},
        "Jupiter": {"sign": "Aquarius", "degree": 12.0, "longitude": 312.0, "house": 6, "retrograde": False},
        "Saturn": {"sign": "Scorpio", "degree": 26.0, "longitude": 236.0, "house": 12, "retrograde": True},
        "Uranus": {"sign": "Sagittarius", "degree": 18.0, "longitude": 258.0, "house": 1, "retrograde": True},
        "Neptune": {"sign": "Sagittarius", "degree": 26.0, "longitude": 266.0, "house": 8, "retrograde": True},
        "Pluto": {"sign": "Libra", "degree": 4.0, "longitude": 184.0, "house": 10, "retrograde": True},
    }


def neutral_planets() -> Dict[str, Any]:
    """Planets with no Pisces emphasis, Neptune non-angular, Moon not in 12."""
    return {
        "Sun": {"sign": "Aries", "degree": 18.0, "longitude": 18.0, "house": 1, "retrograde": False},
        "Moon": {"sign": "Taurus", "degree": 22.0, "longitude": 52.0, "house": 5, "retrograde": False},
        "Mercury": {"sign": "Aries", "degree": 2.0, "longitude": 2.0, "house": 1, "retrograde": False},
        "Venus": {"sign": "Gemini", "degree": 5.0, "longitude": 65.0, "house": 2, "retrograde": False},
        "Mars": {"sign": "Cancer", "degree": 14.0, "longitude": 104.0, "house": 3, "retrograde": False},
        "Jupiter": {"sign": "Leo", "degree": 12.0, "longitude": 132.0, "house": 4, "retrograde": False},
        "Saturn": {"sign": "Virgo", "degree": 26.0, "longitude": 176.0, "house": 5, "retrograde": True},
        "Uranus": {"sign": "Libra", "degree": 18.0, "longitude": 198.0, "house": 6, "retrograde": True},
        "Neptune": {"sign": "Scorpio", "degree": 26.0, "longitude": 236.0, "house": 8, "retrograde": True},
        "Pluto": {"sign": "Capricorn", "degree": 4.0, "longitude": 274.0, "house": 9, "retrograde": True},
    }


def make_chart(
    user_id: str,
    defined_centers: List[str],
    defined_channels: List[Dict],
    active_gates: List,
    planets: Dict[str, Any],
    aspects: List[Dict],
    life_path: int | None,
) -> Dict[str, Any]:
    chart = {
        "user_id": user_id,
        "calculated_at": datetime.now(timezone.utc),
        "debug_stamp": EMPTY_DEBUG_STAMP,
        "human_design": {
            "type": "Generator",
            "strategy": "To Respond",
            "authority": "Sacral",
            "profile": "2/4",
            "definition": "Single",
            "incarnation_cross": {"name": "Right Angle Cross of Eden"},
            "defined_centers": defined_centers,
            "undefined_centers": [],
            "defined_channels": defined_channels,
            "active_gates": active_gates,
            "all_gates": active_gates,
        },
        "astrology": {
            "planets": planets,
            "aspects": aspects,
            "houses": {
                "system": "Equal",
                "cusps": [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                "ascendant": 240.0,
                "mc": 150.0,
            },
            "chart_type": "True Sidereal (Synthetic Test)",
        },
        "numerology": (
            {"core": {"life_path": {"number": life_path, "description": "test"}}}
            if life_path is not None
            else {}
        ),
    }
    return chart


# -------------------- DB helpers --------------------
async def seed_chart(db, chart: Dict[str, Any]) -> None:
    await db.charts.delete_many({"user_id": chart["user_id"]})
    await db.charts.insert_one(chart)


async def delete_chart(db, user_id: str) -> None:
    await db.charts.delete_many({"user_id": user_id})


# -------------------- HTTP helper --------------------
def get_atoms(user_id: str) -> Tuple[int, Dict[str, Any]]:
    r = requests.get(f"{BACKEND_URL}/synthesis/atoms/{user_id}", timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"_raw": r.text}


# -------------------- Test scenarios --------------------
results: List[Tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    results.append((name, ok, detail))


async def test_S1_real_users_no_match() -> None:
    real_users = [
        ("Pete", "697f0c6abf35c0528ff06954"),
        ("Mel", "697ec826ad4b18f75bf42616"),
        ("Isaac", "69dda348de9cb1c83c0780f8"),
        ("Thaddeus", "69dd0b2cc92ba973f8838c11"),
    ]
    for name, uid in real_users:
        code, body = get_atoms(uid)
        if code != 200:
            record(f"S1 {name}", False, f"status={code} body={body}")
            continue
        ok = body.get("atom_count") == 0 and body.get("atoms") == []
        detail = f"atom_count={body.get('atom_count')} ids={[a.get('atom_id') for a in body.get('atoms', [])]}"
        record(f"S1 {name}", ok, detail)


async def test_S2_permeability_demo() -> None:
    uid = "6a111013f662cf2da04a389c"
    code, body = get_atoms(uid)
    if code != 200:
        record("S2 seeded demo", False, f"status={code}")
        return
    atoms = body.get("atoms", [])
    if body.get("atom_count") != 1 or len(atoms) != 1:
        record("S2 seeded demo atom_count", False, f"atom_count={body.get('atom_count')} atoms={atoms}")
        return
    atom = atoms[0]
    expected_recognition = (
        "Emotional environments enter you quickly. You often adapt to "
        "what others are feeling before deciding whether you actually "
        "want to carry it."
    )
    checks = [
        ("atom_id == emotional_permeability", atom.get("atom_id") == "emotional_permeability"),
        ("matched == 4", atom.get("matched") == 4),
        ("required == 4", atom.get("required") == 4),
        ("match_mode == strict_all", atom.get("match_mode") == "strict_all"),
        ("core_signals_required == 3", atom.get("core_signals_required") == 3),
        ("has_supporting == True", atom.get("has_supporting") is True),
        ("recognition matches", atom.get("recognition") == expected_recognition),
    ]
    signals = atom.get("signals", [])
    expected_signals = [
        ("Human Design", "Open Solar Plexus"),
        ("Human Design", "Channel 6-59 — Intimacy"),
        ("Astrology", "Moon Square Neptune (1.8°)"),
        ("Numerology", "Life Path 2 (supporting)"),
    ]
    if len(signals) != 4:
        record("S2 seeded demo signal count", False, f"len(signals)={len(signals)}")
    for i, (exp_lens, exp_label) in enumerate(expected_signals):
        if i >= len(signals):
            checks.append((f"signal[{i}] exists", False))
            continue
        s = signals[i]
        checks.append((f"signal[{i}] lens={exp_lens}", s.get("lens") == exp_lens))
        checks.append((f"signal[{i}] label={exp_label}", s.get("label") == exp_label))

    all_ok = all(ok for _, ok in checks)
    detail = "; ".join([f"{n}={ok}" for n, ok in checks if not ok]) or "all sub-checks passed"
    record("S2 seeded demo", all_ok, detail)


def labels_of(atom) -> List[str]:
    return [s.get("label") for s in atom.get("signals", [])]


async def test_S3_variants(db) -> None:
    pisces_planets_3 = neutral_planets()
    pisces_planets_3["Sun"] = {"sign": "Pisces", "degree": 10.0, "longitude": 340.0, "house": 1, "retrograde": False}
    pisces_planets_3["Moon"] = {"sign": "Pisces", "degree": 12.0, "longitude": 342.0, "house": 1, "retrograde": False}
    pisces_planets_3["Mercury"] = {"sign": "Pisces", "degree": 5.0, "longitude": 335.0, "house": 1, "retrograde": False}

    moon12_planets = neutral_planets()
    moon12_planets["Moon"]["house"] = 12

    neptune_h1_planets = neutral_planets()
    neptune_h1_planets["Neptune"] = {"sign": "Aquarius", "degree": 1.0, "longitude": 301.0, "house": 1, "retrograde": False}

    one_pisces_planets = neutral_planets()
    one_pisces_planets["Mercury"] = {"sign": "Pisces", "degree": 5.0, "longitude": 335.0, "house": 6, "retrograde": False}

    # neptune in house 8 already in neutral_planets

    base_aspect_neptune = [
        {"body1": "Moon", "body2": "Neptune", "type": "square", "orb": 1.8, "exact_angle": 91.8, "applying": False}
    ]

    variants = {
        # a) Defined SP blocks
        "S3a defined SP blocks": {
            "defined_centers": ["Solar Plexus", "Ajna"],
            "defined_channels": [{"gate1": 6, "gate2": 59, "centers": ["SP", "Sacral"]}],
            "active_gates": [6, 59, 22],
            "planets": base_planets(),
            "aspects": base_aspect_neptune,
            "life_path": 2,
            "expect": {"atom_count": 0},
        },
        # b) No HD secondary blocks
        "S3b no HD secondary blocks": {
            "defined_centers": ["Throat", "G Center"],
            "defined_channels": [],
            "active_gates": [1, 2, 3],
            "planets": base_planets(),
            "aspects": base_aspect_neptune,
            "life_path": 2,
            "expect": {"atom_count": 0},
        },
        # c) No astro signal blocks
        "S3c no astro blocks": {
            "defined_centers": ["Throat", "G Center", "Sacral"],
            "defined_channels": [{"gate1": 6, "gate2": 59, "centers": ["SP", "Sacral"]}],
            "active_gates": [6, 59],
            "planets": one_pisces_planets,  # 1 pisces, neptune house 8, moon house 5
            "aspects": [],
            "life_path": 2,
            "expect": {"atom_count": 0},
        },
        # d) Numerology alone never triggers
        "S3d numerology alone": {
            "defined_centers": ["Solar Plexus", "Ajna"],
            "defined_channels": [],
            "active_gates": [1, 2, 3],
            "planets": neutral_planets(),
            "aspects": [],
            "life_path": 2,
            "expect": {"atom_count": 0},
        },
        # e) Channel 39-55 path with Moon 12th, no qualifying LP
        "S3e channel 39-55": {
            "defined_centers": ["Throat", "G Center", "Sacral"],
            "defined_channels": [{"gate1": 39, "gate2": 55, "centers": ["SP", "Root"]}],
            "active_gates": [39, 55],
            "planets": moon12_planets,
            "aspects": [],
            "life_path": 3,
            "expect": {
                "atom_count": 1,
                "labels": ["Open Solar Plexus", "Channel 39-55 — Moodiness", "Moon in the 12th house"],
                "len_signals": 3,
                "has_supporting": False,
                "core_signals_required": 3,
            },
        },
        # f) Gate 22 path + Neptune house 1 + LP 11
        "S3f gate 22 path": {
            "defined_centers": ["Throat", "G Center"],
            "defined_channels": [],
            "active_gates": [22, 1, 2],
            "planets": neptune_h1_planets,
            "aspects": [],
            "life_path": 11,
            "expect": {
                "atom_count": 1,
                "labels": [
                    "Open Solar Plexus",
                    "Gate 22 — Grace",
                    "Neptune angular (house 1)",
                    "Life Path 11 (supporting)",
                ],
            },
        },
        # g) Gate 49 path + 3 pisces personals + LP 6
        "S3g gate 49 path": {
            "defined_centers": ["Throat", "G Center"],
            "defined_channels": [],
            "active_gates": [49, 1, 2],
            "planets": pisces_planets_3,
            "aspects": [],
            "life_path": 6,
            "expect": {
                "atom_count": 1,
                "labels": [
                    "Open Solar Plexus",
                    "Gate 49 — Principles",
                    "3 personal planets in Pisces",
                    "Life Path 6 (supporting)",
                ],
            },
        },
        # h) Moon-Pluto opposition path + LP 7 (non-supporting)
        "S3h moon-pluto path": {
            "defined_centers": ["Throat", "G Center", "Sacral"],
            "defined_channels": [{"gate1": 6, "gate2": 59, "centers": ["SP", "Sacral"]}],
            "active_gates": [6, 59],
            "planets": neutral_planets(),
            "aspects": [
                {"body1": "Moon", "body2": "Pluto", "type": "opposition", "orb": 3.0, "applying": False}
            ],
            "life_path": 7,
            "expect": {
                "atom_count": 1,
                "len_signals": 3,
                "labels_partial": {
                    2: "Moon Opposition Pluto (3.0°)",
                },
            },
        },
        # i) Aspect tightness preference: Pluto opp 2.0 vs Neptune square 5.0 -> Pluto wins (tighter orb)
        "S3i aspect tightness": {
            "defined_centers": ["Throat", "G Center", "Sacral"],
            "defined_channels": [{"gate1": 6, "gate2": 59, "centers": ["SP", "Sacral"]}],
            "active_gates": [6, 59],
            "planets": neutral_planets(),
            "aspects": [
                {"body1": "Moon", "body2": "Pluto", "type": "opposition", "orb": 2.0, "applying": False},
                {"body1": "Moon", "body2": "Neptune", "type": "square", "orb": 5.0, "applying": False},
            ],
            "life_path": 3,
            "expect": {
                "atom_count": 1,
                "labels_partial": {2: ("startswith", "Moon Opposition Pluto")},
            },
        },
        # j) Soft aspects don't count (trine)
        "S3j soft aspects don't count": {
            "defined_centers": ["Throat", "G Center", "Sacral"],
            "defined_channels": [{"gate1": 6, "gate2": 59, "centers": ["SP", "Sacral"]}],
            "active_gates": [6, 59],
            "planets": neutral_planets(),
            "aspects": [
                {"body1": "Moon", "body2": "Neptune", "type": "trine", "orb": 1.0, "applying": False}
            ],
            "life_path": 3,
            "expect": {"atom_count": 0},
        },
        # k) Certainty + Permeability simultaneous
        "S3k certainty + permeability": {
            "defined_centers": ["Ajna", "Throat", "G Center", "Sacral"],  # Defined Ajna, Open SP
            "defined_channels": [{"gate1": 6, "gate2": 59, "centers": ["SP", "Sacral"]}],
            "active_gates": [4, 6, 59],  # Gate 4 for Certainty
            "planets": neutral_planets(),
            "aspects": [
                {"body1": "Mercury", "body2": "Saturn", "type": "square", "orb": 2.0, "applying": False},
                {"body1": "Moon", "body2": "Neptune", "type": "square", "orb": 1.8, "applying": False},
            ],
            "life_path": 7,  # LP 7 for Certainty; not supporting for Permeability
            "expect": {
                "atom_count": 2,
                "atom_ids_order": ["certainty_pattern", "emotional_permeability"],
            },
        },
    }

    for name, cfg in variants.items():
        uid = PREFIX + name.replace(" ", "_")
        chart = make_chart(
            uid,
            cfg["defined_centers"],
            cfg["defined_channels"],
            cfg["active_gates"],
            cfg["planets"],
            cfg["aspects"],
            cfg["life_path"],
        )
        await seed_chart(db, chart)
        code, body = get_atoms(uid)
        try:
            if code != 200:
                record(name, False, f"status={code} body={body}")
                continue
            exp = cfg["expect"]
            ok = True
            details = []
            if "atom_count" in exp:
                if body.get("atom_count") != exp["atom_count"]:
                    ok = False
                    details.append(f"atom_count={body.get('atom_count')} expected {exp['atom_count']}")
            atoms = body.get("atoms", [])
            if "atom_ids_order" in exp:
                ids = [a.get("atom_id") for a in atoms]
                if ids != exp["atom_ids_order"]:
                    ok = False
                    details.append(f"atom_ids={ids} expected {exp['atom_ids_order']}")
            if exp.get("atom_count", 0) == 1 and atoms:
                a = atoms[0]
                if "labels" in exp:
                    labels = labels_of(a)
                    if labels != exp["labels"]:
                        ok = False
                        details.append(f"labels={labels} expected {exp['labels']}")
                if "len_signals" in exp:
                    if len(a.get("signals", [])) != exp["len_signals"]:
                        ok = False
                        details.append(f"len(signals)={len(a.get('signals', []))}")
                if "has_supporting" in exp:
                    if a.get("has_supporting") != exp["has_supporting"]:
                        ok = False
                        details.append(f"has_supporting={a.get('has_supporting')}")
                if "core_signals_required" in exp:
                    if a.get("core_signals_required") != exp["core_signals_required"]:
                        ok = False
                        details.append(f"core_signals_required={a.get('core_signals_required')}")
                if "labels_partial" in exp:
                    labels = labels_of(a)
                    for idx, expected in exp["labels_partial"].items():
                        actual = labels[idx] if idx < len(labels) else None
                        if isinstance(expected, tuple) and expected[0] == "startswith":
                            if not (actual and actual.startswith(expected[1])):
                                ok = False
                                details.append(f"signal[{idx}]={actual!r} did not start with {expected[1]!r}")
                        else:
                            if actual != expected:
                                ok = False
                                details.append(f"signal[{idx}]={actual!r} expected {expected!r}")
            record(name, ok, "; ".join(details) or "ok")
        finally:
            await delete_chart(db, uid)


async def test_S4_resilience(db) -> None:
    # Variant 1: empty human_design
    cases = []
    base_chart = make_chart(
        PREFIX + "S4_empty_hd",
        defined_centers=["Throat"],
        defined_channels=[],
        active_gates=[],
        planets=neutral_planets(),
        aspects=[],
        life_path=2,
    )
    base_chart["human_design"] = {}
    cases.append(("S4 empty human_design", base_chart))

    chart_no_aspects = make_chart(
        PREFIX + "S4_no_aspects",
        defined_centers=["Throat", "G Center"],
        defined_channels=[],
        active_gates=[22],
        planets=neutral_planets(),
        aspects=[],
        life_path=2,
    )
    chart_no_aspects["astrology"].pop("aspects", None)
    cases.append(("S4 missing aspects", chart_no_aspects))

    chart_no_num = make_chart(
        PREFIX + "S4_no_num",
        defined_centers=["Throat", "G Center"],
        defined_channels=[],
        active_gates=[22],
        planets=neutral_planets(),
        aspects=[],
        life_path=None,
    )
    chart_no_num["numerology"] = {}
    cases.append(("S4 missing numerology", chart_no_num))

    chart_bad_gates = make_chart(
        PREFIX + "S4_bad_gates",
        defined_centers=["Throat", "G Center"],
        defined_channels=[],
        active_gates=["foo", "bar", "22"],  # strings; one parseable
        planets=neutral_planets(),
        aspects=[],
        life_path=2,
    )
    cases.append(("S4 malformed gates list", chart_bad_gates))

    for name, chart in cases:
        await seed_chart(db, chart)
        try:
            code, body = get_atoms(chart["user_id"])
            if code != 200:
                record(name, False, f"status={code} body={body}")
                continue
            # For "bad gates" case, "22" can be parsed -> may trigger; but no astro signal so should be 0
            # Just require 200 + atoms is a list, no 500.
            atoms = body.get("atoms")
            ok = isinstance(atoms, list)
            record(name, ok, f"status=200 atom_count={body.get('atom_count')}")
        finally:
            await delete_chart(db, chart["user_id"])


async def test_S5_certainty_regression() -> None:
    uid = "6a110c549ea9d4f6f4e1e961"
    code, body = get_atoms(uid)
    if code != 200:
        record("S5 certainty seed regression", False, f"status={code} body={body}")
        return
    atoms = body.get("atoms", [])
    ok = (
        body.get("atom_count") == 1
        and len(atoms) == 1
        and atoms[0].get("atom_id") == "certainty_pattern"
    )
    record("S5 certainty seed regression", ok, f"atom_count={body.get('atom_count')} ids={[a.get('atom_id') for a in atoms]}")


# -------------------- Main --------------------
async def main() -> int:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        print(f"Backend URL: {BACKEND_URL}\nDB: {DB_NAME}\n")
        await test_S1_real_users_no_match()
        await test_S2_permeability_demo()
        await test_S3_variants(db)
        await test_S4_resilience(db)
        await test_S5_certainty_regression()
    finally:
        # Belt-and-suspenders cleanup
        result = await db.charts.delete_many({"user_id": {"$regex": f"^{PREFIX}"}})
        print(f"\nCleanup: removed {result.deleted_count} synthetic chart docs.")
        client.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(n, d) for n, ok, d in results if not ok]
    print(f"Total: {len(results)}  Passed: {passed}  Failed: {len(failed)}")
    if failed:
        print("\nFailed tests:")
        for n, d in failed:
            print(f"  - {n}: {d}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
