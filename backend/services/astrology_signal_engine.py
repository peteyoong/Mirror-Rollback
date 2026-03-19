"""
Astrology Signal Engine v7
===========================

Reaches Human Design-level signal quality through 4-layer architecture:

LAYER 0: Transit Convergence / Day Class
- Stacked events (new moon + equinox = phase_shift)
- Eclipse seasons
- Major threshold days

LAYER 1: Dominant Transit Tension
- ONE primary tension selected (not multiple themes)
- Describes the inner conflict in lived terms

LAYER 2: Natal Receiver
- How does this transit land in THIS person's chart?
- Personalizes the transit

LAYER 3: Time Altitude
- TODAY = immediate felt tension
- WEEK = recurring loop (attempt → interruption → return)
- MONTH = identity/behavioral shift over time

CRITICAL: Each altitude returns ONE dominant signal.
"""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DAY CLASSIFICATION
# =============================================================================

class DayClass(str, Enum):
    PHASE_SHIFT = "phase_shift"       # Major threshold, stacked events
    CYCLE_EVENT = "cycle_event"       # Single significant event
    NORMAL_FLOW = "normal_flow"       # Ordinary day


# =============================================================================
# LAYER 1: DOMINANT TRANSIT TENSIONS
# =============================================================================
# These are the CORE tensions that astrology translates into lived experience
# Each tension has a specific shape - don't mix them

class TransitTension(str, Enum):
    FORCING_CLARITY = "forcing_clarity"           # wanting to know before ready
    MOVEMENT_BEFORE_ALIGNMENT = "movement_before_alignment"  # urge to act before timing
    REACTING_BEFORE_UNDERSTANDING = "reacting_before_understanding"  # emotional before mental
    REOPENING_UNRESOLVED = "reopening_unresolved"  # past material surfacing
    SHIFT_BEFORE_DIRECTION = "shift_before_direction"  # change happening, destination unclear
    INNER_PACE_OUTER_TIMING = "inner_pace_outer_timing"  # personal rhythm vs external demands
    COMPLETION_RESISTANCE = "completion_resistance"  # something ending, holding on


# Tension descriptions - SHORT and HUMAN (for cause layer)
TENSION_CAUSES = {
    TransitTension.FORCING_CLARITY: [
        "You're trying to know before you're ready to know.",
        "Clarity is being demanded before it's available.",
        "Something wants to be decided before it's been understood.",
    ],
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: [
        "The urge to move is outpacing the timing.",
        "You want to act, but the alignment isn't there yet.",
        "Action is pulling ahead of readiness.",
    ],
    TransitTension.REACTING_BEFORE_UNDERSTANDING: [
        "Feelings are arriving faster than comprehension.",
        "You're responding before you've processed.",
        "The emotional is outpacing the mental.",
    ],
    TransitTension.REOPENING_UNRESOLVED: [
        "Something old is surfacing again.",
        "Unfinished material is making itself known.",
        "The past is knocking on today.",
    ],
    TransitTension.SHIFT_BEFORE_DIRECTION: [
        "Change is happening before the destination is clear.",
        "Something is moving, but not toward anything yet.",
        "The shift started before the path appeared.",
    ],
    TransitTension.INNER_PACE_OUTER_TIMING: [
        "Your inner rhythm and external timing are mismatched.",
        "You're being asked to move at a pace that isn't yours.",
        "Inner time and outer time are out of sync.",
    ],
    TransitTension.COMPLETION_RESISTANCE: [
        "Something is ending, but you're not letting go yet.",
        "The conclusion is arriving before you're ready.",
        "Completion is present, acceptance is not.",
    ],
}


# =============================================================================
# LAYER 2: NATAL RECEIVER PATTERNS
# =============================================================================
# How the transit lands in the person based on chart indicators

