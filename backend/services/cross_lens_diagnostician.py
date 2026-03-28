"""
Cross-Lens Pattern Diagnostician
================================

Transforms Mirror from a multi-lens summarizer into a diagnostic practitioner.

Instead of:
  - Astrology says X
  - Human Design says Y
  - History shows Z
  - Summary: signals are converging

We produce:
  1. Stable Constitution (who you are across lenses)
  2. Current Activation (what kind of moment this is)
  3. History Pattern (where this has appeared before)
  4. Core Diagnosis (one integrated interpretation)
  5. Lens Evidence (supporting details, not separate outputs)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# MOMENT TYPES - How we classify the current moment
# =============================================================================

class MomentType(Enum):
    FORCING_WINDOW = "forcing_window"
    PAUSE_STALL = "pause_stall"
    REVIEW_RECALIBRATION = "review_recalibration"
    OVERREACH_RISK = "overreach_risk"
    PREMATURE_INITIATION = "premature_initiation"
    UNRESOLVED_WAVE = "unresolved_wave"
    STRUCTURE_NOT_READY = "structure_not_ready"
    CLEAN_INITIATION = "clean_initiation"
    CONSOLIDATION = "consolidation"
    THRESHOLD_MOMENT = "threshold_moment"


# =============================================================================
# STABLE CONSTITUTION - User's inherent patterns across lenses
# =============================================================================

class StableConstitution:
    """Represents a user's stable pattern tendencies across all lenses."""
    
    def __init__(
        self,
        action_style: str,
        clarity_style: str,
        pressure_distortion: str,
        recurring_gift: str,
        recurring_failure_mode: str,
        timing_tendency: str,
        decision_pattern: str
    ):
        self.action_style = action_style
        self.clarity_style = clarity_style
        self.pressure_distortion = pressure_distortion
        self.recurring_gift = recurring_gift
        self.recurring_failure_mode = recurring_failure_mode
        self.timing_tendency = timing_tendency
        self.decision_pattern = decision_pattern
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "action_style": self.action_style,
            "clarity_style": self.clarity_style,
            "pressure_distortion": self.pressure_distortion,
            "recurring_gift": self.recurring_gift,
            "recurring_failure_mode": self.recurring_failure_mode,
            "timing_tendency": self.timing_tendency,
            "decision_pattern": self.decision_pattern,
        }


def infer_stable_constitution(
    hd_data: Optional[Dict] = None,
    astro_data: Optional[Dict] = None,
    bazi_data: Optional[Dict] = None,
    journal_patterns: Optional[List[Dict]] = None
) -> StableConstitution:
    """
    Infer user's stable constitution from all available lens data.
    This represents WHO they are, not what's happening today.
    """
    
    # Defaults
    action_style = "measured"
    clarity_style = "gradual"
    pressure_distortion = "internalization"
    recurring_gift = "pattern recognition"
    recurring_failure_mode = "premature action"
    timing_tendency = "responsive"
    decision_pattern = "iterative"
    
    # Human Design contribution
    if hd_data:
        hd_type = hd_data.get("type", "")
        authority = hd_data.get("authority", "")
        profile = hd_data.get("profile", "")
        
        # Action style from type
        TYPE_ACTION_STYLES = {
            "Manifestor": "initiating force",
            "Generator": "responsive building",
            "Manifesting Generator": "responsive initiation",
            "Projector": "guided recognition",
            "Reflector": "environmental mirroring",
        }
        action_style = TYPE_ACTION_STYLES.get(hd_type, action_style)
        
        # Clarity style from authority
        if "emotional" in authority.lower():
            clarity_style = "wave-dependent"
            decision_pattern = "requires emotional neutrality"
        elif "sacral" in authority.lower():
            clarity_style = "gut-immediate"
            decision_pattern = "body response"
        elif "splenic" in authority.lower():
            clarity_style = "instant intuition"
            decision_pattern = "in-the-moment"
        elif "self" in authority.lower():
            clarity_style = "self-articulated"
            decision_pattern = "talking it through"
        
        # Timing tendency from type
        if hd_type == "Manifestor":
            timing_tendency = "initiating"
            recurring_gift = "catalyzing action"
            recurring_failure_mode = "moving before the field is ready"
            pressure_distortion = "resistance to informing"
        elif hd_type == "Generator":
            timing_tendency = "responsive"
            recurring_gift = "sustained building"
            recurring_failure_mode = "initiating instead of responding"
            pressure_distortion = "saying yes when the gut says no"
        elif hd_type == "Manifesting Generator":
            timing_tendency = "responsive-fast"
            recurring_gift = "efficient multi-tasking"
            recurring_failure_mode = "skipping necessary steps"
            pressure_distortion = "impatience with process"
        elif hd_type == "Projector":
            timing_tendency = "recognition-dependent"
            recurring_gift = "seeing systems and patterns"
            recurring_failure_mode = "sharing without invitation"
            pressure_distortion = "bitterness from not being seen"
        elif hd_type == "Reflector":
            timing_tendency = "lunar-cycle"
            recurring_gift = "environmental awareness"
            recurring_failure_mode = "deciding too fast"
            pressure_distortion = "absorbing others' urgency"
        
        # Profile adds nuance
        if profile:
            if "1" in str(profile):
                recurring_gift = f"{recurring_gift}, deep investigation"
            if "3" in str(profile):
                recurring_failure_mode = f"{recurring_failure_mode}, through trial and error"
            if "5" in str(profile):
                pressure_distortion = f"{pressure_distortion}, projection field from others"
            if "6" in str(profile):
                recurring_gift = f"{recurring_gift}, wisdom from experience"
    
    return StableConstitution(
        action_style=action_style,
        clarity_style=clarity_style,
        pressure_distortion=pressure_distortion,
        recurring_gift=recurring_gift,
        recurring_failure_mode=recurring_failure_mode,
        timing_tendency=timing_tendency,
        decision_pattern=decision_pattern
    )


