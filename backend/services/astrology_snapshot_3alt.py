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
# MOST PERSONAL. Real-time thought unfolding.
# Mix of short + longer. Not all punchlines.

TODAY_HOOKS = {
    "phase_shift": [
        "You start to move on it, then stop. Something pulls you back. You try again, and the same thing happens.",
        "You want it done. You keep circling back to it, but each time you get close, something makes you hesitate.",
        "Part of you is ready to move. But there's another part that keeps saying not yet, and you can't tell which one to trust.",
        "You check the thing again. You don't do anything about it. Then you check it again.",
        "You run through the options. None of them feel right. So you wait. Then run through them again.",
    ],
    "cycle_event": [
        "The same thought keeps showing up. You push it aside, focus on something else, and then there it is again.",
        "Today feels heavier than it should. Nothing specific happened, but you're carrying something.",
        "Something wants your attention. You keep looking past it, but it's still there at the edge.",
        "Small things are landing harder than usual. You're reacting more than the situation calls for.",
        "There's something unfinished sitting in the background. You can feel its weight even when you're not thinking about it directly.",
    ],
    "normal_flow": [
        "Part of you is here, doing the thing. Another part is somewhere else entirely.",
        "You keep drifting off. You pull yourself back. Then you drift again. It's been like that all day.",
        "Nothing urgent is happening. But you're not settled either. There's a low-grade restlessness underneath.",
        "The day is fine. Normal. But something keeps tugging at the edge of your attention.",
        "You're going through the motions. Present, but not really here. Autopilot with a slight delay.",
    ],
}

TODAY_CONTEXT = {
    "phase_shift": [
        "Look at what you've been avoiding — the message you keep not answering, the draft sitting unsent, the thing you keep saying 'later' to.",
        "It's in the tabs still open. The decision you haven't made. The conversation you keep rehearsing but not having.",
        "Notice what you're scrolling past. What you're clicking away from. That's where the signal is.",
        "The thing you keep putting off isn't random. It's connected to whatever's making you hesitate right now.",
        "The unfinished thing keeps pulling at you because it's the signal, not the noise.",
    ],
    "cycle_event": [
        "Pay attention to what keeps coming up in conversations. You've probably mentioned it more than once without realizing.",
        "There's a topic you keep circling back to, even when you try to move on. That's the thing.",
        "What did you wake up thinking about this morning? That's probably it.",
        "The thing you've been putting off is louder today. It's asking to be looked at.",
        "Think about what you've said 'I should really deal with that' about. It's still waiting.",
    ],
    "normal_flow": [
        "Notice where your mind goes when you stop directing it. That's the real thread.",
        "What did you reach for in your first free moment? That tells you something.",
        "In the pause between tasks, what shows up? That's the thing underneath.",
        "You're avoiding something that doesn't actually need to be avoided. Look at what that is.",
        "What you're not doing is telling you as much as what you are doing.",
    ],
}

TODAY_GUIDANCE = {
    "phase_shift": [
        "You don't have to decide right now. The loop you're in is information, not failure.",
        "The back-and-forth is the answer for today. Let it be that.",
        "Stop trying to close it. It's not ready to close, and forcing it won't help.",
        "Name what you're feeling. That's enough. You don't have to fix it yet.",
        "Done isn't available today. That's frustrating, but it's also true.",
    ],
    "cycle_event": [
        "Just look at it. Don't try to solve it or push it away. Just see it.",
        "Don't dismiss it because it's familiar. Familiar doesn't mean handled.",
        "The weight you're feeling is real. Stop pretending it isn't there.",
        "At least acknowledge what's been sitting there. That's the first step.",
        "Let it be heavy for now. You don't have to make it light.",
    ],
    "normal_flow": [
        "Use the space while you have it. This kind of quiet doesn't last forever.",
        "Something's processing in the background. You don't have to understand it yet.",
        "Don't rush to fill the gap. Let it be empty for a while.",
        "Just notice where your attention keeps going. That's the work right now.",
        "You don't have to act on it. Just notice that it's there.",
    ],
}


# =============================================================================
# WEEK — PATTERN ENGINE (v6+ Mirror Language)
# =============================================================================
# JOB: Make user feel "This has happened multiple times already"
# MUST show: repetition across time, loop structure (attempt → interruption → return)
# MUST NOT: explain meaning, interpret, advise
# TONE: observational only

