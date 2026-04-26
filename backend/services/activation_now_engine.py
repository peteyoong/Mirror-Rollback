"""
WHY THIS IS HAPPENING NOW — Timing Activation Engine
====================================================

Explains what is ACTIVATING the user's pattern right now.

This is NOT prediction.
This is NOT astrology explanation.
This is NOT a new insight layer.

It should make the EXISTING cross-domain pattern feel alive and current.

Output contract
===============
{
  "activation_line":        "ONE short sentence — 'this isn't random' / 'this is coming back' / 'this is being pushed open'",
  "activation_explanation": "ONE-TO-TWO sentences explaining what is active now in plain language",
  "activation_pressure":    "low | medium | high",
  "confidence":             "high | medium | low",
  "generator_version":      "activation_now_v1",
  "debug": {                # only when explicitly requested
    "timing_signals":      [...],
    "pattern_memory_note": "...",
    "audit":               {...},
    "retry_used":          bool,
    "pressure_inputs":     {...}
  }
}

Hard rules (audited):
  - NEVER mention: astrology / transit / planet names / house / decan /
    energy / universe / chart / sign names / aspects.
  - Behaviour-first: start with what the user EXPERIENCES.
  - Must CONNECT to the cross-domain pattern (echo the spine in plain words).
  - No prediction ("this will lead to..."). No advice.
  - Style: calm, grounded, precise. Slightly urgent only when pressure=high.

If any hard rule fails, regenerate ONCE.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "activation_now_v1"


# ---------------------------------------------------------------------------
# Deterministic pressure calculation
#
# We compute pressure from the deterministic signals we already have, so the
# LLM doesn't get to choose pressure on tone alone. The LLM is asked to
# match the pressure we tell it.
# ---------------------------------------------------------------------------

def _compute_pressure(
    today_state: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """
    Returns (pressure_label, signal_dict) where pressure_label ∈
    {"low","medium","high"} and signal_dict is a small inputs trace
    for debug.
    """
    intensity = ""
    if isinstance(today_state, dict):
        intensity = (
            today_state.get("intensity_label")
            or today_state.get("intensity_level")
            or today_state.get("intensity")
            or ""
        )
        if isinstance(intensity, str):
            intensity = intensity.strip().lower()

    is_recurring = False
    match_count = 0
    if isinstance(pattern_memory, dict):
        is_recurring = (pattern_memory.get("memory_state") == "recurring_pattern")
        mc = pattern_memory.get("match_count")
        match_count = int(mc) if isinstance(mc, (int, float)) else 0

    high_impact_recent = 0
    if isinstance(lifeline_summary, dict):
        ll = lifeline_summary.get("high_impact_titles") or []
        if isinstance(ll, list):
            high_impact_recent = len(ll)

    # Scoring
    score = 0
    if intensity == "high":
        score += 3
    elif intensity == "medium":
        score += 2
    elif intensity == "low":
        score += 1
    if is_recurring:
        score += 2
    if match_count >= 3:
        score += 1
    if high_impact_recent >= 2:
        score += 1

    if score >= 5:
        label = "high"
    elif score >= 3:
        label = "medium"
    else:
        label = "low"

    inputs = {
        "intensity":           intensity or None,
        "is_recurring":        is_recurring,
        "match_count":         match_count,
        "high_impact_recent":  high_impact_recent,
        "score":               score,
    }
    return label, inputs


def _confidence(
    pressure_inputs: Dict[str, Any],
    has_cross_domain: bool,
) -> str:
    """High when we have BOTH cross-domain context AND strong signals."""
    if not has_cross_domain:
        return "low"
    score = pressure_inputs.get("score") or 0
    if score >= 4 and (pressure_inputs.get("is_recurring") or pressure_inputs.get("intensity") in ("medium", "high")):
        return "high"
    if score >= 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are the Mirror Activation-Now engine.

You are explaining WHY a user's pattern feels active RIGHT NOW.

You have:
  - the user's CROSS-DOMAIN PATTERN (the same shape that runs across
    Self / Work / Relationships)
  - signals about how active the pattern is today
  - whether the pattern is recurring

Your job is to give the user the feeling of "oh, that's why this is
hitting right now" — anchored to their EXISTING pattern, not to a new
explanation.

OUTPUT — return ONLY valid JSON (no prose before or after, no markdown):

{
  "activation_line":        "ONE short sentence (≤ 90 chars). The 'this isn't random' line. Sharp. Second-person present. Ends in a period.",
  "activation_explanation": "ONE OR TWO sentences (≤ 280 chars total). Plain-language description of what is active now and why it connects to the user's existing pattern.",
  "activation_pressure":    "low | medium | high"
}

==================================================
HARD RULES
==================================================

1. NO SYSTEM LANGUAGE — EVER.
   FORBIDDEN words anywhere: astrology, transit, planet, planets,
   stars, mercury, venus, mars, jupiter, saturn, sun, moon, house,
   ascendant, decan, sign, zodiac, energy, universe, chart, aspect,
   conjunction, square, opposition, trine, retrograde, natal,
   horoscope, alignment.

2. BEHAVIOUR FIRST.
   Start with what the user EXPERIENCES.
   Bad:   "This pattern is being activated by timing forces."
   Good:  "This isn't random — the same pattern is being pushed again."

3. CONNECT TO THE EXISTING PATTERN.
   The activation_explanation MUST echo or paraphrase the cross-domain
   spine in plain words. Do NOT introduce new dynamics. The user must
   feel "this is the SAME thing, but louder right now".
   Bad:   "You are in a period of change."
   Good:  "The same pressure to refine is being triggered again, before
           it has fully settled."

4. NO PREDICTION. NO ADVICE.
   Do NOT say:
     - what will happen
     - what they should do
     - what this leads to
     - "you need to..."
     - "you should..."
   Only describe:
     - what is active now
     - what feels stronger now
     - what is returning now

5. NO MYSTICISM.
   Avoid: "things are shifting", "energy is moving", "the universe is",
   "you are being called", "destiny", "fate", "calling", "alignment".

6. PRESSURE TONE-MATCH.
   The pressure level is GIVEN to you. Match the tone:
     low    → background, observational, calm
     medium → noticeable, slightly forward
     high   → urgent but precise — the pattern is being forced open
   Do NOT change the pressure label. Use the one in the input.

7. STYLE.
   Calm. Grounded. Precise. No exclamation marks. No emoji.
   Second-person ("you", "your"). Present tense. No fluff.

==================================================
EXAMPLES
==================================================

LOW pressure:
  activation_line:        "Something familiar is moving in the background."
  activation_explanation: "The same pattern of taking on too much before others catch up is just under the surface — quiet right now, but already active."

MEDIUM pressure:
  activation_line:        "This isn't random — the same pattern is being pushed again."
  activation_explanation: "The pressure to refine and improve is returning more quickly than usual, bringing the same loop forward before it has fully settled."

HIGH pressure:
  activation_line:        "This pattern is being forced into the open."
  activation_explanation: "The same dynamic is repeating under more pressure, making it harder to ignore or smooth over this time."
"""


