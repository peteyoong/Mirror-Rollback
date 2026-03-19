"""
Astrology Today Snapshot v5 — Mirror Language Alignment

Every line must feel like: "That's exactly what I'm doing / feeling right now"

Rules:
- Direct "you" language (not "one may feel")
- Observable behavior (what user is DOING)
- Felt tension (what's uncomfortable)
- Internal split ("Part of you... another part...")

NO abstract terms (recalibrating, inner compass, meaningful, reflective)
NO observer language ("may notice", "can feel like")
NO soft/general phrasing

Quality validation before output: if not Mirror-style, REWRITE.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# v5: BANNED LANGUAGE - Expanded for Mirror alignment
# =============================================================================

BANNED_TERMS = [
    # Horoscope vagueness
    "energy", "energies", "vibes", "vibrations",
    "universe", "cosmic", "celestial",
    "alignment", "aligned",
    "manifest", "manifestation",
    "flow", "flowing",
    "embrace", "embracing",
    "journey", "powerful",
    "transformation", "transformative",
    "awakening",
    # Abstract concepts
    "internal compass", "compass",
    "recalibrating", "recalibrate",
    "reflective", "reflection",
    "meaningful", "significance",
    "porous", "permeable",
    "inner world", "inner landscape",
    "emotional current",
    # Observer language
    "you may notice",
    "you may feel",
    "you might find",
    "can feel like",
    "tends to",
    "often feels",
    "there's a sense",
    "a quality of",
]

# Soft modifiers to remove
SOFT_MODIFIERS = ["may", "might", "can", "could", "perhaps", "possibly", "sometimes", "often", "tends"]


def validate_mirror_style(text: str) -> Dict[str, Any]:
    """
    v5: Validate text matches Mirror language style.
    
    Returns: {"valid": bool, "issues": list, "must_rewrite": bool}
    """
    issues = []
    text_lower = text.lower()
    
    # Check banned terms
    for term in BANNED_TERMS:
        if term in text_lower:
            issues.append(f"BANNED: '{term}'")
    
    # Check soft modifiers at start of clauses
    for mod in SOFT_MODIFIERS:
        if f"you {mod}" in text_lower or f". {mod}" in text_lower:
            issues.append(f"SOFT_MODIFIER: 'you {mod}'")
    
    # Check for abstract language patterns
    abstract_patterns = [
        r"a sense of",
        r"quality of",
        r"there'?s? something",
        r"in the air",
        r"atmosphere",
    ]
    for pattern in abstract_patterns:
        if re.search(pattern, text_lower):
            issues.append(f"ABSTRACT: pattern '{pattern}'")
    
    # Check for direct "you" statements (GOOD)
    has_direct_you = "you " in text_lower or "you'" in text_lower
    if not has_direct_you:
        issues.append("MISSING: Direct 'you' language")
    
    # Determine if rewrite needed
    must_rewrite = len([i for i in issues if "BANNED" in i or "SOFT_MODIFIER" in i]) > 0
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "must_rewrite": must_rewrite,
    }


# =============================================================================
# v5: EXPERIENCE HOOKS - Behavior-based, immediately recognizable
# =============================================================================

EXPERIENCE_HOOKS_V5 = {
    "phase_shift": [
        "You keep almost deciding, then pulling back. Part of you wants it settled. Another part knows it's not ready.",
        "You're replaying something. A conversation, a message, a moment. You're trying to figure out what it actually meant.",
        "You want to act, but you can't find the right move. So you wait. And the waiting feels worse than being wrong would.",
        "You've checked your phone three times in the last hour. You're waiting for something to land. It hasn't.",
        "Part of you wants to force a conclusion. Another part knows that forcing it will break something.",
    ],
    "cycle_event": [
        "Something keeps coming back into your head. The same thought. The same question. You're not done with it yet.",
        "You're more aware than usual. Small things feel heavier. You're not imagining it.",
        "You've been putting something off. Today it's harder to ignore. It keeps surfacing.",
        "You're noticing patterns. The same kind of conversation. The same feeling. It's not random.",
        "Something is asking for your attention. You've been looking away. Today you can't.",
    ],
    "normal_flow": [
        "You're running through your day, but something underneath keeps pulling. You're not sure what.",
        "You catch yourself thinking about something without meaning to. It comes back. Again.",
        "Nothing urgent is happening, but you're not settled either. There's something you're not looking at.",
        "You're doing the usual things, but your mind keeps drifting. Somewhere else wants your attention.",
        "Part of you is here. Another part is somewhere else. You keep losing focus.",
    ],
}

# =============================================================================
# v5: PLACEMENT DYNAMICS - Behavior-based (not traits)
# =============================================================================

SUN_DYNAMICS_V5 = {
    "aries": "You act first, think later. Then you wonder if you moved too fast.",
    "taurus": "You dig in. You don't want to be pushed. And right now, something is pushing.",
    "gemini": "You're running three conversations in your head. None of them are finished.",
    "cancer": "You're protecting something. You're not sure if it needs protecting or if you're just scared.",
    "leo": "You want to be seen. But not like this. Not until you figure out how you want to show up.",
    "virgo": "You're scanning for what's wrong. You found something. Now you can't stop thinking about it.",
    "libra": "You're waiting for someone else to decide. Part of you knows that's not fair to either of you.",
    "scorpio": "You know more than you're saying. You're watching. You're waiting to see what they do next.",
    "sagittarius": "You want out. You want something bigger. But you're stuck here for now.",
    "capricorn": "You're carrying more than you should. You won't put it down. You don't trust anyone else to hold it.",
    "aquarius": "You're watching this from the outside. Part of you doesn't want to get involved. Another part already is.",
    "pisces": "You're picking up everything. Other people's moods. The tension in the room. You can't turn it off.",
}

MOON_DYNAMICS_V5 = {
    "aries": "You react fast. Then you wonder if that was too much. Then you get mad at yourself for wondering.",
    "taurus": "You need things to stay where you put them. Right now, they're not. And that's making you anxious.",
    "gemini": "Your feelings keep changing. You're not sure which one is real. Maybe all of them.",
    "cancer": "You're holding onto something. A feeling. A memory. A hope. You're not ready to let go.",
    "leo": "You need to know you matter. Right now, you're not sure. And that's eating at you.",
    "virgo": "You're worried about getting it wrong. The feeling won't go away even when you've checked twice.",
    "libra": "You need peace. But getting it means saying something difficult. So you stay quiet. And tense.",
    "scorpio": "Something is churning underneath. You're not ready to name it. But it's there.",
    "sagittarius": "You want to feel free. Instead you feel trapped. And restless. And slightly angry.",
    "capricorn": "You don't let yourself feel until everything is handled. Nothing is handled right now.",
    "aquarius": "You're disconnected from what you're feeling. You're watching your own emotions from a distance.",
    "pisces": "You absorb everything. You're not sure which feelings are yours anymore.",
}

RISING_DYNAMICS_V5 = {
    "aries": "You show up ready to move. Right now, nothing is moving. And that's frustrating.",
    "taurus": "You take your time. Other people want you to hurry. You're resisting that.",
    "gemini": "You're presenting multiple versions of yourself. You're not sure which one is landing.",
    "cancer": "You approach things carefully. You're testing whether it's safe before you open up.",
    "leo": "You walk in expecting to be noticed. Sometimes you are. Sometimes you're not. Today it stings.",
    "virgo": "You're noticing every detail. You're cataloging what's wrong. You can't help it.",
    "libra": "You're smoothing things over. You're keeping the peace. It's costing you something.",
    "scorpio": "You're not showing your hand. You're watching first. You're deciding who gets to see you.",
    "sagittarius": "Part of you wants to stay. Another part is already planning the exit.",
    "capricorn": "You're handling it. You're always handling it. Even when you're tired.",
    "aquarius": "You do things your own way. Right now, someone wants you to do it their way. You're resisting.",
    "pisces": "You're absorbing the room before you decide how to show up. It takes a moment.",
}

# =============================================================================
# v5: CAUSE BRIDGES - Simple, no jargon
# =============================================================================

CAUSE_BRIDGES_V5 = {
    "reset_at_threshold": [
        "Two things are happening at once: something is ending and something is trying to start. That's why nothing feels settled.",
        "A reset and a turning point landed on the same day. That's why you can't find solid ground.",
        "An ending and a beginning are overlapping. Your system is processing both at once.",
    ],
    "portal_opening": [
        "Multiple things want to begin. None of them have your full attention. That's the split you're feeling.",
        "Too many starting points. Not enough clarity. That's why you feel scattered.",
        "Several doors opened at once. You're standing in the hallway, not sure which one to walk through.",
    ],
    "culmination_at_threshold": [
        "Something is completing right when everything else is shifting. That's the pressure.",
        "An ending is happening during a transition. You're being asked to close and open at the same time.",
        "Completion and change collided. That's why this moment feels heavy.",
    ],
    "destabilization_window": [
        "The usual rules aren't working right now. That's not a failure. That's the window you're in.",
        "What normally holds isn't holding. That's the instability you're feeling.",
        "Things are looser than usual. Boundaries are softer. That's the moment.",
    ],
    "deep_release": [
        "Something old is trying to leave. The weight you feel is the last bit of holding on.",
        "You're at the edge of a release. The discomfort is the resistance before it goes.",
        "What you've been carrying is ready to drop. The pressure is the final grip.",
    ],
    "peak_illumination": [
        "Everything is visible right now. You can see what you've been avoiding.",
        "The picture is clear. That's not always comfortable, but it's true.",
        "Maximum clarity landed. What you see is what's there.",
    ],
    "emotional_culmination": [
        "Feelings that have been building are cresting. You're at the top of the wave.",
        "Emotional pressure built to a peak. That's why small things feel big.",
        "What you're feeling has been accumulating. Today it's surfacing.",
    ],
    "multiple_events_active": [
        "Several things are active at once. That's why there's no single clear signal.",
        "Multiple forces are pulling. The confusion is because there isn't one answer right now.",
        "Different cycles are overlapping. You're navigating more than one thing.",
    ],
}

# Single transit causes
SINGLE_CAUSES_V5 = {
    "new_moon": [
        "A cycle is starting. The slate is blank. That's both freeing and disorienting.",
        "Something new is beginning. You can feel the space where the old thing used to be.",
        "A reset is happening. Your system is wiping clean before the next thing.",
    ],
    "full_moon": [
        "What's been building is now fully visible. You can see the whole picture.",
        "Something is completing. The pressure to resolve is real.",
        "Maximum visibility. What you've been working toward is showing its results.",
    ],
    "equinox": [
        "A turning point. What worked before might need adjustment now.",
        "The system is rebalancing. Old momentum meeting new direction.",
        "You're at a pivot. The shift is happening whether you're ready or not.",
    ],
    "solstice": [
        "You're at an extreme. Maximum stretch in one direction. Something has to give.",
        "Peak point. The furthest extension before reversal.",
        "The limit has been reached. What comes next is the turn.",
    ],
}

# =============================================================================
# v5: GUIDANCE LINES - Direct, grounded instructions
# =============================================================================

GUIDANCE_V5 = {
    "phase_shift": [
        "Don't decide yet. Let the pressure exist without acting on it.",
        "Stop trying to make it make sense. It doesn't yet. That's okay.",
        "The urge to close this is strong. Don't. It's not ready.",
        "Name what you're feeling, not what you should do about it.",
        "Part of you wants this over. That part doesn't have all the information yet.",
    ],
    "cycle_event": [
        "Pay attention. What you notice today matters more than usual.",
        "Don't dismiss what keeps coming back. It's trying to tell you something.",
        "This day has weight. Don't sleepwalk through it.",
        "What completes today shapes what starts next. Let it finish.",
        "The thing you keep avoiding? Look at it. Just look.",
    ],
    "normal_flow": [
        "Use the quiet. It won't last.",
        "Notice what your mind keeps returning to. That's the thing.",
        "Small adjustments now. Before it becomes a bigger correction.",
        "You have space. Don't fill it with noise.",
        "The thing underneath? Let it surface. You don't have to do anything with it yet.",
    ],
}


# =============================================================================
# v5: GENERATION FUNCTIONS
# =============================================================================

def generate_experience_hook_v5(day_class: str) -> str:
    """Generate v5 experience hook - behavior-based, immediately recognizable."""
    hooks = EXPERIENCE_HOOKS_V5.get(day_class, EXPERIENCE_HOOKS_V5["normal_flow"])
    
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    return hooks[seed_hash % len(hooks)]


def generate_internal_dynamics_v5(
    sun_sign: str = None,
    moon_sign: str = None,
    rising_sign: str = None,
    day_class: str = "normal_flow"
) -> str:
    """
    v5: Generate internal dynamics from placements as BEHAVIOR (not traits).
    
    Uses internal split language: "Part of you... another part..."
    """
    dynamics = []
    
    if moon_sign and moon_sign.lower() in MOON_DYNAMICS_V5:
        dynamics.append(("moon", MOON_DYNAMICS_V5[moon_sign.lower()]))
    
    if sun_sign and sun_sign.lower() in SUN_DYNAMICS_V5:
        dynamics.append(("sun", SUN_DYNAMICS_V5[sun_sign.lower()]))
    
    if rising_sign and rising_sign.lower() in RISING_DYNAMICS_V5:
        dynamics.append(("rising", RISING_DYNAMICS_V5[rising_sign.lower()]))
    
    if not dynamics:
        return ""
    
    # Priority: Moon for phase_shift (emotional), Sun for cycle_event (identity)
    if day_class == "phase_shift":
        priority = ["moon", "sun", "rising"]
    elif day_class == "cycle_event":
        priority = ["sun", "moon", "rising"]
    else:
        priority = ["rising", "moon", "sun"]
    
    dynamics_sorted = sorted(dynamics, key=lambda x: priority.index(x[0]) if x[0] in priority else 99)
    
    # Take top 1-2
    selected = [d[1] for d in dynamics_sorted[:2]]
    
    if len(selected) == 2:
        return f"{selected[0]} {selected[1]}"
    elif len(selected) == 1:
        return selected[0]
    
    return ""


def generate_cause_bridge_v5(transit_stack: Dict[str, Any]) -> str:
    """v5: Generate cause - simple, no jargon."""
    interaction_theme = transit_stack.get("interaction_theme", "")
    events = transit_stack.get("events", [])
    
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    # Priority 1: Interaction theme
    if interaction_theme and interaction_theme in CAUSE_BRIDGES_V5:
        causes = CAUSE_BRIDGES_V5[interaction_theme]
        return causes[seed_hash % len(causes)]
    
    # Priority 2: Single transit
    if events:
        event = events[0] if isinstance(events, list) else events
        event_type = event.get("type", "") if isinstance(event, dict) else str(event)
        
        if event_type in SINGLE_CAUSES_V5:
            causes = SINGLE_CAUSES_V5[event_type]
            return causes[seed_hash % len(causes)]
    
    # Fallback
    return "The usual rhythms are running. Nothing is forcing itself on you right now."


def generate_guidance_v5(day_class: str) -> str:
    """v5: Generate guidance - direct, grounded."""
    guidance = GUIDANCE_V5.get(day_class, GUIDANCE_V5["normal_flow"])
    
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    return guidance[(seed_hash + 2) % len(guidance)]


def generate_astrology_snapshot_v2(
    transit_stack: Dict[str, Any],
    day_class: str,
    user_context: Optional[Dict] = None,
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Astrology Today Snapshot v5 — Mirror Language Alignment.
    
    Every line must feel like: "That's exactly what I'm doing"
    
    Returns ONE coherent narrative with quality validation.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Generate v5 components
    experience = generate_experience_hook_v5(day_class)
    cause = generate_cause_bridge_v5(transit_stack)
    guidance = generate_guidance_v5(day_class)
    
    # Generate internal dynamics if chart data available
    internal_dynamics = ""
    technical_placements = []
    
    if chart_data:
        sun_sign = chart_data.get("sun_sign")
        moon_sign = chart_data.get("moon_sign")
        rising_sign = chart_data.get("rising_sign")
        
        internal_dynamics = generate_internal_dynamics_v5(
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            rising_sign=rising_sign,
            day_class=day_class
        )
        
        if sun_sign:
            technical_placements.append(f"{sun_sign.title()} Sun")
        if moon_sign:
            technical_placements.append(f"{moon_sign.title()} Moon")
        if rising_sign:
            technical_placements.append(f"{rising_sign.title()} Rising")
    
    # Build narrative: EXPERIENCE → INTERNAL DYNAMICS → CAUSE → GUIDANCE
    narrative_parts = [experience]
    
    if internal_dynamics:
        narrative_parts.append(internal_dynamics)
    
    narrative_parts.append(cause)
    narrative_parts.append(guidance)
    
    narrative = "\n\n".join(narrative_parts)
    
    # v5: QUALITY VALIDATION - must match Mirror style
    validation = validate_mirror_style(narrative)
    
    if validation["must_rewrite"]:
        logger.warning(f"[AstrologyV5] Quality check failed: {validation['issues']}")
        # If validation fails, use hardcoded safe fallback
        narrative = f"""You keep almost deciding, then pulling back. Part of you wants it settled. Another part knows it's not ready.