NATAL_RECEIVERS = {
    "emotional": [
        "Your emotional body is the entry point.",
        "Feelings arrive first, then the situation.",
        "The wave is picking up this signal.",
    ],
    "mental": [
        "Your thoughts are receiving this first.",
        "The mind is where it's landing.",
        "Processing is happening in thought before body.",
    ],
    "physical": [
        "Your body is registering this.",
        "The signal is landing in action or sensation.",
        "You're feeling it before you're thinking it.",
    ],
    "relational": [
        "This is showing up in how you connect.",
        "Other people are the channel.",
        "The signal is arriving through relationships.",
    ],
    "private": [
        "This is landing in your inner space.",
        "The signal is internal, not external.",
        "No one else can see where this is hitting.",
    ],
}


# =============================================================================
# LAYER 3: TIME ALTITUDE NARRATIVES
# =============================================================================

# TODAY: Immediate felt tension (shortest distance to behavior)
TODAY_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You keep trying to figure it out. Each time you get close, something pulls you back. The answer isn't refusing you — it just isn't here yet.",
            "You want clarity. You've been circling this for a while now. But every time you think you have it, something shifts.",
            "Part of you knows what to do. Another part keeps hesitating. That gap between knowing and not-knowing — that's where you are.",
        ],
        "cycle_event": [
            "The need to understand is strong today. But understanding keeps slipping away when you reach for it.",
            "You're trying to make sense of something. The pieces are there, but they're not clicking together yet.",
            "Clarity feels close but not quite available. You're in the space between confusion and comprehension.",
        ],
        "normal_flow": [
            "Something's on your mind that you can't quite resolve. It's not urgent, but it's there.",
            "You keep returning to the same question. No pressure, but no answer either.",
            "A low-level uncertainty is running in the background. Nothing dramatic, just unresolved.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You want to move. Something is holding you still. That tension between action and patience — it's loud today.",
            "The impulse to do something is strong. But the timing feels off. You're caught between go and wait.",
            "Part of you is ready to act. Another part knows it's not time yet. Neither side is winning.",
        ],
        "cycle_event": [
            "There's an urge to move forward that isn't being satisfied. The path is blocked, or maybe just not clear yet.",
            "You're ready for something to happen. But the happening isn't ready for you.",
            "Action wants to occur. The space for it hasn't opened yet.",
        ],
        "normal_flow": [
            "A quiet restlessness is present. Not dramatic, but noticeable. Something wants to move.",
            "You're waiting for a green light that hasn't come. The wait isn't hard, but it's there.",
            "There's momentum building with nowhere to go yet. Patience is the only available action.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "Feelings are arriving before thoughts can catch up. You're responding to things you haven't fully processed.",
            "Your reactions are faster than your comprehension today. Something's landing in your body before your mind.",
            "Emotions are leading. The understanding will come later — it's just not here yet.",
        ],
        "cycle_event": [
            "You're feeling something strongly that you can't quite explain. The feeling is clear; the reason isn't.",
            "Reactions are happening before analysis. Your system is processing something it hasn't named yet.",
            "There's more emotion than explanation available right now.",
        ],
        "normal_flow": [
            "Small feelings are surfacing without clear causes. Nothing overwhelming, just present.",
            "You're having reactions that don't fully match the situations. Something underneath is active.",
            "Emotions are a half-step ahead of understanding today.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "Something old is back. You thought you were past it, but here it is again. Same material, new day.",
            "The past is making itself known. Whatever you didn't finish is asking for attention again.",
            "You're revisiting something you've seen before. Not by choice — it just showed up.",
        ],
        "cycle_event": [
            "A familiar theme is surfacing. You've been here before. The question is whether it's time to finally close it.",
            "Something you thought was done is reopening. Not dramatically, but noticeably.",
            "Old material is present. It's not asking to be fixed, just acknowledged.",
        ],
        "normal_flow": [
            "A quiet echo from the past is sounding. Nothing urgent, but definitely there.",
            "Something from before is gently returning. Not a crisis, just a reminder.",
            "The past is tapping on your shoulder today. Light touch, but persistent.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "Something is changing, and you don't know where it's going. The shift is happening; the destination isn't clear.",
            "You're in transition. The old thing is fading, the new thing hasn't arrived. You're in the gap.",
            "Movement is occurring without a clear direction. You're not stuck — you're between.",
        ],
        "cycle_event": [
            "Change is in the air, but the form it's taking isn't visible yet. You're sensing shift before seeing shape.",
            "Something is ending or beginning — you're not sure which. The transition is more clear than the destination.",
            "You're moving, but not toward anything specific. That's okay. Direction comes after motion sometimes.",
        ],
        "normal_flow": [
            "A subtle shift is occurring. You might not be able to point to it, but you can feel it.",
            "Things are quietly changing. No fanfare, just gradual movement.",
            "The ground is shifting slightly. Not earthquake, just adjustment.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "Your rhythm and the world's rhythm aren't matching. You're being asked to move at a pace that isn't yours.",
            "External timing is pressing against internal timing. Something needs to give, but you're not sure what.",
            "The outside wants fast. The inside wants slow. You're caught in that mismatch.",
        ],
        "cycle_event": [
            "You're out of sync with something external. Your pace and the required pace aren't aligning.",
            "There's friction between how you want to move and how you're being asked to move.",
            "Your inner clock and outer demands are in different time zones today.",
        ],
        "normal_flow": [
            "A mild disconnect between inner and outer tempo. Nothing severe, but noticeable.",
            "You're slightly out of sync with the day's rhythm. Manageable, but present.",
            "The pace required isn't quite your natural pace. You're adjusting.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "Something is ready to end, but you're not letting go yet. The completion is available; the acceptance isn't.",
            "You're holding onto something that's finished. Not because you don't know — because you're not ready.",
            "An ending is present. Your willingness to accept it isn't matching its readiness to occur.",
        ],
        "cycle_event": [
            "Something wants to close, and you're keeping it open. The question is whether that's wisdom or avoidance.",
            "A natural endpoint is approaching. Your response to it is still forming.",
            "Completion is near. Your relationship to it is still uncertain.",
        ],
        "normal_flow": [
            "A quiet ending is available. You're not resisting hard, but you're not embracing either.",
            "Something could be finished if you let it. The letting is the question.",
            "A soft close is possible. Your grip is light but not yet released.",
        ],
    },
}

