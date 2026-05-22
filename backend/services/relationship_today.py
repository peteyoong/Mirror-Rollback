"""
Between You Today — Relationship Timing Layer v1
=================================================

Modulation engine that answers:

    "How does THIS relationship behave differently today because of timing?"

This is NOT:
  • a couple horoscope
  • transit spam (A's transits + B's transits)
  • "good day / bad day" framing

This IS:
  • a thin, additive modulation layer that sits ON TOP of the existing
    relationship architecture (relationship_field v1, forum HD mapping,
    today v5 transit dominance, synastry contacts) and surfaces:
        - which already-present relationship mechanics are
          unusually loud today
        - what temporary distortion risks ride on top of them
        - what eases the field
        - a collapsible technical proof layer
  • completely deterministic for signal detection (we never invent
    relationship mechanics — only express ones the underlying
    architecture has already named)
  • LLM-polished for the user-facing prose (rotational phrasing,
    short, emotionally readable, non-repeating day-to-day)

Architectural rules (locked by product):
  1. Compute transit → relationship structure, not transit_A + transit_B.
  2. Hero is the retention hook: 1–3 sentences max.
  3. Distortion risk is critical; never moralise.
  4. Avoid generic emotional repetition; vary phrasing daily via a
     rotation seed = hash(anchor_id || target_id || date).
  5. Practical / building / logistical relationships must surface
     practical days — not every day is emotional.
  6. Top-level prose is plain English; technical proof lives in the
     collapsible drawer only.

Envelope:
    {
      "version": "between-you-today-v1",
      "date":               "YYYY-MM-DD",
      "intensity":          "low" | "medium" | "high",
      "hero":               str,       # 1–3 sentences
      "activated_today":    [str, ...] # 2–4 short bullets
      "distortion_risk":    [str, ...] # 1–3 short bullets
      "softens_field":      [str, ...] # 1–3 short bullets
      "proof_layer": {
          "plain_english":  [str, ...] # readable explanations
          "technical":      [str, ...] # transit names, channels, contacts
      }
    }
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_COLLECTION = "relationship_today_cache"
CACHE_TTL_HOURS = 24
ENGINE_VERSION = "between-you-today-v1.0"
LLM_TIMEOUT_SECONDS = 22
LLM_MAX_RETRIES = 2

# Banned vocabulary at the TOP-LEVEL prose layer (proof_layer.technical may
# contain astrology jargon; everything else must stay plain English).
_BANNED_TOP_LEVEL = {
    "transit", "transits", "retrograde", "aspect", "aspects",
    "conjunction", "opposition", "trine", "square", "sextile",
    "house", "houses", "ingress", "decan",
    "natal chart", "ascendant", "rising sign",
    "soulmate", "twin flame", "destiny", "destined", "fated",
    "karmic", "karma", "compatibility", "compatible", "incompatible",
    "vibes", "vibe", "cosmic", "stars align", "universe",
    "manifest", "manifestation",
}
_BANNED_PRESCRIPTIVE = {"should", "must "}


# Emotional vs practical channel taxonomy — drives dimensional routing
# so we never speak about "emotional opening" on a fundamentally
# practical/building relationship architecture.
_EMOTIONAL_CHANNELS = {"6-59", "39-55", "12-22", "30-41", "13-33", "10-20"}
_BUILDING_CHANNELS = {"21-45", "27-50", "37-40", "5-15", "32-54", "18-58"}
_MOMENTUM_CHANNELS = {"1-8", "35-36", "34-57", "11-56", "4-63", "28-38"}
_TRUST_CHANNELS = {"10-20", "13-33", "5-15", "37-40"}


# ---------------------------------------------------------------------------
# Dimension router — maps detected transit signals onto relationship
# dimensions that the architecture below already names.
# ---------------------------------------------------------------------------

# Maps Today V5 transit dominance "type" labels onto relational dimensions.
# Aligned with the lens-domain assignments used in relationship_field v1.3:
#   - HD = activation (what fires)
#   - Astrology = growth pressure
#   - Enneagram = attachment
#   - BaZi = structure
#   - Numerology = symbolic
_TRANSIT_TYPE_TO_DIMENSION = {
    "full_moon":              "emotional_amplification",
    "new_moon":               "emotional_amplification",
    "moon_luminary_trigger":  "emotional_amplification",
    "moon_sign_change":       "emotional_amplification",
    "tight_aspect":           "timing_compression",
    "outer_ingress":          "structural_shift",
    "heavy_ingress":          "structural_shift",
    "personal_ingress":       "tone_shift",
    "strong_aspect":          "timing_compression",
    "sign_cluster":           "tone_shift",
}


def _safe_lower(x: Any) -> str:
    return str(x).lower() if x is not None else ""


def _guard_top_level(text: str) -> bool:
    """Return True iff text contains zero top-level banned tokens."""
    if not text:
        return True
    t = _safe_lower(text)
    for w in _BANNED_TOP_LEVEL:
        if " " in w:
            if w in t:
                return False
        else:
            if re.search(rf"\b{re.escape(w)}\b", t):
                return False
    for w in _BANNED_PRESCRIPTIVE:
        if w in t:
            return False
    return True


def _strip_bad_lines(items: List[str]) -> List[str]:
    return [s.strip() for s in items if isinstance(s, str) and s.strip() and _guard_top_level(s)]


# ---------------------------------------------------------------------------
# Cache helpers — Mongo (TTL-driven, key = anchor:target:date)
# ---------------------------------------------------------------------------

def _cache_key(anchor_id: str, target_id: str, date_str: str) -> str:
    raw = f"{ENGINE_VERSION}|{anchor_id}|{target_id}|{date_str}"
    return hashlib.blake2b(raw.encode("utf-8"), digest_size=12).hexdigest()


async def _read_cache(db, key: str) -> Optional[Dict[str, Any]]:
    try:
        doc = await db[CACHE_COLLECTION].find_one({"key": key})
        if not doc:
            return None
        expires_at = doc.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at < datetime.now(timezone.utc):
            return None
        return doc.get("payload")
    except Exception as e:
        logger.warning(f"[BetweenYouToday] cache read failed: {e}")
        return None


async def _write_cache(db, key: str, payload: Dict[str, Any]) -> None:
    try:
        now = datetime.now(timezone.utc)
        await db[CACHE_COLLECTION].update_one(
            {"key": key},
            {"$set": {
                "key": key,
                "payload": payload,
                "created_at": now,
                "expires_at": now + timedelta(hours=CACHE_TTL_HOURS),
            }},
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"[BetweenYouToday] cache write failed: {e}")


async def ensure_cache_indexes(db) -> None:
    """Ensure unique key index + TTL index. Safe to call repeatedly."""
    try:
        await db[CACHE_COLLECTION].create_index("key", unique=True)
        await db[CACHE_COLLECTION].create_index(
            "expires_at", expireAfterSeconds=0
        )
    except Exception as e:
        logger.warning(f"[BetweenYouToday] index ensure failed: {e}")


# ---------------------------------------------------------------------------
# Deterministic signal detection — the spine of the engine.
# ---------------------------------------------------------------------------

def _extract_channel_ids(mapping: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(mapping, dict):
        return []
    out: List[str] = []
    hd_signals = ((mapping.get("signals") or {}).get("human_design")) or []
    for ch in hd_signals:
        cid = (ch or {}).get("channel")
        if isinstance(cid, str) and cid:
            out.append(cid)
    return out


def _dominant_lens_dimensions(mapping: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Return which relationship dimensions are *already strongly present* in
    this pair's architecture, based on the existing relationship field.

    This is what makes us a modulation engine: today doesn't introduce
    new mechanics, it amplifies (or eases) the ones already living here.
    """
    channels = set(_extract_channel_ids(mapping))
    has_emotional = bool(channels & _EMOTIONAL_CHANNELS)
    has_building  = bool(channels & _BUILDING_CHANNELS)
    has_momentum  = bool(channels & _MOMENTUM_CHANNELS)
    has_trust     = bool(channels & _TRUST_CHANNELS)

    # Astrology presence (attraction or tension already named in field)
    astro = ((mapping or {}).get("signals") or {}).get("astrology") or {}
    has_astro_attraction = bool(astro.get("attraction"))
    has_astro_tension    = bool(astro.get("tension"))
    has_astro_growth     = bool(astro.get("growth"))

    # Enneagram attachment friction (this is the "attachment" dimension
    # owner in v1.3 layered convergence)
    enne = ((mapping or {}).get("signals") or {}).get("enneagram") or {}
    has_attach_friction = bool(enne.get("friction_pattern"))

    return {
        "emotional":            has_emotional,
        "building":             has_building,
        "momentum":             has_momentum,
        "trust":                has_trust,
        "astro_attraction":     has_astro_attraction,
        "astro_tension":        has_astro_tension,
        "astro_growth":         has_astro_growth,
        "attachment_friction":  has_attach_friction,
    }


