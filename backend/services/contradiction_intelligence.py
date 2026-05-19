"""
Contradiction Intelligence — v1
================================

Build marker: contradiction-intelligence-v1

Detects soft divergences between what is *said* and what is repeatedly
*signalled* — in language vs. emotional texture, in stated openness vs.
recurring resistance, in narrative resolution vs. unresolved pattern
memory.

DESIGN RULES (do-or-die):

  1. Contradiction is framed as HUMAN TENSION, never as deceit,
     hypocrisy, denial, manipulation, or exposure.

  2. Only MODERATE+ contradictions are allowed to surface, and even
     then only SOFTLY (single probabilistic clause, one thread max
     per turn).

  3. NEVER name a "villain", "problem person", or "the real issue".
     NEVER quantify with scores in user-facing text.

  4. Reflection taps REDUCE contradiction intensity (a user actively
     marking 'lands' / 'changed' soothes the loop).

  5. Operates entirely on EXISTING signals — pattern memory, micro
     reflections, forum topology/timing/field-intel.  No new Mongo
     collection; nothing persisted by this module.

PUBLIC API:

  await compute_individual_contradictions(
      db, user_id, message_text=None
  ) -> ContradictionPayload

  await compute_forum_contradictions(
      db, forum_id
  ) -> ContradictionPayload

  build_contradiction_system_block(payload) -> str
      Empty string when level < MODERATE or surfaced is False.

  build_contradiction_debug(payload) -> dict
      Always safe to fold into `debug.contradictions`.

  build_field_contradiction_signals(payload) -> List[str]
      Soft labels like 'openness-with-avoidance' for forum field intel.

  build_evidence_contradiction_line(payload) -> Optional[str]
      Field-language line for the EvidenceDrawer.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


MARKER = "contradiction-intelligence-v1"

# Levels — internal only.  Only MODERATE / STRONG may surface softly.
LEVEL_LOW = "LOW"
LEVEL_EMERGING = "EMERGING"
LEVEL_MODERATE = "MODERATE"
LEVEL_STRONG = "STRONG"
_LEVEL_ORDER = [LEVEL_LOW, LEVEL_EMERGING, LEVEL_MODERATE, LEVEL_STRONG]


# Contradiction type vocabulary (internal labels).
T_RESOLUTION_VS_RESISTANCE = "resolution-claimed-resistance-present"
T_OPENNESS_VS_NOTSURE = "openness-claimed-not-sure-recurring"
T_HONESTY_VS_SOFTENING = "honesty-asked-intensity-softened"
T_PROGRESS_VS_STUCK = "progress-claimed-stuck-texture-recurring"
T_FORUM_OPEN_VS_AVOID = "forum-open-stated-avoidance-recurring"
T_FORUM_DIRECT_VS_HUMOUR = "forum-direct-claimed-humour-dissolves"
T_FORUM_FLAT_VS_RIGID = "forum-equal-claimed-hierarchy-rigid"


# ---------------------------------------------------------------------------
# Soft language detectors — case-insensitive.  Each returns a numeric
# weight (0..3) so multiple weak signals can compound into a stronger
# read without any single phrase being decisive.
# ---------------------------------------------------------------------------

_RESOLUTION_PATTERNS = [
    r"\bi['’]?m\s+(?:over|done\s+with|past)\s+(?:it|this|that|all\s+that)\b",
    r"\b(?:things|everything|it)\s+(?:are|is|feels?)\s+(?:better|fine|good|okay|ok)\s+now\b",
    r"\b(?:i\s+)?(?:already\s+)?(?:dealt\s+with|moved\s+(?:on|past))\s+(?:it|this|that)\b",
    r"\bi\s+(?:feel|am)\s+(?:clear|resolved|settled|at\s+peace)\b",
    r"\bno\s+longer\s+(?:bothers?|affects?)\s+me\b",
]

_OPENNESS_CLAIM_PATTERNS = [
    r"\bi['’]?m\s+open\s+(?:to|about)\b",
    r"\bi\s+want\s+(?:to\s+be\s+)?honest\b",
    r"\bi\s+want\s+(?:more\s+)?honesty\b",
    r"\b(?:i\s+)?welcome\s+hard\s+conversations?\b",
    r"\bi\s+can\s+take\s+the\s+truth\b",
    r"\bi['’]?m\s+ready\s+(?:to|for)\s+(?:hear|the\s+truth|directness)\b",
]

_DIRECTNESS_CLAIM_PATTERNS = [
    r"\bjust\s+say\s+it\b",
    r"\bbe\s+(?:direct|blunt|straight)\b",
    r"\bdon['’]?t\s+(?:soften|sugar.?coat)\b",
    r"\bgive\s+it\s+to\s+me\s+straight\b",
]

_PROGRESS_CLAIM_PATTERNS = [
    r"\bi['’]?ve?\s+(?:come|grown|moved)\s+(?:a\s+)?(?:long\s+)?way\b",
    r"\bi\s+(?:have|do)\s+(?:changed|grown|evolved)\b",
    r"\b(?:much|so)\s+better\s+than\s+(?:before|i\s+used\s+to|i\s+was)\b",
    r"\bthat\s+(?:is|was)\s+behind\s+me\b",
]


def _hits(patterns: List[str], text: str) -> int:
    if not text:
        return 0
    n = 0
    for p in patterns:
        try:
            if re.search(p, text, flags=re.IGNORECASE):
                n += 1
        except re.error:
            continue
    return n


# ---------------------------------------------------------------------------
# Internal scorer.  Each "type" can score up to 3 internally.  Final
# level computed from the max(type_score) + cross-corroboration.
# ---------------------------------------------------------------------------


def _level_from_score(score: int) -> str:
    if score >= 4:
        return LEVEL_STRONG
    if score == 3:
        return LEVEL_MODERATE
    if score == 2:
        return LEVEL_EMERGING
    return LEVEL_LOW


# ---------------------------------------------------------------------------
# Individual contradictions
# ---------------------------------------------------------------------------


async def compute_individual_contradictions(
    db,
    *,
    user_id: str,
    message_text: Optional[str] = None,
    recent_user_messages: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Look at recent micro-reflections + pattern memory recurrence vs.
    current/recent user language.

    Returns a dict:
      {
        marker, level, types[], surfaced (bool),
        softened_by_reflection (bool), forum_related (False),
        recurrence_overlap[], debug_signals{...}
      }
    """
    # 1. Reflection summary (uses existing micro_reflection_v2 analyzer).
    try:
        from services.micro_reflection_v2 import analyze_recent
        refl = await analyze_recent(db, user_id=user_id)
    except Exception:
        refl = {
            "growth_score": 0,
            "resistance_score": 0,
            "resonance_score": 0,
            "per_pattern_growth": {},
            "per_pattern_resistance": {},
            "counts_label": {},
            "counts_texture": {},
            "total": 0,
        }

    # 2. Recent pattern recurrence — fetch the user's longitudinal
    # pattern memory store directly.  We only need pattern_key,
    # occurrence_count, last_seen_at.
    pm_records: List[Dict[str, Any]] = []
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=21)
        cursor = db.longitudinal_pattern_memory.find(
            {"user_id": user_id, "last_seen_at": {"$gte": cutoff}}
        ).sort("last_seen_at", -1).limit(40)
        async for r in cursor:
            r.pop("_id", None)
            pm_records.append(r)
    except Exception:
        pm_records = []

    # Compute aggregate "still-active" load.  Anything with
    # occurrence_count >= 2 in the last 21 days counts as active.
    active_pattern_keys: List[str] = [
        r.get("pattern_key", "")
        for r in pm_records
        if int(r.get("occurrence_count", 0) or 0) >= 2
    ]
    active_pattern_keys = [k for k in active_pattern_keys if k]

    # 3. Aggregate the current+recent user text.
    text_blob = (message_text or "")
    if recent_user_messages:
        text_blob = " ".join([text_blob] + list(recent_user_messages))

    resolution_hits = _hits(_RESOLUTION_PATTERNS, text_blob)
    openness_hits = _hits(_OPENNESS_CLAIM_PATTERNS, text_blob)
    directness_hits = _hits(_DIRECTNESS_CLAIM_PATTERNS, text_blob)
    progress_hits = _hits(_PROGRESS_CLAIM_PATTERNS, text_blob)

    resistance_score = int(refl.get("resistance_score", 0) or 0)
    growth_score = int(refl.get("growth_score", 0) or 0)
    counts_label = refl.get("counts_label") or {}
    counts_texture = refl.get("counts_texture") or {}
    not_sure = int(counts_label.get("not_sure", 0) or 0)
    stuck_tex = int(counts_texture.get("stuck", 0) or 0)
    pressured_tex = int(counts_texture.get("pressured", 0) or 0)

    types: List[Dict[str, Any]] = []
    recurrence_overlap: List[str] = []

    # T1: claims resolution while resistance signals continue.
    score = 0
    if resolution_hits >= 1 and resistance_score >= 2:
        score += 2
    if resolution_hits >= 1 and len(active_pattern_keys) >= 1:
        score += 1
        recurrence_overlap.extend(active_pattern_keys[:3])
    if resolution_hits >= 2:
        score += 1
    if score >= 2:
        types.append({"type": T_RESOLUTION_VS_RESISTANCE, "score": min(score, 4)})

    # T2: claims openness while "not_sure" reflections recur.
    score = 0
    if openness_hits >= 1 and not_sure >= 2:
        score += 2
    if openness_hits >= 2 and not_sure >= 1:
        score += 1
    if score >= 2:
        types.append({"type": T_OPENNESS_VS_NOTSURE, "score": min(score, 4)})

    # T3: claims honesty/directness while continuing to soften intensity
    # (proxied by repeated softening reflections AND high resistance).
    score = 0
    soft_lbl = int(counts_label.get("less_intense", 0) or 0) + int(counts_label.get("changed", 0) or 0)
    softer_tex = int(counts_texture.get("softer", 0) or 0)
    if (openness_hits + directness_hits) >= 1 and (soft_lbl + softer_tex) >= 3 and resistance_score >= 1:
        score += 3
    elif (openness_hits + directness_hits) >= 1 and (soft_lbl + softer_tex) >= 2:
        score += 2
    if score >= 2:
        types.append({"type": T_HONESTY_VS_SOFTENING, "score": min(score, 4)})

    # T4: claims progress/growth while "stuck"/"pressured" textures
    # recur AND active pattern keys present.
    score = 0
    if progress_hits >= 1 and (stuck_tex + pressured_tex) >= 2:
        score += 2
    if progress_hits >= 1 and len(active_pattern_keys) >= 2:
        score += 1
        recurrence_overlap.extend([k for k in active_pattern_keys if k not in recurrence_overlap][:3])
    if score >= 2:
        types.append({"type": T_PROGRESS_VS_STUCK, "score": min(score, 4)})

    # Final level = max of any single type's score.
    max_score = max([t["score"] for t in types], default=0)
    level = _level_from_score(max_score)

    # Softening by reflection: lots of growth taps + resonance taps
    # de-escalates contradiction intensity by ONE step.
    softened_by_reflection = False
    resonance_score = int(refl.get("resonance_score", 0) or 0)
    if level in (LEVEL_MODERATE, LEVEL_STRONG) and (growth_score >= 4 or resonance_score >= 4):
        # Step down one level.
        idx = _LEVEL_ORDER.index(level)
        level = _LEVEL_ORDER[max(0, idx - 1)]
        softened_by_reflection = True

    surfaced = level in (LEVEL_MODERATE, LEVEL_STRONG)

    return {
        "marker": MARKER,
        "scope": "individual",
        "level": level,
        "types": [t["type"] for t in types],
        "type_scores": types,
        "surfaced": surfaced,
        "softened_by_reflection": softened_by_reflection,
        "forum_related": False,
        "recurrence_overlap": recurrence_overlap[:5],
        "debug_signals": {
            "resolution_hits": resolution_hits,
            "openness_hits": openness_hits,
            "directness_hits": directness_hits,
            "progress_hits": progress_hits,
            "resistance_score": resistance_score,
            "growth_score": growth_score,
            "resonance_score": resonance_score,
            "not_sure_count": not_sure,
            "stuck_tex_count": stuck_tex,
            "pressured_tex_count": pressured_tex,
            "active_pattern_count": len(active_pattern_keys),
        },
    }


