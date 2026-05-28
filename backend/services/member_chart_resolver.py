"""
Member Chart Resolver  (ask-mirror-astrology-v7)
================================================

Resolves "the target person of an astrology question" inside an Ask Mirror
conversation:

  "Tell me about Mel's 4th house"
      → finds Mel via the asker's forum membership
      → returns Mel's hydrated chart, user_id, display name
      → so the deterministic V2-V6 engines run on Mel's chart, not Pete's.

The resolver is name-aware (looks across the user's forums and saved people)
and falls back to `about_person_id` when supplied. It returns None when no
target person is detectable — in that case the caller defaults to the
user's own chart.

Build marker: ask-mirror-astrology-v7
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

logger = logging.getLogger(__name__)

BUILD_MARKER = "ask-mirror-astrology-v7"

# Names that look like first names but aren't person references.
# Kept short — we only want to skip obvious false positives.
_NAME_STOPWORDS = {
    "i", "me", "my", "mine", "you", "your", "yours",
    "sun", "moon", "mars", "venus", "mercury", "jupiter",
    "saturn", "uranus", "neptune", "pluto", "chiron",
    "north", "south", "node", "ascendant", "midheaven",
    "lilith", "vertex", "juno", "ceres", "pallas", "vesta", "eris",
    "fortune", "spirit",
}

# Possessive name pattern: "Mel's 4th house", "Mel's Sun", "Thaddeus's chart"
_POSSESSIVE_NAME_RE = re.compile(
    r"\b([A-Z][a-z]{2,15})(?:'s|s')\b",
)
# Bare-name + astrology-object pattern: "Mel 4th house", "Thaddeus chart"
_BARE_NAME_RE = re.compile(
    r"\b([A-Z][a-z]{2,15})\b"
)


# ---------------------------------------------------------------------------
# Name extraction
# ---------------------------------------------------------------------------
def extract_candidate_names(message: str) -> List[str]:
    """Pull capitalised possessive-name candidates from the message.

    Returns a unique list, possessive form first, bare form second.
    Excludes obvious astrology bodies (Sun, Moon, etc.) via stopword set.
    """
    if not message:
        return []
    found: List[str] = []
    seen = set()
    for m in _POSSESSIVE_NAME_RE.finditer(message):
        name = m.group(1)
        if name.lower() in _NAME_STOPWORDS:
            continue
        if name.lower() not in seen:
            found.append(name)
            seen.add(name.lower())
    # Only include bare names if the message contains an astrology keyword
    # — guards against picking up random capitalised words.
    msg_lower = message.lower()
    has_astro_word = any(w in msg_lower for w in (
        "chart", "house", "sun", "moon", "rising", "ascendant",
        "natal", "transit", "topology", "stellium", "saturn",
    ))
    if has_astro_word:
        for m in _BARE_NAME_RE.finditer(message):
            name = m.group(1)
            if name.lower() in _NAME_STOPWORDS:
                continue
            if name.lower() not in seen:
                found.append(name)
                seen.add(name.lower())
    return found


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------
async def resolve_target_member(
    *,
    db,
    asker_user_id: str,
    message: str,
    about_person_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Try to resolve a target person + chart for the question.

    Resolution order:
      1. If about_person_id is set → look up saved_people; if that person
         has a linked user_id (because they are also an Emergent user
         themselves), use that user's chart. Otherwise fall through.
      2. Look for possessive / bare names in the message and try to match
         a forum-member name across the asker's forums. If a match has a
         user_id with a stored chart, return it.
      3. Fall back to saved_people by name (no chart available, returns
         metadata only with chart=None — caller may choose to compute
         later).

    Returns:
        {
          "target_user_id":   "...",        # may be None if no chart
          "target_name":      "Mel",
          "target_chart":     {...},         # may be None
          "source":           "forum_member" | "saved_person" | "about_person_id",
          "forum_id":         "...",         # context, may be None
        }
      or None if no target detectable.
    """
    # 1. Explicit about_person_id wins
    if about_person_id:
        person = await db.saved_people.find_one({
            "id": about_person_id,
            "user_id": asker_user_id,
        })
        if person:
            linked_user_id = person.get("linked_user_id") or person.get("emergent_user_id")
            target_chart = None
            if linked_user_id:
                target_chart = await db.charts.find_one({"user_id": linked_user_id})
            logger.info(
                f"[MemberResolver] about_person_id hit: name={person.get('name')!r} "
                f"linked_user_id={linked_user_id} chart_found={target_chart is not None}"
            )
            return {
                "target_user_id": linked_user_id,
                "target_name":    person.get("name"),
                "target_chart":   target_chart,
                "source":         "about_person_id",
                "forum_id":       None,
            }

    # 2. Name-based forum-member lookup
    candidate_names = extract_candidate_names(message)
    if not candidate_names:
        logger.debug("[MemberResolver] no candidate names in message")
        return None

    # Find all forums the asker belongs to
    asker_memberships = await db.forum_members.find(
        {"user_id": asker_user_id}
    ).to_list(length=20)
    asker_forum_ids = [m.get("forum_id") for m in asker_memberships if m.get("forum_id")]

    if asker_forum_ids:
        # All members in those forums
        co_members = await db.forum_members.find({
            "forum_id": {"$in": asker_forum_ids},
            "user_id":  {"$ne": asker_user_id},
        }).to_list(length=100)
        for cand in candidate_names:
            cand_lower = cand.lower()
            for member in co_members:
                m_name = (member.get("name") or member.get("display_name") or "")
                if m_name and m_name.lower() == cand_lower:
                    target_uid = member.get("user_id")
                    target_chart = (
                        await db.charts.find_one({"user_id": target_uid})
                        if target_uid else None
                    )
                    logger.info(
                        f"[MemberResolver] forum-member hit: name={m_name!r} "
                        f"forum_id={member.get('forum_id')} "
                        f"target_user_id={target_uid} "
                        f"chart_found={target_chart is not None}"
                    )
                    return {
                        "target_user_id": target_uid,
                        "target_name":    m_name,
                        "target_chart":   target_chart,
                        "source":         "forum_member",
                        "forum_id":       member.get("forum_id"),
                    }

    # 3. Saved-people by name (no chart unless linked)
    for cand in candidate_names:
        cand_re = re.compile(rf"^{re.escape(cand)}$", re.IGNORECASE)
        sp = await db.saved_people.find_one({
            "user_id": asker_user_id,
            "name":    cand_re,
        })
        if sp:
            linked_user_id = sp.get("linked_user_id") or sp.get("emergent_user_id")
            target_chart = None
            if linked_user_id:
                target_chart = await db.charts.find_one({"user_id": linked_user_id})
            logger.info(
                f"[MemberResolver] saved-person hit: name={sp.get('name')!r} "
                f"linked_user_id={linked_user_id} chart_found={target_chart is not None}"
            )
            return {
                "target_user_id": linked_user_id,
                "target_name":    sp.get("name"),
                "target_chart":   target_chart,
                "source":         "saved_person",
                "forum_id":       None,
            }

    logger.debug(
        f"[MemberResolver] no match for candidates={candidate_names} "
        f"asker={asker_user_id}"
    )
    return None


__all__ = [
    "extract_candidate_names",
    "resolve_target_member",
    "BUILD_MARKER",
]
