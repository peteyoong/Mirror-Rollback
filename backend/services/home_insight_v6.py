"""
Home Insight V6 — Today-Powered, Signal-First, Non-Generic
==========================================================

Purpose
-------
Anchor the Home tab on the Astrology Today V5 dominant signal, but
present it from a *zoomed-out* angle rather than as a duplicate of
Today.  Home is the user's "this is the most important thing happening
in your life right now" headline; Today is the moment-level read.

Design contract (per Mirror brief):

    SECTION 1 — THE CALL       (1-2 line hook + tension line)
    SECTION 2 — THE REALITY    (short paragraph; pressure + incomplete info)
    SECTION 3 — WHERE THIS LANDS (real-life translation of house activations)
    SECTION 4 — THE EDGE       (the move; non-prescriptive, slightly confronting)
    SECTION 5 — CTA            ("→ See what's driving this today")

Critical rules
--------------
- Tension framing, no jargon, no "energy"/"alignment" abstractions.
- Behavior-grounded, slightly confronting, but not harsh.
- MUST differ meaningfully from Today's narrative — Same truth, different
  angle.
- MUST change day-to-day. We use the V5 `signature_hash` + a stored
  rotation index per (user, hash) to vary the entry angle when the
  same hash repeats.

Source of truth
---------------
V5 Today payload (`/api/astrology/today-v5/{user_id}`):
  - `dominant_signal` (Tier 1)
  - `signal_conflict` (bool)
  - `sections.core_message`   (Today narrative — DO NOT echo verbatim)
  - `why_this_is_showing_up`  (proof; secondary/background signals)
  - `house_activations`       (transit→natal house counts)

Future hooks (NOT IMPLEMENTED YET — keep extension points clean):
  - Pattern Memory (lifeline echoes)
  - Relationship context
  - HD timing overlay
  - BaZi reinforcement
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# House → real-life translation (no jargon)
# ---------------------------------------------------------------------------
# Plain-language label for each natal house. Used to translate the
# transit→house clusters into "where this lands" copy that doesn't
# require any astrology knowledge.

HOUSE_ARENA: Dict[int, str] = {
    1:  "How you show up — your energy and presence",
    2:  "Money, resources, self-worth",
    3:  "Communication and decisions",
    4:  "Home and your personal environment",
    5:  "Creative expression, play, romance",
    6:  "Daily routine, work, health",
    7:  "One-on-one relationships",
    8:  "Shared resources, intimacy, what you can't control",
    9:  "Beliefs and the bigger picture",
    10: "Career, public role, reputation",
    11: "Friendships, community, future plans",
    12: "Solitude, the unconscious, what's ending",
}


# ---------------------------------------------------------------------------
# Variation: angle rotation when signature_hash hasn't changed
# ---------------------------------------------------------------------------
# When the V5 sky-state signature is identical to the previous day, we
# rotate the *angle* (entry vector) so the same underlying signal
# produces a fresh-feeling Home read instead of repeating.

ANGLES = ("call", "reality", "edge")


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

async def build_home_v6_payload(
    db,
    user_id: str,
) -> Dict[str, Any]:
    """Build the Home V6 payload for a user.

    Reads (or generates) the V5 Today payload, applies angle rotation
    if the signature_hash has not changed since the last Home V6 read,
    and produces the 5-section Home contract.
    """
    # 1) Fetch V5 today payload (use cached if generated within last 6h)
    from services.astrology_today_v5 import build_today_v5_payload

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cached = await db.daily_astrology.find_one(
        {"user_id": user_id, "date": today_str},
    )
    v5: Dict[str, Any]
    if cached and cached.get("generated_at"):
        ga = cached["generated_at"]
        if isinstance(ga, datetime) and ga.tzinfo is None:
            ga = ga.replace(tzinfo=timezone.utc)
        try:
            age = (
                datetime.now(timezone.utc) - ga
            ).total_seconds() if isinstance(ga, datetime) else 9999
        except Exception:
            age = 9999
        if age < 6 * 3600:
            v5 = {k: v for k, v in cached.items() if k != "_id"}
        else:
            v5 = await _generate_fresh_v5(db, user_id)
    else:
        v5 = await _generate_fresh_v5(db, user_id)

    sig_hash = v5.get("signature_hash") or "no_hash"

    # 2) Pull house activations either from the cached debug payload or
    #    compute fresh.
    house_acts = await _resolve_house_activations(db, user_id, v5)

    # 3) Determine angle (rotate when same hash repeats)
    angle = await _pick_angle(db, user_id, sig_hash)

    # 4) Build the 5-section payload via LLM
    sections = await _llm_build_sections(
        v5=v5,
        house_acts=house_acts,
        angle=angle,
    )

    # 5) Cache + return
    payload = {
        "version":             "v6.1",
        "user_id":             user_id,
        "date":                today_str,
        "signature_hash":      sig_hash,
        "angle":               angle,
        "today_signal":        _summarise_today_signal(v5),
        "the_call":            sections["the_call"],
        "the_reality":         sections["the_reality"],
        "where_this_lands":    sections["where_this_lands"],
        "the_edge":            sections["the_edge"],
        "cta":                 sections["cta"],
        "proof": {
            "dominant_signal": (v5.get("dominant_signal") or {}).get("label"),
            "intensity":       v5.get("intensity"),
            "signal_conflict": bool(v5.get("signal_conflict")),
            "house_clusters":  house_acts.get("clusters", []),
        },
        # Pattern Memory layer (v6.1) — only renders on the frontend when
        # `available` is True AND `confidence == "high"`. Fully optional.
        "pattern_memory":      await _resolve_pattern_memory(db, user_id, v5),
        # Future hooks — explicitly empty placeholders so the contract is
        # stable when later layers light up.
        "future_layers": {
            "relationship":        None,
            "human_design_timing": None,
            "bazi":                None,
        },
        "generated_at":        datetime.now(timezone.utc).isoformat(),
        "success":             True,
    }

    # Persist last-used angle so the next request rotates correctly.
    try:
        await db.home_v6_state.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id":             user_id,
                    "last_signature_hash": sig_hash,
                    "last_angle":          angle,
                    "updated_at":          datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )
    except Exception as e:
        logger.warning("[HomeV6] state upsert failed: %s", e)

    return payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _generate_fresh_v5(db, user_id: str) -> Dict[str, Any]:
    from services.astrology_today_v5 import build_today_v5_payload

    chart = await db.charts.find_one({"user_id": user_id})
    return await build_today_v5_payload(
        user_id=user_id, chart_doc=chart, prior_day_payload=None,
    )


async def _resolve_house_activations(
    db, user_id: str, v5: Dict[str, Any],
) -> Dict[str, Any]:
    """Use the same compute as the v5 engine, against the cached chart."""
    try:
        from services.transit_dominance_engine import (
            get_sky_state, compute_house_activations,
        )
        chart = await db.charts.find_one({"user_id": user_id})
        sky = v5.get("sky") or get_sky_state()
        return compute_house_activations(sky, chart)
    except Exception as e:
        logger.warning("[HomeV6] house_activations fallback: %s", e)
        return {"by_house": {}, "clusters": []}


async def _pick_angle(db, user_id: str, sig_hash: str) -> str:
    """Pick an angle (call|reality|edge).

    First time we see this hash for this user → "call".
    Subsequent reads with the same hash rotate through the angles in
    the ANGLES tuple, anchoring on a different section so the Home
    text reframes the same underlying signal instead of repeating.
    """
    try:
        prev = await db.home_v6_state.find_one({"user_id": user_id})
    except Exception:
        prev = None

    if not prev or prev.get("last_signature_hash") != sig_hash:
        return ANGLES[0]

    last = prev.get("last_angle") or ANGLES[0]
    try:
        idx = ANGLES.index(last)
    except ValueError:
        idx = -1
    return ANGLES[(idx + 1) % len(ANGLES)]


def _summarise_today_signal(v5: Dict[str, Any]) -> Dict[str, Any]:
    ds = v5.get("dominant_signal") or {}
    return {
        "label":       ds.get("label"),
        "type":        ds.get("type"),
        "intensity":   v5.get("intensity"),
        "conflict":    bool(v5.get("signal_conflict")),
    }


def _format_house_arena_lines(house_acts: Dict[str, Any]) -> List[str]:
    """Translate the strongest activated houses into plain language.

    Pick at most the top 3 houses by transit count, ignore singletons
    unless we have nothing else.
    """
    by_house = house_acts.get("by_house") or {}
    if not by_house:
        return []
    # Score: count of transits in that house
    scored = sorted(
        ((int(h), len(bs)) for h, bs in by_house.items()),
        key=lambda x: -x[1],
    )
    multis = [(h, c) for h, c in scored if c >= 2]
    pool = multis if multis else scored[:2]
    out: List[str] = []
    for h, _ in pool[:3]:
        arena = HOUSE_ARENA.get(h)
        if arena:
            out.append(arena)
    return out


# ---------------------------------------------------------------------------
# LLM stage
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You write the HOME card for an app called Mirror.

Your job is to mirror the user's most important psychological tension
RIGHT NOW, anchored on the dominant astrological signal you'll be
given — but you are NOT writing astrology and you are NOT echoing
the Today narrative verbatim.

Mirror Language rules — these are HARD constraints. Violations are
rejected.

LANGUAGE STYLE
1. Blunt. Concrete. Behavioral.
2. NO metaphors. Banned phrasings:
   - "whirlwind", "dancing with", "hazy landscape", "fog of",
     "cobbling together", "quell the discomfort", "swirl of",
     "tides of", "winds of", "tapestry", "kaleidoscope", anything
     poetic.
3. NO jargon. Banned words: "energy", "alignment", "vibe",
   "frequency", "manifest", "flow", "block", "shadow", "tension is
   real" (cliché), anything astrological.
4. NO coaching tone. Banned moves: "Pause to assess", "Consider",
   "Try", "You should", "Take a breath", "Step back and ask
   yourself".
5. Slightly confronting but NEVER harsh. The card should make a
   person think "Yeah… that's exactly what's happening."

SECTION FORMAT (HARD)

THE_CALL  (max 2 short lines)
  Format must be: "You're [behavior] — but [truth underneath]."
  Example shapes:
    - "You're moving fast — but your read of the situation is not
      clean yet."
    - "You're trying to close the loop — but something still doesn't
      add up."
    - "You're ready to act — but the signal isn't clean enough to
      trust fully."

THE_REALITY  (max 2 short sentences, plain)
  Describe the actual behavior — replying, deciding, pushing, settling
  — and name the gap underneath it. No imagery. No coaching.
  Example shape:
    "You may be replying, deciding, or pushing something forward just
    to reduce pressure. But some of the pieces still need a second
    look."

WHERE_THIS_LANDS
  An ARRAY of 2-3 short plain-life domain lines. NEVER reuse the
  exact wording from the input — produce concise plain-life arenas.
  Allowed phrasings include: "Communication and decisions",
  "Home and personal environment", "Creative expression",
  "Work and daily rhythm", "Relationships", "Money and security".

THE_EDGE  (1-2 sentences, observational only)
  MUST be observational, not advisory. Banned: "Pause", "Consider",
  "Try", "You should", "Step back". Use shapes like:
    - "The tension isn't only in the situation — part of it is in how
      quickly you're reading it."
    - "The danger isn't movement. It's moving before the picture is
      clear."
    - "The risk isn't in acting. It's in acting without a second
      look."

CTA
  Always: "→ See what's driving this today"

Output: STRICT JSON, no markdown, no commentary, exactly these keys:
{
  "the_call":         "...",
  "the_reality":      "...",
  "where_this_lands": ["...", "...", "..."],
  "the_edge":         "...",
  "cta":              "→ See what's driving this today"
}

The "angle" you'll be told to use determines which section anchors
strongest:
- call    → lead with a sharper hook on the dominant tension
- reality → lead with the behavioral mechanics underneath
- edge    → lead with the observational truth about HOW the user is reading the situation

The other sections still render but the chosen angle is the loudest
voice."""


