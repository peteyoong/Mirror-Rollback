"""bazi_animal_narrative.py — grounded Chinese-zodiac animal narrative
========================================================================
Build marker: bazi-animal-narrative-v1

Takes two BaZi pillar payloads and produces a *grounded*, human-readable
explanation of the animal-relationship dynamics — without mystical
fatalism. Three blocks:

    1.  pair_dynamic    — primary year-animal complementarity / clash
    2.  inner_dynamic   — day-animal (home / private) interaction
    3.  triad_signal    — if either side is part of a classical triad,
                          named in everyday language.

This module does NOT replace the existing diagnostics in
`compute_bazi_signals`; it produces a separate `animal_narrative` payload
that the UI renders alongside the existing element-cycle evidence.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

NARRATIVE_VERSION = "bazi-animal-narrative-v1"

# ─────────────────────────────────────────────────────────────────────
# Relationship tables — pairwise interactions in everyday language
# ─────────────────────────────────────────────────────────────────────
# Clashes (6 axial oppositions). Reciprocal pairs.
_CLASH_PAIRS = {
    frozenset({"Rat", "Horse"}):     ("focus", "freedom",
        "Rat tightens; Horse runs — when one wants depth the other wants distance."),
    frozenset({"Ox", "Goat"}):       ("steady method", "feeling truth",
        "Ox builds slowly; Goat needs the feeling to be right — pace becomes the argument."),
    frozenset({"Tiger", "Monkey"}):  ("instinct", "strategy",
        "Tiger leaps; Monkey calculates — the one who acts first thinks the other is slow, and vice versa."),
    frozenset({"Rabbit", "Rooster"}): ("softness", "precision",
        "Rabbit avoids friction; Rooster names what's off — the very moves that protect one upset the other."),
    frozenset({"Dragon", "Dog"}):    ("vision", "loyalty",
        "Dragon goes big; Dog protects the small — scope itself becomes the conflict."),
    frozenset({"Snake", "Pig"}):     ("strategy", "directness",
        "Snake plans the angle; Pig says the thing — the indirect and the direct can read each other as dishonest."),
}

# Harmony (six He pairs)
_HARMONY_PAIRS = {
    frozenset({"Rat", "Ox"}):       "quiet, steady building — neither needs to perform for the other.",
    frozenset({"Tiger", "Pig"}):    "ease in your differences — Tiger leads, Pig follows without losing self.",
    frozenset({"Rabbit", "Dog"}):   "deep loyalty — when one promises something, the other can rest on it.",
    frozenset({"Dragon", "Rooster"}):"vision married to detail — what you build together tends to actually finish.",
    frozenset({"Snake", "Monkey"}): "strategic resonance — fewer arguments, more 'how are we doing this'.",
    frozenset({"Horse", "Goat"}):   "natural rhythm together — your timing tends to match without effort.",
}

# Three-Combination triads
_TRIADS = {
    "Water": {"Rat", "Monkey", "Dragon"},
    "Wood":  {"Rabbit", "Pig", "Goat"},
    "Fire":  {"Horse", "Dog", "Tiger"},
    "Metal": {"Rooster", "Snake", "Ox"},
}

_TRIAD_NARRATIVES = {
    "Water": "Together you tend to move things — ideas circulate, plans reshape, fluidity is the field.",
    "Wood":  "Together you tend to grow things — projects, relationships, gardens; this triad nurtures.",
    "Fire":  "Together you tend to ignite things — momentum, attention, the spark in the room.",
    "Metal": "Together you tend to refine things — what gets dropped is as important as what gets kept.",
}

# Harm (6) and Punishment (3) — rarer but real frictions.
_HARM_PAIRS = {
    frozenset({"Rat", "Goat"}):   "small irritations build silently — what one finds endearing the other finds wearing.",
    frozenset({"Ox", "Horse"}):   "different speeds; one of you may consistently feel slowed or rushed by the other.",
    frozenset({"Tiger", "Snake"}):"hidden agendas can be read where there are none — trust takes longer than expected.",
    frozenset({"Rabbit", "Dragon"}):"the soft one can feel run-over; the big one can feel like nothing they do is big enough.",
    frozenset({"Monkey", "Pig"}): "humour styles diverge — one teases, the other absorbs it more than meant.",
    frozenset({"Rooster", "Dog"}):"watching for what's wrong can dominate; both of you should ask what's working.",
}


def _pair_block(animal_a: str, animal_b: str, name_a: str, name_b: str) -> Dict[str, str]:
    if not animal_a or not animal_b:
        return {"summary": "Year-animal data is incomplete for one or both — pair dynamic not computed."}
    pair = frozenset({animal_a, animal_b})
    if animal_a == animal_b:
        return {
            "summary": (
                f"Both of you are {animal_a} — same generational instinct. "
                f"You recognise each other quickly, share blind spots quickly, "
                f"and may underestimate how much you both default the same way under stress."
            ),
            "tone": "same-sign",
        }
    if pair in _CLASH_PAIRS:
        a_label, b_label, body = _CLASH_PAIRS[pair]
        # Disambiguate which side gets which trait
        first, second = animal_a, animal_b
        return {
            "summary": (
                f"{first} and {second}: classical clash. "
                f"{body} "
                f"Handled well, this is sharpening; handled poorly, you each play the part the other expected."
            ),
            "tone": "clash",
        }
    if pair in _HARMONY_PAIRS:
        return {
            "summary": f"{animal_a} and {animal_b}: classical harmony — {_HARMONY_PAIRS[pair]}",
            "tone": "harmony",
        }
    if pair in _HARM_PAIRS:
        return {
            "summary": f"{animal_a} and {animal_b}: classical harm — {_HARM_PAIRS[pair]}",
            "tone": "harm",
        }
    # Default: neutral but explained
    return {
        "summary": (
            f"{animal_a} meets {animal_b} — different generational instincts. "
            f"Neither classical clash nor classical harmony; the dynamic gets made by how you use it."
        ),
        "tone": "neutral",
    }


def _inner_block(day_a: str, day_b: str) -> Dict[str, str]:
    if not day_a or not day_b or day_a == day_b:
        if day_a and day_a == day_b:
            return {"summary": f"Both of your inner natures (day animals) are {day_a} — at home and in private, you default the same way. Familiar and easy; also easy to skip the parts of yourselves that are different from each other."}
        return {"summary": ""}
    pair = frozenset({day_a, day_b})
    if pair in _CLASH_PAIRS:
        _, _, body = _CLASH_PAIRS[pair]
        return {"summary": f"In private (day animals {day_a} ↔ {day_b}), the dynamic gets sharper: {body}"}
    if pair in _HARMONY_PAIRS:
        return {"summary": f"In private (day animals {day_a} ↔ {day_b}), there's natural ease — {_HARMONY_PAIRS[pair]}"}
    if pair in _HARM_PAIRS:
        return {"summary": f"In private (day animals {day_a} ↔ {day_b}), the friction is subtler — {_HARM_PAIRS[pair]}"}
    return {"summary": f"In private (day animals {day_a} ↔ {day_b}), the dynamic is neutral — neither classical match nor clash."}


def _triad_block(animal_a: str, animal_b: str) -> Dict[str, str]:
    if not animal_a or not animal_b:
        return {"summary": ""}
    # If both fall inside the same triad
    for elem, members in _TRIADS.items():
        if animal_a in members and animal_b in members:
            return {
                "summary": (
                    f"You sit in the {elem} triad together ({', '.join(sorted(members))}). "
                    f"{_TRIAD_NARRATIVES[elem]}"
                ),
                "element": elem,
            }
    # If they sit in different triads — note the cross
    triad_a = next((e for e, m in _TRIADS.items() if animal_a in m), None)
    triad_b = next((e for e, m in _TRIADS.items() if animal_b in m), None)
    if triad_a and triad_b and triad_a != triad_b:
        return {
            "summary": (
                f"{animal_a} is part of the {triad_a} triad; {animal_b} is part of the {triad_b} triad. "
                f"You don't share a generational triad, which means you balance each other through difference, "
                f"not through resonance."
            ),
            "element": f"{triad_a}/{triad_b}",
        }
    return {"summary": ""}


def compute_animal_narrative(
    animal_a: str,
    animal_b: str,
    day_animal_a: Optional[str] = None,
    day_animal_b: Optional[str] = None,
    name_a: str = "You",
    name_b: str = "them",
) -> Optional[Dict[str, Any]]:
    if not animal_a or not animal_b:
        return None
    pair = _pair_block(animal_a, animal_b, name_a, name_b)
    inner = _inner_block(day_animal_a or "", day_animal_b or "")
    triad = _triad_block(animal_a, animal_b)
    out = {
        "version": NARRATIVE_VERSION,
        "pair_dynamic":  pair,
        "inner_dynamic": inner,
        "triad_signal":  triad,
    }
    return out


__all__ = ["compute_animal_narrative", "NARRATIVE_VERSION"]
