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
                title=f"Channel Activation: {channel_data.get('name', 'Connection')}",
                what_happening=f"The {transit.get('planet')} is activating a gate that connects to your natal design, creating a temporary channel.",
                why_happening=f"Your Gate {partner_gate} is meeting transit Gate {transit_gate}, completing the Channel of {channel_data.get('name', 'Connection')}.",
                how_shows_up="You may feel a surge of new energy or capability that isn't usually available to you. This can feel exciting but also unfamiliar.",
                best_move="Experiment with this energy while it's here. Notice what becomes possible that wasn't before.",
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
                title=f"Amplified {transit_center} Energy",
                what_happening=f"The {planet} is temporarily activating your {transit_center} center, which is normally open in your design.",
                why_happening=f"Your {transit_center} center is designed to sample and amplify energy from the environment. Right now, the {planet} is providing that energy directly.",
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
                title=f"Decision Clarity Heightened",
                what_happening=f"The {planet} is amplifying your {user_authority}, which is how you make correct decisions.",
                why_happening=f"Your {transit_center} center—the seat of your inner authority—is receiving extra energy from the current transit.",
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
                what_happening=f"The {planet} is creating pressure on your open {transit_center} center.",
                why_happening=f"Because your {transit_center} is undefined, you naturally amplify and absorb energy there. Right now, the transit is intensifying this.",
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
                what_happening=f"The {planet} is reinforcing energy you already carry in your design.",
                why_happening=f"Gate {transit_gate} is part of who you are. The {planet} passing through it turns up the volume on this energy.",
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
    """Get behavior description for center activation."""
    behaviors = {
        "Head": "You may notice more mental pressure, inspiration, or questions flooding in. Ideas want your attention.",
        "Ajna": "Your thinking may feel more certain or fixed. Watch for getting attached to being 'right'.",
        "Throat": "You may feel more desire to speak, express, or manifest. Words want to come out.",
        "G": "Your sense of direction or identity may feel stronger—or you may question where you're going.",
        "Heart": "You may feel more willpower, ambition, or need to prove yourself. Watch for overcommitting.",
        "Solar Plexus": "Your emotional sensitivity is heightened. Feelings may be more intense than usual.",
        "Sacral": "You may notice more sustainable energy available—or pressure to 'do' more.",
        "Spleen": "Your instincts and intuition may be sharper. Body awareness is amplified.",
        "Root": "You may feel more pressure to act, start things, or feel stress about time.",
    }
    return behaviors.get(center, "You may notice this area of your life feeling more active than usual.")


def get_center_activation_move(center: str) -> str:
    """Get best move for center activation."""
    moves = {
        "Head": "Let the inspiration flow without needing to act on everything. Not every idea is yours to pursue.",
        "Ajna": "Notice your thoughts without gripping them too tightly. Your natural flexibility is a gift.",
        "Throat": "Speak when truly invited. This extra expression energy doesn't mean everything needs to be said.",
        "G": "Follow what feels right without needing to know the whole path. Direction reveals itself.",
        "Heart": "Notice where you're trying to prove yourself. You don't need to push—your value isn't in question.",
        "Solar Plexus": "Let emotions move through without making permanent decisions from temporary feelings.",
        "Sacral": "Use the extra energy for what genuinely excites you. Don't just fill time because you 'can'.",
        "Spleen": "Trust the instant knowing, but don't let fear-based instincts run the show.",
        "Root": "Notice what's truly urgent versus manufactured pressure. Most things can wait.",
    }
    return moves.get(center, "Be aware this energy is temporary. Observe without over-identifying.")


