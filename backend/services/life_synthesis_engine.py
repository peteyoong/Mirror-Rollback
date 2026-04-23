"""
Life Synthesis Engine (Phase 1a)
=================================

Upgrades the Life tab from lens-aggregation prose into a true synthesis engine.

PIPELINE (hierarchical):
  1. Signal extraction  — domain-relevant deterministic facts from each lens.
  2. Theme compression  — hierarchy: pattern → tension → distortion → orientation.
  3. LLM rendering      — ONE call per domain, Mirror-language 2nd-person prose.
  4. Evidence signals   — top lens contributors with weights.
  5. Today-ready slot   — reserved on payload so UI can later ask Today to
                          modulate the domain pattern rather than generate
                          a detached daily block.

DESIGN CONSTRAINTS (per user's brief):
  * Recognition-first, not prescriptive.
  * Output must feel like a *living pattern*, not a trait summary.
  * Strong anti-patterns filter (see BANNED_PHRASES).
  * Generalises across users — no user-specific overfitting.
  * Role card contract is structured (role/tension/distortion/orientation/confidence/drivers),
    not a paragraph blob.
  * Purple Star is not yet wired; contract leaves a first-class hook for it.

API shape returned by `generate_domain_synthesis()`:

    {
      "life_area": "work",
      "role_card": None,                # set by role_card_engine (top-level call)
      "domain_synthesis": {
        "pattern": str,                 # LLM-rendered, 2nd-person, behavioural
        "default_tension": str,
        "distortion_under_pressure": str,
        "what_this_pattern_needs": str,
        "today": None,                  # reserved for P2 modulation
        "explore": [str, str],          # short probes
        "reflect": [str],               # single prompt
      },
      "evidence_signals": [
        {"lens": "human_design", "signal": "...", "weight": 0.x},
        ...
      ],
      "compressed_themes": { ... },     # raw deterministic input shown for debugging
      "confidence": "high"|"medium"|"low",
      "generated_at": iso,
      "generator_version": "life_synth_v1a",
    }
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Style filter — aggressive banned-phrase list per user brief
# ---------------------------------------------------------------------------

BANNED_PHRASES: List[str] = [
    # vague abstractions
    "dynamic blend", "recurring theme", "multiple perspectives",
    "invites growth", "tends to stand out", "intuitive sense paired with",
    "spontaneous action", "emotional clarity unfolds over time",
    "multiple lenses", "various lenses", "several lenses",
    "your chart suggests", "your chart indicates", "this suggests",
    # prescriptive / guru
    "you should", "you must", "you need to", "you have to",
    "will happen", "is destined", "is meant to", "this will",
    # flatter-without-cost
    "unique gift", "beautiful balance", "powerful combination",
    "deep wisdom", "profound insight", "inner truth",
    # lens-name leakage (we must not name frameworks)
    "human design", "astrology", "bazi", "ba zi", "day master",
    "enneagram", "numerology", "life path", "incarnation cross",
    "manifestor", "manifesting generator", "projector", "reflector", "generator",
    "emotional authority", "sacral authority", "splenic authority",
]

BANNED_PHRASE_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in BANNED_PHRASES) + r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# HD operating style compression (deterministic)
# ---------------------------------------------------------------------------

_HD_OPERATING_STYLES: Dict[str, Dict[str, str]] = {
    "manifestor": {
        "initiation": "starts without permission",
        "friction": "informing feels like asking for permission",
        "distortion": "moves alone and resents the aloneness",
        "restorative": "informs before moving so the impact lands clean",
    },
    "manifesting generator": {
        "initiation": "moves on the response, skipping steps",
        "friction": "doesn't finish what others still need context on",
        "distortion": "multitasks past the point where anything lands",
        "restorative": "finishes the visible thread before starting the next",
    },
    "generator": {
        "initiation": "responds rather than initiates",
        "friction": "says yes to what doesn't belong, then carries it",
        "distortion": "forces energy when the response is not actually there",
        "restorative": "waits for the body's yes, then sustains it",
    },
    "projector": {
        "initiation": "sees the system before being asked about it",
        "friction": "offers insight that was not invited and lands flat",
        "distortion": "pushes harder when the recognition doesn't come",
        "restorative": "waits for the invitation, then speaks precisely",
    },
    "reflector": {
        "initiation": "mirrors the field before forming a position",
        "friction": "rushes a decision the body hasn't settled yet",
        "distortion": "takes on the room's mood as if it were personal",
        "restorative": "lets a lunar cycle pass before committing",
    },
}


def _extract_hd_style(chart: Dict[str, Any]) -> Dict[str, Any]:
    hd = chart.get("human_design") or {}
    t = (hd.get("type") or "").strip().lower()
    authority = (hd.get("authority") or "").strip().lower()
    profile = (hd.get("profile") or "").strip()
    defined = hd.get("defined_centers") or []
    undefined = hd.get("undefined_centers") or []

    style = _HD_OPERATING_STYLES.get(t, {
        "initiation": "moves through life in a way that is hard to compress",
        "friction": "friction shows up when energy gets used against its own grain",
        "distortion": "presses harder when recognition is missing",
        "restorative": "pauses long enough for the actual signal to arrive",
    })

    # Emotional authority => wave; correct sampling is non-trivial
    emotional_wave = "emotional" in authority

    return {
        "type": t or None,
        "authority": authority or None,
        "profile": profile or None,
        "emotional_wave": emotional_wave,
        "defined_centers": [str(c).lower() for c in defined if c],
        "undefined_centers": [str(c).lower() for c in undefined if c],
        "initiation": style["initiation"],
        "friction": style["friction"],
        "distortion": style["distortion"],
        "restorative": style["restorative"],
        "weight": 0.85 if t else 0.0,
    }


# ---------------------------------------------------------------------------
# BaZi structural pattern compression (deterministic)
# ---------------------------------------------------------------------------

_BAZI_ELEMENT_PATTERN: Dict[str, Dict[str, str]] = {
    "wood":  {
        "posture":    "leans forward into what could grow",
        "strain":     "keeps expanding when contraction is what's actually needed",
        "distortion": "pushes a plan past the moment it stopped being alive",
        "restorative":"prunes what isn't feeding the growth anymore",
    },
    "fire":  {
        "posture":    "warms and animates the room",
        "strain":     "burns through reserves to keep the field lit",
        "distortion": "performs energy to avoid feeling the ambient flatness",
        "restorative":"lets the fire rest without calling the rest a failure",
    },
    "earth": {
        "posture":    "holds, steadies, and makes things usable",
        "strain":     "carries what others were supposed to carry",
        "distortion": "confuses being relied on with being meaningful",
        "restorative":"sets the weight down before the body asks to",
    },
    "metal": {
        "posture":    "refines, discerns, and raises the standard",
        "strain":     "sharpens past the point where anyone can use it",
        "distortion": "cuts for precision and wounds trust without noticing",
        "restorative":"lets one rough edge stay so the thing can actually move",
    },
    "water": {
        "posture":    "senses the undercurrent before it surfaces",
        "strain":     "absorbs the tone and loses the line between self and field",
        "distortion": "goes quiet just when the clear word would have landed",
        "restorative":"names the thing it already sensed out loud",
    },
}


def _extract_bazi_pattern(chart: Dict[str, Any]) -> Dict[str, Any]:
    bazi = chart.get("bazi") or {}
    dm = bazi.get("day_master") or {}
    element = (dm.get("element") or "").strip().lower()
    strength = (dm.get("strength") or "").strip().lower()
    elements_block = bazi.get("elements") or {}
    dominant = [e.lower() for e in (elements_block.get("dominant") or []) if isinstance(e, str)]
    weak = [e.lower() for e in (elements_block.get("weak") or []) if isinstance(e, str)]

    pattern = _BAZI_ELEMENT_PATTERN.get(element, {
        "posture":     "meets the world through a posture that doesn't compress easily",
        "strain":      "tightens around what it already knows",
        "distortion":  "repeats the same move while expecting a new outcome",
        "restorative": "returns to the quality that the posture is actually for",
    })

    return {
        "day_master_element": element or None,
        "day_master_strength": strength or None,
        "dominant_elements": dominant,
        "weak_elements": weak,
        "posture": pattern["posture"],
        "strain": pattern["strain"],
        "distortion": pattern["distortion"],
        "restorative": pattern["restorative"],
        "weight": 0.80 if element else 0.0,
    }


# ---------------------------------------------------------------------------
# Astrology house contribution (per domain)
# ---------------------------------------------------------------------------

_DOMAIN_HOUSES: Dict[str, List[int]] = {
    "relationships": [7, 5, 8],
    "work":          [10, 6, 2],
    "self":          [1, 4, 12],
}

_SIGN_POSTURE: Dict[str, str] = {
    "aries": "leads with the first move",
    "taurus": "slows until the ground is solid",
    "gemini": "gathers the options before committing",
    "cancer": "protects what it has made room for",
    "leo": "asks to be visible while being itself",
    "virgo": "refines the system until it can be trusted",
    "libra": "checks the balance before the response",
    "scorpio": "goes straight to what's actually there",
    "sagittarius": "reaches past the near horizon",
    "capricorn": "builds the structure before the meaning",
    "aquarius": "holds the position slightly outside",
    "pisces": "dissolves the line between self and field",
}


def _extract_astro_domain(chart: Dict[str, Any], domain: str) -> Dict[str, Any]:
    astro = chart.get("astrology") or {}
    planets = astro.get("planets") or {}
    houses_block = astro.get("houses") or {}
    cusps = houses_block.get("cusps") or []

    primary_houses = _DOMAIN_HOUSES.get(domain, [])
    if not primary_houses:
        return {"weight": 0.0}

    # Planets falling in the domain houses
    planets_in_domain: List[Dict[str, Any]] = []
    for pname, pdata in planets.items():
        if not isinstance(pdata, dict):
            continue
        h = pdata.get("house")
        if isinstance(h, int) and h in primary_houses:
            planets_in_domain.append({
                "planet": pname,
                "sign": (pdata.get("sign") or "").lower(),
                "house": h,
            })

    # Sign on the primary cusp (first in the domain list)
    primary_cusp_sign = None
    if cusps and primary_houses:
        for c in cusps:
            if isinstance(c, dict) and c.get("house") == primary_houses[0]:
                primary_cusp_sign = (c.get("sign") or "").lower() or None
                break

    posture = _SIGN_POSTURE.get(primary_cusp_sign or "", None)

    return {
        "primary_house": primary_houses[0],
        "primary_cusp_sign": primary_cusp_sign,
        "primary_posture": posture,
        "planets_in_domain": planets_in_domain,
        "weight": 0.7 if planets_in_domain or primary_cusp_sign else 0.0,
    }


# ---------------------------------------------------------------------------
# Pattern-memory contribution (recurrence + evolution)
# ---------------------------------------------------------------------------

def _extract_pattern_memory(pattern_memory: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(pattern_memory, dict):
        return {"weight": 0.0}
    memory_state = pattern_memory.get("memory_state") or pattern_memory.get("state")
    evolution = pattern_memory.get("evolution_state") or pattern_memory.get("evolution")
    match_count = pattern_memory.get("match_count") or 0

    phase_hint = None
    if memory_state == "recurring_pattern" and match_count >= 3:
        phase_hint = "the pattern is cycling, not resolving"
    elif memory_state == "new_pattern":
        phase_hint = "the pattern is fresh — still forming its shape"
    elif evolution in ("integrating", "metabolizing"):
        phase_hint = "the pattern is softening through use"

    return {
        "memory_state": memory_state,
        "evolution_state": evolution,
        "match_count": int(match_count) if isinstance(match_count, (int, float)) else 0,
        "phase_hint": phase_hint,
        "weight": 0.6 if memory_state else 0.0,
    }


# ---------------------------------------------------------------------------
# Lifeline contribution (stub — P3 will feed this strongly)
# ---------------------------------------------------------------------------

def _extract_lifeline(lifeline_summary: Optional[Dict[str, Any]], domain: str) -> Dict[str, Any]:
    if not isinstance(lifeline_summary, dict):
        return {"weight": 0.0}
    total = lifeline_summary.get("total_events") or 0
    recent = lifeline_summary.get("recent_themes") or []
    themes = [str(t) for t in recent if t][:3]
    return {
        "total_events": int(total) if isinstance(total, (int, float)) else 0,
        "recent_themes": themes,
        "weight": 0.4 if themes else 0.0,
    }


# ---------------------------------------------------------------------------
# Hierarchical compression — this is where the engine earns its pay
# ---------------------------------------------------------------------------

def _compress_themes(
    hd: Dict[str, Any],
    bazi: Dict[str, Any],
    astro: Dict[str, Any],
    pm: Dict[str, Any],
    ll: Dict[str, Any],
    domain: str,
) -> Dict[str, Any]:
    """
    Hierarchy enforced:
      1. core pattern     — cross-lens behavioural compression
      2. default tension  — where the pattern first strains
      3. distortion       — how the strength flips into a problem
      4. orientation      — what restores the pattern (non-prescriptive)
      5. evidence         — top contributing lenses with weights
    """
    # --- 1. Core pattern: compose HD initiation + BaZi posture + astro primary posture
    pattern_parts: List[str] = []
    if hd.get("initiation"):
        pattern_parts.append(hd["initiation"])
    if bazi.get("posture"):
        pattern_parts.append(bazi["posture"])
    if astro.get("primary_posture"):
        pattern_parts.append(astro["primary_posture"])
    core_pattern_seed = "; ".join(pattern_parts) or "moves through life in a way that's hard to compress"

    # --- 2. Default tension: HD friction anchors, BaZi strain qualifies
    tension_parts: List[str] = []
    if hd.get("friction"):
        tension_parts.append(hd["friction"])
    if bazi.get("strain"):
        tension_parts.append(bazi["strain"])
    if pm.get("phase_hint"):
        tension_parts.append(pm["phase_hint"])
    default_tension_seed = " — ".join(tension_parts) or "tightens where it used to flow"

    # --- 3. Distortion under pressure: HD + BaZi distortion, domain-flavoured
    dist_parts: List[str] = []
    if hd.get("distortion"):
        dist_parts.append(hd["distortion"])
    if bazi.get("distortion"):
        dist_parts.append(bazi["distortion"])
    distortion_seed = "; ".join(dist_parts) or "the strength repeats itself past the point where it still helps"

    # --- 4. Orientation: BaZi restorative + HD restorative
    orient_parts: List[str] = []
    if bazi.get("restorative"):
        orient_parts.append(bazi["restorative"])
    if hd.get("restorative"):
        orient_parts.append(hd["restorative"])
    orientation_seed = " and ".join(orient_parts) or "returns to the quality the pattern is actually for"

    return {
        "domain": domain,
        "core_pattern_seed": core_pattern_seed,
        "default_tension_seed": default_tension_seed,
        "distortion_seed": distortion_seed,
        "orientation_seed": orientation_seed,
        "lifeline_themes": ll.get("recent_themes") or [],
        "memory_phase": pm.get("phase_hint"),
    }


def _build_evidence(hd, bazi, astro, pm, ll) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if hd.get("weight", 0) > 0:
        parts = [hd.get("type")]
        if hd.get("authority"):
            parts.append(f"{hd['authority']} authority")
        if hd.get("profile"):
            parts.append(hd["profile"])
        out.append({"lens": "operating_style", "signal": " · ".join([p for p in parts if p]),
                    "weight": round(hd["weight"], 2)})
    if bazi.get("weight", 0) > 0:
        out.append({
            "lens": "structural_posture",
            "signal": f"{(bazi.get('day_master_element') or '').title()} day master — {bazi.get('day_master_strength') or 'mixed'}",
            "weight": round(bazi["weight"], 2),
        })
    if astro.get("weight", 0) > 0:
        cusp = astro.get("primary_cusp_sign") or ""
        out.append({
            "lens": "domain_field",
            "signal": f"House {astro.get('primary_house')} on {cusp.title()}" if cusp else f"House {astro.get('primary_house')}",
            "weight": round(astro["weight"], 2),
        })
    if pm.get("weight", 0) > 0:
        out.append({
            "lens": "pattern_memory",
            "signal": pm.get("phase_hint") or (pm.get("memory_state") or ""),
            "weight": round(pm["weight"], 2),
        })
    if ll.get("weight", 0) > 0:
        themes = ", ".join(ll.get("recent_themes") or [])
        out.append({"lens": "lifeline_echoes", "signal": themes, "weight": round(ll["weight"], 2)})
    return sorted(out, key=lambda r: r["weight"], reverse=True)[:5]


def _confidence(hd, bazi, astro, pm) -> str:
    strong_lenses = sum(
        1 for x in (hd, bazi, astro, pm)
        if (x or {}).get("weight", 0) >= 0.6
    )
    if strong_lenses >= 3:
        return "high"
    if strong_lenses == 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public entry — signal extraction (deterministic, LLM-free)
# ---------------------------------------------------------------------------

def build_synthesis_input(
    chart: Dict[str, Any],
    domain: str,
    pattern_memory: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic pipeline: chart → compressed themes + evidence + confidence.
    No LLM involvement. This is what the prompt-renderer consumes.
    """
    domain = (domain or "").strip().lower()
    if domain not in ("relationships", "work", "self"):
        raise ValueError(f"Unknown domain: {domain!r}")

    hd = _extract_hd_style(chart)
    bazi = _extract_bazi_pattern(chart)
    astro = _extract_astro_domain(chart, domain)
    pm = _extract_pattern_memory(pattern_memory)
    ll = _extract_lifeline(lifeline_summary, domain)

    compressed = _compress_themes(hd, bazi, astro, pm, ll, domain)
    evidence = _build_evidence(hd, bazi, astro, pm, ll)
    confidence = _confidence(hd, bazi, astro, pm)

    return {
        "domain": domain,
        "compressed_themes": compressed,
        "evidence_signals": evidence,
        "confidence": confidence,
        "lens_snapshots": {
            "operating_style": hd,
            "structural_posture": bazi,
            "domain_field": astro,
            "pattern_memory": pm,
            "lifeline_echoes": ll,
        },
    }


