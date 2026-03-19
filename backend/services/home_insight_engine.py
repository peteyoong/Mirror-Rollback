"""Home Insight Engine - Phase 1 MVP

Simple structured insight generation for Home Screen.
Phase 1: Transform existing data into new structured format.
v1.5: Day-Class Hero Framing - titles/copy selected by day classification
v1.7: ELIMINATE GENERIC FALLBACK - Signal Dominance Rule
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import hashlib
import re

logger = logging.getLogger(__name__)


# =============================================================================
# v1.7: BANNED GENERIC PATTERNS - These MUST NEVER appear in output
# =============================================================================

BANNED_PATTERNS = [
    r"something is present",
    r"worth paying attention",
    r"you may notice",
    r"something is shifting(?!\s*under)",  # Allow "shifting under your feet" but not vague "shifting"
    r"something is here",
    r"there's something here",
    r"pay attention to what",
    r"notice what comes up",
    r"something wants your attention",
    r"there's a quality to today",
    r"something may be emerging",
    r"you might feel something",
    r"notice what you're noticing",
    r"what's present today",
    r"something is asking",
    r"be open to what",
    r"stay curious about",
    r"allow yourself to notice",
]

# Compile patterns for efficiency
BANNED_PATTERN_REGEX = re.compile(
    '|'.join(BANNED_PATTERNS), 
    re.IGNORECASE
)


def extract_key_concepts(text: str) -> set:
    """
    Extract key concepts from text for semantic comparison.
    Used to detect if bridge duplicates body.
    """
    if not text:
        return set()
    
    text_lower = text.lower()
    
    # Key concept words to track
    concepts = set()
    
    concept_markers = [
        ("decide", "decision"), ("ready", "readiness"), ("pressure", "pressure"),
        ("clarity", "clarity"), ("relief", "relief"), ("discomfort", "discomfort"),
        ("urgency", "urgency"), ("settle", "settling"), ("forming", "formation"),
        ("conclusion", "conclusion"), ("force", "forcing"), ("wait", "waiting"),
        ("finish", "completion"), ("lock", "locking"), ("grip", "gripping"),
        ("done", "completion"), ("complete", "completion"), ("incomplete", "incompleteness"),
        ("shift", "shifting"), ("turn", "turning"), ("change", "changing"),
    ]
    
    for word, concept in concept_markers:
        if word in text_lower:
            concepts.add(concept)
    
    return concepts


def validate_bridge_additive(body: str, bridge: str) -> Dict[str, Any]:
    """
    v1.8: Validate that bridge adds NEW layer, not semantic duplication.
    
    Bridge must:
    - Add new insight (not repeat body concepts)
    - Land as recognition/truth
    - Be distinct enough from body
    
    Returns: {"is_additive": bool, "overlap_concepts": list, "recommendation": str}
    """
    if not bridge or not body:
        return {"is_additive": True, "overlap_concepts": [], "recommendation": None}
    
    body_concepts = extract_key_concepts(body)
    bridge_concepts = extract_key_concepts(bridge)
    
    # Find overlapping concepts
    overlap = body_concepts.intersection(bridge_concepts)
    
    # If more than 50% of bridge concepts overlap with body, it's repetitive
    if bridge_concepts and len(overlap) > len(bridge_concepts) * 0.5:
        return {
            "is_additive": False,
            "overlap_concepts": list(overlap),
            "recommendation": "Bridge repeats body concepts. Select different bridge.",
        }
    
    # Check for direct phrase duplication
    body_lower = body.lower()
    bridge_lower = bridge.lower()
    
    # Extract key phrases (3+ word sequences) from body
    body_words = body_lower.split()
    
    for i in range(len(body_words) - 2):
        phrase = ' '.join(body_words[i:i+3])
        if phrase in bridge_lower and len(phrase) > 10:
            return {
                "is_additive": False,
                "overlap_concepts": [phrase],
                "recommendation": f"Bridge contains phrase from body: '{phrase}'",
            }
    
    return {"is_additive": True, "overlap_concepts": list(overlap), "recommendation": None}


def is_generic_copy(text: str, is_title: bool = False) -> bool:
    """
    Check if text contains banned generic patterns.
    Returns True if text is generic and should be rejected.
    
    v1.7: Titles have different validation - strong declarative titles are allowed.
    """
    if not text:
        return True
    
    # Check against banned patterns
    if BANNED_PATTERN_REGEX.search(text):
        return True
    
    # Titles have different validation rules
    if is_title:
        # Strong declarative titles are NOT generic
        strong_title_patterns = [
            "not a normal day",
            "don't lock",
            "turning",
            "shifting",
            "moving",
            "ready before",
            "grip",
            "know",
            "choice",
            "coming to a head",
            "threshold",
            "off but",
            "been here before",
            "shape again",
            "energy without",
            "moved",
            "spent",
            "wants to be said",
            "waiting for",
            "pattern",
        ]
        if any(pattern in text.lower() for pattern in strong_title_patterns):
            return False
        
        # Short titles are OK if they're declarative
        if len(text) < 40:
            return False
    
    # Additional check for body text: if text is too short and vague
    if len(text) < 50 and not any(word in text.lower() for word in [
        "pressure", "decide", "urge", "force", "trap", "cost", "mistake",
        "relief", "discomfort", "incomplete", "unfinished", "tension",
        "grip", "control", "waiting", "stuck", "frustrated", "ready",
        "want", "feel", "know", "surface", "forming", "shifting"
    ]):
        return True
    
    return False


def validate_hero_copy(title: str, body: str, bridge: str, day_class: str) -> Dict[str, Any]:
    """
    Validate hero copy against quality requirements.
    
    v1.7 REQUIREMENTS:
    1. Must include a real human tension
    2. Must include a wrong move / trap
    3. Must have a felt experience
    4. NO generic fallback allowed
    
    Returns: {"valid": bool, "issues": list, "severity": str}
    """
    issues = []
    
    # Check title - use is_title=True for proper title validation
    if is_generic_copy(title, is_title=True):
        issues.append(f"TITLE_GENERIC: '{title}' is too vague")
    
    # Check body - body needs full validation
    if is_generic_copy(body, is_title=False):
        issues.append("BODY_GENERIC: Body copy lacks tension or specificity")
    
    # Check for required elements in body
    combined = f"{title} {body} {bridge}".lower()
    
    tension_words = ["pressure", "urge", "pull", "push", "tension", "discomfort", "uncomfortable", "tight", "want", "need", "feel"]
    trap_words = ["trap", "mistake", "wrong", "cost", "risk", "danger", "temptation", "avoid", "don't", "wait", "stop"]
    felt_words = ["feel", "sense", "notice", "experience", "uncomfortable", "heavy", "light", "relief", "ready", "part of you"]
    
    has_tension = any(word in combined for word in tension_words)
    has_trap = any(word in combined for word in trap_words)
    has_felt = any(word in combined for word in felt_words)
    
    # For phase_shift, we REQUIRE tension
    if not has_tension and day_class in ["phase_shift", "cycle_event"]:
        issues.append("MISSING_TENSION: No tension language found in copy")
    
    # Only flag missing trap if ALL three are missing
    if not has_trap and not has_tension and not has_felt:
        issues.append("MISSING_TRAP: No wrong-move/trap language found")
    
    if not has_felt and not has_tension:
        issues.append("MISSING_FELT: No felt-experience language found")
    
    # Determine severity - be less aggressive
    if any("BODY_GENERIC" in i for i in issues):
        severity = "BLOCK"  # Only block if body is generic
    elif len(issues) >= 3:
        severity = "REWRITE"  # Should try to fix
    elif issues:
        severity = "WARNING"  # Log but allow
    else:
        severity = "PASS"
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "severity": severity,
        "has_tension": has_tension,
        "has_trap": has_trap,
        "has_felt": has_felt,
    }


# =============================================================================
# DAY-CLASS HERO FRAMING (v2.0 - Anti-Cleverness Guardrail)
# =============================================================================
# v2.0: CLARITY over cleverness. No metaphors. No abstraction.
# Every line: immediately understandable, personally recognizable
# Test: "yeah... that's exactly what I'm doing"

DAY_CLASS_FRAMINGS = {
    "phase_shift": {
        "tone": "interruptive",
        "description": "Today is not normal - transition / unfinished / turning point",
        "title_options": [
            "This Is Not a Normal Day",
            "Don't Lock It In Yet",
            "Something Is Turning",
            "What's Shifting Hasn't Landed",
            "You're In the Middle of the Change",
            "The Ground Is Still Moving",
            "Not Yet",
            "It's Still Becoming",
        ],
        # v2.0: Direct psychological statements, observable behavior, felt experience
        "body_templates": [
            "You want to decide just to stop feeling this way. That's not clarity. That's wanting relief.",
            "You can feel how hard you're trying to make this make sense. It doesn't yet.",
            "You keep checking if it's ready. It's not. You already know that.",
            "Part of you wants to force an answer just so you can stop thinking about it.",
            "You're trying to finish something that isn't done. You can feel the strain.",
        ],
        # v2.0: Simple, direct bridges - no metaphors
        "bridge_templates": [
            "You want it over more than you want it right.",
            "The rush you feel isn't a sign to act.",
            "You're pushing because waiting is uncomfortable.",
            "You already know it's not ready.",
            "The answer isn't there yet.",
        ],
    },
    "cycle_event": {
        "tone": "directional",
        "description": "Notable day - threshold / culmination / opening",
        "title_options": [
            "Something Is Coming to a Head",
            "A Door Is Opening",
            "The Pattern Is Getting Louder",
            "This Wants Your Attention",
            "A Threshold",
            "Something Is Culminating",
            "The Cycle Is Turning",
            "Pay Attention Today",
        ],
        # v2.0: Direct, recognizable
        "body_templates": [
            "Something feels different today. You're not imagining it. Pay attention.",
            "You keep noticing the same thing. That's not random. That's a signal.",
            "Today feels heavier than usual. You're right. It is.",
            "Something wants your attention. You've been avoiding it.",
        ],
        # v2.0: Direct bridges
        "bridge_templates": [
            "You'll wish you'd paid attention.",
            "This won't feel this way tomorrow.",
            "You already know what this is about.",
            "Ignoring it won't make it go away.",
        ],
    },
    "normal_flow": {
        "tone": "subtle",
        "description": "Ordinary but meaningful - pattern recognition / psychological",
        "title_options": [
            "It's Not One Thing",
            "You've Been Here Before",
            "Something Underneath This",
            "The Same Shape Again",
            "A Familiar Pressure",
            "Part of You Knows",
            "The Pattern Returns",
        ],
        # v2.0: Direct, recognizable
        "body_templates": [
            "You're feeling something but you can't name it. You keep trying to figure it out. That's not helping.",
            "This feels familiar. You've done this before. You know how it usually ends.",
            "Part of you already knows what's going on. You're just not ready to say it.",
            "There's something you're not looking at. You can feel it pulling at you.",
        ],
        # v2.0: Direct bridges
        "bridge_templates": [
            "You've been here before.",
            "You're avoiding the obvious.",
            "Thinking harder won't help.",
            "You already know.",
        ],
    },
}

# Interaction theme to title mappings for phase_shift
PHASE_SHIFT_THEME_TITLES = {
    "reset_at_threshold": [
        "This Is Not a Normal Day",
        "Something Is Turning", 
        "Don't Lock It In Yet",
    ],
    "portal_opening": [
        "A Portal Is Open",
        "This Is Not a Normal Day",
        "Something Is Shifting Under Your Feet",
    ],
    "culmination_at_threshold": [
        "Something Is Coming to a Head",
        "A Threshold Is Crossing",
        "This Wants Your Attention",
    ],
    "destabilization_window": [
        "The Ground Is Still Moving",
        "Don't Make It Make Sense Yet",
        "You're In the Middle of the Change",
    ],
    "deep_release": [
        "Something Wants to Leave",
        "Let It Go",
        "This Is Not a Normal Day",
    ],
    "reset_at_extreme": [
        "A Reset at Peak Intensity",
        "The Ground Is Still Moving",
        "Don't Lock It In Yet",
    ],
    "peak_illumination": [
        "Everything Is Illuminated",
        "The Full Picture Is Here",
        "What You See Is Real",
    ],
    "emotional_culmination": [
        "Deep Feelings Are Surfacing",
        "Something Is Releasing",
        "Let It Move Through",
    ],
    "portal_at_threshold": [
        "A Rare Convergence",
        "This Is Not a Normal Day",
        "Multiple Forces Are Active",
    ],
    "portal_at_extreme": [
        "Portal at Peak Intensity",
        "Don't Force It",
        "Let It Move You",
    ],
    "release_at_threshold": [
        "Old Patterns Are Falling Away",
        "Deep Release at a Turning Point",
        "Let Go",
    ],
    "multiple_events_active": [
        "Multiple Forces Are Converging",
        "This Is Not a Normal Day",
        "The Ground Is Still Moving",
    ],
}


def select_hero_framing(
    day_class: str,
    transit_stack: Dict[str, Any],
    dominant_tension: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Select hero framing based on day classification.
    
    v1.5: Hero title and shape are determined by day_class FIRST,
    then modulated tension fills in the specific message.
    
    v1.7: SIGNAL DOMINANCE - phase_shift ALWAYS uses phase_shift templates.
    NO fallback to generic copy allowed.
    
    Returns:
    {
        "day_class": str,
        "hero_mode": str,
        "selected_title": str,
        "body_direction": str,
        "bridge_direction": str,
        "tone": str
    }
    """
    # Get base framing for day class
    framing = DAY_CLASS_FRAMINGS.get(day_class, DAY_CLASS_FRAMINGS["normal_flow"])
    
    # Get interaction theme for more specific title selection
    interaction_theme = transit_stack.get("interaction_theme", "")
    intensity = transit_stack.get("intensity", 0.5)
    
    # v1.7: SIGNAL DOMINANCE RULE
    # If day_class is phase_shift, ALWAYS use phase_shift framing
    # DO NOT allow override by weak signals or low confidence
    
    if day_class == "phase_shift":
        # Use theme-specific titles if available
        theme_titles = PHASE_SHIFT_THEME_TITLES.get(interaction_theme, framing["title_options"])
        title_options = theme_titles
        hero_mode = "turning_point"
        
        # FORCE phase_shift templates - no fallback
        body_options = framing["body_templates"]
        bridge_options = framing["bridge_templates"]
        
    elif day_class == "cycle_event":
        title_options = framing["title_options"]
        hero_mode = "threshold"
        body_options = framing["body_templates"]
        bridge_options = framing["bridge_templates"]
    else:
        title_options = framing["title_options"]
        hero_mode = "pattern"
        body_options = framing["body_templates"]
        bridge_options = framing["bridge_templates"]
    
    # Use date-based seed for consistent selection within a day
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    # Select title deterministically
    title_index = seed_hash % len(title_options)
    selected_title = title_options[title_index]
    
    # Select body and bridge direction from templates
    body_index = (seed_hash + 1) % len(body_options)
    bridge_index = (seed_hash + 2) % len(bridge_options)
    
    body_direction = body_options[body_index]
    bridge_direction = bridge_options[bridge_index]
    
    # v1.9: Only use modulated_copy if it's substantive (>70 chars)
    # v1.9 templates are compressed by design, so don't replace with shorter transit copy
    if dominant_tension and dominant_tension.get("modulated_copy"):
        modulated_copy = dominant_tension.get("modulated_copy", "")
        
        # Only use if it's long enough AND passes validation
        if len(modulated_copy) >= 70 and not is_generic_copy(modulated_copy):
            # Only use if it matches the day class tone
            if day_class == "phase_shift" and any(word in modulated_copy.lower() for word in 
                ["shift", "form", "shape", "decide", "land", "stable", "pressure", "force", "incomplete"]):
                body_direction = modulated_copy
                logger.info(f"[HeroFraming v1.8] Using modulated_copy ({len(modulated_copy)} chars)")
            elif day_class == "cycle_event" and any(word in modulated_copy.lower() for word in 
                ["turn", "open", "culminat", "threshold", "peak", "reveal", "weight"]):
                body_direction = modulated_copy
                logger.info(f"[HeroFraming v1.8] Using modulated_copy ({len(modulated_copy)} chars)")
        else:
            logger.info(f"[HeroFraming v1.8] Skipping short modulated_copy ({len(modulated_copy)} chars), using template")
    
    # v1.7: VALIDATION - Ensure selected copy is not generic
    validation = validate_hero_copy(selected_title, body_direction, bridge_direction, day_class)
    
    if validation["severity"] == "BLOCK":
        # Generic copy detected - force regeneration with different seed
        logger.warning(f"[HeroFraming] BLOCKED generic copy, regenerating. Issues: {validation['issues']}")
        
        # Try next options
        for offset in range(1, len(title_options)):
            alt_title_index = (title_index + offset) % len(title_options)
            alt_body_index = (body_index + offset) % len(body_options)
            alt_bridge_index = (bridge_index + offset) % len(bridge_options)
            
            alt_title = title_options[alt_title_index]
            alt_body = body_options[alt_body_index]
            alt_bridge = bridge_options[alt_bridge_index]
            
            alt_validation = validate_hero_copy(alt_title, alt_body, alt_bridge, day_class)
            if alt_validation["severity"] != "BLOCK":
                selected_title = alt_title
                body_direction = alt_body
                bridge_direction = alt_bridge
                logger.info(f"[HeroFraming] Regenerated to non-generic copy: {selected_title}")
                break
    
    logger.info(f"[HeroFraming] Day class: {day_class}, Mode: {hero_mode}, Title: {selected_title}")
    
    return {
        "day_class": day_class,
        "hero_mode": hero_mode,
        "interaction_theme": interaction_theme,
        "selected_title": selected_title,
        "body_direction": body_direction,
        "bridge_direction": bridge_direction,
        "tone": framing["tone"],
        "intensity": intensity,
        "validation": validation,
    }


