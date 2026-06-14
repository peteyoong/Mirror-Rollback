"""
Forums Chat routes  (server-router-refactor-v4 → v6)
====================================================

Behaviour-preserving extraction of the forum chat surface from
server.py.  Paths, schemas, log lines, system prompts, rate-limit
window, response shapes, and persistence behaviour are byte-identical.

Endpoints attached:

    GET   /api/forums/{forum_id}/chat/history
    POST  /api/forums/{forum_id}/chat

v6 change — `get_member_lens_data` and `build_forum_dynamics_context`
are no longer passed in via register(); they are imported directly
from `services.forum_lens_helpers`, the single source of truth shared
with forums_intelligence and the (future) extracted forum mirror-chat
router.  The prompt formatters (`format_lens_for_prompt`,
`format_dynamics_for_prompt`) are also imported from there.

Call signature:

    forums_chat.register(api_router, db, logger, emergent_llm_key)
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.forum_lens_helpers import (
    get_member_lens_data,
    build_forum_dynamics_context,
    format_lens_for_prompt,
    format_dynamics_for_prompt,
)


# ---------------------------------------------------------------------------
# Slice B — FORUM_CHAT_AUTO_CONTEXT flag.  When set to "true" the explicit
# `mode` and `target_member_id` request fields become OPTIONAL and the
# request is auto-classified by `services.relationship_field_v2.resolve_…`.
# When unset / "false" / any other value the legacy behaviour is preserved
# byte-for-byte (mode is required, mode=MEMBER requires target_member_id).
# ---------------------------------------------------------------------------
def _forum_chat_auto_context_enabled() -> bool:
    raw = os.environ.get("FORUM_CHAT_AUTO_CONTEXT", "").strip().lower()
    return raw == "true"


# ---------------------------------------------------------------------------
# Mapping from RelationshipField.active_frame → legacy ForumChatMode.
# PAIRWISE   → MEMBER (target_a is primary, target_b travels in context)
# MULTI_PERSON → FORUM (scope_class travels in context)
# ---------------------------------------------------------------------------
_FRAME_TO_LEGACY_MODE: Dict[str, str] = {
    "SELF":         "self",
    "MEMBER":       "member",
    "FORUM":        "forum",
    "PAIRWISE":     "member",
    "MULTI_PERSON": "forum",
}


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
    # Slice B: `mode` is now optional.  When `FORUM_CHAT_AUTO_CONTEXT=true`
    # the resolver decides the effective frame.  When the flag is off and
    # the field is omitted we 400 with the original error.
    mode: Optional[ForumChatMode] = None
    target_member_id: Optional[str] = None
    # Slice B: optional pronoun-memory hint (protects future Slice E).
    last_target_id: Optional[str] = None


# Slice B — Compact context block the FE renders as a chip (no internal
# taxonomy ever bleeds through; this is the SOURCE for the chip but Slice C
# maps it to user-friendly icons + labels).
class ResolvedContextBlock(BaseModel):
    frame:          str               # SELF | MEMBER | FORUM | PAIRWISE | MULTI_PERSON | AMBIGUOUS
    target_user_id: Optional[str] = None
    target_name:    Optional[str] = None
    target_role:    Optional[str] = None         # spouse | child | parent | …
    target_user_id_b: Optional[str] = None       # PAIRWISE only
    target_name_b:    Optional[str] = None       # PAIRWISE only
    scope_class:    Optional[str] = None         # MULTI_PERSON only
    source:         str               # forum_relationship_edges | scope_class | …
    confidence:     float


class ClarificationCandidate(BaseModel):
    user_id:    Optional[str] = None
    name:       str
    role:       Optional[str] = None
    confidence: float
    source:     str


class ForumChatResponse(BaseModel):
    success: bool
    message_id: str
    response: str
    timestamp: str
    # Slice B additive fields — present only when `FORUM_CHAT_AUTO_CONTEXT`
    # is enabled.  When the flag is off these stay `None` so the legacy
    # response shape is preserved byte-for-byte.
    resolved_context: Optional[ResolvedContextBlock] = None
    requires_clarification: bool = False
    clarification_candidates: List[ClarificationCandidate] = []


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
# register() — attach routes onto api_router.
# ---------------------------------------------------------------------------

def register(
    api_router: APIRouter,
    db,
    logger,
    emergent_llm_key: Optional[str],
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
            context_parts.append(format_lens_for_prompt(user_lens))

        if mode == ForumChatMode.MEMBER and target_member_id:
            target_lens = await get_member_lens_data(target_member_id)
            context_parts.append("\n--- TARGET MEMBER PROFILE ---")
            context_parts.append(format_lens_for_prompt(target_lens))

        context_parts.append("\n--- FORUM DYNAMICS SUMMARY ---")
        context_parts.append(format_dynamics_for_prompt(dynamics))

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
            f"mode={request.mode.value if request.mode else 'auto'}"
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

        # ─── Slice B — auto-context resolution (flag-gated) ───────────
        # When `FORUM_CHAT_AUTO_CONTEXT=true`:
        #   * Run the Slice A resolver against the message + viewer graph
        #   * Use the resolved frame to drive `effective_mode` /
        #     `effective_target_id`, overriding the request's `mode` /
        #     `target_member_id`.
        #   * On AMBIGUOUS, return 200 + `requires_clarification=true`
        #     without invoking the LLM.
        # When the flag is off:
        #   * Keep the original "mode is mandatory" contract intact.
        resolved_field = None
        resolved_context_block: Optional[ResolvedContextBlock] = None
        auto_ctx_enabled = _forum_chat_auto_context_enabled()

        # Determine effective_mode / effective_target before we look up
        # `target_member_name`.  These start as the request's literal
        # values and may be overridden by the resolver below.
        effective_mode: Optional[ForumChatMode] = request.mode
        effective_target_id: Optional[str] = request.target_member_id

        if auto_ctx_enabled:
            try:
                from services.relationship_field_v2 import (
                    resolve_relationship_field,
                    ActiveFrame as _ActiveFrame,
                )
                # Pass forum_topology so the resolver can prefer in-forum
                # members for ambiguous names.  The resolver itself is
                # read-only.
                hints: Dict[str, Any] = {
                    "forum_id": forum_id,
                    "forum_topology": {
                        "forum_id": forum_id,
                        "active_member_id": request.target_member_id,
                    },
                }
                if request.last_target_id:
                    hints["last_target_id"] = request.last_target_id
                if request.target_member_id:
                    hints["about_person_id"] = request.target_member_id

                resolved_field = await resolve_relationship_field(
                    db=db,
                    self_user_id=request.user_id,
                    message=request.message,
                    hints=hints,
                )

                # AMBIGUOUS — short-circuit BEFORE any LLM call.
                if resolved_field.active_frame == _ActiveFrame.AMBIGUOUS:
                    logger.info(
                        f"[ForumChat][SliceB] AMBIGUOUS — "
                        f"candidates={len(resolved_field.ambiguity_candidates)} "
                        f"path={resolved_field.resolution_path}"
                    )
                    return ForumChatResponse(
                        success=True,
                        message_id="",
                        response="",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        resolved_context=ResolvedContextBlock(
                            frame="AMBIGUOUS",
                            source=resolved_field.resolution_source,
                            confidence=resolved_field.confidence,
                        ),
                        requires_clarification=True,
                        clarification_candidates=[
                            ClarificationCandidate(
                                user_id=c.get("user_id"),
                                name=c.get("name") or "Unknown",
                                role=c.get("role"),
                                confidence=float(c.get("confidence", 0.0)),
                                source=c.get("source") or "unknown",
                            )
                            for c in resolved_field.ambiguity_candidates[:6]
                        ],
                    )

                # Map frame → legacy mode for the existing context builder.
                legacy_mode = _FRAME_TO_LEGACY_MODE.get(
                    resolved_field.active_frame, "self",
                )
                # Only override the request's mode if it was unset OR the
                # resolver landed on a HIGH-confidence binding.  This
                # guarantees a UI-supplied explicit mode is never silently
                # discarded by a low-confidence resolver call.
                if request.mode is None or resolved_field.confidence >= 0.70:
                    effective_mode = ForumChatMode(legacy_mode)

                # Target override: prefer the resolver's primary target
                # whenever it's set.  Verify forum membership before
                # accepting; if the resolver picked someone outside this
                # forum we demote to SELF so we never leak private info.
                resolver_target_id = resolved_field.target_user_id
                if resolver_target_id and (resolver_target_id != request.user_id):
                    target_in_forum = await db.forum_members.find_one({
                        "forum_id": forum_id,
                        "user_id": resolver_target_id,
                        "status": "active",
                    })
                    if target_in_forum:
                        effective_target_id = resolver_target_id
                    else:
                        logger.info(
                            f"[ForumChat][SliceB] resolver target "
                            f"{resolver_target_id} not a member of forum "
                            f"{forum_id}; demoting to SELF"
                        )
                        effective_mode = ForumChatMode.SELF
                        effective_target_id = None
                        resolved_field.active_frame = _ActiveFrame.SELF
                        resolved_field.target_user_id = None

                # Emit the resolved-context block for the FE chip.
                resolved_context_block = ResolvedContextBlock(
                    frame=resolved_field.active_frame,
                    target_user_id=resolved_field.target_user_id,
                    target_name=resolved_field.target_name,
                    target_role=resolved_field.relationship_role,
                    target_user_id_b=resolved_field.target_user_id_b,
                    target_name_b=resolved_field.target_name_b,
                    scope_class=resolved_field.scope_class,
                    source=resolved_field.resolution_source,
                    confidence=resolved_field.confidence,
                )
                logger.info(
                    f"[ForumChat][SliceB] auto-context resolved: "
                    f"frame={resolved_field.active_frame} "
                    f"target={resolved_field.target_name!r} "
                    f"role={resolved_field.relationship_role!r} "
                    f"source={resolved_field.resolution_source} "
                    f"conf={resolved_field.confidence:.2f} "
                    f"→ legacy_mode={effective_mode.value if effective_mode else None} "
                    f"effective_target={effective_target_id}"
                )
            except Exception as _slice_b_err:  # noqa: BLE001
                logger.warning(
                    f"[ForumChat][SliceB] resolver failed, falling back to "
                    f"legacy mode-driven path: "
                    f"{type(_slice_b_err).__name__}: {_slice_b_err!r}"
                )
                resolved_field = None
                resolved_context_block = None

        # Legacy contract — `mode` is REQUIRED when auto-context is off.
        if effective_mode is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "mode is required (set FORUM_CHAT_AUTO_CONTEXT=true to "
                    "enable automatic mode resolution)"
                ),
            )

        target_member_name: Optional[str] = None
        if effective_mode == ForumChatMode.MEMBER:
            if not effective_target_id:
                raise HTTPException(
                    status_code=400,
                    detail="target_member_id required for member mode",
                )

            target_membership = await db.forum_members.find_one({
                "forum_id": forum_id,
                "user_id": effective_target_id,
                "status": "active",
            })

            if not target_membership:
                raise HTTPException(
                    status_code=404,
                    detail="Target member not found in this forum",
                )

            try:
                target_user = await db.users.find_one({"_id": ObjectId(effective_target_id)})
            except Exception:
                target_user = await db.users.find_one({"_id": effective_target_id})
            target_member_name = target_user.get("name", "Unknown") if target_user else "Unknown"

        try:
            if not emergent_llm_key:
                logger.error("[ForumChat] EMERGENT_LLM_KEY not configured!")
                raise HTTPException(status_code=500, detail="AI service not configured")

            context = await _build_forum_chat_context(
                forum_id=forum_id,
                user_id=request.user_id,
                mode=effective_mode,
                target_member_id=effective_target_id,
            )

            # ── FORUM MIRROR RELATIONAL ORCHESTRATOR V1 ──────────────────
            # forum-mirror-relational-orchestrator-v1
            # Resolves target member, classifies intent, and injects
            # deterministic relational context BEFORE the LLM call so
            # questions like "Mel's 4th house and how does it map to me"
            # don't fall back to textbook astrology.
            orchestrator_payload: Dict[str, Any] = {}
            try:
                from services.forum_mirror_orchestrator import (
                    build_relational_orchestrator_payload,
                )
                orchestrator_payload = await build_relational_orchestrator_payload(
                    db=db,
                    forum_id=forum_id,
                    asker_user_id=request.user_id,
                    message=request.message,
                    mode=effective_mode.value,
                    target_member_id=effective_target_id,
                )
                logger.info(
                    f"[ForumMirrorOrchestrator] frame={orchestrator_payload.get('frame')} "
                    f"intent={orchestrator_payload.get('intent')} "
                    f"house={orchestrator_payload.get('house_number')} "
                    f"life_domain={orchestrator_payload.get('life_domain')!r} "
                    f"target={(orchestrator_payload.get('resolved_target') or {}).get('target_name')!r} "
                    f"role={orchestrator_payload.get('relationship_role')!r} "
                    f"source={orchestrator_payload.get('role_source')!r} "
                    f"spouse_auto={orchestrator_payload.get('spouse_auto_promoted')} "
                    f"layered={orchestrator_payload.get('layered_block_emitted')}"
                )
            except Exception as _orch_err:  # noqa: BLE001
                logger.warning(
                    f"[ForumMirrorOrchestrator] orchestrator failed, "
                    f"falling back to generic prompt: {_orch_err}"
                )
                orchestrator_payload = {}

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

            # ── FKR v1 — Forum Knowledge Retrieval Layer ────────────────
            # Single, deterministic retrieval pass against the graph
            # (charts / users / forum_relationship_edges / forum_members
            #  / forums / pattern_memory / user_timeline) so the LLM
            # answers FACT_LOOKUP / RELATIONSHIP / COMPARISON /
            # TIMELINE / FORUM_DYNAMICS / INTERPRETATION questions from
            # evidence instead of from memory.
            try:
                from services.forum_chat_knowledge_retrieval import (
                    build_fkr_evidence_block,
                )
                _fkr_block, _fkr_debug = await build_fkr_evidence_block(
                    db=db,
                    user_id=request.user_id,
                    message=request.message,
                    forum_id=forum_id,
                )
                if _fkr_block:
                    system_prompt += "\n\n" + _fkr_block
                    logger.info(
                        f"[ForumChat][FKR-v1] block_emitted=True "
                        f"modes={_fkr_debug.get('modes')} "
                        f"targets={[t['name'] for t in _fkr_debug.get('targets', [])]}"
                    )
            except Exception as _fkr_err:
                logger.warning(
                    f"[ForumChat][FKR-v1] failed: "
                    f"{type(_fkr_err).__name__}: {_fkr_err!r}"
                )

            # Inject the orchestrator addendum BEFORE the generic mode
            # hint so the relational framing wins when both apply.
            resolved_target_block = (orchestrator_payload or {}).get("resolved_target")
            if orchestrator_payload.get("system_prompt_addendum"):
                system_prompt += orchestrator_payload["system_prompt_addendum"]

            if effective_mode == ForumChatMode.SELF:
                if resolved_target_block:
                    # User is on Me tab but referenced another member.
                    # Override the generic "asking about themselves"
                    # framing so the LLM treats this as relational.
                    system_prompt += (
                        f"\n\nThe user opened the chat in 'Me' mode but the "
                        f"message references "
                        f"{resolved_target_block.get('target_name')}. "
                        f"Pivot the answer to the field between the user "
                        f"and {resolved_target_block.get('target_name')}. "
                        f"Use the DETERMINISTIC EVIDENCE above.\n"
                    )
                else:
                    system_prompt += "\n\nThe user is asking about THEMSELVES in the context of this forum."
            elif effective_mode == ForumChatMode.MEMBER:
                system_prompt += (
                    f"\n\nThe user is asking about another member ({target_member_name}). "
                    f"Use the DETERMINISTIC EVIDENCE above. Be respectful and "
                    f"answer from the field between the user and "
                    f"{target_member_name}, not in isolation."
                )
            else:  # FORUM mode
                system_prompt += "\n\nThe user is asking about the FORUM GROUP DYNAMICS as a whole."

            # ── Slice B — pairwise / multi-person framing hint ─────────
            # When the resolver landed on PAIRWISE or MULTI_PERSON we add
            # a small additional directive WITHOUT exposing the internal
            # taxonomy to the LLM (Mirror voice only, no jargon).
            if resolved_field is not None:
                if resolved_field.active_frame == "PAIRWISE" and resolved_field.target_name_b:
                    system_prompt += (
                        f"\n\nThe user is asking about the relationship "
                        f"between {resolved_field.target_name} and "
                        f"{resolved_field.target_name_b}.  Answer from the "
                        f"field BETWEEN them, not about either one in "
                        f"isolation."
                    )
                elif resolved_field.active_frame == "MULTI_PERSON":
                    scope_label = (resolved_field.scope_class or "").replace("_", " ")
                    if scope_label:
                        system_prompt += (
                            f"\n\nThe user is asking about a group within "
                            f"the forum (scope: {scope_label}).  Answer "
                            f"from the shared field across these people, "
                            f"not from any single profile in isolation."
                        )

            from emergent_contract import emergent_generate
            from llm_model_config import get_primary_model

            try:
                response_text = await asyncio.wait_for(
                    emergent_generate(
                        mode="reflection_chat",
                        user_message=request.message,
                        endpoint="forum_chat",
                        user_id=request.user_id,
                        context={"forum_id": forum_id, "mode": effective_mode.value},
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

            # ── V8 token-anchor enforcement ──────────────────────────────
            # forum-mirror-relational-orchestrator-v1 + astrology-field-synthesis-v8-anchor
            # When the orchestrator ran V8 field synthesis, append a
            # deterministic "Behind this field:" anchor if the LLM
            # dropped required tokens (house sign, ruler, ruler sign,
            # ruler house, destabilizer, notable hard aspects).
            try:
                _v8_synth_full = (
                    orchestrator_payload.get("debug", {}).get("_v8_synth_full")
                    if orchestrator_payload else None
                )
                if (
                    isinstance(response_text, str)
                    and isinstance(_v8_synth_full, dict)
                    and _v8_synth_full.get("success")
                ):
                    def _ord_v8(n):
                        if not n:
                            return ""
                        suf = "th" if 11 <= (n % 100) <= 13 else \
                              {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
                        return f"{n}{suf}"

                    house_n  = _v8_synth_full.get("house_number")
                    house_s  = _v8_synth_full.get("house_sign") or ""
                    ruler    = _v8_synth_full.get("ruler") or ""
                    ruler_s  = _v8_synth_full.get("ruler_sign") or ""
                    ruler_h  = _v8_synth_full.get("ruler_house")
                    destab   = _v8_synth_full.get("destabilizing_planet") or ""
                    aspects  = _v8_synth_full.get("ruler_aspects") or []

                    lower = response_text.lower()
                    missing: List[str] = []
                    if house_s and house_s.lower() not in lower:
                        missing.append("sign")
                    house_ord = _ord_v8(house_n).lower()
                    if house_ord and house_ord not in lower and f"house {house_n}" not in lower:
                        missing.append("house")
                    if ruler and ruler.lower() not in lower:
                        missing.append("ruler")
                    if destab and destab.lower() not in lower:
                        missing.append("destab")

                    # Hard-aspect phrases to loud bodies (square/opp/conj)
                    _hard_types = {"square", "opposition", "conjunction"}
                    _loud_others = {"Saturn", "Uranus", "Neptune", "Pluto",
                                    "Chiron", "Mars", "Jupiter"}
                    notable_aspect_phrases: List[str] = []
                    for a in aspects:
                        if not isinstance(a, dict):
                            continue
                        other = a.get("with") or ""
                        typ = a.get("type") or ""
                        if not other or not typ:
                            continue
                        if typ.lower() in _hard_types and other in _loud_others:
                            loose_present = (
                                other.lower() in lower and typ.lower() in lower
                            )
                            if not loose_present:
                                notable_aspect_phrases.append(f"{ruler}–{other} {typ}")
                    notable_aspect_phrases = notable_aspect_phrases[:3]
                    if notable_aspect_phrases:
                        missing.append("aspects")

                    if missing:
                        anchor_bits: List[str] = []
                        if house_s and house_n:
                            anchor_bits.append(
                                f"{house_s} on the {_ord_v8(house_n)} house cusp"
                            )
                        if destab and house_n:
                            anchor_bits.append(
                                f"{destab} tenanted in the {_ord_v8(house_n)}"
                            )
                        if ruler and ruler_s and ruler_h:
                            anchor_bits.append(
                                f"{ruler} (the ruler) in {ruler_s} in the {_ord_v8(ruler_h)} house"
                            )
                        elif ruler:
                            anchor_bits.append(f"{ruler} as the ruler")
                        if notable_aspect_phrases:
                            anchor_bits.append("with " + ", ".join(notable_aspect_phrases))
                        if anchor_bits:
                            anchor = "Behind this field: " + "; ".join(anchor_bits) + "."
                            sep = "\n\n" if not response_text.endswith("\n") else ""
                            response_text = response_text.rstrip() + sep + anchor
                            logger.info(
                                f"[ForumMirrorOrchestrator] V8 anchor appended; "
                                f"missing={missing}"
                            )
            except Exception as _v8_post_err:  # noqa: BLE001
                logger.debug(
                    f"[ForumMirrorOrchestrator] V8 anchor skipped: {_v8_post_err}"
                )

            message_doc = {
                "forum_id": forum_id,
                "user_id": request.user_id,
                "mode": effective_mode.value,
                "target_member_id": effective_target_id,
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
                resolved_context=resolved_context_block,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ForumChat] Error: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process chat request")
