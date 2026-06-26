"""relationship_bazi_engine_v2.py — Phase 3 BaZi Relationship Engine V2
=========================================================================

Build marker:  relationship-bazi-engine-v2
Companion to: relationship_bazi_engine.py  (v3 wisdom, untouched)

Architecture
------------
This module is a **pure enrichment layer**.  It does NOT replace the
existing `build_relationship_bazi()` (which still emits the wisdom-v3
prose).  Instead it computes additional dimensions that bring BaZi to
lens parity with Astrology and the new Numerology engine:

    Current Movement                — current annual pillar × both DMs
    Repair Pathway                   — bridge-element behaviour
    How They Help Each Other          — Ten Gods role-casting (A→B, B→A)
    How They Challenge Each Other     — hidden-stem + animal frictions
    Current Relationship Season        — annual pillar's relational signature

Plus diagnostics fields for everything the v2_card narrates.

The engine is **deterministic**: every output is a pure function of the
two charts (already present in MongoDB) + today's date.  No LLM, no
randomness, no network calls.

The engine **enriches** the existing v2_card without removing keys.
Both the v3 wisdom keys (what_strengthens, why_matters, what_bazi_sees)
and the new parity keys (natural_strength, repair_pathway,
current_movement, how_they_help_each_other, how_they_challenge_each_other,
current_relationship_season) live side-by-side.  Backward compatibility
is total.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, Optional, Tuple

ENGINE_VERSION = "relationship-bazi-engine-v2"


# ── Forbidden-language guard ──────────────────────────────────────────
FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "destiny",
    "destined",
    "soulmate",
    "meant to be",
    "guaranteed compatibility",
    "prediction",
    "fortune telling",
    "fortune-telling",
)


def find_forbidden_language(text: str) -> List[str]:
    if not isinstance(text, str) or not text:
        return []
    lower = text.lower()
    return [t for t in FORBIDDEN_TOKENS if t in lower]


# ── Five Elements canonical cycles ───────────────────────────────────
PRODUCES = {"Wood": "Fire",  "Fire": "Earth", "Earth": "Metal",
            "Metal": "Water", "Water": "Wood"}
CONTROLS = {"Wood": "Earth", "Fire": "Metal", "Earth": "Water",
            "Metal": "Wood",  "Water": "Fire"}


def _cycle(el_a: str, el_b: str) -> str:
    if not el_a or not el_b: return "neutral"
    if el_a == el_b:                       return "same"
    if PRODUCES.get(el_a) == el_b:         return "a_produces_b"
    if PRODUCES.get(el_b) == el_a:         return "b_produces_a"
    if CONTROLS.get(el_a) == el_b:         return "a_controls_b"
    if CONTROLS.get(el_b) == el_a:         return "b_controls_a"
    return "neutral"


# ── Bridge element (de-escalator for a control cycle) ────────────────
# When A controls B (e.g. Metal → Wood), the bridge is what A produces
# AND what produces B → resolves the control into the productive cycle.
BRIDGE_ELEMENT = {
    ("Wood",  "Earth"): "Fire",   # Wood→Fire→Earth
    ("Fire",  "Metal"): "Earth",  # Fire→Earth→Metal
    ("Earth", "Water"): "Metal",  # Earth→Metal→Water
    ("Metal", "Wood"):  "Water",  # Metal→Water→Wood
    ("Water", "Fire"):  "Wood",   # Water→Wood→Fire
}

BRIDGE_BEHAVIOUR = {
    "Water": "listening, reflection, curiosity, allowing emotion before moving",
    "Fire":  "warmth, recognition, naming what's working out loud, lightness",
    "Earth": "grounding, slowing the pace, holding the room steady, patience",
    "Metal": "precision, naming what's actually true, refining one thing at a time",
    "Wood":  "growth, opening one new possibility, leaving room for something to start",
}


def _bridge(el_a: str, el_b: str, cycle: str) -> Optional[str]:
    if cycle == "a_controls_b":  return BRIDGE_ELEMENT.get((el_a, el_b))
    if cycle == "b_controls_a":  return BRIDGE_ELEMENT.get((el_b, el_a))
    return None


# ── Yin/Yang polarity ────────────────────────────────────────────────
def _polarity_relation(p_a: str, p_b: str) -> str:
    p_a, p_b = (p_a or "").lower(), (p_b or "").lower()
    if p_a == "yang" and p_b == "yang": return "yang_yang"
    if p_a == "yin"  and p_b == "yin":  return "yin_yin"
    if p_a and p_b and p_a != p_b:      return "yang_yin"
    return "unknown"


YIN_YANG_NARRATIVE = {
    "yang_yang": "Both of you move outward first.  Initiative is doubled, which makes momentum easy and yielding harder.",
    "yin_yin":   "Both of you absorb first.  Sensitivity is doubled, which makes attunement easy and decisive action harder.",
    "yang_yin":  "One of you moves first; the other shapes the response.  The pacing has a natural call-and-answer rhythm when neither side fights it.",
    "unknown":   "",
}


# ── Ten Gods role-casting (collapsed to 5 categories) ────────────────
# Returns one of: Resource / Wealth / Officer / Companion / Output
# from A's perspective looking at B.
def _ten_gods_a_sees_b(el_a: str, el_b: str) -> str:
    if not el_a or not el_b: return ""
    if el_a == el_b:                  return "Companion"
    if PRODUCES.get(el_b) == el_a:    return "Resource"   # B produces A → B nourishes A
    if PRODUCES.get(el_a) == el_b:    return "Output"     # A produces B → A pours into B
    if CONTROLS.get(el_a) == el_b:    return "Wealth"     # A controls B → B is A's wealth
    if CONTROLS.get(el_b) == el_a:    return "Officer"    # B controls A → B is A's officer
    return ""


TEN_GODS_NARRATIVE = {
    "Resource":  "{other} often becomes the person who restores {self}'s perspective — refilling something {self} draws from to function.",
    "Wealth":    "{other} often becomes the field {self} acts on — what {self}'s drive moves toward and shapes.",
    "Officer":   "{other} often becomes the person who introduces structure, responsibility, or a standard {self} has to meet.",
    "Companion": "{other} often becomes a peer for {self} — equal footing, shared rhythm, mirror-recognition, sometimes competitive.",
    "Output":    "{other} often becomes the place {self}'s effort lands — what {self} expresses, builds, or pours into.",
}


# ── Animal relationship (extended) ───────────────────────────────────
ANIMAL_CYCLE = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]

ANIMAL_CLASHES = {frozenset(p) for p in [
    ("Rat", "Horse"), ("Ox", "Goat"), ("Tiger", "Monkey"),
    ("Rabbit", "Rooster"), ("Dragon", "Dog"), ("Snake", "Pig"),
]}

ANIMAL_HARMONIES = {frozenset(p) for p in [
    ("Rat", "Ox"), ("Tiger", "Pig"), ("Rabbit", "Dog"),
    ("Dragon", "Rooster"), ("Snake", "Monkey"), ("Horse", "Goat"),
]}

# 三合 — triangle alliances (3 animals each form a triad).
ANIMAL_TRIADS = [
    {"Rat", "Dragon", "Monkey"},
    {"Ox", "Snake", "Rooster"},
    {"Tiger", "Horse", "Dog"},
    {"Rabbit", "Goat", "Pig"},
]

# 六害 — harm pairs (priorities-clash without overt conflict).
ANIMAL_HARMS = {frozenset(p) for p in [
    ("Rat", "Goat"), ("Ox", "Horse"), ("Tiger", "Snake"),
    ("Rabbit", "Dragon"), ("Monkey", "Pig"), ("Rooster", "Dog"),
]}

# 三刑 — punishment triads (recurring same-pattern friction).
ANIMAL_PUNISHMENTS = [
    {"Rat", "Rabbit"},      # bilateral punishment
    {"Tiger", "Snake", "Monkey"},
    {"Ox", "Goat", "Dog"},
    {"Dragon"}, {"Horse"}, {"Pig"}, {"Rooster"},  # self-punishment singletons
]


def _animal_relation(a: str, b: str) -> str:
    """Return one of: same, clash, harmony, triad, harm, punishment,
    neutral."""
    if not a or not b: return "unknown"
    if a == b: return "same"
    pair = frozenset((a, b))
    if pair in ANIMAL_CLASHES:    return "clash"
    if pair in ANIMAL_HARMONIES:  return "harmony"
    for triad in ANIMAL_TRIADS:
        if {a, b}.issubset(triad): return "triad"
    if pair in ANIMAL_HARMS:      return "harm"
    for punish in ANIMAL_PUNISHMENTS:
        if {a, b}.issubset(punish): return "punishment"
    return "neutral"


ANIMAL_NARRATIVE = {
    "same":       "Your {pillar}-pillar animals match — there is an instinctive recognition in how you both read this domain of life.",
    "harmony":    "Your {pillar}-pillar animals are paired in classical harmony — cooperation comes easily in this domain.",
    "triad":      "Your {pillar}-pillar animals belong to the same triangle alliance — you naturally move in coordinated rhythm here.",
    "clash":      "Your {pillar}-pillar animals sit in direct opposition — the same situation reads as urgent for one of you and not the other.",
    "harm":       "Your {pillar}-pillar animals are in a 'harm' relation — practical priorities pull in different directions without obvious conflict.",
    "punishment": "Your {pillar}-pillar animals form a 'punishment' pattern — the same friction repeats across different surfaces until something gets named.",
    "neutral":    "Your {pillar}-pillar animals don't share a strong classical relation — interaction in this domain is largely shaped by other factors.",
    "unknown":    "",
}


# ── Hidden-stem analysis (day pillar) ────────────────────────────────
def _hidden_stem_relation(hidden_a: List[str], hidden_b: List[str]) -> str:
    """Returns 'shared' if they share any hidden stem, 'distinct' if none,
    'unknown' if data is missing."""
    if not hidden_a or not hidden_b: return "unknown"
    sa, sb = set(hidden_a), set(hidden_b)
    if sa & sb: return "shared"
    return "distinct"


# ── Current pillar (annual) — deterministic from today's date ────────
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
STEM_ELEMENTS = {
    "甲": ("Wood",  "Yang"), "乙": ("Wood",  "Yin"),
    "丙": ("Fire",  "Yang"), "丁": ("Fire",  "Yin"),
    "戊": ("Earth", "Yang"), "己": ("Earth", "Yin"),
    "庚": ("Metal", "Yang"), "辛": ("Metal", "Yin"),
    "壬": ("Water", "Yang"), "癸": ("Water", "Yin"),
}

EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳",
                    "午", "未", "申", "酉", "戌", "亥"]
BRANCH_TO_ANIMAL = dict(zip(EARTHLY_BRANCHES, ANIMAL_CYCLE))
BRANCH_ELEMENTS = {
    "子": "Water", "丑": "Earth", "寅": "Wood", "卯": "Wood",
    "辰": "Earth", "巳": "Fire",  "午": "Fire", "未": "Earth",
    "申": "Metal", "酉": "Metal", "戌": "Earth", "亥": "Water",
}


def _current_annual_pillar(today: Optional[_dt.date] = None) -> Dict[str, str]:
    """Return today's annual pillar: stem, branch, animal, element.

    BaZi year boundary is Lichun (~Feb 4); for narrative purposes we
    use the calendar year shifted at Lichun.  Approximation: years
    flip on Feb 4.  This matches the canonical Variant-A behaviour."""
    today = today or _dt.date.today()
    year = today.year
    if today.month < 2 or (today.month == 2 and today.day < 4):
        year -= 1
    stem_idx   = (year - 4) % 10
    branch_idx = (year - 4) % 12
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    s_el, s_pol = STEM_ELEMENTS[stem]
    return {
        "year":      year,
        "stem":      stem,
        "branch":    branch,
        "animal":    BRANCH_TO_ANIMAL[branch],
        "stem_element":   s_el,
        "stem_polarity":  s_pol,
        "branch_element": BRANCH_ELEMENTS[branch],
    }


# ── Narrative composers ──────────────────────────────────────────────
def _natural_strength_narrative(name_a: str, name_b: str,
                                el_a: str, el_b: str, cycle: str) -> str:
    """Phase 3 lens-parity natural-strength prose."""
    if cycle == "a_produces_b":
        return (
            f"{name_a}'s {el_a} naturally nourishes {name_b}'s {el_b}.  "
            f"When the relationship runs clean, {name_a} provides what "
            f"{name_b} turns into momentum — structure becomes motion, "
            f"care becomes form, attention becomes follow-through."
        )
    if cycle == "b_produces_a":
        return (
            f"{name_b}'s {el_b} naturally nourishes {name_a}'s {el_a}.  "
            f"When the relationship runs clean, {name_b} supplies what "
            f"{name_a} turns into shape — a steady stream of input that "
            f"{name_a} converts into something visible."
        )
    if cycle == "same":
        return (
            f"Both of you operate from {el_a}.  Recognition is fast — "
            f"the same rhythm, the same reflexes.  The natural strength "
            f"is shared instinct; less translation is needed."
        )
    if cycle in ("a_controls_b", "b_controls_a"):
        return (
            f"Your {el_a} and {name_b}'s {el_b} are on the control axis.  "
            f"The strength is honesty under pressure — both of you can "
            f"name uncomfortable truths the other rhythm wouldn't allow."
        )
    return (
        f"Your {el_a} and {name_b}'s {el_b} don't share a direct "
        f"productive or control relation.  The strength is independence "
        f"— each of you brings something the other doesn't have to "
        f"produce on their own."
    )


def _repair_pathway_narrative(name_a: str, name_b: str,
                              el_a: str, el_b: str, cycle: str,
                              bridge: Optional[str]) -> str:
    """Deterministic bridge-behaviour repair for control cycles; gentle
    rebalance suggestion for other cycles."""
    if bridge:
        behaviour = BRIDGE_BEHAVIOUR.get(bridge, "translation")
        controller = name_a if cycle == "a_controls_b" else name_b
        controlled = name_b if cycle == "a_controls_b" else name_a
        return (
            f"When tension rises, move into {bridge} behaviour first — "
            f"{behaviour}.  {controller} steps back from the controlling "
            f"reflex; {controlled} steps out of resistance.  Decisions "
            f"return once the room has softened."
        )
    if cycle == "same":
        return (
            f"When the rhythm doubles into a loop, the repair is "
            f"differentiation — one of you names what you'd do if you "
            f"weren't matching the other.  Trade identical reflexes for "
            f"a brief role-swap."
        )
    if cycle in ("a_produces_b", "b_produces_a"):
        giver = name_a if cycle == "a_produces_b" else name_b
        receiver = name_b if cycle == "a_produces_b" else name_a
        return (
            f"When the flow runs one-way for too long, the repair is "
            f"reciprocity — {receiver} actively names what {giver} is "
            f"providing, and {giver} pauses to receive something small "
            f"back before continuing."
        )
    return (
        f"When friction lands, the repair is translation: each of you "
        f"names what you just heard the other say in your own rhythm, "
        f"and corrects until the description matches the intent."
    )


def _help_narrative(name_a: str, name_b: str,
                    tg_a_sees_b: str, tg_b_sees_a: str) -> str:
    """Two-direction Ten-Gods role-casting narrative."""
    if not tg_a_sees_b or not tg_b_sees_a:
        return ""
    a_line = TEN_GODS_NARRATIVE.get(tg_a_sees_b, "").format(self=name_a, other=name_b)
    b_line = TEN_GODS_NARRATIVE.get(tg_b_sees_a, "").format(self=name_b, other=name_a)
    return f"{a_line}  {b_line}  Each of you experiences the relationship through a different role, which is why the same situation can look completely different from each side."


def _challenge_narrative(name_a: str, name_b: str,
                         cycle: str,
                         animal_day_relation: str,
                         hidden_stem_relation: str,
                         polarity_relation: str) -> str:
    """How they challenge each other — hidden stems + day-animal + polarity."""
    lines: List[str] = []
    if cycle in ("a_controls_b", "b_controls_a"):
        lines.append(
            f"Under stress, the control axis between you reactivates — "
            f"what one of you sees as clarity, the other reads as pressure."
        )
    if animal_day_relation == "clash":
        lines.append(
            f"Your day-pillar animals clash — same situation, opposite "
            f"sense of urgency."
        )
    elif animal_day_relation == "punishment":
        lines.append(
            f"Your day-pillar animals form a punishment pattern — the "
            f"same friction recurs across different surfaces."
        )
    elif animal_day_relation == "harm":
        lines.append(
            f"Your day-pillar animals are in a harm relation — practical "
            f"priorities pull apart without overt conflict."
        )
    if hidden_stem_relation == "distinct":
        lines.append(
            f"Your day-pillar hidden stems don't overlap — what's "
            f"unconsciously activated in each of you is different, which "
            f"is where most misunderstandings actually live."
        )
    if polarity_relation == "yang_yang":
        lines.append(
            f"Both of you tend to initiate first; under pressure neither "
            f"yields, and small disagreements escalate faster than either "
            f"would choose."
        )
    elif polarity_relation == "yin_yin":
        lines.append(
            f"Both of you tend to absorb first; under pressure neither "
            f"surfaces, and unresolved tension lingers underneath the "
            f"surface."
        )
    if not lines:
        lines.append(
            f"The challenge axis is subtle — most friction comes from "
            f"different rhythms processing the same event at different "
            f"speeds."
        )
    return "  ".join(lines)


def _current_movement_narrative(annual: Dict[str, str],
                                el_a: str, el_b: str) -> str:
    """How today's annual pillar interacts with both day masters."""
    a_el = annual["stem_element"]
    a_animal = annual["animal"]
    a_cycle_a = _cycle(a_el, el_a)
    a_cycle_b = _cycle(a_el, el_b)

    def _line(name: str, c: str) -> str:
        if c == "same":          return f"resonates directly with {name}'s rhythm"
        if c == "a_produces_b":  return f"feeds {name}'s rhythm"  # annual produces person
        if c == "b_produces_a":  return f"draws on {name}'s rhythm"
        if c == "a_controls_b":  return f"presses on {name}'s rhythm"
        if c == "b_controls_a":  return f"is shaped by {name}'s rhythm"
        return f"runs alongside {name}'s rhythm without strong interaction"

    return (
        f"This is a {a_el}-{a_animal} year ({annual['year']}).  "
        f"The current {a_el} pillar {_line('the first', a_cycle_a)} "
        f"and {_line('the second', a_cycle_b)}.  "
        f"In practice this means right now the field favours the "
        f"{a_el}-coded behaviours of the relationship."
    )


