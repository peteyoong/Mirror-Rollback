"""
Pattern Running Me V2 routes  (server-router-refactor-v5)
==========================================================

Behaviour-preserving extraction of the pattern-running-me-v2 surface.
All schemas, helpers, side-effects (pattern_memory_signals +
forum_field_signals inserts) and response shapes match the inline
implementation byte-for-byte.

Endpoints attached:

    GET   /api/pattern-running-me/emotions
    POST  /api/pattern-running-me?user_id=...
    GET   /api/pattern-running-me/user/{user_id}

All dependencies live inside `services.pattern_running_me_v2`, so this
router has no upward import on server.py module state.

Call signature:

    pattern_running_me.register(api_router, db, logger)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from services.pattern_running_me_v2 import (
    PatternRunningMePayload as _PRPayload,
    ALLOWED_EMOTIONS as _PR_ALLOWED_EMOTIONS,
    build_storage_document as _pr_build_doc,
    build_pattern_memory_signal as _pr_memory_signal,
    build_forum_field_signal as _pr_forum_signal,
)


def register(api_router: APIRouter, db, logger) -> None:

    @api_router.get("/pattern-running-me/emotions")
    async def pattern_running_me_emotions():
        """Return the canonical, ordered vocabulary of emotion chips."""
        return {"emotions": _PR_ALLOWED_EMOTIONS}

    @api_router.post("/pattern-running-me")
    async def create_pattern_running_me(
        payload: _PRPayload,
        user_id: str,
    ):
        """Persist a Pattern Running Me V2 entry. See services/pattern_running_me_v2.py."""
        if payload.forum_id:
            membership = await db.forum_members.find_one(
                {"forum_id": payload.forum_id, "user_id": user_id, "status": "active"}
            )
            if not membership:
                raise HTTPException(status_code=403, detail="Not a member of this forum")

        doc = _pr_build_doc(user_id, payload)
        res = await db.pattern_running_me_v2.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        doc["id"] = str(res.inserted_id)

        try:
            await db.pattern_memory_signals.insert_one(_pr_memory_signal(doc))
        except Exception as e:
            logger.warning(f"[PRPattern] memory signal failed: {e}")

        try:
            forum_signal = _pr_forum_signal(doc)
            if forum_signal:
                await db.forum_field_signals.insert_one(forum_signal)
        except Exception as e:
            logger.warning(f"[PRPattern] forum signal failed: {e}")

        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if isinstance(doc.get("updated_at"), datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        return doc

    @api_router.get("/pattern-running-me/user/{user_id}")
    async def list_pattern_running_me(
        user_id: str,
        limit: int = 20,
        forum_id: Optional[str] = None,
    ):
        """List a user's recent Pattern Running Me V2 entries."""
        query: Dict[str, Any] = {"user_id": str(user_id)}
        if forum_id:
            query["forum_id"] = forum_id
        cursor = db.pattern_running_me_v2.find(query).sort("created_at", -1).limit(limit)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            if isinstance(doc.get("created_at"), datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            if isinstance(doc.get("updated_at"), datetime):
                doc["updated_at"] = doc["updated_at"].isoformat()
            items.append(doc)
        return {"items": items}