# =============================================================================
# CURRENT ACTIVATION - What kind of moment is this?
# =============================================================================

def determine_moment_type(
    transit_data: Optional[Dict] = None,
    hd_data: Optional[Dict] = None,
    pattern_family: str = "general",
    tension_type: str = "",
    constitution: Optional[StableConstitution] = None
) -> tuple[MomentType, str]:
    """
    Determine what KIND of moment this is, not just list transits.
    Returns (moment_type, interpretation)
    """
    
    day_class = transit_data.get("classification", "normal_flow") if transit_data else "normal_flow"
    active_transits = transit_data.get("active_transits", []) if transit_data else []
    
    # Cross-reference with pattern family and constitution
    moment_type = MomentType.PAUSE_STALL  # default
    interpretation = ""
    
    # Determine moment type based on pattern + timing + constitution
    if pattern_family == "stall":
        if day_class == "high_pressure":
            moment_type = MomentType.STRUCTURE_NOT_READY
            interpretation = "External pressure is pushing for movement, but the internal structure isn't formed yet. The stall is protective."
        elif day_class == "release_window":
            moment_type = MomentType.REVIEW_RECALIBRATION
            interpretation = "The timing supports letting go, not pushing through. This pause is a recalibration point."
        else:
            # Quiet sky - this is important
            if constitution and "initiating" in constitution.timing_tendency:
                moment_type = MomentType.PREMATURE_INITIATION
                interpretation = "When the sky is not forcing movement, internal activation becomes visible. The drive to move may be ahead of readiness."
            else:
                moment_type = MomentType.PAUSE_STALL
                interpretation = "Nothing external is forcing this pause. It's arising from something unresolved within, which makes it worth attending to."
    
    elif pattern_family == "push_pull":
        if day_class == "high_pressure":
            moment_type = MomentType.THRESHOLD_MOMENT
            interpretation = "Real pressure is creating a threshold moment. Both directions have weight—this isn't confusion, it's genuine crossroads."
        else:
            moment_type = MomentType.OVERREACH_RISK
            interpretation = "The back-and-forth signals competing valid impulses. Forcing resolution now risks choosing the wrong one."
    
    elif pattern_family in ["movement", "release"]:
        if day_class == "high_pressure":
            moment_type = MomentType.FORCING_WINDOW
            interpretation = "The timing is creating momentum. The question is whether this force is aligned or premature."
        elif day_class == "release_window":
            moment_type = MomentType.CLEAN_INITIATION
            interpretation = "The timing supports forward movement. This is a cleaner window for action."
        else:
            moment_type = MomentType.CONSOLIDATION
            interpretation = "Quiet timing with forward energy suggests consolidation—building foundation before the next push."
    
    elif pattern_family == "expression":
        if constitution and "emotional" in constitution.clarity_style.lower():
            moment_type = MomentType.UNRESOLVED_WAVE
            interpretation = "What's unsaid may be connected to an emotional wave that hasn't completed. The silence could be wise waiting."
        else:
            moment_type = MomentType.THRESHOLD_MOMENT
            interpretation = "Something is at the threshold of expression. The question is whether it's ready to be said."
    
    elif pattern_family == "clarity":
        moment_type = MomentType.REVIEW_RECALIBRATION
        interpretation = "The fog is asking for review, not resolution. Clarity will come, but this isn't the moment to force it."
    
    elif pattern_family == "control":
        if day_class == "high_pressure":
            moment_type = MomentType.STRUCTURE_NOT_READY
            interpretation = "The grip makes sense—external instability is real. But holding tighter won't create the stability you need."
        else:
            moment_type = MomentType.OVERREACH_RISK
            interpretation = "The urge to control may be responding to internal instability projected outward. Check what's actually unstable."
    
    return moment_type, interpretation


