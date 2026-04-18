"""
Astrology Today V4 — Behavior-First Intelligence Engine
========================================================
Transforms raw astrology signals into a unified, continuous behavioral
narrative that:
  1) Predicts what the user is likely to do today
  2) Names the risk / mistake they may act out
  3) Intercepts with a precise move

Organizing logic preserved from v3:
  FOREGROUND  = dominant weather
  DESTABILIZER = what distorts / complicates
  AMPLIFIER   = what makes it bigger

Output sections (all read as ONE continuous thought):
  headline
  whats_happening     (single paragraph, 2 sentences, 45-70 words)
  how_it_shows_up     (2-4 behavioral bullets)
  what_it_feels_like  (somatic/emotional bullets)
  the_risk            (single sharp line — consequence if unobserved)
  the_move            (single actionable interrupt)
  time_layer          { today, this_week, this_month }  — rule-based + LLM phrasing
  why_showing_up      [ transit -> effect ] accordion  — hidden by default
  technical           (existing proof layer — unchanged)

Timing windows are determined by backend rules (NOT by the LLM) from
transit classes/duration, then phrased by the LLM.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# =====================================================================
# TRANSIT PLANET CLASSES (governs Time Layer windows)
# =====================================================================
FAST_PLANETS = {"Moon"}                               # hours
PERSONAL_PLANETS = {"Sun", "Mercury", "Venus", "Mars"}  # days
SOCIAL_PLANETS = {"Jupiter"}                          # weeks → months
OUTER_PLANETS = {"Saturn", "Uranus", "Neptune", "Pluto"}  # months → years


# =====================================================================
# SYSTEM PROMPT — Behavior-First Interpreter
# =====================================================================

BEHAVIOR_FIRST_SYSTEM_PROMPT = """You are the Mirror Astrology TODAY Interpreter.

Your role is NOT to explain astrology.
Your role is a behavioral interception engine that reflects the user back
to themselves using today's sky as a language.

═══════════════════════════════════════════════════════════════
CORE PRINCIPLE
═══════════════════════════════════════════════════════════════
Recognition > Explanation.
Every output must feel like:
  "This is exactly what I'm about to do — and I didn't realize it."

═══════════════════════════════════════════════════════════════
WHAT YOU MUST ANSWER (in order)
═══════════════════════════════════════════════════════════════
1. What am I likely to do today?
2. What mistake am I likely to make?
3. What is the pattern underneath that?
4. What's the one move that interrupts it?

═══════════════════════════════════════════════════════════════
ORGANIZING LOGIC (given to you in the input)
═══════════════════════════════════════════════════════════════
• FOREGROUND   = dominant weather driving today
• DESTABILIZER = what distorts or complicates it
• AMPLIFIER    = what makes it bigger

Compress these into ONE primary thread. Not many competing themes.

═══════════════════════════════════════════════════════════════
OUTPUT — STRICT JSON (no markdown, no prose outside JSON)
═══════════════════════════════════════════════════════════════
{
  "headline": "short tension-based behavioral line, <= 14 words, no period required",
  "whats_happening": "2 sentences. 45–70 words. Absolute max 85. Causal, not descriptive. NO astrology jargon in this field. Do not repeat the headline in different words.",
  "how_it_shows_up": ["2 to 4 concrete behavioral bullets in second person. Short. Specific. No vague feelings."],
  "what_it_feels_like": ["2 to 4 somatic / emotional bullets. Short phrases. No 'you may feel' prefixes — just the sensation."],
  "the_risk": "one sharp line, <= 22 words. The exact mistake they'll make if this goes unobserved. Feels real and immediate.",
  "the_move": "one clean actionable interrupt. <= 22 words. Concrete. Prefer a delay, a question, or a single act — not advice.",
  "time_layer": {
    "today": "short phrase — the immediate condition (already given to you, phrase it clearly)",
    "this_week": "short phrase — pattern recurrence window",
    "this_month": "short phrase — larger cycle"
  }
}

