"""
Astrology Snapshot 3-Altitude System
=====================================

Three distinct narrative altitudes:
- TODAY: Immediate lived experience
- THIS WEEK: Repeating pattern / resurfacing dynamic  
- THIS MONTH: Developmental arc / what this phase is teaching

CRITICAL RULE: Each altitude MUST sound different.
If all 3 sound like paraphrases of the same thing, the implementation failed.

Transit Intelligence:
- Layer 0: Transit stack detection
- Sky events influence each altitude differently
- Single transit focus per altitude (no overlap)
"""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# =============================================================================
# TODAY HOOKS - Immediate, fractured thought rhythm
# =============================================================================
# MOST PERSONAL. Shortest. What you're doing RIGHT NOW.
# Should feel like: "this is me, right now"

TODAY_HOOKS = {
    "phase_shift": [
        "You try to decide. Then pull back. Then try again.",
        "You want this done. Something keeps blocking you.",
        "Part of you says move. Another part won't.",
        "You keep checking the thing. Not doing the thing.",
        "Every option feels slightly wrong.",
    ],
    "cycle_event": [
        "The same thought returns. You push it away. It returns.",
        "Today feels heavier than yesterday.",
        "Something wants your attention.",
        "Small things are landing harder.",
        "You can feel something unfinished.",
    ],
    "normal_flow": [
        "Part of you is somewhere else.",
        "You keep drifting. Pulling back. Drifting again.",
        "Nothing urgent. But not settled.",
        "The day is fine. Something keeps tugging.",
        "Running on autopilot. Present, but absent.",
    ],
}

TODAY_CONTEXT = {
    "phase_shift": [
        "The message you keep not answering. The draft not sent. That's it.",
        "The tabs still open. The decision not made.",
        "Check what you're scrolling past.",
        "The thing you keep saying 'later' to — look at it.",
        "The unfinished thing is the signal.",
    ],
    "cycle_event": [
        "What keeps coming up in conversations? That.",
        "The topic you keep circling back to.",
        "What did you wake up thinking about?",
        "The thing you've been putting off is louder today.",
        "What have you said 'I should really...' about?",
    ],
    "normal_flow": [
        "Where does your mind go when you're not directing it?",
        "What did you reach for in a free moment?",
        "The pause between tasks — what shows up?",
        "What are you avoiding that doesn't need avoiding?",
        "What you're not doing is telling you something.",
    ],
}

TODAY_GUIDANCE = {
    "phase_shift": [
        "Don't decide. Not yet.",
        "The loop is the answer for now.",
        "Stop trying to close it.",
        "Name what you feel. Don't fix it.",
        "Done isn't available today.",
    ],
    "cycle_event": [
        "Just look at it.",
        "Don't dismiss it.",
        "The weight is real.",
        "At least acknowledge it.",
        "Let it be heavy.",
    ],
    "normal_flow": [
        "Use the space. It won't last.",
        "Something's processing.",
        "Don't fill the gap.",
        "Notice where attention goes.",
        "You don't have to act. Just notice.",
    ],
}


# =============================================================================
# WEEK HOOKS - Pattern recognition, what keeps returning
# =============================================================================
# WIDER RHYTHM. What repeats AFTER the first reaction fades.
# Should feel like: "this keeps coming back"

WEEK_HOOKS = {
    "phase_shift": [
        "Same choice, different day. You've run through this before.",
        "The decision you didn't make earlier in the week? Still here.",
        "Every few days, it resurfaces. You don't pick. It returns.",
        "Forward or stay. You keep arriving at this fork.",
        "You almost decide. Then don't. The pattern holds.",
    ],
    "cycle_event": [
        "There's something cycling through. You've noticed it more than once.",
        "The same feeling keeps showing up in different situations.",
        "A theme is running underneath this week.",
        "Different triggers, same reaction. That's a signal.",
        "The thing you felt on Monday? It's still here Friday.",
    ],
    "normal_flow": [
        "A quiet thread runs through the week. Not loud, but present.",
        "The same thought keeps surfacing at odd moments.",
        "Something small keeps catching your attention.",
        "There's a background hum. You've half-noticed it.",
        "The week has a theme. You can feel it without naming it.",
    ],
}

WEEK_CONTEXT = {
    "phase_shift": [
        "Count how many times you've said 'I'll figure it out later.'",
        "Look at what you've postponed. It's been on your list for days.",
        "How many versions of this decision have you played out in your head?",
        "The reply you didn't send earlier this week — still waiting.",
        "Track where you keep getting stuck. That's the real location.",
    ],
    "cycle_event": [
        "The same topic keeps surfacing with different people.",
        "What bothered you earlier this week? Still there? Unprocessed?",
        "There's a conversation you've been meaning to have.",
        "What did you promise yourself you'd handle? Is it handled?",
        "The pattern shows up when you're not working.",
    ],
    "normal_flow": [
        "What keeps coming back in your free moments?",
        "Look at what you've mentioned to others more than once.",
        "The background thought is actually foreground. You're just not listening.",
        "Pay attention to what returns when you stop directing.",
        "There's something you keep meaning to address.",
    ],
}

