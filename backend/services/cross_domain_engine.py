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


GENERATOR_VERSION = "cross_domain_v1_2_metaphor_variety"


# ---------------------------------------------------------------------------
# Metaphor Variety Control (rule 15)
#
# Recognition lines must NOT reuse the same metaphor family across
# generations for the same user. We keep an in-memory history of the last
# N metaphor families per user, ask the LLM to AVOID them in the next
# generation, and run a post-render check that retries if the new line
# falls back into a recently-used family.
#
# Families intentionally overlap with common Mirror voice patterns we've
# already seen leak repetitively (sharpen / push / build / speed). The
# "allowed alternative frames" mirror what the spec asked for: physical,
# relational, temporal, internal — keyed off easy-to-detect verbs.
# ---------------------------------------------------------------------------

_METAPHOR_FAMILIES: Dict[str, re.Pattern] = {
    # over-used families — the engine actively rotates these
    "sharpen_cut":     re.compile(r"\b(?:sharpen(?:s|ed|ing)?|cut(?:s|ting)?|blade|edge|knife|carve)\b", re.I),
    "push_pull":       re.compile(r"\b(?:push(?:es|ed|ing)?|pull(?:s|ed|ing)?|force(?:s|d)?|forcing|drag(?:s|ged|ging)?)\b", re.I),
    "build_structure": re.compile(r"\b(?:build(?:s|ing)?|built|structure|scaffold|frame(?:s|d|work)?|hold(?:s|ing)? together)\b", re.I),
    "speed_pace":      re.compile(r"\b(?:outpace(?:s|d)?|pace|momentum|speed|fast(?:er)?|race(?:s|d)?|sprint)\b", re.I),
    # alternative frames — preferred when rotation is needed
    "physical_hold":   re.compile(r"\b(?:hold(?:s|ing)?|holding|carry(?:ing)?|drop(?:s|ped|ping)?|let(?:s|ting)? go|grip|grasp)\b", re.I),
    "relational":      re.compile(r"\b(?:reach(?:es|ed|ing)?|meet(?:s|ing)?|miss(?:es|ed|ing)?|respond(?:s|ed|ing)?|receive(?:s|d|ing)?|listen(?:s|ed|ing)?)\b", re.I),
    "temporal":        re.compile(r"\b(?:too early|too long|after the moment|before the space|already passed|keeps going|continu(?:e|es|ed|ing) past)\b", re.I),
    "internal":        re.compile(r"\b(?:tighten(?:s|ed|ing)?|tight|loosen(?:s|ed|ing)?|release(?:s|d|ing)?|correct(?:s|ed|ing)?|self[- ]correct(?:ion|ing)?|inside)\b", re.I),
}

_OVERUSED_FAMILIES = ("sharpen_cut", "push_pull", "build_structure", "speed_pace")
_ALTERNATIVE_FRAMES = ("physical_hold", "relational", "temporal", "internal")

# In-memory recent-metaphor history per user (capacity 5, simple FIFO).
# Survives across calls within the same backend process. Cleared on restart —
# acceptable for V1, since cross-domain output is regenerated on refresh.
_RECENT_METAPHORS_BY_USER: Dict[str, List[str]] = {}
_RECENT_METAPHORS_CAP = 5


def _detect_metaphor_families(text: str) -> List[str]:
    """Return families whose verbs/words appear in `text` (most distinctive first)."""
    if not isinstance(text, str) or not text:
        return []
    hits: List[str] = []
    # Check over-used families first, then alternatives
    for fam in (*_OVERUSED_FAMILIES, *_ALTERNATIVE_FRAMES):
        if _METAPHOR_FAMILIES[fam].search(text):
            hits.append(fam)
    return hits


def _record_metaphor_for_user(user_id: Optional[str], families: List[str]) -> None:
    """Append the families found in this generation to the user's history."""
    if not user_id or not families:
        return
    bucket = _RECENT_METAPHORS_BY_USER.setdefault(user_id, [])
    for fam in families:
        bucket.append(fam)
    if len(bucket) > _RECENT_METAPHORS_CAP:
        # Keep only the most recent N
        del bucket[:-_RECENT_METAPHORS_CAP]


