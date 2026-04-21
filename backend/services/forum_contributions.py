"""
What Each Person Brings — Cross-Lens Synthesis (Mirror Engine v1).

This is the v2 of the forum contributions endpoint. Each item is now a
2-3 sentence synthesized paragraph woven from four internal signals:

    1. Human Design    → base behavior (the trait anchor)
    2. Enneagram       → motivation (the "why")
    3. BaZi            → current pressure / timing
    4. Pattern memory  → recurrence / familiarity

Guardrails (see PRD):
    - Never surface lens names — no "Enneagram says…", no "HD type…"
    - Max 3 sentences per item
    - Must feel current, specific, slightly confronting (not harsh)
    - Must feel like "this is happening now", not a static profile

To avoid each of the 3 items sounding identical, the synthesis rotates
which extra layers attach to which item:

    item[0] = behavior + motive       (hero slot — the "why")
    item[1] = behavior + timing       (the "now")
    item[2] = behavior + pattern/timing (the "recurrence" or fallback)

Only the HD anchor is mandatory. Each additional layer is optional —
if Enneagram / BaZi / pattern data is missing, the synthesis degrades
gracefully without breaking the output.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

logger = logging.getLogger(__name__)


# ===========================================================================
# LAYER 1 — HD anchor tables (titles + 1-sentence base behavior)
# ===========================================================================

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
        {"title": "Building", "description": "You turn talk into something real — people rely on it."},
    ],
    "Manifesting Generator": [
        {"title": "Acceleration", "description": "You move fast — ideas become action before most have caught up."},
        {"title": "Multitasking", "description": "You hold multiple threads at once without dropping them."},
        {"title": "Redirection",  "description": "You change course mid-flight — work flexes around you."},
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

_PROFILE_ITEM: Dict[str, _Item] = {
    "1/3": {"title": "Inquiry",         "description": "You test things by doing — foundation first, then trial."},
    "1/4": {"title": "Inquiry",         "description": "You steady groups with a strong inner base."},
    "2/4": {"title": "Depth",           "description": "Your deepest work surfaces when the people who trust you call you in."},
    "2/5": {"title": "Depth",           "description": "Your natural gift shows up when someone sees it in you and names it."},
    "3/5": {"title": "Experimentation", "description": "You try things, fail, adjust, and show the rest of us what actually works."},
    "3/6": {"title": "Experimentation", "description": "You learn by doing — then, later, you become the mirror others watch."},
    "4/6": {"title": "Connection",      "description": "You move things through the people who trust you. Relationships are the work."},
    "4/1": {"title": "Connection",      "description": "You steady the room by knowing the ground, then pulling people in through trust."},
    "5/1": {"title": "Projection",      "description": "People see you as the one with the answer. You often are."},
    "5/2": {"title": "Projection",      "description": "Others expect you to deliver. You deliver in your own time, on your own terms."},
    "6/2": {"title": "Wisdom",          "description": "You watch first, act second, then model what works — quietly."},
    "6/3": {"title": "Wisdom",          "description": "You're learning in public, and people learn with you by watching."},
}


# ===========================================================================
# LAYER 2 — Enneagram → motive phrase
# ===========================================================================

_ENNEAGRAM_MOTIVE: Dict[int, str] = {
    1: "because getting it right matters to you",
    2: "because you want to be needed",
    3: "because staying effective matters to you",
    4: "because you want to feel something real",
    5: "because you need to understand before acting",
    6: "because uncertainty feels risky",
    7: "because being stuck feels uncomfortable",
    8: "because staying in control matters",
    9: "because conflict feels heavy to hold",
}


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
# LAYER 3 — BaZi / Astrology → pressure state
# ===========================================================================

_TIMING_LINES: Dict[str, str] = {
    "urgency_to_act":       "right now, that urgency is stronger",
    "pullback_and_wait":    "right now, you may feel yourself holding back",
    "emotional_intensity":  "right now, this lands more emotionally than usual",
    "rebuild_phase":        "you're in a phase where things are being reworked",
    "uncertainty_phase":    "clarity isn't fully there yet",
}


def _derive_pressure_state(chart: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Map BaZi day-master + element signals into a simple pressure state.
    Returns None if there's not enough data to be meaningful.
    """
    if not isinstance(chart, dict):
        return None
    bazi = chart.get("bazi") or {}
    dm = bazi.get("day_master") or {}
    element = (dm.get("element") or "").strip().lower()
    strength = (dm.get("strength") or "").strip().lower()

    if not element and not strength:
        return None

    # Water carries emotion; map it first regardless of strength.
    if element == "water":
        return "emotional_intensity"

    if strength == "strong":
        if element in ("fire", "wood"):
            return "urgency_to_act"
        if element == "metal":
            return "pullback_and_wait"
        if element == "earth":
            return "urgency_to_act"
        return "urgency_to_act"

    if strength == "weak":
        return "rebuild_phase"

    # balanced / unknown strength → a softer uncertainty framing
    return "uncertainty_phase"


# ===========================================================================
# LAYER 4 — Pattern memory
# ===========================================================================

_PATTERN_LINES = {
    "RETURNING": "you've been here recently",
    "RECURRING": "this isn't new — you've been here before",
}


async def _pattern_state(db, user_id: str) -> Optional[str]:
    """
    Very lightweight pattern-memory probe. Counts recent forum reflections
    by this member — more than 2 historical reflections → RECURRING, 1 → RETURNING,
    otherwise None (NEW, no line).

    We keep the probe cheap so contributions() stays fast even on big forums.
    """
    try:
        count = await db.forum_reflections.count_documents({"user_id": user_id})
    except Exception:
        return None
    if count >= 3:
        return "RECURRING"
    if count >= 1:
        return "RETURNING"
    return None