def _build_user_prompt(
    *,
    v5: Dict[str, Any],
    house_acts: Dict[str, Any],
    angle: str,
) -> str:
    ds = v5.get("dominant_signal") or {}
    sections = v5.get("sections") or {}
    today_core = sections.get("core_message") or v5.get("headline") or ""
    today_risk = sections.get("the_risk") or ""
    today_move = sections.get("the_move") or {}
    why = v5.get("why_this_is_showing_up") or {}
    secondary = why.get("secondary_signals") or v5.get("secondary_signals") or []

    secondary_lines = []
    for s in secondary[:3]:
        lbl = s.get("label")
        if lbl:
            secondary_lines.append(f"- {lbl}")

    arena_lines = _format_house_arena_lines(house_acts)
    arena_block = "\n".join(f"- {a}" for a in arena_lines) if arena_lines else "- (no strong house clustering)"

    intensity = v5.get("intensity") or "medium"
    conflict = "YES — multiple competing pulls" if v5.get("signal_conflict") else "no — signals largely aligned"

    return f"""ANGLE TO ANCHOR: {angle}

DOMINANT SIGNAL (Tier 1): {ds.get('label')}
INTENSITY: {intensity}
SIGNAL CONFLICT: {conflict}

SECONDARY SIGNALS (background, do NOT name astrologically in output):
{chr(10).join(secondary_lines) if secondary_lines else '- (none)'}

WHERE THIS IS LANDING IN THE USER'S LIFE (real-life translations, choose 2-3 for `where_this_lands`):
{arena_block}

TODAY'S NARRATIVE (do NOT copy. Reframe from a higher altitude.):
- core: {today_core}
- risk: {today_risk}
- move (non-prescriptive shape): action="{today_move.get('action','')}" reflect="{today_move.get('reflect','')}"

Now produce the HOME V6 JSON per the system contract.
Critical: every line must be specific behavior, never generic motivation.
Critical: the_call must NOT repeat any sentence from `core` above —
it must zoom out and name the *life-level* tension underneath."""