WEEK_PATTERNS = {
    "phase_shift": [
        "You've come back to this more than once already.\n\nEach time, you get close. Then something slows you down. You step away. Then later, you're back again.\n\nNotice where it stalls. Not the decision — the moment right before it.\n\nThat's been repeating all week.",
        
        "This isn't the first time you've stood here this week.\n\nYou approach. Something makes you pause. You move on to other things. Then you're back, standing in the same place.\n\nThe loop is visible now. Same crossroads, different days.",
        
        "You've run through this before. More than once.\n\nYou start to move forward. Then you stop. You tell yourself you'll come back to it. And you do — again and again.\n\nWatch the moment where forward becomes later.",
        
        "There's a pattern forming.\n\nYou reach for it. Something pulls you back. You let it go. Then it resurfaces, and you reach again.\n\nThis has happened several times now. The shape is becoming clear.",
        
        "You keep arriving at this point.\n\nEach time you think you're ready. Each time something interrupts. Each time you circle back.\n\nThe decision isn't the pattern. The hesitation is.",
    ],
    "cycle_event": [
        "The same feeling has surfaced more than once this week.\n\nDifferent moments, different triggers. But underneath — the same thing.\n\nYou push it aside. It comes back. You push it aside again.\n\nNotice how it keeps finding you.",
        
        "You've felt this before. Recently.\n\nIt showed up a few days ago. You moved past it. Now it's here again, wearing different clothes.\n\nThe return itself is information.",
        
        "Something keeps cycling through.\n\nIt arrives. You handle it or ignore it. It fades. Then it's back.\n\nThis isn't new — it's been running underneath the whole week.",
        
        "There's a rhythm you've noticed.\n\nTension builds. It releases. Then it builds again. You've been through this loop more than once already.\n\nThe repetition is the thing to look at.",
        
        "A familiar weight keeps returning.\n\nYou felt it earlier in the week. You're feeling it again now. Different context, same undertone.\n\nIt's not coincidence. It's recurrence.",
    ],
    "normal_flow": [
        "Something quiet keeps coming back.\n\nNot dramatic. Not urgent. But there — again and again.\n\nYou notice it. You let it go. Then it reappears.\n\nThat's been the shape of this week.",
        
        "The same thought has surfaced multiple times.\n\nIn the morning. Between tasks. Right before sleep.\n\nYou're not seeking it out. It keeps finding you.",
        
        "There's a thread running through these past few days.\n\nYou've caught it more than once. A thought that returns, a feeling that resurfaces.\n\nThe repetition is quiet, but it's there.",
        
        "You keep coming back to something.\n\nNot consciously. Not on purpose. But the same thing keeps appearing when your attention wanders.\n\nNotice what that is.",
        
        "A small pattern is forming.\n\nThe same moment keeps recurring — not exactly the same, but close enough to recognize.\n\nYou've felt this more than once this week.",
    ],
}

# =============================================================================
# MONTH — IDENTITY SHIFT ENGINE (v6+ Mirror Language)
# =============================================================================
# JOB: Make user feel "Something about me is changing"
# MUST show: behavioral shift over time, implicit past vs now comparison
# MUST NOT: explain lesson, coach, advise, resolve
# TONE: observational, ambiguous

