"""
Cross-Lens Synthesis Atoms — V1
================================
Build marker: cross-lens-atoms-v1

Detects small, deterministic "atoms" of convergence across multiple
symbolic systems (Human Design, Astrology, Numerology). An atom is
surfaced ONLY when ALL required signals match — never partial fits,
never LLM-generated. The first atom shipped is the "Certainty Pattern".

Tone rules (enforced):
  * Recognition-first ("You tend to..."), not framework-first
    ("Your Ajna is defined so...").
  * No pathologizing of Open centers, no fortune-telling, no
    grand "master synthesis" prose.
  * Each signal carries a short, lived sentence describing how it
    shows up — not a definition of the framework.

Public surface:
  compute_atoms(chart: dict) -> List[dict]
      Runs every registered detector and returns the matched atoms.
      Live computation only — no caching at this layer.

Each atom dict:
  {
    "atom_id":      "certainty_pattern",
    "name":         "Certainty Pattern",
    "recognition":  "<one-line lived statement>",
    "framing":      "<short subtitle for the card>",
    "signals":      [ {lens, label, evidence}, ... ],   # ordered HD, HD, Astro, Numerology
    "matched":      4,
    "required":     4,
    "match_mode":   "strict_all"
  }
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

BUILD_MARKER = "cross-lens-atoms-v1"

# Aspects considered "hard contacts" between Mercury and Saturn for the
# Certainty Pattern. Trines and sextiles are intentionally excluded —
# the pattern hinges on the *friction* between thought and weight.
_MERCURY_SATURN_HARD_ASPECTS = {"conjunction", "square", "opposition"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_lower(s: Any) -> str:
    return str(s).strip().lower() if s is not None else ""


def _has_defined_ajna(hd: Dict[str, Any]) -> bool:
    centers = hd.get("defined_centers") or []
    return any(_safe_lower(c) == "ajna" for c in centers)


def _active_gates(hd: Dict[str, Any]) -> set:
    raw = hd.get("active_gates") or hd.get("all_gates") or []
    out = set()
    for g in raw:
        try:
            out.add(int(g))
        except (TypeError, ValueError):
            continue
    return out


def _mercury_saturn_aspect(astro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the tightest Mercury<->Saturn hard aspect, or None."""
    aspects = astro.get("aspects") or []
    best: Optional[Dict[str, Any]] = None
    for asp in aspects:
        if not isinstance(asp, dict):
            continue
        b1 = _safe_lower(asp.get("body1"))
        b2 = _safe_lower(asp.get("body2"))
        pair = {b1, b2}
        if pair != {"mercury", "saturn"}:
            continue
        atype = _safe_lower(asp.get("type"))
        if atype not in _MERCURY_SATURN_HARD_ASPECTS:
            continue
        if best is None or asp.get("orb", 99) < best.get("orb", 99):
            best = asp
    return best


def _life_path_number(numerology: Dict[str, Any]) -> Optional[int]:
    """Pulls the Life Path number from the canonical numerology payload."""
    if not numerology:
        return None
    # Canonical path: numerology.core.life_path.number
    core = numerology.get("core") or {}
    lp = core.get("life_path") or {}
    n = lp.get("number")
    if n is None:
        # Legacy: numerology.life_path.number
        lp_legacy = numerology.get("life_path") or {}
        n = lp_legacy.get("number")
    if n is None:
        return None
    try:
        return int(n)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Detector: Certainty Pattern
# ---------------------------------------------------------------------------
def detect_certainty_pattern(chart: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Strict ALL-4 detector for the 'Certainty Pattern' atom.

    Required signals:
      1. HD: Defined Ajna
      2. HD: Gate 4 (Answers) OR Gate 63 (Doubt) in active gates
      3. Astro: Mercury <-> Saturn conjunction/square/opposition
      4. Numerology: Life Path 7
    """
    if not isinstance(chart, dict):
        return None

    hd = chart.get("human_design") or {}
    astro = chart.get("astrology") or {}
    num = chart.get("numerology") or {}

    if not _has_defined_ajna(hd):
        return None

    gates = _active_gates(hd)
    has_g4 = 4 in gates
    has_g63 = 63 in gates
    if not (has_g4 or has_g63):
        return None

    aspect = _mercury_saturn_aspect(astro)
    if aspect is None:
        return None

    lp = _life_path_number(num)
    if lp != 7:
        return None

    # All 4 matched — build signals (HD center, HD gate(s), Astro, Numerology).
    if has_g4 and has_g63:
        gate_label = "Gates 4 & 63 — Answers & Doubt"
        gate_evidence = (
            "You carry both the drive to give an answer and the instinct to "
            "doubt it. They argue with each other inside the same thought."
        )
    elif has_g4:
        gate_label = "Gate 4 — Answers"
        gate_evidence = (
            "You're the one who reaches for an answer when things feel "
            "uncertain — even before you've fully worked it out."
        )
    else:
        gate_label = "Gate 63 — Doubt"
        gate_evidence = (
            "You question the answer the moment it lands. Doubt is the way "
            "your mind double-checks reality."
        )

    aspect_type = _safe_lower(aspect.get("type")).capitalize()
    orb = aspect.get("orb")
    try:
        orb_txt = f"{float(orb):.1f}°"
    except (TypeError, ValueError):
        orb_txt = "tight"

    astro_label = f"Mercury {aspect_type} Saturn ({orb_txt})"
    astro_evidence = (
        "How you think is shaped by patience and weight. Answers don't come "
        "fast for you — but the ones that hold, hold for a long time."
    )

    signals: List[Dict[str, str]] = [
        {
            "lens": "Human Design",
            "label": "Defined Ajna",
            "evidence": (
                "Your Ajna is consistent — once you land on a way of seeing "
                "something, it stays. Others borrow that certainty from you, "
                "which can quietly raise the stakes on getting it right."
            ),
        },
        {
            "lens": "Human Design",
            "label": gate_label,
            "evidence": gate_evidence,
        },
        {
            "lens": "Astrology",
            "label": astro_label,
            "evidence": astro_evidence,
        },
        {
            "lens": "Numerology",
            "label": "Life Path 7",
            "evidence": (
                "Your path leans toward analysis and inner verification. "
                "Easy answers don't satisfy — you want the one that survives "
                "your own scrutiny."
            ),
        },
    ]

    return {
        "atom_id": "certainty_pattern",
        "name": "Certainty Pattern",
        "framing": "Where different systems point to the same thing.",
        "recognition": (
            "You tend to look for certainty under pressure — and to doubt "
            "the answer the moment you've found one."
        ),
        "signals": signals,
        "matched": 4,
        "required": 4,
        "match_mode": "strict_all",
    }


# ---------------------------------------------------------------------------
# Registry + public entry point
# ---------------------------------------------------------------------------
# Order matters for display: first match in this list is shown first.
_DETECTORS = [
    detect_certainty_pattern,
]


def compute_atoms(chart: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run every registered atom detector against the user's chart.

    Returns an ordered list of matched atoms. Atoms that fail any required
    signal are silently omitted — there is no "partial" surface yet.
    """
    if not chart:
        return []

    matched: List[Dict[str, Any]] = []
    for detector in _DETECTORS:
        try:
            atom = detector(chart)
        except Exception as e:  # noqa: BLE001 - never let one bad detector kill the rest
            logger.warning(
                f"[CrossLensAtoms] detector {detector.__name__} raised: {e}"
            )
            continue
        if atom:
            matched.append(atom)
    return matched
