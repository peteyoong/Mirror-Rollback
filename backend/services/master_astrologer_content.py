"""
Master Astrologer Content V2.0 — Genuine Horizon Separation
============================================================

CORE RULE: If you remove the labels, a reader should STILL correctly
identify which output is Today, Week, or Month.

TODAY = immediate, in-body, situational, present-tense pressure
WEEK = recurring dynamic, multi-day pattern, building momentum  
MONTH = chapter-level arc, identity reorganization, deeper/slower

DO NOT just prepend "today..." / "this week..." / "this month..."
The STRUCTURE and ALTITUDE of the sentence must be different.
"""

import logging
from typing import Dict, List, Optional
import random

logger = logging.getLogger(__name__)


# =============================================================================
# TODAY: IMMEDIATE LIVED TENSION
# =============================================================================
# Voice: Short, direct, situational, in-body
# Feels like: "Right now. This moment. This pressure."
# Test: Should sound like something you'd notice in the next hour

TODAY_THEMES = {
    "identity_pressure": [
        "The ask right now is bigger than you feel ready for.",
        "You're being called to act from a position you haven't fully claimed.",
        "There's a gap between what's expected and what you feel capable of. That gap is today's work.",
        "Something wants your answer before you've finished forming it.",
    ],
    "decision_known": [
        "You already know. The hesitation is about cost, not clarity.",
        "The choice is clear. The willingness isn't.",
        "Stop researching. The answer is already there.",
        "You're stalling on something you've already decided.",
    ],
    "movement_resistance": [
        "The path is visible. You're not taking it.",
        "There's motion available that you're refusing.",
        "You're calling it timing. It's actually fear.",
        "Something could move right now. You're holding it still.",
    ],
    "competing_wants": [
        "Two things you want are colliding today.",
        "You can't have both right now. That's the tension.",
        "The split you feel isn't confusion—it's incompatibility.",
        "Part of you wants ease. Part wants growth. Pick one for today.",
    ],
    "waiting_tension": [
        "The waiting is active, not passive. Feel what it's doing to you.",
        "You're holding a position that costs energy.",
        "Patience is a choice. Notice whether you're choosing it.",
        "The silence isn't empty. It's full of what you're not saying.",
    ],
    "avoidance_pattern": [
        "You're productive in the wrong direction.",
        "The urgency is real. The target is off.",
        "Notice what you're doing instead of the thing.",
        "Busy is a hiding strategy. What are you avoiding?",
    ],
    "relationship_tension": [
        "Someone needs something you're not sure you can give.",
        "There's a conversation you're circling.",
        "What you're not saying is louder than what you are.",
        "You're managing their reaction instead of speaking your truth.",
    ],
    "performance_pressure": [
        "You're performing for an audience that isn't watching.",
        "The standard you're failing is one you invented.",
        "Who are you trying to impress right now? Name them.",
        "The effort is real. The approval won't satisfy.",
    ],
    "energy_mismatch": [
        "Your body knows something your mind is arguing with.",
        "The tiredness is specific. Notice where it points.",
        "You have energy. It's refusing to go where you're directing it.",
        "The resistance is information. What is it protecting?",
    ],
    "self_doubt_loop": [
        "You're asking permission you don't need.",
        "The doubt is a delay tactic. You know this.",
        "Stop polling. Start moving.",
        "The questioning is avoiding the doing.",
    ],
}

TODAY_BODIES = {
    "identity_pressure": [
        "The pressure you're feeling right now isn't circumstantial—it's developmental. This moment is asking for a version of you that's still forming. The discomfort is the gap between who you are and who this requires.",
        "Something in the next few hours will ask you to show up as someone you're not sure you've become yet. That's not a problem. That's the edge.",
    ],
    "decision_known": [
        "The information gathering is complete. What's left isn't analysis—it's commitment. The gap between knowing and acting is where you're living right now.",
        "You've already made the decision. You're just not saying it out loud. Today is about closing the gap between private knowing and public action.",
    ],
    "movement_resistance": [
        "There's a move available that you're pretending doesn't exist. The stuckness is manufactured. Today is about admitting what you already see.",
        "Motion is possible. You're protecting something by staying still. Name what you're protecting.",
    ],
}


