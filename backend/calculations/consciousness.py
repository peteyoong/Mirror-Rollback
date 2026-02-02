"""
Consciousness Lens v1 - Capacity-oriented, non-hierarchical framework
No fatalism. No identity pronouncements. Always optional language.

Includes inference smoothing to prevent rapid state switching.
"""
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Load the master configuration
CONFIG_PATH = Path(__file__).parent.parent / "data" / "consciousness_lens_v1.json"

# Smoothing configuration
SMOOTHING_CONFIG = {
    "min_confirmations": 2,          # Require N consistent signals before changing state
    "history_window_minutes": 30,     # Look back window for inference history
    "max_history_entries": 5,         # Max recent inferences to consider
    "upward_threshold": 0.65,         # Higher confidence needed to move to deeper state
    "downward_threshold": 0.45,       # Lower threshold to move to shallower state (safety bias)
    "stability_bonus": 0.1,           # Bonus confidence for staying at current level
}

# Depth ordering (lower index = lower depth = safer default)
DEPTH_ORDER = {
    "survival": 0,
    "stabilizing": 1,
    "coping": 2,
    "exploring": 3,
    "integrating": 4,
    "expanding": 5
}


def load_consciousness_config() -> Dict:
    """Load the consciousness lens configuration from JSON file."""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def get_consciousness_levels() -> Dict:
    """Get the full consciousness lens configuration."""
    config = load_consciousness_config()
    return config.get("consciousness_lens_v1", {})


def get_level_by_id(level_id: str) -> Optional[Dict]:
    """Get a specific level by its ID."""
    config = get_consciousness_levels()
    levels = config.get("levels", [])
    for level in levels:
        if level.get("level_id") == level_id:
            return level
    return None


def get_default_snapshot() -> Dict:
    """Get the default consciousness snapshot (coping at 0.45 confidence)."""
    config = get_consciousness_levels()
    defaults = config.get("defaults", {})
    
    return {
        "inferred_level_id": defaults.get("fallback_level_id", "coping"),
        "confidence": defaults.get("fallback_confidence_threshold", 0.45),
        "signals": {
            "language_markers": [],
            "affect": "neutral",
            "constraints": []
        },
        "last_updated_iso": datetime.now(timezone.utc).isoformat(),
        "source_events": ["default_fallback"],
        "inference_history": []
    }


def get_adaptation_block(level_id: str, confidence: float = 0.5) -> Dict:
    """
    Generate consciousness adaptation block for the interpret layer.
    This shapes tone, depth, and constraints for LLM responses.
    """
    config = get_consciousness_levels()
    defaults = config.get("defaults", {})
    level = get_level_by_id(level_id)
    
    # If level not found or confidence too low, use fallback
    if not level or confidence < defaults.get("fallback_confidence_threshold", 0.45):
        level = get_level_by_id(defaults.get("fallback_level_id", "coping"))
    
    if not level:
        # Ultimate fallback
        return {
            "mode": "cope",
            "depth": "medium_low",
            "tone": ["grounded", "supportive"],
            "avoid": defaults.get("global_do_not", []),
            "word_budget_max": 220,
            "structure_template": []
        }
    
    # Map level_id to mode name
    mode_map = {
        "survival": "stabilize",
        "stabilizing": "stabilize", 
        "coping": "cope",
        "exploring": "reflect",
        "integrating": "integrate",
        "expanding": "expand"
    }
    
    return {
        "mode": mode_map.get(level_id, "cope"),
        "depth": level.get("depth", "medium_low"),
        "tone": level.get("tone", ["grounded"]),
        "avoid": defaults.get("global_do_not", []) + level.get("do_not", []),
        "word_budget_max": level.get("word_budget_max", 220),
        "structure_template": level.get("structure_template", []),
        "allowed_moves": level.get("allowed_moves", []),
        "ai_interpretation_hint": level.get("ai_interpretation_hint", ""),
        "exit_line": level.get("exit_line", ""),
        "prompt_templates": level.get("prompt_templates", {})
    }