# ---------------------------------------------------------------------------
# Forum contradictions
# ---------------------------------------------------------------------------


async def compute_forum_contradictions(
    db,
    *,
    forum_id: str,
) -> Dict[str, Any]:
    """
    Use forum topology + timing + field intel debug to detect collective
    contradictions.  No member-level diagnosis — all signals are at
    field/structure level.
    """
    types: List[Dict[str, Any]] = []
    signals: Dict[str, Any] = {}

    # 1. Topology + timing — pull existing scores.
    try:
        from services.forum_topology import (
            list_edges,
            get_topology_confidence_state,
        )
        from services.forum_timing_engine import synthesize_timing_state

        edges = await list_edges(db, forum_id=forum_id)
        confidence_info = await get_topology_confidence_state(db, forum_id=forum_id)

        # Collect member ids for timing.
        member_ids: List[str] = []
        try:
            cursor = db.forum_members.find({"forum_id": forum_id})
            async for r in cursor:
                uid = r.get("user_id")
                if uid:
                    member_ids.append(str(uid))
        except Exception:
            pass
        timing = await synthesize_timing_state(db, member_ids=member_ids) if member_ids else {}
    except Exception:
        edges = []
        confidence_info = {"state": "none"}
        timing = {}

    hard_hier = sum(1 for e in edges if e.get("power_gradient") == "hard_hierarchy")
    soft_hier = sum(1 for e in edges if e.get("power_gradient") == "soft_hierarchy")
    equal = sum(1 for e in edges if e.get("power_gradient") == "equal")
    heavy = sum(1 for e in edges if e.get("emotional_weight") == "heavy")
    counts = (timing or {}).get("signal_counts") or {}

    protective = int(counts.get("protective", 0) or 0)
    pressured = int(counts.get("pressured", 0) or 0)
    softening = int(counts.get("softening", 0) or 0)
    transition = int(counts.get("transition", 0) or 0)

    signals["topology_confidence"] = confidence_info.get("state")
    signals["hard_hier"] = hard_hier
    signals["soft_hier"] = soft_hier
    signals["equal"] = equal
    signals["heavy_edges"] = heavy
    signals["protective"] = protective
    signals["pressured"] = pressured
    signals["softening"] = softening
    signals["transition"] = transition

    # T_FORUM_OPEN_VS_AVOID — softening claimed but pressure / protective
    # signals dominate.
    score = 0
    if softening >= 2 and (protective + pressured) >= 3:
        score += 3
    elif softening >= 1 and (protective + pressured) >= 2:
        score += 2
    if score >= 2:
        types.append({"type": T_FORUM_OPEN_VS_AVOID, "score": min(score, 4)})

    # T_FORUM_DIRECT_VS_HUMOUR — protective field dissolves pressure;
    # proxied here as protective ≥ 2 AND no softening signal materialised
    # despite multiple emotional spikes (heavy edges).
    score = 0
    if protective >= 2 and heavy >= 2 and softening <= 1:
        score += 3
    elif protective >= 2 and heavy >= 1:
        score += 2
    if score >= 2:
        types.append({"type": T_FORUM_DIRECT_VS_HUMOUR, "score": min(score, 4)})

    # T_FORUM_FLAT_VS_RIGID — equal edges present alongside multiple
    # hard-hierarchy edges (stated flatness, lived hierarchy).
    score = 0
    if equal >= 1 and hard_hier >= 2:
        score += 3
    elif hard_hier >= 1 and (soft_hier + hard_hier) >= 3 and equal >= 1:
        score += 2
    if score >= 2:
        types.append({"type": T_FORUM_FLAT_VS_RIGID, "score": min(score, 4)})

    max_score = max([t["score"] for t in types], default=0)
    level = _level_from_score(max_score)

    # When topology is sparse/none the data is not enough — refuse to
    # surface anything.
    if confidence_info.get("state") in ("none", "sparse"):
        level = LEVEL_LOW

    surfaced = level in (LEVEL_MODERATE, LEVEL_STRONG)

    return {
        "marker": MARKER,
        "scope": "forum",
        "level": level,
        "types": [t["type"] for t in types],
        "type_scores": types,
        "surfaced": surfaced,
        "softened_by_reflection": False,
        "forum_related": True,
        "recurrence_overlap": [],
        "debug_signals": signals,
    }


