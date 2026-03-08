"""
Pattern Drift Detection Module v0.1.1

Detects possible Enneagram pattern movement (stress/growth drift) over time
using signals from user reflections and journal content.

Architecture: Deterministic layer → Structured JSON → Template-based UI text
Philosophy: "Mirror, not guru" - observational, not diagnostic

Signal sources (v0.1):
- reflections (weight: 1.0)
- journal entries (weight: 0.8)
- chat snippets (reserved for future, weight: 0.5)

CONFIDENCE SCORING (v0.1.1):
- confidence_score: Normalized 0.0–1.0 value
- Formula: min(raw_score / threshold, 1.0)
- confidence_label mapping:
  - "low": confidence_score < 0.4
  - "emerging": confidence_score >= 0.4 and < 0.8
  - "moderate": confidence_score >= 0.8

ROBUSTNESS GUARDRAILS (v0.1.1):
- Requires signals from at least 2 separate entries, OR
- Requires at least 2 distinct matched keywords
- Without meeting these, drift_detected = false (even if raw score > threshold)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
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
# v0.1.1: Added anchor keywords and generic term de-weighting
# ============================================

# Generic terms that appear across multiple types - de-weighted
GENERIC_TERMS = {
    "control", "avoid", "need", "want", "feel", "think", 
    "help", "support", "strong", "weak", "good", "bad"
}

# Weight multipliers
ANCHOR_WEIGHT = 1.5      # Distinctive anchor keywords
STANDARD_WEIGHT = 1.0    # Normal keywords
GENERIC_WEIGHT = 0.3     # Generic/overlapping terms

DRIFT_SIGNAL_CLUSTERS = {
    1: {
        # Anchor keywords: highly distinctive for Type 1
        "anchors": ["perfectionist", "reform", "criticize", "moral", "ethical", "resentment", "principle", "integrity"],
        # Standard keywords
        "keywords": ["correct", "standards", "discipline", "should", "fix", "wrong", "right", "improve", "judge", "mistake", "rules", "order", "proper", "flawed"],
        # Generic keywords (de-weighted)
        "generic": ["control"],
        "themes": ["structure", "standards", "perfectionism", "criticism", "principles"]
    },
    2: {
        "anchors": ["selfless", "martyr", "indispensable", "flattery", "seductive", "possessive", "nurture"],
        "keywords": ["needed", "approval", "care", "love", "give", "appreciate", "thank", "serve", "sacrifice", "attention", "relationship", "generous", "pleasing"],
        "generic": ["help", "support", "others"],
        "themes": ["helping", "connection", "approval", "care", "relationships"]
    },
    3: {
        "anchors": ["achieve", "accomplish", "impressive", "image", "status", "deceive", "efficient", "workaholic", "recognition"],
        "keywords": ["success", "perform", "productivity", "win", "goal", "driven", "compete", "excel", "ambitious", "resume", "promotion"],
        "generic": ["busy"],
        "themes": ["achievement", "success", "image", "productivity", "recognition"]
    },
    4: {
        "anchors": ["misunderstood", "unique", "melancholy", "envy", "abandonment", "longing", "authentic", "special"],
        "keywords": ["depth", "meaning", "different", "intense", "emotional", "creative", "missing", "loneliness", "ordinary", "deficient", "identity"],
        "generic": ["feel"],
        "themes": ["uniqueness", "depth", "meaning", "authenticity", "longing"]
    },
    5: {
        "anchors": ["withdraw", "detach", "observe", "hoard", "privacy", "intrude", "compartmentalize", "minimalist"],
        "keywords": ["space", "analyze", "think", "understand", "knowledge", "alone", "energy", "boundary", "study", "research", "distant", "empty", "deplete"],
        "generic": ["need"],
        "themes": ["withdrawal", "analysis", "knowledge", "privacy", "observation"]
    },
    6: {
        "anchors": ["worst-case", "suspicious", "vigilant", "authority", "rebel", "loyal", "anxious", "paranoid", "doubt"],
        "keywords": ["worry", "security", "certainty", "reassurance", "trust", "fear", "anxiety", "prepare", "question", "betrayal", "testing"],
        "generic": ["support"],
        "themes": ["security", "doubt", "anxiety", "loyalty", "preparation"]
    },
    7: {
        "anchors": ["escape", "possibilities", "options", "reframe", "rationalize", "scattered", "gluttony", "fomo"],
        "keywords": ["excited", "fun", "adventure", "freedom", "bored", "new", "plan", "future", "optimistic", "distract", "restless", "limit", "commit"],
        "generic": ["avoid"],
        "themes": ["possibilities", "freedom", "excitement", "avoidance", "options"]
    },
    8: {
        "anchors": ["confront", "dominate", "intimidate", "vulnerable", "justice", "vengeance", "lust", "excess", "bulldoze"],
        "keywords": ["power", "protect", "challenge", "direct", "intense", "anger", "fight", "assert", "weakness", "betray", "territory"],
        "generic": ["control", "strong"],
        "themes": ["power", "strength", "protection", "confrontation"]
    },
    9: {
        "anchors": ["merge", "numb", "asleep", "stubborn", "passive-aggressive", "procrastinate", "accommodate", "invisible"],
        "keywords": ["peace", "harmony", "conflict", "agree", "passive", "slow", "routine", "calm", "disconnect", "inertia", "foggy"],
        "generic": ["avoid", "comfort"],
        "themes": ["peace", "avoidance", "harmony", "comfort", "merging"]
    }
}

# Source weights for signal scoring
SOURCE_WEIGHTS = {
    "reflection": 1.0,
    "journal": 0.8,
    "chat": 0.5  # Reserved for future use
}

# Scoring thresholds and bounds
# v0.1.1: Lowered threshold from 5.0 to 3.0 for more sensitive detection
# This allows emerging signals (0.4-0.8 confidence) to trigger drift_detected
DETECTION_THRESHOLD = 3.0  # Raw score needed for detection
CONFIDENCE_BOUNDS = {
    "low": (0.0, 0.4),
    "emerging": (0.4, 0.8),
    "moderate": (0.8, 1.0)
}

# Robustness guardrails
MIN_DISTINCT_KEYWORDS = 2  # Minimum distinct keywords required
MIN_SEPARATE_ENTRIES = 2   # Minimum separate entries required (alternative to keywords)

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
# DRIFT DETECTION ENGINE (v0.1.1)
# ============================================

def get_keyword_weight(keyword: str, type_num: int) -> float:
    """
    Get the weight for a keyword based on its category.
    Anchors = 1.5x, Standard = 1.0x, Generic = 0.3x
    """
    cluster = DRIFT_SIGNAL_CLUSTERS.get(type_num, {})
    
    if keyword in cluster.get("anchors", []):
        return ANCHOR_WEIGHT
    elif keyword in cluster.get("generic", []):
        return GENERIC_WEIGHT
    elif keyword in cluster.get("keywords", []):
        return STANDARD_WEIGHT
    else:
        return STANDARD_WEIGHT


def extract_text_signals(text: str, target_types: List[int] = None) -> Dict[int, Dict]:
    """
    Extract keyword signals from text for specified Enneagram types.
    
    Returns dict of {type_num: {"keywords": [...], "weighted_score": float}}
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    signals = {}
    
    types_to_check = target_types if target_types else list(DRIFT_SIGNAL_CLUSTERS.keys())
    
    for type_num in types_to_check:
        cluster = DRIFT_SIGNAL_CLUSTERS.get(type_num, {})
        found_keywords = []
        weighted_score = 0.0
        
        # Check all keyword categories
        all_keywords = (
            cluster.get("anchors", []) + 
            cluster.get("keywords", []) + 
            cluster.get("generic", [])
        )
        
        for keyword in all_keywords:
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text_lower)
            
            if matches:
                weight = get_keyword_weight(keyword, type_num)
                found_keywords.append(keyword)
                weighted_score += len(matches) * weight
        
        if found_keywords:
            signals[type_num] = {
                "keywords": found_keywords,
                "weighted_score": weighted_score
            }
    
    return signals


