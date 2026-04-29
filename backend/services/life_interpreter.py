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

11. IDENTITY RECURRENCE OVERLAY (when recurrence is present in context).

    The context may include a `recurrence` block:
      - recurrence_detected: True
      - human_label: a short surface-safe line
        (e.g. "You've been here before.",
              "This pattern is returning.",
              "This is becoming familiar.")

    When `recurrence_detected` is True:
      * Open the answer with the `human_label` as its OWN first line —
        EXACTLY as written. No quotes. No paraphrasing. No decoration.
        It must stand alone, then a blank line, then the rest of the
        answer in your normal voice.
      * Slightly INCREASE confidence/directness in the body. Less
        exploratory ("perhaps", "you might"), more direct
        ("you do this", "this is the move you make"). The user has
        earned recognition — match it.
      * NEVER expose `match_count`, `memory_state`, scoring, or any
        other internal field. Only the `human_label` itself is
        surface-safe.
      * If `recurrence` is missing or `recurrence_detected` is False,
        IGNORE this rule entirely. Do not invent a recognition line.

12. QUESTION-TENSION REASONING (CRITICAL — when `intent` is in context).

    The context includes an `intent` block telling you what KIND of
    question this is. You MUST answer the SPECIFIC TENSION inside the
    user's question, not just restate the domain pattern. If the answer
    could apply to anyone, it FAILS.

    Intent flags:
      - intent.is_contradiction:    user holds two truths at once
      - intent.is_outlook_timing:   user asks about a year/phase/timeline
      - intent.is_why_pattern:      user asks why something keeps happening

    A) WHEN intent.is_contradiction IS TRUE:
       USE THIS EXACT 4-PART STRUCTURE (no headings, just paragraphs):

       (1) BLADE LINE — A sharp first sentence that names the tension.
           Example: "It may feel better because you're calmer, not
                    because the pattern is finished."

       (2) BOTH CAN BE TRUE — One paragraph explaining how the user's
           felt sense AND the timeline/phase signal can both be valid.
           Example: "You may be genuinely more open now, but the phase
                    you're in still tests what happens when the other
                    person doesn't meet your pace."

       (3) PHASE / TIMING READING — Use phase_context + activation_now
           (when present) to ground the contrast in real timing.
           Example: "The phase you're in is not about sudden ease.
                    It's about seeing whether the old gap returns when
                    response is slower than you want."

       (4) GROUNDED OUTLOOK — A non-predictive close:
              what is actually getting better
              what is not yet resolved
              what to watch
           Example: "What is improving is your awareness. What is still
                    under pressure is timing, response, and trust."
           NEVER say "this will happen". Say "the pattern to watch is…"

    B) WHEN intent.is_outlook_timing IS TRUE (without contradiction):
       Same 4-part structure, but skip part (2) "both can be true" and
       instead lean harder on phase_context + activation_now to give a
       grounded reading of the period the user is asking about. Always
       finish with "what to watch / what is still under pressure".

    C) WHEN intent.is_why_pattern IS TRUE:
       Anchor the answer in cross_domain_pattern + recurrence (if
       present). Show the mechanism, not the moral. Make it land.

    D) ALWAYS, regardless of intent:
       The first sentence MUST address the user's specific question.
       Do NOT open with a generic pattern recap if the user asked about
       this year, this phase, or a contradiction.

==================================================
HARD VOCABULARY BAN (Mirror style — no spiritual filler)
==================================================

NEVER use any of these phrases or near-equivalents:
   - "energetic signal(s)"
   - "internal shift(s)"
   - "quality of (your) connections"
   - "others need time to catch up"
   - "cycle of tuning"
   - "in alignment with" / "aligned"
   - "evolving" / "expansion" / "awakening"
   - "the lessons of" / "lessons from"
   - "a journey" / "your journey"
   - "the universe" / "divine" / "sacred"
   - "trust the process" / "flow with"
   - "holding space"
   - "called you in" / "calling you forward"
   - "deeper truth"
   - "invitation to"
   - "higher self"

