"""
Cross-Domain Pattern Engine (V1).

Sits ABOVE the per-domain layers (Zi Wei origin, Language Physics,
Emotional Gravity). Where those isolate each domain, this layer asks:

    "What is the SAME pattern showing up across Self / Work / Relationships?"

Output contract
===============
{
  "core_pattern":         "...",   # one neutral sentence, behaviour across domains
  "pattern_spine":        "...",   # the underlying mechanism that connects them
  "cross_domain_tension": "...",   # the cost of the pattern across domains
  "recognition_line":     "...",   # ≤ 110 chars, second-person present, no softeners
  "confidence":           "high|medium|low",
  "generator_version":    "cross_domain_v1",
  "debug": {                       # only when explicitly requested
    "shared_signals":    [...],
    "audit":             {...},
    "retry_used":        bool,
  }
}

Must feel like "oh… that's the same thing happening everywhere", not a
summary. Anti-guru rules apply: observational, reflective, precise — no
"your purpose is", no "you are meant to", no advice / prediction.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


GENERATOR_VERSION = "cross_domain_v1"


# ---------------------------------------------------------------------------
# Deterministic signal extraction
#
# We pull a few short tokens from each domain synthesis so the seed sent to
# the LLM is grounded in real material from the user's per-domain output.
# ---------------------------------------------------------------------------

_DOMAIN_FIELDS = (
    "pattern",
    "default_tension",
    "distortion_under_pressure",
    "what_this_pattern_needs",
)

# Heuristic theme regexes — short tokens that often appear in this system's
# output. Used to detect overlap, NOT to drive copy.
_THEME_PATTERNS: Dict[str, re.Pattern] = {
    "pace":            re.compile(r"\b(pace|outpace|speed|momentum|fast(?:er)?|ahead of)\b", re.I),
    "pressure":        re.compile(r"\b(pressure|strain|weight|load|burden|tight(?:en)?)\b", re.I),
    "responsibility":  re.compile(r"\b(responsibility|ownership|carrying|on your shoulders|accumulat)\b", re.I),
    "response_gap":    re.compile(r"\b(response|reach(?:ing)?|signal|gap|distance|silen(?:t|ce)|pause)\b", re.I),
    "refining":        re.compile(r"\b(refin(?:e|ing|ed)|standard|sharper|elevat(?:e|ing)|critique)\b", re.I),
    "self_correction": re.compile(r"\b(self[- ]correct|self[- ]trust|inner pressure|interior|identity)\b", re.I),
    "structure":       re.compile(r"\b(system|structure|infrastructure|workflow|leverage|capacity)\b", re.I),
    "recurrence":      re.compile(r"\b(again|recur|return|loop|repeat|each time|over (?:and over|time))\b", re.I),
    "container":       re.compile(r"\b(container|hold|hold(?:s|ing)?|absorb|absorbed)\b", re.I),
}


def _domain_text(payload: Optional[Dict[str, Any]]) -> str:
    if not isinstance(payload, dict):
        return ""
    parts: List[str] = []
    for f in _DOMAIN_FIELDS:
        v = payload.get(f)
        if isinstance(v, str) and v:
            parts.append(v)
    return " ".join(parts)


def _theme_hits(text: str) -> Dict[str, int]:
    if not text:
        return {}
    return {k: len(rx.findall(text)) for k, rx in _THEME_PATTERNS.items() if rx.search(text)}


def _shared_signals(
    self_text: str,
    work_text: str,
    rels_text: str,
) -> List[str]:
    """
    Themes that appear in at least 2 of the 3 domain texts. Returns a
    sorted-by-coverage list of theme names.
    """
    hits = {"self": _theme_hits(self_text), "work": _theme_hits(work_text), "relationships": _theme_hits(rels_text)}
    coverage: Dict[str, int] = {}
    for theme in _THEME_PATTERNS:
        domains_hit = sum(1 for d in hits.values() if d.get(theme, 0) > 0)
        if domains_hit >= 2:
            coverage[theme] = domains_hit
    # Sort: coverage desc, then theme name for stability
    return [t for t, _ in sorted(coverage.items(), key=lambda kv: (-kv[1], kv[0]))]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are the Mirror Cross-Domain Pattern Engine.

You have three short paragraphs describing the SAME PERSON across three
different parts of life: Self, Work, Relationships. You also have a list
of shared signals that appear across at least two of those domains.

Your job is NOT to summarise the three domains. Your job is to RECOGNISE
the one pattern showing up across all three — the thread the user hasn't
named yet.

OUTPUT — return ONLY valid JSON (no prose before or after, no markdown):

{
  "core_pattern":         "ONE sentence describing the repeating behaviour across domains. Neutral. Second-person.",
  "pattern_spine":        "ONE sentence explaining the underlying mechanism that connects Self / Work / Relationships into one shape.",
  "cross_domain_tension": "ONE sentence describing the cost of the pattern across domains — what breaks, strains, or repeats.",
  "recognition_line":     "≤ 110 chars. Sharp. Second-person present. No softeners. The 'oh, that's me' line.",
  "confidence":           "high | medium | low"
}

CRITICAL RULES

1. NOT a summary. NOT a list. NOT three sentences glued together.
2. NOT advice. NOT prediction. NOT prescription.
3. NOT abstract philosophy. Must feel grounded in lived experience.
4. NOT generic. The output must NOT pass for any other person.
5. NEVER use:
     - "this is your life pattern"
     - "you are meant to"
     - "your purpose is"
     - "always" / "never" / "must"
     - "destiny" / "fate" / "calling"
     - banned framework names: human design, bazi, astrology, zi wei,
       ziwei, palace, stars, manifestor, generator, projector, reflector
6. Tone: observational, reflective, precise.
7. recognition_line MUST be ≤ 110 characters, end with "." or "—",
   contain "you" or "your", and contain NO softener (tends to / may /
   often / sometimes / usually / typically / generally / seems to /
   appears to / seems like).
8. Do NOT quote or paraphrase whole sentences from the per-domain text
   verbatim. Use them as evidence, not as copy.

VOICE

The user should feel:
   "Oh… that's the same thing happening everywhere."
NOT:
   "This is a summary."

Make it feel like the system just connected the dots the user hadn't
named yet.
"""


