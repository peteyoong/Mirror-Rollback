"""
Pattern Language Context Separator V1.0

PROBLEM SOLVED:
Home and Forum were producing identical outputs because both used the same 
pattern detection + language generation path.

SOLUTION:
This module provides context-aware language generation that transforms the same
pattern signal into differentiated experiences:

HOME CONTEXT:
- First person / direct recognition
- Focus: internal experience
- Example: "You've been here before...", "Part of you knows..."

FORUM CONTEXT:
- Field-based / relational language
- Focus: shared space dynamics
- NEVER use "you've been here before"
- Example: "Something in this space...", "The dynamic between you..."

GUARDRAILS:
Forum language MUST:
- Avoid second-person psychological statements
- Avoid identity statements ("you always", "you've been")
- Use field framing ("this space", "between you", "the dynamic")
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONTEXT TYPES
# =============================================================================

class LanguageContext:
    HOME = "home"
    FORUM = "forum"


# =============================================================================
# HOME CONTEXT LANGUAGE (First Person / Internal)
# =============================================================================

HOME_PATTERN_LANGUAGE = {
    # Recognition patterns (internal, direct)
    "recognition_intro": [
        "You've been here before.",
        "Part of you knows this place.",
        "This isn't new to you.",
        "You recognize this.",
        "Something in you has felt this before.",
    ],
    
    # Escalation language (personal, direct)
    "escalation_level_1": [  # Present
        "This is familiar.",
        "You've seen this shape before.",
        "Something here you know.",
    ],
    "escalation_level_2": [  # Recurring (with soft entry)
        "This keeps coming back.",
        "You're here again.",
        "This pattern hasn't let go yet.",
    ],
    "escalation_level_3": [  # Escalating
        "This is getting louder.",
        "It's asking for attention now.",
        "You can't ignore this much longer.",
    ],
    
    # Breakthrough language (personal victory)
    "breakthrough_low": [
        "Something might be shifting.",
        "There's a gap here you didn't have before.",
    ],
    "breakthrough_medium": [
        "You moved through something.",
        "This didn't catch you the way it used to.",
    ],
    "breakthrough_high": [
        "You've actually changed here.",
        "This pattern has less hold on you now.",
    ],
    
    # Soft entry phrases (personal)
    "soft_entry": [
        "This might feel familiar.",
        "You may have noticed this before.",
        "Part of you might recognize...",
    ],
}


# =============================================================================
# FORUM CONTEXT LANGUAGE (Field-Based / Relational)
# =============================================================================

FORUM_PATTERN_LANGUAGE = {
    # Recognition patterns (field-based, relational)
    "recognition_intro": [
        "Something in this space has surfaced before.",
        "This dynamic isn't new to the room.",
        "The field carries this pattern.",
        "There's a familiar tension here.",
        "The space holds a shape that's been here before.",
    ],
    
    # Escalation language (field-based, shared)
    "escalation_level_1": [  # Present
        "Something is present in the field.",
        "A pattern has entered the space.",
        "The room is holding something.",
    ],
    "escalation_level_2": [  # Recurring (with soft entry)
        "This keeps surfacing between you.",
        "The space has been here before.",
        "A familiar dynamic is returning.",
    ],
    "escalation_level_3": [  # Escalating
        "This is building in the field.",
        "The tension is growing between you.",
        "Something in the space is demanding attention.",
    ],
    
    # Breakthrough language (relational shift)
    "breakthrough_low": [
        "Something in the dynamic may be shifting.",
        "There's a gap in the pattern that wasn't there.",
    ],
    "breakthrough_medium": [
        "The space moved through something.",
        "The dynamic didn't catch in the usual way.",
    ],
    "breakthrough_high": [
        "Something has genuinely changed between you.",
        "This pattern has loosened its grip on the field.",
    ],
    
    # Soft entry phrases (relational)
    "soft_entry": [
        "This might feel familiar to the room.",
        "The space may recognize this shape.",
        "Something here echoes what came before.",
    ],
}


# =============================================================================
# PERSPECTIVE TRANSFORMER
# =============================================================================

# Maps internal pattern concepts to field-based language
PERSPECTIVE_TRANSFORMS = {
    # Internal → Field
    "hesitation": "unspoken pause in the space",
    "resistance": "something the room is pushing against",
    "avoidance": "a topic the field keeps circling",
    "anxiety": "tension that hasn't found words",
    "defensiveness": "guardedness between you",
    "withdrawal": "someone stepping back from the field",
    "silence": "what's being held but not said",
    "frustration": "friction that hasn't been named",
    "overwhelm": "too much moving at once",
    "stuckness": "the field not finding its next move",
    "confusion": "something unclear between you",
    "doubt": "uncertainty in the shared space",
    "fear": "something the space is protecting against",
    "anger": "heat that hasn't been expressed",
    "sadness": "weight the field is carrying",
    "disconnection": "distance that's grown between you",
    "misalignment": "different directions pulling at once",
    "pacing mismatch": "different tempos in the room",
}


def transform_to_field_language(internal_concept: str) -> str:
    """
    Transform an internal pattern concept to field-based language.
    
    Example:
    "hesitation" → "unspoken pause in the space"
    """
    return PERSPECTIVE_TRANSFORMS.get(
        internal_concept.lower(), 
        f"something in the space around {internal_concept}"
    )


# =============================================================================
# MAIN LANGUAGE GENERATOR
# =============================================================================

def generate_pattern_language(
    pattern_type: str,
    context: str,
    escalation_level: int = 0,
    breakthrough_confidence: int = 0,
    seed_hash: int = 0,
) -> str:
    """
    Generate context-aware pattern language.
    
    Args:
        pattern_type: Type of pattern ("recognition", "escalation", "breakthrough", "soft_entry")
        context: Either "home" or "forum"
        escalation_level: 0-3 (dormant, present, recurring, escalating)
        breakthrough_confidence: 0-3 (none, low, medium, high)
        seed_hash: For consistent variation selection
        
    Returns:
        Context-appropriate language string
    """
    
    # Select language bank based on context
    if context == LanguageContext.HOME:
        language_bank = HOME_PATTERN_LANGUAGE
    elif context == LanguageContext.FORUM:
        language_bank = FORUM_PATTERN_LANGUAGE
    else:
        logger.warning(f"[PatternLanguage] Unknown context: {context}, defaulting to home")
        language_bank = HOME_PATTERN_LANGUAGE
    
    # Generate based on pattern type
    if pattern_type == "recognition_intro":
        phrases = language_bank["recognition_intro"]
        return phrases[seed_hash % len(phrases)]
    
    elif pattern_type == "escalation":
        key = f"escalation_level_{escalation_level}"
        phrases = language_bank.get(key, [])
        if phrases:
            return phrases[seed_hash % len(phrases)]
        return ""
    
    elif pattern_type == "breakthrough":
        if breakthrough_confidence == 1:
            phrases = language_bank["breakthrough_low"]
        elif breakthrough_confidence == 2:
            phrases = language_bank["breakthrough_medium"]
        elif breakthrough_confidence >= 3:
            phrases = language_bank["breakthrough_high"]
        else:
            return ""
        return phrases[seed_hash % len(phrases)]
    
    elif pattern_type == "soft_entry":
        phrases = language_bank["soft_entry"]
        return phrases[seed_hash % len(phrases)]
    
    return ""


def generate_home_language(
    pattern_signal: Dict,
    seed_hash: int = 0,
) -> Dict[str, str]:
    """
    Generate HOME context language from pattern signal.
    
    HOME LANGUAGE CHARACTERISTICS:
    - First person / direct recognition
    - Focus: internal experience
    - Uses "you", "your", "you've been"
    """
    
    escalation = pattern_signal.get("escalation_level", 0)
    breakthrough = pattern_signal.get("breakthrough_confidence", 0)
    
    result = {}
    
    # Recognition intro (if recurring)
    if escalation >= 2:
        result["recognition"] = generate_pattern_language(
            "recognition_intro", LanguageContext.HOME, seed_hash=seed_hash
        )
    
    # Soft entry for level 2
    if escalation == 2:
        result["soft_entry"] = generate_pattern_language(
            "soft_entry", LanguageContext.HOME, seed_hash=seed_hash
        )
    
    # Escalation language
    if escalation > 0:
        result["escalation"] = generate_pattern_language(
            "escalation", LanguageContext.HOME, 
            escalation_level=escalation, seed_hash=seed_hash
        )
    
    # Breakthrough language
    if breakthrough > 0:
        result["breakthrough"] = generate_pattern_language(
            "breakthrough", LanguageContext.HOME,
            breakthrough_confidence=breakthrough, seed_hash=seed_hash
        )
    
    return result


def generate_forum_language(
    pattern_signal: Dict,
    seed_hash: int = 0,
) -> Dict[str, str]:
    """
    Generate FORUM context language from pattern signal.
    
    FORUM LANGUAGE CHARACTERISTICS:
    - Field-based / relational language
    - Focus: shared space dynamics
    - NEVER uses "you've been here before"
    - Uses "the space", "between you", "the dynamic", "the field"
    
    HARD GUARDRAILS:
    - NO second-person psychological statements
    - NO identity statements ("you always", "you've been")
    - MUST use field framing
    """
    
    escalation = pattern_signal.get("escalation_level", 0)
    breakthrough = pattern_signal.get("breakthrough_confidence", 0)
    
    result = {}
    
    # Recognition intro (if recurring) - FIELD FRAMED
    if escalation >= 2:
        result["recognition"] = generate_pattern_language(
            "recognition_intro", LanguageContext.FORUM, seed_hash=seed_hash
        )
    
    # Soft entry for level 2 - FIELD FRAMED
    if escalation == 2:
        result["soft_entry"] = generate_pattern_language(
            "soft_entry", LanguageContext.FORUM, seed_hash=seed_hash
        )
    
    # Escalation language - FIELD FRAMED
    if escalation > 0:
        result["escalation"] = generate_pattern_language(
            "escalation", LanguageContext.FORUM, 
            escalation_level=escalation, seed_hash=seed_hash
        )
    
    # Breakthrough language - RELATIONAL SHIFT
    if breakthrough > 0:
        result["breakthrough"] = generate_pattern_language(
            "breakthrough", LanguageContext.FORUM,
            breakthrough_confidence=breakthrough, seed_hash=seed_hash
        )
    
    return result


# =============================================================================
# VALIDATION / GUARDRAILS
# =============================================================================

FORBIDDEN_FORUM_PHRASES = [
    "you've been here before",
    "you always",
    "you never",
    "you tend to",
    "your pattern",
    "your tendency",
    "you recognize this",
    "part of you",
    "something in you",
]


def validate_forum_language(text: str) -> bool:
    """
    Validate that forum language doesn't violate guardrails.
    
    Returns True if valid, False if contains forbidden phrases.
    """
    text_lower = text.lower()
    for phrase in FORBIDDEN_FORUM_PHRASES:
        if phrase in text_lower:
            logger.warning(f"[PatternLanguage] Forum guardrail violated: found '{phrase}'")
            return False
    return True


def sanitize_forum_language(text: str) -> str:
    """
    Attempt to sanitize forum language by replacing forbidden phrases.
    """
    replacements = {
        "you've been here before": "the space has been here before",
        "you always": "there's often",
        "you never": "something rarely",
        "you tend to": "there's a tendency in the field to",
        "your pattern": "this pattern",
        "your tendency": "this tendency",
        "you recognize this": "the room recognizes this",
        "part of you": "something in the space",
        "something in you": "something in the field",
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
        result = result.replace(old.capitalize(), new.capitalize())
    
    return result
