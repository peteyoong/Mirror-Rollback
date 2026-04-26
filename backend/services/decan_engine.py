"""
Decan Tone Modulation — invisible polish layer (Rule 16).

Refines HOW the output reads (verb choice, pacing, sentence rhythm) without
changing WHAT it says. This is the FINAL layer applied AFTER:

   Zi Wei origin → Language Physics → Emotional Gravity → Cross-domain.

It MUST NOT:
    - introduce new ideas
    - change conclusions
    - alter domain logic
    - reference astrology, decans, or any system

If two users share the same pattern but different decans, the output should
feel slightly more "like them" — but never *say* anything different.

Public surface
==============

    compute_decan_index(chart) -> 1 | 2 | 3
        Deterministic from the Sun's sign-relative degree.

    build_decan_addendum(decan_index) -> str
        Tone instruction to APPEND to a generation system prompt.

    audit_decan_tone(text, decan_index) -> {pass: bool, reasons: [...]}
        Deterministic post-generation check on average sentence length.
        If it FAILS, callers should treat the decan polish as "make it
        worse" and discard / revert (per the spec).
"""

from __future__ import annotations

import re
import statistics
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Decan computation
# ---------------------------------------------------------------------------

def compute_decan_index(chart: Optional[Dict[str, Any]]) -> int:
    """
    Returns the Sun's decan within its sign:
        Decan 1 → degree ∈ [0°, 10°)
        Decan 2 → degree ∈ [10°, 20°)
        Decan 3 → degree ∈ [20°, 30°)

    Uses the existing chart structure produced by the astrology engine
    (`astrology.planets.Sun.degree`). Falls back to Decan 2 (the
    "balanced" default) if the chart is missing or malformed.
    """
    try:
        if not isinstance(chart, dict):
            return 2
        astro = chart.get("astrology") or {}
        if not isinstance(astro, dict):
            return 2
        planets = astro.get("planets") or {}
        if not isinstance(planets, dict):
            return 2
        sun = planets.get("Sun") or {}
        deg = sun.get("degree") if isinstance(sun, dict) else None
        if not isinstance(deg, (int, float)):
            return 2
        if deg < 10.0:
            return 1
        if deg < 20.0:
            return 2
        return 3
    except Exception:
        return 2


# ---------------------------------------------------------------------------
# Tone profiles (invisible — kept as private constants)
# ---------------------------------------------------------------------------
#
# Targets are deliberately overlapping to keep the audit tolerant. The
# user-visible content must NEVER deviate to satisfy these targets — they
# are guidance for the LLM only and a soft check on the final output.

_DECAN_TONE: Dict[int, Dict[str, Any]] = {
    1: {
        "label":         "direct / initiating",
        "verbs":         ("move", "begin", "start", "shift", "claim", "take", "step"),
        "rhythm":        "shorter, forward-driving sentences",
        "len_target":    (8.0, 14.0),     # avg words/sentence
        "len_audit":     (6.0, 17.0),     # tolerant pass band
    },
    2: {
        "label":         "structured / measured",
        "verbs":         ("hold", "carry", "build", "settle", "adjust", "anchor"),
        "rhythm":        "balanced, sequenced sentences",
        "len_target":    (12.0, 18.0),
        "len_audit":     (9.0, 22.0),
    },
    3: {
        "label":         "reflective / spacious",
        "verbs":         ("notice", "sense", "register", "recognise", "let", "see"),
        "rhythm":        "slightly more spacious, interpretive sentences",
        "len_target":    (14.0, 22.0),
        "len_audit":     (11.0, 26.0),
    },
}


# ---------------------------------------------------------------------------
# Prompt addendum
# ---------------------------------------------------------------------------

