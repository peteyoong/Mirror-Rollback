"""
Mirror Chat Pipeline  (server-router-refactor-v7)
=================================================

Thin, behaviour-preserving stage functions extracted from the
/api/mirror/chat handler in server.py.  v7 ONLY hoists the stage
logic into named functions — the route itself remains in server.py
and continues to call each stage in the exact same order.

This file is the prep step for v8, when /api/mirror/chat will be
extracted into routers/mirror_chat.py.  Until then nothing about
the request/response shape, debug payload, system prompt, or
persistence ordering changes.

Each stage returns a tuple of:

    (system_prompt_block: Optional[str], debug_payload: Optional[dict])

The route appends ``system_prompt_block`` (when truthy) to its
``system_prompt`` and surfaces ``debug_payload`` in the chat
response under the same keys it always has.  Stages that don't
produce a block return ``None`` for one or both elements.

All stages swallow internal exceptions exactly like the inline
versions did — the chat must NEVER crash because of a memory /
relational / contradiction layer error.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage: Lens context  (multi-lens-chat-memory-v1)
# ---------------------------------------------------------------------------

async def build_lens_context(
    *,
    lens: Optional[str],
    user: Optional[dict],
    chart: Optional[dict],
    enneagram_results: Optional[dict],
    bazi_chart: Optional[dict],
    numerology_cycles: Optional[dict],
    user_message: str,
    history: List[dict],
    user_id: str,
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Compose the multi-lens conversational memory block for the active lens
    (astrology / human_design / numerology / enneagram / bazi / zi_wei).
    Returns (memory_block, lens_debug_payload).  Returns (None, None) when
    the request is not in a lens-constrained mode or the registry has no
    entry for the lens.
    """
    if lens not in ("astrology", "human_design", "numerology", "enneagram", "bazi", "zi_wei"):
        return None, None

    try:
        from services.lens_registries import get_registry
        from services.lens_conversation import compose_lens_memory_blocks

        registry = get_registry(lens)
        if registry is None:
            return None, None

        user_context: Dict[str, Any] = {
            "user": user,
            "chart": chart,
            "enneagram_results": enneagram_results,
            "bazi_chart": bazi_chart,
        }
        if lens == "numerology" and numerology_cycles is not None:
            user_context["numerology_cycles"] = numerology_cycles

        memory_block, lens_debug_payload = compose_lens_memory_blocks(
            registry=registry,
            user_context=user_context,
            user_message=user_message,
            history=history,
            max_history_turns=6,
        )

        logger.info(
            f"[MIRROR_CHAT][multi-lens-chat-memory-v1] "
            f"lens={lens} "
            f"active_entity={(lens_debug_payload or {}).get('active_entity')} "
            f"source={(lens_debug_payload or {}).get('active_entity_source')} "
            f"depth_mode={(lens_debug_payload or {}).get('depth_mode')} "
            f"intensity_mode={(lens_debug_payload or {}).get('intensity_mode')} "
            f"grounding={len((lens_debug_payload or {}).get('grounding_sources', []))} "
            f"missing={len((lens_debug_payload or {}).get('missing_sources', []))} "
            f"history_len={len(history)}"
        )
        return memory_block, lens_debug_payload
    except Exception as lens_mem_err:
        logger.error(
            f"[MIRROR_CHAT][multi-lens-chat-memory-v1] memory layer error for lens={lens}: "
            f"{type(lens_mem_err).__name__}: {lens_mem_err}"
        )
        return None, None


# ---------------------------------------------------------------------------
# Stage: Life Tab master voice  (life-tab-master-voice-v1)
# ---------------------------------------------------------------------------

