"""
Tests for Phase-2 Mirror Object Interpretation Layer.

Build marker: mirror-interpretation-layer-v1
"""
from __future__ import annotations

import pytest

from services.mirror_object_interpreter import (
    BUILD_MARKER,
    has_mirror_interpretation,
    build_mirror_object_proof_block,
)
from services.natal_object_engine import build_natal_object_proof_block


# ----------------------------------------------------------------------
# Coverage of Mirror-interpreted objects
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name,expected", [
    ("Vertex", True),
    ("Anti-Vertex", True),
    ("Juno", True),
    ("Chiron", True),
    ("Black Moon Lilith", True),
    ("True Black Moon Lilith", True),       # alias → Black Moon Lilith
    ("Lot of Fortune", True),
    ("Lot of Spirit", True),
    ("Pholus", True),
    # T2 additions — mirror-interpretation-layer-v1.1
    ("Ceres", True),
    ("Pallas", True),
    ("Vesta", True),
    ("North Node", True),
    ("South Node", True),
    # Not Mirror-wrapped — fall back to generic block
    ("Sun", False),
    ("", False),
])
def test_has_mirror_interpretation(name, expected):
    assert has_mirror_interpretation(name) is expected


# ----------------------------------------------------------------------
# Block-shape contract
# ----------------------------------------------------------------------
def _make_envelope(object_name, sign="Virgo", house=9, lon=142.12):
    return {
        "success": True,
        "object": object_name,
        "build_marker": "test",
        "placement": {
            "sign": sign,
            "degree": 0.5,
            "formatted": f"0°{sign}",
            "longitude": lon,
            "house": house,
            "body_type": "angle",
            "source": "test",
        },
    }


@pytest.mark.parametrize("object_name", [
    "Vertex", "Anti-Vertex", "Juno", "Chiron",
    "Black Moon Lilith", "Lot of Fortune", "Lot of Spirit", "Pholus",
])
def test_mirror_block_contains_placement_and_voice_floor(object_name):
    env = _make_envelope(object_name)
    block = build_mirror_object_proof_block(env)
    assert block, f"Mirror block empty for {object_name}"
    assert "MIRROR INTERPRETATION" in block
    assert object_name in block or "Black Moon Lilith" in block
    assert "Mirror question" in block
    assert "VOICE FLOOR" in block
    # Placement must surface inside the block
    assert "0°Virgo" in block
    # Each block must publish its build marker for trace
    assert BUILD_MARKER in block


# ----------------------------------------------------------------------
# Object-specific ban lists
# ----------------------------------------------------------------------
def test_chiron_block_bans_victim_language():
    block = build_mirror_object_proof_block(_make_envelope("Chiron"))
    # Bans must surface in the prompt so the LLM sees them
    for forbidden in ("deep wound", "core wound", "trauma response"):
        assert forbidden in block.lower(), (
            f"Chiron block missing victim-ban for {forbidden!r}"
        )


def test_lilith_block_bans_fear_language():
    block = build_mirror_object_proof_block(_make_envelope("Black Moon Lilith"))
    for forbidden in ("shadow work", "scary", "be careful"):
        assert forbidden in block.lower()


def test_juno_block_bans_soulmate_language():
    block = build_mirror_object_proof_block(_make_envelope("Juno"))
    for forbidden in ("soulmate", "twin flame", "fated to marry"):
        assert forbidden in block.lower()


def test_vertex_block_bans_destiny_language():
    block = build_mirror_object_proof_block(_make_envelope("Vertex"))
    for forbidden in ("fated meeting", "destined to meet", "karmic appointment"):
        assert forbidden in block.lower()


def test_fortune_block_bans_luck_language():
    block = build_mirror_object_proof_block(_make_envelope("Lot of Fortune"))
    for forbidden in ("luck", "destiny", "manifestation"):
        assert forbidden in block.lower()


def test_spirit_block_bans_purpose_cliches():
    block = build_mirror_object_proof_block(_make_envelope("Lot of Spirit"))
    for forbidden in ("soul purpose", "ascension", "destiny"):
        assert forbidden in block.lower()


# ----------------------------------------------------------------------
# True Lilith aliases to Black Moon Lilith block
# ----------------------------------------------------------------------
def test_true_lilith_aliases_to_lilith_block():
    block_bml = build_mirror_object_proof_block(_make_envelope("Black Moon Lilith"))
    block_tru = build_mirror_object_proof_block(_make_envelope("True Black Moon Lilith"))
    # Same instruction set (just the object label differs in the header)
    assert "untamed truth" in block_bml.lower()
    assert "untamed truth" in block_tru.lower()


# ----------------------------------------------------------------------
# Integration: natal_object_engine routes Phase-2 objects to Mirror block
# ----------------------------------------------------------------------
def test_natal_object_engine_uses_mirror_block_for_vertex():
    env = _make_envelope("Vertex")
    block = build_natal_object_proof_block(env)
    assert "MIRROR INTERPRETATION" in block
    assert "Which encounters carry unusual weight" in block


def test_natal_object_engine_uses_mirror_block_for_juno():
    env = _make_envelope("Juno")
    block = build_natal_object_proof_block(env)
    assert "MIRROR INTERPRETATION" in block
    assert "What does commitment actually look like" in block


def test_natal_object_engine_falls_back_to_generic_for_non_mirror_object():
    # Eros is a valid engine object but is NOT in the Mirror interpretation
    # layer — used here to prove the generic fallback path still fires for
    # bodies outside the Mirror catalogue.  (Ceres was the original example
    # here but Ceres is now T2-extended into the Mirror layer.)
    env = _make_envelope("Eros")
    block = build_natal_object_proof_block(env)
    # Not Mirror-wrapped → generic block (no MIRROR INTERPRETATION header)
    assert "ENGINE OUTPUT" in block
    assert "MIRROR INTERPRETATION" not in block


# ----------------------------------------------------------------------
# Safety: unsuccessful envelopes still go through the not-wired path
# ----------------------------------------------------------------------
def test_failed_envelope_does_not_invoke_mirror_block():
    env = {
        "success": False,
        "object": "Vertex",
        "reason": "vertex_inputs_missing",
        "message": "Vertex couldn't be computed — birth coordinates or "
                   "Julian Day are missing from this chart.",
    }
    block = build_natal_object_proof_block(env)
    assert "MIRROR INTERPRETATION" not in block
    assert "ENGINE STATUS" in block
    assert "couldn't be computed" in block
