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
# RULE: Must have ACTION → BREAK POINT → recognition
# BREAK POINT phrases: "then...", "but...", "doesn't land", "doesn't stick", "something catches", "you pause", "you pull back"
TODAY_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You open the thing. You stare at it. You close it. Then you open it again. It doesn't land. You're trying to decide something that isn't ready to be decided.",
            "You draft the message. Delete it. Redraft. Then delete again. It doesn't stick. You know what you want to say — but something catches every time you try.",
            "You check in with yourself. Ask what you think. Then doubt it. Ask again. Nothing settles. You're looking for certainty that isn't available.",
        ],
        "cycle_event": [
            "You think you've got it figured out. Then something shifts. You don't. The answer keeps slipping right when you reach for it.",
            "You run the scenario in your head. It makes sense. Then you run it again — and it doesn't. Something's not clicking.",
            "You try to land on a decision. It almost sticks. Then it doesn't. You pull back to think again.",
        ],
        "normal_flow": [
            "You move to the next task. But part of your mind stays behind. It doesn't release. Something's still chewing on the last thing.",
            "You tell yourself you're done thinking about it. Then you catch yourself thinking about it. It didn't let go.",
            "You reach for the answer. It almost forms. Then it dissolves. Unfinished.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You start to do the thing. Then stop. Something catches. You almost start again — but you don't. The break happens right before action.",
            "You reach for your phone to send it. Then you put it down. You pick it up again. Then put it down again. You're ready — but it doesn't land.",
            "You say 'I'm going to.' Then you don't. You say it again later. Still don't. Something keeps pulling you back at the edge.",
        ],
        "cycle_event": [
            "You feel the push to move. You lean forward. Then something catches. You pull back. The momentum doesn't stick.",
            "You're about to act. Then you pause. Check one more thing. The action dissolves into waiting.",
            "You gear up. Then you don't go. The readiness doesn't convert. Something breaks the chain.",
        ],
        "normal_flow": [
            "You think about starting. Then you do something else. Then you think about it again. It doesn't happen.",
            "You mean to do it. But you don't. Not avoidance. Something catches you before you begin.",
            "You're ready. But you wait. The wait extends. The ready doesn't become action.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "Someone says something. You snap back. Then you pause. That was too hard. The reaction came before the thought — and it didn't match.",
            "You feel the heat rise. You open your mouth. Then catch yourself. Almost too late. The feeling got there first.",
            "You respond. Then regret it. The words came out before you understood why. Something broke the filter.",
        ],
        "cycle_event": [
            "You're irritated. Then you realize — at nothing real. The size doesn't match the trigger. Something else is running underneath.",
            "You tear up. Then stop. That wasn't about this. The emotion hijacked the moment.",
            "You snap. Then catch yourself. That wasn't them. Something slipped through.",
        ],
        "normal_flow": [
            "You sigh. Then notice — that was heavier than the moment called for. Something's processing that you haven't named.",
            "You're short with someone. Then realize — they didn't deserve that. Something unnamed pushed through.",
            "You feel off. Can't pinpoint it. But your body knows something. Your mind hasn't caught up yet.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You're thinking about them again. Then catch yourself. You thought you were past it. You're not. The past didn't close.",
            "A memory surfaces. You push it away. Then it's back. Same one. It doesn't stay down.",
            "You replay the conversation. Then stop. You've done this before. It doesn't change anything — but you keep going back.",
        ],
        "cycle_event": [
            "A song comes on. You're right back there. Then you notice — it still has weight. It didn't finish.",
            "Someone mentions something. Your mind jumps to the old thing. Still loaded. Still live.",
            "You catch yourself wondering about someone. Then stop. You decided to stop doing that. But you didn't.",
        ],
        "normal_flow": [
            "A familiar ache shows up. Then fades. Then shows up again. Something old is asking to be seen.",
            "You scroll past a photo. Your chest tightens. Then you keep scrolling. But the feeling stays.",
            "A thought visits. You didn't invite it. Then you notice — you're still holding it.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You wake up. Something feels different. Then you try to name it. You can't. The shift happened — but the shape didn't form.",
            "You make a decision. Then unmake it. Make another. Unmake that too. Nothing sticks. The ground keeps moving.",
            "You start something. Then lose the thread. Start another. Same thing. Nothing lands because everything is shifting.",
        ],
        "cycle_event": [
            "You feel restless. Then realize — in a space that was fine last week. Something outgrew something. But you don't know what.",
            "You lose interest mid-task. Then notice — not tired. Just done. Before it's done. Something moved on without you.",
            "You say 'I don't know' again. Then catch yourself — you've said that a lot. Not confusion. Recalibration.",
        ],
        "normal_flow": [
            "You pause mid-sentence. Forget what you were going to say. Then it doesn't come back. You shrug. Something shifted.",
            "You pick up your phone. Put it down. Pick up a book. Put that down too. Nothing lands. You don't know what you want.",
            "You feel a hum of 'what now.' Then it fades. Then it's back. No urgency. Just present.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "Everyone's moving fast. You're not. Then you try to speed up. It doesn't fit. Your rhythm and theirs — mismatch.",
            "You're asked to respond now. You try. Then it comes out wrong. Your insides weren't ready. The words didn't match.",
            "You show up on time. But you're not there. Then you realize — you needed ten more minutes you didn't have.",
        ],
        "cycle_event": [
            "You feel rushed. Then notice — nothing's actually urgent. The pressure is external. Your pace doesn't match.",
            "Someone waits for your answer. You give them something. Then catch yourself — that wasn't your real answer.",
            "You're behind. Then realize — only by their clock. By your clock, you're on time. That gap is the friction.",
        ],
        "normal_flow": [
            "You say 'in a minute.' Then say it again. Then again. Your pace and the world's aren't syncing.",
            "You want to linger. Life says move. Then you compromise — badly. The middle doesn't work.",
            "You feel a half-beat off. Then adjust. But it doesn't fix. Slightly out of step — and staying that way.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You could end it. You don't. Then you look at it again. Still not ending it. Something catches before the close.",
            "You hover over 'send.' Then don't press it. Check the draft one more time. Then one more. It's ready — but you're not letting go.",
            "You know it's done. Then you pick it up again. Check it. Put it down. Check it again. Completion is available — you're not taking it.",
        ],
        "cycle_event": [
            "You reread the final version. Looking for something to fix. Then stop. It doesn't need fixing. You're delaying — not improving.",
            "You add one more thing. Then another. Then catch yourself. Not making it better. Making it longer.",
            "You walk away from the finished thing. Then come back. Then walk away again. Something won't let you close it.",
        ],
        "normal_flow": [
            "You finish something. But don't feel finished. Then notice — the gap between done and accepted. That's where you're stuck.",
            "You sit with a completed task. Then realize — longer than needed. Something isn't landing.",
            "You pause before marking it complete. Then pause again. Not checking — just not ready to let go.",
        ],
    },
}

