"""relationship_numerology_engine_lite.py — Compact deterministic
Numerology Relationship engine (Phase 2-lite)
================================================================

Build marker:   relationship-numerology-lite-v1
Owner surface:  Forum mappings → signals.numerology.{themes, v2_card, diagnostics}

Design constraints (per spec):
  • Deterministic — no LLM, no randomness
  • Backward compatible — existing `themes` array preserved verbatim
  • Additive — `v2_card` and `diagnostics` ride along; FE may ignore
  • Mirror language only — no fortune-telling vocabulary
  • Reliable inputs only — life_path / expression / soul_urge /
    personality / birthday + master-number flags.  No personal_year,
    pinnacles, challenges, missing_numbers, karmic_debt, or maturity.

Five questions, five answers per pair:
  1. core_dynamic     — what naturally happens between you
  2. natural_strength — what you strengthen in each other
  3. growth_edge      — what wants to grow
  4. shadow_pattern   — what creates friction under pressure
  5. repair_pathway   — the literal first move when friction lands
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

ENGINE_VERSION = "relationship-numerology-lite-v1"

# ── Forbidden language guard ─────────────────────────────────────────
# Tokens that smell like fortune-telling.  Used by tests and by the
# `assert_mirror_language()` helper.  Lowercased; substring match.
FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "destined",
    "soulmate",
    "karmic partner",
    "meant to be",
    "guaranteed compatibility",
)

def find_forbidden_language(text: str) -> List[str]:
    """Return list of forbidden tokens that appear in `text`."""
    if not isinstance(text, str) or not text:
        return []
    lower = text.lower()
    return [tok for tok in FORBIDDEN_TOKENS if tok in lower]


# ── Number archetypes ────────────────────────────────────────────────
# (label, action_phrase) — used by the compositional fallback when no
# hand-authored cell exists for the pair.
ARCHETYPES: Dict[int, Tuple[str, str]] = {
    1:  ("Initiator",       "moves first and builds momentum"),
    2:  ("Mediator",        "tunes the room and holds the field"),
    3:  ("Voice",           "expresses and amplifies in language"),
    4:  ("Builder",         "structures and trusts the process"),
    5:  ("Disrupter",       "changes shape and refuses stasis"),
    6:  ("Caretaker",       "tends, commits, and makes home"),
    7:  ("Seeker",          "goes inward and watches for pattern"),
    8:  ("Steward",         "directs resources and holds accountability"),
    9:  ("Releaser",        "completes cycles and lets things close"),
    11: ("Inner Knower",    "perceives subtly and signals before words arrive"),
    22: ("Master-Builder",  "scales personal vision into structural form"),
    33: ("Master-Tender",   "carries care as the work itself"),
}


# ── Hand-authored pair cells (frozenset-keyed; order-insensitive) ───
# Tone: Mirror language — rhythm, pacing, translation, friction,
# support, growth, repair, pattern.  Every field is a template string
# accepting {name_a} and {name_b} placeholders.
HAND_AUTHORED: Dict[frozenset, Dict[str, str]] = {

    # ── 11 ↔ 3 — Pete ↔ Mel ──────────────────────────────────────────
    frozenset({11, 3}): {
        "core_dynamic":     "Inner Knower meets Voice — what {name_a} perceives in silence, {name_b} turns into something speakable.",
        "natural_strength": "{name_a} feels what's underneath. {name_b} gives it shape. Together you translate signal into sentence.",
        "growth_edge":      "{name_a} grows by trusting that articulate words don't betray subtlety. {name_b} grows by trusting that silence isn't withdrawal.",
        "shadow_pattern":   "Under pressure {name_a} starts to speak in hints; {name_b} starts to perform warmth. The real thing stops getting said.",
        "repair_pathway":   "Pause. Each of you names one true thing that's also uncomfortable. Don't soften it. Then keep talking.",
    },

    # ── 11 ↔ 5 — Pete ↔ Isaac ────────────────────────────────────────
    frozenset({11, 5}): {
        "core_dynamic":     "Inner Knower meets Disrupter — {name_a} reads the field; {name_b} keeps moving the field around.",
        "natural_strength": "{name_b}'s motion stops {name_a}'s perception from going inward forever. {name_a}'s attentiveness gives {name_b}'s change somewhere to land.",
        "growth_edge":      "{name_a} grows by moving before fully understanding. {name_b} grows by sitting still long enough for a signal to arrive.",
        "shadow_pattern":   "{name_a} reads the room and stays silent; {name_b} keeps changing the topic. Neither lands.",
        "repair_pathway":   "Slow down to one shared question. Let {name_a} say what they're picking up. Let {name_b} pick one direction and try it for a week.",
    },

    # ── 11 ↔ 9 — Pete ↔ Thaddeus ─────────────────────────────────────
    frozenset({11, 9}): {
        "core_dynamic":     "Inner Knower meets Releaser — {name_a} senses what's underneath; {name_b} knows when to let it go.",
        "natural_strength": "{name_a} won't let the unspoken stay buried. {name_b} won't let the finished stay clutched. Together you process and clear.",
        "growth_edge":      "{name_a} grows by accepting that some perceptions don't need to be acted on. {name_b} grows by staying with something long enough to know it's finished.",
        "shadow_pattern":   "{name_a} keeps surfacing what {name_b} already released. {name_b} closes chapters {name_a} still feels open. Both start to feel unmet.",
        "repair_pathway":   "Each names one thing that's actually closed and one thing that isn't. Don't argue the list. Let each other's accounting stand.",
    },

    # ── 3 ↔ 5 ─────────────────────────────────────────────────────────
    frozenset({3, 5}): {
        "core_dynamic":     "Voice meets Disrupter — {name_a} talks the thing alive; {name_b} keeps the thing moving.",
        "natural_strength": "Together you generate momentum. {name_a}'s expression draws attention to what {name_b} just set in motion; {name_b}'s motion gives {name_a}'s words something to land on.",
        "growth_edge":      "{name_a} grows by finishing sentences before starting new ones. {name_b} grows by staying somewhere long enough to mean it.",
        "shadow_pattern":   "Under friction this pair goes loud and scattered — lots of words, lots of motion, nothing actually said or settled.",
        "repair_pathway":   "Stop both rhythms at once. One topic, one direction, ten minutes of quiet between you before either speaks.",
    },

    # ── 4 ↔ 8 ─────────────────────────────────────────────────────────
    frozenset({4, 8}): {
        "core_dynamic":     "Builder meets Steward — {name_a} makes the structure; {name_b} decides what the structure is for.",
        "natural_strength": "{name_a}'s reliability covers {name_b}'s scope. {name_b}'s authority gives {name_a}'s work direction. This pair builds things that last.",
        "growth_edge":      "{name_a} grows by letting strategy override habit when it matters. {name_b} grows by trusting the pace {name_a} sets, not just the outcome.",
        "shadow_pattern":   "{name_a} digs in on the method; {name_b} pushes for the result. The work happens but the relationship goes quiet.",
        "repair_pathway":   "Trade authority briefly. {name_a} names the outcome they actually want. {name_b} names the process they're willing to follow.",
    },

    # ── 2 ↔ 7 ─────────────────────────────────────────────────────────
    frozenset({2, 7}): {
        "core_dynamic":     "Mediator meets Seeker — {name_a} attends to the field between you; {name_b} attends to what's underneath it.",
        "natural_strength": "{name_a} keeps the connection alive while {name_b} processes. {name_b} brings depth back to {name_a} when the surface gets too smooth.",
        "growth_edge":      "{name_a} grows by tolerating {name_b}'s quiet without reading it as distance. {name_b} grows by surfacing more often than feels natural.",
        "shadow_pattern":   "{name_a} starts to chase reassurance. {name_b} starts to disappear into thought. The bridge between you thins.",
        "repair_pathway":   "{name_b} names one specific thing they've been thinking about, even partial. {name_a} listens without asking what it means yet.",
    },
}


# ── Helpers ──────────────────────────────────────────────────────────
def _slug(text: str) -> str:
    """slugify for pair_type diagnostic.  Lowercase, hyphen-joined."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _collect_numbers(num: Dict[str, Any]) -> Dict[str, Optional[int]]:
    """Pull every allowed numerology field as {field_name: int|None}."""
    if not isinstance(num, dict):
        return {k: None for k in ("life_path", "expression", "soul_urge",
                                  "personality", "birthday")}
    out: Dict[str, Optional[int]] = {}
    for k in ("life_path", "expression", "soul_urge", "personality", "birthday"):
        v = (num.get(k) or {}).get("number")
        out[k] = int(v) if isinstance(v, int) else None
    return out