def calculate_type_scores(
    reflections: List[Dict],
    journal_entries: List[Dict],
    baseline_type: int
) -> Tuple[Dict[int, float], Dict[int, List[str]], List[str], Dict[int, int]]:
    """
    Calculate weighted scores for each Enneagram type based on signals.
    Only scores stress and growth candidates for the baseline type.
    
    Returns:
    - scores: {type_num: weighted_score}
    - all_keywords: {type_num: [keywords]}
    - sources_used: [source_names]
    - entry_counts: {type_num: num_entries_with_signals}
    """
    stress_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["stress"]
    growth_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["growth"]
    target_types = [stress_candidate, growth_candidate]
    
    # Initialize tracking
    scores = {stress_candidate: 0.0, growth_candidate: 0.0}
    all_keywords = {stress_candidate: set(), growth_candidate: set()}
    entry_counts = {stress_candidate: 0, growth_candidate: 0}
    sources_used = set()
    
    # Process reflections (weight: 1.0)
    for reflection in reflections:
        text_fields = [
            reflection.get("insight", ""),
            reflection.get("perspective", ""),
            reflection.get("response", ""),
            reflection.get("content", "")
        ]
        combined_text = " ".join(filter(None, text_fields))
        
        if combined_text:
            signals = extract_text_signals(combined_text, target_types)
            for type_num in target_types:
                if type_num in signals:
                    scores[type_num] += signals[type_num]["weighted_score"] * SOURCE_WEIGHTS["reflection"]
                    all_keywords[type_num].update(signals[type_num]["keywords"])
                    entry_counts[type_num] += 1
                    sources_used.add("reflection")
    
    # Process journal entries (weight: 0.8)
    for entry in journal_entries:
        content = entry.get("content", "")
        if content:
            signals = extract_text_signals(content, target_types)
            for type_num in target_types:
                if type_num in signals:
                    scores[type_num] += signals[type_num]["weighted_score"] * SOURCE_WEIGHTS["journal"]
                    all_keywords[type_num].update(signals[type_num]["keywords"])
                    entry_counts[type_num] += 1
                    sources_used.add("journal")
    
    # Convert keyword sets to sorted lists
    all_keywords = {k: sorted(list(v)) for k, v in all_keywords.items()}
    
    return scores, all_keywords, list(sources_used), entry_counts