WEEK_GUIDANCE = {
    "phase_shift": [
        "Name the pattern. That's enough for now.",
        "Stop pretending the loop isn't happening.",
        "Find where the decision keeps stalling. That's where the issue lives.",
        "Notice what's blocking. Don't solve it yet.",
        "Let the repetition teach you something.",
    ],
    "cycle_event": [
        "The returning feeling is asking to be seen, not fixed.",
        "Stay with it instead of pushing past.",
        "The cycle runs until you acknowledge what it's carrying.",
        "You can't process what you won't name.",
        "This isn't about action. It's recognition.",
    ],
    "normal_flow": [
        "The quiet pattern is still a pattern.",
        "Follow the thread.",
        "The recurring thought has information.",
        "Don't wait for it to get louder.",
        "Let it show you what it wants.",
    ],
}


# =============================================================================
# MONTH HOOKS - Developmental arc, what this phase is teaching
# =============================================================================
# LEAST REACTIVE. Most developmental.
# Should answer: "What is this period trying to do in me?"

MONTH_HOOKS = {
    "phase_shift": [
        "This period is reshaping how you hold decisions.",
        "The discomfort is friction. You're becoming someone who waits differently.",
        "You're learning to stay still when everything says move.",
        "Something in you is being restructured. You won't see it until after.",
        "This phase is teaching tolerance for not-knowing.",
    ],
    "cycle_event": [
        "What keeps surfacing is asking to finally close.",
        "This phase is completing something older than this month.",
        "You're being taught that some things can only be felt through.",
        "The cycle is reaching its endpoint. Let it.",
        "Clearing is happening. Room is being made.",
    ],
    "normal_flow": [
        "Nothing dramatic. But something is shifting underneath.",
        "A building phase. Not visible yet.",
        "The quiet work happening now becomes obvious later.",
        "Preparation is underway. You won't see what for.",
        "Integration. Let the recent past settle into place.",
    ],
}

MONTH_CONTEXT = {
    "phase_shift": [
        "How have you been approaching decisions over the last few weeks?",
        "Your tolerance for uncertainty — is it growing or shrinking?",
        "The real question: who are you becoming while you wait?",
        "This phase is testing a specific edge. Can you name it?",
        "What you're learning isn't about the situation. It's about how you hold situations.",
    ],
    "cycle_event": [
        "Look back. What has kept appearing? That's the through-line.",
        "Something that started before now is reaching its endpoint.",
        "The emotional material surfacing has roots further back.",
        "This cycle has been in motion. You're approaching release.",
        "What felt unrelated is connecting. See the pattern.",
    ],
    "normal_flow": [
        "Even in quiet periods, something is being built.",
        "Changes now are foundational, not dramatic.",
        "What's integrating this month supports what comes next.",
        "Your system is consolidating. Give it time.",
        "The work is happening whether you see it or not.",
    ],
}

MONTH_GUIDANCE = {
    "phase_shift": [
        "Let this phase do its work.",
        "The discomfort is educational. What's it teaching?",
        "Don't rush the ending.",
        "The lesson is in the waiting.",
        "You're not stuck. You're being restructured.",
    ],
    "cycle_event": [
        "Let what wants to complete, complete.",
        "The release being asked for is specific. Can you name it?",
        "This ends when you let go.",
        "Clearing creates room.",
        "Honor what's ending.",
    ],
    "normal_flow": [
        "Nothing dramatic doesn't mean nothing important.",
        "Use this period to prepare.",
        "Let the quiet do its work.",
        "Don't force intensity.",
        "Trust the building.",
    ],
}


# =============================================================================
# TRANSIT STACK INTEGRATION
# =============================================================================

def get_altitude_day_class(transit_stack: Dict[str, Any], altitude: str) -> str:
    """
    Derive day class for a specific altitude.
    Different altitudes may interpret the same transit differently.
    """
    base_class = transit_stack.get("classification", "normal_flow")
    intensity = transit_stack.get("intensity", 0)
    
    if altitude == "today":
        # Today is most sensitive to current transits
        return base_class
    
    elif altitude == "week":
        # Week smooths out daily fluctuations
        if base_class == "phase_shift" and intensity < 0.85:
            return "cycle_event"  # Downgrade unless very intense
        return base_class
    
    elif altitude == "month":
        # Month focuses on developmental themes, less on acute events
        if base_class == "phase_shift":
            return "cycle_event" if intensity < 0.9 else "phase_shift"
        return base_class
    
    return base_class


