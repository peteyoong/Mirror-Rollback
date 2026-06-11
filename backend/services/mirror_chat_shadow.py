"""mirror_chat_shadow.py — Slice B1 shadow-mode glue.

Fire-and-forget wrapper that:
  1. Runs `classify_intent_v2` and `resolve_relationship_context` against
     the incoming request *in parallel* with the real LLM pipeline.
  2. Builds a `retrieval_validation_v1` receipt with a simulated set of
     mandatory modules (because the real pipeline hasn't been refactored
     to emit module IDs yet — that's Slice B3).
  3. Persists the receipt to `mirror_chat_retrieval_receipts` and logs a
     single line for live dashboarding.

NEVER touches the response.  Disabled with INTENT_ROUTER_V2_SHADOW=false.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from services.intent_router_v2 import (
    classify_intent_v2,
    shadow_mode_enabled,
)
from services.relationship_router_v2 import resolve_relationship_context
from services.retrieval_validation_v1 import (
    build_receipt,
    format_log_line,
    mandatory_modules,
    persist_receipt,
)

log = logging.getLogger("mirror_chat_shadow")


def _derive_frame(lens: Optional[str], life_domain: Optional[str],
                  about_person_id: Optional[str]) -> str:
    """Approximate the user's frame from request fields."""
    if about_person_id:
        return "member"  # talking about a saved person
    if (life_domain or "").lower() in ("relationships", "relationship"):
        return "forum" if False else "self"  # life-domain "self frame"
    return "self"


async def emit_shadow_receipt(
    *, db,
    request_id: str,
    user_id: str,
    message: str,
    lens: Optional[str] = None,
    about_person_id: Optional[str] = None,
    life_domain: Optional[str] = None,
    saved_people: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Run the V2 routers against this request and persist a receipt.

    Always wrapped in try/except so a routing bug never breaks production.
    """
    if not shadow_mode_enabled():
        return

    t0 = time.perf_counter()
    try:
        frame = _derive_frame(lens, life_domain, about_person_id)

        # Resolve target FIRST so we can feed its role back into the
        # intent classifier (lets "What enneagram pattern does Mel
        # show up with?" bias toward relationship via role=partner).
        #
        # NOTE (B2): we now always run the resolver, even when no
        # about_person_id and no saved_people are present, because the
        # missing-target fallback path detects proper names in the
        # message itself and emits a receipt-only proposed_action.
        rel = None
        resolved_target_id = about_person_id
        resolved_role: Optional[str] = None
        try:
            rel_resolved = resolve_relationship_context(
                self_user_id=user_id,
                user_message=message or "",
                active_frame=frame,
                target_id=about_person_id,
                saved_people=saved_people or [],
            )
            rel = rel_resolved.to_dict()
            resolved_target_id = rel_resolved.target or about_person_id
            resolved_role = rel_resolved.role
        except Exception as e:
            log.warning(f"[Shadow] relationship_router_v2 failed: {e!r}")

        envelope = classify_intent_v2(
            message=message or "",
            active_frame=frame,
            current_target_id=resolved_target_id,
            relationship_role=resolved_role,
        )

        envd = envelope.to_dict()
        # Simulated module-invocation set — real wiring lands in B3.
        modules = mandatory_modules(envd["primary_domain"])
        receipt = build_receipt(
            request_id=request_id,
            intent_envelope=envd,
            relationship_resolution=rel,
            modules_invoked=modules,
            payloads={m: {"sim": True} for m in modules},
        )
        # Annotate that this is shadow-mode (no real retrieval was done).
        receipt["shadow_mode"] = True
        receipt["shadow_latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        receipt["frame_source"] = {
            "lens": lens,
            "life_domain": life_domain,
            "derived_frame": frame,
        }
        receipt["user_id"] = user_id

        if db is not None:
            await persist_receipt(db, receipt)
        log.info(format_log_line(receipt))
    except Exception as e:
        log.warning(f"[Shadow] intent_router_v2 shadow emit failed: "
                    f"{type(e).__name__}: {e}")


def make_request_id() -> str:
    return f"mc-{uuid.uuid4()}"
