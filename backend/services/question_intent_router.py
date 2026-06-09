"""Intent classifier — Mirror Chat v2  ·  question-intent-router-v1
Slice A: relationship/career/home/spiritual domain + optional target name.
Read-only — no DB, no LLM."""
import re
from typing import Any, Dict, Optional, List

BUILD_MARKER = "question-intent-router-v1"

_DOMAINS = [
    ("relationship", r"\b(marriage|spouse|husband|wife|partner|partnership|relationship|relationships|divorce|intimacy|connection|connections|dating|soulmate|romance|romantic|love\s+life)\b"),
    ("career",       r"\b(career|work|profession|professional|business|leadership|job|vocation|calling|success)\b"),
    ("home",         r"\b(family|home|parents|parent|mother|father|children|child|kids|upbringing|household|domestic)\b"),
    ("spiritual",    r"\b(soul|destiny|awakening|spiritual|spirituality|enlightenment|dharma|life\s+purpose|higher\s+self)\b"),
]
_DOMAIN_RES = [(d, re.compile(p, re.I)) for d, p in _DOMAINS]

# "Tell me about Mel's chart" / "what does Mel's Sun" / "for Mel" / "with Mel"
_TARGET_RE = re.compile(
    r"\b(?:about|for|with|of|tell\s+me\s+about|how\s+(?:does|is))\s+([A-Z][a-z]{1,30})(?:'s|\b)",
)
_OWN_RE = re.compile(r"\b(my|mine|me|i\b|for\s+me|in\s+my\s+chart)\b", re.I)


def classify_question_intent(message: str) -> Dict[str, Any]:
    """Returns dict with domain, target, lens_priority, raw_message.
    domain = "general" means no domain-specific routing should fire."""
    if not message or not isinstance(message, str):
        return {"domain": "general", "target": None, "lens_priority": [], "raw_message": message}

    text = message.strip()
    domain = "general"
    for d, rgx in _DOMAIN_RES:
        if rgx.search(text):
            domain = d
            break

    target = None
    m = _TARGET_RE.search(text)
    if m:
        name = m.group(1)
        # Common false positives — ignore
        if name.lower() not in {"the", "my", "your", "their", "this", "that", "today"}:
            target = name
    if target is None and _OWN_RE.search(text):
        target = "self"

    LENS_PRIORITY = {
        "relationship": ["astrology_relationship_layer", "relationship_field",
                         "human_design_relationship", "enneagram_attachment", "numerology"],
        "career":       ["astrology_career_layer", "human_design_work_style",
                         "enneagram_work_pattern", "numerology"],
        "home":         ["astrology_home_layer", "relationship_field",
                         "human_design_family_pattern"],
        "spiritual":    ["astrology_spiritual_layer", "human_design_purpose",
                         "numerology_life_path"],
        "general":      [],
    }

    return {
        "domain":        domain,
        "target":        target,
        "lens_priority": LENS_PRIORITY[domain],
        "raw_message":   text,
    }
