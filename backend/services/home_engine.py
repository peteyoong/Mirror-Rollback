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
    
    # ======================
    # MEMORY ANCHORING FIELDS
    # ======================
    has_journal_memory: bool = False           # User has recent journal entries
    has_pattern_recurrence: bool = False       # Pattern has shown up before
    has_reflection_memory: bool = False        # User has recent reflections
    journal_anchor_phrase: Optional[str] = None  # Extracted phrase from journal
    pattern_recurrence_count: int = 0          # How many times this pattern appeared
    days_since_pattern: int = 999              # Days since last similar pattern
    memory_strength: float = 0.0               # 0-1, how strong the memory anchor is
    
    # ======================
    # LIVE ISSUE SHAPE (from journal/reflections)
    # ======================
    live_issue_summary: Optional[str] = None   # Short summary of what user is dealing with
    issue_action_verb: Optional[str] = None    # What they're DOING (pushing, avoiding, circling)
    issue_object: Optional[str] = None         # What it's about (decision, conversation, person)
    issue_state: Optional[str] = None          # Current state (stuck, almost, revisiting)
    
    # ======================
    # ANCHOR LINE (Pre-computed)
    # ======================
    anchor_line: Optional[str] = None          # "This keeps coming back", "What you've been circling"
    recognition_line: Optional[str] = None     # What they're doing right now


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
    # E. PATTERN HISTORY (Recurrence + Memory Anchoring)
    # =================================================================
    if pattern_history:
        recent = [p for p in pattern_history if p.get("days_ago", 999) < 7]
        
        if len(recent) >= 3:
            profile.recurrence += 0.6
            profile.stakes_level += 0.2  # Recurring = higher stakes
            profile.has_pattern_recurrence = True
            profile.pattern_recurrence_count = len(recent)
        elif len(recent) >= 2:
            profile.recurrence += 0.4
            profile.stakes_level += 0.1
            profile.has_pattern_recurrence = True
            profile.pattern_recurrence_count = len(recent)
        elif len(recent) >= 1:
            profile.recurrence += 0.2
            profile.has_pattern_recurrence = True
            profile.pattern_recurrence_count = 1
        
        # Track days since most recent pattern
        if recent:
            min_days = min(p.get("days_ago", 999) for p in recent)
            profile.days_since_pattern = min_days
            profile.memory_strength += 0.3 if min_days <= 2 else 0.15
        
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
    # F. JOURNAL ENTRIES (Theme Binding + Live Issue Shape Extraction)
    # =================================================================
    if journal_entries:
        profile.has_journal_memory = True
        
        # Action verbs to detect what user is DOING
        action_verbs = {
            "pushing": ["push", "force", "trying to make", "want it to"],
            "avoiding": ["avoid", "not facing", "ignoring", "pretending"],
            "circling": ["keep thinking", "going back", "can't stop", "revisiting", "back and forth"],
            "waiting": ["waiting", "stuck", "blocked", "on hold"],
            "holding": ["holding back", "not saying", "keeping", "haven't told"],
        }
        
        # Objects to detect what it's ABOUT
        issue_objects = {
            "decision": ["decide", "decision", "choose", "choice", "option"],
            "conversation": ["tell", "say", "talk", "speak", "conversation"],
            "person": ["they", "them", "he", "she", "partner", "boss", "friend"],
            "work": ["work", "job", "career", "project", "business"],
            "money": ["money", "pay", "cost", "invest", "spend"],
            "change": ["change", "move", "leave", "start", "end"],
        }
        
        # States to detect current position
        issue_states = {
            "stuck": ["stuck", "blocked", "can't move", "nowhere"],
            "almost": ["almost", "about to", "close to", "ready to"],
            "revisiting": ["keep coming back", "again", "still", "same"],
            "avoiding": ["avoiding", "not ready", "scared", "afraid"],
        }
        
        themes = {
            "waiting": 0, "stuck": 0, "blocked": 0,
            "decision": 0, "choose": 0, "decide": 0,
            "relationship": 0, "they": 0, "person": 0,
            "work": 0, "job": 0, "career": 0,
            "say": 0, "tell": 0, "speak": 0,
            "avoid": 0, "facing": 0, "truth": 0,
            "money": 0, "pay": 0, "cost": 0,
            "back and forth": 0, "keep thinking": 0, "can't stop": 0,
        }
        
        recent_text = ""
        detected_verbs = []
        detected_objects = []
        detected_states = []
        
        for entry in journal_entries[:5]:  # Last 5 entries
            content = entry.get("content", "").lower()
            recent_text += " " + content
            
            for theme in themes:
                if theme in content:
                    themes[theme] += 1
            
            # Detect action verbs
            for verb_name, verb_patterns in action_verbs.items():
                for pattern in verb_patterns:
                    if pattern in content:
                        detected_verbs.append(verb_name)
                        break
            
            # Detect objects
            for obj_name, obj_patterns in issue_objects.items():
                for pattern in obj_patterns:
                    if pattern in content:
                        detected_objects.append(obj_name)
                        break
            
            # Detect states
            for state_name, state_patterns in issue_states.items():
                for pattern in state_patterns:
                    if pattern in content:
                        detected_states.append(state_name)
                        break
        
        # Build live issue shape
        if detected_verbs:
            # Most common verb
            verb_counts = {}
            for v in detected_verbs:
                verb_counts[v] = verb_counts.get(v, 0) + 1
            profile.issue_action_verb = max(verb_counts, key=verb_counts.get)
        
        if detected_objects:
            obj_counts = {}
            for o in detected_objects:
                obj_counts[o] = obj_counts.get(o, 0) + 1
            profile.issue_object = max(obj_counts, key=obj_counts.get)
        
        if detected_states:
            state_counts = {}
            for s in detected_states:
                state_counts[s] = state_counts.get(s, 0) + 1
            profile.issue_state = max(state_counts, key=state_counts.get)
        
        # Build live issue summary
        if profile.issue_action_verb and profile.issue_object:
            verb_phrases = {
                "pushing": "trying to push through",
                "avoiding": "avoiding facing",
                "circling": "going back and forth on",
                "waiting": "stuck waiting on",
                "holding": "holding back from",
            }
            obj_phrases = {
                "decision": "a decision that won't land",
                "conversation": "something that needs to be said",
                "person": "something with someone",
                "work": "a work situation",
                "money": "something involving money",
                "change": "a change that keeps getting delayed",
            }
            verb_p = verb_phrases.get(profile.issue_action_verb, profile.issue_action_verb)
            obj_p = obj_phrases.get(profile.issue_object, profile.issue_object)
            profile.live_issue_summary = f"{verb_p} {obj_p}"
            profile.memory_strength += 0.5
        
        # Build FELT EXPERIENCE anchor lines (not analytical)
        if profile.issue_state == "revisiting" or themes["back and forth"] >= 1:
            profile.anchor_line = "You thought this was done. But it isn't."
        elif profile.issue_state == "stuck":
            profile.anchor_line = "Something in you knows it's not moving."
        elif profile.issue_state == "almost":
            profile.anchor_line = "You get close — then something pulls you back."
        elif profile.issue_state == "avoiding":
            profile.anchor_line = "There's a truth sitting under the surface."
        elif profile.has_pattern_recurrence and profile.pattern_recurrence_count >= 3:
            profile.anchor_line = "You thought you dealt with this. But here it is again."
        elif profile.has_journal_memory:
            profile.anchor_line = "There's something that won't let go."
        
        # Build FELT EXPERIENCE recognition lines (internal moments, not analysis)
        recognition_map = {
            "pushing": "You get close to moving it — then something in you pulls back.",
            "avoiding": "You look at it, then look away. Over and over.",
            "circling": "You keep coming back to it — but you can't land.",
            "waiting": "You're ready. But the next step isn't yours to take.",
            "holding": "There's something you want to say — but you stop yourself.",
        }
        if profile.issue_action_verb:
            profile.recognition_line = recognition_map.get(profile.issue_action_verb)
        
        # FELT EXPERIENCE anchor phrases (not structured)
        anchor_phrases = []
        if "keep" in recent_text and ("thinking" in recent_text or "going back" in recent_text):
            anchor_phrases.append("what won't leave your head")
        if "can't" in recent_text and ("decide" in recent_text or "stop" in recent_text):
            anchor_phrases.append("the thing you can't put down")
        if "need to" in recent_text and ("tell" in recent_text or "say" in recent_text):
            anchor_phrases.append("what's sitting in your throat")
        if "should" in recent_text and ("have" in recent_text or "do" in recent_text):
            anchor_phrases.append("what you almost do, then don't")
        
        if anchor_phrases and not profile.journal_anchor_phrase:
            profile.journal_anchor_phrase = anchor_phrases[0]
            profile.memory_strength += 0.4
        
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
        
        # Recurrence signal from journal
        if themes["back and forth"] + themes["keep thinking"] + themes["can't stop"] >= 1:
            profile.recurrence += 0.2
            profile.memory_strength += 0.2
        
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
# SCENE TYPES - What kind of real-life moment is this?
# =============================================================================