# WEEK: Recurring loop (attempt → interruption → return)
WEEK_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You've tried to figure this out more than once this week.\n\nEach time you get close to understanding, something pulls you back. You step away. Then later, you're thinking about it again.\n\nNotice where the understanding keeps breaking down.\n\nThat's been the loop.",
            "This isn't the first time you've circled this question.\n\nYou approach it. You almost have it. Then it slips. And then you're back, trying again.\n\nThe answer isn't refusing you — the timing is just off.",
        ],
        "cycle_event": [
            "You've returned to this puzzle several times already.\n\nEach time feels like you're getting closer. Then something interrupts. Then you're back at it.\n\nThe repetition itself is information.",
        ],
        "normal_flow": [
            "A quiet question has surfaced more than once this week.\n\nNot urgent. Not pressing. But present.\n\nYou've thought about it, moved on, and found yourself back there again.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You've felt the urge to move forward several times this week.\n\nEach time, something stops you. You pause. Then the urge returns.\n\nThe impulse is real. The opening isn't here yet.\n\nThat's been the pattern.",
            "This push-pull has been happening all week.\n\nYou want to act. You hold back. The tension builds. You consider acting again.\n\nThe loop isn't failure — it's timing working itself out.",
        ],
        "cycle_event": [
            "More than once you've been ready to move.\n\nMore than once something's held you back.\n\nThe readiness keeps arriving before the opportunity.",
        ],
        "normal_flow": [
            "A mild restlessness has been recurring.\n\nIt shows up, settles, then returns.\n\nNothing dramatic, just a persistent readiness that hasn't found its moment.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "You've had strong reactions several times this week.\n\nEach time, the feeling came first. The understanding came later — or hasn't come yet.\n\nYou're processing something that hasn't fully revealed itself.",
        ],
        "cycle_event": [
            "The same emotional tone has surfaced more than once.\n\nDifferent situations, same feeling underneath.\n\nThe repetition is pointing at something.",
        ],
        "normal_flow": [
            "Small reactions have been showing up repeatedly.\n\nNothing overwhelming. But consistent.\n\nYour system is working on something.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "The same material has resurfaced multiple times this week.\n\nYou thought you'd moved past it. Then it appeared again. And again.\n\nIt's not haunting you — it's waiting for completion.",
        ],
        "cycle_event": [
            "A familiar theme keeps returning.\n\nYou notice it. You set it aside. Then it's back.\n\nThe loop is asking for acknowledgment.",
        ],
        "normal_flow": [
            "Something from before keeps gently appearing.\n\nNot demanding. Just present.\n\nIt's shown up more than once this week.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You've felt the ground shifting multiple times this week.\n\nEach time, you look for the new direction. Each time, it's not clear yet.\n\nThe change is real. The destination is still forming.",
        ],
        "cycle_event": [
            "Something has been transitioning all week.\n\nYou sense it ending, beginning, moving. But the shape keeps changing.\n\nYou're in the middle of the shift.",
        ],
        "normal_flow": [
            "A quiet transition has been ongoing.\n\nYou've noticed it more than once.\n\nThe movement is subtle but consistent.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "You've felt out of sync several times this week.\n\nThe world's rhythm and your rhythm keep not matching.\n\nEach time you adjust, the gap shows up again.\n\nThis is the friction that's been running.",
        ],
        "cycle_event": [
            "The mismatch has been recurring.\n\nYou find your pace. External demands interrupt. You readjust.\n\nThe dance between inner and outer time continues.",
        ],
        "normal_flow": [
            "A mild asynchrony has been present.\n\nYou've noticed it more than once.\n\nYour tempo and the world's tempo are slightly off.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You've approached this ending more than once this week.\n\nEach time, you get close to letting go. Each time, you pull back.\n\nThe completion is patient. It's still there.",
        ],
        "cycle_event": [
            "The same ending keeps presenting itself.\n\nYou consider it. You step away. It returns.\n\nThe loop is about readiness, not the ending itself.",
        ],
        "normal_flow": [
            "A quiet close has been available all week.\n\nYou've noticed it. You haven't taken it.\n\nIt's still there when you're ready.",
        ],
    },
}

