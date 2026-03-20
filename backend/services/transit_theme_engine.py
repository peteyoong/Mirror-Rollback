"""
Transit Theme Engine V1
========================

Computes COMPOSITE THEMES from multiple timing signals.
NOT single-point astrology - aggregate environmental conditions.

Sources:
- Lunar phase
- Seasonal position
- Transit activations (simplified)
- Cyclical patterns

Output: Active themes with intensity scores
"""

import os
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TIMING THEMES - Core vocabulary for transit conditions
# ============================================================================

TIMING_THEMES = {
    # === CHALLENGE / SHADOW THEMES ===
    "emotional_sensitivity": {
        "description": "Heightened emotional awareness and reactivity",
        "indicators": ["lunar_peak", "water_season", "venus_active"],
        "polarity": "neutral",  # Can be positive or challenging
    },
    "clarity_vs_confusion": {
        "description": "Mental clarity may fluctuate",
        "indicators": ["mercury_retrograde", "mutable_season", "neptune_active"],
        "polarity": "challenge",
    },
    "pressure": {
        "description": "External or internal pressure intensifying",
        "indicators": ["saturn_active", "cardinal_season", "eclipse_window"],
        "polarity": "challenge",
    },
    "urgency": {
        "description": "Sense of needing to act or decide quickly",
        "indicators": ["mars_active", "fire_season", "lunar_waning"],
        "polarity": "challenge",
    },
    "transition_threshold": {
        "description": "Standing at a crossroads or decision point",
        "indicators": ["equinox_window", "eclipse_window", "saturn_return"],
        "polarity": "neutral",
    },
    "reset_cycle": {
        "description": "Natural ending and beginning phase",
        "indicators": ["new_moon", "solstice_window", "pluto_active"],
        "polarity": "neutral",
    },
    "relational_sensitivity": {
        "description": "Relationships and connection feel heightened",
        "indicators": ["venus_active", "full_moon", "libra_season"],
        "polarity": "neutral",
    },
    "identity_shift": {
        "description": "Questions about self and direction",
        "indicators": ["sun_transit", "aries_season", "uranus_active"],
        "polarity": "neutral",
    },
    "expansion": {
        "description": "Growth, opportunity, opening energy",
        "indicators": ["jupiter_active", "sagittarius_season", "waxing_moon"],
        "polarity": "opening",
    },
    "contraction": {
        "description": "Consolidation, reflection, inward energy",
        "indicators": ["saturn_active", "capricorn_season", "waning_moon"],
        "polarity": "challenge",
    },
    
    # === POSITIVE / OPENING THEMES (NEW) ===
    "relational_harmony": {
        "description": "Ease and flow in connection with others",
        "indicators": ["venus_active", "libra_season", "waxing_moon"],
        "polarity": "opening",
    },
    "emotional_openness": {
        "description": "Capacity to feel and express freely",
        "indicators": ["full_moon", "water_season", "jupiter_active"],
        "polarity": "opening",
    },
    "receptivity": {
        "description": "Openness to receiving support, love, input",
        "indicators": ["venus_active", "cancer_season", "waxing_moon"],
        "polarity": "opening",
    },
    "renewal_cycle": {
        "description": "Fresh energy, new chapter beginning",
        "indicators": ["new_moon", "aries_season", "jupiter_active"],
        "polarity": "opening",
    },
    "reconnection_window": {
        "description": "Opportunity to rebuild or repair connection",
        "indicators": ["venus_active", "full_moon", "libra_season"],
        "polarity": "opening",
    },
    "softening_phase": {
        "description": "Defenses lowering, heart opening",
        "indicators": ["venus_active", "pisces_season", "waning_crescent"],
        "polarity": "opening",
    },
    "integration_phase": {
        "description": "Coming together of previously separate parts",
        "indicators": ["full_moon", "virgo_season", "mercury_direct"],
        "polarity": "opening",
    },
    "grounded_stability": {
        "description": "Sense of solid footing and presence",
        "indicators": ["taurus_season", "earth_element", "saturn_stable"],
        "polarity": "opening",
    },
}


