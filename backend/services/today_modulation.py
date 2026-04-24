"""
Today Modulation Engine — Phase 2 (continued)
=============================================

Does NOT generate a new daily pattern. It MODULATES the existing domain
synthesis based on today's intensity. Same pattern — just stronger or
softer.

Rules (from user's spec):

INTENSITY LEVELS:
  low      — very subtle, light presence markers; do not emphasize distortion.
             tone: "this may feel slightly more present today"
  medium   — noticeable tension; emphasize difficulty of shifting.
             tone: "this may feel harder to step away from today",
                   "this pull may be stronger than usual"
  high     — active pattern; emphasize speed of escalation toward distortion.
             tone: "this can turn more quickly than usual today",
                   "this may become something you carry faster than expected"

CRITICAL:
  - no urgency language
  - no advice
  - not a warning system
  - always describe acceleration/amplification of the SAME pattern

PRIORITY (modulation focus):
  medium: distortion (primary), tension (secondary), pattern (optional), needs (minimal)
  high:   distortion (primary), tension (secondary), pattern (optional), needs (minimal)

OUTPUT CONTRACT:
  {
    "intensity_level": "low|medium|high",
    "pattern":                   str,
    "default_tension":           str,
    "distortion_under_pressure": str,
    "what_this_pattern_needs":   str,
  }
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .life_synthesis_engine import scrub_banned_phrases

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intensity calculation — deterministic, degrades gracefully
# ---------------------------------------------------------------------------

def determine_intensity(
    pattern_memory: Optional[Dict[str, Any]] = None,
    transit_hits: Optional[List[Dict[str, Any]]] = None,
    lifeline_recent: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, List[str]]:
    """
    Simple, honest intensity heuristic. Returns (level, reasons).

    Default is 'low'. Bumps to 'medium' / 'high' when the pattern is clearly
    active: repeated cycling state, lots of recent lifeline activity, or
    strong transit hits on the primary domain axis.
    """
    score = 0
    reasons: List[str] = []

    if isinstance(pattern_memory, dict):
        mc = pattern_memory.get("match_count") or 0
        state = (pattern_memory.get("memory_state") or pattern_memory.get("state") or "").lower()
        if state == "recurring_pattern" and mc >= 3:
            score += 2
            reasons.append("pattern is cycling")
        elif state == "recurring_pattern":
            score += 1
            reasons.append("pattern has recurred recently")
        elif state == "new_pattern":
            score += 1
            reasons.append("pattern is newly visible")

    if isinstance(transit_hits, list) and transit_hits:
        # crude: 1 hit = +1 score, cap at +2
        score += min(len(transit_hits), 2)
        reasons.append("active timing hits on domain axis")

    if isinstance(lifeline_recent, list) and len(lifeline_recent) >= 3:
        score += 1
        reasons.append("recent lived events echo the pattern")

    if score >= 3:
        return "high", reasons
    if score >= 1:
        return "medium", reasons
    return "low", reasons


# ---------------------------------------------------------------------------
# LLM prompt — intensity-aware modulation
# ---------------------------------------------------------------------------

_TODAY_SYSTEM_PROMPT = """You are the Mirror Today Modulator.

You do NOT invent a new pattern. You MODULATE the existing domain synthesis
based on today's intensity level. Same pattern — just stronger or softer.

==================================================
INPUT
==================================================

You receive:
  domain            (self | work | relationships)
  intensity_level   (low | medium | high)
  role_card         (role / tension / distortion / orientation)
  domain_synthesis  (pattern / default_tension / distortion_under_pressure /
                     what_this_pattern_needs)

==================================================
OUTPUT
==================================================

Return ONLY valid JSON:

{
  "intensity_level": "low|medium|high",
  "pattern":                   "...",
  "default_tension":           "...",
  "distortion_under_pressure": "...",
  "what_this_pattern_needs":   "..."
}

No extra keys. No markdown. No explanation.

==================================================
INTENSITY SCALING RULES
==================================================

LOW
  - Very subtle. Add light presence markers.
  - Do NOT emphasise distortion strongly.
  - Allowed tone: "This may feel slightly more present today"

MEDIUM
  - Noticeable tension.
  - Emphasise difficulty in shifting patterns.
  - Allowed tone: "This may feel harder to step away from today",
                  "This pull may be stronger than usual"

HIGH
  - Active pattern.
  - Emphasise speed of escalation toward distortion.
  - Allowed tone: "This can turn more quickly than usual today",
                  "This may become something you carry faster than expected"

==================================================
CRITICAL
==================================================

Do NOT:
  - introduce urgency language
  - give advice
  - sound like a warning system
  - invent new ideas not in the source synthesis

Always:
  - describe acceleration or amplification of the SAME pattern
  - preserve the domain's existing tone and vocabulary
  - stay in second person

==================================================
PRIORITY (at MEDIUM and HIGH)
==================================================

