"""
Micro-Reflection routes  (server-router-refactor-v2)
=====================================================

Extracted from server.py.  Behavior, paths, schemas, markers and log
lines are byte-identical to the original inline implementation.

Endpoints:

    POST  /api/micro-reflection                              # v2 single tap
    GET   /api/micro-reflection/{user_id}/recent             # v2 history+summary

    POST  /api/micro-reflection/home-texture                 # v3 home check-in
    GET   /api/micro-reflection/{user_id}/home-texture/today # v3 daily lookup

Call `register(api_router, db, logger)` from `server.py`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# Domain whitelist for v3 Home texture taps.  None is allowed.
_HOME_TEXTURE_DOMAINS = {
    "work", "relationships", "self", "family", "forum", "not_sure", None,
}


class MicroReflectionCreate(BaseModel):
    """Single tap from a chat surface (v2)."""
    user_id: str
    label: str
    source: str = "other"
    texture: Optional[str] = None
    source_session: Optional[str] = None
    source_message: Optional[str] = None
    context_pattern_keys: Optional[List[str]] = None
    context_lens: Optional[str] = None
    context_life_domain: Optional[str] = None
    context_about_person_id: Optional[str] = None


class HomeTextureCheckIn(BaseModel):
    """Single home-tab texture tap (v3)."""
    user_id: str
    texture: str
    domain: Optional[str] = None


def register(api_router: APIRouter, db, logger) -> None:
    """
    Attach the 4 micro-reflection endpoints onto `api_router`.

    Markers preserved:
      - micro-reflection-v2
      - micro-reflection-v3-home-texture
    """

    # ──────────────────────────────────────────────────────────────────
    # v2 — single tap
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/micro-reflection")
    async def create_micro_reflection(body: MicroReflectionCreate):
        from services.micro_reflection_v2 import (
            record_reflection,
            is_valid_label,
            is_valid_texture,
            valid_labels,
            valid_textures,
        )
        if not is_valid_label(body.label):
            raise HTTPException(
                status_code=400,
                detail=f"invalid label; allowed: {valid_labels()}",
            )
        if not is_valid_texture(body.texture):
            raise HTTPException(
                status_code=400,
                detail=f"invalid texture; allowed: {valid_textures()} or null",
            )
        try:
            doc = await record_reflection(
                db=db,
                user_id=body.user_id,
                label=body.label,
                source=body.source,
                texture=body.texture,
                source_session=body.source_session,
                source_message=body.source_message,
                context_pattern_keys=body.context_pattern_keys,
                context_lens=body.context_lens,
                context_life_domain=body.context_life_domain,
                context_about_person_id=body.context_about_person_id,
            )
            logger.info(
                f"[MICRO_REFLECTION_V2] user={body.user_id} label={body.label} "
                f"texture={body.texture} source={body.source}"
            )
            if isinstance(doc.get("ts"), datetime):
                doc["ts"] = doc["ts"].isoformat()
            return {"ok": True, "reflection": doc, "marker": "micro-reflection-v2"}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"[MICRO_REFLECTION_V2] error recording: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail="micro-reflection storage failed")

    @api_router.get("/micro-reflection/{user_id}/recent")
    async def get_micro_reflections(user_id: str, limit: int = 50):
        from services.micro_reflection_v2 import get_recent_reflections, analyze_recent
        rows = await get_recent_reflections(db, user_id=user_id, limit=limit)
        summary = await analyze_recent(db, user_id=user_id)
        return {
            "marker": "micro-reflection-v2",
            "user_id": user_id,
            "reflections": rows,
            "summary": summary,
        }

    # ──────────────────────────────────────────────────────────────────
    # v3 — Home daily texture check-in
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/micro-reflection/home-texture")
    async def create_home_texture(body: HomeTextureCheckIn):
        from services.micro_reflection_v2 import (
            record_reflection,
            is_valid_texture,
            valid_textures,
        )
        if not is_valid_texture(body.texture):
            raise HTTPException(
                status_code=400,
                detail=f"invalid texture; allowed: {valid_textures()}",
            )
        if body.domain is not None and body.domain not in _HOME_TEXTURE_DOMAINS:
            raise HTTPException(
                status_code=400,
                detail=f"invalid domain; allowed: {sorted([d for d in _HOME_TEXTURE_DOMAINS if d])} or null",
            )
        try:
            domain_to_store = body.domain if body.domain not in (None, "not_sure") else None
            doc = await record_reflection(
                db=db,
                user_id=body.user_id,
                label="true_lately",
                source="home_texture",
                texture=body.texture,
                context_life_domain=domain_to_store,
            )
            logger.info(
                f"[MICRO_REFLECTION_V3] user={body.user_id} "
                f"texture={body.texture} domain={domain_to_store} source=home_texture"
            )
            if isinstance(doc.get("ts"), datetime):
                doc["ts"] = doc["ts"].isoformat()
            return {
                "ok": True,
                "reflection": doc,
                "marker": "micro-reflection-v3-home-texture",
            }
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(
                f"[MICRO_REFLECTION_V3] error recording: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail="home-texture storage failed",
            )

    @api_router.get("/micro-reflection/{user_id}/home-texture/today")
    async def get_home_texture_today(user_id: str):
        try:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            row = await db.micro_reflections.find_one({
                "user_id": user_id,
                "source": "home_texture",
                "ts": {"$gte": start},
            }, sort=[("ts", -1)])
            if not row:
                return {
                    "marker": "micro-reflection-v3-home-texture",
                    "user_id": user_id,
                    "logged_today": False,
                    "last": None,
                }
            row.pop("_id", None)
            ts = row.get("ts")
            if isinstance(ts, datetime):
                row["ts"] = ts.isoformat()
            return {
                "marker": "micro-reflection-v3-home-texture",
                "user_id": user_id,
                "logged_today": True,
                "last": {
                    "texture": row.get("texture"),
                    "domain": row.get("context_life_domain"),
                    "ts": row.get("ts"),
                },
            }
        except Exception as e:
            logger.error(
                f"[MICRO_REFLECTION_V3] today fetch error: {type(e).__name__}: {e}"
            )
            return {
                "marker": "micro-reflection-v3-home-texture",
                "user_id": user_id,
                "logged_today": False,
                "last": None,
            }