class SceneType(Enum):
    """The specific type of real-life moment this shows up in."""
    DECISION = "decision"           # A choice you're weighing
    CONVERSATION = "conversation"   # Something to say/unsaid
    ACTION = "action"               # Something to do/not do
    RELATIONSHIP = "relationship"   # Tension with someone
    INTERNAL = "internal"           # Something you're facing inside


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
# SITUATION → SCENE TYPE MAPPING
# =============================================================================

SITUATION_SCENE_TYPE = {
    HomeSituation.FORCING_PREMATURE: SceneType.ACTION,
    HomeSituation.WAITING_WITHOUT_CLARITY: SceneType.DECISION,
    HomeSituation.BLOCKED_BY_OTHERS: SceneType.RELATIONSHIP,
    HomeSituation.AVOIDING_WHAT_YOU_KNOW: SceneType.INTERNAL,
    HomeSituation.PUSHING_AGAINST_RESISTANCE: SceneType.ACTION,
    HomeSituation.TORN_BETWEEN_OPTIONS: SceneType.DECISION,
    HomeSituation.HOLDING_BACK_EXPRESSION: SceneType.CONVERSATION,
    HomeSituation.DIRECTION_UNCLEAR: SceneType.INTERNAL,
    HomeSituation.PRESSURE_WITHOUT_READINESS: SceneType.DECISION,
    HomeSituation.STANDING_AT_THRESHOLD: SceneType.ACTION,
}


