"""Timezone utilities for proper UTC conversion

===============================================================================
DETERMINISTIC COMPUTATION CORE - FROZEN
===============================================================================
This file is part of Project Mirror's deterministic computation core.
Outputs must remain stable across versions.
Do NOT modify without updating regression tests and bumping computation_version.

Current version: mirror-deterministic-v1
===============================================================================

Project Mirror requires accurate timezone handling for birth datetime inputs.
This module provides parsing and conversion utilities.
"""
import re
from typing import Tuple, Optional
from datetime import datetime, timedelta, timezone as dt_timezone

# Optional: IANA timezone support (requires pytz)
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False


def parse_timezone_offset(tz_string: str) -> Tuple[str, int]:
    """Parse offset-format timezone string to minutes
    
    Accepts:
    - "+07:30" -> 450
    - "+08:00" -> 480
    - "-05:00" -> -300
    - "+00:00" -> 0
    
    Args:
        tz_string: Timezone offset string in +HH:MM or -HH:MM format
    
    Returns:
        Tuple of (original_string, minutes_offset)
    
    Raises:
        ValueError: If format is invalid
    """
    # Strict offset pattern: +/-HH:MM
    offset_pattern = r'^([+-])(\d{2}):(\d{2})$'
    match = re.match(offset_pattern, tz_string.strip())
    
    if not match:
        raise ValueError(
            f"Invalid timezone offset format: '{tz_string}'. "
            f"Expected format: '+07:30' or '-05:00'"
        )
    
    sign, hours_str, minutes_str = match.groups()
    hours = int(hours_str)
    minutes = int(minutes_str)
    
    # Validate ranges
    if hours > 14:  # Max offset is +14:00 (Line Islands)
        raise ValueError(f"Invalid timezone hours: {hours}. Maximum is 14.")
    if minutes > 59:
        raise ValueError(f"Invalid timezone minutes: {minutes}. Maximum is 59.")
    if hours == 14 and minutes > 0:
        raise ValueError(f"Invalid timezone offset: +14:{minutes_str}. Maximum is +14:00.")
    
    total_minutes = hours * 60 + minutes
    if sign == '-':
        total_minutes = -total_minutes
    
    return (tz_string.strip(), total_minutes)


def parse_iana_timezone(tz_string: str) -> Tuple[str, int]:
    """Parse IANA timezone name to offset at current time
    
    Note: IANA offsets vary by date due to DST. This returns the
    standard offset, not accounting for DST at birth time.
    For precise DST handling, use local_to_utc_with_iana().
    
    Args:
        tz_string: IANA timezone name (e.g., "Asia/Kuala_Lumpur")
    
    Returns:
        Tuple of (original_string, standard_offset_minutes)
    
    Raises:
        ValueError: If timezone name is invalid or pytz not available
    """
    if not HAS_PYTZ:
        raise ValueError(
            f"IANA timezone '{tz_string}' requires pytz library. "
            f"Please use offset format instead (e.g., '+08:00')"
        )
    
    try:
        tz = pytz.timezone(tz_string)
        # Get standard offset (not DST-adjusted)
        # Use January 1 of a non-DST period to get standard time
        sample_dt = datetime(2000, 1, 15, 12, 0, 0)
        offset = tz.utcoffset(sample_dt)
        if offset is None:
            raise ValueError(f"Could not determine offset for '{tz_string}'")
        
        total_minutes = int(offset.total_seconds() / 60)
        return (tz_string, total_minutes)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Unknown IANA timezone: '{tz_string}'")


