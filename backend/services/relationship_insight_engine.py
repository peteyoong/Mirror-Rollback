"""Relationship Insight Engine V2.1

Generates 1:1 dynamic reflections that help the user understand:
1) What is happening between them
2) What they need to shift in themselves

CRITICAL RULES:
- Always center the USER, not the other person
- Never suggest what the other person should do
- Do not blame, diagnose, or fix the other person
- Use grounded, real-life language
- Make it feel specific, relational, and slightly confronting

STRUCTURE:
1. ESSENCE - What they are / how they move (1-2 lines)
2. FRICTION - Where it clashes with you (1-2 lines)
3. TENSION - What happens between you (1-2 lines)
4. YOUR SHIFT - What YOU need to adjust (2-3 lines) - MOST IMPORTANT
5. GIFT - Why this person matters in your life (1-2 lines)
6. WHY THIS CONNECTION EXISTS - Meaning layer (2-3 lines)
7. TRY THIS - ONE specific behavioral action

V2.1 UPGRADES:
- Dynamic meaning generation (no fixed templates)
- Subtle activation signals when relevant
- Shorter, more evocative language
- Let users feel meaning, not be told conclusions

TONE: Direct, grounded, human. Slight edge is okay.
"""

import logging
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# STABLE MEANING GENERATOR V3.0
# =============================================================================
# Principles:
# 1. IDENTITY-LEVEL: Stable, trustworthy, feels like a recurring life lesson
# 2. 1:1 LEVEL: Anchored variation - same truth, lighter phrasing shifts
# 3. ACTIVATION: Earned only - never random
# 4. PATTERN LOOPS: Only when recurrence is detected
# 5. INTERRUPTS: Only when pattern is active

# -----------------------------------------------------------------------------
# CORE TRUTHS (Stable - these don't change)
# -----------------------------------------------------------------------------
# Each type has ONE core relational truth that remains consistent

IDENTITY_CORE_TRUTHS = {
    "initiator": {
        "core_truth": "Reaching needs landing.",
        "expanded": "You keep meeting people who don't match your speed. That's not random.",
        "lesson": "Connection isn't just about starting. It's about what lands.",
    },
    "reflector": {
        "core_truth": "Response is action.",
        "expanded": "You keep attracting people who want more than you're showing. That's not random.",
        "lesson": "Your interior needs to reach the surface sometimes.",
    },
    "momentum_carrier": {
        "core_truth": "Force needs awareness.",
        "expanded": "You keep meeting people who slow you down. That's not random.",
        "lesson": "Momentum includes knowing when to pause.",
    },
    "attunement_holder": {
        "core_truth": "Sensing can happen while moving.",
        "expanded": "You keep attracting people who move faster than you sense. That's not random.",
        "lesson": "Reading the room includes moving through it.",
    },
    "certainty_seeker": {
        "core_truth": "Some truths arrive before words.",
        "expanded": "You keep meeting people who can't give straight answers. That's not random.",
        "lesson": "Not all knowing can be pinned down.",
    },
    "sensor": {
        "core_truth": "Impressions can become language.",
        "expanded": "You keep meeting people who want you to be more concrete. That's not random.",
        "lesson": "Your sensing can be shared without losing its truth.",
    },
    "expresser": {
        "core_truth": "Being seen isn't being matched.",
        "expanded": "You keep meeting people who don't show as much as you. That's not random.",
        "lesson": "Expression can land without being mirrored.",
    },
    "absorber": {
        "core_truth": "Surfacing doesn't mean emptying.",
        "expanded": "You keep meeting people who want more from you than silence. That's not random.",
        "lesson": "Small signals matter more than you think.",
    },
    "action_taker": {
        "core_truth": "The field has information too.",
        "expanded": "You keep meeting people who want you to slow down. That's not random.",
        "lesson": "Action without awareness misses things.",
    },
    "atmospheric_reader": {
        "core_truth": "Reading can happen in motion.",
        "expanded": "You keep meeting people who move before you've finished reading. That's not random.",
        "lesson": "The room changes anyway.",
    },
    "container": {
        "core_truth": "Edges can have doors.",
        "expanded": "You keep meeting people who want inside what you're protecting. That's not random.",
        "lesson": "Opening isn't the same as flooding.",
    },
    "porous": {
        "core_truth": "Feeling without absorbing is possible.",
        "expanded": "You keep meeting people with clearer edges than you. That's not random.",
        "lesson": "You can choose what you carry.",
    },
}

# -----------------------------------------------------------------------------
# RELATIONAL TRUTHS (1:1 Dynamics - Anchored)
# -----------------------------------------------------------------------------
# Each pair has ONE core relational truth with 2-3 variations

