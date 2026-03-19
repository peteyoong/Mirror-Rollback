"""
Keystone Lens Explanation Generator
====================================

Generates explanations of the Keystone Pattern from each lens's perspective.

Each lens has ONE job:
- Astrology: Why TODAY triggers this pattern (timing_trigger)
- Human Design: Where this pattern comes from (mechanism)  
- Enneagram: Why this pattern repeats (repetition_loop)

All lenses explain the SAME Keystone. None replace it.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LensRole(str, Enum):
    """Each lens has a specific explanatory role"""
    TIMING_TRIGGER = "timing_trigger"      # Astrology: Why today
    MECHANISM = "mechanism"                 # Human Design: Where it comes from
    REPETITION_LOOP = "repetition_loop"    # Enneagram: Why it repeats


# =============================================================================
# ASTROLOGY TIMING EXPLANATIONS
# Maps pattern_id → why this pattern is loud TODAY
# =============================================================================

ASTROLOGY_TIMING_EXPLANATIONS = {
    "decision_switch_loop": {
        "title": "Why You Can't Land on Anything Today",
        "body": "Mercury is creating static in your decision-making. Information isn't landing cleanly. Every option seems equally valid—and equally flawed. The timing is working against closure."
    },
    "decide_then_undo": {
        "title": "Why You Keep Taking Things Back",
        "body": "There's tension between your impulse to act and your need to be sure. Today's timing rewards neither—commit too fast and you'll regret it, wait too long and the window closes."
    },
    "endless_options": {
        "title": "Why Nothing Feels Like The One",
        "body": "The current energy expands possibilities instead of narrowing them. Every door opens two more. Your system is absorbing options faster than it can process them."
    },
    "start_stop_restart": {
        "title": "Why You Can't Sustain Momentum",
        "body": "Today's rhythm is choppy. Energy comes in bursts that don't last. You have initiation without follow-through—not because you lack will, but because the timing doesn't support continuity."
    },
    "almost_act": {
        "title": "Why You Keep Pulling Back",
        "body": "There's a gap between readiness and release. You get to the edge, but something in the timing says 'not yet.' The hesitation isn't fear—it's information."
    },
    "action_delay_loop": {
        "title": "Why You Keep Postponing",
        "body": "The energy today favors planning over execution. Every time you try to act, something pulls you back to preparation. The delay isn't procrastination—it's misaligned timing."
    },
    "force_clarity_fail": {
        "title": "Why Answers Aren't Coming",
        "body": "Today's transit obscures rather than reveals. The harder you push for clarity, the more elusive it becomes. Understanding will come—but not through force."
    },
    "think_loop": {
        "title": "Why Your Mind Won't Stop",
        "body": "Mercury is amplifying your mental processing. Thoughts loop because there's too much information and not enough ground to stand on. The answer isn't more thinking."
    },
    "check_recheck": {
        "title": "Why You Keep Looking Again",
        "body": "Today's energy creates uncertainty about what you already know. Verification doesn't satisfy because the ground keeps shifting. Trust is hard to hold."
    },
    "direction_shift": {
        "title": "Why You Keep Changing Course",
        "body": "Cross-currents are pulling you in multiple directions. Each new input suggests a different path. The instability isn't in you—it's in the timing."
    },
    "restless_pivot": {
        "title": "Why You Can't Settle",
        "body": "The current transit creates internal restlessness. Stillness feels wrong. Movement feels purposeless. Your system is searching for ground that keeps moving."
    },
    "forward_backward": {
        "title": "Why Progress Feels Like Regression",
        "body": "Today's energy has a retrograde quality. Two steps forward, one step back. The pattern isn't failure—it's integration happening in real time."
    },
    "almost_done": {
        "title": "Why You Can't Cross The Finish Line",
        "body": "Completion is blocked by something you can't name. The last 10% feels harder than the first 90%. There's unfinished internal work that won't let you call it done."
    },
    "hold_open": {
        "title": "Why You Won't Close The Loop",
        "body": "Something in today's timing rewards optionality over closure. Keeping things open feels safer than finishing. The cost of commitment feels higher than usual."
    },
    "finish_unfinish": {
        "title": "Why Done Never Stays Done",
        "body": "Today's transit makes completion feel premature. What you finished keeps reopening because the timing wasn't actually right. Patience, not persistence, is the medicine."
    },
    "react_regret": {
        "title": "Why You're Moving Faster Than You Should",
        "body": "Mars is pushing impulse ahead of wisdom. Your reaction time is faster than your processing time. The gap creates regret before you've even understood what happened."
    },
    "feel_before_think": {
        "title": "Why Emotion Leads Today",
        "body": "The Moon is dominant, and your emotional body is processing faster than your mind. Feelings arrive fully formed before logic catches up. This isn't wrong—it's sequencing."
    },
    "snap_then_soften": {
        "title": "Why You're Sharp Then Sorry",
        "body": "There's friction between assertion and sensitivity today. Your first response comes out harder than you mean it. The softening that follows is real—but so was the edge."
    },
}


def generate_astrology_keystone_explanation(
    keystone_pattern_id: str,
    keystone_label: str,
    keystone_sequence: list,
    transit_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Astrology's explanation of WHY TODAY triggers this Keystone Pattern.
    
    Role: TIMING_TRIGGER
    Question answered: "Why is this pattern louder right now?"
    
    Returns the Lens Framing Contract:
    {
        "keystone_pattern_id": "...",
        "lens_role": "timing_trigger",
        "lens_explanation_title": "...",
        "lens_explanation_body": "...",
        "supports_keystone": true
    }
    """
    
    # Get the pre-written explanation for this pattern
    explanation = ASTROLOGY_TIMING_EXPLANATIONS.get(keystone_pattern_id)
    
    if explanation:
        return {
            "keystone_pattern_id": keystone_pattern_id,
            "keystone_label": keystone_label,
            "keystone_sequence": keystone_sequence,
            "lens_role": LensRole.TIMING_TRIGGER.value,
            "lens_explanation_title": explanation["title"],
            "lens_explanation_body": explanation["body"],
            "supports_keystone": True
        }
    
    # Fallback if pattern not in library
    logger.warning(f"[KeystoneExplanation] No astrology explanation for pattern: {keystone_pattern_id}")
    return {
        "keystone_pattern_id": keystone_pattern_id,
        "keystone_label": keystone_label,
        "keystone_sequence": keystone_sequence,
        "lens_role": LensRole.TIMING_TRIGGER.value,
        "lens_explanation_title": "Why This Pattern Is Active Today",
        "lens_explanation_body": "Current planetary positions are amplifying this behavioral loop. The timing is making this pattern more visible than usual.",
        "supports_keystone": True
    }


