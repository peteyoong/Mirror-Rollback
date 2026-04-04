"""
Daily Transit Window Scanner

===============================================================================
TRUE SIDEREAL DAILY EVENT DETECTION
===============================================================================

Scans a full day (local timezone) for all transit events:
- Moon sign ingress (exact time when Moon changes signs)
- Moon/planet house ingress (exact time when transit planet changes houses)
- Transit-to-natal aspects reaching exactitude
- Major sky events (eclipse windows, station/retrogrades)

Uses Swiss Ephemeris True Sidereal (SVP 31.2836°, J2000) exclusively.

Event Types:
- MOON_INGRESS: Moon enters a new zodiac sign
- HOUSE_INGRESS: Transit planet enters a new natal house
- ASPECT_EXACT: Transit-natal aspect reaches exact orb
- ASPECT_WINDOW: Transit-natal aspect enters/exits orb window
- MOON_PHASE: Lunar phase peaks (new/full/quarter)

All timestamps are returned in both UTC and local timezone.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pytz

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT TYPES
# =============================================================================

class TransitEventType(str, Enum):
    MOON_INGRESS = "moon_ingress"
    HOUSE_INGRESS = "house_ingress"
    ASPECT_EXACT = "aspect_exact"
    ASPECT_ENTERS_ORB = "aspect_enters_orb"
    ASPECT_EXITS_ORB = "aspect_exits_orb"
    MOON_PHASE = "moon_phase"
    PLANET_STATION = "planet_station"  # Retrograde/direct station


class EventTiming(str, Enum):
    PASSED = "passed"
    CURRENT = "current"
    UPCOMING = "upcoming"


# =============================================================================
# EVENT DATA CLASSES
# =============================================================================

@dataclass
class TransitEvent:
    """Represents a single transit event in the daily window."""
    event_type: TransitEventType
    timestamp_utc: datetime
    timestamp_local: datetime
    local_timezone: str
    
    # Event details
    description: str
    significance: str  # "major", "moderate", "minor"
    
    # Timing relative to now
    timing: EventTiming
    minutes_from_now: int
    
    # Aspect-specific (optional)
    transit_planet: Optional[str] = None
    natal_planet: Optional[str] = None
    aspect_type: Optional[str] = None
    orb_at_peak: Optional[float] = None
    
    # Ingress-specific (optional)
    from_sign: Optional[str] = None
    to_sign: Optional[str] = None
    
    # House ingress-specific (optional)
    from_house: Optional[int] = None
    to_house: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "timestamp_local": self.timestamp_local.isoformat(),
            "local_time": self.timestamp_local.strftime("%I:%M %p"),
            "local_timezone": self.local_timezone,
            "description": self.description,
            "significance": self.significance,
            "timing": self.timing.value,
            "minutes_from_now": self.minutes_from_now,
            "transit_planet": self.transit_planet,
            "natal_planet": self.natal_planet,
            "aspect_type": self.aspect_type,
            "orb_at_peak": round(self.orb_at_peak, 2) if self.orb_at_peak else None,
            "from_sign": self.from_sign,
            "to_sign": self.to_sign,
            "from_house": self.from_house,
            "to_house": self.to_house,
        }


@dataclass
class DailyTransitWindow:
    """Full daily transit window scan result."""
    date: str
    local_timezone: str
    scan_start_utc: datetime
    scan_end_utc: datetime
    computed_at: datetime
    
    # Events categorized
    all_events: List[TransitEvent] = field(default_factory=list)
    moon_ingresses: List[TransitEvent] = field(default_factory=list)
    house_ingresses: List[TransitEvent] = field(default_factory=list)
    aspect_events: List[TransitEvent] = field(default_factory=list)
    
    # Slow-moving transits (active but no exact time today)
    slow_transits_active: List[Dict] = field(default_factory=list)
    
    # Current house positions for transit planets
    transit_houses: Dict[str, int] = field(default_factory=dict)
    
    # Summary
    current_moon_sign: str = ""
    current_moon_house: int = 0
    next_moon_sign: str = ""
    next_moon_ingress_time: Optional[str] = None
    strongest_active_aspect: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "local_timezone": self.local_timezone,
            "scan_start_utc": self.scan_start_utc.isoformat(),
            "scan_end_utc": self.scan_end_utc.isoformat(),
            "computed_at": self.computed_at.isoformat(),
            "total_events": len(self.all_events),
            "all_events": [e.to_dict() for e in self.all_events],
            "moon_ingresses": [e.to_dict() for e in self.moon_ingresses],
            "house_ingresses": [e.to_dict() for e in self.house_ingresses],
            "aspect_events": [e.to_dict() for e in self.aspect_events],
            "slow_transits_active": self.slow_transits_active,
            "transit_houses": self.transit_houses,
            "current_moon_sign": self.current_moon_sign,
            "current_moon_house": self.current_moon_house,
            "next_moon_sign": self.next_moon_sign,
            "next_moon_ingress_time": self.next_moon_ingress_time,
            "strongest_active_aspect": self.strongest_active_aspect,
        }


# =============================================================================
# ZODIAC HELPERS
# =============================================================================

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

def longitude_to_sign(longitude: float) -> str:
    """Convert longitude to zodiac sign name."""
    longitude = longitude % 360
    if longitude < 0:
        longitude += 360
    return ZODIAC_SIGNS[int(longitude / 30)]


def sign_to_index(sign: str) -> int:
    """Get zodiac sign index (0-11)."""
    return ZODIAC_SIGNS.index(sign)


def get_sign_boundary(sign: str) -> float:
    """Get the starting longitude of a zodiac sign."""
    return sign_to_index(sign) * 30.0


# =============================================================================
# HOUSE CALCULATION HELPERS
# =============================================================================

def normalize_longitude(longitude: float) -> float:
    """Normalize longitude to 0-360 range."""
    longitude = longitude % 360
    if longitude < 0:
        longitude += 360
    return longitude


def longitude_to_house(longitude: float, house_cusps: List[float]) -> int:
    """
    Determine which natal house a transit planet is in.
    
    Uses the Equal house system (30° per house from Ascendant).
    House 1 starts at the Ascendant.
    
    Args:
        longitude: Transit planet's sidereal longitude (0-360)
        house_cusps: List of 12 house cusp longitudes (index 0 = House 1)
    
    Returns:
        House number (1-12)
    """
    longitude = normalize_longitude(longitude)
    
    # Check each house
    for i in range(12):
        cusp_start = normalize_longitude(house_cusps[i])
        cusp_end = normalize_longitude(house_cusps[(i + 1) % 12])
        
        # Handle wrap-around (e.g., House 12 crosses 0°)
        if cusp_start > cusp_end:
            # Wrap-around case
            if longitude >= cusp_start or longitude < cusp_end:
                return i + 1
        else:
            # Normal case
            if cusp_start <= longitude < cusp_end:
                return i + 1
    
    # Fallback (should not happen)
    return 1


def get_current_transit_houses(
    dt: datetime,
    house_cusps: List[float],
    transit_planets: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Get current house positions for all transit planets.
    
    Args:
        dt: Datetime for calculation
        house_cusps: List of 12 house cusp longitudes
        transit_planets: Planets to track (default: Moon, Sun, Mercury, Venus, Mars)
    
    Returns:
        Dict mapping planet names to house numbers (1-12)
    """
    from calculations.sidereal_config import calculate_planet_by_name
    
    if transit_planets is None:
        transit_planets = ["Moon", "Sun", "Mercury", "Venus", "Mars"]
    
    positions = {}
    for planet_name in transit_planets:
        try:
            pos = calculate_planet_by_name(planet_name, dt)
            house = longitude_to_house(pos['longitude'], house_cusps)
            positions[planet_name] = house
        except Exception as e:
            logger.error(f"[HouseCalc] Error for {planet_name}: {e}")
    
    return positions


