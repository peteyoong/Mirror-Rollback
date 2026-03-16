"""Mirror Language System
==============================

Standardized interpretation language for Mirror.

All interpretations follow this structure:
1. What may be happening - Observable pattern or situation
2. How this may feel - Emotional/experiential context  
3. What to notice - Specific thing to observe
4. One reflection question - Single clear self-inquiry prompt

Language Rules:
- Use concrete, behavioral language (not vague spiritual terms)
- Avoid deterministic claims (use "may", "might", "could")
- Keep sentences short (6-15 words ideal)
- No spiritual jargon (ascension, divine, cosmic, destiny)
- Use everyday psychological language
"""

import re
from typing import Dict, List, Optional

# ============================================================================
# MIRROR LANGUAGE STRUCTURE
# ============================================================================

class MirrorInsight:
    """Standard structure for all Mirror interpretations."""
    
    def __init__(
        self,
        what_may_be_happening: str,
        how_this_may_feel: str,
        what_to_notice: str,
        reflection_question: str,
        source: Optional[str] = None
    ):
        self.what_may_be_happening = what_may_be_happening
        self.how_this_may_feel = how_this_may_feel
        self.what_to_notice = what_to_notice
        self.reflection_question = reflection_question
        self.source = source
    
    def to_dict(self) -> Dict:
        return {
            "what_may_be_happening": self.what_may_be_happening,
            "how_this_may_feel": self.how_this_may_feel,
            "what_to_notice": self.what_to_notice,
            "reflection_question": self.reflection_question,
            "source": self.source
        }
    
    def to_display(self) -> str:
        """Format for display in UI."""
        return f"""{self.what_may_be_happening}

{self.how_this_may_feel}

{self.what_to_notice}"""


# ============================================================================
# FORBIDDEN TERMS AND REPLACEMENTS
# ============================================================================

FORBIDDEN_TERMS = {
    # Spiritual jargon → grounded alternatives
    "ascension": "growth",
    "divine purpose": "underlying motivation",
    "cosmic destiny": "recurring pattern",
    "universe wants": "there may be a pull toward",
    "spiritual mission": "core orientation",
    "higher self": "deeper awareness",
    "soul contract": "recurring dynamic",
    "karmic": "familiar",
    "awakening": "becoming aware",
    "enlightenment": "clarity",
    "vibrational": "emotional",
    "manifest": "create",
    "abundance": "sufficiency",
    "sacred": "meaningful",
    "blessed": "fortunate",
    
    # Deterministic → tentative
    "you will": "you may",
    "this means": "this might suggest",
    "you are destined": "you may find yourself drawn",
    "meant to": "often drawn to",
    "your purpose is": "you may feel pulled toward",
    "you need to": "you might consider",
    "you should": "you could explore",
    "you must": "it may help to",
    
    # Identity locks → observations
    "you are a": "you may notice yourself being",
    "you are someone who": "you might find yourself",
    "your nature is": "a pattern you may notice is",
    
    # Vague → concrete
    "strong energy": "intensity",
    "emotional theme": "recurring feeling",
    "powerful force": "persistent pull",
    "deep connection": "sense of resonance",
}

VAGUE_PATTERNS = [
    (r"a strong (\w+) may be present", r"\1 might be noticeable"),
    (r"powerful forces are at work", "something persistent seems present"),
    (r"the universe is", "there may be"),
    (r"cosmic (\w+)", r"underlying \1"),
    (r"spiritual (\w+)", r"inner \1"),
]


# ============================================================================
# LANGUAGE CLEANING FUNCTIONS
# ============================================================================

def clean_interpretation_text(text: str) -> str:
    """Clean interpretation text according to Mirror language rules."""
    if not text:
        return text
    
    result = text
    
    # Replace forbidden terms
    for forbidden, replacement in FORBIDDEN_TERMS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(forbidden), re.IGNORECASE)
        result = pattern.sub(replacement, result)
    
    # Apply vague pattern replacements
    for pattern, replacement in VAGUE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def validate_language(text: str) -> List[str]:
    """Check text for language violations and return list of issues."""
    issues = []
    text_lower = text.lower()
    
    # Check for forbidden terms
    forbidden_found = []
    for forbidden in FORBIDDEN_TERMS.keys():
        if forbidden.lower() in text_lower:
            forbidden_found.append(forbidden)
    
    if forbidden_found:
        issues.append(f"Forbidden terms found: {', '.join(forbidden_found)}")
    
    # Check sentence length
    sentences = re.split(r'[.!?]+', text)
    long_sentences = []
    for s in sentences:
        words = s.strip().split()
        if len(words) > 20:
            long_sentences.append(f"'{s[:50]}...' ({len(words)} words)")
    
    if long_sentences:
        issues.append(f"Sentences too long: {'; '.join(long_sentences)}")
    
    # Check for deterministic language
    deterministic_patterns = [
        r"\bwill happen\b",
        r"\bis going to\b",
        r"\byou are\s+\w+ing\b",  # "you are becoming" etc
        r"\bmust\b",
    ]
    for pattern in deterministic_patterns:
        if re.search(pattern, text_lower):
            issues.append(f"Deterministic language pattern: {pattern}")
    
    return issues


