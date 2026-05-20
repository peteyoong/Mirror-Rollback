"""
Forums Chat routes  (server-router-refactor-v4)
================================================

Behaviour-preserving extraction of the forum chat surface from
server.py.  Paths, schemas, log lines, system prompts, rate-limit
window, response shapes, and persistence behaviour are byte-identical.

Endpoints attached:

    GET   /api/forums/{forum_id}/chat/history
    POST  /api/forums/{forum_id}/chat

Two heavy server.py helpers (`get_member_lens_data` and
`build_forum_dynamics_context`) are passed in via `register()` so we
avoid pulling in their 700+ lines of body, and so they remain a
single shared implementation across both surfaces.

Call signature:

    forums_chat.register(
        api_router, db, logger,
        emergent_llm_key,
        get_member_lens_data_fn,
        build_forum_dynamics_context_fn,
    )
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Module-level constants (identical to the inline version in server.py).
# ---------------------------------------------------------------------------

FORUM_CHAT_SYSTEM_PROMPT = """You are Emergent!, acting as a reflective facilitator for a forum community in Project Mirror.

YOUR ROLE:
You help forum members understand themselves, each other, and the group dynamics through the lens of their shared profiles (Human Design, Enneagram, Astrology, Numerology, and Pattern work).

TONE & STYLE:
- Write like a thoughtful facilitator, not an analytical system
- Reflective and curious, not authoritative
- Non-deterministic - avoid claims of certainty
- Agency-preserving - the user decides meaning
- Calm, warm, and grounded

USE LANGUAGE LIKE:
- "may suggest"
- "might indicate"  
- "could reflect"
- "one possibility is"
- "this combination seems to..."
- "there's often..."
- "that can create..."

NEVER:
- Diagnose people or claim to know their truth
- Make deterministic predictions
- Tell people what they should or must do
- Claim certainty about personality or behavior
- Use section headers like "Observation:", "Interpretation:", etc.

Mirror is a mirror, not a guru. You reflect patterns for contemplation.

RESPONSE FORMAT:
- Write 2-4 short paragraphs in a conversational, reflective tone
- No section headers or bullet points
- End naturally with a reflective question
- Keep it concise but meaningful

EXAMPLE STYLE:
"Looking at the mix of lenses represented in this forum, there seems to be a combination of strong initiating energy and reflective depth. That often creates groups where ideas move quickly but meaning unfolds more slowly.

Some members may naturally push conversations forward, while others help the group pause and explore what's underneath those ideas. When those two rhythms work together, a forum can become both dynamic and deeply supportive.

