"""
Phase 1.7 — Timezone Hardening regression suite
================================================

These tests pin down the coordinate-driven timezone contract:

1. `services.timezone_resolver.resolve_iana_timezone` must return the correct
   IANA name for known coordinates in Argentina, KL, NY, LA, Chicago, London.
2. `is_iana_name()` must reject fixed offsets, UTC, GMT, empties.
3. `POST /api/users`, saved-people create + update must:
      - IGNORE client `timezone` when coords are present, and store the
        coordinate-derived IANA name.
      - PERSIST provenance fields.
      - REJECT non-IANA tz when no coords are supplied.
      - RE-RESOLVE tz on saved-person PATCH when birth_location coords change.

The HTTP tests hit the live preview backend (loopback :8001) using urllib.
They create isolated test rows and clean up via direct Mongo at the end.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import uuid
from typing import Any, Dict, Optional, Tuple

import pytest

BASE = "http://localhost:8001/api"

CASES = [
    # (label, latitude, longitude, expected_iana)
    ("Argentina",   -34.6037,  -58.3816, "America/Argentina/Buenos_Aires"),
    ("KualaLumpur",   3.1390,  101.6869, "Asia/Kuala_Lumpur"),
    ("NewYork",      40.7128,  -74.0060, "America/New_York"),
    ("LosAngeles",   34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago",      41.8781,  -87.6298, "America/Chicago"),
    ("London",       51.5074,   -0.1278, "Europe/London"),
]


# ---------------------------------------------------------------------------
# 1. Pure resolver tests (no HTTP)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label, lat, lon, expected", CASES)
def test_resolve_iana_timezone(label, lat, lon, expected):
    from services.timezone_resolver import resolve_iana_timezone
    got = resolve_iana_timezone(lat, lon)
    assert got == expected, f"{label}: expected {expected}, got {got}"


def test_resolve_returns_none_for_invalid_inputs():
    from services.timezone_resolver import resolve_iana_timezone
    assert resolve_iana_timezone(None, None) is None
    assert resolve_iana_timezone("not-a-number", "x") is None


def test_is_iana_name_rejects_fixed_offsets_and_aliases():
    from services.timezone_resolver import is_iana_name
    assert is_iana_name("Asia/Kuala_Lumpur") is True
    assert is_iana_name("America/Argentina/Buenos_Aires") is True
    for bad in ("+00:00", "+08:00", "-05:00", "UTC", "GMT", "Z", "", "   ", None, "Europe", "America"):
        assert is_iana_name(bad) is False, f"is_iana_name({bad!r}) should be False"


# ---------------------------------------------------------------------------
# Helpers for HTTP tests
# ---------------------------------------------------------------------------

def _backend_alive() -> bool:
    try:
        with urllib.request.urlopen(BASE + "/admin/build-info", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _backend_alive(),
    reason="Local backend on :8001 not reachable; HTTP regression suite skipped.",
)


def _req(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode() or "{}"
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


_CREATED_USERS: list[str] = []
_CREATED_SAVED: list[Tuple[str, str]] = []  # (user_id, person_id)


def _unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _create_user(name: str, lat: float, lon: float, client_tz: str,
                 city: str = "TestCity", country: str = "TestCountry") -> Tuple[int, Dict[str, Any]]:
    payload = {
        "name": name,
        "birth_date": "1990-05-10",
        "birth_time": "06:00",
        "city": city,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "timezone": client_tz,
    }
    status, body = _req("POST", "/users", payload)
    if status == 200 and isinstance(body, dict) and body.get("id"):
        _CREATED_USERS.append(body["id"])
    return status, body


def _read_user_doc(user_id: str) -> Dict[str, Any]:
    """Direct Mongo read so we can inspect provenance fields the response
    model doesn't expose."""
    import asyncio
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv()
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ.get("DB_NAME", "test_database")]

    async def go():
        return await db.users.find_one({"_id": ObjectId(user_id)})
    try:
        return asyncio.get_event_loop().run_until_complete(go()) or {}
    except RuntimeError:
        # New loop required (pytest already running)
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(go()) or {}
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# 2. POST /api/users — coordinates always win, client tz ignored
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label, lat, lon, expected", CASES)
def test_create_user_coords_override_client_timezone(label, lat, lon, expected):
    status, body = _create_user(
        name=_unique_name(f"U_{label}"),
        lat=lat, lon=lon,
        client_tz="+08:00",  # deliberately wrong for every non-KL case
    )
    assert status == 200, f"{label}: HTTP {status} body={body}"
    uid = body.get("id")
    assert uid, f"{label}: no id returned"
    doc = _read_user_doc(uid)
    assert doc.get("timezone") == expected, (
        f"{label}: expected stored timezone={expected!r}, got {doc.get('timezone')!r}"
    )
    assert doc.get("timezone_source") == "coordinates"
    assert doc.get("timezone_resolver_version") == "1.0.0"
    assert doc.get("timezone_resolved_at"), "provenance timestamp missing"


