"""Adversarial smoke test for Phase 1.7 Timezone Hardening.

Sends payloads with deliberately wrong timezones and verifies that the
backend stores the coordinate-derived IANA name regardless. Reads back
from Mongo directly (bypasses the API response model).
Cleans up everything it creates.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.request
import urllib.error

from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BASE = "http://localhost:8001/api"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "test_database")


def req(method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


async def main():
    cli = AsyncIOMotorClient(MONGO_URL)
    db = cli[DB_NAME]

    created_users = []
    created_people = []  # (user_id, person_id)
    failures = []
    passes = []

    # ---------- Area 2: POST /api/users adversarial cases ----------
    cases = [
        ("BuenosAires", -34.6037, -58.3816, "+08:00", "America/Argentina/Buenos_Aires"),
        ("NewYork",      40.7128, -74.0060, "Asia/Kuala_Lumpur", "America/New_York"),
        ("KualaLumpur",   3.1390, 101.6869, "UTC", "Asia/Kuala_Lumpur"),
        ("LosAngeles",   34.0522, -118.2437, "+00:00", "America/Los_Angeles"),
    ]
    for label, lat, lon, bad_tz, expected in cases:
        payload = {
            "name": f"TEST_ADV_{label}",
            "birth_date": "1990-05-10",
            "birth_time": "06:00",
            "city": "TestCity",
            "country": "TestCountry",
            "latitude": lat, "longitude": lon,
            "timezone": bad_tz,
        }
        status, body = req("POST", "/users", payload)
        if status != 200:
            failures.append(f"USER {label}: HTTP {status} body={body}")
            continue
        uid = body.get("id")
        created_users.append(uid)
        doc = await db.users.find_one({"_id": ObjectId(uid)})
        if not doc:
            failures.append(f"USER {label}: no Mongo doc id={uid}")
            continue
        tz = doc.get("timezone")
        src = doc.get("timezone_source")
        ver = doc.get("timezone_resolver_version")
        resolved_at = doc.get("timezone_resolved_at")
        ok = (tz == expected and src == "coordinates"
              and ver == "1.0.0" and bool(resolved_at))
        msg = (f"USER {label}: stored tz={tz} src={src} ver={ver} "
               f"resolved_at={'set' if resolved_at else 'MISSING'} "
               f"(expected {expected})")
        (passes if ok else failures).append(msg)

    # ---------- Area 3: Saved-people adversarial ----------
    # Parent user with KL coords
    parent_payload = {
        "name": "TEST_ADV_PARENT",
        "birth_date": "1990-01-01",
        "birth_time": "06:00",
        "city": "KL", "country": "Malaysia",
        "latitude": 3.139, "longitude": 101.6869,
        "timezone": "Asia/Kuala_Lumpur",
    }
    status, body = req("POST", "/users", parent_payload)
    if status != 200:
        failures.append(f"SAVED-PEOPLE: parent setup failed {status} {body}")
    else:
        parent_uid = body["id"]
        created_users.append(parent_uid)

        # (3a) Create saved person with BA coords + tz=+08:00
        sp_payload = {
            "name": "TEST_ADV_SP_BA",
            "relationship_type": "friend",
            "birth_date": "1990-05-10",
            "birth_time": "06:00",
            "birth_time_accuracy": "exact",
            "birth_location": {
                "city": "Buenos Aires", "country": "Argentina",
                "latitude": -34.6037, "longitude": -58.3816,
            },
            "birth_location_accuracy": "exact",
            "timezone": "+08:00",
        }
        st, sb = req("POST", f"/people/{parent_uid}", sp_payload)
        if st != 200:
            failures.append(f"SP create BA: {st} {sb}")
        else:
            pid = sb["id"]
            created_people.append((parent_uid, pid))
            ok = (sb["timezone"] == "America/Argentina/Buenos_Aires"
                  and sb["timezone_source"] == "coordinates"
                  and sb["timezone_resolver_version"] == "1.0.0")
            msg = f"SP create BA: tz={sb['timezone']} src={sb['timezone_source']}"
            (passes if ok else failures).append(msg)

            # (3b) PATCH to NY coords without tz field
            st, pb = req("PATCH", f"/people/{parent_uid}/{pid}", {
                "birth_location": {
                    "city": "New York", "country": "USA",
                    "latitude": 40.7128, "longitude": -74.0060,
                },
            })
            if st != 200:
                failures.append(f"SP patch NY: {st} {pb}")
            else:
                ok = (pb["timezone"] == "America/New_York"
                      and pb["timezone_source"] == "coordinates")
                msg = f"SP patch NY (no tz): tz={pb['timezone']} src={pb['timezone_source']}"
                (passes if ok else failures).append(msg)

            # (3c) PATCH clearing birth_location with non-IANA tz → 400
            st, pb = req("PATCH", f"/people/{parent_uid}/{pid}", {
                "birth_location": None,
                "birth_location_accuracy": "unknown",
                "timezone": "+08:00",
            })
            ok = st >= 400
            msg = f"SP patch clear-loc+offset: HTTP {st} (expected >=400) body={pb}"
            (passes if ok else failures).append(msg)

    # ---------- Cleanup ----------
    if created_users:
        result = await db.users.delete_many(
            {"_id": {"$in": [ObjectId(u) for u in created_users]}}
        )
        print(f"[CLEANUP] users deleted: {result.deleted_count}/{len(created_users)}")
    if created_people:
        uids = list({u for u, _ in created_people})
        result = await db.saved_people.delete_many({"user_id": {"$in": uids}})
        print(f"[CLEANUP] saved_people deleted: {result.deleted_count}")

    print("\n=== PASSES ===")
    for p in passes:
        print(" ✓", p)
    print("\n=== FAILURES ===")
    for f in failures:
        print(" ✗", f)
    print(f"\nResult: {len(passes)} pass, {len(failures)} fail")
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    asyncio.run(main())
