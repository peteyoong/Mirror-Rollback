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
# RULE: Must describe WHAT USER IS DOING, not what is happening to them
TODAY_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You open the thing. You stare at it. You close it. Then you open it again. You're trying to decide something that isn't ready to be decided.",
            "You draft the message. Delete it. Redraft. Delete again. You know what you want to say. You just can't land on how to say it.",
            "You keep checking — the email, the text, the conversation you're replaying. You're looking for an answer that isn't there yet.",
        ],
        "cycle_event": [
            "You catch yourself thinking about it again. You thought you'd let it go an hour ago. You didn't.",
            "You're running the same scenario in your head. Different angles, same question. No landing.",
            "You ask yourself what you think. Then second-guess it. Then ask again.",
        ],
        "normal_flow": [
            "You move to the next task, but part of your mind stays on the last one. Unfinished.",
            "You're half-doing something. The other half is still chewing on a question you haven't answered.",
            "You notice you've been staring at the same thing for a while. Thinking, but not arriving anywhere.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You start to do the thing. Then stop. Then almost start again. Something keeps catching you right before you move.",
            "You reach for your phone to send it. Then you put it down. Then you pick it up again. You're ready. But you're not.",
            "You've said 'I'm going to' three times today. You haven't yet. You're not stalling — you're waiting for something to click.",
        ],
        "cycle_event": [
            "You feel the push to act. You hold back. The push comes again. You hold back again.",
            "You want to move forward. Something keeps pulling you back to check one more time.",
            "You're pacing — physically or mentally. Ready to go, but the green light isn't there.",
        ],
        "normal_flow": [
            "You've been meaning to start that thing all day. You haven't. Not avoidance — just not time yet.",
            "You think about doing it, then do something else. Then think about it again.",
            "Your to-do list has one thing that keeps not getting done. Not because you don't want to.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "Someone says something. You snap back. Then you wonder why you reacted that hard. It wasn't about them.",
            "You feel the heat rise before you understand why. You're reacting to something you haven't processed yet.",
            "You catch yourself mid-response — too fast, too sharp. The feeling got there before the thought.",
        ],
        "cycle_event": [
            "You're irritated by something small. Too irritated. The size doesn't match. Something else is under it.",
            "You tear up at something minor. That's not the thing. There's something behind it.",
            "You notice you're tense. You don't know why. Your body figured it out before you did.",
        ],
        "normal_flow": [
            "You sigh heavier than the moment calls for. Something's processing.",
            "You find yourself short with someone. Not because of them. Because of something unnamed.",
            "You feel off. Can't pinpoint it. Your system knows something your mind hasn't caught up to.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You're thinking about them again. The person. The thing. You thought you were past it. You're not.",
            "A name shows up in your head. A memory surfaces. Same one as before. It's back.",
            "You find yourself replaying a conversation that ended months ago. Editing what you should have said.",
        ],
        "cycle_event": [
            "A song comes on. You're right back there. The thing you thought you handled — it's not handled.",
            "Someone mentions something unrelated, and your mind jumps to the old thing. Still loaded.",
            "You catch yourself wondering about someone you decided to stop wondering about.",
        ],
        "normal_flow": [
            "A familiar ache shows up. Not loud. Just there. Something old, asking to be noticed.",
            "You scroll past a photo. Your chest tightens slightly. Still live.",
            "A thought from the past visits. You don't invite it. It just appears.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You wake up and something feels different. You can't point to what. You're not the same as yesterday, but you don't know what changed.",
            "You make a decision, then unmake it. Make another. Unmake that too. The ground keeps shifting under your choices.",
            "You start three things, finish none. Not because you're scattered — because none of them feel like the right one anymore.",
        ],
        "cycle_event": [
            "You feel restless in a space that was fine last week. Something outgrew something.",
            "You lose interest mid-task. Not lazy. Just... done with it. Before it's done.",
            "You hear yourself say 'I don't know' more than usual. Not confusion. Recalibration.",
        ],
        "normal_flow": [
            "You pause mid-sentence. Forget what you were going to say. Not tired — just shifting.",
            "You pick up your phone, then put it down. Pick up a book. Put that down too. Nothing lands.",
            "You feel a low hum of 'what now' in the background. No urgency. Just present.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "Everyone's moving fast. You're moving slow. Or they're dragging and you want to sprint. Either way — mismatch.",
            "You're asked to respond now. Your insides say 'not yet.' You give them something, but it's not your real answer.",
            "You show up on time, but you're not ready. You needed ten more minutes your schedule didn't give you.",
        ],
        "cycle_event": [
            "You feel rushed by something that shouldn't be rushing you. The pressure is external, not real.",
            "Someone's waiting for your answer. You don't have it. You give them a placeholder.",
            "You're behind on everything but actually right on time by your own measure. The gap is friction.",
        ],
        "normal_flow": [
            "You catch yourself saying 'in a minute' more than usual. Your pace and the world's aren't syncing.",
            "You want to linger on something. Life wants you to move on. You compromise badly.",
            "You feel slightly out of step. Nothing dramatic. Just a half-beat off.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You could end it. The conversation, the project, the thing. You keep it open anyway. You're not ready to close it.",
            "You hover over 'send' and don't press it. You check the draft one more time. And again. Completion is available. You're not taking it.",
            "You know it's done. You keep picking it up anyway. Looking for something more. There isn't anything more.",
        ],
        "cycle_event": [
            "You reread the final version, looking for something to fix. Not because it needs fixing. Because ending feels too fast.",
            "You add one more thing. Then another. Not improving — delaying.",
            "You walk away from the finished thing, then come back. Just to look at it. Not done letting go.",
        ],
        "normal_flow": [
            "You finish something and don't feel finished. There's a gap between done and accepted.",
            "You sit with a completed task longer than you need to. Something isn't landing.",
            "You pause before marking it complete. Not checking — just not ready.",
        ],
    },
}

