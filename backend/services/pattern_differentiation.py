"""
Pattern Differentiation Engine
==============================

Prevents over-collapsing different lived situations into one generic pattern ("The Pause").
Creates specific, differentiated pattern diagnoses based on weighted multi-signal scoring.

PROBLEM SOLVED:
Different situations were collapsing into the same pattern:
- emotional clarity not landed → "The Pause"
- waiting on another person → "The Pause"
- blocked forward motion in work → "The Pause"
- avoiding an uncomfortable truth → "The Pause"

NEW APPROACH:
scene_type + tension_type + signal_source_mix → specific differentiated pattern

NEW PATTERN FAMILIES:
- premature_move: Already pushing before it's settled
- clarity_not_landed: Wanting certainty but clarity hasn't arrived
- blocked_by_others: Ready to move but depends on someone else
- avoided_truth: Recurring pattern, not facing something real
- split_pull: Genuinely torn between two valid directions
- pressure_without_decision: Feeling urgency without clarity to decide
- expression_held: Something needs to be said but isn't
- forcing_momentum: Trying to create motion through force
- direction_not_clean: The path forward isn't clear yet
- threshold_without_commitment: At a boundary, not crossing it
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# =============================================================================
# DIFFERENTIATED PATTERN TYPES
# =============================================================================

class DifferentiatedPattern(Enum):
    """Specific pattern types that replace generic 'stall' / 'pause' collapsing."""
    
    # HIGH-ACTION patterns (drive present, something blocking)
    PREMATURE_MOVE = "premature_move"
    FORCING_MOMENTUM = "forcing_momentum"
    
    # CLARITY patterns (wanting to know, can't yet)
    CLARITY_NOT_LANDED = "clarity_not_landed"
    DIRECTION_NOT_CLEAN = "direction_not_clean"
    
    # EXTERNAL DEPENDENCY patterns
    BLOCKED_BY_OTHERS = "blocked_by_others"
    WAITING_ON_RESPONSE = "waiting_on_response"
    
    # AVOIDANCE patterns
    AVOIDED_TRUTH = "avoided_truth"
    PROTECTION_MASKING = "protection_masking"
    
    # TENSION patterns (genuine competing pulls)
    SPLIT_PULL = "split_pull"
    PRESSURE_WITHOUT_DECISION = "pressure_without_decision"
    
    # EXPRESSION patterns
    EXPRESSION_HELD = "expression_held"
    TRUTH_UNSPOKEN = "truth_unspoken"
    
    # THRESHOLD patterns
    THRESHOLD_WITHOUT_COMMITMENT = "threshold_without_commitment"
    
    # SOFT FALLBACK (better than "The Pause")
    SOMETHING_NOT_CLEAN = "something_not_clean"
    BETWEEN_MOVEMENT_AND_CLARITY = "between_movement_and_clarity"


# =============================================================================
# SIGNAL DIMENSIONS FOR SCORING
# =============================================================================

@dataclass
class PatternSignalProfile:
    """Signal dimensions used for pattern scoring."""
    action_pressure: float = 0.0       # Drive to act/move
    clarity_delay: float = 0.0         # Uncertainty, fog, ambiguity
    external_dependency: float = 0.0   # Depends on others/external
    emotional_intensity: float = 0.0   # Emotional wave strength
    recurrence: float = 0.0            # Pattern repetition/history
    avoidance: float = 0.0             # Resistance, not facing
    expression_blockage: float = 0.0   # Something unsaid
    structural_friction: float = 0.0   # External blockers/obstacles
    urgency: float = 0.0               # Time pressure
    readiness_mismatch: float = 0.0    # Ready but timing isn't


# =============================================================================
# PATTERN SCORE RECIPES
# =============================================================================

# Each pattern has a "recipe" - required signal combination
PATTERN_RECIPES = {
    DifferentiatedPattern.PREMATURE_MOVE: {
        "required": {"action_pressure": 0.6, "clarity_delay": 0.4},
        "boosters": {"readiness_mismatch": 0.3, "urgency": 0.3},
        "dampeners": {"external_dependency": 0.5},
        "description": "You're already trying to move forward—but it hasn't settled yet."
    },
    DifferentiatedPattern.CLARITY_NOT_LANDED: {
        "required": {"clarity_delay": 0.6, "emotional_intensity": 0.3},
        "boosters": {"urgency": 0.3},
        "dampeners": {"action_pressure": 0.7},
        "description": "You want certainty now—but your clarity hasn't actually arrived yet."
    },
    DifferentiatedPattern.BLOCKED_BY_OTHERS: {
        "required": {"external_dependency": 0.6, "action_pressure": 0.4},
        "boosters": {"readiness_mismatch": 0.4},
        "dampeners": {"avoidance": 0.5},
        "description": "You're ready to move—but this isn't fully yours to move alone."
    },
    DifferentiatedPattern.AVOIDED_TRUTH: {
        "required": {"recurrence": 0.6, "avoidance": 0.5},
        "boosters": {"structural_friction": 0.3},
        "dampeners": {"clarity_delay": 0.7},
        "description": "This isn't stuck because nothing is happening.\nIt's stuck because something important still isn't being faced."
    },
    DifferentiatedPattern.FORCING_MOMENTUM: {
        "required": {"action_pressure": 0.7, "urgency": 0.5},
        "boosters": {"structural_friction": 0.4},
        "dampeners": {"external_dependency": 0.6},
        "description": "You're trying to make momentum happen by force.\nThat pressure is part of the problem."
    },
    DifferentiatedPattern.SPLIT_PULL: {
        "required": {"clarity_delay": 0.4, "emotional_intensity": 0.3},
        "boosters": {"recurrence": 0.3},
        "dampeners": {"action_pressure": 0.8, "external_dependency": 0.5},
        "description": "You're pulled between two directions—and both feel real.\nThe tension isn't confusion. It's competing truths."
    },
    DifferentiatedPattern.PRESSURE_WITHOUT_DECISION: {
        "required": {"urgency": 0.6, "clarity_delay": 0.5},
        "boosters": {"emotional_intensity": 0.3},
        "dampeners": {"action_pressure": 0.7},
        "description": "The pressure to decide is real—but the clarity to decide isn't.\nSomething is pushing you before you're ready."
    },
    DifferentiatedPattern.EXPRESSION_HELD: {
        "required": {"expression_blockage": 0.6},
        "boosters": {"emotional_intensity": 0.4, "avoidance": 0.3},
        "dampeners": {"external_dependency": 0.6},
        "description": "There's something you're not saying—and it's sitting in you.\nThe silence isn't peace. It's pressure."
    },
    DifferentiatedPattern.DIRECTION_NOT_CLEAN: {
        "required": {"clarity_delay": 0.5, "readiness_mismatch": 0.4},
        "boosters": {"recurrence": 0.3},
        "dampeners": {"action_pressure": 0.7, "external_dependency": 0.6},
        "description": "You know something needs to move—but the direction isn't clear.\nThe path exists. You just can't see it yet."
    },
    DifferentiatedPattern.THRESHOLD_WITHOUT_COMMITMENT: {
        "required": {"readiness_mismatch": 0.5, "action_pressure": 0.3},
        "boosters": {"clarity_delay": 0.4, "avoidance": 0.3},
        "dampeners": {"urgency": 0.7},
        "description": "You're standing at a threshold—but you haven't crossed it.\nThe door is open. The step hasn't happened."
    },
    DifferentiatedPattern.WAITING_ON_RESPONSE: {
        "required": {"external_dependency": 0.7},
        "boosters": {"action_pressure": 0.3, "urgency": 0.3},
        "dampeners": {"avoidance": 0.5},
        "description": "You're waiting for something that isn't yours to control.\nThe next move depends on someone else."
    },
    DifferentiatedPattern.PROTECTION_MASKING: {
        "required": {"avoidance": 0.6, "recurrence": 0.4},
        "boosters": {"emotional_intensity": 0.4},
        "dampeners": {"action_pressure": 0.6},
        "description": "The delay isn't confusion—it's protection.\nSomething is being avoided, and you might know what."
    },
    DifferentiatedPattern.TRUTH_UNSPOKEN: {
        "required": {"expression_blockage": 0.5, "avoidance": 0.4},
        "boosters": {"emotional_intensity": 0.4, "recurrence": 0.3},
        "dampeners": {"external_dependency": 0.5},
        "description": "There's a truth you haven't spoken—maybe to someone, maybe to yourself.\nIt's not that you can't say it. It's that you haven't."
    },
    # SOFT FALLBACKS - better than generic "The Pause"
    DifferentiatedPattern.SOMETHING_NOT_CLEAN: {
        "required": {"clarity_delay": 0.3},
        "boosters": {},
        "dampeners": {},
        "description": "Something isn't clean yet—but it's not clear what.\nThe stuckness is real. The cause is still emerging."
    },
    DifferentiatedPattern.BETWEEN_MOVEMENT_AND_CLARITY: {
        "required": {},
        "boosters": {"clarity_delay": 0.3, "action_pressure": 0.3},
        "dampeners": {},
        "description": "You're between moving and knowing.\nNeither is fully here yet."
    },
}


# =============================================================================
# PATTERN OUTPUTS (Recognition → Split → CTA)
# =============================================================================

PATTERN_OUTPUTS = {
    DifferentiatedPattern.PREMATURE_MOVE: {
        "name": "Premature Move",
        "recognition": "You're already trying to move this forward…",
        "split": "…but something in you knows it hasn't settled yet.",
        "cta": "See what isn't ready",
    },
    DifferentiatedPattern.CLARITY_NOT_LANDED: {
        "name": "Clarity Not Landed",
        "recognition": "You want certainty now…",
        "split": "…but your clarity hasn't actually arrived yet.",
        "cta": "Let it come to you",
    },
    DifferentiatedPattern.BLOCKED_BY_OTHERS: {
        "name": "Waiting on Response",
        "recognition": "You're ready to move…",
        "split": "…but this isn't fully yours to move alone.",
        "cta": "Name what you're waiting for",
    },
    DifferentiatedPattern.AVOIDED_TRUTH: {
        "name": "Avoided Truth",
        "recognition": "This isn't stuck because nothing is happening…",
        "split": "…it's stuck because something important still isn't being faced.",
        "cta": "Face what you already know",
    },
    DifferentiatedPattern.FORCING_MOMENTUM: {
        "name": "Forcing Momentum",
        "recognition": "You're trying to make momentum happen by force…",
        "split": "…and that pressure is part of the problem.",
        "cta": "Stop pushing for a moment",
    },
    DifferentiatedPattern.SPLIT_PULL: {
        "name": "Split Pull",
        "recognition": "You're pulled between two directions…",
        "split": "…and both feel real. That's why choosing feels impossible.",
        "cta": "Name both pulls",
    },
    DifferentiatedPattern.PRESSURE_WITHOUT_DECISION: {
        "name": "Pressure Without Decision",
        "recognition": "The pressure to decide is real…",
        "split": "…but the clarity to decide isn't.",
        "cta": "Notice the pressure's source",
    },
    DifferentiatedPattern.EXPRESSION_HELD: {
        "name": "Expression Held",
        "recognition": "There's something you're not saying…",
        "split": "…and it's sitting in you, taking up space.",
        "cta": "Say it somewhere safe",
    },
    DifferentiatedPattern.DIRECTION_NOT_CLEAN: {
        "name": "Direction Not Clean",
        "recognition": "You know something needs to move…",
        "split": "…but the direction isn't clear yet.",
        "cta": "Wait for the path to appear",
    },
    DifferentiatedPattern.THRESHOLD_WITHOUT_COMMITMENT: {
        "name": "Threshold Ahead",
        "recognition": "You're standing at a threshold…",
        "split": "…but you haven't crossed it. The door is open.",
        "cta": "Feel what's on the other side",
    },
    DifferentiatedPattern.WAITING_ON_RESPONSE: {
        "name": "Waiting on Response",
        "recognition": "You're waiting for something that isn't yours to control…",
        "split": "…and the waiting is starting to feel heavy.",
        "cta": "Name what you can do while waiting",
    },
    DifferentiatedPattern.PROTECTION_MASKING: {
        "name": "Protected Pause",
        "recognition": "This delay isn't confusion…",
        "split": "…it's protection. Something is being avoided.",
        "cta": "Ask what you're protecting",
    },
    DifferentiatedPattern.TRUTH_UNSPOKEN: {
        "name": "Unspoken Truth",
        "recognition": "There's a truth you haven't spoken…",
        "split": "…maybe to someone, maybe to yourself.",
        "cta": "Write it down first",
    },
    DifferentiatedPattern.SOMETHING_NOT_CLEAN: {
        "name": "Something's Off",
        "recognition": "Something isn't clean yet…",
        "split": "…but it's not clear what. The stuckness is real.",
        "cta": "Sit with not knowing",
    },
    DifferentiatedPattern.BETWEEN_MOVEMENT_AND_CLARITY: {
        "name": "Between States",
        "recognition": "You're between moving and knowing…",
        "split": "…and neither is fully here yet.",
        "cta": "Notice which is closer",
    },
}


# =============================================================================
# SIGNAL EXTRACTION FROM INPUTS
# =============================================================================

def extract_signal_profile(
    transit_aspects: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
    recent_interactions: List[Dict] = None,
) -> PatternSignalProfile:
    """
    Extract signal dimensions from all available data sources.
    
    Sources:
    A. Transit evidence
    B. Human Design timing/authority
    C. BaZi daily pressure/opportunity/resource signals
    D. Pattern history / journal recurrence
    E. Recent interaction history
    """
    profile = PatternSignalProfile()
    
    # A. TRANSIT EVIDENCE
    if transit_aspects:
        for aspect in transit_aspects:
            transit_point = aspect.get("transit_point", "").lower()
            aspect_type = aspect.get("aspect_type", "").lower()
            natal_point = aspect.get("natal_point", "").lower()
            weight = aspect.get("weight", 0.5)
            
            # Action/drive signals
            if transit_point in ["mars", "sun"] or "aries" in str(aspect):
                profile.action_pressure += weight * 0.4
            if aspect_type in ["conjunction", "opposition"]:
                profile.urgency += weight * 0.3
                
            # Clarity/confusion signals
            if transit_point in ["neptune", "moon"]:
                profile.clarity_delay += weight * 0.4
            if aspect_type in ["square"]:
                profile.structural_friction += weight * 0.3
                
            # External dependency signals
            if transit_point in ["venus"] or "7th" in str(natal_point) or "libra" in str(aspect):
                profile.external_dependency += weight * 0.4
                
            # Emotional intensity
            if transit_point in ["moon", "pluto"]:
                profile.emotional_intensity += weight * 0.4
            if natal_point in ["moon", "venus"]:
                profile.emotional_intensity += weight * 0.3
                
            # Expression signals
            if transit_point in ["mercury"] or "3rd" in str(natal_point):
                profile.expression_blockage += weight * 0.3
                
            # Avoidance signals (12th house, Neptune)
            if "12th" in str(natal_point) or transit_point in ["neptune"]:
                profile.avoidance += weight * 0.4
    
    # B. HUMAN DESIGN TIMING/AUTHORITY
    if hd_data:
        authority = hd_data.get("authority", "").lower()
        hd_type = hd_data.get("type", "").lower()
        defined_centers = hd_data.get("defined_centers", [])
        
        # Emotional authority = clarity delay
        if "emotional" in authority:
            profile.clarity_delay += 0.5
            profile.emotional_intensity += 0.4
            
        # Sacral/Splenic = action potential
        if "sacral" in authority or "splenic" in authority:
            profile.action_pressure += 0.3
            
        # Open G Center = direction unclear
        if "G Center" not in defined_centers and "G" not in defined_centers:
            profile.clarity_delay += 0.3
            
        # Projector waiting for invitation = external dependency
        if "projector" in hd_type:
            profile.external_dependency += 0.3
            profile.readiness_mismatch += 0.3
    
    # C. BAZI SIGNALS
    if bazi_data:
        day_signals = bazi_data.get("day_signals", {})
        
        if day_signals.get("pressure", 0) > 0.5:
            profile.urgency += 0.4
            profile.action_pressure += 0.3
            
        if day_signals.get("opportunity", 0) > 0.5:
            profile.readiness_mismatch += 0.3
            
        if day_signals.get("conflict", 0) > 0.5:
            profile.structural_friction += 0.4
    
    # D. PATTERN HISTORY / JOURNAL RECURRENCE
    if pattern_history:
        recent_count = len([p for p in pattern_history if p.get("days_ago", 999) < 7])
        if recent_count >= 3:
            profile.recurrence += 0.8
        elif recent_count >= 2:
            profile.recurrence += 0.5
        elif recent_count >= 1:
            profile.recurrence += 0.3
            
        # Check for avoidance patterns
        avoidance_patterns = [p for p in pattern_history if "avoid" in p.get("pattern_id", "").lower()]
        if len(avoidance_patterns) >= 2:
            profile.avoidance += 0.4
    
    if journal_entries:
        recent_journals = [j for j in journal_entries if j.get("days_ago", 999) < 14]
        
        # Look for recurring themes
        themes = {}
        for entry in recent_journals:
            content = entry.get("content", "").lower()
            if "waiting" in content or "stuck" in content:
                themes["stall"] = themes.get("stall", 0) + 1
            if "don't know" in content or "not sure" in content or "unclear" in content:
                themes["clarity"] = themes.get("clarity", 0) + 1
            if "say" in content or "tell" in content or "speak" in content:
                themes["expression"] = themes.get("expression", 0) + 1
            if "avoid" in content or "not facing" in content:
                themes["avoidance"] = themes.get("avoidance", 0) + 1
        
        if themes.get("stall", 0) >= 2:
            profile.recurrence += 0.3
        if themes.get("clarity", 0) >= 2:
            profile.clarity_delay += 0.3
        if themes.get("expression", 0) >= 2:
            profile.expression_blockage += 0.4
        if themes.get("avoidance", 0) >= 2:
            profile.avoidance += 0.4
    
    # E. RECENT INTERACTION HISTORY
    if recent_interactions:
        # Look for patterns in what user has been engaging with
        pass  # Can be extended based on interaction data structure
    
    # Normalize all scores to 0-1 range
    for field in [
        "action_pressure", "clarity_delay", "external_dependency",
        "emotional_intensity", "recurrence", "avoidance",
        "expression_blockage", "structural_friction", "urgency", "readiness_mismatch"
    ]:
        current = getattr(profile, field)
        setattr(profile, field, min(1.0, max(0.0, current)))
    
    return profile


# =============================================================================
# PATTERN SCORING AND SELECTION
# =============================================================================

def score_pattern(profile: PatternSignalProfile, pattern: DifferentiatedPattern) -> float:
    """
    Score how well a signal profile matches a pattern recipe.
    Returns confidence score 0-1.
    
    Patterns with more specific requirements should score higher when met.
    """
    recipe = PATTERN_RECIPES.get(pattern)
    if not recipe:
        return 0.0
    
    required = recipe.get("required", {})
    boosters = recipe.get("boosters", {})
    dampeners = recipe.get("dampeners", {})
    
    # Fallback patterns (empty/minimal requirements) get base low score
    if len(required) == 0:
        base_score = 0.2  # Low base for catch-all patterns
        # Add small boosts if any dimension is elevated
        for dimension, threshold in boosters.items():
            if getattr(profile, dimension, 0.0) >= threshold:
                base_score += 0.1
        return min(0.4, base_score)  # Cap at 0.4 for fallbacks
    
    # Calculate score for patterns with requirements
    required_met = 0
    required_total = len(required)
    
    for dimension, threshold in required.items():
        profile_value = getattr(profile, dimension, 0.0)
        if profile_value >= threshold:
            required_met += 1
    
    # If no required signals are met, return very low score
    if required_met == 0:
        return 0.1
    
    # Base score from required signals
    base_score = required_met / required_total
    
    # Booster signals add to score
    booster_bonus = 0
    for dimension, threshold in boosters.items():
        if getattr(profile, dimension, 0.0) >= threshold:
            booster_bonus += 0.15
    
    # Dampener signals reduce score
    dampener_penalty = 0
    for dimension, threshold in dampeners.items():
        if getattr(profile, dimension, 0.0) >= threshold:
            dampener_penalty += 0.2
    
    # Final confidence
    confidence = base_score + booster_bonus - dampener_penalty
    
    # Reward patterns with more requirements when fully met
    if required_met == required_total and required_total >= 2:
        confidence += 0.1
    
    return max(0.0, min(1.0, confidence))


def select_pattern(
    transit_aspects: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
    recent_interactions: List[Dict] = None,
    confidence_threshold: float = 0.5,
) -> Tuple[DifferentiatedPattern, float, List[Tuple[DifferentiatedPattern, float]]]:
    """
    Select the most appropriate differentiated pattern.
    
    Returns:
    - Selected pattern
    - Confidence score
    - Top 3 candidates with scores (for debugging/transparency)
    """
    
    # Extract signal profile
    profile = extract_signal_profile(
        transit_aspects=transit_aspects,
        hd_data=hd_data,
        bazi_data=bazi_data,
        pattern_history=pattern_history,
        journal_entries=journal_entries,
        recent_interactions=recent_interactions,
    )
    
    # Score all patterns
    scores = []
    for pattern in DifferentiatedPattern:
        confidence = score_pattern(profile, pattern)
        scores.append((pattern, confidence))
    
    # Sort by confidence
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top 3 for transparency
    top_3 = scores[:3]
    
    # Select best pattern above threshold
    best_pattern, best_score = scores[0]
    
    if best_score >= confidence_threshold:
        return best_pattern, best_score, top_3
    
    # Fallback to soft patterns if confidence is low
    if profile.clarity_delay > 0.3:
        return DifferentiatedPattern.SOMETHING_NOT_CLEAN, 0.4, top_3
    else:
        return DifferentiatedPattern.BETWEEN_MOVEMENT_AND_CLARITY, 0.3, top_3


# =============================================================================
# HOME MESSAGE GENERATION
# =============================================================================

def generate_home_message(
    pattern: DifferentiatedPattern,
    confidence: float,
    scene_type: str = None,
) -> Dict[str, str]:
    """
    Generate the home screen message for a pattern.
    
    Structure:
    1. Pattern name
    2. Recognition line (behavior observation)
    3. Split line (internal tension)
    4. CTA
    """
    output = PATTERN_OUTPUTS.get(pattern)
    if not output:
        output = PATTERN_OUTPUTS[DifferentiatedPattern.SOMETHING_NOT_CLEAN]
    
    # Build the message
    return {
        "pattern_name": output["name"],
        "pattern_id": pattern.value,
        "recognition": output["recognition"],
        "split": output["split"],
        "headline": f"{output['recognition']} {output['split']}",
        "cta": output["cta"],
        "confidence": confidence,
    }


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

def get_pattern_family_from_differentiated(pattern: DifferentiatedPattern) -> str:
    """Map differentiated pattern back to legacy pattern family for compatibility."""
    mapping = {
        DifferentiatedPattern.PREMATURE_MOVE: "stall",
        DifferentiatedPattern.CLARITY_NOT_LANDED: "clarity",
        DifferentiatedPattern.BLOCKED_BY_OTHERS: "stall",
        DifferentiatedPattern.AVOIDED_TRUTH: "avoidance",
        DifferentiatedPattern.FORCING_MOMENTUM: "stall",
        DifferentiatedPattern.SPLIT_PULL: "push_pull",
        DifferentiatedPattern.PRESSURE_WITHOUT_DECISION: "stall",
        DifferentiatedPattern.EXPRESSION_HELD: "expression",
        DifferentiatedPattern.DIRECTION_NOT_CLEAN: "clarity",
        DifferentiatedPattern.THRESHOLD_WITHOUT_COMMITMENT: "stall",
        DifferentiatedPattern.WAITING_ON_RESPONSE: "stall",
        DifferentiatedPattern.PROTECTION_MASKING: "avoidance",
        DifferentiatedPattern.TRUTH_UNSPOKEN: "expression",
        DifferentiatedPattern.SOMETHING_NOT_CLEAN: "general",
        DifferentiatedPattern.BETWEEN_MOVEMENT_AND_CLARITY: "general",
    }
    return mapping.get(pattern, "general")


def convert_legacy_tension_to_differentiated(
    tension_type: str,
    profile: PatternSignalProfile = None,
) -> DifferentiatedPattern:
    """Convert legacy tension types to differentiated patterns."""
    
    # Default mappings
    base_mapping = {
        "stall": DifferentiatedPattern.PREMATURE_MOVE,
        "push_pull": DifferentiatedPattern.SPLIT_PULL,
        "speak_swallow": DifferentiatedPattern.EXPRESSION_HELD,
        "grip_release": DifferentiatedPattern.PROTECTION_MASKING,
        "clarity_fog": DifferentiatedPattern.CLARITY_NOT_LANDED,
    }
    
    base_pattern = base_mapping.get(tension_type.lower(), DifferentiatedPattern.SOMETHING_NOT_CLEAN)
    
    # If we have a profile, refine the selection
    if profile:
        if tension_type == "stall":
            # Differentiate between stall subtypes
            if profile.recurrence > 0.5 and profile.avoidance > 0.4:
                return DifferentiatedPattern.AVOIDED_TRUTH
            elif profile.external_dependency > 0.5:
                return DifferentiatedPattern.BLOCKED_BY_OTHERS
            elif profile.action_pressure > 0.6:
                if profile.urgency > 0.5:
                    return DifferentiatedPattern.FORCING_MOMENTUM
                else:
                    return DifferentiatedPattern.PREMATURE_MOVE
            elif profile.clarity_delay > 0.5:
                return DifferentiatedPattern.CLARITY_NOT_LANDED
            elif profile.readiness_mismatch > 0.4:
                return DifferentiatedPattern.THRESHOLD_WITHOUT_COMMITMENT
    
    return base_pattern
