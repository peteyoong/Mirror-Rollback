"""
RELATIONSHIP BaZi ENGINE — v3 (Wisdom Mode)
Each of the 6 sections answers a distinct, non-overlapping question:

  1. Core Dynamic        → What naturally HAPPENS between these two people?
  2. What Strengthens    → What conditions make the flow run clean?
  3. Growth Edge         → What lesson is each person being asked to learn?
  4. Shadow Pattern      → How does this relationship FAIL when unconscious?
  5. Why This Matters    → Where does this pairing fit in the larger arc of life?
  6. What BaZi Sees Here → One integrated insight that names the meaning.

Inputs are unchanged from v1: chart.bazi.day_master.element on both charts,
year-animal harmony/clash, and the existing compute_bazi_signals output
(support/tension/growth arrays). No BaZi math is modified. No chart writes.

BUILD MARKER: relationship-mapping-bazi-narrative-v1   (preserved for forensic continuity)
WISDOM MARKER: relationship-mapping-bazi-wisdom-v3
"""
from typing import Any, Dict, List, Optional

BUILD_MARKER = "relationship-mapping-bazi-narrative-v1"
WISDOM_MARKER = "relationship-mapping-bazi-wisdom-v3"

# ───────────────────────────────────────────────────────────────────────────
# Wu Xing — productive + control cycles (local copies; no coupling to engine math)
# ───────────────────────────────────────────────────────────────────────────
ELEMENT_PRODUCES = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal",
                    "Metal": "Water", "Water": "Wood"}
ELEMENT_CONTROLS = {"Wood": "Earth", "Fire": "Metal", "Earth": "Water",
                    "Metal": "Wood", "Water": "Fire"}

# Phenomenological language — how each element shows up *between* people.
# (Used by sections 1 and 6; not repeated in 2-5.)
# `verb_phrase` slots into "Whatever A brings — A {verb_phrase} — meets..."
# `essence` is a noun form used by the synthesis closer.
ELEMENT_PHENOMENON = {
    "Wood":  {"verb_phrase": "extends outward, opens new room",
              "essence":     "becoming"},
    "Fire":  {"verb_phrase": "burns warm and visible, takes up the air",
              "essence":     "presence"},
    "Earth": {"verb_phrase": "holds the ground, slows the room",
              "essence":     "containment"},
    "Metal": {"verb_phrase": "refines, names, makes things precise",
              "essence":     "discernment"},
    "Water": {"verb_phrase": "deepens, adapts, finds the lowest true point",
              "essence":     "knowing"},
}

# Year-animal harmony tables — same as forum_hd_mapping.
ZODIAC_CLASHES = {frozenset(p) for p in [
    ("Rat","Horse"),("Ox","Goat"),("Tiger","Monkey"),
    ("Rabbit","Rooster"),("Dragon","Dog"),("Snake","Pig")]}
ZODIAC_HARMONIES = {frozenset(p) for p in [
    ("Rat","Dragon"),("Rat","Monkey"),("Ox","Snake"),("Ox","Rooster"),
    ("Tiger","Horse"),("Tiger","Dog"),("Rabbit","Goat"),("Rabbit","Pig"),
    ("Dragon","Monkey"),("Snake","Rooster"),("Horse","Dog"),("Goat","Pig")]}

# Role-aware framings — used only in sections 5 (larger arc) and 6 (synthesis).
# Section 1-4 are role-agnostic so we don't repeat the role framing across all six.
ROLE_LARGER_ARC = {
    "spouse":      "what you metabolise here is what your shared life will be made of, and what your children, if any, will inherit as the shape of love itself",
    "partner":     "what you metabolise here is what your shared life will be made of",
    "ex_partner":  "what didn't get integrated then is still doing developmental work in both of you now",
    "parent":      "this is the elemental imprint you are passing down, named or unnamed",
    "child":       "this dynamic taught you what care looks like, before you had words for it",
    "sibling":     "this is the lateral relationship that taught you how peers work, and you've been running variations of it ever since",
    "friend":      "this is the elemental signature your closest friendships keep selecting — you've been here before with other names",
    "colleague":   "this is the operating-mode pairing that determines what you can actually build together — and what you will keep almost-building",
    "forum_member":"even at low intimacy, the signature is doing real work — noticing it changes how you choose to engage",
    "other":       "this dynamic is the substrate beneath every conversation you've ever had with each other",
}
ROLE_SYNTHESIS_OPEN = {
    "spouse":      "a marriage",
    "partner":     "a partnership",
    "ex_partner":  "a partnership that ended but isn't finished",
    "parent":      "a parent-child bond",
    "child":       "a parent-child bond",
    "sibling":     "a sibling relationship",
    "friend":      "a friendship",
    "colleague":   "a working partnership",
    "forum_member":"a connection",
    "other":       "this relationship",
}