def find_house_ingress_times(
    start_utc: datetime,
    end_utc: datetime,
    house_cusps: List[float],
    planet_name: str = "Moon",
    interval_minutes: int = 30
) -> List[Dict[str, Any]]:
    """
    Find exact times when a transit planet changes natal houses.
    
    Uses binary search for exact ingress time.
    
    Args:
        start_utc: Start of scan window (UTC)
        end_utc: End of scan window (UTC)
        house_cusps: List of 12 house cusp longitudes
        planet_name: Planet to track (default: Moon)
        interval_minutes: Initial scan interval
    
    Returns:
        List of house ingress events with exact timestamps
    """
    from calculations.sidereal_config import calculate_planet_by_name
    
    ingresses = []
    current_time = start_utc
    
    # Get initial house
    pos = calculate_planet_by_name(planet_name, current_time)
    current_house = longitude_to_house(pos['longitude'], house_cusps)
    
    # Scan at intervals
    while current_time < end_utc:
        next_time = current_time + timedelta(minutes=interval_minutes)
        if next_time > end_utc:
            next_time = end_utc
        
        pos = calculate_planet_by_name(planet_name, next_time)
        next_house = longitude_to_house(pos['longitude'], house_cusps)
        
        if next_house != current_house:
            # House change detected - binary search for exact time
            exact_time = _binary_search_house_ingress(
                current_time, next_time, current_house, house_cusps, planet_name
            )
            
            ingresses.append({
                "timestamp_utc": exact_time,
                "planet": planet_name,
                "from_house": current_house,
                "to_house": next_house,
            })
            
            current_house = next_house
        
        current_time = next_time
    
    return ingresses


