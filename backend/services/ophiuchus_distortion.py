"""
Ophiuchus Distortion Layer — Contextual Injection Helper
=========================================================

Ophiuchus is NOT a feature. It's a distortion layer.

This module decides — for each core surface (Astrology Today / Home /
Forum Mappings) — whether the current moment has BOTH of these:

  1. has_ophiuchus        — the user (or a forum counterpart) has at least
                            one body in the IAU Ophiuchus region.
  2. distortion_context   — the present narrative already has something
                            unstable, conflicting, or hard to read cleanly
                            (Neptune aspects, push/hesitation, clarity/doubt
                            tension, multi-planet friction without clean
                            resolution, or a forum misread/projection).

Only when BOTH are true do we inject a short 1–2 line "reality vs model"
pointer — subtly, inside an existing section. No new UI. No new cards.
No mention of the word "Ophiuchus" outside the dedicated overlay card.

Public API:
    check_today(user_id, natal_astro, today_insight) -> dict
    check_home(user_id, natal_astro, home_grounded)  -> dict
    check_forum_pair(user_astro, other_astro, patterns) -> dict

Each returns:
    {
      "inject": bool,
      "reason": str,               # diagnostic, not shown to user
      "happening_line": str|None,  # 1 line for "what's actually happening"
      "move_line":     str|None,   # optional line for "the move"
      "home_line":     str|None,   # 1 line for Home narrative body
      "forum_line":    str|None,   # 1 bullet for "what happens between you"
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from .iau_constellations import resolve_constellation_overlay
except ImportError:  # pragma: no cover — allow direct module loading
    from services.iau_constellations import resolve_constellation_overlay


# ---------------------------------------------------------------------------
# One-liners — kept deliberately short, experiential, not astronomical.
# Never use the word "Ophiuchus" here; that word lives ONLY in the overlay
# card. These are about the FEEL of the distortion layer.
# ---------------------------------------------------------------------------

TODAY_HAPPENING_LINES = [
    "There's also a distortion layer here — part of what you're reading isn't landing cleanly.",
    "What you're feeling is real — but not all of it is coming through clearly.",
]

TODAY_HAPPENING_LINE_NEPTUNE = (
    "You may be reading something accurately — but not in a way that can be "
    "confirmed yet."
)

TODAY_MOVE_LINE = "The pressure is real. The clarity might not be."

HOME_LINES = [
    "This may not feel clean or fully clear — and that's part of what's happening, not a mistake.",
    "Part of why this keeps repeating is that it doesn't resolve cleanly.",
]

FORUM_LINES = [
    "You may both feel something real between you — but not interpret it the same way.",
    "There's a tendency to read each other correctly and still come to different conclusions.",
    "What's happening between you doesn't always land in a way either of you can fully explain.",
]


# ---------------------------------------------------------------------------
# Ophiuchus detection (cheap — reads the already-computed chart or recomputes)
# ---------------------------------------------------------------------------

def has_ophiuchus_placement(astrology_chart: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Return (has_ophiuchus, [body_names])."""
    if not astrology_chart:
        return False, []
    # Prefer precomputed overlay when present on the chart doc
    precomputed = astrology_chart.get("constellations")
    if precomputed and isinstance(precomputed, dict) and precomputed.get("ophiuchus_bodies") is not None:
        bodies = precomputed.get("ophiuchus_bodies") or []
        return bool(bodies), list(bodies)
    # Compute on the fly (cheap)
    overlay = resolve_constellation_overlay(astrology_chart)
    bodies = overlay.get("ophiuchus_bodies") or []
    return bool(bodies), list(bodies)


# Luminaries + personal planets we care about most for divergence
CORE_BODIES_FOR_DIVERGENCE = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant")


# Canonical name map — maps IAU constellation names to their zodiac-sign equivalents.
# These are *not* considered divergent when only the label differs.
_CONSTELLATION_ZODIAC_EQUIVALENTS = {
    "Scorpius": "Scorpio",
    "Capricornus": "Capricorn",
    "Aquarius": "Aquarius",
    "Pisces": "Pisces",
    "Aries": "Aries",
    "Taurus": "Taurus",
    "Gemini": "Gemini",
    "Cancer": "Cancer",
    "Leo": "Leo",
    "Virgo": "Virgo",
    "Libra": "Libra",
    "Sagittarius": "Sagittarius",
    # Ophiuchus deliberately has NO zodiac equivalent.
}


def _is_true_divergence(zodiac_sign: str, constellation: str) -> bool:
    """True only when the constellation genuinely doesn't match the zodiac sign,
    after normalizing IAU name variants (Scorpius<->Scorpio, Capricornus<->Capricorn)."""
    if not zodiac_sign or not constellation:
        return False
    canonical = _CONSTELLATION_ZODIAC_EQUIVALENTS.get(constellation, constellation)
    return canonical != zodiac_sign