# MONTH: Identity/behavioral shift (past vs now comparison)
MONTH_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You're not demanding answers the way you used to.\n\nA month ago, you would have pushed harder for clarity. Now there's more tolerance for not-knowing.\n\nIt's not passivity. It's a different relationship with uncertainty.",
            "Something in how you seek understanding has changed.\n\nYou used to need the answer before you could move. Now you're moving anyway.\n\nThat's a shift.",
        ],
        "cycle_event": [
            "Your relationship with not-knowing is different than it was.\n\nThe need to figure things out is still there. But it's less urgent.\n\nYou're holding questions differently.",
        ],
        "normal_flow": [
            "A quiet change in how you approach confusion.\n\nNothing dramatic. But compare now to a month ago.\n\nYou're not reacting the same way.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You're not rushing the way you used to.\n\nThe impulse to move is still there. But there's a pause now that wasn't there before.\n\nYou're becoming someone who waits differently.",
            "Something in your pacing has shifted.\n\nWhere you once pushed forward, now you check. Where you once assumed readiness, now you confirm.\n\nThe change is gradual but real.",
        ],
        "cycle_event": [
            "Your relationship with timing is evolving.\n\nYou're not the same impulsive mover you were.\n\nThe pause has become part of how you operate.",
        ],
        "normal_flow": [
            "A subtle shift in your approach to action.\n\nYou used to be faster. Now you're more measured.\n\nIt's not hesitation — it's calibration.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "Your emotional response time is changing.\n\nYou used to react first, understand later. Now there's a small gap forming between stimulus and response.\n\nYou're not the same reactive person you were.",
            "Something in how you feel has shifted.\n\nThe feelings still come. But you're not living at their speed anymore.\n\nYou're holding them differently.",
        ],
        "cycle_event": [
            "Your relationship with your reactions is evolving.\n\nThere's more space now than there used to be.\n\nThe emotion is the same; your relationship to it has changed.",
        ],
        "normal_flow": [
            "A quiet shift in emotional processing.\n\nYou're not as fast to react.\n\nIt might look like slowing down. It's actually growing up.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You're not avoiding the old material the way you used to.\n\nWhen it surfaces now, you look at it differently. Less fear. More willingness to see.\n\nYou've changed in how you face what's unfinished.",
            "Something in your relationship with the past has shifted.\n\nYou used to run from it or get overwhelmed by it. Now you're steadier.\n\nThe past isn't as heavy when you're not resisting it.",
        ],
        "cycle_event": [
            "Your posture toward old patterns has evolved.\n\nYou're not the same person who used to be hijacked by them.\n\nThere's more ground under you now.",
        ],
        "normal_flow": [
            "A gradual change in how you relate to what's unresolved.\n\nIt's still there. But you're holding it differently.\n\nThe grip has loosened.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You're more comfortable in transition than you used to be.\n\nThe not-knowing where you're going isn't as destabilizing as it once was.\n\nYou've learned to move without a map.",
            "Something has changed in how you hold uncertainty.\n\nYou used to need the destination before you could move. Now you trust the movement itself.\n\nThat's growth.",
        ],
        "cycle_event": [
            "Your tolerance for ambiguity has expanded.\n\nChange without clear direction used to be threatening. Now it's just change.\n\nYou're different in this.",
        ],
        "normal_flow": [
            "A quiet increase in comfort with the unknown.\n\nYou're not clinging to clarity the way you were.\n\nThe open space is less scary.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "You're not fighting the mismatch the way you used to.\n\nWhen your rhythm and the world's rhythm don't match, you no longer try to force alignment.\n\nYou're trusting your pace more.",
            "Something has shifted in how you navigate external pressure.\n\nYou used to speed up or slow down to match. Now you hold your rhythm.\n\nThat's a significant change.",
        ],
        "cycle_event": [
            "Your relationship with external timing has evolved.\n\nYou're less willing to abandon your pace for someone else's.\n\nThe boundary is forming.",
        ],
        "normal_flow": [
            "A subtle shift in how you respond to timing pressure.\n\nYou're not automatically adjusting anymore.\n\nYour rhythm is becoming more your own.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You're letting go more easily than before.\n\nEndings that would have been painful a month ago now feel more natural.\n\nYou're not the same holder-on you were.",
            "Something has changed in your relationship with completion.\n\nThe resistance isn't as strong. The acceptance is forming.\n\nYou're becoming someone who can finish things.",
        ],
        "cycle_event": [
            "Your grip on what needs to end is loosening.\n\nYou're not fighting closures the way you used to.\n\nThere's more flow now.",
        ],
        "normal_flow": [
            "A gradual softening around endings.\n\nYou're not clinging as hard.\n\nCompletion is starting to feel less like loss.",
        ],
    },
}


