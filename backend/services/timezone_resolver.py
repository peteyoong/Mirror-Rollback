"""
Coordinates → IANA timezone resolver.
Used by user onboarding (server.py) and admin audit routes.

Phase 1 of timezone-integrity remediation. Read-only resolver — never
writes to the DB. Replaces the legacy `estimate_timezone(longitude)`
approximation (longitude/15) which was incorrect for any country whose
political timezone does not follow its meridian (Argentina, India,
China, Newfoundland, etc.).
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone as dt_timezone
from typing import Optional, Tuple

logger = logging.getLogger("timezone_resolver")

# Bump on any change to resolution semantics (DB-recorded provenance).
TIMEZONE_RESOLVER_VERSION = "1.0.0"

_tf = None

def _get_finder():
    global _tf
    if _tf is None:
        from timezonefinder import TimezoneFinder
        _tf = TimezoneFinder()
    return _tf


def resolve_iana_timezone(latitude: Optional[float],
                          longitude: Optional[float]) -> Optional[str]:
    """Return the IANA timezone name (e.g. 'America/Argentina/Buenos_Aires')
    for the given coordinates, or None if it cannot be resolved."""
    if latitude is None or longitude is None:
        return None
    try:
        lat = float(latitude); lon = float(longitude)
    except (TypeError, ValueError):
        return None
    try:
        tz = _get_finder().timezone_at(lat=lat, lng=lon)
        if tz is None:
            tz = _get_finder().closest_timezone_at(lat=lat, lng=lon)
        return tz
    except Exception as e:  # noqa: BLE001
        logger.warning("[timezone_resolver] resolve failed lat=%s lon=%s err=%s",
                       latitude, longitude, e)
        return None


def is_iana_name(tz_value: Optional[str]) -> bool:
    """True if the value looks like an IANA name ('Region/City'), not a
    fixed offset like '+08:00' / 'UTC'."""
    if not tz_value or not isinstance(tz_value, str):
        return False
    if tz_value.startswith(("+", "-")):
        return False
    if tz_value.upper() in ("UTC", "GMT", "Z"):
        return False
    return "/" in tz_value


def build_timezone_provenance(latitude: Optional[float],
                              longitude: Optional[float]) -> Tuple[Optional[str], dict]:
    """Convenience for onboarding: returns (iana_tz, provenance_dict) where
    provenance_dict carries the metadata to merge into the user record."""
    tz = resolve_iana_timezone(latitude, longitude)
    now_iso = datetime.now(dt_timezone.utc).isoformat()
    if tz:
        prov = {
            "timezone":                  tz,
            "timezone_source":           "coordinates",
            "timezone_resolved_at":      now_iso,
            "timezone_resolver_version": TIMEZONE_RESOLVER_VERSION,
        }
        logger.info("[TimezoneResolver] resolved lat=%s lon=%s -> %s",
                    latitude, longitude, tz)
    else:
        prov = {
            "timezone":                  None,
            "timezone_source":           "unresolved",
            "timezone_resolved_at":      now_iso,
            "timezone_resolver_version": TIMEZONE_RESOLVER_VERSION,
        }
        logger.warning("[TimezoneResolver] could not resolve lat=%s lon=%s",
                       latitude, longitude)
    return tz, prov
