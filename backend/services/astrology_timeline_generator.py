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
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Engine version — bump when the structural timeline contract changes.
# Timeline caches are keyed by (user_id, year, engine_version,
# birth_data_hash); a bump automatically invalidates all cached timelines.
#
# v1.1: payload now emits the rich per-phase bullet arrays
#       (whats_happening, what_this_creates, where_people_get_it_wrong,
#       what_its_asking_of_you) + per-phase is_current flag so the
#       Astrology Timeline tab can render entirely from the server
#       payload without a client-side fallback generator.
#
# v1.2: REMOVED the fixed Q1/Q2/Q3/Q4 calendar-quarter scaffold and
#       hard-coded phase names (Recognition / Confrontation /
#       Crossroads / Integration). Phases are now:
#         • 3–4 in count (variable)
#         • dynamically NAMED per user (derived from natal house
#           emphasis × phase role × Sun-sign tension)
#         • anchored to forward-looking timing windows starting from
#           the generation date — NOT calendar quarters
#         • each carries is_current / is_past / is_upcoming
#       Turning points and decision windows are likewise re-anchored
#       relative to "now" (not fixed April / August / November).
#
# v1.3: PRESSURE WINDOW REFRAMING (Timeline V2 Phase 1 — copy-layer
#       only; computation unchanged). Visible phase titles changed
#       from categorical / house-topic language ("What's surfacing
#       in communication") to existential / consequence / threshold
#       language ("Where You Stop Managing Quietly"). The old
#       categorical title is preserved on each phase as
#       `categorical_label` for use inside the proof drawer ONLY —
#       it must never appear in user-visible primary copy.
# v1.4: DESCRIPTION + BULLET REWRITE pass (Timeline V2 Phase 1
#       continued). All {house_area} / {*_area} interpolations
#       removed from visible-tier copy:
#         - each phase's description rewritten existentially
#         - each phase's whats_happening / what_this_creates /
#           where_people_get_it_wrong / what_its_asking_of_you
#           bullet arrays rewritten without categorical interpolation
#         - turning points (confrontation / decision / integration)
#           rewritten without house labels in user-visible text
#         - decision-window `context` is now an existential label
#           ("Naming", "Truth-telling in close range", etc.) instead
#           of "In {house}".
#       Categorical labels are preserved on each phase / turning
#       point / decision window under `categorical_context` for
#       future proof-drawer surfacing.
ENGINE_VERSION = "timeline_v1.4"



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
    # ophiuchus-first-class-content-v1: 13-sign canonical entry.
    # Voice — integration under pressure / contact with complexity / repair
    # at the threshold between Scorpio depth and Sagittarius meaning.
    "Ophiuchus": {
        "tension":         "going through it vs. going around it",
        "year_theme":      "This year keeps putting you at thresholds you've avoided crossing—places where the depth of what you've felt has to translate into something you actually do with it.",
        "arc_description": "Across the year, you'll notice the same pattern: a hard thing surfaces, you sit inside it longer than most people would, and then it asks to be metabolised — not just understood. The year isn't asking you to perform recovery. It's asking what changes when you stop circling the wound and start walking through it.",
        "cost_of_action":  "the integration is exhausting and slow—but the pattern you've been carrying actually shifts",
        "cost_of_waiting": "you stay with the depth, but the depth alone isn't doing the work anymore",
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
    # ophiuchus-first-class-content-v1: preserve Ophiuchus as a canonical
    # sign even though Variant B legacy callers may still pass it through
    # without an entry in their own table. The TIMELINE module's
    # SIGN_PATTERNS now has an "Ophiuchus" key, so we accept it.
    s = (planets.get(name) or {}).get("sign")
    if isinstance(s, str) and s in SIGN_PATTERNS:
        return s
    # Even if the local pattern table somehow lacks Ophiuchus, never
    # silently relabel an actual Ophiuchus placement back to Aries.
    if isinstance(s, str) and s == "Ophiuchus":
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

    # =====================================================================
    # v1.2 — DYNAMIC PHASES (not calendar quarters)
    # =====================================================================
    # Phases are generated NOW-FORWARD from the generation timestamp, with
    # variable date windows (not fixed Q1/Q2/Q3/Q4 buckets) and dynamic
    # names derived from:
    #   • the phase's structural role (active pressure / surfacing /
    #     pivot / settling)
    #   • the user's natal house emphasis (which life-area the role
    #     activates)
    #   • the Sun-sign tension that runs through the whole year
    # Each phase carries:
    #   • description    — single-paragraph summary (ATI / LLM)
    #   • whats_happening / what_this_creates /
    #     where_people_get_it_wrong / what_its_asking_of_you
    #   • is_current / is_past / is_upcoming flags
    # ---------------------------------------------------------------------

    gen_dt = datetime.utcnow()

    def _date_range_label(start: datetime, end: datetime) -> str:
        """'May 13 – Jun 27, 2026' or 'May 13 – Jun 27' when same year."""
        same_year = start.year == end.year
        if same_year:
            return f"{start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
        return (
            f"{start.strftime('%b %-d, %Y')} – {end.strftime('%b %-d, %Y')}"
        )

    # Phase role templates — define structural arc that flows from
    # "right now" forward. Each template carries phase NAMES that
    # interpolate the user's natal house life-areas so each user gets
    # different titles. Names deliberately AVOID the old fixed labels
    # (Recognition / Confrontation / Crossroads / Integration).
    # v1.3 PHASE 2 COPY PASS: descriptions + bullet arrays rewritten
    # from categorical / {house_area} interpolations to existential /
    # consequence-framed language. The {tension} interpolation is
    # retained because it describes the charge/dynamic (e.g. "absorbing
    # vs naming"), not a topic. {*_area} interpolations are fully
    # removed from visible-tier copy and preserved internally on each
    # phase as `categorical_context` for the proof drawer.

    phase_role_templates: List[Dict[str, Any]] = [
        {
            "role":          "active_pressure",
            "offset_days":   (-21, 35),   # past 3w → next 5w
            "human_meaning": "Where pressure becomes recognition",
            "name_template": "Where You Stop Managing Quietly",
            "categorical_label":
                f"What's surfacing in {HOUSE_SHORT.get(sun_house, 'identity')}",
            "categorical_context": (
                f"Underlying activation: {sun_area} (Sun), "
                f"{mars_area} (Mars), {moon_area} (Moon)."
            ),
            "is_primary":    False,
            "whats_happening": [
                f"The {tension} tension you've been quietly managing is "
                "moving from background to foreground",
                "Small moments are carrying more weight than they look — "
                "the system has stopped being able to neutralise them",
            ],
            "what_this_creates": [
                "A sense that something you've been steering around is "
                "starting to ask for your attention",
                "Situations that feel like a repeat — but with the stakes "
                "noticeably higher",
            ],
            "where_people_get_it_wrong": [
                "Treating it as background noise instead of signal",
                "Trying to push through without naming what's actually "
                "happening",
            ],
            "what_its_asking_of_you": [
                "Notice what keeps echoing — the same edge in slightly "
                "different shapes",
                "Stop calling it 'just busy' — name what you're actually "
                "navigating",
            ],
            "description": (
                f"The {tension} tension is moving from something you've "
                "been quietly managing to something that's asking for "
                "your attention. The version of this you've been carrying "
                "for a while is no longer paying its own way."
            ),
        },
        {
            "role":          "surfacing",
            "offset_days":   (35, 105),   # next 5w → 15w
            "human_meaning": "When delay starts costing more than naming",
            "name_template": "When Delay Starts Costing More Than Clarity",
            "categorical_label":
                f"The pressure point in {HOUSE_SHORT.get(saturn_house, 'career')}",
            "categorical_context": (
                f"Underlying activation: {saturn_area} (Saturn), "
                f"{venus_area} (Venus)."
            ),
            "is_primary":    True,
            "whats_happening": [
                "What you've been tolerating stops feeling tolerable — "
                "not dramatically, just consistently",
                "The gap between how you've been presenting and how you "
                "actually feel gets harder to bridge",
            ],
            "what_this_creates": [
                "Conversations you've been putting off start demanding "
                "attention",
                "Choices that feel more permanent than the ones before",
            ],
            "where_people_get_it_wrong": [
                "Blaming the situation instead of seeing what you brought "
                "to it",
                "Making a decision just to escape the pressure, then "
                "regretting the speed",
            ],
            "what_its_asking_of_you": [
                "Name what you've been pretending not to see",
                "Choose from clarity — not from wanting the discomfort "
                "to end",
            ],
            "description": (
                "This is the part of the year where avoiding clarity "
                "starts taking more energy than facing it. What was "
                "manageable on the surface is no longer manageable "
                "underneath. The cost of staying quiet about it has "
                "quietly crossed the cost of saying it out loud."
            ),
        },
        {
            "role":          "pivot",
            "offset_days":   (105, 195),  # 15w → 28w
            "human_meaning": "The threshold you can't cross twice",
            "name_template": "The Threshold You Can't Cross Twice",
            "categorical_label":
                f"Two paths in {HOUSE_SHORT.get(venus_house, 'relationships')}",
            "categorical_context": (
                f"Underlying activation: {sun_area} (Sun), "
                f"{venus_area} (Venus)."
            ),
            "is_primary":    True,
            "whats_happening": [
                "Two versions of you become visible — the one you've "
                "been and the one you could become",
                "The tension you've been carrying crystallises into a "
                "clear choice",
            ],
            "what_this_creates": [
                "A sense that this stretch will be remembered as a "
                "before / after moment",
                "The strange calm of knowing what you need to do, even "
                "before you've done it",
            ],
            "where_people_get_it_wrong": [
                "Waiting for certainty that never comes — the "
                "information is already sufficient",
                "Choosing what's comfortable instead of what's actually "
                "aligned",
            ],
            "what_its_asking_of_you": [
                "Make the choice you've been circling — you've been "
                "preparing for this",
                "Trust what you've learned about yourself in the past "
                "few months",
            ],
            "description": (
                "Two versions of you become visible — the one you've "
                "been, and the one you've been quietly becoming. The "
                "choice that's been building since earlier in the year "
                "becomes the kind of choice you can only make once. "
                "Walking back across it later isn't really an option."
            ),
        },
        {
            "role":          "settling",
            "offset_days":   (195, 320),  # 28w → 46w
            "human_meaning": "What the year asks you to keep",
            "name_template": "The Shape That Holds After",
            "categorical_label":
                f"What settles in {HOUSE_SHORT.get(saturn_house, 'career')} "
                f"and {HOUSE_SHORT.get(mars_house, 'action')}",
            "categorical_context": (
                f"Underlying activation: {saturn_area} (Saturn), "
                f"{mars_area} (Mars), {venus_area} (Venus)."
            ),
            "is_primary":    False,
            "whats_happening": [
                "The ripples from the earlier pivot start showing up "
                "in how things actually run, day to day",
                "What you decided either holds its new shape, or asks "
                "for one more honest conversation",
            ],
            "what_this_creates": [
                "Either: the relief of having finally moved, and new "
                "ground beneath your feet",
                "Or: the recognition that you're not done yet — and "
                "clarity about what next year still needs to address",
            ],
            "where_people_get_it_wrong": [
                "Forcing a sense of completion before it's earned",
                "Dismissing what the year taught because it was "
                "uncomfortable",
            ],
            "what_its_asking_of_you": [
                "Honest inventory: what actually changed, and what "
                "only temporarily settled?",
                "Gratitude for the growth, acceptance for what remains",
            ],
            "description": (
                "What remains after the adjustment becomes more "
                "important than what was temporarily preserved. The "
                "choice you made earlier in the year either holds its "
                "shape, or quietly asks for one more honest pass. "
                "Either way: the ground you're standing on at the end "
                "of the year isn't the ground you were standing on at "
                "the start."
            ),
        },
    ]

    # Build phases with date windows. Cap each phase end at end-of-year
    # so a phase doesn't run into next year's arc.
    eoy = datetime(year, 12, 31)
    phases: List[Dict[str, Any]] = []
    for idx, t in enumerate(phase_role_templates):
        d0, d1 = t["offset_days"]
        start = gen_dt + timedelta(days=d0)
        end = gen_dt + timedelta(days=d1)
        # Don't let phases bleed past calendar year (keeps "this year"
        # bounded for users reading mid-year).
        if start > eoy:
            continue
        end = min(end, eoy)
        # Sanity: keep at least 14 days between start and end
        if (end - start).days < 14:
            continue

        is_current = (start <= gen_dt <= end)
        is_past = end < gen_dt
        is_upcoming = start > gen_dt

        phases.append({
            "id":             f"p{idx + 1}",
            "role":           t["role"],
            "name":           t["name_template"],
            # Phase 1 reframing: preserve the old categorical/topic
            # title for use inside the proof drawer only — it must
            # never appear in user-visible primary copy. The visible
            # "name" above is the new existential title.
            "categorical_label": t.get("categorical_label", ""),
            "period":         _date_range_label(start, end),
            "period_start":   start.strftime("%Y-%m-%d"),
            "period_end":     end.strftime("%Y-%m-%d"),
            "human_meaning":  t["human_meaning"],
            "description":    t["description"],
            "whats_happening":            t["whats_happening"],
            "what_this_creates":          t["what_this_creates"],
            "where_people_get_it_wrong":  t["where_people_get_it_wrong"],
            "what_its_asking_of_you":     t["what_its_asking_of_you"],
            "is_primary":     bool(t["is_primary"]),
            "is_current":     is_current,
            "is_past":        is_past,
            "is_upcoming":    is_upcoming,
        })

    # Cap at 4 (in case eoy logic kept all four); minimum 2 to keep
    # the UI useful even when generated late in the year.
    phases = phases[:4]

    current_phase_id = next((p["id"] for p in phases if p["is_current"]), None)

    # ---- Turning points (3, NOW-anchored, no fixed Apr/Aug/Nov) --------
    # Anchored to "soon", "mid-cycle", "late". Each carries a real
    # date label derived from gen_dt + offset.
    def _month_label(dt: datetime) -> str:
        # "Early May 2026" / "Mid June 2026" / "Late October 2026"
        d = dt.day
        bucket = "Early" if d <= 10 else ("Mid" if d <= 20 else "Late")
        return f"{bucket} {dt.strftime('%B %Y')}"

    tp_offsets = [
        ("soon",        45,  "confrontation",
            HOUSE_AREAS.get(moon_house, "emotional life"),
            moon_area, venus_area),
        ("mid_cycle",   135, "decision",
            HOUSE_AREAS.get(sun_house, "identity"),
            sun_area, saturn_area),
        ("late_year",   240, "integration",
            HOUSE_AREAS.get(saturn_house, "responsibility"),
            saturn_area, sun_area),
    ]
    turning_points: List[Dict[str, Any]] = []
    for slot, days, tp_type, life_area, primary_area, secondary_area in tp_offsets:
        ts = gen_dt + timedelta(days=days)
        if ts > eoy:
            # If it would slip past year-end, anchor to a late-year slot
            ts = eoy - timedelta(days=7)
        # v1.3: rewritten to existential / consequence framing.
        # `life_area` and `*_area` strings are retained internally as
        # `categorical_context` for the proof drawer only — never in
        # user-visible primary copy.
        if tp_type == "confrontation":
            what_activates = (
                f"Something happens that makes the {tension} tension "
                "impossible to keep calling 'manageable'. The cost of "
                "continuing as you have been becomes more visible than "
                "the cost of changing."
            )
            what_becomes_clear = (
                "What you've been tolerating. Why you've been tolerating "
                "it. And what it's actually been taking from you while "
                "you weren't looking."
            )
            if_avoided = (
                "The pattern doesn't go away — it goes underground. What "
                "could have been addressed as a conversation becomes a "
                "crisis later in the year."
            )
        elif tp_type == "decision":
            what_activates = (
                "This is the year's primary choice point. The options "
                "are clear. The information is sufficient. What remains "
                "is whether you'll choose from who you're becoming — or "
                "retreat to who you've already been."
            )
            what_becomes_clear = (
                "Which direction matches the person you've been growing "
                "into. The version of you that hesitates and the version "
                "that moves forward both become visible at the same time."
            )
            if_avoided = (
                "The choice gets made for you by circumstances. You stay "
                "moving, but you lose authorship of your own direction."
            )
        else:  # integration
            what_activates = (
                "The year's arc reaches its natural conclusion. What you "
                "started earlier is ready to be named: either as "
                "something that changed, or as something that needs "
                "another cycle to finish."
            )
            what_becomes_clear = (
                "Whether the year's lesson actually landed. Whether "
                "you're entering next year with new ground beneath you "
                "— or carrying forward what this year tried to resolve."
            )
            if_avoided = (
                "You enter next year still holding what this year asked "
                "you to put down. The same pattern returns, but with "
                "higher stakes."
            )
        turning_points.append({
            "id":                f"tp_{slot}",
            "timing":            _month_label(ts),
            "anchor_date":       ts.strftime("%Y-%m-%d"),
            "type":              tp_type,
            # `life_area` is retained for backwards-compat consumers
            # (Ask About My Life interpreter, life_phase generator).
            # The proof drawer will surface it as `categorical_context`.
            "life_area":         life_area,
            "categorical_context": (
                f"Underlying activation: {primary_area} (primary), "
                f"{secondary_area} (secondary). Life area: {life_area}."
            ),
            "what_activates":    what_activates,
            "what_becomes_clear": what_becomes_clear,
            "if_avoided":        if_avoided,
        })

    # ---- Decision windows (3, NOW-anchored) -----------------------------
    # v1.3 rewrite: drop "In {house_short}" context; existential prompt
    # carries the framing. The old categorical context is preserved on
    # each window as `categorical_context` for the proof drawer.
    dw_specs = [
        (21,
            HOUSE_SHORT.get(mars_house, "action"),
            "Naming",                                    # existential context label
            "You can name it now. Or you can wait until it names itself.",
            ("The conversation gets uncomfortable fast, but the "
             "uncertainty stops running the show. In two weeks you'll "
             "be glad you didn't wait."),
            ("You preserve the surface peace for now, but the thing "
             "you're avoiding keeps growing underneath it. By the next "
             "window it's bigger.")
        ),
        (90,
            HOUSE_SHORT.get(venus_house, "relationships"),
            "Truth-telling in close range",
            "You can say what's actually true. Or you can keep editing "
            "yourself for the room.",
            pattern["cost_of_action"]
            + ". The connection changes — but at least now it's based "
              "on something real.",
            pattern["cost_of_waiting"]
            + ". The connection stays familiar, but you start noticing "
              "how tired you are of managing it.",
        ),
        (180,
            HOUSE_SHORT.get(saturn_house, "career"),
            "Committing to the new direction",
            "You can commit to the new direction. Or you can keep one "
            "foot in both worlds.",
            ("Some doors close. The grief is real. But so is the focus "
             "— and the energy that comes from finally choosing."),
            ("All options stay open, but your energy stays scattered. "
             "You'll wish you'd trusted yourself sooner."),
        ),
    ]
    decision_windows: List[Dict[str, Any]] = []
    for d_off, ctx_short, ctx_existential, prompt, if_act, if_wait in dw_specs:
        ws = gen_dt + timedelta(days=d_off - 7)
        we = gen_dt + timedelta(days=d_off + 7)
        if ws > eoy:
            continue
        we = min(we, eoy)
        decision_windows.append({
            "id":         f"dw_{d_off}",
            "period":     _date_range_label(ws, we),
            "period_start": ws.strftime("%Y-%m-%d"),
            "period_end":   we.strftime("%Y-%m-%d"),
            # v1.3: visible-tier context is existential, not "In {house}".
            "context":    ctx_existential,
            # categorical context retained for the proof drawer.
            "categorical_context": f"In {ctx_short}",
            "prompt":     prompt,
            "if_act":     if_act,
            "if_wait":    if_wait,
        })

    payload = {
        # Top-level — interpreter will pick up year_theme directly.
        "year_theme":      year_theme,
        "year_question":   year_theme,  # alias accepted by ATI
        "arc":             arc,
        "tension":         tension,
        "phases":          phases,
        "current_phase_id": current_phase_id,
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
        "generated_for":    gen_dt.strftime("%Y-%m-%d"),
        "source":           "real_astrology_timeline",
        "generator_version": "astrology_timeline_v1_2_python",
    }
    logger.debug(
        "[AstrologyTimelineGenerator] sun=%s sun_house=%d moon_house=%d "
        "venus_house=%d saturn_house=%d -> %d phases / %d turning points",
        sun_sign, sun_house, moon_house, venus_house, saturn_house,
        len(phases), len(turning_points),
    )
    return payload


__all__ = ["generate_astrology_timeline", "SIGN_PATTERNS", "HOUSE_AREAS", "HOUSE_SHORT"]
