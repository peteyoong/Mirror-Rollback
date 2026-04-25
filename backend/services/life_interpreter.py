"""
Life Interpreter — "Ask About My Life"
======================================

Conversational layer on top of the Mirror system. Given a user_id, a chip
domain (Self/Work/Money/Relationships/Health/Friends/Family) and a free-text
question, it composes the user's existing engine outputs into a structured
context and asks the LLM for a grounded, phase-aware, consequence-aware
answer.

Outputs PLAIN TEXT only (2-4 paragraphs). No JSON. No system names.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chip-domain mapping
# ---------------------------------------------------------------------------
#
# The user-facing chips are 7 topics, but the backend synthesis stack only
# operates on 3 domains. We keep the chip topic in the LLM prompt verbatim
# (so the answer can speak to "money" / "health" / "family" specifically)
# while pulling synthesis context from the closest matching domain.

_VALID_CHIPS = {
    "self", "work", "money", "relationships", "health", "friends", "family",
}

_CHIP_TO_SYNTH_DOMAIN: Dict[str, str] = {
    "self":          "self",
    "work":          "work",
    "money":         "work",          # closest synthesis input
    "relationships": "relationships",
    "health":        "self",
    "friends":       "relationships",
    "family":        "relationships",
}

# ---------------------------------------------------------------------------
# System prompt (verbatim from spec, with scrubber rules tightened)
# ---------------------------------------------------------------------------

_LIFE_INTERPRETER_SYSTEM_PROMPT = """You are the Mirror Life Interpreter.

You are answering a user's question about their life.

You MUST base your answer ONLY on the provided context.

==================================================
RULES
==================================================

1. Start with recognition
   Show the user you understand their situation.
   Example: "This isn't random — this comes from how you tend to…"

2. Reference pattern
   Explain the behaviour clearly.

3. Reference phase
   Anchor the answer in where they are now.
   Example: "Right now, you're in a phase where…"

4. Show consequence
   Explain what this leads to.

5. Keep it grounded
   No mysticism. No vague generalities. No system names.

6. Do NOT give direct advice
   Instead, show:
     - what's happening
     - what it leads to
     - what's becoming visible

7. Tone
   - calm
   - clear
   - direct
   - slightly confronting when needed

8. Length
   2–4 paragraphs max.

==================================================
ANSWER ABOUT THE EXACT TOPIC THE USER ASKED
==================================================

If the user asks about MONEY, FAMILY, FRIENDS, or HEALTH, your answer must
speak to THAT topic specifically — not a generic substitute. The pattern
context comes from a related synthesis domain, but the language must hit
the user's actual chip.

==================================================
HARD CONSTRAINTS
==================================================

NEVER use the words: "human design", "bazi", "astrology", "horoscope",
"transit", "natal chart", "purple star", "ziwei", "framework", "lifeline",
"pattern memory", "domain weight", "primary domain", "secondary domain",
"background domain", "score", "weighting", "system", "the engine".

NEVER mention you are an AI, a model, an interpreter, or a "mirror".
NEVER predict the future. NEVER prescribe a fix.

==================================================
OUTPUT FORMAT
==================================================

Return PLAIN TEXT only. No JSON. No markdown. No headings. No bullets.
2 to 4 short paragraphs separated by blank lines. No prefix like
"Here's an answer:" — start straight into the recognition.

==================================================
PRINCIPLE
==================================================