def generate_day_class_hero(
    day_class: str,
    transit_stack: Dict[str, Any],
    dominant_tension: Optional[Dict[str, Any]] = None,
    pattern_key: str = "default"
) -> Dict[str, Any]:
    """
    Generate complete hero content using day-class framing.
    
    v1.7: SIGNAL DOMINANCE - phase_shift ALWAYS dominates.
    v1.8: Sharper body (2-3 sentences), ADDITIVE bridges (new layer, not repetition).
    """
    # Get hero framing based on day class
    framing = select_hero_framing(day_class, transit_stack, dominant_tension)
    
    body = framing["body_direction"]
    bridge = framing["bridge_direction"]
    
    # v2.0: Emphasis-based bridges - DIRECT & RECOGNIZABLE
    # No metaphors. Felt experience. Observable behavior.
    # Test: "yeah... that's exactly what I'm doing"
    EMPHASIS_BRIDGES_V20 = {
        "incompleteness": [
            "You already know it's not ready.",
            "You're trying to finish something that isn't done.",
            "You can feel how forced this is.",
        ],
        "instability": [
            "Nothing feels solid right now. That's real.",
            "You keep looking for something to hold onto.",
            "You can't find your footing. That's okay for now.",
        ],
        "letting_go": [
            "You're holding onto something that's already leaving.",
            "You can feel how tired you are from gripping.",
            "Part of you knows you need to let go.",
        ],
        "pressure": [
            "You want to decide just to make this feeling stop.",
            "The pressure is real. The answer it's pointing to isn't.",
            "You're rushing because waiting feels unbearable.",
        ],
        "patience": [
            "You're ready. It's not. That's the hard part.",
            "Waiting feels like falling behind. It's not.",
            "You keep checking if it's time yet. It's not.",
        ],
    }
    
    # For phase_shift, select emphasis-based bridge
    if day_class == "phase_shift" and dominant_tension:
        emphasis_list = dominant_tension.get("emphasis", [])
        
        # Find matching emphasis bridge
        for emph in emphasis_list:
            if emph in EMPHASIS_BRIDGES_V20:
                bridges = EMPHASIS_BRIDGES_V20[emph]
                # Select based on date seed
                date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
                seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
                bridge_index = seed_hash % len(bridges)
                candidate_bridge = bridges[bridge_index]
                
                # v2.0: Validate bridge is additive (not repetitive of body)
                bridge_validation = validate_bridge_additive(body, candidate_bridge)
                if bridge_validation["is_additive"]:
                    bridge = candidate_bridge
                    logger.info(f"[HeroFraming v2.0] Selected additive bridge for emphasis '{emph}'")
                else:
                    # Try next bridge option
                    for i in range(1, len(bridges)):
                        alt_bridge = bridges[(bridge_index + i) % len(bridges)]
                        alt_validation = validate_bridge_additive(body, alt_bridge)
                        if alt_validation["is_additive"]:
                            bridge = alt_bridge
                            logger.info(f"[HeroFraming v2.0] Selected alt additive bridge for '{emph}'")
                            break
                break
    
    # v2.0: Final bridge additivity check - if bridge duplicates body, select different
    bridge_check = validate_bridge_additive(body, bridge)
    if not bridge_check["is_additive"]:
        logger.warning(f"[HeroFraming v1.8] Bridge duplicates body concepts: {bridge_check['overlap_concepts']}")
        
        # Get alternative bridge from templates
        framing_templates = DAY_CLASS_FRAMINGS.get(day_class, {})
        bridge_options = framing_templates.get("bridge_templates", [])
        
        if bridge_options:
            date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
            seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
            
            for i in range(len(bridge_options)):
                alt_bridge = bridge_options[(seed_hash + i + 3) % len(bridge_options)]
                alt_check = validate_bridge_additive(body, alt_bridge)
                if alt_check["is_additive"]:
                    bridge = alt_bridge
                    logger.info(f"[HeroFraming v1.8] Replaced with additive bridge: {bridge}")
                    break
    
    # v2.0: Final validation before return
    final_validation = validate_hero_copy(framing["selected_title"], body, bridge, day_class)
    
    if final_validation["severity"] == "BLOCK":
        logger.error("[HeroFraming] CRITICAL: Generic copy slipped through. Forcing override.")
        
        if day_class == "phase_shift":
            body = "You want to decide just to stop feeling this way. That's not clarity. That's wanting relief."
            bridge = "You want it over more than you want it right."
    
    return {
        "success": True,
        "day_class": day_class,
        "hero_mode": framing["hero_mode"],
        "title": framing["selected_title"],
        "body": body,
        "bridge": bridge,
        "tone": framing["tone"],
        "pattern_key": pattern_key,
        "transit_stack": transit_stack,
        "dominant_tension": dominant_tension.get("modulated_id") if dominant_tension else None,
        "validation": final_validation,
        "bridge_validation": bridge_check,
        "debug": {
            "framing_source": "day_class_v1.8_precision",
            "interaction_theme": framing.get("interaction_theme"),
            "intensity": framing.get("intensity"),
            "generic_blocked": final_validation.get("severity") == "BLOCK",
            "bridge_is_additive": bridge_check.get("is_additive", True),
        }
    }