async def _llm_build_sections(
    *,
    v5: Dict[str, Any],
    house_acts: Dict[str, Any],
    angle: str,
) -> Dict[str, Any]:
    """Call gpt-4o via Emergent LLM key. Falls back to a deterministic
    construction if the LLM is unreachable."""
    api_key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get(
        "EMERGENT_INTEGRATIONS_API_KEY",
    )
    if not api_key:
        logger.warning("[HomeV6] No EMERGENT_LLM_KEY — using deterministic fallback")
        return _deterministic_fallback(v5, house_acts, angle)

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"home_v6_{v5.get('user_id','x')}_{v5.get('signature_hash','x')[:8]}_{angle}",
            system_message=_SYSTEM_PROMPT,
        )
        chat.with_model("openai", "gpt-4o")
        try:
            chat.with_params(timeout=18, num_retries=0, max_retries=0)
        except Exception:
            pass

        prompt = _build_user_prompt(v5=v5, house_acts=house_acts, angle=angle)
        msg = UserMessage(text=prompt)
        import asyncio as _asyncio
        raw = await _asyncio.wait_for(chat.send_message(msg), timeout=20)

        cleaned = (raw or "").strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        result = json.loads(cleaned)

        # Coerce shape
        if not isinstance(result.get("where_this_lands"), list):
            wtl = result.get("where_this_lands")
            result["where_this_lands"] = (
                [str(wtl)] if isinstance(wtl, str) and wtl.strip() else _format_house_arena_lines(house_acts)
            )

        result["cta"] = "→ See what's driving this today"
        return result
    except Exception as e:
        logger.warning("[HomeV6] LLM call failed (%s) — falling back", e)
        return _deterministic_fallback(v5, house_acts, angle)


