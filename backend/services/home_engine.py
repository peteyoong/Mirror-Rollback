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
# ACTION PINNING - Pre-Action Interrupt Layer
# Maps situations to EXACT actions the user is about to take
# =============================================================================

# Situation → Specific Action Verb Mapping
SITUATION_ACTION_VERBS = {
    HomeSituation.FORCING_PREMATURE: {
        "primary": "signing off on this",
        "variants": ["locking this in", "saying yes", "committing to this"],
    },
    HomeSituation.WAITING_WITHOUT_CLARITY: {
        "primary": "deciding on this",
        "variants": ["picking one", "closing this out", "making the call"],
    },
    HomeSituation.BLOCKED_BY_OTHERS: {
        "primary": "pushing them again",
        "variants": ["sending another message", "asking them again", "following up again"],
    },
    HomeSituation.AVOIDING_WHAT_YOU_KNOW: {
        "primary": "pretending you don't know",
        "variants": ["ignoring what you see", "looking away again", "telling yourself it's fine"],
    },
    HomeSituation.PUSHING_AGAINST_RESISTANCE: {
        "primary": "forcing this through",
        "variants": ["pushing harder", "trying again the same way", "making it happen now"],
    },
    HomeSituation.TORN_BETWEEN_OPTIONS: {
        "primary": "picking one just to end it",
        "variants": ["forcing yourself to choose", "closing a door prematurely", "committing before you're ready"],
    },
    HomeSituation.HOLDING_BACK_EXPRESSION: {
        "primary": "sending that message",
        "variants": ["saying what's in your head", "replying now", "bringing it up"],
    },
    HomeSituation.DIRECTION_UNCLEAR: {
        "primary": "picking a direction just to have one",
        "variants": ["moving without seeing", "starting just to start", "forcing motion"],
    },
    HomeSituation.PRESSURE_WITHOUT_READINESS: {
        "primary": "deciding because they're waiting",
        "variants": ["giving an answer to end the pressure", "committing under their timeline", "saying yes to stop the ask"],
    },
    HomeSituation.STANDING_AT_THRESHOLD: {
        "primary": "crossing before you've let go",
        "variants": ["stepping through without releasing", "moving while still holding on", "leaving without saying goodbye"],
    },
}

# Scene Type → Generic Action Fallbacks (when no specific situation)
SCENE_ACTION_FALLBACKS = {
    SceneType.DECISION: ["deciding now", "making the call", "picking one", "closing this out"],
    SceneType.CONVERSATION: ["sending that message", "saying it", "replying now", "bringing it up"],
    SceneType.ACTION: ["signing off", "locking this in", "saying yes", "committing"],
    SceneType.RELATIONSHIP: ["pushing them again", "reaching out", "forcing a response", "asking again"],
    SceneType.INTERNAL: ["ignoring it", "pretending it's fine", "moving past it", "looking away"],
}


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
# DAILY MASTER GUIDE HOME MESSAGES
# Structure: HEADLINE → LIVE READ → DON'T DO THIS → IF YOU IGNORE → INSTEAD → CTA
# =============================================================================

# Decision Signal Types
class DecisionSignal:
    HOLD = "hold"      # This isn't ready yet
    MOVE = "move"      # You already know — act
    CLARIFY = "clarify"  # Name the real issue first

# Life Arenas (no vague language)
class LifeArena:
    DECISION = "decision"       # work / decision
    COMMITMENT = "commitment"   # money / commitment  
    CONVERSATION = "conversation"  # message / conversation
    RELATIONSHIP = "relationship"  # relationship / tension
    INTERNAL = "internal"       # internal / avoidance

