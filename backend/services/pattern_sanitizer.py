"""Pattern Label Sanitization - V5.0

Ensures NO internal pattern keys, test labels, or debug-like tokens 
ever appear in user-facing copy.

RULES:
- Internal pattern keys like "escalating_test", "strong_urge_wrong_timing" → clean language
- Underscores become spaces and are rewritten behaviorally
- If no clean mapping exists, omit entirely or rewrite generically
- Never leak: test, debug, internal, placeholder, _id suffixes
"""

import re
from typing import Optional


# =============================================================================
# PATTERN KEY → HUMAN LANGUAGE MAPPING
# =============================================================================

PATTERN_KEY_MAPPING = {
    # Test patterns (should NEVER appear)
    "escalating_test": "building pressure",
    "test_tension": "inner tension",
    "test_pattern": "what's surfacing",
    
    # Timing patterns
    "strong_urge_wrong_timing": "the urge to act before it's time",
    "premature_initiation": "starting before you're ready",
    "forcing_timing": "trying to make things happen too fast",
    "waiting_game": "the pressure of waiting",
    "threshold_moment": "standing at a turning point",
    
    # Action patterns
    "urgency_vs_readiness": "wanting to move but not trusting the direction",
    "action_taken": "having already acted",
    "pushing_through": "forcing past resistance",
    "holding_back": "holding yourself back",
    
    # Emotional patterns
    "frustration": "frustration building",
    "emotional_intensity": "heightened emotional charge",
    "doubt": "self-doubt surfacing",
    "internal_doubt": "questioning yourself",
    "low_clarity": "unclear direction",
    "seeking_validation": "wanting confirmation",
    
    # Relational patterns
    "relationship_tension": "tension with someone",
    "boundary_pressure": "pressure around boundaries",
    "communication_gap": "things left unsaid",
    
    # Control patterns
    "control_grip": "gripping for control",
    "letting_go": "struggling to release",
    "surrender_resistance": "resistance to letting things unfold",
    
    # Cycle patterns
    "transition_pressure": "being in transition",
    "cycle_event": "something cycling through",
    "recurring_pattern": "a pattern returning",
    "returning_pattern": "something familiar resurfacing",
    
    # Generic fallbacks
    "general_tension": "something asking for attention",
    "general": "what's present",
    "unknown": "what's stirring",
}


# =============================================================================
# FORBIDDEN TOKENS (Never show these in user-facing copy)
# =============================================================================

FORBIDDEN_TOKENS = [
    "_test",
    "_debug",
    "_internal",
    "_placeholder",
    "_id",
    "test_",
    "debug_",
    "placeholder_",
    "undefined",
    "null",
    "NaN",
    "N/A",
    "TODO",
    "FIXME",
]


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def sanitize_pattern_key(pattern_key: str) -> str:
    """
    Convert internal pattern key to clean human-readable language.
    
    Examples:
        "escalating_test" → "building pressure"
        "strong_urge_wrong_timing" → "the urge to act before it's time"
    """
    if not pattern_key:
        return "what's surfacing"
    
    # Check direct mapping first
    key_lower = pattern_key.lower().strip()
    if key_lower in PATTERN_KEY_MAPPING:
        return PATTERN_KEY_MAPPING[key_lower]
    
    # Check if contains forbidden tokens
    for token in FORBIDDEN_TOKENS:
        if token.lower() in key_lower:
            # Remove the forbidden part and try to map remainder
            cleaned = key_lower.replace(token.lower(), "").strip("_").strip()
            if cleaned in PATTERN_KEY_MAPPING:
                return PATTERN_KEY_MAPPING[cleaned]
            # Fall back to generic
            return "what's present"
    
    # Convert underscores to spaces and clean up
    human_readable = pattern_key.replace("_", " ").strip()
    
    # Capitalize first letter only (not title case)
    if human_readable:
        human_readable = human_readable[0].lower() + human_readable[1:]
    
    return human_readable


def sanitize_text_content(text: str) -> str:
    """
    Remove or replace any internal tokens/patterns from user-facing text.
    
    Scans text for forbidden tokens and pattern keys, replacing them
    with clean language or removing entirely.
    """
    if not text:
        return text
    
    result = text
    
    # Check for forbidden tokens
    for token in FORBIDDEN_TOKENS:
        if token.lower() in result.lower():
            result = re.sub(re.escape(token), "", result, flags=re.IGNORECASE)
    
    # Check for pattern keys in text (surrounded by spaces or punctuation)
    for key, replacement in PATTERN_KEY_MAPPING.items():
        # Match pattern key as whole word
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, result, re.IGNORECASE):
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # Also check for underscore-separated words that look like internal keys
    underscore_pattern = r'\b([a-z]+_[a-z_]+)\b'
    matches = re.findall(underscore_pattern, result.lower())
    for match in matches:
        # This looks like an internal key - sanitize it
        sanitized = sanitize_pattern_key(match)
        result = re.sub(r'\b' + re.escape(match) + r'\b', sanitized, result, flags=re.IGNORECASE)
    
    # Clean up double spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


def sanitize_tendency_phrase(raw_phrase: str) -> str:
    """
    Sanitize tendency phrases for "How this interacts with you" section.
    
    Converts internal-looking phrases into natural language.
    
    Examples:
        "This touches your tendency around escalating_test" 
        → "This touches your tendency around building pressure when clarity isn't there"
    """
    if not raw_phrase:
        return raw_phrase
    
    result = raw_phrase
    
    # Replace any pattern keys
    for key, replacement in PATTERN_KEY_MAPPING.items():
        if key.lower() in result.lower():
            result = re.sub(
                r'\b' + re.escape(key) + r'\b', 
                replacement, 
                result, 
                flags=re.IGNORECASE
            )
    
    # Also handle underscore patterns
    underscore_pattern = r'\b([a-z]+_[a-z_]+)\b'
    matches = re.findall(underscore_pattern, result.lower())
    for match in matches:
        sanitized = sanitize_pattern_key(match)
        result = re.sub(r'\b' + re.escape(match) + r'\b', sanitized, result, flags=re.IGNORECASE)
    
    return result


def is_safe_for_display(text: str) -> bool:
    """
    Check if text is safe to display to users (no internal tokens).
    """
    if not text:
        return True
    
    text_lower = text.lower()
    
    # Check forbidden tokens
    for token in FORBIDDEN_TOKENS:
        if token.lower() in text_lower:
            return False
    
    # Check for obvious underscore patterns (internal keys)
    if re.search(r'\b[a-z]+_[a-z]+_[a-z]+\b', text_lower):
        return False
    
    return True


def ensure_clean_copy(text: str, fallback: str = "") -> str:
    """
    Ensure text is clean for display, returning fallback if not salvageable.
    """
    if not text:
        return fallback
    
    sanitized = sanitize_text_content(text)
    
    if is_safe_for_display(sanitized):
        return sanitized
    
    # Still has issues - return fallback
    return fallback if fallback else sanitized