def _deterministic_fallback(
    v5: Dict[str, Any],
    house_acts: Dict[str, Any],
    angle: str,
) -> Dict[str, Any]:
    """Behavioral fallback when LLM is unavailable.  Still avoids
    jargon and keeps tension framing."""
    ds = v5.get("dominant_signal") or {}
    label = (ds.get("label") or "").lower()
    intensity = v5.get("intensity") or "medium"
    conflict = bool(v5.get("signal_conflict"))

    # Generic but tension-shaped — only used when LLM is down.
    if "full moon" in label or "new moon" in label:
        call = "Something's coming to a head — and you're about to act on it before it's actually clear."
        reality = (
            "There's pressure to decide, reply, or commit so the tension stops. "
            "But what's pushing you isn't fully accurate yet — you're filling gaps "
            "to feel resolved instead of waiting until the picture lands."
        )
        edge = "The move isn't to stop — it's to see what you're actually reacting to before you commit."
    elif conflict:
        call = "You're being pulled in two directions and treating one of them as the obvious answer."
        reality = (
            "Two real pulls are active right now and you've already started narrowing onto one to "
            "relieve the friction. The decision feels clean — but you've stopped weighing the half "
            "you don't want to look at."
        )
        edge = "The move isn't to pick faster. It's to name what you're avoiding seeing on the other side."
    else:
        call = "You're moving on something — and you're trusting the read more than the read deserves."
        reality = (
            "Action feels right. The story you've built around it is tidy. But under that tidy story "
            "is information you haven't checked, and the speed is how you keep yourself from checking."
        )
        edge = "The move isn't to slow down — it's to name what you'd see if you stopped narrating it."

    return {
        "the_call":         call,
        "the_reality":      reality,
        "where_this_lands": _format_house_arena_lines(house_acts),
        "the_edge":         edge,
        "cta":              "→ See what's driving this today",
    }



