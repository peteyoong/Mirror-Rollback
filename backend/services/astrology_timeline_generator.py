"""
Astrology Timeline Generator (Python port of frontend AstrologyTimelineTab)
============================================================================

Produces the SAME structured timeline payload that the client-side
AstrologyTimelineTab renders, but generated server-side from the user's
stored natal chart so it can be cached under `astro_timeline::{user_id}`
and consumed by the Life Interpreter ("Ask About My Life").

This is a 1:1 port of /app/frontend/components/astrology/AstrologyTimelineTab.tsx
`generateTimelineData()` so backend and frontend stay aligned.

No LLM. No astrology recompute. Pure deterministic pattern derived from
the natal Sun sign + key house placements. Astrology jargon is kept
inside this module — the output text is in user-experience language.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# House → life area maps (mirror of frontend HOUSE_AREAS / HOUSE_SHORT)
# ---------------------------------------------------------------------------

HOUSE_AREAS: Dict[int, str] = {
    1: "identity and how you show up",
    2: "money, security, and self-worth",
    3: "communication, decisions, and daily routines",
    4: "home, family, and emotional foundation",
    5: "creativity, joy, and what you pour yourself into",
    6: "work, health, and daily habits",
    7: "relationships and partnerships",
    8: "intimacy, shared resources, and transformation",
    9: "beliefs, meaning, and long-term direction",
    10: "career, reputation, and public life",
    11: "community, future vision, and friendships",
    12: "rest, solitude, and what you hide from yourself",
}

HOUSE_SHORT: Dict[int, str] = {
    1: "identity",
    2: "security",
    3: "communication",
    4: "home",
    5: "creativity",
    6: "work",
    7: "relationships",
    8: "intimacy",
    9: "direction",
    10: "career",
    11: "community",
    12: "inner life",
}

# ---------------------------------------------------------------------------
# Sign-pattern table (mirror of frontend SIGN_PATTERNS — verbatim copy)
# ---------------------------------------------------------------------------

SIGN_PATTERNS: Dict[str, Dict[str, str]] = {
    "Aries": {
        "tension":         "moving fast vs. moving right",
        "year_theme":      "This year keeps asking whether speed is actually getting you closer—or just keeping you from feeling stuck.",
        "arc_description": "You'll notice the same friction between action and timing appearing in different contexts. The impulse to move shows up first; the question of whether it's time comes second. The year is teaching you that readiness isn't the same as restlessness.",
        "cost_of_action":  "the conversation gets uncomfortable fast, but the uncertainty stops running the show",
        "cost_of_waiting": "you preserve momentum for now, but the question you're avoiding gets louder",
    },
    "Taurus": {
        "tension":         "holding on vs. letting go",
        "year_theme":      "This year keeps showing you the difference between stability and stagnation—and which one you've been calling the other.",
        "arc_description": "Across the year, you'll feel the weight of things you've been carrying longer than necessary. The pattern isn't about loss—it's about recognizing when holding on has become the obstacle, not the anchor.",
        "cost_of_action":  "the discomfort of releasing something familiar, but the relief of finally moving",
        "cost_of_waiting": "the comfort of keeping things as they are, but the growing sense that comfort isn't the same as peace",
    },
    "Gemini": {
        "tension":         "exploring options vs. choosing a path",
        "year_theme":      "This year keeps narrowing your options until you discover which one you actually want—not which one sounds interesting.",
        "arc_description": "You'll notice the same tension between curiosity and commitment returning in different forms. The year isn't trying to limit you. It's showing you that depth requires staying somewhere long enough to see what's really there.",
        "cost_of_action":  "closing doors feels limiting, but the focus brings clarity you couldn't find while juggling",
        "cost_of_waiting": "options remain open, but the energy stays scattered and nothing quite lands",
    },
    "Cancer": {
        "tension":         "protecting vs. connecting",
        "year_theme":      "This year keeps asking whether your walls are keeping you safe—or keeping out what you actually need.",
        "arc_description": "Across the year, you'll notice the same pattern: the instinct to protect, followed by the cost of isolation. The year is teaching you that vulnerability isn't the opposite of safety—sometimes it's the only path to it.",
        "cost_of_action":  "the exposure feels raw, but the connection becomes real instead of guarded",
        "cost_of_waiting": "the distance feels safer, but the loneliness underneath keeps growing",
    },
    "Leo": {
        "tension":         "being seen vs. being known",
        "year_theme":      "This year keeps showing you the difference between the version of you that performs and the version that's actually real.",
        "arc_description": "You'll feel the gap between how you present and how you feel appearing in different contexts. The year isn't asking you to stop shining. It's asking whether the light is coming from somewhere authentic.",
        "cost_of_action":  "the mask drops, and not everyone will recognize you—but the right ones will",
        "cost_of_waiting": "the performance continues smoothly, but the exhaustion of maintaining it grows",
    },
    "Virgo": {
        "tension":         "fixing vs. accepting",
        "year_theme":      "This year keeps asking whether the problem is actually the thing you're trying to fix—or the fact that you can't stop fixing.",
        "arc_description": "Across the year, you'll notice the same impulse: something isn't right, and you're the one who sees it. The pattern isn't about lowering your standards. It's about recognizing when improvement has become avoidance.",
        "cost_of_action":  "you let something be imperfect, and it doesn't collapse—the anxiety was the problem",
        "cost_of_waiting": "you keep refining, but the thing you're avoiding keeps waiting underneath the tasks",
    },
    "Libra": {
        "tension":         "pleasing vs. choosing",
        "year_theme":      "This year keeps putting you in positions where harmony requires honesty—and you can't have both by staying silent.",
        "arc_description": "You'll feel the same tension between keeping the peace and stating your position appearing in different relationships. The year isn't asking you to become disagreeable. It's showing you that real connection requires knowing where you actually stand.",
        "cost_of_action":  "the conversation gets tense, but they finally know who they're dealing with",
        "cost_of_waiting": "the relationship stays smooth on the surface, but you start disappearing from it",
    },
    "Scorpio": {
        "tension":         "controlling vs. trusting",
        "year_theme":      "This year keeps asking you to loosen your grip—and discover what stays when you stop holding so tightly.",
        "arc_description": "Across the year, you'll notice the same pattern: the impulse to control outcomes, followed by the cost of never knowing what would have happened naturally. The year is teaching you that trust isn't weakness—it's a different kind of power.",
        "cost_of_action":  "you let go, and it's terrifying—but you finally see what's real without your influence",
        "cost_of_waiting": "you maintain control, but you never know if what you have would have chosen you back",
    },
    "Sagittarius": {
        "tension":         "freedom vs. commitment",
        "year_theme":      "This year keeps showing you that some kinds of freedom are actually just avoidance wearing adventure as a costume.",
        "arc_description": "You'll feel the pull between staying and going appearing in different contexts. The year isn't trying to cage you. It's asking whether the next horizon is actually calling—or just easier than being fully present here.",
        "cost_of_action":  "you commit, and some doors close—but you finally find out what's behind the one you chose",
        "cost_of_waiting": "all options stay open, but you start noticing how shallow everything feels",
    },
    "Capricorn": {
        "tension":         "achieving vs. arriving",
        "year_theme":      "This year keeps asking whether you're climbing toward something real—or just avoiding the emptiness that might be at the top.",
        "arc_description": "Across the year, you'll notice the same pattern: the drive to accomplish, followed by the question of what it's actually for. The year isn't asking you to stop working. It's asking whether the work is building something that matters to you.",
        "cost_of_action":  "you pause the climb, and the identity question hits—but so does clarity about what's worth reaching",
        "cost_of_waiting": "you keep achieving, but the satisfaction keeps requiring the next achievement to feel real",
    },
    "Aquarius": {
        "tension":         "distance vs. belonging",
        "year_theme":      "This year keeps asking whether your independence is freedom—or just a sophisticated way of staying alone.",
        "arc_description": "You'll feel the tension between standing apart and being part of something appearing in different contexts. The year isn't asking you to conform. It's asking whether the distance is protecting something valuable—or just preventing connection.",
        "cost_of_action":  "you move closer, and it feels vulnerable—but you finally know what belonging actually feels like",
        "cost_of_waiting": "you maintain your position, but the loneliness you've been calling freedom gets harder to ignore",
    },
    "Pisces": {
        "tension":         "absorbing vs. protecting",
        "year_theme":      "This year keeps showing you the difference between compassion and losing yourself—and how often you've confused them.",
        "arc_description": "Across the year, you'll notice the same pattern: feeling everything around you, followed by the cost of not knowing which feelings are actually yours. The year is teaching you that boundaries aren't walls—they're the shape of who you are.",
        "cost_of_action":  "you draw a line, and it feels selfish—but you finally have energy that belongs to you",
        "cost_of_waiting": "you keep absorbing, but you start forgetting what you wanted before you felt what everyone else needed",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _planet_house(planets: Dict[str, Any], name: str, default: int) -> int:
    """Pull the natal house number for a planet, defaulting safely."""
    try:
        h = (planets.get(name) or {}).get("house")
        h = int(h)
        if 1 <= h <= 12:
            return h
    except (TypeError, ValueError):
        pass
    return default


def _planet_sign(planets: Dict[str, Any], name: str, default: str) -> str:
    s = (planets.get(name) or {}).get("sign")
    if isinstance(s, str) and s in SIGN_PATTERNS:
        return s
    return default


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_astrology_timeline(
    chart_doc: Optional[Dict[str, Any]],
    *,
    current_year: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build the structured astrology timeline payload from a stored natal
    chart (the document at db.charts['user_id']).

    Returns a dict shaped to be consumed by
    `astrology_timeline_interpreter.build_timeline_context` — i.e. it has
    the keys ATI knows how to parse:
        year_question / year_theme, arc, phases[], turning_points[],
        domain_relevance hints (implicit, derived from house language).

    Returns None when chart data is incomplete enough that a meaningful
    timeline cannot be produced.
    """
    if not isinstance(chart_doc, dict):
        return None

    astro = chart_doc.get("astrology") or chart_doc.get("natal") or {}
    planets = astro.get("planets") or {}
    if not planets:
        return None

    sun_sign = _planet_sign(planets, "Sun", "Aries")
    sun_house = _planet_house(planets, "Sun", 5)
    moon_house = _planet_house(planets, "Moon", 4)
    mars_house = _planet_house(planets, "Mars", 1)
    venus_house = _planet_house(planets, "Venus", 7)
    saturn_house = _planet_house(planets, "Saturn", 10)

    pattern = SIGN_PATTERNS.get(sun_sign) or SIGN_PATTERNS["Aries"]

    sun_area = HOUSE_AREAS.get(sun_house, "self-expression")
    moon_area = HOUSE_AREAS.get(moon_house, "emotional life")
    mars_area = HOUSE_SHORT.get(mars_house, "action")
    venus_area = HOUSE_SHORT.get(venus_house, "relationships")
    saturn_area = HOUSE_SHORT.get(saturn_house, "responsibility")

    year = current_year or datetime.utcnow().year

    year_theme = pattern["year_theme"]
    arc = pattern["arc_description"]
    tension = pattern["tension"]

    # ---- Phases (4 quarters) -------------------------------------------------
    phases: List[Dict[str, Any]] = [
        {
            "id":             "q1",
            "name":           "Recognition",
            "period":         f"Jan – Mar {year}",
            "human_meaning":  "Something is becoming clear",
            "description": (
                f"The {tension} tension starts showing up in {sun_area}. "
                f"Small moments in {mars_area} and {venus_area} carry more weight than they look. "
                f"What this creates: a nagging sense you've been here before — situations that "
                f"feel minor but keep replaying. What is asked of you: notice what keeps echoing, "
                f"especially around {moon_area}."
            ),
            "is_primary":      False,
        },
        {
            "id":             "q2",
            "name":           "Confrontation",
            "period":         f"Apr – Jun {year}",
            "human_meaning":  "Something can no longer be avoided",
            "description": (
                f"What you've been tolerating in {venus_area} and {saturn_area} stops feeling tolerable. "
                f"The gap between how you present in {sun_area} and how you feel in {moon_area} gets harder "
                f"to bridge. Conversations you've been putting off start demanding attention. "
                f"What is asked of you: name what you've been pretending not to see; in {saturn_area}, "
                f"choose from clarity — not from wanting the discomfort to end."
            ),
            "is_primary":      True,
        },
        {
            "id":             "q3",
            "name":           "Crossroads",
            "period":         f"Jul – Sep {year}",
            "human_meaning":  "A choice, split, or redirection is active",
            "description": (
                f"In {sun_area}, two versions of you become visible — the one you've been and the one "
                f"you could become. The tension in {venus_area} crystallizes into a clear choice. "
                f"Where people get this wrong: waiting for certainty that never comes — the information "
                f"is already sufficient. What is asked of you: make the choice you've been circling. "
                f"The year has prepared you for this."
            ),
            "is_primary":      True,
        },
        {
            "id":             "q4",
            "name":           "Integration",
            "period":         f"Oct – Dec {year}",
            "human_meaning":  "Something is settling into a new form",
            "description": (
                f"The ripples from your Q3 choices start showing in {saturn_area} and {mars_area}. "
                f"What you decided in {venus_area} either settles or requires one more honest "
                f"conversation. Either: the relief of having finally moved, and the new ground "
                f"beneath your feet. Or: the recognition that you're not done yet — and clarity "
                f"about what next year needs to address."
            ),
            "is_primary":      False,
        },
    ]

    # ---- Turning points ------------------------------------------------------
    turning_points: List[Dict[str, Any]] = [
        {
            "timing":   f"Late April {year}",
            "type":     "confrontation",
            "life_area": HOUSE_AREAS.get(moon_house, "emotional life"),
            "what_activates": (
                f"Something happens in {moon_area} that makes the {tension} tension impossible to "
                f"keep calling 'manageable'. The cost of continuing as you have been becomes clearer "
                f"than the cost of changing."
            ),
            "what_becomes_clear": (
                f"What you've been tolerating. Why you've been tolerating it. And what it's actually "
                f"been costing you in {venus_area}."
            ),
            "if_avoided": (
                "The pattern doesn't go away — it goes underground. What could have been addressed as "
                "a conversation becomes a crisis by August."
            ),
        },
        {
            "timing":   f"Mid-August {year}",
            "type":     "decision",
            "life_area": HOUSE_AREAS.get(sun_house, "identity"),
            "what_activates": (
                f"This is the year's primary choice point in {sun_area}. The options are clear. The "
                f"information is sufficient. What remains is whether you'll choose from who you're "
                f"becoming — or retreat to who you've been."
            ),
            "what_becomes_clear": (
                "Which direction matches the person you've been growing into. The version of you that "
                "hesitates and the version that moves forward both become visible."
            ),
            "if_avoided": (
                f"The choice gets made for you by circumstances. In {saturn_area}, you lose authorship "
                f"of your own direction."
            ),
        },
        {
            "timing":   f"Early November {year}",
            "type":     "integration",
            "life_area": HOUSE_AREAS.get(saturn_house, "responsibility"),
            "what_activates": (
                f"The year's arc reaches its natural conclusion in {saturn_area}. What you started in "
                f"Q1 is ready to be named: either as something that changed, or as something that "
                f"needs another cycle."
            ),
            "what_becomes_clear": (
                "Whether the year's lesson landed. Whether you're entering next year with new ground "
                "beneath you — or carrying forward what this year tried to resolve."
            ),
            "if_avoided": (
                "You enter next year still holding what this year asked you to put down. The same "
                "pattern returns, but with higher stakes."
            ),
        },
    ]

    # ---- Decision windows ----------------------------------------------------
    decision_windows: List[Dict[str, Any]] = [
        {
            "period":   f"Mar 15-31 {year}",
            "context":  f"In {HOUSE_SHORT.get(mars_house, 'action')}",
            "prompt":   "You can name it now. Or you can wait until it names itself.",
            "if_act":   (
                "The conversation gets uncomfortable fast, but the uncertainty stops running the show. "
                "In two weeks, you'll be glad you didn't wait."
            ),
            "if_wait":  (
                "You preserve the surface peace for now, but the thing you're avoiding keeps growing "
                "underneath it. By May, it's bigger."
            ),
        },
        {
            "period":   f"Jun 1-15 {year}",
            "context":  f"In {HOUSE_SHORT.get(venus_house, 'relationships')}",
            "prompt":   "You can say what's actually true. Or you can keep editing yourself for the room.",
            "if_act":   pattern["cost_of_action"]
            + ". The relationship changes — but at least now it's based on something real.",
            "if_wait":  pattern["cost_of_waiting"]
            + ". The connection stays familiar, but you start noticing how tired you are of managing it.",
        },
        {
            "period":   f"Sep 1-20 {year}",
            "context":  f"In {HOUSE_SHORT.get(saturn_house, 'career')}",
            "prompt":   "You can commit to the new direction. Or you can keep one foot in both worlds.",
            "if_act":   "Some doors close. The grief is real. But so is the focus — and the energy that comes from finally choosing.",
            "if_wait":  "All options stay open, but your energy stays scattered. By November, you'll wish you'd trusted yourself sooner.",
        },
    ]

    payload = {
        # Top-level — interpreter will pick up year_theme directly.
        "year_theme":      year_theme,
        "year_question":   year_theme,  # alias accepted by ATI
        "arc":             arc,
        "tension":         tension,
        "phases":          phases,
        "turning_points":  turning_points,
        "decision_windows": decision_windows,
        # Optional: explicit dominant life-area hints so ATI's domain
        # relevance scan is grounded by the chart's actual house layout.
        "house_hints": {
            "sun_area":     sun_area,
            "moon_area":    moon_area,
            "mars_area":    mars_area,
            "venus_area":   venus_area,
            "saturn_area":  saturn_area,
        },
        "year":             year,
        "source":           "real_astrology_timeline",
        "generator_version": "astrology_timeline_v1_python",
    }
    logger.debug(
        "[AstrologyTimelineGenerator] sun=%s sun_house=%d moon_house=%d "
        "venus_house=%d saturn_house=%d -> %d phases / %d turning points",
        sun_sign, sun_house, moon_house, venus_house, saturn_house,
        len(phases), len(turning_points),
    )
    return payload


__all__ = ["generate_astrology_timeline", "SIGN_PATTERNS", "HOUSE_AREAS", "HOUSE_SHORT"]