# =============================================================================
# TARGETED SITUATION CONTEXTS (Memory-anchored, no generic language)
# =============================================================================

# Generic contexts (fallback when no memory)
SITUATION_CONTEXTS = {
    SceneType.DECISION: [
        "the thing you've been going back and forth on",
        "what keeps not landing",
        "what you've already decided but won't commit to",
        "what you're trying to close before you're ready",
    ],
    SceneType.CONVERSATION: [
        "what you're not saying out loud",
        "what you've been rehearsing in your head",
        "what you keep editing before it comes out",
        "what you're holding back to keep the peace",
    ],
    SceneType.ACTION: [
        "what you're trying to force through",
        "the move you keep almost making",
        "what you want done before it's ready",
        "what you're pushing against instead of around",
    ],
    SceneType.RELATIONSHIP: [
        "what's unspoken between you and them",
        "the dynamic that's been off lately",
        "what you're waiting for them to do",
        "what you're pretending is fine",
    ],
    SceneType.INTERNAL: [
        "what you already know but haven't faced",
        "what keeps showing up in your head",
        "what you're protecting yourself from seeing",
        "the truth you're circling but not landing",
    ],
}

# Memory-anchored contexts (when user has recent journal/patterns)
MEMORY_ANCHORED_CONTEXTS = {
    SceneType.DECISION: [
        "what you've been revisiting in your head",
        "what keeps coming back no matter how many times you think through it",
        "what you mentioned recently—still not resolved",
        "the thing that won't settle",
    ],
    SceneType.CONVERSATION: [
        "what you've been meaning to say",
        "what you almost said last time",
        "what you've written but not sent",
        "what's been building up",
    ],
    SceneType.ACTION: [
        "what you keep almost doing",
        "what you've been about to do for days",
        "what you're forcing before you're ready for what comes after",
        "what you're trying to move before the ground is solid",
    ],
    SceneType.RELATIONSHIP: [
        "what's been between you and them lately",
        "what you're waiting for them to see",
        "what you're pretending isn't there",
        "what keeps showing up in your interactions",
    ],
    SceneType.INTERNAL: [
        "what you already know—you've been circling it",
        "this keeps coming back for a reason",
        "what you've been avoiding looking at directly",
        "what showed up again recently",
    ],
}

# Recurrence-based contexts (when pattern has shown up multiple times)
RECURRENCE_CONTEXTS = {
    SceneType.DECISION: "this keeps coming back because you haven't actually resolved it",
    SceneType.CONVERSATION: "this keeps coming back because you haven't said it",
    SceneType.ACTION: "this keeps coming back because you haven't done it or let it go",
    SceneType.RELATIONSHIP: "this keeps coming back because it's not actually handled",
    SceneType.INTERNAL: "this keeps coming back because you know what it means",
}