# ---------------------------------------------------------------------------
# Pattern Memory layer (v6.1)
# ---------------------------------------------------------------------------
# Light, deterministic — looks across `db.pattern_memory` and
# `db.reflections` (last 30 days) for recurrence of today's tension.
# Only returns `available=True, confidence="high"` when at least one
# of these holds:
#   * Same `tension_hash` appeared 2+ times in the last 30 days.
#   * Same `primary_tension` text appeared 2+ times in the last 30 days.
#   * A reflection in the last 30 days mentions the same theme keywords
#     as today's dominant signal.
#
# The summary line is built from a curated set of safe, non-overclaiming
# phrasings — never echoes raw private journal text, never says
# "you always", never diagnoses.

_SAFE_RECURRENCE_LINES = (
    "This has shown up before when uncertainty feels hard to sit with.",
    "A recent reflection points to a similar pattern.",
    "There's a familiar move here: trying to regain control by moving faster.",
    "This is not the first time pressure has made speed feel necessary.",
    "There's a similar shape from a recent stretch — pushing to settle "
    "something before it's fully clear.",
)


def _theme_for_signal(v5: Dict[str, Any]) -> str:
    """Compact internal label for the dominant signal's theme."""
    ds = v5.get("dominant_signal") or {}
    t = (ds.get("type") or "").lower()
    if "full_moon" in t:
        return "speed_under_uncertainty"
    if "new_moon" in t:
        return "premature_initiation"
    if "ingress" in t:
        return "shift_in_focus"
    if "tight_aspect" in t:
        return "tight_pressure"
    if v5.get("signal_conflict"):
        return "competing_pulls"
    return "background_pattern"