# =============================================================================
# THIS WEEK: RECURRING DYNAMIC
# =============================================================================
# Voice: Pattern recognition across days, building momentum, escalating
# Feels like: "This keeps happening. You've seen this before this week."
# Test: Should reference multiple occurrences, pattern visibility

WEEK_THEMES = {
    "identity_pressure": [
        "The same demand keeps finding you in different forms.",
        "You've noticed this ask showing up multiple times now. It's not random.",
        "The pattern this week: being pushed toward something before you feel ready.",
        "Several moments this week have asked the same thing. The consistency is the message.",
    ],
    "decision_known": [
        "The same decision keeps presenting itself. Your non-answer is becoming your answer.",
        "You've circled this choice multiple times now. The circling is visible.",
        "Every detour this week has led back to the same fork. Notice that.",
        "The decision you're avoiding is getting louder with each pass.",
    ],
    "movement_resistance": [
        "The same stuck point keeps appearing in different contexts.",
        "You've hit this wall before this week. It's not the circumstances—it's the pattern.",
        "Multiple situations have asked you to move. You've declined each time.",
        "The resistance is consistent. That consistency is trying to tell you something.",
    ],
    "competing_wants": [
        "The same split has shown up in different costumes this week.",
        "You keep choosing between the same two things. Neither wins for long.",
        "The tension between these two wants is maturing into something you can't ignore.",
        "Every version of this week's dilemma has the same underlying structure.",
    ],
    "waiting_tension": [
        "The waiting has extended across days now. Feel its cumulative weight.",
        "You've been holding this position all week. Notice what that's cost you.",
        "The patience you thought was temporary is becoming a stance.",
        "Multiple days of holding still. The stillness is no longer neutral.",
    ],
    "avoidance_pattern": [
        "You've been productively avoiding the same thing for days.",
        "The real task has been waiting while you completed everything else.",
        "Your week has been shaped by what you're not doing.",
        "The avoidance has become architectural. It's organizing your days now.",
    ],
    "relationship_tension": [
        "The same conversation has been waiting at the edge of multiple interactions.",
        "You've navigated around this person all week. The navigation is exhausting.",
        "The dynamic keeps recreating itself in different moments.",
        "What you're managing with them has become a full-time position.",
    ],
}

WEEK_BODIES = {
    "identity_pressure": [
        "This pressure has shown up in at least three different forms this week. The packaging changes, but the developmental demand stays the same. You're being asked to grow into something faster than feels comfortable.",
        "The week has been organized around a single question you haven't fully answered: can you be the person this situation requires? The repetition is trying to make the question unavoidable.",
    ],
    "decision_known": [
        "The same choice has presented itself in multiple costumes this week. Each time you've found a reason to wait. The reasons are running out. The choice remains.",
        "You've spent days circling something you already know. The circling has become its own activity—a way of staying near the decision without making it.",
    ],
}


# =============================================================================
# THIS MONTH: CHAPTER-LEVEL ARC
# =============================================================================
# Voice: Deeper, slower, identity-level, reorganization
# Feels like: "Something larger is shifting. This month is a chapter."
# Test: Should feel consequential, structural, long-term