def determine_confidence(score: float, threshold: float = DETECTION_THRESHOLD) -> Tuple[str, float]:
    """
    Determine confidence label and normalized score.
    
    Returns: (confidence_label, confidence_score)
    
    confidence_score: Normalized 0.0–1.0 value
    - Formula: min(raw_score / threshold, 1.0)
    
    confidence_label:
    - "low": confidence_score < 0.4
    - "emerging": 0.4 <= confidence_score < 0.8
    - "moderate": confidence_score >= 0.8
    """
    # Normalize score to 0-1 range
    confidence_score = min(score / threshold, 1.0) if threshold > 0 else 0.0
    confidence_score = round(confidence_score, 2)
    
    # Determine label based on normalized score
    if confidence_score < CONFIDENCE_BOUNDS["low"][1]:
        label = "low"
    elif confidence_score < CONFIDENCE_BOUNDS["emerging"][1]:
        label = "emerging"
    else:
        label = "moderate"
    
    return label, confidence_score


def passes_robustness_check(
    distinct_keywords: int,
    entry_count: int
) -> bool:
    """
    Check if signals pass robustness guardrails.
    
    Requires EITHER:
    - At least MIN_DISTINCT_KEYWORDS distinct keywords, OR
    - At least MIN_SEPARATE_ENTRIES separate entries with signals
    
    This prevents false positives from:
    - Single entry with repeated generic terms
    - One-off mentions that don't indicate pattern
    """
    return distinct_keywords >= MIN_DISTINCT_KEYWORDS or entry_count >= MIN_SEPARATE_ENTRIES