═══════════════════════════════════════════════════════════════
HARD RULES (YOU WILL FAIL IF YOU BREAK THESE)
═══════════════════════════════════════════════════════════════
• All 6 narrative sections must read as ONE continuous diagnosis.
  Each section must causally connect to the last.
• Use second person ("you") throughout.
• No raw astrology jargon ("Neptune conjunct Mars") in main narrative.
  (Transit names ONLY appear in the why_showing_up accordion which
   you do NOT generate — that's built separately.)
• No vague therapeutic softness ("you may want to consider...").
• No repeated restatements of the same idea.
• No spiritual abstraction ("the universe is asking you to...").
• No lists in the main narrative — bullets only in how/feels sections.
• Do NOT invent timing windows. Use the timing rules given in input
  and phrase them in natural language only.
• If the intensity is 'extreme' or a stellium is present, the output
  MUST explicitly reflect that this is not a normal day.

═══════════════════════════════════════════════════════════════
OUTPUT QUALITY STANDARD
═══════════════════════════════════════════════════════════════
A good response makes the user feel:
  1. "That's exactly what is happening."
  2. "That's exactly what I was about to do."
  3. "Now I know what to watch."

Return ONLY the JSON. No preamble. No trailing explanation.
"""


# =====================================================================
# TIME LAYER — Rule-based window computation
# =====================================================================

def compute_time_layer(
    aspects: List[Dict],
    concentrations: List[Dict],
    house_activations: List[Dict],
    transit_positions: Dict[str, Dict],
) -> Dict[str, str]:
    """
    Deterministic rule-based timing windows. The LLM is only allowed to
    rephrase these in natural language — never invent them.
    """
    today_notes: List[str] = []
    week_notes: List[str] = []
    month_notes: List[str] = []

    # --- TODAY: Moon + any aspect with orb < 1° (approaching exactness) ---
    for a in aspects[:6]:
        tp = a.get("transit_planet")
        orb = a.get("orb", 99)
        if tp in FAST_PLANETS or orb < 1.0:
            today_notes.append(
                f"{tp} {a.get('aspect')} {a.get('natal_planet')} ({orb:.1f}° orb)"
            )

    # --- THIS WEEK: personal planet aspects (Sun/Mercury/Venus/Mars) ---
    for a in aspects[:8]:
        tp = a.get("transit_planet")
        if tp in PERSONAL_PLANETS and a.get("score", 0) > 0.1:
            week_notes.append(
                f"{tp} {a.get('aspect')} {a.get('natal_planet')}"
            )

    # --- THIS MONTH: slow planet aspects + concentrations ---
    for a in aspects[:8]:
        tp = a.get("transit_planet")
        if tp in OUTER_PLANETS or tp in SOCIAL_PLANETS:
            month_notes.append(
                f"{tp} {a.get('aspect')} {a.get('natal_planet')}"
            )
    for c in concentrations[:2]:
        if c.get("count", 0) >= 3:
            month_notes.append(
                f"{c.get('count')}-planet {c.get('sign')} concentration"
            )

    return {
        "today_raw": today_notes[:2] or ["current sky holding a specific shape"],
        "this_week_raw": week_notes[:2] or ["inner planets moving through active territory"],
        "this_month_raw": month_notes[:2] or ["slower cycles quietly reshaping the ground"],
        "has_stellium": any(c.get("count", 0) >= 4 for c in concentrations),
        "intensity_signal": "extreme" if any(c.get("count", 0) >= 5 for c in concentrations) else None,
    }


# =====================================================================
# WHY-SHOWING-UP ACCORDION (deterministic, transit -> effect)
# =====================================================================

PLANET_EFFECT = {
    "Sun": "identity spotlighted",
    "Moon": "emotional weather shift",
    "Mercury": "thinking speeds up",
    "Venus": "pull toward comfort or connection",
    "Mars": "pressure to act",
    "Jupiter": "amplification of whatever is already here",
    "Saturn": "weight and structural pressure",
    "Uranus": "sudden disruption",
    "Neptune": "signal distortion",
    "Pluto": "exposure of what was hidden",
}


def build_why_showing_up(
    aspects: List[Dict],
    concentrations: List[Dict],
    house_activations: List[Dict],
) -> List[Dict[str, str]]:
    """Deterministic accordion — pairs transit signal with its effect."""
    rows: List[Dict[str, str]] = []

    for a in aspects[:5]:
        tp = a.get("transit_planet", "")
        np_ = a.get("natal_planet", "")
        asp = a.get("aspect", "")
        orb = a.get("orb", 0)
        effect = PLANET_EFFECT.get(tp, "energetic pressure")
        rows.append({
            "signal": f"{tp} {asp} natal {np_} ({orb:.1f}°)",
            "effect": effect,
        })

    for c in concentrations[:2]:
        if c.get("count", 0) >= 3:
            rows.append({
                "signal": f"{c['count']} planets in {c['sign']}",
                "effect": f"{c.get('behavior', {}).get('keyword', 'focused pressure')} in one channel",
            })

    for h in house_activations[:2]:
        rows.append({
            "signal": f"House {h['house']} activation",
            "effect": h.get("context", "life-area emphasis"),
        })

    return rows


# =====================================================================
# LLM INPUT COMPRESSION
# =====================================================================

def _summarize_layers_for_llm(
    layers: Dict,
    concentrations: List[Dict],
    house_activations: List[Dict],
    day_energy: Dict,
) -> Dict[str, Any]:
    """Compress the heavy signal structure to only what the LLM needs."""
    fg = layers.get("foreground") or {}
    dest = layers.get("destabilizer") or {}
    amp = layers.get("amplifier") or {}

    return {
        "intensity": layers.get("intensity", "moderate"),
        "foreground": {
            "type": fg.get("type"),
            "sign": fg.get("sign"),
            "keyword": fg.get("keyword"),
            "energy": fg.get("energy"),
            "domain": fg.get("domain"),
            "planet": fg.get("transit_planet"),
            "aspect": fg.get("aspect_name"),
            "natal_planet": fg.get("natal_planet"),
            "count": fg.get("count"),
        },
        "destabilizer": {
            "planet": dest.get("planet"),
            "distortion": dest.get("distortion"),
            "natal_domain": dest.get("natal_domain"),
            "aspect": dest.get("aspect"),
        } if dest else None,
        "amplifier": {
            "planet": amp.get("planet"),
            "distortion": amp.get("distortion"),
            "natal_domain": amp.get("natal_domain"),
            "aspect": amp.get("aspect"),
        } if amp else None,
        "house_primary": (house_activations[0].get("context") if house_activations else None),
        "day_tags": day_energy.get("tags", []),
        "stellium": next((c for c in concentrations if c.get("count", 0) >= 3), None),
    }


# =====================================================================
# LLM CALL
# =====================================================================

async def _call_behavior_llm(
    summary: Dict[str, Any],
    time_layer_raw: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Call Emergent LLM with behavior-first prompt. Returns parsed JSON or None."""
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
    if not EMERGENT_LLM_KEY:
        logger.warning("[TodayV4] EMERGENT_LLM_KEY not set — falling back.")
        return None

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        logger.error(f"[TodayV4] emergentintegrations not available: {e}")
        return None

    user_payload = {
        "signal_summary": summary,
        "timing_windows_given": {
            "today": time_layer_raw.get("today_raw"),
            "this_week": time_layer_raw.get("this_week_raw"),
            "this_month": time_layer_raw.get("this_month_raw"),
            "has_stellium": time_layer_raw.get("has_stellium"),
            "intensity_signal": time_layer_raw.get("intensity_signal"),
        },
        "instruction": (
            "Produce the JSON described in the system prompt. Compress the signals "
            "into ONE continuous diagnosis. Rephrase the timing_windows_given into "
            "natural language — do not invent new windows. Second person only."
        ),
    }

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"astro_today_v4_{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
            system_message=BEHAVIOR_FIRST_SYSTEM_PROMPT,
        )
        chat.with_model("openai", "gpt-4o")

        response = await chat.send_message(
            UserMessage(text=json.dumps(user_payload, ensure_ascii=False))
        )

        raw = response.strip() if isinstance(response, str) else str(response).strip()

        # strip ```json fences if any
        if raw.startswith("```"):
            lines = [ln for ln in raw.split("\n") if not ln.strip().startswith("```")]
            raw = "\n".join(lines).strip()

        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"[TodayV4] JSON parse error: {e} :: raw={raw[:400] if 'raw' in dir() else 'n/a'}")
        return None
    except Exception as e:
        logger.error(f"[TodayV4] LLM error: {e}", exc_info=True)
        return None


