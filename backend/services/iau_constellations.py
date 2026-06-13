"""
IAU Constellation Overlay — Ophiuchus-aware sky mapping.
=========================================================

This module is PURELY ADDITIVE. It does NOT change how Mirror computes the
12-sign True Sidereal zodiac. Instead, it layers a *secondary* sky-observation
view on top of the canonical astronomy — mapping each body's ecliptic
longitude to the actual IAU constellation the Sun/Moon/planet is "passing
through" on the celestial sphere.

This is the layer that lets us say, honestly:

    "If we look at the sky directly, your Sun is currently passing through
     Ophiuchus — this adds a layer of..."

without breaking the 12-sign model that the rest of Mirror depends on.

## Source of truth

IAU 1930 official constellation boundaries (Delporte) projected onto the
ecliptic. The Sun's annual path crosses 13 constellations (Scorpius is the
shortest at ~7°; Ophiuchus occupies ~19° between Scorpius and Sagittarius).

Boundaries are expressed in **tropical J2000 ecliptic longitude**. Since the
canonical astronomy layer already stores both sidereal AND tropical longitudes
per body, the overlay maps against `tropical_longitude` to avoid any
ayanamsa-dependent drift.

Values below are the standard ones used by astronomy software and the IAU
sun-path tables (e.g. NASA / Meeus).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any

# ---------------------------------------------------------------------------
# Canonical SVP — used to reconstruct tropical longitude from a stored
# sidereal longitude when callers provide only `longitude` (sidereal) on
# an angle / body record.
#
# Build marker: angle-staleness-step1-v1 (remediation)
#
# Prior to this remediation, this module hardcoded a literal `28.69`
# offset in four places (sources marked `D9` in the forensic audit).
# `28.69` ≠ canonical `SVP_DEGREES = 31.2836` — Δ = −2.5936°, large
# enough to misplace any body within ~3° of an IAU constellation
# boundary.  We now import the canonical constant from the single
# source-of-truth sidereal config module.
# ---------------------------------------------------------------------------
from calculations.sidereal_config import SVP_DEGREES as _CANONICAL_SVP_OFFSET

# ---------------------------------------------------------------------------
# IAU ecliptic boundaries — tropical J2000 longitude ranges.
# Each entry: (constellation_name, start_longitude_deg, end_longitude_deg)
# Ranges are half-open [start, end). Pisces wraps around 360°.
# ---------------------------------------------------------------------------

IAU_ECLIPTIC_BOUNDARIES: List[Tuple[str, float, float]] = [
    # Pisces wraps around 0° — handled explicitly by lookup()
    ("Pisces",      351.57, 28.69),
    ("Aries",        28.69, 53.50),
    ("Taurus",       53.50, 90.44),
    ("Gemini",       90.44, 118.26),
    ("Cancer",      118.26, 138.19),
    ("Leo",         138.19, 173.95),
    ("Virgo",       173.95, 217.81),
    ("Libra",       217.81, 241.15),
    ("Scorpius",    241.15, 247.81),
    ("Ophiuchus",   247.81, 266.62),
    ("Sagittarius", 266.62, 299.71),
    ("Capricornus", 299.71, 327.88),
    ("Aquarius",    327.88, 351.57),
]

# Emoji / glyph hint per constellation — used only for UI flourish.
CONSTELLATION_GLYPHS: Dict[str, str] = {
    "Pisces":      "♓",
    "Aries":       "♈",
    "Taurus":      "♉",
    "Gemini":      "♊",
    "Cancer":      "♋",
    "Leo":         "♌",
    "Virgo":       "♍",
    "Libra":       "♎",
    "Scorpius":    "♏",
    "Ophiuchus":   "⛎",   # the IAU-assigned Ophiuchus glyph
    "Sagittarius": "♐",
    "Capricornus": "♑",
    "Aquarius":    "♒",
}

# ---------------------------------------------------------------------------
# Mirror-style overlay narrative — 5-section structure, BODY-AWARE.
#   RECOGNITION → TENSION → REALITY LAYER → HOW THIS SHOWS UP → THE SHIFT
#
# Each Ophiuchus body (Sun / Moon / Ascendant / Midheaven / Neptune / …) gets
# its OWN full 5-section narrative. Generic shared text is not allowed.
#
# Writing rules (see /app/memory/mirror_narrative_standard.md if it exists):
#   - RECOGNITION: one sharp sentence; immediate, personal, undeniable.
#   - TENSION: lived contradiction, not theoretical uncertainty.
#   - REALITY LAYER: fixed template — clean + factual. Do not expand.
#   - HOW THIS SHOWS UP: 3-5 observable, specific behaviours. No "feel
#     emotional" / "feel confused" style bullets.
#   - THE SHIFT: reframe, not advice. No "try to…" / "remember to…".
#
# Ophiuchus-specific cues: threshold, in-between, signal-without-proof,
# perception-without-confirmation, categories that don't quite hold.
# ---------------------------------------------------------------------------

BODY_NARRATIVE_PACKS: Dict[str, Dict[str, Any]] = {
    "Sun": {
        "recognition": (
            "Who you are keeps reforming itself, and you've stopped waiting "
            "for the final version."
        ),
        "tension": (
            "You can feel the shape of your identity clearly — but the moment "
            "you try to name it, something about the name stops being true."
        ),
        "how_this_shows_up": [
            "recognise yourself more clearly in contradictions than in categories",
            "notice that labels that used to describe you now describe a version of you that's gone",
            "feel most like yourself in the moments just after something ends",
            "get called intense by people who are only reading the surface",
            "resist bios and introductions that ask you to pick one version",
        ],
        "the_shift": (
            "The mistake isn't that you can't settle into a definition — it's "
            "assuming a self that regenerates was supposed to stay still enough "
            "to be framed."
        ),
    },
    "Moon": {
        "recognition": (
            "Your emotional weather isn't messy — it's carrying information "
            "you haven't been taught to read."
        ),
        "tension": (
            "You feel something strongly and sit with it, then watch other "
            "people treat the same moment like it barely registered."
        ),
        "how_this_shows_up": [
            "take longer than people expect to name what you're feeling",
            "sense grief or relief before the event everyone else is still reacting to",
            "absorb the emotional temperature of a room without being asked to",
            "come out of hard moments noticing you're calmer than you should be",
            "get told your response was disproportionate, and privately know it wasn't",
        ],
        "the_shift": (
            "The mistake isn't that your feelings are too much — it's "
            "expecting them to match the volume of whoever else is in the room."
        ),
    },
    "Mercury": {
        "recognition": (
            "You say the thing nobody has said yet, and then watch the room "
            "decide whether to admit it was already there."
        ),
        "tension": (
            "You're trying to stay accurate in conversations where accuracy "
            "costs something."
        ),
        "how_this_shows_up": [
            "find yourself naming what's been unsaid and watching people recalibrate",
            "hold back obvious observations because stating them would be read as cruel",
            "hear the question underneath the question and answer that one instead",
            "feel misread as indirect when you were actually being precise",
            "get thanked later for something that landed badly in the moment",
        ],
        "the_shift": (
            "The mistake isn't that you're too blunt or too careful — it's "
            "assuming precision is welcome everywhere it's needed."
        ),
    },
    "Venus": {
        "recognition": (
            "You're drawn to people who make you feel something you can't "
            "quite explain — and you've stopped pretending those are the "
            "safe ones."
        ),
        "tension": (
            "You value closeness that sees everything, but the closeness you "
            "actually get usually stops one layer short of that."
        ),
        "how_this_shows_up": [
            "feel more seen by someone in a single conversation than by people you've known for years",
            "find surface-level relationships tiring in ways you can't fully justify",
            "stay when others leave, and leave when others think you should stay",
            "want intensity and quiet in the same person and keep not finding both",
            "choose people who don't match your stated type, and be right about it",
        ],
        "the_shift": (
            "The mistake isn't that you keep choosing the wrong people — "
            "it's expecting someone who can meet you fully to also be uncomplicated."
        ),
    },
    "Mars": {
        "recognition": (
            "You act on something real, then second-guess whether it was real "
            "enough to act on."
        ),
        "tension": (
            "You can feel what needs to happen before you can prove it should — "
            "and you keep having to move anyway."
        ),
        "how_this_shows_up": [
            "move decisively in moments where others are still weighing options",
            "pull back at the last second because something felt off before it looked off",
            "find the gap between wanting something and claiming you want it embarrassing",
            "make choices that look impulsive and weren't",
            "get accused of overthinking by the same people who also call you reckless",
        ],
        "the_shift": (
            "The mistake isn't that your instinct is unreliable — it's "
            "expecting instinct to arrive with the paperwork attached."
        ),
    },
    "Jupiter": {
        "recognition": (
            "What you're learning isn't the lesson anyone's teaching, and you "
            "keep forgetting that's allowed."
        ),
        "tension": (
            "You keep trusting a bigger picture that hasn't shown up yet — "
            "and quietly doubting whether the trust is still doing anything."
        ),
        "how_this_shows_up": [
            "feel most at home in conversations nobody expected to have",
            "grow from what was supposed to break you, and only notice later",
            "resist the motivational version of your own story",
            "find meaning arriving without any of the usual signposts",
            "say something true that doesn't sound wise in the moment",
        ],
        "the_shift": (
            "The mistake isn't that your faith is fuzzy — it's expecting "
            "meaning to announce itself in the language you were trained to recognise."
        ),
    },
    "Saturn": {
        "recognition": (
            "You build things that hold, and then quietly question whether "
            "the thing you built is the thing you wanted."
        ),
        "tension": (
            "The rules you follow keep working, but the version of you that "
            "agreed to them doesn't quite exist anymore."
        ),
        "how_this_shows_up": [
            "honour commitments past the point they make sense",
            "carry other people's structure and call it your own stability",
            "feel responsible for holding frames that were never formally handed to you",
            "hit stretches where discipline stops feeling like virtue and starts feeling like a cage",
            "find it harder to rest than to keep going",
        ],
        "the_shift": (
            "The mistake isn't that you're too rigid or too loose — it's "
            "assuming the structure that made you was supposed to keep fitting "
            "the person it made."
        ),
    },
    "Uranus": {
        "recognition": (
            "You disrupt things that look stable, and the things you leave "
            "behind quietly admit later that they weren't."
        ),
        "tension": (
            "You trust the break more than the fix — and the trust has cost "
            "you people who needed you to stay."
        ),
        "how_this_shows_up": [
            "leave rooms at exactly the moment the room notices you're the one leaving",
            "see the crack in a system before anyone else is willing to name it",
            "get called unreliable by people who couldn't keep the pace",
            "feel relief during endings that are supposed to feel difficult",
            "find 'normal' genuinely harder to sustain than change",
        ],
        "the_shift": (
            "The mistake isn't that you can't stay — it's expecting 'stay' to "
            "mean the same thing for you as it does for people who weren't "
            "built to see the cracks."
        ),
    },
    "Neptune": {
        "recognition": (
            "You pick up on things that aren't said, then can't always tell "
            "if you picked up anything real."
        ),
        "tension": (
            "You're holding something real without proof that it's real — "
            "and you keep filing it under 'probably imagined' even when it isn't."
        ),
        "how_this_shows_up": [
            "sense shifts in people before anything is said",
            "feel misunderstood in subtle ways you can't quite explain",
            "mistrust your own perceptions even when they keep being right",
            "dissolve into other people's moods without meaning to",
            "feel clearer about other people's lives than about your own",
        ],
        "the_shift": (
            "The mistake isn't that you're wrong — it's expecting clarity to "
            "feel clean. What you're picking up doesn't come with proof attached."
        ),
    },
    "Pluto": {
        "recognition": (
            "The things that remade you are things most people never knew happened."
        ),
        "tension": (
            "You carry something private and heavy, and the weight is useful — "
            "but calling it useful is not the same as saying it's okay."
        ),
        "how_this_shows_up": [
            "hold the hardest material in a room without anyone asking you to",
            "find small talk strange with people who haven't been through anything unbearable",
            "recognise power dynamics most people don't see until they're trapped in them",
            "rebuild yourself from the inside and not talk about it",
            "feel the door between 'surface relationship' and 'real one' more clearly than most",
        ],
        "the_shift": (
            "The mistake isn't that you go too deep — it's expecting people "
            "who haven't had to, to meet you there."
        ),
    },
    "Chiron": {
        "recognition": (
            "You know exactly where the wound is — for yourself and for the "
            "people around you — and that knowing hasn't made it easier."
        ),
        "tension": (
            "You can do for others the thing you can't do for yourself, and "
            "the asymmetry doesn't get more comfortable with time."
        ),
        "how_this_shows_up": [
            "find strangers trusting you with things they haven't told their closest people",
            "carry a particular pain long enough that it's become a language",
            "hold space for what you can't yet offer yourself",
            "get asked to help in an area you're still actively bleeding in",
            "skip your own version of the conversation you just held for someone else",
        ],
        "the_shift": (
            "The mistake isn't that you haven't healed yet — it's assuming "
            "the usefulness of the wound and the resolution of the wound have "
            "to arrive in that order."
        ),
    },
    "North Node": {
        "recognition": (
            "The path forward keeps asking you to be seen as something you "
            "haven't verified about yourself yet."
        ),
        "tension": (
            "You're being asked to walk toward something that looks nothing "
            "like the person you were trained to become."
        ),
        "how_this_shows_up": [
            "circle situations that would require you to be believed in by yourself first",
            "feel pulled toward rooms that expose you more than you're used to",
            "resist the next step even when it keeps being obvious",
            "notice that the thing you're drawn to is the thing that would change you the most",
            "find the old path still open, and still not quite fitting",
        ],
        "the_shift": (
            "The mistake isn't that you can't take the next step — it's "
            "expecting the next step to feel familiar enough to be trusted."
        ),
    },
    "South Node": {
        "recognition": (
            "You keep returning to what you know how to do, even though the "
            "version of you that needed to do it is gone."
        ),
        "tension": (
            "The competence that once saved you now costs you — and setting "
            "it down doesn't feel like relief, it feels like losing a piece."
        ),
        "how_this_shows_up": [
            "catch yourself performing a strength that's no longer needed",
            "feel disloyal at the thought of stopping the thing that used to work",
            "return to old roles under stress even when they no longer fit",
            "mistake familiarity for necessity",
            "describe yourself using a past tense you're not actually done with",
        ],
        "the_shift": (
            "The mistake isn't that you can't let go — it's assuming what "
            "protected you still deserves to steer you."
        ),
    },
    "Ascendant": {
        "recognition": (
            "People read you before they meet you — and the read is almost "
            "never what you actually are."
        ),
        "tension": (
            "You keep adjusting who you are to whoever's in front of you, "
            "while quietly wondering which version is the real one."
        ),
        "how_this_shows_up": [
            "notice people treating you as someone you don't fully recognise",
            "feel slightly different in every room without meaning to",
            "get labelled with qualities you haven't chosen",
            "sense that first impressions of you carry more weight than most people's",
            "find yourself correcting assumptions about who you are more than you'd like",
        ],
        "the_shift": (
            "The mistake isn't that people keep misreading you — it's "
            "expecting a single, stable first impression from a self that "
            "forms at the threshold."
        ),
    },
    "Midheaven": {
        "recognition": (
            "The 'right path' keeps shifting every time you look at it — "
            "even though you're the one walking it."
        ),
        "tension": (
            "You can name what you don't want to be doing more easily than "
            "what you do — and the thing that fits keeps changing shape."
        ),
        "how_this_shows_up": [
            "recognise a wrong direction faster than a right one",
            "find that roles you grow into stop fitting once they're settled",
            "feel visible for things that don't match your internal sense of purpose",
            "resist being pinned to a single public identity",
            "sense that who you're becoming isn't what was expected of you",
        ],
        "the_shift": (
            "The mistake isn't that you can't find your direction — it's "
            "assuming your direction is supposed to be a fixed point rather "
            "than a moving one."
        ),
    },
}

# Generic fallback (same tone, same standard) for any body we haven't
# handcrafted. Still passes the quality bar: specific, lived, non-prescriptive.
GENERIC_BODY_NARRATIVE_PACK: Dict[str, Any] = {
    "recognition": (
        "{body} is doing something in you that keeps slipping through the "
        "usual categories."
    ),
    "tension": (
        "You can feel the signal clearly; the language for it hasn't caught "
        "up yet."
    ),
    "how_this_shows_up": [
        "notice the part of this that nobody else is naming",
        "carry information the moment hasn't caught up to yet",
        "hold contradictions that most descriptions flatten",
        "find existing frames useful but never quite sufficient",
    ],
    "the_shift": (
        "The mistake isn't that it doesn't fit — it's assuming the reason it "
        "doesn't fit is you."
    ),
}


def _reality_layer_text(body: str, zodiac_sign: str, constellation: str) -> str:
    return (
        f"In the symbolic system, this reads as {zodiac_sign}.\n"
        f"But in the actual sky, {body} is moving through {constellation} — "
        f"a region that doesn't follow the same clean boundaries."
    )


def _build_structured_narrative(
    overlay_bodies: Dict[str, Dict[str, Any]],
    ophiuchus_bodies: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Build the structured 5-section narrative payload for Ophiuchus
    placements. Returns None when there are no Ophiuchus bodies.

    Output shape:
      {
        "version": "mirror_narrative_v1",
        "items": [
          {
            "body": "Ascendant",
            "zodiac_sign": "Scorpio",
            "constellation": "Ophiuchus",
            "recognition": "...",
            "tension": "...",
            "reality_layer": "...",
            "how_this_shows_up": [...],
            "the_shift": "...",
          },
          ...
        ]
      }
    """
    if not ophiuchus_bodies:
        return None

    items: List[Dict[str, Any]] = []
    for body in ophiuchus_bodies:
        entry = overlay_bodies.get(body) or {}
        zodiac = entry.get("zodiac_sign") or "its 12-sign position"
        pack = BODY_NARRATIVE_PACKS.get(body)
        if pack is None:
            pack = {
                "recognition": GENERIC_BODY_NARRATIVE_PACK["recognition"].format(body=body),
                "tension": GENERIC_BODY_NARRATIVE_PACK["tension"],
                "how_this_shows_up": list(GENERIC_BODY_NARRATIVE_PACK["how_this_shows_up"]),
                "the_shift": GENERIC_BODY_NARRATIVE_PACK["the_shift"],
            }

        items.append(
            {
                "body": body,
                "zodiac_sign": zodiac,
                "constellation": "Ophiuchus",
                "recognition": pack["recognition"],
                "tension": pack["tension"],
                "reality_layer": _reality_layer_text(body, zodiac, "Ophiuchus"),
                "how_this_shows_up": list(pack["how_this_shows_up"]),
                "the_shift": pack["the_shift"],
            }
        )

    return {"version": "mirror_narrative_v1", "items": items}


