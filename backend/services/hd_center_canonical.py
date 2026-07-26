"""hd_center_canonical.py — Canonical HD centre naming
========================================================

Session-2 policy decision: canonical name is "Heart/Ego" (product owner
sign-off).  All backend endpoints, prompts, evidence objects and the FE
must resolve any legacy alias to this canonical vocabulary.

Legacy aliases we accept at ingestion boundaries:
  Ego / Heart / Heart Center / Ego Center / heart / ego / heart_center /
  the_heart / etc.

Also normalizes:
  G Center / G / G/Identity / Identity → G/Identity

Nine canonical centres (rendered in this canonical order):
  Head, Ajna, Throat, G/Identity, Heart/Ego,
  Solar Plexus, Sacral, Spleen, Root

build_marker: hd-center-canonical-v1
"""
from __future__ import annotations
from typing import Iterable, List, Optional


CANONICAL_CENTERS: List[str] = [
    "Head", "Ajna", "Throat", "G/Identity", "Heart/Ego",
    "Solar Plexus", "Sacral", "Spleen", "Root",
]


_ALIAS_MAP = {
    # heart / ego family
    "ego":            "Heart/Ego",
    "heart":          "Heart/Ego",
    "heart center":   "Heart/Ego",
    "heart centre":   "Heart/Ego",
    "ego center":     "Heart/Ego",
    "ego centre":     "Heart/Ego",
    "heart/ego":      "Heart/Ego",
    "heart / ego":    "Heart/Ego",
    "ego/heart":      "Heart/Ego",
    "the heart":      "Heart/Ego",
    "will":           "Heart/Ego",

    # g / identity family
    "g":              "G/Identity",
    "g center":       "G/Identity",
    "g centre":       "G/Identity",
    "g/identity":     "G/Identity",
    "g / identity":   "G/Identity",
    "identity":       "G/Identity",
    "the g":          "G/Identity",
    "self":           "G/Identity",

    # straightforward ones — enable case-insensitive resolution
    "head":           "Head",
    "head center":    "Head",
    "head centre":    "Head",
    "ajna":           "Ajna",
    "ajna center":    "Ajna",
    "ajna centre":    "Ajna",
    "throat":         "Throat",
    "throat center":  "Throat",
    "throat centre":  "Throat",
    "sacral":         "Sacral",
    "sacral center":  "Sacral",
    "sacral centre":  "Sacral",
    "solar plexus":   "Solar Plexus",
    "solar plexus center":  "Solar Plexus",
    "solar plexus centre":  "Solar Plexus",
    "sp":             "Solar Plexus",
    "spleen":         "Spleen",
    "spleen center":  "Spleen",
    "spleen centre":  "Spleen",
    "splenic":        "Spleen",
    "root":           "Root",
    "root center":    "Root",
    "root centre":    "Root",
}


def canonicalize_center(name: object) -> Optional[str]:
    """Return the canonical centre name or None when unrecognisable."""
    if not isinstance(name, str) or not name.strip():
        return None
    key = name.strip().lower().replace("_", " ").replace("-", " ")
    # Strip parenthetical annotations like "Ajna (Mind)" → "ajna"
    import re
    key = re.sub(r"\s*\([^)]*\)", "", key)
    # collapse repeat whitespace
    while "  " in key:
        key = key.replace("  ", " ")
    key = key.strip()
    return _ALIAS_MAP.get(key)


def canonicalize_centers(names: Iterable[object]) -> List[str]:
    """Canonicalize an iterable of centre-name strings, dropping
    unrecognisable entries and de-duplicating while preserving canonical
    order."""
    seen: set = set()
    out: List[str] = []
    for n in names or []:
        c = canonicalize_center(n)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    # Preserve canonical rendering order
    order_idx = {c: i for i, c in enumerate(CANONICAL_CENTERS)}
    out.sort(key=lambda c: order_idx.get(c, 999))
    return out


def split_defined_undefined(
    defined_raw: Iterable[object],
) -> tuple:
    """Given a list of defined centres (in any alias), return the
    (defined, undefined) canonical pair with the invariants:
      * every centre resolves to a canonical name
      * no centre appears in both lists
      * total = 9
    """
    canon_defined = canonicalize_centers(defined_raw)
    undefined = [c for c in CANONICAL_CENTERS if c not in canon_defined]
    return canon_defined, undefined


__all__ = [
    "CANONICAL_CENTERS",
    "canonicalize_center",
    "canonicalize_centers",
    "split_defined_undefined",
]