HOME_MESSAGES = {
    HomeSituation.FORCING_PREMATURE: {
        "arena": LifeArena.COMMITMENT,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to close this — even though it still doesn't sit right.",
        "reinforcement": "You can feel it's off.\nYou're pushing anyway.",
        "pressure": "The moment you force this through, you'll feel it slip again.",
        "shift": "Stop. Don't close it. Say what's actually wrong.",
        # LEGACY FIELDS (kept for backward compatibility)
        "headline": "You're about to close this — even though it still doesn't sit right.",
        "live_read": "You can feel it's off.\nYou're pushing anyway.",
        "dont_do": "Don't sign off on this today.",
        "if_ignore": "The moment you force this through, you'll feel it slip again.",
        "instead": "Stop. Don't close it. Say what's actually wrong.",
        "cta": "What's actually wrong?",
        "decision_signal": DecisionSignal.HOLD,
        "scene_type": SceneType.ACTION,
        "pinned_action": "signing off on this",
    },
    HomeSituation.WAITING_WITHOUT_CLARITY: {
        "arena": LifeArena.DECISION,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to decide — even though you still don't know.",
        "reinforcement": "You keep thinking it through.\nYou keep landing nowhere.",
        "pressure": "The moment you force this call, you'll start second-guessing it.",
        "shift": "Stop. Don't decide. Name the one thing you're still missing.",
        # LEGACY FIELDS
        "headline": "You're about to decide — even though you still don't know.",
        "live_read": "You keep thinking it through.\nYou keep landing nowhere.",
        "dont_do": "Don't force the call today.",
        "if_ignore": "The moment you force this call, you'll start second-guessing it.",
        "instead": "Stop. Don't decide. Name the one thing you're still missing.",
        "cta": "What are you still missing?",
        "decision_signal": DecisionSignal.HOLD,
        "scene_type": SceneType.DECISION,
        "pinned_action": "making the call",
    },
    HomeSituation.BLOCKED_BY_OTHERS: {
        "arena": LifeArena.RELATIONSHIP,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to follow up again — even though they still haven't replied.",
        "reinforcement": "You check for their response.\nNothing.\nYou're about to send another one.",
        "pressure": "The moment you send it, you become the one who keeps pushing.",
        "shift": "Stop. Close what's yours. Leave theirs alone.",
        # LEGACY FIELDS
        "headline": "You're about to follow up again — even though they still haven't replied.",
        "live_read": "You check for their response.\nNothing.\nYou're about to send another one.",
        "dont_do": "Don't send that follow-up.",
        "if_ignore": "The moment you send it, you become the one who keeps pushing.",
        "instead": "Stop. Close what's yours. Leave theirs alone.",
        "cta": "What can you finish without them?",
        "decision_signal": DecisionSignal.MOVE,
        "scene_type": SceneType.RELATIONSHIP,
        "pinned_action": "pushing them again",
    },
    HomeSituation.AVOIDING_WHAT_YOU_KNOW: {
        "arena": LifeArena.INTERNAL,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to move past this — even though you already know what's wrong.",
        "reinforcement": "You can see the problem.\nYou keep trying to close it anyway.",
        "pressure": "The moment you push through, you'll feel it resurface.",
        "shift": "Stop. Don't finish it. Say what's actually wrong.",
        # LEGACY FIELDS
        "headline": "You're about to move past this — even though you already know what's wrong.",
        "live_read": "You can see the problem.\nYou keep trying to close it anyway.",
        "dont_do": "Don't tell yourself it's fine.",
        "if_ignore": "The moment you push through, you'll feel it resurface.",
        "instead": "Stop. Don't finish it. Say what's actually wrong.",
        "cta": "What's actually wrong?",
        "decision_signal": DecisionSignal.CLARIFY,
        "scene_type": SceneType.INTERNAL,
        "pinned_action": "pretending you don't know",
    },
    HomeSituation.PUSHING_AGAINST_RESISTANCE: {
        "arena": LifeArena.COMMITMENT,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to try again — the exact same way it didn't work before.",
        "reinforcement": "You push.\nIt doesn't move.\nYou're about to push harder.",
        "pressure": "The moment you force it again, you'll just be more tired and still stuck.",
        "shift": "Stop. Don't push here. Find where there's actual movement.",
        # LEGACY FIELDS
        "headline": "You're about to try again — the exact same way it didn't work before.",
        "live_read": "You push.\nIt doesn't move.\nYou're about to push harder.",
        "dont_do": "Don't force this through today.",
        "if_ignore": "The moment you force it again, you'll just be more tired and still stuck.",
        "instead": "Stop. Don't push here. Find where there's actual movement.",
        "cta": "Where is there actual movement?",
        "decision_signal": DecisionSignal.HOLD,
        "scene_type": SceneType.ACTION,
        "pinned_action": "forcing this through",
    },
    HomeSituation.TORN_BETWEEN_OPTIONS: {
        "arena": LifeArena.DECISION,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to pick one — just to end the back and forth.",
        "reinforcement": "You lean one way.\nYou pull back.\nYou're about to just choose.",
        "pressure": "The moment you pick, you'll carry the doubt into whatever you chose.",
        "shift": "Stop. Don't pick yet. Name what you'd lose on each side.",
        # LEGACY FIELDS
        "headline": "You're about to pick one — just to end the back and forth.",
        "live_read": "You lean one way.\nYou pull back.\nYou're about to just choose.",
        "dont_do": "Don't commit just to end the discomfort.",
        "if_ignore": "The moment you pick, you'll carry the doubt into whatever you chose.",
        "instead": "Stop. Don't pick yet. Name what you'd lose on each side.",
        "cta": "What would you lose on each side?",
        "decision_signal": DecisionSignal.CLARIFY,
        "scene_type": SceneType.DECISION,
        "pinned_action": "picking one just to end it",
    },
    HomeSituation.HOLDING_BACK_EXPRESSION: {
        "arena": LifeArena.CONVERSATION,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to soften it again — even though you know what you actually want to say.",
        "reinforcement": "You write it.\nYou rewrite it.\nYou're about to delete the real part.",
        "pressure": "The moment you send the soft version, you'll wish you'd said the real one.",
        "shift": "Stop. Write the real version first. You don't have to send it yet.",
        # LEGACY FIELDS
        "headline": "You're about to soften it again — even though you know what you actually want to say.",
        "live_read": "You write it.\nYou rewrite it.\nYou're about to delete the real part.",
        "dont_do": "Don't smooth this over again.",
        "if_ignore": "The moment you send the soft version, you'll wish you'd said the real one.",
        "instead": "Stop. Write the real version first. You don't have to send it yet.",
        "cta": "What's the real version?",
        "decision_signal": DecisionSignal.CLARIFY,
        "scene_type": SceneType.CONVERSATION,
        "pinned_action": "smoothing this over",
    },
    HomeSituation.DIRECTION_UNCLEAR: {
        "arena": LifeArena.INTERNAL,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to pick a direction — even though you can't see past the first step.",
        "reinforcement": "You look for clarity.\nYou don't find it.\nYou're about to move anyway.",
        "pressure": "The moment you commit blind, you'll start undoing it.",
        "shift": "Stop. Find the one step you can actually see. Take only that one.",
        # LEGACY FIELDS
        "headline": "You're about to pick a direction — even though you can't see past the first step.",
        "live_read": "You look for clarity.\nYou don't find it.\nYou're about to move anyway.",
        "dont_do": "Don't pick just to have a direction.",
        "if_ignore": "The moment you commit blind, you'll start undoing it.",
        "instead": "Stop. Find the one step you can actually see. Take only that one.",
        "cta": "What's the one step you can actually see?",
        "decision_signal": DecisionSignal.HOLD,
        "scene_type": SceneType.INTERNAL,
        "pinned_action": "picking a direction blindly",
    },
    HomeSituation.PRESSURE_WITHOUT_READINESS: {
        "arena": LifeArena.DECISION,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to say yes — even though your body is still saying wait.",
        "reinforcement": "They're waiting.\nYou can feel the pressure.\nYou're about to answer.",
        "pressure": "The moment you say yes, you'll start regretting it.",
        "shift": "Stop. Their deadline isn't yours. Answer when you actually know.",
        # LEGACY FIELDS
        "headline": "You're about to say yes — even though your body is still saying wait.",
        "live_read": "They're waiting.\nYou can feel the pressure.\nYou're about to answer.",
        "dont_do": "Don't answer just to end the asking.",
        "if_ignore": "The moment you say yes, you'll start regretting it.",
        "instead": "Stop. Their deadline isn't yours. Answer when you actually know.",
        "cta": "What would you decide if no one was waiting?",
        "decision_signal": DecisionSignal.HOLD,
        "scene_type": SceneType.DECISION,
        "pinned_action": "saying yes because they're waiting",
    },
    HomeSituation.STANDING_AT_THRESHOLD: {
        "arena": LifeArena.COMMITMENT,
        # V5 IMMINENT INTERRUPTION SYSTEM
        "core_line": "You're about to step through — even though you're still gripping what's behind you.",
        "reinforcement": "You look forward.\nYou reach back.\nYou're about to move anyway.",
        "pressure": "The moment you cross while holding on, you'll feel torn in half.",
        "shift": "Stop. Name what you're leaving. Out loud. Then decide.",
        # LEGACY FIELDS
        "headline": "You're about to step through — even though you're still gripping what's behind you.",
        "live_read": "You look forward.\nYou reach back.\nYou're about to move anyway.",
        "dont_do": "Don't step through while holding on.",
        "if_ignore": "The moment you cross while holding on, you'll feel torn in half.",
        "instead": "Stop. Name what you're leaving. Out loud. Then decide.",
        "cta": "What are you still holding onto?",
        "decision_signal": DecisionSignal.CLARIFY,
        "scene_type": SceneType.ACTION,
        "pinned_action": "crossing while holding on",
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
    
    # Get decision signal
    decision_signal = message.get("decision_signal", DecisionSignal.HOLD)
    
    # Get arena
    arena = message.get("arena", LifeArena.INTERNAL)
    
    # =====================================================
    # BUILD V3 RECOGNITION STRUCTURE (4-Part)
    # =====================================================
    
    # V3 STRUCTURE: core_line, reinforcement, pressure, shift
    core_line = message.get("core_line", "")
    reinforcement = message.get("reinforcement", "")
    pressure = message.get("pressure", "")
    shift = message.get("shift", "")
    
    # LEGACY FIELDS (kept for backward compatibility)
    headline = message.get("headline", core_line)  # Falls back to core_line
    live_read = message.get("live_read", reinforcement)
    dont_do = message.get("dont_do", "")
    if_ignore = message.get("if_ignore", pressure)  # if_ignore maps to pressure
    instead = message.get("instead", shift)
    cta = message.get("cta", "")
    
    return {
        # V3 RECOGNITION STRUCTURE (Primary)
        "core_line": core_line,
        "reinforcement": reinforcement,
        "pressure": pressure,
        "shift": shift,
        
        # LEGACY FIELDS (Backward Compatibility)
        "headline": headline,
        "live_read": live_read,
        "dont_do": dont_do,
        "if_ignore": if_ignore,
        "instead": instead,
        "cta": cta,
        
        # Arena
        "arena": arena,
        
        # DECISION SIGNAL
        "decision_signal": decision_signal,
        
        # ACTION PINNING
        "pinned_action": message.get("pinned_action", ""),
        
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
# FORMATTED HOME OUTPUT (Daily Master Guide Structure)
# =============================================================================

def format_home_for_display(home: Dict[str, Any]) -> str:
    """Format Home message as V3 Recognition Structure (4-Part)."""
    # Decision signal indicator
    signal = home.get("decision_signal", "hold")
    signal_icons = {
        "hold": "⏸️ HOLD",
        "move": "▶️ MOVE",
        "clarify": "🔍 CLARIFY",
    }
    signal_display = signal_icons.get(signal, "⏸️ HOLD")
    
    # Arena indicator
    arena = home.get("arena", "internal")
    arena_display = arena.upper() if arena else "INTERNAL"
    
    lines = [
        # CORE LINE (Recognition hit)
        home.get("core_line", ""),
        "",
        # REINFORCEMENT (Scene behavior)
        home.get("reinforcement", ""),
        "",
        # PRESSURE (Consequence / Tension)
        home.get("pressure", ""),
        "",
        # SHIFT (Actionable move)
        f"→ {home.get('shift', '')}",
        "",
        f"---",
        f"{signal_display} | {arena_display} | {home.get('situation', '')}",
    ]
    return "\n".join(lines)
