"""
Master Astrology Transit Evidence Engine
========================================

Provides real transit hierarchy for the cross-lens diagnosis:

1. FOREGROUND TRANSITS - Strongest active/applying aspects
2. BACKGROUND CLIMATE - Slower outer-planet pressure
3. EMOTIONAL TRIGGER - Moon context (sign, phase, aspects)

Transit Types:
- FORCING: External pressure demanding action
- PAUSE/REVIEW: Time to slow down, reassess
- THRESHOLD: Decision point, crossroads
- OVERREACH: Risk of pushing too hard/fast
- OPENING: New possibilities emerging
- CLOSURE: Endings, completions

This feeds into the cross-lens diagnostician as evidence.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSIT TYPES - What kind of moment is this?
# =============================================================================

class TransitType(str, Enum):
    FORCING = "forcing"                    # External pressure demanding action
    PAUSE_REVIEW = "pause_review"          # Time to slow down, reassess
    THRESHOLD = "threshold"                # Decision point, crossroads
    OVERREACH_RISK = "overreach_risk"      # Risk of pushing too hard
    OPENING = "opening"                    # New possibilities emerging
    CLOSURE = "closure"                    # Endings, completions
    RIPENING = "ripening"                  # Things developing, not ready yet
    NEUTRAL = "neutral"                    # No strong transit pressure


# =============================================================================
# ZODIAC AND PLANETARY CONSTANTS
# =============================================================================

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Sign modalities and their timing implications
SIGN_MODALITY = {
    "Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal", "Capricorn": "cardinal",
    "Taurus": "fixed", "Leo": "fixed", "Scorpio": "fixed", "Aquarius": "fixed",
    "Gemini": "mutable", "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable",
}

MODALITY_MEANING = {
    "cardinal": "initiating energy—pressure to start, act, decide",
    "fixed": "stabilizing energy—pressure to commit, hold, persist",
    "mutable": "adaptive energy—pressure to adjust, release, flow",
}

# Sign elements
SIGN_ELEMENT = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

ELEMENT_MEANING = {
    "fire": "action, will, expression",
    "earth": "structure, form, manifestation",
    "air": "thought, communication, connection",
    "water": "emotion, intuition, depth",
}

# Planetary speeds and influence types
PLANET_INFO = {
    "Sun": {"speed": "fast", "domain": "identity, will, purpose", "forcing_power": 0.5},
    "Moon": {"speed": "fast", "domain": "emotion, needs, instinct", "forcing_power": 0.4},
    "Mercury": {"speed": "fast", "domain": "thought, communication, decision", "forcing_power": 0.5},
    "Venus": {"speed": "fast", "domain": "values, relationship, desire", "forcing_power": 0.4},
    "Mars": {"speed": "medium", "domain": "action, drive, assertion", "forcing_power": 0.7},
    "Jupiter": {"speed": "slow", "domain": "expansion, opportunity, growth", "forcing_power": 0.5},
    "Saturn": {"speed": "slow", "domain": "structure, limit, maturity", "forcing_power": 0.8},
    "Uranus": {"speed": "glacial", "domain": "disruption, awakening, change", "forcing_power": 0.6},
    "Neptune": {"speed": "glacial", "domain": "dissolution, dreams, confusion", "forcing_power": 0.3},
    "Pluto": {"speed": "glacial", "domain": "transformation, power, depth", "forcing_power": 0.7},
    "North Node": {"speed": "slow", "domain": "growth direction, destiny", "forcing_power": 0.5},
    "South Node": {"speed": "slow", "domain": "release, past patterns", "forcing_power": 0.4},
}

# Aspect meanings and transit types
ASPECT_INFO = {
    "conjunction": {
        "orb": 8, "strength": 1.0, "type": "major", 
        "meaning": "fusion, intensification, new beginning",
        "transit_type": TransitType.FORCING,
    },
    "opposition": {
        "orb": 8, "strength": 0.9, "type": "major",
        "meaning": "tension, awareness, balance needed",
        "transit_type": TransitType.THRESHOLD,
    },
    "square": {
        "orb": 7, "strength": 0.85, "type": "major",
        "meaning": "friction, challenge, action required",
        "transit_type": TransitType.FORCING,
    },
    "trine": {
        "orb": 7, "strength": 0.7, "type": "major",
        "meaning": "flow, ease, opportunity",
        "transit_type": TransitType.OPENING,
    },
    "sextile": {
        "orb": 5, "strength": 0.5, "type": "minor",
        "meaning": "opportunity, potential, requires effort",
        "transit_type": TransitType.OPENING,
    },
    "quincunx": {
        "orb": 3, "strength": 0.6, "type": "minor",
        "meaning": "adjustment, discomfort, integration needed",
        "transit_type": TransitType.PAUSE_REVIEW,
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TransitEvidence:
    """A single piece of transit evidence."""
    planet: str
    aspect: str
    target: str  # natal planet/point or sign
    strength: float  # 0-1
    transit_type: TransitType
    is_applying: bool  # applying = getting stronger
    orb: float  # degrees from exact
    interpretation: str
    evidence_statement: str  # User-facing evidence


@dataclass
class TransitHierarchy:
    """The full transit picture for a moment."""
    foreground: List[TransitEvidence]  # Strongest 1-2 transits
    background_climate: str  # Outer planet context
    background_type: TransitType
    moon_context: Dict[str, Any]  # Moon sign, phase, aspects
    overall_type: TransitType
    overall_strength: float  # 0-1
    evidence_summary: str  # Master astrologer summary
    debug_data: Dict[str, Any]  # For verification


# =============================================================================
# MOON CALCULATIONS (Enhanced)
# =============================================================================

def calculate_detailed_moon_context(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate comprehensive Moon context for transit evidence.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Known new moon: January 11, 2024 11:57 UTC
    reference_new_moon = datetime(2024, 1, 11, 11, 57, 0, tzinfo=timezone.utc)
    synodic_month = 29.53059
    
    # Calculate days into cycle
    delta = dt - reference_new_moon
    days_since = delta.total_seconds() / 86400.0
    cycle_days = days_since % synodic_month
    phase_fraction = cycle_days / synodic_month
    illumination = (1 - math.cos(2 * math.pi * phase_fraction)) / 2
    
    # Determine phase name and type
    if cycle_days < 1.85:
        phase_name = "New Moon"
        phase_type = TransitType.OPENING
        phase_meaning = "new beginnings, fresh starts, seeds being planted"
    elif cycle_days < 7.38:
        phase_name = "Waxing Crescent"
        phase_type = TransitType.RIPENING
        phase_meaning = "building momentum, intentions taking shape"
    elif cycle_days < 9.23:
        phase_name = "First Quarter"
        phase_type = TransitType.THRESHOLD
        phase_meaning = "decision point, challenges emerging, action needed"
    elif cycle_days < 12.91:
        phase_name = "Waxing Gibbous"
        phase_type = TransitType.FORCING
        phase_meaning = "refinement, adjustment, nearing completion"
    elif cycle_days < 16.61:
        phase_name = "Full Moon"
        phase_type = TransitType.THRESHOLD
        phase_meaning = "culmination, revelation, clarity or crisis"
    elif cycle_days < 20.29:
        phase_name = "Waning Gibbous"
        phase_type = TransitType.PAUSE_REVIEW
        phase_meaning = "integration, sharing, processing"
    elif cycle_days < 23.99:
        phase_name = "Last Quarter"
        phase_type = TransitType.CLOSURE
        phase_meaning = "release, reassessment, letting go"
    else:
        phase_name = "Waning Crescent"
        phase_type = TransitType.PAUSE_REVIEW
        phase_meaning = "surrender, rest, preparation for new cycle"
    
    # Calculate Moon sign (approximate)
    # Moon moves ~13 degrees per day through zodiac
    # Full cycle = 27.32 days (sidereal month)
    sidereal_month = 27.32
    sidereal_days = days_since % sidereal_month
    sign_index = int((sidereal_days / sidereal_month) * 12) % 12
    moon_sign = ZODIAC_SIGNS[sign_index]
    
    # Moon sign characteristics
    moon_element = SIGN_ELEMENT.get(moon_sign, "water")
    moon_modality = SIGN_MODALITY.get(moon_sign, "mutable")
    
    # Moon sign interpretations for emotional state
    MOON_SIGN_EMOTIONAL_TONE = {
        "Aries": "emotionally reactive, quick to act, impatient with hesitation",
        "Taurus": "emotionally stable but stubborn, need for security, slow to change",
        "Gemini": "emotionally restless, need for variety, processing through talking",
        "Cancer": "emotionally sensitive, need for safety, protective instincts high",
        "Leo": "emotionally expressive, need for recognition, generous but proud",
        "Virgo": "emotionally analytical, tendency to worry, need for order",
        "Libra": "emotionally balanced-seeking, need for harmony, difficulty with conflict",
        "Scorpio": "emotionally intense, all-or-nothing, transformation pressure",
        "Sagittarius": "emotionally optimistic, need for freedom, restless energy",
        "Capricorn": "emotionally reserved, need for control, practical about feelings",
        "Aquarius": "emotionally detached, need for space, intellectual about feelings",
        "Pisces": "emotionally porous, need for boundary, intuition very high",
    }
    
    emotional_tone = MOON_SIGN_EMOTIONAL_TONE.get(moon_sign, "emotionally active")
    
    return {
        "sign": moon_sign,
        "phase_name": phase_name,
        "phase_type": phase_type,
        "phase_meaning": phase_meaning,
        "illumination": round(illumination, 2),
        "cycle_day": round(cycle_days, 1),
        "element": moon_element,
        "modality": moon_modality,
        "emotional_tone": emotional_tone,
        "evidence": f"Moon in {moon_sign} ({phase_name}) — {emotional_tone}",
    }


# =============================================================================
# BACKGROUND CLIMATE (Outer Planet Context)
# =============================================================================

def calculate_background_climate(dt: Optional[datetime] = None) -> Tuple[str, TransitType, str]:
    """
    Calculate the slow-moving outer planet backdrop.
    These create the background pressure that personal transits play against.
    
    Returns (climate_description, transit_type, evidence_statement)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    year = dt.year
    month = dt.month
    
    # Saturn position (approximate - moves ~1 sign per 2.5 years)
    # Saturn entered Pisces March 2023, stays until Feb 2026
    # Saturn in Aries from Feb 2026
    if year < 2026 or (year == 2026 and month < 2):
        saturn_sign = "Pisces"
        saturn_meaning = "dissolving old structures, spiritual maturation, endings before new forms"
    elif year < 2028:
        saturn_sign = "Aries"
        saturn_meaning = "pressure to initiate, new structural foundations, identity restructuring"
    else:
        saturn_sign = "Aries"
        saturn_meaning = "structural pressure on identity and action"
    
    # Pluto position (entered Aquarius 2024, stays until 2043)
    if year >= 2024:
        pluto_sign = "Aquarius"
        pluto_meaning = "collective transformation, power structures shifting, technology and humanity themes"
    else:
        pluto_sign = "Capricorn"
        pluto_meaning = "institutional transformation, authority restructuring"
    
    # Neptune position (in Pisces until 2026, then Aries)
    if year < 2026:
        neptune_sign = "Pisces"
        neptune_meaning = "collective dissolution, spiritual emergence, reality blurring"
    else:
        neptune_sign = "Aries"
        neptune_meaning = "new collective dreams, idealism around identity and action"
    
    # Uranus position (in Taurus until 2026, then Gemini)
    if year < 2026 or (year == 2026 and month < 7):
        uranus_sign = "Taurus"
        uranus_meaning = "disruption of stability, financial/value revolution, body awareness"
    else:
        uranus_sign = "Gemini"
        uranus_meaning = "communication revolution, mental breakthroughs, information disruption"
    
    # Determine dominant background theme
    # Saturn in mutable sign + Pluto in fixed = structure dissolving while power consolidates
    saturn_modality = SIGN_MODALITY.get(saturn_sign, "mutable")
    
    if saturn_modality == "mutable":
        background_type = TransitType.PAUSE_REVIEW
        climate = f"Saturn in {saturn_sign} creates {saturn_meaning}. This is background pressure favoring review over hasty action."
    elif saturn_modality == "cardinal":
        background_type = TransitType.FORCING
        climate = f"Saturn in {saturn_sign} creates {saturn_meaning}. This is background pressure to initiate new structures."
    else:
        background_type = TransitType.RIPENING
        climate = f"Saturn in {saturn_sign} creates {saturn_meaning}. This is background pressure to commit and consolidate."
    
    evidence = f"Background: Saturn in {saturn_sign}, Pluto in {pluto_sign}. {saturn_meaning}"
    
    return climate, background_type, evidence