PREFER concrete, behavior-first phrasing:
   - "what is actually getting better is…"
   - "what is not yet resolved is…"
   - "the timeline is not saying no — it is showing pressure around…"
   - "this year tests whether…"
   - "the old pattern returns when…"
   - "better does not mean finished"
   - "the pattern to watch is…"

LIMIT hedging modifiers (≤ 3 across the whole answer): "may be",
"might be", "tends to", "perhaps", "seems like", "kind of", "in
some ways". One or two are fine. Four+ makes the answer feel
evasive — don't.

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

# ---------------------------------------------------------------------------
# QUESTION INTENT DETECTOR (deterministic — no LLM)
# ---------------------------------------------------------------------------
#
# Maps the user's free-text question to one or more intent categories so the
# system prompt can tell the LLM "this is a contradiction question — answer
# the contrast directly" instead of falling back to a generic pattern recap.

_INTENT_OUTLOOK_RE = re.compile(
    r"\b(this year|next year|the rest of (the )?year|by year|by the end of|"
    r"outlook|timeline|coming months?|coming weeks?|next (?:few )?months?|"
    r"phase|chapter|when does|how long|in (?:the )?short[- ]?term|"
    r"in (?:the )?long[- ]?term)\b",
    re.IGNORECASE,
)

# Contradictions: "feels X but Y", "I feel … but timeline …", etc.
_INTENT_CONTRADICTION_RE = re.compile(
    r"(?:i\s+feel(?:ing)?[^.?!]{0,80}\bbut\b)|"
    r"(?:\bbut\b[^.?!]{0,40}(?:timeline|astrology|chart|forecast|prediction|signs|points|says))|"
    r"(?:seems? to (?:say|indicate|suggest)\s*otherwise)|"
    r"(?:contradict\w*)|"
    r"(?:on (?:one|the other) hand)|"
    r"(?:yet[^.?!]{0,80}(?:says?|shows?|indicates?))|"
    r"(?:doesn'?t match)",
    re.IGNORECASE,
)

_INTENT_WHY_PATTERN_RE = re.compile(
    r"\b(why (?:do|does|am|is)\s+(?:i|this|it)|why (?:do|does)?\s*"
    r"(?:i|this|it)?\s*keeps?|keeps? happening|"
    r"again and again|over and over|stuck in|same (?:thing|loop|pattern))\b",
    re.IGNORECASE,
)


def detect_question_intent(question: str) -> Dict[str, Any]:
    """
    Detect what kind of question the user is actually asking.

    Returns:
      {
        "primary":     str,                  # primary intent
        "all":         List[str],            # all matched intents (in order)
        "is_contradiction":    bool,
        "is_outlook_timing":   bool,
        "is_why_pattern":      bool,
      }

    Categories (per spec):
      - outlook_timing      ("this year", "next year", "outlook", "timeline", "phase")
      - contradiction       ("I feel X but timeline says Y", "seems to say otherwise")
      - why_pattern         ("why does this keep happening")
      - domain_explanation  (default fallback)
    """
    q = question or ""
    matches: List[str] = []

    is_contradiction = bool(_INTENT_CONTRADICTION_RE.search(q))
    is_outlook = bool(_INTENT_OUTLOOK_RE.search(q))
    is_why = bool(_INTENT_WHY_PATTERN_RE.search(q))

    # Order matters: contradiction is the highest-priority signal because
    # it tells us the user is holding two truths at once.
    if is_contradiction:
        matches.append("contradiction")
    if is_outlook:
        matches.append("outlook_timing")
    if is_why:
        matches.append("why_pattern")
    if not matches:
        matches.append("domain_explanation")

    return {
        "primary":            matches[0],
        "all":                matches,
        "is_contradiction":   is_contradiction,
        "is_outlook_timing":  is_outlook,
        "is_why_pattern":     is_why,
    }


# ---------------------------------------------------------------------------
# GENERIC-FILLER AUDIT (catches the failure modes from the user's complaint)
# ---------------------------------------------------------------------------
#
# These phrases triggered the user's complaint that answers feel generic.
# We flag and retry once with a sharper instruction.