def _avoid_families_for_user(user_id: Optional[str]) -> List[str]:
    """Return the families to AVOID for this user (the most recently used)."""
    if not user_id:
        return []
    bucket = _RECENT_METAPHORS_BY_USER.get(user_id, [])
    # Avoid any family that has appeared in the last 3 generations
    return list(dict.fromkeys(bucket[-3:]))  # preserves order, deduped


def _suggested_frames_for_user(user_id: Optional[str]) -> List[str]:
    """Return the alternative frames NOT recently used by this user."""
    avoid = set(_avoid_families_for_user(user_id))
    return [f for f in _ALTERNATIVE_FRAMES if f not in avoid] or list(_ALTERNATIVE_FRAMES)


_FRAME_DESCRIPTIONS: Dict[str, str] = {
    "physical_hold": "physical (hold, carry, drop, let go, grip, grasp)",
    "relational":    "relational (reach, meet, miss, respond, receive, listen)",
    "temporal":      "temporal (start too early, continue too long, after the moment, before the space)",
    "internal":      "internal (tighten, hold, correct, release, loosen)",
}


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

Your job is NOT to summarise. Your job is to RECOGNISE the ONE pattern
showing up across all three — the thread the user hasn't named yet.

Make it feel like a Mirror line: sharp, simple, behaviour-first, emotionally
recognisable. Not analytical. Not a research report. The user should read
this and feel "oh… that's the same thing happening everywhere", not "this
is a useful executive summary".

OUTPUT — return ONLY valid JSON (no prose before or after, no markdown):

{
  "core_pattern":         "ONE sentence. Starts with WHAT THE USER DOES, not with an abstract noun phrase. Behaviour first.",
  "pattern_spine":        "ONE sentence (or two short ones). Plain language explanation of the shared mechanism — what starts as one thing and turns into another.",
  "cross_domain_tension": "ONE sentence describing the COST of the pattern in plain emotional language. Do NOT mechanically list domains.",
  "recognition_line":     "≤ 110 chars. ONE COMPLETE SENTENCE. The 'oh, that's me' line. Sharp. Second-person present. No domain list. No softeners. Ends in a period.",
  "confidence":           "high | medium | low"
}

==================================================
HARD RULES
==================================================

1. BEHAVIOUR FIRST
   Do NOT start core_pattern (or any field) with abstract noun phrases.
   FORBIDDEN openers / phrases (in any field):
     - "a cyclical process"
     - "a recurring pattern" / "a repeated pattern"
     - "a recurring dynamic" / "a repeated dynamic"
     - "a tendency"
     - "a mechanism"
     - any field starting with "A " followed by an abstract noun.
   Bad:  "A cyclical process of refinement recurs across your life."
   Good: "You keep improving the thing until the improvement itself becomes the pressure."

2. NO DOMAIN LISTING IN recognition_line
   recognition_line MUST NOT enumerate "self", "work", "relationships",
   "inner life", "family", "money", "health", "friends" as a list. It
   should capture the pattern without listing where it appears.
   Bad:  "You repeat cycles of refinement across your inner life, work…"
   Good: "You sharpen the thing until it starts cutting back."

3. RECOGNITION LINE MUST BE SELF-CONTAINED
   recognition_line MUST be a complete sentence ending in a period.
   ≤ 110 characters. NEVER comma-truncated. NEVER ending mid-clause.
   If it would exceed 110 chars, write a SHORTER one — do not clip.

4. PATTERN SPINE MUST CONNECT, NOT SUMMARISE
   pattern_spine names the shared mechanism in plain language.
   Bad:  "This cycle increases precision yet diminishes natural flow."
   Good: "You begin by improving what feels weak, but the improvement keeps going after the moment has passed."

5. CROSS-DOMAIN TENSION MUST SHOW COST IN HUMAN LANGUAGE
   Show the cost of the pattern; do NOT enumerate domains as a checklist.
   Bad:  "undermines collaboration and trust, creating distance…"
   Good: "What began as care becomes pressure, and what began as clarity starts to feel like distance."

6. MORE MIRROR, LESS REPORT
   AVOID this management-report vocabulary in ANY field:
     cyclical process · counterproductive · diminishes · undermines ·
     generates friction · effective limits · internal sense of stability ·
     scalability · burnout cycle · operational tension
   PREFER:
     starts as · becomes · turns into · costs · distance · pressure ·
     the thing you meant to improve · the thing you end up carrying ·
     the thing you keep · the thing that keeps coming back

