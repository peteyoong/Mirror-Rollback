"""
Keystone Pattern Detection Engine
==================================

From Astrology, Human Design, and Enneagram inputs,
detect ONE dominant behavioral pattern.

Step 1 Only: Pattern Detection (no narrative generation)

Output: ONE observable behavioral pattern the user literally did today.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERN TYPES
# =============================================================================

class KeystonePattern(str, Enum):
    """Core behavioral patterns - observable, specific, non-abstract"""
    
    # Decision patterns
    DECISION_SWITCH_LOOP = "decision_switch_loop"           # decide → hesitate → switch
    DECIDE_THEN_UNDO = "decide_then_undo"                   # commit → doubt → reverse
    ENDLESS_OPTIONS = "endless_options"                      # consider → consider more → never pick
    
    # Action patterns
    START_STOP_RESTART = "start_stop_restart"               # begin → stop → begin again
    ALMOST_ACT = "almost_act"                               # reach for it → pull back → reach again
    ACTION_DELAY_LOOP = "action_delay_loop"                 # plan to act → delay → plan again
    
    # Clarity patterns
    FORCE_CLARITY_FAIL = "force_clarity_fail"               # push for answer → nothing lands
    THINK_LOOP = "think_loop"                               # figure it out → doubt it → figure again
    CHECK_RECHECK = "check_recheck"                         # verify → not sure → verify again
    
    # Movement patterns
    DIRECTION_SHIFT = "direction_shift"                     # head one way → change → head another
    RESTLESS_PIVOT = "restless_pivot"                       # settle → unsettled → move again
    FORWARD_BACKWARD = "forward_backward"                   # progress → retreat → progress
    
    # Completion patterns
    ALMOST_DONE = "almost_done"                             # near finish → pull back → near again
    HOLD_OPEN = "hold_open"                                 # could close → don't → could close again
    FINISH_UNFINISH = "finish_unfinish"                     # complete → reopen → complete
    
    # Reaction patterns
    REACT_REGRET = "react_regret"                           # respond fast → realize too fast
    FEEL_BEFORE_THINK = "feel_before_think"                 # emotion leads → mind catches up late
    SNAP_THEN_SOFTEN = "snap_then_soften"                   # sharp response → soften after


# =============================================================================
# PATTERN DEFINITIONS
# =============================================================================

PATTERN_DEFINITIONS = {
    KeystonePattern.DECISION_SWITCH_LOOP: {
        "label": "Decide → hesitate → switch",
        "sequence": [
            "decide something",
            "hesitate / something doesn't land",
            "switch to another option"
        ],
    },
    KeystonePattern.DECIDE_THEN_UNDO: {
        "label": "Commit → doubt → reverse",
        "sequence": [
            "commit to a choice",
            "doubt creeps in",
            "reverse or undo the decision"
        ],
    },
    KeystonePattern.ENDLESS_OPTIONS: {
        "label": "Consider → consider more → never pick",
        "sequence": [
            "look at options",
            "find more options",
            "don't pick any"
        ],
    },
    KeystonePattern.START_STOP_RESTART: {
        "label": "Start → stop → start again",
        "sequence": [
            "begin something",
            "stop mid-way",
            "start it again later"
        ],
    },
    KeystonePattern.ALMOST_ACT: {
        "label": "Reach → pull back → reach again",
        "sequence": [
            "move toward action",
            "pull back at the edge",
            "move toward it again"
        ],
    },
    KeystonePattern.ACTION_DELAY_LOOP: {
        "label": "Plan → delay → plan again",
        "sequence": [
            "plan to do something",
            "delay doing it",
            "plan to do it again"
        ],
    },
    KeystonePattern.FORCE_CLARITY_FAIL: {
        "label": "Push for answer → nothing lands",
        "sequence": [
            "try to figure it out",
            "answer doesn't stick",
            "try again"
        ],
    },
    KeystonePattern.THINK_LOOP: {
        "label": "Figure out → doubt → figure again",
        "sequence": [
            "think you understand",
            "doubt the understanding",
            "think through it again"
        ],
    },
    KeystonePattern.CHECK_RECHECK: {
        "label": "Check → not sure → check again",
        "sequence": [
            "verify something",
            "still not certain",
            "check it again"
        ],
    },
    KeystonePattern.DIRECTION_SHIFT: {
        "label": "Head one way → change → head another",
        "sequence": [
            "move in a direction",
            "direction doesn't feel right",
            "change to another direction"
        ],
    },
    KeystonePattern.RESTLESS_PIVOT: {
        "label": "Settle → unsettled → move",
        "sequence": [
            "settle into something",
            "feel unsettled",
            "move to something else"
        ],
    },
    KeystonePattern.FORWARD_BACKWARD: {
        "label": "Progress → retreat → progress",
        "sequence": [
            "make progress forward",
            "pull back or retreat",
            "try to progress again"
        ],
    },
    KeystonePattern.ALMOST_DONE: {
        "label": "Near finish → pull back → near again",
        "sequence": [
            "get close to done",
            "pull back from completion",
            "get close again"
        ],
    },
    KeystonePattern.HOLD_OPEN: {
        "label": "Could close → don't → could close again",
        "sequence": [
            "have option to finish",
            "keep it open instead",
            "option to finish returns"
        ],
    },
    KeystonePattern.FINISH_UNFINISH: {
        "label": "Complete → reopen → complete",
        "sequence": [
            "finish something",
            "reopen or revisit it",
            "try to finish again"
        ],
    },
    KeystonePattern.REACT_REGRET: {
        "label": "Respond fast → realize too fast",
        "sequence": [
            "respond quickly",
            "realize it was too quick",
            "wish you'd waited"
        ],
    },
    KeystonePattern.FEEL_BEFORE_THINK: {
        "label": "Feel first → think catches up",
        "sequence": [
            "feel something strongly",
            "react from the feeling",
            "understanding comes after"
        ],
    },
    KeystonePattern.SNAP_THEN_SOFTEN: {
        "label": "Sharp response → soften after",
        "sequence": [
            "respond sharply",
            "realize it was too sharp",
            "soften or regret"
        ],
    },
}


# =============================================================================
# SIGNAL MAPPING
# =============================================================================

# Astrology tension → pattern mapping
ASTROLOGY_TO_PATTERN = {
    "forcing_clarity": [
        KeystonePattern.FORCE_CLARITY_FAIL,
        KeystonePattern.THINK_LOOP,
        KeystonePattern.CHECK_RECHECK,
    ],
    "movement_before_alignment": [
        KeystonePattern.ALMOST_ACT,
        KeystonePattern.START_STOP_RESTART,
        KeystonePattern.ACTION_DELAY_LOOP,
    ],
    "reacting_before_understanding": [
        KeystonePattern.REACT_REGRET,
        KeystonePattern.FEEL_BEFORE_THINK,
        KeystonePattern.SNAP_THEN_SOFTEN,
    ],
    "reopening_unresolved": [
        KeystonePattern.FINISH_UNFINISH,
        KeystonePattern.HOLD_OPEN,
        KeystonePattern.THINK_LOOP,
    ],
    "shift_before_direction": [
        KeystonePattern.DIRECTION_SHIFT,
        KeystonePattern.DECISION_SWITCH_LOOP,
        KeystonePattern.RESTLESS_PIVOT,
    ],
    "inner_pace_outer_timing": [
        KeystonePattern.ACTION_DELAY_LOOP,
        KeystonePattern.FORWARD_BACKWARD,
        KeystonePattern.ALMOST_ACT,
    ],
    "completion_resistance": [
        KeystonePattern.ALMOST_DONE,
        KeystonePattern.HOLD_OPEN,
        KeystonePattern.FINISH_UNFINISH,
    ],
}

# Enneagram type → pattern affinity
ENNEAGRAM_TO_PATTERN = {
    1: [KeystonePattern.CHECK_RECHECK, KeystonePattern.FINISH_UNFINISH],  # perfectionist
    2: [KeystonePattern.REACT_REGRET, KeystonePattern.SNAP_THEN_SOFTEN],  # helper overextends
    3: [KeystonePattern.START_STOP_RESTART, KeystonePattern.FORWARD_BACKWARD],  # achiever pivots
    4: [KeystonePattern.FEEL_BEFORE_THINK, KeystonePattern.DIRECTION_SHIFT],  # individualist
    5: [KeystonePattern.THINK_LOOP, KeystonePattern.FORCE_CLARITY_FAIL],  # investigator
    6: [KeystonePattern.DECISION_SWITCH_LOOP, KeystonePattern.CHECK_RECHECK],  # loyalist doubt
    7: [KeystonePattern.ENDLESS_OPTIONS, KeystonePattern.RESTLESS_PIVOT],  # enthusiast scatters
    8: [KeystonePattern.ALMOST_ACT, KeystonePattern.SNAP_THEN_SOFTEN],  # challenger
    9: [KeystonePattern.ACTION_DELAY_LOOP, KeystonePattern.HOLD_OPEN],  # peacemaker avoids
}

# Human Design center activations → pattern affinity
HD_CENTER_TO_PATTERN = {
    "head": [KeystonePattern.THINK_LOOP, KeystonePattern.FORCE_CLARITY_FAIL],
    "ajna": [KeystonePattern.CHECK_RECHECK, KeystonePattern.ENDLESS_OPTIONS],
    "throat": [KeystonePattern.ALMOST_ACT, KeystonePattern.START_STOP_RESTART],
    "g_center": [KeystonePattern.DIRECTION_SHIFT, KeystonePattern.RESTLESS_PIVOT],
    "heart": [KeystonePattern.DECIDE_THEN_UNDO, KeystonePattern.FORWARD_BACKWARD],
    "sacral": [KeystonePattern.START_STOP_RESTART, KeystonePattern.ACTION_DELAY_LOOP],
    "solar_plexus": [KeystonePattern.REACT_REGRET, KeystonePattern.FEEL_BEFORE_THINK],
    "spleen": [KeystonePattern.SNAP_THEN_SOFTEN, KeystonePattern.ALMOST_ACT],
    "root": [KeystonePattern.ACTION_DELAY_LOOP, KeystonePattern.FORWARD_BACKWARD],
}


# =============================================================================
# PATTERN DETECTION ENGINE
# =============================================================================

@dataclass
class PatternSignal:
    """A signal pointing toward a pattern"""
    pattern: KeystonePattern
    source: str  # astrology, human_design, enneagram
    weight: float  # 0.0 - 1.0


def extract_astrology_signals(astrology_input: Dict[str, Any]) -> List[PatternSignal]:
    """Extract pattern signals from astrology data"""
    signals = []
    
    dominant_tension = astrology_input.get("dominant_tension", "").lower().replace(" ", "_")
    
    if dominant_tension in ASTROLOGY_TO_PATTERN:
        patterns = ASTROLOGY_TO_PATTERN[dominant_tension]
        # Primary pattern gets highest weight
        for i, pattern in enumerate(patterns):
            weight = 0.9 - (i * 0.15)  # 0.9, 0.75, 0.6
            signals.append(PatternSignal(
                pattern=pattern,
                source="astrology",
                weight=weight
            ))
    
    # Boost weight if phase_shift day class
    transit_stack = astrology_input.get("transit_stack", {})
    if transit_stack.get("classification") == "phase_shift":
        for signal in signals:
            signal.weight = min(1.0, signal.weight + 0.1)
    
    return signals


def extract_human_design_signals(hd_input: Dict[str, Any]) -> List[PatternSignal]:
    """Extract pattern signals from Human Design data"""
    signals = []
    
    active_centers = hd_input.get("active_centers", [])
    
    for center in active_centers:
        center_key = center.lower().replace(" ", "_")
        if center_key in HD_CENTER_TO_PATTERN:
            patterns = HD_CENTER_TO_PATTERN[center_key]
            for i, pattern in enumerate(patterns):
                weight = 0.7 - (i * 0.2)  # 0.7, 0.5
                signals.append(PatternSignal(
                    pattern=pattern,
                    source="human_design",
                    weight=weight
                ))
    
    # Check for decision instability (multiple defined centers)
    defined_channels = hd_input.get("defined_channels", [])
    if len(defined_channels) >= 3:
        # More definition = more potential for internal conflict
        signals.append(PatternSignal(
            pattern=KeystonePattern.DECISION_SWITCH_LOOP,
            source="human_design",
            weight=0.5
        ))
    
    return signals


def extract_enneagram_signals(ennea_input: Dict[str, Any]) -> List[PatternSignal]:
    """Extract pattern signals from Enneagram data"""
    signals = []
    
    ennea_type = ennea_input.get("type")
    if ennea_type and ennea_type in ENNEAGRAM_TO_PATTERN:
        patterns = ENNEAGRAM_TO_PATTERN[ennea_type]
        for i, pattern in enumerate(patterns):
            weight = 0.8 - (i * 0.2)  # 0.8, 0.6
            signals.append(PatternSignal(
                pattern=pattern,
                source="enneagram",
                weight=weight
            ))
    
    # Check current pattern activation
    current_activation = ennea_input.get("current_pattern_activation", "").lower()
    if "avoid" in current_activation:
        signals.append(PatternSignal(
            pattern=KeystonePattern.ACTION_DELAY_LOOP,
            source="enneagram",
            weight=0.7
        ))
    elif "push" in current_activation:
        signals.append(PatternSignal(
            pattern=KeystonePattern.FORCE_CLARITY_FAIL,
            source="enneagram",
            weight=0.7
        ))
    elif "switch" in current_activation:
        signals.append(PatternSignal(
            pattern=KeystonePattern.DECISION_SWITCH_LOOP,
            source="enneagram",
            weight=0.7
        ))
    elif "delay" in current_activation:
        signals.append(PatternSignal(
            pattern=KeystonePattern.ACTION_DELAY_LOOP,
            source="enneagram",
            weight=0.7
        ))
    
    return signals


def collapse_to_one_pattern(signals: List[PatternSignal]) -> Tuple[KeystonePattern, float]:
    """
    Collapse all signals into ONE dominant pattern.
    
    Returns (pattern, confidence)
    """
    if not signals:
        # Default fallback
        return KeystonePattern.DECISION_SWITCH_LOOP, 0.3
    
    # Aggregate weights by pattern
    pattern_scores: Dict[KeystonePattern, float] = {}
    pattern_sources: Dict[KeystonePattern, set] = {}
    
    for signal in signals:
        if signal.pattern not in pattern_scores:
            pattern_scores[signal.pattern] = 0.0
            pattern_sources[signal.pattern] = set()
        
        pattern_scores[signal.pattern] += signal.weight
        pattern_sources[signal.pattern].add(signal.source)
    
    # Boost patterns that appear in multiple sources (convergence bonus)
    for pattern in pattern_scores:
        source_count = len(pattern_sources[pattern])
        if source_count >= 3:
            pattern_scores[pattern] *= 1.5  # Strong convergence
        elif source_count >= 2:
            pattern_scores[pattern] *= 1.25  # Moderate convergence
    
    # Find the dominant pattern
    dominant_pattern = max(pattern_scores, key=pattern_scores.get)
    raw_score = pattern_scores[dominant_pattern]
    
    # Normalize confidence to 0.0 - 1.0
    # Max possible score is roughly 3.0 (all three sources, high weights, convergence)
    confidence = min(1.0, raw_score / 3.0)
    
    # Round confidence to 2 decimal places
    confidence = round(confidence, 2)
    
    return dominant_pattern, confidence


# =============================================================================
# VALIDATION
# =============================================================================

ABSTRACT_WORDS = [
    "growth", "clarity", "alignment", "energy", "transformation",
    "journey", "path", "universe", "cosmic", "spiritual",
    "healing", "awakening", "consciousness", "vibration",
]

def validate_pattern_output(output: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate the pattern output against hard fail conditions.
    
    Returns (is_valid, reason)
    """
    # Check for abstract words in label or sequence
    label = output.get("pattern_label", "").lower()
    sequence = output.get("behavior_sequence", [])
    
    all_text = label + " " + " ".join(sequence)
    
    for word in ABSTRACT_WORDS:
        if word in all_text.lower():
            return False, f"Contains abstract word: '{word}'"
    
    # Check sequence is behavioral (must have action verbs)
    action_indicators = [
        "decide", "start", "stop", "push", "pull", "check", "move",
        "respond", "feel", "think", "commit", "hesitate", "switch",
        "begin", "finish", "open", "close", "consider", "pick",
        "reach", "delay", "plan", "progress", "retreat", "settle",
    ]
    
    has_action = any(
        any(indicator in step.lower() for indicator in action_indicators)
        for step in sequence
    )
    
    if not has_action:
        return False, "Sequence lacks action verbs - not behavioral enough"
    
    return True, "Valid"


