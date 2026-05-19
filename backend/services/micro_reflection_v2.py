"""
Micro-Reflection v2
===================

Build marker: micro-reflection-v2

Lightweight, ambient reflection system.  Lets a user tap a single chip
("That lands.", "This feels familiar.", "I'm resisting this.", ...)
under an assistant message and have that signal feed Mirror's
longitudinal pattern memory.

Design rules baked in here:
    - One tap is enough.  No journaling expected, no streaks, no counts.
    - Micro-reflections influence TONE, TIMING, growth detection, pattern
      confidence — but are RARELY referenced explicitly.
    - Growth signals (changed / less_intense / softer / clear) are
      especially valuable: they're how Mirror knows when an old pattern
      is loosening, not just when it's still alive.
    - Resistance signals (resisting / stuck / pressured) are tracked but
      surfaced gently — they're a flag, not a verdict.

Collection: `micro_reflections`
Schema (Mongo doc, no PII / no raw user text):
    {
        id:              uuid str,
        user_id:         str,
        ts:              datetime (UTC),
        label:           one of `_VALID_LABELS`,
        texture:         optional, one of `_VALID_TEXTURES`,
        source:          "life_tab" | "people" | "mirror" | "other",
        source_session:  optional str,
        source_message:  optional str  (the assistant message id user tapped from),
        context_pattern_keys: list[str]  (snapshot of patterns active at tap time),
        context_lens:    optional str  (the lens active at tap time),
        context_life_domain: optional str,
        context_about_person_id: optional str,
    }

Public API:
    record_reflection(...)
    get_recent_reflections(user_id, limit, since=None)
    analyze_recent(user_id)   ->  dict of bucketed counts + growth signals
    compose_reflection_loop_block(user_id)
        ->  (system_block_text or "", debug_payload)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


_VALID_LABELS: List[str] = [
    "lands",          # "That lands."
    "familiar",       # "This feels familiar."
    "resisting",      # "I'm resisting this."
    "true_lately",    # "This feels true lately."
    "not_sure",       # "Not sure yet."
    "changed",        # "This changed."
    "less_intense",   # "This feels less intense now."
]


_VALID_TEXTURES: List[str] = [
    "tense", "distant", "open", "pressured",
    "stuck", "clear", "conflicted", "softer",
]


# Labels / textures that count as a GROWTH signal (charge reducing).
_GROWTH_LABELS = {"changed", "less_intense"}
_GROWTH_TEXTURES = {"softer", "clear", "open"}

# Labels / textures that count as a RESISTANCE / STUCKNESS signal.
_RESISTANCE_LABELS = {"resisting"}
_RESISTANCE_TEXTURES = {"stuck", "pressured", "tense"}

# Labels / textures that count as RESONANCE (this is landing).
_RESONANCE_LABELS = {"lands", "familiar", "true_lately"}

# How far back we look when summarising for the dispatcher.
_LOOKBACK_DAYS = 14
_RECENT_LOOKBACK_DAYS = 7


# --------------------------------------------------------------------------
# Validation helpers (small, defensive)
# --------------------------------------------------------------------------


def is_valid_label(label: Optional[str]) -> bool:
    return isinstance(label, str) and label in _VALID_LABELS


def is_valid_texture(texture: Optional[str]) -> bool:
    return texture is None or (isinstance(texture, str) and texture in _VALID_TEXTURES)


def valid_labels() -> List[str]:
    return list(_VALID_LABELS)


def valid_textures() -> List[str]:
    return list(_VALID_TEXTURES)


# --------------------------------------------------------------------------
# Writes
# --------------------------------------------------------------------------


async def record_reflection(
    db,
    *,
    user_id: str,
    label: str,
    source: str,
    texture: Optional[str] = None,
    source_session: Optional[str] = None,
    source_message: Optional[str] = None,
    context_pattern_keys: Optional[List[str]] = None,
    context_lens: Optional[str] = None,
    context_life_domain: Optional[str] = None,
    context_about_person_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insert a single micro-reflection.  Returns the created doc.
    Raises ValueError on invalid label / texture.
    """
    if not is_valid_label(label):
        raise ValueError(f"invalid label: {label!r}")
    if not is_valid_texture(texture):
        raise ValueError(f"invalid texture: {texture!r}")
    if not source:
        source = "other"

    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "ts": datetime.now(timezone.utc),
        "label": label,
        "texture": texture,
        "source": source,
        "source_session": source_session,
        "source_message": source_message,
        "context_pattern_keys": list(context_pattern_keys or []),
        "context_lens": context_lens,
        "context_life_domain": context_life_domain,
        "context_about_person_id": context_about_person_id,
    }
    try:
        await db.micro_reflections.insert_one(dict(doc))
    except Exception:
        # Storage must never crash the chat flow.  Caller is expected to
        # log; we still return the doc shape so the API contract holds.
        pass
    return doc


