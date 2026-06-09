"""
Pressure Topology Engine
========================

Build marker: astrology-pressure-topology-v6

Whole-chart synthesis layer that runs ABOVE v4 object coverage and v5
house inventory. It scans the chart for REPEATING pressures — sign
repetition, house concentrations, structural-vs-impulse contradictions,
key aspects like Sun↔Saturn / Sun↔Pluto / Moon↔Saturn — and surfaces a
deterministic narrative-constraint envelope that the LLM is required to
express (not invent).

The point: the LLM stops doing "Sun in Pisces means…" and starts
expressing "you keep experiencing X as Y" — because the topology engine
already detected the X→Y pressure.

This module does NOT touch sign attribution, SVP, midpoint boundaries,
solar return math, the v4 object registry, or v5 inventory. It only
READS and SYNTHESISES.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "astrology-pressure-topology-v6"

# Bodies that carry structural weight in pressure-topology detection.
# Higher score = stronger contribution to the topology.
_BODY_WEIGHT = {
    "Sun": 10, "Moon": 10,
    "Saturn": 9, "Pluto": 9,
    "Mercury": 7, "Venus": 7, "Mars": 7,
    "Jupiter": 6,
    "Uranus": 6, "Neptune": 6,
    "Chiron": 5,
    "North Node": 7, "South Node": 7,
    "Black Moon Lilith": 5,
    "Juno": 4, "Vesta": 4, "Ceres": 4, "Pallas": 4,
}

# Sign → keyword pressure mapping (kept deterministic and brief; the LLM
# is told to use these as labels, not to elaborate textbook meanings).
_SIGN_PRESSURE = {
    "Aries":       "initiating impulse",
    "Taurus":      "stabilisation",
    "Gemini":      "verbal processing",
    "Cancer":      "containment / belonging",
    "Leo":         "self-authorship",
    "Virgo":       "precision / standards",
    "Libra":       "calibration through other",
    "Scorpio":     "control of intensity",
    "Sagittarius": "scope expansion",
    "Capricorn":   "responsibility / structure",
    "Aquarius":    "differentiation",
    "Pisces":      "permeability",
    # ophiuchus-first-class-content-v1: integration / threshold-crossing.
    "Ophiuchus":   "integration under pressure",
}

# House → life-domain pressure label (intentionally short).
_HOUSE_DOMAIN = {
    1:  "identity / how I land",
    2:  "value / what I hold",
    3:  "communication / consequence of speech",
    4:  "private self / home base",
    5:  "expression / authorship",
    6:  "labour / daily refinement",
    7:  "partnership / mirror",
    8:  "shared depth / what's withheld",
    9:  "meaning / horizon",
    10: "visibility / public role",
    11: "groups / chosen world",
    12: "hidden interior / dissolution",
}


# ---------------------------------------------------------------------------
# 1.  Signal extraction
# ---------------------------------------------------------------------------
def _planet_sign_house_list(chart: Dict[str, Any]) -> List[Tuple[str, str, Optional[int]]]:
    """Flatten the chart's planet dict into [(name, sign, house), ...].
    Includes Sun..Pluto + Chiron + Nodes + Juno (whatever is stored).
    """
    astro = (chart or {}).get("astrology") or {}
    planets = astro.get("planets") or {}
    out = []
    for name, p in planets.items():
        sign = p.get("sign")
        house = p.get("house")
        if sign:
            out.append((name, sign, house))
    return out


def _count_repetitions(items: List[Tuple[str, str, Optional[int]]]) -> Dict[str, Any]:
    """Tally weighted sign + house frequencies. Bodies count by their
    _BODY_WEIGHT so the Sun in Pisces > Juno in Pisces.
    """
    sign_score: Dict[str, float] = {}
    house_score: Dict[int, float] = {}
    sign_bodies: Dict[str, List[str]] = {}
    house_bodies: Dict[int, List[str]] = {}

    for name, sign, house in items:
        w = _BODY_WEIGHT.get(name, 3)
        sign_score[sign] = sign_score.get(sign, 0) + w
        sign_bodies.setdefault(sign, []).append(name)
        if house is not None:
            house_score[house] = house_score.get(house, 0) + w
            house_bodies.setdefault(house, []).append(name)
    return {
        "sign_score":   sign_score,
        "sign_bodies":  sign_bodies,
        "house_score":  house_score,
        "house_bodies": house_bodies,
    }


def _detect_compression(items, astro_block) -> Optional[Dict[str, Any]]:
    """Compression = Sun↔Saturn contact OR heavy Capricorn/Saturn-ruled
    weight. Cheap heuristic — Sun and Saturn in the same sign OR same
    house OR <12° apart."""
    by_name = {n: (s, h, astro_block.get(n, {})) for n, s, h in items}
    sun = by_name.get("Sun"); sat = by_name.get("Saturn")
    if not sun or not sat:
        return None
    sun_lng = (sun[2] or {}).get("longitude")
    sat_lng = (sat[2] or {}).get("longitude")
    same_sign = sun[0] == sat[0]
    same_house = sun[1] is not None and sun[1] == sat[1]
    close = (
        sun_lng is not None and sat_lng is not None
        and abs(((sun_lng - sat_lng + 180) % 360) - 180) <= 12
    )
    if same_sign or same_house or close:
        return {
            "type": "compression",
            "theme": "identity edited before it leaves the mouth — Sun moves through a Saturn filter",
            "strength": 0.85 if close else (0.75 if same_sign else 0.65),
            "signals": ["Sun↔Saturn same_sign" if same_sign else None,
                        "Sun↔Saturn same_house" if same_house else None,
                        "Sun↔Saturn ≤12°" if close else None],
        }
    return None


def _detect_pluto_pressure(items, astro_block) -> Optional[Dict[str, Any]]:
    """Pluto pressure on Sun or Moon — intensity / control / withholding."""
    by_name = {n: (s, h, astro_block.get(n, {})) for n, s, h in items}
    for target in ("Sun", "Moon"):
        t = by_name.get(target); p = by_name.get("Pluto")
        if not t or not p:
            continue
        t_lng = (t[2] or {}).get("longitude"); p_lng = (p[2] or {}).get("longitude")
        if t_lng is None or p_lng is None:
            continue
        d = abs(((t_lng - p_lng + 180) % 360) - 180)
        # orb 0-10° conjunct, also catch hard aspects within 6°
        if d <= 10:
            asp = "conjunction"
        elif abs(d - 90) <= 6:
            asp = "square"
        elif abs(d - 180) <= 8:
            asp = "opposition"
        else:
            continue
        return {
            "type": "pluto_pressure",
            "theme": f"intensity organised around {target.lower()} — control over what is shown",
            "aspect": f"{target}↔Pluto {asp}",
            "strength": 0.85 if asp == "conjunction" else 0.70,
        }
    return None


def _detect_overcompensation(items, dominant_pressures) -> Optional[Dict[str, Any]]:
    """If a strong restrictive/structural body sits on a fire-element
    Moon, expression overcompensates outward to mask suppression."""
    by_name = {n: (s, h) for n, s, h in items}
    moon = by_name.get("Moon")
    if not moon:
        return None
    fire = moon[0] in ("Aries", "Leo", "Sagittarius")
    has_compression = any(p.get("type") == "compression" for p in dominant_pressures)
    has_pluto = any(p.get("type") == "pluto_pressure" for p in dominant_pressures)
    if fire and (has_compression or has_pluto):
        return {
            "type": "overcompensation",
            "theme": "outward intensity used to mask interior suppression",
            "strength": 0.75,
        }
    return None


def _detect_repetition_loops(reps: Dict[str, Any]) -> List[Dict[str, Any]]:
    """A theme repeats when ≥3 bodies share a sign, OR ≥3 bodies share a
    house. Strength scales with the cumulative weight."""
    loops: List[Dict[str, Any]] = []
    for sign, score in sorted(reps["sign_score"].items(), key=lambda kv: -kv[1]):
        bodies = reps["sign_bodies"][sign]
        if len(bodies) >= 3:
            loops.append({
                "type": "sign_repetition",
                "sign": sign,
                "theme": _SIGN_PRESSURE.get(sign, sign.lower()),
                "bodies": bodies,
                "strength": min(1.0, score / 30.0),
            })
    for house, score in sorted(reps["house_score"].items(), key=lambda kv: -kv[1]):
        bodies = reps["house_bodies"][house]
        if len(bodies) >= 3:
            loops.append({
                "type": "house_concentration",
                "house": house,
                "theme": f"life pulls into {_HOUSE_DOMAIN.get(house, str(house))}",
                "bodies": bodies,
                "strength": min(1.0, score / 30.0),
            })
    return loops[:5]


def _detect_contradiction_pairs(items, reps) -> List[Dict[str, Any]]:
    """Find structural contradictions: dominant sign-pair tensions.
    Dedupes by axis so (Pisces, Virgo) and (Virgo, Pisces) only appear
    once, in the order of dominance (heaviest sign first).
    """
    out: List[Dict[str, Any]] = []
    top_signs = [s for s, _ in sorted(reps["sign_score"].items(), key=lambda kv: -kv[1])[:3]]
    pairs = {
        ("Cancer", "Capricorn"): "belonging vs responsibility",
        ("Capricorn", "Cancer"): "belonging vs responsibility",
        ("Aries", "Libra"):      "self-assertion vs calibration",
        ("Libra", "Aries"):      "self-assertion vs calibration",
        ("Taurus", "Scorpio"):   "stabilisation vs deep change",
        ("Scorpio", "Taurus"):   "stabilisation vs deep change",
        ("Gemini", "Sagittarius"): "precision of fact vs scope of meaning",
        ("Sagittarius", "Gemini"): "precision of fact vs scope of meaning",
        ("Leo", "Aquarius"):     "self-authorship vs collective differentiation",
        ("Aquarius", "Leo"):     "self-authorship vs collective differentiation",
        ("Virgo", "Pisces"):     "precision vs permeability",
        ("Pisces", "Virgo"):     "precision vs permeability",
        # ophiuchus-first-class-content-v1: stabilisation pulled against
        # threshold-crossing integration.
        ("Taurus", "Ophiuchus"): "stabilisation vs integration under pressure",
        ("Ophiuchus", "Taurus"): "stabilisation vs integration under pressure",
    }
    seen_axes: set = set()
    for s1 in top_signs:
        for s2 in top_signs:
            if s1 == s2:
                continue
            key = (s1, s2)
            if key in pairs:
                # Canonical axis = frozenset to dedupe (Pisces, Virgo) ==
                # (Virgo, Pisces). We keep insertion order (heaviest-sign
                # pair first because top_signs is already sorted).
                axis_id = frozenset((s1, s2))
                if axis_id in seen_axes:
                    continue
                seen_axes.add(axis_id)
                out.append({
                    "axis": f"{s1} ↔ {s2}",
                    "theme": pairs[key],
                })
                break
    return out[:3]


# ---------------------------------------------------------------------------
# 2.  Public API
# ---------------------------------------------------------------------------
def build_pressure_topology(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Build the deterministic pressure topology envelope for a user's
    natal chart. Pure read — no DB writes."""
    items = _planet_sign_house_list(chart)
    if not items:
        return {
            "success": False,
            "build_marker": BUILD_MARKER,
            "reason": "no_planets_in_chart",
        }

    astro = (chart or {}).get("astrology") or {}
    planets = astro.get("planets") or {}

    reps = _count_repetitions(items)

    dominant_pressures: List[Dict[str, Any]] = []
    compression = _detect_compression(items, planets)
    if compression:
        dominant_pressures.append(compression)
    pluto_p = _detect_pluto_pressure(items, planets)
    if pluto_p:
        dominant_pressures.append(pluto_p)

    overcomp = _detect_overcompensation(items, dominant_pressures)
    overcompensation_patterns = [overcomp] if overcomp else []

    repetition_loops = _detect_repetition_loops(reps)
    contradiction_pairs = _detect_contradiction_pairs(items, reps)

    # Activation hubs = top houses by weighted score with ≥2 bodies
    activation_hubs = []
    for house, score in sorted(reps["house_score"].items(), key=lambda kv: -kv[1])[:3]:
        bodies = reps["house_bodies"][house]
        if len(bodies) >= 2:
            activation_hubs.append({
                "house": house,
                "domain": _HOUSE_DOMAIN.get(house, str(house)),
                "bodies": bodies,
                "weight_score": score,
            })

    # Top dominant signs (for the "field" label)
    dominant_signs = [
        {"sign": s, "score": sc, "bodies": reps["sign_bodies"][s]}
        for s, sc in sorted(reps["sign_score"].items(), key=lambda kv: -kv[1])[:3]
    ]

    return {
        "success": True,
        "build_marker": BUILD_MARKER,
        "dominant_pressures":    dominant_pressures,
        "contradiction_pairs":   contradiction_pairs,
        "overcompensation_patterns": overcompensation_patterns,
        "repetition_loops":      repetition_loops,
        "activation_hubs":       activation_hubs,
        "dominant_signs":        dominant_signs,
        "hierarchy_weights":     {
            "sign_score":  reps["sign_score"],
            "house_score": reps["house_score"],
        },
    }