7. NEVER use:
     - "this is your life pattern"
     - "you are meant to" / "your purpose is"
     - "always" / "never" / "must"
     - "destiny" / "fate" / "calling"
     - banned framework names: human design · bazi · astrology · zi wei ·
       ziwei · palace · stars · manifestor · generator · projector · reflector

8. Tone: observational, reflective, precise. Not advice. Not prediction.
   Not abstract philosophy. Must feel grounded in lived experience.

9. METAPHOR VARIETY (recognition_line specifically)
   recognition_line MUST NOT reuse the same metaphor family across
   generations for the same user. If the input payload contains a
   `metaphor_avoid` field, you MUST avoid those families in the
   recognition_line. If it contains a `metaphor_prefer` field, prefer
   one of those alternative experiential frames.
   Allowed alternative frames:
     - physical (hold, carry, drop, let go, grip, grasp)
     - relational (reach, meet, miss, respond, receive, listen)
     - temporal (start too early, continue too long, after the moment,
                 before the space)
     - internal (tighten, hold, correct, release, loosen)
   Pick the frame that fits the actual evidence. Do NOT force a frame
   that does not fit — but do not fall back into a recently-used one
   either.

==================================================
EXAMPLE TARGET OUTPUT
==================================================

core_pattern:
"You keep improving what feels unfinished until the improvement itself becomes the pressure."

pattern_spine:
"What starts as care, precision, or responsibility keeps going past the useful moment. The thing you meant to strengthen starts needing you too much."

cross_domain_tension:
"The cost is that people step back, systems depend on you, and you turn the same pressure inward."

recognition_line:
"You sharpen the thing until it starts cutting back."

VOICE

The user should feel:
   "Oh… that's the same thing happening everywhere."
NOT:
   "This is a summary."
