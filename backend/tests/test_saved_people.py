"""
Audit tests for services/saved_people.py
=========================================

Validates the persistence contract:
  1. Required-at-creation: name + relationship_type + birth_date.
  2. Decision-field contract (silent nulls REJECTED):
     - birth_time + birth_time_accuracy
     - birth_location + birth_location_accuracy
     - null only allowed when accuracy="unknown"
  3. Patch updates re-enforce the contract.
  4. Precision level computed correctly.
  5. CRUD over the live FastAPI router (in-memory async client).

Notes
-----
Endpoint tests run a TestClient against the actual app + a Motor handle
to the configured Mongo DB. Records are written to a one-off collection
namespace and cleaned up at end of session.
"""

import os
import sys
import uuid
from pathlib import Path

import pytest

# Ensure the backend dir is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.saved_people import (  # noqa: E402
    ACCURACY_VALUES,
    RELATIONSHIP_TYPES,
    SavedPersonCreate,
    SavedPersonUpdate,
    _compute_precision_level,
)


# ---------------------------------------------------------------------------
# Pure model validation tests
# ---------------------------------------------------------------------------

def _good_payload(**overrides):
    base = {
        "name": "Alex",
        "relationship_type": "partner",
        "birth_date": "1990-04-15",
        "birth_time": "14:30",
        "birth_time_accuracy": "exact",
        "birth_location": {
            "city": "Singapore",
            "country": "Singapore",
            "latitude": 1.3521,
            "longitude": 103.8198,
        },
        "birth_location_accuracy": "exact",
    }
    base.update(overrides)
    return base


def test_required_fields_at_creation():
    # Missing name
    with pytest.raises(Exception):
        SavedPersonCreate(**{k: v for k, v in _good_payload().items() if k != "name"})
    # Missing relationship_type
    with pytest.raises(Exception):
        SavedPersonCreate(**{k: v for k, v in _good_payload().items() if k != "relationship_type"})
    # Missing birth_date
    with pytest.raises(Exception):
        SavedPersonCreate(**{k: v for k, v in _good_payload().items() if k != "birth_date"})


def test_relationship_type_must_be_in_allowed_set():
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(relationship_type="enemy"))
    # Case-insensitive accepted
    p = SavedPersonCreate(**_good_payload(relationship_type="Partner"))
    assert p.relationship_type == "partner"


def test_birth_date_must_be_iso_calendar_date():
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(birth_date="15/04/1990"))
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(birth_date="1990-13-15"))  # invalid month
    # Valid YYYY-MM-DD passes
    p = SavedPersonCreate(**_good_payload(birth_date="1990-04-15"))
    assert p.birth_date == "1990-04-15"


def test_silent_null_birth_time_rejected_when_accuracy_exact():
    with pytest.raises(Exception) as exc:
        SavedPersonCreate(**_good_payload(birth_time=None, birth_time_accuracy="exact"))
    assert "birth_time" in str(exc.value).lower()


def test_unknown_accuracy_allows_null_birth_time():
    p = SavedPersonCreate(**_good_payload(
        birth_time=None, birth_time_accuracy="unknown",
    ))
    assert p.birth_time is None
    assert p.birth_time_accuracy == "unknown"


def test_silent_null_birth_location_rejected_when_accuracy_exact():
    with pytest.raises(Exception) as exc:
        SavedPersonCreate(**_good_payload(
            birth_location=None, birth_location_accuracy="exact",
        ))
    assert "birth_location" in str(exc.value).lower()


def test_unknown_accuracy_allows_null_birth_location():
    p = SavedPersonCreate(**_good_payload(
        birth_location=None, birth_location_accuracy="unknown",
    ))
    assert p.birth_location is None
    assert p.birth_location_accuracy == "unknown"


def test_invalid_accuracy_value_rejected():
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(birth_time_accuracy="approximate"))
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(birth_location_accuracy="rough"))


def test_birth_time_format_must_be_24h_hhmm():
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(birth_time="2:30 pm"))
    with pytest.raises(Exception):
        SavedPersonCreate(**_good_payload(birth_time="25:00"))


def test_precision_level_high_when_both_exact():
    p = SavedPersonCreate(**_good_payload())
    doc = p.model_dump()
    doc["birth_location"] = doc["birth_location"]
    assert _compute_precision_level(doc) == "high"


def test_precision_level_medium_when_one_unknown():
    p = SavedPersonCreate(**_good_payload(
        birth_time=None, birth_time_accuracy="unknown",
    ))
    doc = p.model_dump()
    assert _compute_precision_level(doc) == "medium"