MONTH_SHIFTS = {
    "phase_shift": [
        "Something in how you move is changing.\n\nYou're not responding the way you used to. There's more hesitation. More space before you act.\n\nIt can feel like you're stuck. Like things aren't moving.\n\nBut look closer — you're not reacting the same way anymore.",
        
        "Your timing has shifted.\n\nDecisions that used to come quickly now take longer. Things that used to feel urgent don't land the same way.\n\nYou're not who you were a month ago in this.\n\nThe change is subtle, but it's there.",
        
        "There's a different rhythm now.\n\nYou used to push through faster. Now there's a pause where there wasn't one before.\n\nIt's not indecision. It's something else.\n\nYou're holding things differently than you did.",
        
        "You're not moving the same way.\n\nThe old pattern was: feel the pressure, act. Now there's a gap in between. A hesitation that wasn't there.\n\nSomething about how you respond has changed.",
        
        "Compare how you handled things a month ago to now.\n\nThere's a difference. Not in what you're doing — in how you're doing it.\n\nMore measured. More careful. Or maybe just slower.\n\nThe shift happened somewhere along the way.",
    ],
    "cycle_event": [
        "Something is completing.\n\nYou can feel it — the sense that a long arc is bending toward its end.\n\nYou're not holding things the way you were. There's less grip now.\n\nThis is different from a month ago.",
        
        "You're not carrying it the same way.\n\nThe thing that felt heavy before — it's still there, but your relationship to it has shifted.\n\nSomewhere in the past few weeks, something changed.\n\nYou're closer to setting it down than you realize.",
        
        "There's less resistance than there was.\n\nA month ago, you were holding tighter. Now something has loosened.\n\nNot resolved. Not fixed. Just... different.\n\nNotice how you're relating to it now versus before.",
        
        "The cycle is reaching somewhere.\n\nYou've been through several turns of this already. But this time feels different.\n\nYou're not reacting the same. The edges have softened.\n\nSomething shifted without you noticing.",
        
        "You used to push back harder.\n\nNow there's more give. More willingness to let it be what it is.\n\nThis isn't something you decided. It happened gradually.\n\nYou're not the same in this as you were.",
    ],
    "normal_flow": [
        "Something quiet has shifted.\n\nYou might not see it clearly yet. But compare how you felt a month ago to now.\n\nThere's a difference. Not dramatic. Not obvious. But real.\n\nYou're not in the same place anymore.",
        
        "You're not approaching things the same way.\n\nThe urgency that used to be there has faded. Or maybe it's not urgency — maybe it's just pace.\n\nEither way, you've slowed down somewhere.\n\nNotice where.",
        
        "There's been a gradual shift.\n\nNothing sudden. Nothing you could point to as a turning point.\n\nBut if you compare now to a month ago, you're not standing in the same place.\n\nSomething moved.",
        
        "Your baseline has changed.\n\nThe way you rest. The way you wait. The way you hold uncertainty.\n\nIt's different than it was. Not better or worse. Just different.\n\nYou're not who you were in this.",
        
        "Look at how you've been over the past few weeks.\n\nThere's a thread there — a gradual change in how you respond, how you hold things, how you wait.\n\nYou're not moving the same way you were.\n\nThe shift is quiet, but it's real.",
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


# =============================================================================
# VALIDATION RULES (v6+ Mirror Language)
# =============================================================================

WEEK_FAIL_PHRASES = [
    "this week is about",
    "you're learning",
    "you are learning",
    "this is about",
    "the lesson",
    "what you need",
    "try to",
    "should",
]

MONTH_FAIL_PHRASES = [
    "you're learning",
    "you are learning", 
    "this period",
    "this phase is teaching",
    "you need to",
    "should",
    "the lesson",
    "it's asking you to",
]

WEEK_REQUIRED_MARKERS = [
    "again", "each time", "more than once", "come back", "keep", 
    "returning", "repeating", "multiple times", "same", "loop",
    "resurface", "recur", "pattern"
]

MONTH_REQUIRED_MARKERS = [
    "used to", "not the same", "changing", "shifted", "different",
    "anymore", "wasn't there", "wasn't before", "compare", "gradual",
    "no longer", "now there's"
]


def validate_week_narrative(body: str) -> bool:
    """Check WEEK narrative passes v6+ rules."""
    body_lower = body.lower()
    
    # Check for fail phrases
    for phrase in WEEK_FAIL_PHRASES:
        if phrase in body_lower:
            logger.warning(f"[WeekValidation] FAIL: contains '{phrase}'")
            return False
    
    # Check for required repetition markers
    has_repetition = any(marker in body_lower for marker in WEEK_REQUIRED_MARKERS)
    if not has_repetition:
        logger.warning("[WeekValidation] FAIL: no repetition markers found")
        return False
    
    return True


def validate_month_narrative(body: str) -> bool:
    """Check MONTH narrative passes v6+ rules."""
    body_lower = body.lower()
    
    # Check for fail phrases
    for phrase in MONTH_FAIL_PHRASES:
        if phrase in body_lower:
            logger.warning(f"[MonthValidation] FAIL: contains '{phrase}'")
            return False
    
    # Check for required shift markers (past vs now comparison)
    has_shift = any(marker in body_lower for marker in MONTH_REQUIRED_MARKERS)
    if not has_shift:
        logger.warning("[MonthValidation] FAIL: no behavioral shift markers found")
        return False
    
    return True


def generate_altitude_narrative(
    altitude: str,
    day_class: str,
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate narrative for a single altitude.
    
    TODAY: immediate lived experience (unchanged)
    WEEK: pattern engine - shows repetition/loop structure
    MONTH: identity shift engine - shows behavioral change over time
    
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
    
    # Generate based on altitude type
    if altitude == "today":
        # TODAY uses the existing hook/context/guidance structure
        hooks = TODAY_HOOKS.get(day_class, TODAY_HOOKS["normal_flow"])
        contexts = TODAY_CONTEXT.get(day_class, TODAY_CONTEXT["normal_flow"])
        guidances = TODAY_GUIDANCE.get(day_class, TODAY_GUIDANCE["normal_flow"])
        title = "Today"
        
        # Select deterministically
        hook = hooks[(seed_hash + seed_offset) % len(hooks)]
        context = contexts[(seed_hash + seed_offset + 3) % len(contexts)]
        guidance = guidances[(seed_hash + seed_offset + 7) % len(guidances)]
        
        body = f"{hook} {context} {guidance}"
        
    elif altitude == "week":
        # WEEK uses pre-written pattern narratives (v6+ Mirror Language)
        patterns = WEEK_PATTERNS.get(day_class, WEEK_PATTERNS["normal_flow"])
        title = "This Week"
        
        # Select and validate
        for attempt in range(len(patterns)):
            idx = (seed_hash + seed_offset + attempt) % len(patterns)
            body = patterns[idx]
            if validate_week_narrative(body):
                break
        else:
            # Fallback: use first pattern
            body = patterns[0]
            logger.warning("[WeekNarrative] All patterns failed validation, using first")
        
    elif altitude == "month":
        # MONTH uses pre-written shift narratives (v6+ Mirror Language)
        shifts = MONTH_SHIFTS.get(day_class, MONTH_SHIFTS["normal_flow"])
        title = "This Month"
        
        # Select and validate
        for attempt in range(len(shifts)):
            idx = (seed_hash + seed_offset + attempt) % len(shifts)
            body = shifts[idx]
            if validate_month_narrative(body):
                break
        else:
            # Fallback: use first shift
            body = shifts[0]
            logger.warning("[MonthNarrative] All shifts failed validation, using first")
    
    else:
        return {"title": altitude.title(), "body": "Unknown altitude.", "bridge": None}
    
    # NO FILLER BRIDGE - narrative speaks for itself
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
