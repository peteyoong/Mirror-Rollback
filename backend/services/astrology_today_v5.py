"""
Astrology Today v5 Interpreter (hybrid)
=======================================

Pipeline:
  1. Call transit_dominance_engine.build_dominance_payload() — structured.
  2. Produce a DETERMINISTIC diagnosis sentence from the dominant signal.
  3. Ask the LLM for ONLY paragraphs 2-4 (ground / pattern / watch-for),
     passing the dominance payload as signal. The LLM is NOT allowed to
     recompute astrology or choose a different dominant signal.
  4. Merge deterministic sentence 1 + LLM paragraphs 2-4 into the final
     user-facing prose.
  5. Apply the continuity rule: if prior signature == today signature,
     the deterministic seed uses continuity language
     ("The same window is still open, and the pressure is narrower
     today…") so the output never copies yesterday verbatim.

Zero astrology jargon in user-facing text. Technical details belong in
the `why_this_is_showing_up` proof payload.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.transit_dominance_engine import build_dominance_payload

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 25
_SYSTEM_PROMPT = (
    "You are extending an astrology-today daily reflection. A deterministic "
    "'diagnosis sentence' has already been produced from the day's dominant "
    "timing signal. Your job is to write ONLY paragraphs 2, 3 and 4 that "
    "follow it.\n\n"
    "STYLE RULES\n"
    "- Second person. Lowercase-voice. No exclamations.\n"
    "- Do NOT mention planets, signs, houses, aspects, transits, decans, "
    "  degrees, moon phases (no 'full moon', 'new moon', 'waxing', "
    "  'waning'), or any astrology jargon at all.\n"
    "- Do NOT use words like 'culmination', 'ingress', 'retrograde'.\n"
    "- Refer to the day abstractly: 'today', 'this window', 'this short "
    "  stretch'.\n"
    "- Do NOT repeat the diagnosis sentence.\n"
    "- Do NOT use vague phrases like 'energy is shifting', 'the universe', "
    "  'cosmic', 'vibes', 'stars align'.\n"
    "- Paragraphs should be 2-3 short sentences each. Concrete, "
    "  behavior-focused, specific.\n"
    "- If CONTINUITY=true, use continuity phrasing — the same window is "
    "  still open, but you are a day deeper in. Do NOT say 'nothing new'.\n\n"
    "STRUCTURE (exactly 3 paragraphs in order)\n"
    "  Paragraph 2 — WHERE IT LANDS IN LIFE:\n"
    "    Based on HOUSE_HINT and DOMAIN_HINT, describe where today's "
    "    pressure shows up in daily life (communication / relationships / "
    "    money / work / home / body / inner).\n"
    "  Paragraph 3 — WHAT PATTERN IT MAY TRIGGER:\n"
    "    What old habit or pattern is most likely to activate? Name the "
    "    failure mode directly.\n"
    "  Paragraph 4 — WHAT TO WATCH IN BEHAVIOUR:\n"
    "    One or two concrete tells a person could actually notice in their "
    "    own day.\n\n"
    "OUTPUT FORMAT\n"
    "Return strict JSON with keys: where_it_lands, pattern_trigger, "
    "watch_for. Each value is a single string (one paragraph)."
)


# ---------------------------------------------------------------------------
# Deterministic diagnosis sentence (paragraph 1)
# ---------------------------------------------------------------------------

_DIAGNOSIS_TEMPLATES = {
    # dominant_signal.type → template
    "full_moon": (
        "This is not a subtle day. Something that has been building is "
        "reaching its visible moment — whatever you can see clearly now is "
        "what this window is for."
    ),
    "new_moon": (
        "The ground is quiet in a particular way. This is a seeding window, "
        "not a proving one — what you choose to begin here sets tone, not "
        "outcome."
    ),
    "outer_ingress": (
        "The background is changing. The way you think, speak, or react to "
        "new information may not behave like it used to — give yourself a "
        "slightly wider margin."
    ),
    "heavy_ingress": (
        "Something structural is moving underneath. You may not feel it "
        "sharply today, but the floor you are standing on is being re-laid."
    ),
    "tight_aspect": (
        "A sharp, short-window activation is exact. This is the kind of day "
        "where one decision or one conversation can cut further than "
        "normal — clarity matters more than speed."
    ),
    "moon_luminary_trigger": (
        "A feeling is rising faster than usual. This is a short window — "
        "it deserves your attention, but it does not have to become a "
        "decision before the hour is out."
    ),
    "moon_sign_change": (
        "The emotional frame of the day has shifted. What felt relevant "
        "yesterday may feel like a different conversation now — don't "
        "trust yesterday's mood to read today."
    ),
    "personal_ingress": (
        "The day is about to change register. A short-range shift is "
        "close enough that you can already feel the tone changing."
    ),
    "strong_aspect": (
        "Your mind, or your pace, is running ahead of your certainty — "
        "that gap is where today's mistake can happen, and where today's "
        "real clarity also lives."
    ),
    "sign_cluster": (
        "The day is weighted in one direction. More of your attention than "
        "usual belongs to a single theme — resist the urge to spread it "
        "thin."
    ),
    "house_cluster": (
        "A particular area of life is getting most of the day's signal. "
        "Meeting it there, rather than anywhere else, is how you use today."
    ),
}

_CONTINUITY_TEMPLATES = {
    "full_moon":            "The culmination window is still open — you are one day deeper into it now, and what was visible yesterday is asking to be named today.",
    "new_moon":             "The seeding window holds. What you began yesterday is still forming — do not re-decide yet.",
    "outer_ingress":        "The background shift is still running. The edge that felt unfamiliar yesterday is starting to look like the new normal.",
    "heavy_ingress":        "The structural move is still underway. Today is not a fresh diagnosis — it is a continuation.",
    "tight_aspect":         "The sharp activation is still live. The orb is narrower or wider than yesterday, but the same cut is still being made.",
    "moon_luminary_trigger": "The same feeling is still near the surface. It is one day further from its peak, not a new feeling.",
    "moon_sign_change":     "The emotional frame from yesterday is still the operating frame. You are two days inside it now.",
    "personal_ingress":     "The shift is still approaching. You can feel the tone continuing to change.",
    "strong_aspect":        "The same aspect is still shaping you. Your pace-versus-certainty gap has not yet closed.",
    "sign_cluster":         "The same theme still carries the day's weight. Another day in the same register.",
    "house_cluster":        "The same area of life is still pulling signal. Meet it there again today.",
}


def _diagnosis_for(
    dominant_type: Optional[str],
    is_continuity: bool,
) -> str:
    if not dominant_type:
        return (
            "Today does not have a headline to offer. The background is "
            "doing most of the work — this is a day for maintenance, "
            "noticing, and not forcing a diagnosis."
        )
    if is_continuity:
        return _CONTINUITY_TEMPLATES.get(dominant_type) or _DIAGNOSIS_TEMPLATES.get(
            dominant_type,
        ) or "The same timing signal is still live."
    return _DIAGNOSIS_TEMPLATES.get(dominant_type) or (
        "A timing signal is active today that is worth your attention."
    )


def _domain_hint_from_signal(signal: Dict[str, Any]) -> str:
    """Map a dominant signal to a domain chip hint."""
    if not signal:
        return "general"
    t = signal.get("type")
    if t in ("tight_aspect", "strong_aspect", "moon_luminary_trigger"):
        n = (signal.get("natal") or "").lower()
        if n in ("venus",):    return "relationships"
        if n in ("mercury",):  return "communication"
        if n in ("mars",):     return "action"
        if n in ("saturn",):   return "responsibility"
        if n in ("moon",):     return "inner life"
        if n in ("sun",):      return "identity"
    if t in ("sign_cluster",):
        return "concentration"
    if t in ("house_cluster",):
        return f"house {signal.get('house')}"
    if t == "moon_sign_change":
        return "emotional frame"
    return "general"


def _house_hint_from_signal(signal: Dict[str, Any]) -> str:
    h = (signal or {}).get("house")
    if isinstance(h, int) and 1 <= h <= 12:
        return {
            1: "identity / how you show up",
            2: "money / security / self-worth",
            3: "communication / daily routines / decisions",
            4: "home / family / emotional foundation",
            5: "creativity / joy / what you pour yourself into",
            6: "work / health / daily habits",
            7: "relationships / partnerships",
            8: "intimacy / shared resources / transformation",
            9: "beliefs / meaning / long-range direction",
            10: "career / reputation / public life",
            11: "community / future vision / friendships",
            12: "rest / solitude / inner life",
        }[h]
    return "no specific life area — the signal is systemic"


# ---------------------------------------------------------------------------
# LLM call for paragraphs 2-4
# ---------------------------------------------------------------------------

async def _call_llm_for_paragraphs(
    dominance: Dict[str, Any],
    is_continuity: bool,
) -> Optional[Dict[str, str]]:
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
    if not EMERGENT_LLM_KEY:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception:
        return None

    dom = dominance.get("dominant_signal") or {}
    user_payload = {
        "continuity":     is_continuity,
        "dominant_type":  dom.get("type"),
        "dominant_label": dom.get("label"),
        "why":            dominance.get("why_today_is_different"),
        "intensity":      dominance.get("intensity"),
        "house_hint":     _house_hint_from_signal(dom),
        "domain_hint":    _domain_hint_from_signal(dom),
        # Give the LLM visibility on secondary pressure so its paragraph 2/3
        # can reflect it, but do NOT ask it to re-rank.
        "secondary_labels": [s.get("label") for s in (dominance.get("secondary_signals") or [])][:3],
    }
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"astro_v5_{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
            system_message=_SYSTEM_PROMPT,
        )
        chat.with_model("openai", os.environ.get("OPENAI_PRIMARY_MODEL", "gpt-4o"))
        try:
            chat.with_params(
                timeout=LLM_TIMEOUT_SECONDS,
                request_timeout=LLM_TIMEOUT_SECONDS,
                num_retries=0,
            )
        except Exception:
            pass
        resp = await asyncio.wait_for(
            chat.send_message(UserMessage(text=json.dumps(user_payload, ensure_ascii=False))),
            timeout=LLM_TIMEOUT_SECONDS + 3,
        )
        raw = resp.strip() if isinstance(resp, str) else str(resp).strip()
        # Strip markdown fences if any
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        parsed = json.loads(raw)
        out = {
            "where_it_lands":   str(parsed.get("where_it_lands") or "").strip(),
            "pattern_trigger":  str(parsed.get("pattern_trigger") or "").strip(),
            "watch_for":        str(parsed.get("watch_for") or "").strip(),
        }
        if not out["where_it_lands"] or not out["pattern_trigger"] or not out["watch_for"]:
            return None
        return out
    except Exception as e:
        logger.warning("[AstroTodayV5] LLM call failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Interpretation orchestrator
# ---------------------------------------------------------------------------

async def build_today_v5_payload(
    user_id: str,
    chart_doc: Optional[Dict[str, Any]],
    prior_day_payload: Optional[Dict[str, Any]] = None,
    dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    dominance = build_dominance_payload(user_id, chart_doc, dt=dt, prior_day_payload=prior_day_payload)
    dom = dominance.get("dominant_signal") or {}
    dom_type = dom.get("type")

    # Continuity: prior_day_payload has the same signature
    is_continuity = bool(
        prior_day_payload
        and prior_day_payload.get("signature_hash") == dominance["signature_hash"]
    )

    diagnosis = _diagnosis_for(dom_type, is_continuity)

    # Hybrid: LLM for paragraphs 2-4
    llm_parts = await _call_llm_for_paragraphs(dominance, is_continuity)
    if llm_parts:
        where_it_lands  = llm_parts["where_it_lands"]
        pattern_trigger = llm_parts["pattern_trigger"]
        watch_for       = llm_parts["watch_for"]
    else:
        # Deterministic fallback — avoid silent failure
        where_it_lands = (
            "Today lands most directly in "
            + _house_hint_from_signal(dom)
            + "."
        )
        pattern_trigger = (
            "The pattern most likely to activate is your default way of "
            "reacting when things press — notice it before it becomes a move."
        )
        watch_for = (
            "Watch for the first small sign that you are moving faster than "
            "your clarity. That is the tell."
        )

    body_md = "\n\n".join([diagnosis, where_it_lands, pattern_trigger, watch_for])

    return {
        "user_id":              user_id,
        "date":                 (dt or datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
        "timestamp_utc":        dominance["timestamp_utc"],
        "headline":             diagnosis,
        "body_markdown":        body_md,
        "paragraphs": {
            "diagnosis":       diagnosis,
            "where_it_lands":  where_it_lands,
            "pattern_trigger": pattern_trigger,
            "watch_for":       watch_for,
        },
        "intensity":            dominance["intensity"],
        "continuity":           is_continuity,
        "why_today_is_different": dominance["why_today_is_different"],
        "dominant_signal":      dominance["dominant_signal"],
        "secondary_signals":    dominance["secondary_signals"],
        "background_signals":   dominance["background_signals"],
        "signature_hash":       dominance["signature_hash"],
        "signature_changed":    dominance["signature_changed"],
        # Proof accordion payload — client surfaces under "Why this is showing up"
        "why_this_is_showing_up": {
            "dominant_signal":      dominance["dominant_signal"],
            "secondary_signals":    dominance["secondary_signals"],
            "background_signals":   dominance["background_signals"],
            "intensity":            dominance["intensity"],
            "moon_phase":           dominance["moon_phase"],
            "tight_aspect_count":   dominance["tight_aspect_count"],
            "aspect_count":         dominance["aspect_count"],
        },
        "llm_used":             llm_parts is not None,
    }


__all__ = ["build_today_v5_payload"]
