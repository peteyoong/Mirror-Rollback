"""
Mirror Home Engine - Truth-Based
================================

Generates Home content based ONLY on real signals, not artificial variance.

REMOVED:
- User-id-based pseudo-variance
- Seeded randomness
- Arbitrary per-user noise

USES ONLY:
- Transit stack
- House/domain activation
- HD authority/tension
- BaZi day profile
- Recent journal/reflection/pattern history
- Prior exposure state

HOME STRUCTURE:
1. OPENING HIT - Direct confronting statement
2. TENSION - Two forces in conflict
3. CONTEXT - Where this is showing up today
4. STAKES - What happens if misread
5. ONE WISE MOVE - Clear action
6. CTA - See what's really going on →
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# LIFE DOMAINS - Real contexts
# =============================================================================

class LifeDomain(Enum):
    WORK = "work"
    RELATIONSHIP = "relationship"
    DECISION = "decision"
    MONEY = "money"
    FAMILY = "family"
    INTERNAL = "internal"
    CREATIVE = "creative"
    HEALTH = "health"


DOMAIN_CONTEXTS = {
    LifeDomain.WORK: [
        "a work move you want to lock in",
        "a career decision that feels overdue",
        "a project or direction you're trying to push through",
    ],
    LifeDomain.RELATIONSHIP: [
        "a relationship tension you're trying to settle",
        "a conversation you keep replaying",
        "something you haven't said to someone close",
    ],
    LifeDomain.DECISION: [
        "a decision that feels overdue",
        "a choice you're about to make",
        "something you're trying to close or commit to",
    ],
    LifeDomain.MONEY: [
        "a financial decision you're weighing",
        "something involving money or resources",
        "an investment of time or capital you're considering",
    ],
    LifeDomain.FAMILY: [
        "a family dynamic that's unresolved",
        "something involving home or family",
        "a tension with someone close to you",
    ],
    LifeDomain.INTERNAL: [
        "something you haven't let yourself face",
        "an internal conversation you keep having",
        "a truth you're circling but not landing",
    ],
    LifeDomain.CREATIVE: [
        "something you want to create or express",
        "a project that's been waiting for you",
        "something you've been meaning to say or make",
    ],
    LifeDomain.HEALTH: [
        "a change you know you need to make",
        "a pattern that's affecting your wellbeing",
        "something your body has been telling you",
    ],
}


# =============================================================================
# DAY PRESSURES - Live situation types
# =============================================================================

class DayPressure(Enum):
    PUSH = "push"       # Urge to act/move
    HOLD = "hold"       # Need to wait
    CLARIFY = "clarify" # Seeking certainty
    CORRECT = "correct" # Something off-track
    EXPRESS = "express" # Something unsaid


# =============================================================================
# CORE TENSIONS
# =============================================================================

class CoreTension(Enum):
    URGE_VS_UNREADINESS = "urge_vs_unreadiness"
    CERTAINTY_VS_AMBIGUITY = "certainty_vs_ambiguity"
    PRESSURE_VS_TRUTH = "pressure_vs_truth"
    MOVEMENT_VS_CONSEQUENCE = "movement_vs_consequence"
    EXPRESSION_VS_HOLDING = "expression_vs_holding"
    COMMITMENT_VS_FREEDOM = "commitment_vs_freedom"
    KNOWING_VS_AVOIDING = "knowing_vs_avoiding"


TENSION_TEMPLATES = {
    CoreTension.URGE_VS_UNREADINESS: {
        "line": "The urge is real—but acting on it too early is the trap.",
        "expanded": "Part of you wants to move now.\nBut another part knows the ground isn't solid yet.",
    },
    CoreTension.CERTAINTY_VS_AMBIGUITY: {
        "line": "You want to know—but the answer hasn't fully landed.",
        "expanded": "Part of you wants certainty now.\nBut another part knows it hasn't arrived yet.",
    },
    CoreTension.PRESSURE_VS_TRUTH: {
        "line": "The pressure is real—but it's not the same as clarity.",
        "expanded": "Part of you feels urgency.\nBut another part knows this isn't about speed.",
    },
    CoreTension.MOVEMENT_VS_CONSEQUENCE: {
        "line": "Moving now might feel like progress—but the cleanup could cost more.",
        "expanded": "Part of you wants forward motion.\nBut another part senses the consequences aren't clear.",
    },
    CoreTension.EXPRESSION_VS_HOLDING: {
        "line": "There's something that wants to be said—and something keeping it in.",
        "expanded": "Part of you wants to speak.\nBut another part is holding back.",
    },
    CoreTension.COMMITMENT_VS_FREEDOM: {
        "line": "Committing feels right—but so does keeping options open.",
        "expanded": "Part of you wants to lock in.\nBut another part isn't ready to close the door.",
    },
    CoreTension.KNOWING_VS_AVOIDING: {
        "line": "You already know—but facing it means something has to change.",
        "expanded": "Part of you sees the truth.\nBut another part is protecting you from it.",
    },
}


# =============================================================================
# SIGNAL PROFILE (Truth-Based)
# =============================================================================

@dataclass
class LiveSignalProfile:
    """Real signals only - no artificial variance."""
    
    # Day pressure signals (0-1)
    action_pressure: float = 0.0
    clarity_delay: float = 0.0
    external_dependency: float = 0.0
    emotional_intensity: float = 0.0
    expression_blockage: float = 0.0
    urgency: float = 0.0
    recurrence: float = 0.0
    avoidance: float = 0.0
    readiness_mismatch: float = 0.0
    
    # Domain signals
    dominant_domain: LifeDomain = LifeDomain.INTERNAL
    domain_confidence: float = 0.0
    
    # Derived
    strongest_pressure: DayPressure = DayPressure.CLARIFY
    strongest_tension: CoreTension = CoreTension.CERTAINTY_VS_AMBIGUITY
    
    # Stakes
    stakes_level: float = 0.0  # 0-1, how much this matters today
    
    # Journal binding
    recent_theme: Optional[str] = None
    bound_context: Optional[str] = None


def extract_live_signals(
    transit_aspects: List[Dict] = None,
    house_activations: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
    exposure_state: str = None,
) -> LiveSignalProfile:
    """
    Extract REAL signals only. No user-id variance.
    
    Signals come from:
    - Transit stack
    - House/domain activation
    - HD authority/tension
    - BaZi day profile
    - Recent journal/reflection/pattern history
    - Prior exposure state
    """
    profile = LiveSignalProfile()
    
    # =================================================================
    # A. TRANSIT EVIDENCE
    # =================================================================
    if transit_aspects:
        for aspect in transit_aspects:
            transit_point = aspect.get("transit_point", "").lower()
            aspect_type = aspect.get("aspect_type", "").lower()
            natal_point = aspect.get("natal_point", "").lower()
            weight = aspect.get("weight", 0.5)
            house = aspect.get("natal_house", 0)
            
            # Action/drive signals
            if transit_point in ["mars", "sun"]:
                profile.action_pressure += weight * 0.4
                profile.urgency += weight * 0.2
            
            # Clarity/confusion signals
            if transit_point in ["neptune"]:
                profile.clarity_delay += weight * 0.5
                profile.avoidance += weight * 0.2
            if transit_point == "moon":
                profile.emotional_intensity += weight * 0.4
                profile.clarity_delay += weight * 0.2
            
            # Relationship/external signals
            if transit_point in ["venus"] or house == 7:
                profile.external_dependency += weight * 0.4
            
            # Communication/expression signals
            if transit_point in ["mercury"] or house == 3:
                profile.expression_blockage += weight * 0.2
            
            # Challenging aspects increase stakes
            if aspect_type in ["square", "opposition"]:
                profile.stakes_level += weight * 0.2
                profile.readiness_mismatch += weight * 0.3
            
            # Domain detection from houses
            if house in [2, 8]:
                profile.dominant_domain = LifeDomain.MONEY
            elif house in [4, 10]:
                profile.dominant_domain = LifeDomain.WORK
            elif house in [5, 7]:
                profile.dominant_domain = LifeDomain.RELATIONSHIP
            elif house == 12:
                profile.dominant_domain = LifeDomain.INTERNAL
                profile.avoidance += weight * 0.3
    
    # =================================================================
    # B. HOUSE/DOMAIN ACTIVATION
    # =================================================================
    if house_activations:
        domain_scores = {}
        for activation in house_activations:
            house = activation.get("house", 0)
            intensity = activation.get("intensity", 0.5)
            
            if house in [2, 8]:
                domain_scores[LifeDomain.MONEY] = domain_scores.get(LifeDomain.MONEY, 0) + intensity
            elif house in [6, 10]:
                domain_scores[LifeDomain.WORK] = domain_scores.get(LifeDomain.WORK, 0) + intensity
            elif house in [4]:
                domain_scores[LifeDomain.FAMILY] = domain_scores.get(LifeDomain.FAMILY, 0) + intensity
            elif house in [5, 7, 11]:
                domain_scores[LifeDomain.RELATIONSHIP] = domain_scores.get(LifeDomain.RELATIONSHIP, 0) + intensity
            elif house in [1, 12]:
                domain_scores[LifeDomain.INTERNAL] = domain_scores.get(LifeDomain.INTERNAL, 0) + intensity
            elif house in [3, 9]:
                domain_scores[LifeDomain.CREATIVE] = domain_scores.get(LifeDomain.CREATIVE, 0) + intensity
        
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            profile.dominant_domain = best_domain[0]
            profile.domain_confidence = min(1.0, best_domain[1])
    
    # =================================================================
    # C. HUMAN DESIGN SIGNALS
    # =================================================================
    if hd_data:
        authority = hd_data.get("authority", "").lower()
        hd_type = hd_data.get("type", "").lower()
        defined_centers = [c.lower() for c in hd_data.get("defined_centers", [])]
        
        # Emotional authority = clarity takes time
        if "emotional" in authority:
            profile.clarity_delay += 0.35
            profile.emotional_intensity += 0.3
            profile.strongest_tension = CoreTension.CERTAINTY_VS_AMBIGUITY
        
        # Sacral authority = gut responses
        if "sacral" in authority:
            profile.action_pressure += 0.25
        
        # Splenic = instant knowing (but can be overridden)
        if "splenic" in authority:
            profile.action_pressure += 0.2
            profile.stakes_level += 0.1
        
        # Projector = waiting for invitation
        if "projector" in hd_type:
            profile.external_dependency += 0.3
            profile.readiness_mismatch += 0.2
            profile.strongest_tension = CoreTension.PRESSURE_VS_TRUTH
        
        # Manifestor = urge to initiate
        if "manifestor" in hd_type:
            profile.action_pressure += 0.3
            profile.urgency += 0.2
        
        # Open centers create specific tensions
        if "throat" not in defined_centers:
            profile.expression_blockage += 0.25
        if "g" not in defined_centers and "g center" not in defined_centers:
            profile.clarity_delay += 0.2
    
    # =================================================================
    # D. BAZI DAY PROFILE
    # =================================================================
    if bazi_data:
        day_stem = bazi_data.get("day_stem", "")
        day_signals = bazi_data.get("day_signals", {})
        
        if day_signals.get("pressure", 0) > 0.5:
            profile.urgency += 0.3
            profile.stakes_level += 0.2
        if day_signals.get("conflict", 0) > 0.5:
            profile.readiness_mismatch += 0.3
            profile.stakes_level += 0.15
        if day_signals.get("opportunity", 0) > 0.5:
            profile.action_pressure += 0.2
        if day_signals.get("clarity", 0) > 0.5:
            profile.clarity_delay -= 0.2  # Reduce if clarity is high
    
    # =================================================================
    # E. PATTERN HISTORY (Recurrence)
    # =================================================================
    if pattern_history:
        recent = [p for p in pattern_history if p.get("days_ago", 999) < 7]
        
        if len(recent) >= 3:
            profile.recurrence += 0.6
            profile.stakes_level += 0.2  # Recurring = higher stakes
        elif len(recent) >= 2:
            profile.recurrence += 0.4
            profile.stakes_level += 0.1
        elif len(recent) >= 1:
            profile.recurrence += 0.2
        
        # Check for specific pattern types
        for p in recent:
            pattern_id = p.get("pattern_id", "").lower()
            if "avoid" in pattern_id:
                profile.avoidance += 0.15
                profile.strongest_tension = CoreTension.KNOWING_VS_AVOIDING
            if "express" in pattern_id:
                profile.expression_blockage += 0.15
            if "force" in pattern_id or "push" in pattern_id:
                profile.action_pressure += 0.1
    
    # =================================================================
    # F. JOURNAL ENTRIES (Theme Binding)
    # =================================================================
    if journal_entries:
        themes = {
            "waiting": 0, "stuck": 0, "blocked": 0,
            "decision": 0, "choose": 0, "decide": 0,
            "relationship": 0, "they": 0, "person": 0,
            "work": 0, "job": 0, "career": 0,
            "say": 0, "tell": 0, "speak": 0,
            "avoid": 0, "facing": 0, "truth": 0,
            "money": 0, "pay": 0, "cost": 0,
        }
        
        recent_text = ""
        for entry in journal_entries[:5]:  # Last 5 entries
            content = entry.get("content", "").lower()
            recent_text += " " + content
            
            for theme in themes:
                if theme in content:
                    themes[theme] += 1
        
        # Detect dominant theme
        theme_groups = {
            LifeDomain.DECISION: themes["decision"] + themes["choose"] + themes["decide"],
            LifeDomain.RELATIONSHIP: themes["relationship"] + themes["they"] + themes["person"],
            LifeDomain.WORK: themes["work"] + themes["job"] + themes["career"],
            LifeDomain.MONEY: themes["money"] + themes["pay"] + themes["cost"],
            LifeDomain.INTERNAL: themes["avoid"] + themes["facing"] + themes["truth"],
        }
        
        best_theme = max(theme_groups.items(), key=lambda x: x[1])
        if best_theme[1] >= 2:
            profile.dominant_domain = best_theme[0]
            profile.domain_confidence = min(1.0, best_theme[1] / 5.0)
        
        # Signal extraction from journal
        if themes["waiting"] + themes["stuck"] + themes["blocked"] >= 2:
            profile.external_dependency += 0.3
        if themes["say"] + themes["tell"] + themes["speak"] >= 2:
            profile.expression_blockage += 0.4  # Strong signal
            profile.strongest_tension = CoreTension.EXPRESSION_VS_HOLDING
        if themes["avoid"] + themes["facing"] + themes["truth"] >= 2:
            profile.avoidance += 0.35
            profile.strongest_tension = CoreTension.KNOWING_VS_AVOIDING
        
        # Extract recent theme for context binding
        if len(recent_text) > 50:
            # Find most specific phrase
            if "decision" in recent_text or "decide" in recent_text:
                profile.recent_theme = "decision"
            elif "work" in recent_text or "job" in recent_text:
                profile.recent_theme = "work"
            elif "relationship" in recent_text or "they" in recent_text:
                profile.recent_theme = "relationship"
            elif "express" in recent_text or "say" in recent_text:
                profile.recent_theme = "expression"
    
    # =================================================================
    # G. EXPOSURE STATE (Prior engagement)
    # =================================================================
    if exposure_state:
        if exposure_state == "first_exposure":
            pass  # No adjustment
        elif exposure_state == "repeated_exposure":
            profile.recurrence += 0.2
            profile.stakes_level += 0.1
        elif exposure_state == "persistent_pattern":
            profile.recurrence += 0.4
            profile.avoidance += 0.2
            profile.stakes_level += 0.2
        elif exposure_state == "engaged_pattern":
            profile.stakes_level += 0.15
    
    # =================================================================
    # DERIVE PRESSURE TYPE
    # =================================================================
    if profile.action_pressure > 0.4 and profile.urgency > 0.3:
        profile.strongest_pressure = DayPressure.PUSH
    elif profile.clarity_delay > 0.4:
        profile.strongest_pressure = DayPressure.CLARIFY
    elif profile.expression_blockage > 0.35:
        profile.strongest_pressure = DayPressure.EXPRESS
    elif profile.external_dependency > 0.35:
        profile.strongest_pressure = DayPressure.HOLD
    elif profile.recurrence > 0.4 or profile.avoidance > 0.35:
        profile.strongest_pressure = DayPressure.CORRECT
    
    # =================================================================
    # DERIVE CORE TENSION
    # =================================================================
    # Choose tension based on strongest signals
    if profile.action_pressure > 0.4 and profile.clarity_delay > 0.3:
        profile.strongest_tension = CoreTension.URGE_VS_UNREADINESS
    elif profile.action_pressure > 0.4 and profile.readiness_mismatch > 0.3:
        profile.strongest_tension = CoreTension.MOVEMENT_VS_CONSEQUENCE
    elif profile.urgency > 0.4 and profile.clarity_delay > 0.3:
        profile.strongest_tension = CoreTension.PRESSURE_VS_TRUTH
    elif profile.expression_blockage > 0.35:
        profile.strongest_tension = CoreTension.EXPRESSION_VS_HOLDING
    elif profile.avoidance > 0.35:
        profile.strongest_tension = CoreTension.KNOWING_VS_AVOIDING
    elif profile.external_dependency > 0.35 and profile.action_pressure > 0.3:
        profile.strongest_tension = CoreTension.COMMITMENT_VS_FREEDOM
    # Default is CERTAINTY_VS_AMBIGUITY (already set)
    
    # =================================================================
    # NORMALIZE
    # =================================================================
    for attr in ["action_pressure", "clarity_delay", "external_dependency",
                 "emotional_intensity", "expression_blockage", "urgency",
                 "recurrence", "avoidance", "readiness_mismatch", "stakes_level"]:
        val = getattr(profile, attr)
        setattr(profile, attr, min(1.0, max(0.0, val)))
    
    return profile


# =============================================================================
# HOME PATTERN TYPES (Specific situations, not abstract labels)
# =============================================================================

class HomeSituation(Enum):
    """Specific lived situations, not abstract patterns."""
    FORCING_PREMATURE = "forcing_premature"
    WAITING_WITHOUT_CLARITY = "waiting_without_clarity"
    BLOCKED_BY_OTHERS = "blocked_by_others"
    AVOIDING_WHAT_YOU_KNOW = "avoiding_what_you_know"
    PUSHING_AGAINST_RESISTANCE = "pushing_against_resistance"
    TORN_BETWEEN_OPTIONS = "torn_between_options"
    HOLDING_BACK_EXPRESSION = "holding_back_expression"
    DIRECTION_UNCLEAR = "direction_unclear"
    PRESSURE_WITHOUT_READINESS = "pressure_without_readiness"
    STANDING_AT_THRESHOLD = "standing_at_threshold"


# =============================================================================
# HIGH-STAKES HOME MESSAGES
# =============================================================================

HOME_MESSAGES = {
    HomeSituation.FORCING_PREMATURE: {
        "opening_hit": "You're close to forcing something that will cost more to clean up later.",
        "tension": "The urge is real—but acting on it too early is the trap.",
        "tension_expanded": "Part of you wants to move now.\nBut another part knows the ground isn't solid yet.",
        "stakes": "If you force it today, you'll create more cleanup than progress.",
        "wise_move": "Wait until the signal feels settled, not just urgent.",
        "cta": "See what's not ready yet →",
    },
    HomeSituation.WAITING_WITHOUT_CLARITY: {
        "opening_hit": "You're waiting for certainty that hasn't arrived—and the waiting is creating its own pressure.",
        "tension": "You want to know—but the answer hasn't fully landed.",
        "tension_expanded": "Part of you wants certainty now.\nBut another part knows it hasn't arrived yet.",
        "stakes": "Deciding just to end the uncertainty will give you a false answer, not a real one.",
        "wise_move": "Hold the question without forcing an answer. Let it settle.",
        "cta": "See what's actually clear →",
    },
    HomeSituation.BLOCKED_BY_OTHERS: {
        "opening_hit": "You're ready to move—but this one isn't fully yours to move.",
        "tension": "The wait isn't confusion. It's dependence on something outside your control.",
        "tension_expanded": "Part of you is ready.\nBut another part is waiting for something that isn't yours to control.",
        "stakes": "Pushing harder won't make them move faster—it'll just create tension.",
        "wise_move": "Focus on what IS yours while you wait.",
        "cta": "See what you can do →",
    },
    HomeSituation.AVOIDING_WHAT_YOU_KNOW: {
        "opening_hit": "You already know what's true here—but naming it means something has to change.",
        "tension": "This isn't confusion. It's protection from what you already see.",
        "tension_expanded": "Part of you sees the truth.\nBut another part is protecting you from it.",
        "stakes": "The longer you circle without landing, the heavier it gets.",
        "wise_move": "Name it to yourself first. Just that.",
        "cta": "Face what you already know →",
    },
    HomeSituation.PUSHING_AGAINST_RESISTANCE: {
        "opening_hit": "You're pushing hard—but the harder you push, the less it moves.",
        "tension": "The effort is real. So is the resistance. They're feeding each other.",
        "tension_expanded": "Part of you wants to force this through.\nBut another part feels the friction building.",
        "stakes": "More effort in the wrong direction just exhausts you without creating progress.",
        "wise_move": "Pause and ask: where IS there flow right now?",
        "cta": "See what's actually open →",
    },
    HomeSituation.TORN_BETWEEN_OPTIONS: {
        "opening_hit": "You're pulled between two things that both feel true—and choosing feels impossible.",
        "tension": "This isn't indecision. It's two real truths competing.",
        "tension_expanded": "Part of you wants one thing.\nBut another part wants something that contradicts it.",
        "stakes": "Forcing a choice before the tension resolves will abandon something that matters.",
        "wise_move": "Name both pulls honestly. Let them coexist for now.",
        "cta": "See both sides clearly →",
    },
    HomeSituation.HOLDING_BACK_EXPRESSION: {
        "opening_hit": "There's something you're not saying—and it's sitting in you, taking up space.",
        "tension": "Expression wants to happen. But something is keeping it in.",
        "tension_expanded": "Part of you wants to speak.\nBut another part is holding back.",
        "stakes": "What's unsaid doesn't disappear. It builds pressure or becomes resentment.",
        "wise_move": "Say it somewhere safe first. Write it. Speak it to one person.",
        "cta": "See what wants to be said →",
    },
    HomeSituation.DIRECTION_UNCLEAR: {
        "opening_hit": "You know something needs to move—but you can't see the path clearly yet.",
        "tension": "Direction exists. You just can't see it from here.",
        "tension_expanded": "Part of you knows change is needed.\nBut another part can't see where to go.",
        "stakes": "Forcing a direction just to have one will point you somewhere wrong.",
        "wise_move": "Take the smallest step you can see. The next one will appear.",
        "cta": "See what's emerging →",
    },
    HomeSituation.PRESSURE_WITHOUT_READINESS: {
        "opening_hit": "The pressure to decide is real—but your clarity isn't caught up yet.",
        "tension": "Urgency and readiness are out of sync. They're not the same thing.",
        "tension_expanded": "Part of you feels urgent pressure.\nBut another part isn't actually ready.",
        "stakes": "Deciding under pressure without clarity will give you relief, not resolution.",
        "wise_move": "Separate the pressure from the decision. Which is actually yours?",
        "cta": "See what's truly urgent →",
    },
    HomeSituation.STANDING_AT_THRESHOLD: {
        "opening_hit": "You're standing at a threshold—but you haven't stepped through yet.",
        "tension": "The door is open. The step hasn't happened. Something is keeping you on this side.",
        "tension_expanded": "Part of you is ready to cross.\nBut another part is anchored to what's behind.",
        "stakes": "Hovering at the threshold drains more than either staying or going.",
        "wise_move": "Name what you'd be leaving. Then decide if you're ready.",
        "cta": "See what's on the other side →",
    },
}


# =============================================================================
# SITUATION SELECTION (Truth-Based)
# =============================================================================

def select_home_situation(profile: LiveSignalProfile) -> Tuple[HomeSituation, float]:
    """
    Select the single strongest live situation based on real signals.
    NO artificial variance. Pure signal-based selection.
    """
    
    scores = {}
    
    # FORCING_PREMATURE: high action + clarity delay
    scores[HomeSituation.FORCING_PREMATURE] = (
        profile.action_pressure * 0.4 +
        profile.clarity_delay * 0.3 +
        profile.urgency * 0.2 +
        profile.readiness_mismatch * 0.1
    )
    
    # WAITING_WITHOUT_CLARITY: high clarity delay + emotional
    scores[HomeSituation.WAITING_WITHOUT_CLARITY] = (
        profile.clarity_delay * 0.5 +
        profile.emotional_intensity * 0.3 +
        profile.urgency * 0.2
    )
    
    # BLOCKED_BY_OTHERS: external dependency
    scores[HomeSituation.BLOCKED_BY_OTHERS] = (
        profile.external_dependency * 0.5 +
        profile.readiness_mismatch * 0.3 +
        profile.action_pressure * 0.2
    )
    
    # AVOIDING_WHAT_YOU_KNOW: avoidance + recurrence
    scores[HomeSituation.AVOIDING_WHAT_YOU_KNOW] = (
        profile.avoidance * 0.5 +
        profile.recurrence * 0.3 +
        profile.emotional_intensity * 0.2
    )
    
    # PUSHING_AGAINST_RESISTANCE: action + readiness mismatch
    scores[HomeSituation.PUSHING_AGAINST_RESISTANCE] = (
        profile.action_pressure * 0.4 +
        profile.readiness_mismatch * 0.4 +
        profile.urgency * 0.2
    )
    
    # TORN_BETWEEN_OPTIONS: emotional intensity + clarity delay
    scores[HomeSituation.TORN_BETWEEN_OPTIONS] = (
        profile.emotional_intensity * 0.4 +
        profile.clarity_delay * 0.3 +
        profile.recurrence * 0.2 +
        (1 - profile.action_pressure) * 0.1  # Less action = more torn
    )
    
    # HOLDING_BACK_EXPRESSION: expression blockage
    scores[HomeSituation.HOLDING_BACK_EXPRESSION] = (
        profile.expression_blockage * 0.5 +
        profile.emotional_intensity * 0.3 +
        profile.avoidance * 0.2
    )
    
    # DIRECTION_UNCLEAR: clarity delay + low action
    scores[HomeSituation.DIRECTION_UNCLEAR] = (
        profile.clarity_delay * 0.4 +
        (1 - profile.action_pressure) * 0.3 +
        profile.readiness_mismatch * 0.3
    )
    
    # PRESSURE_WITHOUT_READINESS: urgency + clarity delay
    scores[HomeSituation.PRESSURE_WITHOUT_READINESS] = (
        profile.urgency * 0.4 +
        profile.clarity_delay * 0.3 +
        profile.external_dependency * 0.2 +
        (1 - profile.action_pressure) * 0.1
    )
    
    # STANDING_AT_THRESHOLD: readiness mismatch + avoidance
    scores[HomeSituation.STANDING_AT_THRESHOLD] = (
        profile.readiness_mismatch * 0.4 +
        profile.avoidance * 0.3 +
        profile.emotional_intensity * 0.2 +
        (1 - profile.urgency) * 0.1
    )
    
    # Apply stakes multiplier
    for situation in scores:
        scores[situation] *= (1 + profile.stakes_level * 0.3)
    
    # Select highest
    best = max(scores.items(), key=lambda x: x[1])
    
    return best[0], min(1.0, best[1])


# =============================================================================
# HOME MESSAGE GENERATION
# =============================================================================

def generate_home_message(
    transit_aspects: List[Dict] = None,
    house_activations: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
    exposure_state: str = None,
) -> Dict[str, Any]:
    """
    Generate truth-based Home message.
    
    NO artificial variance.
    Based only on real signals from transits, HD, BaZi, journals, history.
    """
    
    # Extract real signals
    profile = extract_live_signals(
        transit_aspects=transit_aspects,
        house_activations=house_activations,
        hd_data=hd_data,
        bazi_data=bazi_data,
        pattern_history=pattern_history,
        journal_entries=journal_entries,
        exposure_state=exposure_state,
    )
    
    # Select situation based on truth
    situation, confidence = select_home_situation(profile)
    
    # Get message template
    message = HOME_MESSAGES.get(situation, HOME_MESSAGES[HomeSituation.DIRECTION_UNCLEAR])
    
    # Build context based on real domain
    domain_contexts = DOMAIN_CONTEXTS.get(profile.dominant_domain, DOMAIN_CONTEXTS[LifeDomain.INTERNAL])
    
    # Choose most specific context based on journal binding
    if profile.bound_context:
        context_line = profile.bound_context
    elif profile.recent_theme:
        theme_contexts = {
            "decision": "a decision you're weighing",
            "work": "a work situation you're navigating",
            "relationship": "a relationship dynamic",
            "expression": "something you want to say",
        }
        context_line = theme_contexts.get(profile.recent_theme, domain_contexts[0])
    else:
        context_line = domain_contexts[0]
    
    # Build full context sentence
    full_context = f"This is most likely showing up in {context_line}."
    
    # Get tension template
    tension_template = TENSION_TEMPLATES.get(profile.strongest_tension, 
                                             TENSION_TEMPLATES[CoreTension.CERTAINTY_VS_AMBIGUITY])
    
    return {
        # HOME STRUCTURE
        "opening_hit": message["opening_hit"],
        "tension": message["tension_expanded"],
        "tension_short": message["tension"],
        "context": full_context,
        "stakes": message["stakes"],
        "wise_move": message["wise_move"],
        "cta": message["cta"],
        
        # Metadata
        "situation": situation.value,
        "confidence": confidence,
        "domain": profile.dominant_domain.value,
        "pressure_type": profile.strongest_pressure.value,
        "core_tension": profile.strongest_tension.value,
        "stakes_level": profile.stakes_level,
        
        # Debug (for verification)
        "debug": {
            "action_pressure": round(profile.action_pressure, 2),
            "clarity_delay": round(profile.clarity_delay, 2),
            "external_dependency": round(profile.external_dependency, 2),
            "emotional_intensity": round(profile.emotional_intensity, 2),
            "expression_blockage": round(profile.expression_blockage, 2),
            "urgency": round(profile.urgency, 2),
            "recurrence": round(profile.recurrence, 2),
            "avoidance": round(profile.avoidance, 2),
            "readiness_mismatch": round(profile.readiness_mismatch, 2),
        },
    }


# =============================================================================
# FORMATTED HOME OUTPUT
# =============================================================================

def format_home_for_display(home: Dict[str, Any]) -> str:
    """Format Home message for display (testing/preview)."""
    lines = [
        home["opening_hit"],
        "",
        home["tension"],
        "",
        home["context"],
        "",
        home["stakes"],
        "",
        home["wise_move"],
        "",
        f"[{home['cta']}]",
    ]
    return "\n".join(lines)