You are not predicting. You are helping the user see what is already
happening in their life."""


# ---------------------------------------------------------------------------
# Banned phrase scrubber
# ---------------------------------------------------------------------------

_BANNED_RE = re.compile(
    r"\b(human design|bazi|ba-?zi|astrology|horoscope|natal chart|transit|"
    r"retrograde|purple star|ziwei|framework|lifeline|pattern memory|"
    r"pattern-memory|domain weight|primary domain|secondary domain|"
    r"background domain|domain weighting|weighting|score|the engine|"
    r"the system|mirror|generator|manifestor|projector|reflector|"
    r"day master|profile)\b",
    re.IGNORECASE,
)

_AI_SELF_RE = re.compile(
    r"\b(as an ai|i am an ai|i'm an ai|as a model|as a language model|"
    r"i was trained|my training data|interpreter|i cannot)\b",
    re.IGNORECASE,
)


def _scrub(text: str) -> tuple[str, List[str]]:
    if not text:
        return text, []
    hits: List[str] = []

    def _record(m: re.Match) -> str:
        hits.append(m.group(0))
        return ""

    cleaned = _BANNED_RE.sub(_record, text)
    cleaned = _AI_SELF_RE.sub(_record, cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    return cleaned.strip(), hits


# ---------------------------------------------------------------------------
# Context payload builder
# ---------------------------------------------------------------------------

def _short(s: Optional[str], n: int = 240) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + "…"


def build_context_payload(
    *,
    chip_domain: str,
    question: str,
    role_card: Optional[Dict[str, Any]],
    domain_synthesis: Optional[Dict[str, Any]],
    phase_current: Optional[Dict[str, Any]],
    domain_weights: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
    evidence_signals: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Compose the context the LLM will lean on. Values are kept SHORT to keep
    the prompt focused and to avoid the LLM drifting into list-mode.
    """
    rc: Dict[str, Any] = {}
    if isinstance(role_card, dict):
        rc = {
            "role":        _short(role_card.get("role") or role_card.get("role_seed")),
            "tension":     _short(role_card.get("tension") or role_card.get("tension_seed")),
            "distortion":  _short(role_card.get("distortion") or role_card.get("distortion_seed")),
            "orientation": _short(role_card.get("orientation") or role_card.get("orientation_seed")),
        }

    ds: Dict[str, Any] = {}
    if isinstance(domain_synthesis, dict):
        ds = {
            "pattern":                   _short(domain_synthesis.get("pattern")),
            "default_tension":           _short(domain_synthesis.get("default_tension")),
            "distortion_under_pressure": _short(domain_synthesis.get("distortion_under_pressure")),
            "what_this_pattern_needs":   _short(domain_synthesis.get("what_this_pattern_needs")),
        }

    ph: Dict[str, Any] = {}
    if isinstance(phase_current, dict):
        ph = {
            "label":              _short(phase_current.get("label"), 80),
            "description":        _short(phase_current.get("description")),
            "pattern_expression": _short(phase_current.get("pattern_expression")),
        }

    dw_summary: Optional[str] = None
    if isinstance(domain_weights, dict) and domain_weights.get("dominant_domain"):
        dom = domain_weights.get("dominant_domain")
        # Translate to a hint without exposing weight vocabulary.
        dw_summary = (
            f"the area most actively shaping things right now is {dom}"
            if dom else None
        )

    pm: Dict[str, Any] = {}
    if isinstance(pattern_memory, dict):
        mc = pattern_memory.get("match_count") or 0
        pm = {
            "dominant_tension": _short(pattern_memory.get("dominant_tension"), 100),
            "match_count":      int(mc) if isinstance(mc, (int, float)) else 0,
            "is_recurring":     (pattern_memory.get("memory_state") == "recurring_pattern"),
        }

    ts_intensity: Optional[str] = None
    if isinstance(today_state, dict):
        lvl = today_state.get("intensity_level")
        if lvl in ("low", "medium", "high"):
            ts_intensity = lvl

    # Evidence signals — keep top 3 with no scoring vocabulary
    ev_summary: List[str] = []
    if isinstance(evidence_signals, list):
        for e in evidence_signals[:3]:
            if not isinstance(e, dict):
                continue
            sig = (e.get("signal") or "").strip()
            if sig:
                ev_summary.append(_short(sig, 140))

    return {
        "chip":            chip_domain,
        "question":        _short(question, 600),
        "role_card":       rc,
        "domain_synthesis": ds,
        "current_phase":   ph,
        "active_arena_hint": dw_summary,
        "pattern_memory":  pm,
        "today_intensity": ts_intensity,
        "evidence":        ev_summary,
    }


# ---------------------------------------------------------------------------
# User message builder
# ---------------------------------------------------------------------------