"""


def _user_prompt(
    self_text: str,
    work_text: str,
    rels_text: str,
    shared: List[str],
    pattern_memory: Optional[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
    avoid_families: Optional[List[str]] = None,
    suggested_frames: Optional[List[str]] = None,
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

    # Metaphor variety: avoid recently-used families for this user, prefer
    # alternative experiential frames. Sent as additional payload keys so the
    # LLM can read them in context.
    if avoid_families:
        payload["metaphor_avoid"] = (
            "Do NOT use these metaphor families in recognition_line: "
            + ", ".join(avoid_families)
            + ". They have been used recently for this user and would feel "
            + "stale. Choose a different experiential frame."
        )
    if suggested_frames:
        payload["metaphor_prefer"] = (
            "Prefer ONE of these alternative frames for recognition_line: "
            + " | ".join(_FRAME_DESCRIPTIONS.get(f, f) for f in suggested_frames)
            + ". Pick the one that fits the actual evidence; do not force it."
        )
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


# Mirror-vs-report vocabulary blocks. These are forbidden in ANY field
# because they make the output sound like a management report instead of
# a recognition line.
_REPORT_VOCAB_RX = re.compile(
    r"\b(?:cyclical process|counterproductive|diminish(?:es|ed|ing)?|"
    r"undermin(?:e|es|ed|ing)|generates? friction|effective limits|"
    r"internal sense of stability|scalability|burnout cycle|"
    r"operational tension|recurring dynamic|repeated dynamic|"
    r"recurring pattern|repeated pattern)\b",
    re.I,
)

# Abstract noun openers — fields that start with "A " or "An " followed
# by an analytical noun phrase. Sniffs the first 25 chars of any field.
_ABSTRACT_OPENER_RX = re.compile(
    r"^(?:A|An)\s+(?:cyclical|recurring|repeated|persistent|continuous|"
    r"underlying|driving|tendency|mechanism|dynamic|pattern|process|"
    r"loop|cycle|trend)\b",
    re.I,
)

# Domain enumeration in recognition_line — flags lists like
# "self / work / relationships" or "your inner life, work, and family".
_DOMAIN_ENUM_RX = re.compile(
    r"\b(self|work|relationships?|inner life|family|money|health|"
    r"friends|career)\b[^.?!]*?\b(self|work|relationships?|inner life|"
    r"family|money|health|friends|career)\b",
    re.I,
)


def _audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns {flagged: bool, reasons: [...], counts: {...}}.
    Flags any of:
      - missing required field
      - banned framework / guru phrases
      - report-y / management vocabulary (cyclical process, undermines, ...)
      - abstract noun opener on any field ("A cyclical process...")
      - generic-applies-to-anyone phrasing
      - absolute-language abuse (always / never / must)
      - recognition_line: > 110 chars, missing 'you', has softener,
                          has directive, lists domains, doesn't end in period
    """
    out: Dict[str, Any] = {"flagged": False, "reasons": [], "counts": {}}
    if not isinstance(payload, dict):
        out["flagged"] = True
        out["reasons"].append("payload_not_dict")
        return out

    required = ("core_pattern", "pattern_spine", "cross_domain_tension", "recognition_line")
    for key in required:
        v = payload.get(key)
        if not isinstance(v, str) or not v.strip():
            out["flagged"] = True
            out["reasons"].append(f"missing_or_empty:{key}")

    full_text = " ".join(str(payload.get(k, "")) for k in required)

    # Banned framework / guru phrases
    banned = _BANNED_RX.findall(full_text)
    if banned:
        out["flagged"] = True
        out["reasons"].append(f"banned_phrase ({', '.join(set(b.lower() for b in banned))[:120]})")

    # Absolute-language abuse
    absolutes = _ABSOLUTE_RX.findall(full_text)
    if len(absolutes) >= 2:
        out["flagged"] = True
        out["reasons"].append(f"too_many_absolutes ({len(absolutes)})")

    # Generic-applies-to-anyone phrasing
    generic = _GENERIC_RX.findall(full_text)
    if generic:
        out["flagged"] = True
        out["reasons"].append(f"generic ({', '.join(set(g.lower() for g in generic))})")

    # Mirror-vs-report vocabulary
    report_hits = _REPORT_VOCAB_RX.findall(full_text)
    if report_hits:
        out["flagged"] = True
        out["reasons"].append(f"report_vocab ({', '.join(set(h.lower() for h in report_hits))[:160]})")

    # Abstract noun opener on any field
    for key in required:
        v = (payload.get(key) or "").strip()
        if v and _ABSTRACT_OPENER_RX.match(v):
            out["flagged"] = True
            out["reasons"].append(f"abstract_opener:{key}")

    # recognition_line specific checks
    rl = (payload.get("recognition_line") or "").strip()
    if rl:
        if len(rl) > 110:
            out["flagged"] = True
            out["reasons"].append(f"recognition_line_too_long ({len(rl)})")
        if not _SECOND_PERSON_RX.search(rl):
            out["flagged"] = True
            out["reasons"].append("recognition_line_not_second_person")
        if _SOFTENER_RX.search(rl):
            out["flagged"] = True
            out["reasons"].append("recognition_line_has_softener")
        if re.search(r"\b(?:must|should|need to|have to)\b", rl, re.I):
            out["flagged"] = True
            out["reasons"].append("recognition_line_has_directive")
        # Domain enumeration check — recognition_line should NOT list domains
        if _DOMAIN_ENUM_RX.search(rl):
            out["flagged"] = True
            out["reasons"].append("recognition_line_lists_domains")
        # Must end with a period (or '—' or '!') for completeness
        if not re.search(r"[.!—]$", rl):
            out["flagged"] = True
            out["reasons"].append("recognition_line_not_complete_sentence")
        # Must not end with a comma, preposition, or 'and'
        if re.search(r"\b(?:and|or|with|of|to|by|across|in|the)[\s,]*[.!—]?$", rl, re.I):
            out["flagged"] = True
            out["reasons"].append("recognition_line_ends_mid_thought")

    out["counts"] = {
        "banned":        len(banned),
        "absolutes":     len(absolutes),
        "generic":       len(generic),
        "report_vocab":  len(report_hits),
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
    user_id: Optional[str] = None,
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
    avoid_families = _avoid_families_for_user(user_id)
    suggested_frames = _suggested_frames_for_user(user_id)
    user_msg = _user_prompt(
        self_text, work_text, rels_text, shared, pattern_memory,
        lifeline_summary, today_state,
        avoid_families=avoid_families,
        suggested_frames=suggested_frames,
    )
    payload, audit, retry_used = await _render_once(
        llm_chat_factory=llm_chat_factory,
        system_prompt=_SYSTEM_PROMPT,
        user_msg=user_msg,
    )

    # Metaphor variety check on the FIRST draft. If recognition_line uses a
    # recently-used family, mark the audit as flagged so the standard retry
    # path triggers with the metaphor reasons included.
    rl_first = (payload.get("recognition_line") or "")
    metaphor_hits_first = _detect_metaphor_families(rl_first)
    overlap_first = [f for f in metaphor_hits_first if f in avoid_families]
    if overlap_first and not audit.get("flagged"):
        audit["flagged"] = True
        audit.setdefault("reasons", []).append(
            f"metaphor_reuse ({', '.join(overlap_first)})"
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
            + "\n\n=== RETRY (CRITICAL — your previous draft was REJECTED) ===\n"
            + "Reasons your previous draft failed: "
            + "; ".join(audit.get("reasons") or [])
            + ".\n\n"
            + "FOLLOW THE TARGET EXAMPLE BELOW EXACTLY IN STYLE:\n\n"
            + "core_pattern:        \"You keep improving what feels unfinished until the improvement itself becomes the pressure.\"\n"
            + "pattern_spine:       \"What starts as care, precision, or responsibility keeps going past the useful moment. The thing you meant to strengthen starts needing you too much.\"\n"
            + "cross_domain_tension: \"The cost is that people step back, systems depend on you, and you turn the same pressure inward.\"\n"
            + "recognition_line:    \"You sharpen the thing until it starts cutting back.\"\n\n"
            + "RULES YOU MUST FOLLOW:\n"
            + "  - Every field begins with WHAT THE USER DOES (\"You ...\").\n"
            + "    NEVER begin a field with \"A\", \"An\", \"A cyclical\", \"A recurring\", or any abstract noun phrase.\n"
            + "  - recognition_line MUST NOT name or list any domains (self, work, relationships, inner life, family, money, health, friends, career).\n"
            + "  - recognition_line MUST be ≤ 110 chars AND a complete sentence ending in a period. If you cannot fit it under 110 chars, write a SHORTER one — do not let it run long.\n"
            + "  - No report vocabulary (cyclical process, counterproductive, diminishes, undermines, generates friction, effective limits, internal sense of stability, scalability, burnout cycle, operational tension, recurring dynamic, repeated dynamic, recurring pattern, repeated pattern).\n"
            + "  - Use Mirror words: starts as / becomes / turns into / costs / distance / pressure / the thing you keep / the thing that keeps coming back.\n"
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

    # Note on recognition_line:
    # The earlier deterministic trim was REMOVED. If the line is still > 110
    # chars after the retry, we no longer mid-clause clip — the spec asks for
    # a complete sentence, not a truncated one. We log a WARNING so we can
    # tighten the prompt if this happens at scale.
    rl_final = payload.get("recognition_line")
    if isinstance(rl_final, str) and len(rl_final) > 110:
        logger.warning(
            "[CrossDomain] recognition_line still > 110 chars after retry: %d chars — keeping as-is",
            len(rl_final),
        )

    # Drop LLM-supplied confidence in favour of the deterministic one when it's
    # missing or invalid; otherwise keep it as long as it's one of high/medium/low.
    llm_conf = (payload.get("confidence") or "").strip().lower()
    if llm_conf not in ("high", "medium", "low"):
        payload["confidence"] = confidence

    payload["generator_version"] = GENERATOR_VERSION

    # Record the final recognition_line metaphor family in the user's
    # rolling history so subsequent calls steer away from the same frame.
    final_rl = (payload.get("recognition_line") or "")
    final_families = _detect_metaphor_families(final_rl)
    _record_metaphor_for_user(user_id, final_families)

    if debug:
        payload["debug"] = {
            "shared_signals":         shared,
            "audit":                  audit,
            "retry_used":             retry_used,
            "metaphor_avoid":         avoid_families,
            "metaphor_suggested":     suggested_frames,
            "metaphor_families_used": final_families,
            "metaphor_history":       list(_RECENT_METAPHORS_BY_USER.get(user_id or "", [])),
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
