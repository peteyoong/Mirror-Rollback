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
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta, timezone as dt_timezone

# Optional: IANA timezone support (requires pytz)
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False


def normalize_birth_time(time_str: str) -> Tuple[bool, str, str]:
    """Normalize various birth time formats to HH:MM 24-hour format.
    
    Accepts:
    - "1:25am", "1:25 am", "1:25AM", "1:25 AM"
    - "1:25pm", "1:25 pm", "1:25PM", "1:25 PM"
    - "01:25", "1:25" (assumed 24h format)
    - "13:25" (24h format)
    
    Returns:
        Tuple of (success, normalized_time, error_message)
        - success: True if parsing succeeded
        - normalized_time: "HH:MM" format or empty string if failed
        - error_message: Error description or empty if success
    """
    if not time_str:
        return (False, "", "Birth time is required")
    
    time_str = time_str.strip().lower()
    
    # Pattern 1: 12-hour format with AM/PM
    # Matches: "1:25am", "1:25 am", "01:25am", "12:30pm"
    ampm_pattern = r'^(\d{1,2}):(\d{2})\s*(am|pm)$'
    ampm_match = re.match(ampm_pattern, time_str)
    
    if ampm_match:
        hour = int(ampm_match.group(1))
        minute = int(ampm_match.group(2))
        period = ampm_match.group(3)
        
        # Validate 12-hour range
        if hour < 1 or hour > 12:
            return (False, "", f"Invalid hour for 12-hour format: {hour}. Must be 1-12.")
        if minute > 59:
            return (False, "", f"Invalid minute: {minute}. Must be 0-59.")
        
        # Convert to 24-hour
        if period == 'am':
            if hour == 12:
                hour = 0  # 12:xx AM = 00:xx
        else:  # pm
            if hour != 12:
                hour += 12  # 1:xx PM = 13:xx, but 12:xx PM stays 12:xx
        
        return (True, f"{hour:02d}:{minute:02d}", "")
    
    # Pattern 2: 24-hour format (or ambiguous)
    # Matches: "01:25", "1:25", "13:25", "23:59"
    h24_pattern = r'^(\d{1,2}):(\d{2})$'
    h24_match = re.match(h24_pattern, time_str)
    
    if h24_match:
        hour = int(h24_match.group(1))
        minute = int(h24_match.group(2))
        
        # Validate 24-hour range
        if hour > 23:
            return (False, "", f"Invalid hour: {hour}. Must be 0-23.")
        if minute > 59:
            return (False, "", f"Invalid minute: {minute}. Must be 0-59.")
        
        return (True, f"{hour:02d}:{minute:02d}", "")
    
    # No pattern matched
    return (False, "", f"Could not parse birth time: '{time_str}'. Expected formats: 'HH:MM', 'H:MMam', 'H:MM PM'")


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


def resolve_iana_offset_at_datetime(tz_name: str, local_dt: datetime) -> Tuple[int, str]:
    """Resolve IANA timezone to offset at a specific datetime.
    
    Handles historical timezone changes and DST automatically.
    
    Args:
        tz_name: IANA timezone name (e.g., "Asia/Kuala_Lumpur")
        local_dt: The local datetime for which to resolve the offset
    
    Returns:
        Tuple of (offset_minutes, formatted_offset_string)
        
    Example:
        - "Asia/Kuala_Lumpur" at 1968-04-01 -> (+07:30, "+07:30")
        - "Asia/Kuala_Lumpur" at 1982-01-01 -> (+08:00, "+08:00")
    """
    if not HAS_PYTZ:
        raise ValueError(
            f"IANA timezone '{tz_name}' requires pytz library. "
            f"Install pytz or use offset format (e.g., '+08:00')."
        )
    
    try:
        tz = pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Unknown IANA timezone: '{tz_name}'")
    
    # Localize the datetime to get the correct offset for that specific date
    try:
        localized_dt = tz.localize(local_dt, is_dst=None)
    except pytz.exceptions.AmbiguousTimeError:
        # DST transition - assume standard time
        localized_dt = tz.localize(local_dt, is_dst=False)
    except pytz.exceptions.NonExistentTimeError:
        # Time doesn't exist (DST spring forward) - use next valid time
        localized_dt = tz.localize(local_dt, is_dst=True)
    
    offset = localized_dt.utcoffset()
    if offset is None:
        raise ValueError(f"Could not determine offset for '{tz_name}' at {local_dt}")
    
    total_minutes = int(offset.total_seconds() / 60)
    
    # Format as +HH:MM or -HH:MM
    sign = '+' if total_minutes >= 0 else '-'
    abs_minutes = abs(total_minutes)
    hours = abs_minutes // 60
    mins = abs_minutes % 60
    formatted = f"{sign}{hours:02d}:{mins:02d}"
    
    return (total_minutes, formatted)


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
        birth_time_str: Time in "HH:MM" format (or various formats - will be normalized)
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
    
    # Normalize birth time (handles various formats)
    success, normalized_time, error_msg = normalize_birth_time(birth_time_str)
    if not success:
        raise ValueError(f"BIRTH_TIME_PARSE_FAILED: {error_msg}")
    
    # Parse normalized time
    hour, minute = map(int, normalized_time.split(':'))
    
    # Combine date and time
    local_dt = birth_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Parse timezone - handle IANA with historical offset resolution
    timezone_str = timezone_str.strip() if timezone_str else ""
    
    if not timezone_str:
        raise ValueError(
            "Timezone is required. Please provide a timezone offset "
            "(e.g., '+07:30') or IANA timezone (e.g., 'Asia/Kuala_Lumpur')."
        )
    
    # Check if IANA format
    is_iana = '/' in timezone_str or timezone_str in ('UTC', 'GMT')
    
    if is_iana and timezone_str not in ('UTC', 'GMT'):
        # Use historical offset resolution for IANA timezones
        parsed_timezone_minutes, resolved_offset_str = resolve_iana_offset_at_datetime(
            timezone_str, local_dt
        )
        input_timezone_raw = timezone_str  # Store IANA name
    else:
        # Use standard offset parsing
        input_timezone_raw, parsed_timezone_minutes = parse_timezone(timezone_str)
    
    # Convert to UTC
    birth_utc = local_to_utc(local_dt, parsed_timezone_minutes)
    
    # Format as ISO string
    resolved_birth_utc_iso = format_utc_iso(birth_utc)
    
    return (birth_utc, resolved_birth_utc_iso, parsed_timezone_minutes, input_timezone_raw)


