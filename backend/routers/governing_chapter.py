"""
Governing Chapter Router — Timeline V2 / Phase Architecture
============================================================
Build marker: phase-architecture-v1a

Single endpoint:
  GET /api/timeline/governing-chapter/{user_id}?force_refresh=false

Returns the user's current Governing Life Chapter — the 3-9 month phase
that becomes the gravitational center of the new Timeline V2.

Response shape: see services.phase_governor.resolve_governing_chapter().
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.phase_governor import resolve_governing_chapter

logger = logging.getLogger(__name__)


def register_governing_chapter_routes(api_router: APIRouter, db) -> None:
    @api_router.get("/timeline/governing-chapter/{user_id}")
    async def get_governing_chapter(
        user_id: str,
        force_refresh: bool = False,
    ) -> JSONResponse:
        payload = await resolve_governing_chapter(
            db, user_id, force_refresh=force_refresh,
        )
        if payload is None:
            raise HTTPException(status_code=404, detail="chart not found for user")

        logger.info(
            f"[GoverningChapter] user={user_id[:8]}... "
            f"chapter={payload.get('chapter', {}).get('chapter_id')} "
            f"mode={payload.get('selection_mode')} "
            f"from_cache={payload.get('from_cache')}"
        )

        return JSONResponse(
            content={"success": True, **payload},
            headers={"Cache-Control": "no-store, max-age=0"},
        )