_DECAN_PROMPT_ADDENDA: Dict[int, str] = {
    1: (
        "\n=================================================="
        "\nFINAL POLISH — INVISIBLE TONE (apply to surface expression ONLY)"
        "\n=================================================="
        "\nApply this tone shape to your sentences. NEVER reference it."
        "\nThis is a POLISH layer — do NOT change meaning, do NOT add new"
        "\nideas, do NOT introduce new metaphors. If applying this would"
        "\ndistort the meaning, IGNORE it and keep the meaning intact."
        "\n  - Tone: direct, initiating, forward-moving."
        "\n  - Sentences: shorter (avg 8–14 words). Strong active verbs."
        "\n  - Less reflective phrasing, more immediate."
        "\n  - Prefer initiating verbs where natural: move, begin, start,"
        "\n    shift, claim, take, step."
        "\n  - Do NOT begin every sentence with a verb — that becomes a"
        "\n    pattern. Vary openings naturally."
    ),
    2: (
        "\n=================================================="
        "\nFINAL POLISH — INVISIBLE TONE (apply to surface expression ONLY)"
        "\n=================================================="
        "\nApply this tone shape to your sentences. NEVER reference it."
        "\nThis is a POLISH layer — do NOT change meaning, do NOT add new"
        "\nideas, do NOT introduce new metaphors. If applying this would"
        "\ndistort the meaning, IGNORE it and keep the meaning intact."
        "\n  - Tone: structured, measured, grounded."
        "\n  - Sentences: balanced (avg 12–18 words). Clear sequence."
        "\n  - Slight emphasis on cause/effect or process."
        "\n  - Prefer steady verbs where natural: hold, carry, build,"
        "\n    settle, adjust, anchor."
        "\n  - Do NOT become formal or report-like. Stay conversational."
    ),
    3: (
        "\n=================================================="
        "\nFINAL POLISH — INVISIBLE TONE (apply to surface expression ONLY)"
        "\n=================================================="
        "\nApply this tone shape to your sentences. NEVER reference it."
        "\nThis is a POLISH layer — do NOT change meaning, do NOT add new"
        "\nideas, do NOT introduce new metaphors. If applying this would"
        "\ndistort the meaning, IGNORE it and keep the meaning intact."
        "\n  - Tone: reflective, slightly spacious, context-aware."
        "\n  - Sentences: a touch longer (avg 14–22 words). Interpretive"
        "\n    framing where natural (e.g. 'before the moment has fully"
        "\n    taken shape')."
        "\n  - Awareness of timing — but NOT philosophical or vague."
        "\n  - Prefer reflective verbs where natural: notice, sense,"
        "\n    register, recognise, let, see."
        "\n  - Stay grounded. Never drift into abstraction."
    ),
}


def build_decan_addendum(decan_index: int) -> str:
    """
    Return the prompt suffix to append to an engine's existing system
    prompt. Returns "" for invalid indices so callers can ALWAYS append
    safely.
    """
    if not isinstance(decan_index, int):
        return ""
    return _DECAN_PROMPT_ADDENDA.get(decan_index, "")


def get_decan_tone_label(decan_index: int) -> str:
    """Returns the (internal-only) tone label for debug/logging."""
    p = _DECAN_TONE.get(decan_index) if isinstance(decan_index, int) else None
    return p.get("label") if isinstance(p, dict) else "unknown"


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

# Sentence-end splitter (greedy enough for the conversational style we use).
_SENT_SPLIT_RX = re.compile(r"(?<=[.!?…])\s+(?=[A-Z\"'])")


def _sentences(text: str) -> List[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    parts = _SENT_SPLIT_RX.split(text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def _avg_sentence_length(text: str) -> Optional[float]:
    """Average words per sentence. None if no sentences."""
    sents = _sentences(text)
    if not sents:
        return None
    word_counts = [len(re.findall(r"\b\w+\b", s)) for s in sents]
    word_counts = [c for c in word_counts if c > 0]
    if not word_counts:
        return None
    return statistics.mean(word_counts)


def audit_decan_tone(text: str, decan_index: int) -> Dict[str, Any]:
    """
    Soft-pass audit on the polished output. Returns:
      {
        "pass":       bool,         # True if tone target is met (or close)
        "reasons":    [str, ...],   # why it failed
        "avg_len":    float | None,
        "expected":   (lo, hi),     # tolerant pass band
        "decan":      int,
        "tone_label": str,
      }

    Per spec: "If decan layer makes it worse → DISCARD". Callers should
    treat pass=False as a signal to KEEP the pre-decan version. We
    intentionally use a TOLERANT band (not the target band) — tone
    polishing is supposed to be subtle, not radical, so we only flag
    when the output is wildly off.
    """
    profile = _DECAN_TONE.get(decan_index) if isinstance(decan_index, int) else None
    if not profile:
        return {"pass": True, "reasons": ["no_profile"], "avg_len": None,
                "expected": None, "decan": decan_index, "tone_label": "unknown"}

    avg = _avg_sentence_length(text or "")
    lo, hi = profile["len_audit"]
    reasons: List[str] = []
    ok = True

    if avg is None:
        # Empty text — irrelevant to tone, treat as pass.
        return {"pass": True, "reasons": ["empty_text"], "avg_len": None,
                "expected": (lo, hi), "decan": decan_index,
                "tone_label": profile["label"]}

    if avg < lo:
        ok = False
        reasons.append(f"avg_sentence_too_short ({avg:.1f} < {lo})")
    elif avg > hi:
        ok = False
        reasons.append(f"avg_sentence_too_long ({avg:.1f} > {hi})")

    return {
        "pass":       ok,
        "reasons":    reasons,
        "avg_len":    round(avg, 2),
        "expected":   (lo, hi),
        "decan":      decan_index,
        "tone_label": profile["label"],
    }


# ---------------------------------------------------------------------------
# Convenience: full debug payload for an engine to surface in `debug`
# ---------------------------------------------------------------------------

def decan_debug(text: str, decan_index: int) -> Dict[str, Any]:
    """Compact debug block for engines that want to expose tone state."""
    audit = audit_decan_tone(text, decan_index)
    return {
        "decan_index":   decan_index,
        "tone_label":    audit.get("tone_label"),
        "avg_sentence":  audit.get("avg_len"),
        "audit_pass":    audit.get("pass"),
        "audit_reasons": audit.get("reasons"),
    }
