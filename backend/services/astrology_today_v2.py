"""
Astrology Today Snapshot v6 — Real Thought Pattern Layer

Output must feel like:
- the user's actual thoughts
- slightly messy, not perfectly structured
- interruptive, not explanatory

Rules:
- Less perfect sentences (thought fragments)
- Replace descriptions with motivation (WHY they're doing it)
- Remove explanation tone from cause
- Add context hook (messages, decisions, conversations)
- Must feel like inner dialogue, not well-written paragraph

Quality check: If it sounds written → REWRITE. If it feels like a thought → PASS.
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
# v6: EXPERIENCE HOOKS - Thought fragments, real-time thinking
# =============================================================================
# Less perfect sentences. Slightly messy. Like actual thoughts.

EXPERIENCE_HOOKS_V5 = {
    "phase_shift": [
        "You try to decide. Then something feels off. You pull back. Then you try again. It keeps happening.",
        "You want this done. You just want to stop thinking about it. But something won't let you close it.",
        "You've been here before — almost ready to move, then not. The loop is getting old.",
        "There's a decision sitting there. You keep circling it. You don't land.",
        "Part of you says just do it. Another part says wait. Neither one wins.",
    ],
    "cycle_event": [
        "The same thought keeps coming back. You push it away. It returns. There's something there.",
        "Today feels different. Heavier. You're not imagining it.",
        "You've been avoiding something. Today it's louder. Harder to ignore.",
        "Small things are catching your attention. They don't feel small.",
        "Something wants you to look at it. You've been looking away. That's getting harder.",
    ],
    "normal_flow": [
        "Nothing urgent. But you're not settled either. Something is there, underneath.",
        "You keep drifting. Your mind goes somewhere else. You pull it back. It drifts again.",
        "You're here, doing the thing. But part of you is somewhere else.",
        "The day is fine. Regular. But something keeps tugging. You don't know what.",
        "You lose focus. Catch yourself somewhere else. Come back. It happens again.",
    ],
}

# =============================================================================
# v6: CONTEXT HOOKS - Real-life connection (mandatory)
# =============================================================================
# Messages, decisions, conversations, delays

CONTEXT_HOOKS_V6 = {
    "phase_shift": [
        "You see it in the messages you haven't replied to. The decisions you keep pushing.",
        "It shows up in small places — texts sitting there, things half-started, nothing finished.",
        "There's probably a conversation you're putting off. A decision that keeps getting delayed.",
        "Look at what you're avoiding. The email. The call. The thing you keep saying 'later' to.",
        "It's in the tabs still open. The draft not sent. The thing you'll 'get to tomorrow.'",
    ],
    "cycle_event": [
        "You notice it in conversations. The same topic keeps surfacing. It's not random.",
        "There's something you've been meaning to address. Today it's harder to sidestep.",
        "Look at what keeps coming up. In your head. In your messages. In what people say to you.",
        "It's showing up in what you're reading, watching, overhearing. The theme is there.",
        "Pay attention to what you've said 'I should really...' about. That's the thing.",
    ],
    "normal_flow": [
        "You might notice it in what you're scrolling. What you're reaching for without thinking.",
        "It's there in the pauses. The moments between tasks. Where your mind goes.",
        "Look at what you did when you didn't have to do anything. That tells you something.",
        "The thing you keep thinking about when you're doing something else. That's it.",
        "Notice what you're putting off that doesn't need to be put off. There's information there.",
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
# v6: CAUSE BRIDGES - Fragmented, not explanation
# =============================================================================
# Remove "Two things are happening" → "Something is ending. Something else is starting."

CAUSE_BRIDGES_V5 = {
    "reset_at_threshold": [
        "Something is ending. Something else is trying to start. They don't line up yet. That's the tension.",
        "A chapter closing. A new one opening. Both at once. That's why nothing lands.",
        "Reset happening. Shift happening. Same time. No wonder you can't find your footing.",
    ],
    "portal_opening": [
        "Too many things want to begin. You can't give them all attention. Something has to wait.",
        "Several doors. All open. You're standing in the middle. Not moving.",
        "Start here. Or here. Or here. You can't do all of them. That's the jam.",
    ],
    "culmination_at_threshold": [
        "Something finishing. Something shifting. Both at once. Heavy.",
        "Ending and beginning colliding. That's the weight you feel.",
        "Close this. Open that. Same moment. It's a lot.",
    ],
    "destabilization_window": [
        "The usual rules? Not working. That's the window you're in.",
        "What normally holds isn't holding. You're not doing it wrong. Things are just loose right now.",
        "The ground shifted. You didn't imagine it.",
    ],
    "deep_release": [
        "Something old is ready to go. You're still gripping. That's the pressure.",
        "The weight you feel? It's the last bit of holding on. It wants to drop.",
        "You're at the edge of letting go. The discomfort is the resistance.",
    ],
    "peak_illumination": [
        "Everything visible. Can't unsee it. That's today.",
        "The picture is clear now. Uncomfortable, but clear.",
        "Full view. No hiding. You see what's there.",
    ],
    "emotional_culmination": [
        "Feelings built up. Now they're cresting. Small things feel big because they are.",
        "Emotional pressure peaked. That's why you're raw.",
        "What you're feeling has been accumulating. Today it surfaces.",
    ],
    "multiple_events_active": [
        "Several things pulling at once. No single answer. That's the confusion.",
        "Multiple forces. Different directions. No wonder you're scattered.",
        "It's not one thing. It's several. All at once. Makes sense you can't land.",
    ],
}

# Single transit causes
SINGLE_CAUSES_V5 = {
    "new_moon": [
        "New cycle starting. Old one ended. The gap between feels weird.",
        "Blank slate. The old thing is gone. The new thing hasn't formed yet.",
        "Reset. Clean. Also disorienting.",
    ],
    "full_moon": [
        "Everything visible now. What's been building is showing itself.",
        "Full picture. Can't pretend anymore. You see it.",
        "Peak. Whatever was growing is here now.",
    ],
    "equinox": [
        "Turning point. Old direction meeting new one. Friction.",
        "Shift happening. What worked before might not work now.",
        "The system is rebalancing. You're in the wobble.",
    ],
    "solstice": [
        "Extreme point. Something has to give.",
        "Furthest stretch in one direction. Turn coming.",
        "The limit. You're there. Now what?",
    ],
}

# =============================================================================
# v6: GUIDANCE LINES - Direct, interruptive
# =============================================================================

GUIDANCE_V5 = {
    "phase_shift": [
        "Don't decide. Not yet. Let it sit.",
        "Stop trying to close it. It's not ready.",
        "The loop you're in? That's the answer for now. Stay in it.",
        "You want it done. Fine. But done isn't available today.",
        "Name what you feel. Don't fix it. Just name it.",
    ],
    "cycle_event": [
        "Look at the thing you keep avoiding. Just look.",
        "What keeps coming back? Pay attention to that.",
        "Don't dismiss it. It's not random.",
        "The weight is real. Stop pretending it's not.",
        "Whatever you've been putting off. Today's the day to at least acknowledge it.",
    ],
    "normal_flow": [
        "Use the space. It won't last.",
        "Notice where your mind keeps going. There's something there.",
        "The quiet isn't nothing. Something's processing.",
        "Don't fill the gap. Let it be a gap.",
        "What you're avoiding? You don't have to do it. But notice you're avoiding it.",
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
    """v6: Generate guidance - direct, interruptive."""
    guidance = GUIDANCE_V5.get(day_class, GUIDANCE_V5["normal_flow"])
    
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    return guidance[(seed_hash + 2) % len(guidance)]


def generate_context_hook_v6(day_class: str) -> str:
    """v6: Generate context hook - connects to real-life situations (mandatory)."""
    hooks = CONTEXT_HOOKS_V6.get(day_class, CONTEXT_HOOKS_V6["normal_flow"])
    
    date_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(date_seed.encode()).hexdigest()[:8], 16)
    
    return hooks[(seed_hash + 3) % len(hooks)]


def validate_thought_pattern(text: str) -> Dict[str, Any]:
    """
    v6: Validate text feels like inner dialogue, not well-written paragraph.
    
    If it sounds written → FAIL
    If it feels like a thought → PASS
    """
    issues = []
    text_lower = text.lower()
    
    # Check banned terms (from v5)
    for term in BANNED_TERMS:
        if term in text_lower:
            issues.append(f"BANNED: '{term}'")
    
    # Check for overly clean phrasing (too polished)
    polished_markers = [
        "this is because",
        "that's why",
        "as a result",
        "therefore",
        "consequently",
        "in other words",
        "to put it simply",
    ]
    for marker in polished_markers:
        if marker in text_lower:
            issues.append(f"TOO_POLISHED: '{marker}'")
    
    # Check for thought fragment patterns (GOOD)
    fragment_markers = [".", "—", "?"]
    sentence_count = len([s for s in text.split('.') if s.strip()])
    has_short_sentences = any(len(s.strip().split()) <= 6 for s in text.split('.') if s.strip())
    
    if not has_short_sentences and sentence_count > 2:
        issues.append("TOO_SMOOTH: No short thought fragments")
    
    # Check for direct "you" (required)
    if "you " not in text_lower and "you'" not in text_lower:
        issues.append("MISSING: Direct 'you' language")
    
    # Determine severity
    must_rewrite = len([i for i in issues if "BANNED" in i]) > 0
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "must_rewrite": must_rewrite,
        "feels_like_thought": has_short_sentences and "you " in text_lower,
    }


def generate_astrology_snapshot_v2(
    transit_stack: Dict[str, Any],
    day_class: str,
    user_context: Optional[Dict] = None,
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Astrology Today Snapshot v6 — Real Thought Pattern Layer.
    
    Output must feel like:
    - inner dialogue
    - slightly messy but clear
    - immediately recognizable
    - not "written well" but "felt true"
    
    Returns ONE coherent narrative with quality validation.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Generate v6 components
    experience = generate_experience_hook_v5(day_class)
    cause = generate_cause_bridge_v5(transit_stack)
    guidance = generate_guidance_v5(day_class)
    context_hook = generate_context_hook_v6(day_class)  # v6: mandatory context hook
    
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
    
    # v6: Build narrative: EXPERIENCE → CONTEXT → INTERNAL DYNAMICS → CAUSE → GUIDANCE
    narrative_parts = [experience]
    
    # Add context hook after experience (grounds it in real life)
    narrative_parts.append(context_hook)
    
    if internal_dynamics:
        narrative_parts.append(internal_dynamics)
    
    narrative_parts.append(cause)
    narrative_parts.append(guidance)
    
    narrative = "\n\n".join(narrative_parts)
    
    # v6: QUALITY VALIDATION - must feel like thought, not written
    validation = validate_thought_pattern(narrative)
    
    if validation["must_rewrite"]:
        logger.warning(f"[AstrologyV6] Quality check failed: {validation['issues']}")
        # If validation fails, use hardcoded safe fallback
        narrative = f"""You try to decide. Then something feels off. You pull back. Then you try again.

{context_hook}

{cause}

{guidance}"""
        validation = validate_thought_pattern(narrative)
    
    # Build transit summary
    events = transit_stack.get("events", [])
    event_names = [
        e.get("name", e.get("type", "unknown")) if isinstance(e, dict) else str(e)
        for e in events
    ]
    transit_summary = f"Active: {', '.join(event_names)}" if event_names else "No major transits"
    
    return {
        "success": True,
        "version": "v6_thought_pattern",
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
        "version": "v6_thought_pattern",
    }