# =============================================================================
# HISTORY PATTERN ANALYSIS - Recurrence detection
# =============================================================================

def analyze_history_patterns(
    journal_entries: List[Dict],
    lifeline_events: List[Dict],
    pattern_family: str,
    constitution: Optional[StableConstitution] = None
) -> Dict[str, Any]:
    """
    Analyze journal and lifeline for pattern recurrence.
    Returns behavioral shape, not just frequency.
    """
    
    result = {
        "frequency": 0,
        "pattern_shape": "",
        "examples": [],
        "deeper_roots": "",
        "cycle_observation": "",
    }
    
    # Count entries
    result["frequency"] = len(journal_entries)
    
    # Determine pattern shape based on pattern family + constitution
    PATTERN_SHAPES = {
        "stall": {
            "default": "start, then stall — the momentum builds but doesn't complete",
            "initiating": "initiate, then pause — the force is there but something holds it back",
            "responsive": "wait, then stall — even after the signal comes, movement doesn't follow",
        },
        "push_pull": {
            "default": "move toward, then pull back — the same crossroads appearing repeatedly",
            "initiating": "push forward, then hesitate — the initiating force meets internal resistance",
            "responsive": "respond yes, then reconsider — the gut says go but something else says wait",
        },
        "expression": {
            "default": "ready to speak, then hold back — truth at the threshold that doesn't cross",
            "initiating": "about to declare, then silence — the inform that doesn't happen",
            "emotional": "feeling it fully, then swallowing it — the wave peaks but the words don't come",
        },
        "clarity": {
            "default": "almost clear, then fog returns — understanding that doesn't stabilize",
            "emotional": "clarity in the high or low, confusion in the neutral — the wave distorting the view",
        },
        "control": {
            "default": "grip, then grip tighter — the need for control escalating",
            "initiating": "trying to force outcomes that aren't ready to be forced",
        },
        "release": {
            "default": "let go, then pick it back up — release that doesn't complete",
        },
        "movement": {
            "default": "move, then question — forward motion followed by doubt",
            "initiating": "act, then second-guess — the initiating force not trusting itself",
        },
    }
    
    # Select appropriate shape
    family_shapes = PATTERN_SHAPES.get(pattern_family, PATTERN_SHAPES["stall"])
    if constitution:
        if "initiating" in constitution.timing_tendency:
            result["pattern_shape"] = family_shapes.get("initiating", family_shapes["default"])
        elif "emotional" in constitution.clarity_style.lower():
            result["pattern_shape"] = family_shapes.get("emotional", family_shapes["default"])
        else:
            result["pattern_shape"] = family_shapes["default"]
    else:
        result["pattern_shape"] = family_shapes["default"]
    
    # Extract real examples from journal
    if journal_entries:
        examples = extract_behavioral_examples(journal_entries, pattern_family)
        result["examples"] = examples[:3]  # Max 3
    
    # Analyze lifeline for deeper roots
    if lifeline_events:
        if len(lifeline_events) >= 5:
            # Look for similar patterns in life history
            if pattern_family == "stall":
                result["deeper_roots"] = "This pause has roots. Your lifeline shows other threshold moments where movement stopped before completion."
            elif pattern_family == "push_pull":
                result["deeper_roots"] = "This crossroads isn't new. Your history contains other moments of standing between two valid paths."
            elif pattern_family == "expression":
                result["deeper_roots"] = "The held-back voice has history. There are other moments where truth stayed inside."
            else:
                result["deeper_roots"] = "This pattern has appeared before in different forms. The shape is familiar."
    
    # Generate cycle observation
    if result["frequency"] >= 5:
        if constitution and "initiating" in constitution.timing_tendency:
            result["cycle_observation"] = f"This pattern has shown up {result['frequency']} times recently. For someone with initiating force, repeated stalling often signals premature activation—the drive is real, but the target isn't ready."
        elif constitution and "emotional" in constitution.clarity_style.lower():
            result["cycle_observation"] = f"This pattern has appeared {result['frequency']} times. With emotional authority, recurrence often means the wave hasn't completed—you keep returning because clarity hasn't landed."
        else:
            result["cycle_observation"] = f"This same pattern has surfaced {result['frequency']} times recently. Recurrence this frequent isn't random—something is trying to be seen."
    
    return result