def _legacy_narrative_from_structured(structured: Dict[str, Any]) -> str:
    """
    Flatten the structured narrative into a plain-text form for older
    clients that only know about `overlay_narrative` (string).
    """
    chunks: List[str] = []
    for idx, item in enumerate(structured.get("items", [])):
        if idx > 0:
            chunks.append("")
            chunks.append("---")
            chunks.append("")
        chunks += [
            f"### {item['body']} IN OPHIUCHUS",
            "",
            "### RECOGNITION",
            item["recognition"],
            "",
            "### TENSION",
            item["tension"],
            "",
            "### REALITY LAYER",
            item["reality_layer"],
            "",
            "### HOW THIS SHOWS UP",
            *[f"- {b}" for b in item["how_this_shows_up"]],
            "",
            "### THE SHIFT",
            item["the_shift"],
        ]
    return "\n".join(chunks).strip()


# Kept only so any legacy imports don't break.
OPHIUCHUS_BODY_NARRATIVES: Dict[str, str] = {}
GENERIC_OPHIUCHUS_NARRATIVE = ""


# ---------------------------------------------------------------------------
# Core lookup
# ---------------------------------------------------------------------------

def _normalize_360(lon: float) -> float:
    x = lon % 360.0
    return x + 360.0 if x < 0 else x


