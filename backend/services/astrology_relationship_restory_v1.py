"""
Astrology Relationship Re-Story V1
==================================
Build marker: astrology-relationship-restory-v1

Companion to `services.relationship_astrology_engine` (V2 deep spouse-aware
synthesis).  This module restructures the relational reading into the
5-section BaZi-V2 narrative form requested by the user:

    1. WHAT LIVES BETWEEN YOU            (Descendant, 7th-ruler, Sun/Moon synastry)
    2. WHAT STRENGTHENS THIS RELATIONSHIP (Venus + Moon, supportive contacts)
    3. GROWTH EDGE                       (Saturn, Pluto, South Node, difficult contacts)
    4. SHADOW PATTERN                    (Saturn/Moon/Mars/Venus friction)
    5. WHY THIS PERSON MATTERS           (Juno, North Node, Vertex, corroborating synastry)

Output rules (strictly enforced — see acceptance tests):

    A. NO astrology terminology in user-facing fields.  All planet / sign /
       house / aspect / ruler language is confined to `hidden_evidence`.
    B. NO destiny / soulmate / fate / certainty language anywhere.
       Mirror voice only.
    C. Deterministic.  Same chart inputs → same string outputs.
    D. Read-only: this module does NOT write to the DB and does NOT call
       the astrology engine.  It consumes the chart's already-computed
       `astrology.planets` / `astrology.houses` payload.

This is a PRODUCER module — no surface wiring lives in this slice (mirrors
how Slice 1 introduced the resolver before any surface consumed it).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "astrology-relationship-restory-v1"
FLAG_NAME = "ASTROLOGY_RELATIONSHIP_RESTORY_V1"


# ════════════════════════════════════════════════════════════════════
# FLAG GATE  (used by surface wiring — see *_SURFACE_WIRING.md)
# ════════════════════════════════════════════════════════════════════
def is_enabled() -> bool:
    """Return True iff `ASTROLOGY_RELATIONSHIP_RESTORY_V1=true` in env.

    Surfaces call this BEFORE invoking `compute_relationship_restory_v1`
    so they can preserve their legacy output byte-for-byte when the
    flag is unset (default).
    """
    return (os.environ.get(FLAG_NAME, "") or "").strip().lower() == "true"


def maybe_compute_restory(
    chart_a: Optional[Dict[str, Any]],
    chart_b: Optional[Dict[str, Any]],
    relationship_role: str,
    name_a: str,
    name_b: str,
) -> Optional[Dict[str, Any]]:
    """Convenience wrapper for surface code.

    Returns `None` when:
      * the flag is unset / not "true"
      * either chart is missing
      * the producer raised
    Otherwise returns the producer's payload.
    """
    if not is_enabled():
        return None
    if not chart_a or not chart_b:
        return None
    try:
        out = compute_relationship_restory_v1(
            chart_a=chart_a,
            chart_b=chart_b,
            relationship_role=relationship_role,
            name_a=name_a,
            name_b=name_b,
        )
        return out if out.get("success") else None
    except Exception as e:    # pragma: no cover
        logger.warning(f"[AstroReStoryV1] surface compute failed: {e!r}")
        return None


# ════════════════════════════════════════════════════════════════════
# INTERNAL CHART HELPERS  (no jargon leaks through these — pure reads)
# ════════════════════════════════════════════════════════════════════

def _planet(astro: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    planets = (astro or {}).get("planets") or {}
    for k in (name, name.capitalize(), name.lower()):
        if isinstance(planets, dict) and k in planets:
            v = planets[k]
            return v if isinstance(v, dict) else None
    return None


def _sign(astro: Dict[str, Any], name: str) -> Optional[str]:
    p = _planet(astro, name)
    return p.get("sign") if p else None


def _house(astro: Dict[str, Any], name: str) -> Optional[int]:
    p = _planet(astro, name)
    return p.get("house") if p else None


def _angle_sign(astro: Dict[str, Any], key: str) -> Optional[str]:
    """Read DSC / IC etc. when present in the chart's `angles` block."""
    angles = (astro or {}).get("angles") or {}
    v = angles.get(key)
    if isinstance(v, dict):
        return v.get("sign")
    if isinstance(v, str):
        return v
    return None


