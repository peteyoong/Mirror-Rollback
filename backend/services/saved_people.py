"""
Saved People — persistence + validation for relationship subjects
==================================================================

Stores structured records for the people in a user's life so that:
  • Pattern recurrence can be keyed against a stable identity.
  • Astrology / Human Design / relationship insights can be applied
    when birth data is sufficient, with explicit confidence degradation
    when it is not.

Data contract
-------------
At creation, the following are REQUIRED:
  - name              (string, 1-120 chars)
  - relationship_type (string, must be one of RELATIONSHIP_TYPES)
  - birth_date        (string YYYY-MM-DD)

Two fields are decision fields — must be EITHER provided OR
EXPLICITLY marked unknown via an accuracy flag. Silent nulls are
rejected:
  - birth_time          (HH:MM, nullable) +
    birth_time_accuracy ("exact" | "unknown")
  - birth_location      ({city, country, latitude?, longitude?},
                         nullable) +
    birth_location_accuracy ("exact" | "unknown")

The `*_accuracy` field is the source of truth for downstream services
when degrading precision (e.g. astrology charts that require an exact
birth time produce a "low confidence" variant when accuracy is
"unknown" rather than failing silently).

Public router: `saved_people_router` — mount under /api inside server.py.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Accepted relationship types. Kept open-ended ("other") so users can
# fall back gracefully, but the closed list keeps the recurrence engine
# from drifting.
RELATIONSHIP_TYPES = {
    "partner", "spouse", "ex_partner",
    "parent", "child", "sibling",
    "family_other",
    "friend", "close_friend",
    "colleague", "boss", "report", "client",
    "mentor", "mentee",
    "other",
}

ACCURACY_VALUES = {"exact", "unknown"}

# UX copy surfaced by the form — single source of truth for the
# microcopy so frontend/backend can't drift.
UX_COPY = {
    "birth_details_hint": (
        "Birth details improve precision. You can mark as unknown and "
        "update later."
    ),
}

# YYYY-MM-DD validator
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# HH:MM validator (24h)
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SavedPersonLocation(BaseModel):
    """Birth location. Coordinates optional — geocoding can fill them."""
    city:      str = Field(min_length=1, max_length=120)
    country:   str = Field(min_length=1, max_length=120)
    latitude:  Optional[float] = None
    longitude: Optional[float] = None


class SavedPersonCreate(BaseModel):
    """Payload for POST /api/people/{user_id}."""
    # --- required at creation ---------------------------------------------
    name: str = Field(min_length=1, max_length=120)
    relationship_type: str
    birth_date: str  # YYYY-MM-DD

    # --- decision fields (must satisfy accuracy contract) -----------------
    birth_time: Optional[str] = None
    birth_time_accuracy: str   # "exact" | "unknown"

    birth_location: Optional[SavedPersonLocation] = None
    birth_location_accuracy: str  # "exact" | "unknown"

    # --- optional metadata ------------------------------------------------
    notes:    Optional[str] = Field(default=None, max_length=2000)
    timezone: Optional[str] = None      # "+07:30" or IANA — used when
                                        # birth_time is exact

    # --- v0.1 Relationship Profile enhancements (May 2026) ---------------
    # Optional. NEVER required to save. Storing these unlocks deeper
    # numerology / typology synthesis on the Profile page.
    full_birth_name:   Optional[str] = Field(default=None, max_length=200)
    enneagram_type:    Optional[str] = Field(default=None, max_length=10)
    enneagram_source:  Optional[str] = Field(default=None, max_length=20)

    # ---- validators ------------------------------------------------------

    @field_validator("relationship_type")
    @classmethod
    def _valid_relationship_type(cls, v: str) -> str:
        v_norm = (v or "").strip().lower()
        if v_norm not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"relationship_type must be one of "
                f"{sorted(RELATIONSHIP_TYPES)}; got {v!r}"
            )
        return v_norm

    @field_validator("birth_date")
    @classmethod
    def _valid_birth_date(cls, v: str) -> str:
        v_str = (v or "").strip()
        if not _DATE_RE.match(v_str):
            raise ValueError("birth_date must be YYYY-MM-DD")
        try:
            datetime.strptime(v_str, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"birth_date is not a valid calendar date: {e}")
        return v_str

    @field_validator("birth_time")
    @classmethod
    def _valid_birth_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not _TIME_RE.match(s):
            raise ValueError("birth_time must be HH:MM (24h)")
        return s

    @field_validator("birth_time_accuracy", "birth_location_accuracy")
    @classmethod
    def _valid_accuracy(cls, v: str) -> str:
        s = (v or "").strip().lower()
        if s not in ACCURACY_VALUES:
            raise ValueError(
                f"accuracy must be one of {sorted(ACCURACY_VALUES)}; got {v!r}"
            )
        return s

    @model_validator(mode="after")
    def _enforce_accuracy_contract(self) -> "SavedPersonCreate":
        """Reject silent nulls. Accept null only if accuracy is 'unknown'."""
        # Birth time
        if self.birth_time_accuracy == "exact":
            if not self.birth_time:
                raise ValueError(
                    "birth_time is required when birth_time_accuracy is "
                    "'exact'. Set birth_time_accuracy='unknown' to skip."
                )
        elif self.birth_time_accuracy == "unknown":
            # Allow either None (preferred) or a stored value, but the
            # source of truth for downstream is the accuracy flag.
            pass
        # Birth location
        if self.birth_location_accuracy == "exact":
            if not self.birth_location:
                raise ValueError(
                    "birth_location is required when "
                    "birth_location_accuracy is 'exact'. Set "
                    "birth_location_accuracy='unknown' to skip."
                )
        return self


class SavedPersonUpdate(BaseModel):
    """Partial PATCH. All fields optional — but if accuracy is updated,
    the value contract still applies to the fields supplied."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    relationship_type: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_time_accuracy: Optional[str] = None
    birth_location: Optional[SavedPersonLocation] = None
    birth_location_accuracy: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    timezone: Optional[str] = None
    # v0.1 Relationship Profile enhancements — see SavedPersonCreate.
    full_birth_name:   Optional[str] = Field(default=None, max_length=200)
    enneagram_type:    Optional[str] = Field(default=None, max_length=10)
    enneagram_source:  Optional[str] = Field(default=None, max_length=20)

    @field_validator("relationship_type")
    @classmethod
    def _valid_relationship_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip().lower()
        if s not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"relationship_type must be one of "
                f"{sorted(RELATIONSHIP_TYPES)}"
            )
        return s

    @field_validator("birth_date")
    @classmethod
    def _valid_birth_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not _DATE_RE.match(s):
            raise ValueError("birth_date must be YYYY-MM-DD")
        return s

    @field_validator("birth_time")
    @classmethod
    def _valid_birth_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not _TIME_RE.match(s):
            raise ValueError("birth_time must be HH:MM (24h)")
        return s

    @field_validator("birth_time_accuracy", "birth_location_accuracy")
    @classmethod
    def _valid_accuracy(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip().lower()
        if s not in ACCURACY_VALUES:
            raise ValueError(
                f"accuracy must be one of {sorted(ACCURACY_VALUES)}"
            )
        return s


class SavedPersonResponse(BaseModel):
    id: str
    user_id: str
    name: str
    relationship_type: str
    birth_date: str
    birth_time: Optional[str]
    birth_time_accuracy: str
    birth_location: Optional[SavedPersonLocation]
    birth_location_accuracy: str
    notes: Optional[str]
    timezone: Optional[str]
    created_at: str
    updated_at: str
    # Derived: callers can use this to surface "needs more info" hints
    # without re-deriving the rule.
    precision_level: str   # "high" | "medium" | "low"
    # v0.1 Relationship Profile enhancements
    full_birth_name:  Optional[str] = None
    enneagram_type:   Optional[str] = None
    enneagram_source: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_precision_level(doc: Dict[str, Any]) -> str:
    """
    Quick rule for downstream services:
      - high   = both birth_time + birth_location accuracy 'exact'
      - medium = exactly one is 'exact'
      - low    = both 'unknown'
    Astrology / Human Design lenses can use this to degrade gracefully
    while still allowing the core relationship insight to run.
    """
    bta = doc.get("birth_time_accuracy") == "exact"
    bla = doc.get("birth_location_accuracy") == "exact"
    if bta and bla:
        return "high"
    if bta or bla:
        return "medium"
    return "low"


def _serialise(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Mongo doc to the response shape (safe for JSON return)."""
    bl = doc.get("birth_location")
    out = {
        "id":                       doc["id"],
        "user_id":                  doc["user_id"],
        "name":                     doc["name"],
        "relationship_type":        doc["relationship_type"],
        "birth_date":               doc.get("birth_date"),
        "birth_time":               doc.get("birth_time"),
        "birth_time_accuracy":      doc.get("birth_time_accuracy", "unknown"),
        "birth_location":           bl if isinstance(bl, dict) else None,
        "birth_location_accuracy":  doc.get("birth_location_accuracy", "unknown"),
        "notes":                    doc.get("notes"),
        "timezone":                 doc.get("timezone"),
        "full_birth_name":          doc.get("full_birth_name"),
        "enneagram_type":           doc.get("enneagram_type"),
        "enneagram_source":         doc.get("enneagram_source"),
        "created_at": (
            doc["created_at"].isoformat()
            if isinstance(doc.get("created_at"), datetime)
            else doc.get("created_at", "")
        ),
        "updated_at": (
            doc["updated_at"].isoformat()
            if isinstance(doc.get("updated_at"), datetime)
            else doc.get("updated_at", "")
        ),
        "precision_level": _compute_precision_level(doc),
    }
    return out


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def build_saved_people_router(db) -> APIRouter:  # noqa: ANN001 — db is Motor handle
    """
    Build the FastAPI router for saved-people CRUD. Takes the active
    Motor `db` so server.py can share the same DB handle.
    """
    router = APIRouter()

    @router.get("/people/meta")
    async def get_saved_people_meta() -> Dict[str, Any]:
        """Static metadata: relationship types + UX copy. Lets the
        frontend keep the form options aligned with the backend."""
        return {
            "relationship_types": sorted(RELATIONSHIP_TYPES),
            "accuracy_values":    sorted(ACCURACY_VALUES),
            "ux_copy":            UX_COPY,
        }

    @router.post("/people/{user_id}", response_model=SavedPersonResponse)
    async def create_saved_person(
        user_id: str, body: SavedPersonCreate,
    ) -> Dict[str, Any]:
        """Create a saved person for the given user."""
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="user_id is required")

        now = datetime.now(timezone.utc)
        doc: Dict[str, Any] = {
            "id":                       str(uuid.uuid4()),
            "user_id":                  user_id.strip(),
            "name":                     body.name.strip(),
            "relationship_type":        body.relationship_type,
            "birth_date":               body.birth_date,
            "birth_time":               body.birth_time,
            "birth_time_accuracy":      body.birth_time_accuracy,
            "birth_location": (
                body.birth_location.model_dump()
                if body.birth_location else None
            ),
            "birth_location_accuracy":  body.birth_location_accuracy,
            "notes":                    (body.notes or None),
            "timezone":                 (body.timezone or None),
            "created_at":               now,
            "updated_at":               now,
        }
        await db.saved_people.insert_one(doc)
        logger.info(
            "[SavedPeople] created person=%s user=%s precision=%s",
            doc["id"], user_id, _compute_precision_level(doc),
        )
        return _serialise(doc)

    @router.get("/people/{user_id}")
    async def list_saved_people(user_id: str) -> Dict[str, Any]:
        """List all people saved by a user, newest first."""
        cursor = db.saved_people.find(
            {"user_id": user_id.strip()},
        ).sort("created_at", -1)
        rows = await cursor.to_list(length=500)
        return {
            "people": [_serialise(r) for r in rows],
            "count":  len(rows),
        }

    @router.get(
        "/people/{user_id}/{person_id}",
        response_model=SavedPersonResponse,
    )
    async def get_saved_person(
        user_id: str, person_id: str,
    ) -> Dict[str, Any]:
        doc = await db.saved_people.find_one({
            "user_id": user_id.strip(), "id": person_id.strip(),
        })
        if not doc:
            raise HTTPException(status_code=404, detail="Person not found")
        return _serialise(doc)

    @router.patch(
        "/people/{user_id}/{person_id}",
        response_model=SavedPersonResponse,
    )
    async def update_saved_person(
        user_id: str, person_id: str, body: SavedPersonUpdate,
    ) -> Dict[str, Any]:
        existing = await db.saved_people.find_one({
            "user_id": user_id.strip(), "id": person_id.strip(),
        })
        if not existing:
            raise HTTPException(status_code=404, detail="Person not found")

        # Apply patch in-memory so we can re-validate the accuracy
        # contract holistically (e.g. flipping accuracy="exact" while
        # the value stays None is rejected).
        merged = dict(existing)
        update_payload = body.model_dump(exclude_unset=True)
        if "birth_location" in update_payload and update_payload["birth_location"] is not None:
            # Pydantic returned a dict already
            merged["birth_location"] = update_payload["birth_location"]
        elif "birth_location" in update_payload:
            merged["birth_location"] = None
        for k, v in update_payload.items():
            if k == "birth_location":
                continue
            merged[k] = v

        # Re-enforce contract
        bta = merged.get("birth_time_accuracy")
        bla = merged.get("birth_location_accuracy")
        if bta == "exact" and not merged.get("birth_time"):
            raise HTTPException(
                status_code=400,
                detail="birth_time is required when birth_time_accuracy is 'exact'.",
            )
        if bla == "exact" and not merged.get("birth_location"):
            raise HTTPException(
                status_code=400,
                detail="birth_location is required when birth_location_accuracy is 'exact'.",
            )

        merged["updated_at"] = datetime.now(timezone.utc)
        await db.saved_people.update_one(
            {"_id": existing["_id"]},
            {"$set": {k: v for k, v in merged.items() if k != "_id"}},
        )
        return _serialise(merged)

    @router.delete("/people/{user_id}/{person_id}")
    async def delete_saved_person(
        user_id: str, person_id: str,
    ) -> Dict[str, Any]:
        result = await db.saved_people.delete_one({
            "user_id": user_id.strip(), "id": person_id.strip(),
        })
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Person not found")
        return {"ok": True, "deleted_id": person_id.strip()}

    return router


__all__ = [
    "RELATIONSHIP_TYPES",
    "ACCURACY_VALUES",
    "UX_COPY",
    "SavedPersonCreate",
    "SavedPersonUpdate",
    "SavedPersonResponse",
    "SavedPersonLocation",
    "build_saved_people_router",
    "_compute_precision_level",
]
