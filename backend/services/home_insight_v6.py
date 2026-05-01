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
        "version":             "v6.2",
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
        "relational_pattern":  await _resolve_relational_pattern(db, user_id, v5),
        # Future hooks — explicitly empty placeholders so the contract is
        # stable when later layers light up.
        "future_layers": {
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


# ---------------------------------------------------------------------------
# Relational Pattern overlay (v6.2)
# ---------------------------------------------------------------------------
# Detects whether today's tension also tends to activate around specific
# people in the user's life — without becoming relationship advice and
# without exposing private information.
#
# Sources (light, existing data only — no new system):
#   * db.relationship_patterns       (organic interaction logs from
#                                     Forum / People / Life)
#   * db.saved_people                (explicit user-curated list,
#                                     authoritative for naming)
#
# Confidence policy:
#   HIGH only if at least ONE holds:
#     - ≥ 2 organic interactions with the same non-test person in
#       the last 30 days AND the user_type from those records matches
#       today's behavioral theme (e.g. initiator → speed_under_uncertainty)
#     - person is in saved_people AND has ≥ 1 organic mention in 30d
#     - ≥ 3 distinct people share the same dynamic_signature, in which
#       case we render a CONTEXT label (e.g. "close conversations")
#       rather than a person name.
#   Anything below → DO NOT render.
#
# Safety filter:
#   - name must pass `_is_safe_person_name`
#   - name MUST appear in saved_people OR have ≥ 3 organic mentions
#     (organic threshold prevents accidental exposure of one-off names
#      that may have been entered for testing / journaling abstractions)
#   - never quote conversations, never describe the other person
#   - never state how the other person feels / acts / "makes you feel"

import re

_TEST_NAME_PATTERNS = (
    re.compile(r"\d{4,}"),                      # contains 4+ digit run
    re.compile(r"(?i)\btest\b"),                # any "test" token
    re.compile(r"(?i)^(escalate|fresh|recurring|soft|structure)\w*\d", ),
)


def _is_safe_person_name(name: Optional[str]) -> bool:
    if not name or not isinstance(name, str):
        return False
    n = name.strip()
    if not (2 <= len(n) <= 30):
        return False
    if any(p.search(n) for p in _TEST_NAME_PATTERNS):
        return False
    # Must be primarily alphabetic (allow hyphen, apostrophe, single space)
    if not re.fullmatch(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-' ]{1,29}", n):
        return False
    return True


# Map of theme → behavioral keyword aliases.  We use these to decide
# whether a given relationship_patterns user_type matches today's
# dominant pattern theme.
_THEME_USER_TYPES: Dict[str, set] = {
    "speed_under_uncertainty": {"initiator", "rusher", "fixer"},
    "premature_initiation":    {"initiator", "starter"},
    "tight_pressure":          {"initiator", "fixer", "responder"},
    "competing_pulls":         {"oscillator", "negotiator"},
    "shift_in_focus":          {"initiator", "transitioner"},
    "background_pattern":      set(),  # don't anchor by user_type
}

# Curated, safe phrasings.  Person-anchored vs context-anchored.
_RELATIONAL_PERSON_LINES = (
    "This may show up in how you respond to {name}. The reaction arrives before clarity fully forms.",
    "This pattern may surface in how you respond to {name}. The speed comes in before the full picture lands.",
    "This shows up most when conversations with {name} move faster than clarity.",
)

_RELATIONAL_CONTEXT_LINES = (
    "This tends to show up in conversations where you feel the need to respond quickly.",
    "This may surface in how you respond to people close to you. The reaction arrives before clarity fully forms.",
    "The pattern shows up most when the conversation moves faster than clarity.",
    "This tends to show up in close conversations — the reply lands before the picture does.",
)


def _pick_line(lines: tuple, key: str) -> str:
    """Deterministic selection — stable per (key) so the same context
    yields the same phrasing across cache reads."""
    if not lines:
        return ""
    h = sum(ord(c) for c in (key or "")) % len(lines)
    return lines[h]


async def _resolve_relational_pattern(
    db, user_id: str, v5: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        from datetime import timedelta
        cutoff_dt  = datetime.now(timezone.utc) - timedelta(days=30)
        cutoff_iso = cutoff_dt.isoformat()
        cutoff_q = {"$or": [
            {"timestamp":  {"$gte": cutoff_dt}},
            {"timestamp":  {"$gte": cutoff_iso}},
            {"created_at": {"$gte": cutoff_dt}},
            {"created_at": {"$gte": cutoff_iso}},
        ]}

        theme = _theme_for_signal(v5)
        target_user_types = _THEME_USER_TYPES.get(theme, set())

        # 1) Pull recent relationship_patterns.  Tally organic mentions
        #    per *safe* name AND tally how many of those rows match
        #    today's behavioral theme via user_type.
        rp_recent = []
        try:
            rp_recent = await db.relationship_patterns.find({
                "$and": [{"user_id": user_id}, cutoff_q],
            }).limit(200).to_list(200)
        except Exception:
            rp_recent = []

        from collections import Counter
        name_counts: Counter = Counter()
        name_theme_hits: Counter = Counter()
        dyn_sig_counts: Counter = Counter()

        for r in rp_recent:
            n = r.get("other_name")
            if not _is_safe_person_name(n):
                continue
            name_counts[n] += 1
            ut = (r.get("user_type") or "").lower()
            if target_user_types and ut in target_user_types:
                name_theme_hits[n] += 1
            ds = r.get("dynamic_signature")
            if ds:
                dyn_sig_counts[ds] += 1

        # 2) Saved_people authoritative list — only names from here may be
        #    revealed unless organic count is ≥ 3.
        saved_names: set = set()
        try:
            sp_docs = await db.saved_people.find(
                {"user_id": user_id},
            ).to_list(200)
            for sp in sp_docs or []:
                n = (sp.get("name") or "").strip()
                if _is_safe_person_name(n):
                    saved_names.add(n)
        except Exception:
            pass

        # 3) Decide person reveal eligibility
        ranked = name_counts.most_common()
        chosen_name: Optional[str] = None
        chosen_count: int = 0
        for n, c in ranked:
            organic_ok = (c >= 3) or (n in saved_names and c >= 1)
            theme_ok   = (
                not target_user_types          # theme has no behavioral anchor — accept
                or name_theme_hits.get(n, 0) >= 1
            )
            if organic_ok and theme_ok and c >= 2:
                chosen_name = n
                chosen_count = c
                break

        if chosen_name:
            line = _pick_line(_RELATIONAL_PERSON_LINES, chosen_name + theme)
            return {
                "available":     True,
                "confidence":    "high",
                "type":          "person",
                "label":         chosen_name,
                "summary":       line.format(name=chosen_name),
                "source_count":  int(chosen_count),
                "theme":         theme,
            }

        # 4) Context fallback — only if multiple safe people share a
        #    common dynamic_signature recently (→ "close conversations" type)
        total_safe_mentions = sum(name_counts.values())
        distinct_safe_people = len(name_counts)
        top_dyn = dyn_sig_counts.most_common(1)
        if (
            distinct_safe_people >= 2
            and total_safe_mentions >= 4
            and top_dyn
            and top_dyn[0][1] >= 2
        ):
            label = "close conversations"
            # If saved_people exists, prefer "people you've named"
            if saved_names and len(saved_names) >= 2:
                label = "people you've named in your life"
            line = _pick_line(_RELATIONAL_CONTEXT_LINES, theme + label)
            return {
                "available":     True,
                "confidence":    "high",
                "type":          "context",
                "label":         label,
                "summary":       line,
                "source_count":  int(total_safe_mentions),
                "theme":         theme,
            }

        return {"available": False, "confidence": "low"}
    except Exception as e:
        logger.warning("[HomeV6/Rel] resolution failed: %s", e)
        return {"available": False, "confidence": "low"}

