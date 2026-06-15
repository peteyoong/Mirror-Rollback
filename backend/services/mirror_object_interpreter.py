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
    "VOICE FLOOR (applies to every sentence):\n"
    "  • Speak in 2nd person, present tense, conversational. Sound like\n"
    "    a careful observer of THIS PERSON, not a teacher of astrology.\n"
    "  • Lead with what HAPPENS in their life. Mirror reads behaviour,\n"
    "    tension, trade-offs, and recurring patterns — not what a body\n"
    "    'represents' or 'symbolises'.\n"
    "  • Behavioural / observational only. Name what they do, what they\n"
    "    choose, where they get stuck, where the same loop comes back.\n"
    "  • One concrete behaviour or observable tendency per sentence.\n"
    "  • Length: 70–130 words total — Mirror is concise.\n"
    "  • Do NOT mention any other body unless directly contextualising\n"
    "    the requested one.\n"
    "\n"
    "HARD BANS (do not use ANY of these phrasings — escalated, voice-floor-v2):\n"
    "  • 'this placement…' / 'this placement suggests…' /\n"
    "    'this placement indicates…' / 'this placement invites…' /\n"
    "    'this placement often…' / 'this placement encourages…' /\n"
    "    'this placement reflects…' / 'this placement speaks to…'\n"
    "  • 'often manifests as…' / 'often manifests through…' /\n"
    "    'can manifest as…' / 'may manifest as…' / 'tends to manifest…'\n"
    "  • 'speaks to how…' / 'speaks to the way…' / 'speaks of…' /\n"
    "    'this energy speaks…'\n"
    "  • 'themes of…' / 'the theme here is…'\n"
    "  • 'invites you to…' / 'invites a sense of…' / 'invites growth…'\n"
    "  • 'where do you notice…?' / closing reflective question of any kind\n"
    "  • Closing platitudes: 'Remember, this doesn't define you', 'this\n"
    "    is just a tool', 'take this with a grain of salt', 'trust your\n"
    "    journey', 'embrace…', 'lean into…' (as a final coachy tail)\n"
    "  • Reflective homework prompts: 'consider journaling…',\n"
    "    'sit with this…', 'a small habit to try…' (UNLESS the block\n"
    "    instruction explicitly asks for a behavioural close)\n"
    "  • Textbook astrology framings: 'the energy of {sign}…',\n"
    "    'as a {sign}/{house} placement…', 'archetypally…'\n"
    "  • Coaching tone: 'I encourage you to…', 'trust this sense…'\n"
    "  • Generic disclaimers: 'as per our agreement…', 'let's stay\n"
    "    grounded in one area at a time' — NEVER invent a prior\n"
    "    instruction; just answer.\n"
    "\n"
    "MIRROR SOUNDS LIKE WHAT HAPPENS, NOT WHAT THIS PLACEMENT MEANS."
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
            "1. Sentence 1: name the SIGN and HOUSE of their Lot of Fortune.\n"
            "   Example: 'Your Fortune sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–5 sentences of Mirror reading framed around\n"
            "   NATURAL OPENINGS — life areas that reward participation without\n"
            "   force.  Where ease finds them.  Which kinds of activity put them\n"
            "   in flow.  Speak from the sign/house combination, not generic\n"
            "   'fortune' tropes.",
            "3. End with ONE short line that describes a small concrete\n"
            "   move they could make TODAY to step into that flow.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Lot of Spirit.\n"
            "   Example: 'Your Spirit sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–5 sentences of Mirror reading framed around\n"
            "   DELIBERATE BECOMING — the direction they're consciously\n"
            "   reaching for.  Where their growth feels chosen rather than\n"
            "   imposed.  What kind of person they're quietly building.\n"
            "   Speak from the actual sign/house, not 'spiritual purpose'\n"
            "   abstractions.",
            "3. End with ONE short line naming the specific kind of\n"
            "   commitment that keeps this direction alive.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their natal Chiron.\n"
            "   Example: 'Your Chiron sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–5 sentences of Mirror reading framed around the\n"
            "   GROWTH EDGE → TEACHING GIFT arc.  Where the friction lives,\n"
            "   why it keeps showing up, and what mature expression of it\n"
            "   looks like (the way they end up able to help others in this\n"
            "   exact area).  Sign + house specific.  NO victim framing —\n"
            "   no 'deep wound' / 'old trauma' / 'unhealed' language.  This\n"
            "   is the LEARNING curriculum, not the diagnosis.",
            "3. End with ONE short line naming what the matured version of\n"
            "   this gift looks like in their actual life.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Lilith.\n"
            "   Example: 'Your Lilith sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–5 sentences of Mirror reading framed around\n"
            "   UNTAMED TRUTH + PERSONAL SOVEREIGNTY.  Which part of their\n"
            "   nature has refused to be made polite.  Where they bristle\n"
            "   when asked to perform.  Where their authentic edge shows\n"
            "   up — and what tends to happen when they pretend it isn't\n"
            "   there.  Sign + house specific.  NO fear-based framing —\n"
            "   this is not the 'shadow' as something to fix.  This is the\n"
            "   ungovernable territory of their selfhood.",
            "3. End with ONE short line about what changes when they stop\n"
            "   apologising for this part of themselves.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Juno.\n"
            "   Example: 'Your Juno sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–5 sentences of Mirror reading framed around HOW\n"
            "   THEY DO PARTNERSHIP — not who they'll meet.  What they\n"
            "   ratify when they commit.  Which part of a bond they\n"
            "   protect first.  What kind of partnership-architecture\n"
            "   feels native vs. forced.  Sign + house specific.  NEVER\n"
            "   soulmate / fated partner / one true love / marriage\n"
            "   destiny language — this is about THEIR commitment style.",
            "3. End with ONE short line about the recurring partnership\n"
            "   shape this signature tends to draw them into.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Vertex.\n"
            "   Example: 'Your Vertex sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–5 sentences of Mirror reading framed around\n"
            "   ENCOUNTER-WEIGHT.  Which life-area tends to host meetings\n"
            "   that punch above their weight.  What FLAVOUR of contact\n"
            "   the sign points to.  How they tend to recognise these\n"
            "   contacts in real time (and how they sometimes only\n"
            "   recognise them in retrospect).  Sign + house specific.\n"
            "   NEVER fated meeting / soulmate / karmic appointment\n"
            "   language — these are sensitive contact points, not\n"
            "   destiny markers.",
            "3. End with ONE short line about what shifts when they treat\n"
            "   these encounters as INFORMATION rather than as fate.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Anti-Vertex.\n"
            "   Example: 'Your Anti-Vertex sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around AGENCY.\n"
            "   The Vertex is where weighty encounters arrive.  The\n"
            "   Anti-Vertex is the complementary axis — the life-area\n"
            "   where they CHOOSE in, where their consent and entry are\n"
            "   active rather than receptive.  Sign + house specific.\n"
            "   Speak to what they walk towards on purpose, and what\n"
            "   forms of involvement they tend to actively step into.",
            "3. End with ONE short line about the trade-off when they\n"
            "   forget this axis exists.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Pholus.\n"
            "   Example: 'Your Pholus sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around\n"
            "   DISPROPORTIONATE CONSEQUENCE — life-areas where small\n"
            "   actions trigger outsized chains of effect.  Where a\n"
            "   single decision tends to set a long arc in motion.\n"
            "   Sign + house specific.",
            "3. End with ONE short line about the kind of choice they\n"
            "   should make slowly here.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Ceres.\n"
            "   Example: 'Your Ceres sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around CARE\n"
            "   SIGNATURE — how they tend to feed the people around them,\n"
            "   what kind of attention they themselves can actually metabolise\n"
            "   as 'being cared for', and the gap between the two when it\n"
            "   shows up.  Sign + house specific.  Speak to behaviours, not\n"
            "   archetypes.  No 'mother wound' / 'great mother goddess'\n"
            "   talk — this is the practical mechanics of how care moves\n"
            "   in and out of them.",
            "3. End with ONE short line naming the specific kind of care\n"
            "   they tend to give too freely (or accept too rarely).",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Pallas.\n"
            "   Example: 'Your Pallas sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around STRATEGIC\n"
            "   PATTERN-RECOGNITION — what kinds of systems they see\n"
            "   clearly (often before the people around them), which life\n"
            "   areas their problem-solving instinct is sharpest in, and\n"
            "   the SHAPE of their thinking style.  Sign + house specific.\n"
            "   No 'warrior queen' / 'sacred wisdom' archetypal language.",
            "3. End with ONE short line about the kind of problem they\n"
            "   should be allowed to lead on.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their Vesta.\n"
            "   Example: 'Your Vesta sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around\n"
            "   DEVOTED FOCUS — what they protect with quiet daily\n"
            "   attention, the part of life where they go monk-like and\n"
            "   shut everything else out, what 'sacred work' actually\n"
            "   looks like in their hands.  Sign + house specific.  No\n"
            "   'virgin priestess' / 'sacred fire goddess' archetypal\n"
            "   language and no sexuality framing.",
            "3. End with ONE short line about what tends to suffer when\n"
            "   this devotion goes unfed for too long.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their North Node.\n"
            "   Example: 'Your North Node sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around GROWTH\n"
            "   DIRECTION — the kind of behaviour that feels slightly\n"
            "   unfamiliar but is exactly the stretch their development\n"
            "   keeps pointing toward, the life-area where leaning IN tends\n"
            "   to pay off, and what 'growing into' this looks like in\n"
            "   practical terms.  Sign + house specific.  NO destiny /\n"
            "   fate / soul contract / past-life language.",
            "3. End with ONE short line about the small habit that moves\n"
            "   them in this direction.",
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
            "1. Sentence 1: name the SIGN and HOUSE of their South Node.\n"
            "   Example: 'Your South Node sits at {SIGN_PLACEMENT} in the {N}th house.'",
            "2. Then 3–4 sentences of Mirror reading framed around\n"
            "   FAMILIAR COMPETENCE — the behaviours they already do well,\n"
            "   sometimes default to under stress, and which stop\n"
            "   producing growth past a certain point.  This is not\n"
            "   wrong — it's the comfort zone that keeps pulling them\n"
            "   back from the stretch.  Sign + house specific.  NO\n"
            "   past-life karma / soul-debt language.",
            "3. End with ONE short line about what to keep using and\n"
            "   what to stop relying on.",
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


