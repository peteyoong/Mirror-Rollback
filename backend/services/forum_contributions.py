"""
What Each Person Brings — SUPERPOWER-BASED synthesis (Mirror Engine v2).

For each forum member, emit:

    {
        "name": "Pete",
        "is_host": true,
        "superpower": "Expansion",
        "lines": [
            "When you move, the room grows with you.",            # what happens in the room because of them
            "You tend to open space for others…",                  # how they uniquely express it
        ],
        # --- backward-compat fields (older clients can still render) ---
        "items":        [{"title": "Expansion", "description": "line 1 + line 2"}],
        "attributes":   ["EXPANSION"],
        "primary_label":"When you move, the room grows with you.",
    }

Rules honoured:
  • No archetype titles ("The Mystic")
  • No system language ("Initiation", "Generator energy")
  • No two members in the same forum share the same superpower (collision-resolved)
  • Superpower is 1–2 words, human, feels like a gift not a diagnosis

Inputs consulted (never surfaced by name):
  • Human Design type + profile  → base superpower family
  • Enneagram type               → which superpower inside the family
  • (BaZi / Decan / Pattern data is available for future description tuning;
     v2 keeps line descriptions static per superpower for clarity, variety
     comes from uniqueness of the superpower itself.)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from bson import ObjectId

logger = logging.getLogger(__name__)


# ===========================================================================
# The superpower pool — each entry has what the room gets (l1) and the
# characteristic style (l2). Human voice; no system language.
# ===========================================================================

_SUPERPOWERS: Dict[str, Dict[str, str]] = {
    "Expansion": {
        "l1": "When you move, the room grows with you.",
        "l2": "You tend to open space for others before they even realise they're ready.",
    },
    "Amplification": {
        "l1": "You reflect what's really happening in the room.",
        "l2": "What others feel vaguely becomes clear through you, often without you needing to push.",
    },
    "Momentum": {
        "l1": "When you're in, the work moves.",
        "l2": "You turn half-formed ideas into forward motion faster than most can track.",
    },
    "Clarity": {
        "l1": "After you speak, the fog lifts.",
        "l2": "You cut through what others are trying to say but haven't yet named.",
    },
    "Disruption": {
        "l1": "You break the pattern the room was quietly agreeing to.",
        "l2": "You say what needs saying before it's comfortable to hear.",
    },
    "Anchoring": {
        "l1": "The group settles when you enter.",
        "l2": "You hold steady ground so others can stop bracing.",
    },
    "Catalysis": {
        "l1": "Things start changing the moment you're in the mix.",
        "l2": "You don't push — your presence alone makes the next move obvious.",
    },
    "Revelation": {
        "l1": "Truths that were hiding come into view because you're here.",
        "l2": "You name the thing underneath the conversation, gently.",
    },
    "Acceleration": {
        "l1": "Time moves faster in your presence.",
        "l2": "Things that usually take weeks come together inside one session with you.",
    },
    "Attunement": {
        "l1": "You feel the room before it speaks.",
        "l2": "You adjust your tone to what the moment is actually asking for.",
    },
    "Insistence": {
        "l1": "You don't let the bar drop when others would.",
        "l2": "You hold the line on what matters until everyone else matches it.",
    },
    "Witnessing": {
        "l1": "You see people as they actually are, not who they perform to be.",
        "l2": "Your attention alone invites them to drop the act.",
    },
    "Resonance": {
        "l1": "The emotional truth of the room lives through you.",
        "l2": "You amplify what's real and let what's performative fall away.",
    },
    "Steadiness": {
        "l1": "When things get loud, you don't escalate.",
        "l2": "You lower the temperature of the room just by being in it.",
    },
    "Direction": {
        "l1": "You see who should do what, and you say it.",
        "l2": "Your instinct for where people belong is usually right before the rest of us catch up.",
    },
    "Refinement": {
        "l1": "What you touch gets noticeably better.",
        "l2": "You improve things others would have called done.",
    },
    "Reliability": {
        "l1": "When you commit, it happens.",
        "l2": "The work quietly gets carried by what you follow through on.",
    },
    "Vitality": {
        "l1": "Your energy re-charges the room.",
        "l2": "Things that were drooping start standing up again when you're in.",
    },
    "Recognition": {
        "l1": "You name the gift others don't know they have.",
        "l2": "People leave conversations with you feeling more clearly seen.",
    },
    "Endurance": {
        "l1": "You stay with what others have already given up on.",
        "l2": "Your patience is the thing that finishes the work.",
    },
    "Invitation": {
        "l1": "People lean in when you're the one asking.",
        "l2": "You draw out contribution others weren't sure they had.",
    },
    "Precision": {
        "l1": "You catch what others miss.",
        "l2": "Small errors stop compounding because you surface them early.",
    },
    "Depth": {
        "l1": "Conversations go to a truer layer when you're in them.",
        "l2": "You don't skim — you go where the real thing is happening.",
    },
    "Presence": {
        "l1": "You're fully here, and that changes what's possible.",
        "l2": "You make it easier for others to stop multitasking and land.",
    },
}


# ===========================================================================
# HD type × Enneagram type → superpower pick.
# If the ideal pick is already taken by someone else in the forum, we walk
# the per-HD-type fallback list to find the next best unused one.
# ===========================================================================

_HD_ENN_PICK: Dict[str, Dict[int, str]] = {
    "Manifestor": {
        1: "Insistence",
        2: "Invitation",
        3: "Momentum",
        4: "Disruption",
        5: "Revelation",
        6: "Anchoring",
        7: "Expansion",
        8: "Catalysis",
        9: "Clarity",
    },
    "Generator": {
        1: "Precision",
        2: "Reliability",
        3: "Momentum",
        4: "Depth",
        5: "Refinement",
        6: "Steadiness",
        7: "Vitality",
        8: "Endurance",
        9: "Presence",
    },
    "Manifesting Generator": {
        1: "Refinement",
        2: "Invitation",
        3: "Acceleration",
        4: "Resonance",
        5: "Revelation",
        6: "Reliability",
        7: "Catalysis",
        8: "Momentum",
        9: "Attunement",
    },
    "Projector": {
        1: "Precision",
        2: "Recognition",
        3: "Direction",
        4: "Witnessing",
        5: "Clarity",
        6: "Attunement",
        7: "Revelation",
        8: "Direction",
        9: "Recognition",
    },
    "Reflector": {
        1: "Precision",
        2: "Witnessing",
        3: "Amplification",
        4: "Resonance",
        5: "Witnessing",
        6: "Attunement",
        7: "Amplification",
        8: "Presence",
        9: "Resonance",
    },
}

# Fallback ordering per HD type (for collision resolution). First try ideal
# for (type × enneagram); if taken walk this list; finally fall back to the
# global pool.
_HD_FALLBACKS: Dict[str, List[str]] = {
    "Manifestor": ["Momentum", "Catalysis", "Disruption", "Expansion",
                   "Revelation", "Insistence", "Anchoring", "Clarity", "Invitation"],
    "Generator": ["Momentum", "Reliability", "Endurance", "Precision",
                  "Depth", "Refinement", "Vitality", "Steadiness", "Presence"],
    "Manifesting Generator": ["Acceleration", "Catalysis", "Momentum",
                              "Refinement", "Revelation", "Attunement",
                              "Reliability", "Invitation", "Resonance"],
    "Projector": ["Clarity", "Direction", "Recognition", "Witnessing",
                  "Attunement", "Revelation", "Precision", "Steadiness", "Depth"],
    "Reflector": ["Resonance", "Witnessing", "Amplification", "Attunement",
                  "Reflection", "Presence", "Precision", "Steadiness", "Depth"],
}

# A final universal fallback order if everything type-specific is taken
_GLOBAL_FALLBACKS: List[str] = [
    "Presence", "Depth", "Steadiness", "Recognition", "Witnessing",
    "Attunement", "Clarity", "Resonance", "Refinement", "Invitation",
    "Reliability", "Direction",
]


# ===========================================================================
# HD normalisation
# ===========================================================================

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


def _extract_enneagram(user: Dict[str, Any]) -> Optional[int]:
    raw = (
        user.get("enneagram_type")
        or user.get("primary_enneagram_type")
        or (user.get("enneagram") or {}).get("primary_type")
        or (user.get("enneagram_result") or {}).get("primary_type")
    )
    try:
        n = int(raw)
        return n if 1 <= n <= 9 else None
    except (TypeError, ValueError):
        return None


# ===========================================================================
# Superpower picker with collision resolution
# ===========================================================================

def _pick_superpower(
    hd_type: Optional[str],
    enneagram_num: Optional[int],
    used: Set[str],
) -> str:
    """
    Choose a superpower for this member that's not already used in the forum.
    Order of preference:
        1. Ideal (HD type × Enneagram)
        2. HD-type fallback list
        3. Global fallback list
        4. Last resort: any unused key from the pool
        5. Reuse (only if forum has more members than we have superpowers)
    """
    candidates: List[str] = []

    # 1. Ideal pick
    if hd_type and enneagram_num:
        ideal = _HD_ENN_PICK.get(hd_type, {}).get(enneagram_num)
        if ideal:
            candidates.append(ideal)

    # 2. HD-type fallback list
    if hd_type:
        candidates.extend(_HD_FALLBACKS.get(hd_type, []))

    # 3. Global fallback list
    candidates.extend(_GLOBAL_FALLBACKS)

    # 4. Any remaining pool key
    candidates.extend(_SUPERPOWERS.keys())

    for c in candidates:
        if c in _SUPERPOWERS and c not in used:
            return c

    # 5. Last-resort reuse (more members than superpowers)
    for c in candidates:
        if c in _SUPERPOWERS:
            return c

    # Absolute last-resort safety
    return "Presence"


# ===========================================================================
# Public API
# ===========================================================================

async def get_forum_contributions(db, forum_id: str) -> List[Dict[str, Any]]:
    """
    Build the "What Each Person Brings" superpower cards for a forum.
    Host first, then members by joined_at. Superpowers are unique within
    a forum whenever the pool allows (24 distinct superpowers available).
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

    used: Set[str] = set()
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

        hd_type = _normalise_type(hd.get("type"))
        enneagram_num = _extract_enneagram(user)

        superpower = _pick_superpower(hd_type, enneagram_num, used)
        used.add(superpower)

        content = _SUPERPOWERS[superpower]
        l1 = content["l1"]
        l2 = content["l2"]

        out.append({
            "member_id": uid,
            "name": name,
            "is_host": uid == creator_id,
            # New superpower shape (preferred)
            "superpower": superpower,
            "lines": [l1, l2],
            # Backward-compatible shapes for older clients that may still
            # render items/attributes/primary_label. These derive from the
            # same superpower so no client paints stale content.
            "items": [
                {"title": superpower, "description": f"{l1} {l2}"},
            ],
            "attributes": [superpower.upper()],
            "primary_label": l1,
        })

    return out