def extract_behavioral_examples(entries: List[Dict], pattern_family: str) -> List[str]:
    """Extract real behavioral examples from journal entries."""
    examples = []
    
    BEHAVIOR_KEYWORDS = {
        "stall": ["stopped", "paused", "couldn't", "waiting", "stuck", "hesitated", "held back"],
        "push_pull": ["back and forth", "both", "torn", "can't decide", "either", "wanted to but"],
        "expression": ["didn't say", "held back", "silent", "couldn't tell", "wanted to say"],
        "clarity": ["confused", "unclear", "don't know", "foggy", "not sure"],
        "control": ["trying to", "need to control", "managing", "holding together"],
        "release": ["let go", "released", "stopped trying", "surrendered"],
        "movement": ["moved", "acted", "decided", "went for it", "started"],
    }
    
    keywords = BEHAVIOR_KEYWORDS.get(pattern_family, BEHAVIOR_KEYWORDS["stall"])
    
    for entry in entries:
        content = entry.get("content", "").lower()
        for keyword in keywords:
            if keyword in content:
                # Extract a meaningful snippet
                snippet = extract_snippet(content, keyword)
                if snippet and len(snippet) > 20 and snippet not in examples:
                    examples.append(snippet)
                    break
        if len(examples) >= 3:
            break
    
    return examples


def extract_snippet(content: str, keyword: str) -> str:
    """Extract a readable snippet around a keyword."""
    import re
    sentences = re.split(r'[.!?]', content)
    for sentence in sentences:
        if keyword in sentence.lower():
            cleaned = sentence.strip()
            if 20 < len(cleaned) < 150:
                return cleaned[0].upper() + cleaned[1:] if cleaned else ""
    return ""


# =============================================================================
# CORE DIAGNOSIS - The main interpretive output
# =============================================================================

