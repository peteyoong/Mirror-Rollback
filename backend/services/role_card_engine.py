"""
Role Card Engine (Phase 1a)
===========================

Produces the top anchor "The Role You're In" card that sits above the Life
sub-tabs. Structured fields only — no paragraph blob.

CONTRACT:
    {
        "role":           str,            # "You're in a phase where you build and hand off"
        "tension":        str,            # "What you start has a way of becoming what you carry"
        "distortion":     str,            # "You can mistake responsibility for purpose"
        "orientation":    str,            # "This phase works when you initiate, then let it run without you"
        "confidence":     "high|medium|low",
        "dominant_drivers": [str, ...],   # compressed cues, never framework names
        "purple_star_input": None,        # first-class hook for P-later
        "generated_at":   iso,
        "generator_version": "role_card_v1a",
    }

INPUT PRIORITY (per user brief):
  1. Purple Star / role logic — NOT WIRED YET (stub hook).
  2. BaZi structural pattern   — day master element × strength × dominant element(s)
  3. HD operating style        — type + authority + definition
  4. Pattern Memory            — memory_state / evolution
  5. Current transit phase     — optional, degrades gracefully

This file is deterministic + ONE LLM polish call at the end (shared budget
with the per-domain calls). If LLM is unavailable it falls back to the
deterministic seeds.
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
# Role matrix: BaZi element × HD type → role phrase + tension + distortion + orientation
# ---------------------------------------------------------------------------

_ELEMENT_ROLE_BASE: Dict[str, Dict[str, str]] = {
    "wood": {
        "role":        "You're in a phase where you're meant to start things",
        "tension":     "You keep pushing growth after the thing is already grown",
        "distortion":  "You confuse expansion with progress",
        "orientation": "This phase works when you prune as often as you plant",
    },
    "fire": {
        "role":        "You're in a phase where you're meant to warm the room and set the pace",
        "tension":     "Your energy becomes the weather — and you forget you can set it down",
        "distortion":  "You perform vitality to cover ambient flatness",
        "orientation": "This phase works when the fire gets to rest without being called weakness",
    },
    "earth": {
        "role":        "You're in a phase where you're meant to build systems — but not carry them",
        "tension":     "What starts as momentum becomes weight when you stay too long",
        "distortion":  "You mistake being relied on for being meaningful",
        "orientation": "This phase works when you initiate, structure, and let the system take over",
    },
    "metal": {
        "role":        "You're in a phase where you're meant to refine and raise the standard",
        "tension":     "You sharpen past the point where anyone can use it",
        "distortion":  "You cut for precision and wound the trust in the room",
        "orientation": "This phase works when one rough edge gets to stay",
    },
    "water": {
        "role":        "You're in a phase where you're meant to sense the undercurrent before it surfaces",
        "tension":     "You absorb the tone of the room and lose your own line",
        "distortion":  "You go quiet just when the clear word would have landed",
        "orientation": "This phase works when you name the thing you already felt",
    },
}

# HD type modulates the role base — changes HOW the role operates
_HD_TYPE_MODULATION: Dict[str, str] = {
    "manifestor":              "— and the move is yours to make without waiting for permission",
    "manifesting generator":   "— and the move is to finish one thread before starting the next",
    "generator":               "— and the move is to respond to what actually lights up",
    "projector":               "— and the move is to wait for the invitation, then speak precisely",
    "reflector":               "— and the move is to let a full cycle pass before committing",
}

_AUTHORITY_NOTE: Dict[str, str] = {
    "emotional":  "Decisions land clean after the wave, not at its peak.",
    "sacral":     "The body's yes is what you're listening for.",
    "splenic":    "The first quiet signal is usually the right one.",
    "ego":        "What your willpower can sustain is the real measure.",
    "self-projected": "You know it when you hear yourself say it out loud.",
    "lunar":      "Clarity comes on a longer arc than most people allow.",
}

_PATTERN_MEMORY_NOTE: Dict[str, str] = {
    "recurring_pattern":  "The pattern is cycling, not resolving — that's the signal.",
    "new_pattern":        "The pattern is fresh. It hasn't yet calcified into a position.",
    "known_pattern":      "The pattern has shown itself before. It's familiar, not new.",
    "integrating":        "The pattern is softening through use.",
    "metabolizing":       "The pattern is being digested, not fought.",
}


def _lifeline_phase_note(lifeline_summary: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Phase 3 — translate aggregated lifeline activity into a phase note for
    the role card. Only fires when lived history actually shows clusters;
    stays silent for sparse timelines to avoid inventing a narrative.
    """
    if not isinstance(lifeline_summary, dict):
        return None
    total = lifeline_summary.get("total_events") or 0
    counts = lifeline_summary.get("domain_event_counts") or {}
    recurring = lifeline_summary.get("recurring_categories") or []

    if total < 5:
        return None

    # Which domain dominates the lived history?
    dominant = None
    if counts:
        dominant = max(counts, key=lambda k: counts.get(k, 0) or 0)
        if (counts.get(dominant) or 0) < 3:
            dominant = None

    parts: List[str] = []
    if dominant == "work":
        parts.append("this phase has been carried mostly by what you build and where you earn")
    elif dominant == "relationships":
        parts.append("this phase has been shaped by the relational ground you've been standing on")
    elif dominant == "self":
        parts.append("this phase has been marked by internal shifts, not external ones")

    if any(c in {"move", "loss", "identity"} for c in recurring):
        parts.append("the lived markers include disruption and identity shifts")
    elif "career" in recurring or "achievement" in recurring:
        parts.append("the lived markers cluster around work thresholds")

    if not parts:
        return None
    # Keep it one sentence, no prescription.
    note = "; ".join(parts) + "."
    return note[0].upper() + note[1:]