{cause}

{guidance}"""
        validation = validate_mirror_style(narrative)
    
    # Build transit summary
    events = transit_stack.get("events", [])
    event_names = [
        e.get("name", e.get("type", "unknown")) if isinstance(e, dict) else str(e)
        for e in events
    ]
    transit_summary = f"Active: {', '.join(event_names)}" if event_names else "No major transits"
    
    return {
        "success": True,
        "version": "v5_mirror_aligned",
        "date": today,
        # v5: Single narrative only (no section labels)
        "narrative": narrative,
        # Components for debugging
        "experience": experience,
        "internal_dynamics": internal_dynamics if internal_dynamics else None,
        "cause": cause,
        "guidance": guidance,
        # Technical for expandable
        "technical": {
            "placements": technical_placements if technical_placements else None,
            "transits": event_names if event_names else None,
        } if technical_placements or event_names else None,
        # Metadata
        "day_class": day_class,
        "transit_summary": transit_summary,
        "interaction_theme": transit_stack.get("interaction_theme"),
        "intensity": transit_stack.get("intensity", 0),
        "validation": validation,
        "debug": {
            "transit_type": transit_stack.get("type"),
            "events_count": len(events),
            "interaction_theme": transit_stack.get("interaction_theme"),
            "day_class": day_class,
            "has_chart_data": chart_data is not None,
            "has_internal_dynamics": bool(internal_dynamics),
            "quality_check_passed": validation["valid"],
        }
    }


def format_snapshot_for_display(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """v5: Format for display - narrative only, no section labels."""
    return {
        "title": "Today",
        "date": snapshot.get("date"),
        "narrative": snapshot.get("narrative"),
        "expandable": snapshot.get("technical"),
        "version": "v5_mirror_aligned",
    }