# ───────────────────────────────────────────────────────────────────────────
# helpers
# ───────────────────────────────────────────────────────────────────────────
def _bazi(c): return (c or {}).get("bazi") or {}
def _dm(c):   return _bazi(c).get("day_master") or {}
def _yr(c):   return ((_bazi(c).get("pillars") or {}).get("year")) or {}
def _safe(x): return str(x) if x is not None else ""

def _cycle(a, b):
    if not a or not b: return "neutral"
    if a == b: return "same"
    if ELEMENT_PRODUCES.get(a) == b: return "a_produces_b"
    if ELEMENT_PRODUCES.get(b) == a: return "b_produces_a"
    if ELEMENT_CONTROLS.get(a) == b: return "a_controls_b"
    if ELEMENT_CONTROLS.get(b) == a: return "b_controls_a"
    return "neutral"

def _animal(a, b):
    if not a or not b: return "unknown"
    if a == b: return "same"
    pair = frozenset((a, b))
    if pair in ZODIAC_CLASHES: return "clash"
    if pair in ZODIAC_HARMONIES: return "harmony"
    return "neutral"

def _role_key(r):
    rk = (r or "").strip().lower()
    return rk if rk in ROLE_LARGER_ARC else "other"


# ───────────────────────────────────────────────────────────────────────────
# SECTION GENERATORS — each answers a distinct question. No idea overlap.
# ───────────────────────────────────────────────────────────────────────────