# ---------------------------------------------------------------------------
# Deterministic seed extraction
# ---------------------------------------------------------------------------

def _build_role_seeds(
    chart: Dict[str, Any],
    pattern_memory: Optional[Dict[str, Any]] = None,
    purple_star_input: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    bazi = chart.get("bazi") or {}
    dm = bazi.get("day_master") or {}
    element = (dm.get("element") or "").strip().lower()
    strength = (dm.get("strength") or "").strip().lower()

    hd = chart.get("human_design") or {}
    hd_type = (hd.get("type") or "").strip().lower()
    authority = (hd.get("authority") or "").strip().lower()

    pm = pattern_memory or {}
    memory_state = (pm.get("memory_state") or pm.get("state") or "").strip().lower()
    dominant_tension = pm.get("dominant_tension")
    match_count = pm.get("match_count") or 0

    # 1. Base role from element
    base = _ELEMENT_ROLE_BASE.get(element, {
        "role":        "You're in a phase that doesn't compress into a single posture",
        "tension":     "You tighten around the parts that already know what to do",
        "distortion":  "You repeat the same move while expecting a different result",
        "orientation": "This phase works when you return to why the posture exists",
    })

    # 2. HD modulation
    role_suffix = _HD_TYPE_MODULATION.get(hd_type, "")
    role_full = base["role"] + " " + role_suffix if role_suffix else base["role"]

    # 3. Authority note — appended to orientation, not merged
    authority_note = _AUTHORITY_NOTE.get(authority)

    # 4. Pattern-memory note
    memory_note = _PATTERN_MEMORY_NOTE.get(memory_state)

    # 5. Phase-3 lifeline phase note (only when lived history is rich enough)
    lifeline_note = _lifeline_phase_note(lifeline_summary)

    # Drivers: compressed cues, no framework names
    drivers: List[str] = []
    if element:
        drivers.append(f"{element} posture" + (f" · {strength}" if strength else ""))
    if hd_type:
        drivers.append(f"{hd_type} operating style")
    if authority:
        drivers.append(f"{authority} decision signal")
    if memory_state:
        drivers.append(f"memory: {memory_state.replace('_', ' ')}")
    if dominant_tension and match_count >= 2:
        drivers.append(f"recurring tension ({match_count}×)")
    if lifeline_summary and (lifeline_summary.get("total_events") or 0) >= 5:
        drivers.append(f"lived history: {lifeline_summary.get('total_events')} events")
    if purple_star_input:
        drivers.append("purple star phase (supplied)")

    # Confidence
    signal_count = sum(1 for x in (element, hd_type, authority, memory_state) if x)
    if lifeline_note:
        signal_count += 1
    confidence = "high" if signal_count >= 3 else "medium" if signal_count == 2 else "low"

    orientation_seed = base["orientation"]
    if authority_note:
        orientation_seed += f" {authority_note}"
    if memory_note:
        orientation_seed += f" {memory_note}"
    if lifeline_note:
        orientation_seed += f" {lifeline_note}"

    # Tension seed — sharpened by recurrence when we have it
    tension_seed = base["tension"]
    if dominant_tension and match_count >= 3:
        tension_seed += " — and it has re-formed in this shape more than once"

    return {
        "role_seed":          role_full,
        "tension_seed":       tension_seed,
        "distortion_seed":    base["distortion"],
        "orientation_seed":   orientation_seed,
        "dominant_drivers":   drivers[:6],
        "confidence":         confidence,
        "hd_type":            hd_type or None,
        "authority":          authority or None,
        "day_master_element": element or None,
        "day_master_strength": strength or None,
        "memory_state":       memory_state or None,
        "dominant_tension":   dominant_tension,
        "match_count":        int(match_count) if isinstance(match_count, (int, float)) else 0,
        "lifeline_phase_note": lifeline_note,
        "purple_star_input":  purple_star_input,  # carried through untouched
    }


# ---------------------------------------------------------------------------
# LLM polish
# ---------------------------------------------------------------------------

_ROLE_SYSTEM_PROMPT = """You are the Mirror Life Synthesis Engine — Role Card Renderer.

Your job is NOT to describe the user. Your job is to:
- detect the living pattern of the current PHASE they are in
- show where it turns
- show what it becomes over time
- make the cost visible
- and orient them back to alignment

==================================================
OUTPUT STRUCTURE
==================================================

Return ONLY valid JSON with:

{
  "role": "...",
  "tension": "...",
  "distortion": "...",
  "orientation": "...",
  "not_for": "..."
}

No extra keys. No markdown. No explanation.

==================================================
CORE WRITING RULES
==================================================

1. BEHAVIOR FIRST. Write what the user DOES, not what they ARE.
   Bad:  "You are decisive and sharp"
   Good: "You move first, then refine what you moved"

2. TEMPORAL MOVEMENT. At least one of {role, tension, distortion} MUST include
   "at first... then...", "over time...", or "what starts as... becomes...".

3. DISTORTION MUST INCLUDE COST. Show what the user does, what it turns into,
   and what it costs them.
   Bad:  "You overextend yourself"
   Good: "You take on more than you intended, and over time what you started
          becomes something you feel responsible for finishing."

4. ASYMMETRY. Do NOT soften. Avoid "this can sometimes", "you may find".
   Prefer "this turns when", "this becomes heavy when".

5. NOT_FOR must be a sharp one-liner describing what this phase is NOT for.
   Example: "This is not a phase for carrying everything yourself."

6. ORIENTATION IS NOT ADVICE. Describe what the pattern needs to function
   correctly.
   Bad:  "You should step back"
   Good: "This pattern works when initiation is followed by space"

7. NO GENERIC LANGUAGE: "dynamic blend", "recurring theme", "invites growth",
   "multiple perspectives", "tends to", "you may find", "suggests that",
   "in many ways", "deeply connected to". If it sounds like a horoscope, it
   is wrong.

8. NO FRAMEWORK NAMES. Never mention chart, lens, system, astrology, human
   design, bazi, enneagram, numerology, manifestor, projector, generator,
   reflector, day master, authority, life path.

9. KEEP IT TIGHT. Each field 1-3 sentences. No fluff, no repetition.

==================================================
QUALITY CHECK BEFORE OUTPUT
==================================================

Before returning, ensure:
- Each field contains a clear behaviour
- At least one field contains time progression
- distortion shows a cost
- not_for is present and sharp
- Language is specific, not general

If not, rewrite internally.

==================================================
FINAL RULE
==================================================

It should feel like: "This is exactly what I do... and I can see where it turns."
"""


def _build_role_user_message(seeds: Dict[str, Any]) -> str:
    payload = {
        "role_card_seeds": {
            "role":               seeds["role_seed"],
            "tension":            seeds["tension_seed"],
            "distortion":         seeds["distortion_seed"],
            "orientation":        seeds["orientation_seed"],
            "dominant_drivers":   seeds["dominant_drivers"],
        },
        "confidence":        seeds["confidence"],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _parse_role_json(raw: str) -> Tuple[Optional[Dict[str, str]], List[str]]:
    all_hits: List[str] = []
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, ["no_json_detected"]
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, ["json_parse_error"]
    for k in ("role", "tension", "distortion", "orientation", "not_for"):
        v = payload.get(k)
        if isinstance(v, str):
            cleaned, hits = scrub_banned_phrases(v)
            payload[k] = cleaned.strip()
            all_hits.extend(hits)
    return payload, all_hits


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_role_card(
    *,
    chart: Dict[str, Any],
    pattern_memory: Optional[Dict[str, Any]] = None,
    purple_star_input: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    llm_chat_factory=None,
) -> Dict[str, Any]:
    """
    End-to-end role card. ONE LLM call. Falls back to deterministic seeds on
    any failure.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local import

    seeds = _build_role_seeds(chart, pattern_memory, purple_star_input, lifeline_summary)
    user_msg = _build_role_user_message(seeds)

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
            logger.exception("[RoleCard] LLM render failed")
            render_error = f"llm_render_error: {e}"

    payload: Optional[Dict[str, str]] = None
    if llm_output:
        payload, banned_hits = _parse_role_json(llm_output)

    if not payload or not payload.get("role"):
        payload = {
            "role":        seeds["role_seed"].rstrip(".") + ".",
            "tension":     seeds["tension_seed"].rstrip(".") + ".",
            "distortion":  seeds["distortion_seed"].rstrip(".") + ".",
            "orientation": seeds["orientation_seed"].rstrip(".") + ".",
            "not_for":     "This is not a phase for proving the pattern, only living it.",
        }

    return {
        "role":             payload.get("role", ""),
        "tension":          payload.get("tension", ""),
        "distortion":       payload.get("distortion", ""),
        "orientation":      payload.get("orientation", ""),
        "not_for":          payload.get("not_for", ""),
        "confidence":       seeds["confidence"],
        "dominant_drivers": seeds["dominant_drivers"],
        "purple_star_input": seeds["purple_star_input"],
        "debug": {
            "llm_used":            llm_output is not None,
            "render_error":        render_error,
            "banned_phrase_hits":  banned_hits,
            "seed_hd_type":        seeds["hd_type"],
            "seed_authority":      seeds["authority"],
            "seed_element":        seeds["day_master_element"],
            "seed_memory_state":   seeds["memory_state"],
        },
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "generator_version": "role_card_v1a2",
    }


def build_role_seeds_public(
    chart: Dict[str, Any],
    pattern_memory: Optional[Dict[str, Any]] = None,
    purple_star_input: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Public accessor for deterministic role seeds (used when we want the
    synthesis engine to render role + domain in a single LLM call).
    """
    return _build_role_seeds(chart, pattern_memory, purple_star_input, lifeline_summary)