# WEEK: Recurring loop (attempt → interruption → return)
# RULE: Must show loop with BREAK POINT - where it fails each time
WEEK_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "You've opened that thing more than once this week. Stared at it. Then closed it.\n\nEach time, you think you'll finally figure it out. Then you don't. Something catches right before the landing.\n\nThe answer keeps dissolving when you reach for it.",
            "You've asked yourself the same question at least three times.\n\nYou think you have the answer. Then doubt it. Then ask again. Each time — the certainty doesn't stick.\n\nThat loop has been running all week.",
        ],
        "cycle_event": [
            "You've caught yourself drifting back to this more than once.\n\nYou move on. Then you're back. Then you move on again. But it doesn't release.\n\nThe question keeps pulling you.",
        ],
        "normal_flow": [
            "You've noticed the same thought returning.\n\nMorning. Afternoon. Evening. Each time you think you're done with it — then it's back.\n\nIt doesn't let go.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You've said 'I'm going to do that' more than once this week. Then you didn't.\n\nNot because you don't want to. Something catches you right before you start. Every time.\n\nThe action keeps dissolving at the edge.",
            "You've reached for it several times. Then pulled back.\n\nReach. Something catches. Pull back. Repeat.\n\nThe break point is always the same — right before the doing.",
        ],
        "cycle_event": [
            "You've felt ready to move more than once.\n\nEach time, you pause. Check one more thing. Then the moment passes.\n\nThe readiness doesn't convert. Something keeps breaking the chain.",
        ],
        "normal_flow": [
            "That thing on your list — you've looked at it several times.\n\nEach time, you almost start. Then you don't. Then you look at it again.\n\nThe gap stays the same.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "You've snapped at someone more than once this week. Then caught yourself.\n\nDifferent people. Different moments. Same overreaction. Same pause after.\n\nThe pattern is: react first, then realize it was too much.",
            "You've felt the heat rise several times. Each time — caught yourself mid-response.\n\nThe trigger was small. The response was big. Then you pulled back.\n\nThat gap keeps showing up.",
        ],
        "cycle_event": [
            "You've noticed the same feeling surfacing in different situations.\n\nAnnoyed. Then fine. Then annoyed again. Each time — at something that shouldn't matter that much.\n\nThe size keeps not matching the trigger.",
        ],
        "normal_flow": [
            "You've sighed heavily more than usual this week.\n\nNot always at anything specific. Then you notice — something's processing underneath.\n\nIt keeps coming through in small ways.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You've thought about them again. More than once.\n\nYou moved on. Then you didn't. Then you thought you did — then there they were again.\n\nThe past doesn't stay past. It keeps surfacing.",
            "That thing from before has come back multiple times this week.\n\nYou don't summon it. It just shows up. Then you push it away. Then it's back.\n\nSame memory. Same weight. Same loop.",
        ],
        "cycle_event": [
            "A familiar feeling has surfaced more than once.\n\nDifferent triggers. Same undertone. Then it fades. Then it's back.\n\nIt's not new. It's returning.",
        ],
        "normal_flow": [
            "You've caught yourself remembering something more than once.\n\nNot dwelling. Just noticing — it's still there. Then you move on. Then you notice it again.\n\nQuiet, but persistent.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You've changed your mind more than once this week.\n\nDecided something. Then undecided. Made another choice. Then unmade that too.\n\nNothing sticks because everything keeps shifting underneath.",
            "You've started things and stopped them multiple times.\n\nNot because they're wrong. Because something catches — they don't feel right anymore.\n\nThe fit keeps breaking.",
        ],
        "cycle_event": [
            "You've felt restless in spaces that were fine last week.\n\nMore than once, you've looked around and thought: this doesn't fit. Then you're not sure what would.\n\nThe mismatch keeps repeating.",
        ],
        "normal_flow": [
            "You've said 'I don't know' more than usual.\n\nNot confused. Just not landed. Then you try to land somewhere — and you don't.\n\nThe answer keeps moving.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "You've felt rushed more than once this week. By things that shouldn't be rushing you.\n\nYou speed up. It doesn't feel right. You slow down. They push again.\n\nThe mismatch keeps repeating at the same break point.",
            "You've given placeholder answers several times.\n\n'I'll let you know.' 'I'm thinking about it.' Each time — your real answer wasn't ready.\n\nBut the moment didn't wait.",
        ],
        "cycle_event": [
            "You've felt out of sync more than once.\n\nWith the day. With someone's pace. Each time you adjust — something catches. The fit doesn't land.\n\nThe friction keeps returning.",
        ],
        "normal_flow": [
            "You've said 'in a minute' more than usual.\n\nNot stalling. Just needing one more beat. Then another. Then another.\n\nThe gap stays consistent.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You've almost finished it more than once this week. Then pulled back.\n\nChecked it again. Tweaked something. Kept it open. Each time — right at the edge of done.\n\nThe ending is available. But you keep not taking it.",
            "You've hovered over 'done' several times.\n\nThen found one more thing to adjust. Then one more. Each time — the close doesn't happen.\n\nDelaying, not improving.",
        ],
        "cycle_event": [
            "You've circled back to something that's finished more than once.\n\nJust to look at it. Just to make sure. Then leave. Then come back.\n\nThe release doesn't land.",
        ],
        "normal_flow": [
            "You've paused before closing things out this week.\n\nSmall pauses. But repeated. Each time — not checking. Just hesitating.\n\nThe finish line keeps feeling premature.",
        ],
    },
}

