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
# Start from what they're DOING or LOOPING IN today

TODAY_HOOKS = {
    "phase_shift": [
        "You try to decide. Then something feels off. You pull back. Then you try again.",
        "You want this done. You just want to stop thinking about it. But something won't let you.",
        "Part of you says just do it. Another part says wait. Neither one wins.",
        "You keep checking your phone. Checking the thing. Not doing the thing.",
        "The urge to decide is there. But every option feels slightly wrong.",
    ],
    "cycle_event": [
        "The same thought keeps coming back. You push it away. It returns.",
        "Today feels heavier than yesterday. You're not imagining it.",
        "Something wants your attention. You've been looking away.",
        "Small things are landing harder than they should.",
        "You can feel the weight of something unfinished.",
    ],
    "normal_flow": [
        "You're here, doing the thing. But part of you is somewhere else.",
        "You lose focus. Catch yourself drifting. Pull back. Drift again.",
        "Nothing urgent. But you're not settled either.",
        "The day is fine. Regular. But something keeps tugging.",
        "You're running on autopilot. Not bad. Just absent.",
    ],
}

TODAY_CONTEXT = {
    "phase_shift": [
        "Look at what you're avoiding — the message, the call, the thing you keep saying 'later' to.",
        "It shows up in the tabs still open. The draft not sent. The decision not made.",
        "Check your messages. Something there is asking for your attention.",
        "Notice what you're scrolling past. What you're not clicking on.",
        "The unfinished thing isn't random. It's the signal.",
    ],
    "cycle_event": [
        "Notice what keeps coming up in conversations. That's not coincidence.",
        "Pay attention to the topic you keep circling back to.",
        "What did you wake up thinking about? That's it.",
        "The thing you've been putting off — today it's louder.",
        "Look at what you've said 'I should really...' about.",
    ],
    "normal_flow": [
        "Notice where your mind keeps going when you're doing something else.",
        "What did you reach for when you had a free moment?",
        "The pause between tasks — what shows up there?",
        "Look at what you're avoiding that doesn't need to be avoided.",
        "What you're not doing is telling you something.",
    ],
}

TODAY_GUIDANCE = {
    "phase_shift": [
        "Don't decide. Not yet.",
        "The loop you're in? That's the answer for now.",
        "Stop trying to close it. It's not ready.",
        "Name what you feel. Don't fix it.",
        "You want it done. Fine. But done isn't available today.",
    ],
    "cycle_event": [
        "Look at the thing you keep avoiding. Just look.",
        "Don't dismiss it. It's not random.",
        "The weight is real. Stop pretending it's not.",
        "Whatever you've been putting off — at least acknowledge it today.",
        "Let it be heavy. Don't fake light.",
    ],
    "normal_flow": [
        "Use the space. It won't last.",
        "The quiet isn't nothing. Something's processing.",
        "Don't fill the gap. Let it be a gap.",
        "Notice where your attention naturally goes.",
        "What you're avoiding? You don't have to do it. But notice you're avoiding it.",
    ],
}


# =============================================================================
# WEEK HOOKS - Pattern recognition, what keeps returning
# =============================================================================
# Describe what repeats AFTER the first reaction fades

WEEK_HOOKS = {
    "phase_shift": [
        "There's a pattern here you've seen before. Decision delayed. Then delayed again. Then the same options, reshuffled.",
        "Every few days, the same choice comes back wearing different clothes. You keep not picking.",
        "You've had this conversation with yourself multiple times this week. It hasn't resolved.",
        "The theme keeps returning: forward or stay. Forward or stay. The loop continues.",
        "Watch for the moment when you almost decide — then pull back. That's the pattern.",
    ],
    "cycle_event": [
        "The same emotional tone keeps returning. Something is cycling through that wants to be seen.",
        "Notice what keeps surfacing when you're alone. That's the pattern this week.",
        "There's a rhythm to this week — tension, release, tension again. Not random.",
        "A familiar feeling keeps showing up in different situations. It's connected.",
        "The same theme is appearing in different conversations. Pay attention to that.",
    ],
    "normal_flow": [
        "Nothing dramatic, but something keeps quietly returning. A thought. A memory. A question.",
        "There's a background hum this week. Not urgent, but persistent.",
        "You might notice the same thought showing up at odd moments. That's the thread.",
        "The week has a theme even if you can't name it yet. Watch for the repetition.",
        "Something small keeps catching your attention. It's trying to show you something.",
    ],
}

WEEK_CONTEXT = {
    "phase_shift": [
        "The thing you keep postponing? It's been on your list since earlier in the week. Maybe longer.",
        "Notice how many times you've said 'I'll figure it out later.' That later is now stacking.",
        "Look at your messages from a few days ago. What did you not reply to? It's still there.",
        "The decision you're avoiding — how many versions of it have you already played out in your head?",
        "Count the number of times this topic has come up. That's the signal strength.",
    ],
    "cycle_event": [
        "There's probably a conversation you've been meaning to have. Or one you've been avoiding.",
        "The same topic keeps surfacing with different people. The source is internal.",
        "Look back at what bothered you earlier this week. Is it still there? Unprocessed?",
        "What did you promise yourself you'd handle? Is it handled?",
        "The pattern shows up in what you're thinking about when you're not working.",
    ],
    "normal_flow": [
        "Pay attention to what keeps coming back when you have free time.",
        "The recurring thought is showing you where your attention actually wants to go.",
        "Look at what you've mentioned to others more than once this week.",
        "There's something you keep meaning to address. It's still there.",
        "The background thought? It's not background. It's foreground waiting to be acknowledged.",
    ],
}