_GENERIC_FILLER_RX = re.compile(
    r"\b("
    r"energetic signal[s]?|"
    r"internal shift[s]?|"
    r"quality of (?:your )?connection[s]?|"
    r"others? need time to catch up|"
    r"cycle of tuning|"
    r"in alignment|"
    r"alignment with|"
    r"evolving|"
    r"on (?:a |this )?journey|"
    r"this is (?:an? |the )?invitation|"
    r"sacred|"
    r"divine|"
    r"the universe|"
    r"higher self|"
    r"trust the process|"
    r"flow with|"
    r"(?:emotional |spiritual )?expansion|"
    r"awakening|"
    r"the lessons? (?:of|in)|"
    r"holding space|"
    r"calling you (?:in|forward|home)|"
    r"deeper truth"
    r")\b",
    re.IGNORECASE,
)

# Hedging language that softens a Mirror answer into vagueness.
_HEDGE_RX = re.compile(
    r"\b(may be|might be|tends to|perhaps|seems? like|kind of|sort of|"
    r"in some ways?|in many ways?|on (?:some|many) levels?|"
    r"a bit|somewhat|relatively|fairly|quite a bit)\b",
    re.IGNORECASE,
)


def audit_generic_filler(answer: str, intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flag answers that fall back to generic spiritual / hedging language
    instead of answering the specific tension the user asked about.

    Returns:
      {
        "flagged":  bool,
        "reasons":  List[str],
        "filler":   List[str],   # specific filler phrases caught
        "hedges":   int,         # count of hedges (≤2 OK, ≥4 flagged)
      }
    """
    out: Dict[str, Any] = {"flagged": False, "reasons": [], "filler": [], "hedges": 0}
    if not isinstance(answer, str) or not answer.strip():
        return out

    filler_hits = _GENERIC_FILLER_RX.findall(answer)
    if filler_hits:
        out["flagged"] = True
        out["filler"] = list(set(s.lower() for s in filler_hits))[:8]
        out["reasons"].append(f"generic_filler ({', '.join(out['filler'])})")

    hedges = _HEDGE_RX.findall(answer)
    out["hedges"] = len(hedges)
    if len(hedges) >= 4:
        out["flagged"] = True
        out["reasons"].append(f"hedging_overload ({len(hedges)} soft modifiers)")

    # Contradiction-specific check: the answer must address the contrast.
    # We require at least one "both can be true" / "different things" / "X
    # but Y" / "what is improving" / "what is not yet" structure.
    if intent.get("is_contradiction"):
        contrast_markers = re.compile(
            r"\b(both (?:can|are) (?:true|valid)|different things|"
            r"two (?:things|truths)|what is (?:actually )?(?:improving|"
            r"changing|getting better|not yet|still under)|"
            r"better (?:does not|doesn't) mean|"
            r"timeline is not saying|"
            r"yes.{0,20}(?:and|but)|"
            r"it (?:can|may) feel|"
            r"calmer.{0,30}not (?:because|that))\b",
            re.IGNORECASE,
        )
        if not contrast_markers.search(answer):
            out["flagged"] = True
            out["reasons"].append("contradiction_not_addressed")

    # Outlook-specific check: must mention the phase/timing dimension.
    if intent.get("is_outlook_timing"):
        timing_markers = re.compile(
            r"\b(phase|this year|tests? whether|what to watch|"
            r"still under pressure|not (?:yet )?(?:resolved|finished|"
            r"smooth)|pattern to watch|the gap|the old pattern)\b",
            re.IGNORECASE,
        )
        if not timing_markers.search(answer):
            out["flagged"] = True
            out["reasons"].append("outlook_lacks_phase_or_timing_anchor")

    return out


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


def _safe_decan_audit(text: str, decan_index: Optional[int]) -> Optional[Dict[str, Any]]:
    """Run decan tone audit, swallowing any error so debug never breaks the response."""
    try:
        if not isinstance(decan_index, int) or decan_index not in (1, 2, 3):
            return None
        from .decan_engine import audit_decan_tone
        return audit_decan_tone(text or "", decan_index)
    except Exception as e:
        logger.warning("[LifeInterpreter] decan audit failed: %s", e)
        return {"pass": True, "reasons": [f"audit_error: {e}"]}


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
    recurrence_data: Optional[Dict[str, Any]] = None,
    activation_now_data: Optional[Dict[str, Any]] = None,
    phase_context: Optional[Dict[str, Any]] = None,
    timeline_context: Optional[Dict[str, Any]] = None,
    intent: Optional[Dict[str, Any]] = None,
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

    # Identity recurrence overlay (subtle anchor — drives the opening
    # line of the answer when recurrence_detected=True).
    rec_block: Dict[str, Any] = {}
    if isinstance(recurrence_data, dict):
        if recurrence_data.get("recurrence_detected"):
            human_label = (recurrence_data.get("human_label") or "").strip()
            if human_label:
                rec_block = {
                    "recurrence_detected": True,
                    "human_label":         _short(human_label, 80),
                    # NOTE: never expose match_count / memory_state to
                    # the LLM either — they're not needed for tone.
                }

    # Activation-Now block — used as TIMING evidence for "why now" and
    # outlook questions. The LLM never references the system that
    # produced these strings.
    ane_block: Dict[str, Any] = {}
    if isinstance(activation_now_data, dict):
        line = (activation_now_data.get("activation_line") or "").strip()
        expl = (activation_now_data.get("activation_explanation") or "").strip()
        pressure = (activation_now_data.get("activation_pressure") or "").strip().lower()
        if line or expl:
            ane_block = {
                "activation_line":        _short(line, 110),
                "activation_explanation": _short(expl, 320),
                "activation_pressure":    pressure or None,
            }

    # Phase context — current/previous/emerging phase labels + dominant
    # domain. Used heavily for outlook_timing questions.
    phase_block: Dict[str, Any] = {}
    if isinstance(phase_context, dict):
        phase_block = {
            "current_phase_label":   _short(str(phase_context.get("current_phase_label") or ""), 80) or None,
            "current_phase_summary": _short(str(phase_context.get("current_phase_summary") or ""), 280) or None,
            "previous_phase_label":  _short(str(phase_context.get("previous_phase_label") or ""), 80) or None,
            "next_phase_label":      _short(str(phase_context.get("next_phase_label") or ""), 80) or None,
            "dominant_domain":       (phase_context.get("dominant_domain") or "") or None,
            "phase_confidence":      (phase_context.get("phase_confidence") or "") or None,
        }
        # Drop the block entirely if every field is empty
        if not any(v for v in phase_block.values()):
            phase_block = {}

    # Timeline context — annual / long-range notes. Only relevant when
    # the user asks about year/timeline/outlook. NEVER quote any source
    # of this data verbatim; treat it as deep ground truth only.
    # Supports BOTH shapes:
    #   1. Legacy: {period, notes, themes}
    #   2. Astrology Timeline Interpreter: {year_theme, current_phase,
    #      next_phase, key_turning_points, domain_relevance,
    #      failure_mode, confidence}
    tl_block: Dict[str, Any] = {}
    if isinstance(timeline_context, dict):
        notes = (timeline_context.get("notes") or "").strip()
        period = (timeline_context.get("period") or "").strip()
        themes = timeline_context.get("themes") or []
        if isinstance(themes, list):
            themes = [str(t).strip() for t in themes if str(t).strip()][:4]

        year_theme = (timeline_context.get("year_theme") or "").strip()
        current_phase = timeline_context.get("current_phase") or {}
        next_phase = timeline_context.get("next_phase") or {}
        key_tps = timeline_context.get("key_turning_points") or []
        if isinstance(key_tps, list):
            key_tps = [tp for tp in key_tps if isinstance(tp, dict)][:3]
        domain_rel = timeline_context.get("domain_relevance") or {}
        if not isinstance(domain_rel, dict):
            domain_rel = {}
        failure_mode = (timeline_context.get("failure_mode") or "").strip()
        confidence = (timeline_context.get("confidence") or "").strip()

        has_anything = (
            notes or period or themes
            or year_theme or current_phase or next_phase
            or key_tps or domain_rel or failure_mode
        )
        if has_anything:
            tl_block = {
                "period":               _short(period, 80) or None,
                "notes":                _short(notes, 400) or None,
                "themes":               themes or None,
                "year_theme":           _short(year_theme, 200) or None,
                "current_phase":        current_phase or None,
                "next_phase":           next_phase or None,
                "key_turning_points":   key_tps or None,
                "domain_relevance":     domain_rel or None,
                "failure_mode":         _short(failure_mode, 240) or None,
                "confidence":           confidence or None,
            }

    # Question intent — drives the answer structure (contradiction /
    # outlook / why_pattern / domain_explanation).
    intent_block: Dict[str, Any] = {}
    if isinstance(intent, dict) and intent.get("primary"):
        intent_block = {
            "primary":           intent.get("primary"),
            "is_contradiction":  bool(intent.get("is_contradiction")),
            "is_outlook_timing": bool(intent.get("is_outlook_timing")),
            "is_why_pattern":    bool(intent.get("is_why_pattern")),
        }

    return {
        "chip":            chip_domain,
        "question":        _short(question, 600),
        "intent":          intent_block,
        "role_card":       rc,
        "domain_synthesis": ds,
        "domain_origin":   do,
        "cross_domain_pattern": cdp,
        "recurrence":      rec_block,
        "activation_now":  ane_block,
        "phase_context":   phase_block,
        "timeline_context": tl_block,
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
    rec = ctx.get("recurrence") or {}
    if rec.get("recurrence_detected") and rec.get("human_label"):
        lines.append(
            "IDENTITY RECURRENCE — the user is in a returning/recurring "
            "loop. Open the answer with the human_label below as its OWN "
            "first line, exactly as written (no quotes, no rewording, "
            "no decoration). Then continue with the rest of your answer "
            "in your normal voice. Slightly INCREASE confidence (more "
            "direct, less exploratory) — this user has earned recognition."
        )
        lines.append(f"  - human_label (use as line 1, verbatim): {rec['human_label']}")
        lines.append("")

    intent = ctx.get("intent") or {}
    if intent.get("primary"):
        lines.append("QUESTION INTENT — what kind of question this is:")
        lines.append(f"  - primary:           {intent.get('primary')}")
        lines.append(f"  - is_contradiction:  {intent.get('is_contradiction')}")
        lines.append(f"  - is_outlook_timing: {intent.get('is_outlook_timing')}")
        lines.append(f"  - is_why_pattern:    {intent.get('is_why_pattern')}")
        if intent.get("is_contradiction"):
            lines.append(
                "  → ANSWER THE CONTRADICTION DIRECTLY using the 4-part "
                "structure (BLADE LINE / BOTH CAN BE TRUE / PHASE READING / "
                "GROUNDED OUTLOOK). Do NOT just restate the domain pattern."
            )
        elif intent.get("is_outlook_timing"):
            lines.append(
                "  → ANCHOR the answer in phase + timing. Lean on "
                "phase_context and activation_now. End with 'what to "
                "watch / what is still under pressure'. Do NOT predict."
            )
        elif intent.get("is_why_pattern"):
            lines.append(
                "  → Show the MECHANISM. Use cross_domain_pattern + "
                "recurrence to anchor the answer. Make it land."
            )
        lines.append("")

    phase_ctx = ctx.get("phase_context") or {}
    if phase_ctx and any(phase_ctx.values()):
        lines.append("PHASE CONTEXT — where the user is in their life arc:")
        if phase_ctx.get("current_phase_label"):
            lines.append(f"  - current phase: {phase_ctx['current_phase_label']}")
        if phase_ctx.get("current_phase_summary"):
            lines.append(f"      summary: {phase_ctx['current_phase_summary']}")
        if phase_ctx.get("previous_phase_label"):
            lines.append(f"  - previous phase: {phase_ctx['previous_phase_label']}")
        if phase_ctx.get("next_phase_label"):
            lines.append(f"  - emerging phase: {phase_ctx['next_phase_label']}")
        if phase_ctx.get("dominant_domain"):
            lines.append(f"  - dominant domain: {phase_ctx['dominant_domain']}")
        lines.append(
            "  Use phase context to ground outlook/timing answers. NEVER "
            "name 'phase' as a system; speak about 'this period' or 'this "
            "year' or 'this stretch'."
        )
        lines.append("")

    ane = ctx.get("activation_now") or {}
    if ane and (ane.get("activation_line") or ane.get("activation_explanation")):
        lines.append(
            "ACTIVATION NOW — what is making the pattern feel active "
            "right now (already verified; safe to use as TIMING evidence):"
        )
        if ane.get("activation_line"):
            lines.append(f"  - line: {ane['activation_line']}")
        if ane.get("activation_explanation"):
            lines.append(f"  - reason: {ane['activation_explanation']}")
        if ane.get("activation_pressure"):
            lines.append(f"  - pressure: {ane['activation_pressure']}")
        lines.append(
            "  Use this to answer 'why now' / outlook timing questions. "
            "Paraphrase, don't quote verbatim."
        )
        lines.append("")

    tl = ctx.get("timeline_context") or {}
    # Recognise both the legacy {period, notes, themes} shape and the
    # richer Astrology Timeline Interpreter shape (year_theme,
    # current_phase, next_phase, key_turning_points, domain_relevance,
    # failure_mode, confidence). Either is sufficient to render.
    has_legacy = bool(tl.get("notes") or tl.get("themes"))
    has_rich = bool(
        tl.get("year_theme")
        or tl.get("current_phase")
        or tl.get("next_phase")
        or tl.get("key_turning_points")
        or tl.get("domain_relevance")
    )
    if tl and (has_legacy or has_rich):
        lines.append("TIMELINE CONTEXT — long-range/annual signals:")
        # Legacy fields (still supported for back-compat)
        if tl.get("period"):
            lines.append(f"  - period: {tl['period']}")
        if tl.get("notes"):
            lines.append(f"  - notes: {tl['notes']}")
        if tl.get("themes"):
            lines.append(f"  - themes: {', '.join(tl['themes'])}")
        # Richer structured fields (Astrology Timeline Interpreter)
        if tl.get("year_theme"):
            lines.append(f"  - year_theme: {tl['year_theme']}")
        cur_ph = tl.get("current_phase") or {}
        if cur_ph:
            cp_name = cur_ph.get("name") or ""
            cp_press = cur_ph.get("pressure_type") or ""
            cp_desc = cur_ph.get("description") or ""
            cp_period = cur_ph.get("period") or ""
            lines.append(
                f"  - current period: {cp_name}"
                + (f" ({cp_period})" if cp_period else "")
            )
            if cp_press:
                lines.append(f"      pressure: {cp_press}")
            if cp_desc:
                lines.append(f"      what's happening: {cp_desc}")
        nxt_ph = tl.get("next_phase") or {}
        if nxt_ph:
            np_name = nxt_ph.get("name") or ""
            np_press = nxt_ph.get("pressure_type") or ""
            np_desc = nxt_ph.get("description") or ""
            np_period = nxt_ph.get("period") or ""
            lines.append(
                f"  - emerging period: {np_name}"
                + (f" ({np_period})" if np_period else "")
            )
            if np_press:
                lines.append(f"      pressure: {np_press}")
            if np_desc:
                lines.append(f"      what's coming: {np_desc}")
        tps = tl.get("key_turning_points") or []
        if tps:
            lines.append("  - key turning points:")
            for tp in tps[:3]:
                bits: List[str] = []
                if tp.get("timing"):
                    bits.append(f"timing={tp['timing']}")
                if tp.get("type"):
                    bits.append(f"type={tp['type']}")
                if tp.get("what_activates"):
                    bits.append(f"activates={tp['what_activates']}")
                if tp.get("what_becomes_clear"):
                    bits.append(f"clarity={tp['what_becomes_clear']}")
                if tp.get("if_avoided"):
                    bits.append(f"if_avoided={tp['if_avoided']}")
                lines.append("      • " + " | ".join(bits))
        dr = tl.get("domain_relevance") or {}
        if dr:
            chip = (ctx.get("chip") or "").lower()
            chip_note = dr.get(chip)
            if chip_note:
                lines.append(f"  - domain note ({chip}): {chip_note}")
            other = [(k, v) for k, v in dr.items() if k != chip]
            if other:
                lines.append(
                    "  - other domains in play: "
                    + "; ".join(f"{k}: {v}" for k, v in other[:3])
                )
        if tl.get("failure_mode"):
            lines.append(f"  - failure mode: {tl['failure_mode']}")
        if tl.get("confidence"):
            lines.append(f"  - confidence: {tl['confidence']}")
        lines.append(
            "  Use this for 'this year' / 'outlook' / contradiction "
            "questions. Reason WITH the timeline, do NOT summarise it. "
            "NEVER mention astrology / chart / transit / decan / source. "
            "Speak as if describing the period itself. Acceptable phrasings: "
            "'The timeline is not saying no — it is showing pressure around…', "
            "'What feels better now may be real, but the next period still "
            "tests…', 'What improves is… What remains under pressure is…', "
            "'The pattern to watch is…'."
        )
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
    decan_index: Optional[int] = None,
    recurrence_data: Optional[Dict[str, Any]] = None,
    activation_now_data: Optional[Dict[str, Any]] = None,
    phase_context: Optional[Dict[str, Any]] = None,
    timeline_context: Optional[Dict[str, Any]] = None,
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

    # Detect question intent so the LLM can answer the SPECIFIC tension
    # (contradiction / outlook / why_pattern) instead of falling back to
    # a generic pattern recap.
    intent = detect_question_intent(q)

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
        recurrence_data=recurrence_data,
        activation_now_data=activation_now_data,
        phase_context=phase_context,
        timeline_context=timeline_context,
        intent=intent,
    )
    user_msg = _format_context_for_llm(ctx)

    # Decan tone (Rule 16) — invisible final-polish layer. We override the
    # chat's system prompt with base + decan addendum. Decan is INVISIBLE:
    # never referenced in output. If audit later flags the result, the
    # pre-decan version of the engine is preserved (the addendum is
    # additive, never replaces the base prompt's hard rules).
    decan_addendum = ""
    if isinstance(decan_index, int) and decan_index in (1, 2, 3):
        try:
            from .decan_engine import build_decan_addendum
            decan_addendum = build_decan_addendum(decan_index)
        except Exception as e:
            logger.warning("[LifeInterpreter] decan addendum failed: %s", e)
            decan_addendum = ""

    answer_raw: Optional[str] = None
    render_error: Optional[str] = None
    if llm_chat_factory is not None:
        try:
            chat: LlmChat = llm_chat_factory()
            # Apply decan tone polish to the system prompt for this turn
            if decan_addendum and hasattr(chat, "with_system_message"):
                try:
                    chat = chat.with_system_message(
                        _LIFE_INTERPRETER_SYSTEM_PROMPT + decan_addendum
                    )
                except Exception:
                    # Fallback: try direct attribute assignment (best-effort)
                    try:
                        chat.system_message = (
                            _LIFE_INTERPRETER_SYSTEM_PROMPT + decan_addendum
                        )
                    except Exception:
                        pass
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

    # ------------------------------------------------------------------
    # GENERIC-FILLER AUDIT + RETRY (Phase 7 — answer-quality enforcement)
    # ------------------------------------------------------------------
    # If the answer falls back to vague spiritual filler OR (for
    # contradiction/outlook questions) fails to address the actual
    # tension, retry once with a sharper instruction.
    audit_quality = audit_generic_filler(answer, intent)
    quality_retry_used = False
    if audit_quality.get("flagged") and llm_chat_factory is not None:
        logger.warning(
            "[LifeInterpreter] answer-quality audit flagged (intent=%s, "
            "reasons=%s) — retrying once",
            intent.get("primary"), audit_quality.get("reasons"),
        )
        retry_hint = (
            "\n\n=== RETRY (CRITICAL — your previous answer was REJECTED) ===\n"
            "Your previous draft was flagged for: "
            + "; ".join(audit_quality.get("reasons") or [])
            + ".\n\n"
            "ANSWER THE EXACT TENSION IN THE USER'S QUESTION.\n"
            "Do NOT summarize the relationship pattern.\n"
            "Do NOT use any of: energetic signal, internal shift, quality "
            "of connection, in alignment, evolving, expansion, awakening, "
            "lessons, journey, the universe, divine, sacred, trust the "
            "process, holding space, calling you, deeper truth, "
            "invitation, higher self.\n"
        )
        if intent.get("is_contradiction"):
            retry_hint += (
                "This is a CONTRADICTION question. Use the 4-part "
                "structure:\n"
                "  1) BLADE LINE — sharp first sentence naming the tension\n"
                "  2) BOTH CAN BE TRUE — explain how felt sense AND "
                "timeline can both be valid\n"
                "  3) PHASE READING — anchor in phase + activation_now\n"
                "  4) GROUNDED OUTLOOK — what is improving, what is "
                "still under pressure, what to watch (NEVER predict)\n"
            )
        elif intent.get("is_outlook_timing"):
            retry_hint += (
                "This is an OUTLOOK/TIMING question. Anchor in phase + "
                "activation_now. End with 'what to watch / what is still "
                "under pressure'. Do NOT predict.\n"
            )
        retry_user_msg = user_msg + retry_hint
        try:
            chat2: LlmChat = llm_chat_factory()
            if hasattr(chat2, "with_system_message"):
                try:
                    chat2 = chat2.with_system_message(
                        _LIFE_INTERPRETER_SYSTEM_PROMPT
                        + (decan_addendum if isinstance(decan_index, int)
                           and decan_index in (1, 2, 3) else "")
                    )
                except Exception:
                    pass
            resp2 = await chat2.send_message(UserMessage(text=retry_user_msg))
            answer_raw2 = resp2 if isinstance(resp2, str) else str(resp2)
            answer_text2, follow_ups2, _ = _parse_interpreter_json(answer_raw2, chip)
            if answer_text2 and answer_text2.strip():
                answer2 = re.sub(
                    r"\s+\n", "\n",
                    answer_text2.replace("\\n", "\n").strip(),
                )
                if len(answer2) > 2400:
                    answer2 = answer2[:2400].rsplit(" ", 1)[0] + "…"
                answer2 = _ensure_paragraphs(answer2, target=3)
                audit_quality2 = audit_generic_filler(answer2, intent)
                # Prefer retry if it cleaned up at least one issue OR
                # at least did not get worse.
                if (not audit_quality2.get("flagged")) or (
                    len(audit_quality2.get("reasons") or [])
                    < len(audit_quality.get("reasons") or [])
                ):
                    answer = answer2
                    if isinstance(follow_ups2, list) and len(follow_ups2) >= 2:
                        follow_ups = follow_ups2
                    audit_quality = audit_quality2
                    quality_retry_used = True
        except Exception as e:
            logger.warning("[LifeInterpreter] retry pass failed: %s", e)

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
        "generator_version": "life_interpreter_v7_question_tension",
        "debug": {
            "llm_used":       answer_raw is not None and render_error is None,
            "render_error":   render_error,
            "parse_error":    parse_error,
            "banned_hits":    banned_hits,
            "decan_index":    decan_index if isinstance(decan_index, int) else None,
            "decan_audit":    (
                _safe_decan_audit(answer, decan_index)
                if isinstance(decan_index, int) and decan_index in (1, 2, 3)
                else None
            ),
            "intent":             intent,
            "quality_audit":      audit_quality,
            "quality_retry_used": quality_retry_used,
            "context_keys":   {
                "has_role_card":          bool(ctx["role_card"]),
                "has_domain_synthesis":   bool(ctx["domain_synthesis"]),
                "has_current_phase":      bool(ctx["current_phase"]),
                "has_cross_domain":       bool(ctx.get("cross_domain_pattern")),
                "has_recurrence":         bool((ctx.get("recurrence") or {}).get("recurrence_detected")),
                "has_activation_now":     bool(ctx.get("activation_now")),
                "has_phase_context":      bool(ctx.get("phase_context")),
                "has_timeline_context":   bool(ctx.get("timeline_context")),
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
