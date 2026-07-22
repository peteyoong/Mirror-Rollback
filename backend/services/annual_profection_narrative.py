"""Annual Profection Narrative — Timeline Intelligence V2 · Phase 2
==================================================================
Surface marker: annual-profection-narrative-v1

Deterministic Mirror-voice interpretation layer over the profection
engine. No LLM. No astrology jargon in visible copy. Observational tone.
Never predictive. Never fatalistic. Never claims certainty.

Every profection year is one of twelve houses. Each house has a template
answering the six Mirror V2 timing questions:

    1. What area of life is naturally asking for more attention this year?
    2. What kinds of experiences tend to emerge?
    3. What developmental question is active?
    4. What strengths become easier?
    5. What blind spots become more visible?
    6. How might this interact with the existing Identity Synthesis?

The templates are ADAPTED (not replaced) by three ruler-condition
modulators computed from the engine output:

    • ruler_house      — where the Lord of the Year LIVES in the natal
                          chart. This is where the year's attention keeps
                          "showing up" in daily life.
    • ruler_condition  — retrograde / combust / cazimi / angular /
                          aspected. Softens or amplifies emphasis.
    • ruler_absent     — Ophiuchus (no classical ruler) → narrative falls
                          back to house-only voicing.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

BUILD_MARKER = "annual-profection-narrative-v1"


# ---------------------------------------------------------------------------
# House-by-house observational templates.
# Mirror voice: soft, evidence-first, present-tense, no promises.
# ---------------------------------------------------------------------------
HOUSE_TEMPLATES: Dict[int, Dict[str, str]] = {
    1: {
        "area": "Self-image, physical presence, and how you're being met when you walk into a room.",
        "experiences": (
            "Small identity questions surface more often this year — how you look, how you sound, "
            "how you're introduced. New starts feel available even when nothing outwardly changes."
        ),
        "question": "Who am I becoming when I stop performing who I used to be?",
        "strengths": "Starting things. Being seen. Standing at the front of a room without shrinking.",
        "blind_spots": (
            "Confusing visibility with worth. Editing yourself for the room before checking whether "
            "the room deserves that edit."
        ),
    },
    2: {
        "area": "Money, self-worth, physical resources, and what you consider yours.",
        "experiences": (
            "Financial rearrangements — earnings, spending patterns, tools, possessions. Also a "
            "slower conversation with self-worth underneath the numbers."
        ),
        "question": "What am I actually willing to receive?",
        "strengths": "Steadiness with material things. Building something durable. Saying \"enough\".",
        "blind_spots": (
            "Tying self-worth to income figures. Confusing scarcity with prudence, or generosity "
            "with self-erasure."
        ),
    },
    3: {
        "area": "Everyday communication, learning, siblings, short journeys, the immediate environment.",
        "experiences": (
            "More messages, more logistics, more short trips. Learning something new or revisiting "
            "something you thought you'd finished with."
        ),
        "question": "What am I ready to say out loud that I've only been thinking?",
        "strengths": "Language. Curiosity. Making connections between things that seem unrelated.",
        "blind_spots": (
            "Talking around a decision instead of making it. Mistaking activity for progress."
        ),
    },
    4: {
        "area": "Home, family, ancestry, emotional foundations, and where you feel rooted.",
        "experiences": (
            "Home life becomes louder — a move, a renovation, a family conversation you've been "
            "putting off, or a quiet reordering of what \"belonging\" means to you now."
        ),
        "question": "What do I need to feel truly at home in myself?",
        "strengths": "Rootedness. Making a space safe. Holding history without being ruled by it.",
        "blind_spots": (
            "Retreating so far inward that the outside starts to atrophy. Confusing familiar "
            "with true."
        ),
    },
    5: {
        "area": "Creativity, play, romance, children, and the things you make purely because you want to.",
        "experiences": (
            "Creative projects start or resume. Attraction becomes more legible — to people, to "
            "ideas, to work that has your fingerprints on it."
        ),
        "question": "What am I making just because it's mine to make?",
        "strengths": "Play. Delight. The kind of confidence that doesn't need permission.",
        "blind_spots": (
            "Chasing applause instead of the making. Treating fun as a reward you have to earn."
        ),
    },
    6: {
        "area": "Daily routine, health, work-you-actually-do, service, and small repeated maintenance.",
        "experiences": (
            "The ordinary day gets more attention — sleep, diet, habits, the shape of the week. "
            "Work of the hands-on-tools variety, not just the strategy variety."
        ),
        "question": "What am I willing to do quietly, every day, whether or not anyone notices?",
        "strengths": "Follow-through. Care of the body. Getting the boring things reliably done.",
        "blind_spots": (
            "Confusing being busy with being useful. Ignoring the body until it forces a "
            "conversation."
        ),
    },
    7: {
        "area": "One-to-one relationships, partnerships, contracts, and the mirror other people hold up.",
        "experiences": (
            "A relationship comes into sharper focus — a new one, an existing one, or a decisive "
            "conversation about the terms of one. Contracts and commitments become more real."
        ),
        "question": "Who am I when I stop being the one holding the whole thing up alone?",
        "strengths": "Meeting people where they are. Diplomacy. Reading a room without losing yourself.",
        "blind_spots": (
            "Losing the plot inside someone else's needs. Editing yourself to keep the peace."
        ),
    },
    8: {
        "area": "Shared resources, intimacy, inheritance, endings, and what changes hands.",
        "experiences": (
            "Money that belongs to more than one person. Joint decisions. Something ending, "
            "something being metabolised. Deep conversations that don't fit a coffee-catch-up."
        ),
        "question": "What am I ready to release so something else can move?",
        "strengths": "Depth. Honesty in hard conversations. Sitting with intensity without flinching.",
        "blind_spots": (
            "Confusing secrecy with intimacy. Holding onto grievances because they're familiar."
        ),
    },
    9: {
        "area": "Meaning, worldview, teachers, long journeys, publishing, and what you believe.",
        "experiences": (
            "Bigger-picture questions come back. Study, travel, a mentor, a system of thought — "
            "something is expanding the frame you use to make sense of your life."
        ),
        "question": "What am I willing to believe now that I couldn't have believed before?",
        "strengths": "Perspective. Teaching. Zooming out without losing warmth.",
        "blind_spots": (
            "Prescribing your framework to people who didn't ask. Confusing certainty with truth."
        ),
    },
    10: {
        "area": "Public role, career, reputation, and the version of you that's visible from far away.",
        "experiences": (
            "The outer story gets louder — recognition, responsibility, a shift in what you're "
            "known for. External milestones tend to cluster."
        ),
        "question": "What am I actually building, and who am I building it for?",
        "strengths": "Leadership. Being trusted with weight. Showing up to be counted.",
        "blind_spots": (
            "Optimising for the résumé instead of the life. Mistaking title for meaning."
        ),
    },
    11: {
        "area": "Friendships, communities, longer-range hopes, and the networks you belong to.",
        "experiences": (
            "The people around you shift — old friendships deepen or thin out, new communities "
            "form, and the longer-range hopes get more specific."
        ),
        "question": "Which room am I actually trying to be in?",
        "strengths": "Weaving people together. Long-horizon thinking. Generosity that scales.",
        "blind_spots": (
            "Loyalty to rooms you've outgrown. Confusing being liked with being known."
        ),
    },
    12: {
        "area": "The interior life, rest, unconscious material, retreat, and what happens off-stage.",
        "experiences": (
            "Something wants to be composted this year — an old story, an old identity, an old "
            "pattern. Rest, solitude, and interior work quietly matter more than the outer to-do list."
        ),
        "question": "What am I finally ready to lay down?",
        "strengths": "Reflection. Compassion. The kind of listening that doesn't need to fix.",
        "blind_spots": (
            "Isolating and calling it healing. Confusing exhaustion with a spiritual awakening."
        ),
    },
}


# ---------------------------------------------------------------------------
# Ruler-condition modulators — soften/amplify without contradicting.
# All wording is observational, not prescriptive.
# ---------------------------------------------------------------------------
def _condition_note(cond: Dict[str, Any]) -> Optional[str]:
    if not cond: return None
    if cond.get("cazimi"):
        return ("The Lord of the Year sits close to the Sun — this year's theme tends to become "
                "personal and highly visible; whatever moves, moves in the open.")
    if cond.get("combust"):
        return ("The Lord of the Year is close to the Sun and easily overshadowed — the theme is "
                "loud, but it's easy for your own light to obscure it. Attention drifts toward "
                "identity performance rather than the underlying signal.")
    if cond.get("under_beams"):
        return ("The Lord of the Year is near the Sun — the theme is present but half-lit; it "
                "may take longer to see it clearly, and clarity often arrives via other people.")
    if cond.get("retrograde"):
        return ("The Lord of the Year is retrograde in the natal chart — the theme tends to move "
                "by return, not by first pass. Old material comes back for another look, and "
                "outward motion feels less useful than review.")
    if cond.get("angularity") == "angular":
        return ("The Lord of the Year sits on an angle of the natal chart — this year's theme "
                "shows up in visible, first-order ways rather than behind the scenes.")
    if cond.get("angularity") == "cadent":
        return ("The Lord of the Year sits in a cadent house — this year's theme tends to move "
                "in the background, through preparation and re-arrangement rather than fanfare.")
    return None


def _ruler_house_note(cond: Dict[str, Any]) -> Optional[str]:
    """A one-line hint about WHERE the year keeps 'showing up' — the natal
    house of the ruler is the persistent daily surface for the theme."""
    h = cond.get("house") if cond else None
    if not h: return None
    map_ = {
        1:  "shows up in how you present yourself and what you begin",
        2:  "shows up in money, self-worth, and what you decide is yours",
        3:  "shows up in conversations, learning, and short journeys",
        4:  "shows up at home, in family, and in your inner sense of ground",
        5:  "shows up in creative output, play, and matters of the heart",
        6:  "shows up in daily habits, work, and the body's signals",
        7:  "shows up in one-to-one relationships and negotiated terms",
        8:  "shows up in shared resources, intimacy, and what changes hands",
        9:  "shows up in meaning-making, study, and the wider frame",
        10: "shows up in public role, reputation, and what you're building",
        11: "shows up in friendships, communities, and longer-range hopes",
        12: "shows up in interior life, rest, and what happens off-stage",
    }
    return f"In this chart the year's theme {map_.get(h, 'shows up in a specific area of daily life')}."


# ---------------------------------------------------------------------------
# Public: build narrative payload from a ProfectionYear dataclass
# ---------------------------------------------------------------------------
def build_narrative(prof: Any) -> Dict[str, Any]:
    """Return the six Mirror-V2 timing answers for a ProfectionYear.

    `prof` is a `services.annual_profection_engine.ProfectionYear`. We
    accept it structurally so this module has no import-time dependency
    on the engine (useful for tests + future reshuffling)."""
    tpl = HOUSE_TEMPLATES.get(int(prof.activated_house)) or {}
    cond = prof.ruler_natal_condition or {}
    ruler = prof.lord_of_the_year

    condition_note = _condition_note(cond)
    house_note     = _ruler_house_note(cond)

    # Compose 'strengths_easier_this_year' with the condition note when
    # helpful. Keep visible copy identity-safe and jargon-free.
    strengths = tpl.get("strengths", "")
    blind     = tpl.get("blind_spots", "")

    # Identity Synthesis interaction — a bridge line describing how the
    # year interacts with the person's existing profile. Deterministic
    # observational bridge, non-fatalistic.
    if ruler:
        identity_bridge = (
            f"This year's attention rests on {prof.profected_sign} and moves through "
            f"the natal placements of {ruler}. Wherever {ruler} already sits in your "
            f"Identity Synthesis, that signature is doing more of the talking this year — "
            f"not because the identity has changed, but because the timing has spotlighted "
            f"the part of you already carrying it."
        )
    else:
        identity_bridge = (
            f"This year's attention rests on {prof.profected_sign}. Because {prof.profected_sign} "
            f"has no classical ruling planet in the 13-sign frame, the year is read from the "
            f"house alone — treat it as an atmosphere rather than a single spotlight."
        )

    return {
        "engine_marker":                       BUILD_MARKER,
        "what_area_is_asking_attention":       tpl.get("area", ""),
        "experiences_that_tend_to_emerge":     tpl.get("experiences", ""),
        "active_developmental_question":       tpl.get("question", ""),
        "strengths_easier_this_year":          strengths,
        "blind_spots_more_visible":            blind,
        "identity_synthesis_interaction":      identity_bridge,
        "ruler_condition_note":                condition_note,
        "ruler_house_signal":                  house_note,
        "tone_contract": {
            "observational_not_predictive": True,
            "no_fatalism":                  True,
            "no_certainty_claim":           True,
            "identity_first":               True,
        },
    }


__all__ = ["BUILD_MARKER", "HOUSE_TEMPLATES", "build_narrative"]
