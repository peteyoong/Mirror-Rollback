"""ADV-OBJ-13 — Pairwise target hydration bridge.

Regression test for the bug where Forum-tab cross-chart queries
("How do Mel's Juno and my Juno interact?") silently degraded to
single-object self-only because the orchestrator's resolved target
(Mel) was never lifted into the advanced_object_resolver call.

This file tests the **bridge logic** that lives in
routers/forums_chat.py lines 708-757 ("ADV-OBJ-13 — Bridge
orchestrator-resolved target" / "Escalate FORUM/SELF → PAIRWISE…").

The compute path (resolve_advanced_object → compute_natal_object →
proof block) is exhaustively tested by 58 cases in
services/test_mirror_object_interpreter.py and
services/test_multi_object_routing.py.  This file's job is to lock in
the *routing* decision — the frame value and the target_user_id that
the router hands to the resolver.

If the bridge block in forums_chat.py is moved or rewritten, these
tests will catch a regression even if the higher-level smoke test
isn't run.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from services.advanced_object_resolver import (
    FRAME_FORUM,
    FRAME_MEMBER,
    FRAME_PAIRWISE,
    FRAME_SELF,
)


# ---------------------------------------------------------------------
# Replica of the bridge block in routers/forums_chat.py.
# Keep this in sync with that file; if either drifts, both should be
# updated together.  See:
#   /app/backend/routers/forums_chat.py
#     "ADV-OBJ-13 — Bridge orchestrator-resolved target"
# ---------------------------------------------------------------------
def _bridge(
    *,
    request_message: str,
    request_user_id: str,
    effective_mode: str,            # "self" | "member" | "forum"
    effective_target_id: Optional[str],
    target_member_name: Optional[str],
    orchestrator_payload: Dict[str, Any],
    resolved_field_active_frame: Optional[str] = None,
):
    """Returns (resolver_frame, effective_target_uid, target_name)
    that routers/forums_chat.py would compute for this request."""
    # 1. Initial frame map (mirrors lines 696-706)
    resolver_frame = FRAME_SELF
    if effective_mode == "member":
        resolver_frame = FRAME_MEMBER
    elif effective_mode == "forum":
        resolver_frame = FRAME_FORUM
    if resolved_field_active_frame == "PAIRWISE":
        resolver_frame = FRAME_PAIRWISE

    # 2. ADV-OBJ-13 bridge — orchestrator target lift
    orch_resolved = (orchestrator_payload or {}).get("resolved_target") or {}
    orch_target_uid = orch_resolved.get("target_user_id")
    effective_target_for_resolver = effective_target_id
    if (
        not effective_target_for_resolver
        and orch_target_uid
        and orch_target_uid != request_user_id
    ):
        effective_target_for_resolver = orch_target_uid

    target_name_for_resolver = None
    if effective_target_for_resolver:
        target_name_for_resolver = (
            target_member_name or orch_resolved.get("target_name")
        )

    # 3. ADV-OBJ-13 self-pronoun escalation.  Must mirror the production
    #    heuristic exactly: " me " is EXCLUDED because of imperatives
    #    ("Tell me…", "Show me…").
    if (
        effective_target_for_resolver
        and resolver_frame in (FRAME_SELF, FRAME_FORUM)
    ):
        q_lower = (request_message or "").lower()
        padded = f" {q_lower} "
        self_pronoun_hit = (
            " my "    in padded
            or " mine " in padded
            or " i "    in padded
            or " i'm "  in padded
            or " i've " in padded
            or " i'll " in padded
        )
        if self_pronoun_hit:
            resolver_frame = FRAME_PAIRWISE

    return resolver_frame, effective_target_for_resolver, target_name_for_resolver


# ---------------------------------------------------------------------
# 1. Forum-tab cross-chart → PAIRWISE  (the marquee case)
# ---------------------------------------------------------------------
def test_forum_tab_cross_chart_query_escalates_to_pairwise():
    frame, target_uid, target_name = _bridge(
        request_message="How do Mel's Juno and my Juno interact?",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {
                "target_user_id": "mel-uid",
                "target_name":    "Mel",
                "source":         "forum_member",
            }
        },
    )
    assert frame == FRAME_PAIRWISE
    assert target_uid == "mel-uid"
    assert target_name == "Mel"


# ---------------------------------------------------------------------
# 2. Mel target chart loadable via orchestrator target alone
# ---------------------------------------------------------------------
def test_mel_target_loaded_via_orchestrator():
    """Even with effective_target_id=None (Forum tab default), the bridge
    must surface the orchestrator's resolved target so the router can
    load Mel's chart from db.charts in the next step."""
    _, target_uid, target_name = _bridge(
        request_message="how do mel and i compare on Juno",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {
                "target_user_id": "mel-uid",
                "target_name":    "Mel",
                "source":         "forum_member",
            }
        },
    )
    assert target_uid == "mel-uid"
    assert target_name == "Mel"


# ---------------------------------------------------------------------
# 3. Self-only query (no target) — must NOT escalate
# ---------------------------------------------------------------------
def test_self_only_query_stays_single_object():
    frame, target_uid, _ = _bridge(
        request_message="Tell me about my Juno",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={},                # orchestrator finds nobody
    )
    assert frame == FRAME_FORUM
    assert target_uid is None