@pytest.mark.parametrize("bad_tz", ["+00:00", "+08:00", "UTC", "GMT"])
def test_create_user_rejects_fixed_offset_when_no_coords(bad_tz):
    """Without coordinates AND without a geocodable city, fixed offsets MUST
    be rejected. We pick a deliberately-unresolvable place so geocoding
    cannot supply coords and bail us into the coord-driven path."""
    payload = {
        "name": _unique_name("U_nocoord"),
        "birth_date": "1990-05-10",
        "birth_time": "06:00",
        "city": f"NoSuchPlace_{uuid.uuid4().hex[:6]}",
        "country": f"NoSuchCountry_{uuid.uuid4().hex[:6]}",
        # No lat/lon supplied — and the city/country above will not geocode.
        "timezone": bad_tz,
    }
    status, body = _req("POST", "/users", payload)
    # Either rejected at tz validation (400) or geocode failure (400).
    assert status >= 400, f"Expected rejection, got {status} body={body}"
    if status == 200 and isinstance(body, dict) and body.get("id"):
        _CREATED_USERS.append(body["id"])


# ---------------------------------------------------------------------------
# 3. Saved person create — coord-driven
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def parent_user_id() -> str:
    status, body = _create_user(
        name=_unique_name("PARENT"),
        lat=3.139, lon=101.6869,
        client_tz="Asia/Kuala_Lumpur",
    )
    assert status == 200, f"parent_user setup failed: {body}"
    return body["id"]


@pytest.mark.parametrize("label, lat, lon, expected", CASES)
def test_create_saved_person_coords_override_client_timezone(parent_user_id, label, lat, lon, expected):
    payload = {
        "name": _unique_name(f"SP_{label}"),
        "relationship_type": "friend",
        "birth_date": "1990-05-10",
        "birth_time": "06:00",
        "birth_time_accuracy": "exact",
        "birth_location": {
            "city": "TestCity", "country": "TestCountry",
            "latitude": lat, "longitude": lon,
        },
        "birth_location_accuracy": "exact",
        "timezone": "+08:00",  # wrong on purpose
    }
    status, body = _req("POST", f"/people/{parent_user_id}", payload)
    assert status == 200, f"{label}: {status} body={body}"
    pid = body["id"]
    _CREATED_SAVED.append((parent_user_id, pid))
    assert body["timezone"] == expected
    assert body["timezone_source"] == "coordinates"
    assert body["timezone_resolver_version"] == "1.0.0"


# ---------------------------------------------------------------------------
# 4. Saved person update — coord changes always re-resolve tz
# ---------------------------------------------------------------------------