# ============================================================================
# REFLECTION QUESTION TEMPLATES
# ============================================================================

REFLECTION_QUESTIONS = {
    "energy_vitality": [
        "What feels like it needs more energy today?",
        "Where does your energy naturally want to go?",
        "What drains you that you could set down?",
        "What restores you that you've been skipping?",
    ],
    "emotional_landscape": [
        "What emotion keeps returning today?",
        "What feeling are you trying not to notice?",
        "What would shift if you named this feeling out loud?",
        "What is this emotion trying to tell you?",
    ],
    "relationships_connection": [
        "What conversation might be waiting to happen?",
        "Who are you thinking about that you haven't reached out to?",
        "What relationship needs attention right now?",
        "What are you holding back in connection with others?",
    ],
    "work_purpose": [
        "What work feels meaningful right now?",
        "What task are you avoiding that might matter?",
        "What would make today's work feel more purposeful?",
        "What are you building that you care about?",
    ],
    "growth_transformation": [
        "What part of you is ready to change?",
        "What are you outgrowing?",
        "What would you do if you weren't afraid of changing?",
        "What pattern keeps repeating that you're tired of?",
    ],
    "intuition_inner_knowing": [
        "What do you already know that you're ignoring?",
        "What is your gut telling you?",
        "What would you do if you trusted yourself more?",
        "What quiet voice have you been dismissing?",
    ],
    "identity_expression": [
        "How are you holding back from being yourself?",
        "What part of you wants to be seen more?",
        "What would authentic expression look like today?",
        "Who are you becoming?",
    ],
    # Generic fallbacks
    "general": [
        "What feels most present right now?",
        "What are you noticing that you usually ignore?",
        "What would shift if you paused here for a moment?",
        "What is asking for your attention?",
    ]
}


def get_reflection_question(domain: str, index: int = 0) -> str:
    """Get a reflection question for a domain."""
    questions = REFLECTION_QUESTIONS.get(domain, REFLECTION_QUESTIONS["general"])
    return questions[index % len(questions)]


# ============================================================================
# STANDARD INTERPRETATION TEMPLATES
# ============================================================================

def format_standard_insight(
    what_happening: str,
    how_feels: str,
    what_notice: str,
    question: str
) -> Dict:
    """Format an insight using the standard Mirror structure."""
    return {
        "primary": clean_interpretation_text(what_happening),
        "support": clean_interpretation_text(how_feels),
        "notice": clean_interpretation_text(what_notice),
        "reflection": question,
    }


# ============================================================================
# DOMAIN-SPECIFIC TEMPLATES
# ============================================================================