RELATIONAL_CORE_TRUTHS = {
    ("initiator", "reflector"): {
        "core": "You create openings. They deepen what enters.",
        "variations": [
            "What you start needs somewhere to land.",
            "Your motion meets their stillness. Neither is wrong.",
        ],
    },
    ("reflector", "initiator"): {
        "core": "They bring motion. You bring depth.",
        "variations": [
            "Their reaching draws out your response.",
            "Without their push, you'd stay internal.",
        ],
    },
    ("momentum_carrier", "attunement_holder"): {
        "core": "You carry force. They carry awareness.",
        "variations": [
            "Your power needs their sensing.",
            "Force without calibration is rough.",
        ],
    },
    ("attunement_holder", "momentum_carrier"): {
        "core": "They move. You read.",
        "variations": [
            "Their force gives you something to shape.",
            "Your awareness shapes their power.",
        ],
    },
    ("certainty_seeker", "sensor"): {
        "core": "You anchor. They perceive.",
        "variations": [
            "Facts meet impressions here.",
            "Some things can't be named until they're felt.",
        ],
    },
    ("sensor", "certainty_seeker"): {
        "core": "They give structure. You give texture.",
        "variations": [
            "Your impressions become their facts.",
            "Without them, sensing stays formless.",
        ],
    },
    ("expresser", "absorber"): {
        "core": "You show. They hold.",
        "variations": [
            "What you express lands somewhere real.",
            "They take you in differently than others.",
        ],
    },
    ("absorber", "expresser"): {
        "core": "They model showing. You model receiving.",
        "variations": [
            "Their visibility invites yours.",
            "Small expressions from you mean more.",
        ],
    },
    ("action_taker", "atmospheric_reader"): {
        "core": "You change the room. They read the change.",
        "variations": [
            "You can't see what you create. They can.",
            "Action meets perception here.",
        ],
    },
    ("atmospheric_reader", "action_taker"): {
        "core": "They act. You perceive the impact.",
        "variations": [
            "You see consequences they can't.",
            "Your perception shapes their direction.",
        ],
    },
    ("initiator", "attunement_holder"): {
        "core": "You start. They feel whether it's right.",
        "variations": [
            "Not every start lands well.",
            "Initiation needs calibration.",
        ],
    },
    ("attunement_holder", "initiator"): {
        "core": "They start. You sense the field.",
        "variations": [
            "Let their motion teach you.",
            "You can attune while moving.",
        ],
    },
    ("momentum_carrier", "sensor"): {
        "core": "You build. They feel what's coming.",
        "variations": [
            "Force meets foresight here.",
            "Momentum lands better with direction.",
        ],
    },
    ("sensor", "momentum_carrier"): {
        "core": "They carry. You shape.",
        "variations": [
            "Your sensing gives their force direction.",
            "Together: force with feeling.",
        ],
    },
    ("expresser", "container"): {
        "core": "You show. They hold steady.",
        "variations": [
            "They receive without flooding.",
            "Not everyone needs to match you.",
        ],
    },
    ("container", "expresser"): {
        "core": "They model visibility. You model steadiness.",
        "variations": [
            "Small openings from you mean more.",
            "Your edges can have doors.",
        ],
    },
    ("certainty_seeker", "attunement_holder"): {
        "core": "You need names. They feel fields.",
        "variations": [
            "Different intelligences. Different timings.",
            "Some knowing arrives through feeling.",
        ],
    },
    ("attunement_holder", "certainty_seeker"): {
        "core": "They need ground. You read atmospheres.",
        "variations": [
            "Your impressions can become their language.",
            "Clarity and sensing aren't opposites.",
        ],
    },
    ("action_taker", "absorber"): {
        "core": "You do. They hold the doing.",
        "variations": [
            "Your action lands at depth.",
            "Leave room between actions.",
        ],
    },
    ("absorber", "action_taker"): {
        "core": "They generate. You transform.",
        "variations": [
            "Their motion gives you material.",
            "Some things pass through.",
        ],
    },
    ("container", "porous"): {
        "core": "You hold edges. They blur edges.",
        "variations": [
            "Structure meets permeability.",
            "Your steadiness gives them ground.",
        ],
    },
    ("porous", "container"): {
        "core": "They model edges. You model flow.",
        "variations": [
            "Their structure gives you something to push against.",
            "Boundaries aren't disconnection.",
        ],
    },
    # Same-type pairs (when both are same type)
    ("initiator", "initiator"): {
        "core": "Two starters. Nothing to catch.",
        "variations": [
            "Both reaching. Neither landing.",
            "Competition for the opening.",
        ],
    },
    ("reflector", "reflector"): {
        "core": "Two mirrors. Waiting for the first move.",
        "variations": [
            "Depth without motion.",
            "Who starts?",
        ],
    },
    ("momentum_carrier", "momentum_carrier"): {
        "core": "Force meets force.",
        "variations": [
            "Fast together. Aware of nothing.",
            "Who calibrates?",
        ],
    },
    ("attunement_holder", "attunement_holder"): {
        "core": "Both sensing. Neither moving.",
        "variations": [
            "The room stays read. Nothing changes.",
            "Someone needs to act.",
        ],
    },
    ("expresser", "expresser"): {
        "core": "Two surfaces. No depth to land in.",
        "variations": [
            "Both showing. Neither holding.",
            "Who receives?",
        ],
    },
    ("absorber", "absorber"): {
        "core": "Two interiors. Nothing reaching the surface.",
        "variations": [
            "Depth without visibility.",
            "Someone needs to show something.",
        ],
    },
}

# -----------------------------------------------------------------------------
# PATTERN LOOP LANGUAGE (Only when recurrence is detected)
# -----------------------------------------------------------------------------

PATTERN_LOOP_PHRASES = [
    "Again.",
    "Same loop. Different face.",
    "This keeps showing up.",
    "You've met this before.",
    "Here it is again.",
]

# -----------------------------------------------------------------------------
# INTERRUPT MOMENTS (Only when pattern is active)
# -----------------------------------------------------------------------------

INTERRUPT_PHRASES = [
    "Pause here.",
    "Before you respond, stop.",
    "This is the moment to do something different.",
    "Right here. Different choice.",
    "Notice what you're about to do.",
]


def generate_identity_meaning(
    user_type: str,
    recurrence_detected: bool = False,
) -> str:
    """
    Generate STABLE identity-level meaning.
    
    Principles:
    - Core truth is ALWAYS the same
    - Phrasing has minimal variation (same truth, tight band)
    - Pattern loop language only when recurrence is actually detected
    - NO random activation
    """
    truth = IDENTITY_CORE_TRUTHS.get(user_type, IDENTITY_CORE_TRUTHS["initiator"])
    
    # Build stable output
    lines = []
    
    # Add pattern loop recognition only if recurrence is detected
    if recurrence_detected:
        lines.append("Same loop. Different face.")
    
    # Core expanded truth (stable)
    lines.append(truth["expanded"])
    
    # Core lesson (stable)
    lines.append(truth["lesson"])
    
    return "\n".join(lines)


def generate_relational_meaning(
    user_type: str,
    other_type: str,
    seed_hash: int,
    pattern_active: bool = False,
    recurrence_count: int = 0,
) -> str:
    """
    Generate 1:1 relational meaning with ANCHORED variation.
    
    Principles:
    - Core truth is stable (always the same for this pair)
    - ONE variation line allowed (anchored to same truth)
    - Pattern loop only if recurrence is real (count > 0)
    - Interrupt only if pattern is currently active
    - NO random activation
    """
    # Get pair key
    pair_key = (user_type, other_type)
    reversed_key = (other_type, user_type)
    
    truth = RELATIONAL_CORE_TRUTHS.get(pair_key)
    if not truth:
        truth = RELATIONAL_CORE_TRUTHS.get(reversed_key)
    if not truth:
        # Fallback
        truth = {
            "core": "You shape each other differently.",
            "variations": ["There's a reason you're here."],
        }
    
    lines = []
    
    # Pattern loop recognition - only if recurrence is real
    if recurrence_count >= 2:
        lines.append("Again.")
    elif recurrence_count == 1:
        lines.append("You've met this before.")
    
    # Core truth (ALWAYS present, stable)
    lines.append(truth["core"])
    
    # ONE variation (anchored - selected by seed for consistency)
    variation_idx = seed_hash % len(truth["variations"])
    lines.append(truth["variations"][variation_idx])
    
    # Interrupt moment - only if pattern is currently active
    if pattern_active:
        interrupt_idx = seed_hash % len(INTERRUPT_PHRASES)
        lines.append(INTERRUPT_PHRASES[interrupt_idx])
    
    return "\n".join(lines)


def detect_pattern_recurrence(
    db_user: dict,
    other_name: str,
    user_type: str,
) -> tuple:
    """
    Detect if this relational pattern has appeared before.
    
    Returns:
    - recurrence_count: How many times this pattern has been encountered
    - pattern_active: Whether the pattern is currently active/escalating
    
    For now, returns baseline values. Can be enhanced with:
    - Journal analysis
    - Previous relationship insight requests
    - Reflection patterns
    """
    # TODO: Implement real recurrence detection from:
    # 1. Journal entries mentioning similar dynamics
    # 2. Previous relationship insight requests
    # 3. Pattern memory from reflections
    
    # For now, return conservative baseline
    # This ensures NO false positives on recurrence/activation
    return 0, False


