"""relationship_router_v2 — Mirror Chat V2 Slice B1 (SHADOW MODE).

Resolves who the user is currently talking about based on explicit target,
name mention, last-target memory, and active frame.  Shadow-only; does not
mutate any user state.

B2 additions (still receipt-only):
  * Missing-target fallback: if a proper name appears in the message that
    does NOT resolve against `saved_people`, we emit `target_unresolved`
    plus a `proposed_action` payload of the form
        {type: "add_to_circle",
         suggested_name: <name>,
         reason: <short>,
         source_text: <verbatim user text>,
         confidence: <0..1>}
    This stays in the diagnostic receipt only — no UI/CTA is wired yet and
    no relationship-role inference is performed.  The intent is purely
    telemetry-gathering for the B2 cutover review window.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

log = logging.getLogger("relationship_router_v2")
ROUTER_VERSION = "relationship_router_v2.1.0"

_PRONOUN_RE = re.compile(r"\b(us|we|he|she|they|them|him|her)\b", re.IGNORECASE)

# Proper-name candidate: capitalised token, optionally followed by 's possessive.
# We capture letters only (avoids matching numbers like "4th").
_NAME_TOKEN_RE = re.compile(r"\b([A-Z][a-z]{1,30})\b")

# Tokens that look like proper names but are not people we'd add to a
# circle.  Kept conservative — when in doubt we'd rather skip a candidate
# than fire a false-positive proposed_action.
_NAME_BLOCKLIST: set = {
    # sentence starters / wh-words
    "How", "What", "Why", "When", "Where", "Who", "Which", "Whose",
    "Tell", "Show", "Can", "Could", "Should", "Would", "Will", "Shall",
    "Am", "Is", "Are", "Was", "Were", "Do", "Does", "Did", "Has", "Have",
    "Had", "May", "Might", "Must", "Let",
    # pronouns / determiners
    "I", "Me", "My", "Mine", "We", "Us", "Our", "Ours",
    "You", "Your", "Yours", "He", "She", "Him", "Her", "His", "Hers",
    "They", "Them", "Their", "Theirs", "It", "Its",
    "This", "That", "These", "Those", "There", "Here",
    "A", "An", "The", "Any", "All", "Some", "None",
    "But", "And", "Or", "If", "So", "Yet",
    # filler & meta
    "Yes", "No", "Ok", "Okay", "Hi", "Hey", "Hello",
    "Mirror", "Chat", "Cross", "Lens", "Lenses", "Frame", "Forum",
    "Reflection", "RL", "Probe", "Test", "Today",
    # planets / luminaries / nodes / sensitive points
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron", "Lilith", "Ceres", "Pallas",
    "Juno", "Vesta", "North", "South", "Node", "Nodes",
    "Ascendant", "Descendant", "Midheaven", "MC", "IC", "Asc", "Dsc",
    # signs
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    # lenses / systems
    "Human", "Design", "Enneagram", "Astrology", "Numerology",
    "BaZi", "Bazi", "Vedic", "Western", "Tropical", "Sidereal",
    "Manifestor", "Generator", "Projector", "Reflector",
    "Type", "Profile", "Authority", "Strategy", "Gate", "Channel",
    # houses / aspects shorthand
    "House", "Sign", "Square", "Trine", "Sextile", "Opposition", "Conjunction",
    # days / months (sometimes capitalised mid-sentence)
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
    # placeholders / qualifiers
    "God", "Universe", "Life", "Soul", "Spirit", "Self", "Other",
}

# Role nouns: "my husband", "my wife", "the kids" — these are NOT proper
# names but are sometimes lowercased.  Tracked here for documentation
# purposes; they do not currently emit proposed_actions because
# (per product) we don't want role-inference auto-creates.
_ROLE_NOUNS = {
    "husband", "wife", "partner", "spouse", "boyfriend", "girlfriend",
    "ex", "mother", "father", "mom", "dad", "son", "daughter",
    "sister", "brother", "sibling", "kid", "kids", "child", "children",
    "boss", "manager", "colleague", "coworker", "friend", "mentor",
    "client", "team",
}


@dataclass
class RelationshipResolution:
    self_user_id: str
    target: Optional[str]
    role: Optional[str]
    closeness: float
    relationship_weight: float
    active_frame: str
    context_mode: str  # SELF | OTHER | RELATIONAL
    resolution_path: List[str]
    conflicts: List[str]
    missing_data: List[str]
    # B2 additions — RECEIPT-ONLY:
    target_unresolved_name: Optional[str] = None
    proposed_action: Optional[Dict[str, Any]] = None
    router_version: str = ROUTER_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _name_in_message(text: str, names: List[str]) -> Optional[str]:
    tl = (text or "").lower()
    best = None
    for n in names:
        if not n:
            continue
        if n.lower() in tl:
            if best is None or len(n) > len(best):
                best = n
    return best


def _extract_proper_name_candidates(text: str) -> List[str]:
    """Pull capitalised tokens out of `text` that look like proper names.

    Filters out the blocklist (planets, signs, wh-words, etc.).  Sentence-
    initial capitalisation is allowed — common false-positive starters
    are already enumerated in `_NAME_BLOCKLIST`.
    """
    if not text:
        return []
    raw = _NAME_TOKEN_RE.findall(text)
    if not raw:
        return []
    out: List[str] = []
    seen: set = set()
    for tok in raw:
        if tok in _NAME_BLOCKLIST:
            continue
        if tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
    return out


def _build_proposed_action(
    *, suggested_name: str, source_text: str, reason: str, confidence: float
) -> Dict[str, Any]:
    """Receipt-only payload describing a *suggested* next step.

    Intentionally narrow: just a typed suggestion, the verbatim user text
    that triggered it, and a short human-readable reason.  No
    relationship-role inference, no auto-create.  Surfaced to UI only
    after the post-B2 telemetry review window approves it.
    """
    return {
        "type": "add_to_circle",
        "suggested_name": suggested_name,
        "reason": reason,
        "source_text": source_text,
        "confidence": round(float(confidence), 3),
    }


def resolve_relationship_context(
    *, self_user_id: str,
    user_message: str,
    active_frame: str = "self",
    target_id: Optional[str] = None,
    saved_people: Optional[List[Dict[str, Any]]] = None,
    forum_topology: Optional[Dict[str, Any]] = None,
    last_target_id: Optional[str] = None,
) -> RelationshipResolution:
    saved_people = saved_people or []
    resolution_path: List[str] = []
    missing: List[str] = []
    conflicts: List[str] = []
    proposed_action: Optional[Dict[str, Any]] = None
    target_unresolved_name: Optional[str] = None

    target = None
    role = None
    closeness = 0.0
    weight = 0.0

    # 1. explicit target id wins
    if target_id:
        target = target_id
        resolution_path.append("explicit_target_id")
        match = next((p for p in saved_people if p.get("id") == target_id), None)
        if match:
            role = match.get("role")
            closeness = float(match.get("closeness") or 0.0)
            weight = float(match.get("weight") or closeness)
        else:
            missing.append("target_not_in_saved_people")

    # 2. name in message — match against saved_people first
    if not target and saved_people:
        names = [p.get("name") for p in saved_people if p.get("name")]
        hit = _name_in_message(user_message or "", names)
        if hit:
            match = max((p for p in saved_people if p.get("name") == hit),
                        key=lambda p: float(p.get("closeness") or 0.0), default=None)
            if match:
                target = match.get("id") or match.get("name")
                role = match.get("role")
                closeness = float(match.get("closeness") or 0.0)
                weight = float(match.get("weight") or closeness)
                resolution_path.append("mentioned_name")

    # 3. implicit pronoun + last-target memory
    if not target and last_target_id and _PRONOUN_RE.search(user_message or ""):
        target = last_target_id
        match = next((p for p in saved_people if p.get("id") == last_target_id), None)
        if match:
            role = match.get("role")
            closeness = float(match.get("closeness") or 0.0)
            weight = float(match.get("weight") or closeness)
        resolution_path.append("pronoun_memory")

    # 4. forum frame default
    if not target and active_frame == "forum" and forum_topology:
        active = (forum_topology or {}).get("active_member_id")
        if active:
            target = active
            resolution_path.append("forum_active_member")

    if not target and active_frame in ("forum", "member"):
        missing.append("forum_target_unresolved")

    # 5. MISSING-TARGET FALLBACK (B2, receipt-only)
    # Run *whenever* no target has been resolved yet AND the message
    # contains a proper-name candidate that doesn't match any saved
    # person.  We deliberately don't gate this on active_frame because
    # name-mentions in the "self" frame are the most common ambiguous
    # case in the historical chat corpus.
    if not target:
        saved_names_lc = {(p.get("name") or "").lower()
                          for p in saved_people if p.get("name")}
        candidates = _extract_proper_name_candidates(user_message or "")
        unresolved = [c for c in candidates if c.lower() not in saved_names_lc]
        if unresolved:
            # take the first unresolved candidate — keep it simple
            target_unresolved_name = unresolved[0]
            missing.append("target_unresolved")
            # confidence reflects: 1) message length normalised, 2) how
            # cleanly the candidate stands out.  Capped to 0.85 — we are
            # never *certain* this is a person and the proposed_action is
            # a suggestion, not an assertion.
            base = 0.55 if len(unresolved) == 1 else 0.45
            if active_frame in ("member", "forum"):
                base += 0.10
            confidence = min(base, 0.85)
            proposed_action = _build_proposed_action(
                suggested_name=target_unresolved_name,
                source_text=(user_message or "").strip()[:500],
                reason=(
                    f"name '{target_unresolved_name}' appears in message but "
                    f"is not in user's saved_people"
                ),
                confidence=confidence,
            )

    context_mode = "RELATIONAL" if target else "SELF"
    if active_frame == "member" and not target:
        # frame demanded a target but we couldn't find one
        conflicts.append("frame=member_but_no_target")

    return RelationshipResolution(
        self_user_id=self_user_id,
        target=target,
        role=role,
        closeness=round(closeness, 3),
        relationship_weight=round(weight, 3),
        active_frame=active_frame,
        context_mode=context_mode,
        resolution_path=resolution_path or ["none"],
        conflicts=conflicts,
        missing_data=missing,
        target_unresolved_name=target_unresolved_name,
        proposed_action=proposed_action,
    )