def _current_season_narrative(annual: Dict[str, str],
                              el_a: str, el_b: str) -> str:
    """One-sentence relationship season."""
    pair = (annual["stem_element"], el_a, el_b)
    a_el = annual["stem_element"]
    if a_el == el_a == el_b:
        return f"The current {a_el} cycle deepens what's already strong between you — same rhythm, amplified."
    if CONTROLS.get(a_el) in (el_a, el_b):
        return f"The current {a_el} cycle tests one rhythm in particular — expect that side to feel slightly more pressed than usual."
    if PRODUCES.get(a_el) in (el_a, el_b):
        return f"The current {a_el} cycle is feeding one of your rhythms — that side will run noticeably easier this year."
    return f"The current {a_el} cycle runs adjacent to both of you — neither pushed nor strongly fed; this is a baseline year for the connection."


# ── Public API ───────────────────────────────────────────────────────
def enrich_bazi_relationship(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
    today: Optional[_dt.date] = None,
) -> Optional[Dict[str, Any]]:
    """Compute the Phase-3 v2_card enrichment and diagnostics.

    Returns None when day-master elements are missing on either side.
    The output is intended to be **merged** into the existing v2_card
    (which still owns the wisdom-v3 prose).  No keys collide; both
    legacy keys (what_strengthens, why_matters, what_bazi_sees) and
    the new parity keys ride together.
    """
    bazi_a = (chart_a or {}).get("bazi") or {}
    bazi_b = (chart_b or {}).get("bazi") or {}
    dm_a = bazi_a.get("day_master") or {}
    dm_b = bazi_b.get("day_master") or {}
    el_a, el_b = dm_a.get("element", ""), dm_b.get("element", "")
    if not el_a or not el_b:
        return None

    pol_a, pol_b = dm_a.get("polarity", ""), dm_b.get("polarity", "")
    cycle = _cycle(el_a, el_b)
    bridge = _bridge(el_a, el_b, cycle)
    polarity = _polarity_relation(pol_a, pol_b)

    pillars_a = bazi_a.get("pillars") or {}
    pillars_b = bazi_b.get("pillars") or {}
    year_a = pillars_a.get("year") or {}
    year_b = pillars_b.get("year") or {}
    day_a  = pillars_a.get("day")  or {}
    day_b  = pillars_b.get("day")  or {}

    animal_year_relation = _animal_relation(year_a.get("animal_name", ""),
                                            year_b.get("animal_name", ""))
    animal_day_relation  = _animal_relation(day_a.get("animal_name", ""),
                                            day_b.get("animal_name", ""))
    hidden_stem_relation = _hidden_stem_relation(day_a.get("hidden_stems", []),
                                                 day_b.get("hidden_stems", []))
    tg_a_sees_b = _ten_gods_a_sees_b(el_a, el_b)
    tg_b_sees_a = _ten_gods_a_sees_b(el_b, el_a)
    annual = _current_annual_pillar(today=today)
    day_master_relation = (
        f"{el_a}-{pol_a} ↔ {el_b}-{pol_b}".strip()
        if pol_a and pol_b else f"{el_a} ↔ {el_b}"
    )

    # Build narratives
    new_v2_card = {
        "natural_strength":             _natural_strength_narrative(name_a, name_b, el_a, el_b, cycle),
        "repair_pathway":               _repair_pathway_narrative(name_a, name_b, el_a, el_b, cycle, bridge),
        "current_movement":             _current_movement_narrative(annual, el_a, el_b),
        "how_they_help_each_other":     _help_narrative(name_a, name_b, tg_a_sees_b, tg_b_sees_a),
        "how_they_challenge_each_other": _challenge_narrative(name_a, name_b, cycle, animal_day_relation,
                                                               hidden_stem_relation, polarity),
        "current_relationship_season":   _current_season_narrative(annual, el_a, el_b),
    }

    new_diagnostics = {
        "day_master_relation":     day_master_relation,
        "ten_gods_a_sees_b":       tg_a_sees_b,
        "ten_gods_b_sees_a":       tg_b_sees_a,
        "animal_relation_year":    animal_year_relation,
        "animal_relation_day":     animal_day_relation,
        "hidden_stem_relation":    hidden_stem_relation,
        "yin_yang_relation":       polarity,
        "bridge_element":          bridge,
        "luck_pillar_relation":    "not_computed",   # placeholder; requires gender + birth_date math
        "current_annual_pillar":   annual,
        "engine_version":          ENGINE_VERSION,
    }

    return {"v2_card": new_v2_card, "diagnostics": new_diagnostics}
