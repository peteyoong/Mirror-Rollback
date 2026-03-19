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
#
# RULES:
# - Must reference specific timing (transit, moon phase, planetary position)
# - Must answer: "Why TODAY specifically?"
# - NO banned words: energy, alignment, growth, transformation, awareness
# - Must be causally tied to the Keystone behavior, not personality
# =============================================================================

ASTROLOGY_TIMING_EXPLANATIONS = {
    "decision_switch_loop": {
        "title": "Why You Can't Land on Anything Right Now",
        "body": "Mercury is square Neptune today. Information is distorted. What seemed clear five minutes ago now has gaps. You're not indecisive—you're receiving conflicting signals that make commitment feel premature."
    },
    "decide_then_undo": {
        "title": "Why You Keep Taking Things Back",
        "body": "Mars is pushing action while the Moon is in a holding pattern. You commit from impulse, then the slower part of you catches up and says 'wait.' The reversal isn't weakness—it's two different timing systems colliding."
    },
    "endless_options": {
        "title": "Why Nothing Feels Like The One",
        "body": "Jupiter is expanding your field of perception today. Every option opens two more. Your system is absorbing faster than it can filter. The paralysis isn't in you—it's in the volume of incoming data."
    },
    "start_stop_restart": {
        "title": "Why You Can't Sustain Momentum",
        "body": "The Moon is void-of-course right now. Actions started during this window tend to stall or need restarting. This isn't a personal failing—it's literally a dead zone for follow-through."
    },
    "almost_act": {
        "title": "Why You Keep Pulling Back at the Edge",
        "body": "Saturn is aspecting your action planets today. Every time you reach forward, something pulls you back for one more check. The hesitation is Saturn asking: 'Are you actually ready for what happens next?'"
    },
    "action_delay_loop": {
        "title": "Why You Keep Postponing",
        "body": "Mars is in a slow sign and squared by Saturn. The drive to act is there, but the timing keeps saying 'not yet.' You're not procrastinating—the window for clean action hasn't opened."
    },
    "force_clarity_fail": {
        "title": "Why Answers Aren't Coming",
        "body": "Mercury is conjunct Neptune today. The harder you push for clarity, the more it dissolves. This isn't confusion—it's a transit that dissolves false certainty before real understanding arrives."
    },
    "think_loop": {
        "title": "Why Your Mind Won't Stop Looping",
        "body": "Mercury is in a tight aspect to Pluto today. Thoughts go deep, then deeper, then circle back. You're not overthinking—you're caught in a transit that demands you see what's underneath."
    },
    "check_recheck": {
        "title": "Why You Keep Looking Again",
        "body": "The Moon is in Virgo today, activating the part of you that double-checks everything. Verification doesn't satisfy because the transit keeps moving the threshold for 'enough.' It passes tomorrow."
    },
    "direction_shift": {
        "title": "Why You Keep Changing Course",
        "body": "Uranus is active in your chart today. Each new input rewrites the previous plan. The instability isn't in your character—it's in a transit that literally specializes in sudden pivots."
    },
    "restless_pivot": {
        "title": "Why You Can't Stay in One Place",
        "body": "The Moon is making multiple hard aspects today—square, opposition, square again. Every few hours, your internal state shifts. You're not restless by nature right now—you're being moved by rapid lunar transits."
    },
    "forward_backward": {
        "title": "Why Progress Feels Like Regression",
        "body": "Mercury is stationing retrograde (or just stationed direct). Forward motion hits review mode. Two steps forward, one step back isn't failure—it's the literal signature of this transit period."
    },
    "almost_done": {
        "title": "Why You Can't Cross The Finish Line",
        "body": "Saturn is aspecting your completion planets today. The last 10% requires more than the first 90%. This isn't resistance—it's a transit that demands you earn the ending."
    },
    "hold_open": {
        "title": "Why You Won't Close The Loop",
        "body": "Neptune is active today, blurring boundaries between done and not-done. Closure feels like loss of possibility. You're not avoiding commitment—you're under a transit that makes endings feel premature."
    },
    "finish_unfinish": {
        "title": "Why Done Never Stays Done",
        "body": "Mercury retrograde (or its shadow) is activating revision. What you finished keeps reopening because the transit insists on one more pass. Completion will stick once Mercury clears this zone."
    },
    "react_regret": {
        "title": "Why You're Moving Faster Than You Should",
        "body": "Mars is conjunct or square your natal Mercury today. Your reaction speed is outpacing your processing speed. The impulse arrives before the thought completes. This gap closes when Mars moves on."
    },
    "feel_before_think": {
        "title": "Why Emotion Arrives Before Logic",
        "body": "The Moon is making a hard aspect to Mercury today. Emotional data is reaching you faster than mental data. You're not being irrational—you're receiving information in the wrong order."
    },
    "snap_then_soften": {
        "title": "Why You're Sharp Then Sorry",
        "body": "Mars is square Venus today. Assertion comes out harder than intended because tenderness isn't available in the same moment. The softening that follows is the Venus catching up. The friction is temporary."
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

# Banned words that indicate generic/vague language
BANNED_WORDS = [
    "energy", "energies", "alignment", "aligned", "growth", 
    "transformation", "transforming", "awareness", "conscious",
    "vibration", "vibrations", "manifest", "manifesting",
    "universe", "cosmic", "spiritual", "journey"
]


def validate_lens_explanation(
    lens_explanation: Dict[str, Any],
    expected_pattern_id: str
) -> Dict[str, Any]:
    """
    Validate that lens explanation matches the Keystone pattern.
    
    Fails if:
    - keystone_pattern_id doesn't match
    - supports_keystone is False
    - explanation contains banned words
    - explanation is too generic (doesn't mention timing)
    
    Returns validation result with pass/fail status.
    """
    
    actual_pattern_id = lens_explanation.get("keystone_pattern_id")
    supports_keystone = lens_explanation.get("supports_keystone", False)
    explanation_body = lens_explanation.get("lens_explanation_body", "").lower()
    
    # Check 1: Pattern ID must match
    if actual_pattern_id != expected_pattern_id:
        logger.error(f"[LensValidation] MISMATCH: Expected {expected_pattern_id}, got {actual_pattern_id}")
        return {
            "valid": False,
            "error": "pattern_id_mismatch",
            "expected": expected_pattern_id,
            "actual": actual_pattern_id
        }
    
    # Check 2: Must support keystone
    if not supports_keystone:
        logger.error(f"[LensValidation] Lens does not support Keystone: {actual_pattern_id}")
        return {
            "valid": False,
            "error": "lens_does_not_support_keystone",
            "pattern_id": actual_pattern_id
        }
    
    # Check 3: No banned words
    found_banned = [word for word in BANNED_WORDS if word in explanation_body]
    if found_banned:
        logger.warning(f"[LensValidation] Banned words found in explanation: {found_banned}")
        return {
            "valid": False,
            "error": "contains_banned_words",
            "banned_words_found": found_banned,
            "pattern_id": actual_pattern_id
        }
    
    # Check 4: Must contain timing language (for astrology)
    timing_indicators = [
        "today", "right now", "this transit", "currently", 
        "mercury", "mars", "venus", "saturn", "jupiter", "uranus", "neptune", "pluto",
        "moon", "sun", "retrograde", "square", "conjunct", "aspect",
        "this window", "this period", "passes", "moves on", "clears"
    ]
    has_timing = any(indicator in explanation_body for indicator in timing_indicators)
    
    if not has_timing:
        logger.warning(f"[LensValidation] No timing language found in explanation")
        return {
            "valid": False,
            "error": "missing_timing_language",
            "pattern_id": actual_pattern_id
        }
    
    return {
        "valid": True,
        "pattern_id": actual_pattern_id,
        "lens_role": lens_explanation.get("lens_role")
    }