# =============================================================================
# FELT EXPERIENCE HOME MESSAGES (Natural flow, internal moments, no structure)
# =============================================================================

HOME_MESSAGES = {
    HomeSituation.FORCING_PREMATURE: {
        # FELT EXPERIENCE (blended flow)
        "felt_opening": "You get close to moving this forward — then something in you pulls back.",
        "felt_body": "You thought you were ready. But there's a part that knows you're not.\n\nThe urge to close it is real. But so is the knowing that the ground still isn't solid.",
        "felt_stakes": "If you force it today, you'll end up dealing with it again — just messier.",
        "felt_move": "Don't move yet. Name what's still not clean.",
        "cta": "What are you trying to skip?",
        "scene_type": SceneType.ACTION,
    },
    HomeSituation.WAITING_WITHOUT_CLARITY: {
        "felt_opening": "You want to know — but the answer isn't arriving.",
        "felt_body": "You've thought it through. Multiple times. But something still doesn't land.\n\nPart of you wants to just decide and be done with it. But another part knows the clarity isn't there yet — you're just tired of sitting with it.",
        "felt_stakes": "Deciding now won't give you resolution. It'll give you relief — and then regret.",
        "felt_move": "Hold it one more day. Let it settle before you lock it in.",
        "cta": "What are you pretending is clear?",
        "scene_type": SceneType.DECISION,
    },
    HomeSituation.BLOCKED_BY_OTHERS: {
        "felt_opening": "You're ready to move — but this one isn't fully yours.",
        "felt_body": "There's someone else in this. And they're not doing what you need them to do.\n\nThe frustration is real. But it's also burning energy on something outside your hands.",
        "felt_stakes": "Pushing harder won't make them move faster. It'll just add friction to something already stuck.",
        "felt_move": "Name what's actually yours to do right now. Start there.",
        "cta": "What are you waiting for them to do?",
        "scene_type": SceneType.RELATIONSHIP,
    },
    HomeSituation.AVOIDING_WHAT_YOU_KNOW: {
        "felt_opening": "You already know what this is. You just haven't said it out loud yet.",
        "felt_body": "There's a truth sitting under the surface. You've seen it. You're just not ready to deal with what naming it would mean.\n\nSo you keep circling. Looking for another explanation. Hoping it's something else.",
        "felt_stakes": "The longer you avoid naming it, the heavier it gets. What you're protecting yourself from is smaller than what the avoidance is creating.",
        "felt_move": "Name it. Privately. Just to yourself. That's the first move.",
        "cta": "What are you avoiding admitting?",
        "scene_type": SceneType.INTERNAL,
    },
    HomeSituation.PUSHING_AGAINST_RESISTANCE: {
        "felt_opening": "You keep pushing — but it's not moving.",
        "felt_body": "The effort is real. But so is the friction. And the harder you push, the more resistance shows up.\n\nPart of you wants to believe if you just try harder, it'll break through. But another part can feel the energy draining without progress.",
        "felt_stakes": "More force in this direction will burn you out — not break you through.",
        "felt_move": "Stop pushing. Ask: where IS there movement right now?",
        "cta": "What would happen if you stopped pushing?",
        "scene_type": SceneType.ACTION,
    },
    HomeSituation.TORN_BETWEEN_OPTIONS: {
        "felt_opening": "You move toward one — then hesitate. Then lean toward the other.",
        "felt_body": "Both feel true. That's why you can't choose.\n\nIt's not that you're indecisive. It's that there are two real things pulling you, and picking one means letting go of the other.",
        "felt_stakes": "Forcing a choice right now won't resolve it. You'll just circle back later — probably at a worse time.",
        "felt_move": "Name both pulls. Let them both be real for now.",
        "cta": "What are you afraid of losing?",
        "scene_type": SceneType.DECISION,
    },
    HomeSituation.HOLDING_BACK_EXPRESSION: {
        "felt_opening": "There's something you want to say — but you stop yourself before it comes out.",
        "felt_body": "You've rehearsed it. Maybe more than once. But something keeps it from landing.\n\nPart of you wants to just say it and be done. But another part knows it might change things — and you're not ready for that yet.",
        "felt_stakes": "What's unsaid doesn't disappear. It builds. Into resentment. Or distance. Or something you can't take back.",
        "felt_move": "Say it somewhere safe first. Write it. Voice memo. Then decide if it needs to land.",
        "cta": "What are you not saying?",
        "scene_type": SceneType.CONVERSATION,
    },
    HomeSituation.DIRECTION_UNCLEAR: {
        "felt_opening": "Something needs to move — but you can't see where.",
        "felt_body": "You know things can't stay the way they are. But the path forward isn't clear.\n\nPart of you wants to just pick something and go. But another part knows that forcing a direction won't give you one — it'll just take you somewhere wrong.",
        "felt_stakes": "Moving without direction still costs energy. And wrong paths take time to walk back.",
        "felt_move": "Take the smallest step you can see. The next one appears after.",
        "cta": "What do you already know but won't admit?",
        "scene_type": SceneType.INTERNAL,
    },
    HomeSituation.PRESSURE_WITHOUT_READINESS: {
        "felt_opening": "You feel the pressure to decide — but you're not ready.",
        "felt_body": "Something is pressing you to move. But your clarity hasn't caught up yet.\n\nPart of you wants to just make the call and get relief. But another part knows you'd be deciding from pressure, not from knowing.",
        "felt_stakes": "Deciding under pressure won't give you peace. It'll give you something you have to undo.",
        "felt_move": "Separate the pressure from the decision. Ask: whose deadline is this really?",
        "cta": "Whose pressure is this?",
        "scene_type": SceneType.DECISION,
    },
    HomeSituation.STANDING_AT_THRESHOLD: {
        "felt_opening": "You're right at the edge — but you haven't stepped through.",
        "felt_body": "The door is open. You've looked at what's on the other side. But something is keeping you on this side.\n\nPart of you is ready to cross. But another part is still holding onto what you'd be leaving behind.",
        "felt_stakes": "Hovering at the edge drains more than crossing or staying. The in-between costs the most.",
        "felt_move": "Name what you'd be leaving. Then decide if you're ready to let it go.",
        "cta": "What are you not ready to let go of?",
        "scene_type": SceneType.ACTION,
    },
}