def calculate_pattern_drift(
    user_id: str,
    baseline_type: int,
    reflections: List[Dict],
    journal_entries: List[Dict],
    window_days: int = 14,
    threshold: float = DETECTION_THRESHOLD
) -> Dict[str, Any]:
    """
    Main drift calculation function.
    
    Returns structured JSON for the interpretation layer.
    
    ROBUSTNESS GUARDRAILS:
    - Requires signals from at least 2 separate entries, OR
    - Requires at least 2 distinct matched keywords
    - Without meeting these, drift_detected = false
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
            "distinct_keywords": 0,
            "entry_count": 0,
            "window_days": window_days,
            "summary": None,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    stress_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["stress"]
    growth_candidate = ENNEAGRAM_DRIFT_MAP[baseline_type]["growth"]
    
    # Calculate scores with robustness tracking
    scores, all_keywords, sources_used, entry_counts = calculate_type_scores(
        reflections, journal_entries, baseline_type
    )
    
    stress_score = scores.get(stress_candidate, 0)
    growth_score = scores.get(growth_candidate, 0)
    
    logger.info(f"[PatternDrift] Scores - Stress ({stress_candidate}): {stress_score:.2f}, Growth ({growth_candidate}): {growth_score:.2f}")
    
    # Determine winning direction
    drift_detected = False
    drift_candidate = None
    direction = None
    winning_score = 0.0
    winning_keywords = []
    winning_entry_count = 0
    summary = None
    
    # Determine which direction has stronger signal
    if stress_score >= growth_score and stress_score > 0:
        direction = "stress"
        drift_candidate = stress_candidate
        winning_score = stress_score
        winning_keywords = all_keywords.get(stress_candidate, [])
        winning_entry_count = entry_counts.get(stress_candidate, 0)
    elif growth_score > 0:
        direction = "growth"
        drift_candidate = growth_candidate
        winning_score = growth_score
        winning_keywords = all_keywords.get(growth_candidate, [])
        winning_entry_count = entry_counts.get(growth_candidate, 0)
    
    # Calculate confidence
    confidence_label, confidence_score = determine_confidence(winning_score, threshold)
    
    # Apply robustness guardrails
    distinct_keyword_count = len(winning_keywords)
    passes_guardrails = passes_robustness_check(distinct_keyword_count, winning_entry_count)
    
    logger.info(f"[PatternDrift] Robustness check: {distinct_keyword_count} distinct keywords, {winning_entry_count} entries, passes={passes_guardrails}")
    
    # Only mark as detected if score meets threshold AND passes guardrails
    if winning_score >= threshold and passes_guardrails:
        drift_detected = True
        summary = DRIFT_SUMMARY_TEMPLATES.get(direction, {}).get(baseline_type)
    elif winning_score > 0 and passes_guardrails:
        # Below threshold but has valid signals - still show as emerging
        summary = DRIFT_SUMMARY_TEMPLATES.get(direction, {}).get(baseline_type)
    else:
        # Failed guardrails - don't show drift
        direction = None
        drift_candidate = None
        winning_keywords = []
        summary = None
        confidence_label = "low"
        confidence_score = 0.0
    
    # Calculate total raw signals (for logging/debugging)
    total_signals = int(stress_score + growth_score)
    
    result = {
        "baseline_type": baseline_type,
        "baseline_name": TYPE_NAMES.get(baseline_type, f"Type {baseline_type}"),
        "drift_detected": drift_detected,
        "drift_candidate": drift_candidate,
        "drift_candidate_name": TYPE_NAMES.get(drift_candidate) if drift_candidate else None,
        "direction": direction,
        "confidence_label": confidence_label,
        "confidence_score": confidence_score,
        "signal_keywords": winning_keywords[:5],  # Top 5 keywords only
        "signal_sources": sources_used,
        "signals_detected": total_signals,
        "distinct_keywords": distinct_keyword_count,
        "entry_count": winning_entry_count,
        "window_days": window_days,
        "summary": summary,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        # Debug info (can be removed in production)
        "_debug": {
            "stress_candidate": stress_candidate,
            "growth_candidate": growth_candidate,
            "stress_score": round(stress_score, 2),
            "growth_score": round(growth_score, 2),
            "threshold": threshold,
            "passes_guardrails": passes_guardrails
        }
    }
    
    logger.info(f"[PatternDrift] Result: direction={direction}, candidate={drift_candidate}, confidence={confidence_label}, detected={drift_detected}")
    
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