# ── 1. CORE DYNAMIC — phenomenological observation only.
#    Names what is OBSERVABLE in the room. Avoids: lessons, failure modes,
#    conditions, larger meaning. Just: what naturally happens.
def _s1_core(a, b, el_a, el_b, cycle):
    pa = ELEMENT_PHENOMENON.get(el_a, {})
    pb = ELEMENT_PHENOMENON.get(el_b, {})
    if cycle == "a_produces_b":
        return (
            f"There is a current in this relationship that runs one way. {a} "
            f"{pa.get('verb_phrase','arrives first into the room')}, and meets something "
            f"in {b} that takes shape in response. {b} doesn't try to match {a}'s form, "
            f"and doesn't try to slow it down. {b} simply receives, and what {b} becomes "
            f"after receiving is what you both end up living with. Watch the room: {a} "
            f"arrives first into any moment, names it, sets a shape. {b} settles into the "
            f"shape, and the shape becomes warmer for being inhabited. Neither of you has "
            f"chosen this. It is the geometry of {el_a} meeting {el_b} — production "
            f"downstream, reception upstream — observable in every ordinary exchange."
        )
    if cycle == "b_produces_a":
        return (
            f"What naturally happens in this room is that {b} sets the conditions and {a} "
            f"becomes possible inside them. {b} {pb.get('verb_phrase','prepares the ground')}; "
            f"{a} then {pa.get('verb_phrase','expresses against that ground')}. Neither of "
            f"you experiences this as hierarchy because it isn't one — it is sequence. {b} "
            f"comes first in the elemental cycle, not first in importance. You can watch "
            f"it in the small choices: {b} adjusts something invisible, and a few minutes "
            f"later {a} does something that depended on that adjustment without knowing "
            f"it. The relationship runs on this quiet upstream-downstream rhythm. It is "
            f"the natural phenomenon of {el_b} producing {el_a}."
        )
    if cycle == "a_controls_b":
        return (
            f"What happens between you is structural friction with a direction. {a}'s {el_a} "
            f"naturally checks {b}'s {el_b} — not as criticism, not as control in the "
            f"hostile sense, but as the geometric pressure that {el_a} exerts on {el_b} "
            f"wherever they meet. {b} feels it as being held against an edge: refined when "
            f"the contact is welcome, squeezed when it isn't. {a} usually doesn't experience "
            f"themselves as exerting anything — the pressure is so native it reads as just "
            f"caring. Observe carefully and you'll see it in the texture of every "
            f"disagreement: {a} adjusts, {b} either stretches or contracts."
        )
    if cycle == "b_controls_a":
        return (
            f"What happens here is {b} steadily holding {a} against a shape {a} did not "
            f"choose. {b}'s {el_b} naturally exerts a check on {a}'s {el_a}: it slows you "
            f"down, refines what you're doing, sometimes contradicts what you thought you "
            f"wanted. {b} rarely intends this as friction — it's just how {el_b} occupies "
            f"the same room as {el_a}. {a} feels it as a kind of weather pattern in the "
            f"relationship: something that shapes everything but is hard to point at. The "
            f"phenomenon is observable in how decisions land: {a} proposes, {b}'s presence "
            f"alone changes what gets proposed."
        )
    if cycle == "same":
        return (
            f"What happens in this room is mutual recognition without translation. Both of "
            f"you {pa.get('observable','share the same operating mode')}. There is no "
            f"explaining the basics; there is also no contrast bringing anything into "
            f"relief. The relationship runs on a shared frequency that outsiders often "
            f"can't hear. You finish each other's elemental sentences — sometimes literally — "
            f"and you reach the same conclusions through the same reasoning. Watch the "
            f"texture: agreement arrives early, disagreement is rare and feels jarring "
            f"because it's stepping out of a shared idiom. This is the phenomenon of two "
            f"{el_a}s in one room — comfortable, recognisable, and unusually mirrored."
        )
    # neutral
    return (
        f"What happens between {a} and {b} is the absence of automatic pull. {el_a} and "
        f"{el_b} don't sit on a cycle together — neither feeds nor checks the other — so "
        f"the room has no built-in direction. You can watch this in any joint decision: "
        f"there is no elemental gravity choosing for you. What you build together you have "
        f"to build deliberately, and what falls apart falls apart from neglect rather than "
        f"from collision. The natural phenomenon here is parallel-ness: two distinct "
        f"operating modes that can coexist for years without ever quite meeting, unless "
        f"someone chooses to make them meet."
    )


# ── 2. WHAT STRENGTHENS — conditions / behaviours. No mention of lessons,
#    shadows, or larger arc. Just: what makes the flow run clean today.
def _s2_strengthens(a, b, el_a, el_b, cycle, animal, support):
    if cycle == "a_produces_b":
        body = (
            f"The flow runs clean when neither of you reads the asymmetry as a problem to "
            f"solve. {a} stops measuring the giving against any expected return; {b} stops "
            f"apologising for needing what {b} clearly needs. What remains is the dynamic "
            f"itself, doing its work. Three conditions help: {b} names a received gift "
            f"briefly and out loud, often, so the flow stays visible; {a} gives without "
            f"itemising, treating the producing as its own integrity; and both of you "
            f"refuse the temptation to compare contributions in different currencies. "
            f"Where these three conditions hold, the relationship feels effortless even "
            f"when the work is real."
        )
    elif cycle == "b_produces_a":
        body = (
            f"The flow runs clean when {a} stops performing self-sufficiency and lets {b}'s "
            f"upstream contribution actually land. The condition is permeability. When {a} "
            f"deflects the support — even politely, even by reciprocating immediately — the "
            f"sequence breaks and both of you end up working harder. The other condition is "
            f"{b}'s discipline of giving without quietly attaching a timeline. The "
            f"relationship strengthens when receiving and giving are both allowed to be "
            f"unhurried, with no covert accounting between them."
        )
    elif cycle == "a_controls_b":
        body = (
            f"The flow runs clean only when the pressure is named. {a} asks before "
            f"adjusting. {b} either consents to the refinement or declines it without "
            f"penalty. Both of you treat unconsented refinement as off-limits — not because "
            f"it would be cruel but because it bypasses the only mechanism that keeps "
            f"this dynamic from sliding into management. The condition is transparency: "
            f"the standard {a} is holding {b} to is spoken aloud, regularly, so {b} can "
            f"choose it freely rather than guess at it."
        )
    elif cycle == "b_controls_a":
        body = (
            f"The flow runs clean when {a} stops reading {b}'s checks as withdrawal. The "
            f"condition is reframe: {b}'s pressure is not the opposite of love — it is the "
            f"specific shape {b}'s love takes. {b}'s contribution to the same condition is "
            f"making the standard visible rather than implicit, so {a} can meet a stated "
            f"expectation instead of trying to read minds. When both of these conditions "
            f"hold, the friction becomes generative; when either is missing, it doesn't."
        )
    elif cycle == "same":
        body = (
            f"The flow runs clean when you both deliberately import what {el_a} doesn't "
            f"supply by default. The condition isn't difference for its own sake — it is "
            f"importing a missing element: a friend whose temperament contradicts yours, a "
            f"shared practice that requires what {el_a} resists, a routine pause from each "
            f"other so you can both bring back something the shared idiom can't generate. "
            f"Two {el_a}s strengthen by refusing to be each other's whole world."
        )
    else:
        body = (
            f"The flow runs clean only on explicit agreement. The condition is conscious "
            f"choice: you both name what you want this relationship to be, you both name "
            f"what you're protecting, and you make the implicit terms explicit. Without "
            f"the automatic pull of a cycle, the relationship survives only on the strength "
            f"of what you both decide to keep choosing."
        )
    # Animal harmony is a strengthener — only mention here, never repeated.
    if animal == "harmony":
        body += (
            " Your year-animal harmony gives the dynamic a natural pacing — you don't "
            "have to negotiate timing the way most pairs do."
        )
    elif animal == "same":
        body += (
            " Sharing the same year animal means your sense of when to push and when to "
            "rest is already synchronised."
        )
    # Quote one concrete signal as evidence, never more — keeps section focused.
    if support:
        body += f" In practice: \"{support[0]}\""
    return body


