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
        
        # Timing tendency from type (Scene-specific language)
        if hd_type == "Manifestor":
            timing_tendency = "initiating"
            recurring_gift = "making things happen once direction is clear"
            recurring_failure_mode = "trying to close things before they sit right"
            pressure_distortion = "not naming what you're about to do"
        elif hd_type == "Generator":
            timing_tendency = "responsive"
            recurring_gift = "building what matters once you get the signal"
            recurring_failure_mode = "saying yes before your body agrees"
            pressure_distortion = "ignoring the gut 'no' to keep things moving"
        elif hd_type == "Manifesting Generator":
            timing_tendency = "responsive-fast"
            recurring_gift = "moving fast once something clicks"
            recurring_failure_mode = "skipping steps to get to the finish"
            pressure_distortion = "forcing closure when something still feels off"
        elif hd_type == "Projector":
            timing_tendency = "recognition-dependent"
            recurring_gift = "seeing what others miss"
            recurring_failure_mode = "offering before you're asked"
            pressure_distortion = "pushing when you haven't been invited"
        elif hd_type == "Reflector":
            timing_tendency = "lunar-cycle"
            recurring_gift = "reading the room accurately"
            recurring_failure_mode = "deciding before the full picture lands"
            pressure_distortion = "treating their urgency as your own"
        
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
    
    # Determine moment type based on pattern + timing + constitution (Scene-specific language)
    if pattern_family == "stall":
        if day_class == "high_pressure":
            moment_type = MomentType.STRUCTURE_NOT_READY
            interpretation = "There's real pressure to move. But part of you knows it's not ready—that hesitation is accurate."
        elif day_class == "release_window":
            moment_type = MomentType.REVIEW_RECALIBRATION
            interpretation = "This is a moment for letting go, not pushing through. The stall is telling you something."
        else:
            # Quiet sky - this is important
            if constitution and "initiating" in constitution.timing_tendency:
                moment_type = MomentType.PREMATURE_INITIATION
                interpretation = "Nothing external is forcing this—you're creating the urgency yourself. The drive is real, but the target isn't ready yet."
            else:
                moment_type = MomentType.PAUSE_STALL
                interpretation = "Nothing external is forcing this pause. Something inside hasn't landed—and that's worth paying attention to."
    
    elif pattern_family == "push_pull":
        if day_class == "high_pressure":
            moment_type = MomentType.THRESHOLD_MOMENT
            interpretation = "This is a real crossroads—both directions have weight. You're not confused. You're accurate."
        else:
            moment_type = MomentType.OVERREACH_RISK
            interpretation = "You keep going back and forth because both options are real. Forcing a choice now will just make you revisit it later."
    
    elif pattern_family in ["movement", "release"]:
        if day_class == "high_pressure":
            moment_type = MomentType.FORCING_WINDOW
            interpretation = "There's momentum here. The question is whether you're moving toward something clear—or just away from discomfort."
        elif day_class == "release_window":
            moment_type = MomentType.CLEAN_INITIATION
            interpretation = "This is a cleaner window to move. If you've been waiting for a signal—this is closer to it."
        else:
            moment_type = MomentType.CONSOLIDATION
            interpretation = "Quiet timing with forward energy means build now, push later. Strengthen what you're standing on first."
    
    elif pattern_family == "expression":
        if constitution and "emotional" in constitution.clarity_style.lower():
            moment_type = MomentType.UNRESOLVED_WAVE
            interpretation = "What you're not saying may be connected to a wave that hasn't finished. The silence might be wise waiting—or avoidance."
        else:
            moment_type = MomentType.THRESHOLD_MOMENT
            interpretation = "Something is sitting at the threshold. You've almost said it. The question is whether you're ready for what happens after."
    
    elif pattern_family == "clarity":
        moment_type = MomentType.REVIEW_RECALIBRATION
        interpretation = "The fog is asking for review, not resolution. Stop trying to figure it out—let the answer find you."
    
    elif pattern_family == "control":
        if day_class == "high_pressure":
            moment_type = MomentType.STRUCTURE_NOT_READY
            interpretation = "The grip makes sense—something really is unstable. But holding tighter won't create what you need."
        else:
            moment_type = MomentType.OVERREACH_RISK
            interpretation = "You're trying to control something that may not need controlling. Check what's actually unstable versus what you're projecting."
    
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
    
    # Determine pattern shape based on pattern family + constitution (Scene-specific language)
    PATTERN_SHAPES = {
        "stall": {
            "default": "almost move, then stop — you get close, then something pulls you back",
            "initiating": "try to close it, then pause — you want this done but something still doesn't sit right",
            "responsive": "wait for the signal, then stall — even when you feel it, you don't move",
        },
        "push_pull": {
            "default": "lean one way, then pull back — you've done this loop before",
            "initiating": "try to force it, then hesitate — you want closure but something keeps reopening",
            "responsive": "feel a yes, then second-guess — your body moves but your mind pulls back",
        },
        "expression": {
            "default": "almost say it, then hold back — you've rehearsed this but still didn't send it",
            "initiating": "about to declare it, then silence — you know what to say but you stop yourself",
            "emotional": "feel it rising, then swallow it — the words are there but they don't come out",
        },
        "clarity": {
            "default": "almost clear, then fog returns — you think you've got it, then you don't",
            "emotional": "clear in the high, lost in the low — the wave keeps distorting your view",
        },
        "control": {
            "default": "grip tighter, then grip again — you're holding on harder than you need to",
            "initiating": "try to force outcomes that aren't ready to be forced — you're pushing against something that won't move",
        },
        "release": {
            "default": "let go, then pick it back up — you release it but it keeps coming back",
        },
        "movement": {
            "default": "move forward, then question — you act, then wonder if it was right",
            "initiating": "close it, then second-guess — you finish things but you keep looking back",
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
    
    # Generate cycle observation (Scene-specific language)
    if result["frequency"] >= 5:
        if constitution and "initiating" in constitution.timing_tendency:
            result["cycle_observation"] = f"This has shown up {result['frequency']} times recently. You keep trying to close things that still don't sit right—you want movement, but something in you keeps pumping the brakes."
        elif constitution and "emotional" in constitution.clarity_style.lower():
            result["cycle_observation"] = f"This has appeared {result['frequency']} times. You keep coming back because clarity hasn't actually landed—you're trying to decide while still in the wave."
        else:
            result["cycle_observation"] = f"This same thing has surfaced {result['frequency']} times recently. That's not random—there's something you keep trying to get past without actually resolving."
    
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
    
    # WHAT IS HAPPENING - based on pattern + constitution (Scene-specific language)
    if pattern_family == "stall":
        if "initiating" in constitution.action_style:
            what_is_happening = "You want to close this—but something in you keeps pumping the brakes. That hesitation isn't confusion. It's signal."
        else:
            what_is_happening = "You keep trying to move forward on this—and something keeps stopping you. Not because you're stuck. Because something hasn't landed yet."
    elif pattern_family == "push_pull":
        what_is_happening = "You lean one way, then pull back. Both directions feel valid—because they are. You're not indecisive. You're accurate."
    elif pattern_family == "expression":
        what_is_happening = "There's something you've almost said. Multiple times. You've drafted it, softened it, deleted it. It's still there—waiting to come out."
    elif pattern_family == "clarity":
        what_is_happening = "You keep thinking you've figured it out—then the fog returns. Stop trying to force clarity. It hasn't landed yet."
    elif pattern_family == "control":
        what_is_happening = "You're gripping harder than you need to. Something feels unstable—but holding tighter won't stabilize it."
    elif pattern_family == "release":
        what_is_happening = "You've let go of this before. But it keeps coming back. Maybe the release wasn't complete—or wasn't actually what you wanted."
    elif pattern_family == "movement":
        what_is_happening = "You're moving forward—but part of you keeps looking back. Are you moving toward something, or just away from discomfort?"
    else:
        what_is_happening = "Something is surfacing that wants attention. It keeps coming back because there's something you haven't faced yet."
    
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
    
    # WHAT KIND OF MOMENT - from moment type (Scene-specific language)
    MOMENT_DESCRIPTIONS = {
        MomentType.FORCING_WINDOW: "There's momentum here. The question is whether you're moving toward clarity—or just away from discomfort.",
        MomentType.PAUSE_STALL: "This is a real pause—not laziness, not failure. Something in you hasn't landed yet. That's worth paying attention to.",
        MomentType.REVIEW_RECALIBRATION: "This is a moment for review, not resolution. Stop trying to figure it out—let the answer find you.",
        MomentType.OVERREACH_RISK: "You're close to forcing something that isn't ready. Sitting in discomfort is hard—but collapsing it prematurely is harder to undo.",
        MomentType.PREMATURE_INITIATION: "You're creating urgency that doesn't exist yet. The drive is real, but the target isn't ready.",
        MomentType.UNRESOLVED_WAVE: "You're trying to decide while still in the wave. Clarity will come—but not while you're high or low.",
        MomentType.STRUCTURE_NOT_READY: "The intention is clear. The foundation isn't. Build before pushing.",
        MomentType.CLEAN_INITIATION: "This is a cleaner window to move. If you've been waiting for a signal—this is closer to it.",
        MomentType.CONSOLIDATION: "Build now, push later. Use this quieter moment to strengthen what you're standing on.",
        MomentType.THRESHOLD_MOMENT: "You're at a real threshold. The question isn't whether to cross—it's whether you're clear about what you're crossing into.",
    }
    what_kind_of_moment = MOMENT_DESCRIPTIONS.get(moment_type, "Something is surfacing that wants attention.")
    
    # WHAT WOULD BE WISE - based on moment type + constitution (Scene-specific language)
    if moment_type == MomentType.PREMATURE_INITIATION:
        if "initiating" in constitution.action_style:
            what_would_be_wise = "Don't close this yet. Name what still doesn't sit right. The drive is real—but the target isn't ready."
        else:
            what_would_be_wise = "Wait one more beat before moving. The urgency you feel might be yours—or it might be borrowed."
    elif moment_type == MomentType.PAUSE_STALL:
        if "emotional" in constitution.clarity_style.lower():
            what_would_be_wise = "Don't try to think your way through this. Let the wave finish. Clarity will come when you feel neutral, not when you've figured it out."
        else:
            what_would_be_wise = "Name what's unresolved. The pause exists because something hasn't landed—identifying it matters more than pushing through."
    elif moment_type == MomentType.UNRESOLVED_WAVE:
        what_would_be_wise = "Wait for neutral before deciding. If you're still in the wave—high or low—your view is distorted."
    elif moment_type == MomentType.OVERREACH_RISK:
        what_would_be_wise = "Resist the urge to force this. Sitting in uncertainty is uncomfortable—but collapsing it prematurely will just make you revisit it later."
    elif moment_type == MomentType.THRESHOLD_MOMENT:
        what_would_be_wise = "This is a real threshold. Before crossing, name what you're leaving behind—and what you're walking into."
    elif moment_type == MomentType.STRUCTURE_NOT_READY:
        what_would_be_wise = "The intention is right. The foundation isn't. Build what's missing before pushing for results."
    elif moment_type == MomentType.CLEAN_INITIATION:
        what_would_be_wise = "This is as clean a window as you'll get. If you've been waiting for a signal—this is closer to it."
    elif moment_type == MomentType.CONSOLIDATION:
        what_would_be_wise = "Build now, push later. Strengthen what you're standing on before trying to move forward."
    else:
        what_would_be_wise = "Notice what keeps coming back. The pattern is surfacing for a reason—understanding it matters more than fixing it."
    
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


# =============================================================================
# V1: PREFERENCE-AWARE HOME ADAPTATION
# =============================================================================

def adapt_diagnosis_to_preferences(
    diagnosis: Dict[str, Any],
    v1_tone: str = "calm",
    v1_depth: str = "balanced",
    v1_support_style: str = "work_with"
) -> Dict[str, Any]:
    """
    Adapt diagnosis output based on user preferences.
    
    GOAL: Home should feel like it speaks in the user's chosen tone, depth, and support style.
    
    RULES:
    - Keep single flow structure
    - Keep interruption feel
    - Keep short lines
    - No labels or explanations
    - Do NOT turn Home into advice
    """
    if not diagnosis:
        return diagnosis
    
    adapted = diagnosis.copy()
    
    what_is_happening = diagnosis.get("what_is_happening", "")
    
    # =============================================================================
    # TONE ADAPTATION
    # =============================================================================
    
    if v1_tone == "direct":
        # Shorter lines, less padding, more blunt
        # Remove softer phrases
        what_is_happening = what_is_happening.replace("—but ", ". ")
        what_is_happening = what_is_happening.replace("Maybe ", "")
        what_is_happening = what_is_happening.replace("something in you ", "you ")
        what_is_happening = what_is_happening.replace("It's signal.", "That's the signal.")
        
    elif v1_tone == "confronting":
        # Sharper truth, more direct exposure
        if "hesitation" in what_is_happening.lower():
            what_is_happening = what_is_happening.replace(
                "That hesitation isn't confusion. It's signal.",
                "You're about to do the thing that keeps costing you."
            )
        if "keep trying" in what_is_happening.lower():
            what_is_happening += " You already know what's stopping you."
        if "let go" in what_is_happening.lower():
            what_is_happening += " Be honest about why it's still here."
            
    elif v1_tone == "grounded":
        # Practical phrasing, less emotional language
        what_is_happening = what_is_happening.replace("signal", "information")
        what_is_happening = what_is_happening.replace("fog", "uncertainty")
        what_is_happening = what_is_happening.replace("gripping", "holding")
        what_is_happening = what_is_happening.replace("waiting to come out", "needs to be said")
    
    # calm = default, no changes needed
    
    # =============================================================================
    # DEPTH ADAPTATION
    # =============================================================================
    
    if v1_depth == "light":
        # Fewer lines, quicker hit
        # Split on periods and take first 2-3 sentences
        sentences = what_is_happening.split(". ")
        if len(sentences) > 2:
            what_is_happening = ". ".join(sentences[:2]) + "."
        # Also shorten why_it_is_happening
        why_text = diagnosis.get("why_it_is_happening", "")
        why_sentences = why_text.split(". ")
        if len(why_sentences) > 2:
            adapted["why_it_is_happening"] = ". ".join(why_sentences[:2]) + "."
            
    elif v1_depth == "deep":
        # Allow one extra reinforcing line
        if not what_is_happening.endswith("You've seen this before."):
            what_is_happening += " This isn't new. You've seen this pattern before."
    
    # balanced = default, no changes needed
    
    # =============================================================================
    # SUPPORT STYLE ADAPTATION
    # =============================================================================
    
    if v1_support_style == "interrupt":
        # Stronger interception, more "You're about to..."
        if "keep" in what_is_happening.lower() and "You're about to" not in what_is_happening:
            what_is_happening = "You're about to loop again. " + what_is_happening
        if "trying" in what_is_happening.lower():
            what_is_happening = what_is_happening.replace("You keep trying", "Stop. You keep trying")
            
    elif v1_support_style == "explore":
        # More open-ended, reflective ending
        if not what_is_happening.endswith("?"):
            what_is_happening += " What's actually underneath this?"
        # Make what_would_be_wise more reflective
        wise = adapted.get("what_would_be_wise", "")
        if wise and not wise.endswith("?"):
            adapted["what_would_be_wise"] = wise.rstrip(".") + "—if you're ready to name it."
    
    # work_with = default, current behavior is already action-oriented
    
    adapted["what_is_happening"] = what_is_happening
    
    # Rebuild full_diagnosis
    adapted["full_diagnosis"] = f"""{adapted.get("what_is_happening", "")}

{adapted.get("what_kind_of_moment", "")}

{adapted.get("why_it_is_happening", "")}

{adapted.get("what_would_be_wise", "")}"""
    
    return adapted

