"""
Forum Field Intelligence  (forum-topology-and-timing-v1)
========================================================

The HEART of the forum-topology-and-timing-v1 stack.  Synthesises
topology, timing, pattern memory, micro-reflections and relational
awareness into the user-facing "Story of This Circle" object.

CRITICAL rules baked in:
  1. NEVER name or diagnose individual members.
  2. NEVER expose framework jargon (astrology, HD, BaZi, enneagram).
  3. NEVER quantify or rank.
  4. Speak only at FIELD / ROOM / CONVERSATIONS level.
  5. When topology confidence is `none` or `sparse`, return the calm
     placeholder — do NOT fabricate insight.

Output shape (the user-facing Story object):
    {
      marker: "forum-topology-and-timing-v1",
      ready: bool,
      placeholder: str | None,
      the_field: str | None,
      moves_toward: str | None,
      softening: str | None,
      unsaid: str | None,
      field_state_chips: [str, ...]   # max 2
    }

Plus a `debug` payload (dev-only) with internal signals.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from services.forum_topology import (
    compute_field_stability_score,
    get_topology_confidence_state,
    list_edges,
)
from services.forum_timing_engine import (
    synthesize_timing_state,
    VALID_FIELD_STATES,
)


# ---------------------------------------------------------------------------
# Field state → human chip label
# ---------------------------------------------------------------------------


_STATE_CHIP_LABEL: Dict[str, str] = {
    "stabilizing":         "Stabilizing",
    "transitional":        "Transitional",
    "pressured":           "Pressured",
    "clarifying":          "Clarifying",
    "reconnecting":        "Reconnecting",
    "fragmenting":         "Fragmenting",
    "emotionally_opening": "Opening",
    "protective":          "Protective",
    "future_oriented":     "Future-oriented",
    "reality_confronting": "Honest",
}


# ---------------------------------------------------------------------------
# Helpers — build each Story section softly from available signals.
# ---------------------------------------------------------------------------


def _build_the_field(
    *,
    timing: Dict[str, Any],
    topo_confidence: str,
) -> str:
    """
    THE FIELD — one short emotionally-alive paragraph.
    """
    dom = timing.get("dominant_phrase")
    sec = timing.get("secondary_phrase")
    qual = {
        "sparse":    "Even with limited information about how everyone here is connected, ",
        "emerging":  "From what's visible so far, ",
        "stable":    "",
    }.get(topo_confidence, "")

    if dom and sec:
        return (
            f"{qual}{dom}, while at the same time {sec}.  These are different "
            "registers of the same room — held at the same time."
        )
    if dom:
        return f"{qual}{dom}."
    return (
        f"{qual}the room seems to be in an ordinary in-between place — neither "
        "sharply pressured nor obviously expanding."
    )


def _moves_toward(
    *,
    timing: Dict[str, Any],
    edge_summary: Dict[str, Any],
) -> str:
    counts = timing.get("signal_counts") or {}
    protective = counts.get("protective", 0)
    pressure = counts.get("pressured", 0) + counts.get("structural_pressure", 0)
    transition = counts.get("transition", 0)
    softening = counts.get("softening", 0)

    has_hierarchy = edge_summary.get("hard_hierarchy_count", 0) >= 1
    has_heavy = edge_summary.get("heavy_count", 0) >= 1

    if protective >= max(pressure, transition, softening):
        return (
            "The room tends to move toward practicality and 'getting on with it' "
            "when conversations become emotionally charged."
        )
    if pressure > softening and pressure >= 2:
        return (
            "When friction shows up, the room tends to move toward problem-solving "
            "rather than naming what's actually being felt."
        )
    if transition >= 2:
        return (
            "The room tends to move toward decision-making and re-orientation when "
            "things feel ungrounded."
        )
    if softening >= max(pressure, protective):
        return (
            "The room tends to move toward shared meaning rather than answers when "
            "conversations open up."
        )
    if has_hierarchy and has_heavy:
        return (
            "Where power and weight are uneven, the room tends to defer "
            "rather than negotiate aloud."
        )
    return (
        "The room tends to translate emotional tension into language about "
        "process and next steps."
    )


def _softening(*, timing: Dict[str, Any]) -> Optional[str]:
    counts = timing.get("signal_counts") or {}
    soft = counts.get("softening", 0) + counts.get("clarity", 0) + counts.get("reconnecting", 0)
    if soft <= 0:
        return None
    if soft >= 3:
        return (
            "Something in the room feels noticeably less guarded lately — there "
            "seems to be slightly more willingness to remain with difficult "
            "conversations."
        )
    return (
        "Something in the room feels slightly less guarded than it did before — "
        "small openings, not yet a full shift."
    )


def _unsaid(
    *,
    timing: Dict[str, Any],
    edge_summary: Dict[str, Any],
) -> Optional[str]:
    counts = timing.get("signal_counts") or {}
    protective = counts.get("protective", 0)
    pressure = counts.get("pressured", 0)
    has_hierarchy = edge_summary.get("hard_hierarchy_count", 0) >= 1

    if protective + pressure <= 0:
        return None
    if has_hierarchy and protective >= 1:
        return (
            "Some tensions may still be getting routed through hierarchy rather "
            "than spoken across it."
        )
    if pressure >= 2:
        return (
            "Some tensions may still be getting translated into strategy and "
            "logistics rather than named directly."
        )
    if protective >= 2:
        return "The field still feels cautious about disruption."
    return None


def _chips(*, timing: Dict[str, Any]) -> List[str]:
    chips: List[str] = []
    dom = timing.get("dominant_state")
    sec = timing.get("secondary_state")
    if dom and dom in _STATE_CHIP_LABEL:
        chips.append(_STATE_CHIP_LABEL[dom])
    if sec and sec in _STATE_CHIP_LABEL and _STATE_CHIP_LABEL[sec] not in chips:
        chips.append(_STATE_CHIP_LABEL[sec])
    return chips[:2]


def _edge_summary(edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(edges)
    hard = sum(1 for e in edges if e.get("power_gradient") == "hard_hierarchy")
    soft = sum(1 for e in edges if e.get("power_gradient") == "soft_hierarchy")
    equal = sum(1 for e in edges if e.get("power_gradient") == "equal")
    heavy = sum(1 for e in edges if e.get("emotional_weight") == "heavy")
    roles: Dict[str, int] = {}
    for e in edges:
        rt = e.get("role_type") or "other"
        roles[rt] = roles.get(rt, 0) + 1
    return {
        "edges_total": n,
        "hard_hierarchy_count": hard,
        "soft_hierarchy_count": soft,
        "equal_count": equal,
        "heavy_count": heavy,
        "roles_present": roles,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def compose_story_of_circle(db, *, forum_id: str) -> Dict[str, Any]:
    """
    The single function the API endpoint calls.  Returns both the
    user-facing Story object AND a `debug` block (dev only).
    """
    # 1. Topology + confidence + edges.
    confidence_info = await get_topology_confidence_state(db, forum_id=forum_id)
    topo_confidence = confidence_info["state"]

    edges = await list_edges(db, forum_id=forum_id)
    edge_summary = _edge_summary(edges)

    # 2. Field stability score.
    stability = await compute_field_stability_score(db, forum_id=forum_id)

    # 3. Member list — for timing engine input.
    member_ids: List[str] = []
    try:
        cursor = db.forum_members.find({"forum_id": forum_id})
        async for r in cursor:
            uid = r.get("user_id")
            if uid:
                member_ids.append(str(uid))
    except Exception:
        member_ids = []

    # 4. Timing engine — behavioural state(s).
    timing = await synthesize_timing_state(db, member_ids=member_ids)

    # 5. Topology confidence gating.
    if topo_confidence in ("none", "sparse"):
        story: Dict[str, Any] = {
            "marker": "forum-topology-and-timing-v1",
            "ready": False,
            "placeholder": (
                "The field is still becoming visible.  Some dynamics only "
                "emerge through time, interaction, and shared context."
            ),
            "the_field": None,
            "moves_toward": None,
            "softening": None,
            "unsaid": None,
            "field_state_chips": [],
        }
    else:
        story = {
            "marker": "forum-topology-and-timing-v1",
            "ready": True,
            "placeholder": None,
            "the_field": _build_the_field(timing=timing, topo_confidence=topo_confidence),
            "moves_toward": _moves_toward(timing=timing, edge_summary=edge_summary),
            "softening": _softening(timing=timing),
            "unsaid": _unsaid(timing=timing, edge_summary=edge_summary),
            "field_state_chips": _chips(timing=timing),
        }

    # 6. Debug payload — INTERNAL only.
    counts = timing.get("signal_counts") or {}
    convergence_signals: List[str] = []
    if counts.get("structural_pressure", 0) >= 2:
        convergence_signals.append("structural_pressure_convergence")
    if counts.get("transition", 0) >= 2:
        convergence_signals.append("transition_convergence")
    if counts.get("softening", 0) >= 2:
        convergence_signals.append("softening_convergence")
    unresolved_tensions: List[str] = []
    if counts.get("protective", 0) >= 2:
        unresolved_tensions.append("protective_field")
    if counts.get("pressured", 0) >= 2:
        unresolved_tensions.append("pressured_field")

    debug = {
        "marker": "forum-topology-and-timing-v1",
        "topology_confidence": topo_confidence,
        "topology_summary": confidence_info,
        "edge_summary": edge_summary,
        "field_stability_score": stability,
        "dominant_field_state": timing.get("dominant_state"),
        "secondary_field_state": timing.get("secondary_state"),
        "convergence_signals": convergence_signals,
        "softening_signals": (
            ["softening"] if counts.get("softening", 0) > 0 else []
        ) + (
            ["clarity"] if counts.get("clarity", 0) > 0 else []
        ),
        "unresolved_tensions": unresolved_tensions,
        "topology_roles_present": edge_summary.get("roles_present", {}),
        "timing_pressure_summary": counts,
        "power_gradient_count": {
            "equal": edge_summary["equal_count"],
            "soft_hierarchy": edge_summary["soft_hierarchy_count"],
            "hard_hierarchy": edge_summary["hard_hierarchy_count"],
        },
        "member_count": len(member_ids),
    }

    return {"story": story, "debug": debug}