# =============================================================================
# SITUATION SELECTION (Truth-Based, Discriminative)
# =============================================================================

def select_home_situation(profile: LiveSignalProfile) -> Tuple[HomeSituation, float]:
    """
    Select the single strongest live situation based on real signals.
    NO artificial variance. Pure signal-based selection.
    
    Uses DISCRIMINATIVE scoring - situations require specific signal thresholds.
    """
    
    scores = {}
    
    # FORCING_PREMATURE: high action + urgency + low clarity
    # REQUIRED: action_pressure > 0.3 AND (urgency > 0.3 OR clarity_delay > 0.3)
    if profile.action_pressure > 0.3 and (profile.urgency > 0.3 or profile.clarity_delay > 0.3):
        scores[HomeSituation.FORCING_PREMATURE] = (
            profile.action_pressure * 0.45 +
            profile.urgency * 0.3 +
            profile.clarity_delay * 0.25
        )
    else:
        scores[HomeSituation.FORCING_PREMATURE] = 0.0
    
    # WAITING_WITHOUT_CLARITY: high clarity delay + low action
    # REQUIRED: clarity_delay > 0.3 AND action_pressure < 0.4
    if profile.clarity_delay > 0.3 and profile.action_pressure < 0.4:
        scores[HomeSituation.WAITING_WITHOUT_CLARITY] = (
            profile.clarity_delay * 0.5 +
            profile.emotional_intensity * 0.3 +
            (1 - profile.action_pressure) * 0.2
        )
    else:
        scores[HomeSituation.WAITING_WITHOUT_CLARITY] = 0.0
    
    # BLOCKED_BY_OTHERS: external dependency dominant
    # REQUIRED: external_dependency > 0.35
    if profile.external_dependency > 0.35:
        scores[HomeSituation.BLOCKED_BY_OTHERS] = (
            profile.external_dependency * 0.6 +
            profile.readiness_mismatch * 0.25 +
            profile.action_pressure * 0.15
        )
    else:
        scores[HomeSituation.BLOCKED_BY_OTHERS] = 0.0
    
    # AVOIDING_WHAT_YOU_KNOW: avoidance dominant
    # REQUIRED: avoidance > 0.3 OR recurrence > 0.4
    if profile.avoidance > 0.3 or profile.recurrence > 0.4:
        scores[HomeSituation.AVOIDING_WHAT_YOU_KNOW] = (
            profile.avoidance * 0.5 +
            profile.recurrence * 0.35 +
            profile.emotional_intensity * 0.15
        )
    else:
        scores[HomeSituation.AVOIDING_WHAT_YOU_KNOW] = 0.0
    
    # PUSHING_AGAINST_RESISTANCE: action + readiness mismatch
    # REQUIRED: action_pressure > 0.35 AND readiness_mismatch > 0.25
    if profile.action_pressure > 0.35 and profile.readiness_mismatch > 0.25:
        scores[HomeSituation.PUSHING_AGAINST_RESISTANCE] = (
            profile.action_pressure * 0.45 +
            profile.readiness_mismatch * 0.4 +
            profile.urgency * 0.15
        )
    else:
        scores[HomeSituation.PUSHING_AGAINST_RESISTANCE] = 0.0
    
    # TORN_BETWEEN_OPTIONS: emotional intensity + clarity delay + low urgency
    # REQUIRED: emotional_intensity > 0.25 AND clarity_delay > 0.25
    if profile.emotional_intensity > 0.25 and profile.clarity_delay > 0.25:
        scores[HomeSituation.TORN_BETWEEN_OPTIONS] = (
            profile.emotional_intensity * 0.45 +
            profile.clarity_delay * 0.35 +
            profile.recurrence * 0.2
        )
    else:
        scores[HomeSituation.TORN_BETWEEN_OPTIONS] = 0.0
    
    # HOLDING_BACK_EXPRESSION: expression blockage dominant
    # REQUIRED: expression_blockage > 0.3
    if profile.expression_blockage > 0.3:
        scores[HomeSituation.HOLDING_BACK_EXPRESSION] = (
            profile.expression_blockage * 0.7 +
            profile.emotional_intensity * 0.2 +
            profile.avoidance * 0.1
        )
    else:
        scores[HomeSituation.HOLDING_BACK_EXPRESSION] = 0.0
    
    # DIRECTION_UNCLEAR: low clarity, low action, low urgency (genuine confusion)
    # REQUIRED: clarity_delay > 0.25 AND action_pressure < 0.3 AND urgency < 0.35
    # Also: expression_blockage must be LOW (otherwise it's not confusion, it's held expression)
    if profile.clarity_delay > 0.25 and profile.action_pressure < 0.3 and profile.urgency < 0.35 and profile.expression_blockage < 0.4:
        scores[HomeSituation.DIRECTION_UNCLEAR] = (
            profile.clarity_delay * 0.5 +
            profile.readiness_mismatch * 0.3 +
            (1 - profile.action_pressure) * 0.2
        )
    else:
        scores[HomeSituation.DIRECTION_UNCLEAR] = 0.0
    
    # PRESSURE_WITHOUT_READINESS: urgency + clarity delay + external pressure
    # REQUIRED: urgency > 0.3 AND clarity_delay > 0.2
    if profile.urgency > 0.3 and profile.clarity_delay > 0.2:
        scores[HomeSituation.PRESSURE_WITHOUT_READINESS] = (
            profile.urgency * 0.45 +
            profile.clarity_delay * 0.3 +
            profile.external_dependency * 0.25
        )
    else:
        scores[HomeSituation.PRESSURE_WITHOUT_READINESS] = 0.0
    
    # STANDING_AT_THRESHOLD: readiness mismatch + avoidance (near-decision)
    # REQUIRED: readiness_mismatch > 0.3 AND avoidance > 0.2
    if profile.readiness_mismatch > 0.3 and profile.avoidance > 0.2:
        scores[HomeSituation.STANDING_AT_THRESHOLD] = (
            profile.readiness_mismatch * 0.45 +
            profile.avoidance * 0.35 +
            profile.emotional_intensity * 0.2
        )
    else:
        scores[HomeSituation.STANDING_AT_THRESHOLD] = 0.0
    
    # Apply stakes multiplier
    for situation in scores:
        scores[situation] *= (1 + profile.stakes_level * 0.3)
    
    # Select highest - FALLBACK if all scores are 0
    best = max(scores.items(), key=lambda x: x[1])
    
    # If all situations scored 0, use intelligent fallback based on dominant signals
    if best[1] == 0:
        # Pick fallback based on highest individual signals
        signal_map = {
            "action_pressure": HomeSituation.FORCING_PREMATURE,
            "clarity_delay": HomeSituation.WAITING_WITHOUT_CLARITY,
            "external_dependency": HomeSituation.BLOCKED_BY_OTHERS,
            "avoidance": HomeSituation.AVOIDING_WHAT_YOU_KNOW,
            "expression_blockage": HomeSituation.HOLDING_BACK_EXPRESSION,
            "readiness_mismatch": HomeSituation.STANDING_AT_THRESHOLD,
            "urgency": HomeSituation.PRESSURE_WITHOUT_READINESS,
            "emotional_intensity": HomeSituation.TORN_BETWEEN_OPTIONS,
            "recurrence": HomeSituation.AVOIDING_WHAT_YOU_KNOW,
        }
        
        # Find the highest signal
        signal_values = [
            (profile.action_pressure, "action_pressure"),
            (profile.clarity_delay, "clarity_delay"),
            (profile.external_dependency, "external_dependency"),
            (profile.avoidance, "avoidance"),
            (profile.expression_blockage, "expression_blockage"),
            (profile.readiness_mismatch, "readiness_mismatch"),
            (profile.urgency, "urgency"),
            (profile.emotional_intensity, "emotional_intensity"),
            (profile.recurrence, "recurrence"),
        ]
        highest_signal = max(signal_values, key=lambda x: x[0])
        
        if highest_signal[0] > 0.1:
            fallback_situation = signal_map.get(highest_signal[1], HomeSituation.DIRECTION_UNCLEAR)
            return fallback_situation, highest_signal[0]
        else:
            # Default fallback
            return HomeSituation.DIRECTION_UNCLEAR, 0.3
    
    return best[0], min(1.0, best[1])


