"""
Reflector Lunar Cycle Engine - Task 49 & Task 50

Special support for Human Design Reflectors by tracking lunar cycle phases
and aligning Mirror reflections to the Moon instead of the Sun.

Task 50: Extended with Moon-to-Gate mapping for "Lunar Gates of Possibility"

Reflectors (~1% of users) are uniquely sensitive to lunar cycles.
Their strategy is "To Wait a Lunar Cycle" for major decisions.
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# LUNAR CYCLE CONSTANTS
# =============================================================================

# Average synodic month (new moon to new moon) in days
SYNODIC_MONTH = 29.53059

# Sidereal month (Moon's orbit relative to stars) - used for gate calculation
SIDEREAL_MONTH = 27.321661

# Moon's average daily motion in degrees
MOON_DAILY_MOTION = 360.0 / SIDEREAL_MONTH  # ~13.176°/day

# Moon phases with day ranges (0-29 scale)
MOON_PHASES = [
    {"name": "New Moon", "start": 0, "end": 1.85, "icon": "🌑", "energy": "beginning"},
    {"name": "Waxing Crescent", "start": 1.85, "end": 7.38, "icon": "🌒", "energy": "emerging"},
    {"name": "First Quarter", "start": 7.38, "end": 11.07, "icon": "🌓", "energy": "action"},
    {"name": "Waxing Gibbous", "start": 11.07, "end": 14.77, "icon": "🌔", "energy": "refining"},
    {"name": "Full Moon", "start": 14.77, "end": 16.61, "icon": "🌕", "energy": "illumination"},
    {"name": "Waning Gibbous", "start": 16.61, "end": 22.15, "icon": "🌖", "energy": "integrating"},
    {"name": "Last Quarter", "start": 22.15, "end": 25.84, "icon": "🌗", "energy": "releasing"},
    {"name": "Waning Crescent", "start": 25.84, "end": 29.53, "icon": "🌘", "energy": "surrendering"},
]

# Reflector reflection messages by lunar phase (Mirror language - observational)
LUNAR_REFLECTION_MESSAGES = {
    "New Moon": {
        "message": "A new lunar cycle may be beginning for you. This could be a time of quiet sensing and inner stillness.",
        "question": "What new possibility seems to be emerging from the darkness?",
        "guidance": "Reflectors often find this phase invites rest and receptivity."
    },
    "Waxing Crescent": {
        "message": "The Moon appears to be growing. You may notice subtle shifts in how you experience your environment.",
        "question": "What intention seems to be forming in you?",
        "guidance": "This phase may support gentle exploration of emerging impulses."
    },
    "First Quarter": {
        "message": "You may be entering a phase of clearer direction. Challenges could arise to test what's emerging.",
        "question": "Where do you feel called to take action, even small action?",
        "guidance": "Reflectors often find clarity comes through witnessing resistance."
    },
    "Waxing Gibbous": {
        "message": "You may be approaching a moment of emotional clarity in this lunar cycle.",
        "question": "What feels different now compared with earlier in the month?",
        "guidance": "This phase may reveal what needs refining before the Full Moon."
    },
    "Full Moon": {
        "message": "The Moon appears full. This could be a time of heightened sensitivity and illumination for you.",
        "question": "What has become clear to you over this lunar cycle?",
        "guidance": "Reflectors may experience this as a peak of awareness and insight."
    },
    "Waning Gibbous": {
        "message": "The energy may be shifting toward integration. What you've learned could be settling in.",
        "question": "What wisdom from this cycle seems ready to be shared or applied?",
        "guidance": "This phase often supports teaching or expressing what's been received."
    },
    "Last Quarter": {
        "message": "You may be in a phase of release. Old patterns or decisions could be ready to dissolve.",
        "question": "What no longer serves you that you might be ready to let go?",
        "guidance": "Reflectors often find this phase supports conscious releasing."
    },
    "Waning Crescent": {
        "message": "The lunar cycle appears to be completing. This could be a time for rest and renewal.",
        "question": "What needs to end before the new cycle can begin?",
        "guidance": "This phase may invite surrender and deep restoration."
    },
}


# =============================================================================
# LUNAR CYCLE CALCULATIONS
# =============================================================================

def calculate_moon_position(dt: Optional[datetime] = None) -> float:
    """
    Calculate the Moon's position in the lunar cycle.
    
    Uses a simplified algorithm based on a known new moon reference point.
    Returns lunar day (0-29.53).
    
    Reference: January 11, 2024 11:57 UTC was a New Moon
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Ensure timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Reference new moon: January 11, 2024 11:57 UTC
    reference_new_moon = datetime(2024, 1, 11, 11, 57, 0, tzinfo=timezone.utc)
    
    # Calculate days since reference
    delta = dt - reference_new_moon
    days_since_reference = delta.total_seconds() / 86400.0
    
    # Calculate position in current cycle (0 to SYNODIC_MONTH)
    lunar_day = days_since_reference % SYNODIC_MONTH
    
    return lunar_day