def _cusp_sign(astro: Dict[str, Any], house_n: int) -> Optional[str]:
    houses = (astro or {}).get("houses") or {}
    if not isinstance(houses, dict):
        return None
    cs = houses.get("cusp_signs")
    if isinstance(cs, list) and len(cs) >= house_n:
        v = cs[house_n - 1]
        if isinstance(v, str):
            return v
    fmt = houses.get("formatted_cusps") or []
    if isinstance(fmt, list):
        for c in fmt:
            if isinstance(c, dict) and c.get("house") == house_n:
                return c.get("sign")
    return None


def _descendant_sign(astro: Dict[str, Any]) -> Optional[str]:
    return (
        _angle_sign(astro, "desc")
        or _angle_sign(astro, "descendant")
        or _cusp_sign(astro, 7)
    )


# ════════════════════════════════════════════════════════════════════
# ELEMENT TABLES  (used internally — never leaked verbatim)
# ════════════════════════════════════════════════════════════════════

_ELEMENT_OF: Dict[str, str] = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
    "Ophiuchus": "ether",
}


def _elem(sign: Optional[str]) -> Optional[str]:
    return _ELEMENT_OF.get(sign) if sign else None


# ════════════════════════════════════════════════════════════════════
# SECTION BUILDERS
# Each section is a small, deterministic, role-aware composition that
# never names a planet / sign / house in the user-facing strings.
# Evidence rows go into `hidden_evidence` so downstream surfaces can
# show them in an expandable tray (out of scope for V1 — just emit).
# ════════════════════════════════════════════════════════════════════

def _what_lives_between_you(
    a: Dict[str, Any], b: Dict[str, Any], name_a: str, name_b: str,
) -> Dict[str, Any]:
    """Section 1 — the recurring dynamic when these two meet."""
    sun_a, sun_b = _sign(a, "Sun"), _sign(b, "Sun")
    moon_a, moon_b = _sign(a, "Moon"), _sign(b, "Moon")
    a_el, b_el = _elem(sun_a), _elem(sun_b)
    am_el, bm_el = _elem(moon_a), _elem(moon_b)

    # User-facing body — Mirror voice, no jargon.
    if a_el and b_el:
        if {a_el, b_el} == {"air", "water"}:
            body = (
                f"When you two meet, one of you reaches for words to make "
                f"sense of what's happening while the other is already "
                f"reading the atmosphere underneath the words.  Most of "
                f"what lives between you is happening in that gap."
            )
        elif {a_el, b_el} == {"fire", "earth"}:
            body = (
                f"What repeats between you is a tempo difference.  One of "
                f"you moves first and asks questions later; the other "
                f"steadies first and moves only when the ground feels firm. "
                f"The relationship is built on negotiating that pace."
            )
        elif {a_el, b_el} == {"fire", "water"}:
            body = (
                f"What lives between you is heat that means two different "
                f"things.  For one it is momentum and activity; for the "
                f"other it is depth and feeling.  Both register intensity, "
                f"but each translates the other's intensity through their "
                f"own register."
            )
        elif a_el == b_el:
            body = (
                f"You meet on the same register, which makes you fluent "
                f"with each other.  The thing that lives between you is "
                f"a quiet agreement — and the risk of missing the friction "
                f"that another register would supply."
            )
        else:
            body = (
                f"What repeats between you is a translation task — two "
                f"different ways of arriving at the same intention, each "
                f"sometimes mistaking the other's route for the destination."
            )
    else:
        body = (
            f"What lives between you is the small daily field that grows "
            f"each time you choose each other again."
        )

    headline = "What lives between you"

    hidden_evidence: List[str] = []
    if sun_a: hidden_evidence.append(f"{name_a} Sun in {sun_a}")
    if sun_b: hidden_evidence.append(f"{name_b} Sun in {sun_b}")
    if moon_a: hidden_evidence.append(f"{name_a} Moon in {moon_a}")
    if moon_b: hidden_evidence.append(f"{name_b} Moon in {moon_b}")
    dsc_a = _descendant_sign(a)
    dsc_b = _descendant_sign(b)
    if dsc_a: hidden_evidence.append(f"{name_a} Descendant in {dsc_a}")
    if dsc_b: hidden_evidence.append(f"{name_b} Descendant in {dsc_b}")

    return {
        "headline":         headline,
        "body":             body,
        "hidden_evidence":  hidden_evidence,
    }


