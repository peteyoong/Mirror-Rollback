"""
Relational Awareness Layer
==========================

Build marker: relational-awareness-v1

When a Mirror chat turn is about a SAVED PERSON (not just the user), the
interpretation must shift.  The same insight lands differently when it's
about a spouse vs. a child vs. a cofounder vs. an ex-partner.

This module:
    1. Classifies any saved-person `relationship_type` into one of nine
       relationship CLASSES (romantic, former, family_adult, child,
       friendship, professional, authority, power_over, mentorship, other).
    2. Defines a per-class INTENSITY CEILING that caps how hard Mirror is
       allowed to land an insight in that relational field (child caps
       below CONFRONTING, romantic+attachment caps at DIRECT, etc).
    3. Detects PROJECTION risk in the user's framing ("why is he always X",
       absolutist language about the other person, recruitment requests).
    4. Builds a RELATIONAL CONTEXT prompt block that tells the LLM:
         a. who the conversation is about
         b. which class the relationship belongs to
         c. the calibration rules for that class
         d. whether projection risk is elevated
         e. the responsibility framing rule
         f. the pseudo-certainty rule (no definitive truths about the
            other person — pattern probabilities only)
    5. Returns a debug payload so frontend dev tools and future relational
       intelligence layers can see the calibration.

This module is deterministic and lens-agnostic.  It plugs in alongside the
existing lens_conversation memory/voice/compression/intensity layers — it
does NOT replace them.  Lens voice still owns interpretation style; this
layer owns relational appropriateness.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1.  Relationship classes
# ---------------------------------------------------------------------------

RELATIONSHIP_CLASSES = {
    "romantic":       {"partner", "spouse"},
    "former":         {"ex_partner"},
    "child":          {"child", "child_minor"},
    "family_adult":   {"parent", "sibling", "family_other"},
    "friendship":     {"friend", "close_friend"},
    "professional":   {"colleague", "client"},
    "authority":      {"boss"},        # user reports to this person
    "power_over":     {"report"},      # user has authority over this person
    "mentorship":     {"mentor", "mentee"},
    "other":          {"other"},
}

# Inverse lookup
_TYPE_TO_CLASS: Dict[str, str] = {}
for cls, types in RELATIONSHIP_CLASSES.items():
    for t in types:
        _TYPE_TO_CLASS[t] = cls


def classify_relationship(relationship_type: Optional[str]) -> str:
    """Return the high-level class for a given relationship_type."""
    if not relationship_type:
        return "other"
    return _TYPE_TO_CLASS.get(relationship_type.lower().strip(), "other")


# ---------------------------------------------------------------------------
# 2.  Per-class intensity ceiling
# ---------------------------------------------------------------------------
#
# These cap the intensity that emotional-timing-v1 may pick when the chat
# is *about* this person.  The user's own lens chat is unaffected.
#
# Reasoning notes:
#   CHILD          — avoid deterministic labeling; parent-guilt amplification
#                    risk; preserve developmental openness.
#   ROMANTIC       — attachment dynamics; do not pathologise the partner.
#   FORMER         — high projection risk; avoid recruiting into a post-mortem.
#   AUTHORITY      — user cannot fix the boss; avoid reckless advice framing.
#   POWER_OVER     — user's blind spots become someone's career — keep
#                    feedback developmental, not punitive.
#   FAMILY_ADULT   — long-arc loyalty patterns; do not side.
#   FRIENDSHIP     — voluntary; least role baggage; can tolerate more.
#   PROFESSIONAL   — workplace contract; structural framing.
#   MENTORSHIP     — developmental, not collusive.
#   OTHER          — conservative default.

_CLASS_INTENSITY_CEILING: Dict[str, str] = {
    "romantic":       "DIRECT",
    "former":         "DIRECT",
    "child":          "DIRECT",        # below CONFRONTING by design
    "family_adult":   "DIRECT",
    "friendship":     "CONFRONTING",   # the only class that allows CONFRONTING
    "professional":   "DIRECT",
    "authority":      "DIRECT",
    "power_over":     "DIRECT",
    "mentorship":     "DIRECT",
    "other":          "DIRECT",
}

_INTENSITY_RANK = {"SOFT": 0, "OBSERVATIONAL": 1, "DIRECT": 2, "CONFRONTING": 3}


def cap_intensity_for_relationship(intensity_mode: str, relationship_class: str) -> str:
    """
    Apply the relational ceiling to a lens-level intensity decision.
    SOFT is never raised; everything else is capped at the class ceiling.
    """
    if intensity_mode == "SOFT":
        return "SOFT"
    ceiling = _CLASS_INTENSITY_CEILING.get(relationship_class, "DIRECT")
    if _INTENSITY_RANK.get(intensity_mode, 1) > _INTENSITY_RANK[ceiling]:
        return ceiling
    return intensity_mode


# ---------------------------------------------------------------------------
# 3.  Projection detection
# ---------------------------------------------------------------------------
#
# The user often describes themselves through the other person.  This
# function flags signals that suggest elevated projection risk so the LLM
# can preserve ambiguity rather than confirm a one-sided narrative.

_ABSOLUTIST_PATTERNS = [
    r"\b(?:he|she|they|my (?:partner|spouse|ex|child|son|daughter|mom|mum|dad|mother|father|boss|colleague|friend))\b[^.!?]{0,30}?\b(?:always|never|constantly|just won't|refuses to|can't|cannot)\b",
    r"\b(?:always|never|constantly)\s+(?:does|says|acts|behaves|treats|makes|gets)\b",
]
_RECRUITMENT_PATTERNS = [
    r"\b(?:am i|am i not|aren'?t i|isn'?t it true that i'?m)\s+right\b",
    r"\bback me up\b", r"\btell me i'?m right\b",
    r"\bso (?:i'?m|i am) (?:not )?the (?:bad|crazy) one\b",
    r"\bwhy (?:is|are) (?:he|she|they|my)\b.*\bso (?:cold|selfish|narcissistic|toxic|controlling|avoidant|cruel|manipulative)\b",
    r"\bwhat'?s (?:wrong|the matter) with (?:him|her|them|my (?:partner|spouse|child|parent|boss))\b",
]
_BLAME_FOCUS_PATTERNS = [
    r"\bif only (?:he|she|they) (?:would|could|had|didn'?t)\b",
    r"\bit'?s (?:all )?(?:his|her|their) fault\b",
    r"\b(?:he|she|they) (?:ruined|destroyed|broke) (?:my|our|everything)\b",
]

_ABS_RE = re.compile("|".join(_ABSOLUTIST_PATTERNS), re.IGNORECASE)
_REC_RE = re.compile("|".join(_RECRUITMENT_PATTERNS), re.IGNORECASE)
_BLM_RE = re.compile("|".join(_BLAME_FOCUS_PATTERNS), re.IGNORECASE)


def detect_projection_signals(user_message: str, history: List[Dict[str, str]]) -> Dict[str, bool]:
    """
    Return projection-risk signals for the current turn.

    Each flag is True/False; the prompt block uses them to decide how
    much ambiguity to preserve.
    """
    msg = (user_message or "")
    return {
        "absolutist_language": bool(_ABS_RE.search(msg)),
        "recruitment_request": bool(_REC_RE.search(msg)),
        "blame_focus":         bool(_BLM_RE.search(msg)),
    }


def projection_risk_level(signals: Dict[str, bool]) -> str:
    """
    Aggregate signals into a level:  "low" | "moderate" | "high".
    """
    score = sum(1 for v in signals.values() if v)
    if score >= 2:
        return "high"
    if score == 1:
        return "moderate"
    return "low"


# ---------------------------------------------------------------------------
# 4.  Calibration copy per relationship class
# ---------------------------------------------------------------------------

_CLASS_CALIBRATION: Dict[str, str] = {
    "romantic": (
        "Class: ROMANTIC PARTNER\n"
        "  - Attachment dynamics are in play on both sides.  Read the\n"
        "    pattern as a SHARED field, not as a verdict on one person.\n"
        "  - Reciprocity matters — describe how the user shows up TOO,\n"
        "    not just what the partner does.\n"
        "  - Do NOT pathologise the partner from one-sided account.\n"
        "  - Closeness raises stakes — emotional reciprocity, not analysis."
    ),
    "former": (
        "Class: FORMER ROMANTIC PARTNER\n"
        "  - You are reading a memory, not a present-tense person.\n"
        "  - Avoid recruiting into a post-mortem.  Do not re-litigate.\n"
        "  - Patterns can still be useful for the user's next relationship;\n"
        "    they are not useful for re-trying this one.\n"
        "  - Treat the former partner as having ALSO changed since."
    ),
    "child": (
        "Class: CHILD (the user's child)\n"
        "  - The child is still becoming.  Do NOT label them deterministically.\n"
        "  - Pattern language must stay developmental, not diagnostic.\n"
        "  - When you describe what the child seems to be doing, route\n"
        "    responsibility back to the user's role in the relationship —\n"
        "    not to assign blame, but because the user is the only one\n"
        "    you can actually coach here.\n"
        "  - Do NOT speculate about pathology, attachment style, or any\n"
        "    fixed trait of a child you have not assessed."
    ),
    "family_adult": (
        "Class: ADULT FAMILY (parent / sibling / extended)\n"
        "  - Long-arc loyalty patterns are present.  The system has its\n"
        "    own gravity that pulls both people back into old roles.\n"
        "  - Do NOT side.  Describe the field, not the verdict.\n"
        "  - The user's leverage is over their OWN position in the field,\n"
        "    not the other person's behaviour."
    ),
    "friendship": (
        "Class: FRIENDSHIP\n"
        "  - Voluntary relationship — neither person is obligated.\n"
        "  - The least role baggage of any class — patterns here are\n"
        "    usually about elective dynamics, not structural ones.\n"
        "  - Can tolerate more directness because the stakes are usually\n"
        "    lower than family or romantic."
    ),
    "professional": (
        "Class: PROFESSIONAL PEER (colleague / client)\n"
        "  - There is a CONTRACT (formal or implicit) shaping the field.\n"
        "  - Frame structurally: scope, expectations, asymmetry of\n"
        "    information, trust over time.\n"
        "  - Do NOT give reckless career advice ('quit', 'confront them').\n"
        "    Help the user see the structure they're inside."
    ),
    "authority": (
        "Class: AUTHORITY (the user reports to this person)\n"
        "  - Real power asymmetry.  The user cannot 'fix' the boss.\n"
        "  - Read the field as: what's actually the user's scope vs.\n"
        "    what's being handed down.\n"
        "  - Avoid coaching the boss through the user; coach the user\n"
        "    on what they can actually move."
    ),
    "power_over": (
        "Class: POWER-OVER (the user has authority over this person)\n"
        "  - The user's blind spot becomes someone else's career scope.\n"
        "  - Feedback framing must stay developmental, not punitive.\n"
        "  - Watch for over-personalising the report's mistakes."
    ),
    "mentorship": (
        "Class: MENTORSHIP\n"
        "  - One person is a few steps ahead of the other on a road.\n"
        "  - Developmental, not collusive.  Real questions over admiration.\n"
        "  - Mentor's model is a doorway, not a ceiling."
    ),
    "other": (
        "Class: OTHER\n"
        "  - The category doesn't fit a neat label, which usually means\n"
        "    the dynamic is specific to these two people.\n"
        "  - Default to conservative framing: preserve ambiguity, avoid\n"
        "    universal claims."
    ),
}


# ---------------------------------------------------------------------------
# 5.  System-prompt block builder
# ---------------------------------------------------------------------------

def build_person_summary_lines(person: Dict[str, Any]) -> List[str]:
    """
    A few short factual lines about the target person — name, relationship,
    optional birth date / location / enneagram, to give the LLM grounding.
    Stays deterministic and non-interpretive.
    """
    lines: List[str] = []
    name = person.get("name") or "(unnamed)"
    rt = person.get("relationship_type") or "other"
    lines.append(f"Name: {name}")
    lines.append(f"Relationship to user: {rt}")
    if person.get("full_birth_name"):
        lines.append(f"Full birth name on file: yes")
    if person.get("birth_date"):
        lines.append(f"Birth date: {person.get('birth_date')}")
    if person.get("birth_location", {}).get("city"):
        loc = person["birth_location"]
        lines.append(f"Birth location: {loc.get('city', '?')}, {loc.get('country', '?')}")
    if person.get("enneagram_type"):
        lines.append(f"Enneagram type (user-supplied): {person['enneagram_type']}")
    return lines


def format_relational_context_block(
    person: Dict[str, Any],
    relationship_class: str,
    projection_signals: Dict[str, bool],
    risk_level: str,
    relationship_intensity_ceiling: str,
) -> str:
    """
    The RELATIONAL CONTEXT system-prompt block.  Always rendered when the
    chat is about a saved person.
    """
    name = person.get("name") or "the other person"
    summary_lines = build_person_summary_lines(person)
    calibration = _CLASS_CALIBRATION.get(relationship_class, _CLASS_CALIBRATION["other"])

    proj_lines: List[str] = []
    if projection_signals.get("absolutist_language"):
        proj_lines.append("  - Absolutist language detected (always/never/constantly).")
    if projection_signals.get("recruitment_request"):
        proj_lines.append("  - Recruitment-style framing detected (asking Mirror to side with the user).")
    if projection_signals.get("blame_focus"):
        proj_lines.append("  - Blame-focused language detected.")
    if not proj_lines:
        proj_lines.append("  - No elevated projection markers in this turn.")

    return (
        f"--- RELATIONAL CONTEXT (relational-awareness-v1) ---\n"
        f"This conversation is about a specific person in the user's life.\n"
        f"You are NOT speaking to that person.  You are interpreting the\n"
        f"relational field between the user and {name}.\n"
        f"\n"
        f"Target person:\n"
        + "\n".join(f"  - {line}" for line in summary_lines) + "\n"
        f"\n"
        f"Relationship classification:\n"
        f"{calibration}\n"
        f"\n"
        f"Projection risk for this turn: {risk_level.upper()}\n"
        + "\n".join(proj_lines) + "\n"
        f"\n"
        f"Relational intensity ceiling for this class: {relationship_intensity_ceiling}\n"
        f"  - The lens-level intensity may be CAPPED by this ceiling.\n"
        f"  - When capped, honour the spirit (still observant) but pull back\n"
        f"    on confrontational framing.\n"
        f"\n"
        f"RELATIONAL RULES (apply to every reply about this person):\n"
        f"  1. Pattern probabilities, NOT pseudo-certainty.  Phrases like\n"
        f"     'tends to', 'is likely to', 'often shows up as' — NOT 'is',\n"
        f"     'always', 'will'.  You do not have this person's full chart\n"
        f"     and even if you did, behaviour is not deterministic.\n"
        f"  2. Preserve ambiguity where appropriate.  The user may be\n"
        f"     describing themselves through this person.  Do not confirm\n"
        f"     a one-sided account by mirroring it back as fact.\n"
        f"  3. Route responsibility to what the USER can actually move.\n"
        f"     Especially in CHILD, ROMANTIC, AUTHORITY, FAMILY_ADULT cases\n"
        f"     — do not over-validate blame narratives.\n"
        f"  4. Describe the FIELD between user and {name}, not a verdict on\n"
        f"     {name}.\n"
        f"  5. Stay observant, NOT recruiting.  You are a mirror, not an ally\n"
        f"     in a dispute."
    )


# ---------------------------------------------------------------------------
# 6.  Debug payload
# ---------------------------------------------------------------------------

def build_relational_debug_payload(
    person: Dict[str, Any],
    relationship_class: str,
    relationship_intensity_ceiling: str,
    projection_signals: Dict[str, bool],
    risk_level: str,
    applied_intensity: str,
    pre_cap_intensity: str,
) -> Dict[str, Any]:
    return {
        "marker": "relational-awareness-v1",
        "about_person": {
            "id": person.get("id"),
            "name": person.get("name"),
            "relationship_type": person.get("relationship_type"),
        },
        "relationship_class": relationship_class,
        "relationship_intensity_ceiling": relationship_intensity_ceiling,
        "projection_signals": projection_signals,
        "projection_risk": risk_level,
        "intensity_pre_cap": pre_cap_intensity,
        "intensity_applied": applied_intensity,
        "intensity_was_capped": applied_intensity != pre_cap_intensity,
    }


# ---------------------------------------------------------------------------
# 7.  Public one-call API
# ---------------------------------------------------------------------------

def compose_relational_block(
    person: Optional[Dict[str, Any]],
    user_message: str,
    history: List[Dict[str, str]],
    lens_intensity_mode: str,
) -> Tuple[str, Dict[str, Any], str]:
    """
    Compose the relational system-prompt block for the current turn.

    Returns:
      (prompt_block_text, relational_debug_payload, applied_intensity_mode)

    If `person` is None (chat not about a saved person), returns
    ("", {}, lens_intensity_mode) — i.e. no-op.

    The third return value is the FINAL intensity to use this turn, after
    applying the relational ceiling cap.
    """
    if not person:
        return "", {}, lens_intensity_mode

    rel_class = classify_relationship(person.get("relationship_type"))
    ceiling = _CLASS_INTENSITY_CEILING.get(rel_class, "DIRECT")
    signals = detect_projection_signals(user_message, history)
    risk = projection_risk_level(signals)
    applied = cap_intensity_for_relationship(lens_intensity_mode, rel_class)

    block = format_relational_context_block(
        person=person,
        relationship_class=rel_class,
        projection_signals=signals,
        risk_level=risk,
        relationship_intensity_ceiling=ceiling,
    )
    debug = build_relational_debug_payload(
        person=person,
        relationship_class=rel_class,
        relationship_intensity_ceiling=ceiling,
        projection_signals=signals,
        risk_level=risk,
        applied_intensity=applied,
        pre_cap_intensity=lens_intensity_mode,
    )
    return block, debug, applied
