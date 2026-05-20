"""
Admin Forum Export / Import routes  (server-router-refactor-v3)
================================================================

Extracted from server.py.  Behaviour, paths, schemas, markers and
log lines are byte-identical to the inline implementation.

Endpoints:

    GET   /api/admin/forum/export/{forum_name}?admin_key=...
    POST  /api/admin/forum/import

Security:
    Simple admin-key string match — same constant the inline code
    used (`ADMIN_MIGRATION_KEY = "forum_migration_2024"`).

Call signature:

    admin_forum.register(api_router, db, logger)
"""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


ADMIN_MIGRATION_KEY = "forum_migration_2024"


class ForumImportRequest(BaseModel):
    """Request model for importing forum data."""
    forum_data: dict
    new_forum_name: Optional[str] = None  # Optional: rename forum on import
    admin_key: str


def register(api_router: APIRouter, db, logger) -> None:
    """Attach the two admin forum-migration endpoints onto `api_router`."""

    @api_router.get("/admin/forum/export/{forum_name}")
    async def export_forum_by_name(forum_name: str, admin_key: str):
        """
        Export a forum and all related data by forum name.
        Returns JSON that can be imported into another environment.

        Security: Requires admin_key query parameter.
        """
        if admin_key != ADMIN_MIGRATION_KEY:
            raise HTTPException(status_code=403, detail="Invalid admin key")

        try:
            # Find forum by name (case-insensitive)
            forum = await db.forums.find_one({
                "name": {"$regex": f"^{forum_name}$", "$options": "i"}
            })

            if not forum:
                raise HTTPException(status_code=404, detail=f"Forum '{forum_name}' not found")

            forum_id = str(forum["_id"])
            logger.info(f"[ForumExport] Exporting forum: {forum_name} (ID: {forum_id})")

            # Export forum record
            forum_export = {
                "name": forum.get("name"),
                "description": forum.get("description"),
                "invite_token": forum.get("invite_token"),
                "created_by": forum.get("created_by"),
                "active_exercise_id": forum.get("active_exercise_id"),
                "created_at": forum.get("created_at").isoformat() if forum.get("created_at") else None,
            }

            # Export members
            members_cursor = db.forum_members.find({"forum_id": forum_id})
            members = []
            async for member in members_cursor:
                members.append({
                    "user_id": member.get("user_id"),
                    "role": member.get("role"),
                    "joined_at": member.get("joined_at").isoformat() if member.get("joined_at") else None,
                })

            # Export reflections
            reflections_cursor = db.forum_reflections.find({"forum_id": forum_id})
            reflections = []
            async for reflection in reflections_cursor:
                reflections.append({
                    "user_id": reflection.get("user_id"),
                    "exercise_id": reflection.get("exercise_id"),
                    "selected_domain": reflection.get("selected_domain"),
                    "reflection_text": reflection.get("reflection_text"),
                    "is_shared": reflection.get("is_shared", False),
                    "created_at": reflection.get("created_at").isoformat() if reflection.get("created_at") else None,
                })

            # Export chat messages
            chat_cursor = db.forum_chat_messages.find({"forum_id": forum_id})
            chat_messages = []
            async for msg in chat_cursor:
                chat_messages.append({
                    "user_id": msg.get("user_id"),
                    "mode": msg.get("mode"),
                    "target_member_id": msg.get("target_member_id"),
                    "message": msg.get("message"),
                    "response": msg.get("response"),
                    "timestamp": msg.get("timestamp").isoformat() if msg.get("timestamp") else None,
                })

            # Export forum story cache
            story_cache = await db.forum_story_cache.find_one({"forum_id": forum_id})
            story_cache_export = None
            if story_cache:
                story_cache_export = {
                    "story": story_cache.get("story"),
                    "generated_at": story_cache.get("generated_at").isoformat() if story_cache.get("generated_at") else None,
                }

            # Get user info for members (names)
            user_ids = [m["user_id"] for m in members]
            users_info = {}
            for uid in user_ids:
                try:
                    user = await db.users.find_one({"_id": ObjectId(uid)})
                    if user:
                        users_info[uid] = {
                            "name": user.get("name"),
                            "email": user.get("email"),
                        }
                except Exception:
                    pass

            export_data = {
                "export_version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "source_forum_id": forum_id,
                "forum": forum_export,
                "members": members,
                "members_info": users_info,
                "reflections": reflections,
                "chat_messages": chat_messages,
                "story_cache": story_cache_export,
                "stats": {
                    "member_count": len(members),
                    "reflection_count": len(reflections),
                    "chat_message_count": len(chat_messages),
                    "has_story_cache": story_cache_export is not None,
                }
            }

            logger.info(
                f"[ForumExport] Export complete: {len(members)} members, "
                f"{len(reflections)} reflections, {len(chat_messages)} chat messages"
            )

            return export_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ForumExport] Error: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    @api_router.post("/admin/forum/import")
    async def import_forum(request: ForumImportRequest):
        """
        Import a forum from exported JSON data.
        Optionally rename the forum on import.

        Security: Requires admin_key in request body.
        """
        if request.admin_key != ADMIN_MIGRATION_KEY:
            raise HTTPException(status_code=403, detail="Invalid admin key")

        try:
            data = request.forum_data
            forum_info = data.get("forum", {})

            new_name = request.new_forum_name or forum_info.get("name")
            if not new_name:
                raise HTTPException(status_code=400, detail="Forum name is required")

            logger.info(f"[ForumImport] Importing forum as: {new_name}")

            existing = await db.forums.find_one({
                "name": {"$regex": f"^{new_name}$", "$options": "i"}
            })

            if existing:
                existing_id = str(existing["_id"])
                logger.info(f"[ForumImport] Removing existing forum: {new_name} (ID: {existing_id})")
                await db.forums.delete_one({"_id": existing["_id"]})
                await db.forum_members.delete_many({"forum_id": existing_id})
                await db.forum_reflections.delete_many({"forum_id": existing_id})
                await db.forum_chat_messages.delete_many({"forum_id": existing_id})
                await db.forum_story_cache.delete_many({"forum_id": existing_id})

            new_invite_token = secrets.token_urlsafe(16)
            forum_doc = {
                "name": new_name,
                "description": forum_info.get("description"),
                "invite_token": new_invite_token,
                "created_by": forum_info.get("created_by"),
                "active_exercise_id": forum_info.get("active_exercise_id"),
                "created_at": datetime.utcnow(),
            }

            result = await db.forums.insert_one(forum_doc)
            new_forum_id = str(result.inserted_id)
            logger.info(f"[ForumImport] Created forum with ID: {new_forum_id}")

            # Import members
            members = data.get("members", [])
            members_imported = 0
            for member in members:
                await db.forum_members.insert_one({
                    "forum_id": new_forum_id,
                    "user_id": member.get("user_id"),
                    "role": member.get("role", "member"),
                    "joined_at": datetime.utcnow(),
                })
                members_imported += 1

            # Import reflections
            reflections = data.get("reflections", [])
            reflections_imported = 0
            for reflection in reflections:
                await db.forum_reflections.insert_one({
                    "forum_id": new_forum_id,
                    "user_id": reflection.get("user_id"),
                    "exercise_id": reflection.get("exercise_id"),
                    "selected_domain": reflection.get("selected_domain"),
                    "reflection_text": reflection.get("reflection_text"),
                    "is_shared": reflection.get("is_shared", False),
                    "created_at": datetime.utcnow(),
                })
                reflections_imported += 1

            # Import chat messages
            chat_messages = data.get("chat_messages", [])
            chat_imported = 0
            for msg in chat_messages:
                await db.forum_chat_messages.insert_one({
                    "forum_id": new_forum_id,
                    "user_id": msg.get("user_id"),
                    "mode": msg.get("mode"),
                    "target_member_id": msg.get("target_member_id"),
                    "message": msg.get("message"),
                    "response": msg.get("response"),
                    "timestamp": datetime.utcnow(),
                })
                chat_imported += 1

            # Import story cache if present
            story_cache = data.get("story_cache")
            story_imported = False
            if story_cache and story_cache.get("story"):
                await db.forum_story_cache.insert_one({
                    "forum_id": new_forum_id,
                    "story": story_cache.get("story"),
                    "generated_at": datetime.utcnow(),
                })
                story_imported = True

            logger.info(
                f"[ForumImport] Import complete: {members_imported} members, "
                f"{reflections_imported} reflections, {chat_imported} chat messages"
            )

            return {
                "success": True,
                "source_forum_id": data.get("source_forum_id"),
                "destination_forum_id": new_forum_id,
                "forum_name": new_name,
                "invite_token": new_invite_token,
                "stats": {
                    "members_imported": members_imported,
                    "reflections_imported": reflections_imported,
                    "chat_messages_imported": chat_imported,
                    "story_cache_imported": story_imported,
                },
                "members_info": data.get("members_info", {}),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ForumImport] Error: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