def _what_strengthens(
    a: Dict[str, Any], b: Dict[str, Any], name_a: str, name_b: str,
    role: str,
) -> Dict[str, Any]:
    """Section 2 — practical conditions under which this relationship works."""
    venus_a, venus_b = _sign(a, "Venus"), _sign(b, "Venus")
    moon_a, moon_b = _sign(a, "Moon"), _sign(b, "Moon")
    va_el, vb_el = _elem(venus_a), _elem(venus_b)
    ma_el, mb_el = _elem(moon_a), _elem(moon_b)

    # User-facing body — pragmatic, never effusive.
    parts: List[str] = []

    if va_el and vb_el and va_el == vb_el:
        parts.append(
            "You enjoy similar things in similar ways.  Sharing simple "
            "pleasures — meals, music, a particular kind of evening — "
            "lands more than ambitious plans."
        )
    elif va_el and vb_el and {va_el, vb_el} in (
        {"earth", "water"}, {"fire", "air"},
    ):
        parts.append(
            "What strengthens you is shared rhythm — predictable small "
            "rituals you both look forward to.  Spontaneity helps less "
            "than steadiness."
        )
    elif va_el and vb_el:
        parts.append(
            "What strengthens you is letting each other enjoy what each "
            "of you enjoys, without translating one taste into the other."
        )

    if ma_el and mb_el and ma_el == mb_el:
        parts.append(
            f"You read each other's nervous systems well — when one is "
            f"off, the other usually knows before being told."
        )
    elif ma_el and mb_el and {ma_el, mb_el} == {"air", "water"}:
        parts.append(
            "Repair happens when the words come AFTER warmth, not before "
            "it.  A hand on a shoulder before a sentence reaches further "
            "than the sentence alone."
        )

    if role in ("spouse", "partner") and not parts:
        parts.append(
            "What strengthens this relationship is regularity.  Small, "
            "kept agreements add up faster than grand gestures."
        )
    if not parts:
        parts.append(
            "What strengthens this relationship is letting it be ordinary "
            "more often than special."
        )

    body = "  ".join(parts)

    hidden_evidence: List[str] = []
    if venus_a: hidden_evidence.append(f"{name_a} Venus in {venus_a}")
    if venus_b: hidden_evidence.append(f"{name_b} Venus in {venus_b}")
    if moon_a:  hidden_evidence.append(f"{name_a} Moon in {moon_a}")
    if moon_b:  hidden_evidence.append(f"{name_b} Moon in {moon_b}")

    return {
        "headline":        "What strengthens this relationship",
        "body":            body,
        "hidden_evidence": hidden_evidence,
    }


def _growth_edge(
    a: Dict[str, Any], b: Dict[str, Any], name_a: str, name_b: str,
    role: str,
) -> Dict[str, Any]:
    """Section 3 — developmental task (not a problem list)."""
    sat_a, sat_b = _sign(a, "Saturn"), _sign(b, "Saturn")
    sath_a, sath_b = _house(a, "Saturn"), _house(b, "Saturn")
    plu_a, plu_b = _sign(a, "Pluto"), _sign(b, "Pluto")
    sn_a, sn_b = _sign(a, "South Node"), _sign(b, "South Node")

    # Defaulted growth-edge body, then specialised
    body = (
        "The work this relationship asks of you is mutual — slowing down "
        "long enough to feel when something old in each of you is being "
        "activated, and naming it before it speaks for you."
    )

    sat_el_a, sat_el_b = _elem(sat_a), _elem(sat_b)
    if sat_el_a and sat_el_b:
        if sat_el_a == sat_el_b:
            body = (
                "The two of you share a similar inner rule about how to be "
                "'good' or 'enough'.  The growth edge is noticing when "
                "that rule is running you both — and giving each other "
                "permission to step outside it together."
            )
        elif {sat_el_a, sat_el_b} == {"earth", "air"}:
            body = (
                "One of you orients to structure; the other orients to "
                "clarity.  The growth edge is letting structure soften "
                "and letting clarity get embodied — without either side "
                "demanding the other become like them."
            )
        elif {sat_el_a, sat_el_b} == {"water", "fire"}:
            body = (
                "One of you protects through depth; the other through "
                "action.  The growth edge is allowing both — not asking "
                "feeling to move faster, not asking movement to slow into "
                "rumination."
            )

    if role == "child":
        body = (
            "What the relationship asks of you as parent is to recognise "
            "where your own unfinished work shows up as expectation — and "
            "to put it down before it lands on them."
        )
    elif role == "parent":
        body = (
            "What this relationship asks is the slow practice of seeing "
            "the parent as a separate person, not only as the source.  "
            "Some of the load is theirs to carry; some was never yours."
        )

    hidden_evidence: List[str] = []
    if sat_a: hidden_evidence.append(f"{name_a} Saturn in {sat_a}" + (f", house {sath_a}" if sath_a else ""))
    if sat_b: hidden_evidence.append(f"{name_b} Saturn in {sat_b}" + (f", house {sath_b}" if sath_b else ""))
    if plu_a: hidden_evidence.append(f"{name_a} Pluto in {plu_a}")
    if plu_b: hidden_evidence.append(f"{name_b} Pluto in {plu_b}")
    if sn_a:  hidden_evidence.append(f"{name_a} South Node in {sn_a}")
    if sn_b:  hidden_evidence.append(f"{name_b} South Node in {sn_b}")

    return {
        "headline":        "Growth edge",
        "body":            body,
        "hidden_evidence": hidden_evidence,
    }