def _summary_for_theme(theme: str, count: int) -> str:
    """Pick a safe summary line. Deterministic by theme + count parity
    so the line stays stable across cache reads but varies per user
    over time."""
    if theme in ("speed_under_uncertainty", "premature_initiation",
                 "tight_pressure"):
        idx = (count + 0) % len(_SAFE_RECURRENCE_LINES)
    elif theme == "competing_pulls":
        idx = (count + 1) % len(_SAFE_RECURRENCE_LINES)
    else:
        idx = (count + 2) % len(_SAFE_RECURRENCE_LINES)
    return _SAFE_RECURRENCE_LINES[idx]


async def _resolve_pattern_memory(
    db, user_id: str, v5: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect light recurrence and return a safe Mirror Remembers block.

    Output contract:
        available=True, confidence="high"  → render
        available=False                    → hide
    """
    try:
        from datetime import timedelta
        cutoff_dt  = datetime.now(timezone.utc) - timedelta(days=30)
        cutoff_iso = cutoff_dt.isoformat()
        # Some legacy docs store `stored_at` as a string (ISO) instead of
        # a datetime — the cutoff condition supports both shapes via $or.
        cutoff_q = {"$or": [
            {"stored_at": {"$gte": cutoff_dt}},
            {"stored_at": {"$gte": cutoff_iso}},
            {"date":      {"$gte": cutoff_dt.strftime("%Y-%m-%d")}},
        ]}

        # 1) Same tension_hash count in last 30 days (highest signal)
        try:
            today_pm = await db.pattern_memory.find_one(
                {"user_id": user_id},
                sort=[("stored_at", -1)],
            )
        except Exception:
            today_pm = None

        target_hash = (today_pm or {}).get("tension_hash") if today_pm else None
        target_tension = (today_pm or {}).get("primary_tension") if today_pm else None

        same_hash_count = 0
        same_tension_count = 0
        try:
            if target_hash:
                same_hash_count = await db.pattern_memory.count_documents({
                    "$and": [
                        {"user_id":      user_id},
                        {"tension_hash": target_hash},
                        cutoff_q,
                    ],
                })
            if target_tension:
                same_tension_count = await db.pattern_memory.count_documents({
                    "$and": [
                        {"user_id":         user_id},
                        {"primary_tension": target_tension},
                        cutoff_q,
                    ],
                })
        except Exception as e:
            logger.warning("[HomeV6/PM] count failed: %s", e)

        # 2) Reflection mentions in last 30 days (handle both date types)
        recent_reflection_count = 0
        try:
            recent_reflection_count = await db.reflections.count_documents({
                "$and": [
                    {"user_id": user_id},
                    {"$or": [
                        {"created_at": {"$gte": cutoff_dt}},
                        {"created_at": {"$gte": cutoff_iso}},
                    ]},
                ],
            })
        except Exception:
            pass

        theme = _theme_for_signal(v5)

        # Decide: high-confidence recurrence?
        if same_hash_count >= 2:
            return {
                "available":     True,
                "confidence":    "high",
                "theme":         theme,
                "summary":       _summary_for_theme(theme, same_hash_count),
                "source_type":   "pattern_memory_hash",
                "source_count":  int(same_hash_count),
            }
        if same_tension_count >= 2:
            return {
                "available":     True,
                "confidence":    "high",
                "theme":         theme,
                "summary":       _summary_for_theme(theme, same_tension_count),
                "source_type":   "pattern_memory_tension",
                "source_count":  int(same_tension_count),
            }
        if recent_reflection_count >= 2 and (same_hash_count >= 1 or same_tension_count >= 1):
            # Mixed evidence: pattern_memory hit once + reflections present
            count = max(same_hash_count, same_tension_count) + recent_reflection_count
            return {
                "available":     True,
                "confidence":    "high",
                "theme":         theme,
                "summary":       _summary_for_theme(theme, count),
                "source_type":   "reflection_plus_pattern",
                "source_count":  int(count),
            }

        return {
            "available":  False,
            "confidence": "low",
        }
    except Exception as e:
        logger.warning("[HomeV6/PM] resolution failed: %s", e)
        return {"available": False, "confidence": "low"}