def test_precision_level_low_when_both_unknown():
    p = SavedPersonCreate(**_good_payload(
        birth_time=None, birth_time_accuracy="unknown",
        birth_location=None, birth_location_accuracy="unknown",
    ))
    doc = p.model_dump()
    assert _compute_precision_level(doc) == "low"


def test_update_model_partial_fields_validate():
    # Invalid relationship_type still rejected on PATCH
    with pytest.raises(Exception):
        SavedPersonUpdate(relationship_type="enemy")
    # Invalid accuracy still rejected on PATCH
    with pytest.raises(Exception):
        SavedPersonUpdate(birth_time_accuracy="approximate")
    # Empty patch is fine
    p = SavedPersonUpdate()
    assert p.model_dump(exclude_unset=True) == {}


def test_relationship_types_set_includes_canonical():
    expected = {"partner", "spouse", "ex_partner", "parent", "child",
                "sibling", "family_other", "friend", "close_friend",
                "colleague", "boss", "report", "client", "mentor",
                "mentee", "other"}
    assert expected == RELATIONSHIP_TYPES


def test_accuracy_values_canonical():
    assert ACCURACY_VALUES == {"exact", "unknown"}


# ---------------------------------------------------------------------------
# Endpoint integration tests (requires DB)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Spin up an httpx ASGI client against the real FastAPI app."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("MONGO_URL") or not os.environ.get("DB_NAME"):
        pytest.skip("MONGO_URL / DB_NAME not configured for endpoint tests")
    # Import server to register routes
    import server  # noqa: F401  pylint: disable=import-error
    from fastapi.testclient import TestClient
    return TestClient(server.app)


@pytest.fixture(scope="module")
def test_user_id():
    return f"test_saved_people_user_{uuid.uuid4().hex[:8]}"


def test_endpoint_meta(client):
    r = client.get("/api/people/meta")
    assert r.status_code == 200
    body = r.json()
    assert "relationship_types" in body
    assert body["ux_copy"]["birth_details_hint"].startswith("Birth details")


def test_endpoint_full_crud(client, test_user_id):
    # CREATE — full data
    payload = _good_payload(name="Test Pat", relationship_type="friend")
    r = client.post(f"/api/people/{test_user_id}", json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    pid = created["id"]
    assert created["name"] == "Test Pat"
    assert created["precision_level"] == "high"

    try:
        # GET single
        r = client.get(f"/api/people/{test_user_id}/{pid}")
        assert r.status_code == 200
        assert r.json()["name"] == "Test Pat"

        # LIST
        r = client.get(f"/api/people/{test_user_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 1
        assert any(p["id"] == pid for p in body["people"])

        # PATCH — flip birth_location to unknown (must not require value)
        r = client.patch(
            f"/api/people/{test_user_id}/{pid}",
            json={"birth_location": None, "birth_location_accuracy": "unknown"},
        )
        assert r.status_code == 200, r.text
        updated = r.json()
        assert updated["birth_location"] is None
        assert updated["birth_location_accuracy"] == "unknown"
        assert updated["precision_level"] == "medium"

        # PATCH — try to set accuracy=exact while clearing the value:
        # must be rejected (silent null guard at update time).
        r = client.patch(
            f"/api/people/{test_user_id}/{pid}",
            json={"birth_location": None, "birth_location_accuracy": "exact"},
        )
        assert r.status_code == 400, r.text

    finally:
        # DELETE — cleanup
        r = client.delete(f"/api/people/{test_user_id}/{pid}")
        assert r.status_code in (200, 404)


def test_endpoint_rejects_silent_null_at_create(client, test_user_id):
    """Reject a payload that nulls birth_time without flagging it unknown."""
    bad = _good_payload(
        name="Test Bad", birth_time=None, birth_time_accuracy="exact",
    )
    r = client.post(f"/api/people/{test_user_id}", json=bad)
    assert r.status_code == 422, r.text


def test_endpoint_accepts_unknown_at_create(client, test_user_id):
    """Accept a payload that skips both birth_time and birth_location
    via the unknown accuracy flag."""
    payload = _good_payload(
        name="Test Unknown",
        birth_time=None, birth_time_accuracy="unknown",
        birth_location=None, birth_location_accuracy="unknown",
    )
    r = client.post(f"/api/people/{test_user_id}", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["birth_time"] is None
    assert body["birth_location"] is None
    assert body["precision_level"] == "low"
    # Cleanup
    client.delete(f"/api/people/{test_user_id}/{body['id']}")
