"""
Astrology Lookup Router
=======================
Build marker: astro-chat-transit-grounding-v1

Single-object transit lookup endpoint used by:
  - Astrology Lens Chat (server-side orchestration)
  - Anyone else needing factual transit data for a single body

Routes:
  GET /api/astrology/transit-object/{user_id}
      ?object=Chiron
      &date=YYYY-MM-DD            (optional, defaults to today UTC)

Response shape: see services.transit_object_engine module docstring.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.transit_object_engine import (
    BUILD_MARKER,
    SUPPORTED_OBJECTS,
    compute_transit_object,
    resolve_object_name,
)

logger = logging.getLogger(__name__)


def register_astrology_lookup_routes(api_router: APIRouter, db) -> None:
    """Attach the transit-object endpoint to the given api_router."""

    @api_router.get("/astrology/transit-object/{user_id}")
    async def get_transit_object(
        user_id: str,
        object: str,                                # noqa: A002 - matches spec
        date: Optional[str] = None,
    ):
        """Deterministic transit position + aspects-to-natal for one body."""
        if not object:
            raise HTTPException(status_code=400, detail="object parameter required")

        canonical = resolve_object_name(object)
        if canonical is None:
            return JSONResponse(
                content={
                    "success":   False,
                    "data_mode": "transit_object",
                    "reason":    "unknown_object",
                    "requested": object,
                    "supported": SUPPORTED_OBJECTS,
                },
                headers={"Cache-Control": "no-store"},
            )

        # Resolve chart (try ObjectId then string id)
        chart = None
        if ObjectId.is_valid(user_id):
            chart = await db.charts.find_one({"user_id": str(user_id)})
        if chart is None:
            chart = await db.charts.find_one({"user_id": user_id})
        if chart is None:
            raise HTTPException(status_code=404, detail="chart not found for user")

        # Parse date if provided
        target_dt: Optional[datetime] = None
        if date:
            try:
                target_dt = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

        envelope = compute_transit_object(
            chart=chart,
            object_name=object,
            date=target_dt,
        )
        envelope["build_marker"] = BUILD_MARKER
        logger.info(
            f"[TransitLookup] user={user_id[:8]}... object={canonical} "
            f"success={envelope.get('success')} reason={envelope.get('reason')}"
        )
        return JSONResponse(content=envelope, headers={"Cache-Control": "no-store"})