def generate_core_diagnosis(
    pattern_title: str,
    pattern_family: str,
    moment_type: MomentType,
    moment_interpretation: str,
    constitution: StableConstitution,
    history_analysis: Dict[str, Any],
    lens_evidence: Dict[str, Any]
) -> Dict[str, str]:
    """
    Generate ONE core diagnosis that synthesizes all lenses.
    
    Returns:
        - what_is_happening: The core observation
        - why_it_is_happening: The explanation across lenses
        - what_kind_of_moment: Classification
        - what_would_be_wise: Guidance
        - full_diagnosis: Complete narrative
    """
    
    # Build the diagnosis components
    what_is_happening = ""
    why_it_is_happening = ""
    what_kind_of_moment = ""
    what_would_be_wise = ""
    
    # WHAT IS HAPPENING - based on pattern + constitution
    if pattern_family == "stall":
        if "initiating" in constitution.action_style:
            what_is_happening = "There is real force here—initiating energy that wants to move. But it's meeting something that isn't ready."
        else:
            what_is_happening = "Movement has stopped. Not from lack of energy, but from something unresolved blocking the path."
    elif pattern_family == "push_pull":
        what_is_happening = "Two valid directions are competing for the same moment. This isn't indecision—it's recognition that both paths have weight."
    elif pattern_family == "expression":
        what_is_happening = "Something wants to be said but hasn't crossed the threshold into speech. The silence isn't empty—it's holding something."
    elif pattern_family == "clarity":
        what_is_happening = "Understanding hasn't landed. The fog isn't confusion—it's protection against premature certainty."
    elif pattern_family == "control":
        what_is_happening = "There's a grip on something that may not need to be held so tightly. The control is responding to real instability, but may be creating more."
    elif pattern_family == "release":
        what_is_happening = "Something is leaving. The letting go is real, but may not be complete."
    elif pattern_family == "movement":
        what_is_happening = "There is forward momentum. The question is whether it's aligned with readiness or ahead of it."
    else:
        what_is_happening = "A pattern is surfacing that wants attention. Something is trying to be seen."
    
    # WHY IT IS HAPPENING - cross-lens synthesis
    why_parts = []
    
    # Constitution contribution
    why_parts.append(f"Your design has {constitution.action_style}—with {constitution.clarity_style} clarity")
    
    # Timing contribution
    timing_evidence = lens_evidence.get("timing", {})
    if timing_evidence:
        why_parts.append(moment_interpretation)
    
    # History contribution
    if history_analysis.get("frequency", 0) >= 3:
        why_parts.append(f"Your own history shows this same shape: {history_analysis.get('pattern_shape', 'recurring patterns')}")
    
    # Failure mode connection
    if constitution.recurring_failure_mode:
        why_parts.append(f"The risk here connects to a familiar pattern: {constitution.recurring_failure_mode}")
    
    why_it_is_happening = ". ".join(why_parts) + "."
    
    # WHAT KIND OF MOMENT - from moment type
    MOMENT_DESCRIPTIONS = {
        MomentType.FORCING_WINDOW: "This is a forcing window—external pressure creating momentum. The question is whether to ride it or wait.",
        MomentType.PAUSE_STALL: "This is a genuine pause—not laziness, not failure, but information. Something is asking to be understood before movement.",
        MomentType.REVIEW_RECALIBRATION: "This is a recalibration moment. The timing supports review and adjustment, not forward push.",
        MomentType.OVERREACH_RISK: "This is an overreach risk moment. The impulse to force resolution could create more problems than it solves.",
        MomentType.PREMATURE_INITIATION: "This is a premature initiation risk. The drive to act is real, but the field may not be ready to receive it.",
        MomentType.UNRESOLVED_WAVE: "This is an unresolved wave moment. Emotional clarity hasn't landed—decisions made now may be revised later.",
        MomentType.STRUCTURE_NOT_READY: "This is a structure-not-ready moment. The intention is clear, but the foundation isn't in place.",
        MomentType.CLEAN_INITIATION: "This is a cleaner initiation window. The timing and readiness are more aligned than usual.",
        MomentType.CONSOLIDATION: "This is a consolidation moment. Build foundation now, push forward later.",
        MomentType.THRESHOLD_MOMENT: "This is a threshold moment. Something is ready to cross over—the question is whether to let it.",
    }
    what_kind_of_moment = MOMENT_DESCRIPTIONS.get(moment_type, "This is a moment asking for attention.")
    
    # WHAT WOULD BE WISE - based on moment type + constitution
    if moment_type == MomentType.PREMATURE_INITIATION:
        if "initiating" in constitution.action_style:
            what_would_be_wise = "The force is real, but this may not be the clean initiation point. Wait for the field to be ready, not just your drive. Inform before acting—sometimes the inform itself reveals whether the moment is ripe."
        else:
            what_would_be_wise = "The impulse to move is valid, but check whether it's arising from readiness or impatience. Waiting one more beat may reveal something."
    elif moment_type == MomentType.PAUSE_STALL:
        if "emotional" in constitution.clarity_style.lower():
            what_would_be_wise = "Don't try to think your way through this pause. Let the emotional wave complete. Clarity will come when you feel neutral, not when you've figured it out."
        else:
            what_would_be_wise = "Name what's unresolved. The pause exists because something hasn't landed—identifying it is more useful than pushing through it."
    elif moment_type == MomentType.UNRESOLVED_WAVE:
        what_would_be_wise = "Wait for emotional neutrality before deciding. If you're still in the wave—high or low—your view is distorted. The truth lives in the middle."
    elif moment_type == MomentType.OVERREACH_RISK:
        what_would_be_wise = "Resist the urge to force resolution. Sitting in uncertainty is uncomfortable but wiser than collapsing it prematurely."
    elif moment_type == MomentType.THRESHOLD_MOMENT:
        what_would_be_wise = "This is a real threshold. The question isn't whether to cross—it's whether you're clear about what you're crossing into."
    elif moment_type == MomentType.STRUCTURE_NOT_READY:
        what_would_be_wise = "The intention is right. The structure isn't. Focus on building foundation before pushing for results."
    elif moment_type == MomentType.CLEAN_INITIATION:
        what_would_be_wise = "This is as clean as initiation gets for you. If you've been waiting for a signal—this is closer to it."
    elif moment_type == MomentType.CONSOLIDATION:
        what_would_be_wise = "Build now, push later. Use this quieter moment to strengthen what will support the next move."
    else:
        what_would_be_wise = "Notice what wants attention. The pattern is surfacing for a reason—understanding it is more valuable than fixing it."
    
    # BUILD FULL DIAGNOSIS
    full_diagnosis = f"""{what_is_happening}

{what_kind_of_moment}

{why_it_is_happening}

{what_would_be_wise}"""
    
    return {
        "what_is_happening": what_is_happening,
        "why_it_is_happening": why_it_is_happening,
        "what_kind_of_moment": what_kind_of_moment,
        "what_would_be_wise": what_would_be_wise,
        "full_diagnosis": full_diagnosis,
        "moment_type": moment_type.value,
    }