def _detect_transit_activations(
    dominance_a: Dict[str, Any],
    dominance_b: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Translate per-user transit dominance into relational dimension events.

    We deliberately do NOT add A's transits to B's transits. Instead we
    look at each user's dominant signals and ask: which already-existing
    relational dimension does this *modulate*?
    """
    activations: List[Dict[str, Any]] = []

    def _harvest(dom: Dict[str, Any], side: str) -> None:
        if not isinstance(dom, dict):
            return
        dom_sig = dom.get("dominant_signal") or {}
        seconds = dom.get("secondary_signals") or []
        for sig in [dom_sig] + (seconds[:2] if isinstance(seconds, list) else []):
            t = (sig or {}).get("type")
            label = (sig or {}).get("label") or ""
            dim = _TRANSIT_TYPE_TO_DIMENSION.get(t)
            if not dim:
                continue
            activations.append({
                "side":     side,
                "type":     t,
                "label":    label,
                "dimension": dim,
                "weight":    sig.get("weight") or sig.get("intensity") or 1,
            })

    _harvest(dominance_a, "anchor")
    _harvest(dominance_b, "target")
    return activations


def _compute_intensity(
    activations: List[Dict[str, Any]],
    dominance_a: Dict[str, Any],
    dominance_b: Dict[str, Any],
) -> str:
    """LOW / MEDIUM / HIGH based on activation count + transit intensity + conflict."""
    score = 0
    if len(activations) >= 4:
        score += 2
    elif len(activations) >= 2:
        score += 1

    for dom in (dominance_a, dominance_b):
        if not isinstance(dom, dict):
            continue
        tight = dom.get("tight_aspect_count") or 0
        if tight >= 2:
            score += 1
        intensity = _safe_lower(dom.get("intensity"))
        if intensity == "high":
            score += 2
        elif intensity == "medium":
            score += 1
        if dom.get("signal_conflict"):
            score += 1

    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _activated_dimension_summary(
    activations: List[Dict[str, Any]],
    dimensions: Dict[str, bool],
) -> List[Dict[str, str]]:
    """
    For each unique transit-driven dimension, decide WHAT it activates
    inside the relationship architecture. Returns a structured list
    that downstream LLM polish can express, but never invent past.
    """
    summary: List[Dict[str, str]] = []
    seen: set = set()
    for a in activations:
        dim = a["dimension"]
        if dim in seen:
            continue
        seen.add(dim)

        # Map onto already-active relationship dimensions
        if dim == "emotional_amplification":
            if dimensions["emotional"]:
                summary.append({
                    "dimension":       "emotional_amplification",
                    "modulates":       "emotional_layer",
                    "what_it_does":    "the emotional permeability already present between you is unusually open today — closeness comes easier, but reactions also land more strongly",
                    "evidence_kind":   "lunar/emotional transit",
                    "evidence_label":  a["label"],
                })
            elif dimensions["trust"]:
                summary.append({
                    "dimension":       "emotional_amplification",
                    "modulates":       "trust_layer",
                    "what_it_does":    "the thin layer of trust you usually move through gets felt more directly today — what's unsaid takes up more space than usual",
                    "evidence_kind":   "lunar/emotional transit",
                    "evidence_label":  a["label"],
                })
            else:
                summary.append({
                    "dimension":       "emotional_amplification",
                    "modulates":       "tone",
                    "what_it_does":    "feelings move closer to the surface today than this connection usually carries — small moments are weighted differently",
                    "evidence_kind":   "lunar/emotional transit",
                    "evidence_label":  a["label"],
                })

        elif dim == "timing_compression":
            if dimensions["momentum"]:
                summary.append({
                    "dimension":       "timing_compression",
                    "modulates":       "momentum_layer",
                    "what_it_does":    "momentum outruns clarity today — the connection wants movement before both people fully understand what they feel",
                    "evidence_kind":   "tight aspect window",
                    "evidence_label":  a["label"],
                })
            elif dimensions["building"]:
                summary.append({
                    "dimension":       "timing_compression",
                    "modulates":       "building_layer",
                    "what_it_does":    "the connection moves toward building and coordination today — decisions won't stay abstract for long",
                    "evidence_kind":   "tight aspect window",
                    "evidence_label":  a["label"],
                })
            else:
                summary.append({
                    "dimension":       "timing_compression",
                    "modulates":       "decision_window",
                    "what_it_does":    "a narrow timing window is alive between you today — small choices land heavier than they normally would",
                    "evidence_kind":   "tight aspect window",
                    "evidence_label":  a["label"],
                })

        elif dim == "structural_shift":
            if dimensions["building"]:
                summary.append({
                    "dimension":       "structural_shift",
                    "modulates":       "building_layer",
                    "what_it_does":    "what you're building together gets read against a different floor today — what felt stable yesterday is being weighed against something larger",
                    "evidence_kind":   "outer-body movement",
                    "evidence_label":  a["label"],
                })
            else:
                summary.append({
                    "dimension":       "structural_shift",
                    "modulates":       "ground_under_pair",
                    "what_it_does":    "the floor under this connection is moving in a way neither of you can name yet — today is not the day to make it big",
                    "evidence_kind":   "outer-body movement",
                    "evidence_label":  a["label"],
                })

        elif dim == "tone_shift":
            summary.append({
                "dimension":       "tone_shift",
                "modulates":       "register",
                "what_it_does":    "the register this connection runs in is shifting under you — yesterday's tone is not today's tone",
                "evidence_kind":   "ingress / sign change",
                "evidence_label":  a["label"],
            })

    return summary


def _distortion_risks(
    summary: List[Dict[str, str]],
    dimensions: Dict[str, bool],
    intensity: str,
) -> List[str]:
    """
    Surface temporary distortion risks specific to today's activations.
    Always relational, never moralising, never deterministic.
    """
    out: List[str] = []
    activated = {s["dimension"] for s in summary}

    if "emotional_amplification" in activated:
        if dimensions["attachment_friction"]:
            out.append(
                "Today amplifies what's already unresolved between you instead of hiding it — the urge to revisit an old conversation is stronger than usual."
            )
        elif dimensions["emotional"]:
            out.append(
                "One of you may interpret silence more personally than usual."
            )
        else:
            out.append(
                "Small reactions can be read as bigger statements than they are."
            )

    if "timing_compression" in activated:
        if dimensions["building"]:
            out.append(
                "Practical stress can disguise itself as emotional distance today."
            )
        elif dimensions["momentum"]:
            out.append(
                "The connection may move faster than emotional processing can keep up with."
            )
        else:
            out.append(
                "The urge to decide outruns the readiness to decide."
            )

    if "structural_shift" in activated:
        out.append(
            "A small choice between you may be treated as bigger than it actually is."
        )

    if "tone_shift" in activated:
        out.append(
            "Yesterday's read of each other is not today's read — pattern-matching the old version is where the miss happens."
        )

    # Intensity-aware fallbacks if nothing fired (low days deserve honesty too)
    if not out and intensity == "low":
        out.append(
            "Today is quieter between you than usual — nothing is asking to be solved."
        )
    return out[:3]


def _softeners(
    summary: List[Dict[str, str]],
    dimensions: Dict[str, bool],
    intensity: str,
) -> List[str]:
    """Non-prescriptive easing — observations, not coaching."""
    out: List[str] = []
    activated = {s["dimension"] for s in summary}

    if "emotional_amplification" in activated:
        out.append("Clarity matters more than reassurance today.")
    if "timing_compression" in activated:
        if dimensions["building"]:
            out.append("The field softens when expectations are named early.")
        else:
            out.append("Giving each other a little more pacing room helps today.")
    if "structural_shift" in activated:
        out.append("This works better as reconnection than resolution.")
    if "tone_shift" in activated:
        out.append("Humour breaks tension faster than explanation right now.")

    if not out:
        if intensity == "low":
            out.append("Nothing in particular needs handling — the connection is allowed to rest today.")
        else:
            out.append("Naming what's actually here is enough — nothing needs to be fixed.")

    return out[:3]


def _proof_layer(
    summary: List[Dict[str, str]],
    dominance_a: Dict[str, Any],
    dominance_b: Dict[str, Any],
    mapping: Optional[Dict[str, Any]],
    current_user_name: str,
    member_name: str,
) -> Dict[str, List[str]]:
    """Plain + technical proof. Plain is reader-friendly; technical can name signals."""
    plain: List[str] = []
    technical: List[str] = []

    for s in summary:
        plain.append(
            f"{s['what_it_does'].capitalize()}."
        )
        technical.append(
            f"{s['evidence_kind']}: {s['evidence_label']} → activates {s['modulates'].replace('_', ' ')}"
        )

    # Add channel-name proof (which existing relationship channel is in play)
    channels = _extract_channel_ids(mapping)
    if channels:
        plain.append(
            f"Why this lands on you specifically: the channels already alive between you ({', '.join(channels[:3])}) are exactly the ones today is leaning on."
        )
        technical.append(
            f"Activated HD channels: {', '.join(channels[:5])}"
        )

    # Strip empties
    plain = [p for p in plain if p]
    technical = [t for t in technical if t]
    return {"plain_english": plain, "technical": technical}


# ---------------------------------------------------------------------------
# LLM polish (hybrid). Deterministic detection owns WHAT is activated;
# LLM only owns HOW it is expressed.
# ---------------------------------------------------------------------------

_LLM_SYSTEM_PROMPT = """You are the BETWEEN YOU TODAY narrator inside an emotionally-intelligent reflection app.

You are NOT an astrologer. You are NOT a couple's horoscope writer.
You are a relational modulation narrator who takes a SET OF
ALREADY-DETECTED relational signals and renders them as plain English.

ABSOLUTE RULES:
1. Do NOT invent new relationship mechanics. Only express the
   signals provided in the JSON payload. If a dimension is not in
   the payload, do not allude to it.
2. NO astrology jargon at the top level (no planet names, transit
   names, signs, houses, aspects, retrograde, lunation language).
3. NO predictions. Never say "you will fight", "you will reconnect",
   "today will be hard". Speak in *modulation*: what is louder /
   thinner / faster / quieter inside this connection today.
4. NO advice. NO "should", "must", "try to", "remember to".
5. NO soulmate / fate / compatibility / karmic / cosmic vocabulary.
6. NO numeric timing ("for 20 minutes", "in 3 hours").
7. Keep the HERO to 1–3 short sentences. It is the retention hook.
   It must read in under 5 seconds.
8. Keep each ACTIVATED bullet to one sentence. Lead with what is
   moving, not why.
9. Keep each DISTORTION RISK bullet to one sentence. State the
   temporary distortion, not the diagnosis.
10. Keep each SOFTENS bullet to one sentence. Observational, not
    prescriptive.
11. Vary phrasing across days. The payload includes a rotation_seed
    integer — use it to favour a different sentence opening / verb
    register than yesterday would have produced.
12. Reference the relationship by its real shape (use first names
    when natural) — never "your partner", "your friend".

OUTPUT FORMAT — strict JSON, no markdown, no commentary:
{
  "hero":               "string (1–3 sentences)",
  "activated_today":    ["string", ...],
  "distortion_risk":    ["string", ...],
  "softens_field":      ["string", ...]
}

If any payload list is empty, emit an empty list in the response —
NEVER fabricate to fill space.
"""


def _rotation_seed(anchor_id: str, target_id: str, date_str: str) -> int:
    raw = f"{anchor_id}|{target_id}|{date_str}".encode("utf-8")
    return int(hashlib.blake2b(raw, digest_size=4).hexdigest(), 16)


async def _llm_polish(
    *,
    summary: List[Dict[str, str]],
    distortions: List[str],
    softeners: List[str],
    intensity: str,
    dimensions: Dict[str, bool],
    current_user_name: str,
    member_name: str,
    rotation_seed: int,
    field_paragraph: Optional[str],
    field_activation: Optional[str],
    emergent_llm_key: Optional[str],
) -> Optional[Dict[str, Any]]:
    key = emergent_llm_key or os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        logger.warning(f"[BetweenYouToday] emergentintegrations import failed: {e}")
        return None

    payload = {
        "anchor_name":   current_user_name,
        "target_name":   member_name,
        "intensity":     intensity,
        "rotation_seed": rotation_seed,
        "relationship_dimensions_present": dimensions,
        "field_context": {
            "field_paragraph": field_paragraph or "",
            "field_activation": field_activation or "",
        },
        "detected_today": [
            {
                "dimension":     s["dimension"],
                "modulates":     s["modulates"],
                "what_it_does":  s["what_it_does"],
            } for s in summary
        ],
        "distortion_seeds": distortions,
        "softener_seeds":   softeners,
    }

    for attempt in range(LLM_MAX_RETRIES):
        try:
            chat = LlmChat(
                api_key=key,
                session_id=f"between_you_today_{rotation_seed}_{attempt}",
                system_message=_LLM_SYSTEM_PROMPT,
            )
            chat.with_model("openai", os.environ.get("OPENAI_PRIMARY_MODEL", "gpt-4o"))
            try:
                chat.with_params(timeout=LLM_TIMEOUT_SECONDS, num_retries=0)
            except Exception:
                pass

            user_msg = json.dumps(payload, ensure_ascii=False)
            if attempt > 0:
                user_msg += (
                    "\n\nPrevious attempt violated the rules (astrology jargon, "
                    "prescriptive language, or invented mechanics). Regenerate "
                    "strictly within the rules. Plain English only at the top level."
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

            hero = (parsed.get("hero") or "").strip()
            activated = parsed.get("activated_today") or []
            distortion_out = parsed.get("distortion_risk") or []
            softens_out = parsed.get("softens_field") or []

            if not isinstance(hero, str) or not hero:
                logger.info("[BetweenYouToday] LLM polish missing hero — retry")
                continue
            if not _guard_top_level(hero):
                logger.info("[BetweenYouToday] hero failed guard — retry")
                continue

            activated = _strip_bad_lines(activated)
            distortion_out = _strip_bad_lines(distortion_out)
            softens_out = _strip_bad_lines(softens_out)

            return {
                "hero": hero,
                "activated_today": activated,
                "distortion_risk": distortion_out,
                "softens_field": softens_out,
            }

        except Exception as e:
            logger.warning(f"[BetweenYouToday] LLM polish failed attempt {attempt}: {e}")
            continue

    return None


# ---------------------------------------------------------------------------
# Deterministic fallback prose — used when LLM key absent or call fails.
# ---------------------------------------------------------------------------

def _deterministic_hero(
    summary: List[Dict[str, str]],
    intensity: str,
    member_name: str,
) -> str:
    if not summary:
        if intensity == "low":
            return (
                "Today is quiet between you. Nothing in particular is "
                "asking to be moved — the connection is allowed to rest."
            )
        return (
            "Today moves gently between you. Whatever is alive between "
            "you can be carried at its own pace."
        )

    first = summary[0]
    dim = first["dimension"]
    if dim == "emotional_amplification":
        return (
            f"The emotional door is thinner between you and {member_name} today. "
            f"Closeness lands faster, and so does the rest of it."
        )
    if dim == "timing_compression":
        return (
            f"Today favours movement over abstraction between you and {member_name}. "
            f"Decisions won't stay theoretical for long."
        )
    if dim == "structural_shift":
        return (
            "The floor under this connection is moving. Today is not the day to make "
            "it big — it's the day to notice what's shifting."
        )
    if dim == "tone_shift":
        return (
            f"The register between you and {member_name} is shifting today. "
            f"Yesterday's read of each other is not today's read."
        )
    return (
        f"Something is moving inside the connection between you and {member_name} today."
    )


def _deterministic_activated_bullets(
    summary: List[Dict[str, str]],
) -> List[str]:
    out: List[str] = []
    for s in summary:
        out.append(s["what_it_does"].capitalize() + ".")
    return out[:4]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def build_between_you_today(
    *,
    db,
    forum_id: str,
    anchor_user_id: str,
    target_user_id: str,
    date: Optional[datetime] = None,
    emergent_llm_key: Optional[str] = None,
    force_refresh: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Build the "Between You Today" envelope for an anchor↔target pair on
    a given date. Reads the existing relationship architecture from
    services.forum_hd_mapping (we do not recompute it) and modulates it
    against today's transit dominance for each side.

    Returns the envelope dict (see module docstring) or None if the pair
    cannot be resolved.
    """
    try:
        dt = date or datetime.now(timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        key = _cache_key(anchor_user_id, target_user_id, date_str)

        if not force_refresh:
            cached = await _read_cache(db, key)
            if cached:
                cached["_cache_hit"] = True
                return cached

        # Resolve charts + the existing mapping for this pair
        from bson import ObjectId
        from services.forum_hd_mapping import get_forum_member_mappings

        mappings = await get_forum_member_mappings(
            db=db,
            forum_id=forum_id,
            current_user_id=anchor_user_id,
        )
        target_mapping = None
        for m in mappings:
            if str(m.get("member_id")) == str(target_user_id):
                target_mapping = m
                break

        if not target_mapping:
            logger.info(
                f"[BetweenYouToday] no mapping found for "
                f"{anchor_user_id[:8]}↔{target_user_id[:8]} in forum {forum_id}"
            )
            return None

        # Pull both users + charts for transit dominance
        anchor_user = None
        try:
            anchor_user = await db.users.find_one({"_id": ObjectId(anchor_user_id)})
        except Exception:
            pass
        if not anchor_user:
            anchor_user = await db.users.find_one({"_id": anchor_user_id})

        target_user = None
        try:
            target_user = await db.users.find_one({"_id": ObjectId(target_user_id)})
        except Exception:
            pass
        if not target_user:
            target_user = await db.users.find_one({"_id": target_user_id})

        anchor_chart = (
            await db.charts.find_one({"user_id": str(anchor_user_id)})
            or await db.charts.find_one({"user_id": anchor_user_id})
        )
        target_chart = (
            await db.charts.find_one({"user_id": str(target_user_id)})
            or await db.charts.find_one({"user_id": target_user_id})
        )

        current_user_name = (anchor_user or {}).get("name") or "You"
        member_name = target_mapping.get("member_name") or (target_user or {}).get("name") or "Them"

        # Transit dominance for both sides
        from services.transit_dominance_engine import build_dominance_payload
        dominance_a = build_dominance_payload(anchor_user_id, anchor_chart, dt=dt)
        dominance_b = build_dominance_payload(target_user_id, target_chart, dt=dt)

        dimensions = _dominant_lens_dimensions(target_mapping)
        activations = _detect_transit_activations(dominance_a, dominance_b)
        intensity = _compute_intensity(activations, dominance_a, dominance_b)
        summary = _activated_dimension_summary(activations, dimensions)
        distortions = _distortion_risks(summary, dimensions, intensity)
        softeners_out = _softeners(summary, dimensions, intensity)

        field = target_mapping.get("field") or {}
        field_paragraph = field.get("field_paragraph")
        field_activation = field.get("activation")

        seed = _rotation_seed(anchor_user_id, target_user_id, date_str)

        # Hybrid LLM polish
        polished = await _llm_polish(
            summary=summary,
            distortions=distortions,
            softeners=softeners_out,
            intensity=intensity,
            dimensions=dimensions,
            current_user_name=current_user_name,
            member_name=member_name,
            rotation_seed=seed,
            field_paragraph=field_paragraph,
            field_activation=field_activation,
            emergent_llm_key=emergent_llm_key,
        )

        if polished:
            hero = polished["hero"]
            activated_today = polished["activated_today"] or _deterministic_activated_bullets(summary)
            distortion_risk = polished["distortion_risk"] or distortions
            softens_field = polished["softens_field"] or softeners_out
        else:
            hero = _deterministic_hero(summary, intensity, member_name)
            activated_today = _deterministic_activated_bullets(summary)
            distortion_risk = distortions
            softens_field = softeners_out

        # Strict guard at the boundary (LLM output already filtered, but
        # deterministic fallbacks pass through too).
        activated_today = _strip_bad_lines(activated_today)
        distortion_risk = _strip_bad_lines(distortion_risk)
        softens_field = _strip_bad_lines(softens_field)
        if not _guard_top_level(hero):
            hero = _deterministic_hero(summary, intensity, member_name)

        proof = _proof_layer(
            summary, dominance_a, dominance_b, target_mapping,
            current_user_name, member_name,
        )

        envelope = {
            "version":           "between-you-today-v1",
            "engine_version":    ENGINE_VERSION,
            "date":              date_str,
            "intensity":         intensity,
            "hero":              hero,
            "activated_today":   activated_today,
            "distortion_risk":   distortion_risk,
            "softens_field":     softens_field,
            "proof_layer":       proof,
            "_meta": {
                "anchor_name":  current_user_name,
                "target_name":  member_name,
                "dimensions":   dimensions,
                "activation_count": len(activations),
                "llm_polished": polished is not None,
            },
        }

        await _write_cache(db, key, envelope)
        envelope["_cache_hit"] = False
        return envelope

    except Exception as exc:
        logger.error(
            f"[BetweenYouToday] build failed for "
            f"{anchor_user_id}↔{target_user_id}: {type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return None


__all__ = [
    "build_between_you_today",
    "ensure_cache_indexes",
    "ENGINE_VERSION",
]
