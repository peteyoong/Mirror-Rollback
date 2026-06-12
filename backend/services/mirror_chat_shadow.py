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
    cutover_decision_for,
    shadow_mode_enabled,
)
from services.relationship_router_v2 import resolve_relationship_context
from services.cross_lens_synthesis_v2 import compute_synthesis_v2
from services.relationship_orchestration_v1 import plan_lens_priority
from services.retrieval_validation_v1 import (
    build_receipt,
    format_log_line,
    mandatory_modules,
    persist_receipt,
)

log = logging.getLogger("mirror_chat_shadow")


def _derive_frame(lens: Optional[str], life_domain: Optional[str],
                  about_person_id: Optional[str],
                  forum_topology: Optional[Dict[str, Any]] = None) -> str:
    """Approximate the user's frame from request fields.

    P4: when `forum_topology.active_member_id` is supplied we promote the
    frame to `"forum"` so the resolver's forum-default path engages
    (binds the active member as the relationship target).
    """
    if forum_topology and (forum_topology.get("active_member_id")
                           or forum_topology.get("forum_id")):
        return "forum"
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
    forum_topology: Optional[Dict[str, Any]] = None,
) -> None:
    """Run the V2 routers against this request and persist a receipt.

    Always wrapped in try/except so a routing bug never breaks production.
    """
    if not shadow_mode_enabled():
        return

    t0 = time.perf_counter()
    try:
        frame = _derive_frame(lens, life_domain, about_person_id, forum_topology)

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
                forum_topology=forum_topology,
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
            # P4 visibility — was forum_topology supplied at the call site?
            "forum_topology_supplied": bool(forum_topology),
            "forum_topology_active_member_id": (
                (forum_topology or {}).get("active_member_id")
            ),
        }
        receipt["user_id"] = user_id

        # ──────────────────────────────────────────────────────────────
        # Stage 1 rollout telemetry  (intent-router-v2-stage1-v1)
        #
        # Records the per-user cutover decision in EVERY receipt so the
        # dashboard can verify:
        #   * Bucket distribution is uniform across users
        #   * `cutover_decision.enabled` == False for ALL users while
        #     CUTOVER=false AND ROLLOUT_PERCENT=0  (current state)
        #   * After flipping ROLLOUT_PERCENT=10, ~10% of unique users
        #     get `enabled=True` and ~90% get `enabled=False` (only one
        #     decision per user — sticky bucket).
        #
        # SHADOW MODE: this decision is recorded but NEVER acted on by
        # the live request handler. The cutover flip happens later, in
        # a separate (explicit) operation.
        # ──────────────────────────────────────────────────────────────
        try:
            decision = cutover_decision_for(user_id)
        except Exception as e:
            log.warning(f"[Shadow] cutover_decision_for failed: {e!r}")
            decision = {
                "enabled":         False,
                "reason":          "decision_error",
                "stage1_bucket":   -1,
                "rollout_percent": 0,
                "cutover_flag":    False,
                "salt":            None,
            }
        receipt["stage1_bucket"] = decision["stage1_bucket"]
        receipt["cutover_decision"] = decision

        # ──────────────────────────────────────────────────────────────
        # Cross-Lens Synthesis Phase 2  (cross_lens_synthesis_v2.1.0)
        #
        # Receipt-only enrichment that surfaces agreement / tension /
        # polarity patterns across the lens space. ADDITIVE: existing
        # lens outputs (`lens_payloads`, `lens_priority`,
        # `intent_envelope`) are preserved verbatim.
        # Never raises (helper catches its own errors and returns a
        # `computed=false` payload instead).
        # ──────────────────────────────────────────────────────────────
        try:
            receipt["cross_lens_synthesis_v2"] = compute_synthesis_v2(
                intent_envelope=envd, message=message,
            )
        except Exception as _cl_exc:
            log.warning(f"[Shadow] cross_lens_synthesis_v2 failed: {_cl_exc!r}")
            receipt["cross_lens_synthesis_v2"] = {
                "version": "cross_lens_synthesis_v2.1.0",
                "computed": False,
                "error": f"{type(_cl_exc).__name__}: {_cl_exc!s}",
                "lens_outputs_preserved": True,
            }

        # ──────────────────────────────────────────────────────────────
        # P3 — Relationship-Aware Lens Orchestration (v1.0.0)
        #
        # Receipt-only enrichment that re-prioritizes the lens stack
        # based on the resolved relationship context (spouse / child /
        # cofounder / forum_member / self). ADDITIVE: the live response
        # still reads `lens_priority` from the intent envelope. This
        # plan is recorded for dashboard observation only.
        # ──────────────────────────────────────────────────────────────
        try:
            receipt["relationship_orchestration_v1"] = plan_lens_priority(
                intent_envelope=envd,
                relationship_role=resolved_role,
                target_resolved=resolved_target_id,
                forum_topology=forum_topology,
                context_mode=lens or life_domain,
            )
        except Exception as _ro_exc:
            log.warning(f"[Shadow] relationship_orchestration_v1 failed: {_ro_exc!r}")
            receipt["relationship_orchestration_v1"] = {
                "version":  "relationship_orchestration_v1.0.0",
                "computed": False,
                "error":    f"{type(_ro_exc).__name__}: {_ro_exc!s}",
                "lens_outputs_preserved": True,
            }

        # ──────────────────────────────────────────────────────────────
        # P4 v2 — Forum-topology resolution telemetry.
        # Captures how the topology was used, frame-disambiguation
        # signal, and topology breadth so dashboards can monitor P4
        # plumbing health on real traffic. Receipt-only.
        # ──────────────────────────────────────────────────────────────
        try:
            _topology_members = (forum_topology or {}).get("members") or []
            _active_id = (forum_topology or {}).get("active_member_id")
            _active_found = bool(
                _active_id and any(
                    m.get("id") == _active_id for m in _topology_members
                )
            )
            # Frame disambiguation — was the resolver's frame consistent
            # with the topology presence? Surfaces forum-vs-self drift.
            _frame_consistent = (
                (frame == "forum" and bool(_active_id))
                or (frame != "forum" and not _active_id)
            )
            receipt["forum_topology_resolution"] = {
                "topology_supplied":        bool(forum_topology),
                "active_member_id":         _active_id,
                "active_member_in_members": _active_found,
                "topology_member_count":    len(_topology_members),
                "resolver_frame":           frame,
                "frame_consistent":         _frame_consistent,
            }
        except Exception as _ft_exc:
            log.warning(f"[Shadow] forum_topology_resolution failed: {_ft_exc!r}")
            receipt["forum_topology_resolution"] = {
                "topology_supplied": bool(forum_topology),
                "error": f"{type(_ft_exc).__name__}: {_ft_exc!s}",
            }

        if db is not None:
            await persist_receipt(db, receipt)
        log.info(format_log_line(receipt))
    except Exception as e:
        log.warning(f"[Shadow] intent_router_v2 shadow emit failed: "
                    f"{type(e).__name__}: {e}")


def make_request_id() -> str:
    return f"mc-{uuid.uuid4()}"