# ── 3. GROWTH EDGE — the developmental task each person is being asked to take on.
#    Distinct from conditions (section 2) and from shadow (section 4) and from
#    larger arc (section 5). Speaks ONLY to the individual lesson per person.
def _s3_growth(a, b, el_a, el_b, cycle, growth):
    if cycle == "a_produces_b":
        body = (
            f"{a} is being asked to learn that integrity is not the same as reception. The "
            f"work {a} does has its own truth even when no one is tracking it — the giving "
            f"is not invalidated by going unnoticed, and demanding acknowledgement converts "
            f"the gift into a transaction. {b}'s lesson is harder and quieter: how to "
            f"receive without converting the gift into debt, and without disappearing "
            f"inside someone else's care. Receiving cleanly is a specific skill — it asks "
            f"{b} to stay distinct while being fed. Both lessons are about the difference "
            f"between flow and exchange, and neither person can learn theirs by waiting "
            f"for the other to learn first."
        )
    elif cycle == "b_produces_a":
        body = (
            f"{a} is being asked to learn how to be fed without losing autonomy — how to "
            f"let something land without immediately flipping the dynamic into debt or "
            f"obligation. That lesson is uncomfortable for anyone who has built an identity "
            f"around self-supply. {b}'s lesson is the harder mirror image: how to give "
            f"without making the giving into an identity. {b} is being asked to discover "
            f"that they exist outside the role of contributor, and that ceasing to give for "
            f"a season does not collapse who they are."
        )
    elif cycle == "a_controls_b":
        body = (
            f"{a}'s lesson is the difference between refining someone and managing them. "
            f"Refinement requires consent; management proceeds without it. The work is to "
            f"keep noticing where the line is — and to stop the moment it is crossed, "
            f"without scoring it as a personal failure. {b}'s lesson is to receive "
            f"consented-to pressure without contracting, to stretch toward a standard "
            f"without reading it as evidence that the unstandardised version of {b} was "
            f"unloved. Both lessons require the courage to stay distinct under contact."
        )
    elif cycle == "b_controls_a":
        body = (
            f"{a} is being asked to learn that being held to a standard is a form of love "
            f"when the standard is named, and that contraction under that pressure is "
            f"optional — there is a third response between rebellion and shame. {b}'s "
            f"lesson is to make the standard transparent rather than implicit, so {a} can "
            f"meet it as a stated expectation rather than read it from {b}'s mood. Both "
            f"lessons are about turning weather into language."
        )
    elif cycle == "same":
        body = (
            f"The shared lesson is the discomfort of difference. Two {el_a}s in a room can "
            f"confirm each other's instincts so thoroughly that growth requires deliberately "
            f"importing what {el_a} doesn't generate. Each of you is being asked to seek "
            f"out the missing element — in friends, in practices, in moments of solitude — "
            f"and then to bring what you've learned back into the room. The work is "
            f"refusing the comfort of total agreement."
        )
    else:
        body = (
            f"The lesson here is choice without gravity. Both of you are being asked to "
            f"build something that has no elemental pull holding it together — to make the "
            f"agreements explicit, to repeat them, and to discover that consciously-built "
            f"relationships are not weaker than gravity-driven ones, only more honest "
            f"about their construction."
        )
    if growth:
        body += f" Concretely: \"{growth[0]}\""
    return body