# ---------------------------------------------------------------------------
# System-prompt block (LLM instruction; never directly user-facing).
# ---------------------------------------------------------------------------


_INDIVIDUAL_BLOCK_TEMPLATES: Dict[str, str] = {
    T_RESOLUTION_VS_RESISTANCE: (
        "Some signals seem mixed: in language there's a sense that "
        "things are resolved, while in recent texture there's still "
        "active charge around it.  If it fits the moment, acknowledge "
        "this as TENSION — part of them may genuinely feel through it "
        "while another part still reacts when the situation returns.  "
        "Do NOT call it denial.  Do NOT call it hypocrisy."
    ),
    T_OPENNESS_VS_NOTSURE: (
        "There's a quiet mismatch — openness is named in language, "
        "while uncertainty keeps re-appearing as the actual texture.  "
        "If it fits naturally, gently honour BOTH: the wish to be open "
        "and the not-yet-clear underneath."
    ),
    T_HONESTY_VS_SOFTENING: (
        "There's a quiet mismatch — directness is asked for, while "
        "intensity keeps being softened in practice.  Hold this as "
        "human, not deceptive — a pull toward both at once.  Do NOT "
        "expose it as a problem.  Do NOT push harder."
    ),
    T_PROGRESS_VS_STUCK: (
        "There's a quiet mismatch — progress is named in language, "
        "while the older texture is still surfacing.  If natural, you "
        "MAY (one clause max) acknowledge that growth and an unfinished "
        "thread can both be present.  Do NOT minimise the progress."
    ),
}


