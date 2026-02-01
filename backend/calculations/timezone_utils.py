"""Timezone utilities for proper UTC conversion"""
import re
from typing import Tuple
from datetime import datetime, timedelta

def parse_timezone(tz_string: str) -> Tuple[str, int]:
    """Parse timezone string to (raw_string, minutes_offset)
    
    Accepts:
    - Offset format: "+07:30", "-05:00"
    
    Returns:
    - (timezone_raw, parsed_timezone_minutes)
    
    Raises:
    - ValueError if timezone is not parseable
    """
    # Try offset format: +HH:MM or -HH:MM
    offset_pattern = r'^([+-])(\d{2}):(\d{2})$'
    match = re.match(offset_pattern, tz_string)
    
    if match:
        sign, hours, minutes = match.groups()
        total_minutes = int(hours) * 60 + int(minutes)
        if sign == '-':
            total_minutes = -total_minutes
        return (tz_string, total_minutes)
    
    raise ValueError(f"Timezone '{tz_string}' not parseable. Use format '+07:30' or '-05:00'")

def local_to_utc(local_dt: datetime, timezone_minutes: int) -> datetime:
    """Convert local datetime to UTC
    
    Args:
        local_dt: Local datetime
        timezone_minutes: Offset in minutes (positive for east of UTC)
    
    Returns:
        UTC datetime
    """
    # UTC = local - offset
    utc_dt = local_dt - timedelta(minutes=timezone_minutes)
    return utc_dt
