"""
RELATIONSHIP BaZi ENGINE — v1
Builds a deterministic 5-section narrative card from already-computed BaZi data.

Parity goal: bring BaZi to the same UX level as Astrology Dynamics and Enneagram
Dynamics — i.e. a relationship-interpretation layer, not just an evidence layer.
The existing Elemental Dynamics (signals.bazi.support/tension/growth) is preserved
as the proof/evidence layer beneath this card.

Sections (per spec):
  1. Core Dynamic
  2. What Strengthens This Relationship
  3. Growth Edge
  4. Shadow Pattern
  5. Why This Relationship Matters

Inputs (all derived from chart.bazi — NO calculator changes, NO chart modifications):
  - element relationship (5x5 = 25 element pairs)
  - productive / control cycle direction
  - support / tension / growth signal arrays (verbatim re-use from
    compute_bazi_signals — the existing single source of truth)
  - zodiac animal interactions (year and day animals)
  - role context (spouse, parent, child, friend, colleague, other)

Each section is deterministic English narrative, ~80-150 words, relationship-
focused. No fortune telling. No generic personality text. Strings are composed
from a small, auditable set of templates keyed on cycle + role + animal.

BUILD MARKER: relationship-mapping-bazi-narrative-v1
"""

from typing import Any, Dict, List, Optional

BUILD_MARKER = "relationship-mapping-bazi-narrative-v1"

# ----------------------------------------------------------------------------
# Wu Xing tables (productive + control cycles)
# These mirror BAZI_ELEMENT_CYCLE / BAZI_CONTROL_CYCLE in forum_hd_mapping.py.
# Duplicated here so this engine has zero coupling to that module's globals.
# ----------------------------------------------------------------------------

ELEMENT_PRODUCES = {
    "Wood": "Fire", "Fire": "Earth", "Earth": "Metal",
    "Metal": "Water", "Water": "Wood",
}
ELEMENT_CONTROLS = {
    "Wood": "Earth", "Fire": "Metal", "Earth": "Water",
    "Metal": "Wood", "Water": "Fire",
}

# Two-word relational traits — chosen specifically for how the element shows up
# *between* people, not for solo personality. (e.g., Metal's relational signature
# is "structuring + refining" not "perfectionist".)
ELEMENT_RELATIONAL_TRAITS: Dict[str, Dict[str, str]] = {
    "Wood":  {"verb": "extends",  "mode": "visioning",   "noun": "growth",      "shadow": "uprooting"},
    "Fire":  {"verb": "amplifies","mode": "expressing",  "noun": "presence",    "shadow": "burning out"},
    "Earth": {"verb": "holds",    "mode": "stabilising", "noun": "ground",      "shadow": "rigidity"},
    "Metal": {"verb": "refines",  "mode": "discerning",  "noun": "clarity",     "shadow": "overcorrecting"},
    "Water": {"verb": "deepens",  "mode": "adapting",    "noun": "flow",        "shadow": "ungroundedness"},
}

# Element → what the OTHER element receives from it in productive cycle
PRODUCES_GIFT = {
    "Wood":  "fuel and momentum",
    "Fire":  "warmth and visibility",
    "Earth": "stability and slow trust",
    "Metal": "precision and structure",
    "Water": "depth and adaptability",
}

# Element → what the OTHER element gets compressed by in control cycle
CONTROLS_PRESSURE = {
    "Wood":  "shape and discipline",
    "Fire":  "boundaries and pacing",
    "Earth": "challenges to settle into",
    "Metal": "demands for accountability",
    "Water": "containers for the mystery",
}

# Zodiac compatibility (year animals — same set as forum_hd_mapping)
ZODIAC_CLASHES = {
    frozenset(("Rat", "Horse")), frozenset(("Ox", "Goat")),
    frozenset(("Tiger", "Monkey")), frozenset(("Rabbit", "Rooster")),
    frozenset(("Dragon", "Dog")), frozenset(("Snake", "Pig")),
}
ZODIAC_HARMONIES = {
    frozenset(("Rat", "Dragon")), frozenset(("Rat", "Monkey")),
    frozenset(("Ox", "Snake")),   frozenset(("Ox", "Rooster")),
    frozenset(("Tiger", "Horse")),frozenset(("Tiger", "Dog")),
    frozenset(("Rabbit", "Goat")),frozenset(("Rabbit", "Pig")),
    frozenset(("Dragon", "Monkey")),
    frozenset(("Snake", "Rooster")),
    frozenset(("Horse", "Dog")),
    frozenset(("Goat", "Pig")),
}

