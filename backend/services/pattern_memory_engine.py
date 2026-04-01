"""Pattern Memory Engine V4.1 - Pattern Evolution Engine

Makes Mirror feel continuous AND tracks how patterns evolve over time.
User should feel: "I'm not just seeing my pattern... I'm seeing whether I'm changing."

V4:
- Detects repetition (NEW, RETURNING, RECURRING)

V4.1:
- Detects evolution of the pattern
- Is this pattern getting stronger? Loosening?
- Is the user seeing it earlier? Stuck in the same loop?
- Is the user starting to respond differently?

CORE:
1. Generate pattern_signature for each diagnosis
2. Store rolling history with evolution scores
3. Detect repetition AND evolution trajectory
4. Inject evolution-aware language into diagnosis

NOT analytics - psychological trajectory awareness.
The win: "I'm not just seeing my pattern... I'm seeing whether I'm actually changing."
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import re

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERN MEMORY CLASSIFICATION (V4)
# =============================================================================

class PatternMemoryState:
    NEW_PATTERN = "new_pattern"
    RETURNING_PATTERN = "returning_pattern"  # Seen in last 7-14 days
    RECURRING_PATTERN = "recurring_pattern"  # Seen multiple times over longer window


# =============================================================================
# PATTERN EVOLUTION CLASSIFICATION (V4.1)
# =============================================================================

class PatternEvolutionState:
    """V4.1: How the pattern is changing over time."""
    NONE = "none"                      # No evolution detected (new or insufficient data)
    ESCALATING = "escalating"          # urgency ↑, intensity ↑, repeating quickly
    SOFTENING = "softening"            # urgency ↓, intensity ↓
    LOOPING = "looping"                # high misstep similarity, low better_move alignment
    EARLY_AWARENESS = "early_awareness"  # detection latency decreasing
    INTEGRATING = "integrating"        # better_move alignment ↑, misstep decreasing


# =============================================================================
# MEMORY LANGUAGE - Recognition phrases, not tracking
# =============================================================================

RETURNING_PHRASES = [
    "You've been here recently.",
    "This isn't the first time this has come up.",
    "You were here a few days ago.",
    "This showed up before—and it's back.",
]

RECURRING_PHRASES = [
    "You keep coming back to this.",
    "This pattern doesn't resolve because something in it hasn't changed yet.",
    "You've circled back to this more than once.",
    "This keeps surfacing. That's not random.",
    "You've been here before. More than once.",
]

CROSS_LENS_PHRASES = [
    "This is showing up in more than one place right now.",
    "Multiple parts of your chart are pointing at the same thing.",
    "This isn't just one signal—it's echoing across your system.",
]


# =============================================================================
# V4.1: EVOLUTION LANGUAGE MAPPING - Trajectory awareness, not metrics
# =============================================================================
# CRITICAL: Never show scores. Only surface language when confidence > threshold.
# Pick ONE strongest signal - no stacking.

EVOLUTION_LANGUAGE = {
    PatternEvolutionState.ESCALATING: [
        "This isn't just back — it's getting stronger.",
        "The intensity is building. This is louder than before.",
        "It's not just returning — it's escalating.",
    ],
    PatternEvolutionState.SOFTENING: [
        "This is still here — but it's not gripping you the same way.",
        "The pattern is present, but softer than before.",
        "Something has loosened. The same shape, but less charge.",
    ],
    PatternEvolutionState.LOOPING: [
        "You've seen this pattern — but the way it plays out hasn't changed yet.",
        "Same pattern, same response. The loop is still running.",
        "You recognize this — but you're still caught in the same move.",
    ],
    PatternEvolutionState.EARLY_AWARENESS: [
        "You're noticing this earlier than before.",
        "You're catching it faster now. That's different.",
        "The pattern is here — but you saw it coming this time.",
    ],
    PatternEvolutionState.INTEGRATING: [
        "The same pattern is here — but you're not fully inside it anymore.",
        "You're responding differently. Something has shifted.",
        "This used to take over. Now you're holding it differently.",
    ],
}

# Cross-lens convergence language (V4.1)
CROSS_LENS_CONVERGENCE_PHRASES = [
    "This isn't coming from just one place — it's showing up across multiple layers right now.",
    "Both your design and the sky are pointing at the same thing today.",
    "This is echoing across systems. Pay attention.",
]

# Evolution confidence threshold (only inject if above this)
EVOLUTION_CONFIDENCE_THRESHOLD = 0.55


# =============================================================================
# V4.1: EVOLUTION SCORE COMPUTATION
# =============================================================================

def compute_evolution_scores(
    signal_flags: Dict[str, bool],
    journal_keywords: List[str] = None,
    misstep_text: str = "",
    better_move_text: str = "",
    user_interactions: List[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Compute evolution scores from available signals.
    
    Returns:
        {
            "urgency_score": 0.0-1.0,
            "emotional_intensity_score": 0.0-1.0,
            "clarity_score": 0.0-1.0,
            "misstep_similarity_score": 0.0-1.0 (vs prior),
            "better_move_alignment_score": 0.0-1.0,
            "detection_latency": float (hours since pattern emerged)
        }
    """
    if journal_keywords is None:
        journal_keywords = []
    if user_interactions is None:
        user_interactions = []
    
    scores = {
        "urgency_score": 0.5,
        "emotional_intensity_score": 0.5,
        "clarity_score": 0.5,
        "misstep_similarity_score": 0.0,
        "better_move_alignment_score": 0.0,
        "detection_latency": 24.0,  # Default to 24 hours
    }
    
    # Urgency score from signal flags
    urgency_signals = ["high_urgency", "action_taken", "frustration", "seeking_validation"]
    urgency_count = sum(1 for s in urgency_signals if signal_flags.get(s, False))
    scores["urgency_score"] = min(1.0, 0.3 + (urgency_count * 0.2))
    
    # Emotional intensity from signal flags
    intensity_signals = ["emotional_intensity", "frustration", "doubt", "low_clarity"]
    intensity_count = sum(1 for s in intensity_signals if signal_flags.get(s, False))
    scores["emotional_intensity_score"] = min(1.0, 0.3 + (intensity_count * 0.2))
    
    # Clarity score (inverse of low_clarity signals)
    clarity_signals = ["low_clarity", "doubt", "seeking_validation"]
    clarity_count = sum(1 for s in clarity_signals if signal_flags.get(s, False))
    scores["clarity_score"] = max(0.0, 1.0 - (clarity_count * 0.25))
    
    # Journal keyword analysis for intensity
    intense_keywords = ["overwhelm", "can't", "need to", "have to", "stuck", "trapped", "desperate"]
    soft_keywords = ["noticing", "aware", "seeing", "curious", "wondering", "maybe"]
    
    journal_text = " ".join(journal_keywords).lower()
    intense_matches = sum(1 for kw in intense_keywords if kw in journal_text)
    soft_matches = sum(1 for kw in soft_keywords if kw in journal_text)
    
    if intense_matches > soft_matches:
        scores["emotional_intensity_score"] = min(1.0, scores["emotional_intensity_score"] + 0.15)
    elif soft_matches > intense_matches:
        scores["emotional_intensity_score"] = max(0.0, scores["emotional_intensity_score"] - 0.15)
    
    # Detection latency from user interactions
    if user_interactions:
        # Check for recent reflection button clicks or journal entries
        recent_interactions = [i for i in user_interactions if i.get("type") in ["reflect", "journal", "open"]]
        if recent_interactions:
            # Earlier interaction = lower latency = earlier awareness
            scores["detection_latency"] = max(1.0, 24.0 - (len(recent_interactions) * 4))
    
    return scores


