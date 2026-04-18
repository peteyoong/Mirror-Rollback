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
# Mirror-style overlay narratives. Kept concise: 2-3 lines per body when
# the placement falls in Ophiuchus (the "hidden" zodiacal constellation),
# or in Scorpius (which shrinks dramatically under the IAU boundaries).
# For the other 11 constellations the overlay is identical to the zodiac
# sign most of the time, so we only surface a narrative when it diverges.
# ---------------------------------------------------------------------------

OPHIUCHUS_BODY_NARRATIVES: Dict[str, str] = {
    "Sun": (
        "If we look at the sky directly, your Sun is currently passing through "
        "Ophiuchus — the serpent-bearer. This adds a layer of transformation-"
        "through-healing to your core identity: the part of you that rebuilds "
        "itself after shedding something."
    ),
    "Moon": (
        "Your Moon passes through Ophiuchus when we read the sky as it actually "
        "is. Emotionally, this tends to show up as a pull toward depth work, "
        "hidden material, and the kind of intimacy that involves watching "
        "something die and something else begin."
    ),
    "Mercury": (
        "Mercury in Ophiuchus — how you think and speak carries a healer's "
        "cadence. You're wired to ask the question everyone else is avoiding; "
        "that's a gift when it's invited, and an intrusion when it's not."
    ),
    "Venus": (
        "Venus in Ophiuchus — you're drawn to love that metabolises something. "
        "The relationships that actually hold you are the ones where both "
        "people have already seen each other at their rawest."
    ),
    "Mars": (
        "Mars in Ophiuchus — the way you act on desire is serpentine: patient, "
        "precise, occasionally ruthless. You don't strike unless the moment is "
        "ripe, and when you do, something transforms."
    ),
    "Jupiter": (
        "Jupiter in Ophiuchus — growth comes through what you're willing to "
        "heal or witness heal. The classroom isn't a book; it's the room where "
        "something is actually being released."
    ),
    "Saturn": (
        "Saturn in Ophiuchus — the structures you build are ones that hold "
        "other people's weight. Mastery here is knowing when to carry, when to "
        "teach, and when to put the load back down."
    ),
    "Uranus": (
        "Uranus in Ophiuchus — your rebellion is against inherited pain. You "
        "don't just disrupt for disruption's sake; you break the patterns that "
        "were quietly running the family, the team, the relationship."
    ),
    "Neptune": (
        "Neptune in Ophiuchus — your imagination is a healing chamber. What "
        "you dream up, others get to walk through. Be mindful of who you invite."
    ),
    "Pluto": (
        "Pluto in Ophiuchus — the deep-rebirth work of your life involves "
        "someone else's wound as much as your own. You are built to go into "
        "the underworld and come back with something useful."
    ),
    "Chiron": (
        "Chiron in Ophiuchus — doubly written as a wounded healer. The wound "
        "is real. The capacity to help others is also real. They share a root."
    ),
    "North Node": (
        "North Node in Ophiuchus — your growth edge is learning to stay in "
        "rooms where real healing happens, even when it's uncomfortable, "
        "instead of routing around them."
    ),
    "Ascendant": (
        "Ascendant in Ophiuchus — people often sense you've already been "
        "through something. The first impression you leave is depth, not "
        "brightness — and that opens some doors while closing others."
    ),
    "Midheaven": (
        "Midheaven in Ophiuchus — in the world, you're recognized for depth "
        "work: roles that involve witnessing, holding, or transforming "
        "something hidden."
    ),
}

# Generic fallback (used for minor bodies or when we don't have a specific line)
GENERIC_OPHIUCHUS_NARRATIVE = (
    "Passing through Ophiuchus when we read the sky directly — this placement "
    "carries an undercurrent of transformation-through-witnessing. It isn't a "
    "13th sign; it's a reminder that the sky has more texture than any 12-fold "
    "model can hold."
)


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
                # if only sidereal is stored, reconstruct approximate tropical
                # using the canonical SVP offset — good enough for boundary
                # lookup (the IAU boundaries are not tight to sub-degree).
                or (
                    (entry.get("longitude") or entry.get("sidereal_longitude"))
                    + 28.69
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
            return (float(entry) + 28.69, None)
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
    def _angle_lon(key_variants: List[str]) -> Optional[float]:
        for k in key_variants:
            v = angles.get(k) if isinstance(angles, dict) else None
            if isinstance(v, dict):
                lon = (
                    v.get("tropical_longitude")
                    or v.get("tropical_lon")
                    or (
                        (v.get("longitude") or v.get("sidereal_longitude")) + 28.69
                        if v.get("longitude") is not None
                        or v.get("sidereal_longitude") is not None
                        else None
                    )
                )
                if lon is not None:
                    return float(lon)
            elif isinstance(v, (int, float)):
                return float(v) + 28.69
        return None

    asc_lon = _angle_lon(["Ascendant", "ascendant", "ASC", "asc"])
    mc_lon = _angle_lon(["Midheaven", "midheaven", "MC", "mc"])
    if asc_lon is not None:
        body_records.append(("Ascendant", asc_lon, None))
    if mc_lon is not None:
        body_records.append(("Midheaven", mc_lon, None))

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
        narrative_lines: List[str] = []
        for body in ophiuchus_bodies:
            line = OPHIUCHUS_BODY_NARRATIVES.get(body, GENERIC_OPHIUCHUS_NARRATIVE)
            # Templates for known bodies already start with "<Body> in Ophiuchus"
            # (except Sun/Moon/Ascendant/Midheaven which use a slightly different
            # opening). For unknown bodies we prepend a bold header.
            has_inline_header = (
                line.lower().startswith(f"{body.lower()} in ophiuchus")
                or body in ("Sun", "Moon", "Ascendant", "Midheaven")
            )
            if has_inline_header:
                narrative_lines.append(line)
            else:
                narrative_lines.append(f"**{body} in Ophiuchus** — {line}")

        preamble = (
            "Every Mirror chart is computed using the 12-sign True Sidereal "
            "system. What follows is an *additional* sky-view observation: "
            "where these bodies actually fall against the IAU constellation "
            "boundaries — which include Ophiuchus, the serpent-bearer, "
            "between Scorpius and Sagittarius.\n\n"
            "Ophiuchus is not a 13th sign. It's a constellation the ecliptic "
            "crosses, and seeing it named can add texture to a placement you "
            "already know in the 12-sign frame."
        )
        overlay["overlay_narrative"] = preamble + "\n\n" + "\n\n".join(narrative_lines)

    return overlay


# ---------------------------------------------------------------------------
# Self-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick boundary sanity check — Scorpius -> Ophiuchus -> Sagittarius band
    for lon in [220, 240, 244, 248, 255, 266, 270, 300, 330, 355, 5, 30]:
        print(f"{lon:6.1f}° tropical  ->  {lookup_constellation(lon)}")