# ---------------------------------------------------------------------------
# 3.  Narrative-constraints bridge
# ---------------------------------------------------------------------------
def build_narrative_constraints(topology: Dict[str, Any]) -> Dict[str, Any]:
    """Convert topology into the constraint envelope the LLM must
    express. The LLM is forbidden from improvising fields not surfaced
    here.
    """
    if not topology or not topology.get("success"):
        return {"available": False}

    pressures = topology.get("dominant_pressures") or []
    loops = topology.get("repetition_loops") or []
    contras = topology.get("contradiction_pairs") or []
    hubs = topology.get("activation_hubs") or []
    overcomp = topology.get("overcompensation_patterns") or []
    dom_signs = topology.get("dominant_signs") or []

    core_field = (
        loops[0]["theme"] if loops else
        (pressures[0]["theme"] if pressures else
         (dom_signs[0]["sign"] + " emphasis" if dom_signs else "unstructured"))
    )

    primary_tension = contras[0]["theme"] if contras else (
        pressures[0]["theme"] if pressures else None
    )
    secondary_tension = contras[1]["theme"] if len(contras) > 1 else None

    overcomp_style = overcomp[0]["theme"] if overcomp else None

    # Where pressure accumulates — top activation hub
    where_accumulates = (
        f"house {hubs[0]['house']} ({hubs[0]['domain']})" if hubs else None
    )

    # What repeats
    what_repeats = loops[0]["theme"] if loops else None

    return {
        "available":                  True,
        "core_field":                 core_field,
        "primary_tension":            primary_tension,
        "secondary_tension":          secondary_tension,
        "dominant_survival_strategy": (
            "containment and editing" if any(p.get("type") == "compression" for p in pressures) else
            "controlled intensity"    if any(p.get("type") == "pluto_pressure" for p in pressures) else
            None
        ),
        "overcompensation_style":     overcomp_style,
        "where_pressure_accumulates": where_accumulates,
        "what_repeats":               what_repeats,
    }


