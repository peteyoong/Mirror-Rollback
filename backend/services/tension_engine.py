"""
Tension Engine V3.3 - Real-World Clarity System

CORE PRINCIPLE:
Mirror is NOT a lens aggregator.
Mirror is a REAL-TIME SCENE ENGINE that speaks in plain language.

V3.3 EVOLUTION: EVENT → CAUSE → OBJECT → TENSION → MOVE
Every card must be instantly understandable to a non-astrology user.
User should immediately think: "yes, I know exactly what this is about"

V3.3 REQUIREMENTS:
1. REAL-WORLD EVENT HOOK (moment): Something actually happening, not internal state
2. CLEAR HUMAN CAUSE (cause_line): Why now, in human language (no astrology terms)
3. EXPLICIT OBJECT (about): Concrete, real-life thing (decision, conversation, work)
4. TIGHT CONTRADICTION: Simple and sharp, no fluff
5. DYNAMIC TENSION LABEL: Situation-based, not generic ("Say it vs perfect it" not "Push vs Hold")

V3.3 OUTPUT STRUCTURE:
{
  "moment": "... (real-world event)",
  "cause_line": "... (why now, human language)",
  "where": "... (life area)",
  "about": "... (clear object)",
  "contradiction": "...",
  "current_cost": "...",
  "supporting_line": "...",
  "why_now_plain": "... (visible, no astrology)",
  "pattern_reason": "... (behavioral tendency)",
  "why_now_technical": "... (hidden, astrology details)",
  "tension_label_dynamic": "... (situation-specific)",
  "avoided_move": "...",
  "micro_shift": "..."
}

LANGUAGE RULES (STRICT):
- No vague words unless tied to object ("this", "it", "something" cannot stand alone)
- Every sentence must be instantly understandable
- No "self-help" tone, no over-explanation
- Must feel like observation, not interpretation
- Transits DRIVE the system but are HIDDEN (only in technical layer)

SUCCESS: Non-astrology user should NOT ask "what does this mean?"
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from enum import Enum
import hashlib
import random

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIDENCE MODES
# =============================================================================

class ConfidenceMode(Enum):
    """Three modes based on evidence strength."""
    CONVERGED = "converged"      # 2+ strong lens signals align
    REPEATING = "repeating"      # Pattern memory strong, multi-lens weak
    LOW_SIGNAL = "low_signal"    # Evidence weak overall


class TriggerConfidence(Enum):
    """V3.2: Distinguishes between recurring pattern vs current activation."""
    RECURRING_ONLY = "recurring_only"               # Only pattern memory, no current trigger
    RECURRING_PLUS_TRIGGER = "recurring_plus_trigger"  # Pattern + some current signal
    STRONGLY_ACTIVE_NOW = "strongly_active_now"     # Strong current activation evidence


# =============================================================================
# SOURCE CLASSIFICATION: RECURRING vs NOW
# =============================================================================

# Sources that explain WHY THIS KEEPS HAPPENING (baseline/structural)
RECURRING_SOURCES = {"pattern_memory", "enneagram", "bazi", "human_design"}

# Sources that explain WHY IT'S ACTIVE NOW (current trigger)
NOW_SOURCES = {"astrology"}  # Transits, house activations, recent spikes


# =============================================================================
# TENSION SIGNAL DATA STRUCTURE
# =============================================================================

@dataclass
class TensionSignal:
    """Standardized signal from any lens."""
    tension: str           # e.g. "hesitating before acting"
    direction: str         # e.g. "push vs hold"
    intensity: float       # 0.0 - 1.0
    confidence: float      # 0.0 - 1.0
    domain: str            # action, decision, emotion, relationship, control
    source: str            # pattern_memory, astrology, human_design, bazi, enneagram
    raw_data: Dict = field(default_factory=dict)  # Original lens data for evidence
    evidence_text: str = ""  # Concrete evidence statement for this signal


# =============================================================================
# TENSION CLUSTERS - Map similar tensions to unified directions
# =============================================================================

TENSION_CLUSTERS = {
    "push_vs_hold": {
        "label": "Push vs Hold",
        "keywords": [
            "hesitating", "waiting", "holding back", "not moving", "stuck",
            "momentum blocked", "waiting for clarity", "afraid to act",
            "paralysis", "overthinking", "stalling", "delay", "caution"
        ],
        "domain": "action"
    },
    "control_vs_flow": {
        "label": "Control vs Flow",
        "keywords": [
            "controlling", "micromanaging", "gripping", "forcing", "rigid",
            "need certainty", "perfectionism", "can't let go", "overplanning",
            "resistance", "fighting", "not surrendering"
        ],
        "domain": "control"
    },
    "precision_vs_progress": {
        "label": "Precision vs Progress",
        "keywords": [
            "perfectionist", "refining", "polishing", "not shipping",
            "too careful", "over-editing", "never ready", "detail obsessed",
            "quality over speed", "afraid of mistakes"
        ],
        "domain": "action"
    },
    "visible_vs_hidden": {
        "label": "Visible vs Hidden",
        "keywords": [
            "hiding", "not showing up", "staying small", "avoiding exposure",
            "fear of being seen", "withdrawing", "protective", "private",
            "not sharing", "keeping back"
        ],
        "domain": "relationship"
    },
    "logic_vs_instinct": {
        "label": "Logic vs Instinct",
        "keywords": [
            "overthinking", "analyzing", "ignoring gut", "rationalizing",
            "head vs heart", "second-guessing", "not trusting", "doubt",
            "need proof", "dismissing feelings"
        ],
        "domain": "decision"
    },
    "self_vs_others": {
        "label": "Self vs Others",
        "keywords": [
            "people pleasing", "boundaries", "saying yes", "overgiving",
            "resentment building", "losing self", "accommodating",
            "neglecting needs", "conflict avoidance"
        ],
        "domain": "relationship"
    },
    "rest_vs_push": {
        "label": "Rest vs Push",
        "keywords": [
            "exhaustion", "burnout", "forcing energy", "not resting",
            "pushing through", "ignoring fatigue", "overdoing",
            "can't stop", "productivity addiction"
        ],
        "domain": "action"
    },
    "clarity_vs_chaos": {
        "label": "Clarity vs Chaos",
        "keywords": [
            "confused", "unclear", "overwhelmed", "too many options",
            "scattered", "no direction", "lost", "spinning",
            "can't decide", "fog"
        ],
        "domain": "decision"
    },
    "trust_vs_doubt": {
        "label": "Trust vs Doubt",
        "keywords": [
            "doubting", "questioning", "suspicious", "not believing",
            "second-guessing others", "paranoid", "skeptical",
            "waiting for proof", "defensive"
        ],
        "domain": "emotion"
    },
    "expression_vs_suppression": {
        "label": "Expression vs Suppression",
        "keywords": [
            "holding back words", "not speaking up", "swallowing feelings",
            "unexpressed", "bottled up", "silent", "contained",
            "afraid to say", "keeping peace"
        ],
        "domain": "emotion"
    }
}


# =============================================================================
# ENERGY TITLES - Short punchy labels
# =============================================================================

ENERGY_TITLES = {
    "push_vs_hold": [
        "Still Hesitating",
        "Not Moving Yet",
        "Waiting Again",
        "Holding the Line",
        "Something Wants to Move"
    ],
    "control_vs_flow": [
        "Gripping Too Tight",
        "Trying to Control",
        "Not Letting Go",
        "Forcing It",
        "Fighting the Current"
    ],
    "precision_vs_progress": [
        "Still Refining",
        "Not Ready Yet",
        "Almost Perfect",
        "One More Edit",
        "Never Quite Done"
    ],
    "visible_vs_hidden": [
        "Staying Small",
        "Hiding Again",
        "Not Showing Up",
        "Keeping Back",
        "Behind the Curtain"
    ],
    "logic_vs_instinct": [
        "Overthinking It",
        "In Your Head",
        "Ignoring the Gut",
        "Too Much Analysis",
        "Not Trusting"
    ],
    "self_vs_others": [
        "Giving Too Much",
        "Losing Yourself",
        "Saying Yes Again",
        "Boundary Blur",
        "Their Needs First"
    ],
    "rest_vs_push": [
        "Running Empty",
        "Pushing Through",
        "Not Stopping",
        "Forcing Energy",
        "Past the Limit"
    ],
    "clarity_vs_chaos": [
        "Still Unclear",
        "Spinning",
        "Too Many Options",
        "No Direction",
        "In the Fog"
    ],
    "trust_vs_doubt": [
        "Doubting Again",
        "Questioning Everything",
        "Waiting for Proof",
        "Not Believing",
        "On Guard"
    ],
    "expression_vs_suppression": [
        "Holding Back",
        "Words Stuck",
        "Not Saying It",
        "Swallowing It",
        "Keeping Quiet"
    ]
}


# =============================================================================
# MOMENT LANGUAGE TEMPLATES - Sharp, second-person, no soft language
# =============================================================================

MOMENT_TEMPLATES = {
    "push_vs_hold": [
        "You're hesitating again — and you know it.",
        "Part of you wants to move. Part of you is holding back.",
        "You're back here again.",
        "The opening is there. You're not taking it.",
        "You're waiting for certainty that isn't coming."
    ],
    "control_vs_flow": [
        "You're trying to control something that wants to move.",
        "You're gripping when you need to let go.",
        "The harder you hold, the more it slips.",
        "You're forcing something that needs space.",
        "Control isn't working right now."
    ],
    "precision_vs_progress": [
        "You're polishing something that needs to ship.",
        "Good enough shipped beats perfect never did.",
        "You're hiding behind quality.",
        "The refining is the stalling.",
        "Done is the goal. Perfect is the trap."
    ],
    "visible_vs_hidden": [
        "You're making yourself small again.",
        "Part of you wants to be seen. Part of you is hiding.",
        "You're protecting yourself from exposure.",
        "The world can't respond to what it can't see.",
        "You're holding back what wants to come forward."
    ],
    "logic_vs_instinct": [
        "You already know. You're just not trusting it.",
        "Your gut said something. Your head overruled it.",
        "You're analyzing when you need to act.",
        "The answer is there. You're looking past it.",
        "More data won't help. You have enough."
    ],
    "self_vs_others": [
        "You're giving more than you have.",
        "Their needs are louder than yours right now.",
        "You said yes when you meant no.",
        "The resentment is building.",
        "You're losing yourself in someone else's story."
    ],
    "rest_vs_push": [
        "You're running on fumes.",
        "Your body is asking for something your mind won't give.",
        "Pushing harder isn't the answer right now.",
        "You're past the point of productive.",
        "The tank is empty. You're still driving."
    ],
    "clarity_vs_chaos": [
        "You don't know what to do next.",
        "Too many options. No clear path.",
        "The fog is real. Don't pretend it isn't.",
        "You're spinning without landing.",
        "Clarity isn't coming from more thinking."
    ],
    "trust_vs_doubt": [
        "You're questioning something you used to believe.",
        "Doubt has moved in. It's not leaving easily.",
        "You're waiting for proof that won't arrive.",
        "The suspicion is running the show.",
        "Trust is hard right now."
    ],
    "expression_vs_suppression": [
        "There's something you're not saying.",
        "The words are there. You're holding them back.",
        "You're keeping the peace at your own expense.",
        "What's unsaid is building pressure.",
        "You're swallowing what needs to come out."
    ]
}


# =============================================================================
# SUPPORTING LINES - One sentence reinforcements
# =============================================================================

SUPPORTING_LINES = {
    "recurring": [
        "Same situation. Different day.",
        "You've seen this before.",
        "This isn't new.",
        "It's a pattern. Not a surprise.",
        "Here again."
    ],
    "intensity_high": [
        "It's louder than usual.",
        "This one has weight.",
        "Pay attention to this.",
        "Something is building.",
        "Don't ignore this."
    ],
    "intensity_low": [
        "Subtle, but present.",
        "Just under the surface.",
        "Barely visible. Still real.",
        "Quiet signal.",
        "Easy to miss. Worth noticing."
    ],
    "cross_lens": [
        "Multiple signals pointing here.",
        "Everything is pointing the same direction.",
        "Not just one source.",
        "Converging.",
        "Hard to argue with."
    ]
}


# =============================================================================
# MICRO-SHIFTS - One action sentence
# =============================================================================

MICRO_SHIFTS = {
    "push_vs_hold": [
        "Move before you feel ready.",
        "Take one step. Any step.",
        "Do the smallest version.",
        "Start before you're sure.",
        "Act first. Adjust after."
    ],
    "control_vs_flow": [
        "Let one thing go.",
        "Stop managing for an hour.",
        "See what happens if you don't intervene.",
        "Release the grip on one thing.",
        "Allow it to unfold."
    ],
    "precision_vs_progress": [
        "Ship it at 80%.",
        "Send it imperfect.",
        "Let it be seen before it's perfect.",
        "Done today beats perfect next week.",
        "Release the last revision."
    ],
    "visible_vs_hidden": [
        "Show one thing you've been hiding.",
        "Let yourself be seen once today.",
        "Share before you're ready.",
        "Step forward instead of back.",
        "Be visible in one small way."
    ],
    "logic_vs_instinct": [
        "Trust the first answer.",
        "Act on the gut feeling.",
        "Skip the analysis. Decide.",
        "Let instinct lead once.",
        "Follow the feeling, not the logic."
    ],
    "self_vs_others": [
        "Say no once today.",
        "Put your need first in one situation.",
        "Let them figure it out.",
        "Take something back for yourself.",
        "Stop over-functioning for someone."
    ],
    "rest_vs_push": [
        "Stop one hour early.",
        "Take the break you're avoiding.",
        "Let the day end incomplete.",
        "Rest without earning it.",
        "Do less today."
    ],
    "clarity_vs_chaos": [
        "Choose one thing. Ignore the rest.",
        "Sit with the not-knowing.",
        "Stop gathering options.",
        "Commit to one direction for 24 hours.",
        "Let the fog be there."
    ],
    "trust_vs_doubt": [
        "Act as if you trusted.",
        "Give benefit of doubt once.",
        "Suspend the questioning for a day.",
        "Let something be true.",
        "Choose trust over proof."
    ],
    "expression_vs_suppression": [
        "Say one thing you've been holding.",
        "Speak before you're ready.",
        "Let it out, even imperfectly.",
        "Break the silence on one thing.",
        "Voice it. Even quietly."
    ]
}


# =============================================================================
# V2: MODE-SPECIFIC MOMENT TEMPLATES
# =============================================================================

# MODE A: CONVERGED - Strong multi-lens alignment (bold, undeniable)
CONVERGED_MOMENTS = {
    "push_vs_hold": [
        "You already know. You still haven't moved.",
        "The hesitation isn't confusion anymore. It's avoidance.",
        "You're stalling in the name of clarity.",
        "Every lens is saying the same thing: move.",
        "This is the moment you keep rehearsing but not taking."
    ],
    "control_vs_flow": [
        "You're managing what needs to unfold.",
        "The grip is showing up everywhere.",
        "This isn't planning. It's resisting.",
        "Every system in you is trying to hold something still.",
        "You're trying to control the uncontrollable."
    ],
    "precision_vs_progress": [
        "You're perfecting instead of completing.",
        "The polish is the procrastination.",
        "This isn't quality control. It's hiding.",
        "You've crossed from careful into stuck.",
        "Done is the word you're avoiding."
    ],
    "visible_vs_hidden": [
        "You're ready to be seen. You're still hiding.",
        "The world is waiting. You're not showing up.",
        "Every part of you is pulling back.",
        "Invisibility isn't protecting you anymore.",
        "You're making yourself smaller than you are."
    ],
    "logic_vs_instinct": [
        "You know the answer. You're talking yourself out of it.",
        "The gut spoke. The head overruled.",
        "Analysis is your delay tactic.",
        "More thinking won't change what you already know.",
        "You're researching what you should be doing."
    ],
    "self_vs_others": [
        "You're disappearing into someone else's needs.",
        "The resentment is building. You're still saying yes.",
        "Their comfort is costing you.",
        "You've been overfunctioning again.",
        "You're giving what you need for yourself."
    ],
    "rest_vs_push": [
        "You're pushing past empty.",
        "Your body is asking. Your mind is refusing.",
        "This isn't discipline. It's depletion.",
        "Every signal says rest. You're ignoring them all.",
        "You're running on fumes and calling it commitment."
    ],
    "clarity_vs_chaos": [
        "You're looking for certainty that doesn't exist.",
        "The fog isn't lifting because you keep stirring it.",
        "Too many options is another word for avoidance.",
        "You're spinning because landing feels risky.",
        "Clarity won't come from more thinking."
    ],
    "trust_vs_doubt": [
        "You're questioning what you already decided.",
        "The doubt is running the show now.",
        "Proof isn't coming. You have to choose.",
        "This isn't skepticism. It's self-sabotage.",
        "You're waiting for permission that won't arrive."
    ],
    "expression_vs_suppression": [
        "The words are ready. You're choking them back.",
        "What you're not saying is building pressure.",
        "Silence isn't peace right now. It's avoidance.",
        "You're protecting something that doesn't need protecting.",
        "This truth wants out. You're holding the door closed."
    ]
}

# MODE B: REPEATING - Pattern memory strong, limited multi-lens (honest recurrence)
REPEATING_MOMENTS = {
    "push_vs_hold": [
        "This hesitation is repeating again.",
        "You've been here before. Same stall.",
        "The pattern is familiar: almost moving, then not.",
        "This is the same spot you keep returning to.",
        "Hesitation is your default. It's showing again."
    ],
    "control_vs_flow": [
        "This grip is familiar.",
        "You've tried to control this before.",
        "The pattern: tighten, then wonder why nothing moves.",
        "Control mode activated. Again.",
        "You keep returning to managing instead of allowing."
    ],
    "precision_vs_progress": [
        "The perfectionism is back.",
        "Same pattern: refine instead of release.",
        "You've done this editing loop before.",
        "Quality as delay. Again.",
        "This polishing pattern is repeating."
    ],
    "visible_vs_hidden": [
        "You're pulling back again. Same pattern.",
        "Hiding is familiar territory.",
        "This shrinking is something you've done before.",
        "The invisibility pattern is active.",
        "You keep returning to the shadows."
    ],
    "logic_vs_instinct": [
        "Overthinking. Again.",
        "You've analyzed your way out of action before.",
        "This is a familiar loop: think instead of do.",
        "The head-over-gut pattern is back.",
        "Same loop: research, doubt, stall."
    ],
    "self_vs_others": [
        "Over-giving is showing up again.",
        "This pattern: their needs first, yours ignored.",
        "You've been here before. Giving too much.",
        "The accommodation pattern is active.",
        "Same dynamic: them first, you later."
    ],
    "rest_vs_push": [
        "Pushing past tired. Again.",
        "This pattern: ignore the body, keep going.",
        "You've depleted yourself this way before.",
        "The override pattern is back.",
        "Same loop: exhaustion ignored."
    ],
    "clarity_vs_chaos": [
        "Scattered again. Same pattern.",
        "You've spun like this before.",
        "The too-many-directions pattern is active.",
        "This confusion loop is familiar.",
        "Same pattern: options without decisions."
    ],
    "trust_vs_doubt": [
        "Doubt is back. Same pattern.",
        "You've questioned like this before.",
        "The suspicion loop is active.",
        "This is familiar: trust, then pull back.",
        "Same pattern: wait for proof that won't come."
    ],
    "expression_vs_suppression": [
        "Holding back again. Same pattern.",
        "You've swallowed words like this before.",
        "The silence pattern is active.",
        "Same loop: things unsaid building up.",
        "This suppression is familiar."
    ]
}

# MODE C: LOW_SIGNAL - Weak evidence (modest, observational)
LOW_SIGNAL_MOMENTS = {
    "default": [
        "Something is building, but not fully clear yet.",
        "There's movement happening. Hard to name yet.",
        "A signal is forming. Not loud yet.",
        "Something is present. Watching it.",
        "Quiet activity. Worth noticing."
    ]
}

# V2: Mode-specific energy titles
CONVERGED_TITLES = [
    "Multiple Signals Aligning",
    "Clear Convergence",
    "Strong Signal",
    "Undeniable",
    "Everything Pointing Here"
]

REPEATING_TITLES = [
    "Familiar Pattern",
    "Here Again",
    "Recurring",
    "Same Territory", 
    "Pattern Repeating"
]

LOW_SIGNAL_TITLES = [
    "Watching",
    "Something Forming",
    "Quiet Signal",
    "Early Movement",
    "Not Clear Yet"
]

# V2: Mode-specific supporting lines
CONVERGED_SUPPORTING = [
    "Multiple lenses agree.",
    "Hard to argue with this one.",
    "Everything is pointing the same direction.",
    "Not just one signal.",
    "Convergence."
]

REPEATING_SUPPORTING = [
    "This pattern keeps returning.",
    "You've seen this before.",
    "Familiar territory.",
    "Same place, different day.",
    "The pattern is consistent."
]

LOW_SIGNAL_SUPPORTING = [
    "Signal is forming.",
    "Too early to be sure.",
    "Stay with it.",
    "Not enough evidence yet.",
    "Watching."
]


# =============================================================================
# V3: SCENE ENGINE - Concrete, lived-moment language
# =============================================================================

# V3 Scene Templates: Each cluster has concrete scenes with all 4 elements:
# - object_of_tension: what this is about (decision, conversation, etc.)
# - contradiction: the felt pull
# - current_cost: what this is costing now
# - avoided_move: the thing not being done

V3_SCENE_TEMPLATES = {
    "push_vs_hold": {
        "objects": [
            "the decision you keep circling",
            "the move you almost made",
            "the conversation you're avoiding",
            "the message sitting unsent",
            "the commitment you haven't named"
        ],
        "moments": [
            "You already know what needs naming.",
            "The opening is there. You're still circling.",
            "You've thought about this more than you've acted on it.",
            "Something is waiting to be done. You're not doing it.",
            "You're rehearsing instead of moving."
        ],
        "contradictions": [
            "You want to move, but you keep preparing.",
            "You want closure, but you keep postponing contact.",
            "You know what to do, but you're waiting for certainty.",
            "The impulse is there, but you're second-guessing it.",
            "Part of you is ready. Part of you is stalling."
        ],
        "costs": [
            "The pressure stays alive because nothing has been named.",
            "The delay is costing energy.",
            "You're spending more effort avoiding than it would take to act.",
            "The weight of this follows you into other things.",
            "You're carrying what you could resolve."
        ],
        "avoided_moves": [
            "making the actual move",
            "saying the thing out loud",
            "committing to one direction",
            "starting before you're sure",
            "naming what you already know"
        ]
    },
    "control_vs_flow": {
        "objects": [
            "a situation you're trying to manage",
            "something that needs to unfold on its own",
            "the outcome you're gripping",
            "the process you keep intervening in",
            "the thing that wants to move without you"
        ],
        "moments": [
            "You're managing what needs to unfold.",
            "The tighter you hold, the more friction you create.",
            "You're interfering with something that doesn't need you.",
            "Control is running the show right now.",
            "You're trying to force a shape onto something alive."
        ],
        "contradictions": [
            "You want it to work, but you won't let it breathe.",
            "You want progress, but you keep adjusting.",
            "You say you trust it, but you keep checking.",
            "You want ease, but you're overengineering.",
            "You want flow, but you keep directing."
        ],
        "costs": [
            "The thing you're managing is resisting your grip.",
            "Your energy is going into steering instead of receiving.",
            "You're exhausting yourself trying to hold the shape.",
            "Control is blocking the very outcome you want.",
            "You're working harder than necessary."
        ],
        "avoided_moves": [
            "letting go for one day",
            "not checking or adjusting",
            "allowing the outcome to arrive differently",
            "trusting the process without managing it",
            "stepping back"
        ]
    },
    "precision_vs_progress": {
        "objects": [
            "the thing that's almost ready but not shipped",
            "the work you keep refining",
            "the message you've edited five times",
            "the project that's 90% done",
            "the decision you keep polishing instead of making"
        ],
        "moments": [
            "You're perfecting what needs to ship.",
            "The last 10% is where you're hiding.",
            "Refinement has become delay.",
            "You've crossed from careful into stuck.",
            "Done is the word you're avoiding."
        ],
        "contradictions": [
            "You want it out there, but you keep improving it.",
            "You want to finish, but you're afraid of flaws.",
            "You say you're almost done, but you keep finding more.",
            "You want to be seen, but not before it's perfect.",
            "You're ready, but you keep editing."
        ],
        "costs": [
            "Nothing is landing while you keep polishing.",
            "Feedback you need can't arrive until you release.",
            "You're stuck in refinement instead of learning.",
            "The world can't respond to what it hasn't seen.",
            "You're protecting yourself with quality."
        ],
        "avoided_moves": [
            "sending it at 80%",
            "releasing before you're fully ready",
            "letting it be imperfect",
            "saying 'done' and moving on",
            "shipping today"
        ]
    },
    "visible_vs_hidden": {
        "objects": [
            "something you're not showing",
            "a part of you that wants to be seen",
            "the thing you're holding back",
            "the work you haven't shared",
            "the truth you're protecting"
        ],
        "moments": [
            "You're making yourself smaller than you are.",
            "Something wants to be seen. You're hiding it.",
            "You're curating what's visible.",
            "There's more of you than you're showing.",
            "You're playing safe with your presence."
        ],
        "contradictions": [
            "You want recognition, but you're staying invisible.",
            "You want connection, but you're holding back.",
            "You want to be known, but you're filtering.",
            "You crave visibility, but you fear exposure.",
            "Part of you wants out. Part of you is shrinking."
        ],
        "costs": [
            "The world can't respond to what it can't see.",
            "Connection requires showing up as you are.",
            "You're paying the price of invisibility.",
            "Protection is becoming isolation.",
            "Opportunity can't find what's hidden."
        ],
        "avoided_moves": [
            "showing the unpolished version",
            "letting yourself be seen as you are",
            "sharing before you're ready",
            "taking up more space",
            "stepping into the light"
        ]
    },
    "logic_vs_instinct": {
        "objects": [
            "a decision your gut already made",
            "the answer you keep researching",
            "what your body knows",
            "the thing you're analyzing past the point of usefulness",
            "the choice you're overthinking"
        ],
        "moments": [
            "You already know. You're just not trusting it.",
            "Your gut said something. Your head overruled.",
            "More thinking won't change what you already feel.",
            "The answer is there. You're looking past it.",
            "You're researching what you should be doing."
        ],
        "contradictions": [
            "You want certainty, but you're ignoring what's already clear.",
            "You say you don't know, but your body does.",
            "You're asking for data when you need courage.",
            "You want proof for something that doesn't work that way.",
            "The answer is available. You're not accepting it."
        ],
        "costs": [
            "Time is passing while you keep analyzing.",
            "The moment to act is slipping.",
            "Your gut is losing trust in you.",
            "You're expending mental energy instead of moving.",
            "Analysis is becoming avoidance."
        ],
        "avoided_moves": [
            "acting on the first answer",
            "trusting what your body told you",
            "deciding without more research",
            "following the instinct",
            "letting the gut lead"
        ]
    },
    "self_vs_others": {
        "objects": [
            "someone else's need that's taking priority",
            "the yes you said when you meant no",
            "the boundary you didn't hold",
            "the thing you're doing for them instead of you",
            "the resentment that's building"
        ],
        "moments": [
            "You're giving more than you have.",
            "Someone else's need is running your schedule.",
            "You said yes when you meant something else.",
            "Your own priorities are at the bottom of the list.",
            "You're disappearing into someone else's story."
        ],
        "contradictions": [
            "You want to help, but you're losing yourself.",
            "You care about them, but you're neglecting you.",
            "You want harmony, but resentment is building.",
            "You want to give, but you're running empty.",
            "You say it's fine. It isn't."
        ],
        "costs": [
            "Your own needs keep getting pushed back.",
            "Resentment is building under the surface.",
            "You're exhausting yourself for someone else's comfort.",
            "What you need isn't getting any attention.",
            "Your presence is becoming performance."
        ],
        "avoided_moves": [
            "saying no to the next request",
            "putting yourself first once",
            "letting them figure it out",
            "taking something back for yourself",
            "naming what you actually need"
        ]
    },
    "rest_vs_push": {
        "objects": [
            "the fatigue you're ignoring",
            "the break you keep postponing",
            "the rest your body is asking for",
            "the energy you're forcing",
            "the tiredness you're pushing past"
        ],
        "moments": [
            "You're running on fumes.",
            "Your body is asking for something your mind won't give.",
            "You're forcing energy that isn't there.",
            "The tank is empty. You're still driving.",
            "Rest is available. You're refusing it."
        ],
        "contradictions": [
            "You want to perform, but your system is depleted.",
            "You want to keep going, but your body is done.",
            "You call it discipline. Your body calls it depletion.",
            "You want results, but you're working from empty.",
            "You're pushing through something that's asking you to stop."
        ],
        "costs": [
            "Everything you do is costing more than it should.",
            "Quality is dropping because you're depleted.",
            "Your capacity is shrinking the harder you push.",
            "You're accumulating a debt you'll pay later.",
            "Your system is learning to distrust you."
        ],
        "avoided_moves": [
            "stopping before you're forced to",
            "resting without earning it",
            "ending the day incomplete",
            "taking the break now",
            "honoring what your body said"
        ]
    },
    "clarity_vs_chaos": {
        "objects": [
            "the decision you keep circling without landing",
            "the confusion that won't resolve",
            "the too-many-options situation",
            "the direction you can't find",
            "the fog that won't lift"
        ],
        "moments": [
            "You don't know what to do next. And that's real.",
            "Too many options is another kind of stuck.",
            "You're spinning without landing.",
            "The fog isn't lifting. Pretending it is won't help.",
            "Clarity isn't coming from more thinking."
        ],
        "contradictions": [
            "You want a direction, but you keep adding options.",
            "You want certainty, but nothing feels certain.",
            "You're seeking clarity through more input.",
            "You want to land, but you keep orbiting.",
            "You say you need more info. You actually need a choice."
        ],
        "costs": [
            "Energy is going into spinning, not moving.",
            "The longer you wait, the harder choosing feels.",
            "Options are multiplying while clarity shrinks.",
            "Indecision is draining you more than any wrong choice would.",
            "You're getting nowhere fast."
        ],
        "avoided_moves": [
            "picking one direction for now",
            "eliminating options instead of adding them",
            "committing for 24 hours",
            "acting without full clarity",
            "accepting the not-knowing and moving anyway"
        ]
    },
    "trust_vs_doubt": {
        "objects": [
            "something you decided but keep questioning",
            "someone you believe but keep checking",
            "a choice that's already made",
            "the commitment you're second-guessing",
            "the trust you keep withdrawing"
        ],
        "moments": [
            "You're questioning what you already decided.",
            "Doubt is running the show now.",
            "You keep reopening what was settled.",
            "The checking is becoming the problem.",
            "You're waiting for certainty that won't arrive."
        ],
        "contradictions": [
            "You committed, but you keep reviewing.",
            "You want to trust, but you keep testing.",
            "You made a choice, but you're still shopping.",
            "You said yes, but you're still unsure.",
            "You want to believe. You can't stop doubting."
        ],
        "costs": [
            "The thing you chose can't land while you keep questioning it.",
            "Trust can't build while you keep testing.",
            "You're paying attention to doubt instead of building forward.",
            "The relationship to this decision is fraying.",
            "You're eroding your own commitment."
        ],
        "avoided_moves": [
            "acting as if you trust",
            "stopping the checking",
            "letting the decision rest",
            "giving it a real chance before reviewing",
            "choosing trust over proof"
        ]
    },
    "expression_vs_suppression": {
        "objects": [
            "something you haven't said",
            "the words you're holding back",
            "the conversation you've been avoiding",
            "what wants to come out",
            "the truth stuck in your throat"
        ],
        "moments": [
            "There's something you're not saying.",
            "The words are ready. You're holding them back.",
            "You're keeping the peace at your own expense.",
            "What's unsaid is building pressure.",
            "You're swallowing what needs to come out."
        ],
        "contradictions": [
            "You want to be heard, but you're staying silent.",
            "You want resolution, but you won't speak plainly.",
            "You want closeness, but you're withholding.",
            "You say it's fine. It isn't fine.",
            "You want truth, but you're managing their comfort."
        ],
        "costs": [
            "The pressure stays alive because nothing has been named.",
            "Distance is growing from what remains unspoken.",
            "You're holding tension that belongs in words.",
            "The relationship can't move past what isn't said.",
            "Your silence is costing you."
        ],
        "avoided_moves": [
            "saying the thing out loud",
            "naming what still doesn't sit right",
            "speaking before you have it perfect",
            "letting them know what you're actually thinking",
            "saying the unsaid part first"
        ]
    }
}

# V3: Energy titles that feel scene-aware, not category-based
V3_ENERGY_TITLES = {
    "push_vs_hold": [
        "Still circling it",
        "Almost moved",
        "Not yet",
        "The opening is there",
        "Still rehearsing"
    ],
    "control_vs_flow": [
        "Gripping",
        "Managing again",
        "Not letting go",
        "Forcing the shape",
        "Won't stop steering"
    ],
    "precision_vs_progress": [
        "Still refining",
        "Almost done, again",
        "Hiding in quality",
        "One more pass",
        "Not shipping"
    ],
    "visible_vs_hidden": [
        "Playing small",
        "Not showing up",
        "Staying back",
        "Holding it in",
        "Invisible mode"
    ],
    "logic_vs_instinct": [
        "In your head",
        "Ignoring the gut",
        "Analyzing again",
        "Not trusting it",
        "Researching what you know"
    ],
    "self_vs_others": [
        "Their needs first",
        "Said yes again",
        "Running empty for them",
        "Boundary blur",
        "Losing yourself"
    ],
    "rest_vs_push": [
        "Past empty",
        "Forcing it",
        "Ignoring the body",
        "Won't stop",
        "Depleted"
    ],
    "clarity_vs_chaos": [
        "Spinning",
        "Too many options",
        "Can't land",
        "In the fog",
        "No direction"
    ],
    "trust_vs_doubt": [
        "Questioning again",
        "Can't stop checking",
        "Reopening it",
        "Doubt running",
        "Waiting for proof"
    ],
    "expression_vs_suppression": [
        "Holding it back",
        "Words stuck",
        "Not saying it",
        "Swallowing it",
        "Silence building"
    ]
}


# =============================================================================
# V3.3: REAL-WORLD EVENT TEMPLATES (NOT INTERNAL STATES)
# User should immediately think: "yes, I know exactly what this is about"
# =============================================================================

V33_REAL_WORLD_MOMENTS = {
    "push_vs_hold": [
        "You're sitting on a decision you already understand.",
        "You're holding back a conversation that would move things forward.",
        "There's a message you keep editing instead of sending.",
        "You're circling a commitment instead of making it.",
        "You're waiting for the right moment that keeps not arriving."
    ],
    "control_vs_flow": [
        "You're managing something that would work better without your grip.",
        "You keep checking on something that needs space.",
        "You're steering a situation that wants to unfold on its own.",
        "You're over-preparing for something that requires trust.",
        "You're adjusting something that's already good enough."
    ],
    "precision_vs_progress": [
        "You're refining something that should already be out.",
        "You're polishing work that's ready to be seen.",
        "You're editing instead of shipping.",
        "You're holding back finished work for one more pass.",
        "You're waiting until it's perfect, which means waiting."
    ],
    "visible_vs_hidden": [
        "You're holding back something that wants to be shared.",
        "You're staying quiet when there's something to say.",
        "You're keeping your work to yourself when it's ready for others.",
        "You're making yourself smaller than the space you could fill.",
        "You're watching from the side when you could be in the room."
    ],
    "logic_vs_instinct": [
        "You're researching a decision your gut already made.",
        "You're looking for more information when you have enough.",
        "You're thinking through something that needs feeling.",
        "You're asking for opinions when you already know.",
        "You're building a case for what you already believe."
    ],
    "self_vs_others": [
        "You're adjusting your schedule around someone else's needs.",
        "You're saying yes to something you want to decline.",
        "You're prioritizing their comfort over your boundary.",
        "You're taking care of their needs while ignoring your own.",
        "You're keeping peace at the cost of your truth."
    ],
    "rest_vs_push": [
        "You're pushing through exhaustion instead of resting.",
        "You're adding more to a plate that's already full.",
        "You're treating tiredness as weakness instead of information.",
        "You're overriding your body's signals to keep going.",
        "You're saying yes when your system is saying no."
    ],
    "clarity_vs_chaos": [
        "You're trying to think your way to clarity that won't come from thinking.",
        "You're searching for certainty in a situation that requires trust.",
        "You're gathering more data when action would reveal more.",
        "You're looking for the answer in the wrong place.",
        "You're waiting for clarity that comes from doing, not thinking."
    ],
    "trust_vs_doubt": [
        "You're double-checking something that's already been verified.",
        "You're looking for reassurance when you've already decided.",
        "You're asking 'are you sure?' when the answer is yes.",
        "You're reviewing something that doesn't need another pass.",
        "You're seeking certainty that won't come until you act."
    ],
    "expression_vs_suppression": [
        "You're swallowing words that want to come out.",
        "You're editing your truth before speaking it.",
        "You're sitting on something that needs to be said.",
        "You're holding back an honest response.",
        "You're keeping quiet when silence is costing you."
    ]
}

# V3.3: DYNAMIC TENSION LABELS (situation-specific, not generic)
V33_DYNAMIC_TENSION_LABELS = {
    "push_vs_hold": ["Act vs Wait", "Move vs Prepare", "Do it vs Think about it", "Decide vs Delay"],
    "control_vs_flow": ["Grip vs Trust", "Manage vs Allow", "Steer vs Release", "Control vs Let go"],
    "precision_vs_progress": ["Polish vs Ship", "Perfect vs Done", "Refine vs Release", "Edit vs Send"],
    "visible_vs_hidden": ["Show up vs Hold back", "Speak vs Stay quiet", "Be seen vs Stay safe", "Share vs Protect"],
    "logic_vs_instinct": ["Think vs Feel", "Research vs Decide", "Analyze vs Trust", "Know vs Do"],
    "self_vs_others": ["Your needs vs Their needs", "Your truth vs Their comfort", "Boundary vs Peace", "Yes vs No"],
    "rest_vs_push": ["Rest vs Push", "Stop vs Continue", "Pause vs Power through", "Enough vs More"],
    "clarity_vs_chaos": ["Act vs Wait for clarity", "Trust vs Know for sure", "Move vs Understand first"],
    "trust_vs_doubt": ["Trust vs Verify", "Proceed vs Check again", "Believe vs Doubt", "Act vs Reassure"],
    "expression_vs_suppression": ["Say it vs Swallow it", "Speak vs Edit", "Truth vs Peace", "Express vs Suppress"]
}

# V3.3: CAUSE LINES (why now, in human language - NO astrology terms)
V33_CAUSE_LINES = {
    "push_vs_hold": [
        "There's pressure right now to act before everything feels ready.",
        "Something is asking you to move, and you're not moving yet.",
        "The window is open. You're aware of it. You haven't stepped through.",
        "You're being pushed toward action, but choosing preparation instead.",
        "The moment is here. You're still getting ready for it."
    ],
    "control_vs_flow": [
        "Something needs to happen without your management right now.",
        "You're being asked to trust what you can't control.",
        "The situation is asking for release, not more grip.",
        "There's an invitation to step back and let things move.",
        "What you're holding wants to be let go."
    ],
    "precision_vs_progress": [
        "Something is pushing for expression, not refinement.",
        "You're being called to ship, not polish.",
        "The work wants to be seen. You're still editing.",
        "There's pressure to release what's ready.",
        "Done is being asked for. Perfect is being offered."
    ],
    "visible_vs_hidden": [
        "There's an opening to be seen that you're not taking.",
        "Something in you wants to show up. Another part is holding back.",
        "Visibility is available. You're choosing invisibility.",
        "You could take up more space right now. You're not.",
        "There's room for you to speak. You're staying quiet."
    ],
    "logic_vs_instinct": [
        "Your gut has an answer. Your mind is still researching.",
        "You already know. You're looking for permission.",
        "The feeling is clear. The thinking hasn't caught up.",
        "Your instinct spoke first. Your logic is trying to verify.",
        "The answer exists. You're building a case around it."
    ],
    "self_vs_others": [
        "Your needs are being overridden by someone else's.",
        "There's a boundary that wants to exist. You haven't named it.",
        "You're putting their comfort ahead of your truth.",
        "Something in you wants to say no. You're saying yes instead.",
        "You're adapting when you could be asserting."
    ],
    "rest_vs_push": [
        "Your system is asking for pause. You're not listening.",
        "There's a signal to stop. You're pushing through it.",
        "Rest is being requested. You're overriding the request.",
        "Your body knows what it needs. Your mind is arguing.",
        "The push is costing more than it's producing."
    ],
    "clarity_vs_chaos": [
        "Clarity won't come from more thinking right now.",
        "Action would reveal more than analysis.",
        "You're seeking certainty that only movement can provide.",
        "The fog won't lift from waiting. It lifts from walking.",
        "What you need to know will come from doing."
    ],
    "trust_vs_doubt": [
        "The reassurance you're seeking won't come from checking again.",
        "You've already verified. You're still doubting.",
        "Trust is being asked for. Doubt is being offered.",
        "Certainty won't come from more information.",
        "You're looking for proof that only action can provide."
    ],
    "expression_vs_suppression": [
        "Something in you needs to be said right now.",
        "The words are ready. You're holding them back.",
        "There's a truth pressing forward. You're editing it.",
        "Silence is costing more than speaking would.",
        "What's unsaid is louder than what's spoken."
    ]
}

# V3.3: TIGHT CONTRADICTIONS (simple and sharp, no fluff)
V33_TIGHT_CONTRADICTIONS = {
    "push_vs_hold": [
        "You know what to do. You're waiting anyway.",
        "The answer is clear. The action isn't happening.",
        "Ready to move. Still standing still.",
        "Part of you is ready. Part of you wants certainty first.",
        "You understand. You're not acting on it."
    ],
    "control_vs_flow": [
        "Wanting it to work. Not letting it work.",
        "Trust is available. You're choosing grip instead.",
        "Release would help. You're holding tighter.",
        "You want ease. You're creating friction.",
        "The way forward is letting go. You're holding on."
    ],
    "precision_vs_progress": [
        "It's ready. You're still refining.",
        "Good enough exists. You're not accepting it.",
        "Done is available. Perfect is being chased.",
        "Ship it or keep editing. You're choosing editing.",
        "The work is finished. You're still working on it."
    ],
    "visible_vs_hidden": [
        "Want to be seen. Choosing to hide.",
        "Something to say. Staying quiet.",
        "Room to take up. Making yourself smaller.",
        "Ready to show up. Holding back.",
        "Space is available. You're not filling it."
    ],
    "logic_vs_instinct": [
        "You feel it. You're still thinking about it.",
        "The gut says yes. The mind says 'but...'",
        "You know. You're looking for proof.",
        "The answer is felt. You're building a case.",
        "Instinct is clear. Logic is arguing."
    ],
    "self_vs_others": [
        "Your need exists. You're prioritizing theirs.",
        "Truth is available. You're protecting their comfort.",
        "Boundary is ready. Peace is being kept instead.",
        "You want to say no. You're saying yes.",
        "Your truth is here. Their feelings come first."
    ],
    "rest_vs_push": [
        "Body says stop. You're still going.",
        "Rest is needed. Push is happening.",
        "The signal is clear. You're ignoring it.",
        "Enough is here. More is being demanded.",
        "Pause is asked for. You're powering through."
    ],
    "clarity_vs_chaos": [
        "Action would help. Thinking is happening.",
        "Movement creates clarity. You're staying still.",
        "Doing would reveal. Waiting is chosen.",
        "The answer comes from moving. You're analyzing.",
        "Clarity lives in action. You're seeking it in thought."
    ],
    "trust_vs_doubt": [
        "Done checking. Still doubting.",
        "Verified. Not believed.",
        "Evidence exists. Trust doesn't.",
        "You've confirmed. You're still unsure.",
        "Proof is there. You're looking for more."
    ],
    "expression_vs_suppression": [
        "Words are ready. Silence is chosen.",
        "Truth is available. It's being edited.",
        "Something to say. Nothing being said.",
        "The real thing is held back.",
        "Speak or swallow. You're swallowing."
    ]
}

# V3.3: PATTERN REASONS (behavioral tendency, plain language)
V33_PATTERN_REASONS = {
    "push_vs_hold": "You tend to wait until it feels right. It rarely does.",
    "control_vs_flow": "You default to managing when you feel uncertain.",
    "precision_vs_progress": "You'd rather perfect than be seen imperfect.",
    "visible_vs_hidden": "Safety feels like staying small. It's not.",
    "logic_vs_instinct": "You trust thinking more than feeling. That's the pattern.",
    "self_vs_others": "You accommodate before asserting. That's the habit.",
    "rest_vs_push": "You override your body. It keeps track.",
    "clarity_vs_chaos": "You seek understanding before acting. Sometimes action is understanding.",
    "trust_vs_doubt": "Doubt feels like protection. It's mostly delay.",
    "expression_vs_suppression": "You edit before you speak. Sometimes the edit is silence."
}

# V3.3: EXPLICIT OBJECTS (mandatory, concrete)
V33_EXPLICIT_OBJECTS = {
    "push_vs_hold": [
        "the decision you've been circling",
        "the conversation you haven't had",
        "the message you keep not sending",
        "the commitment you haven't named out loud",
        "the move you keep almost making"
    ],
    "control_vs_flow": [
        "the situation you keep checking on",
        "the outcome you're trying to manage",
        "the thing you won't let unfold without you",
        "the process you keep interrupting",
        "the result you're gripping too tightly"
    ],
    "precision_vs_progress": [
        "the work you're not ready to show",
        "the thing that's done but you keep refining",
        "the project that's ready but not released",
        "the draft that keeps getting edited",
        "the creation that's waiting to be seen"
    ],
    "visible_vs_hidden": [
        "the thing you haven't shared yet",
        "the truth you're keeping to yourself",
        "the voice you're not using",
        "the opinion you're not offering",
        "the space you're not taking"
    ],
    "logic_vs_instinct": [
        "the choice you already know the answer to",
        "the decision your gut already made",
        "the thing you're researching instead of doing",
        "the answer you keep looking for permission on",
        "the knowing you're not acting on"
    ],
    "self_vs_others": [
        "the boundary you haven't named",
        "the no you're not saying",
        "the yes that should be a no",
        "the need you're not expressing",
        "the truth you're softening for them"
    ],
    "rest_vs_push": [
        "the pause you're not taking",
        "the rest you're postponing",
        "the break you keep skipping",
        "the recovery you're delaying",
        "the stop you're not allowing"
    ],
    "clarity_vs_chaos": [
        "the action that would create clarity",
        "the step you're overthinking",
        "the move that would reveal the path",
        "the experiment you're not running",
        "the doing you're replacing with thinking"
    ],
    "trust_vs_doubt": [
        "the thing you've already verified",
        "the decision you keep second-guessing",
        "the choice you've made but not committed to",
        "the plan you keep questioning",
        "the answer you have but don't trust"
    ],
    "expression_vs_suppression": [
        "the thing you haven't said yet",
        "the truth you're sitting on",
        "the words you keep editing",
        "the response you're holding back",
        "the conversation you're avoiding"
    ]
}


# =============================================================================
# HOUSE → PLAIN ENGLISH LIFE AREA MAPPING
# =============================================================================

HOUSE_TO_LIFE_AREA = {
    1: "self and identity",
    2: "money and value",
    3: "communication and decisions",
    4: "home and family",
    5: "expression and creativity",
    6: "work rhythm and daily systems",
    7: "relationship and commitment",
    8: "intimacy and shared stakes",
    9: "meaning and direction",
    10: "work and visibility",
    11: "community and future vision",
    12: "inner world and avoidance",
}

# BaZi domain → life area mapping
BAZI_DOMAIN_TO_LIFE_AREA = {
    "wealth": ("money and value", 2),
    "career": ("work and visibility", 10),
    "relationship": ("relationship and commitment", 7),
    "health": ("work rhythm and daily systems", 6),
    "creativity": ("expression and creativity", 5),
    "authority": ("work and visibility", 10),
    "resource": ("money and value", 2),
    "output": ("expression and creativity", 5),
    "power": ("intimacy and shared stakes", 8),
    "companion": ("relationship and commitment", 7),
}

# Tension cluster → default life area mapping (fallback)
CLUSTER_TO_LIFE_AREA = {
    "push_vs_hold": ("decisions and action", 3),
    "control_vs_flow": ("self and identity", 1),
    "precision_vs_progress": ("work and visibility", 10),
    "visible_vs_hidden": ("expression and creativity", 5),
    "logic_vs_instinct": ("communication and decisions", 3),
    "self_vs_others": ("relationship and commitment", 7),
    "rest_vs_push": ("work rhythm and daily systems", 6),
    "clarity_vs_chaos": ("meaning and direction", 9),
    "trust_vs_doubt": ("intimacy and shared stakes", 8),
    "expression_vs_suppression": ("communication and decisions", 3),
}

# Cluster-specific confidence boost (some clusters strongly imply life area)
CLUSTER_LIFE_AREA_CONFIDENCE = {
    "self_vs_others": 0.55,  # Clearly about relationships
    "rest_vs_push": 0.55,   # Clearly about work/daily rhythm
    "precision_vs_progress": 0.52,  # Often about work
    "visible_vs_hidden": 0.52,  # Often about expression/creativity
}


# =============================================================================
# V3.2: HOUSE-CONTEXTUALIZED COPY TEMPLATES
# When life_area confidence > 0.6, use these to shape moment/contradiction/cost
# =============================================================================

HOUSE_CONTEXTUALIZED_MOMENTS = {
    # House 1: Self and identity
    1: {
        "push_vs_hold": "You're still deciding who to be instead of being it.",
        "control_vs_flow": "You're managing your image instead of expressing yourself.",
        "visible_vs_hidden": "You're hiding who you are instead of showing it.",
        "precision_vs_progress": "You're refining how you present instead of actually showing up.",
    },
    # House 2: Money and value
    2: {
        "push_vs_hold": "You're circling the financial move instead of making it.",
        "control_vs_flow": "You're gripping the money situation instead of letting it move.",
        "trust_vs_doubt": "You're checking the numbers again instead of trusting your value.",
    },
    # House 3: Communication and decisions
    3: {
        "push_vs_hold": "The message is written. You're still not sending it.",
        "expression_vs_suppression": "The words are ready. You're holding them back.",
        "logic_vs_instinct": "You're overthinking what needs saying instead of saying it.",
    },
    # House 4: Home and family
    4: {
        "push_vs_hold": "You're avoiding the family conversation that needs to happen.",
        "self_vs_others": "You're prioritizing their comfort over your boundary.",
        "expression_vs_suppression": "There's something you've never said to them.",
    },
    # House 5: Expression and creativity
    5: {
        "push_vs_hold": "The creative thing is ready. You're still not releasing it.",
        "visible_vs_hidden": "You want to be seen, but you're still hiding the work.",
        "precision_vs_progress": "You're refining the work instead of sharing it.",
    },
    # House 6: Work rhythm and daily systems
    6: {
        "push_vs_hold": "You know what needs changing in your routine. You're not doing it.",
        "rest_vs_push": "Your body is asking for rest. You're pushing through.",
        "control_vs_flow": "You're micromanaging your schedule instead of flowing with it.",
    },
    # House 7: Relationship and commitment
    7: {
        "push_vs_hold": "You're avoiding the conversation that would change everything.",
        "self_vs_others": "You're giving more than you're receiving in this.",
        "expression_vs_suppression": "There's something you haven't named to them yet.",
        "trust_vs_doubt": "You're waiting for certainty before committing.",
    },
    # House 8: Intimacy and shared stakes
    8: {
        "push_vs_hold": "The vulnerability is asking to come forward. You're holding it.",
        "trust_vs_doubt": "You want to trust. You're still protecting yourself.",
        "control_vs_flow": "You're controlling what you let them see.",
    },
    # House 9: Meaning and direction
    9: {
        "push_vs_hold": "You know where you want to go. You're not starting the journey.",
        "clarity_vs_chaos": "You're looking for more meaning instead of making meaning.",
        "logic_vs_instinct": "You're researching the path instead of walking it.",
    },
    # House 10: Work and visibility
    10: {
        "push_vs_hold": "You're rehearsing the career move instead of making it.",
        "visible_vs_hidden": "You're staying small when it's time to be seen professionally.",
        "precision_vs_progress": "You're polishing instead of publishing.",
        "control_vs_flow": "You're managing your reputation instead of just doing the work.",
    },
    # House 11: Community and future vision
    11: {
        "push_vs_hold": "You're thinking about the community move instead of joining.",
        "visible_vs_hidden": "You want to belong, but you're not putting yourself out there.",
        "self_vs_others": "You're fitting in instead of showing what makes you different.",
    },
    # House 12: Inner world and avoidance
    12: {
        "push_vs_hold": "There's something you're avoiding looking at.",
        "clarity_vs_chaos": "You're staying busy to avoid what's underneath.",
        "expression_vs_suppression": "There's something you've never admitted to yourself.",
    },
}

HOUSE_CONTEXTUALIZED_CONTRADICTIONS = {
    1: "You want to be yourself, but you keep performing a version.",
    2: "You want financial freedom, but you're not making the move that would create it.",
    3: "You know what to say, but you keep editing instead of speaking.",
    4: "You want peace at home, but you're avoiding the conversation that would create it.",
    5: "You want to create, but you're waiting until it's safe to be seen.",
    6: "You want sustainable rhythm, but you keep overriding your own signals.",
    7: "You want connection, but you're holding something back from them.",
    8: "You want to be known, but you're controlling what they can see.",
    9: "You want direction, but you keep researching instead of moving.",
    10: "You want recognition, but you're not letting the work be visible.",
    11: "You want to belong, but you're not showing up as yourself.",
    12: "You want clarity, but you're avoiding the thing that would bring it.",
}

HOUSE_CONTEXTUALIZED_COSTS = {
    1: "The longer you perform, the further you drift from yourself.",
    2: "The opportunity has a window. It's shrinking.",
    3: "The message unsent is costing more than the conversation would.",
    4: "The peace you're protecting isn't peace. It's avoidance.",
    5: "The creative energy you're holding is starting to turn inward.",
    6: "Your body is keeping score. The exhaustion is building.",
    7: "The distance in the relationship is growing while you wait.",
    8: "The walls you've built are keeping out what you actually want.",
    9: "The direction you're seeking won't come from more thinking.",
    10: "Your reputation is being shaped by what you're not doing.",
    11: "The belonging you want requires showing up first.",
    12: "What you're avoiding is still running the show from underneath.",
}


@dataclass
class LifeAreaContext:
    """Life area context for grounding the tension."""
    label: str
    source: str  # astrology_house, bazi_domain, pattern_memory, cluster_default
    house: Optional[int] = None
    confidence: float = 0.5


async def derive_life_area_context(
    db,
    user_id: str,
    signals: List['TensionSignal'],
    dominant_cluster: str
) -> Optional[LifeAreaContext]:
    """
    Derive the life area context from multiple sources.
    
    Priority order:
    1. Astrology house activation (transits → natal houses)
    2. BaZi domain mapping (if clear)
    3. Pattern Memory context
    4. Cluster default (lowest priority)
    
    Returns None if confidence < 0.5
    """
    life_area_candidates = []
    
    # 1. Try to get astrology house from transit data
    try:
        astro_context = await _get_astrology_life_area(db, user_id)
        if astro_context:
            life_area_candidates.append(astro_context)
    except Exception as e:
        logger.debug(f"[LifeArea] Astrology extraction failed: {e}")
    
    # 2. Check BaZi domain from signals
    for signal in signals:
        if signal.source == "bazi" and signal.raw_data:
            bazi_context = _get_bazi_life_area(signal)
            if bazi_context:
                life_area_candidates.append(bazi_context)
                break
    
    # 3. Check Pattern Memory for domain hints
    for signal in signals:
        if signal.source == "pattern_memory" and signal.raw_data:
            pm_context = _get_pattern_memory_life_area(signal)
            if pm_context:
                life_area_candidates.append(pm_context)
                break
    
    # 4. Cluster default (lowest priority, use boosted confidence for some clusters)
    if dominant_cluster in CLUSTER_TO_LIFE_AREA:
        label, house = CLUSTER_TO_LIFE_AREA[dominant_cluster]
        base_confidence = CLUSTER_LIFE_AREA_CONFIDENCE.get(dominant_cluster, 0.4)
        life_area_candidates.append(LifeAreaContext(
            label=label,
            source="cluster_default",
            house=house,
            confidence=base_confidence
        ))
    
    # Select highest confidence candidate
    if not life_area_candidates:
        return None
    
    best_candidate = max(life_area_candidates, key=lambda x: x.confidence)
    
    # Don't return if confidence is too low
    if best_candidate.confidence < 0.5:
        logger.info(f"[LifeArea] No high-confidence life area (best: {best_candidate.confidence})")
        return None
    
    logger.info(f"[LifeArea] Selected: {best_candidate.label} (source={best_candidate.source}, conf={best_candidate.confidence})")
    return best_candidate


async def _get_astrology_life_area(db, user_id: str) -> Optional[LifeAreaContext]:
    """Get life area from astrology transits hitting natal houses."""
    try:
        from services.daily_transit_window import scan_daily_transit_window, get_current_transit_houses
        
        # Get user's chart
        chart = await db.astrology_charts.find_one({"user_id": user_id})
        if not chart:
            return None
        
        house_cusps = chart.get("house_cusps", [])
        if not house_cusps or len(house_cusps) < 12:
            return None
        
        # Get current transit positions
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # Scan for active transit events
        transit_data = scan_daily_transit_window(
            now,
            chart.get("planet_positions", {}),
            house_cusps
        )
        
        if not transit_data:
            return None
        
        # Look for the most activated house
        activated_houses = {}
        
        # Check transit house positions (where transiting planets currently are)
        transit_houses = transit_data.get("transit_houses", {})
        for planet, house in transit_houses.items():
            if planet in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:  # Personal planets
                weight = 1.0 if planet in ["Sun", "Moon"] else 0.7
                activated_houses[house] = activated_houses.get(house, 0) + weight
        
        # Check active aspects - the houses being aspected
        active_aspects = transit_data.get("active_aspects", [])
        for aspect in active_aspects:
            if isinstance(aspect, dict):
                # If aspect targets a natal planet, find which house it rules
                natal_planet = aspect.get("natal_planet", "")
                if natal_planet:
                    # Simple mapping: natal planet's house position
                    natal_positions = chart.get("planet_positions", {})
                    if natal_planet in natal_positions:
                        from services.daily_transit_window import longitude_to_house
                        natal_lon = natal_positions[natal_planet].get("longitude", 0)
                        house = longitude_to_house(natal_lon, house_cusps)
                        activated_houses[house] = activated_houses.get(house, 0) + 0.8
        
        # Check house ingresses
        house_ingresses = transit_data.get("house_ingresses", [])
        for ingress in house_ingresses:
            if isinstance(ingress, dict):
                to_house = ingress.get("to_house")
                if to_house:
                    activated_houses[to_house] = activated_houses.get(to_house, 0) + 1.2
        
        if not activated_houses:
            # Fallback: use current Moon house
            moon_house = transit_data.get("current_moon_house", 0)
            if moon_house and moon_house in HOUSE_TO_LIFE_AREA:
                return LifeAreaContext(
                    label=HOUSE_TO_LIFE_AREA[moon_house],
                    source="astrology_house",
                    house=moon_house,
                    confidence=0.55
                )
            return None
        
        # Get most activated house
        dominant_house = max(activated_houses.items(), key=lambda x: x[1])
        house_num = dominant_house[0]
        activation_score = dominant_house[1]
        
        if house_num not in HOUSE_TO_LIFE_AREA:
            return None
        
        # Calculate confidence based on activation strength
        confidence = min(0.85, 0.5 + (activation_score * 0.1))
        
        return LifeAreaContext(
            label=HOUSE_TO_LIFE_AREA[house_num],
            source="astrology_house",
            house=house_num,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"[LifeArea] Astrology extraction error: {e}")
        return None


def _get_bazi_life_area(signal: 'TensionSignal') -> Optional[LifeAreaContext]:
    """Extract life area from BaZi signal."""
    raw_data = signal.raw_data or {}
    insight = raw_data.get("insight", {})
    
    # Look for domain indicators in the insight
    domain = insight.get("domain", "") or insight.get("area", "") or ""
    domain_lower = domain.lower()
    
    for key, (label, house) in BAZI_DOMAIN_TO_LIFE_AREA.items():
        if key in domain_lower:
            return LifeAreaContext(
                label=label,
                source="bazi_domain",
                house=house,
                confidence=0.65
            )
    
    # Check tension text for domain hints
    tension = signal.tension.lower() if signal.tension else ""
    if any(w in tension for w in ["career", "work", "job", "profession"]):
        return LifeAreaContext(
            label="work and visibility",
            source="bazi_domain",
            house=10,
            confidence=0.6
        )
    if any(w in tension for w in ["relationship", "partner", "marriage"]):
        return LifeAreaContext(
            label="relationship and commitment",
            source="bazi_domain",
            house=7,
            confidence=0.6
        )
    if any(w in tension for w in ["money", "wealth", "finance"]):
        return LifeAreaContext(
            label="money and value",
            source="bazi_domain",
            house=2,
            confidence=0.6
        )
    
    return None


def _get_pattern_memory_life_area(signal: 'TensionSignal') -> Optional[LifeAreaContext]:
    """Extract life area from Pattern Memory signal."""
    raw_data = signal.raw_data or {}
    
    # Look for domain/context in pattern memory
    context = raw_data.get("context", "") or raw_data.get("domain", "") or ""
    context_lower = context.lower()
    
    # Also check the tension text itself and any evidence
    tension = signal.tension.lower() if signal.tension else ""
    evidence = signal.evidence_text.lower() if signal.evidence_text else ""
    cluster = raw_data.get("cluster", "")
    combined = f"{context_lower} {tension} {evidence} {cluster}"
    
    # Domain detection with broader patterns
    work_patterns = ["work", "career", "job", "project", "boss", "colleague", "deadline", 
                     "meeting", "email", "client", "professional", "office", "team"]
    relationship_patterns = ["relationship", "partner", "spouse", "dating", "commitment",
                            "marriage", "boyfriend", "girlfriend", "love", "intimacy"]
    money_patterns = ["money", "finance", "income", "spending", "value", "budget", 
                     "salary", "investment", "debt", "pay"]
    family_patterns = ["family", "home", "parent", "child", "mother", "father", "sibling",
                      "kids", "house", "domestic"]
    creative_patterns = ["creative", "express", "art", "write", "create", "design", 
                        "music", "perform", "show", "visible"]
    decision_patterns = ["decision", "choice", "communicate", "speak", "message", 
                        "conversation", "tell", "say", "ask", "discuss"]
    identity_patterns = ["identity", "self", "who i am", "authentic", "real me",
                        "purpose", "meaning", "direction"]
    
    if any(w in combined for w in work_patterns):
        return LifeAreaContext(
            label="work and visibility",
            source="pattern_memory",
            house=10,
            confidence=0.7
        )
    if any(w in combined for w in relationship_patterns):
        return LifeAreaContext(
            label="relationship and commitment",
            source="pattern_memory",
            house=7,
            confidence=0.7
        )
    if any(w in combined for w in money_patterns):
        return LifeAreaContext(
            label="money and value",
            source="pattern_memory",
            house=2,
            confidence=0.65
        )
    if any(w in combined for w in family_patterns):
        return LifeAreaContext(
            label="home and family",
            source="pattern_memory",
            house=4,
            confidence=0.7
        )
    if any(w in combined for w in creative_patterns):
        return LifeAreaContext(
            label="expression and creativity",
            source="pattern_memory",
            house=5,
            confidence=0.65
        )
    if any(w in combined for w in decision_patterns):
        return LifeAreaContext(
            label="communication and decisions",
            source="pattern_memory",
            house=3,
            confidence=0.6
        )
    if any(w in combined for w in identity_patterns):
        return LifeAreaContext(
            label="self and identity",
            source="pattern_memory",
            house=1,
            confidence=0.6
        )
    
    return None


# =============================================================================
# SIGNAL EXTRACTION FROM LENSES
# =============================================================================

async def extract_pattern_memory_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from Pattern Memory - HIGHEST PRIORITY."""
    try:
        from services.pattern_memory_engine import get_pattern_history
        
        # Get recent pattern history
        history = await get_pattern_history(db, user_id, days=14)
        if not history:
            logger.info(f"[TensionEngine] No pattern history for user {user_id}")
            return None
        
        # Count pattern frequencies and track context
        pattern_counts = defaultdict(int)
        pattern_recency = {}
        pattern_context = {}  # Track context/domain for each pattern
        
        for entry in history:
            # Look for tension or pattern_key in the entry
            tension = entry.get("primary_tension", "") or entry.get("pattern_key", "") or entry.get("tension", "")
            if tension:
                pattern_counts[tension] += 1
                entry_date = entry.get("date", "") or entry.get("created_at", "")
                if entry_date:
                    if isinstance(entry_date, datetime):
                        entry_date = entry_date.strftime("%Y-%m-%d")
                    pattern_recency[tension] = str(entry_date)[:10]
                # Track context for life area detection
                context = entry.get("context", "") or entry.get("domain", "") or entry.get("area", "")
                if context:
                    pattern_context[tension] = context
        
        if not pattern_counts:
            return None
        
        # Find most frequent pattern
        dominant_pattern = max(pattern_counts.items(), key=lambda x: x[1])
        pattern_key = dominant_pattern[0]
        frequency = dominant_pattern[1]
        
        # Calculate intensity based on frequency
        intensity = min(1.0, frequency / 5)  # 5+ occurrences = max intensity
        
        # Calculate confidence based on recency
        recent_date = pattern_recency.get(pattern_key, "")
        confidence = 0.5
        if recent_date:
            try:
                days_ago = (datetime.now(timezone.utc).date() - datetime.strptime(recent_date[:10], "%Y-%m-%d").date()).days
                if days_ago <= 1:
                    confidence = 1.0
                elif days_ago <= 3:
                    confidence = 0.85
                elif days_ago <= 7:
                    confidence = 0.7
            except Exception:
                pass
        
        # Map to cluster
        cluster_key = _find_matching_cluster(pattern_key)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        # Get context for this pattern
        context = pattern_context.get(pattern_key, "")
        
        return TensionSignal(
            tension=pattern_key,
            direction=cluster.get("label", "Unknown"),
            intensity=intensity,
            confidence=confidence,
            domain=cluster.get("domain", "action"),
            source="pattern_memory",
            raw_data={
                "frequency": frequency,
                "recent_date": recent_date,
                "cluster": cluster_key,
                "context": context  # Include context for life area detection
            },
            evidence_text=f"This same pattern has repeated {frequency} times in the last two weeks." if frequency >= 3 else "This pattern is returning."
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Pattern memory extraction failed: {e}")
        return None


async def extract_astrology_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from current transits."""
    try:
        from services.daily_transit_window import scan_daily_transit_window, build_daily_theme_from_events
        
        # Get user's chart
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return None
            
        # Try to get chart data
        chart = await db.astrology_charts.find_one({"user_id": user_id})
        if not chart:
            # Try to generate transit signal without natal chart
            from services.transit_signals import get_current_transit_context
            transit_ctx = get_current_transit_context()
            
            if transit_ctx and transit_ctx.get("dominant_theme"):
                tension_text = transit_ctx.get("dominant_theme", "energy shifting")
                intensity = transit_ctx.get("intensity", 0.5)
            else:
                tension_text = "momentum building"
                intensity = 0.5
        else:
            # Scan transit window with natal chart
            transit_data = scan_daily_transit_window(
                datetime.now(timezone.utc),
                chart.get("planet_positions", {}),
                chart.get("house_cusps", [])
            )
            
            if transit_data:
                theme = build_daily_theme_from_events(
                    transit_data.get("events", []),
                    transit_data.get("active_aspects", [])
                )
                tension_text = theme.get("theme", "transit activation")
                intensity = theme.get("intensity", 0.5)
            else:
                tension_text = "energy in motion"
                intensity = 0.5
        
        # Map to cluster
        cluster_key = _find_matching_cluster(tension_text)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Momentum"),
            intensity=min(1.0, intensity),
            confidence=0.7,  # Transits are reliable but less personal
            domain=cluster.get("domain", "action"),
            source="astrology",
            raw_data={
                "theme": tension_text,
                "intensity": intensity,
                "cluster": cluster_key
            },
            evidence_text="Current transits are applying pressure to your chart."
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Astrology extraction failed: {e}")
        return None


async def extract_human_design_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from Human Design mechanics."""
    try:
        # Get user's HD data
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return None
        
        hd_type = user.get("human_design_type", "")
        authority = user.get("human_design_authority", "")
        
        if not hd_type:
            return None
        
        # Map HD type + authority to typical tensions
        HD_TYPE_TENSIONS = {
            "Manifestor": ("push_vs_hold", "The urge to initiate is meeting resistance.", 0.7),
            "Generator": ("rest_vs_push", "Energy is available, but forcing won't help.", 0.65),
            "Manifesting Generator": ("precision_vs_progress", "Moving fast, but skipping steps.", 0.7),
            "Projector": ("visible_vs_hidden", "Waiting for invitation feels like stalling.", 0.75),
            "Reflector": ("clarity_vs_chaos", "Too many inputs, not enough clarity.", 0.6),
        }
        
        AUTHORITY_TENSIONS = {
            "Emotional": ("logic_vs_instinct", "The wave hasn't settled yet.", 0.7),
            "Sacral": ("push_vs_hold", "Your body knows. Listen.", 0.65),
            "Splenic": ("trust_vs_doubt", "The instinct is there. Trust it.", 0.7),
            "Ego": ("self_vs_others", "Willpower isn't infinite.", 0.65),
            "Self-Projected": ("expression_vs_suppression", "Speak to find clarity.", 0.6),
            "Mental": ("logic_vs_instinct", "Talk it through with someone.", 0.55),
            "Lunar": ("clarity_vs_chaos", "Wait for the full cycle.", 0.5),
        }
        
        # Prefer authority tension if available
        if authority and authority in AUTHORITY_TENSIONS:
            cluster_key, tension_text, intensity = AUTHORITY_TENSIONS[authority]
        elif hd_type in HD_TYPE_TENSIONS:
            cluster_key, tension_text, intensity = HD_TYPE_TENSIONS[hd_type]
        else:
            return None
        
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Inner Mechanics"),
            intensity=intensity,
            confidence=0.75,
            domain=cluster.get("domain", "decision"),
            source="human_design",
            raw_data={
                "type": hd_type,
                "authority": authority,
                "cluster": cluster_key
            },
            evidence_text=tension_text
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Human Design extraction failed: {e}")
        return None


async def extract_bazi_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from BaZi structure + timing."""
    try:
        from services.bazi_insight_layer import generate_today_insight
        
        # Get user's BaZi data
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return None
        
        bazi_chart = await db.bazi_charts.find_one({"user_id": user_id})
        if not bazi_chart:
            return None
        
        # Generate today's insight
        today_insight = generate_today_insight(bazi_chart)
        
        if not today_insight:
            return None
        
        tension_text = today_insight.get("tension", "") or today_insight.get("theme", "structural pull")
        intensity = today_insight.get("intensity", 0.5)
        
        # Map to cluster
        cluster_key = _find_matching_cluster(tension_text)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Structure"),
            intensity=min(1.0, intensity),
            confidence=0.7,
            domain=cluster.get("domain", "action"),
            source="bazi",
            raw_data={
                "insight": today_insight,
                "cluster": cluster_key
            },
            evidence_text="Your chart structure favors precision over speed."
        )
    except Exception as e:
        logger.error(f"[TensionEngine] BaZi extraction failed: {e}")
        return None


async def extract_enneagram_signal(db, user_id: str) -> Optional[TensionSignal]:
    """Extract tension signal from Enneagram defense pattern."""
    try:
        # Get user's enneagram type
        users = db["users"]
        user = await users.find_one({"_id": user_id})
        if not user:
            return None
        
        enneagram_type = user.get("enneagram_type")
        if not enneagram_type:
            return None
        
        # Map enneagram to typical tensions
        ENNEAGRAM_TENSIONS = {
            "1": ("control_vs_flow", "The inner critic is loud.", 0.7),
            "2": ("self_vs_others", "Giving more than you have.", 0.7),
            "3": ("visible_vs_hidden", "Performance mode activated.", 0.7),
            "4": ("expression_vs_suppression", "Feeling misunderstood.", 0.6),
            "5": ("logic_vs_instinct", "Retreating into analysis.", 0.7),
            "6": ("trust_vs_doubt", "Scanning for what could go wrong.", 0.75),
            "7": ("clarity_vs_chaos", "Scattered across too many options.", 0.65),
            "8": ("control_vs_flow", "Need to control the outcome.", 0.75),
            "9": ("push_vs_hold", "Avoiding the conflict.", 0.7),
        }
        
        type_num = str(enneagram_type).split("w")[0].strip()
        tension_data = ENNEAGRAM_TENSIONS.get(type_num)
        
        if not tension_data:
            return None
        
        cluster_key, tension_text, intensity = tension_data
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
        return TensionSignal(
            tension=tension_text,
            direction=cluster.get("label", "Defense Pattern"),
            intensity=intensity,
            confidence=0.6,  # Enneagram is structural, less real-time
            domain=cluster.get("domain", "emotion"),
            source="enneagram",
            raw_data={
                "type": enneagram_type,
                "cluster": cluster_key
            },
            evidence_text=tension_text
        )
    except Exception as e:
        logger.error(f"[TensionEngine] Enneagram extraction failed: {e}")
        return None


# =============================================================================
# CLUSTERING AND DOMINANCE SCORING
# =============================================================================

def _find_matching_cluster(text: str) -> str:
    """Find the best matching tension cluster for a text."""
    if not text:
        return "push_vs_hold"  # Default
    
    text_lower = text.lower()
    best_match = "push_vs_hold"
    best_score = 0
    
    for cluster_key, cluster_data in TENSION_CLUSTERS.items():
        keywords = cluster_data.get("keywords", [])
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = cluster_key
    
    return best_match


def cluster_signals(signals: List[TensionSignal]) -> Dict[str, List[TensionSignal]]:
    """Group signals by their tension cluster."""
    clusters = defaultdict(list)
    
    for signal in signals:
        cluster_key = _find_matching_cluster(signal.tension)
        clusters[cluster_key].append(signal)
    
    return dict(clusters)


def score_cluster_dominance(
    cluster_key: str,
    signals: List[TensionSignal]
) -> float:
    """
    Score dominance for a cluster using the required weights:
    - Pattern Memory: 0.45
    - Cross-lens agreement: 0.25
    - Intensity: 0.15
    - Recency: 0.15
    """
    if not signals:
        return 0.0
    
    # Pattern Memory weight (0.45)
    pattern_memory_score = 0.0
    for signal in signals:
        if signal.source == "pattern_memory":
            pattern_memory_score = signal.confidence * signal.intensity
            break
    
    # Cross-lens agreement (0.25) - more sources = higher score
    unique_sources = len(set(s.source for s in signals))
    cross_lens_score = min(1.0, unique_sources / 3)  # 3+ sources = max
    
    # Intensity (0.15) - average intensity across signals
    avg_intensity = sum(s.intensity for s in signals) / len(signals)
    
    # Recency (0.15) - highest confidence signal represents recency
    max_confidence = max(s.confidence for s in signals)
    
    # Weighted sum
    dominance = (
        0.45 * pattern_memory_score +
        0.25 * cross_lens_score +
        0.15 * avg_intensity +
        0.15 * max_confidence
    )
    
    return min(1.0, dominance)


def select_dominant_tension(
    clustered_signals: Dict[str, List[TensionSignal]]
) -> Tuple[str, List[TensionSignal], float]:
    """
    Select ONE dominant tension cluster.
    Returns: (cluster_key, signals, dominance_score)
    """
    if not clustered_signals:
        return "push_vs_hold", [], 0.0
    
    scored_clusters = []
    
    for cluster_key, signals in clustered_signals.items():
        score = score_cluster_dominance(cluster_key, signals)
        scored_clusters.append((cluster_key, signals, score))
    
    # Sort by dominance score descending
    scored_clusters.sort(key=lambda x: x[2], reverse=True)
    
    # Return the highest scoring cluster
    return scored_clusters[0]


# =============================================================================
# LANGUAGE GENERATION
# =============================================================================

def generate_energy_title(cluster_key: str, seed: int = None) -> str:
    """Generate a short, punchy energy title."""
    titles = ENERGY_TITLES.get(cluster_key, ["Something Happening"])
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    return titles[seed % len(titles)]


def generate_moment(cluster_key: str, seed: int = None) -> str:
    """Generate the sharp moment statement."""
    templates = MOMENT_TEMPLATES.get(cluster_key, ["You're in the middle of something."])
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    return templates[seed % len(templates)]


def generate_supporting_line(
    signals: List[TensionSignal],
    dominance_score: float,
    seed: int = None
) -> str:
    """Generate the supporting line based on signal characteristics."""
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    
    # Check for Pattern Memory presence (recurring)
    has_pattern_memory = any(s.source == "pattern_memory" for s in signals)
    
    # Check cross-lens agreement
    unique_sources = len(set(s.source for s in signals))
    
    # Check intensity
    avg_intensity = sum(s.intensity for s in signals) / len(signals) if signals else 0.5
    
    if has_pattern_memory:
        lines = SUPPORTING_LINES["recurring"]
    elif unique_sources >= 3:
        lines = SUPPORTING_LINES["cross_lens"]
    elif avg_intensity > 0.7:
        lines = SUPPORTING_LINES["intensity_high"]
    else:
        lines = SUPPORTING_LINES["intensity_low"]
    
    return lines[seed % len(lines)]


def generate_micro_shift(cluster_key: str, seed: int = None) -> str:
    """Generate the micro-shift action."""
    shifts = MICRO_SHIFTS.get(cluster_key, ["Do one small thing differently."])
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp())
    return shifts[seed % len(shifts)]


def generate_drivers(signals: List[TensionSignal]) -> List[Dict[str, str]]:
    """Generate the bullet-point driver evidence."""
    drivers = []
    
    for signal in signals:
        if signal.source == "pattern_memory":
            freq = signal.raw_data.get("frequency", 0) if signal.raw_data else 0
            text = f"This has shown up {freq} times recently." if freq > 0 else "This pattern keeps returning."
        elif signal.source == "astrology":
            text = "Momentum is rising, but your system is resisting it."
        elif signal.source == "human_design":
            text = "You're waiting for certainty before acting."
        elif signal.source == "bazi":
            text = "Precision is slowing movement."
        elif signal.source == "enneagram":
            text = "Control feels safer than exposure."
        else:
            text = signal.tension
        
        drivers.append({
            "source": signal.source,
            "text": text
        })
    
    return drivers


def generate_driver_synthesis(cluster_key: str, signals: List[TensionSignal]) -> str:
    """Generate the 1-2 line synthesis of what's driving this."""
    SYNTHESIS_TEMPLATES = {
        "push_vs_hold": "You're ready to move — but not trusting the move.",
        "control_vs_flow": "You're managing instead of allowing.",
        "precision_vs_progress": "You're perfecting instead of completing.",
        "visible_vs_hidden": "You want to be seen — but you're making yourself invisible.",
        "logic_vs_instinct": "You know the answer. You're just not accepting it.",
        "self_vs_others": "You're giving what you need for yourself.",
        "rest_vs_push": "Your body is asking. Your mind is refusing.",
        "clarity_vs_chaos": "You're looking for clarity in more thinking.",
        "trust_vs_doubt": "You're waiting for certainty that won't arrive.",
        "expression_vs_suppression": "The words are ready. You're not letting them out.",
    }
    
    return SYNTHESIS_TEMPLATES.get(cluster_key, "Something is happening beneath the surface.")


# =============================================================================
# MAIN ENGINE FUNCTION
# =============================================================================

async def generate_tension_moment(db, user_id: str) -> Dict[str, Any]:
    """
    V2: Generate the Home tension moment with confidence modes.
    
    CONFIDENCE MODES:
    - CONVERGED: 2+ strong lens signals align → bold moment card
    - REPEATING: Pattern memory strong, multi-lens weak → recurrence card
    - LOW_SIGNAL: Evidence weak → modest, observational card
    
    Returns:
    - mode: which confidence mode was selected
    - tension_label
    - energy_title
    - moment
    - supporting_line
    - micro_shift
    - drivers (with concrete evidence text)
    - driver_synthesis
    - confidence
    - intensity
    - debug info
    """
    logger.info(f"[TensionEngine V2] Generating tension for user {user_id}")
    
    # Collect signals from all lenses
    signals = []
    signal_debug = {}
    
    # Pattern Memory - HIGHEST PRIORITY
    pm_signal = await extract_pattern_memory_signal(db, user_id)
    if pm_signal:
        signals.append(pm_signal)
        signal_debug["pattern_memory"] = {
            "found": True,
            "tension": pm_signal.tension,
            "confidence": pm_signal.confidence,
            "intensity": pm_signal.intensity,
            "evidence": pm_signal.evidence_text
        }
        logger.info(f"[TensionEngine V2] Pattern Memory: {pm_signal.tension} (conf={pm_signal.confidence:.2f})")
    else:
        signal_debug["pattern_memory"] = {"found": False}
    
    # Astrology
    astro_signal = await extract_astrology_signal(db, user_id)
    if astro_signal:
        signals.append(astro_signal)
        signal_debug["astrology"] = {
            "found": True,
            "tension": astro_signal.tension,
            "confidence": astro_signal.confidence,
            "intensity": astro_signal.intensity,
            "evidence": astro_signal.evidence_text
        }
        logger.info(f"[TensionEngine V2] Astrology: {astro_signal.tension} (conf={astro_signal.confidence:.2f})")
    else:
        signal_debug["astrology"] = {"found": False}
    
    # Human Design
    hd_signal = await extract_human_design_signal(db, user_id)
    if hd_signal:
        signals.append(hd_signal)
        signal_debug["human_design"] = {
            "found": True,
            "tension": hd_signal.tension,
            "confidence": hd_signal.confidence,
            "intensity": hd_signal.intensity,
            "evidence": hd_signal.evidence_text
        }
        logger.info(f"[TensionEngine V2] Human Design: {hd_signal.tension} (conf={hd_signal.confidence:.2f})")
    else:
        signal_debug["human_design"] = {"found": False}
    
    # BaZi
    bazi_signal = await extract_bazi_signal(db, user_id)
    if bazi_signal:
        signals.append(bazi_signal)
        signal_debug["bazi"] = {
            "found": True,
            "tension": bazi_signal.tension,
            "confidence": bazi_signal.confidence,
            "intensity": bazi_signal.intensity,
            "evidence": bazi_signal.evidence_text
        }
        logger.info(f"[TensionEngine V2] BaZi: {bazi_signal.tension} (conf={bazi_signal.confidence:.2f})")
    else:
        signal_debug["bazi"] = {"found": False}
    
    # Enneagram
    enneagram_signal = await extract_enneagram_signal(db, user_id)
    if enneagram_signal:
        signals.append(enneagram_signal)
        signal_debug["enneagram"] = {
            "found": True,
            "tension": enneagram_signal.tension,
            "confidence": enneagram_signal.confidence,
            "intensity": enneagram_signal.intensity,
            "evidence": enneagram_signal.evidence_text
        }
        logger.info(f"[TensionEngine V2] Enneagram: {enneagram_signal.tension} (conf={enneagram_signal.confidence:.2f})")
    else:
        signal_debug["enneagram"] = {"found": False}
    
    # Count strong signals (confidence >= 0.6 and not pattern_memory alone)
    non_pm_signals = [s for s in signals if s.source != "pattern_memory"]
    strong_non_pm = [s for s in non_pm_signals if s.confidence >= 0.6]
    has_strong_pm = pm_signal is not None and pm_signal.confidence >= 0.6
    
    # Determine confidence mode
    total_signals = len(signals)
    strong_signals = len([s for s in signals if s.confidence >= 0.6])
    
    if len(strong_non_pm) >= 2 or (len(strong_non_pm) >= 1 and has_strong_pm and total_signals >= 3):
        mode = ConfidenceMode.CONVERGED
    elif has_strong_pm and total_signals <= 2:
        mode = ConfidenceMode.REPEATING
    elif total_signals >= 1:
        # At least one signal but not converged
        if has_strong_pm:
            mode = ConfidenceMode.REPEATING
        else:
            mode = ConfidenceMode.LOW_SIGNAL
    else:
        mode = ConfidenceMode.LOW_SIGNAL
    
    logger.info(f"[TensionEngine V3] Mode: {mode.value} (total={total_signals}, strong_non_pm={len(strong_non_pm)}, has_strong_pm={has_strong_pm})")
    
    # Handle no signals case
    if not signals:
        logger.warning(f"[TensionEngine V3] No signals for user {user_id}")
        return _generate_low_signal_response(user_id, signal_debug)
    
    # Cluster signals and select dominant
    clustered = cluster_signals(signals)
    dominant_cluster, dominant_signals, dominance_score = select_dominant_tension(clustered)
    logger.info(f"[TensionEngine V3] Dominant cluster: {dominant_cluster} (score={dominance_score:.2f})")
    
    # Generate seed for variety
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = int(hashlib.md5(f"{user_id}:{date_str}".encode()).hexdigest()[:8], 16)
    
    # V3: Generate scene-based content
    cluster_info = TENSION_CLUSTERS.get(dominant_cluster, {})
    tension_label = cluster_info.get("label", "Tension")
    
    # Get V3 scene templates for this cluster
    scene = V3_SCENE_TEMPLATES.get(dominant_cluster, V3_SCENE_TEMPLATES.get("push_vs_hold"))
    titles = V3_ENERGY_TITLES.get(dominant_cluster, V3_ENERGY_TITLES.get("push_vs_hold"))
    
    # V3: Scene-based generation (defaults)
    energy_title = titles[seed % len(titles)]
    default_moment = scene["moments"][seed % len(scene["moments"])]
    object_of_tension = scene["objects"][seed % len(scene["objects"])]
    default_contradiction = scene["contradictions"][seed % len(scene["contradictions"])]
    default_cost = scene["costs"][seed % len(scene["costs"])]
    avoided_move = scene["avoided_moves"][seed % len(scene["avoided_moves"])]
    
    # V3.1: Derive life area context for grounding (do this early so we can shape copy)
    life_area = await derive_life_area_context(db, user_id, dominant_signals, dominant_cluster)
    life_area_context = None
    house_num = None
    if life_area:
        house_num = life_area.house
        life_area_context = {
            "label": life_area.label,
            "source": life_area.source,
            "house": life_area.house,
            "confidence": round(life_area.confidence, 2)
        }
        logger.info(f"[TensionEngine V3.3] Life area: {life_area.label} (source={life_area.source}, conf={life_area.confidence})")
    
    # V3.3: Use real-world moment templates
    v33_moments = V33_REAL_WORLD_MOMENTS.get(dominant_cluster, V33_REAL_WORLD_MOMENTS.get("push_vs_hold"))
    moment = v33_moments[seed % len(v33_moments)]
    
    # V3.3: Apply house context to shape moment if strong confidence
    if life_area and life_area.confidence >= 0.6 and house_num:
        house_moments = HOUSE_CONTEXTUALIZED_MOMENTS.get(house_num, {})
        if dominant_cluster in house_moments:
            moment = house_moments[dominant_cluster]
    
    # V3.3: Get cause line (why now, human language)
    cause_lines = V33_CAUSE_LINES.get(dominant_cluster, V33_CAUSE_LINES.get("push_vs_hold"))
    cause_line = cause_lines[seed % len(cause_lines)]
    
    # V3.3: Get explicit object (mandatory)
    objects = V33_EXPLICIT_OBJECTS.get(dominant_cluster, V33_EXPLICIT_OBJECTS.get("push_vs_hold"))
    about = objects[seed % len(objects)]
    
    # V3.3: Get tight contradiction
    contradictions = V33_TIGHT_CONTRADICTIONS.get(dominant_cluster, V33_TIGHT_CONTRADICTIONS.get("push_vs_hold"))
    contradiction = contradictions[seed % len(contradictions)]
    
    # V3.3: Apply house context to contradiction if strong
    if life_area and life_area.confidence >= 0.6 and house_num:
        if house_num in HOUSE_CONTEXTUALIZED_CONTRADICTIONS:
            contradiction = HOUSE_CONTEXTUALIZED_CONTRADICTIONS[house_num]
    
    # V3.3: Get current cost (house-shaped if possible)
    current_cost = scene["costs"][seed % len(scene["costs"])]
    if life_area and life_area.confidence >= 0.6 and house_num:
        if house_num in HOUSE_CONTEXTUALIZED_COSTS:
            current_cost = HOUSE_CONTEXTUALIZED_COSTS[house_num]
    
    # V3.3: Dynamic tension label (situation-specific)
    dynamic_labels = V33_DYNAMIC_TENSION_LABELS.get(dominant_cluster, ["Move vs Wait"])
    tension_label_dynamic = dynamic_labels[seed % len(dynamic_labels)]
    
    # V3.3: Pattern reason (behavioral tendency)
    pattern_reason = V33_PATTERN_REASONS.get(dominant_cluster, "This is a recurring pattern.")
    
    # V3.2: Determine trigger confidence
    trigger_confidence = determine_trigger_confidence(dominant_signals)
    logger.info(f"[TensionEngine V3.3] Trigger confidence: {trigger_confidence.value}")
    
    # V3.2: Split drivers into why_recurring and why_now
    why_recurring, why_now = split_drivers_by_why(dominant_signals)
    
    # V3.3: Generate why_now_plain (visible, no astrology terms)
    if trigger_confidence == TriggerConfidence.STRONGLY_ACTIVE_NOW:
        why_now_plain = cause_line  # Use the cause line directly
    elif trigger_confidence == TriggerConfidence.RECURRING_PLUS_TRIGGER:
        why_now_plain = "Something is amplifying this pattern right now."
    else:
        why_now_plain = "This is a recurring pattern, not a new trigger."
    
    # V3.3: Technical explanation (hidden layer, only for debug/accordion)
    why_now_technical = None
    for signal in dominant_signals:
        if signal.source == "astrology":
            transit = signal.raw_data.get("transit", "") or signal.raw_data.get("aspect", "")
            if transit:
                why_now_technical = f"Transit activation: {transit}"
            else:
                why_now_technical = "Current planetary positions are activating this area of your chart."
            break
    
    # Mode-specific supporting line
    if mode == ConfidenceMode.CONVERGED:
        supporting_line = CONVERGED_SUPPORTING[seed % len(CONVERGED_SUPPORTING)]
    elif mode == ConfidenceMode.REPEATING:
        # V3.3: Be honest about recurrence
        if trigger_confidence == TriggerConfidence.RECURRING_ONLY:
            supporting_variations = [
                "This keeps happening. The pattern is real.",
                "You've been here before. That's the information.",
                "This is familiar territory. That's worth noticing.",
                "The recurrence is the message."
            ]
        else:
            supporting_variations = [
                f"You've circled {about} before. Today it's pressing.",
                "This is familiar, but something is amplifying it now.",
                "You've been here before. Today, it's louder.",
                "The pattern is back, and it's asking for attention."
            ]
        supporting_line = supporting_variations[seed % len(supporting_variations)]
    else:
        return _generate_low_signal_response(user_id, signal_debug, dominant_cluster, dominant_signals)
    
    micro_shift = f"Start with {avoided_move}." if len(avoided_move) < 30 else scene["avoided_moves"][(seed + 1) % len(scene["avoided_moves"])]
    
    # V3.3: Generate synthesis based on trigger confidence
    driver_synthesis = generate_v32_synthesis(
        trigger_confidence,
        why_recurring,
        why_now,
        life_area.label if life_area else None
    )
    
    # Keep old drivers format for backward compatibility
    drivers = generate_v3_drivers(dominant_signals)
    
    # Calculate overall confidence and intensity
    avg_confidence = sum(s.confidence for s in dominant_signals) / len(dominant_signals)
    avg_intensity = sum(s.intensity for s in dominant_signals) / len(dominant_signals)
    
    return {
        "mode": mode.value,
        "trigger_confidence": trigger_confidence.value,
        # V3.3: New output structure
        "moment": moment,
        "cause_line": cause_line,
        "where": life_area.label if life_area else None,
        "about": about,
        "contradiction": contradiction,
        "current_cost": current_cost,
        "supporting_line": supporting_line,
        # V3.3: WHY layers (visible)
        "why_now_plain": why_now_plain,
        "pattern_reason": pattern_reason,
        # V3.3: Technical (hidden)
        "why_now_technical": why_now_technical,
        # V3.3: Dynamic tension label
        "tension_label_dynamic": tension_label_dynamic,
        "tension_label": tension_label,  # Keep old for compat
        "energy_title": energy_title,
        "avoided_move": avoided_move,
        "micro_shift": micro_shift,
        # V3.2 backward compat
        "life_area_context": life_area_context,
        "object_of_tension": about,  # Alias for compat
        "why_recurring": why_recurring,
        "why_now": why_now,
        "drivers": drivers,
        "driver_synthesis": driver_synthesis,
        "confidence": round(avg_confidence, 2),
        "intensity": round(avg_intensity, 2),
        "fallback_used": False,
        "debug": {
            "version": "v3.3_clarity_engine",
            "cluster": dominant_cluster,
            "dominance_score": round(dominance_score, 2),
            "signal_count": len(signals),
            "strong_signal_count": strong_signals,
            "trigger_confidence": trigger_confidence.value,
            "mode_reason": f"non_pm_strong={len(strong_non_pm)}, has_pm={has_strong_pm}, total={total_signals}",
            "signals_used": [s.source for s in dominant_signals],
            "life_area_source": life_area.source if life_area else None,
            "house_copy_applied": life_area is not None and life_area.confidence >= 0.6,
            "all_signals": signal_debug
        }
    }


def _generate_low_signal_response(
    user_id: str,
    signal_debug: Dict,
    dominant_cluster: str = None,
    dominant_signals: List[TensionSignal] = None
) -> Dict[str, Any]:
    """Generate a modest, honest low-signal response."""
    seed = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
    
    moments = LOW_SIGNAL_MOMENTS["default"]
    titles = LOW_SIGNAL_TITLES
    supporting = LOW_SIGNAL_SUPPORTING
    
    return {
        "mode": ConfidenceMode.LOW_SIGNAL.value,
        "tension_label": "Forming",
        "energy_title": titles[seed % len(titles)],
        "moment": moments[seed % len(moments)],
        "supporting_line": supporting[seed % len(supporting)],
        "micro_shift": "Notice what's present without forcing a name.",
        "drivers": [],
        "driver_synthesis": "Not enough clarity yet to say more.",
        "confidence": 0.3,
        "intensity": 0.3,
        "fallback_used": True,
        "debug": {
            "cluster": dominant_cluster,
            "dominance_score": 0.0,
            "signal_count": len(dominant_signals) if dominant_signals else 0,
            "strong_signal_count": 0,
            "mode_reason": "low_signal_evidence",
            "signals_used": [],
            "all_signals": signal_debug
        }
    }


# =============================================================================
# V2: MODE-SPECIFIC GENERATORS
# =============================================================================

def generate_converged_energy_title(seed: int) -> str:
    """Energy title for converged mode (bold)."""
    return CONVERGED_TITLES[seed % len(CONVERGED_TITLES)]


def generate_repeating_energy_title(seed: int) -> str:
    """Energy title for repeating mode (honest recurrence)."""
    return REPEATING_TITLES[seed % len(REPEATING_TITLES)]


def generate_converged_moment(cluster_key: str, seed: int) -> str:
    """Moment text for converged mode (bold, undeniable)."""
    moments = CONVERGED_MOMENTS.get(cluster_key, CONVERGED_MOMENTS.get("push_vs_hold", []))
    return moments[seed % len(moments)]


def generate_repeating_moment(cluster_key: str, seed: int) -> str:
    """Moment text for repeating mode (honest recurrence)."""
    moments = REPEATING_MOMENTS.get(cluster_key, REPEATING_MOMENTS.get("push_vs_hold", []))
    return moments[seed % len(moments)]


def generate_converged_supporting(seed: int) -> str:
    """Supporting line for converged mode."""
    return CONVERGED_SUPPORTING[seed % len(CONVERGED_SUPPORTING)]


def generate_repeating_supporting(seed: int) -> str:
    """Supporting line for repeating mode."""
    return REPEATING_SUPPORTING[seed % len(REPEATING_SUPPORTING)]


def generate_v2_drivers(signals: List[TensionSignal]) -> List[Dict[str, str]]:
    """
    V2: Generate concrete, evidence-based driver text.
    NOT filler. Real statements.
    """
    drivers = []
    
    for signal in signals:
        # Use the evidence_text if available, otherwise generate based on source
        if signal.evidence_text:
            text = signal.evidence_text
        else:
            text = _generate_driver_evidence(signal)
        
        drivers.append({
            "source": signal.source,
            "text": text
        })
    
    return drivers


def _generate_driver_evidence(signal: TensionSignal) -> str:
    """Generate concrete evidence text for a signal."""
    source = signal.source
    raw = signal.raw_data or {}
    
    if source == "pattern_memory":
        freq = raw.get("frequency", 0)
        if freq >= 5:
            return f"This same hesitation has repeated {freq} times in two weeks."
        elif freq >= 3:
            return f"This pattern has shown up {freq} times recently."
        elif freq >= 1:
            return "This is a returning pattern."
        else:
            return "Pattern memory active."
    
    elif source == "astrology":
        theme = raw.get("theme", "")
        if "momentum" in theme.lower():
            return "Momentum is rising, but conviction is blurred."
        elif "tension" in theme.lower():
            return "Transit tension is active in your chart today."
        else:
            return "Current transits are applying pressure."
    
    elif source == "human_design":
        hd_type = raw.get("type", "")
        authority = raw.get("authority", "")
        if authority == "Emotional":
            return "Your emotional wave hasn't settled yet."
        elif authority == "Sacral":
            return "Your body knows. You're not listening."
        elif authority == "Splenic":
            return "The instinct is there. You're overriding it."
        elif hd_type == "Projector":
            return "You're pushing for recognition instead of waiting."
        elif hd_type == "Generator":
            return "You're initiating instead of responding."
        else:
            return f"Your {hd_type} mechanics are creating friction."
    
    elif source == "bazi":
        return "Your chart structure favors precision over speed."
    
    elif source == "enneagram":
        etype = raw.get("type", "")
        if "1" in str(etype):
            return "The inner critic is loud right now."
        elif "6" in str(etype):
            return "You're scanning for what could go wrong."
        elif "9" in str(etype):
            return "Avoidance is protecting you from conflict."
        else:
            return "Defense pattern activated."
    
    return signal.tension or "Signal detected."


# =============================================================================
# V3: SCENE-BASED DRIVER AND SYNTHESIS GENERATORS
# =============================================================================

def generate_v3_drivers(signals: List[TensionSignal]) -> List[Dict[str, str]]:
    """
    V3: Generate concrete, situation-aware driver text.
    Each driver should answer: what is THIS source saying about THIS situation?
    """
    drivers = []
    
    for signal in signals:
        source = signal.source
        raw = signal.raw_data or {}
        
        if source == "pattern_memory":
            freq = raw.get("frequency", 0)
            if freq >= 5:
                text = f"You've circled this same decision {freq} times in two weeks."
            elif freq >= 3:
                text = f"This exact stuck point has shown up {freq} times recently."
            else:
                text = "This isn't the first time you've been here."
        
        elif source == "astrology":
            text = "Transits are pushing for movement your system isn't making."
        
        elif source == "human_design":
            authority = raw.get("authority", "")
            if authority == "Emotional":
                text = "Your emotional clarity hasn't arrived yet. You're acting before it does."
            elif authority == "Sacral":
                text = "Your body has an answer. Your mind is overruling it."
            elif authority == "Splenic":
                text = "There's an instinct you're not following."
            else:
                text = "Your mechanics are creating friction with what you're trying to do."
        
        elif source == "bazi":
            text = "Your chart structure makes this kind of pause predictable."
        
        elif source == "enneagram":
            etype = raw.get("type", "")
            if "1" in str(etype):
                text = "The perfectionist voice is holding you back."
            elif "2" in str(etype):
                text = "You're prioritizing their comfort over your need."
            elif "3" in str(etype):
                text = "You're protecting an image instead of moving."
            elif "4" in str(etype):
                text = "You're waiting to feel more before you act."
            elif "5" in str(etype):
                text = "You're gathering more information instead of using what you have."
            elif "6" in str(etype):
                text = "You're scanning for problems instead of acting."
            elif "7" in str(etype):
                text = "You're keeping options open to avoid commitment."
            elif "8" in str(etype):
                text = "You're trying to control instead of allow."
            elif "9" in str(etype):
                text = "You're keeping the peace at your expense."
            else:
                text = "A defense pattern is active."
        
        else:
            text = signal.evidence_text or "Signal detected."
        
        drivers.append({
            "source": source,
            "text": text
        })
    
    return drivers


def generate_v3_synthesis(
    cluster_key: str,
    signals: List[TensionSignal],
    contradiction: str,
    current_cost: str
) -> str:
    """
    V3: Generate driver synthesis that explains WHY this is showing up.
    Should feel like insight, not category label.
    """
    signal_count = len(signals)
    sources = [s.source for s in signals]
    
    # If multiple lenses agree, highlight the convergence
    if signal_count >= 3:
        return f"This isn't just one thing. Multiple parts of your system are pointing at the same stuck point: {contradiction.lower()}"
    
    # If pattern memory is primary
    if "pattern_memory" in sources and signal_count <= 2:
        return "This is less about today and more about a repeated moment you keep arriving at."
    
    # Cluster-specific synthesis
    SYNTHESIS_BY_CLUSTER = {
        "push_vs_hold": "You're not confused about what to do. You're avoiding the discomfort of doing it.",
        "control_vs_flow": "The grip isn't protecting anything. It's creating the friction you're trying to avoid.",
        "precision_vs_progress": "Quality isn't the real issue. Fear of being seen imperfect is.",
        "visible_vs_hidden": "You want to be seen, but you're doing everything to stay invisible.",
        "logic_vs_instinct": "The answer already exists. You're looking for permission, not information.",
        "self_vs_others": "You're losing yourself in someone else's needs while yours go unmet.",
        "rest_vs_push": "You're treating depletion like weakness instead of a signal.",
        "clarity_vs_chaos": "You're looking for clarity through thinking. It won't come that way.",
        "trust_vs_doubt": "Checking again won't give you certainty. Only action will.",
        "expression_vs_suppression": "The pressure isn't going away because the thing hasn't been said."
    }
    
    return SYNTHESIS_BY_CLUSTER.get(cluster_key, f"The core tension: {contradiction.lower()}")


# =============================================================================
# V3.2: TRIGGER CONFIDENCE AND SPLIT WHY LAYERS
# =============================================================================

def determine_trigger_confidence(signals: List[TensionSignal]) -> TriggerConfidence:
    """
    V3.2: Determine whether this is primarily recurring, has a current trigger, or is strongly active now.
    
    Returns:
    - RECURRING_ONLY: Only pattern memory/structural sources, no current activation
    - RECURRING_PLUS_TRIGGER: Has both recurring pattern and some current signal
    - STRONGLY_ACTIVE_NOW: Strong current activation evidence (astrology, recent spike)
    """
    recurring_signals = []
    now_signals = []
    
    for signal in signals:
        if signal.source in RECURRING_SOURCES:
            recurring_signals.append(signal)
        if signal.source in NOW_SOURCES:
            now_signals.append(signal)
    
    # Check for strong current activation
    strong_now = [s for s in now_signals if s.confidence >= 0.7]
    
    # Check for recent pattern spike (intensity or frequency indicator)
    pattern_spike = False
    for signal in recurring_signals:
        if signal.source == "pattern_memory":
            freq = signal.raw_data.get("frequency", 0)
            if freq >= 4:  # 4+ times in 2 weeks = spike
                pattern_spike = True
                break
    
    # Determine trigger confidence
    if strong_now:
        return TriggerConfidence.STRONGLY_ACTIVE_NOW
    elif now_signals or pattern_spike:
        return TriggerConfidence.RECURRING_PLUS_TRIGGER
    else:
        return TriggerConfidence.RECURRING_ONLY


def split_drivers_by_why(signals: List[TensionSignal]) -> Tuple[List[Dict], List[Dict]]:
    """
    V3.2: Split drivers into two categories:
    - why_recurring: Explains long-term pattern (PM, Enneagram, BaZi, HD)
    - why_now: Explains current activation (Astrology, recency spike)
    
    Returns: (why_recurring_drivers, why_now_drivers)
    """
    why_recurring = []
    why_now = []
    
    for signal in signals:
        source = signal.source
        raw = signal.raw_data or {}
        
        # Generate the driver text (reuse existing logic)
        if source == "pattern_memory":
            freq = raw.get("frequency", 0)
            if freq >= 5:
                text = f"You've circled this {freq} times in two weeks. This isn't new territory."
            elif freq >= 3:
                text = f"This exact pattern has repeated {freq} times recently."
            else:
                text = "This isn't the first time you've been here."
            why_recurring.append({"source": "Pattern Memory", "text": text})
            
            # If high frequency, also add to why_now as a spike indicator
            if freq >= 4:
                why_now.append({
                    "source": "Recent Spike",
                    "text": f"Frequency jumped to {freq} occurrences. Something is pressing."
                })
        
        elif source == "enneagram":
            etype = raw.get("type", "")
            if "1" in str(etype):
                text = "Your perfectionist defense makes this pause predictable."
            elif "2" in str(etype):
                text = "Your need to be needed keeps you giving first."
            elif "3" in str(etype):
                text = "Image protection is blocking authentic action."
            elif "4" in str(etype):
                text = "You wait to feel more before you act."
            elif "5" in str(etype):
                text = "You gather instead of using what you have."
            elif "6" in str(etype):
                text = "Your doubt pattern makes you scan for problems."
            elif "7" in str(etype):
                text = "Keeping options open helps you avoid commitment."
            elif "8" in str(etype):
                text = "Control is your default response to uncertainty."
            elif "9" in str(etype):
                text = "Peace-keeping keeps you from speaking your truth."
            else:
                text = "A core defense pattern is contributing."
            why_recurring.append({"source": "Enneagram", "text": text})
        
        elif source == "human_design":
            authority = raw.get("authority", "")
            hd_type = raw.get("type", "")
            if authority == "Emotional":
                text = "Your emotional authority requires time. Rushing creates friction."
            elif authority == "Sacral":
                text = "Your sacral response is being overruled by thinking."
            elif authority == "Splenic":
                text = "Your splenic hits are instant. You're not following them."
            elif hd_type == "Projector":
                text = "You initiate when you should wait for recognition."
            elif hd_type == "Generator":
                text = "You're initiating instead of responding to life."
            elif hd_type == "Manifestor":
                text = "You're asking permission when you should inform and act."
            else:
                text = "Your mechanics create predictable friction here."
            why_recurring.append({"source": "Human Design", "text": text})
        
        elif source == "bazi":
            text = "Your chart structure shows this timing pattern."
            why_recurring.append({"source": "BaZi", "text": text})
        
        elif source == "astrology":
            # Astrology is a NOW signal
            transit_info = raw.get("transit", "") or raw.get("aspect", "") or ""
            if transit_info:
                text = f"Current transit is pushing this forward: {transit_info}"
            else:
                text = "Today's transits are activating this exact tension."
            why_now.append({"source": "Astrology", "text": text})
    
    return why_recurring, why_now


def generate_v32_synthesis(
    trigger_confidence: TriggerConfidence,
    why_recurring: List[Dict],
    why_now: List[Dict],
    life_area_label: Optional[str] = None
) -> str:
    """
    V3.2: Generate synthesis that acknowledges whether this is recurring vs currently triggered.
    """
    if trigger_confidence == TriggerConfidence.STRONGLY_ACTIVE_NOW:
        if life_area_label:
            return f"This isn't just a pattern—something in your {life_area_label} is actively pushing it forward right now."
        return "This isn't just a pattern—something is actively pushing it forward right now."
    
    elif trigger_confidence == TriggerConfidence.RECURRING_PLUS_TRIGGER:
        if life_area_label:
            return f"This is a familiar pattern, and something in your {life_area_label} is amplifying it today."
        return "This is a familiar pattern, but something is amplifying it today."
    
    else:  # RECURRING_ONLY
        if len(why_recurring) >= 2:
            return "This keeps happening because multiple parts of your system reinforce it."
        return "This keeps happening. The pattern is structural, not situational."


def apply_house_context_to_copy(
    life_area: Optional['LifeAreaContext'],
    cluster: str,
    default_moment: str,
    default_contradiction: str,
    default_cost: str
) -> Tuple[str, str, str]:
    """
    V3.2: Use house context to shape the actual copy when confidence is high enough.
    
    Returns: (moment, contradiction, cost) - possibly house-contextualized
    """
    if not life_area or life_area.confidence < 0.6:
        return default_moment, default_contradiction, default_cost
    
    house = life_area.house
    
    # Try to get house-contextualized moment
    moment = default_moment
    if house in HOUSE_CONTEXTUALIZED_MOMENTS:
        cluster_moments = HOUSE_CONTEXTUALIZED_MOMENTS[house]
        if cluster in cluster_moments:
            moment = cluster_moments[cluster]
    
    # Try to get house-contextualized contradiction
    contradiction = default_contradiction
    if house in HOUSE_CONTEXTUALIZED_CONTRADICTIONS:
        contradiction = HOUSE_CONTEXTUALIZED_CONTRADICTIONS[house]
    
    # Try to get house-contextualized cost
    cost = default_cost
    if house in HOUSE_CONTEXTUALIZED_COSTS:
        cost = HOUSE_CONTEXTUALIZED_COSTS[house]
    
    return moment, contradiction, cost