def compute_misstep_similarity(
    current_misstep: str,
    prior_missteps: List[str]
) -> float:
    """
    Compute how similar the current misstep is to prior occurrences.
    High similarity = still making same mistake = LOOPING
    """
    if not current_misstep or not prior_missteps:
        return 0.0
    
    current_words = set(current_misstep.lower().split())
    
    similarity_scores = []
    for prior in prior_missteps[-5:]:  # Last 5 missteps
        prior_words = set(prior.lower().split())
        if not prior_words:
            continue
        intersection = len(current_words & prior_words)
        union = len(current_words | prior_words)
        if union > 0:
            similarity_scores.append(intersection / union)
    
    if not similarity_scores:
        return 0.0
    
    return sum(similarity_scores) / len(similarity_scores)


def compute_better_move_alignment(
    better_move_text: str,
    recent_actions: List[str],
    journal_keywords: List[str]
) -> float:
    """
    Compute how aligned the user's recent behavior is with the recommended better_move.
    High alignment = INTEGRATING
    """
    if not better_move_text:
        return 0.0
    
    # Extract key action words from better_move
    action_indicators = {
        "wait": ["waited", "paused", "held back", "didn't rush"],
        "ask": ["asked", "questioned", "checked in"],
        "stop": ["stopped", "paused", "held", "didn't"],
        "notice": ["noticed", "saw", "recognized", "aware"],
        "let go": ["released", "let go", "surrendered", "accepted"],
        "trust": ["trusted", "believed", "followed"],
    }
    
    better_move_lower = better_move_text.lower()
    all_signals = " ".join(recent_actions + journal_keywords).lower()
    
    alignment_score = 0.0
    matches_found = 0
    
    for action, indicators in action_indicators.items():
        if action in better_move_lower:
            for indicator in indicators:
                if indicator in all_signals:
                    matches_found += 1
                    break
    
    # Normalize
    if matches_found >= 2:
        alignment_score = 0.8
    elif matches_found == 1:
        alignment_score = 0.5
    else:
        alignment_score = 0.2
    
    return alignment_score


# =============================================================================
# V4.1: EVOLUTION DETECTION ENGINE
# =============================================================================

