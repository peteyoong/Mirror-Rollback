"""
Astrology Today Snapshot v2 — Causal Layer Architecture

This module generates astrology snapshots with 3 layers:
1. EXPERIENCE - what user feels (clear human tension)
2. CAUSE - what is driving it (transit stack translated to plain language)
3. GUIDANCE - how to relate to it (1-line activation)

NO vague astrology language ("energy", "vibes")
NO generic statements
ALWAYS explain "why now"
Human-readable (no heavy jargon)
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# BANNED ASTROLOGY LANGUAGE - We reject horoscope-style vagueness
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
]


def is_horoscope_language(text: str) -> bool:
    """Check if text contains banned horoscope-style language."""
    text_lower = text.lower()
    return any(term in text_lower for term in BANNED_ASTROLOGY_TERMS)


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

# Day class to experience mapping
DAY_CLASS_EXPERIENCES = {
    "phase_shift": {
        "experiences": [
            "There's pressure to decide something before it's ready.",
            "You want to lock something in, but you can't.",
            "Something is trying to finish before it's actually done.",
            "You feel urgency but the path forward isn't clear.",
            "The ground feels unstable. Nothing is landing.",
        ],
        "tone": "interruptive",
    },
    "cycle_event": {
        "experiences": [
            "Something feels more significant than usual today.",
            "There's weight to decisions that wouldn't normally feel heavy.",
            "You're aware that something is peaking or completing.",
            "Attention is being demanded on something specific.",
            "A pattern you've been watching is becoming obvious.",
        ],
        "tone": "directional",
    },
    "normal_flow": {
        "experiences": [
            "Today feels ordinary but something underneath is moving.",
            "You might notice subtle patterns more than dramatic shifts.",
            "The usual rhythms are running, but with slight variation.",
            "Nothing is forcing itself on your attention today.",
            "Space exists for reflection without pressure.",
        ],
        "tone": "subtle",
    },
}

# Guidance templates by day class
DAY_CLASS_GUIDANCE = {
    "phase_shift": [
        "Don't treat urgency as a signal to decide.",
        "Let the pressure exist without acting on it.",
        "What feels like delay is actually timing.",
        "The answer you want isn't available yet.",
        "Stay with the discomfort instead of resolving it prematurely.",
    ],
    "cycle_event": [
        "Pay attention. This day carries weight.",
        "What you notice today matters more than usual.",
        "Don't dismiss the significance you're feeling.",
        "This window won't stay open indefinitely.",
        "The pattern you're seeing is real.",
    ],
    "normal_flow": [
        "Use the space. It won't last forever.",
        "Notice what's moving underneath the surface.",
        "The quiet is information, not absence.",
        "Small adjustments today prevent larger corrections later.",
        "Let things settle without forcing movement.",
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


def generate_experience_statement(
    day_class: str,
    transit_stack: Dict[str, Any],
    user_signals: Optional[Dict] = None
) -> str:
    """
    Generate the EXPERIENCE layer - what user feels.
    
    Uses day_class as primary driver, with optional user signal influence.
    """
    experiences = DAY_CLASS_EXPERIENCES.get(day_class, DAY_CLASS_EXPERIENCES["normal_flow"])
    experience_options = experiences["experiences"]
    
    # Use date-based seed for consistency within a day
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    # Select experience
    experience_index = seed_hash % len(experience_options)
    return experience_options[experience_index]


def generate_guidance_statement(day_class: str, transit_stack: Dict[str, Any]) -> str:
    """
    Generate the GUIDANCE layer - how to relate to it.
    
    1-line activation based on day class.
    """
    guidance_options = DAY_CLASS_GUIDANCE.get(day_class, DAY_CLASS_GUIDANCE["normal_flow"])
    
    # Use date-based seed for consistency
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    guidance_index = (seed_hash + 1) % len(guidance_options)
    return guidance_options[guidance_index]


def generate_astrology_snapshot_v2(
    transit_stack: Dict[str, Any],
    day_class: str,
    user_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Astrology Today Snapshot v2 with 3-layer causal structure.
    
    Returns:
    {
        "success": True,
        "version": "v2_causal",
        "date": str,
        "experience": {
            "statement": str,
            "tone": str
        },
        "cause": {
            "statement": str,
            "effect": str,
            "why_now": str
        },
        "guidance": str,
        "day_class": str,
        "transit_summary": str,
        "debug": {...}
    }
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Generate EXPERIENCE layer
    experience_statement = generate_experience_statement(day_class, transit_stack)
    experience_tone = DAY_CLASS_EXPERIENCES.get(day_class, {}).get("tone", "subtle")
    
    # Generate CAUSE layer
    cause_data = generate_cause_from_transit_stack(transit_stack)
    
    # Generate GUIDANCE layer
    guidance_statement = generate_guidance_statement(day_class, transit_stack)
    
    # Build transit summary (human-readable)
    events = transit_stack.get("events", [])
    event_names = []
    for e in events:
        if isinstance(e, dict):
            event_names.append(e.get("name", e.get("type", "unknown")))
        else:
            event_names.append(str(e))
    
    if event_names:
        transit_summary = f"Active: {', '.join(event_names)}"
    else:
        transit_summary = "No major transits active"
    
    # Validate no horoscope language slipped through
    all_text = f"{experience_statement} {cause_data['cause_statement']} {guidance_statement}"
    if is_horoscope_language(all_text):
        logger.warning("[AstrologyV2] Horoscope language detected in output")
    
    return {
        "success": True,
        "version": "v2_causal",
        "date": today,
        "experience": {
            "statement": experience_statement,
            "tone": experience_tone,
        },
        "cause": {
            "statement": cause_data["cause_statement"],
            "effect": cause_data["effect_statement"],
            "why_now": cause_data["why_now"],
        },
        "guidance": guidance_statement,
        "day_class": day_class,
        "transit_summary": transit_summary,
        "interaction_theme": transit_stack.get("interaction_theme"),
        "intensity": transit_stack.get("intensity", 0),
        "debug": {
            "transit_type": transit_stack.get("type"),
            "events_count": len(events),
            "interaction_theme": transit_stack.get("interaction_theme"),
            "day_class": day_class,
            "horoscope_check_passed": not is_horoscope_language(all_text),
        }
    }


def format_snapshot_for_display(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the v2 snapshot for frontend display.
    
    Returns a structure optimized for rendering.
    """
    return {
        "title": "Today's Snapshot",
        "date": snapshot.get("date"),
        "sections": [
            {
                "label": "What You're Feeling",
                "body": snapshot["experience"]["statement"],
            },
            {
                "label": "Why This Is Happening",
                "body": f"{snapshot['cause']['statement']}. {snapshot['cause']['effect']}",
            },
            {
                "label": "How to Work With It",
                "body": snapshot["guidance"],
            },
        ],
        "transit_info": snapshot.get("transit_summary"),
        "day_class": snapshot.get("day_class"),
        "version": "v2_causal",
    }
