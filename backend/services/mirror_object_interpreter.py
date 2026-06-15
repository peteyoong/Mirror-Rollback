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
    "  • Speak in 2nd person, present tense, conversational.\n"
    "  • Lead with WHERE this energy SHOWS UP in their life — not what the\n"
    "    body 'represents' or 'symbolises'.\n"
    "  • Behavioural / observational — what they do, not what they 'are'.\n"
    "  • No 'this placement suggests…', no 'themes of…', no 'this can\n"
    "    manifest as…', no 'where do you notice…?', no closing reflective\n"
    "    question, no fortune-cookie generalities.\n"
    "  • One concrete behaviour or pattern per sentence.\n"
    "  • Length: 70–130 words total — Mirror is concise.\n"
    "  • Do NOT mention any other body unless directly contextualising the\n"
    "    requested one."
)


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
    degree = placement.get("degree")
    formatted = placement.get("formatted") or (
        f"{int(degree) if isinstance(degree, (int, float)) else '?'}°{sign}"
    )
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