def detect_pattern_evolution(
    current_scores: Dict[str, float],
    history_entries: List[Dict[str, Any]],
    current_signature: str,
    today_str: str
) -> Tuple[str, float, Dict[str, Any]]:
    """
    Detect the evolution trajectory of the current pattern.
    
    Compares current scores against last 3-5 similar entries.
    
    Returns:
        (evolution_state, confidence, evolution_details)
    """
    # Filter to similar patterns (same signature or same tension hash)
    similar_entries = [
        h for h in history_entries 
        if h.get("date") != today_str and h.get("evolution_scores")
    ][:5]  # Last 5 with scores
    
    if len(similar_entries) < 2:
        # Not enough history for evolution detection
        return PatternEvolutionState.NONE, 0.0, {"reason": "insufficient_history"}
    
    # Extract historical scores
    historical_urgency = [e.get("evolution_scores", {}).get("urgency_score", 0.5) for e in similar_entries]
    historical_intensity = [e.get("evolution_scores", {}).get("emotional_intensity_score", 0.5) for e in similar_entries]
    historical_misstep_sim = [e.get("evolution_scores", {}).get("misstep_similarity_score", 0.0) for e in similar_entries]
    historical_alignment = [e.get("evolution_scores", {}).get("better_move_alignment_score", 0.0) for e in similar_entries]
    historical_latency = [e.get("evolution_scores", {}).get("detection_latency", 24.0) for e in similar_entries]
    
    # Current scores
    curr_urgency = current_scores.get("urgency_score", 0.5)
    curr_intensity = current_scores.get("emotional_intensity_score", 0.5)
    curr_misstep_sim = current_scores.get("misstep_similarity_score", 0.0)
    curr_alignment = current_scores.get("better_move_alignment_score", 0.0)
    curr_latency = current_scores.get("detection_latency", 24.0)
    
    # Calculate averages
    avg_urgency = sum(historical_urgency) / len(historical_urgency) if historical_urgency else 0.5
    avg_intensity = sum(historical_intensity) / len(historical_intensity) if historical_intensity else 0.5
    avg_misstep_sim = sum(historical_misstep_sim) / len(historical_misstep_sim) if historical_misstep_sim else 0.0
    avg_alignment = sum(historical_alignment) / len(historical_alignment) if historical_alignment else 0.0
    avg_latency = sum(historical_latency) / len(historical_latency) if historical_latency else 24.0
    
    # Evolution detection logic
    evolution_signals = {}
    
    # ESCALATING: urgency ↑, intensity ↑, repeating quickly
    urgency_delta = curr_urgency - avg_urgency
    intensity_delta = curr_intensity - avg_intensity
    if urgency_delta > 0.15 and intensity_delta > 0.1:
        evolution_signals["escalating"] = 0.6 + (urgency_delta + intensity_delta) / 2
    elif urgency_delta > 0.2 or intensity_delta > 0.2:
        evolution_signals["escalating"] = 0.5 + max(urgency_delta, intensity_delta) / 2
    
    # SOFTENING: urgency ↓, intensity ↓
    if urgency_delta < -0.15 and intensity_delta < -0.1:
        evolution_signals["softening"] = 0.6 + abs(urgency_delta + intensity_delta) / 2
    elif urgency_delta < -0.2 or intensity_delta < -0.2:
        evolution_signals["softening"] = 0.5 + abs(min(urgency_delta, intensity_delta)) / 2
    
    # LOOPING: high misstep similarity, low better_move alignment
    if curr_misstep_sim > 0.6 and curr_alignment < 0.4:
        evolution_signals["looping"] = 0.5 + (curr_misstep_sim - curr_alignment) / 2
    
    # EARLY_AWARENESS: detection latency decreasing
    latency_improvement = avg_latency - curr_latency
    if latency_improvement > 4:  # Noticing 4+ hours earlier
        evolution_signals["early_awareness"] = 0.5 + min(0.4, latency_improvement / 20)
    
    # INTEGRATING: better_move alignment increasing, misstep decreasing
    alignment_delta = curr_alignment - avg_alignment
    misstep_delta = avg_misstep_sim - curr_misstep_sim
    if alignment_delta > 0.15 or (alignment_delta > 0.1 and misstep_delta > 0.1):
        evolution_signals["integrating"] = 0.5 + (alignment_delta + max(0, misstep_delta)) / 2
    
    # Select strongest signal
    if not evolution_signals:
        return PatternEvolutionState.NONE, 0.0, {"reason": "no_clear_trajectory"}
    
    # Get highest confidence evolution
    best_evolution = max(evolution_signals.items(), key=lambda x: x[1])
    evolution_state_key = best_evolution[0]
    confidence = min(1.0, best_evolution[1])
    
    # Map to enum
    state_mapping = {
        "escalating": PatternEvolutionState.ESCALATING,
        "softening": PatternEvolutionState.SOFTENING,
        "looping": PatternEvolutionState.LOOPING,
        "early_awareness": PatternEvolutionState.EARLY_AWARENESS,
        "integrating": PatternEvolutionState.INTEGRATING,
    }
    
    evolution_state = state_mapping.get(evolution_state_key, PatternEvolutionState.NONE)
    
    details = {
        "evolution_signals": evolution_signals,
        "selected": evolution_state_key,
        "confidence": round(confidence, 3),
        "score_deltas": {
            "urgency": round(urgency_delta, 3),
            "intensity": round(intensity_delta, 3),
            "misstep_sim": round(curr_misstep_sim - avg_misstep_sim, 3),
            "alignment": round(alignment_delta, 3),
            "latency": round(latency_improvement, 1),
        },
        "history_count": len(similar_entries),
    }
    
    logger.info(f"[PatternEvolution] Detected: {evolution_state} (confidence={confidence:.2f})")
    
    return evolution_state, confidence, details


def get_evolution_language(
    evolution_state: str,
    confidence: float,
    user_id: str
) -> Optional[str]:
    """
    Get the evolution-aware language to inject.
    Returns None if confidence is below threshold.
    
    RULES:
    - Never show scores or metrics
    - Only surface when confidence > threshold
    - Pick ONE phrase (no stacking)
    """
    if evolution_state == PatternEvolutionState.NONE:
        return None
    
    if confidence < EVOLUTION_CONFIDENCE_THRESHOLD:
        return None
    
    phrases = EVOLUTION_LANGUAGE.get(evolution_state, [])
    if not phrases:
        return None
    
    # Deterministic selection based on user + date
    seed = f"{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}:evolution"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    phrase_idx = seed_hash % len(phrases)
    
    return phrases[phrase_idx]


# =============================================================================
# PATTERN SIGNATURE GENERATION
# =============================================================================