def _raw_infer_from_text(text: str) -> Dict:
    """
    Raw inference from text using language markers.
    Returns raw detection without smoothing.
    """
    if not text:
        return {"level_id": "coping", "confidence": 0.45, "markers": []}
    
    config = get_consciousness_levels()
    levels = config.get("levels", [])
    
    text_lower = text.lower()
    
    # Score each level based on language markers
    level_scores = {}
    
    for level in levels:
        level_id = level.get("level_id")
        markers = level.get("language_markers", [])
        
        score = 0
        matched_markers = []
        
        for marker in markers:
            if marker.lower() in text_lower:
                score += 1
                matched_markers.append(marker)
        
        if score > 0:
            level_scores[level_id] = {
                "score": score,
                "markers": matched_markers,
                "depth_order": DEPTH_ORDER.get(level_id, 2)
            }
    
    if not level_scores:
        return {"level_id": "coping", "confidence": 0.45, "markers": []}
    
    # Find highest scoring level
    max_score = max(s["score"] for s in level_scores.values())
    
    # Get all levels with max score
    top_levels = [
        (lid, data) for lid, data in level_scores.items() 
        if data["score"] == max_score
    ]
    
    # If conflict (multiple top scorers), bias to lower depth
    if len(top_levels) > 1:
        top_levels.sort(key=lambda x: x[1]["depth_order"])
    
    chosen_level_id = top_levels[0][0]
    chosen_data = top_levels[0][1]
    
    # Calculate confidence based on score strength
    confidence = min(0.95, 0.3 + (chosen_data["score"] * 0.15))
    
    return {
        "level_id": chosen_level_id,
        "confidence": round(confidence, 2),
        "markers": chosen_data["markers"]
    }


def apply_smoothing(
    raw_inference: Dict,
    current_snapshot: Optional[Dict],
    inference_history: List[Dict]
) -> Dict:
    """
    Apply smoothing to prevent rapid state switching.
    
    Rules:
    1. Require confirmation across multiple signals before changing state
    2. Bias toward lower depth when signals conflict
    3. Apply stability bonus for staying at current level
    4. Moving up requires higher confidence than moving down
    """
    raw_level = raw_inference.get("level_id", "coping")
    raw_confidence = raw_inference.get("confidence", 0.45)
    raw_markers = raw_inference.get("markers", [])
    
    # Get current level (default to coping if none)
    current_level = "coping"
    if current_snapshot:
        current_level = current_snapshot.get("inferred_level_id", "coping")
    
    # If no change, apply stability bonus and return
    if raw_level == current_level:
        smoothed_confidence = min(0.95, raw_confidence + SMOOTHING_CONFIG["stability_bonus"])
        return {
            "level_id": raw_level,
            "confidence": round(smoothed_confidence, 2),
            "markers": raw_markers,
            "smoothing_applied": "stability_bonus",
            "transition": "none"
        }
    
    # Calculate direction of change
    raw_depth = DEPTH_ORDER.get(raw_level, 2)
    current_depth = DEPTH_ORDER.get(current_level, 2)
    
    is_moving_deeper = raw_depth > current_depth
    is_moving_shallower = raw_depth < current_depth
    
    # Check inference history for confirmation
    recent_history = inference_history[-SMOOTHING_CONFIG["max_history_entries"]:]
    
    # Count how many recent inferences agree with the proposed new level
    confirmations = sum(
        1 for h in recent_history 
        if h.get("level_id") == raw_level
    )
    
    # Determine if we should allow the transition
    allow_transition = False
    transition_reason = ""
    
    if is_moving_shallower:
        # Moving to lower depth (safety) - lower threshold, fewer confirmations needed
        if raw_confidence >= SMOOTHING_CONFIG["downward_threshold"]:
            # Allow immediate transition to shallower state if confident
            # Safety bias: we want to catch distress quickly
            allow_transition = True
            transition_reason = "safety_bias_shallower"
        elif confirmations >= 1:
            allow_transition = True
            transition_reason = "confirmed_shallower"
    
    elif is_moving_deeper:
        # Moving to higher depth - require more confirmation
        min_confirmations = SMOOTHING_CONFIG["min_confirmations"]
        required_confidence = SMOOTHING_CONFIG["upward_threshold"]
        
        if raw_confidence >= required_confidence and confirmations >= min_confirmations:
            allow_transition = True
            transition_reason = "confirmed_deeper"
        elif raw_confidence >= 0.8 and confirmations >= 1:
            # Very high confidence can reduce confirmation requirement
            allow_transition = True
            transition_reason = "high_confidence_deeper"
    
    # Apply the decision
    if allow_transition:
        return {
            "level_id": raw_level,
            "confidence": raw_confidence,
            "markers": raw_markers,
            "smoothing_applied": transition_reason,
            "transition": "deeper" if is_moving_deeper else "shallower",
            "confirmations": confirmations
        }
    else:
        # Stay at current level, but note the attempted transition
        # Apply a small dampening to confidence since we're overriding
        dampened_confidence = max(0.4, raw_confidence - 0.1)
        return {
            "level_id": current_level,
            "confidence": round(dampened_confidence, 2),
            "markers": raw_markers,
            "smoothing_applied": "transition_blocked",
            "blocked_transition_to": raw_level,
            "transition": "blocked",
            "reason": f"insufficient_confirmation_{confirmations}/{SMOOTHING_CONFIG['min_confirmations']}"
        }


