"""
Tension Engine V3.0 - Scene-Based Tension Resolution System

CORE PRINCIPLE:
Mirror is NOT a lens aggregator.
Mirror is a REAL-TIME SCENE ENGINE.

V3.0 EVOLUTION:
Home must not just identify a tension CATEGORY. It must identify a LIVED MOMENT.

A resonant Home card contains 4 things:
1. A CONCRETE OBJECT (the decision, conversation, message, move, unresolved thing)
2. A FELT CONTRADICTION (you want X but you keep doing Y)
3. A CURRENT STAKE (what this is costing right now)
4. A SCENE-LIKE QUALITY (catches the user in the act)

V3.0 OUTPUT FIELDS:
- moment: Sharp opening line
- object_of_tension: What this is about (decision, conversation, etc.)
- contradiction: The felt pull in opposite directions
- current_cost: What this is costing right now
- avoided_move: The thing not being done
- supporting_line: Reinforcement
- micro_shift: One action

LANGUAGE RULES:
- PREFER: decision, conversation, move, message, commitment, naming, saying, acting
- AVOID LEADING WITH: hesitation, tendency, pattern, dynamic, signal

CONFIDENCE MODES:
- CONVERGED: 2+ strong lens signals → scene-based bold moment
- REPEATING: Pattern memory strong → pattern-aware but still scene-based
- LOW_SIGNAL: Weak evidence → observational, no bold claims

OUTPUT: One scene, one contradiction, one cost.
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
        
        # Count pattern frequencies
        pattern_counts = defaultdict(int)
        pattern_recency = {}
        
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
            except:
                pass
        
        # Map to cluster
        cluster_key = _find_matching_cluster(pattern_key)
        cluster = TENSION_CLUSTERS.get(cluster_key, {})
        
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
                "cluster": cluster_key
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
    
    # V3: Scene-based generation
    energy_title = titles[seed % len(titles)]
    moment = scene["moments"][seed % len(scene["moments"])]
    object_of_tension = scene["objects"][seed % len(scene["objects"])]
    contradiction = scene["contradictions"][seed % len(scene["contradictions"])]
    current_cost = scene["costs"][seed % len(scene["costs"])]
    avoided_move = scene["avoided_moves"][seed % len(scene["avoided_moves"])]
    
    # Mode-specific supporting line
    if mode == ConfidenceMode.CONVERGED:
        supporting_line = CONVERGED_SUPPORTING[seed % len(CONVERGED_SUPPORTING)]
    elif mode == ConfidenceMode.REPEATING:
        # V3: For repeating, acknowledge it's a pattern but still scene-based
        supporting_variations = [
            f"You've circled {object_of_tension} before.",
            "This scene is familiar.",
            "You've been here before. Same stuck point.",
            f"Same territory: {avoided_move} keeps getting postponed.",
            "The pattern is recognizable. The moment is now."
        ]
        supporting_line = supporting_variations[seed % len(supporting_variations)]
    else:
        return _generate_low_signal_response(user_id, signal_debug, dominant_cluster, dominant_signals)
    
    micro_shift = f"Start with {avoided_move}." if len(avoided_move) < 30 else scene["avoided_moves"][(seed + 1) % len(scene["avoided_moves"])]
    drivers = generate_v3_drivers(dominant_signals)
    
    # V3: Driver synthesis should answer "why this is showing up"
    driver_synthesis = generate_v3_synthesis(dominant_cluster, dominant_signals, contradiction, current_cost)
    
    # Calculate overall confidence and intensity
    avg_confidence = sum(s.confidence for s in dominant_signals) / len(dominant_signals)
    avg_intensity = sum(s.intensity for s in dominant_signals) / len(dominant_signals)
    
    return {
        "mode": mode.value,
        "tension_label": tension_label,
        "energy_title": energy_title,
        "moment": moment,
        "object_of_tension": object_of_tension,
        "contradiction": contradiction,
        "current_cost": current_cost,
        "avoided_move": avoided_move,
        "supporting_line": supporting_line,
        "micro_shift": micro_shift,
        "drivers": drivers,
        "driver_synthesis": driver_synthesis,
        "confidence": round(avg_confidence, 2),
        "intensity": round(avg_intensity, 2),
        "fallback_used": False,
        "debug": {
            "version": "v3_scene_engine",
            "cluster": dominant_cluster,
            "dominance_score": round(dominance_score, 2),
            "signal_count": len(signals),
            "strong_signal_count": strong_signals,
            "mode_reason": f"non_pm_strong={len(strong_non_pm)}, has_pm={has_strong_pm}, total={total_signals}",
            "signals_used": [s.source for s in dominant_signals],
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