def _is_master(n: Optional[int]) -> bool:
    return n in (11, 22, 33)


def _master_flags(side: str, nums: Dict[str, Optional[int]]) -> List[str]:
    flags: List[str] = []
    for field, val in nums.items():
        if _is_master(val):
            flags.append(f"{side}:{field}={val}")
    return flags


def _shared_numbers(a: Dict[str, Optional[int]],
                    b: Dict[str, Optional[int]]) -> List[int]:
    set_a = {v for v in a.values() if v is not None}
    set_b = {v for v in b.values() if v is not None}
    return sorted(set_a & set_b)


def _compose_fallback(lp_a: int, lp_b: int,
                      name_a: str, name_b: str) -> Dict[str, str]:
    """Compositional template used when no hand-authored cell exists."""
    arc_a = ARCHETYPES.get(lp_a, (f"Path-{lp_a}", f"moves at a {lp_a}-rhythm"))
    arc_b = ARCHETYPES.get(lp_b, (f"Path-{lp_b}", f"moves at a {lp_b}-rhythm"))

    if lp_a == lp_b:
        # Same-rhythm fallback.
        return {
            "core_dynamic":     f"{arc_a[0]} meets {arc_b[0]} — {name_a} and {name_b} both {arc_a[1]}.",
            "natural_strength": f"You recognise each other on sight — the same rhythm, the same default move. Less translation needed; more shared instinct.",
            "growth_edge":      f"The lens you both default to is also the lens you both avoid the work behind. Each grows by leaning into what the other quietly skips.",
            "shadow_pattern":   f"Under pressure you both reach for the same {arc_a[0].lower()} reflex. The pattern doubles instead of balancing.",
            "repair_pathway":   "Trade roles briefly. One of you names what the other usually carries; the other tries that move for an hour.",
        }

    return {
        "core_dynamic":     f"{arc_a[0]} meets {arc_b[0]} — {name_a} {arc_a[1]}; {name_b} {arc_b[1]}.",
        "natural_strength": f"What {name_a} brings forward, {name_b} carries differently. Two operating rhythms, one shared field — and a steady supply of translation between them.",
        "growth_edge":      f"{name_a} grows by leaning into what {name_b} naturally does. {name_b} grows by doing the same in reverse. The lens you're least fluent in is where the work is.",
        "shadow_pattern":   f"Under pressure {name_a} overdoes their {arc_a[0].lower()} reflex; {name_b} overdoes theirs. Both rhythms become caricatures of themselves.",
        "repair_pathway":   "Trade speed for translation. Each names what they just felt in one sentence. Don't fix it yet — let the translation sit.",
    }