# =============================================================================
# SIGNAL SELECTION ENGINE
# =============================================================================

def select_dominant_tension(
    day_class: DayClass,
    transit_stack: Dict[str, Any],
    chart_data: Optional[Dict] = None
) -> TransitTension:
    """
    Select ONE dominant tension based on transit conditions.
    
    Priority:
    1. Stacked events → specific tensions
    2. Single events → matched tensions
    3. Fallback → context-appropriate default
    """
    events = transit_stack.get("events", [])
    event_types = set(e.get("type", e) if isinstance(e, dict) else str(e) for e in events)
    
    # Stacked event combinations → specific tensions
    if "equinox" in event_types or "solstice" in event_types:
        if "new_moon" in event_types:
            return TransitTension.SHIFT_BEFORE_DIRECTION
        elif "full_moon" in event_types:
            return TransitTension.COMPLETION_RESISTANCE
        else:
            return TransitTension.INNER_PACE_OUTER_TIMING
    
    if "eclipse_solar" in event_types or "eclipse_lunar" in event_types:
        return TransitTension.SHIFT_BEFORE_DIRECTION
    
    if "new_moon" in event_types:
        return TransitTension.MOVEMENT_BEFORE_ALIGNMENT
    
    if "full_moon" in event_types:
        return TransitTension.FORCING_CLARITY
    
    # Day class fallbacks
    if day_class == DayClass.PHASE_SHIFT:
        return TransitTension.SHIFT_BEFORE_DIRECTION
    elif day_class == DayClass.CYCLE_EVENT:
        return TransitTension.REOPENING_UNRESOLVED
    else:
        return TransitTension.INNER_PACE_OUTER_TIMING


