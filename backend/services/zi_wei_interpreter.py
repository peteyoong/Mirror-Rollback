"""
Zi Wei / Purple Star Interpreter — v1
=====================================

Build marker: zi-wei-master-v1

This is intentionally NOT a full classical Zi Wei Dou Shu calculator.
v1 produces a STRUCTURAL-BEHAVIOURAL profile from the user's birth date
and (optional) birth time, mapping to the 12-palace anchor set plus a
small set of major stars and transformations.  The lens uses this to
ground its conversational reads in BEHAVIOURAL language — never as a
fortune-telling output.

Two design rules baked in here:

  1. NO classical jargon escapes this module into user-facing text.
     The interpreter emits structured JSON; the lens registry's
     voice_prompt translates it into behavioural language.

  2. Outputs are STABLE per birth date+time so conversational
     continuity holds across turns.  The deeper classical Ziwei
     algorithm is deferred to v2 — the v1 model is deterministic and
     plausible but acknowledges itself as a structural profile, not
     a predictive chart.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional


# 12 palaces — fixed wheel anchors.
PALACES: List[str] = [
    "Life", "Siblings", "Marriage", "Children",
    "Wealth", "Health", "Travel", "Friends",
    "Career", "Property", "Mental/Spiritual", "Parents",
]

# 14 major stars supported in v1.
MAJOR_STARS: List[str] = [
    "Zi Wei", "Tian Fu", "Tan Lang", "Qi Sha", "Po Jun", "Wu Qu",
    "Tian Xiang", "Tian Ji", "Tai Yang", "Tai Yin", "Lian Zhen",
    "Ju Men", "Tian Tong", "Tian Liang",
]

# 4 transformations.
TRANSFORMATIONS: List[str] = ["Hua Lu", "Hua Quan", "Hua Ke", "Hua Ji"]


# Behavioural translation per major star (structural strategist tone).
_STAR_BEHAVIOUR: Dict[str, str] = {
    "Zi Wei":     "tends to organise around dignity and quiet authority; responsible for the room whether or not asked to be",
    "Tian Fu":    "stabilises and protects; the steady hand under pressure",
    "Tan Lang":   "expansive, persuasive, drawn toward visibility and stimulation",
    "Qi Sha":     "decisive under pressure, comfortable cutting losses; can isolate when overwhelmed",
    "Po Jun":     "breaks structures that no longer fit; high-friction with rigid roles",
    "Wu Qu":      "executes ruthlessly when committed; quiet around emotion",
    "Tian Xiang": "diplomatic, harmonising; takes time choosing a side",
    "Tian Ji":    "moves quickly between ideas; finds the angle others miss",
    "Tai Yang":   "external, visible, generous; uncomfortable with being unseen",
    "Tai Yin":    "internal, intuitive, attuned; conserves and waits",
    "Lian Zhen":  "intense and principled; controls itself before others",
    "Ju Men":     "questions everything; speech can land sharp before being meant that way",
    "Tian Tong":  "harmonising, slow to confront; values ease and continuity",
    "Tian Liang": "the elder voice; arrives slowly and carries weight",
}


# Behavioural framing per transformation.
_TRANSFORMATION_BEHAVIOUR: Dict[str, str] = {
    "Hua Lu":   "an area where flow is currently available — capacity exceeds demand",
    "Hua Quan": "an area where power and authority concentrate this cycle",
    "Hua Ke":   "an area where reputation, recognition or quiet credibility build",
    "Hua Ji":   "an area carrying obstruction, friction, or unfinished work",
}


# Palace → domain mapping for behavioural read.
PALACE_DOMAIN: Dict[str, str] = {
    "Life":             "identity and self-presentation",
    "Siblings":         "peer dynamics and lateral relationships",
    "Marriage":         "intimate partnership and committed coupling",
    "Children":         "creative output and what you take responsibility for",
    "Wealth":           "resource flow, capacity and abundance",
    "Health":           "vitality, body, and self-maintenance",
    "Travel":           "external movement and engagement with the world",
    "Friends":          "wider community and support network",
    "Career":           "vocation, public role, and contribution",
    "Property":         "foundation, home, and accumulated stability",
    "Mental/Spiritual": "inner life, meaning, and reflection",
    "Parents":          "authority, lineage, and inherited expectations",
}


# ---------------------------------------------------------------------------
# Stable deterministic derivation — keeps continuity across chat turns.
# ---------------------------------------------------------------------------


def _digest(seed: str) -> List[int]:
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    return list(h)


def _pick(stream: List[int], options: List[str], idx: int) -> str:
    return options[stream[idx % len(stream)] % len(options)]


def compute_zi_wei_profile(
    *,
    birth_date: Optional[str],
    birth_time: Optional[str] = None,
    birth_time_accuracy: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns the structured Zi Wei profile shape required by the lens.
    Stable per (birth_date, birth_time).  Falls back to date-only when
    time is not exact (downgraded confidence).
    """
    if not birth_date:
        return {
            "available": False,
            "marker": "zi-wei-master-v1",
            "reason": "birth_date missing",
        }

    has_exact_time = (birth_time_accuracy == "exact") and bool(birth_time)
    seed = f"zi-wei|{birth_date}|{birth_time if has_exact_time else 'no-time'}"
    stream = _digest(seed)

    # Life Palace anchor — one of the 14 stars + one of the 12 palaces.
    life_palace_name = _pick(stream, PALACES, 0)
    life_palace_star = _pick(stream, MAJOR_STARS, 1)
    body_palace_name = _pick(stream, PALACES, 2)
    body_palace_star = _pick(stream, MAJOR_STARS, 3)

    # Each palace anchored to a major star.
    palaces: List[Dict[str, Any]] = []
    for i, pname in enumerate(PALACES):
        star = MAJOR_STARS[(stream[(4 + i) % len(stream)] + i) % len(MAJOR_STARS)]
        palaces.append({
            "palace": pname,
            "domain": PALACE_DOMAIN[pname],
            "primary_star": star,
            "behavioural_signal": _STAR_BEHAVIOUR.get(star, ""),
        })

    major_stars_used = sorted({p["primary_star"] for p in palaces})

    # Transformations — distribute across 4 random palaces.
    trans: List[Dict[str, Any]] = []
    used_palaces = set()
    for i, t in enumerate(TRANSFORMATIONS):
        idx = (16 + i * 3) % len(stream)
        p_idx = stream[idx] % len(PALACES)
        # Avoid duplicate palace assignment.
        while PALACES[p_idx] in used_palaces:
            p_idx = (p_idx + 1) % len(PALACES)
        used_palaces.add(PALACES[p_idx])
        pname = PALACES[p_idx]
        trans.append({
            "transformation": t,
            "palace": pname,
            "domain": PALACE_DOMAIN[pname],
            "behavioural_signal": _TRANSFORMATION_BEHAVIOUR[t],
        })

    # Decade cycles — produce 4 anchors (each ~10y arc).
    decade_cycles = []
    for i in range(4):
        idx = (24 + i * 5) % len(stream)
        pname = PALACES[stream[idx] % len(PALACES)]
        decade_cycles.append({
            "decade_index": i,
            "anchor_palace": pname,
            "anchor_domain": PALACE_DOMAIN[pname],
        })

    # Current cycle inference — pick one of the 4 decade anchors as
    # current (stable per profile + current-decade-year).
    current_decade_idx = stream[40 % len(stream)] % 4
    current_cycle = decade_cycles[current_decade_idx]

    # Current year overlay — pick a transformation pair.
    yr_seed = stream[44 % len(stream)] % len(TRANSFORMATIONS)
    current_year_overlay = {
        "active_transformation": TRANSFORMATIONS[yr_seed],
        "affected_palace": trans[yr_seed]["palace"],
        "affected_domain": trans[yr_seed]["domain"],
    }

    # Dominant structural themes — derived from life/career/marriage anchors.
    life_p = next(p for p in palaces if p["palace"] == "Life")
    career_p = next(p for p in palaces if p["palace"] == "Career")
    marriage_p = next(p for p in palaces if p["palace"] == "Marriage")
    parents_p = next(p for p in palaces if p["palace"] == "Parents")

    dominant_patterns = [
        f"In how you present yourself, {life_p['behavioural_signal']}.",
    ]
    relationship_patterns = [
        f"In committed partnership, you {marriage_p['behavioural_signal']}.",
    ]
    work_patterns = [
        f"In your public role, you {career_p['behavioural_signal']}.",
    ]
    identity_patterns = [
        f"Around authority and inherited expectation, you {parents_p['behavioural_signal']}.",
    ]
    timing_patterns = [
        f"Right now, attention is being pulled toward {current_cycle['anchor_domain']}.",
        f"This period also carries {current_year_overlay['active_transformation']}-style movement in {current_year_overlay['affected_domain']}.",
    ]

    return {
        "available": True,
        "marker": "zi-wei-master-v1",
        "confidence": "moderate" if has_exact_time else "low",
        "life_palace": {
            "palace": "Life",
            "anchor_house": life_palace_name,
            "primary_star": life_palace_star,
            "behavioural_signal": _STAR_BEHAVIOUR.get(life_palace_star, ""),
        },
        "body_palace": {
            "palace": "Body",
            "anchor_house": body_palace_name,
            "primary_star": body_palace_star,
            "behavioural_signal": _STAR_BEHAVIOUR.get(body_palace_star, ""),
        },
        "palaces": palaces,
        "major_stars": major_stars_used,
        "supporting_stars": [],
        "transformations": trans,
        "decade_cycles": decade_cycles,
        "current_cycle": current_cycle,
        "current_year_overlay": current_year_overlay,
        "dominant_patterns": dominant_patterns,
        "relationship_patterns": relationship_patterns,
        "work_patterns": work_patterns,
        "identity_patterns": identity_patterns,
        "timing_patterns": timing_patterns,
    }


def get_or_compute_profile(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Return cached chart.zi_wei profile if present, else compute lazily."""
    chart = user_context.get("chart") or {}
    cached = chart.get("zi_wei")
    if isinstance(cached, dict) and cached.get("available"):
        return cached
    user = user_context.get("user") or {}
    return compute_zi_wei_profile(
        birth_date=user.get("birth_date") or chart.get("birth_date"),
        birth_time=user.get("birth_time") or chart.get("birth_time"),
        birth_time_accuracy=user.get("birth_time_accuracy"),
    )
