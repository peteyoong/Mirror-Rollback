"""
Daily Differentiation Layer for Mirror Home - V2 BEHAVIORAL SPECIFICITY
========================================================================

V1: Daily signal weighting + anti-repetition + freshness injection
V2: BEHAVIORAL IMMEDIACY - Catch user mid-action

UPGRADE FROM V1:
- Replace abstract "why today phrases" with "BEHAVIOR SNAPS"
- Force life arena resolution (almost never null)
- Move behavior to first line
- Tighten language (verbs > nouns, present tense, short lines)

USER REACTION GOAL: "That literally just happened."

USAGE:
    from services.daily_differentiation import (
        compute_daily_signals,
        get_anti_repetition_penalty,
        generate_behavior_snap,
        inject_behavior_first,
        resolve_life_arena_forced,
        PatternCandidate,
        DailySignalProfile,
    )
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# "WHY TODAY" REASONS - What made this pattern win today (internal tracking)
# =============================================================================

class WhyTodayReason(Enum):
    """Internal reason for why this pattern surfaces today."""
    TRANSIT_PRESSURE = "transit_pressure"           # Active transit hitting natal chart
    RECENT_REPETITION = "recent_repetition"         # User keeps coming back to this
    UNRESOLVED_REFLECTION = "unresolved_reflection" # Recent journal shows unfinished business
    DECISION_TENSION = "decision_tension"           # Active choice/commitment pending
    RELATIONAL_FRICTION = "relational_friction"     # Tension with someone
    TIMING_AMPLIFICATION = "timing_amplification"   # BaZi/Astro timing is amplifying
    EXPRESSION_BLOCKED = "expression_blocked"       # Something unsaid
    PATTERN_INTENSIFYING = "pattern_intensifying"   # Same pattern getting louder
    BODY_SIGNAL = "body_signal"                     # Physical/somatic cue
    FINANCIAL_TENSION = "financial_tension"         # Money-related pressure


# =============================================================================
# V2: BEHAVIOR SNAPS - Specific micro-behaviors (replaces abstract phrases)
# =============================================================================
# These feel like Mirror caught user MID-ACTION
# Format: present tense, specific, immediate

BEHAVIOR_SNAPS = {
    WhyTodayReason.TRANSIT_PRESSURE: [
        "you were about to decide — then stopped",
        "you almost moved — then pulled back",
        "you started, then paused",
        "you felt the push — and resisted",
    ],
    WhyTodayReason.RECENT_REPETITION: [
        "you went back to it again",
        "you checked again",
        "you reopened the same thing",
        "you circled back — like you always do",
    ],
    WhyTodayReason.UNRESOLVED_REFLECTION: [
        "you tried to move past it — it stayed",
        "you pushed it down — it came back up",
        "you told yourself it's done — it isn't",
        "you closed it — but you're still thinking about it",
    ],
    WhyTodayReason.DECISION_TENSION: [
        "you were about to choose — then hesitated",
        "you almost picked one — then second-guessed",
        "you started to commit — then backed off",
        "you went to lock it in — then stopped",
    ],
    WhyTodayReason.RELATIONAL_FRICTION: [
        "you almost said it — then didn't",
        "you started typing — then deleted",
        "you rehearsed it in your head — again",
        "you waited for them — they didn't respond",
    ],
    WhyTodayReason.TIMING_AMPLIFICATION: [
        "you felt the pressure rise",
        "you sensed the window closing",
        "you knew you should move — but didn't",
        "you felt the urgency — and ignored it",
    ],
    WhyTodayReason.EXPRESSION_BLOCKED: [
        "you almost sent it",
        "you started to speak — then stopped",
        "you had the words — they didn't come out",
        "you drafted it — then saved it",
    ],
    WhyTodayReason.PATTERN_INTENSIFYING: [
        "you tried the same thing again",
        "you pushed harder — same result",
        "you went back to the same approach",
        "you did it again — knowing it wouldn't work",
    ],
    WhyTodayReason.BODY_SIGNAL: [
        "you felt it in your body — then ignored it",
        "you paused — your body said no",
        "you pushed through — something felt off",
        "you felt the tightness — kept going anyway",
    ],
    WhyTodayReason.FINANCIAL_TENSION: [
        "you almost pulled the trigger — then stopped",
        "you ran the numbers again",
        "you went to pay — then hesitated",
        "you checked the account — again",
    ],
}


# =============================================================================
# V2: LIFE ARENAS - Forced resolution (almost never null)
# =============================================================================

class LifeArena(Enum):
    """Specific life contexts - must resolve to one."""
    DECISION = "decision"                # A choice pending
    MESSAGE = "message"                  # Something to say/send
    FOLLOW_UP = "follow_up"              # Waiting on response
    COMMITMENT = "commitment"            # Locking something in
    INTERNAL_DOUBT = "internal_doubt"    # Self-questioning
    RELATIONSHIP = "relationship"        # Tension with someone
    TIMING = "timing"                    # Waiting for right moment
    EXECUTION = "execution"              # Pushing something through


# Arena detection keywords (expanded for forced resolution)
ARENA_KEYWORDS = {
    LifeArena.DECISION: [
        "decide", "decision", "choose", "choice", "option", "pick", "which",
        "should I", "whether", "or", "between", "either"
    ],
    LifeArena.MESSAGE: [
        "say", "tell", "speak", "message", "text", "call", "email", "send",
        "reply", "respond", "write", "draft"
    ],
    LifeArena.FOLLOW_UP: [
        "wait", "waiting", "response", "reply", "back", "heard", "follow",
        "check", "heard back", "get back", "any word"
    ],
    LifeArena.COMMITMENT: [
        "commit", "promise", "agree", "sign", "lock", "yes", "accept",
        "finalize", "confirm", "book", "schedule"
    ],
    LifeArena.INTERNAL_DOUBT: [
        "doubt", "sure", "unsure", "question", "wonder", "thinking",
        "feel like", "maybe", "probably", "not sure"
    ],
    LifeArena.RELATIONSHIP: [
        "they", "them", "partner", "friend", "boss", "colleague", "family",
        "relationship", "between us", "with them", "told me", "said"
    ],
    LifeArena.TIMING: [
        "timing", "when", "now", "later", "soon", "ready", "wait",
        "too early", "too late", "right time", "not yet"
    ],
    LifeArena.EXECUTION: [
        "do", "doing", "push", "move", "start", "finish", "complete",
        "execute", "make happen", "get done", "action"
    ],
}


# Arena behavior openers (first line of Home based on arena)
ARENA_BEHAVIOR_OPENERS = {
    LifeArena.DECISION: [
        "You were about to decide — then stopped.",
        "You almost chose — then pulled back.",
        "You went to lock it in — then hesitated.",
    ],
    LifeArena.MESSAGE: [
        "You almost sent it.",
        "You started typing — then deleted.",
        "You had the words — they didn't come out.",
    ],
    LifeArena.FOLLOW_UP: [
        "You checked again.",
        "You waited — still nothing.",
        "You looked for the response — it wasn't there.",
    ],
    LifeArena.COMMITMENT: [
        "You were about to commit — then backed off.",
        "You almost said yes — then paused.",
        "You went to sign — something stopped you.",
    ],
    LifeArena.INTERNAL_DOUBT: [
        "You questioned yourself again.",
        "You talked yourself out of it — again.",
        "You had the answer — then doubted it.",
    ],
    LifeArena.RELATIONSHIP: [
        "You almost said it to them.",
        "You rehearsed it in your head — again.",
        "You wanted to bring it up — then didn't.",
    ],
    LifeArena.TIMING: [
        "You felt the window — and hesitated.",
        "You knew it was time — but didn't move.",
        "You sensed the pressure — and waited anyway.",
    ],
    LifeArena.EXECUTION: [
        "You pushed — it didn't move.",
        "You tried again — same result.",
        "You went to do it — then stopped.",
    ],
}


# Legacy phrases kept for backward compatibility but deprecated
WHY_TODAY_PHRASES = {
    WhyTodayReason.TRANSIT_PRESSURE: [
        "today this gets louder",
        "the timing is pushing this up",
        "this is more active today",
        "something shifted today",
    ],
    WhyTodayReason.RECENT_REPETITION: [
        "again today",
        "this keeps coming back",
        "you thought this was done",
        "same thing, different day",
    ],
    WhyTodayReason.UNRESOLVED_REFLECTION: [
        "what you wrote about recently",
        "still not resolved",
        "the thing that won't settle",
        "what keeps surfacing",
    ],
    WhyTodayReason.DECISION_TENSION: [
        "the decision that's waiting",
        "what you haven't closed",
        "still sitting there",
        "the thing you keep circling",
    ],
    WhyTodayReason.RELATIONAL_FRICTION: [
        "something between you and them",
        "the dynamic that's off",
        "what you're not saying",
        "tension that hasn't broken",
    ],
    WhyTodayReason.TIMING_AMPLIFICATION: [
        "this is tighter today",
        "the timing is amplifying this",
        "harder to ignore today",
        "today it's more insistent",
    ],
    WhyTodayReason.EXPRESSION_BLOCKED: [
        "what you've almost said",
        "the thing in your throat",
        "what keeps getting edited",
        "what you're holding back",
    ],
    WhyTodayReason.PATTERN_INTENSIFYING: [
        "this is getting stronger",
        "harder to push past today",
        "what you could push through yesterday is sticking today",
        "the pattern is tightening",
    ],
    WhyTodayReason.BODY_SIGNAL: [
        "your body knows",
        "the tension you're carrying",
        "what you felt this morning",
        "the signal you keep ignoring",
    ],
    WhyTodayReason.FINANCIAL_TENSION: [
        "the money thing",
        "what you're weighing",
        "the cost you're calculating",
        "the investment on your mind",
    ],
}


# =============================================================================
# DAILY SIGNAL PROFILE
# =============================================================================

@dataclass
class DailySignalProfile:
    """
    Weighted signals that change DAY to DAY.
    These should dominate over stable constitution signals.
    """
    
    # SHORT-TERM SIGNALS (24-72h) - HIGH WEIGHT
    transit_pressure_today: float = 0.0      # Active transits right now
    journal_recency: float = 0.0             # How recent the journal activity
    last_72h_pattern_count: int = 0          # Pattern appearances in 72h
    unresolved_recent_loop: float = 0.0      # Unresolved recent issues
    
    # TIMING SIGNALS - HIGH WEIGHT
    bazi_day_pressure: float = 0.0           # BaZi day pressure
    lunar_phase_pressure: float = 0.0        # Moon phase intensity
    
    # RELATIONAL/CONTEXT SIGNALS - MEDIUM WEIGHT
    decision_pending: float = 0.0            # Active decision in play
    relational_friction: float = 0.0         # People tension
    financial_tension: float = 0.0           # Money tension
    body_signal: float = 0.0                 # Physical/somatic
    
    # STATIC SIGNALS (reduced weight)
    hd_structure: float = 0.0                # HD type/authority (stable)
    natal_baseline: float = 0.0              # Birth chart constants (stable)
    
    # Computed
    why_today: Optional[WhyTodayReason] = None
    why_today_phrase: Optional[str] = None
    daily_intensity: float = 0.0             # 0-1, how "today" this is


@dataclass
class PatternCandidate:
    """A pattern being considered for Home."""
    pattern_id: str
    pattern_family: str
    pattern_title: str
    
    # Scoring
    base_score: float = 0.0                  # From live signal profile
    daily_boost: float = 0.0                 # Daily signal boost
    anti_repetition_penalty: float = 0.0     # Penalty for recent appearances
    final_score: float = 0.0                 # After all adjustments
    
    # "Why Today" tracking
    why_today_reason: Optional[WhyTodayReason] = None
    why_today_phrase: Optional[str] = None
    daily_signals_contributing: List[str] = field(default_factory=list)
    
    # Recurrence tracking
    times_shown_72h: int = 0
    times_shown_7d: int = 0
    last_shown_days_ago: int = 999
    
    # Metadata
    life_arena: Optional[str] = None         # decision/conversation/commitment/etc


# =============================================================================
# COMPUTE DAILY SIGNALS
# =============================================================================

def compute_daily_signals(
    transit_aspects: List[Dict] = None,
    bazi_data: Dict = None,
    journal_entries: List[Dict] = None,
    pattern_history: List[Dict] = None,
    recent_reflections: List[Dict] = None,
) -> DailySignalProfile:
    """
    Compute signals that change DAY to DAY.
    These are weighted MORE heavily than stable constitution.
    """
    profile = DailySignalProfile()
    
    # =================================================================
    # A. TRANSIT PRESSURE (HIGH WEIGHT)
    # =================================================================
    if transit_aspects:
        total_weight = 0.0
        for aspect in transit_aspects:
            weight = aspect.get("weight", 0.5)
            aspect_type = aspect.get("aspect_type", "").lower()
            transit_point = aspect.get("transit_point", "").lower()
            
            # Outer planet transits = more pressure
            if transit_point in ["pluto", "neptune", "uranus", "saturn"]:
                weight *= 1.4
            
            # Hard aspects = more pressure
            if aspect_type in ["square", "opposition", "conjunction"]:
                weight *= 1.3
            
            total_weight += weight
        
        profile.transit_pressure_today = min(1.0, total_weight / 3.0)
        profile.daily_signals_contributing = ["transit_pressure"] if total_weight > 0.5 else []
    
    # =================================================================
    # B. JOURNAL RECENCY (HIGH WEIGHT)
    # =================================================================
    if journal_entries:
        # Check how recent entries are
        now = datetime.now(timezone.utc)
        recent_count = 0
        very_recent_count = 0
        
        for entry in journal_entries:
            created_at = entry.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                
                days_ago = (now - created_at).days
                
                if days_ago <= 1:
                    very_recent_count += 1
                    recent_count += 1
                elif days_ago <= 3:
                    recent_count += 1
        
        if very_recent_count >= 1:
            profile.journal_recency = 0.8
        elif recent_count >= 2:
            profile.journal_recency = 0.5
        elif recent_count >= 1:
            profile.journal_recency = 0.3
        
        # Detect unresolved loops from journal text
        unresolved_keywords = ["still", "again", "keep", "can't stop", "won't leave", "back"]
        unresolved_count = 0
        for entry in journal_entries[:3]:
            content = entry.get("content", "").lower()
            for keyword in unresolved_keywords:
                if keyword in content:
                    unresolved_count += 1
                    break
        
        profile.unresolved_recent_loop = min(1.0, unresolved_count * 0.4)
    
    # =================================================================
    # C. BAZI DAY PRESSURE (HIGH WEIGHT)
    # =================================================================
    if bazi_data:
        day_signals = bazi_data.get("day_signals", {})
        profile.bazi_day_pressure = day_signals.get("pressure", 0.0)
        
        # Clash or punishment days = higher pressure
        if bazi_data.get("day_clash") or bazi_data.get("day_punishment"):
            profile.bazi_day_pressure += 0.3
    
    # =================================================================
    # D. PATTERN RECURRENCE (72h/7d)
    # =================================================================
    if pattern_history:
        count_72h = 0
        count_7d = 0
        
        for p in pattern_history:
            days_ago = p.get("days_ago", 999)
            if days_ago <= 3:
                count_72h += 1
            if days_ago <= 7:
                count_7d += 1
        
        profile.last_72h_pattern_count = count_72h
        
        # Recurrence = pattern intensifying
        if count_72h >= 2:
            profile.unresolved_recent_loop += 0.3
    
    # =================================================================
    # E. DETECT LIFE ARENAS FROM JOURNALS
    # =================================================================
    if journal_entries:
        arena_keywords = {
            "decision": ["decide", "decision", "choose", "choice", "option", "pick"],
            "conversation": ["tell", "say", "talk", "speak", "message", "call"],
            "commitment": ["commit", "promise", "lock", "sign", "agree"],
            "money": ["money", "pay", "cost", "invest", "spend", "salary"],
            "relationship": ["they", "them", "partner", "boss", "friend", "mom", "dad"],
            "body": ["tired", "sick", "pain", "body", "sleep", "energy", "health"],
        }
        
        arena_scores = {k: 0 for k in arena_keywords}
        
        for entry in journal_entries[:5]:
            content = entry.get("content", "").lower()
            for arena, keywords in arena_keywords.items():
                for kw in keywords:
                    if kw in content:
                        arena_scores[arena] += 1
        
        # Set tensions based on detected arenas
        if arena_scores["decision"] >= 2:
            profile.decision_pending = 0.6
        if arena_scores["relationship"] >= 2:
            profile.relational_friction = 0.5
        if arena_scores["money"] >= 1:
            profile.financial_tension = 0.4
        if arena_scores["body"] >= 1:
            profile.body_signal = 0.3
    
    # =================================================================
    # F. COMPUTE DAILY INTENSITY
    # =================================================================
    # Daily signals should dominate (70% weight)
    daily_signals = [
        profile.transit_pressure_today * 1.2,  # Extra weight
        profile.journal_recency * 1.0,
        profile.bazi_day_pressure * 1.0,
        profile.unresolved_recent_loop * 1.0,
    ]
    
    # Static signals (30% weight)
    static_signals = [
        profile.hd_structure * 0.5,
        profile.natal_baseline * 0.5,
    ]
    
    daily_total = sum(daily_signals)
    static_total = sum(static_signals)
    
    profile.daily_intensity = min(1.0, (daily_total * 0.7) + (static_total * 0.3))
    
    # =================================================================
    # G. DETERMINE PRIMARY "WHY TODAY" REASON
    # =================================================================
    reason_scores = [
        (WhyTodayReason.TRANSIT_PRESSURE, profile.transit_pressure_today * 1.2),
        (WhyTodayReason.RECENT_REPETITION, profile.last_72h_pattern_count * 0.3),
        (WhyTodayReason.UNRESOLVED_REFLECTION, profile.unresolved_recent_loop),
        (WhyTodayReason.DECISION_TENSION, profile.decision_pending),
        (WhyTodayReason.RELATIONAL_FRICTION, profile.relational_friction),
        (WhyTodayReason.TIMING_AMPLIFICATION, profile.bazi_day_pressure),
        (WhyTodayReason.FINANCIAL_TENSION, profile.financial_tension),
        (WhyTodayReason.BODY_SIGNAL, profile.body_signal),
    ]
    
    # Sort by score
    reason_scores.sort(key=lambda x: x[1], reverse=True)
    
    if reason_scores[0][1] > 0.2:
        profile.why_today = reason_scores[0][0]
        phrases = WHY_TODAY_PHRASES.get(profile.why_today, [])
        if phrases:
            # Use day-based rotation for variety
            day_of_year = datetime.now().timetuple().tm_yday
            profile.why_today_phrase = phrases[day_of_year % len(phrases)]
    
    return profile


# =============================================================================
# ANTI-REPETITION PENALTY
# =============================================================================

def get_anti_repetition_penalty(
    pattern_id: str,
    pattern_history: List[Dict],
    daily_profile: DailySignalProfile,
) -> Tuple[float, bool]:
    """
    Calculate penalty for patterns that have appeared too recently.
    
    Returns:
        (penalty: float, should_allow: bool)
        
    RULES:
    - Same pattern 2x in 3 days → 0.3 penalty UNLESS intensifying
    - Same pattern 3x in 7 days → 0.5 penalty UNLESS strongly validated
    - If pattern is intensifying (higher daily signals) → reduce penalty
    """
    if not pattern_history:
        return 0.0, True
    
    # Count appearances
    count_3d = 0
    count_7d = 0
    
    for p in pattern_history:
        if p.get("pattern_id") == pattern_id:
            days_ago = p.get("days_ago", 999)
            if days_ago <= 3:
                count_3d += 1
            if days_ago <= 7:
                count_7d += 1
    
    # Base penalty
    penalty = 0.0
    
    if count_3d >= 2:
        penalty = 0.3
    if count_7d >= 3:
        penalty = 0.5
    if count_7d >= 5:
        penalty = 0.7
    
    # EXCEPTION: If pattern is intensifying, reduce penalty
    # This allows genuinely active patterns to recur
    if daily_profile.daily_intensity > 0.6:
        penalty *= 0.5  # Halve the penalty
    if daily_profile.transit_pressure_today > 0.5:
        penalty *= 0.7  # Further reduce if transit active
    
    # Should we allow this pattern?
    # Block if penalty > 0.6 AND not intensifying
    should_allow = penalty < 0.6 or daily_profile.daily_intensity > 0.5
    
    return penalty, should_allow


# =============================================================================
# INJECT DAILY FRESHNESS
# =============================================================================

def inject_daily_freshness(
    flow_text: str,
    daily_profile: DailySignalProfile,
    why_today_phrase: Optional[str] = None,
) -> str:
    """
    Inject at least one daily-fresh signal into the Home copy.
    
    RULES:
    - Add "why today" phrase if available
    - Vary naturally, don't use same phrase every time
    - Don't make it feel tacked-on
    """
    if not flow_text:
        return flow_text
    
    # Get the why-today phrase
    phrase = why_today_phrase or daily_profile.why_today_phrase
    
    if not phrase:
        # Generate a generic freshness phrase based on signals
        if daily_profile.transit_pressure_today > 0.4:
            phrase = "harder to ignore today"
        elif daily_profile.unresolved_recent_loop > 0.3:
            phrase = "still here"
        elif daily_profile.last_72h_pattern_count >= 2:
            phrase = "again"
        else:
            # No strong daily signal - use subtle freshness
            phrase = None
    
    if not phrase:
        return flow_text
    
    # Insert the freshness phrase naturally
    # Strategy: Add after first line break or after first sentence
    lines = flow_text.split("\n")
    
    if len(lines) >= 2:
        # Insert after first line as a bridge
        first_line = lines[0]
        rest = "\n".join(lines[1:])
        
        # Different injection patterns based on phrase type
        if phrase in ["again today", "again", "still here"]:
            # Standalone line
            return f"{first_line}\n\n{phrase.capitalize()}.\n\n{rest}"
        elif phrase.startswith("what"):
            # Question-like - add as follow-up
            return f"{first_line}\n\n— {phrase}\n\n{rest}"
        else:
            # Statement - add as observation
            return f"{first_line}\n\n{phrase.capitalize()}.\n\n{rest}"
    
    # Fallback: append
    return f"{flow_text}\n\n{phrase.capitalize()}."


# =============================================================================
# BUILD "WHY TODAY" EXPLANATION
# =============================================================================

def build_why_today(
    pattern_candidate: PatternCandidate,
    daily_profile: DailySignalProfile,
) -> str:
    """
    Build a short explanation for why this pattern is showing up today.
    Used internally for debugging and potentially for user display.
    """
    reasons = []
    
    if daily_profile.transit_pressure_today > 0.3:
        reasons.append("transit pressure active")
    
    if pattern_candidate.times_shown_72h >= 2:
        reasons.append(f"appeared {pattern_candidate.times_shown_72h}x in 72h")
    
    if daily_profile.unresolved_recent_loop > 0.3:
        reasons.append("unresolved loop in recent reflections")
    
    if daily_profile.decision_pending > 0.4:
        reasons.append("decision tension detected")
    
    if daily_profile.relational_friction > 0.4:
        reasons.append("relational friction detected")
    
    if daily_profile.bazi_day_pressure > 0.3:
        reasons.append("timing amplification (BaZi)")
    
    if not reasons:
        reasons.append("baseline pattern match")
    
    return "; ".join(reasons)


# =============================================================================
# SCORE PATTERN CANDIDATES WITH DAILY WEIGHTING
# =============================================================================

def score_pattern_candidates(
    candidates: List[PatternCandidate],
    daily_profile: DailySignalProfile,
    pattern_history: List[Dict] = None,
) -> List[PatternCandidate]:
    """
    Score and rank pattern candidates with daily signal boosting.
    
    GOAL: Daily signals should matter MORE than static patterns.
    """
    if not candidates:
        return []
    
    for candidate in candidates:
        # Get anti-repetition penalty
        penalty, should_allow = get_anti_repetition_penalty(
            candidate.pattern_id,
            pattern_history or [],
            daily_profile,
        )
        candidate.anti_repetition_penalty = penalty
        
        # Count recent appearances
        if pattern_history:
            for p in pattern_history:
                if p.get("pattern_id") == candidate.pattern_id:
                    days_ago = p.get("days_ago", 999)
                    if days_ago <= 3:
                        candidate.times_shown_72h += 1
                    if days_ago <= 7:
                        candidate.times_shown_7d += 1
                    if days_ago < candidate.last_shown_days_ago:
                        candidate.last_shown_days_ago = days_ago
        
        # DAILY BOOST - This is the key differentiator
        daily_boost = 0.0
        signals_contributing = []
        
        # Transit pressure boost
        if daily_profile.transit_pressure_today > 0.3:
            daily_boost += daily_profile.transit_pressure_today * 0.4
            signals_contributing.append("transit")
        
        # Recent journal boost
        if daily_profile.journal_recency > 0.4:
            daily_boost += daily_profile.journal_recency * 0.3
            signals_contributing.append("journal")
        
        # Unresolved loop boost (if pattern is recurring)
        if candidate.times_shown_72h >= 1 and daily_profile.unresolved_recent_loop > 0.2:
            daily_boost += 0.25
            signals_contributing.append("loop")
        
        # BaZi timing boost
        if daily_profile.bazi_day_pressure > 0.3:
            daily_boost += daily_profile.bazi_day_pressure * 0.2
            signals_contributing.append("timing")
        
        # Life arena match boost
        if candidate.life_arena:
            if candidate.life_arena == "decision" and daily_profile.decision_pending > 0.3:
                daily_boost += 0.2
                signals_contributing.append("decision_match")
            elif candidate.life_arena == "relationship" and daily_profile.relational_friction > 0.3:
                daily_boost += 0.2
                signals_contributing.append("relationship_match")
            elif candidate.life_arena == "money" and daily_profile.financial_tension > 0.2:
                daily_boost += 0.15
                signals_contributing.append("money_match")
        
        candidate.daily_boost = daily_boost
        candidate.daily_signals_contributing = signals_contributing
        
        # Determine why-today reason for this candidate
        if daily_profile.transit_pressure_today > 0.4:
            candidate.why_today_reason = WhyTodayReason.TRANSIT_PRESSURE
        elif candidate.times_shown_72h >= 2:
            candidate.why_today_reason = WhyTodayReason.RECENT_REPETITION
        elif daily_profile.unresolved_recent_loop > 0.3:
            candidate.why_today_reason = WhyTodayReason.UNRESOLVED_REFLECTION
        elif daily_profile.decision_pending > 0.4:
            candidate.why_today_reason = WhyTodayReason.DECISION_TENSION
        elif daily_profile.relational_friction > 0.4:
            candidate.why_today_reason = WhyTodayReason.RELATIONAL_FRICTION
        elif daily_profile.bazi_day_pressure > 0.3:
            candidate.why_today_reason = WhyTodayReason.TIMING_AMPLIFICATION
        
        # Get why-today phrase
        if candidate.why_today_reason:
            phrases = WHY_TODAY_PHRASES.get(candidate.why_today_reason, [])
            if phrases:
                day_of_year = datetime.now().timetuple().tm_yday
                candidate.why_today_phrase = phrases[(day_of_year + hash(candidate.pattern_id)) % len(phrases)]
        
        # FINAL SCORE
        # Formula: base_score + daily_boost - anti_repetition_penalty
        candidate.final_score = candidate.base_score + daily_boost - penalty
        
        # If penalty makes this unviable and not intensifying, mark it
        if not should_allow:
            candidate.final_score *= 0.3  # Heavily penalize
    
    # Sort by final score
    candidates.sort(key=lambda c: c.final_score, reverse=True)
    
    return candidates


# =============================================================================
# DEBUG OUTPUT
# =============================================================================

def generate_debug_output(
    candidates: List[PatternCandidate],
    daily_profile: DailySignalProfile,
    winner: Optional[PatternCandidate] = None,
) -> Dict[str, Any]:
    """
    Generate internal debug logging for Home pattern selection.
    
    Not exposed to user by default.
    """
    debug = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "daily_intensity": round(daily_profile.daily_intensity, 2),
        "why_today": daily_profile.why_today.value if daily_profile.why_today else None,
        "why_today_phrase": daily_profile.why_today_phrase,
        
        "daily_signals": {
            "transit_pressure": round(daily_profile.transit_pressure_today, 2),
            "journal_recency": round(daily_profile.journal_recency, 2),
            "bazi_pressure": round(daily_profile.bazi_day_pressure, 2),
            "unresolved_loop": round(daily_profile.unresolved_recent_loop, 2),
            "decision_pending": round(daily_profile.decision_pending, 2),
            "relational_friction": round(daily_profile.relational_friction, 2),
        },
        
        "top_3_candidates": [],
        
        "winner": None,
        "why_winner_won": None,
        "anti_repetition_applied": False,
    }
    
    # Top 3 candidates
    for i, c in enumerate(candidates[:3]):
        debug["top_3_candidates"].append({
            "rank": i + 1,
            "pattern_id": c.pattern_id,
            "pattern_title": c.pattern_title,
            "base_score": round(c.base_score, 2),
            "daily_boost": round(c.daily_boost, 2),
            "anti_repetition_penalty": round(c.anti_repetition_penalty, 2),
            "final_score": round(c.final_score, 2),
            "times_shown_72h": c.times_shown_72h,
            "daily_signals_contributing": c.daily_signals_contributing,
            "why_today_reason": c.why_today_reason.value if c.why_today_reason else None,
        })
    
    # Winner details
    if winner:
        debug["winner"] = {
            "pattern_id": winner.pattern_id,
            "pattern_title": winner.pattern_title,
            "final_score": round(winner.final_score, 2),
            "why_today_reason": winner.why_today_reason.value if winner.why_today_reason else None,
            "why_today_phrase": winner.why_today_phrase,
        }
        
        # Build explanation for why winner won
        reasons = []
        if winner.daily_boost > 0.2:
            reasons.append(f"daily boost +{round(winner.daily_boost, 2)}")
        if winner.times_shown_72h >= 2:
            reasons.append(f"recurring ({winner.times_shown_72h}x in 72h)")
        if winner.daily_signals_contributing:
            reasons.append(f"signals: {', '.join(winner.daily_signals_contributing)}")
        if winner.anti_repetition_penalty > 0:
            reasons.append(f"anti-repetition penalty -{round(winner.anti_repetition_penalty, 2)}")
            debug["anti_repetition_applied"] = True
        
        debug["why_winner_won"] = "; ".join(reasons) if reasons else "baseline match"
    
    logger.info(f"[DailyDiff] Debug: {debug}")
    
    return debug


# =============================================================================
# LIFE ARENA RESOLUTION
# =============================================================================

LIFE_ARENAS = {
    "decision": {
        "keywords": ["decide", "choice", "option", "commit", "lock in"],
        "opening": "a decision that won't land",
        "variants": [
            "a choice you've been weighing",
            "something you need to close",
            "a commitment that's waiting",
        ],
    },
    "conversation": {
        "keywords": ["say", "tell", "speak", "message", "call"],
        "opening": "something you need to say",
        "variants": [
            "a conversation you've been avoiding",
            "something you've almost said",
            "what you keep rehearsing in your head",
        ],
    },
    "commitment": {
        "keywords": ["commit", "promise", "agree", "sign", "yes"],
        "opening": "a commitment you're circling",
        "variants": [
            "something you're about to lock in",
            "a promise you're not sure about",
            "an agreement that doesn't sit right",
        ],
    },
    "follow_up": {
        "keywords": ["follow", "check", "waiting", "reply", "response"],
        "opening": "something you're waiting on",
        "variants": [
            "a follow-up that's overdue",
            "something that needs a response",
            "a thread you keep checking",
        ],
    },
    "body_no": {
        "keywords": ["tired", "sick", "pain", "body", "energy"],
        "opening": "something your body is saying no to",
        "variants": [
            "the thing that's exhausting you",
            "what your body has been telling you",
            "the drain you keep ignoring",
        ],
    },
    "financial_tension": {
        "keywords": ["money", "pay", "cost", "invest", "spend"],
        "opening": "a financial tension you're carrying",
        "variants": [
            "a money decision you're avoiding",
            "something involving cost or investment",
            "what you're weighing financially",
        ],
    },
    "relational_hesitation": {
        "keywords": ["they", "them", "partner", "relationship", "between"],
        "opening": "something between you and someone",
        "variants": [
            "a dynamic that's been off",
            "tension with someone close",
            "what you're not saying to them",
        ],
    },
}


def resolve_life_arena(
    journal_entries: List[Dict] = None,
    daily_profile: DailySignalProfile = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve the pattern into a specific life arena.
    
    Returns:
        (arena_key, arena_phrase)
    """
    if not journal_entries:
        return None, None
    
    # Score arenas based on journal content
    arena_scores = {k: 0 for k in LIFE_ARENAS}
    
    for entry in journal_entries[:5]:
        content = entry.get("content", "").lower()
        for arena_key, arena_def in LIFE_ARENAS.items():
            for keyword in arena_def["keywords"]:
                if keyword in content:
                    arena_scores[arena_key] += 1
    
    # Also boost based on daily profile
    if daily_profile:
        if daily_profile.decision_pending > 0.3:
            arena_scores["decision"] += 2
        if daily_profile.relational_friction > 0.3:
            arena_scores["relational_hesitation"] += 2
        if daily_profile.financial_tension > 0.2:
            arena_scores["financial_tension"] += 1
        if daily_profile.body_signal > 0.2:
            arena_scores["body_no"] += 1
    
    # Find best arena
    best_arena = max(arena_scores.items(), key=lambda x: x[1])
    
    if best_arena[1] >= 2:
        arena_key = best_arena[0]
        arena_def = LIFE_ARENAS[arena_key]
        
        # Rotate through variants for freshness
        day_of_year = datetime.now().timetuple().tm_yday
        variants = [arena_def["opening"]] + arena_def["variants"]
        phrase = variants[day_of_year % len(variants)]
        
        return arena_key, phrase
    
    return None, None