# MONTH: Identity/behavioral shift (past vs now comparison)
# RULE: Must show behavioral change with BREAK POINT - what used to happen vs what happens now
MONTH_NARRATIVES = {
    TransitTension.FORCING_CLARITY: {
        "phase_shift": [
            "A month ago, you would have pushed harder. Forced the answer. Demanded to know.\n\nNow you do something different. You reach for certainty — then pause. Let it sit.\n\nThat pause wasn't there before. Something changed in how you hold not-knowing.",
            "You used to need the answer before you could move. Now you try to force it — then stop.\n\nThe grab doesn't work the same way. So you're learning to move anyway.\n\nThat's not how you used to operate.",
        ],
        "cycle_event": [
            "You're holding uncertainty differently.\n\nBefore, you'd chase the answer until something broke. Now you chase — then catch yourself. Pull back.\n\nThe grip is lighter. That took something.",
        ],
        "normal_flow": [
            "You're not as urgent about figuring things out.\n\nThat impatience — the one that used to drive you — it still fires. Then it doesn't land the same way.\n\nYou're still curious. Just less frantic about it.",
        ],
    },
    TransitTension.MOVEMENT_BEFORE_ALIGNMENT: {
        "phase_shift": [
            "You used to jump. Now you jump — then pause mid-air.\n\nThe impulse still fires. But something catches you before you land. You check. Then move.\n\nThat check wasn't there a month ago.",
            "You've slowed down. Not because you're tired — because something breaks the chain earlier now.\n\nBefore, you'd go. Now you start to go — then verify.\n\nThe change happened without you noticing.",
        ],
        "cycle_event": [
            "You're not pushing as hard as you used to.\n\nThe urgency is still there. It rises. Then — something catches. You don't follow through the same way.\n\nSomewhere along the way, you started waiting.",
        ],
        "normal_flow": [
            "You're more patient than you were.\n\nNot infinitely. But noticeably. The push comes — then doesn't complete.\n\nYou're giving things time that you used to try to force.",
        ],
    },
    TransitTension.REACTING_BEFORE_UNDERSTANDING: {
        "phase_shift": [
            "You used to react first, think later. That's changing.\n\nNow the reaction rises — then you catch it. A small gap. A beat before you speak.\n\nThat beat is new. You're editing in real time.",
            "A month ago, you'd have already said the thing. Now you start to — then hold it.\n\nThe feeling still rises. It tries to become words. Then something catches.\n\nYou're not letting it out as fast.",
        ],
        "cycle_event": [
            "Your responses are slower than they used to be.\n\nNot sluggish. Just — the reaction starts, then pauses. You choose instead of blurt.\n\nThat's different.",
        ],
        "normal_flow": [
            "You're less reactive.\n\nThe feeling comes up. You start to express it — then don't. The filter caught something.\n\nIt's thicker than it was.",
        ],
    },
    TransitTension.REOPENING_UNRESOLVED: {
        "phase_shift": [
            "You used to avoid the old stuff. Change the subject. Look away.\n\nNow it surfaces — and you let it sit there. You don't run. Something broke the avoidance pattern.\n\nThat steadiness wasn't there before.",
            "The past shows up, and you don't flinch as hard.\n\nBefore, it would land — and you'd shut it down fast. Now it lands — and you look at it.\n\nThe fear doesn't complete the way it used to.",
        ],
        "cycle_event": [
            "You're not dodging it the way you used to.\n\nThe old material surfaces. You start to push it away — then don't.\n\nSomething shifted in how you face it.",
        ],
        "normal_flow": [
            "You're handling the old stuff better.\n\nIt arrives. You notice. You start to resist — then let it be there instead.\n\nThat's progress you didn't plan.",
        ],
    },
    TransitTension.SHIFT_BEFORE_DIRECTION: {
        "phase_shift": [
            "You used to need to know where you were going. Now you try to figure it out — then stop.\n\nThe destination isn't clear. You move anyway. The need for certainty doesn't complete.\n\nThat's not how you used to travel.",
            "You're more comfortable in the unknown than you were.\n\nBefore, ambiguity made you freeze. Now it starts to — then curiosity takes over.\n\nThe relationship with uncertainty has shifted.",
        ],
        "cycle_event": [
            "You're not demanding a map the way you used to.\n\nThe urge to control the path arises. Then it doesn't follow through.\n\nYou're letting things reveal themselves instead.",
        ],
        "normal_flow": [
            "You're okay with not knowing.\n\nNot thrilled. But okay. The anxiety rises — then dissipates faster.\n\nThat tolerance wasn't there a month ago.",
        ],
    },
    TransitTension.INNER_PACE_OUTER_TIMING: {
        "phase_shift": [
            "You used to speed up when they wanted you to. Now you start to — then stop.\n\nYou hold your pace. Even when it's uncomfortable. Something catches the accommodation reflex.\n\nThat boundary is new.",
            "You're not adjusting your rhythm as quickly.\n\nThe world pushes. You feel the pull to match. Then you don't.\n\nYou've started trusting your own timing more.",
        ],
        "cycle_event": [
            "You're less apologetic about your pace.\n\nYou start to rush — then catch yourself. State your timing. Stick to it.\n\nThat confidence wasn't there before.",
        ],
        "normal_flow": [
            "You're moving at your own speed more often.\n\nNot always. But more. The pressure to match arises — then doesn't complete.\n\nYour rhythm is becoming more your own.",
        ],
    },
    TransitTension.COMPLETION_RESISTANCE: {
        "phase_shift": [
            "You used to hold on longer. Past the point. Past the use.\n\nNow the grip starts — then loosens. You're setting things down faster.\n\nNot perfectly. But more than before.",
            "Endings used to feel like loss. Now they start to — then something shifts. Release becomes possible.\n\nThat shift didn't happen overnight. But it happened.",
        ],
        "cycle_event": [
            "You're letting go easier.\n\nThe grip starts. Then catches. Loosens.\n\nYou're closing chapters you used to keep open.",
        ],
        "normal_flow": [
            "You're finishing things you used to leave open.\n\nSmall things. But consistently. The resistance arises — then doesn't complete.\n\nThe pattern is changing.",
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
# VALIDATION (v7 Edge Detection)
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

# EDGE/BREAK POINT markers - indicate where behavior breaks or fails
EDGE_MARKERS = [
    "then", "but", "doesn't land", "doesn't stick", "doesn't complete",
    "something catches", "you pause", "you pull back", "it doesn't",
    "you stop", "you catch yourself", "then you don't", "then stop",
    "that wasn't there", "that's not how", "that didn't",
]

def validate_narrative(body: str, altitude: str) -> Tuple[bool, str]:
    """
    Validate narrative against v7 edge detection standards.
    Returns (is_valid, reason).
    """
    body_lower = body.lower()
    
    # Check for banned phrases
    for phrase in FAIL_PHRASES:
        if phrase in body_lower:
            return False, f"Contains banned phrase: '{phrase}'"
    
    # Check for edge/break point markers (REQUIRED for all altitudes)
    has_edge = any(m in body_lower for m in EDGE_MARKERS)
    if not has_edge:
        return False, "Missing break point / edge marker (then, but, doesn't land, etc.)"
    
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