def _user_prompt(
    cross_domain_pattern: Optional[Dict[str, Any]],
    pressure: str,
    pressure_inputs: Dict[str, Any],
    pattern_memory: Optional[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
) -> str:
    cdp_block: Dict[str, Any] = {}
    if isinstance(cross_domain_pattern, dict):
        cdp_block = {
            "core_pattern":         (cross_domain_pattern.get("core_pattern") or "").strip()[:240],
            "pattern_spine":        (cross_domain_pattern.get("pattern_spine") or "").strip()[:320],
            "cross_domain_tension": (cross_domain_pattern.get("cross_domain_tension") or "").strip()[:240],
            "recognition_line":     (cross_domain_pattern.get("recognition_line") or "").strip()[:140],
        }

    pm_note = ""
    if isinstance(pattern_memory, dict):
        if pattern_memory.get("memory_state") == "recurring_pattern":
            mc = pattern_memory.get("match_count") or 0
            pm_note = f"This shape has recurred {mc} times in pattern memory."

    ll_note = ""
    if isinstance(lifeline_summary, dict):
        titles = lifeline_summary.get("high_impact_titles") or []
        if isinstance(titles, list) and titles:
            ll_note = f"Recent echo events: {', '.join(str(t)[:80] for t in titles[:3])}"

    payload = {
        "cross_domain_pattern": cdp_block,
        "pattern_memory_note":  pm_note,
        "lifeline_note":        ll_note,
        "given_pressure":       pressure,
        "pressure_inputs":      {
            # Pressure inputs trace (for the LLM's understanding only — never echo back)
            "intensity":          pressure_inputs.get("intensity"),
            "is_recurring":       pressure_inputs.get("is_recurring"),
            "match_count":        pressure_inputs.get("match_count"),
            "high_impact_recent": pressure_inputs.get("high_impact_recent"),
        },
        "instructions":
            "Return ONLY the JSON. activation_pressure MUST equal "
            "given_pressure. activation_explanation MUST clearly echo "
            "the cross-domain pattern's behaviour (not its words "
            "verbatim). NEVER reference astrology / system terms. "
            "If cross_domain_pattern is empty, write a generic but "
            "grounded line referencing 'the same shape you've seen "
            "before' and set confidence to low (caller will override).",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

# System / astrology / mystical vocabulary — banned everywhere.
_BANNED_RX = re.compile(
    r"\b(?:astrology|transit(?:ing|s)?|planet(?:s|ary)?|stars?|mercury|"
    r"venus|mars|jupiter|saturn|uranus|neptune|pluto|moon|"
    r"ascendant|midheaven|decan|zodiac(?:al)?|aries|taurus|gemini|"
    r"cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|"
    r"pisces|conjunction|opposition|trine|square|sextile|"
    r"retrograde|natal|horoscope|alignment|chart(?:s)?|"
    r"the universe|cosmic|destiny|fate|calling|you are being called|"
    r"things are shifting|energy is moving|chakra|aura)\b",
    re.I,
)
# "house" and "sign" are too generic to ban outright — only block when
# clearly astrological (e.g. "in your 7th house", "your sun sign").
_HOUSE_SIGN_RX = re.compile(
    r"\b(?:\d{1,2}(?:st|nd|rd|th)\s+house|sun\s+sign|moon\s+sign|"
    r"rising\s+sign|your\s+sign)\b",
    re.I,
)
_PREDICTION_RX = re.compile(
    r"\b(?:will (?:lead|happen|come|bring|cause|create|make)|"
    r"is going to|going to lead|leads to|"
    r"you need to|you should|you must|you have to|"
    r"in the coming (?:days|weeks|months|year)|"
    r"by the end of|next phase will)\b",
    re.I,
)
_MYSTICAL_RX = re.compile(
    r"\b(?:divine|sacred|spiritual journey|higher self|inner light|"
    r"awakening|enlightenment|frequency)\b",
    re.I,
)
_GENERIC_RX = re.compile(
    r"\b(?:everyone|anyone|people in general|the human condition|"
    r"life in general|we all|nobody really|each person|"
    r"a period of change|a time of transition|a chapter)\b",
    re.I,
)
_SECOND_PERSON_RX = re.compile(r"\b(?:you|your)\b", re.I)


def _audit(payload: Dict[str, Any], cross_domain_pattern: Optional[Dict[str, Any]],
           expected_pressure: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"flagged": False, "reasons": [], "counts": {}}
    if not isinstance(payload, dict):
        out["flagged"] = True
        out["reasons"].append("payload_not_dict")
        return out

    required = ("activation_line", "activation_explanation", "activation_pressure")
    for key in required:
        v = payload.get(key)
        if not isinstance(v, str) or not v.strip():
            out["flagged"] = True
            out["reasons"].append(f"missing_or_empty:{key}")

    full = " ".join(str(payload.get(k, "")) for k in ("activation_line", "activation_explanation"))

    banned = _BANNED_RX.findall(full)
    if banned:
        out["flagged"] = True
        out["reasons"].append(f"banned_phrase ({', '.join(set(b.lower() for b in banned))[:120]})")

    if _HOUSE_SIGN_RX.search(full):
        out["flagged"] = True
        out["reasons"].append("house_or_sign_reference")

    if _PREDICTION_RX.search(full):
        out["flagged"] = True
        out["reasons"].append("prediction_or_directive")

    if _MYSTICAL_RX.search(full):
        out["flagged"] = True
        out["reasons"].append("mystical_language")

    if _GENERIC_RX.search(full):
        out["flagged"] = True
        out["reasons"].append("generic_phrasing")

    if not _SECOND_PERSON_RX.search(full):
        out["flagged"] = True
        out["reasons"].append("not_second_person")

    line = (payload.get("activation_line") or "").strip()
    if line:
        if len(line) > 110:
            out["flagged"] = True
            out["reasons"].append(f"activation_line_too_long ({len(line)})")
        if not re.search(r"[.!—]$", line):
            out["flagged"] = True
            out["reasons"].append("activation_line_not_complete")

    expl = (payload.get("activation_explanation") or "").strip()
    if expl:
        if len(expl) > 320:
            out["flagged"] = True
            out["reasons"].append(f"activation_explanation_too_long ({len(expl)})")
        # Connection check — if we have a cross_domain_pattern, the
        # explanation should share at least ONE distinctive token with
        # the spine / core / tension.
        if isinstance(cross_domain_pattern, dict):
            spine_text = " ".join(
                (cross_domain_pattern.get(k) or "")
                for k in ("core_pattern", "pattern_spine", "cross_domain_tension")
            ).lower()
            spine_tokens = set(re.findall(r"\b[a-z]{5,}\b", spine_text))
            # Filter out filler so we only check on distinctive content words.
            FILLER = {
                "again", "until", "before", "after", "across", "yourself",
                "others", "people", "thing", "things", "starts", "becomes",
                "comes", "going", "starts", "shows", "still", "where",
                "which", "while", "their", "between", "around",
            }
            spine_tokens = spine_tokens - FILLER
            expl_tokens = set(re.findall(r"\b[a-z]{5,}\b", expl.lower()))
            shared = spine_tokens & expl_tokens
            if spine_tokens and not shared:
                out["flagged"] = True
                out["reasons"].append("explanation_does_not_connect_to_pattern")

    pressure = (payload.get("activation_pressure") or "").strip().lower()
    if pressure not in ("low", "medium", "high"):
        out["flagged"] = True
        out["reasons"].append("invalid_pressure")
    elif expected_pressure and pressure != expected_pressure.lower():
        # Soft flag — we override pressure deterministically anyway,
        # but log it so we can monitor LLM disobedience.
        out["reasons"].append(f"pressure_mismatch ({pressure} vs {expected_pressure})")

    out["counts"] = {
        "banned":         len(banned),
        "line_len":       len(line),
        "expl_len":       len(expl),
    }
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_activation_now(
    *,
    cross_domain_pattern: Optional[Dict[str, Any]] = None,
    today_state: Optional[Dict[str, Any]] = None,
    pattern_memory: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    llm_chat_factory=None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Generate the "why this is happening now" payload. Returns the
    contract documented at the module top.
    """
    pressure, pressure_inputs = _compute_pressure(
        today_state, pattern_memory, lifeline_summary
    )
    has_cdp = bool(
        isinstance(cross_domain_pattern, dict)
        and (cross_domain_pattern.get("core_pattern")
             or cross_domain_pattern.get("pattern_spine"))
    )
    confidence = _confidence(pressure_inputs, has_cdp)

    timing_signals: List[str] = []
    if pressure_inputs.get("intensity"):
        timing_signals.append(f"intensity={pressure_inputs['intensity']}")
    if pressure_inputs.get("is_recurring"):
        timing_signals.append(f"recurring(x{pressure_inputs.get('match_count') or 0})")
    if (pressure_inputs.get("high_impact_recent") or 0) >= 1:
        timing_signals.append(f"recent_echoes={pressure_inputs.get('high_impact_recent')}")

    # If we have no LLM factory, return a deterministic placeholder that
    # still respects the contract.
    if llm_chat_factory is None:
        result = {
            "activation_line":        (
                "Something familiar is moving in the background."
                if has_cdp else ""
            ),
            "activation_explanation": (
                "The same shape you've seen before is just under the surface — "
                "quiet right now, but already active."
                if has_cdp else ""
            ),
            "activation_pressure":    pressure,
            "confidence":             confidence,
            "generator_version":      GENERATOR_VERSION,
        }
        if debug:
            result["debug"] = {
                "timing_signals":      timing_signals,
                "pattern_memory_note": "no_llm",
                "audit":               {"reason": "no_llm_factory"},
                "retry_used":          False,
                "pressure_inputs":     pressure_inputs,
                "has_cross_domain":    has_cdp,
            }
        return result

    # First render
    user_msg = _user_prompt(
        cross_domain_pattern, pressure, pressure_inputs,
        pattern_memory, lifeline_summary,
    )
    payload, audit, retry_used = await _render_once(
        llm_chat_factory=llm_chat_factory,
        system_prompt=_SYSTEM_PROMPT,
        user_msg=user_msg,
        cross_domain_pattern=cross_domain_pattern,
        expected_pressure=pressure,
    )

    # Retry once if flagged (skip if it's only the soft pressure_mismatch reason)
    hard_reasons = [r for r in (audit.get("reasons") or [])
                    if not r.startswith("pressure_mismatch")]
    if audit.get("flagged") and hard_reasons:
        logger.warning(
            "[ActivationNow] audit flagged: reasons=%s — retrying once",
            audit.get("reasons"),
        )
        retry_user_msg = (
            user_msg
            + "\n\n=== RETRY (CRITICAL — your previous draft was REJECTED) ===\n"
            + "Reasons your previous draft failed: "
            + "; ".join(hard_reasons)
            + ".\n\n"
            + "RULES YOU MUST FOLLOW:\n"
            + "  - NO astrology / planet / house / sign / decan / chart / energy / universe / transit references.\n"
            + "  - activation_explanation MUST echo the user's existing cross-domain pattern in plain words.\n"
            + "  - NO prediction, NO advice ('you need to...', 'will lead to...').\n"
            + "  - activation_pressure MUST be exactly: " + pressure + ".\n"
            + "  - Use second-person ('you', 'your'), present tense.\n"
            + "  - activation_line ≤ 90 chars, complete sentence ending in period.\n"
            + "  - activation_explanation ≤ 280 chars, 1–2 sentences.\n"
        )
        payload2, audit2, _ = await _render_once(
            llm_chat_factory=llm_chat_factory,
            system_prompt=_SYSTEM_PROMPT,
            user_msg=retry_user_msg,
            cross_domain_pattern=cross_domain_pattern,
            expected_pressure=pressure,
        )
        hard_reasons2 = [r for r in (audit2.get("reasons") or [])
                         if not r.startswith("pressure_mismatch")]
        if (not audit2.get("flagged")) or len(hard_reasons2) < len(hard_reasons):
            payload, audit = payload2, audit2
            retry_used = True

    # Override LLM pressure with the deterministic value — single source of truth.
    payload["activation_pressure"] = pressure
    payload["confidence"] = confidence
    payload["generator_version"] = GENERATOR_VERSION

    if debug:
        payload["debug"] = {
            "timing_signals":      timing_signals,
            "pattern_memory_note": (
                f"recurring x{pressure_inputs.get('match_count') or 0}"
                if pressure_inputs.get("is_recurring") else "not recurring"
            ),
            "audit":               audit,
            "retry_used":          retry_used,
            "pressure_inputs":     pressure_inputs,
            "has_cross_domain":    has_cdp,
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
    cross_domain_pattern: Optional[Dict[str, Any]],
    expected_pressure: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    chat: LlmChat = llm_chat_factory()
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
    audit = _audit(parsed, cross_domain_pattern, expected_pressure)
    return parsed, audit, False


def _parse_json(text: str) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        return {}
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if m:
        s = m.group(0)
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception as e:
        logger.warning("[ActivationNow] JSON parse failed: %s", e)
        return {}