# ===========================================================================
# Synthesis — weave the layers into 3 items, each 2–3 sentences
# ===========================================================================

def _finish_sentence(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    if s[-1] not in ".!?":
        s += "."
    return s


def _compose(anchor_sentence: str, *extras: str) -> str:
    """
    Stitch an anchor sentence with 0-2 extra sentences into a natural
    paragraph. Each extra becomes its own sentence, so the result reads
    cleanly regardless of which layers are present.
    """
    parts: List[str] = [_finish_sentence(anchor_sentence)]
    for extra in extras:
        if not extra:
            continue
        # First letter uppercase, trailing period.
        extra = extra.strip()
        if extra:
            extra = extra[0].upper() + extra[1:]
        parts.append(_finish_sentence(extra))
    return " ".join(parts)


def _synthesize_items(
    base_items: List[_Item],
    motive_phrase: Optional[str],
    timing_key: Optional[str],
    pattern_key: Optional[str],
) -> List[_Item]:
    """
    Rotate the extra layers across the 3 items so no two paragraphs feel
    identical. Guaranteed output:
        item[0]: anchor + motive (if any)
        item[1]: anchor + timing (if any)
        item[2]: anchor + pattern (if any) else anchor + secondary timing
    """
    # Defensive: ensure we always have exactly 3 slots to work with.
    items = [dict(it) for it in base_items][:3]
    while len(items) < 3 and items:
        items.append(dict(items[-1]))

    out: List[_Item] = []

    # --- Item 0: behavior + motive (the "why") ---
    if items:
        anchor0 = items[0]["description"]
        motive_sentence = (
            f"You tend to do this {motive_phrase}" if motive_phrase else ""
        )
        # Add a subtle "in this room, right now" anchoring if we also have timing
        now_sentence = ""
        if timing_key and timing_key in _TIMING_LINES and not motive_sentence:
            now_sentence = _TIMING_LINES[timing_key]
        out.append({
            "title": items[0]["title"],
            "description": _compose(anchor0, motive_sentence, now_sentence),
        })

    # --- Item 1: behavior + timing (the "now") ---
    if len(items) >= 2:
        anchor1 = items[1]["description"]
        timing_sentence = _TIMING_LINES.get(timing_key) if timing_key else None
        out.append({
            "title": items[1]["title"],
            "description": _compose(anchor1, timing_sentence or ""),
        })

    # --- Item 2: behavior + pattern (the "recurrence") ---
    if len(items) >= 3:
        anchor2 = items[2]["description"]
        pattern_sentence = _PATTERN_LINES.get(pattern_key) if pattern_key else None
        # If no pattern line, softly reuse the timing line (different slot gives it fresh weight)
        fallback = ""
        if not pattern_sentence and timing_key:
            fallback_map = {
                "urgency_to_act":       "the pace here is asking more of you today",
                "pullback_and_wait":    "you may want to move — but the room isn't ready for it yet",
                "emotional_intensity":  "this one is hitting closer than usual",
                "rebuild_phase":        "you're rebuilding the ground you stand on as you go",
                "uncertainty_phase":    "the shape of this room is still settling",
            }
            fallback = fallback_map.get(timing_key, "")
        out.append({
            "title": items[2]["title"],
            "description": _compose(anchor2, pattern_sentence or fallback),
        })

    return out


# ===========================================================================
# HD normalisation helpers
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


def _normalise_profile(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip().replace("–", "/").replace("-", "/")
    return s if s in _PROFILE_ITEM else None


def _base_items_for(hd: Dict[str, Any]) -> Tuple[List[_Item], Optional[str], Optional[str]]:
    """Return (items, hd_type, profile). Items come from HD tables; 3rd slot
    is swapped for the profile-specific variant when available."""
    hd_type = _normalise_type(hd.get("type"))
    profile = _normalise_profile(hd.get("profile"))
    if hd_type and hd_type in _TYPE_ITEMS:
        items = [dict(it) for it in _TYPE_ITEMS[hd_type]]
        if profile and profile in _PROFILE_ITEM:
            items[2] = dict(_PROFILE_ITEM[profile])
        return items, hd_type, profile
    return [], hd_type, profile


# ===========================================================================
# Public API
# ===========================================================================

async def get_forum_contributions(db, forum_id: str) -> List[Dict[str, Any]]:
    """
    Build the "What Each Person Brings" synthesis for a forum.
    Host first, then members by joined_at.
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

        base_items, _hd_type, _profile = _base_items_for(hd)

        if not base_items:
            # Graceful neutral fallback — still one item so the UI doesn't
            # render an empty member block.
            out.append({
                "member_id": uid,
                "name": name,
                "is_host": uid == creator_id,
                "items": [{
                    "title": "Presence",
                    "description": f"{name} is in the room — the pattern is still forming.",
                }],
                # legacy
                "attributes": ["PRESENCE"],
                "primary_label": "Present in the room — the pattern is still forming.",
            })
            continue

        enneagram_num = _extract_enneagram(user)
        motive_phrase = _ENNEAGRAM_MOTIVE.get(enneagram_num) if enneagram_num else None

        timing_key = _derive_pressure_state(chart)
        pattern_key = await _pattern_state(db, uid)

        synthesized = _synthesize_items(
            base_items=base_items,
            motive_phrase=motive_phrase,
            timing_key=timing_key,
            pattern_key=pattern_key,
        )

        out.append({
            "member_id": uid,
            "name": name,
            "is_host": uid == creator_id,
            "items": synthesized,
            # Legacy backward-compat fields (derived from the anchor titles
            # / first descriptions so older consumers keep working).
            "attributes": [it["title"].upper() for it in synthesized],
            "primary_label": synthesized[0]["description"] if synthesized else "",
        })

    return out
