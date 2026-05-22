"""
Forums Intelligence routes  (server-router-refactor-v6)
========================================================

Behaviour-preserving extraction of the read-only / reflective forum
intelligence surface from server.py.

Endpoints attached:

    GET   /api/forums/{forum_id}/member-lens/{member_user_id}
    GET   /api/forums/{forum_id}/member-mappings
    GET   /api/forums/{forum_id}/relationship-map     (alias of member-mappings)
    GET   /api/forums/{forum_id}/contributions
    GET   /api/forums/{forum_id}/dynamics-context
    POST  /api/forums/{forum_id}/pairwise-dynamics
    GET   /api/forums/{forum_id}/pattern-map

All paths, schemas, log lines, response shapes, and prompts are
byte-identical to the inline versions.  Shared lens helpers
(`get_member_lens_data`, `build_forum_dynamics_context`,
`format_lens_for_prompt`) come from `services.forum_lens_helpers`,
the same module used by forums_chat — single source of truth.

NOT moved in v6 (still inline in server.py for now):
  • /forums/{forum_id}/member-summary/{member_id}  — pure delegation
    to services.member_summary; bundled with other member-summary
    surfaces in server.py and left for a later pass.

Call signature:

    forums_intelligence.register(api_router, db, logger, emergent_llm_key)
"""

from __future__ import annotations

import asyncio
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.forum_lens_helpers import (
    get_member_lens_data,
    build_forum_dynamics_context,
    format_lens_for_prompt,
)

# ---------------------------------------------------------------------------
# Pairwise Dynamics — module-level constants (verbatim from server.py).
# ---------------------------------------------------------------------------

PAIRWISE_DYNAMICS_SYSTEM_PROMPT = """You are Emergent!, a reflective facilitator helping two forum members explore how their different profiles might interact.

YOUR ROLE:
Generate a calm, thoughtful reflection about how two members' profiles may complement or contrast with each other, based on their lens data (Human Design, Enneagram, Astrology, Numerology, and Pattern work).

TONE GUIDELINES:
- Reflective facilitator, not analyst or relationship counselor
- Non-deterministic and exploratory
- Calm, warm, and grounded
- Agency-preserving - the pair decides what resonates

USE LANGUAGE LIKE:
- "may bring different approaches"
- "might complement each other"
- "could create productive tension"
- "one person may tend toward... while the other..."
- "this contrast sometimes invites..."

AVOID:
- Relationship predictions or diagnoses
- Deterministic claims about compatibility
- Rigid framework explanations
- Lists of differences without reflection
- Statements like "you will" or "this means"

OUTPUT FORMAT:
Write exactly 3 short paragraphs followed by a reflective question. Use these EXACT markers:

[COMPLEMENT]
How these two profiles may complement each other. Focus on what each might naturally bring that the other doesn't.

[TENSION]
Where tensions or differences may arise. Frame these as growth invitations, not problems.

[INSIGHT]
What the pair may help each other see or learn. What might become visible through their differences.

[QUESTION]
A single reflective question for the pair to explore together.

Keep each section to 2-4 sentences. Write like a wise facilitator offering a gentle observation.
"""


class PairwiseDynamicsRequest(BaseModel):
    user_id: str
    member_a_id: str
    member_b_id: str


# ---------------------------------------------------------------------------
# register() — attach routes onto api_router.
# ---------------------------------------------------------------------------

