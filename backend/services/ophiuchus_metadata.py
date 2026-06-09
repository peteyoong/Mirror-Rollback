"""
Ophiuchus Metadata — single source of truth for sign-keyed registries.
========================================================================
Build marker: midpoint13-variant-a-canonical-v1

Variant A (the canonical Mirror engine) treats Ophiuchus as a first-class
sign sitting between Scorpio and Sagittarius. Every sign-keyed dictionary
in the codebase (element, modality, ruler, archetype, polarity, etc.)
must be Ophiuchus-aware.

Rather than scattering Ophiuchus literals across dozens of files, this
module exposes the canonical attributes once. Each registry file imports
from here and patches its own table at import time.

Canonical assignments (Athen / Mastering-the-Zodiac / Genetic Matrix
tradition; chosen for internal consistency, not as a horoscope claim):

    element     : "ether"        # the 5th / transcendent element, distinct
                                  # from fire/earth/air/water — preserves
                                  # the 4-element symmetry rather than
                                  # forcing Ophiuchus into one of the four.
    modality    : "mutable"      # transitional / shamanic / healer.
    polarity    : "neutral"      # sits between yang Scorpio and yang Sag.
    ruler       : "Chiron"       # wounded-healer / Asclepius archetype.
    co_ruler    : "Pluto"        # depth/transformation continuity from Sco.
    glyph       : "⛎"
    archetype   : "shaman / wound-keeper / threshold"
    keyword     : "threshold"

These are deliberately minimal — Ophiuchus interpretation content lives
downstream (lens narratives), NOT in this metadata module.
"""

from __future__ import annotations

from typing import Dict, Any

OPHIUCHUS_SIGN_NAME = "Ophiuchus"

OPHIUCHUS_ELEMENT  = "ether"
OPHIUCHUS_MODALITY = "mutable"
OPHIUCHUS_POLARITY = "neutral"
OPHIUCHUS_RULER    = "Chiron"
OPHIUCHUS_CO_RULER = "Pluto"
OPHIUCHUS_GLYPH    = "⛎"
OPHIUCHUS_ARCHETYPE = "shaman / wound-keeper / threshold"
OPHIUCHUS_KEYWORD   = "threshold"


def patch_element_map(m: Dict[str, str]) -> Dict[str, str]:
    """Ensure an element map has an Ophiuchus entry. Idempotent."""
    if OPHIUCHUS_SIGN_NAME not in m:
        m[OPHIUCHUS_SIGN_NAME] = OPHIUCHUS_ELEMENT
    return m


def patch_modality_map(m: Dict[str, str]) -> Dict[str, str]:
    """Ensure a modality map has an Ophiuchus entry. Idempotent."""
    if OPHIUCHUS_SIGN_NAME not in m:
        m[OPHIUCHUS_SIGN_NAME] = OPHIUCHUS_MODALITY
    return m


def patch_ruler_map(m: Dict[str, str]) -> Dict[str, str]:
    """Ensure a sign-ruler map has an Ophiuchus entry. Idempotent."""
    if OPHIUCHUS_SIGN_NAME not in m:
        m[OPHIUCHUS_SIGN_NAME] = OPHIUCHUS_RULER
    return m


def patch_polarity_map(m: Dict[str, str]) -> Dict[str, str]:
    if OPHIUCHUS_SIGN_NAME not in m:
        m[OPHIUCHUS_SIGN_NAME] = OPHIUCHUS_POLARITY
    return m


def patch_glyph_map(m: Dict[str, str]) -> Dict[str, str]:
    if OPHIUCHUS_SIGN_NAME not in m:
        m[OPHIUCHUS_SIGN_NAME] = OPHIUCHUS_GLYPH
    return m


def get_ophiuchus_meta() -> Dict[str, Any]:
    """Return the full Ophiuchus metadata bundle."""
    return {
        "sign":      OPHIUCHUS_SIGN_NAME,
        "element":   OPHIUCHUS_ELEMENT,
        "modality":  OPHIUCHUS_MODALITY,
        "polarity":  OPHIUCHUS_POLARITY,
        "ruler":     OPHIUCHUS_RULER,
        "co_ruler":  OPHIUCHUS_CO_RULER,
        "glyph":     OPHIUCHUS_GLYPH,
        "archetype": OPHIUCHUS_ARCHETYPE,
        "keyword":   OPHIUCHUS_KEYWORD,
    }


__all__ = [
    "OPHIUCHUS_SIGN_NAME",
    "OPHIUCHUS_ELEMENT",
    "OPHIUCHUS_MODALITY",
    "OPHIUCHUS_POLARITY",
    "OPHIUCHUS_RULER",
    "OPHIUCHUS_CO_RULER",
    "OPHIUCHUS_GLYPH",
    "OPHIUCHUS_ARCHETYPE",
    "OPHIUCHUS_KEYWORD",
    "patch_element_map",
    "patch_modality_map",
    "patch_ruler_map",
    "patch_polarity_map",
    "patch_glyph_map",
    "get_ophiuchus_meta",
]