MONTH_THEMES = {
    "identity_pressure": [
        "A version of who you've been is becoming unsustainable.",
        "This month is dismantling something you used to rely on.",
        "The ground you've been standing on is shifting. It won't shift back.",
        "Something foundational is being renegotiated. You're inside that process now.",
    ],
    "decision_known": [
        "A long-delayed reckoning is arriving. The delay ends this month.",
        "Something you've been outrunning is catching up. This month is the convergence.",
        "The postponement strategy has reached its limit.",
        "A choice you've been deferring is becoming impossible to defer.",
    ],
    "movement_resistance": [
        "A period of holding still is ending. What comes next requires motion.",
        "The structure that allowed you to stay put is dissolving.",
        "The resistance that used to work is becoming costly. This month shows you the cost.",
        "Something that was stable enough to wait is no longer stable.",
    ],
    "competing_wants": [
        "A fundamental incompatibility is surfacing. It's been underground for longer than you realize.",
        "Two versions of your future are becoming mutually exclusive. This month forces the acknowledgment.",
        "The tension you've been managing is becoming unmanageable. That's the point.",
        "What you want and what you're building are diverging. This month makes that visible.",
    ],
    "waiting_tension": [
        "A season of patience is transforming into a season of consequence.",
        "What you've been waiting for is either arriving or dissolving. Either way, the waiting changes.",
        "The suspended state has run its course. Something is landing this month.",
        "Outcomes you seeded earlier are maturing. This month you see what grew.",
    ],
    "avoidance_pattern": [
        "Something you've structured your life around avoiding is becoming unavoidable.",
        "The architecture of your avoidance is being exposed. This month shows you the blueprint.",
        "What you've been running from is no longer behind you. It's in front of you now.",
        "The detours have led somewhere. This month you see where.",
    ],
    "relationship_tension": [
        "A relational pattern is reaching its natural conclusion. What happens next depends on what you do now.",
        "The dynamic you've been managing is evolving beyond management.",
        "Something unspoken is becoming structural. If it stays unspoken much longer, it becomes permanent.",
        "The relationship is reorganizing itself around what neither of you has said.",
    ],
}

MONTH_BODIES = {
    "identity_pressure": [
        "This month represents a threshold. The person who entered it and the person who exits it won't be quite the same. The pressure you're feeling isn't random stress—it's the friction of transformation. Something is being asked to change at the level of identity, not just behavior.",
        "You're inside a restructuring that won't reverse. The discomfort you're experiencing is appropriate—this is consequential. By month's end, you'll have moved through something, not just past something.",
    ],
    "decision_known": [
        "The choice you've been circling has a time horizon that ends this month. Not because someone is imposing a deadline, but because the conditions that allowed delay are expiring. What you decide—or fail to decide—becomes increasingly permanent.",
        "Something that was optional is becoming mandatory. The window for easy choice is closing. This month, you either choose consciously or the circumstances choose for you.",
    ],
}


# =============================================================================
# MASTER SYNTHESIS VOICE - Expert Astrological Judgment
# =============================================================================

MASTER_SYNTHESIS_TODAY = [
    "This transit pattern is activating the part of you that hasn't fully formed yet.",
    "The pressure today isn't ambient—it's directional. Something specific is being asked.",
    "What's being triggered right now will show up in your decisions within hours.",
    "Today's astrological weather rewards action over analysis, but only honest action.",
    "The current configuration is exposing where your strategy has stopped working.",
    "This is not a day for waiting. The energy is demanding a response.",
]

MASTER_SYNTHESIS_WEEK = [
    "The same transit pattern has been echoing across multiple days. That's not noise—it's emphasis.",
    "This week's astrological structure is designed to make a pattern undeniable.",
    "What keeps surfacing this week is being amplified on purpose. Pay attention to the repetition.",
    "The planetary rhythm this week is teaching through recurrence. The lesson repeats until integrated.",
    "This configuration rewards those who notice what keeps returning. The pattern is the message.",
    "The week's transits are building toward something. Each day adds pressure to the same point.",
]

MASTER_SYNTHESIS_MONTH = [
    "The planetary movements this month are reorganizing something fundamental.",
    "This is not a corrective month—it's a restructuring month. The changes are architectural.",
    "The transits operating this month don't negotiate. They reveal what's actually true.",
    "What's being activated this month operates at the level of identity, not circumstance.",
    "The astrological pressure this month is slow, deep, and consequential. Don't rush the process.",
    "This month's configuration strips away what's no longer viable. What remains is what's real.",
]


# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def get_today_theme(pattern_key: str, seed_hash: int = 0) -> str:
    """Get an immediate, situational, in-body theme for TODAY."""
    themes = TODAY_THEMES.get(pattern_key, TODAY_THEMES.get("identity_pressure"))
    return themes[seed_hash % len(themes)]


def get_week_theme(pattern_key: str, seed_hash: int = 0) -> str:
    """Get a recurring, multi-day pattern theme for THIS WEEK."""
    themes = WEEK_THEMES.get(pattern_key, WEEK_THEMES.get("identity_pressure"))
    return themes[seed_hash % len(themes)]