def get_moon_phase(lunar_day: float) -> Dict[str, Any]:
    """
    Determine the moon phase from the lunar day.
    
    Returns phase info including name, icon, and energy.
    """
    # Handle edge case at cycle boundary
    if lunar_day >= SYNODIC_MONTH - 0.01:
        lunar_day = 0
    
    for phase in MOON_PHASES:
        if phase["start"] <= lunar_day < phase["end"]:
            return {
                "name": phase["name"],
                "icon": phase["icon"],
                "energy": phase["energy"],
                "lunar_day": round(lunar_day, 2),
            }
    
    # Default to New Moon if something goes wrong
    return {
        "name": "New Moon",
        "icon": "🌑",
        "energy": "beginning",
        "lunar_day": round(lunar_day, 2),
    }


def calculate_lunar_cycle_info(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate complete lunar cycle information.
    
    Returns:
        - lunar_day: Current day in cycle (0-29)
        - moon_phase: Phase name
        - days_since_new_moon: Days since last new moon
        - days_until_new_moon: Days until next new moon
        - days_until_full_moon: Days until next full moon
        - phase_progress: Percentage through current phase
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    lunar_day = calculate_moon_position(dt)
    phase_info = get_moon_phase(lunar_day)
    
    # Calculate days until next new moon
    days_until_new_moon = SYNODIC_MONTH - lunar_day
    
    # Calculate days until/since full moon (around day 14.77)
    full_moon_day = 14.77
    if lunar_day < full_moon_day:
        days_until_full_moon = full_moon_day - lunar_day
        days_since_full_moon = None
    else:
        days_until_full_moon = SYNODIC_MONTH - lunar_day + full_moon_day
        days_since_full_moon = lunar_day - full_moon_day
    
    # Calculate phase progress
    phase_start = 0
    phase_end = SYNODIC_MONTH
    for phase in MOON_PHASES:
        if phase["name"] == phase_info["name"]:
            phase_start = phase["start"]
            phase_end = phase["end"]
            break
    
    phase_duration = phase_end - phase_start
    phase_progress = (lunar_day - phase_start) / phase_duration if phase_duration > 0 else 0
    
    return {
        "lunar_day": round(lunar_day, 2),
        "moon_phase": phase_info["name"],
        "moon_icon": phase_info["icon"],
        "phase_energy": phase_info["energy"],
        "days_since_new_moon": round(lunar_day, 1),
        "days_until_new_moon": round(days_until_new_moon, 1),
        "days_until_full_moon": round(days_until_full_moon, 1),
        "days_since_full_moon": round(days_since_full_moon, 1) if days_since_full_moon else None,
        "phase_progress": round(phase_progress, 2),
        "cycle_progress": round(lunar_day / SYNODIC_MONTH, 2),
    }


# =============================================================================
# MOON-TO-GATE MAPPING - TRUE SIDEREAL (Swiss Ephemeris)
# =============================================================================
# FIXED: Now uses canonical True Sidereal Swiss Ephemeris config
# instead of linear approximation. Aligned with:
# - SVP: 31.2836° (Fixed)
# - Mode: SIDM_USER
# - Epoch: J2000
# =============================================================================

def calculate_moon_longitude(dt: Optional[datetime] = None) -> float:
    """
    Calculate the Moon's TRUE SIDEREAL longitude using Swiss Ephemeris.
    
    FIXED: Previously used linear approximation which accumulated drift error.
    Now uses canonical sidereal_config.py for accurate calculations.
    
    Args:
        dt: Datetime for calculation (default: now UTC)
    
    Returns:
        Moon's sidereal longitude (0-360)
    """
    try:
        from calculations.sidereal_config import calculate_planet_by_name
        
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Use TRUE SIDEREAL calculation from canonical config
        moon_pos = calculate_planet_by_name("Moon", dt)
        
        logger.debug(f"[LunarCycle] Moon TRUE SIDEREAL: {moon_pos['longitude']:.2f}° ({moon_pos['sign']})")
        
        return moon_pos['longitude']
        
    except Exception as e:
        logger.error(f"[LunarCycle] Error in TRUE SIDEREAL calculation, falling back: {e}")
        # Emergency fallback - should not happen in production
        return _calculate_moon_longitude_fallback(dt)


def _calculate_moon_longitude_fallback(dt: Optional[datetime] = None) -> float:
    """
    DEPRECATED FALLBACK: Linear approximation for emergency use only.
    This should NOT be used in normal operation.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    logger.warning("[LunarCycle] Using DEPRECATED linear approximation fallback!")
    
    reference_time = datetime(2024, 1, 11, 11, 57, 0, tzinfo=timezone.utc)
    reference_longitude = 270.0
    delta = dt - reference_time
    days_since = delta.total_seconds() / 86400.0
    longitude_traveled = days_since * MOON_DAILY_MOTION
    current_longitude = (reference_longitude + longitude_traveled) % 360.0
    
    return current_longitude


def get_current_moon_gate(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get the Human Design gate activated by the current Moon position.
    
    Uses TRUE SIDEREAL Swiss Ephemeris calculation (via sidereal_config.py).
    Maps Moon's sidereal longitude to HD gate using the HD Rave Mandala.
    
    Returns gate number, line, sign, and gate information from the dictionary.
    """
    try:
        from calculations.human_design import longitude_to_gate
        from calculations.sidereal_config import calculate_planet_by_name, longitude_to_sign_degree
        from services.lunar_gates_dictionary import get_gate_data
        
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Use TRUE SIDEREAL calculation from canonical config
        moon_pos = calculate_planet_by_name("Moon", dt)
        moon_longitude = moon_pos['longitude']
        moon_sign = moon_pos['sign']
        moon_degree = moon_pos['degree']
        
        # Convert to HD gate
        gate_info = longitude_to_gate(moon_longitude)
        gate_number = gate_info.get('gate', 1)
        gate_line = gate_info.get('line', 1)
        
        # Get the gate interpretation data
        gate_data = get_gate_data(gate_number)
        
        logger.info(f"[LunarGate] Moon TRUE SIDEREAL at {moon_longitude:.2f}° ({moon_sign}) -> Gate {gate_number}.{gate_line}")
        
        return {
            "moon_longitude": round(moon_longitude, 4),
            "moon_sign": moon_sign,
            "moon_degree_in_sign": round(moon_degree, 2),
            "current_moon_gate": gate_number,
            "gate_line": gate_line,
            "gate_formatted": f"{gate_number}.{gate_line}",
            "gate_title": gate_data.get("title", f"Gate {gate_number}"),
            "gate_theme": gate_data.get("theme", ""),
            "center": gate_data.get("center", ""),
            "gate_reflection_message": gate_data.get("reflection", ""),
            "gate_reflective_question": gate_data.get("question", ""),
            "calculation_method": "swiss_ephemeris_true_sidereal",
        }
        
    except Exception as e:
        logger.error(f"[LunarGate] Error calculating moon gate: {e}")
        # Return fallback
        return {
            "moon_longitude": None,
            "current_moon_gate": None,
            "gate_line": None,
            "gate_formatted": None,
            "gate_title": None,
            "gate_theme": None,
            "center": None,
            "gate_reflection_message": None,
            "gate_reflective_question": None,
        }


# =============================================================================
# REFLECTOR DETECTION
# =============================================================================

async def is_user_reflector(db, user_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if a user is a Human Design Reflector.
    
    Returns (is_reflector, human_design_data)
    """
    from bson import ObjectId
    
    try:
        # First check cached chart data
        chart = await db.charts.find_one({"user_id": user_id})
        
        if chart:
            hd_data = chart.get("human_design", {})
            hd_type = hd_data.get("type")
            
            if hd_type == "Reflector":
                logger.info(f"[LunarCycle] User {user_id[:8]}... is a Reflector (from cached chart)")
                return True, hd_data
            elif hd_type:
                # Has HD type but not Reflector
                return False, hd_data
        
        # If no cached chart, check user record
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, None
        
        # Check if birth data is available to compute HD
        birth_data = user.get("birth_date") or user.get("birthDate")
        if not birth_data:
            return False, None
        
        # Could compute HD here, but for efficiency we rely on cached data
        return False, None
        
    except Exception as e:
        logger.error(f"[LunarCycle] Error checking reflector status: {e}")
        return False, None


# =============================================================================
# LUNAR REFLECTION SIGNAL GENERATION
# =============================================================================

def generate_lunar_reflection_signal(
    lunar_info: Dict[str, Any],
    user_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a lunar reflection signal for a Reflector.
    
    Uses Mirror language principles - observational, non-deterministic.
    """
    phase_name = lunar_info.get("moon_phase", "New Moon")
    phase_data = LUNAR_REFLECTION_MESSAGES.get(phase_name, LUNAR_REFLECTION_MESSAGES["New Moon"])
    
    return {
        "signal_title": "Lunar Reflection Signal",
        "moon_phase": phase_name,
        "moon_icon": lunar_info.get("moon_icon", "🌙"),
        "phase_energy": lunar_info.get("phase_energy", ""),
        "lunar_day": lunar_info.get("lunar_day", 0),
        "reflection_message": phase_data["message"],
        "reflective_question": phase_data["question"],
        "guidance": phase_data["guidance"],
        "days_until_new_moon": lunar_info.get("days_until_new_moon", 0),
        "days_until_full_moon": lunar_info.get("days_until_full_moon", 0),
        "cycle_progress": lunar_info.get("cycle_progress", 0),
    }


# =============================================================================
# MAIN API FUNCTION
# =============================================================================

async def get_lunar_cycle_for_user(db, user_id: str) -> Dict[str, Any]:
    """
    Get lunar cycle information for a user.
    
    If user is a Reflector, returns full lunar reflection signal including:
    - Task 49: Lunar phase data
    - Task 50: Current Moon gate with reflection prompts
    
    Otherwise returns basic lunar info with is_reflector=False.
    """
    logger.info(f"[LunarCycle] Getting lunar cycle for user {user_id[:8]}...")
    
    # Check if user is a Reflector
    is_reflector, hd_data = await is_user_reflector(db, user_id)
    
    # Calculate lunar cycle info
    lunar_info = calculate_lunar_cycle_info()
    
    if is_reflector:
        # Generate phase-based reflection signal
        signal = generate_lunar_reflection_signal(lunar_info)
        
        # Task 50: Get current Moon gate data
        gate_data = get_current_moon_gate()
        
        # Build result with both phase and gate info
        result = {
            "is_reflector": True,
            "human_design_type": "Reflector",
            "strategy": "To Wait a Lunar Cycle",
            **lunar_info,
            # Task 50: Gate data for "Lunar Gate of Possibility"
            **gate_data,
            # Phase-based signal (fallback if gate unavailable)
            "phase_reflection_message": signal.get("reflection_message"),
            "phase_reflective_question": signal.get("reflective_question"),
            "phase_guidance": signal.get("guidance"),
            # Use gate-based reflection if available, otherwise phase-based
            "reflection_message": gate_data.get("gate_reflection_message") or signal.get("reflection_message"),
            "reflective_question": gate_data.get("gate_reflective_question") or signal.get("reflective_question"),
            "guidance": signal.get("guidance"),
            # Card titles
            "signal_title": "Lunar Gate of Possibility",
            "pattern_lens_message": "Reflectors often experience clarity by observing how decisions feel across an entire lunar cycle. The Moon activates different gates as it moves, offering changing perspectives.",
            "reflector_note": "For Reflectors, the Moon offers a changing perspective across the cycle.",
        }
        
        logger.info(f"[LunarCycle] Reflector user: phase={lunar_info['moon_phase']}, day={lunar_info['lunar_day']}, gate={gate_data.get('current_moon_gate')}")
        return result
    
    else:
        # Return basic lunar info for non-Reflectors
        result = {
            "is_reflector": False,
            "human_design_type": hd_data.get("type") if hd_data else None,
            **lunar_info,
            "current_moon_gate": None,
            "gate_theme": None,
            "center": None,
            "reflection_message": None,
            "reflective_question": None,
            "guidance": None,
        }
        
        logger.info(f"[LunarCycle] Non-Reflector user: phase={lunar_info['moon_phase']}")
        return result