def build_mirror_object_proof_block(envelope: Dict[str, Any]) -> str:
    """Build the Mirror-native instruction block for the natal object in
    `envelope`.  Returns "" if we don't have a Mirror block for that
    object — the caller should then fall back to the generic builder
    in natal_object_engine.build_natal_object_proof_block.

    `envelope` is the dict returned by
    services.natal_object_engine.compute_natal_object.
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

    bans_str = ""
    if object_bans:
        bans_str = "OBJECT-SPECIFIC BAN LIST (do not use any of these):\n"
        bans_str += "  " + ", ".join(sorted(set(object_bans)))

    return (
        f"━━━━ NATAL OBJECT — MIRROR INTERPRETATION: {canon} ━━━━\n"
        f"Mirror question:  {question_line}\n"
        f"placement:        {formatted}\n"
        f"{house_line}\n"
        f"build:            {BUILD_MARKER}\n"
        f"sign attribution: True Sidereal-M Midpoint (same as natal chart)\n"
        "\n"
        f"INSTRUCTION TO YOU:\n{instructions}\n"
        "\n"
        f"{_UNIVERSAL_VOICE_FLOOR}\n"
        "\n"
        f"{bans_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


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
        "1. Sentence 1: name the axis in plain language — South Node sign\n"
        "   and house FIRST (the familiar competence), then North Node\n"
        "   sign and house (the stretch).\n"
        "2. Then 4–6 sentences of Mirror reading framed as ONE polarity,\n"
        "   not two separate placements.  Mirror reads the GRAVITATIONAL\n"
        "   DRAG of the SN — what behaviour they default to under stress,\n"
        "   what they over-rely on because it has always worked — and\n"
        "   then the NN as the deliberate stretch that feels slightly\n"
        "   unnatural but is exactly where development keeps pointing.\n"
        "   Speak to the CHRONIC VACATING of one for the other.\n"
        "3. Be sign-and-house specific on BOTH ends — name what the SN\n"
        "   competence actually looks like in their life, and what the\n"
        "   NN stretch actually looks like behaviourally.\n"
        "4. End with ONE short line about the small move that shifts\n"
        "   them off the SN comfort and toward the NN stretch.\n"
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
        "1. Give each body 2–3 sentences in Mirror voice. State the\n"
        "   sign + house of each on its first sentence, then describe\n"
        "   the observable behaviour or recurring pattern.  Sign + house\n"
        "   specific.  Behavioural only.\n"
        "2. After both bodies have been read, write ONE final paragraph\n"
        "   (2–3 sentences) naming the INTERSECTION — how these two\n"
        "   bodies show up TOGETHER in their life.  Name one concrete\n"
        "   place the two patterns reinforce each other and one place\n"
        "   they pull against each other.  No abstract synthesis.\n"
        "3. Do NOT refuse to read the second body, do NOT defer one\n"
        "   for later, do NOT invent a prior agreement about staying\n"
        "   on a single topic.  Both bodies were requested; both get\n"
        "   read.\n"
        "4. Total length: 140–220 words.\n"
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