# --------------------------------------------------------------------------
# Reads
# --------------------------------------------------------------------------


async def get_recent_reflections(
    db,
    *,
    user_id: str,
    limit: int = 50,
    since: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Most-recent-first list of reflections for the user."""
    q: Dict[str, Any] = {"user_id": user_id}
    if since is not None:
        q["ts"] = {"$gte": since}
    try:
        cursor = db.micro_reflections.find(q).sort("ts", -1).limit(max(1, int(limit)))
        rows: List[Dict[str, Any]] = []
        async for r in cursor:
            r.pop("_id", None)
            # Normalise ts to isoformat for JSON.
            ts = r.get("ts")
            if isinstance(ts, datetime):
                r["ts"] = ts.isoformat()
            rows.append(r)
        return rows
    except Exception:
        return []


# --------------------------------------------------------------------------
# Analysis — used by the dispatcher to bias growth detection and to
# generate the (rare) reflection-loop system block.
# --------------------------------------------------------------------------


async def analyze_recent(
    db,
    *,
    user_id: str,
    lookback_days: int = _LOOKBACK_DAYS,
) -> Dict[str, Any]:
    """
    Returns a bucketed summary of recent micro-reflections.  Cheap to
    compute, safe to call on every chat turn.
    """
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    rows = await get_recent_reflections(db, user_id=user_id, limit=200, since=since)

    counts_label: Dict[str, int] = {k: 0 for k in _VALID_LABELS}
    counts_texture: Dict[str, int] = {k: 0 for k in _VALID_TEXTURES}
    growth_score = 0
    resistance_score = 0
    resonance_score = 0
    per_pattern_growth: Dict[str, int] = {}
    per_pattern_resistance: Dict[str, int] = {}

    recent_since = datetime.now(timezone.utc) - timedelta(days=_RECENT_LOOKBACK_DAYS)

    for r in rows:
        lbl = r.get("label")
        tex = r.get("texture")
        ts_str = r.get("ts")
        in_recent_window = False
        if isinstance(ts_str, str):
            try:
                ts_dt = datetime.fromisoformat(ts_str)
                in_recent_window = ts_dt >= recent_since
            except Exception:
                in_recent_window = False

        if lbl in counts_label:
            counts_label[lbl] += 1
        if tex in counts_texture:
            counts_texture[tex] += 1

        is_growth = (lbl in _GROWTH_LABELS) or (tex in _GROWTH_TEXTURES)
        is_resistance = (lbl in _RESISTANCE_LABELS) or (tex in _RESISTANCE_TEXTURES)
        is_resonance = lbl in _RESONANCE_LABELS

        # Recent-window-only signals are weighted higher.
        w = 2 if in_recent_window else 1

        if is_growth:
            growth_score += w
            for k in (r.get("context_pattern_keys") or []):
                per_pattern_growth[k] = per_pattern_growth.get(k, 0) + w
        if is_resistance:
            resistance_score += w
            for k in (r.get("context_pattern_keys") or []):
                per_pattern_resistance[k] = per_pattern_resistance.get(k, 0) + w
        if is_resonance:
            resonance_score += w

    return {
        "marker": "micro-reflection-v2",
        "total": len(rows),
        "counts_label": counts_label,
        "counts_texture": counts_texture,
        "growth_score": growth_score,
        "resistance_score": resistance_score,
        "resonance_score": resonance_score,
        "per_pattern_growth": per_pattern_growth,
        "per_pattern_resistance": per_pattern_resistance,
        "lookback_days": lookback_days,
    }


# --------------------------------------------------------------------------
# Reflection-loop system block
# --------------------------------------------------------------------------


# A small library of soft loop lines.  The dispatcher picks at most ONE
# of these per turn, and only when the signal is real.  These are NOT
# user-facing text directly — they are INSTRUCTIONS to the LLM about
# what to lightly acknowledge.  The LLM is then free to phrase the
# acknowledgement in its own voice.
_LOOP_SCRIPTS = {
    "softening_with_pattern": (
        "REFLECTION LOOP — micro-reflection-v2 noticed that the user has "
        "recently tapped 'changed' / 'less intense' / 'softer' against "
        "patterns including: {patterns}.  Lightly (one short clause max) "
        "acknowledge that something around this feels less charged than "
        "before.  Do NOT mention reflections, taps, or tracking.  Do NOT "
        "over-celebrate or call it growth.  Recognition only.  Then "
        "continue with the user's current message naturally."
    ),
    "softening_general": (
        "REFLECTION LOOP — micro-reflection-v2 noticed a general softening "
        "trend across the user's recent micro-acknowledgements (multiple "
        "'changed' / 'softer' / 'less intense' / 'clear' signals in the "
        "last 7 days, no specific pattern targeted).  If appropriate to "
        "the current message, you MAY (one clause max) reflect that "
        "something seems quieter or clearer for them right now.  Do NOT "
        "mention reflections, taps, or tracking.  Do not force it."
    ),
    "resistance_recent": (
        "REFLECTION LOOP — micro-reflection-v2 detected the user has "
        "recently tapped 'resisting' or 'stuck' or 'pressured' against "
        "patterns including: {patterns}.  Tone-only adjustment: be a touch "
        "softer than the calibrated intensity, and DO NOT push insight "
        "this turn.  Honour the resistance.  Do NOT name the resistance "
        "explicitly unless the user names it first."
    ),
}


async def compose_reflection_loop_block(
    db,
    *,
    user_id: str,
) -> Tuple[str, Dict[str, Any]]:
    """
    Produces an optional system-prompt fragment driven by the user's
    recent micro-reflections.  Returns ("", {}) when no signal is strong
    enough — the dispatcher then appends nothing.
    """
    analysis = await analyze_recent(db, user_id=user_id)
    debug: Dict[str, Any] = {
        "marker": "micro-reflection-v2",
        "growth_score": analysis["growth_score"],
        "resistance_score": analysis["resistance_score"],
        "resonance_score": analysis["resonance_score"],
        "total_recent": analysis["total"],
        "softened_patterns": [],
        "stuck_patterns": [],
        "loop_applied": None,
    }

    if analysis["total"] == 0:
        return "", debug

    # 1. Softening tied to specific patterns wins.
    softened = [
        k for k, v in (analysis["per_pattern_growth"] or {}).items() if v >= 2
    ][:3]
    if softened:
        debug["softened_patterns"] = softened
        debug["loop_applied"] = "softening_with_pattern"
        return (
            _LOOP_SCRIPTS["softening_with_pattern"].format(
                patterns=", ".join(softened)
            ),
            debug,
        )

    # 2. General softening trend.
    if analysis["growth_score"] >= 3 and analysis["growth_score"] >= analysis["resistance_score"]:
        debug["loop_applied"] = "softening_general"
        return _LOOP_SCRIPTS["softening_general"], debug

    # 3. Resistance / stuckness tied to patterns — softer tone this turn.
    stuck = [
        k for k, v in (analysis["per_pattern_resistance"] or {}).items() if v >= 2
    ][:3]
    if stuck:
        debug["stuck_patterns"] = stuck
        debug["loop_applied"] = "resistance_recent"
        return (
            _LOOP_SCRIPTS["resistance_recent"].format(patterns=", ".join(stuck)),
            debug,
        )

    return "", debug