WEEK_GUIDANCE = {
    "phase_shift": [
        "The pattern won't break until you name it. Just naming it is enough for now.",
        "You don't have to solve the loop. Just stop pretending it's not happening.",
        "Track where the decision keeps getting stuck. That's where the real issue lives.",
        "This isn't about making a choice. It's about noticing what's blocking the choice.",
        "Let the repetition teach you something. What keeps coming back?",
    ],
    "cycle_event": [
        "The returning feeling isn't asking you to fix it. It's asking you to see it.",
        "Instead of pushing it away, try staying with it for a moment.",
        "The cycle will keep running until you acknowledge what it's carrying.",
        "You can't process what you won't name. Start there.",
        "This isn't about action. It's about recognition.",
    ],
    "normal_flow": [
        "The quiet pattern is still a pattern. Don't dismiss it because it's not loud.",
        "Follow the thread. See where it goes.",
        "The recurring thought has information. What is it pointing at?",
        "Don't wait for it to get louder. It's already speaking.",
        "Let the pattern show you what it wants. Stop directing.",
    ],
}


# =============================================================================
# MONTH HOOKS - Developmental arc, what this phase is teaching
# =============================================================================
# Answer: "What is this period trying to do in me?"

MONTH_HOOKS = {
    "phase_shift": [
        "This period is teaching you how to stay still when everything in you wants to move.",
        "The discomfort you're feeling? It's the friction of becoming someone who decides differently.",
        "This isn't about the decision. It's about who you become by not forcing the decision.",
        "Something in you is being restructured. You're not supposed to understand it yet.",
        "This phase is training you to tolerate uncertainty. That's the actual work.",
    ],
    "cycle_event": [
        "What keeps returning is asking to finally be completed — or released.",
        "This phase is finishing something you started a while ago. Let it conclude.",
        "You're being taught that some things need to be felt through, not figured out.",
        "The cycle is completing. What you're holding needs to be set down.",
        "This period is clearing space. What's coming needs room you haven't made yet.",
    ],
    "normal_flow": [
        "Nothing dramatic is happening, but something is quietly shifting underneath.",
        "This is a building phase. Not visible yet, but forming.",
        "The subtle work happening now will become obvious later.",
        "You're being prepared for something you can't see yet. Trust the preparation.",
        "This period is about integration. Let what's been happening settle.",
    ],
}

MONTH_CONTEXT = {
    "phase_shift": [
        "Look at how you've been approaching decisions over the past few weeks. A pattern is forming.",
        "Notice how your tolerance for uncertainty has shifted. Is it growing or shrinking?",
        "The big question isn't 'what should I do?' It's 'who am I becoming while I wait?'",
        "This phase is testing a specific edge in you. Can you name what it is?",
        "What you're learning isn't about the situation. It's about how you hold situations.",
    ],
    "cycle_event": [
        "Look back at the past month. What has kept appearing? That's the through-line.",
        "Something that started before now is reaching its natural endpoint.",
        "The emotional material surfacing this month has roots further back. Follow them.",
        "This cycle has been in motion for a while. You're approaching resolution or release.",
        "What felt unrelated is starting to connect. See the pattern emerging.",
    ],
    "normal_flow": [
        "Even in quiet periods, something is being built. Look for the evidence.",
        "The changes happening now are foundational, not dramatic. That's okay.",
        "What's integrating this month will support what's coming next.",
        "Your system is consolidating something. Give it time.",
        "The work is happening whether you see it or not. Trust the process.",
    ],
}

MONTH_GUIDANCE = {
    "phase_shift": [
        "Let this phase do its work. You're being shaped, not punished.",
        "The discomfort is educational. What is it teaching you about yourself?",
        "Don't rush the ending. The timing has its own intelligence.",
        "Stay present to the process. The lesson is in the waiting.",
        "You're not stuck. You're being restructured. Those feel similar but aren't.",
    ],
    "cycle_event": [
        "Let what wants to complete, complete. Stop holding it open.",
        "The release you're being asked for is specific. Can you name it?",
        "This phase ends when you let go. Not before.",
        "Trust that clearing creates room. Something better is waiting.",
        "Honor what's ending. Gratitude makes space for what comes next.",
    ],
    "normal_flow": [
        "Nothing dramatic doesn't mean nothing important. Stay attentive.",
        "Use this period to prepare. Something is coming that will need you ready.",
        "Let the quiet do its work. Integration happens in stillness.",
        "Don't force intensity. This period has its own value.",
        "The foundation being laid now matters. Trust the building.",
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
    
    # Build body: HOOK → CONTEXT → GUIDANCE
    body = f"{hook}\n\n{context}\n\n{guidance}"
    
    # Generate bridge for altitude-specific emphasis
    bridge = None
    if altitude == "today":
        bridge = "This is what's happening right now."
    elif altitude == "week":
        bridge = "This is the pattern that keeps returning."
    elif altitude == "month":
        bridge = "This is what this period is teaching you."
    
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