# WEEK: Recurring loop (attempt → interruption → return)
# RULE: Must show SPECIFIC BEHAVIOR that has repeated multiple times
WEEK_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You've opened that thing more than once this week. Stared at it. Closed it. Opened it again.\n\nEach time, you think you'll finally figure it out. Each time, you don't.\n\nYou're not avoiding it. You keep coming back. The answer just isn't arriving.",
            "You've asked yourself the same question at least three times.\n\nYou think you have the answer. Then you doubt it. Then you ask again.\n\nThat loop — it's been running all week.",
        ],
        "cycle_event": [
            "You've caught yourself drifting back to this more than once.\n\nYou move on to other things. Then you're back. Thinking about it again.\n\nThe pattern is visible now.",
        ],
        "normal_flow": [
            "You've noticed the same thought returning in quiet moments.\n\nMorning. Mid-afternoon. Right before sleep.\n\nNot urgent. Just persistent.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You've said 'I'm going to do that' more than once this week. You haven't.\n\nNot because you don't want to. Because something keeps catching you right before you start.\n\nThat hesitation has shown up multiple times now.",
            "You've reached for it several times. Each time, you pull back.\n\nReach. Pull back. Reach again.\n\nThe loop is the same every time.",
        ],
        "cycle_event": [
            "You've felt ready to move forward more than once.\n\nEach time, something makes you pause. Then you feel ready again.\n\nThe readiness keeps arriving. The action doesn't.",
        ],
        "normal_flow": [
            "That thing on your list — you've looked at it several times.\n\nEach time, you do something else.\n\nNot avoiding. Just not yet.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "You've snapped at someone more than once this week. Then wondered why.\n\nDifferent people. Different moments. Same overreaction.\n\nSomething's been running under the surface.",
            "You've felt the heat rise several times. Caught yourself mid-reaction.\n\nEach time, the trigger was small. The response was big.\n\nThat gap keeps showing up.",
        ],
        "cycle_event": [
            "You've noticed the same feeling surfacing in different situations.\n\nAnnoyed. Then fine. Then annoyed again.\n\nThe loop is emotional.",
        ],
        "normal_flow": [
            "You've sighed heavily more than usual this week.\n\nNot always at anything specific.\n\nJust releasing something you haven't named.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You've thought about them again. More than once.\n\nYou moved on. Then you didn't. Then you thought you did. Then there they were again.\n\nThe past keeps visiting.",
            "That thing from before — it's come back multiple times this week.\n\nYou don't summon it. It just shows up.\n\nSame memory. Same weight.",
        ],
        "cycle_event": [
            "A familiar feeling has surfaced more than once.\n\nDifferent triggers. Same undertone.\n\nIt's not new. It's returning.",
        ],
        "normal_flow": [
            "You've caught yourself remembering something more than once.\n\nNot dwelling. Just... noticing it's still there.\n\nQuiet, but present.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You've changed your mind more than once this week.\n\nDecided something. Then undecided. Then decided something else.\n\nNothing is sticking because everything is shifting.",
            "You've started things and stopped them multiple times.\n\nNot because they're wrong. Because something about them doesn't fit anymore.\n\nThe ground keeps moving.",
        ],
        "cycle_event": [
            "You've felt restless in spaces that were fine last week.\n\nMore than once, you've looked around and thought: this doesn't feel right.\n\nSomething outgrew something.",
        ],
        "normal_flow": [
            "You've said 'I don't know' more than usual.\n\nNot confused. Just... not landed.\n\nThe answer keeps moving.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "You've felt rushed more than once this week. By things that shouldn't be rushing you.\n\nYou speed up. It doesn't feel right. You slow down. They push again.\n\nThe mismatch keeps repeating.",
            "You've given placeholder answers several times.\n\n'I'll let you know.' 'I'm thinking about it.' 'Soon.'\n\nYou're buying time because your real timing isn't matching theirs.",
        ],
        "cycle_event": [
            "You've felt out of sync more than once.\n\nWith the day. With someone's pace. With what's being asked.\n\nThe friction is recurring.",
        ],
        "normal_flow": [
            "You've said 'in a minute' more than usual.\n\nNot stalling. Just needing a beat more than the moment allows.\n\nA small gap, but consistent.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You've almost finished it more than once this week. Then pulled back.\n\nChecked it again. Tweaked something. Kept it open.\n\nThe ending is available. You keep not taking it.",
            "You've hovered over 'done' several times.\n\nThen found one more thing to adjust. Then one more.\n\nNot improving. Delaying.",
        ],
        "cycle_event": [
            "You've circled back to something that's finished more than once.\n\nJust to look at it. Just to make sure.\n\nNot checking. Lingering.",
        ],
        "normal_flow": [
            "You've paused before closing things out this week.\n\nSmall pauses. But repeated.\n\nThe finish line keeps feeling premature.",
        ],
    },
}

