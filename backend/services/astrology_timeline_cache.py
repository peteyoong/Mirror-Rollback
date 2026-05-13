"""
Astrology Timeline Cache — weekly refresh policy
=================================================

The astrology timeline is a YEARLY ARC. It should feel stable and
trustworthy — not rewrite itself on every chat turn or page load.

Refresh policy
--------------
Cached payload is returned UNCHANGED for up to 7 days unless one of the
following invalidation triggers fires:

  1. ``force_refresh=True`` is passed in by the caller (manual refresh,
     admin/debug, or explicit user action).
  2. The user's `birth_data_hash` has changed (birth date, time, or
     location was edited).
  3. The engine version has been bumped
     (`astrology_timeline_generator.ENGINE_VERSION` constant).
  4. The current calendar year has rolled over (new yearly arc needed).
  5. No cached payload exists yet for this user.

Cache key
---------
``astrology_timeline::{user_id}::{year}::{engine_version}``

Storage
-------
Persisted in MongoDB at ``db.astrology_timeline_cache`` so timelines
survive backend restarts. (The legacy in-memory ``_LIFE_SYNTH_CACHE``
loses everything on restart, which violated the "stable across the
week" product rule.)

Lookup contract
---------------
``get_or_build_astrology_timeline(db, user_id, chart_doc, force_refresh=False)``
returns the timeline payload PLUS a small ``_cache_meta`` envelope so
callers can render staleness UI and reason about why a refresh
happened.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from services.astrology_timeline_generator import (
    ENGINE_VERSION,
    generate_astrology_timeline,
)

logger = logging.getLogger(__name__)


# Weekly TTL — payloads older than this are regenerated even if all
# other invariants (year, engine_version, birth_data_hash) still match.
TIMELINE_TTL_SECONDS = 7 * 24 * 3600


CACHE_COLLECTION = "astrology_timeline_cache"


# ---------------------------------------------------------------------------
# Cache key + birth-data hash
# ---------------------------------------------------------------------------

def build_cache_key(user_id: str, year: int, engine_version: str = ENGINE_VERSION) -> str:
    """Canonical cache key string. Kept as a single helper so the format
    stays in lockstep across read / write / log sites."""
    return f"astrology_timeline::{user_id}::{year}::{engine_version}"


def compute_birth_data_hash(chart_doc: Optional[Dict[str, Any]]) -> str:
    """Stable short hash of the user's natal-chart birth inputs.

    A change to any of these inputs (birth_date, birth_time,
    birth_location.latitude/longitude, timezone) MUST invalidate the
    cached timeline because the underlying planet houses/signs change.
    """
    if not isinstance(chart_doc, dict):
        return "no_chart"

    birth = chart_doc.get("birth_data") or {}
    user_birth = (
        # legacy fallbacks — some older charts store birth inputs at top
        # level rather than under birth_data
        chart_doc.get("user_birth_inputs")
        or birth
        or {}
    )

    parts = [
        str(user_birth.get("birth_date") or chart_doc.get("birth_date") or ""),
        str(user_birth.get("birth_time") or chart_doc.get("birth_time") or ""),
        str(user_birth.get("timezone") or chart_doc.get("timezone") or ""),
        str(user_birth.get("latitude") or chart_doc.get("latitude") or ""),
        str(user_birth.get("longitude") or chart_doc.get("longitude") or ""),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Cache reader / builder
# ---------------------------------------------------------------------------

async def get_or_build_astrology_timeline(
    db,
    user_id: str,
    chart_doc: Optional[Dict[str, Any]] = None,
    *,
    force_refresh: bool = False,
) -> Optional[Dict[str, Any]]:
    """Return a fresh-or-cached astrology timeline payload.

    Args:
        db: motor AsyncIOMotorDatabase.
        user_id: target user id.
        chart_doc: the user's chart doc (db.charts.find_one(...)). If
            None, the function loads it.
        force_refresh: if True, bypass cache and regenerate.

    Returns:
        Timeline payload dict (with ``_cache_meta`` envelope), or None
        when no chart is available to build from.

    ``_cache_meta``:
        {
          "source":   "cache" | "generated",
          "year":     int,
          "engine_version": str,
          "birth_data_hash": str,
          "generated_at":   ISO datetime,
          "age_seconds":    float,
          "refresh_reason": Optional[str]    # only present on rebuild
        }
    """
    # Load chart if not provided
    if chart_doc is None:
        try:
            chart_doc = await db.charts.find_one({"user_id": user_id})
        except Exception as e:  # noqa: BLE001
            logger.warning("[AstroTimelineCache] chart fetch failed for %s: %s", user_id, e)
            chart_doc = None

    if not chart_doc:
        return None

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_hash = compute_birth_data_hash(chart_doc)
    current_version = ENGINE_VERSION

    # ---- Read cache ------------------------------------------------------
    cached: Optional[Dict[str, Any]] = None
    refresh_reason: Optional[str] = None

    if not force_refresh:
        try:
            cached = await db[CACHE_COLLECTION].find_one({"user_id": user_id})
        except Exception as e:  # noqa: BLE001
            logger.warning("[AstroTimelineCache] cache read failed for %s: %s", user_id, e)
            cached = None

    if force_refresh:
        refresh_reason = "force_refresh"
    elif cached is None:
        refresh_reason = "no_cache"
    else:
        # Trigger checks
        if cached.get("year") != current_year:
            refresh_reason = "year_rollover"
        elif cached.get("engine_version") != current_version:
            refresh_reason = "engine_version_changed"
        elif cached.get("birth_data_hash") != current_hash:
            refresh_reason = "birth_data_changed"
        else:
            generated_at = cached.get("generated_at")
            try:
                if isinstance(generated_at, datetime):
                    ga = (
                        generated_at if generated_at.tzinfo
                        else generated_at.replace(tzinfo=timezone.utc)
                    )
                    age = (now - ga).total_seconds()
                else:
                    age = TIMELINE_TTL_SECONDS + 1  # force refresh on bad data
            except Exception:  # noqa: BLE001
                age = TIMELINE_TTL_SECONDS + 1
            if age > TIMELINE_TTL_SECONDS:
                refresh_reason = "ttl_expired"

    # ---- Return cached when valid ---------------------------------------
    if refresh_reason is None and cached is not None:
        payload = cached.get("payload") or {}
        ga = cached.get("generated_at")
        age_seconds = 0.0
        if isinstance(ga, datetime):
            ga_aware = ga if ga.tzinfo else ga.replace(tzinfo=timezone.utc)
            age_seconds = (now - ga_aware).total_seconds()
        payload["_cache_meta"] = {
            "source": "cache",
            "year": cached.get("year"),
            "engine_version": cached.get("engine_version"),
            "birth_data_hash": cached.get("birth_data_hash"),
            "generated_at": ga.isoformat() if isinstance(ga, datetime) else None,
            "age_seconds": age_seconds,
            "cache_key": build_cache_key(user_id, current_year, current_version),
        }
        return payload

    # ---- Regenerate -----------------------------------------------------
    try:
        fresh = generate_astrology_timeline(chart_doc, current_year=current_year)
    except Exception as e:  # noqa: BLE001
        logger.warning("[AstroTimelineCache] generator failed for %s: %s", user_id, e)
        fresh = None

    if not fresh:
        return None

    cache_doc = {
        "user_id": user_id,
        "year": current_year,
        "engine_version": current_version,
        "birth_data_hash": current_hash,
        "generated_at": now,
        "cache_key": build_cache_key(user_id, current_year, current_version),
        "payload": fresh,
        "refresh_reason": refresh_reason,
    }
    try:
        await db[CACHE_COLLECTION].update_one(
            {"user_id": user_id},
            {"$set": cache_doc},
            upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[AstroTimelineCache] cache write failed for %s: %s", user_id, e)

    payload_with_meta = dict(fresh)
    payload_with_meta["_cache_meta"] = {
        "source": "generated",
        "year": current_year,
        "engine_version": current_version,
        "birth_data_hash": current_hash,
        "generated_at": now.isoformat(),
        "age_seconds": 0.0,
        "refresh_reason": refresh_reason,
        "cache_key": cache_doc["cache_key"],
    }
    return payload_with_meta


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

async def invalidate_user_timeline_cache(db, user_id: str) -> int:
    """Delete the cached timeline doc for a user. Returns deletion count.

    Use when the system mutates birth data and wants to guarantee the
    next read regenerates."""
    try:
        res = await db[CACHE_COLLECTION].delete_many({"user_id": user_id})
        return res.deleted_count or 0
    except Exception as e:  # noqa: BLE001
        logger.warning("[AstroTimelineCache] invalidate failed for %s: %s", user_id, e)
        return 0