# ---------------------------------------------------------------------------
# 4.  Proof block for LLM
# ---------------------------------------------------------------------------
def build_pressure_topology_proof_block(
    topology: Dict[str, Any],
    constraints: Dict[str, Any],
) -> str:
    if not topology.get("success"):
        return (
            "━━━━ PRESSURE TOPOLOGY — ENGINE STATUS ━━━━\n"
            "available: NO\n"
            "INSTRUCTION: tell the user the chart's topology layer could "
            "not be computed. Do NOT improvise textbook descriptions.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def _fmt_list(items, key=None):
        if not items: return "  (none)"
        out = []
        for it in items[:5]:
            if isinstance(it, dict):
                out.append(f"  • { ' | '.join(f'{k}={v}' for k,v in it.items() if k != 'signals') }")
            else:
                out.append(f"  • {it}")
        return "\n".join(out)

    lines = [
        "━━━━ PRESSURE TOPOLOGY — ENGINE OUTPUT ━━━━",
        "DOMINANT PRESSURES:",
        _fmt_list(topology.get("dominant_pressures", [])),
        "",
        "REPETITION LOOPS (themes the chart insists on):",
        _fmt_list(topology.get("repetition_loops", [])),
        "",
        "CONTRADICTION PAIRS:",
        _fmt_list(topology.get("contradiction_pairs", [])),
        "",
        "OVERCOMPENSATION PATTERNS:",
        _fmt_list(topology.get("overcompensation_patterns", [])),
        "",
        "ACTIVATION HUBS (where life concentrates):",
        _fmt_list(topology.get("activation_hubs", [])),
        "",
        "NARRATIVE CONSTRAINTS — express ALL of these. Do not invent more:",
        f"  core_field:                 {constraints.get('core_field')}",
        f"  primary_tension:            {constraints.get('primary_tension')}",
        f"  secondary_tension:          {constraints.get('secondary_tension')}",
        f"  survival_strategy:          {constraints.get('dominant_survival_strategy')}",
        f"  overcompensation_style:     {constraints.get('overcompensation_style')}",
        f"  where_pressure_accumulates: {constraints.get('where_pressure_accumulates')}",
        f"  what_repeats:               {constraints.get('what_repeats')}",
        "",
        "INSTRUCTION TO YOU:",
        "1. Synthesise a MASTER-ASTROLOGER reading of this person's chart",
        "   using ONLY the constraints above plus the v5 inventory/v4",
        "   placements already injected in the system prompt.",
        "2. Open with the CORE FIELD as a felt observation, not a sign",
        "   summary. Example: 'Your chart keeps circling the same",
        "   pressure: <core_field>.' Then expand for 2-3 short paragraphs.",
        "3. Name the primary tension. Name how the chart compensates for it.",
        "4. NO 'Sun in X means…'. NO 'this house rules…'. NO",
        "   'spiritual journey'. NO 'lesson'. NO 'might'. NO 'may'.",
        "   NO closing question.",
        "5. Length: 180–280 words.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)