# ── 4. SHADOW PATTERN — the failure mode when the lesson goes unlearned.
#    Distinct from growth (which names the task); shadow names what happens
#    when the task is avoided. No mention of conditions, lessons explicitly,
#    or larger arc — only the precise shape of the failure.
def _s4_shadow(a, b, el_a, el_b, cycle, animal, tension):
    if cycle == "a_produces_b":
        body = (
            f"When this dynamic fails, it does so silently. {a} stops bringing the precise "
            f"thing because no one seems to be tracking it; {b} stops feeling fed and "
            f"starts feeling indebted, then resents the debt. The relationship becomes a "
            f"polite arrangement around an exhausted core. By the time you can name it, "
            f"the giving has stopped and neither of you remembers when. The early signature "
            f"is a quiet ledger forming on {a}'s side — kept silently, never discussed — "
            f"and a faint suspicion forming on {b}'s side that the care comes with strings."
        )
    elif cycle == "b_produces_a":
        body = (
            f"The failure mode here is unrecognised dependency. {a} stops noticing how much "
            f"of their stability is upstream of {b}'s {el_b}; {b}'s own needs go "
            f"unattended because {b} is busy preparing the ground for {a}. The relationship "
            f"hides its asymmetry until one day {b}'s capacity runs out and {a} discovers "
            f"the supply was never automatic. The hidden ending is a sudden boundary that "
            f"reads as betrayal but was actually long overdue."
        )
    elif cycle == "a_controls_b":
        body = (
            f"The failure mode is refinement turning into surveillance. {a} starts to "
            f"adjust {b} without asking — small corrections that read as care from inside "
            f"{a} and as supervision from inside {b}. {b} either internalises the "
            f"corrections and shrinks, or fights them and becomes brittle. Either way the "
            f"warmth thins. The signature phrase is {a} saying \"I'm just trying to help\" "
            f"while {b} hears \"you keep getting it wrong,\" and neither of you can find "
            f"the moment the disconnect started."
        )
    elif cycle == "b_controls_a":
        body = (
            f"The failure mode is a closed loop of shame and intensification. {a} reads "
            f"every check from {b} as withdrawal of love and collapses toward "
            f"self-criticism instead of stretching toward the standard. {b} reads the "
            f"collapse as not-trying and intensifies the pressure. The loop tightens until "
            f"both of you are convinced the other person is the problem, and neither of "
            f"you can see the geometry that's actually running the room."
        )
    elif cycle == "same":
        body = (
            f"The failure mode is shared blind spots becoming shared certainties. Two "
            f"{el_a}s can avoid the same things together and call it conviction. Without "
            f"an outside element in the room, you lose the corrective — your shared "
            f"signature confirms itself, and what's missing stays missing because nothing "
            f"in the relationship asks for it. The pairing fails most often not by conflict "
            f"but by mutual confirmation of the same avoidance."
        )
    else:
        body = (
            f"The failure mode is parallel living. Without an elemental pull, you can "
            f"co-exist for years without quite meeting — comfortable distance that reads "
            f"as peace from inside but is actually absence. The warning sign is the "
            f"quietness: not the quiet of agreement but the quiet of two people who have "
            f"stopped expecting much from each other and have not yet noticed."
        )
    if animal == "clash":
        body += (
            " The year-animal clash sharpens this: under stress, your generational "
            "instincts pull in opposite directions, so the failure mode gets extra leverage."
        )
    if tension:
        body += f" Visible as: \"{tension[0]}\""
    return body


