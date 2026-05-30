"""
Relationship Astrology Engine (V2 — deep spouse-aware synthesis)
=================================================================

Build marker: relationship-mapping-deep-astrology-v2

Produces a richer, role-aware astrology relational synthesis to replace
the shallow "you hold them to a higher standard" bullet in the member-
mappings page. Used PRIMARILY when relationship_role ∈ {spouse, partner,
ex_partner}; when role is other (close_friend, parent, child, colleague,
forum_member) the synthesis is still produced but with role-appropriate
framing.

Inputs:
    chart_a: viewer chart (asker)
    chart_b: target chart
    relationship_role: spouse | partner | ex_partner | child | parent | ...
    closeness, emotional_weight (from relationship_resolver)
    name_a, name_b

Output:
    {
        success: bool,
        build_marker: "relationship-mapping-deep-astrology-v2",
        relationship_role: "spouse",
        core_relational_pattern: "Mercury reach vs Pisces atmosphere",
        emotional_safety_loop: "...",
        communication_loop: "...",
        intimacy_loop: "...",
        conflict_signature: "...",
        repair_condition: "...",
        what_a_triggers_in_b: "...",
        what_b_triggers_in_a: "...",
        where_it_gets_misread: "...",
        spouse_specific_translation: "Pete's calm steadiness can be experienced
                                       as emotional absence by Mel...",
        supporting_signals: [
            "Pete Sun in Pisces — receives atmosphere before thought",
            "Mel Sun in Gemini — processes through language and option",
            ...
        ],
        astrology_card: {
            headline: str,
            body:     str,
            supporting_signals: [str, ...],
        },
    }
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "relationship-mapping-deep-astrology-v2"

# ---------------------------------------------------------------------------
# Sign mechanics — concise, lived-experience language (not textbook)
# ---------------------------------------------------------------------------
SIGN_MECHANICS: Dict[str, Dict[str, str]] = {
    "Aries":      {"element": "fire",  "mode": "cardinal",
                   "drive": "initiates by acting before deliberating",
                   "intimacy": "lands through directness; reads hedging as withholding"},
    "Taurus":     {"element": "earth", "mode": "fixed",
                   "drive": "stabilises through what can be touched and tasted",
                   "intimacy": "lands through sensory presence; reads urgency as threat"},
    "Gemini":     {"element": "air",   "mode": "mutable",
                   "drive": "processes through language, movement, mental framing, options, change",
                   "intimacy": "experiences talking and explaining as connection; needs air and movement"},
    "Cancer":     {"element": "water", "mode": "cardinal",
                   "drive": "navigates by atmosphere, memory, and emotional weather",
                   "intimacy": "needs felt safety before words; reads logic-during-feeling as dismissal"},
    "Leo":        {"element": "fire",  "mode": "fixed",
                   "drive": "becomes visible by taking up space and being seen",
                   "intimacy": "needs witnessing; reads neutrality as withdrawal of warmth"},
    "Virgo":      {"element": "earth", "mode": "mutable",
                   "drive": "orders through precision, refinement, exact care",
                   "intimacy": "lands through small acts of care; reads sloppiness as not-bothered"},
    "Libra":      {"element": "air",   "mode": "cardinal",
                   "drive": "calibrates by reading the other side and finding the balance point",
                   "intimacy": "needs the partner's presence as mirror; reads being alone as not-chosen"},
    "Scorpio":    {"element": "water", "mode": "fixed",
                   "drive": "moves through what is faced when the surface drops",
                   "intimacy": "needs trust earned in depth; reads small evasions as betrayal"},
    "Sagittarius":{"element": "fire",  "mode": "mutable",
                   "drive": "scales through meaning, scope, the wider frame",
                   "intimacy": "needs room to roam mentally; reads control as suffocation"},
    "Capricorn":  {"element": "earth", "mode": "cardinal",
                   "drive": "structures by long arc, discipline, the form that lasts",
                   "intimacy": "lands through reliability over time; reads moodiness as instability"},
    "Aquarius":   {"element": "air",   "mode": "fixed",
                   "drive": "differentiates by stepping outside the pattern and finding the wider view",
                   "intimacy": "lands through respect for autonomy; reads possessiveness as suffocation"},
    "Pisces":     {"element": "water", "mode": "mutable",
                   "drive": "processes through atmosphere, emotional permeability, subtle signals, fusion, sensitivity",
                   "intimacy": "experiences explanation-without-emotional-presence as distance; needs emotional saturation and reassurance"},
}

# Outer planets / nodal axis flavour
_OUTER_FLAVOUR = {
    "Uranus":  "electric interruption — the field will not stay still",
    "Neptune": "the field's outlines dissolve — what felt solid becomes diffuse",
    "Pluto":   "deep pressure on what the field is built on — compulsive intensity",
    "Saturn":  "the field edits itself — narrower than the interior wants",
}

# Role-specific synthesis framing
_ROLE_FRAMING = {
    "spouse":      "Inside the marriage / household field — emotional safety, intimacy, conflict, repair.",
    "partner":     "Inside the intimate partnership — chemistry, conflict, what holds and what dissolves.",
    "ex_partner":  "Inside the residual relational charge — what still pulls, what has been re-organised.",
    "child":       "Inside the parent–child container — how the child's field is held inside the household.",
    "parent":      "Inside the parent–child container — how the parent's field shaped the asker's foundation.",
    "sibling":     "Inside the shared-origin field — what was held in common, what diverged.",
    "close_friend":"Inside the chosen-family field — what is named and what is felt without naming.",
    "close_circle":"Inside the small trusted group — how this field meets the asker's in close company.",
    "friend":      "Inside the ongoing friendship — what stabilises and what destabilises across time.",
    "colleague":   "Inside the professional container — the working-edge of the field.",
    "boss":        "Across the authority gradient — how the field meets the asker's across power.",
    "forum_member":"Inside the shared reflective space — what shows up when both fields are present.",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_planet(planets: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    if not planets:
        return None
    for k in (name, name.capitalize(), name.lower()):
        if k in planets:
            return planets[k]
    return None


def _planet_sign(planets: Dict[str, Any], name: str) -> Optional[str]:
    p = _get_planet(planets, name)
    if not p:
        return None
    return p.get("sign")


def _planet_house(planets: Dict[str, Any], name: str) -> Optional[int]:
    p = _get_planet(planets, name)
    if not p:
        return None
    return p.get("house")


def _ic_sign(astro: Dict[str, Any]) -> Optional[str]:
    # IC is the 4th-house cusp sign. Use formatted_cusps or cusp_signs.
    houses = (astro or {}).get("houses") or {}
    if isinstance(houses, dict):
        cusp_signs = houses.get("cusp_signs")
        if isinstance(cusp_signs, list) and len(cusp_signs) >= 4:
            v = cusp_signs[3]
            if isinstance(v, str):
                return v
        fmt = houses.get("formatted_cusps") or []
        if isinstance(fmt, list):
            for c in fmt:
                if isinstance(c, dict) and c.get("house") == 4:
                    return c.get("sign")
    return None


def _planets_in_house(planets: Dict[str, Any], house_n: int) -> List[str]:
    out = []
    if not isinstance(planets, dict):
        return out
    for name, p in planets.items():
        if isinstance(p, dict) and p.get("house") == house_n:
            out.append(name)
    return out


# ---------------------------------------------------------------------------
# Core loop builders
# ---------------------------------------------------------------------------
def _build_sign_loop(
    sun_a: Optional[str], sun_b: Optional[str],
    moon_a: Optional[str], moon_b: Optional[str],
    name_a: str, name_b: str,
) -> Tuple[str, str, str]:
    """Return (core_pattern, emotional_safety_loop, communication_loop)."""
    a_sun = SIGN_MECHANICS.get(sun_a) if sun_a else None
    b_sun = SIGN_MECHANICS.get(sun_b) if sun_b else None
    a_moon = SIGN_MECHANICS.get(moon_a) if moon_a else None
    b_moon = SIGN_MECHANICS.get(moon_b) if moon_b else None

    # CORE PATTERN
    if a_sun and b_sun:
        a_el, b_el = a_sun["element"], b_sun["element"]
        core = (
            f"{name_a}'s Sun in {sun_a} ({a_sun['drive']}); "
            f"{name_b}'s Sun in {sun_b} ({b_sun['drive']})."
        )
        # Elemental compress: air↔water = "thought vs atmosphere"
        if (a_el, b_el) in (("air", "water"), ("water", "air")):
            air = name_a if a_el == "air" else name_b
            water = name_b if a_el == "air" else name_a
            core += (
                f" The asymmetry: {air} reaches for clarity through language; "
                f"{water} reads atmosphere first. This is where the friction begins."
            )
        elif (a_el, b_el) in (("fire", "earth"), ("earth", "fire")):
            fire = name_a if a_el == "fire" else name_b
            earth = name_b if a_el == "fire" else name_a
            core += (
                f" The asymmetry: {fire} initiates by moving; {earth} stabilises "
                "by building. Pace mismatch is the recurring edge."
            )
        elif (a_el, b_el) in (("fire", "water"), ("water", "fire")):
            fire = name_a if a_el == "fire" else name_b
            water = name_b if a_el == "fire" else name_a
            core += (
                f" The asymmetry: {fire} runs on warmth and momentum; "
                f"{water} runs on saturation and depth. Both register heat — "
                "but one means activity, the other means feeling."
            )
        elif a_el == b_el:
            core += (
                " The element matches — which makes you fluent with each "
                "other but can dim the productive friction."
            )
    else:
        core = f"Sun-sign data partial for {name_a} or {name_b}."

    # EMOTIONAL SAFETY LOOP (driven by Moon mechanics)
    if a_moon and b_moon:
        safety = (
            f"{name_a} feels safe through {a_moon['intimacy'].split(';')[0]}. "
            f"{name_b} feels safe through {b_moon['intimacy'].split(';')[0]}."
        )
        # Specific loop framing
        if b_moon["element"] == "water" and a_moon["element"] == "air":
            safety += (
                f" Loop: when {name_a} stays calm and analytical, "
                f"{name_b}'s nervous system reads the calm as emotional absence "
                "and starts searching for what is missing — even when nothing "
                "outwardly is wrong."
            )
        elif a_moon["element"] == "water" and b_moon["element"] == "air":
            safety += (
                f" Loop: when {name_b} stays calm and analytical, "
                f"{name_a}'s nervous system reads it as emotional absence."
            )
    else:
        safety = "Moon-sign data partial — emotional-safety loop not fully computed."

    # COMMUNICATION LOOP
    if a_sun and b_sun:
        if a_sun["element"] == "air" and b_sun["element"] == "water":
            comm = (
                f"{name_a} talks toward connection; {name_b} feels toward connection. "
                f"{name_a} may believe explanation IS presence. {name_b} may experience "
                "explanation-without-emotional-warmth as distance."
            )
        elif a_sun["element"] == "water" and b_sun["element"] == "air":
            comm = (
                f"{name_a} feels toward connection; {name_b} talks toward connection. "
                f"{name_b} may believe explanation IS presence. {name_a} may experience "
                "explanation-without-emotional-warmth as distance."
            )
        elif a_sun["element"] == b_sun["element"]:
            comm = (
                f"Same elemental register — communication flows but can lose the "
                "productive edge that the other elements would bring."
            )
        else:
            comm = (
                f"{name_a} communicates through {a_sun['drive'].split(',')[0]}; "
                f"{name_b} through {b_sun['drive'].split(',')[0]}. "
                "Translation is required."
            )
    else:
        comm = "Communication loop not fully computed (Sun data partial)."

    return core, safety, comm


def _build_conflict_repair(
    sun_a: Optional[str], sun_b: Optional[str],
    moon_a: Optional[str], moon_b: Optional[str],
    name_a: str, name_b: str,
) -> Tuple[str, str]:
    """Return (conflict_signature, repair_condition)."""
    a_m = SIGN_MECHANICS.get(moon_a) if moon_a else None
    b_m = SIGN_MECHANICS.get(moon_b) if moon_b else None
    if not a_m or not b_m:
        return ("Conflict signature partial — Moon data missing.",
                "Repair condition partial.")

    a_el, b_el = a_m["element"], b_m["element"]

    if a_el == "air" and b_el == "water":
        return (
            f"In conflict, {name_a} analyzes and tries to find the rational frame; "
            f"{name_b} absorbs and may withdraw. The mismatch makes {name_a} talk "
            f"more and {name_b} go quieter.",
            f"{name_b} needs emotional warmth before clarity can land. {name_a} "
            f"may need to lead with body-presence (eye contact, slowed breath, "
            "touch) before language."
        )
    if a_el == "water" and b_el == "air":
        return (
            f"In conflict, {name_b} analyzes; {name_a} absorbs and may withdraw. "
            f"{name_b} talks more, {name_a} goes quieter.",
            f"{name_a} needs emotional warmth first. {name_b} may need to lead "
            "with presence before words."
        )
    if a_el == "fire" and b_el == "earth":
        return (
            f"{name_a} pushes; {name_b} resists by holding ground. Timing "
            "mismatch becomes the argument.",
            f"{name_a} slows the pace by a beat; {name_b} names the discomfort "
            "in clear language before retreating."
        )
    if a_el == "earth" and b_el == "fire":
        return (
            f"{name_b} pushes; {name_a} resists by holding ground.",
            f"{name_b} slows the pace; {name_a} names the discomfort in clear "
            "language."
        )
    if a_el == b_el:
        return (
            f"Same elemental fight — when conflict comes, you escalate or "
            "withdraw in sync, missing the corrective friction the other element "
            "would supply.",
            "deliberate slowing — one of you must take the missing-element "
            "role consciously."
        )
    return (
        f"{name_a}'s Moon ({a_el}) and {name_b}'s Moon ({b_el}) read conflict "
        "differently — one as activity, the other as emotional load.",
        "name the asymmetry out loud before debating content."
    )


def _ic_layer_for_target(
    target_astro: Dict[str, Any],
    target_planets: Dict[str, Any],
    name_b: str,
) -> Optional[str]:
    """Build the 4th-house / IC / emotional-foundation layer for the target.
    This is the spouse-relevant 'how Mel experiences emotional safety' line.
    """
    ic_sign = _ic_sign(target_astro)
    if not ic_sign:
        return None
    ic_mech = SIGN_MECHANICS.get(ic_sign) or {}
    h4_planets = _planets_in_house(target_planets, 4)
    destab = None
    for p in h4_planets:
        if p in _OUTER_FLAVOUR:
            destab = p
            break
    foundation = (
        f"{name_b}'s emotional foundation is shaped by {ic_sign} on the IC — "
        f"{ic_mech.get('intimacy', 'their emotional ground').split(';')[0]}."
    )
    if destab:
        foundation += (
            f" {destab} sits in the 4th house — {_OUTER_FLAVOUR[destab]} — so "
            "the foundation does not stay still. When the emotional field becomes "
            "procedural, muted, or emotionally absent, the nervous system starts "
            "searching for what is missing even when nothing outwardly is wrong."
        )
    return foundation


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_relationship_astrology(
    *,
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str,
    name_b: str,
    relationship_role: str = "forum_member",
    closeness: str = "medium",
    emotional_weight: str = "medium",
) -> Dict[str, Any]:
    """Build the deep V2 relational-astrology synthesis."""
    if not chart_a or not chart_b:
        return {"success": False, "reason": "missing_chart_data",
                "build_marker": BUILD_MARKER}
    astro_a = chart_a.get("astrology") or {}
    astro_b = chart_b.get("astrology") or {}
    planets_a = astro_a.get("planets") or {}
    planets_b = astro_b.get("planets") or {}

    sun_a = _planet_sign(planets_a, "Sun")
    sun_b = _planet_sign(planets_b, "Sun")
    moon_a = _planet_sign(planets_a, "Moon")
    moon_b = _planet_sign(planets_b, "Moon")
    rising_a = _planet_sign(planets_a, "Ascendant") or (
        ((astro_a.get("angles") or {}).get("ascendant") or {}).get("sign")
    )
    rising_b = _planet_sign(planets_b, "Ascendant") or (
        ((astro_b.get("angles") or {}).get("ascendant") or {}).get("sign")
    )

    core_pattern, safety_loop, communication_loop = _build_sign_loop(
        sun_a, sun_b, moon_a, moon_b, name_a, name_b,
    )
    conflict_sig, repair_cond = _build_conflict_repair(
        sun_a, sun_b, moon_a, moon_b, name_a, name_b,
    )
    ic_layer = _ic_layer_for_target(astro_b, planets_b, name_b)

    # Role-specific translation
    role_framing = _ROLE_FRAMING.get(relationship_role, _ROLE_FRAMING["forum_member"])

    # SPOUSE-SPECIFIC TRANSLATION (or partner equivalent)
    is_intimate = relationship_role in ("spouse", "partner")
    spouse_translation = None
    if is_intimate:
        a_sun_m = SIGN_MECHANICS.get(sun_a) if sun_a else None
        b_sun_m = SIGN_MECHANICS.get(sun_b) if sun_b else None
        if a_sun_m and b_sun_m:
            if a_sun_m["element"] == "air" and b_sun_m["element"] == "water":
                spouse_translation = (
                    f"{name_a} thinks staying calm and rational IS being present. "
                    f"{name_b} may experience that same calm as emotional absence. "
                    "The conflict loop is not care-versus-lack-of-care. It is "
                    "language-versus-atmosphere."
                )
            elif a_sun_m["element"] == "water" and b_sun_m["element"] == "air":
                spouse_translation = (
                    f"{name_b} thinks explaining IS presence. {name_a} may "
                    "experience that explanation-without-emotional-warmth as "
                    "distance."
                )
            elif a_sun_m["element"] == b_sun_m["element"]:
                spouse_translation = (
                    f"Same elemental register — you understand each other's "
                    "language fluently. The risk is losing the productive "
                    "friction that an opposite element would supply."
                )
            else:
                spouse_translation = (
                    f"{name_a} processes through "
                    f"{a_sun_m['drive'].split(',')[0]}; "
                    f"{name_b} processes through "
                    f"{b_sun_m['drive'].split(',')[0]}. "
                    "Translation is the relational work."
                )

    # WHAT EACH TRIGGERS IN THE OTHER
    what_a_triggers = None
    what_b_triggers = None
    a_moon_m = SIGN_MECHANICS.get(moon_a) if moon_a else None
    b_moon_m = SIGN_MECHANICS.get(moon_b) if moon_b else None
    if a_moon_m and b_moon_m:
        if a_moon_m["element"] == "air" and b_moon_m["element"] == "water":
            what_a_triggers = (
                f"When {name_a} stays in the head — analytical, calm, neutral — "
                f"{name_b}'s nervous system reads the silence and starts searching."
            )
            what_b_triggers = (
                f"When {name_b} goes quiet or withdraws, {name_a} may try to fix "
                "the rupture with more language, which compounds the loop."
            )
        elif a_moon_m["element"] == "water" and b_moon_m["element"] == "air":
            what_a_triggers = (
                f"When {name_a} goes quiet, {name_b} may try to bridge with "
                "language — which {name_a} can experience as performance."
            )
            what_b_triggers = (
                f"When {name_b} stays analytical, {name_a} reads it as absence."
            )

    where_misread = (
        f"The relationship gets misread as care-vs-coldness, when it is actually "
        "two different operating systems trying to translate the same intention."
        if (a_moon_m and b_moon_m
            and {a_moon_m["element"], b_moon_m["element"]} == {"air", "water"})
        else "Translation gaps get personalised — read as character flaws rather "
             "than register mismatch."
    )

    # Supporting signals (deterministic, citable)
    supporting: List[str] = []
    if sun_a:
        supporting.append(
            f"{name_a} Sun in {sun_a} — {SIGN_MECHANICS.get(sun_a, {}).get('drive', '')}"
        )
    if sun_b:
        supporting.append(
            f"{name_b} Sun in {sun_b} — {SIGN_MECHANICS.get(sun_b, {}).get('drive', '')}"
        )
    if moon_a:
        supporting.append(
            f"{name_a} Moon in {moon_a} — feels safe via "
            f"{SIGN_MECHANICS.get(moon_a, {}).get('intimacy', '').split(';')[0]}"
        )
    if moon_b:
        supporting.append(
            f"{name_b} Moon in {moon_b} — feels safe via "
            f"{SIGN_MECHANICS.get(moon_b, {}).get('intimacy', '').split(';')[0]}"
        )
    if rising_a:
        supporting.append(f"{name_a} Rising in {rising_a}")
    if rising_b:
        supporting.append(f"{name_b} Rising in {rising_b}")
    if ic_layer:
        supporting.append(ic_layer)

    # ASTROLOGY CARD (replaces the shallow line in member-mappings UI)
    a_sun_m = SIGN_MECHANICS.get(sun_a) if sun_a else None
    b_sun_m = SIGN_MECHANICS.get(sun_b) if sun_b else None
    if (a_sun_m and b_sun_m
            and {a_sun_m["element"], b_sun_m["element"]} == {"air", "water"}):
        air_side = name_a if a_sun_m["element"] == "air" else name_b
        water_side = name_b if a_sun_m["element"] == "air" else name_a
        headline = (
            f"{air_side}'s mind reaches for clarity; "
            f"{water_side} reads atmosphere first."
        )
    elif (a_sun_m and b_sun_m
            and {a_sun_m["element"], b_sun_m["element"]} == {"fire", "earth"}):
        fire_side = name_a if a_sun_m["element"] == "fire" else name_b
        earth_side = name_b if a_sun_m["element"] == "fire" else name_a
        headline = (
            f"{fire_side} initiates by moving; "
            f"{earth_side} stabilises by building. Pace is the recurring edge."
        )
    elif (a_sun_m and b_sun_m and a_sun_m["element"] == b_sun_m["element"]):
        headline = (
            f"{name_a} and {name_b} share the {a_sun_m['element']} register — "
            "fluent with each other, missing the productive friction."
        )
    else:
        headline = (
            f"{name_a}'s field and {name_b}'s field — two different operating "
            "systems trying to translate the same intention."
        )
    body_parts = [core_pattern]
    if spouse_translation:
        body_parts.append(spouse_translation)
    if ic_layer:
        body_parts.append(ic_layer)
    body_parts.append(f"Conflict signature: {conflict_sig}")
    body_parts.append(f"Repair condition: {repair_cond}")
    body = " ".join(body_parts)

    return {
        "success":                  True,
        "build_marker":             BUILD_MARKER,
        "relationship_role":        relationship_role,
        "closeness":                closeness,
        "emotional_weight":         emotional_weight,
        "role_framing":             role_framing,
        "core_relational_pattern":  core_pattern,
        "emotional_safety_loop":    safety_loop,
        "communication_loop":       communication_loop,
        "intimacy_loop":            spouse_translation if is_intimate else None,
        "conflict_signature":       conflict_sig,
        "repair_condition":         repair_cond,
        "what_a_triggers_in_b":     what_a_triggers,
        "what_b_triggers_in_a":     what_b_triggers,
        "where_it_gets_misread":    where_misread,
        "spouse_specific_translation": spouse_translation if is_intimate else None,
        "ic_emotional_foundation":  ic_layer,
        "supporting_signals":       supporting,
        "astrology_card": {
            "headline":             headline,
            "body":                 body,
            "supporting_signals":   supporting,
        },
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
# Common shallow phrases that tend to repeat across HD / astrology /
# enneagram / bazi cards. When two sections both surface the same phrase,
# the weaker (later-priority) is suppressed.
_DEDUPE_PHRASES = [
    "emotional reach",
    "building together",
    "coordination",
    "shared responsibility",
    "shared direction",
    "what activates",
    "higher standard",
    "energetic mechanics",
]


def dedupe_mapping_sections(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Walk the mapping payload and dedupe overlapping themes across
    sections (summary / HD / astrology / bazi / enneagram).

    Records dedupe activity into mapping["debug"]["relationship_mapping_dedupe"].
    Priority order: summary > field synthesis > astrology > HD > BaZi >
    Enneagram > Numerology. Lower-priority sections lose duplicate themes.
    """
    debug: Dict[str, Any] = {
        "repeated_themes_detected":  [],
        "suppressed_duplicates":     [],
        "final_sections_unique":     True,
        "build_marker":              BUILD_MARKER,
    }

    signals = mapping.get("signals") or {}
    section_order = ["astrology", "human_design", "bazi", "enneagram", "numerology"]
    seen_phrases: set = set()

    def _collect_text(section_data: Any) -> str:
        if section_data is None:
            return ""
        if isinstance(section_data, str):
            return section_data
        if isinstance(section_data, list):
            return " ".join(_collect_text(x) for x in section_data)
        if isinstance(section_data, dict):
            return " ".join(_collect_text(v) for v in section_data.values())
        return ""

    def _scrub_list_dedupe(items: List[str], section_label: str) -> List[str]:
        if not isinstance(items, list):
            return items
        kept: List[str] = []
        for item in items:
            if not isinstance(item, str):
                kept.append(item)
                continue
            low = item.lower()
            hit = next((p for p in _DEDUPE_PHRASES if p in low), None)
            if hit and hit in seen_phrases:
                debug["suppressed_duplicates"].append({
                    "section":  section_label,
                    "phrase":   hit,
                    "snippet":  item[:120],
                })
                continue
            if hit:
                seen_phrases.add(hit)
                if hit not in debug["repeated_themes_detected"]:
                    debug["repeated_themes_detected"].append(hit)
            kept.append(item)
        return kept

    for section_label in section_order:
        section = signals.get(section_label)
        if not section:
            continue
        if isinstance(section, dict):
            for key, val in list(section.items()):
                if isinstance(val, list):
                    section[key] = _scrub_list_dedupe(val, f"{section_label}.{key}")

    # Dedupe top-level patterns too — what_happens / tensions / gifts
    patterns = mapping.get("patterns") or {}
    for k in ("what_happens", "tensions", "gifts"):
        if isinstance(patterns.get(k), list):
            patterns[k] = _scrub_list_dedupe(patterns[k], f"patterns.{k}")

    if debug["suppressed_duplicates"]:
        debug["final_sections_unique"] = True
    # Attach
    mapping.setdefault("debug", {})["relationship_mapping_dedupe"] = debug
    return mapping


__all__ = [
    "build_relationship_astrology",
    "dedupe_mapping_sections",
    "BUILD_MARKER",
]
