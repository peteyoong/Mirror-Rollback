"""
Forums Exercise / Reflections / Updates routes  (server-router-refactor-v4)
============================================================================

Behaviour-preserving extraction.  Paths, schemas, log lines and
response shapes are byte-identical to the inline implementation.

Endpoints attached:

    GET   /api/forums/{forum_id}/exercise
    POST  /api/forums/{forum_id}/reflections
    GET   /api/forums/{forum_id}/reflections/shared
    POST  /api/forums/update
    GET   /api/forums/{forum_id}/updates
    GET   /api/forums/{forum_id}/my-update

LEFT BEHIND (deferred, with reason):

    GET  /api/forums/{forum_id}/pulse                    — ~712 lines,
        couples to multiple lens services + pattern aggregator + LLM.
    POST /api/pattern-running-me                         — separate
        pattern-running-me-v2 cluster (own surface contract).
    GET  /api/forums/{forum_id}/live-field-v1            — heavy
        services.live_field coupling.

Call signature:

    forums_exercise.register(api_router, db, logger)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# Local copy of PATTERN_DOMAINS — IDENTICAL to forums_core / server.py.
PATTERN_DOMAINS = [
    {"id": "energy_vitality", "name": "Energy & Vitality"},
    {"id": "emotional_landscape", "name": "Emotional Landscape"},
    {"id": "identity_direction", "name": "Identity & Direction"},
    {"id": "mind_meaning", "name": "Mind & Meaning"},
    {"id": "expression_action", "name": "Expression & Action"},
    {"id": "relationships_boundaries", "name": "Relationships & Boundaries"},
    {"id": "growth_transformation", "name": "Growth & Transformation"},
]


class ForumReflectionCreate(BaseModel):
    user_id: str
    selected_domain: str
    reflection_text: str
    is_shared: bool = False


class ForumUpdateCheckin(BaseModel):
    mentally: Optional[str] = ""
    emotionally: Optional[str] = ""
    relationship: Optional[str] = ""
    vocationally: Optional[str] = ""
    spiritually: Optional[str] = ""
    financially: Optional[str] = ""
    physically: Optional[str] = ""


class ForumUpdateArea(BaseModel):
    title: str = ""
    emotions: List[str] = []
    update_text: str = ""
    add_to_journal: bool = False


class ForumUpdateInput(BaseModel):
    forum_id: str
    user_id: str
    one_word_checkin: ForumUpdateCheckin
    updates: Dict[str, ForumUpdateArea]


def register(api_router: APIRouter, db, logger) -> None:

    # ──────────────────────────────────────────────────────────────────
    # /forums/{id}/exercise — active exercise + submission status
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/{forum_id}/exercise")
    async def get_active_exercise(forum_id: str, user_id: str):
        logger.info(f"[Forums] Getting active exercise for forum: {forum_id}")

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        exercise = await db.forum_exercises.find_one({
            "forum_id": forum_id,
            "is_active": True,
        })

        if not exercise:
            return {"exercise": None}

        user_reflection = await db.forum_reflections.find_one({
            "forum_id": forum_id,
            "exercise_id": str(exercise["_id"]),
            "user_id": user_id,
        })

        return {
            "exercise": {
                "id": str(exercise["_id"]),
                "slug": exercise["slug"],
                "title": exercise["title"],
                "description": exercise["description"],
                "prompts": exercise["prompts"],
            },
            "domains": PATTERN_DOMAINS,
            "has_submitted": user_reflection is not None,
            "user_reflection_id": str(user_reflection["_id"]) if user_reflection else None,
        }

    # ──────────────────────────────────────────────────────────────────
    # /forums/{id}/reflections — POST create/update
    # ──────────────────────────────────────────────────────────────────
    @api_router.post("/forums/{forum_id}/reflections")
    async def submit_reflection(forum_id: str, data: ForumReflectionCreate):
        logger.info(
            f"[Forums] User {data.user_id[:8]}... submitting reflection for forum {forum_id}"
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")
        if not ObjectId.is_valid(data.user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": data.user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        exercise = await db.forum_exercises.find_one({
            "forum_id": forum_id,
            "is_active": True,
        })
        if not exercise:
            raise HTTPException(status_code=404, detail="No active exercise found")

        exercise_id = str(exercise["_id"])

        existing = await db.forum_reflections.find_one({
            "forum_id": forum_id,
            "exercise_id": exercise_id,
            "user_id": data.user_id,
        })

        if existing:
            await db.forum_reflections.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "selected_domain": data.selected_domain,
                    "reflection_text": data.reflection_text,
                    "is_shared": data.is_shared,
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            reflection_id = str(existing["_id"])
            logger.info(f"[Forums] Updated reflection {reflection_id}")
        else:
            reflection_doc = {
                "forum_id": forum_id,
                "exercise_id": exercise_id,
                "user_id": data.user_id,
                "selected_domain": data.selected_domain,
                "reflection_text": data.reflection_text,
                "is_shared": data.is_shared,
                "created_at": datetime.now(timezone.utc),
            }
            result = await db.forum_reflections.insert_one(reflection_doc)
            reflection_id = str(result.inserted_id)
            logger.info(f"[Forums] Created reflection {reflection_id}")

        domain_name = next(
            (d["name"] for d in PATTERN_DOMAINS if d["id"] == data.selected_domain),
            data.selected_domain,
        )

        return {
            "id": reflection_id,
            "forum_id": forum_id,
            "exercise_id": exercise_id,
            "selected_domain": data.selected_domain,
            "domain_name": domain_name,
            "is_shared": data.is_shared,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    # ──────────────────────────────────────────────────────────────────
    # /forums/{id}/reflections/shared — GET shared list
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/{forum_id}/reflections/shared")
    async def get_shared_reflections(forum_id: str, user_id: str):
        logger.info(f"[Forums] Getting shared reflections for forum: {forum_id}")

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        exercise = await db.forum_exercises.find_one({
            "forum_id": forum_id,
            "is_active": True,
        })
        if not exercise:
            return {"reflections": [], "exercise": None}

        exercise_id = str(exercise["_id"])

        reflections_cursor = db.forum_reflections.find({
            "forum_id": forum_id,
            "exercise_id": exercise_id,
            "is_shared": True,
        }).sort("created_at", -1)

        reflections: List[Dict[str, Any]] = []
        async for r in reflections_cursor:
            user = await db.users.find_one({"_id": ObjectId(r["user_id"])})
            user_name = user.get("name", "Anonymous") if user else "Anonymous"

            domain_name = next(
                (d["name"] for d in PATTERN_DOMAINS if d["id"] == r["selected_domain"]),
                r["selected_domain"],
            )

            reflections.append({
                "id": str(r["_id"]),
                "forum_id": r["forum_id"],
                "exercise_id": r["exercise_id"],
                "user_id": r["user_id"],
                "user_name": user_name,
                "selected_domain": r["selected_domain"],
                "domain_name": domain_name,
                "reflection_text": r["reflection_text"],
                "is_shared": r["is_shared"],
                "created_at": r["created_at"].isoformat(),
            })

        return {
            "reflections": reflections,
            "exercise": {
                "id": str(exercise["_id"]),
                "title": exercise["title"],
            },
        }

    # ──────────────────────────────────────────────────────────────────
    # /forums/update — POST structured update + journal sync
    # ──────────────────────────────────────────────────────────────────
    @api_router.post("/forums/update")
    async def save_forum_update(data: ForumUpdateInput):
        logger.info(
            f"[ForumUpdate] Saving update for user {data.user_id} in forum {data.forum_id}"
        )

        membership = await db.forum_members.find_one({
            "forum_id": data.forum_id,
            "user_id": data.user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        user = await db.users.find_one({"_id": ObjectId(data.user_id)})
        user_name = user.get("name", "Anonymous") if user else "Anonymous"

        forum_update = {
            "forum_id": data.forum_id,
            "user_id": data.user_id,
            "user_name": user_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "one_word_checkin": data.one_word_checkin.model_dump(),
            "updates": {k: v.model_dump() for k, v in data.updates.items()},
        }

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = await db.forum_updates.update_one(
            {
                "forum_id": data.forum_id,
                "user_id": data.user_id,
                "created_date": today,
            },
            {"$set": {**forum_update, "created_date": today}},
            upsert=True,
        )

        journal_entries_added = 0
        for area_key, area_data in data.updates.items():
            if area_data.add_to_journal and area_data.update_text.strip():
                emotion_tags = ", ".join(area_data.emotions[:3]) if area_data.emotions else ""

                journal_entry = {
                    "user_id": data.user_id,
                    "entry_text": area_data.update_text,
                    "domain": area_key.capitalize(),
                    "emotions": emotion_tags,
                    "source": "forum_update",
                    "forum_id": data.forum_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await db.journal.insert_one(journal_entry)
                journal_entries_added += 1
                logger.info(f"[ForumUpdate] Added journal entry for {area_key}")

        logger.info(
            f"[ForumUpdate] Saved update for {data.user_id}, journal entries: {journal_entries_added}"
        )

        return {
            "success": True,
            "message": "Forum update saved",
            "journal_entries_added": journal_entries_added,
            "update_id": str(result.upserted_id) if result.upserted_id else None,
        }

    # ──────────────────────────────────────────────────────────────────
    # /forums/{id}/updates — GET recent updates
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/{forum_id}/updates")
    async def get_forum_updates(forum_id: str, user_id: str, limit: int = 20):
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="Not a forum member")

        updates_cursor = db.forum_updates.find(
            {"forum_id": forum_id}
        ).sort("created_at", -1).limit(limit)

        updates: List[Dict[str, Any]] = []
        async for update in updates_cursor:
            updates.append({
                "id": str(update["_id"]),
                "user_id": update["user_id"],
                "user_name": update.get("user_name", "Anonymous"),
                "created_at": update["created_at"],
                "one_word_checkin": update.get("one_word_checkin", {}),
                "updates": update.get("updates", {}),
            })

        return {"updates": updates}

    # ──────────────────────────────────────────────────────────────────
    # /forums/{id}/my-update — GET today's own update
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/forums/{forum_id}/my-update")
    async def get_my_forum_update(forum_id: str, user_id: str):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        update = await db.forum_updates.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "created_date": today,
        })

        if not update:
            return {"found": False, "update": None}

        return {
            "found": True,
            "update": {
                "id": str(update["_id"]),
                "created_at": update["created_at"],
                "one_word_checkin": update.get("one_word_checkin", {}),
                "updates": update.get("updates", {}),
            },
        }