# =============================================================================
# PHASE 1: PATTERN TEMPLATES (v1.7 - NO DEFAULT GENERIC)
# =============================================================================
# Direct, behavioral language. No hedging.

PATTERN_TEMPLATES = {
    "fast_start_delayed_feedback": {
        "title": "You Moved. Nothing Echoed Back.",
        "what_happening": "You took action and now you're waiting. The silence is making you want to do more—send another message, check again, change course.",
        "why_feels": "Silence feels like rejection. It's not. But waiting is the hardest part.",
        "watch_for": "Sending a follow-up before it's needed. Changing direction because silence feels like rejection.",
        "better_move": "Let the current move finish playing out. Give it 24-48 more hours before deciding if something is wrong.",
        "interrupt": "Right before you check again—stop. Nothing broke. It just hasn't landed."
    },
    "high_drive_low_signal": {
        "title": "Energy Without a Target",
        "what_happening": "You want to do something, but you don't know what. So you're scanning—opening tabs, starting things, looking for a place to put this restlessness.",
        "why_feels": "Movement feels like progress. It's not. But stillness feels worse.",
        "watch_for": "Starting three things instead of finishing one. Confusing movement with progress.",
        "better_move": "Write down the one thing that would actually matter if it got done today. Do that first.",
        "interrupt": "You just switched tasks again. Stop. Pick one. Finish it."
    },
    "emotional_noise_low_clarity": {
        "title": "It's Not One Thing",
        "what_happening": "You're feeling something strongly, but you can't name it. The urge right now is to decide—just to get relief. That's the trap.",
        "why_feels": "Part of you wants this resolved more than understood.",
        "watch_for": "Making a decision just to get relief. Picking a fight because the tension needs somewhere to go.",
        "better_move": "Don't solve it right now. Let the wave move through before you act on any of it.",
        "interrupt": "If you feel the snap coming—stop. Say nothing. Walk away for five minutes."
    },
    "strong_urge_wrong_timing": {
        "title": "You're Ready Before It Is",
        "what_happening": "You know what you want. You've known for a while. But the situation isn't ready—and that gap is unbearable.",
        "why_feels": "Waiting when you're ready feels like being held back. It's not. But it feels that way.",
        "watch_for": "Trying to manufacture the opening. Pushing someone to be ready before they are.",
        "better_move": "Stay ready without acting. Use this time to prepare so when the window opens, you can move cleanly.",
        "interrupt": "You're about to force it. Don't. The cost of waiting is lower than the cost of pushing."
    },
    "pattern_returning_control": {
        "title": "The Grip Is Getting Tighter",
        "what_happening": "You can't control the thing that matters, so you're controlling everything around it—details, plans, other people's timelines.",
        "why_feels": "Controlling small things feels like safety. It's not. But it stops the panic.",
        "watch_for": "Over-preparing. Checking details you've already checked. Asking for updates you don't need.",
        "better_move": "Name what you're actually worried about—the real thing. Is controlling details helping that, or keeping you busy?",
        "interrupt": "You're checking it again. That's the pattern. Step back. Let it breathe."
    },
    "waiting_for_permission": {
        "title": "You Already Know",
        "what_happening": "You know what you want to do. You've known for a while. But you keep asking for input because committing feels too final.",
        "why_feels": "If someone else says it's right, you don't have to own it alone.",
        "watch_for": "Asking for opinions you don't need. Framing statements as questions. Waiting for permission you could give yourself.",
        "better_move": "Notice what you would do if no one would judge the choice. That's probably the answer.",
        "interrupt": "You're about to ask what they think. You already know. Say what you know instead."
    },
    "momentum_building": {
        "title": "It's Starting to Work",
        "what_happening": "You got traction. Now part of you wants to go faster, add more, scale before it's stable.",
        "why_feels": "Early wins create urgency to lock it in. That urgency can break what's working.",
        "watch_for": "Adding complexity before this stabilizes. Making promises based on early results.",
        "better_move": "Keep doing exactly what's working. Don't optimize yet. Don't expand yet.",
        "interrupt": "You're about to add something. Don't. Finish this first."
    },
    "holding_back_expression": {
        "title": "Something Wants to Be Said",
        "what_happening": "There's something you want to say—you've rehearsed it—but you keep waiting for the right moment. That moment won't come.",
        "why_feels": "You're protecting them from your honesty. Or protecting yourself from their reaction.",
        "watch_for": "Waiting for a perfect moment that doesn't come. Letting resentment build because they should have figured it out.",
        "better_move": "Say the smaller version first. You don't have to say all of it—just the first honest piece.",
        "interrupt": "You've rehearsed it twice already. Next time you see them—say the first sentence. Now."
    },
    "decision_avoidance": {
        "title": "The Choice You Keep Circling",
        "what_happening": "You've thought about this decision until thinking feels like action. It's not. You're avoiding the cost of choosing.",
        "why_feels": "Every option closes a door. Staying in analysis keeps them all open—hypothetically.",
        "watch_for": "Gathering more information when you already have enough. Treating 'still deciding' as an answer when it's avoidance.",
        "better_move": "Name what you're actually afraid of getting wrong. Not the practical risk—the emotional one.",
        "interrupt": "You're running the same loop again. Decide now—or drop it entirely. No more thinking."
    },
    "energy_recovery": {
        "title": "You Spent Something Recently",
        "what_happening": "You pushed hard and now you're running on less. The guilt is making you pretend you're not depleted.",
        "why_feels": "Resting feels like falling behind. It's not. But it feels that way.",
        "watch_for": "Forcing productivity when your body asks for rest. Saying yes because you feel guilty about slowing down.",
        "better_move": "Protect the recovery window. Don't fill empty space with new commitments.",
        "interrupt": "You feel guilty about resting. That's the signal. Stay down. One more day."
    },
    "quiet_signal_day": {
        "title": "Nothing Urgent Is Pulling",
        "what_happening": "No crisis. No breakthrough. Nothing demanding attention. And that quiet might feel like you're missing something.",
        "why_feels": "You're used to responding to urgency. When there's none, you might manufacture it.",
        "watch_for": "Looking for something to fix when nothing is broken. Making a neutral day feel significant because quiet feels wrong.",
        "better_move": "Use the space for maintenance—loose ends, small tasks. Don't fill it with new drama.",
        "interrupt": "You're scanning for a problem. Stop. There isn't one. Let the quiet be quiet."
    },
    # v1.7: REMOVED "default" pattern - NO GENERIC FALLBACK
}