# =============================================================================
# FOREGROUND TRANSIT DETECTION
# =============================================================================

def detect_foreground_transits(
    moon_context: Dict[str, Any],
    dt: Optional[datetime] = None
) -> List[TransitEvidence]:
    """
    Detect the strongest 1-2 active transits for today.
    
    In a full implementation, this would use ephemeris data.
    For now, we derive from moon and day-of-week patterns.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    transits = []
    
    # Moon phase creates primary emotional transit
    moon_phase = moon_context.get("phase_name", "")
    moon_sign = moon_context.get("sign", "")
    moon_type = moon_context.get("phase_type", TransitType.NEUTRAL)
    
    # Primary: Moon transit
    moon_transit = TransitEvidence(
        planet="Moon",
        aspect="transiting",
        target=moon_sign,
        strength=0.6 if "New" in moon_phase or "Full" in moon_phase else 0.4,
        transit_type=moon_type,
        is_applying=moon_context.get("illumination", 0.5) < 0.5,  # Applying when waxing
        orb=0,
        interpretation=moon_context.get("phase_meaning", ""),
        evidence_statement=f"The Moon is in {moon_sign} ({moon_phase}), highlighting {SIGN_ELEMENT.get(moon_sign, 'emotional')} themes.",
    )
    transits.append(moon_transit)
    
    # Secondary transit based on day patterns
    # In reality, this would use actual planetary positions
    day_of_year = dt.timetuple().tm_yday
    week_of_year = day_of_year // 7
    
    # Mercury influence (communication/decision pressure)
    # Mercury is retrograde roughly 3x per year for ~3 weeks
    mercury_retro_periods = [
        (1, 21), (32, 52),  # Jan-Feb
        (105, 125),  # April
        (224, 244),  # August
        (305, 325),  # November
    ]
    
    is_mercury_retro = any(start <= day_of_year <= end for start, end in mercury_retro_periods)
    
    if is_mercury_retro:
        mercury_transit = TransitEvidence(
            planet="Mercury",
            aspect="retrograde",
            target="natal Mercury",
            strength=0.7,
            transit_type=TransitType.PAUSE_REVIEW,
            is_applying=False,
            orb=0,
            interpretation="Mercury retrograde is slowing communication and decision clarity. Review, don't initiate.",
            evidence_statement="Mercury is retrograde, creating decision fog and communication delays. Not ideal for new commitments.",
        )
        transits.append(mercury_transit)
    else:
        # Check if Mercury is in a "forcing" sign (cardinal)
        # Approximate Mercury position
        mercury_sign_index = (day_of_year // 30) % 12
        mercury_sign = ZODIAC_SIGNS[mercury_sign_index]
        mercury_modality = SIGN_MODALITY.get(mercury_sign, "mutable")
        
        if mercury_modality == "cardinal":
            mercury_transit = TransitEvidence(
                planet="Mercury",
                aspect="transiting",
                target=mercury_sign,
                strength=0.5,
                transit_type=TransitType.FORCING,
                is_applying=True,
                orb=5,
                interpretation=f"Mercury in {mercury_sign} is activating decision pressure.",
                evidence_statement=f"Mercury in {mercury_sign} is pushing for clarity and decision-making.",
            )
            transits.append(mercury_transit)
    
    # Mars influence (action pressure)
    # Mars takes ~2 years to go through zodiac, ~2 months per sign
    mars_sign_index = ((day_of_year + week_of_year * 7) // 60) % 12
    mars_sign = ZODIAC_SIGNS[mars_sign_index]
    mars_modality = SIGN_MODALITY.get(mars_sign, "fixed")
    
    if mars_modality == "cardinal":
        mars_transit = TransitEvidence(
            planet="Mars",
            aspect="transiting",
            target=mars_sign,
            strength=0.65,
            transit_type=TransitType.FORCING,
            is_applying=True,
            orb=3,
            interpretation=f"Mars in {mars_sign} is creating action pressure—the urge to do, not wait.",
            evidence_statement=f"Mars in {mars_sign} is amplifying drive and impatience. Action energy is high.",
        )
        transits.append(mars_transit)
    elif mars_modality == "fixed":
        mars_transit = TransitEvidence(
            planet="Mars",
            aspect="transiting",
            target=mars_sign,
            strength=0.55,
            transit_type=TransitType.OVERREACH_RISK,
            is_applying=True,
            orb=5,
            interpretation=f"Mars in {mars_sign} creates stubborn push—risk of forcing what isn't ready.",
            evidence_statement=f"Mars in {mars_sign} can create overcommitment. Watch for forcing timing.",
        )
        transits.append(mars_transit)
    
    # Sort by strength
    transits.sort(key=lambda t: t.strength, reverse=True)
    
    return transits[:2]  # Top 2 foreground transits


# =============================================================================
# MAIN HIERARCHY BUILDER
# =============================================================================

def build_transit_hierarchy(dt: Optional[datetime] = None) -> TransitHierarchy:
    """
    Build the complete transit hierarchy for cross-lens diagnosis.
    
    Returns:
        TransitHierarchy with foreground, background, moon context, and summary
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # 1. Calculate Moon context
    moon_context = calculate_detailed_moon_context(dt)
    
    # 2. Calculate background climate
    background_desc, background_type, background_evidence = calculate_background_climate(dt)
    
    # 3. Detect foreground transits
    foreground = detect_foreground_transits(moon_context, dt)
    
    # 4. Determine overall transit type
    # Priority: strong foreground > moon phase > background
    if foreground and foreground[0].strength >= 0.6:
        overall_type = foreground[0].transit_type
    elif moon_context.get("phase_type"):
        overall_type = moon_context["phase_type"]
    else:
        overall_type = background_type
    
    # 5. Calculate overall strength
    foreground_strength = max((t.strength for t in foreground), default=0.3)
    moon_strength = 0.5 if "New" in moon_context.get("phase_name", "") or "Full" in moon_context.get("phase_name", "") else 0.35
    overall_strength = min(0.95, foreground_strength * 0.6 + moon_strength * 0.4)
    
    # 6. Generate master astrologer evidence summary
    evidence_summary = generate_evidence_summary(
        foreground, moon_context, background_desc, overall_type
    )
    
    # 7. Build debug data
    debug_data = {
        "top_transit_label": foreground[0].planet + " " + foreground[0].aspect if foreground else "none",
        "top_transit_type": foreground[0].transit_type.value if foreground else "neutral",
        "top_transit_strength": foreground[0].strength if foreground else 0,
        "moon_sign": moon_context.get("sign"),
        "moon_phase": moon_context.get("phase_name"),
        "moon_type": moon_context.get("phase_type", TransitType.NEUTRAL).value if isinstance(moon_context.get("phase_type"), TransitType) else "neutral",
        "background_climate": background_type.value,
        "overall_type": overall_type.value,
        "overall_strength": overall_strength,
    }
    
    return TransitHierarchy(
        foreground=foreground,
        background_climate=background_desc,
        background_type=background_type,
        moon_context=moon_context,
        overall_type=overall_type,
        overall_strength=overall_strength,
        evidence_summary=evidence_summary,
        debug_data=debug_data,
    )