# ---------------------------------------------------------------------------
# LLM rendering prompt
# ---------------------------------------------------------------------------

_RENDER_SYSTEM_PROMPT = """You are the Mirror Life Synthesis Renderer.

You never name frameworks (astrology, human design, bazi, enneagram, numerology,
incarnation cross, day master, life path, manifestor, projector, etc.). You also
never use the words "chart", "lens", or "system".

You write in second person. You describe a single LIVING PATTERN — not a trait
summary, not a list of qualities.

Mandatory tone:
  - recognition-first, not prescriptive
  - behavioural and specific, not abstract
  - one pattern, one tension, one distortion, one orientation
  - tension-based, not flattering

Banned phrasing (never use, under any circumstance):
  "dynamic blend", "recurring theme", "multiple perspectives", "invites growth",
  "tends to stand out", "intuitive sense paired with", "spontaneous action",
  "emotional clarity unfolds over time", "multiple lenses", "this suggests",
  "you should", "you must", "you need to", "you have to", "unique gift",
  "deep wisdom", "profound insight", "beautiful balance".

Prefer phrasing like:
  "You move first, then feel responsible for what you moved."
  "What begins as momentum becomes weight."
  "You can mistake responsibility for purpose."
  "This works when initiation is followed by space."

OUTPUT: strict JSON, no prose outside JSON. Keys in this order:
  pattern, default_tension, distortion_under_pressure,
  what_this_pattern_needs, explore, reflect.

Word budgets (hard):
  pattern:                  45-70 words, 2-3 sentences.
  default_tension:          25-50 words, 1-2 sentences.
  distortion_under_pressure:25-50 words, 1-2 sentences.
  what_this_pattern_needs:  20-40 words, 1-2 sentences. Orientation, not advice.
  explore:                  exactly 2 short probes, max 14 words each.
  reflect:                  exactly 1 journal prompt, max 18 words.
"""