def register(
    api_router: APIRouter,
    db,
    logger,
    emergent_llm_key: Optional[str],
) -> None:

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/member-lens/{member_user_id}
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/member-lens/{member_user_id}")
    async def get_forum_member_lens(forum_id: str, member_user_id: str, user_id: str):
        """
        Get detailed lens data for a specific forum member.
        Used by Member Lens Profile modal.
        """
        logger.info(
            f"[ForumMemberLens] Getting lens data for member {member_user_id[:8]}... "
            f"in forum {forum_id}"
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        # Check requester membership
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        # Check target member is also in forum
        target_membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": member_user_id,
            "status": "active",
        })

        if not target_membership:
            raise HTTPException(status_code=404, detail="Member not found in this forum")

        # Get lens data
        lens_data = await get_member_lens_data(member_user_id)

        return {
            "success": True,
            "lens_data": lens_data,
        }

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/member-mappings
    # GET /api/forums/{forum_id}/relationship-map   (alias)
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/member-mappings")
    @api_router.get("/forums/{forum_id}/relationship-map")
    async def get_forum_member_mappings(forum_id: str, user_id: str):
        """
        Get "How they map to me" - HD channel-completion based mappings
        for all forum members relative to the current user.

        Returns relational interpretations, NOT raw HD data.
        Each member mapping includes:
        - headline (scannable)
        - what_to_watch (short watch-out)
        - description (detail view)
        - what_works (detail view)
        - why_this_happens (HD mechanics, hidden unless expanded)
        """
        logger.info(
            f"[ForumMapping] Getting member mappings for user {user_id[:8]}... "
            f"in forum {forum_id}"
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        # Check membership
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        try:
            from services.forum_hd_mapping import get_forum_member_mappings as _hd_mappings

            mappings = await _hd_mappings(
                db=db,
                forum_id=forum_id,
                current_user_id=user_id,
            )

            return {
                "success": True,
                "mappings": mappings,
                "current_user_id": user_id,
            }

        except Exception as e:
            logger.error(f"[ForumMapping] Error: {e}")
            return {
                "success": False,
                "mappings": [],
                "error": str(e),
            }

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/between-you-today
    # Relationship Timing Layer v1 — "Between You Today"
    # Modulates the existing relationship architecture against today's
    # transit dominance for each side. NOT a horoscope, NOT a forecast.
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/between-you-today")
    async def get_between_you_today(
        forum_id: str,
        user_id: str,
        member_id: str,
        refresh: Optional[bool] = False,
    ):
        """
        Generate (or return cached) "Between You Today" envelope for the
        anchor↔target pair on today's date.

        - forum_id:  the forum context (used to authorise + scope)
        - user_id:   the anchor (current user) viewing the card
        - member_id: the target member they are looking at
        - refresh:   if True, bypass 24h cache
        """
        logger.info(
            f"[BetweenYouToday] forum={forum_id} anchor={user_id[:8]}... "
            f"target={member_id[:8]}... refresh={refresh}"
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        # Anchor must be an active member of the forum
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        # Target must also be in the forum
        target_membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": member_id,
            "status": "active",
        })
        if not target_membership:
            raise HTTPException(status_code=404, detail="Member not found in this forum")

        try:
            from services.relationship_today import (
                build_between_you_today, ensure_cache_indexes,
            )
            # Lazy index creation — idempotent; never raises into request path
            try:
                await ensure_cache_indexes(db)
            except Exception:
                pass

            envelope = await build_between_you_today(
                db=db,
                forum_id=forum_id,
                anchor_user_id=user_id,
                target_user_id=member_id,
                emergent_llm_key=emergent_llm_key,
                force_refresh=bool(refresh),
            )

            if envelope is None:
                return JSONResponse(
                    content={
                        "success": False,
                        "today": None,
                        "error": "unable to compute relationship timing for this pair",
                    },
                    headers={"Cache-Control": "no-store, max-age=0"},
                )

            return JSONResponse(
                content={"success": True, "today": envelope},
                headers={
                    "Cache-Control": "no-store, max-age=0",
                    "CDN-Cache-Control": "no-store",
                },
            )

        except Exception as e:
            logger.error(f"[BetweenYouToday] Error: {e}", exc_info=True)
            return JSONResponse(
                content={"success": False, "today": None, "error": str(e)},
                headers={"Cache-Control": "no-store, max-age=0"},
            )

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/contributions
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/contributions")
    async def get_forum_contributions_endpoint(forum_id: str, user_id: str):
        """
        "What Each Person Brings" — compact per-member contribution cards.

        Returns, for every active member, 2–3 uppercase attribute chips plus a
        single-line primary label derived deterministically from the member's
        Human Design profile (type + profile + prominent defined centers).

        The requester must be an active member of the forum.
        """
        logger.info(f"[ForumContributions] forum={forum_id} by user={user_id[:8]}...")

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        try:
            from services.forum_contributions import get_forum_contributions
            contributions = await get_forum_contributions(db=db, forum_id=forum_id)
            return JSONResponse(
                content={
                    "success": True,
                    "contributions": contributions,
                },
                headers={
                    "Cache-Control": "no-store, max-age=0",
                    "CDN-Cache-Control": "no-store",
                },
            )
        except Exception as e:
            logger.error(f"[ForumContributions] Error: {e}", exc_info=True)
            return JSONResponse(
                content={"success": False, "contributions": [], "error": str(e)},
                headers={"Cache-Control": "no-store, max-age=0"},
            )

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/dynamics-context
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/dynamics-context")
    async def get_forum_dynamics_context(forum_id: str, user_id: str):
        """
        Get the aggregated dynamics context for a forum.
        Returns structured data for Forum Chat and future dynamics features.
        """
        logger.info(f"[ForumDynamics] Building dynamics context for forum {forum_id}")

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        # Check membership
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        # Get all active member IDs
        members_cursor = db.forum_members.find({
            "forum_id": forum_id,
            "status": "active",
        })

        member_user_ids = []
        async for m in members_cursor:
            member_user_ids.append(m["user_id"])

        # Build lens data for all members
        members_lens_data = []
        for mid in member_user_ids:
            lens_data = await get_member_lens_data(mid)
            members_lens_data.append(lens_data)

        # Build dynamics context
        context = build_forum_dynamics_context(members_lens_data)

        return {
            "success": True,
            "context": context,
        }

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/member-summary/{member_id}
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/member-summary/{member_id}")
    async def get_member_summary_endpoint(forum_id: str, member_id: str, user_id: str):
        """
        Quick orientation card for a single forum member — Astrology, HD, BaZi,
        Enneagram, Numerology + one "how they read in the room" line. Used by
        the interactive members row on /forums/[id].
        Requester must be an active member of the forum.
        """
        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        if not ObjectId.is_valid(member_id):
            raise HTTPException(status_code=400, detail="Invalid member_id format")

        requester = await db.forum_members.find_one({
            "forum_id": forum_id, "user_id": user_id, "status": "active",
        })
        if not requester:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        try:
            from services.member_summary import get_member_summary
            summary = await get_member_summary(db=db, forum_id=forum_id, member_id=member_id)
            if not summary:
                raise HTTPException(status_code=404, detail="Member not found in this forum")
            return JSONResponse(
                content={"success": True, "summary": summary},
                headers={"Cache-Control": "no-store, max-age=0",
                         "CDN-Cache-Control": "no-store"},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[MemberSummary] error: {e}", exc_info=True)
            return JSONResponse(
                content={"success": False, "summary": None, "error": str(e)},
                headers={"Cache-Control": "no-store"},
            )

    # ──────────────────────────────────────────────────────────────────
    # POST /api/forums/{forum_id}/pairwise-dynamics
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/forums/{forum_id}/pairwise-dynamics")
    async def get_pairwise_dynamics(forum_id: str, request: PairwiseDynamicsRequest):
        """
        Generate a reflective comparison between two forum members.
        """
        logger.info(
            f"[PairwiseDynamics] Comparing {request.member_a_id[:8]}... "
            f"and {request.member_b_id[:8]}..."
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")

        # Verify requester is a member
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": request.user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        # Verify both members are in the forum
        member_a_membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": request.member_a_id,
            "status": "active",
        })
        member_b_membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": request.member_b_id,
            "status": "active",
        })

        if not member_a_membership or not member_b_membership:
            raise HTTPException(
                status_code=404,
                detail="One or both members not found in this forum",
            )

        try:
            if not emergent_llm_key:
                raise HTTPException(status_code=500, detail="AI service not configured")

            # Fetch lens data for both members
            member_a_lens = await get_member_lens_data(request.member_a_id)
            member_b_lens = await get_member_lens_data(request.member_b_id)

            # Format for prompt
            context_text = f"""MEMBER A: {member_a_lens.get('name', 'Member A')}
{format_lens_for_prompt(member_a_lens)}

MEMBER B: {member_b_lens.get('name', 'Member B')}
{format_lens_for_prompt(member_b_lens)}"""

            user_message = f"""Based on these two member profiles, write a reflective narrative about how they might interact or complement each other.

{context_text}

Remember: Write a warm, thoughtful reflection. Avoid predictions or deterministic claims. End with a reflective question for the pair."""

            # Call LLM
            from emergent_contract import emergent_generate
            from llm_model_config import get_primary_model

            try:
                reflection_text = await asyncio.wait_for(
                    emergent_generate(
                        mode="reflection_chat",
                        user_message=user_message,
                        endpoint="pairwise_dynamics",
                        user_id=request.user_id,
                        context={"forum_id": forum_id},
                        additional_system_prompt=PAIRWISE_DYNAMICS_SYSTEM_PROMPT,
                        model=get_primary_model(),
                    ),
                    timeout=60.0,
                )
                logger.info(
                    f"[PairwiseDynamics] Reflection generated, "
                    f"length={len(reflection_text) if reflection_text else 0}"
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Mirror is taking too long. Please try again.",
                )

            return {
                "success": True,
                "member_a": {
                    "id": request.member_a_id,
                    "name": member_a_lens.get("name", "Member A"),
                },
                "member_b": {
                    "id": request.member_b_id,
                    "name": member_b_lens.get("name", "Member B"),
                },
                "reflection": reflection_text,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[PairwiseDynamics] Error: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate pairwise dynamics")

    # ──────────────────────────────────────────────────────────────────
    # GET /api/forums/{forum_id}/pattern-map
    # ──────────────────────────────────────────────────────────────────

    @api_router.get("/forums/{forum_id}/pattern-map")
    async def get_forum_pattern_map(forum_id: str, user_id: str):
        """
        Get the Forum Pattern Map - aggregated patterns across all forum members.

        Detects:
        1. Shared Pattern Types - When multiple members have similar pattern arcs
        2. Timeline Clusters - Event concentrations across members in time windows

        Returns pattern visualization data with Mirror language principles.
        """
        logger.info(
            f"[ForumPatternMap] Generating pattern map for forum {forum_id} "
            f"(requested by {user_id[:8]}...)"
        )

        if not ObjectId.is_valid(forum_id):
            raise HTTPException(status_code=400, detail="Invalid forum_id format")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        # Check membership
        membership = await db.forum_members.find_one({
            "forum_id": forum_id,
            "user_id": user_id,
            "status": "active",
        })

        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this forum")

        try:
            from services.forum_pattern_map import generate_forum_pattern_map

            pattern_map = await generate_forum_pattern_map(db, forum_id)

            logger.info(
                f"[ForumPatternMap] Generated: members={pattern_map['member_count']} "
                f"events={pattern_map['events_total']} "
                f"patterns={len(pattern_map['shared_patterns'])} "
                f"clusters={len(pattern_map['timeline_clusters'])}"
            )

            return pattern_map

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ForumPatternMap] Error: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate forum pattern map")