def _format_context_for_llm(ctx: Dict[str, Any]) -> str:
    """
    Render the context as a compact, readable block for the LLM. Plain text,
    not JSON — gpt-4.1-mini handles structured prose better here.
    """
    lines: List[str] = []
    lines.append(f"USER QUESTION (about {ctx['chip']}):")
    lines.append(f'"{ctx["question"]}"')
    lines.append("")
    rc = ctx.get("role_card") or {}
    if rc:
        lines.append("HOW THEY OPERATE:")
        for k in ("role", "tension", "distortion", "orientation"):
            if rc.get(k):
                lines.append(f"  - {k}: {rc[k]}")
        lines.append("")
    ds = ctx.get("domain_synthesis") or {}
    if ds:
        lines.append("PATTERN IN THIS LIFE AREA:")
        for k in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
            if ds.get(k):
                lines.append(f"  - {k}: {ds[k]}")
        lines.append("")
    ph = ctx.get("current_phase") or {}
    if ph:
        lines.append("CURRENT PHASE:")
        for k in ("label", "description", "pattern_expression"):
            if ph.get(k):
                lines.append(f"  - {k}: {ph[k]}")
        lines.append("")
    if ctx.get("active_arena_hint"):
        lines.append(f"WHAT IS MOST ACTIVE: {ctx['active_arena_hint']}.")
        lines.append("")
    pm = ctx.get("pattern_memory") or {}
    if pm.get("is_recurring") and pm.get("dominant_tension"):
        lines.append(
            f"RECURRENCE: the same shape — '{pm['dominant_tension']}' — has "
            f"shown up {pm.get('match_count') or 0} times."
        )
        lines.append("")
    if ctx.get("today_intensity") in ("medium", "high"):
        lines.append(
            f"TODAY: the pattern is more active than usual right now "
            f"(intensity {ctx['today_intensity']})."
        )
        lines.append("")
    ev = ctx.get("evidence") or []
    if ev:
        lines.append("BACKGROUND SIGNALS:")
        for s in ev:
            lines.append(f"  - {s}")
        lines.append("")
    lines.append(
        "Now answer the user's question in 2–4 short paragraphs, plain text "
        "only. Follow all rules above (recognition → pattern → phase → "
        "consequence). Speak directly to the user (you/your). Speak to the "
        f"specific topic they asked about ({ctx['chip']})."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def ask_life_question(
    *,
    chip_domain: str,
    question: str,
    role_card: Optional[Dict[str, Any]],
    domain_synthesis: Optional[Dict[str, Any]],
    phase_current: Optional[Dict[str, Any]],
    domain_weights: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
    evidence_signals: Optional[List[Dict[str, Any]]],
    llm_chat_factory=None,
) -> Dict[str, Any]:
    """
    One LLM call. Returns:
      {
        "answer": "plain text, 2-4 paragraphs",
        "chip_domain": "...",
        "synthesis_domain": "...",
        "generated_at": "...",
        "generator_version": "life_interpreter_v1",
        "debug": {...}
      }
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local

    chip = (chip_domain or "").strip().lower()
    if chip not in _VALID_CHIPS:
        raise ValueError(f"invalid chip_domain: {chip_domain}")

    synth_dom = _CHIP_TO_SYNTH_DOMAIN[chip]

    q = (question or "").strip()
    if not q:
        raise ValueError("question is required")
    if len(q) > 600:
        q = q[:600]

    ctx = build_context_payload(
        chip_domain=chip,
        question=q,
        role_card=role_card,
        domain_synthesis=domain_synthesis,
        phase_current=phase_current,
        domain_weights=domain_weights,
        pattern_memory=pattern_memory,
        today_state=today_state,
        evidence_signals=evidence_signals,
    )
    user_msg = _format_context_for_llm(ctx)

    answer_raw: Optional[str] = None
    render_error: Optional[str] = None
    if llm_chat_factory is not None:
        try:
            chat: LlmChat = llm_chat_factory()
            resp = await chat.send_message(UserMessage(text=user_msg))
            answer_raw = resp if isinstance(resp, str) else str(resp)
        except Exception as e:
            logger.exception("[LifeInterpreter] LLM call failed")
            render_error = f"llm_error: {e}"
    else:
        render_error = "no_llm_factory"

    if not answer_raw:
        # Deterministic fallback — never hard-error the UI
        answer_raw = (
            "This question is touching something that has actually been "
            "moving for a while. The pattern shows up here too, just in a "
            "different shape.\n\n"
            "Right now, what's becoming visible is less about the topic "
            "itself and more about how you usually move when this kind "
            "of pressure shows up. The cost is showing up the same way it "
            "does in other parts of your life.\n\n"
            "What you're starting to notice is the shape of it, not just "
            "the events around it."
        )

    answer, banned_hits = _scrub(answer_raw)

    # Strip leading "Here's...", "Answer:" type prefixes if any sneak through.
    answer = re.sub(
        r"^(here(?:'s| is)\s+(an\s+)?answer\b[:.]?\s*)",
        "",
        answer,
        flags=re.IGNORECASE,
    )
    # Cap to a sane length (defence-in-depth — prompt also limits).
    if len(answer) > 2400:
        answer = answer[:2400].rsplit(" ", 1)[0] + "…"

    return {
        "answer":           answer,
        "chip_domain":      chip,
        "synthesis_domain": synth_dom,
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "generator_version": "life_interpreter_v1",
        "debug": {
            "llm_used":       answer_raw is not None and render_error is None,
            "render_error":   render_error,
            "banned_hits":    banned_hits,
            "context_keys":   {
                "has_role_card":        bool(ctx["role_card"]),
                "has_domain_synthesis": bool(ctx["domain_synthesis"]),
                "has_current_phase":    bool(ctx["current_phase"]),
                "today_intensity":      ctx.get("today_intensity"),
                "is_recurring":         (pattern_memory or {}).get("memory_state") == "recurring_pattern",
                "evidence_count":       len(ctx.get("evidence") or []),
            },
        },
    }