def lookup_constellation(tropical_longitude: float) -> str:
    """
    Map a tropical J2000 ecliptic longitude (0-360°) to one of the 13 IAU
    constellations the ecliptic crosses.

    Pisces wraps around 0° (351.57° → 28.69°). All other ranges are
    contiguous half-open [start, end).
    """
    lon = _normalize_360(tropical_longitude)

    # Pisces wrap
    if lon >= 351.57 or lon < 28.69:
        return "Pisces"

    for name, start, end in IAU_ECLIPTIC_BOUNDARIES:
        if name == "Pisces":
            continue
        if start <= lon < end:
            return name

    # Fallback — should never happen if boundaries sum to 360°
    return "Pisces"


def glyph_for(constellation: str) -> str:
    return CONSTELLATION_GLYPHS.get(constellation, "")


# ---------------------------------------------------------------------------
# Chart-level resolution
# ---------------------------------------------------------------------------

def resolve_constellation_overlay(astrology_chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given Mirror's existing astrology chart dict, compute the IAU
    constellation overlay. Does NOT mutate the input. Returns a dict shaped:

    {
        "version": "iau_1930_v1",
        "bodies": {                       # per-body mapping
            "Sun":       {"constellation": "Pisces",    "glyph": "♓", "zodiac_sign": "Pisces",  "divergent": false, ...},
            "Moon":      {"constellation": "Ophiuchus", "glyph": "⛎", "zodiac_sign": "Sagittarius", "divergent": true, ...},
            ...
        },
        "summary": {
            "sun_constellation": "...",
            "moon_constellation": "...",
            "ascendant_constellation": "...",
            "mc_constellation": "...",
        },
        "ophiuchus_bodies": ["Moon", "Mercury", ...],
        "has_ophiuchus": bool,
        "overlay_narrative": "...",       # only populated when has_ophiuchus
    }

    Accepts several possible input shapes (chart may come from canonical
    astronomy OR the legacy shape stored on the user document), so we try a
    few field names for each body.
    """
    overlay: Dict[str, Any] = {
        "version": "iau_1930_v1",
        "bodies": {},
        "summary": {},
        "ophiuchus_bodies": [],
        "has_ophiuchus": False,
        "overlay_narrative": None,
    }

    if not astrology_chart or not isinstance(astrology_chart, dict):
        return overlay

    # Extract planet longitudes — prefer tropical, fall back to sidereal.
    # Mirror stores them under several aliases depending on age of chart.
    planets = (
        astrology_chart.get("planets")
        or astrology_chart.get("natal", {}).get("planets")
        or {}
    )
    angles = (
        astrology_chart.get("angles")
        or astrology_chart.get("natal", {}).get("angles")
        or {}
    )
    nodes = (
        astrology_chart.get("nodes")
        or astrology_chart.get("natal", {}).get("nodes")
        or {}
    )

    # Compile a unified (name, tropical_lon, sidereal_sign) iterable.
    body_records: List[Tuple[str, float, Optional[str]]] = []

    def _extract(name: str, entry: Any) -> Optional[Tuple[float, Optional[str]]]:
        if entry is None:
            return None
        if isinstance(entry, dict):
            lon = (
                entry.get("tropical_longitude")
                or entry.get("tropical_lon")
                or entry.get("longitude_tropical")
                # If only sidereal is stored, reconstruct tropical using
                # the canonical SVP offset (angle-staleness-step1-v1).
                # Pre-remediation this used a literal `28.69` which was
                # ~2.59° off from canonical SVP=31.2836 and could
                # misplace bodies at constellation boundaries.
                or (
                    (entry.get("longitude") or entry.get("sidereal_longitude"))
                    + _CANONICAL_SVP_OFFSET
                    if (entry.get("longitude") is not None
                        or entry.get("sidereal_longitude") is not None)
                    else None
                )
            )
            sign = entry.get("sign") or entry.get("sidereal_sign")
            if lon is None:
                return None
            return (float(lon), sign)
        if isinstance(entry, (int, float)):
            return (float(entry) + _CANONICAL_SVP_OFFSET, None)
        return None

    for name, entry in (planets or {}).items():
        rec = _extract(name, entry)
        if rec:
            body_records.append((name, rec[0], rec[1]))

    for name, entry in (nodes or {}).items():
        # normalize "North Node" / "south_node" naming
        canonical_name = name.replace("_", " ").title()
        if canonical_name == "North Node" or canonical_name == "South Node":
            pass
        rec = _extract(canonical_name, entry)
        if rec:
            body_records.append((canonical_name, rec[0], rec[1]))

    # Angles (Ascendant + Midheaven) — allow many shapes
    def _angle(key_variants: List[str]) -> Optional[Tuple[float, Optional[str]]]:
        for k in key_variants:
            v = angles.get(k) if isinstance(angles, dict) else None
            if isinstance(v, dict):
                lon = (
                    v.get("tropical_longitude")
                    or v.get("tropical_lon")
                    or (
                        (v.get("longitude") or v.get("sidereal_longitude")) + _CANONICAL_SVP_OFFSET
                        if v.get("longitude") is not None
                        or v.get("sidereal_longitude") is not None
                        else None
                    )
                )
                sign = v.get("sign") or v.get("sidereal_sign")
                if lon is not None:
                    return (float(lon), sign)
            elif isinstance(v, (int, float)):
                return (float(v) + _CANONICAL_SVP_OFFSET, None)
        return None

    asc_rec = _angle(["asc", "Ascendant", "ascendant", "ASC"])
    mc_rec = _angle(["mc", "Midheaven", "midheaven", "MC"])
    if asc_rec is not None:
        body_records.append(("Ascendant", asc_rec[0], asc_rec[1]))
    if mc_rec is not None:
        body_records.append(("Midheaven", mc_rec[0], mc_rec[1]))

    ophiuchus_bodies: List[str] = []

    for name, lon, sidereal_sign in body_records:
        constellation = lookup_constellation(lon)
        divergent = (
            sidereal_sign is not None
            and constellation != sidereal_sign
        )
        overlay["bodies"][name] = {
            "constellation": constellation,
            "glyph": glyph_for(constellation),
            "zodiac_sign": sidereal_sign,
            "divergent": bool(divergent),
            "tropical_longitude": round(_normalize_360(lon), 3),
        }
        if constellation == "Ophiuchus":
            ophiuchus_bodies.append(name)

    # Summary shorthand — the 4 most-requested points
    sun = overlay["bodies"].get("Sun") or {}
    moon = overlay["bodies"].get("Moon") or {}
    asc = overlay["bodies"].get("Ascendant") or {}
    mc = overlay["bodies"].get("Midheaven") or {}
    overlay["summary"] = {
        "sun_constellation": sun.get("constellation"),
        "moon_constellation": moon.get("constellation"),
        "ascendant_constellation": asc.get("constellation"),
        "mc_constellation": mc.get("constellation"),
    }

    overlay["ophiuchus_bodies"] = ophiuchus_bodies
    overlay["has_ophiuchus"] = bool(ophiuchus_bodies)

    if ophiuchus_bodies:
        structured = _build_structured_narrative(overlay["bodies"], ophiuchus_bodies)
        overlay["overlay_narrative_v2"] = structured
        overlay["overlay_narrative"] = _legacy_narrative_from_structured(structured)
    else:
        overlay["overlay_narrative_v2"] = None
        overlay["overlay_narrative"] = None

    return overlay


# ---------------------------------------------------------------------------
# Self-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick boundary sanity check — Scorpius -> Ophiuchus -> Sagittarius band
    for lon in [220, 240, 244, 248, 255, 266, 270, 300, 330, 355, 5, 30]:
        print(f"{lon:6.1f}° tropical  ->  {lookup_constellation(lon)}")
