"""
Master Astrologer Content V1.0
==============================

VOICE: Authoritative, specific, consequential
NOT: Vague, ambient, mood-wallpaper

PRINCIPLE: Every output should feel like a real astrologer making a grounded judgment.
User reads and says: "That's exactly what's happening."
NOT: "That's an interesting observation."

RULES:
1. Name the actual tension, not generic discomfort
2. State the consequence of action/inaction
3. Be specific about WHERE this shows up in life
4. Avoid: "something is off", "you've been here before", "low-grade discomfort"
5. Prefer: Named patterns, behavioral truth, real-life consequences
"""

import logging
from typing import Dict, List, Optional
import random

logger = logging.getLogger(__name__)


# =============================================================================
# AUTHORITATIVE HOME TITLES - Specific, Named, Consequential
# =============================================================================

AUTHORITATIVE_HOME_TITLES = {
    # DECISION TENSION
    "decision_known": [
        "You already know the decision. You don't trust the cost.",
        "The answer is clear. The willingness isn't.",
        "You're not confused. You're negotiating with the obvious.",
        "The decision is made. You're just not saying it out loud yet.",
    ],
    
    # MOVEMENT TENSION
    "movement_resistance": [
        "You want movement, but not the version of you it requires.",
        "You're not stuck. You're resisting the next visible step.",
        "The path is clear. You're avoiding what walking it means.",
        "Motion is available. You're protecting something by staying still.",
    ],
    
    # IDENTITY PRESSURE
    "identity_pressure": [
        "You're being pushed to act before your identity feels settled.",
        "The pressure isn't just emotional. It's directional.",
        "Something is asking you to be the person you're not sure you are yet.",
        "The demand is for a version of you that doesn't fully exist yet.",
    ],
    
    # COMPETING WANTS
    "competing_wants": [
        "Part of you wants relief. Another part wants expansion. Those are not the same move.",
        "Two things you want are incompatible right now. That's the tension.",
        "You're trying to hold two positions that don't fit in the same hand.",
        "The conflict isn't external. It's between two versions of what you want.",
    ],
    
    # WAITING TENSION
    "waiting_tension": [
        "The wait isn't neutral. It's doing something to you.",
        "You're not patient. You're controlled. There's a difference.",
        "The silence isn't empty. It's full of what you're not saying.",
        "Waiting is a choice. You're pretending it isn't.",
    ],
    
    # AVOIDANCE
    "avoidance_pattern": [
        "You're busy, but not with the thing that actually matters.",
        "The urgency you feel is real. The target is wrong.",
        "You're solving the wrong problem on purpose.",
        "Activity without direction is just sophisticated hiding.",
    ],
    
    # RELATIONSHIP TENSION
    "relationship_tension": [
        "Someone needs something you're not sure you can give.",
        "The conversation you're avoiding is louder than the one you're having.",
        "What you're not saying is running the dynamic.",
        "You're managing someone else's feelings at the cost of your own clarity.",
    ],
    
    # PRESSURE TO PERFORM
    "performance_pressure": [
        "The audience you're performing for isn't in the room.",
        "You're meeting expectations that no one actually set.",
        "The standard you're failing is one you invented.",
        "You're working for approval that won't satisfy even if it comes.",
    ],
    
    # ENERGY MISMATCH
    "energy_mismatch": [
        "Your body knows something your mind is still arguing with.",
        "The fatigue isn't physical. It's directional.",
        "You have energy. It's just refusing to go where you're pointing it.",
        "The exhaustion is selective. Notice what still has access to you.",
    ],
    
    # SELF-DOUBT LOOP
    "self_doubt_loop": [
        "You keep asking for permission you don't actually need.",
        "The doubt isn't about the decision. It's about trusting yourself to handle what comes next.",
        "You're looking for certainty in a situation that doesn't offer it.",
        "The questioning is a way to avoid acting. You already know this.",
    ],
}


# =============================================================================
# AUTHORITATIVE HOME BODIES - Specific consequences, not vague moods
# =============================================================================

