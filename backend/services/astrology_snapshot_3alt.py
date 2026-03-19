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
# WEEK HOOKS - Pattern recognition, what keeps returning
# =============================================================================
# WIDER RHYTHM. What repeats AFTER the first reaction fades.
# Flowing, not stacked. Shows the recurrence unfolding.

WEEK_HOOKS = {
    "phase_shift": [
        "This is the same crossroads you were at a few days ago. You thought you'd moved past it, but here it is again, dressed slightly differently.",
        "The decision you didn't make earlier this week is still sitting there. You've walked around it, looked at it from different angles, but it hasn't budged.",
        "Every few days you arrive back at the same fork. You stand there, consider both paths, then step back without choosing. The pattern holds.",
        "You keep returning to this. Forward or stay. You've run through it multiple times now, and you're no closer to resolution than when you started.",
        "Watch for the moment when you almost commit to something, then pull back. That hesitation has been happening all week.",
    ],
    "cycle_event": [
        "There's something cycling through this week. You've noticed it more than once — the same feeling surfacing in different situations.",
        "The same emotional tone keeps returning. Different triggers, but the same reaction underneath. That's not coincidence.",
        "There's a rhythm running through these past few days. Tension builds, then releases, then builds again. You can feel it even when you can't name it.",
        "A familiar feeling keeps showing up. It finds you in conversations, in quiet moments, in reactions you don't quite understand.",
        "The same theme is threading through your week. Different contexts, same underlying current.",
    ],
    "normal_flow": [
        "Something quiet keeps returning. Not dramatic, not urgent, but present. A thought that surfaces at odd moments.",
        "There's a background hum to this week. You've half-noticed it — something persistent underneath the ordinary.",
        "The same thought keeps appearing when you're not paying attention. In the shower, between tasks, right before sleep.",
        "The week has a theme, even if you can't name it yet. Something keeps catching your attention, again and again.",
        "Something small keeps pulling at you. It's easy to dismiss, but it keeps coming back.",
    ],
}

WEEK_CONTEXT = {
    "phase_shift": [
        "Think about how many times you've said 'I'll figure it out later' this week. That later keeps getting pushed forward.",
        "The thing you've been postponing has been on your mental list for days now. Maybe longer. It's not going anywhere.",
        "How many versions of this decision have you already played out in your head? And yet here you are, still undecided.",
        "There's probably a message or a conversation you've been avoiding since earlier this week. It's still waiting.",
        "Try to track where you keep getting stuck. The location where progress stalls — that's where the real issue lives.",
    ],
    "cycle_event": [
        "Notice that the same topic keeps surfacing with different people. The common thread isn't them — it's you.",
        "What bothered you earlier this week? Check if it's still there, unprocessed, still carrying weight.",
        "There's a conversation you've been meaning to have. You keep finding reasons to postpone it.",
        "Think about what you promised yourself you'd handle this week. Has it actually been handled?",
        "The pattern is most visible when you're not working. Pay attention to what shows up in the quiet moments.",
    ],
    "normal_flow": [
        "Notice what keeps coming back when you have a free moment. That's where your attention actually wants to go.",
        "Pay attention to what you've mentioned to others more than once this week. That repetition is meaningful.",
        "The thought you keep having in the background isn't background. It's foreground waiting to be acknowledged.",
        "When you stop directing your attention, where does it drift? That's the thread worth following.",
        "There's something you keep meaning to address. It's been waiting patiently for days now.",
    ],
}

WEEK_GUIDANCE = {
    "phase_shift": [
        "You don't have to break the pattern yet. Just naming it is enough for now. Recognition before resolution.",
        "Stop pretending the loop isn't happening. You've been running through the same options all week — acknowledge that.",
        "Find where the decision keeps stalling out. The sticking point tells you more than the options themselves.",
        "This week isn't about making the choice. It's about noticing what's been blocking the choice.",
        "Let the repetition teach you something. What keeps coming back? That's the information.",
    ],
    "cycle_event": [
        "The feeling that keeps returning is asking to be seen, not solved. You can't process what you won't acknowledge.",
        "Instead of pushing past it again, try staying with it for a moment. See what it's actually carrying.",
        "The cycle will keep running until you acknowledge what it's trying to show you. That's how these things work.",
        "You can't process what you won't name. Start by naming it, even if just to yourself.",
        "This isn't about taking action. It's about recognition. Action comes later.",
    ],
    "normal_flow": [
        "The quiet pattern is still a pattern. Don't dismiss it just because it's not loud.",
        "Follow the thread and see where it leads. You don't have to do anything about it yet.",
        "The thought that keeps recurring has information in it. What is it pointing toward?",
        "Don't wait for it to get louder before you pay attention. It's already been speaking all week.",
        "Let the pattern show you what it wants. Stop trying to direct it.",
    ],
}


