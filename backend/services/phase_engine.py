"""
Mirror Phase Engine
===================

Produces a narrative *phase timeline* across a user's life: 3-5 phases describing
how the SAME pattern has evolved over time, with exactly one current phase.

This is NOT an event list. A phase is a way the user was operating — a pattern
expressing itself over a stretch of time.

Inputs (fed from server.py):
  * role_card          — the deterministic role seeds (role / tension / distortion / orientation)
  * domain_weights     — output of life_synthesis_engine.derive_domain_weights
  * pattern_memory     — output of server._load_pattern_memory_for_user
  * lifeline_summary   — output of server._load_lifeline_summary_for_user
  * today_state        — {"intensity_level": "low"|"medium"|"high"}

Output contract (JSON only, no markdown, no explanation):
  {
    "phases": [
      {
        "label": "Short 3-6 word phase name",
        "description": "1-2 sentence summary of how pattern behaved",
        "dominant_domain": "work|relationships|self",
        "pattern_expression": "1 sentence — the pattern's active form this phase",
        "is_current": true|false,
        "confidence": "high|medium|low"
      },
      ...
    ]
  }

Invariants enforced by this module (post-LLM):
  * Exactly one phase has is_current=true (forced if LLM returns 0 or >1).
  * Between 3 and 5 phases.
  * Each phase has the required fields as non-empty strings.
  * No system/framework language ("lifeline", "pattern memory", "astrology",
    "domain weight", "score") leaks into any user-facing field.

One LLM call per user. Deterministic skeleton fallback when LLM is unavailable
or returns junk.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — verbatim user spec (adjusted for our JSON contract)
# ---------------------------------------------------------------------------

_PHASE_SYSTEM_PROMPT = """You are the Mirror Phase Engine.

Your role is NOT to list events.

Your role is to:
- detect phases in the user's life
- group time into meaningful segments
- describe how the user's pattern has evolved across those phases
- identify what is changing now

==================================================
OUTPUT STRUCTURE
==================================================

Return ONLY valid JSON (no markdown, no explanation):

{
  "phases": [
    {
      "label": "...",
      "description": "...",
      "dominant_domain": "work | relationships | self",
      "pattern_expression": "...",
      "is_current": true | false,
      "confidence": "high | medium | low"
    }
  ]
}

==================================================
CORE PRINCIPLES
==================================================

1. PHASES ARE NOT EVENTS
Do NOT list jobs, years, milestones, or life events. A phase is:
  - a way the user was operating
  - a pattern expressing itself over time

2. 3–5 PHASES MAX
Create:
  - 2–3 past phases
  - 1 current phase (REQUIRED — exactly one phase with is_current=true)
  - optional: 1 emerging/next phase (only if clear)

3. EACH PHASE MUST FEEL DISTINCT
Each phase must show:
  - how the pattern behaved differently
  - how the consequence evolved
Bad: repeating the same pattern wording.
Good: progression — expansion → pressure → isolation → awareness.

4. USE DOMAIN WEIGHTING
Each phase must have a dominant_domain. Do NOT assign domains evenly.
Early phases often dominated by one domain; later phases may shift domains.

5. SHOW MOVEMENT
Every phase must imply change. Use language like:
  - "at first…"
  - "this begins as…"
  - "this shifts into…"
  - "over time…"

6. CURRENT PHASE MUST FEEL ACTIVE
The current phase must:
  - connect to the role_card
  - reflect pattern recurrence (if present)
  - reflect today's intensity if medium/high
It should feel like: "This is where you are now."

7. PATTERN EVOLUTION (CRITICAL)
You are NOT describing different patterns.
You are describing the SAME pattern evolving over time.

8. NO SYSTEM LANGUAGE
Do NOT mention: lifeline, pattern memory, domains, scores, weights,
astrology, human design, bazi, purple star, frameworks, or any system.
Do NOT say "primary", "secondary", "background", or "dominant_domain"
in any user-facing field (label / description / pattern_expression).

9. KEEP IT TIGHT
  - label: 3–6 words (NOT 1-2 words — avoid ultra-short labels like "Refinement"; use evocative 3-6 word phrases like "Precision Becomes Pressure" or "Seeing the Loop")
  - description: 1–2 sentences max
  - pattern_expression: 1 sentence