def generate_evidence_summary(
    foreground: List[TransitEvidence],
    moon_context: Dict[str, Any],
    background: str,
    overall_type: TransitType
) -> str:
    """
    Generate the master astrologer evidence summary.
    This is what appears in the diagnosis as "TIMING" evidence.
    """
    
    parts = []
    
    # Lead with overall type
    TYPE_LEADS = {
        TransitType.FORCING: "The timing is pushing for action.",
        TransitType.PAUSE_REVIEW: "The timing supports pause and review, not push.",
        TransitType.THRESHOLD: "The timing is at a decision threshold.",
        TransitType.OVERREACH_RISK: "The timing carries overreach risk—watch for forcing.",
        TransitType.OPENING: "The timing is opening new possibilities.",
        TransitType.CLOSURE: "The timing supports endings and release.",
        TransitType.RIPENING: "Things are ripening but not ready—this is a formation phase.",
        TransitType.NEUTRAL: "No strong transit is forcing the pace.",
    }
    parts.append(TYPE_LEADS.get(overall_type, "The timing is relatively neutral."))
    
    # Add foreground evidence
    if foreground:
        top = foreground[0]
        if top.strength >= 0.6:
            parts.append(top.evidence_statement)
        elif top.strength >= 0.4:
            parts.append(f"Moderate: {top.evidence_statement}")
    
    # Add moon context
    moon_phase = moon_context.get("phase_name", "")
    moon_sign = moon_context.get("sign", "")
    if moon_phase and moon_sign:
        moon_summary = f"The Moon in {moon_sign} ({moon_phase}) colors the emotional field with {moon_context.get('emotional_tone', 'varying intensity')}."
        parts.append(moon_summary)
    
    # Join
    return " ".join(parts)