One thing the group might explore is this: how does each person naturally contribute to the forum's movement — initiating, holding space, questioning, or synthesizing?"
"""


# ---------------------------------------------------------------------------
# Pydantic schemas (identical names / shapes).
# ---------------------------------------------------------------------------

class ForumChatMode(str, Enum):
    SELF = "self"
    MEMBER = "member"
    FORUM = "forum"


class ForumChatRequest(BaseModel):
    user_id: str
    message: str
    mode: ForumChatMode
    target_member_id: Optional[str] = None


class ForumChatResponse(BaseModel):
    success: bool
    message_id: str
    response: str
    timestamp: str


# ---------------------------------------------------------------------------
# Per-process rate-limit window (3-second cooldown), same as inline.
# Module-private so it persists across calls without leaking into other
# rate-limiters.
# ---------------------------------------------------------------------------

_forum_chat_rate_limits: Dict[str, float] = {}


def _check_forum_chat_rate_limit(user_id: str, cooldown_seconds: float = 3.0) -> bool:
    current_time = time.time()
    last_request = _forum_chat_rate_limits.get(user_id, 0)
    if current_time - last_request < cooldown_seconds:
        return False
    _forum_chat_rate_limits[user_id] = current_time
    return True


# ---------------------------------------------------------------------------
# Prompt-building helpers — formatting only, no DB access.
# ---------------------------------------------------------------------------

def _format_lens_for_prompt(lens_data: dict) -> str:
    parts: List[str] = []

    name = lens_data.get("name", "Anonymous")
    parts.append(f"Name: {name}")

    hd = lens_data.get("human_design", {})
    if hd.get("type"):
        hd_line = f"Human Design: {hd.get('type')}"
        if hd.get("profile"):
            hd_line += f" • {hd.get('profile')}"
        if hd.get("authority"):
            hd_line += f" • {hd.get('authority')} Authority"
        parts.append(hd_line)

        if hd.get("definition"):
            parts.append(f"  Definition: {hd.get('definition')}")
        if hd.get("centers_defined"):
            parts.append(f"  Defined Centers: {', '.join(hd.get('centers_defined', []))}")
        if hd.get("centers_undefined"):
            parts.append(f"  Open Centers: {', '.join(hd.get('centers_undefined', []))}")

    enneagram = lens_data.get("enneagram", {})
    if enneagram.get("core_type"):
        enne_line = f"Enneagram: Type {enneagram.get('core_type')}"
        if enneagram.get("wing"):
            enne_line += f"w{enneagram.get('wing')}"
        parts.append(enne_line)

    astro = lens_data.get("astrology", {})
    if astro.get("sun") or astro.get("moon"):
        astro_line = "Astrology:"
        if astro.get("sun"):
            astro_line += f" Sun in {astro.get('sun')}"
        if astro.get("moon"):
            astro_line += f", Moon in {astro.get('moon')}"
        if astro.get("rising"):
            astro_line += f", {astro.get('rising')} Rising"
        parts.append(astro_line)

    numerology = lens_data.get("numerology", {})
    if numerology.get("life_path"):
        lp = numerology.get("life_path")
        if isinstance(lp, dict):
            lp = lp.get("number")
        parts.append(f"Numerology: Life Path {lp}")

    patterns = lens_data.get("patterns", {})
    if patterns.get("active_domains"):
        parts.append(f"Active Pattern Domains: {', '.join(patterns.get('active_domains', []))}")
    if patterns.get("recurring_domains"):
        parts.append(f"Recurring Domains: {', '.join(patterns.get('recurring_domains', []))}")

    return "\n".join(parts)


def _format_dynamics_for_prompt(dynamics: dict) -> str:
    parts: List[str] = []

    member_count = dynamics.get("member_count", 0)
    parts.append(f"Forum has {member_count} active member(s)")

    hd_dist = dynamics.get("hd_type_distribution", {})
    if hd_dist:
        hd_summary = ", ".join([f"{k}: {v}" for k, v in hd_dist.items()])
        parts.append(f"Human Design Types: {hd_summary}")

    auth_dist = dynamics.get("hd_authority_distribution", {})
    if auth_dist:
        auth_summary = ", ".join([f"{k}: {v}" for k, v in auth_dist.items()])
        parts.append(f"Authorities: {auth_summary}")

    enne_dist = dynamics.get("enneagram_distribution", {})
    if enne_dist:
        enne_summary = ", ".join([f"Type {k}: {v}" for k, v in enne_dist.items()])
        parts.append(f"Enneagram Types: {enne_summary}")

    elem_dist = dynamics.get("astrology_elements", {})
    if elem_dist:
        elem_summary = ", ".join([f"{k}: {v}" for k, v in elem_dist.items()])
        parts.append(f"Dominant Elements: {elem_summary}")

    pattern_domains = dynamics.get("active_pattern_domains", [])
    if pattern_domains:
        domain_names = [d.get("domain", "") for d in pattern_domains[:5]]
        parts.append(f"Active Pattern Domains: {', '.join(domain_names)}")

    defined_centers = dynamics.get("defined_centers_coverage", {})
    if defined_centers:
        coverage = ", ".join([f"{k}({v})" for k, v in list(defined_centers.items())[:5]])
        parts.append(f"Center Coverage (defined): {coverage}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# register() — attach routes onto api_router.
# ---------------------------------------------------------------------------

def register(
    api_router: APIRouter,
    db,
    logger,
    emergent_llm_key: Optional[str],
    get_member_lens_data,           # async fn(user_id) -> dict
    build_forum_dynamics_context,   # sync fn(members_lens_data: List[dict]) -> dict
) -> None:

    async def _build_forum_chat_context(
        forum_id: str,
        user_id: str,
        mode: ForumChatMode,
        target_member_id: Optional[str] = None,
    ) -> str:
        context_parts: List[str] = []

        members_cursor = db.forum_members.find({
            "forum_id": forum_id,
            "status": "active",
        })
        member_user_ids: List[str] = []
        async for m in members_cursor:
            member_user_ids.append(m["user_id"])

        members_lens_data: List[dict] = []
        for mid in member_user_ids:
            lens_data = await get_member_lens_data(mid)
            members_lens_data.append(lens_data)

        dynamics = build_forum_dynamics_context(members_lens_data)

        if mode in [ForumChatMode.SELF, ForumChatMode.MEMBER]:
            user_lens = await get_member_lens_data(user_id)
            context_parts.append("--- YOUR PROFILE (Requesting User) ---")
            context_parts.append(_format_lens_for_prompt(user_lens))

        if mode == ForumChatMode.MEMBER and target_member_id:
            target_lens = await get_member_lens_data(target_member_id)
            context_parts.append("\n--- TARGET MEMBER PROFILE ---")
            context_parts.append(_format_lens_for_prompt(target_lens))

        context_parts.append("\n--- FORUM DYNAMICS SUMMARY ---")
        context_parts.append(_format_dynamics_for_prompt(dynamics))

        return "\n".join(context_parts)

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/chat/history
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/chat/history")
    async def get_forum_chat_history(forum_id: str, user_id: str, limit: int = 50):
        logger.info(f"[ForumChat] Getting chat history for forum {forum_id}, user {user_id[:8]}...")

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        messages_cursor = db.forum_chat_messages.find({
            "forum_id": forum_id,
            "user_id": user_id,
        }).sort("timestamp", 1).limit(limit)

        messages: List[Dict[str, Any]] = []
        async for msg in messages_cursor:
            messages.append({
                "id": str(msg["_id"]),
                "mode": msg.get("mode"),
                "target_member_id": msg.get("target_member_id"),
                "target_member_name": msg.get("target_member_name"),
                "message": msg.get("message"),
                "response": msg.get("response"),
                "timestamp": msg["timestamp"].isoformat() if msg.get("timestamp") else None,
            })

        return {"success": True, "messages": messages}

    # ──────────────────────────────────────────────────────────────────
    # POST /api/forums/{forum_id}/chat
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/forums/{forum_id}/chat", response_model=ForumChatResponse)
    async def forum_chat(forum_id: str, request: ForumChatRequest):
        logger.info(
            f"[ForumChat] Request: forum={forum_id}, user={request.user_id[:8]}..., "
            f"mode={request.mode}"
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        if not _check_forum_chat_rate_limit(request.user_id):
            raise HTTPException(
                status_code=429,
                detail="Please wait a moment before sending another message.",
            )

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": request.user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        target_member_name: Optional[str] = None
        if request.mode == ForumChatMode.MEMBER:
            if not request.target_member_id:
                raise HTTPException(
                    status_code=400,
                    detail="target_member_id required for member mode",
                )

            target_membership = await db.forum_members.find_one({
                "forum_id": forum_id,
                "user_id": request.target_member_id,
                "status": "active",
            })

            if not target_membership:
                raise HTTPException(
                    status_code=404,
                    detail="Target member not found in this forum",
                )

            target_user = await db.users.find_one({"_id": ObjectId(request.target_member_id)})
            target_member_name = target_user.get("name", "Unknown") if target_user else "Unknown"

        try:
            if not emergent_llm_key:
                logger.error("[ForumChat] EMERGENT_LLM_KEY not configured!")
                raise HTTPException(status_code=500, detail="AI service not configured")

            context = await _build_forum_chat_context(
                forum_id=forum_id,
                user_id=request.user_id,
                mode=request.mode,
                target_member_id=request.target_member_id,
            )

            recent_history = await db.forum_chat_messages.find({
                "forum_id": forum_id,
                "user_id": request.user_id,
            }).sort("timestamp", -1).limit(5).to_list(5)
            recent_history = list(reversed(recent_history))

            history_parts: List[str] = []
            if recent_history:
                history_parts.append("\n--- RECENT CONVERSATION ---")
                for msg in recent_history:
                    history_parts.append(
                        f"User ({msg.get('mode', 'unknown')} mode): {msg.get('message', '')[:300]}"
                    )
                    history_parts.append(f"Mirror: {msg.get('response', '')[:500]}")

            system_prompt = FORUM_CHAT_SYSTEM_PROMPT
            system_prompt += "\n\n--- FORUM CONTEXT ---\n" + context
            if history_parts:
                system_prompt += "\n" + "\n".join(history_parts)

            if request.mode == ForumChatMode.SELF:
                system_prompt += "\n\nThe user is asking about THEMSELVES in the context of this forum."
            elif request.mode == ForumChatMode.MEMBER:
                system_prompt += (
                    f"\n\nThe user is asking about another member ({target_member_name}). "
                    f"Be respectful and focus on potential strengths and perspectives."
                )
            else:  # FORUM mode
                system_prompt += "\n\nThe user is asking about the FORUM GROUP DYNAMICS as a whole."

            from emergent_contract import emergent_generate
            from llm_model_config import get_primary_model

            try:
                response_text = await asyncio.wait_for(
                    emergent_generate(
                        mode="reflection_chat",
                        user_message=request.message,
                        endpoint="forum_chat",
                        user_id=request.user_id,
                        context={"forum_id": forum_id, "mode": request.mode.value},
                        additional_system_prompt=system_prompt,
                        model=get_primary_model(),
                    ),
                    timeout=60.0,
                )
                logger.info(
                    f"[ForumChat] LLM response received, "
                    f"length={len(response_text) if response_text else 0}"
                )
            except asyncio.TimeoutError:
                logger.error(f"[ForumChat] LLM timeout for user {request.user_id}")
                raise HTTPException(
                    status_code=504,
                    detail="Mirror is taking too long. Please try again.",
                )

            now = datetime.now(timezone.utc)
            message_doc = {
                "forum_id": forum_id,
                "user_id": request.user_id,
                "mode": request.mode.value,
                "target_member_id": request.target_member_id,
                "target_member_name": target_member_name,
                "message": request.message,
                "response": response_text,
                "timestamp": now,
            }

            result = await db.forum_chat_messages.insert_one(message_doc)
            message_id = str(result.inserted_id)

            logger.info(f"[ForumChat] Message stored: {message_id}")

            return ForumChatResponse(
                success=True,
                message_id=message_id,
                response=response_text,
                timestamp=now.isoformat(),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ForumChat] Error: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process chat request")