# =============================================================================
# LENS EVIDENCE FORMATTING - Support for diagnosis, not separate output
# =============================================================================

def format_lens_evidence(
    constitution: StableConstitution,
    moment_type: MomentType,
    moment_interpretation: str,
    history_analysis: Dict[str, Any],
    transit_data: Optional[Dict] = None,
    hd_data: Optional[Dict] = None,
    pattern_family: str = "general",
    mode: str = "exploratory",
    transit_aspects: Optional[List[Dict]] = None,
    birth_date: Optional[datetime] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Format lens evidence as SUPPORT for the diagnosis.
    These are not separate summaries—they're evidence points.
    
    UPGRADED: Now uses unified_timing_intelligence for real transit data.
    NEVER says "quiet" if outer planet aspects exist.
    """
    from services.unified_timing_intelligence import get_unified_timing
    
    evidence = {}
    
    # TIMING EVIDENCE (Unified: Astrology + BaZi + Numerology)
    try:
        # Use actual transit aspects if provided
        aspects = transit_aspects or []
        
        # Pattern-specific behavioral titles (no system terms)
        PATTERN_TITLES = {
            "stall": "You're moving before it's settled",
            "push_pull": "You're pulled in two directions",
            "expression": "There's something you're not saying",
            "control": "You're holding on tighter than you need to",
            "clarity": "You're still searching for the right answer",
        }
        
        unified = get_unified_timing(
            user_id="",
            transit_aspects=aspects,
            pattern_family=pattern_family,
            pattern_title=PATTERN_TITLES.get(pattern_family, "Something's emerging"),
            natal_bazi=None,
            birth_date=birth_date,
        )
        
        transit_profile = unified.get("transit", {})
        bazi_profile = unified.get("bazi", {})
        
        # Build timing summary - NEVER "quiet" with real transits
        timing_summary = transit_profile.get("summary", "")
        if not timing_summary or "No major transits" in timing_summary:
            timing_summary = unified.get("master_summary", "The timing shows moderate activation across systems.")
        
        # Build timing implication - pattern-linked
        timing_implication = transit_profile.get("pattern_link", "")
        if not timing_implication:
            timing_implication = unified.get("pattern_synthesis", moment_interpretation)
        
        evidence["timing"] = {
            "summary": timing_summary,
            "implication": timing_implication,
        }
        
        # Add BaZi as separate evidence if meaningful
        if bazi_profile.get("ten_gods_active"):
            evidence["bazi"] = {
                "summary": bazi_profile.get("implication", ""),
                "implication": bazi_profile.get("pattern_link", ""),
            }
        
        # Log debug data
        logger.debug(f"[Diagnostician] Unified timing: intensity={unified.get('overall_intensity')}, type={unified.get('overall_type')}")
            
    except Exception as e:
        logger.warning(f"[Diagnostician] Unified timing failed, using fallback: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback
        evidence["timing"] = {
            "summary": "Timing data unavailable—working with internal patterns.",
            "implication": moment_interpretation,
        }
    
    # DESIGN EVIDENCE (Human Design)
    if hd_data:
        hd_type = hd_data.get("type", "")
        authority = hd_data.get("authority", "")
        
        if hd_type:
            design_summary = f"As a {hd_type} with {authority} authority, you have {constitution.action_style}."
            design_implication = f"Your pattern: {constitution.recurring_failure_mode}. Your gift: {constitution.recurring_gift}."
            
            evidence["design"] = {
                "summary": design_summary,
                "implication": design_implication,
            }
    
    # HISTORY EVIDENCE
    if history_analysis.get("frequency", 0) > 0:
        history_summary = f"This pattern has appeared {history_analysis['frequency']} times recently."
        history_implication = history_analysis.get("pattern_shape", "A recurring theme in your reflections.")
        
        if history_analysis.get("examples"):
            history_summary += f" Real examples from your reflections: {'; '.join(history_analysis['examples'][:2])}"
        
        if history_analysis.get("deeper_roots"):
            history_implication += f" {history_analysis['deeper_roots']}"
        
        evidence["history"] = {
            "summary": history_summary,
            "implication": history_implication,
        }
    
    return evidence


# =============================================================================
# MAIN DIAGNOSTIC FUNCTION
# =============================================================================

async def generate_cross_lens_diagnosis(
    user_id: str,
    pattern_title: str,
    pattern_family: str,
    tension_type: str,
    hd_data: Optional[Dict] = None,
    transit_data: Optional[Dict] = None,
    journal_entries: Optional[List[Dict]] = None,
    lifeline_events: Optional[List[Dict]] = None,
    bazi_data: Optional[Dict] = None,
    transit_aspects: Optional[List[Dict]] = None,  # Actual transit-to-natal aspects
) -> Dict[str, Any]:
    """
    Main entry point for cross-lens diagnosis.
    
    Returns a complete diagnostic package:
    - constitution: User's stable patterns
    - moment: What kind of moment this is
    - history: Pattern recurrence analysis
    - diagnosis: Core interpretive output
    - evidence: Lens-by-lens support
    """
    
    logger.info(f"[Diagnostician] Generating cross-lens diagnosis for {user_id[:8]}: {pattern_title}")
    
    # Step 1: Infer stable constitution
    constitution = infer_stable_constitution(
        hd_data=hd_data,
        astro_data=transit_data,
        bazi_data=bazi_data,
        journal_patterns=journal_entries
    )
    logger.debug(f"[Diagnostician] Constitution: {constitution.action_style}, {constitution.clarity_style}")
    
    # Step 2: Determine current moment type
    moment_type, moment_interpretation = determine_moment_type(
        transit_data=transit_data,
        hd_data=hd_data,
        pattern_family=pattern_family,
        tension_type=tension_type,
        constitution=constitution
    )
    logger.debug(f"[Diagnostician] Moment type: {moment_type.value}")
    
    # Step 3: Analyze history patterns
    history_analysis = analyze_history_patterns(
        journal_entries=journal_entries or [],
        lifeline_events=lifeline_events or [],
        pattern_family=pattern_family,
        constitution=constitution
    )
    logger.debug(f"[Diagnostician] History: {history_analysis['frequency']} occurrences, shape: {history_analysis['pattern_shape']}")
    
    # Step 4: Format lens evidence (with unified timing intelligence)
    # Use actual transit aspects if provided
    actual_transit_aspects = transit_aspects or []
    if not actual_transit_aspects and transit_data and "active_transits" in transit_data:
        actual_transit_aspects = transit_data.get("active_transits", [])
    
    lens_evidence = format_lens_evidence(
        constitution=constitution,
        moment_type=moment_type,
        moment_interpretation=moment_interpretation,
        history_analysis=history_analysis,
        transit_data=transit_data,
        hd_data=hd_data,
        pattern_family=pattern_family,
        mode="exploratory",  # Always get full evidence, frontend truncates
        transit_aspects=actual_transit_aspects,
        birth_date=None,
    )
    
    # Step 5: Generate core diagnosis
    diagnosis = generate_core_diagnosis(
        pattern_title=pattern_title,
        pattern_family=pattern_family,
        moment_type=moment_type,
        moment_interpretation=moment_interpretation,
        constitution=constitution,
        history_analysis=history_analysis,
        lens_evidence=lens_evidence
    )
    
    return {
        "constitution": constitution.to_dict(),
        "moment": {
            "type": moment_type.value,
            "interpretation": moment_interpretation,
        },
        "history": history_analysis,
        "diagnosis": diagnosis,
        "evidence": lens_evidence,
    }
