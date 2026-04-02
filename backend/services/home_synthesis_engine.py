"""Home Synthesis Engine V5.0 - Decisive Pattern Synthesis

CORE RULE: Home answers ONLY:
→ "Out of everything happening — what matters most right now?"

DO NOT:
- explain transits
- mention astrology explicitly
- give long advice
- sound like a horoscope

OUTPUT STRUCTURE (4 blocks):
1. THE CALL (1 sentence — sharp, decisive)
2. THE REALITY (1–2 sentences — grounded, felt experience)
3. THE SOURCE HINT (1 sentence — subtle synthesis cue)
4. THE EDGE (1 sentence — tension / choice)
+ CTA: "See what's driving this today →"

V5.0 UPGRADES:
1. DOMINANCE SCORING - Select ONLY highest scoring pattern
2. BEHAVIORAL LANGUAGE ENFORCEMENT - Every line maps to real behavior
3. EXPRESSION ANGLE ROTATION - Prevent repetition with angle cycling
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import re

logger = logging.getLogger(__name__)


# =============================================================================
# DOMINANCE SCORING MODEL (CRITICAL)
# =============================================================================

def compute_pattern_dominance_score(
    pattern_key: str,
    memory_frequency: float,
    recency_score: float,
    transit_activation: float,
    journal_intensity: float,
    cross_lens_agreement: float
) -> float:
    """
    Compute dominance score for a candidate pattern.
    
    Weights:
    - memory_frequency_weight → how often this pattern has appeared (30%)
    - recency_weight → how recent - last 1-3 days gets higher weight (25%)
    - transit_activation_weight → whether current transits activate this (20%)
    - journal_signal_weight → emotional intensity from recent reflections (15%)
    - cross_lens_agreement_weight → how many lenses point to same tension (10%)
    
    Returns: 0.0 - 1.0 dominance score
    """
    score = (
        0.30 * memory_frequency +
        0.25 * recency_score +
        0.20 * transit_activation +
        0.15 * journal_intensity +
        0.10 * cross_lens_agreement
    )
    return min(1.0, max(0.0, score))


async def select_dominant_pattern(
    db,
    user_id: str,
    candidate_patterns: List[Dict[str, Any]],
    transit_data: Dict[str, Any] = None,
    journal_signals: List[str] = None,
    lens_tensions: Dict[str, str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Select ONLY the highest scoring pattern for Home.
    DO NOT blend multiple patterns into one message.
    
    Returns:
        (dominant_pattern, scoring_details)
    """
    if not candidate_patterns:
        return None, {"error": "no_candidates"}
    
    if transit_data is None:
        transit_data = {}
    if journal_signals is None:
        journal_signals = []
    if lens_tensions is None:
        lens_tensions = {}
    
    # Get pattern memory history
    from services.pattern_memory_engine import get_pattern_history
    history = await get_pattern_history(db, user_id, days=30)
    
    # Count pattern frequencies
    pattern_frequency = {}
    pattern_recency = {}
    
    for entry in history:
        sig = entry.get("primary_tension", "")
        if sig:
            pattern_frequency[sig] = pattern_frequency.get(sig, 0) + 1
            entry_date = entry.get("date", "")
            if entry_date and (sig not in pattern_recency or entry_date > pattern_recency[sig]):
                pattern_recency[sig] = entry_date
    
    # Score each candidate
    scored_patterns = []
    
    for pattern in candidate_patterns:
        pattern_key = pattern.get("pattern_key", "")
        
        # Memory frequency (0-1 normalized)
        freq = pattern_frequency.get(pattern_key, 0)
        max_freq = max(pattern_frequency.values()) if pattern_frequency else 1
        memory_frequency = min(1.0, freq / max(max_freq, 1))
        
        # Recency score (higher if appeared in last 3 days)
        recent_date = pattern_recency.get(pattern_key, "")
        recency_score = 0.0
        if recent_date:
            days_ago = (datetime.now(timezone.utc) - datetime.strptime(recent_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
            if days_ago <= 1:
                recency_score = 1.0
            elif days_ago <= 3:
                recency_score = 0.7
            elif days_ago <= 7:
                recency_score = 0.4
            else:
                recency_score = 0.2
        
        # Transit activation (check if pattern maps to current transits)
        transit_activation = 0.0
        transit_tensions = transit_data.get("dominant_tensions", [])
        if pattern_key.lower() in " ".join(transit_tensions).lower():
            transit_activation = 0.8
        elif transit_data.get("intensity", 0) > 0.7:
            transit_activation = 0.5
        
        # Journal intensity (check keyword overlap)
        journal_intensity = 0.0
        pattern_words = set(pattern_key.lower().replace("_", " ").split())
        journal_text = " ".join(journal_signals).lower()
        overlap = sum(1 for w in pattern_words if w in journal_text)
        if overlap > 0:
            journal_intensity = min(1.0, overlap * 0.3)
        
        # Cross-lens agreement (check if HD, Astro, etc point to same tension)
        cross_lens_agreement = 0.0
        matching_lenses = 0
        for lens, tension in lens_tensions.items():
            if pattern_key.lower() in tension.lower() or tension.lower() in pattern_key.lower():
                matching_lenses += 1
        if matching_lenses >= 2:
            cross_lens_agreement = 1.0
        elif matching_lenses == 1:
            cross_lens_agreement = 0.5
        
        # Compute total score
        dominance_score = compute_pattern_dominance_score(
            pattern_key=pattern_key,
            memory_frequency=memory_frequency,
            recency_score=recency_score,
            transit_activation=transit_activation,
            journal_intensity=journal_intensity,
            cross_lens_agreement=cross_lens_agreement
        )
        
        scored_patterns.append({
            **pattern,
            "dominance_score": dominance_score,
            "score_breakdown": {
                "memory_frequency": round(memory_frequency, 3),
                "recency": round(recency_score, 3),
                "transit_activation": round(transit_activation, 3),
                "journal_intensity": round(journal_intensity, 3),
                "cross_lens_agreement": round(cross_lens_agreement, 3),
            }
        })
    
    # Sort by dominance score and select highest
    scored_patterns.sort(key=lambda x: x["dominance_score"], reverse=True)
    
    dominant = scored_patterns[0]
    
    logger.info(f"[HomeSynthesis] Selected dominant pattern: {dominant.get('pattern_key')} (score={dominant['dominance_score']:.3f})")
    
    return dominant, {
        "candidates_evaluated": len(scored_patterns),
        "top_3": [{"key": p.get("pattern_key"), "score": p["dominance_score"]} for p in scored_patterns[:3]],
    }


# =============================================================================
# BEHAVIORAL LANGUAGE ENFORCEMENT (CRITICAL)
# =============================================================================

VAGUE_PHRASES = [
    "a pull toward",
    "energy shifting",
    "weight landing",
    "a door appearing",
    "something emerging",
    "cosmic forces",
    "universal energy",
    "vibration",
    "alignment",
    "the universe wants",
    "stars aligning",
    "flow state",
    "higher self",
    "inner calling",
]

BEHAVIORAL_REPLACEMENTS = {
    "a pull toward more": "you're trying to take on more than you can realistically hold right now",
    "energy shifting": "something is changing in how you're approaching this",
    "weight landing": "a decision is pressing on you",
    "a door appearing": "an opportunity is becoming visible, and you're deciding whether to take it",
    "something emerging": "a pattern is becoming clear that you couldn't see before",
    "cosmic forces": "multiple pressures are converging at once",
    "universal energy": "the timing of several things is colliding",
    "vibration": "the way you're responding to this situation",
    "alignment": "whether what you're doing matches what you actually want",
    "the universe wants": "the situation is pushing you toward",
    "stars aligning": "several conditions are lining up",
    "flow state": "when you stop resisting and start responding",
    "higher self": "the part of you that knows what's actually right",
    "inner calling": "what you keep coming back to even when you try to ignore it",
}


def enforce_behavioral_language(text: str) -> str:
    """
    Reject vague/poetic abstraction and convert to concrete behavioral statements.
    
    Every line must map to a REAL human behavior or decision moment.
    """
    result = text
    
    # Replace known vague phrases
    for vague, behavioral in BEHAVIORAL_REPLACEMENTS.items():
        if vague.lower() in result.lower():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(vague), re.IGNORECASE)
            result = pattern.sub(behavioral, result)
    
    # Check for remaining vague phrases and flag
    for phrase in VAGUE_PHRASES:
        if phrase.lower() in result.lower() and phrase.lower() not in [v.lower() for v in BEHAVIORAL_REPLACEMENTS.values()]:
            logger.warning(f"[BehavioralLanguage] Vague phrase detected: '{phrase}' - needs manual rewrite")
    
    return result


def validate_behavioral_content(text: str) -> Tuple[bool, List[str]]:
    """
    Validate that content is behavioral, not abstract.
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    for phrase in VAGUE_PHRASES:
        if phrase.lower() in text.lower():
            if phrase.lower() not in BEHAVIORAL_REPLACEMENTS:
                issues.append(f"Vague phrase: '{phrase}'")
    
    # Check for action verbs
    action_verbs = ["decide", "delay", "avoid", "push", "close", "say", "commit", "withdraw", 
                   "wait", "move", "stop", "start", "choose", "refuse", "accept", "try", 
                   "force", "hold", "release", "take", "leave", "stay"]
    
    has_action_verb = any(verb in text.lower() for verb in action_verbs)
    
    if not has_action_verb and len(text) > 50:
        issues.append("Missing action verbs - may be too abstract")
    
    return len(issues) == 0, issues


# =============================================================================
# EXPRESSION ANGLE ROTATION (ANTI-REPETITION)
# =============================================================================

EXPRESSION_ANGLES = {
    "timing": {
        "call_template": "You're trying to move something forward that isn't ready yet",
        "reality_template": "The timing feels off—and part of you knows it",
        "edge_template": "The question is whether you wait for clarity or push through uncertainty",
        "keywords": ["too early", "not yet", "before ready", "timing off"],
    },
    "control": {
        "call_template": "You're trying to force an outcome that wants to unfold on its own",
        "reality_template": "The grip is tightening—and it's not helping",
        "edge_template": "The question is whether you hold tighter or let it breathe",
        "keywords": ["force", "control", "grip", "make it happen"],
    },
    "clarity": {
        "call_template": "You're closing a decision before you can see it clearly",
        "reality_template": "Something feels unfinished—because it is",
        "edge_template": "The question is whether you commit now or stay open longer",
        "keywords": ["unclear", "can't see", "fog", "closing too fast"],
    },
    "readiness": {
        "call_template": "You're acting before you've fully formed what you're doing",
        "reality_template": "The action is outpacing the intention",
        "edge_template": "The question is whether you slow down or trust the momentum",
        "keywords": ["not ready", "unformed", "half-baked", "premature"],
    },
    "resistance": {
        "call_template": "You're avoiding something that's asking to be faced",
        "reality_template": "The avoidance is louder than the thing itself now",
        "edge_template": "The question is whether you turn toward it or keep circling",
        "keywords": ["avoiding", "resisting", "circling", "not facing"],
    },
    "overcommitment": {
        "call_template": "You're taking on more than you can actually hold right now",
        "reality_template": "The load is heavier than it looks—and you're pretending it isn't",
        "edge_template": "The question is whether you drop something or keep carrying it all",
        "keywords": ["too much", "overloaded", "can't hold", "spreading thin"],
    },
}


async def get_next_expression_angle(
    db,
    user_id: str,
    pattern_key: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Get next expression angle for a repeated pattern.
    Rotates through angles to prevent semantic repetition.
    
    Returns:
        (angle_id, angle_data)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get recent angle history
    try:
        recent_angles = await db.home_angle_history.find({
            "user_id": user_id,
            "pattern_key": pattern_key,
        }).sort("date", -1).limit(5).to_list(5)
    except Exception as e:
        logger.debug(f"[AngleRotation] Could not get history: {e}")
        recent_angles = []
    
    # Get used angles
    used_angles = [a.get("angle_id") for a in recent_angles]
    
    # Find unused angle
    available_angles = [a for a in EXPRESSION_ANGLES.keys() if a not in used_angles]
    
    if not available_angles:
        # All angles used, start over with least recently used
        available_angles = list(EXPRESSION_ANGLES.keys())
    
    # Select next angle (deterministic based on user + date)
    seed = f"{user_id}:{today}:{pattern_key}"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    angle_id = available_angles[seed_hash % len(available_angles)]
    
    # Store angle usage
    try:
        await db.home_angle_history.update_one(
            {"user_id": user_id, "date": today, "pattern_key": pattern_key},
            {"$set": {
                "user_id": user_id,
                "date": today,
                "pattern_key": pattern_key,
                "angle_id": angle_id,
                "stored_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True
        )
    except Exception as e:
        logger.debug(f"[AngleRotation] Could not store history: {e}")
    
    logger.info(f"[AngleRotation] Pattern '{pattern_key}' using angle '{angle_id}'")
    
    return angle_id, EXPRESSION_ANGLES[angle_id]


# =============================================================================
# PATTERN STATE LANGUAGE (RETURNING / RECURRING)
# =============================================================================

RETURNING_PHRASES = [
    "You felt this recently — and it's still here.",
    "This showed up a few days ago. It hasn't left.",
    "This is familiar territory. You were just here.",
]

RECURRING_PHRASES = [
    "You're back here again — this isn't passing.",
    "This keeps coming up. That's not coincidence.",
    "You've circled this before. Multiple times now.",
    "This pattern isn't new. It's been asking for attention.",
]


def get_pattern_state_language(
    pattern_state: str,
    evolution_state: str,
    user_id: str
) -> Optional[str]:
    """
    Get pattern state acknowledgment language.
    
    Injects continuity phrases based on pattern state:
    - RETURNING: subtle continuity
    - RECURRING (3+): stronger acknowledgment
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed = f"{user_id}:{today}:state"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    
    if pattern_state == "recurring_pattern":
        return RECURRING_PHRASES[seed_hash % len(RECURRING_PHRASES)]
    elif pattern_state == "returning_pattern":
        return RETURNING_PHRASES[seed_hash % len(RETURNING_PHRASES)]
    
    return None


# =============================================================================
# SOURCE HINT PHRASES
# =============================================================================

SOURCE_HINT_PHRASES = [
    "This is showing up across multiple areas right now.",
    "This isn't random — something deeper is driving it today.",
    "Multiple signals are pointing at the same thing.",
    "This is coming from more than one direction.",
    "Several parts of your system are flagging the same tension.",
]


def get_source_hint(
    cross_lens_agreement: float,
    evolution_state: str,
    user_id: str
) -> str:
    """Get source hint phrase."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed = f"{user_id}:{today}:source"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    
    # Stronger language if cross-lens agreement is high
    if cross_lens_agreement > 0.5:
        strong_hints = [
            "This is showing up across multiple areas right now.",
            "Multiple signals are pointing at the same thing.",
            "Several parts of your system are flagging the same tension.",
        ]
        return strong_hints[seed_hash % len(strong_hints)]
    
    return SOURCE_HINT_PHRASES[seed_hash % len(SOURCE_HINT_PHRASES)]


# =============================================================================
# MAIN SYNTHESIS GENERATOR
# =============================================================================

async def generate_home_synthesis(
    db,
    user_id: str,
    pattern_data: Dict[str, Any],
    transit_data: Dict[str, Any] = None,
    pattern_memory_state: str = "new_pattern",
    evolution_state: str = "none",
    cross_lens_agreement: float = 0.0
) -> Dict[str, Any]:
    """
    Generate the 4-block Home synthesis.
    
    Structure:
    1. THE CALL (1 sentence — sharp, decisive)
    2. THE REALITY (1–2 sentences — grounded, felt experience)
    3. THE SOURCE HINT (1 sentence — subtle synthesis cue)
    4. THE EDGE (1 sentence — tension / choice)
    + CTA
    """
    from services.pattern_sanitizer import (
        sanitize_pattern_key, 
        sanitize_text_content,
        ensure_clean_copy,
    )
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pattern_key = pattern_data.get("pattern_key", "general_tension")
    
    # Get expression angle for anti-repetition
    angle_id, angle_data = await get_next_expression_angle(db, user_id, pattern_key)
    
    # Generate THE CALL
    the_call = angle_data["call_template"]
    
    # Personalize call based on pattern data
    if pattern_data.get("title"):
        # Use pattern title as base
        the_call = pattern_data["title"]
        # Ensure it's behavioral
        the_call = enforce_behavioral_language(the_call)
    
    # SANITIZE: Remove any internal pattern keys from the_call
    the_call = sanitize_text_content(the_call)
    the_call = ensure_clean_copy(the_call, angle_data["call_template"])
    
    # Generate THE REALITY
    the_reality = angle_data["reality_template"]
    
    # Add pattern-specific reality
    if pattern_data.get("body"):
        # Extract first sentence as reality
        body_sentences = pattern_data["body"].split(". ")
        if body_sentences:
            the_reality = enforce_behavioral_language(body_sentences[0])
            if len(body_sentences) > 1 and len(body_sentences[1]) > 20:
                the_reality += f" {body_sentences[1]}"
    
    # SANITIZE: Remove any internal pattern keys from the_reality
    the_reality = sanitize_text_content(the_reality)
    
    # Inject pattern state language if applicable
    state_language = get_pattern_state_language(pattern_memory_state, evolution_state, user_id)
    if state_language:
        the_reality = f"{state_language} {the_reality}"
    
    # Generate THE SOURCE HINT
    the_source_hint = get_source_hint(cross_lens_agreement, evolution_state, user_id)
    
    # Generate THE EDGE
    the_edge = angle_data["edge_template"]
    
    # Personalize edge based on pattern
    if pattern_data.get("bridge"):
        edge_candidate = enforce_behavioral_language(pattern_data["bridge"])
        # Only use if it's a question or choice
        if "?" in edge_candidate or "whether" in edge_candidate.lower():
            the_edge = edge_candidate
    
    # SANITIZE: Remove any internal pattern keys from the_edge
    the_edge = sanitize_text_content(the_edge)
    the_edge = ensure_clean_copy(the_edge, angle_data["edge_template"])
    
    # CTA
    cta_text = "See what's driving this today →"
    cta_target = "/astrology"  # Deep link to Astrology Today
    
    # Final validation: all content must be behavioral and clean
    all_content = f"{the_call} {the_reality} {the_source_hint} {the_edge}"
    is_valid, issues = validate_behavioral_content(all_content)
    
    if not is_valid:
        logger.warning(f"[HomeSynthesis] Behavioral validation issues: {issues}")
    
    # DO NOT expose pattern_key to frontend - keep it in debug only
    return {
        "success": True,
        "date": today,
        # V5.0 4-BLOCK STRUCTURE (CLEAN - no internal tokens)
        "the_call": the_call,
        "the_reality": the_reality,
        "the_source_hint": the_source_hint,
        "the_edge": the_edge,
        "cta_text": cta_text,
        "cta_target": cta_target,
        # Metadata (sanitized for display)
        "pattern_memory_state": pattern_memory_state,
        "evolution_state": evolution_state,
        "version": "v5.0_synthesis",
        # Debug only (NOT for user display)
        "debug": {
            "pattern_key": pattern_key,  # Internal only
            "angle_id": angle_id,
            "pattern_memory_state": pattern_memory_state,
            "evolution_state": evolution_state,
            "cross_lens_agreement": round(cross_lens_agreement, 3),
            "behavioral_valid": is_valid,
            "behavioral_issues": issues if not is_valid else [],
        }
    }