def generate_pattern_signature(
    primary_tension: str,
    lens_source: str,
    key_drivers: List[str],
    secondary_tension: Optional[str] = None
) -> str:
    """
    Generate a pattern signature for matching across days.
    
    Format: tension__source__driver1_driver2_...
    
    Example: "urgency_vs_readiness__human_design__gate35"
    """
    # Normalize tension
    tension_clean = primary_tension.lower().strip()
    tension_clean = re.sub(r'[^a-z0-9_]', '_', tension_clean)
    tension_clean = re.sub(r'_+', '_', tension_clean).strip('_')
    
    # Normalize lens source
    lens_clean = lens_source.lower().strip()
    lens_clean = re.sub(r'[^a-z0-9_]', '_', lens_clean)
    
    # Normalize drivers
    drivers_clean = []
    for driver in key_drivers[:3]:  # Max 3 drivers
        d = str(driver).lower().strip()
        d = re.sub(r'[^a-z0-9_]', '_', d)
        d = re.sub(r'_+', '_', d).strip('_')
        if d:
            drivers_clean.append(d)
    
    # Build signature
    parts = [tension_clean, lens_clean]
    if drivers_clean:
        parts.append('_'.join(drivers_clean))
    
    return '__'.join(parts)


def generate_tension_hash(primary_tension: str, secondary_tension: Optional[str] = None) -> str:
    """
    Generate a short hash for quick tension matching.
    Used for partial matches across lenses.
    """
    content = primary_tension.lower()
    if secondary_tension:
        content += f"|{secondary_tension.lower()}"
    
    return hashlib.md5(content.encode()).hexdigest()[:8]


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def store_pattern_memory(
    db,
    user_id: str,
    date_str: str,
    pattern_signature: str,
    tension_hash: str,
    diagnosis_title: str,
    primary_tension: str,
    lens_source: str,
    key_drivers: List[str],
    evolution_scores: Dict[str, float] = None,
    misstep_text: str = "",
    better_move_text: str = ""
):
    """Store a pattern in the user's memory history with V4.1 evolution scores."""
    try:
        data = {
            "user_id": user_id,
            "date": date_str,
            "pattern_signature": pattern_signature,
            "tension_hash": tension_hash,
            "diagnosis_title": diagnosis_title,
            "primary_tension": primary_tension,
            "lens_source": lens_source,
            "key_drivers": key_drivers,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            # V4.1: Evolution tracking
            "evolution_scores": evolution_scores or {},
            "misstep_text": misstep_text,
            "better_move_text": better_move_text,
        }
        
        await db.pattern_memory.update_one(
            {"user_id": user_id, "date": date_str, "lens_source": lens_source},
            {"$set": data},
            upsert=True
        )
        logger.info(f"[PatternMemory V4.1] Stored pattern for {user_id[:8]}: {pattern_signature[:30]}...")
    except Exception as e:
        logger.error(f"[PatternMemory] Store error: {e}")


async def get_pattern_history(
    db,
    user_id: str,
    days: int = 60
) -> List[Dict[str, Any]]:
    """Get user's pattern history for the last N days."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        
        history = await db.pattern_memory.find({
            "user_id": user_id,
            "date": {"$gte": cutoff_str}
        }).sort("date", -1).to_list(days)
        
        return history
    except Exception as e:
        logger.error(f"[PatternMemory] History fetch error: {e}")
        return []


# =============================================================================
# REPETITION DETECTION
# =============================================================================

def detect_pattern_repetition(
    current_signature: str,
    current_tension_hash: str,
    history: List[Dict[str, Any]],
    today_str: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Detect if the current pattern is repeating.
    
    Returns:
        (memory_state, memory_details)
    """
    # Filter out today's entry
    past_entries = [h for h in history if h.get("date") != today_str]
    
    if not past_entries:
        return PatternMemoryState.NEW_PATTERN, {"match_count": 0}
    
    # Track matches
    exact_matches = []
    partial_matches = []  # Same tension, different source
    
    for entry in past_entries:
        entry_signature = entry.get("pattern_signature", "")
        entry_tension_hash = entry.get("tension_hash", "")
        
        # Exact signature match
        if entry_signature == current_signature:
            exact_matches.append(entry)
        # Partial match (same tension across lenses)
        elif entry_tension_hash == current_tension_hash:
            partial_matches.append(entry)
    
    # Classify based on match patterns
    total_matches = len(exact_matches) + len(partial_matches)
    
    if total_matches == 0:
        return PatternMemoryState.NEW_PATTERN, {"match_count": 0}
    
    # Check recency of matches
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    recent_cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
    
    recent_matches = [m for m in (exact_matches + partial_matches) 
                      if m.get("date", "") >= recent_cutoff_str]
    
    # Determine classification
    if len(exact_matches) >= 2 or total_matches >= 3:
        # Multiple occurrences - RECURRING
        memory_state = PatternMemoryState.RECURRING_PATTERN
    elif recent_matches:
        # Seen recently - RETURNING
        memory_state = PatternMemoryState.RETURNING_PATTERN
    else:
        # Old match only - treat as new
        memory_state = PatternMemoryState.NEW_PATTERN
    
    # Build details
    most_recent_match = None
    if exact_matches:
        most_recent_match = exact_matches[0]
    elif partial_matches:
        most_recent_match = partial_matches[0]
    
    details = {
        "match_count": total_matches,
        "exact_matches": len(exact_matches),
        "partial_matches": len(partial_matches),
        "most_recent_date": most_recent_match.get("date") if most_recent_match else None,
        "most_recent_title": most_recent_match.get("diagnosis_title") if most_recent_match else None,
        "recent_match_count": len(recent_matches),
    }
    
    logger.info(f"[PatternMemory] Detection result: {memory_state} (exact={len(exact_matches)}, partial={len(partial_matches)})")
    
    return memory_state, details