# ============================================================================
# LUNAR PHASE COMPUTATION
# ============================================================================

def get_lunar_phase(dt: datetime) -> Dict[str, Any]:
    """
    Calculate lunar phase for a given datetime.
    Returns phase name and intensity (0-1).
    """
    # Known new moon: January 29, 2025 12:36 UTC
    known_new_moon = datetime(2025, 1, 29, 12, 36, 0, tzinfo=timezone.utc)
    lunar_cycle = 29.530588853  # Synodic month in days
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    days_since = (dt - known_new_moon).total_seconds() / 86400
    phase_position = (days_since % lunar_cycle) / lunar_cycle
    
    # Phase names and emotional associations
    if phase_position < 0.0625:
        phase = "new_moon"
        emotional_weight = 0.9  # New beginnings, introspection
    elif phase_position < 0.25:
        phase = "waxing_crescent"
        emotional_weight = 0.5
    elif phase_position < 0.3125:
        phase = "first_quarter"
        emotional_weight = 0.6
    elif phase_position < 0.4375:
        phase = "waxing_gibbous"
        emotional_weight = 0.7
    elif phase_position < 0.5625:
        phase = "full_moon"
        emotional_weight = 1.0  # Peak emotional intensity
    elif phase_position < 0.6875:
        phase = "waning_gibbous"
        emotional_weight = 0.7
    elif phase_position < 0.8125:
        phase = "last_quarter"
        emotional_weight = 0.6
    else:
        phase = "waning_crescent"
        emotional_weight = 0.8  # Release, letting go
    
    return {
        "phase": phase,
        "position": phase_position,
        "emotional_weight": emotional_weight,
        "is_waxing": phase_position < 0.5,
        "is_peak": phase in ["full_moon", "new_moon"],
    }


# ============================================================================
# SEASONAL POSITION
# ============================================================================

def get_seasonal_context(dt: datetime) -> Dict[str, Any]:
    """
    Get seasonal and astrological context.
    Returns season, element, and modality.
    """
    month = dt.month
    day = dt.day
    
    # Approximate zodiac seasons (tropical)
    zodiac_seasons = [
        (1, 20, "aquarius", "air", "fixed", "capricorn_season"),
        (2, 19, "pisces", "water", "mutable", "aquarius_season"),
        (3, 20, "aries", "fire", "cardinal", "pisces_season"),
        (4, 20, "taurus", "earth", "fixed", "aries_season"),
        (5, 21, "gemini", "air", "mutable", "taurus_season"),
        (6, 21, "cancer", "water", "cardinal", "gemini_season"),
        (7, 22, "leo", "fire", "fixed", "cancer_season"),
        (8, 23, "virgo", "earth", "mutable", "leo_season"),
        (9, 23, "libra", "air", "cardinal", "virgo_season"),
        (10, 23, "scorpio", "water", "fixed", "libra_season"),
        (11, 22, "sagittarius", "fire", "mutable", "scorpio_season"),
        (12, 21, "capricorn", "earth", "cardinal", "sagittarius_season"),
    ]
    
    current_sign = None
    current_element = None
    current_modality = None
    season_indicator = None
    
    for i, (end_month, end_day, sign, element, modality, prev_season) in enumerate(zodiac_seasons):
        if month < end_month or (month == end_month and day < end_day):
            current_sign = zodiac_seasons[i-1][2] if i > 0 else "capricorn"
            current_element = zodiac_seasons[i-1][3] if i > 0 else "earth"
            current_modality = zodiac_seasons[i-1][4] if i > 0 else "cardinal"
            season_indicator = f"{current_sign}_season"
            break
    else:
        current_sign = "capricorn"
        current_element = "earth"
        current_modality = "cardinal"
        season_indicator = "capricorn_season"
    
    # Check for equinox/solstice windows (within 7 days)
    equinox_solstice_dates = [
        (3, 20), (6, 21), (9, 22), (12, 21)
    ]
    
    near_threshold = False
    for m, d in equinox_solstice_dates:
        days_diff = abs((month * 30 + day) - (m * 30 + d))
        if days_diff <= 7 or days_diff >= 358:
            near_threshold = True
            break
    
    return {
        "sign": current_sign,
        "element": current_element,
        "modality": current_modality,
        "season_indicator": season_indicator,
        "near_equinox_solstice": near_threshold,
        "is_water_season": current_element == "water",
        "is_fire_season": current_element == "fire",
        "is_cardinal": current_modality == "cardinal",
        "is_mutable": current_modality == "mutable",
    }


