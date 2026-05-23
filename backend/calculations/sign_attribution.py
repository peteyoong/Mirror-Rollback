"""
Sign Attribution — Mode Router
==============================
Build marker: true-sidereal-midpoint-toggle-v1

Pure functions for mapping a tropical longitude to a (sign, degree) pair
under two distinct sign-attribution modes:

  uniform_30:
      Mirror's current production behaviour. Subtract SVP=31.2836 and
      assign 30° equal signs starting at sidereal 0° Aries.

  true_sidereal_midpoint (Variant B, Ophiuchus merged into Scorpius):
      Genetic Matrix candidate. Non-uniform sign boundaries fixed at
      the midpoints between consecutive IAU constellation centers,
      with Ophiuchus merged into Scorpius. SVP is NOT used here —
      attribution is performed directly on the tropical longitude.

NEITHER function mutates state. They are pure mappings.

The default mode is `uniform_30` (production parity). Nothing in this
module changes existing behaviour unless callers explicitly opt into
`true_sidereal_midpoint`.

Functions:
    attribute_sign_uniform_30(tropical_longitude, ayanamsa=31.2836)
    attribute_sign_true_sidereal_midpoint(tropical_longitude)
    attribute_sign(tropical_longitude, mode="uniform_30", ayanamsa=31.2836)

Return shape (both modes):
    {
        "sign":              str,    # "Aries" ... "Pisces"
        "degree_within_sign": float,
        "sign_start":        float,  # tropical longitude where sign starts
        "sign_end":          float,  # tropical longitude where sign ends
        "sign_width":        float,
        "attribution_mode":  str,    # "uniform_30" | "true_sidereal_midpoint_12_merged_candidate"
    }
"""
from __future__ import annotations

from typing import Dict, List, Tuple

BUILD_MARKER = "true-sidereal-midpoint-toggle-v1"

# Mode constants (the public API)
MODE_UNIFORM_30 = "uniform_30"
MODE_TRUE_SIDEREAL_MIDPOINT = "true_sidereal_midpoint"
DEFAULT_MODE = MODE_UNIFORM_30

# Internal label exposed in debug output so consumers can disambiguate
# variants if/when we ship Variant A (Ophiuchus dropped).
MIDPOINT_MODEL_NAME = "true_sidereal_midpoint_12_merged_candidate"

DEFAULT_AYANAMSA = 31.2836  # Sharatan (β Arietis) anchored SVP

SIGNS_12 = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# -----------------------------------------------------------------------------
# True Sidereal-M Midpoint boundary table (Variant B — Ophiuchus merged into
# Scorpius). Each entry: (sign_name, start_tropical°, end_tropical°).
# These boundaries were derived as midpoints between consecutive IAU
# constellation ecliptic-projection centers (Delporte 1930, projected at
# J2000), with Ophiuchus's range absorbed into Scorpius.
#
# Verified against Mel / Ana / Pete in the genetic-matrix-reconciliation
# round — the only entry that wraps the 0° point is Pisces.
# -----------------------------------------------------------------------------
MIDPOINT_BOUNDARIES: List[Tuple[str, float, float]] = [
    ("Aries",        25.61,  56.53),
    ("Taurus",       56.53,  88.16),
    ("Gemini",       88.16, 116.29),
    ("Cancer",      116.29, 142.15),
    ("Leo",         142.15, 175.97),
    ("Virgo",       175.97, 212.68),
    ("Libra",       212.68, 241.68),
    ("Scorpio",     241.68, 268.52),
    ("Sagittarius", 268.52, 298.48),
    ("Capricorn",   298.48, 326.76),
    ("Aquarius",    326.76, 354.93),
    ("Pisces",      354.93,  25.61),   # wraps through 0° Aries tropical
]


def _norm(lng: float) -> float:
    """Normalise to [0, 360)."""
    return lng % 360.0


def attribute_sign_uniform_30(
    tropical_longitude: float,
    ayanamsa: float = DEFAULT_AYANAMSA,
) -> Dict[str, float]:
    """Mirror's current default: subtract ayanamsa, 30° equal signs.

    This is the production behaviour. Do not change without changing the
    production default explicitly.
    """
    trop = _norm(tropical_longitude)
    sidereal = _norm(trop - ayanamsa)
    idx = int(sidereal // 30) % 12
    deg = sidereal - 30.0 * idx
    sign_start_sidereal = 30.0 * idx
    sign_end_sidereal = sign_start_sidereal + 30.0
    # Express sign_start/end in TROPICAL frame for cross-mode comparability
    sign_start_trop = _norm(sign_start_sidereal + ayanamsa)
    sign_end_trop = _norm(sign_end_sidereal + ayanamsa)
    return {
        "sign":               SIGNS_12[idx],
        "degree_within_sign": round(deg, 6),
        "sign_start":         round(sign_start_trop, 6),
        "sign_end":           round(sign_end_trop, 6),
        "sign_width":         30.0,
        "attribution_mode":   MODE_UNIFORM_30,
    }


def attribute_sign_true_sidereal_midpoint(
    tropical_longitude: float,
) -> Dict[str, float]:
    """Genetic Matrix candidate: non-uniform sign boundaries at IAU
    constellation midpoints, with Ophiuchus merged into Scorpius.

    Attribution operates directly on the tropical longitude — the SVP /
    ayanamsa is NOT subtracted here because the boundary table is
    already expressed in tropical frame.
    """
    trop = _norm(tropical_longitude)
    for name, start, end in MIDPOINT_BOUNDARIES:
        if start <= end:
            if start <= trop < end:
                width = end - start
                return {
                    "sign":               name,
                    "degree_within_sign": round(trop - start, 6),
                    "sign_start":         round(start, 6),
                    "sign_end":           round(end, 6),
                    "sign_width":         round(width, 6),
                    "attribution_mode":   MIDPOINT_MODEL_NAME,
                }
        else:
            # Pisces wraps the 0° point.
            if trop >= start or trop < end:
                width = (360.0 - start) + end
                deg = (trop - start) % 360.0
                return {
                    "sign":               name,
                    "degree_within_sign": round(deg, 6),
                    "sign_start":         round(start, 6),
                    "sign_end":           round(end, 6),
                    "sign_width":         round(width, 6),
                    "attribution_mode":   MIDPOINT_MODEL_NAME,
                }
    # Should be unreachable — the table tiles [0, 360) exactly.
    raise ValueError(f"Sign attribution failed for tropical_longitude={tropical_longitude}")


def attribute_sign(
    tropical_longitude: float,
    mode: str = DEFAULT_MODE,
    ayanamsa: float = DEFAULT_AYANAMSA,
) -> Dict[str, float]:
    """Router. Default mode preserves production behaviour."""
    if mode == MODE_TRUE_SIDEREAL_MIDPOINT:
        return attribute_sign_true_sidereal_midpoint(tropical_longitude)
    # Default + any unknown mode → uniform_30
    return attribute_sign_uniform_30(tropical_longitude, ayanamsa=ayanamsa)
