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
EVENT_COLLECTION = "relationship_today_events"
CACHE_TTL_HOURS = 24
ENGINE_VERSION = "between-you-today-v1.1"
LLM_TIMEOUT_SECONDS = 22
LLM_MAX_RETRIES = 2

# Allowed event names — kept whitelisted to keep the telemetry surface
# observable rather than overgrown. New event types must be added here
# explicitly. All events are passive / read-only signals.
EVENT_TYPES = {
    "today_card_viewed",
    "proof_expanded",
    "proof_collapsed",
    "proof_mode_switched",
    "today_card_revisited_same_day",
    "hero_regenerated_same_day",
}

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

# V1.1 — anti-AI-symmetry / generated-prose patterns. Catches "summary-mode"
# phrasings the LLM tends to slip into. Matched as substrings (case-insensitive).
# Top-level prose containing any of these is regenerated or, if that fails,
# replaced with the deterministic embodied seed.
_BANNED_AI_PATTERNS = [
    "you both feel",
    "you both sense",
    "you both experience",
    "drives you both",
    "drive you both",
    "is being assessed",
    "are being assessed",
    "there is a sense of",
    "there's a sense of",
    "there is a feeling of",
    "this may cause",
    "this might cause",
    "this can cause",
    "energy around",
    "energy between",
    "the dynamic of",
    "what this means",
    "invitation to",
    "opportunity for growth",
    "opportunity to grow",
    "growth edges",
    "growth opportunities",
    # over-poetic / mini-essay tells
    "in this moment",
    "at this time",
    "the universe",
    "is opening up",
    "are opening up",
    "open up to",
]


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
    # V1.1 — anti-AI-symmetry / generated-prose substring check
    for pat in _BANNED_AI_PATTERNS:
        if pat in t:
            return False
    # Cap "today" appearances per text block — overuse is the strongest
    # tell of generated prose. Allow at most 2 per single string.
    if t.count("today") > 2:
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
        if isinstance(expires_at, datetime):
            # Mongo returns naive UTC datetimes; normalise so we don't blow up
            # on naive-vs-aware comparison.
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
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
        # Events collection indexes — for revisit-rate / engagement analytics
        await db[EVENT_COLLECTION].create_index("anchor_id")
        await db[EVENT_COLLECTION].create_index("date")
        await db[EVENT_COLLECTION].create_index("event")
    except Exception as e:
        logger.warning(f"[BetweenYouToday] index ensure failed: {e}")


# ---------------------------------------------------------------------------
# Telemetry — passive event log. Read-only signal collection.
# Never blocks the request path. Writes are best-effort.
# ---------------------------------------------------------------------------