def has_constellation_divergence(astrology_chart: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Returns (has_divergence, [{body, zodiac_sign, constellation}, ...])
    for each CORE body whose zodiac_sign != constellation (after normalizing
    IAU name variants).

    This is the general "reality vs model" check — it's a softer distortion
    than Ophiuchus alone, but still qualifies as a distortion flag.
    """
    if not astrology_chart:
        return False, []
    overlay = astrology_chart.get("constellations")
    if not (overlay and isinstance(overlay, dict) and overlay.get("bodies")):
        overlay = resolve_constellation_overlay(astrology_chart)
    bodies = (overlay or {}).get("bodies") or {}
    divergent: List[Dict[str, str]] = []
    for body_name in CORE_BODIES_FOR_DIVERGENCE:
        entry = bodies.get(body_name)
        if not entry:
            continue
        zodiac = entry.get("zodiac_sign") or ""
        constellation = entry.get("constellation") or ""
        if _is_true_divergence(zodiac, constellation):
            divergent.append({
                "body": body_name,
                "zodiac_sign": zodiac,
                "constellation": constellation,
            })
    return bool(divergent), divergent


# ---------------------------------------------------------------------------
# Distortion context detection — per surface
# ---------------------------------------------------------------------------

NEPTUNE_TAG_HINTS = ("neptune", "confusion", "fog", "dissolve", "illusion")
CONFLICT_TAG_HINTS = (
    "conflict", "clash", "tension", "friction", "unresolved", "destabilizer",
    "disrupt", "sudden", "shift", "inflat", "pressure", "identity-disrupt",
    "action-heavy", "heavy", "destabil", "reactive",
)
NARRATIVE_DISTORTION_WORDS = (
    "sudden", "disrupt", "destabil", "inflat", "bigger than warranted",
    "reactive", "off", "unclear", "fog", "can't tell", "doubt",
    "conflict", "tension", "push-pull", "split", "pulled",
)


def _has_neptune_in_today(today_insight: Dict[str, Any]) -> bool:
    if not today_insight:
        return False
    tech = today_insight.get("technical") or {}
    text_blobs: List[str] = []
    for key in ("aspects", "signals", "layers", "destabilizer", "amplifier", "foreground"):
        val = tech.get(key)
        if isinstance(val, list):
            text_blobs += [str(v) for v in val]
        elif isinstance(val, dict):
            text_blobs += [str(v) for v in val.values()]
        elif val:
            text_blobs.append(str(val))
    # Also check plain narrative
    for key in ("whats_happening", "how_it_shows_up", "what_it_feels_like"):
        val = today_insight.get(key)
        if isinstance(val, list):
            text_blobs += [str(v) for v in val]
        elif isinstance(val, str):
            text_blobs.append(val)
    joined = " ".join(text_blobs).lower()
    return "neptune" in joined


def _today_has_conflict(today_insight: Dict[str, Any]) -> bool:
    if not today_insight:
        return False
    tension_type = str(today_insight.get("tension_type") or "").lower()
    tags_blob = " ".join(today_insight.get("technical", {}).get("tags", []) if isinstance(today_insight.get("technical"), dict) else []).lower()
    combined = f"{tension_type} {tags_blob}"
    return any(h in combined for h in CONFLICT_TAG_HINTS)


def _today_multi_tension(today_insight: Dict[str, Any]) -> bool:
    """Multi-planet tension without clean resolution."""
    if not today_insight:
        return False
    tech = today_insight.get("technical") or {}
    aspects = tech.get("aspects") if isinstance(tech, dict) else None
    if isinstance(aspects, list) and len(aspects) >= 3:
        # count destabilizing aspects (square/opposition keywords)
        hard_count = sum(
            1 for a in aspects
            if any(k in str(a).lower() for k in ("square", "opposition", "conjunction"))
        )
        return hard_count >= 2
    return False


# ---------------------------------------------------------------------------
# Surface 1 — ASTROLOGY TODAY
# ---------------------------------------------------------------------------

def check_today(
    natal_astro: Optional[Dict[str, Any]],
    today_insight: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Decide whether to inject the distortion layer into Astrology Today.

    Returns { inject, reason, happening_line, move_line }.
    """
    result: Dict[str, Any] = {
        "inject": False,
        "reason": "",
        "happening_line": None,
        "move_line": None,
    }
    if not natal_astro or not today_insight:
        result["reason"] = "no_context"
        return result

    has_ophi, bodies = has_ophiuchus_placement(natal_astro)
    has_divergence, divergent = has_constellation_divergence(natal_astro)

    if not has_ophi and not has_divergence:
        result["reason"] = "no_overlay_mismatch"
        return result

    neptune_active = _has_neptune_in_today(today_insight)
    conflict = _today_has_conflict(today_insight)
    multi_tension = _today_multi_tension(today_insight)

    distortion = neptune_active or conflict or multi_tension
    if not distortion:
        result["reason"] = "no_distortion_context"
        return result

    # pick the right line — Ophiuchus wins priority (sharper distortion)
    if neptune_active:
        happening = TODAY_HAPPENING_LINE_NEPTUNE
    elif has_ophi and multi_tension:
        happening = TODAY_HAPPENING_LINES[1]  # "not all of it is coming through clearly"
    elif has_ophi:
        happening = TODAY_HAPPENING_LINES[0]
    else:
        # General divergence — softer wording
        happening = "There's a layer here that doesn't fit neatly — the symbolic read and the actual sky aren't pointing at exactly the same thing."

    result.update(
        {
            "inject": True,
            "reason": (
                f"ophi={bodies} divergent={[d['body'] for d in divergent]} "
                f"neptune={neptune_active} conflict={conflict} multi={multi_tension}"
            ),
            "happening_line": happening,
            # Only include move line when pressure is genuinely high
            "move_line": TODAY_MOVE_LINE if (conflict or multi_tension) else None,
            "has_ophiuchus": has_ophi,
            "ophiuchus_bodies": bodies,
            "has_divergence": has_divergence,
            "divergent_bodies": divergent,
        }
    )
    return result


# ---------------------------------------------------------------------------
# Surface 2 — HOME
# ---------------------------------------------------------------------------

def _home_is_tension_day(home_grounded: Dict[str, Any]) -> bool:
    """True when Home is already reflecting tension / high-intensity / sky-led."""
    if not home_grounded:
        return False
    sources = set((home_grounded.get("distinct_sources") or []))
    # Sky-led = astrology transit is the dominant source
    sky_led = "transit" in sources or "stellium" in sources
    # Intensity proxy: signal count >= 4 AND hook contains tension words
    signal_count = home_grounded.get("signal_count") or 0
    hook = (home_grounded.get("hook") or "").lower()
    recognition = (home_grounded.get("recognition") or "").lower()
    cost = (home_grounded.get("cost") or "").lower()
    tension_words = ("keep", "again", "can't", "won't", "stuck", "rehearsing",
                     "bracing", "clench", "hesitat", "freeze", "friction",
                     "split", "pull", "conflict", "tension")
    has_tension = any(w in f"{hook} {recognition} {cost}" for w in tension_words)
    return sky_led or (signal_count >= 4 and has_tension)


def check_home(
    natal_astro: Optional[Dict[str, Any]],
    home_grounded: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Decide whether to inject a single subtle line into the Home narrative.

    Returns { inject, reason, home_line }.
    """
    result: Dict[str, Any] = {"inject": False, "reason": "", "home_line": None}
    if not natal_astro or not home_grounded:
        result["reason"] = "no_context"
        return result

    has_ophi, bodies = has_ophiuchus_placement(natal_astro)
    if not has_ophi:
        result["reason"] = "no_ophiuchus"
        return result

    if not _home_is_tension_day(home_grounded):
        result["reason"] = "not_tension_day"
        return result

    # Pick "keeps repeating" flavour when the hook/recognition implies
    # recurrence; otherwise the softer "may not feel clean" line.
    hook_low = (home_grounded.get("hook") or "").lower()
    rec_low = (home_grounded.get("recognition") or "").lower()
    recurrence = any(w in f"{hook_low} {rec_low}" for w in ("again", "keep", "same", "once more", "still"))
    line = HOME_LINES[1] if recurrence else HOME_LINES[0]

    result.update({"inject": True, "reason": f"tension_day has_ophi={bodies}", "home_line": line})
    return result


# ---------------------------------------------------------------------------
# Surface 3 — FORUM MAPPING
# ---------------------------------------------------------------------------

def check_forum_pair(
    viewer_astro: Optional[Dict[str, Any]],
    other_astro: Optional[Dict[str, Any]],
    patterns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Decide whether to inject a single bullet into a forum member mapping.

    Condition: at least one of the two people has Ophiuchus AND the pair's
    computed patterns show some kind of misread/tension/projection
    (≥ 2 tensions, OR explicit clarity/doubt wording in either tension).

    Returns { inject, reason, forum_line }.
    """
    result: Dict[str, Any] = {"inject": False, "reason": "", "forum_line": None}

    viewer_ophi, _ = has_ophiuchus_placement(viewer_astro or {})
    other_ophi, _ = has_ophiuchus_placement(other_astro or {})
    if not (viewer_ophi or other_ophi):
        result["reason"] = "no_ophiuchus_on_either_side"
        return result

    tensions = []
    if patterns and isinstance(patterns, dict):
        tensions = patterns.get("tensions") or []
    if not tensions:
        result["reason"] = "no_tensions_to_contextualise"
        return result

    # Misread signal = explicit words suggesting misinterpretation OR ≥2 tensions
    tensions_blob = " ".join(str(t) for t in tensions).lower()
    misread_words = ("mis", "unclear", "assume", "read", "doubt", "confus",
                     "interpret", "project", "unsaid", "silence", "different")
    has_misread = any(w in tensions_blob for w in misread_words)
    enough_tension = len(tensions) >= 2
    if not (has_misread or enough_tension):
        result["reason"] = "tensions_are_clean"
        return result

    # Rotate through 3 options based on tension count, so siblings in the
    # same forum don't all get the exact same line.
    idx = min(len(tensions) - 1, len(FORUM_LINES) - 1)
    result.update(
        {
            "inject": True,
            "reason": f"viewer_ophi={viewer_ophi} other_ophi={other_ophi} tensions={len(tensions)}",
            "forum_line": FORUM_LINES[idx],
        }
    )
    return result
