"""
Timeline Modulation — Phase 1B/1C
=================================
Build marker: timeline-phase-1b-1c-modulation-v1

Modulates the Today and Home payloads with awareness of the user's
Governing Life Chapter — WITHOUT replacing local truth.

CORE PRINCIPLE (load-bearing):
  Timeline is climate. Today is weather.
  The chapter MODULATES interpretation. It does NOT consume the surface.

This module is a strict POST-PROCESSOR. It NEVER mutates the existing
fields of the Today/Home payload. It ONLY appends:
    payload["timeline_modulation"]        # visible to UI
    payload["timeline_modulation_debug"]  # proof layer

If the user has no chapter, has a fallback chapter, or a calm/light
transit day, modulation strength collapses to LOW and the chapter
recedes — exactly as climate should when the weather is its own thing.

USAGE (called after Today/Home are computed, BEFORE caching):
    from services.timeline_modulation import (
        attach_modulation_to_today,
        attach_modulation_to_home,
    )

    insight = await generate_today_v4(...)
    await attach_modulation_to_today(db, user_id, insight)   # mutates `insight`
    return insight
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "timeline-phase-1b-1c-modulation-v1"


# ---------------------------------------------------------------------------
# Strength taxonomy
# ---------------------------------------------------------------------------
STRENGTH_LOW    = "LOW"
STRENGTH_MEDIUM = "MEDIUM"
STRENGTH_HIGH   = "HIGH"


# ---------------------------------------------------------------------------
# Interpretive-bias codes (frontend-consumable taxonomy)
# ---------------------------------------------------------------------------
# These are short codes the UI can lean on for subtle emphasis (eyebrow
# colour, copy de-emphasis, CTA tilt) WITHOUT having to read the chapter.
BIAS_CODES = (
    "none",
    "relational",        # emotional_permeability → boundaries / absorbed truths
    "recursive",         # cognitive_recursion    → loop visibility / decision deferral
    "momentum",          # achievement_axis       → output vs progress
    "compression",       # identity / closure arc → letting-go inflection
    "expansion",         # expansion arcs         → capacity / cost-of-more
)

_FAMILY_TO_BIAS: Dict[str, str] = {
    "emotional_permeability": "relational",
    "cognitive_recursion":    "recursive",
    "achievement_axis":       "momentum",
}

_ARC_TO_BIAS: Dict[str, str] = {
    "closure":     "compression",
    "expansion":   "expansion",
    "identity":    "compression",
    "integration": "none",
    "ending":      "compression",
    "threshold":   "none",
    "pressure":    "none",
}


# ---------------------------------------------------------------------------
# Thread-line banks — family-keyed, never quote the chapter title.
# Multiple options per family so the frontend doesn't repeat verbatim.
# Selection is deterministic per (user, day, family) via signature_hash.
# Lines are intentionally HORIZONTAL (no chapter reference, no slogan).
# ---------------------------------------------------------------------------
THREAD_LINES_BY_FAMILY: Dict[str, List[str]] = {
    "emotional_permeability": [
        "What gets absorbed today without being named will still be carried tomorrow.",
        "Small relational moments may register more weight than they appear to.",
        "Notice where smoothing the room is happening before you choose it.",
        "The cost of holding the peace continues to accumulate quietly underneath.",
        "Some of what arrives today belongs to someone else's emotional state, not yours.",
    ],
    "cognitive_recursion": [
        "The thinking that protected you isn't doing new work today — just the same work louder.",
        "Refinement is asking to be re-examined as a category.",
        "The small decisions in front of you may not need the certainty you're asking them to wait for.",
        "Pre-deciding is starting to feel like the deciding.",
        "The question is being used as cover for the move.",
    ],
    "achievement_axis": [
        "Effort and progress aren't tracking together right now. Read the gap directly.",
        "Output isn't the variable today. Recovery is.",
        "What you're calling momentum may already be inertia.",
        "Stopping briefly will give you more useful information than continuing.",
    ],
}


# ---------------------------------------------------------------------------
# Resonance keywords — used to detect when today's transit text aligns
# with the chapter's internal topics. Strong resonance bumps strength
# from MEDIUM → HIGH.
# ---------------------------------------------------------------------------
_RESONANCE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "emotional_permeability": (
        "communicat", "relationship", "partner", "boundary", "boundar",
        "absorb", "harmon", "peace", "say no", "voice", "speak",
        "feel", "mood", "emotion", "home", "family", "domestic",
    ),
    "cognitive_recursion": (
        "think", "thought", "analy", "doubt", "uncertain", "decid",
        "decision", "refine", "question", "loop", "mental", "mind",
        "clari", "ruminat", "second-guess", "over-think", "overthink",
    ),
    "achievement_axis": (
        "work", "output", "effort", "push", "ambit", "career", "task",
        "productiv", "exhaust", "tired", "burnout", "achiev",
        "drive", "performance", "deliver",
    ),
}


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------
ModulationPayload = Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return " ".join(_safe_str(i) for i in x)
    if isinstance(x, dict):
        return " ".join(_safe_str(v) for v in x.values())
    return ""


def _collect_visible_text_from_today(insight: Dict[str, Any]) -> str:
    parts: List[str] = []
    for k in (
        "headline", "whats_happening", "how_it_shows_up",
        "what_it_feels_like", "the_risk",
    ):
        parts.append(_safe_str(insight.get(k)))
    mv = insight.get("the_move")
    if isinstance(mv, dict):
        parts.append(_safe_str(mv.get("text")))
        parts.append(_safe_str(mv.get("reflection")))
    elif isinstance(mv, str):
        parts.append(mv)
    return " ".join(p for p in parts if p).lower()


def _collect_visible_text_from_home(home: Dict[str, Any]) -> str:
    parts: List[str] = []
    for k in (
        "the_call", "the_reality", "where_this_lands",
        "the_edge", "cta", "today_signal",
    ):
        parts.append(_safe_str(home.get(k)))
    return " ".join(p for p in parts if p).lower()


def _resonance_score(family: Optional[str], visible_text: str) -> int:
    if not family:
        return 0
    kws = _RESONANCE_KEYWORDS.get(family) or ()
    if not kws:
        return 0
    return sum(1 for kw in kws if kw in visible_text)


# ---------------------------------------------------------------------------
# Strength + bias
# ---------------------------------------------------------------------------
def compute_modulation_strength(
    *,
    chapter_id: Optional[str],
    chapter_score: float,
    resonance_count: int,
    intensity: Optional[str],
) -> str:
    """Return STRENGTH_LOW / MEDIUM / HIGH.

    Heuristic (load-bearing — protects transit truth):
      LOW: fallback chapter, OR very weak chapter score, OR low-intensity
           day with no resonance.
      HIGH: requires AT LEAST ONE resonance keyword (today's transit text
            must topically rhyme with the chapter's family). Without this
            gate, an extreme-but-off-topic day would still attach a
            thread line about a domain that has nothing to do with what
            the user is actually experiencing today.
            HIGH triggers when:
              - resonance >= 1 AND chapter_score >= 4.0, OR
              - resonance >= 2 AND intensity in extreme/stellium, OR
              - resonance >= 3 (very strong topical alignment alone).
      MEDIUM: real chapter, but no thread overlay — only the bias flows
              through. This is the most common branch and is intentional:
              the chapter modulates UI emphasis without ever speaking
              over the day.

    Critical: the thread surface (HIGH) MUST require resonance >= 1.
    A chapter that doesn't rhyme with today's actual weather should
    recede — not narrate over it.
    """
    if not chapter_id or chapter_id == "active_recalibration":
        return STRENGTH_LOW
    if chapter_score < 1.5:
        return STRENGTH_LOW
    intensity_l = (intensity or "").strip().lower()
    if intensity_l == "low" and resonance_count == 0:
        return STRENGTH_LOW

    # HIGH always requires topical resonance — otherwise the thread
    # would speak over the day instead of with it.
    if resonance_count >= 1 and chapter_score >= 4.0:
        return STRENGTH_HIGH
    if resonance_count >= 2 and intensity_l in ("extreme", "stellium"):
        return STRENGTH_HIGH
    if resonance_count >= 3:
        return STRENGTH_HIGH

    return STRENGTH_MEDIUM


def compute_interpretive_bias(
    *,
    existential_family: Optional[str],
    arc_type: Optional[str],
) -> str:
    """Map chapter family (preferred) / arc to a UI-consumable code.

    Family wins over arc. Unknown → 'none'.
    """
    if existential_family and existential_family in _FAMILY_TO_BIAS:
        return _FAMILY_TO_BIAS[existential_family]
    if arc_type and arc_type in _ARC_TO_BIAS:
        return _ARC_TO_BIAS[arc_type]
    return "none"


# ---------------------------------------------------------------------------
# Thread-line picker
# ---------------------------------------------------------------------------
def _deterministic_index(*parts: str, modulo: int) -> int:
    """Stable per-day picker — same user + same day + same family
    produces the same thread line. Avoids "different line every refresh"."""
    if modulo <= 0:
        return 0
    raw = "|".join(parts).encode("utf-8")
    return int(hashlib.sha1(raw).hexdigest(), 16) % modulo


def pick_thread_line(
    *,
    family: Optional[str],
    user_id: str,
    day_key: str,
    strength: str,
) -> Optional[str]:
    """Return a single subtle thread sentence, or None when no thread
    should be surfaced. Threads are ONLY surfaced when strength = HIGH."""
    if strength != STRENGTH_HIGH:
        return None
    if not family:
        return None
    bank = THREAD_LINES_BY_FAMILY.get(family)
    if not bank:
        return None
    idx = _deterministic_index(user_id, day_key, family, modulo=len(bank))
    return bank[idx]


# ---------------------------------------------------------------------------
# Core: build the modulation block from a Governing Chapter payload
# ---------------------------------------------------------------------------
def _build_modulation_block(
    *,
    gc_payload: Optional[Dict[str, Any]],
    visible_text: str,
    intensity: Optional[str],
    user_id: str,
    day_key: str,
    surface: str,    # "today" | "home"
) -> ModulationPayload:
    """Construct timeline_modulation + timeline_modulation_debug."""
    # Default-safe block when no chapter is available.
    if not gc_payload or not isinstance(gc_payload, dict):
        return {
            "visible": {
                "active":         False,
                "strength":       STRENGTH_LOW,
                "bias":           "none",
                "thread":         None,
                "chapter_id":     None,
                "chapter_title":  None,
            },
            "debug": {
                "build_marker":             BUILD_MARKER,
                "surface":                  surface,
                "governing_chapter":        None,
                "modulation_strength":      STRENGTH_LOW,
                "modulated_signals":        [],
                "weight_adjustments":       [],
                "suppressed_interpretations": [],
                "selected_biases":          ["none"],
                "reason":                   "no_governing_chapter",
            },
        }

    chapter = gc_payload.get("chapter") or {}
    chapter_id = chapter.get("chapter_id")
    chapter_title = chapter.get("title")
    arc_type = chapter.get("arc_type")
    proof = gc_payload.get("proof") or {}
    score = float(proof.get("score") or 0.0)
    matched_signals = list(proof.get("matched_signals") or [])
    existential_family: Optional[str] = None
    # Pull family from shortlist (chapter dict itself doesn't carry it post-serialization)
    for s in (gc_payload.get("shortlist") or []):
        if s.get("chapter_id") == chapter_id:
            existential_family = s.get("existential_family")
            break

    resonance_count = _resonance_score(existential_family, visible_text)
    strength = compute_modulation_strength(
        chapter_id=chapter_id,
        chapter_score=score,
        resonance_count=resonance_count,
        intensity=intensity,
    )
    bias = compute_interpretive_bias(
        existential_family=existential_family,
        arc_type=arc_type,
    )
    thread = pick_thread_line(
        family=existential_family,
        user_id=user_id,
        day_key=day_key,
        strength=strength,
    )

    # Debug fields — we keep these populated for the proof drawer.
    suppressed: List[str] = []
    selected_biases: List[str] = [bias] if bias != "none" else []
    weight_adjustments: List[Dict[str, Any]] = []

    if strength == STRENGTH_LOW:
        # When LOW, the chapter explicitly recedes — record that we
        # suppressed any chapter-overlay text on purpose.
        suppressed.append("chapter_overlay_thread")
        reason = "low_strength_chapter_recedes"
    elif strength == STRENGTH_MEDIUM:
        # MEDIUM still suppresses the overlay thread. The bias is the
        # only visible influence.
        suppressed.append("chapter_overlay_thread")
        reason = "medium_strength_bias_only"
    else:
        # HIGH: thread surfaces.
        reason = "high_strength_thread_surfaced"
        weight_adjustments.append({
            "category": existential_family or "(unflagged)",
            "applied":  "narrative_emphasis_tilt",
        })

    return {
        "visible": {
            "active":        strength != STRENGTH_LOW,
            "strength":      strength,
            "bias":          bias,
            "thread":        thread,            # None unless HIGH
            "chapter_id":    chapter_id,
            "chapter_title": chapter_title,
        },
        "debug": {
            "build_marker":             BUILD_MARKER,
            "surface":                  surface,
            "governing_chapter": {
                "chapter_id":         chapter_id,
                "title":              chapter_title,
                "arc_type":           arc_type,
                "existential_family": existential_family,
                "score":              score,
                "matched_signals":    matched_signals,
            },
            "modulation_strength":      strength,
            "resonance_count":          resonance_count,
            "modulated_signals":        matched_signals[:5],
            "weight_adjustments":       weight_adjustments,
            "suppressed_interpretations": suppressed,
            "selected_biases":          selected_biases,
            "intensity":                intensity,
            "reason":                   reason,
        },
    }


# ---------------------------------------------------------------------------
# Governing-chapter fetch helper
# ---------------------------------------------------------------------------
async def _safe_get_governing_chapter(db, user_id: str) -> Optional[Dict[str, Any]]:
    """Best-effort fetch. Modulation is OPTIONAL — never bring the host
    endpoint down because the governor failed."""
    try:
        from services.phase_governor import resolve_governing_chapter
        gc = await resolve_governing_chapter(db, user_id, force_refresh=False)
        return gc
    except Exception as e:
        logger.warning(f"[TimelineModulation] governor fetch failed for {user_id[:8]}: {e}")
        return None


# ---------------------------------------------------------------------------
# Public surface APIs
# ---------------------------------------------------------------------------
async def attach_modulation_to_today(
    db,
    user_id: str,
    insight: Dict[str, Any],
    *,
    day_key: str,
) -> None:
    """Mutates `insight` in place. Adds:
        insight["timeline_modulation"]        (visible block)
        insight["timeline_modulation_debug"]  (proof block)

    Idempotent: safe to call twice (re-derives from current state)."""
    if not isinstance(insight, dict):
        return
    try:
        gc = await _safe_get_governing_chapter(db, user_id)
        visible_text = _collect_visible_text_from_today(insight)
        intensity = insight.get("intensity")
        block = _build_modulation_block(
            gc_payload=gc,
            visible_text=visible_text,
            intensity=intensity,
            user_id=user_id,
            day_key=day_key,
            surface="today",
        )
        insight["timeline_modulation"]       = block["visible"]
        insight["timeline_modulation_debug"] = block["debug"]
        logger.info(
            f"[TimelineModulation] today user={user_id[:8]} "
            f"strength={block['visible']['strength']} "
            f"bias={block['visible']['bias']} "
            f"thread={'yes' if block['visible']['thread'] else 'no'}"
        )
    except Exception as e:
        logger.exception(f"[TimelineModulation] attach_to_today failed for {user_id}: {e}")
        # Fail-soft — never break Today
        insight.setdefault("timeline_modulation", {
            "active": False, "strength": STRENGTH_LOW,
            "bias": "none", "thread": None,
            "chapter_id": None, "chapter_title": None,
        })
        insight.setdefault("timeline_modulation_debug", {
            "build_marker": BUILD_MARKER,
            "surface": "today",
            "reason": "modulation_exception",
        })


async def attach_modulation_to_home(
    db,
    user_id: str,
    home_payload: Dict[str, Any],
    *,
    day_key: str,
) -> None:
    """Mutates `home_payload` in place. Same contract as Today."""
    if not isinstance(home_payload, dict):
        return
    try:
        gc = await _safe_get_governing_chapter(db, user_id)
        visible_text = _collect_visible_text_from_home(home_payload)
        # Home doesn't always expose 'intensity' at the top level; try to
        # pull it from today_signal which is the v6 anchor.
        intensity = None
        ts = home_payload.get("today_signal")
        if isinstance(ts, dict):
            intensity = ts.get("intensity") or ts.get("day_class")
        block = _build_modulation_block(
            gc_payload=gc,
            visible_text=visible_text,
            intensity=intensity,
            user_id=user_id,
            day_key=day_key,
            surface="home",
        )
        home_payload["timeline_modulation"]       = block["visible"]
        home_payload["timeline_modulation_debug"] = block["debug"]
        logger.info(
            f"[TimelineModulation] home user={user_id[:8]} "
            f"strength={block['visible']['strength']} "
            f"bias={block['visible']['bias']} "
            f"thread={'yes' if block['visible']['thread'] else 'no'}"
        )
    except Exception as e:
        logger.exception(f"[TimelineModulation] attach_to_home failed for {user_id}: {e}")
        home_payload.setdefault("timeline_modulation", {
            "active": False, "strength": STRENGTH_LOW,
            "bias": "none", "thread": None,
            "chapter_id": None, "chapter_title": None,
        })
        home_payload.setdefault("timeline_modulation_debug", {
            "build_marker": BUILD_MARKER,
            "surface": "home",
            "reason": "modulation_exception",
        })