# =============================================================================
# MAIN DETECTION FUNCTION
# =============================================================================

def detect_keystone_pattern(
    astrology: Optional[Dict[str, Any]] = None,
    human_design: Optional[Dict[str, Any]] = None,
    enneagram: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Detect ONE dominant behavioral pattern from multi-lens input.
    
    Args:
        astrology: {dominant_tension, altitude, transit_stack}
        human_design: {active_centers, defined_channels, current_transit_gates}
        enneagram: {type, pattern, current_pattern_activation}
    
    Returns:
        {
            "pattern_id": "string_snake_case",
            "pattern_label": "short human readable label",
            "behavior_sequence": ["action", "break_point", "continuation"],
            "confidence": 0.0-1.0,
            "sources": ["astrology", "human_design", "enneagram"]
        }
    """
    # Collect signals from all sources
    all_signals: List[PatternSignal] = []
    active_sources: List[str] = []
    
    if astrology:
        astro_signals = extract_astrology_signals(astrology)
        all_signals.extend(astro_signals)
        if astro_signals:
            active_sources.append("astrology")
    
    if human_design:
        hd_signals = extract_human_design_signals(human_design)
        all_signals.extend(hd_signals)
        if hd_signals:
            active_sources.append("human_design")
    
    if enneagram:
        ennea_signals = extract_enneagram_signals(enneagram)
        all_signals.extend(ennea_signals)
        if ennea_signals:
            active_sources.append("enneagram")
    
    # Log signal extraction
    logger.info(f"[KeystonePattern] Extracted {len(all_signals)} signals from {active_sources}")
    
    # Collapse to ONE pattern
    dominant_pattern, confidence = collapse_to_one_pattern(all_signals)
    
    # Get pattern definition
    pattern_def = PATTERN_DEFINITIONS.get(dominant_pattern, {
        "label": dominant_pattern.value.replace("_", " ").title(),
        "sequence": ["action", "interruption", "continuation"]
    })
    
    # Build output
    output = {
        "pattern_id": dominant_pattern.value,
        "pattern_label": pattern_def["label"],
        "behavior_sequence": pattern_def["sequence"],
        "confidence": confidence,
        "sources": active_sources,
    }
    
    # Validate
    is_valid, reason = validate_pattern_output(output)
    if not is_valid:
        logger.warning(f"[KeystonePattern] Validation failed: {reason}")
        # Fallback to decision_switch_loop which is always valid
        fallback = PATTERN_DEFINITIONS[KeystonePattern.DECISION_SWITCH_LOOP]
        output = {
            "pattern_id": KeystonePattern.DECISION_SWITCH_LOOP.value,
            "pattern_label": fallback["label"],
            "behavior_sequence": fallback["sequence"],
            "confidence": 0.5,
            "sources": active_sources,
        }
    
    logger.info(f"[KeystonePattern] Detected: {output['pattern_id']} (confidence={output['confidence']})")
    
    return output


# =============================================================================
# CONVENIENCE FUNCTION FOR ENDPOINT
# =============================================================================

def detect_pattern_for_user(
    user_id: str,
    astrology_tension: Optional[str] = None,
    astrology_transit_stack: Optional[Dict] = None,
    hd_active_centers: Optional[List[str]] = None,
    hd_defined_channels: Optional[List[str]] = None,
    enneagram_type: Optional[int] = None,
    enneagram_activation: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function that takes individual parameters.
    """
    astrology = None
    if astrology_tension:
        astrology = {
            "dominant_tension": astrology_tension,
            "altitude": "today",
            "transit_stack": astrology_transit_stack or {},
        }
    
    human_design = None
    if hd_active_centers:
        human_design = {
            "active_centers": hd_active_centers,
            "defined_channels": hd_defined_channels or [],
            "current_transit_gates": [],
        }
    
    enneagram = None
    if enneagram_type:
        enneagram = {
            "type": enneagram_type,
            "pattern": "",
            "current_pattern_activation": enneagram_activation or "",
        }
    
    return detect_keystone_pattern(
        astrology=astrology,
        human_design=human_design,
        enneagram=enneagram,
    )
