"""
Mirror Evidence Layer — Phase 2
================================

Powers the "Why this is showing up" expander. Takes the deterministic signal
bundle from the life synthesis engine and produces 3-5 human, behavioural
explanations of where the pattern comes from. Never mentions framework names.

Input:
  domain             (self | work | relationships)
  role_card          (rendered — role / tension / distortion / orientation / not_for)
  domain_synthesis   (rendered — pattern / default_tension / distortion / needs)
  evidence_signals   (raw: lens + signal + weight)

Output (strict JSON):
  { "evidence": [ { "title": "...", "explanation": "..." }, ... ] }
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .life_synthesis_engine import scrub_banned_phrases

logger = logging.getLogger(__name__)


_EVIDENCE_SYSTEM_PROMPT = """You are the Mirror Evidence Layer.

Your role is NOT to explain the system.

Your role is to:
- show where the pattern comes from
- anchor it in recognizable signals
- deepen trust without overwhelming the user

==================================================
OUTPUT STRUCTURE
==================================================

Return ONLY valid JSON:

{
  "evidence": [
    { "title": "...", "explanation": "..." }
  ]
}

No extra keys. No markdown.

==================================================
CORE PRINCIPLE
==================================================

This is NOT a technical breakdown.
It should feel like: "These are the parts of you creating this pattern."
NOT: "Here is how the system calculated this."

==================================================
SELECTION RULES
==================================================

1. Select ONLY the top 3-5 strongest signals by weight.
2. Each evidence item must:
   - clearly connect to the pattern
   - feel recognizable to the user
   - be grounded in behavior (not abstract traits)
3. Do NOT include weak or redundant signals.

==================================================
WRITING RULES
==================================================

1. HUMAN, NOT TECHNICAL.
   Bad:  "Your type indicates..."
   Good: "You tend to move first, without waiting for others to respond."

2. CONNECT DIRECTLY TO THE PATTERN.
   Every explanation must tie back to the domain pattern.

3. SHORT AND CLEAR.
   Each item: 1-2 sentences max. No fluff. No repetition.

4. NO JARGON. Never mention:
   "Human Design", "BaZi", "transits", "numerology", "pattern memory",
   "astrology", "chart", "lens", "system", "day master", "authority",
   "manifestor", "projector", "generator", "reflector", "life path".

5. DIFFERENTIATE THE SIGNALS.
   Each item a different "angle":
   - one about action style
   - one about emotional pattern
   - one about timing or cycles
   - one about past repetition (if available)

6. NO ADVICE. Do NOT say "you should", "you need to".
   Only describe what is already happening and why it feels familiar.

7. AVOID GENERIC LANGUAGE.
   Never: "this suggests", "you may find", "in many ways",
   "a dynamic blend", "invites growth", "tends to" (unless followed by a
   concrete behaviour), "recurring theme", "multiple perspectives".

==================================================
TONE
==================================================

Tone: quiet clarity. Grounded. Matter-of-fact. Slightly revealing.
NOT inspirational. NOT mystical. NOT analytical. NOT explanatory.

==================================================
EXAMPLE STYLE (REFERENCE ONLY, do not copy)
==================================================

[
  {
    "title": "You tend to move first",
    "explanation": "You initiate quickly, which is why you often find yourself ahead of others before they have a chance to respond."
  },
  {
    "title": "You hold what you start",
    "explanation": "Once you begin something, you tend to carry it forward yourself, even when it was only meant to be a starting point."
  },
  {
    "title": "This pattern has repeated",
    "explanation": "You've seen this cycle before — starting with momentum, then feeling the weight of what you created."
  }
]

==================================================
FINAL CHECK
==================================================

Before returning, ensure:
- Each item is clear and grounded.
- No system names mentioned.
- Each explanation connects to the pattern.
- The list feels cohesive but not repetitive.

If not, rewrite internally.

==================================================
FINAL RULE
==================================================

