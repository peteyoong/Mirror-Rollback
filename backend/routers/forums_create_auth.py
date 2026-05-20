"""
Forums Create + Auth routes  (server-router-refactor-v5)
=========================================================

Behaviour-preserving extraction of:

    POST /api/forums/login   — same response shape as /users/login;
                                provided to bypass CDN cached errors
                                on the /users path.
    POST /api/forums         — multi-mode handler:
                                (a) if body has `get_mappings`, returns
                                forum-member mappings;
                                (b) otherwise creates a forum + owner
                                membership + the default "The Pattern
                                Running Me" exercise.

`generate_invite_token` moves here (it is used only by this surface).

Two server.py-level dependencies are passed in via register() so we
avoid circular imports:
    login_user_fn  : async fn(LoginRequest) -> Any
    LoginRequest_cls : pydantic model class
    ForumCreate_cls : pydantic model class

Call signature:

    forums_create_auth.register(
        api_router, db, logger,
        login_user_fn, LoginRequest_cls, ForumCreate_cls,
    )
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request


def generate_invite_token() -> str:
    """Generate a unique invite token for a forum."""
    return hashlib.sha256(
        f"{uuid.uuid4()}{datetime.now(timezone.utc).isoformat()}".encode()
    ).hexdigest()[:12]


def register(
    api_router: APIRouter,
    db,
    logger,
    login_user_fn,
    LoginRequest_cls,
    ForumCreate_cls,
) -> None:

    # ──────────────────────────────────────────────────────────────────
    # POST /api/forums/login
    # Login handler via /forums path — bypasses CDN cached errors on
    # /api/users/login.  Reuses login_user_fn passed in.
    # Note: `LoginRequest_cls` is bound via the register() closure, so
    # the FastAPI route signature uses `Request` and we construct the
    # pydantic model manually — this preserves identical request/
    # response shape with the inline implementation.
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/forums/login")
    async def forums_login_handler(request: Request):
        """Login handler accessible via /api/forums/login — bypasses CDN cached errors on /api/users/login."""
        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            login_req = LoginRequest_cls(**body)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
        return await login_user_fn(login_req)

    # ──────────────────────────────────────────────────────────────────
    # POST /api/forums  (multi-mode)
    #
    #   (a) Member mappings mode — body has `get_mappings: true`.
    #   (b) Forum create mode — body parsed as ForumCreate_cls.
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/forums")
    async def create_forum(request: Request):
        """
        Create a new forum OR get member mappings (via POST to bypass CDN GET caching).
        If body has 'get_mappings', handles as member-mappings request.
        """
        body = await request.json()

        # MEMBER MAPPINGS MODE
        if body.get("get_mappings"):
            forum_id = body.get("forum_id", "")
            user_id = body.get("user_id", "")
            if not forum_id or not user_id:
                return {"success": False, "error": "Missing forum_id or user_id"}
            try:
                from services.forum_hd_mapping import get_forum_member_mappings
                mappings = await get_forum_member_mappings(db, forum_id, user_id)
                return {"success": True, "mappings": mappings, "current_user_id": user_id}
            except Exception as e:
                logger.error(f"[ForumMappingPOST] Error: {e}", exc_info=True)
                return {"success": False, "mappings": [], "error": str(e)}

        # NORMAL FORUM CREATE MODE
        try:
            data = ForumCreate_cls(**body)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))

        logger.info(f"[Forums] Creating forum: {data.name} by user {data.user_id[:8]}...")

        # Validate user exists
        if not ObjectId.is_valid(data.user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        user = await db.users.find_one({"_id": ObjectId(data.user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create the forum
        invite_token = generate_invite_token()
        forum_doc = {
            "name": data.name,
            "description": data.description,
            "created_by": data.user_id,
            "invite_token": invite_token,
            "created_at": datetime.now(timezone.utc),
        }

        result = await db.forums.insert_one(forum_doc)
        forum_id = str(result.inserted_id)

        # Add creator as first member with 'owner' role
        member_doc = {
            "forum_id": forum_id,
            "user_id": data.user_id,
            "role": "owner",
            "status": "active",
            "invited_at": datetime.now(timezone.utc),
            "joined_at": datetime.now(timezone.utc),
        }
        await db.forum_members.insert_one(member_doc)

        # Create the default exercise: "The Pattern Running Me"
        exercise_doc = {
            "forum_id": forum_id,
            "slug": "pattern-running-me",
            "title": "The Pattern Running Me",
            "description": "This exercise helps surface one pattern that may currently be shaping how you lead, relate, or respond to life.",
            "prompts": [
                "Where is this pattern showing up in your life right now?",
                "What situation from the last 30–60 days best represents it?",
                "How has this pattern helped you succeed?",
                "Where might this same pattern now be limiting you?",
                "If this pattern softened by 10%, what might change?"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await db.forum_exercises.insert_one(exercise_doc)

        logger.info(f"[Forums] Forum created: {forum_id} with invite token: {invite_token}")

        return {
            "id": forum_id,
            "name": data.name,
            "description": data.description,
            "invite_token": invite_token,
            "created_by": data.user_id,
            "member_count": 1,
            "created_at": forum_doc["created_at"].isoformat(),
        }