DOMAIN_TEMPLATES = {
    "energy_vitality": {
        "recurring": {
            "what_happening": "You may be feeling a persistent pull on your energy—either too much demand or not enough outlet.",
            "how_feels": "This can show up as restlessness, fatigue, or a sense of running on empty.",
            "what_notice": "Notice what activities leave you feeling more alive versus depleted.",
        },
        "stable": {
            "what_happening": "Your energy seems to have found a rhythm that works.",
            "how_feels": "There may be a sense of sustainable flow, neither pushing nor collapsing.",
            "what_notice": "Notice what conditions have allowed this balance.",
        },
        "quiet": {
            "what_happening": "Energy patterns aren't demanding attention right now.",
            "how_feels": "This could feel like a neutral zone—neither charged nor depleted.",
            "what_notice": "Notice if there's something quietly asking for energy you haven't acknowledged.",
        },
    },
    "emotional_landscape": {
        "recurring": {
            "what_happening": "A familiar emotional pattern may be surfacing—something that keeps returning.",
            "how_feels": "This can feel like being caught in a loop, or like the same feeling finding different triggers.",
            "what_notice": "Notice what situation keeps activating this emotional response.",
        },
        "stable": {
            "what_happening": "Your emotional ground seems relatively steady.",
            "how_feels": "There may be a sense of being able to feel without being overwhelmed.",
            "what_notice": "Notice what has helped create this emotional stability.",
        },
        "quiet": {
            "what_happening": "Emotions aren't particularly loud right now.",
            "how_feels": "This could feel neutral, or like there's something being held back.",
            "what_notice": "Notice if there's a feeling waiting to be acknowledged.",
        },
    },
    "relationships_connection": {
        "recurring": {
            "what_happening": "Something in your relational world keeps asking for attention.",
            "how_feels": "This might show up as tension, longing, or a persistent question about connection.",
            "what_notice": "Notice which relationship or dynamic keeps coming to mind.",
        },
        "stable": {
            "what_happening": "Your connections seem to be in a steady place.",
            "how_feels": "There may be a sense of knowing where you stand with important people.",
            "what_notice": "Notice what makes these connections feel secure.",
        },
        "quiet": {
            "what_happening": "Relationship dynamics aren't particularly active right now.",
            "how_feels": "This could feel like a pause in relational intensity.",
            "what_notice": "Notice if there's a conversation you've been putting off.",
        },
    },
    "work_purpose": {
        "recurring": {
            "what_happening": "Questions about work or purpose keep surfacing.",
            "how_feels": "This might feel like restlessness, dissatisfaction, or a pull toward something more meaningful.",
            "what_notice": "Notice what kind of contribution feels important to you right now.",
        },
        "stable": {
            "what_happening": "Your sense of purpose seems grounded.",
            "how_feels": "There may be a feeling of alignment between effort and meaning.",
            "what_notice": "Notice what makes your current work feel worthwhile.",
        },
        "quiet": {
            "what_happening": "Purpose and work questions aren't particularly active.",
            "how_feels": "This could be a neutral period, or a time of steady focus.",
            "what_notice": "Notice if there's a creative impulse you've been ignoring.",
        },
    },
    "growth_transformation": {
        "recurring": {
            "what_happening": "Something in you may be ready for change.",
            "how_feels": "This can feel like pressure, anticipation, or discomfort with the status quo.",
            "what_notice": "Notice what part of your life feels too small or outdated.",
        },
        "stable": {
            "what_happening": "Growth seems to be happening at a sustainable pace.",
            "how_feels": "There may be a sense of integration—absorbing recent changes.",
            "what_notice": "Notice what you've learned recently that's settling in.",
        },
        "quiet": {
            "what_happening": "Transformation isn't urgently demanding attention.",
            "how_feels": "This could be a period of consolidation, or preparation for the next shift.",
            "what_notice": "Notice if there's resistance to something that wants to change.",
        },
    },
    "intuition_inner_knowing": {
        "recurring": {
            "what_happening": "Your inner knowing may be trying to get your attention.",
            "how_feels": "This can show up as a persistent sense that something is off, or a quiet certainty you keep ignoring.",
            "what_notice": "Notice what your gut has been telling you that you haven't acted on.",
        },
        "stable": {
            "what_happening": "Your intuition seems clear and accessible.",
            "how_feels": "There may be a sense of trust in your own knowing.",
            "what_notice": "Notice what helped you develop this inner clarity.",
        },
        "quiet": {
            "what_happening": "Intuitive signals aren't particularly strong right now.",
            "how_feels": "This could be a clear period, or a time when the signal is subtle.",
            "what_notice": "Notice if there's a quiet voice you've been dismissing.",
        },
    },
    "identity_expression": {
        "recurring": {
            "what_happening": "Questions about who you are or how you express yourself keep returning.",
            "how_feels": "This might feel like uncertainty, a desire for authenticity, or friction between inner and outer selves.",
            "what_notice": "Notice where you feel most like yourself, and where you feel constrained.",
        },
        "stable": {
            "what_happening": "Your sense of identity seems grounded.",
            "how_feels": "There may be a feeling of knowing who you are, even if others don't fully see it.",
            "what_notice": "Notice what allows you to feel authentic.",
        },
        "quiet": {
            "what_happening": "Identity questions aren't particularly loud right now.",
            "how_feels": "This could be a settled period, or a time of quiet self-discovery.",
            "what_notice": "Notice if there's a part of yourself you've been hiding.",
        },
    },
}


def get_domain_interpretation(domain_id: str, signal_strength: str) -> Dict:
    """Get a standardized interpretation for a domain based on signal strength."""
    domain_template = DOMAIN_TEMPLATES.get(domain_id, DOMAIN_TEMPLATES.get("growth_transformation"))
    strength_template = domain_template.get(signal_strength, domain_template.get("stable"))
    
    return format_standard_insight(
        what_happening=strength_template["what_happening"],
        how_feels=strength_template["how_feels"],
        what_notice=strength_template["what_notice"],
        question=get_reflection_question(domain_id)
    )
