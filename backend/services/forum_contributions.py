"""
What Each Person Brings — per-member contribution derivation.

Given a forum's active members, emit a rich per-member contribution block:
the member's display name plus 3 titled items (short title + a one-sentence
description) describing what this person naturally brings into the room.

The derivation is 100% deterministic from each member's cached HD chart
(type + profile). No LLM calls, no pair-wise dynamics — this is each
person's individual energetic contribution, independent of the viewer.

Public entrypoint:

    await get_forum_contributions(db, forum_id)  ->  List[dict]

Each item shape:

    {
        "member_id": "69...",
        "name": "Pete",
        "is_host": true,
        "items": [
            {"title": "Ignition",        "description": "..."},
            {"title": "Opening",         "description": "..."},
            {"title": "Pressure Shift",  "description": "..."},
        ],
        # legacy flat fields retained for any older consumers:
        "attributes": ["IGNITION", "OPENING", "PRESSURE SHIFT"],
        "primary_label": "You're the one who starts what others are circling.",
    }
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from bson import ObjectId

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Derivation tables — each HD type has 3 base items. HD profile swaps the
# 3rd slot for added specificity.
# ---------------------------------------------------------------------------

_Item = Dict[str, str]

_TYPE_ITEMS: Dict[str, List[_Item]] = {
    "Manifestor": [
        {"title": "Ignition",       "description": "You're the one who starts what others are circling."},
        {"title": "Opening",        "description": "You say the thing that lets the real conversation begin."},
        {"title": "Pressure Shift", "description": "When the room stalls, you create movement."},
    ],
    "Generator": [
        {"title": "Response", "description": "You build momentum by answering what's in front of you."},
        {"title": "Stamina",  "description": "You stay with the work longer than most can."},
        {"title": "Building", "description": "You turn talk into something real. People rely on it."},
    ],
    "Manifesting Generator": [
        {"title": "Acceleration",  "description": "You move fast — ideas become action before most have caught up."},
        {"title": "Multitasking",  "description": "You hold multiple threads at once without dropping them."},
        {"title": "Redirection",   "description": "You change course mid-flight. Work flexes around you."},
    ],
    "Projector": [
        {"title": "Guidance",    "description": "You see who should be doing what, and you say it cleanly."},
        {"title": "Recognition", "description": "You do your best work when you're invited and seen."},
        {"title": "Seeing",      "description": "You read the system others are stuck inside and make it clearer."},
    ],
    "Reflector": [
        {"title": "Reflection",  "description": "You show people how they're actually coming across."},
        {"title": "Sensitivity", "description": "You read the room's tone before anyone else names it."},
        {"title": "Noticing",    "description": "You hold up what shifted in the conversation when no one else clocked it."},
    ],
}

# Profile-specific 3rd-item override. Each entry is a full item that replaces
# the last slot of the type's base items, giving each person a distinct
# specialization.
_PROFILE_ITEM: Dict[str, _Item] = {
    "1/3": {
        "title": "Inquiry",
        "description": "You test things by doing — foundation first, then trial.",
    },
    "1/4": {
        "title": "Inquiry",
        "description": "You steady groups with a strong inner base. People trust what you know.",
    },
    "2/4": {
        "title": "Depth",
        "description": "Your deepest work surfaces when the people who trust you call you in.",
    },
    "2/5": {
        "title": "Depth",
        "description": "Your natural gift shows up when someone sees it in you and names it.",
    },
    "3/5": {
        "title": "Experimentation",
        "description": "You try things, fail, adjust, and show the rest of us what actually works.",
    },
    "3/6": {
        "title": "Experimentation",
        "description": "You learn by doing — then, later, you become the mirror others watch.",
    },
    "4/6": {
        "title": "Connection",
        "description": "You move things through the people who trust you. Relationships are the work.",
    },
    "4/1": {
        "title": "Connection",
        "description": "You steady the room by knowing the ground — then pulling people in through trust.",
    },
    "5/1": {
        "title": "Projection",
        "description": "People see you as the one with the answer. You often are.",
    },
    "5/2": {
        "title": "Projection",
        "description": "Others expect you to deliver. You deliver in your own time, on your own terms.",
    },
    "6/2": {
        "title": "Wisdom",
        "description": "You watch first, act second, then model what works — quietly.",
    },
    "6/3": {
        "title": "Wisdom",
        "description": "You're learning in public, and people learn with you by watching.",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_type(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    t = raw.strip().lower()
    if "manifesting" in t and "generator" in t:
        return "Manifesting Generator"
    if t.startswith("manifestor"):
        return "Manifestor"
    if t.startswith("projector"):
        return "Projector"
    if t.startswith("reflector"):
        return "Reflector"
    if "generator" in t:
        return "Generator"
    return None


def _normalise_profile(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip().replace("–", "/").replace("-", "/")
    return s if s in _PROFILE_ITEM else None


def derive_items(hd: Optional[Dict[str, Any]], fallback_name: str = "") -> Dict[str, Any]:
    """
    Produce 3 {title, description} items for a single member, plus backward-
    compatible flat fields (`attributes`, `primary_label`) so older clients
    keep rendering something sensible during rollout.
    """
    if not isinstance(hd, dict):
        hd = {}

    hd_type = _normalise_type(hd.get("type"))
    profile = _normalise_profile(hd.get("profile"))

    if hd_type and hd_type in _TYPE_ITEMS:
        # Start from a COPY so we don't mutate the module-level tables.
        items: List[_Item] = [dict(it) for it in _TYPE_ITEMS[hd_type]]

        if profile and profile in _PROFILE_ITEM:
            # Profile specialisation replaces the 3rd item.
            items[2] = dict(_PROFILE_ITEM[profile])

        # Legacy flat view derived from the same items.
        attributes = [it["title"].upper() for it in items]
        primary_label = items[0]["description"]

        return {
            "items": items,
            "attributes": attributes,
            "primary_label": primary_label,
        }

    # No HD type yet — user onboarded but chart is empty or malformed.
    neutral_line = (
        f"{fallback_name} is in the room — the pattern is still forming."
        if fallback_name
        else "Present in the room — the pattern is still forming."
    )
    return {
        "items": [
            {"title": "Presence", "description": neutral_line},
        ],
        "attributes": ["PRESENCE"],
        "primary_label": neutral_line,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_forum_contributions(db, forum_id: str) -> List[Dict[str, Any]]:
    """
    Build the ordered list of "What Each Person Brings" blocks for a forum.
    Creator is surfaced first so the host is the first thing you scan.
    """
    if not ObjectId.is_valid(forum_id):
        return []

    forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
    if not forum:
        return []

    creator_id = forum.get("created_by")

    memberships = await db.forum_members.find({
        "forum_id": forum_id,
        "status": "active",
    }).to_list(500)

    def sort_key(m):
        uid = m.get("user_id")
        joined = m.get("joined_at")
        return (0 if uid == creator_id else 1, joined or 0)

    memberships.sort(key=sort_key)

    out: List[Dict[str, Any]] = []
    for m in memberships:
        uid = m.get("user_id")
        if not uid or not ObjectId.is_valid(uid):
            continue

        user = await db.users.find_one({"_id": ObjectId(uid)})
        if not user:
            continue

        name = (user.get("name") or "").strip() or "Member"

        chart = await db.charts.find_one({"user_id": uid})
        hd = (chart or {}).get("human_design") or {}

        derived = derive_items(hd, fallback_name=name)

        out.append({
            "member_id": uid,
            "name": name,
            "is_host": uid == creator_id,
            "items": derived["items"],
            # legacy compatibility (don't break the old clients still in the wild)
            "attributes": derived["attributes"],
            "primary_label": derived["primary_label"],
        })

    return out