def get_authority_amplification_behavior(authority: str) -> str:
    """Get behavior for authority amplification."""
    auth_lower = authority.lower()
    if "emotional" in auth_lower:
        return "Your emotional waves may be more pronounced. Clarity will come—but it needs time to settle."
    if "sacral" in auth_lower:
        return "Your gut responses may be clearer and more reliable. Notice the pull toward or away from things."
    if "splenic" in auth_lower:
        return "Your instinctual knowing may be sharper. Pay attention to what your body signals in the moment."
    if "ego" in auth_lower:
        return "Your willpower and sense of what you truly want may be clearer. Trust your heart's direction."
    if "self" in auth_lower or "projected" in auth_lower:
        return "Your sense of self and direction may feel more accessible. Notice what you hear yourself saying."
    return "Your natural way of making decisions is heightened. Trust your process more than usual."


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
    """Get behavior for open center pressure."""
    behaviors = {
        "Head": "You may feel overwhelmed by questions or inspiration that isn't yours to solve.",
        "Ajna": "You may feel pressure to have answers or appear certain about things.",
        "Throat": "You may feel pressure to speak before you're ready or attract attention.",
        "G": "You may feel lost or unclear about direction, or too attached to a fixed identity.",
        "Heart": "You may feel pressure to prove your worth or compete unnecessarily.",
        "Solar Plexus": "You may absorb emotions from others and mistake them for your own.",
        "Sacral": "You may push past your natural limits or feel guilty for resting.",
        "Spleen": "You may ignore your instincts or hold onto things past their time.",
        "Root": "You may feel unnecessary urgency or rush decisions that can wait.",
    }
    return behaviors.get(center, "You may feel pressure or amplification in this area that isn't truly yours.")


def get_open_center_pressure_move(center: str) -> str:
    """Get best move for open center pressure."""
    moves = {
        "Head": "Let questions exist without needing to answer them all. Not every inspiration is your responsibility.",
        "Ajna": "It's okay not to know. Your openness here is wisdom, not weakness.",
        "Throat": "Wait for invitation before speaking. Silence is also communication.",
        "G": "Trust that your direction will become clear. You don't need to force identity.",
        "Heart": "You have nothing to prove. Your value exists whether you push or not.",
        "Solar Plexus": "Check whose feelings you're carrying. Return what isn't yours.",
        "Sacral": "Rest is correct for you. Don't match others' energy output.",
        "Spleen": "Notice what your body says, but don't let passing fears drive decisions.",
        "Root": "Slow down. The urgency you feel may not reflect actual deadlines.",
    }
    return moves.get(center, "Remember this energy is amplified, not yours. Observe without over-reacting.")


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
    
    # Assign roles: Biggest Activation, Opportunity, Friction
    categorized = categorize_signals(adapted_signals)
    
    logger.info(f"[TransitSignals] Computed {len(all_signals)} signals, returning top 3 (field_tone={field_context.get('field_tone')})")
    
    return {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "transits": transits,
        "signals": {
            "activation": signal_to_dict(categorized["activation"]),
            "opportunity": signal_to_dict(categorized["opportunity"]),
            "friction": signal_to_dict(categorized["friction"]),
        },
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


def remove_mechanical_language(text: str, center: Optional[str] = None) -> str:
    """Replace mechanical planetary language with experiential language."""
    replacements = [
        ("The Sun is amplifying", "You're feeling a heightening of"),
        ("The Sun is activating", "You may notice more activity in"),
        ("The Sun is temporarily activating", "You're sensing increased energy in"),
        ("The Earth is activating", "There's grounding pressure on"),
        ("The Earth is creating pressure", "You may feel weight or stability around"),
        ("The Moon is activating", "Your emotional awareness of"),
        ("The Moon is creating", "There's a shifting quality to"),
        ("Transit is hitting", "Energy is moving through"),
        ("transit Gate", "this energy pattern"),
        ("Transit completes", "A connection forms in"),
    ]
    
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    
    # Add experiential opener if still starts with planet name
    if result.startswith(("The Sun", "The Moon", "The Earth")):
        result = "You may notice " + result[0].lower() + result[1:]
    
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
    
    # Ensure friction signal is properly labeled
    if friction.signal_type != SignalType.OPEN_CENTER_PRESSURE:
        # Convert to friction framing
        friction.title = f"Watch For: {friction.center or 'Energy'} Distortion"
        friction.label = "Temporary activation"
    
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