Do not explain how the system works.
Just show the pieces of the user that make the pattern make sense.
"""


def _build_evidence_user_message(
    domain: str,
    role_card: Dict[str, Any],
    domain_synthesis: Dict[str, Any],
    evidence_signals: List[Dict[str, Any]],
) -> str:
    """Send the engine everything it needs — strictly as input, not for repetition."""
    # Trim & sort signals by weight; pass top 6 (engine will pick 3-5)
    cleaned_signals = [
        {"lens": s.get("lens"), "signal": s.get("signal"), "weight": s.get("weight")}
        for s in (evidence_signals or [])
        if isinstance(s, dict) and s.get("signal")
    ]
    cleaned_signals.sort(key=lambda x: (x.get("weight") or 0), reverse=True)
    cleaned_signals = cleaned_signals[:6]

    payload = {
        "domain": domain,
        "role_card": {
            "role":        role_card.get("role"),
            "tension":     role_card.get("tension"),
            "distortion":  role_card.get("distortion"),
            "orientation": role_card.get("orientation"),
        },
        "domain_synthesis": {
            "pattern":                  domain_synthesis.get("pattern"),
            "default_tension":          domain_synthesis.get("default_tension"),
            "distortion_under_pressure": domain_synthesis.get("distortion_under_pressure"),
            "what_this_pattern_needs":  domain_synthesis.get("what_this_pattern_needs"),
        },
        "evidence_signals": cleaned_signals,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _parse_evidence_json(raw: str) -> Tuple[Optional[List[Dict[str, str]]], List[str]]:
    """Parse + scrub. Returns (evidence_list, banned_hits)."""
    hits: List[str] = []
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, ["no_json_detected"]
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, ["json_parse_error"]

    items = payload.get("evidence") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return None, ["missing_evidence_list"]

    cleaned: List[Dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("title", "")
        expl = item.get("explanation", "")
        if not isinstance(title, str) or not isinstance(expl, str):
            continue
        t_clean, t_hits = scrub_banned_phrases(title)
        e_clean, e_hits = scrub_banned_phrases(expl)
        hits.extend(t_hits)
        hits.extend(e_hits)
        if t_clean and e_clean:
            cleaned.append({"title": t_clean, "explanation": e_clean})

    return cleaned[:5], hits


def _deterministic_fallback(
    evidence_signals: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Used only when the LLM is unavailable. Human-language mapping by lens."""
    lens_phrase_map: Dict[str, Dict[str, str]] = {
        "operating_style": {
            "title": "You move on your own signal",
            "explanation": "You tend to initiate before consensus — which is why you often find yourself ahead of others.",
        },
        "structural_posture": {
            "title": "You carry a steady posture",
            "explanation": "Once you take a position, you hold it — which is why the same stance can become weight over time.",
        },
        "domain_field": {
            "title": "This domain is lit up for you",
            "explanation": "The part of your life where this pattern shows up has real intensity right now.",
        },
        "pattern_memory": {
            "title": "This pattern has repeated",
            "explanation": "You've moved through a version of this before — the edges are familiar.",
        },
        "lifeline_echoes": {
            "title": "The echoes are there",
            "explanation": "Earlier moments in your story have the same shape underneath.",
        },
    }
    out: List[Dict[str, str]] = []
    for sig in (evidence_signals or [])[:4]:
        lens = sig.get("lens")
        phrase = lens_phrase_map.get(lens)
        if phrase and phrase not in out:
            out.append(dict(phrase))
    return out[:4]


async def generate_evidence_layer(
    *,
    domain: str,
    role_card: Dict[str, Any],
    domain_synthesis: Dict[str, Any],
    evidence_signals: List[Dict[str, Any]],
    llm_chat_factory=None,
) -> Dict[str, Any]:
    """End-to-end evidence layer generation. ONE LLM call. Graceful fallback."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local

    user_msg = _build_evidence_user_message(domain, role_card, domain_synthesis, evidence_signals)

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
            logger.exception("[EvidenceLayer] LLM render failed")
            render_error = f"llm_render_error: {e}"

    items: Optional[List[Dict[str, str]]] = None
    if llm_output:
        items, banned_hits = _parse_evidence_json(llm_output)

    if not items:
        items = _deterministic_fallback(evidence_signals)

    return {
        "domain":   domain,
        "evidence": items,
        "debug": {
            "llm_used":           llm_output is not None,
            "render_error":       render_error,
            "banned_phrase_hits": banned_hits,
            "signals_considered": len(evidence_signals or []),
        },
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "generator_version":  "evidence_layer_v1",
    }