# MONTH: Identity/behavioral shift (past vs now comparison)
# RULE: Must show SPECIFIC BEHAVIORAL CHANGE - what user DOES differently now
MONTH_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "A month ago, you would have pushed harder. Forced the answer. Demanded to know.\n\nNow you're doing something different. You're sitting with the question longer.\n\nYou still want to know. But you're not grabbing for it the same way.",
            "You used to need the answer before you could move. You don't do that anymore.\n\nYou move anyway. Even when it's unclear.\n\nThat's not how you used to operate.",
        ],
        "cycle_event": [
            "You're holding uncertainty differently.\n\nBefore, you'd chase the answer until you had it. Now you let it come.\n\nThe need to know is still there. The grip is lighter.",
        ],
        "normal_flow": [
            "You're not as urgent about figuring things out.\n\nThat impatience — the one that used to show up — it's quieter now.\n\nYou're still curious. Just less frantic.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You used to jump. Now you pause first.\n\nThe impulse still fires. But you're not acting on it as fast.\n\nThat pause? It wasn't there a month ago.",
            "You've slowed down. Not because you're tired — because you're checking.\n\nBefore, you'd go. Now you verify.\n\nThe change happened without you noticing.",
        ],
        "cycle_event": [
            "You're not pushing as hard as you used to.\n\nThe urgency is still there. But you're not letting it drive.\n\nSomewhere along the way, you started waiting.",
        ],
        "normal_flow": [
            "You're more patient than you were.\n\nNot infinitely. But noticeably.\n\nYou're giving things time that you used to try to force.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "You used to react first, think later. That's changing.\n\nNow there's a beat. A small gap between feeling and responding.\n\nYou're catching yourself before you speak. That's new.",
            "A month ago, you'd have already said the thing. Now you hold it.\n\nThe feeling still rises. But you're not letting it out as fast.\n\nYou're editing in real time.",
        ],
        "cycle_event": [
            "Your responses are slower than they used to be.\n\nNot sluggish. Just measured.\n\nYou're giving yourself time to choose the reaction.",
        ],
        "normal_flow": [
            "You're less reactive.\n\nStill feeling things. But not blurting.\n\nThe filter is thicker than it was.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You used to avoid the old stuff. Change the subject. Look away.\n\nNow you're letting it sit there. Not running.\n\nThat's different. That took something.",
            "The past shows up, and you don't flinch as hard.\n\nYou used to shut it down fast. Now you look at it.\n\nYou're steadier with your own history.",
        ],
        "cycle_event": [
            "You're not dodging it the way you used to.\n\nWhen the old material surfaces, you let it be there.\n\nThe fear of it is fading.",
        ],
        "normal_flow": [
            "You're handling the old stuff better.\n\nNot processing it all. Just not running from it.\n\nThat's progress you didn't plan.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You used to need to know where you were going. Now you just go.\n\nThe destination isn't clear. You're moving anyway.\n\nThat's not how you used to travel.",
            "You're more comfortable in the unknown than you were.\n\nBefore, ambiguity made you freeze. Now it makes you curious.\n\nThe relationship with uncertainty has shifted.",
        ],
        "cycle_event": [
            "You're not demanding a map the way you used to.\n\nYou're letting the path reveal itself.\n\nLess control. More trust.",
        ],
        "normal_flow": [
            "You're okay with not knowing.\n\nNot thrilled. But okay.\n\nThat tolerance wasn't there a month ago.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "You used to speed up when they wanted you to. Now you don't.\n\nYou hold your pace. Even when it's uncomfortable.\n\nThat boundary is new.",
            "You're not adjusting your rhythm as quickly.\n\nThe world pushes. You don't fold.\n\nYou've started trusting your own timing more.",
        ],
        "cycle_event": [
            "You're less apologetic about your pace.\n\nYou used to rush to match. Now you state your timing and stick to it.\n\nThat confidence wasn't there before.",
        ],
        "normal_flow": [
            "You're moving at your own speed more often.\n\nNot always. But more.\n\nThe accommodation reflex is softening.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You used to hold on longer. Past the point. Past the use.\n\nNow you're setting things down faster.\n\nNot perfectly. But more than before.",
            "Endings used to feel like loss. Now they feel like release.\n\nThat shift didn't happen overnight. But it happened.",
        ],
        "cycle_event": [
            "You're letting go easier.\n\nThe grip that used to be automatic — it's loosening.\n\nYou're closing chapters you used to keep open.",
        ],
        "normal_flow": [
            "You're finishing things you used to leave open.\n\nSmall things. But consistently.\n\nThe pattern is changing.",
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
# VALIDATION (v7 Behavioral Edge)
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
    "something is happening",
    "you are experiencing",
    "that's growth",
    "this is about",
]

def validate_narrative(body: str, altitude: str) -> Tuple[bool, str]:
    """
    Validate narrative against v7 behavioral edge standards.
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
        week_markers = ["more than once", "multiple times", "several times", "again",
                       "same", "each time", "loop", "pattern", "repeated", "returning"]
        if not any(m in body_lower for m in week_markers):
            return False, "Week narrative lacks repetition markers"
    
    elif altitude == "month":
        # Must have shift markers (past vs now)
        month_markers = ["used to", "now you", "a month ago", "before", "anymore",
                        "that wasn't there", "that's new", "that's different",
                        "you don't do that", "you're not", "that's not how", "now there's"]
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