def infer_level_from_text(
    text: str, 
    current_snapshot: Optional[Dict] = None,
    inference_history: List[Dict] = None
) -> Dict:
    """
    Infer consciousness level from text with smoothing applied.
    
    Args:
        text: The text to analyze
        current_snapshot: User's current consciousness snapshot (for smoothing)
        inference_history: Recent inference history (for confirmation)
    
    Returns a snapshot with inferred_level_id and confidence.
    Uses bias_lower_depth policy when signals conflict.
    Applies smoothing to prevent rapid state switching.
    """
    if not text:
        return get_default_snapshot()
    
    # Get raw inference
    raw_inference = _raw_infer_from_text(text)
    
    # Apply smoothing
    history = inference_history or []
    smoothed = apply_smoothing(raw_inference, current_snapshot, history)
    
    # Get level details
    level = get_level_by_id(smoothed["level_id"])
    
    # Build the snapshot
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Update history with this inference (for future smoothing)
    new_history_entry = {
        "level_id": raw_inference["level_id"],
        "confidence": raw_inference["confidence"],
        "timestamp": now_iso
    }
    
    # Keep recent history within window
    updated_history = (history or []) + [new_history_entry]
    updated_history = updated_history[-SMOOTHING_CONFIG["max_history_entries"]:]
    
    return {
        "inferred_level_id": smoothed["level_id"],
        "confidence": smoothed["confidence"],
        "signals": {
            "language_markers": smoothed.get("markers", []),
            "affect": level.get("primary_emotion", "neutral") if level else "neutral",
            "constraints": []
        },
        "last_updated_iso": now_iso,
        "source_events": ["text_analysis"],
        "smoothing": {
            "applied": smoothed.get("smoothing_applied", "none"),
            "transition": smoothed.get("transition", "none"),
            "blocked_to": smoothed.get("blocked_transition_to"),
            "confirmations": smoothed.get("confirmations", 0)
        },
        "inference_history": updated_history
    }


# Legacy compatibility functions (for existing imports)
def get_consciousness_framework() -> List[Dict]:
    """Legacy function - returns levels in simplified format."""
    config = get_consciousness_levels()
    return config.get("levels", [])


def analyze_consciousness_indicators(journal_text: str = None) -> Dict:
    """Legacy function - analyze text for consciousness indicators."""
    if not journal_text:
        return get_default_snapshot()
    return infer_level_from_text(journal_text)
