"""
Astrology Today v5 Interpreter — Mirror Language upgrade
========================================================

Narrative generation layer ONLY. Engine, classification, API contract,
caching, and proof payload are untouched.

New structure (replaces the 4-paragraph body):
  1. CORE MESSAGE   — HOOK / BODY / EDGE diagnosis. Tension-based when
                      multiple Tier 1/2 signals conflict.
  2. HOW IT SHOWS UP — 3-5 concrete behavioural bullets. Each bullet must
                      map to a real-world action a person would
                      recognise instantly.
  3. THE RISK       — ONE sharp sentence. The consequence of the default
                      move, not a generic warning.
  4. THE MOVE       — non-prescriptive opening. No numbers, no
                      instructions, no "should". Two lines:
                        ACTION   — a framing, not a directive
                        REFLECT  — a live question the reader can sit with

Guardrails enforced in the LLM prompt + post-process:
  • Banned vague vocabulary: energy, alignment, flow, projection, vibes,
    cosmic, stars, universe, resonance, manifest, frequency.
  • Banned astrology jargon: planet/sign/house/aspect/transit names,
    moon phases (full/new/waxing/waning), degrees, retrograde,
    decan, culmination, ingress.
  • Banned prescriptive tokens: number patterns ("30 minutes", "three
    hours"), the word "should", "must".
  • De-dupe: each section must introduce new information. If the move
    or risk overlaps >=60% of the core-message tokens, we regenerate.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from services.transit_dominance_engine import build_dominance_payload

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 25
MAX_LLM_RETRIES = 2   # initial call + 1 regeneration if de-dupe / guard fails

# ---------------------------------------------------------------------------
# Guardrails — applied in prompt AND as a post-filter
# ---------------------------------------------------------------------------

# Words that violate Mirror Language. Matched case-insensitively as
# whole words. Kept deliberately narrow — we don't want to flag normal
# English like "bright" or "clear".
_BANNED_VOCAB = {
    "energy", "alignment", "flow", "flowing", "projection",
    "vibes", "vibe", "cosmic", "stars", "universe",
    "resonance", "resonate", "manifest", "manifestation",
    "frequency", "frequencies",
    # vague abstractions the user specifically called out
    "muddled", "initiation energy",
}
_BANNED_JARGON = {
    "planet", "planets", "sign", "zodiac", "house", "houses",
    "aspect", "aspects", "transit", "transits",
    "decan", "decans", "retrograde",
    "culmination", "culminate", "ingress", "ingresses",
    "full moon", "new moon", "waxing", "waning", "lunation",
    "ayanamsa", "natal chart", "ascendant",
    "sun sign", "moon sign", "rising sign",
    # body names — the LLM sometimes slips them
    "saturn", "jupiter", "mars", "venus", "mercury",
    "uranus", "neptune", "pluto", "chiron", "lilith",
}
_BANNED_PRESCRIPTIVE = {
    "should", "must ",  # trailing space excludes "must-read", etc.
}
_NUMBER_PATTERN = re.compile(
    r"\b\d+\s*(?:min|minute|minutes|hour|hours|day|days|second|seconds)\b",
    re.IGNORECASE,
)


def _guardrail_violations(text: str) -> List[str]:
    """Return a list of rule violations inside `text`."""
    if not text:
        return []
    t = text.lower()
    hits: List[str] = []
    for w in _BANNED_VOCAB | _BANNED_JARGON:
        # Word-boundary match unless the token itself contains a space
        if " " in w:
            if w in t:
                hits.append(w)
        else:
            if re.search(rf"\b{re.escape(w)}\b", t):
                hits.append(w)
    for w in _BANNED_PRESCRIPTIVE:
        if w in t:
            hits.append(w.strip())
    if _NUMBER_PATTERN.search(text):
        hits.append("numeric-timing")
    return hits


# ---------------------------------------------------------------------------
# De-dupe — token-set overlap (no embeddings, no external deps)
# ---------------------------------------------------------------------------

_STOPWORDS: Set[str] = {
    "the", "a", "an", "to", "of", "and", "or", "but", "is", "it", "in",
    "on", "at", "for", "with", "you", "your", "yours", "that", "this",
    "these", "those", "as", "by", "be", "are", "was", "were", "not",
    "do", "does", "did", "doing", "have", "has", "had", "will", "would",
    "can", "could", "may", "might", "from", "what", "when", "where",
    "why", "how", "about", "into", "just", "too", "very", "more",
    "less", "than", "so", "if", "then", "yet", "still", "even", "also",
}


def _token_set(text: str) -> Set[str]:
    tokens = re.findall(r"[a-z][a-z\-']{2,}", (text or "").lower())
    return {t for t in tokens if t not in _STOPWORDS}


def _overlap_ratio(a: str, b: str) -> float:
    """Jaccard-style overlap of content tokens between two strings."""
    ta, tb = _token_set(a), _token_set(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    smaller = min(len(ta), len(tb))
    return len(inter) / smaller


# ---------------------------------------------------------------------------
# Core Message templates — HOOK / BODY / EDGE
# ---------------------------------------------------------------------------
#
# Two families:
#   SINGLE — when signal_conflict is False. Dominant signal carries the
#            whole day; HOOK / BODY / EDGE stays tight to that one theme.
#   CONFLICT — when signal_conflict is True. HOOK names a pull, BODY
#              names the distortion, EDGE names the lock-in cost.
#
# Every template is already Mirror-voice: tension-based, no vague
# vocabulary. HOOK + BODY + EDGE are joined with a space to form a
# single paragraph.

_SINGLE_CORE = {
    "full_moon": (
        "Something that has been building is reaching a moment where it "
        "can actually be seen. "
        "The temptation is to move on whatever becomes visible, right "
        "now, just to feel like you're responding to it. But visibility "
        "and readiness aren't the same thing — you can see it clearly "
        "before you're clear about what to do. "
        "Acting too early here doesn't resolve what's surfacing — it "
        "closes the window before you've finished looking."
    ),
    "new_moon": (
        "The ground is quieter than it's been. "
        "The pull is to decide, name, commit — to prove the quiet means "
        "something. But the signal here is seeding, not starting; the "
        "things you reach for now may just be ways to break the silence. "
        "Moving too quickly here turns a beginning into a placeholder."
    ),
    "outer_ingress": (
        "Your read of a familiar situation is not going to behave like "
        "it used to. "
        "You'll want to trust your pattern — the way you usually size up "
        "people, pressure, or tone. Some of that pattern is out of date, "
        "and reacting from it will make you feel sure of things you "
        "shouldn't be sure of yet. "
        "Treating today like yesterday is how the miss happens."
    ),
    "heavy_ingress": (
        "Something structural is moving under you that you can't see "
        "directly yet. "
        "The temptation is to make today's decision bigger than it is, "
        "to treat a small choice as if it needs to match the shift. It "
        "doesn't. The shift is not asking you for a plan — it's asking "
        "you to notice the floor changing. "
        "Over-deciding now locks in a response to something you haven't "
        "fully felt yet."
    ),
    "tight_aspect": (
        "A sharp, narrow window is exact today. "
        "A conversation, a message, a decision that normally wouldn't "
        "carry much weight can cut further than usual right now — in "
        "either direction. The pressure is to match the sharpness with "
        "your own, to be decisive just because the moment feels charged. "
        "Reacting to the charge instead of the content is how you end "
        "up owning the wrong cut."
    ),
    "moon_luminary_trigger": (
        "A feeling is coming up faster than usual — louder than what "
        "triggered it. "
        "The pull is to treat the feeling as data and move on it "
        "immediately, to send the message or say the thing while the "
        "pressure is live. It's a real feeling, but it is a short "
        "window. "
        "Turning a passing pulse into a decision is the mistake this "
        "kind of day makes."
    ),
    "moon_sign_change": (
        "The emotional frame you woke up in is not the one you're in now. "
        "You'll keep reading today through yesterday's mood — grading "
        "conversations, responses, and your own reactions through a "
        "filter that's already shifted. That's how you mis-judge what's "
        "actually happening in the room. "
        "Trusting yesterday's temperature today is where the small "
        "misread becomes a real one."
    ),
    "personal_ingress": (
        "The day is about to change register, and you can already feel "
        "the tone shifting. "
        "The pull is to over-prepare for the new phase, to pre-decide "
        "how you're going to show up in it. You don't need to meet the "
        "shift with a plan — it will show you what it wants from you. "
        "Rushing to be ready for it is how you arrive already defended."
    ),
    "strong_aspect": (
        "Your pace is running faster than your certainty, and you can "
        "feel the gap. "
        "The temptation is to close that gap by moving — to replace "
        "the uncomfortable not-yet-clear with the cleaner feeling of "
        "having acted. But the gap is the useful part right now; it's "
        "telling you something that action will cover over. "
        "Using speed to solve uncertainty is today's quiet mistake."
    ),
    "sign_cluster": (
        "Most of today's pull is coming from one direction, and the "
        "weight is real. "
        "You'll want to spread your attention to feel more balanced — "
        "start a second thing, open a second conversation, stay "
        "available across the board. The density is asking you to not "
        "split. "
        "Dispersing the weight is how you waste the focus this day is "
        "actually handing you."
    ),
    "house_cluster": (
        "One part of your life is pulling more of the day than the rest "
        "of it. "
        "The temptation is to balance it out — to rebalance your focus "
        "back toward whatever you've been neglecting. Today isn't a "
        "balance day. The concentration is where the honest meeting is. "
        "Spreading back out is how you miss it entirely."
    ),
}

_CONFLICT_CORE = (
    "You feel pushed to act — but your read of the situation isn't fully "
    "clean. "
    "There's pressure to move, to reply, to settle it, just to relieve "
    "the tension in your body. But part of what you're reacting to isn't "
    "fully accurate. You may be filling gaps, assuming intent, or moving "
    "before the picture is actually clear. "
    "Acting too early here doesn't resolve the situation — it locks you "
    "into it."
)

_CONTINUITY_WRAPPER = (
    "The same window is still open from yesterday — you're one day "
    "deeper inside it now, not looking at a new thing. "
)


def _core_message(
    dominant_type: Optional[str],
    signal_conflict: bool,
    is_continuity: bool,
) -> str:
    if signal_conflict:
        base = _CONFLICT_CORE
    elif dominant_type and dominant_type in _SINGLE_CORE:
        base = _SINGLE_CORE[dominant_type]
    else:
        base = (
            "Today doesn't have a loud headline. The pull is to find one "
            "anyway, to turn an ordinary day into a signal so it feels "
            "more useful. Forcing a verdict out of a neutral day is how "
            "you over-read your own noise."
        )
    if is_continuity:
        return _CONTINUITY_WRAPPER + base
    return base


# ---------------------------------------------------------------------------
# House + domain hints (unchanged)
# ---------------------------------------------------------------------------

def _house_hint_from_signal(signal: Optional[Dict[str, Any]]) -> str:
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
# LLM call — new prompt for sections 2, 3, 4
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are extending an astrology-today daily reflection written in "
    "Mirror Language. A deterministic CORE MESSAGE has already been "
    "produced for the day. Your job is to write three short sections "
    "that follow it:\n\n"
    "  1. HOW IT SHOWS UP — a JSON array of 3-5 bullet strings. Each "
    "     bullet must describe a concrete behaviour a person would "
    "     recognise instantly — something they might literally catch "
    "     themselves doing in the next few hours. Examples of the level "
    "     of specificity required:\n"
    "       - 'Replying to a message before you've actually finished "
    "         reading it.'\n"
    "       - 'Agreeing with something in a meeting just to keep things "
    "         moving.'\n"
    "       - 'Drafting a response three times and still feeling uneasy "
    "         before you send it.'\n"
    "     Each bullet must be a single sentence, 8-20 words, lowercase "
    "     voice. No abstractions. No feelings-as-nouns.\n\n"
    "  2. THE RISK — ONE sharp sentence naming the concrete consequence "
    "     of defaulting to the behaviours above. Not a warning. A "
    "     prediction. Should feel like 'damn, that's exactly what "
    "     happens to me'. Max 24 words.\n\n"
    "  3. THE MOVE — a JSON object with TWO keys:\n"
    "       'action'  — a short framing sentence that opens space. NOT "
    "                   an instruction. No 'should', 'must', 'try to'. "
    "                   No numeric timing (no '30 minutes', 'an hour'). "
    "                   It should feel like a doorway, not a to-do.\n"
    "       'reflect' — a single live question the reader can sit with. "
    "                   Format: 'What feels X here … and what actually "
    "                   needs to be true?' or similar tension-form.\n\n"
    "STYLE RULES (hard)\n"
    "- Second person. Lowercase-voice. No exclamations.\n"
    "- DO NOT mention: planets, signs, houses, aspects, transits, "
    "  decans, degrees, 'moon phase', 'full moon', 'new moon', "
    "  'waxing', 'waning', 'retrograde', 'culmination', 'ingress'.\n"
    "- DO NOT use: 'energy', 'alignment', 'flow', 'projection', "
    "  'vibes', 'cosmic', 'stars', 'universe', 'resonance', 'manifest', "
    "  'frequency', 'muddled'.\n"
    "- DO NOT use any numbered time windows ('30 minutes', 'three "
    "  hours', 'two days').\n"
    "- DO NOT repeat the content of the CORE MESSAGE. Each section must "
    "  introduce NEW information: bullets = behaviours, risk = "
    "  consequence, move = opening.\n"
    "- If CONTINUITY=true, acknowledge you're a day deeper without "
    "  using the word 'continuity'.\n\n"
    "OUTPUT — strict JSON object:\n"
    "  { 'how_it_shows_up': ['…','…','…'], "
    "    'the_risk': '…', "
    "    'the_move': { 'action': '…', 'reflect': '…' } }"
)


async def _call_llm_for_sections(
    dominance: Dict[str, Any],
    core_message: str,
    is_continuity: bool,
) -> Optional[Dict[str, Any]]:
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
    if not EMERGENT_LLM_KEY:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception:
        return None

    dom = dominance.get("dominant_signal") or {}
    conflict = bool(dominance.get("signal_conflict"))
    payload = {
        "continuity":       is_continuity,
        "signal_conflict":  conflict,
        "dominant_type":    dom.get("type"),
        "dominant_label":   dom.get("label"),
        "intensity":        dominance.get("intensity"),
        "house_hint":       _house_hint_from_signal(dom),
        "active_categories": dominance.get("active_categories") or [],
        "core_message_already_written": core_message,
        "secondary_labels": [s.get("label") for s in (dominance.get("secondary_signals") or [])][:3],
    }

    for attempt in range(MAX_LLM_RETRIES):
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"astro_v5b_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}_{attempt}",
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
            user_msg = json.dumps(payload, ensure_ascii=False)
            if attempt > 0:
                user_msg += (
                    "\n\nPrevious attempt had guardrail violations or "
                    "overlapped the CORE MESSAGE. Regenerate strictly "
                    "within the rules. Use concrete behaviours only."
                )
            resp = await asyncio.wait_for(
                chat.send_message(UserMessage(text=user_msg)),
                timeout=LLM_TIMEOUT_SECONDS + 3,
            )
            raw = resp.strip() if isinstance(resp, str) else str(resp).strip()
            if raw.startswith("```"):
                raw = raw.strip("`").strip()
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()
            parsed = json.loads(raw)

            bullets = parsed.get("how_it_shows_up") or []
            risk = parsed.get("the_risk") or ""
            move = parsed.get("the_move") or {}
            if (
                not isinstance(bullets, list) or len(bullets) < 3
                or not isinstance(risk, str) or not risk.strip()
                or not isinstance(move, dict)
                or not move.get("action") or not move.get("reflect")
            ):
                logger.debug("[AstroV5] shape invalid; retrying")
                continue
            bullets = [str(b).strip() for b in bullets if str(b).strip()][:5]

            # Guardrail post-filter
            all_text = " ".join(bullets + [risk, move.get("action", ""), move.get("reflect", "")])
            hits = _guardrail_violations(all_text)
            if hits:
                logger.info("[AstroV5] guardrail hits %s — regen", hits)
                continue

            # De-dupe vs core_message
            overlap = _overlap_ratio(core_message, " ".join(bullets + [risk]))
            if overlap > 0.60:
                logger.info("[AstroV5] overlap %.2f — regen", overlap)
                continue

            return {
                "how_it_shows_up": bullets,
                "the_risk":        risk.strip(),
                "the_move": {
                    "action":  move["action"].strip(),
                    "reflect": move["reflect"].strip(),
                },
            }
        except Exception as e:
            logger.warning("[AstroV5] LLM call failed on attempt %d: %s", attempt, e)
            continue
    return None


# ---------------------------------------------------------------------------
# Deterministic fallback sections (no LLM)
# ---------------------------------------------------------------------------

def _fallback_sections(
    dominance: Dict[str, Any],
) -> Dict[str, Any]:
    dom = dominance.get("dominant_signal") or {}
    conflict = bool(dominance.get("signal_conflict"))

    if conflict:
        bullets = [
            "Replying to something before you've finished understanding it.",
            "Agreeing just to move a conversation forward.",
            "Making a call to relieve your own tension, not because it's clear.",
            "Filling in what you don't know with what you suspect.",
        ]
        risk = (
            "You commit to a version of the situation that turns out to be "
            "mostly your own read — and then have to live inside that read."
        )
    else:
        bullets = [
            "Drafting a response three times and still feeling uneasy.",
            "Reacting to the charge of the moment rather than its content.",
            "Treating a passing feeling as a decision that has to be made.",
        ]
        risk = "The fast move here costs you more than waiting would have."

    return {
        "how_it_shows_up": bullets,
        "the_risk":        risk,
        "the_move": {
            "action":  "Slow the moment down — not to stop it, but to see it more clearly.",
            "reflect": "What feels urgent here … and what actually needs to be true?",
        },
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def build_today_v5_payload(
    user_id: str,
    chart_doc: Optional[Dict[str, Any]],
    prior_day_payload: Optional[Dict[str, Any]] = None,
    dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    dominance = build_dominance_payload(
        user_id, chart_doc, dt=dt, prior_day_payload=prior_day_payload,
    )
    dom_type = (dominance.get("dominant_signal") or {}).get("type")
    signal_conflict = bool(dominance.get("signal_conflict"))

    is_continuity = bool(
        prior_day_payload
        and prior_day_payload.get("signature_hash") == dominance["signature_hash"]
    )

    # Section 1 — deterministic CORE MESSAGE
    core_message = _core_message(dom_type, signal_conflict, is_continuity)

    # Sections 2-4 — LLM with guardrails + regen loop
    sections = await _call_llm_for_sections(dominance, core_message, is_continuity)
    llm_used = sections is not None
    if not sections:
        sections = _fallback_sections(dominance)

    # Assemble markdown body for any downstream consumer that just wants
    # one string (the FE will read the structured `sections` instead).
    bullets_md = "\n".join(f"- {b}" for b in sections["how_it_shows_up"])
    body_md = (
        f"{core_message}\n\n"
        f"How this shows up:\n{bullets_md}\n\n"
        f"The risk:\n{sections['the_risk']}\n\n"
        f"The move:\n"
        f"Action — {sections['the_move']['action']}\n"
        f"Reflect — {sections['the_move']['reflect']}"
    )

    return {
        "user_id":          user_id,
        "date":             (dt or datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
        "timestamp_utc":    dominance["timestamp_utc"],
        "headline":         core_message,
        "body_markdown":    body_md,
        # New structured sections — consumed by the upcoming FE accordion.
        "sections": {
            "core_message":    core_message,
            "how_it_shows_up": sections["how_it_shows_up"],
            "the_risk":        sections["the_risk"],
            "the_move":        sections["the_move"],
        },
        "intensity":            dominance["intensity"],
        "signal_conflict":      signal_conflict,
        "continuity":           is_continuity,
        "why_today_is_different": dominance["why_today_is_different"],
        "dominant_signal":      dominance["dominant_signal"],
        "secondary_signals":    dominance["secondary_signals"],
        "background_signals":   dominance["background_signals"],
        "signature_hash":       dominance["signature_hash"],
        "signature_changed":    dominance["signature_changed"],
        "why_this_is_showing_up": {
            "dominant_signal":      dominance["dominant_signal"],
            "secondary_signals":    dominance["secondary_signals"],
            "background_signals":   dominance["background_signals"],
            "intensity":            dominance["intensity"],
            "signal_conflict":      signal_conflict,
            "active_categories":    dominance.get("active_categories") or [],
            "moon_phase":           dominance["moon_phase"],
            "tight_aspect_count":   dominance["tight_aspect_count"],
            "aspect_count":         dominance["aspect_count"],
        },
        "llm_used":             llm_used,
    }


__all__ = [
    "build_today_v5_payload",
    "_guardrail_violations",
    "_overlap_ratio",
]