# =============================================================================
# DEEP DYNAMIC LAYER (V2.0)
# =============================================================================
# These are the deeper relational dynamics that go beyond surface patterns

DEEP_DYNAMICS = {
    # Initiation vs Reflection
    "initiator": {
        "essence": [
            "They start things. Ideas, conversations, decisions — they move first.",
            "They don't wait to be invited. They create the opening.",
            "Energy originates with them. They set things in motion.",
        ],
        "quality": "initiation",
    },
    "reflector": {
        "essence": [
            "They respond to what's already there. They don't originate — they deepen.",
            "They take in before they put out. Their insight comes after contact.",
            "They mirror back what others can't see in themselves.",
        ],
        "quality": "reflection",
    },
    
    # Momentum vs Attunement
    "momentum_carrier": {
        "essence": [
            "They carry energy forward. Stopping costs them.",
            "They build by moving. Hesitation breaks their flow.",
            "Their clarity comes from doing, not waiting.",
        ],
        "quality": "momentum",
    },
    "attunement_holder": {
        "essence": [
            "They feel the room before they speak. They read what isn't said.",
            "Their timing comes from sensing, not deciding.",
            "They adjust to what's present. That's their intelligence.",
        ],
        "quality": "attunement",
    },
    
    # Certainty vs Sensing
    "certainty_seeker": {
        "essence": [
            "They need to know before they move. Ambiguity stalls them.",
            "They trust what's clear. Vagueness feels dangerous.",
            "Their confidence comes from knowing where they stand.",
        ],
        "quality": "certainty",
    },
    "sensor": {
        "essence": [
            "They trust what they feel before they understand it.",
            "Clarity comes last for them. Sensing comes first.",
            "They know things before they can explain them.",
        ],
        "quality": "sensing",
    },
    
    # Expression vs Absorption
    "expresser": {
        "essence": [
            "What they feel, they show. It's not a choice.",
            "They process by externalizing. Silence is pressure.",
            "Their inner world is visible. That's both gift and exposure.",
        ],
        "quality": "expression",
    },
    "absorber": {
        "essence": [
            "They take in more than they put out. That's how they learn.",
            "Their interior is larger than their exterior shows.",
            "What you see is not all of what they're holding.",
        ],
        "quality": "absorption",
    },
    
    # Action vs Atmospheric Reading
    "action_taker": {
        "essence": [
            "They move. That's their answer to most questions.",
            "Thinking without doing doesn't feel real to them.",
            "Their knowing comes after their doing, not before.",
        ],
        "quality": "action",
    },
    "atmospheric_reader": {
        "essence": [
            "They read the room before they act. The field tells them what to do.",
            "They sense what's appropriate before they decide what they want.",
            "Their intelligence is environmental. Context matters more than conviction.",
        ],
        "quality": "atmospheric reading",
    },
    
    # Containment vs Porosity
    "container": {
        "essence": [
            "They hold what they feel. It stays inside until they choose to release it.",
            "Their boundaries are clear. You know where they end.",
            "What's theirs stays theirs. That's protection, not coldness.",
        ],
        "quality": "containment",
    },
    "porous": {
        "essence": [
            "They feel what's around them. Others' emotions enter easily.",
            "Boundaries are harder for them. Not weakness — porosity.",
            "They carry what isn't theirs. Sometimes without knowing.",
        ],
        "quality": "porosity",
    },
}

# =============================================================================
# DEEP FRICTION PATTERNS
# =============================================================================