# v1.7: Fallback patterns when no signal is detected - still tension-based
SIGNAL_ABSENT_PATTERNS = {
    "ambient_unease": {
        "title": "Something Is Off But You Can't Name It",
        "what_happening": "There's a low-grade discomfort today. Not crisis-level, but not neutral either. Part of you keeps scanning for what's wrong.",
        "why_feels": "Unnamed tension is harder to release. You want to fix something, but there's nothing obvious to fix.",
        "watch_for": "Projecting the discomfort onto small things. Creating problems so the feeling has somewhere to go.",
        "better_move": "Acknowledge the unease without solving it. It might just be atmospheric today.",
        "interrupt": "You're about to pick a fight with something small. That's not what this is about."
    },
    "restless_readiness": {
        "title": "You're Ready—But For What?",
        "what_happening": "There's energy available, but no clear place to put it. You're ready to move, but nothing is calling you forward yet.",
        "why_feels": "Readiness without direction feels like wasted potential. The urge is to create something to move toward.",
        "watch_for": "Starting things just to use the energy. Saying yes to invitations that aren't actually right.",
        "better_move": "Stay coiled. The right thing will appear. When it does, you'll be ready.",
        "interrupt": "You're about to commit to something just because you're bored. Wait."
    },
    "familiar_pressure": {
        "title": "This Shape Again",
        "what_happening": "You've been here before. The situation is different, but the feeling is the same. Part of you knows exactly how this usually goes.",
        "why_feels": "Patterns are comfortable even when they hurt. Breaking them takes more energy than repeating them.",
        "watch_for": "Defaulting to the familiar response. Knowing the ending but walking toward it anyway.",
        "better_move": "Notice the script. Ask what one small thing could be different this time.",
        "interrupt": "You're about to do the thing you always do. What if you didn't?"
    },
}


