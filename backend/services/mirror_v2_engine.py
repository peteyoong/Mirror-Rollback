"""
Mirror V2 Engine
================

Combines:
1) Pattern Differentiation Engine (no generic patterns)
2) TENSION-FIRST content system
3) Scene-based, real-life language
4) Human Design + Gene Keys translation into behavior

CORE PRINCIPLE:
Every output must show TENSION - two opposing forces:
"Part of you… but another part…"

STRUCTURE:
- RECOGNITION (what you're doing - specific, present-moment)
- TENSION (WHY you're stuck - MOST IMPORTANT)
- CONTEXT (where this is happening in life)
- WHAT THIS IS / WHEN IT TRIPS YOU UP / WHEN IT WORKS / AT YOUR HIGHEST
- WHERE YOU'LL NOTICE THIS TODAY (3 real situations)
- TRY THIS (3 real behaviors)
- WHY THIS IS HAPPENING (collapsible - systems appear here only)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# SCENE TYPES - Real-life contexts
# =============================================================================

class SceneType(Enum):
    DECISION = "decision"
    WORK_DIRECTION = "work_direction"
    RELATIONSHIP = "relationship"
    CONVERSATION = "conversation"
    INTERNAL_AVOIDANCE = "internal_avoidance"
    CREATIVE_EXPRESSION = "creative_expression"
    COMMITMENT = "commitment"


SCENE_DESCRIPTIONS = {
    SceneType.DECISION: "a decision you're trying to push through",
    SceneType.WORK_DIRECTION: "your work or career direction",
    SceneType.RELATIONSHIP: "a relationship dynamic that feels unresolved",
    SceneType.CONVERSATION: "a conversation you're avoiding or replaying",
    SceneType.INTERNAL_AVOIDANCE: "something you're not letting yourself fully face",
    SceneType.CREATIVE_EXPRESSION: "something you want to express but haven't",
    SceneType.COMMITMENT: "a commitment you're weighing",
}


# =============================================================================
# DIFFERENTIATED PATTERNS (No generic fallbacks)
# =============================================================================

class DifferentiatedPatternV2(Enum):
    """Specific pattern types - NO generic 'Pause' or 'Stall'."""
    PREMATURE_MOVE = "premature_move"
    CLARITY_NOT_LANDED = "clarity_not_landed"
    WAITING_ON_RESPONSE = "waiting_on_response"
    AVOIDED_TRUTH = "avoided_truth"
    FORCING_MOMENTUM = "forcing_momentum"
    SPLIT_PULL = "split_pull"
    EXPRESSION_HELD_BACK = "expression_held_back"
    DIRECTION_NOT_CLEAN = "direction_not_clean"
    PRESSURE_WITHOUT_CLARITY = "pressure_without_clarity"
    THRESHOLD_UNCOMMITTED = "threshold_uncommitted"


# =============================================================================
# TENSION TEMPLATES - Core of V2
# =============================================================================

PATTERN_TENSIONS = {
    DifferentiatedPatternV2.PREMATURE_MOVE: {
        "tension": "Part of you wants to move now.\nBut another part knows it hasn't settled yet.",
        "recognition": "You're already trying to push this forward—even though something in you knows it's not ready.",
        "context_scene": SceneType.DECISION,
        "what_this_is": "You have momentum. The drive is real. But the ground underneath isn't solid yet. You're reaching for resolution before the situation has actually resolved.",
        "when_it_trips_you_up": "You commit too early. You force a timeline. You create pressure where patience would serve. You mistake urgency for clarity.",
        "when_it_works": "You recognize the difference between readiness and restlessness. You let things settle before acting. You trust that timing matters.",
        "at_your_highest": "You move at exactly the right moment—not too early, not too late—because you've learned to feel when something is actually ready.",
        "where_youll_notice": [
            "When you're about to send a message you've written too quickly",
            "When someone asks for a decision and you feel pressure to answer now",
            "When you're pushing to close something that keeps reopening"
        ],
        "try_this": [
            "Say: 'Let me come back to you on this.'",
            "Notice urgency vs actual clarity. Are they the same?",
            "Delay by 24 hours. See if the answer changes."
        ],
    },
    DifferentiatedPatternV2.CLARITY_NOT_LANDED: {
        "tension": "Part of you wants certainty now.\nBut another part knows the answer hasn't arrived yet.",
        "recognition": "You're waiting for clarity that hasn't come—and the waiting is starting to feel like a problem.",
        "context_scene": SceneType.DECISION,
        "what_this_is": "Clarity comes in its own time. For you, decisions often need to marinate. The pressure to know right now is real, but forcing certainty creates false answers.",
        "when_it_trips_you_up": "You decide just to end the uncertainty. You manufacture a position because the ambiguity is uncomfortable. You mistake relief for resolution.",
        "when_it_works": "You hold the uncertainty without collapsing. You let the answer arrive rather than forcing it. You trust your process.",
        "at_your_highest": "You become someone who can sit with 'I don't know yet' without anxiety—and your clarity, when it comes, is deep and true.",
        "where_youll_notice": [
            "When someone asks where you stand and you give a half-answer",
            "When you keep changing your mind about the same thing",
            "When you feel pressure to commit before you're ready"
        ],
        "try_this": [
            "Say: 'I'm still sitting with this.'",
            "Write down what you'd say if you HAD to decide—then don't.",
            "Notice if the pressure is external or internal."
        ],
    },
    DifferentiatedPatternV2.WAITING_ON_RESPONSE: {
        "tension": "Part of you is ready to move.\nBut another part is waiting on something that isn't yours to control.",
        "recognition": "You're waiting for something that depends on someone else—and the waiting is creating its own tension.",
        "context_scene": SceneType.RELATIONSHIP,
        "what_this_is": "Your next step depends on someone else's response, decision, or action. You're ready, but the system isn't. This creates a particular kind of stuckness.",
        "when_it_trips_you_up": "You try to force the other person's hand. You create artificial urgency. You fill the waiting with anxiety instead of patience.",
        "when_it_works": "You focus on what IS yours to do. You release the timeline. You trust that their timing has its own logic.",
        "at_your_highest": "You hold space for others to move at their own pace—without losing yourself in the waiting.",
        "where_youll_notice": [
            "When you're checking your phone for a response that hasn't come",
            "When you're waiting on someone's decision to know what you're doing",
            "When you can't move until they move first"
        ],
        "try_this": [
            "Ask: 'What CAN I do while waiting?'",
            "Set a 'check-in' date instead of hovering.",
            "Name what you're waiting for out loud."
        ],
    },
    DifferentiatedPatternV2.AVOIDED_TRUTH: {
        "tension": "Part of you already knows.\nBut another part isn't ready to face it yet.",
        "recognition": "This isn't stuck because nothing is happening. It's stuck because something important isn't being faced.",
        "context_scene": SceneType.INTERNAL_AVOIDANCE,
        "what_this_is": "There's something you already know—but naming it would change things. So you keep circling without landing. The avoidance feels like confusion, but it isn't.",
        "when_it_trips_you_up": "You keep analyzing instead of admitting. You create complexity to avoid simplicity. You mistake movement for progress.",
        "when_it_works": "You say the thing you've been avoiding—to yourself first. You stop pretending you don't know. You face what's uncomfortable.",
        "at_your_highest": "You become someone who can name hard truths quickly—because you know that avoidance costs more than honesty.",
        "where_youll_notice": [
            "When you keep having the same conversation in your head",
            "When you feel stuck but can't explain why",
            "When you know what you'd tell a friend to do"
        ],
        "try_this": [
            "Write: 'The thing I'm not saying is...'",
            "Ask: 'What would change if I admitted this?'",
            "Notice what you're protecting by not knowing."
        ],
    },
    DifferentiatedPatternV2.FORCING_MOMENTUM: {
        "tension": "Part of you is trying to make this happen.\nBut another part feels the resistance you're pushing against.",
        "recognition": "You're trying to create momentum through force—and the force itself is part of the problem.",
        "context_scene": SceneType.WORK_DIRECTION,
        "what_this_is": "Effort is real. But effort against resistance creates friction, not flow. You're pushing harder instead of asking why it's not moving.",
        "when_it_trips_you_up": "You burn energy fighting friction. You mistake effort for alignment. You keep pushing after the door has closed.",
        "when_it_works": "You pause and ask: 'Why isn't this moving?' You look for ease instead of forcing through. You recognize when to redirect.",
        "at_your_highest": "You become someone who knows the difference between persistence and stubbornness—and you save your energy for what actually wants to open.",
        "where_youll_notice": [
            "When you're working harder and getting less",
            "When everything feels like a push",
            "When others seem to move easily and you're stuck"
        ],
        "try_this": [
            "Stop pushing for one day. See what happens.",
            "Ask: 'Where IS there flow right now?'",
            "Notice what you're trying to prove."
        ],
    },
    DifferentiatedPatternV2.SPLIT_PULL: {
        "tension": "Part of you wants one thing.\nBut another part wants something that contradicts it.",
        "recognition": "You're pulled between two directions—and both feel real. That's why choosing feels impossible.",
        "context_scene": SceneType.COMMITMENT,
        "what_this_is": "This isn't confusion. It's competing truths. Two parts of you want different things, and neither is wrong. The tension isn't a problem to solve—it's a signal to hold.",
        "when_it_trips_you_up": "You try to force a choice before the tension has resolved. You abandon one truth for the other. You pretend one pull isn't real.",
        "when_it_works": "You name both pulls honestly. You let them coexist without forcing resolution. You trust that clarity will emerge from holding the tension.",
        "at_your_highest": "You become someone who can hold complexity—seeing multiple truths without needing to collapse them prematurely.",
        "where_youll_notice": [
            "When you feel torn between two paths that both matter",
            "When choosing one thing feels like betraying another",
            "When you keep flip-flopping between positions"
        ],
        "try_this": [
            "Write both truths down: 'I want X' and 'I also want Y'",
            "Ask: 'What if both are true?'",
            "Stop trying to choose for now. Just hold."
        ],
    },
    DifferentiatedPatternV2.EXPRESSION_HELD_BACK: {
        "tension": "Part of you has something to say.\nBut another part is holding it back.",
        "recognition": "There's something you're not saying—and it's sitting in you, taking up space.",
        "context_scene": SceneType.CONVERSATION,
        "what_this_is": "Expression wants to happen. But something—fear, timing, protection—is keeping it inside. The silence isn't peace. It's pressure.",
        "when_it_trips_you_up": "You swallow what needs to be said. You hold resentment instead of speaking. You wait for the 'perfect moment' that never comes.",
        "when_it_works": "You find a way to say it—imperfectly, but honestly. You let expression happen even when it's messy. You stop waiting for permission.",
        "at_your_highest": "You become someone whose truth moves easily through you—not harshly, but clearly.",
        "where_youll_notice": [
            "When you rehearse conversations that never happen",
            "When you feel tension in your throat or chest",
            "When you know what you'd say if you were braver"
        ],
        "try_this": [
            "Write what you'd say if you weren't afraid.",
            "Say it to one safe person first.",
            "Ask: 'What's the cost of not saying this?'"
        ],
    },
    DifferentiatedPatternV2.DIRECTION_NOT_CLEAN: {
        "tension": "Part of you knows something needs to move.\nBut another part can't see the path clearly yet.",
        "recognition": "You know something needs to change—but the direction isn't clear. The path exists, but you can't see it yet.",
        "context_scene": SceneType.WORK_DIRECTION,
        "what_this_is": "Direction comes. But sometimes it emerges rather than appearing. You're in the gap between 'this isn't right' and 'here's what's next.'",
        "when_it_trips_you_up": "You force a direction just to have one. You choose randomly to end the uncertainty. You move for the sake of moving.",
        "when_it_works": "You stay in the question without forcing an answer. You take small steps while waiting for bigger clarity. You trust the direction will emerge.",
        "at_your_highest": "You become someone who can hold 'I don't know yet' without panic—and when direction comes, it's clear and certain.",
        "where_youll_notice": [
            "When you feel restless but don't know where to aim",
            "When options all feel equally unclear",
            "When you're asking 'What should I do?' a lot"
        ],
        "try_this": [
            "Ask: 'What's the smallest step I could take?'",
            "Notice what you're drawn toward, even slightly.",
            "Stop looking for THE answer. Look for the next step."
        ],
    },
    DifferentiatedPatternV2.PRESSURE_WITHOUT_CLARITY: {
        "tension": "Part of you feels urgent pressure to decide.\nBut another part knows the clarity to decide isn't here yet.",
        "recognition": "The pressure to decide is real—but the clarity to decide isn't. Something is pushing you before you're ready.",
        "context_scene": SceneType.DECISION,
        "what_this_is": "Pressure and clarity are different things. You can feel urgent without being ready. The pressure might be external, or it might be internal—but either way, it's ahead of your knowing.",
        "when_it_trips_you_up": "You decide just to relieve the pressure. You let urgency override accuracy. You commit to end discomfort, not because you're clear.",
        "when_it_works": "You separate pressure from readiness. You tolerate urgency without collapsing into premature action. You wait for clarity, not just relief.",
        "at_your_highest": "You become unshakeable in the face of pressure—able to hold urgency without being moved until you're genuinely ready.",
        "where_youll_notice": [
            "When someone needs an answer and you don't have one",
            "When a deadline is pushing you but clarity isn't",
            "When you feel rushed but not resolved"
        ],
        "try_this": [
            "Say: 'I'm not ready to decide yet.'",
            "Name the pressure: 'I feel rushed because...'",
            "Ask: 'What's actually urgent vs. what just feels urgent?'"
        ],
    },
    DifferentiatedPatternV2.THRESHOLD_UNCOMMITTED: {
        "tension": "Part of you is standing at a threshold.\nBut another part hasn't stepped through yet.",
        "recognition": "You're at a boundary—the door is open—but you haven't crossed it. Something is keeping you on this side.",
        "context_scene": SceneType.COMMITMENT,
        "what_this_is": "Thresholds require commitment. You can see what's on the other side, but crossing means leaving something behind. The hesitation isn't weakness—it's recognition of what's being asked.",
        "when_it_trips_you_up": "You hover indefinitely. You keep one foot on each side. You avoid the finality of actually choosing.",
        "when_it_works": "You name what you're leaving. You honor the weight of the threshold. You step through when you're ready—not before, not after.",
        "at_your_highest": "You become someone who can cross thresholds cleanly—honoring what's behind, committing to what's ahead.",
        "where_youll_notice": [
            "When you know what the next step is but haven't taken it",
            "When you're ready but not moving",
            "When you keep almost doing something but stopping short"
        ],
        "try_this": [
            "Name what you'd be leaving by stepping through.",
            "Ask: 'What's keeping me on this side?'",
            "Set a date by which you'll decide to cross—or not."
        ],
    },
}


# =============================================================================
# SIGNAL PROFILE FOR PATTERN SCORING
# =============================================================================

@dataclass
class SignalProfileV2:
    """Dimensions used for pattern scoring."""
    action_pressure: float = 0.0
    clarity_delay: float = 0.0
    external_dependency: float = 0.0
    emotional_intensity: float = 0.0
    recurrence: float = 0.0
    avoidance: float = 0.0
    expression_blockage: float = 0.0
    urgency: float = 0.0
    readiness_mismatch: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "action_pressure": self.action_pressure,
            "clarity_delay": self.clarity_delay,
            "external_dependency": self.external_dependency,
            "emotional_intensity": self.emotional_intensity,
            "recurrence": self.recurrence,
            "avoidance": self.avoidance,
            "expression_blockage": self.expression_blockage,
            "urgency": self.urgency,
            "readiness_mismatch": self.readiness_mismatch,
        }


# Pattern scoring recipes
PATTERN_RECIPES_V2 = {
    DifferentiatedPatternV2.PREMATURE_MOVE: {
        "required": {"action_pressure": 0.4, "readiness_mismatch": 0.3},
        "boosters": {"urgency": 0.3},
        "dampeners": {"external_dependency": 0.6, "clarity_delay": 0.6},
    },
    DifferentiatedPatternV2.CLARITY_NOT_LANDED: {
        "required": {"clarity_delay": 0.55, "emotional_intensity": 0.35},
        "boosters": {"urgency": 0.4},
        "dampeners": {"action_pressure": 0.6, "avoidance": 0.5},
    },
    DifferentiatedPatternV2.WAITING_ON_RESPONSE: {
        "required": {"external_dependency": 0.45, "readiness_mismatch": 0.3},
        "boosters": {"action_pressure": 0.3},
        "dampeners": {"avoidance": 0.5, "clarity_delay": 0.5},
    },
    DifferentiatedPatternV2.AVOIDED_TRUTH: {
        "required": {"avoidance": 0.45, "recurrence": 0.35},
        "boosters": {"emotional_intensity": 0.3},
        "dampeners": {"action_pressure": 0.6},
    },
    DifferentiatedPatternV2.FORCING_MOMENTUM: {
        "required": {"action_pressure": 0.5, "urgency": 0.35},
        "boosters": {"readiness_mismatch": 0.3},
        "dampeners": {"clarity_delay": 0.55},
    },
    DifferentiatedPatternV2.SPLIT_PULL: {
        "required": {"emotional_intensity": 0.4},
        "boosters": {"clarity_delay": 0.3, "recurrence": 0.3},
        "dampeners": {"action_pressure": 0.65, "avoidance": 0.5},
    },
    DifferentiatedPatternV2.EXPRESSION_HELD_BACK: {
        "required": {"expression_blockage": 0.4},
        "boosters": {"emotional_intensity": 0.3, "avoidance": 0.3},
        "dampeners": {"external_dependency": 0.5},
    },
    DifferentiatedPatternV2.DIRECTION_NOT_CLEAN: {
        "required": {"clarity_delay": 0.35, "readiness_mismatch": 0.35},
        "boosters": {"urgency": 0.3},
        "dampeners": {"action_pressure": 0.55, "avoidance": 0.5},
    },
    DifferentiatedPatternV2.PRESSURE_WITHOUT_CLARITY: {
        "required": {"urgency": 0.45, "clarity_delay": 0.35},
        "boosters": {"external_dependency": 0.3},
        "dampeners": {"action_pressure": 0.55},
    },
    DifferentiatedPatternV2.THRESHOLD_UNCOMMITTED: {
        "required": {"readiness_mismatch": 0.4, "avoidance": 0.25},
        "boosters": {"emotional_intensity": 0.3},
        "dampeners": {"urgency": 0.55},
    },
}


# =============================================================================
# USER-SPECIFIC SIGNAL EXTRACTION
# =============================================================================

def extract_user_signals(
    user_id: str,
    transit_aspects: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
) -> SignalProfileV2:
    """
    Extract user-specific signal profile.
    
    TRUTH-BASED: Uses only real signals from:
    - Transit aspects
    - HD authority/type
    - BaZi day profile
    - Pattern history
    - Journal entries
    
    NO artificial user-id variance.
    """
    profile = SignalProfileV2()
    
    # A. TRANSIT EVIDENCE (astrology)
    if transit_aspects:
        for aspect in transit_aspects:
            transit_point = aspect.get("transit_point", "").lower()
            aspect_type = aspect.get("aspect_type", "").lower()
            natal_point = aspect.get("natal_point", "").lower()
            weight = aspect.get("weight", 0.5)
            
            # Action/drive signals
            if transit_point in ["mars", "sun"] or "aries" in str(aspect):
                profile.action_pressure += weight * 0.4
            if aspect_type in ["conjunction", "opposition"]:
                profile.urgency += weight * 0.3
                
            # Clarity/confusion signals
            if transit_point in ["neptune", "moon"]:
                profile.clarity_delay += weight * 0.4
            if aspect_type == "square":
                profile.readiness_mismatch += weight * 0.3
                
            # External dependency signals
            if transit_point in ["venus"] or "7th" in str(natal_point):
                profile.external_dependency += weight * 0.4
                
            # Emotional intensity
            if transit_point in ["moon", "pluto"]:
                profile.emotional_intensity += weight * 0.4
                
            # Expression signals
            if transit_point in ["mercury"] or "3rd" in str(natal_point):
                profile.expression_blockage += weight * 0.25
                
            # Avoidance signals
            if "12th" in str(natal_point) or transit_point in ["neptune"]:
                profile.avoidance += weight * 0.4
    
    # B. HUMAN DESIGN SIGNALS
    if hd_data:
        authority = hd_data.get("authority", "").lower()
        hd_type = hd_data.get("type", "").lower()
        defined_centers = hd_data.get("defined_centers", [])
        
        # Emotional authority = clarity delay
        if "emotional" in authority:
            profile.clarity_delay += 0.4
            profile.emotional_intensity += 0.3
            
        # Sacral/Splenic = action potential
        if "sacral" in authority:
            profile.action_pressure += 0.2
        if "splenic" in authority:
            profile.action_pressure += 0.15
            
        # Open G = direction unclear
        g_defined = any("g" in c.lower() for c in defined_centers)
        if not g_defined:
            profile.clarity_delay += 0.25
            
        # Projector = external dependency
        if "projector" in hd_type:
            profile.external_dependency += 0.3
            profile.readiness_mismatch += 0.2
            
        # Open Throat = expression challenges
        throat_defined = any("throat" in c.lower() for c in defined_centers)
        if not throat_defined:
            profile.expression_blockage += 0.25
    
    # C. BAZI SIGNALS
    if bazi_data:
        day_signals = bazi_data.get("day_signals", {})
        if day_signals.get("pressure", 0) > 0.5:
            profile.urgency += 0.3
        if day_signals.get("conflict", 0) > 0.5:
            profile.readiness_mismatch += 0.3
    
    # D. PATTERN HISTORY (recurrence detection)
    if pattern_history:
        recent = [p for p in pattern_history if p.get("days_ago", 999) < 7]
        if len(recent) >= 3:
            profile.recurrence += 0.6
        elif len(recent) >= 2:
            profile.recurrence += 0.4
        elif len(recent) >= 1:
            profile.recurrence += 0.2
            
        # Check for avoidance patterns
        avoidance_count = sum(1 for p in pattern_history 
                            if "avoid" in p.get("pattern_id", "").lower())
        if avoidance_count >= 2:
            profile.avoidance += 0.3
    
    # E. JOURNAL ENTRIES (theme detection)
    if journal_entries:
        for entry in journal_entries[:10]:  # Last 10 entries
            content = entry.get("content", "").lower()
            
            if any(w in content for w in ["waiting", "stuck", "blocked"]):
                profile.external_dependency += 0.1
            if any(w in content for w in ["don't know", "not sure", "unclear", "confused"]):
                profile.clarity_delay += 0.1
            if any(w in content for w in ["say", "tell", "speak", "express"]):
                profile.expression_blockage += 0.1
            if any(w in content for w in ["avoid", "not facing", "hiding"]):
                profile.avoidance += 0.1
            if any(w in content for w in ["torn", "both", "either", "split"]):
                profile.emotional_intensity += 0.1
    
    # TRUTH-BASED: No artificial variance
    # Signals come only from real data (transits, HD, BaZi, journals, history)
    
    # Normalize all to 0-1
    for field in profile.to_dict().keys():
        val = getattr(profile, field)
        setattr(profile, field, min(1.0, max(0.0, val)))
    
    return profile


# =============================================================================
# PATTERN SCORING (No generic fallbacks)
# =============================================================================

def score_pattern_v2(profile: SignalProfileV2, pattern: DifferentiatedPatternV2) -> float:
    """Score how well a profile matches a pattern. Returns 0-1 confidence."""
    recipe = PATTERN_RECIPES_V2.get(pattern)
    if not recipe:
        return 0.0
    
    required = recipe.get("required", {})
    boosters = recipe.get("boosters", {})
    dampeners = recipe.get("dampeners", {})
    
    if not required:
        return 0.1  # Minimal score for patterns without requirements
    
    # Count required signals met
    required_met = 0
    partial_score = 0.0
    
    for dimension, threshold in required.items():
        value = getattr(profile, dimension, 0.0)
        if value >= threshold:
            required_met += 1
        else:
            # Partial credit
            partial_score += (value / threshold) * 0.3
    
    if required_met == 0 and partial_score < 0.2:
        return 0.1  # Very low score if no requirements met
    
    # Base score
    base_score = (required_met / len(required)) * 0.7 + partial_score
    
    # Booster bonus
    for dimension, threshold in boosters.items():
        if getattr(profile, dimension, 0.0) >= threshold:
            base_score += 0.1
    
    # Dampener penalty
    for dimension, threshold in dampeners.items():
        if getattr(profile, dimension, 0.0) >= threshold:
            base_score -= 0.15
    
    # Bonus for fully meeting all requirements
    if required_met == len(required):
        base_score += 0.1
    
    return max(0.0, min(1.0, base_score))


def select_pattern_v2(
    user_id: str,
    transit_aspects: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
) -> Tuple[DifferentiatedPatternV2, float, List[Tuple[DifferentiatedPatternV2, float]], SignalProfileV2]:
    """
    Select the best differentiated pattern for a user.
    
    CRITICAL: No generic fallbacks. Always returns a specific pattern.
    
    Returns:
    - Selected pattern
    - Confidence score
    - Top 3 candidates
    - Signal profile (for debugging)
    """
    # Extract user-specific signals
    profile = extract_user_signals(
        user_id=user_id,
        transit_aspects=transit_aspects,
        hd_data=hd_data,
        bazi_data=bazi_data,
        pattern_history=pattern_history,
        journal_entries=journal_entries,
    )
    
    # Score all patterns
    scores = []
    for pattern in DifferentiatedPatternV2:
        confidence = score_pattern_v2(profile, pattern)
        scores.append((pattern, confidence))
    
    # Sort by confidence
    scores.sort(key=lambda x: x[1], reverse=True)
    top_3 = scores[:3]
    
    # Select best pattern (NO generic fallback)
    best_pattern, best_score = scores[0]
    
    # If confidence is very low, use signal-based selection
    if best_score < 0.3:
        # Choose based on highest signal dimension
        signals = profile.to_dict()
        max_signal = max(signals.items(), key=lambda x: x[1])
        
        signal_to_pattern = {
            "action_pressure": DifferentiatedPatternV2.FORCING_MOMENTUM,
            "clarity_delay": DifferentiatedPatternV2.CLARITY_NOT_LANDED,
            "external_dependency": DifferentiatedPatternV2.WAITING_ON_RESPONSE,
            "emotional_intensity": DifferentiatedPatternV2.SPLIT_PULL,
            "recurrence": DifferentiatedPatternV2.AVOIDED_TRUTH,
            "avoidance": DifferentiatedPatternV2.AVOIDED_TRUTH,
            "expression_blockage": DifferentiatedPatternV2.EXPRESSION_HELD_BACK,
            "urgency": DifferentiatedPatternV2.PRESSURE_WITHOUT_CLARITY,
            "readiness_mismatch": DifferentiatedPatternV2.PREMATURE_MOVE,
        }
        
        best_pattern = signal_to_pattern.get(max_signal[0], DifferentiatedPatternV2.DIRECTION_NOT_CLEAN)
        best_score = 0.4  # Adjusted confidence
    
    return best_pattern, best_score, top_3, profile


# =============================================================================
# V2 CONTENT GENERATION
# =============================================================================

def generate_v2_content(
    pattern: DifferentiatedPatternV2,
    profile: SignalProfileV2,
    hd_data: Dict = None,
    transit_summary: str = None,
) -> Dict[str, Any]:
    """
    Generate tension-first V2 content.
    
    Structure:
    - RECOGNITION
    - TENSION (most important)
    - CONTEXT
    - WHAT THIS IS / WHEN IT TRIPS / WHEN IT WORKS / AT YOUR HIGHEST
    - WHERE YOU'LL NOTICE / TRY THIS
    - WHY THIS IS HAPPENING (collapsible)
    """
    template = PATTERN_TENSIONS.get(pattern)
    if not template:
        template = PATTERN_TENSIONS[DifferentiatedPatternV2.DIRECTION_NOT_CLEAN]
    
    # Build context line
    scene = template.get("context_scene", SceneType.DECISION)
    scene_desc = SCENE_DESCRIPTIONS.get(scene, "a situation you're navigating")
    context = f"This is likely showing up in {scene_desc}."
    
    # Build "Why This Is Happening" with system info
    why_parts = []
    
    if hd_data:
        authority = hd_data.get("authority", "")
        hd_type = hd_data.get("type", "")
        if authority:
            why_parts.append(f"Your {authority.lower()} processing creates a natural rhythm for how clarity arrives.")
        if hd_type:
            why_parts.append(f"As a {hd_type}, your timing works differently than others expect.")
    
    if transit_summary:
        why_parts.append(transit_summary)
    
    # Add pattern-specific why
    pattern_whys = {
        DifferentiatedPatternV2.CLARITY_NOT_LANDED: "Clarity emerges over time, not on demand. The pressure to know now doesn't match how you actually process.",
        DifferentiatedPatternV2.PREMATURE_MOVE: "Your drive is real, but the situation hasn't fully formed yet. Acting now would be premature.",
        DifferentiatedPatternV2.AVOIDED_TRUTH: "Something is being protected by not being named. The avoidance has a function—but it may have outlived its usefulness.",
        DifferentiatedPatternV2.FORCING_MOMENTUM: "You're expending energy against resistance. The force creates friction that slows you further.",
        DifferentiatedPatternV2.WAITING_ON_RESPONSE: "Your next step depends on factors outside your control. The waiting has its own timing.",
        DifferentiatedPatternV2.SPLIT_PULL: "Two truths are competing. This isn't confusion—it's complexity that needs holding, not solving.",
        DifferentiatedPatternV2.EXPRESSION_HELD_BACK: "Something wants to be expressed but is being held. The silence takes energy to maintain.",
        DifferentiatedPatternV2.DIRECTION_NOT_CLEAN: "The path forward hasn't fully emerged. Forcing direction now would create misalignment.",
        DifferentiatedPatternV2.PRESSURE_WITHOUT_CLARITY: "Urgency and readiness are out of sync. The pressure is real but premature.",
        DifferentiatedPatternV2.THRESHOLD_UNCOMMITTED: "You're at a crossing point but haven't stepped through. Something is keeping you on this side.",
    }
    
    why_parts.append(pattern_whys.get(pattern, ""))
    why_this_is_happening = " ".join(why_parts)
    
    return {
        "pattern_name": pattern.value.replace("_", " ").title(),
        "pattern_id": pattern.value,
        
        # Top section
        "recognition": template["recognition"],
        "tension": template["tension"],
        "context": context,
        
        # Core content
        "what_this_is": template["what_this_is"],
        "when_it_trips_you_up": template["when_it_trips_you_up"],
        "when_it_works": template["when_it_works"],
        "at_your_highest": template["at_your_highest"],
        
        # Practical
        "where_youll_notice_today": template["where_youll_notice"],
        "try_this": template["try_this"],
        
        # Collapsible
        "why_this_is_happening": why_this_is_happening,
        
        # Debug info
        "confidence": profile.to_dict(),
        "scene_type": scene.value,
    }


# =============================================================================
# HD TENSION ADDITIONS
# =============================================================================

HD_CENTER_TENSIONS = {
    "Head": {
        "defined": {
            "tension": "Your mind generates questions constantly.\nBut not every question is yours to answer.",
            "recognition_upgrade": "You've already locked onto something—and now everything is being filtered through that question.",
        },
        "undefined": {
            "tension": "You're thinking about something intensely.\nBut it might not actually be your thought.",
            "recognition_upgrade": "You're carrying mental pressure that may not be yours.",
        },
    },
    "Ajna": {
        "defined": {
            "tension": "Your mind wants certainty.\nBut the situation isn't fully clear yet.",
            "recognition_upgrade": "You've already decided how you see this—and you're defending that view.",
        },
        "undefined": {
            "tension": "You see multiple perspectives.\nBut you feel pressure to pick one.",
            "recognition_upgrade": "Your view keeps shifting based on who you're talking to.",
        },
    },
    "Throat": {
        "defined": {
            "tension": "You feel the pull to speak or act.\nBut the timing might not be right.",
            "recognition_upgrade": "You're about to say something—but you haven't checked if it's the right moment.",
        },
        "undefined": {
            "tension": "You have something to express.\nBut the words or timing aren't coming.",
            "recognition_upgrade": "You're waiting to speak—and the waiting is creating pressure.",
        },
    },
    "G Center": {
        "defined": {
            "tension": "You know your direction.\nBut you're not sure this situation fits it.",
            "recognition_upgrade": "You're steady in who you are—but something here isn't aligning.",
        },
        "undefined": {
            "tension": "You're looking for direction.\nBut it keeps shifting based on where you are.",
            "recognition_upgrade": "You're not sure who you are in this situation—and that's creating uncertainty.",
        },
    },
    "Ego": {
        "defined": {
            "tension": "You can push through this.\nBut you're not sure you should.",
            "recognition_upgrade": "You're about to commit willpower—but something is asking if it's worth it.",
        },
        "undefined": {
            "tension": "You want to prove you can.\nBut you're not sure the effort is actually required.",
            "recognition_upgrade": "You're pushing to prove yourself—when no proof may be needed.",
        },
    },
    "Solar Plexus": {
        "defined": {
            "tension": "You feel something strongly.\nBut you're not sure if it's the wave or the truth.",
            "recognition_upgrade": "Your emotions are high right now—which means clarity might not be.",
        },
        "undefined": {
            "tension": "You're feeling something intensely.\nBut it might not be your feeling.",
            "recognition_upgrade": "You've absorbed someone else's emotional state—and it's affecting your clarity.",
        },
    },
    "Sacral": {
        "defined": {
            "tension": "You have the energy to do this.\nBut your gut might be saying no.",
            "recognition_upgrade": "You can keep going—but something in you is signaling to stop.",
        },
        "undefined": {
            "tension": "You want to keep up.\nBut your actual energy doesn't match the demand.",
            "recognition_upgrade": "You're running on borrowed energy—and it's starting to show.",
        },
    },
    "Spleen": {
        "defined": {
            "tension": "Your instinct gave you a signal.\nBut your mind is second-guessing it.",
            "recognition_upgrade": "You got a hit about this—but you're not listening to it.",
        },
        "undefined": {
            "tension": "You're holding onto something.\nBut it may have passed its time.",
            "recognition_upgrade": "You're gripping something out of fear—not because it's still right.",
        },
    },
    "Root": {
        "defined": {
            "tension": "You feel pressure to act.\nBut the pressure might be self-created.",
            "recognition_upgrade": "You're creating urgency—but the situation may not actually be urgent.",
        },
        "undefined": {
            "tension": "You feel rushed.\nBut the deadline might not be yours.",
            "recognition_upgrade": "You're absorbing someone else's pressure—and it's pushing you before you're ready.",
        },
    },
}


def get_hd_center_with_tension(center_name: str, is_defined: bool) -> Dict[str, str]:
    """Get HD center content with tension addition for V2."""
    state = "defined" if is_defined else "undefined"
    tension_data = HD_CENTER_TENSIONS.get(center_name, {}).get(state, {})
    
    return {
        "tension": tension_data.get("tension", ""),
        "recognition_upgrade": tension_data.get("recognition_upgrade", ""),
    }


# =============================================================================
# MAIN V2 ENTRY POINT
# =============================================================================

def generate_mirror_v2(
    user_id: str,
    transit_aspects: List[Dict] = None,
    hd_data: Dict = None,
    bazi_data: Dict = None,
    pattern_history: List[Dict] = None,
    journal_entries: List[Dict] = None,
    transit_summary: str = None,
) -> Dict[str, Any]:
    """
    Main entry point for Mirror V2 content generation.
    
    Returns complete V2 output with:
    - Differentiated pattern (no generic fallbacks)
    - Tension-first structure
    - Scene-based context
    - Practical actions
    """
    # Select pattern
    pattern, confidence, top_3, profile = select_pattern_v2(
        user_id=user_id,
        transit_aspects=transit_aspects,
        hd_data=hd_data,
        bazi_data=bazi_data,
        pattern_history=pattern_history,
        journal_entries=journal_entries,
    )
    
    # Generate content
    content = generate_v2_content(
        pattern=pattern,
        profile=profile,
        hd_data=hd_data,
        transit_summary=transit_summary,
    )
    
    # Add debugging info
    content["debug"] = {
        "selected_pattern": pattern.value,
        "confidence": confidence,
        "top_3": [(p.value, round(c, 3)) for p, c in top_3],
        "signal_profile": profile.to_dict(),
        "user_id_hash": hashlib.md5(user_id.encode()).hexdigest()[:8],
    }
    
    return content