async def build_life_domain_context(
    *,
    life_domain: Optional[str],
    lens: Optional[str],
    user: Optional[dict],
    chart: Optional[dict],
    enneagram_results: Optional[dict],
    bazi_chart: Optional[dict],
    user_message: str,
    history: List[dict],
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Compose the Life Tab Master Voice integrative block when the chat is
    on a Life Tab surface (life_domain ∈ {"relationships","work","self"})
    and not constrained to a single lens.
    """
    if life_domain not in ("relationships", "work", "self"):
        return None, None
    if lens in ("astrology", "human_design", "numerology", "enneagram", "bazi", "zi_wei"):
        return None, None

    try:
        from services.life_tab_master import compose_master_voice_blocks

        user_context_mv = {
            "user": user,
            "chart": chart,
            "enneagram_results": enneagram_results,
            "bazi_chart": bazi_chart,
        }
        mv_block, master_voice_debug_payload = compose_master_voice_blocks(
            user_context=user_context_mv,
            domain=life_domain,
            user_message=user_message,
            history=history,
            max_history_turns=6,
        )
        logger.info(
            f"[MIRROR_CHAT][life-tab-master-voice-v1] "
            f"domain={life_domain} "
            f"frameworks={(master_voice_debug_payload or {}).get('contributing_frameworks')} "
            f"signals={(master_voice_debug_payload or {}).get('signals_count')} "
            f"depth={(master_voice_debug_payload or {}).get('depth_mode')} "
            f"intensity={(master_voice_debug_payload or {}).get('intensity_mode')}"
        )
        return mv_block, master_voice_debug_payload
    except Exception as mv_err:
        logger.error(
            f"[MIRROR_CHAT][life-tab-master-voice-v1] error: "
            f"{type(mv_err).__name__}: {mv_err}"
        )
        return None, None


# ---------------------------------------------------------------------------
# Stage: Relational awareness  (relational-awareness-v1)
# ---------------------------------------------------------------------------

async def build_relational_context(
    *,
    db,
    user_id: str,
    about_person_id: Optional[str],
    user_message: str,
    history: List[dict],
    lens_debug_payload: Optional[dict],
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Compose the Relational Awareness block when the chat is about a saved
    person.  This may also CAP intensity in `lens_debug_payload` (mutated
    in place — same behaviour as the inline version).
    """
    if not about_person_id:
        return None, None

    try:
        from services.relational_awareness import compose_relational_block

        person_doc = await db.saved_people.find_one({
            "id": about_person_id,
            "user_id": user_id,
        })
        if not person_doc:
            logger.warning(
                f"[MIRROR_CHAT][relational-awareness-v1] "
                f"about_person_id={about_person_id} not found for user={user_id}"
            )
            return None, None

        person_for_block = {
            "id": person_doc.get("id"),
            "name": person_doc.get("name"),
            "relationship_type": person_doc.get("relationship_type"),
            "full_birth_name": person_doc.get("full_birth_name"),
            "birth_date": person_doc.get("birth_date"),
            "birth_location": person_doc.get("birth_location") or {},
            "enneagram_type": person_doc.get("enneagram_type"),
        }
        lens_intensity = (lens_debug_payload or {}).get("intensity_mode") or "OBSERVATIONAL"
        rel_block, relational_debug_payload, applied_intensity = compose_relational_block(
            person=person_for_block,
            user_message=user_message,
            history=history,
            lens_intensity_mode=lens_intensity,
        )
        # Mutate lens debug in place when relational layer capped intensity.
        if lens_debug_payload is not None and applied_intensity != lens_intensity:
            lens_debug_payload["intensity_mode"] = applied_intensity
            lens_debug_payload["intensity_capped_by_relational"] = True
        logger.info(
            f"[MIRROR_CHAT][relational-awareness-v1] "
            f"person={person_for_block.get('name')} "
            f"class={(relational_debug_payload or {}).get('relationship_class')} "
            f"projection_risk={(relational_debug_payload or {}).get('projection_risk')} "
            f"intensity={lens_intensity}->{applied_intensity}"
        )
        return rel_block, relational_debug_payload
    except Exception as rel_err:
        logger.error(
            f"[MIRROR_CHAT][relational-awareness-v1] error: "
            f"{type(rel_err).__name__}: {rel_err}"
        )
        return None, None


# ---------------------------------------------------------------------------
# Stage: Longitudinal pattern memory  (pattern-memory-v1)
# ---------------------------------------------------------------------------

async def build_pattern_memory_context(
    *,
    db,
    user_id: str,
    user_message: str,
    lens: Optional[str],
    lens_debug_payload: Optional[dict],
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Detect abstracted pattern tags + maybe inject a PATTERN MEMORY block.
    """
    try:
        from services.longitudinal_pattern_memory import process_pattern_memory
        current_intensity = (
            (lens_debug_payload or {}).get("intensity_mode")
            or "OBSERVATIONAL"
        )
        pattern_block, pattern_debug_payload = await process_pattern_memory(
            db=db,
            user_id=user_id,
            user_message=user_message,
            lens=lens,
            intensity_mode=current_intensity,
            domain=None,
        )
        if pattern_debug_payload and pattern_debug_payload.get("matched_patterns"):
            logger.info(
                f"[MIRROR_CHAT][pattern-memory-v1] "
                f"user={user_id} "
                f"matched={len(pattern_debug_payload['matched_patterns'])} "
                f"surfaced={pattern_debug_payload['surfaceable_count']} "
                f"growth={pattern_debug_payload['growth_shifts_count']}"
            )
        return pattern_block, pattern_debug_payload
    except Exception as pat_err:
        logger.error(
            f"[MIRROR_CHAT][pattern-memory-v1] error: "
            f"{type(pat_err).__name__}: {pat_err}"
        )
        return None, None


# ---------------------------------------------------------------------------
# Stage: Micro-reflection loop  (micro-reflection-v2)
# ---------------------------------------------------------------------------

async def build_micro_reflection_context(
    *,
    db,
    user_id: str,
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Read recent micro-reflections and inject a SOFT system block when a
    clear signal exists (loop, growth, resistance).
    """
    try:
        from services.micro_reflection_v2 import compose_reflection_loop_block
        r_block, reflection_debug_payload = await compose_reflection_loop_block(
            db=db, user_id=user_id,
        )
        if r_block:
            logger.info(
                f"[MIRROR_CHAT][micro-reflection-v2] "
                f"user={user_id} "
                f"loop={reflection_debug_payload.get('loop_applied')} "
                f"growth={reflection_debug_payload.get('growth_score')} "
                f"resistance={reflection_debug_payload.get('resistance_score')}"
            )
        return r_block, reflection_debug_payload
    except Exception as ref_err:
        logger.error(
            f"[MIRROR_CHAT][micro-reflection-v2] error: "
            f"{type(ref_err).__name__}: {ref_err}"
        )
        return None, None


# ---------------------------------------------------------------------------
# Stage: Contradiction intelligence  (contradiction-intelligence-v1)
# ---------------------------------------------------------------------------

async def build_contradiction_context(
    *,
    db,
    user_id: str,
    user_message: str,
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Compute soft divergences between stated language and recurring signals.
    Returns (system_block, debug_payload).  Only MODERATE / STRONG surface.
    """
    try:
        from services.contradiction_intelligence import (
            compute_individual_contradictions,
            build_contradiction_system_block,
            build_contradiction_debug,
        )
        _contra = await compute_individual_contradictions(
            db, user_id=user_id, message_text=user_message,
        )
        contradiction_debug_payload = build_contradiction_debug(_contra)
        _c_block = build_contradiction_system_block(_contra)
        if _c_block:
            logger.info(
                f"[MIRROR_CHAT][contradiction-intelligence-v1] "
                f"user={user_id} level={_contra.get('level')} "
                f"types={_contra.get('types')} "
                f"softened={_contra.get('softened_by_reflection')}"
            )
        return _c_block, contradiction_debug_payload
    except Exception as ci_err:
        logger.error(
            f"[MIRROR_CHAT][contradiction-intelligence-v1] error: "
            f"{type(ci_err).__name__}: {ci_err}"
        )
        return None, None