# =============================================================================
# V2: BEHAVIOR SNAP GENERATION
# =============================================================================

def generate_behavior_snap(
    why_today: WhyTodayReason = None,
    life_arena: LifeArena = None,
    daily_profile: DailySignalProfile = None,
    pattern_id: str = None,
) -> str:
    """
    V2: Generate a BEHAVIOR SNAP - specific micro-behavior that feels immediate.
    
    Replaces abstract "why today" phrases with action-based language.
    
    Returns a present-tense, specific behavior line like:
    - "You were about to decide — then stopped."
    - "You almost sent it."
    - "You checked again."
    """
    day_of_year = datetime.now().timetuple().tm_yday
    hash_seed = hash(pattern_id or "") if pattern_id else 0
    
    # Priority 1: Use life_arena if available (most specific)
    if life_arena and life_arena in ARENA_BEHAVIOR_OPENERS:
        openers = ARENA_BEHAVIOR_OPENERS[life_arena]
        return openers[(day_of_year + hash_seed) % len(openers)]
    
    # Priority 2: Use why_today reason
    if why_today and why_today in BEHAVIOR_SNAPS:
        snaps = BEHAVIOR_SNAPS[why_today]
        return snaps[(day_of_year + hash_seed) % len(snaps)]
    
    # Priority 3: Infer from daily profile signals
    if daily_profile:
        if daily_profile.decision_pending > 0.4:
            return BEHAVIOR_SNAPS[WhyTodayReason.DECISION_TENSION][(day_of_year + hash_seed) % 4]
        if daily_profile.relational_friction > 0.4:
            return BEHAVIOR_SNAPS[WhyTodayReason.RELATIONAL_FRICTION][(day_of_year + hash_seed) % 4]
        if daily_profile.unresolved_recent_loop > 0.3:
            return BEHAVIOR_SNAPS[WhyTodayReason.UNRESOLVED_REFLECTION][(day_of_year + hash_seed) % 4]
        if daily_profile.transit_pressure_today > 0.4:
            return BEHAVIOR_SNAPS[WhyTodayReason.TRANSIT_PRESSURE][(day_of_year + hash_seed) % 4]
        if daily_profile.body_signal > 0.3:
            return BEHAVIOR_SNAPS[WhyTodayReason.BODY_SIGNAL][(day_of_year + hash_seed) % 4]
    
    # Fallback: Generic but still behavioral
    fallback_behaviors = [
        "You paused — something didn't land.",
        "You almost moved — then stopped.",
        "You felt it — and let it pass.",
        "You started — then pulled back.",
    ]
    return fallback_behaviors[(day_of_year + hash_seed) % len(fallback_behaviors)]


