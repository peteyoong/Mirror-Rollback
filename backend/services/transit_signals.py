"""
Transit Signal Engine for Human Design Today Tab

Computes real-time transit signals by comparing:
- User's natal chart (defined gates, channels, centers)
- Current planetary transits (Sun, Moon, Mercury, Venus, Mars)

Signal Types:
1. Channel Completion - Transit completes a defined channel
2. Center Activation - Transit defines an undefined center
3. Authority Amplification - Transit activates authority-related centers
4. Open Center Pressure - Transit hits undefined centers (distortion risk)
5. Natal Reinforcement - Transit strengthens already-defined energy

Returns TOP 3 signals ranked by strength for frontend rendering.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# HUMAN DESIGN CONSTANTS
# =============================================================================

# Channel definitions (pairs of gates)
HD_CHANNELS = {
    "1-8": {"name": "Inspiration", "centers": ["G", "Throat"]},
    "2-14": {"name": "The Beat", "centers": ["G", "Sacral"]},
    "3-60": {"name": "Mutation", "centers": ["Sacral", "Root"]},
    "4-63": {"name": "Logic", "centers": ["Ajna", "Head"]},
    "5-15": {"name": "Rhythm", "centers": ["Sacral", "G"]},
    "6-59": {"name": "Intimacy", "centers": ["Solar Plexus", "Sacral"]},
    "7-31": {"name": "The Alpha", "centers": ["G", "Throat"]},
    "9-52": {"name": "Concentration", "centers": ["Sacral", "Root"]},
    "10-20": {"name": "Awakening", "centers": ["G", "Throat"]},
    "10-34": {"name": "Exploration", "centers": ["G", "Sacral"]},
    "10-57": {"name": "Perfected Form", "centers": ["G", "Spleen"]},
    "11-56": {"name": "Curiosity", "centers": ["Ajna", "Throat"]},
    "12-22": {"name": "Openness", "centers": ["Throat", "Solar Plexus"]},
    "13-33": {"name": "The Prodigal", "centers": ["G", "Throat"]},
    "16-48": {"name": "The Wavelength", "centers": ["Throat", "Spleen"]},
    "17-62": {"name": "Acceptance", "centers": ["Ajna", "Throat"]},
    "18-58": {"name": "Judgment", "centers": ["Spleen", "Root"]},
    "19-49": {"name": "Synthesis", "centers": ["Root", "Solar Plexus"]},
    "20-34": {"name": "Charisma", "centers": ["Throat", "Sacral"]},
    "20-57": {"name": "The Brainwave", "centers": ["Throat", "Spleen"]},
    "21-45": {"name": "The Money Line", "centers": ["Heart", "Throat"]},
    "23-43": {"name": "Structuring", "centers": ["Throat", "Ajna"]},
    "24-61": {"name": "Awareness", "centers": ["Ajna", "Head"]},
    "25-51": {"name": "Initiation", "centers": ["G", "Heart"]},
    "26-44": {"name": "Surrender", "centers": ["Heart", "Spleen"]},
    "27-50": {"name": "Preservation", "centers": ["Sacral", "Spleen"]},
    "28-38": {"name": "Struggle", "centers": ["Spleen", "Root"]},
    "29-46": {"name": "Discovery", "centers": ["Sacral", "G"]},
    "30-41": {"name": "Recognition", "centers": ["Solar Plexus", "Root"]},
    "32-54": {"name": "Transformation", "centers": ["Spleen", "Root"]},
    "34-57": {"name": "Power", "centers": ["Sacral", "Spleen"]},
    "35-36": {"name": "Transitoriness", "centers": ["Throat", "Solar Plexus"]},
    "37-40": {"name": "Community", "centers": ["Solar Plexus", "Heart"]},
    "39-55": {"name": "Emoting", "centers": ["Root", "Solar Plexus"]},
    "42-53": {"name": "Maturation", "centers": ["Sacral", "Root"]},
    "47-64": {"name": "Abstraction", "centers": ["Ajna", "Head"]},
}

# Gate to Center mapping
GATE_TO_CENTER = {
    # Head
    64: "Head", 61: "Head", 63: "Head",
    # Ajna
    47: "Ajna", 24: "Ajna", 4: "Ajna", 17: "Ajna", 43: "Ajna", 11: "Ajna",
    # Throat
    62: "Throat", 23: "Throat", 56: "Throat", 35: "Throat", 12: "Throat", 45: "Throat",
    31: "Throat", 8: "Throat", 33: "Throat", 20: "Throat", 16: "Throat",
    # G Center
    7: "G", 1: "G", 13: "G", 25: "G", 46: "G", 2: "G", 15: "G", 10: "G",
    # Heart/Ego
    21: "Heart", 51: "Heart", 26: "Heart", 40: "Heart",
    # Solar Plexus
    36: "Solar Plexus", 22: "Solar Plexus", 37: "Solar Plexus", 6: "Solar Plexus",
    49: "Solar Plexus", 55: "Solar Plexus", 30: "Solar Plexus",
    # Sacral
    34: "Sacral", 5: "Sacral", 14: "Sacral", 29: "Sacral", 59: "Sacral",
    9: "Sacral", 3: "Sacral", 42: "Sacral", 27: "Sacral",
    # Spleen
    48: "Spleen", 57: "Spleen", 44: "Spleen", 50: "Spleen", 32: "Spleen",
    28: "Spleen", 18: "Spleen",
    # Root
    58: "Root", 38: "Root", 54: "Root", 53: "Root", 60: "Root", 52: "Root",
    19: "Root", 39: "Root", 41: "Root",
}

# Gate to Channel partner mapping
GATE_CHANNEL_PARTNERS = {}
for channel_key, channel_data in HD_CHANNELS.items():
    gates = [int(g) for g in channel_key.split("-")]
    GATE_CHANNEL_PARTNERS[gates[0]] = gates[1]
    GATE_CHANNEL_PARTNERS[gates[1]] = gates[0]

# Authority-related centers
AUTHORITY_CENTERS = {
    "Emotional": "Solar Plexus",
    "Sacral": "Sacral",
    "Splenic": "Spleen",
    "Ego": "Heart",
    "Self-Projected": "G",
    "Mental": "Ajna",
}

# Signal type enum
class SignalType(str, Enum):
    CHANNEL_COMPLETION = "channel_completion"
    CENTER_ACTIVATION = "center_activation"
    AUTHORITY_AMPLIFICATION = "authority_amplification"
    OPEN_CENTER_PRESSURE = "open_center_pressure"
    NATAL_REINFORCEMENT = "natal_reinforcement"


@dataclass
class TransitSignal:
    """Represents a single transit signal."""
    signal_type: SignalType
    strength: float  # 0-1, higher = more significant
    transit_planet: str
    transit_gate: int
    user_gate: Optional[int] = None
    center: Optional[str] = None
    channel_name: Optional[str] = None
    
    # Human-readable content
    title: str = ""
    what_happening: str = ""
    why_happening: str = ""
    how_shows_up: str = ""
    best_move: str = ""
    label: str = ""  # "Temporary activation" / "Reinforcing your design" / "Temporary completion"
    

@dataclass
class DominantSignal:
    """Represents the ONE dominant theme that all content should orbit."""
    theme: str  # Core idea in one sentence
    theme_id: str  # Identifier: "emotional_wait", "mental_pressure", etc.
    confidence: float  # 0.0 - 1.0
    center_focus: Optional[str] = None  # Primary center involved
    field_alignment: bool = False  # Does field context support this?
    supporting_signals: List[str] = None  # List of signal types that align
    
    # Theme-specific content for each section
    activation_framing: str = ""
    opportunity_framing: str = ""
    friction_framing: str = ""
    today_framing: str = ""
    week_framing: str = ""
    month_framing: str = ""


# =============================================================================
# DOMINANT SIGNAL THEMES - Core narratives that unify the experience
# =============================================================================

DOMINANT_THEMES = {
    "emotional_wait": {
        "theme": "You may feel like something needs to be decided—but clarity isn't ready yet",
        "centers": ["Solar Plexus"],
        "field_tones": ["reset", "turning_point"],
        # MIRROR DOMINANT (What's Active Now): Hook → Name → Reframe → Action
        "activation": "You may feel your emotions pulling harder than usual. That intensity is data, not a deadline.",
        "opportunity": "If you let the wave pass without forcing an answer, the knowing comes on its own.",
        "friction": "Part of you wants certainty now. That's the trap—pushing here costs you clarity.",
        # ASTROLOGIST DOMINANT (Timing): Pattern + How to hold it
        "today": "You may feel pressure to decide. That pressure isn't clarity—let it move through.",
        "week": "You might notice the same feeling keeps returning. It's showing you what actually matters.",
        "month": "This cycle is resetting how you relate to uncertainty. Let that be the lesson.",
    },
    "mental_pressure": {
        "theme": "Your mind wants answers it doesn't need yet",
        "centers": ["Ajna", "Head"],
        "field_tones": ["reset", "clarity"],
        # MIRROR DOMINANT
        "activation": "You may notice thoughts demanding resolution. That urgency is mental pressure, not truth.",
        "opportunity": "You can watch the patterns without concluding. The understanding comes after, not during.",
        "friction": "Part of you wants to believe your first thought. That's the mistake here.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel mental loops spinning. Notice them without gripping.",
        "week": "You might notice the same thought keeps returning. It's trying to show you something.",
        "month": "This phase is recalibrating your relationship with certainty. Let questions exist unanswered.",
    },
    "energy_available": {
        "theme": "Something is ready to move—use it consciously",
        "centers": ["Sacral", "Root"],
        "field_tones": ["building", "clarity"],
        # MIRROR DOMINANT
        "activation": "You may feel more available than usual. That pull is real—follow it.",
        "opportunity": "If you channel this toward what actually has pull, there's traction here.",
        "friction": "Part of you may want to spray this everywhere. That wastes it.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel pulled toward something. Follow the strongest pull.",
        "week": "You might notice where effort flows versus where you have to force. That's the signal.",
        "month": "This cycle is teaching you what actually sustains versus what depletes.",
    },
    "instinct_amplified": {
        "theme": "Your body is speaking louder—listen before your mind overrides",
        "centers": ["Spleen"],
        "field_tones": ["clarity", "building"],
        # MIRROR DOMINANT
        "activation": "You may feel your gut responding faster than usual. Trust what lands instantly.",
        "opportunity": "If you act on the first hit, you catch what the body knows.",
        "friction": "Part of you may want to rationalize away what you felt. That's the regret pattern.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel something in your body before you understand it. Act on that.",
        "week": "You might notice which instincts keep proving right. That's building trust.",
        "month": "This phase is deepening your relationship with body intelligence.",
    },
    "expression_ready": {
        "theme": "Something wants to be said—timing matters",
        "centers": ["Throat"],
        "field_tones": ["building", "clarity"],
        # MIRROR DOMINANT
        "activation": "You may feel words forming, ready or not. That urge is real—but timing matters.",
        "opportunity": "If you wait for invitation, what comes out lands deeper.",
        "friction": "Part of you wants to say it all now. That forces what isn't ready.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel something wants to come out. Notice what it is.",
        "week": "You might notice a theme keeps wanting expression. Let it form.",
        "month": "This cycle is about finding your voice in this area of life.",
    },
    "direction_questioning": {
        "theme": "Where you're going feels less certain—that's part of it",
        "centers": ["G"],
        "field_tones": ["reset", "turning_point"],
        # MIRROR DOMINANT
        "activation": "You may feel questions about direction are louder. That uncertainty is recalibration, not failure.",
        "opportunity": "If you let go of needing to know the path, the next step shows itself.",
        "friction": "Part of you wants to force a direction. That creates false paths.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel uncertain about where you're going. Don't commit yet.",
        "week": "You might notice what keeps calling you back. That's the real signal.",
        "month": "This phase is recalibrating your sense of purpose. Let it take time.",
    },
    "willpower_test": {
        "theme": "What you actually want is being tested",
        "centers": ["Heart", "Ego"],
        "field_tones": ["building", "clarity"],
        # MIRROR DOMINANT
        "activation": "You may feel the drive to prove something. That intensity is real—but check what's underneath.",
        "opportunity": "If you commit only to what genuinely matters, this fuels it.",
        "friction": "Part of you wants to overcommit. That's ego, not will.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel the urge to push. Check if it's real desire or performance.",
        "week": "You might notice what you keep returning to. That's what actually matters.",
        "month": "This cycle is teaching you what you're actually willing to sustain.",
    },
    "reset_active": {
        "theme": "Something is dissolving—don't fill the space yet",
        "centers": [],
        "field_tones": ["reset"],
        # MIRROR DOMINANT
        "activation": "You may feel something shifting beneath the surface. That's not loss—it's clearing.",
        "opportunity": "If you create space without filling it, what's next has room to form.",
        "friction": "Part of you wants to understand this too early. That blocks what's coming.",
        # ASTROLOGIST DOMINANT
        "today": "You may feel the urge to grip. Let go instead.",
        "week": "You might notice old patterns loosening. Don't re-tighten them.",
        "month": "This is a clearing phase. The new shape comes after, not during.",
    },
}



def _enhance_dominant_for_stacked(dominant: 'DominantSignal', transit_stack: Dict, copy_tone: Dict) -> 'DominantSignal':
    """
    Enhance the dominant signal copy when we have stacked transits (phase_shift).
    
    Makes copy more:
    - Direct
    - Interruptive  
    - Less explanatory
    - More "this matters now"
    """
    from dataclasses import replace
    
    interaction_theme = transit_stack.get("interaction_theme", "")
    copy_direction = transit_stack.get("copy_direction", "")
    
    # Enhance activation framing for stacked events
    enhanced_activation = dominant.activation_framing
    if copy_direction and not enhanced_activation.startswith("This isn't"):
        enhanced_activation = f"{copy_direction}"
    
    # Make today framing more urgent for phase_shift
    enhanced_today = dominant.today_framing
    if "phase_shift" in transit_stack.get("classification", ""):
        if not enhanced_today.startswith("This isn't"):
            enhanced_today = f"This isn't a normal day. {enhanced_today}"
    
    return DominantSignal(
        theme=dominant.theme,
        theme_id=dominant.theme_id,
        confidence=min(0.98, dominant.confidence * 1.1),  # Boost confidence for stacked
        center_focus=dominant.center_focus,
        field_alignment=dominant.field_alignment,
        supporting_signals=dominant.supporting_signals,
        activation_framing=enhanced_activation,
        opportunity_framing=dominant.opportunity_framing,
        friction_framing=dominant.friction_framing,
        today_framing=enhanced_today,
        week_framing=dominant.week_framing,
        month_framing=dominant.month_framing,
    )



def select_dominant_signal(
    all_signals: List[TransitSignal],
    field_context: Dict[str, str],
    defined_centers: List[str],
    undefined_centers: List[str]
) -> DominantSignal:
    """
    Analyze all signals and select ONE dominant theme.
    Everything else will orbit this central idea.
    """
    field_tone = field_context.get("field_tone", "clarity")
    clarity_level = field_context.get("clarity_level", "high")
    
    # Count signals by center
    center_counts = {}
    center_strengths = {}
    for sig in all_signals:
        if sig.center:
            center = sig.center
            center_counts[center] = center_counts.get(center, 0) + 1
            center_strengths[center] = max(center_strengths.get(center, 0), sig.strength)
    
    # Score each potential theme
    theme_scores = {}
    
    for theme_id, theme_data in DOMINANT_THEMES.items():
        score = 0.0
        
        # 1. Field alignment bonus (+0.3)
        if field_tone in theme_data.get("field_tones", []):
            score += 0.3
        
        # 2. Center activation bonus
        theme_centers = theme_data.get("centers", [])
        for center in theme_centers:
            if center in center_counts:
                score += center_counts[center] * 0.15
                score += center_strengths.get(center, 0) * 0.2
        
        # 3. Low clarity favors "wait" themes
        if clarity_level == "low" and theme_id in ["emotional_wait", "reset_active", "direction_questioning"]:
            score += 0.25
        
        # 4. Undefined center bonus (temporary = higher impact)
        for center in theme_centers:
            if center in undefined_centers:
                score += 0.1
        
        theme_scores[theme_id] = score
    
    # Select highest scoring theme
    best_theme_id = max(theme_scores, key=theme_scores.get) if theme_scores else "reset_active"
    best_score = theme_scores.get(best_theme_id, 0.5)
    theme_data = DOMINANT_THEMES[best_theme_id]
    
    # Determine primary center focus
    center_focus = None
    if theme_data.get("centers"):
        for c in theme_data["centers"]:
            if c in center_counts:
                center_focus = c
                break
        if not center_focus:
            center_focus = theme_data["centers"][0] if theme_data["centers"] else None
    
    # Create supporting signals list
    supporting = []
    for sig in all_signals:
        if sig.center and sig.center in theme_data.get("centers", []):
            supporting.append(str(sig.signal_type))
    
    return DominantSignal(
        theme=theme_data["theme"],
        theme_id=best_theme_id,
        confidence=min(0.95, 0.5 + best_score),
        center_focus=center_focus,
        field_alignment=field_tone in theme_data.get("field_tones", []),
        supporting_signals=supporting[:3],
        activation_framing=theme_data.get("activation", ""),
        opportunity_framing=theme_data.get("opportunity", ""),
        friction_framing=theme_data.get("friction", ""),
        today_framing=theme_data.get("today", ""),
        week_framing=theme_data.get("week", ""),
        month_framing=theme_data.get("month", ""),
    )


def unify_signals_around_theme(
    signals: List[TransitSignal],
    dominant: DominantSignal,
    field_context: Dict[str, str]
) -> List[TransitSignal]:
    """
    Rewrite signal content to align with the dominant theme.
    This ensures ONE coherent narrative across all sections.
    """
    if len(signals) < 3:
        return signals
    
    # Signal 0 = Activation - articulates the dominant theme most clearly
    signals[0].how_shows_up = dominant.activation_framing
    
    # Signal 1 = Opportunity - how to work WITH the dominant theme  
    signals[1].how_shows_up = dominant.opportunity_framing
    signals[1].best_move = dominant.opportunity_framing
    
    # Signal 2 = Friction - what goes wrong if you resist
    signals[2].how_shows_up = dominant.friction_framing
    signals[2].best_move = dominant.friction_framing
    
    return signals


# =============================================================================
# CURRENT TRANSIT CALCULATIONS
# =============================================================================

def calculate_sun_gate(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate the current Sun gate based on sidereal position.
    Sun moves approximately 1° per day through the zodiac.
    """
    try:
        from calculations.human_design import longitude_to_gate
        
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Reference: Vernal equinox 2024 (Sun at 0° Aries tropical, ~5° Pisces sidereal)
        # March 20, 2024 03:06 UTC
        reference_time = datetime(2024, 3, 20, 3, 6, 0, tzinfo=timezone.utc)
        reference_longitude = 350.0  # ~350° sidereal (late Pisces/early Aries)
        
        # Calculate days since reference
        delta = dt - reference_time
        days_since = delta.total_seconds() / 86400.0
        
        # Sun moves ~0.9856°/day
        sun_daily_motion = 360.0 / 365.25
        longitude_traveled = days_since * sun_daily_motion
        
        # Calculate current sidereal longitude
        current_longitude = (reference_longitude + longitude_traveled) % 360.0
        
        # Convert to HD gate
        gate_info = longitude_to_gate(current_longitude)
        
        return {
            "planet": "Sun",
            "longitude": round(current_longitude, 2),
            "gate": gate_info.get('gate', 1),
            "line": gate_info.get('line', 1),
            "center": GATE_TO_CENTER.get(gate_info.get('gate', 1), "Unknown"),
        }
    except Exception as e:
        logger.error(f"Error calculating Sun gate: {e}")
        return {"planet": "Sun", "gate": 1, "line": 1, "center": "G"}