def detect_cross_lens_memory(
    current_tension_hash: str,
    history: List[Dict[str, Any]],
    current_lens: str,
    today_str: str
) -> Tuple[bool, Optional[str]]:
    """
    Detect if the same tension is appearing across different lenses.
    
    Returns:
        (is_cross_lens, other_lens)
    """
    # Find matches with same tension but different lens
    past_entries = [h for h in history if h.get("date") != today_str]
    
    cross_lens_matches = [
        h for h in past_entries
        if h.get("tension_hash") == current_tension_hash
        and h.get("lens_source") != current_lens
    ]
    
    if cross_lens_matches:
        other_lens = cross_lens_matches[0].get("lens_source", "another lens")
        return True, other_lens
    
    return False, None


# =============================================================================
# MEMORY LANGUAGE INJECTION
# =============================================================================

def get_memory_prefix(
    memory_state: str,
    memory_details: Dict[str, Any],
    is_cross_lens: bool = False,
    user_id: str = ""
) -> Optional[str]:
    """
    Get the memory recognition phrase to inject into diagnosis.
    
    Returns None if no memory phrase should be added.
    """
    if memory_state == PatternMemoryState.NEW_PATTERN:
        return None
    
    # Generate deterministic but varied selection
    seed = f"{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    
    # Select phrase based on state
    if memory_state == PatternMemoryState.RECURRING_PATTERN:
        phrases = RECURRING_PHRASES
    else:
        phrases = RETURNING_PHRASES
    
    phrase_idx = seed_hash % len(phrases)
    prefix = phrases[phrase_idx]
    
    # Add cross-lens note if applicable
    if is_cross_lens and memory_state in [PatternMemoryState.RECURRING_PATTERN, PatternMemoryState.RETURNING_PATTERN]:
        cross_idx = seed_hash % len(CROSS_LENS_PHRASES)
        prefix += f" {CROSS_LENS_PHRASES[cross_idx]}"
    
    return prefix


def inject_memory_into_diagnosis(
    diagnosis: Dict[str, Any],
    memory_state: str,
    memory_details: Dict[str, Any],
    memory_prefix: Optional[str]
) -> Dict[str, Any]:
    """
    Inject memory language into the diagnosis.
    Modifies the diagnosis in place and returns it.
    """
    if not memory_prefix:
        # No memory to inject
        diagnosis["pattern_memory"] = {
            "state": memory_state,
            "is_new": True,
        }
        return diagnosis
    
    # Inject prefix into body
    original_body = diagnosis.get("body", "")
    if original_body:
        # Add memory line before the main body
        diagnosis["body"] = f"{memory_prefix}\n\n{original_body}"
    
    # Add memory metadata
    diagnosis["pattern_memory"] = {
        "state": memory_state,
        "is_new": False,
        "match_count": memory_details.get("match_count", 0),
        "most_recent_date": memory_details.get("most_recent_date"),
        "memory_prefix": memory_prefix,
    }
    
    return diagnosis


# =============================================================================
# MAIN MEMORY ENGINE INTERFACE (V4.1 - Evolution Aware)
# =============================================================================