async def record_event(
    db,
    *,
    event: str,
    forum_id: str,
    anchor_id: str,
    target_id: str,
    date_str: Optional[str] = None,
    intensity: Optional[str] = None,
    cache_hit: Optional[bool] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Append a single passive telemetry event. Returns True iff persisted.
    Silent on failure — telemetry must never affect the user request.

    Event whitelist enforced via EVENT_TYPES.

    Side effect: when `event == 'today_card_viewed'`, we also detect
    same-day revisits by checking whether a prior 'today_card_viewed'
    exists for (anchor_id, target_id, date_str). If so, we ALSO emit
    a derived 'today_card_revisited_same_day' event.
    """
    if event not in EVENT_TYPES:
        logger.warning(f"[BetweenYouToday] rejected unknown event: {event}")
        return False
    try:
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        doc = {
            "event":      event,
            "forum_id":   forum_id,
            "anchor_id":  anchor_id,
            "target_id":  target_id,
            "date":       date_str,
            "intensity":  intensity,
            "cache_hit":  cache_hit,
            "extra":      extra or {},
            "ts":         datetime.now(timezone.utc),
        }
        await db[EVENT_COLLECTION].insert_one(doc)

        # Derived revisit event — fires on the SECOND view of the same
        # pair on the same day. We treat this as the strongest passive
        # interest signal we can detect without notifications.
        if event == "today_card_viewed":
            prior = await db[EVENT_COLLECTION].count_documents({
                "event":     "today_card_viewed",
                "anchor_id": anchor_id,
                "target_id": target_id,
                "date":      date_str,
            })
            # prior includes the doc we just inserted, so >1 means revisit
            if prior > 1:
                await db[EVENT_COLLECTION].insert_one({
                    **doc,
                    "event": "today_card_revisited_same_day",
                    "extra": {**doc["extra"], "view_count": prior},
                    "ts":    datetime.now(timezone.utc),
                })
        return True
    except Exception as e:
        logger.warning(f"[BetweenYouToday] event write failed ({event}): {e}")
        return False


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
    intensity: str = "medium",
    rotation_seed: int = 0,
) -> List[Dict[str, str]]:
    """
    For each unique transit-driven dimension, decide WHAT it activates
    inside the relationship architecture. Returns a structured list
    that downstream LLM polish can express, but never invent past.

    V1.1 — embodied, relationally specific seed library. Three pools per
    (dimension × already-active-shape): the rotation_seed (= blake2b
    of anchor|target|date) selects one consistently for the day,
    giving day-to-day variety even on the deterministic path.
    """
    summary: List[Dict[str, str]] = []
    seen: set = set()

    def _pick(pool: List[str]) -> str:
        if not pool:
            return ""
        return pool[rotation_seed % len(pool)]

    for a in activations:
        dim = a["dimension"]
        if dim in seen:
            continue
        seen.add(dim)

        # ──────────────────────────────────────────────────────────
        # EMOTIONAL AMPLIFICATION
        # ──────────────────────────────────────────────────────────
        if dim == "emotional_amplification":
            if dimensions["emotional"]:
                pool = [
                    "the emotional door between you is thinner today — closeness, tension, and reactions all register faster than usual",
                    "feelings move more quickly across the space between you today; what would normally take hours to land lands in minutes",
                    "the pair is operating with less emotional buffer today — small things land closer to the bone on both sides",
                ]
            elif dimensions["trust"]:
                pool = [
                    "the unsaid takes up more room today — silences and pauses carry more weight than they normally would",
                    "today the trust between you is more audible; what is and isn't said registers more sharply on both sides",
                    "small moments of withholding land louder today than the words around them",
                ]
            else:
                pool = [
                    "feelings sit closer to the surface today than this connection usually carries — small moments are weighted differently",
                    "today the emotional register between you is one notch louder than the relationship's baseline",
                    "the connection is running with a thinner skin today — minor frictions and warmths both arrive more directly",
                ]
            summary.append({
                "dimension":      "emotional_amplification",
                "modulates":      "emotional_layer" if dimensions["emotional"] else ("trust_layer" if dimensions["trust"] else "tone"),
                "what_it_does":   _pick(pool),
                "evidence_kind":  "lunar/emotional transit",
                "evidence_label": a["label"],
            })

        # ──────────────────────────────────────────────────────────
        # TIMING COMPRESSION
        # ──────────────────────────────────────────────────────────
        elif dim == "timing_compression":
            if dimensions["building"]:
                pool = [
                    "questions about direction, responsibility, or what this connection is actually building become harder to ignore today",
                    "decisions that have been hovering over the pair want to land — abstraction won't hold them today",
                    "the practical conversation you've been delaying gets closer to the surface today; the window for clean coordination is narrow",
                ]
            elif dimensions["momentum"]:
                pool = [
                    "the pull is to act first and process second; the pace between you outruns the room either of you has to feel it through",
                    "the connection is in a hurry today — it wants movement, not interpretation",
                    "today, the urge to do something with this connection is louder than the urge to understand it",
                ]
            else:
                pool = [
                    "small choices between you are heavier than usual today; the pair is making decisions at a pace it can't fully feel yet",
                    "the timing of a single conversation matters more today than the conversation itself does",
                    "decisions that would normally drift quietly between you sharpen up and ask to be answered today",
                ]
            summary.append({
                "dimension":      "timing_compression",
                "modulates":      "building_layer" if dimensions["building"] else ("momentum_layer" if dimensions["momentum"] else "decision_window"),
                "what_it_does":   _pick(pool),
                "evidence_kind":  "tight aspect window",
                "evidence_label": a["label"],
            })

        # ──────────────────────────────────────────────────────────
        # STRUCTURAL SHIFT
        # ──────────────────────────────────────────────────────────
        elif dim == "structural_shift":
            if dimensions["building"]:
                pool = [
                    "what the two of you are building gets weighed against a bigger frame today — yesterday's stable answer might not land the same way",
                    "the ground under what you're building is moving slightly; today is for noticing the shift, not committing to a new shape",
                    "the floor underneath the partnership has changed register — old agreements feel less self-evident today",
                ]
            else:
                pool = [
                    "the floor under this connection is moving in a way neither of you can fully name; today is not the day to make it big",
                    "something underneath this relationship is rearranging; small moves carry more weight than usual",
                    "the baseline this connection sits on is being recalibrated today — the right move is to wait, not to declare",
                ]
            summary.append({
                "dimension":      "structural_shift",
                "modulates":      "building_layer" if dimensions["building"] else "ground_under_pair",
                "what_it_does":   _pick(pool),
                "evidence_kind":  "outer-body movement",
                "evidence_label": a["label"],
            })

        # ──────────────────────────────────────────────────────────
        # TONE SHIFT
        # ──────────────────────────────────────────────────────────
        elif dim == "tone_shift":
            pool = [
                "the register the two of you are speaking in has shifted; yesterday's read of each other is not today's read",
                "the tone between you has rotated since the last time you spoke — old assumptions fit slightly less well",
                "the way you read each other is recalibrating today; the same words may not mean what they did last time",
            ]
            summary.append({
                "dimension":      "tone_shift",
                "modulates":      "register",
                "what_it_does":   _pick(pool),
                "evidence_kind":  "ingress / sign change",
                "evidence_label": a["label"],
            })

    return summary


def _distortion_risks(
    summary: List[Dict[str, str]],
    dimensions: Dict[str, bool],
    intensity: str,
    rotation_seed: int = 0,
) -> List[str]:
    """
    Surface temporary distortion risks specific to today's activations.
    Always relational, never moralising, never deterministic.

    V1.1 — distortion is now the strongest stickiness layer; lean into
    misinterpretation, pacing mismatch, projection, momentum-vs-clarity,
    practical-stress-disguised-as-emotion. Pools rotate by date seed.
    """
    out: List[str] = []
    activated = {s["dimension"] for s in summary}

    def _pick(pool: List[str]) -> str:
        return pool[rotation_seed % len(pool)] if pool else ""

    if "emotional_amplification" in activated:
        if dimensions["attachment_friction"]:
            pool = [
                "an old conversation that one of you thought was settled is more pullable today than usual",
                "the urge to re-open something you'd quietly buried is louder; the temptation will look like 'just clarifying'",
                "what's already unresolved between you is louder today, not quieter — and louder will feel like 'finally talking about it'",
            ]
        elif dimensions["emotional"]:
            pool = [
                "one of you may read a pause as withdrawal that the other meant as space",
                "a small silence is more likely to be filled in with the wrong story today",
                "tone gets misread first today — what's said second is heard before what's said first",
            ]
        else:
            pool = [
                "small reactions can read as bigger statements than they are",
                "a tone-of-voice mismatch lands harder than the words it carried",
                "a casual moment can be over-interpreted before either of you notices it has been",
            ]
        out.append(_pick(pool))

    if "timing_compression" in activated:
        if dimensions["building"]:
            pool = [
                "practical stress can disguise itself as emotional distance — the pair will look further apart than the actual issue is",
                "logistical pressure on one of you may register as relational coolness on the other",
                "what looks like emotional withdrawal today might just be one of you carrying more practical weight than the other can see",
            ]
        elif dimensions["momentum"]:
            pool = [
                "movement outruns processing — the connection may agree to something today that one of you hasn't fully felt through",
                "a fast yes today is more available than a clean yes",
                "the speed of the conversation may outpace the readiness underneath it",
            ]
        else:
            pool = [
                "the urge to decide outruns the readiness to decide",
                "a decision is more available today than clarity is — and one will look like the other",
                "the temptation is to close a question that hasn't actually finished forming",
            ]
        out.append(_pick(pool))

    if "structural_shift" in activated:
        pool = [
            "a small choice between you may be treated as bigger than it is — and what you settle here today might lock in something that should still be moving",
            "today's instinct is to make a clean call; the cleaner call may be to leave the question open another day",
            "neither of you is wrong about what's shifting — but acting on it before it has fully shifted is where the misstep lives",
        ]
        out.append(_pick(pool))

    if "tone_shift" in activated:
        pool = [
            "pattern-matching the old version of each other is where the miss happens today",
            "yesterday's read of each other is the most likely thing to lead you wrong today",
            "you'll be tempted to use last week's framing on this week's conversation; it will not fit cleanly",
        ]
        out.append(_pick(pool))

    # Low-intensity fallbacks — gentle, observational, not warnings
    if not out and intensity == "low":
        low_pool = [
            "the connection isn't asking for anything today — over-interpreting the quiet is the only real risk",
            "nothing in particular is wrong today; the temptation to look for something to fix is itself the distortion",
            "the dynamic is mostly resting today — reading meaning into the quiet is where today goes wrong",
        ]
        out.append(_pick(low_pool))

    return out[:3]


def _softeners(
    summary: List[Dict[str, str]],
    dimensions: Dict[str, bool],
    intensity: str,
    rotation_seed: int = 0,
) -> List[str]:
    """
    Non-prescriptive easing — observations, not coaching.
    V1.1 — no "should" / "must" / "try to". Soft observational register.
    """
    out: List[str] = []
    activated = {s["dimension"] for s in summary}

    def _pick(pool: List[str]) -> str:
        return pool[rotation_seed % len(pool)] if pool else ""

    if "emotional_amplification" in activated:
        pool = [
            "clarity lands better than reassurance today",
            "naming what's actually happening tends to ease the field faster than soothing it does",
            "the field eases when one of you is willing to be the first to be specific",
        ]
        out.append(_pick(pool))

    if "timing_compression" in activated:
        if dimensions["building"]:
            pool = [
                "the field softens when expectations are named early",
                "the pair tends to ease when the practical question gets put on the table cleanly, before it leaks into tone",
                "the friction tends to drop the moment the unspoken decision is named out loud",
            ]
        else:
            pool = [
                "a little more pacing room between you helps today",
                "letting the conversation breathe ends up being faster than rushing the resolution",
                "the field tends to ease when neither of you has to decide anything in the same hour",
            ]
        out.append(_pick(pool))

    if "structural_shift" in activated:
        pool = [
            "this works better as reconnection than resolution",
            "today is more useful for noticing than for deciding",
            "the field eases when neither of you tries to make today's shift mean something final",
        ]
        out.append(_pick(pool))

    if "tone_shift" in activated:
        pool = [
            "humour ends up landing faster than explanation here",
            "a small re-introduction lands cleaner than a long context-set",
            "going slow at the start of the conversation tends to do the recalibration on its own",
        ]
        out.append(_pick(pool))

    if not out:
        if intensity == "low":
            low_pool = [
                "nothing in particular needs handling — the connection is allowed to coast today",
                "today is a logistical day between you more than an emotional one; treating it that way is enough",
                "the connection is running smoothly today; the right move is to not over-attend to it",
            ]
            out.append(_pick(low_pool))
        else:
            mid_pool = [
                "naming what's actually here is enough — nothing needs to be solved",
                "the field doesn't need anything special — it just needs to not be over-managed",
                "today, presence outperforms intervention",
            ]
            out.append(_pick(mid_pool))

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
ALREADY-DETECTED relational signals and renders them as plain English
that a real person would recognise as exactly how today feels between
the two named people.

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
7. Reference the relationship by its real shape (use first names
   when natural) — never "your partner", "your friend".
8. The HERO is 2–3 short sentences, ≤45 words total. Compressed,
   embodied, fast to read, emotionally charged. NOT a mini-essay.
9. Each ACTIVATED / DISTORTION / SOFTENS bullet is ONE short
   sentence. Max ~22 words.
10. Vary phrasing across days using the rotation_seed integer.
    Don't reuse the same sentence opening or verb register that
    yesterday would have used.

CRITICAL — RECOGNITION RULES (V1.1):
The output must feel OBSERVED, not INTERPRETED. The reader should
feel: "that IS what today is between us" — not "interesting
astrology insight".

ANTI-PATTERNS (FORBIDDEN — will be rejected by post-filter):
  • "you both feel" / "you both sense" / "you both experience"
  • "X drives you both" / "drives you both" / "is being assessed"
  • "there is a sense of" / "there's a feeling of"
  • "this may cause" / "this can cause"
  • "energy around" / "energy between" / "the dynamic of"
  • "what this means" / "invitation to" / "opportunity for growth"
  • "in this moment" / "at this time"
  • mirrored sentence symmetry ("X opens, Y opens", "X is louder, Y is louder")
  • the word "today" more than 2 times in any single string
  • therapy-blog / coaching phrases
  • explanatory transitions ("which means…", "so that…", "because of this…")

WORK FROM THESE BAD vs BETTER EXAMPLES:

  BAD:    "Emotions drive you both, opening doors quickly."
            (abstract, generated, mirrored, generic)
  BETTER: "The emotional door between Pete and Mel is thinner today —
           closeness, tension, and reactions all register faster than
           usual."

  BAD:    "What you're building together is being assessed on a larger scale."
            (systemic, abstract, AI-shaped)
  BETTER: "Questions about direction, responsibility, or what this
           connection is actually building become harder to ignore today."

  BAD:    "There is a sense of opportunity for growth between you both."
            (banned vocabulary, summary-mode)
  BETTER: "The pair is operating with less emotional buffer today —
           small things land closer to the bone on both sides."

LOW-INTENSITY DAYS (CRITICAL):
When `intensity == "low"`, the prose MUST feel quieter, more
practical, more observational. NOT muted emotion — actually grounded
everyday register. Examples of correct low-day register:
  • "The connection feels more practical than emotional today."
  • "Most of today between Pete and Mel is logistical — the field
     is running smoothly without needing attention."
  • "Nothing dramatic is pulling at the connection today; it settles
     more into rhythm than intensity."
Do NOT make every day feel intense / transformative / heavy.

OUTPUT FORMAT — strict JSON, no markdown, no commentary:
{
  "hero":               "string (2–3 sentences, ≤45 words total)",
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
    rotation_seed: int = 0,
) -> str:
    """
    V1.1 — embodied, 2–3 sentences, ≤45 words, day-rotated. The
    deterministic hero is the safety net when the LLM polish either
    isn't available or fails the post-filter. It must still feel
    like a real person noticing today, not a generated summary.
    """
    def _pick(pool: List[str]) -> str:
        return pool[rotation_seed % len(pool)] if pool else ""

    if not summary:
        if intensity == "low":
            pool = [
                f"Today is quiet between you and {member_name}. The connection isn't asking for anything in particular — it's running at its baseline.",
                f"Most of today between you and {member_name} is logistical. Nothing is pulling at the field; the dynamic is mostly resting.",
                f"The connection between you and {member_name} feels more practical than emotional today. The field is breathable; nothing is sharpening.",
            ]
            return _pick(pool)
        pool = [
            f"Today moves gently between you and {member_name}. Whatever is alive between you can be carried at its own pace; nothing is forcing.",
            f"The connection between you and {member_name} is steady today — not flat, not loud. Today is for tending, not for deciding.",
        ]
        return _pick(pool)

    first = summary[0]
    dim = first["dimension"]

    if dim == "emotional_amplification":
        pool = [
            f"The emotional door between you and {member_name} is thinner today. Closeness, tension, and small reactions all register faster than usual.",
            f"Feelings move more quickly across the space between you and {member_name} today. What would normally take hours to land lands in minutes.",
            "The pair is operating with less emotional buffer today. Small things land closer to the bone on both sides.",
        ]
        return _pick(pool)

    if dim == "timing_compression":
        pool = [
            f"Questions about direction, responsibility, or what this connection between you and {member_name} is actually building become harder to ignore today.",
            f"Today, the conversation between you and {member_name} wants to land. Decisions that have been hovering won't stay abstract much longer.",
            f"The pace between you and {member_name} is slightly ahead of the room you have to feel things through. Action is more available than clarity.",
        ]
        return _pick(pool)

    if dim == "structural_shift":
        pool = [
            f"The floor under what you and {member_name} have built is moving slightly. Today is for noticing the shift, not committing to a new shape.",
            f"Something underneath the connection between you and {member_name} is rearranging. Old agreements feel less self-evident than they did last week.",
            "The ground this connection sits on is being recalibrated. The right move is to wait, not to declare.",
        ]
        return _pick(pool)

    if dim == "tone_shift":
        pool = [
            f"The register between you and {member_name} has rotated. Yesterday's read of each other is the most likely thing to lead you wrong today.",
            f"The tone between you and {member_name} has shifted since you last spoke. Old assumptions don't fit quite as cleanly.",
            "The way you read each other is recalibrating today. The same words may not mean what they did last time.",
        ]
        return _pick(pool)

    pool = [
        f"Something is moving inside the connection between you and {member_name} today.",
        f"The connection between you and {member_name} is in modulation today — small things carry more weight than usual.",
    ]
    return _pick(pool)


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

        seed = _rotation_seed(anchor_user_id, target_user_id, date_str)

        summary = _activated_dimension_summary(activations, dimensions, intensity, seed)
        distortions = _distortion_risks(summary, dimensions, intensity, seed)
        softeners_out = _softeners(summary, dimensions, intensity, seed)

        field = target_mapping.get("field") or {}
        field_paragraph = field.get("field_paragraph")
        field_activation = field.get("activation")

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
            hero = _deterministic_hero(summary, intensity, member_name, seed)
            activated_today = _deterministic_activated_bullets(summary)
            distortion_risk = distortions
            softens_field = softeners_out

        # Strict guard at the boundary (LLM output already filtered, but
        # deterministic fallbacks pass through too).
        activated_today = _strip_bad_lines(activated_today)
        distortion_risk = _strip_bad_lines(distortion_risk)
        softens_field = _strip_bad_lines(softens_field)
        if not _guard_top_level(hero):
            hero = _deterministic_hero(summary, intensity, member_name, seed)

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
    "record_event",
    "ENGINE_VERSION",
    "EVENT_TYPES",
]