# =============================================================================
# V2: FORCED LIFE ARENA RESOLUTION
# =============================================================================

def resolve_life_arena_forced(
    journal_entries: List[Dict] = None,
    daily_profile: DailySignalProfile = None,
    why_today: WhyTodayReason = None,
) -> Tuple[LifeArena, str]:
    """
    V2: Force life arena resolution - ALMOST NEVER returns None.
    
    Uses multiple inference strategies:
    1. Journal keyword detection
    2. Daily profile signal inference
    3. Why-today reason mapping
    4. Fallback to most common arenas
    
    Returns:
        (LifeArena, behavior_opener)
    """
    arena_scores: Dict[LifeArena, float] = {arena: 0.0 for arena in LifeArena}
    
    # =================================================================
    # Strategy 1: Journal keyword detection
    # =================================================================
    if journal_entries:
        for entry in journal_entries[:5]:
            content = entry.get("content", "").lower()
            for arena, keywords in ARENA_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in content:
                        arena_scores[arena] += 1.0
    
    # =================================================================
    # Strategy 2: Daily profile signal inference
    # =================================================================
    if daily_profile:
        if daily_profile.decision_pending > 0.3:
            arena_scores[LifeArena.DECISION] += daily_profile.decision_pending * 3
        if daily_profile.relational_friction > 0.3:
            arena_scores[LifeArena.RELATIONSHIP] += daily_profile.relational_friction * 3
        if daily_profile.financial_tension > 0.2:
            arena_scores[LifeArena.DECISION] += daily_profile.financial_tension * 2
        if daily_profile.body_signal > 0.2:
            arena_scores[LifeArena.INTERNAL_DOUBT] += daily_profile.body_signal * 2
        if daily_profile.unresolved_recent_loop > 0.3:
            arena_scores[LifeArena.FOLLOW_UP] += daily_profile.unresolved_recent_loop * 2
        if daily_profile.transit_pressure_today > 0.4:
            arena_scores[LifeArena.TIMING] += daily_profile.transit_pressure_today * 2
    
    # =================================================================
    # Strategy 3: Why-today reason mapping
    # =================================================================
    WHY_TO_ARENA = {
        WhyTodayReason.TRANSIT_PRESSURE: LifeArena.TIMING,
        WhyTodayReason.RECENT_REPETITION: LifeArena.EXECUTION,
        WhyTodayReason.UNRESOLVED_REFLECTION: LifeArena.INTERNAL_DOUBT,
        WhyTodayReason.DECISION_TENSION: LifeArena.DECISION,
        WhyTodayReason.RELATIONAL_FRICTION: LifeArena.RELATIONSHIP,
        WhyTodayReason.TIMING_AMPLIFICATION: LifeArena.TIMING,
        WhyTodayReason.EXPRESSION_BLOCKED: LifeArena.MESSAGE,
        WhyTodayReason.PATTERN_INTENSIFYING: LifeArena.EXECUTION,
        WhyTodayReason.BODY_SIGNAL: LifeArena.INTERNAL_DOUBT,
        WhyTodayReason.FINANCIAL_TENSION: LifeArena.DECISION,
    }
    
    if why_today and why_today in WHY_TO_ARENA:
        arena_scores[WHY_TO_ARENA[why_today]] += 2.0
    
    # =================================================================
    # Find best arena
    # =================================================================
    best_arena = max(arena_scores.items(), key=lambda x: x[1])
    
    # If we have a clear winner
    if best_arena[1] >= 1.0:
        arena = best_arena[0]
    else:
        # Fallback: Use most common arena based on general distribution
        # Decision and Internal Doubt are most universal
        arena = LifeArena.INTERNAL_DOUBT
    
    # Get behavior opener for this arena
    if arena in ARENA_BEHAVIOR_OPENERS:
        day_of_year = datetime.now().timetuple().tm_yday
        openers = ARENA_BEHAVIOR_OPENERS[arena]
        opener = openers[day_of_year % len(openers)]
    else:
        opener = "You paused — something didn't land."
    
    return arena, opener