# =============================================================================
# PATTERN-SPECIFIC TRANSIT INTERPRETATION
# =============================================================================

def interpret_transit_for_pattern(
    hierarchy: TransitHierarchy,
    pattern_family: str,
    mode: str = "exploratory"
) -> Dict[str, Any]:
    """
    Generate pattern-specific transit interpretation.
    This bridges raw transit data to pattern-relevant meaning.
    """
    
    # Pattern-transit resonance map
    PATTERN_TRANSIT_INTERPRETATIONS = {
        "stall": {
            TransitType.FORCING: "External timing is pushing for action, but you're paused. The stall may be protective—the timing is demanding something you're not ready for.",
            TransitType.PAUSE_REVIEW: "The timing itself supports this pause. It's not resistance—it's correct pacing. The stall aligns with what the sky is doing.",
            TransitType.THRESHOLD: "You're at a real threshold, and the sky is reflecting it. The pause is the moment before the choice.",
            TransitType.OVERREACH_RISK: "The timing carries overreach energy. Your stall may be wisdom—pushing now risks premature commitment.",
            TransitType.OPENING: "New possibilities are opening, but you're paused. The stall may mean you haven't seen the right opening yet.",
            TransitType.CLOSURE: "The timing supports endings. The stall might be connected to something that needs to complete before you move.",
            TransitType.RIPENING: "This is a ripening phase. The stall isn't blockage—it's development. Not ready yet is the correct read.",
            TransitType.NEUTRAL: "No strong transit is forcing this pause. The signal is more internal than external—something hasn't settled inside.",
        },
        "push_pull": {
            TransitType.FORCING: "The timing is creating action pressure while you're feeling pulled both ways. One direction may be more aligned with the external push.",
            TransitType.PAUSE_REVIEW: "The timing favors review, but you're feeling pulled to act. The back-and-forth may resolve if you wait.",
            TransitType.THRESHOLD: "You're at a genuine threshold. The push-pull is the feeling of standing at a real crossroads with the timing.",
            TransitType.OVERREACH_RISK: "The timing has overreach energy. Neither direction may be ready—forcing either could create problems.",
            TransitType.NEUTRAL: "No transit is forcing this choice. The back-and-forth is internally generated, which means the answer is internal too.",
        },
        "expression": {
            TransitType.FORCING: "The timing is pushing for expression, but something is held back. There may be good reason for the silence.",
            TransitType.PAUSE_REVIEW: "The timing supports holding back. What's unsaid may correctly be waiting for a better moment.",
            TransitType.THRESHOLD: "You're at an expression threshold. The timing is asking: say it or release it?",
            TransitType.NEUTRAL: "No transit is demanding expression. The silence is self-generated—which makes it more significant.",
        },
        "clarity": {
            TransitType.PAUSE_REVIEW: "The timing is foggy by nature. Confusion aligns with the sky—don't force premature clarity.",
            TransitType.THRESHOLD: "You're at a clarity threshold. The fog may lift soon if you don't force.",
            TransitType.OPENING: "New understanding is possible. The fog may be protecting you from seeing too much too fast.",
            TransitType.NEUTRAL: "No transit is blocking clarity. If fog persists, it's more internal than external.",
        },
        "control": {
            TransitType.FORCING: "The timing is pressuring action, which explains the grip. The control may be appropriate response to real pressure.",
            TransitType.OVERREACH_RISK: "The timing has overreach energy. The grip might be creating the instability it's trying to prevent.",
            TransitType.PAUSE_REVIEW: "The timing supports release, not grip. Consider whether the control is helping or hindering.",
            TransitType.NEUTRAL: "No transit is driving this control need. The grip is internally generated—what are you protecting?",
        },
        "release": {
            TransitType.CLOSURE: "The timing supports this release. What you're letting go of is aligned with the sky.",
            TransitType.OPENING: "Releasing creates space for what's opening. The timing supports this.",
            TransitType.PAUSE_REVIEW: "The timing supports release and review. Let go as a form of completion.",
            TransitType.NEUTRAL: "No transit is forcing this release. It's arising from internal readiness—which makes it authentic.",
        },
        "movement": {
            TransitType.FORCING: "The timing supports this forward movement. The action impulse is externally supported.",
            TransitType.OPENING: "New pathways are opening. The movement is aligned with what's becoming possible.",
            TransitType.OVERREACH_RISK: "Caution—the timing has overreach energy. The forward movement may be ahead of readiness.",
            TransitType.NEUTRAL: "No transit is driving this movement. The forward impulse is internally generated—check if it's readiness or impatience.",
        },
    }
    
    # Get interpretation
    family_interps = PATTERN_TRANSIT_INTERPRETATIONS.get(pattern_family, PATTERN_TRANSIT_INTERPRETATIONS["stall"])
    interp = family_interps.get(hierarchy.overall_type, family_interps.get(TransitType.NEUTRAL, "The timing doesn't strongly influence this pattern."))
    
    # Mode-adjust length
    if mode == "grounding":
        # Truncate to first sentence
        interp = interp.split(".")[0] + "." if "." in interp else interp
    
    return {
        "interpretation": interp,
        "transit_type": hierarchy.overall_type.value,
        "strength": hierarchy.overall_strength,
        "evidence": hierarchy.evidence_summary,
        "debug": hierarchy.debug_data,
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def get_astrology_evidence_for_diagnosis(
    pattern_family: str,
    mode: str = "exploratory",
    dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Main entry point for getting astrology evidence for the cross-lens diagnosis.
    
    Returns:
        - summary: User-facing evidence summary
        - implication: Pattern-specific interpretation
        - transit_type: The dominant transit type
        - strength: Overall transit strength
        - debug: Debug data for verification
    """
    
    hierarchy = build_transit_hierarchy(dt)
    pattern_interp = interpret_transit_for_pattern(hierarchy, pattern_family, mode)
    
    # Build the final evidence package
    return {
        "summary": hierarchy.evidence_summary,
        "implication": pattern_interp["interpretation"],
        "transit_type": hierarchy.overall_type.value,
        "strength": hierarchy.overall_strength,
        "moon_context": {
            "sign": hierarchy.moon_context.get("sign"),
            "phase": hierarchy.moon_context.get("phase_name"),
            "meaning": hierarchy.moon_context.get("phase_meaning"),
        },
        "foreground": [
            {
                "planet": t.planet,
                "aspect": t.aspect,
                "target": t.target,
                "strength": t.strength,
                "evidence": t.evidence_statement,
            }
            for t in hierarchy.foreground
        ],
        "background": hierarchy.background_climate,
        "debug": pattern_interp.get("debug", {}),
    }