# ============================================================================
# TRANSIT ACTIVATIONS (Simplified)
# ============================================================================

def get_transit_activations(dt: datetime) -> Dict[str, bool]:
    """
    Simplified transit activation check.
    In production, this would connect to ephemeris data.
    For now, uses cyclical approximations.
    """
    day_of_year = dt.timetuple().tm_yday
    year = dt.year
    
    activations = {}
    
    # Mercury retrograde approximation (3x per year, ~3 weeks each)
    # Simplified: roughly every 116 days for 21 days
    mercury_cycle = (day_of_year + year * 365) % 116
    activations["mercury_retrograde"] = mercury_cycle < 21
    
    # Venus activation (every 18 months prominent)
    venus_cycle = (day_of_year + year * 365) % 584
    activations["venus_active"] = venus_cycle < 40 or venus_cycle > 544
    
    # Mars activation (every 2 years prominent)
    mars_cycle = (day_of_year + year * 365) % 780
    activations["mars_active"] = mars_cycle < 60
    
    # Jupiter activation (annual aspect windows)
    jupiter_cycle = (day_of_year + year * 365) % 399
    activations["jupiter_active"] = jupiter_cycle < 30 or jupiter_cycle > 369
    
    # Saturn activation (longer cycles)
    saturn_cycle = (day_of_year + year * 365) % 378
    activations["saturn_active"] = saturn_cycle < 45
    
    # Uranus activation (surprise/change windows)
    uranus_cycle = (day_of_year + year * 365) % 369
    activations["uranus_active"] = uranus_cycle < 30
    
    # Neptune activation (confusion/intuition)
    neptune_cycle = (day_of_year + year * 365) % 367
    activations["neptune_active"] = neptune_cycle < 35
    
    # Pluto activation (transformation)
    pluto_cycle = (day_of_year + year * 365) % 366
    activations["pluto_active"] = pluto_cycle < 40
    
    # Eclipse window approximation (within 2 weeks of eclipse)
    eclipse_dates_2025 = [(3, 14), (3, 29), (9, 7), (9, 21)]
    eclipse_dates_2026 = [(2, 17), (3, 3), (8, 12), (8, 28)]
    
    eclipse_dates = eclipse_dates_2025 if year == 2025 else eclipse_dates_2026
    
    for m, d in eclipse_dates:
        days_diff = abs((dt.month * 30 + dt.day) - (m * 30 + d))
        if days_diff <= 14:
            activations["eclipse_window"] = True
            break
    else:
        activations["eclipse_window"] = False
    
    return activations


# ============================================================================
# COMPOSITE THEME COMPUTATION
# ============================================================================

@dataclass
class TransitThemes:
    """Computed transit themes with intensity scores."""
    active_themes: List[str]
    theme_intensity: Dict[str, float]
    lunar_phase: str
    seasonal_context: str
    raw_indicators: List[str]
    computed_at: str