def select_natal_receiver(chart_data: Optional[Dict] = None) -> str:
    """
    Determine how the transit lands based on natal chart.
    Returns receiver type: emotional, mental, physical, relational, private
    """
    if not chart_data:
        return "private"  # Default for unknown chart
    
    moon_sign = chart_data.get("moon_sign", "").lower()
    sun_sign = chart_data.get("sun_sign", "").lower()
    rising_sign = chart_data.get("rising_sign", "").lower()
    
    # Moon sign indicates emotional processing style
    water_signs = ["cancer", "scorpio", "pisces"]
    fire_signs = ["aries", "leo", "sagittarius"]
    air_signs = ["gemini", "libra", "aquarius"]
    earth_signs = ["taurus", "virgo", "capricorn"]
    
    if moon_sign in water_signs:
        return "emotional"
    elif moon_sign in air_signs:
        return "mental"
    elif moon_sign in fire_signs:
        return "physical"
    elif moon_sign in earth_signs:
        return "physical"
    
    # Rising affects how it appears externally
    if rising_sign in ["libra", "gemini", "leo"]:
        return "relational"
    
    return "private"


def get_cause_sentence(tension: TransitTension, transit_stack: Dict[str, Any]) -> str:
    """
    Generate a SHORT, HUMAN cause sentence.
    No technical astrology - just the lived reason.
    """
    causes = TENSION_CAUSES.get(tension, ["Something is pressing."])
    
    # Add context from transit stack
    events = transit_stack.get("events", [])
    event_count = len(events)
    
    # Select cause deterministically
    seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    cause = causes[seed_hash % len(causes)]
    
    # Enhance if stacked events
    if event_count >= 2:
        stacked_additions = [
            " And more than one thing is happening at once.",
            " Multiple forces are converging.",
            " Several currents are meeting.",
        ]
        cause += stacked_additions[seed_hash % len(stacked_additions)]
    
    return cause


# =============================================================================
# VALIDATION
# =============================================================================

FAIL_PHRASES = [
    "you may notice",
    "today's quality",
    "inner compass",
    "energy",
    "alignment",
    "universe",
    "this period is about",
    "you're learning",
    "you are learning",
    "cosmic",
    "powerful transformation",
    "gentle recalibration",
]