Primary focus:  distortion_under_pressure — modulate most strongly
Secondary:      default_tension
Optional:       pattern — minor echo
Minimal:        what_this_pattern_needs — only light presence touch

At LOW: modulate all four very lightly; do not push distortion.

==================================================
OTHER RULES
==================================================

  - No framework names (chart, lens, system, astrology, human design, bazi,
    enneagram, numerology, manifestor, projector, generator, reflector,
    transit, day master, authority, life path).
  - No generic language: "dynamic blend", "recurring theme", "invites growth",
    "this suggests", "you may find", "in many ways", "tends to" without a
    concrete behavior, "multiple perspectives".
  - Each field: 1-2 sentences max. Stay tight.
  - Same behaviour as the source — do NOT introduce a different pattern.

==================================================
FINAL CHECK
==================================================

Ensure:
  - tone matches intensity_level
  - no new ideas introduced
  - same pattern, just stronger/weaker
  - at medium/high, distortion carries the weight; needs stays light

If not, rewrite internally.
"""


def _build_today_user_message(
    domain: str,
    intensity_level: str,
    role_card: Dict[str, Any],
    domain_synthesis: Dict[str, Any],
) -> str:
    payload = {
        "domain":           domain,
        "intensity_level":  intensity_level,
        "role_card": {
            "role":        role_card.get("role"),
            "tension":     role_card.get("tension"),
            "distortion":  role_card.get("distortion"),
            "orientation": role_card.get("orientation"),
        },
        "domain_synthesis": {
            "pattern":                   domain_synthesis.get("pattern"),
            "default_tension":           domain_synthesis.get("default_tension"),
            "distortion_under_pressure": domain_synthesis.get("distortion_under_pressure"),
            "what_this_pattern_needs":   domain_synthesis.get("what_this_pattern_needs"),
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _parse_today_json(raw: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    hits: List[str] = []
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, ["no_json_detected"]
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, ["json_parse_error"]
    for k in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = payload.get(k)
        if isinstance(v, str):
            cleaned, new_hits = scrub_banned_phrases(v)
            payload[k] = cleaned
            hits.extend(new_hits)
    return payload, hits


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

async def generate_today_modulation(
    *,
    domain: str,
    role_card: Dict[str, Any],
    domain_synthesis: Dict[str, Any],
    pattern_memory: Optional[Dict[str, Any]] = None,
    transit_hits: Optional[List[Dict[str, Any]]] = None,
    lifeline_recent: Optional[List[Dict[str, Any]]] = None,
    llm_chat_factory=None,
) -> Dict[str, Any]:
    """
    End-to-end Today modulation. ONE LLM call. Falls back to a light
    deterministic paraphrase if the LLM is unavailable.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local import

    intensity_level, reasons = determine_intensity(
        pattern_memory=pattern_memory,
        transit_hits=transit_hits,
        lifeline_recent=lifeline_recent,
    )

    user_msg = _build_today_user_message(domain, intensity_level, role_card, domain_synthesis)

    llm_output: Optional[str] = None
    render_error: Optional[str] = None
    banned_hits: List[str] = []

    if llm_chat_factory is None:
        render_error = "no_llm_factory"
    else:
        try:
            chat: LlmChat = llm_chat_factory()
            resp = await chat.send_message(UserMessage(text=user_msg))
            llm_output = resp if isinstance(resp, str) else str(resp)
        except Exception as e:
            logger.exception("[TodayModulation] LLM render failed")
            render_error = f"llm_render_error: {e}"

    payload: Optional[Dict[str, Any]] = None
    if llm_output:
        payload, banned_hits = _parse_today_json(llm_output)

    if not payload or not payload.get("distortion_under_pressure"):
        # Lightweight deterministic fallback — paraphrase the original with
        # an intensity marker at the front, no invention.
        marker = {
            "low":    "Today this may feel slightly more present.",
            "medium": "Today this pull may be stronger than usual.",
            "high":   "Today this can turn more quickly than usual.",
        }[intensity_level]
        payload = {
            "pattern":                   f"{marker} {domain_synthesis.get('pattern', '')}".strip(),
            "default_tension":           domain_synthesis.get("default_tension", ""),
            "distortion_under_pressure": domain_synthesis.get("distortion_under_pressure", ""),
            "what_this_pattern_needs":   domain_synthesis.get("what_this_pattern_needs", ""),
        }

    return {
        "domain":                     domain,
        "intensity_level":            intensity_level,
        "intensity_reasons":          reasons,
        "pattern":                    payload.get("pattern", ""),
        "default_tension":            payload.get("default_tension", ""),
        "distortion_under_pressure":  payload.get("distortion_under_pressure", ""),
        "what_this_pattern_needs":    payload.get("what_this_pattern_needs", ""),
        "debug": {
            "llm_used":           llm_output is not None,
            "render_error":       render_error,
            "banned_phrase_hits": banned_hits,
        },
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "generator_version":  "today_modulation_v1",
    }
