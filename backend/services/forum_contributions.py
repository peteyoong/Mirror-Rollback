"""
What Each Person Brings — per-member contribution derivation.

Given a forum's active members, emit a compact scannable contribution card
for each: 2–3 uppercase attribute chips plus a single-line primary label
that summarises what this person naturally brings into the room.

The derivation is 100% deterministic from each member's cached HD chart
(type + profile + prominent defined centers). No LLM calls, no pair-wise
dynamics — this is each person's individual energetic contribution,
independent of the viewer.

Public entrypoint:

    await get_forum_contributions(db, forum_id)  ->  List[dict]

Each item shape:

    {
        "member_id": "69...",
        "name": "Pete",
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
# Derivation tables — scannable, deterministic.
# ---------------------------------------------------------------------------

# HD Type → base chips + one-line "what they bring" framing.
# The third chip is optional and will be overridden by a profile / center
# modifier when one is available.
_TYPE_BASE: Dict[str, Dict[str, Any]] = {
    "Manifestor": {
        "chips": ["IGNITION", "OPENING", "PRESSURE SHIFT"],
        "label": "You're the one who starts what others are circling.",
    },
    "Generator": {
        "chips": ["RESPONSE", "STAMINA", "BUILDING"],
        "label": "You build what gets built. When you're in, the work moves.",
    },
    "Manifesting Generator": {
        "chips": ["ACCELERATION", "MULTITASKING", "REDIRECTION"],
        "label": "You move fast and change course. Work flexes around you.",
    },
    "Projector": {
        "chips": ["GUIDANCE", "RECOGNITION", "SEEING"],
        "label": "You see who should move where. You make the system clearer.",
    },
    "Reflector": {
        "chips": ["REFLECTION", "SENSITIVITY", "NOTICING"],
        "label": "You notice the room. People learn about themselves through you.",
    },
}

# Profile → a flavour chip that replaces the 3rd type chip when present, and
# (optionally) tweaks the label for specificity. We keep the chip pool short
# so the row stays scannable.
_PROFILE_MOD: Dict[str, Dict[str, str]] = {
    "1/3": {"chip": "INQUIRY", "label": "You test things by doing — foundation first, then trial."},
    "1/4": {"chip": "INQUIRY", "label": "You build trust by knowing the ground first."},
    "2/4": {"chip": "DEPTH", "label": "Your deepest work surfaces when you're called in."},
    "2/5": {"chip": "DEPTH", "label": "Your natural gift shows up when someone sees it."},
    "3/5": {"chip": "EXPERIMENTATION", "label": "You experiment, adjust, and show others what works."},
    "3/6": {"chip": "EXPERIMENTATION", "label": "You learn by doing, then become the mirror."},
    "4/6": {"chip": "CONNECTION", "label": "You move things through people who trust you."},
    "4/1": {"chip": "CONNECTION", "label": "You steady groups with a strong inner base."},
    "5/1": {"chip": "PROJECTION", "label": "People see you as the one with the solution — you often are."},
    "5/2": {"chip": "PROJECTION", "label": "Others expect you to deliver. You deliver in your own time."},
    "6/2": {"chip": "WISDOM", "label": "You watch first, act second, then model what works."},
    "6/3": {"chip": "WISDOM", "label": "You're learning in public, and people learn from it."},
}

# Prominent defined-centre modifiers — used as a secondary chip option when
# profile data is missing. Ordered by scannability priority.
_CENTER_CHIP: Dict[str, str] = {
    "Throat": "VOICE",
    "G": "DIRECTION",
    "G Center": "DIRECTION",
    "Ajna": "CONCEPT",
    "Head": "INSPIRATION",
    "Heart": "WILLPOWER",
    "Ego": "WILLPOWER",
    "Sacral": "LIFE FORCE",
    "Root": "PRESSURE",
    "Spleen": "INTUITION",
    "Solar Plexus": "EMOTIONAL WAVE",
    "Emotional Solar Plexus": "EMOTIONAL WAVE",
    "Emotional": "EMOTIONAL WAVE",
}


# ---------------------------------------------------------------------------
# Core derivation
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
    return s if s in _PROFILE_MOD else None


def _pick_center_chip(centers_defined: Any) -> Optional[str]:
    if not isinstance(centers_defined, list):
        return None
    # Preference order — pick the first meaningful one.
    for preferred in ("Throat", "G", "G Center", "Ajna", "Head",
                      "Heart", "Ego", "Spleen", "Solar Plexus",
                      "Emotional Solar Plexus", "Sacral", "Root"):
        for c in centers_defined:
            if isinstance(c, str) and c.strip().lower() == preferred.lower():
                return _CENTER_CHIP.get(preferred)
    # Fallback: first entry we can map at all.
    for c in centers_defined:
        if isinstance(c, str):
            chip = _CENTER_CHIP.get(c.strip())
            if chip:
                return chip
    return None


def derive_contribution(hd: Optional[Dict[str, Any]], fallback_name: str = "") -> Dict[str, Any]:
    """
    Produce the {attributes, primary_label} pair for a single member.

    Always returns a non-empty structure — if we have no HD data at all we
    surface a neutral "present in the room" framing rather than silently
    excluding the member.
    """
    if not isinstance(hd, dict):
        hd = {}

    hd_type = _normalise_type(hd.get("type"))
    profile = _normalise_profile(hd.get("profile"))
    centers = hd.get("defined_centers") or hd.get("centers_defined")

    if hd_type and hd_type in _TYPE_BASE:
        base = _TYPE_BASE[hd_type]
        chips: List[str] = list(base["chips"])
        label: str = base["label"]

        if profile and profile in _PROFILE_MOD:
            mod = _PROFILE_MOD[profile]
            # Profile flavour replaces the 3rd base chip.
            if len(chips) >= 3:
                chips[2] = mod["chip"]
            else:
                chips.append(mod["chip"])
            # Prefer the more specific profile-aware label.
            label = mod["label"]
        else:
            # No profile — if we have a notable defined center, use it to
            # replace the 3rd chip so each person looks distinct.
            center_chip = _pick_center_chip(centers)
            if center_chip:
                if len(chips) >= 3:
                    chips[2] = center_chip
                else:
                    chips.append(center_chip)

        # Dedupe while preserving order and cap at 3.
        seen = set()
        dedup = []
        for c in chips:
            cu = c.strip().upper()
            if cu and cu not in seen:
                seen.add(cu)
                dedup.append(cu)
            if len(dedup) == 3:
                break
        return {"attributes": dedup, "primary_label": label}

    # No HD type yet — user onboarded but chart is empty or malformed.
    return {
        "attributes": ["PRESENCE"],
        "primary_label": (
            f"{fallback_name} is in the room — the pattern is still forming."
            if fallback_name
            else "Present in the room — the pattern is still forming."
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_forum_contributions(db, forum_id: str) -> List[Dict[str, Any]]:
    """
    Build the ordered list of "What Each Person Brings" cards for a forum.
    Creator is always surfaced first so the host is the first thing you scan.
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

    # Sort: creator first, then by joined_at ascending.
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

        contribution = derive_contribution(hd, fallback_name=name)

        out.append({
            "member_id": uid,
            "name": name,
            "attributes": contribution["attributes"],
            "primary_label": contribution["primary_label"],
            "is_host": uid == creator_id,
        })

    return out
