"""
Mirror Object Interpreter — Phase 2 Interpretation Layer
========================================================

Build marker: mirror-interpretation-layer-v1

Replaces the generic "describe a placement" instruction set with
Mirror-native, object-aware interpretation blocks for the advanced
objects recovered by the Phase 1 audit (Vertex, Anti-Vertex, Juno,
Chiron, Lilith, Part of Fortune, Part of Spirit, plus Pholus).

Design contract
---------------

Each interpretation block answers ONE specific Mirror question:

    Part of Fortune    →  What naturally opens for me?
    Part of Spirit     →  What am I consciously trying to become?
    Chiron             →  What wound becomes wisdom?
    Lilith             →  What part of me refuses domestication?
    Juno               →  What does commitment look like in your hands?
    Vertex             →  Which encounters carry unusual weight?
    Anti-Vertex        →  Where do you walk in instead of being pulled?
    Pholus             →  What small choice opens the big door?

Mirror voice rules baked into every block
-----------------------------------------

* Specific, behavioural, observational — never textbook.
* Lead with WHERE this energy SHOWS UP in their life.
* No "this placement suggests…", no "themes of…", no closing
  reflective question, no fortune-cookie generalities.
* Strict word budget (60–140 words) — Mirror is concise.
* Use the user's actual sign + house — these are the only two slots
  the LLM is permitted to vary on.
* For Chiron: no victim framing.
* For Lilith: no fear framing.
* For Fortune: no luck/destiny language; this is FLOW, not gifts.
* For Spirit: this is DELIBERATE evolution, not fate.
* For Juno: not soulmate / not fated partner — how YOU hold commitment.
* For Vertex: not destined-meeting / not karmic — weight of encounter.
* For Anti-Vertex: agency / choosing instead of being chosen.

The interpretation layer does NOT generate prose itself. It builds the
constrained instruction prompt that the lens LLM then fills with the
person's actual placement. This keeps:

  (a) determinism — the same placement always produces the same shape
  (b) personality — the LLM keeps the Mirror voice already established
      elsewhere
  (c) safety — banned phrases are repeated in EVERY block so the model
      cannot drift back into generic astrology talk.

Public API
----------

    has_mirror_interpretation(canonical_name: str) -> bool
    build_mirror_object_proof_block(envelope: Dict) -> str

If `envelope.object` is one we have a Mirror block for, this returns
the Mirror-style prompt. Otherwise it returns "" and the caller falls
back to the generic builder in `natal_object_engine.py`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

BUILD_MARKER = "mirror-interpretation-layer-v1"


# ---------------------------------------------------------------------------
# Per-object Mirror blocks
# ---------------------------------------------------------------------------
#
# Each block is composed of:
#   header      — bracket banner identifying the object + Mirror question
#   reading_set — the 4-6 numbered instruction lines specific to this object
#   universal_floor — banned-phrases + voice contract repeated everywhere
#
# Sign-and-house specifics are NOT pre-baked. We deliberately give the LLM
# the placement and the framing rules, then let it speak from voice.

_UNIVERSAL_VOICE_FLOOR = (
    "▒▒▒ MIRROR INTERPRETATION FRAMEWORK — V3 (BEHAVIOR-FIRST) ▒▒▒\n"
    "\n"
    "SUCCESS TEST (the only test that matters):\n"
    "  When the user reads this paragraph, they must be able to say\n"
    "  'that is exactly what I do' WITHOUT needing to know astrology.\n"
    "  If the interpretation only makes sense to someone who already\n"
    "  understands signs/houses/aspects, the interpretation has failed.\n"
    "\n"
    "VOICE FLOOR (applies to every sentence):\n"
    "  • Mirror describes WHAT HAPPENS — recurring patterns, observable\n"
    "    behaviours, tensions, gifts.  Mirror does NOT describe sign\n"
    "    meanings, house meanings, or astrology definitions.\n"
    "  • 2nd person, present tense, conversational.  Sound like a\n"
    "    careful observer of THIS PERSON, not a teacher of astrology.\n"
    "  • One concrete behaviour or observable tendency per sentence.\n"
    "  • Length: 110–180 words total.  Concise > comprehensive.\n"
    "  • Sign + house are CONTEXT (cited once at the top so the reader\n"
    "    knows what's being read).  After that, do NOT lean on them.\n"
    "    The body of the response is behaviour, not astrology.\n"
    "  • Do NOT mention any other body unless directly contextualising\n"
    "    the requested one.\n"
    "\n"
    "BEHAVIOR-FIRST 4-PART STRUCTURE (use this shape, not the labels):\n"
    "  1. THE PATTERN — what they repeatedly do.\n"
    "     What recurring behaviour shows up in their life? Lead with a\n"
    "     real, observable scene: 'When people bring you a problem,\n"
    "     you rarely solve the problem itself first…'\n"
    "  2. THE TENSION — what works until it doesn't.\n"
    "     The same strength becomes the hiding place under stress.\n"
    "     Name the threshold where the gift turns into avoidance,\n"
    "     control, or self-erasure.\n"
    "  3. THE GIFT — what becomes available when integrated.\n"
    "     What opens when the pattern is met consciously rather than\n"
    "     defaulted into.  Be specific.  Be quietly hopeful, never\n"
    "     coachy.\n"
    "  4. THE OBSERVABLE SIGNAL — what people around them would\n"
    "     actually notice.  One short line.  Example shapes:\n"
    "       'People experience your care long before they hear you\n"
    "        talk about it.'\n"
    "       'Others come to you for perspective before they come to\n"
    "        you for answers.'\n"
    "       'You become the stabilising force in environments that\n"
    "        feel chaotic.'\n"
    "  Do NOT print the labels 'The Pattern', 'The Tension', etc.\n"
    "  The four moves should flow as natural prose, not as headers.\n"
    "\n"
    "HARD BANS (do not use ANY of these phrasings — voice-floor-v3):\n"
    "  • 'this placement…' / 'this placement suggests…' /\n"
    "    'this placement indicates…' / 'this placement invites…' /\n"
    "    'this placement often…' / 'this placement encourages…' /\n"
    "    'this placement reflects…' / 'this placement speaks to…' /\n"
    "    'this placement gives…' / 'this placement is about…'\n"
    "  • 'often manifests as…' / 'often manifests through…' /\n"
    "    'can manifest as…' / 'may manifest as…' / 'tends to manifest…'\n"
    "  • 'speaks to how…' / 'speaks to the way…' / 'speaks of…'\n"
    "  • 'themes of…' / 'the theme here is…'\n"
    "  • 'invites you to…' / 'invites a sense of…' / 'invites growth…'\n"
    "  • 'encourages you to…' / 'encourages a sense of…'\n"
    "  • 'represents…' / 'symbolises…' / 'symbolizes…' / 'stands for…'\n"
    "  • 'archetypally…' / 'as an archetype…' / 'the archetype of…'\n"
    "  • 'where do you notice…?' / closing reflective question of any kind\n"
    "  • Closing platitudes: 'Remember, this doesn't define you', 'this\n"
    "    is just a tool', 'take this with a grain of salt', 'trust your\n"
    "    journey', 'embrace…', 'lean into…' (as a final coachy tail)\n"
    "  • Reflective homework prompts: 'consider journaling…',\n"
    "    'sit with this…', 'a small habit to try…' (UNLESS the block\n"
    "    instruction explicitly asks for a behavioural close)\n"
    "  • Sign-first or house-first framings: 'as a {Sign} placement…',\n"
    "    'the energy of {Sign}…', 'the {Nth} house deals with…' —\n"
    "    Mirror cites sign+house ONCE, then describes the BEHAVIOUR.\n"
    "  • Generic disclaimers: 'as per our agreement…', 'let's stay\n"
    "    grounded in one area at a time' — NEVER invent a prior\n"
    "    instruction; just answer.\n"
    "  • Coaching tone: 'I encourage you to…', 'trust this sense…',\n"
    "    'allow yourself to…', 'give yourself permission to…'\n"
    "\n"
    "MIRROR SOUNDS LIKE 'WHAT TENDS TO HAPPEN', NOT 'WHAT THIS\n"
    "PLACEMENT MEANS'."
)


# ---------------------------------------------------------------------------
# Display-degree helper — Variant-A sign widths are non-uniform (some
# signs span > 30°). Internal `degree` is preserved as the canonical
# within-sign value (e.g. Pallas Leo 33.31° in a 33.34°-wide Leo band).
# But user-facing rendering must NOT surface "33° Leo" because users
# read degrees against a mental 0–29° model.  Display-cap at 29.
# ---------------------------------------------------------------------------
def _display_degree(degree: Any) -> Optional[int]:
    """Return a 0–29 integer for user-facing rendering, or None if
    `degree` isn't numeric. Internal float value stays untouched in the
    envelope; this only affects the proof block string shown to the LLM."""
    if not isinstance(degree, (int, float)):
        return None
    capped = max(0.0, min(float(degree), 29.999))
    return int(capped)


def _format_placement_display(placement: Dict[str, Any]) -> str:
    """Compose a user-safe '{deg}°{sign}' string for proof blocks.
    Falls back to '{sign}' alone when degree is missing or unparseable."""
    sign = placement.get("sign") or "?"
    deg = placement.get("degree")
    d = _display_degree(deg)
    if d is None:
        return sign
    return f"{d}°{sign}"


_MIRROR_BLOCKS: Dict[str, Dict[str, Any]] = {
    # ─────────────────────────────────────────────────────────────────
    # Part of Fortune — natural openings / flow
    # ─────────────────────────────────────────────────────────────────
    "Lot of Fortune": {
        "question": "What naturally opens for me?",
        "headline_hint": "The pathway that asks the least force.",
        "instructions": [
            "Sentence 1: name the SIGN and HOUSE of their Lot of Fortune\n"
            "in plain language. Example: 'Your Fortune sits at\n"
            "{SIGN_PLACEMENT} in the {N}th house.'  After this single\n"
            "sentence, the reader should not see sign/house language\n"
            "again — switch into pure behavioural description.",
            "Then use the BEHAVIOR-FIRST 4-PART STRUCTURE (do not print\n"
            "the labels; write natural prose):\n"
            "  • PATTERN — describe ONE recurring scene where things\n"
            "    open for them without force.  Specific.  Visible.\n"
            "    Example shape: 'When you stop pushing for an outcome\n"
            "    and just show up where you're naturally pulled, the\n"
            "    next step tends to walk up to you.'\n"
            "  • TENSION — what HAPPENS when they try to force this\n"
            "    flow with willpower or hustle instead of letting it\n"
            "    arrive.  Where the gift shuts down under pressure.\n"
            "  • GIFT — what becomes available when they stop muscling\n"
            "    through and trust the natural opening — a concrete\n"
            "    behavioural change, not a feeling.\n"
            "  • OBSERVABLE SIGNAL — one short closing line about what\n"
            "    other people in their life would actually notice when\n"
            "    they're aligned here.",
        ],
        "object_bans": [
            "luck", "destiny", "lucky", "good fortune in the traditional sense",
            "what the universe gives", "blessings", "manifestation",
            "abundance flow", "good vibes",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Part of Spirit — deliberate becoming
    # ─────────────────────────────────────────────────────────────────
    "Lot of Spirit": {
        "question": "What am I consciously trying to become?",
        "headline_hint": "The chosen direction — not fate, intent.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Spirit ONCE in\n"
            "plain language ('Your Spirit sits at {SIGN_PLACEMENT} in\n"
            "the {N}th house.') and then switch immediately into\n"
            "behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the kind of person they're QUIETLY trying\n"
            "    to build through repeated choices.  Show the choice,\n"
            "    not the ideal.\n"
            "  • TENSION — what happens when this deliberate becoming\n"
            "    gets confused with should-do or performance — when\n"
            "    'who I am building' becomes 'who I am supposed to be'.\n"
            "  • GIFT — what becomes available when the direction stays\n"
            "    chosen rather than inherited.  Concrete and quiet.\n"
            "  • OBSERVABLE SIGNAL — what people who know them well\n"
            "    would actually witness as evidence of this becoming.",
        ],
        "object_bans": [
            "soul purpose", "your purpose is", "you were born to",
            "higher self", "ascension", "your soul mission", "destiny",
            "what the universe wants from you",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Chiron — wound becomes wisdom
    # ─────────────────────────────────────────────────────────────────
    "Chiron": {
        "question": "What wound becomes wisdom?",
        "headline_hint": "The growth edge that turns into your teaching.",
        "instructions": [
            "Sentence 1: cite the sign+house of their natal Chiron ONCE\n"
            "('Your Chiron sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "then switch immediately into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the recurring scene where their growth edge\n"
            "    keeps showing up.  A real, observable interaction: the\n"
            "    moment they go quiet, or push back, or over-explain, or\n"
            "    take responsibility for something that isn't theirs.\n"
            "  • TENSION — what works until it doesn't: where the\n"
            "    coping competence becomes the cage.  Stress amplifies\n"
            "    the very pattern they're trying to grow past.\n"
            "  • GIFT — what mature expression looks like in their\n"
            "    actual life.  The exact way they end up able to help\n"
            "    others IN this same area because they've walked it.\n"
            "    Concrete teaching gift, not abstract 'healing'.\n"
            "  • OBSERVABLE SIGNAL — what people around them would\n"
            "    actually notice once this is integrated.  Example\n"
            "    shape: 'Others often come to you for the very thing\n"
            "    you once felt least qualified to offer.'\n"
            "NEVER use victim framing: no 'deep wound', 'old trauma',\n"
            "'unhealed', 'broken'.  This is curriculum, not diagnosis.",
        ],
        "object_bans": [
            "deep wound", "primal wound", "unhealed", "trauma response",
            "broken", "damaged", "victim", "core wound", "you were hurt",
            "soul wound",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Lilith — untamed truth
    # ─────────────────────────────────────────────────────────────────
    "Black Moon Lilith": {
        "question": "What part of me refuses domestication?",
        "headline_hint": "The territory that won't be smoothed over.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Lilith ONCE\n"
            "('Your Lilith sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the recurring moment they REFUSE to perform.\n"
            "    A real scene where they bristle, go cold, or break ranks\n"
            "    rather than make themselves palatable.\n"
            "  • TENSION — what happens when they pretend this edge\n"
            "    isn't there.  Where the performance costs them.  The\n"
            "    exact tax they pay for being agreeable here.\n"
            "  • GIFT — what changes in their life when they STOP\n"
            "    apologising for this part of themselves.  Concrete\n"
            "    behavioural change: how they show up differently in\n"
            "    rooms once this edge is owned.\n"
            "  • OBSERVABLE SIGNAL — what people who underestimated\n"
            "    them eventually notice.  One short line.\n"
            "NOT fear-based.  NOT 'shadow to fix'.  This is sovereign\n"
            "territory, not damage.",
        ],
        "object_bans": [
            "shadow work", "demon", "dark feminine to overcome",
            "the dark side of you", "scary", "scariest", "fear of",
            "be careful", "watch out for", "exiled witch",
        ],
    },

    # Same block for True Lilith — Mirror reads them the same way.
    "True Black Moon Lilith": "__alias__:Black Moon Lilith",

    # ─────────────────────────────────────────────────────────────────
    # Juno — how YOU hold commitment (no soulmate framing)
    # ─────────────────────────────────────────────────────────────────
    "Juno": {
        "question": "What does commitment actually look like in your hands?",
        "headline_hint": "How you weight a bond, not who you'll meet.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Juno ONCE\n"
            "('Your Juno sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — what they actually DO when they commit:\n"
            "    which part of a bond they protect first, what they\n"
            "    ratify, what kind of partnership-architecture they\n"
            "    instinctively build.\n"
            "  • TENSION — the kind of bond where this commitment\n"
            "    style starts costing them.  Where the same quality\n"
            "    that makes them faithful makes them stuck.\n"
            "  • GIFT — what a partner FEELS when they're chosen by\n"
            "    someone with this commitment shape.  The specific\n"
            "    safety their partnership grants.\n"
            "  • OBSERVABLE SIGNAL — what their partners would say\n"
            "    about being with them, in plain language.\n"
            "NEVER use soulmate / twin flame / fated partner /\n"
            "marriage destiny language.  This is about HOW they\n"
            "commit, not WHO they'll meet.",
        ],
        "object_bans": [
            "soulmate", "twin flame", "one true love", "marriage destiny",
            "you'll meet", "your partner will be", "fated to marry",
            "karmic partner",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Vertex — encounter-weight (no destined-meeting framing)
    # ─────────────────────────────────────────────────────────────────
    "Vertex": {
        "question": "Which encounters carry unusual weight in your life?",
        "headline_hint": "Not who you'll meet — what registers when you do.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Vertex ONCE\n"
            "('Your Vertex sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — which life-area tends to host meetings that\n"
            "    punch above their weight.  How they recognise these\n"
            "    contacts in real time (or only in retrospect).\n"
            "  • TENSION — what happens when they MIS-READ these\n"
            "    encounters as fate instead of information.  Where\n"
            "    they over-invest, or wait passively for arrival.\n"
            "  • GIFT — what shifts when they treat these meetings\n"
            "    as data: what changes in how they show up TO them.\n"
            "  • OBSERVABLE SIGNAL — what an outside observer would\n"
            "    notice about who shows up in their life.  One line.\n"
            "NEVER fated meeting / soulmate contact / karmic\n"
            "appointment language — sensitive contact points, not\n"
            "destiny markers.",
        ],
        "object_bans": [
            "fated meeting", "destined to meet", "soulmate contact",
            "karmic appointment", "this person is destined",
            "the universe will send",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Anti-Vertex — agency / choosing in
    # ─────────────────────────────────────────────────────────────────
    "Anti-Vertex": {
        "question": "Where do you walk in instead of being pulled?",
        "headline_hint": "The complementary axis — chosen entry, not magnetism.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Anti-Vertex ONCE\n"
            "('Your Anti-Vertex sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the life-area where they WALK IN rather\n"
            "    than being pulled.  Where their consent and entry\n"
            "    are active.  What they choose toward on purpose.\n"
            "  • TENSION — what happens when they forget this axis\n"
            "    exists and slide into passivity, waiting for things\n"
            "    to find them instead of stepping toward them.\n"
            "  • GIFT — what changes when they consciously USE this\n"
            "    agency.  The concrete behaviour of deliberate entry.\n"
            "  • OBSERVABLE SIGNAL — what people notice when they\n"
            "    show up by choice rather than by drift.",
        ],
        "object_bans": [
            "fated meeting", "destiny", "karmic", "pulled into", "drawn in",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Pholus — small choice / big door
    # ─────────────────────────────────────────────────────────────────
    "Pholus": {
        "question": "What small choice opens the big door?",
        "headline_hint": "The centaur of disproportionate consequence.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Pholus ONCE\n"
            "('Your Pholus sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the life-area where small actions\n"
            "    consistently trigger outsized chains of effect.\n"
            "    Where one decision sets a long arc in motion.\n"
            "  • TENSION — what happens when they treat these\n"
            "    decisions as small ones.  The cost of casual\n"
            "    choices in this exact terrain.\n"
            "  • GIFT — what becomes available when they pause\n"
            "    long enough to notice which choice is the door.\n"
            "  • OBSERVABLE SIGNAL — one line about what the arc\n"
            "    of their life keeps revealing about decisions in\n"
            "    this area.",
        ],
        "object_bans": [
            "karma", "fate", "punishment", "irreversible doom",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Ceres — how you nourish (and what you receive as nourishment)
    # ─────────────────────────────────────────────────────────────────
    "Ceres": {
        "question": "How do you nourish — and what do you accept as care?",
        "headline_hint": "Your care signature in both directions.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Ceres ONCE\n"
            "('Your Ceres sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the specific way they FEED the people\n"
            "    around them.  A real scene.  Show their care\n"
            "    SIGNATURE in action, not the concept of care.\n"
            "  • TENSION — what happens when they give in their\n"
            "    natural shape but can't actually metabolise care\n"
            "    coming BACK at them.  The gap between what they\n"
            "    give and what they can receive.\n"
            "  • GIFT — what changes when they let care arrive in\n"
            "    forms that aren't theirs to control.\n"
            "  • OBSERVABLE SIGNAL — what people in their life\n"
            "    already say (or would say) about being taken care\n"
            "    of by them.  Example shape: 'People experience\n"
            "    your care long before they hear you talk about it.'\n"
            "NO mother-wound / great-mother / earth-mother /\n"
            "goddess language.  Pure mechanics of how care moves\n"
            "in and out of them.",
        ],
        "object_bans": [
            "mother wound", "great mother", "goddess", "smothering",
            "co-dependent", "earth mother", "divine feminine",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Pallas — how you pattern (strategic sight)
    # ─────────────────────────────────────────────────────────────────
    "Pallas": {
        "question": "How do you pattern? Where do you see structure first?",
        "headline_hint": "The strategist underneath the surface.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Pallas ONCE\n"
            "('Your Pallas sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the recurring scene where they SEE the\n"
            "    underlying system before the people around them.\n"
            "    Lead with a real moment: 'When people bring you a\n"
            "    problem, you rarely solve the problem itself first.\n"
            "    You look for the framework underneath it.'\n"
            "  • TENSION — what happens when others want the\n"
            "    surface fix and they keep redrawing the map.  Where\n"
            "    seeing the structure becomes a way to avoid the\n"
            "    messy human layer.\n"
            "  • GIFT — what becomes available when their strategic\n"
            "    sight is paired with willingness to act inside the\n"
            "    messy version of the system, not just the clean one.\n"
            "  • OBSERVABLE SIGNAL — one line about what makes\n"
            "    people seek them out for thinking.  Example: 'Others\n"
            "    often come to you for perspective before they come\n"
            "    to you for answers.'\n"
            "NO warrior-queen / Athena / goddess-of-wisdom framing.",
        ],
        "object_bans": [
            "warrior queen", "sacred wisdom", "divine wisdom",
            "athena archetype", "goddess of wisdom",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Vesta — what you tend (devotion / sacred flame)
    # ─────────────────────────────────────────────────────────────────
    "Vesta": {
        "question": "What do you tend with quiet, ongoing attention?",
        "headline_hint": "The flame you keep alive without being asked.",
        "instructions": [
            "Sentence 1: cite the sign+house of their Vesta ONCE\n"
            "('Your Vesta sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — what they protect with quiet, daily\n"
            "    attention even when nobody's watching.  The thing\n"
            "    they keep tending without being asked.\n"
            "  • TENSION — what happens when this devotion gets\n"
            "    interrupted or pulled apart by competing demands.\n"
            "    Where the loss of focus actually CHANGES them.\n"
            "  • GIFT — what's protected for everyone else because\n"
            "    they keep this fire alive.  The specific value\n"
            "    their devotion creates around them.\n"
            "  • OBSERVABLE SIGNAL — one line about what others\n"
            "    notice when they get to witness this tending.\n"
            "NO virgin-priestess / vestal-virgin / hearth-goddess\n"
            "/ sexuality framing.  This is devoted focus.",
        ],
        "object_bans": [
            "virgin priestess", "hearth goddess", "sacred sexuality",
            "celibacy", "virgin archetype", "vestal virgin",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # North Node — direction of growth (deliberate stretch)
    # ─────────────────────────────────────────────────────────────────
    "North Node": {
        "question": "What direction are you growing toward?",
        "headline_hint": "The unfamiliar muscle the chart is asking you to use.",
        "instructions": [
            "Sentence 1: cite the sign+house of their North Node ONCE\n"
            "('Your North Node sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — the kind of behaviour that feels slightly\n"
            "    unfamiliar but is exactly the stretch their\n"
            "    development keeps pointing toward.  Show it as a\n"
            "    real scene, not a concept.\n"
            "  • TENSION — what happens when they refuse this stretch\n"
            "    and stay in the known.  Where avoidance shows up.\n"
            "  • GIFT — the concrete behavioural change that arrives\n"
            "    when certainty is no longer required before movement\n"
            "    begins.  What opens.\n"
            "  • OBSERVABLE SIGNAL — one line about what people\n"
            "    closest to them would actually witness as evidence\n"
            "    of this growth taking root.\n"
            "NO destiny / fate / soul-contract / past-life language.",
        ],
        "object_bans": [
            "destiny", "fate", "soul contract", "past life",
            "karmic path", "soul mission", "you were born to",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # South Node — what you can put down (overused competence)
    # ─────────────────────────────────────────────────────────────────
    "South Node": {
        "question": "What can you safely put down?",
        "headline_hint": "The overused muscle — competent, but no longer the growth edge.",
        "instructions": [
            "Sentence 1: cite the sign+house of their South Node ONCE\n"
            "('Your South Node sits at {SIGN_PLACEMENT} in the {N}th house.')\n"
            "and immediately switch into behaviour.",
            "Body-specific seeds for the 4-part structure:\n"
            "  • PATTERN — what they ALREADY do well, almost\n"
            "    reflexively, especially under stress.  The exact\n"
            "    competence they default into when life gets\n"
            "    uncertain.  Show a real scene.\n"
            "  • TENSION — competence becomes the HIDING PLACE.\n"
            "    Example shape: 'The more uncertain life feels, the\n"
            "    more tempting it becomes to fix, organise, and\n"
            "    optimise everything around you.'  Name the\n"
            "    specific way this overused muscle stops producing\n"
            "    growth past a certain point.\n"
            "  • GIFT — what they get back when they stop\n"
            "    over-relying on this strength.  The capacity that\n"
            "    becomes free.\n"
            "  • OBSERVABLE SIGNAL — one line about what people\n"
            "    notice when they finally put this down in a\n"
            "    moment where they used to grip it.\n"
            "NO past-life / karmic-debt / soul-debt language.",
        ],
        "object_bans": [
            "past life", "past lives", "soul debt", "karmic debt",
            "previous incarnation", "what you owe",
        ],
    },
}


def _resolve_alias(name: str) -> str:
    """Resolve __alias__ pointers inside _MIRROR_BLOCKS."""
    block = _MIRROR_BLOCKS.get(name)
    if isinstance(block, str) and block.startswith("__alias__:"):
        return block.split(":", 1)[1]
    return name


def has_mirror_interpretation(canonical_name: str) -> bool:
    """True iff this object has a Mirror-native interpretation block."""
    if not canonical_name:
        return False
    resolved = _resolve_alias(canonical_name)
    block = _MIRROR_BLOCKS.get(resolved)
    return isinstance(block, dict)


def build_mirror_object_proof_block(
    envelope: Dict[str, Any],
    chart_owner_name: Optional[str] = None,
) -> str:
    """Build the Mirror-native instruction block for the natal object in
    `envelope`.  Returns "" if we don't have a Mirror block for that
    object — the caller should then fall back to the generic builder
    in natal_object_engine.build_natal_object_proof_block.

    `envelope` is the dict returned by
    services.natal_object_engine.compute_natal_object.

    ADV-OBJ-15 — `chart_owner_name`:
      When the proof block describes a chart owned by someone OTHER than
      the asker (e.g. Forum-tab target-only queries like "Tell me about
      Mel's Juno"), pass the chart owner's display name here.  The
      builder will swap every `'Your <Object> sits at'` instruction
      template into `'<name>'s <Object> sits at'`, removing the
      "you vs Mel" pronoun conflict that previously caused the LLM to
      hallucinate placements.  When `None` (the common self-chart case),
      behaviour is unchanged.
    """
    if not envelope or not envelope.get("success"):
        return ""
    canon = envelope.get("object") or ""
    resolved = _resolve_alias(canon)
    block = _MIRROR_BLOCKS.get(resolved)
    if not isinstance(block, dict):
        return ""

    placement = envelope.get("placement") or {}
    sign = placement.get("sign", "?")
    formatted = _format_placement_display(placement)
    house = placement.get("house")
    house_line = f"House: {house}" if house is not None else "House: (not computed)"

    question_line = block.get("question", "")
    instructions = "\n".join(block.get("instructions", []))
    object_bans = block.get("object_bans") or []

    # ── ADV-OBJ-16 — Pre-substitute placeholders ────────────────────────
    # The instruction templates ship with literal `{SIGN_PLACEMENT}` and
    # `{N}` tokens (e.g. "Your Juno sits at {SIGN_PLACEMENT} in the
    # {N}th house").  When the LLM sees template variables it sometimes
    # ignores them and pulls a "similar" placement from elsewhere in the
    # prompt (FKR block, member summary).  Pre-substituting with the
    # actual envelope values removes that interpretive freedom.
    house_str = str(house) if house is not None else "?"
    instructions = instructions.replace("{SIGN_PLACEMENT}", formatted)
    instructions = instructions.replace("{N}", house_str)

    bans_str = ""
    if object_bans:
        bans_str = "OBJECT-SPECIFIC BAN LIST (do not use any of these):\n"
        bans_str += "  " + ", ".join(sorted(set(object_bans)))

    # ── ADV-OBJ-16 — Authority footer ───────────────────────────────────
    # Add an explicit anti-substitution instruction so the LLM does not
    # swap the proof block's sign/degree/house for a different value
    # pulled from upstream context blocks (FKR member-table, orchestrator
    # addenda, etc.).  Pinned to the SPECIFIC object so the LLM cannot
    # generalise "any Mel placement" into the slot.
    authority_footer = (
        "AUTHORITATIVE PLACEMENT (do not contradict, do not substitute):\n"
        f"  {canon}: {formatted}, house {house_str}\n"
        f"  Use exactly this sign, degree, and house when discussing {canon}.\n"
        f"  Do not substitute another sign, degree, or house from any\n"
        f"  other placement that may be visible elsewhere in this prompt\n"
        f"  (e.g. FKR member tables, planet listings, prior turns).\n"
        f"  If you discuss {canon}, you MUST use only the placement above."
    )

    block = (
        f"━━━━ NATAL OBJECT — MIRROR INTERPRETATION: {canon} ━━━━\n"
        f"Mirror question:  {question_line}\n"
        f"placement:        {formatted}\n"
        f"{house_line}\n"
        f"build:            {BUILD_MARKER}\n"
        f"sign attribution: True Sidereal-M Midpoint (same as natal chart)\n"
        "\n"
        f"{authority_footer}\n"
        "\n"
        f"INSTRUCTION TO YOU:\n{instructions}\n"
        "\n"
        f"{_UNIVERSAL_VOICE_FLOOR}\n"
        "\n"
        f"{bans_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    # ── ADV-OBJ-15 — Target-only pronoun rewrite ────────────────────────
    # When the proof block describes a chart that is NOT the asker's own
    # (Forum-tab "Tell me about Mel's Juno" path), the instruction
    # template lines like "Your Juno sits at {SIGN} in the {N}th house"
    # are addressed to the wrong person.  The LLM resolves that conflict
    # by hallucinating a sign/degree that "sounds Mel-ish".  Rewriting
    # to "Mel's Juno sits at …" eliminates the ambiguity.  Only the
    # instruction-template sentences match this exact phrasing — the
    # universal voice floor uses they/them/their/this person and is
    # untouched.  No-op when chart_owner_name is None.
    if chart_owner_name:
        block = re.sub(
            r"\bYour ([A-Z][\w\- ]*?) sits at\b",
            lambda m: f"{chart_owner_name}'s {m.group(1)} sits at",
            block,
        )

    return block


# ---------------------------------------------------------------------------
# Multi-object Mirror blocks — pairwise + axis
# ---------------------------------------------------------------------------
#
# Single-object queries are the common case. When the user explicitly
# references TWO or more natal objects in one turn (e.g. "Ceres and
# Vesta", "my North Node and South Node"), the dispatcher resolves all
# of them and asks for a UNIFIED interpretation rather than one block
# per body.  Two shapes are supported:
#
#   • axis mode      — North Node ↔ South Node  (polarity reading)
#   • pairwise mode  — any other pair, e.g. Ceres + Vesta
#                      (two short blocks + ONE intersection sentence)
#
# Both honour the same VOICE FLOOR and HARD BANS as single-object reads.


def _placement_line(envelope: Dict[str, Any]) -> str:
    """Compose a single deterministic placement line for envelopes used
    inside multi-object blocks. Falls back gracefully if the envelope is
    not a success envelope (None / unwired)."""
    if not envelope or not envelope.get("success"):
        obj = (envelope or {}).get("object", "?")
        return f"  {obj}: (not computed — engine_message: " \
               f"{(envelope or {}).get('message','unknown')})"
    obj = envelope.get("object", "?")
    p = envelope.get("placement") or {}
    formatted = _format_placement_display(p)
    house = p.get("house")
    house_blurb = f", house {house}" if house is not None else ", house (n/a)"
    return f"  {obj}: {formatted}{house_blurb}"


def build_axis_mirror_block(
    nn_env: Dict[str, Any],
    sn_env: Dict[str, Any],
) -> str:
    """Polarity-style Mirror prompt for the North Node ↔ South Node axis.

    Treats the two nodes as ONE behavioural axis (overused competence on
    the SN end, deliberate stretch on the NN end), not as two separate
    bodies.  Returns the full prompt block.  Either envelope may be a
    failure envelope — in that case the corresponding side of the axis
    becomes 'not computed' but the block still emits so the LLM doesn't
    silently fall back to free-form astrology.
    """
    nn_line = _placement_line(nn_env)
    sn_line = _placement_line(sn_env)
    return (
        "━━━━ NATAL OBJECT — MIRROR INTERPRETATION: Nodal Axis "
        "(North Node ↔ South Node) ━━━━\n"
        "Mirror question:  What can you safely put down — and which "
        "unfamiliar muscle is the chart asking you to use?\n"
        "AXIS placements:\n"
        f"{sn_line}    (the overused, comfortable end)\n"
        f"{nn_line}    (the unfamiliar, growth end)\n"
        f"build:            {BUILD_MARKER}\n"
        "sign attribution: True Sidereal-M Midpoint (same as natal chart)\n"
        "\n"
        "INSTRUCTION TO YOU:\n"
        "Cite both ends of the axis in plain language in the OPENING\n"
        "sentence — South Node sign+house first (the comfortable end),\n"
        "then North Node sign+house (the stretch).  After that single\n"
        "sentence, the rest of the paragraph is BEHAVIOUR, not\n"
        "astrology.\n"
        "\n"
        "Use the BEHAVIOR-FIRST PAIRWISE STRUCTURE (do NOT print the\n"
        "labels — write natural prose with these moves):\n"
        "\n"
        "  SHARED PATTERN — what they REPEATEDLY DO that is the\n"
        "    axis in motion.  The chronic vacating of one for the\n"
        "    other under stress: when life gets uncertain, the SN\n"
        "    behaviour kicks in automatically.  Lead with a real,\n"
        "    observable scene from the SN sign+house — not a concept.\n"
        "\n"
        "  SHARED TENSION — the same competence that has carried\n"
        "    them is now the LID on what's next.  Name the exact\n"
        "    threshold where the SN strength becomes the hiding\n"
        "    place that keeps them from the NN stretch.\n"
        "    Example shape: 'Competence becomes the hiding place.\n"
        "    The more uncertain life feels, the more tempting it\n"
        "    becomes to fix, organise, and optimise everything\n"
        "    around you.'\n"
        "\n"
        "  SHARED GIFT — what becomes available when the NN\n"
        "    stretch is met with the SN strength behind it rather\n"
        "    than INSTEAD of it.  Specific behavioural change.\n"
        "    Example shape: 'The breakthrough often arrives when\n"
        "    certainty is no longer required before movement\n"
        "    begins.'\n"
        "\n"
        "  HOW THEY INTERACT — one paragraph (2–3 sentences) on\n"
        "    the dynamic between the two ends: NOT a sum of two\n"
        "    placements, but how the chronic relationship between\n"
        "    them runs the person's life.  Where the polarity\n"
        "    plays out daily.\n"
        "\n"
        "  OBSERVABLE SIGNAL — ONE short closing line about what\n"
        "    other people would actually witness when the SN is\n"
        "    being put down (even briefly) and the NN is being\n"
        "    chosen.  No coaching homework.\n"
        "\n"
        "Length: 160–230 words total.\n"
        "Do NOT label or section-header the moves; flow as prose.\n"
        "Do NOT use destiny / fate / soul-contract / past-life\n"
        "language.\n"
        "\n"
        f"{_UNIVERSAL_VOICE_FLOOR}\n"
        "\n"
        "AXIS-SPECIFIC BAN LIST (do not use any of these):\n"
        "  past life, past lives, soul debt, karmic debt, karmic path,\n"
        "  previous incarnation, you were born to, destiny, fate,\n"
        "  soul contract, soul mission, what you owe, life purpose\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def build_pairwise_mirror_block(envelopes: list) -> str:
    """Multi-object Mirror prompt for any combination of 2+ bodies that
    is NOT the nodal axis.  Each body gets a short stand-alone read; an
    explicit intersection paragraph forces the LLM to name how they
    interact behaviourally rather than answer one and refuse the rest.

    `envelopes` is a list of natal-object envelopes (from
    services.natal_object_engine.compute_natal_object).
    """
    if not envelopes:
        return ""
    if len(envelopes) == 1:
        return build_mirror_object_proof_block(envelopes[0])

    placement_block = "\n".join(_placement_line(e) for e in envelopes)
    obj_names = [
        (e.get("object") or "?") for e in envelopes if e
    ]
    obj_names_str = " + ".join(obj_names)

    # Mirror questions per body, when known — gives the LLM the framing
    # for each side so it doesn't drift into textbook.
    per_object_questions = []
    for e in envelopes:
        if not e or not e.get("success"):
            continue
        resolved = _resolve_alias(e.get("object") or "")
        spec = _MIRROR_BLOCKS.get(resolved)
        if isinstance(spec, dict):
            q = spec.get("question", "")
            per_object_questions.append(f"  • {e.get('object')} → {q}")
    qmap = (
        "Per-body Mirror question(s):\n" + "\n".join(per_object_questions)
        if per_object_questions
        else ""
    )

    # Collect the merged ban list across every body in the request.
    merged_bans: set[str] = set()
    for e in envelopes:
        if not e or not e.get("success"):
            continue
        resolved = _resolve_alias(e.get("object") or "")
        spec = _MIRROR_BLOCKS.get(resolved)
        if isinstance(spec, dict):
            for b in spec.get("object_bans") or []:
                merged_bans.add(b)
    bans_str = ""
    if merged_bans:
        bans_str = "OBJECT-SPECIFIC BAN LIST (do not use any of these):\n"
        bans_str += "  " + ", ".join(sorted(merged_bans))

    return (
        f"━━━━ NATAL OBJECT — MIRROR INTERPRETATION (pairwise): "
        f"{obj_names_str} ━━━━\n"
        f"placements:\n{placement_block}\n"
        f"build:            {BUILD_MARKER}\n"
        "sign attribution: True Sidereal-M Midpoint (same as natal chart)\n"
        "\n"
        f"{qmap}\n"
        "\n"
        "INSTRUCTION TO YOU:\n"
        "Cite each body's sign+house ONCE in the opening sentence\n"
        "(plain language, one sentence is enough).  After that, the\n"
        "response is BEHAVIOUR, not astrology.\n"
        "\n"
        "Use the BEHAVIOR-FIRST PAIRWISE STRUCTURE (do NOT print the\n"
        "labels — write natural prose with these moves):\n"
        "\n"
        "  SHARED PATTERN — what these two bodies REPEATEDLY DO\n"
        "    TOGETHER in this person's life.  Not a sum of two\n"
        "    placements.  Lead with ONE real, observable scene\n"
        "    where both are clearly in motion at the same time.\n"
        "\n"
        "  SHARED TENSION — the SHARED point where the combined\n"
        "    pattern works until it doesn't.  The exact threshold\n"
        "    where the strengths of both bodies start working\n"
        "    against each other or against the person carrying\n"
        "    them.  Name the cost.\n"
        "\n"
        "  SHARED GIFT — what becomes available when both bodies\n"
        "    are met consciously rather than defaulted into.  A\n"
        "    concrete behavioural change, not a feeling.\n"
        "\n"
        "  HOW THEY INTERACT — one paragraph (2–3 sentences)\n"
        "    naming: ONE concrete place these two patterns\n"
        "    REINFORCE each other in real life, and ONE concrete\n"
        "    place they pull AGAINST each other.  Use specific\n"
        "    everyday scenes, not abstract synthesis.\n"
        "\n"
        "  OBSERVABLE SIGNAL — ONE short closing line about what\n"
        "    other people in their life actually notice when\n"
        "    these two bodies are working together well.\n"
        "\n"
        "Length: 180–260 words total.\n"
        "Do NOT label or section-header the moves; flow as prose.\n"
        "Do NOT refuse to read the second body, do NOT defer one\n"
        "for later, do NOT invent a prior agreement about staying\n"
        "on a single topic.  Both bodies were requested; both get\n"
        "read as ONE behavioural read.\n"
        "\n"
        f"{_UNIVERSAL_VOICE_FLOOR}\n"
        "\n"
        f"{bans_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


# ---------------------------------------------------------------------------
# Public helpers for the dispatcher
# ---------------------------------------------------------------------------
def is_nodal_axis(objects: list) -> bool:
    """Return True if the supplied canonical names form the NN/SN axis."""
    if not objects:
        return False
    norm = {(o or "").strip() for o in objects}
    return ("North Node" in norm) and ("South Node" in norm)