# =============================================================================
# PHASE 2: SIGNAL-BASED PATTERN SELECTION
# =============================================================================
# Extract signals from journal, mirror chat, reflections
# Map signals to patterns using simple heuristics

# Signal detection keywords
SIGNAL_KEYWORDS = {
    "action_taken": [
        "did", "sent", "made", "started", "launched", "pushed", "submitted",
        "told", "asked", "called", "emailed", "texted", "posted", "shipped",
        "finished", "completed", "delivered", "created", "built", "wrote"
    ],
    "waiting_outcome": [
        "waiting", "wait", "haven't heard", "no response", "nothing yet",
        "still waiting", "haven't gotten", "no reply", "silence", "crickets",
        "not yet", "hasn't landed", "hasn't happened", "no sign", "no word"
    ],
    "frustration": [
        "frustrated", "annoying", "annoyed", "stuck", "blocked", "tired of",
        "sick of", "fed up", "impatient", "why won't", "ugh", "argh",
        "driving me crazy", "can't believe", "so slow", "taking forever"
    ],
    "doubt": [
        "doubt", "not sure", "uncertain", "second guess", "maybe I shouldn't",
        "wrong", "mistake", "regret", "should I have", "was that right",
        "overthinking", "questioning", "wonder if", "what if I"
    ],
    "seeking_validation": [
        "what do you think", "should I", "is this right", "does this make sense",
        "am I crazy", "tell me", "need advice", "opinions", "feedback",
        "asking", "asked everyone", "checking with", "running it by"
    ],
    "high_urgency": [
        "need to", "have to", "must", "urgent", "now", "immediately",
        "can't wait", "right now", "asap", "deadline", "running out of time",
        "pressure", "pushing", "hurry", "rush"
    ],
    "low_clarity": [
        "confused", "unclear", "don't know", "not sure what", "which way",
        "can't decide", "torn", "options", "either", "or", "both",
        "no idea", "lost", "foggy", "muddled"
    ],
    "emotional_intensity": [
        "overwhelmed", "anxious", "stressed", "worried", "scared", "angry",
        "sad", "upset", "crying", "can't stop thinking", "obsessing",
        "spiraling", "triggered", "emotional", "feelings", "heavy"
    ],
    "recovery_needed": [
        "exhausted", "tired", "drained", "burnt out", "burnout", "need rest",
        "low energy", "depleted", "running on empty", "nothing left",
        "can't keep going", "need a break", "worn out"
    ],
    "momentum": [
        "working", "progress", "moving", "traction", "starting to",
        "finally", "breakthrough", "it's happening", "coming together",
        "things are", "getting somewhere", "on track"
    ],
    "something_unsaid": [
        "want to say", "need to tell", "haven't said", "holding back",
        "keeping", "secret", "can't say", "afraid to say", "should tell",
        "been meaning to", "avoiding the conversation"
    ],
    "control_seeking": [
        "need to control", "micromanaging", "checking", "monitoring",
        "can't let go", "have to make sure", "double checking", "triple",
        "keeping tabs", "watching", "obsessing over details"
    ]
}

def extract_signal_flags(texts: list) -> Dict[str, bool]:
    """
    Extract signal flags from a list of text content.
    Simple keyword matching - no NLP needed.
    """
    if not texts:
        return {}
    
    # Combine all text, lowercase
    combined = " ".join(str(t).lower() for t in texts if t)
    
    flags = {}
    for signal_name, keywords in SIGNAL_KEYWORDS.items():
        # Check if any keyword appears in the combined text
        flags[signal_name] = any(kw in combined for kw in keywords)
    
    return flags


# =============================================================================
# PHASE 3: TRAJECTORY / PHASE DETECTION
# =============================================================================
# Detect WHERE user is in pattern cycle: INITIATION → BUILD-UP → FRICTION → RECOVERY