# =============================================================================
# V2: INJECT BEHAVIOR FIRST
# =============================================================================

def inject_behavior_first(
    flow_text: str,
    behavior_snap: str,
    life_arena: LifeArena = None,
) -> str:
    """
    V2: Move BEHAVIOR SNAP to first line of Home.
    
    Structure becomes:
    Line 1 → behavior
    Line 2 → recognition  
    Line 3 → tension
    Line 4 → consequence
    Line 5 → opening
    
    Args:
        flow_text: Original flow text from Home
        behavior_snap: The behavior line to put first
        life_arena: Optional arena for context
        
    Returns:
        Restructured flow with behavior first
    """
    if not flow_text:
        return behavior_snap
    
    if not behavior_snap:
        return flow_text
    
    # Parse existing flow into lines
    lines = [line.strip() for line in flow_text.split("\n") if line.strip()]
    
    # If flow is already short, just prepend behavior
    if len(lines) <= 2:
        return f"{behavior_snap}\n\n{flow_text}"
    
    # Remove any existing opening line that feels abstract
    # (Starting with "You already", "There's a", "Something", etc.)
    abstract_openers = [
        "you already", "there's a", "something", "the thing", 
        "what you", "this is", "today", "right now"
    ]
    
    first_line_lower = lines[0].lower()
    if any(first_line_lower.startswith(opener) for opener in abstract_openers):
        lines = lines[1:]  # Remove first abstract line
    
    # Build new flow: behavior first, then remaining lines
    new_flow_parts = [behavior_snap]
    
    # Add remaining lines with proper spacing
    for line in lines:
        new_flow_parts.append(line)
    
    return "\n\n".join(new_flow_parts)


