"""
Field Synthesis Engine (V8)
============================

Build marker: astrology-field-synthesis-v8

Transforms deterministic chart inputs (house inventory + ruler condition +
aspects + pressure topology) into ONE coherent FIELD narrative that
describes what an area of life FEELS like in the person's lived
experience.

This engine ELIMINATES the textbook-prose failure mode in which the LLM
falls back to:
    "the 4th house relates to home, family, and roots…"

Instead it produces deterministic field synthesis:
    foundation / instability / compensation / relational_consequence /
    evolution

The engine works for EMPTY houses too — it synthesizes via the house
ruler's condition + topology overlay rather than refusing to interpret.

Inputs:
    chart: the user's astrology dict (from db.charts)
    house_number: 1-12
    inventory_envelope: result of house_inventory_engine.build_house_inventory
                        (optional but recommended)
    topology: result of pressure_topology_engine.build_pressure_topology
              (optional)

Output: see build_field_synthesis() docstring.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "astrology-field-synthesis-v8"

_NO_ASPECTS_LINE = "    (none within orb)\n"

# ---------------------------------------------------------------------------
# House archetypal fields (NOT textbook themes — lived field words)
# ---------------------------------------------------------------------------
# Each entry is what the field FEELS like, not what it 'represents'.
HOUSE_ARCHETYPES: Dict[int, Dict[str, str]] = {
    1: {
        "field_name":      "self-arrival field",
        "core":            "how this person enters a room and what their body broadcasts before they speak",
        "stabilizer_seed": "a stable sense of one's own physical presence",
        "destab_seed":     "being mis-seen or having one's first impression rewritten by others",
    },
    2: {
        "field_name":      "ground / self-worth field",
        "core":            "what this person builds inner security on and what they treat as 'theirs'",
        "stabilizer_seed": "tangible resources they can hold or count",
        "destab_seed":     "anything that pulls the resource floor away — financial, sensory, or value-based",
    },
    3: {
        "field_name":      "thinking and immediate-environment field",
        "core":            "how thought lands, how speech becomes consequence, the texture of the immediate world",
        "stabilizer_seed": "a working language for one's own observations",
        "destab_seed":     "the sense that words have weight and can rearrange a room",
    },
    4: {
        "field_name":      "emotional foundation field",
        "core":            "the ground beneath emotional life — what gives interior safety and what feels like home",
        "stabilizer_seed": "steady emotional atmosphere, predictable interior conditions",
        "destab_seed":     "atmospheric absence — a foundation that feels procedural, muted, or emotionally unavailable",
    },
    5: {
        "field_name":      "creative force / radiance field",
        "core":            "how this person plays, takes up space, and what makes them visible to themselves",
        "stabilizer_seed": "permission to be seen taking up space",
        "destab_seed":     "performance-pressure that turns spontaneity into output",
    },
    6: {
        "field_name":      "daily routine and body discipline field",
        "core":            "how the nervous system runs the day, what small acts knit a life together",
        "stabilizer_seed": "rituals and small repeatable acts",
        "destab_seed":     "structure that becomes joyless, body that becomes a task list",
    },
    7: {
        "field_name":      "relational mirror field",
        "core":            "the one-to-one encounter — who shows up across the table and what they reveal in this person",
        "stabilizer_seed": "a partner who reflects this person back to themselves cleanly",
        "destab_seed":     "the temptation to use the other to complete what isn't yet integrated",
    },
    8: {
        "field_name":      "shared-resource / depth field",
        "core":            "what is pooled, inherited, owed, exchanged in intimacy — and what is faced when the surface drops",
        "stabilizer_seed": "trust strong enough to allow merging without losing self",
        "destab_seed":     "anything that demands trust before it has been earned",
    },
    9: {
        "field_name":      "meaning-making / horizon field",
        "core":            "how this person constructs a worldview large enough to live inside",
        "stabilizer_seed": "a working philosophy that holds during compression",
        "destab_seed":     "a meaning-frame that is too small for the actual life",
    },
    10: {
        "field_name":      "public visibility / vocation field",
        "core":            "what shape this person makes when other people see them at work in the world",
        "stabilizer_seed": "a public form that doesn't betray the interior",
        "destab_seed":     "a role taken on that the inner field cannot sustain",
    },
    11: {
        "field_name":      "collective belonging / future field",
        "core":            "where this person fits into a larger group and what they are reaching toward",
        "stabilizer_seed": "a group whose terms this person can actually meet",
        "destab_seed":     "isolation from the kind of people who would actually recognise them",
    },
    12: {
        "field_name":      "undertow / dissolved-self field",
        "core":            "what runs beneath the visible life — the residue, the unmetabolised material, the dream-floor",
        "stabilizer_seed": "a private practice that lets the undertow surface in a contained way",
        "destab_seed":     "ignoring the undertow until it overflows",
    },
}

# ---------------------------------------------------------------------------
# Modern sign rulerships (single-ruler simplification — sufficient for
# field synthesis; classical rulers can be added if needed later).
# ---------------------------------------------------------------------------
SIGN_RULER: Dict[str, str] = {
    "Aries":       "Mars",
    "Taurus":      "Venus",
    "Gemini":      "Mercury",
    "Cancer":      "Moon",
    "Leo":         "Sun",
    "Virgo":       "Mercury",
    "Libra":       "Venus",
    "Scorpio":     "Pluto",
    "Sagittarius": "Jupiter",
    "Capricorn":   "Saturn",
    "Aquarius":    "Uranus",
    "Pisces":      "Neptune",
}

# Outer planets whose hard aspects to the house ruler create
# destabilization patterns.
_OUTER_PLANETS = ("Uranus", "Neptune", "Pluto", "Saturn")
_HARD_ASPECTS = ("conjunction", "square", "opposition", "quincunx")

# What each outer planet imports as instability seed when it touches the
# house ruler.
_DESTABILIZER_BY_PLANET = {
    "Uranus":  "sudden shifts, electric interruption, the field refuses to stay still",
    "Neptune": "the field's outlines dissolve, what felt solid becomes diffuse",
    "Pluto":   "deep pressure on what the field is built on — compulsive intensity",
    "Saturn":  "the field is editing itself, narrower than the interior wants",
}

# Survival-strategy translations from topology constraints.
_SURVIVAL_STRATEGY_NARRATIVES = {
    "containment and editing": (
        "by tightening, by becoming more deliberate, by editing what is shown"
    ),
    "controlled intensity": (
        "by metering the depth that is allowed to surface, choosing what to expose"
    ),
    "overcompensating performance": (
        "by performing the missing stability — projecting the steadiness they "
        "do not yet feel"
    ),
    "withdrawal and recalibration": (
        "by stepping out of the field to reset, returning when interior conditions settle"
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ord(n: Optional[int]) -> str:
    """Return ordinal suffix string for an integer (1 → '1st', 4 → '4th')."""
    if n is None:
        return "?"
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _get_house_cusp_sign(chart: Dict[str, Any], house_number: int) -> Optional[str]:
    """Return the sign on the Nth-house cusp, e.g. 'Virgo' for Mel's 4th.

    Supports BOTH storage shapes:
      • new (True Sidereal-M migrated):
          houses.cusp_signs = ['Sagittarius', 'Capricorn', ...]  (12 entries)
      • legacy:
          houses.formatted_cusps = [{'house':1,'sign':'Cancer',...}, ...]
    """
    astro = (chart or {}).get("astrology") or {}
    houses = astro.get("houses") or {}
    if not isinstance(houses, dict):
        return None
    # New shape — flat list of sign strings, index 0 = house 1
    cusp_signs = houses.get("cusp_signs")
    if isinstance(cusp_signs, list) and len(cusp_signs) >= house_number:
        sign = cusp_signs[house_number - 1]
        if isinstance(sign, str):
            return sign
    # Legacy shape — list of dicts
    cusps_fmt = houses.get("formatted_cusps") or []
    if isinstance(cusps_fmt, list):
        for c in cusps_fmt:
            if isinstance(c, dict) and c.get("house") == house_number:
                return c.get("sign")
    return None


def _find_planet(chart: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    """Look up a planet by name in chart.astrology.planets (case-insensitive)."""
    astro = (chart or {}).get("astrology") or {}
    planets = astro.get("planets") or {}
    if isinstance(planets, dict):
        for k, v in planets.items():
            if k.lower() == name.lower():
                return v
    return None


def _planet_house(chart: Dict[str, Any], planet_name: str) -> Optional[int]:
    """Resolve which house a named planet sits in."""
    p = _find_planet(chart, planet_name)
    if not p:
        return None
    return p.get("house")


def _planet_sign(chart: Dict[str, Any], planet_name: str) -> Optional[str]:
    p = _find_planet(chart, planet_name)
    if not p:
        return None
    return p.get("sign")


def _major_aspects_to(chart: Dict[str, Any], planet_name: str,
                       max_orb: float = 6.0) -> List[Dict[str, Any]]:
    """Return aspects (from chart.astrology.aspects) involving `planet_name`,
    sorted tight-orb-first. Only includes major + quincunx within max_orb.
    """
    astro = (chart or {}).get("astrology") or {}
    aspects = astro.get("aspects") or []
    pname = planet_name.lower()
    out: List[Dict[str, Any]] = []
    for a in aspects:
        b1 = (a.get("body1") or "").lower()
        b2 = (a.get("body2") or "").lower()
        if pname not in (b1, b2):
            continue
        orb = a.get("orb") or 0
        if orb > max_orb:
            continue
        a_type = (a.get("type") or "").lower()
        if a_type not in ("conjunction", "sextile", "square", "trine",
                          "opposition", "quincunx"):
            continue
        out.append({
            "with":     a.get("body1") if b1 != pname else a.get("body2"),
            "type":     a_type,
            "orb":      round(orb, 2),
            "applying": a.get("applying", False),
        })
    out.sort(key=lambda a: a["orb"])
    return out[:8]


# ---------------------------------------------------------------------------
# Synthesis builders
# ---------------------------------------------------------------------------
def _build_destabilizer(
    house_arch: Dict[str, str],
    ruler_aspects: List[Dict[str, Any]],
    inventory_envelope: Optional[Dict[str, Any]],
) -> Tuple[str, Optional[str]]:
    """Return (destabilizer_text, destabilizing_planet_name)."""
    # If the house itself has Uranus/Pluto/Neptune/Saturn IN it → use that
    if inventory_envelope and inventory_envelope.get("objects_in_house"):
        for obj in inventory_envelope["objects_in_house"]:
            n = obj.get("name")
            if n in _OUTER_PLANETS:
                return _DESTABILIZER_BY_PLANET[n], n

    # Otherwise look for hard aspects from outer planets to the house ruler
    for asp in ruler_aspects:
        if asp["with"] in _OUTER_PLANETS and asp["type"] in _HARD_ASPECTS:
            return _DESTABILIZER_BY_PLANET[asp["with"]], asp["with"]

    # Soft outer-planet aspects still mean the field is colored by that planet
    for asp in ruler_aspects:
        if asp["with"] in _OUTER_PLANETS:
            return (
                f"the field is quietly colored by {asp['with']} — "
                f"{_DESTABILIZER_BY_PLANET[asp['with']].split(',')[0]}, "
                "less acute but present"
            ), asp["with"]

    return house_arch["destab_seed"], None


def _build_stabilizer(
    house_arch: Dict[str, str],
    ruler_name: Optional[str],
    ruler_sign: Optional[str],
    ruler_house: Optional[int],
    inventory_envelope: Optional[Dict[str, Any]],
) -> str:
    """Construct what stabilizes this field."""
    seed = house_arch["stabilizer_seed"]
    if not ruler_name or not ruler_sign:
        return seed
    # Modulate the seed with ruler-sign flavor
    sign_flavor = {
        "Aries":       "directly, by acting before deliberating",
        "Taurus":      "slowly, through what can be touched and tasted",
        "Gemini":      "through naming and re-naming what is happening",
        "Cancer":      "through atmosphere and emotional memory",
        "Leo":         "through being seen taking up space",
        "Virgo":       "through ordering, refining, and precise care",
        "Libra":       "through calibration and the consent of another",
        "Scorpio":     "through what is faced when the surface drops",
        "Sagittarius": "through scale — by widening the frame",
        "Capricorn":   "through structure, discipline, the long arc",
        "Aquarius":    "through breaking pattern, finding the outside view",
        "Pisces":      "through dissolving the edge between self and field",
    }.get(ruler_sign, "")
    if sign_flavor:
        return f"{seed} — accessed {sign_flavor}"
    return seed


def _build_compensation(
    survival_strategy: Optional[str],
    destabilizing_planet: Optional[str],
) -> str:
    """Compensation = how the person adapts to the destabilizer.
    Derived from topology survival_strategy when available."""
    if survival_strategy:
        # Try a phrase-match against the table
        for key, narrative in _SURVIVAL_STRATEGY_NARRATIVES.items():
            if key.split()[0].lower() in survival_strategy.lower():
                return narrative
        return f"by {survival_strategy.strip().rstrip('.')}"
    # Fallback by destabilizing planet
    if destabilizing_planet == "Uranus":
        return "by holding the door open for the interruption rather than fighting it"
    if destabilizing_planet == "Pluto":
        return "by metering the depth allowed to surface in any given moment"
    if destabilizing_planet == "Neptune":
        return "by attaching small concrete forms to what would otherwise dissolve"
    if destabilizing_planet == "Saturn":
        return "by carrying the editor inside, doing the narrowing themselves"
    return "by attending to what stabilizes the field before exposure"


def _build_relational_consequence(
    field_name: str,
    destabilizing_planet: Optional[str],
    survival_strategy: Optional[str],
) -> str:
    """What others experience standing close to this field."""
    if destabilizing_planet == "Uranus":
        return (
            f"others standing close to this {field_name} feel its electric edge "
            "— hard to fully predict, sometimes mistaken for distance"
        )
    if destabilizing_planet == "Pluto":
        return (
            f"others feel the gravitational weight of this {field_name} "
            "— that something is being held back, and that the held thing is alive"
        )
    if destabilizing_planet == "Neptune":
        return (
            f"others sense this {field_name} more than they see it "
            "— atmospheric, hard to pin down"
        )
    if destabilizing_planet == "Saturn":
        return (
            f"others read this {field_name} as composed, contained "
            "— and may not realise the cost of the composure"
        )
    return f"others meet this {field_name} as the version it has chosen to show"


def _build_evolution(
    house_number: int,
    dominant_dynamic: str,
    survival_strategy: Optional[str],
) -> str:
    """What the chart is reaching to integrate in this field."""
    arch = HOUSE_ARCHETYPES.get(house_number, {})
    return (
        f"the field is reaching to hold "
        f"{arch.get('stabilizer_seed', 'its center')} "
        f"WITHOUT collapsing under the destabilizer — to let the disruption "
        "in without losing the ground"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_field_synthesis(
    *,
    chart: Dict[str, Any],
    house_number: int,
    inventory_envelope: Optional[Dict[str, Any]] = None,
    topology: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return field synthesis for a given house. Works for empty houses.

    Returns:
      {
        "success": bool,
        "build_marker": "astrology-field-synthesis-v8",
        "house_number": int,
        "is_empty": bool,
        "house_sign": str,
        "ruler": str,                # e.g. "Mercury"
        "ruler_sign": str,
        "ruler_house": int,
        "ruler_aspects": [{with, type, orb, applying}, ...],
        "field_name": str,
        "dominant_dynamic": str,
        "stabilizer": str,
        "destabilizer": str,
        "destabilizing_planet": str | None,
        "survival_strategy": str | None,
        "compensation": str,
        "relational_consequence": str,
        "evolution": str,
        "emotional_experience": str,
        "synthesis_narrative": str,  # one short, opinionated prose block
        "synthesis_mode": "field",
        "textbook_mode_used": False,
      }
    """
    if not (1 <= house_number <= 12):
        return {
            "success":      False,
            "build_marker": BUILD_MARKER,
            "reason":       f"house_number out of range: {house_number}",
        }

    house_arch = HOUSE_ARCHETYPES.get(house_number, {})
    house_sign = _get_house_cusp_sign(chart, house_number)
    ruler_name = SIGN_RULER.get(house_sign) if house_sign else None
    ruler_sign = _planet_sign(chart, ruler_name) if ruler_name else None
    ruler_house = _planet_house(chart, ruler_name) if ruler_name else None
    ruler_aspects = (
        _major_aspects_to(chart, ruler_name) if ruler_name else []
    )

    is_empty = bool(
        inventory_envelope
        and not inventory_envelope.get("objects_in_house")
    )

    # Topology-driven survival strategy
    survival_strategy = None
    if topology and topology.get("success"):
        survival_strategy = topology.get("dominant_survival_strategy")
        if not survival_strategy:
            try:
                from services.pressure_topology_engine import (
                    build_narrative_constraints,
                )
                survival_strategy = build_narrative_constraints(
                    topology
                ).get("dominant_survival_strategy")
            except Exception:
                pass

    # Destabilizer (and which planet drives it)
    destabilizer_text, destab_planet = _build_destabilizer(
        house_arch, ruler_aspects, inventory_envelope,
    )

    # Stabilizer
    stabilizer_text = _build_stabilizer(
        house_arch, ruler_name, ruler_sign, ruler_house, inventory_envelope,
    )

    # Dominant dynamic — short, clean phrasing
    if destab_planet and stabilizer_text:
        dominant_dynamic = (
            f"a pull between the {house_arch['field_name'].split('/')[0].strip()} "
            f"and the disruption {destab_planet} imports"
        )
    elif inventory_envelope and inventory_envelope.get("dominant_body"):
        dominant_dynamic = (
            f"the field is set by {inventory_envelope['dominant_body']}, "
            f"{inventory_envelope.get('pressure_pattern', 'tight and definitive')}"
        )
    else:
        dominant_dynamic = (
            f"the field is read through {ruler_name} in "
            f"{ruler_sign or '?'} in the {ruler_house or '?'}{('th' if ruler_house and ruler_house > 3 else 'st' if ruler_house == 1 else 'nd' if ruler_house == 2 else 'rd' if ruler_house == 3 else '')} house"
        ) if ruler_name else "no ruler available"

    compensation = _build_compensation(survival_strategy, destab_planet)
    relational_consequence = _build_relational_consequence(
        house_arch["field_name"], destab_planet, survival_strategy,
    )
    evolution = _build_evolution(
        house_number, dominant_dynamic, survival_strategy,
    )

    # Emotional experience: short first-line that the LLM must lead with.
    if is_empty and ruler_name:
        emotional_experience = (
            f"{house_arch['core']} — in this person, it lives less through "
            f"the {_ord(house_number)} house itself (which is structurally quiet) "
            f"and more through {ruler_name} in {ruler_sign} in the "
            f"{_ord(ruler_house)} house"
            + (f", which {destabilizer_text}" if destab_planet else "")
        )
    else:
        emotional_experience = house_arch.get("core", "")
        if destab_planet:
            emotional_experience += f" — but {destabilizer_text}"

    # Synthesis narrative — the deterministic prose seed the LLM expands.
    # This is the model for the LLM's first sentence (it must NOT start
    # with "the 4th house relates to…").
    parts: List[str] = []
    if is_empty and ruler_name:
        parts.append(
            f"This {house_arch['field_name']} is structurally quiet — "
            f"no planets occupy the {_ord(house_number)} house — so its "
            f"texture is read through {ruler_name}, the ruler of "
            f"{house_sign}, currently in {ruler_sign} in the "
            f"{_ord(ruler_house) if ruler_house else '?'} house."
        )
    elif inventory_envelope and inventory_envelope.get("dominant_body"):
        dom = inventory_envelope["dominant_body"]
        parts.append(
            f"This {house_arch['field_name']} is set by {dom}, "
            f"{inventory_envelope.get('pressure_pattern', '').rstrip('.')}."
        )
    else:
        parts.append(
            f"This {house_arch['field_name']} is shaped by "
            f"{ruler_name} in {ruler_sign} in the {_ord(ruler_house)} house."
            if ruler_name else
            f"This {house_arch['field_name']} reads as quiet — no anchor "
            "body to set the texture."
        )

    if destab_planet:
        parts.append(
            f"What stabilizes it: {stabilizer_text}. "
            f"What disrupts it: {destabilizer_text}."
        )
    else:
        parts.append(f"What stabilizes it: {stabilizer_text}.")

    parts.append(f"How this person adapts: {compensation}.")
    parts.append(f"Relational consequence: {relational_consequence}.")

    synthesis_narrative = " ".join(parts)

    return {
        "success":             True,
        "build_marker":        BUILD_MARKER,
        "house_number":        house_number,
        "is_empty":            is_empty,
        "house_sign":          house_sign,
        "ruler":               ruler_name,
        "ruler_sign":          ruler_sign,
        "ruler_house":         ruler_house,
        "ruler_aspects":       ruler_aspects,
        "field_name":          house_arch.get("field_name", ""),
        "dominant_dynamic":    dominant_dynamic,
        "stabilizer":          stabilizer_text,
        "destabilizer":        destabilizer_text,
        "destabilizing_planet": destab_planet,
        "survival_strategy":   survival_strategy,
        "compensation":        compensation,
        "relational_consequence": relational_consequence,
        "evolution":           evolution,
        "emotional_experience": emotional_experience,
        "synthesis_narrative": synthesis_narrative,
        "synthesis_mode":      "field",
        "textbook_mode_used":  False,
    }