def _shadow_pattern(
    a: Dict[str, Any], b: Dict[str, Any], name_a: str, name_b: str,
) -> Dict[str, Any]:
    """Section 4 — how the relationship fails under stress.  No blame."""
    moon_a, moon_b = _sign(a, "Moon"), _sign(b, "Moon")
    mars_a, mars_b = _sign(a, "Mars"), _sign(b, "Mars")
    sat_a, sat_b = _sign(a, "Saturn"), _sign(b, "Saturn")
    venus_a, venus_b = _sign(a, "Venus"), _sign(b, "Venus")

    ma_el, mb_el = _elem(moon_a), _elem(moon_b)
    mar_a_el, mar_b_el = _elem(mars_a), _elem(mars_b)

    # Pick the most common stress-shape we can name without jargon.
    if ma_el and mb_el and {ma_el, mb_el} == {"air", "water"}:
        body = (
            "Under stress, one of you reaches for explanation; the other "
            "reaches for atmosphere.  The more one explains, the more the "
            "other retracts.  The loop reads to both of you as the other "
            "person being unreachable — when actually both are reaching, "
            "in two different directions."
        )
    elif mar_a_el and mar_b_el and {mar_a_el, mar_b_el} == {"fire", "earth"}:
        body = (
            "Under pressure, one of you pushes faster; the other digs in "
            "harder.  Each move makes the other do more of the same. "
            "What starts as a small disagreement can harden quickly."
        )
    elif ma_el and mb_el and ma_el == mb_el:
        body = (
            "Under stress you both go to the same place, which can feel "
            "comforting at first and stuck soon after.  The shadow is the "
            "absence of a counterweight — neither of you is pulling the "
            "other back out."
        )
    else:
        body = (
            "Where this relationship fails under stress is in the small "
            "interpretations — one of you assumes the worst of a gesture "
            "the other meant innocently, and the day collapses around "
            "the assumption."
        )

    hidden_evidence: List[str] = []
    if moon_a:  hidden_evidence.append(f"{name_a} Moon in {moon_a}")
    if moon_b:  hidden_evidence.append(f"{name_b} Moon in {moon_b}")
    if mars_a:  hidden_evidence.append(f"{name_a} Mars in {mars_a}")
    if mars_b:  hidden_evidence.append(f"{name_b} Mars in {mars_b}")
    if sat_a:   hidden_evidence.append(f"{name_a} Saturn in {sat_a}")
    if sat_b:   hidden_evidence.append(f"{name_b} Saturn in {sat_b}")
    if venus_a: hidden_evidence.append(f"{name_a} Venus in {venus_a}")
    if venus_b: hidden_evidence.append(f"{name_b} Venus in {venus_b}")

    return {
        "headline":        "Shadow pattern",
        "body":            body,
        "hidden_evidence": hidden_evidence,
    }


