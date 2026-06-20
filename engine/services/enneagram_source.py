"""
Canonical Enneagram source helper.
==================================

Single source of truth for resolving a user's Enneagram CORE TYPE across
the codebase. Forum Dynamics, Member Mapping, Home Insight, and any other
aggregator MUST use this helper to avoid drift between:

  - user.enneagram_type            (canonical)
  - user.enneagram.inferred_core   (computed by the inference engine)
  - user.enneagram.core            (self-declared / legacy nested)
  - user.enneagram                 (legacy scalar)

Also provides a batch backfill function for the one-time startup migration
that normalises legacy values into user.enneagram_type.

Helper contract:
  get_user_enneagram(user) -> int | None     # 1..9 or None
  NEVER returns wing. Core-only.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple


def _normalize_core(value: Any) -> Optional[int]:
    """Coerce anything into a valid core int 1..9 or None."""
    if value is None:
        return None
    # Handle dict like {"number": 5, "label": "Type 5"} defensively
    if isinstance(value, dict):
        return _normalize_core(value.get("number") or value.get("type") or value.get("core"))
    try:
        core = int(value)
    except (TypeError, ValueError):
        # Accept strings like "Type 5", "5w4", "5"
        if isinstance(value, str):
            import re as _re
            m = _re.search(r"\b([1-9])\b", value)
            if m:
                try:
                    core = int(m.group(1))
                except ValueError:
                    return None
            else:
                return None
        else:
            return None
    return core if 1 <= core <= 9 else None


def get_user_enneagram(user: Optional[Dict[str, Any]]) -> Optional[int]:
    """
    Return the canonical Enneagram core type (1..9) for this user, following
    the fallback chain in priority order:

      1. user.enneagram_type
      2. user.enneagram.inferred_core
      3. user.enneagram.core
      4. legacy scalar user.enneagram

    Returns None when no valid core is found.
    """
    if not user or not isinstance(user, dict):
        return None

    # 1) canonical
    core = _normalize_core(user.get("enneagram_type"))
    if core is not None:
        return core

    # 2 + 3) nested inferred_core / core
    enneagram_obj = user.get("enneagram")
    if isinstance(enneagram_obj, dict):
        core = _normalize_core(enneagram_obj.get("inferred_core"))
        if core is not None:
            return core
        core = _normalize_core(enneagram_obj.get("core"))
        if core is not None:
            return core

    # 4) legacy scalar
    core = _normalize_core(user.get("enneagram"))
    return core  # may be None


def resolve_with_source(user: Optional[Dict[str, Any]]) -> Tuple[Optional[int], Optional[str]]:
    """
    Same as `get_user_enneagram` but also returns which field the value
    came from. Useful for migrations and diagnostics.
    """
    if not user or not isinstance(user, dict):
        return None, None

    core = _normalize_core(user.get("enneagram_type"))
    if core is not None:
        return core, "enneagram_type"

    enneagram_obj = user.get("enneagram")
    if isinstance(enneagram_obj, dict):
        core = _normalize_core(enneagram_obj.get("inferred_core"))
        if core is not None:
            return core, "enneagram.inferred_core"
        core = _normalize_core(enneagram_obj.get("core"))
        if core is not None:
            return core, "enneagram.core"

    core = _normalize_core(user.get("enneagram"))
    if core is not None:
        return core, "enneagram(legacy)"

    return None, None


async def backfill_enneagram_type(db, logger=None) -> Dict[str, int]:
    """
    One-time backfill. For every user where `enneagram_type` is missing but
    a valid legacy value exists anywhere in the fallback chain, set
    `enneagram_type` to the resolved integer core. NEVER overwrites an
    existing value.

    Also — if `enneagram_results` collection has a valid `inferred_core` for
    a user whose user doc has nothing, we backfill the user doc from there
    too (this was the specific drift that made Forum Dynamics stale).

    Returns a summary dict:
      { "scanned": N, "backfilled_from_user_doc": N, "backfilled_from_results": N }
    """
    summary = {
        "scanned": 0,
        "backfilled_from_user_doc": 0,
        "backfilled_from_results": 0,
    }

    cursor = db.users.find(
        {"$or": [
            {"enneagram_type": {"$exists": False}},
            {"enneagram_type": None},
        ]}
    )
    async for user in cursor:
        summary["scanned"] += 1
        uid = user.get("_id")

        # First try to resolve from the user doc alone
        core, source = resolve_with_source(user)
        if core is not None and source != "enneagram_type":
            await db.users.update_one({"_id": uid}, {"$set": {"enneagram_type": core}})
            summary["backfilled_from_user_doc"] += 1
            if logger:
                logger.info(f"[EnneagramBackfill] {uid} → type={core} (from {source})")
            continue

        # Otherwise fall back to the enneagram_results collection
        er = await db.enneagram_results.find_one({"user_id": str(uid)})
        if not er:
            continue
        er_core = _normalize_core(er.get("inferred_core") or er.get("core_type"))
        if er_core is None:
            continue
        await db.users.update_one({"_id": uid}, {"$set": {"enneagram_type": er_core}})
        summary["backfilled_from_results"] += 1
        if logger:
            logger.info(
                f"[EnneagramBackfill] {uid} → type={er_core} (from enneagram_results)"
            )

    return summary
