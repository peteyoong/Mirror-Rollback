"""
Transit-to-Natal Aspect Calculator

===============================================================================
TRUE SIDEREAL ASPECT COMPUTATION
===============================================================================

Computes deterministic transit-to-natal aspects using:
- True Sidereal positions from canonical sidereal_config.py
- Standard aspect orbs (configurable)
- Both current snapshot and daily window scans

Aspect Types:
- Conjunction (0°) - orb 8°
- Opposition (180°) - orb 8°
- Trine (120°) - orb 8°
- Square (90°) - orb 7°
- Sextile (60°) - orb 6°
- Quincunx (150°) - orb 3°
- Semi-sextile (30°) - orb 2°

Returns aspects with:
- Exact orb
- Aspect type
- Whether applying or separating
- Timestamp
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ASPECT CONFIGURATION
# =============================================================================

class AspectType(str, Enum):
    CONJUNCTION = "conjunction"
    OPPOSITION = "opposition"
    TRINE = "trine"
    SQUARE = "square"
    SEXTILE = "sextile"
    QUINCUNX = "quincunx"
    SEMI_SEXTILE = "semi-sextile"


ASPECT_CONFIG = {
    AspectType.CONJUNCTION: {"angle": 0, "orb": 8, "nature": "major"},
    AspectType.OPPOSITION: {"angle": 180, "orb": 8, "nature": "major"},
    AspectType.TRINE: {"angle": 120, "orb": 8, "nature": "major"},
    AspectType.SQUARE: {"angle": 90, "orb": 7, "nature": "major"},
    AspectType.SEXTILE: {"angle": 60, "orb": 6, "nature": "major"},
    AspectType.QUINCUNX: {"angle": 150, "orb": 3, "nature": "minor"},
    AspectType.SEMI_SEXTILE: {"angle": 30, "orb": 2, "nature": "minor"},
}

# Tighter orbs for more precise aspects (used for "exact" labeling)
EXACT_ORB_THRESHOLD = 1.0


@dataclass
class TransitAspect:
    """Represents a single transit-to-natal aspect."""
    transit_planet: str
    natal_planet: str
    aspect_type: AspectType
    orb: float
    is_applying: bool
    is_exact: bool
    transit_longitude: float
    natal_longitude: float
    timestamp: str
    
    # Human-readable
    description: str = ""
    significance: str = ""  # "major", "minor"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transit_planet": self.transit_planet,
            "natal_planet": self.natal_planet,
            "aspect_type": self.aspect_type.value,
            "orb": round(self.orb, 2),
            "is_applying": self.is_applying,
            "is_exact": self.is_exact,
            "transit_longitude": round(self.transit_longitude, 4),
            "natal_longitude": round(self.natal_longitude, 4),
            "timestamp": self.timestamp,
            "description": self.description,
            "significance": self.significance,
        }


# =============================================================================
# ASPECT CALCULATION HELPERS
# =============================================================================

def normalize_degrees(deg: float) -> float:
    """Normalize degrees to 0-360 range."""
    deg = deg % 360
    if deg < 0:
        deg += 360
    return deg


def angular_distance(a: float, b: float) -> float:
    """Calculate shortest angular distance between two angles (0-180)."""
    diff = abs(normalize_degrees(a) - normalize_degrees(b))
    if diff > 180:
        diff = 360 - diff
    return diff


def check_aspect(
    transit_long: float,
    natal_long: float,
    transit_speed: float = 0.0
) -> Optional[Tuple[AspectType, float, bool]]:
    """
    Check if two longitudes form an aspect.
    
    Args:
        transit_long: Transiting planet longitude
        natal_long: Natal planet longitude
        transit_speed: Daily motion of transit planet (for applying/separating)
    
    Returns:
        Tuple of (aspect_type, orb, is_applying) or None
    """
    distance = angular_distance(transit_long, natal_long)
    
    for aspect_type, config in ASPECT_CONFIG.items():
        angle = config["angle"]
        orb = config["orb"]
        
        deviation = abs(distance - angle)
        if deviation <= orb:
            # Calculate if applying or separating
            # Applying = transit moving toward exact aspect
            # Separating = transit moving away from exact aspect
            
            # Simplified: if transit speed is positive (moving forward) and
            # it's before the exact aspect, it's applying
            exact_position = natal_long + angle if angle != 0 else natal_long
            exact_position = normalize_degrees(exact_position)
            
            # For conjunction/opposition, handle the two possible exact points
            if angle == 180:
                exact_position = normalize_degrees(natal_long + 180)
            
            # Is the transit approaching or departing the exact point?
            current_distance = angular_distance(transit_long, exact_position)
            
            # Assume positive speed means forward motion
            if transit_speed >= 0:
                is_applying = deviation > 0.1  # Not yet exact
            else:
                is_applying = False  # Retrograde = generally separating
            
            return (aspect_type, deviation, is_applying)
    
    return None


# =============================================================================
# MAIN ASPECT COMPUTATION
# =============================================================================

def compute_transit_natal_aspects(
    natal_planets: Dict[str, Dict[str, Any]],
    transit_dt: Optional[datetime] = None,
    transit_planets: Optional[List[str]] = None
) -> List[TransitAspect]:
    """
    Compute all transit-to-natal aspects for a given moment.
    
    Args:
        natal_planets: Dict of natal planet data with 'longitude' key
                      e.g., {"Sun": {"longitude": 120.5, ...}, "Moon": {...}}
        transit_dt: Datetime for transit calculation (default: now UTC)
        transit_planets: List of transit planets to check (default: Sun, Moon, Mercury, Venus, Mars)
    
    Returns:
        List of TransitAspect objects sorted by orb (tightest first)
    """
    from calculations.sidereal_config import calculate_planet_by_name, PLANETS
    
    if transit_dt is None:
        transit_dt = datetime.now(timezone.utc)
    
    if transit_planets is None:
        # Default: personal planets that move fast enough to be meaningful for daily transits
        transit_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
    
    aspects = []
    timestamp = transit_dt.isoformat()
    
    # Calculate current transit positions
    transit_positions = {}
    for planet_name in transit_planets:
        try:
            pos = calculate_planet_by_name(planet_name, transit_dt)
            transit_positions[planet_name] = pos
        except Exception as e:
            logger.error(f"[TransitAspects] Error calculating {planet_name}: {e}")
    
    # Check each transit planet against each natal planet
    for transit_name, transit_pos in transit_positions.items():
        transit_long = transit_pos['longitude']
        transit_speed = transit_pos.get('speed', 0)
        
        for natal_name, natal_data in natal_planets.items():
            natal_long = natal_data.get('longitude')
            if natal_long is None:
                continue
            
            # Skip same planet (Sun-Sun aspects are less meaningful for transits)
            # But include them for completeness
            
            result = check_aspect(transit_long, natal_long, transit_speed)
            if result:
                aspect_type, orb, is_applying = result
                config = ASPECT_CONFIG[aspect_type]
                
                aspect = TransitAspect(
                    transit_planet=transit_name,
                    natal_planet=natal_name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=is_applying,
                    is_exact=orb <= EXACT_ORB_THRESHOLD,
                    transit_longitude=transit_long,
                    natal_longitude=natal_long,
                    timestamp=timestamp,
                    description=f"Transit {transit_name} {aspect_type.value} natal {natal_name}",
                    significance=config["nature"],
                )
                aspects.append(aspect)
    
    # Sort by orb (tightest first)
    aspects.sort(key=lambda a: a.orb)
    
    return aspects


def compute_daily_aspect_window(
    natal_planets: Dict[str, Dict[str, Any]],
    date: Optional[datetime] = None,
    transit_planets: Optional[List[str]] = None,
    interval_hours: int = 2
) -> Dict[str, Any]:
    """
    Scan a full day for transit-to-natal aspects at regular intervals.
    
    Useful for finding when aspects become exact during the day.
    
    Args:
        natal_planets: Dict of natal planet data with 'longitude' key
        date: Date to scan (default: today UTC)
        transit_planets: List of transit planets to check
        interval_hours: Hours between scan points (default: 2)
    
    Returns:
        Dict with:
        - aspects_found: List of unique aspects found
        - exact_times: Dict mapping aspect descriptions to exact times
        - scan_points: Number of points scanned
    """
    if date is None:
        date = datetime.now(timezone.utc)
    
    # Start at midnight UTC of the given date
    day_start = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    
    all_aspects = {}  # aspect_key -> best (tightest orb) aspect
    exact_times = {}  # aspect_key -> timestamp when orb is tightest
    
    # Scan every interval_hours
    scan_points = 24 // interval_hours
    for i in range(scan_points + 1):
        scan_dt = day_start + timedelta(hours=i * interval_hours)
        aspects = compute_transit_natal_aspects(natal_planets, scan_dt, transit_planets)
        
        for aspect in aspects:
            key = f"{aspect.transit_planet}_{aspect.aspect_type.value}_{aspect.natal_planet}"
            
            if key not in all_aspects or aspect.orb < all_aspects[key].orb:
                all_aspects[key] = aspect
                exact_times[key] = aspect.timestamp
    
    return {
        "date": day_start.strftime("%Y-%m-%d"),
        "aspects_found": [a.to_dict() for a in all_aspects.values()],
        "exact_times": exact_times,
        "scan_points": scan_points + 1,
        "interval_hours": interval_hours,
    }


def get_current_transit_aspects_for_user(
    user_natal_chart: Dict[str, Any],
    dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get current transit-to-natal aspects for a user's natal chart.
    
    Args:
        user_natal_chart: User's natal chart data (from astrology.py get_full_natal_chart)
        dt: Datetime for calculation (default: now UTC)
    
    Returns:
        Dict with current aspects, formatted for frontend display
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Extract natal planet positions from chart
    natal_planets = user_natal_chart.get('planets', {})
    
    # Compute current snapshot aspects
    current_aspects = compute_transit_natal_aspects(natal_planets, dt)
    
    # Filter to major aspects for display
    major_aspects = [a for a in current_aspects if a.significance == "major"]
    minor_aspects = [a for a in current_aspects if a.significance == "minor"]
    
    # Find exact or nearly exact aspects (orb < 1°)
    exact_aspects = [a for a in current_aspects if a.is_exact]
    
    return {
        "computed_at": dt.isoformat(),
        "total_aspects": len(current_aspects),
        "major_aspects": [a.to_dict() for a in major_aspects],
        "minor_aspects": [a.to_dict() for a in minor_aspects],
        "exact_aspects": [a.to_dict() for a in exact_aspects],
        "top_3": [a.to_dict() for a in current_aspects[:3]],
    }


# =============================================================================
# DEBUG HELPER
# =============================================================================

def debug_transit_aspects(natal_planets: Dict[str, Dict[str, Any]], user_label: str = "Test") -> None:
    """
    Debug helper to print all current transit-to-natal aspects.
    """
    print(f"\n{'='*70}")
    print(f"TRANSIT-TO-NATAL ASPECTS: {user_label}")
    print(f"{'='*70}")
    
    now = datetime.now(timezone.utc)
    print(f"Timestamp: {now.isoformat()}")
    print()
    
    aspects = compute_transit_natal_aspects(natal_planets, now)
    
    if not aspects:
        print("No aspects found within orb.")
        return
    
    print(f"Found {len(aspects)} aspects:")
    print("-"*70)
    
    for aspect in aspects:
        exact_marker = "★" if aspect.is_exact else " "
        applying = "applying" if aspect.is_applying else "separating"
        print(f"{exact_marker} {aspect.description}")
        print(f"    Orb: {aspect.orb:.2f}° ({applying})")
        print(f"    Transit: {aspect.transit_longitude:.2f}° | Natal: {aspect.natal_longitude:.2f}°")
        print()