DEEP_FRICTION = {
    ("initiator", "reflector"): {
        "friction": "You start things. They respond to things.\nYour energy asks for movement. Theirs asks for contact first.",
        "tension": "You reach. They wait. You reach again.\nYour initiation can feel like demand. Their reflection can feel like absence.",
        "your_shift": "Let your initiation land before you add to it.\nGive them something to respond to — then stop.\nTheir reflection needs stillness, not more input.",
        "gift": "They show you what your forward motion obscures.\nWhat you start, they complete — if you let them.",
        "why_this_connection": "You create openings. They deepen what enters.\nWithout you, nothing would start. Without them, nothing would land.\nYou're learning that reaching isn't enough — it has to land somewhere.",
        "try_this": "Initiate once. Then wait. Count to five before adding anything.",
    },
    ("reflector", "initiator"): {
        "friction": "They start things. You respond to things.\nTheir speed can feel like pressure. Your pace can feel like hesitation.",
        "tension": "They move. You need a moment. They move again.\nYour reflection gets crowded by their next idea.",
        "your_shift": "Speak before you've fully formed it.\nYour response doesn't need to be complete to be valuable.\nLet them see you working, not just the result.",
        "gift": "They pull things out of you that wouldn't emerge alone.\nTheir initiation is a prompt — not a demand.",
        "why_this_connection": "They bring motion. You bring depth.\nWithout them, you'd stay in your interior. Without you, they'd stay on the surface.\nYou're learning that responding is also a form of action.",
        "try_this": "Say: 'I'm still landing this. Here's my first thought.'",
    },
    
    ("momentum_carrier", "attunement_holder"): {
        "friction": "You build by moving. They build by sensing.\nYour forward motion can miss what they're reading.",
        "tension": "You push. They attune. You push harder.\nWhat feels like responsiveness to you feels like overwhelm to them.",
        "your_shift": "Your momentum is real. So is their attunement.\nSlowing doesn't break your flow — it deepens it.\nLet their sensing catch up. It's seeing something you missed.",
        "gift": "They slow you down enough to notice what speed hides.\nTheir attunement catches what your momentum would miss.",
        "why_this_connection": "You bring force. They bring calibration.\nWithout you, things wouldn't move. Without them, movement wouldn't land right.\nYou're learning that power includes knowing when to pause.",
        "try_this": "Before your next move, ask: 'What are you sensing here?'",
    },
    ("attunement_holder", "momentum_carrier"): {
        "friction": "They carry energy. You read energy.\nYour pace feels slow to them. Their speed feels rough to you.",
        "tension": "They move. You adjust. They're already somewhere else.\nYour attunement loses its object.",
        "your_shift": "Their momentum isn't carelessness. It's their way of knowing.\nMatch some of it without abandoning your sensing.\nYou can attune while moving.",
        "gift": "They bring force to what you feel.\nYour sensing shapes their momentum into something smarter.",
        "why_this_connection": "They move things forward. You make sure it's the right direction.\nWithout them, you'd sense forever. Without you, they'd move blind.\nYou're learning that sensing can happen while moving.",
        "try_this": "Move with them once before pausing to sense.",
    },
    
    ("certainty_seeker", "sensor"): {
        "friction": "You need to know. They need to feel.\nYour questions can feel like interrogation. Their vagueness can feel like avoidance.",
        "tension": "You ask for clarity. They offer impressions.\nYour certainty seeks ground. Their sensing stays fluid.",
        "your_shift": "Not everything can be known before it's lived.\nTheir sensing isn't weakness — it's a different way of reading.\nLet some things stay unresolved longer.",
        "gift": "They see around corners you haven't reached yet.\nTheir sensing notices what your certainty would filter out.",
        "why_this_connection": "You anchor things. They perceive what anchors can't hold.\nWithout you, everything stays vague. Without them, you miss what logic can't reach.\nYou're learning that some truths arrive before words.",
        "try_this": "Instead of 'What do you think?' ask 'What are you picking up on?'",
    },
    ("sensor", "certainty_seeker"): {
        "friction": "They need to know. You need to feel.\nTheir directness can flatten your subtlety.",
        "tension": "They ask questions. You give impressions.\nThey want a clear answer. You have a felt sense.",
        "your_shift": "Give them something concrete to hold.\nYour sensing doesn't need to be vague when you share it.\nName one thing you're certain about — even if the rest is still forming.",
        "gift": "They ground what you sense into something usable.\nYour impressions become actionable through them.",
        "why_this_connection": "They give form to what you feel. You give texture to what they know.\nWithout them, your sensing stays private. Without you, their knowing stays flat.\nYou're learning that impressions can become language.",
        "try_this": "Offer one concrete thing: 'I don't have the whole picture, but I'm certain about this.'",
    },
    
    ("expresser", "absorber"): {
        "friction": "You show what you feel. They hold what they feel.\nYour visibility can feel like exposure to them.",
        "tension": "You reach out. They take in.\nYour expression meets a depth you can't see the bottom of.",
        "your_shift": "Your expression is a gift. But it can feel like demand.\nShow without needing matching.\nWhat they hold is larger than what they show.",
        "gift": "They receive what you give in a way most people can't.\nYour expression lands somewhere real.",
        "why_this_connection": "You make the invisible visible. They hold what visibility can't contain.\nWithout you, nothing would surface. Without them, nothing would be truly received.\nYou're learning that being seen isn't the same as being matched.",
        "try_this": "Share something without asking for response. Say: 'You don't need to reply.'",
    },
    ("absorber", "expresser"): {
        "friction": "They show what they feel. You hold what you feel.\nTheir expression can feel like a lot coming at you.",
        "tension": "They reach. You take in. They wonder if you're there.\nWhat you're holding doesn't reach the surface.",
        "your_shift": "Let something small surface.\nThey're not asking for everything — just something.\nYour small expressions mean more to them than your silence.",
        "gift": "They draw out what you wouldn't express alone.\nTheir visibility invites yours.",
        "why_this_connection": "They model expression. You model depth.\nWithout them, you'd stay hidden. Without you, they'd have no landing place.\nYou're learning that surfacing doesn't mean emptying.",
        "try_this": "Name one feeling you're holding. Just one.",
    },
    
    ("action_taker", "atmospheric_reader"): {
        "friction": "You move. They read the room.\nYour action can feel abrupt. Their reading can feel stalled.",
        "tension": "You act. They sense. You've already changed the room they were reading.\nYour doing can override what they're perceiving.",
        "your_shift": "Your action is real. So is the field they're reading.\nLet them sense before you move.\nWhat they see might change what you do.",
        "gift": "They read what your action creates — and tell you what you can't see.\nTheir perception completes your motion.",
        "why_this_connection": "You change the room. They read what the room becomes.\nWithout you, nothing would change. Without them, you wouldn't know what you changed.\nYou're learning that action has consequences you can't see alone.",
        "try_this": "Before acting, ask: 'What's the room saying?'",
    },
    ("atmospheric_reader", "action_taker"): {
        "friction": "They move. You read.\nTheir action can disturb what you're sensing.",
        "tension": "They act. You're still reading. The field has already changed.\nYour sense of timing doesn't match their sense of readiness.",
        "your_shift": "Let some of their action in before you assess it.\nYour reading can include their movement, not just resist it.\nSometimes the action clarifies what reading couldn't.",
        "gift": "They bring motion to what you perceive.\nYour atmospheric reading shapes where their action lands.",
        "why_this_connection": "They create change. You perceive what change creates.\nWithout them, you'd read a static room. Without you, they'd act without awareness.\nYou're learning that perception can follow action, not just precede it.",
        "try_this": "Let them act once. Read the result. Then share what you see.",
    },
    
    # Cross-type dynamics (initiator + attunement, momentum + sensing, etc.)
    ("initiator", "attunement_holder"): {
        "friction": "You start things. They feel into things.\nYour forward motion meets their environmental reading.",
        "tension": "You move. They sense. You've already moved again.\nWhat you initiate, they're still metabolizing.",
        "your_shift": "Slow your initiations. Let one land fully.\nTheir attunement isn't hesitation — it's a different kind of intelligence.\nGive them the room to sense what you've started.",
        "gift": "They catch what your initiation misses.\nYour starting becomes smarter when it includes their sensing.",
        "why_this_connection": "You create openings. They feel whether they're the right ones.\nWithout you, nothing would start. Without them, starts wouldn't be calibrated.\nYou're learning that starting well includes sensing the field.",
        "try_this": "Start something. Then ask: 'What are you sensing here?' Wait for the full answer.",
    },
    ("attunement_holder", "initiator"): {
        "friction": "They start things. You feel into things.\nTheir energy can overwhelm your sensing.",
        "tension": "They initiate. You attune. They've initiated again.\nYour tempo doesn't match their pace.",
        "your_shift": "Let their initiation land without immediately attuning to it.\nYou can respond without first having fully sensed.\nSometimes action teaches what attunement can't.",
        "gift": "They pull you into motion before you've finished reading.\nThat forward energy shows you what you wouldn't have moved toward alone.",
        "why_this_connection": "They bring motion. You bring awareness of what motion creates.\nWithout them, you'd sense without moving. Without you, they'd move without sensing.\nYou're learning that you can attune and move at the same time.",
        "try_this": "Say yes to one thing before you've fully felt into it. See what happens.",
    },
    
    ("momentum_carrier", "sensor"): {
        "friction": "You carry energy forward. They feel before they move.\nYour momentum can outrun their knowing.",
        "tension": "You build through doing. They trust impressions.\nYour motion can drown out what they're sensing.",
        "your_shift": "Your momentum is real. But it's not the only signal.\nPause mid-motion to ask what they're picking up.\nTheir sensing sees around corners you haven't reached.",
        "gift": "They sense what's coming before you get there.\nYour momentum lands better when it includes their feeling.",
        "why_this_connection": "You bring force. They bring foresight.\nWithout you, nothing would build. Without them, you'd build toward the wrong thing.\nYou're learning that feeling can guide momentum.",
        "try_this": "Mid-action, pause and ask: 'What are you picking up on here?'",
    },
    ("sensor", "momentum_carrier"): {
        "friction": "They carry energy forward. You feel before you move.\nTheir pace can feel like too much, too fast.",
        "tension": "They build. You sense. The gap widens.\nWhat you're feeling gets lost in their forward motion.",
        "your_shift": "Let your sensing inform their momentum without stopping it.\nSpeak your impressions while they're moving.\nYour input doesn't require their pause.",
        "gift": "Your sensing gives their momentum direction.\nTogether, you move with both force and feeling.",
        "why_this_connection": "They carry energy. You give it shape.\nWithout them, your sensing stays still. Without you, their energy has no direction.\nYou're learning that sensing can happen in motion.",
        "try_this": "Share one impression while they're still moving. Don't wait until they stop.",
    },
    
    ("expresser", "container"): {
        "friction": "You show what you feel. They hold what they feel.\nYour expression can feel like demand. Their containment can feel like rejection.",
        "tension": "You reach. They hold. You wonder what's there.\nWhat you give isn't matched in kind. That's not coldness — it's their structure.",
        "your_shift": "Your expression is generous. But it needs less return.\nShow without requiring them to show back.\nTheir containment isn't a wall — it's just how they're built.",
        "gift": "They receive what you give without flooding.\nYour expression lands somewhere stable.",
        "why_this_connection": "You show what's happening. They hold what's precious.\nWithout you, nothing would surface. Without them, everything would scatter.\nYou're learning that stability can receive without reflecting.",
        "try_this": "Express something without asking for response. End with: 'You don't have to reply.'",
    },
    ("container", "expresser"): {
        "friction": "They show what they feel. You hold what you feel.\nTheir openness can feel like a lot. Your reserve can confuse them.",
        "tension": "They share. You take it in. They wonder if you're there.\nWhat they give seems to disappear into your holding.",
        "your_shift": "Give them something small. A signal that you're receiving.\nYour containment is protection — but they need to see past it.\nOne small opening changes everything.",
        "gift": "They draw out what you hold.\nYour small expressions mean more because they're rare.",
        "why_this_connection": "They model visibility. You model steadiness.\nWithout them, you'd stay unseen. Without you, they'd have no anchor.\nYou're learning that opening doesn't mean flooding.",
        "try_this": "Name one thing you're holding that relates to what they just shared.",
    },
    
    ("certainty_seeker", "attunement_holder"): {
        "friction": "You need to know. They need to feel the room.\nYour questions can interrupt their sensing.",
        "tension": "You ask for clarity. They're reading the field.\nDifferent intelligences, different timings.",
        "your_shift": "Your certainty isn't wrong. But it's not the only way to know.\nLet them sense without requiring translation into facts.\nSometimes the feeling is the answer.",
        "gift": "They bring information your questions can't reach.\nTheir sensing completes your knowing.",
        "why_this_connection": "You seek ground. They read the field.\nWithout you, nothing would be named. Without them, you'd miss what can't be named.\nYou're learning that some knowing arrives through feeling.",
        "try_this": "Instead of asking 'What do you think?', ask 'What's the feeling here?'",
    },
    ("attunement_holder", "certainty_seeker"): {
        "friction": "They need to know. You need to feel the room.\nTheir directness can flatten your nuance.",
        "tension": "They ask. You sense. Your answers don't satisfy their questions.\nYou speak in impressions. They want facts.",
        "your_shift": "Give them one certainty to hold. Even if the rest is still forming.\nYour sensing doesn't have to stay vague when you share it.\nMeet their clarity need without abandoning your own way of knowing.",
        "gift": "They ground what you sense into something usable.\nYour impressions become actionable through their structure.",
        "why_this_connection": "They need named things. You perceive unnamed things.\nWithout them, your sensing stays formless. Without you, their knowing stays incomplete.\nYou're learning that impressions can become language without losing their essence.",
        "try_this": "Start with: 'Here's one thing I'm certain about.' Then add the sensing.",
    },
    
    ("action_taker", "absorber"): {
        "friction": "You move. They take in.\nYour action can overwhelm their absorption.",
        "tension": "You do. They hold. You've done more before they've processed the first thing.\nYour doing fills the space they need.",
        "your_shift": "Leave room between actions.\nWhat you do lands deeper when there's space around it.\nTheir absorption isn't passivity — it's how they learn.",
        "gift": "They take in your action at a depth you can't see.\nWhat you do matters more because of how they receive it.",
        "why_this_connection": "You create impact. They register impact.\nWithout you, there would be nothing to absorb. Without them, your actions would vanish unwitnessed.\nYou're learning that impact needs space to land.",
        "try_this": "Do one thing. Then leave space. Ask: 'What are you holding from that?'",
    },
    ("absorber", "action_taker"): {
        "friction": "They move. You take in.\nTheir doing can outpace your absorption.",
        "tension": "They act. You're still processing. The actions accumulate.\nYou're holding more than you can show.",
        "your_shift": "Let some of what they do pass through without holding it.\nYou don't have to absorb everything.\nSurface what you're holding before it becomes too much.",
        "gift": "Their action gives you something to work with.\nYour absorption transforms what they do into something deeper.",
        "why_this_connection": "They generate material. You transform it.\nWithout them, you'd have nothing to process. Without you, their actions wouldn't gain depth.\nYou're learning that you can choose what to hold and what to release.",
        "try_this": "Before you've fully processed, say: 'Here's what I'm holding so far.'",
    },
    
    ("container", "porous"): {
        "friction": "You hold your edges. They feel everything.\nYour containment can feel like withholding. Their porosity can feel like flooding.",
        "tension": "You keep what's yours. They take in what's not theirs.\nYour boundaries protect you. Their openness absorbs.",
        "your_shift": "Your containment isn't coldness. But it can read that way.\nOffer a door, not a wall.\nThey can't enter what you don't open.",
        "gift": "They bring feeling into spaces you've protected.\nTheir porosity softens your edges without breaking them.",
        "why_this_connection": "You hold edges. They blur edges.\nWithout you, they'd have no structure. Without them, you'd have no permeability.\nYou're learning that edges can have doors.",
        "try_this": "Name one thing you're holding that they haven't seen.",
    },
    ("porous", "container"): {
        "friction": "They hold their edges. You feel everything.\nYou absorb what they contain. That imbalance can tire you.",
        "tension": "You feel them. They hold themselves.\nWhat you're carrying may not be theirs to feel back.",
        "your_shift": "Their containment isn't rejection. It's how they're built.\nYou don't have to hold everything they don't show.\nCreate some edge of your own. Just a little.",
        "gift": "They provide structure when your edges blur.\nTheir containment gives you something to push against.",
        "why_this_connection": "They model edges. You model permeability.\nWithout them, you'd have no boundaries. Without you, they'd have no flow.\nYou're learning that you can feel without absorbing.",
        "try_this": "Notice what you're carrying that isn't yours. Put one thing down.",
    },
}