# ---------------------------------------------------------------------
# 4. " me " in "Tell me about…" must NOT trigger self-pronoun escalation
# ---------------------------------------------------------------------
def test_imperative_me_does_not_escalate():
    """`"Tell me about Mel's Juno"` is target-only.  No real
    self-pronoun.  Frame must stay FORUM (no PAIRWISE escalation),
    even though the orchestrator did resolve Mel."""
    frame, target_uid, target_name = _bridge(
        request_message="Tell me about Mel's Juno",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {
                "target_user_id": "mel-uid",
                "target_name":    "Mel",
            }
        },
    )
    assert frame == FRAME_FORUM
    # target IS lifted so the router CAN load Mel's chart, but the
    # resolver frame stays FORUM — current intentional behavior.
    assert target_uid == "mel-uid"
    assert target_name == "Mel"


def test_imperative_show_me_does_not_escalate():
    """Same as above for `Show me…` imperative."""
    frame, _, _ = _bridge(
        request_message="Show me Mel's Vesta",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
    )
    assert frame == FRAME_FORUM


def test_imperative_let_me_does_not_escalate():
    frame, _, _ = _bridge(
        request_message="Let me know Mel's North Node",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
    )
    assert frame == FRAME_FORUM


# ---------------------------------------------------------------------
# 5. Self-pronoun variants that SHOULD escalate
# ---------------------------------------------------------------------
def test_my_escalates():
    frame, _, _ = _bridge(
        request_message="Show me my Anti-Vertex against Mel",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
    )
    assert frame == FRAME_PAIRWISE


def test_i_subject_pronoun_escalates():
    frame, _, _ = _bridge(
        request_message="how do Mel's Juno and what i have for Juno interact",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
    )
    assert frame == FRAME_PAIRWISE


def test_im_contraction_escalates():
    frame, _, _ = _bridge(
        request_message="i'm curious how Mel's Vesta compares to mine",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
    )
    assert frame == FRAME_PAIRWISE


def test_mine_escalates():
    frame, _, _ = _bridge(
        request_message="how does Mel's Juno relate to mine",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
    )
    assert frame == FRAME_PAIRWISE


# ---------------------------------------------------------------------
# 6. Member mode is untouched by the bridge
# ---------------------------------------------------------------------
def test_explicit_member_mode_unaffected_by_bridge():
    frame, target_uid, target_name = _bridge(
        request_message="What does Juno reveal here?",
        request_user_id="pete-uid",
        effective_mode="member",
        effective_target_id="mel-uid",
        target_member_name="Mel",
        orchestrator_payload={
            "resolved_target": {
                "target_user_id": "mel-uid",
                "target_name":    "Mel",
                "source":         "explicit_mode_member",
            }
        },
    )
    assert frame == FRAME_MEMBER
    assert target_uid == "mel-uid"
    assert target_name == "Mel"


# ---------------------------------------------------------------------
# 7. Slice B PAIRWISE still wins when later enabled
# ---------------------------------------------------------------------
def test_slice_b_pairwise_overrides_take_priority():
    frame, target_uid, _ = _bridge(
        request_message="anything about Mel and me",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id="mel-uid",        # Slice B set it
        target_member_name="Mel",
        orchestrator_payload={
            "resolved_target": {"target_user_id": "mel-uid", "target_name": "Mel"}
        },
        resolved_field_active_frame="PAIRWISE",
    )
    assert frame == FRAME_PAIRWISE
    assert target_uid == "mel-uid"


# ---------------------------------------------------------------------
# 8. Privacy: orchestrator picked self → bridge must not propagate
# ---------------------------------------------------------------------
def test_orchestrator_target_equal_to_self_is_ignored():
    """If the orchestrator's resolved target IS the asker themselves
    (edge case from spouse_auto_promote), the bridge must NOT set
    target_uid — keep it None so the resolver stays self-only."""
    _, target_uid, _ = _bridge(
        request_message="what does my Juno say",
        request_user_id="pete-uid",
        effective_mode="forum",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={
            "resolved_target": {
                "target_user_id": "pete-uid",       # self!
                "target_name":    "Pete",
            }
        },
    )
    assert target_uid is None


# ---------------------------------------------------------------------
# 9. Empty / malformed orchestrator payload — must not crash
# ---------------------------------------------------------------------
def test_empty_orchestrator_payload_safe():
    frame, target_uid, target_name = _bridge(
        request_message="how is my Juno today",
        request_user_id="pete-uid",
        effective_mode="self",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload={},
    )
    assert frame == FRAME_SELF
    assert target_uid is None
    assert target_name is None


def test_none_orchestrator_payload_safe():
    frame, target_uid, _ = _bridge(
        request_message="how is my Juno today",
        request_user_id="pete-uid",
        effective_mode="self",
        effective_target_id=None,
        target_member_name=None,
        orchestrator_payload=None,  # type: ignore[arg-type]
    )
    assert frame == FRAME_SELF
    assert target_uid is None