def validate_narrative(body: str, altitude: str) -> Tuple[bool, str]:
    """
    Validate narrative against quality standards.
    Returns (is_valid, reason).
    """
    body_lower = body.lower()
    
    # Check for banned phrases
    for phrase in FAIL_PHRASES:
        if phrase in body_lower:
            return False, f"Contains banned phrase: '{phrase}'"
    
    # Altitude-specific validation
    if altitude == "week":
        # Must have repetition markers
        week_markers = ["more than once", "again", "returned", "several times", 
                       "same", "each time", "loop", "pattern", "recurring", "back"]
        if not any(m in body_lower for m in week_markers):
            return False, "Week narrative lacks repetition markers"
    
    elif altitude == "month":
        # Must have shift markers (past vs now)
        month_markers = ["used to", "not the same", "changed", "different",
                        "anymore", "was", "now there", "shift", "evolving", "becoming"]
        if not any(m in body_lower for m in month_markers):
            return False, "Month narrative lacks shift markers"
    
    elif altitude == "today":
        # Must have immediacy
        today_markers = ["you", "today", "now", "right now", "this", 
                        "keep", "feeling", "happening"]
        if not any(m in body_lower for m in today_markers):
            return False, "Today narrative lacks immediacy"
    
    return True, "Valid"


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_astrology_signal(
    altitude: str,
    day_class: str,
    transit_stack: Dict[str, Any],
    chart_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate a single altitude narrative using the 4-layer signal engine.
    
    Returns:
    {
        "title": str,
        "body": str,
        "cause": str | None,
        "bridge": str | None,
        "technical": {...}
    }
    """
    # Normalize day class
    if isinstance(day_class, str):
        try:
            day_class_enum = DayClass(day_class)
        except ValueError:
            day_class_enum = DayClass.NORMAL_FLOW
    else:
        day_class_enum = day_class
    
    # LAYER 1: Select dominant tension
    tension = select_dominant_tension(day_class_enum, transit_stack, chart_data)
    
    # LAYER 2: Determine natal receiver
    receiver = select_natal_receiver(chart_data)
    
    # LAYER 3: Get altitude-appropriate narratives
    if altitude == "today":
        narratives_by_class = TODAY_NARRATIVES.get(tension, TODAY_NARRATIVES[TransitTension.FORCING_CLARITY])
        title = "Today"
    elif altitude == "week":
        narratives_by_class = WEEK_NARRATIVES.get(tension, WEEK_NARRATIVES[TransitTension.FORCING_CLARITY])
        title = "This Week"
    elif altitude == "month":
        narratives_by_class = MONTH_NARRATIVES.get(tension, MONTH_NARRATIVES[TransitTension.FORCING_CLARITY])
        title = "This Month"
    else:
        return {"title": altitude.title(), "body": "Unknown altitude.", "cause": None, "bridge": None}
    
    # Get narratives for this day class
    day_class_str = day_class_enum.value
    narratives = narratives_by_class.get(day_class_str, narratives_by_class.get("normal_flow", []))
    
    # If no narratives for this class, fallback
    if not narratives:
        narratives = list(narratives_by_class.values())[0] if narratives_by_class else ["Something is present."]
    
    # Select deterministically
    seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    altitude_offsets = {"today": 0, "week": 7, "month": 31}
    seed_str = f"{seed}_{altitude}_{tension.value}"
    seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    offset = altitude_offsets.get(altitude, 0)
    
    body = narratives[(seed_hash + offset) % len(narratives)]
    
    # Validate
    is_valid, reason = validate_narrative(body, altitude)
    if not is_valid:
        logger.warning(f"[AstroSignal] Validation failed for {altitude}: {reason}")
        # Try next narrative
        if len(narratives) > 1:
            body = narratives[(seed_hash + offset + 1) % len(narratives)]
    
    # Generate cause (only for today, optional for others)
    cause = None
    if altitude == "today" and day_class_enum in [DayClass.PHASE_SHIFT, DayClass.CYCLE_EVENT]:
        cause = get_cause_sentence(tension, transit_stack)
    
    # Generate bridge (optional)
    bridge = None
    
    # Get receiver hint for technical
    receiver_texts = NATAL_RECEIVERS.get(receiver, NATAL_RECEIVERS["private"])
    receiver_hint = receiver_texts[seed_hash % len(receiver_texts)]
    
    # Build technical details
    events = transit_stack.get("events", [])
    event_names = [
        e.get("name", e.get("type", "unknown")) if isinstance(e, dict) else str(e)
        for e in events
    ]
    
    technical = {
        "tension": tension.value.replace("_", " ").title(),
        "receiver": receiver,
        "receiver_hint": receiver_hint,
        "day_class": day_class_str,
        "transits": event_names if event_names else None,
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
    
    return {
        "title": title,
        "body": body,
        "cause": cause,
        "bridge": bridge,
        "technical": technical,
    }