# =============================================================================
# MONTH HOOKS - Developmental arc, what this phase is teaching
# =============================================================================
# LEAST REACTIVE. Most developmental. Flows like reflection.
# Answer: "What is this period trying to do in me?"

MONTH_HOOKS = {
    "phase_shift": [
        "This period is reshaping how you hold decisions. You can feel it in the way you approach choices now — more carefully, more hesitantly. Something is shifting.",
        "The discomfort you've been feeling isn't random. It's the friction that comes from becoming someone who waits differently than you used to.",
        "You're learning to stay still when every instinct says move. It doesn't feel like progress, but it is.",
        "Something in you is being restructured. You won't be able to see the shape of it until later, but the work is happening now.",
        "This phase is teaching you to tolerate not-knowing. That's harder than deciding, and also more important.",
    ],
    "cycle_event": [
        "What keeps surfacing this month is asking to finally close. It's been open for longer than you realized, and now it wants resolution.",
        "This phase is completing something that started well before this month. You're at the end of a cycle, not the beginning.",
        "You're being taught that some things can only be felt through, not figured out. The understanding comes after, not before.",
        "The cycle that's been running is reaching its endpoint. What you've been holding is ready to be set down.",
        "Clearing is happening, whether you're directing it or not. Space is being made for something you can't see yet.",
    ],
    "normal_flow": [
        "Nothing dramatic is happening on the surface, but something is shifting underneath. You can sense it in the background.",
        "This is a building phase. The foundation being laid now isn't visible yet, but it will support what comes next.",
        "The quiet work happening this month will become obvious later. Right now it just feels like ordinary time.",
        "Preparation is underway for something you can't see yet. Trust the process even when you can't track the progress.",
        "Integration is the work of this period. Let what's happened recently settle into place. That's enough for now.",
    ],
}

MONTH_CONTEXT = {
    "phase_shift": [
        "Look at how you've been approaching decisions over the past few weeks. Notice if there's a pattern forming in how you hesitate, reconsider, wait.",
        "Ask yourself: has your tolerance for uncertainty been growing or shrinking? The answer tells you something about what this phase is doing.",
        "The real question isn't 'what should I do?' It's 'who am I becoming while I wait?' That's what this month is about.",
        "This phase is testing a specific edge in you. Can you name what capacity is being stretched? What tolerance is being built?",
        "What you're learning right now isn't about the situation itself. It's about how you hold situations like this one.",
    ],
    "cycle_event": [
        "Look back at the past month. What has kept appearing? That repeated theme is the through-line trying to complete.",
        "Something that started before now is reaching its natural endpoint. You can feel the arc bending toward conclusion.",
        "The emotional material surfacing this month has roots further back than you might think. It's connected to older patterns.",
        "This cycle has been in motion for a while. You're approaching the point of resolution or release — whichever is needed.",
        "Things that seemed unrelated are starting to connect. See the larger pattern that's been emerging.",
    ],
    "normal_flow": [
        "Even in quiet periods like this, something is being built. Look for the subtle evidence of change.",
        "The changes happening now are foundational rather than dramatic. They won't be visible until later.",
        "What's integrating this month will support what comes next. The quiet work matters.",
        "Your system is consolidating something. Give it time to finish before you push for the next thing.",
        "The work is happening whether you can see it or not. Some progress isn't measurable in the moment.",
    ],
}

MONTH_GUIDANCE = {
    "phase_shift": [
        "Let this phase do its work. You're being shaped by it, not punished by it.",
        "The discomfort is educational. Instead of trying to end it, ask what it's teaching you about yourself.",
        "Don't rush toward an ending. The timing has its own intelligence, and forcing it won't help.",
        "The lesson is in the waiting itself. Stay present to the process instead of focusing on when it will end.",
        "You're not stuck. You're being restructured. Those feel similar but aren't the same thing.",
    ],
    "cycle_event": [
        "Let what wants to complete, complete. Stop holding things open that are ready to close.",
        "The release being asked of you is specific. Can you name what you're being asked to let go of?",
        "This ends when you let go. Not before. The timing is connected to your willingness.",
        "Clearing creates room. Trust that what's being made space for is worth what's leaving.",
        "Honor what's ending instead of rushing past it. Endings deserve attention too.",
    ],
    "normal_flow": [
        "Nothing dramatic doesn't mean nothing important. Stay attentive to the quiet shifts.",
        "Use this period to prepare. Something is coming that will need you ready.",
        "Let the quiet do its work. Integration happens in stillness, not activity.",
        "Don't force intensity where there isn't any. This period has its own value exactly as it is.",
        "Trust the building that's happening beneath the surface. The foundation matters.",
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
