"""
Pattern Drift Detection Module v0.1

Detects possible Enneagram pattern movement (stress/growth drift) over time
using signals from user reflections and journal content.

Architecture: Deterministic layer → Structured JSON → Template-based UI text
Philosophy: "Mirror, not guru" - observational, not diagnostic

Signal sources (v0.1):
- reflections (weight: 1.0)
- journal entries (weight: 0.8)
- chat snippets (reserved for future, weight: 0.5)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import re
import logging

logger = logging.getLogger(__name__)

# ============================================
# ENNEAGRAM DRIFT MODEL (Deterministic)
# ============================================

ENNEAGRAM_DRIFT_MAP = {
    1: {"stress": 4, "growth": 7},
    2: {"stress": 8, "growth": 4},
    3: {"stress": 9, "growth": 6},
    4: {"stress": 2, "growth": 1},
    5: {"stress": 7, "growth": 8},
    6: {"stress": 3, "growth": 9},
    7: {"stress": 1, "growth": 5},
    8: {"stress": 5, "growth": 2},
    9: {"stress": 6, "growth": 3}
}

# Type names for display
TYPE_NAMES = {
    1: "The Reformer",
    2: "The Helper",
    3: "The Achiever",
    4: "The Individualist",
    5: "The Investigator",
    6: "The Loyalist",
    7: "The Enthusiast",
    8: "The Challenger",
    9: "The Peacemaker"
}

# ============================================
# DRIFT SIGNAL CLUSTERS (Keyword-based)
# ============================================

DRIFT_SIGNAL_CLUSTERS = {
    1: {
        "keywords": ["control", "correct", "standards", "discipline", "should", "fix", "wrong", "right", "perfect", "improve", "criticize", "judge", "mistake", "rules", "order"],
        "themes": ["structure", "standards", "control", "perfectionism", "criticism"]
    },
    2: {
        "keywords": ["help", "support", "needed", "approval", "care", "love", "give", "others", "appreciate", "thank", "serve", "selfless", "sacrifice", "attention", "relationship"],
        "themes": ["helping", "connection", "approval", "care", "relationships"]
    },
    3: {
        "keywords": ["achieve", "success", "perform", "image", "productivity", "win", "goal", "accomplish", "recognition", "status", "efficient", "busy", "driven", "impressive", "compete"],
        "themes": ["achievement", "success", "image", "productivity", "recognition"]
    },
    4: {
        "keywords": ["misunderstood", "unique", "depth", "meaning", "longing", "different", "authentic", "special", "melancholy", "envy", "intense", "emotional", "creative", "missing", "loneliness"],
        "themes": ["uniqueness", "depth", "meaning", "authenticity", "longing"]
    },
    5: {
        "keywords": ["withdraw", "space", "observe", "analyze", "privacy", "think", "understand", "knowledge", "alone", "energy", "boundary", "detach", "study", "research", "distant"],
        "themes": ["withdrawal", "analysis", "knowledge", "privacy", "observation"]
    },
    6: {
        "keywords": ["worry", "doubt", "security", "certainty", "reassurance", "trust", "fear", "anxiety", "worst", "plan", "prepare", "loyal", "question", "suspicious", "support"],
        "themes": ["security", "doubt", "anxiety", "loyalty", "preparation"]
    },
    7: {
        "keywords": ["escape", "options", "possibilities", "avoid", "excited", "fun", "adventure", "freedom", "bored", "new", "plan", "future", "optimistic", "distract", "restless"],
        "themes": ["possibilities", "freedom", "excitement", "avoidance", "options"]
    },
    8: {
        "keywords": ["control", "power", "protect", "strong", "confront", "challenge", "direct", "intense", "anger", "fight", "dominate", "weak", "vulnerable", "justice", "assert"],
        "themes": ["power", "control", "strength", "protection", "confrontation"]
    },
    9: {
        "keywords": ["avoid", "peace", "merge", "comfort", "numb", "harmony", "conflict", "agree", "passive", "slow", "routine", "calm", "disconnect", "procrastinate", "accommodate"],
        "themes": ["peace", "avoidance", "harmony", "comfort", "merging"]
    }
}

# Source weights for signal scoring
SOURCE_WEIGHTS = {
    "reflection": 1.0,
    "journal": 0.8,
    "chat": 0.5  # Reserved for future use
}

# ============================================
# TEMPLATE-BASED SUMMARIES (No LLM for v0.1)
# ============================================

DRIFT_SUMMARY_TEMPLATES = {
    "stress": {
        1: "Possible recent pull toward structure and standards. This sometimes appears when seeking control or order.",
        2: "Possible recent pull toward assertion and intensity. This sometimes appears when feeling unappreciated or depleted.",
        3: "Possible recent pull toward withdrawal and disengagement. This sometimes appears when facing potential failure.",
        4: "Possible recent pull toward connection-seeking and involvement. This sometimes appears when feeling emotionally depleted.",
        5: "Possible recent pull toward scattered activity and distraction. This sometimes appears when feeling mentally overwhelmed.",
        6: "Possible recent pull toward image-focus and performance. This sometimes appears when seeking external validation.",
        7: "Possible recent pull toward criticism and rigidity. This sometimes appears when options feel limited.",
        8: "Possible recent pull toward withdrawal and secrecy. This sometimes appears when feeling vulnerable.",
        9: "Possible recent pull toward anxiety and vigilance. This sometimes appears when harmony is threatened."
    },
    "growth": {
        1: "Possible recent access to spontaneity and lightness. This sometimes appears when feeling resourced and accepting.",
        2: "Possible recent access to emotional depth and authenticity. This sometimes appears when honoring your own needs.",
        3: "Possible recent access to loyalty and commitment. This sometimes appears when valuing depth over image.",
        4: "Possible recent access to objectivity and discipline. This sometimes appears when channeling emotion into action.",
        5: "Possible recent access to confident engagement. This sometimes appears when moving from observation to participation.",
        6: "Possible recent access to inner peace and trust. This sometimes appears when relaxing vigilance.",
        7: "Possible recent access to focused depth. This sometimes appears when staying with one thing.",
        8: "Possible recent access to openheartedness and care. This sometimes appears when letting others in.",
        9: "Possible recent access to assertive energy and clarity. This sometimes appears when claiming your presence."
    }
}

# ============================================
# DRIFT DETECTION ENGINE
# ============================================

def extract_text_signals(text: str) -> Dict[int, List[str]]:
    """Extract keyword signals from text for each Enneagram type."""
    if not text:
        return {}
    
    text_lower = text.lower()
    signals = {}
    
    for type_num, cluster in DRIFT_SIGNAL_CLUSTERS.items():
        found_keywords = []
        for keyword in cluster["keywords"]:
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                found_keywords.append(keyword)
        
        if found_keywords:
            signals[type_num] = found_keywords
    
    return signals


def calculate_type_scores(
    reflections: List[Dict],
    journal_entries: List[Dict],
    baseline_type: int
) -> Dict[int, float]:
    """
    Calculate weighted scores for each Enneagram type based on signals.
    Only scores stress and growth candidates for the baseline type.
    """
    stress_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["stress"]
    growth_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["growth"]
    
    # Initialize scores only for relevant types
    scores = {
        stress_candidate: 0.0,
        growth_candidate: 0.0
    }
    
    all_keywords = {stress_candidate: [], growth_candidate: []}
    sources_used = set()
    
    # Process reflections (weight: 1.0)
    for reflection in reflections:
        # Check multiple possible text fields
        text_fields = [
            reflection.get("insight", ""),
            reflection.get("perspective", ""),
            reflection.get("response", ""),
            reflection.get("content", "")
        ]
        combined_text = " ".join(filter(None, text_fields))
        
        if combined_text:
            signals = extract_text_signals(combined_text)
            for type_num in [stress_candidate, growth_candidate]:
                if type_num in signals:
                    scores[type_num] += len(signals[type_num]) * SOURCE_WEIGHTS["reflection"]
                    all_keywords[type_num].extend(signals[type_num])
                    sources_used.add("reflection")
    
    # Process journal entries (weight: 0.8)
    for entry in journal_entries:
        content = entry.get("content", "")
        if content:
            signals = extract_text_signals(content)
            for type_num in [stress_candidate, growth_candidate]:
                if type_num in signals:
                    scores[type_num] += len(signals[type_num]) * SOURCE_WEIGHTS["journal"]
                    all_keywords[type_num].extend(signals[type_num])
                    sources_used.add("journal")
    
    # Deduplicate keywords
    for type_num in all_keywords:
        all_keywords[type_num] = list(set(all_keywords[type_num]))
    
    return scores, all_keywords, list(sources_used)


def determine_confidence_label(score: float, threshold: float = 5.0) -> str:
    """
    Determine confidence label based on score.
    Returns: 'low', 'emerging', or 'moderate'
    """
    ratio = score / threshold if threshold > 0 else 0
    
    if ratio < 0.5:
        return "low"
    elif ratio < 1.0:
        return "emerging"
    else:
        return "moderate"


def calculate_pattern_drift(
    user_id: str,
    baseline_type: int,
    reflections: List[Dict],
    journal_entries: List[Dict],
    window_days: int = 14,
    threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Main drift calculation function.
    
    Returns structured JSON for the interpretation layer.
    """
    logger.info(f"[PatternDrift] Calculating drift for user {user_id}, baseline type {baseline_type}")
    
    if baseline_type not in ENNEAGRAM_DRIFT_MAP:
        logger.warning(f"[PatternDrift] Invalid baseline type: {baseline_type}")
        return {
            "baseline_type": baseline_type,
            "drift_detected": False,
            "drift_candidate": None,
            "direction": None,
            "confidence_label": "low",
            "confidence_score": 0.0,
            "signal_keywords": [],
            "signal_sources": [],
            "signals_detected": 0,
            "window_days": window_days,
            "summary": None,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    stress_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["stress"]
    growth_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["growth"]
    
    # Calculate scores
    scores, all_keywords, sources_used = calculate_type_scores(
        reflections, journal_entries, baseline_type
    )
    
    stress_score = scores.get(stress_candidate, 0)
    growth_score = scores.get(growth_candidate, 0)
    
    total_signals = int(stress_score + growth_score)
    
    logger.info(f"[PatternDrift] Scores - Stress ({stress_candidate}): {stress_score}, Growth ({growth_candidate}): {growth_score}")
    
    # Determine drift direction (if any)
    drift_detected = False
    drift_candidate = None
    direction = None
    winning_score = 0.0
    winning_keywords = []
    summary = None
    
    # Check if either candidate exceeds threshold
    if stress_score >= threshold or growth_score >= threshold:
        drift_detected = True
        
        # Determine which direction is stronger
        if stress_score > growth_score:
            direction = "stress"
            drift_candidate = stress_candidate
            winning_score = stress_score
            winning_keywords = all_keywords.get(stress_candidate, [])[:5]  # Top 5 keywords
            summary = DRIFT_SUMMARY_TEMPLATES["stress"].get(baseline_type)
        else:
            direction = "growth"
            drift_candidate = growth_candidate
            winning_score = growth_score
            winning_keywords = all_keywords.get(growth_candidate, [])[:5]
            summary = DRIFT_SUMMARY_TEMPLATES["growth"].get(baseline_type)
    elif stress_score > 0 or growth_score > 0:
        # Below threshold but some signals detected - report the stronger one as "emerging"
        if stress_score >= growth_score and stress_score > 0:
            direction = "stress"
            drift_candidate = stress_candidate
            winning_score = stress_score
            winning_keywords = all_keywords.get(stress_candidate, [])[:5]
            summary = DRIFT_SUMMARY_TEMPLATES["stress"].get(baseline_type)
        elif growth_score > 0:
            direction = "growth"
            drift_candidate = growth_candidate
            winning_score = growth_score
            winning_keywords = all_keywords.get(growth_candidate, [])[:5]
            summary = DRIFT_SUMMARY_TEMPLATES["growth"].get(baseline_type)
    
    # Calculate confidence
    confidence_score = min(winning_score / threshold, 1.0) if threshold > 0 else 0.0
    confidence_label = determine_confidence_label(winning_score, threshold)
    
    result = {
        "baseline_type": baseline_type,
        "baseline_name": TYPE_NAMES.get(baseline_type, f"Type {baseline_type}"),
        "drift_detected": drift_detected,
        "drift_candidate": drift_candidate,
        "drift_candidate_name": TYPE_NAMES.get(drift_candidate) if drift_candidate else None,
        "direction": direction,
        "confidence_label": confidence_label,
        "confidence_score": round(confidence_score, 2),
        "signal_keywords": winning_keywords,
        "signal_sources": sources_used,
        "signals_detected": total_signals,
        "window_days": window_days,
        "summary": summary,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"[PatternDrift] Result: direction={direction}, candidate={drift_candidate}, confidence={confidence_label}")
    
    return result


# ============================================
# CACHE UTILITIES
# ============================================

def get_cache_key(user_id: str) -> str:
    """Generate cache key for pattern drift results."""
    return f"pattern_drift_{user_id}"


def is_cache_valid(cached_result: Dict, max_age_hours: int = 24) -> bool:
    """Check if cached result is still valid."""
    if not cached_result or "calculated_at" not in cached_result:
        return False
    
    try:
        calculated_at = datetime.fromisoformat(cached_result["calculated_at"].replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - calculated_at
        return age.total_seconds() < (max_age_hours * 3600)
    except (ValueError, TypeError):
        return False
