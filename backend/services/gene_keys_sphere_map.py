"""Gene Keys Canonical Sphere Map — The Mirror

===============================================================================
CANONICAL SOURCE OF TRUTH — Session 4A (2026-07-26)
===============================================================================
Version: mirror_true_sidereal_gk_v1

METHODOLOGY DISCLOSURE
----------------------
Sphere-to-activation semantics follow the first-party Gene Keys mapping
documented by the Gene Keys tradition:
  - https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/
  - https://genekeys.com/resource/astrology/

Longitudes, the Design (pre-natal) calculation, and 64-gate placement come
from The Mirror's governed True Sidereal activation engine
(`calculations/human_design.py`, `hd_sidereal_v1`).

The resulting profile is therefore *The Mirror's True Sidereal Gene Keys
variant*.  It may differ from profiles produced by the standard Gene Keys
online generator, which uses a different zodiacal convention.  We do not
claim calculation parity with the official Gene Keys profile unless that
parity has been independently verified.

IP GOVERNANCE
-------------
This file records mapping facts only (permitted structural terminology per
`memory/gene_keys_ip_policy_v1.md`).  It contains no copyrighted
interpretive prose.  All interpretive content is Mirror-authored elsewhere.

DO NOT modify without:
  - bumping GENE_KEYS_SPHERE_MAP_VERSION
  - updating the regression tests in
    `tests/test_the_mirror_session4a_gene_keys_foundation.py`
"""

from typing import Dict, List, TypedDict, Literal


GENE_KEYS_SPHERE_MAP_VERSION = "mirror_true_sidereal_gk_v1"


# =============================================================================
# CANONICAL SPHERE → ACTIVATION MAP (first-party Gene Keys correlations)
# =============================================================================
#
# Each entry: sphere_name -> (planet, chart_side)
#   planet: name from human_design.py's hd_planets list
#   chart_side: "personality" (natal/conscious) or "design" (pre-natal/unconscious)
#
# Ordering follows the standard three-sequence Golden Path.
# Life's Work / Brand and Core / Vocation are represented as *shared activation
# roles*, not duplicated sphere data (see UNIQUE_SPHERE_ACTIVATIONS below).

ChartSide = Literal["personality", "design"]


class SphereActivation(TypedDict):
    planet: str
    chart_side: ChartSide


CANONICAL_SPHERE_MAP: Dict[str, SphereActivation] = {
    # Activation Sequence
    "Life's Work": {"planet": "Sun",   "chart_side": "personality"},
    "Evolution":   {"planet": "Earth", "chart_side": "personality"},
    "Radiance":    {"planet": "Sun",   "chart_side": "design"},
    "Purpose":     {"planet": "Earth", "chart_side": "design"},

    # Venus Sequence
    "Attraction":  {"planet": "Moon",    "chart_side": "design"},
    "IQ":          {"planet": "Venus",   "chart_side": "personality"},
    "EQ":          {"planet": "Mars",    "chart_side": "personality"},
    "SQ":          {"planet": "Venus",   "chart_side": "design"},
    "Core":        {"planet": "Mars",    "chart_side": "design"},

    # Pearl Sequence
    "Vocation":    {"planet": "Mars",    "chart_side": "design"},   # shares activation with Core
    "Culture":     {"planet": "Jupiter", "chart_side": "design"},
    "Brand":       {"planet": "Sun",     "chart_side": "personality"},  # shares activation with Life's Work
    "Pearl":       {"planet": "Jupiter", "chart_side": "personality"},
}


# =============================================================================
# SEQUENCE MEMBERSHIP — an ordered list per sequence
# =============================================================================

ACTIVATION_SEQUENCE: List[str] = ["Life's Work", "Evolution", "Radiance", "Purpose"]
VENUS_SEQUENCE:      List[str] = ["Attraction", "IQ", "EQ", "SQ", "Core"]
PEARL_SEQUENCE:      List[str] = ["Vocation", "Culture", "Brand", "Pearl"]

SEQUENCES: Dict[str, List[str]] = {
    "Activation": ACTIVATION_SEQUENCE,
    "Venus":      VENUS_SEQUENCE,
    "Pearl":      PEARL_SEQUENCE,
}


# =============================================================================
# SHARED-ACTIVATION ROLES
# =============================================================================
# Some spheres are participation roles for the *same* underlying activation.
# We keep the roles distinct (they mean different things) but represent the
# fact-of-sharing explicitly, so downstream systems do not duplicate sphere
# data or double-count evidence.

SHARED_ACTIVATION_ROLES: List[Dict[str, str]] = [
    {
        "primary": "Life's Work",
        "shared":  "Brand",
        "reason":  "Both spheres read the natal/Personality Sun (Activation vs Pearl context).",
    },
    {
        "primary": "Core",
        "shared":  "Vocation",
        "reason":  "Both spheres read the pre-natal/Design Mars (Venus vs Pearl context).",
    },
]