def _binary_search_house_ingress(
    start: datetime,
    end: datetime,
    from_house: int,
    house_cusps: List[float],
    planet_name: str,
    precision_minutes: float = 2.0
) -> datetime:
    """Binary search to find exact house ingress time."""
    from calculations.sidereal_config import calculate_planet_by_name
    
    while (end - start).total_seconds() > precision_minutes * 60:
        mid = start + (end - start) / 2
        pos = calculate_planet_by_name(planet_name, mid)
        house = longitude_to_house(pos['longitude'], house_cusps)
        
        if house == from_house:
            start = mid
        else:
            end = mid
    
    return end  # Return the first moment in the new house


def _ordinal(n: int) -> str:
    """Convert number to ordinal string (1st, 2nd, 3rd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return f"{n}{suffix}"


# =============================================================================
# MOON INGRESS DETECTION
# =============================================================================

def find_moon_ingress_times(
    start_utc: datetime,
    end_utc: datetime,
    interval_minutes: int = 15
) -> List[Dict[str, Any]]:
    """
    Find exact times when Moon changes zodiac signs within a time window.
    
    Uses binary search to find exact ingress time (within ~1 minute accuracy).
    
    Args:
        start_utc: Start of scan window (UTC)
        end_utc: End of scan window (UTC)
        interval_minutes: Initial scan interval
    
    Returns:
        List of ingress events with exact timestamps
    """
    from calculations.sidereal_config import calculate_planet_by_name
    
    ingresses = []
    current_time = start_utc
    
    # Get initial Moon sign
    moon_pos = calculate_planet_by_name("Moon", current_time)
    current_sign = moon_pos['sign']
    
    # Scan at intervals
    while current_time < end_utc:
        next_time = current_time + timedelta(minutes=interval_minutes)
        if next_time > end_utc:
            next_time = end_utc
        
        moon_pos = calculate_planet_by_name("Moon", next_time)
        next_sign = moon_pos['sign']
        
        if next_sign != current_sign:
            # Sign change detected - binary search for exact time
            exact_time = _binary_search_ingress(current_time, next_time, current_sign, next_sign)
            
            ingresses.append({
                "timestamp_utc": exact_time,
                "from_sign": current_sign,
                "to_sign": next_sign,
                "moon_longitude": calculate_planet_by_name("Moon", exact_time)['longitude'],
            })
            
            current_sign = next_sign
        
        current_time = next_time
    
    return ingresses


def _binary_search_ingress(
    start: datetime,
    end: datetime,
    from_sign: str,
    to_sign: str,
    precision_minutes: float = 1.0
) -> datetime:
    """Binary search to find exact ingress time."""
    from calculations.sidereal_config import calculate_planet_by_name
    
    while (end - start).total_seconds() > precision_minutes * 60:
        mid = start + (end - start) / 2
        moon_pos = calculate_planet_by_name("Moon", mid)
        
        if moon_pos['sign'] == from_sign:
            start = mid
        else:
            end = mid
    
    return end  # Return the first moment in the new sign


# =============================================================================
# ASPECT EXACTITUDE DETECTION
# =============================================================================

def find_aspect_exact_times(
    natal_planets: Dict[str, Dict[str, Any]],
    start_utc: datetime,
    end_utc: datetime,
    transit_planets: Optional[List[str]] = None,
    interval_minutes: int = 30
) -> List[Dict[str, Any]]:
    """
    Find times when transit-natal aspects reach exact (minimum orb).
    
    Scans the window and tracks orb changes to find local minima.
    
    Args:
        natal_planets: Dict of natal planet data with 'longitude' key
        start_utc: Start of scan window (UTC)
        end_utc: End of scan window (UTC)
        transit_planets: Planets to track (default: Sun, Moon, Mercury, Venus, Mars)
        interval_minutes: Scan interval
    
    Returns:
        List of aspect events when they reach minimum orb
    """
    from calculations.sidereal_config import calculate_planet_by_name
    from services.transit_natal_aspects import check_aspect, ASPECT_CONFIG, AspectType
    
    if transit_planets is None:
        transit_planets = ["Moon", "Sun", "Mercury", "Venus", "Mars"]
    
    exact_events = []
    
    # For each transit-natal pair, track orb across the window
    for transit_name in transit_planets:
        for natal_name, natal_data in natal_planets.items():
            natal_long = natal_data.get('longitude')
            if natal_long is None:
                continue
            
            # Skip same-planet (e.g., Sun-Sun)
            if transit_name == natal_name:
                continue
            
            # Scan and find local orb minima
            orb_history = []
            current_time = start_utc
            
            while current_time <= end_utc:
                transit_pos = calculate_planet_by_name(transit_name, current_time)
                transit_long = transit_pos['longitude']
                
                result = check_aspect(transit_long, natal_long)
                if result:
                    aspect_type, orb, is_applying = result
                    orb_history.append({
                        "time": current_time,
                        "orb": orb,
                        "aspect_type": aspect_type,
                        "transit_long": transit_long,
                        "is_applying": is_applying,
                    })
                
                current_time += timedelta(minutes=interval_minutes)
            
            # Find local minima (exact moments)
            for i in range(1, len(orb_history) - 1):
                prev_orb = orb_history[i-1]['orb']
                curr_orb = orb_history[i]['orb']
                next_orb = orb_history[i+1]['orb']
                
                # Local minimum = aspect reaching exact
                if curr_orb < prev_orb and curr_orb < next_orb:
                    # Refine exact time with binary search
                    exact_time = _refine_aspect_exact_time(
                        orb_history[i-1]['time'],
                        orb_history[i+1]['time'],
                        transit_name,
                        natal_long
                    )
                    
                    exact_events.append({
                        "timestamp_utc": exact_time,
                        "transit_planet": transit_name,
                        "natal_planet": natal_name,
                        "aspect_type": orb_history[i]['aspect_type'].value,
                        "orb_at_peak": orb_history[i]['orb'],
                        "significance": ASPECT_CONFIG[orb_history[i]['aspect_type']]['nature'],
                    })
    
    # Sort by time
    exact_events.sort(key=lambda e: e['timestamp_utc'])
    
    return exact_events


def _refine_aspect_exact_time(
    start: datetime,
    end: datetime,
    transit_name: str,
    natal_long: float,
    precision_minutes: float = 5.0
) -> datetime:
    """Refine exact aspect time using ternary search for minimum orb."""
    from calculations.sidereal_config import calculate_planet_by_name
    from services.transit_natal_aspects import check_aspect
    
    def get_orb(dt: datetime) -> float:
        transit_pos = calculate_planet_by_name(transit_name, dt)
        result = check_aspect(transit_pos['longitude'], natal_long)
        return result[1] if result else 999
    
    # Ternary search for minimum
    while (end - start).total_seconds() > precision_minutes * 60:
        third = (end - start) / 3
        m1 = start + third
        m2 = end - third
        
        if get_orb(m1) < get_orb(m2):
            end = m2
        else:
            start = m1
    
    return start + (end - start) / 2


# =============================================================================
# CURRENT ACTIVE ASPECTS
# =============================================================================

def get_current_active_aspects(
    natal_planets: Dict[str, Dict[str, Any]],
    now: Optional[datetime] = None,
    max_orb_for_active: float = 3.0
) -> List[Dict[str, Any]]:
    """
    Get currently active transit-natal aspects (within tight orb).
    
    "Active" means orb < max_orb_for_active (default 3°).
    Sorted by orb (tightest first).
    """
    from calculations.sidereal_config import calculate_planet_by_name
    from services.transit_natal_aspects import check_aspect, ASPECT_CONFIG
    
    if now is None:
        now = datetime.now(timezone.utc)
    
    transit_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
    active_aspects = []
    
    for transit_name in transit_planets:
        transit_pos = calculate_planet_by_name(transit_name, now)
        transit_long = transit_pos['longitude']
        
        for natal_name, natal_data in natal_planets.items():
            natal_long = natal_data.get('longitude')
            if natal_long is None or transit_name == natal_name:
                continue
            
            result = check_aspect(transit_long, natal_long)
            if result:
                aspect_type, orb, is_applying = result
                
                if orb <= max_orb_for_active:
                    active_aspects.append({
                        "transit_planet": transit_name,
                        "natal_planet": natal_name,
                        "aspect_type": aspect_type.value,
                        "orb": round(orb, 2),
                        "is_applying": is_applying,
                        "significance": ASPECT_CONFIG[aspect_type]['nature'],
                        "description": f"Transit {transit_name} {aspect_type.value} natal {natal_name}",
                    })
    
    # Sort by orb
    active_aspects.sort(key=lambda a: a['orb'])
    
    return active_aspects


# =============================================================================
# MAIN DAILY WINDOW SCANNER
# =============================================================================

def scan_daily_transit_window(
    natal_planets: Dict[str, Dict[str, Any]],
    local_timezone_str: str = "UTC",
    target_date: Optional[datetime] = None,
    house_cusps: Optional[List[float]] = None
) -> DailyTransitWindow:
    """
    Comprehensive daily transit window scan.
    
    Scans the full local day (midnight to midnight) for:
    - Moon sign ingress times
    - Moon/planet house ingress times (if house_cusps provided)
    - Transit-natal aspect exact times
    - Currently active aspects
    
    Args:
        natal_planets: Dict of natal planet data with 'longitude' key
        local_timezone_str: User's local timezone (e.g., "Asia/Singapore", "America/New_York")
        target_date: Date to scan (default: today in local timezone)
        house_cusps: Optional list of 12 house cusp longitudes for house tracking
    
    Returns:
        DailyTransitWindow with all events categorized
    """
    from calculations.sidereal_config import calculate_planet_by_name
    
    # Set up timezone
    try:
        local_tz = pytz.timezone(local_timezone_str)
    except:
        logger.warning(f"[DailyWindow] Unknown timezone {local_timezone_str}, using UTC")
        local_tz = pytz.UTC
        local_timezone_str = "UTC"
    
    # Get current time
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(local_tz)
    
    # Determine scan window (local day midnight to midnight)
    if target_date is None:
        target_date = now_local.date()
    else:
        target_date = target_date.date() if isinstance(target_date, datetime) else target_date
    
    day_start_local = local_tz.localize(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
    day_end_local = day_start_local + timedelta(days=1)
    
    scan_start_utc = day_start_local.astimezone(timezone.utc)
    scan_end_utc = day_end_local.astimezone(timezone.utc)
    
    logger.info(f"[DailyWindow] Scanning {target_date} in {local_timezone_str}")
    
    # Initialize result
    result = DailyTransitWindow(
        date=str(target_date),
        local_timezone=local_timezone_str,
        scan_start_utc=scan_start_utc,
        scan_end_utc=scan_end_utc,
        computed_at=now_utc,
    )
    
    # Get current Moon position
    moon_now = calculate_planet_by_name("Moon", now_utc)
    result.current_moon_sign = moon_now['sign']
    
    # =================================================================
    # HOUSE TRACKING (if house_cusps provided)
    # =================================================================
    if house_cusps and len(house_cusps) >= 12:
        # Get current house positions for all transit planets
        result.transit_houses = get_current_transit_houses(now_utc, house_cusps)
        result.current_moon_house = result.transit_houses.get("Moon", 0)
        
        logger.info(f"[DailyWindow] Transit houses: {result.transit_houses}")
        
        # Scan for Moon house ingresses (Moon changes houses more than signs in a day)
        moon_house_ingresses = find_house_ingress_times(
            scan_start_utc, scan_end_utc, house_cusps, "Moon", interval_minutes=30
        )
        
        for ingress in moon_house_ingresses:
            timestamp_utc = ingress['timestamp_utc']
            timestamp_local = timestamp_utc.astimezone(local_tz)
            minutes_from_now = int((timestamp_utc - now_utc).total_seconds() / 60)
            
            if minutes_from_now < -60:
                timing = EventTiming.PASSED
            elif minutes_from_now < 60:
                timing = EventTiming.CURRENT
            else:
                timing = EventTiming.UPCOMING
            
            event = TransitEvent(
                event_type=TransitEventType.HOUSE_INGRESS,
                timestamp_utc=timestamp_utc,
                timestamp_local=timestamp_local,
                local_timezone=local_timezone_str,
                description=f"Moon enters {_ordinal(ingress['to_house'])} house",
                significance="moderate",
                timing=timing,
                minutes_from_now=minutes_from_now,
                transit_planet="Moon",
                from_house=ingress['from_house'],
                to_house=ingress['to_house'],
            )
            
            result.house_ingresses.append(event)
            result.all_events.append(event)
    
    # =================================================================
    # SCAN 1: Moon Ingresses (faster interval - Moon moves quickly)
    # =================================================================
    moon_ingresses = find_moon_ingress_times(scan_start_utc, scan_end_utc, interval_minutes=30)
    
    for ingress in moon_ingresses:
        timestamp_utc = ingress['timestamp_utc']
        timestamp_local = timestamp_utc.astimezone(local_tz)
        minutes_from_now = int((timestamp_utc - now_utc).total_seconds() / 60)
        
        # Determine timing
        if minutes_from_now < -60:
            timing = EventTiming.PASSED
        elif minutes_from_now < 60:
            timing = EventTiming.CURRENT
        else:
            timing = EventTiming.UPCOMING
        
        event = TransitEvent(
            event_type=TransitEventType.MOON_INGRESS,
            timestamp_utc=timestamp_utc,
            timestamp_local=timestamp_local,
            local_timezone=local_timezone_str,
            description=f"Moon enters {ingress['to_sign']}",
            significance="major",  # Moon ingress is always major for daily planning
            timing=timing,
            minutes_from_now=minutes_from_now,
            from_sign=ingress['from_sign'],
            to_sign=ingress['to_sign'],
        )
        
        result.moon_ingresses.append(event)
        result.all_events.append(event)
        
        # Track next ingress
        if timing == EventTiming.UPCOMING and result.next_moon_sign == "":
            result.next_moon_sign = ingress['to_sign']
            result.next_moon_ingress_time = timestamp_local.strftime("%I:%M %p")
    
    # =================================================================
    # SCAN 2: Aspect Exact Times (Moon, Sun, Mercury, Venus, Mars)
    # =================================================================
    aspect_exacts = find_aspect_exact_times(
        natal_planets,
        scan_start_utc,
        scan_end_utc,
        transit_planets=["Moon", "Sun", "Mercury", "Venus", "Mars"],
        interval_minutes=60  # Hourly scan for speed
    )
    
    for aspect in aspect_exacts:
        timestamp_utc = aspect['timestamp_utc']
        timestamp_local = timestamp_utc.astimezone(local_tz)
        minutes_from_now = int((timestamp_utc - now_utc).total_seconds() / 60)
        
        if minutes_from_now < -60:
            timing = EventTiming.PASSED
        elif minutes_from_now < 60:
            timing = EventTiming.CURRENT
        else:
            timing = EventTiming.UPCOMING
        
        event = TransitEvent(
            event_type=TransitEventType.ASPECT_EXACT,
            timestamp_utc=timestamp_utc,
            timestamp_local=timestamp_local,
            local_timezone=local_timezone_str,
            description=f"Transit {aspect['transit_planet']} {aspect['aspect_type']} natal {aspect['natal_planet']}",
            significance=aspect['significance'],
            timing=timing,
            minutes_from_now=minutes_from_now,
            transit_planet=aspect['transit_planet'],
            natal_planet=aspect['natal_planet'],
            aspect_type=aspect['aspect_type'],
            orb_at_peak=aspect['orb_at_peak'],
        )
        
        result.aspect_events.append(event)
        result.all_events.append(event)
    
    # =================================================================
    # CURRENT ACTIVE ASPECTS (snapshot, not scan)
    # =================================================================
    active_aspects = get_current_active_aspects(natal_planets, now_utc, max_orb_for_active=3.0)
    if active_aspects:
        result.strongest_active_aspect = active_aspects[0]
    
    # =================================================================
    # IDENTIFY SLOW-MOVING TRANSITS (Mercury, Venus, Mars)
    # These don't reach exact within a day but are still active
    # =================================================================
    timed_transit_planets = set(e.transit_planet for e in result.aspect_events if e.transit_planet)
    slow_transit_names = ["Mercury", "Venus", "Mars"]
    
    for aspect in active_aspects:
        transit_planet = aspect['transit_planet']
        # If this planet has NO timed events but IS in active aspects, it's a slow transit
        if transit_planet in slow_transit_names and transit_planet not in timed_transit_planets:
            result.slow_transits_active.append({
                "transit_planet": aspect['transit_planet'],
                "natal_planet": aspect['natal_planet'],
                "aspect_type": aspect['aspect_type'],
                "orb": aspect['orb'],
                "description": aspect['description'],
                "note": "Active all day (slow-moving transit)",
            })
    
    # Sort all events by time
    result.all_events.sort(key=lambda e: e.timestamp_utc)
    
    logger.info(f"[DailyWindow] Found {len(result.all_events)} events")
    
    return result


# =============================================================================
# DAILY THEME BUILDER
# =============================================================================

def build_daily_theme_from_events(
    window: DailyTransitWindow,
    natal_planets: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build a concise daily theme layer from actual transit events.
    
    Returns:
    - primary_theme: Main energy/focus for the day
    - moon_context: Current and upcoming Moon sign context
    - active_aspects: Currently tight aspects
    - upcoming_events: What's happening later today
    - theme_keywords: Key themes for the day
    """
    from calculations.sidereal_config import calculate_planet_by_name
    
    now_utc = datetime.now(timezone.utc)
    
    # Get current positions
    sun = calculate_planet_by_name("Sun", now_utc)
    moon = calculate_planet_by_name("Moon", now_utc)
    
    # Build theme
    theme = {
        "primary_theme": "",
        "moon_context": {
            "current_sign": window.current_moon_sign,
            "next_sign": window.next_moon_sign if window.next_moon_sign else None,
            "ingress_time": window.next_moon_ingress_time,
        },
        "sun_context": {
            "sign": sun['sign'],
            "degree": round(sun['degree'], 1),
        },
        "active_aspects": [],
        "upcoming_events": [],
        "passed_events": [],
        "theme_keywords": [],
    }
    
    # Categorize events
    for event in window.all_events:
        if event.timing == EventTiming.CURRENT:
            if event.event_type == TransitEventType.ASPECT_EXACT:
                theme["active_aspects"].append({
                    "description": event.description,
                    "orb": event.orb_at_peak,
                    "significance": event.significance,
                })
        elif event.timing == EventTiming.UPCOMING:
            theme["upcoming_events"].append({
                "time": event.timestamp_local.strftime("%I:%M %p"),
                "description": event.description,
                "event_type": event.event_type.value,
                "minutes_away": event.minutes_from_now,
            })
        elif event.timing == EventTiming.PASSED:
            theme["passed_events"].append({
                "time": event.timestamp_local.strftime("%I:%M %p"),
                "description": event.description,
            })
    
    # Build primary theme
    if window.strongest_active_aspect:
        strongest = window.strongest_active_aspect
        theme["primary_theme"] = f"{strongest['transit_planet']}-{strongest['natal_planet']} {strongest['aspect_type']}"
        theme["theme_keywords"].append(strongest['aspect_type'])
    
    # Add Moon themes
    moon_themes = {
        "Aries": ["initiative", "action", "impulse"],
        "Taurus": ["stability", "comfort", "grounding"],
        "Gemini": ["communication", "curiosity", "flexibility"],
        "Cancer": ["nurturing", "emotion", "home"],
        "Leo": ["expression", "creativity", "recognition"],
        "Virgo": ["analysis", "refinement", "service"],
        "Libra": ["balance", "relationship", "harmony"],
        "Scorpio": ["depth", "transformation", "intensity"],
        "Sagittarius": ["expansion", "meaning", "freedom"],
        "Capricorn": ["structure", "responsibility", "achievement"],
        "Aquarius": ["innovation", "community", "detachment"],
        "Pisces": ["intuition", "dissolution", "compassion"],
    }
    
    if window.current_moon_sign in moon_themes:
        theme["theme_keywords"].extend(moon_themes[window.current_moon_sign][:2])
    
    return theme