AUTHORITATIVE_HOME_BODIES = {
    "decision_known": [
        "The discomfort isn't confusion—it's the weight of what saying yes actually costs. You're not gathering information. You're negotiating with something you've already decided.",
        "You've run the analysis enough times. What's left isn't clarity, it's commitment. The gap isn't knowledge. It's willingness to be changed by the choice.",
        "The hesitation feels like wisdom, but it's protection. You know what's right. You're just not sure you want to be the person who has to follow through.",
    ],
    
    "movement_resistance": [
        "The stuck feeling isn't about options—it's about what moving forward requires you to release. You're not blocked. You're holding position.",
        "There's motion available that you're not taking. Not because you can't see it, but because taking it means becoming someone new. That's the actual resistance.",
        "You're calling it timing, but it's actually willingness. The path exists. The question is whether you're ready to walk it as yourself.",
    ],
    
    "identity_pressure": [
        "The pressure you're feeling isn't circumstantial—it's developmental. Something is demanding you act from a position you haven't fully grown into yet.",
        "You're being asked to operate as a version of yourself that's still forming. The discomfort isn't weakness. It's the edge of who you're becoming.",
        "This moment is asking for more than you think you have. That's by design. The gap between who you are and who this requires is the actual work.",
    ],
    
    "competing_wants": [
        "The tension isn't a problem to solve—it's information about what you actually value. Two genuine desires are competing. Only one can be chosen right now.",
        "You're trying to architect a solution that honors both. But this moment is asking you to choose. The discomfort is the choice you haven't made yet.",
        "What you want for yourself and what you want from the situation are different things. Until you name that, you'll keep feeling split.",
    ],
    
    "waiting_tension": [
        "The waiting feels passive, but it's not. You're holding a position that takes energy. The question is whether you're waiting wisely or just avoiding the next move.",
        "Time isn't neutral here. Every day in this position changes what the options mean. You're not preserving choice. You're letting it change shape.",
        "The wait has a cost you're pretending not to see. You're not patient. You're just not ready to face what acting means.",
    ],
    
    "avoidance_pattern": [
        "The productivity is real, but it's pointed at the wrong thing. You're not lazy. You're strategically busy in a way that protects you from the thing that actually matters.",
        "There's a conversation, a decision, or an action you're circling without touching. Everything else is distraction with a purpose.",
        "You keep finding important things to do. The question is whether any of them are the important thing you're avoiding.",
    ],
}


# =============================================================================
# AUTHORITATIVE ASTROLOGY SYNTHESIS - Master astrologer voice
# =============================================================================

MASTER_ASTROLOGER_SYNTHESIS = {
    "today": {
        "frame": "What is being activated RIGHT NOW",
        "voice_examples": [
            "This transit isn't asking for your understanding—it's asking for your response.",
            "The pressure today is directional, not just emotional. Something wants to move.",
            "Today's energy rewards motion over rumination, but only if the motion is honest.",
            "The friction isn't random—it's exposing the part of the strategy that no longer holds.",
        ],
        "consequence_patterns": [
            "If you move with this: {positive_outcome}",
            "If you resist this: {friction_outcome}",
            "The opportunity here is: {opportunity}",
            "The trap to avoid is: {trap}",
        ],
    },
    "week": {
        "frame": "What keeps RETURNING across these days",
        "voice_examples": [
            "The same tension keeps finding you. That's not coincidence—it's curriculum.",
            "You'll notice this theme surfacing in different costumes. The pattern is the point.",
            "This week is teaching through repetition. The question is whether you're learning.",
            "The same choice keeps presenting itself. Your response is becoming your answer.",
        ],
        "consequence_patterns": [
            "Each time it returns, it's asking: {recurring_question}",
            "The pattern is showing you: {pattern_revelation}",
            "By week's end, you'll know: {week_outcome}",
            "The repetition is trying to: {repetition_purpose}",
        ],
    },
    "month": {
        "frame": "What larger arc is being reorganized",
        "voice_examples": [
            "This month is restructuring something you thought was settled.",
            "The developments this month aren't random—they're connected by what's being dismantled and rebuilt.",
            "You're in a chapter transition. The discomfort is the page turning.",
            "What's being asked of you this month is different from what was asked last month. That's the point.",
        ],
        "consequence_patterns": [
            "By month's end: {month_transformation}",
            "What's being stripped away: {being_removed}",
            "What's being clarified: {being_clarified}",
            "The developmental demand is: {developmental_demand}",
        ],
    },
}


# =============================================================================
# HORIZON-SPECIFIC INTERPRETATION JOBS
# =============================================================================

HORIZON_INTERPRETATION_JOBS = {
    "today": {
        "primary_question": "What kind of day is this?",
        "secondary_question": "What is active and demanding response?",
        "focus": "Immediate lived texture—body, emotions, reactions",
        "language_markers": ["today", "right now", "this moment", "immediately"],
        "avoid": ["this week", "over time", "eventually", "this month"],
    },
    "week": {
        "primary_question": "What keeps showing up?",
        "secondary_question": "What pattern is maturing or becoming visible?",
        "focus": "Recurring dynamics across days—buildup, peak, aftermath",
        "language_markers": ["keeps returning", "showing up again", "the same tension", "repeated"],
        "avoid": ["today", "right now", "this month", "this phase"],
    },
    "month": {
        "primary_question": "What is this month teaching or reorganizing?",
        "secondary_question": "What larger arc is this part of?",
        "focus": "Identity-level shifts—what's being dismantled and rebuilt",
        "language_markers": ["this month", "this phase", "the arc", "chapter", "being restructured"],
        "avoid": ["today", "right now", "this week", "immediately"],
    },
}


# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def get_authoritative_home_title(pattern_key: str, seed_hash: int = 0) -> str:
    """Get a specific, authoritative home title for a pattern."""
    titles = AUTHORITATIVE_HOME_TITLES.get(pattern_key)
    if not titles:
        # Fallback to decision_known as default
        titles = AUTHORITATIVE_HOME_TITLES.get("decision_known", ["Something is asking for your attention."])
    return titles[seed_hash % len(titles)]


def get_authoritative_home_body(pattern_key: str, seed_hash: int = 0) -> str:
    """Get a specific, consequential home body for a pattern."""
    bodies = AUTHORITATIVE_HOME_BODIES.get(pattern_key)
    if not bodies:
        bodies = AUTHORITATIVE_HOME_BODIES.get("decision_known", ["The tension has a specific shape. Name it."])
    return bodies[seed_hash % len(bodies)]


def get_master_synthesis_voice(timeframe: str, seed_hash: int = 0) -> str:
    """Get master astrologer voice for a timeframe."""
    horizon = MASTER_ASTROLOGER_SYNTHESIS.get(timeframe, MASTER_ASTROLOGER_SYNTHESIS["today"])
    voices = horizon.get("voice_examples", [])
    if not voices:
        return "This transit is asking for your attention."
    return voices[seed_hash % len(voices)]


def get_horizon_job(timeframe: str) -> Dict:
    """Get the interpretive job for a horizon."""
    return HORIZON_INTERPRETATION_JOBS.get(timeframe, HORIZON_INTERPRETATION_JOBS["today"])


def generate_authoritative_theme(
    pattern_key: str,
    timeframe: str = "today",
    context_data: Optional[Dict] = None,
    seed_hash: int = 0,
) -> Dict[str, str]:
    """
    Generate a complete authoritative theme package.
    
    Returns:
        {
            "title": "...",
            "body": "...",
            "synthesis_voice": "...",
            "horizon_frame": "...",
        }
    """
    return {
        "title": get_authoritative_home_title(pattern_key, seed_hash),
        "body": get_authoritative_home_body(pattern_key, seed_hash),
        "synthesis_voice": get_master_synthesis_voice(timeframe, seed_hash),
        "horizon_frame": get_horizon_job(timeframe).get("primary_question", ""),
    }


# =============================================================================
# PATTERN DETECTION MAPPING
# =============================================================================

SIGNAL_TO_PATTERN_MAP = {
    # Decision signals
    "already_know": "decision_known",
    "obvious_choice": "decision_known",
    "clear_but_scary": "decision_known",
    
    # Movement signals
    "stuck": "movement_resistance",
    "blocked": "movement_resistance",
    "can't_move": "movement_resistance",
    "frozen": "movement_resistance",
    
    # Identity signals
    "not_ready": "identity_pressure",
    "not_sure_who": "identity_pressure",
    "becoming": "identity_pressure",
    "growing_into": "identity_pressure",
    
    # Competing wants
    "want_both": "competing_wants",
    "torn": "competing_wants",
    "conflict": "competing_wants",
    
    # Waiting
    "waiting": "waiting_tension",
    "patience": "waiting_tension",
    "holding": "waiting_tension",
    
    # Avoidance
    "busy_but": "avoidance_pattern",
    "productive_but": "avoidance_pattern",
    "avoiding": "avoidance_pattern",
    
    # Relationship
    "someone_needs": "relationship_tension",
    "dynamic": "relationship_tension",
    "managing": "relationship_tension",
    
    # Performance
    "expectations": "performance_pressure",
    "standards": "performance_pressure",
    "performing": "performance_pressure",
    
    # Energy
    "tired_but": "energy_mismatch",
    "drained": "energy_mismatch",
    "exhausted": "energy_mismatch",
    
    # Self-doubt
    "permission": "self_doubt_loop",
    "validation": "self_doubt_loop",
    "certainty": "self_doubt_loop",
}


def detect_pattern_from_signals(signals: List[str]) -> str:
    """Detect the most relevant pattern from a list of signals."""
    pattern_scores = {}
    
    for signal in signals:
        signal_lower = signal.lower()
        for keyword, pattern in SIGNAL_TO_PATTERN_MAP.items():
            if keyword in signal_lower:
                pattern_scores[pattern] = pattern_scores.get(pattern, 0) + 1
    
    if not pattern_scores:
        return "decision_known"  # Default to decision tension
    
    # Return highest scoring pattern
    return max(pattern_scores, key=pattern_scores.get)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "AUTHORITATIVE_HOME_TITLES",
    "AUTHORITATIVE_HOME_BODIES",
    "MASTER_ASTROLOGER_SYNTHESIS",
    "HORIZON_INTERPRETATION_JOBS",
    "get_authoritative_home_title",
    "get_authoritative_home_body",
    "get_master_synthesis_voice",
    "get_horizon_job",
    "generate_authoritative_theme",
    "detect_pattern_from_signals",
]