==================================================
STYLE GUIDE
==================================================

Tone:
  - grounded, observational, slightly revealing
  - NOT mystical, NOT analytical

Avoid:
  - "you may find"
  - "this suggests"
  - "in many ways"
  - "dynamic blend"
  - "invites growth"
  - any generic fluff

==================================================
FINAL CHECK (apply silently before returning)
==================================================

- Phases feel sequential and progressive
- Each phase has a distinct dominant domain where possible (later phases may
  shift domains to show evolution)
- Exactly one phase has is_current=true
- Current phase clearly stands out
- Pattern evolves, not repeats
- No system/framework language
- Return ONLY the JSON object — no prose before or after
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_DOMAINS = {"work", "relationships", "self"}
_VALID_CONFIDENCE = {"high", "medium", "low"}
_MIN_PHASES = 3
_MAX_PHASES = 5

# System-language scrubber. These words should NEVER appear in user-facing copy.
_SYSTEM_LANGUAGE_RE = re.compile(
    r"\b(lifeline|pattern memory|pattern-memory|human design|bazi|ba-zi|"
    r"purple star|ziwei|astrology|horoscope|natal chart|transit|retrograde|"
    r"primary domain|secondary domain|background domain|domain weight|"
    r"scoring|weighting|confidence score|"
    r"role card|role-card|role_card|"
    r"framework|mirror)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def generate_phases(
    *,
    role_card: Optional[Dict[str, Any]] = None,
    domain_weights: Optional[Dict[str, Any]] = None,
    pattern_memory: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    today_state: Optional[Dict[str, Any]] = None,
    llm_chat_factory=None,
) -> Dict[str, Any]:
    """
    One LLM call → 3-5 phases. Falls back to deterministic skeleton when LLM
    is unavailable or returns unusable output.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local import

    user_msg = _build_user_message(
        role_card=role_card,
        domain_weights=domain_weights,
        pattern_memory=pattern_memory,
        lifeline_summary=lifeline_summary,
        today_state=today_state,
    )

    llm_used = False
    render_error: Optional[str] = None
    scrubbed_hits: List[str] = []
    llm_raw: Optional[str] = None

    parsed: Optional[Dict[str, Any]] = None

    if llm_chat_factory is not None:
        try:
            chat: LlmChat = llm_chat_factory()
            resp = await chat.send_message(UserMessage(text=user_msg))
            llm_raw = resp if isinstance(resp, str) else str(resp)
            llm_used = True
        except Exception as e:
            logger.exception("[PhaseEngine] LLM call failed")
            render_error = f"llm_error: {e}"

    if llm_raw:
        parsed, parse_err = _parse_and_validate(llm_raw)
        if parse_err:
            render_error = render_error or parse_err

    if not parsed:
        # Deterministic skeleton fallback
        parsed = _deterministic_skeleton(
            role_card=role_card,
            domain_weights=domain_weights,
            pattern_memory=pattern_memory,
            lifeline_summary=lifeline_summary,
            today_state=today_state,
        )
        render_error = render_error or "fallback_skeleton"

    # Invariants
    phases = parsed.get("phases") or []
    phases = _enforce_phase_invariants(phases)

    # Scrub system language from each user-facing field
    for ph in phases:
        for field in ("label", "description", "pattern_expression"):
            v = ph.get(field)
            if isinstance(v, str) and v:
                cleaned, hits = _scrub_system_language(v)
                if hits:
                    scrubbed_hits.extend(hits)
                ph[field] = cleaned

    # Phase 3.4 — deterministic gap detection (no LLM)
    phase_gap = detect_phase_gap(
        phases=phases,
        lifeline_summary=lifeline_summary,
        pattern_memory=pattern_memory,
    )

    return {
        "phases":       phases,
        "phase_gap":    phase_gap,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "phase_engine_v1",
        "debug": {
            "llm_used":            llm_used,
            "render_error":        render_error,
            "scrubbed_hits":       scrubbed_hits,
            "input_snapshot": {
                "has_role_card":         bool(role_card),
                "domain_weights":        (domain_weights or {}).get("dominant_domain") if domain_weights else None,
                "pattern_memory_state":  (pattern_memory or {}).get("memory_state") if pattern_memory else None,
                "match_count":           (pattern_memory or {}).get("match_count") if pattern_memory else 0,
                "lifeline_total_events": (lifeline_summary or {}).get("total_events") if lifeline_summary else 0,
                "today_intensity":       (today_state or {}).get("intensity_level"),
            },
        },
    }


# ---------------------------------------------------------------------------
# User-message builder
# ---------------------------------------------------------------------------

def _build_user_message(
    *,
    role_card: Optional[Dict[str, Any]],
    domain_weights: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
) -> str:
    rc: Dict[str, Any] = {}
    if isinstance(role_card, dict):
        for k in ("role", "tension", "distortion", "orientation"):
            v = role_card.get(k) or role_card.get(f"{k}_seed")
            if v:
                rc[k] = v

    dw: Dict[str, Any] = {}
    if isinstance(domain_weights, dict):
        for k in ("work", "relationships", "self", "dominant_domain", "confidence"):
            if domain_weights.get(k) is not None:
                dw[k] = domain_weights[k]

    pm: Dict[str, Any] = {}
    if isinstance(pattern_memory, dict):
        pm = {
            "dominant_tension": pattern_memory.get("dominant_tension"),
            "memory_state":     pattern_memory.get("memory_state"),
            "match_count":      pattern_memory.get("match_count") or 0,
            "recent_tensions":  [
                rt.get("tension") for rt in (pattern_memory.get("recent_tensions") or [])[:5]
                if isinstance(rt, dict) and rt.get("tension")
            ],
        }

    ll: Dict[str, Any] = {}
    if isinstance(lifeline_summary, dict):
        ll = {
            "total_events":           lifeline_summary.get("total_events") or 0,
            "domain_distribution":    lifeline_summary.get("domain_event_counts") or {},
            "tone_distribution":      lifeline_summary.get("domain_tone_mix") or {},
            "recurring_categories":   lifeline_summary.get("recurring_categories") or [],
            "high_impact_titles":     lifeline_summary.get("high_impact_titles") or [],
        }

    ts: Dict[str, Any] = {
        "intensity_level": (today_state or {}).get("intensity_level") or "low",
    }

    payload = {
        "role_card":        rc,
        "domain_weights":   dw,
        "pattern_memory":   pm,
        "lifeline_summary": ll,
        "today_state":      ts,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Parsing + validation
# ---------------------------------------------------------------------------

def _parse_and_validate(raw: str) -> (Optional[Dict[str, Any]], Optional[str]):
    if not raw:
        return None, "empty_llm_output"
    # Strip code fences if any
    s = raw.strip()
    if s.startswith("```"):
        # drop leading fence line and trailing fence
        s = re.sub(r"^```[a-zA-Z0-9]*\s*\n", "", s)
        s = re.sub(r"\n```\s*$", "", s)
    # Pluck the first {...} object
    first_brace = s.find("{")
    last_brace = s.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        return None, "no_json_object_found"
    chunk = s[first_brace:last_brace + 1]
    try:
        parsed = json.loads(chunk)
    except Exception as e:
        return None, f"json_decode_error: {e}"
    if not isinstance(parsed, dict):
        return None, "json_not_object"
    if "phases" not in parsed or not isinstance(parsed["phases"], list):
        return None, "missing_phases_array"
    return parsed, None


def _enforce_phase_invariants(phases: List[Any]) -> List[Dict[str, Any]]:
    """
    - Filter out malformed phases
    - Clamp count to [3, 5]
    - Ensure exactly one is_current=true (force last phase if needed)
    - Normalise field types
    """
    cleaned: List[Dict[str, Any]] = []
    for ph in phases:
        if not isinstance(ph, dict):
            continue
        label = _safe_str(ph.get("label"))
        description = _safe_str(ph.get("description"))
        pattern_expr = _safe_str(ph.get("pattern_expression"))
        if not (label and description and pattern_expr):
            continue
        domain = (ph.get("dominant_domain") or "").strip().lower()
        if domain not in _VALID_DOMAINS:
            domain = "self"
        confidence = (ph.get("confidence") or "").strip().lower()
        if confidence not in _VALID_CONFIDENCE:
            confidence = "medium"
        is_current = bool(ph.get("is_current", False))
        cleaned.append({
            "label":             label[:80],
            "description":       description[:400],
            "dominant_domain":   domain,
            "pattern_expression": pattern_expr[:220],
            "is_current":        is_current,
            "confidence":        confidence,
        })

    # Clamp to max
    if len(cleaned) > _MAX_PHASES:
        cleaned = cleaned[:_MAX_PHASES]

    # Pad if under min (shouldn't happen after LLM parse; kept for safety)
    while len(cleaned) < _MIN_PHASES:
        cleaned.append({
            "label":              "Current Phase",
            "description":        "You are in a phase that hasn't yet compressed into a single shape.",
            "dominant_domain":    "self",
            "pattern_expression": "The pattern is still forming into something nameable.",
            "is_current":         False,
            "confidence":         "low",
        })

    # Enforce exactly one is_current=true
    current_idxs = [i for i, p in enumerate(cleaned) if p.get("is_current")]
    if not current_idxs:
        cleaned[-1]["is_current"] = True
    elif len(current_idxs) > 1:
        # keep only the LAST one marked current (most likely intended)
        keep = current_idxs[-1]
        for i in current_idxs:
            cleaned[i]["is_current"] = (i == keep)

    return cleaned


def _safe_str(v: Any) -> str:
    if not isinstance(v, str):
        return ""
    return v.strip()


# ---------------------------------------------------------------------------
# System-language scrubber
# ---------------------------------------------------------------------------

def _scrub_system_language(text: str) -> (str, List[str]):
    """Remove any banned system/framework vocabulary and return (cleaned, hits)."""
    hits: List[str] = []
    def _record(m: re.Match) -> str:
        hits.append(m.group(0))
        return ""
    cleaned = _SYSTEM_LANGUAGE_RE.sub(_record, text)
    # Collapse whitespace and fix orphan punctuation caused by removal
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = cleaned.strip()
    return cleaned, hits


# ---------------------------------------------------------------------------
# Deterministic skeleton (no LLM)

# ---------------------------------------------------------------------------
# Phase gap detection (deterministic — no LLM)
# ---------------------------------------------------------------------------

_TRANSITION_KEYWORDS: List[str] = [
    "then", "shift", "became", "turned", "over time", "began",
    "at first", "later", "now", "eventually", "started",
]


def detect_phase_gap(
    phases: List[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Deterministic detection of missing timeline context.

    Returns:
      {
        "show":       bool,
        "reasons":    ["low_confidence"|"weak_transition"|"sparse_lifeline"|"weak_memory", ...],
        "confidence": "low" | "medium",
        "dominant_domain": "work|relationships|self"|None
          — the dominant domain of the current phase, so the CTA can pre-fill
            a suggested_category on the add-event flow.
      }
    """
    reasons: List[str] = []

    if not isinstance(phases, list) or not phases:
        return {"show": False, "reasons": [], "confidence": "low", "dominant_domain": None}

    # A) Any low-confidence phase → nudge
    if any((p or {}).get("confidence") == "low" for p in phases):
        reasons.append("low_confidence")

    # B) Weak transitions between adjacent phases
    def _weak_transition(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        combined = ((a.get("description") or "") + " " + (b.get("description") or "")).lower()
        return not any(k in combined for k in _TRANSITION_KEYWORDS)

    weak_pairs = [
        (i, i + 1)
        for i in range(len(phases) - 1)
        if _weak_transition(phases[i], phases[i + 1])
    ]
    if weak_pairs:
        reasons.append("weak_transition")

    # C) Sparse lifeline in dominant domain(s)
    domain_counts = (lifeline_summary or {}).get("domain_event_counts") or {}
    # Accept either domain_counts (spec) or domain_event_counts (our schema)
    if not domain_counts:
        domain_counts = (lifeline_summary or {}).get("domain_counts") or {}
    doms = [(p or {}).get("dominant_domain") for p in phases if (p or {}).get("dominant_domain")]
    sparse = any(int(domain_counts.get(d, 0) or 0) < 3 for d in doms)
    if sparse:
        reasons.append("sparse_lifeline")

    # D) Weak pattern memory
    mem_state = (pattern_memory or {}).get("memory_state") or ""
    if mem_state in ("new", "new_pattern", "returning", "known_pattern"):
        # "known_pattern" = a first repeat but not yet strongly cycling
        reasons.append("weak_memory")

    show = bool(reasons)
    confidence = "medium" if len(reasons) >= 2 else "low"

    # Dominant domain = current phase's domain (for prefill)
    current_dom: Optional[str] = None
    for p in phases:
        if (p or {}).get("is_current"):
            current_dom = (p or {}).get("dominant_domain") or current_dom
            break
    if not current_dom and phases:
        current_dom = (phases[-1] or {}).get("dominant_domain")

    return {
        "show":            show,
        "reasons":         reasons,
        "confidence":      confidence,
        "dominant_domain": current_dom,
    }



# ---------------------------------------------------------------------------

def _deterministic_skeleton(
    *,
    role_card: Optional[Dict[str, Any]],
    domain_weights: Optional[Dict[str, Any]],
    pattern_memory: Optional[Dict[str, Any]],
    lifeline_summary: Optional[Dict[str, Any]],
    today_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Skeleton used when the LLM is unavailable or fails. Produces 4 phases
    derived from the core signals. Intentionally plain; we still scrub and
    enforce invariants afterward.
    """
    dominant = (domain_weights or {}).get("dominant_domain")
    pm_state = (pattern_memory or {}).get("memory_state")
    match_count = (pattern_memory or {}).get("match_count") or 0
    total_events = (lifeline_summary or {}).get("total_events") or 0
    intensity = (today_state or {}).get("intensity_level") or "low"

    # Pick a 4-phase arc that reflects the user's data volume.
    early_domain = "work" if dominant == "work" else ("relationships" if dominant == "relationships" else "self")

    phases: List[Dict[str, Any]] = [
        {
            "label":              "Moving First",
            "description":        "At first, you led with action — moving before others had named what they wanted. This opened ground quickly.",
            "dominant_domain":    early_domain,
            "pattern_expression": "You start before the room catches up.",
            "is_current":         False,
            "confidence":         "medium",
        },
        {
            "label":              "Precision Tightens",
            "description":        "Over time your standards sharpened. What started as care began to outpace the people you were moving with.",
            "dominant_domain":    "work" if early_domain != "work" else "relationships",
            "pattern_expression": "You refine beyond what others can follow.",
            "is_current":         False,
            "confidence":         "medium",
        },
    ]

    # Optional third past phase only if the user has real history
    if total_events >= 10 or match_count >= 3:
        phases.append({
            "label":              "Carrying It Alone",
            "description":        "This shifts into carrying more by yourself as others disengage. Connection weakens under the weight of execution.",
            "dominant_domain":    "relationships" if early_domain != "relationships" else "self",
            "pattern_expression": "You continue alone and the loop tightens.",
            "is_current":         False,
            "confidence":         "medium",
        })

    # Current phase — depends on pattern_memory + intensity
    if pm_state == "recurring_pattern" and match_count >= 3:
        current_label = "Seeing the Loop"
        current_desc = (
            "You are beginning to notice the loop itself, especially as it "
            "becomes more active. This creates a chance to shift how you move."
        )
        current_expr = "You can now see what you are doing as it happens."
        current_domain = "self"
        current_conf = "high"
    elif pm_state == "recurring_pattern":
        current_label = "The Pattern Returns"
        current_desc = "The same shape is returning, softer than before but still recognisable. You catch it earlier each time."
        current_expr = "You notice the pattern before it finishes."
        current_domain = "self"
        current_conf = "medium"
    elif intensity == "high":
        current_label = "Active Pressure"
        current_desc = "The pattern is alive right now. It is shaping how you move through the day more than you might realise."
        current_expr = "The pattern is acting quickly today."
        current_domain = dominant if dominant in _VALID_DOMAINS else "self"
        current_conf = "medium"
    else:
        current_label = "Where You Are Now"
        current_desc = "You are in a quieter stretch where the pattern is present but not driving. Space is opening to see it clearly."
        current_expr = "The pattern is here but not leading."
        current_domain = "self"
        current_conf = "low" if total_events < 3 else "medium"

    phases.append({
        "label":              current_label,
        "description":        current_desc,
        "dominant_domain":    current_domain,
        "pattern_expression": current_expr,
        "is_current":         True,
        "confidence":         current_conf,
    })

    return {"phases": phases}