_FORUM_BLOCK_TEMPLATES: Dict[str, str] = {
    T_FORUM_OPEN_VS_AVOID: (
        "The room appears to hold a tension between stated openness "
        "and how difficult conversations actually move.  If it fits, "
        "name this as the field carrying BOTH at once.  Do NOT name "
        "people.  Do NOT call it avoidance."
    ),
    T_FORUM_DIRECT_VS_HUMOUR: (
        "There seems to be a pattern where pressure rises and then "
        "softens through humour or lightness before reaching a "
        "resolution.  You MAY reflect this as a field characteristic "
        "(one short observation), without judgement and without "
        "naming anyone."
    ),
    T_FORUM_FLAT_VS_RIGID: (
        "There may be a mismatch between stated equality and how "
        "responsibility / authority actually concentrates in the room.  "
        "Speak of this as field STRUCTURE, never as a person's fault."
    ),
}


def build_contradiction_system_block(payload: Optional[Dict[str, Any]]) -> str:
    if not payload or not isinstance(payload, dict):
        return ""
    if not payload.get("surfaced"):
        return ""
    types: List[str] = payload.get("types") or []
    if not types:
        return ""
    # Pick the highest-scored type to surface (one thread per turn).
    type_scores = payload.get("type_scores") or []
    chosen_type = None
    if type_scores:
        type_scores_sorted = sorted(
            type_scores, key=lambda t: t.get("score", 0), reverse=True
        )
        chosen_type = type_scores_sorted[0].get("type")
    if not chosen_type:
        chosen_type = types[0]

    if payload.get("scope") == "forum":
        line = _FORUM_BLOCK_TEMPLATES.get(chosen_type)
    else:
        line = _INDIVIDUAL_BLOCK_TEMPLATES.get(chosen_type)
    if not line:
        return ""

    softened_note = ""
    if payload.get("softened_by_reflection"):
        softened_note = (
            "  Recent micro-acknowledgements suggest the charge here is "
            "easing — keep the tone correspondingly light.  "
        )

    return (
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"CONTRADICTION-INTELLIGENCE — soft surface (level={payload.get('level')})\n"
        "Frame as human tension, NEVER deceit or denial.  At most ONE "
        "short clause referencing this per response, and only if the "
        "user's current message naturally invites it.  Probabilistic "
        "language only ('may', 'can', 'seems', 'part of this').\n"
        f"{line}{softened_note}\n"
        "ABSOLUTELY FORBIDDEN tokens: 'you are in denial', 'hypocrite', "
        "'lying to yourself', 'the truth is', 'gotcha', 'inconsistency', "
        "'contradiction detected'.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def build_contradiction_debug(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not payload or not isinstance(payload, dict):
        return {"marker": MARKER, "level": LEVEL_LOW, "surfaced": False}
    return {
        "marker": MARKER,
        "scope": payload.get("scope"),
        "contradiction_level": payload.get("level"),
        "contradiction_types": list(payload.get("types") or []),
        "surfaced": bool(payload.get("surfaced")),
        "softened_by_reflection": bool(payload.get("softened_by_reflection")),
        "forum_related": bool(payload.get("forum_related")),
        "recurrence_overlap": list(payload.get("recurrence_overlap") or []),
    }


# ---------------------------------------------------------------------------
# Soft field labels (for forum_field_intelligence consumption)
# ---------------------------------------------------------------------------


_FORUM_FIELD_LABEL: Dict[str, str] = {
    T_FORUM_OPEN_VS_AVOID: "openness-with-avoidance",
    T_FORUM_DIRECT_VS_HUMOUR: "softened-directness",
    T_FORUM_FLAT_VS_RIGID: "stability-with-friction",
}


def build_field_contradiction_signals(payload: Optional[Dict[str, Any]]) -> List[str]:
    if not payload or not payload.get("surfaced"):
        return []
    out: List[str] = []
    for t in (payload.get("types") or []):
        lbl = _FORUM_FIELD_LABEL.get(t)
        if lbl and lbl not in out:
            out.append(lbl)
    return out[:2]


# ---------------------------------------------------------------------------
# Evidence-drawer line (field language only)
# ---------------------------------------------------------------------------


def build_evidence_contradiction_line(
    payload: Optional[Dict[str, Any]],
) -> Optional[str]:
    if not payload or not payload.get("surfaced"):
        return None
    if payload.get("scope") == "forum":
        return "The room may be balancing honesty with caution."
    return "Some signals appear mixed or unresolved lately."