# =============================================================================
# V2: TIGHTEN LANGUAGE
# =============================================================================

def tighten_copy(text: str) -> str:
    """
    V2: Tighten language for behavioral immediacy.
    
    Rules applied:
    - Remove abstract nouns when possible
    - Prefer verbs over descriptions
    - Short lines (1-2 clauses max)
    - Present tense only
    """
    if not text:
        return text
    
    # Past tense to present tense conversions
    past_to_present = {
        " was ": " is ",
        " were ": " are ",
        " felt ": " feel ",
        " had ": " have ",
        " thought ": " think ",
        " knew ": " know ",
        " wanted ": " want ",
        " needed ": " need ",
    }
    
    result = text
    
    # Convert past to present tense
    for past, present in past_to_present.items():
        result = result.replace(past, present)
    
    # We intentionally don't replace abstract nouns automatically
    # as they sometimes add necessary context
    # This is a placeholder for more sophisticated NLP if needed
    
    return result


# =============================================================================
# V2: COMPLETE BEHAVIORAL HOME GENERATION
# =============================================================================

def generate_behavioral_home(
    flow_text: str,
    daily_profile: DailySignalProfile,
    journal_entries: List[Dict] = None,
    pattern_id: str = None,
) -> Dict[str, Any]:
    """
    V2: Generate complete behavioral Home with all V2 upgrades.
    
    Returns dict with:
    - behavior_snap: First line behavior
    - life_arena: Forced resolution
    - flow: Restructured flow with behavior first
    - debug: V2 debug info
    """
    # Force life arena resolution
    life_arena, arena_opener = resolve_life_arena_forced(
        journal_entries=journal_entries,
        daily_profile=daily_profile,
        why_today=daily_profile.why_today,
    )
    
    # Generate behavior snap based on arena and why_today
    behavior_snap = generate_behavior_snap(
        why_today=daily_profile.why_today,
        life_arena=life_arena,
        daily_profile=daily_profile,
        pattern_id=pattern_id,
    )
    
    # Inject behavior first into flow
    new_flow = inject_behavior_first(
        flow_text=flow_text,
        behavior_snap=behavior_snap,
        life_arena=life_arena,
    )
    
    # Tighten language
    new_flow = tighten_copy(new_flow)
    
    return {
        "behavior_snap": behavior_snap,
        "life_arena": life_arena.value,
        "arena_opener": arena_opener,
        "flow": new_flow,
        "why_today": daily_profile.why_today.value if daily_profile.why_today else None,
        "daily_intensity": daily_profile.daily_intensity,
        "debug": {
            "original_flow_length": len(flow_text) if flow_text else 0,
            "new_flow_length": len(new_flow) if new_flow else 0,
            "behavior_source": "arena" if life_arena in ARENA_BEHAVIOR_OPENERS else "why_today",
        }
    }

