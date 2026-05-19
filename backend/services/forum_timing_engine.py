"""
Forum Timing Engine  (forum-topology-and-timing-v1)
===================================================

Synthesises collective TIMING / TRANSIT pressure across the forum's
members into BEHAVIOURAL field-states.  Never exposes astrology jargon.

Output: 1 dominant field-state, optionally 1 secondary.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


# Valid behavioural field-state vocabulary.
VALID_FIELD_STATES: List[str] = [
    "stabilizing",
    "transitional",
    "pressured",
    "clarifying",
    "reconnecting",
    "fragmenting",
    "emotionally_opening",
    "protective",
    "future_oriented",
    "reality_confronting",
]


# Map of high-level signal buckets → field state hints + soft phrases.
_SIGNAL_TO_STATE: Dict[str, Dict[str, Any]] = {
    "structural_pressure": {
        "state": "reality_confronting",
        "phrase": "old structures are becoming harder to maintain",
    },
    "transition": {
        "state": "transitional",
        "phrase": "several people appear to be mid-transition",
    },
    "destabilization": {
        "state": "fragmenting",
        "phrase": "the field is carrying real instability",
    },
    "future_pull": {
        "state": "future_oriented",
        "phrase": "attention seems to be moving toward what's next",
    },
    "softening": {
        "state": "emotionally_opening",
        "phrase": "something in the field feels less guarded",
    },
    "clarity": {
        "state": "clarifying",
        "phrase": "old confusion seems to be loosening",
    },
    "stabilizing": {
        "state": "stabilizing",
        "phrase": "the field seems to be settling",
    },
    "protective": {
        "state": "protective",
        "phrase": "the field feels protective right now",
    },
    "reconnecting": {
        "state": "reconnecting",
        "phrase": "older threads seem to be reweaving",
    },
    "pressured": {
        "state": "pressured",
        "phrase": "the field is carrying real weight",
    },
}


# ---------------------------------------------------------------------------
# Signal extractors — keep them defensive; missing data → no signal.
# ---------------------------------------------------------------------------


async def _collect_member_signals(db, *, member_ids: List[str]) -> Dict[str, int]:
    """
    Walk each member's data and count behavioural signals.  Keep this
    intentionally lightweight — we never need full astrology timeline
    parsing.  Heuristics tuned to existing collections we already have.
    """
    counts: Dict[str, int] = {k: 0 for k in _SIGNAL_TO_STATE.keys()}
    if not member_ids:
        return counts

    now = datetime.now(timezone.utc)
    recent = now - timedelta(days=14)

    # 1. Longitudinal pattern memory — strong work_exhaustion or
    #    structural patterns add structural_pressure / pressured.
    structural_pattern_keys = {
        "work_exhaustion", "career_direction",
        "authority_conflict", "control_pattern",
        "shutdown_pattern",
    }
    transition_keys = {"identity_question", "career_direction", "grief_processing"}
    softening_evidence = 0
    pressure_evidence = 0
    transition_evidence = 0
    try:
        cursor = db.longitudinal_pattern_memory.find({"user_id": {"$in": member_ids}})
        async for row in cursor:
            pk = row.get("pattern_key", "")
            occ = int(row.get("occurrence_count", 0) or 0)
            growth = int(row.get("growth_shifts_count", 0) or 0)
            peak = (row.get("peak_intensity") or "").upper()
            if pk in structural_pattern_keys and occ >= 2:
                pressure_evidence += 1
                if peak in ("DIRECT", "CONFRONTING"):
                    counts["structural_pressure"] += 1
            if pk in transition_keys and occ >= 2:
                transition_evidence += 1
            if growth >= 1:
                softening_evidence += 1
    except Exception:
        pass

    if pressure_evidence >= 1:
        counts["pressured"] += pressure_evidence
    if transition_evidence >= 1:
        counts["transition"] += transition_evidence
    if softening_evidence >= 1:
        counts["softening"] += softening_evidence

    # 2. Micro-reflections — recent growth labels feed softening /
    #    clarity; recent resistance feeds protective / pressured.
    try:
        cursor = db.micro_reflections.find({
            "user_id": {"$in": member_ids},
            "ts": {"$gte": recent},
        })
        async for r in cursor:
            lbl = r.get("label")
            tex = r.get("texture")
            if lbl in ("changed", "less_intense") or tex in ("softer", "open"):
                counts["softening"] += 1
            if tex == "clear" or lbl == "true_lately":
                counts["clarity"] += 1
            if lbl == "resisting" or tex in ("stuck", "pressured", "tense"):
                counts["protective"] += 1
            if lbl == "changed":
                counts["transition"] += 1
    except Exception:
        pass

    # 3. Astrology — look only at heavy-signal fields if present, never
    #    exposing the source.  We expect chart docs may have
    #    `transits_summary` or `current_transit_pressure` keys; if not
    #    found, just skip.
    try:
        cursor = db.charts.find({"user_id": {"$in": member_ids}})
        async for chart in cursor:
            astro = chart.get("astrology") or {}
            transits = astro.get("current_transits") or astro.get("transits_summary") or {}
            if isinstance(transits, dict):
                if transits.get("saturn_pressure") or transits.get("structure_pressure"):
                    counts["structural_pressure"] += 1
                if transits.get("uranus_disruption") or transits.get("destabilizing"):
                    counts["destabilization"] += 1
                if transits.get("jupiter_expansion") or transits.get("future_pull"):
                    counts["future_pull"] += 1
                if transits.get("neptune_softening") or transits.get("opening"):
                    counts["softening"] += 1
    except Exception:
        pass

    return counts


async def synthesize_timing_state(
    db,
    *,
    member_ids: List[str],
) -> Dict[str, Any]:
    """
    Compose the timing engine output.  Returns:
      {
        marker, dominant_state, secondary_state,
        dominant_phrase, secondary_phrase,
        signal_counts, member_count,
      }
    Either / both states may be None when signals are insufficient.
    """
    counts = await _collect_member_signals(db, member_ids=member_ids)
    # Rank the signals by raw count.
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ranked = [(k, v) for (k, v) in ranked if v > 0]

    dominant_state: Optional[str] = None
    dominant_phrase: Optional[str] = None
    secondary_state: Optional[str] = None
    secondary_phrase: Optional[str] = None

    if ranked:
        top_key = ranked[0][0]
        dominant_state = _SIGNAL_TO_STATE[top_key]["state"]
        dominant_phrase = _SIGNAL_TO_STATE[top_key]["phrase"]
        if len(ranked) >= 2 and ranked[1][1] >= max(1, ranked[0][1] // 2):
            sec_key = ranked[1][0]
            sec_state = _SIGNAL_TO_STATE[sec_key]["state"]
            if sec_state != dominant_state:
                secondary_state = sec_state
                secondary_phrase = _SIGNAL_TO_STATE[sec_key]["phrase"]

    return {
        "marker": "forum-topology-and-timing-v1",
        "dominant_state": dominant_state,
        "secondary_state": secondary_state,
        "dominant_phrase": dominant_phrase,
        "secondary_phrase": secondary_phrase,
        "signal_counts": counts,
        "member_count": len(member_ids),
    }