def _user_prompt(
    self_text: str,
    work_text: str,
    rels_text: str,
    shared: List[str],
    pattern_memory: Optional[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
) -> str:
    pm_summary = ""
    if isinstance(pattern_memory, dict):
        match_count = pattern_memory.get("match_count")
        if isinstance(match_count, int) and match_count > 0:
            pm_summary = f"This shape has recurred {match_count} times in pattern memory."

    today_intensity = ""
    if isinstance(today_state, dict):
        ti = (today_state.get("intensity_label") or today_state.get("intensity") or "").strip()
        if ti:
            today_intensity = f"Today intensity: {ti}."

    ll_note = ""
    if isinstance(lifeline_summary, dict):
        n = lifeline_summary.get("event_count") or 0
        if isinstance(n, int) and n > 0:
            ll_note = f"Lifeline event count: {n}."

    payload = {
        "self_synthesis":        self_text[:1200],
        "work_synthesis":        work_text[:1200],
        "relationships_synthesis": rels_text[:1200],
        "shared_signals":        shared,
        "pattern_memory_note":   pm_summary,
        "today_note":            today_intensity,
        "lifeline_note":         ll_note,
        "instructions":
            "Recognise the ONE pattern showing up across all three domains. "
            "Use the shared_signals as a hint at where the overlap is. Do NOT "
            "summarise. Do NOT quote whole sentences from the domain text. "
            "Return JSON exactly as specified by the system prompt.",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

_BANNED_RX = re.compile(
    r"\b(?:human design|bazi|ba zi|astrology|zi wei|ziwei|purple star|"
    r"palace|manifestor|generator|projector|reflector|life path|"
    r"day master|incarnation cross|destiny|fate|your purpose is|"
    r"you are meant to|this is your life pattern)\b",
    re.I,
)
_ABSOLUTE_RX = re.compile(r"\b(?:always|never|must)\b", re.I)
_SOFTENER_RX = re.compile(
    r"\b(?:tends? to|tend to|may|might|often|sometimes|usually|"
    r"typically|generally|seems? to|appears? to|seems? like)\b",
    re.I,
)
_GENERIC_RX = re.compile(
    r"\b(?:everyone|anyone|people in general|the human condition|"
    r"life in general|we all|nobody really|each person)\b",
    re.I,
)
_SECOND_PERSON_RX = re.compile(r"\b(?:you|your)\b", re.I)


def _audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns {flagged: bool, reasons: [...], counts: {...}}.
    Flags any of:
      - missing required field
      - banned framework / guru phrases
      - generic-applies-to-anyone phrasing
      - absolute-language abuse (always / never / must)
      - recognition_line too long, missing 'you', or contains softener
    """
    out: Dict[str, Any] = {"flagged": False, "reasons": [], "counts": {}}
    if not isinstance(payload, dict):
        out["flagged"] = True
        out["reasons"].append("payload_not_dict")
        return out

    # Required-field check first — if the LLM returned the wrong shape, all
    # other audits become noise.
    required = ("core_pattern", "pattern_spine", "cross_domain_tension", "recognition_line")
    for key in required:
        v = payload.get(key)
        if not isinstance(v, str) or not v.strip():
            out["flagged"] = True
            out["reasons"].append(f"missing_or_empty:{key}")

    full_text = " ".join(str(payload.get(k, "")) for k in required)

    banned = _BANNED_RX.findall(full_text)
    if banned:
        out["flagged"] = True
        out["reasons"].append(f"banned_phrase ({', '.join(set(b.lower() for b in banned))[:120]})")

    absolutes = _ABSOLUTE_RX.findall(full_text)
    if len(absolutes) >= 2:
        out["flagged"] = True
        out["reasons"].append(f"too_many_absolutes ({len(absolutes)})")

    generic = _GENERIC_RX.findall(full_text)
    if generic:
        out["flagged"] = True
        out["reasons"].append(f"generic ({', '.join(set(g.lower() for g in generic))})")

    # recognition_line specific checks
    rl = (payload.get("recognition_line") or "").strip()
    if not rl:
        # already flagged above as missing_or_empty:recognition_line
        pass
    else:
        if len(rl) > 110:
            out["flagged"] = True
            out["reasons"].append(f"recognition_line_too_long ({len(rl)})")
        if not _SECOND_PERSON_RX.search(rl):
            out["flagged"] = True
            out["reasons"].append("recognition_line_not_second_person")
        if _SOFTENER_RX.search(rl):
            out["flagged"] = True
            out["reasons"].append("recognition_line_has_softener")
        # recognition_line is a recognition, not advice — flag any directive
        # vocabulary inside it specifically.
        if re.search(r"\b(?:must|should|need to|have to)\b", rl, re.I):
            out["flagged"] = True
            out["reasons"].append("recognition_line_has_directive")

    out["counts"] = {
        "banned":    len(banned),
        "absolutes": len(absolutes),
        "generic":   len(generic),
        "recognition_line_len": len(rl),
    }
    return out


def _scrub_banned(text: str) -> str:
    """Last-resort post-scrub: strip banned phrases (keeps the engine resilient)."""
    if not isinstance(text, str) or not text:
        return text
    cleaned = _BANNED_RX.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,.;:—")
    return cleaned


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def _confidence(
    self_text: str,
    work_text: str,
    rels_text: str,
    shared: List[str],
    pattern_memory: Optional[Dict[str, Any]],
) -> str:
    domains_with_text = sum(1 for t in (self_text, work_text, rels_text) if t and len(t) > 80)
    if domains_with_text < 2:
        return "low"
    if shared and len(shared) >= 3:
        if isinstance(pattern_memory, dict) and (pattern_memory.get("match_count") or 0) >= 2:
            return "high"
        return "medium"
    if shared:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_cross_domain_pattern(
    *,
    self_synth: Optional[Dict[str, Any]],
    work_synth: Optional[Dict[str, Any]],
    rels_synth: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    today_state: Optional[Dict[str, Any]] = None,
    llm_chat_factory=None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Generate the cross-domain pattern recognition. Returns the structured
    contract documented at module top.

    `*_synth` arguments accept either:
      - the full /api/life/{domain}/synthesis response dict, or
      - just the inner `domain_synthesis` block (with pattern / default_tension / ...)
    """
    def _inner(s: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(s, dict):
            return {}
        return s.get("domain_synthesis") if isinstance(s.get("domain_synthesis"), dict) else s

    self_inner = _inner(self_synth)
    work_inner = _inner(work_synth)
    rels_inner = _inner(rels_synth)

    self_text = _domain_text(self_inner)
    work_text = _domain_text(work_inner)
    rels_text = _domain_text(rels_inner)

    shared = _shared_signals(self_text, work_text, rels_text)
    confidence = _confidence(self_text, work_text, rels_text, shared, pattern_memory)

    # If we have no LLM factory we still return a deterministic
    # placeholder so callers don't break.
    if llm_chat_factory is None or (not self_text and not work_text and not rels_text):
        result = {
            "core_pattern":         "",
            "pattern_spine":        "",
            "cross_domain_tension": "",
            "recognition_line":     "",
            "confidence":           "low",
            "generator_version":    GENERATOR_VERSION,
        }
        if debug:
            result["debug"] = {"shared_signals": shared, "audit": {"reason": "no_llm_or_no_text"}, "retry_used": False}
        return result

    # First render
    user_msg = _user_prompt(self_text, work_text, rels_text, shared, pattern_memory, lifeline_summary, today_state)
    payload, audit, retry_used = await _render_once(
        llm_chat_factory=llm_chat_factory,
        system_prompt=_SYSTEM_PROMPT,
        user_msg=user_msg,
    )

    # If the audit flagged the result and we have an LLM factory, retry ONCE
    # with a stronger instruction hint inline.
    if audit.get("flagged"):
        logger.warning(
            "[CrossDomain] audit flagged: reasons=%s — retrying once",
            audit.get("reasons"),
        )
        retry_user_msg = (
            user_msg
            + "\n\n=== RETRY (CRITICAL) ===\n"
            + "Your previous draft was flagged: "
            + "; ".join(audit.get("reasons") or [])
            + ".\nFix EVERY issue. Keep the JSON shape exactly. The "
            + "recognition_line MUST be ≤ 110 chars, second-person present, "
            + "no softener, end with '.' or '—'. Do NOT summarise the three "
            + "domain paragraphs — recognise the ONE shared pattern. Avoid "
            + "absolutes (always/never/must). Avoid generic phrases that "
            + "would apply to anyone."
        )
        payload2, audit2, _ = await _render_once(
            llm_chat_factory=llm_chat_factory,
            system_prompt=_SYSTEM_PROMPT,
            user_msg=retry_user_msg,
        )
        # Only swap in if retry has fewer flagged reasons OR resolves it
        if (not audit2.get("flagged")) or (
            len(audit2.get("reasons") or []) < len(audit.get("reasons") or [])
        ):
            payload, audit = payload2, audit2
            retry_used = True

    # Final scrub on banned phrases (defence in depth)
    for k in ("core_pattern", "pattern_spine", "cross_domain_tension", "recognition_line"):
        if isinstance(payload.get(k), str):
            payload[k] = _scrub_banned(payload[k])

    # Hard cap on recognition_line length — if the LLM stayed long after retry,
    # deterministically trim at the last clause boundary inside 110 chars and
    # ensure it ends with "." or "—".
    rl = payload.get("recognition_line")
    if isinstance(rl, str) and len(rl) > 110:
        # Try to clip at a clause boundary inside 110 chars.
        candidate = rl[:110]
        # prefer cutting at last sentence/clause break in the trimmed window
        for sep in (". ", "; ", "—", ", "):
            idx = candidate.rfind(sep)
            if idx >= 60:  # avoid clipping too aggressively
                candidate = candidate[:idx + (1 if sep == ", " else len(sep))].rstrip()
                break
        candidate = candidate.rstrip(" ,;:—.").rstrip()
        if not candidate.endswith((".", "—")):
            candidate += "."
        payload["recognition_line"] = candidate

    # Drop LLM-supplied confidence in favour of the deterministic one when it's
    # missing or invalid; otherwise keep it as long as it's one of high/medium/low.
    llm_conf = (payload.get("confidence") or "").strip().lower()
    if llm_conf not in ("high", "medium", "low"):
        payload["confidence"] = confidence

    payload["generator_version"] = GENERATOR_VERSION
    if debug:
        payload["debug"] = {
            "shared_signals": shared,
            "audit":          audit,
            "retry_used":     retry_used,
        }
    return payload


# ---------------------------------------------------------------------------
# Internal: a single LLM call → parse → audit
# ---------------------------------------------------------------------------

async def _render_once(
    *,
    llm_chat_factory,
    system_prompt: str,
    user_msg: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
    """Send one chat turn, parse JSON, run audit. Returns (payload, audit, retry_used=False)."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local import — keep startup light

    chat: LlmChat = llm_chat_factory()
    # Set the system message for this turn
    if hasattr(chat, "with_system_message"):
        chat = chat.with_system_message(system_prompt)
    elif hasattr(chat, "system_message"):
        try:
            chat.system_message = system_prompt
        except Exception:
            pass

    raw = await chat.send_message(UserMessage(text=user_msg))
    raw_text = raw if isinstance(raw, str) else str(raw)

    parsed = _parse_json(raw_text)
    audit = _audit(parsed)
    return parsed, audit, False


def _parse_json(text: str) -> Dict[str, Any]:
    """Tolerant JSON parse — strips fences and surrounding prose if present."""
    if not isinstance(text, str) or not text.strip():
        return {}
    s = text.strip()
    # Strip ```json / ``` fences
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    # If the LLM included prose, find the first { ... } block
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if m:
        s = m.group(0)
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception as e:
        logger.warning("[CrossDomain] JSON parse failed: %s", e)
        return {}