PHASE_DEFINITIONS = {
    "INITIATION": {
        "description": "Starting energy. Movement beginning.",
        "tone": "encourage movement, avoid overthinking"
    },
    "BUILD_UP": {
        "description": "Progress happening. Momentum building.",
        "tone": "reinforce consistency, avoid distraction"
    },
    "FRICTION": {
        "description": "Effort not landing. Tension building.",
        "tone": "normalize frustration, prevent overreaction"
    },
    "RECOVERY": {
        "description": "Slowing down. Integration happening.",
        "tone": "slow down, integrate learning"
    }
}

# Phase-specific content adjustments
PHASE_MODIFIERS = {
    "INITIATION": {
        "title_prefix": "",
        "what_happening_suffix": "",
        "watch_for_emphasis": "Don't second-guess too early.",
        "better_move_emphasis": "Keep moving forward.",
        "interrupt_emphasis": "Hesitation now costs more than mistakes."
    },
    "BUILD_UP": {
        "title_prefix": "",
        "what_happening_suffix": " This is part of the process.",
        "watch_for_emphasis": "Don't get distracted by new shiny things.",
        "better_move_emphasis": "Stay the course a bit longer.",
        "interrupt_emphasis": "Consistency beats intensity here."
    },
    "FRICTION": {
        "title_prefix": "",
        "what_happening_suffix": " The gap between effort and result is creating pressure.",
        "watch_for_emphasis": "Don't blow up what's actually working.",
        "better_move_emphasis": "The frustration is information, not a command.",
        "interrupt_emphasis": "Nothing has failed yet—it just hasn't landed."
    },
    "RECOVERY": {
        "title_prefix": "",
        "what_happening_suffix": " Your system is recalibrating.",
        "watch_for_emphasis": "Don't judge the slowdown as failure.",
        "better_move_emphasis": "Rest is part of the work.",
        "interrupt_emphasis": "Guilt about rest means you need more rest."
    }
}


def extract_signal_flags_per_entry(texts: list) -> list:
    """
    Extract signal flags for EACH text entry separately.
    Used for detecting trajectory across recent entries.
    """
    if not texts:
        return []
    
    entry_flags = []
    for text in texts:
        if not text:
            continue
        text_lower = str(text).lower()
        flags = {}
        for signal_name, keywords in SIGNAL_KEYWORDS.items():
            flags[signal_name] = any(kw in text_lower for kw in keywords)
        entry_flags.append(flags)
    
    return entry_flags


def detect_pattern_phase(signal_flags: Dict[str, bool], entry_history: list) -> tuple:
    """
    Detect where user is in the pattern cycle.
    
    Uses current signals + recent history to determine phase.
    Returns (phase, phase_description, trajectory_summary)
    
    Phases:
    - INITIATION: action_taken, high_urgency, no frustration yet
    - BUILD_UP: action_taken, momentum, some progress
    - FRICTION: frustration/doubt after action, waiting for outcome
    - RECOVERY: recovery signals, lower urgency, reflection mode
    """
    
    # Count signals across recent history
    history_counts = {
        "action_taken": 0,
        "frustration": 0,
        "doubt": 0,
        "momentum": 0,
        "recovery_needed": 0,
        "waiting_outcome": 0,
        "emotional_intensity": 0,
        "high_urgency": 0
    }
    
    for entry_flags in entry_history:
        for key in history_counts.keys():
            if entry_flags.get(key):
                history_counts[key] += 1
    
    # Build trajectory summary
    trajectory_parts = []
    if history_counts["action_taken"] > 0:
        trajectory_parts.append(f"action({history_counts['action_taken']})")
    if history_counts["momentum"] > 0:
        trajectory_parts.append(f"momentum({history_counts['momentum']})")
    if history_counts["frustration"] > 0:
        trajectory_parts.append(f"frustration({history_counts['frustration']})")
    if history_counts["recovery_needed"] > 0:
        trajectory_parts.append(f"recovery({history_counts['recovery_needed']})")
    
    trajectory_summary = " → ".join(trajectory_parts) if trajectory_parts else "no clear trajectory"
    
    # Current state signals
    has_action = signal_flags.get("action_taken", False)
    has_frustration = signal_flags.get("frustration", False)
    has_doubt = signal_flags.get("doubt", False)
    has_momentum = signal_flags.get("momentum", False)
    has_recovery = signal_flags.get("recovery_needed", False)
    has_waiting = signal_flags.get("waiting_outcome", False)
    has_urgency = signal_flags.get("high_urgency", False)
    has_emotional = signal_flags.get("emotional_intensity", False)
    
    # Historical patterns
    had_action_before = history_counts["action_taken"] > 0
    had_frustration_before = history_counts["frustration"] > 0
    had_momentum_before = history_counts["momentum"] > 0
    
    # =================================================================
    # PHASE DETECTION RULES (priority order)
    # =================================================================
    
    # RECOVERY: Clear recovery signals, or coming down from intensity
    if has_recovery:
        return ("RECOVERY", 
                "I think I'm coming out of it.",
                trajectory_summary)
    
    if had_frustration_before and not has_frustration and not has_urgency:
        return ("RECOVERY",
                "Something in me is settling again.",
                trajectory_summary)
    
    # FRICTION: Frustration/doubt after taking action, waiting without result
    if has_frustration or has_doubt:
        if has_waiting or had_action_before:
            return ("FRICTION",
                    "I did my part. Nothing came back yet.",
                    trajectory_summary)
        if has_emotional:
            return ("FRICTION",
                    "There's a lot here, but none of it is clear.",
                    trajectory_summary)
        return ("FRICTION",
                "Something's off, but I can't name it.",
                trajectory_summary)
    
    # BUILD-UP: Momentum happening, action taken, progress visible
    if has_momentum:
        if has_action or had_action_before:
            return ("BUILD_UP",
                    "Things are picking up—I can feel it.",
                    trajectory_summary)
        return ("BUILD_UP",
                "This is already in motion.",
                trajectory_summary)
    
    if had_action_before and had_momentum_before and not has_frustration:
        return ("BUILD_UP",
                "I just need to keep going.",
                trajectory_summary)
    
    # INITIATION: Action starting, urgency present, no friction yet
    if has_action and not has_frustration and not has_doubt:
        return ("INITIATION",
                "Something is starting to move.",
                trajectory_summary)
    
    if has_urgency and not had_frustration_before:
        return ("INITIATION",
                "I'm ready. I just don't know for what yet.",
                trajectory_summary)
    
    # Default: INITIATION with inner voice
    return ("INITIATION",
            "Something is starting… I just don't know what yet.",
            trajectory_summary)


def apply_phase_modifier(template: dict, phase: str, phase_description: str) -> dict:
    """
    Apply phase-specific modifications to template content.
    Returns modified template with phase-aware adjustments.
    """
    modifier = PHASE_MODIFIERS.get(phase, PHASE_MODIFIERS["INITIATION"])
    
    # Create modified copy
    modified = template.copy()
    
    # For FRICTION phase, provide more specific content
    if phase == "FRICTION":
        # Add context about the friction
        if "hasn't landed" not in modified["what_happening"]:
            modified["what_happening"] = modified["what_happening"] + modifier["what_happening_suffix"]
        
        # Emphasize the interrupt for friction
        if "nothing has failed" not in modified["interrupt"].lower():
            modified["interrupt"] = modified["interrupt"] + " " + modifier["interrupt_emphasis"]
    
    elif phase == "RECOVERY":
        # Soften the urgency for recovery
        if "recalibrating" not in modified["what_happening"]:
            modified["what_happening"] = modified["what_happening"] + modifier["what_happening_suffix"]
    
    elif phase == "BUILD_UP":
        # Reinforce consistency
        if "stay" not in modified["better_move"].lower():
            modified["better_move"] = modified["better_move"] + " " + modifier["better_move_emphasis"]
    
    return modified