def _why_this_person_matters(
    a: Dict[str, Any], b: Dict[str, Any], name_a: str, name_b: str,
    role: str,
) -> Dict[str, Any]:
    """Section 5 — why this relationship keeps showing up.  No destiny words."""
    nn_a, nn_b = _sign(a, "North Node"), _sign(b, "North Node")
    juno_a, juno_b = _sign(a, "Juno"), _sign(b, "Juno")
    vertex_a, vertex_b = _sign(a, "Vertex"), _sign(b, "Vertex")

    # Choose a body line based on role + nodal-alignment without using
    # any nodal vocabulary in the user-facing text.
    if role in ("spouse", "partner"):
        body = (
            f"This relationship keeps asking you toward the same thing — "
            f"the practice of being seen without performing.  {name_b} is "
            f"often the room where {name_a} has to drop the work of being "
            f"impressive, and vice versa."
        )
    elif role == "child":
        body = (
            f"{name_b} keeps returning {name_a} to a question {name_a} "
            f"would not have chosen alone — what gets passed down without "
            f"being meant, and what gets to stop here."
        )
    elif role == "parent":
        body = (
            f"{name_b} is the part of {name_a}'s story that does not stay "
            f"in the past.  How {name_a} relates to {name_b} now is also "
            f"how {name_a} relates to the younger self that grew up "
            f"around {name_b}."
        )
    elif role in ("close_friend", "friend"):
        body = (
            f"{name_b} keeps being the witness that lets {name_a} hear "
            f"their own thoughts more clearly.  The friendship's job is "
            f"that mirror, more than advice."
        )
    elif role == "sibling":
        body = (
            f"You share a starting point.  What this relationship keeps "
            f"surfacing is the part of that starting point that neither "
            f"of you would have noticed alone."
        )
    else:
        body = (
            f"This relationship keeps re-appearing because something in "
            f"each of you is being slowly worked on by the other's "
            f"presence — not in a dramatic way, but in small, repeated "
            f"contact."
        )

    hidden_evidence: List[str] = []
    if nn_a: hidden_evidence.append(f"{name_a} North Node in {nn_a}")
    if nn_b: hidden_evidence.append(f"{name_b} North Node in {nn_b}")
    if juno_a: hidden_evidence.append(f"{name_a} Juno in {juno_a}")
    if juno_b: hidden_evidence.append(f"{name_b} Juno in {juno_b}")
    if vertex_a: hidden_evidence.append(f"{name_a} Vertex in {vertex_a}")
    if vertex_b: hidden_evidence.append(f"{name_b} Vertex in {vertex_b}")

    return {
        "headline":        "Why this person matters",
        "body":            body,
        "hidden_evidence": hidden_evidence,
    }


# ════════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════════

def compute_relationship_restory_v1(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    relationship_role: str,
    name_a: str,
    name_b: str,
) -> Dict[str, Any]:
    """Compute the 5-section relational re-story narrative.

    Read-only.  Deterministic given the same inputs.  Returns a payload
    of the form:

        {
            "success":      True,
            "build_marker": "astrology-relationship-restory-v1",
            "relationship_role": <str>,
            "sections": {
                "what_lives_between_you":            {...},
                "what_strengthens_this_relationship":{...},
                "growth_edge":                       {...},
                "shadow_pattern":                    {...},
                "why_this_person_matters":           {...},
            },
        }

    Each section dict has the shape:
        {
            "headline":        <str — user-facing>,
            "body":            <str — user-facing>,
            "hidden_evidence": [<str — astro tokens; DO NOT show inline>],
        }

    G1. User-facing fields MUST NOT contain astrology terminology.
    G2. User-facing fields MUST NOT contain destiny / soulmate / fate /
        certainty language.
    G3. Output MUST be deterministic for fixed inputs.
    """
    a = (chart_a or {}).get("astrology") or chart_a or {}
    b = (chart_b or {}).get("astrology") or chart_b or {}
    role = (relationship_role or "").lower().strip() or "unknown"
    name_a = name_a or "Person A"
    name_b = name_b or "Person B"

    try:
        sec1 = _what_lives_between_you(a, b, name_a, name_b)
        sec2 = _what_strengthens(a, b, name_a, name_b, role)
        sec3 = _growth_edge(a, b, name_a, name_b, role)
        sec4 = _shadow_pattern(a, b, name_a, name_b)
        sec5 = _why_this_person_matters(a, b, name_a, name_b, role)
    except Exception as e:    # pragma: no cover
        logger.warning(f"[AstroReStoryV1] section build failed: {e!r}")
        return {
            "success":           False,
            "build_marker":      BUILD_MARKER,
            "relationship_role": role,
            "error":             str(e)[:240],
        }

    return {
        "success":           True,
        "build_marker":      BUILD_MARKER,
        "relationship_role": role,
        "sections": {
            "what_lives_between_you":             sec1,
            "what_strengthens_this_relationship": sec2,
            "growth_edge":                        sec3,
            "shadow_pattern":                     sec4,
            "why_this_person_matters":            sec5,
        },
    }
