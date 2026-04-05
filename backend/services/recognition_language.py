"""
Recognition Language System v1.0
=================================

OBJECTIVE:
Transform Mirror outputs to match "recognition clarity" — 
User reads and says "That's exactly what just happened."
NOT "That's an interesting explanation."

CORE PRINCIPLES:
1. Recognition First — Start with observable behavior
2. System Invisibility — No mention of astrology/HD/Enneagram
3. Environmental Context — "This shows up more in [context]"
4. No Identity Locking — Situational language, not identity statements
5. Reduced Drama — Grounded, observable phrasing
6. Open Reflection Endings — Questions, not instructions

SUCCESS METRIC:
Immediate recognition, not intellectual understanding.
"""

import re
import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =============================================================================
# PATTERN CONTEXT (Environmental Activation)
# =============================================================================

@dataclass
class PatternContext:
    """
    Environmental tag for pattern amplification.
    Used to generate: "In this environment, this pattern gets louder."
    """
    trigger: str = "environment"  # environment / person / timing / group
    amplification: str = "increase"  # increase / soften / distort
    context_phrase: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "trigger": self.trigger,
            "amplification": self.amplification,
            "context_phrase": self.context_phrase,
        }


# =============================================================================
# SYSTEM TERMS TO REMOVE (Rule 2: System Invisibility)
# =============================================================================

SYSTEM_TERMS_TO_REMOVE = [
    # Full astrological phrases to remove (ordered by specificity - most specific first)
    (r"Your\s+(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)\s+(in\s+the\s+\d+\w*\s+house|in\s+\w+)\s*", ""),
    (r"(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)\s+(square|trine|opposite|conjunct|sextile)\s+(your\s+)?(natal\s+)?(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)", "This energy"),
    (r"(transiting|transit)\s+(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)", "something"),
    (r"(according to|based on)\s+(your\s+)?(chart|profile|astrology|human design|enneagram)\s*,?\s*", ""),
    (r"your\s+(natal\s+)?(chart|profile)\s+(shows|indicates|suggests)", "there's a pattern where"),
    (r"As\s+a\s+(Generator|Manifestor|Projector|Reflector)\s+type\s+(in\s+Human\s+Design\s*,?\s*)?", ""),
    (r"Your\s+Enneagram\s+Type\s+\d(\s+wing\s+\d)?\s*", "You "),
    
    # Astrology terms
    (r"\b(astrolog\w+)\b", ""),
    (r"\b(horoscope)\b", ""),
    (r"\b(zodiac)\b", ""),
    (r"\b(natal chart)\b", ""),
    (r"\b(birth chart)\b", ""),
    (r"\b(Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)\s+retrograde\b", "something in a holding pattern"),
    (r"\bretrograde\b", "in a holding pattern"),
    (r"\bascendant\b", ""),
    (r"\bmidheaven\b", ""),
    (r"\b(the\s+)?\d+(st|nd|rd|th)\s+house\b", ""),
    
    # Human Design terms
    (r"\bhuman design\b", ""),
    (r"\b(generator|manifestor|projector|reflector)\s+type\b", ""),
    (r"\bgate\s+\d+\b", ""),
    (r"\bchannel\s+\d+[-/]\d+\b", ""),
    (r"\b(defined|undefined)\s+(center|channel)\b", ""),
    (r"\b(sacral|emotional|splenic)\s+(authority|response)\b", ""),
    
    # Enneagram terms  
    (r"\benneagram\b", ""),
    (r"\btype\s+\d\b", ""),
    (r"\bwing\s+\d\b", ""),
    (r"\binstinctual\s+variant\b", ""),
    (r"\btritype\b", ""),
    
    # Numerology / BaZi
    (r"\bnumerolog\w+\b", ""),
    (r"\blife path\s+\d+\b", ""),
    (r"\b(bazi|ba zi)\b", ""),
    (r"\bday master\b", ""),
    
    # Generic system references
    (r"\b(your\s+)?(chart|profile)\s+(says|shows|indicates)\b", ""),
    (r"\baccording to\b", ""),
    (r"\bthis indicates\b", "this suggests"),
]

# =============================================================================
# DRAMATIC TERMS TO SOFTEN (Rule 5: Reduce Drama by 30%)
# =============================================================================

