"""
Astrology Today Snapshot v4 — Full Integration (No Dual Systems)

ONE coherent intelligence. No split between "narrative" and "data".

Structure:
1. EXPERIENCE (hook) - Start with lived experience
2. INTERNAL DYNAMICS (placements translated to felt experience)
3. CAUSE (transit stack in human language)
4. GUIDANCE (what to do)

Technical astrology available in expandable "See what's driving this"

NO bullet points. NO numbered lists. NO placement-first explanations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# BANNED LANGUAGE - Horoscope vagueness + Abstract concepts
# =============================================================================

BANNED_ASTROLOGY_TERMS = [
    "energy", "energies", "vibes", "vibrations",
    "universe", "cosmic", "celestial dance",
    "alignment", "aligned", "in alignment",
    "manifest", "manifestation", "manifesting",
    "flow", "flowing", "go with the flow",
    "open yourself", "be open to",
    "embrace", "embracing",
    "journey", "on your journey",
    "powerful", "powerful time",
    "transformation", "transformative",
    "awakening", "spiritual awakening",
    "internal compass", "compass",
    "recalibrating", "recalibrate",
    "reflective day", "reflective time",
]


def is_horoscope_language(text: str) -> bool:
    """Check if text contains banned horoscope-style language."""
    text_lower = text.lower()
    return any(term in text_lower for term in BANNED_ASTROLOGY_TERMS)


# =============================================================================
# v4: PLACEMENT TO EXPERIENCE TRANSLATIONS
# =============================================================================
# Translate raw placements into felt internal dynamics

SUN_SIGN_DYNAMICS = {
    "aries": "Quick impulses. A need to act before thinking catches up.",
    "taurus": "A pull toward stability. Resistance to being pushed.",
    "gemini": "Multiple threads running at once. Hard to settle on one.",
    "cancer": "Emotional undertow. Sensitivity to atmosphere.",
    "leo": "Need to be seen. Tension when overlooked.",
    "virgo": "Noticing everything that's wrong. Difficulty letting it go.",
    "libra": "Weighing options. Difficulty committing without consensus.",
    "scorpio": "Intensity underneath. Awareness of what's not being said.",
    "sagittarius": "Restlessness. A pull toward something bigger.",
    "capricorn": "Weight of responsibility. Focus on what's practical.",
    "aquarius": "Detachment. Observing more than participating.",
    "pisces": "Picking up more nuance than usual. Boundaries feel thin.",
}

MOON_SIGN_DYNAMICS = {
    "aries": "Emotional reactions come quickly. Impatience with slow processing.",
    "taurus": "Emotional security through stability. Resistance to disruption.",
    "gemini": "Feelings change quickly. Hard to pin down what you actually feel.",
    "cancer": "Deep emotional sensitivity. Strong reactions to personal space.",
    "leo": "Need for emotional recognition. Hurt when dismissed.",
    "virgo": "Anxiety about getting things right. Emotional perfectionism.",
    "libra": "Emotional peace through harmony. Conflict feels destabilizing.",
    "scorpio": "Intense feelings running deep. Hard to surface them.",
    "sagittarius": "Emotional need for freedom. Restlessness when contained.",
    "capricorn": "Guarded emotions. Difficulty expressing vulnerability.",
    "aquarius": "Emotional distance. Processing through observation, not feeling.",
    "pisces": "Absorbing others' emotions. Difficulty knowing what's yours.",
}

RISING_SIGN_DYNAMICS = {
    "aries": "Approach things directly. Frustration with hesitation.",
    "taurus": "Slow, steady approach. Taking your time feels natural.",
    "gemini": "Curious, scattered attention. Multiple approaches at once.",
    "cancer": "Protective stance. Cautious until safety is established.",
    "leo": "Present yourself visibly. Confidence as default mode.",
    "virgo": "Analytical approach. Noticing details before acting.",
    "libra": "Diplomatic stance. Seeking balance before committing.",
    "scorpio": "Guarded approach. Revealing slowly, watching first.",
    "sagittarius": "Pull between stepping back and wanting movement.",
    "capricorn": "Serious approach. Responsibility before pleasure.",
    "aquarius": "Unconventional stance. Doing things your own way.",
    "pisces": "Receptive approach. Taking in before responding.",
}

HOUSE_CONTEXTS = {
    1: "how you present yourself",
    2: "what you value and need for security",
    3: "how you think and communicate",
    4: "home, family, and emotional foundation",
    5: "creativity, pleasure, and self-expression",
    6: "daily routines and how you handle stress",
    7: "relationships and how you partner",
    8: "shared resources and emotional intensity",
    9: "beliefs, meaning, and expansion",
    10: "career, reputation, and public role",
    11: "community, hopes, and future vision",
    12: "what's hidden, including from yourself",
}


def translate_placement_to_experience(
    planet: str,
    sign: str,
    house: Optional[int] = None
) -> str:
    """
    Translate a single placement into felt experience.
    
    Instead of: "Sun in Pisces in 3rd house"
    Returns: "Your mind is picking up more nuance than usual"
    """
    sign_lower = sign.lower() if sign else ""
    planet_lower = planet.lower() if planet else ""
    
    # Get base dynamic from sign
    if planet_lower == "sun":
        base = SUN_SIGN_DYNAMICS.get(sign_lower, "")
    elif planet_lower == "moon":
        base = MOON_SIGN_DYNAMICS.get(sign_lower, "")
    elif planet_lower in ["ascendant", "rising"]:
        base = RISING_SIGN_DYNAMICS.get(sign_lower, "")
    else:
        base = ""
    
    # Add house context if available
    if house and house in HOUSE_CONTEXTS:
        context = HOUSE_CONTEXTS[house]
        if base:
            # Combine: dynamic + context
            return f"{base} This shows up especially around {context}."
        else:
            return f"Something is active around {context}."
    
    return base


def generate_internal_dynamics(
    sun_sign: str = None,
    moon_sign: str = None,
    rising_sign: str = None,
    sun_house: int = None,
    moon_house: int = None,
    day_class: str = "normal_flow"
) -> str:
    """
    Generate the INTERNAL DYNAMICS layer - placements as felt experience.
    
    Picks the most relevant 1-2 dynamics based on day_class.
    No bullet points. Flowing prose.
    """
    dynamics = []
    
    # Sun dynamic
    if sun_sign:
        sun_exp = translate_placement_to_experience("sun", sun_sign, sun_house)
        if sun_exp:
            dynamics.append(("sun", sun_exp))
    
    # Moon dynamic
    if moon_sign:
        moon_exp = translate_placement_to_experience("moon", moon_sign, moon_house)
        if moon_exp:
            dynamics.append(("moon", moon_exp))
    
    # Rising dynamic
    if rising_sign:
        rising_exp = translate_placement_to_experience("rising", rising_sign)
        if rising_exp:
            dynamics.append(("rising", rising_exp))
    
    if not dynamics:
        return ""
    
    # Select based on day_class priority
    # phase_shift: prioritize Moon (emotional processing)
    # cycle_event: prioritize Sun (core identity)
    # normal_flow: prioritize Rising (daily approach)
    
    if day_class == "phase_shift":
        priority_order = ["moon", "sun", "rising"]
    elif day_class == "cycle_event":
        priority_order = ["sun", "moon", "rising"]
    else:
        priority_order = ["rising", "moon", "sun"]
    
    # Sort by priority
    dynamics_sorted = sorted(dynamics, key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else 99)
    
    # Take top 2 max for narrative flow
    selected = [d[1] for d in dynamics_sorted[:2]]
    
    # Combine into flowing prose
    if len(selected) == 2:
        return f"{selected[0]} Meanwhile, {selected[1].lower()}"
    elif len(selected) == 1:
        return selected[0]
    
    return ""


# =============================================================================
# TRANSIT STACK TO CAUSE MAPPING
# =============================================================================
# Maps transit events to plain-language causal explanations

TRANSIT_CAUSE_TEMPLATES = {
    # New Moon causes
    "new_moon": {
        "base_cause": "A new cycle is beginning",
        "what_happens": "Old patterns are closing and something new is trying to start",
        "why_pressure": "The impulse to start fresh collides with things that aren't finished yet",
    },
    
    # Full Moon causes
    "full_moon": {
        "base_cause": "Something is coming to completion",
        "what_happens": "What's been building is now visible and asking for resolution",
        "why_pressure": "You can see the full picture now, which creates pressure to act on it",
    },
    
    # Equinox causes
    "equinox": {
        "base_cause": "A major directional shift is happening",
        "what_happens": "The system is recalibrating between expansion and contraction",
        "why_pressure": "Old momentum hasn't stopped but new direction hasn't started",
    },
    
    # Solstice causes
    "solstice": {
        "base_cause": "A peak or trough point in the year",
        "what_happens": "Maximum extension in one direction before reversal",
        "why_pressure": "You're at an extreme—something has to give",
    },
    
    # Mercury Retrograde causes
    "mercury_retrograde": {
        "base_cause": "Communication and planning systems are under review",
        "what_happens": "Things you thought were settled are reopening",
        "why_pressure": "Forward motion is blocked; revision is required",
    },
    
    # Venus Retrograde causes  
    "venus_retrograde": {
        "base_cause": "Relationship and value patterns are being reconsidered",
        "what_happens": "What you want and what you're getting are being compared",
        "why_pressure": "Dissatisfaction surfaces that was previously ignored",
    },
    
    # Mars Retrograde causes
    "mars_retrograde": {
        "base_cause": "Action and drive patterns are being questioned",
        "what_happens": "Your usual ways of pushing forward aren't working",
        "why_pressure": "Frustration builds when effort doesn't produce results",
    },
}

# Interaction theme to cause mapping (when transits combine)
INTERACTION_THEME_CAUSES = {
    "reset_at_threshold": {
        "cause": "A reset cycle and a directional shift are happening at the same time",
        "effect": "That creates urgency without clarity",
        "why_now": "Two major transitions are overlapping, so nothing feels stable",
    },
    "portal_opening": {
        "cause": "Multiple starting points are converging",
        "effect": "Too many things want to begin at once",
        "why_now": "The system is flooded with new impulses before old ones resolved",
    },
    "culmination_at_threshold": {
        "cause": "Something is completing exactly when direction is shifting",
        "effect": "Endings and beginnings are colliding",
        "why_now": "You need to close one chapter while opening another—at the same time",
    },
    "destabilization_window": {
        "cause": "The usual rules aren't holding",
        "effect": "What normally works isn't working right now",
        "why_now": "Multiple systems are in flux simultaneously",
    },
    "deep_release": {
        "cause": "Something old is ready to leave",
        "effect": "Pressure builds until you let go",
        "why_now": "The holding pattern has reached its limit",
    },
    "peak_illumination": {
        "cause": "Maximum visibility on something previously hidden",
        "effect": "You can't unsee what's now obvious",
        "why_now": "The full picture is available—denial isn't",
    },
    "emotional_culmination": {
        "cause": "Feelings that have been building are cresting",
        "effect": "Emotional pressure demands acknowledgment",
        "why_now": "The container is full; overflow is inevitable",
    },
    "multiple_events_active": {
        "cause": "Several transit events are active simultaneously",
        "effect": "Competing pressures create confusion",
        "why_now": "There's no single clear signal—multiple forces are pulling at once",
    },
}

# =============================================================================
# v3: EXPERIENCE HOOKS - Lived experience, not descriptions
# =============================================================================
# Start with what user is actually experiencing right now

EXPERIENCE_HOOKS = {
    "phase_shift": [
        "You may find yourself replaying things today — conversations, messages, small moments that suddenly feel heavier than they should.",
        "You keep wanting to make a decision, but every time you try, something doesn't feel right.",
        "There's a restlessness that won't settle. You want something resolved, but you're not sure what.",
        "You're noticing details you normally wouldn't — small things that feel like they mean something.",
        "Part of you knows something is shifting, but you can't point to what exactly.",
    ],
    "cycle_event": [
        "Something keeps pulling at your attention today. You can't quite look away from it.",
        "A conversation or moment from recently keeps surfacing. There's something there you haven't fully processed.",
        "You may feel more aware of time today — what's been and what's coming.",
        "Things you'd normally let pass are catching your attention. Something is asking to be noticed.",
        "There's a sense that something is completing, even if you can't name what.",
    ],
    "normal_flow": [
        "The day feels ordinary, but something underneath is gently moving.",
        "You may catch yourself thinking about things without any obvious trigger.",
        "There's a quiet quality to today. Nothing is demanding, but something is present.",
        "Small observations feel more interesting than usual. Your mind is processing something.",
        "Things feel steady, but there's a subtle pull toward reflection.",
    ],
}

# =============================================================================
# v3: CAUSE BRIDGES - Human language cause statements
# =============================================================================
# Translate transits into felt experience, not astrology terms

CAUSE_BRIDGES = {
    "reset_at_threshold": [
        "That's because a reset cycle and a directional shift are overlapping right now. It creates reflection before movement.",
        "This is happening because two cycles are converging — one ending, one trying to start. That overlap creates pressure without resolution.",
        "A new beginning and a major turning point are landing at the same time. Your system is processing more than usual.",
    ],
    "portal_opening": [
        "Multiple starting points are converging right now. Your attention is being pulled in several directions.",
        "Several things are trying to begin at once. That's why nothing feels settled yet.",
        "New impulses are stacking up before old ones have resolved. That's the source of the restlessness.",
    ],
    "culmination_at_threshold": [
        "Something is coming to a head exactly when the ground is shifting. Endings and beginnings are colliding.",
        "A completion is happening during a major transition. That's why the weight feels doubled.",
        "You're being asked to close one chapter while another is already opening. That's the pressure.",
    ],
    "destabilization_window": [
        "The usual rules aren't holding right now. What normally works isn't working.",
        "Multiple systems are in flux at the same time. That's why things feel off.",
        "This is a window where stability isn't available. That's information, not a problem to solve.",
    ],
    "deep_release": [
        "Something old is ready to leave. The pressure you feel is resistance to that release.",
        "A holding pattern has reached its limit. What's been held is asking to move.",
        "The weight you're feeling is accumulated — things that have been waiting to release.",
    ],
    "peak_illumination": [
        "Everything is more visible right now. What was hidden is becoming obvious.",
        "You can see the full picture now. That's why it feels heavier — denial isn't available.",
        "Maximum clarity is landing. What you're seeing is what's actually there.",
    ],
    "emotional_culmination": [
        "Feelings that have been building are cresting. That's why small things feel big.",
        "Emotional pressure that's been accumulating is surfacing. The container is full.",
        "What you're feeling isn't new — it's been building. This is just when it's becoming visible.",
    ],
    "multiple_events_active": [
        "Several forces are active at once. That's why there's no single clear signal.",
        "Multiple cycles are overlapping. The confusion you feel is because there isn't one answer right now.",
        "This is a convergence point. Several things are asking for attention simultaneously.",
    ],
}

# Single transit causes (when no interaction theme)
SINGLE_TRANSIT_CAUSES = {
    "new_moon": [
        "A new cycle is starting. Old patterns are closing and something new is trying to begin.",
        "This is a beginning point. Your system is wiping the slate before the next thing.",
        "Something is resetting. That's why the urge to start fresh feels strong.",
    ],
    "full_moon": [
        "Something that's been building is now fully visible. You can see it clearly now.",
        "This is a completion point. What's been developing is ready to be acknowledged.",
        "Maximum visibility on something. What you're noticing has been building for a while.",
    ],
    "equinox": [
        "A major directional shift is happening. The system is rebalancing.",
        "You're at a pivot point in the year. Old momentum is meeting new direction.",
        "This is a turning point. What worked before may need adjustment.",
    ],
    "solstice": [
        "You're at an extreme point. Maximum extension before reversal.",
        "This is a peak or trough. Something has gone as far as it can in one direction.",
        "The system is at maximum stretch. Change of direction is coming.",
    ],
}

# =============================================================================
# v3: GUIDANCE LINES - Single actionable statements
# =============================================================================

GUIDANCE_LINES = {
    "phase_shift": [
        "Don't rush to act on what comes up. Let it show you what it's actually about first.",
        "The pressure to decide is real. The answer isn't available yet. Both are true.",
        "Let things stay unresolved for now. Clarity comes after this passes.",
        "Notice what keeps coming back. That's the thing to pay attention to.",
        "Don't try to make it make sense yet. Let the picture develop.",
    ],
    "cycle_event": [
        "What you notice today matters. Don't dismiss it as coincidence.",
        "Pay closer attention than usual. Something is trying to land.",
        "This is a day to watch, not to force. Let it reveal itself.",
        "What completes today shapes what begins next. Let it finish properly.",
        "The significance you're feeling is real. Trust that.",
    ],
    "normal_flow": [
        "Use the quiet. It won't last.",
        "Let things settle without forcing movement.",
        "Small adjustments now prevent larger corrections later.",
        "The space is here for a reason. Don't fill it unnecessarily.",
        "Notice what surfaces. It's showing you what's next.",
    ],
}


def generate_cause_from_transit_stack(transit_stack: Dict[str, Any]) -> Dict[str, str]:
    """
    Translate transit stack into plain-language causal explanation.
    
    Returns:
    {
        "cause_statement": str,  # What is causing this
        "effect_statement": str,  # What that creates
        "why_now": str,  # Why specifically today
    }
    """
    transit_type = transit_stack.get("type", "background")
    events = transit_stack.get("events", [])
    interaction_theme = transit_stack.get("interaction_theme", "")
    intensity = transit_stack.get("intensity", 0)
    
    # If we have an interaction theme (stacked transits), use that
    if interaction_theme and interaction_theme in INTERACTION_THEME_CAUSES:
        theme_cause = INTERACTION_THEME_CAUSES[interaction_theme]
        return {
            "cause_statement": theme_cause["cause"],
            "effect_statement": theme_cause["effect"],
            "why_now": theme_cause["why_now"],
        }
    
    # Single transit event
    if transit_type == "single" and events:
        event = events[0] if isinstance(events, list) else events
        event_type = event.get("type", "") if isinstance(event, dict) else str(event)
        
        if event_type in TRANSIT_CAUSE_TEMPLATES:
            template = TRANSIT_CAUSE_TEMPLATES[event_type]
            return {
                "cause_statement": template["base_cause"],
                "effect_statement": template["what_happens"],
                "why_now": template["why_pressure"],
            }
    
    # Stacked transits without specific interaction theme
    if transit_type == "stacked" and len(events) >= 2:
        event_types = [e.get("type", "") if isinstance(e, dict) else str(e) for e in events]
        
        # Build combined cause
        causes = []
        for et in event_types[:2]:  # Max 2 for readability
            if et in TRANSIT_CAUSE_TEMPLATES:
                causes.append(TRANSIT_CAUSE_TEMPLATES[et]["base_cause"].lower())
        
        if causes:
            return {
                "cause_statement": f"{causes[0].capitalize()} while {causes[1]}" if len(causes) > 1 else causes[0].capitalize(),
                "effect_statement": "Multiple transitions are competing for your attention",
                "why_now": "These cycles rarely overlap—when they do, things feel unstable",
            }
    
    # Background/normal - still provide cause
    return {
        "cause_statement": "No major transit events are active",
        "effect_statement": "The usual patterns are running without disruption",
        "why_now": "This is a maintenance window—useful for integration, not initiation",
    }


def generate_experience_hook(day_class: str, transit_stack: Dict[str, Any]) -> str:
    """
    v3: Generate the EXPERIENCE hook - lived experience opener.
    
    Starts with what user is actually experiencing right now.
    """
    hooks = EXPERIENCE_HOOKS.get(day_class, EXPERIENCE_HOOKS["normal_flow"])
    
    # Use date-based seed for consistency within a day
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    hook_index = seed_hash % len(hooks)
    return hooks[hook_index]


def generate_cause_bridge(transit_stack: Dict[str, Any], day_class: str) -> str:
    """
    v3: Generate the CAUSE bridge - human language cause statement.
    
    Translates transit stack into felt experience, not astrology terms.
    """
    interaction_theme = transit_stack.get("interaction_theme", "")
    transit_type = transit_stack.get("type", "background")
    events = transit_stack.get("events", [])
    
    # Use date-based seed for consistency
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    # Priority 1: Interaction theme (stacked transits)
    if interaction_theme and interaction_theme in CAUSE_BRIDGES:
        bridges = CAUSE_BRIDGES[interaction_theme]
        bridge_index = seed_hash % len(bridges)
        return bridges[bridge_index]
    
    # Priority 2: Single transit event
    if events:
        event = events[0] if isinstance(events, list) else events
        event_type = event.get("type", "") if isinstance(event, dict) else str(event)
        
        if event_type in SINGLE_TRANSIT_CAUSES:
            causes = SINGLE_TRANSIT_CAUSES[event_type]
            cause_index = seed_hash % len(causes)
            return causes[cause_index]
    
    # Fallback: Normal flow
    return "The usual rhythms are running. Nothing is forcing itself on you right now."


def generate_guidance_line(day_class: str, transit_stack: Dict[str, Any]) -> str:
    """
    v3: Generate the GUIDANCE line - single actionable statement.
    """
    guidance_options = GUIDANCE_LINES.get(day_class, GUIDANCE_LINES["normal_flow"])
    
    # Use date-based seed for consistency
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    guidance_index = (seed_hash + 2) % len(guidance_options)
    return guidance_options[guidance_index]


def generate_narrative_block(
    transit_stack: Dict[str, Any],
    day_class: str
) -> str:
    """
    v3: Generate ONE continuous narrative block.
    
    Structure:
    1. EXPERIENCE (hook) - lived experience opener
    2. CAUSE (why) - transit in human language
    3. GUIDANCE (what to do) - single actionable line
    
    No sections. No bullet points. One flow.
    """
    experience = generate_experience_hook(day_class, transit_stack)
    cause = generate_cause_bridge(transit_stack, day_class)
    guidance = generate_guidance_line(day_class, transit_stack)
    
    # Build narrative as single flowing block
    narrative = f"{experience}\n\n{cause}\n\n{guidance}"
    
    return narrative


def generate_astrology_snapshot_v2(
    transit_stack: Dict[str, Any],
    day_class: str,
    user_context: Optional[Dict] = None,
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Astrology Today Snapshot v4 - Full Integration.
    
    Structure:
    1. EXPERIENCE (hook)
    2. INTERNAL DYNAMICS (placements as felt experience)
    3. CAUSE (transit stack)
    4. GUIDANCE
    
    Returns ONE coherent narrative, no dual systems.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Generate v4 components
    experience = generate_experience_hook(day_class, transit_stack)
    cause = generate_cause_bridge(transit_stack, day_class)
    guidance = generate_guidance_line(day_class, transit_stack)
    
    # v4: Generate internal dynamics from chart placements
    internal_dynamics = ""
    technical_placements = []  # For "See what's driving this" expandable
    
    if chart_data:
        sun_sign = chart_data.get("sun_sign")
        moon_sign = chart_data.get("moon_sign")
        rising_sign = chart_data.get("rising_sign") or chart_data.get("ascendant_sign")
        sun_house = chart_data.get("sun_house")
        moon_house = chart_data.get("moon_house")
        
        # Generate felt experience from placements
        internal_dynamics = generate_internal_dynamics(
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            rising_sign=rising_sign,
            sun_house=sun_house,
            moon_house=moon_house,
            day_class=day_class
        )
        
        # Store technical for expandable section
        if sun_sign:
            house_str = f" in {sun_house}th house" if sun_house else ""
            technical_placements.append(f"Sun in {sun_sign.title()}{house_str}")
        if moon_sign:
            house_str = f" in {moon_house}th house" if moon_house else ""
            technical_placements.append(f"Moon in {moon_sign.title()}{house_str}")
        if rising_sign:
            technical_placements.append(f"{rising_sign.title()} Rising")
    
    # Build v4 narrative: EXPERIENCE → INTERNAL DYNAMICS → CAUSE → GUIDANCE
    narrative_parts = [experience]
    
    if internal_dynamics:
        narrative_parts.append(internal_dynamics)
    
    narrative_parts.append(cause)
    narrative_parts.append(guidance)
    
    # Join with paragraph breaks
    narrative = "\n\n".join(narrative_parts)
    
    # Build transit summary (human-readable)
    events = transit_stack.get("events", [])
    event_names = []
    for e in events:
        if isinstance(e, dict):
            event_names.append(e.get("name", e.get("type", "unknown")))
        else:
            event_names.append(str(e))
    
    transit_summary = f"Active: {', '.join(event_names)}" if event_names else "No major transits"
    
    # Validate no horoscope language
    if is_horoscope_language(narrative):
        logger.warning("[AstrologyV4] Horoscope language detected in output")
    
    return {
        "success": True,
        "version": "v4_integrated",
        "date": today,
        # v4: Single coherent narrative (primary output)
        "narrative": narrative,
        # Component parts (for debugging)
        "experience": experience,
        "internal_dynamics": internal_dynamics if internal_dynamics else None,
        "cause": cause,
        "guidance": guidance,
        # Technical details for "See what's driving this" expandable
        "technical": {
            "placements": technical_placements if technical_placements else None,
            "transits": event_names if event_names else None,
        } if technical_placements or event_names else None,
        # Metadata
        "day_class": day_class,
        "transit_summary": transit_summary,
        "interaction_theme": transit_stack.get("interaction_theme"),
        "intensity": transit_stack.get("intensity", 0),
        "debug": {
            "transit_type": transit_stack.get("type"),
            "events_count": len(events),
            "interaction_theme": transit_stack.get("interaction_theme"),
            "day_class": day_class,
            "has_chart_data": chart_data is not None,
            "has_internal_dynamics": bool(internal_dynamics),
            "horoscope_check_passed": not is_horoscope_language(narrative),
        }
    }


def format_snapshot_for_display(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    v4: Format for display - single narrative with optional technical expandable.
    """
    return {
        "title": "Today",
        "date": snapshot.get("date"),
        "narrative": snapshot.get("narrative"),
        "day_class": snapshot.get("day_class"),
        # Expandable "See what's driving this"
        "expandable": snapshot.get("technical"),
        "version": "v4_integrated",
    }
