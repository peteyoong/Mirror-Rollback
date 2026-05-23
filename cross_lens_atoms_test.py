"""
Cross-Lens Synthesis Atoms V1 — Backend Test
Tests GET /api/synthesis/atoms/{user_id} per review request.
"""
import os
import sys
import uuid
import asyncio
from dotenv import load_dotenv
import requests
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

BASE_URL = "http://localhost:8001/api"

results = []


def record(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    results.append((name, ok, detail))
    print(f"[{status}] {name}{(' — ' + detail) if detail else ''}")


def assert_eq(name: str, actual, expected):
    ok = actual == expected
    record(name, ok, f"expected={expected!r} actual={actual!r}" if not ok else "")
    return ok


def hit(user_id: str):
    r = requests.get(f"{BASE_URL}/synthesis/atoms/{user_id}", timeout=15)
    return r


# ---------------------------------------------------------------------------
# Scenario 1: real users — expect 200 + empty atoms
# ---------------------------------------------------------------------------
REAL_USERS = {
    "Pete":     "697f0c6abf35c0528ff06954",
    "Mel":      "697ec826ad4b18f75bf42616",
    "Isaac":    "69dda348de9cb1c83c0780f8",
    "Thaddeus": "69dd0b2cc92ba973f8838c11",
}


def test_real_users_empty():
    print("\n=== Scenario 1: Real users (expect 200 + atom_count == 0) ===")
    for name, uid in REAL_USERS.items():
        r = hit(uid)
        ok_status = r.status_code == 200
        record(f"S1.{name} status 200", ok_status, f"got {r.status_code}")
        if not ok_status:
            continue
        cc = r.headers.get("Cache-Control", "")
        record(f"S1.{name} Cache-Control contains 'no-store'", "no-store" in cc, f"got '{cc}'")
        j = r.json()
        assert_eq(f"S1.{name} success", j.get("success"), True)
        assert_eq(f"S1.{name} build_marker", j.get("build_marker"), "cross-lens-atoms-v1")
        assert_eq(f"S1.{name} data_mode", j.get("data_mode"), "cross_lens_atoms")
        assert_eq(f"S1.{name} atom_count", j.get("atom_count"), 0)
        assert_eq(f"S1.{name} atoms == []", j.get("atoms"), [])


# ---------------------------------------------------------------------------
# Scenario 2: unknown user -> 404
# ---------------------------------------------------------------------------
def test_unknown_user_404():
    print("\n=== Scenario 2: Unknown user (expect 404) ===")
    r = hit("000000000000000000000099")
    record("S2 status 404", r.status_code == 404, f"got {r.status_code}")
    try:
        detail = r.json().get("detail", "")
    except Exception:
        detail = r.text
    record(
        "S2 detail mentions 'chart not found'",
        "chart not found" in str(detail).lower(),
        f"detail={detail!r}",
    )


# ---------------------------------------------------------------------------
# Scenario 3-5: synthetic charts. Use motor for async insert + cleanup.
# ---------------------------------------------------------------------------
async def insert_chart(client, user_id: str, chart_payload: dict):
    db = client[DB_NAME]
    doc = {"user_id": user_id, **chart_payload}
    await db.charts.delete_many({"user_id": user_id})
    await db.charts.insert_one(doc)


async def cleanup_chart(client, user_id: str):
    db = client[DB_NAME]
    await db.charts.delete_many({"user_id": user_id})


def synth_chart(
    centers=("Ajna", "Throat"),
    gates=(4, 63, 17, 11),
    aspect_type="square",
    aspect_orb=2.1,
    life_path=7,
    include_numerology=True,
    include_aspects=True,
):
    chart = {
        "human_design": {
            "defined_centers": list(centers),
            "active_gates": list(gates),
        },
        "astrology": {
            "aspects": (
                [{"body1": "Mercury", "body2": "Saturn", "type": aspect_type, "orb": aspect_orb}]
                if include_aspects
                else []
            ),
        },
    }
    if include_numerology:
        chart["numerology"] = {"core": {"life_path": {"number": life_path}}}
    else:
        chart["numerology"] = {}
    return chart


async def test_synthetic_match(client):
    print("\n=== Scenario 3: Synthetic chart that MATCHES (all 4) ===")
    uid = f"cross_lens_atoms_test_{uuid.uuid4().hex[:12]}"
    await insert_chart(client, uid, synth_chart())
    try:
        r = hit(uid)
        record("S3 status 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code != 200:
            return
        j = r.json()
        assert_eq("S3 atom_count", j.get("atom_count"), 1)
        atoms = j.get("atoms") or []
        if not atoms:
            record("S3 atoms non-empty", False, "atoms list empty")
            return
        a = atoms[0]
        assert_eq("S3 atom_id", a.get("atom_id"), "certainty_pattern")
        assert_eq("S3 matched", a.get("matched"), 4)
        assert_eq("S3 required", a.get("required"), 4)
        assert_eq("S3 match_mode", a.get("match_mode"), "strict_all")
        signals = a.get("signals") or []
        assert_eq("S3 signals length == 4", len(signals), 4)
        if len(signals) == 4:
            # signal 0
            assert_eq("S3 signal[0].lens", signals[0].get("lens"), "Human Design")
            assert_eq("S3 signal[0].label", signals[0].get("label"), "Defined Ajna")
            # signal 1
            assert_eq("S3 signal[1].lens", signals[1].get("lens"), "Human Design")
            record(
                "S3 signal[1].label contains 'Gate 4 & 63'",
                "Gate 4 & 63" in (signals[1].get("label") or "") or
                "Gates 4 & 63" in (signals[1].get("label") or ""),
                f"got {signals[1].get('label')!r}",
            )
            # signal 2
            assert_eq("S3 signal[2].lens", signals[2].get("lens"), "Astrology")
            record(
                "S3 signal[2].label starts with 'Mercury Square Saturn'",
                (signals[2].get("label") or "").startswith("Mercury Square Saturn"),
                f"got {signals[2].get('label')!r}",
            )
            # signal 3
            assert_eq("S3 signal[3].lens", signals[3].get("lens"), "Numerology")
            assert_eq("S3 signal[3].label", signals[3].get("label"), "Life Path 7")
        rec = a.get("recognition") or ""
        record("S3 recognition non-empty string", isinstance(rec, str) and len(rec.strip()) > 0,
               f"got {rec!r}")
        record(
            "S3 recognition does NOT start with 'Your Ajna'",
            not rec.strip().startswith("Your Ajna"),
            f"got {rec!r}",
        )
    finally:
        await cleanup_chart(client, uid)


async def test_boundary_cases(client):
    print("\n=== Scenario 4: Boundary variants ===")

    boundary_specs = [
        ("S4a life_path=8", synth_chart(life_path=8), 0, None),
        ("S4b aspect=trine", synth_chart(aspect_type="trine"), 0, None),
        ("S4c no Ajna", synth_chart(centers=("Throat", "Spleen")), 0, None),
        ("S4d gates [17,11]", synth_chart(gates=(17, 11)), 0, None),
        ("S4e gates [4] only", synth_chart(gates=(4,)), 1, "Gate 4 — Answers"),
        ("S4f gates [63] only", synth_chart(gates=(63,)), 1, "Gate 63 — Doubt"),
    ]

    for label, chart_payload, expected_count, expected_gate_label in boundary_specs:
        uid = f"cross_lens_atoms_test_{uuid.uuid4().hex[:12]}"
        await insert_chart(client, uid, chart_payload)
        try:
            r = hit(uid)
            record(f"{label} status 200", r.status_code == 200, f"got {r.status_code}")
            if r.status_code != 200:
                continue
            j = r.json()
            assert_eq(f"{label} atom_count", j.get("atom_count"), expected_count)
            if expected_count == 1 and expected_gate_label is not None:
                atoms = j.get("atoms") or []
                if atoms and len(atoms[0].get("signals", [])) >= 2:
                    actual_label = atoms[0]["signals"][1].get("label")
                    assert_eq(f"{label} signals[1].label", actual_label, expected_gate_label)
                else:
                    record(f"{label} signals[1] present", False, "no signals or atoms")
        finally:
            await cleanup_chart(client, uid)


async def test_resilience(client):
    print("\n=== Scenario 5: Resilience (missing/empty sections) ===")
    uid = f"cross_lens_atoms_test_{uuid.uuid4().hex[:12]}"
    chart = {
        "human_design": {},  # nothing
        "astrology": {},      # no aspects field
        "numerology": {},     # empty
    }
    await insert_chart(client, uid, chart)
    try:
        r = hit(uid)
        record("S5 status 200 (not 500)", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            j = r.json()
            assert_eq("S5 atoms == []", j.get("atoms"), [])
            assert_eq("S5 atom_count == 0", j.get("atom_count"), 0)
    finally:
        await cleanup_chart(client, uid)

    # Also test with totally missing top-level sections.
    uid2 = f"cross_lens_atoms_test_{uuid.uuid4().hex[:12]}"
    await insert_chart(client, uid2, {})  # only user_id
    try:
        r = hit(uid2)
        record("S5b empty chart status 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            j = r.json()
            assert_eq("S5b atoms == []", j.get("atoms"), [])
    finally:
        await cleanup_chart(client, uid2)


async def main_async():
    client = AsyncIOMotorClient(MONGO_URL)
    try:
        test_real_users_empty()
        test_unknown_user_404()
        await test_synthetic_match(client)
        await test_boundary_cases(client)
        await test_resilience(client)
    finally:
        # Defensive sweep — remove any leftover test docs.
        await client[DB_NAME].charts.delete_many(
            {"user_id": {"$regex": "^cross_lens_atoms_test_"}}
        )
        # Also remove the historical "synthetic_certainty_test_user" if any prior run left it.
        await client[DB_NAME].charts.delete_many(
            {"user_id": "synthetic_certainty_test_user"}
        )
        client.close()


if __name__ == "__main__":
    asyncio.run(main_async())

    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed}/{total} passed, {failed} failed")
    if failed:
        print("\nFailed checks:")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
    sys.exit(0 if failed == 0 else 1)
