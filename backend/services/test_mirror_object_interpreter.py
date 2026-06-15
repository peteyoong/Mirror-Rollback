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


# ----------------------------------------------------------------------
# voice-floor-v2 — escalated bans baked into every Mirror block
# ----------------------------------------------------------------------
def test_voice_floor_v2_escalated_bans_present():
    """Every Mirror block must surface the escalated voice-floor bans
    so the LLM cannot silently drift back into textbook phrasing."""
    block = build_mirror_object_proof_block(_make_envelope("Ceres"))
    for forbidden in (
        "this placement suggests",
        "this placement indicates",
        "this placement invites",
        "often manifests as",
        "speaks to how",
        "Remember, this",
        "as per our agreement",
        "grounded in one area at a time",
    ):
        assert forbidden.lower() in block.lower(), (
            f"voice-floor-v2: missing ban on {forbidden!r}"
        )


# ----------------------------------------------------------------------
# Multi-object — pairwise builder + nodal axis builder
# astrology-chat-multi-object-v1
# ----------------------------------------------------------------------
from services.mirror_object_interpreter import (  # noqa: E402
    build_axis_mirror_block,
    build_pairwise_mirror_block,
    is_nodal_axis,
)


def test_is_nodal_axis_detection():
    assert is_nodal_axis(["North Node", "South Node"]) is True
    assert is_nodal_axis(["South Node", "North Node"]) is True
    assert is_nodal_axis(["Ceres", "Vesta"]) is False
    assert is_nodal_axis(["North Node"]) is False
    assert is_nodal_axis([]) is False


def test_nodal_axis_block_unifies_both_nodes():
    nn = _make_envelope("North Node", sign="Pisces", house=4)
    sn = _make_envelope("South Node", sign="Virgo", house=10)
    block = build_axis_mirror_block(nn, sn)
    assert "Nodal Axis" in block
    assert "North Node" in block
    assert "South Node" in block
    # Both placements must surface in the unified block
    assert "Pisces" in block
    assert "Virgo" in block
    # Polarity framing markers
    assert "overused" in block.lower()
    assert "stretch" in block.lower()
    # Axis-specific ban list must still ban past-life / soul-debt language
    assert "past life" in block.lower()
    assert "soul debt" in block.lower()


def test_pairwise_block_concatenates_two_bodies():
    ceres = _make_envelope("Ceres", sign="Virgo", house=10)
    vesta = _make_envelope("Vesta", sign="Aquarius", house=2)
    block = build_pairwise_mirror_block([ceres, vesta])
    assert "pairwise" in block.lower() or "INTERSECTION" in block.upper() or "intersection" in block.lower()
    # Both objects surface in the block
    assert "Ceres" in block
    assert "Vesta" in block
    # Both placements surface
    assert "Virgo" in block
    assert "Aquarius" in block
    # Per-object Mirror questions are surfaced
    assert "nourish" in block.lower()           # Ceres question
    assert "quiet, ongoing attention" in block.lower()  # Vesta question
    # The intersection instruction must explicitly forbid refusing the
    # second body (so the LLM can't bail with "let's stay on one topic").
    assert "do not refuse" in block.lower()
    assert "do not invent a prior agreement" in block.lower()


def test_pairwise_with_single_envelope_returns_single_block():
    """Pairwise builder gracefully delegates to single-block when only
    one envelope is passed."""
    env = _make_envelope("Ceres", sign="Virgo", house=10)
    block = build_pairwise_mirror_block([env])
    assert "MIRROR INTERPRETATION: Ceres" in block
    assert "pairwise" not in block.lower()


def test_pairwise_with_one_failed_envelope_still_renders():
    """If one body in a pair fails to compute, the block still emits
    rather than silently dropping the multi-object query."""
    ok = _make_envelope("Ceres", sign="Virgo", house=10)
    fail = {
        "success": False,
        "object": "Eros",
        "reason": "ephemeris_file_missing",
        "message": "Eros isn't wired into this build (its .se1 file is "
                   "missing).",
    }
    block = build_pairwise_mirror_block([ok, fail])
    assert "Ceres" in block
    assert "Eros" in block
    assert "not computed" in block.lower()


# ----------------------------------------------------------------------
# Degree-rendering — Variant-A signs can be > 30° wide.
# Display-cap at 29 so user-visible text never shows "33° Leo".
# voice-floor-v2 degree-rendering-fix
# ----------------------------------------------------------------------
def test_display_degree_caps_above_29():
    env = _make_envelope("Pallas", sign="Leo", house=9)
    env["placement"]["degree"] = 33.3121   # Variant-A Pallas in wide Leo
    block = build_mirror_object_proof_block(env)
    # Capped to 29° in the user-visible proof block
    assert "29°Leo" in block
    # Raw 33° MUST NOT appear (would confuse users)
    assert "33°" not in block
    assert "33° Leo" not in block


def test_display_degree_normal_range_unchanged():
    env = _make_envelope("Chiron", sign="Aries", house=1)
    env["placement"]["degree"] = 12.4
    block = build_mirror_object_proof_block(env)
    assert "12°Aries" in block


def test_display_degree_missing_degree_falls_back_to_sign_only():
    env = _make_envelope("Chiron", sign="Aries", house=1)
    env["placement"]["degree"] = None
    env["placement"].pop("formatted", None)
    block = build_mirror_object_proof_block(env)
    # No raw '?°' or numeric junk; sign alone is acceptable
    assert "Aries" in block
    assert "?°" not in block