def resolve_birth_utc_with_debug(
    birth_date_str: str,
    birth_time_str: str,
    timezone_str: str
) -> Dict[str, Any]:
    """Resolve birth datetime to UTC with comprehensive debug stamp.
    
    Returns a dictionary with all resolution details for debugging.
    
    Args:
        birth_date_str: Date in "YYYY-MM-DD" format
        birth_time_str: Time in various formats (will be normalized)
        timezone_str: Timezone in offset or IANA format
    
    Returns:
        Dict with:
        - success: bool
        - error: str or None
        - birth_utc: datetime (if success)
        - debug_stamp: dict with all resolution details
    """
    debug_stamp = {
        "input_date": birth_date_str,
        "input_time_raw": birth_time_str,
        "input_timezone_raw": timezone_str,
    }
    
    # Step 1: Normalize birth time
    success, normalized_time, error_msg = normalize_birth_time(birth_time_str)
    debug_stamp["time_normalized"] = normalized_time if success else None
    debug_stamp["time_parse_success"] = success
    
    if not success:
        debug_stamp["time_parse_error"] = error_msg
        return {
            "success": False,
            "error": "BIRTH_TIME_PARSE_FAILED",
            "error_message": error_msg,
            "birth_utc": None,
            "debug_stamp": debug_stamp
        }
    
    # Step 2: Parse date
    try:
        birth_date = datetime.strptime(birth_date_str.strip(), "%Y-%m-%d")
        debug_stamp["date_parse_success"] = True
    except (ValueError, AttributeError) as e:
        debug_stamp["date_parse_success"] = False
        debug_stamp["date_parse_error"] = str(e)
        return {
            "success": False,
            "error": "BIRTH_DATE_PARSE_FAILED",
            "error_message": str(e),
            "birth_utc": None,
            "debug_stamp": debug_stamp
        }
    
    # Step 3: Build local datetime
    hour, minute = map(int, normalized_time.split(':'))
    local_dt = birth_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    debug_stamp["local_datetime"] = local_dt.isoformat()
    
    # Step 4: Resolve timezone
    timezone_str = (timezone_str or "").strip()
    if not timezone_str:
        return {
            "success": False,
            "error": "TIMEZONE_MISSING",
            "error_message": "Timezone is required",
            "birth_utc": None,
            "debug_stamp": debug_stamp
        }
    
    is_iana = '/' in timezone_str or timezone_str in ('UTC', 'GMT')
    debug_stamp["timezone_is_iana"] = is_iana
    
    try:
        if is_iana and timezone_str not in ('UTC', 'GMT'):
            # IANA timezone with historical resolution
            offset_minutes, resolved_offset_str = resolve_iana_offset_at_datetime(
                timezone_str, local_dt
            )
            debug_stamp["timezone_iana"] = timezone_str
            debug_stamp["resolved_utc_offset_at_birth"] = resolved_offset_str
            debug_stamp["resolved_offset_minutes"] = offset_minutes
        else:
            # Offset format or UTC/GMT
            _, offset_minutes = parse_timezone(timezone_str)
            debug_stamp["timezone_iana"] = None
            # Format offset
            sign = '+' if offset_minutes >= 0 else '-'
            abs_min = abs(offset_minutes)
            resolved_offset_str = f"{sign}{abs_min // 60:02d}:{abs_min % 60:02d}"
            debug_stamp["resolved_utc_offset_at_birth"] = resolved_offset_str
            debug_stamp["resolved_offset_minutes"] = offset_minutes
        
        debug_stamp["timezone_parse_success"] = True
        
    except ValueError as e:
        debug_stamp["timezone_parse_success"] = False
        debug_stamp["timezone_parse_error"] = str(e)
        return {
            "success": False,
            "error": "TIMEZONE_PARSE_FAILED",
            "error_message": str(e),
            "birth_utc": None,
            "debug_stamp": debug_stamp
        }
    
    # Step 5: Convert to UTC
    birth_utc = local_to_utc(local_dt, offset_minutes)
    debug_stamp["datetime_utc"] = birth_utc.isoformat() + "Z"
    debug_stamp["datetime_utc_iso"] = format_utc_iso(birth_utc)
    
    return {
        "success": True,
        "error": None,
        "birth_utc": birth_utc,
        "debug_stamp": debug_stamp
    }