def generate_altitude_narrative(
    altitude: str,
    day_class: str,
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate narrative for a single altitude.
    
    Args:
        altitude: "today" | "week" | "month"
        day_class: "phase_shift" | "cycle_event" | "normal_flow"
        chart_data: Optional placement data
    
    Returns:
        {title, body, bridge}
    """
    # Get current date for deterministic selection
    today = datetime.now(timezone.utc)
    date_seed = today.strftime("%Y%m%d")
    
    # Different seed offsets for each altitude to ensure variety
    altitude_offsets = {"today": 0, "week": 7, "month": 31}
    seed_offset = altitude_offsets.get(altitude, 0)
    
    # Create deterministic seed
    seed_str = f"{date_seed}_{altitude}_{day_class}"
    seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    
    # Select content based on altitude
    if altitude == "today":
        hooks = TODAY_HOOKS.get(day_class, TODAY_HOOKS["normal_flow"])
        contexts = TODAY_CONTEXT.get(day_class, TODAY_CONTEXT["normal_flow"])
        guidances = TODAY_GUIDANCE.get(day_class, TODAY_GUIDANCE["normal_flow"])
        title = "Today"
    elif altitude == "week":
        hooks = WEEK_HOOKS.get(day_class, WEEK_HOOKS["normal_flow"])
        contexts = WEEK_CONTEXT.get(day_class, WEEK_CONTEXT["normal_flow"])
        guidances = WEEK_GUIDANCE.get(day_class, WEEK_GUIDANCE["normal_flow"])
        title = "This Week"
    elif altitude == "month":
        hooks = MONTH_HOOKS.get(day_class, MONTH_HOOKS["normal_flow"])
        contexts = MONTH_CONTEXT.get(day_class, MONTH_CONTEXT["normal_flow"])
        guidances = MONTH_GUIDANCE.get(day_class, MONTH_GUIDANCE["normal_flow"])
        title = "This Month"
    else:
        return {"title": altitude.title(), "body": "Unknown altitude.", "bridge": None}
    
    # Select deterministically with offset
    hook = hooks[(seed_hash + seed_offset) % len(hooks)]
    context = contexts[(seed_hash + seed_offset + 3) % len(contexts)]
    guidance = guidances[(seed_hash + seed_offset + 7) % len(guidances)]
    
    # Build body: HOOK → CONTEXT → GUIDANCE as ONE COHERENT DESCENT
    # Not 3 disconnected slogans - one fluid movement
    body = f"{hook} {context} {guidance}"
    
    # NO FILLER BRIDGE - removed generic explanatory text
    # The narrative should speak for itself
    bridge = None
    
    return {
        "title": title,
        "body": body,
        "bridge": bridge,
    }


def generate_astrology_snapshot_3alt(
    transit_stack: Dict[str, Any],
    chart_data: Optional[Dict] = None,
    user_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate complete 3-altitude Astrology Snapshot.
    
    Returns:
        {
            today: {title, body, bridge, technical},
            week: {title, body, bridge, technical},
            month: {title, body, bridge, technical},
            transit_stack: {...},
            version: "astrology_snapshot_v_next"
        }
    """
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Calculate week boundaries
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Get month range
    month_name = now.strftime("%B %Y")
    
    # Get day class for each altitude
    today_class = get_altitude_day_class(transit_stack, "today")
    week_class = get_altitude_day_class(transit_stack, "week")
    month_class = get_altitude_day_class(transit_stack, "month")
    
    # Generate narratives
    today_narrative = generate_altitude_narrative("today", today_class, chart_data)
    week_narrative = generate_altitude_narrative("week", week_class, chart_data)
    month_narrative = generate_altitude_narrative("month", month_class, chart_data)
    
    # Build technical data
    events = transit_stack.get("events", [])
    event_names = [
        e.get("name", e.get("type", "unknown")) if isinstance(e, dict) else str(e)
        for e in events
    ]
    
    technical = {
        "day_class": today_class,
        "week_class": week_class,
        "month_class": month_class,
        "transits": event_names if event_names else None,
        "interaction_theme": transit_stack.get("interaction_theme"),
        "intensity": transit_stack.get("intensity", 0),
    }
    
    # Add chart placements if available
    if chart_data:
        placements = []
        if chart_data.get("sun_sign"):
            placements.append(f"{chart_data['sun_sign'].title()} Sun")
        if chart_data.get("moon_sign"):
            placements.append(f"{chart_data['moon_sign'].title()} Moon")
        if chart_data.get("rising_sign"):
            placements.append(f"{chart_data['rising_sign'].title()} Rising")
        if placements:
            technical["placements"] = placements
    
    # Add technical to each altitude
    today_narrative["technical"] = technical
    week_narrative["technical"] = technical
    month_narrative["technical"] = technical
    
    # Add date context
    today_narrative["date"] = today_date
    week_narrative["date_range"] = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"
    month_narrative["month"] = month_name
    
    return {
        "success": True,
        "today": today_narrative,
        "week": week_narrative,
        "month": month_narrative,
        "transit_stack": {
            "classification": transit_stack.get("classification"),
            "intensity": transit_stack.get("intensity"),
            "interaction_theme": transit_stack.get("interaction_theme"),
            "events": event_names,
        },
        "version": "astrology_snapshot_v_next",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