DRAMATIC_REPLACEMENTS = {
    # Extreme → Grounded
    "hardest": "most challenging",
    "terrifying": "uncomfortable",
    "devastating": "difficult",
    "impossible": "very difficult",
    "invisible": "hard to see",
    "unbearable": "heavy",
    "overwhelming": "a lot to hold",
    "crushing": "weighing on you",
    "excruciating": "painful",
    "catastrophic": "significant",
    "nightmare": "difficult situation",
    "disaster": "setback",
    "destroyed": "disrupted",
    "shattered": "broken",
    "ruined": "damaged",
    
    # Hyperbolic → Observable
    "always": "often",
    "never": "rarely",
    "everyone": "many people",
    "no one": "few people",
    "completely": "largely",
    "totally": "mostly",
    "absolutely": "clearly",
    "definitely": "likely",
    "certainly": "probably",
    
    # Vague intensity → Specific
    "very": "",
    "really": "",
    "extremely": "noticeably",
    "incredibly": "notably",
    "deeply": "strongly",
    "profoundly": "significantly",
}

# =============================================================================
# IDENTITY LOCKS TO CONVERT (Rule 4: No Identity Locking)
# =============================================================================

IDENTITY_PATTERNS = [
    # "You are X" → "You tend to X"
    (r"\bYou are someone who\s+(\w+)", r"You tend to \1"),
    (r"\bYou are a person who\s+(\w+)", r"You tend to \1"),
    (r"\bYou are the type who\s+(\w+)", r"You tend to \1"),
    (r"\bYou're someone who\s+(\w+)", r"You tend to \1"),
    
    # "You are [adjective]" → "You tend to be [adjective]"
    (r"\bYou are (naturally |inherently |fundamentally )?(\w+)", r"You tend to be \2"),
    (r"\bYou're (naturally |inherently |fundamentally )?(\w+)", r"You tend to be \2"),
    
    # "Your nature is" → "A pattern you notice is"
    (r"\bYour nature is\b", "A pattern you may notice is"),
    (r"\bYour essence is\b", "What tends to show up is"),
    (r"\bYou have always been\b", "You've often found yourself"),
    
    # "You will always" → "You often"
    (r"\bYou will always\b", "You often"),
    (r"\bYou'll always\b", "You often"),
]

# =============================================================================
# RECOGNITION STARTERS (Rule 1: Always Start with Recognition)
# =============================================================================

RECOGNITION_OPENERS = {
    "hesitation": [
        "You were about to decide — then paused again.",
        "Right before acting, something pulled you back.",
        "The moment was there, but you waited.",
    ],
    "conflict_avoidance": [
        "You felt the tension rise, and went quiet.",
        "There was something to say — and you didn't.",
        "You noticed yourself stepping back from the edge.",
    ],
    "overthinking": [
        "The decision was clear, but you kept circling.",
        "You already knew — but kept asking anyway.",
        "One more angle. Then another. Then another.",
    ],
    "seeking_approval": [
        "You checked to see if they agreed before continuing.",
        "Their reaction mattered more than your own.",
        "You adjusted based on what you thought they wanted.",
    ],
    "self_doubt": [
        "For a moment you trusted yourself — then questioned it.",
        "The confidence flickered, then dimmed.",
        "You second-guessed what you already knew.",
    ],
    "people_pleasing": [
        "You said yes when you meant not really.",
        "Their comfort became your priority.",
        "You absorbed their mood without meaning to.",
    ],
    "withdrawal": [
        "You pulled back before anyone noticed.",
        "The space felt easier than the connection.",
        "You chose silence over the risk of being seen.",
    ],
    "control": [
        "You tightened your grip — just to feel steady.",
        "The plan had to go a certain way.",
        "Letting go felt like losing something important.",
    ],
    "pressure": [
        "The weight showed up again — familiar, heavy.",
        "Something was expected, and you felt it.",
        "The demand was unspoken but clear.",
    ],
    "default": [
        "Something familiar happened again.",
        "You noticed the pattern before you named it.",
        "It showed up — the same way it usually does.",
    ],
}

# =============================================================================
# ENVIRONMENTAL CONTEXT PHRASES (Rule 3: Contextualize Patterns)
# =============================================================================

