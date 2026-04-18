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
# Mirror-style overlay narrative — 5-section structure.
#   RECOGNITION → TENSION → REALITY LAYER → HOW THIS SHOWS UP → THE SHIFT
#
# Sections 1, 2, 4, 5 are body-agnostic (same wording regardless of which
# body falls in Ophiuchus). Section 3 ("REALITY LAYER") is templated per
# body and uses {zodiac_sign}, {body}, {constellation}.
#
# When multiple bodies fall in Ophiuchus we render the shared sections once
# and stack a REALITY LAYER block per body.
# ---------------------------------------------------------------------------

NARRATIVE_RECOGNITION = (
    "There's a part of you that doesn't sit cleanly inside the way you're "
    "usually described."
)

NARRATIVE_TENSION = (
    "Even when something \"fits\" on paper, your actual experience of it "
    "can feel different — harder to name, harder to stabilize, or slightly "
    "off from what you expect."
)

NARRATIVE_REALITY_LAYER_TEMPLATE = (
    "In the symbolic system, this reads as {zodiac_sign}.\n"
    "But in the actual sky, {body} is moving through {constellation} — a "
    "region that doesn't follow the same clean boundaries."
)

NARRATIVE_HOW_THIS_SHOWS_UP = [
    "feel something strongly but struggle to define exactly what it is",
    "move toward something, then question whether you're reading it right",
    "sense that there's more going on beneath the surface than you can "
    "fully articulate",
]

NARRATIVE_THE_SHIFT = (
    "This isn't confusion to fix — it's a signal that your instinct is "
    "picking up more than the model can fully explain."
)


def _build_structured_narrative(
    overlay_bodies: Dict[str, Dict[str, Any]],
    ophiuchus_bodies: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Build the structured 5-section narrative payload for Ophiuchus
    placements. Returns None when there are no Ophiuchus bodies.
    """
    if not ophiuchus_bodies:
        return None

    reality_layers: List[Dict[str, str]] = []
    for body in ophiuchus_bodies:
        entry = overlay_bodies.get(body) or {}
        zodiac = entry.get("zodiac_sign") or "its 12-sign position"
        reality_layers.append(
            {
                "body": body,
                "zodiac_sign": zodiac,
                "constellation": "Ophiuchus",
                "text": NARRATIVE_REALITY_LAYER_TEMPLATE.format(
                    zodiac_sign=zodiac,
                    body=body,
                    constellation="Ophiuchus",
                ),
            }
        )

    return {
        "recognition": NARRATIVE_RECOGNITION,
        "tension": NARRATIVE_TENSION,
        "reality_layers": reality_layers,
        "how_this_shows_up": list(NARRATIVE_HOW_THIS_SHOWS_UP),
        "the_shift": NARRATIVE_THE_SHIFT,
    }


def _legacy_narrative_from_structured(structured: Dict[str, Any]) -> str:
    """
    Flatten the structured narrative into a plain-text form for older
    clients that only know about `overlay_narrative` (string).
    """
    lines: List[str] = [
        "### RECOGNITION",
        structured["recognition"],
        "",
        "### TENSION",
        structured["tension"],
        "",
        "### REALITY LAYER",
    ]
    for rl in structured["reality_layers"]:
        lines.append(rl["text"])
        lines.append("")
    lines += [
        "### HOW THIS SHOWS UP",
        *[f"- {b}" for b in structured["how_this_shows_up"]],
        "",
        "### THE SHIFT",
        structured["the_shift"],
    ]
    return "\n".join(lines).strip()


# Kept as a safety net for places that previously imported these constants.
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
    def _angle(key_variants: List[str]) -> Optional[Tuple[float, Optional[str]]]:
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
                sign = v.get("sign") or v.get("sidereal_sign")
                if lon is not None:
                    return (float(lon), sign)
            elif isinstance(v, (int, float)):
                return (float(v) + 28.69, None)
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
