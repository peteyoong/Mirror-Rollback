"""
Parallel forensic module — 13-sign True Sidereal Midpoint boundaries.
=====================================================================
Build marker: ``midpoint13-forensic-module-v1``  (2026-06-07)

PURPOSE
-------
A/B comparison layer ONLY. This module is **NOT wired into production**.
Mirror's live sign attribution remains:

    services / lens / today / chat   ──>   calculations/sign_attribution.py
                                            (Variant B — 12 signs, Ophiuchus
                                             merged into Scorpius, tropical
                                             boundary table)

This module exposes the **13-sign Athen / Mastering-the-Zodiac midpoint
table** so we can compute what a chart *would* look like under the
alternative model without changing any stored chart, any interpretation
copy, or any runtime sign label.

RULES
-----
* No production codepath imports this module's helpers.
* No chart math is mutated.
* No DB writes.
* No interpretation content for Ophiuchus is added.
* Pure data + read-only helpers + comparison function.

If/when product decides to migrate to the 13-sign model, this module is
the canonical source of truth for the new boundary table. Until then it
is forensic-only.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

BUILD_MARKER = "midpoint13-forensic-module-v1"

# ---------------------------------------------------------------------------
# 13-sign midpoint boundary table — operates on the **zodiacal** longitude,
# i.e. (tropical_longitude − ARIES_BOUNDARY_OFFSET) mod 360.
# ---------------------------------------------------------------------------
TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13: Dict[str, tuple[float, float]] = {
    "Aries":       (0.0,      19.7286),
    "Taurus":      (19.7286,  56.5875),
    "Gemini":      (56.5875,  86.0412),
    "Cancer":      (86.0412,  103.19),
    "Leo":         (103.19,   141.6065),
    "Virgo":       (141.6065, 191.32),
    "Libra":       (191.32,   210.1972),
    "Scorpio":     (210.1972, 223.4245),
    "Ophiuchus":   (223.4245, 235.7818),
    "Sagittarius": (235.7818, 269.2677),
    "Capricorn":   (269.2677, 294.8435),
    "Aquarius":    (294.8435, 318.0103),
    "Pisces":      (318.0103, 360.0),
}

# Offset between tropical longitude and the proposed 13-sign zodiacal
# coordinate system. Equals Mirror's SVP (Sharatan / β-Arietis at J2000),
# i.e. tropical 0° Aries is 31.2836° earlier than the 13-sign Aries boundary.
ARIES_BOUNDARY_OFFSET: float = 31.2836

# Anything within this many degrees of a boundary is flagged for human review.
TRANSITION_ZONE_DEGREES: float = 3.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_sign_for_zodiacal_degree(zodiacal_degree: float) -> tuple[str, float, float]:
    """Look up the sign band containing ``zodiacal_degree`` in [0, 360).

    Returns (sign, boundary_start, boundary_end). Raises ValueError if the
    input is out of range — callers normalise via ``% 360`` first.
    """
    if not (0.0 <= zodiacal_degree < 360.0):
        raise ValueError(f"zodiacal_degree out of [0,360): {zodiacal_degree!r}")
    for sign, (lo, hi) in TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13.items():
        if lo <= zodiacal_degree < hi:
            return sign, lo, hi
    # Defensive: Pisces high bound is 360.0 (exclusive). 359.999… still hits
    # the loop above. If we get here something is malformed.
    raise RuntimeError(f"no band matched zodiacal_degree={zodiacal_degree!r}")


def _nearest_boundary_distance(zodiacal_degree: float, lo: float, hi: float) -> float:
    """Smaller of (degree − lo) and (hi − degree). Handles the wrap at
    Pisces→Aries by checking against 0.0 / 360.0 as well."""
    candidates = [
        abs(zodiacal_degree - lo),
        abs(hi - zodiacal_degree),
    ]
    # Wrap-around for the Pisces-Aries seam
    if lo == 0.0 or hi == 360.0:
        candidates.append(abs((zodiacal_degree % 360.0) - 0.0))
        candidates.append(abs(360.0 - zodiacal_degree))
    return min(candidates)


def midpoint_13_sign_from_tropical_longitude(tropical_longitude: float) -> Dict[str, Any]:
    """Compute the 13-sign midpoint sign for a tropical ecliptic longitude.

    Returns a dict with:
        sign                       — one of the 13 sign names
        zodiacal_degree            — tropical − ARIES_BOUNDARY_OFFSET mod 360
        degree_in_sign             — zodiacal_degree − boundary_start
        boundary_start             — band lower bound
        boundary_end               — band upper bound
        within_transition_zone     — True iff |distance| < TRANSITION_ZONE_DEGREES
        distance_to_nearest_boundary — minimum arc distance to any boundary
    """
    trop = float(tropical_longitude) % 360.0
    zodiacal_degree = (trop - ARIES_BOUNDARY_OFFSET) % 360.0

    sign, lo, hi = _resolve_sign_for_zodiacal_degree(zodiacal_degree)
    nearest = _nearest_boundary_distance(zodiacal_degree, lo, hi)
    within_tz = nearest < TRANSITION_ZONE_DEGREES

    return {
        "sign":                          sign,
        "zodiacal_degree":               round(zodiacal_degree, 4),
        "degree_in_sign":                round(zodiacal_degree - lo, 4),
        "boundary_start":                lo,
        "boundary_end":                  hi,
        "within_transition_zone":        within_tz,
        "distance_to_nearest_boundary":  round(nearest, 4),
    }


def compare_current_vs_midpoint13(tropical_longitude: float) -> Dict[str, Any]:
    """Compute both Mirror-current and 13-sign labels for the same longitude.

    Does NOT mutate any production state. Reads ``calculations.sign_attribution``
    in production-default mode (True Sidereal-M Midpoint, Variant B).
    """
    # Local import to keep this module side-effect free
    from calculations.sign_attribution import (
        attribute_sign, MODE_TRUE_SIDEREAL_MIDPOINT,
    )

    current = attribute_sign(tropical_longitude, mode=MODE_TRUE_SIDEREAL_MIDPOINT)
    proposed = midpoint_13_sign_from_tropical_longitude(tropical_longitude)

    return {
        "tropical_longitude":     round(float(tropical_longitude) % 360.0, 4),
        "current_sign":           current.get("sign"),
        "current_degree":         current.get("degree_in_sign"),
        "midpoint13_sign":        proposed["sign"],
        "midpoint13_degree":      proposed["degree_in_sign"],
        "match":                  current.get("sign") == proposed["sign"],
        "midpoint13_is_ophiuchus":proposed["sign"] == "Ophiuchus",
        "transition_zone":        proposed["within_transition_zone"],
        "nearest_boundary_dist":  proposed["distance_to_nearest_boundary"],
    }


__all__ = [
    "BUILD_MARKER",
    "TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13",
    "ARIES_BOUNDARY_OFFSET",
    "TRANSITION_ZONE_DEGREES",
    "midpoint_13_sign_from_tropical_longitude",
    "compare_current_vs_midpoint13",
]