# ── 5. WHY THIS RELATIONSHIP MATTERS — larger-arc significance only.
#    Distinct from shadow (failure), growth (lesson), conditions (strengthens).
#    Speaks to WHERE this pairing fits in the longer story of both lives.
def _s5_matters(a, b, el_a, el_b, cycle, role_key):
    arc = ROLE_LARGER_ARC.get(role_key, ROLE_LARGER_ARC["other"])
    if cycle == "a_produces_b":
        body = (
            f"Pairings of this elemental signature are where two people learn to participate "
            f"in love without a balance sheet. {a} learns that giving can be the work itself, "
            f"not a deposit toward a future return. {b} learns that receiving is also "
            f"craftsmanship — that being fed requires its own kind of presence. These are "
            f"developmental tasks the rest of life keeps testing in different forms. In "
            f"this specific bond, "
        )
    elif cycle == "b_produces_a":
        body = (
            f"This pairing is where {a} discovers how to be supported without converting "
            f"support into debt, and where {b} discovers an identity that is not "
            f"co-extensive with contribution. Both discoveries shape every later "
            f"relationship in both of your lives — friendships, work partnerships, the "
            f"way you each show up for your own bodies. In this specific bond, "
        )
    elif cycle == "a_controls_b":
        body = (
            f"This pairing is the laboratory where {a} learns to refine someone without "
            f"managing them — a distinction that turns out to apply everywhere, from "
            f"parenting to leadership to friendship. {b} learns to be sharpened without "
            f"being diminished, which is one of the rarer adult skills. Both lessons "
            f"generalise. In this specific bond, "
        )
    elif cycle == "b_controls_a":
        body = (
            f"This pairing is where {a} learns the difference between being checked and "
            f"being unloved, and where {b} learns the difference between exerting "
            f"transparent pressure and assuming you'll be intuited. Both of these "
            f"distinctions migrate outward into the rest of your relational lives. In "
            f"this specific bond, "
        )
    elif cycle == "same":
        body = (
            f"This pairing is where you both discover that recognition is the beginning of "
            f"the work, not the end of it. Mirror-pairings of the same element teach you "
            f"that comfort without difference produces stasis — and that the missing "
            f"element has to be invited in rather than waited for. In this specific bond, "
        )
    else:
        body = (
            f"This pairing teaches both of you that consciously-built relationships can be "
            f"as load-bearing as gravity-driven ones — that chemistry is one path to "
            f"intimacy and explicit agreement is another, and the second path produces "
            f"clarity the first one often skips. In this specific bond, "
        )
    return body + arc + "."