ENVIRONMENTAL_CONTEXT = {
    "group": [
        "In this group, it gets louder.",
        "Around these people, it tends to surface.",
        "Something about this space brings it out.",
    ],
    "relationship": [
        "With this person, the pattern sharpens.",
        "In this dynamic, it becomes harder to ignore.",
        "This connection tends to activate it.",
    ],
    "work": [
        "At work, this version of you shows up more.",
        "In professional settings, it's more pronounced.",
        "This context tends to trigger it.",
    ],
    "timing": [
        "Lately, it's been more present.",
        "This season tends to bring it forward.",
        "Right now, it's closer to the surface.",
    ],
    "stress": [
        "Under pressure, it intensifies.",
        "When things get tight, this is what emerges.",
        "Stress tends to amplify this.",
    ],
    "default": [
        "In certain situations, this shows up more.",
        "Some contexts make this louder.",
        "It tends to surface in specific moments.",
    ],
}

# =============================================================================
# OPEN REFLECTION ENDINGS (Rule 6: End with Open Reflection)
# =============================================================================

OPEN_REFLECTION_ENDINGS = [
    "See if that's true.",
    "Or maybe it's just how this moment feels.",
    "Notice what comes up.",
    "What does that bring up?",
    "Is that what's actually happening?",
    "Sit with that for a moment.",
    "Let it be seen.",
    "What if you just noticed it?",
    "No need to fix it yet.",
    "Just name it for now.",
    "Check if that lands.",
    "Does that match your experience?",
]

# =============================================================================
# MAIN TRANSFORMATION FUNCTIONS
# =============================================================================

def remove_system_language(text: str) -> str:
    """
    Rule 2: Remove all system language (astrology, HD, Enneagram).
    Systems inform backend only — never visible in output.
    """
    result = text
    
    for pattern_tuple in SYSTEM_TERMS_TO_REMOVE:
        pattern, replacement = pattern_tuple
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # Clean up double spaces and awkward punctuation
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\s+([,.])', r'\1', result)
    result = re.sub(r'([,.])\s*([,.])', r'\1', result)
    result = re.sub(r'^\s*[,.:;]\s*', '', result)  # Remove leading punctuation
    result = result.strip()
    
    return result


def soften_dramatic_language(text: str) -> str:
    """
    Rule 5: Reduce drama by 30%.
    Replace hyperbolic terms with grounded, observable phrasing.
    """
    result = text
    
    for dramatic, grounded in DRAMATIC_REPLACEMENTS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(dramatic), re.IGNORECASE)
        if grounded:
            result = pattern.sub(grounded, result)
        else:
            # Remove filler words like "very", "really"
            result = pattern.sub("", result)
    
    # Clean up double spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


def convert_identity_to_situational(text: str) -> str:
    """
    Rule 4: No identity locking.
    Convert "You are X" to "You tend to X".
    """
    result = text
    
    for pattern, replacement in IDENTITY_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def get_recognition_opener(pattern_key: str, seed_hash: int = 0) -> str:
    """
    Rule 1: Always start with recognition.
    Get a recognition-based opener for a pattern.
    """
    openers = RECOGNITION_OPENERS.get(pattern_key, RECOGNITION_OPENERS["default"])
    return openers[seed_hash % len(openers)]


def get_environmental_context(context_type: str = "default", seed_hash: int = 0) -> str:
    """
    Rule 3: Contextualize patterns (environmental activation).
    Returns: "In this environment, this pattern gets louder."
    """
    contexts = ENVIRONMENTAL_CONTEXT.get(context_type, ENVIRONMENTAL_CONTEXT["default"])
    return contexts[seed_hash % len(contexts)]


def get_open_reflection_ending(seed_hash: int = 0) -> str:
    """
    Rule 6: End with open reflection, not instruction.
    """
    return OPEN_REFLECTION_ENDINGS[seed_hash % len(OPEN_REFLECTION_ENDINGS)]