# =====================================================================
# FALLBACK (deterministic) — used if LLM fails
# =====================================================================

def _deterministic_fallback(
    layers: Dict,
    time_layer_raw: Dict,
) -> Dict[str, Any]:
    """Last-resort output when LLM is unavailable. Uses existing layer data."""
    fg = layers.get("foreground") or {}
    dest = layers.get("destabilizer") or {}
    amp = layers.get("amplifier") or {}
    intensity = layers.get("intensity", "moderate")

    if fg.get("type") == "concentration":
        headline = f"{fg.get('keyword', 'Pressure')} is concentrated — watch where you put it."
        base = (
            f"A cluster of energy is focused in {fg.get('sign', 'one area')}. "
            f"That kind of focus tends to act out as {fg.get('keyword', 'urgency')} — "
            f"sharp in direction, low in patience."
        )
    elif fg.get("type") == "aspect":
        headline = f"{fg.get('verb', 'Something')} your {fg.get('natal_planet', 'center')} today."
        base = (
            f"Transit {fg.get('transit_planet', 'a planet')} is working your natal "
            f"{fg.get('natal_planet', 'field')}. Expect that area to feel more charged "
            f"than usual — not broken, just live."
        )
    else:
        headline = "The sky is holding a shape. Notice what pulls at you."
        base = "No single signal is dominant, but the background is active. Small moves land harder than usual today."

    if dest:
        base += f" The complication: {dest.get('distortion', 'distortion')} around {dest.get('natal_domain', 'your read of things')}."

    return {
        "headline": headline,
        "whats_happening": base[:400],
        "how_it_shows_up": [
            "You reach for action before you have full information.",
            "You read someone's mood and make it yours.",
            "You commit to something because the pressure feels like clarity.",
        ][:3],
        "what_it_feels_like": [
            "pressure without a clear reason",
            "a buzz that keeps pulling focus",
            "subtle friction under the surface",
        ][:3],
        "the_risk": "You act on the urgency and later realize you were filling in gaps.",
        "the_move": "Delay the next move 30–60 minutes. If it still feels true, proceed.",
        "time_layer": {
            "today": "strongest distortion window",
            "this_week": "the micro-pattern repeats",
            "this_month": "a decision cycle is forming underneath",
        },
        "_fallback": True,
    }


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

