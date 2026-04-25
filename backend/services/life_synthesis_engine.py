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
# Style filter — banned-phrase list per user's Mirror Life Synthesis Engine spec
# ---------------------------------------------------------------------------

BANNED_PHRASES: List[str] = [
    # vague abstractions (spec §8)
    "dynamic blend", "recurring theme", "invites growth",
    "multiple perspectives", "tends to", "you may find",
    "suggests that", "in many ways", "deeply connected to",
    "intuitive sense paired with", "spontaneous action",
    "emotional clarity unfolds over time", "tends to stand out",
    "multiple lenses", "various lenses", "several lenses",
    "your chart suggests", "your chart indicates", "this suggests",
    "this can sometimes", "in certain situations",
    # prescriptive / guru (spec §7, §8)
    "you should", "you must", "you need to", "you have to",
    "will happen", "is destined", "this will",
    # flatter-without-cost
    "unique gift", "beautiful balance", "powerful combination",
    "deep wisdom", "profound insight", "inner truth",
    # lens-name leakage (spec: no mention of frameworks)
    "human design", "astrology", "bazi", "ba zi", "day master",
    "enneagram", "numerology", "life path", "incarnation cross",
    "manifestor", "manifesting generator", "projector", "reflector", "generator",
    "emotional authority", "sacral authority", "splenic authority",
    # zi wei dou shu — invisible domain layer; never surface in user copy
    "zi wei", "ziwei", "zi wei dou shu", "purple star", "purple star astrology",
    "命宫", "官禄宫", "财帛宫", "夫妻宫", "疾厄宫", "交友宫", "父母宫",
    "life palace", "career palace", "wealth palace", "spouse palace",
    "health palace", "friends palace", "parents palace",
    "palace of life", "palace of career", "palace of wealth",
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


# Phase 3 — domain-specific consequence frames.
# These give the LLM a concrete axis for where the pattern LANDS in this
# domain. They are behavioural, not generic. The LLM must still write the
# final prose; these just prevent the "same paragraph three times" failure.
_DOMAIN_CONSEQUENCE_FRAME: Dict[str, Dict[str, str]] = {
    "self": {
        "focus":          "turns inward — onto identity, self-pressure, and the relationship with the self",
        "where_it_lands": "you start treating yourself the way the pattern treats everything else: as something to be refined, completed, or gotten right",
        "what_erodes":    "self-trust — you stop being able to tell the difference between your own signal and the pressure to keep moving",
        "needs_axis":     "room to exist without needing to be finished or proving anything",
    },
    "work": {
        "focus":          "shows up in execution, leadership, and what actually gets built",
        "where_it_lands": "the work starts belonging to you even when it shouldn't — the system routes around you instead of through you",
        "what_erodes":    "leverage — what was supposed to scale ends up depending on your continued involvement",
        "needs_axis":     "a handoff point that isn't conditional on you staying in the loop",
    },
    "relationships": {
        "focus":          "shows up in connection, response, and the quality of trust",
        "where_it_lands": "the other person stops reaching the real you — they reach the version of you that is already moving",
        "what_erodes":    "trust in the signal — people start to guess at what you want rather than asking, because the pattern has already made the decision",
        "needs_axis":     "a pause long enough for the other person to actually arrive",
    },
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
    dominant_tension = pattern_memory.get("dominant_tension")
    recent_tensions = pattern_memory.get("recent_tensions") or []
    dominant_lens = pattern_memory.get("dominant_lens_source")

    phase_hint: Optional[str] = None
    if memory_state == "recurring_pattern" and match_count >= 3:
        phase_hint = f"the pattern is cycling — this shape has shown up {int(match_count)} times"
    elif memory_state == "recurring_pattern":
        phase_hint = "the pattern has returned before"
    elif memory_state == "new_pattern":
        phase_hint = "the pattern is fresh — still forming its shape"
    elif evolution in ("integrating", "metabolizing"):
        phase_hint = "the pattern is softening through use"

    # Build a "recurring theme" note that can be injected into default_tension seed.
    # Keep it short + behavioural; never include quoted user text verbatim to avoid
    # lens-jargon leaking in.
    recurring_note: Optional[str] = None
    if dominant_tension and isinstance(match_count, int) and match_count >= 2:
        # Light sanitisation — lowercase, strip pipe characters, trim length.
        dt = str(dominant_tension).strip().strip('"').lower()
        dt = re.sub(r"[^a-z0-9 \-']", " ", dt)
        dt = re.sub(r"\s+", " ", dt).strip()
        if dt:
            recurring_note = f"this shape keeps returning around '{dt}'"

    # Weight scaling — richer memory → stronger weight
    weight = 0.0
    if memory_state:
        weight = 0.55
    if isinstance(match_count, int) and match_count >= 3:
        weight = 0.85
    elif isinstance(match_count, int) and match_count >= 2:
        weight = 0.7

    return {
        "memory_state":      memory_state,
        "evolution_state":   evolution,
        "match_count":       int(match_count) if isinstance(match_count, (int, float)) else 0,
        "dominant_tension":  dominant_tension,
        "dominant_lens":     dominant_lens,
        "recent_tensions":   recent_tensions[:3],
        "phase_hint":        phase_hint,
        "recurring_note":    recurring_note,
        "weight":            weight,
    }


# ---------------------------------------------------------------------------
# Lifeline contribution (stub — P3 will feed this strongly)
# ---------------------------------------------------------------------------

def _extract_lifeline(lifeline_summary: Optional[Dict[str, Any]], domain: str) -> Dict[str, Any]:
    """
    Phase 3 — Lifeline extraction per domain.

    Uses the domain-grouped lifeline summary produced by the server loader
    to produce a per-domain set of echoes that feed directly into synthesis
    seeds.
    """
    if not isinstance(lifeline_summary, dict):
        return {"weight": 0.0}
    total = lifeline_summary.get("total_events") or 0

    domain_counts = lifeline_summary.get("domain_event_counts") or {}
    domain_tone_mix = lifeline_summary.get("domain_tone_mix") or {}
    domain_recent_titles = lifeline_summary.get("domain_recent_titles") or {}
    recurring_categories = lifeline_summary.get("recurring_categories") or []

    domain_event_count = int(domain_counts.get(domain, 0) or 0)
    tone_dist = domain_tone_mix.get(domain) or {}
    titles = domain_recent_titles.get(domain) or []

    # Back-compat flat themes
    flat_themes = [str(t) for t in (lifeline_summary.get("recent_themes") or []) if t][:3]

    # Phase echo: did this domain actually show up in the user's lived history?
    phase_echo_hint: Optional[str] = None
    if domain_event_count >= 5:
        phase_echo_hint = f"this domain has shown up repeatedly across lived history ({domain_event_count} marked events)"
    elif domain_event_count >= 2:
        phase_echo_hint = "this domain has appeared more than once in lived history"

    # Emotional-cluster cue: if 'negative' or 'mixed' tones dominate, name it.
    tone_cue: Optional[str] = None
    if tone_dist:
        total_t = sum(tone_dist.values()) or 1
        neg = (tone_dist.get("negative", 0) + tone_dist.get("mixed", 0)) / total_t
        pos = tone_dist.get("positive", 0) / total_t
        if neg >= 0.4 and domain_event_count >= 3:
            tone_cue = "the emotional colour of these events leans strained"
        elif pos >= 0.5 and domain_event_count >= 3:
            tone_cue = "the emotional colour of these events leans alive"

    # Weight: scales with domain event count
    weight = 0.0
    if domain_event_count >= 5:
        weight = 0.7
    elif domain_event_count >= 2:
        weight = 0.5
    elif domain_event_count >= 1 or flat_themes:
        weight = 0.35

    return {
        "total_events":         int(total) if isinstance(total, (int, float)) else 0,
        "domain":               domain,
        "domain_event_count":   domain_event_count,
        "domain_titles":        titles[:3],
        "tone_distribution":    tone_dist,
        "phase_echo_hint":      phase_echo_hint,
        "tone_cue":             tone_cue,
        "recurring_categories": recurring_categories,
        "recent_themes":        flat_themes,
        "weight":               weight,
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
    ziwei: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Hierarchy enforced:
      0. ziwei domain origin — domain-causal seed (PRIMARY when present)
      1. core pattern        — cross-lens behavioural compression
      2. default tension     — where the pattern first strains (recurrence-aware)
      3. distortion          — how the strength flips into a problem
      4. orientation         — what restores the pattern (non-prescriptive)
      5. evidence            — top contributing lenses with weights

    `ziwei` (optional) carries domain-origin seed data. When present, it is
    the PRIMARY axis — the LLM is steered toward this domain's specific
    causal frame instead of re-projecting a single global pattern across
    every domain. NEVER surfaced as a label or quoted string in user copy.
    """
    ziwei = ziwei or {}
    ziwei_origin   = (ziwei.get("domain_pattern_origin") or "").strip()
    ziwei_tension  = (ziwei.get("domain_tension") or "").strip()
    ziwei_failure  = (ziwei.get("domain_failure_mode") or "").strip()
    ziwei_evolve   = (ziwei.get("domain_evolution_hint") or "").strip()

    # --- 1. Core pattern: domain-weighted composition.
    #
    # Domain lens balance: HD operating-style language must NOT lead every
    # domain or it makes Work / Relationships / Self all sound like the same
    # Manifestor reading. Each domain picks its strongest seed first, then
    # supplements with the other lenses. HD is allowed in EVERY domain, but
    # only as a contributing signal — never as the lead phrase for Work or
    # Relationships, where structural / lifeline / connection evidence is
    # the stronger explanatory frame.
    pattern_parts: List[str] = []
    if domain == "self":
        # Self: HD operating style is most relevant here (it is identity-shaped),
        # so it can lead. BaZi posture follows. Astro adds tone.
        if hd.get("initiation"):
            pattern_parts.append(hd["initiation"])
        if bazi.get("posture"):
            pattern_parts.append(bazi["posture"])
        if astro.get("primary_posture"):
            pattern_parts.append(astro["primary_posture"])
    elif domain == "work":
        # Work: BaZi structural posture leads (closer to systems / execution
        # / responsibility). Astro 10th-house / career sign follows. HD is
        # last and skipped if other signals already filled the seed.
        if bazi.get("posture"):
            pattern_parts.append(bazi["posture"])
        if astro.get("primary_posture"):
            pattern_parts.append(astro["primary_posture"])
        # Lifeline domain themes feed into Work seed — work-event evidence
        if ll.get("recent_themes"):
            pattern_parts.append(
                "this shape has shown up across "
                + ", ".join(ll["recent_themes"][:2])
            )
        # Only add HD if we still have <2 signals to avoid HD dominance
        if hd.get("initiation") and len(pattern_parts) < 2:
            pattern_parts.append(hd["initiation"])
    elif domain == "relationships":
        # Relationships: connection / response / trust frame leads via
        # consequence frame. Astro 7th / 5th / 8th-house posture follows.
        # BaZi adds element tone. HD last — only if room remains.
        if astro.get("primary_posture"):
            pattern_parts.append(astro["primary_posture"])
        if bazi.get("posture"):
            pattern_parts.append(bazi["posture"])
        if ll.get("recent_themes"):
            pattern_parts.append(
                "the same shape has surfaced in "
                + ", ".join(ll["recent_themes"][:2])
            )
        if hd.get("initiation") and len(pattern_parts) < 2:
            pattern_parts.append(hd["initiation"])
    else:
        # Fallback (unknown domain): old order preserved.
        if hd.get("initiation"):
            pattern_parts.append(hd["initiation"])
        if bazi.get("posture"):
            pattern_parts.append(bazi["posture"])
        if astro.get("primary_posture"):
            pattern_parts.append(astro["primary_posture"])
    core_pattern_seed = "; ".join(pattern_parts) or "moves through life in a way that's hard to compress"

    # Zi Wei domain origin leads the seed when present — the domain's own
    # causal axis is more important than any cross-lens compression.
    if ziwei_origin:
        core_pattern_seed = ziwei_origin + " — " + core_pattern_seed

    # --- 2. Default tension: domain-weighted.
    # Self leans HD friction first; Work leans BaZi strain + lifeline echo;
    # Relationships leans BaZi strain + consequence frame.
    tension_parts: List[str] = []
    if domain == "self":
        if hd.get("friction"):
            tension_parts.append(hd["friction"])
        if bazi.get("strain"):
            tension_parts.append(bazi["strain"])
    elif domain == "work":
        if bazi.get("strain"):
            tension_parts.append(bazi["strain"])
        if ll.get("phase_echo_hint"):
            tension_parts.append(ll["phase_echo_hint"])
        if hd.get("friction") and len(tension_parts) < 2:
            tension_parts.append(hd["friction"])
    elif domain == "relationships":
        if bazi.get("strain"):
            tension_parts.append(bazi["strain"])
        if hd.get("friction") and len(tension_parts) < 2:
            tension_parts.append(hd["friction"])
    else:
        if hd.get("friction"):
            tension_parts.append(hd["friction"])
        if bazi.get("strain"):
            tension_parts.append(bazi["strain"])

    # Pattern-memory phase hint and lifeline echo are added at the end for
    # all domains (they're cross-cutting evidence, not domain-specific lens).
    if pm.get("phase_hint") and pm["phase_hint"] not in tension_parts:
        tension_parts.append(pm["phase_hint"])
    if ll.get("phase_echo_hint") and ll["phase_echo_hint"] not in tension_parts:
        tension_parts.append(ll["phase_echo_hint"])
    default_tension_seed = " — ".join(tension_parts) or "tightens where it used to flow"
    if ziwei_tension:
        default_tension_seed = ziwei_tension + " — " + default_tension_seed

    # --- 3. Distortion: HD + BaZi distortion, with domain-specific CONSEQUENCE
    #     (Phase 3.1). The LLM is required to rewrite distortion per domain;
    #     these seeds give it concrete consequence material to lean on.
    domain_frame = _DOMAIN_CONSEQUENCE_FRAME.get(domain, {})
    dist_parts: List[str] = []
    if hd.get("distortion"):
        dist_parts.append(hd["distortion"])
    if bazi.get("distortion"):
        dist_parts.append(bazi["distortion"])
    if domain_frame.get("where_it_lands"):
        dist_parts.append(domain_frame["where_it_lands"])
    if domain_frame.get("what_erodes"):
        dist_parts.append("what erodes: " + domain_frame["what_erodes"])
    if pm.get("recurring_note"):
        dist_parts.append("this is not a one-time distortion; it keeps returning with the same shape")
    if ll.get("tone_cue") == "the emotional colour of these events leans strained":
        dist_parts.append("lived events in this domain carry the same strained tone")
    distortion_seed = "; ".join(dist_parts) or "the strength repeats itself past the point where it still helps"
    if ziwei_failure:
        distortion_seed = ziwei_failure + " — " + distortion_seed

    # --- 4. Orientation: BaZi restorative + HD restorative + domain needs_axis
    orient_parts: List[str] = []
    if bazi.get("restorative"):
        orient_parts.append(bazi["restorative"])
    if hd.get("restorative"):
        orient_parts.append(hd["restorative"])
    if domain_frame.get("needs_axis"):
        orient_parts.append(domain_frame["needs_axis"])
    orientation_seed = " and ".join(orient_parts) or "returns to the quality the pattern is actually for"
    if ziwei_evolve:
        orientation_seed = ziwei_evolve + "; " + orientation_seed

    return {
        "domain":               domain,
        "core_pattern_seed":    core_pattern_seed,
        "default_tension_seed": default_tension_seed,
        "distortion_seed":      distortion_seed,
        "orientation_seed":     orientation_seed,
        "lifeline_themes":      ll.get("recent_themes") or [],
        "lifeline_titles":      ll.get("domain_titles") or [],
        "lifeline_echo":        ll.get("phase_echo_hint"),
        "lifeline_tone_cue":    ll.get("tone_cue"),
        "memory_phase":         pm.get("phase_hint"),
        "memory_dominant":      pm.get("dominant_tension"),
        "memory_match_count":   pm.get("match_count") or 0,
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
        # Phase 3 — richer pattern memory signal
        pm_signal_parts: List[str] = []
        if pm.get("dominant_tension"):
            mc = pm.get("match_count") or 0
            if mc >= 2:
                pm_signal_parts.append(f"\"{pm['dominant_tension']}\" has repeated {mc}×")
            else:
                pm_signal_parts.append(f"tension: {pm['dominant_tension']}")
        elif pm.get("phase_hint"):
            pm_signal_parts.append(pm["phase_hint"])
        else:
            pm_signal_parts.append(str(pm.get("memory_state") or ""))
        out.append({
            "lens":   "pattern_memory",
            "signal": " — ".join([s for s in pm_signal_parts if s]) or "pattern memory active",
            "weight": round(pm["weight"], 2),
        })
    if ll.get("weight", 0) > 0:
        # Phase 3 — rich lifeline signal per domain
        ll_signal_parts: List[str] = []
        if ll.get("domain_event_count", 0) >= 2:
            ll_signal_parts.append(f"{ll['domain_event_count']} {ll.get('domain', '')} events in lived history")
        if ll.get("tone_cue"):
            ll_signal_parts.append(ll["tone_cue"])
        if not ll_signal_parts:
            ll_signal_parts.append(", ".join(ll.get("recent_themes") or []))
        out.append({
            "lens":   "lifeline_echoes",
            "signal": " · ".join([s for s in ll_signal_parts if s]) or "lifeline events present",
            "weight": round(ll["weight"], 2),
        })
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
# Domain weighting (Phase 3.2)
# ---------------------------------------------------------------------------
#
# Produces an asymmetric view across work / relationships / self so the Life
# tab doesn't render three equally-intense stories. Deterministic, inspectable,
# never exposes scoring language to the end user.

from collections import Counter as _DW_Counter  # alias to avoid shadow

# Pattern-memory lens_source → domain hint. The `home` lens is ambient (not
# a real domain signal), so we leave it unmapped.
_PM_LENS_TO_DOMAIN: Dict[str, str] = {
    "work":          "work",
    "career":        "work",
    "relationships": "relationships",
    "people":        "relationships",
    "person":        "relationships",
    "family":        "relationships",
    "self":          "self",
    "identity":      "self",
    "inner":         "self",
}


def _pm_domain_hint(pattern_memory: Optional[Dict[str, Any]]) -> "_DW_Counter":
    """Count pattern_memory tensions per domain via lens_source."""
    counts: "_DW_Counter" = _DW_Counter()
    if not isinstance(pattern_memory, dict):
        return counts
    dom_lens = (pattern_memory.get("dominant_lens_source") or "").lower()
    mapped = _PM_LENS_TO_DOMAIN.get(dom_lens)
    if mapped:
        counts[mapped] += 1
    for rt in (pattern_memory.get("recent_tensions") or [])[:5]:
        if not isinstance(rt, dict):
            continue
        lens = (rt.get("lens") or "").lower()
        m = _PM_LENS_TO_DOMAIN.get(lens)
        if m:
            counts[m] += 1
    return counts


def derive_domain_weights(
    pattern_memory: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic asymmetric scoring across work/relationships/self.

    Composite score per domain:
        0.5 × normalised_event_count
        0.3 × normalised_avg_impact (impact_score / 10)
        0.2 × strain_ratio           (fraction negative+mixed)
        +   0.1 bump if pattern memory lens points here

    Close-call guard: if the top score is within 15% of the second, no strong
    primary is assigned — top two become "secondary" and the third
    "background". Sparse data (<3 total events, no pattern memory) falls back
    to all-background with confidence="low".

    Returns:
      {
        work/relationships/self: "primary|secondary|background",
        scores, dominant_domain, confidence, reason
      }
    """
    domains = ("work", "relationships", "self")

    ll = lifeline_summary or {}
    event_counts: Dict[str, int] = {d: int((ll.get("domain_event_counts") or {}).get(d, 0) or 0) for d in domains}
    avg_impact: Dict[str, float] = {d: float((ll.get("domain_avg_impact") or {}).get(d, 0.0) or 0.0) for d in domains}
    strain: Dict[str, float] = {d: float((ll.get("domain_strain_ratio") or {}).get(d, 0.0) or 0.0) for d in domains}
    total_events = int(ll.get("total_events") or 0)
    pm_hint = _pm_domain_hint(pattern_memory)

    max_count = max(event_counts.values() or [0]) or 1
    scores: Dict[str, float] = {}
    for d in domains:
        norm_count = event_counts[d] / max_count if max_count else 0.0
        norm_impact = min(avg_impact[d] / 10.0, 1.0)
        pm_bump = 0.1 if pm_hint.get(d, 0) > 0 else 0.0
        scores[d] = round(
            0.5 * norm_count
            + 0.3 * norm_impact
            + 0.2 * strain[d]
            + pm_bump,
            4,
        )

    # Sparse-data fallback
    if total_events < 3 and sum(pm_hint.values()) == 0:
        return {
            "work":           "background",
            "relationships":  "background",
            "self":            "background",
            "scores":         scores,
            "dominant_domain": None,
            "confidence":     "low",
            "reason":         "not enough lived history to infer where the pattern is most active",
        }

    sorted_domains = sorted(domains, key=lambda d: scores[d], reverse=True)
    top, mid, low = sorted_domains
    top_score, mid_score = scores[top], scores[mid]

    gap = (top_score - mid_score) / max(top_score, 1e-6) if top_score > 0 else 0.0
    close_call = gap < 0.15

    weights: Dict[str, str] = {}
    dominant_domain: Optional[str] = None
    confidence: str
    reason: str

    if close_call:
        weights[top] = "secondary"
        weights[mid] = "secondary"
        weights[low] = "background"
        dominant_domain = None
        confidence = "medium" if total_events >= 5 else "low"
        reason = (
            f"{top} and {mid} both carry noticeable weight; no single domain "
            f"is clearly dominant right now"
        )
    else:
        weights[top] = "primary"
        weights[mid] = "secondary"
        weights[low] = "background"
        dominant_domain = top
        if total_events >= 10 and gap >= 0.30:
            confidence = "high"
        elif total_events >= 5:
            confidence = "medium"
        else:
            confidence = "low"
        contribs: List[str] = []
        if event_counts[top] >= 5:
            contribs.append(f"{event_counts[top]} lived events")
        if avg_impact[top] >= 6:
            contribs.append(f"high-impact moments (avg {avg_impact[top]:.1f})")
        if strain[top] >= 0.4:
            contribs.append("strained emotional tone")
        if pm_hint.get(top, 0):
            contribs.append("pattern memory points here")
        reason = (
            f"{top} is where the pattern is most active"
            + (" — " + ", ".join(contribs) if contribs else "")
        )

    return {
        "work":           weights["work"],
        "relationships":  weights["relationships"],
        "self":            weights["self"],
        "scores":         scores,
        "dominant_domain": dominant_domain,
        "confidence":     confidence,
        "reason":         reason,
    }




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

    # Zi Wei domain-origin layer — invisible domain-pattern source. Acts as
    # the PRIMARY causal seed so each domain has its own origin instead of
    # being a re-projection of one global pattern. NEVER surfaced to UI.
    try:
        from .ziwei_domain_engine import generate_ziwei_domain_pattern  # local import to keep startup light
        ziwei = generate_ziwei_domain_pattern(
            domain,
            chart=chart,
            lifeline_summary=lifeline_summary,
            pattern_memory=pattern_memory,
        )
    except Exception as e:
        logger.warning("[LifeSynth] ziwei domain origin unavailable for domain=%s: %s", domain, e)
        ziwei = {}

    compressed = _compress_themes(hd, bazi, astro, pm, ll, domain, ziwei=ziwei)
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
            "domain_origin": {
                "domain_pattern_origin": ziwei.get("domain_pattern_origin"),
                "domain_tension": ziwei.get("domain_tension"),
                "domain_failure_mode": ziwei.get("domain_failure_mode"),
                "domain_evolution_hint": ziwei.get("domain_evolution_hint"),
                "confidence": ziwei.get("confidence"),
                "source": ziwei.get("source"),
                # NOTE: 'palace' field intentionally omitted from snapshots that
                # might be exposed via debug. Internal-only.
            },
        },
    }


# ---------------------------------------------------------------------------
# LLM rendering prompt — the Mirror Life Synthesis Engine
# ---------------------------------------------------------------------------

_RENDER_SYSTEM_PROMPT = """You are the Mirror Life Synthesis Engine.

Your job is NOT to describe the user.

Your job is to:
- detect the living pattern
- show where it turns
- show what it becomes over time
- make the cost visible
- and orient the user back to alignment

==================================================
INPUT
==================================================

You will receive structured synthesis data:

- role_card:
  - role
  - tension
  - distortion
  - orientation
  - dominant_drivers

- domain_synthesis:
  - pattern
  - default_tension
  - distortion_under_pressure
  - what_this_pattern_needs
  - memory_phase_note           (optional — present if the pattern has history)
  - recurrence_signal           (optional — {repeat_count, instruction}; when present
                                  treat the distortion as a loop that keeps re-forming,
                                  NOT a first-time episode)
  - lifeline_echoes             (optional — list of past event titles; shorthand for
                                  how this domain has actually played out in life)
  - lifeline_note               (optional — domain-level echo: "this domain has shown
                                  up repeatedly in lived history")
  - lifeline_tone_cue           (optional — "lived events lean strained/alive")

- domain: (self | work | relationships)

==================================================
OUTPUT STRUCTURE
==================================================

Return ONLY valid JSON with:

{
  "role_card": {
    "role": "...",
    "tension": "...",
    "distortion": "...",
    "orientation": "...",
    "not_for": "...",
    "confidence": "high|medium|low"
  },
  "domain": {
    "pattern": "...",
    "default_tension": "...",
    "distortion_under_pressure": "...",
    "what_this_pattern_needs": "..."
  }
}

No extra keys. No markdown. No explanation.

ALL FOUR DOMAIN FIELDS (pattern, default_tension, distortion_under_pressure,
what_this_pattern_needs) MUST be rewritten as complete 2nd-person prose.
Never return raw seed fragments, semi-colon lists, or em-dash chains from
the input. If a field reads like a seed ("starts without permission; refines,
discerns..."), you have done it wrong — rewrite as a full sentence.

==================================================
CORE WRITING RULES (CRITICAL)
==================================================

1. BEHAVIOR FIRST
Write what the user DOES — not what they ARE.

Bad:
"You are intuitive and dynamic"

Good:
"You move quickly toward things that feel right"

2. INCLUDE TEMPORAL MOVEMENT
Every section MUST include progression:
- "at first... then..."
- "over time..."
- "what starts as... becomes..."
If there is no sense of time or escalation, the output is wrong.

3. DISTORTION MUST INCLUDE COST
This is the most important rule.
You MUST show:
- what the user does
- what it turns into
- what it costs them

Bad:
"You overextend yourself"

Good:
"You take on more than you intended, and over time what you started becomes something you feel responsible for finishing."

4. LEAN INTO ASYMMETRY (TRUTH > BALANCE)
Do NOT soften the message.
Avoid: "this can sometimes", "you may find", "in certain situations"
Prefer: "this turns when", "this becomes heavy when"

5. DOMAIN DIFFERENTIATION (MANDATORY)

Do NOT restate the same pattern across domains.

The root pattern may be the SAME, but each domain must produce a DIFFERENT
CONSEQUENCE. Re-describing the pattern itself is not enough — you must show
where it lands in this specific life area.

  - SELF          → describe how the pattern turns INWARD: identity, self-pressure,
                    self-trust vs self-force, internal loop, the relationship with
                    the self.
  - WORK          → describe how the pattern affects EXECUTION, leadership, and
                    outcomes: what gets built, what gets dropped, what gets carried,
                    how others end up working around you.
  - RELATIONSHIPS → describe how the pattern affects CONNECTION, response, and
                    trust: how the other person receives you, where the signal gets
                    lost, what quietly erodes between you.

Each domain's distortion_under_pressure MUST describe a consequence that is
specific to that domain — not a generic restatement of the pattern. If the
word "work" / "relationship" / "self" could be swapped between two domains and
the sentence would still read correctly, the output is wrong — rewrite.

The `pattern` and `default_tension` fields may share some root behaviour
language, but `distortion_under_pressure` and `what_this_pattern_needs` MUST
be domain-specific.

6. ROLE CARD MUST INCLUDE "NOT FOR"
Add a sharp one-liner describing what this phase is NOT for.
Example: "This is not a phase for carrying everything yourself."

7. ORIENTATION IS NOT ADVICE
Do NOT tell the user what to do.
Do describe what the pattern needs to function correctly.

Bad:  "You should step back"
Good: "This pattern works when initiation is followed by space"

8. NO GENERIC LANGUAGE
DO NOT use: "dynamic blend", "recurring theme", "invites growth", "multiple perspectives",
"tends to", "you may find", "suggests that", "in many ways", "deeply connected to".
If it sounds like a horoscope, it is wrong.

9. KEEP IT TIGHT
Each field: 1-3 sentences max, no fluff, no repetition.

10. RECURRENCE AWARENESS (CRITICAL when recurrence_signal is present)
When `recurrence_signal.repeat_count >= 2`, this is NOT a first-time episode.
Write the distortion_under_pressure as a loop that keeps re-forming:
  - show it returning, not just appearing
  - acknowledge the cost of repetition (not the cost of one event)
  - use language like "each time this returns", "this has re-formed before",
    "you've been here in this shape"
Do NOT name the user's internal tension verbatim. Do NOT quote framework names.
Let the REPETITION itself be the weight.

11. LIFELINE AWARENESS (optional)
When `lifeline_note` or `lifeline_echoes` are present, the pattern is anchored
in actual lived events in this domain. Lightly ground the default_tension or
distortion in that lived history. Do NOT invent new events. Do NOT quote event
titles. Acknowledge that the pattern has left marks, without listing them.

11A. DOMAIN LENS BALANCE (CRITICAL — anti-Manifestor-leakage)

Do NOT let one lens explain every domain.

Each domain MUST be governed by its own STRONGEST EVIDENCE:
  - WORK          = responsibility / systems / execution / career history /
                    delegation / leverage / what gets built or dropped
  - RELATIONSHIPS = connection / response / trust / emotional distance /
                    family / partner / friend dynamics / how the other person
                    actually receives you
  - SELF          = identity / inner pressure / self-trust / recovery /
                    inner clarity / the relationship with the self

11B. DOMAIN PATTERN ORIGIN (CRITICAL when domain_origin is present)

The render input may include `domain_origin` block:
  {
    domain_pattern_origin:  "what this life area is really about",
    domain_tension:         "what tension this domain carries",
    domain_failure_mode:    "what specifically fails here under pressure",
    domain_evolution_hint:  "how this part of life evolves"
  }

Treat `domain_origin` as the PRIMARY domain-causal axis. It tells you:
  - what this life area is really about (origin)
  - what tension this domain specifically carries
  - what repeats here that is different from other domains
  - how this part of life evolves

Use it to answer:
  - "what is this part of life really about?"
  - "what tension does this specific domain carry?"
  - "what repeats here in particular?"
  - "what is moving / evolving here?"

DO NOT derive one global pattern and rewrite it across domains.

DO NOT mention or hint at the source of `domain_origin`. It is an
internal architecture signal — not user-facing language. NEVER use the
words "palace", "stars", "purple star", "zi wei", "ziwei", "命宫" or any
related Chinese terminology.

The output should make the user feel "this part of my life has its own
pattern" without ever revealing the engine that produced it.

11C. DOMAIN LENS BALANCE — anti-Manifestor-leakage rules

Human Design operating-style language (e.g. "initiate without permission",
"inform before moving", "wait to respond", "seeing the system before being
asked") is ONE contributing signal. It MUST NOT be the lead frame for every
domain.

HARD CAP — at most ONE Human-Design-style concept per domain output. The
following words/phrases together count as Human-Design vocabulary:

  initiate · initiation · permission · approval · informing · inform ·
  inform-before-moving · move first · move alone · refine the standard ·
  raise the standard · without asking · without waiting · seeking approval

If you find yourself using ≥ 2 of these in a single domain, REWRITE using
domain-specific evidence (BaZi structural posture, lifeline lived history,
astrology house posture, pattern memory recurrence) instead.

ANTI-LEAKAGE TEST: Imagine a reader sees only Work, Relationships, and Self
side-by-side. If the three paragraphs sound like the same Manifestor reading
in three costumes, you have failed. Rewrite so:
  - Work sounds like work systems / responsibility / leverage
  - Relationships sounds like response gaps / connection / emotional distance
  - Self sounds like internal pressure / identity / self-trust / recovery

12. DOMAIN WEIGHTING (CRITICAL when domain_weight is present)

You will receive `domain_weight`: "primary" | "secondary" | "background".

Adjust CONSEQUENCE DEPTH — not just length — based on this.
Importance is expressed through HOW FAR YOU TRACE THE CHAIN, not sentence count.

  PRIMARY:
    - Must include a FULL CONSEQUENCE CHAIN: cause → effect → outcome.
    - Show what the user does, what it turns into, AND what it ends up
      shaping or costing over time.
    - Feels like: "this is shaping things."
    - distortion_under_pressure must trace all three links of the chain.

  SECONDARY:
    - Show consequence, but SHORTER CHAIN: cause → effect.
    - Show what the user does and what it turns into, without tracing the
      full outcome.
    - Feels like: "this is affecting things."
    - distortion_under_pressure stops at the effect; it does not fully
      unfold the outcome.

  BACKGROUND:
    - HINT AT CONSEQUENCE ONLY. No full chain.
    - Name the pattern's presence in this domain; do not unfold it.
    - Feels like: "this exists, but is not central."
    - distortion_under_pressure is ONE sentence that acknowledges the
      pattern shows up here, without describing what it turns into.

Importance is CONSEQUENCE DEPTH, not length. A background field should
feel less consequential even if it has the same word count.

If the background field traces a full chain, it is wrong — collapse it
to a presence-only acknowledgement.
If the primary field only names an effect without showing outcome, it is
wrong — extend the chain.

NEVER expose the words "primary", "secondary", "background", "weight",
"score", "weighting", "chain", or "domain" in the rendered output. The
weighting is INVISIBLE to the user. Show it through depth, not labels.

==================================================
13. DOMAIN LANGUAGE PHYSICS (CRITICAL)
==================================================

Each domain MUST use a different language field. Two domains can share
the same person, but they must NOT share the same vocabulary texture or
the same sentence physics. The user should feel "each part of my life
has its own intelligence", not "the same engine is describing different
areas".

▶ SELF — internal / reflective / identity-based language.

   Use words from this register:
     inner pressure · self-trust · identity · recovery · clarity ·
     self-correction · inner signal · standard · belonging in yourself ·
     interior · stillness · weight you carry · what you tell yourself

   AVOID for SELF (these belong to Work):
     system · leverage · delegation · output · process · infrastructure ·
     stakeholders · execution · workflow · scaling · ownership

   Sentence physics: START FROM THE INNER EXPERIENCE.
     e.g. "The pressure begins inside, before anyone asks anything of you."

▶ WORK — structural / operational / systems-based language.

   Use words from this register:
     responsibility · structure · capacity · leverage · handoff ·
     ownership · workflow · execution · system · load · distribution ·
     scaling · the work · the output · the team

   AVOID for WORK (these belong to Self / Relationships):
     self-trust · inner child · emotional closeness · intimacy ·
     belonging · love · rejection · being met · warmth

   Sentence physics: START FROM THE SYSTEM OR WORKLOAD.
     e.g. "The work starts to gather around you before the structure is
     ready to hold it."

▶ RELATIONSHIPS — interpersonal / relational / timing-based language.

   Use words from this register:
     response · distance · closeness · trust · timing · repair ·
     emotional signal · being met · reaching · receiving · warmth ·
     the pause · the silence between

   AVOID for RELATIONSHIPS (these belong to Work):
     system · leverage · workflow · delegation · output ·
     infrastructure · ownership · productivity · scaling · stakeholders

   Sentence physics: START FROM THE INTERACTION GAP.
     e.g. "The distance forms in the space between your signal and their
     response."

STRUCTURE VARIATION — Do NOT use the same sentence logic across all
domains. Avoid the lazy template "you do X → this causes Y → over time
Z" appearing in all three. Vary the entry point per domain as above so
the three outputs feel like three different worlds for the same person.

==================================================
14. DOMAIN EMOTIONAL GRAVITY (FINAL LAYER — how it LANDS, not what it says)
==================================================

Beyond vocabulary, each domain must LAND with a different emotional
gravity. The user should feel "each part of my life is a different
lived experience", not "the same engine described three areas".

▶ SELF — HIGH INTENSITY · CLOSE RANGE
   Land as RECOGNITION, not explanation.
   - Use statements, not analysis.
   - Reduce softeners. AVOID over-using "tends to", "may", "might",
     "often", "sometimes", "usually". One softener across the four
     fields is the max for SELF.
   - At least ONE sentence should be sharp enough to feel almost
     uncomfortably direct. Short. Declarative. Second-person present.
   - The user should feel: "this is about me."
   - Bad:  "You tend to carry internal pressure to refine yourself over time."
   - Good: "The pressure starts inside you — before anything is asked."

▶ WORK — MEDIUM INTENSITY · SYSTEM DISTANCE
   Land as CLARITY about a system.
   - Frame issues as system dynamics, not personal flaws.
   - Sentences can be a touch longer and more explanatory than SELF.
   - Reduce emotional charge. Increase observational distance.
   - The user should feel: "this is what's happening in the system."
   - Bad:  "You push yourself too hard and end up overwhelmed."
   - Good: "The work builds faster than the structure holding it."

▶ RELATIONSHIPS — SOFT INTENSITY · INTERPERSONAL FIELD
   Land as a SUBTLE, EXPERIENTIAL OBSERVATION.
   - Softer, relational phrasing. Focus on space, timing, response.
   - AVOID harsh or absolute language: never, always, must, fail,
     destroy, ruin, broken, never-ever.
   - Less analytical, more experiential. Acknowledge what happens
     between two people without judgment.
   - The user should feel: "this is what happens between us."
   - Bad:  "You create distance by acting too quickly."
   - Good: "The gap forms before either of you names it."

BLADE + ANCHOR enforcement (every section, every domain):
   1. BLADE  — sharp recognition line, the "I know me" moment.
   2. ANCHOR — a stabilising explanation or framing immediately after.

   SELF: blade can be very sharp; anchor grounds without softening too much.
   WORK: blade is OBSERVATIONAL (not emotional); anchor explains structure.
   RELATIONSHIPS: blade is SUBTLE (not harsh); anchor adds emotional clarity.

The three tabs side-by-side must feel like THREE different lived
experiences, not three explanations of one thing.

==================================================
QUALITY CHECK BEFORE OUTPUT
==================================================

Before returning, ensure:
- Each section contains a clear behavior
- At least one section contains time progression
- Distortion clearly shows a cost
- Language is specific, not general
- Domains feel distinct
- Role card includes "not_for"
- SWAP TEST: could you exchange the word "work" with "relationships" or "self"
  in distortion_under_pressure and the sentence would still read correctly?
  If YES, the output is wrong — rewrite with a domain-specific CONSEQUENCE.
- CONSEQUENCE DEPTH TEST (when domain_weight is present):
    PRIMARY   distortion → cause → effect → outcome (full chain present)
    SECONDARY distortion → cause → effect (stops at effect, no full outcome)
    BACKGROUND distortion → presence only (no chain, one-sentence acknowledgement)
  If the background field traces a full chain, collapse it. If the primary
  field only names an effect without outcome, extend the chain.

If not, rewrite internally.

==================================================
EXAMPLE STYLE (REFERENCE ONLY — DO NOT COPY)
==================================================

Pattern:
"You move toward things quickly and initiate without waiting. At first this creates momentum, but over time what you begin has a way of becoming something you carry."

Distortion:
"You keep stepping in to keep things moving, and eventually the system depends on you in a way that becomes difficult to step out of."

Orientation:
"This works when momentum is followed by space, not continued involvement."

==================================================
FINAL RULE
==================================================

Do not explain the system.
Do not mention lenses.
Do not sound like analysis.

It should feel like:
"This is exactly what I do... and I can see where it turns."
"""


def build_render_user_message(
    domain: str,
    input_bundle: Dict[str, Any],
    role_seeds: Optional[Dict[str, Any]] = None,
    domain_weight_info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Assemble the deterministic seeds into a compact structured input for the
    Mirror Life Synthesis Engine. The engine expects BOTH role_card seeds and
    domain_synthesis seeds; it returns rendered versions of both.
    """
    c = input_bundle["compressed_themes"]

    role_block: Dict[str, Any] = {}
    if role_seeds:
        role_block = {
            "role":              role_seeds.get("role_seed", ""),
            "tension":           role_seeds.get("tension_seed", ""),
            "distortion":        role_seeds.get("distortion_seed", ""),
            "orientation":       role_seeds.get("orientation_seed", ""),
            "dominant_drivers":  role_seeds.get("dominant_drivers", []),
        }
    else:
        # Role card will not be re-rendered inline; leave seeds minimal so the
        # model fills with stub coherence (caller will discard role_card block).
        role_block = {
            "role":             "",
            "tension":          "",
            "distortion":       "",
            "orientation":      "",
            "dominant_drivers": [],
        }

    domain_block = {
        "pattern":                   c["core_pattern_seed"],
        "default_tension":           c["default_tension_seed"],
        "distortion_under_pressure": c["distortion_seed"],
        "what_this_pattern_needs":   c["orientation_seed"],
    }

    # Phase 3.2 — domain weighting. Tells the renderer how dominant this
    # domain is in the user's current life so outputs feel asymmetric
    # (primary = main arena, secondary = spillover, background = quieter).
    if domain_weight_info and domain_weight_info.get(domain):
        weight = domain_weight_info.get(domain)  # primary | secondary | background
        instr_map = {
            "primary":
                "This is the MAIN ARENA where the pattern is currently active. "
                "distortion_under_pressure MUST trace a FULL CONSEQUENCE CHAIN: "
                "cause → effect → outcome. Show what the user does, what it "
                "turns into, AND what it ends up shaping or costing over time. "
                "Feels like: 'this is shaping things.'",
            "secondary":
                "This is a SPILLOVER arena. distortion_under_pressure traces a "
                "SHORTER CHAIN: cause → effect. Show what the user does and "
                "what it turns into, but do NOT fully unfold the outcome. "
                "Feels like: 'this is affecting things.'",
            "background":
                "This domain is PRESENT BUT NOT CENTRAL. distortion_under_pressure "
                "is a HINT AT CONSEQUENCE ONLY — one sentence acknowledging the "
                "pattern shows up here, without tracing what it turns into. "
                "Feels like: 'this exists, but is not central.' "
                "If you trace a full chain for this domain, you have done it wrong.",
        }
        domain_block["domain_weight"] = {
            "weight":      weight,
            "confidence":  domain_weight_info.get("confidence", "medium"),
            "instruction": instr_map.get(weight, instr_map["secondary"]),
        }

    # Phase 3.1 — explicit domain consequence frame so the LLM has a concrete
    # axis it must hit. Prevents the "same paragraph three times" failure mode.
    frame = _DOMAIN_CONSEQUENCE_FRAME.get(domain)
    if frame:
        domain_block["domain_frame"] = {
            "focus":          frame["focus"],
            "where_it_lands": frame["where_it_lands"],
            "what_erodes":    frame["what_erodes"],
            "needs_axis":     frame["needs_axis"],
            "instruction":    "distortion_under_pressure MUST describe `where_it_lands` and `what_erodes` in this specific domain — not a generic restatement of the pattern. Apply the SWAP TEST before finalising.",
        }
    if c.get("memory_phase"):
        domain_block["memory_phase_note"] = c["memory_phase"]
    if c.get("memory_match_count") and c.get("memory_match_count") >= 2:
        # Phase 3 — tell the renderer the pattern has REPEATED, so it
        # writes the distortion as a CYCLE not a one-off episode.
        domain_block["recurrence_signal"] = {
            "repeat_count":          int(c["memory_match_count"]),
            "instruction":           "this exact shape has shown up multiple times before — write the distortion as a loop that keeps re-forming, not a first-time event",
        }
    if c.get("lifeline_titles"):
        domain_block["lifeline_echoes"] = c["lifeline_titles"]
    elif c.get("lifeline_themes"):
        domain_block["lifeline_echoes"] = c["lifeline_themes"]
    if c.get("lifeline_echo"):
        domain_block["lifeline_note"] = c["lifeline_echo"]
    if c.get("lifeline_tone_cue"):
        domain_block["lifeline_tone_cue"] = c["lifeline_tone_cue"]

    # Domain Pattern Origin — invisible domain-causal axis. Comes from the
    # zi-wei-domain-engine placeholder. Surfaced to the LLM as a
    # `domain_origin` block; the LLM treats this as the PRIMARY frame.
    domain_origin_snapshot = (
        input_bundle.get("lens_snapshots", {}).get("domain_origin") or {}
    )
    if any([
        domain_origin_snapshot.get("domain_pattern_origin"),
        domain_origin_snapshot.get("domain_tension"),
        domain_origin_snapshot.get("domain_failure_mode"),
        domain_origin_snapshot.get("domain_evolution_hint"),
    ]):
        domain_block["domain_origin"] = {
            "domain_pattern_origin": domain_origin_snapshot.get("domain_pattern_origin", ""),
            "domain_tension":        domain_origin_snapshot.get("domain_tension", ""),
            "domain_failure_mode":   domain_origin_snapshot.get("domain_failure_mode", ""),
            "domain_evolution_hint": domain_origin_snapshot.get("domain_evolution_hint", ""),
            "instruction":
                "Treat domain_origin as the PRIMARY domain-causal axis. Use it "
                "to answer: what is this part of life really about? what "
                "tension does this domain specifically carry? what repeats "
                "here? what is moving here? Do NOT mention or hint at the "
                "source of this signal — never use the words palace, stars, "
                "purple star, zi wei, ziwei, 命宫, or any related Chinese "
                "terminology in the user-facing copy.",
        }

    payload = {
        "role_card":         role_block,
        "domain_synthesis":  domain_block,
        "domain":            domain,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


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


# ---------------------------------------------------------------------------
# Domain Lens Balance — anti-Manifestor-leakage cap.
#
# After the LLM renders, count Human-Design-style vocabulary across the four
# domain prose fields. If a single domain trips ≥ 2 HD-vocab hits, log a
# diagnostic flag (not a hard rewrite — the prompt rule is the primary guard,
# this is monitoring + safety net so we can detect regressions).
# ---------------------------------------------------------------------------

_HD_VOCAB_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.I) for p in [
        r"\binitiat(?:e|ion|ing|or)\b",
        r"\bpermission\b",
        r"\bapproval\b",
        r"\binform(?:s|ed|ing|-before-moving)?\b",
        r"\bmove(?:s|d)?\s+(?:first|alone)\b",
        r"\bwithout\s+(?:asking|waiting|approval|permission)\b",
        r"\b(?:raise|raises|raising|raised|refine|refines|refining|refined)\s+(?:the\s+)?standard(?:s)?\b",
        r"\bseek(?:s|ing)?\s+(?:permission|approval)\b",
        r"\bwait(?:s|ing|ed)?\s+(?:for|to|on)\s+(?:permission|approval|response)\b",
    ]
]


def _count_hd_vocab(text: str) -> Tuple[int, List[str]]:
    """Count Human-Design-style vocabulary hits in a string. Returns (count, matched_phrases)."""
    if not isinstance(text, str) or not text:
        return 0, []
    hits: List[str] = []
    for pat in _HD_VOCAB_PATTERNS:
        for m in pat.finditer(text):
            hits.append(m.group(0).lower())
    return len(hits), hits


def _domain_lens_balance_audit(domain_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audit a domain payload for HD-vocab over-use. Returns a diagnostic dict
    with per-field counts. Logs a warning if any field has ≥ 2 HD hits.
    Used for monitoring; does not rewrite content (prompt + seed weighting
    are the primary guards).
    """
    if not isinstance(domain_payload, dict):
        return {"hd_total": 0, "fields": {}, "flagged": False}
    audit: Dict[str, Any] = {"fields": {}, "hd_total": 0, "flagged": False}
    for field in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = domain_payload.get(field, "")
        count, phrases = _count_hd_vocab(v)
        audit["fields"][field] = {"count": count, "phrases": phrases}
        audit["hd_total"] += count
        if count >= 2:
            audit["flagged"] = True
    return audit


# ---------------------------------------------------------------------------
# Domain Emotional Gravity — final audit on HOW the insight LANDS.
#
# SELF — high intensity / close range. Should land as recognition.
#   Fails if too many softeners ("tends to", "may", "often", ...) — analytical drift.
#   Fails if no sharp recognition line is present (every sentence too long/explainery).
#
# WORK — medium intensity / system distance. Should land as system clarity.
#   Fails if it leaks emotional/identity charge (overlap with lang_physics,
#   so we re-use part of that audit).
#
# RELATIONSHIPS — soft intensity / interpersonal field.
#   Fails if it uses harsh / absolute language (must, never, always, fail,
#   destroy, ruin, broken).
# ---------------------------------------------------------------------------

_SOFTENER_RE = re.compile(
    r"\b(?:tends? to|tend to|may|might|often|sometimes|usually|"
    r"typically|generally|seems? to|appears? to|seems like|seems? like)\b",
    re.I,
)

# A "sharp" SELF line: short (≤ 90 chars), declarative, second-person
# present, no softener, ends with "." or "—".
_SECOND_PERSON_RE = re.compile(r"\b(?:you|your)\b", re.I)

# Harsh / absolute language for RELATIONSHIPS audit.
_HARSH_ABSOLUTE_RE = re.compile(
    r"\b(?:never|always|must|fail(?:s|ed|ing)?|destroy(?:s|ed|ing)?|"
    r"ruin(?:s|ed|ing)?|broken|impossible|hopeless|toxic|wrecks?|"
    r"shatter(?:s|ed|ing)?)\b",
    re.I,
)


def _has_sharp_recognition_line(payload: Dict[str, Any]) -> bool:
    """A blade line is short, declarative, second-person, softener-free."""
    if not isinstance(payload, dict):
        return False
    for field in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = payload.get(field, "")
        if not isinstance(v, str) or not v:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", v.strip()):
            s = sentence.strip()
            if not s or len(s) > 110:
                continue
            if _SOFTENER_RE.search(s):
                continue
            if not _SECOND_PERSON_RE.search(s):
                continue
            return True
    return False


def _count_softeners(payload: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Count softener phrases across the four prose fields."""
    if not isinstance(payload, dict):
        return 0, []
    hits: List[str] = []
    for field in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = payload.get(field, "")
        if isinstance(v, str) and v:
            hits.extend(m.group(0).lower() for m in _SOFTENER_RE.finditer(v))
    return len(hits), hits


def _count_harsh_absolutes(payload: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Count harsh / absolute words across the four prose fields."""
    if not isinstance(payload, dict):
        return 0, []
    hits: List[str] = []
    for field in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = payload.get(field, "")
        if isinstance(v, str) and v:
            hits.extend(m.group(0).lower() for m in _HARSH_ABSOLUTE_RE.finditer(v))
    return len(hits), hits


def _domain_emotional_gravity_audit(domain: str, domain_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns {flagged, reason, counts}. Used as a TONE audit AFTER the
    language-physics audit. Only flags clear failures so we don't retry too
    aggressively.
    """
    audit: Dict[str, Any] = {"flagged": False, "reason": "", "counts": {}}
    if not isinstance(domain_payload, dict) or not domain:
        return audit

    softener_count, softener_hits = _count_softeners(domain_payload)
    harsh_count, harsh_hits = _count_harsh_absolutes(domain_payload)
    audit["counts"] = {
        "softeners": {"count": softener_count, "phrases": softener_hits},
        "harsh_absolutes": {"count": harsh_count, "phrases": harsh_hits},
        "has_sharp_line": _has_sharp_recognition_line(domain_payload),
    }

    d = domain.lower()
    if d == "self":
        # SELF must land as recognition — too many softeners breaks intensity,
        # absence of any sharp line means the LLM only delivered analysis.
        if softener_count >= 3:
            audit["flagged"] = True
            audit["reason"] = f"self_too_many_softeners ({softener_count})"
        elif not audit["counts"]["has_sharp_line"]:
            audit["flagged"] = True
            audit["reason"] = "self_no_sharp_recognition_line"
    elif d == "relationships":
        # RELATIONSHIPS must land subtly — harsh / absolute words break that field.
        if harsh_count >= 2:
            audit["flagged"] = True
            audit["reason"] = f"relationships_too_harsh ({harsh_count})"
    # WORK tone audit covered by the language-physics layer (emotional/identity
    # vocab is already forbidden), so no separate gravity rule fires here.
    return audit



#
# Each domain has its own vocabulary register (set in prompt rule 13).
# After the LLM renders, we count hits of forbidden cross-domain vocabulary
# and flag any domain that crosses into another domain's register.
#
# Self  fails if it leans too operational (system, leverage, workflow, ...).
# Work  fails if it leans too emotional/identity (self-trust, intimacy, ...).
# Rels  fails if it leans too operational (system, workflow, output, ...).
# ---------------------------------------------------------------------------

_DOMAIN_FORBIDDEN_VOCAB: Dict[str, List[str]] = {
    # Self should not sound like Work
    "self": [
        r"\bsystem(?:s)?\b",
        r"\bleverage\b",
        r"\bdelegation\b",
        r"\bworkflow(?:s)?\b",
        r"\boutput(?:s)?\b",
        r"\binfrastructure\b",
        r"\bscaling\b",
        r"\bstakeholder(?:s)?\b",
        r"\bhandoff(?:s)?\b",
        r"\bdistribution\b",
    ],
    # Work should not sound like Self / Relationships
    "work": [
        r"\bself[- ]trust\b",
        r"\binner\s+(?:child|signal|voice)\b",
        r"\bintimacy\b",
        r"\bbelonging\b",
        r"\brejection\b",
        r"\bemotional\s+closeness\b",
        r"\bbeing\s+met\b",
        r"\bwarmth\b",
        r"\blove\b",
    ],
    # Relationships should not sound like Work
    "relationships": [
        r"\bsystem(?:s)?\b",
        r"\bleverage\b",
        r"\bworkflow(?:s)?\b",
        r"\bdelegation\b",
        r"\boutput(?:s)?\b",
        r"\binfrastructure\b",
        r"\bproductivity\b",
        r"\bownership\b",
        r"\bscaling\b",
        r"\bstakeholder(?:s)?\b",
    ],
}

_DOMAIN_FORBIDDEN_PATTERNS: Dict[str, List[re.Pattern]] = {
    domain: [re.compile(p, re.I) for p in patterns]
    for domain, patterns in _DOMAIN_FORBIDDEN_VOCAB.items()
}


def _count_forbidden_vocab(text: str, domain: str) -> Tuple[int, List[str]]:
    """Count cross-domain forbidden vocabulary hits in a string."""
    if not isinstance(text, str) or not text:
        return 0, []
    pats = _DOMAIN_FORBIDDEN_PATTERNS.get(domain.lower())
    if not pats:
        return 0, []
    hits: List[str] = []
    for pat in pats:
        for m in pat.finditer(text):
            hits.append(m.group(0).lower())
    return len(hits), hits


def _domain_language_audit(domain: str, domain_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audit a domain payload for cross-domain vocabulary leakage.
    Domain fails if ≥ 2 forbidden hits in any field, or ≥ 3 across all fields.
    Returns a diagnostic dict {fields: {...}, total_hits: N, flagged: bool}.
    """
    if not isinstance(domain_payload, dict) or not domain:
        return {"total_hits": 0, "fields": {}, "flagged": False}
    audit: Dict[str, Any] = {"fields": {}, "total_hits": 0, "flagged": False}
    for field in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = domain_payload.get(field, "")
        count, phrases = _count_forbidden_vocab(v, domain)
        audit["fields"][field] = {"count": count, "phrases": phrases}
        audit["total_hits"] += count
        if count >= 2:
            audit["flagged"] = True
    if audit["total_hits"] >= 3:
        audit["flagged"] = True
    return audit


def _validate_and_clean_render(raw: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Parse JSON produced by the Mirror Life Synthesis Engine, run banned-phrase
    scrub on every string field in {role_card, domain}, and return cleaned
    payload.
    """
    all_hits: List[str] = []
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, ["no_json_detected"]
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        logger.warning("[LifeSynth] JSON parse failed: %s", e)
        return None, ["json_parse_error"]

    # Scrub role_card strings
    rc = payload.get("role_card") or {}
    if isinstance(rc, dict):
        for k in ("role", "tension", "distortion", "orientation", "not_for"):
            v = rc.get(k)
            if isinstance(v, str):
                cleaned, hits = scrub_banned_phrases(v)
                rc[k] = cleaned
                all_hits.extend(hits)
        payload["role_card"] = rc

    # Scrub domain strings
    dom = payload.get("domain") or payload.get("domain_synthesis") or {}
    if isinstance(dom, dict):
        for k in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
            v = dom.get(k)
            if isinstance(v, str):
                cleaned, hits = scrub_banned_phrases(v)
                dom[k] = cleaned
                all_hits.extend(hits)
        payload["domain"] = dom

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
    role_seeds: Optional[Dict[str, Any]] = None,
    domain_weight_info: Optional[Dict[str, Any]] = None,
    llm_chat_factory=None,  # callable: () -> LlmChat, injected by caller
) -> Dict[str, Any]:
    """
    End-to-end synthesis for a single domain. Exactly ONE LLM call that renders
    BOTH the role_card AND the domain_synthesis (per Mirror Life Synthesis
    Engine contract).

    llm_chat_factory: a callable that returns a configured LlmChat instance with
    the system message baked in. The caller (server.py) owns LLM provider setup.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # local import

    input_bundle = build_synthesis_input(chart, domain, pattern_memory, lifeline_summary)
    user_msg = build_render_user_message(
        domain,
        input_bundle,
        role_seeds=role_seeds,
        domain_weight_info=domain_weight_info,
    )

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

    parsed: Optional[Dict[str, Any]] = None
    if llm_output_raw:
        parsed, render_hits = _validate_and_clean_render(llm_output_raw)

    domain_payload: Optional[Dict[str, Any]] = None
    role_payload: Optional[Dict[str, Any]] = None
    if parsed:
        domain_payload = parsed.get("domain")
        role_payload = parsed.get("role_card")

    # Fallback: deterministic seeds if LLM failed or was scrubbed empty.
    if not domain_payload or not domain_payload.get("pattern"):
        c = input_bundle["compressed_themes"]
        domain_payload = {
            "pattern":                   _prose_from_seed(c["core_pattern_seed"]),
            "default_tension":           _prose_from_seed(c["default_tension_seed"]),
            "distortion_under_pressure": _prose_from_seed(c["distortion_seed"]),
            "what_this_pattern_needs":   _prose_from_seed(c["orientation_seed"]),
        }

    # Post-render guard: strip any accidental weight vocabulary leakage
    # ("primary domain", "secondary arena", "background", etc.) from user-facing
    # text. This is a belt-and-braces safety net — the prompt already forbids
    # it, but user copy must never expose scoring language.
    for f in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
        v = domain_payload.get(f)
        if isinstance(v, str) and v:
            domain_payload[f] = _strip_weight_vocab(v)

    # Phase 3.2 — Consequence-depth trim for BACKGROUND.
    # The prompt asks for a "hint at consequence only" one-sentence distortion
    # when weight=background, but the LLM sometimes traces a full chain even
    # within a single compound sentence. Deterministically clip at the first
    # clause boundary (period / semicolon) AND enforce a char cap so the
    # depth/length matches the weight band.
    target_weight = (domain_weight_info or {}).get(domain) if domain_weight_info else None
    if target_weight == "background":
        # tighter per-field caps — distortion max ~140 chars, needs max ~120
        caps = {"distortion_under_pressure": 140, "what_this_pattern_needs": 120}
        for f, cap in caps.items():
            v = domain_payload.get(f)
            if not (isinstance(v, str) and v):
                continue
            trimmed = _trim_to_first_clause(v, max_chars=cap)
            if trimmed and len(trimmed) < len(v) * 0.9:
                domain_payload[f] = trimmed

    # Domain Lens Balance audit — monitor for HD-vocab over-use. Logged for
    # diagnostics; the prompt rules + seed weighting are the primary guards.
    lens_audit = _domain_lens_balance_audit(domain_payload)
    if lens_audit.get("flagged"):
        logger.warning(
            "[LifeSynth] HD-vocab over-use in domain=%s | total_hits=%d | per_field=%s",
            domain, lens_audit["hd_total"], lens_audit["fields"],
        )
    elif lens_audit.get("hd_total", 0) > 0:
        logger.info(
            "[LifeSynth] HD-vocab usage in domain=%s | total_hits=%d (under cap)",
            domain, lens_audit["hd_total"],
        )

    # Domain Language Physics audit — check that the domain stayed within
    # its own vocabulary register. If it leaked into another domain's
    # register, regenerate ONCE with a stronger language instruction;
    # if still failing, log and continue (prompt rules are the primary
    # guard, this is a safety net).
    lang_audit = _domain_language_audit(domain, domain_payload)
    if lang_audit.get("flagged") and llm_chat_factory is not None:
        logger.warning(
            "[LifeSynth] domain language leakage in domain=%s | total_hits=%d | per_field=%s — retrying once",
            domain, lang_audit["total_hits"], lang_audit["fields"],
        )
        # Build a stronger language-physics instruction tailored to this domain
        leaked_words = sorted({
            w for f in lang_audit["fields"].values() for w in f.get("phrases", [])
        })
        register_hint = {
            "self":          "internal / reflective / identity-based — inner pressure, self-trust, identity, recovery, clarity, self-correction, inner signal, standard, belonging in yourself. AVOID: system, leverage, delegation, workflow, output, infrastructure, scaling, ownership.",
            "work":          "structural / operational / systems-based — responsibility, structure, capacity, leverage, handoff, ownership, workflow, execution, system, load, distribution, scaling. AVOID: self-trust, inner child, intimacy, belonging, rejection, emotional closeness, being met, warmth, love.",
            "relationships": "interpersonal / relational / timing-based — response, distance, closeness, trust, timing, repair, emotional signal, being met, reaching, receiving, warmth, the pause. AVOID: system, leverage, workflow, delegation, output, infrastructure, productivity, ownership, scaling.",
        }.get(domain, "")
        retry_msg = (
            user_msg
            + "\n\n=== RETRY INSTRUCTION (CRITICAL) ===\n"
            + f"Your previous draft for domain '{domain}' used cross-domain "
            + "vocabulary that does not belong in this register. Leaked terms: "
            + (", ".join(leaked_words) if leaked_words else "(see audit)")
            + ".\nRewrite the entire JSON keeping the same content frame but "
            + f"strictly within the {domain.upper()} language register: "
            + register_hint
            + "\nDo NOT use the leaked terms. Keep all other rules (no banned "
            + "phrases, no mention of palace/zi wei/ziwei, no mention of "
            + "weight/primary/secondary/background, etc.)."
        )
        try:
            chat2: LlmChat = llm_chat_factory()
            resp2 = await chat2.send_message(UserMessage(text=retry_msg))
            llm_output_raw2 = resp2 if isinstance(resp2, str) else str(resp2)
            parsed2, _hits2 = _validate_and_clean_render(llm_output_raw2)
            if parsed2 and isinstance(parsed2.get("domain"), dict) and parsed2["domain"].get("pattern"):
                # Strip weight vocab on the retry payload too
                retry_payload = parsed2["domain"]
                for f in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
                    v = retry_payload.get(f)
                    if isinstance(v, str) and v:
                        retry_payload[f] = _strip_weight_vocab(v)
                # Apply same background trim if applicable
                if target_weight == "background":
                    caps = {"distortion_under_pressure": 140, "what_this_pattern_needs": 120}
                    for f, cap in caps.items():
                        v = retry_payload.get(f)
                        if isinstance(v, str) and v:
                            trimmed = _trim_to_first_clause(v, max_chars=cap)
                            if trimmed and len(trimmed) < len(v) * 0.9:
                                retry_payload[f] = trimmed
                # Re-audit; only swap in if the retry actually improved things
                retry_lang_audit = _domain_language_audit(domain, retry_payload)
                if retry_lang_audit["total_hits"] < lang_audit["total_hits"]:
                    logger.info(
                        "[LifeSynth] domain language retry improved domain=%s | %d → %d hits",
                        domain, lang_audit["total_hits"], retry_lang_audit["total_hits"],
                    )
                    domain_payload = retry_payload
                    if retry_lang_audit.get("flagged"):
                        logger.warning(
                            "[LifeSynth] domain language still flagged after retry domain=%s | total_hits=%d",
                            domain, retry_lang_audit["total_hits"],
                        )
                else:
                    logger.warning(
                        "[LifeSynth] domain language retry did not improve domain=%s (%d → %d hits) — keeping original",
                        domain, lang_audit["total_hits"], retry_lang_audit["total_hits"],
                    )
        except Exception as e:
            logger.warning("[LifeSynth] domain language retry failed for domain=%s: %s", domain, e)
    elif lang_audit.get("total_hits", 0) > 0:
        logger.info(
            "[LifeSynth] domain language usage in domain=%s | total_hits=%d (under cap)",
            domain, lang_audit["total_hits"],
        )

    # Domain Emotional Gravity audit — final tone layer. Checks HOW the
    # output LANDS (Self = sharp/close, Work = clear/system-distance,
    # Relationships = subtle/no-harsh-absolutes). Retry once with a
    # stronger gravity instruction if flagged; if still failing, log and
    # continue.
    gravity_audit = _domain_emotional_gravity_audit(domain, domain_payload)
    if gravity_audit.get("flagged") and llm_chat_factory is not None:
        logger.warning(
            "[LifeSynth] emotional gravity flag in domain=%s | reason=%s | counts=%s — retrying once",
            domain, gravity_audit.get("reason"), gravity_audit.get("counts"),
        )
        gravity_hint = {
            "self": (
                "SELF must land as RECOGNITION, not analysis. "
                "Use short declarative second-person sentences. "
                "Drop softeners ('tends to', 'may', 'often', 'sometimes', 'usually'). "
                "Include AT LEAST ONE sharp recognition line that feels almost "
                "uncomfortably direct — short, declarative, present tense, no softener."
            ),
            "work": (
                "WORK must land as SYSTEM CLARITY. Frame issues as system "
                "dynamics, not personal flaws. Reduce emotional charge."
            ),
            "relationships": (
                "RELATIONSHIPS must land SUBTLY. Remove harsh / absolute words "
                "(never, always, must, fail, destroy, ruin, broken, toxic). "
                "Lean on space, timing, response, repair — not judgment."
            ),
        }.get(domain, "")
        retry_msg2 = (
            user_msg
            + "\n\n=== GRAVITY RETRY (CRITICAL) ===\n"
            + f"Your previous draft for domain '{domain}' did not land with the "
            + f"correct emotional gravity (audit reason: {gravity_audit.get('reason')}).\n"
            + gravity_hint
            + "\nKeep the same content frame and Zi Wei domain origin. Keep all "
            + "vocabulary-physics rules. Only adjust the TONE / sentence physics."
        )
        try:
            chat3: LlmChat = llm_chat_factory()
            resp3 = await chat3.send_message(UserMessage(text=retry_msg2))
            llm_output_raw3 = resp3 if isinstance(resp3, str) else str(resp3)
            parsed3, _hits3 = _validate_and_clean_render(llm_output_raw3)
            if parsed3 and isinstance(parsed3.get("domain"), dict) and parsed3["domain"].get("pattern"):
                retry_payload2 = parsed3["domain"]
                # Re-apply the same scrub / clause trim guards
                for f in ("pattern", "default_tension", "distortion_under_pressure", "what_this_pattern_needs"):
                    v = retry_payload2.get(f)
                    if isinstance(v, str) and v:
                        retry_payload2[f] = _strip_weight_vocab(v)
                if target_weight == "background":
                    caps = {"distortion_under_pressure": 140, "what_this_pattern_needs": 120}
                    for f, cap in caps.items():
                        v = retry_payload2.get(f)
                        if isinstance(v, str) and v:
                            trimmed = _trim_to_first_clause(v, max_chars=cap)
                            if trimmed and len(trimmed) < len(v) * 0.9:
                                retry_payload2[f] = trimmed
                # Re-audit gravity AND keep the language audit intact
                retry_lang = _domain_language_audit(domain, retry_payload2)
                retry_grav = _domain_emotional_gravity_audit(domain, retry_payload2)
                # Only swap in if gravity improved AND language didn't regress
                if not retry_grav.get("flagged") and retry_lang["total_hits"] <= lang_audit["total_hits"] + 1:
                    logger.info(
                        "[LifeSynth] gravity retry improved domain=%s (reason resolved)",
                        domain,
                    )
                    domain_payload = retry_payload2
                else:
                    logger.warning(
                        "[LifeSynth] gravity retry did not satisfy guards in domain=%s "
                        "(grav_flagged=%s, lang_total=%d) — keeping original",
                        domain, retry_grav.get("flagged"), retry_lang["total_hits"],
                    )
        except Exception as e:
            logger.warning("[LifeSynth] gravity retry failed for domain=%s: %s", domain, e)
    elif gravity_audit.get("counts"):
        logger.info(
            "[LifeSynth] gravity audit pass in domain=%s | sharp_line=%s | softeners=%d | harsh=%d",
            domain,
            gravity_audit["counts"].get("has_sharp_line"),
            gravity_audit["counts"].get("softeners", {}).get("count", 0),
            gravity_audit["counts"].get("harsh_absolutes", {}).get("count", 0),
        )

    # Reserved slots (contract promise to UI / P2)
    domain_payload.setdefault("today", None)
    domain_payload.setdefault("explore", [])
    domain_payload.setdefault("reflect", [])

    return {
        "life_area":        domain,
        "role_card":        role_payload,  # may be None; caller fills from role_card_engine if needed
        "domain_synthesis": domain_payload,
        "evidence_signals": input_bundle["evidence_signals"],
        "compressed_themes": input_bundle["compressed_themes"],
        "confidence":       input_bundle["confidence"],
        "domain_weight":        (domain_weight_info or {}).get(domain),
        "domain_weight_confidence": (domain_weight_info or {}).get("confidence"),
        "domain_weight_reason":     (domain_weight_info or {}).get("reason"),
        "debug": {
            "llm_used":           llm_output_raw is not None,
            "render_error":       render_error,
            "banned_phrase_hits": render_hits,
            "domain_weight":      (domain_weight_info or {}).get(domain),
            "domain_weight_confidence": (domain_weight_info or {}).get("confidence"),
            "domain_weight_reason":     (domain_weight_info or {}).get("reason"),
            "domain_weight_scores":     (domain_weight_info or {}).get("scores"),
        },
        "generated_at":      datetime.now(timezone.utc).isoformat(),
        "generator_version": "life_synth_v1a7_emotional_gravity",
    }


# Weight vocabulary that must never appear in user-facing copy
_WEIGHT_VOCAB_RE = re.compile(
    r"\b(primary|secondary|background)\s+(domain|arena|area|lens)\b|"
    r"\b(scoring|weighting|weight|score)\b",
    re.IGNORECASE,
)


def _strip_weight_vocab(text: str) -> str:
    """Remove any scoring/weighting vocabulary that might leak from the LLM."""
    if not text:
        return text
    cleaned = _WEIGHT_VOCAB_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    return cleaned.strip()


def _trim_to_first_clause(text: str, max_chars: int = 140) -> str:
    """
    Collapse a compound/long sentence down to the first clause or full sentence,
    whichever comes first. Used for BACKGROUND-weight fields so they stay a
    "hint at consequence only" and don't render a full cause → effect → outcome
    chain.
    """
    if not isinstance(text, str):
        return text
    t = text.strip()
    if not t:
        return t
    min_clause_chars = max(60, max_chars // 3)
    boundary_re = re.compile(r"[.!?;](?=\s|$)")
    cand = None
    for m in boundary_re.finditer(t):
        end = m.end()
        if end < min_clause_chars:
            continue
        if end > max_chars + 10:
            break
        cand = end
        break

    if cand is not None:
        out = t[:cand].rstrip()
    elif len(t) <= max_chars:
        out = t
    else:
        # Hard cap at nearest space before max_chars
        out = t[:max_chars].rsplit(" ", 1)[0].rstrip(",;: ")
        if not out.endswith((".", "!", "?")):
            out = out + "."

    # Clean dangling punctuation and connector/determiner artifacts that appear
    # when we cut mid-clause (e.g. "...for your.", "...and the.", "...to the.")
    if out.endswith(";"):
        out = out[:-1].rstrip() + "."
    out = re.sub(
        r"\b(and|but|while|so|which|that|because|though|although|yet|or|for|to|in|on|at|of|with|by|from)(\s+(the|a|an|your|my|his|her|their|its|our))?\.\s*$",
        ".",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(the|a|an|your|my|his|her|their|its|our)\.\s*$",
        ".",
        out,
        flags=re.IGNORECASE,
    )
    # Also strip a trailing comma-only ending we may have left when hard-capping
    out = re.sub(r"[,;:]\s*\.\s*$", ".", out)
    out = re.sub(r"\.{2,}", ".", out)
    # Collapse " ." (orphan period after space)
    out = re.sub(r"\s+\.\s*$", ".", out)
    return out.strip()


def _prose_from_seed(seed: str) -> str:
    """Tiny sanitiser when LLM is unavailable — never ships generic filler."""
    if not seed:
        return ""
    s = seed.strip()
    s = s[0].upper() + s[1:]
    if not s.endswith((".", "?", "!")):
        s += "."
    return s
