"""
Live Field V1 — Forum field-level pattern engine
================================================

Purpose
-------
Reads the *room* — not the people in it.  Aggregates each member's
Astrology Today V5 dominant signal, intensity, and pattern_memory
state into a field-level read that every member sees the same way,
except for the "your position" line which is personalized.

Output sections (per the Mirror brief):

    FIELD STATE        — what the room is doing collectively
    YOUR POSITION      — how YOU sit relative to that pattern
    TRAJECTORY         — where the room is heading if this continues
    STORY              — felt narrative of the room (not literal)
    MOVE               — subtle opening (only at high confidence)

Hard rules
----------
- NEVER name individuals
- NEVER expose private behavior
- NEVER quote journal text
- Speak in terms of "the room"
- No advice, no instruction
- Field-state classification only when ≥3 members have V5 signals

Field states
------------
- acceleration_field   — many pushing/acting fast
- holding_field        — many hesitating / processing
- tension_field        — mixed signals / opposing pulls
- disengagement_field  — low activity / withdrawal
- alignment_field      — shared direction / clarity

Source-of-truth: db.forum_members + db.daily_astrology + db.pattern_memory.
Fully deterministic (no LLM) for safety + tone control.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Theme buckets — coarse-grained behavioral classification of a member's
# current V5 state.  These map directly onto field-state aggregation.
# ---------------------------------------------------------------------------
THEME_ACCELERATING = "accelerating"   # pushing fast under uncertainty
THEME_HOLDING      = "holding"        # hesitating / over-processing
THEME_OPPOSING     = "opposing"       # signal_conflict / pulled both ways
THEME_DISENGAGED   = "disengaged"     # low activity, no recent signal
THEME_ALIGNED      = "aligned"        # clear/low intensity coherent state


def _classify_member_theme(v5_doc: Optional[Dict[str, Any]]) -> str:
    """Map a member's stored V5 daily_astrology row to a coarse theme.

    Falls back to `disengaged` when the member has no recent V5 read
    (no document or document older than 36h)."""
    if not v5_doc:
        return THEME_DISENGAGED
    ga = v5_doc.get("generated_at")
    if isinstance(ga, datetime):
        if ga.tzinfo is None:
            ga = ga.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - ga).total_seconds() > 36 * 3600:
            return THEME_DISENGAGED

    if v5_doc.get("signal_conflict"):
        return THEME_OPPOSING

    ds = v5_doc.get("dominant_signal") or {}
    ds_type = (ds.get("type") or "").lower()
    intensity = (v5_doc.get("intensity") or "medium").lower()

    if any(t in ds_type for t in ("full_moon", "new_moon", "lunation")):
        return THEME_ACCELERATING
    if "ingress" in ds_type:
        return THEME_HOLDING
    if "tight_aspect" in ds_type or "aspect" in ds_type:
        return THEME_ACCELERATING if intensity == "high" else THEME_HOLDING
    if intensity == "high":
        return THEME_ACCELERATING
    if intensity == "low":
        return THEME_HOLDING
    return THEME_ALIGNED


# ---------------------------------------------------------------------------
# Field-state classifier
# ---------------------------------------------------------------------------

def _classify_field_state(theme_counts: Counter, total: int) -> Tuple[str, str]:
    """Return (field_state, intensity)."""
    if total == 0:
        return ("disengagement_field", "low")

    accel = theme_counts.get(THEME_ACCELERATING, 0)
    hold  = theme_counts.get(THEME_HOLDING, 0)
    opp   = theme_counts.get(THEME_OPPOSING, 0)
    diseng = theme_counts.get(THEME_DISENGAGED, 0)
    align  = theme_counts.get(THEME_ALIGNED, 0)

    # Disengagement dominates only if a clear majority of members have
    # no recent signal.
    if diseng / total >= 0.6:
        return ("disengagement_field", "low")

    # Tension when both accelerators and holders are present in roughly
    # equal proportion, OR a meaningful share of members are in
    # signal_conflict themselves.
    has_polarity = accel >= 2 and hold >= 2
    has_conflict = opp >= max(2, total // 4)
    if has_polarity or has_conflict:
        intensity = "high" if (opp + min(accel, hold)) >= total // 2 else "medium"
        return ("tension_field", intensity)

    # Acceleration / holding cluster (≥3 members same theme — per brief)
    if accel >= 3 and accel >= hold:
        intensity = "high" if accel / total >= 0.5 else "medium"
        return ("acceleration_field", intensity)
    if hold >= 3 and hold >= accel:
        intensity = "high" if hold / total >= 0.5 else "medium"
        return ("holding_field", intensity)

    # Alignment when most members are in the aligned theme with
    # clear/low-intensity signals.
    if align / total >= 0.5:
        return ("alignment_field", "medium")

    # Fallback: small or mixed group with no dominant cluster.
    return ("alignment_field", "low")


# ---------------------------------------------------------------------------
# Curated phrasings — every line stays in "the room" register.
# ---------------------------------------------------------------------------

_FIELD_MESSAGES = {
    "acceleration_field": "There's a shared pressure in the room right now — people are moving quickly, but not everything is fully clear.",
    "holding_field":      "The room is sitting in something — there's hesitation underneath the surface that hasn't quite settled.",
    "tension_field":      "There's a split in the room right now — some are moving forward while others are still trying to read the situation.",
    "disengagement_field":"The room is quieter than usual — most people aren't actively in the field today.",
    "alignment_field":    "The room is largely in the same direction right now — there's a quiet coherence underneath the activity.",
}

_TRAJECTORIES = {
    "acceleration_field": "If this continues, the room may move forward before everyone is fully aligned.",
    "holding_field":      "If this continues, things may keep being held — the readiness to move hasn't arrived.",
    "tension_field":      "If this continues, decisions may get made before everyone is on the same page.",
    "disengagement_field":"If this continues, the field will keep thinning — there's nothing to coalesce around right now.",
    "alignment_field":    "If this continues, the room will keep moving as one — the direction is clear enough to hold.",
}

_STORIES = {
    "acceleration_field": "It feels like everyone is trying to land something — but no one is fully certain what the landing actually is.",
    "holding_field":      "It feels like the room is waiting for something — though it's not entirely clear what.",
    "tension_field":      "It feels like the room is split between two pulls — and neither side is fully sure of itself.",
    "disengagement_field":"It feels like the room hasn't shown up yet today.",
    "alignment_field":    "It feels like the room knows where it's going — even if no one is naming it out loud.",
}

_MOVES = {
    "acceleration_field": "There's space here to slow this down without stopping it.",
    "holding_field":      "There's space here to name what's holding things in place.",
    "tension_field":      "There's space here to let the split be visible without forcing a side.",
    "disengagement_field":"",  # no move when field is too thin
    "alignment_field":    "There's space here to keep going — the room has the coherence for it.",
}


# Personalized "Your Position" relative to the field theme.  Two lines
# per field state — one for *aligned* member, one for *out-of-sync*.
_POSITIONS = {
    "acceleration_field": {
        "in":  "You're contributing to the speed of the room — not because things are clear, but because the pressure to move is high.",
        "out": "You're slightly out of sync with the room — while others are moving quickly, you're still trying to make sense of things.",
    },
    "holding_field": {
        "in":  "You're part of what's holding the room — the same hesitation is sitting in you too.",
        "out": "You're slightly out of sync with the room — while others are holding back, something in you is already moving.",
    },
    "tension_field": {
        "in":  "You're carrying part of the split yourself — the same pull is alive in you too.",
        "out": "You're sitting outside the split right now — the room is pulling in two directions but you're not in either.",
    },
    "disengagement_field": {
        "in":  "You're quiet today too — the room and you are in a similar low gear.",
        "out": "You're more active than the room right now — what's moving in you isn't yet showing up across the field.",
    },
    "alignment_field": {
        "in":  "You're in the same direction as the room — what's true here is also true in you.",
        "out": "You're slightly outside the shared direction — what's coherent for the room isn't fully landed in you yet.",
    },
}


def _user_position_line(field_state: str, user_theme: str) -> str:
    field_to_in_themes = {
        "acceleration_field": {THEME_ACCELERATING},
        "holding_field":      {THEME_HOLDING},
        "tension_field":      {THEME_OPPOSING, THEME_ACCELERATING, THEME_HOLDING},
        "disengagement_field":{THEME_DISENGAGED},
        "alignment_field":    {THEME_ALIGNED},
    }
    in_set = field_to_in_themes.get(field_state, set())
    pos = _POSITIONS.get(field_state, _POSITIONS["alignment_field"])
    return pos["in"] if user_theme in in_set else pos["out"]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

async def build_live_field_payload(
    db, forum_id: str, user_id: str,
) -> Dict[str, Any]:
    """Build the Live Field card for `user_id` viewing forum `forum_id`."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1) Active members of this forum
    members = await db.forum_members.find({
        "forum_id": forum_id,
        "status":   "active",
    }).to_list(500)
    member_ids = [m.get("user_id") for m in members if m.get("user_id")]

    # Confidence floor — need at least 3 active members for any field
    # classification per the brief.
    if len(member_ids) < 3:
        return {
            "version":        "lf-v1",
            "forum_id":       forum_id,
            "available":      False,
            "reason":         "insufficient_members",
            "member_count":   len(member_ids),
            "generated_at":   datetime.now(timezone.utc).isoformat(),
        }

    # 2) Pull each member's most recent V5 daily_astrology row (today
    #    preferred, otherwise the freshest within 48h).
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    v5_by_user: Dict[str, Dict[str, Any]] = {}
    try:
        async for doc in db.daily_astrology.find({
            "user_id": {"$in": member_ids},
        }).sort("generated_at", -1):
            uid = doc.get("user_id")
            if not uid or uid in v5_by_user:
                continue
            ga = doc.get("generated_at")
            if isinstance(ga, datetime):
                ga_aware = ga if ga.tzinfo else ga.replace(tzinfo=timezone.utc)
                if ga_aware < cutoff and doc.get("date") != today_str:
                    continue
            v5_by_user[uid] = doc
    except Exception as e:
        logger.warning("[LiveField] daily_astrology pull failed: %s", e)

    # 3) Classify each member into a coarse theme
    member_themes: Dict[str, str] = {
        uid: _classify_member_theme(v5_by_user.get(uid))
        for uid in member_ids
    }
    theme_counts = Counter(member_themes.values())
    total_members = len(member_ids)

    # Coverage — members with a fresh V5 row (today preferred, else <=48h).
    members_with_fresh_v5 = len([
        uid for uid in member_ids if uid in v5_by_user
    ])
    coverage_ratio = (
        members_with_fresh_v5 / total_members if total_members > 0 else 0.0
    )

    # ---------------------------------------------------------------
    # V1.1 SIGNAL COVERAGE RULES — refuse overconfident reads when
    # too little of the room has a fresh V5 signal.
    # ---------------------------------------------------------------
    if coverage_ratio < 0.5:
        # LOW SIGNAL FIELD — do NOT run the normal classifier.  The
        # user-position line still varies ("you're more active than
        # the visible part of the room") so the user sees it's them
        # bringing most of the signal, not the room being flat.
        user_theme = member_themes.get(user_id, THEME_DISENGAGED)
        if user_theme in (THEME_ACCELERATING, THEME_OPPOSING, THEME_HOLDING):
            user_pos = ("You're more active than the visible part of the "
                        "room right now.")
        else:
            user_pos = ("You're part of the quiet stretch in the room "
                        "right now — not much signal either way.")

        return {
            "version":        "lf-v1.1",
            "forum_id":       forum_id,
            "available":      True,
            "field_state":    "low_signal_field",
            "intensity":      "low",
            "field_message":  "The room is not giving enough signal yet.",
            "user_position":  user_pos,
            "trajectory":     "It's too early to read where this is going.",
            "story":          "Only part of the room is visible, so this reflects activity more than the full field.",
            "move":           {"available": False, "line": ""},
            "signal_coverage": {
                "members":  total_members,
                "active":   members_with_fresh_v5,
                "ratio":    round(coverage_ratio, 3),
                "tier":     "low",
            },
            "stats": {
                "member_count":     total_members,
                "members_with_v5":  members_with_fresh_v5,
                "theme_counts": {
                    "accelerating": theme_counts.get(THEME_ACCELERATING, 0),
                    "holding":      theme_counts.get(THEME_HOLDING, 0),
                    "opposing":     theme_counts.get(THEME_OPPOSING, 0),
                    "disengaged":   theme_counts.get(THEME_DISENGAGED, 0),
                    "aligned":      theme_counts.get(THEME_ALIGNED, 0),
                },
            },
            "generated_at":   datetime.now(timezone.utc).isoformat(),
        }

    # 4) Field-state classification (coverage ≥ 0.5)
    field_state, intensity = _classify_field_state(theme_counts, total_members)

    # Medium coverage → cap intensity at "medium".
    if 0.5 <= coverage_ratio < 0.75 and intensity == "high":
        intensity = "medium"

    coverage_tier = "high" if coverage_ratio >= 0.75 else "medium"

    # 5) User's own position relative to the field
    user_theme = member_themes.get(user_id, THEME_DISENGAGED)
    user_position_line = _user_position_line(field_state, user_theme)

    # 6) Field-level lines (deterministic by field_state)
    field_message = _FIELD_MESSAGES[field_state]
    trajectory    = _TRAJECTORIES[field_state]
    story         = _STORIES[field_state]
    move_line     = _MOVES.get(field_state, "")

    # Show MOVE only at high/medium intensity AND when we have a non-empty
    # phrasing for that state.
    move_block = (
        {"available": True,  "line": move_line}
        if move_line and intensity in ("high", "medium")
        else {"available": False, "line": ""}
    )

    return {
        "version":        "lf-v1.1",
        "forum_id":       forum_id,
        "available":      True,
        "field_state":    field_state,
        "intensity":      intensity,
        "field_message":  field_message,
        "user_position":  user_position_line,
        "trajectory":     trajectory,
        "story":          story,
        "move":           move_block,
        "signal_coverage": {
            "members":  total_members,
            "active":   members_with_fresh_v5,
            "ratio":    round(coverage_ratio, 3),
            "tier":     coverage_tier,
        },
        "stats": {
            "member_count":     total_members,
            "members_with_v5":  members_with_fresh_v5,
            "theme_counts": {
                "accelerating": theme_counts.get(THEME_ACCELERATING, 0),
                "holding":      theme_counts.get(THEME_HOLDING, 0),
                "opposing":     theme_counts.get(THEME_OPPOSING, 0),
                "disengaged":   theme_counts.get(THEME_DISENGAGED, 0),
                "aligned":      theme_counts.get(THEME_ALIGNED, 0),
            },
        },
        "generated_at":   datetime.now(timezone.utc).isoformat(),
    }
