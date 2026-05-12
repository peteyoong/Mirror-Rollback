"""
Micro-Reflection V2
===================

Low-friction reflection loop that replaces the generic "Reflect" button.

Contract:
    POST /api/reflections/micro
    Body:
        user_id:                str  (required)
        source:                 str  ("home_v6" | "today" | "forum" | ...)
        prompt:                 str  (the question shown to the user)
        response:               str  (user's one-sentence reply, may be empty if
                                      they only used quick-tap)
        quick_tap:              str? ("accurate" | "partly_true" | "not_me")
        linked_signature_hash:  str?
        linked_tension:         str?
        forum_id:               str? (when source == "forum")

    Response:
        id:                     str  (inserted document id)
        pattern_label:          str  (human-readable, no jargon)
        saved:                  True

Storage:
    Writes a `micro_reflection` document to db.reflections so that the
    existing pattern_memory pipeline picks it up automatically on the
    next Home V6 read.

Pattern classification is deterministic (no LLM — Mirror tone
control + zero-latency response so the UX feels instant).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Deterministic pattern-label classifier
# ---------------------------------------------------------------------------
# Maps internal theme strings → human-readable labels.  Lowercase, no
# jargon, no capitalisation — they read as natural sentence fragments
# ("This looks like: speed under uncertainty").

_THEME_LABELS = {
    "speed_under_uncertainty": "speed under uncertainty",
    "premature_initiation":    "closing loops too early",
    "tight_pressure":          "acting to reduce pressure",
    "competing_pulls":         "being pulled in two directions",
    "shift_in_focus":          "redirecting mid-stride",
    "holding":                 "holding back under uncertainty",
    "low_signal":              "reading the room before it's clear",
    "threshold_moment":        "moving at the edge of a decision",
    "background_pattern":      "acting before it's fully clear",
}


# Keyword → theme, used when caller doesn't pass a linked_tension but
# the response text contains an obvious pattern signal.
_RESPONSE_KEYWORDS = [
    ("speed_under_uncertainty", (
        "quickly", "fast", "rush", "urgent", "right now", "before",
        "respond quickly", "reply fast",
    )),
    ("competing_pulls", (
        "two minds", "pulled in", "both ways", "half of me",
        "part of me", "can't decide",
    )),
    ("premature_initiation", (
        "closing", "finalise", "finalize", "wrapping up", "settle",
    )),
    ("tight_pressure", (
        "pressure", "stressed", "overwhelm", "squeeze", "deadline",
    )),
    ("holding", (
        "not moving", "stuck", "hesitant", "waiting", "unsure",
    )),
]


def _infer_theme_from_response(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    for theme, kws in _RESPONSE_KEYWORDS:
        if any(kw in t for kw in kws):
            return theme
    return None


def classify_pattern_label(
    *,
    linked_tension: Optional[str] = None,
    response_text: Optional[str] = None,
    dominant_signal_type: Optional[str] = None,
) -> str:
    """Pick the best-fitting pattern label for this reflection.

    Priority:
      1. `linked_tension` — if the caller passed one from the UI (source
         card already knows its own theme).
      2. Response-text keyword heuristic.
      3. `dominant_signal_type` fallback (full_moon/lunation →
         speed_under_uncertainty; ingress → shift_in_focus; etc.)
      4. background_pattern (safe default).
    """
    if linked_tension and linked_tension.lower() in _THEME_LABELS:
        return _THEME_LABELS[linked_tension.lower()]

    inferred = _infer_theme_from_response(response_text)
    if inferred:
        return _THEME_LABELS[inferred]

    ds = (dominant_signal_type or "").lower()
    if "full_moon" in ds or "new_moon" in ds or "lunation" in ds:
        return _THEME_LABELS["speed_under_uncertainty"]
    if "ingress" in ds:
        return _THEME_LABELS["shift_in_focus"]
    if "tight_aspect" in ds or "aspect" in ds:
        return _THEME_LABELS["tight_pressure"]

    return _THEME_LABELS["background_pattern"]


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

async def save_micro_reflection(
    db,
    *,
    user_id: str,
    source: str,
    prompt: str,
    response: str,
    quick_tap: Optional[str] = None,
    linked_signature_hash: Optional[str] = None,
    linked_tension: Optional[str] = None,
    forum_id: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    rid = str(uuid.uuid4())

    # Pull current V5 dominant_signal_type from cached daily_astrology
    # if available — we use it as a fallback for pattern classification.
    dst: Optional[str] = None
    try:
        v5 = await db.daily_astrology.find_one(
            {"user_id": user_id},
            sort=[("generated_at", -1)],
        )
        if v5:
            ds = v5.get("dominant_signal") or {}
            dst = ds.get("type")
    except Exception:
        pass

    pattern_label = classify_pattern_label(
        linked_tension=linked_tension,
        response_text=response,
        dominant_signal_type=dst,
    )

    doc = {
        "id":                     rid,
        "user_id":                user_id,
        "kind":                   "micro_reflection",
        "source":                 source,                 # "home_v6" | "today" | "forum"
        "prompt":                 (prompt or "").strip(),
        "response":               (response or "").strip(),
        "quick_tap":              quick_tap or None,
        "pattern_label":          pattern_label,
        "linked_signature_hash":  linked_signature_hash,
        "linked_tension":         linked_tension,
        "forum_id":               forum_id,
        "created_at":             now,
        "timestamp":              now,
    }

    try:
        await db.reflections.insert_one(doc)
    except Exception as e:
        logger.warning("[MicroReflect] insert failed: %s", e)
        raise

    return {
        "id":            rid,
        "pattern_label": pattern_label,
        "saved":         True,
        "created_at":    now.isoformat(),
    }
