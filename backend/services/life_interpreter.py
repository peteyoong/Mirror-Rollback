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
OUTPUT FORMAT (CRITICAL)
==================================================

Return a single JSON object with EXACTLY two keys:

{
  "answer":     "2-3 short plain-text paragraphs, separated by an EXPLICIT \\n\\n",
  "follow_ups": ["question 1", "question 2", "question 3"]
}

CRITICAL: the value of "answer" MUST contain at least one literal "\\n\\n"
to separate paragraphs. Each paragraph: 1-3 sentences max.

NO markdown. NO code fences. NO prose before or after the JSON.
"answer" is plain text only — no headings, no bullets.
"follow_ups" must contain 2 or 3 items.

==================================================
ANSWER RULES
==================================================

1. Start with recognition (VARY the opening — don't always use the same phrase).
   Use phrases like:
     - "This isn't random — this comes from how you tend to…"
     - "This connects back to how you tend to…"
     - "What you're noticing comes from…"
     - "This pattern shows up because…"
     - "What's surfacing here is tied to…"
   Pick whichever fits the situation; never use the same opening twice in a row.

2. Reference pattern. Explain the behaviour clearly.

3. Reference phase. Anchor the answer in where they are now.
   Example: "Right now, you're in a phase where…"

4. Show consequence. Explain what this leads to.

5. Keep it grounded. No mysticism. No vague generalities. No system names.

6. Do NOT give direct advice. Show what's happening, what it leads to,
   what's becoming visible.

7. Tone: calm, clear, direct, slightly confronting when needed.

8. Length: 2–4 short paragraphs max.

9. DOMAIN PATTERN ORIGIN (CRITICAL when domain_origin is present in context).

   The context may include a `domain_origin` block with:
     - domain_pattern_origin: what this life area is really about
     - domain_tension:        what tension this domain specifically carries
     - domain_failure_mode:   what fails here under pressure
     - domain_evolution_hint: how this part of life evolves

   Treat `domain_origin` as the PRIMARY domain-causal axis when answering
   any question about money / family / health / friends / relationships /
   work / self. Do NOT reuse a Self / Work / Relationships pattern for
   chips like money or family — let the domain origin drive the frame so
   the answer feels specific to that life area.

   NEVER mention the source of this signal. NEVER use the words "palace",
   "stars", "purple star", "zi wei", "ziwei", "命宫", or any related
   Chinese terminology. The user should only feel "this part of my life
   has its own pattern" without ever seeing the engine that produced it.

10. CROSS-DOMAIN SPINE (when cross_domain_pattern is present in context).

    The context may include a `cross_domain_pattern` block with:
      - core_pattern:         the SAME behaviour playing across all life areas
      - pattern_spine:        the underlying mechanism connecting them
      - cross_domain_tension: the cost of the pattern across life areas
      - recognition_line:     a short Mirror-like recognition (≤ 110 chars)

    This is the SINGULAR pattern showing up across the user's entire life,
    not just this domain. Use it as DEEPER ANCHORING CONTEXT — the user's
    answer should feel rooted in their broader behaviour, not just this
    one chip. When relevant, briefly nod to "the same shape that shows up
    elsewhere in your life" or "the thread you're already running in
    other parts of your life" — but in YOUR OWN WORDS.

    HARD RULES for cross_domain_pattern:
      - NEVER quote `recognition_line` verbatim. It is for YOUR anchoring
        only. Quoting it makes the answer feel canned across sessions.
      - NEVER quote `core_pattern` or `pattern_spine` word-for-word either.
      - You MAY paraphrase the spine in 5-10 fresh words if it strengthens
        the answer.
      - Follow-up questions of TYPE B (CROSS-DOMAIN EFFECT) SHOULD lean
        on this spine — that's what makes them feel sharp instead of
        generic. Example: instead of "How is this showing up in my work?",
        prefer "Is this why I keep over-tightening when I lead a project?"
        — concrete, specific to the spine.
      - If `cross_domain_pattern` is missing or empty, ignore this rule.

==================================================
FOLLOW-UP RULES
==================================================

After the answer, propose 2–3 follow-up questions the user is most likely
to want to ask next. Each one MUST be:

  - grounded in this user's specific context (their pattern + phase + domain)
  - a NATURAL next step from the answer just given
  - 10–12 words MAX
  - phrased the way the user would phrase it (first person: "my", "I")
  - NOT a repetition of the original question
  - NOT generic ("Tell me more", "Can I help you further")
  - NOT advice ("Should I...?")

Mix 2–3 of these types (you do not need all four):

  TYPE A — DEEPER WHY:           "Why does this keep happening to me?"
  TYPE B — CROSS-DOMAIN EFFECT:  "How is this showing up in my work?"
  TYPE C — PHASE-BASED:          "What phase is this moving me into?"
  TYPE D — PRESENT MOMENT:       "Why does this feel stronger today?"

Do NOT label the type in the output — just write the natural questions.

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


def _ensure_paragraphs(text: str, target: int = 3) -> str:
    """
    Ensure the answer renders as 2-3 short paragraphs.

    The LLM occasionally collapses everything into a single block. If we
    detect zero blank-line separators we split on sentence boundaries and
    rebuild ~`target` evenly sized paragraphs. Existing paragraph breaks
    are preserved when present.
    """
    if not text:
        return text
    s = text.strip()
    # Already paragraph-broken — preserve as-is (the LLM did the right thing).
    if "\n\n" in s or s.count("\n") >= 2:
        return s

    # Split into sentences. Greedy enough for the conversational style we use.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", s)
    sentences = [x.strip() for x in sentences if x and x.strip()]
    if len(sentences) <= 2:
        return s  # not enough material to bother splitting

    # Pick number of paragraphs: 2 if 3-4 sentences, else 3.
    para_count = 2 if len(sentences) <= 4 else min(target, 3)
    chunk_size = max(1, len(sentences) // para_count)
    paragraphs: List[str] = []
    for i in range(para_count):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < para_count - 1 else len(sentences)
        chunk = " ".join(sentences[start:end]).strip()
        if chunk:
            paragraphs.append(chunk)
    return "\n\n".join(paragraphs)



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
    chart: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    cross_domain_pattern: Optional[Dict[str, Any]] = None,
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

    # Domain origin (Zi Wei domain pattern engine — invisible).
    # Acts as the PRIMARY domain-causal axis for chips like money / family /
    # health / friends so those answers don't reuse Self / Work / Relationships
    # patterns. NEVER surfaced to UI by name.
    do: Dict[str, Any] = {}
    try:
        from .ziwei_domain_engine import generate_ziwei_domain_pattern
        zw = generate_ziwei_domain_pattern(
            chip_domain,
            chart=chart,
            lifeline_summary=lifeline_summary,
            pattern_memory=pattern_memory,
        )
        if zw and (zw.get("domain_pattern_origin") or zw.get("domain_tension")):
            do = {
                "domain_pattern_origin": _short(zw.get("domain_pattern_origin"), 200),
                "domain_tension":        _short(zw.get("domain_tension"), 200),
                "domain_failure_mode":   _short(zw.get("domain_failure_mode"), 200),
                "domain_evolution_hint": _short(zw.get("domain_evolution_hint"), 200),
            }
    except Exception as e:
        logger.warning("[LifeInterp] domain origin unavailable for chip=%s: %s", chip_domain, e)

    # Cross-domain pattern (Mirror Cross-Domain Engine — invisible).
    # The single pattern showing up across Self / Work / Relationships.
    # Used as DEEPER ANCHORING context, not surfaced verbatim.
    cdp: Dict[str, Any] = {}
    if isinstance(cross_domain_pattern, dict):
        core = (cross_domain_pattern.get("core_pattern") or "").strip()
        spine = (cross_domain_pattern.get("pattern_spine") or "").strip()
        cost = (cross_domain_pattern.get("cross_domain_tension") or "").strip()
        rec  = (cross_domain_pattern.get("recognition_line") or "").strip()
        # Only include if there's actual content (placeholder responses have empty strings)
        if core or spine or cost:
            cdp = {
                "core_pattern":         _short(core, 240),
                "pattern_spine":        _short(spine, 320),
                "cross_domain_tension": _short(cost, 240),
                "recognition_line":     _short(rec, 140),
                "confidence":           (cross_domain_pattern.get("confidence") or "").strip().lower() or None,
            }

    return {
        "chip":            chip_domain,
        "question":        _short(question, 600),
        "role_card":       rc,
        "domain_synthesis": ds,
        "domain_origin":   do,
        "cross_domain_pattern": cdp,
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
    cdp = ctx.get("cross_domain_pattern") or {}
    if cdp and (cdp.get("core_pattern") or cdp.get("pattern_spine")):
        lines.append(
            "CROSS-DOMAIN PATTERN (the SAME shape showing up across all of "
            "this user's life — anchor your answer to this, but do NOT "
            "quote any line verbatim):"
        )
        if cdp.get("core_pattern"):
            lines.append(f"  - core: {cdp['core_pattern']}")
        if cdp.get("pattern_spine"):
            lines.append(f"  - spine: {cdp['pattern_spine']}")
        if cdp.get("cross_domain_tension"):
            lines.append(f"  - cost: {cdp['cross_domain_tension']}")
        if cdp.get("recognition_line"):
            lines.append(
                f"  - recognition (REFERENCE ONLY — do NOT quote): "
                f"{cdp['recognition_line']}"
            )
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
        "Now produce the JSON object as specified. Speak directly to the "
        "user (you/your). Speak to the specific topic they asked about "
        f"({ctx['chip']}). Generate 2–3 follow-up questions in the user's "
        "first-person voice ('my', 'I'). Vary the opening line of the "
        "answer — don't always start with 'This isn't just about'."
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
    chart: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    cross_domain_pattern: Optional[Dict[str, Any]] = None,
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
        chart=chart,
        lifeline_summary=lifeline_summary,
        cross_domain_pattern=cross_domain_pattern,
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

    # Parse JSON {answer, follow_ups}. Fall back to treating the raw text as
    # the answer if parsing fails — this keeps the API contract resilient.
    answer_text, follow_ups, parse_error = _parse_interpreter_json(answer_raw, chip)

    answer, banned_hits = _scrub(answer_text)

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

    # Paragraph guard — gpt sometimes returns the whole answer in one
    # block. Break it into 2-3 paragraphs on sentence boundaries so the
    # UI can render it as multiple stanzas.
    answer = _ensure_paragraphs(answer, target=3)

    # Scrub banned phrases from follow-ups; drop any that become empty.
    cleaned_follow_ups: List[str] = []
    for f in follow_ups[:3]:
        if not isinstance(f, str):
            continue
        c, hits = _scrub(f)
        c = c.strip(" -•·").strip()
        if hits:
            banned_hits.extend(hits)
        # Filter out malformed / overly long / overly short
        if 4 <= len(c) <= 140:
            cleaned_follow_ups.append(c if c.endswith(("?", ".", "!")) else c + "?")

    # Defensive: if the model didn't supply usable follow-ups, fill with a
    # context-aware deterministic set (covers the LLM-failure path too).
    if len(cleaned_follow_ups) < 2:
        cleaned_follow_ups = _default_follow_ups(chip, pattern_memory, today_state)

    return {
        "answer":           answer,
        "follow_ups":       cleaned_follow_ups[:3],
        "chip_domain":      chip,
        "synthesis_domain": synth_dom,
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "generator_version": "life_interpreter_v4_cross_domain",
        "debug": {
            "llm_used":       answer_raw is not None and render_error is None,
            "render_error":   render_error,
            "parse_error":    parse_error,
            "banned_hits":    banned_hits,
            "context_keys":   {
                "has_role_card":          bool(ctx["role_card"]),
                "has_domain_synthesis":   bool(ctx["domain_synthesis"]),
                "has_current_phase":      bool(ctx["current_phase"]),
                "has_cross_domain":       bool(ctx.get("cross_domain_pattern")),
                "today_intensity":        ctx.get("today_intensity"),
                "is_recurring":           (pattern_memory or {}).get("memory_state") == "recurring_pattern",
                "evidence_count":         len(ctx.get("evidence") or []),
            },
        },
    }


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------

def _parse_interpreter_json(raw: str, chip: str) -> tuple[str, List[str], Optional[str]]:
    """
    Best-effort parse of the LLM JSON. Returns (answer_text, follow_ups, parse_error).
    On any failure: treats raw as plain answer and emits empty follow_ups.
    """
    import json as _json

    if not raw:
        return "", [], "empty"
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", s)
        s = re.sub(r"\n?```\s*$", "", s)
    first = s.find("{")
    last = s.rfind("}")
    if first == -1 or last == -1 or last < first:
        return s, [], "no_json_object"
    chunk = s[first:last + 1]
    try:
        obj = _json.loads(chunk)
    except Exception as e:
        return s, [], f"json_decode_error: {e}"
    if not isinstance(obj, dict):
        return s, [], "json_not_object"
    answer_text = obj.get("answer")
    follow_ups_raw = obj.get("follow_ups") or []
    if not isinstance(answer_text, str) or not answer_text.strip():
        return s, [], "missing_answer_field"
    if not isinstance(follow_ups_raw, list):
        follow_ups_raw = []
    return answer_text.strip(), follow_ups_raw, None


def _default_follow_ups(
    chip: str,
    pattern_memory: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
) -> List[str]:
    """
    Deterministic fallback follow-ups when the LLM doesn't produce any.
    Context-aware: uses chip + recurrence + today intensity to pick the
    most useful 2-3 questions, in the user's first-person voice.
    """
    out: List[str] = []
    is_recurring = (pattern_memory or {}).get("memory_state") == "recurring_pattern"
    intensity = (today_state or {}).get("intensity_level")

    if is_recurring:
        out.append("Why does this keep repeating for me?")
    if chip == "self":
        out.append("How is this showing up in my work?")
    elif chip == "work":
        out.append("How is this affecting my relationships?")
    elif chip == "money":
        out.append("Is this connected to how I work?")
    elif chip == "relationships":
        out.append("How does this show up in my work?")
    elif chip == "health":
        out.append("Is this tied to what's happening at work?")
    elif chip == "friends":
        out.append("Is this the same shape with my family?")
    elif chip == "family":
        out.append("Is this the same shape with my friends?")
    if intensity == "high":
        out.append("Why does this feel stronger right now?")
    else:
        out.append("What phase is this moving me into?")
    # Dedup + cap
    seen = set()
    deduped: List[str] = []
    for q in out:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            deduped.append(q)
    return deduped[:3]