def build_field_synthesis_proof_block(synthesis: Dict[str, Any]) -> str:
    """LLM-facing system-prompt block that FORCES field synthesis output.

    The block contains:
      • the deterministic field data
      • the model first-line / synthesis narrative
      • a hard ban on textbook openings
      • the 5-part scaffold (foundation / instability / compensation /
        relational consequence / evolution)
    """
    if not synthesis or not synthesis.get("success"):
        return ""

    aspects_lines = ""
    for a in (synthesis.get("ruler_aspects") or [])[:5]:
        aspects_lines += (
            f"    - {a['with']} {a['type']} (orb {a['orb']}°"
            + (", applying" if a.get("applying") else "")
            + ")\n"
        )

    return (
        "\n=== FIELD SYNTHESIS PROOF (astrology-field-synthesis-v8) ===\n"
        f"house_number:          {synthesis['house_number']}\n"
        f"field_name:            {synthesis['field_name']}\n"
        f"house_sign_on_cusp:    {synthesis.get('house_sign')}\n"
        f"is_empty:              {synthesis['is_empty']}\n"
        f"ruler:                 {synthesis.get('ruler')} "
        f"in {synthesis.get('ruler_sign')} "
        f"in house {synthesis.get('ruler_house')}\n"
        "ruler_aspects (orb ≤ 6°):\n"
        f"{aspects_lines if aspects_lines else _NO_ASPECTS_LINE}"
        f"dominant_dynamic:      {synthesis['dominant_dynamic']}\n"
        f"stabilizer:            {synthesis['stabilizer']}\n"
        f"destabilizer:          {synthesis['destabilizer']}\n"
        f"destabilizing_planet:  {synthesis.get('destabilizing_planet')}\n"
        f"compensation:          {synthesis['compensation']}\n"
        f"relational_consequence:{synthesis['relational_consequence']}\n"
        f"evolution:             {synthesis['evolution']}\n"
        f"emotional_experience:  {synthesis['emotional_experience']}\n"
        "\n"
        "DETERMINISTIC SYNTHESIS SEED (use as the model for your first\n"
        "sentence; expand into a single coherent paragraph; do NOT\n"
        "preface with definitions or 'in astrology…'):\n"
        f"  {synthesis['synthesis_narrative']}\n"
        "\n"
        "HARD STRUCTURE — your response MUST cover all five in order,\n"
        "woven into one paragraph (no bullet headings):\n"
        "  A. FOUNDATION: what stabilizes the field\n"
        "  B. INSTABILITY: what disrupts it\n"
        "  C. COMPENSATION: how this person adapts\n"
        "  D. RELATIONAL CONSEQUENCE: how others experience the field\n"
        "  E. EVOLUTION: what the chart is reaching to integrate\n"
        "\n"
        "ABSOLUTE BANS (any of these = failed turn):\n"
        "  ✗ 'the Nth house relates to / represents…'\n"
        "  ✗ 'in astrology, the Nth house…'\n"
        "  ✗ 'this placement suggests / indicates / may mean…'\n"
        "  ✗ 'this energy', 'themes of home/family/security'\n"
        "  ✗ 'spiritual journey'\n"
        "  ✗ generic textbook house definitions\n"
        "  ✗ closing reflection question ('how does this resonate?', etc.)\n"
        "\n"
        "FIRST-SENTENCE RULE: open with the LIVED FIELD, not the label.\n"
        "Example acceptable opening: 'This person's emotional foundation\n"
        "is built around steadiness, but Uranus keeps the floor from\n"
        "settling.'\n"
        "============================================================\n"
    )


__all__ = [
    "build_field_synthesis",
    "build_field_synthesis_proof_block",
    "BUILD_MARKER",
    "HOUSE_ARCHETYPES",
    "SIGN_RULER",
]