# =============================================================================
# DEBUG HELPER
# =============================================================================

def debug_daily_window(
    natal_planets: Dict[str, Dict[str, Any]],
    local_timezone_str: str = "Asia/Singapore"
) -> None:
    """Debug helper to print daily window scan results."""
    print(f"\n{'='*70}")
    print(f"DAILY TRANSIT WINDOW SCAN")
    print(f"{'='*70}")
    
    window = scan_daily_transit_window(natal_planets, local_timezone_str)
    
    print(f"Date: {window.date} ({window.local_timezone})")
    print(f"Current Moon: {window.current_moon_sign}")
    print(f"Next Moon Sign: {window.next_moon_sign or 'N/A'}")
    if window.next_moon_ingress_time:
        print(f"Next Ingress: {window.next_moon_ingress_time}")
    print()
    
    print(f"MOON INGRESSES ({len(window.moon_ingresses)}):")
    for event in window.moon_ingresses:
        print(f"  [{event.timing.value:8}] {event.timestamp_local.strftime('%I:%M %p')} - {event.description}")
    print()
    
    print(f"ASPECT EVENTS ({len(window.aspect_events)}):")
    for event in window.aspect_events:
        sig = "★" if event.significance == "major" else " "
        print(f"  {sig}[{event.timing.value:8}] {event.timestamp_local.strftime('%I:%M %p')} - {event.description} (orb: {event.orb_at_peak:.2f}°)")
    print()
    
    if window.strongest_active_aspect:
        print(f"STRONGEST ACTIVE ASPECT:")
        asp = window.strongest_active_aspect
        print(f"  {asp['description']} (orb: {asp['orb']}°)")
    print()
    
    # Build theme
    theme = build_daily_theme_from_events(window, natal_planets)
    print(f"DAILY THEME:")
    print(f"  Primary: {theme['primary_theme'] or 'General'}")
    print(f"  Keywords: {', '.join(theme['theme_keywords'])}")
    print(f"  Upcoming: {len(theme['upcoming_events'])} events")
