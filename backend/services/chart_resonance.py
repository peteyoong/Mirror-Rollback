"""
Chart-Timeline Resonance Detection Service

Detects moments where a user's life events align with significant chart signals.
This creates recognition moments where users see resonance between their lived 
experiences and astrological/Human Design/BaZi cycles.

IMPORTANT: Mirror does NOT claim prediction. This module highlights RESONANCE
between life events and chart signals - timing coincidences, not causation.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# RESONANCE SIGNAL TYPES
# =============================================================================

RESONANCE_TYPES = {
    "saturn_return": {
        "name": "Saturn Return",
        "system": "astrology",
        "description": "A major Saturn cycle associated with restructuring and responsibility.",
        "reflection": "These cycles often correspond with periods of life restructuring.",
    },
    "nodal_return": {
        "name": "Nodal Return",
        "system": "astrology", 
        "description": "A lunar node cycle associated with life direction and purpose themes.",
        "reflection": "Nodal returns often align with periods of directional shift or calling.",
    },
    "saturn_opposition": {
        "name": "Saturn Opposition",
        "system": "astrology",
        "description": "A mid-Saturn cycle associated with reevaluation.",
        "reflection": "This period often invites reassessment of established structures.",
    },
    "bazi_element_shift": {
        "name": "Elemental Shift Year",
        "system": "bazi",
        "description": "A year where dominant elemental energy shifts in your BaZi chart.",
        "reflection": "Elemental transitions can feel like changes in life's texture or pace.",
    },
    "bazi_clash_year": {
        "name": "Branch Clash Year",
        "system": "bazi",
        "description": "A year where elemental branches clash with your birth chart.",
        "reflection": "Clash years often coincide with periods of friction or accelerated change.",
    },
    "human_design_gate": {
        "name": "Significant Gate Activation",
        "system": "human_design",
        "description": "A period aligned with a key gate in your Human Design chart.",
        "reflection": "Gate activations can highlight themes already present in your design.",
    },
}

# =============================================================================
# CYCLE CALCULATION FUNCTIONS
# =============================================================================

def calculate_saturn_return_years(birth_year: int) -> List[int]:
    """
    Calculate approximate Saturn return years.
    Saturn return occurs approximately every 29.5 years.
    
    Returns years when Saturn returns would occur.
    """
    saturn_cycle = 29.5
    returns = []
    
    # Calculate up to 3 returns (ages ~29, ~59, ~88)
    for i in range(1, 4):
        return_year = birth_year + int(saturn_cycle * i)
        returns.append(return_year)
    
    return returns


def calculate_saturn_opposition_years(birth_year: int) -> List[int]:
    """
    Calculate approximate Saturn opposition years.
    Saturn opposition occurs approximately at 14-15 years and 44-45 years.
    """
    oppositions = []
    half_cycle = 14.75  # Half of 29.5
    
    for i in range(1, 5):  # Up to 4 oppositions
        opp_year = birth_year + int(half_cycle * (2 * i - 1))
        oppositions.append(opp_year)
    
    return oppositions


def calculate_nodal_return_years(birth_year: int) -> List[int]:
    """
    Calculate approximate Nodal return years.
    Lunar nodes return approximately every 18.6 years.
    """
    nodal_cycle = 18.6
    returns = []
    
    # Calculate up to 5 returns
    for i in range(1, 6):
        return_year = birth_year + int(nodal_cycle * i)
        returns.append(return_year)
    
    return returns


def calculate_bazi_significant_years(birth_year: int, bazi_chart: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Calculate significant BaZi years based on elemental cycles.
    
    Chinese zodiac cycles every 12 years (branch) and 10 years (stem).
    Clash years are when the current year's branch opposes the birth branch.
    """
    significant_years = []
    
    # Branch clash pairs (opposing branches in the zodiac)
    branch_clashes = {
        0: 6,   # Rat (子) clashes with Horse (午)
        1: 7,   # Ox (丑) clashes with Goat (未)
        2: 8,   # Tiger (寅) clashes with Monkey (申)
        3: 9,   # Rabbit (卯) clashes with Rooster (酉)
        4: 10,  # Dragon (辰) clashes with Dog (戌)
        5: 11,  # Snake (巳) clashes with Pig (亥)
        6: 0, 7: 1, 8: 2, 9: 3, 10: 4, 11: 5  # Reverse
    }
    
    # Calculate birth year branch (using 1984 as Rat year reference)
    birth_branch_idx = (birth_year - 1984) % 12
    clash_branch_idx = branch_clashes.get(birth_branch_idx, -1)
    
    # Find clash years within reasonable range
    current_year = datetime.now().year
    for year in range(birth_year + 12, current_year + 10):
        year_branch_idx = (year - 1984) % 12
        
        if year_branch_idx == clash_branch_idx:
            significant_years.append({
                "year": year,
                "type": "bazi_clash_year",
                "description": "Branch clash year"
            })
    
    # Add 12-year cycle returns (when animal sign repeats)
    for cycle in range(1, 8):
        return_year = birth_year + (12 * cycle)
        if return_year <= current_year + 10:
            significant_years.append({
                "year": return_year,
                "type": "bazi_element_shift",
                "description": "Zodiac return year"
            })
    
    return significant_years