def get_month_theme(pattern_key: str, seed_hash: int = 0) -> str:
    """Get a chapter-level, reorganization theme for THIS MONTH."""
    themes = MONTH_THEMES.get(pattern_key, MONTH_THEMES.get("identity_pressure"))
    return themes[seed_hash % len(themes)]


def get_today_body(pattern_key: str, seed_hash: int = 0) -> str:
    """Get body copy for TODAY scope."""
    bodies = TODAY_BODIES.get(pattern_key)
    if not bodies:
        bodies = TODAY_BODIES.get("identity_pressure", ["The pressure is immediate and specific."])
    return bodies[seed_hash % len(bodies)]


def get_week_body(pattern_key: str, seed_hash: int = 0) -> str:
    """Get body copy for WEEK scope."""
    bodies = WEEK_BODIES.get(pattern_key)
    if not bodies:
        bodies = WEEK_BODIES.get("identity_pressure", ["The pattern has been building across days."])
    return bodies[seed_hash % len(bodies)]


def get_month_body(pattern_key: str, seed_hash: int = 0) -> str:
    """Get body copy for MONTH scope."""
    bodies = MONTH_BODIES.get(pattern_key)
    if not bodies:
        bodies = MONTH_BODIES.get("identity_pressure", ["Something foundational is being renegotiated."])
    return bodies[seed_hash % len(bodies)]


def get_master_synthesis(timeframe: str, seed_hash: int = 0) -> str:
    """Get expert astrological judgment for a timeframe."""
    if timeframe == "today":
        voices = MASTER_SYNTHESIS_TODAY
    elif timeframe == "week":
        voices = MASTER_SYNTHESIS_WEEK
    else:  # month
        voices = MASTER_SYNTHESIS_MONTH
    return voices[seed_hash % len(voices)]


def get_horizon_theme(timeframe: str, pattern_key: str, seed_hash: int = 0) -> str:
    """Get the theme for a specific horizon."""
    if timeframe == "today":
        return get_today_theme(pattern_key, seed_hash)
    elif timeframe == "week":
        return get_week_theme(pattern_key, seed_hash)
    else:  # month
        return get_month_theme(pattern_key, seed_hash)


def get_horizon_body(timeframe: str, pattern_key: str, seed_hash: int = 0) -> str:
    """Get the body copy for a specific horizon."""
    if timeframe == "today":
        return get_today_body(pattern_key, seed_hash)
    elif timeframe == "week":
        return get_week_body(pattern_key, seed_hash)
    else:  # month
        return get_month_body(pattern_key, seed_hash)


# =============================================================================
# LEGACY COMPATIBILITY ALIASES
# =============================================================================

def get_authoritative_home_title(pattern_key: str, seed_hash: int = 0) -> str:
    """Legacy alias - returns TODAY theme."""
    return get_today_theme(pattern_key, seed_hash)


def get_authoritative_home_body(pattern_key: str, seed_hash: int = 0) -> str:
    """Legacy alias - returns TODAY body."""
    return get_today_body(pattern_key, seed_hash)


def get_master_synthesis_voice(timeframe: str, seed_hash: int = 0) -> str:
    """Legacy alias."""
    return get_master_synthesis(timeframe, seed_hash)


def get_horizon_job(timeframe: str) -> Dict:
    """Get the interpretive job for a horizon."""
    jobs = {
        "today": {
            "primary_question": "What kind of day is this?",
            "focus": "Immediate lived texture—body, emotions, reactions",
        },
        "week": {
            "primary_question": "What keeps showing up?",
            "focus": "Recurring dynamics across days—buildup, peak, visibility",
        },
        "month": {
            "primary_question": "What is being reorganized?",
            "focus": "Identity-level shifts—what's being dismantled and rebuilt",
        },
    }
    return jobs.get(timeframe, jobs["today"])


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TODAY_THEMES",
    "WEEK_THEMES",
    "MONTH_THEMES",
    "get_today_theme",
    "get_week_theme",
    "get_month_theme",
    "get_today_body",
    "get_week_body",
    "get_month_body",
    "get_master_synthesis",
    "get_horizon_theme",
    "get_horizon_body",
    "get_authoritative_home_title",
    "get_authoritative_home_body",
    "get_master_synthesis_voice",
    "get_horizon_job",
]