# =============================================================================
# TYPE DETECTION (V2.0 - Deeper)
# =============================================================================

def detect_deep_type(profile_data: Dict[str, Any], context: str = "") -> str:
    """Detect user's deep dynamic type from profile and context."""
    
    # From Enneagram (more nuanced mapping)
    enneagram = profile_data.get("enneagram", {})
    enneagram_type = enneagram.get("type")
    
    enneagram_deep_map = {
        1: "certainty_seeker",    # Needs to know what's right
        2: "porous",              # Absorbs others' needs
        3: "momentum_carrier",    # Builds through doing
        4: "absorber",            # Takes in deeply
        5: "atmospheric_reader",  # Reads the field
        6: "certainty_seeker",    # Needs ground
        7: "initiator",           # Starts things
        8: "action_taker",        # Moves first
        9: "attunement_holder",   # Senses the room
    }
    
    # Context overrides
    context_lower = context.lower()
    
    if any(w in context_lower for w in ["starts things", "initiates", "leads", "begins"]):
        return "initiator"
    if any(w in context_lower for w in ["responds", "reflects", "mirrors", "deepens"]):
        return "reflector"
    if any(w in context_lower for w in ["moves forward", "momentum", "keeps going", "doesn't stop"]):
        return "momentum_carrier"
    if any(w in context_lower for w in ["feels the room", "senses", "attunes", "adjusts"]):
        return "attunement_holder"
    if any(w in context_lower for w in ["needs to know", "certain", "clear", "direct"]):
        return "certainty_seeker"
    if any(w in context_lower for w in ["feels", "senses", "impressions", "intuitive"]):
        return "sensor"
    if any(w in context_lower for w in ["expressive", "shows feelings", "visible", "open"]):
        return "expresser"
    if any(w in context_lower for w in ["takes in", "absorbs", "holds", "quiet"]):
        return "absorber"
    if any(w in context_lower for w in ["acts", "does", "moves", "action"]):
        return "action_taker"
    if any(w in context_lower for w in ["reads the room", "atmospheric", "sensitive to environment"]):
        return "atmospheric_reader"
    if any(w in context_lower for w in ["contained", "boundaried", "holds back", "protected"]):
        return "container"
    if any(w in context_lower for w in ["porous", "absorbs emotions", "feels others", "no boundaries"]):
        return "porous"
    
    # Fall back to enneagram
    if enneagram_type:
        return enneagram_deep_map.get(enneagram_type, "initiator")
    
    return "initiator"


