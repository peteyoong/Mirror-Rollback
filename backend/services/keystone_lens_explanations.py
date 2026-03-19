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
        "title": "Where The Switching Comes From",
        "body": "Your system processes decisions through multiple centers before landing. The Head and Ajna want certainty. The Solar Plexus wants emotional clarity. When they don't sync, you cycle through options. This isn't indecision—it's your mechanism requiring more passes before commitment."
    },
    "decide_then_undo": {
        "title": "Why You Reverse After Committing",
        "body": "Your design has a fast response mechanism paired with a slower emotional wave. The initial 'yes' comes from one center. Then another center catches up and overrides. The undo isn't flip-flopping—it's a two-stage verification system built into your wiring."
    },
    "endless_options": {
        "title": "Why Options Keep Multiplying",
        "body": "Your Head Center generates possibilities faster than your Authority can filter them. Each option triggers three more considerations. The paralysis isn't weakness—it's an overactive conceptual system outpacing your decision mechanism."
    },
    "start_stop_restart": {
        "title": "Why Momentum Breaks",
        "body": "Your Sacral responds in bursts, not sustained streams. It says 'yes' to begin, then needs to check again mid-process. The stopping isn't lack of commitment—it's your generator mechanism requiring re-confirmation to continue."
    },
    "almost_act": {
        "title": "Why You Pull Back at the Edge",
        "body": "Your system has a built-in pause before action. The Spleen or Solar Plexus sends a last-second check signal. You get to the threshold, then something in your design says 'wait.' The hesitation is protective circuitry, not fear."
    },
    "action_delay_loop": {
        "title": "Why Doing Gets Postponed",
        "body": "Your Authority requires time that your mind doesn't want to give. The head plans immediately. The body needs to process longer. The delay isn't procrastination—it's a mismatch between your mental speed and your decision mechanism's timing requirements."
    },
    "force_clarity_fail": {
        "title": "Why Clarity Won't Arrive on Demand",
        "body": "Your design doesn't produce clarity through force. The Ajna analyzes, but your Authority operates on its own timeline. Pushing harder creates static, not signal. Your mechanism requires patience that your mind resists."
    },
    "think_loop": {
        "title": "Why Thoughts Keep Circling",
        "body": "Your Head Center is defined and constantly active. It generates questions, then questions the answers. The loop isn't overthinking—it's a pressure system designed to process deeply, not quickly. Completion comes from the body, not the mind."
    },
    "check_recheck": {
        "title": "Why Verification Never Satisfies",
        "body": "Your system has an undefined center that amplifies uncertainty. It absorbs doubt from the environment and magnifies it internally. The checking isn't paranoia—it's an open center looking for stability it can't generate on its own."
    },
    "direction_shift": {
        "title": "Why Direction Keeps Changing",
        "body": "Your G Center or Spleen receives new orientation data continuously. Each input recalibrates your sense of direction. The shifting isn't confusion—it's a navigation system that updates in real-time rather than locking in."
    },
    "restless_pivot": {
        "title": "Why Settling Feels Impossible",
        "body": "Your design has motor energy that seeks movement. Stillness creates pressure in your system. The restlessness isn't anxiety—it's defined motor centers that aren't satisfied with static states. Your mechanism is built to move."
    },
    "forward_backward": {
        "title": "Why Progress Reverses",
        "body": "Your Authority operates in waves, not straight lines. Forward movement triggers a review signal from another center. The backward step isn't regression—it's your system's natural integration rhythm. Two steps forward, one step back is your pattern, not a flaw."
    },
    "almost_done": {
        "title": "Why Finishing Stalls",
        "body": "Your system has a completion checkpoint that activates near the end. The Throat or Solar Plexus sends a pause signal before the final step. The stall isn't resistance—it's a quality-control mechanism asking: 'Are we actually ready to close this?'"
    },
    "hold_open": {
        "title": "Why Closure Gets Avoided",
        "body": "Your design processes better with options than with finality. Closing a loop triggers loss signals in your system. The avoidance isn't fear of commitment—it's a mechanism that values possibility over completion."
    },
    "finish_unfinish": {
        "title": "Why Done Keeps Reopening",
        "body": "Your Authority doesn't recognize 'done' the way your mind does. The mental 'complete' happens before the body agrees. The reopening isn't perfectionism—it's your system signaling that the actual completion criteria weren't met."
    },
    "react_regret": {
        "title": "Why Response Outruns Processing",
        "body": "Your Sacral or Solar Plexus responds before your Ajna can evaluate. The response mechanism is faster than the analysis mechanism. The regret isn't impulsivity—it's a timing gap between reaction and understanding that's built into your design."
    },
    "feel_before_think": {
        "title": "Why Emotion Arrives First",
        "body": "Your Solar Plexus is defined and processes ahead of your mental centers. Feeling is your first data point, not an afterthought. The sequencing isn't irrationality—it's your system prioritizing emotional intelligence over mental analysis."
    },
    "snap_then_soften": {
        "title": "Why Sharpness Comes Before Tenderness",
        "body": "Your system has a protective edge that activates before your softer response. The Spleen or defined Will pushes out first. Vulnerability follows once safety is established. The snap isn't aggression—it's a defense mechanism that fires before your heart center engages."
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
        "title": "Why You Keep Cycling Through Options",
        "body": "Switching protects you from the wrong choice. If you never land, you never fail. The loop repeats because certainty feels dangerous—what if you pick wrong? So you keep the options open, rewrite the draft, check one more time. The switching isn't indecision. It's a defense against regret that never lets you rest."
    },
    "decide_then_undo": {
        "title": "Why You Take It Back",
        "body": "The reversal protects you from being locked in. Committing feels like closing a door you might need. So you say yes, then feel trapped, then undo it to breathe again. The loop repeats because finality triggers something in you that needs an exit. It's not about the decision—it's about keeping the escape hatch open."
    },
    "endless_options": {
        "title": "Why Nothing Ever Feels Like Enough",
        "body": "More options feel like more safety. If you keep looking, maybe you'll find the perfect one that doesn't require sacrifice. The loop repeats because choosing means losing the others. So you keep them all in view, never narrowing, because narrowing feels like loss. The paralysis isn't weakness—it's a refusal to grieve what you'd give up."
    },
    "start_stop_restart": {
        "title": "Why You Keep Stalling Out",
        "body": "Stopping protects you from what happens if you finish. Starting feels safe—full of possibility. But midway, the stakes get real. So you pause, reset, begin again where it still feels open. The loop repeats because completion carries weight you're not ready to hold. Starting over is lighter than finishing."
    },
    "almost_act": {
        "title": "Why You Pull Back at the Edge",
        "body": "The hesitation protects you from being seen acting. Moving forward means committing publicly. Pulling back means you can still change your mind. The loop repeats because action makes you visible, and visibility makes you vulnerable. Staying at the edge feels safer than crossing it."
    },
    "action_delay_loop": {
        "title": "Why Tomorrow Always Feels Safer",
        "body": "Delaying protects you from the discomfort of now. Doing it later means you don't have to feel the friction today. The loop repeats because the future version of you seems more capable, more ready. But that version never arrives—because avoiding today is the point, not the problem."
    },
    "force_clarity_fail": {
        "title": "Why Answers Keep Slipping Away",
        "body": "Pushing for clarity protects you from sitting with not-knowing. Uncertainty feels unbearable, so you search harder. But the loop repeats because the answer you want doesn't exist yet—and forcing it creates more confusion. The real fear isn't the question. It's the silence while you wait."
    },
    "think_loop": {
        "title": "Why Your Mind Won't Stop",
        "body": "Thinking protects you from feeling. As long as you're analyzing, you don't have to land in the discomfort of not understanding. The loop repeats because stopping feels like giving up, and giving up feels like failure. So you keep circling, hoping the next pass will finally make it click. It won't. But stopping feels worse."
    },
    "check_recheck": {
        "title": "Why Once Is Never Enough",
        "body": "Checking protects you from the fear of missing something. What if you overlooked it? What if it changed? The loop repeats because trust doesn't stick. Each verification fades quickly, and the doubt returns. You're not looking for new information—you're looking for the certainty that checking can never give you."
    },
    "direction_shift": {
        "title": "Why You Keep Changing Course",
        "body": "Shifting protects you from being wrong for too long. If you change direction, maybe you'll find the right one before it's too late. The loop repeats because staying the course requires tolerating doubt—and doubt feels like failure. So you pivot, hoping the next direction will feel more certain. It doesn't, but you keep trying."
    },
    "restless_pivot": {
        "title": "Why Stillness Feels Like Danger",
        "body": "Moving protects you from feeling stuck. Staying in one place too long makes you anxious—what if you're missing something better? The loop repeats because rest feels like stagnation, and stagnation feels like death. So you keep pivoting, not toward something, but away from the discomfort of standing still."
    },
    "forward_backward": {
        "title": "Why You Undo Your Own Progress",
        "body": "Retreating protects you from the exposure of moving forward. Progress makes you visible. Regression lets you stay hidden. The loop repeats because advancement triggers fear of being seen, judged, or proven inadequate. Going backward isn't failure—it's a return to safety."
    },
    "almost_done": {
        "title": "Why You Can't Cross The Finish Line",
        "body": "Stopping short protects you from what happens after. Finishing means facing the next thing—or worse, facing judgment on what you made. The loop repeats because incompleteness is safe. As long as it's not done, it can't be evaluated. You stay in the 90% zone because 100% feels too exposed."
    },
    "hold_open": {
        "title": "Why You Won't Let It Close",
        "body": "Keeping it open protects you from the grief of closing. Finishing means accepting that this version is the final version. The loop repeats because endings feel like loss, and loss feels unbearable. So you hold it open, just in case, because 'just in case' feels better than 'it's done.'"
    },
    "finish_unfinish": {
        "title": "Why Done Never Stays Done",
        "body": "Reopening protects you from living with the finished version. Once it's done, you have to accept it as-is. But if you reopen it, you can still make it better—or at least delay accepting it. The loop repeats because closure triggers doubt, and doubt demands another pass. The real fear isn't imperfection—it's finality."
    },
    "react_regret": {
        "title": "Why You Move Before You Think",
        "body": "Reacting fast protects you from sitting with the discomfort of waiting. Slowness feels unbearable—something needs to happen now. The loop repeats because the impulse to act is stronger than the fear of being wrong. You move, then regret, then move again. The pattern isn't impulsivity—it's an intolerance for stillness."
    },
    "feel_before_think": {
        "title": "Why Emotion Arrives First",
        "body": "Feeling first protects you from overthinking yourself into paralysis. If you waited for logic, you might never move. The loop repeats because your emotional system trusts itself more than your mental system. The feeling isn't irrational—it's faster, and sometimes that's what you need. But it also means understanding comes late."
    },
    "snap_then_soften": {
        "title": "Why You Lead With Edge",
        "body": "The sharpness protects you from being hurt first. If you come in strong, you control the interaction. The softening that follows is the real you—but you can't lead with it. The loop repeats because vulnerability without armor feels dangerous. So you snap, then soften, because softening first feels too exposed."
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