async def process_pattern_memory(
    db,
    user_id: str,
    diagnosis: Dict[str, Any],
    primary_tension: str,
    lens_source: str,
    key_drivers: List[str],
    diagnosis_title: str,
    secondary_tension: Optional[str] = None,
    signal_flags: Dict[str, bool] = None,
    journal_keywords: List[str] = None,
    user_interactions: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    V4.1: Main entry point for Pattern Evolution Engine.
    
    1. Generates pattern signature
    2. Fetches history
    3. Detects repetition (V4)
    4. Computes evolution scores (V4.1)
    5. Detects evolution trajectory (V4.1)
    6. Injects memory + evolution language
    7. Stores current pattern with scores
    
    Returns modified diagnosis with memory + evolution data.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if signal_flags is None:
        signal_flags = {}
    if journal_keywords is None:
        journal_keywords = []
    if user_interactions is None:
        user_interactions = []
    
    # Generate signatures
    pattern_signature = generate_pattern_signature(
        primary_tension=primary_tension,
        lens_source=lens_source,
        key_drivers=key_drivers,
        secondary_tension=secondary_tension
    )
    
    tension_hash = generate_tension_hash(primary_tension, secondary_tension)
    
    # Get history
    history = await get_pattern_history(db, user_id, days=60)
    
    # V4: Detect repetition
    memory_state, memory_details = detect_pattern_repetition(
        current_signature=pattern_signature,
        current_tension_hash=tension_hash,
        history=history,
        today_str=today
    )
    
    # V4: Detect cross-lens memory
    is_cross_lens, other_lens = detect_cross_lens_memory(
        current_tension_hash=tension_hash,
        history=history,
        current_lens=lens_source,
        today_str=today
    )
    
    if is_cross_lens:
        memory_details["is_cross_lens"] = True
        memory_details["other_lens"] = other_lens
    
    # V4.1: Compute evolution scores
    misstep_text = diagnosis.get("misstep", "")
    better_move_text = diagnosis.get("better_move", "")
    
    # Get prior missteps for similarity computation
    prior_missteps = [
        h.get("misstep_text", "") for h in history 
        if h.get("misstep_text") and h.get("date") != today
    ][:5]
    
    evolution_scores = compute_evolution_scores(
        signal_flags=signal_flags,
        journal_keywords=journal_keywords,
        misstep_text=misstep_text,
        better_move_text=better_move_text,
        user_interactions=user_interactions
    )
    
    # Add misstep similarity
    evolution_scores["misstep_similarity_score"] = compute_misstep_similarity(
        misstep_text, prior_missteps
    )
    
    # Add better move alignment (using journal keywords as proxy for behavior)
    recent_actions = [kw for kw in journal_keywords if len(kw) > 3]
    evolution_scores["better_move_alignment_score"] = compute_better_move_alignment(
        better_move_text, recent_actions, journal_keywords
    )
    
    # V4.1: Detect evolution trajectory
    evolution_state, evolution_confidence, evolution_details = detect_pattern_evolution(
        current_scores=evolution_scores,
        history_entries=history,
        current_signature=pattern_signature,
        today_str=today
    )
    
    # Get evolution language (only if confidence > threshold)
    evolution_language = get_evolution_language(
        evolution_state=evolution_state,
        confidence=evolution_confidence,
        user_id=user_id
    )
    
    # Get memory prefix (V4)
    memory_prefix = get_memory_prefix(
        memory_state=memory_state,
        memory_details=memory_details,
        is_cross_lens=is_cross_lens,
        user_id=user_id
    )
    
    # V4.1: Determine final injection - evolution takes priority
    final_prefix = None
    prefix_source = "none"
    
    if evolution_language and evolution_confidence >= EVOLUTION_CONFIDENCE_THRESHOLD:
        # Evolution language takes priority
        final_prefix = evolution_language
        prefix_source = "evolution"
    elif memory_prefix:
        # Fall back to memory prefix
        final_prefix = memory_prefix
        prefix_source = "memory"
    
    # Inject into diagnosis
    diagnosis = inject_memory_into_diagnosis(
        diagnosis=diagnosis,
        memory_state=memory_state,
        memory_details=memory_details,
        memory_prefix=final_prefix
    )
    
    # V4.1: Add evolution data to pattern_memory
    diagnosis["pattern_memory"]["evolution_state"] = evolution_state
    diagnosis["pattern_memory"]["evolution_confidence"] = round(evolution_confidence, 3)
    diagnosis["pattern_memory"]["evolution_language"] = evolution_language
    diagnosis["pattern_memory"]["prefix_source"] = prefix_source
    
    # Store current pattern with V4.1 evolution scores
    await store_pattern_memory(
        db=db,
        user_id=user_id,
        date_str=today,
        pattern_signature=pattern_signature,
        tension_hash=tension_hash,
        diagnosis_title=diagnosis_title,
        primary_tension=primary_tension,
        lens_source=lens_source,
        key_drivers=key_drivers,
        evolution_scores=evolution_scores,
        misstep_text=misstep_text,
        better_move_text=better_move_text
    )
    
    # Add debug info
    diagnosis["debug"] = diagnosis.get("debug", {})
    diagnosis["debug"]["pattern_memory"] = {
        "signature": pattern_signature,
        "tension_hash": tension_hash,
        "memory_state": memory_state,
        "match_count": memory_details.get("match_count", 0),
        "is_cross_lens": is_cross_lens,
        "history_entries": len(history),
        # V4.1: Evolution debug
        "evolution_state": evolution_state,
        "evolution_confidence": round(evolution_confidence, 3),
        "evolution_details": evolution_details,
        "evolution_scores": {k: round(v, 3) for k, v in evolution_scores.items()},
        "prefix_source": prefix_source,
        "version": "v4.1",
    }
    
    logger.info(f"[PatternMemory V4.1] Processed for {user_id[:8]}: memory={memory_state}, evolution={evolution_state} (conf={evolution_confidence:.2f})")
    
    return diagnosis


# =============================================================================
# HOME OVERRIDE CHECK - For recurring patterns
# =============================================================================

async def should_override_home_with_memory(
    db,
    user_id: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if Home should be overridden with a recurring pattern.
    
    Returns:
        (should_override, recurring_pattern_info)
    """
    history = await get_pattern_history(db, user_id, days=30)
    
    if len(history) < 3:
        return False, None
    
    # Count signature occurrences
    signature_counts = {}
    for entry in history:
        sig = entry.get("pattern_signature", "")
        if sig:
            if sig not in signature_counts:
                signature_counts[sig] = []
            signature_counts[sig].append(entry)
    
    # Find recurring patterns (3+ occurrences)
    recurring_patterns = [
        (sig, entries) for sig, entries in signature_counts.items()
        if len(entries) >= 3
    ]
    
    if not recurring_patterns:
        return False, None
    
    # Get the most frequent recurring pattern
    most_frequent = max(recurring_patterns, key=lambda x: len(x[1]))
    sig, entries = most_frequent
    
    # Check if it appeared recently (last 7 days)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent_cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
    
    recent_entries = [e for e in entries if e.get("date", "") >= recent_cutoff_str]
    
    if not recent_entries:
        return False, None
    
    # This is a recurring pattern that showed up recently
    most_recent = entries[0]
    
    return True, {
        "pattern_signature": sig,
        "occurrence_count": len(entries),
        "primary_tension": most_recent.get("primary_tension"),
        "diagnosis_title": most_recent.get("diagnosis_title"),
        "lens_source": most_recent.get("lens_source"),
        "most_recent_date": most_recent.get("date"),
    }


# =============================================================================
# HOME MEMORY OVERRIDE - Special Home diagnosis for recurring patterns
# =============================================================================

def generate_home_memory_override(recurring_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a special Home diagnosis that acknowledges recurring pattern.
    """
    tension = recurring_info.get("primary_tension", "this tension")
    occurrences = recurring_info.get("occurrence_count", 3)
    
    # Build recognition-focused diagnosis
    title = "You're Back Here Again"
    
    body = f"This isn't new. You've been circling this pattern—{tension.lower()}—and it keeps coming back because something hasn't shifted yet. "
    body += "That's not failure. That's the pattern asking to be seen more clearly."
    
    bridge = "The repetition isn't random. What you haven't resolved keeps returning until you do."
    
    misstep = "ignoring it because it feels familiar"
    
    better_move = "Instead of pushing past it, ask: what about this am I not yet willing to see?"
    
    return {
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": better_move,
        "pattern_memory": {
            "state": PatternMemoryState.RECURRING_PATTERN,
            "is_override": True,
            "occurrence_count": occurrences,
            "primary_tension": tension,
        },
        "debug": {
            "source": "home_memory_override",
            "recurring_info": recurring_info,
        }
    }


# =============================================================================
# V4.1: HOME PRIORITY LOGIC - Evolution signals take precedence
# =============================================================================
# Priority: ESCALATING > LOOPING > RECURRING > RETURNING > NEW

EVOLUTION_PRIORITY = {
    PatternEvolutionState.ESCALATING: 100,
    PatternEvolutionState.LOOPING: 90,
    PatternEvolutionState.INTEGRATING: 80,  # Good signal, worth noting
    PatternEvolutionState.EARLY_AWARENESS: 70,  # Good signal, worth noting
    PatternEvolutionState.SOFTENING: 60,  # Positive change
    PatternEvolutionState.NONE: 0,
}

MEMORY_PRIORITY = {
    PatternMemoryState.RECURRING_PATTERN: 50,
    PatternMemoryState.RETURNING_PATTERN: 30,
    PatternMemoryState.NEW_PATTERN: 10,
}


async def get_home_override_with_evolution(
    db,
    user_id: str,
    signal_flags: Dict[str, bool] = None,
    journal_keywords: List[str] = None
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    V4.1: Determine Home override with evolution priority.
    
    Priority order:
    1. ESCALATING
    2. LOOPING
    3. RECURRING
    4. RETURNING
    5. NEW
    
    Returns:
        (should_override, override_info, override_reason)
    """
    if signal_flags is None:
        signal_flags = {}
    if journal_keywords is None:
        journal_keywords = []
    
    history = await get_pattern_history(db, user_id, days=30)
    
    if len(history) < 2:
        return False, None, "insufficient_history"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Analyze patterns with evolution scores
    patterns_with_evolution = []
    
    # Group by signature
    signature_groups = {}
    for entry in history:
        sig = entry.get("pattern_signature", "")
        if sig:
            if sig not in signature_groups:
                signature_groups[sig] = []
            signature_groups[sig].append(entry)
    
    # For each pattern group, compute evolution
    for sig, entries in signature_groups.items():
        if len(entries) < 2:
            continue
        
        most_recent = entries[0]
        
        # Get evolution scores from most recent
        evolution_scores = most_recent.get("evolution_scores", {})
        
        # If no stored scores, compute from current signals
        if not evolution_scores:
            evolution_scores = compute_evolution_scores(
                signal_flags=signal_flags,
                journal_keywords=journal_keywords,
            )
        
        # Detect evolution against this group
        evolution_state, evolution_confidence, evolution_details = detect_pattern_evolution(
            current_scores=evolution_scores,
            history_entries=entries,
            current_signature=sig,
            today_str=today
        )
        
        # Determine memory state
        if len(entries) >= 3:
            memory_state = PatternMemoryState.RECURRING_PATTERN
        else:
            # Check recency
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            recent_cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
            if any(e.get("date", "") >= recent_cutoff_str for e in entries):
                memory_state = PatternMemoryState.RETURNING_PATTERN
            else:
                memory_state = PatternMemoryState.NEW_PATTERN
        
        # Calculate combined priority
        evolution_priority = EVOLUTION_PRIORITY.get(evolution_state, 0)
        if evolution_confidence < EVOLUTION_CONFIDENCE_THRESHOLD:
            evolution_priority = 0  # Don't prioritize uncertain evolution
        
        memory_priority = MEMORY_PRIORITY.get(memory_state, 0)
        
        combined_priority = evolution_priority + memory_priority
        
        patterns_with_evolution.append({
            "signature": sig,
            "entries": entries,
            "most_recent": most_recent,
            "evolution_state": evolution_state,
            "evolution_confidence": evolution_confidence,
            "memory_state": memory_state,
            "combined_priority": combined_priority,
            "evolution_details": evolution_details,
        })
    
    if not patterns_with_evolution:
        return False, None, "no_patterns"
    
    # Sort by combined priority
    patterns_with_evolution.sort(key=lambda x: x["combined_priority"], reverse=True)
    
    # Get highest priority pattern
    top_pattern = patterns_with_evolution[0]
    
    # Only override if significant
    if top_pattern["combined_priority"] < 40:  # At least RETURNING level
        return False, None, "priority_too_low"
    
    # Check if appeared recently (last 7 days)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent_cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
    
    recent_entries = [e for e in top_pattern["entries"] if e.get("date", "") >= recent_cutoff_str]
    
    if not recent_entries:
        return False, None, "not_recent"
    
    override_info = {
        "pattern_signature": top_pattern["signature"],
        "occurrence_count": len(top_pattern["entries"]),
        "primary_tension": top_pattern["most_recent"].get("primary_tension"),
        "diagnosis_title": top_pattern["most_recent"].get("diagnosis_title"),
        "lens_source": top_pattern["most_recent"].get("lens_source"),
        "most_recent_date": top_pattern["most_recent"].get("date"),
        # V4.1: Evolution data
        "evolution_state": top_pattern["evolution_state"],
        "evolution_confidence": top_pattern["evolution_confidence"],
        "memory_state": top_pattern["memory_state"],
        "combined_priority": top_pattern["combined_priority"],
    }
    
    override_reason = f"{top_pattern['evolution_state']}_{top_pattern['memory_state']}"
    
    logger.info(f"[Home V4.1] Override: evolution={top_pattern['evolution_state']}, memory={top_pattern['memory_state']}, priority={top_pattern['combined_priority']}")
    
    return True, override_info, override_reason


def generate_home_evolution_override(override_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    V4.1: Generate Home diagnosis based on evolution state.
    """
    tension = override_info.get("primary_tension", "this tension")
    evolution_state = override_info.get("evolution_state", PatternEvolutionState.NONE)
    memory_state = override_info.get("memory_state", PatternMemoryState.NEW_PATTERN)
    occurrences = override_info.get("occurrence_count", 2)
    
    # Select title and body based on evolution state
    if evolution_state == PatternEvolutionState.ESCALATING:
        title = "This Is Getting Stronger"
        body = f"The pattern around {tension.lower()} isn't just back—it's intensifying. "
        body += "Something about it hasn't been addressed, and now it's demanding more attention."
        bridge = "Escalation is the pattern's way of saying: you can't wait this one out."
        misstep = "hoping it will settle on its own"
        better_move = "Name what's escalating. Not the situation—the internal pressure."
        
    elif evolution_state == PatternEvolutionState.LOOPING:
        title = "The Same Loop Is Running"
        body = f"You recognize this—{tension.lower()}—and you know how it usually plays out. "
        body += "But knowing the pattern hasn't changed how you respond to it. That's the loop."
        bridge = "Awareness without different action just makes the loop more visible."
        misstep = "thinking that recognizing it is the same as changing it"
        better_move = "What's one small thing you could do differently this time?"
        
    elif evolution_state == PatternEvolutionState.INTEGRATING:
        title = "Something Is Shifting"
        body = f"The pattern around {tension.lower()} is still here—but you're meeting it differently. "
        body += "That's not nothing. That's the beginning of actual change."
        bridge = "Integration isn't dramatic. It's subtle. But it's real."
        misstep = "dismissing the progress because it feels small"
        better_move = "Notice what you did differently. That's worth remembering."
        
    elif evolution_state == PatternEvolutionState.EARLY_AWARENESS:
        title = "You're Catching It Earlier"
        body = f"You're noticing {tension.lower()} before it takes over. "
        body += "That space—between noticing and reacting—is new. Use it."
        bridge = "Early awareness is where choice lives."
        misstep = "waiting to see if it gets worse before responding"
        better_move = "Act now, while you have space to choose how."
        
    elif evolution_state == PatternEvolutionState.SOFTENING:
        title = "The Grip Is Loosening"
        body = f"The pattern around {tension.lower()} is still present—but something has softened. "
        body += "It doesn't have the same charge it did before."
        bridge = "Softening doesn't mean resolved. But it means less power over you."
        misstep = "pushing for complete resolution when partial is progress"
        better_move = "Let it be softer without needing it to be gone."
        
    else:
        # Fall back to recurring override
        return generate_home_memory_override(override_info)
    
    return {
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": better_move,
        "pattern_memory": {
            "state": memory_state,
            "evolution_state": evolution_state,
            "is_override": True,
            "occurrence_count": occurrences,
            "primary_tension": tension,
        },
        "debug": {
            "source": "home_evolution_override_v4.1",
            "override_info": override_info,
        }
    }


# =============================================================================
# V4.1: CROSS-LENS CONVERGENCE DETECTION
# =============================================================================

async def detect_cross_lens_convergence(
    db,
    user_id: str,
    current_tension_hash: str = None
) -> Tuple[bool, Optional[str]]:
    """
    V4.1: Detect if HD + Astro share same pattern within same session/day.
    
    Conditions:
    - Same tension_axis OR high similarity score
    - Within same day/session
    
    Returns:
        (is_convergent, convergence_language)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    try:
        # Get today's patterns from both lenses
        todays_patterns = await db.pattern_memory.find({
            "user_id": user_id,
            "date": today
        }).to_list(10)
        
        if len(todays_patterns) < 2:
            return False, None
        
        # Check for different lens sources with same tension
        lens_sources = set()
        tension_hashes = {}
        
        for pattern in todays_patterns:
            lens = pattern.get("lens_source", "")
            t_hash = pattern.get("tension_hash", "")
            
            if lens and t_hash:
                lens_sources.add(lens)
                if t_hash not in tension_hashes:
                    tension_hashes[t_hash] = []
                tension_hashes[t_hash].append(lens)
        
        # Check if we have multiple lenses pointing at same tension
        for t_hash, lenses in tension_hashes.items():
            unique_lenses = set(lenses)
            if len(unique_lenses) >= 2:
                # Cross-lens convergence detected
                # Deterministic phrase selection
                seed = f"{user_id}:{today}:convergence"
                seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
                phrase_idx = seed_hash % len(CROSS_LENS_CONVERGENCE_PHRASES)
                
                logger.info(f"[PatternMemory V4.1] Cross-lens convergence: {unique_lenses} on tension {t_hash[:8]}")
                
                return True, CROSS_LENS_CONVERGENCE_PHRASES[phrase_idx]
        
        # Also check if current tension hash matches other lenses
        if current_tension_hash:
            for pattern in todays_patterns:
                if pattern.get("tension_hash") == current_tension_hash:
                    if pattern.get("lens_source") not in ["home"]:  # Different lens
                        seed = f"{user_id}:{today}:convergence"
                        seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
                        phrase_idx = seed_hash % len(CROSS_LENS_CONVERGENCE_PHRASES)
                        
                        return True, CROSS_LENS_CONVERGENCE_PHRASES[phrase_idx]
        
        return False, None
        
    except Exception as e:
        logger.debug(f"[PatternMemory V4.1] Cross-lens detection error: {e}")
        return False, None