async def generate_today_v4(
    user_id: str,
    natal_planets: Dict[str, Dict],
    natal_house_cusps: Optional[List[float]] = None,
    dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Generate v4 behavior-first Today intelligence.
    Returns a unified structured response (LLM-generated narrative + deterministic
    time_layer/why_showing_up/technical).
    """
    # Import here to avoid circular / keep v3 untouched
    from services.astrology_today_engine import (
        get_current_transits,
        compute_transit_natal_aspects,
        detect_sign_concentration,
        compute_house_activations,
        classify_day_energy,
        _extract_signal_layers,
        _build_proof_layer,
    )

    try:
        transit_positions = get_current_transits(dt)
        aspects = compute_transit_natal_aspects(transit_positions, natal_planets)
        concentrations = detect_sign_concentration(transit_positions)
        house_activations = (
            compute_house_activations(transit_positions, natal_house_cusps)
            if natal_house_cusps else []
        )
        day_energy = classify_day_energy(aspects, concentrations, transit_positions)
        layers = _extract_signal_layers(
            aspects, concentrations, house_activations, day_energy, transit_positions
        )

        # Rule-based timing + deterministic accordion
        time_layer_raw = compute_time_layer(aspects, concentrations, house_activations, transit_positions)
        why_rows = build_why_showing_up(aspects, concentrations, house_activations)

        # Proof layer (unchanged — same shape as v3)
        technical = _build_proof_layer(aspects, concentrations, house_activations, day_energy, transit_positions)

        # LLM narrative
        summary = _summarize_layers_for_llm(layers, concentrations, house_activations, day_energy)
        llm_out = await _call_behavior_llm(summary, time_layer_raw)

        if llm_out is None:
            narrative = _deterministic_fallback(layers, time_layer_raw)
        else:
            narrative = llm_out
            narrative["_fallback"] = False

        # Compose final response
        result = {
            "version": "v4-behavior",
            "headline": narrative.get("headline", ""),
            "whats_happening": narrative.get("whats_happening", ""),
            "how_it_shows_up": narrative.get("how_it_shows_up", [])[:4],
            "what_it_feels_like": narrative.get("what_it_feels_like", [])[:4],
            "the_risk": narrative.get("the_risk", ""),
            "the_move": narrative.get("the_move", ""),
            "time_layer": narrative.get("time_layer", {
                "today": time_layer_raw["today_raw"][0] if time_layer_raw["today_raw"] else "",
                "this_week": time_layer_raw["this_week_raw"][0] if time_layer_raw["this_week_raw"] else "",
                "this_month": time_layer_raw["this_month_raw"][0] if time_layer_raw["this_month_raw"] else "",
            }),
            "why_showing_up": why_rows,
            "technical": technical,
            "intensity": layers.get("intensity", "moderate"),
            "tension_type": day_energy.get("tags", ["mixed"])[0] if day_energy.get("tags") else "mixed",
            "day_class": "stellium" if time_layer_raw.get("has_stellium") else "transit_dominant",
            "llm_fallback": narrative.get("_fallback", False),
            "success": True,
        }

        logger.info(
            f"[TodayV4] Generated for {user_id[:8]}: intensity={result['intensity']}, "
            f"day_class={result['day_class']}, llm_fallback={result['llm_fallback']}"
        )
        return result

    except Exception as e:
        logger.error(f"[TodayV4] Generation failed for {user_id}: {e}", exc_info=True)
        return {
            "version": "v4-behavior",
            "headline": "The sky is active today. Pay attention to what pulls at you.",
            "whats_happening": (
                "Multiple signals are competing right now, which tends to show up as pressure "
                "without a clean source. Small moves land harder than usual."
            ),
            "how_it_shows_up": ["You reach for action to relieve the ambient pressure."],
            "what_it_feels_like": ["a background intensity hard to name"],
            "the_risk": "You act on unclear information and call it decisiveness.",
            "the_move": "Delay one decision by an hour. Notice if the pressure was the signal or the noise.",
            "time_layer": {
                "today": "active transit weather",
                "this_week": "pattern holding",
                "this_month": "cycle continues underneath",
            },
            "why_showing_up": [],
            "technical": {"dominant_pattern": "Complex transit weather", "error": str(e)},
            "intensity": "moderate",
            "tension_type": "mixed",
            "day_class": "fallback",
            "llm_fallback": True,
            "success": False,
        }