# ── 6. WHAT BaZi SEES HERE — synthesis. One memorable insight, 60-110 words.
#    Pulls element + animal + cycle + role together into a single image.
def _s6_synthesis(a, b, el_a, el_b, cycle, animal, role_key, support, tension, growth):
    arc_open = ROLE_SYNTHESIS_OPEN.get(role_key, ROLE_SYNTHESIS_OPEN["other"])
    pa = ELEMENT_PHENOMENON.get(el_a, {}).get("essence", "their nature")
    pb = ELEMENT_PHENOMENON.get(el_b, {}).get("essence", "their nature")

    if cycle == "a_produces_b":
        spine = (
            f"BaZi sees {arc_open} that is not a contract but a cycle. {a}'s {pa} feeds "
            f"{b}'s {pb}, and the work of this lifetime is to let that be enough — to "
            f"stop translating the geometry into a ledger, to stop asking whether it's "
            f"fair, and to discover that what looks like asymmetry up close is a closed "
            f"loop when seen from far away. Pete is not over-giving; Mel is not "
            f"under-giving. The current is moving in one direction because the elements "
            f"asked it to."
        ).replace("Pete", a).replace("Mel", b)
    elif cycle == "b_produces_a":
        spine = (
            f"BaZi sees {arc_open} held up by an upstream contribution most relationships "
            f"would miss. {b} prepares the ground; {a} grows in it. Both of you are "
            f"halves of one motion, not two competing claims on the same air. The wisdom "
            f"is to honour the sequence without ranking it."
        )
    elif cycle == "a_controls_b":
        spine = (
            f"BaZi sees {arc_open} built on consented friction. {a}'s {pa} can refine "
            f"{b}'s {pb} — but only when {b} chooses the refinement freely. The whole "
            f"relationship turns on that one variable: consent. Where consent holds, the "
            f"friction is generative. Where it doesn't, the same friction corrodes."
        )
    elif cycle == "b_controls_a":
        spine = (
            f"BaZi sees {arc_open} structured around named pressure. {b}'s {pb} holds {a} "
            f"to a standard, and the standard is love rather than rejection — but only "
            f"once it is spoken aloud. The whole bond depends on making the implicit "
            f"explicit. Translation is the work."
        )
    elif cycle == "same":
        spine = (
            f"BaZi sees {arc_open} between two people running on the same frequency. "
            f"Recognition is instant; difference must be deliberately imported. The "
            f"developmental task is to refuse the comfort of total agreement and bring "
            f"in what {el_a} doesn't generate."
        )
    else:
        spine = (
            f"BaZi sees {arc_open} that has no elemental gravity holding it together — "
            f"and that's the gift, not the problem. What you build here, you build by "
            f"choice. What survives, survives by agreement. That's a stronger foundation "
            f"than chemistry, just less spectacular."
        )

    # Animal closer: one short clause from harmony/clash, never repeated elsewhere.
    if animal == "clash":
        spine += " The year-animal clash adds drag under stress, but does not change the central truth of the pair."
    elif animal == "harmony":
        spine += " The year-animal harmony gives the dynamic an unusually intuitive sense of pacing."
    elif animal == "same":
        spine += " Sharing the same year animal lets the timing of the bond run quiet."

    return spine


# ───────────────────────────────────────────────────────────────────────────
# Public API — same signature as v1 to keep callers untouched.
# ───────────────────────────────────────────────────────────────────────────
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
    try:
        el_a = _safe(_dm(chart_a).get("element"))
        el_b = _safe(_dm(chart_b).get("element"))
        if not el_a or not el_b:
            return {"success": False, "reason": "missing_day_master_elements",
                    "build_marker": BUILD_MARKER, "wisdom_marker": WISDOM_MARKER}

        cycle = _cycle(el_a, el_b)
        animal_a = _safe(_yr(chart_a).get("animal_name"))
        animal_b = _safe(_yr(chart_b).get("animal_name"))
        animal_rel = _animal(animal_a, animal_b)
        rkey = _role_key(relationship_role)

        support = list(support_signals or [])
        tension = list(tension_signals or [])
        growth = list(growth_signals or [])

        card = {
            "core_dynamic":      _s1_core(name_a, name_b, el_a, el_b, cycle),
            "what_strengthens":  _s2_strengthens(name_a, name_b, el_a, el_b, cycle, animal_rel, support),
            "growth_edge":       _s3_growth(name_a, name_b, el_a, el_b, cycle, growth),
            "shadow_pattern":    _s4_shadow(name_a, name_b, el_a, el_b, cycle, animal_rel, tension),
            "why_matters":       _s5_matters(name_a, name_b, el_a, el_b, cycle, rkey),
            # NEW v3: integrative synthesis
            "what_bazi_sees":    _s6_synthesis(name_a, name_b, el_a, el_b, cycle, animal_rel, rkey,
                                                support, tension, growth),
        }

        return {
            "success": True,
            "bazi_card": card,
            "diagnostics": {
                "element_a": el_a, "element_b": el_b, "cycle": cycle,
                "animal_a": animal_a, "animal_b": animal_b,
                "animal_relation": animal_rel, "role_key": rkey,
                "support_count": len(support), "tension_count": len(tension),
                "growth_count": len(growth),
            },
            "build_marker": BUILD_MARKER,
            "wisdom_marker": WISDOM_MARKER,
        }
    except Exception as e:  # pragma: no cover
        return {"success": False,
                "reason": f"engine_exception: {type(e).__name__}: {e}",
                "build_marker": BUILD_MARKER, "wisdom_marker": WISDOM_MARKER}
