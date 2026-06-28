"""
Sign Attribution — Mode Router (Variant A canonical + Variant B forensic)
=========================================================================
Build marker: midpoint13-variant-a-canonical-v1   (2026-02-XX)

This is the single source of truth for sign attribution under Project Mirror.

ENGINE VERSIONS (versioned so every chart output is self-describing):
  - midpoint13_variant_a_v1   (CANONICAL — production default)
        True Sidereal-M Midpoint, 13 signs, Ophiuchus as a first-class
        sign sitting between Scorpio and Sagittarius. Boundaries derived
        from the Athen / Mastering-the-Zodiac midpoint table at SVP=
        31.2836° (J2000 reference, yearly_increment=0).

  - midpoint12_variant_b      (LEGACY / FORENSIC ROLLBACK)
        True Sidereal-M Midpoint, 12 signs, Ophiuchus merged into Scorpio.
        Retained for forensic audit + rollback only. Never the default.

  - uniform_30                (DEPRECATED)
        Mirror's original behaviour. Subtract SVP=31.2836° and assign
        equal 30° signs. Retained for back-compat only.

NEITHER function mutates state. They are pure mappings.

The default mode is `midpoint13_variant_a` (production). Variant B remains
fully callable so rollback / forensic comparisons work without churn.

Public API:
    attribute_sign_uniform_30(tropical_longitude, ayanamsa=31.2836)
    attribute_sign_midpoint12_variant_b(tropical_longitude)
    attribute_sign_midpoint13_variant_a(tropical_longitude)
    attribute_sign(tropical_longitude, mode=DEFAULT_MODE, ayanamsa=31.2836)

Return shape (all modes):
    {
        "sign":               str,
        "degree_within_sign": float,
        "sign_start":         float,
        "sign_end":           float,
        "sign_width":         float,
        "attribution_mode":   str,
        "engine_version":     str,    # midpoint13_variant_a_v1 etc.
    }
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# BUILD / VERSION MARKERS
# ---------------------------------------------------------------------------
BUILD_MARKER = "midpoint13-variant-a-canonical-v1"

# Engine version strings — these are persisted on every chart payload.
ENGINE_VERSION_VARIANT_A = "midpoint13_variant_a_v1"   # CANONICAL
ENGINE_VERSION_VARIANT_B = "midpoint12_variant_b"      # LEGACY / FORENSIC
ENGINE_VERSION_UNIFORM_30 = "uniform_30_legacy"        # DEPRECATED

# Public engine version constant — every NEW chart writes this value.
ASTROLOGY_ENGINE_VERSION = ENGINE_VERSION_VARIANT_A

# ---------------------------------------------------------------------------
# MODE CONSTANTS (public API)
# ---------------------------------------------------------------------------
MODE_UNIFORM_30                 = "uniform_30"
MODE_MIDPOINT12_VARIANT_B       = "midpoint12_variant_b"
MODE_MIDPOINT13_VARIANT_A       = "midpoint13_variant_a"

# Backwards-compatibility aliases (do not remove — many files still import these)
MODE_TRUE_SIDEREAL_MIDPOINT = MODE_MIDPOINT12_VARIANT_B  # legacy alias → Variant B

# Default mode = Variant A (canonical, production)
DEFAULT_MODE = MODE_MIDPOINT13_VARIANT_A

# Internal mode-label exposed in payloads
MIDPOINT_MODEL_NAME_VARIANT_A = "true_sidereal_midpoint_13_ophiuchus_separate"
MIDPOINT_MODEL_NAME_VARIANT_B = "true_sidereal_midpoint_12_merged_candidate"

# Legacy alias — old callers expect the Variant-B label (12-sign merged).
# We keep that semantics for back-compat so the migration script
# `astrology.zodiac_mode` filter does not silently re-tag every chart.
MIDPOINT_MODEL_NAME = MIDPOINT_MODEL_NAME_VARIANT_B

DEFAULT_AYANAMSA = 31.2836  # Sharatan (β-Arietis) SVP

# ---------------------------------------------------------------------------
# SIGN ENUMS — both registries (12-sign + 13-sign)
# ---------------------------------------------------------------------------
SIGNS_12: Tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# 13-sign canonical ordering (Ophiuchus sits between Scorpio and Sagittarius).
SIGNS_13: Tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Ophiuchus", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

OPHIUCHUS_SIGN_NAME = "Ophiuchus"
OPHIUCHUS_INDEX_IN_SIGNS_13 = SIGNS_13.index(OPHIUCHUS_SIGN_NAME)  # 8


def get_zodiac_signs(mode: str = DEFAULT_MODE) -> Tuple[str, ...]:
    """Return the sign enum appropriate for the given attribution mode."""
    if mode == MODE_MIDPOINT13_VARIANT_A:
        return SIGNS_13
    return SIGNS_12


# ---------------------------------------------------------------------------
# Variant B — True Sidereal-M Midpoint boundaries (12 signs, Ophiuchus merged).
# Tropical frame. Pisces wraps the 0° point.
# ---------------------------------------------------------------------------
MIDPOINT_BOUNDARIES_VARIANT_B: List[Tuple[str, float, float]] = [
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
    ("Pisces",      354.93,  25.61),
]
# Alias for legacy callers
MIDPOINT_BOUNDARIES = MIDPOINT_BOUNDARIES_VARIANT_B

# ---------------------------------------------------------------------------
# Variant A — 13-sign True Sidereal-M Midpoint boundaries (Ophiuchus separate).
# Derived from TRUE_SIDEREAL_MIDPOINT_BOUNDARIES_13 (zodiacal frame, 0° at
# Sharatan) shifted to tropical frame by ARIES_BOUNDARY_OFFSET = SVP = 31.2836.
# Pisces wraps the 0° point.
# ---------------------------------------------------------------------------
_VARIANT_A_OFFSET = 31.2836  # = SVP

_VARIANT_A_ZODIACAL: List[Tuple[str, float, float]] = [
    ("Aries",        0.0,      19.7286),
    ("Taurus",       19.7286,  56.5875),
    ("Gemini",       56.5875,  86.0412),
    ("Cancer",       86.0412, 103.19),
    ("Leo",         103.19,   141.6065),
    ("Virgo",       141.6065, 191.32),
    ("Libra",       191.32,   210.1972),
    ("Scorpio",     210.1972, 223.4245),
    ("Ophiuchus",   223.4245, 235.7818),
    ("Sagittarius", 235.7818, 269.2677),
    ("Capricorn",   269.2677, 294.8435),
    ("Aquarius",    294.8435, 318.0103),
    ("Pisces",      318.0103, 360.0),
]


def _build_variant_a_tropical() -> List[Tuple[str, float, float]]:
    """Convert the zodiacal-frame Variant A table to tropical frame.

    The shift moves the wrap point: Pisces ends at 360+offset = 31.2836°
    in tropical frame. We materialise that as a single entry where
    start > end (callers handle the wrap explicitly).
    """
    out: List[Tuple[str, float, float]] = []
    for name, lo, hi in _VARIANT_A_ZODIACAL:
        trop_lo = (lo + _VARIANT_A_OFFSET) % 360.0
        trop_hi = (hi + _VARIANT_A_OFFSET) % 360.0
        if trop_hi == 0.0:
            trop_hi = 360.0  # rare; keep half-open semantics
        out.append((name, trop_lo, trop_hi))
    return out


MIDPOINT_BOUNDARIES_VARIANT_A: List[Tuple[str, float, float]] = _build_variant_a_tropical()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(lng: float) -> float:
    """Normalise to [0, 360)."""
    return lng % 360.0


def _attribute_with_table(
    tropical_longitude: float,
    table: List[Tuple[str, float, float]],
    *,
    attribution_mode: str,
    engine_version: str,
) -> Dict[str, float]:
    """Generic boundary-table lookup honouring the Pisces wrap case."""
    trop = _norm(tropical_longitude)
    for name, start, end in table:
        if start <= end:
            if start <= trop < end:
                width = end - start
                raw_deg = round(trop - start, 6)
                # variant-a-real-width-display-v1
                # Variant-A canonical policy (per product owner, 2026-06-28):
                # Under the 13-sign Athen / Sharatan boundary table the
                # constellations have UNEQUAL widths (Virgo ≈ 49.71°,
                # Taurus ≈ 36.86°, Pisces ≈ 41.99°). The displayed degree
                # within a sign is the REAL offset from sign_start and
                # MAY legitimately exceed 30°. We do NOT clamp, wrap, or
                # proportionally rescale — that destroys astronomical
                # fidelity. The validity rule is simply:
                #     0 <= degree_within_sign < sign_width
                # `display_degree` is exposed as an alias of
                # `degree_within_sign` so downstream callers have a stable
                # field name; both values are identical.
                disp_deg = raw_deg
                return {
                    "sign":               name,
                    "degree_within_sign": raw_deg,
                    "display_degree":     disp_deg,
                    "sign_start":         round(start, 6),
                    "sign_end":           round(end, 6),
                    "sign_width":         round(width, 6),
                    "attribution_mode":   attribution_mode,
                    "engine_version":     engine_version,
                }
        else:
            # Wrap-band (Pisces) — start..360 ∪ 0..end.
            if trop >= start or trop < end:
                width = (360.0 - start) + end
                deg = (trop - start) % 360.0
                raw_deg = round(deg, 6)
                # See note above — display_degree is the raw offset.
                disp_deg = raw_deg
                return {
                    "sign":               name,
                    "degree_within_sign": raw_deg,
                    "display_degree":     disp_deg,
                    "sign_start":         round(start, 6),
                    "sign_end":           round(end, 6),
                    "sign_width":         round(width, 6),
                    "attribution_mode":   attribution_mode,
                    "engine_version":     engine_version,
                }
    raise ValueError(f"Sign attribution failed for tropical_longitude={tropical_longitude}")


# ---------------------------------------------------------------------------
# Mode-specific attributors
# ---------------------------------------------------------------------------

def attribute_sign_uniform_30(
    tropical_longitude: float,
    ayanamsa: float = DEFAULT_AYANAMSA,
) -> Dict[str, float]:
    """Original Mirror behaviour. Subtract ayanamsa, 30° equal signs."""
    trop = _norm(tropical_longitude)
    sidereal = _norm(trop - ayanamsa)
    idx = int(sidereal // 30) % 12
    deg = sidereal - 30.0 * idx
    sign_start_sidereal = 30.0 * idx
    sign_end_sidereal = sign_start_sidereal + 30.0
    sign_start_trop = _norm(sign_start_sidereal + ayanamsa)
    sign_end_trop = _norm(sign_end_sidereal + ayanamsa)
    return {
        "sign":               SIGNS_12[idx],
        "degree_within_sign": round(deg, 6),
        "sign_start":         round(sign_start_trop, 6),
        "sign_end":           round(sign_end_trop, 6),
        "sign_width":         30.0,
        "attribution_mode":   MODE_UNIFORM_30,
        "engine_version":     ENGINE_VERSION_UNIFORM_30,
    }


def attribute_sign_midpoint12_variant_b(
    tropical_longitude: float,
) -> Dict[str, float]:
    """LEGACY / FORENSIC — Variant B (12 signs, Ophiuchus merged into Scorpio).

    Retained as a rollback path. Do NOT use as the production default.
    """
    return _attribute_with_table(
        tropical_longitude,
        MIDPOINT_BOUNDARIES_VARIANT_B,
        attribution_mode=MIDPOINT_MODEL_NAME_VARIANT_B,
        engine_version=ENGINE_VERSION_VARIANT_B,
    )


def attribute_sign_midpoint13_variant_a(
    tropical_longitude: float,
) -> Dict[str, float]:
    """CANONICAL — Variant A (13 signs, Ophiuchus first-class).

    True Sidereal-M Midpoint with Ophiuchus broken out as its own band
    between Scorpio and Sagittarius. Production default.
    """
    return _attribute_with_table(
        tropical_longitude,
        MIDPOINT_BOUNDARIES_VARIANT_A,
        attribution_mode=MIDPOINT_MODEL_NAME_VARIANT_A,
        engine_version=ENGINE_VERSION_VARIANT_A,
    )


# Legacy alias (kept for callers that still import the old name).
attribute_sign_true_sidereal_midpoint = attribute_sign_midpoint12_variant_b


# ---------------------------------------------------------------------------
# Public router
# ---------------------------------------------------------------------------

def attribute_sign(
    tropical_longitude: float,
    mode: str = DEFAULT_MODE,
    ayanamsa: float = DEFAULT_AYANAMSA,
) -> Dict[str, float]:
    """Router. Default = MODE_MIDPOINT13_VARIANT_A (canonical)."""
    if mode == MODE_MIDPOINT13_VARIANT_A:
        return attribute_sign_midpoint13_variant_a(tropical_longitude)
    if mode in (MODE_MIDPOINT12_VARIANT_B, MODE_TRUE_SIDEREAL_MIDPOINT):
        return attribute_sign_midpoint12_variant_b(tropical_longitude)
    if mode == MODE_UNIFORM_30:
        return attribute_sign_uniform_30(tropical_longitude, ayanamsa=ayanamsa)
    # Unknown mode → safest fallback = canonical Variant A
    return attribute_sign_midpoint13_variant_a(tropical_longitude)


def dual_compute(
    tropical_longitude: float,
    ayanamsa: float = DEFAULT_AYANAMSA,
) -> Dict[str, Dict]:
    """PHASE 3 helper — compute both Variant A (canonical) and Variant B
    (forensic) for the same tropical longitude in one call.

    Returns:
        {
            "canonical":          <Variant A result>,
            "forensic_variant_b": <Variant B result>,
            "uniform_30":         <legacy uniform>,
            "match_a_vs_b":       bool,
            "is_ophiuchus":       bool,
        }
    """
    a = attribute_sign_midpoint13_variant_a(tropical_longitude)
    b = attribute_sign_midpoint12_variant_b(tropical_longitude)
    u = attribute_sign_uniform_30(tropical_longitude, ayanamsa=ayanamsa)
    return {
        "canonical":          a,
        "forensic_variant_b": b,
        "uniform_30":         u,
        "match_a_vs_b":       a["sign"] == b["sign"],
        "is_ophiuchus":       a["sign"] == OPHIUCHUS_SIGN_NAME,
    }


# Re-exports for callers that want the registries directly.
__all__ = [
    "BUILD_MARKER",
    "ASTROLOGY_ENGINE_VERSION",
    "ENGINE_VERSION_VARIANT_A",
    "ENGINE_VERSION_VARIANT_B",
    "ENGINE_VERSION_UNIFORM_30",
    "DEFAULT_MODE",
    "DEFAULT_AYANAMSA",
    "MODE_UNIFORM_30",
    "MODE_MIDPOINT12_VARIANT_B",
    "MODE_MIDPOINT13_VARIANT_A",
    "MODE_TRUE_SIDEREAL_MIDPOINT",  # legacy alias
    "MIDPOINT_MODEL_NAME_VARIANT_A",
    "MIDPOINT_MODEL_NAME_VARIANT_B",
    "MIDPOINT_MODEL_NAME",
    "SIGNS_12",
    "SIGNS_13",
    "OPHIUCHUS_SIGN_NAME",
    "OPHIUCHUS_INDEX_IN_SIGNS_13",
    "MIDPOINT_BOUNDARIES",                  # legacy alias → Variant B
    "MIDPOINT_BOUNDARIES_VARIANT_A",
    "MIDPOINT_BOUNDARIES_VARIANT_B",
    "get_zodiac_signs",
    "attribute_sign",
    "attribute_sign_uniform_30",
    "attribute_sign_midpoint12_variant_b",
    "attribute_sign_midpoint13_variant_a",
    "attribute_sign_true_sidereal_midpoint",  # legacy alias → Variant B
    "dual_compute",
]
