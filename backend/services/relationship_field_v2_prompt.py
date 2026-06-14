"""relationship_field_v2_prompt.py — Slice 3 of Relationship Field V2.

Builds the small, gated `RESOLVED RELATIONSHIP FIELD` prompt block for
Ask Mirror. The block is read from the `relationship_field_v2`
envelope already attached to `v2_receipt` by Slice 2.

GUARDRAILS (per user directive — verbatim):
    G3.1 — Only emit when env flag RELATIONSHIP_FIELD_V2_PROMPT == "true".
    G3.2 — Only emit when confidence >= 0.70.
    G3.3 — Only emit when resolution_source ∈ {
              forum_relationship_edges, saved_people,
              relationship_mappings, self_no_target
           }.
    G3.4 — Never emit for resolution_source == "proposed_unresolved".
    G3.5 — Never emit if `conflicts[]` is non-empty.

For low-confidence / proposed_unresolved / conflicted resolutions the
receipt continues to carry the envelope, but no prompt block is
emitted (Slice 2 attachment is unaffected).

NO BACKEND SCHEMA / DB / MIGRATION TOUCHES.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

FLAG_NAME = "RELATIONSHIP_FIELD_V2_PROMPT"

# G3.3 — high-confidence sources allowed to fire the block.
_ALLOWED_SOURCES: set = {
    "forum_relationship_edges",
    "saved_people",
    "relationship_mappings",   # legacy explicit map; resolver maps this
                                # to "explicit_map" — handled below.
    "explicit_map",            # V2 enum name for relationship_mappings
    "self_no_target",
}

# G3.2 — confidence threshold (must match Slice 1's
# `HIGH_CONFIDENCE_THRESHOLD` in `relationship_field_v2.py`).
_CONFIDENCE_THRESHOLD = 0.70


def _flag_enabled() -> bool:
    """Read the env flag fresh each call so tests can flip it at runtime."""
    raw = (os.getenv(FLAG_NAME) or "").strip().lower()
    return raw in ("true", "1", "yes", "on")


def build_relationship_field_v2_prompt_block(
    v2_receipt: Optional[Dict[str, Any]],
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Build the prompt block, if all gates pass.

    Returns (block_text_or_None, debug_dict). The debug dict is suitable
    for attachment to phase4_debug so the dashboard can see exactly why
    the block did or did not fire.
    """
    debug: Dict[str, Any] = {
        "flag_enabled":   _flag_enabled(),
        "reason_skipped": None,
        "stance":         None,
        "role":           None,
        "source":         None,
        "confidence":     None,
        "block_emitted":  False,
    }

    if not v2_receipt:
        debug["reason_skipped"] = "no_v2_receipt"
        return None, debug

    rfv2 = v2_receipt.get("relationship_field_v2")
    if not isinstance(rfv2, dict):
        debug["reason_skipped"] = "no_rfv2_envelope"
        return None, debug

    # Hydrate debug snapshot (so the dashboard sees the values even when
    # we skip).
    debug["stance"]     = rfv2.get("relationship_stance")
    debug["role"]       = rfv2.get("relationship_role")
    debug["source"]     = rfv2.get("resolution_source")
    debug["confidence"] = rfv2.get("confidence")
    debug["frame"]      = rfv2.get("active_frame")

    # G3.1 — flag gate
    if not debug["flag_enabled"]:
        debug["reason_skipped"] = "flag_off"
        return None, debug

    # G3.5 — never emit when there's an unresolved conflict
    conflicts = rfv2.get("conflicts") or []
    if conflicts:
        debug["reason_skipped"] = f"conflicts_present:{len(conflicts)}"
        debug["conflicts"] = conflicts
        return None, debug

    # G3.4 — never emit for proposed_unresolved (low-confidence by nature)
    src = (rfv2.get("resolution_source") or "").strip()
    if src == "proposed_unresolved":
        debug["reason_skipped"] = "source_proposed_unresolved"
        return None, debug

    # G3.3 — allowed-source gate
    if src not in _ALLOWED_SOURCES:
        debug["reason_skipped"] = f"source_not_allowed:{src!r}"
        return None, debug

    # G3.2 — confidence gate
    conf = float(rfv2.get("confidence") or 0.0)
    if conf < _CONFIDENCE_THRESHOLD:
        debug["reason_skipped"] = (
            f"confidence_below_threshold:{conf} < {_CONFIDENCE_THRESHOLD}"
        )
        return None, debug

    # ── All gates passed — emit the block ───────────────────────────
    target_name = rfv2.get("target_name") or rfv2.get("target_user_id") or "—"
    role        = rfv2.get("relationship_role")        or "—"
    stance      = rfv2.get("relationship_stance")      or "—"
    direction   = rfv2.get("directionality")           or "—"
    confidence  = rfv2.get("confidence")
    source      = rfv2.get("resolution_source")        or "—"

    # Self-subject special case: target_name == "—" is fine; we tell the
    # model the user is reflecting on themselves.
    if src == "self_no_target":
        target_name = "(the user themselves)"

    block = (
        "RESOLVED RELATIONSHIP FIELD\n"
        f"Target: {target_name}\n"
        f"Role: {role}\n"
        f"Stance: {stance}\n"
        f"Directionality: {direction}\n"
        f"Confidence: {confidence}\n"
        f"Source: {source}\n"
        "\n"
        "Instruction:\n"
        "Interpret this person through the relationship field above.\n"
        "Do not ignore the relationship context.\n"
        "Do not substitute a generic person profile when role/stance "
        "are high confidence."
    )

    debug["block_emitted"] = True
    debug["block_length"]  = len(block)

    return block, debug
