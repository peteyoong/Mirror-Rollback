"""
Forums Core routes  (server-router-refactor-v3)
================================================

Behaviour-preserving extraction of the low-coupling forum CRUD /
membership routes from server.py.  Paths, schemas, log lines and
response shapes are byte-identical.

Endpoints attached here:

    POST  /api/forums/{forum_id}/delete       — owner-only delete
    GET   /api/forums/user/{user_id}          — list user's forums
    POST  /api/get-user-forums                — same, POST variant
    GET   /api/forums/{forum_id}              — forum detail (member only)
    GET   /api/forums/invite/{invite_token}   — public invite preview
    POST  /api/forums/join/{invite_token}     — join via invite
    GET   /api/forums/{forum_id}/members      — member list (member only)
    GET   /api/forums/domains/list            — pattern domains constant

LEFT BEHIND (deferred to v4+, with reason):

    POST  /api/forums/login                   — coupled to login_user / LoginRequest
    POST  /api/forums                         — coupled to ForumCreate +
                                                generate_invite_token +
                                                forum_hd_mapping service
                                                (multi-mode endpoint with
                                                member-mappings fallback).
    GET   /api/forums/{forum_id}/exercise     — exercise CRUD, separate cluster
    POST  /api/forums/{forum_id}/reflections  — reflection CRUD, separate cluster
    GET   /api/forums/{forum_id}/reflections/shared
    GET   /api/forums/{forum_id}/live-field-v1
    GET/POST /api/forums/{forum_id}/updates*
    GET   /api/forums/{forum_id}/pulse

Call signature:

    forums_core.register(api_router, db, logger)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Local copies — IDENTICAL to the inline versions in server.py.  Kept
# here so this router has no upward import on server.py module state.
PATTERN_DOMAINS = [
    {"id": "energy_vitality", "name": "Energy & Vitality"},
    {"id": "emotional_landscape", "name": "Emotional Landscape"},
    {"id": "identity_direction", "name": "Identity & Direction"},
    {"id": "mind_meaning", "name": "Mind & Meaning"},
    {"id": "expression_action", "name": "Expression & Action"},
    {"id": "relationships_boundaries", "name": "Relationships & Boundaries"},
    {"id": "growth_transformation", "name": "Growth & Transformation"},
]


class ForumJoinRequest(BaseModel):
    user_id: str


def register(api_router: APIRouter, db, logger) -> None:
    """Attach the 8 forum-core routes onto `api_router`."""

    async def _get_user_forums_data(user_id: str) -> dict:
        memberships = await db.forum_members.find({
            "user_id": user_id,
            "status": "active",
        }).to_list(100)

        forum_ids = [m["forum_id"] for m in memberships]

        if not forum_ids:
            return {"forums": []}

        forums = []
        for forum_id in forum_ids:
            forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
            if forum:
                member_count = await db.forum_members.count_documents({
                    "forum_id": forum_id,
                    "status": "active",
                })

                created_at = forum.get("created_at", datetime.now(timezone.utc))
                created_at_iso = (
                    created_at.isoformat()
                    if hasattr(created_at, "isoformat")
                    else str(created_at)
                )

                forums.append({
                    "id": str(forum["_id"]),
                    "name": forum["name"],
                    "description": forum.get("description"),
                    "invite_token": forum.get("invite_token", ""),
                    "created_by": forum.get("created_by", ""),
                    "member_count": member_count,
                    "created_at": created_at_iso,
                })

        return {"forums": forums}

    # ──────────────────────────────────────────────────────────────────
    # Delete forum (owner-only)
    # ──────────────────────────────────────────────────────────────────
    @api_router.post("/forums/{forum_id}/delete")
    async def delete_forum(forum_id: str, user_id: str):
        """Delete a forum. Only the forum creator can delete it."""
        try:
            forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
            if not forum:
                raise HTTPException(status_code=404, detail="Forum not found")

            if forum.get("created_by") != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Only the forum creator can delete this forum",
                )

            delete_members = await db.forum_members.delete_many({"forum_id": forum_id})
            await db.forums.delete_one({"_id": ObjectId(forum_id)})

            logger.info(
                f"[Forums] Deleted forum {forum_id} ({forum.get('name')}) by user "
                f"{user_id[:8]}, removed {delete_members.deleted_count} members"
            )

            return {
                "success": True,
                "message": f"Forum '{forum.get('name')}' deleted",
                "members_removed": delete_members.deleted_count,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Forums] Error deleting forum {forum_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ──────────────────────────────────────────────────────────────────
    # List user's forums (GET + POST variants)
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/user/{user_id}")
    async def get_user_forums(user_id: str):
        logger.info(f"[Forums] Getting forums for user: {user_id[:8]}...")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        return await _get_user_forums_data(user_id)

    @api_router.post("/get-user-forums")
    async def get_user_forums_post(request: Request):
        body = await request.json()
        user_id = body.get("user_id", "")
        if not user_id or not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id")
        logger.info(f"[Forums] POST getting forums for user: {user_id[:8]}...")
        result = await _get_user_forums_data(user_id)
        return JSONResponse(content=result, headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "CDN-Cache-Control": "no-store",
        })

    # ──────────────────────────────────────────────────────────────────
    # Get forum detail (member-only)
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/{forum_id}")
    async def get_forum(forum_id: str, user_id: str):
        logger.info(f"[Forums] Getting forum: {forum_id}")
        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
        if not forum:
            raise HTTPException(status_code=404, detail="Forum not found")

        member_count = await db.forum_members.count_documents({
            "forum_id": forum_id,
            "status": "active",
        })

        exercise = await db.forum_exercises.find_one({
            "forum_id": forum_id,
            "is_active": True,
        })

        return {
            "id": str(forum["_id"]),
            "name": forum["name"],
            "description": forum.get("description"),
            "invite_token": forum["invite_token"],
            "created_by": forum["created_by"],
            "member_count": member_count,
            "created_at": forum["created_at"].isoformat(),
            "active_exercise": {
                "id": str(exercise["_id"]),
                "slug": exercise["slug"],
                "title": exercise["title"],
                "description": exercise["description"],
                "prompts": exercise["prompts"],
            } if exercise else None,
        }

    # ──────────────────────────────────────────────────────────────────
    # Invite preview + join
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/invite/{invite_token}")
    async def get_forum_by_invite(invite_token: str):
        logger.info(f"[Forums] Looking up forum by invite token: {invite_token}")
        forum = await db.forums.find_one({"invite_token": invite_token})
        if not forum:
            raise HTTPException(status_code=404, detail="Invalid invite link")

        forum_id = str(forum["_id"])
        member_count = await db.forum_members.count_documents({
            "forum_id": forum_id,
            "status": "active",
        })

        return {
            "id": forum_id,
            "name": forum["name"],
            "description": forum.get("description"),
            "member_count": member_count,
            "created_at": forum["created_at"].isoformat(),
        }

    @api_router.post("/forums/join/{invite_token}")
    async def join_forum(invite_token: str, data: ForumJoinRequest):
        logger.info(
            f"[Forums] User {data.user_id[:8]}... joining forum with token: {invite_token}"
        )

        if not ObjectId.is_valid(data.user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        forum = await db.forums.find_one({"invite_token": invite_token})
        if not forum:
            raise HTTPException(status_code=404, detail="Invalid invite link")

        forum_id = str(forum["_id"])

        existing = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": data.user_id,
        })

        if existing:
            if existing["status"] == "active":
                return {
                    "message": "Already a member",
                    "forum_id": forum_id,
                    "already_member": True,
                }
            await db.forum_members.update_one(
                {"_id": existing["_id"]},
                {"$set": {"status": "active", "joined_at": datetime.now(timezone.utc)}},
            )
            return {
                "message": "Membership reactivated",
                "forum_id": forum_id,
                "already_member": False,
            }

        await db.forum_members.insert_one({
            "forum_id": forum_id,
            "user_id": data.user_id,
            "role": "member",
            "status": "active",
            "invited_at": datetime.now(timezone.utc),
            "joined_at": datetime.now(timezone.utc),
        })

        logger.info(f"[Forums] User {data.user_id[:8]}... joined forum {forum_id}")

        return {
            "message": "Joined forum successfully",
            "forum_id": forum_id,
            "already_member": False,
        }

    # ──────────────────────────────────────────────────────────────────
    # Member list (member-only)
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/{forum_id}/members")
    async def get_forum_members(forum_id: str, user_id: str):
        logger.info(f"[Forums] Getting members for forum: {forum_id}")
        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        members_cursor = db.forum_members.find({
            "forum_id": forum_id,
            "status": "active",
        }).sort("joined_at", 1)

        members = []
        async for m in members_cursor:
            user = await db.users.find_one({"_id": ObjectId(m["user_id"])})
            user_name = user.get("name", "Anonymous") if user else "Anonymous"

            joined_at = m.get("joined_at")
            joined_at_str = joined_at.isoformat() if joined_at else None

            members.append({
                "user_id": m["user_id"],
                "user_name": user_name,
                "role": m.get("role", "member"),
                "joined_at": joined_at_str,
            })

        return {"members": members}

    # ──────────────────────────────────────────────────────────────────
    # Pattern domains (static)
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/domains/list")
    async def get_pattern_domains():
        return {"domains": PATTERN_DOMAINS}