# =============================================================================
# HOME MESSAGE GENERATION (with Memory Anchoring)
# =============================================================================

def get_targeted_context(situation: HomeSituation, profile: LiveSignalProfile) -> str:
    """
    Generate ONE specific, memory-anchored context.
    
    Priority:
    1. Journal anchor phrase (if extracted)
    2. Recurrence context (if pattern is recurring)
    3. Memory-anchored context (if has journal/pattern memory)
    4. Signal-based context (fallback)
    """
    scene_type = SITUATION_SCENE_TYPE.get(situation, SceneType.INTERNAL)
    
    # PRIORITY 1: Journal anchor phrase (most specific)
    if profile.journal_anchor_phrase:
        return profile.journal_anchor_phrase
    
    # PRIORITY 2: Recurrence context (pattern keeps coming back)
    if profile.has_pattern_recurrence and profile.pattern_recurrence_count >= 3:
        return RECURRENCE_CONTEXTS.get(scene_type, "this keeps coming back")
    
    # PRIORITY 3: Memory-anchored context (user has recent journal/patterns)
    if profile.has_journal_memory or profile.has_pattern_recurrence:
        memory_contexts = MEMORY_ANCHORED_CONTEXTS.get(scene_type, MEMORY_ANCHORED_CONTEXTS[SceneType.INTERNAL])
        
        # Choose based on recency/strength
        if profile.days_since_pattern <= 1:
            idx = 3  # "what showed up again recently" / most immediate
        elif profile.memory_strength > 0.5:
            idx = 0  # "what you've been revisiting" / strong anchor
        elif profile.recurrence > 0.3:
            idx = 1  # "keeps coming back" variant
        else:
            idx = 2  # moderate anchor
        
        return memory_contexts[min(idx, len(memory_contexts) - 1)]
    
    # PRIORITY 4: Signal-based context (no memory, use current signals)
    contexts = SITUATION_CONTEXTS.get(scene_type, SITUATION_CONTEXTS[SceneType.INTERNAL])
    
    # Choose the most specific context based on profile signals
    idx = 0
    
    if scene_type == SceneType.DECISION:
        if profile.urgency > 0.4:
            idx = 0  # "the thing you've been going back and forth on"
        elif profile.recurrence > 0.3:
            idx = 1  # "what keeps not landing"
        elif profile.clarity_delay > 0.4:
            idx = 2  # "what you've already decided but won't commit to"
        else:
            idx = 3  # "what you're trying to close before you're ready"
    
    elif scene_type == SceneType.CONVERSATION:
        if profile.avoidance > 0.3:
            idx = 0  # "what you're not saying out loud"
        elif profile.emotional_intensity > 0.3:
            idx = 1  # "what you've been rehearsing in your head"
        elif profile.action_pressure > 0.3:
            idx = 2  # "what you keep editing before it comes out"
        else:
            idx = 3  # "what you're holding back to keep the peace"
    
    elif scene_type == SceneType.ACTION:
        if profile.urgency > 0.4:
            idx = 0  # "what you're trying to force through"
        elif profile.readiness_mismatch > 0.3:
            idx = 1  # "the move you keep almost making"
        elif profile.action_pressure > 0.4:
            idx = 2  # "what you want done before it's ready"
        else:
            idx = 3  # "what you're pushing against instead of around"
    
    elif scene_type == SceneType.RELATIONSHIP:
        if profile.expression_blockage > 0.3:
            idx = 0  # "what's unspoken between you and them"
        elif profile.avoidance > 0.3:
            idx = 1  # "the dynamic that's been off lately"
        elif profile.external_dependency > 0.4:
            idx = 2  # "what you're waiting for them to do"
        else:
            idx = 3  # "what you're pretending is fine"
    
    elif scene_type == SceneType.INTERNAL:
        if profile.avoidance > 0.4:
            idx = 0  # "what you already know but haven't faced"
        elif profile.recurrence > 0.3:
            idx = 1  # "what keeps showing up in your head"
        elif profile.emotional_intensity > 0.3:
            idx = 2  # "what you're protecting yourself from seeing"
        else:
            idx = 3  # "the truth you're circling but not landing"
    
    return contexts[min(idx, len(contexts) - 1)]


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
    Generate FELT EXPERIENCE Home message.
    
    Outputs as ONE continuous natural flow, not segmented structure.
    Uses internal moments: hesitation, pull/push, almost doing, stopping yourself.
    
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
    
    # Get scene type
    scene_type = SITUATION_SCENE_TYPE.get(situation, SceneType.INTERNAL)
    
    # =====================================================
    # BUILD FELT EXPERIENCE MESSAGE (Natural Flow)
    # =====================================================
    
    # Use felt_opening (with memory override if available)
    if profile.recognition_line:
        felt_opening = profile.recognition_line
    else:
        felt_opening = message.get("felt_opening", "")
    
    # Add anchor context for memory-bound users
    if profile.anchor_line and profile.memory_strength > 0.3:
        felt_opening = f"{profile.anchor_line}\n\n{felt_opening}"
    
    # Get the body (tension + internal moments)
    felt_body = message.get("felt_body", "")
    
    # Get stakes
    felt_stakes = message.get("felt_stakes", "")
    
    # Get wise move
    felt_move = message.get("felt_move", "")
    
    # Get CTA
    cta = message.get("cta", "")
    
    # Build the FULL MESSAGE as one natural flow
    full_message_parts = []
    
    if felt_opening:
        full_message_parts.append(felt_opening)
    
    if felt_body:
        full_message_parts.append(felt_body)
    
    if felt_stakes:
        full_message_parts.append(felt_stakes)
    
    if felt_move:
        full_message_parts.append(felt_move)
    
    full_message = "\n\n".join(full_message_parts)
    
    return {
        # FELT EXPERIENCE OUTPUT (Single natural flow)
        "full_message": full_message,
        "cta": cta,
        
        # Individual parts (for flexible rendering)
        "felt_opening": felt_opening,
        "felt_body": felt_body,
        "felt_stakes": felt_stakes,
        "felt_move": felt_move,
        
        # Scene & Targeting
        "scene_type": scene_type.value,
        
        # Memory Anchoring Info
        "memory_anchored": profile.has_journal_memory or profile.has_pattern_recurrence,
        "memory_strength": round(profile.memory_strength, 2),
        "recurrence_count": profile.pattern_recurrence_count,
        "live_issue_summary": profile.live_issue_summary,
        
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
            "has_journal_memory": profile.has_journal_memory,
            "has_pattern_recurrence": profile.has_pattern_recurrence,
            "anchor_line": profile.anchor_line,
            "recognition_line": profile.recognition_line,
        },
    }


# =============================================================================
# FORMATTED HOME OUTPUT (Felt Experience)
# =============================================================================

def format_home_for_display(home: Dict[str, Any]) -> str:
    """Format Home message as one continuous felt experience."""
    memory_indicator = "📍 MEMORY-BOUND" if home.get("memory_anchored") else "📎 SIGNAL-BASED"
    
    lines = [
        home.get("full_message", ""),
        "",
        f"[{home.get('cta', '')}]",
        "",
        f"---",
        f"{memory_indicator} | {home.get('situation', '')}",
    ]
    return "\n".join(lines)