# =============================================================================
# MAIN RESONANCE DETECTION
# =============================================================================

def detect_chart_resonances(
    events: List[Dict[str, Any]],
    birth_year: int,
    bazi_chart: Optional[Dict] = None,
    human_design_chart: Optional[Dict] = None,
    astrology_chart: Optional[Dict] = None,
    tolerance_years: int = 1,
    min_confidence: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Detect resonance between lifeline events and chart signals.
    
    This function finds moments where life events coincide with significant 
    astrological or metaphysical cycles (Saturn returns, nodal returns, etc.)
    
    IMPORTANT: This does NOT claim prediction. It only highlights COINCIDENCE
    between recorded life events and chart signal timing.
    
    Args:
        events: List of lifeline events with at least 'year' field
        birth_year: User's birth year for calculating signal years
        bazi_chart: Optional BaZi chart data for element-based signals
        human_design_chart: Optional Human Design chart data
        astrology_chart: Optional astrology chart data
        tolerance_years: How many years difference to still consider a match
        min_confidence: Minimum confidence score to include a resonance (0-1)
    
    Returns:
        List of resonance objects with event_id, signal_type, confidence, and explanation
    """
    resonances = []
    
    # Build chart signal years
    chart_signals = []
    
    # Saturn returns (~29, ~58, ~87) - HIGH confidence, major life cycle
    saturn_returns = calculate_saturn_return_years(birth_year)
    for year in saturn_returns:
        chart_signals.append({
            "year": year,
            "type": "saturn_return",
            "age": year - birth_year,
            "base_confidence": 0.9  # Saturn returns are well-established
        })
    
    # Saturn oppositions (~14, ~44, ~73) - MEDIUM confidence
    saturn_oppositions = calculate_saturn_opposition_years(birth_year)
    for year in saturn_oppositions:
        chart_signals.append({
            "year": year,
            "type": "saturn_opposition", 
            "age": year - birth_year,
            "base_confidence": 0.75
        })
    
    # Nodal returns (~18, ~37, ~56, ~74, ~93) - MEDIUM confidence
    nodal_returns = calculate_nodal_return_years(birth_year)
    for year in nodal_returns:
        chart_signals.append({
            "year": year,
            "type": "nodal_return",
            "age": year - birth_year,
            "base_confidence": 0.7
        })
    
    # BaZi significant years - LOWER confidence (more speculative)
    bazi_years = calculate_bazi_significant_years(birth_year, bazi_chart)
    for bazi_signal in bazi_years:
        chart_signals.append({
            "year": bazi_signal["year"],
            "type": bazi_signal["type"],
            "age": bazi_signal["year"] - birth_year,
            "base_confidence": 0.6
        })
    
    # Match events to signals
    raw_resonances = []
    for event in events:
        event_year = event.get("year")
        if not event_year:
            continue
        
        # Skip events that happened before the user was born
        age_at_event = event_year - birth_year
        if age_at_event < 0:
            continue
        
        event_id = event.get("id", str(event_year))
        
        for signal in chart_signals:
            signal_year = signal["year"]
            year_diff = abs(event_year - signal_year)
            
            # Check if event year is within tolerance of signal year
            if year_diff <= tolerance_years:
                signal_type = signal["type"]
                signal_info = RESONANCE_TYPES.get(signal_type, {})
                
                # Additional validation for specific signal types
                signal_age = signal.get("age", signal_year - birth_year)
                
                # Saturn return should be ~29, ~58, ~87 (allow ±3 years)
                if signal_type == "saturn_return":
                    valid_ages = [29, 58, 87]
                    if not any(abs(signal_age - va) <= 3 for va in valid_ages):
                        continue
                    # Also validate the event age matches
                    if not any(abs(age_at_event - va) <= 3 for va in valid_ages):
                        continue
                
                # Saturn opposition should be ~14, ~44, ~73 (allow ±2 years)
                if signal_type == "saturn_opposition":
                    valid_ages = [14, 44, 73]
                    if not any(abs(signal_age - va) <= 2 for va in valid_ages):
                        continue
                
                # Nodal return should be ~18, ~37, ~56, ~74 (allow ±2 years)
                if signal_type == "nodal_return":
                    valid_ages = [18, 37, 56, 74, 93]
                    if not any(abs(signal_age - va) <= 2 for va in valid_ages):
                        continue
                
                # Calculate confidence based on:
                # 1. Base confidence of the signal type
                # 2. Exactness of the year match
                base_confidence = signal.get("base_confidence", 0.5)
                year_match_bonus = 0.1 if year_diff == 0 else 0
                confidence = min(base_confidence + year_match_bonus, 1.0)
                
                raw_resonances.append({
                    "event_id": event_id,
                    "event_year": event_year,
                    "event_title": event.get("title", ""),
                    "signal_type": signal_type,
                    "signal_year": signal_year,
                    "signal_name": signal_info.get("name", signal_type),
                    "system": signal_info.get("system", "unknown"),
                    "description": signal_info.get("description", ""),
                    "reflection": signal_info.get("reflection", ""),
                    "age_at_event": age_at_event,
                    "match_quality": "exact" if year_diff == 0 else "near",
                    "confidence": confidence
                })
    
    # Filter by minimum confidence
    confident_resonances = [r for r in raw_resonances if r["confidence"] >= min_confidence]
    
    # Deduplicate: For each signal_type, only keep the best match per 3-year window
    # This prevents "Saturn Return" showing for every event in 1996, 1997, 1998
    deduped_resonances = deduplicate_resonances_by_window(confident_resonances, window_years=3)
    
    # Remove event-level duplicates (same event matching multiple similar signals)
    seen = set()
    unique_resonances = []
    for r in deduped_resonances:
        key = (r["event_id"], r["signal_type"])
        if key not in seen:
            seen.add(key)
            unique_resonances.append(r)
    
    # Sort by event year
    unique_resonances.sort(key=lambda x: x["event_year"])
    
    logger.info(f"[ChartResonance] Detected {len(unique_resonances)} resonances for birth_year={birth_year} (filtered from {len(raw_resonances)} raw)")
    
    return unique_resonances


def deduplicate_resonances_by_window(resonances: List[Dict], window_years: int = 3) -> List[Dict]:
    """
    Deduplicate resonances so that only the best match per signal_type 
    is kept within each time window.
    
    For example, if there are 3 events in 1996-1998 all showing Saturn Return,
    only keep the one with highest confidence or exact match.
    """
    if not resonances:
        return []
    
    # Group by signal_type
    by_type: Dict[str, List[Dict]] = {}
    for r in resonances:
        signal_type = r["signal_type"]
        if signal_type not in by_type:
            by_type[signal_type] = []
        by_type[signal_type].append(r)
    
    result = []
    for signal_type, type_resonances in by_type.items():
        # Sort by event_year
        type_resonances.sort(key=lambda x: x["event_year"])
        
        # Keep best match per window
        windows_used = []  # Track (start_year, end_year) windows used
        
        for r in type_resonances:
            event_year = r["event_year"]
            
            # Check if this falls within an already-used window
            in_existing_window = False
            for start, end in windows_used:
                if start <= event_year <= end:
                    in_existing_window = True
                    break
            
            if not in_existing_window:
                # Add this resonance and mark the window
                result.append(r)
                windows_used.append((event_year - window_years // 2, event_year + window_years // 2))
    
    return result


def format_resonance_for_display(resonance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a resonance object for frontend display.
    
    Returns observational, non-predictive language.
    """
    signal_name = resonance.get("signal_name", "Chart Signal")
    event_year = resonance.get("event_year", "")
    event_title = resonance.get("event_title", "life event")
    reflection = resonance.get("reflection", "")
    confidence = resonance.get("confidence", 0.5)
    
    # Build display text with observational language
    if resonance.get("match_quality") == "exact":
        timing_text = f"In {event_year}, a {signal_name.lower()} occurred."
    else:
        timing_text = f"Around {event_year}, a {signal_name.lower()} was active."
    
    return {
        **resonance,
        "display_title": "Resonance Moment",
        "display_timing": timing_text,
        "display_reflection": reflection,
        "display_footer": "Your timeline shows a turning point during this same period.",
        "display_confidence": "strong" if confidence >= 0.85 else "moderate" if confidence >= 0.7 else "light"
    }


def get_resonance_summary_for_patterns(
    resonances: List[Dict[str, Any]], 
    max_items: int = 3
) -> List[Dict[str, Any]]:
    """
    Get a summary of resonances for the Pattern Lens view.
    
    Returns up to max_items resonances formatted for pattern display.
    """
    if not resonances:
        return []
    
    # Prioritize high-impact resonances (Saturn returns, exact matches)
    priority_order = ["saturn_return", "nodal_return", "saturn_opposition", "bazi_clash_year", "bazi_element_shift"]
    
    sorted_resonances = sorted(
        resonances,
        key=lambda x: (
            priority_order.index(x["signal_type"]) if x["signal_type"] in priority_order else 99,
            0 if x["match_quality"] == "exact" else 1
        )
    )
    
    result = []
    for r in sorted_resonances[:max_items]:
        formatted = format_resonance_for_display(r)
        result.append({
            "year": r["event_year"],
            "event_title": r["event_title"],
            "signal_name": r["signal_name"],
            "system": r["system"],
            "summary": f"Resonates with a {r['signal_name']} associated with {r['description'].lower()}" if r.get("description") else f"Resonates with a {r['signal_name']}."
        })
    
    return result