def calculate_earth_gate(sun_gate_info: Dict) -> Dict[str, Any]:
    """
    Calculate Earth gate (always opposite Sun, 180° away).
    """
    try:
        from calculations.human_design import longitude_to_gate
        
        earth_longitude = (sun_gate_info.get("longitude", 0) + 180) % 360
        gate_info = longitude_to_gate(earth_longitude)
        
        return {
            "planet": "Earth",
            "longitude": round(earth_longitude, 2),
            "gate": gate_info.get('gate', 1),
            "line": gate_info.get('line', 1),
            "center": GATE_TO_CENTER.get(gate_info.get('gate', 1), "Unknown"),
        }
    except Exception as e:
        logger.error(f"Error calculating Earth gate: {e}")
        return {"planet": "Earth", "gate": 2, "line": 1, "center": "G"}


def calculate_moon_gate_transit(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate current Moon gate using existing lunar_cycle service.
    """
    try:
        from services.lunar_cycle import get_current_moon_gate
        
        moon_data = get_current_moon_gate(dt)
        
        return {
            "planet": "Moon",
            "longitude": moon_data.get("moon_longitude", 0),
            "gate": moon_data.get("current_moon_gate", 1),
            "line": moon_data.get("gate_line", 1),
            "center": GATE_TO_CENTER.get(moon_data.get("current_moon_gate", 1), "Unknown"),
        }
    except Exception as e:
        logger.error(f"Error calculating Moon gate: {e}")
        return {"planet": "Moon", "gate": 28, "line": 1, "center": "Spleen"}


def get_current_transits(dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Get all current planetary transits relevant to Human Design.
    Returns Sun, Earth, Moon positions.
    """
    sun = calculate_sun_gate(dt)
    earth = calculate_earth_gate(sun)
    moon = calculate_moon_gate_transit(dt)
    
    # Log for debugging
    logger.info(f"[TransitSignals] Current transits: Sun G{sun['gate']}, Earth G{earth['gate']}, Moon G{moon['gate']}")
    
    return [sun, earth, moon]


# =============================================================================
# SIGNAL COMPUTATION
# =============================================================================

def compute_channel_completion_signals(
    transits: List[Dict],
    user_gates: List[int],
    user_channels: List[str]
) -> List[TransitSignal]:
    """
    Find transits that complete a channel with user's natal gates.
    This is the most powerful signal type.
    """
    signals = []
    
    for transit in transits:
        transit_gate = transit.get("gate")
        if transit_gate is None:
            continue
            
        # Check if transit gate's partner is in user's gates
        partner_gate = GATE_CHANNEL_PARTNERS.get(transit_gate)
        if partner_gate and partner_gate in user_gates:
            # This transit completes a channel!
            channel_key = f"{min(transit_gate, partner_gate)}-{max(transit_gate, partner_gate)}"
            channel_data = HD_CHANNELS.get(channel_key, {})
            
            # Skip if user already has this channel defined
            if channel_key in user_channels:
                continue
            
            signal = TransitSignal(
                signal_type=SignalType.CHANNEL_COMPLETION,
                strength=0.95,  # Highest priority
                transit_planet=transit.get("planet", ""),
                transit_gate=transit_gate,
                user_gate=partner_gate,
                center=None,
                channel_name=channel_data.get("name", channel_key),
                title=f"New Energy: {channel_data.get('name', 'Connection')}",
                what_happening="A new channel is temporarily active in your design.",
                why_happening=f"Transit completing Gate {transit_gate}—this energy isn't usually available.",
                how_shows_up="A capability opens up that you don't normally have.",
                best_move="Experiment with this while it's here.",
                label="Temporary completion",
            )
            signals.append(signal)
    
    return signals


def compute_center_activation_signals(
    transits: List[Dict],
    defined_centers: List[str],
    undefined_centers: List[str]
) -> List[TransitSignal]:
    """
    Find transits that activate (define) an undefined center.
    """
    signals = []
    
    for transit in transits:
        transit_gate = transit.get("gate")
        transit_center = transit.get("center")
        planet = transit.get("planet", "")
        
        if transit_center and transit_center.lower() not in [c.lower() for c in defined_centers]:
            # Transit is hitting an undefined center
            signal = TransitSignal(
                signal_type=SignalType.CENTER_ACTIVATION,
                strength=0.75,
                transit_planet=planet,
                transit_gate=transit_gate,
                center=transit_center,
                title=f"Your {transit_center} is Louder",
                what_happening=f"Your {transit_center.lower()} center is amplified right now.",
                why_happening="This center is open in your design—outside energy turns up its volume.",
                how_shows_up=get_center_activation_behavior(transit_center),
                best_move=get_center_activation_move(transit_center),
                label="Temporary activation",
            )
            signals.append(signal)
    
    return signals


def compute_authority_amplification_signals(
    transits: List[Dict],
    user_authority: str,
    defined_centers: List[str]
) -> List[TransitSignal]:
    """
    Find transits that amplify the user's decision-making authority.
    """
    signals = []
    
    # Determine the authority center
    authority_center = None
    for auth_type, center in AUTHORITY_CENTERS.items():
        if auth_type.lower() in user_authority.lower():
            authority_center = center
            break
    
    if not authority_center:
        return signals
    
    for transit in transits:
        transit_center = transit.get("center")
        planet = transit.get("planet", "")
        
        if transit_center and transit_center.lower() == authority_center.lower():
            # Transit is hitting the authority center
            signal = TransitSignal(
                signal_type=SignalType.AUTHORITY_AMPLIFICATION,
                strength=0.85,
                transit_planet=planet,
                transit_gate=transit.get("gate"),
                center=transit_center,
                title="Decision Clarity Heightened",
                what_happening=f"The {planet} is amplifying your {transit_center} center—where you feel into decisions.",
                why_happening=f"Your {transit_center} center is receiving extra energy right now.",
                how_shows_up=get_authority_amplification_behavior(user_authority),
                best_move=get_authority_amplification_move(user_authority),
                label="Reinforcing your design",
            )
            signals.append(signal)
    
    return signals


def compute_open_center_pressure_signals(
    transits: List[Dict],
    undefined_centers: List[str]
) -> List[TransitSignal]:
    """
    Find transits that create pressure on undefined centers (distortion risk).
    """
    signals = []
    
    for transit in transits:
        transit_center = transit.get("center")
        planet = transit.get("planet", "")
        
        if transit_center and transit_center.lower() in [c.lower() for c in undefined_centers]:
            # This is a friction signal - pressure on open center
            signal = TransitSignal(
                signal_type=SignalType.OPEN_CENTER_PRESSURE,
                strength=0.65,
                transit_planet=planet,
                transit_gate=transit.get("gate"),
                center=transit_center,
                title=f"Watch Your {transit_center}",
                what_happening=f"The {planet} is pressing on your open {transit_center} center.",
                why_happening="Open centers amplify outside energy—this one is getting extra right now.",
                how_shows_up=get_open_center_pressure_behavior(transit_center),
                best_move=get_open_center_pressure_move(transit_center),
                label="Temporary activation",
            )
            signals.append(signal)
    
    return signals


def compute_natal_reinforcement_signals(
    transits: List[Dict],
    user_gates: List[int],
    defined_centers: List[str]
) -> List[TransitSignal]:
    """
    Find transits that reinforce already-defined energy.
    """
    signals = []
    
    for transit in transits:
        transit_gate = transit.get("gate")
        planet = transit.get("planet", "")
        
        if transit_gate in user_gates:
            # Transit is hitting a gate the user already has
            center = GATE_TO_CENTER.get(transit_gate, "")
            signal = TransitSignal(
                signal_type=SignalType.NATAL_REINFORCEMENT,
                strength=0.70,
                transit_planet=planet,
                transit_gate=transit_gate,
                user_gate=transit_gate,
                center=center,
                title=f"Your Gate {transit_gate} Amplified",
                what_happening=f"The {planet} is reinforcing energy you already carry.",
                why_happening=f"Gate {transit_gate} is part of your design. The {planet} is turning up its volume.",
                how_shows_up="You may feel more 'yourself' than usual in this area—or notice this theme appearing more prominently in your life.",
                best_move="Lean into this amplified version of yourself. This is your design, just louder.",
                label="Reinforcing your design",
            )
            signals.append(signal)
    
    return signals


# =============================================================================
# BEHAVIOR HELPERS
# =============================================================================

def get_center_activation_behavior(center: str) -> str:
    """Get behavior description for center activation - personalized."""
    behaviors = {
        "Head": "You might feel mental pressure, inspiration, or questions flooding in. Ideas may want your attention more than usual.",
        "Ajna": "You may feel thinking is more certain or fixed. Part of you might get attached to being 'right'.",
        "Throat": "You might notice the desire to speak, express, or manifest is stronger. Words may want to come out.",
        "G": "You may feel your sense of direction or identity is stronger—or questions arise about where you're going.",
        "Heart": "You might notice willpower, ambition, or the need to prove yourself is heightened. Part of you may want to overcommit.",
        "Solar Plexus": "You may feel emotional sensitivity is heightened. Feelings run deeper than usual.",
        "Sacral": "You might feel sustainable energy is more available—or there's pressure to 'do' more.",
        "Spleen": "You may notice instincts and intuition are sharper. Body awareness feels amplified.",
        "Root": "You might feel pressure to act, start things, or stress about time shows up more strongly.",
    }
    return behaviors.get(center, "You may notice this area of your life feels more active than usual.")


def get_center_activation_move(center: str) -> str:
    """Get best move for center activation - personalized."""
    moves = {
        "Head": "You may feel every idea is urgent. Let inspiration flow without needing to act on everything—not every idea is yours to pursue.",
        "Ajna": "Part of you may want to grip your thoughts tightly. Notice them without holding on—your natural flexibility is a gift.",
        "Throat": "You might feel everything needs to be said. Speak when truly invited—this extra expression energy doesn't mean everything belongs out loud.",
        "G": "You may feel pressure to know where you're going. Follow what feels right without needing the whole path yet.",
        "Heart": "Part of you may feel the need to prove yourself. Notice where you're pushing—your value isn't in question.",
        "Solar Plexus": "You might want to act on how you feel right now. Let emotions move through without making permanent decisions from temporary feelings.",
        "Sacral": "You may feel like you have to use all this energy. Use it for what genuinely excites you—don't just fill time because you 'can'.",
        "Spleen": "You might feel your instincts pulling you. Trust the instant knowing, but don't let fear-based signals run everything.",
        "Root": "Part of you may feel everything is urgent. Notice what's truly time-sensitive versus manufactured pressure—most things can wait.",
    }
    return moves.get(center, "You may feel this energy strongly. Be aware it's temporary—observe without over-identifying.")


def get_authority_amplification_behavior(authority: str) -> str:
    """Get behavior for authority amplification."""
    auth_lower = authority.lower()
    if "emotional" in auth_lower:
        return "Emotional rhythm runs deeper right now. Clarity will come—but it needs time to settle."
    if "sacral" in auth_lower:
        return "Gut responses feel clearer and more reliable. The pull toward or away from things is more pronounced."
    if "splenic" in auth_lower:
        return "Instinctual knowing is sharper. What the body signals in the moment is more pronounced."
    if "ego" in auth_lower:
        return "Willpower and sense of what you truly want is clearer. Trust the heart's direction."
    if "self" in auth_lower or "projected" in auth_lower:
        return "Sense of self and direction feels more accessible. What you hear yourself saying matters now."
    return "The natural way of making decisions is heightened. Trust the process more than usual."


def get_authority_amplification_move(authority: str) -> str:
    """Get best move for authority amplification."""
    auth_lower = authority.lower()
    if "emotional" in auth_lower:
        return "Use this time for decisions that have been waiting for clarity. Sleep on anything new."
    if "sacral" in auth_lower:
        return "Pay extra attention to your gut. Let responses guide you rather than mental reasoning."
    if "splenic" in auth_lower:
        return "Act on clear instincts quickly. The knowing won't repeat—trust the first hit."
    if "ego" in auth_lower:
        return "Check in with what you genuinely want. Make commitments only from true desire."
    if "self" in auth_lower or "projected" in auth_lower:
        return "Talk through decisions with trusted people. Notice what truth emerges as you speak."
    return "Lean into your natural decision-making process. It's working better than usual."


def get_open_center_pressure_behavior(center: str) -> str:
    """Get behavior for open center pressure - personalized."""
    behaviors = {
        "Head": "You may feel overwhelmed by questions or inspiration that isn't actually yours to solve.",
        "Ajna": "Part of you may feel pressure to have answers or appear certain about things you don't know.",
        "Throat": "You might feel pressure to speak before you're ready or attract attention you don't need.",
        "G": "You may feel lost or unclear about direction, or too attached to a fixed identity that isn't really you.",
        "Heart": "Part of you may feel pressure to prove your worth or compete when you don't need to.",
        "Solar Plexus": "You might absorb emotions from others and mistake them for your own.",
        "Sacral": "You may feel like you should push past your natural limits or feel guilty for resting.",
        "Spleen": "Part of you may ignore your instincts or hold onto things past their time.",
        "Root": "You might feel unnecessary urgency or rush decisions that can actually wait.",
    }
    return behaviors.get(center, "You may feel pressure or amplification in this area that isn't truly yours.")


def get_open_center_pressure_move(center: str) -> str:
    """Get best move for open center pressure - personalized."""
    moves = {
        "Head": "You may feel like you need to solve every question. Let them exist without needing to answer them all—not every inspiration is your responsibility.",
        "Ajna": "Part of you may feel you should have answers. It's okay not to know—your openness here is wisdom, not weakness.",
        "Throat": "You might feel the urge to fill silence. Wait for invitation before speaking—silence is also communication.",
        "G": "You may feel lost without a clear direction. Trust that it will become clear—you don't need to force identity.",
        "Heart": "Part of you may feel you have something to prove. You don't—your value exists whether you push or not.",
        "Solar Plexus": "You might be carrying feelings that aren't yours. Check whose emotions you're holding—return what doesn't belong to you.",
        "Sacral": "You may feel guilty for not doing more. Rest is correct for you—don't match others' energy output.",
        "Spleen": "Part of you may feel fear-driven. Notice what your body says, but don't let passing fears drive major decisions.",
        "Root": "You might feel like everything is urgent. Slow down—the urgency you feel may not reflect actual deadlines.",
    }
    return moves.get(center, "You may feel this energy strongly. Remember it's amplified, not yours—observe without over-reacting.")


# =============================================================================
# MAIN SIGNAL COMPUTATION
# =============================================================================

def compute_transit_signals(
    user_gates: List[int],
    user_channels: List[str],
    defined_centers: List[str],
    user_authority: str,
    user_type: str,
    field_context: Optional[Dict[str, str]] = None,
    dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Compute all transit signals for a user and return TOP 3.
    
    Args:
        user_gates: List of all gates in user's design
        user_channels: List of defined channel keys (e.g., "1-8")
        defined_centers: List of defined center names
        user_authority: User's authority type
        user_type: User's HD type
        field_context: Field context from field_signals (tone, clarity, pace)
        dt: Datetime for transit calculation (default: now)
    
    Returns:
        Dict with top 3 signals and metadata
    """
    # Get current transits
    transits = get_current_transits(dt)
    
    # Derive undefined centers
    all_centers = ["Head", "Ajna", "Throat", "G", "Heart", "Solar Plexus", "Sacral", "Spleen", "Root"]
    undefined_centers = [c for c in all_centers if c.lower() not in [dc.lower() for dc in defined_centers]]
    
    # Default field context if not provided
    if not field_context:
        field_context = {
            "field_tone": "clarity",
            "clarity_level": "high",
            "pace": "building",
            "dominant_message": "things are relatively stable",
        }
    
    # Compute all signal types
    all_signals = []
    
    # 1. Channel completions (highest priority)
    all_signals.extend(compute_channel_completion_signals(transits, user_gates, user_channels))
    
    # 2. Authority amplification (high priority for decision-making)
    all_signals.extend(compute_authority_amplification_signals(transits, user_authority, defined_centers))
    
    # 3. Center activations (good opportunities)
    all_signals.extend(compute_center_activation_signals(transits, defined_centers, undefined_centers))
    
    # 4. Natal reinforcement (moderate priority)
    all_signals.extend(compute_natal_reinforcement_signals(transits, user_gates, defined_centers))
    
    # 5. Open center pressure (friction signals)
    all_signals.extend(compute_open_center_pressure_signals(transits, undefined_centers))
    
    # Sort by strength and select top 3
    all_signals.sort(key=lambda s: s.strength, reverse=True)
    top_signals = all_signals[:3]
    
    # Ensure we always have 3 signals (pad with default if needed)
    while len(top_signals) < 3:
        top_signals.append(create_default_signal(user_type, len(top_signals)))
    
    # Apply field context adaptation to all signals
    adapted_signals = [adapt_signal_to_field(s, field_context, i == 0) for i, s in enumerate(top_signals)]
    
    # === LAYER 0: MULTI-TRANSIT CONVERGENCE ===
    # Detect if multiple major transits are converging
    from services.field_signals import (
        get_major_sky_events, 
        get_sky_dominant_override,
        detect_transit_convergence,
        get_field_climate_from_transit_stack,
        get_copy_tone_for_classification,
    )
    
    # Detect transit convergence FIRST
    transit_stack = detect_transit_convergence()
    
    # Get field climate derived from transit stack (Layer 1 updated)
    stacked_field_climate = get_field_climate_from_transit_stack(transit_stack)
    
    # Get copy tone rules based on classification
    copy_tone = get_copy_tone_for_classification(transit_stack.get("classification", "normal_flow"))
    
    # Merge stacked climate with original field context
    enhanced_field_context = {
        **field_context,
        **stacked_field_climate,
        "transit_stack": transit_stack,
        "copy_tone": copy_tone,
    }
    
    # === SKY PRIORITY LAYER ===
    major_sky_events = get_major_sky_events()
    sky_override = get_sky_dominant_override(major_sky_events)
    
    # === SELECT DOMINANT SIGNAL ===
    if sky_override:
        # Enhance with stacked context
        dominant = DominantSignal(
            theme=sky_override["theme"],
            theme_id=sky_override["theme_id"],
            confidence=sky_override["confidence"],
            center_focus=sky_override.get("center_focus"),
            field_alignment=True,
            supporting_signals=[],
            activation_framing=sky_override.get("activation_framing", ""),
            opportunity_framing=sky_override.get("opportunity_framing", ""),
            friction_framing=sky_override.get("friction_framing", ""),
            today_framing=sky_override.get("today_framing", ""),
            week_framing=sky_override.get("week_framing", ""),
            month_framing=sky_override.get("month_framing", ""),
        )
        
        # If stacked (phase_shift), enhance copy to be more direct/interruptive
        if transit_stack.get("classification") == "phase_shift":
            dominant = _enhance_dominant_for_stacked(dominant, transit_stack, copy_tone)
        
        logger.info(f"[TransitSignals] Sky event override active: {sky_override.get('sky_event')} (classification: {transit_stack.get('classification')})")
    else:
        # No major sky event - use personal HD signals
        dominant = select_dominant_signal(all_signals, enhanced_field_context, defined_centers, undefined_centers)
    
    # === UNIFY SIGNALS AROUND DOMINANT THEME ===
    unified_signals = unify_signals_around_theme(adapted_signals, dominant, enhanced_field_context)
    
    # FINAL POLISH: Differentiate signals and compress language
    polished_signals = differentiate_and_polish_signals(unified_signals, enhanced_field_context)
    
    # Assign roles: Biggest Activation, Opportunity, Friction
    categorized = categorize_signals(polished_signals)
    
    logger.info(f"[TransitSignals] Computed {len(all_signals)} signals, dominant theme: {dominant.theme_id} (confidence: {dominant.confidence:.2f}, classification: {transit_stack.get('classification')})")
    
    return {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "transits": transits,
        "signals": {
            "activation": signal_to_dict(categorized["activation"]),
            "opportunity": signal_to_dict(categorized["opportunity"]),
            "friction": signal_to_dict(categorized["friction"]),
        },
        # === Include transit stack (Layer 0) ===
        "transit_stack": transit_stack,
        # === Include dominant signal in response ===
        "dominant_signal": {
            "theme": dominant.theme,
            "theme_id": dominant.theme_id,
            "confidence": dominant.confidence,
            "center_focus": dominant.center_focus,
            "field_alignment": dominant.field_alignment,
            "sky_event": sky_override.get("sky_event") if sky_override else None,
            "today": dominant.today_framing,
            "week": dominant.week_framing,
            "month": dominant.month_framing,
        },
        # === Major sky events for frontend display ===
        "major_sky_events": major_sky_events[:2] if major_sky_events else [],
        "field_context": field_context,
        "user_context": {
            "type": user_type,
            "authority": user_authority,
            "defined_centers": defined_centers,
            "undefined_centers": undefined_centers,
        }
    }


def adapt_signal_to_field(signal: TransitSignal, field_context: Dict[str, str], is_primary: bool = False) -> TransitSignal:
    """
    Adapt a transit signal based on field context.
    
    Rules:
    - If clarity_level is "low", remove words like "clarity", "certain", "decisive"
    - Add field connection line
    - Adjust pace language
    """
    field_tone = field_context.get("field_tone", "clarity")
    clarity_level = field_context.get("clarity_level", "high")
    pace = field_context.get("pace", "building")
    dominant_message = field_context.get("dominant_message", "")
    
    # Create adapted copy
    adapted = TransitSignal(
        signal_type=signal.signal_type,
        strength=signal.strength,
        transit_planet=signal.transit_planet,
        transit_gate=signal.transit_gate,
        user_gate=signal.user_gate,
        center=signal.center,
        channel_name=signal.channel_name,
        title=signal.title,
        what_happening=signal.what_happening,
        why_happening=signal.why_happening,
        how_shows_up=signal.how_shows_up,
        best_move=signal.best_move,
        label=signal.label,
    )
    
    # === ADAPT TITLE BASED ON FIELD TONE ===
    if field_tone == "reset" and clarity_level == "low":
        # Override clarity-related titles
        if "clarity" in adapted.title.lower() or "heightened" in adapted.title.lower():
            adapted.title = "Something Is Stirring"
        elif "decision" in adapted.title.lower():
            adapted.title = "Clarity Isn't Here Yet"
    
    # === ADAPT WHAT'S HAPPENING (remove mechanical language) ===
    # Replace "The Sun is amplifying..." with "You're feeling..."
    adapted.what_happening = remove_mechanical_language(adapted.what_happening, signal.center)
    
    # === ADAPT WHY HAPPENING TO CONNECT TO FIELD ===
    # Add field connection line
    if is_primary and dominant_message:
        field_connection = f"This is intensified by {dominant_message}."
        if adapted.why_happening:
            adapted.why_happening = f"{adapted.why_happening} {field_connection}"
        else:
            adapted.why_happening = field_connection
    
    # === ADAPT HOW IT SHOWS UP BASED ON CLARITY ===
    if clarity_level == "low":
        adapted.how_shows_up = adapt_for_low_clarity(adapted.how_shows_up)
    elif clarity_level == "emerging":
        adapted.how_shows_up = adapt_for_emerging_clarity(adapted.how_shows_up)
    
    # === ADAPT BEST MOVE BASED ON PACE ===
    if pace == "slow":
        adapted.best_move = adapt_for_slow_pace(adapted.best_move)
    elif pace == "fast":
        adapted.best_move = adapt_for_fast_pace(adapted.best_move)
    
    # === REMOVE CONTRADICTING WORDS ===
    if clarity_level == "low":
        adapted.what_happening = remove_clarity_words(adapted.what_happening)
        adapted.how_shows_up = remove_clarity_words(adapted.how_shows_up)
        adapted.best_move = remove_clarity_words(adapted.best_move)
    
    return adapted


# =============================================================================
# SIGNAL DIFFERENTIATION + NARRATIVE COMPRESSION (FINAL POLISH)
# =============================================================================

# Role-specific templates for generating unique content per signal position
ROLE_SPECIFIC_CONTENT = {
    # ACTIVATION (position 0): What is strongest/unavoidable right now
    # Tone: descriptive + slightly intense, names the internal state
    0: {
        "how_shows_up_templates": [
            "You may feel like something needs your attention right now.",
            "Part of you might sense the intensity is hard to ignore.",
            "You might notice this pressing more than usual.",
            "It can feel like something is asking to be acknowledged.",
        ],
        "best_move_templates": [
            "You may feel pressure to act—acknowledge it before deciding anything.",
            "Part of you wants resolution. Name what you're feeling first.",
            "It can feel urgent. Let this move through rather than around you.",
            "You might want to push against it. Work with the intensity instead.",
        ],
    },
    # OPPORTUNITY (position 1): How to work WITH the energy
    # Tone: enabling / directional, shows what opens if they don't react
    1: {
        "how_shows_up_templates": [
            "You may notice there's extra bandwidth here if you use it consciously.",
            "Something feels available that isn't usually.",
            "Part of you might sense a door opening.",
            "It can feel like support is present where it wasn't before.",
        ],
        "best_move_templates": [
            "You might find this supports something you've been circling.",
            "If you don't force it, you may find this helps decisions settle.",
            "Part of you may want to grab it. Let it support what's already forming.",
            "You could channel this toward what actually has pull.",
        ],
    },
    # FRICTION (position 2): What goes wrong if misused
    # Tone: caution / grounding, calls out the specific mistake
    2: {
        "how_shows_up_templates": [
            "Part of you may want to do something about this right now.",
            "You might notice an urge to fix, solve, or control.",
            "It can feel like action is required. That's the distortion.",
            "You may feel pressure that isn't actually yours.",
        ],
        "best_move_templates": [
            "You may be about to make this harder than it needs to be.",
            "Part of you wants to react. Catch yourself before that takes over.",
            "It can feel urgent, but rushing here creates the problem.",
            "You might notice the pull to do something. That's what to pause on.",
        ],
    },
}


def differentiate_and_polish_signals(
    signals: List[TransitSignal], 
    field_context: Dict[str, str]
) -> List[TransitSignal]:
    """
    Final polish layer:
    1. Ensure each signal has a DISTINCT title and feeling
    2. Compress language to be vivid and short
    3. Remove any remaining explanatory HD language
    4. Apply strict field filter
    5. Remove generic safe language
    6. ENFORCE role differentiation (Activation/Opportunity/Friction)
    7. DEDUPLICATE sentences across all signals
    """
    field_tone = field_context.get("field_tone", "clarity")
    clarity_level = field_context.get("clarity_level", "high")
    
    # === STEP 1: Generate vivid, distinct titles ===
    used_title_themes = set()
    polished = []
    
    for i, signal in enumerate(signals):
        polished_signal = polish_single_signal(signal, i, field_tone, clarity_level, used_title_themes)
        polished.append(polished_signal)
    
    # === STEP 2: Ensure no duplicate titles ===
    polished = ensure_distinct_titles(polished, field_tone, clarity_level)
    
    # === STEP 3: ENFORCE ROLE DIFFERENTIATION ===
    polished = enforce_role_differentiation(polished, field_tone, clarity_level)
    
    # === STEP 4: DEDUPLICATE sentences across all signals ===
    polished = deduplicate_across_signals(polished)
    
    return polished


def enforce_role_differentiation(
    signals: List[TransitSignal],
    field_tone: str,
    clarity_level: str
) -> List[TransitSignal]:
    """
    Ensure each signal position has role-appropriate content.
    Position 0 = Activation (what's strongest)
    Position 1 = Opportunity (what's available)
    Position 2 = Friction (what to avoid)
    """
    import random
    
    for i, signal in enumerate(signals):
        if i not in ROLE_SPECIFIC_CONTENT:
            continue
            
        role_content = ROLE_SPECIFIC_CONTENT[i]
        
        # Check if how_shows_up needs role-specific enhancement
        current_how = signal.how_shows_up or ""
        if len(current_how) < 20 or "rhythm runs deeper" in current_how.lower():
            # Generate role-appropriate content
            templates = role_content["how_shows_up_templates"]
            base = random.choice(templates)
            # Combine with center-specific context if available
            if signal.center:
                center_context = get_center_feeling(signal.center)
                signal.how_shows_up = f"{base} {center_context}"
            else:
                signal.how_shows_up = base
        
        # Check if best_move needs role-specific enhancement
        current_move = signal.best_move or ""
        # If best_move looks generic or repeats common phrases
        generic_phrases = ["wait.", "notice", "let this", "use this time"]
        is_generic = any(p in current_move.lower()[:30] for p in generic_phrases) or len(current_move) < 15
        
        if is_generic:
            templates = role_content["best_move_templates"]
            signal.best_move = random.choice(templates)
    
    return signals


def get_center_feeling(center: str) -> str:
    """Get a human-readable feeling for each center - returns role-appropriate text with personal hooks."""
    import random
    
    feeling_variations = {
        "Solar Plexus": [
            "You may feel your emotions carrying more weight than usual.",
            "Part of you might notice feelings are closer to the surface.",
            "What you feel matters more right now than what you think.",
        ],
        "Ajna": [
            "You might notice thoughts wanting resolution faster than they should.",
            "Part of you may feel mental activity is heightened.",
            "Your mind may be working overtime—notice without gripping.",
        ],
        "Sacral": [
            "You might feel your body is louder about what it wants.",
            "Part of you may notice energy levels more distinctly.",
            "The pull toward or away from things may feel stronger.",
        ],
        "Spleen": [
            "You may feel your gut instincts are sharper than usual.",
            "Part of you might notice body wisdom speaking louder.",
            "Instinctual responses may feel more pronounced.",
        ],
        "Heart": [
            "You might feel the need to prove something is amplified.",
            "Part of you may notice willpower and drive are heightened.",
            "What matters to you may feel more urgent.",
        ],
        "Throat": [
            "You may feel words wanting to come out, ready or not.",
            "Part of you might notice expression feels more urgent.",
            "Something may want to be said.",
        ],
        "G": [
            "You might feel questions about direction are more present.",
            "Part of you may notice identity and purpose feel more in focus.",
            "Where you're going may matter more right now.",
        ],
        "Root": [
            "You may feel pressure to act or decide is heightened.",
            "Part of you might notice urgency is amplified.",
            "Time pressure may feel more intense than it actually is.",
        ],
        "Head": [
            "You might feel ideas flooding in faster than you can process.",
            "Part of you may notice inspiration and mental pressure are elevated.",
            "Questions and possibilities may be multiplying.",
        ],
    }
    
    variations = feeling_variations.get(center, ["You might notice something feels different here."])
    return random.choice(variations)


def deduplicate_across_signals(signals: List[TransitSignal]) -> List[TransitSignal]:
    """
    Ensure no two signals share the same sentence or near-duplicate content.
    """
    import re
    
    def normalize(text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Lowercase, remove punctuation, collapse whitespace
        text = re.sub(r'[^\w\s]', '', text.lower())
        return ' '.join(text.split())
    
    def sentences_overlap(text1: str, text2: str) -> bool:
        """Check if two texts share similar core content."""
        norm1 = normalize(text1)
        norm2 = normalize(text2)
        
        # Check for exact substring match
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Check for high word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        min_len = min(len(words1), len(words2))
        if min_len > 0 and overlap / min_len > 0.6:
            return True
        
        return False
    
    # Collect all unique sentences
    seen_content = {}
    
    for i, signal in enumerate(signals):
        for field in ['how_shows_up', 'best_move', 'what_happening']:
            text = getattr(signal, field, '') or ''
            if not text:
                continue
                
            # Check against previously seen content
            for prev_key, prev_text in seen_content.items():
                if sentences_overlap(text, prev_text):
                    # Generate alternative content based on position
                    new_text = generate_alternative_content(field, i, signal.center)
                    setattr(signal, field, new_text)
                    text = new_text
                    break
            
            # Store this content
            seen_content[f"{i}_{field}"] = text
    
    return signals


def generate_alternative_content(field: str, position: int, center: Optional[str]) -> str:
    """Generate alternative content when deduplication is needed."""
    import random
    
    alternatives = {
        'how_shows_up': {
            0: [  # Activation
                "The intensity is impossible to miss.",
                "This energy demands attention.",
                "Something is amplified and won't be ignored.",
            ],
            1: [  # Opportunity
                "There's traction here for what you've been waiting on.",
                "Energy is available that wasn't before.",
                "A window has opened—use it consciously.",
            ],
            2: [  # Friction
                "This is where misalignment becomes obvious.",
                "The distortion pattern tends to show up here.",
                "Watch for this pulling you off track.",
            ],
        },
        'best_move': {
            0: [  # Activation
                "Stay present with what's actually happening.",
                "Don't interpret it yet—just feel it.",
                "Let the intensity inform you without controlling you.",
            ],
            1: [  # Opportunity
                "Move toward what feels expansive.",
                "Move toward what feels naturally easy.",
                "Act where there's genuine pull.",
            ],
            2: [  # Friction
                "Pause when you notice this pattern.",
                "Name it before it names you.",
                "Notice when you're reacting without thinking.",
            ],
        },
        'what_happening': {
            0: ["Something significant is moving through your design."],
            1: ["An opportunity is present in how energy is configured."],
            2: ["There's a potential friction point to navigate."],
        },
    }
    
    field_alts = alternatives.get(field, {})
    position_alts = field_alts.get(position, field_alts.get(0, ["Something is present."]))
    
    return random.choice(position_alts)


def polish_single_signal(
    signal: TransitSignal,
    position: int,
    field_tone: str,
    clarity_level: str,
    used_themes: set
) -> TransitSignal:
    """
    Polish a single signal with vivid language and compression.
    """
    # Create a copy to modify
    polished = TransitSignal(
        signal_type=signal.signal_type,
        strength=signal.strength,
        transit_planet=signal.transit_planet,
        transit_gate=signal.transit_gate,
        user_gate=signal.user_gate,
        center=signal.center,
        channel_name=signal.channel_name,
        title=signal.title,
        what_happening=signal.what_happening,
        why_happening=signal.why_happening,
        how_shows_up=signal.how_shows_up,
        best_move=signal.best_move,
        label=signal.label,
    )
    
    # === GENERATE VIVID TITLE (4-6 words, emotionally sharp) ===
    polished.title = generate_vivid_title(signal, position, field_tone, clarity_level, used_themes)
    used_themes.add(polished.title.lower())
    
    # === COMPRESS AND VIVIFY CONTENT ===
    polished.what_happening = compress_and_vivify(
        polished.what_happening, 
        field_tone, 
        clarity_level,
        max_sentences=2
    )
    
    polished.how_shows_up = compress_and_vivify(
        polished.how_shows_up,
        field_tone,
        clarity_level, 
        max_sentences=1
    )
    
    polished.best_move = compress_best_move(polished.best_move, field_tone, clarity_level)
    
    # === REMOVE EXPLANATORY HD LANGUAGE ===
    polished.what_happening = remove_explanatory_language(polished.what_happening)
    polished.why_happening = remove_explanatory_language(polished.why_happening)
    polished.how_shows_up = remove_explanatory_language(polished.how_shows_up)
    
    # === STRICT FIELD FILTER ===
    if clarity_level == "low":
        polished = apply_strict_field_filter(polished)
    
    # === REMOVE GENERIC SAFE LANGUAGE ===
    polished = remove_generic_language(polished)
    
    return polished


def generate_vivid_title(
    signal: TransitSignal,
    position: int,
    field_tone: str,
    clarity_level: str,
    used_themes: set
) -> str:
    """
    Generate emotionally sharp titles (4-6 words).
    Each title must feel DIFFERENT.
    """
    signal_type = signal.signal_type
    center = signal.center or ""
    
    # Title banks based on signal type and field context
    if field_tone == "reset" and clarity_level == "low":
        # RESET TITLES - things are forming, unclear
        title_banks = {
            SignalType.CHANNEL_COMPLETION: [
                "Something New Is Forming",
                "A Bridge Is Building",
                "Energy Is Connecting",
                "A Path Wants to Open",
            ],
            SignalType.CENTER_ACTIVATION: {
                "Solar Plexus": [
                    "Feelings Without Names Yet",
                    "Emotions Are Moving Through",
                    "Something Wants to Be Felt",
                ],
                "Ajna": [
                    "Your Mind Wants Answers",
                    "Thoughts Without Conclusions",
                    "The Need to Know",
                ],
                "Head": [
                    "Questions Without Answers",
                    "Inspiration Stirring",
                    "Mental Pressure Building",
                ],
                "Throat": [
                    "Words Not Ready Yet",
                    "Expression Is Forming",
                    "Something Wants Voice",
                ],
                "G": [
                    "Direction Isn't Clear Yet",
                    "Identity Is Shifting",
                    "The Path Is Hidden",
                ],
                "Heart": [
                    "Will Isn't Ready",
                    "Commitment Needs Time",
                    "Value Is Recalibrating",
                ],
                "Spleen": [
                    "Instincts Are Fuzzy",
                    "Trust What's Unclear",
                    "Fear Moves Through",
                ],
                "Sacral": [
                    "Energy Is Rebuilding",
                    "Response Isn't Clear Yet",
                    "Life Force Resetting",
                ],
                "Root": [
                    "Pressure Without Direction",
                    "Urgency Needs Waiting",
                    "Drive Without Target",
                ],
                "default": [
                    "Something Is Stirring Here",
                    "Energy Is Shifting",
                    "Change Without Shape Yet",
                ],
            },
            SignalType.AUTHORITY_AMPLIFICATION: [
                "Clarity Isn't Here Yet",
                "Wait Before Deciding",
                "Answers Are Still Coming",
                "Trust Takes Time Now",
            ],
            SignalType.OPEN_CENTER_PRESSURE: [
                "Watch What You Absorb",
                "Not All of This Is Yours",
                "Borrowed Energy Moving Through",
                "Notice What's Not Yours",
            ],
            SignalType.NATAL_REINFORCEMENT: [
                "Your Pattern Is Louder",
                "Familiar Energy Amplified",
                "You Feel More Yourself",
            ],
        }
    elif field_tone == "clarity":
        # CLARITY TITLES - things are visible
        title_banks = {
            SignalType.CHANNEL_COMPLETION: [
                "A New Capability Is Here",
                "Something Just Connected",
                "A Channel Has Opened",
            ],
            SignalType.CENTER_ACTIVATION: {
                "Solar Plexus": [
                    "Emotions Are Heightened",
                    "You Feel Everything More",
                    "Emotional Waves Peak",
                ],
                "Ajna": [
                    "Mental Clarity Sharpens",
                    "Thoughts Come Faster",
                    "Your Mind Is Active",
                ],
                "default": [
                    "This Part of You Lights Up",
                    "Extra Energy Here",
                    "Amplification Happening",
                ],
            },
            SignalType.AUTHORITY_AMPLIFICATION: [
                "Decision Clarity Arrives",
                "Your Knowing Is Sharp",
                "Trust What You Feel",
            ],
            SignalType.OPEN_CENTER_PRESSURE: [
                "Watch for Overdoing",
                "Boundaries Needed Here",
                "This Isn't All Yours",
            ],
            SignalType.NATAL_REINFORCEMENT: [
                "Your Pattern Amplifies",
                "More of What's Already You",
                "Familiar Becomes Louder",
            ],
        }
    else:
        # DEFAULT/TURNING POINT TITLES
        title_banks = {
            SignalType.CHANNEL_COMPLETION: [
                "Something Is Connecting",
                "A Bridge Forms Temporarily",
                "New Energy Available",
            ],
            SignalType.CENTER_ACTIVATION: {
                "Solar Plexus": [
                    "Emotional Intensity Rising",
                    "Feelings Run Deep Now",
                ],
                "default": [
                    "This Area Activates",
                    "Energy Shifts Here",
                ],
            },
            SignalType.AUTHORITY_AMPLIFICATION: [
                "Your Inner Compass Shifts",
                "Decision Energy Changes",
            ],
            SignalType.OPEN_CENTER_PRESSURE: [
                "Watch What's Coming In",
                "External Pressure Here",
            ],
            SignalType.NATAL_REINFORCEMENT: [
                "Your Design Speaks Louder",
                "Who You Are Intensifies",
            ],
        }
    
    # Get title bank for this signal type
    bank = title_banks.get(signal_type, title_banks.get(SignalType.NATAL_REINFORCEMENT, []))
    
    # Handle nested center-specific banks
    if isinstance(bank, dict):
        center_key = center if center in bank else "default"
        bank = bank.get(center_key, bank.get("default", []))
    
    # Find unused title
    for title in bank:
        if title.lower() not in used_themes:
            return title
    
    # Fallback: generate based on position
    position_titles = {
        0: "The Main Thing Happening",
        1: "Also Present Now",
        2: "Watch For This",
    }
    return position_titles.get(position, "Energy Is Shifting")


def compress_and_vivify(text: str, field_tone: str, clarity_level: str, max_sentences: int = 2) -> str:
    """
    Compress text to be vivid and short.
    Max sentences, remove filler.
    """
    if not text:
        return text
    
    # Split into sentences
    sentences = [s.strip() for s in text.replace('...', '.').split('.') if s.strip()]
    
    # Take only first N sentences
    sentences = sentences[:max_sentences]
    
    # Rejoin
    result = '. '.join(sentences)
    if result and not result.endswith('.'):
        result += '.'
    
    return result


def compress_best_move(text: str, field_tone: str, clarity_level: str) -> str:
    """
    Compress best_move to one clear action.
    Adapt based on field.
    """
    if not text:
        return "Notice what you feel."
    
    # If low clarity/reset, prepend "Wait."
    if field_tone == "reset" and clarity_level == "low":
        # Block action words
        action_words = ["decide", "commit", "act", "move forward", "take action", "make a decision"]
        for word in action_words:
            if word in text.lower():
                return "Wait. Let this settle before acting."
    
    # Compress to first sentence
    first_sentence = text.split('.')[0].strip()
    if first_sentence:
        return first_sentence + '.'
    return text


def remove_explanatory_language(text: str) -> str:
    """
    Remove explanatory HD language.
    NO: "Solar Plexus center—the seat of your inner authority"
    YES: "This shows up as..."
    """
    if not text:
        return text
    
    import re
    
    # Remove parenthetical explanations
    text = re.sub(r'—[^.]*—', '', text)
    text = re.sub(r'\([^)]*center[^)]*\)', '', text)
    text = re.sub(r'—the seat of[^.]*', '', text)
    
    # Remove HD jargon explanations
    explanatory_patterns = [
        r'which is normally open in your design[,.]?',
        r'which is normally undefined[,.]?',
        r'is designed to sample and amplify[^.]*[,.]?',
        r'Your .* center is designed to[^.]*[,.]?',
        r'This gate connects to[^.]*[,.]?',
        r'completing the Channel of[^.]*[,.]?',
        r'the seat of your inner authority[,.]?',
        r'the seat of your decision-making[,.]?',
        r'energy from the environment[^.]*[,.]?',
    ]
    
    for pattern in explanatory_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up double spaces and trailing commas
    text = re.sub(r'\s*,\s*\.', '.', text)
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r',\s*$', '', text)
    text = re.sub(r',\.$', '.', text)
    
    return text


def apply_strict_field_filter(signal: TransitSignal) -> TransitSignal:
    """
    STRICT: When clarity_level is low, block certain words entirely.
    """
    blocked_words = {
        "clarity": "something forming",
        "certainty": "a sense of something",
        "certain": "sensing",
        "decide": "notice",
        "decisive": "aware",
        "decision": "feeling",
        "clear": "forming",
        "obvious": "present",
    }
    
    for field in ['what_happening', 'how_shows_up', 'best_move', 'why_happening']:
        text = getattr(signal, field, '') or ''
        for blocked, replacement in blocked_words.items():
            text = text.replace(blocked, replacement)
            text = text.replace(blocked.capitalize(), replacement.capitalize())
        setattr(signal, field, text)
    
    return signal


def remove_generic_language(signal: TransitSignal) -> TransitSignal:
    """
    Remove generic safe language and fix common grammar/phrasing issues.
    Replace "may be" with more direct language.
    """
    replacements = [
        # Fix "You notice" / "You may notice" openings
        ("You notice your ", ""),
        ("You notice the ", "The "),
        ("You notice ", ""),
        ("You may notice ", ""),
        ("You feel ", ""),
        ("Your ", ""),  # Make it even more direct at the start
        # Generic hedging
        ("may be", "is"),
        ("might be", "is"),
        ("can be", "shows up as"),
        ("could be", "is"),
        ("You may feel", "The feeling is"),
        ("You might notice", "What rises is"),
        ("This may show", "This shows"),
        ("This might show", "This shows"),
        # Grammar fixes
        ("waves is", "rhythm is"),
        ("emotional waves is", "emotional rhythm is"),
        ("your emotional waves is", "your emotional rhythm is"),
        ("centeris", "center is"),
        ("center is is", "center is"),
        # Awkward phrasing fixes
        ("how you make correct feelings", "how you arrive at what feels right"),
        ("make correct decisions", "make decisions that are right for you"),
        ("correct feelings", "real clarity"),
        ("the seat of your inner authority", ""),
        ("the seat of your decision-making", ""),
        ("—the seat of", "—"),
        # More natural phrasing
        ("is more pronounced", "runs deeper"),
        ("can be more pronounced", "is heightened"),
        ("may be more pronounced", "is heightened"),
        ("is amplified", "is heightened"),
        ("things are still forming", "something is taking shape"),
        ("still forming", "taking shape"),
    ]
    
    for field in ['what_happening', 'how_shows_up', 'best_move']:
        text = getattr(signal, field, '') or ''
        for old, new in replacements:
            text = text.replace(old, new)
            # Also handle capitalized versions
            text = text.replace(old.capitalize(), new.capitalize() if new else new)
        # Ensure first letter is capitalized after all replacements
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        # Clean up double spaces
        text = ' '.join(text.split())
        setattr(signal, field, text)
    
    return signal


def ensure_distinct_titles(signals: List[TransitSignal], field_tone: str, clarity_level: str) -> List[TransitSignal]:
    """
    Ensure all 3 signals have distinct titles.
    If duplicates found, rewrite.
    """
    titles = [s.title.lower() for s in signals]
    
    # Check for duplicates
    if len(titles) != len(set(titles)):
        # Find duplicates and rewrite
        seen = set()
        for i, signal in enumerate(signals):
            if signal.title.lower() in seen:
                # Generate alternative title based on position
                alternatives = {
                    0: "The Primary Pattern Now",
                    1: "What Else Is Present",
                    2: "The Friction Point",
                }
                signal.title = alternatives.get(i, f"Signal {i+1}")
            seen.add(signal.title.lower())
    
    return signals


def remove_mechanical_language(text: str, center: Optional[str] = None) -> str:
    """Replace mechanical planetary language with experiential language."""
    replacements = [
        ("The Sun is amplifying", "What rises now is a heightening of"),
        ("The Sun is activating", "The feeling is increased activity in"),
        ("The Sun is temporarily activating", "This lands as increased energy in"),
        ("The Earth is activating", "The grounding pressure shows up in"),
        ("The Earth is creating pressure", "This can feel like weight or stability around"),
        ("The Moon is activating", "Your emotional awareness shifts around"),
        ("The Moon is creating", "There's a shifting quality to"),
        ("Transit is hitting", "Energy is moving through"),
        ("transit Gate", "this energy pattern"),
        ("Transit completes", "A connection forms in"),
        ("You notice the", "The"),
        ("You may notice the", "The"),
        ("You notice", "The feeling is"),
        ("You may notice", "This can feel like"),
    ]
    
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    
    # Add experiential opener if still starts with planet name
    if result.startswith(("The Sun", "The Moon", "The Earth")):
        result = "The pressure shows up as " + result[4:].strip()
    
    return result


def remove_clarity_words(text: str) -> str:
    """Remove words that imply clarity when field clarity is low."""
    replacements = [
        ("clarity", "a sense of something forming"),
        ("Clarity", "Something"),
        ("certain", "sensing"),
        ("decisive", "aware"),
        ("clear", "forming"),
        ("Clear", "Emerging"),
        ("heightened", "stirring"),
        ("Heightened", "Shifting"),
    ]
    
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    
    return result


def adapt_for_low_clarity(text: str) -> str:
    """Adapt text when clarity is low (reset, eclipse)."""
    # Add uncertainty framing
    if not text.startswith(("You may", "This might", "There's")):
        text = "You may notice " + text[0].lower() + text[1:]
    
    # Add "but unclear" qualifier for definitive statements
    if "will" in text.lower() and "may" not in text.lower():
        text = text.replace(" will ", " may ")
    
    return text


def adapt_for_emerging_clarity(text: str) -> str:
    """Adapt text when clarity is emerging."""
    # Less definitive but still forward
    if text.startswith("You will"):
        text = text.replace("You will", "You may begin to")
    return text


def adapt_for_slow_pace(text: str) -> str:
    """Adapt best_move text for slow pace."""
    pace_phrases = [
        ("Act on", "When ready, act on"),
        ("Move on", "Take your time and move on"),
        ("Decide", "Before deciding"),
        ("Commit", "Before committing"),
    ]
    
    result = text
    for old, new in pace_phrases:
        if result.startswith(old):
            result = new + result[len(old):]
            break
    
    return result


def adapt_for_fast_pace(text: str) -> str:
    """Adapt best_move text for fast pace."""
    # Fast pace means things are moving - stay present
    if "wait" in text.lower():
        # Don't contradict "wait" advice, but acknowledge the intensity
        text = text + " The pace is intense right now."
    return text


def categorize_signals(signals: List[TransitSignal]) -> Dict[str, TransitSignal]:
    """
    Categorize top 3 signals into Activation, Opportunity, Friction.
    """
    activation = signals[0]
    
    # Find best opportunity (center activation or reinforcement that isn't friction)
    opportunity = signals[1] if len(signals) > 1 else signals[0]
    
    # Find friction signal (open center pressure, or lowest strength)
    friction_candidates = [s for s in signals if s.signal_type == SignalType.OPEN_CENTER_PRESSURE]
    friction = friction_candidates[0] if friction_candidates else (signals[2] if len(signals) > 2 else signals[-1])
    
    # Don't override polished titles with generic "Watch For:" pattern
    # The polish layer already handles friction titles
    
    return {
        "activation": activation,
        "opportunity": opportunity,
        "friction": friction,
    }


def create_default_signal(user_type: str, index: int) -> TransitSignal:
    """Create a default signal when not enough real signals are computed."""
    defaults = [
        TransitSignal(
            signal_type=SignalType.NATAL_REINFORCEMENT,
            strength=0.5,
            transit_planet="Sun",
            transit_gate=1,
            title="Steady State",
            what_happening="No major activations are happening right now.",
            why_happening="The current transits aren't creating significant interactions with your design.",
            how_shows_up="You may feel relatively 'normal'—closer to your baseline energy.",
            best_move="Focus on your strategy and authority. Your design knows what it needs.",
            label="Reinforcing your design",
        ),
        TransitSignal(
            signal_type=SignalType.CENTER_ACTIVATION,
            strength=0.4,
            transit_planet="Moon",
            transit_gate=28,
            title="Subtle Openings",
            what_happening="Background energy is shifting in gentle ways.",
            why_happening="The Moon continues its cycle, touching different areas of experience.",
            how_shows_up="You may notice small shifts in mood or focus throughout the day.",
            best_move="Stay present. The small things often matter more than the big ones.",
            label="Temporary activation",
        ),
        TransitSignal(
            signal_type=SignalType.OPEN_CENTER_PRESSURE,
            strength=0.3,
            transit_planet="Earth",
            transit_gate=2,
            title="General Awareness",
            what_happening="Your open centers are doing their normal job of sampling energy.",
            why_happening="This is simply how your design works—always sensing, always learning.",
            how_shows_up="You may be more aware of others' energy than your own.",
            best_move="Come back to yourself. What do YOU actually feel?",
            label="Temporary activation",
        ),
    ]
    return defaults[min(index, len(defaults) - 1)]


def signal_to_dict(signal: TransitSignal) -> Dict[str, Any]:
    """Convert TransitSignal to dictionary for API response."""
    return {
        "signal_type": signal.signal_type.value,
        "strength": signal.strength,
        "transit_planet": signal.transit_planet,
        "transit_gate": signal.transit_gate,
        "user_gate": signal.user_gate,
        "center": signal.center,
        "channel_name": signal.channel_name,
        "title": signal.title,
        "what_happening": signal.what_happening,
        "why_happening": signal.why_happening,
        "how_shows_up": signal.how_shows_up,
        "best_move": signal.best_move,
        "label": signal.label,
    }