def build_render_user_message(domain: str, input_bundle: Dict[str, Any]) -> str:
    """Assemble the deterministic seeds into a compact user message."""
    c = input_bundle["compressed_themes"]
    lines: List[str] = [
        f"LIFE DOMAIN: {domain}",
        "",
        "DETERMINISTIC SEEDS (compressed from all available signals — treat as raw ingredients, not prose to repeat):",
        f"  core_pattern_seed:    {c['core_pattern_seed']}",
        f"  default_tension_seed: {c['default_tension_seed']}",
        f"  distortion_seed:      {c['distortion_seed']}",
        f"  orientation_seed:     {c['orientation_seed']}",
    ]
    if c.get("memory_phase"):
        lines.append(f"  memory_phase:         {c['memory_phase']}")
    if c.get("lifeline_themes"):
        lines.append(f"  lifeline_echoes:      {', '.join(c['lifeline_themes'])}")
    lines += [
        "",
        "TASK:",
        "  1. Compress the seeds into ONE living pattern for this domain. Do not list the seeds.",
        "  2. Name the tension, then the distortion, then the orientation.",
        "  3. Respect the word budgets and banned phrasing in the system message.",
        "  4. Output strict JSON with keys: pattern, default_tension, distortion_under_pressure, what_this_pattern_needs, explore (array of 2 strings), reflect (array of 1 string).",
        "  5. Do not reference the user by name. Do not mention frameworks or lenses.",
        "",
        f"DOMAIN FOCUS ({domain}):",
        {
            "relationships": "how you initiate contact, what you assume in the silence, what the connection needs from you.",
            "work":          "how you create, lead, build; where initiation becomes over-carrying.",
            "self":          "how you hold identity, pressure, recovery, inner direction.",
        }[domain],
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Post-render filters
# ---------------------------------------------------------------------------

def scrub_banned_phrases(text: str) -> Tuple[str, List[str]]:
    """Return cleaned text + list of phrases that were hit."""
    if not isinstance(text, str):
        return "", []
    hits: List[str] = []
    def _sub(m: re.Match) -> str:
        hits.append(m.group(0).lower())
        return ""
    cleaned = BANNED_PHRASE_RE.sub(_sub, text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,.;:—")
    return cleaned, hits


def _validate_and_clean_render(raw: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Parse JSON, run banned-phrase scrub, return (payload_or_none, hits)."""
    all_hits: List[str] = []
    # Extract JSON blob (model sometimes wraps in ``` or adds preamble)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, ["no_json_detected"]
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        logger.warning("[LifeSynth] JSON parse failed: %s", e)
        return None, ["json_parse_error"]

    # Scrub each string field; arrays of strings
    for key in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = payload.get(key)
        if isinstance(v, str):
            cleaned, hits = scrub_banned_phrases(v)
            payload[key] = cleaned
            all_hits.extend(hits)
    for listkey in ("explore", "reflect"):
        arr = payload.get(listkey)
        if isinstance(arr, list):
            out_arr = []
            for s in arr:
                if isinstance(s, str):
                    cleaned, hits = scrub_banned_phrases(s)
                    out_arr.append(cleaned)
                    all_hits.extend(hits)
            payload[listkey] = out_arr

    return payload, all_hits


# ---------------------------------------------------------------------------
# Public entry — full synthesis with LLM rendering
# ---------------------------------------------------------------------------

async def generate_domain_synthesis(
    *,
    chart: Dict[str, Any],
    domain: str,
    pattern_memory: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    llm_chat_factory=None,  # callable: () -> LlmChat, injected by caller
) -> Dict[str, Any]:
    """
    End-to-end synthesis for a single domain. Exactly ONE LLM call.

    llm_chat_factory: a callable that returns a configured LlmChat instance with
    the system message baked in. The caller (server.py) owns LLM provider setup.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local import

    input_bundle = build_synthesis_input(chart, domain, pattern_memory, lifeline_summary)
    user_msg = build_render_user_message(domain, input_bundle)

    llm_output_raw: Optional[str] = None
    render_error: Optional[str] = None
    render_hits: List[str] = []

    if llm_chat_factory is None:
        render_error = "no_llm_factory"
    else:
        try:
            chat: LlmChat = llm_chat_factory()
            resp = await chat.send_message(UserMessage(text=user_msg))
            llm_output_raw = resp if isinstance(resp, str) else str(resp)
        except Exception as e:
            logger.exception("[LifeSynth] LLM render failed")
            render_error = f"llm_render_error: {e}"

    payload: Optional[Dict[str, Any]] = None
    if llm_output_raw:
        payload, render_hits = _validate_and_clean_render(llm_output_raw)

    # Fallback: use the deterministic seeds directly if LLM failed or was scrubbed empty.
    if not payload or not payload.get("pattern"):
        c = input_bundle["compressed_themes"]
        payload = {
            "pattern": _prose_from_seed(c["core_pattern_seed"]),
            "default_tension": _prose_from_seed(c["default_tension_seed"]),
            "distortion_under_pressure": _prose_from_seed(c["distortion_seed"]),
            "what_this_pattern_needs": _prose_from_seed(c["orientation_seed"]),
            "explore": [
                "Where is this pattern most alive right now?",
                "Where does the strength flip into weight?",
            ],
            "reflect": [
                "What would it look like to let this pattern end on time?",
            ],
        }

    payload["today"] = None  # reserved for P2 modulation

    return {
        "life_area": domain,
        "role_card": None,  # filled in by caller via role_card_engine
        "domain_synthesis": payload,
        "evidence_signals": input_bundle["evidence_signals"],
        "compressed_themes": input_bundle["compressed_themes"],
        "confidence": input_bundle["confidence"],
        "debug": {
            "llm_used": llm_output_raw is not None,
            "render_error": render_error,
            "banned_phrase_hits": render_hits,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "life_synth_v1a",
    }


def _prose_from_seed(seed: str) -> str:
    """Tiny sanitiser when LLM is unavailable — never ships generic filler."""
    if not seed:
        return ""
    s = seed.strip()
    s = s[0].upper() + s[1:]
    if not s.endswith((".", "?", "!")):
        s += "."
    return s