def select_pattern_from_signals(flags: Dict[str, bool]) -> tuple:
    """
    Select pattern based on signal flags.
    Returns (pattern_key, reason)
    """
    # Priority-ordered pattern matching rules
    
    # Rule 1: Action taken + waiting for outcome + frustration/doubt
    if flags.get("action_taken") and flags.get("waiting_outcome"):
        if flags.get("frustration"):
            return ("fast_start_delayed_feedback", 
                    "Action taken + waiting for outcome + frustration detected")
        if flags.get("doubt"):
            return ("fast_start_delayed_feedback",
                    "Action taken + waiting for outcome + doubt detected")
        return ("fast_start_delayed_feedback",
                "Action taken + waiting for outcome")
    
    # Rule 2: High urgency + low clarity
    if flags.get("high_urgency") and flags.get("low_clarity"):
        return ("strong_urge_wrong_timing",
                "High urgency + low clarity detected")
    
    # Rule 3: High urgency without action
    if flags.get("high_urgency") and not flags.get("action_taken"):
        if flags.get("doubt") or flags.get("low_clarity"):
            return ("strong_urge_wrong_timing",
                    "High urgency without action + doubt/uncertainty")
    
    # Rule 4: Seeking validation + hesitation
    if flags.get("seeking_validation"):
        if not flags.get("action_taken"):
            return ("waiting_for_permission",
                    "Seeking validation without action taken")
        if flags.get("doubt"):
            return ("waiting_for_permission",
                    "Seeking validation + doubt detected")
    
    # Rule 5: Emotional intensity + low clarity
    if flags.get("emotional_intensity") and flags.get("low_clarity"):
        return ("emotional_noise_low_clarity",
                "Emotional intensity + low clarity detected")
    
    # Rule 6: Emotional intensity alone (high)
    if flags.get("emotional_intensity"):
        if flags.get("frustration"):
            return ("emotional_noise_low_clarity",
                    "Emotional intensity + frustration")
    
    # Rule 7: Control seeking behavior
    if flags.get("control_seeking"):
        return ("pattern_returning_control",
                "Control-seeking behavior detected")
    
    # Rule 8: Recovery signals
    if flags.get("recovery_needed"):
        return ("energy_recovery",
                "Recovery/exhaustion signals detected")
    
    # Rule 9: Momentum signals
    if flags.get("momentum") and flags.get("action_taken"):
        return ("momentum_building",
                "Momentum + action signals detected")
    
    # Rule 10: Something unsaid
    if flags.get("something_unsaid"):
        return ("holding_back_expression",
                "Holding back expression signals detected")
    
    # Rule 11: High drive but no clear direction
    if flags.get("high_urgency") and not flags.get("momentum"):
        return ("high_drive_low_signal",
                "High urgency without clear momentum")
    
    # Rule 12: Low clarity / indecision dominant
    if flags.get("low_clarity") and flags.get("doubt"):
        return ("decision_avoidance",
                "Low clarity + doubt = decision avoidance")
    
    # v1.7: NO GENERIC FALLBACK - return signal-absent pattern instead
    return (None, "No strong lived-state signals detected")


def select_pattern_for_user(user_id: str, signal_flags: Dict[str, bool], chart_data: Optional[dict] = None) -> tuple:
    """
    Select appropriate pattern template based on signal flags.
    
    v1.7: When no signals detected, use SIGNAL_ABSENT_PATTERNS instead of generic default.
    
    Returns (pattern_key, reason)
    """
    import hashlib
    from datetime import datetime, timezone
    
    # First try signal-based selection
    if signal_flags:
        pattern_key, reason = select_pattern_from_signals(signal_flags)
        if pattern_key:
            logger.info(f"[HomeInsight] Signal-selected pattern '{pattern_key}' for user {user_id[:8]}: {reason}")
            return (pattern_key, reason)
    
    # v1.7: Fallback to SIGNAL_ABSENT patterns - still tension-based, NOT generic
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = hashlib.sha256(f"{user_id}:{today}".encode()).hexdigest()
    
    # Get list of signal-absent pattern keys
    absent_keys = list(SIGNAL_ABSENT_PATTERNS.keys())
    
    # Select based on seed
    index = int(seed[:8], 16) % len(absent_keys)
    selected = absent_keys[index]
    
    logger.info(f"[HomeInsight] Signal-absent pattern '{selected}' for user {user_id[:8]}")
    return (selected, "No lived-state signals - using tension-based signal-absent pattern")