def test_patch_saved_person_recomputes_tz_when_coords_change(parent_user_id):
    # Start in Kuala Lumpur
    create = {
        "name": _unique_name("SP_UPD"),
        "relationship_type": "friend",
        "birth_date": "1990-05-10",
        "birth_time": "06:00",
        "birth_time_accuracy": "exact",
        "birth_location": {
            "city": "Kuala Lumpur", "country": "Malaysia",
            "latitude": 3.139, "longitude": 101.6869,
        },
        "birth_location_accuracy": "exact",
        "timezone": "Asia/Kuala_Lumpur",
    }
    s, body = _req("POST", f"/people/{parent_user_id}", create)
    assert s == 200 and body["timezone"] == "Asia/Kuala_Lumpur"
    pid = body["id"]
    _CREATED_SAVED.append((parent_user_id, pid))

    # PATCH: move to Buenos Aires WITHOUT supplying a new tz
    s, body = _req("PATCH", f"/people/{parent_user_id}/{pid}", {
        "birth_location": {
            "city": "Buenos Aires", "country": "Argentina",
            "latitude": -34.6037, "longitude": -58.3816,
        },
    })
    assert s == 200, body
    assert body["timezone"] == "America/Argentina/Buenos_Aires", body
    assert body["timezone_source"] == "coordinates"


def test_patch_saved_person_rejects_fixed_offset_when_loc_cleared(parent_user_id):
    """If user clears birth_location and supplies a non-IANA tz, reject."""
    create = {
        "name": _unique_name("SP_CLR"),
        "relationship_type": "friend",
        "birth_date": "1990-05-10",
        "birth_time": "06:00",
        "birth_time_accuracy": "exact",
        "birth_location": {
            "city": "Kuala Lumpur", "country": "Malaysia",
            "latitude": 3.139, "longitude": 101.6869,
        },
        "birth_location_accuracy": "exact",
        "timezone": "Asia/Kuala_Lumpur",
    }
    s, body = _req("POST", f"/people/{parent_user_id}", create)
    assert s == 200
    pid = body["id"]
    _CREATED_SAVED.append((parent_user_id, pid))

    # Clear coords by switching accuracy=unknown so location can be None,
    # then supply a bad tz.
    s, body = _req("PATCH", f"/people/{parent_user_id}/{pid}", {
        "birth_location": None,
        "birth_location_accuracy": "unknown",
        "timezone": "+08:00",
    })
    assert s >= 400, f"Expected rejection of fixed-offset tz, got {s} body={body}"


def test_patch_saved_person_coord_change_overrides_client_tz(parent_user_id):
    """If both coords and a (wrong) client tz are PATCHed together,
    coordinates win."""
    create = {
        "name": _unique_name("SP_BOTH"),
        "relationship_type": "friend",
        "birth_date": "1990-05-10",
        "birth_time": "06:00",
        "birth_time_accuracy": "exact",
        "birth_location": {
            "city": "Kuala Lumpur", "country": "Malaysia",
            "latitude": 3.139, "longitude": 101.6869,
        },
        "birth_location_accuracy": "exact",
        "timezone": "Asia/Kuala_Lumpur",
    }
    s, body = _req("POST", f"/people/{parent_user_id}", create)
    assert s == 200
    pid = body["id"]
    _CREATED_SAVED.append((parent_user_id, pid))

    s, body = _req("PATCH", f"/people/{parent_user_id}/{pid}", {
        "birth_location": {
            "city": "New York", "country": "United States",
            "latitude": 40.7128, "longitude": -74.0060,
        },
        "timezone": "+08:00",
    })
    assert s == 200, body
    assert body["timezone"] == "America/New_York"
    assert body["timezone_source"] == "coordinates"


# ---------------------------------------------------------------------------
# Teardown
# ---------------------------------------------------------------------------

def teardown_module(_module):
    """Best-effort cleanup of isolated test rows."""
    import asyncio
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv()

    async def run():
        cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = cli[os.environ.get("DB_NAME", "test_database")]
        if _CREATED_USERS:
            await db.users.delete_many(
                {"_id": {"$in": [ObjectId(u) for u in _CREATED_USERS]}}
            )
        if _CREATED_SAVED:
            await db.saved_people.delete_many({
                "user_id": {"$in": list({u for u, _ in _CREATED_SAVED})}
            })

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run())
        loop.close()
    except Exception:
        pass