def transform_to_recognition_language(
    text: str,
    pattern_key: Optional[str] = None,
    context_type: Optional[str] = None,
    add_opener: bool = False,
    add_context: bool = False,
    add_reflection: bool = False,
    seed_hash: int = 0,
) -> str:
    """
    Main transformation function.
    Applies all recognition language rules to input text.
    
    Args:
        text: Input text to transform
        pattern_key: Pattern identifier for recognition opener
        context_type: Context type for environmental phrase
        add_opener: Whether to prepend a recognition opener
        add_context: Whether to add environmental context
        add_reflection: Whether to append open reflection ending
        seed_hash: For consistent variation selection
        
    Returns:
        Transformed text matching recognition language standards
    """
    if not text:
        return text
    
    result = text
    
    # Apply all transformation rules
    result = remove_system_language(result)
    result = soften_dramatic_language(result)
    result = convert_identity_to_situational(result)
    
    # Optional enhancements
    components = []
    
    if add_opener and pattern_key:
        opener = get_recognition_opener(pattern_key, seed_hash)
        components.append(opener)
    
    components.append(result)
    
    if add_context and context_type:
        context_phrase = get_environmental_context(context_type, seed_hash)
        components.append(context_phrase)
    
    if add_reflection:
        reflection = get_open_reflection_ending(seed_hash)
        components.append(reflection)
    
    return " ".join(components)


def generate_recognition_insight(
    pattern_key: str,
    pattern_description: str,
    context_type: str = "default",
    seed_hash: int = 0,
) -> Dict[str, str]:
    """
    Generate a complete recognition-first insight.
    
    Returns:
        {
            "recognition": "You were about to decide — then paused again.",
            "observation": "...transformed pattern description...",
            "context": "In this group, it gets louder.",
            "reflection": "See if that's true."
        }
    """
    return {
        "recognition": get_recognition_opener(pattern_key, seed_hash),
        "observation": transform_to_recognition_language(
            pattern_description,
            pattern_key=pattern_key,
            seed_hash=seed_hash,
        ),
        "context": get_environmental_context(context_type, seed_hash),
        "reflection": get_open_reflection_ending(seed_hash),
    }


def build_pattern_context(
    trigger: str = "environment",
    amplification: str = "increase",
    forum_id: Optional[str] = None,
    relationship_context: Optional[str] = None,
) -> PatternContext:
    """
    Build a PatternContext for environmental activation tagging.
    
    Args:
        trigger: environment / person / timing / group
        amplification: increase / soften / distort
        forum_id: If in forum context, use for context phrase
        relationship_context: If relationship context, use for phrase
        
    Returns:
        PatternContext with appropriate context_phrase
    """
    context = PatternContext(trigger=trigger, amplification=amplification)
    
    if forum_id:
        context.trigger = "group"
        context.context_phrase = "In this space, the pattern tends to surface."
    elif relationship_context:
        context.trigger = "person"
        context.context_phrase = "With this person, it becomes harder to ignore."
    elif trigger == "timing":
        context.context_phrase = "Right now, it's closer to the surface."
    elif trigger == "stress":
        context.context_phrase = "Under pressure, this is what emerges."
    else:
        context.context_phrase = "In certain situations, this shows up more."
    
    return context


# =============================================================================
# VALIDATION / QUALITY CHECK
# =============================================================================

def validate_recognition_output(text: str) -> Tuple[bool, List[str]]:
    """
    Validate that output meets recognition language standards.
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    # Check for system language leakage
    for pattern in SYSTEM_TERMS_TO_REMOVE[:10]:  # Check key terms
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"System language detected: {pattern}")
    
    # Check for identity locking
    identity_locks = [
        r"\bYou are someone who\b",
        r"\bYou are a person who\b",
        r"\bYour nature is\b",
    ]
    for pattern in identity_locks:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"Identity lock detected: {pattern}")
    
    # Check for dramatic language
    dramatic_terms = ["hardest", "terrifying", "devastating", "impossible", "nightmare"]
    for term in dramatic_terms:
        if term.lower() in text.lower():
            issues.append(f"Dramatic term detected: {term}")
    
    # Check for instructional endings
    instructional = [
        r"\bYou should\b",
        r"\bYou need to\b",
        r"\bYou must\b",
        r"\bTry to\b",
        r"\bMake sure to\b",
    ]
    for pattern in instructional:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"Instructional language detected: {pattern}")
    
    return len(issues) == 0, issues


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PatternContext",
    "remove_system_language",
    "soften_dramatic_language",
    "convert_identity_to_situational",
    "get_recognition_opener",
    "get_environmental_context",
    "get_open_reflection_ending",
    "transform_to_recognition_language",
    "generate_recognition_insight",
    "build_pattern_context",
    "validate_recognition_output",
    "RECOGNITION_OPENERS",
    "ENVIRONMENTAL_CONTEXT",
    "OPEN_REFLECTION_ENDINGS",
]
