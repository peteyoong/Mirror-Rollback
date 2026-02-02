"""
Consciousness Lens v1 - Capacity-oriented, non-hierarchical framework
No fatalism. No identity pronouncements. Always optional language.
"""
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone

# Load the master configuration
CONFIG_PATH = Path(__file__).parent.parent / "data" / "consciousness_lens_v1.json"

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
        "source_events": ["default_fallback"]
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

def infer_level_from_text(text: str, recent_context: List[str] = None) -> Dict:
    """
    Infer consciousness level from text using language markers.
    
    Returns a snapshot with inferred_level_id and confidence.
    Uses bias_lower_depth policy when signals conflict.
    """
    if not text:
        return get_default_snapshot()
    
    config = get_consciousness_levels()
    levels = config.get("levels", [])
    defaults = config.get("defaults", {})
    
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
                "depth": level.get("depth", "medium")
            }
    
    if not level_scores:
        return get_default_snapshot()
    
    # Find highest scoring level
    max_score = max(s["score"] for s in level_scores.values())
    
    # Get all levels with max score
    top_levels = [
        (lid, data) for lid, data in level_scores.items() 
        if data["score"] == max_score
    ]
    
    # If conflict (multiple top scorers), bias to lower depth
    if len(top_levels) > 1:
        # Order by depth: low < medium_low < medium < high
        depth_order = {"low": 0, "medium_low": 1, "medium": 2, "high": 3}
        top_levels.sort(key=lambda x: depth_order.get(x[1]["depth"], 2))
        chosen_level_id = top_levels[0][0]
        chosen_data = top_levels[0][1]
    else:
        chosen_level_id = top_levels[0][0]
        chosen_data = top_levels[0][1]
    
    # Calculate confidence based on score strength
    total_markers = sum(len(level.get("language_markers", [])) for level in levels)
    confidence = min(0.95, 0.3 + (chosen_data["score"] / max(1, len(chosen_data["markers"]))) * 0.4)
    
    return {
        "inferred_level_id": chosen_level_id,
        "confidence": round(confidence, 2),
        "signals": {
            "language_markers": chosen_data["markers"],
            "affect": get_level_by_id(chosen_level_id).get("primary_emotion", "neutral"),
            "constraints": []
        },
        "last_updated_iso": datetime.now(timezone.utc).isoformat(),
        "source_events": ["text_analysis"]
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