async def generate_daily_insight(db, user_id: str) -> Dict[str, Any]:
    """
    Generate structured daily insight for Home Screen.
    
    v1.7: SIGNAL DOMINANCE + NO GENERIC FALLBACK
    - phase_shift days ALWAYS use phase_shift framing
    - Generic copy is BLOCKED
    - Signal-absent days use tension-based patterns, not generic
    
    Returns the new structured format with debug info.
    """
    from datetime import datetime, timezone, timedelta
    from bson import ObjectId
    
    logger.info(f"[HomeInsight] Generating insight for user {user_id[:8]}...")
    
    # =================================================================
    # STEP 1: Collect lived-state signals from recent activity
    # =================================================================
    texts_to_analyze = []
    signal_sources = []
    
    # Calculate cutoff date (no timezone for MongoDB comparison with naive datetimes)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Get recent journal entries (last 7 days)
    try:
        journal_cursor = db.journal.find({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago}
        }).sort("created_at", -1).limit(10)
        
        async for entry in journal_cursor:
            content = entry.get("content", "")
            if content:
                texts_to_analyze.append(content)
                signal_sources.append("journal")
    except Exception as e:
        logger.debug(f"[HomeInsight] Journal fetch error: {e}")
    
    # Get recent mirror chat insights (last 7 days)
    try:
        chat_cursor = db.mirror_insights.find({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago.isoformat()}
        }).sort("created_at", -1).limit(10)
        
        async for insight in chat_cursor:
            content = insight.get("content", "") or insight.get("insight", "")
            if content:
                texts_to_analyze.append(content)
                signal_sources.append("mirror_chat")
    except Exception as e:
        logger.debug(f"[HomeInsight] Mirror chat fetch error: {e}")
    
    # Get recent lunar reflections (last 7 days)
    try:
        lunar_cursor = db.lunar_journal.find({
            "user_id": user_id,
            "created_at": {"$gte": seven_days_ago.isoformat()}
        }).sort("created_at", -1).limit(5)
        
        async for reflection in lunar_cursor:
            content = reflection.get("content", "") or reflection.get("reflection", "")
            if content:
                texts_to_analyze.append(content)
                signal_sources.append("lunar_reflection")
    except Exception as e:
        logger.debug(f"[HomeInsight] Lunar journal fetch error: {e}")
    
    logger.info(f"[HomeInsight] Collected {len(texts_to_analyze)} texts from {len(set(signal_sources))} sources")
    
    # =================================================================
    # STEP 2: Extract signal flags (combined + per-entry for trajectory)
    # =================================================================
    signal_flags = extract_signal_flags(texts_to_analyze)
    active_flags = {k: v for k, v in signal_flags.items() if v}
    logger.info(f"[HomeInsight] Active signal flags: {list(active_flags.keys())}")
    
    # Extract per-entry flags for trajectory detection
    entry_history = extract_signal_flags_per_entry(texts_to_analyze)
    
    # =================================================================
    # STEP 3: Detect pattern phase (trajectory awareness)
    # =================================================================
    phase, phase_description, trajectory_summary = detect_pattern_phase(signal_flags, entry_history)
    logger.info(f"[HomeInsight] Detected phase: {phase} - {phase_description}")
    
    # =================================================================
    # STEP 4: Select pattern based on signals
    # =================================================================
    chart_data = None
    try:
        chart_data = await db.charts.find_one({"user_id": user_id})
    except Exception as e:
        logger.debug(f"[HomeInsight] Could not load chart: {e}")
    
    pattern_key, selection_reason = select_pattern_for_user(user_id, signal_flags, chart_data)
    
    # v1.7: Check if using signal-absent pattern
    if pattern_key in SIGNAL_ABSENT_PATTERNS:
        template = SIGNAL_ABSENT_PATTERNS[pattern_key]
    elif pattern_key in PATTERN_TEMPLATES:
        template = PATTERN_TEMPLATES[pattern_key]
    else:
        # Absolute fallback - should never happen
        template = SIGNAL_ABSENT_PATTERNS["ambient_unease"]
        pattern_key = "ambient_unease"
        logger.warning(f"[HomeInsight] Pattern key '{pattern_key}' not found, using ambient_unease")
    
    # =================================================================
    # STEP 5: Apply phase modifier to template
    # =================================================================
    modified_template = apply_phase_modifier(template, phase, phase_description)
    
    # =================================================================
    # STEP 5.5 (v1.5 + v1.7): GET DAY-CLASS HERO FRAMING WITH SIGNAL DOMINANCE
    # =================================================================
    # Fetch transit stack from field signals for day classification
    try:
        from services.field_signals import detect_transit_convergence
        transit_stack = detect_transit_convergence()
    except Exception as e:
        logger.debug(f"[HomeInsight] Transit detection error: {e}")
        transit_stack = {"type": "background", "classification": "normal_flow", "intensity": 0}
    
    day_class = transit_stack.get("classification", "normal_flow")
    
    # Fetch modulated tension for the day
    try:
        from services.transit_signals import get_dominant_modulated_tension
        field_context = {"field_tone": "clarity" if phase == "CLARITY" else "reset", "clarity_level": "low" if phase == "FRICTION" else "medium"}
        dominant_tension = get_dominant_modulated_tension(transit_stack, field_context)
    except Exception as e:
        logger.debug(f"[HomeInsight] Tension modulation error: {e}")
        dominant_tension = None
    
    # v1.7: SIGNAL DOMINANCE - Generate day-class aware hero with validation
    hero_output = generate_day_class_hero(day_class, transit_stack, dominant_tension, pattern_key)
    
    logger.info(f"[HomeInsight] Day class: {day_class}, Hero title: {hero_output.get('title')}")
    
    # =================================================================
    # STEP 6: Build response with day-class hero (v1.7 validated)
    # =================================================================
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Determine confidence based on signal strength
    confidence = "low"
    if len(active_flags) >= 3:
        confidence = "high"
    elif len(active_flags) >= 1:
        confidence = "medium"
    
    # v1.7: SIGNAL DOMINANCE RULE
    # phase_shift and cycle_event ALWAYS use day-class framing
    # NO fallback to generic copy
    
    if day_class in ["phase_shift", "cycle_event"]:
        # Day-class framing takes priority - ALWAYS
        title = hero_output.get("title", modified_template["title"])
        body = hero_output.get("body", modified_template["what_happening"])
        bridge = hero_output.get("bridge", "")
    else:
        # Normal flow - use pattern-based title
        title = modified_template["title"]
        body = modified_template["what_happening"]
        
        # v1.7: Validate even normal flow copy
        if is_generic_copy(body):
            logger.warning("[HomeInsight] Generic body detected in normal_flow, using signal-absent pattern")
            fallback = SIGNAL_ABSENT_PATTERNS["ambient_unease"]
            title = fallback["title"]
            body = fallback["what_happening"]
        
        # Use why_feels as bridge if it's personal enough
        bridge = modified_template.get("why_feels", "")
        if is_generic_copy(bridge):
            bridge = ""
    
    # v1.7: Final validation - BLOCK generic output
    final_validation = validate_hero_copy(title, body, bridge, day_class)
    
    if final_validation["severity"] == "BLOCK":
        logger.error("[HomeInsight] BLOCKED GENERIC OUTPUT - forcing strong override")
        # Force a strong tension-based output
        title = "Something Is Off But You Can't Name It"
        body = "There's a low-grade discomfort today. Not crisis-level, but not neutral either. Part of you keeps scanning for what's wrong."
        bridge = "Unnamed tension is harder to release."
    
    return {
        "success": True,
        "date": today,
        "pattern_id": f"{pattern_key}_{today.replace('-', '')}",
        "title": title,
        # New Mirror-format fields (v1.7 signal dominance)
        "body": body,
        "bridge": bridge if bridge else None,
        # Day-class metadata
        "day_class": day_class,
        "hero_mode": hero_output.get("hero_mode"),
        "tone": hero_output.get("tone"),
        # Legacy fields (for compatibility)
        "what_happening": modified_template["what_happening"],
        "why_feels": modified_template["why_feels"],
        "watch_for": modified_template["watch_for"],
        "better_move": modified_template["better_move"],
        "interrupt": modified_template["interrupt"],
        "phase": phase,
        "phase_description": phase_description,
        "confidence": confidence,
        "card_version": "mirror_v20_clarity",  # Version flag for frontend
        "debug": {
            "pattern_key": pattern_key,
            "selection_reason": selection_reason,
            "phase": phase,
            "phase_description": phase_description,
            "trajectory_summary": trajectory_summary,
            "signal_flags": active_flags,
            "signal_sources": list(set(signal_sources)),
            "texts_analyzed": len(texts_to_analyze),
            "entries_in_history": len(entry_history),
            "source": "signal_v7_dominance" if day_class != "normal_flow" else "signal_v7_pattern" if active_flags else "signal_v7_absent",
            "day_class": day_class,
            "hero_mode": hero_output.get("hero_mode"),
            "interaction_theme": transit_stack.get("interaction_theme"),
            "transit_intensity": transit_stack.get("intensity"),
            "dominant_tension": dominant_tension.get("modulated_id") if dominant_tension else None,
            "validation": final_validation,
            "generic_blocked": final_validation.get("severity") == "BLOCK",
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
    }