def get_complementary_type(user_type: str) -> str:
    """Get the complementary/contrasting type for interesting dynamics."""
    complements = {
        "initiator": "reflector",
        "reflector": "initiator",
        "momentum_carrier": "attunement_holder",
        "attunement_holder": "momentum_carrier",
        "certainty_seeker": "sensor",
        "sensor": "certainty_seeker",
        "expresser": "absorber",
        "absorber": "expresser",
        "action_taker": "atmospheric_reader",
        "atmospheric_reader": "action_taker",
        "container": "porous",
        "porous": "container",
    }
    return complements.get(user_type, "reflector")


# =============================================================================
# MAIN GENERATOR V2.0
# =============================================================================

def generate_relationship_insight(
    user_profile: Dict[str, Any],
    other_profile: Optional[Dict[str, Any]] = None,
    other_name: str = "them",
    relationship_type: str = "relationship",
    relationship_context: str = "",
    seed: str = ""
) -> Dict[str, Any]:
    """
    V2.0: Generate a 1:1 relationship insight with deeper dynamics.
    
    Centered on USER, not the other person.
    Helps user understand what's happening and what to shift.
    """
    
    # Generate seed for deterministic output
    if not seed:
        seed = f"{user_profile.get('user_id', '')}:{other_name}:{datetime.now().strftime('%Y-%m-%d')}"
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    
    # Detect deep types
    user_type = detect_deep_type(user_profile, "")  # User's own type
    other_type = detect_deep_type(other_profile or {}, relationship_context)  # Other's type from context
    
    # If no context, use complementary type for interesting dynamic
    if not relationship_context and not other_profile:
        other_type = get_complementary_type(user_type)
    
    dynamic_pair = (user_type, other_type)
    
    # Get deep dynamic content
    deep_content = DEEP_FRICTION.get(dynamic_pair)
    
    if not deep_content:
        # Try reversed pair
        reversed_pair = (other_type, user_type)
        deep_content = DEEP_FRICTION.get(reversed_pair)
        
        if deep_content:
            # We found the reversed pair - need to flip perspective
            dynamic_pair = reversed_pair
    
    # If still no match, try to find closest match by qualities
    if not deep_content:
        # Map types to broad categories for fallback matching
        initiation_types = ["initiator", "action_taker", "momentum_carrier", "expresser"]
        reflection_types = ["reflector", "atmospheric_reader", "attunement_holder", "absorber", "sensor"]
        certainty_types = ["certainty_seeker", "container"]
        fluid_types = ["porous", "sensor", "attunement_holder"]
        
        # Determine fallback pair
        user_is_initiating = user_type in initiation_types
        other_is_reflecting = other_type in reflection_types
        
        if user_is_initiating and other_is_reflecting:
            dynamic_pair = ("initiator", "reflector")
        elif not user_is_initiating and not other_is_reflecting:
            dynamic_pair = ("reflector", "initiator")
        else:
            dynamic_pair = ("initiator", "reflector")
        
        deep_content = DEEP_FRICTION[dynamic_pair]
    
    # Get essence
    other_deep = DEEP_DYNAMICS.get(other_type, DEEP_DYNAMICS["reflector"])
    essence_options = other_deep["essence"]
    essence = essence_options[seed_hash % len(essence_options)]
    
    return {
        "success": True,
        "version": "v3.0",
        "other_name": other_name,
        "relationship_type": relationship_type,
        
        # The 7-section structure (WHY THIS CONNECTION now STABLE with anchored variation)
        "essence": essence,
        "friction": deep_content["friction"],
        "tension": deep_content["tension"],
        "your_shift": deep_content["your_shift"],
        "gift": deep_content["gift"],
        "why_this_connection": generate_relational_meaning(
            user_type=user_type,
            other_type=other_type,
            seed_hash=seed_hash,
            pattern_active=False,  # TODO: detect from journal/history
            recurrence_count=0,    # TODO: detect from journal/history
        ),
        "try_this": deep_content["try_this"],
        
        # Metadata
        "dynamic": {
            "user_type": user_type,
            "other_type": other_type,
            "user_quality": DEEP_DYNAMICS.get(user_type, {}).get("quality", "unknown"),
            "other_quality": DEEP_DYNAMICS.get(other_type, {}).get("quality", "unknown"),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# GENERAL RELATIONSHIP PATTERN (IDENTITY-LEVEL)
# =============================================================================
# This generates the user's general way of showing up in ALL relationships.
# Not about specific people - about their relational identity.

IDENTITY_PATTERNS = {
    "initiator": {
        "core_pattern": "You start things. In relationships, you're the one who reaches first.\nYou don't wait for invitations — you create openings.\nThis is how you connect: by moving toward.",
        "default_tension": "Your initiation can feel like demand when it isn't received.\nYou reach. Silence. You reach again.\nThe gap between your offer and their response is where you struggle.",
        "growth_edge": "Let your reaching land before you add to it.\nNot every silence is rejection. Some people need time to meet your energy.\nYour shift: Initiate once, then wait.",
        "gift": "You make connection happen.\nWithout you, things stay still. People who can't start things need you.\nYour forward motion creates openings others can't.",
        "what_teaching": "You keep meeting people who don't match your speed.\nThis isn't random. You're learning that connection isn't just about reaching — it's about landing.\nThe ones who make you wait are teaching you that your energy needs space to be received.",
        "try_this": "Next time you reach out: wait twice as long as feels comfortable before reaching again.",
    },
    "reflector": {
        "core_pattern": "You respond to what's already there. You don't originate — you deepen.\nIn relationships, you mirror back what others can't see.\nThis is how you connect: by receiving first.",
        "default_tension": "Your reflection can feel like hesitation to people who move fast.\nThey reach. You need a moment. They wonder if you're there.\nThe gap between their offer and your response is where friction lives.",
        "growth_edge": "Speak before you've fully formed it.\nYour response doesn't need to be complete to be valuable.\nYour shift: Show your process, not just your result.",
        "gift": "You see what others miss about themselves.\nYour reflection is a mirror they can't find alone.\nWhat you give back is often clearer than what they sent.",
        "what_teaching": "You keep attracting people who want more than you're showing.\nThis isn't random. You're learning that your interior needs to reach the surface sometimes.\nThe ones who push you to respond are teaching you that presence isn't passive.",
        "try_this": "Say 'I'm still landing this — here's my first thought' instead of waiting until you're ready.",
    },
    "momentum_carrier": {
        "core_pattern": "You carry energy forward. In relationships, you build through doing.\nStopping costs you. Hesitation breaks your flow.\nThis is how you connect: by moving together.",
        "default_tension": "Your momentum can outpace people who need to feel before they move.\nYou're building. They're sensing. The gap widens.\nWhat feels like responsiveness to you can feel like pressure to them.",
        "growth_edge": "Slowing doesn't break your flow — it deepens it.\nSome people need to sense what's happening before they can join.\nYour shift: Pause mid-motion to check in.",
        "gift": "You bring force to what matters.\nPeople who struggle to move need your momentum.\nYour energy makes things happen that wouldn't happen otherwise.",
        "what_teaching": "You keep meeting people who slow you down.\nThis isn't random. You're learning that force without awareness misses things.\nThe ones who can't match your pace are teaching you that momentum includes pausing.",
        "try_this": "Mid-action, pause and ask: 'Are you with me?' Then actually wait for the answer.",
    },
    "attunement_holder": {
        "core_pattern": "You feel the room before you speak. In relationships, you read what isn't said.\nYour timing comes from sensing, not deciding.\nThis is how you connect: by adjusting to what's present.",
        "default_tension": "Your attunement can feel like hesitation to people who move fast.\nThey act. You're still sensing. They've moved again.\nYour tempo doesn't match their speed.",
        "growth_edge": "You can attune while moving.\nMatching some momentum doesn't mean abandoning your sensing.\nYour shift: Move with them once before pausing to sense.",
        "gift": "You catch what speed misses.\nPeople who move fast need someone who reads the field.\nYour sensing prevents collisions they don't see coming.",
        "what_teaching": "You keep attracting people who move faster than you sense.\nThis isn't random. You're learning that your attunement can happen in motion.\nThe ones who don't wait are teaching you that reading the room includes moving through it.",
        "try_this": "Say yes to one thing before you've fully felt into it. See what happens.",
    },
    "certainty_seeker": {
        "core_pattern": "You need to know before you move. In relationships, ambiguity stalls you.\nYou trust what's clear. Vagueness feels dangerous.\nThis is how you connect: through clarity and ground.",
        "default_tension": "Your questions can feel like interrogation to people who work by feeling.\nYou ask for clarity. They offer impressions.\nYour need for ground meets their fluidity.",
        "growth_edge": "Not everything can be known before it's lived.\nSome people's vagueness isn't avoidance — it's how they know.\nYour shift: Let some things stay unresolved longer.",
        "gift": "You bring structure to what's formless.\nPeople who float need someone who names things clearly.\nYour certainty creates ground others can stand on.",
        "what_teaching": "You keep meeting people who can't give you straight answers.\nThis isn't random. You're learning that clarity isn't the only form of truth.\nThe ones who speak in impressions are teaching you that some knowing can't be pinned down.",
        "try_this": "Instead of 'What do you think?' ask 'What are you picking up on?' — and accept the vague answer.",
    },
    "sensor": {
        "core_pattern": "You trust what you feel before you understand it.\nIn relationships, clarity comes last. Sensing comes first.\nThis is how you connect: by picking up on what's unsaid.",
        "default_tension": "Your impressions can feel like evasion to people who need facts.\nThey ask questions. You give impressions.\nYour felt sense doesn't translate into their language.",
        "growth_edge": "Give them something concrete to hold.\nYour sensing doesn't have to be vague when you share it.\nYour shift: Name one thing you're certain about — even if the rest is forming.",
        "gift": "You see around corners others haven't reached.\nPeople who only trust facts miss what you perceive.\nYour sensing notices what logic would filter out.",
        "what_teaching": "You keep meeting people who want you to be more concrete.\nThis isn't random. You're learning that impressions can become language.\nThe ones who ask for facts are teaching you that your sensing can be shared without losing its truth.",
        "try_this": "Offer one concrete thing: 'I don't have the whole picture, but I'm certain about this.'",
    },
    "expresser": {
        "core_pattern": "What you feel, you show. In relationships, it's not a choice.\nYou process by externalizing. Silence is pressure.\nThis is how you connect: by making your inner world visible.",
        "default_tension": "Your expression can feel like demand to people who hold more inside.\nYou reach out. They take in.\nYour visibility meets their depth — and wonders what's there.",
        "growth_edge": "Show without needing matching.\nNot everyone processes out loud. Their silence isn't rejection.\nYour shift: Express without requiring equal expression back.",
        "gift": "You make the invisible visible.\nPeople who can't name their feelings learn from watching you.\nYour openness gives permission to others.",
        "what_teaching": "You keep meeting people who don't show as much as you do.\nThis isn't random. You're learning that expression can land without being matched.\nThe ones who stay quiet are teaching you that reception is different from reflection.",
        "try_this": "Share something and end with: 'You don't need to reply.' Mean it.",
    },
    "absorber": {
        "core_pattern": "You take in more than you put out. In relationships, that's how you learn.\nYour interior is larger than your exterior shows.\nThis is how you connect: by receiving deeply.",
        "default_tension": "Your silence can feel like absence to people who need feedback.\nThey share. You take it in. They wonder if you're there.\nWhat you're holding doesn't reach the surface.",
        "growth_edge": "Let something small surface.\nThey're not asking for everything — just something.\nYour shift: Your small expressions mean more because they're rare.",
        "gift": "You receive at a depth most people can't.\nPeople who express need someone who actually takes it in.\nWhat you hold transforms over time into something valuable.",
        "what_teaching": "You keep meeting people who want more from you than silence.\nThis isn't random. You're learning that what you hold can reach the surface without emptying.\nThe ones who ask if you're there are teaching you that small signals matter.",
        "try_this": "Name one feeling you're holding. Just one. Out loud.",
    },
    "action_taker": {
        "core_pattern": "You move. In relationships, that's your answer to most questions.\nThinking without doing doesn't feel real to you.\nThis is how you connect: by doing things together.",
        "default_tension": "Your action can feel abrupt to people who need to feel first.\nYou act. They're still reading. The room has already changed.\nYour doing can override what they're perceiving.",
        "growth_edge": "Let them sense before you move.\nWhat they see might change what you do.\nYour shift: Ask 'What's the room saying?' before acting.",
        "gift": "You make things happen.\nPeople who get stuck in sensing need your motion.\nYour action clarifies what thinking couldn't.",
        "what_teaching": "You keep meeting people who want you to slow down.\nThis isn't random. You're learning that action without awareness misses what's happening.\nThe ones who read the room are teaching you that the field has information too.",
        "try_this": "Before your next move, ask: 'What are you sensing here?' Wait for the full answer.",
    },
    "atmospheric_reader": {
        "core_pattern": "You read the room before you act. In relationships, the field tells you what to do.\nYou sense what's appropriate before you decide what you want.\nThis is how you connect: through environmental intelligence.",
        "default_tension": "Your reading can feel like stalling to people who move fast.\nThey act. You're still reading. The field has already changed.\nYour sense of timing doesn't match their readiness.",
        "growth_edge": "Let some action in before you assess it.\nYour reading can include movement, not just resist it.\nYour shift: Sometimes action clarifies what reading couldn't.",
        "gift": "You see what action creates.\nPeople who move fast need someone who reads the impact.\nYour perception prevents unintended consequences.",
        "what_teaching": "You keep meeting people who move before you've finished reading.\nThis isn't random. You're learning that reading can happen in motion.\nThe ones who act fast are teaching you that the room keeps changing anyway.",
        "try_this": "Let them act once. Read the result. Then share what you see.",
    },
    "container": {
        "core_pattern": "You hold what you feel. In relationships, it stays inside until you choose.\nYour boundaries are clear. You know where you end.\nThis is how you connect: by protecting what's precious.",
        "default_tension": "Your containment can feel like withholding to people who share openly.\nThey reach. You hold. They wonder what's there.\nYour protection can read as coldness.",
        "growth_edge": "Offer a door, not a wall.\nThey can't enter what you don't open.\nYour shift: Name one thing you're holding that they haven't seen.",
        "gift": "You provide structure when others flood.\nPeople with no edges need your containment.\nYour steadiness is a form of safety.",
        "what_teaching": "You keep meeting people who want inside what you're protecting.\nThis isn't random. You're learning that your edges can have doors.\nThe ones who reach toward you are teaching you that opening isn't the same as flooding.",
        "try_this": "Share one thing from inside before they ask. Proactively.",
    },
    "porous": {
        "core_pattern": "You feel what's around you. In relationships, others' emotions enter easily.\nBoundaries are harder for you. Not weakness — porosity.\nThis is how you connect: by feeling what others feel.",
        "default_tension": "You absorb what isn't yours. That can tire you.\nThey contain themselves. You feel them anyway.\nWhat you're carrying may not be theirs to feel back.",
        "growth_edge": "Create some edge of your own. Just a little.\nYou don't have to hold everything you feel.\nYour shift: Notice what you're carrying that isn't yours. Put one thing down.",
        "gift": "You feel what others hide from themselves.\nPeople who can't access their feelings need your perception.\nYour porosity brings hidden things to light.",
        "what_teaching": "You keep meeting people who have clearer edges than you do.\nThis isn't random. You're learning that boundaries don't mean disconnection.\nThe ones who hold themselves are teaching you that you can feel without absorbing.",
        "try_this": "At the end of each conversation, ask yourself: 'What am I carrying that isn't mine?'",
    },
}


def generate_relationship_pattern(
    user_profile: Dict[str, Any],
    seed: str = ""
) -> Dict[str, Any]:
    """
    Generate user's general relationship pattern (identity-level).
    
    This is NOT about specific people.
    This is about HOW THE USER SHOWS UP in relationships.
    
    Output:
    - Core Pattern: How they show up
    - Default Tension: Their typical friction point
    - Growth Edge: What to shift (Your Shift equivalent)
    - Gift: What they bring
    - What Teaching: What relationships are teaching (STABLE)
    - Try This: One actionable suggestion
    """
    
    # Use STABLE seed (user_id only, NOT date-based)
    # This ensures the identity-level meaning stays consistent
    if not seed:
        seed = f"{user_profile.get('user_id', '')}:identity"
    
    # Detect user's deep type
    user_type = detect_deep_type(user_profile, "")
    
    # Get identity pattern
    pattern = IDENTITY_PATTERNS.get(user_type, IDENTITY_PATTERNS["initiator"])
    
    return {
        "success": True,
        "version": "v3.0",
        "pattern_type": user_type,
        "pattern_quality": DEEP_DYNAMICS.get(user_type, {}).get("quality", "unknown"),
        
        # The 6-section structure for identity-level (what_teaching now STABLE)
        "core_pattern": pattern["core_pattern"],
        "default_tension": pattern["default_tension"],
        "growth_edge": pattern["growth_edge"],
        "gift": pattern["gift"],
        "what_teaching": generate_identity_meaning(
            user_type=user_type,
            recurrence_detected=False,  # TODO: detect from journal/history
        ),
        "try_this": pattern["try_this"],
        
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_relationship_pattern(
    db,
    user_id: str
) -> Dict[str, Any]:
    """
    Get user's general relationship pattern from database profile.
    """
    try:
        # Get user profile
        user = await db.users.find_one({"_id": user_id})
        user_profile = {
            "user_id": user_id,
            "enneagram": user.get("enneagram", {}) if user else {},
            "astrology": user.get("astrology", {}) if user else {},
        }
        
        return generate_relationship_pattern(user_profile=user_profile)
        
    except Exception as e:
        logger.error(f"[RelationshipPattern] Error: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# API HELPERS
# =============================================================================

async def get_relationship_insight(
    db,
    user_id: str,
    other_user_id: Optional[str] = None,
    other_name: str = "them",
    relationship_type: str = "relationship",
    relationship_context: str = ""
) -> Dict[str, Any]:
    """
    Get relationship insight from database profiles.
    """
    try:
        # Get user profile
        user = await db.users.find_one({"_id": user_id})
        user_profile = {
            "user_id": user_id,
            "enneagram": user.get("enneagram", {}) if user else {},
            "astrology": user.get("astrology", {}) if user else {},
        }
        
        # Get other profile if available
        other_profile = None
        if other_user_id:
            other = await db.users.find_one({"_id": other_user_id})
            if other:
                other_profile = {
                    "user_id": other_user_id,
                    "enneagram": other.get("enneagram", {}),
                    "astrology": other.get("astrology", {}),
                }
        
        return generate_relationship_insight(
            user_profile=user_profile,
            other_profile=other_profile,
            other_name=other_name,
            relationship_type=relationship_type,
            relationship_context=relationship_context,
        )
        
    except Exception as e:
        logger.error(f"[RelationshipInsight] Error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