def get_unique_activation_points() -> List[SphereActivation]:
    """Return the deduplicated set of underlying (planet, chart_side)
    activation points referenced by the profile.

    Order-preserving deduplication over CANONICAL_SPHERE_MAP.values().
    """
    seen: set = set()
    unique: List[SphereActivation] = []
    for act in CANONICAL_SPHERE_MAP.values():
        key = (act["planet"], act["chart_side"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(act)
    return unique


def get_sphere_role_map() -> Dict[str, Dict[str, object]]:
    """Return sphere -> {sequences: [...], activation: {planet, chart_side}}.

    A sphere always sits in exactly one sequence in this v1 mapping, but the
    structure supports future extensions (e.g. Star Pearl) without changing
    the schema.
    """
    role_map: Dict[str, Dict[str, object]] = {}
    for sphere, activation in CANONICAL_SPHERE_MAP.items():
        role_map[sphere] = {
            "activation": activation,
            "sequences": [seq for seq, members in SEQUENCES.items() if sphere in members],
        }
    return role_map


# =============================================================================
# METHODOLOGY PROVENANCE (permitted structural reference — mapping facts only)
# =============================================================================
METHODOLOGY_PROVENANCE: Dict[str, object] = {
    "version": GENE_KEYS_SPHERE_MAP_VERSION,
    "sphere_map_source": "gene_keys_first_party_docs_v1",
    "sphere_map_reference_urls": [
        "https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/",
        "https://genekeys.com/resource/astrology/",
    ],
    "longitude_engine": "the_mirror.hd_sidereal_v1",
    "gate_mandala": "human_design_64_gate_i_ching_wheel",
    "design_calculation": "pre_natal_88_solar_degrees",
    "disclosure": (
        "This profile uses The Mirror's True Sidereal activation method. "
        "It may differ from profiles calculated using other zodiac or Human "
        "Design conventions."
    ),
    "not_claimed": "parity_with_standard_gene_keys_online_profile",
}


# =============================================================================
# STAR PEARL POLICY (Session 4A: withheld)
# =============================================================================
STAR_PEARL_AVAILABILITY = "UNAVAILABLE_OR_DEFERRED"
STAR_PEARL_REASON = (
    "Star Pearl requires a fourth foundational sequence whose sphere-to-"
    "activation correlations, terminology audit against the IP policy, and "
    "product-purpose justification are not yet verified.  Not surfaced in "
    "Session 4A."
)


# =============================================================================
# LEGACY / PRE-CANONICAL MAPPINGS (for delta reporting only)
# =============================================================================
# These are recorded so the audit report can show *what changed* when
# reconciling the two earlier source files.  Do not consume these at runtime.

LEGACY_CALC_MAP: Dict[str, SphereActivation] = {
    "Life's Work": {"planet": "Sun",   "chart_side": "personality"},
    "Evolution":   {"planet": "Earth", "chart_side": "personality"},
    "Radiance":    {"planet": "Sun",   "chart_side": "design"},
    "Purpose":     {"planet": "Earth", "chart_side": "design"},
    "Attraction":  {"planet": "Venus", "chart_side": "design"},    # WAS WRONG
    "IQ":          {"planet": "Mercury","chart_side": "personality"},# WAS WRONG (Mercury vs Venus)
    "EQ":          {"planet": "Venus", "chart_side": "personality"},# WAS WRONG (Venus vs Mars)
    "SQ":          {"planet": "Moon",  "chart_side": "design"},    # WAS WRONG (Moon vs Venus)
    "Core":        {"planet": "Mars",  "chart_side": "design"},
    "Brand":       {"planet": "Sun",   "chart_side": "personality"},
    "Culture":     {"planet": "Jupiter","chart_side": "design"},
    "Vocation":    {"planet": "Mars",  "chart_side": "design"},
    "Pearl":       {"planet": "Jupiter","chart_side": "personality"},
}


LEGACY_INTERPRETER_DOCSTRING_MAP: Dict[str, SphereActivation] = {
    # From the docstring inside services/gene_keys_interpreter.py (functions
    # get_activation_sequence, get_venus_sequence, get_pearl_sequence).
    "Life's Work": {"planet": "Sun",     "chart_side": "personality"},
    "Evolution":   {"planet": "Earth",   "chart_side": "personality"},
    "Radiance":    {"planet": "Sun",     "chart_side": "design"},
    "Purpose":     {"planet": "Earth",   "chart_side": "design"},
    "Attraction":  {"planet": "Moon",    "chart_side": "design"},
    "IQ":          {"planet": "Mercury", "chart_side": "personality"},# WAS WRONG (planet)
    "EQ":          {"planet": "Mercury", "chart_side": "design"},    # WAS WRONG (planet + side)
    "SQ":          {"planet": "Venus",   "chart_side": "design"},
    "Core":        {"planet": "Mars",    "chart_side": "personality"},# WAS WRONG (side)
    "Vocation":    {"planet": "Mars",    "chart_side": "design"},
    "Culture":     {"planet": "Jupiter", "chart_side": "personality"},# WAS WRONG (side)
    "Brand":       {"planet": "Sun",     "chart_side": "personality"},
    "Pearl":       {"planet": "Jupiter", "chart_side": "design"},    # WAS WRONG (side)
}


def sphere_deltas_vs_canonical(other: Dict[str, SphereActivation]) -> List[Dict[str, str]]:
    """Return per-sphere deltas between `other` mapping and CANONICAL_SPHERE_MAP.

    Used by the audit report and tests.
    """
    deltas = []
    for sphere, canonical in CANONICAL_SPHERE_MAP.items():
        legacy = other.get(sphere)
        if not legacy:
            deltas.append({"sphere": sphere, "status": "missing_in_legacy"})
            continue
        if legacy["planet"] != canonical["planet"] or legacy["chart_side"] != canonical["chart_side"]:
            deltas.append({
                "sphere": sphere,
                "legacy_planet": legacy["planet"],
                "legacy_side": legacy["chart_side"],
                "canonical_planet": canonical["planet"],
                "canonical_side": canonical["chart_side"],
                "status": "changed",
            })
    return deltas