# Role-aware sentence stems
ROLE_FRAMING: Dict[str, Dict[str, str]] = {
    "spouse":      {"context": "as partners sharing daily life",
                    "stakes":  "what gets repeated under the same roof becomes the relationship",
                    "matters": "marriage compounds whatever pattern you don't name"},
    "partner":     {"context": "as partners sharing daily life",
                    "stakes":  "what gets repeated under the same roof becomes the relationship",
                    "matters": "long-term partnership compounds whatever pattern you don't name"},
    "ex_partner":  {"context": "as people who shared a partnership",
                    "stakes":  "what didn't get repaired then is still doing work in you both now",
                    "matters": "the pattern doesn't end when the relationship does"},
    "parent":      {"context": "in a parent-child bond",
                    "stakes":  "what you model is what's inherited — not what you teach",
                    "matters": "this is the elemental inheritance you're passing down"},
    "child":       {"context": "in a parent-child bond",
                    "stakes":  "what was modelled to you is the elemental imprint you're metabolising",
                    "matters": "this dynamic shaped how you relate to all later authority"},
    "sibling":     {"context": "as siblings or chosen family",
                    "stakes":  "shared origin doesn't mean shared signature — siblings often have opposite chemistry",
                    "matters": "this is the lateral relationship that taught you how peers work"},
    "friend":      {"context": "as friends",
                    "stakes":  "friendship is the relationship of voluntary repetition",
                    "matters": "friendships of this elemental signature shape how you do reciprocity"},
    "colleague":   {"context": "as people working alongside each other",
                    "stakes":  "in shared work the elemental friction shows up in how decisions get made",
                    "matters": "this is the operating-mode pairing that determines what you can actually build together"},
    "forum_member":{"context": "as members of the same circle",
                    "stakes":  "even at low intimacy, elemental signatures shape who feels easy and who feels effortful",
                    "matters": "noticing this signature changes how you choose to engage"},
    "other":       {"context": "in this relationship",
                    "stakes":  "the elemental signature is the substrate beneath the words you exchange",
                    "matters": "this is the unspoken layer the relationship runs on"},
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _safe_str(x: Any) -> str:
    return str(x) if x is not None else ""


def _bazi_block(chart: Dict[str, Any]) -> Dict[str, Any]:
    return (chart or {}).get("bazi") or {}


def _day_master(chart: Dict[str, Any]) -> Dict[str, Any]:
    return _bazi_block(chart).get("day_master") or {}


def _year_pillar(chart: Dict[str, Any]) -> Dict[str, Any]:
    return ((_bazi_block(chart).get("pillars") or {}).get("year")) or {}


def _day_pillar(chart: Dict[str, Any]) -> Dict[str, Any]:
    return ((_bazi_block(chart).get("pillars") or {}).get("day")) or {}


def _cycle_dynamic(el_a: str, el_b: str) -> str:
    """Returns one of: 'a_produces_b', 'b_produces_a', 'a_controls_b',
    'b_controls_a', 'same', 'neutral'."""
    if not el_a or not el_b:
        return "neutral"
    if el_a == el_b:
        return "same"
    if ELEMENT_PRODUCES.get(el_a) == el_b:
        return "a_produces_b"
    if ELEMENT_PRODUCES.get(el_b) == el_a:
        return "b_produces_a"
    if ELEMENT_CONTROLS.get(el_a) == el_b:
        return "a_controls_b"
    if ELEMENT_CONTROLS.get(el_b) == el_a:
        return "b_controls_a"
    return "neutral"


def _animal_dynamic(an_a: str, an_b: str) -> str:
    if not an_a or not an_b:
        return "unknown"
    if an_a == an_b:
        return "same"
    pair = frozenset((an_a, an_b))
    if pair in ZODIAC_CLASHES:
        return "clash"
    if pair in ZODIAC_HARMONIES:
        return "harmony"
    return "neutral"


def _role_key(role: Optional[str]) -> str:
    r = (role or "").strip().lower()
    return r if r in ROLE_FRAMING else "other"


# ----------------------------------------------------------------------------
# Section generators — deterministic, ~80-150 words each
# ----------------------------------------------------------------------------

def _sec_core_dynamic(
    name_a: str, name_b: str, el_a: str, el_b: str,
    cycle: str, role_key: str,
) -> str:
    """SECTION 1: Core Dynamic — names the central elemental signature."""
    rk = ROLE_FRAMING[role_key]
    ta = ELEMENT_RELATIONAL_TRAITS.get(el_a, {})
    tb = ELEMENT_RELATIONAL_TRAITS.get(el_b, {})
    a_verb, a_mode = ta.get("verb", "moves"), ta.get("mode", "operating")
    b_verb, b_mode = tb.get("verb", "moves"), tb.get("mode", "operating")

    if cycle == "a_produces_b":
        spine = (
            f"{name_a} is the {a_mode} energy in this pairing; {name_b} is the receiving "
            f"vessel. Your {el_a} feeds {name_b}'s {el_b} — when it works, you're not "
            f"competing for the same air, you're moving in different functions of the same "
            f"system. {name_a} produces, {name_b} metabolises. The elemental geometry means "
            f"the relationship has a natural direction of flow: from {name_a}'s {a_mode} "
            f"into {name_b}'s {b_mode}. Neither person chose this — it's structural. The "
            f"work is to recognise the direction without resenting it."
        )
    elif cycle == "b_produces_a":
        spine = (
            f"{name_b} is the {b_mode} energy that quietly fuels you. Their {el_b} produces "
            f"the conditions your {el_a} needs to land. {name_a} {a_verb} on top of what "
            f"{name_b} has already prepared — even when neither of you names it that way. "
            f"This is not a hierarchy and it's not a debt. It's elemental sequence: "
            f"{name_b}'s {b_mode} comes first in the cycle, and your {a_mode} expresses "
            f"after. The relationship feels easiest when you stop pretending the order goes "
            f"the other way."
        )
    elif cycle == "a_controls_b":
        spine = (
            f"You exert structural pressure on {name_b} whether or not you intend to. "
            f"Your {el_a} {a_verb} their {el_b} — for {name_b} this can feel like being "
            f"held to a standard, refined, or sometimes squeezed. The relationship lives "
            f"in how that pressure gets metabolised. {name_a}'s {a_mode} isn't aggression — "
            f"it's the elemental check that {el_a} naturally exerts on {el_b}. Done with "
            f"consent it sharpens both of you. Done without it, it slowly erodes the "
            f"intimacy you both came here for."
        )
    elif cycle == "b_controls_a":
        spine = (
            f"{name_b} holds you to a standard their {el_b} naturally enforces over your "
            f"{el_a}. You feel checked, refined, sometimes constrained. This is not "
            f"hostility — it is the elemental geometry. {name_b}'s {b_mode} arrives as "
            f"friction against your {a_mode}, and {name_a} usually reads that friction as "
            f"either criticism or withdrawal. Neither is what's happening. The relationship "
            f"matures when {name_a} stops reading the check as rejection and starts hearing "
            f"it as the specific shape of {name_b}'s care."
        )
    elif cycle == "same":
        spine = (
            f"You're both {el_a}. That means deep recognition — {name_a} {a_verb} and "
            f"{name_b} {b_verb} in the same idiom. It also means shared blind spots: "
            f"neither of you brings the missing ingredient by default. The relationship "
            f"feels like a mirror, which is calming until it isn't. Two {el_a}s in a room "
            f"can confirm each other's instincts so thoroughly that nothing in the room "
            f"contradicts you. Recognition is not the same as growth. The shared signature "
            f"is the gift; the missing element is the developmental task."
        )
    else:  # neutral
        spine = (
            f"{el_a} and {el_b} don't sit on a cycle together — neither produces, nor "
            f"controls, the other. The relationship is built more by mutual choice than "
            f"by elemental gravity. {name_a} {a_verb}, {name_b} {b_verb}, and the work is "
            f"to keep choosing the same room. Without the automatic pull of a productive "
            f"or control cycle, this pairing has to construct its own rhythm. The upside "
            f"is freedom from a prewritten dynamic; the downside is that nothing pulls you "
            f"back together when you drift."
        )

    tail = f"Read {rk['context']}, {rk['stakes']}."
    return spine + " " + tail


def _sec_strengthens(
    name_a: str, name_b: str, el_a: str, el_b: str, cycle: str,
    animal: str, support: List[str], role_key: str,
) -> str:
    """SECTION 2: What Strengthens This Relationship."""
    rk = ROLE_FRAMING[role_key]
    pieces: List[str] = []
    if cycle == "a_produces_b":
        pieces.append(
            f"What strengthens you is when {name_a}'s {el_a} delivers "
            f"{PRODUCES_GIFT.get(el_a, 'what it has')} and {name_b} is willing to receive "
            f"it without scoring it. Production needs a receiver. The pairing thrives "
            f"when {name_b} names the gift out loud — even briefly — and when {name_a} "
            f"gives without itemising. Reciprocity in this cycle doesn't mean equal "
            f"output; it means honest acknowledgement of the direction of flow."
        )
    elif cycle == "b_produces_a":
        pieces.append(
            f"What strengthens you is when {name_b}'s {el_b} delivers "
            f"{PRODUCES_GIFT.get(el_b, 'what it has')} and you let it land without "
            f"deflecting. {name_a} growing here means receiving. The pairing thrives "
            f"when you stop performing self-sufficiency and let {name_b}'s contribution "
            f"actually nourish you. {name_b}'s strengthening move is giving without "
            f"keeping a record."
        )
    elif cycle == "a_controls_b":
        pieces.append(
            f"What strengthens you is when {name_a}'s {el_a} brings "
            f"{CONTROLS_PRESSURE.get(el_a, 'specific pressure')} *with consent* — when "
            f"{name_b} has named that they want the refinement, not just received it. "
            f"Consensual pressure builds capacity in {name_b} and integrity in {name_a}. "
            f"Without the consent step, the same dynamic erodes both of you."
        )
    elif cycle == "b_controls_a":
        pieces.append(
            f"What strengthens you is when {name_a} reframes {name_b}'s checks as "
            f"{CONTROLS_PRESSURE.get(el_b, 'useful friction')} rather than as withholding. "
            f"The pressure is doing real work — when {name_a} stops fighting it and starts "
            f"meeting it, the relationship stabilises into a partnership of accountable "
            f"adults rather than a parent-child re-enactment."
        )
    elif cycle == "same":
        pieces.append(
            f"What strengthens you is mutual recognition — neither of you has to translate "
            f"the basics. {el_a}-{el_a} pairs build resilience by sharing a vocabulary that "
            f"few outsiders share. The strength compounds when you both deliberately "
            f"import what {el_a} doesn't supply: another element's perspective, a friend "
            f"who thinks differently, a structured break from the shared idiom."
        )
    else:
        pieces.append(
            f"What strengthens you is intentional reciprocity. With no automatic cycle "
            f"between {el_a} and {el_b}, the relationship runs on the agreements you make, "
            f"not the chemistry you inherit. The pairing thrives on explicit gestures — "
            f"check-ins, shared rituals, named appreciation — that other element-pairs "
            f"can leave implicit and still survive."
        )

    if animal == "harmony":
        pieces.append(
            "Your generational rhythms align — there's an intuitive sense of when to push "
            "and when to pause that you don't have to negotiate."
        )
    elif animal == "same":
        pieces.append(
            "You share the same year animal — pacing and timing feel naturally synced, "
            "which is rare and worth noticing."
        )

    if support:
        pieces.append(f"In practice this shows up as: \"{support[0]}\"")

    return " ".join(pieces)


def _sec_growth_edge(
    name_a: str, name_b: str, el_a: str, el_b: str, cycle: str,
    growth: List[str], role_key: str,
) -> str:
    """SECTION 3: Growth Edge — where the relationship asks each person to stretch."""
    rk = ROLE_FRAMING[role_key]
    if cycle == "a_produces_b":
        spine = (
            f"Your growth edge is acknowledgement asymmetry. Production is invisible labour — "
            f"{name_a} may feel they give more than they receive, while {name_b} may not "
            f"register the giving as a gift at all. The work is making the producing visible "
            f"without turning it into a debt. {name_a} grows by trusting that the giving is "
            f"its own integrity; {name_b} grows by learning to name what's landed before it "
            f"becomes invisible furniture."
        )
    elif cycle == "b_produces_a":
        spine = (
            f"Your growth edge is the opposite of pride: letting {name_b}'s "
            f"{el_b} feed you without immediately reciprocating. Receiving cleanly is a "
            f"skill {name_a} may not have practised. {name_b}'s growth edge is letting "
            f"the giving be the giving — not a leverage point, not a quiet expectation "
            f"that {name_a} will eventually return in kind on {name_b}'s timing."
        )
    elif cycle == "a_controls_b":
        spine = (
            f"Your growth edge is consent around pressure. {name_a}'s {el_a} can refine "
            f"{name_b} — but only if {name_b} has asked for the refinement. Unconsented "
            f"refinement reads as criticism, even when it isn't. Name the pressure out loud. "
            f"{name_a} grows by asking before adjusting; {name_b} grows by separating "
            f"adjustment-with-consent from older experiences of being managed."
        )
    elif cycle == "b_controls_a":
        spine = (
            f"Your growth edge is metabolising being held to a standard you didn't pick. "
            f"{name_a} grows by separating {name_b}'s checks from rejection — the check is "
            f"often love arriving as friction. {name_b}'s growth edge is making the "
            f"standard transparent rather than implicit, so {name_a} knows what they're "
            f"meeting and can choose it freely."
        )
    elif cycle == "same":
        spine = (
            f"Your growth edge is bringing the missing ingredient. Two {el_a}s in a room "
            f"reinforce each other's tendencies — including the blind ones. Growth means "
            f"deliberately importing what {el_a} doesn't supply by default: another "
            f"element's pacing, a friend's blunt question, a structured pause from the "
            f"shared loop. The shared signature is comfortable; growth is the discomfort "
            f"of difference."
        )
    else:
        spine = (
            f"Your growth edge is conscious choice. Without an automatic elemental pull, "
            f"the relationship grows only as much as you both decide it should. Drift is "
            f"the silent risk; intention is the only antidote. Both of you grow by making "
            f"the agreements explicit — what we are to each other, what we're protecting, "
            f"what we're building."
        )

    if growth:
        spine += f" Specifically: \"{growth[0]}\""

    return spine + " " + rk["stakes"].capitalize() + "."


def _sec_shadow(
    name_a: str, name_b: str, el_a: str, el_b: str, cycle: str,
    animal: str, tension: List[str], role_key: str,
) -> str:
    """SECTION 4: Shadow Pattern — the failure mode."""
    sh_a = ELEMENT_RELATIONAL_TRAITS.get(el_a, {}).get("shadow", "overextension")
    sh_b = ELEMENT_RELATIONAL_TRAITS.get(el_b, {}).get("shadow", "overextension")

    if cycle == "a_produces_b":
        spine = (
            f"The shadow is martyrdom on {name_a}'s side and entitlement on {name_b}'s. "
            f"When the producing isn't acknowledged, {name_a} starts keeping a quiet ledger "
            f"of {sh_a}; {name_b} starts treating the gift as a baseline. The relationship "
            f"degrades through silent accounting. By the time either of you names it, the "
            f"ledger has years of entries. The signal that you've entered this shadow is "
            f"sentence-stems like \"I'm always the one who…\" or \"You never notice when…\" "
            f"The early intervention is naming the direction of flow before the resentment "
            f"calcifies into identity."
        )
    elif cycle == "b_produces_a":
        spine = (
            f"The shadow is unrecognised dependency. {name_a} stops noticing how much of "
            f"their stability comes from {name_b}'s {el_b}; {name_b}'s {sh_b} goes "
            f"unattended because they're busy feeding you. The relationship hides its "
            f"asymmetry until it doesn't — usually in a moment where {name_b}'s capacity "
            f"runs out and {name_a} realises the supply was never automatic."
        )
    elif cycle == "a_controls_b":
        spine = (
            f"The shadow is refinement turning into surveillance. {name_a}'s {sh_a} shows "
            f"up as constant adjustment of {name_b}. {name_b} either internalises the "
            f"correction (becomes small) or fights it (becomes brittle). Either way the "
            f"warmth thins. The signature shadow phrase is {name_a} saying \"I'm just "
            f"trying to help\" while {name_b} hears \"you keep getting it wrong.\""
        )
    elif cycle == "b_controls_a":
        spine = (
            f"The shadow is {name_a} reading every check from {name_b} as withdrawal of "
            f"love. {name_a}'s {sh_a} compounds: when held to a standard, they collapse "
            f"toward shame instead of stretching toward the standard. {name_b}'s pressure "
            f"intensifies in response because they read the collapse as not-trying. The "
            f"loop hardens until someone names it."
        )
    elif cycle == "same":
        spine = (
            f"The shadow is shared blind spots becoming shared certainties. Two {el_a}s "
            f"can {sh_a} together and call it conviction. Without an outside element in the "
            f"room, you lose the corrective. The pairing fails most often not by conflict "
            f"but by mutual confirmation — each of you handing the other a permission slip "
            f"for the same avoidance."
        )
    else:
        spine = (
            f"The shadow is parallel living. With no elemental cycle pulling you "
            f"together, you can co-exist for years without actually meeting. {sh_a} on "
            f"one side, {sh_b} on the other, and a polite middle that hides both. The "
            f"warning sign is comfortable distance — the version of peace that's actually "
            f"absence."
        )

    if animal == "clash":
        spine += (
            " The year-animal clash sharpens this: your generational instincts pull in "
            "opposite directions, so the shadow has extra leverage when stress is high."
        )

    if tension:
        spine += f" In practice: \"{tension[0]}\""

    return spine


def _sec_why_matters(
    name_a: str, name_b: str, el_a: str, el_b: str, cycle: str, role_key: str,
) -> str:
    """SECTION 5: Why This Relationship Matters — the developmental significance."""
    rk = ROLE_FRAMING[role_key]
    if cycle == "a_produces_b":
        why = (
            f"This pairing teaches {name_a} that giving without reception is just expense — "
            f"and that naming the giving is not the same as demanding payment. It teaches "
            f"{name_b} that receiving is also a discipline: choosing to register the gift "
            f"before it becomes background. Both lessons are necessary; neither is optional. "
            f"This relationship is the laboratory where you both learn how to participate "
            f"in asymmetric flow without breaking it. The skill compounds — every later "
            f"relationship in your lives will benefit from what you metabolise here."
        )
    elif cycle == "b_produces_a":
        why = (
            f"This pairing teaches {name_a} how to be fed without losing autonomy — how to "
            f"receive without flipping the dynamic into debt. It teaches {name_b} how to "
            f"give without making the giving the whole identity. The relationship matters "
            f"because both of you are learning a skill that the rest of your life will keep "
            f"asking of you."
        )
    elif cycle == "a_controls_b":
        why = (
            f"This pairing teaches {name_a} the difference between refining someone and "
            f"managing them. It teaches {name_b} how to receive structure without "
            f"shrinking inside it. When the lesson lands, both of you become more "
            f"capable in every other relationship you have. When it doesn't, the same "
            f"pattern repeats with different people."
        )
    elif cycle == "b_controls_a":
        why = (
            f"This pairing teaches {name_a} that being held to a standard is a form of "
            f"love when the standard is named — not when it's implicit. It teaches "
            f"{name_b} that pressure has to be transparent to be useful. The lesson is "
            f"specific and it generalises: every other relationship in your life benefits "
            f"when you both metabolise this one."
        )
    elif cycle == "same":
        why = (
            f"This pairing teaches you both that recognition is not the same as growth. "
            f"You will find each other instantly; the work is what you do after. The "
            f"relationship matters because it's the place you both learn that comfort is "
            f"a starting point, not a destination — and that the missing element has to be "
            f"actively invited in, not waited for."
        )
    else:
        why = (
            f"This pairing teaches you both that chemistry isn't a substitute for "
            f"agreement. The relationship rewards what you decide together, not what "
            f"the elements arrange. It matters because it forces a kind of conscious "
            f"relational construction that gravity-driven pairings can skip — and the "
            f"clarity you build here will outlast the relationship itself."
        )
    return f"{why} {rk['matters'].capitalize()}."


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------

def build_relationship_bazi(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
    relationship_role: Optional[str] = None,
    support_signals: Optional[List[str]] = None,
    tension_signals: Optional[List[str]] = None,
    growth_signals: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build the 5-section BaZi narrative card.

    Returns:
        {
            "success": bool,
            "bazi_card": {
                "core_dynamic": str,
                "what_strengthens": str,
                "growth_edge": str,
                "shadow_pattern": str,
                "why_matters": str,
            },
            "diagnostics": {
                "element_a": str, "element_b": str,
                "cycle": str, "animal_a": str, "animal_b": str,
                "animal_relation": str, "role_key": str,
                "support_count": int, "tension_count": int, "growth_count": int,
            },
            "build_marker": "relationship-mapping-bazi-narrative-v1",
        }

    Returns {"success": False, ...} when bazi data is missing on either chart.
    Never raises — defensive by design.
    """
    try:
        dm_a, dm_b = _day_master(chart_a), _day_master(chart_b)
        el_a = _safe_str(dm_a.get("element"))
        el_b = _safe_str(dm_b.get("element"))

        if not el_a or not el_b:
            return {
                "success": False,
                "reason": "missing_day_master_elements",
                "build_marker": BUILD_MARKER,
            }

        cycle = _cycle_dynamic(el_a, el_b)
        yr_a, yr_b = _year_pillar(chart_a), _year_pillar(chart_b)
        animal_a = _safe_str(yr_a.get("animal_name"))
        animal_b = _safe_str(yr_b.get("animal_name"))
        animal_rel = _animal_dynamic(animal_a, animal_b)

        rkey = _role_key(relationship_role)

        # Narrative sections — composed deterministically from element + cycle +
        # role + animal. Each one references the verbatim signal arrays when
        # available, so the evidence layer stays consistent.
        support = list(support_signals or [])
        tension = list(tension_signals or [])
        growth = list(growth_signals or [])

        card = {
            "core_dynamic":      _sec_core_dynamic(name_a, name_b, el_a, el_b, cycle, rkey),
            "what_strengthens":  _sec_strengthens(name_a, name_b, el_a, el_b, cycle, animal_rel, support, rkey),
            "growth_edge":       _sec_growth_edge(name_a, name_b, el_a, el_b, cycle, growth, rkey),
            "shadow_pattern":    _sec_shadow(name_a, name_b, el_a, el_b, cycle, animal_rel, tension, rkey),
            "why_matters":       _sec_why_matters(name_a, name_b, el_a, el_b, cycle, rkey),
        }

        return {
            "success": True,
            "bazi_card": card,
            "diagnostics": {
                "element_a": el_a,
                "element_b": el_b,
                "cycle": cycle,
                "animal_a": animal_a,
                "animal_b": animal_b,
                "animal_relation": animal_rel,
                "role_key": rkey,
                "support_count": len(support),
                "tension_count": len(tension),
                "growth_count": len(growth),
            },
            "build_marker": BUILD_MARKER,
        }
    except Exception as e:  # pragma: no cover — defensive net
        return {
            "success": False,
            "reason": f"engine_exception: {type(e).__name__}: {e}",
            "build_marker": BUILD_MARKER,
        }