# =============================================================================
# VALIDATION: Ensure lens explanation matches Keystone
# =============================================================================

def validate_lens_explanation(
    lens_explanation: Dict[str, Any],
    expected_pattern_id: str
) -> Dict[str, Any]:
    """
    Validate that lens explanation matches the Keystone pattern.
    
    Fails if:
    - keystone_pattern_id doesn't match
    - supports_keystone is False
    
    Returns validation result with pass/fail status.
    """
    
    actual_pattern_id = lens_explanation.get("keystone_pattern_id")
    supports_keystone = lens_explanation.get("supports_keystone", False)
    
    if actual_pattern_id != expected_pattern_id:
        logger.error(f"[LensValidation] MISMATCH: Expected {expected_pattern_id}, got {actual_pattern_id}")
        return {
            "valid": False,
            "error": "pattern_id_mismatch",
            "expected": expected_pattern_id,
            "actual": actual_pattern_id
        }
    
    if not supports_keystone:
        logger.error(f"[LensValidation] Lens does not support Keystone: {actual_pattern_id}")
        return {
            "valid": False,
            "error": "lens_does_not_support_keystone",
            "pattern_id": actual_pattern_id
        }
    
    return {
        "valid": True,
        "pattern_id": actual_pattern_id,
        "lens_role": lens_explanation.get("lens_role")
    }