def parse_timezone(tz_string: str) -> Tuple[str, int]:
    """Parse timezone string (offset or IANA) to minutes offset
    
    Accepts:
    A) Offset format: "+07:30", "+08:00", "-05:00"
    B) IANA format: "Asia/Kuala_Lumpur" (if pytz available)
    
    Args:
        tz_string: Timezone string in either format
    
    Returns:
        Tuple of (original_string, parsed_timezone_minutes)
    
    Raises:
        ValueError: If timezone is missing, empty, or invalid
    """
    if not tz_string:
        raise ValueError(
            "Timezone is required. Please provide a timezone offset "
            "(e.g., '+07:30') or IANA timezone (e.g., 'Asia/Kuala_Lumpur')."
        )
    
    tz_string = tz_string.strip()
    
    if not tz_string:
        raise ValueError("Timezone cannot be empty.")
    
    # Try offset format first (most common and doesn't require pytz)
    if tz_string.startswith('+') or tz_string.startswith('-'):
        return parse_timezone_offset(tz_string)
    
    # Try IANA format
    if '/' in tz_string or tz_string in ('UTC', 'GMT'):
        if tz_string in ('UTC', 'GMT'):
            return (tz_string, 0)
        return parse_iana_timezone(tz_string)
    
    raise ValueError(
        f"Invalid timezone format: '{tz_string}'. "
        f"Use offset format (e.g., '+07:30') or IANA name (e.g., 'Asia/Kuala_Lumpur')."
    )


def local_to_utc(local_dt: datetime, timezone_minutes: int) -> datetime:
    """Convert local datetime to UTC
    
    Formula: UTC = local_time - timezone_offset
    
    Example:
    - Local: 1981-07-13 07:25 in +07:30
    - Offset: +07:30 = 450 minutes
    - UTC: 07:25 - 7h30m = 1981-07-12 23:55
    
    Args:
        local_dt: Naive datetime representing local time
        timezone_minutes: Offset in minutes (positive = east of UTC)
    
    Returns:
        UTC datetime (naive, but represents UTC)
    """
    utc_dt = local_dt - timedelta(minutes=timezone_minutes)
    return utc_dt


def format_utc_iso(utc_dt: datetime) -> str:
    """Format UTC datetime as ISO string with trailing Z
    
    Output format: "YYYY-MM-DDTHH:MM:SSZ"
    Always includes seconds (":00" if not present)
    
    Args:
        utc_dt: UTC datetime
    
    Returns:
        ISO formatted string with Z suffix
    """
    # Ensure we have seconds
    if utc_dt.second == 0 and utc_dt.microsecond == 0:
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    else:
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def resolve_birth_utc(
    birth_date_str: str,
    birth_time_str: str,
    timezone_str: str
) -> Tuple[datetime, str, int, str]:
    """Resolve birth datetime to UTC with full debug info
    
    Args:
        birth_date_str: Date in "YYYY-MM-DD" format
        birth_time_str: Time in "HH:MM" format
        timezone_str: Timezone in offset ("+07:30") or IANA format
    
    Returns:
        Tuple of:
        - birth_utc: datetime object in UTC
        - resolved_birth_utc_iso: ISO string with Z suffix
        - parsed_timezone_minutes: integer offset
        - input_timezone_raw: original timezone string
    
    Raises:
        ValueError: If any input is invalid or missing
    """
    # Validate date
    if not birth_date_str:
        raise ValueError("Birth date is required.")
    
    try:
        birth_date = datetime.strptime(birth_date_str.strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid birth date format: '{birth_date_str}'. "
            f"Expected format: 'YYYY-MM-DD'"
        )
    
    # Validate time
    if not birth_time_str:
        raise ValueError("Birth time is required.")
    
    birth_time_str = birth_time_str.strip()
    time_pattern = r'^(\d{1,2}):(\d{2})$'
    time_match = re.match(time_pattern, birth_time_str)
    
    if not time_match:
        raise ValueError(
            f"Invalid birth time format: '{birth_time_str}'. "
            f"Expected format: 'HH:MM'"
        )
    
    hour = int(time_match.group(1))
    minute = int(time_match.group(2))
    
    if hour < 0 or hour > 23:
        raise ValueError(f"Invalid hour: {hour}. Must be 0-23.")
    if minute < 0 or minute > 59:
        raise ValueError(f"Invalid minute: {minute}. Must be 0-59.")
    
    # Combine date and time
    local_dt = birth_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Parse timezone
    input_timezone_raw, parsed_timezone_minutes = parse_timezone(timezone_str)
    
    # Convert to UTC
    birth_utc = local_to_utc(local_dt, parsed_timezone_minutes)
    
    # Format as ISO string
    resolved_birth_utc_iso = format_utc_iso(birth_utc)
    
    return (birth_utc, resolved_birth_utc_iso, parsed_timezone_minutes, input_timezone_raw)
