"""
Field Signal Engine - Astrological Context Layer

Detects MACRO sky events that influence the collective field:
- New Moon / Full Moon
- Approaching Equinox / Solstice
- Major planet sign changes (Saturn, Jupiter)
- Eclipses
- Strong lunar phases

Returns 1-2 MAX dominant signals with experiential language.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)


# =============================================================================
# FIELD SIGNAL TYPES
# =============================================================================

class FieldSignalType(str, Enum):
    NEW_MOON = "new_moon"
    FULL_MOON = "full_moon"
    ECLIPSE_SOLAR = "eclipse_solar"
    ECLIPSE_LUNAR = "eclipse_lunar"
    EQUINOX = "equinox"
    SOLSTICE = "solstice"
    SATURN_SIGN_CHANGE = "saturn_sign_change"
    JUPITER_SIGN_CHANGE = "jupiter_sign_change"
    WANING_CRESCENT = "waning_crescent"
    WAXING_CRESCENT = "waxing_crescent"
    FIRST_QUARTER = "first_quarter"
    LAST_QUARTER = "last_quarter"


@dataclass
class FieldSignal:
    """A macro astrological field signal."""
    signal_type: FieldSignalType
    strength: float  # 0-1, how dominant
    headline: str
    what_happening: str
    why_happening: str
    how_interacts_with_hd: str
    hd_connection_hint: str  # Used to modify HD signals
    days_until: int  # Days until/since event
    is_approaching: bool  # True if upcoming, False if just passed


# =============================================================================
# ASTRONOMICAL CALCULATIONS
# =============================================================================

def calculate_moon_phase(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate current moon phase with high precision.
    Returns phase name, illumination, and days into cycle.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Known new moon: January 11, 2024 11:57 UTC
    reference_new_moon = datetime(2024, 1, 11, 11, 57, 0, tzinfo=timezone.utc)
    
    # Synodic month (new moon to new moon) = 29.53059 days
    synodic_month = 29.53059
    
    # Calculate days since reference new moon
    delta = dt - reference_new_moon
    days_since = delta.total_seconds() / 86400.0
    
    # Days into current lunar cycle
    cycle_days = days_since % synodic_month
    
    # Phase calculation (0 = new, 0.5 = full)
    phase_fraction = cycle_days / synodic_month
    illumination = (1 - math.cos(2 * math.pi * phase_fraction)) / 2
    
    # Days until next new moon
    days_to_new = synodic_month - cycle_days
    
    # Days until next full moon
    if cycle_days < synodic_month / 2:
        days_to_full = (synodic_month / 2) - cycle_days
    else:
        days_to_full = synodic_month - cycle_days + (synodic_month / 2)
    
    # Determine phase name
    if cycle_days < 1.85:
        phase_name = "New Moon"
        is_new_moon = True
        is_full_moon = False
    elif cycle_days < 7.38:
        phase_name = "Waxing Crescent"
        is_new_moon = False
        is_full_moon = False
    elif cycle_days < 9.23:
        phase_name = "First Quarter"
        is_new_moon = False
        is_full_moon = False
    elif cycle_days < 14.77:
        phase_name = "Waxing Gibbous"
        is_new_moon = False
        is_full_moon = False
    elif cycle_days < 16.61:
        phase_name = "Full Moon"
        is_new_moon = False
        is_full_moon = True
    elif cycle_days < 22.15:
        phase_name = "Waning Gibbous"
        is_new_moon = False
        is_full_moon = False
    elif cycle_days < 23.99:
        phase_name = "Last Quarter"
        is_new_moon = False
        is_full_moon = False
    else:
        phase_name = "Waning Crescent"
        is_new_moon = False
        is_full_moon = False
    
    return {
        "phase_name": phase_name,
        "cycle_days": round(cycle_days, 2),
        "illumination": round(illumination * 100, 1),
        "days_to_new": round(days_to_new, 1),
        "days_to_full": round(days_to_full, 1),
        "is_new_moon": is_new_moon,
        "is_full_moon": is_full_moon,
        "phase_fraction": round(phase_fraction, 3),
    }


def calculate_season(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate proximity to equinoxes and solstices.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    year = dt.year
    
    # Approximate dates for 2024-2026 (UTC)
    # These shift slightly each year
    events = {
        "spring_equinox": datetime(year, 3, 20, 3, 0, tzinfo=timezone.utc),
        "summer_solstice": datetime(year, 6, 21, 4, 0, tzinfo=timezone.utc),
        "fall_equinox": datetime(year, 9, 22, 13, 0, tzinfo=timezone.utc),
        "winter_solstice": datetime(year, 12, 21, 10, 0, tzinfo=timezone.utc),
    }
    
    # Also check next year's spring equinox for winter dates
    events["next_spring_equinox"] = datetime(year + 1, 3, 20, 3, 0, tzinfo=timezone.utc)
    
    closest_event = None
    closest_days = float('inf')
    is_approaching = True
    
    for event_name, event_date in events.items():
        if event_name.startswith("next_"):
            continue
        
        delta = (event_date - dt).total_seconds() / 86400.0
        
        if abs(delta) < abs(closest_days):
            closest_days = delta
            closest_event = event_name
            is_approaching = delta > 0
    
    # Check if winter solstice just passed and next spring is closer
    if closest_event == "winter_solstice" and closest_days < -30:
        spring_delta = (events["next_spring_equinox"] - dt).total_seconds() / 86400.0
        if abs(spring_delta) < abs(closest_days):
            closest_days = spring_delta
            closest_event = "spring_equinox"
            is_approaching = True
    
    return {
        "closest_event": closest_event,
        "days_until": round(closest_days, 1),
        "is_approaching": is_approaching,
        "is_equinox": "equinox" in (closest_event or ""),
        "is_solstice": "solstice" in (closest_event or ""),
    }


def check_eclipse_season(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Check if we're in or near an eclipse season.
    Eclipse seasons occur approximately every 6 months.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Known eclipse dates for 2024-2026
    eclipses = [
        {"date": datetime(2024, 3, 25, tzinfo=timezone.utc), "type": "lunar", "name": "Penumbral Lunar"},
        {"date": datetime(2024, 4, 8, tzinfo=timezone.utc), "type": "solar", "name": "Total Solar"},
        {"date": datetime(2024, 9, 18, tzinfo=timezone.utc), "type": "lunar", "name": "Partial Lunar"},
        {"date": datetime(2024, 10, 2, tzinfo=timezone.utc), "type": "solar", "name": "Annular Solar"},
        {"date": datetime(2025, 3, 14, tzinfo=timezone.utc), "type": "lunar", "name": "Total Lunar"},
        {"date": datetime(2025, 3, 29, tzinfo=timezone.utc), "type": "solar", "name": "Partial Solar"},
        {"date": datetime(2025, 9, 7, tzinfo=timezone.utc), "type": "lunar", "name": "Total Lunar"},
        {"date": datetime(2025, 9, 21, tzinfo=timezone.utc), "type": "solar", "name": "Partial Solar"},
        {"date": datetime(2026, 2, 17, tzinfo=timezone.utc), "type": "solar", "name": "Annular Solar"},
        {"date": datetime(2026, 3, 3, tzinfo=timezone.utc), "type": "lunar", "name": "Total Lunar"},
        {"date": datetime(2026, 8, 12, tzinfo=timezone.utc), "type": "solar", "name": "Total Solar"},
        {"date": datetime(2026, 8, 28, tzinfo=timezone.utc), "type": "lunar", "name": "Partial Lunar"},
    ]
    
    closest_eclipse = None
    closest_days = float('inf')
    
    for eclipse in eclipses:
        delta = (eclipse["date"] - dt).total_seconds() / 86400.0
        if -14 <= delta <= 30:  # Within 2 weeks before or 1 month after
            if abs(delta) < abs(closest_days):
                closest_days = delta
                closest_eclipse = eclipse
    
    if closest_eclipse:
        return {
            "in_eclipse_season": True,
            "eclipse_type": closest_eclipse["type"],
            "eclipse_name": closest_eclipse["name"],
            "days_until": round(closest_days, 1),
            "is_approaching": closest_days > 0,
        }
    
    return {
        "in_eclipse_season": False,
        "eclipse_type": None,
        "eclipse_name": None,
        "days_until": None,
        "is_approaching": False,
    }


# =============================================================================
# FIELD SIGNAL GENERATION
# =============================================================================

def generate_new_moon_signal(moon_data: Dict, hd_type: str, hd_authority: str) -> Optional[FieldSignal]:
    """Generate signal for new moon energy."""
    days_to_new = moon_data["days_to_new"]
    cycle_days = moon_data["cycle_days"]
    
    # Check if new moon is approaching (within 3 days) or just happened (within 2 days)
    if days_to_new <= 3:
        # Approaching new moon
        return FieldSignal(
            signal_type=FieldSignalType.NEW_MOON,
            strength=0.95 - (days_to_new * 0.1),
            headline="A Reset Is Beginning",
            what_happening="Something is clearing. You may feel things dissolving, simplifying, or returning to zero.",
            why_happening="The lunar cycle is completing. A new beginning is forming in the dark.",
            how_interacts_with_hd=get_new_moon_hd_interaction(hd_type, hd_authority),
            hd_connection_hint="amplifies the need for pause and inner sensing",
            days_until=round(days_to_new),
            is_approaching=True,
        )
    elif cycle_days <= 2:
        # New moon just happened
        return FieldSignal(
            signal_type=FieldSignalType.NEW_MOON,
            strength=0.90 - (cycle_days * 0.1),
            headline="Fresh Seeds Are Planted",
            what_happening="A new cycle has just begun. Intentions set now carry extra weight.",
            why_happening="The new moon is seeding what will unfold over the coming weeks.",
            how_interacts_with_hd=get_new_moon_hd_interaction(hd_type, hd_authority),
            hd_connection_hint="supports new beginnings aligned with your strategy",
            days_until=0,
            is_approaching=False,
        )
    
    return None


def generate_full_moon_signal(moon_data: Dict, hd_type: str, hd_authority: str) -> Optional[FieldSignal]:
    """Generate signal for full moon energy."""
    days_to_full = moon_data["days_to_full"]
    phase_name = moon_data["phase_name"]
    
    # Check if full moon is approaching (within 3 days) or just happened
    if days_to_full <= 3 and phase_name != "Full Moon":
        return FieldSignal(
            signal_type=FieldSignalType.FULL_MOON,
            strength=0.92 - (days_to_full * 0.1),
            headline="Something Is Coming to a Head",
            what_happening="Tension is building. What's been developing is reaching a peak or revelation.",
            why_happening="The full moon illuminates what was hidden. Clarity—or confrontation—is near.",
            how_interacts_with_hd=get_full_moon_hd_interaction(hd_type, hd_authority),
            hd_connection_hint="intensifies emotional processing and decision-making",
            days_until=round(days_to_full),
            is_approaching=True,
        )
    elif phase_name == "Full Moon":
        return FieldSignal(
            signal_type=FieldSignalType.FULL_MOON,
            strength=0.93,
            headline="Everything Is Illuminated",
            what_happening="What's been building is now fully visible. This is a moment of clarity or completion.",
            why_happening="The full moon reveals. Emotions and situations reach their peak expression.",
            how_interacts_with_hd=get_full_moon_hd_interaction(hd_type, hd_authority),
            hd_connection_hint="magnifies awareness and emotional intensity",
            days_until=0,
            is_approaching=False,
        )
    
    return None


def generate_waning_crescent_signal(moon_data: Dict, hd_type: str, hd_authority: str) -> Optional[FieldSignal]:
    """Generate signal for waning crescent (balsamic) phase."""
    if moon_data["phase_name"] == "Waning Crescent":
        return FieldSignal(
            signal_type=FieldSignalType.WANING_CRESCENT,
            strength=0.75,
            headline="Time to Let Go",
            what_happening="The old cycle is completing. Release what no longer serves.",
            why_happening="The moon is surrendering to the dark. This is nature's exhale before the next breath.",
            how_interacts_with_hd=get_waning_hd_interaction(hd_type, hd_authority),
            hd_connection_hint="supports releasing and rest before new response",
            days_until=round(moon_data["days_to_new"]),
            is_approaching=True,
        )
    return None


def generate_equinox_signal(season_data: Dict, hd_type: str, hd_authority: str) -> Optional[FieldSignal]:
    """Generate signal for approaching equinox."""
    if not season_data["is_equinox"]:
        return None
    
    days = abs(season_data["days_until"])
    is_approaching = season_data["is_approaching"]
    
    if days > 14:
        return None
    
    is_spring = "spring" in season_data["closest_event"]
    
    if is_approaching:
        return FieldSignal(
            signal_type=FieldSignalType.EQUINOX,
            strength=0.85 - (days * 0.03),
            headline="A Turning Point Is Near" if is_spring else "Balance Is Shifting",
            what_happening="Day and night are equalizing. A threshold is being crossed." if is_spring 
                else "Light and dark are rebalancing. Something is pivoting.",
            why_happening=f"The {'spring' if is_spring else 'fall'} equinox marks a shift between seasons and energies.",
            how_interacts_with_hd=get_equinox_hd_interaction(hd_type, hd_authority, is_spring),
            hd_connection_hint="supports recalibration and fresh direction",
            days_until=round(days),
            is_approaching=True,
        )
    else:
        return FieldSignal(
            signal_type=FieldSignalType.EQUINOX,
            strength=0.80 - (days * 0.04),
            headline="The Pivot Has Happened",
            what_happening="A threshold has just been crossed. New rhythms are establishing.",
            why_happening=f"The {'spring' if is_spring else 'fall'} equinox just passed. The field is recalibrating.",
            how_interacts_with_hd=get_equinox_hd_interaction(hd_type, hd_authority, is_spring),
            hd_connection_hint="amplifies sensitivity to new directions",
            days_until=round(-days),
            is_approaching=False,
        )


def generate_solstice_signal(season_data: Dict, hd_type: str, hd_authority: str) -> Optional[FieldSignal]:
    """Generate signal for approaching solstice."""
    if not season_data["is_solstice"]:
        return None
    
    days = abs(season_data["days_until"])
    is_approaching = season_data["is_approaching"]
    
    if days > 14:
        return None
    
    is_summer = "summer" in season_data["closest_event"]
    
    if is_approaching:
        return FieldSignal(
            signal_type=FieldSignalType.SOLSTICE,
            strength=0.88 - (days * 0.03),
            headline="Peak Energy Approaching" if is_summer else "The Depths Are Calling",
            what_happening="Light is reaching its maximum." if is_summer 
                else "Darkness is at its peak. This is a time of deep inner work.",
            why_happening=f"The {'summer' if is_summer else 'winter'} solstice marks the {'longest' if is_summer else 'shortest'} day.",
            how_interacts_with_hd=get_solstice_hd_interaction(hd_type, hd_authority, is_summer),
            hd_connection_hint="intensifies inner reflection and recalibration",
            days_until=round(days),
            is_approaching=True,
        )
    else:
        return FieldSignal(
            signal_type=FieldSignalType.SOLSTICE,
            strength=0.82 - (days * 0.04),
            headline="The Turn Has Begun",
            what_happening="The extremity has passed. Light is now {'waning' if is_summer else 'returning'}.",
            why_happening=f"The {'summer' if is_summer else 'winter'} solstice marks a turning point in the year.",
            how_interacts_with_hd=get_solstice_hd_interaction(hd_type, hd_authority, is_summer),
            hd_connection_hint="supports integration and gradual shift",
            days_until=round(-days),
            is_approaching=False,
        )


def generate_eclipse_signal(eclipse_data: Dict, hd_type: str, hd_authority: str) -> Optional[FieldSignal]:
    """Generate signal for eclipse season."""
    if not eclipse_data["in_eclipse_season"]:
        return None
    
    days = eclipse_data["days_until"]
    is_approaching = eclipse_data["is_approaching"]
    is_solar = eclipse_data["eclipse_type"] == "solar"
    
    if is_approaching and days <= 14:
        return FieldSignal(
            signal_type=FieldSignalType.ECLIPSE_SOLAR if is_solar else FieldSignalType.ECLIPSE_LUNAR,
            strength=0.95 - (abs(days) * 0.02),
            headline="A Portal Is Opening" if is_solar else "Deep Feelings Are Surfacing",
            what_happening="Major shifts are possible. What changes now may have lasting impact." if is_solar
                else "Emotional material is rising to be seen and released.",
            why_happening=f"A {eclipse_data['eclipse_name'].lower()} is approaching, intensifying the field.",
            how_interacts_with_hd=get_eclipse_hd_interaction(hd_type, hd_authority, is_solar),
            hd_connection_hint="magnifies the importance of correct decision-making",
            days_until=round(days),
            is_approaching=True,
        )
    elif not is_approaching and abs(days) <= 7:
        return FieldSignal(
            signal_type=FieldSignalType.ECLIPSE_SOLAR if is_solar else FieldSignalType.ECLIPSE_LUNAR,
            strength=0.88 - (abs(days) * 0.03),
            headline="Integration Time" if is_solar else "Processing the Depths",
            what_happening="A significant shift just occurred. Give yourself time to integrate.",
            why_happening=f"The recent {eclipse_data['eclipse_name'].lower()} is still reverberating.",
            how_interacts_with_hd=get_eclipse_hd_interaction(hd_type, hd_authority, is_solar),
            hd_connection_hint="supports rest and avoiding major decisions",
            days_until=round(days),
            is_approaching=False,
        )
    
    return None


# =============================================================================
# HD INTERACTION TEXT GENERATORS
# =============================================================================

def get_new_moon_hd_interaction(hd_type: str, hd_authority: str) -> str:
    """How new moon interacts with HD type."""
    interactions = {
        "Generator": "This reset energy supports letting go of commitments that no longer light you up. Your sacral is ready to respond to new possibilities.",
        "Manifesting Generator": "New beginnings are calling—but wait for genuine response before jumping in. Your efficiency serves you after clarity, not before.",
        "Projector": "This is a powerful time to release old invitations that weren't right. Fresh recognition is seeding.",
        "Manifestor": "The reset supports new impulses. Notice what wants to be initiated as the cycle begins.",
        "Reflector": "A new lunar cycle begins your sampling anew. What felt true last month may shift. Stay open.",
    }
    
    base = interactions.get(hd_type, interactions["Generator"])
    
    if "emotional" in hd_authority.lower():
        base += " Your emotional clarity may feel especially still—trust the quiet."
    
    return base


def get_full_moon_hd_interaction(hd_type: str, hd_authority: str) -> str:
    """How full moon interacts with HD type."""
    interactions = {
        "Generator": "Your responses may feel more charged. Notice what your gut is clearly saying yes or no to.",
        "Manifesting Generator": "Energy is high—but watch for scattered action. Let the illumination show you what truly needs doing.",
        "Projector": "Your insights are sharp. Others may be more receptive—or reactive. Choose where you share wisely.",
        "Manifestor": "Your impact is amplified. Inform clearly, as your words and actions carry extra weight.",
        "Reflector": "You're feeling everything more intensely. What you're sensing may belong to others. Discern carefully.",
    }
    
    base = interactions.get(hd_type, interactions["Generator"])
    
    if "emotional" in hd_authority.lower():
        base += " Emotional waves may be stronger—avoid permanent decisions from peak feelings."
    
    return base


def get_waning_hd_interaction(hd_type: str, hd_authority: str) -> str:
    """How waning moon interacts with HD type."""
    interactions = {
        "Generator": "This is a time to rest and release, not initiate. Let commitments that drain you fall away.",
        "Manifesting Generator": "Slow down. Not everything needs to be finished or started right now.",
        "Projector": "Rest is especially important now. Recharge before the next cycle of invitations.",
        "Manifestor": "Let the old impulse complete before the new one arrives. Rest is productive now.",
        "Reflector": "The lunar cycle is completing. Notice what has become clear over this month.",
    }
    return interactions.get(hd_type, interactions["Generator"])


def get_equinox_hd_interaction(hd_type: str, hd_authority: str, is_spring: bool) -> str:
    """How equinox interacts with HD type."""
    if is_spring:
        interactions = {
            "Generator": "Fresh response energy is available. Notice what new things call for your yes.",
            "Manifesting Generator": "New paths are opening. Your ability to pivot serves you now.",
            "Projector": "New invitations may arrive. Be discerning—not everything is for you.",
            "Manifestor": "Initiating energy is supported. New impulses have extra traction.",
            "Reflector": "The environment is shifting. Take time to sample the new energies.",
        }
    else:
        interactions = {
            "Generator": "Time to release what no longer gets a true response. Prepare for a more inward season.",
            "Manifesting Generator": "Some threads can be dropped. Efficiency means knowing when to stop.",
            "Projector": "Fewer invitations may come—use this time to rest and refine your gifts.",
            "Manifestor": "Let some initiatives complete. Not everything needs to continue into the dark season.",
            "Reflector": "Begin to draw inward. Your sampling may become more internal.",
        }
    return interactions.get(hd_type, interactions["Generator"])


def get_solstice_hd_interaction(hd_type: str, hd_authority: str, is_summer: bool) -> str:
    """How solstice interacts with HD type."""
    if is_summer:
        return "Energy is at maximum. Pace yourself—this peak will turn toward rest."
    else:
        return "Deep inner work is supported. Trust your design even when external productivity is low."


def get_eclipse_hd_interaction(hd_type: str, hd_authority: str, is_solar: bool) -> str:
    """How eclipse interacts with HD type."""
    if is_solar:
        interactions = {
            "Generator": "Major life-direction shifts are possible. Wait for clear gut response before committing.",
            "Manifesting Generator": "Powerful changes may call you—but don't rush. Clarity takes time now.",
            "Projector": "Significant invitations may come. Be extra discerning—eclipse energy is destabilizing.",
            "Manifestor": "Your impulses carry extra weight. Inform carefully before initiating anything major.",
            "Reflector": "You may feel the collective shift intensely. Ground yourself before deciding.",
        }
    else:
        interactions = {
            "Generator": "Deep emotional material is surfacing. Let it move through without forcing resolution.",
            "Manifesting Generator": "Feelings may slow you down—that's correct. Process before pivoting.",
            "Projector": "Your sensitivity is heightened. Protect your energy and rest more than usual.",
            "Manifestor": "Emotional undercurrents may affect your impulses. Wait for them to settle.",
            "Reflector": "You're feeling the collective emotional release. Discern what's yours to process.",
        }
    return interactions.get(hd_type, interactions["Generator"])


# =============================================================================
# MAIN COMPUTATION
# =============================================================================

def compute_field_signals(
    hd_type: str = "Generator",
    hd_authority: str = "Emotional",
    dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Compute field (macro astrological) signals.
    Returns 1-2 MAX dominant signals.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Calculate astronomical data
    moon_data = calculate_moon_phase(dt)
    season_data = calculate_season(dt)
    eclipse_data = check_eclipse_season(dt)
    
    # Generate all possible signals
    all_signals: List[FieldSignal] = []
    
    # Check each signal type
    new_moon_signal = generate_new_moon_signal(moon_data, hd_type, hd_authority)
    if new_moon_signal:
        all_signals.append(new_moon_signal)
    
    full_moon_signal = generate_full_moon_signal(moon_data, hd_type, hd_authority)
    if full_moon_signal:
        all_signals.append(full_moon_signal)
    
    waning_signal = generate_waning_crescent_signal(moon_data, hd_type, hd_authority)
    if waning_signal:
        all_signals.append(waning_signal)
    
    equinox_signal = generate_equinox_signal(season_data, hd_type, hd_authority)
    if equinox_signal:
        all_signals.append(equinox_signal)
    
    solstice_signal = generate_solstice_signal(season_data, hd_type, hd_authority)
    if solstice_signal:
        all_signals.append(solstice_signal)
    
    eclipse_signal = generate_eclipse_signal(eclipse_data, hd_type, hd_authority)
    if eclipse_signal:
        all_signals.append(eclipse_signal)
    
    # Sort by strength and take top 2
    all_signals.sort(key=lambda s: s.strength, reverse=True)
    top_signals = all_signals[:2]
    
    # Extract HD connection hints for modifying transit signals
    hd_connection_hints = [s.hd_connection_hint for s in top_signals]
    
    logger.info(f"[FieldSignals] Computed {len(all_signals)} signals, returning top {len(top_signals)}")
    
    # Compute field context for downstream signal adaptation
    field_context = compute_field_context(top_signals, moon_data, season_data, eclipse_data)
    
    return {
        "computed_at": dt.isoformat(),
        "moon_phase": moon_data,
        "season": season_data,
        "eclipse": eclipse_data,
        "signals": [signal_to_dict(s) for s in top_signals],
        "hd_connection_hints": hd_connection_hints,
        "has_major_event": len(top_signals) > 0 and top_signals[0].strength >= 0.85,
        "field_context": field_context,
    }


def compute_field_context(
    signals: List[FieldSignal],
    moon_data: Dict,
    season_data: Dict,
    eclipse_data: Dict
) -> Dict[str, str]:
    """
    Compute field context that governs how HD signals should be adapted.
    
    Returns:
        field_tone: "reset" | "clarity" | "pressure" | "release" | "turning_point"
        clarity_level: "low" | "emerging" | "high"
        pace: "slow" | "building" | "fast"
        dominant_message: A short phrase for connecting signals
    """
    if not signals:
        return {
            "field_tone": "clarity",
            "clarity_level": "high",
            "pace": "building",
            "dominant_message": "things are relatively stable",
        }
    
    primary = signals[0]
    signal_type = primary.signal_type
    
    # Determine field tone based on signal type
    if signal_type in [FieldSignalType.NEW_MOON]:
        field_tone = "reset"
        clarity_level = "low"
        pace = "slow"
        dominant_message = "a reset is happening—things are still forming"
    elif signal_type in [FieldSignalType.FULL_MOON]:
        field_tone = "clarity"
        clarity_level = "high"
        pace = "fast"
        dominant_message = "everything is illuminated right now"
    elif signal_type in [FieldSignalType.WANING_CRESCENT]:
        field_tone = "release"
        clarity_level = "emerging"
        pace = "slow"
        dominant_message = "a cycle is completing"
    elif signal_type in [FieldSignalType.EQUINOX]:
        field_tone = "turning_point"
        clarity_level = "emerging"
        pace = "building"
        dominant_message = "a major shift is unfolding"
    elif signal_type in [FieldSignalType.SOLSTICE]:
        field_tone = "turning_point"
        clarity_level = "emerging"
        pace = "slow"
        dominant_message = "the energy is at an extreme"
    elif signal_type in [FieldSignalType.ECLIPSE_SOLAR, FieldSignalType.ECLIPSE_LUNAR]:
        field_tone = "pressure"
        clarity_level = "low"
        pace = "fast"
        dominant_message = "powerful forces are at play"
    else:
        field_tone = "clarity"
        clarity_level = "emerging"
        pace = "building"
        dominant_message = "subtle shifts are happening"
    
    # Check for secondary signals that modify context
    if len(signals) > 1:
        secondary = signals[1]
        if secondary.signal_type in [FieldSignalType.ECLIPSE_SOLAR, FieldSignalType.ECLIPSE_LUNAR]:
            # Eclipse intensifies everything
            if clarity_level == "high":
                clarity_level = "emerging"
            pace = "fast"
        elif secondary.signal_type in [FieldSignalType.EQUINOX, FieldSignalType.SOLSTICE]:
            # Seasonal shift adds turning point energy
            if field_tone not in ["reset", "pressure"]:
                field_tone = "turning_point"
    
    return {
        "field_tone": field_tone,
        "clarity_level": clarity_level,
        "pace": pace,
        "dominant_message": dominant_message,
    }


def signal_to_dict(signal: FieldSignal) -> Dict[str, Any]:
    """Convert FieldSignal to dictionary."""
    return {
        "signal_type": signal.signal_type.value,
        "strength": signal.strength,
        "headline": signal.headline,
        "what_happening": signal.what_happening,
        "why_happening": signal.why_happening,
        "how_interacts_with_hd": signal.how_interacts_with_hd,
        "hd_connection_hint": signal.hd_connection_hint,
        "days_until": signal.days_until,
        "is_approaching": signal.is_approaching,
    }