def compute_transit_themes(dt: Optional[datetime] = None) -> TransitThemes:
    """
    Main function: Compute composite themes from all timing signals.
    
    Returns active themes with intensity scores.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Gather all timing signals
    lunar = get_lunar_phase(dt)
    seasonal = get_seasonal_context(dt)
    transits = get_transit_activations(dt)
    
    # Collect active indicators
    active_indicators = []
    
    # Lunar indicators
    if lunar["phase"] in ["full_moon"]:
        active_indicators.append("full_moon")
        active_indicators.append("lunar_peak")
    elif lunar["phase"] == "new_moon":
        active_indicators.append("new_moon")
        active_indicators.append("lunar_peak")
    
    if lunar["is_waxing"]:
        active_indicators.append("waxing_moon")
    else:
        active_indicators.append("waning_moon")
    
    # Seasonal indicators
    active_indicators.append(seasonal["season_indicator"])
    
    if seasonal["is_water_season"]:
        active_indicators.append("water_season")
    if seasonal["is_fire_season"]:
        active_indicators.append("fire_season")
    if seasonal["is_cardinal"]:
        active_indicators.append("cardinal_season")
    if seasonal["is_mutable"]:
        active_indicators.append("mutable_season")
    if seasonal["near_equinox_solstice"]:
        active_indicators.append("equinox_window")
        active_indicators.append("solstice_window")
    
    # Transit indicators
    for transit, is_active in transits.items():
        if is_active:
            active_indicators.append(transit)
    
    # Compute theme intensities
    theme_intensity = {}
    
    for theme_name, theme_data in TIMING_THEMES.items():
        theme_indicators = theme_data["indicators"]
        matching = [ind for ind in theme_indicators if ind in active_indicators]
        
        if matching:
            # Base intensity from indicator match ratio
            base_intensity = len(matching) / len(theme_indicators)
            
            # Boost for lunar peak
            if lunar["is_peak"] and "lunar_peak" in matching:
                base_intensity = min(1.0, base_intensity + 0.2)
            
            # Boost for seasonal alignment
            if seasonal["season_indicator"] in matching:
                base_intensity = min(1.0, base_intensity + 0.15)
            
            # Apply lunar emotional weight
            final_intensity = base_intensity * (0.7 + 0.3 * lunar["emotional_weight"])
            
            theme_intensity[theme_name] = round(final_intensity, 2)
    
    # Sort themes by intensity
    sorted_themes = sorted(
        theme_intensity.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Active themes = those with intensity >= 0.3
    active_themes = [t[0] for t in sorted_themes if t[1] >= 0.3]
    
    return TransitThemes(
        active_themes=active_themes,
        theme_intensity=theme_intensity,
        lunar_phase=lunar["phase"],
        seasonal_context=f"{seasonal['sign']} ({seasonal['element']}, {seasonal['modality']})",
        raw_indicators=active_indicators,
        computed_at=dt.isoformat()
    )


# ============================================================================
# CONTEXT GENERATION
# ============================================================================

def generate_timing_context(themes: TransitThemes) -> List[str]:
    """
    Generate human-readable context lines from transit themes.
    
    Rules:
    - NOT about user identity
    - Describes environment/conditions
    - 2-4 lines max
    - INCLUDES positive/opening context when relevant
    """
    context_lines = []
    
    # Map themes to context statements (including POSITIVE themes)
    theme_to_context = {
        # Challenge/Neutral themes
        "emotional_sensitivity": "Emotional sensitivity may be elevated",
        "clarity_vs_confusion": "Decision clarity may fluctuate",
        "pressure": "External or internal pressure may feel intensified",
        "urgency": "You may feel a push to act or decide quickly",
        "transition_threshold": "This may feel like a transition or crossroads phase",
        "reset_cycle": "This may be a natural ending-and-beginning moment",
        "relational_sensitivity": "Relationships and connection may feel more prominent",
        "identity_shift": "Questions about direction may be surfacing",
        "expansion": "Opportunity and growth energy may be present",
        "contraction": "This may be a period for consolidation and reflection",
        
        # POSITIVE / OPENING themes
        "relational_harmony": "Relational ease and connection may feel more accessible",
        "emotional_openness": "Emotional openness and expression may flow more freely",
        "receptivity": "This may be a time of openness to receiving",
        "renewal_cycle": "Fresh energy and new beginnings may be emerging",
        "reconnection_window": "Conditions may support reconnection and repair",
        "softening_phase": "Defenses may be softening, allowing more in",
        "integration_phase": "What was separate may be coming together",
        "grounded_stability": "A sense of solid ground may be present",
    }
    
    # Add context for top 3 active themes
    for theme in themes.active_themes[:3]:
        if theme in theme_to_context:
            context_lines.append(theme_to_context[theme])
    
    # Add lunar context if relevant
    lunar_context = {
        "full_moon": "Full moon energy may amplify what's already present",
        "new_moon": "New moon suggests a reset or fresh starting point",
        "waning_crescent": "This may be a time for release before new beginnings",
        "waxing_crescent": "New intentions may be gaining momentum",
        "waxing_gibbous": "What you've been building may be coming into focus",
    }
    
    if themes.lunar_phase in lunar_context and len(context_lines) < 4:
        context_lines.append(lunar_context[themes.lunar_phase])
    
    return context_lines[:4]  # Max 4 lines


# ============================================================================
# TIMING SIGNALS FOR EXPLAINABILITY
# ============================================================================

def generate_timing_signals(themes: TransitThemes) -> List[str]:
    """
    Generate timing-specific signals for the explainability layer.
    Includes BOTH challenge and positive/opening signals.
    """
    signals = []
    
    # High-intensity theme signals
    high_intensity_themes = [
        t for t in themes.active_themes 
        if themes.theme_intensity.get(t, 0) >= 0.5
    ]
    
    # === CHALLENGE THEME SIGNALS ===
    if "emotional_sensitivity" in high_intensity_themes:
        signals.append(
            "Current conditions may be amplifying emotional fluctuation"
        )
    
    if "clarity_vs_confusion" in high_intensity_themes:
        signals.append(
            "This may be a period where clarity comes in waves rather than stability"
        )
    
    if "transition_threshold" in high_intensity_themes:
        signals.append(
            "Timing suggests you may be standing at a natural decision point"
        )
    
    if "pressure" in high_intensity_themes:
        signals.append(
            "Current timing may be intensifying pressure that was already present"
        )
    
    if "reset_cycle" in high_intensity_themes:
        signals.append(
            "This may be a natural closing-and-opening phase, not a crisis"
        )
    
    if "urgency" in high_intensity_themes:
        signals.append(
            "The sense of needing to act quickly may be timing-driven, not actual emergency"
        )
    
    # === POSITIVE / OPENING THEME SIGNALS (NEW) ===
    if "relational_harmony" in high_intensity_themes:
        signals.append(
            "Current conditions suggest emotional openness and relational ease"
        )
    
    if "emotional_openness" in high_intensity_themes:
        signals.append(
            "This may be a period where emotional expression flows more freely"
        )
    
    if "receptivity" in high_intensity_themes:
        signals.append(
            "Conditions support openness to receiving support, connection, or insight"
        )
    
    if "renewal_cycle" in high_intensity_themes:
        signals.append(
            "Fresh energy may be present, signaling new beginnings"
        )
    
    if "reconnection_window" in high_intensity_themes:
        signals.append(
            "This may be a favorable window for reconnection or repair"
        )
    
    if "softening_phase" in high_intensity_themes:
        signals.append(
            "Defenses may be naturally softening, allowing more connection"
        )
    
    if "integration_phase" in high_intensity_themes:
        signals.append(
            "What was fragmented may be finding coherence"
        )
    
    if "grounded_stability" in high_intensity_themes:
        signals.append(
            "A sense of stability and groundedness may be present"
        )
    
    if "expansion" in high_intensity_themes:
        signals.append(
            "Growth and opening energy may be available"
        )
    
    # Lunar phase signals
    if themes.lunar_phase == "full_moon":
        signals.append(
            "Full moon period may be bringing subconscious patterns to the surface"
        )
    elif themes.lunar_phase == "new_moon":
        signals.append(
            "New moon suggests this is a natural reset point"
        )
    elif themes.lunar_phase == "waxing_gibbous":
        signals.append(
            "Waxing moon suggests building momentum and clarity"
        )
    
    return signals[:2]  # Max 2 timing signals
