"""hd_signature_notself.py — Canonical Signature + Not-Self derivation
========================================================================

Deterministic HD-domain mapping from Type → (Signature, Not-Self theme).
Session-3b Decision 2: this is a HD-domain semantic. It must live on
the backend so the frontend never re-derives it.

Sources (standard HD literature — Ra Uru Hu / Jovian Archive):
  Manifestor        → Signature: Peace         · Not-Self: Anger
  Generator         → Signature: Satisfaction  · Not-Self: Frustration
  Manifesting Gen.  → Signature: Satisfaction  · Not-Self: Frustration + Anger
  Projector         → Signature: Success       · Not-Self: Bitterness
  Reflector         → Signature: Surprise      · Not-Self: Disappointment

build_marker: the-mirror-hd-signature-notself-v1
"""
from __future__ import annotations
from typing import Dict, Optional


_MAP: Dict[str, Dict[str, str]] = {
    "Manifestor":          {"signature": "Peace",        "not_self": "Anger"},
    "Generator":           {"signature": "Satisfaction", "not_self": "Frustration"},
    "Manifesting Generator": {"signature": "Satisfaction", "not_self": "Frustration and Anger"},
    "Projector":           {"signature": "Success",      "not_self": "Bitterness"},
    "Reflector":           {"signature": "Surprise",     "not_self": "Disappointment"},
}

DERIVATION_RULE_ID = "hd_signature_notself_from_type_v1"


def signature_and_not_self(hd_type: Optional[str]) -> Optional[Dict[str, str]]:
    """Return {signature, not_self, derivation_rule, source} for a
    canonical HD Type. None when the Type is unrecognisable."""
    if not isinstance(hd_type, str) or not hd_type.strip():
        return None
    key = hd_type.strip()
    # Accept a couple of common variants
    variants = {
        "MG": "Manifesting Generator",
        "Manifesting-Generator": "Manifesting Generator",
        "Man Gen": "Manifesting Generator",
    }
    key = variants.get(key, key)
    entry = _MAP.get(key)
    if not entry:
        return None
    return {
        "signature":       entry["signature"],
        "not_self":        entry["not_self"],
        "derivation_rule": DERIVATION_RULE_ID,
        "source":          "human_design.type",
    }


__all__ = ["signature_and_not_self", "DERIVATION_RULE_ID"]