def _build_v2_card(lp_a: int, lp_b: int,
                   name_a: str, name_b: str) -> Tuple[Dict[str, str], bool]:
    """Return (v2_card, used_hand_authored)."""
    cell = HAND_AUTHORED.get(frozenset({lp_a, lp_b}))
    used_hand_authored = False
    if cell:
        # Determine which side is which when the two LPs differ — the
        # hand-authored cells are written from {name_a}'s perspective
        # using the smaller-or-master LP convention noted in each cell.
        # We always render {name_a} = the side whose LP appears first
        # in the cell's title.  For LP=lp_a, lp_b ordering we render
        # accordingly.
        used_hand_authored = True
        rendered = {
            k: v.format(name_a=name_a, name_b=name_b)
            for k, v in cell.items()
        }
        return rendered, used_hand_authored

    return _compose_fallback(lp_a, lp_b, name_a, name_b), used_hand_authored


def _pair_type(lp_a: int, lp_b: int) -> str:
    """Deterministic pair-type slug ordered by (smaller-then-larger).
    Master numbers sort to their numeric position (11 > 9; 22 > 11)."""
    a, b = sorted((lp_a, lp_b))
    arc_a = ARCHETYPES.get(a, (f"path-{a}", ""))[0]
    arc_b = ARCHETYPES.get(b, (f"path-{b}", ""))[0]
    return _slug(f"{a}x{b}-{arc_a}-meets-{arc_b}")


# ── Public API ───────────────────────────────────────────────────────
def compute_numerology_relationship(num_a: Dict[str, Any],
                                    num_b: Dict[str, Any],
                                    name_a: str,
                                    name_b: str) -> Optional[Dict[str, Any]]:
    """Compute the v2_card + diagnostics block for a numerology pair.

    Returns None ONLY when life_path data is missing on either side.
    Themes are produced by the existing Phase-1 path in
    `forum_hd_mapping.compute_numerology_signals` and stitched in by
    the caller — this engine is responsible exclusively for `v2_card`
    and `diagnostics`.
    """
    nums_a = _collect_numbers(num_a)
    nums_b = _collect_numbers(num_b)
    lp_a, lp_b = nums_a.get("life_path"), nums_b.get("life_path")
    if not lp_a or not lp_b:
        return None

    v2_card, used_hand = _build_v2_card(lp_a, lp_b, name_a, name_b)
    diagnostics: Dict[str, Any] = {
        "life_path_a":         lp_a,
        "life_path_b":         lp_b,
        "pair_type":           _pair_type(lp_a, lp_b),
        "shared_numbers":      _shared_numbers(nums_a, nums_b),
        "master_number_flags": _master_flags("a", nums_a) + _master_flags("b", nums_b),
        "used_hand_authored":  used_hand,
        "engine_version":      ENGINE_VERSION,
    }
    return {"v2_card": v2_card, "diagnostics": diagnostics}
