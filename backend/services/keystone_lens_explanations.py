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
        "title": "Why Today Won't Let You Land",
        "body": "Mercury is square Neptune today. Information is distorted. What seemed clear five minutes ago now has gaps. You're not indecisive—you're receiving conflicting signals that make commitment feel premature."
    },
    "decide_then_undo": {
        "title": "Why Today Pulls You Back",
        "body": "Mars is pushing action while the Moon is in a holding pattern. You commit from impulse, then the slower part catches up and says 'wait.' Two different timing systems are colliding."
    },
    "endless_options": {
        "title": "Why Nothing Settles Today",
        "body": "Jupiter is expanding your field of perception. Every option opens two more. Your system is absorbing faster than it can filter. The paralysis isn't in you—it's in the volume of incoming data."
    },
    "start_stop_restart": {
        "title": "Why Today Stalls Momentum",
        "body": "The Moon is void-of-course right now. Actions started during this window tend to stall or need restarting. This isn't personal—it's literally a dead zone for follow-through."
    },
    "almost_act": {
        "title": "Why Today Keeps You at the Edge",
        "body": "Saturn is aspecting your action planets. Every time you reach forward, something pulls you back for one more check. Saturn is asking: 'Are you actually ready for what happens next?'"
    },
    "action_delay_loop": {
        "title": "Why Today Says 'Not Yet'",
        "body": "Mars is in a slow sign and squared by Saturn. The drive to act is there, but the timing keeps saying 'not yet.' The window for clean action hasn't opened."
    },
    "force_clarity_fail": {
        "title": "Why Today Dissolves Answers",
        "body": "Mercury is conjunct Neptune. The harder you push for clarity, the more it dissolves. This transit dissolves false certainty before real understanding arrives."
    },
    "think_loop": {
        "title": "Why Today Won't Let You Stop Thinking",
        "body": "Mercury is in a tight aspect to Pluto. Thoughts go deep, then deeper, then circle back. You're caught in a transit that demands you see what's underneath."
    },
    "check_recheck": {
        "title": "Why Today Moves the Threshold",
        "body": "The Moon is in Virgo, activating the part of you that double-checks everything. Verification doesn't satisfy because the transit keeps moving the threshold for 'enough.' It passes tomorrow."
    },
    "direction_shift": {
        "title": "Why Today Keeps Rewriting the Plan",
        "body": "Uranus is active in your chart today. Each new input rewrites the previous plan. The instability isn't in your character—it's in a transit that literally specializes in sudden pivots."
    },
    "restless_pivot": {
        "title": "Why Today Won't Let You Settle",
        "body": "The Moon is making multiple hard aspects—square, opposition, square again. Every few hours, your internal state shifts. You're being moved by rapid lunar transits."
    },
    "forward_backward": {
        "title": "Why Today Reverses Progress",
        "body": "Mercury is stationing retrograde (or just stationed direct). Forward motion hits review mode. Two steps forward, one step back isn't failure—it's the literal signature of this transit period."
    },
    "almost_done": {
        "title": "Why Today Blocks the Finish",
        "body": "Saturn is aspecting your completion planets. The last 10% requires more than the first 90%. This transit demands you earn the ending."
    },
    "hold_open": {
        "title": "Why Today Resists Closure",
        "body": "Neptune is active today, blurring boundaries between done and not-done. Closure feels like loss of possibility. This transit makes endings feel premature."
    },
    "finish_unfinish": {
        "title": "Why Today Reopens What's Done",
        "body": "Mercury retrograde (or its shadow) is activating revision. What you finished keeps reopening because the transit insists on one more pass. Completion will stick once Mercury clears this zone."
    },
    "react_regret": {
        "title": "Why Today Moves You Too Fast",
        "body": "Mars is conjunct or square your natal Mercury. Your reaction speed is outpacing your processing speed. The impulse arrives before the thought completes. This gap closes when Mars moves on."
    },
    "feel_before_think": {
        "title": "Why Today Puts Feeling First",
        "body": "The Moon is making a hard aspect to Mercury. Emotional data is reaching you faster than mental data. You're not being irrational—you're receiving information in the wrong order."
    },
    "snap_then_soften": {
        "title": "Why Today Makes You Sharp First",
        "body": "Mars is square Venus. Assertion comes out harder than intended because tenderness isn't available in the same moment. The softening follows as Venus catches up. The friction is temporary."
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
# HUMAN DESIGN MECHANISM EXPLANATIONS
# Maps pattern_id → where this pattern comes from in the person's system
#
# RULES:
# - Must reference specific HD mechanics (centers, channels, authority type)
# - Must answer: "Why does this pattern happen in my system?"
# - NO banned words: energy, alignment, growth, transformation, awareness
# - Must describe the MECHANISM, not the whole person
# - Must NOT create a new daily truth or compete with Keystone
# =============================================================================

HUMAN_DESIGN_MECHANISM_EXPLANATIONS = {
    "decision_switch_loop": {
        "title": "How Your System Cycles Through Options",
        "body": "When you try to land on something, your system routes it through multiple centers. Head wants certainty. Ajna wants logic. Solar Plexus wants emotional clarity. They don't sync at the same speed—so you cycle."
    },
    "decide_then_undo": {
        "title": "How Your System Overrides Itself",
        "body": "When you commit, your fast-response mechanism fires first. Then a slower center catches up and says 'wait.' The undo isn't flip-flopping—it's a two-stage verification system built into your wiring."
    },
    "endless_options": {
        "title": "How Your System Generates More Than It Can Filter",
        "body": "When you consider options, your Head Center generates possibilities faster than your Authority can filter. Each option triggers three more. The paralysis is an overactive conceptual system outpacing your decision mechanism."
    },
    "start_stop_restart": {
        "title": "How Your System Checks Mid-Process",
        "body": "When you start something, your Sacral says 'yes.' Mid-process, it needs to check again. The stopping isn't lack of commitment—it's your mechanism requiring re-confirmation to continue."
    },
    "almost_act": {
        "title": "How Your System Pauses Before Action",
        "body": "When you reach for action, your Spleen or Solar Plexus sends a last-second check signal. The hesitation isn't fear—it's protective circuitry built into your design."
    },
    "action_delay_loop": {
        "title": "How Your System Slows the Mental Rush",
        "body": "When you plan to act, your head moves immediately. Your body needs longer. The delay isn't procrastination—it's a mismatch between mental speed and your Authority's timing requirements."
    },
    "force_clarity_fail": {
        "title": "How Your System Resists Forced Answers",
        "body": "When you push for clarity, your Ajna analyzes—but your Authority operates on its own timeline. Pushing harder creates static, not signal. Your mechanism requires patience your mind resists."
    },
    "think_loop": {
        "title": "How Your System Processes Deeply",
        "body": "When you think, your defined Head Center generates questions, then questions the answers. The loop isn't overthinking—it's a pressure system designed to process deeply, not quickly."
    },
    "check_recheck": {
        "title": "How Your System Amplifies Uncertainty",
        "body": "When you check, your undefined center absorbs doubt from the environment and magnifies it. The rechecking isn't paranoia—it's an open center looking for stability it can't generate on its own."
    },
    "direction_shift": {
        "title": "How Your System Updates in Real-Time",
        "body": "When you set a direction, your G Center or Spleen keeps receiving new orientation data. Each input recalibrates. The shifting isn't confusion—it's a navigation system that updates continuously."
    },
    "restless_pivot": {
        "title": "How Your System Seeks Movement",
        "body": "When you try to settle, your defined motor centers create pressure. Stillness doesn't satisfy them. The restlessness isn't anxiety—your mechanism is built to move, not stay still."
    },
    "forward_backward": {
        "title": "How Your System Integrates in Waves",
        "body": "When you move forward, another center triggers a review signal. The backward step isn't regression—it's your system's natural integration rhythm. Two forward, one back is your pattern."
    },
    "almost_done": {
        "title": "How Your System Quality-Checks the Ending",
        "body": "When you near completion, your Throat or Solar Plexus sends a pause signal. The stall isn't resistance—it's a quality-control checkpoint asking: 'Are we actually ready to close this?'"
    },
    "hold_open": {
        "title": "How Your System Values Optionality",
        "body": "When you could close something, your design processes better with options than finality. Closing triggers loss signals. The avoidance isn't fear—it's a mechanism that values possibility."
    },
    "finish_unfinish": {
        "title": "How Your System Signals 'Not Actually Done'",
        "body": "When you finish mentally, your body hasn't agreed yet. The reopening isn't perfectionism—it's your system signaling that actual completion criteria weren't met."
    },
    "react_regret": {
        "title": "How Your System Responds Before Processing",
        "body": "When something happens, your Sacral or Solar Plexus responds before your Ajna can evaluate. The regret isn't impulsivity—it's a timing gap between reaction and understanding built into your design."
    },
    "feel_before_think": {
        "title": "How Your System Prioritizes Emotional Data",
        "body": "When you encounter something, your defined Solar Plexus processes ahead of your mental centers. Feeling is your first data point. The sequencing isn't irrational—it's how you're built."
    },
    "snap_then_soften": {
        "title": "How Your System Protects Before It Softens",
        "body": "When you respond, your Spleen or Will pushes out a protective edge first. Vulnerability follows once safety is established. The snap isn't aggression—it's a defense mechanism that fires before your heart engages."
    },
}


def generate_human_design_keystone_explanation(
    keystone_pattern_id: str,
    keystone_label: str,
    keystone_sequence: list,
    hd_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Human Design's explanation of WHERE this Keystone Pattern comes from.
    
    Role: MECHANISM
    Question answered: "Why does this pattern happen in my system?"
    
    Returns the Lens Framing Contract:
    {
        "keystone_pattern_id": "...",
        "lens_role": "mechanism",
        "lens_explanation_title": "...",
        "lens_explanation_body": "...",
        "supports_keystone": true
    }
    """
    
    # Get the pre-written explanation for this pattern
    explanation = HUMAN_DESIGN_MECHANISM_EXPLANATIONS.get(keystone_pattern_id)
    
    if explanation:
        return {
            "keystone_pattern_id": keystone_pattern_id,
            "keystone_label": keystone_label,
            "keystone_sequence": keystone_sequence,
            "lens_role": LensRole.MECHANISM.value,
            "lens_explanation_title": explanation["title"],
            "lens_explanation_body": explanation["body"],
            "supports_keystone": True
        }
    
    # Fallback if pattern not in library
    logger.warning(f"[KeystoneExplanation] No HD explanation for pattern: {keystone_pattern_id}")
    return {
        "keystone_pattern_id": keystone_pattern_id,
        "keystone_label": keystone_label,
        "keystone_sequence": keystone_sequence,
        "lens_role": LensRole.MECHANISM.value,
        "lens_explanation_title": "Where This Pattern Lives In Your Design",
        "lens_explanation_body": "This behavioral loop originates from specific centers and channels in your Human Design. Your system processes this way by design, not by choice.",
        "supports_keystone": True
    }


# =============================================================================
# ENNEAGRAM REPETITION LOOP EXPLANATIONS
# Maps pattern_id → why this pattern keeps repeating
#
# RULES:
# - Must explain the LOOP, not the identity
# - Must answer: "Why do I keep repeating this pattern?"
# - Must reference self-protective reaction and recurring tendency
# - NO banned words: energy, alignment, growth, transformation, awareness
# - Must NOT become generic type description
# - Must NOT sound like "who you are" - must sound like "why this repeats"
# =============================================================================

ENNEAGRAM_REPETITION_EXPLANATIONS = {
    "decision_switch_loop": {
        "title": "Why You Won't Let Yourself Land",
        "body": "Switching protects you from the wrong choice. If you never land, you never fail. The loop repeats because certainty feels dangerous. So you keep options open, rewrite the draft, check one more time. It's a defense against regret."
    },
    "decide_then_undo": {
        "title": "Why You Keep the Exit Open",
        "body": "Reversing protects you from being locked in. Commitment feels like closing a door you might need. So you say yes, feel trapped, then undo it to breathe. The loop repeats because finality triggers something that needs an escape hatch."
    },
    "endless_options": {
        "title": "Why You Won't Narrow Down",
        "body": "More options feel safer. If you keep looking, maybe you'll find the perfect one. The loop repeats because choosing means losing the others. Paralysis isn't weakness—it's a refusal to grieve what you'd give up."
    },
    "start_stop_restart": {
        "title": "Why You Keep Resetting",
        "body": "Stopping protects you from what happens if you finish. Midway, the stakes get real. The loop repeats because completion carries weight you're not ready to hold. Starting over is lighter than finishing."
    },
    "almost_act": {
        "title": "Why You Stay at the Edge",
        "body": "Hesitation protects you from being seen acting. Moving forward means committing publicly. The loop repeats because action makes you visible, and visibility makes you vulnerable. The edge feels safer than crossing."
    },
    "action_delay_loop": {
        "title": "Why You Keep Pushing It Forward",
        "body": "Delaying protects you from the friction of now. The future version of you seems more ready. The loop repeats because that version never arrives—avoiding today is the point, not the problem."
    },
    "force_clarity_fail": {
        "title": "Why You Keep Searching Harder",
        "body": "Pushing protects you from sitting with not-knowing. The loop repeats because the answer you want doesn't exist yet—forcing it creates more confusion. The real fear isn't the question. It's the silence."
    },
    "think_loop": {
        "title": "Why You Keep Circling Back",
        "body": "Thinking protects you from feeling. The loop repeats because stopping feels like giving up. So you keep circling, hoping the next pass will click. It won't. But stopping feels worse."
    },
    "check_recheck": {
        "title": "Why You Don't Trust the First Look",
        "body": "Checking protects you from missing something. The loop repeats because trust doesn't stick. Each verification fades quickly. You're not looking for new information—you're looking for certainty checking can't give."
    },
    "direction_shift": {
        "title": "Why You Keep Pivoting",
        "body": "Shifting protects you from being wrong for too long. The loop repeats because staying the course requires tolerating doubt—and doubt feels like failure. So you pivot, hoping the next direction feels certain. It doesn't."
    },
    "restless_pivot": {
        "title": "Why Staying Put Feels Wrong",
        "body": "Moving protects you from feeling stuck. The loop repeats because rest feels like stagnation. So you keep pivoting—not toward something, but away from the discomfort of standing still."
    },
    "forward_backward": {
        "title": "Why You Retreat From Progress",
        "body": "Retreating protects you from exposure. Progress makes you visible. Regression lets you stay hidden. The loop repeats because advancement triggers fear of being seen or judged. Going backward is a return to safety."
    },
    "almost_done": {
        "title": "Why You Stop at 90%",
        "body": "Stopping short protects you from what happens after. Finishing means facing judgment. The loop repeats because incompleteness is safe—it can't be evaluated yet. 100% feels too exposed."
    },
    "hold_open": {
        "title": "Why You Won't Close It",
        "body": "Keeping it open protects you from grief. Finishing means this version is final. The loop repeats because endings feel like loss. So you hold it open, just in case."
    },
    "finish_unfinish": {
        "title": "Why Done Keeps Reopening",
        "body": "Reopening protects you from living with the finished version. The loop repeats because closure triggers doubt. The real fear isn't imperfection—it's finality."
    },
    "react_regret": {
        "title": "Why You Move Before You're Ready",
        "body": "Reacting fast protects you from the discomfort of waiting. The loop repeats because the impulse to act is stronger than the fear of being wrong. You move, regret, move again."
    },
    "feel_before_think": {
        "title": "Why Feeling Leads",
        "body": "Feeling first protects you from overthinking into paralysis. The loop repeats because your emotional system trusts itself more than logic. The feeling isn't irrational—it's faster. Understanding comes late."
    },
    "snap_then_soften": {
        "title": "Why You Come In Sharp",
        "body": "Sharpness protects you from being hurt first. The softening that follows is the real you—but you can't lead with it. The loop repeats because vulnerability without armor feels dangerous."
    },
}


def generate_enneagram_keystone_explanation(
    keystone_pattern_id: str,
    keystone_label: str,
    keystone_sequence: list,
    enneagram_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Enneagram's explanation of WHY this Keystone Pattern keeps repeating.
    
    Role: REPETITION_LOOP
    Question answered: "Why do I keep repeating this pattern?"
    
    Returns the Lens Framing Contract:
    {
        "keystone_pattern_id": "...",
        "lens_role": "repetition_loop",
        "lens_explanation_title": "...",
        "lens_explanation_body": "...",
        "supports_keystone": true
    }
    """
    
    # Get the pre-written explanation for this pattern
    explanation = ENNEAGRAM_REPETITION_EXPLANATIONS.get(keystone_pattern_id)
    
    if explanation:
        return {
            "keystone_pattern_id": keystone_pattern_id,
            "keystone_label": keystone_label,
            "keystone_sequence": keystone_sequence,
            "lens_role": LensRole.REPETITION_LOOP.value,
            "lens_explanation_title": explanation["title"],
            "lens_explanation_body": explanation["body"],
            "supports_keystone": True
        }
    
    # Fallback if pattern not in library
    logger.warning(f"[KeystoneExplanation] No Enneagram explanation for pattern: {keystone_pattern_id}")
    return {
        "keystone_pattern_id": keystone_pattern_id,
        "keystone_label": keystone_label,
        "keystone_sequence": keystone_sequence,
        "lens_role": LensRole.REPETITION_LOOP.value,
        "lens_explanation_title": "Why This Pattern Keeps Returning",
        "lens_explanation_body": "This loop serves a protective function. It repeats because some part of you believes it keeps you safe. Understanding the protection reveals the pattern.",
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
    - Astrology: doesn't mention timing language
    - Human Design: doesn't mention mechanism language
    
    Returns validation result with pass/fail status.
    """
    
    actual_pattern_id = lens_explanation.get("keystone_pattern_id")
    supports_keystone = lens_explanation.get("supports_keystone", False)
    explanation_body = lens_explanation.get("lens_explanation_body", "").lower()
    lens_role = lens_explanation.get("lens_role", "")
    
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
    
    # Check 4: Lens-specific language requirements
    if lens_role == LensRole.TIMING_TRIGGER.value:
        # Astrology must contain timing language
        timing_indicators = [
            "today", "right now", "this transit", "currently", 
            "mercury", "mars", "venus", "saturn", "jupiter", "uranus", "neptune", "pluto",
            "moon", "sun", "retrograde", "square", "conjunct", "aspect",
            "this window", "this period", "passes", "moves on", "clears"
        ]
        has_timing = any(indicator in explanation_body for indicator in timing_indicators)
        
        if not has_timing:
            logger.warning(f"[LensValidation] No timing language found in astrology explanation")
            return {
                "valid": False,
                "error": "missing_timing_language",
                "pattern_id": actual_pattern_id
            }
    
    elif lens_role == LensRole.MECHANISM.value:
        # Human Design must contain mechanism language
        mechanism_indicators = [
            "center", "centers", "channel", "channels", "authority", "type",
            "sacral", "solar plexus", "spleen", "head", "ajna", "throat", "g center",
            "heart", "root", "defined", "undefined", "open", "generator", "projector",
            "manifestor", "reflector", "system", "design", "wiring", "mechanism",
            "response", "invitation", "inform", "wait"
        ]
        has_mechanism = any(indicator in explanation_body for indicator in mechanism_indicators)
        
        if not has_mechanism:
            logger.warning(f"[LensValidation] No mechanism language found in HD explanation")
            return {
                "valid": False,
                "error": "missing_mechanism_language",
                "pattern_id": actual_pattern_id
            }
    
    elif lens_role == LensRole.REPETITION_LOOP.value:
        # Enneagram must contain repetition/loop language
        repetition_indicators = [
            "loop", "repeats", "repeat", "keeps", "again", "cycle", "cycling",
            "protects", "protection", "protective", "defense", "defending",
            "pattern", "recurring", "returns", "returning", "back",
            "fear", "avoid", "avoiding", "safety", "safe", "danger", "dangerous",
            "because", "so you", "that's why", "the real"
        ]
        has_repetition = any(indicator in explanation_body for indicator in repetition_indicators)
        
        if not has_repetition:
            logger.warning(f"[LensValidation] No repetition language found in Enneagram explanation")
            return {
                "valid": False,
                "error": "missing_repetition_language",
                "pattern_id": actual_pattern_id
            }
    
    return {
        "valid": True,
        "pattern_id": actual_pattern_id,
        "lens_role": lens_role
    }
